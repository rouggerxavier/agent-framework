"""Applying an independent review to the lifecycle.

The kernel could judge a review and could not record one. `validate-spec-review`
and `validate-quality-review` read a document and returned issues; the appliers
that moved the gates were called by nothing outside the tests; and `gate-status`
refuses both gates on purpose, naming those commands as their owners. Nothing
wrote them, so `spec_compliance` and `code_quality` stayed `pending` forever and
`reviewing -> verifying` had no way through that was not a hand edit of
`STATE.md` — the forged record the independence rules exist to prevent.

These tests cover the writer that closes the gap, and they end on the reported
shape: U3A under review at plan revision 2, a quality review that finds
something, the correction, and the transition that finally opens.
"""

from contextlib import redirect_stderr
from copy import deepcopy
from io import StringIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from kernel.runtime.cli import build_parser, main
from kernel.runtime.contracts import load_task_index
from kernel.runtime.documents import write_frontmatter
from kernel.runtime.gates import gate_issues
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.review_application import apply_quality_review, apply_spec_review
from kernel.runtime.state_machine import (
    compute_plan_fingerprint,
    reopen_review_gates,
    validate_state,
    validate_transition,
)
from tests.helpers import initialized_project, minimal_task, read_state, write_tasks


FEATURE = "feat/u3a-organization-setup"
PHASE_DIR = ".agent/phases/01-kernel"
RESULT = PHASE_DIR + "/U3A-result.md"
SPEC_REPORT = PHASE_DIR + "/U3A-spec-review.md"
QUALITY_REPORT = PHASE_DIR + "/U3A-quality-review.md"
QUALITY_REPORT_2 = PHASE_DIR + "/U3A-quality-review-2.md"
EXECUTOR = "implementer-1"

QUALITY_AREAS = [
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
]


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def _write(root: Path, relative: str, data, body: str = "# Document\n") -> None:
    write_frontmatter(root / relative, data, body)


def _reviewing_phase(root: Path, *, revision: int = 2, task_mode: str = None) -> str:
    """U3A under review at revision 2, exactly as reported.

    Self review passed, both independent gates pending, three later tasks still
    pending, and the execution bound to the feature branch.
    """

    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")
    _git(root, "checkout", "-b", FEATURE)

    initialized_project(root, with_phase=True)
    u3a = minimal_task("U3A", status="reviewing")
    if task_mode:
        u3a["execution_mode"] = task_mode
    write_tasks(
        root,
        [
            u3a,
            minimal_task("U3B1"),
            minimal_task("U3B2", depends_on=["U3A", "U3B1"]),
            minimal_task("U3C"),
        ],
    )

    decisions = root / ".agent" / "DECISIONS.md"
    decisions.write_text(
        decisions.read_text(encoding="utf-8")
        + "\n### DEC-TEST — Approve test plan\n\n- Status: accepted\n",
        encoding="utf-8",
    )

    state, body = read_state(root)
    state["status"] = "reviewing"
    state["phase"]["status"] = "reviewing"
    state["current_task"] = {
        "id": "U3A",
        "status": "reviewing",
        "execution": {
            "task_id": "U3A",
            "branch": FEATURE,
            "worktree": ".",
            "bound_at": "2026-08-03T00:00:00+00:00",
            "bound_by": "workflow-runner",
        },
    }
    state["gates"]["plan_quality"] = "passed"
    state["gates"]["self_review"] = "passed"
    state["gates"]["spec_compliance"] = "pending"
    state["gates"]["code_quality"] = "pending"
    state["blockers"] = []
    state["risk"] = {"level": "medium", "reasons": ["review application fixture"]}
    state["git"]["base_branch"] = "main"
    state["git"]["working_branch"] = FEATURE
    state["git"]["worktree"] = "."
    state["context"]["source_commit"] = None
    state["next_action"] = {"operation": "run-spec-review", "target": "U3A"}
    state["plan_revision"] = {
        "version": revision,
        "decision_id": "DEC-TEST",
        "fingerprint": compute_plan_fingerprint(state, root),
        "evidence": state["artifacts"]["evidence"] + "#plan-gate",
    }
    write_frontmatter(root / ".agent" / "STATE.md", state, body)

    _write(root, RESULT, _result())
    commit = _git(root, "rev-parse", "HEAD")
    _write(root, SPEC_REPORT, _spec_report(revision=revision, commit=commit))
    _write(root, QUALITY_REPORT, _quality_report(revision=revision, commit=commit))
    return commit


def _result():
    return {
        "schema_version": 1,
        "task": {
            "id": "U3A",
            "result": "implementation_complete",
            "executor": EXECUTOR,
            "starting_commit": "abc123",
        },
        "changes": {"files_modified": ["README.md"], "files_created": [], "files_deleted": []},
        "verification": {"commands_run": [], "runtime": [], "passed": [], "failed": []},
        "acceptance_evidence": {"AC-01": ["README.md"]},
        "scope": {"unexpected_changes": [], "deviations": []},
        "risks": {"discovered": []},
        "self_review": {"result": "PASS", "checklist": {}, "notes": []},
        "test_waiver": None,
        "review_notes": [],
    }


