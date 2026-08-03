"""Calibration of fast / standard / critical.

Every case here is a classification the framework has to get right. The ones
that matter most are the negatives: a migration, a permission change, a
financial screen or a large diff must *not* reach `critical` on their own,
because that is how a ten-file frontend task ended up running the full kernel.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.contracts import (
    CORE_SELF_REVIEW_CHECKS,
    load_test_policy,
    validate_task_contract,
)
from kernel.runtime.execution_modes import (
    classify_task,
    mode_requirements,
    reclassify_execution_mode,
    resolve_execution_mode,
    route_execution,
)
from kernel.runtime.mode_control import set_execution_mode
from kernel.runtime.state_machine import (
    effective_task_mode,
    phase_requires_seal,
    validate_state,
    validate_transition,
)
from tests.helpers import (
    FRAMEWORK_ROOT,
    initialized_project,
    minimal_task,
    read_state,
    set_lifecycle,
    write_state,
    write_tasks,
)


def _mode(**kwargs) -> str:
    return classify_task(**kwargs)["mode"]


class FastClassificationTests(unittest.TestCase):
    def test_small_localized_correction_is_fast(self) -> None:
        self.assertEqual(
            "fast",
            _mode(
                localized=True,
                files_touched=1,
                estimated_minutes=8,
                blast_radius="local",
            ),
        )

    def test_short_feature_touching_few_files_is_fast(self) -> None:
        self.assertEqual(
            "fast",
            _mode(
                localized=True,
                files_touched=3,
                estimated_minutes=12,
                blast_radius="feature",
            ),
        )

    def test_sensitive_area_alone_does_not_cost_a_task_its_fast_mode(self) -> None:
        self.assertEqual(
            "fast",
            _mode(
                localized=True,
                files_touched=1,
                estimated_minutes=5,
                blast_radius="local",
                sensitive_areas=["authentication_area", "financial_area"],
            ),
        )

    def test_router_reads_short_contained_work_as_fast(self) -> None:
        for request in (
            "Corrija o typo no título da página.",
            "Faça um ajuste visual no espaçamento do card.",
            "Adicione o teste faltante do helper de datas.",
            "Redirect simples de /antigo para /novo.",
        ):
            with self.subTest(request=request):
                self.assertEqual("fast", route_execution(request)["selected_mode"])


class StandardClassificationTests(unittest.TestCase):
    def test_standard_is_the_default_when_nothing_argues_otherwise(self) -> None:
        self.assertEqual("standard", _mode())
        decision = route_execution("Implemente o fluxo de convite de membros.")
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual([], decision["risk_factors"])

    def test_medium_frontend_feature_is_standard(self) -> None:
        self.assertEqual(
            "standard",
            _mode(files_touched=10, estimated_minutes=90, blast_radius="feature"),
        )

    def test_large_but_bounded_backend_feature_is_standard(self) -> None:
        self.assertEqual(
            "standard",
            _mode(
                files_touched=25,
                estimated_minutes=300,
                blast_radius="module",
                sensitive_areas=["authorization_area"],
            ),
        )

    def test_controlled_migration_is_standard(self) -> None:
        self.assertEqual(
            "standard",
            _mode(
                files_touched=8,
                estimated_minutes=120,
                blast_radius="module",
                reversibility="straightforward",
                sensitive_areas=["migration_area"],
            ),
        )
        self.assertEqual(
            "standard",
            route_execution(
                "Crie a migration de onboarding com backfill compatível e rollback "
                "documentado."
            )["selected_mode"],
        )

    def test_u3a_frontend_setup_route_is_standard(self) -> None:
        """Ten allowed files, no backend, no persistence, no migration."""

        self.assertEqual(
            "standard",
            _mode(
                files_touched=10,
                estimated_minutes=180,
                blast_radius="feature",
                reversibility="trivial",
                sensitive_areas=["tenant_area", "authorization_area"],
            ),
        )
        decision = route_execution(
            "Mova a tela de setup empresarial da organização para a rota própria, "
            "derivando o progresso das entidades legais e contas ativas."
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual([], decision["risk_factors"])

    def test_u3b1_membership_persistence_is_standard(self) -> None:
        """Membership persistence plus a compatible migration is ordinary work."""

        self.assertEqual(
            "standard",
            _mode(
                files_touched=12,
                estimated_minutes=240,
                blast_radius="module",
                reversibility="straightforward",
                sensitive_areas=["migration_area", "tenant_area", "authorization_area"],
            ),
        )
        decision = route_execution(
            "Adicione onboarding_completed_at à membership com backfill compatível, "
            "exponha o estado em /api/v1/me e conclua o onboarding de forma "
            "idempotente."
        )
        self.assertEqual("standard", decision["selected_mode"])
        self.assertEqual([], decision["risk_factors"])

    def test_oversized_work_that_can_be_split_stays_standard(self) -> None:
        classification = classify_task(
            coupled_oversized_work=True, splittable=True, blast_radius="module"
        )
        self.assertEqual("standard", classification["mode"])
        self.assertIn("split", classification["reason"])

    def test_size_files_and_hours_never_reach_critical_on_their_own(self) -> None:
        self.assertEqual(
            "standard",
            _mode(files_touched=60, estimated_minutes=900, blast_radius="module"),
        )


class CriticalClassificationTests(unittest.TestCase):
    def test_small_change_in_the_authentication_core_is_critical(self) -> None:
        self.assertEqual(
            "critical",
            _mode(
                localized=True,
                files_touched=1,
                estimated_minutes=10,
                severe_harm_factors=["auth_core_breakage"],
            ),
        )
        self.assertEqual(
            "critical",
            route_execution(
                "Ajuste pequeno no núcleo de autenticação que decide toda sessão."
            )["selected_mode"],
        )

    def test_payment_gateway_is_critical(self) -> None:
        self.assertEqual(
            "critical",
            route_execution("Troque o gateway de pagamento do checkout.")[
                "selected_mode"
            ],
        )

    def test_central_tenant_isolation_is_critical(self) -> None:
        self.assertEqual(
            "critical",
            route_execution(
                "Reescreva o isolamento central entre tenants das queries."
            )["selected_mode"],
        )

    def test_destructive_hard_to_reverse_migration_is_critical(self) -> None:
        self.assertEqual(
            "critical",
            route_execution(
                "Rode uma migration destrutiva que remove coluna com dados."
            )["selected_mode"],
        )
        self.assertEqual(
            "critical",
            _mode(reversibility="irreversible", blast_radius="tenant-wide"),
        )

    def test_oversized_coupled_work_that_cannot_be_split_is_critical(self) -> None:
        self.assertEqual(
            "critical",
            _mode(coupled_oversized_work=True, splittable=False),
        )

    def test_an_unnamed_risk_cannot_become_critical(self) -> None:
        with self.assertRaises(ValueError):
            classify_task(severe_harm_factors=["parece arriscado"])


class ResolutionTests(unittest.TestCase):
    def test_most_specific_declaration_wins_without_taking_the_maximum(self) -> None:
        self.assertEqual(
            {"mode": "standard", "source": "task"},
            resolve_execution_mode(project="critical", phase="critical", task="standard"),
        )
        self.assertEqual(
            {"mode": "fast", "source": "task-override"},
            resolve_execution_mode(project="critical", task="standard", override="fast"),
        )
        self.assertEqual(
            {"mode": "critical", "source": "task"},
            resolve_execution_mode(project="fast", phase="standard", task="critical"),
        )

    def test_phase_and_project_are_defaults_not_floors(self) -> None:
        self.assertEqual(
            "standard",
            resolve_execution_mode(project="critical", phase="standard")["mode"],
        )
        self.assertEqual("standard", resolve_execution_mode()["mode"])


class ReclassificationTests(unittest.TestCase):
    def test_escalating_to_critical_requires_a_named_grave_damage_path(self) -> None:
        refused = reclassify_execution_mode(
            "standard", "critical", justification="parece perigoso demais"
        )
        self.assertFalse(refused["allowed"])
        allowed = reclassify_execution_mode(
            "standard",
            "critical",
            justification="a query nova cruza o filtro de tenant",
            severe_harm_factors=["cross_tenant_exposure"],
        )
        self.assertTrue(allowed["allowed"])
        self.assertEqual("escalation", allowed["direction"])

    def test_reduction_costs_only_a_reason(self) -> None:
        verdict = reclassify_execution_mode(
            "critical",
            "standard",
            justification="frontend delimitado, sem backend nem migration",
        )
        self.assertTrue(verdict["allowed"])
        self.assertEqual("reduction", verdict["direction"])

    def test_a_bare_reduction_still_has_to_say_why(self) -> None:
        self.assertFalse(
            reclassify_execution_mode("critical", "standard", justification="ok")[
                "allowed"
            ]
        )


class RequirementTests(unittest.TestCase):
    def test_ceremony_scales_with_the_mode(self) -> None:
        self.assertEqual(0, mode_requirements("fast")["independent_reviews"])
        self.assertEqual(1, mode_requirements("standard")["independent_reviews"])
        self.assertEqual(2, mode_requirements("critical")["independent_reviews"])
        self.assertFalse(mode_requirements("standard")["plan_seal"])
        self.assertTrue(mode_requirements("critical")["plan_seal"])

    def test_standard_contract_keeps_scope_and_acceptance_without_the_paperwork(
        self,
    ) -> None:
        policy = load_test_policy(FRAMEWORK_ROOT)
        contract = {
            "id": "T1",
            "title": "Add supplier form",
            "status": "pending",
            "change_type": "documentation",
            "goal": {"description": "Add the supplier form."},
            "depends_on": [],
            "allowed_files": ["app/form.tsx"],
            "acceptance": [{"id": "AC-1", "criterion": "Form saves."}],
            "test_policy": {"mode": "test-exempt", "commands": []},
            "rollback": {"strategy": "revert the commit"},
            "review": {"self_review": "required", "spec_compliance": "required"},
            "completion": {"requires": ["reviewed-diff"]},
        }
        self.assertEqual([], validate_task_contract(contract, policy, mode="standard"))
        # The same contract under critical still owes the full paperwork.
        self.assertTrue(validate_task_contract(contract, policy, mode="critical"))

    def test_a_contract_without_scope_is_refused_in_every_mode(self) -> None:
        policy = load_test_policy(FRAMEWORK_ROOT)
        contract = {
            "id": "T1",
            "title": "Add supplier form",
            "status": "pending",
            "change_type": "documentation",
            "goal": {"description": "Add the supplier form."},
            "allowed_files": [],
            "acceptance": [{"id": "AC-1", "criterion": "Form saves."}],
            "test_policy": {"mode": "test-exempt", "commands": []},
            "completion": {"requires": []},
        }
        for mode in ("fast", "standard", "critical"):
            with self.subTest(mode=mode):
                codes = {
                    issue["code"]
                    for issue in validate_task_contract(contract, policy, mode=mode)
                }
                self.assertIn("scope-empty", codes)

    def test_fast_keeps_the_self_review_checks_that_catch_real_mistakes(self) -> None:
        self.assertEqual(
            {"complete_diff", "scope", "acceptance", "tests", "secrets"},
            CORE_SELF_REVIEW_CHECKS,
        )


class PhaseGranularityTests(unittest.TestCase):
    def test_a_phase_holds_tasks_of_different_modes(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [
                    dict(minimal_task("P1-T01"), execution_mode="fast"),
                    dict(minimal_task("P1-T02"), execution_mode="standard"),
                    dict(minimal_task("P1-T03"), execution_mode="critical"),
                ],
            )
            state, _ = read_state(root)
            self.assertEqual(
                ["fast", "standard", "critical"],
                [
                    effective_task_mode(state, root, task_id=identifier)
                    for identifier in ("P1-T01", "P1-T02", "P1-T03")
                ],
            )

    def test_a_critical_task_does_not_raise_its_neighbours(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [
                    dict(minimal_task("P1-T01"), execution_mode="standard"),
                    dict(minimal_task("P1-T02"), execution_mode="critical"),
                ],
            )
            state, _ = read_state(root)
            self.assertEqual(
                "standard", effective_task_mode(state, root, task_id="P1-T01")
            )
            # The phase still owes a seal, because one of its tasks is critical.
            self.assertTrue(phase_requires_seal(state, root))

    def test_phase_default_applies_where_a_task_says_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [
                    minimal_task("P1-T01"),
                    dict(minimal_task("P1-T02"), execution_mode="critical"),
                ],
                default_mode="standard",
            )
            state, _ = read_state(root)
            self.assertEqual(
                "standard", effective_task_mode(state, root, task_id="P1-T01")
            )
            self.assertEqual(
                "critical", effective_task_mode(state, root, task_id="P1-T02")
            )

    def test_a_phase_of_ordinary_tasks_owes_no_plan_seal(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [dict(minimal_task("P1-T01", status="pending"), execution_mode="standard")],
                default_mode="standard",
            )
            state, _ = read_state(root)
            self.assertFalse(phase_requires_seal(state, root))
            set_lifecycle(state, "planned")
            write_frontmatter(root / ".agent" / "STATE.md", state, "# State\n")
            codes = {issue["code"] for issue in validate_state(state, root)}
            self.assertNotIn("plan-fingerprint", codes)
            self.assertNotIn("plan-revision", codes)

    def test_a_phase_with_a_critical_task_still_owes_its_seal(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialized_project(root, with_phase=True)
            write_tasks(
                root,
                [dict(minimal_task("P1-T01"), execution_mode="critical")],
            )
            state, _ = read_state(root)
            set_lifecycle(state, "planned")
            write_frontmatter(root / ".agent" / "STATE.md", state, "# State\n")
            codes = {issue["code"] for issue in validate_state(state, root)}
            self.assertIn("plan-fingerprint", codes)


class ProportionalReviewTests(unittest.TestCase):
    def _reviewing_project(self, root: Path, mode: str) -> dict:
        initialized_project(root, with_phase=True)
        write_tasks(
            root,
            [dict(minimal_task("P1-T01", status="reviewing"), execution_mode=mode)],
        )
        state, _ = read_state(root)
        set_lifecycle(state, "reviewing")
        state["current_task"] = {"id": "P1-T01", "status": "reviewing"}
        state["gates"]["self_review"] = "passed"
        state["gates"]["spec_compliance"] = "passed"
        state["gates"]["code_quality"] = "not_required"
        write_state(root, state)
        return read_state(root)[0]

    def test_one_review_carries_a_standard_task_to_verification(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._reviewing_project(root, "standard")
            codes = {
                issue["code"] for issue in validate_transition(state, "verifying", root)
            }
            self.assertNotIn("quality-review", codes)
            self.assertNotIn("independent-review", codes)

    def test_critical_still_needs_both_independent_reviews(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._reviewing_project(root, "critical")
            codes = {
                issue["code"] for issue in validate_transition(state, "verifying", root)
            }
            self.assertIn("quality-review", codes)

    def test_standard_still_needs_one_review(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._reviewing_project(root, "standard")
            state["gates"]["spec_compliance"] = "pending"
            state["gates"]["code_quality"] = "pending"
            codes = {
                issue["code"] for issue in validate_transition(state, "verifying", root)
            }
            self.assertIn("independent-review", codes)

    def test_a_blocking_review_stops_a_standard_task_too(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = self._reviewing_project(root, "standard")
            state["gates"]["spec_compliance"] = "blocked"
            codes = {
                issue["code"] for issue in validate_transition(state, "verifying", root)
            }
            self.assertIn("spec-review", codes)


class SetExecutionModeTests(unittest.TestCase):
    def _project_with_task(self, root: Path, status: str = "pending") -> None:
        initialized_project(root, with_phase=True)
        write_tasks(root, [minimal_task("P1-T01", status=status)])

    def test_reducing_an_over_classification_records_the_reason(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project_with_task(root)
            tasks_before = (root / ".agent/phases/01-kernel/TASKS.md").read_bytes()
            state, issues, changed = set_execution_mode(
                root,
                scope="task",
                mode="standard",
                reason="frontend delimitado, sem backend, sem migration",
                actor="tests",
                task_id="P1-T01",
            )
            self.assertEqual([], issues)
            self.assertTrue(changed)
            record = state["task_modes"]["P1-T01"]
            self.assertEqual("standard", record["mode"])
            self.assertEqual("critical", record["previous"])
            self.assertEqual("reduction", record["direction"])
            self.assertEqual(
                "standard", effective_task_mode(state, root, task_id="P1-T01")
            )
            # The sealed contract is never rewritten to correct a label.
            self.assertEqual(
                tasks_before, (root / ".agent/phases/01-kernel/TASKS.md").read_bytes()
            )

    def test_escalation_without_a_named_harm_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project_with_task(root)
            set_execution_mode(
                root,
                scope="task",
                mode="standard",
                reason="frontend delimitado, sem backend",
                actor="tests",
                task_id="P1-T01",
            )
            _, issues, changed = set_execution_mode(
                root,
                scope="task",
                mode="critical",
                reason="achei que era arriscado",
                actor="tests",
                task_id="P1-T01",
            )
            self.assertFalse(changed)
            self.assertTrue(issues)

    def test_escalation_with_a_named_harm_is_allowed_and_keeps_history(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project_with_task(root)
            set_execution_mode(
                root,
                scope="task",
                mode="standard",
                reason="frontend delimitado, sem backend",
                actor="tests",
                task_id="P1-T01",
            )
            state, issues, changed = set_execution_mode(
                root,
                scope="task",
                mode="critical",
                reason="a consulta nova atravessa o filtro de tenant",
                actor="tests",
                task_id="P1-T01",
                severe_harm_factors=["cross_tenant_exposure"],
            )
            self.assertEqual([], issues)
            self.assertTrue(changed)
            record = state["task_modes"]["P1-T01"]
            self.assertEqual("critical", record["mode"])
            self.assertEqual(["cross_tenant_exposure"], record["severe_harm_factors"])
            self.assertEqual(1, len(record["history"]))
            self.assertEqual("standard", record["history"][0]["mode"])

    def test_reclassifying_an_unknown_task_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project_with_task(root)
            _, issues, changed = set_execution_mode(
                root,
                scope="task",
                mode="standard",
                reason="tarefa que não existe neste índice",
                actor="tests",
                task_id="P9-T99",
            )
            self.assertFalse(changed)
            self.assertTrue(issues)

    def test_project_default_can_be_lowered_without_losing_the_kernel(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project_with_task(root)
            state, issues, changed = set_execution_mode(
                root,
                scope="project",
                mode="standard",
                reason="desenvolvimento normal; critical fica para dano grave",
                actor="tests",
            )
            self.assertEqual([], issues)
            self.assertTrue(changed)
            self.assertEqual("standard", state["execution_mode"])
            self.assertTrue((root / ".agent" / "phases").is_dir())
            self.assertEqual([], validate_state(state, root))
            self.assertEqual(
                "standard", effective_task_mode(state, root, task_id="P1-T01")
            )

    def test_the_ledger_records_the_reclassification(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project_with_task(root)
            set_execution_mode(
                root,
                scope="task",
                mode="standard",
                reason="frontend delimitado, sem backend, sem migration",
                actor="tests",
                task_id="P1-T01",
            )
            ledger = (root / ".agent/phases/01-kernel/EVIDENCE.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("classification", ledger)
            self.assertIn("critical -> standard", ledger)


class PersistentStandardProjectTests(unittest.TestCase):
    def test_the_full_kernel_is_reachable_without_declaring_everything_critical(
        self,
    ) -> None:
        from kernel.runtime.next_operation import determine_next_operation
        from kernel.runtime.project import initialize_phase, initialize_project

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            initialize_project(
                root,
                FRAMEWORK_ROOT,
                project_name="persistent-standard",
                mode="standard",
                persistent=True,
            )
            state, _ = load_frontmatter(root / ".agent" / "STATE.md")
            self.assertEqual("standard", state["execution_mode"])
            self.assertEqual([], validate_state(state, root))
            initialize_phase(
                root,
                FRAMEWORK_ROOT,
                phase_id="P1",
                phase_name="Onboarding",
                slug="01-onboarding",
                actor="tests",
            )
            decision = determine_next_operation(root)
            self.assertEqual("standard", decision["execution_mode"])
            self.assertEqual(
                "continue-discussion", decision["next_operation"]["operation"]
            )


if __name__ == "__main__":
    unittest.main()
