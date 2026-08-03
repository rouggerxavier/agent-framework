"""Closing a review round with the correction, instead of a second review.

Standard used to owe two full independent reviews for a single finding: one to
raise it and one to confirm the fix it had already specified. The round now
closes on the record of the correction — every finding resolved, each against
evidence — and `executing -> verifying` is the door. Critical keeps the second
review; fast never had a finding to close.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.cli import main
from kernel.runtime.documents import write_frontmatter
from kernel.runtime.execution_modes import mode_requirements
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.review_application import resolve_review_finding
from kernel.runtime.state_machine import validate_state, validate_transition
from tests.helpers import read_state
from tests.test_review_application import (
    EXECUTOR,
    PHASE_DIR,
    QUALITY_REPORT,
    SPEC_REPORT,
    _blocking_spec,
    _codes,
    _quality,
    _medium_finding,
    _reviewing_phase,
    _spec,
    _statuses,
    _write,
)


CORRECTION = PHASE_DIR + "/U3A-correction.md"


def _correction_evidence(root: Path) -> str:
    """The targeted test run that proves the correction, as a document."""

    (root / CORRECTION).write_text(
        "# Correction\n\n`pytest tests/test_setup.py` — 4 passed.\n", encoding="utf-8"
    )
    return CORRECTION


def _blocked_standard_round(root: Path) -> str:
    """A standard task whose single integrated review required changes."""

    commit = _reviewing_phase(root, revision=2, task_mode="standard")
    _write(root, SPEC_REPORT, _blocking_spec(commit))
    state, issues, changed = _spec(root)
    assert issues == [] and changed, issues
    assert state["gates"]["spec_compliance"] == "blocked"
    return commit


def _return_to_execution(root: Path) -> None:
    assert 0 == main(
        [
            "--project", str(root), "transition", "--to", "executing",
            "--actor", "workflow-runner", "--reason", "review required changes",
        ]
    )


def _implementation_complete(root: Path) -> None:
    assert 0 == main(
        [
            "--project", str(root), "task-status", "--task-id", "U3A",
            "--to", "implementation_complete", "--actor", EXECUTOR,
        ]
    )
    state, body = read_state(root)
    state["gates"]["self_review"] = "passed"
    write_frontmatter(root / ".agent" / "STATE.md", state, body)


class StandardApprovedFirstTime(unittest.TestCase):
    def test_one_review_still_takes_an_approved_task_to_verifying(self) -> None:
        """Nothing new is owed when the first review approves."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root, revision=2, task_mode="standard")
            state, issues, changed = _spec(root)

            self.assertEqual(([], True), (issues, changed))
            self.assertEqual("passed", state["gates"]["spec_compliance"])
            # The integrated review covers quality below critical.
            self.assertEqual("not_required", state["gates"]["code_quality"])
            self.assertEqual("reviewed", state["current_task"]["status"])
            self.assertEqual([], validate_transition(state, "verifying", root))


class StandardClosesItsOwnCorrection(unittest.TestCase):
    def test_a_finding_is_corrected_and_verified_without_a_second_review(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _blocked_standard_round(root)

            # The round returns the task to execution with the finding open.
            _return_to_execution(root)
            state, _ = read_state(root)
            self.assertEqual(["SPEC-U3A-01"], [b["id"] for b in state["blockers"]])
            self.assertEqual(
                "resolve-finding",
                determine_next_operation(root)["next_operation"]["operation"],
            )

            evidence = _correction_evidence(root)
            _implementation_complete(root)
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "resolve-finding",
                        "--blocker", "SPEC-U3A-01", "--evidence", evidence,
                        "--actor", EXECUTOR, "--note", "targeted tests re-run",
                    ]
                ),
            )

            state, _ = read_state(root)
            self.assertEqual([], validate_state(state, root))
            self.assertEqual("verify-phase", state["next_action"]["operation"])
            self.assertEqual([], validate_transition(state, "verifying", root))
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "transition", "--to", "verifying",
                        "--actor", "workflow-runner", "--reason", "finding corrected",
                    ]
                ),
            )
            state, _ = read_state(root)
            self.assertEqual("verifying", state["status"])
            self.assertEqual("verifying", _statuses(root)["U3A"])
            # No second review was recorded, and none is asked for.
            self.assertEqual("pending", state["gates"]["spec_compliance"])
            self.assertEqual(
                1,
                len(
                    [
                        entry
                        for entry in state["gate_records"]["spec_compliance"]["history"]
                        if entry["status"] == "blocked"
                    ]
                ),
            )

    def test_a_quality_changes_required_round_closes_the_same_way(self) -> None:
        """The other rejection the framework has, on the same path."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=2)
            self.assertEqual(([], True), _spec(root)[1:])
            _write(root, QUALITY_REPORT, _medium_finding(commit))
            self.assertEqual(([], True), _quality(root)[1:])

            _return_to_execution(root)
            # Reclassified to standard: the finding was one duplicated path.
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "set-execution-mode",
                        "--scope", "task", "--task-id", "U3A", "--to", "standard",
                        "--reason", "one localized duplication, no grave harm path",
                        "--actor", "workflow-runner",
                    ]
                ),
            )
            evidence = _correction_evidence(root)
            _implementation_complete(root)
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "resolve-finding",
                        "--blocker", "QUALITY-U3A-01", "--evidence", evidence,
                        "--actor", EXECUTOR,
                    ]
                ),
            )
            state, _ = read_state(root)
            self.assertEqual([], validate_transition(state, "verifying", root))


class StandardStaysBlockedWhileAFindingIsOpen(unittest.TestCase):
    def test_verification_is_refused_until_every_finding_is_resolved(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _blocked_standard_round(root)
            _return_to_execution(root)
            _implementation_complete(root)

            state, _ = read_state(root)
            codes = _codes(validate_transition(state, "verifying", root))
            self.assertIn("open-blockers", codes)
            self.assertIn("no-resolved-finding", codes)

            # And an unrelated open blocker keeps the door shut too.
            evidence = _correction_evidence(root)
            resolve_review_finding(
                root,
                blocker_id="SPEC-U3A-01",
                evidence=evidence,
                actor=EXECUTOR,
            )
            state, body = read_state(root)
            state["blockers"].append(
                {
                    "id": "SPEC-U3A-02",
                    "summary": "second finding",
                    "evidence": ["README.md"],
                    "status": "open",
                    "source": "spec-compliance",
                    "task_id": "U3A",
                }
            )
            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self.assertIn(
                "open-blockers", _codes(validate_transition(state, "verifying", root))
            )


class StandardDemandsTheCorrectionBeTested(unittest.TestCase):
    def test_a_resolution_without_evidence_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _blocked_standard_round(root)
            _return_to_execution(root)

            state, issues, changed = resolve_review_finding(
                root,
                blocker_id="SPEC-U3A-01",
                evidence=PHASE_DIR + "/never-written.md",
                actor=EXECUTOR,
            )
            self.assertIn("finding-evidence", _codes(issues))
            self.assertFalse(changed)

    def test_verification_is_refused_while_the_correction_is_incomplete(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _blocked_standard_round(root)
            _return_to_execution(root)
            evidence = _correction_evidence(root)
            resolve_review_finding(
                root, blocker_id="SPEC-U3A-01", evidence=evidence, actor=EXECUTOR
            )

            state, _ = read_state(root)
            codes = _codes(validate_transition(state, "verifying", root))
            self.assertIn("implementation-incomplete", codes)
            self.assertIn("self-review", codes)

    def test_a_finding_resolved_without_evidence_cannot_open_verification(self) -> None:
        """The guard reads the record, not the command that wrote it."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _blocked_standard_round(root)
            _return_to_execution(root)
            _implementation_complete(root)
            state, body = read_state(root)
            state["blockers"][0]["status"] = "resolved"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            self.assertIn(
                "finding-resolution-evidence",
                _codes(validate_transition(state, "verifying", root)),
            )