def _spec_report(*, revision: int, commit: str, classification: str = "PASS"):
    return {
        "schema_version": 1,
        "task_id": "U3A",
        "phase": "P1",
        "plan_revision": revision,
        "reviewed_commit": commit,
        "branch": FEATURE,
        "reviewer": "spec-reviewer",
        "classification": classification,
        "diff_inspected": True,
        "files_inspected": ["README.md"],
        "evidence_inspected": [RESULT],
        "acceptance": {"AC-01": {"status": "pass", "evidence": ["README.md"]}},
        "missing_requirements": [],
        "extra_scope": [],
        "invalid_evidence": [],
        "waiver_reviewed": False,
        "blockers": [],
        "notes": [],
    }


def _quality_report(
    *,
    revision: int,
    commit: str,
    classification: str = "APPROVED",
    reviewer: str = "quality-reviewer",
):
    return {
        "schema_version": 1,
        "task_id": "U3A",
        "phase": "P1",
        "plan_revision": revision,
        "reviewed_commit": commit,
        "branch": FEATURE,
        "reviewer": reviewer,
        "classification": classification,
        "diff_inspected": True,
        "files_inspected": ["README.md"],
        "evidence_inspected": [RESULT],
        "areas_checked": list(QUALITY_AREAS),
        "findings": [],
        "notes": [],
    }


def _blocking_spec(commit: str, *, revision: int = 2):
    report = _spec_report(revision=revision, commit=commit, classification="BLOCKED")
    report["acceptance"]["AC-01"] = {
        "status": "blocked",
        "evidence": ["README.md documents nothing"],
    }
    report["missing_requirements"] = ["REQ-TEST is not covered"]
    report["blockers"] = [
        {
            "id": "SPEC-U3A-01",
            "summary": "REQ-TEST is not covered",
            "evidence": ["README.md"],
        }
    ]
    return report


def _medium_finding(commit: str, *, revision: int = 2):
    report = _quality_report(
        revision=revision, commit=commit, classification="CHANGES_REQUIRED"
    )
    report["findings"] = [
        {
            "severity": "medium",
            "summary": "Setup path is duplicated",
            "evidence": ["README.md line 3"],
            "required_change": "Extract the duplicated setup path.",
        }
    ]
    return report


def _spec(root: Path, **overrides):
    arguments = {
        "contract_reference": PHASE_DIR + "/TASKS.md",
        "task_id": "U3A",
        "result_reference": RESULT,
        "review_reference": SPEC_REPORT,
        "actor": "reviewer-cli",
    }
    arguments.update(overrides)
    return apply_spec_review(root, **arguments)


def _quality(root: Path, **overrides):
    arguments = {
        "result_reference": RESULT,
        "spec_review_reference": SPEC_REPORT,
        "review_reference": QUALITY_REPORT,
        "actor": "reviewer-cli",
    }
    arguments.update(overrides)
    return apply_quality_review(root, **arguments)


def _codes(issues):
    return {issue["code"] for issue in issues}


def _statuses(root: Path):
    state, _ = read_state(root)
    index, _ = load_task_index(root / state["artifacts"]["tasks"])
    return {task["id"]: task["status"] for task in index["tasks"]}


def _bytes(root: Path):
    state, _ = read_state(root)
    return {
        name: (root / state["artifacts"][name]).read_bytes()
        for name in ("tasks", "evidence", "review")
    }, (root / ".agent" / "STATE.md").read_bytes()


