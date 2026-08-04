"""The lifecycle gap that stranded a finished phase.

A phase can be integrated, verified and green in CI and still have nowhere to
go: ``ready_to_ship -> shipped`` demands a release gate that nothing could pass,
and the next phase — contracted months earlier, sitting complete on disk — could
not be reached by ``init-phase`` (the directory exists), ``seal-plan`` (it only
seals the active phase) or ``reconcile-phase`` (its tasks are all pending).

These tests reproduce that shape end to end and pin the guards that must not
soften while closing it.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.contracts import load_task_index
from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.gates import set_gate_status
from kernel.runtime.project import initialize_phase
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.rotation import activate_phase
from kernel.runtime.state_machine import (
    transition_state,
    validate_state,
    validate_transition,
)
from tests.helpers import (
    initialized_project,
    minimal_task,
    read_state,
    write_state,
)


CLOSED_SLUG = "01-kernel"
NEXT_SLUG = "02-next"


def _write_tasks(root: Path, slug: str, phase_id: str, tasks) -> Path:
    path = root / ".agent" / "phases" / slug / "TASKS.md"
    write_frontmatter(
        path,
        {
            "schema_version": 1,
            "phase": {"id": phase_id, "name": "Phase {}".format(phase_id)},
            "tasks": tasks,
        },
        "# Tasks\n",
    )
    return path


def _record_decision(root: Path, decision_id: str) -> None:
    decisions = root / ".agent" / "DECISIONS.md"
    text = decisions.read_text(encoding="utf-8")
    if "## {} ".format(decision_id) not in text:
        decisions.write_text(
            text
            + "\n## {} — Recorded for the test\n\n- Status: accepted\n".format(
                decision_id
            ),
            encoding="utf-8",
        )


def _stranded_project(root: Path, *, next_tasks=None) -> None:
    """A closed phase in ready_to_ship and a planned phase waiting on disk.

    Mirrors the shape that produced the gap: five verified tasks, one cancelled
    by supersession, a pending release gate, and a next phase whose contracts
    exist and whose tasks have never been touched.
    """

    initialized_project(root, with_phase=True)

    # The next phase is contracted while the state is still fresh, which is the
    # only moment init-phase accepts. This is how it lands on disk in real
    # projects, and why it later cannot be reached.
    initialize_phase(
        root,
        Path(__file__).resolve().parents[1],
        phase_id="P2",
        phase_name="Next",
        slug=NEXT_SLUG,
        actor="tests",
    )
    _write_tasks(
        root,
        NEXT_SLUG,
        "P2",
        next_tasks
        if next_tasks is not None
        else [
            minimal_task("P2-T01"),
            minimal_task("P2-T02", depends_on=["P2-T01"]),
            minimal_task("P2-T03"),
            minimal_task("P2-T04"),
        ],
    )

    _write_tasks(
        root,
        CLOSED_SLUG,
        "P1",
        [
            minimal_task("P1-T01", status="verified"),
            minimal_task("P1-T02", status="verified"),
            minimal_task("P1-T03", status="verified"),
            minimal_task("P1-T04", status="verified"),
            minimal_task("P1-T05", status="verified"),
            minimal_task("P1-T06", status="cancelled"),
        ],
    )

    state, _ = read_state(root)
    closed = ".agent/phases/{}".format(CLOSED_SLUG)
    state["artifacts"].update(
        {
            "spec": closed + "/SPEC.md",
            "plan": closed + "/PLAN.md",
            "tasks": closed + "/TASKS.md",
            "evidence": closed + "/EVIDENCE.md",
            "review": closed + "/REVIEW.md",
            "handoff": closed + "/HANDOFF.md",
        }
    )
    state["phase"] = {"id": "P1", "name": "Kernel", "status": "ready_to_ship"}
    state["status"] = "ready_to_ship"
    state["risk"] = {"level": "medium", "reasons": ["lifecycle regression fixture"]}
    state["current_task"] = {"id": "P1-T05", "status": "verified"}
    state["next_action"] = {"operation": "ship", "target": "P1"}
    state["gates"].update(
        {
            "specification": "passed",
            "plan_quality": "passed",
            "self_review": "passed",
            "spec_compliance": "passed",
            "code_quality": "passed",
            "acceptance": "passed",
            "verification": "passed",
            "release": "pending",
        }
    )
    write_state(root, state)

    roadmap = root / ".agent" / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8") + "\n| P1 | closed |\n| P2 | planned |\n",
        encoding="utf-8",
    )
    _record_decision(root, "DEC-RELEASE")


def _pass_release(root: Path, **overrides):
    arguments = {
        "gate": "release",
        "target": "passed",
        "decision_id": "DEC-RELEASE",
        "evidence": ".agent/phases/{}/EVIDENCE.md#release".format(CLOSED_SLUG),
        "actor": "releaser",
    }
    arguments.update(overrides)
    return set_gate_status(root, **arguments)


class ReleaseGateTests(unittest.TestCase):
    def test_shipping_is_refused_until_the_release_gate_is_paid(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)
            state, _ = read_state(root)

            issues = validate_transition(state, "shipped", root)

            self.assertTrue(
                any(item["code"] == "release-gate" for item in issues),
                issues,
            )

    def test_gate_passes_against_a_decision_and_evidence_then_ships(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            state, issues, changed = _pass_release(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(state["gates"]["release"], "passed")
            self.assertEqual(validate_state(state, root), [])
            self.assertEqual(validate_transition(state, "shipped", root), [])

            shipped = transition_state(
                state, "shipped", root, actor="releaser", reason="integrated"
            )
            self.assertEqual(shipped["status"], "shipped")

    def test_passing_the_gate_does_not_ship_by_itself(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            state, _, _ = _pass_release(root)

            self.assertEqual(state["status"], "ready_to_ship")
            self.assertEqual(state["next_action"]["operation"], "ship")

    def test_the_change_is_appended_to_the_existing_ledger(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)
            ledger = root / ".agent" / "phases" / CLOSED_SLUG / "EVIDENCE.md"
            before = ledger.read_text(encoding="utf-8")

            _pass_release(root)

            after = ledger.read_text(encoding="utf-8")
            self.assertIn(before, after)
            self.assertIn("gate", after)
            self.assertIn("DEC-RELEASE", after)

    def test_repeating_the_same_change_is_idempotent(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)
            _pass_release(root)
            ledger = root / ".agent" / "phases" / CLOSED_SLUG / "EVIDENCE.md"
            after_first = ledger.read_text(encoding="utf-8")

            state, issues, changed = _pass_release(root)

            self.assertEqual(issues, [])
            self.assertFalse(changed)
            self.assertEqual(state["gates"]["release"], "passed")
            self.assertEqual(ledger.read_text(encoding="utf-8"), after_first)

    def test_repeating_with_a_different_justification_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)
            _pass_release(root)
            _record_decision(root, "DEC-OTHER")

            _, issues, changed = _pass_release(root, decision_id="DEC-OTHER")

            self.assertFalse(changed)
            self.assertTrue(
                any("refusing to rewrite" in message for message in issues), issues
            )

    def test_passing_without_evidence_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(root, evidence=None)

            self.assertFalse(changed)
            self.assertTrue(
                any("evidence reference" in message for message in issues), issues
            )

    def test_passing_without_a_decision_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(root, decision_id=None)

            self.assertFalse(changed)
            self.assertTrue(any("requires a decision" in m for m in issues), issues)

    def test_a_decision_that_is_not_recorded_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(root, decision_id="DEC-GHOST")

            self.assertFalse(changed)
            self.assertTrue(
                any("not recorded in DECISIONS.md" in m for m in issues), issues
            )

    def test_evidence_pointing_at_a_missing_file_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(
                root, evidence=".agent/phases/{}/GONE.md#x".format(CLOSED_SLUG)
            )

            self.assertFalse(changed)
            self.assertTrue(any("evidence file is missing" in m for m in issues), issues)

    def test_evidence_from_another_phase_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(
                root, evidence=".agent/phases/{}/EVIDENCE.md#x".format(NEXT_SLUG)
            )

            self.assertFalse(changed)
            self.assertTrue(any("belongs to phase" in m for m in issues), issues)

    def test_an_unknown_gate_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(root, gate="deployment")

            self.assertFalse(changed)
            self.assertTrue(any("unknown gate" in m for m in issues), issues)

    def test_an_invalid_gate_state_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(root, target="green")

            self.assertFalse(changed)
            self.assertTrue(any("invalid gate state" in m for m in issues), issues)

    def test_review_owned_gates_are_refused_with_their_operation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)

            _, issues, changed = _pass_release(root, gate="spec_compliance")

            self.assertFalse(changed)
            self.assertTrue(
                any("validate-spec-review" in m for m in issues), issues
            )

    def test_pending_cannot_be_used_to_un_record_a_gate(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)
            _pass_release(root)

            _, issues, changed = _pass_release(root, target="pending")

            self.assertFalse(changed)
            self.assertTrue(any("invalid gate state" in m for m in issues), issues)

    def test_a_refused_change_writes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)
            state_file = root / ".agent" / "STATE.md"
            ledger = root / ".agent" / "phases" / CLOSED_SLUG / "EVIDENCE.md"
            before_state = state_file.read_text(encoding="utf-8")
            before_ledger = ledger.read_text(encoding="utf-8")

            _pass_release(root, decision_id="DEC-GHOST")

            self.assertEqual(state_file.read_text(encoding="utf-8"), before_state)
            self.assertEqual(ledger.read_text(encoding="utf-8"), before_ledger)


class PhaseActivationTests(unittest.TestCase):
    def _shipped(self, root: Path) -> None:
        _stranded_project(root)
        state, _, _ = _pass_release(root)
        shipped = transition_state(
            state, "shipped", root, actor="releaser", reason="integrated"
        )
        write_frontmatter(root / ".agent" / "STATE.md", shipped, "# State\n")

    def _activate(self, root: Path, **overrides):
        arguments = {
            "phase_id": "P2",
            "phase_name": "Next",
            "slug": NEXT_SLUG,
            "actor": "planner",
        }
        arguments.update(overrides)
        return activate_phase(root, **arguments)

    def test_activation_lands_on_specified_when_the_plan_is_not_sealed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            state, issues = self._activate(root)

            self.assertEqual(issues, [])
            self.assertEqual(state["status"], "specified")
            self.assertEqual(state["phase"]["id"], "P2")
            self.assertIsNone(state["plan_revision"]["fingerprint"])
            self.assertEqual(validate_state(state, root), [])

    def test_the_next_operation_is_the_plan_gate_not_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            self._activate(root)

            decision = determine_next_operation(root)
            self.assertEqual(decision["next_operation"]["operation"], "build-plan")
            self.assertEqual(decision["inconsistencies"], [])

    def test_sealing_then_planning_reaches_the_first_eligible_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            self._activate(root)
            _record_decision(root, "DEC-PLAN")

            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            from kernel.runtime.state_machine import compute_plan_fingerprint

            state["plan_revision"] = {
                "version": 1,
                "decision_id": "DEC-PLAN",
                "fingerprint": compute_plan_fingerprint(state, root),
                "evidence": ".agent/phases/{}/EVIDENCE.md#plan".format(NEXT_SLUG),
            }
            self.assertEqual(validate_transition(state, "planned", root), [])
            planned = transition_state(
                state, "planned", root, actor="planner", reason="plan sealed"
            )
            write_frontmatter(root / ".agent" / "STATE.md", planned, body)

            decision = determine_next_operation(root)
            self.assertEqual(decision["next_operation"]["operation"], "execute-task")
            self.assertEqual(decision["next_operation"]["target"], "P2-T01")

    def test_activation_lands_on_planned_when_the_plan_is_genuinely_sealed(self) -> None:
        """Rotating back to a phase whose stored seal still describes it."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            _record_decision(root, "DEC-PLAN")

            # Seal the stored revision against the phase about to be activated,
            # which is what makes the fingerprint match on arrival.
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            target = dict(state)
            target["artifacts"] = dict(state["artifacts"])
            target["artifacts"].update(
                {
                    "plan": ".agent/phases/{}/PLAN.md".format(NEXT_SLUG),
                    "tasks": ".agent/phases/{}/TASKS.md".format(NEXT_SLUG),
                }
            )
            from kernel.runtime.state_machine import compute_plan_fingerprint

            state["plan_revision"] = {
                "version": 3,
                "decision_id": "DEC-PLAN",
                "fingerprint": compute_plan_fingerprint(target, root),
                "evidence": ".agent/phases/{}/EVIDENCE.md#plan".format(NEXT_SLUG),
            }
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            activated, issues = self._activate(root)

            self.assertEqual(issues, [])
            self.assertEqual(activated["status"], "planned")
            self.assertEqual(activated["plan_revision"]["version"], 3)
            self.assertEqual(validate_state(activated, root), [])

            decision = determine_next_operation(root)
            self.assertEqual(decision["next_operation"]["operation"], "execute-task")
            self.assertEqual(decision["next_operation"]["target"], "P2-T01")
            self.assertEqual(decision["inconsistencies"], [])

    def test_the_closed_phase_keeps_every_document_and_is_recorded(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            closed_dir = root / ".agent" / "phases" / CLOSED_SLUG
            before = {
                path.name: path.read_text(encoding="utf-8")
                for path in sorted(closed_dir.iterdir())
                if path.is_file()
            }

            state, _ = self._activate(root)

            after = {
                path.name: path.read_text(encoding="utf-8")
                for path in sorted(closed_dir.iterdir())
                if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertTrue(
                any(
                    entry.get("id") == "P1" for entry in state.get("completed_phases", [])
                ),
                state.get("completed_phases"),
            )

    def test_the_activated_phase_does_not_inherit_the_release_gate(self) -> None:
        """The reported shape: P1 ships, P2 is activated already shipped.

        ``release`` guards ``ready_to_ship -> shipped``, and the rotation was
        carrying it over intact — so the activated phase started with the gate
        paid, on a record whose evidence pointed inside the *closed* phase's
        directory. It is the one gate whose inheritance is not merely untidy:
        ``GATE_TRANSITIONS`` has no edge from ``passed`` to ``passed``, so the
        activated phase could not have recorded its own verdict even if someone
        had noticed.
        """

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            before, _ = read_state(root)
            self.assertEqual(before["gates"]["release"], "passed")
            self.assertEqual(
                before["gate_records"]["release"]["evidence"],
                ".agent/phases/{}/EVIDENCE.md#release".format(CLOSED_SLUG),
            )

            state, issues = self._activate(root)

            self.assertEqual(issues, [])
            self.assertEqual(state["gates"]["release"], "pending")
            self.assertEqual(validate_state(state, root), [])

            # A coherent record, not an absent one: it describes the phase now
            # active, and carries nothing the closed phase paid for.
            record = state["gate_records"]["release"]
            self.assertEqual(record["status"], "pending")
            self.assertIsNone(record["decision"])
            self.assertIsNone(record["evidence"])
            self.assertEqual(record["by"], "planner")
            self.assertEqual(record["plan_revision"], state["plan_revision"]["version"])

    def test_the_closed_phase_release_verdict_is_kept_as_history(self) -> None:
        """Reopening is not erasing. What P1 paid for stays readable, as P1's."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            state, issues = self._activate(root)

            self.assertEqual(issues, [])
            history = state["gate_records"]["release"]["history"]
            self.assertEqual(1, len(history))
            self.assertEqual(history[0]["status"], "passed")
            self.assertEqual(history[0]["decision"], "DEC-RELEASE")
            self.assertEqual(
                history[0]["evidence"],
                ".agent/phases/{}/EVIDENCE.md#release".format(CLOSED_SLUG),
            )
            # Stamped with the phase it judged, so the two verdicts on this gate
            # can never be read as one.
            self.assertEqual(history[0]["phase"], "P1")

    def test_the_activated_phase_can_record_its_own_release(self) -> None:
        """The dead end the inherited ``passed`` created, at its own door."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            self._activate(root)

            state, issues, changed = _pass_release(
                root,
                evidence=".agent/phases/{}/EVIDENCE.md#release".format(NEXT_SLUG),
                actor="releaser",
            )

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(state["gates"]["release"], "passed")
            self.assertEqual(
                state["gate_records"]["release"]["evidence"],
                ".agent/phases/{}/EVIDENCE.md#release".format(NEXT_SLUG),
            )
            # And the closed phase's verdict is still underneath it, alongside
            # the pending record this passage replaced.
            history = state["gate_records"]["release"]["history"]
            self.assertEqual(
                [entry.get("phase") for entry in history], ["P1", None]
            )
            self.assertEqual(
                [entry["status"] for entry in history], ["passed", "pending"]
            )

    def test_the_work_gates_of_the_activated_phase_start_pending(self) -> None:
        """``release`` was the sharp end, not the only one.

        The five review gates judge a contract and a diff. Inherited across a
        rotation they approve a diff that does not exist yet.
        """

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            state, issues = self._activate(root)

            self.assertEqual(issues, [])
            self.assertEqual(
                {
                    gate: state["gates"][gate]
                    for gate in (
                        "self_review",
                        "spec_compliance",
                        "code_quality",
                        "acceptance",
                        "verification",
                    )
                },
                {
                    "self_review": "pending",
                    "spec_compliance": "pending",
                    "code_quality": "pending",
                    "acceptance": "pending",
                    "verification": "pending",
                },
            )

    def test_activation_records_the_closed_phase_in_completed_phases(self) -> None:
        """Rotation is what advances the register; nobody edits it by hand."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            before, _ = read_state(root)
            self.assertEqual(before.get("completed_phases", []), [])

            state, issues = self._activate(root)

            self.assertEqual(issues, [])
            self.assertEqual(1, len(state["completed_phases"]))
            entry = state["completed_phases"][0]
            self.assertEqual(entry["id"], "P1")
            self.assertEqual(entry["status"], "shipped")
            self.assertEqual(
                entry["artifacts"], ".agent/phases/{}/TASKS.md".format(CLOSED_SLUG)
            )
            self.assertTrue(entry["closed_at"])

    def test_no_task_of_the_activated_phase_is_marked_executed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            self._activate(root)

            index, _ = load_task_index(
                root / ".agent" / "phases" / NEXT_SLUG / "TASKS.md"
            )
            self.assertEqual(
                {task["status"] for task in index["tasks"]}, {"pending"}
            )

    def test_activation_before_the_phase_is_closed_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _stranded_project(root)  # ready_to_ship, never shipped

            _, issues = self._activate(root)

            self.assertTrue(
                any("requires a closed phase" in m for m in issues), issues
            )

    def test_activating_the_current_phase_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            _, issues = self._activate(root, phase_id="P1", slug=CLOSED_SLUG)

            self.assertTrue(
                any("already the active phase" in m for m in issues), issues
            )

    def test_activating_a_phase_that_does_not_exist_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)

            _, issues = self._activate(root, phase_id="P9", slug="09-ghost")

            self.assertTrue(
                any("does not exist" in m for m in issues), issues
            )

    def test_activating_a_phase_with_started_work_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            _write_tasks(
                root,
                NEXT_SLUG,
                "P2",
                [minimal_task("P2-T01", status="executing"), minimal_task("P2-T02")],
            )

            _, issues = self._activate(root)

            self.assertTrue(
                any("must not have executed work" in m for m in issues), issues
            )

    def test_activating_a_phase_with_a_malformed_task_is_refused(self) -> None:
        """Structural validity is activation's business; plan quality is seal-plan's."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            broken = minimal_task("P2-T01")
            del broken["title"]
            _write_tasks(root, NEXT_SLUG, "P2", [broken])

            state, issues = self._activate(root)

            self.assertTrue(issues)
            self.assertEqual(state["phase"]["id"], "P1")

    def test_activating_a_phase_with_a_dangling_dependency_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            _write_tasks(
                root,
                NEXT_SLUG,
                "P2",
                [minimal_task("P2-T01", depends_on=["P2-T99"])],
            )

            state, issues = self._activate(root)

            self.assertTrue(issues)
            self.assertEqual(state["phase"]["id"], "P1")

    def test_activating_a_phase_missing_from_the_roadmap_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            roadmap = root / ".agent" / "ROADMAP.md"
            roadmap.write_text(
                roadmap.read_text(encoding="utf-8").replace("| P2 | planned |", ""),
                encoding="utf-8",
            )

            _, issues = self._activate(root)

            self.assertTrue(
                any("not recorded in" in m for m in issues), issues
            )

    def test_activating_with_an_open_blocker_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["blockers"] = [{"id": "B-01", "status": "open", "summary": "x"}]
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues = self._activate(root)

            self.assertTrue(any("blockers" in m for m in issues), issues)

    def test_a_refused_activation_writes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._shipped(root)
            state_file = root / ".agent" / "STATE.md"
            before = state_file.read_text(encoding="utf-8")

            self._activate(root, phase_id="P9", slug="09-ghost")

            self.assertEqual(state_file.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
