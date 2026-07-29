from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.contracts import update_task_status
from kernel.runtime.state_machine import validate_state, validate_transition
from tests.helpers import (
    initialized_project,
    minimal_task,
    seal_plan,
    set_lifecycle,
    write_tasks,
)


class StateMachineTests(unittest.TestCase):
    def test_forbidden_transition_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root)
            issues = validate_transition(state, "ready_to_ship", root)
            self.assertIn("forbidden-transition", {item["code"] for item in issues})

    def test_specified_to_planned_requires_gate_tasks_and_risk(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            set_lifecycle(state, "specified")
            issues = validate_transition(state, "planned", root)
            codes = {item["code"] for item in issues}
            self.assertIn("plan-gate", codes)
            self.assertIn("risk-unclassified", codes)
            self.assertIn("empty-plan", codes)

    def test_planned_to_executing_with_validated_contract(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task()])
            set_lifecycle(state, "planned")
            state["gates"]["plan_quality"] = "passed"
            state["risk"]["level"] = "medium"
            state["current_task"] = {"id": "P1-T01", "status": "pending"}
            seal_plan(state, root)
            self.assertEqual([], validate_transition(state, "executing", root))

    def test_planned_to_executing_rejects_unsatisfied_dependency(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [
                    minimal_task("P1-T01", status="executing"),
                    minimal_task("P1-T02", depends_on=["P1-T01"]),
                ],
            )
            set_lifecycle(state, "planned")
            state["gates"]["plan_quality"] = "passed"
            state["risk"]["level"] = "medium"
            state["current_task"] = {"id": "P1-T02", "status": "pending"}
            seal_plan(state, root)
            issues = validate_transition(state, "executing", root)
            self.assertIn("dependency-unsatisfied", {item["code"] for item in issues})

    def test_review_blocker_returns_to_execution_with_evidence(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task(status="reviewing")])
            set_lifecycle(state, "reviewing")
            state["current_task"] = {"id": "P1-T01", "status": "reviewing"}
            state["gates"]["spec_compliance"] = "blocked"
            state["blockers"] = [
                {
                    "id": "B1",
                    "summary": "AC-01 missing",
                    "evidence": ["review report AC-01"],
                }
            ]
            self.assertEqual([], validate_transition(state, "executing", root))

    def test_review_return_without_evidence_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task(status="reviewing")])
            set_lifecycle(state, "reviewing")
            state["current_task"] = {"id": "P1-T01", "status": "reviewing"}
            state["gates"]["code_quality"] = "changes_required"
            state["blockers"] = [{"id": "B1", "summary": "bug"}]
            issues = validate_transition(state, "executing", root)
            self.assertIn(
                "review-blocker-evidence", {item["code"] for item in issues}
            )

    def test_verification_promotes_only_with_all_evidence(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task(status="verified")])
            set_lifecycle(state, "verifying")
            state["current_task"] = {"id": "P1-T01", "status": "verified"}
            state["verification"]["required"] = ["unit", "runtime"]
            state["verification"]["results"] = {
                "unit": "passed",
                "runtime": "passed",
            }
            state["gates"].update(
                {
                    "acceptance": "passed",
                    "verification": "passed",
                    "waivers": "not_required",
                }
            )
            self.assertEqual([], validate_transition(state, "ready_to_ship", root))

    def test_blocker_prevents_ready_to_ship(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task(status="verified")])
            set_lifecycle(state, "verifying")
            state["current_task"] = {"id": "P1-T01", "status": "verified"}
            state["gates"].update(
                {
                    "acceptance": "passed",
                    "verification": "passed",
                    "waivers": "not_required",
                }
            )
            state["blockers"] = [
                {"id": "B1", "summary": "open", "evidence": ["failed runtime"]}
            ]
            issues = validate_transition(state, "ready_to_ship", root)
            self.assertIn("open-blockers", {item["code"] for item in issues})

    def test_verified_task_can_advance_to_next_eligible_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [
                    minimal_task("P1-T01", status="verified"),
                    minimal_task("P1-T02", depends_on=["P1-T01"]),
                ],
            )
            set_lifecycle(state, "verifying")
            state["current_task"] = {"id": "P1-T02", "status": "pending"}
            state["gates"]["verification"] = "passed"
            self.assertEqual([], validate_transition(state, "executing", root))

    def test_plan_change_after_seal_is_detected(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task()])
            set_lifecycle(state, "planned")
            state["risk"]["level"] = "medium"
            state["gates"]["plan_quality"] = "passed"
            seal_plan(state, root)
            plan = root / state["artifacts"]["plan"]
            plan.write_text(
                plan.read_text(encoding="utf-8") + "\nUnapproved change.\n",
                encoding="utf-8",
            )
            issues = validate_state(state, root, check_git=False)
            self.assertIn(
                "plan-changed-without-revision", {item["code"] for item in issues}
            )

    def test_task_status_change_does_not_invalidate_plan_seal(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            task_path = write_tasks(root, [minimal_task()])
            set_lifecycle(state, "planned")
            state["risk"]["level"] = "medium"
            state["gates"]["plan_quality"] = "passed"
            seal_plan(state, root)
            update_task_status(task_path, "P1-T01", "executing")
            state["current_task"] = {"id": "P1-T01", "status": "executing"}
            set_lifecycle(state, "executing")
            issues = validate_state(state, root, check_git=False)
            self.assertNotIn(
                "plan-changed-without-revision", {item["code"] for item in issues}
            )

    def test_parallel_tasks_with_shared_file_are_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            first = minimal_task("P1-T01")
            second = minimal_task("P1-T02")
            first["execution"] = {"parallel_group": "G1", "isolation": "worktree"}
            second["execution"] = {"parallel_group": "G1", "isolation": "worktree"}
            write_tasks(root, [first, second])
            set_lifecycle(state, "specified")
            state["risk"]["level"] = "medium"
            state["gates"]["plan_quality"] = "passed"
            seal_plan(state, root)
            issues = validate_transition(state, "planned", root)
            self.assertIn("task-graph", {item["code"] for item in issues})

    def test_high_risk_execution_requires_worktree(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task()])
            set_lifecycle(state, "planned")
            state["risk"]["level"] = "high"
            state["gates"]["plan_quality"] = "passed"
            state["current_task"] = {"id": "P1-T01", "status": "pending"}
            seal_plan(state, root)
            issues = validate_transition(state, "executing", root)
            self.assertIn("worktree-required", {item["code"] for item in issues})


if __name__ == "__main__":
    unittest.main()