class TheGapItself(unittest.TestCase):
    def test_gate_status_still_refuses_both_review_gates(self) -> None:
        """The refusal is the reason a dedicated writer has to exist."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            state, _ = read_state(root)
            for gate in ("spec_compliance", "code_quality"):
                issues = gate_issues(
                    state,
                    root,
                    gate=gate,
                    target="passed",
                    decision_id="DEC-TEST",
                    evidence=SPEC_REPORT,
                )
                self.assertTrue(
                    any("owned by" in issue for issue in issues),
                    "gate-status must keep refusing {}".format(gate),
                )

    def test_reviewing_to_verifying_is_closed_until_both_reviews_land(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            state, _ = read_state(root)
            self.assertEqual([], validate_state(state, root))
            self.assertEqual(
                {"spec-review", "quality-review"},
                _codes(validate_transition(state, "verifying", root)),
            )


class SpecReviewApplication(unittest.TestCase):
    def test_pass_records_the_gate_and_points_at_the_quality_review(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)

            state, issues, changed = _spec(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("passed", state["gates"]["spec_compliance"])
            # The phase and the task stay where they are: a spec review is not a
            # lifecycle move, and quality has not run.
            self.assertEqual("reviewing", state["status"])
            self.assertEqual("reviewing", state["current_task"]["status"])
            self.assertEqual("pending", state["gates"]["code_quality"])
            self.assertEqual(
                {"operation": "run-quality-review", "target": "U3A"},
                state["next_action"],
            )
            self.assertEqual("reviewing", _statuses(root)["U3A"])

            record = state["gate_records"]["spec_compliance"]
            self.assertEqual("passed", record["status"])
            self.assertEqual("PASS", record["classification"])
            self.assertEqual(2, record["plan_revision"])
            self.assertEqual("U3A", record["task_id"])
            self.assertEqual("spec-reviewer", record["reviewer"])
            self.assertEqual(EXECUTOR, record["executor"])
            self.assertEqual(SPEC_REPORT, record["report"])
            self.assertEqual(RESULT, record["result"])
            self.assertEqual(commit, record["reviewed_commit"])
            self.assertEqual(FEATURE, record["branch"])
            self.assertEqual(["README.md"], record["files_inspected"])
            self.assertEqual([RESULT], record["evidence_inspected"])
            self.assertTrue(record["report_digest"].startswith("sha256:"))
            self.assertTrue(record["at"])
            self.assertEqual("reviewer-cli", record["by"])

            persisted, _ = read_state(root)
            self.assertEqual(state["gates"], persisted["gates"])
            self.assertEqual([], validate_state(persisted, root))
            self.assertEqual(
                "run-quality-review",
                determine_next_operation(root)["next_operation"]["operation"],
            )

    def test_pass_with_notes_maps_to_its_own_gate_state(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            report = _spec_report(revision=2, commit=commit, classification="PASS_WITH_NOTES")
            report["notes"] = ["The naming could be clearer."]
            _write(root, SPEC_REPORT, report)

            state, issues, changed = _spec(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("passed_with_notes", state["gates"]["spec_compliance"])
            self.assertEqual(
                ["The naming could be clearer."],
                state["gate_records"]["spec_compliance"]["notes"],
            )
            # `passed_with_notes` satisfies the spec half of the guard; only
            # the quality half is still outstanding.
            self.assertEqual(
                {"quality-review"},
                _codes(validate_transition(state, "verifying", root)),
            )

    def test_blocked_raises_the_blocker_and_asks_for_a_correction(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            _write(root, SPEC_REPORT, _blocking_spec(commit))

            state, issues, changed = _spec(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("blocked", state["gates"]["spec_compliance"])
            # It records the verdict; it does not perform the transition.
            self.assertEqual("reviewing", state["status"])
            self.assertEqual("reviewing", state["current_task"]["status"])
            self.assertEqual(
                {"operation": "return-to-execution", "target": "U3A"},
                state["next_action"],
            )
            blocker = state["blockers"][0]
            self.assertEqual("SPEC-U3A-01", blocker["id"])
            self.assertEqual("spec-compliance", blocker["source"])
            self.assertEqual("U3A", blocker["task_id"])
            self.assertEqual(["README.md"], blocker["evidence"])
            self.assertEqual("open", blocker["status"])
            self.assertEqual(
                "return-to-execution",
                determine_next_operation(root)["next_operation"]["operation"],
            )
            # And the door the blocking verdict opens is the one that works.
            self.assertEqual([], validate_transition(state, "executing", root))

    def test_a_reviewer_who_executed_the_task_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            report = _spec_report(revision=2, commit=commit)
            report["reviewer"] = EXECUTOR
            _write(root, SPEC_REPORT, report)

            state, issues, changed = _spec(root)

            self.assertIn("review-independence", _codes(issues))
            self.assertFalse(changed)
            self.assertEqual("pending", state["gates"]["spec_compliance"])

    def test_a_review_of_another_task_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            report = _spec_report(revision=2, commit=commit)
            report["task_id"] = "U3B1"
            _write(root, SPEC_REPORT, report)

            state, issues, changed = _spec(root)

            self.assertIn("review-task", _codes(issues))
            self.assertFalse(changed)

    def test_a_review_of_an_older_commit_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            report = _spec_report(revision=2, commit="0" * 40)
            _write(root, SPEC_REPORT, report)

            state, issues, changed = _spec(root)

            self.assertIn("review-commit", _codes(issues))
            self.assertFalse(changed)
            self.assertEqual("pending", state["gates"]["spec_compliance"])

    def test_a_review_of_an_older_plan_revision_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=2)
            _write(root, SPEC_REPORT, _spec_report(revision=1, commit=commit))

            state, issues, changed = _spec(root)

            self.assertIn("review-revision", _codes(issues))
            self.assertFalse(changed)

    def test_a_review_with_no_revision_stamp_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            report = _spec_report(revision=2, commit=commit)
            report.pop("plan_revision")
            _write(root, SPEC_REPORT, report)

            self.assertIn("review-revision", _codes(_spec(root)[1]))

    def test_a_missing_report_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            (root / SPEC_REPORT).unlink()

            state, issues, changed = _spec(root)

            self.assertIn("review-document", _codes(issues))
            self.assertFalse(changed)

    def test_product_changes_the_reviewer_did_not_read_are_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            (root / "README.md").write_text("# project\n\nlater\n", encoding="utf-8")

            self.assertIn("review-worktree-moved", _codes(_spec(root)[1]))

    def test_check_runs_every_guard_and_writes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            before = _bytes(root)

            state, issues, changed = _spec(root, write=False)

            self.assertEqual([], issues)
            self.assertFalse(changed)
            self.assertEqual(before, _bytes(root))
            self.assertEqual("pending", state["gates"]["spec_compliance"])

    def test_applying_without_an_actor_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            self.assertIn("review-actor", _codes(_spec(root, actor=None)[1]))


class QualityReviewApplication(unittest.TestCase):
    def _through_spec(self, root: Path) -> str:
        commit = _reviewing_phase(root)
        _, issues, changed = _spec(root)
        self.assertEqual(([], True), (issues, changed))
        return commit

    def test_quality_before_spec_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)

            state, issues, changed = _quality(root)

            self.assertIn("review-order", _codes(issues))
            self.assertFalse(changed)
            self.assertEqual("pending", state["gates"]["code_quality"])

    def test_approved_marks_the_task_reviewed_and_opens_verifying(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)

            state, issues, changed = _quality(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("approved", state["gates"]["code_quality"])
            self.assertEqual("reviewed", state["current_task"]["status"])
            self.assertEqual("reviewed", _statuses(root)["U3A"])
            # The phase does not move. The transition is its own act.
            self.assertEqual("reviewing", state["status"])
            self.assertEqual(
                {"operation": "verify-phase", "target": "U3A"}, state["next_action"]
            )

            record = state["gate_records"]["code_quality"]
            self.assertEqual("approved", record["status"])
            self.assertEqual(2, record["plan_revision"])
            self.assertEqual("quality-reviewer", record["reviewer"])
            self.assertEqual(commit, record["reviewed_commit"])

            persisted, _ = read_state(root)
            self.assertEqual([], validate_state(persisted, root))
            self.assertEqual([], validate_transition(persisted, "verifying", root))

    def test_approved_with_notes_maps_to_its_own_gate_state(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)
            report = _quality_report(
                revision=2, commit=commit, classification="APPROVED_WITH_NOTES"
            )
            report["findings"] = [
                {
                    "severity": "low",
                    "summary": "A comment would help",
                    "evidence": ["README.md"],
                }
            ]
            _write(root, QUALITY_REPORT, report)

            state, issues, changed = _quality(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("approved_with_notes", state["gates"]["code_quality"])
            self.assertEqual([], validate_transition(state, "verifying", root))

    def test_an_approval_carrying_a_required_change_is_refused(self) -> None:
        """A `medium` that still demands work is not an approval."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)
            report = _quality_report(revision=2, commit=commit, classification="APPROVED")
            report["findings"] = [
                {
                    "severity": "medium",
                    "summary": "Setup path is duplicated",
                    "evidence": ["README.md line 3"],
                    "required_change": "Extract the duplicated setup path.",
                }
            ]
            _write(root, QUALITY_REPORT, report)

            state, issues, changed = _quality(root)

            self.assertIn("quality-approval-invalid", _codes(issues))
            self.assertFalse(changed)
            self.assertEqual("pending", state["gates"]["code_quality"])

    def test_rejected_is_not_a_verdict_this_framework_has(self) -> None:
        """No vocabulary is invented: `CHANGES_REQUIRED` is the rejection."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)
            _write(
                root,
                QUALITY_REPORT,
                _quality_report(revision=2, commit=commit, classification="REJECTED"),
            )

            state, issues, changed = _quality(root)

            codes = _codes(issues)
            self.assertIn("quality-classification", codes)
            self.assertIn("review-classification", codes)
            self.assertFalse(changed)
            self.assertEqual("pending", state["gates"]["code_quality"])

    def test_changes_required_records_the_finding_and_returns_the_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)
            _write(root, QUALITY_REPORT, _medium_finding(commit))

            state, issues, changed = _quality(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("changes_required", state["gates"]["code_quality"])
            # The spec approval is untouched: this review judged quality.
            self.assertEqual("passed", state["gates"]["spec_compliance"])
            self.assertEqual("reviewing", state["current_task"]["status"])
            self.assertEqual(
                {"operation": "return-to-execution", "target": "U3A"},
                state["next_action"],
            )
            blocker = state["blockers"][0]
            self.assertEqual("QUALITY-U3A-01", blocker["id"])
            self.assertEqual("medium", blocker["severity"])
            self.assertEqual("Extract the duplicated setup path.", blocker["required_change"])
            self.assertEqual("code-quality", blocker["source"])
            self.assertEqual(["README.md line 3"], blocker["evidence"])
            # Verifying stays shut; correction is the only way out.
            self.assertEqual(
                {"quality-review", "open-blockers"},
                _codes(validate_transition(state, "verifying", root)),
            )
            self.assertEqual([], validate_transition(state, "executing", root))

    def test_a_quality_review_ordered_behind_another_spec_document_is_refused(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)
            other = PHASE_DIR + "/U3A-spec-review-copy.md"
            _write(root, other, _spec_report(revision=2, commit=commit))

            issues = _quality(root, spec_review_reference=other)[1]

            self.assertIn("review-spec-source", _codes(issues))

    def test_a_spec_document_edited_after_it_was_applied_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = self._through_spec(root)
            report = _spec_report(revision=2, commit=commit)
            report["notes"] = ["added after the approval"]
            _write(root, SPEC_REPORT, report)

            self.assertIn("review-spec-source", _codes(_quality(root)[1]))


class Idempotence(unittest.TestCase):
    def test_repeating_the_same_application_changes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            _spec(root)
            first = _bytes(root)

            state, issues, changed = _spec(root)

            self.assertEqual([], issues)
            self.assertFalse(changed)
            self.assertEqual(first, _bytes(root))
            self.assertEqual("passed", state["gates"]["spec_compliance"])
            self.assertEqual([], state["gate_records"]["spec_compliance"]["history"])

    def test_repeating_an_applied_quality_review_changes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            _spec(root)
            _quality(root)
            first = _bytes(root)

            state, issues, changed = _quality(root)

            self.assertEqual([], issues)
            self.assertFalse(changed)
            self.assertEqual(first, _bytes(root))
            self.assertEqual("reviewed", _statuses(root)["U3A"])

    def test_a_different_verdict_on_the_same_gate_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            _spec(root)
            before = _bytes(root)
            _write(
                root,
                SPEC_REPORT,
                _spec_report(revision=2, commit=commit, classification="PASS_WITH_NOTES"),
            )

            state, issues, changed = _spec(root)

            self.assertIn("review-already-applied", _codes(issues))
            self.assertFalse(changed)
            self.assertEqual(before, _bytes(root))
            self.assertEqual("passed", state["gates"]["spec_compliance"])

    def test_a_different_reviewer_on_the_same_gate_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            _spec(root)
            report = _spec_report(revision=2, commit=commit)
            report["reviewer"] = "someone-else"
            _write(root, SPEC_REPORT, report)

            self.assertIn("review-already-applied", _codes(_spec(root)[1]))

    def test_a_landed_review_is_not_a_repeat_once_the_plan_moves_on(self) -> None:
        """Three revisions have to agree, not two."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=1)
            _write(root, SPEC_REPORT, _spec_report(revision=1, commit=commit))
            _spec(root)

            # The plan moves on without the gates being reopened — a hand-edited
            # state. The revision-1 approval must not be replayed as "already
            # applied" against revision 2.
            state, body = read_state(root)
            state["plan_revision"]["version"] = 2
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            issues = _spec(root)[1]

            self.assertIn("review-revision", _codes(issues))

    def test_an_edited_report_is_a_different_review(self) -> None:
        """The digest is what makes silent post-approval edits visible."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            _spec(root)
            report = _spec_report(revision=2, commit=commit)
            report["notes"] = ["quietly added"]
            _write(root, SPEC_REPORT, report)

            issues = _spec(root)[1]

            self.assertIn("review-already-applied", _codes(issues))
            self.assertIn("report_digest", issues[0]["message"])


class Atomicity(unittest.TestCase):
    """Every write boundary, injected, with all four documents checked."""

    def _fails_at(self, target: str, **kwargs) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            before = _bytes(root)

            with patch(
                "kernel.runtime.review_application." + target,
                side_effect=RuntimeError("injected"),
                **kwargs,
            ):
                with self.assertRaises(RuntimeError):
                    _spec(root)

            self.assertEqual(before, _bytes(root), "{} left a partial write".format(target))
            state, _ = read_state(root)
            self.assertEqual("pending", state["gates"]["spec_compliance"])
            self.assertNotIn("spec_compliance", state.get("gate_records", {}))
            self.assertEqual([], validate_state(state, root))

    def test_a_failed_ledger_write_leaves_nothing_behind(self) -> None:
        self._fails_at("append_evidence_event")

    def test_a_failed_review_artifact_write_leaves_nothing_behind(self) -> None:
        self._fails_at("_review_entry")

    def test_a_failed_index_write_leaves_nothing_behind(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            _spec(root)
            before = _bytes(root)

            with patch(
                "kernel.runtime.review_application.update_task_status",
                side_effect=RuntimeError("injected"),
            ):
                with self.assertRaises(RuntimeError):
                    _quality(root)

            self.assertEqual(before, _bytes(root))
            state, _ = read_state(root)
            self.assertEqual("pending", state["gates"]["code_quality"])
            self.assertEqual("reviewing", _statuses(root)["U3A"])

    def test_a_failed_state_write_leaves_nothing_behind(self) -> None:
        self._fails_at("write_frontmatter")

    def test_a_state_that_would_not_validate_is_rolled_back(self) -> None:
        """The authoritative pass runs after every document has moved."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            before = _bytes(root)
            real = validate_state
            calls = {"n": 0}

            def counted(state, root_, **kwargs):
                calls["n"] += 1
                if calls["n"] >= 3:
                    return [
                        {
                            "code": "injected",
                            "message": "injected settled failure",
                            "severity": "error",
                        }
                    ]
                return real(state, root_, **kwargs)

            with patch(
                "kernel.runtime.review_application.validate_state", side_effect=counted
            ):
                state, issues, changed = _spec(root)

            self.assertIn("review-result-state", _codes(issues))
            self.assertFalse(changed)
            self.assertEqual(before, _bytes(root))
            self.assertEqual("pending", state["gates"]["spec_compliance"])


