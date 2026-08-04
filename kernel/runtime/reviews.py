"""Independent spec-compliance and code-quality review validation.

These functions answer one question: *is this a well-formed, independent review
of this contract and this result?* They read documents and return issues; they
never read the persisted state and never write anything.

Applying a validated review — moving the gate, stamping the record with the plan
revision it was granted under, recording the blockers and the ledger event — is
``review_application.py``, which owns the questions this module cannot answer:
whether the review describes the work that is actually under way, at the
revision and commit that actually exist.
"""

from __future__ import annotations

from typing import Any, Dict, List

QUALITY_AREAS = {
    "bugs",
    "readability",
    "local-standards",
    "duplication",
    "security",
    "performance",
    "observability",
    "error-handling",
    "test-quality",
    "maintainability",
    "compatibility",
}


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def _executor(result: Dict[str, Any]) -> Any:
    task = result.get("task", {})
    return task.get("executor") if isinstance(task, dict) else None


def _validate_independence(
    result: Dict[str, Any], report: Dict[str, Any]
) -> List[Dict[str, str]]:
    reviewer = report.get("reviewer")
    issues: List[Dict[str, str]] = []
    if not reviewer:
        issues.append(_issue("reviewer", "reviewer identity is required"))
    if reviewer and reviewer == _executor(result):
        issues.append(
            _issue("review-independence", "reviewer must differ from task executor")
        )
    if report.get("diff_inspected") is not True:
        issues.append(_issue("diff-inspection", "reviewer must inspect the complete diff"))
    files = report.get("files_inspected")
    if not isinstance(files, list) or not files:
        issues.append(_issue("code-inspection", "reviewer must list inspected files"))
    evidence = report.get("evidence_inspected")
    if not isinstance(evidence, list) or not evidence:
        issues.append(
            _issue("evidence-inspection", "reviewer must inspect direct evidence")
        )
    return issues


def validate_spec_review(
    contract: Dict[str, Any],
    result: Dict[str, Any],
    report: Dict[str, Any],
) -> List[Dict[str, str]]:
    issues = _validate_independence(result, report)
    if report.get("task_id") != contract.get("id"):
        issues.append(_issue("review-task", "spec review task_id must match contract"))
    classification = report.get("classification")
    if classification not in {"PASS", "PASS_WITH_NOTES", "BLOCKED"}:
        issues.append(_issue("spec-classification", "invalid spec classification"))

    acceptance = report.get("acceptance", {})
    if not isinstance(acceptance, dict):
        issues.append(_issue("spec-acceptance", "acceptance must be an object"))
        acceptance = {}
    blocked_criteria = []
    for criterion in contract.get("acceptance", []):
        criterion_id = criterion.get("id") if isinstance(criterion, dict) else None
        entry = acceptance.get(criterion_id)
        if not isinstance(entry, dict) or entry.get("status") not in {"pass", "blocked"}:
            issues.append(
                _issue(
                    "spec-criterion",
                    "{} must have pass/blocked status and evidence".format(criterion_id),
                )
            )
            continue
        criterion_evidence = entry.get("evidence")
        if not isinstance(criterion_evidence, list) or not criterion_evidence:
            issues.append(
                _issue(
                    "spec-criterion-evidence",
                    "{} evidence must be a non-empty list".format(criterion_id),
                )
            )
        if entry.get("status") == "blocked":
            blocked_criteria.append(criterion_id)

    blocking_lists = (
        "missing_requirements",
        "extra_scope",
        "invalid_evidence",
        "blockers",
    )
    has_blocking_content = bool(blocked_criteria)
    for field in blocking_lists:
        value = report.get(field, [])
        if not isinstance(value, list):
            issues.append(_issue("spec-list", "{} must be an array".format(field)))
        elif value:
            has_blocking_content = True

    if classification == "BLOCKED" and not has_blocking_content:
        issues.append(_issue("spec-blocker", "BLOCKED requires a concrete blocker"))
    if classification == "BLOCKED":
        for blocker in report.get("blockers", []):
            if not (
                isinstance(blocker, dict)
                and blocker.get("id")
                and blocker.get("summary")
            ):
                issues.append(
                    _issue(
                        "spec-blocker-shape",
                        "each blocker requires id, summary, and evidence",
                    )
                )
                continue
            blocker_evidence = blocker.get("evidence")
            if not isinstance(blocker_evidence, list) or not blocker_evidence:
                issues.append(
                    _issue(
                        "spec-blocker-evidence",
                        "blocker {} evidence must be a non-empty list".format(
                            blocker.get("id")
                        ),
                    )
                )
    if classification in {"PASS", "PASS_WITH_NOTES"} and has_blocking_content:
        issues.append(
            _issue("spec-pass-invalid", "passing review cannot contain blocking findings")
        )
    if result.get("test_waiver") is not None and report.get("waiver_reviewed") is not True:
        issues.append(_issue("waiver-review", "test waiver must be reviewed"))
    return issues


