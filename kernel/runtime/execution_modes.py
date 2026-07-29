"""Adaptive execution policy for routing, review, and verification.

The policy is intentionally side-effect free. Routing a request must never create
``.agent/`` or instantiate persistent artifacts.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


EXECUTION_MODES = ("fast", "standard", "critical")
REQUESTED_MODES = ("auto",) + EXECUTION_MODES
LEGACY_MODE_ALIASES = {
    "quick": "standard",
    "full": "critical",
    "audit": "critical",
}

VERIFICATION_BUDGETS: Dict[str, Dict[str, Any]] = {
    "fast": {"target_ratio": 0.20, "max_full_review_passes": 1},
    "standard": {"target_ratio": 0.30, "max_full_review_passes": 1},
    "critical": {"target_ratio": None, "max_full_review_passes": "proportional"},
}

MODE_POLICIES: Dict[str, Dict[str, Any]] = {
    "fast": {
        "persistent_state": False,
        "formal_spec": False,
        "task_contract": False,
        "plan_seal": False,
        "evidence_ledger": False,
        "independent_reviews": False,
        "worktree": False,
        "review_strategy": "integrated",
        "verification_scope": "targeted",
    },
    "standard": {
        "persistent_state": "optional",
        "formal_spec": "lightweight",
        "task_contract": "optional",
        "plan_seal": False,
        "evidence_ledger": "lightweight-or-none",
        "independent_reviews": False,
        "worktree": "conditional",
        "review_strategy": "integrated",
        "verification_scope": "proportional",
    },
    "critical": {
        "persistent_state": True,
        "formal_spec": True,
        "task_contract": True,
        "plan_seal": True,
        "evidence_ledger": True,
        "independent_reviews": True,
        "worktree": "proportional",
        "review_strategy": "split",
        "verification_scope": "complete",
    },
}

ASSETS_BY_MODE = {
    "fast": [
        "skills/diff-reviewer/SKILL.md",
    ],
    "standard": [
        "skills/workflow-planner/SKILL.md",
        "skills/test-strategy-builder/SKILL.md",
        "skills/goal-coverage-verifier/SKILL.md",
    ],
    "critical": [
        "skills/framework-next/SKILL.md",
        "skills/workflow-planner/SKILL.md",
        "skills/workflow-runner/SKILL.md",
        "skills/code-review-gate/SKILL.md",
    ],
}

SKIPPED_BY_MODE = {
    "fast": [
        ".agent/",
        "formal spec",
        "task contracts",
        "plan seal",
        "evidence ledger",
        "independent split reviews",
        "worktree",
    ],
    "standard": [
        "plan seal",
        "full evidence ledger",
        "independent split reviews",
        "automatic worktree",
    ],
    "critical": [],
}


def _normalized_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def _signals(
    text: str, patterns: Iterable[Tuple[str, str]]
) -> List[str]:
    return [
        name
        for name, pattern in patterns
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


CRITICAL_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("authentication_or_authorization", r"\b(auth|authentication|authorization|autenticacao|autorizacao)\b"),
    ("payment_or_financial", r"\b(payment|payments|billing|finance|financial|pagamento|pagamentos|financeiro)\b"),
    ("migration_or_backfill", r"\b(migration|migracao|migrate|backfill)\b"),
    ("destructive_change", r"\b(destructive|destrutiv[ao]|irreversible|irreversivel|data loss|perda de dados)\b"),
    ("security_sensitive", r"\b(security model|security boundary|permission model|secrets? rotation|modelo de seguranca|limite de seguranca)\b"),
    ("data_synchronization", r"\b(data sync|data synchronization|sincronizacao de dados)\b"),
    ("critical_external_integration", r"\b(critical integration|integracao critica|external financial integration|integracao financeira externa)\b"),
    ("sensitive_external_contract", r"\b(sensitive external contract|contrato externo sensivel)\b"),
    ("multiple_agents", r"\b(multiple agents|multi-agent|multiplos agentes)\b"),
    ("long_running_task", r"\b(long[- ]running task|long task|tarefa longa)\b"),
    ("complex_rollback", r"\b(complex rollback|rollback complexo)\b"),
    ("high_operational_impact", r"\b(high operational impact|alto impacto operacional)\b"),
)

GRAVE_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("authentication_or_authorization", r"\b(auth|authentication|authorization|autenticacao|autorizacao)\b"),
    ("destructive_migration", r"\b(destructive migration|migration destrutiva|migracao destrutiva|destructive backfill)\b"),
    ("data_loss_or_corruption", r"\b(data loss|data corruption|perda de dados|corrupcao de dados)\b"),
    ("security_sensitive", r"\b(security model|security boundary|permission model|secrets? rotation|modelo de seguranca|limite de seguranca)\b"),
)

STANDARD_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("cross_session_work", r"\b(cross[- ]session|multiple sessions|varias sessoes|atravessar sessoes|retomada)\b"),
    ("dependent_steps", r"\b(dependent steps|etapas dependentes|multi[- ]step|multiplas etapas)\b"),
    ("distributed_feature", r"\b(distributed feature|feature distribuida|multiple modules|varios modulos)\b"),
    ("moderate_refactor", r"\b(moderate refactor|refatoracao moderada)\b"),
    ("new_endpoint_or_route", r"\b(new|novo|nova)\b.{0,30}\b(endpoint|route|rota)\b"),
    ("moderate_regression_risk", r"\b(moderate regression|risco moderado de regressao)\b"),
)


def normalize_mode(value: Optional[str], *, default: str = "auto") -> str:
    candidate = (value or default).strip().casefold()
    if candidate.startswith("--"):
        candidate = candidate[2:]
    candidate = LEGACY_MODE_ALIASES.get(candidate, candidate)
    if candidate not in REQUESTED_MODES:
        raise ValueError("invalid execution mode: {!r}".format(value))
    return candidate


def requested_mode_from_text(request: str, explicit: Optional[str] = None) -> str:
    if explicit is not None:
        return normalize_mode(explicit)
    flags = re.findall(r"(?<!\w)--(fast|standard|critical|auto)\b", request.casefold())
    if len(set(flags)) > 1:
        raise ValueError("request contains conflicting execution mode flags")
    return normalize_mode(flags[0] if flags else "auto")


def should_create_persistent_state(
    mode: str,
    *,
    crosses_sessions: bool = False,
    dependent_tasks: bool = False,
    user_requested: bool = False,
) -> bool:
    selected = normalize_mode(mode, default="fast")
    if selected == "auto":
        raise ValueError("persistence requires a selected execution mode")
    if selected == "critical":
        return True
    if selected == "fast":
        return False
    return crosses_sessions or dependent_tasks or user_requested


def route_execution(
    request: str,
    *,
    requested_mode: Optional[str] = None,
    persistence_requested: bool = False,
) -> Dict[str, Any]:
    """Select a mode from concrete signals, preferring fast when evidence is absent."""

    clean = _normalized_text(request)
    explicit = requested_mode_from_text(request, requested_mode)
    risk_factors = _signals(clean, CRITICAL_PATTERNS)
    grave_factors = _signals(clean, GRAVE_PATTERNS)
    complexity_factors = _signals(clean, STANDARD_PATTERNS)

    escalated = False
    if explicit == "critical":
        selected = "critical"
        reason = "User explicitly selected critical mode."
    elif explicit in {"fast", "standard"}:
        if grave_factors:
            selected = "critical"
            escalated = True
            reason = (
                "Escalated from explicit {} because of grave security or data-loss risk: {}."
                .format(explicit, ", ".join(grave_factors))
            )
        else:
            selected = explicit
            reason = "User explicitly selected {} mode.".format(explicit)
    elif risk_factors:
        selected = "critical"
        reason = "Concrete critical risk detected: {}.".format(", ".join(risk_factors))
    elif complexity_factors:
        selected = "standard"
        reason = "Concrete moderate complexity detected: {}.".format(
            ", ".join(complexity_factors)
        )
    else:
        selected = "fast"
        reason = "No concrete critical risk or moderate complexity was detected; defaulting to fast."

    policy = deepcopy(MODE_POLICIES[selected])
    policy["verification_budget"] = deepcopy(VERIFICATION_BUDGETS[selected])
    policy["create_persistent_state"] = should_create_persistent_state(
        selected,
        crosses_sessions="cross_session_work" in complexity_factors,
        dependent_tasks="dependent_steps" in complexity_factors,
        user_requested=persistence_requested,
    )

    return {
        "selected_mode": selected,
        "reason": reason,
        "risk_factors": risk_factors,
        "complexity_factors": complexity_factors,
        "assets_selected": list(ASSETS_BY_MODE[selected]),
        "assets_skipped": list(SKIPPED_BY_MODE[selected]),
        "requested_mode": explicit,
        "escalated": escalated,
        "policy": policy,
    }


def review_policy(mode: str, *, localized_correction: bool = False) -> Dict[str, Any]:
    selected = normalize_mode(mode, default="fast")
    if selected == "auto":
        raise ValueError("review policy requires a selected execution mode")
    return {
        "review_mode": "split" if selected == "critical" else "integrated",
        "depth": {"fast": "light", "standard": "normal", "critical": "deep"}[selected],
        "blocking_threshold": "BLOCKER",
        "scope": "affected-diff-and-criteria" if localized_correction else "full-current-diff",
        "independent_reviews": selected == "critical",
    }


def verification_budget_exceeded(
    mode: str,
    *,
    implementation_effort: float,
    verification_effort: float,
    full_review_passes: int,
    concrete_risk_remaining: bool = False,
) -> bool:
    selected = normalize_mode(mode, default="fast")
    if selected == "auto":
        raise ValueError("verification budget requires a selected execution mode")
    if selected == "critical" or concrete_risk_remaining:
        return False
    budget = VERIFICATION_BUDGETS[selected]
    if full_review_passes > int(budget["max_full_review_passes"]):
        return True
    if implementation_effort <= 0:
        return verification_effort > 0
    return verification_effort / implementation_effort > float(budget["target_ratio"])


def classify_review_finding(
    requested_classification: str,
    *,
    reachability: str = "",
    likelihood: str = "",
    impact: str = "",
    supporting_evidence: Sequence[str] = (),
    explicit_requirement: bool = False,
    security_risk: bool = False,
    data_loss_risk: bool = False,
    reproducible_regression: bool = False,
    operational_impact: bool = False,
    acceptance_failure: bool = False,
) -> str:
    requested = requested_classification.strip().upper()
    if requested not in {"BLOCKER", "IMPORTANT", "NOTE", "SPECULATIVE"}:
        raise ValueError("invalid finding classification: {!r}".format(requested))

    evidence_complete = all(
        (
            reachability.strip(),
            likelihood.strip(),
            impact.strip(),
            list(supporting_evidence),
        )
    )
    blocker_basis = any(
        (
            explicit_requirement,
            security_risk,
            data_loss_risk,
            reproducible_regression,
            operational_impact,
            acceptance_failure,
        )
    )
    theoretical = likelihood.strip().casefold() in {
        "",
        "theoretical",
        "speculative",
        "unknown",
        "teorica",
        "especulativa",
        "desconhecida",
    }

    if requested == "BLOCKER":
        if evidence_complete and blocker_basis and not theoretical:
            return "BLOCKER"
        return "SPECULATIVE"
    if requested == "IMPORTANT":
        return "IMPORTANT" if evidence_complete and not theoretical else "SPECULATIVE"
    return requested


def finding_blocks_delivery(classification: str) -> bool:
    return classification.strip().upper() == "BLOCKER"


def should_reground(
    *,
    commit_changed_materially: bool = False,
    scope_changed: bool = False,
    core_files_discovered: bool = False,
    context_stale: bool = False,
    contradiction_found: bool = False,
) -> bool:
    return any(
        (
            commit_changed_materially,
            scope_changed,
            core_files_discovered,
            context_stale,
            contradiction_found,
        )
    )


def build_review_package(
    *,
    goal: str,
    mode: str,
    diff: str,
    files_changed: Sequence[str],
    tests_run: Sequence[Mapping[str, Any]],
    acceptance_or_expected_behavior: Sequence[str],
    known_risks: Sequence[str],
) -> Dict[str, Any]:
    selected = normalize_mode(mode, default="fast")
    if selected == "auto":
        raise ValueError("review package requires a selected execution mode")
    return {
        "goal": goal,
        "mode": selected,
        "diff": diff,
        "files_changed": list(files_changed),
        "tests_run": [dict(item) for item in tests_run],
        "acceptance_or_expected_behavior": list(acceptance_or_expected_behavior),
        "known_risks": list(known_risks),
    }


def state_execution_mode(state: Mapping[str, Any]) -> str:
    explicit = state.get("execution_mode")
    if explicit is not None and not isinstance(explicit, str):
        raise ValueError("execution_mode must be fast, standard, or critical")
    if isinstance(explicit, str):
        normalized = normalize_mode(explicit, default="critical")
        if normalized == "auto":
            raise ValueError("persisted execution_mode cannot be auto")
        return normalized
    # States created before adaptive execution used the complete P0/P1 kernel.
    return "critical"


def migrate_state_execution_mode(
    state: Mapping[str, Any],
) -> Tuple[Dict[str, Any], bool]:
    migrated = deepcopy(dict(state))
    if "execution_mode" in migrated:
        return migrated, False
    migrated["execution_mode"] = state_execution_mode(migrated)
    return migrated, True


def validate_lightweight_state(
    state: Mapping[str, Any], project_root: Path
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    def issue(code: str, message: str) -> None:
        issues.append({"code": code, "message": message, "severity": "error"})

    if state.get("schema_version") != 1:
        issue("schema-version", "schema_version must equal 1")
    try:
        mode = state_execution_mode(state)
    except ValueError as exc:
        issue("execution-mode", str(exc))
        return issues
    if mode != "standard":
        issue("execution-mode", "lightweight state requires standard mode")
    status = state.get("status")
    if status not in {
        "proposed",
        "discussing",
        "specified",
        "planned",
        "executing",
        "reviewing",
        "verifying",
        "ready_to_ship",
        "shipped",
        "blocked",
        "cancelled",
        "superseded",
    }:
        issue("invalid-state", "unknown standard lifecycle status: {!r}".format(status))
    next_action = state.get("next_action")
    if not isinstance(next_action, Mapping) or not next_action.get("operation"):
        issue("next-action", "next_action.operation must be explicit")
    if not isinstance(state.get("blockers"), list):
        issue("invalid-blockers", "blockers must be an array")
    plan = state.get("artifacts", {}).get("plan") if isinstance(
        state.get("artifacts"), Mapping
    ) else None
    if not isinstance(plan, str):
        issue("missing-plan", "standard state requires artifacts.plan")
    else:
        root = project_root.expanduser().resolve()
        plan_path = (root / plan).resolve()
        if root not in plan_path.parents:
            issue("unsafe-plan", "artifacts.plan escapes the project root")
        elif not plan_path.is_file():
            issue("missing-plan", "artifacts.plan points to missing file {}".format(plan))
    return issues


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-framework-route")
    choices = parser.add_mutually_exclusive_group()
    for mode in REQUESTED_MODES:
        choices.add_argument("--" + mode, dest="requested_mode", action="store_const", const=mode)
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    parser.add_argument("request", nargs="+", help="task request to route")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        decision = route_execution(
            " ".join(args.request), requested_mode=args.requested_mode
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return 0
    for key in (
        "selected_mode",
        "reason",
        "risk_factors",
        "complexity_factors",
        "assets_selected",
        "assets_skipped",
    ):
        value = decision[key]
        if isinstance(value, list):
            if not value:
                print("{}: []".format(key))
                continue
            print("{}:".format(key))
            for item in value:
                print("  - {}".format(item))
        else:
            print("{}: {}".format(key, value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
