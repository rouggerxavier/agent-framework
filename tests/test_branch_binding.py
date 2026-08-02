"""Branch affinity belongs to execution, not to the whole lifecycle.

``git.working_branch`` was written once at initialization and then read as if it
meant "the branch this work must happen on", for every state from ``planned``
onward. Those are two different facts wearing one field. The consequence showed
up the moment a planning branch was merged: the integration branch reported
``git-branch-mismatch`` forever, in the one state where nothing had started yet
and the implementation branch might not even exist.

These tests pin the corrected model — affinity begins when a task starts, is
captured from Git rather than declared, and is released when execution ends.
"""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.cli import build_parser
from kernel.runtime.contracts import load_contract, update_task_status
from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.state_machine import (
    DocumentError,
    execution_binding,
    transition_state,
    validate_state,
    validate_transition,
)
from tests.helpers import (
    initialized_project,
    minimal_task,
    read_state,
    write_state,
    write_tasks,
)


MERGED_BRANCH = "chore/ship-and-activate"
FEATURE = "feat/u3a-organization-setup"
OTHER_FEATURE = "feat/something-else"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def _repository(root: Path) -> None:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")


def _planned_on_main(root: Path, tasks=None) -> None:
    """A sealed plan, no task started, and a merged working branch on record.

    This is the Fluxo Nexo shape: the branch that prepared and published the
    plan is merged and gone, and the operator is back on the integration
    branch with `execute-task` as the next move.
    """

    _repository(root)
    initialized_project(root, with_phase=True)
    write_tasks(
        root,
        tasks
        if tasks is not None
        else [
            minimal_task("U3A"),
            minimal_task("U3B1"),
            minimal_task("U3B2", depends_on=["U3A", "U3B1"]),
        ],
    )
    state, _ = read_state(root)
    state["status"] = "planned"
    state["phase"]["status"] = "planned"
    state["current_task"] = {"id": None, "status": None}
    state["next_action"] = {"operation": "execute-task", "target": None}
    state["risk"] = {"level": "medium", "reasons": ["binding fixture"]}
    state["gates"]["plan_quality"] = "passed"
    state["git"]["base_branch"] = "main"
    state["git"]["working_branch"] = MERGED_BRANCH
    state["context"]["source_commit"] = None
    write_state(root, state)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "planned state")


def _start(root: Path, task_id: str = "U3A", actor: str = "runner"):
    """Drive the start the way the CLI does: transition, then sync the index."""

    state, body = load_frontmatter(root / ".agent" / "STATE.md")
    state["current_task"] = {"id": task_id, "status": "pending"}
    updated = transition_state(
        state, "executing", root, actor=actor, reason="start {}".format(task_id)
    )
    update_task_status(root / updated["artifacts"]["tasks"], task_id, "executing")
    write_frontmatter(root / ".agent" / "STATE.md", updated, body)
    return updated


def _advance(root: Path, state, target: str, actor: str = "runner"):
    """A guarded transition that keeps the task index in step, as the CLI does."""

    updated = transition_state(state, target, root, actor=actor, reason=target)
    task = updated.get("current_task", {})
    if task.get("id") and task.get("status"):
        tasks_path = root / updated["artifacts"]["tasks"]
        indexed = load_contract(tasks_path, task["id"])
        if indexed.get("status") != task["status"]:
            update_task_status(tasks_path, task["id"], task["status"])
    write_frontmatter(root / ".agent" / "STATE.md", updated, "# State\n")
    return updated


