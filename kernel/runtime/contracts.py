"""Executable task contract and result validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .documents import (
    DocumentError,
    load_frontmatter,
    safe_project_path,
    write_frontmatter,
)
from .execution_modes import DEFAULT_EXECUTION_MODE, normalize_mode


TASK_STATUSES = {
    "pending",
    "executing",
    "implementation_complete",
    "reviewing",
    "reviewed",
    "verifying",
    "verified",
    "blocked",
    "cancelled",
}

TASK_STATUS_TRANSITIONS = {
    "pending": {"executing", "blocked", "cancelled"},
    "executing": {"implementation_complete", "blocked", "cancelled"},
    "implementation_complete": {"reviewing", "executing", "blocked", "cancelled"},
    "reviewing": {"reviewed", "executing", "blocked", "cancelled"},
    "reviewed": {"verifying", "executing", "blocked", "cancelled"},
    "verifying": {"verified", "executing", "blocked", "cancelled"},
    "blocked": {"executing", "cancelled"},
    "verified": set(),
    "cancelled": set(),
}

REQUIRED_CONTRACT_FIELDS = {
    "id",
    "title",
    "status",
    "change_type",
    "goal",
    "depends_on",
    "read_first",
    "allowed_files",
    "forbidden_changes",
    "requirements",
    "acceptance",
    "test_policy",
    "runtime_verification",
    "rollback",
    "review",
    "completion",
}

#: What a contract must state, per mode. The scope boundary — `allowed_files` —
#: and the acceptance criteria are in every row: they are the guardrails that
#: stop an agent from drifting into the wrong files or forgetting half the goal,
#: and they cost one line each. What the lighter modes drop is paperwork that
#: only pays for itself when a defect would be catastrophic.
CONTRACT_FIELDS_BY_MODE: Dict[str, set] = {
    "fast": {
        "id",
        "title",
        "status",
        "change_type",
        "goal",
        "allowed_files",
        "acceptance",
        "test_policy",
        "completion",
    },
    "standard": {
        "id",
        "title",
        "status",
        "change_type",
        "goal",
        "depends_on",
        "allowed_files",
        "acceptance",
        "test_policy",
        "rollback",
        "review",
        "completion",
    },
    "critical": set(REQUIRED_CONTRACT_FIELDS),
}

#: List-shaped fields, checked only when the mode requires them or they are
#: present anyway.
CONTRACT_LIST_FIELDS = (
    "depends_on",
    "read_first",
    "allowed_files",
    "forbidden_changes",
    "requirements",
    "acceptance",
    "runtime_verification",
)

SELF_REVIEW_CHECKS = {
    "complete_diff",
    "modified_files",
    "scope",
    "acceptance",
    "tests",
    "temporary_logs",
    "debug_code",
    "todos",
    "secrets",
    "error_behavior",
    "compatibility",
    "documentation",
}

#: The part of the self-review that catches the errors a competent model still
#: makes: wrong scope, missed acceptance, unrun tests, a secret in the diff.
CORE_SELF_REVIEW_CHECKS = {
    "complete_diff",
    "scope",
    "acceptance",
    "tests",
    "secrets",
}

GENERIC_WAIVER_REASONS = {
    "not possible to test",
    "could not test",
    "nao foi possivel testar",
    "não foi possível testar",
    "n/a",
    "none",
}


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def load_task_index(path: Path) -> Tuple[Dict[str, Any], str]:
    data, body = load_frontmatter(path)
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        raise DocumentError("{} frontmatter must contain a tasks array".format(path))
    return data, body


def load_contract(path: Path, task_id: Optional[str] = None) -> Dict[str, Any]:
    data, _ = load_frontmatter(path)
    if "tasks" in data:
        if not task_id:
            raise DocumentError("--task-id is required for a task index")
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            raise DocumentError("{} tasks must be an array".format(path))
        task = task_by_id(tasks, task_id)
        if task is None:
            raise DocumentError("{} not found in {}".format(task_id, path))
        return task
    if task_id and data.get("id") != task_id:
        raise DocumentError("{} does not contain {}".format(path, task_id))
    return data


def update_task_status(path: Path, task_id: str, target: str) -> str:
    data, body = load_task_index(path)
    task = task_by_id(data["tasks"], task_id)
    if task is None:
        raise DocumentError("{} not found in {}".format(task_id, path))
    current = task.get("status")
    if target not in TASK_STATUS_TRANSITIONS.get(current, set()):
        raise DocumentError(
            "task transition {} -> {} is forbidden".format(current, target)
        )
    task["status"] = target
    write_frontmatter(path, data, body)
    return str(current)


def restore_task_status(path: Path, task_id: str, status: str) -> None:
    """Restore an index after a failed paired STATE.md write."""
    if status not in TASK_STATUSES:
        raise DocumentError("cannot restore invalid task status {}".format(status))
    data, body = load_task_index(path)
    task = task_by_id(data["tasks"], task_id)
    if task is None:
        raise DocumentError("{} not found in {}".format(task_id, path))
    task["status"] = status
    write_frontmatter(path, data, body)


def load_test_policy(framework_root: Path) -> Dict[str, Any]:
    path = framework_root / "kernel" / "test-policy.yaml"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentError("cannot load central test policy: {}".format(exc)) from exc
    if data.get("schema_version") != 1:
        raise DocumentError("unsupported test policy schema")
    return data


def task_by_id(tasks: Iterable[Dict[str, Any]], task_id: str) -> Optional[Dict[str, Any]]:
    for task in tasks:
        if isinstance(task, dict) and task.get("id") == task_id:
            return task
    return None


def task_execution_mode(task: Dict[str, Any]) -> Optional[str]:
    """The mode a task declares for itself, if any."""

    declared = task.get("execution_mode")
    if declared is None:
        return None
    if not isinstance(declared, str):
        raise DocumentError(
            "task {} has a non-text execution_mode".format(task.get("id", "<unknown>"))
        )
    return normalize_mode(declared, default=DEFAULT_EXECUTION_MODE)


def phase_default_execution_mode(index: Dict[str, Any]) -> Optional[str]:
    """The default mode a phase index declares for its tasks, if any."""

    declared = index.get("default_execution_mode")
    if declared is None:
        return None
    if not isinstance(declared, str):
        raise DocumentError("phase default_execution_mode must be text")
    return normalize_mode(declared, default=DEFAULT_EXECUTION_MODE)


def validate_task_shape(task: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for field in ("id", "title", "status"):
        if not isinstance(task.get(field), str) or not task.get(field):
            issues.append("task missing non-empty {}".format(field))
    if task.get("status") not in TASK_STATUSES:
        issues.append("task {} has invalid status".format(task.get("id", "<unknown>")))
    if not isinstance(task.get("depends_on", []), list):
        issues.append("task {} depends_on must be an array".format(task.get("id", "<unknown>")))
    try:
        task_execution_mode(task)
    except (DocumentError, ValueError) as exc:
        issues.append(str(exc))
    return issues


def _review_issues(
    contract: Dict[str, Any], mode: str
) -> List[Dict[str, str]]:
    """How many judgements a contract has to promise, per mode."""

    review = contract.get("review", {})
    if mode == "fast":
        if "review" in contract and not isinstance(review, dict):
            return [_issue("review-policy", "review must be an object when present")]
        return []
    if not isinstance(review, dict):
        return [_issue("review-policy", "review must be an object")]
    if mode == "critical":
        if any(
            review.get(name) != "required"
            for name in ("self_review", "spec_compliance", "code_quality")
        ):
            return [_issue("review-policy", "all three reviews must be marked required")]
        return []

    issues: List[Dict[str, str]] = []
    if review.get("self_review") != "required":
        issues.append(_issue("review-policy", "self_review must be required"))
    independent = [
        review.get(name) for name in ("spec_compliance", "code_quality")
    ]
    if not any(value in {"required", "integrated"} for value in independent):
        issues.append(
            _issue(
                "review-policy",
                "standard requires one review beyond the self-review: mark "
                "spec_compliance or code_quality as required or integrated",
            )
        )
    return issues


def validate_task_contract(
    contract: Dict[str, Any],
    policy: Dict[str, Any],
    *,
    project_root: Optional[Path] = None,
    mode: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Validate a contract against the obligations of its execution mode.

    ``mode`` defaults to the contract's own declaration and then to ``critical``,
    so a contract written before modes were per-task is held to exactly the rules
    it was written under.
    """

    issues: List[Dict[str, str]] = []
    try:
        declared = task_execution_mode(contract)
    except (DocumentError, ValueError) as exc:
        issues.append(_issue("contract-shape", str(exc)))
        declared = None
    selected = normalize_mode(mode or declared or "critical", default="critical")
    if selected == "auto":
        selected = "critical"

    for field in sorted(CONTRACT_FIELDS_BY_MODE[selected] - set(contract)):
        issues.append(_issue("contract-field", "missing contract field {}".format(field)))
    for message in validate_task_shape(contract):
        issues.append(_issue("contract-shape", message))

    change_type = contract.get("change_type")
    change_policy = policy.get(change_type)
    if not isinstance(change_policy, dict):
        issues.append(
            _issue("change-type", "unknown change_type {!r}".format(change_type))
        )
    else:
        test_policy = contract.get("test_policy", {})
        if not isinstance(test_policy, dict):
            issues.append(_issue("test-policy", "test_policy must be an object"))
        elif test_policy.get("mode") != change_policy.get("default"):
            override = test_policy.get("override")
            if not (
                isinstance(override, dict)
                and override.get("reason")
                and override.get("approved_by")
            ):
                issues.append(
                    _issue(
                        "test-policy-mode",
                        "{} requires mode {}, got {}".format(
                            change_type,
                            change_policy.get("default"),
                            test_policy.get("mode"),
                        ),
                    )
                )

    goal = contract.get("goal")
    if not isinstance(goal, dict) or not goal.get("description"):
        issues.append(_issue("goal", "goal.description is required"))

    for field in CONTRACT_LIST_FIELDS:
        if field not in contract and field not in CONTRACT_FIELDS_BY_MODE[selected]:
            continue
        if not isinstance(contract.get(field), list):
            issues.append(_issue("contract-list", "{} must be an array".format(field)))

    acceptance = contract.get("acceptance", [])
    acceptance_ids = []
    if isinstance(acceptance, list):
        for item in acceptance:
            if not isinstance(item, dict) or not item.get("id") or not item.get("criterion"):
                issues.append(
                    _issue(
                        "acceptance-shape",
                        "each acceptance item requires id and criterion",
                    )
                )
                continue
            if item["id"] in acceptance_ids:
                issues.append(
                    _issue("acceptance-duplicate", "duplicate {}".format(item["id"]))
                )
            acceptance_ids.append(item["id"])
        if not acceptance:
            issues.append(_issue("acceptance-empty", "at least one criterion is required"))

    allowed = contract.get("allowed_files", [])
    if isinstance(allowed, list) and not allowed:
        issues.append(_issue("scope-empty", "allowed_files cannot be empty"))

    if project_root is not None:
        for field in ("read_first", "allowed_files"):
            values = contract.get(field, [])
            if not isinstance(values, list):
                continue
            for relative in values:
                if not isinstance(relative, str):
                    issues.append(_issue("path-type", "{} path must be text".format(field)))
                    continue
                try:
                    path = safe_project_path(project_root, relative)
                except DocumentError as exc:
                    issues.append(_issue("unsafe-path", str(exc)))
                    continue
                if field == "read_first" and not path.is_file():
                    issues.append(
                        _issue("read-first-missing", "{} does not exist".format(relative))
                    )

    issues.extend(_review_issues(contract, selected))

    if "rollback" in CONTRACT_FIELDS_BY_MODE[selected] or "rollback" in contract:
        rollback = contract.get("rollback", {})
        if not isinstance(rollback, dict) or not rollback.get("strategy"):
            issues.append(_issue("rollback", "rollback.strategy is required"))
    return issues


