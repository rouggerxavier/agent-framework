"""CI gates integration, not continuous development.

Every case here is a scenario where the old implicit rule — push, wait for CI,
only then continue — cost throughput without buying safety, plus the cases where
waiting is genuinely the right answer.
"""

from pathlib import Path
import subprocess
import unittest

from kernel.runtime.execution_modes import _parser
from kernel.runtime.ci_policy import (
    SECURITY_CORE_HARM_FACTORS,
    audit_scope_after_green,
    ci_decision,
    ci_decision_for_request,
    classify_change_impacts,
    classify_next_work,
    concurrency_recommendation,
    documentation_checkpoint_policy,
    post_merge_observation,
    runner_policy,
    select_ci_profile,
    select_gates,
    select_wait_policy,
)
from kernel.runtime.execution_modes import (
    SEVERE_HARM_FACTORS,
    ci_context_from_arguments,
    main as route_main,
    route_execution,
    verification_for_ci,
    verification_scope_for_change,
)
from tests.helpers import FRAMEWORK_ROOT


class CiProfileTests(unittest.TestCase):
    def test_frontend_standard_is_targeted_background_and_lets_work_continue(self) -> None:
        """Case A: the shape of most work in the framework.

        A `standard` frontend change owes the gates of the surface it touched
        and nothing else, CI runs in the background, and the next unit starts.
        """

        decision = ci_decision(execution_mode="standard", impacts=["frontend"])
        self.assertEqual("targeted", decision["ci_profile"])
        self.assertEqual("background", decision["ci_wait_policy"])
        self.assertEqual("before_merge", decision["ci_blocking_point"])
        self.assertEqual("continue_independent", decision["next_work_policy"])
        self.assertEqual([], decision["next_work_blockers"])
        self.assertNotIn("full-suite", decision["remote_gates"])
        self.assertIn("component-tests-affected", decision["remote_gates"])

    def test_critical_migration_is_full_and_blocks_before_integration(self) -> None:
        """Case B: `full` is what a migration buys, and it gates the merge.

        It gates the *merge*. With safe work available the wait stays
        `background` and the hold is on publication, not on the keyboard.
        """

        decision = ci_decision(execution_mode="critical", impacts=["database", "backend"])
        self.assertEqual("full", decision["ci_profile"])
        self.assertEqual("before_merge", decision["ci_blocking_point"])
        self.assertEqual("background", decision["ci_wait_policy"])
        self.assertTrue(decision["publication_hold"])
        self.assertIn("migration-forward-and-rollback", decision["remote_gates"])
        self.assertIn("full-suite", decision["remote_gates"])
        self.assertTrue(decision["merge_blockers"])
        # Blocking the merge is not blocking the keyboard.
        self.assertEqual([], decision["next_work_blockers"])

    def test_full_profile_waits_only_when_no_safe_work_is_left(self) -> None:
        decision = ci_decision(
            execution_mode="critical", impacts=["database"], has_next_unit=False
        )
        self.assertEqual("blocking_before_merge", decision["ci_wait_policy"])
        self.assertEqual("before_merge", decision["ci_blocking_point"])
        self.assertTrue(decision["publication_hold"])
        self.assertIn("pending", decision["blocker_report"]["merge_blocker"])

    def test_neither_full_nor_critical_nor_a_running_job_creates_a_wait_now(self) -> None:
        """The negative case: `blocking_now` is never a side effect of a profile."""

        decision = ci_decision(
            execution_mode="critical",
            impacts=["database", "security_core"],
            runner_kind="self_hosted_shared",
            remote_ci_running=True,
        )
        self.assertEqual("full", decision["ci_profile"])
        self.assertNotEqual("blocking_now", decision["ci_wait_policy"])
        self.assertEqual([], decision["next_work_blockers"])
        self.assertEqual(
            [], select_wait_policy(ci_profile="full", execution_mode="critical")[
                "blocking_now_reasons"
            ]
        )

    def test_docs_only_change_is_minimal(self) -> None:
        """Case C: a README owes no pipeline."""

        decision = ci_decision(execution_mode="standard", impacts=["docs"])
        self.assertEqual("minimal", decision["ci_profile"])
        self.assertEqual(["docs-check"], decision["remote_gates"])
        deferred = {item["gate"] for item in decision["deferred_gates"]}
        self.assertIn("full-suite", deferred)
        self.assertIn("unit-tests-affected", deferred)

    def test_refactor_claimed_mechanical_but_unproven_gets_targeted(self) -> None:
        unproven = select_ci_profile(impacts=["mechanical_refactor"])
        proven = select_ci_profile(
            impacts=["mechanical_refactor"], mechanical_change_proven=True
        )
        self.assertEqual("targeted", unproven["ci_profile"])
        self.assertEqual("minimal", proven["ci_profile"])

    def test_explicit_minimal_is_raised_when_the_change_owes_full(self) -> None:
        decision = select_ci_profile(impacts=["database"], requested_profile="minimal")
        self.assertEqual("full", decision["ci_profile"])
        self.assertEqual("minimal", decision["escalated_from"])
        self.assertIn("database", decision["reason"])

    def test_irreversible_or_application_wide_change_owes_full(self) -> None:
        self.assertEqual(
            "full",
            select_ci_profile(impacts=["backend"], reversibility="irreversible")["ci_profile"],
        )
        self.assertEqual(
            "full",
            select_ci_profile(impacts=["backend"], blast_radius="tenant-wide")["ci_profile"],
        )

    def test_sensitive_area_adds_a_scan_without_buying_the_whole_pipeline(self) -> None:
        """The distinction the mode router already makes, kept on the CI axis.

        Mentioning a login screen is proximity to a sensitive area, not a change
        to the authentication core. It earns a security scan, not `full`.
        """

        decision = ci_decision(
            execution_mode="standard",
            impacts=["frontend"],
            sensitive_areas=["authentication_area"],
        )
        self.assertEqual("targeted", decision["ci_profile"])
        self.assertIn("security-scan", decision["remote_gates"])

    def test_security_core_harm_factors_mirror_the_router_vocabulary(self) -> None:
        self.assertTrue(SECURITY_CORE_HARM_FACTORS <= SEVERE_HARM_FACTORS)

    def test_named_grave_damage_path_makes_the_change_security_core(self) -> None:
        impacts = classify_change_impacts(
            "Ajuste o endpoint", severe_harm_factors=["privilege_escalation"]
        )
        self.assertIn("security_core", impacts)
        self.assertEqual("full", select_ci_profile(impacts=impacts)["ci_profile"])

    def test_unknown_impact_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            select_ci_profile(impacts=["telepathy"])


