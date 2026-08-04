"""Advancing a phase whose leftover gate records disagree with its gates map.

The reported shape came from a project that had finished a task and could not
start the next one. `start-task` already knew how to advance from `verifying`,
and `reopen_review_gates` already knew how to move `gates` and `gate_records`
together — but the start refused first, over divergences that were exactly what
its own reopen would overwrite. The only move left was editing `STATE.md` by
hand, which is the thing the formal writers exist to avoid.

The divergences were legacy in a precise sense: every record was stamped with
another task, an earlier plan revision, or both, because an older kernel reset
the map without touching the ledger index. These tests pin that the advance may
spend exactly those, and nothing else — a record about the current task at the
current revision is live disagreement and still refuses.
"""

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.contracts import load_task_index, update_task_status
from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.next_operation import determine_next_operation
from kernel.runtime.state_machine import superseded_gate_records, validate_state
from kernel.runtime.task_start import start_task
from tests.helpers import (
    initialized_project,
    minimal_task,
    read_state,
    write_state,
    write_tasks,
)


DONE = "feat/u3b2-membership-welcome-routing"
NEXT = "feat/u3c-controlled-organization-creation"

#: The revision the plan is on, after the amendment that reopened the gates.
CURRENT_REVISION = 6

#: The revision every leftover record was granted under.
LEGACY_REVISION = 5


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def _tasks():
    return [
        minimal_task("U3A", status="verified"),
        minimal_task("U3B1", status="verified"),
        minimal_task("U3B2", depends_on=["U3A", "U3B1"]),
        minimal_task("U3C"),
    ]


def _legacy_record(gate: str, status: str, *, task_id="U3B1", revision=LEGACY_REVISION):
    return {
        "gate": gate,
        "status": status,
        "task_id": task_id,
        "plan_revision": revision,
        "decision": "D-056",
        "evidence": "REVIEW.md",
        "at": "2026-08-03T23:07:54+00:00",
        "by": "reviewer",
        "history": [],
    }


def _reported_shape(root: Path, *, records=None, gates=None, blockers=None) -> None:
    """U3B2 verified, U3C pending, and the divergences the advance inherits.

    Built through the real writers as far as they go: U3B2 is started and its
    contract driven to `verified` the way execution and verification leave it.
    Only the legacy drift is injected, because no current writer produces it —
    that is the point of the fixture.
    """

    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")

    initialized_project(root, with_phase=True)
    write_tasks(root, _tasks())
    state, _ = read_state(root)
    state["status"] = "planned"
    state["phase"]["status"] = "planned"
    state["current_task"] = {"id": None, "status": None}
    state["next_action"] = {"operation": "execute-task", "target": None}
    state["risk"] = {"level": "medium", "reasons": ["legacy divergence fixture"]}
    state["gates"]["plan_quality"] = "passed"
    state["git"]["base_branch"] = "main"
    state["git"]["working_branch"] = "main"
    state["context"]["source_commit"] = None
    write_state(root, state)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "planned")

    _git(root, "checkout", "-b", DONE)
    start_task(root, actor="workflow-runner", reason="plan gate passed")

    state, body = load_frontmatter(root / ".agent" / "STATE.md")
    state["status"] = "verifying"
    # The hand-edit that broke the mirror: a phase left `executing` while the
    # canonical status moved on.
    state["phase"]["status"] = "executing"
    state["current_task"]["status"] = "verified"
    state["gates"]["self_review"] = "passed"
    state["gates"]["spec_compliance"] = "passed_with_notes"
    state["gates"].update(
        gates
        if gates is not None
        else {
            "code_quality": "approved_with_notes",
            "acceptance": "pending",
            "verification": "pending",
        }
    )
    state["gate_records"] = dict(state.get("gate_records") or {})
    state["gate_records"].update(
        records
        if records is not None
        else {
            "acceptance": _legacy_record("acceptance", "passed", task_id=None),
            "verification": _legacy_record("verification", "passed", task_id=None),
            "code_quality": _legacy_record("code_quality", "not_required"),
        }
    )
    # The amendment that reopened the gates and left every record behind.
    state["plan_revision"] = dict(state["plan_revision"], version=CURRENT_REVISION)
    state["next_action"] = {"operation": "verify-phase", "target": "U3B2"}
    if blockers is not None:
        state["blockers"] = blockers
    write_frontmatter(root / ".agent" / "STATE.md", state, body)

    tasks_path = root / state["artifacts"]["tasks"]
    for step in ("implementation_complete", "reviewing", "reviewed", "verifying", "verified"):
        update_task_status(tasks_path, "U3B2", step)

    _git(root, "add", "-A")
    _git(root, "commit", "-m", "U3B2 verified")
    _git(root, "checkout", "-b", NEXT)


