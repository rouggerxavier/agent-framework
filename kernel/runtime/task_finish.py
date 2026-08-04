"""Close the task that is under way.

``start-task`` had no counterpart. A task begun outside `critical` could only be
finished by walking the gated lifecycle that `critical` exists for — record the
self-review gate, record a spec review, record a quality review, record
acceptance, record verification, transition four times — or by editing
``STATE.md`` and ``TASKS.md`` by hand. Both are wrong for ordinary work: the
first charges the price of `critical` without buying anything, and the second
writes the record the kernel exists to keep, in a way nothing can check.

So the minimal loop is two operations and the work between them::

    start-task -> implement -> targeted tests -> (optional review) -> finish-task

``finish-task`` marks the task ``verified`` in the index, moves the phase to
``verifying``, releases the execution binding and appends to the evidence ledger
when the phase keeps one. It records what happened; it does not judge whether it
should have. The judging is what `critical` is for, and there this operation
refuses outright — a task under the critical lifecycle is closed by its reviews
and its gates, and a shortcut past them would be the forged record every one of
those gates exists to prevent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import FINISHED_TASK_STATES, load_task_index, task_by_id, update_task_status
from .documents import (
    DocumentError,
    load_frontmatter,
    safe_project_path,
    utc_now,
    write_state,
)
from .evidence import append_evidence_event
from .execution_modes import strict_lifecycle
from .state_machine import (
    effective_task_mode,
    execution_binding,
    release_execution_binding,
)
from .task_start import ledger_path


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def finish_issues(
    state: Dict[str, Any], root: Path, *, requested_task_id: Optional[str]
) -> Tuple[List[str], Optional[str]]:
    """Everything that stops the close, plus the task it would close."""

    issues: List[str] = []
    current = _mapping(state.get("current_task"))
    task_id = current.get("id")

    if strict_lifecycle(effective_task_mode(state, root, task_id=task_id)):
        issues.append(
            "critical closes a task through its reviews and gates, not through "
            "finish-task; record the reviews and transition the phase"
        )

    if not task_id:
        issues.append("no task is under way; current_task holds nothing to finish")
        return issues, None
    if requested_task_id and requested_task_id != task_id:
        issues.append(
            "task {} is not the task under way ({})".format(requested_task_id, task_id)
        )

    open_blockers = [
        str(blocker.get("id") or blocker.get("summary") or "unnamed")
        for blocker in state.get("blockers") or []
        if isinstance(blocker, dict)
        and blocker.get("status", "open") != "resolved"
        and blocker.get("task_id") == task_id
    ]
    if open_blockers:
        issues.append(
            "task {} has open blockers: {}".format(task_id, ", ".join(open_blockers))
        )

    relative = _mapping(state.get("artifacts")).get("tasks")
    if not relative:
        issues.append("state has no task index")
        return issues, task_id
    try:
        index, _ = load_task_index(safe_project_path(root, relative))
    except DocumentError as exc:
        issues.append("task index is invalid: {}".format(exc))
        return issues, task_id

    contract = task_by_id(index.get("tasks") or [], task_id)
    if contract is None:
        issues.append("task {} has no contract in the index".format(task_id))
    elif contract.get("status") in FINISHED_TASK_STATES:
        issues.append(
            "task {} is already {!r}".format(task_id, contract.get("status"))
        )

    return issues, task_id


def finish_task(
    project_root: Path,
    *,
    actor: str,
    reason: str,
    task_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[str], bool]:
    """Mark the current task verified and leave the phase ready for the next one.

    Returns the state, the issues that stopped it, and whether anything changed.
    When issues are present nothing is written. ``TASKS.md`` and ``STATE.md``
    are restored from the bytes read before the first write if any later step
    fails, so a failure cannot leave a verified task inside an executing phase.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)

    issues, target = finish_issues(state, project_root, requested_task_id=task_id)
    if issues:
        return state, issues, False

    tasks_path = safe_project_path(project_root, state["artifacts"]["tasks"])
    state_before = state_path.read_bytes()
    tasks_before = tasks_path.read_bytes()

    previous_status = state.get("status")
    binding = execution_binding(state)
    moment = utc_now()

    updated = dict(state)
    updated["current_task"] = dict(_mapping(state.get("current_task")))
    updated["current_task"]["status"] = "verified"
    updated["status"] = "verifying"
    if _mapping(updated.get("phase")).get("id"):
        updated["phase"] = dict(_mapping(state.get("phase")))
        updated["phase"]["status"] = "verifying"
    # The task is over, so the branch it ran on stops speaking for whatever runs
    # next. The binding is kept as history in `git.last_execution`, which
    # validation never reads.
    release_execution_binding(updated)
    updated["next_action"] = {"operation": "execute-task", "target": None}
    updated["last_transition"] = {
        "from": previous_status,
        "to": "verifying",
        "at": moment,
        "by": actor,
        "reason": reason,
    }
    updated["updated_at"] = moment
    updated["updated_by"] = actor

    try:
        update_task_status(tasks_path, target, "verified", strict=False)
        write_state(state_path, updated, body)
        ledger = ledger_path(updated, project_root)
        if ledger is not None:
            append_evidence_event(
                ledger,
                {
                    "schema_version": 1,
                    "task_id": target,
                    "kind": "task-finish",
                    "actor": actor,
                    "status": "verified",
                    "summary": "Task {} finished on branch {} under phase {}. {}".format(
                        target,
                        binding.get("branch"),
                        _mapping(updated.get("phase")).get("id"),
                        reason,
                    ),
                    "source": state["artifacts"]["tasks"],
                    "acceptance_criteria": [],
                    "details": {
                        "task_id": target,
                        "phase": _mapping(updated.get("phase")).get("id"),
                        "phase_transition": "{} -> verifying".format(previous_status),
                        "task_transition": "{} -> verified".format(
                            _mapping(state.get("current_task")).get("status")
                        ),
                        "branch": binding.get("branch"),
                        "worktree": binding.get("worktree"),
                        "reason": reason,
                    },
                },
            )
    except Exception:
        state_path.write_bytes(state_before)
        tasks_path.write_bytes(tasks_before)
        raise

    return updated, [], True
