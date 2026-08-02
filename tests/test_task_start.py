"""Starting the task the kernel already chose.

`execute-task -> <id>` was a recommendation nothing could carry out.
`current_task.id` had three writers and all of them look backwards: two set it
to `None`, and `reconcile-phase` fills it from work already `verified`.
`task-status` refuses unless the task is already current — the thing that needed
setting — and `transition --to executing` refuses because nothing is selected.

The gap hid for as long as every phase arrived by reconciliation. It surfaces
the first time a task is started forwards, which is exactly the shape these
tests reproduce.
"""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from kernel.runtime.cli import build_parser
from kernel.runtime.contracts import load_task_index
from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.state_machine import validate_state, validate_transition
from kernel.runtime.task_start import start_task
from tests.helpers import (
    initialized_project,
    minimal_task,
    read_state,
    write_state,
    write_tasks,
)


MERGED_BRANCH = "chore/ship-u2-and-activate-u3"
FEATURE = "feat/u3a-organization-setup"
OTHER = "feat/something-else"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def _planned_phase(root: Path, tasks=None) -> None:
    """A sealed plan with nothing started — the exact reported shape.

    Four pending tasks, `current_task` empty, and a historical working branch
    left behind by the session that published the plan.
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
        tasks
        if tasks is not None
        else [
            minimal_task("U3A"),
            minimal_task("U3B1"),
            minimal_task("U3B2", depends_on=["U3A", "U3B1"]),
            minimal_task("U3C"),
        ],
    )
    state, _ = read_state(root)
    state["status"] = "planned"
    state["phase"]["status"] = "planned"
    state["current_task"] = {"id": None, "status": None}
    state["next_action"] = {"operation": "execute-task", "target": None}
    state["risk"] = {"level": "medium", "reasons": ["task start fixture"]}
    state["gates"]["plan_quality"] = "passed"
    state["git"]["base_branch"] = "main"
    state["git"]["working_branch"] = MERGED_BRANCH
    state["context"]["source_commit"] = None
    write_state(root, state)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "planned")


def _on_feature(root: Path, tasks=None) -> None:
    _planned_phase(root, tasks=tasks)
    _git(root, "checkout", "-b", FEATURE)


def _start(root: Path, **overrides):
    arguments = {"actor": "workflow-runner", "reason": "Plan gate passed"}
    arguments.update(overrides)
    return start_task(root, **arguments)


def _statuses(root: Path):
    state, _ = read_state(root)
    index, _ = load_task_index(root / state["artifacts"]["tasks"])
    return {task["id"]: task["status"] for task in index["tasks"]}


class TheReportedScenario(unittest.TestCase):
    def test_the_old_commands_still_refuse(self) -> None:
        """Neither existing door opens, which is what made the gap a dead end."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            state, _ = read_state(root)

            self.assertEqual(validate_state(state, root), [])
            # task-status: the task is not current_task, and cannot become it.
            self.assertIsNone(state["current_task"]["id"])
            # transition: refuses because no task is selected.
            codes = {
                issue["code"] for issue in validate_transition(state, "executing", root)
            }
            self.assertIn("task-not-selected", codes)

    def test_start_task_selects_starts_and_binds(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)

            updated, issues, changed = _start(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(updated["current_task"]["id"], "U3A")
            self.assertEqual(updated["current_task"]["status"], "executing")
            self.assertEqual(updated["status"], "executing")
            self.assertEqual(updated["phase"]["status"], "executing")

            binding = updated["current_task"]["execution"]
            self.assertEqual(binding["branch"], FEATURE)
            self.assertEqual(binding["task_id"], "U3A")
            self.assertEqual(binding["bound_by"], "workflow-runner")

            self.assertEqual(validate_state(updated, root), [])

    def test_only_the_started_task_moves(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)

            _start(root)

            self.assertEqual(
                _statuses(root),
                {
                    "U3A": "executing",
                    "U3B1": "pending",
                    "U3B2": "pending",
                    "U3C": "pending",
                },
            )

    def test_the_next_operation_stops_pointing_at_execute_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            before = determine_next_operation(root)
            self.assertEqual(before["next_operation"]["operation"], "execute-task")
            self.assertEqual(before["next_operation"]["target"], "U3A")

            _start(root)

            after = determine_next_operation(root)
            self.assertEqual(after["next_operation"]["operation"], "resume-task")
            self.assertEqual(after["next_operation"]["target"], "U3A")
            self.assertEqual(after["inconsistencies"], [])

    def test_only_the_expected_documents_change(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            agent = root / ".agent"
            before = {
                path: path.read_bytes()
                for path in sorted(agent.rglob("*"))
                if path.is_file()
            }

            _start(root)

            changed = {
                path.relative_to(agent).as_posix()
                for path, content in before.items()
                if path.read_bytes() != content
            }
            state, _ = read_state(root)
            self.assertEqual(
                changed,
                {
                    "STATE.md",
                    Path(state["artifacts"]["tasks"]).relative_to(".agent").as_posix(),
                    Path(state["artifacts"]["evidence"])
                    .relative_to(".agent")
                    .as_posix(),
                },
            )


class TheTargetIsNotTheOperatorsToChoose(unittest.TestCase):
    def test_a_matching_task_id_is_accepted_as_confirmation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)

            updated, issues, changed = _start(root, task_id="U3A")

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(updated["current_task"]["id"], "U3A")

    def test_a_different_task_id_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)

            _, issues, changed = _start(root, task_id="U3C")

            self.assertFalse(changed)
            self.assertTrue(
                any("not the operator's to choose" in m for m in issues), issues
            )
            self.assertEqual(_statuses(root)["U3C"], "pending")

    def test_no_command_exposes_a_free_task_selector(self) -> None:
        parser = build_parser()
        subparsers = [
            action
            for action in parser._actions
            if hasattr(action, "choices") and isinstance(action.choices, dict)
        ][0].choices

        self.assertNotIn("select-task", subparsers)
        self.assertIn("start-task", subparsers)
        options = {
            option
            for action in subparsers["start-task"]._actions
            for option in action.option_strings
        }
        self.assertNotIn("--branch", options)
        # --task-id exists only as confirmation; the refusal test above proves
        # it cannot name a different task.
        self.assertIn("--task-id", options)


