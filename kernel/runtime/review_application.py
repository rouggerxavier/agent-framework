"""Apply a validated independent review to the lifecycle, as one operation.

The kernel could *judge* a review and could not *record* one. ``reviews.py``
held two halves that were never joined: ``validate_spec_review`` and
``validate_quality_review``, reachable through the CLI, which read a review
document and returned issues; and a pair of in-memory appliers that moved the
gates and were called by nothing outside the tests. ``gate-status`` refuses
``spec_compliance`` and ``code_quality`` on purpose — a second writer would let
a gate be recorded without a review document behind it — and pointed at the
``validate-*`` commands as their owners. Those commands wrote nothing.

The result was a lifecycle with no exit. ``reviewing → verifying`` reads both
gates; both were permanently ``pending``; the only way past them was to edit
``STATE.md`` by hand, which forges the exact record the independence check
exists to produce. A second dead end sat underneath: ``TASK_STATUS_TRANSITIONS``
has no ``reviewing → verifying`` edge, so even a hand-edited gate map would have
been refused at the index.

This module is the missing writer, and it is deliberately one operation rather
than two. A durable state in which a review has been validated but not applied
is the same class of half-truth the framework refuses everywhere else: the
document was read, the verdict exists, and nothing in the persisted state can be
asked about it. Loading, validating, applying, recording and re-validating
happen in a single call, over documents that are restored byte for byte if any
step fails.

What it does not do is move the lifecycle. Passing a gate and transitioning are
two deliberate acts here for the same reason they are in ``gate-status``: the
transition carries its own actor, its own reason and its own guards, and a
review that silently advanced the phase would be deciding something the reviewer
was not asked. A blocking verdict likewise records the gate, the blockers and
the ledger event, and then points at ``return-to-execution`` — it does not
perform it.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from .contracts import load_contract, update_task_status
from .documents import (
    DocumentError,
    git_snapshot,
    load_frontmatter,
    safe_project_path,
    utc_now,
    write_frontmatter,
)
from .evidence import append_evidence_event
from .reviews import validate_quality_review, validate_spec_review
from .state_machine import execution_binding, validate_state


#: The two gates this module owns. Nothing else may write them: ``gate-status``
#: names these operations in its refusal, and the refusal is the point.
SPEC_GATE = "spec_compliance"
QUALITY_GATE = "code_quality"

#: The framework's review vocabulary, mapped to the gate states the transition
#: guards already read. No verdict is invented here — ``BLOCKED`` and
#: ``CHANGES_REQUIRED`` are the rejections the framework has, and
#: ``reviewing → executing`` is written against exactly those two values.
SPEC_GATE_STATUS = {
    "PASS": "passed",
    "PASS_WITH_NOTES": "passed_with_notes",
    "BLOCKED": "blocked",
}
QUALITY_GATE_STATUS = {
    "APPROVED": "approved",
    "APPROVED_WITH_NOTES": "approved_with_notes",
    "CHANGES_REQUIRED": "changes_required",
}

SPEC_APPROVING = frozenset({"passed", "passed_with_notes"})
QUALITY_APPROVING = frozenset({"approved", "approved_with_notes"})

#: Stamped on every blocker this module raises, so the approving review that
#: closes it can tell its own findings from everyone else's.
SPEC_BLOCKER_SOURCE = "spec-compliance"
QUALITY_BLOCKER_SOURCE = "code-quality"

#: The only lifecycle status a review may be applied from, and the only task
#: status it may be applied to.
REVIEW_PHASE_STATUS = "reviewing"
REVIEW_TASK_STATUS = "reviewing"

#: The fields that decide whether two applications of a review are the same
#: application. ``report_digest`` carries the document itself — findings,
#: acceptance table, inspected files — so a report edited after it was applied
#: is a different review even when every other field matches.
IDENTITY_FIELDS = (
    "status",
    "classification",
    "plan_revision",
    "task_id",
    "reviewer",
    "executor",
    "report",
    "report_digest",
    "result",
    "reviewed_commit",
    "branch",
)

_PHASE_PATH = re.compile(r"^\.agent/phases/(?P<slug>[^/]+)/")


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _listing(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _active_phase_slug(state: Dict[str, Any]) -> Optional[str]:
    relative = _mapping(state.get("artifacts")).get("tasks")
    if not relative:
        return None
    match = _PHASE_PATH.match(str(relative))
    return match.group("slug") if match else None


def _digest(path: Path) -> str:
    return "sha256:{}".format(hashlib.sha256(path.read_bytes()).hexdigest())


def _project_document(root: Path, reference: str) -> Tuple[Path, str]:
    """Resolve a project-relative reference, refusing anything unreproducible.

    A review is recorded by reference, and a reference that leaves the project
    describes a document nobody else can open. Absolute paths are refused here
    even though ``validate-result`` accepts them, because that command only
    reads and this one writes the path into the permanent record.
    """

    path = safe_project_path(root, reference)
    if not path.is_file():
        raise DocumentError("document is missing: {}".format(reference))
    return path, reference


# ---------------------------------------------------------------------------
# Correspondence between the review and the state it claims to describe
# ---------------------------------------------------------------------------


def _correspondence_issues(
    state: Dict[str, Any],
    root: Path,
    *,
    gate: str,
    report: Dict[str, Any],
    result: Dict[str, Any],
    report_relative: str,
    snapshot: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Everything that stops the application other than the document's own shape.

    ``reviews.py`` answers "is this a well-formed, independent review?". This
    answers "is it a review of *this* work, at *this* revision, of *this*
    commit?" — the questions that need the persisted state and the checkout, and
    the ones that decide whether an old approval can be replayed against new
    work.
    """

    issues: List[Dict[str, str]] = []
    task = _mapping(state.get("current_task"))
    task_id = task.get("id")

    if state.get("status") != REVIEW_PHASE_STATUS:
        issues.append(
            _issue(
                "review-phase",
                "applying a review requires a phase in {!r}; status is {!r}".format(
                    REVIEW_PHASE_STATUS, state.get("status")
                ),
            )
        )

    if not task_id:
        issues.append(
            _issue("review-task", "there is no current_task for a review to describe")
        )
    else:
        if report.get("task_id") != task_id:
            issues.append(
                _issue(
                    "review-task",
                    "the review reports task {!r}; the task under review is "
                    "{!r}".format(report.get("task_id"), task_id),
                )
            )
        if _mapping(result.get("task")).get("id") != task_id:
            issues.append(
                _issue(
                    "review-result-task",
                    "the execution result reports task {!r}; the task under review "
                    "is {!r}".format(_mapping(result.get("task")).get("id"), task_id),
                )
            )
        if task.get("status") != REVIEW_TASK_STATUS:
            issues.append(
                _issue(
                    "review-task-status",
                    "task {} is {!r}; a review applies to a task in {!r}".format(
                        task_id, task.get("status"), REVIEW_TASK_STATUS
                    ),
                )
            )

    phase_id = _mapping(state.get("phase")).get("id")
    reported_phase = report.get("phase")
    if reported_phase and phase_id and reported_phase != phase_id:
        issues.append(
            _issue(
                "review-phase-mismatch",
                "the review belongs to phase {!r}; the active phase is {!r}".format(
                    reported_phase, phase_id
                ),
            )
        )

    # The revision is the contract the reviewer read. Without it an approval
    # granted before an amendment is indistinguishable from one granted after
    # it, which is exactly the replay `amend-plan` reopens the gates to prevent.
    revision = _mapping(state.get("plan_revision")).get("version")
    reported_revision = report.get("plan_revision")
    if not isinstance(reported_revision, int):
        issues.append(
            _issue(
                "review-revision",
                "the review must state the plan_revision it read; the plan is at "
                "revision {!r}".format(revision),
            )
        )
    elif reported_revision != revision:
        issues.append(
            _issue(
                "review-revision",
                "the review read plan revision {}; the plan is at revision {}. An "
                "approval belongs to the revision it was granted under".format(
                    reported_revision, revision
                ),
            )
        )

    reported_commit = report.get("reviewed_commit")
    if not reported_commit:
        issues.append(
            _issue("review-commit", "the review must state the commit it read")
        )

    if snapshot["is_repository"]:
        if reported_commit and reported_commit != snapshot["commit"]:
            issues.append(
                _issue(
                    "review-commit",
                    "the review read commit {} and HEAD is {}; a review approves "
                    "the diff that exists".format(reported_commit, snapshot["commit"]),
                )
            )
        if snapshot["branch"] is None:
            issues.append(
                _issue(
                    "review-detached-head",
                    "HEAD is detached; a review is applied from the branch the "
                    "execution is bound to",
                )
            )
        else:
            bound = execution_binding(state).get("branch")
            if bound and bound != snapshot["branch"]:
                issues.append(
                    _issue(
                        "review-branch",
                        "execution is bound to branch {} but the current branch is "
                        "{}".format(bound, snapshot["branch"]),
                    )
                )
            reported_branch = report.get("branch")
            if reported_branch and reported_branch != snapshot["branch"]:
                issues.append(
                    _issue(
                        "review-branch",
                        "the review names branch {!r}; the current branch is "
                        "{!r}".format(reported_branch, snapshot["branch"]),
                    )
                )
        # `.agent/` moves constantly while the kernel runs and is never the
        # product. Anything else uncommitted is a change the reviewer did not
        # read, which makes the reviewed commit an incomplete description of
        # what is on disk.
        material = sorted(
            path
            for path in snapshot.get("changed_files", [])
            if not path.startswith(".agent/")
        )
        if material:
            issues.append(
                _issue(
                    "review-worktree-moved",
                    "the working tree carries product changes the review did not "
                    "read: {}".format(", ".join(material[:5])),
                )
            )

    match = _PHASE_PATH.match(report_relative)
    active = _active_phase_slug(state)
    if match and active and match.group("slug") != active:
        issues.append(
            _issue(
                "review-report-phase",
                "the review document belongs to phase {!r}; the active phase is "
                "{!r}".format(match.group("slug"), active),
            )
        )

    for relative in _listing(report.get("files_inspected")):
        if not isinstance(relative, str) or not relative:
            issues.append(
                _issue(
                    "review-files",
                    "each inspected file must be a project-relative path",
                )
            )
            continue
        try:
            safe_project_path(root, relative)
        except DocumentError as exc:
            issues.append(_issue("review-files", str(exc)))

    gates = _mapping(state.get("gates"))
    if gate == SPEC_GATE:
        if gates.get(QUALITY_GATE) in QUALITY_APPROVING:
            issues.append(
                _issue(
                    "review-order",
                    "code_quality already holds {!r}; a spec review cannot be "
                    "applied after the quality review that depended on it".format(
                        gates.get(QUALITY_GATE)
                    ),
                )
            )
    else:
        if gates.get(SPEC_GATE) not in SPEC_APPROVING:
            issues.append(
                _issue(
                    "review-order",
                    "spec_compliance is {!r}; the quality review runs only after "
                    "spec compliance passes".format(gates.get(SPEC_GATE)),
                )
            )

    # Everything else about the state must already hold. A review is a judgement
    # about work, not a repair: applying one on top of a broken state would
    # stamp an approval onto something the kernel cannot read.
    broken = [
        item["message"]
        for item in validate_state(state, root)
        if item["severity"] == "error"
    ]
    if broken:
        issues.append(
            _issue(
                "review-state",
                "the state has errors a review does not repair: {}".format(
                    "; ".join(broken)
                ),
            )
        )

    return issues