class E2ETierTests(unittest.TestCase):
    def test_full_regression_is_deferred_outside_the_full_profile(self) -> None:
        gates = select_gates(ci_profile="targeted", impacts=["frontend", "e2e_relevant"])
        self.assertEqual("focal", gates["e2e_tier"])
        deferred = {item["gate"]: item["runs_at"] for item in gates["deferred_gates"]}
        self.assertIn("e2e-full-regression", deferred)
        self.assertIn("nightly", deferred["e2e-full-regression"])

    def test_critical_user_paths_are_never_weakened_silently(self) -> None:
        gates = select_gates(
            ci_profile="targeted", impacts=["frontend"], critical_user_paths_touched=True
        )
        self.assertEqual("operational", gates["e2e_tier"])

    def test_full_profile_runs_the_regression_tier(self) -> None:
        gates = select_gates(ci_profile="full", impacts=["release"])
        self.assertEqual("full_regression", gates["e2e_tier"])
        self.assertIn("full-suite", gates["gates"])


class NextWorkTests(unittest.TestCase):
    def test_dependent_next_unit_stacks_locally_without_publishing(self) -> None:
        """Case D: dependency is a reason to branch locally, not to idle."""

        decision = ci_decision(
            execution_mode="standard",
            impacts=["backend"],
            next_unit_depends_on_current=True,
        )
        self.assertEqual("stack_local", decision["next_work_policy"])
        self.assertEqual("pending-head", decision["next_work"]["branch_base"])
        self.assertFalse(decision["next_work"]["publish_dependent_pr"])
        self.assertTrue(decision["next_work"]["rebase_after_parent_merge"])

    def test_explicitly_stacked_workflow_may_publish_the_dependent_pr(self) -> None:
        decision = classify_next_work(
            depends_on_pending_unit=True, stacked_prs_supported=True
        )
        self.assertEqual("stack_local", decision["next_work_policy"])
        self.assertTrue(decision["publish_dependent_pr"])

    def test_independent_next_unit_starts_from_the_integration_base(self) -> None:
        """Case E: a pending pull request is not a lock on the repository."""

        decision = ci_decision(execution_mode="standard", impacts=["frontend"])
        self.assertEqual("continue_independent", decision["next_work_policy"])
        self.assertEqual("integration-base", decision["next_work"]["branch_base"])
        self.assertEqual(
            "new-from-integration-base", decision["next_work"]["worktree"]
        )

    def test_wait_needs_a_named_reason(self) -> None:
        for field in (
            "next_decision_depends_on_ci",
            "critical_risk_forbids_speculation",
            "external_dependency_blocks",
        ):
            with self.subTest(field=field):
                decision = classify_next_work(**{field: True})
                self.assertEqual("wait", decision["next_work_policy"])
        self.assertEqual(
            "continue_independent", classify_next_work()["next_work_policy"]
        )

    def test_blocking_now_is_earned_by_a_concrete_reason(self) -> None:
        self.assertEqual("background", select_wait_policy()["ci_wait_policy"])
        for field in (
            "next_decision_depends_on_ci",
            "release_in_progress",
            "deploy_in_progress",
            "external_dependency_blocks",
            "speculative_work_forbidden",
        ):
            with self.subTest(field=field):
                decision = select_wait_policy(**{field: True})
                self.assertEqual("blocking_now", decision["ci_wait_policy"])
                self.assertEqual("now", decision["ci_blocking_point"])
                self.assertTrue(decision["next_work_blocked"])


