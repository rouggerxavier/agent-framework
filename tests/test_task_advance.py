"""Starting the *next* task of a phase, once the previous one is verified.

`verifying -> executing` "may select the next eligible task" was documented as a
legal move and had no writer. The derivation computed `execute-task -> <next>`
from `verifying` with no blockers, so the kernel pointed at an operation nothing
could perform: a phase of four tasks could start its first one and no other.

These tests reproduce the reported shape — U3A verified, U3B1 pending and
eligible, the persisted cursor still on `verify-phase`, and the operator already
standing on U3B1's branch — and pin the semantics of the advance: what carries
over, what rotates, and what still refuses.
"""

import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from kernel.runtime.contracts import load_task_index, update_task_status
from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.state_machine import effective_task_mode, validate_state
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
NEXT = "feat/u3b1-membership-onboarding-persistence"
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


def _default_tasks():
    return [
        minimal_task("U3A"),
        minimal_task("U3B1"),
        minimal_task("U3B2", depends_on=["U3A", "U3B1"]),
        minimal_task("U3C"),
    ]


def _planned_phase(root: Path, tasks=None, *, default_mode=None) -> None:
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")

    initialized_project(root, with_phase=True)
    write_tasks(
        root,
        _default_tasks() if tasks is None else tasks,
        default_mode=default_mode,
    )
    state, _ = read_state(root)
    state["status"] = "planned"
    state["phase"]["status"] = "planned"
    state["current_task"] = {"id": None, "status": None}
    state["next_action"] = {"operation": "execute-task", "target": None}
    state["risk"] = {"level": "medium", "reasons": ["task advance fixture"]}
    state["gates"]["plan_quality"] = "passed"
    state["git"]["base_branch"] = "main"
    state["git"]["working_branch"] = MERGED_BRANCH
    state["context"]["source_commit"] = None
    write_state(root, state)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "planned")


def _verified_first_task(
    root: Path,
    tasks=None,
    *,
    default_mode=None,
    move_to: str = NEXT,
    task_modes=None,
) -> None:
    """The reported shape: U3A verified, the phase still `verifying`.

    U3A is started through the real writer so its binding is captured the way a
    genuine execution captures it, then driven to `verified` the way the review
    and verification operations leave it.
    """

    _planned_phase(root, tasks=tasks, default_mode=default_mode)
    _git(root, "checkout", "-b", FEATURE)
    start_task(root, actor="workflow-runner", reason="plan gate passed")

    state, body = load_frontmatter(root / ".agent" / "STATE.md")
    state["status"] = "verifying"
    state["phase"]["status"] = "verifying"
    state["current_task"]["status"] = "verified"
    state["gates"]["self_review"] = "passed"
    state["gates"]["spec_compliance"] = "passed_with_notes"
    state["gates"]["code_quality"] = "approved_with_notes"
    state["gates"]["acceptance"] = "passed"
    state["gates"]["verification"] = "passed"
    # The judgements U3A was actually paid for. `reopen_review_gates` never
    # invents a record, so without these there would be no approval to check
    # survives the advance.
    state["gate_records"] = dict(state.get("gate_records") or {})
    for gate, verdict in (
        ("self_review", "passed"),
        ("spec_compliance", "passed_with_notes"),
        ("code_quality", "approved_with_notes"),
    ):
        state["gate_records"][gate] = {
            "gate": gate,
            "status": verdict,
            "task_id": "U3A",
            "plan_revision": 1,
            "decision": None,
            "evidence": "REVIEW.md",
            "at": "2026-01-01T00:00:00+00:00",
            "by": "reviewer",
            "history": [],
        }
    # The cursor the phase verification left behind, and the whole reason the
    # start used to refuse.
    state["next_action"] = {"operation": "verify-phase", "target": "U3A"}
    if task_modes is not None:
        state["task_modes"] = task_modes
    write_frontmatter(root / ".agent" / "STATE.md", state, body)

    tasks_path = root / state["artifacts"]["tasks"]
    for step in ("implementation_complete", "reviewing", "reviewed", "verifying", "verified"):
        update_task_status(tasks_path, "U3A", step)

    _git(root, "add", "-A")
    _git(root, "commit", "-m", "U3A verified")
    if move_to:
        _git(root, "checkout", "-b", move_to)


