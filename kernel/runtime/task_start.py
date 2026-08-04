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

``start-task`` starts a task in two contexts, and they are the same operation:

1. **The first task of a phase**, from ``planned``.
2. **The next task of a phase already under way**, from ``verifying``, once the
   previous task is ``verified`` and another contract is eligible.

The second context was documented as a legal move — ``verifying -> executing``
"may select the next eligible task" — and had no writer. The derivation already
computed ``execute-task -> <next>`` from ``verifying`` with no blockers, so the
kernel was pointing at an operation nothing could perform, and a phase with
four tasks could only ever start its first one.

It is the same operation because the decision is the same one: the kernel names
the eligible task, and this writer selects it, binds it and starts it in a
single write. What differs is only what has to be true first, and what has to be
carried over — the finished task keeps its status, its gates' history and its
binding, the last of which moves to ``git.last_execution`` rather than being
overwritten in place. This is not reconciliation: nothing here back-fills work
that already happened.
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
    write_state,
)
from .evidence import append_evidence_event
from .execution_modes import strict_lifecycle
from .next_operation import determine_next_operation
from .state_machine import (
    FINISHED_TASK_STATES,
    bind_execution,
    effective_task_mode,
    execution_binding,
    release_execution_binding,
    transition_state,
)


#: The status the first task of a phase is started from.
START_FROM = "planned"

#: The status the *next* task of a phase is started from, once the previous one
#: is verified. Rework paths back into execution keep their own transitions;
#: this operation is only ever about starting a task that has not run.
ADVANCE_FROM = "verifying"

#: Every status a task may be started from under `critical`, where walking the
#: phase lifecycle in order is part of what the mode is bought for.
START_STATES = (START_FROM, ADVANCE_FROM)

#: Statuses that are over. Outside `critical` these are the only ones a task
#: cannot be started from: a phase is a grouper, an eligible task is work that
#: is ready, and how far the *phase* has walked its own lifecycle says nothing
#: about whether that work may begin.
CLOSED_PHASE_STATES = {"shipped", "cancelled", "superseded"}

#: Task states that prove some other task is already under way.
ACTIVE_TASK_STATES = {"executing", "reviewing", "verifying"}


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def ledger_path(state: Dict[str, Any], root: Path) -> Optional[Path]:
    """The evidence ledger to append to, or ``None`` when the phase has none.

    A phase outside `critical` may keep a lightweight ledger or no ledger at
    all, so its absence is a shape, not a fault. Refusing the whole operation
    over a missing EVIDENCE.md made "record what happened" a precondition for
    doing anything — which is how the trail ended up mattering more than the
    work it was supposed to describe.
    """

    relative = _mapping(state.get("artifacts")).get("evidence")
    if not relative:
        return None
    path = safe_project_path(root, relative)
    return path if path.is_file() else None


def selected_target(decision: Dict[str, Any]) -> Optional[str]:
    """The task the kernel points at, or ``None`` when it points elsewhere."""

    operation = _mapping(decision.get("next_operation"))
    if operation.get("operation") != "execute-task":
        return None
    target = operation.get("target")
    return target if isinstance(target, str) and target else None


def advancing_from_verified(state: Dict[str, Any]) -> bool:
    """Whether this start continues a phase whose previous task is finished.

    The shape is narrow on purpose: ``verifying`` with a ``current_task`` the
    state itself calls ``verified``. Any other ``verifying`` — a task still
    being verified, a failed verification on its way back to ``executing`` — is
    not an advance and keeps the ordinary refusal.
    """

    if state.get("status") != ADVANCE_FROM:
        return False
    return _mapping(state.get("current_task")).get("status") == "verified"


def _open_blockers(state: Dict[str, Any]) -> List[str]:
    return [
        str(blocker.get("id") or blocker.get("summary") or "unnamed")
        for blocker in state.get("blockers") or []
        if isinstance(blocker, dict) and blocker.get("status", "open") != "resolved"
    ]