class GateRecords(unittest.TestCase):
    def test_the_map_and_the_record_agree(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            _spec(root)
            _quality(root)
            state, _ = read_state(root)

            for gate in ("spec_compliance", "code_quality"):
                self.assertEqual(
                    state["gates"][gate], state["gate_records"][gate]["status"]
                )
                self.assertEqual(2, state["gate_records"][gate]["plan_revision"])
            self.assertEqual([], validate_state(state, root))

    def test_the_previous_review_becomes_history(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            _write(root, SPEC_REPORT, _blocking_spec(commit))
            _spec(root)
            blocked, _ = read_state(root)

            # The correction round: gates reopen, then the clean review lands.
            reopened = deepcopy(blocked)
            reopen_review_gates(
                reopened, revision=2, at="2026-08-03T01:00:00+00:00", actor="tests"
            )
            reopened["gates"]["self_review"] = "passed"
            reopened["blockers"] = [
                dict(blocker, status="resolved") for blocker in reopened["blockers"]
            ]
            write_frontmatter(root / ".agent" / "STATE.md", reopened, "# State\n")
            _write(root, SPEC_REPORT, _spec_report(revision=2, commit=commit))

            state, issues, changed = _spec(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            record = state["gate_records"]["spec_compliance"]
            self.assertEqual("passed", record["status"])
            statuses = [entry["status"] for entry in record["history"]]
            self.assertIn("blocked", statuses)

    def test_a_legacy_record_without_a_stamp_never_counts_as_applied(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            state, body = read_state(root)
            state.setdefault("gate_records", {})["spec_compliance"] = {
                "status": "passed",
                "decision": None,
                "evidence": "legacy.md",
                "at": "2025-01-01T00:00:00+00:00",
                "by": "legacy",
            }
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            # Readable — `validate` leaves unstamped records alone — but it
            # approves nothing: the gate map still says pending, and the review
            # has to be applied for real.
            self.assertEqual([], validate_state(state, root))
            applied, issues, changed = _spec(root)

            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("passed", applied["gates"]["spec_compliance"])
            record = applied["gate_records"]["spec_compliance"]
            self.assertEqual(2, record["plan_revision"])
            self.assertEqual(
                ["passed"], [entry["status"] for entry in record["history"]]
            )

    def test_a_review_granted_before_an_amendment_cannot_be_replayed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=1)
            _write(root, SPEC_REPORT, _spec_report(revision=1, commit=commit))
            _spec(root)

            # amend-plan reopens the gates and moves the revision on.
            state, body = read_state(root)
            reopen_review_gates(
                state, revision=2, at="2026-08-03T02:00:00+00:00", actor="planner"
            )
            state["plan_revision"]["version"] = 2
            state["gates"]["self_review"] = "passed"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            # The revision-1 approval is history and does not carry over.
            self.assertEqual("pending", state["gates"]["spec_compliance"])
            stale, issues, changed = _spec(root)
            self.assertIn("review-revision", _codes(issues))
            self.assertFalse(changed)

            # Only a review of revision 2 applies.
            _write(root, SPEC_REPORT, _spec_report(revision=2, commit=commit))
            applied, issues, changed = _spec(root)
            self.assertEqual([], issues)
            self.assertTrue(changed)
            record = applied["gate_records"]["spec_compliance"]
            self.assertEqual(2, record["plan_revision"])
            self.assertEqual(
                [1], [entry["plan_revision"] for entry in record["history"]]
            )


class TheReportedScenario(unittest.TestCase):
    """U3A at plan revision 2, end to end, including the finding."""

    def test_u3a_reaches_verifying_through_both_reviews_and_a_correction(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, revision=2)

            # 1. Spec review v2 passes with notes.
            report = _spec_report(revision=2, commit=commit, classification="PASS_WITH_NOTES")
            report["notes"] = ["Naming could be clearer."]
            _write(root, SPEC_REPORT, report)
            state, issues, changed = _spec(root)
            self.assertEqual(([], True), (issues, changed))
            self.assertEqual("passed_with_notes", state["gates"]["spec_compliance"])
            self.assertEqual("run-quality-review", state["next_action"]["operation"])

            # 2. Quality review v2 finds a medium and requires changes.
            _write(root, QUALITY_REPORT, _medium_finding(commit))
            state, issues, changed = _quality(root)
            self.assertEqual(([], True), (issues, changed))
            self.assertEqual("changes_required", state["gates"]["code_quality"])
            self.assertEqual("return-to-execution", state["next_action"]["operation"])
            self.assertEqual(["QUALITY-U3A-01"], [b["id"] for b in state["blockers"]])

            # 3. The task returns to execution. The finding survives; so does the
            #    binding; so does the review that found it.
            self.assertEqual([], validate_transition(state, "executing", root))
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "transition", "--to", "executing",
                        "--actor", "workflow-runner",
                        "--reason", "quality review required changes",
                    ]
                ),
            )
            state, _ = read_state(root)
            self.assertEqual("executing", state["status"])
            self.assertEqual("executing", _statuses(root)["U3A"])
            self.assertEqual(FEATURE, state["current_task"]["execution"]["branch"])
            self.assertEqual(["QUALITY-U3A-01"], [b["id"] for b in state["blockers"]])
            self.assertIn(
                "changes_required",
                [
                    entry["status"]
                    for entry in state["gate_records"]["code_quality"]["history"]
                ],
            )
            # A code correction that does not change the contract is not an
            # amendment: the revision stays at 2.
            self.assertEqual(2, state["plan_revision"]["version"])

            # 4. The correction is made and the task comes back through review.
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
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "transition", "--to", "reviewing",
                        "--actor", "workflow-runner", "--reason", "correction complete",
                    ]
                ),
            )

            # 5. Both reviews are earned again at revision 2 — re-entering
            #    execution retired them, so neither approval is inherited.
            state, _ = read_state(root)
            self.assertEqual("pending", state["gates"]["spec_compliance"])
            self.assertEqual("pending", state["gates"]["code_quality"])
            _write(root, SPEC_REPORT, _spec_report(revision=2, commit=commit))
            self.assertEqual(([], True), _spec(root)[1:])

            # 6. A new, independent quality review approves the corrected work
            #    and closes the finding it raised.
            _write(
                root,
                QUALITY_REPORT_2,
                _quality_report(revision=2, commit=commit, reviewer="quality-reviewer-2"),
            )
            state, issues, changed = _quality(root, review_reference=QUALITY_REPORT_2)
            self.assertEqual(([], True), (issues, changed))
            self.assertEqual("approved", state["gates"]["code_quality"])
            self.assertEqual("quality-reviewer-2", state["gate_records"]["code_quality"]["reviewer"])
            resolved = state["blockers"][0]
            self.assertEqual("QUALITY-U3A-01", resolved["id"])
            self.assertEqual("resolved", resolved["status"])
            self.assertEqual(QUALITY_REPORT_2, resolved["resolved_by_review"])

            # 7. Task reviewed, phase still reviewing, verifying now reachable.
            self.assertEqual("reviewed", state["current_task"]["status"])
            self.assertEqual("reviewed", _statuses(root)["U3A"])
            self.assertEqual("reviewing", state["status"])
            self.assertEqual("verify-phase", state["next_action"]["operation"])
            self.assertEqual([], validate_transition(state, "verifying", root))

            # 8. `validate` is clean and the kernel agrees with the record.
            self.assertEqual([], validate_state(state, root))
            decision = determine_next_operation(root)
            self.assertEqual([], decision["inconsistencies"])
            self.assertEqual("verify-phase", decision["next_operation"]["operation"])

            # 9. Nothing else moved.
            statuses = _statuses(root)
            self.assertEqual("pending", statuses["U3B1"])
            self.assertEqual("pending", statuses["U3B2"])
            self.assertEqual("pending", statuses["U3C"])

            # 10. And the transition, when taken, is a deliberate act that works.
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "transition", "--to", "verifying",
                        "--actor", "workflow-runner", "--reason", "both reviews applied",
                    ]
                ),
            )
            state, _ = read_state(root)
            self.assertEqual("verifying", state["status"])
            self.assertEqual("verifying", _statuses(root)["U3A"])