class SharedRunnerTests(unittest.TestCase):
    def test_busy_shared_runner_holds_heavy_jobs_and_never_the_keyboard(self) -> None:
        """Case F: contention throttles machines, not editing."""

        policy = runner_policy(
            runner_kind="self_hosted_shared",
            remote_ci_running=True,
            planned_local_workloads=[
                "edit the reducer",
                "pnpm test:e2e (playwright)",
                "docker compose build",
                "npx next build",
            ],
        )
        self.assertTrue(policy["contention"])
        self.assertFalse(policy["allow_local_heavy_jobs"])
        self.assertEqual(["edit the reducer"], policy["local_workloads_allowed"])
        held = {item["kind"] for item in policy["local_workloads_on_hold"]}
        self.assertEqual({"browser_e2e", "container_build", "bundler_build"}, held)
        for allowed in ("read", "edit", "plan", "analyse", "review-diff"):
            self.assertIn(allowed, policy["allowed_local_work"])
        self.assertIn("contention", policy["interpretation_note"])

    def test_contention_is_not_reported_as_runner_instability(self) -> None:
        policy = runner_policy(runner_kind="self_hosted_shared", remote_ci_running=True)
        self.assertIn("do not report them as", policy["interpretation_note"])
        self.assertNotIn("unstable", policy["reason"])

    def test_hosted_and_dedicated_runners_do_not_throttle_local_work(self) -> None:
        for kind in ("hosted", "self_hosted_dedicated"):
            with self.subTest(kind=kind):
                policy = runner_policy(
                    runner_kind=kind,
                    remote_ci_running=True,
                    planned_local_workloads=["pnpm test:e2e"],
                )
                self.assertFalse(policy["contention"])
                self.assertTrue(policy["allow_local_heavy_jobs"])
                self.assertEqual(["pnpm test:e2e"], policy["local_workloads_allowed"])

    def test_hosted_runners_are_a_capability_not_a_requirement(self) -> None:
        policy = runner_policy(runner_kind="self_hosted_shared")
        self.assertFalse(policy["contention"])
        self.assertNotIn("github", policy["reason"].lower())

    def test_contention_moves_moderate_gates_off_the_local_budget(self) -> None:
        decision = ci_decision(
            execution_mode="standard",
            impacts=["backend"],
            runner_kind="self_hosted_shared",
            remote_ci_running=True,
        )
        self.assertIn("lint", decision["local_gates"])
        self.assertNotIn("integration-tests-affected", decision["local_gates"])
        self.assertIn("integration-tests-affected", decision["remote_gates"])
        self.assertTrue(decision["local_gates_on_hold"])

    def test_unknown_runner_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            runner_policy(runner_kind="borrowed-laptop")