# ---------------------------------------------------------------------------
# Records, blockers and repetition
# ---------------------------------------------------------------------------


def _identity(
    *,
    gate_status: str,
    classification: str,
    revision: Any,
    task_id: Any,
    reviewer: Any,
    executor: Any,
    report_relative: str,
    report_digest: str,
    result_relative: str,
    reviewed_commit: Any,
    branch: Any,
) -> Dict[str, Any]:
    return {
        "status": gate_status,
        "classification": classification,
        "plan_revision": revision,
        "task_id": task_id,
        "reviewer": reviewer,
        "executor": executor,
        "report": report_relative,
        "report_digest": report_digest,
        "result": result_relative,
        "reviewed_commit": reviewed_commit,
        "branch": branch,
    }


def _repeat_outcome(
    state: Dict[str, Any], *, gate: str, identity: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, str]]]:
    """Whether this exact review already landed, and what makes a repeat wrong.

    A record stamped with an *earlier* revision is history, not an application:
    it belongs to the contract that was amended away, and it neither blocks nor
    approves the review being applied now. A record with no stamp at all is a
    legacy record, treated the same way — conservatively, never as approval of
    an amendment it predates.
    """

    record = _mapping(_mapping(state.get("gate_records")).get(gate))
    if not record or record.get("status") in (None, "pending"):
        return False, []
    # Three revisions have to agree for this to be the same application: the
    # one the record was granted under, the one the review says it read, and the
    # one the plan is on now. Dropping the third would let a stale approval be
    # reported as already-landed against a plan that has since moved.
    current_revision = _mapping(state.get("plan_revision")).get("version")
    if identity["plan_revision"] != current_revision:
        return False, []
    if record.get("plan_revision") != identity["plan_revision"]:
        return False, []

    mismatches = [
        "{} is recorded as {!r}, not {!r}".format(
            field, record.get(field), identity[field]
        )
        for field in IDENTITY_FIELDS
        if record.get(field) != identity[field]
    ]
    if mismatches:
        return False, [
            _issue(
                "review-already-applied",
                "gate {} already holds {!r} for plan revision {}: {}; refusing to "
                "rewrite an applied review".format(
                    gate,
                    record.get("status"),
                    record.get("plan_revision"),
                    "; ".join(mismatches),
                ),
            )
        ]
    return True, []


