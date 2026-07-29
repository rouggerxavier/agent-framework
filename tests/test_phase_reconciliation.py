from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.documents import load_frontmatter
from kernel.runtime.reconcile import reconcile_phase
from kernel.runtime.state_machine import validate_state, validate_transition
from tests.helpers import (
    FRAMEWORK_ROOT,
    initialized_project,
    minimal_task,
    read_state,
    set_lifecycle,
    write_state,
    write_tasks,
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(root),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _repository(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")


def _executed_phase(root: Path, *, statuses=("verified", "verified")) -> None:
    """A phase whose work is finished and committed, executing an earlier task."""
    initialized_project(root, with_phase=True)
    write_tasks(
        root,
        [
            minimal_task("P1-T01", status=statuses[0]),
            minimal_task("P1-T02", status=statuses[1], depends_on=["P1-T01"]),
        ],
    )
    state, _ = read_state(root)
    set_lifecycle(state, "executing")
    state["current_task"] = {"id": "P1-T01", "status": statuses[0]}
    write_state(root, state)
    decisions = root / state["artifacts"]["decisions"]
    decisions.write_text(
        decisions.read_text(encoding="utf-8")
        + "\n## DEC-RECONCILE — Reconcile the executed phase\n\n- Status: accepted\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "phase work")


def _reconcile(root: Path, **overrides):
    arguments = {
        "phase_id": "P1",
        "phase_name": "Kernel",
        "slug": "01-kernel",
        "decision_id": "DEC-RECONCILE",
        "evidence": ".agent/phases/01-kernel/EVIDENCE.md#reconciliation",
        "version": 2,
        "actor": "reconciliation",
    }
    arguments.update(overrides)
    return reconcile_phase(root, **arguments)


class PhaseReconciliationTests(unittest.TestCase):
    def test_executed_phase_lands_on_verifying_with_a_resealed_plan(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root)

            state, issues = _reconcile(root)
            self.assertEqual([], issues)
            self.assertEqual("verifying", state["status"])
            self.assertEqual("verifying", state["phase"]["status"])
            self.assertEqual({"id": "P1-T02", "status": "verified"}, state["current_task"])
            self.assertEqual(2, state["plan_revision"]["version"])
            self.assertTrue(state["plan_revision"]["reconciled"])
            self.assertEqual(
                {"operation": "verify-phase", "target": "P1"}, state["next_action"]
            )

            persisted, _ = load_frontmatter(root / ".agent" / "STATE.md")
            self.assertEqual("verifying", persisted["status"])
            # Grounding freshness is the caller's business; the reconciled state
            # itself must raise nothing.
            codes = {
                issue["code"]
                for issue in validate_state(persisted, root)
                if issue["code"] != "stale-context"
            }
            self.assertEqual(set(), codes)

    def test_shipping_gate_still_decides_after_reconciliation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root)
            _reconcile(root)

            state, _ = read_state(root)
            state["gates"]["acceptance"] = "pending"
            codes = {
                issue["code"] for issue in validate_transition(state, "ready_to_ship", root)
            }
            self.assertIn("acceptance-evidence", codes)

    def test_unfinished_work_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root, statuses=("verified", "executing"))
            _, issues = _reconcile(root)
            self.assertTrue(any("unfinished: P1-T02" in issue for issue in issues))
            persisted, _ = load_frontmatter(root / ".agent" / "STATE.md")
            self.assertEqual("executing", persisted["status"])

    def test_uncommitted_product_changes_are_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root)
            (root / "app.py").write_text("print('unfinished')\n", encoding="utf-8")
            _, issues = _reconcile(root)
            self.assertTrue(any("uncommitted changes" in issue for issue in issues))

    def test_unrecorded_decision_and_missing_evidence_are_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root)
            _, issues = _reconcile(root, decision_id="DEC-ABSENT")
            self.assertTrue(any("DEC-ABSENT" in issue for issue in issues))
            _, issues = _reconcile(root, evidence="does/not/exist.md#anchor")
            self.assertTrue(any("evidence file is missing" in issue for issue in issues))

    def test_open_blocker_and_stale_revision_are_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root)

            _, issues = _reconcile(root, version=1)
            self.assertTrue(any("plan revision must increase" in issue for issue in issues))

            state, _ = read_state(root)
            state["blockers"] = [
                {
                    "id": "BLK-1",
                    "summary": "open",
                    "status": "open",
                    "evidence": ".agent/phases/01-kernel/EVIDENCE.md#blk-1",
                }
            ]
            write_state(root, state)
            _, issues = _reconcile(root)
            self.assertTrue(any("open blockers" in issue for issue in issues))

    def test_reconciliation_requires_an_active_phase(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root)
            state, _ = read_state(root)
            set_lifecycle(state, "planned")
            write_state(root, state)
            _, issues = _reconcile(root)
            self.assertTrue(any("requires an active phase" in issue for issue in issues))

    def test_cli_reports_refusal_without_writing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _repository(root)
            _executed_phase(root, statuses=("verified", "executing"))
            completed = subprocess.run(
                [
                    str(FRAMEWORK_ROOT / "scripts" / "framework-next"),
                    "--project",
                    str(root),
                    "reconcile-phase",
                    "--id",
                    "P1",
                    "--name",
                    "Kernel",
                    "--slug",
                    "01-kernel",
                    "--decision",
                    "DEC-RECONCILE",
                    "--evidence",
                    ".agent/phases/01-kernel/EVIDENCE.md#reconciliation",
                    "--version",
                    "2",
                    "--actor",
                    "reconciliation",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.assertNotEqual(0, completed.returncode, completed.stdout)
            self.assertIn("unfinished", completed.stdout)
            persisted, _ = load_frontmatter(root / ".agent" / "STATE.md")
            self.assertEqual("executing", persisted["status"])


if __name__ == "__main__":
    unittest.main()
