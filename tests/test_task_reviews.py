from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.evidence import append_evidence_event
from kernel.runtime.reviews import validate_quality_review, validate_spec_review
from kernel.runtime.state_machine import validate_transition
from tests.helpers import (
    full_contract,
    full_result,
    initialized_project,
    minimal_task,
    set_lifecycle,
    write_tasks,
)


def passing_spec_review():
    return {
        "task_id": "P1-T03",
        "reviewer": "spec-reviewer",
        "classification": "PASS",
        "diff_inspected": True,
        "files_inspected": ["app/mapper.py", "tests/test_mapper.py"],
        "evidence_inspected": ["test output", "diff"],
        "acceptance": {
            "AC-01": {"status": "pass", "evidence": ["test_known_values"]},
            "AC-02": {"status": "pass", "evidence": ["test_unknown_traceable"]},
        },
        "missing_requirements": [],
        "extra_scope": [],
        "invalid_evidence": [],
        "waiver_reviewed": False,
        "blockers": [],
    }


def passing_quality_review():
    return {
        "task_id": "P1-T03",
        "reviewer": "quality-reviewer",
        "classification": "APPROVED",
        "diff_inspected": True,
        "files_inspected": ["app/mapper.py", "tests/test_mapper.py"],
        "evidence_inspected": ["test output", "diff"],
        "areas_checked": [
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
        ],
        "findings": [],
    }


class TaskReviewTests(unittest.TestCase):
    def test_spec_review_blocks_missing_requirement(self) -> None:
        report = passing_spec_review()
        report["classification"] = "BLOCKED"
        report["acceptance"]["AC-02"] = {
            "status": "blocked",
            "evidence": ["unknown values are dropped in app/mapper.py"],
        }
        report["missing_requirements"] = ["REQ-004 traceability missing"]
        report["blockers"] = [
            {
                "id": "SPEC-1",
                "summary": "REQ-004 missing",
                "evidence": ["app/mapper.py drops unknown values"],
            }
        ]
        # Applying this verdict is `review_application`'s job and is covered in
        # `test_review_application`; validation is what this module owns.
        self.assertEqual(
            [], validate_spec_review(full_contract(), full_result(), report)
        )

    def test_passing_spec_cannot_hide_missing_requirement(self) -> None:
        report = passing_spec_review()
        report["missing_requirements"] = ["REQ-004"]
        issues = validate_spec_review(full_contract(), full_result(), report)
        self.assertIn("spec-pass-invalid", {item["code"] for item in issues})

    def test_code_quality_changes_required_returns_to_executor(self) -> None:
        report = passing_quality_review()
        report["classification"] = "CHANGES_REQUIRED"
        report["findings"] = [
            {
                "severity": "high",
                "summary": "Unhandled value",
                "evidence": ["app/mapper.py line 10"],
                "required_change": "Handle the value explicitly.",
            }
        ]
        self.assertEqual(
            [],
            validate_quality_review(full_result(), passing_spec_review(), report),
        )

    def test_correction_must_return_through_review(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task("P1-T03", status="implementation_complete")])
            set_lifecycle(state, "executing")
            state["current_task"] = {
                "id": "P1-T03",
                "status": "implementation_complete",
            }
            state["gates"]["self_review"] = "passed"
            state["gates"]["spec_compliance"] = "pending"
            state["gates"]["code_quality"] = "pending"
            state["blockers"] = []
            self.assertEqual([], validate_transition(state, "reviewing", root))

    def test_approval_can_be_recorded_as_evidence(self) -> None:
        with TemporaryDirectory() as temporary:
            ledger = Path(temporary) / "EVIDENCE.md"
            ledger.write_text("# Evidence Ledger\n", encoding="utf-8")
            event = append_evidence_event(
                ledger,
                {
                    "task_id": "P1-T03",
                    "kind": "spec-compliance",
                    "actor": "spec-reviewer",
                    "status": "passed",
                    "summary": "All acceptance criteria passed.",
                    "source": "spec-compliance-review.md",
                    "acceptance_criteria": ["AC-01", "AC-02"],
                },
            )
            self.assertEqual("passed", event["status"])
            content = ledger.read_text(encoding="utf-8")
            self.assertIn('"kind": "spec-compliance"', content)
            self.assertIn('"AC-02"', content)

    def test_quality_review_requires_passing_spec_first(self) -> None:
        spec = passing_spec_review()
        spec["classification"] = "BLOCKED"
        issues = validate_quality_review(full_result(), spec, passing_quality_review())
        self.assertIn("quality-order", {item["code"] for item in issues})


if __name__ == "__main__":
    unittest.main()
