"""Command-line interface for the Agent Framework kernel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .documents import (
    DocumentError,
    load_frontmatter,
    resolve_project_root,
    write_frontmatter,
)
from .contracts import (
    load_contract,
    load_test_policy,
    restore_task_status,
    update_task_status,
    validate_execution_result,
    validate_task_contract,
)
from .evidence import append_evidence_event
from .execution_modes import state_execution_mode, validate_lightweight_state
from .next_operation import determine_next_operation
from .project import initialize_phase, initialize_project
from .reviews import validate_quality_review, validate_spec_review
from .state_machine import (
    compute_plan_fingerprint,
    transition_state,
    validate_state,
    validate_transition,
)
from .worktree import normalize_worktree


FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]


def _project(value: Optional[str]) -> Path:
    return resolve_project_root(Path(value or "."))


def _print_decision(decision: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return
    print("Current state: {}".format(decision["current_state"]))
    print("Execution mode: {}".format(decision.get("execution_mode") or "not selected"))
    print("Detected evidence:")
    for item in decision["detected_evidence"] or ["none"]:
        print("- {}".format(item))
    print("Inconsistencies:")
    for item in decision["inconsistencies"] or ["none"]:
        print("- {}".format(item))
    operation = decision["next_operation"]
    print(
        "Next operation: {}{}".format(
            operation["operation"],
            " -> {}".format(operation["target"]) if operation["target"] else "",
        )
    )
    print("Required asset: {}".format(decision["required_asset"] or "none"))
    print("Blocking conditions:")
    for item in decision["blocking_conditions"] or ["none"]:
        print("- {}".format(item))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="framework-next")
    parser.add_argument("--project", help="project path; defaults to current directory")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    subparsers = parser.add_subparsers(dest="command")

    init = subparsers.add_parser("init", help="initialize .agent safely")
    init.add_argument("--project", dest="init_project")
    init.add_argument("--name", required=True)
    init.add_argument(
        "--mode",
        default="critical",
        choices=("fast", "standard", "critical", "quick", "full", "audit"),
        help="execution mode; quick/full/audit remain accepted as legacy aliases",
    )

    phase = subparsers.add_parser("init-phase", help="create phase artifacts")
    phase.add_argument("--project", dest="phase_project")
    phase.add_argument("--id", required=True)
    phase.add_argument("--name", required=True)
    phase.add_argument("--slug", required=True)
    phase.add_argument("--actor", default="framework-next:init-phase")

    seal = subparsers.add_parser(
        "seal-plan", help="seal PLAN.md and TASKS.md after the plan gate"
    )
    seal.add_argument("--project", dest="seal_project")
    seal.add_argument("--version", type=int, required=True)
    seal.add_argument("--decision", required=True)
    seal.add_argument("--evidence", required=True)
    seal.add_argument("--actor", required=True)

    validate = subparsers.add_parser("validate", help="validate STATE.md and references")
    validate.add_argument("--project", dest="validate_project")

    normalize = subparsers.add_parser(
        "normalize-worktree",
        help=(
            "rewrite a legacy absolute git.worktree as '.'; validation never "
            "edits STATE.md, this operation is the only one that does"
        ),
    )
    normalize.add_argument("--project", dest="normalize_project")
    normalize.add_argument(
        "--check",
        action="store_true",
        help="report what would change without writing",
    )

    transition = subparsers.add_parser("transition", help="apply a guarded state transition")
    transition.add_argument("--project", dest="transition_project")
    transition.add_argument("--to", required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--reason", required=True)

    task_status = subparsers.add_parser(
        "task-status", help="apply a guarded task status transition"
    )
    task_status.add_argument("--project", dest="status_project")
    task_status.add_argument("--task-id", required=True)
    task_status.add_argument("--to", required=True)
    task_status.add_argument("--actor", required=True)

    task = subparsers.add_parser("validate-task", help="validate a complete task contract")
    task.add_argument("--project", dest="task_project")
    task.add_argument("--contract", required=True)
    task.add_argument("--task-id")

    result = subparsers.add_parser("validate-result", help="validate executor result")
    result.add_argument("--project", dest="result_project")
    result.add_argument("--contract", required=True)
    result.add_argument("--task-id")
    result.add_argument("--result", required=True)

    spec = subparsers.add_parser(
        "validate-spec-review", help="validate independent spec review"
    )
    spec.add_argument("--project", dest="spec_project")
    spec.add_argument("--contract", required=True)
    spec.add_argument("--task-id")
    spec.add_argument("--result", required=True)
    spec.add_argument("--review", required=True)

    quality = subparsers.add_parser(
        "validate-quality-review", help="validate independent quality review"
    )
    quality.add_argument("--project", dest="quality_project")
    quality.add_argument("--result", required=True)
    quality.add_argument("--spec-review", required=True)
    quality.add_argument("--review", required=True)

    evidence = subparsers.add_parser(
        "record-evidence", help="append a validated event to EVIDENCE.md"
    )
    evidence.add_argument("--project", dest="evidence_project")
    evidence.add_argument("--ledger", required=True)
    evidence.add_argument("--event", required=True)
    return parser


def _document(root: Path, value: str) -> Dict[str, Any]:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    data, _ = load_frontmatter(path.resolve())
    return data


def _contract(root: Path, value: str, task_id: Optional[str]) -> Dict[str, Any]:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return load_contract(path.resolve(), task_id)


def _emit_issues(issues: Sequence[Dict[str, str]], label: str) -> int:
    if issues:
        print(json.dumps(list(issues), ensure_ascii=False, indent=2))
        return 2
    print("{}: valid".format(label))
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            root = _project(args.init_project or args.project)
            created = initialize_project(
                root, FRAMEWORK_ROOT, project_name=args.name, mode=args.mode
            )
            print("initialized: {}".format(created))
            return 0
        if args.command == "init-phase":
            root = _project(args.phase_project or args.project)
            created = initialize_phase(
                root,
                FRAMEWORK_ROOT,
                phase_id=args.id,
                phase_name=args.name,
                slug=args.slug,
                actor=args.actor,
            )
            print("initialized phase: {}".format(created))
            return 0
        if args.command == "seal-plan":
            root = _project(args.seal_project or args.project)
            state_path = root / ".agent" / "STATE.md"
            state, body = load_frontmatter(state_path)
            if state.get("status") != "specified":
                raise DocumentError("plan may be sealed only from specified")
            state["plan_revision"] = {
                "version": args.version,
                "decision_id": args.decision,
                "fingerprint": compute_plan_fingerprint(state, root),
                "evidence": args.evidence,
            }
            issues = validate_transition(state, "planned", root)
            if issues:
                return _emit_issues(issues, "plan seal")
            from .documents import utc_now

            state["updated_at"] = utc_now()
            state["updated_by"] = args.actor
            write_frontmatter(state_path, state, body)
            print("plan sealed: version={} {}".format(args.version, state["plan_revision"]["fingerprint"]))
            return 0
        if args.command == "validate":
            root = _project(args.validate_project or args.project)
            state, _ = load_frontmatter(root / ".agent" / "STATE.md")
            try:
                execution_mode = state_execution_mode(state)
            except ValueError:
                execution_mode = "invalid"
            issues = (
                validate_lightweight_state(state, root)
                if execution_mode == "standard"
                else validate_state(state, root)
            )
            if issues:
                print(json.dumps(issues, ensure_ascii=False, indent=2))
            if any(issue["severity"] == "error" for issue in issues):
                return 2
            print("state: valid")
            return 0
        if args.command == "normalize-worktree":
            root = _project(args.normalize_project or args.project)
            outcome = normalize_worktree(
                root / ".agent" / "STATE.md", root, apply=not args.check
            )
            if args.json:
                print(json.dumps(outcome, ensure_ascii=False, indent=2))
            else:
                print(
                    "worktree: {}{}".format(
                        outcome["message"],
                        " (not written; --check)"
                        if args.check and outcome["changed"]
                        else "",
                    )
                )
            return 0
        if args.command == "transition":
            root = _project(args.transition_project or args.project)
            state_path = root / ".agent" / "STATE.md"
            state, body = load_frontmatter(state_path)
            updated = transition_state(
                state, args.to, root, actor=args.actor, reason=args.reason
            )
            task_path = None
            previous_task_status = None
            task_id = updated.get("current_task", {}).get("id")
            target_task_status = updated.get("current_task", {}).get("status")
            if task_id and target_task_status:
                task_path = root / updated["artifacts"]["tasks"]
                indexed = load_contract(task_path, task_id)
                if indexed.get("status") != target_task_status:
                    previous_task_status = update_task_status(
                        task_path, task_id, target_task_status
                    )
            try:
                write_frontmatter(state_path, updated, body)
            except Exception:
                if task_path and previous_task_status:
                    restore_task_status(task_path, task_id, previous_task_status)
                raise
            print("transition: {} -> {}".format(state["status"], args.to))
            return 0
        if args.command == "task-status":
            root = _project(args.status_project or args.project)
            state_path = root / ".agent" / "STATE.md"
            state, body = load_frontmatter(state_path)
            if state.get("current_task", {}).get("id") != args.task_id:
                raise DocumentError("task-status may update only current_task")
            task_path = root / state["artifacts"]["tasks"]
            previous = update_task_status(task_path, args.task_id, args.to)
            state["current_task"]["status"] = args.to
            state["updated_by"] = args.actor
            from .documents import utc_now

            state["updated_at"] = utc_now()
            try:
                write_frontmatter(state_path, state, body)
            except Exception:
                restore_task_status(task_path, args.task_id, previous)
                raise
            print("task status: {} {} -> {}".format(args.task_id, previous, args.to))
            return 0
        if args.command == "validate-task":
            root = _project(args.task_project or args.project)
            contract = _contract(root, args.contract, args.task_id)
            issues = validate_task_contract(
                contract, load_test_policy(FRAMEWORK_ROOT), project_root=root
            )
            return _emit_issues(issues, "task contract")
        if args.command == "validate-result":
            root = _project(args.result_project or args.project)
            contract = _contract(root, args.contract, args.task_id)
            result = _document(root, args.result)
            policy = load_test_policy(FRAMEWORK_ROOT)
            issues = validate_task_contract(contract, policy, project_root=root)
            issues.extend(validate_execution_result(contract, result, policy))
            return _emit_issues(issues, "execution result")
        if args.command == "validate-spec-review":
            root = _project(args.spec_project or args.project)
            issues = validate_spec_review(
                _contract(root, args.contract, args.task_id),
                _document(root, args.result),
                _document(root, args.review),
            )
            return _emit_issues(issues, "spec review")
        if args.command == "validate-quality-review":
            root = _project(args.quality_project or args.project)
            issues = validate_quality_review(
                _document(root, args.result),
                _document(root, args.spec_review),
                _document(root, args.review),
            )
            return _emit_issues(issues, "quality review")
        if args.command == "record-evidence":
            root = _project(args.evidence_project or args.project)
            ledger = Path(args.ledger)
            if not ledger.is_absolute():
                ledger = root / ledger
            recorded = append_evidence_event(
                ledger.resolve(), _document(root, args.event)
            )
            print(
                "evidence recorded: {} {}".format(
                    recorded["kind"], recorded["recorded_at"]
                )
            )
            return 0

        decision = determine_next_operation(_project(args.project))
        _print_decision(decision, args.json)
        return 2 if decision["blocking_conditions"] else 0
    except DocumentError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