class CriticalKeepsTheSecondReview(unittest.TestCase):
    def test_a_correction_cannot_close_a_critical_round(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=2, task_mode="critical")
            _write(root, SPEC_REPORT, _blocking_spec(commit))
            self.assertEqual(([], True), _spec(root)[1:])
            _return_to_execution(root)
            evidence = _correction_evidence(root)

            state, issues, changed = resolve_review_finding(
                root, blocker_id="SPEC-U3A-01", evidence=evidence, actor=EXECUTOR
            )
            self.assertIn("finding-mode", _codes(issues))
            self.assertFalse(changed)

            _implementation_complete(root)
            state, body = read_state(root)
            state["blockers"][0].update(
                {"status": "resolved", "resolution_evidence": evidence}
            )
            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self.assertIn(
                "correction-requires-review",
                _codes(validate_transition(state, "verifying", root)),
            )
            # The review door is the one that is open.
            self.assertEqual([], validate_transition(state, "reviewing", root))


class FastGainsNothing(unittest.TestCase):
    def test_fast_still_has_no_independent_review_and_no_shortcut(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root, revision=2, task_mode="fast")
            self.assertEqual(0, mode_requirements("fast")["independent_reviews"])

            # Fast owes no independent review, so nothing ever raises a finding
            # for it — and with no finding there is no round to close this way.
            state, body = read_state(root)
            state["status"] = "executing"
            state["phase"]["status"] = "executing"
            state["current_task"]["status"] = "implementation_complete"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            main(
                [
                    "--project", str(root), "task-status", "--task-id", "U3A",
                    "--to", "executing", "--actor", EXECUTOR,
                ]
            )
            main(
                [
                    "--project", str(root), "task-status", "--task-id", "U3A",
                    "--to", "implementation_complete", "--actor", EXECUTOR,
                ]
            )
            state, _ = read_state(root)
            self.assertIn(
                "no-resolved-finding",
                _codes(validate_transition(state, "verifying", root)),
            )
            self.assertEqual([], validate_transition(state, "reviewing", root))


class TheHistorySurvives(unittest.TestCase):
    def test_review_finding_and_correction_are_all_still_readable(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _blocked_standard_round(root)
            _return_to_execution(root)
            evidence = _correction_evidence(root)
            _implementation_complete(root)
            resolve_review_finding(
                root,
                blocker_id="SPEC-U3A-01",
                evidence=evidence,
                actor=EXECUTOR,
                note="targeted tests re-run",
            )

            state, _ = read_state(root)
            blocker = state["blockers"][0]
            # The finding is answered, not erased.
            self.assertEqual("resolved", blocker["status"])
            self.assertEqual("REQ-TEST is not covered", blocker["summary"])
            self.assertEqual("spec-compliance", blocker["source"])
            self.assertEqual(evidence, blocker["resolution_evidence"])
            self.assertEqual("correction", blocker["resolution"])
            self.assertEqual(EXECUTOR, blocker["resolved_by"])

            record = state["gate_records"]["spec_compliance"]
            self.assertIn("blocked", [entry["status"] for entry in record["history"]])

            review = (root / state["artifacts"]["review"]).read_text(encoding="utf-8")
            self.assertIn("SPEC-U3A-01", review)
            self.assertIn("finding resolved", review)
            ledger = (root / state["artifacts"]["evidence"]).read_text(encoding="utf-8")
            self.assertIn("correction", ledger)
            self.assertIn(evidence, ledger)


if __name__ == "__main__":
    unittest.main()
