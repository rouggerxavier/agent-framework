from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.project import initialize_project
from tests.helpers import (
    FRAMEWORK_ROOT,
    initialized_project,
    minimal_task,
    read_state,
    set_lifecycle,
    write_state,
    write_tasks,
)


class FrameworkNextTests(unittest.TestCase):
    def test_recorded_fast_mode_preserves_agent_but_skips_kernel(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_project(root, FRAMEWORK_ROOT, project_name="legacy-fast")
            state, body = read_state(root)
            state["execution_mode"] = "fast"
            write_state(root, state, body)
            decision = determine_next_operation(root)
            self.assertEqual("fast", decision["execution_mode"])
            self.assertEqual("route-task", decision["next_operation"]["operation"])
            self.assertTrue((root / ".agent" / "STATE.md").is_file())

    def test_recorded_standard_mode_routes_to_short_plan(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_project(
                root, FRAMEWORK_ROOT, project_name="standard", mode="standard"
            )
            decision = determine_next_operation(root)
            self.assertEqual("standard", decision["execution_mode"])
            self.assertEqual(
                "build-short-plan", decision["next_operation"]["operation"]
            )
            self.assertEqual(
                "skills/workflow-planner/SKILL.md", decision["required_asset"]
            )

    def test_planned_selects_first_eligible_task(self) -> None:
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
            set_lifecycle(state, "planned")
            state["risk"]["level"] = "medium"
            state["gates"]["plan_quality"] = "passed"
            state["current_task"] = {"id": None, "status": None}
            write_state(root, state)
            decision = determine_next_operation(root)
            self.assertEqual("execute-task", decision["next_operation"]["operation"])
            self.assertEqual("P1-T02", decision["next_operation"]["target"])

    def test_executing_resumes_active_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task(status="executing")])
            set_lifecycle(state, "executing")
            state["risk"]["level"] = "medium"
            state["current_task"] = {"id": "P1-T01", "status": "executing"}
            write_state(root, state)
            decision = determine_next_operation(root)
            self.assertEqual("resume-task", decision["next_operation"]["operation"])
            self.assertEqual("P1-T01", decision["next_operation"]["target"])

    def test_reviewing_routes_to_pending_spec_review(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            write_tasks(root, [minimal_task(status="reviewing")])
            set_lifecycle(state, "reviewing")
            state["risk"]["level"] = "medium"
            state["current_task"] = {"id": "P1-T01", "status": "reviewing"}
            write_state(root, state)
            decision = determine_next_operation(root)
            self.assertEqual(
                "run-spec-review", decision["next_operation"]["operation"]
            )

    def test_verified_task_selects_next_eligible_task(self) -> None:
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
            state["risk"]["level"] = "medium"
            state["current_task"] = {"id": "P1-T01", "status": "verified"}
            state["gates"]["verification"] = "passed"
            write_state(root, state)
            decision = determine_next_operation(root)
            self.assertEqual("execute-task", decision["next_operation"]["operation"])
            self.assertEqual("P1-T02", decision["next_operation"]["target"])

    def test_inconsistent_state_is_blocked(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            state["artifacts"]["spec"] = ".agent/phases/01-kernel/MISSING.md"
            write_state(root, state)
            decision = determine_next_operation(root)
            self.assertEqual("repair-state", decision["next_operation"]["operation"])
            self.assertTrue(decision["blocking_conditions"])

    def test_missing_active_contract_is_blocked(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = initialized_project(root, with_phase=True)
            set_lifecycle(state, "executing")
            state["risk"]["level"] = "medium"
            state["current_task"] = {"id": "P1-T99", "status": "executing"}
            write_state(root, state)
            decision = determine_next_operation(root)
            self.assertEqual("repair-state", decision["next_operation"]["operation"])
            self.assertTrue(
                any("no contract" in item for item in decision["blocking_conditions"])
            )


if __name__ == "__main__":
    unittest.main()