def start_issues(
    state: Dict[str, Any],
    root: Path,
    decision: Dict[str, Any],
    *,
    requested_task_id: Optional[str],
    strict: bool,
) -> Tuple[List[str], Optional[str]]:
    """Everything that stops the start, plus the target when there is one."""

    issues: List[str] = []

    status = state.get("status")
    advancing = advancing_from_verified(state)
    if strict:
        if status == ADVANCE_FROM and not advancing:
            issues.append(
                "starting the next task requires the current one to be verified; "
                "{} is {!r}".format(
                    _mapping(state.get("current_task")).get("id") or "current_task",
                    _mapping(state.get("current_task")).get("status"),
                )
            )
        elif status not in START_STATES:
            issues.append(
                "starting a task requires a {!r} or {!r} phase; status is {!r}".format(
                    START_FROM, ADVANCE_FROM, status
                )
            )
    elif status in CLOSED_PHASE_STATES:
        issues.append(
            "phase is {!r}; activate a phase before starting a task".format(status)
        )

    # `inconsistencies` is reporting. What stops an operation is
    # `blocking_conditions`, which the derivation fills from the state errors
    # alone — a missing document, a task that does not exist, an open blocker,
    # a checkout standing somewhere else. Refusing over the rest is what made a
    # lagging `phase.status` cost an operator a hand edit of STATE.md.
    blocking = decision.get("blocking_conditions") or []
    if blocking:
        issues.append("resolve state errors first: {}".format("; ".join(blocking)))

    target = selected_target(decision)
    if target is None:
        operation = _mapping(decision.get("next_operation")).get("operation")
        issues.append(
            "the kernel does not point at a task to execute; next operation is "
            "{!r}".format(operation)
        )

    if requested_task_id and target and requested_task_id != target:
        issues.append(
            "task {} is not the task the kernel selected ({}); the target is not "
            "the operator's to choose".format(requested_task_id, target)
        )

    current = _mapping(state.get("current_task"))
    if (
        current.get("id")
        and current.get("id") != target
        and not advancing
        and current.get("status") not in FINISHED_TASK_STATES
    ):
        issues.append(
            "current_task already holds {}; finish or cancel it first".format(
                current.get("id")
            )
        )

    # A blocker raised against the task being started is the one blocker that
    # stops it. Phase-wide blockers and blockers naming other tasks are
    # reported by `validate`, and holding an eligible task hostage to them is
    # what turned an open question in one corner of a phase into a stop-work
    # order over all of it.
    blocking_the_target = [
        str(blocker.get("id") or blocker.get("summary") or "unnamed")
        for blocker in state.get("blockers") or []
        if isinstance(blocker, dict)
        and blocker.get("status", "open") != "resolved"
        and target
        and blocker.get("task_id") == target
    ]
    if blocking_the_target:
        issues.append(
            "task {} has open blockers: {}".format(
                target, ", ".join(blocking_the_target)
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

    # The index belongs to the phase named in `artifacts.tasks`, so a target
    # found in it is in the current phase by construction. The check is written
    # out anyway for the index that carries its own phase id: a state pointed at
    # one phase and an index describing another is a mismatch worth naming here
    # rather than discovering after the write.
    index_phase = _mapping(index.get("phase")).get("id")
    phase_id = _mapping(state.get("phase")).get("id")
    if index_phase and phase_id and index_phase != phase_id:
        issues.append(
            "task index describes phase {} but the state is in phase {}".format(
                index_phase, phase_id
            )
        )

    if advancing and strict:
        # The state calling the previous task verified is not enough — the index
        # is what every other reader consults, and a task the two disagree about
        # is not finished.
        previous_id = current.get("id")
        previous = task_by_id(tasks, previous_id) if previous_id else None
        if previous is None:
            issues.append(
                "current_task {} has no contract in the index".format(previous_id)
            )
        elif previous.get("status") != "verified":
            issues.append(
                "current_task {} is {!r} in the index, expected verified".format(
                    previous_id, previous.get("status")
                )
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

    strict = strict_lifecycle(effective_task_mode(state, project_root))
    decision = determine_next_operation(project_root)
    issues, target = start_issues(
        state, project_root, decision, requested_task_id=task_id, strict=strict
    )
    if issues:
        return state, issues, False

    tasks_path = safe_project_path(project_root, state["artifacts"]["tasks"])
    state_before = state_path.read_bytes()
    tasks_before = tasks_path.read_bytes()
    previous_status = state.get("status")

    # The selection is made here, in memory, and immediately spent: the very
    # next call is the guarded transition, which refuses if anything about the
    # task, the plan, the branch or the worktree is wrong. There is no window
    # in which a selected-but-not-started task is persisted, because the
    # selection is never written on its own.
    outgoing = _mapping(state.get("current_task")).get("id")
    previous_task = outgoing if outgoing and outgoing != target else None
    if previous_task:
        # The finished task's binding becomes history rather than being
        # overwritten in place, so the branch U3A ran on survives the start of
        # U3B1 and never speaks for it. This reads the *outgoing* current_task,
        # so it has to happen before the selection replaces it.
        release_execution_binding(state)
    state["current_task"] = {"id": target, "status": "pending"}
    # The state being left may itself be execution-bound, and `transition_state`
    # validates before it binds. A selected task with no binding would fall
    # through to the legacy `git.working_branch` and report a mismatch against a
    # branch nobody is standing on, so the capture happens before the validation
    # that depends on it. The transition captures it again; both readings come
    # from the same checkout.
    bind_execution(state, project_root, actor=actor)
    try:
        updated = transition_state(
            state,
            "executing",
            project_root,
            actor=actor,
            reason=reason,
        )
    except DocumentError as exc:
        # The guarded transition owns the hard checks — plan seal, plan gate,
        # risk, dirty worktree, detached HEAD, integration branch, contract and
        # dependencies. It signals by raising; this operation answers in issues
        # and writes nothing, so the refusal is translated rather than
        # duplicated here. Nothing has been written at this point.
        return state, [str(exc)], False

    try:
        update_task_status(tasks_path, target, "executing", strict=strict)
        write_state(state_path, updated, body)
        binding = execution_binding(updated)
        ledger = ledger_path(updated, project_root)
        if ledger is not None:
            append_evidence_event(
                ledger,
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
                        "phase_transition": "{} -> executing".format(previous_status),
                        "task_transition": "pending -> executing",
                        # Names which task this start followed, so the ledger
                        # reads as a sequence rather than a set of unrelated
                        # first starts. Never a claim about that task's own
                        # record.
                        "follows_task": previous_task,
                        "released_execution": _mapping(updated.get("git")).get(
                            "last_execution"
                        )
                        if previous_task
                        else None,
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