def dependency_issues(task: Dict[str, Any], tasks: List[Dict[str, Any]]) -> List[str]:
    issues: List[str] = []
    for dependency_id in task.get("depends_on", []):
        dependency = task_by_id(tasks, dependency_id)
        if dependency is None:
            issues.append(
                "task {} references missing dependency {}".format(task.get("id"), dependency_id)
            )
        elif dependency.get("status") != "verified":
            issues.append(
                "dependency {} is {}, expected verified".format(
                    dependency_id, dependency.get("status")
                )
            )
    return issues


def eligible_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    eligible: List[Dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict) or task.get("status") != "pending":
            continue
        if not dependency_issues(task, tasks):
            eligible.append(task)
    return eligible


def task_graph_issues(tasks: List[Dict[str, Any]]) -> List[str]:
    issues: List[str] = []
    identifiers: List[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            issues.append("task entry must be an object")
            continue
        issues.extend(validate_task_shape(task))
        task_id = task.get("id")
        if isinstance(task_id, str):
            if task_id in identifiers:
                issues.append("duplicate task id {}".format(task_id))
            identifiers.append(task_id)

    known = set(identifiers)
    graph: Dict[str, List[str]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            continue
        dependencies = task.get("depends_on", [])
        if isinstance(dependencies, list):
            graph[task["id"]] = [item for item in dependencies if isinstance(item, str)]
            for dependency in graph[task["id"]]:
                if dependency not in known:
                    issues.append(
                        "task {} references missing dependency {}".format(
                            task["id"], dependency
                        )
                    )

    visiting = set()
    visited = set()

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            issues.append("task dependency cycle includes {}".format(task_id))
            return
        visiting.add(task_id)
        for dependency in graph.get(task_id, []):
            if dependency in graph:
                visit(dependency)
        visiting.remove(task_id)
        visited.add(task_id)

    for identifier in graph:
        visit(identifier)

    parallel_groups: Dict[str, List[Dict[str, Any]]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        execution = task.get("execution", {})
        group = execution.get("parallel_group") if isinstance(execution, dict) else None
        if group:
            parallel_groups.setdefault(str(group), []).append(task)
    for group, grouped_tasks in parallel_groups.items():
        for index, task in enumerate(grouped_tasks):
            task_files = set(task.get("allowed_files", []))
            for other in grouped_tasks[index + 1 :]:
                conflicts = sorted(task_files.intersection(other.get("allowed_files", [])))
                if conflicts:
                    issues.append(
                        "parallel group {} has file conflict between {} and {}: {}".format(
                            group,
                            task.get("id"),
                            other.get("id"),
                            ", ".join(conflicts),
                        )
                    )
    return issues


def validate_test_waiver(waiver: Any) -> List[Dict[str, str]]:
    if not isinstance(waiver, dict):
        return [_issue("waiver-missing", "test waiver must be an object")]
    issues: List[Dict[str, str]] = []
    reason = str(waiver.get("reason", "")).strip()
    if not reason or reason.lower() in GENERIC_WAIVER_REASONS or len(reason) < 12:
        issues.append(_issue("waiver-reason", "waiver reason must be specific"))
    if not waiver.get("approved_by"):
        issues.append(_issue("waiver-approval", "waiver approved_by is required"))
    evidence = waiver.get("alternative_evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append(
            _issue(
                "waiver-evidence",
                "waiver requires non-empty alternative_evidence",
            )
        )
    return issues


def _command_records(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    verification = result.get("verification", {})
    if not isinstance(verification, dict):
        return []
    records = verification.get("commands_run", [])
    return [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []


def _passed_record(records: List[Dict[str, Any]], *, stage: Optional[str] = None, test_type: Optional[str] = None) -> bool:
    for record in records:
        if stage is not None and record.get("stage") != stage:
            continue
        if test_type is not None and record.get("type") != test_type:
            continue
        if record.get("outcome") == "passed":
            return True
    return False


def _validate_test_execution(
    contract: Dict[str, Any],
    result: Dict[str, Any],
    policy: Dict[str, Any],
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    change_policy = policy.get(contract.get("change_type"), {})
    mode = contract.get("test_policy", {}).get("mode")
    records = _command_records(result)
    waiver = result.get("test_waiver")

    if waiver is not None:
        issues.extend(validate_test_waiver(waiver))
        return issues
    if mode == "test-exempt":
        return issues

    required_commands = contract.get("test_policy", {}).get("commands", [])
    recorded_commands = {
        item.get("command")
        for item in records
        if item.get("outcome") in {"passed", "failed"}
    }
    for command in required_commands if isinstance(required_commands, list) else []:
        if command not in recorded_commands:
            issues.append(
                _issue("test-command-missing", "required command not run: {}".format(command))
            )

    if mode in {"red-green-required", "regression-first-required"}:
        red = [
            item
            for item in records
            if item.get("stage") == "red"
            and item.get("outcome") == "failed"
            and item.get("expected_failure") is True
        ]
        if not red:
            issues.append(_issue("red-missing", "expected RED failure was not recorded"))
        for stage in ("green", "refactor"):
            if not _passed_record(records, stage=stage):
                issues.append(
                    _issue(
                        "{}-missing".format(stage),
                        "{} passing run was not recorded".format(stage),
                    )
                )
    elif mode == "characterization-first":
        for stage in ("characterize", "change", "verify-difference"):
            if not _passed_record(records, stage=stage):
                issues.append(
                    _issue("trace-missing", "missing passing {} stage".format(stage))
                )
    elif mode == "forward-and-rollback-required":
        for stage in ("precheck", "forward", "validate", "rollback-or-recovery"):
            if not _passed_record(records, stage=stage):
                issues.append(
                    _issue("migration-trace", "missing passing {} stage".format(stage))
                )
    else:
        required_types = change_policy.get("required_types", [])
        for test_type in required_types:
            if not _passed_record(records, test_type=test_type):
                issues.append(
                    _issue(
                        "test-type-missing",
                        "missing passing {} verification".format(test_type),
                    )
                )
        required_any = change_policy.get("required_types_any", [])
        if required_any and not any(
            _passed_record(records, test_type=test_type) for test_type in required_any
        ):
            issues.append(
                _issue(
                    "test-type-any-missing",
                    "one of {} must pass".format(", ".join(required_any)),
                )
            )
    return issues


def validate_execution_result(
    contract: Dict[str, Any],
    result: Dict[str, Any],
    policy: Dict[str, Any],
    *,
    mode: Optional[str] = None,
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    try:
        declared = task_execution_mode(contract)
    except (DocumentError, ValueError):
        declared = None
    selected = normalize_mode(mode or declared or "critical", default="critical")
    if selected == "auto":
        selected = "critical"
    task_result = result.get("task", {})
    if not isinstance(task_result, dict) or task_result.get("id") != contract.get("id"):
        issues.append(_issue("result-task", "result task id must match contract"))
    if not isinstance(task_result, dict) or task_result.get("result") != "implementation_complete":
        issues.append(
            _issue(
                "executor-authority",
                "executor result must be implementation_complete, never reviewed or verified",
            )
        )
    if not isinstance(task_result, dict) or not task_result.get("executor"):
        issues.append(_issue("executor-id", "task.executor is required"))

    changes = result.get("changes", {})
    allowed = set(contract.get("allowed_files", []))
    changed_paths: List[str] = []
    if not isinstance(changes, dict):
        issues.append(_issue("changes", "changes must be an object"))
    else:
        for field in ("files_modified", "files_created", "files_deleted"):
            values = changes.get(field, [])
            if not isinstance(values, list):
                issues.append(_issue("changes-list", "{} must be an array".format(field)))
                continue
            changed_paths.extend(item for item in values if isinstance(item, str))
    for path in changed_paths:
        if path not in allowed:
            issues.append(
                _issue("file-out-of-scope", "{} is outside allowed_files".format(path))
            )

    scope = result.get("scope", {})
    if not isinstance(scope, dict):
        issues.append(_issue("scope", "scope must be an object"))
    else:
        for field in ("unexpected_changes", "deviations"):
            values = scope.get(field, [])
            if not isinstance(values, list):
                issues.append(_issue("scope-list", "{} must be an array".format(field)))
            elif values:
                issues.append(
                    _issue(
                        "scope-deviation",
                        "{} requires plan or contract revision".format(field),
                    )
                )

    evidence = result.get("acceptance_evidence", {})
    if not isinstance(evidence, dict):
        issues.append(_issue("acceptance-evidence", "acceptance_evidence must be an object"))
        evidence = {}
    for criterion in contract.get("acceptance", []):
        criterion_id = criterion.get("id") if isinstance(criterion, dict) else None
        if criterion_id and (
            not isinstance(evidence.get(criterion_id), list)
            or not evidence.get(criterion_id)
        ):
            issues.append(
                _issue(
                    "acceptance-evidence-missing",
                    "{} has no evidence".format(criterion_id),
                )
            )

    self_review = result.get("self_review", {})
    if not isinstance(self_review, dict) or self_review.get("result") != "PASS":
        issues.append(_issue("self-review", "self_review.result must be PASS"))
    checklist = self_review.get("checklist", {}) if isinstance(self_review, dict) else {}
    if not isinstance(checklist, dict):
        issues.append(_issue("self-review-checklist", "self-review checklist is required"))
    else:
        required_checks = (
            SELF_REVIEW_CHECKS if selected != "fast" else CORE_SELF_REVIEW_CHECKS
        )
        for check in sorted(required_checks):
            if checklist.get(check) is not True:
                issues.append(
                    _issue(
                        "self-review-check",
                        "self-review check {} must be true".format(check),
                    )
                )

    issues.extend(_validate_test_execution(contract, result, policy))

    runtime = result.get("verification", {}).get("runtime", [])
    for required in contract.get("runtime_verification", []):
        if required not in runtime:
            issues.append(
                _issue(
                    "runtime-verification",
                    "missing runtime verification {}".format(required),
                )
            )
    return issues