class CommandLine(unittest.TestCase):
    def _run(self, *arguments) -> int:
        return main(list(arguments))

    def test_the_commands_apply_and_repeat_cleanly(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)

            self.assertEqual(
                0,
                self._run(
                    "--project", str(root), "validate-spec-review",
                    "--contract", PHASE_DIR + "/TASKS.md", "--task-id", "U3A",
                    "--result", RESULT, "--review", SPEC_REPORT,
                    "--actor", "reviewer-cli",
                ),
            )
            state, _ = read_state(root)
            self.assertEqual("passed", state["gates"]["spec_compliance"])

            self.assertEqual(
                0,
                self._run(
                    "--project", str(root), "validate-quality-review",
                    "--result", RESULT, "--spec-review", SPEC_REPORT,
                    "--review", QUALITY_REPORT, "--actor", "reviewer-cli",
                ),
            )
            state, _ = read_state(root)
            self.assertEqual("approved", state["gates"]["code_quality"])
            self.assertEqual("reviewed", _statuses(root)["U3A"])

            before = _bytes(root)
            self.assertEqual(
                0,
                self._run(
                    "--project", str(root), "validate-quality-review",
                    "--result", RESULT, "--spec-review", SPEC_REPORT,
                    "--review", QUALITY_REPORT, "--actor", "reviewer-cli",
                ),
            )
            self.assertEqual(before, _bytes(root))

    def test_check_writes_nothing_and_a_bad_review_exits_two(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root)
            before = _bytes(root)

            self.assertEqual(
                0,
                self._run(
                    "--project", str(root), "validate-spec-review",
                    "--contract", PHASE_DIR + "/TASKS.md", "--task-id", "U3A",
                    "--result", RESULT, "--review", SPEC_REPORT,
                    "--actor", "reviewer-cli", "--check",
                ),
            )
            self.assertEqual(before, _bytes(root))

            _write(root, SPEC_REPORT, _spec_report(revision=1, commit=commit))
            self.assertEqual(
                2,
                self._run(
                    "--project", str(root), "validate-spec-review",
                    "--contract", PHASE_DIR + "/TASKS.md", "--task-id", "U3A",
                    "--result", RESULT, "--review", SPEC_REPORT,
                    "--actor", "reviewer-cli",
                ),
            )
            self.assertEqual(before, _bytes(root))

    def test_an_actor_is_required(self) -> None:
        """The command writes now, so it names who wrote."""

        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            build_parser().parse_args(
                [
                    "validate-spec-review", "--contract", "TASKS.md",
                    "--result", RESULT, "--review", SPEC_REPORT,
                ]
            )