def validate_quality_review(
    result: Dict[str, Any],
    spec_report: Dict[str, Any],
    report: Dict[str, Any],
) -> List[Dict[str, str]]:
    issues = _validate_independence(result, report)
    result_task = result.get("task", {})
    if not isinstance(result_task, dict) or report.get("task_id") != result_task.get("id"):
        issues.append(_issue("review-task", "quality review task_id must match result"))
    if spec_report.get("classification") not in {"PASS", "PASS_WITH_NOTES"}:
        issues.append(
            _issue("quality-order", "quality review requires passing spec review")
        )
    classification = report.get("classification")
    if classification not in {
        "APPROVED",
        "APPROVED_WITH_NOTES",
        "CHANGES_REQUIRED",
    }:
        issues.append(_issue("quality-classification", "invalid quality classification"))
    findings = report.get("findings")
    if not isinstance(findings, list):
        issues.append(_issue("quality-findings", "findings must be an array"))
        findings = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        if item.get("severity") or item.get("required_change"):
            finding_evidence = item.get("evidence")
            if not isinstance(finding_evidence, list) or not finding_evidence:
                issues.append(
                    _issue(
                        "quality-finding-evidence",
                        "finding {} evidence must be a non-empty list".format(
                            item.get("summary") or item.get("id") or "?"
                        ),
                    )
                )
    actionable = [
        item
        for item in findings
        if isinstance(item, dict)
        and item.get("severity")
        and isinstance(item.get("evidence"), list)
        and item.get("evidence")
        and item.get("required_change")
    ]
    if classification == "CHANGES_REQUIRED" and not actionable:
        issues.append(
            _issue(
                "quality-change-evidence",
                "CHANGES_REQUIRED needs an evidenced actionable finding",
            )
        )
    # The mirror of `spec-pass-invalid`, and it was missing. A finding that
    # names a `required_change` is a change that has not been made; approving
    # while carrying one records the gate as satisfied and leaves the demand
    # with nothing to enforce it. Notes without a required change stay legal —
    # that is what `APPROVED_WITH_NOTES` is for.
    if classification in {"APPROVED", "APPROVED_WITH_NOTES"}:
        unmet = [
            item
            for item in findings
            if isinstance(item, dict) and item.get("required_change")
        ]
        if unmet:
            issues.append(
                _issue(
                    "quality-approval-invalid",
                    "an approving review cannot carry a required change: {}".format(
                        "; ".join(
                            str(item.get("summary") or item.get("required_change"))
                            for item in unmet
                        )
                    ),
                )
            )
    areas = report.get("areas_checked")
    if not isinstance(areas, list):
        issues.append(_issue("quality-areas", "areas_checked must be an array"))
    else:
        missing_areas = sorted(QUALITY_AREAS - set(areas))
        if missing_areas:
            issues.append(
                _issue(
                    "quality-areas",
                    "quality review omitted: {}".format(", ".join(missing_areas)),
                )
            )
    return issues


# `apply_spec_review` and `apply_quality_review` used to live here as in-memory
# state transforms. They were reachable from nothing but the tests, kept no
# record, replaced the blocker list outright and moved the lifecycle themselves.
# Both names now belong to `review_application`, which applies a review to the
# documents on disk. They are deliberately not re-exported: a second `apply_*`
# that writes nothing is the ambiguity this split removes.
