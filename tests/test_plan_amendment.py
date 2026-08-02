"""Amending the contract of a task that is already under way.

The reported shape, reproduced: a task implemented, reviewed by two independent
reviewers, locally verified, published — and then failed by CI, on a path no
local verification reached. The correction was not to the code but to the
contract: two more files in `allowed_files`, one acceptance criterion rewritten,
one added.

Nothing in the kernel could seal that. `seal-plan` refuses outside `specified`,
`reconcile-phase` describes work already integrated, and the only mechanical
route to a second seal ran through a manufactured `BLOCKED` review and a return
to `specified` — which releases the binding and claims nobody had started.

A second dead end sits underneath the first: `TASK_STATUS_TRANSITIONS` gives
`verified` no outgoing edge, so a locally verified task had no way back into
execution even if the seal were solved.
"""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from kernel.runtime.amendment import amend_plan
from kernel.runtime.cli import build_parser, main
from kernel.runtime.contracts import load_task_index
from kernel.runtime.documents import DocumentError, load_frontmatter
from kernel.runtime.state_machine import (
    REVIEW_GATES,
    compute_plan_fingerprint,
    validate_state,
)
from tests.helpers import (
    initialized_project,
    minimal_task,
    read_state,
    write_state,
    write_tasks,
)


FEATURE = "feat/u3a-organization-setup"
OTHER = "feat/something-else"
DECISION = "D-047"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return completed.stdout.strip()


def _record_decision(root: Path, state, decision_id: str = DECISION) -> None:
    path = root / state["artifacts"]["decisions"]
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n### {} — CI exposed a defective active-task contract\n\n"
        "- Status: accepted\n".format(decision_id),
        encoding="utf-8",
    )


def _verifying_phase(root: Path, *, task_status: str = "verified", tasks=None) -> None:
    """A task locally verified and published, with the plan sealed at v1."""

    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tests@example.com")
    _git(root, "config", "user.name", "tests")
    (root / "README.md").write_text("# project\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "initial")
    _git(root, "checkout", "-b", FEATURE)

    initialized_project(root, with_phase=True)
    write_tasks(
        root,
        tasks
        if tasks is not None
        else [
            minimal_task("U3A", status=task_status),
            minimal_task("U3B1"),
            minimal_task("U3B2", depends_on=["U3A", "U3B1"]),
            minimal_task("U3C"),
        ],
    )
    state, _ = read_state(root)
    state["status"] = "verifying"
    state["phase"]["status"] = "verifying"
    state["current_task"] = {
        "id": "U3A",
        "status": task_status,
        "execution": {
            "task_id": "U3A",
            "branch": FEATURE,
            "worktree": ".",
            "bound_at": "2026-08-02T16:09:54+00:00",
            "bound_by": "workflow-runner",
        },
    }
    state["next_action"] = {"operation": "verify-phase", "target": "U3A"}
    state["risk"] = {"level": "medium", "reasons": ["amendment fixture"]}
    state["gates"].update(
        {
            "specification": "passed",
            "plan_quality": "passed",
            "self_review": "passed",
            "spec_compliance": "passed_with_notes",
            "code_quality": "approved",
            "acceptance": "passed",
            "verification": "passed",
        }
    )
    state["git"]["base_branch"] = "main"
    state["git"]["worktree"] = "."
    state["context"]["source_commit"] = None
    _record_decision(root, state)
    write_state(root, state)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "verifying")


def _amend_the_contract(root: Path) -> None:
    """The legitimate edit CI forced: two files, one AC rewritten, one added."""

    state, _ = read_state(root)
    path = root / state["artifacts"]["tasks"]
    index, body = load_frontmatter(path)
    task = next(item for item in index["tasks"] if item["id"] == "U3A")
    task["allowed_files"] = list(task["allowed_files"]) + [
        "e2e/customer-onboarding.spec.ts",
        "e2e/support/first-access.ts",
    ]
    task["acceptance"][0]["criterion"] = (
        "Redirects internally, without a loop, and never to welcome."
    )
    task["acceptance"].append(
        {
            "id": "AC-06",
            "criterion": "A configured organization enters the operational area.",
        }
    )
    from kernel.runtime.documents import write_frontmatter

    write_frontmatter(path, index, body)


def _evidence(root: Path) -> str:
    state, _ = read_state(root)
    return state["artifacts"]["evidence"] + "#event-2026-08-02T17:09:38+00:00"


def _amend(root: Path, **overrides):
    arguments = {
        "decision_id": DECISION,
        "evidence": _evidence(root),
        "actor": "planner",
        "reason": "CI exposed a defective active-task contract.",
    }
    arguments.update(overrides)
    return amend_plan(root, **arguments)