class IntegratedReviewTests(unittest.TestCase):
    """One reviewer closes the round below `critical`.

    The point of these tests is that the reduction is real: a standard task
    reaches `verifying` after a single application, without a second reviewer
    reading the same diff and without a second document to write.
    """

    def test_one_review_carries_a_standard_task_to_verification(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root, task_mode="standard")

            state, issues, changed = _spec(root)
            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("passed", state["gates"]["spec_compliance"])
            self.assertEqual("not_required", state["gates"]["code_quality"])
            self.assertEqual("reviewed", state["current_task"]["status"])
            self.assertEqual("verify-phase", state["next_action"]["operation"])

            index, _ = load_task_index(root / PHASE_DIR / "TASKS.md")
            self.assertEqual(
                "reviewed",
                [task for task in index["tasks"] if task["id"] == "U3A"][0]["status"],
            )
            self.assertEqual([], validate_transition(state, "verifying", root))
            self.assertEqual(
                "verify-phase",
                determine_next_operation(root)["next_operation"]["operation"],
            )

    def test_the_second_gate_says_why_it_was_not_required(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root, task_mode="standard")
            state, _, _ = _spec(root)
            record = state["gate_records"]["code_quality"]
            self.assertEqual("not_required", record["status"])
            self.assertEqual(SPEC_REPORT, record["evidence"])
            self.assertIn("integrated review", record["note"])

    def test_a_critical_task_still_owes_the_second_reviewer(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _reviewing_phase(root)
            state, _, _ = _spec(root)
            self.assertEqual("pending", state["gates"]["code_quality"])
            self.assertEqual("reviewing", state["current_task"]["status"])
            self.assertEqual("run-quality-review", state["next_action"]["operation"])
            self.assertTrue(validate_transition(state, "verifying", root))

    def test_a_blocking_review_still_returns_a_standard_task_to_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            commit = _reviewing_phase(root, task_mode="standard")
            _write(root, SPEC_REPORT, _blocking_spec(commit))
            state, issues, changed = _spec(root)
            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("blocked", state["gates"]["spec_compliance"])
            self.assertEqual("pending", state["gates"]["code_quality"])
            self.assertEqual(
                "return-to-execution", state["next_action"]["operation"]
            )
            self.assertTrue(validate_transition(state, "verifying", root))


if __name__ == "__main__":
    unittest.main()