def _advance(root: Path, **overrides):
    arguments = {
        "actor": "workflow-runner",
        "reason": "U3B2 verified; U3C is the next eligible Standard task",
        "task_id": "U3C",
    }
    arguments.update(overrides)
    return start_task(root, **arguments)


def _statuses(root: Path):
    state, _ = read_state(root)
    index, _ = load_task_index(root / state["artifacts"]["tasks"])
    return {task["id"]: task["status"] for task in index["tasks"]}


class SupersededRecordTest(unittest.TestCase):
    def test_classifies_records_of_other_tasks_and_earlier_revisions(self):
        state = {
            "plan_revision": {"version": CURRENT_REVISION},
            "current_task": {"id": "U3B2"},
            "gates": {
                "acceptance": "pending",
                "verification": "pending",
                "code_quality": "approved_with_notes",
                "spec_compliance": "passed_with_notes",
            },
            "gate_records": {
                "acceptance": _legacy_record("acceptance", "passed", task_id=None),
                "verification": _legacy_record("verification", "passed", task_id=None),
                "code_quality": _legacy_record("code_quality", "not_required"),
                # Agrees with the map, so it is not a divergence at all.
                "spec_compliance": _legacy_record(
                    "spec_compliance", "passed_with_notes"
                ),
            },
        }
        self.assertEqual(
            superseded_gate_records(state),
            {"acceptance", "verification", "code_quality"},
        )

    def test_current_task_at_current_revision_is_not_superseded(self):
        state = {
            "plan_revision": {"version": CURRENT_REVISION},
            "current_task": {"id": "U3B2"},
            "gates": {"code_quality": "approved_with_notes"},
            "gate_records": {
                "code_quality": _legacy_record(
                    "code_quality",
                    "changes_required",
                    task_id="U3B2",
                    revision=CURRENT_REVISION,
                )
            },
        }
        self.assertEqual(superseded_gate_records(state), set())

    def test_unplaceable_revision_is_not_superseded(self):
        """No current revision to compare against is ambiguity, not staleness."""

        state = {
            "plan_revision": {},
            "current_task": {"id": "U3B2"},
            "gates": {"acceptance": "pending"},
            "gate_records": {
                "acceptance": _legacy_record("acceptance", "passed", task_id=None)
            },
        }
        self.assertEqual(superseded_gate_records(state), set())