def _statuses(root: Path):
    state, _ = read_state(root)
    index, _ = load_task_index(root / state["artifacts"]["tasks"])
    return {task["id"]: task["status"] for task in index["tasks"]}


class TheReportedScenario(unittest.TestCase):
    def test_the_edit_invalidates_the_seal(self) -> None:
        """Before the operation exists, the state is simply broken."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            self.assertEqual(validate_state(read_state(root)[0], root), [])

            _amend_the_contract(root)
            codes = {
                issue["code"] for issue in validate_state(read_state(root)[0], root)
            }
            self.assertIn("plan-changed-without-revision", codes)

    def test_the_verified_task_has_no_way_back(self) -> None:
        """The second half of the gap: `verified` has no outgoing transition."""

        from kernel.runtime.contracts import TASK_STATUS_TRANSITIONS

        self.assertEqual(TASK_STATUS_TRANSITIONS["verified"], set())

    def test_amend_plan_reseals_in_place(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            before, _ = read_state(root)
            binding_before = dict(before["current_task"]["execution"])
            _amend_the_contract(root)

            state, issues, changed = _amend(root)
            self.assertEqual(issues, [])
            self.assertTrue(changed)

            # The seal describes the artifacts as they are, and the kernel
            # computed it — there is no argument through which it could be named.
            self.assertEqual(state["plan_revision"]["version"], 2)
            self.assertEqual(
                state["plan_revision"]["fingerprint"],
                compute_plan_fingerprint(state, root),
            )
            self.assertEqual(state["plan_revision"]["decision_id"], DECISION)
            self.assertEqual(state["plan_revision"]["supersedes"]["version"], 1)
            self.assertEqual(
                state["plan_revision"]["supersedes"]["fingerprint"],
                before["plan_revision"]["fingerprint"],
            )
            self.assertNotEqual(
                state["plan_revision"]["fingerprint"],
                before["plan_revision"]["fingerprint"],
            )

            # The state stands on its own.
            self.assertEqual(validate_state(state, root), [])
            self.assertEqual(validate_state(read_state(root)[0], root), [])

    def test_the_task_and_its_binding_are_preserved(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            binding_before = dict(read_state(root)[0]["current_task"]["execution"])
            _amend_the_contract(root)

            state, issues, _ = _amend(root)
            self.assertEqual(issues, [])

            self.assertEqual(state["current_task"]["id"], "U3A")
            # Byte for byte: the work did not restart, so `bound_at` and
            # `bound_by` still describe when and by whom it began.
            self.assertEqual(state["current_task"]["execution"], binding_before)
            # The binding was not released on the way through.
            self.assertNotIn("last_execution", state.get("git", {}))

    def test_the_phase_and_task_return_to_execution(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            state, issues, _ = _amend(root)
            self.assertEqual(issues, [])

            self.assertEqual(state["status"], "executing")
            self.assertEqual(state["phase"]["status"], "executing")
            self.assertEqual(state["current_task"]["status"], "executing")
            # The index moved with it, which is what `verified` alone forbade.
            self.assertEqual(_statuses(root)["U3A"], "executing")
            self.assertEqual(
                state["next_action"], {"operation": "resume-task", "target": "U3A"}
            )

    def test_the_five_gates_reopen_and_the_rest_stand(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            state, issues, _ = _amend(root)
            self.assertEqual(issues, [])

            for gate in REVIEW_GATES:
                self.assertEqual(state["gates"][gate], "pending", gate)
            # An amendment made under a recorded decision is the plan process
            # working, not evidence against it.
            self.assertEqual(state["gates"]["specification"], "passed")
            self.assertEqual(state["gates"]["plan_quality"], "passed")

    def test_the_old_approvals_survive_in_the_ledger(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            state, issues, _ = _amend(root)
            self.assertEqual(issues, [])

            ledger = (root / state["artifacts"]["evidence"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("plan-amendment", ledger)
            self.assertIn('"revision_from": 1', ledger)
            self.assertIn('"revision_to": 2', ledger)
            self.assertIn(DECISION, ledger)
            # What the gates held before is recorded, because the review-owned
            # gates keep no record of their own.
            self.assertIn('"gates_before"', ledger)
            self.assertIn("passed_with_notes", ledger)
            self.assertIn(state["plan_revision"]["fingerprint"], ledger)

    def test_the_other_tasks_are_untouched(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            _amend(root)
            statuses = _statuses(root)
            self.assertEqual(statuses["U3B1"], "pending")
            self.assertEqual(statuses["U3B2"], "pending")
            self.assertEqual(statuses["U3C"], "pending")

    def test_new_reviews_can_then_be_recorded_against_the_new_revision(self) -> None:
        """The point of the operation: the correction proceeds normally."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _amend(root)

            from kernel.runtime.gates import set_gate_status

            state, issues, changed = set_gate_status(
                root,
                gate="verification",
                target="passed",
                decision_id=DECISION,
                evidence=_evidence(root),
                actor="reviewer",
            )
            self.assertEqual(issues, [])
            self.assertTrue(changed)
            record = state["gate_records"]["verification"]
            self.assertEqual(record["status"], "passed")
            # The new judgement is bound to the revision it was made against.
            self.assertEqual(record["plan_revision"], 2)
            self.assertEqual(validate_state(state, root), [])