class PostMergeTests(unittest.TestCase):
    def test_validated_merge_tree_with_observational_main_frees_the_next_unit(self) -> None:
        """Case G: main re-running the same gates is a report, not permission."""

        decision = ci_decision(
            execution_mode="standard",
            impacts=["backend"],
            unit_merged=True,
            merge_tree_validated_by_pr=True,
            main_status="green",
        )
        observation = decision["post_merge_observation"]
        self.assertEqual("observation", observation["role"])
        self.assertFalse(observation["blocks_next_unit"])
        self.assertTrue(observation["investigate_on_red"])

    def test_main_workflow_with_a_new_gate_is_still_a_gate(self) -> None:
        observation = post_merge_observation(
            merge_tree_validated_by_pr=True, main_adds_new_gate=True
        )
        self.assertEqual("gate", observation["role"])
        self.assertTrue(observation["blocks_next_unit"])

    def test_unvalidated_merge_tree_is_still_a_gate(self) -> None:
        observation = post_merge_observation(merge_tree_validated_by_pr=False)
        self.assertEqual("gate", observation["role"])
        self.assertTrue(observation["blocks_next_unit"])

    def test_red_main_is_an_incident_and_is_never_ignored(self) -> None:
        observation = post_merge_observation(
            merge_tree_validated_by_pr=True, main_status="red"
        )
        self.assertEqual("incident", observation["role"])
        self.assertTrue(observation["blocks_next_unit"])
        self.assertTrue(observation["investigate_on_red"])


class SupersededAndAuditTests(unittest.TestCase):
    def test_superseded_runs_are_cancelled(self) -> None:
        recommendation = concurrency_recommendation(unit_ref="pr-42")
        self.assertEqual("ci-pr-42", recommendation["group"])
        self.assertTrue(recommendation["cancel_in_progress"])

    def test_audit_is_incremental_when_nothing_moved(self) -> None:
        self.assertEqual(
            "incremental", audit_scope_after_green()["audit_scope"]
        )
        for field in ("head_changed", "scope_changed"):
            with self.subTest(field=field):
                self.assertEqual(
                    "full", audit_scope_after_green(**{field: True})["audit_scope"]
                )
        self.assertEqual(
            "full",
            audit_scope_after_green(previous_gates_valid=False)["audit_scope"],
        )

    def test_open_blockers_are_audited_even_incrementally(self) -> None:
        decision = audit_scope_after_green(open_blockers=True, new_evidence=True)
        self.assertEqual("incremental", decision["audit_scope"])
        self.assertIn("open blockers", decision["audit_targets"])

    def test_documentation_checkpoint_defaults_to_background(self) -> None:
        self.assertFalse(documentation_checkpoint_policy()["blocks_next_unit"])
        self.assertTrue(
            documentation_checkpoint_policy(
                stale_docs_risk_incorrect_implementation=True
            )["blocks_next_unit"]
        )
        self.assertTrue(
            documentation_checkpoint_policy(documents_contract_or_interface=True)[
                "blocks_next_unit"
            ]
        )