class LegacyDivergenceAdvanceTest(unittest.TestCase):
    def test_derivation_points_at_the_next_task_and_still_reports_the_drift(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            decision = determine_next_operation(root)

            self.assertEqual(
                decision["next_operation"],
                {"operation": "execute-task", "target": "U3C"},
            )
            self.assertEqual(decision["blocking_conditions"], [])
            # Reported, never hidden: the operator sees what the advance is
            # about to overwrite.
            self.assertEqual(len(decision["advance_resolvable"]), 4)
            for message in decision["advance_resolvable"]:
                self.assertIn(message, decision["inconsistencies"])

    def test_advance_starts_the_next_task(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            updated, issues, changed = _advance(root)

            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(updated["status"], "executing")
            self.assertEqual(updated["phase"]["status"], "executing")
            self.assertEqual(updated["current_task"]["id"], "U3C")
            self.assertEqual(updated["current_task"]["status"], "executing")

    def test_binding_rotates_and_the_finished_one_becomes_history(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            updated, _, _ = _advance(root)

            self.assertEqual(updated["current_task"]["execution"]["task_id"], "U3C")
            self.assertEqual(updated["current_task"]["execution"]["branch"], NEXT)
            self.assertEqual(updated["git"]["last_execution"]["task_id"], "U3B2")
            self.assertEqual(updated["git"]["last_execution"]["branch"], DONE)

    def test_finished_tasks_stay_verified(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            _advance(root)

            self.assertEqual(
                _statuses(root),
                {
                    "U3A": "verified",
                    "U3B1": "verified",
                    "U3B2": "verified",
                    "U3C": "executing",
                },
            )

    def test_gates_and_records_reopen_together_without_copying_approval(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            updated, _, _ = _advance(root)

            for gate in ("acceptance", "verification", "code_quality"):
                record = updated["gate_records"][gate]
                self.assertEqual(updated["gates"][gate], "pending", gate)
                self.assertEqual(record["status"], "pending", gate)
                self.assertEqual(record["plan_revision"], CURRENT_REVISION, gate)
                # Nothing the previous task was judged for may speak for this
                # one: the reopened record carries no verdict and no evidence.
                self.assertIsNone(record["decision"], gate)
                self.assertIsNone(record["evidence"], gate)

    def test_the_old_verdicts_survive_in_history(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            updated, _, _ = _advance(root)

            # The verdict archived is the *record's*, with the provenance it
            # was granted under — the legacy revision it belonged to, not the
            # one the phase has moved to. Nothing is dropped and nothing is
            # restamped, so the judgement stays readable as U3B1's.
            for gate, verdict in (
                ("acceptance", "passed"),
                ("verification", "passed"),
                ("code_quality", "not_required"),
            ):
                history = updated["gate_records"][gate]["history"]
                self.assertEqual([entry["status"] for entry in history], [verdict], gate)
                self.assertEqual(history[0]["plan_revision"], LEGACY_REVISION, gate)
                self.assertEqual(history[0]["decision"], "D-056", gate)

    def test_state_validates_after_the_advance(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            _advance(root)

            state, _ = read_state(root)
            self.assertEqual(validate_state(state, root), [])
            self.assertEqual(determine_next_operation(root)["blocking_conditions"], [])

    def test_the_start_is_recorded_in_the_ledger(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            updated, _, _ = _advance(root)

            text = (root / updated["artifacts"]["evidence"]).read_text(encoding="utf-8")
            events = [
                json.loads(block.split("```", 1)[0])
                for block in text.split("```json\n")[1:]
            ]
            starts = [event for event in events if event.get("kind") == "task-start"]
            self.assertEqual(starts[-1]["task_id"], "U3C")
            self.assertEqual(starts[-1]["details"]["follows_task"], "U3B2")


class LegacyDivergenceRefusalTest(unittest.TestCase):
    def test_refuses_a_record_about_the_current_task_and_revision(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(
                root,
                records={
                    "code_quality": _legacy_record(
                        "code_quality",
                        "changes_required",
                        task_id="U3B2",
                        revision=CURRENT_REVISION,
                    )
                },
            )

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("gate code_quality" in issue for issue in issues), issues
            )

    def test_refuses_an_open_blocker(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(
                root,
                blockers=[
                    {
                        "id": "B-009",
                        "summary": "migration not reversible",
                        "status": "open",
                    }
                ],
            )

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(any("B-009" in issue for issue in issues), issues)

    def test_refuses_a_task_the_kernel_did_not_select(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            _, issues, changed = _advance(root, task_id="U3B1")

            self.assertFalse(changed)
            self.assertTrue(any("U3B1" in issue for issue in issues), issues)

    def test_refuses_any_other_inconsistency(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            # A fault the advance does not write over: the sealed plan no
            # longer matches the artifacts it was sealed against.
            state["plan_revision"] = dict(
                state["plan_revision"], fingerprint="sha256:" + "0" * 64
            )
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            self.assertTrue(
                any("resolve state inconsistencies first" in issue for issue in issues),
                issues,
            )

    def test_refuses_while_the_current_task_is_not_verified(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _reported_shape(root)

            state, body = load_frontmatter(root / ".agent" / "STATE.md")
            state["current_task"]["status"] = "verifying"
            write_frontmatter(root / ".agent" / "STATE.md", state, body)

            _, issues, changed = _advance(root)

            self.assertFalse(changed)
            # Without the advance shape nothing is forgiven, so the drift the
            # advance would have overwritten becomes a refusal again.
            self.assertTrue(
                any("resolve state inconsistencies first" in issue for issue in issues),
                issues,
            )


if __name__ == "__main__":
    unittest.main()
