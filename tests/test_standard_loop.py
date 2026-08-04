"""The whole of `standard`: start a task, do the work, finish it.

Everything else the kernel can record — gates, seals, independent reviews, an
evidence ledger, a phase walking `discussing → specified → planned` in order —
stays available and stays optional. What these tests pin is that none of it is
a *precondition*: a phase that never paid a gate, whose `next_action` is stale,
whose `phase.status` lags, whose plan was edited after it was sealed, can still
start an eligible task and finish it. The framework organises the work; it is
not allowed to become the reason the work cannot happen.

`critical` is the opposite half of the same contract, and it appears here as the
control: every refusal these tests show removed is shown still standing there.
"""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.cli import main
from kernel.runtime.contracts import load_task_index
from kernel.runtime.documents import write_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.state_machine import validate_state, validate_transition
from kernel.runtime.task_finish import finish_task
from kernel.runtime.task_start import start_task
from tests.helpers import (
    initialized_project,
    minimal_task,
    read_state,
    write_tasks,
)


BRANCH = "feat/the-work"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def _project(root: Path, *, mode: str = "standard", tasks=None) -> None:
    """A phase with contracts on disk and nothing else paid for.

    Deliberately left at `specified`: no plan gate, no seal, no risk
    classification, and a `next_action` still pointing at the plan. This is what
    an ordinary project looks like halfway through an afternoon.
    """

    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")

    initialized_project(root, with_phase=True)
    write_tasks(
        root,
        tasks if tasks is not None else [minimal_task("T1"), minimal_task("T2")],
        default_mode=mode,
    )
    state, body = read_state(root)
    state["execution_mode"] = mode
    state["status"] = "specified"
    state["phase"]["status"] = "specified"
    state["git"]["base_branch"] = "main"
    state["context"]["source_commit"] = None
    write_frontmatter(root / ".agent" / "STATE.md", state, body)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "phase contracted")
    _git(root, "checkout", "-q", "-b", BRANCH)


def _statuses(root: Path):
    state, _ = read_state(root)
    index, _ = load_task_index(root / state["artifacts"]["tasks"])
    return {task["id"]: task["status"] for task in index["tasks"]}


class TheMinimalLoop(unittest.TestCase):
    def test_start_then_finish_is_the_whole_lifecycle(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)

            state, issues, changed = start_task(
                root, actor="implementer", reason="build the thing"
            )
            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("executing", state["status"])
            self.assertEqual("T1", state["current_task"]["id"])
            self.assertEqual(BRANCH, state["current_task"]["execution"]["branch"])
            self.assertEqual("executing", _statuses(root)["T1"])

            state, issues, changed = finish_task(
                root, actor="implementer", reason="tests pass"
            )
            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("verifying", state["status"])
            self.assertEqual("verified", state["current_task"]["status"])
            self.assertEqual("verified", _statuses(root)["T1"])
            # The branch the task ran on stops speaking for whatever runs next.
            self.assertNotIn("execution", state["current_task"])

    def test_the_next_task_starts_straight_after(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            start_task(root, actor="implementer", reason="first")
            finish_task(root, actor="implementer", reason="first done")

            self.assertEqual(
                "T2", determine_next_operation(root)["next_operation"]["target"]
            )
            state, issues, changed = start_task(
                root, actor="implementer", reason="second"
            )
            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("T2", state["current_task"]["id"])
            self.assertEqual({"T1": "verified", "T2": "executing"}, _statuses(root))

    def test_the_command_line_runs_the_loop(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "start-task",
                        "--actor", "implementer", "--reason", "build",
                    ]
                ),
            )
            self.assertEqual(
                0,
                main(
                    [
                        "--project", str(root), "finish-task",
                        "--actor", "implementer", "--reason", "done",
                    ]
                ),
            )
            self.assertEqual("verified", _statuses(root)["T1"])


