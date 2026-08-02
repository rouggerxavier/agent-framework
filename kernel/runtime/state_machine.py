"""Formal state validation and guarded transitions."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional

from .contracts import (
    dependency_issues,
    load_task_index,
    load_test_policy,
    task_by_id,
    task_graph_issues,
    validate_task_contract,
)
from .documents import DocumentError, git_snapshot, safe_project_path, utc_now
from .execution_modes import state_execution_mode
from .worktree import resolve_worktree


STATES = {
    "proposed",
    "discussing",
    "specified",
    "planned",
    "executing",
    "reviewing",
    "verifying",
    "ready_to_ship",
    "shipped",
    "blocked",
    "cancelled",
    "superseded",
}

ALLOWED_TRANSITIONS = {
    "proposed": {"discussing", "blocked", "cancelled", "superseded"},
    "discussing": {"specified", "blocked", "cancelled", "superseded"},
    "specified": {"discussing", "planned", "blocked", "cancelled", "superseded"},
    "planned": {"specified", "executing", "blocked", "cancelled", "superseded"},
    "executing": {"reviewing", "blocked", "cancelled", "superseded"},
    "reviewing": {"executing", "verifying", "blocked", "cancelled", "superseded"},
    "verifying": {
        "executing",
        "reviewing",
        "ready_to_ship",
        "blocked",
        "cancelled",
        "superseded",
    },
    "ready_to_ship": {"verifying", "shipped", "blocked", "cancelled", "superseded"},
    "shipped": {"superseded"},
    "blocked": {
        "discussing",
        "specified",
        "planned",
        "executing",
        "reviewing",
        "verifying",
        "ready_to_ship",
        "cancelled",
        "superseded",
    },
    "cancelled": {"superseded"},
    "superseded": set(),
}

ACTIVE_TASK_STATES = {"executing", "reviewing", "verifying"}

#: States where a task is genuinely being worked on, and the branch and worktree
#: it was bound to must still be the ones under the operator's feet. Everything
#: outside this set — including ``planned`` — has no branch affinity: a sealed
#: plan is not an execution, and the implementation branch may not exist yet.
#: Applying affinity there made a merged working branch outlive its own work and
#: leave the integration branch permanently invalid.
EXECUTION_BOUND_STATES = {"executing", "reviewing", "verifying"}
PHASE_ARTIFACTS = ("spec", "plan", "tasks", "evidence", "review", "handoff")
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]


def _issue(code: str, message: str, severity: str = "error") -> Dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _blockers(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    value = state.get("blockers", [])
    return value if isinstance(value, list) else []


def _artifact_path(
    state: Dict[str, Any], root: Path, name: str
) -> Optional[Path]:
    relative = _mapping(state.get("artifacts")).get(name)
    if not relative:
        return None
    return safe_project_path(root, relative)


def _bind_execution(state: Dict[str, Any], root: Path, *, actor: str) -> None:
    """Record the branch the active task is being worked on, read from Git.

    The binding is captured rather than declared: it comes from the checkout in
    the same write that moves the task, so there is no window where a task is
    bound to a branch nobody is standing on, and no argument through which a
    different branch could be named.
    """

    task = _mapping(state.get("current_task"))
    if not task.get("id"):
        return
    snapshot = git_snapshot(root)
    if not snapshot["is_repository"] or not snapshot["branch"]:
        return
    state["current_task"]["execution"] = {
        "task_id": task["id"],
        "branch": snapshot["branch"],
        "worktree": _mapping(state.get("git")).get("worktree"),
        "bound_at": utc_now(),
        "bound_by": actor,
    }


def execution_binding(state: Dict[str, Any]) -> Dict[str, Any]:
    """The branch and worktree the active task was bound to when it started.

    Executions started by this kernel record the binding on ``current_task``,
    where it belongs: a binding describes one task's work, not the project. A
    state written before the binding existed falls back to
    ``git.working_branch``, so a project already mid-execution keeps its
    protection without being migrated.
    """

    task = _mapping(state.get("current_task"))
    binding = _mapping(task.get("execution"))
    if binding.get("branch"):
        return binding
    git_state = _mapping(state.get("git"))
    legacy = git_state.get("working_branch")
    if legacy:
        return {
            "branch": legacy,
            "worktree": git_state.get("worktree"),
            "legacy": True,
        }
    return {}


def _binding_issues(
    state: Dict[str, Any], snapshot: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Affinity checks that only apply while a task is genuinely being executed."""

    issues: List[Dict[str, str]] = []
    if not snapshot["is_repository"]:
        return issues

    binding = execution_binding(state)
    expected = binding.get("branch")
    if not expected:
        return issues

    current = snapshot["branch"]
    if current is None:
        issues.append(
            _issue(
                "git-detached-head",
                "execution is bound to branch {} but HEAD is detached".format(expected),
            )
        )
    elif current != expected:
        issues.append(
            _issue(
                "git-branch-mismatch",
                "execution is bound to branch {} but the current branch is {}".format(
                    expected, current
                ),
            )
        )

    bound_task = binding.get("task_id")
    task_id = _mapping(state.get("current_task")).get("id")
    if bound_task and task_id and bound_task != task_id:
        issues.append(
            _issue(
                "execution-binding-mismatch",
                "execution binding names task {} but current_task is {}".format(
                    bound_task, task_id
                ),
            )
        )

    if not binding.get("legacy"):
        declared = _mapping(state.get("git")).get("worktree")
        if binding.get("worktree") != declared:
            issues.append(
                _issue(
                    "worktree-binding-mismatch",
                    "execution was bound to worktree {!r} but git.worktree is {!r}".format(
                        binding.get("worktree"), declared
                    ),
                )
            )

    return issues


