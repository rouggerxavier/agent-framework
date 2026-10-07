import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.execution_modes import state_execution_mode
from tests.helpers import FRAMEWORK_ROOT


class CompatibilityTests(unittest.TestCase):
    def test_legacy_state_without_execution_mode_defaults_to_standard(self) -> None:
        """Silence is not a declaration of catastrophic risk.

        A state written before the field existed says nothing about grave
        damage, and reading it as `critical` inferred the heaviest lifecycle in
        the framework from an absent key.
        """

        self.assertEqual(
            "standard",
            state_execution_mode(
                {"schema_version": 1, "project": {"mode": "full"}}
            ),
        )

    def test_legacy_orchestrator_routes_to_split_roles(self) -> None:
        content = (
            FRAMEWORK_ROOT / "skills" / "workflow-orchestrator" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("name: workflow-orchestrator", content)
        self.assertIn("workflow-planner", content)
        self.assertIn("workflow-runner", content)
        self.assertIn("alias", content.lower())

    def test_main_legacy_workflows_route_through_kernel(self) -> None:
        for name in ("feature-build.md", "bugfix.md", "api-refactor.md", "release.md"):
            content = (FRAMEWORK_ROOT / "workflows" / name).read_text(
                encoding="utf-8"
            )
            self.assertIn("framework-next", content, name)
            self.assertIn("workflow-runner", content, name)

    def test_multi_agent_router_exposes_maestri_control_plane(self) -> None:
        router = (
            FRAMEWORK_ROOT / "skills" / "agent-framework-router" / "SKILL.md"
        ).read_text(encoding="utf-8")
        for asset in (
            "team-orchestrator",
            "worktree-lane-manager",
            "fresh-task-session",
            "project-notebook",
            "integration-batch-manager",
        ):
            self.assertIn(asset, router)

    def test_team_orchestrator_keeps_decisions_local_and_work_moving(self) -> None:
        content = (
            FRAMEWORK_ROOT / "skills" / "team-orchestrator" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("awaiting_decision", content)
        self.assertIn("Q-###", content)
        self.assertIn("fresh-task-session", content)
        self.assertIn("worktree-lane-manager", content)
        self.assertIn("integration-batch-manager", content)

    def test_team_orchestrator_yields_instead_of_polling_workers(self) -> None:
        orchestrator = (
            FRAMEWORK_ROOT / "skills" / "team-orchestrator" / "SKILL.md"
        ).read_text(encoding="utf-8")
        workflow = (
            FRAMEWORK_ROOT / "workflows" / "multi-agent-development.md"
        ).read_text(encoding="utf-8")
        policy = (
            FRAMEWORK_ROOT / "kernel" / "orchestration-policy.md"
        ).read_text(encoding="utf-8")
        state = (
            FRAMEWORK_ROOT / "templates" / "orchestration-state.md"
        ).read_text(encoding="utf-8")

        for content in (orchestrator, workflow, policy):
            self.assertIn("waiting_for_event", content)
            self.assertIn("yield", content.lower())

        self.assertIn("sleep -> check", orchestrator)
        self.assertIn("sleep -> terminal check", workflow)
        self.assertIn("sleep -> check", policy)
        self.assertIn('"waiting_for_events": []', state)
        self.assertIn("`waiting_for_event`", state)

    def test_multi_agent_templates_persist_lanes_questions_and_fresh_context(self) -> None:
        state = (FRAMEWORK_ROOT / "templates" / "orchestration-state.md").read_text(
            encoding="utf-8"
        )
        dispatch = (FRAMEWORK_ROOT / "templates" / "agent-dispatch.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('"lanes": []', state)
        self.assertIn('"integration_batches": []', state)
        self.assertIn('"awaiting_user": []', state)
        self.assertIn('"fresh_context_required": true', dispatch)
        self.assertIn('"kind": "worktree"', dispatch)
        for name in ("INDEX.md", "QUESTIONS.md", "PROGRESS.md", "PHASES.md"):
            self.assertTrue(
                (FRAMEWORK_ROOT / "templates" / "project-notes" / name).is_file(),
                name,
            )

    def test_installer_syncs_kernel_and_preserves_unrelated_assets(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "codex"
            skills = root / "skills"
            unrelated = root / "templates" / "external-template.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("external\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "AGENT_FRAMEWORK_DIR": str(FRAMEWORK_ROOT),
                    "CODEX_SKILLS_DIR": str(skills),
                }
            )
            completed = subprocess.run(
                ["bash", str(FRAMEWORK_ROOT / "installers" / "install-codex.sh")],
                cwd=str(FRAMEWORK_ROOT),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stdout)
            self.assertTrue((root / "kernel" / "protocol.md").is_file())
            self.assertTrue(
                (root / "kernel" / "adaptive-execution-policy.md").is_file()
            )
            self.assertTrue((root / "scripts" / "framework-next").is_file())
            self.assertTrue((root / "scripts" / "agent-framework-route").is_file())
            self.assertTrue((skills / "framework-next" / "SKILL.md").is_file())
            self.assertEqual("external\n", unrelated.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