class PlannedHasNoBranchAffinity(unittest.TestCase):
    """Scenario A — the exact shape that stranded the integration branch."""

    def test_planned_validates_on_main_with_a_merged_working_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            state, _ = read_state(root)

            self.assertEqual(_git(root, "rev-parse", "--abbrev-ref", "HEAD"), "main")
            self.assertEqual(state["git"]["working_branch"], MERGED_BRANCH)
            self.assertEqual(validate_state(state, root), [])

    def test_the_next_operation_is_still_to_execute_the_first_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)

            decision = determine_next_operation(root)

            self.assertEqual(decision["next_operation"]["operation"], "execute-task")
            self.assertEqual(decision["next_operation"]["target"], "U3A")
            self.assertEqual(decision["inconsistencies"], [])

    def test_validate_never_writes(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            path = root / ".agent" / "STATE.md"
            before = path.read_text(encoding="utf-8")

            state, _ = read_state(root)
            validate_state(state, root)
            determine_next_operation(root)

            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_states_after_execution_have_no_affinity_either(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            state, _ = read_state(root)

            for status in ("specified", "ready_to_ship", "shipped", "superseded"):
                state["status"] = status
                state["phase"]["status"] = status
                codes = {
                    issue["code"] for issue in validate_state(state, root)
                }
                self.assertNotIn("git-branch-mismatch", codes, status)


class StartingATaskBindsIt(unittest.TestCase):
    """Scenario B — affinity is captured from Git, never declared."""

    def test_starting_on_a_feature_branch_records_the_binding(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            _git(root, "checkout", "-b", FEATURE)

            updated = _start(root)

            binding = updated["current_task"]["execution"]
            self.assertEqual(binding["branch"], FEATURE)
            self.assertEqual(binding["task_id"], "U3A")
            self.assertEqual(binding["bound_by"], "runner")
            self.assertIn("bound_at", binding)
            self.assertEqual(validate_state(updated, root), [])

    def test_the_binding_overrides_the_stale_working_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            _git(root, "checkout", "-b", FEATURE)

            updated = _start(root)

            self.assertEqual(updated["git"]["working_branch"], MERGED_BRANCH)
            self.assertEqual(execution_binding(updated)["branch"], FEATURE)
            self.assertEqual(validate_state(updated, root), [])

    def test_no_operation_accepts_a_branch_argument(self) -> None:
        """The binding cannot be declared, so it cannot be declared falsely."""

        parser = build_parser()
        subparsers = [
            action
            for action in parser._actions
            if hasattr(action, "choices") and isinstance(action.choices, dict)
        ][0].choices

        self.assertNotIn("set-branch", subparsers)
        for name, subparser in subparsers.items():
            options = {
                option
                for action in subparser._actions
                for option in action.option_strings
            }
            self.assertNotIn("--branch", options, name)
            self.assertNotIn("--working-branch", options, name)

    def test_the_portable_worktree_survives_binding(self) -> None:
        """Scenario E — nothing machine-specific is written."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["git"]["worktree"] = "."
            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            _git(root, "checkout", "-b", FEATURE)

            updated = _start(root)

            self.assertEqual(updated["current_task"]["execution"]["worktree"], ".")
            self.assertNotIn(str(root), str(updated["current_task"]["execution"]))
            self.assertEqual(validate_state(updated, root), [])


class ExecutionStaysProtected(unittest.TestCase):
    """Scenario C — the guard that must not soften."""

    def _executing(self, root: Path):
        _planned_on_main(root)
        _git(root, "checkout", "-b", FEATURE)
        return _start(root)

    def test_switching_to_the_integration_branch_is_caught(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            _git(root, "checkout", "main")

            codes = {issue["code"] for issue in validate_state(updated, root)}

            self.assertIn("git-branch-mismatch", codes)

    def test_switching_to_another_feature_branch_is_caught(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            _git(root, "checkout", "-b", OTHER_FEATURE)

            codes = {issue["code"] for issue in validate_state(updated, root)}

            self.assertIn("git-branch-mismatch", codes)

    def test_returning_to_the_bound_branch_clears_the_issue(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            _git(root, "checkout", "main")
            self.assertTrue(validate_state(updated, root))

            _git(root, "checkout", FEATURE)

            self.assertEqual(validate_state(updated, root), [])

    def test_a_detached_head_during_execution_is_caught(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            _git(root, "checkout", "--detach")

            codes = {issue["code"] for issue in validate_state(updated, root)}

            self.assertIn("git-detached-head", codes)

    def test_reviewing_and_verifying_stay_bound(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            _git(root, "checkout", "main")

            for status in ("executing", "reviewing", "verifying"):
                updated["status"] = status
                codes = {issue["code"] for issue in validate_state(updated, root)}
                self.assertIn("git-branch-mismatch", codes, status)

    def test_a_binding_naming_another_task_is_caught(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            updated["current_task"]["id"] = "U3B1"

            codes = {issue["code"] for issue in validate_state(updated, root)}

            self.assertIn("execution-binding-mismatch", codes)

    def test_a_changed_worktree_declaration_is_caught(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._executing(root)
            updated["git"]["worktree"] = "somewhere-else"

            codes = {issue["code"] for issue in validate_state(updated, root)}

            self.assertIn("worktree-binding-mismatch", codes)

    def test_legacy_states_without_a_binding_stay_protected(self) -> None:
        """A project already mid-execution keeps its guard without migration."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            _git(root, "checkout", "-b", FEATURE)
            state, _ = read_state(root)
            state["status"] = "executing"
            state["phase"]["status"] = "executing"
            state["current_task"] = {"id": "U3A", "status": "executing"}
            state["git"]["working_branch"] = OTHER_FEATURE

            codes = {issue["code"] for issue in validate_state(state, root)}

            self.assertIn("git-branch-mismatch", codes)
            self.assertTrue(execution_binding(state)["legacy"])


class TheRecommendationPointsAtTheCheckout(unittest.TestCase):
    """A moved checkout is not a broken state, and must not be told to edit one."""

    def test_a_branch_mismatch_recommends_restoring_the_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            _git(root, "checkout", "-b", FEATURE)
            _start(root)
            _git(root, "checkout", "main")

            decision = determine_next_operation(root)

            self.assertEqual(
                decision["next_operation"]["operation"], "restore-execution-branch"
            )
            self.assertEqual(decision["next_operation"]["target"], FEATURE)
            self.assertNotEqual(decision["next_operation"]["target"], ".agent/STATE.md")

    def test_a_genuinely_broken_state_still_recommends_repair(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["risk"] = {"level": "nonsense", "reasons": []}
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            decision = determine_next_operation(root)

            self.assertEqual(decision["next_operation"]["operation"], "repair-state")
            self.assertEqual(decision["next_operation"]["target"], ".agent/STATE.md")


class StartingIsRefusedWhenItCannotBind(unittest.TestCase):
    def test_execution_cannot_start_on_the_integration_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            state, _ = read_state(root)
            state["current_task"] = {"id": "U3A", "status": "pending"}

            codes = {
                issue["code"] for issue in validate_transition(state, "executing", root)
            }

            self.assertIn("execution-on-base-branch", codes)

    def test_execution_cannot_start_on_a_detached_head(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            _git(root, "checkout", "--detach")
            state, _ = read_state(root)
            state["current_task"] = {"id": "U3A", "status": "pending"}

            codes = {
                issue["code"] for issue in validate_transition(state, "executing", root)
            }

            self.assertIn("git-detached-head", codes)

    def test_starting_without_a_selected_task_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            _git(root, "checkout", "-b", FEATURE)
            state, _ = read_state(root)

            codes = {
                issue["code"] for issue in validate_transition(state, "executing", root)
            }

            self.assertIn("task-not-selected", codes)

    def test_a_refused_start_writes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _planned_on_main(root)
            path = root / ".agent" / "STATE.md"
            before = path.read_text(encoding="utf-8")

            with self.assertRaises(DocumentError):
                _start(root)  # still on main

            self.assertEqual(path.read_text(encoding="utf-8"), before)


class LeavingExecutionReleasesTheBinding(unittest.TestCase):
    """Scenario D — a merged branch stops speaking for finished work."""

    def _verifying_with_binding(self, root: Path):
        """Reach verifying with a real binding, without walking the review gates.

        The review chain has guards of its own and they are not what these
        tests are about; what matters here is that the transition *out* of
        execution releases the binding.
        """

        # A single-task phase: reaching ready_to_ship needs every task
        # verified, and the review chain of the others is not what is on trial.
        _planned_on_main(root, tasks=[minimal_task("U3A")])
        _git(root, "checkout", "-b", FEATURE)
        updated = _start(root)
        self.assertEqual(updated["current_task"]["execution"]["branch"], FEATURE)

        updated["status"] = "verifying"
        updated["phase"]["status"] = "verifying"
        updated["current_task"]["status"] = "verified"
        updated["gates"].update(
            {
                "self_review": "passed",
                "spec_compliance": "passed",
                "code_quality": "approved",
                "acceptance": "passed",
                "verification": "passed",
            }
        )
        tasks_path = root / updated["artifacts"]["tasks"]
        for step in (
            "implementation_complete",
            "reviewing",
            "reviewed",
            "verifying",
            "verified",
        ):
            update_task_status(tasks_path, "U3A", step)
        write_frontmatter(root / ".agent" / "STATE.md", updated, "# State\n")
        return updated

    def test_the_binding_survives_the_whole_of_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._verifying_with_binding(root)

            self.assertEqual(
                updated["current_task"]["execution"]["branch"], FEATURE
            )
            self.assertEqual(validate_state(updated, root), [])

    def test_reaching_ready_to_ship_releases_and_preserves_the_binding(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._verifying_with_binding(root)

            shipped = _advance(root, updated, "ready_to_ship", actor="verifier")

            self.assertNotIn("execution", shipped["current_task"])
            self.assertEqual(shipped["git"]["last_execution"]["branch"], FEATURE)
            self.assertEqual(shipped["git"]["last_execution"]["task_id"], "U3A")
            self.assertIn("released_at", shipped["git"]["last_execution"])

    def test_reworking_from_ready_to_ship_binds_again(self) -> None:
        """Re-entering execution must not fall back to a branch it never used."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._verifying_with_binding(root)
            shipped = _advance(root, updated, "ready_to_ship", actor="verifier")
            self.assertNotIn("execution", shipped["current_task"])

            _git(root, "checkout", "-b", OTHER_FEATURE)
            reworked = transition_state(
                shipped, "verifying", root, actor="verifier", reason="defect found"
            )

            self.assertEqual(
                reworked["current_task"]["execution"]["branch"], OTHER_FEATURE
            )
            codes = {issue["code"] for issue in validate_state(reworked, root)}
            self.assertNotIn("git-branch-mismatch", codes)

    def test_the_released_branch_may_be_deleted_and_main_still_validates(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            updated = self._verifying_with_binding(root)
            _advance(root, updated, "ready_to_ship", actor="verifier")

            _git(root, "checkout", "main")
            _git(root, "branch", "-D", FEATURE)

            state, _ = read_state(root)
            self.assertEqual(validate_state(state, root), [])
            self.assertEqual(state["git"]["last_execution"]["branch"], FEATURE)


if __name__ == "__main__":
    unittest.main()