def _advance(root: Path, **overrides):
    arguments = {
        "actor": "workflow-runner",
        "reason": "U3A verified; U3B1 is the next eligible task",
    }
    arguments.update(overrides)
    return start_task(root, **arguments)


def _statuses(root: Path):
    state, _ = read_state(root)
    index, _ = load_task_index(root / state["artifacts"]["tasks"])
    return {task["id"]: task["status"] for task in index["tasks"]}


def _ledger_events(root: Path):
    """The ledger's JSON blocks, in the order they were appended."""

    state, _ = read_state(root)
    text = (root / state["artifacts"]["evidence"]).read_text(encoding="utf-8")
    return [
        json.loads(block)
        for block in re.findall(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    ]


class TheGapItself(unittest.TestCase):
    def test_the_kernel_points_at_the_next_task(self) -> None:
        """The derivation was never the problem — the missing writer was."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            decision = determine_next_operation(root)

            self.assertEqual(
                decision["next_operation"],
                {"operation": "execute-task", "target": "U3B1"},
            )
            self.assertEqual(decision["blocking_conditions"], [])

    def test_a_verified_task_no_longer_pins_the_checkout(self) -> None:
        """U3A is over; its branch stops constraining where U3B1 may run."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, _ = read_state(root)

            self.assertEqual(_git(root, "branch", "--show-current"), NEXT)
            self.assertEqual(state["current_task"]["execution"]["branch"], FEATURE)
            self.assertEqual(validate_state(state, root), [])


class TheAdvance(unittest.TestCase):
    def test_the_next_task_starts(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            updated, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(updated["current_task"]["id"], "U3B1")
            self.assertEqual(updated["current_task"]["status"], "executing")
            self.assertEqual(updated["status"], "executing")
            self.assertEqual(updated["phase"]["status"], "executing")
            self.assertEqual(validate_state(updated, root), [])

    def test_only_the_target_moves_in_the_index(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            _advance(root)

            self.assertEqual(
                _statuses(root),
                {
                    "U3A": "verified",
                    "U3B1": "executing",
                    "U3B2": "pending",
                    "U3C": "pending",
                },
            )

    def test_the_binding_rotates_to_the_new_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            updated, _, _ = _advance(root)

            binding = updated["current_task"]["execution"]
            self.assertEqual(binding["task_id"], "U3B1")
            self.assertEqual(binding["branch"], NEXT)
            self.assertEqual(binding["bound_by"], "workflow-runner")

    def test_the_previous_binding_is_kept_as_history(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            updated, _, _ = _advance(root)

            released = updated["git"]["last_execution"]
            self.assertEqual(released["task_id"], "U3A")
            self.assertEqual(released["branch"], FEATURE)
            self.assertIn("released_at", released)

    def test_the_stale_cursor_is_normalised_by_the_operation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            before, _ = read_state(root)
            self.assertEqual(before["next_action"]["operation"], "verify-phase")

            updated, issues, _ = _advance(root)

            self.assertEqual(issues, [])
            self.assertEqual(
                updated["next_action"],
                {"operation": "resume-task", "target": "U3B1"},
            )

    def test_the_ledger_records_an_advance_not_a_first_start(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            _advance(root)

            events = _ledger_events(root)
            starts = [event for event in events if event.get("kind") == "task-start"]
            self.assertEqual([event["task_id"] for event in starts], ["U3A", "U3B1"])
            details = starts[-1]["details"]
            self.assertEqual(details["phase_transition"], "verifying -> executing")
            self.assertEqual(details["follows_task"], "U3A")
            self.assertEqual(details["branch"], NEXT)


class ThePreviousTaskIsUntouched(unittest.TestCase):
    def test_its_status_and_approvals_survive(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            updated, _, _ = _advance(root)

            self.assertEqual(_statuses(root)["U3A"], "verified")
            # The new round opens on pending gates, and U3A's judgements are
            # kept as history rather than erased.
            history = updated["gate_records"]["spec_compliance"]["history"]
            self.assertTrue(
                any(entry.get("status") == "passed_with_notes" for entry in history),
                history,
            )

    def test_the_review_gates_open_for_the_new_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            updated, _, _ = _advance(root)

            self.assertEqual(updated["gates"]["spec_compliance"], "pending")
            self.assertEqual(updated["gates"]["code_quality"], "pending")
            self.assertEqual(updated["gates"]["self_review"], "pending")


class AdvanceGuards(unittest.TestCase):
    def test_the_previous_task_must_be_verified(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["current_task"]["status"] = "reviewing"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("requires the current one to be verified" in m for m in issues),
                issues,
            )

    def test_the_index_must_agree_the_previous_task_is_verified(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            for task in index["tasks"]:
                if task["id"] == "U3A":
                    task["status"] = "reviewing"
            write_frontmatter(path, index, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(any("expected verified" in m for m in issues), issues)

    def test_the_operator_may_not_choose_a_different_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            _, issues, changed = _advance(root, task_id="U3C")

            self.assertFalse(changed)
            self.assertTrue(
                any("not the task the kernel selected" in m for m in issues), issues
            )
            self.assertEqual(_statuses(root)["U3C"], "pending")

    def test_an_open_blocker_stops_the_advance(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["blockers"] = [
                {
                    "id": "B-1",
                    "summary": "migration unresolved",
                    "status": "open",
                    "evidence": "notes.md",
                }
            ]
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(any("open blockers" in m for m in issues), issues)

    def test_the_integration_branch_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root, move_to="")
            _git(root, "checkout", "main")

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(issues)
            self.assertEqual(_statuses(root)["U3B1"], "pending")

    def test_a_detached_head_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            _git(root, "checkout", "--detach")

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertEqual(_statuses(root)["U3B1"], "pending")

    def test_no_eligible_task_leaves_the_phase_alone(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(
                root,
                tasks=[minimal_task("U3A"), minimal_task("U3B2", depends_on=["U3B1"])],
            )

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("does not point at a task to execute" in m for m in issues), issues
            )

    def test_a_task_already_under_way_stops_the_advance(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            for task in index["tasks"]:
                if task["id"] == "U3C":
                    task["status"] = "executing"
            write_frontmatter(path, index, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("already under way" in m for m in issues), issues
            )

    def test_an_index_from_another_phase_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            index["phase"] = {"id": "P9", "name": "Elsewhere"}
            write_frontmatter(path, index, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("describes phase P9" in m for m in issues), issues
            )

    def test_a_real_inconsistency_still_stops_the_advance(self) -> None:
        """Only the cursor is forgiven; a genuine defect is not."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["artifacts"]["tasks"] = ".agent/phases/01-kernel/MISSING.md"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(issues)


class AdvanceGatesFollowTheNewTaskMode(unittest.TestCase):
    def _mode_of(self, root: Path, task_id: str) -> str:
        state, _ = read_state(root)
        return effective_task_mode(state, root, task_id=task_id)

    def test_a_standard_next_task_resolves_standard(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root, default_mode="standard")

            updated, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(self._mode_of(root, "U3B1"), "standard")
            self.assertEqual(updated["gates"]["spec_compliance"], "pending")

    def test_a_critical_previous_task_does_not_raise_the_next_one(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(
                root,
                default_mode="standard",
                task_modes={
                    "U3A": {
                        "mode": "critical",
                        "reason": "previous task only",
                        "severe_harm_factors": ["data loss"],
                        "at": "2026-01-01T00:00:00+00:00",
                        "by": "tests",
                    }
                },
            )

            _advance(root)

            self.assertEqual(self._mode_of(root, "U3A"), "critical")
            self.assertEqual(self._mode_of(root, "U3B1"), "standard")

    def test_a_fast_next_task_keeps_its_own_mode(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            tasks = _default_tasks()
            for task in tasks:
                if task["id"] == "U3B1":
                    task["execution_mode"] = "fast"
            _verified_first_task(root, tasks=tasks, default_mode="standard")

            _, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(self._mode_of(root, "U3B1"), "fast")

    def test_a_critical_next_task_keeps_its_own_mode(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            tasks = _default_tasks()
            for task in tasks:
                if task["id"] == "U3B1":
                    task["execution_mode"] = "critical"
            _verified_first_task(root, tasks=tasks, default_mode="standard")

            _, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(self._mode_of(root, "U3B1"), "critical")


class AdvanceIsIdempotent(unittest.TestCase):
    def test_repeating_the_same_advance_changes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            first, _, _ = _advance(root)

            second, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertFalse(changed)
            self.assertEqual(
                second["current_task"]["execution"],
                first["current_task"]["execution"],
            )

    def test_repeating_it_does_not_duplicate_the_ledger_event(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            _advance(root)
            _advance(root)

            events = _ledger_events(root)
            starts = [
                event
                for event in events
                if event.get("kind") == "task-start" and event["task_id"] == "U3B1"
            ]
            self.assertEqual(len(starts), 1)

    def test_asking_for_a_different_task_after_the_advance_fails(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            _advance(root)

            _, issues, changed = _advance(root, task_id="U3C")

            self.assertFalse(changed)
            self.assertTrue(
                any("U3B1 is already executing" in m for m in issues), issues
            )

    def test_repeating_it_from_another_branch_fails(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            _advance(root)
            _git(root, "checkout", "-b", OTHER)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("already executing on branch" in m for m in issues), issues
            )


class AdvanceIsAtomic(unittest.TestCase):
    def test_a_failed_ledger_append_restores_both_documents(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)
            state_path = root / ".agent" / "STATE.md"
            state, _ = read_state(root)
            tasks_path = root / state["artifacts"]["tasks"]
            state_before = state_path.read_bytes()
            tasks_before = tasks_path.read_bytes()

            with patch(
                "kernel.runtime.task_start.append_evidence_event",
                side_effect=OSError("ledger is unwritable"),
            ):
                with self.assertRaises(OSError):
                    _advance(root)

            self.assertEqual(state_path.read_bytes(), state_before)
            self.assertEqual(tasks_path.read_bytes(), tasks_before)

    def test_nothing_is_left_half_advanced(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            with patch(
                "kernel.runtime.task_start.append_evidence_event",
                side_effect=OSError("ledger is unwritable"),
            ):
                with self.assertRaises(OSError):
                    _advance(root)

            state, _ = read_state(root)
            self.assertEqual(state["status"], "verifying")
            self.assertEqual(state["current_task"]["id"], "U3A")
            self.assertEqual(state["current_task"]["status"], "verified")
            self.assertEqual(_statuses(root)["U3B1"], "pending")
            self.assertEqual(validate_state(state, root), [])

    def test_a_failed_index_write_leaves_the_phase_verifying(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root)

            with patch(
                "kernel.runtime.task_start.update_task_status",
                side_effect=OSError("index is unwritable"),
            ):
                with self.assertRaises(OSError):
                    _advance(root)

            state, _ = read_state(root)
            self.assertEqual(state["status"], "verifying")
            self.assertEqual(_statuses(root)["U3B1"], "pending")


class TheFluxoNexoScenario(unittest.TestCase):
    """The reported state, end to end, on the branch it was reported from."""

    def test_u3b1_starts_as_standard_and_leaves_the_rest_alone(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verified_first_task(root, default_mode="standard")

            state, _ = read_state(root)
            self.assertEqual(state["status"], "verifying")
            self.assertEqual(state["next_action"]["operation"], "verify-phase")
            self.assertEqual(_git(root, "branch", "--show-current"), NEXT)
            decision = determine_next_operation(root)
            self.assertEqual(decision["next_operation"]["target"], "U3B1")
            self.assertEqual(decision["blocking_conditions"], [])
            self.assertTrue(decision["stale_next_action"])

            updated, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(updated["status"], "executing")
            self.assertEqual(updated["current_task"]["id"], "U3B1")
            self.assertEqual(
                _statuses(root),
                {
                    "U3A": "verified",
                    "U3B1": "executing",
                    "U3B2": "pending",
                    "U3C": "pending",
                },
            )
            self.assertEqual(
                effective_task_mode(updated, root, task_id="U3B1"), "standard"
            )
            self.assertEqual(updated["current_task"]["execution"]["branch"], NEXT)
            self.assertEqual(updated["git"]["last_execution"]["branch"], FEATURE)
            self.assertEqual(validate_state(updated, root), [])
            self.assertEqual(determine_next_operation(root)["inconsistencies"], [])


if __name__ == "__main__":
    unittest.main()