class RouterIntegrationTests(unittest.TestCase):
    def test_router_reports_the_ci_axis_without_changing_the_mode(self) -> None:
        decision = route_execution("Implemente a tela de fornecedores com os testes.")
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual("targeted", decision["ci"]["ci_profile"])
        self.assertEqual("background", decision["ci"]["ci_wait_policy"])

    def test_standard_mode_does_not_imply_a_full_pipeline(self) -> None:
        docs = route_execution("Atualize o README e o CHANGELOG com a nova secao.")
        migration = route_execution(
            "--critical Rode a migration no banco de dados com backfill."
        )
        self.assertEqual("minimal", docs["ci"]["ci_profile"])
        self.assertEqual("full", migration["ci"]["ci_profile"])
        self.assertEqual("before_merge", migration["ci"]["ci_blocking_point"])
        self.assertEqual("background", migration["ci"]["ci_wait_policy"])

    def test_router_accepts_context_the_request_text_cannot_carry(self) -> None:
        decision = route_execution(
            "Implemente o endpoint de fornecedores.",
            ci_context={
                "runner_kind": "self_hosted_shared",
                "remote_ci_running": True,
                "next_unit_depends_on_current": True,
            },
        )
        self.assertEqual("stack_local", decision["ci"]["next_work_policy"])
        self.assertTrue(decision["ci"]["runner_policy"]["contention"])

    def test_unknown_ci_context_field_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ci_decision_for_request("qualquer coisa", context={"runner": "hosted"})

    def test_existing_router_consumers_keep_their_fields(self) -> None:
        decision = route_execution("Corrija o typo no titulo da pagina.")
        for field in (
            "selected_mode",
            "reason",
            "risk_factors",
            "sensitive_areas",
            "fast_factors",
            "complexity_factors",
            "assets_selected",
            "assets_skipped",
            "requested_mode",
            "escalated",
            "policy",
        ):
            self.assertIn(field, decision)

    def test_router_cli_emits_the_ci_contract(self) -> None:
        completed = subprocess.run(
            [
                str(FRAMEWORK_ROOT / "scripts" / "agent-framework-route"),
                "--auto",
                "Implemente o endpoint de fornecedores e os testes.",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout)
        for field in (
            "ci_profile:",
            "ci_blocking_point:",
            "ci_wait_policy:",
            "next_work_policy:",
            "local_gates:",
            "remote_gates:",
            "deferred_gates:",
            "runner_policy:",
        ):
            self.assertIn(field, completed.stdout)


class CiContextIngressTests(unittest.TestCase):
    """The policy is only real if the workflow can feed it.

    Operational state — which runner, what is running, what comes next — is
    data. Leaving it to be inferred from the request's prose is what made the
    policy unreachable from the actual command line.
    """

    def _context(self, argv):
        return ci_context_from_arguments(_parser().parse_args(argv + ["a request"]))

    def test_flags_carry_every_operational_field(self) -> None:
        context = self._context(
            [
                "--runner-kind",
                "self_hosted_shared",
                "--remote-ci-running",
                "--next-unit",
                "dependent",
                "--unit-merged",
                "--merge-tree-validated",
                "--main-status",
                "green",
                "--release-in-flight",
                "--deploy-in-flight",
                "--unit-ref",
                "pr-42",
                "--local-workload",
                "pnpm test:e2e",
            ]
        )
        self.assertEqual("self_hosted_shared", context["runner_kind"])
        self.assertTrue(context["remote_ci_running"])
        self.assertTrue(context["next_unit_depends_on_current"])
        self.assertTrue(context["has_next_unit"])
        self.assertTrue(context["unit_merged"])
        self.assertTrue(context["merge_tree_validated_by_pr"])
        self.assertEqual("green", context["main_status"])
        self.assertTrue(context["release_in_progress"])
        self.assertTrue(context["deploy_in_progress"])
        self.assertEqual("pr-42", context["unit_ref"])
        self.assertEqual(["pnpm test:e2e"], context["planned_local_workloads"])

    def test_json_context_is_accepted_and_flags_win_over_it(self) -> None:
        context = self._context(
            [
                "--ci-context-json",
                '{"runner_kind": "hosted", "remote_ci_running": true}',
                "--runner-kind",
                "self_hosted_shared",
            ]
        )
        self.assertEqual("self_hosted_shared", context["runner_kind"])
        self.assertTrue(context["remote_ci_running"])

    def test_invalid_context_fails_with_a_clear_message(self) -> None:
        for argv, fragment in (
            (["--ci-context-json", "not json"], "not valid JSON"),
            (["--ci-context-json", "[1]"], "must be a JSON object"),
            (["--ci-context-json", '{"runner": "hosted"}'], "unknown ci context field"),
        ):
            with self.subTest(argv=argv):
                with self.assertRaises(ValueError) as error:
                    self._context(argv)
                self.assertIn(fragment, str(error.exception))

    def test_invalid_context_values_are_rejected_by_the_policy(self) -> None:
        for context, fragment in (
            ({"remote_ci_running": "yes"}, "must be a boolean"),
            ({"runner_kind": "laptop"}, "unknown runner kind"),
            ({"requested_profile": "paranoid"}, "unknown ci profile"),
            ({"planned_local_workloads": "docker build"}, "must be a list"),
        ):
            with self.subTest(context=context):
                with self.assertRaises(ValueError) as error:
                    ci_decision_for_request("qualquer coisa", context=context)
                self.assertIn(fragment, str(error.exception))

    def test_operational_context_is_never_mixed_into_the_task_text(self) -> None:
        """The flags describe the machine; the positional argument describes the work."""

        arguments = _parser().parse_args(
            ["--auto", "--runner-kind", "hosted", "Implemente", "o", "endpoint"]
        )
        self.assertEqual(["Implemente", "o", "endpoint"], arguments.request)
        self.assertEqual({"runner_kind": "hosted"}, ci_context_from_arguments(arguments))

    def test_the_cli_accepts_the_context_end_to_end(self) -> None:
        completed = subprocess.run(
            [
                str(FRAMEWORK_ROOT / "scripts" / "agent-framework-route"),
                "--auto",
                "--runner-kind",
                "self_hosted_shared",
                "--remote-ci-running",
                "--next-unit",
                "dependent",
                "--unit-ref",
                "pr-42",
                "Implemente a tela de fornecedores no frontend.",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout)
        self.assertIn("next_work_policy: stack_local", completed.stdout)
        self.assertIn("MERGE BLOCKER:", completed.stdout)
        self.assertIn("NEXT-WORK BLOCKER: none — stack_local permitted", completed.stdout)
        self.assertIn("POST-MERGE OBSERVATION:", completed.stdout)

    def test_an_invalid_runner_kind_fails_the_cli_with_a_message(self) -> None:
        completed = subprocess.run(
            [
                str(FRAMEWORK_ROOT / "scripts" / "agent-framework-route"),
                "--auto",
                "--ci-context-json",
                '{"runner_kind": "laptop"}',
                "qualquer coisa",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("unknown runner kind", completed.stdout)


class DefaultContextTests(unittest.TestCase):
    def test_no_context_keeps_the_documented_defaults(self) -> None:
        decision = ci_decision_for_request("Implemente o endpoint de fornecedores.")
        self.assertEqual("unknown", decision["runner_policy"]["runner_kind"])
        self.assertTrue(decision["runner_policy"]["shares_development_machine"])
        self.assertFalse(decision["runner_policy"]["remote_ci_running"])
        self.assertEqual("continue_independent", decision["next_work_policy"])
        self.assertEqual("not_applicable", decision["post_merge_observation"]["role"])

    def test_unknown_runner_is_conservative_only_while_a_run_executes(self) -> None:
        idle = runner_policy(runner_kind="unknown")
        busy = runner_policy(runner_kind="unknown", remote_ci_running=True)
        self.assertFalse(idle["contention"])
        self.assertTrue(idle["allow_local_heavy_jobs"])
        self.assertTrue(busy["contention"])
        # Conservative about the machine, never about the keyboard.
        self.assertIn("read", busy["allowed_local_work"])
        self.assertIn("edit", busy["allowed_local_work"])
        self.assertIn("Declare the runner kind", idle["reason"])

    def test_an_undeclared_dependency_is_not_a_confirmed_dependency(self) -> None:
        decision = classify_next_work()
        self.assertEqual("continue_independent", decision["next_work_policy"])
        self.assertIn("not declared dependent", decision["reason"])
        self.assertEqual(
            "stack_local",
            classify_next_work(depends_on_pending_unit=True)["next_work_policy"],
        )

    def test_context_defaults_are_documented_where_the_policy_lives(self) -> None:
        content = (FRAMEWORK_ROOT / "kernel" / "ci-throughput-policy.md").read_text(
            encoding="utf-8"
        )
        for field in ("runner_kind", "next_unit_depends_on_current", "unit_merged"):
            self.assertIn(field, content)


class EndToEndPropagationTests(unittest.TestCase):
    """route_execution → ci_profile → verification decision → gates.

    Testing `ci_policy` alone proves the policy is coherent, not that it
    reaches the work. These cross the boundary the workflow actually crosses.
    """

    def test_frontend_standard_journey_never_replays_the_full_suite(self) -> None:
        decision = route_execution(
            "Implemente a nova tela de listagem de fornecedores no frontend."
        )
        ci = decision["ci"]
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual("targeted", ci["ci_profile"])

        verification = verification_for_ci(
            decision["selected_mode"], ci, pull_request=True
        )
        self.assertFalse(verification["run_full_suite"])
        self.assertEqual("targeted", verification["scope"])
        self.assertEqual(verification, ci["local_verification"])
        self.assertIn("component-tests-affected", ci["remote_gates"])
        self.assertNotIn("full-suite", ci["remote_gates"])

    def test_critical_migration_journey_keeps_complete_verification(self) -> None:
        decision = route_execution(
            "--critical Rode a migration no banco de dados com backfill e rollback."
        )
        ci = decision["ci"]
        self.assertEqual("critical", decision["selected_mode"])
        self.assertEqual("full", ci["ci_profile"])
        self.assertTrue(ci["local_verification"]["run_full_suite"])
        self.assertTrue(
            verification_for_ci(decision["selected_mode"], ci, pull_request=True)[
                "run_full_suite"
            ]
        )
        self.assertIn("full-suite", ci["remote_gates"])

    def test_a_busy_shared_runner_reaches_the_verification_decision(self) -> None:
        decision = route_execution(
            "Implemente a nova tela de fornecedores no frontend.",
            ci_context={
                "runner_kind": "self_hosted_shared",
                "remote_ci_running": True,
            },
        )
        self.assertFalse(decision["ci"]["local_verification"]["run_full_suite"])
        self.assertFalse(
            decision["ci"]["runner_policy"]["allow_local_heavy_jobs"]
        )

    def test_login_copy_change_stays_targeted_with_a_security_gate(self) -> None:
        """Pinned: proximity to a sensitive area is not the security core."""

        decision = route_execution(
            "Ajuste o texto e o espacamento do formulario de login."
        )
        ci = decision["ci"]
        self.assertNotIn("security_core", ci["change_impacts"])
        self.assertEqual("targeted", ci["ci_profile"])
        self.assertIn("security-scan", ci["remote_gates"])
        self.assertFalse(ci["local_verification"]["run_full_suite"])


class VerificationScopeCompatibilityTests(unittest.TestCase):
    def test_pull_request_still_asks_for_the_full_suite_without_a_profile(self) -> None:
        self.assertTrue(
            verification_scope_for_change("standard", pull_request=True)["run_full_suite"]
        )

    def test_targeted_profile_leaves_the_full_suite_to_ci(self) -> None:
        scope = verification_scope_for_change(
            "standard", pull_request=True, ci_profile="targeted"
        )
        self.assertFalse(scope["run_full_suite"])
        self.assertEqual("targeted", scope["scope"])

    def test_full_profile_still_runs_the_complete_suite(self) -> None:
        scope = verification_scope_for_change(
            "critical", pull_request=True, ci_profile="full"
        )
        self.assertTrue(scope["run_full_suite"])

    def test_busy_shared_runner_keeps_local_verification_light(self) -> None:
        scope = verification_scope_for_change(
            "standard",
            pull_request=True,
            ci_profile="targeted",
            local_heavy_jobs_allowed=False,
        )
        self.assertFalse(scope["run_full_suite"])

    def test_unknown_ci_profile_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            verification_scope_for_change("standard", ci_profile="paranoid")


class AssetTests(unittest.TestCase):
    def test_the_policy_and_its_asset_are_installed_with_the_framework(self) -> None:
        self.assertTrue((FRAMEWORK_ROOT / "kernel" / "ci-throughput-policy.md").is_file())
        self.assertTrue(
            (FRAMEWORK_ROOT / "skills" / "ci-throughput-controller" / "SKILL.md").is_file()
        )
        self.assertTrue(
            (FRAMEWORK_ROOT / "templates" / "ci-throughput-decision.md").is_file()
        )

    def test_the_router_points_at_the_ci_asset(self) -> None:
        content = (
            FRAMEWORK_ROOT / "skills" / "agent-framework-router" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("ci-throughput-controller", content)
        self.assertIn("ci_profile", content)
        self.assertIn("next_work_policy", content)

    def test_the_workflow_document_covers_the_operational_sequence(self) -> None:
        content = (FRAMEWORK_ROOT / "workflows" / "ci-throughput.md").read_text(
            encoding="utf-8"
        )
        for step in (
            "continue_independent",
            "stack_local",
            "wait",
            "cancel-in-progress",
            "rebase",
            "incremental",
            "resource contention",
        ):
            self.assertIn(step, content)

    def test_the_template_separates_merge_from_next_work(self) -> None:
        content = (FRAMEWORK_ROOT / "templates" / "ci-throughput-decision.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("MERGE BLOCKER", content)
        self.assertIn("NEXT-WORK BLOCKER", content)
        self.assertIn("POST-MERGE OBSERVATION", content)
        self.assertIn("publication_hold", content)
        # The one confusion the template exists to make impossible.
        self.assertIn("nao pode continuar trabalhando", content)

    def test_the_policy_states_that_full_does_not_imply_waiting(self) -> None:
        content = (FRAMEWORK_ROOT / "kernel" / "ci-throughput-policy.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("publication_hold", content)
        self.assertIn("is never a side effect", content)

    def test_the_adaptive_policy_no_longer_implies_waiting_on_remote_ci(self) -> None:
        content = (
            FRAMEWORK_ROOT / "kernel" / "adaptive-execution-policy.md"
        ).read_text(encoding="utf-8")
        self.assertIn("ci-throughput-policy.md", content)
        self.assertIn("not the next unit of work", content)
        self.assertIn("Remote", content)


if __name__ == "__main__":
    unittest.main()