class NothingCeremonialBlocksTheStart(unittest.TestCase):
    def test_no_gate_is_owed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, _ = read_state(root)
            self.assertTrue(
                all(
                    status in {"pending", "not_required"}
                    for status in state["gates"].values()
                )
            )
            self.assertEqual([], start_task(root, actor="a", reason="r")[1])

    def test_no_plan_seal_is_owed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, _ = read_state(root)
            self.assertIsNone(state["plan_revision"]["fingerprint"])
            self.assertEqual([], start_task(root, actor="a", reason="r")[1])

    def test_an_edited_plan_does_not_invalidate_a_sealed_phase(self) -> None:
        """The seal is `critical`'s. A plan is meant to move as work teaches you."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, body = read_state(root)
            state["plan_revision"] = {
                "version": 1,
                "decision_id": "DEC-OLD",
                "fingerprint": "sha256:stale",
                "evidence": state["artifacts"]["evidence"],
            }
            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            (root / state["artifacts"]["plan"]).write_text(
                "# Plan\n\nRewritten mid-phase.\n", encoding="utf-8"
            )

            errors = [
                item
                for item in validate_state(state, root)
                if item["severity"] == "error"
            ]
            self.assertEqual([], errors)
            self.assertEqual([], start_task(root, actor="a", reason="r")[1])

    def test_a_lagging_next_action_is_a_warning(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            decision = determine_next_operation(root)
            self.assertEqual("execute-task", decision["next_operation"]["operation"])
            self.assertTrue(
                any("next_action" in item for item in decision["inconsistencies"])
            )
            self.assertEqual([], decision["blocking_conditions"])
            self.assertEqual([], start_task(root, actor="a", reason="r")[1])

    def test_a_lagging_phase_status_is_a_warning(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, body = read_state(root)
            state["phase"]["status"] = "discussing"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            codes = {
                item["code"]
                for item in validate_state(state, root)
                if item["severity"] == "error"
            }
            self.assertNotIn("phase-state-mismatch", codes)
            self.assertEqual([], start_task(root, actor="a", reason="r")[1])

    def test_a_gate_record_that_disagrees_with_the_map_is_not_a_defect(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, body = read_state(root)
            state["gates"]["acceptance"] = "pending"
            state["gate_records"] = {
                "acceptance": {"status": "passed", "plan_revision": 1}
            }
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            self.assertEqual([], determine_next_operation(root)["blocking_conditions"])
            self.assertEqual([], start_task(root, actor="a", reason="r")[1])


class TheRefusalsThatRemain(unittest.TestCase):
    def test_a_task_that_does_not_exist(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, body = read_state(root)
            state["current_task"] = {"id": "GHOST", "status": "executing"}
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            codes = {
                item["code"]
                for item in validate_state(state, root)
                if item["severity"] == "error"
            }
            self.assertIn("task-contract-missing", codes)

    def test_an_unreadable_document(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, _ = read_state(root)
            (root / state["artifacts"]["tasks"]).write_text(
                "not frontmatter at all\n", encoding="utf-8"
            )

            codes = {
                item["code"]
                for item in validate_state(state, root)
                if item["severity"] == "error"
            }
            self.assertIn("task-index-invalid", codes)

    def test_a_missing_document(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, _ = read_state(root)
            (root / state["artifacts"]["spec"]).unlink()

            codes = {
                item["code"]
                for item in validate_state(state, root)
                if item["severity"] == "error"
            }
            self.assertIn("missing-artifact", codes)

    def test_an_open_blocker_naming_the_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, body = read_state(root)
            state["blockers"] = [
                {"id": "B-1", "summary": "schema undecided", "task_id": "T1"}
            ]
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            issues = start_task(root, actor="a", reason="r")[1]
            self.assertTrue(any("B-1" in message for message in issues), issues)

    def test_an_open_blocker_naming_another_task_does_not_stop_this_one(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            state, body = read_state(root)
            state["blockers"] = [
                {"id": "B-2", "summary": "OD-005 is open", "task_id": "T2"}
            ]
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            self.assertEqual([], start_task(root, actor="a", reason="r")[1])

    def test_a_finished_task_cannot_be_executed_again(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            start_task(root, actor="a", reason="r")
            finish_task(root, actor="a", reason="done")

            state, body = read_state(root)
            state["current_task"] = {"id": "T1", "status": "verified"}
            codes = {
                item["code"] for item in validate_transition(state, "executing", root)
            }
            self.assertIn("task-already-finished", codes)

            issues = finish_task(root, actor="a", reason="again", task_id="T1")[1]
            self.assertTrue(any("already" in message for message in issues), issues)

    def test_a_dependency_that_has_not_landed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(
                root,
                tasks=[minimal_task("T1", depends_on=["T0"]), minimal_task("T0")],
            )
            state, body = read_state(root)
            state["current_task"] = {"id": "T1", "status": "pending"}
            codes = {
                item["code"] for item in validate_transition(state, "executing", root)
            }
            self.assertIn("dependency-unsatisfied", codes)

    def test_a_branch_the_execution_is_not_standing_on(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root)
            start_task(root, actor="a", reason="r")
            # The operator wanders off the branch the execution was bound to.
            _git(root, "checkout", "-q", "main")

            state, _ = read_state(root)
            codes = {
                item["code"]
                for item in validate_state(state, root)
                if item["severity"] == "error"
            }
            self.assertIn("git-branch-mismatch", codes)


class CriticalKeepsEveryGuard(unittest.TestCase):
    def test_a_critical_phase_still_walks_its_lifecycle(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root, mode="critical")

            issues = start_task(root, actor="a", reason="r")[1]
            self.assertTrue(
                any("planned" in message for message in issues), issues
            )

    def test_finish_task_is_refused_under_critical(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _project(root, mode="critical")
            state, body = read_state(root)
            state["current_task"] = {"id": "T1", "status": "executing"}
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            issues = finish_task(root, actor="a", reason="done")[1]
            self.assertTrue(
                any("reviews and gates" in message for message in issues), issues
            )


if __name__ == "__main__":
    unittest.main()
