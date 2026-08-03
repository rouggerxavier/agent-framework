from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from kernel.runtime.documents import load_frontmatter, write_frontmatter
from kernel.runtime.project import initialize_phase, initialize_project
from kernel.runtime.contracts import SELF_REVIEW_CHECKS
from kernel.runtime.state_machine import compute_plan_fingerprint


FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]


def initialized_project(root: Path, *, with_phase: bool = False) -> Dict[str, Any]:
    initialize_project(
        root, FRAMEWORK_ROOT, project_name="test-project", mode="full"
    )
    if with_phase:
        initialize_phase(
            root,
            FRAMEWORK_ROOT,
            phase_id="P1",
            phase_name="Kernel",
            slug="01-kernel",
            actor="tests",
        )
    state, _ = load_frontmatter(root / ".agent" / "STATE.md")
    return state


def read_state(root: Path) -> Tuple[Dict[str, Any], str]:
    return load_frontmatter(root / ".agent" / "STATE.md")


def write_state(root: Path, state: Dict[str, Any], body: str = "# State\n") -> None:
    if state.get("status") in {
        "planned",
        "executing",
        "reviewing",
        "verifying",
        "ready_to_ship",
        "shipped",
    }:
        seal_plan(state, root)
    write_frontmatter(root / ".agent" / "STATE.md", state, body)


def write_tasks(
    root: Path, tasks: List[Dict[str, Any]], *, default_mode: str = None
) -> Path:
    state, _ = read_state(root)
    path = root / state["artifacts"]["tasks"]
    index: Dict[str, Any] = {
        "schema_version": 1,
        "phase": {"id": "P1", "name": "Kernel"},
        "tasks": tasks,
    }
    if default_mode is not None:
        index["default_execution_mode"] = default_mode
    write_frontmatter(path, index, "# Tasks\n")
    return path


def minimal_task(
    task_id: str = "P1-T01",
    *,
    status: str = "pending",
    depends_on: List[str] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": task_id,
        "title": "Task {}".format(task_id),
        "status": status,
        "change_type": "documentation",
        "goal": {"description": "Complete {}".format(task_id)},
        "depends_on": list(depends_on or []),
        "read_first": ["README.md"],
        "allowed_files": ["README.md"],
        "forbidden_changes": ["Runtime behavior"],
        "requirements": ["REQ-TEST"],
        "acceptance": [{"id": "AC-01", "criterion": "Task is documented."}],
        "test_policy": {"mode": "test-exempt", "commands": [], "retry_limit": 0},
        "runtime_verification": [],
        "rollback": {"strategy": "revert-task-commit"},
        "review": {
            "self_review": "required",
            "spec_compliance": "required",
            "code_quality": "required",
        },
        "completion": {
            "requires": [
                "acceptance-evidence",
                "reviewed-diff",
                "atomic-commit",
            ]
        },
    }


def set_lifecycle(state: Dict[str, Any], status: str) -> Dict[str, Any]:
    state["status"] = status
    if state["phase"].get("id"):
        state["phase"]["status"] = status
    return state


def seal_plan(state: Dict[str, Any], root: Path) -> Dict[str, Any]:
    decisions = root / state["artifacts"]["decisions"]
    decision_text = decisions.read_text(encoding="utf-8")
    if "### DEC-TEST " not in decision_text:
        decisions.write_text(
            decision_text
            + "\n### DEC-TEST — Approve test plan\n\n"
            + "- Status: accepted\n"
            + "- Decision: Approve the sealed test plan.\n",
            encoding="utf-8",
        )
    state["plan_revision"] = {
        "version": 1,
        "decision_id": "DEC-TEST",
        "fingerprint": compute_plan_fingerprint(state, root),
        "evidence": state["artifacts"]["evidence"] + "#plan-gate",
    }
    return state


def full_contract() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "id": "P1-T03",
        "title": "Normalize property types",
        "status": "executing",
        "change_type": "business_logic",
        "goal": {"description": "Normalize property types."},
        "depends_on": [],
        "read_first": ["app/mapper.py", "tests/test_mapper.py"],
        "allowed_files": ["app/mapper.py", "tests/test_mapper.py"],
        "forbidden_changes": ["Database schema"],
        "requirements": ["REQ-004"],
        "acceptance": [
            {"id": "AC-01", "criterion": "Known values map."},
            {"id": "AC-02", "criterion": "Unknown values are traceable."},
        ],
        "test_policy": {
            "mode": "red-green-required",
            "commands": ["python3 -m unittest tests.test_mapper"],
            "retry_limit": 2,
        },
        "runtime_verification": [],
        "rollback": {"strategy": "revert-task-commit"},
        "review": {
            "self_review": "required",
            "spec_compliance": "required",
            "code_quality": "required",
        },
        "completion": {
            "requires": [
                "acceptance-evidence",
                "passing-tests",
                "reviewed-diff",
                "atomic-commit",
            ]
        },
    }


def full_result() -> Dict[str, Any]:
    command = "python3 -m unittest tests.test_mapper"
    return {
        "schema_version": 1,
        "task": {
            "id": "P1-T03",
            "result": "implementation_complete",
            "executor": "implementer-1",
            "starting_commit": "abc123",
        },
        "changes": {
            "files_modified": ["app/mapper.py", "tests/test_mapper.py"],
            "files_created": [],
            "files_deleted": [],
        },
        "verification": {
            "commands_run": [
                {
                    "command": command,
                    "stage": "red",
                    "type": "unit",
                    "outcome": "failed",
                    "expected_failure": True,
                },
                {
                    "command": command,
                    "stage": "green",
                    "type": "unit",
                    "outcome": "passed",
                    "expected_failure": False,
                },
                {
                    "command": command,
                    "stage": "refactor",
                    "type": "unit",
                    "outcome": "passed",
                    "expected_failure": False,
                },
            ],
            "runtime": [],
            "passed": [command],
            "failed": [],
        },
        "acceptance_evidence": {
            "AC-01": ["test_known_values", "app/mapper.py"],
            "AC-02": ["test_unknown_traceable", "app/mapper.py"],
        },
        "scope": {"unexpected_changes": [], "deviations": []},
        "risks": {"discovered": []},
        "self_review": {
            "result": "PASS",
            "checklist": {check: True for check in SELF_REVIEW_CHECKS},
            "notes": [],
        },
        "test_waiver": None,
        "review_notes": [],
    }
