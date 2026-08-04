"""The body of ``STATE.md`` must never describe a phase the frontmatter has left.

The frontmatter moved on every formal write and the prose underneath it did not,
so a project that had shipped U2 and activated U3 opened to a file whose first
readable words still said "active phase: U2", with U2's branch and U2's task
list. The frontmatter was right and the part written for humans was wrong.

These tests pin the shape of the fix: the body is a projection of the
frontmatter, every formal state write regenerates it, nothing reads it back, and
prose that is genuinely not a mirror survives when it is fenced for keeping.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.documents import load_frontmatter, write_frontmatter, write_state
from kernel.runtime.gates import set_gate_status
from kernel.runtime.project import initialize_phase
from kernel.runtime.rotation import activate_phase
from kernel.runtime.state_body import (
    PRESERVE_CLOSE,
    PRESERVE_OPEN,
    extract_preserved,
    project_state_body,
    render_state_body,
)
from kernel.runtime.state_machine import (
    compute_plan_fingerprint,
    transition_state,
    validate_state,
)
from tests.helpers import initialized_project, minimal_task, read_state


FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]

U2_SLUG = "02-business-configuration"
U3_SLUG = "03-membership-onboarding"


def _write_tasks(root: Path, slug: str, phase_id: str, tasks) -> None:
    write_frontmatter(
        root / ".agent" / "phases" / slug / "TASKS.md",
        {
            "schema_version": 1,
            "phase": {"id": phase_id, "name": "Phase {}".format(phase_id)},
            "tasks": tasks,
        },
        "# Tasks\n",
    )


def _record_decision(root: Path, decision_id: str) -> None:
    decisions = root / ".agent" / "DECISIONS.md"
    text = decisions.read_text(encoding="utf-8")
    if "## {} ".format(decision_id) not in text:
        decisions.write_text(
            text + "\n## {} — Recorded for the test\n\n- Status: accepted\n".format(decision_id),
            encoding="utf-8",
        )


def _seal(root: Path, decision_id: str) -> None:
    """Pay the plan gate for the phase now active, through a formal write."""

    _record_decision(root, decision_id)
    state, body = load_frontmatter(root / ".agent" / "STATE.md")
    state["plan_revision"] = {
        "version": 1,
        "decision_id": decision_id,
        "fingerprint": compute_plan_fingerprint(state, root),
        "evidence": state["artifacts"]["evidence"] + "#plan-gate",
    }
    write_state(root / ".agent" / "STATE.md", state, body)


def _shipped_u2_with_u3_on_disk(root: Path) -> None:
    """U2 finished and closed; U3 contracted, complete on disk, never started.

    The exact shape the defect was found in: the rotation is legal, and the
    body it leaves behind is the thing under test.
    """

    initialized_project(root)
    initialize_phase(
        root, FRAMEWORK_ROOT, phase_id="U2", phase_name="Business configuration",
        slug=U2_SLUG, actor="tests",
    )
    initialize_phase(
        root, FRAMEWORK_ROOT, phase_id="U3", phase_name="Membership onboarding",
        slug=U3_SLUG, actor="tests",
    )
    _write_tasks(root, U2_SLUG, "U2", [minimal_task("U2A", status="verified")])
    _write_tasks(root, U3_SLUG, "U3", [minimal_task("U3A"), minimal_task("U3B", depends_on=["U3A"])])

    state, body = read_state(root)
    closed = ".agent/phases/{}".format(U2_SLUG)
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
    state["phase"] = {"id": "U2", "name": "Business configuration", "status": "shipped"}
    state["status"] = "shipped"
    state["current_task"] = {"id": "U2A", "status": "verified"}
    state["next_action"] = {"operation": "none", "target": None}
    state["risk"] = {"level": "medium", "reasons": ["projection regression fixture"]}
    for gate in state["gates"]:
        if gate != "waivers":
            state["gates"][gate] = "passed"

    # A shipped phase has a sealed plan; without one the fixture would not
    # validate, and the test would be measuring the fixture rather than the fix.
    _record_decision(root, "DEC-U2")
    state["plan_revision"] = {
        "version": 1,
        "decision_id": "DEC-U2",
        "fingerprint": compute_plan_fingerprint(state, root),
        "evidence": state["artifacts"]["evidence"] + "#plan-gate",
    }

    # Written the way the defect was born: the frontmatter says U2, and the
    # body is hand-written prose that will go stale the moment the phase turns
    # over. write_frontmatter, deliberately, not write_state.
    write_frontmatter(
        root / ".agent" / "STATE.md",
        state,
        "# STATE\n\n## Identification\n\n| Field | Value |\n| --- | --- |\n"
        "| Active phase | U2 — business configuration |\n"
        "| Branch | chore/close-u2-business-configuration |\n\n"
        "## Units of U2\n\nU2A is verified. U3 is not the active phase.\n",
    )

    roadmap = root / ".agent" / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8") + "\n| U2 | shipped |\n| U3 | planned |\n",
        encoding="utf-8",
    )


class TheBodyFollowsTheFrontmatter(unittest.TestCase):
    def test_the_rotation_from_u2_to_u3_renames_both_halves(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _shipped_u2_with_u3_on_disk(root)

            stale, stale_body = read_state(root)
            self.assertEqual("U2", stale["phase"]["id"])
            self.assertIn("U2 — business configuration", stale_body)

            state, issues = activate_phase(
                root,
                phase_id="U3",
                phase_name="Membership onboarding",
                slug=U3_SLUG,
                actor="tests",
            )
            self.assertEqual([], issues)

            frontmatter, body = read_state(root)
            self.assertEqual("U3", frontmatter["phase"]["id"])

            # The half that a person reads first names the same phase.
            self.assertIn("U3", body)
            self.assertIn("Membership onboarding", body)

            # And no longer names the one that closed as if it were current.
            self.assertNotIn("U2 — business configuration", body)
            self.assertNotIn("chore/close-u2-business-configuration", body)
            self.assertNotIn("U3 is not the active phase", body)

            self.assertEqual([], validate_state(frontmatter, root))

    def test_a_later_transition_keeps_the_two_coherent(self) -> None:
        """One rotation is not enough: every formal write has to regenerate."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _shipped_u2_with_u3_on_disk(root)
            activate_phase(
                root, phase_id="U3", phase_name="Membership onboarding",
                slug=U3_SLUG, actor="tests",
            )

            frontmatter, _ = read_state(root)
            self.assertEqual("specified", frontmatter["status"])

            _seal(root, "DEC-U3")
            frontmatter, body = read_state(root)
            self.assertIn("| Sealed | yes |", body)

            # specified -> planned, the way the CLI applies it: the guard runs,
            # then one formal write.
            updated = transition_state(
                frontmatter, "planned", root, actor="tests", reason="plan approved"
            )
            write_state(root / ".agent" / "STATE.md", updated, body)

            frontmatter, body = read_state(root)
            self.assertEqual("planned", frontmatter["status"])
            self.assertIn("| Status | `planned` |", body)
            self.assertNotIn("| Status | `specified` |", body)
            self.assertIn("U3", body)
            self.assertIn("Membership onboarding", body)
            self.assertEqual([], validate_state(frontmatter, root))

            # A gate write is a formal state write too, and it moves nothing
            # about the phase — the body must still agree afterwards.
            _, issues, changed = set_gate_status(
                root,
                gate="self_review",
                target="passed",
                decision_id="DEC-U3",
                evidence=frontmatter["artifacts"]["evidence"] + "#gate",
                actor="tests",
            )
            self.assertEqual([], issues, issues)
            self.assertTrue(changed)

            frontmatter, body = read_state(root)
            self.assertIn("U3", body)
            self.assertIn("| self_review | `passed` |", body)
            self.assertIn("| Status | `planned` |", body)
            self.assertEqual([], validate_state(frontmatter, root))

    def test_validate_stays_green_across_the_whole_sequence(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _shipped_u2_with_u3_on_disk(root)
            self.assertEqual([], validate_state(read_state(root)[0], root))

            activate_phase(
                root, phase_id="U3", phase_name="Membership onboarding",
                slug=U3_SLUG, actor="tests",
            )
            self.assertEqual([], validate_state(read_state(root)[0], root))

            _seal(root, "DEC-U3")
            frontmatter, body = read_state(root)
            updated = transition_state(
                frontmatter, "planned", root, actor="tests", reason="plan approved"
            )
            write_state(root / ".agent" / "STATE.md", updated, body)
            self.assertEqual([], validate_state(read_state(root)[0], root))


class WhatTheProjectionKeeps(unittest.TestCase):
    def test_fenced_prose_survives_every_write(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _shipped_u2_with_u3_on_disk(root)

            state, body = read_state(root)
            kept = "The pilot's category codes come from the client, not from us."
            write_state(
                root / ".agent" / "STATE.md",
                state,
                body + "\n{}\n{}\n{}\n".format(PRESERVE_OPEN, kept, PRESERVE_CLOSE),
            )
            self.assertIn(kept, read_state(root)[1])

            activate_phase(
                root, phase_id="U3", phase_name="Membership onboarding",
                slug=U3_SLUG, actor="tests",
            )

            _, body = read_state(root)
            self.assertIn(kept, body)
            self.assertIn("U3", body)
            # It is kept, and it is still fenced, so the next write keeps it too.
            self.assertIn(PRESERVE_OPEN, body)

            _seal(root, "DEC-U3")
            frontmatter, body = read_state(root)
            updated = transition_state(
                frontmatter, "planned", root, actor="tests", reason="plan approved"
            )
            write_state(root / ".agent" / "STATE.md", updated, body)
            self.assertIn(kept, read_state(root)[1])

    def test_an_unfenced_body_is_a_mirror_and_is_replaced(self) -> None:
        """Bodies written before the fence existed are stale by construction."""

        self.assertEqual("", extract_preserved("# STATE\n\nActive phase: U2.\n"))
        self.assertEqual("", extract_preserved(None))
        self.assertEqual("", extract_preserved(""))

    def test_the_projection_reports_what_the_frontmatter_holds(self) -> None:
        body = render_state_body(
            {
                "status": "executing",
                "execution_mode": "standard",
                "project": {"name": "Fluxo"},
                "phase": {"id": "U4", "name": "Categories", "status": "executing"},
                "current_task": {"id": "U4A", "status": "executing"},
                "next_action": {"operation": "execute-task", "target": "U4A"},
                "gates": {"release": "pending"},
                "plan_revision": {"version": 3, "fingerprint": "sha256:abc"},
                "blockers": [
                    {"id": "B-1", "status": "open", "summary": "Still open"},
                    {"id": "B-0", "status": "resolved", "summary": "Closed already"},
                ],
                "open_decisions": [{"id": "OD-005", "summary": "Chart of accounts?"}],
                "completed_phases": [{"id": "U3", "name": "Onboarding", "status": "shipped"}],
                "artifacts": {"plan": ".agent/phases/u4/PLAN.md"},
            }
        )
        self.assertIn("execute-task -> U4A", body)
        self.assertIn("`U4`", body)
        self.assertIn("| release | `pending` |", body)
        self.assertIn("| Sealed | yes |", body)
        self.assertIn("B-1", body)
        self.assertIn("OD-005", body)
        self.assertIn("U3", body)
        # A resolved blocker is not an open item and must not be listed as one.
        self.assertNotIn("Closed already", body)

    def test_an_unsealed_plan_says_so_in_words(self) -> None:
        body = render_state_body(
            {
                "status": "specified",
                "gates": {"release": "pending"},
                "plan_revision": {"version": 0, "fingerprint": None},
                "next_action": {"operation": "build-plan", "target": ".agent/PLAN.md"},
            }
        )
        self.assertIn("| Sealed | **no** |", body)

    def test_the_lightweight_state_gets_a_body_without_kernel_sections(self) -> None:
        """The resume-only shape has no gates, so it must not grow a gate table."""

        body = render_state_body(
            {
                "status": "proposed",
                "execution_mode": "standard",
                "project": {"name": "Small"},
                "next_action": {"operation": "build-short-plan", "target": ".agent/PLAN.md"},
                "artifacts": {"plan": ".agent/PLAN.md"},
            }
        )
        self.assertIn("build-short-plan", body)
        self.assertNotIn("## Gates", body)
        self.assertNotIn("## Plan revision", body)

    def test_regeneration_is_deterministic(self) -> None:
        """Same frontmatter, same body — a write that changes nothing is a no-op."""

        state = {
            "status": "planned",
            "project": {"name": "Fluxo"},
            "phase": {"id": "U4", "name": "Categories", "status": "planned"},
            "gates": {"release": "pending"},
            "next_action": {"operation": "execute-task", "target": "U4A"},
            "artifacts": {"plan": ".agent/PLAN.md"},
        }
        first = project_state_body(state, "")
        self.assertEqual(first, project_state_body(state, first))


if __name__ == "__main__":
    unittest.main()