def _record(previous: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    """The new record, with the one it replaces pushed onto its history."""

    history = list(_listing(previous.get("history")))
    if previous.get("status") and previous.get("status") != "pending":
        history.append(
            {
                field: previous.get(field)
                for field in (
                    "status",
                    "classification",
                    "plan_revision",
                    "reviewer",
                    "executor",
                    "report",
                    "report_digest",
                    "reviewed_commit",
                    "decision",
                    "evidence",
                    "at",
                    "by",
                )
            }
        )
    settled = dict(record)
    settled["history"] = history
    return settled


def _merge_blockers(
    existing: List[Any], produced: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Add the review's blockers without discarding anyone else's.

    Replacing the list outright — which the unreachable applier used to do —
    would let a review silently close a blocker it never examined.
    """

    merged = [item for item in existing if isinstance(item, dict)]
    positions = {
        item.get("id"): index
        for index, item in enumerate(merged)
        if item.get("id")
    }
    for blocker in produced:
        index = positions.get(blocker.get("id"))
        if index is None:
            positions[blocker.get("id")] = len(merged)
            merged.append(blocker)
        else:
            merged[index] = blocker
    return merged


def _spec_blockers(report: Dict[str, Any], task_id: Any) -> List[Dict[str, Any]]:
    return [
        {
            "id": str(blocker.get("id")),
            "summary": blocker.get("summary"),
            "evidence": _listing(blocker.get("evidence")),
            "status": "open",
            "source": SPEC_BLOCKER_SOURCE,
            "task_id": task_id,
        }
        for blocker in _listing(report.get("blockers"))
        if isinstance(blocker, dict)
    ]


def _quality_blockers(report: Dict[str, Any], task_id: Any) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    for position, finding in enumerate(_listing(report.get("findings")), start=1):
        if not isinstance(finding, dict) or not finding.get("required_change"):
            continue
        blockers.append(
            {
                "id": "QUALITY-{}-{:02d}".format(task_id, position),
                "summary": finding.get("summary", "quality change required"),
                "evidence": _listing(finding.get("evidence")),
                "severity": finding.get("severity"),
                "required_change": finding.get("required_change"),
                "status": "open",
                "source": QUALITY_BLOCKER_SOURCE,
                "task_id": task_id,
            }
        )
    return blockers


def _resolve_blockers(
    existing: List[Any],
    *,
    source: str,
    task_id: Any,
    report_relative: str,
    at: str,
    actor: Optional[str],
) -> Tuple[List[Any], List[str]]:
    """Close the blockers this gate opened, once a later review approves the work.

    A blocking review is the only thing that opens these, so an approving review
    of the same gate, on the same task, is the only thing that can honestly close
    them: an independent reviewer read the corrected diff and did not raise the
    finding again. Leaving them open instead would make ``reviewing → verifying``
    permanently unreachable after any ``CHANGES_REQUIRED`` round, since that
    guard refuses to advance while a blocker is open — and the alternative,
    editing ``blockers`` by hand, is the forged record this module exists to
    prevent.

    Only blockers this module wrote are touched: they carry both ``source`` and
    ``task_id``. A blocker raised by anything else, or by another task, is not
    this review's to close, and one written before those fields existed is left
    alone rather than guessed about.
    """

    resolved: List[str] = []
    updated: List[Any] = []
    for blocker in existing:
        if (
            isinstance(blocker, dict)
            and blocker.get("source") == source
            and blocker.get("task_id") == task_id
            and blocker.get("status", "open") != "resolved"
        ):
            closed = dict(blocker)
            closed["status"] = "resolved"
            closed["resolved_at"] = at
            closed["resolved_by"] = actor
            closed["resolved_by_review"] = report_relative
            updated.append(closed)
            resolved.append(str(blocker.get("id")))
            continue
        updated.append(blocker)
    return updated, resolved


# ---------------------------------------------------------------------------
# The review artifact
# ---------------------------------------------------------------------------


def _review_entry(
    *, gate: str, record: Dict[str, Any], recorded_at: str
) -> str:
    """One append-only section for ``REVIEW.md``.

    Appending rather than editing the template's table is deliberate: an audit
    document that a command rewrites in place is a document a command can
    quietly correct.
    """

    lines = [
        "",
        "## {} — {} {}: {}".format(
            recorded_at,
            record.get("task_id"),
            gate.replace("_", " "),
            record.get("status"),
        ),
        "",
        "- Classification: {}".format(record.get("classification")),
        "- Reviewer: {}".format(record.get("reviewer")),
        "- Executor: {}".format(record.get("executor")),
        "- Plan revision: {}".format(record.get("plan_revision")),
        "- Reviewed commit: {}".format(record.get("reviewed_commit")),
        "- Branch: {}".format(record.get("branch")),
        "- Report: {}".format(record.get("report")),
        "- Report digest: {}".format(record.get("report_digest")),
        "- Result: {}".format(record.get("result")),
        "- Files inspected: {}".format(
            ", ".join(str(item) for item in record.get("files_inspected") or []) or "none"
        ),
        "- Evidence inspected: {}".format(
            ", ".join(str(item) for item in record.get("evidence_inspected") or [])
            or "none"
        ),
        "- Applied by: {}".format(record.get("by")),
        "",
    ]
    findings = record.get("findings") or []
    if findings:
        lines.append("Findings:")
        lines.append("")
        for finding in findings:
            lines.append(
                "- [{}] {} — {}".format(
                    finding.get("severity") or "unspecified",
                    finding.get("summary") or "",
                    finding.get("required_change") or "no change required",
                )
            )
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The operation
# ---------------------------------------------------------------------------


def _next_action(gate: str, gate_status: str, task_id: Any) -> Dict[str, Any]:
    if gate_status in {"blocked", "changes_required"}:
        return {"operation": "return-to-execution", "target": task_id}
    if gate == SPEC_GATE:
        return {"operation": "run-quality-review", "target": task_id}
    return {"operation": "verify-phase", "target": task_id}


def _load_state(project_root: Path) -> Tuple[Dict[str, Any], str]:
    return load_frontmatter(project_root / ".agent" / "STATE.md")


def _apply(
    project_root: Path,
    *,
    gate: str,
    report: Dict[str, Any],
    report_relative: str,
    report_digest: str,
    result: Dict[str, Any],
    result_relative: str,
    document_issues: List[Dict[str, str]],
    actor: Optional[str],
    write: bool,
) -> Tuple[Dict[str, Any], List[Dict[str, str]], bool]:
    """Validate the review against the state and, when asked, record it.

    Returns the state, the issues that stopped it, and whether anything changed.
    When issues are present nothing is written. ``write=False`` runs every check
    and writes nothing, which is what the ``validate-*`` commands do.
    """

    state_path = project_root / ".agent" / "STATE.md"
    if not state_path.is_file():
        # A review document can be checked for shape and independence without a
        # project; it cannot be checked against work that is not recorded, and
        # it certainly cannot be applied.
        if write:
            return {}, document_issues + [
                _issue("review-state", "no .agent/STATE.md to apply the review to")
            ], False
        return {}, document_issues, False

    state, body = _load_state(project_root)

    classification = report.get("classification")
    mapping = SPEC_GATE_STATUS if gate == SPEC_GATE else QUALITY_GATE_STATUS
    gate_status = mapping.get(classification)

    revision = _mapping(state.get("plan_revision")).get("version")
    task = _mapping(state.get("current_task"))
    executor = _mapping(result.get("task")).get("executor")
    snapshot = git_snapshot(project_root)
    identity = _identity(
        gate_status=gate_status,
        classification=classification,
        revision=report.get("plan_revision"),
        task_id=report.get("task_id"),
        reviewer=report.get("reviewer"),
        executor=executor,
        report_relative=report_relative,
        report_digest=report_digest,
        result_relative=result_relative,
        reviewed_commit=report.get("reviewed_commit"),
        branch=snapshot["branch"] if snapshot["is_repository"] else None,
    )

    # Repetition is answered before the preconditions, because a landed
    # application moves the very things those preconditions read — an approved
    # quality review leaves the task ``reviewed``, which "a review applies to a
    # task in reviewing" would then reject. Asking again for what already
    # happened is not an error; asking for something else is.
    repeated, repeat_issues = _repeat_outcome(state, gate=gate, identity=identity)
    if repeat_issues:
        return state, document_issues + repeat_issues, False
    if repeated and not document_issues:
        return state, [], False

    issues = list(document_issues)
    if gate_status is None:
        issues.append(
            _issue(
                "review-classification",
                "classification {!r} has no gate state; allowed: {}".format(
                    classification, ", ".join(sorted(mapping))
                ),
            )
        )
    issues.extend(
        _correspondence_issues(
            state,
            project_root,
            gate=gate,
            report=report,
            result=result,
            report_relative=report_relative,
            snapshot=snapshot,
        )
    )
    if write and not actor:
        issues.append(_issue("review-actor", "applying a review requires an actor"))
    if issues:
        return state, issues, False
    if not write:
        return state, [], False

    recorded_at = utc_now()
    task_id = task.get("id")
    findings = [item for item in _listing(report.get("findings")) if isinstance(item, dict)]

    updated = deepcopy(state)

    blocker_source = (
        SPEC_BLOCKER_SOURCE if gate == SPEC_GATE else QUALITY_BLOCKER_SOURCE
    )
    approving = SPEC_APPROVING if gate == SPEC_GATE else QUALITY_APPROVING
    raised_blockers: List[Dict[str, Any]] = []
    resolved_blockers: List[str] = []
    if gate == SPEC_GATE and gate_status == "blocked":
        raised_blockers = _spec_blockers(report, task_id)
        updated["blockers"] = _merge_blockers(
            _listing(updated.get("blockers")), raised_blockers
        )
    elif gate == QUALITY_GATE and gate_status == "changes_required":
        raised_blockers = _quality_blockers(report, task_id)
        updated["blockers"] = _merge_blockers(
            _listing(updated.get("blockers")), raised_blockers
        )
    elif gate_status in approving:
        updated["blockers"], resolved_blockers = _resolve_blockers(
            _listing(updated.get("blockers")),
            source=blocker_source,
            task_id=task_id,
            report_relative=report_relative,
            at=recorded_at,
            actor=actor,
        )

    record = _record(
        _mapping(_mapping(state.get("gate_records")).get(gate)),
        {
            "gate": gate,
            "status": gate_status,
            "classification": classification,
            "task_id": task_id,
            "plan_revision": revision,
            "reviewer": report.get("reviewer"),
            "executor": executor,
            "report": report_relative,
            "report_digest": report_digest,
            "result": result_relative,
            "reviewed_commit": report.get("reviewed_commit"),
            "branch": identity["branch"],
            "files_inspected": _listing(report.get("files_inspected")),
            "evidence_inspected": _listing(report.get("evidence_inspected")),
            "findings": findings,
            "required_changes": [
                finding.get("required_change")
                for finding in findings
                if finding.get("required_change")
            ],
            "notes": _listing(report.get("notes")),
            "blockers_raised": [blocker["id"] for blocker in raised_blockers],
            "blockers_resolved": resolved_blockers,
            # Review gates are not decision-backed: the review document is the
            # justification, and `decision`/`evidence` are kept so a reader of
            # `gate_records` finds the same shape `gate-status` writes.
            "decision": None,
            "evidence": report_relative,
            "note": None,
            "at": recorded_at,
            "by": actor,
        },
    )

    updated["gates"] = dict(_mapping(updated.get("gates")))
    updated["gates"][gate] = gate_status
    updated["gate_records"] = dict(_mapping(updated.get("gate_records")))
    updated["gate_records"][gate] = record

    # The one task-status move a review owns. It is what makes
    # `reviewing → verifying` reachable at all: `TASK_STATUS_TRANSITIONS` has no
    # edge from `reviewing` to `verifying`, so without `reviewed` the phase
    # transition would be refused at the index even with both gates green.
    task_status_target = None
    if gate == QUALITY_GATE and gate_status in QUALITY_APPROVING:
        task_status_target = "reviewed"
        updated["current_task"] = dict(_mapping(updated.get("current_task")))
        updated["current_task"]["status"] = task_status_target

    updated["next_action"] = _next_action(gate, gate_status, task_id)
    updated["updated_at"] = recorded_at
    updated["updated_by"] = actor

    # Built whole before anything is written, and it has to stand on its own.
    # `task-state-mismatch` is excluded from this pass and only this pass: the
    # index has not moved yet, so it would report a disagreement that exists
    # only because the writes have not happened. The authoritative pass runs
    # after every document has moved.
    residual = [
        item["message"]
        for item in validate_state(updated, project_root)
        if item["severity"] == "error" and item["code"] != "task-state-mismatch"
    ]
    if residual:
        return (
            state,
            [
                _issue(
                    "review-result-state",
                    "applying the review would produce an invalid state: {}".format(
                        "; ".join(residual)
                    ),
                )
            ],
            False,
        )

    artifacts = _mapping(state.get("artifacts"))
    ledger_relative = artifacts.get("evidence")
    if not ledger_relative:
        return state, [_issue("review-ledger", "state has no evidence ledger")], False
    ledger_path = safe_project_path(project_root, ledger_relative)
    if not ledger_path.is_file():
        return (
            state,
            [_issue("review-ledger", "evidence ledger is missing: {}".format(ledger_relative))],
            False,
        )
    review_relative = artifacts.get("review")
    review_path = (
        safe_project_path(project_root, review_relative) if review_relative else None
    )
    if review_path is None or not review_path.is_file():
        return (
            state,
            [
                _issue(
                    "review-artifact",
                    "the phase review artifact is missing: {!r}".format(review_relative),
                )
            ],
            False,
        )
    tasks_path = safe_project_path(project_root, artifacts["tasks"])

    state_before = state_path.read_bytes()
    tasks_before = tasks_path.read_bytes()
    ledger_before = ledger_path.read_bytes()
    review_before = review_path.read_bytes()

    def restore() -> None:
        ledger_path.write_bytes(ledger_before)
        review_path.write_bytes(review_before)
        tasks_path.write_bytes(tasks_before)
        state_path.write_bytes(state_before)

    # Ledger, review artifact, index, state. No pair of these writes can be made
    # atomic against a process that dies between them, so the order is chosen by
    # which half-written outcome is safest. A ledger event and a review entry
    # without the gate describe a review that did not take effect: the gate
    # still blocks, `validate` is clean, and repeating the command completes it,
    # because repetition is a no-op only when the gate actually holds. The
    # reverse — a passed gate with no trail — is the exact outcome this
    # operation exists to make impossible.
    try:
        append_evidence_event(
            ledger_path,
            {
                "schema_version": 1,
                "task_id": task_id,
                "kind": "spec-compliance" if gate == SPEC_GATE else "code-quality",
                "actor": actor,
                "status": gate_status,
                "summary": (
                    "{} review by {} classified {} for {} at plan revision {} on "
                    "commit {}.".format(
                        "Spec compliance" if gate == SPEC_GATE else "Code quality",
                        report.get("reviewer"),
                        classification,
                        task_id,
                        revision,
                        report.get("reviewed_commit"),
                    )
                ),
                "source": report_relative,
                "acceptance_criteria": sorted(_mapping(report.get("acceptance"))),
                "details": {
                    "gate": gate,
                    "from": _mapping(state.get("gates")).get(gate),
                    "to": gate_status,
                    "classification": classification,
                    "task_id": task_id,
                    "plan_revision": revision,
                    "reviewer": report.get("reviewer"),
                    "executor": executor,
                    "report": report_relative,
                    "report_digest": report_digest,
                    "result": result_relative,
                    "reviewed_commit": report.get("reviewed_commit"),
                    "branch": identity["branch"],
                    "files_inspected": _listing(report.get("files_inspected")),
                    "evidence_inspected": _listing(report.get("evidence_inspected")),
                    "findings": findings,
                    "blockers_raised": [blocker["id"] for blocker in raised_blockers],
                    "blockers_resolved": resolved_blockers,
                    "task_transition": (
                        "{} -> {}".format(REVIEW_TASK_STATUS, task_status_target)
                        if task_status_target
                        else None
                    ),
                    "phase": _mapping(state.get("phase")).get("id"),
                },
                "recorded_at": recorded_at,
            },
        )
        review_path.write_bytes(
            review_before
            + _review_entry(gate=gate, record=record, recorded_at=recorded_at).encode(
                "utf-8"
            )
        )
        if task_status_target:
            update_task_status(tasks_path, str(task_id), task_status_target)
        write_frontmatter(state_path, updated, body)
    except Exception:
        restore()
        raise

    # Authoritative, and the only pass that sees every document in its final
    # form. Anything it finds means the application produced a state the kernel
    # would refuse to read, so all four go back and the operator is told.
    settled = [
        item["message"]
        for item in validate_state(updated, project_root)
        if item["severity"] == "error"
    ]
    if settled:
        restore()
        return (
            state,
            [
                _issue(
                    "review-result-state",
                    "applying the review produced an invalid state: {}".format(
                        "; ".join(settled)
                    ),
                )
            ],
            False,
        )

    return updated, [], True


def apply_spec_review(
    project_root: Path,
    *,
    contract_reference: str,
    task_id: Optional[str],
    result_reference: str,
    review_reference: str,
    actor: Optional[str] = None,
    write: bool = True,
) -> Tuple[Dict[str, Any], List[Dict[str, str]], bool]:
    """Validate an independent spec-compliance review and record its verdict."""

    project_root = project_root.expanduser().resolve()
    try:
        result_path, result_relative = _project_document(project_root, result_reference)
        review_path, review_relative = _project_document(project_root, review_reference)
        contract = load_contract(
            safe_project_path(project_root, contract_reference), task_id
        )
    except DocumentError as exc:
        return {}, [_issue("review-document", str(exc))], False

    result, _ = load_frontmatter(result_path)
    report, _ = load_frontmatter(review_path)

    return _apply(
        project_root,
        gate=SPEC_GATE,
        report=report,
        report_relative=review_relative,
        report_digest=_digest(review_path),
        result=result,
        result_relative=result_relative,
        document_issues=validate_spec_review(contract, result, report),
        actor=actor,
        write=write,
    )


def apply_quality_review(
    project_root: Path,
    *,
    result_reference: str,
    spec_review_reference: str,
    review_reference: str,
    actor: Optional[str] = None,
    write: bool = True,
) -> Tuple[Dict[str, Any], List[Dict[str, str]], bool]:
    """Validate an independent code-quality review and record its verdict.

    The spec review is passed by reference and checked against the one the
    ``spec_compliance`` record names. Accepting any passing spec document here
    would let a quality review be ordered behind a review of something else.
    """

    project_root = project_root.expanduser().resolve()
    try:
        result_path, result_relative = _project_document(project_root, result_reference)
        spec_path, spec_relative = _project_document(
            project_root, spec_review_reference
        )
        review_path, review_relative = _project_document(project_root, review_reference)
    except DocumentError as exc:
        return {}, [_issue("review-document", str(exc))], False

    result, _ = load_frontmatter(result_path)
    spec_report, _ = load_frontmatter(spec_path)
    report, _ = load_frontmatter(review_path)

    document_issues = validate_quality_review(result, spec_report, report)

    state_path = project_root / ".agent" / "STATE.md"
    if state_path.is_file():
        state, _ = _load_state(project_root)
        record = _mapping(_mapping(state.get("gate_records")).get(SPEC_GATE))
        if record.get("report") and record.get("report") != spec_relative:
            document_issues.append(
                _issue(
                    "review-spec-source",
                    "the applied spec review is {}, not {}".format(
                        record.get("report"), spec_relative
                    ),
                )
            )
        elif record.get("report_digest") and record.get("report_digest") != _digest(
            spec_path
        ):
            document_issues.append(
                _issue(
                    "review-spec-source",
                    "{} changed after it was applied; the quality review would be "
                    "ordered behind a document nobody approved".format(spec_relative),
                )
            )

    return _apply(
        project_root,
        gate=QUALITY_GATE,
        report=report,
        report_relative=review_relative,
        report_digest=_digest(review_path),
        result=result,
        result_relative=result_relative,
        document_issues=document_issues,
        actor=actor,
        write=write,
    )
