from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.documents import DocumentError, load_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.project import initialize_phase, initialize_project
from kernel.runtime.state_machine import validate_state
from tests.helpers import FRAMEWORK_ROOT


class InitializationTests(unittest.TestCase):
    def test_uninitialized_project_routes_to_initialization(self) -> None:
        with TemporaryDirectory() as temporary:
            decision = determine_next_operation(Path(temporary))
            self.assertEqual("uninitialized", decision["current_state"])
            self.assertEqual(
                "initialize-project", decision["next_operation"]["operation"]
            )

    def test_partial_agent_directory_is_blocked_not_overwritten(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".agent").mkdir()
            decision = determine_next_operation(root)
            self.assertEqual("repair-state", decision["next_operation"]["operation"])
            self.assertTrue(decision["blocking_conditions"])

    def test_initialization_creates_required_artifacts_and_valid_state(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_project(
                root, FRAMEWORK_ROOT, project_name="example", mode="full"
            )
            expected = {
                "PROJECT.md",
                "ROADMAP.md",
                "STATE.md",
                "CONTEXT.md",
                "DECISIONS.md",
                "REQUIREMENTS.md",
                "phases",
            }
            self.assertEqual(expected, {path.name for path in (root / ".agent").iterdir()})
            state, _ = load_frontmatter(root / ".agent" / "STATE.md")
            self.assertEqual("proposed", state["status"])
            self.assertEqual([], validate_state(state, root))

    def test_initialization_never_overwrites_existing_agent_directory(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_project(root, FRAMEWORK_ROOT, project_name="example")
            with self.assertRaises(DocumentError):
                initialize_project(root, FRAMEWORK_ROOT, project_name="other")

    def test_phase_initialization_creates_all_phase_artifacts(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_project(root, FRAMEWORK_ROOT, project_name="example")
            phase = initialize_phase(
                root,
                FRAMEWORK_ROOT,
                phase_id="P1",
                phase_name="Kernel",
                slug="01-kernel",
                actor="test",
            )
            self.assertEqual(
                {"SPEC.md", "PLAN.md", "TASKS.md", "EVIDENCE.md", "REVIEW.md", "HANDOFF.md"},
                {path.name for path in phase.iterdir()},
            )
            state, _ = load_frontmatter(root / ".agent" / "STATE.md")
            self.assertEqual("discussing", state["status"])
            self.assertEqual([], validate_state(state, root))

    def test_framework_next_cli_initializes_and_resumes(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = FRAMEWORK_ROOT / "scripts" / "framework-next"
            initialized = subprocess.run(
                [
                    str(script),
                    "init",
                    "--project",
                    str(root),
                    "--name",
                    "cli-project",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.assertEqual(0, initialized.returncode, initialized.stdout)
            resumed = subprocess.run(
                [str(script), "--project", str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.assertEqual(0, resumed.returncode, resumed.stdout)
            self.assertIn("Current state: proposed", resumed.stdout)
            self.assertIn("Next operation: discuss-requirements", resumed.stdout)


if __name__ == "__main__":
    unittest.main()
