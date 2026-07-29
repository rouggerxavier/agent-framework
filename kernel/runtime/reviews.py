"""Independent spec-compliance and code-quality review validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from .documents import DocumentError

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
        if not entry.get("evidence"):
            issues.append(
                _issue("spec-criterion-evidence", "{} lacks evidence".format(criterion_id))
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
                and blocker.get("evidence")
            ):
                issues.append(
                    _issue(
                        "spec-blocker-shape",
                        "each blocker requires id, summary, and evidence",
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
    if classification == "CHANGES_REQUIRED":
        actionable = [
            item
            for item in findings
            if isinstance(item, dict)
            and item.get("severity")
            and item.get("evidence")
            and item.get("required_change")
        ]
        if not actionable:
            issues.append(
                _issue(
                    "quality-change-evidence",
                    "CHANGES_REQUIRED needs an evidenced actionable finding",
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


def apply_spec_review(
    state: Dict[str, Any], report: Dict[str, Any]
) -> Tuple[Dict[str, Any], str]:
    updated = deepcopy(state)
    classification = report.get("classification")
    if classification == "BLOCKED":
        updated["gates"]["spec_compliance"] = "blocked"
        updated["gates"]["code_quality"] = "pending"
        updated["current_task"]["status"] = "executing"
        updated["status"] = "executing"
        updated["phase"]["status"] = "executing"
        updated["blockers"] = list(report.get("blockers", []))
        return updated, "executing"
    if classification not in {"PASS", "PASS_WITH_NOTES"}:
        raise DocumentError("cannot apply invalid spec review")
    updated["gates"]["spec_compliance"] = (
        "passed" if classification == "PASS" else "passed_with_notes"
    )
    return updated, "reviewing"


def apply_quality_review(
    state: Dict[str, Any], report: Dict[str, Any]
) -> Tuple[Dict[str, Any], str]:
    updated = deepcopy(state)
    classification = report.get("classification")
    if classification == "CHANGES_REQUIRED":
        updated["gates"]["code_quality"] = "changes_required"
        updated["gates"]["spec_compliance"] = "pending"
        updated["current_task"]["status"] = "executing"
        updated["status"] = "executing"
        updated["phase"]["status"] = "executing"
        updated["blockers"] = [
            {
                "id": "QUALITY-{}".format(updated["current_task"].get("id")),
                "summary": item.get("summary", "quality change required"),
                "evidence": item.get("evidence", []),
            }
            for item in report.get("findings", [])
            if isinstance(item, dict)
        ]
        return updated, "executing"
    if classification not in {"APPROVED", "APPROVED_WITH_NOTES"}:
        raise DocumentError("cannot apply invalid quality review")
    updated["gates"]["code_quality"] = (
        "approved" if classification == "APPROVED" else "approved_with_notes"
    )
    updated["current_task"]["status"] = "reviewed"
    return updated, "verifying"