class GatesAndRecordsStayCoherent(unittest.TestCase):
    def test_a_stamped_record_may_not_diverge_from_the_map(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _amend(root)

            from kernel.runtime.gates import set_gate_status

            set_gate_status(
                root,
                gate="verification",
                target="passed",
                decision_id=DECISION,
                evidence=_evidence(root),
                actor="reviewer",
            )
            state, body = read_state(root)
            # Hand-edit exactly the drift this rule exists to catch.
            state["gates"]["verification"] = "pending"
            codes = {issue["code"] for issue in validate_state(state, root)}
            self.assertIn("gate-record-divergence", codes)

    def test_unstamped_records_are_left_alone(self) -> None:
        """Projects written before revisions were stamped are not migrated."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            state, _ = read_state(root)
            state["gate_records"] = {
                "verification": {"status": "passed", "decision": "DEC-OLD"}
            }
            state["gates"]["verification"] = "failed"
            codes = {issue["code"] for issue in validate_state(state, root)}
            self.assertNotIn("gate-record-divergence", codes)

    def test_reentering_execution_moves_records_with_the_map(self) -> None:
        """The drift this fixes: a transition used to reset only the map."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            # A task the transition is willing to move: `verifying -> executing`
            # requires a pending task, which is itself part of why a verified
            # one had nowhere to go.
            _verifying_phase(root, task_status="pending")
            from kernel.runtime.gates import set_gate_status
            from kernel.runtime.state_machine import transition_state

            set_gate_status(
                root,
                gate="self_review",
                target="failed",
                decision_id=None,
                evidence=_evidence(root),
                actor="reviewer",
            )
            state, _ = read_state(root)
            updated = transition_state(
                state, "executing", root, actor="reviewer", reason="rework"
            )
            self.assertEqual(updated["gates"]["self_review"], "pending")
            self.assertEqual(
                updated["gate_records"]["self_review"]["status"], "pending"
            )
            self.assertEqual(
                updated["gate_records"]["self_review"]["history"][-1]["status"],
                "failed",
            )
            # The point: map and record moved together, so nothing diverges.
            # (`transition_state` leaves the index write to its caller, so the
            # unrelated task-state check is not asserted here.)
            codes = {issue["code"] for issue in validate_state(updated, root)}
            self.assertNotIn("gate-record-divergence", codes)


class Idempotency(unittest.TestCase):
    def test_the_same_amendment_twice_is_unchanged(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            first, issues, changed = _amend(root)
            self.assertTrue(changed)

            ledger_path = root / first["artifacts"]["evidence"]
            ledger_after_first = ledger_path.read_text(encoding="utf-8")

            second, issues, changed_again = _amend(root)
            self.assertEqual(issues, [])
            self.assertFalse(changed_again)
            self.assertEqual(second["plan_revision"]["version"], 2)
            self.assertEqual(
                second["plan_revision"]["amended_at"],
                first["plan_revision"]["amended_at"],
            )
            self.assertEqual(
                second["current_task"]["execution"],
                first["current_task"]["execution"],
            )
            self.assertEqual(ledger_path.read_text(encoding="utf-8"), ledger_after_first)

    def test_a_repeat_under_a_different_decision_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _amend(root)

            state, _ = read_state(root)
            _record_decision(root, state, "D-048")
            _, issues, changed = _amend(root, decision_id="D-048")
            self.assertFalse(changed)
            self.assertTrue(
                any("refusing to rewrite a landed amendment" in item for item in issues),
                issues,
            )

    def test_a_repeat_under_different_evidence_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _amend(root)

            _, issues, changed = _amend(
                root, evidence=_evidence(root).split("#")[0] + "#other"
            )
            self.assertFalse(changed)
            self.assertTrue(
                any("refusing to rewrite a landed amendment" in item for item in issues),
                issues,
            )

    def test_further_edits_after_an_amendment_amend_again(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _amend(root)

            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            task = next(item for item in index["tasks"] if item["id"] == "U3A")
            task["allowed_files"] = list(task["allowed_files"]) + ["e2e/extra.spec.ts"]
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(path, index, body)

            third, issues, changed = _amend(root)
            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(third["plan_revision"]["version"], 3)
            self.assertEqual(third["plan_revision"]["supersedes"]["version"], 2)


class Refusals(unittest.TestCase):
    def _refuses(self, root: Path, fragment: str, **overrides) -> None:
        _, issues, changed = _amend(root, **overrides)
        self.assertFalse(changed)
        self.assertTrue(
            any(fragment in item for item in issues),
            "expected {!r} in {!r}".format(fragment, issues),
        )

    def test_no_change_to_the_artifacts(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            self._refuses(root, "are unchanged since revision 1")

    def test_an_unsealed_plan(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, body = read_state(root)
            state["plan_revision"] = {
                "version": None,
                "decision_id": None,
                "fingerprint": None,
                "evidence": None,
            }
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self._refuses(root, "no sealed plan to amend")

    def test_a_decision_that_is_not_recorded(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            self._refuses(root, "is not recorded in DECISIONS.md", decision_id="D-999")

    def test_evidence_that_does_not_exist(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            self._refuses(
                root, "evidence file is missing", evidence=".agent/phases/01-kernel/NOPE.md"
            )

    def test_evidence_from_another_phase(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            other = root / ".agent" / "phases" / "02-other"
            other.mkdir(parents=True)
            (other / "EVIDENCE.md").write_text("# other\n", encoding="utf-8")
            self._refuses(
                root,
                "evidence belongs to phase",
                evidence=".agent/phases/02-other/EVIDENCE.md",
            )

    def test_a_phase_with_nothing_under_way(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, body = read_state(root)
            state["status"] = "planned"
            state["phase"]["status"] = "planned"
            state["current_task"] = {"id": None, "status": None}
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self._refuses(root, "requires a phase in executing, reviewing, verifying")

    def test_a_shipped_phase(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, body = read_state(root)
            state["status"] = "shipped"
            state["phase"]["status"] = "shipped"
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self._refuses(root, "requires a phase in executing, reviewing, verifying")

    def test_an_integrated_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, body = read_state(root)
            state["completed_units"] = [
                {"id": "U3A", "integrated_by": {"pull_request": 27}}
            ]
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self._refuses(root, "is already integrated")

    def test_a_divergent_branch(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _git(root, "checkout", "-b", OTHER)
            self._refuses(root, "the current branch is {}".format(OTHER))

    def test_a_detached_head(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _git(root, "checkout", "--detach")
            self._refuses(root, "HEAD is detached")

    def test_an_amendment_that_removes_the_current_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            index["tasks"] = [
                task for task in index["tasks"] if task["id"] != "U3A"
            ]
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(path, index, body)
            self._refuses(root, "may not remove or rename the task it is amending")

    def test_an_amendment_that_starts_another_task(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            next(item for item in index["tasks"] if item["id"] == "U3B1")[
                "status"
            ] = "executing"
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(path, index, body)
            self._refuses(root, "starts another task")

    def test_an_amendment_that_completes_downstream_work(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            next(item for item in index["tasks"] if item["id"] == "U3B2")[
                "status"
            ] = "verified"
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(path, index, body)
            self._refuses(root, "complete while U3A is still open")

    def test_an_invalid_dependency(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            next(item for item in index["tasks"] if item["id"] == "U3C")[
                "depends_on"
            ] = ["GHOST"]
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(path, index, body)
            self._refuses(root, "amended task graph")

    def test_a_malformed_contract(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, _ = read_state(root)
            path = root / state["artifacts"]["tasks"]
            index, body = load_frontmatter(path)
            del next(item for item in index["tasks"] if item["id"] == "U3C")[
                "acceptance"
            ]
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(path, index, body)
            self._refuses(root, "U3C")

    def test_the_wrong_revision_number(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            self._refuses(root, "is not the next revision", version=5)

    def test_the_right_revision_number_is_accepted(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            _, issues, changed = _amend(root, version=2)
            self.assertEqual(issues, [])
            self.assertTrue(changed)

    def test_an_unrelated_state_error_is_not_sealed_over(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)
            state, body = read_state(root)
            state["risk"] = {"level": "nonsense"}
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            self._refuses(root, "errors an amendment does not repair")


class Rollback(unittest.TestCase):
    def test_a_failed_state_write_restores_every_document(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            state, _ = read_state(root)
            state_path = root / ".agent" / "STATE.md"
            tasks_path = root / state["artifacts"]["tasks"]
            ledger_path = root / state["artifacts"]["evidence"]
            before = {
                path: path.read_bytes()
                for path in (state_path, tasks_path, ledger_path)
            }

            real = __import__(
                "kernel.runtime.amendment", fromlist=["write_frontmatter"]
            ).write_frontmatter

            def explode(path, data, body):
                if Path(path).name == "STATE.md":
                    raise OSError("disk full")
                return real(path, data, body)

            with patch("kernel.runtime.amendment.write_frontmatter", explode):
                with self.assertRaises(OSError):
                    _amend(root)

            for path, content in before.items():
                self.assertEqual(path.read_bytes(), content, path.name)
            # And the state is still exactly as broken as it was, so the
            # operator sees the same problem and repeats the same command.
            codes = {
                issue["code"] for issue in validate_state(read_state(root)[0], root)
            }
            self.assertIn("plan-changed-without-revision", codes)

    def test_a_failed_ledger_append_writes_nothing(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            state, _ = read_state(root)
            state_path = root / ".agent" / "STATE.md"
            tasks_path = root / state["artifacts"]["tasks"]
            ledger_path = root / state["artifacts"]["evidence"]
            before = {
                path: path.read_bytes()
                for path in (state_path, tasks_path, ledger_path)
            }

            with patch(
                "kernel.runtime.amendment.append_evidence_event",
                side_effect=OSError("ledger unavailable"),
            ):
                with self.assertRaises(OSError):
                    _amend(root)

            for path, content in before.items():
                self.assertEqual(path.read_bytes(), content, path.name)

    def test_a_failed_index_write_restores_the_ledger(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            state, _ = read_state(root)
            ledger_path = root / state["artifacts"]["evidence"]
            before = ledger_path.read_bytes()

            real = __import__(
                "kernel.runtime.amendment", fromlist=["write_frontmatter"]
            ).write_frontmatter

            def explode(path, data, body):
                if Path(path).name == "TASKS.md":
                    raise OSError("disk full")
                return real(path, data, body)

            with patch("kernel.runtime.amendment.write_frontmatter", explode):
                with self.assertRaises(OSError):
                    _amend(root)

            self.assertEqual(ledger_path.read_bytes(), before)


class Compatibility(unittest.TestCase):
    def test_a_project_without_gate_records_amends_normally(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            state, body = read_state(root)
            state.pop("gate_records", None)
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            _amend_the_contract(root)

            amended, issues, changed = _amend(root)
            self.assertEqual(issues, [])
            self.assertTrue(changed)
            self.assertEqual(validate_state(amended, root), [])

    def test_a_legacy_binding_still_guards_the_branch(self) -> None:
        """States written before `current_task.execution` fall back to git."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            state, body = read_state(root)
            del state["current_task"]["execution"]
            state["git"]["working_branch"] = FEATURE
            from kernel.runtime.documents import write_frontmatter

            write_frontmatter(root / ".agent" / "STATE.md", state, body)
            _amend_the_contract(root)
            _git(root, "checkout", "-b", OTHER)

            _, issues, changed = _amend(root)
            self.assertFalse(changed)
            self.assertTrue(
                any("the current branch is" in item for item in issues), issues
            )


class CommandLine(unittest.TestCase):
    def test_the_parser_never_accepts_a_fingerprint(self) -> None:
        parser = build_parser()
        arguments = parser.parse_args(
            [
                "amend-plan",
                "--decision",
                DECISION,
                "--evidence",
                ".agent/phases/01-kernel/EVIDENCE.md",
                "--actor",
                "planner",
                "--reason",
                "CI exposed a defective contract.",
            ]
        )
        self.assertFalse(hasattr(arguments, "fingerprint"))
        self.assertIsNone(arguments.version)

    def test_the_command_reports_what_changed(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            _amend_the_contract(root)

            code = main(
                [
                    "--project",
                    str(root),
                    "amend-plan",
                    "--decision",
                    DECISION,
                    "--evidence",
                    _evidence(root),
                    "--actor",
                    "planner",
                    "--reason",
                    "CI exposed a defective contract.",
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(read_state(root)[0]["plan_revision"]["version"], 2)

    def test_a_refusal_exits_non_zero(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _verifying_phase(root)
            code = main(
                [
                    "--project",
                    str(root),
                    "amend-plan",
                    "--decision",
                    DECISION,
                    "--evidence",
                    _evidence(root),
                    "--actor",
                    "planner",
                    "--reason",
                    "nothing changed",
                ]
            )
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
