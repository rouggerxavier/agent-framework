from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.execution_modes import (
    build_review_package,
    classify_review_finding,
    finding_blocks_delivery,
    migrate_state_execution_mode,
    review_policy,
    route_execution,
    should_create_persistent_state,
    should_reground,
    state_execution_mode,
    verification_budget_exceeded,
)
from tests.helpers import FRAMEWORK_ROOT


class AdaptiveRoutingTests(unittest.TestCase):
    def test_simple_task_defaults_to_fast_without_creating_agent_state(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            decision = route_execution("Corrija o texto da resposta deste endpoint.")
            self.assertEqual("fast", decision["selected_mode"])
            self.assertFalse(decision["policy"]["create_persistent_state"])
            self.assertFalse((root / ".agent").exists())
            self.assertNotIn("skills/framework-next/SKILL.md", decision["assets_selected"])

    def test_moderate_feature_routes_to_standard_short_flow(self) -> None:
        decision = route_execution(
            "Implemente um novo endpoint e testes seguindo o padrão existente."
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual("integrated", decision["policy"]["review_strategy"])
        self.assertFalse(decision["policy"]["plan_seal"])
        self.assertFalse(decision["policy"]["independent_reviews"])

    def test_destructive_migration_routes_to_critical_full_kernel(self) -> None:
        decision = route_execution(
            "Faça uma migration destrutiva com backfill e rollback complexo."
        )
        self.assertEqual("critical", decision["selected_mode"])
        self.assertTrue(decision["policy"]["task_contract"])
        self.assertTrue(decision["policy"]["evidence_ledger"])
        self.assertEqual("split", decision["policy"]["review_strategy"])
        self.assertIn("skills/framework-next/SKILL.md", decision["assets_selected"])

    def test_simple_backend_change_is_not_automatically_critical(self) -> None:
        decision = route_execution(
            "No backend, altere somente o texto de uma resposta existente."
        )
        self.assertEqual("fast", decision["selected_mode"])
        self.assertEqual([], decision["risk_factors"])

    def test_explicit_user_mode_is_respected(self) -> None:
        self.assertEqual(
            "fast",
            route_execution("--fast adicione um endpoint novo")["selected_mode"],
        )
        self.assertEqual(
            "standard",
            route_execution("--standard corrija o typo")["selected_mode"],
        )
        self.assertEqual(
            "critical",
            route_execution("--critical corrija o typo")["selected_mode"],
        )

    def test_explicit_fast_escalates_only_for_grave_risk_with_reason(self) -> None:
        decision = route_execution(
            "--fast altere autenticação e autorização do sistema"
        )
        self.assertEqual("critical", decision["selected_mode"])
        self.assertTrue(decision["escalated"])
        self.assertIn("grave security or data-loss risk", decision["reason"])

    def test_router_cli_emits_required_contract(self) -> None:
        completed = subprocess.run(
            [
                str(FRAMEWORK_ROOT / "scripts" / "agent-framework-route"),
                "--auto",
                "Corrija um bug simples no filtro.",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout)
        self.assertNotIn("RuntimeWarning", completed.stdout)
        for field in (
            "selected_mode:",
            "reason:",
            "risk_factors:",
            "complexity_factors:",
            "assets_selected:",
            "assets_skipped:",
        ):
            self.assertIn(field, completed.stdout)
        self.assertIn("risk_factors: []", completed.stdout)
        self.assertIn("complexity_factors: []", completed.stdout)


class AdaptivePolicyTests(unittest.TestCase):
    def test_standard_persistence_is_opt_in_by_need(self) -> None:
        self.assertFalse(should_create_persistent_state("standard"))
        self.assertTrue(
            should_create_persistent_state("standard", crosses_sessions=True)
        )
        self.assertTrue(
            should_create_persistent_state("standard", user_requested=True)
        )
        self.assertFalse(should_create_persistent_state("fast", user_requested=True))
        self.assertTrue(should_create_persistent_state("critical"))

    def test_review_modes_and_localized_correction_scope(self) -> None:
        self.assertEqual("integrated", review_policy("fast")["review_mode"])
        self.assertEqual("integrated", review_policy("standard")["review_mode"])
        self.assertEqual("split", review_policy("critical")["review_mode"])
        self.assertEqual(
            "affected-diff-and-criteria",
            review_policy("standard", localized_correction=True)["scope"],
        )

    def test_speculative_finding_never_blocks(self) -> None:
        classification = classify_review_finding(
            "BLOCKER",
            reachability="No real caller was found.",
            likelihood="theoretical",
            impact="Unknown.",
            supporting_evidence=[],
        )
        self.assertEqual("SPECULATIVE", classification)
        self.assertFalse(finding_blocks_delivery(classification))

    def test_blocker_requires_reachability_likelihood_impact_and_evidence(self) -> None:
        missing_evidence = classify_review_finding(
            "BLOCKER",
            reachability="Production request path.",
            likelihood="likely",
            impact="Acceptance criterion fails.",
            acceptance_failure=True,
        )
        proven = classify_review_finding(
            "BLOCKER",
            reachability="Production request path.",
            likelihood="reproduced",
            impact="Acceptance criterion AC-2 fails.",
            supporting_evidence=["tests/test_filter.py::test_invalid_filter failed"],
            acceptance_failure=True,
            reproducible_regression=True,
        )
        self.assertEqual("SPECULATIVE", missing_evidence)
        self.assertEqual("BLOCKER", proven)
        self.assertTrue(finding_blocks_delivery(proven))

    def test_verification_budget_stops_speculative_extra_passes(self) -> None:
        self.assertTrue(
            verification_budget_exceeded(
                "fast",
                implementation_effort=10,
                verification_effort=3,
                full_review_passes=1,
            )
        )
        self.assertTrue(
            verification_budget_exceeded(
                "standard",
                implementation_effort=10,
                verification_effort=3,
                full_review_passes=2,
            )
        )
        self.assertFalse(
            verification_budget_exceeded(
                "standard",
                implementation_effort=10,
                verification_effort=4,
                full_review_passes=2,
                concrete_risk_remaining=True,
            )
        )
        self.assertFalse(
            verification_budget_exceeded(
                "critical",
                implementation_effort=1,
                verification_effort=10,
                full_review_passes=4,
            )
        )

    def test_grounding_is_reused_until_materially_invalidated(self) -> None:
        self.assertFalse(should_reground())
        self.assertTrue(should_reground(scope_changed=True))
        package = build_review_package(
            goal="Fix filter.",
            mode="fast",
            diff="diff --git ...",
            files_changed=["filter.py"],
            tests_run=[{"command": "pytest test_filter.py", "outcome": "passed"}],
            acceptance_or_expected_behavior=["Filter returns matching rows."],
            known_risks=[],
        )
        self.assertEqual(
            {
                "goal",
                "mode",
                "diff",
                "files_changed",
                "tests_run",
                "acceptance_or_expected_behavior",
                "known_risks",
            },
            set(package),
        )

    def test_legacy_persistent_state_defaults_safely_to_critical(self) -> None:
        old_state = {"schema_version": 1, "project": {"mode": "full"}}
        self.assertEqual("critical", state_execution_mode(old_state))
        migrated, changed = migrate_state_execution_mode(old_state)
        self.assertTrue(changed)
        self.assertEqual("critical", migrated["execution_mode"])
        self.assertNotIn("execution_mode", old_state)

    def test_invalid_persisted_execution_mode_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            state_execution_mode({"execution_mode": "auto"})
        with self.assertRaises(ValueError):
            state_execution_mode({"execution_mode": 3})


if __name__ == "__main__":
    unittest.main()