class StartIsRefused(unittest.TestCase):
    def test_when_the_phase_is_not_planned(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["status"] = "specified"
            state["phase"]["status"] = "specified"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(any("requires a 'planned' phase" in m for m in issues), issues)

    def test_when_no_task_is_eligible(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(
                root, tasks=[minimal_task("U3B2", depends_on=["U3A"]), minimal_task("U3A", status="cancelled")]
            )

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(issues)

    def test_when_the_target_task_is_not_pending(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root, tasks=[minimal_task("U3A", status="cancelled")])

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(issues)

    def test_when_another_task_is_already_under_way(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(
                root,
                tasks=[minimal_task("U3A"), minimal_task("U3B1", status="executing")],
            )

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("already under way" in m for m in issues), issues
            )

    def test_on_the_integration_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_phase(root)  # stays on main

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("integration branch" in m for m in issues), issues
            )
            self.assertEqual(_statuses(root)["U3A"], "pending")

    def test_on_a_detached_head(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            _git(root, "checkout", "--detach")

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(any("detached HEAD" in m for m in issues), issues)

    def test_when_the_plan_is_not_sealed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["plan_revision"] = {
                "version": 0,
                "decision_id": None,
                "fingerprint": None,
                "evidence": None,
            }
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(issues)

    def test_a_refused_start_writes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_phase(root)  # on main, will be refused
            agent = root / ".agent"
            before = {
                path: path.read_bytes()
                for path in sorted(agent.rglob("*"))
                if path.is_file()
            }

            _start(root)

            for path, content in before.items():
                self.assertEqual(path.read_bytes(), content, path.name)


class WritesAreAllOrNothing(unittest.TestCase):
    def test_a_ledger_failure_rolls_back_state_and_index(self) -> None:
        """The trail is part of the start, not a postscript to it.

        The ledger is appended last, after both documents are written, so this
        is the only failure that can find the state already moved. It has to
        put both back.
        """

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            state, _ = read_state(root)
            state_path = root / ".agent" / "STATE.md"
            tasks_path = root / state["artifacts"]["tasks"]
            state_before = state_path.read_bytes()
            tasks_before = tasks_path.read_bytes()

            with patch(
                "kernel.runtime.task_start.append_evidence_event",
                side_effect=OSError("ledger unavailable"),
            ):
                with self.assertRaises(OSError):
                    _start(root)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertEqual(tasks_path.read_bytes(), tasks_before)
            self.assertEqual(_statuses(root)["U3A"], "pending")

            state_after, _ = read_state(root)
            self.assertIsNone(state_after["current_task"]["id"])
            self.assertEqual(state_after["status"], "planned")

    def test_the_start_can_be_retried_after_a_rolled_back_failure(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            with patch(
                "kernel.runtime.task_start.append_evidence_event",
                side_effect=OSError("ledger unavailable"),
            ):
                with self.assertRaises(OSError):
                    _start(root)

            updated, issues, changed = _start(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(updated["current_task"]["id"], "U3A")
            self.assertEqual(validate_state(updated, root), [])


class Repetition(unittest.TestCase):
    def test_an_identical_repeat_is_a_no_op(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            first, _, _ = _start(root)
            bound_at = first["current_task"]["execution"]["bound_at"]
            state_path = root / ".agent" / "STATE.md"
            after_first = state_path.read_bytes()
            ledger = root / first["artifacts"]["evidence"]
            ledger_after_first = ledger.read_bytes()

            state, issues, changed = _start(root)

            self.assertEqual(issues, [])
            self.assertFalse(changed)
            self.assertEqual(state["current_task"]["execution"]["bound_at"], bound_at)
            self.assertEqual(state_path.read_bytes(), after_first)
            self.assertEqual(ledger.read_bytes(), ledger_after_first)

    def test_repeating_from_another_branch_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            _start(root)
            _git(root, "checkout", "-b", OTHER)

            _, issues, changed = _start(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("already executing on branch" in m for m in issues), issues
            )

    def test_repeating_for_another_task_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(root)
            _start(root)

            _, issues, changed = _start(root, task_id="U3C")

            self.assertFalse(changed)
            self.assertTrue(
                any("is already executing" in m for m in issues), issues
            )


class LegacyProjectsAreUnaffected(unittest.TestCase):
    def test_a_project_already_executing_is_not_restarted(self) -> None:
        """Reconciled and legacy states keep their own execution untouched."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _on_feature(
                root,
                tasks=[minimal_task("U3A", status="executing"), minimal_task("U3B1")],
            )
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["status"] = "executing"
            state["phase"]["status"] = "executing"
            # No execution binding at all: the legacy shape.
            state["current_task"] = {"id": "U3A", "status": "executing"}
            state["git"]["working_branch"] = FEATURE
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            updated, issues, changed = _start(root)

            self.assertEqual(issues, [])
            self.assertFalse(changed)
            self.assertEqual(updated["current_task"]["id"], "U3A")
            self.assertNotIn("execution", updated["current_task"])


if __name__ == "__main__":
    unittest.main()
