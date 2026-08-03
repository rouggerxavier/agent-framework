"""Record a change of execution-mode classification, with its justification.

A classification can be wrong in two directions, and the two are not symmetric.
Discovering that a task can break authentication for everyone has to be able to
raise it to `critical` mid-flight; discovering that a ten-file frontend task was
never critical has to be able to lower it without a ceremony that costs more
than the correction. So escalation is paid for with a *named* grave-damage path
— the same vocabulary the classifier uses — and reduction is paid for with a
plain reason.

The record lives in ``STATE.md``, never in ``TASKS.md``. A task's classification
is not part of the contract the plan seal froze: rewriting the sealed index to
correct a label would either break the fingerprint or demand a full re-seal,
which would put the heaviest operation in the kernel in front of the one that
exists to remove weight. Nothing here rewrites a review, an evidence entry, or a
gate: it changes what the *next* steps owe, and says who decided that and why.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .contracts import load_task_index, task_by_id
from .documents import (
    DocumentError,
    load_frontmatter,
    safe_project_path,
    utc_now,
    write_frontmatter,
)
from .evidence import append_evidence_event
from .execution_modes import (
    is_persistent_state,
    reclassify_execution_mode,
    state_execution_mode,
)
from .state_machine import effective_task_mode, validate_state


SCOPES = ("task", "project")


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _issue(code: str, message: str) -> Dict[str, str]:
    return {"code": code, "message": message}


def _current_mode(
    state: Dict[str, Any], root: Path, *, scope: str, task_id: Optional[str]
) -> str:
    if scope == "project":
        return state_execution_mode(state)
    return effective_task_mode(state, root, task_id=task_id)


def _task_exists(state: Dict[str, Any], root: Path, task_id: str) -> bool:
    relative = _mapping(state.get("artifacts")).get("tasks")
    if not relative:
        return False
    try:
        path = safe_project_path(root, relative)
    except DocumentError:
        return False
    if not path.is_file():
        return False
    try:
        index, _ = load_task_index(path)
    except DocumentError:
        return False
    return task_by_id(index.get("tasks", []), task_id) is not None


def set_execution_mode(
    project_root: Path,
    *,
    scope: str,
    mode: str,
    reason: str,
    actor: str,
    task_id: Optional[str] = None,
    severe_harm_factors: Sequence[str] = (),
    evidence: Optional[str] = None,
    write: bool = True,
) -> Tuple[Dict[str, Any], List[Dict[str, str]], bool]:
    """Reclassify one task, or the project default, and record why.

    Returns the state, the issues that stopped the change, and whether anything
    was written. Nothing is written when issues are present, and a repeat of a
    classification that already holds is a no-op rather than a second record.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    if not state_path.is_file():
        return {}, [_issue("mode-state", "no .agent/STATE.md to classify against")], False

    state, body = load_frontmatter(state_path)
    issues: List[Dict[str, str]] = []

    if scope not in SCOPES:
        return (
            state,
            [
                _issue(
                    "mode-scope",
                    "unknown scope {!r}; allowed: {}".format(scope, ", ".join(SCOPES)),
                )
            ],
            False,
        )
    if scope == "task" and not task_id:
        return state, [_issue("mode-task", "reclassifying a task requires --task-id")], False
    if scope == "task" and not _task_exists(state, project_root, str(task_id)):
        return (
            state,
            [
                _issue(
                    "mode-task",
                    "task {} is not in the active phase index".format(task_id),
                )
            ],
            False,
        )

    try:
        current = _current_mode(state, project_root, scope=scope, task_id=task_id)
    except ValueError as exc:
        return state, [_issue("mode-state", str(exc))], False

    verdict = reclassify_execution_mode(
        current,
        mode,
        justification=reason,
        severe_harm_factors=severe_harm_factors,
    )
    issues.extend(_issue("mode-justification", message) for message in verdict["issues"])
    if verdict["direction"] == "unchanged":
        # Not an error: asking for the classification that already holds is a
        # no-op, the same way re-applying a landed review is.
        return state, issues, False
    if scope == "project" and verdict["to"] == "critical" and not is_persistent_state(state):
        issues.append(
            _issue(
                "mode-state",
                "a critical default needs the persistent kernel; this project holds "
                "the resume-only state",
            )
        )
    if write and not actor:
        issues.append(_issue("mode-actor", "recording a classification requires an actor"))
    if issues:
        return state, issues, False
    if not write:
        return state, [], False

    recorded_at = utc_now()
    updated = deepcopy(state)
    entry = {
        "mode": verdict["to"],
        "previous": verdict["from"],
        "direction": verdict["direction"],
        "reason": verdict["justification"],
        "severe_harm_factors": verdict["severe_harm_factors"],
        "evidence": evidence,
        "at": recorded_at,
        "by": actor,
    }

    if scope == "task":
        overrides = deepcopy(_mapping(updated.get("task_modes")))
        previous_record = _mapping(overrides.get(str(task_id)))
        history = list(previous_record.get("history", []))
        if previous_record.get("mode"):
            history.append(
                {
                    key: previous_record.get(key)
                    for key in (
                        "mode",
                        "previous",
                        "reason",
                        "severe_harm_factors",
                        "at",
                        "by",
                    )
                }
            )
        overrides[str(task_id)] = dict(entry, history=history)
        updated["task_modes"] = overrides
    else:
        history = list(_mapping(updated.get("execution_mode_record")).get("history", []))
        previous_record = _mapping(updated.get("execution_mode_record"))
        if previous_record.get("mode"):
            history.append(
                {
                    key: previous_record.get(key)
                    for key in ("mode", "previous", "reason", "at", "by")
                }
            )
        updated["execution_mode"] = verdict["to"]
        updated["execution_mode_record"] = dict(entry, history=history)

    updated["updated_at"] = recorded_at
    updated["updated_by"] = actor

    residual = [
        item["message"]
        for item in validate_state(updated, project_root)
        if item["severity"] == "error"
    ]
    if residual:
        return (
            state,
            [
                _issue(
                    "mode-result-state",
                    "the reclassification would produce an invalid state: {}".format(
                        "; ".join(residual)
                    ),
                )
            ],
            False,
        )

    # The ledger first, for the same reason every other writer here does it: a
    # ledger event without the state change describes something that did not
    # take effect and repeating the command completes it, while a changed
    # classification with no trail is the record this operation exists to write.
    ledger_relative = _mapping(state.get("artifacts")).get("evidence")
    ledger_path = None
    ledger_before = b""
    if ledger_relative:
        candidate = safe_project_path(project_root, ledger_relative)
        if candidate.is_file():
            ledger_path = candidate
            ledger_before = candidate.read_bytes()

    state_before = state_path.read_bytes()
    try:
        if ledger_path is not None:
            append_evidence_event(
                ledger_path,
                {
                    "schema_version": 1,
                    "task_id": (
                        task_id
                        if scope == "task"
                        else _mapping(state.get("phase")).get("id") or "project"
                    ),
                    "kind": "classification",
                    "actor": actor,
                    "status": verdict["to"],
                    "summary": "{} classification {} -> {}: {}".format(
                        "Task {}".format(task_id) if scope == "task" else "Project default",
                        verdict["from"],
                        verdict["to"],
                        verdict["justification"],
                    ),
                    # A classification is justified by its recorded reason; an
                    # extra evidence file is welcome and not demanded.
                    "source": evidence or ".agent/STATE.md",
                    "acceptance_criteria": [],
                    "details": dict(entry, scope=scope, task_id=task_id),
                    "recorded_at": recorded_at,
                },
            )
        write_frontmatter(state_path, updated, body)
    except Exception:
        if ledger_path is not None:
            ledger_path.write_bytes(ledger_before)
        state_path.write_bytes(state_before)
        raise

    return updated, [], True
