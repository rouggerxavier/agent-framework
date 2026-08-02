"""Start the task the kernel already selected.

The kernel could compute ``execute-task -> <id>`` and had no way to perform it.
``current_task.id`` was written in exactly three places, and all three look
backwards: ``initialize_project`` and ``activate-phase`` set it to ``None``, and
``reconcile-phase`` fills it from work that is already ``verified``. Every other
writer touches only ``.status``. ``task-status`` refuses unless the task is
already ``current_task`` — which is the very thing that needed setting — and
``transition --to executing`` refuses because no task is selected. A project
that reached ``planned`` honestly, without reconciliation, had no legal move
left except editing ``STATE.md`` by hand.

That gap stayed invisible for as long as every phase arrived through
reconciliation, which back-fills the field. It appears the first time a task is
started *forwards*.

``start_task`` closes it as one operation rather than two. Selecting a task and
starting it are not separate decisions: a persisted state holding a selected
task that is not executing, and not bound to a branch, is a state nothing else
in the lifecycle knows how to read.

The operator does not choose the task. The kernel does — the target comes from
``determine_next_operation``, and an explicitly passed ``task_id`` is only ever
a confirmation that must match. There is deliberately no way to name a
different one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .contracts import load_task_index, task_by_id, update_task_status
from .documents import (
    DocumentError,
    git_snapshot,
    load_frontmatter,
    safe_project_path,
    write_frontmatter,
)
from .evidence import append_evidence_event
from .next_operation import determine_next_operation
from .state_machine import execution_binding, transition_state


#: The only status a task may be started from. Rework paths back into execution
#: keep their own transitions; this operation is about the first start.
START_FROM = "planned"

#: Task states that prove some other task is already under way.
ACTIVE_TASK_STATES = {"executing", "reviewing", "verifying"}


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _ledger_path(state: Dict[str, Any], root: Path) -> Path:
    relative = _mapping(state.get("artifacts")).get("evidence")
    if not relative:
        raise DocumentError("state has no evidence ledger to record the start in")
    path = safe_project_path(root, relative)
    if not path.is_file():
        raise DocumentError("evidence ledger is missing: {}".format(relative))
    return path


def selected_target(decision: Dict[str, Any]) -> Optional[str]:
    """The task the kernel points at, or ``None`` when it points elsewhere."""

    operation = _mapping(decision.get("next_operation"))
    if operation.get("operation") != "execute-task":
        return None
    target = operation.get("target")
    return target if isinstance(target, str) and target else None


def start_issues(
    state: Dict[str, Any],
    root: Path,
    decision: Dict[str, Any],
    *,
    requested_task_id: Optional[str],
) -> Tuple[List[str], Optional[str]]:
    """Everything that stops the start, plus the target when there is one."""

    issues: List[str] = []

    status = state.get("status")
    if status != START_FROM:
        issues.append(
            "starting a task requires a {!r} phase; status is {!r}".format(
                START_FROM, status
            )
        )

    inconsistencies = decision.get("inconsistencies") or []
    if inconsistencies:
        issues.append(
            "resolve state inconsistencies first: {}".format("; ".join(inconsistencies))
        )

    target = selected_target(decision)
    if target is None:
        operation = _mapping(decision.get("next_operation")).get("operation")
        issues.append(
            "the kernel does not point at a task to execute; next operation is "
            "{!r}".format(operation)
        )

    # A persisted target is advisory: transitions record `execute-task` without
    # resolving which task, so `None` here is normal. What is not normal is a
    # persisted target that disagrees with the one the kernel computes.
    persisted = _mapping(state.get("next_action")).get("target")
    if target and isinstance(persisted, str) and persisted and persisted != target:
        issues.append(
            "persisted next_action target {} disagrees with the eligible task "
            "{}".format(persisted, target)
        )

    if requested_task_id and target and requested_task_id != target:
        issues.append(
            "task {} is not the task the kernel selected ({}); the target is not "
            "the operator's to choose".format(requested_task_id, target)
        )

    current = _mapping(state.get("current_task"))
    if current.get("id") and current.get("id") != target:
        issues.append(
            "current_task already holds {}; finish or cancel it first".format(
                current.get("id")
            )
        )

    tasks_relative = _mapping(state.get("artifacts")).get("tasks")
    if not tasks_relative:
        issues.append("state has no task index")
        return issues, target

    try:
        index, _ = load_task_index(safe_project_path(root, tasks_relative))
    except DocumentError as exc:
        issues.append("task index is invalid: {}".format(exc))
        return issues, target

    tasks = index.get("tasks") or []
    started = [
        str(task.get("id"))
        for task in tasks
        if isinstance(task, dict) and task.get("status") in ACTIVE_TASK_STATES
    ]
    if started:
        issues.append(
            "another task is already under way: {}".format(", ".join(started))
        )

    if target:
        contract = task_by_id(tasks, target)
        if contract is None:
            issues.append("task {} has no contract in the index".format(target))
        elif contract.get("status") != "pending":
            issues.append(
                "task {} is {!r}, expected pending".format(
                    target, contract.get("status")
                )
            )

    return issues, target


def _repeat_outcome(
    state: Dict[str, Any], root: Path, *, task_id: Optional[str]
) -> Tuple[bool, List[str]]:
    """Whether this start already happened, and what makes a repeat incompatible.

    Returns ``(True, [])`` when the same task is already running on the same
    checkout — a no-op. Returns issues when the repeat asks for something the
    running execution is not.
    """

    current = _mapping(state.get("current_task"))
    if state.get("status") != "executing" or current.get("status") != "executing":
        return False, []

    running = current.get("id")
    if task_id and running and task_id != running:
        return False, [
            "task {} cannot start: {} is already executing".format(task_id, running)
        ]

    binding = execution_binding(state)
    snapshot = git_snapshot(root)
    if snapshot["is_repository"] and binding.get("branch"):
        if snapshot["branch"] != binding.get("branch"):
            return False, [
                "task {} is already executing on branch {}, and the current "
                "branch is {}".format(running, binding.get("branch"), snapshot["branch"])
            ]
    if binding.get("worktree") != _mapping(state.get("git")).get("worktree"):
        return False, [
            "task {} is already executing against worktree {!r}".format(
                running, binding.get("worktree")
            )
        ]
    return True, []


def start_task(
    project_root: Path,
    *,
    actor: str,
    reason: str,
    task_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[str], bool]:
    """Select the eligible task, start it, and bind it to the checkout.

    Returns the state, the issues that stopped it, and whether anything
    changed. When issues are present nothing is written. Repeating a start that
    already holds — same task, same branch, same worktree — is a no-op rather
    than a second event.

    All three documents move together. ``TASKS.md`` and ``STATE.md`` are
    restored from the bytes read before the first write if any later step
    fails, including the ledger append, so a failure cannot leave a phase
    executing a task the index still calls pending, or an execution with no
    trail.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)

    # Repetition is answered before anything else, because a task that is
    # already running takes the lifecycle out of `planned` — the state that
    # every other check below is written against. Asking again for the start
    # that already happened is not an error; asking for a different one, or
    # from a different checkout, is.
    repeated, repeat_issues = _repeat_outcome(state, project_root, task_id=task_id)
    if repeat_issues:
        return state, repeat_issues, False
    if repeated:
        return state, [], False

    decision = determine_next_operation(project_root)
    issues, target = start_issues(
        state, project_root, decision, requested_task_id=task_id
    )
    if issues:
        return state, issues, False

    tasks_path = safe_project_path(project_root, state["artifacts"]["tasks"])
    state_before = state_path.read_bytes()
    tasks_before = tasks_path.read_bytes()

    # The selection is made here, in memory, and immediately spent: the very
    # next call is the guarded transition, which refuses if anything about the
    # task, the plan, the branch or the worktree is wrong. There is no window
    # in which a selected-but-not-started task is persisted, because the
    # selection is never written on its own.
    state["current_task"] = {"id": target, "status": "pending"}
    try:
        updated = transition_state(
            state, "executing", project_root, actor=actor, reason=reason
        )
    except DocumentError as exc:
        # The guarded transition owns the hard checks — plan seal, plan gate,
        # risk, dirty worktree, detached HEAD, integration branch, contract and
        # dependencies. It signals by raising; this operation answers in issues
        # and writes nothing, so the refusal is translated rather than
        # duplicated here. Nothing has been written at this point.
        return state, [str(exc)], False

    try:
        update_task_status(tasks_path, target, "executing")
        write_frontmatter(state_path, updated, body)
        binding = execution_binding(updated)
        append_evidence_event(
            _ledger_path(updated, project_root),
            {
                "schema_version": 1,
                "task_id": target,
                "kind": "task-start",
                "actor": actor,
                "status": "executing",
                "summary": "Task {} started on branch {} under phase {}. {}".format(
                    target,
                    binding.get("branch"),
                    _mapping(updated.get("phase")).get("id"),
                    reason,
                ),
                "source": state["artifacts"]["tasks"],
                "acceptance_criteria": [],
                "details": {
                    "task_id": target,
                    "selected_by": "kernel",
                    "phase": _mapping(updated.get("phase")).get("id"),
                    "phase_transition": "{} -> executing".format(START_FROM),
                    "task_transition": "pending -> executing",
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