def validate_state(
    state: Dict[str, Any],
    root: Path,
    *,
    check_files: bool = True,
    check_git: bool = True,
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if state.get("schema_version") != 1:
        issues.append(_issue("schema-version", "schema_version must equal 1"))
    try:
        state_execution_mode(state)
    except ValueError as exc:
        issues.append(_issue("execution-mode", str(exc)))

    status = state.get("status")
    if status not in STATES:
        issues.append(_issue("invalid-state", "unknown lifecycle status: {!r}".format(status)))

    next_action = state.get("next_action")
    if not isinstance(next_action, dict) or not next_action.get("operation"):
        issues.append(
            _issue("next-action", "next_action.operation must be explicit structured data")
        )

    for key in (
        "project",
        "milestone",
        "phase",
        "current_task",
        "risk",
        "verification",
        "artifacts",
        "git",
        "gates",
        "context",
        "plan_revision",
    ):
        if not isinstance(state.get(key), dict):
            issues.append(_issue("invalid-section", "{} must be an object".format(key)))

    blockers = state.get("blockers")
    if not isinstance(blockers, list):
        issues.append(_issue("invalid-blockers", "blockers must be an array"))
        blockers = []
    if status == "blocked" and not blockers:
        issues.append(_issue("blocked-without-blocker", "blocked state requires a blocker"))
    open_blockers = _open_blockers(state)
    if status in {"ready_to_ship", "shipped"} and open_blockers:
        issues.append(
            _issue("shipping-with-blocker", "{} cannot contain open blockers".format(status))
        )

    artifacts = _mapping(state.get("artifacts"))
    required = ["project", "roadmap", "context", "requirements", "decisions"]
    if _mapping(state.get("phase")).get("id"):
        required.extend(PHASE_ARTIFACTS)
    for name in required:
        relative = artifacts.get(name)
        if not relative:
            issues.append(
                _issue("missing-artifact-reference", "artifacts.{} is required".format(name))
            )
            continue
        try:
            path = safe_project_path(root, relative)
        except DocumentError as exc:
            issues.append(_issue("unsafe-artifact-reference", str(exc)))
            continue
        if check_files and not path.is_file():
            issues.append(
                _issue(
                    "missing-artifact",
                    "artifacts.{} points to missing file {}".format(name, relative),
                )
            )

    current_task = _mapping(state.get("current_task"))
    if status in ACTIVE_TASK_STATES and not current_task.get("id"):
        issues.append(
            _issue("active-task-missing", "{} requires current_task.id".format(status))
        )

    if current_task.get("id") and artifacts.get("tasks") and check_files:
        try:
            task_path = safe_project_path(root, artifacts["tasks"])
            index, _ = load_task_index(task_path)
            task = task_by_id(index["tasks"], current_task["id"])
            if task is None:
                issues.append(
                    _issue(
                        "task-contract-missing",
                        "current task {} has no contract in {}".format(
                            current_task["id"], artifacts["tasks"]
                        ),
                    )
                )
            else:
                if current_task.get("status") != task.get("status"):
                    issues.append(
                        _issue(
                            "task-state-mismatch",
                            "current_task.status must match the task contract index",
                        )
                    )
                for contract_issue in validate_task_contract(
                    task, load_test_policy(FRAMEWORK_ROOT)
                ):
                    issues.append(
                        _issue(
                            "task-contract-invalid",
                            contract_issue["message"],
                        )
                    )
        except DocumentError as exc:
            issues.append(_issue("task-index-invalid", str(exc)))

    phase = _mapping(state.get("phase"))
    if phase.get("id") and phase.get("status") != status:
        issues.append(
            _issue("phase-state-mismatch", "phase.status must mirror canonical status")
        )

    if status in {
        "planned",
        "executing",
        "reviewing",
        "verifying",
        "ready_to_ship",
        "shipped",
    } or (
        status == "blocked"
        and state.get("blocked_from")
        in {"planned", "executing", "reviewing", "verifying", "ready_to_ship"}
    ):
        issues.extend(_plan_seal_issues(state, root))

    issues.extend(_gate_record_issues(state))

    risk_level = _mapping(state.get("risk")).get("level")
    if risk_level not in {"unclassified", "low", "medium", "high", "critical"}:
        issues.append(_issue("invalid-risk", "risk.level is invalid"))

    if check_git:
        snapshot = git_snapshot(root)
        context = _mapping(state.get("context"))
        git_state = _mapping(state.get("git"))
        source_commit = context.get("source_commit")
        if (
            snapshot["is_repository"]
            and source_commit
            and snapshot["commit"] != source_commit
            and status in {"planned", "executing", "reviewing", "verifying"}
        ):
            issues.append(
                _issue(
                    "stale-context",
                    "context commit {} differs from current {}; revalidate grounding".format(
                        source_commit, snapshot["commit"]
                    ),
                )
            )
        if status in EXECUTION_BOUND_STATES:
            issues.extend(_binding_issues(state, snapshot))
        resolution = resolve_worktree(git_state.get("worktree"), root)
        if resolution.code:
            issues.append(
                _issue(resolution.code, resolution.message, resolution.severity)
            )
    return issues


#: The gates a new round of work invalidates. They judge a contract and a diff,
#: so re-entering execution — whether because a review sent the task back or
#: because the contract itself was amended — retires all five together.
REVIEW_GATES = (
    "self_review",
    "spec_compliance",
    "code_quality",
    "acceptance",
    "verification",
)


def reopen_review_gates(
    state: Dict[str, Any], *, revision: Optional[int], at: str, actor: str
) -> List[str]:
    """Reset the review gates in place, keeping their approvals as history.

    Mutates ``state`` and returns the gates that actually moved.

    Resetting the map alone is what let ``gates`` and ``gate_records`` drift
    apart: the map said ``pending`` and the record still said ``passed``. Both
    move here, and the record that replaces an approval is a *pending* record
    stamped with the revision it is pending against — so the two can be read
    interchangeably, which is the only way a reader has no wrong choice.

    An approval is never dropped. It is appended to the record's ``history``
    with the revision it was granted under.

    A gate with no record keeps none. Creating one here would be the wrong kind
    of thorough: ``spec_compliance`` and ``code_quality`` are written by the
    review appliers, which move the map and keep no record, and inventing a
    record for them would make the very next review look like a divergence. What
    those gates leave behind instead is the ledger event the caller writes,
    which carries their previous values.
    """

    gates = dict(_mapping(state.get("gates")))
    records = deepcopy(_mapping(state.get("gate_records")))
    moved: List[str] = []

    for gate in REVIEW_GATES:
        if gate not in gates:
            continue
        previous_status = gates[gate]
        if previous_status != "pending":
            moved.append(gate)
        gates[gate] = "pending"

        if gate not in records:
            continue
        record = _mapping(records.get(gate))
        history = list(record.get("history", []))
        if record.get("status") and record.get("status") != "pending":
            history.append(
                {
                    "status": record.get("status"),
                    "decision": record.get("decision"),
                    "evidence": record.get("evidence"),
                    "at": record.get("at"),
                    "by": record.get("by"),
                    # A record written before revisions were stamped belongs to
                    # whatever revision was current when it was written, which
                    # is the one being left behind now.
                    "plan_revision": record.get(
                        "plan_revision",
                        revision - 1 if isinstance(revision, int) else None,
                    ),
                }
            )
        records[gate] = {
            "status": "pending",
            "decision": None,
            "evidence": None,
            "at": at,
            "by": actor,
            "plan_revision": revision,
            "history": history,
        }

    state["gates"] = gates
    state["gate_records"] = records
    return moved


def _gate_record_issues(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """The gates map and its ledger index must tell the same story.

    They can drift: ``transition --to executing`` resets the five review gates in
    ``gates`` and leaves ``gate_records`` untouched, so a state can hold
    ``acceptance: pending`` beside a record that still says ``passed``. Reading
    one or the other then answers the same question differently, and which one
    is authoritative is decided by whichever code path happens to look.

    The check applies only to records carrying a ``plan_revision`` stamp. That
    stamp is written by the operations that know about revisions, so its absence
    identifies a record written before they existed — those are reported by
    nothing and migrated by nobody, which is the compatible default. New records
    are held to the rule from the moment they are written.
    """

    issues: List[Dict[str, str]] = []
    gates = _mapping(state.get("gates"))
    records = _mapping(state.get("gate_records"))
    for name, record in records.items():
        record = _mapping(record)
        if record.get("plan_revision") is None:
            continue
        if name not in gates:
            continue
        if record.get("status") != gates.get(name):
            issues.append(
                _issue(
                    "gate-record-divergence",
                    "gate {} holds {!r} but its record says {!r}".format(
                        name, gates.get(name), record.get("status")
                    ),
                )
            )
    return issues


def _gate(state: Dict[str, Any], name: str) -> Optional[str]:
    return _mapping(state.get("gates")).get(name)


def _verification_results(state: Dict[str, Any]) -> Dict[str, Any]:
    return _mapping(_mapping(state.get("verification")).get("results"))


def _blockers_have_evidence(blockers: Iterable[Dict[str, Any]]) -> bool:
    found = False
    for blocker in blockers:
        found = True
        if not isinstance(blocker, dict) or not blocker.get("evidence"):
            return False
    return found


def _open_blockers(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        blocker
        for blocker in _blockers(state)
        if isinstance(blocker, dict) and blocker.get("status", "open") != "resolved"
    ]


def compute_plan_fingerprint(state: Dict[str, Any], root: Path) -> str:
    digest = hashlib.sha256()
    plan_path = _artifact_path(state, root, "plan")
    task_path = _artifact_path(state, root, "tasks")
    if plan_path is None or not plan_path.is_file():
        raise DocumentError("cannot seal missing plan artifact")
    if task_path is None or not task_path.is_file():
        raise DocumentError("cannot seal missing tasks artifact")

    digest.update(b"plan\0")
    digest.update(plan_path.read_bytes())
    digest.update(b"\0tasks\0")
    task_index, task_body = load_task_index(task_path)
    canonical = deepcopy(task_index)
    for task in canonical.get("tasks", []):
        if isinstance(task, dict):
            task.pop("status", None)
    digest.update(
        json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )
    digest.update(b"\0")
    digest.update(task_body.encode("utf-8"))
    return "sha256:{}".format(digest.hexdigest())


def _plan_seal_issues(state: Dict[str, Any], root: Path) -> List[Dict[str, str]]:
    revision = _mapping(state.get("plan_revision"))
    issues: List[Dict[str, str]] = []
    if not isinstance(revision.get("version"), int) or revision.get("version", 0) < 1:
        issues.append(_issue("plan-revision", "plan revision version must be positive"))
    if not revision.get("decision_id"):
        issues.append(_issue("plan-decision", "plan revision requires a decision id"))
    else:
        decisions_path = _artifact_path(state, root, "decisions")
        if decisions_path is None or not decisions_path.is_file():
            issues.append(_issue("plan-decision", "decisions artifact is missing"))
        else:
            decision_pattern = re.compile(
                r"^#{{2,6}}\s+{}\b".format(
                    re.escape(str(revision["decision_id"]))
                ),
                re.MULTILINE,
            )
            if not decision_pattern.search(decisions_path.read_text(encoding="utf-8")):
                issues.append(
                    _issue(
                        "plan-decision",
                        "decision {} is not recorded in DECISIONS.md".format(
                            revision["decision_id"]
                        ),
                    )
                )
    evidence_reference = revision.get("evidence")
    if not evidence_reference:
        issues.append(_issue("plan-evidence", "plan revision requires gate evidence"))
    else:
        evidence_path = str(evidence_reference).split("#", 1)[0]
        try:
            if not safe_project_path(root, evidence_path).is_file():
                issues.append(
                    _issue("plan-evidence", "plan gate evidence file is missing")
                )
        except DocumentError as exc:
            issues.append(_issue("plan-evidence", str(exc)))
    expected = revision.get("fingerprint")
    if not expected:
        issues.append(_issue("plan-fingerprint", "approved plan must be sealed"))
        return issues
    try:
        actual = compute_plan_fingerprint(state, root)
    except (DocumentError, OSError) as exc:
        issues.append(_issue("plan-fingerprint", str(exc)))
        return issues
    if actual != expected:
        issues.append(
            _issue(
                "plan-changed-without-revision",
                "PLAN.md or TASKS.md changed after plan approval",
            )
        )
    return issues


def validate_transition(
    state: Dict[str, Any], target: str, root: Path
) -> List[Dict[str, str]]:
    current = state.get("status")
    issues: List[Dict[str, str]] = []
    if current not in STATES or target not in STATES:
        return [_issue("invalid-transition-state", "{} -> {}".format(current, target))]
    if target not in ALLOWED_TRANSITIONS[current]:
        return [
            _issue(
                "forbidden-transition",
                "transition {} -> {} is not allowed".format(current, target),
            )
        ]

    blockers = _open_blockers(state)
    task = _mapping(state.get("current_task"))

    if target == "blocked" and not _blockers_have_evidence(blockers):
        issues.append(
            _issue(
                "blocker-evidence",
                "entering blocked requires at least one blocker with evidence",
            )
        )

    if current == "discussing" and target == "specified":
        if _gate(state, "specification") != "passed":
            issues.append(_issue("specification-gate", "specification gate must pass"))
        for artifact in ("requirements", "spec"):
            path = _artifact_path(state, root, artifact)
            if path is None or not path.is_file():
                issues.append(
                    _issue(
                        "spec-artifact",
                        "{} artifact must exist before specified".format(artifact),
                    )
                )

    if current == "specified" and target == "planned":
        if _gate(state, "plan_quality") != "passed":
            issues.append(_issue("plan-gate", "plan quality gate must be passed"))
        if _mapping(state.get("risk")).get("level") in {None, "unclassified"}:
            issues.append(_issue("risk-unclassified", "risk must be classified"))
        for artifact in ("plan", "tasks"):
            path = _artifact_path(state, root, artifact)
            if path is None or not path.is_file():
                issues.append(
                    _issue(
                        "plan-artifact",
                        "{} artifact must exist before planned".format(artifact),
                    )
                )
        task_path = _artifact_path(state, root, "tasks")
        if task_path and task_path.is_file():
            try:
                index, _ = load_task_index(task_path)
                if not index["tasks"]:
                    issues.append(_issue("empty-plan", "planned requires at least one task"))
                for message in task_graph_issues(index["tasks"]):
                    issues.append(_issue("task-graph", message))
                for contract in index["tasks"]:
                    if not isinstance(contract, dict):
                        continue
                    for contract_issue in validate_task_contract(
                        contract, load_test_policy(FRAMEWORK_ROOT)
                    ):
                        issues.append(
                            _issue(
                                "task-contract-invalid",
                                "{}: {}".format(
                                    contract.get("id", "<unknown>"),
                                    contract_issue["message"],
                                ),
                            )
                        )
            except DocumentError as exc:
                issues.append(_issue("task-index-invalid", str(exc)))
        issues.extend(_plan_seal_issues(state, root))

    if current == "planned" and target == "executing":
        issues.extend(_plan_seal_issues(state, root))
        if _gate(state, "plan_quality") != "passed":
            issues.append(_issue("plan-gate", "plan quality gate must be passed"))
        if _mapping(state.get("risk")).get("level") in {None, "unclassified"}:
            issues.append(_issue("risk-unclassified", "risk must be classified"))
        risk_level = _mapping(state.get("risk")).get("level")
        worktree = _mapping(state.get("git")).get("worktree")
        if risk_level in {"high", "critical"} and not worktree:
            issues.append(
                _issue("worktree-required", "high-risk execution requires a worktree")
            )
        snapshot = git_snapshot(root)
        material_changes = [
            path for path in snapshot.get("changed_files", []) if not path.startswith(".agent/")
        ]
        if snapshot["is_repository"] and material_changes and not worktree:
            issues.append(
                _issue(
                    "dirty-worktree",
                    "unrelated working-tree changes require isolated worktree",
                )
            )
        # Starting execution is the moment the work is bound to a branch, so the
        # branch has to be one that can carry it. A detached HEAD has nothing to
        # bind to, and the integration branch is where the work is meant to
        # arrive — not where it is written.
        if snapshot["is_repository"]:
            branch = snapshot["branch"]
            if branch is None:
                issues.append(
                    _issue(
                        "git-detached-head",
                        "execution cannot start on a detached HEAD",
                    )
                )
            else:
                base_branch = _mapping(state.get("git")).get("base_branch")
                if base_branch and branch == base_branch:
                    issues.append(
                        _issue(
                            "execution-on-base-branch",
                            "execution cannot start on the integration branch {}; "
                            "create a working branch first".format(base_branch),
                        )
                    )
        if not task.get("id"):
            issues.append(_issue("task-not-selected", "current_task.id must select a task"))
        task_path = _artifact_path(state, root, "tasks")
        if task_path and task_path.is_file() and task.get("id"):
            try:
                index, _ = load_task_index(task_path)
                contract = task_by_id(index["tasks"], task["id"])
                if contract is None:
                    issues.append(_issue("task-contract-missing", "selected task has no contract"))
                else:
                    for contract_issue in validate_task_contract(
                        contract, load_test_policy(FRAMEWORK_ROOT)
                    ):
                        issues.append(
                            _issue(
                                "task-contract-invalid",
                                contract_issue["message"],
                            )
                        )
                    for message in dependency_issues(contract, index["tasks"]):
                        issues.append(_issue("dependency-unsatisfied", message))
            except DocumentError as exc:
                issues.append(_issue("task-index-invalid", str(exc)))
        else:
            issues.append(_issue("task-index-missing", "task contract index must exist"))

    if current == "executing" and target == "reviewing":
        if task.get("status") != "implementation_complete":
            issues.append(
                _issue(
                    "implementation-incomplete",
                    "executor may enter review only after implementation_complete",
                )
            )
        if _gate(state, "self_review") != "passed":
            issues.append(_issue("self-review", "self-review must be recorded as passed"))

    if current == "reviewing" and target == "executing":
        review_blocked = _gate(state, "spec_compliance") == "blocked"
        quality_blocked = _gate(state, "code_quality") == "changes_required"
        if not (review_blocked or quality_blocked):
            issues.append(
                _issue(
                    "review-not-blocked",
                    "return to executing requires a blocking review result",
                )
            )
        if not _blockers_have_evidence(blockers):
            issues.append(
                _issue("review-blocker-evidence", "review blocker must include evidence")
            )

    if current == "reviewing" and target == "verifying":
        if _gate(state, "spec_compliance") not in {"passed", "passed_with_notes"}:
            issues.append(_issue("spec-review", "spec compliance review has not passed"))
        if _gate(state, "code_quality") not in {"approved", "approved_with_notes"}:
            issues.append(_issue("quality-review", "code quality review has not approved"))
        if blockers:
            issues.append(_issue("open-blockers", "review cannot advance with blockers"))

    if current == "verifying" and target == "ready_to_ship":
        verification = _mapping(state.get("verification"))
        required = verification.get("required", [])
        results = _verification_results(state)
        for check in required if isinstance(required, list) else []:
            if results.get(check) != "passed":
                issues.append(
                    _issue(
                        "verification-missing",
                        "required verification {} has not passed".format(check),
                    )
                )
        if _gate(state, "acceptance") != "passed":
            issues.append(_issue("acceptance-evidence", "acceptance evidence must pass"))
        if _gate(state, "verification") != "passed":
            issues.append(_issue("verification-gate", "verification gate must pass"))
        if _gate(state, "waivers") not in {"not_required", "passed"}:
            issues.append(_issue("waiver-gate", "waivers must be absent or valid"))
        if blockers:
            issues.append(_issue("open-blockers", "ready_to_ship forbids blockers"))
        task_path = _artifact_path(state, root, "tasks")
        if task_path and task_path.is_file():
            try:
                index, _ = load_task_index(task_path)
                unfinished = [
                    task.get("id")
                    for task in index["tasks"]
                    if isinstance(task, dict)
                    and task.get("status") not in {"verified", "cancelled"}
                ]
                if unfinished:
                    issues.append(
                        _issue(
                            "tasks-unverified",
                            "tasks are not verified: {}".format(", ".join(unfinished)),
                        )
                    )
            except DocumentError as exc:
                issues.append(_issue("task-index-invalid", str(exc)))

    if current == "verifying" and target in {"executing", "reviewing"}:
        verification_gate = _gate(state, "verification")
        selecting_next = target == "executing" and verification_gate == "passed"
        if selecting_next:
            if blockers:
                issues.append(
                    _issue("open-blockers", "next task cannot start with blockers")
                )
            task_path = _artifact_path(state, root, "tasks")
            if task_path and task_path.is_file() and task.get("id"):
                try:
                    index, _ = load_task_index(task_path)
                    contract = task_by_id(index["tasks"], task["id"])
                    if contract is None:
                        issues.append(
                            _issue("task-contract-missing", "next task has no contract")
                        )
                    else:
                        if contract.get("status") != "pending":
                            issues.append(
                                _issue(
                                    "next-task-status",
                                    "next task must be pending before execution",
                                )
                            )
                        for message in dependency_issues(contract, index["tasks"]):
                            issues.append(_issue("dependency-unsatisfied", message))
                except DocumentError as exc:
                    issues.append(_issue("task-index-invalid", str(exc)))
            else:
                issues.append(_issue("task-not-selected", "next task must be selected"))
        elif verification_gate != "failed":
            issues.append(
                _issue(
                    "verification-not-failed",
                    "verification must pass for the next task or fail before returning",
                )
            )
        elif not _blockers_have_evidence(blockers):
            issues.append(
                _issue(
                    "verification-failure-evidence",
                    "verification failure requires evidence",
                )
            )

    if current == "ready_to_ship" and target == "shipped":
        if _gate(state, "release") != "passed":
            issues.append(_issue("release-gate", "release gate must pass"))

    if current == "blocked" and target not in {"cancelled", "superseded"}:
        if blockers:
            issues.append(_issue("blockers-open", "resolve blockers before resuming"))
        blocked_from = state.get("blocked_from")
        if blocked_from != target:
            issues.append(
                _issue(
                    "invalid-resume-state",
                    "blocked execution may resume only to {!r}".format(blocked_from),
                )
            )
    return issues


def transition_state(
    state: Dict[str, Any],
    target: str,
    root: Path,
    *,
    actor: str,
    reason: str,
) -> Dict[str, Any]:
    state_issues = validate_state(state, root)
    if state_issues:
        raise DocumentError(
            "state invalid: {}".format(
                "; ".join(item["message"] for item in state_issues)
            )
        )
    issues = validate_transition(state, target, root)
    if issues:
        raise DocumentError(
            "transition blocked: {}".format("; ".join(item["message"] for item in issues))
        )

    updated = deepcopy(state)
    previous = updated["status"]
    if target == "blocked":
        updated["blocked_from"] = previous
    elif previous == "blocked":
        updated["blocked_from"] = None
    updated["status"] = target
    if _mapping(updated.get("phase")).get("id"):
        updated["phase"]["status"] = target
    if target == "executing" and _mapping(updated.get("current_task")).get("id"):
        updated["current_task"]["status"] = "executing"
        _bind_execution(updated, root, actor=actor)
        reopen_review_gates(
            updated,
            revision=_mapping(updated.get("plan_revision")).get("version"),
            at=utc_now(),
            actor=actor,
        )
    elif target == "reviewing" and _mapping(updated.get("current_task")).get("id"):
        updated["current_task"]["status"] = "reviewing"
    elif target == "verifying" and _mapping(updated.get("current_task")).get("id"):
        updated["current_task"]["status"] = "verifying"
    elif target == "ready_to_ship" and _mapping(updated.get("current_task")).get("id"):
        updated["current_task"]["status"] = "verified"

    # Leaving execution releases the binding. Keeping it would let a merged
    # branch keep speaking for work that is over — which is exactly how the
    # integration branch became permanently invalid. The released binding is
    # preserved as history in a field that is never used for validation, so
    # "the branch this ran on" and "the branch this must run on" stop being the
    # same value.
    if target not in EXECUTION_BOUND_STATES:
        current_task = _mapping(updated.get("current_task"))
        released = current_task.pop("execution", None)
        if released:
            updated["git"] = dict(_mapping(updated.get("git")))
            updated["git"]["last_execution"] = dict(released, released_at=utc_now())
    elif not _mapping(_mapping(updated.get("current_task")).get("execution")).get(
        "branch"
    ):
        # Re-entering execution — reworking from ready_to_ship, for instance —
        # arrives with the binding already released. Without capturing it again
        # the legacy fallback would speak for the work and report a branch the
        # rework was never on.
        _bind_execution(updated, root, actor=actor)

    action_by_state = {
        "proposed": ("discuss-requirements", ".agent/PROJECT.md"),
        "discussing": ("continue-discussion", updated.get("phase", {}).get("id")),
        "specified": ("build-plan", updated.get("artifacts", {}).get("plan")),
        "planned": ("execute-task", None),
        "executing": ("resume-task", updated.get("current_task", {}).get("id")),
        "reviewing": ("run-spec-review", updated.get("current_task", {}).get("id")),
        "verifying": ("verify-phase", updated.get("current_task", {}).get("id")),
        "ready_to_ship": ("ship", updated.get("phase", {}).get("id")),
        "shipped": ("none", None),
        "blocked": ("resolve-blocker", updated.get("blockers", [])),
        "cancelled": ("none", None),
        "superseded": ("none", None),
    }
    operation, operation_target = action_by_state[target]
    updated["next_action"] = {
        "operation": operation,
        "target": operation_target,
    }
    updated["last_transition"] = {
        "from": previous,
        "to": target,
        "at": utc_now(),
        "by": actor,
        "reason": reason,
    }
    updated["updated_at"] = updated["last_transition"]["at"]
    updated["updated_by"] = actor
    return updated
