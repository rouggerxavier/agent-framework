from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.execution_modes import (
    build_review_package,
    classify_review_finding,
    finding_blocks_delivery,
    migrate_state_execution_mode,
    plan_session_scope,
    review_policy,
    route_execution,
    should_create_persistent_state,
    should_reground,
    state_execution_mode,
    verification_scope_for_change,
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

    def test_ordinary_work_defaults_to_standard(self) -> None:
        decision = route_execution(
            "Implemente a tela de cadastro de fornecedores com os testes."
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual([], decision["risk_factors"])

    def test_moderate_feature_routes_to_standard_short_flow(self) -> None:
        decision = route_execution(
            "Implemente um novo endpoint e testes seguindo o padrão existente."
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual("integrated", decision["policy"]["review_strategy"])
        self.assertFalse(decision["policy"]["plan_seal"])
        self.assertFalse(decision["policy"]["independent_reviews"])

    def test_explicit_critical_routes_to_the_full_kernel(self) -> None:
        decision = route_execution(
            "--critical Faça uma migration destrutiva com backfill e rollback complexo."
        )
        self.assertEqual("critical", decision["selected_mode"])
        self.assertTrue(decision["policy"]["task_contract"])
        self.assertTrue(decision["policy"]["evidence_ledger"])
        self.assertEqual("split", decision["policy"]["review_strategy"])
        self.assertIn("skills/framework-next/SKILL.md", decision["assets_selected"])

    def test_a_detected_grave_damage_path_recommends_rather_than_escalates(
        self,
    ) -> None:
        decision = route_execution(
            "Faça uma migration destrutiva com backfill e rollback complexo."
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertIn("destructive_migration", decision["risk_factors"])
        self.assertIn("--critical", decision["reason"])

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

    def test_explicit_fast_never_escalates_past_standard(self) -> None:
        """An explicit mode is honoured; the harm is reported beside it.

        The floor is real — a sensitive area rules out `fast` — but the ceiling
        is the user's. Routing a request into `critical` on the strength of a
        phrase is what made an ordinary feature pay the heaviest lifecycle in
        the framework because its description contained the word `auth`.
        """

        decision = route_execution(
            "--fast troque o núcleo de autenticação e o core de sessões"
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertIn("auth_core_breakage", decision["risk_factors"])
        self.assertIn("--critical", decision["reason"])

    def test_touching_a_sensitive_area_blocks_fast_but_not_critical(self) -> None:
        decision = route_execution(
            "--fast ajuste o texto do formulário de login e da tela de pagamento"
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertTrue(decision["escalated"])
        self.assertIn(
            "fast rejected: sensitive area requires at least standard",
            decision["reason"],
        )
        self.assertEqual([], decision["risk_factors"])
        self.assertIn("authentication_area", decision["sensitive_areas"])
        self.assertIn("financial_area", decision["sensitive_areas"])

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

    def test_legacy_persistent_state_defaults_to_standard(self) -> None:
        old_state = {"schema_version": 1, "project": {"mode": "full"}}
        self.assertEqual("standard", state_execution_mode(old_state))
        migrated, changed = migrate_state_execution_mode(old_state)
        self.assertTrue(changed)
        self.assertEqual("standard", migrated["execution_mode"])
        self.assertNotIn("execution_mode", old_state)

    def test_invalid_persisted_execution_mode_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            state_execution_mode({"execution_mode": "auto"})
        with self.assertRaises(ValueError):
            state_execution_mode({"execution_mode": 3})


class SessionScopeTests(unittest.TestCase):
    def test_large_work_is_split_and_only_one_unit_runs_per_session(self) -> None:
        plan = plan_session_scope(["Fase C", "Fase D", "Fase E"])
        self.assertEqual(["Fase C"], plan["planned_units"])
        self.assertEqual(["Fase D", "Fase E"], plan["deferred_units"])
        self.assertFalse(plan["auto_advance_to_next_phase"])
        self.assertFalse(plan["volume_is_blocker"])
        self.assertTrue(plan["requires_explicit_continuation"])

    def test_work_inside_the_budget_keeps_going(self) -> None:
        plan = plan_session_scope(
            ["fatia única"], elapsed_minutes=12.0, minutes_to_finish_current_unit=8.0
        )
        self.assertEqual("continue", plan["checkpoint"]["action"])
        self.assertFalse(plan["checkpoint"]["commit_required"])

    def test_correction_minutes_from_done_finishes_before_the_checkpoint(self) -> None:
        plan = plan_session_scope(
            ["correção pendente"],
            elapsed_minutes=52.0,
            minutes_to_finish_current_unit=4.0,
        )
        self.assertEqual("finish-current-unit", plan["checkpoint"]["action"])
        self.assertTrue(plan["checkpoint"]["commit_required"])
        self.assertTrue(plan["checkpoint"]["handoff_required"])

    def test_long_remaining_work_stops_at_the_checkpoint(self) -> None:
        plan = plan_session_scope(
            ["fase inteira"],
            elapsed_minutes=48.0,
            minutes_to_finish_current_unit=40.0,
        )
        self.assertEqual("checkpoint-now", plan["checkpoint"]["action"])
        self.assertTrue(plan["checkpoint"]["commit_required"])

    def test_explicit_full_run_keeps_every_unit_in_one_session(self) -> None:
        plan = plan_session_scope(
            ["Fase C", "Fase D"],
            elapsed_minutes=90.0,
            minutes_to_finish_current_unit=30.0,
            full_run_requested=True,
        )
        self.assertEqual(["Fase C", "Fase D"], plan["planned_units"])
        self.assertEqual([], plan["deferred_units"])
        self.assertEqual("continue", plan["checkpoint"]["action"])

    def test_explicit_continuation_does_not_require_more_ceremony(self) -> None:
        plan = plan_session_scope(
            ["Fase D", "Fase E"], continuation_requested=True
        )
        self.assertEqual(["Fase D"], plan["planned_units"])
        self.assertFalse(plan["requires_explicit_continuation"])

    def test_routing_exposes_session_limits_without_auto_advance(self) -> None:
        policy = route_execution("Implemente um endpoint novo com testes.")["policy"]
        self.assertEqual(1, policy["session_scope"]["max_units_per_session"])
        self.assertEqual(30, policy["session_scope"]["soft_checkpoint_minutes"])
        self.assertEqual(45, policy["session_scope"]["hard_checkpoint_minutes"])
        self.assertFalse(policy["auto_advance_to_next_phase"])


class ReviewRoundTests(unittest.TestCase):
    def test_one_review_round_and_one_correction_round(self) -> None:
        policy = review_policy("standard")
        self.assertEqual(1, policy["max_review_rounds"])
        self.assertEqual(1, policy["max_correction_rounds"])
        self.assertTrue(policy["another_review_round_allowed"])

        after_correction = review_policy(
            "standard",
            localized_correction=True,
            completed_review_rounds=1,
            completed_correction_rounds=1,
        )
        self.assertFalse(after_correction["another_review_round_allowed"])
        self.assertFalse(after_correction["another_correction_round_allowed"])
        self.assertEqual("affected-diff-and-criteria", after_correction["scope"])

    def test_single_reviewer_per_diff_outside_critical(self) -> None:
        self.assertEqual(1, review_policy("fast")["reviewers_per_diff"])
        self.assertEqual(1, review_policy("standard")["reviewers_per_diff"])
        self.assertEqual(2, review_policy("critical")["reviewers_per_diff"])
        self.assertTrue(review_policy("fast")["additional_reviewer_requires_evidence"])

    def test_surviving_blockers_escalate_instead_of_looping(self) -> None:
        policy = review_policy(
            "standard",
            completed_review_rounds=1,
            completed_correction_rounds=1,
            unresolved_blockers=True,
        )
        self.assertFalse(policy["another_review_round_allowed"])
        self.assertTrue(policy["escalate_instead_of_looping"])


class TestScopeTests(unittest.TestCase):
    def test_small_local_change_does_not_replay_the_full_suite(self) -> None:
        scope = verification_scope_for_change(
            "standard", change_size="small", full_suite_already_green=True
        )
        self.assertEqual("targeted", scope["scope"])
        self.assertFalse(scope["run_full_suite"])

    def test_broader_diff_gets_proportional_verification(self) -> None:
        scope = verification_scope_for_change("standard", change_size="broad")
        self.assertEqual("proportional", scope["scope"])
        self.assertFalse(scope["run_full_suite"])

    def test_full_suite_runs_at_phase_closure_and_pull_request(self) -> None:
        self.assertTrue(
            verification_scope_for_change("standard", phase_closure=True)["run_full_suite"]
        )
        self.assertTrue(
            verification_scope_for_change("fast", pull_request=True)["run_full_suite"]
        )

    def test_selector_failure_reuses_the_running_environment(self) -> None:
        scope = verification_scope_for_change("standard", failure_kind="selector")
        self.assertFalse(scope["rebuild_environment"])
        self.assertTrue(scope["rerun_failing_spec_only"])

    def test_build_failure_or_stopped_environment_rebuilds(self) -> None:
        self.assertTrue(
            verification_scope_for_change("standard", failure_kind="build")["rebuild_environment"]
        )
        self.assertTrue(
            verification_scope_for_change("standard", environment_running=False)[
                "rebuild_environment"
            ]
        )

    def test_unknown_change_size_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            verification_scope_for_change("standard", change_size="enormous")


if __name__ == "__main__":
    unittest.main()
