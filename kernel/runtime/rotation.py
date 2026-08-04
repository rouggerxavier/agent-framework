"""Activate a phase that was planned ahead of time.

A milestone is often contracted before it is executed: the next phase already
has SPEC, PLAN, TASKS and an evidence ledger on disk, written while the current
phase was still running. Nothing in the lifecycle could then *reach* it.
``init-phase`` refuses a directory that exists — and rightly so, since running
it would overwrite those documents — ``seal-plan`` only ever seals the phase the
state already points at, and ``reconcile-phase`` describes work that is already
finished, so a phase whose tasks are all ``pending`` is exactly what it must
refuse.

The missing operation is rotation: the current phase is closed, and the state
moves to a phase that already exists without touching a byte of either one's
documents. It lands on the honest lifecycle position — ``specified`` when the
plan is not sealed for the new phase, so the plan gate still has to be paid, and
``planned`` only when the sealed fingerprint genuinely describes the phase being
activated.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import (
    eligible_tasks,
    load_task_index,
    task_graph_issues,
    validate_task_shape,
)
from .documents import (
    DocumentError,
    load_frontmatter,
    safe_project_path,
    utc_now,
    write_frontmatter,
)
from .state_machine import REVIEW_GATES, compute_plan_fingerprint


PHASE_ARTIFACT_FILES = {
    "spec": "SPEC.md",
    "plan": "PLAN.md",
    "tasks": "TASKS.md",
    "evidence": "EVIDENCE.md",
    "review": "REVIEW.md",
    "handoff": "HANDOFF.md",
}

#: A phase may only be left behind once it is closed. ``ready_to_ship`` is
#: deliberately excluded: it means the current phase still has a ship decision
#: pending, and rotating away from it would strand that decision forever.
ACTIVATABLE_FROM = {"shipped", "superseded"}

#: Task states that prove a phase has already been worked on. Activating into
#: one of these would adopt execution the kernel never witnessed.
EXECUTED_TASK_STATES = {"executing", "reviewing", "verifying", "verified"}

#: States a not-yet-started task may legitimately hold.
UNSTARTED_TASK_STATES = {"pending", "cancelled"}

#: The gates that judge one phase and must not be inherited by the next.
#:
#: ``release`` is the sharp end of it. It guards ``ready_to_ship -> shipped``,
#: and carried across a rotation the activated phase starts already shipped —
#: on a record whose evidence points inside the *previous* phase's directory,
#: which ``set-gate`` would refuse if anyone tried to write it there. Worse, it
#: could never record its own: ``GATE_TRANSITIONS`` has no edge from ``passed``
#: to ``passed``, so the honest verdict was not merely missing, it was
#: unreachable.
#:
#: ``specification`` and ``plan_quality`` are deliberately absent, for the same
#: reason ``amend-plan`` leaves them alone. The rotation lands on ``specified``
#: precisely because the new phase's SPEC exists on disk, and a gate saying
#: otherwise would contradict the landing; ``plan_quality`` is what
#: ``specified -> planned`` and ``planned -> executing`` require, and the plan
#: of the activated phase is held to account by its seal — the fingerprint is
#: reset unless it genuinely describes the phase now active. ``waivers`` is a
#: register, not a judgement about a phase.
PHASE_SCOPED_GATES = REVIEW_GATES + ("release",)


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _open_blockers(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    blockers = state.get("blockers", [])
    if not isinstance(blockers, list):
        return []
    return [
        blocker
        for blocker in blockers
        if isinstance(blocker, dict)
        and blocker.get("status") not in {"resolved", "waived"}
    ]


def _phase_relative(slug: str) -> str:
    return ".agent/phases/{}".format(slug)


def reopen_phase_gates(
    state: Dict[str, Any],
    *,
    closed_phase_id: Any,
    revision: Optional[int],
    at: str,
    actor: str,
) -> List[str]:
    """Retire the closed phase's gates in place. Mutates ``state``.

    Returns the gates that actually moved.

    A gate is a judgement about one phase's work. The rotation was resetting
    the phase, the artifacts, the task and the plan seal, and leaving the gates
    exactly where the closed phase left them — so the activated phase inherited
    verdicts nobody had passed on it.

    The previous record is neither reused nor dropped. What stands on the gate
    is a ``pending`` record for the phase now active, stamped with its revision;
    the closed phase's verdict moves into ``history``, carrying the phase id it
    judged so the two can never be read as one. A gate with no record keeps
    none — creating one here would invent a judgement nobody made.
    """

    gates = dict(_mapping(state.get("gates")))
    records = deepcopy(_mapping(state.get("gate_records")))
    moved: List[str] = []

    for gate in PHASE_SCOPED_GATES:
        if gate not in gates:
            continue
        if gates[gate] != "pending":
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
                    "plan_revision": record.get("plan_revision"),
                    "phase": closed_phase_id,
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


def activation_issues(
    state: Dict[str, Any],
    root: Path,
    *,
    phase_id: str,
    slug: str,
) -> List[str]:
    """Everything that stops the rotation, as operator-facing sentences."""

    issues: List[str] = []

    status = state.get("status")
    if status not in ACTIVATABLE_FROM:
        issues.append(
            "activation requires a closed phase; status is {!r}, expected one of "
            "{}".format(status, ", ".join(sorted(ACTIVATABLE_FROM)))
        )

    current_phase = _mapping(state.get("phase"))
    if current_phase.get("id") == phase_id:
        issues.append("phase {} is already the active phase".format(phase_id))

    current_tasks = _mapping(state.get("artifacts")).get("tasks")
    if current_tasks and str(current_tasks).startswith(_phase_relative(slug) + "/"):
        issues.append("phase directory {} is already active".format(slug))

    if _open_blockers(state):
        issues.append("resolve or waive open blockers before activating a phase")

    try:
        phase_dir = safe_project_path(root, _phase_relative(slug))
    except DocumentError as exc:
        issues.append(str(exc))
        return issues

    if not phase_dir.is_dir():
        issues.append(
            "phase directory does not exist: {}".format(_phase_relative(slug))
        )
        return issues

    for name in sorted(PHASE_ARTIFACT_FILES.values()):
        if not (phase_dir / name).is_file():
            issues.append("phase artifact is missing: {}/{}".format(slug, name))

    roadmap_relative = _mapping(state.get("artifacts")).get("roadmap")
    if roadmap_relative:
        try:
            roadmap = safe_project_path(root, roadmap_relative)
        except DocumentError as exc:
            issues.append(str(exc))
        else:
            if not roadmap.is_file():
                issues.append("roadmap artifact is missing")
            elif phase_id not in roadmap.read_text(encoding="utf-8"):
                issues.append(
                    "phase {} is not recorded in {}".format(phase_id, roadmap_relative)
                )

    tasks_path = phase_dir / "TASKS.md"
    if not tasks_path.is_file():
        return issues

    try:
        index, _ = load_task_index(tasks_path)
    except DocumentError as exc:
        issues.append("task index is invalid: {}".format(exc))
        return issues

    tasks = index.get("tasks") or []
    if not tasks:
        issues.append("activated phase requires at least one task")
        return issues

    started = [
        str(task.get("id"))
        for task in tasks
        if isinstance(task, dict) and task.get("status") in EXECUTED_TASK_STATES
    ]
    if started:
        issues.append(
            "activated phase must not have executed work; already started: "
            "{}".format(", ".join(started))
        )

    unknown = [
        "{}={!r}".format(task.get("id"), task.get("status"))
        for task in tasks
        if isinstance(task, dict)
        and task.get("status") not in UNSTARTED_TASK_STATES
        and task.get("status") not in EXECUTED_TASK_STATES
    ]
    if unknown:
        issues.append(
            "activated phase holds unrecognized task states: {}".format(
                ", ".join(unknown)
            )
        )

    if all(
        isinstance(task, dict) and task.get("status") == "cancelled" for task in tasks
    ):
        issues.append("activated phase has no task left to execute")

    for task in tasks:
        if not isinstance(task, dict):
            issues.append("task index holds a non-object task")
            continue
        for message in validate_task_shape(task):
            issues.append("{}: {}".format(task.get("id", "<unknown>"), message))

    for message in task_graph_issues([t for t in tasks if isinstance(t, dict)]):
        issues.append(message)

    return issues


def activate_phase(
    project_root: Path,
    *,
    phase_id: str,
    phase_name: str,
    slug: str,
    actor: str,
    reason: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """Point the state at an existing, planned phase.

    Returns the updated state and the issues that stopped it. When issues are
    present, nothing is written. The phase being left behind keeps every one of
    its documents; it is recorded in ``completed_phases`` and never rewritten.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)

    issues = activation_issues(state, project_root, phase_id=phase_id, slug=slug)
    if issues:
        return state, issues

    updated = deepcopy(state)
    relative = _phase_relative(slug)

    closed = _mapping(state.get("phase"))
    if closed.get("id"):
        completed = updated.get("completed_phases")
        if not isinstance(completed, list):
            completed = []
        already = any(
            isinstance(entry, dict) and entry.get("id") == closed.get("id")
            for entry in completed
        )
        if not already:
            completed.append(
                {
                    "id": closed.get("id"),
                    "name": closed.get("name"),
                    "status": state.get("status"),
                    "artifacts": _mapping(state.get("artifacts")).get("tasks"),
                    "closed_at": utc_now(),
                }
            )
        updated["completed_phases"] = completed

    updated["artifacts"] = dict(_mapping(state.get("artifacts")))
    updated["artifacts"].update(
        {
            name: "{}/{}".format(relative, filename)
            for name, filename in PHASE_ARTIFACT_FILES.items()
        }
    )

    # The plan only counts as sealed when the stored fingerprint describes the
    # phase now being activated. Anything else is an unsealed plan, and the plan
    # gate has to be paid again through seal-plan.
    revision = _mapping(state.get("plan_revision"))
    sealed = False
    if revision.get("fingerprint"):
        try:
            sealed = compute_plan_fingerprint(updated, project_root) == revision.get(
                "fingerprint"
            )
        except (DocumentError, OSError):
            sealed = False

    landing = "planned" if sealed else "specified"
    if not sealed:
        updated["plan_revision"] = {
            "version": 0,
            "decision_id": None,
            "fingerprint": None,
            "evidence": None,
        }

    updated["phase"] = {"id": phase_id, "name": phase_name, "status": landing}
    updated["status"] = landing
    updated["current_task"] = {"id": None, "status": None}
    updated["blocked_from"] = None

    # After the seal is settled, so the pending records are stamped with the
    # revision the activated phase actually starts on rather than the one the
    # closed phase ended with.
    reopen_phase_gates(
        updated,
        closed_phase_id=closed.get("id"),
        revision=_mapping(updated.get("plan_revision")).get("version"),
        at=utc_now(),
        actor=actor,
    )

    if landing == "planned":
        operation, target = "execute-task", None
        index, _ = load_task_index(project_root / relative / "TASKS.md")
        candidates = eligible_tasks(
            [task for task in index["tasks"] if isinstance(task, dict)]
        )
        if candidates:
            target = candidates[0]["id"]
        updated["next_action"] = {"operation": operation, "target": target}
    else:
        updated["next_action"] = {
            "operation": "build-plan",
            "target": updated["artifacts"]["plan"],
        }

    moment = utc_now()
    updated["last_transition"] = {
        "from": state.get("status"),
        "to": landing,
        "at": moment,
        "by": actor,
        "reason": reason
        or "phase {} activated from existing contracts".format(phase_id),
    }
    updated["updated_at"] = moment
    updated["updated_by"] = actor

    write_frontmatter(state_path, updated, body)
    return updated, []
