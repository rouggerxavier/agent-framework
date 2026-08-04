"""Regression for the U3C bug: malformed evidence and a one-status resolve door.

Two things went wrong downstream, in a project called U3C. First, a
spec-compliance review classified ``BLOCKED`` was accepted even though one of
its findings carried evidence that was not a non-empty list — a string, which
reads as truthy and slipped past the old check. Second, ``resolve-finding``
only ever worked from the ``executing`` phase status, so a standard task with
several open findings raised by the same review round had to bounce back to
execution before the first one could be closed, and Standard mode had no way
to close a round of findings without also opening the door critical relies on
for a second independent review.

This module reproduces both, then reproduces the corrected round end to end:
a standard task under review with four open findings, each resolved from
either side of the return trip (``reviewing`` and ``executing``), each keeping
the original review document and blocker text, and the transition to
``verifying`` that follows without a second review.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.cli import main
from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.review_application import resolve_review_finding
from kernel.runtime.reviews import validate_spec_review
from kernel.runtime.state_machine import validate_state, validate_transition
from tests.helpers import read_state
from tests.test_review_application import (
    EXECUTOR,
    PHASE_DIR,
    RESULT,
    SPEC_REPORT,
    _codes,
    _reviewing_phase,
    _spec,
    _spec_report,
    _write,
)


CORRECTION = PHASE_DIR + "/U3C-correction.md"


def _correction_evidence(root: Path) -> str:
    (root / CORRECTION).write_text(
        "# Correction\n\n`pytest tests/test_setup.py` — 4 passed.\n", encoding="utf-8"
    )
    return CORRECTION


def _verify_task(root: Path, task_id: str) -> None:
    """Carry one task to ``verified`` in the state and in the contract index.

    The two are validated against each other, so the reported shape — a task
    that reached ``verified`` while its phase stayed in ``reviewing`` — only
    exists when both say so.
    """

    state, body = read_state(root)
    state["current_task"]["status"] = "verified"
    write_frontmatter(root / ".agent" / "STATE.md", state, body)

    tasks_path = root / state["artifacts"]["tasks"]
    index, index_body = load_frontmatter(tasks_path)
    for task in index["tasks"]:
        if task["id"] == task_id:
            task["status"] = "verified"
    write_frontmatter(tasks_path, index, index_body)


def _four_blockers():
    return [
        {
            "id": "SPEC-U3A-{:02d}".format(index),
            "summary": "duplicated setup path #{}".format(index),
            "evidence": ["README.md line {}".format(index)],
        }
        for index in range(1, 5)
    ]


class MalformedEvidenceIsRejected(unittest.TestCase):
    def test_string_evidence_on_a_blocked_finding_is_no_longer_accepted(self) -> None:
        """The exact shape that slipped past the old truthy check."""

        contract = {
            "id": "U3A",
            "acceptance": [{"id": "AC-01"}],
        }
        result = {"task": {"id": "U3A", "executor": "someone-else"}}
        report = {
            "task_id": "U3A",
            "reviewer": "spec-reviewer",
            "diff_inspected": True,
            "files_inspected": ["README.md"],
            "evidence_inspected": [RESULT],
            "classification": "BLOCKED",
            "acceptance": {"AC-01": {"status": "blocked", "evidence": ["README.md"]}},
            "missing_requirements": ["REQ-TEST is not covered"],
            "blockers": [
                {
                    "id": "SPEC-U3A-01",
                    "summary": "REQ-TEST is not covered",
                    # Malformed: a string, not a non-empty list. Truthy, and
                    # previously accepted.
                    "evidence": "README.md",
                }
            ],
        }

        issues = validate_spec_review(contract, result, report)

        self.assertIn("spec-blocker-evidence", _codes(issues))

    def test_an_empty_evidence_list_is_also_rejected(self) -> None:
        contract = {"id": "U3A", "acceptance": [{"id": "AC-01"}]}
        result = {"task": {"id": "U3A", "executor": "someone-else"}}
        report = {
            "task_id": "U3A",
            "reviewer": "spec-reviewer",
            "diff_inspected": True,
            "files_inspected": ["README.md"],
            "evidence_inspected": [RESULT],
            "classification": "BLOCKED",
            "acceptance": {"AC-01": {"status": "blocked", "evidence": ["README.md"]}},
            "missing_requirements": ["REQ-TEST is not covered"],
            "blockers": [
                {
                    "id": "SPEC-U3A-01",
                    "summary": "REQ-TEST is not covered",
                    "evidence": [],
                }
            ],
        }

        issues = validate_spec_review(contract, result, report)

        self.assertIn("spec-blocker-evidence", _codes(issues))


class FourFindingsResolvedFromEitherSideOfTheReturnTrip(unittest.TestCase):
    def test_standard_closes_all_four_without_a_second_review(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=2, task_mode="standard")

            spec_report = _spec_report(revision=2, commit=commit, classification="BLOCKED")
            spec_report["acceptance"]["AC-01"] = {
                "status": "blocked",
                "evidence": ["README.md documents nothing"],
            }
            spec_report["missing_requirements"] = ["REQ-TEST is not covered"]
            spec_report["blockers"] = _four_blockers()
            _write(root, SPEC_REPORT, spec_report)
            state, issues, changed = _spec(root)
            self.assertEqual(([], True), (issues, changed))

            blocker_ids = [
                b["id"] for b in state["blockers"] if b["source"] == "spec-compliance"
            ]
            self.assertEqual(4, len(blocker_ids))
            self.assertTrue(all(b["plan_revision"] == 2 for b in state["blockers"]))

            review_before = (root / state["artifacts"]["review"]).read_bytes()

            # Still in `reviewing`: resolve-finding must work from here now.
            self.assertEqual("reviewing", state["status"])
            evidence = _correction_evidence(root)
            for blocker_id in blocker_ids[:2]:
                resolved_state, issues, changed = resolve_review_finding(
                    root,
                    blocker_id=blocker_id,
                    evidence=evidence,
                    actor=EXECUTOR,
                    note="fixed in {}".format(blocker_id),
                )
                self.assertEqual([], issues)
                self.assertTrue(changed)

            # Return to execution and finish the round from there — the other
            # status resolve-finding must accept.
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "transition", "--to", "executing",
                        "--actor", "workflow-runner", "--reason", "closing the round",
                    ]
                ),
            )
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "task-status", "--task-id", "U3A",
                        "--to", "implementation_complete", "--actor", EXECUTOR,
                    ]
                ),
            )
            state, body = read_state(root)
            state["gates"]["self_review"] = "passed"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            for blocker_id in blocker_ids[2:]:
                resolved_state, issues, changed = resolve_review_finding(
                    root,
                    blocker_id=blocker_id,
                    evidence=evidence,
                    actor=EXECUTOR,
                    note="fixed in {}".format(blocker_id),
                )
                self.assertEqual([], issues)
                self.assertTrue(changed)

            state, _ = read_state(root)
            for blocker in state["blockers"]:
                if blocker["source"] != "spec-compliance":
                    continue
                self.assertEqual("resolved", blocker["status"])
                self.assertEqual("correction", blocker["resolution"])
                self.assertEqual(evidence, blocker["resolution_evidence"])
                self.assertEqual(EXECUTOR, blocker["resolved_by"])
                self.assertEqual(
                    "fixed in {}".format(blocker["id"]), blocker["note"]
                )
                # Original text preserved, nothing overwritten.
                self.assertTrue(blocker["summary"].startswith("duplicated setup path"))
                self.assertEqual(2, blocker["plan_revision"])

            # The original review document was never touched by resolve-finding
            # itself — it only appends its own entries.
            review_after = (root / state["artifacts"]["review"]).read_bytes()
            self.assertTrue(review_after.startswith(review_before))

            self.assertEqual([], validate_state(state, root))
            self.assertEqual([], validate_transition(state, "verifying", root))
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "transition", "--to", "verifying",
                        "--actor", "workflow-runner", "--reason", "all findings resolved",
                    ]
                ),
            )
            state, _ = read_state(root)
            self.assertEqual("verifying", state["status"])
            # No second independent review was ever recorded for spec_compliance.
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


class NextOperationReadsTheRoundAndNotOnlyTheVerdict(unittest.TestCase):
    """The second half of the U3C bug, in ``next_operation``.

    ``resolve-finding`` closes a standard round against the evidence of the
    correction and deliberately leaves ``gates.spec_compliance`` on ``blocked``:
    the verdict is the record of what the reviewer found, and rewriting it would
    erase the review. ``next_operation`` read that field alone, so a round whose
    every finding was resolved still derived ``return-to-execution`` — sending a
    finished task back to be re-implemented, and contradicting the
    ``verify-phase`` cursor ``resolve-finding`` had just written.
    """

    def _blocked_round(self, root: Path, *, task_mode: str = "standard"):
        commit = _reviewing_phase(root, revision=2, task_mode=task_mode)
        spec_report = _spec_report(revision=2, commit=commit, classification="BLOCKED")
        spec_report["acceptance"]["AC-01"] = {
            "status": "blocked",
            "evidence": ["README.md documents nothing"],
        }
        spec_report["missing_requirements"] = ["REQ-TEST is not covered"]
        spec_report["blockers"] = _four_blockers()
        _write(root, SPEC_REPORT, spec_report)
        state, issues, changed = _spec(root)
        self.assertEqual(([], True), (issues, changed))
        return state

    def test_the_u3c_shape_derives_verify_phase_without_an_inconsistency(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._blocked_round(root)
            self.assertEqual("blocked", state["gates"]["spec_compliance"])

            evidence = _correction_evidence(root)
            blocker_ids = [
                b["id"] for b in state["blockers"] if b["source"] == "spec-compliance"
            ]
            self.assertEqual(4, len(blocker_ids))
            for blocker_id in blocker_ids:
                _, issues, changed = resolve_review_finding(
                    root,
                    blocker_id=blocker_id,
                    evidence=evidence,
                    actor=EXECUTOR,
                    note="fixed in {}".format(blocker_id),
                )
                self.assertEqual([], issues)
                self.assertTrue(changed)

            # The reported shape: the task carried on to `verified` while the
            # phase stayed in `reviewing`, in the state and in the index alike.
            _verify_task(root, "U3A")

            state, _ = read_state(root)
            self.assertEqual("reviewing", state["status"])
            self.assertEqual("blocked", state["gates"]["spec_compliance"])
            self.assertEqual("verified", state["current_task"]["status"])
            self.assertTrue(
                all(
                    blocker["status"] == "resolved"
                    for blocker in state["blockers"]
                    if blocker["source"] == "spec-compliance"
                )
            )
            self.assertEqual(
                {"operation": "verify-phase", "target": "U3A"}, state["next_action"]
            )

            decision = determine_next_operation(root)

            self.assertEqual("verify-phase", decision["next_operation"]["operation"])
            self.assertEqual("U3A", decision["next_operation"]["target"])
            self.assertEqual([], decision["inconsistencies"])
            self.assertEqual([], decision["stale_next_action"])
            self.assertEqual([], decision["blocking_conditions"])

    def test_an_open_finding_still_sends_the_task_back_to_execution(self) -> None:
        """The guard the fix must not remove: one finding open is a round open."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._blocked_round(root)
            evidence = _correction_evidence(root)
            blocker_ids = [
                b["id"] for b in state["blockers"] if b["source"] == "spec-compliance"
            ]

            # Close every finding but the last.
            for blocker_id in blocker_ids[:-1]:
                _, issues, changed = resolve_review_finding(
                    root,
                    blocker_id=blocker_id,
                    evidence=evidence,
                    actor=EXECUTOR,
                    note="fixed in {}".format(blocker_id),
                )
                self.assertEqual([], issues)
                self.assertTrue(changed)

            decision = determine_next_operation(root)

            self.assertEqual(
                "return-to-execution", decision["next_operation"]["operation"]
            )

    def test_critical_still_owes_a_new_independent_review(self) -> None:
        """Critical closes a round through a review, never through a correction."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._blocked_round(root, task_mode="critical")
            blocker_ids = [
                b["id"] for b in state["blockers"] if b["source"] == "spec-compliance"
            ]
            evidence = _correction_evidence(root)

            # `resolve-finding` is closed to critical, so the findings can only
            # be marked resolved by writing them — which is what a project that
            # tried to shortcut the second review would do.
            state, body = read_state(root)
            for blocker in state["blockers"]:
                if blocker["id"] in blocker_ids:
                    blocker["status"] = "resolved"
                    blocker["resolution"] = "correction"
                    blocker["resolution_evidence"] = evidence
                    blocker["resolved_by"] = EXECUTOR
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            decision = determine_next_operation(root)

            self.assertEqual(
                "return-to-execution", decision["next_operation"]["operation"]
            )


if __name__ == "__main__":
    unittest.main()
