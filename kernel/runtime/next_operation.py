"""Evidence-based selection of one next kernel operation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .contracts import eligible_tasks, load_task_index, task_by_id
from .documents import DocumentError, git_snapshot, load_frontmatter, safe_project_path
from .execution_modes import (
    is_persistent_state,
    state_execution_mode,
    validate_lightweight_state,
)
from .state_machine import execution_binding, validate_state


#: Validation codes that mean "the checkout moved", not "the state is wrong".
BINDING_CODES = {
    "git-branch-mismatch",
    "git-detached-head",
}

ASSET_BY_OPERATION = {
    "route-task": "skills/agent-framework-router/SKILL.md",
    "repair-state": "skills/framework-next/SKILL.md",
    "restore-execution-branch": "skills/framework-next/SKILL.md",
    "build-short-plan": "skills/workflow-planner/SKILL.md",
    "execute-standard-plan": "skills/workflow-runner/SKILL.md",
    "run-integrated-review": "skills/goal-coverage-verifier/SKILL.md",
    "discuss-requirements": "skills/workflow-planner/SKILL.md",
    "continue-discussion": "skills/workflow-planner/SKILL.md",
    "build-plan": "skills/workflow-planner/SKILL.md",
    "execute-task": "skills/workflow-runner/SKILL.md",
    "resume-task": "skills/task-runner/SKILL.md",
    "run-spec-review": "skills/spec-compliance-reviewer/SKILL.md",
    "run-quality-review": "skills/code-quality-reviewer/SKILL.md",
    "return-to-execution": "skills/task-runner/SKILL.md",
    "verify-phase": "skills/goal-coverage-verifier/SKILL.md",
    "resolve-blocker": "skills/persistent-debug-session/SKILL.md",
    "ship": "skills/git-decision-router/SKILL.md",
    "none": None,
}


def _decision(
    *,
    state: str,
    evidence: List[str],
    inconsistencies: List[str],
    operation: str,
    target: Any,
    blockers: List[str],
    execution_mode: Any = None,
) -> Dict[str, Any]:
    return {
        "current_state": state,
        "execution_mode": execution_mode,
        "detected_evidence": evidence,
        "inconsistencies": inconsistencies,
        "next_operation": {"operation": operation, "target": target},
        "required_asset": ASSET_BY_OPERATION.get(operation),
        "blocking_conditions": blockers,
    }


def determine_next_operation(project_root: Path) -> Dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    snapshot = git_snapshot(project_root)
    evidence = [
        "project root: {}".format(project_root),
        "git repository: {}".format(snapshot["is_repository"]),
    ]
    if snapshot["is_repository"]:
        evidence.extend(
            [
                "git commit: {}".format(snapshot["commit"]),
                "git dirty: {}".format(snapshot["dirty"]),
            ]
        )

    if not state_path.is_file() and (project_root / ".agent").exists():
        return _decision(
            state="invalid",
            evidence=evidence + ["found .agent/ without STATE.md"],
            inconsistencies=[".agent/STATE.md is missing"],
            operation="repair-state",
            target=".agent/STATE.md",
            blockers=["partial initialization must be inspected; do not overwrite"],
        )

    if not state_path.is_file():
        return _decision(
            state="uninitialized",
            evidence=evidence + ["missing .agent/STATE.md"],
            inconsistencies=[],
            operation="route-task",
            target=str(project_root),
            blockers=[],
            execution_mode="auto",
        )

    try:
        state, _ = load_frontmatter(state_path)
    except DocumentError as exc:
        return _decision(
            state="invalid",
            evidence=evidence + ["found .agent/STATE.md"],
            inconsistencies=[str(exc)],
            operation="repair-state",
            target=".agent/STATE.md",
            blockers=["state document is unreadable"],
        )

    status = str(state.get("status", "invalid"))
    try:
        execution_mode = state_execution_mode(state)
    except ValueError as exc:
        return _decision(
            state=status,
            evidence=evidence + ["found invalid execution_mode"],
            inconsistencies=[str(exc)],
            operation="repair-state",
            target=".agent/STATE.md",
            blockers=[str(exc)],
        )
    evidence.append("loaded state: {}".format(status))
    evidence.append("execution mode: {}".format(execution_mode))

    # Which lifecycle runs is a property of the state that exists, not of the
    # default mode recorded in it. A project keeps its phases, contracts and
    # gates when its default mode is lowered to `standard`; what changes is how
    # much ceremony each task inside it owes.
    persistent = is_persistent_state(state)
    evidence.append(
        "state shape: {}".format("persistent kernel" if persistent else "resume-only")
    )

    # `fast` stays an opt-out even over a persistent state: the existence of
    # `.agent/` does not oblige the next task to run the kernel, and a project
    # that lowered its default to `fast` said exactly that.
    if execution_mode == "fast":
        return _decision(
            state=status,
            evidence=evidence
            + [".agent/ preserved but persistent kernel skipped for fast"],
            inconsistencies=[],
            operation="route-task",
            target=str(project_root),
            blockers=[],
            execution_mode=execution_mode,
        )

    if not persistent:
        lightweight_issues = validate_lightweight_state(state, project_root)
        if lightweight_issues:
            errors = [item["message"] for item in lightweight_issues]
            return _decision(
                state=status,
                evidence=evidence,
                inconsistencies=errors,
                operation="repair-state",
                target=".agent/STATE.md",
                blockers=errors,
                execution_mode=execution_mode,
            )
        if status in {"proposed", "discussing", "specified"}:
            operation, target = "build-short-plan", state.get("artifacts", {}).get(
                "plan"
            )
        elif status in {"planned", "executing"}:
            operation, target = "execute-standard-plan", state.get(
                "current_task", {}
            ).get("id")
        elif status in {"reviewing", "verifying"}:
            operation, target = "run-integrated-review", state.get(
                "current_task", {}
            ).get("id")
        elif status == "blocked":
            operation, target = "resolve-blocker", state.get("blockers", [])
        elif status == "ready_to_ship":
            operation, target = "ship", state.get("phase", {}).get("id")
        elif status in {"shipped", "cancelled", "superseded"}:
            operation, target = "none", None
        else:
            return _decision(
                state=status,
                evidence=evidence,
                inconsistencies=["unknown standard lifecycle status: {}".format(status)],
                operation="repair-state",
                target=".agent/STATE.md",
                blockers=["state status must be repaired before resuming"],
                execution_mode=execution_mode,
            )
        return _decision(
            state=status,
            evidence=evidence + ["resume-only state uses a lightweight lifecycle"],
            inconsistencies=[],
            operation=operation,
            target=target,
            blockers=[],
            execution_mode=execution_mode,
        )

    issues = validate_state(state, project_root)
    errors = [item["message"] for item in issues if item["severity"] == "error"]
    if errors:
        # A binding mismatch is not a broken state — the state is right and the
        # checkout is wrong. Recommending `repair-state` here would point at
        # STATE.md and invite an edit that hides the divergence instead of
        # resolving it, which is the opposite of what the binding is for.
        failing = {
            item["code"] for item in issues if item["severity"] == "error"
        }
        if failing and failing <= BINDING_CODES:
            binding = execution_binding(state)
            return _decision(
                state=status,
                evidence=evidence,
                inconsistencies=errors,
                operation="restore-execution-branch",
                target=binding.get("branch"),
                blockers=errors,
                execution_mode=execution_mode,
            )
        return _decision(
            state=status,
            evidence=evidence,
            inconsistencies=errors,
            operation="repair-state",
            target=".agent/STATE.md",
            blockers=errors,
            execution_mode=execution_mode,
        )

    mapping = {
        "proposed": ("discuss-requirements", ".agent/PROJECT.md"),
        "discussing": ("continue-discussion", state["artifacts"].get("spec")),
        "specified": ("build-plan", state["artifacts"].get("plan")),
        "blocked": (
            "resolve-blocker",
            [
                blocker
                for blocker in state.get("blockers", [])
                if isinstance(blocker, dict)
                and blocker.get("status", "open") != "resolved"
            ],
        ),
        "ready_to_ship": ("ship", state["phase"].get("id")),
        "shipped": ("none", None),
        "cancelled": ("none", None),
        "superseded": ("none", None),
    }

    if status == "planned":
        task_path = safe_project_path(project_root, state["artifacts"]["tasks"])
        index, _ = load_task_index(task_path)
        candidates = eligible_tasks(index["tasks"])
        if not candidates:
            all_verified = all(
                isinstance(task, dict) and task.get("status") in {"verified", "cancelled"}
                for task in index["tasks"]
            )
            reason = (
                "all tasks are verified; state should advance to verifying"
                if all_verified
                else "no pending task has satisfied dependencies"
            )
            return _decision(
                state=status,
                evidence=evidence,
                inconsistencies=[reason],
                operation="repair-state",
                target=state["artifacts"]["tasks"],
                blockers=[reason],
            )
        operation, target = "execute-task", candidates[0]["id"]
        evidence.append("eligible task: {}".format(target))
    elif status == "executing":
        operation, target = "resume-task", state["current_task"]["id"]
        evidence.append("active task contract found: {}".format(target))
    elif status == "reviewing":
        # A rejected review is not a missing one. Recommending the review that
        # already ran would send the reviewer back to re-read the same diff,
        # when what the verdict asked for is a correction.
        if (
            state["gates"].get("spec_compliance") == "blocked"
            or state["gates"].get("code_quality") == "changes_required"
        ):
            operation = "return-to-execution"
        elif state["gates"].get("spec_compliance") not in {
            "passed",
            "passed_with_notes",
        }:
            operation = "run-spec-review"
        elif state["gates"].get("code_quality") not in {
            "approved",
            "approved_with_notes",
            # Recorded by the integrated review below `critical`: the single
            # reviewer covered quality, so pointing at a second one would send
            # the operator back over a diff that has already been judged.
            "not_required",
        }:
            operation = "run-quality-review"
        else:
            operation = "verify-phase"
        target = state["current_task"].get("id") or state["phase"].get("id")
    elif status == "verifying":
        task_path = safe_project_path(project_root, state["artifacts"]["tasks"])
        index, _ = load_task_index(task_path)
        current = task_by_id(index["tasks"], state["current_task"].get("id"))
        if current and current.get("status") == "verified":
            candidates = eligible_tasks(index["tasks"])
            if candidates:
                operation, target = "execute-task", candidates[0]["id"]
                evidence.append("verified task: {}".format(current["id"]))
                evidence.append("eligible next task: {}".format(target))
            else:
                operation, target = "verify-phase", state["phase"].get("id")
        else:
            operation, target = "verify-phase", state["current_task"].get("id")
    else:
        operation, target = mapping[status]

    inconsistencies: List[str] = []
    persisted_action = state.get("next_action", {})
    if isinstance(persisted_action, dict):
        persisted_operation = persisted_action.get("operation")
        persisted_target = persisted_action.get("target")
        if persisted_operation != operation:
            inconsistencies.append(
                "persisted next_action {} is stale; observed state requires {}".format(
                    persisted_operation, operation
                )
            )
        elif persisted_target is not None and persisted_target != target:
            inconsistencies.append(
                "persisted next_action target {} differs from observed {}".format(
                    persisted_target, target
                )
            )

    return _decision(
        state=status,
        evidence=evidence,
        inconsistencies=inconsistencies,
        operation=operation,
        target=target,
        blockers=[],
        execution_mode=execution_mode,
    )
