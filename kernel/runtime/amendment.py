"""Amend the sealed plan of a task that is already under way.

A plan is sealed once, at the plan gate, by ``seal-plan`` — and ``seal-plan``
refuses outside ``specified``. That is correct for the *first* seal and wrong for
everything after it, because it assumes the contract can only be wrong before
anyone starts working. It cannot: the fact that proves a contract defective is
often produced by the work itself. A CI run that exercises paths no local
verification reaches is the ordinary case, not the exotic one.

When that happens the kernel had nothing to offer. ``reconcile-phase`` re-seals,
but it is retrospective — it describes a phase already executed and committed,
and using it here would mark work done that is not. The only mechanical route to
a second seal ran ``executing -> blocked -> specified -> seal-plan -> planned ->
executing``, and every step of it lies:

* ``blocked`` requires a blocker, and the only formal writers of blockers are a
  spec review classified ``BLOCKED`` and a quality review classified
  ``CHANGES_REQUIRED``. Neither happened. Manufacturing one turns the
  independence check into a lever for moving the state machine.
* leaving the execution-bound states releases the binding into
  ``git.last_execution``, so the task re-enters execution as if it had started
  again, with a new ``bound_at``. The work did not restart. Only the contract
  changed.
* ``specified`` says nobody has begun. Somebody has.

So the lifecycle offered a choice between hand-editing the fingerprint and
narrating a sequence of events that did not occur. Both destroy the thing the
seal exists to prove.

This operation is the third option. It re-seals **in place**: the phase stays in
execution, ``current_task`` keeps its id, and the binding is copied through byte
for byte rather than released and recaptured. What it does move is the evidence
that the amendment invalidates — the five review and verification gates, which
approved a contract and a diff that no longer exist.

The operator never supplies the fingerprint. It is computed by
``compute_plan_fingerprint``, the same function ``seal-plan`` and ``validate``
use, over the artifacts as they are on disk. This operation seals content; it
never writes it.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from .contracts import (
    load_task_index,
    load_test_policy,
    task_by_id,
    task_graph_issues,
    validate_task_contract,
)
from .documents import (
    DocumentError,
    git_snapshot,
    load_frontmatter,
    safe_project_path,
    utc_now,
    write_frontmatter,
)
from .evidence import append_evidence_event
from .state_machine import (
    FRAMEWORK_ROOT,
    REVIEW_GATES,
    compute_plan_fingerprint,
    effective_task_mode,
    execution_binding,
    reopen_review_gates,
    validate_state,
)


#: The lifecycle states an amendment may be applied from. All three mean the
#: same thing for this purpose: a task is under way and not shipped. ``planned``
#: is deliberately absent — nothing has been executed there, so ``seal-plan``
#: after a return to ``specified`` is still the honest route.
AMENDABLE_STATES = ("executing", "reviewing", "verifying")

#: Task statuses an amendment may act on. ``verified`` is included on purpose:
#: it is the exact status of a task whose local verification passed and whose CI
#: then failed, which is the case this operation was built for. Integration is
#: what closes a task for good, and integration is not a task status — it is
#: recorded in ``completed_units``, which is checked separately.
AMENDABLE_TASK_STATUSES = (
    "executing",
    "implementation_complete",
    "reviewing",
    "reviewed",
    "verifying",
    "verified",
    "blocked",
)

#: The gates an amendment invalidates.
#:
#: All five are judgements about a contract and a diff. The amendment changes
#: the contract, and the diff that satisfied the old one is not the diff that
#: satisfies the new one — so an approval that survived would be approving
#: something nobody read.
#:
#: ``specification`` and ``plan_quality`` are deliberately **not** reopened.
#: They are the gates of the phase's specification and of the plan's quality as
#: a plan, and an amendment made under a recorded decision is an exercise of
#: that plan's quality process, not evidence against it. Reopening them would
#: also strand the state: ``plan_quality`` is what ``specified -> planned`` and
#: ``planned -> executing`` require, so a phase would emerge from the amendment
#: unable to move. Their records keep whatever revision stamped them.
#:
#: The set is shared with the transition that re-enters execution, because the
#: reason is the same in both: a new round of work has begun against a contract
#: the old approvals did not read.
REOPENED_GATES = REVIEW_GATES

#: Task states proving some task other than the current one is under way.
ACTIVE_TASK_STATES = {"executing", "reviewing", "verifying"}

#: Task states that claim work is finished.
COMPLETED_TASK_STATES = {"verified"}

#: The one validation error this operation is allowed to start from — it is the
#: condition being repaired. Every other error means the state is broken in a
#: way an amendment does not address, and the operation refuses rather than
#: sealing on top of it.
REPAIRABLE_CODES = {"plan-changed-without-revision"}

_PHASE_EVIDENCE = re.compile(r"^\.agent/phases/(?P<slug>[^/]+)/")


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _decision_recorded(root: Path, state: Dict[str, Any], decision_id: str) -> bool:
    relative = _mapping(state.get("artifacts")).get("decisions")
    if not relative:
        return False
    try:
        path = safe_project_path(root, relative)
    except DocumentError:
        return False
    if not path.is_file():
        return False
    pattern = re.compile(
        r"^#{{2,6}}\s+{}\b".format(re.escape(decision_id)), re.MULTILINE
    )
    return bool(pattern.search(path.read_text(encoding="utf-8")))


def _active_phase_slug(state: Dict[str, Any]) -> Optional[str]:
    relative = _mapping(state.get("artifacts")).get("tasks")
    if not relative:
        return None
    match = _PHASE_EVIDENCE.match(str(relative))
    return match.group("slug") if match else None


def _integrated_task_ids(state: Dict[str, Any]) -> set:
    integrated = set()
    units = state.get("completed_units")
    if not isinstance(units, list):
        return integrated
    for unit in units:
        if not isinstance(unit, dict):
            continue
        if unit.get("integrated_by") and unit.get("id"):
            integrated.add(str(unit["id"]))
    return integrated


def _contract_issues(
    state: Dict[str, Any], root: Path, *, task_id: str
) -> List[str]:
    """Structural checks on the amended index that need no earlier copy of it.

    The previous contract is not recoverable — only its fingerprint was kept —
    so this cannot diff old against new. What it can do is refuse every shape
    that would let an amendment smuggle in a change of *subject*: losing the
    current task, starting a different one, or declaring downstream work
    finished. Those are the edits that would make the amendment a replan
    wearing a correction's clothes.
    """

    issues: List[str] = []
    relative = _mapping(state.get("artifacts")).get("tasks")
    if not relative:
        return ["state has no task index"]
    try:
        index, _ = load_task_index(safe_project_path(root, relative))
    except DocumentError as exc:
        return ["amended task index is invalid: {}".format(exc)]

    tasks = index.get("tasks") or []
    contract = task_by_id(tasks, task_id)
    if contract is None:
        return [
            "the amended plan has no contract for {}; an amendment may not remove "
            "or rename the task it is amending".format(task_id)
        ]

    for message in task_graph_issues(tasks):
        issues.append("amended task graph: {}".format(message))

    policy = load_test_policy(FRAMEWORK_ROOT)
    for task in tasks:
        if not isinstance(task, dict):
            issues.append("amended task index contains a non-object entry")
            continue
        for contract_issue in validate_task_contract(
            task,
            policy,
            mode=effective_task_mode(state, root, task_id=task.get("id"), index=index),
        ):
            issues.append(
                "{}: {}".format(task.get("id", "<unknown>"), contract_issue["message"])
            )

    others_active = [
        str(task.get("id"))
        for task in tasks
        if isinstance(task, dict)
        and task.get("id") != task_id
        and task.get("status") in ACTIVE_TASK_STATES
    ]
    if others_active:
        issues.append(
            "the amended plan starts another task: {}; an amendment corrects the "
            "task under way, it does not reorder the work".format(
                ", ".join(sorted(others_active))
            )
        )

    # Downstream work cannot be finished, because it cannot have run: it depends
    # on the task being amended, which is still open.
    downstream = [
        str(task.get("id"))
        for task in tasks
        if isinstance(task, dict)
        and task.get("id") != task_id
        and task.get("status") in COMPLETED_TASK_STATES
        and task_id in (task.get("depends_on") or [])
    ]
    if downstream:
        issues.append(
            "the amended plan marks {} complete while {} is still open".format(
                ", ".join(sorted(downstream)), task_id
            )
        )

    return issues


def amend_issues(
    state: Dict[str, Any],
    root: Path,
    *,
    decision_id: Optional[str],
    evidence: Optional[str],
    version: Optional[int],
    new_fingerprint: Optional[str],
) -> List[str]:
    """Everything that stops the amendment, as operator-facing sentences."""

    issues: List[str] = []

    status = state.get("status")
    if status not in AMENDABLE_STATES:
        issues.append(
            "amending an active plan requires a phase in {}; status is {!r}".format(
                ", ".join(AMENDABLE_STATES), status
            )
        )

    task = _mapping(state.get("current_task"))
    task_id = task.get("id")
    if not task_id:
        issues.append(
            "there is no current_task to amend; a plan with nothing under way is "
            "revised by returning to specified and sealing it"
        )
    else:
        if task.get("status") not in AMENDABLE_TASK_STATUSES:
            issues.append(
                "task {} is {!r}; an amendment applies to a task under way".format(
                    task_id, task.get("status")
                )
            )
        if task_id in _integrated_task_ids(state):
            issues.append(
                "task {} is already integrated; amend the contract of work that "
                "has not shipped".format(task_id)
            )

    revision = _mapping(state.get("plan_revision"))
    previous_version = revision.get("version")
    previous_fingerprint = revision.get("fingerprint")
    if not isinstance(previous_version, int) or previous_version < 1:
        issues.append(
            "there is no sealed plan to amend; plan_revision.version is {!r}".format(
                previous_version
            )
        )
    if not previous_fingerprint:
        issues.append(
            "there is no sealed plan to amend; plan_revision has no fingerprint"
        )

    if (
        isinstance(previous_version, int)
        and previous_version >= 1
        and version is not None
        and version != previous_version + 1
    ):
        issues.append(
            "revision {} is not the next revision; the plan is at {} and an "
            "amendment advances it by one".format(version, previous_version)
        )

    if (
        previous_fingerprint
        and new_fingerprint
        and previous_fingerprint == new_fingerprint
    ):
        issues.append(
            "PLAN.md and TASKS.md are unchanged since revision {}; an amendment "
            "seals a correction that was already made".format(previous_version)
        )

    if not decision_id:
        issues.append("an amendment requires a recorded decision")
    elif not _decision_recorded(root, state, decision_id):
        issues.append(
            "decision {} is not recorded in DECISIONS.md".format(decision_id)
        )

    if not evidence:
        issues.append("an amendment requires an evidence reference")
    else:
        relative = str(evidence).split("#", 1)[0]
        if not relative:
            issues.append("evidence reference has no file: {!r}".format(evidence))
        else:
            try:
                path = safe_project_path(root, relative)
            except DocumentError as exc:
                issues.append(str(exc))
            else:
                if not path.is_file():
                    issues.append("evidence file is missing: {}".format(relative))
                else:
                    match = _PHASE_EVIDENCE.match(relative)
                    active = _active_phase_slug(state)
                    if match and active and match.group("slug") != active:
                        issues.append(
                            "evidence belongs to phase {!r}; the active phase is "
                            "{!r}".format(match.group("slug"), active)
                        )

    # The checkout has to be the one the task is bound to. An amendment sealing
    # artifacts from a different branch would seal a plan nobody is executing.
    binding = execution_binding(state)
    snapshot = git_snapshot(root)
    if snapshot["is_repository"] and binding.get("branch"):
        if snapshot["branch"] is None:
            issues.append(
                "execution is bound to branch {} but HEAD is detached".format(
                    binding.get("branch")
                )
            )
        elif snapshot["branch"] != binding.get("branch"):
            issues.append(
                "execution is bound to branch {} but the current branch is "
                "{}".format(binding.get("branch"), snapshot["branch"])
            )

    # Everything else about the state must already hold. The stale fingerprint
    # is the one error an amendment is allowed to find, because repairing it is
    # the point.
    unrelated = [
        item["message"]
        for item in validate_state(state, root)
        if item["severity"] == "error" and item["code"] not in REPAIRABLE_CODES
    ]
    if unrelated:
        issues.append(
            "the state has errors an amendment does not repair: {}".format(
                "; ".join(unrelated)
            )
        )

    if task_id:
        issues.extend(_contract_issues(state, root, task_id=str(task_id)))

    return issues


def _is_repeat(
    state: Dict[str, Any],
    *,
    decision_id: str,
    evidence: str,
    task_id: Optional[str],
    fingerprint: str,
) -> Tuple[bool, List[str]]:
    """Whether this exact amendment already landed, and what makes a repeat wrong.

    ``(True, [])`` means the stored revision already describes these artifacts
    under this decision for this task: nothing to do. Issues mean the repeat
    asks for a different amendment of a plan that is already sealed as it
    stands, which is a rewrite of history rather than a retry.
    """

    revision = _mapping(state.get("plan_revision"))
    if revision.get("fingerprint") != fingerprint:
        return False, []

    # A fingerprint that still matches can mean two different things, and the
    # difference decides which answer is useful. If the seal came from
    # `seal-plan`, nothing has been amended and the operator edited nothing —
    # the honest reply is "the artifacts are unchanged", which `amend_issues`
    # gives. Only a seal this operation wrote can be *re*-applied, so only that
    # one can be re-applied incompatibly.
    if not revision.get("amended_at"):
        return False, []

    mismatches: List[str] = []
    if revision.get("decision_id") != decision_id:
        mismatches.append(
            "sealed under decision {!r}, not {!r}".format(
                revision.get("decision_id"), decision_id
            )
        )
    if revision.get("evidence") != evidence:
        mismatches.append(
            "sealed against evidence {!r}, not {!r}".format(
                revision.get("evidence"), evidence
            )
        )
    stored_task = revision.get("task_id")
    if stored_task is not None and task_id is not None and stored_task != task_id:
        mismatches.append(
            "sealed for task {!r}, not {!r}".format(stored_task, task_id)
        )

    if mismatches:
        return False, [
            "revision {} already seals these artifacts: {}; refusing to rewrite a "
            "landed amendment".format(revision.get("version"), "; ".join(mismatches))
        ]
    return True, []


def amend_plan(
    project_root: Path,
    *,
    decision_id: str,
    evidence: str,
    actor: str,
    reason: str,
    version: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[str], bool]:
    """Re-seal the plan of the task under way and reopen what the change invalidates.

    Returns the state, the issues that stopped it, and whether anything changed.
    When issues are present nothing is written.

    ``STATE.md``, ``TASKS.md`` and the ledger move together. The bytes of all
    three are captured before the first write and restored if any later step
    raises, so a failure cannot leave a new fingerprint against an old status, a
    reopened gate against an old fingerprint, or a revision with no trail.

    The write order is ledger, then index, then state. Neither ordering can be
    made atomic against a process that dies between writes, so the question is
    which half-written outcome is safest. A ledger event without the re-seal
    describes an amendment that did not take effect, and ``validate`` still
    reports the stale fingerprint — the operator sees both and repeats the
    command, which is idempotent. The reverse would leave a plan sealed against
    artifacts with no record of who sealed them or why, which is the outcome
    this operation exists to make impossible.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)

    try:
        fingerprint = compute_plan_fingerprint(state, project_root)
    except (DocumentError, OSError) as exc:
        return state, [str(exc)], False

    task = _mapping(state.get("current_task"))
    task_id = task.get("id")

    # Repetition is answered first. A landed amendment leaves the stored
    # fingerprint equal to the computed one, which every check below would
    # otherwise read as "nothing changed" and refuse — turning a retry after a
    # crashed write into an error.
    repeated, repeat_issues = _is_repeat(
        state,
        decision_id=decision_id,
        evidence=evidence,
        task_id=task_id,
        fingerprint=fingerprint,
    )
    if repeat_issues:
        return state, repeat_issues, False
    if repeated:
        return state, [], False

    issues = amend_issues(
        state,
        project_root,
        decision_id=decision_id,
        evidence=evidence,
        version=version,
        new_fingerprint=fingerprint,
    )
    if issues:
        return state, issues, False

    previous_revision = _mapping(state.get("plan_revision"))
    new_version = int(previous_revision["version"]) + 1
    at = utc_now()

    updated = deepcopy(state)
    updated["plan_revision"] = {
        "version": new_version,
        "decision_id": decision_id,
        # Computed, never supplied. The operator has no argument through which
        # a fingerprint could be named.
        "fingerprint": fingerprint,
        "evidence": evidence,
        "task_id": task_id,
        "reason": reason,
        "amended_at": at,
        "amended_by": actor,
        "supersedes": {
            "version": previous_revision.get("version"),
            "decision_id": previous_revision.get("decision_id"),
            "fingerprint": previous_revision.get("fingerprint"),
            "evidence": previous_revision.get("evidence"),
        },
    }

    # Captured before the reset. For gates that keep a record this duplicates
    # the record's history; for the ones that keep none — the review-owned
    # gates — it is the only surviving trace of what the old contract was
    # approved at, which is why it goes in the ledger rather than nowhere.
    gates_before = {
        gate: _mapping(updated.get("gates")).get(gate)
        for gate in REOPENED_GATES
        if gate in _mapping(updated.get("gates"))
    }
    reopened = reopen_review_gates(
        updated, revision=new_version, at=at, actor=actor
    )

    previous_status = updated.get("status")
    previous_task_status = task.get("status")

    updated["status"] = "executing"
    if _mapping(updated.get("phase")).get("id"):
        updated["phase"] = dict(_mapping(updated["phase"]))
        updated["phase"]["status"] = "executing"

    # The binding is carried across untouched — not released into
    # `git.last_execution`, not recaptured. The work did not restart, so
    # `bound_at` and `bound_by` still describe when and by whom it began.
    # `updated` is already a deep copy, so only the status is touched and the
    # binding object below it is left exactly as it was read.
    updated["current_task"]["status"] = "executing"

    updated["next_action"] = {"operation": "resume-task", "target": task_id}
    updated["last_transition"] = {
        "from": previous_status,
        "to": "executing",
        "at": at,
        "by": actor,
        "reason": reason,
    }
    updated["updated_at"] = at
    updated["updated_by"] = actor

    # The whole state is built before anything is written, and it has to stand
    # on its own: an amendment that produced an invalid state would replace one
    # broken seal with another.
    #
    # ``task-state-mismatch`` is excluded from this pass and only this pass. It
    # compares ``current_task.status`` against the index *on disk*, and the
    # index has not moved yet — the in-memory state says ``executing`` while the
    # file still says what it said. Checking it here would report a
    # disagreement that exists only because the writes have not happened. The
    # authoritative check runs after both documents have moved, below, and rolls
    # everything back if the pair really does disagree.
    residual = [
        item["message"]
        for item in validate_state(updated, project_root)
        if item["severity"] == "error" and item["code"] != "task-state-mismatch"
    ]
    if residual:
        return (
            state,
            ["the amended state would be invalid: {}".format("; ".join(residual))],
            False,
        )

    tasks_path = safe_project_path(project_root, state["artifacts"]["tasks"])
    ledger_relative = _mapping(state.get("artifacts")).get("evidence")
    if not ledger_relative:
        return state, ["state has no evidence ledger to record the amendment in"], False
    ledger_path = safe_project_path(project_root, ledger_relative)
    if not ledger_path.is_file():
        return state, ["evidence ledger is missing: {}".format(ledger_relative)], False

    state_before = state_path.read_bytes()
    tasks_before = tasks_path.read_bytes()
    ledger_before = ledger_path.read_bytes()

    try:
        append_evidence_event(
            ledger_path,
            {
                "schema_version": 1,
                "task_id": task_id,
                "kind": "plan-amendment",
                "actor": actor,
                "status": "executing",
                "summary": (
                    "Plan amended from revision {} to {} under {} while {} was "
                    "{}. {}".format(
                        previous_revision.get("version"),
                        new_version,
                        decision_id,
                        task_id,
                        previous_task_status,
                        reason,
                    )
                ),
                "source": evidence,
                "acceptance_criteria": [],
                "details": {
                    "task_id": task_id,
                    "decision": decision_id,
                    "evidence": evidence,
                    "reason": reason,
                    "revision_from": previous_revision.get("version"),
                    "revision_to": new_version,
                    "fingerprint_from": previous_revision.get("fingerprint"),
                    "fingerprint_to": fingerprint,
                    "phase_transition": "{} -> executing".format(previous_status),
                    "task_transition": "{} -> executing".format(previous_task_status),
                    "gates_reopened": reopened,
                    "gates_before": gates_before,
                    "branch": execution_binding(state).get("branch"),
                    "worktree": execution_binding(state).get("worktree"),
                    "phase": _mapping(state.get("phase")).get("id"),
                },
                "recorded_at": at,
            },
        )
        _write_task_status(tasks_path, str(task_id), "executing")
        write_frontmatter(state_path, updated, body)
    except Exception:
        ledger_path.write_bytes(ledger_before)
        tasks_path.write_bytes(tasks_before)
        state_path.write_bytes(state_before)
        raise

    # Authoritative, and the only pass that sees both documents in their final
    # form. Anything it finds means the amendment produced a state the kernel
    # would refuse to read, so all three documents go back and the operator is
    # told rather than left holding it.
    settled = [
        item["message"]
        for item in validate_state(updated, project_root)
        if item["severity"] == "error"
    ]
    if settled:
        ledger_path.write_bytes(ledger_before)
        tasks_path.write_bytes(tasks_before)
        state_path.write_bytes(state_before)
        return (
            state,
            ["the amended state would be invalid: {}".format("; ".join(settled))],
            False,
        )

    return updated, [], True


def _write_task_status(path: Path, task_id: str, target: str) -> None:
    """Set the index status directly, as the formal owner of this move.

    ``update_task_status`` is refused here on purpose, and the refusal is
    correct everywhere else: ``TASK_STATUS_TRANSITIONS`` gives ``verified`` no
    outgoing edge, so nothing can quietly un-verify a task. That closed door is
    also the second half of the gap this module exists to close — a task whose
    local verification passed and whose CI then failed had no way back.

    Opening ``verified -> executing`` in the shared table would hand that power
    to every caller. Keeping it here means exactly one operation can do it, only
    after a recorded decision, real evidence and a re-seal, and only for the
    task the state already names as current.
    """

    index, body = load_task_index(path)
    task = task_by_id(index["tasks"], task_id)
    if task is None:
        raise DocumentError("{} not found in {}".format(task_id, path))
    task["status"] = target
    write_frontmatter(path, index, body)
