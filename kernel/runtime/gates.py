"""Evidence-backed gate transitions.

Gates decide whether the lifecycle may advance, and one of them — ``release`` —
guards ``ready_to_ship -> shipped``. Until this operation existed the kernel
could *require* that gate but nothing could *satisfy* it: ``release`` was written
once at initialization and never again, so the only way to ship was to edit
``STATE.md`` by hand, which forges the very record the gate exists to produce.

This operation closes that gap without weakening the gate. A gate only reaches
an advancing state against a decision recorded in ``DECISIONS.md`` and an
evidence reference that resolves to a real file inside the project, and every
change is appended to the existing evidence ledger. It never performs the
lifecycle transition itself: passing the release gate and shipping stay two
deliberate acts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .documents import (
    DocumentError,
    load_frontmatter,
    safe_project_path,
    utc_now,
    write_frontmatter,
)
from .evidence import append_evidence_event


#: Gates the kernel knows. Mirrors the set created by ``initialize_project``.
GATE_NAMES = (
    "specification",
    "plan_quality",
    "self_review",
    "spec_compliance",
    "code_quality",
    "acceptance",
    "verification",
    "waivers",
    "release",
)

#: Gates that already have a dedicated formal writer. Accepting them here would
#: turn this command into a second way to record a review, bypassing the
#: validation those commands perform on the review document itself.
REVIEW_OWNED_GATES = {
    "spec_compliance": "validate-spec-review",
    "code_quality": "validate-quality-review",
}

#: States that let the lifecycle move forward. They cost a decision *and*
#: evidence, because they are the ones a transition guard will later trust.
ADVANCING_STATES = ("passed", "not_required")

#: States that stop the lifecycle. They cost evidence — a failure has to be
#: traceable — but not a decision: recording that something failed is an
#: observation, not an approval.
HALTING_STATES = ("failed", "blocked")

GATE_STATES = ADVANCING_STATES + HALTING_STATES

#: ``pending`` is deliberately absent as a target. It is the initial value, and
#: allowing it here would let a recorded gate be un-recorded — erasing evidence
#: through the same door that wrote it. The lifecycle already resets gates when
#: a task starts executing.
GATE_TRANSITIONS = {
    "pending": {"passed", "not_required", "failed", "blocked"},
    "passed": {"failed", "blocked"},
    "not_required": {"passed", "failed", "blocked"},
    "failed": {"passed", "blocked"},
    "blocked": {"passed", "failed"},
}

#: Gate changes describe the phase, so they are refused while the lifecycle has
#: no phase to describe.
PHASELESS_STATES = {"proposed", "discussing"}

_PHASE_EVIDENCE = re.compile(r"^\.agent/phases/(?P<slug>[^/]+)/")


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def gate_records(state: Dict[str, Any]) -> Dict[str, Any]:
    """Read the gate ledger index, tolerating states written before it existed."""

    return _mapping(state.get("gate_records"))


def _decision_recorded(root: Path, state: Dict[str, Any], decision_id: str) -> bool:
    relative = _mapping(state.get("artifacts")).get("decisions")
    if not relative:
        return False
    try:
        path = safe_project_path(root, relative)
    except DocumentError:
        return False
    if not path.is_file():
        return False
    pattern = re.compile(
        r"^#{{2,6}}\s+{}\b".format(re.escape(decision_id)), re.MULTILINE
    )
    return bool(pattern.search(path.read_text(encoding="utf-8")))


def _active_phase_slug(state: Dict[str, Any]) -> Optional[str]:
    relative = _mapping(state.get("artifacts")).get("tasks")
    if not relative:
        return None
    match = _PHASE_EVIDENCE.match(str(relative))
    return match.group("slug") if match else None


def gate_issues(
    state: Dict[str, Any],
    root: Path,
    *,
    gate: str,
    target: str,
    decision_id: Optional[str],
    evidence: Optional[str],
) -> List[str]:
    """Everything that stops the change, as operator-facing sentences."""

    issues: List[str] = []

    if gate not in GATE_NAMES:
        issues.append(
            "unknown gate {!r}; known gates: {}".format(gate, ", ".join(GATE_NAMES))
        )
    elif gate in REVIEW_OWNED_GATES:
        issues.append(
            "gate {} is owned by {}; use that operation so the review document is "
            "validated".format(gate, REVIEW_OWNED_GATES[gate])
        )

    if target not in GATE_STATES:
        issues.append(
            "invalid gate state {!r}; allowed: {}".format(
                target, ", ".join(GATE_STATES)
            )
        )

    status = state.get("status")
    if status in PHASELESS_STATES:
        issues.append(
            "gate changes describe a phase; status is {!r}".format(status)
        )

    gates = _mapping(state.get("gates"))
    if gate in GATE_NAMES and gate not in gates:
        issues.append("state has no {} gate to change".format(gate))

    current = gates.get(gate)
    if (
        gate in GATE_NAMES
        and gate in gates
        and target in GATE_STATES
        and current != target
    ):
        allowed = GATE_TRANSITIONS.get(current)
        if allowed is None:
            issues.append(
                "gate {} holds unrecognized state {!r}; refusing to guess a "
                "transition".format(gate, current)
            )
        elif target not in allowed:
            issues.append(
                "gate {} cannot move {!r} -> {!r}".format(gate, current, target)
            )

    if target in ADVANCING_STATES and not decision_id:
        issues.append("state {!r} requires a decision".format(target))
    if not evidence:
        issues.append("gate changes require an evidence reference")

    if decision_id and not _decision_recorded(root, state, decision_id):
        issues.append(
            "decision {} is not recorded in DECISIONS.md".format(decision_id)
        )

    if evidence:
        relative = str(evidence).split("#", 1)[0]
        if not relative:
            issues.append("evidence reference has no file: {!r}".format(evidence))
        else:
            try:
                path = safe_project_path(root, relative)
            except DocumentError as exc:
                issues.append(str(exc))
            else:
                if not path.is_file():
                    issues.append("evidence file is missing: {}".format(relative))
                else:
                    match = _PHASE_EVIDENCE.match(relative)
                    active = _active_phase_slug(state)
                    if match and active and match.group("slug") != active:
                        issues.append(
                            "evidence belongs to phase {!r}; the active phase is "
                            "{!r}".format(match.group("slug"), active)
                        )

    return issues


def _ledger_path(state: Dict[str, Any], root: Path) -> Path:
    relative = _mapping(state.get("artifacts")).get("evidence")
    if not relative:
        raise DocumentError("state has no evidence ledger to record the gate in")
    path = safe_project_path(root, relative)
    if not path.is_file():
        raise DocumentError("evidence ledger is missing: {}".format(relative))
    return path


def set_gate_status(
    project_root: Path,
    *,
    gate: str,
    target: str,
    decision_id: Optional[str],
    evidence: Optional[str],
    actor: str,
    note: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[str], bool]:
    """Move one gate, backed by a decision and an evidence reference.

    Returns the state, the issues that stopped it, and whether the call changed
    anything. When issues are present nothing is written. Repeating a change
    that already holds — same state, same decision, same evidence — is a
    no-op; repeating it with a different justification is refused rather than
    silently rewriting the record.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)

    issues = gate_issues(
        state,
        project_root,
        gate=gate,
        target=target,
        decision_id=decision_id,
        evidence=evidence,
    )
    if issues:
        return state, issues, False

    records = gate_records(state)
    previous = _mapping(records.get(gate))
    if state["gates"].get(gate) == target:
        same_decision = previous.get("decision") == decision_id
        same_evidence = previous.get("evidence") == evidence
        if same_decision and same_evidence:
            return state, [], False
        return (
            state,
            [
                "gate {} already holds {!r} under decision {!r} and evidence {!r}; "
                "refusing to rewrite it with a different justification".format(
                    gate,
                    target,
                    previous.get("decision"),
                    previous.get("evidence"),
                )
            ],
            False,
        )

    # The ledger is written before the state, and the order is deliberate.
    # Neither write can be made atomic with the other, so the question is which
    # half-finished outcome is safer. A ledger event without the gate change
    # describes something that did not happen, and the gate still blocks — the
    # conservative failure. The reverse would leave a gate passed with no
    # evidence trail, which is the exact outcome this command exists to prevent.
    ledger = _ledger_path(state, project_root)
    recorded_at = utc_now()
    phase_id = _mapping(state.get("phase")).get("id") or "phase"

    summary = "gate {} moved {!r} -> {!r}".format(
        gate, state["gates"].get(gate), target
    )
    if decision_id:
        summary += " under {}".format(decision_id)
    if note:
        summary += ". {}".format(note)

    append_evidence_event(
        ledger,
        {
            "schema_version": 1,
            "task_id": phase_id,
            "kind": "gate",
            "actor": actor,
            "status": target,
            "summary": summary,
            "source": evidence,
            "acceptance_criteria": [],
            "details": {
                "gate": gate,
                "from": state["gates"].get(gate),
                "to": target,
                "decision": decision_id,
                "evidence": evidence,
                "note": note,
                "phase": _mapping(state.get("phase")).get("id"),
            },
            "recorded_at": recorded_at,
        },
    )

    updated = dict(state)
    updated["gates"] = dict(state["gates"])
    updated["gates"][gate] = target
    history = list(previous.get("history", []))
    if previous.get("status"):
        history.append(
            {
                "status": previous.get("status"),
                "decision": previous.get("decision"),
                "evidence": previous.get("evidence"),
                "at": previous.get("at"),
                "by": previous.get("by"),
            }
        )
    updated["gate_records"] = dict(records)
    updated["gate_records"][gate] = {
        "status": target,
        "decision": decision_id,
        "evidence": evidence,
        "note": note,
        "at": recorded_at,
        "by": actor,
        "history": history,
    }
    updated["updated_at"] = recorded_at
    updated["updated_by"] = actor

    write_frontmatter(state_path, updated, body)
    return updated, [], True
