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

#: The mode ordinary development runs in. `fast` optimises speed, `critical`
#: protects the application from grave damage, and everything between them is
#: `standard` — which is where most real work lives.
DEFAULT_EXECUTION_MODE = "standard"

#: Only for comparing two classifications ("is this an escalation?"). It is
#: deliberately not used to combine a phase mode with a task mode: a phase that
#: contains one critical task does not make its other tasks critical.
MODE_SEVERITY = {"fast": 0, "standard": 1, "critical": 2}

VERIFICATION_BUDGETS: Dict[str, Dict[str, Any]] = {
    "fast": {"target_ratio": 0.20, "max_full_review_passes": 1},
    "standard": {"target_ratio": 0.30, "max_full_review_passes": 1},
    "critical": {"target_ratio": None, "max_full_review_passes": "proportional"},
}

REVIEW_ROUNDS: Dict[str, Dict[str, int]] = {
    "fast": {"max_review_rounds": 1, "max_correction_rounds": 1, "reviewers_per_diff": 1},
    "standard": {"max_review_rounds": 1, "max_correction_rounds": 1, "reviewers_per_diff": 1},
    "critical": {"max_review_rounds": 1, "max_correction_rounds": 1, "reviewers_per_diff": 2},
}

SESSION_SCOPE: Dict[str, Any] = {
    "soft_checkpoint_minutes": 30,
    "hard_checkpoint_minutes": 45,
    "grace_minutes": 10,
    "max_units_per_session": 1,
}

CHANGE_SIZES = ("small", "moderate", "broad")

ENVIRONMENT_REBUILD_FAILURES = (
    "build",
    "dependency",
    "image",
    "migration",
    "schema",
    "server",
)

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


#: What `critical` is for: a defect here causes grave damage. Every entry names a
#: *harm*, never an area of the codebase. "Touches auth" is not one of them —
#: "breaks the authentication core" is. This distinction is the whole policy:
#: classifying by area is what made ordinary features critical because their
#: description happened to contain the word `auth`, `migration` or `financeiro`.
SEVERE_HARM_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (
        "auth_core_breakage",
        r"\b(n[uú]cleo de (auth|autentica[cç][aã]o)|authentication core|auth core|"
        r"core de sess[oõ]es|session core|quebrar? (o )?login|"
        r"fluxo de sess[aã]o|session management core)\b",
    ),
    (
        "privilege_escalation",
        r"\b(privilege escalation|escala[cç][aã]o de privil[eé]gio|eleva[cç][aã]o de privil[eé]gio|"
        r"bypass de (permiss[aã]o|autoriza[cç][aã]o)|permission bypass|authorization bypass|"
        r"invas[aã]o|unauthorized access|acesso n[aã]o autorizado)\b",
    ),
    (
        "cross_tenant_exposure",
        r"\b(cross[- ]tenant|entre tenants|vazamento entre tenants|tenant isolation|"
        r"isolamento (central )?entre tenants|isolamento de tenant|data leak between)\b",
    ),
    (
        "data_loss_or_corruption",
        r"\b(data loss|data corruption|perda de dados|corrup[cç][aã]o de dados|"
        r"perda s[eé]ria de dados|apagar dados|drop table|truncate)\b",
    ),
    (
        "money_movement",
        r"\b(mover dinheiro|movimenta[cç][aã]o de dinheiro|move money|transfer(ir)? fundos|"
        r"transfer funds|cobran[cç]a real|charge (the )?customer|preju[ií]zo financeiro|"
        r"financial loss|settlement)\b",
    ),
    (
        "payment_gateway",
        r"\b(payment gateway|gateway de pagamento|checkout gateway|adquirente|"
        r"processadora de pagamento|payment processor|psp)\b",
    ),
    (
        "secrets_or_cryptography",
        r"\b(criptografia|cryptograph|encryption key|chave de criptografia|"
        r"secrets? rotation|rota[cç][aã]o de segredos|gest[aã]o de segredos|secret management|"
        r"key management|assinatura de token|token signing)\b",
    ),
    (
        "account_recovery",
        r"\b(recupera[cç][aã]o de conta|account recovery|password reset|"
        r"reset de senha|esqueci minha senha|magic link)\b",
    ),
    (
        "destructive_migration",
        r"\b(migration destrutiva|migra[cç][aã]o destrutiva|destructive migration|"
        r"destructive backfill|migration irrevers[ií]vel|migra[cç][aã]o irrevers[ií]vel|"
        r"drop column|remover coluna com dados)\b",
    ),
    (
        "production_outage",
        r"\b(derrubar (a )?produ[cç][aã]o|production outage|indisponibilidade em produ[cç][aã]o|"
        r"parte essencial da aplica[cç][aã]o em produ[cç][aã]o|downtime em produ[cç][aã]o)\b",
    ),
    (
        "irreversible_wide_operation",
        r"\b(opera[cç][aã]o irrevers[ií]vel|irreversible operation|blast radius (grande|amplo|wide|large))\b",
    ),
)

#: Recognised harm categories. An escalation to `critical` has to name one of
#: these, so "it feels risky" cannot become a classification.
SEVERE_HARM_FACTORS = frozenset(name for name, _ in SEVERE_HARM_PATTERNS)

#: Areas that deserve care and *no* automatic escalation. They are reported so a
#: reader sees why the work is sensitive, and they raise the bar for `fast` only
#: through the ordinary criteria — never by themselves.
SENSITIVE_AREA_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("authentication_area", r"\b(auth|authentication|autentica[cç][aã]o|login|sess[aã]o|session)\b"),
    (
        "authorization_area",
        r"\b(authorization|autoriza[cç][aã]o|permission|permiss[aã]o|role|papel|capability)\b",
    ),
    (
        "financial_area",
        r"\b(payment|pagamento|billing|faturamento|finance|financial|financeiro|invoice|fatura)\b",
    ),
    ("migration_area", r"\b(migration|migra[cç][aã]o|migrate|backfill|schema)\b"),
    ("tenant_area", r"\b(tenant|multi-?tenant|organization|organiza[cç][aã]o)\b"),
    ("personal_data_area", r"\b(pii|dados pessoais|personal data|lgpd|gdpr)\b"),
)

#: Positive evidence that the work is short and contained. `fast` is claimed, not
#: assumed: without one of these the request falls to `standard`.
FAST_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (
        "copy_or_text_fix",
        r"\b(typo|copy fix|wording|mensagem de erro|label)\b"
        r"|\b(corrij|ajust|alter|mud)\w*\s+(apenas\s+|somente\s+)?(o\s+)?texto\b",
    ),
    (
        "visual_adjustment",
        r"\b(ajuste visual|espa[cç]amento|padding|margin|alinhamento|cor do bot[aã]o|"
        r"visual adjustment|styling fix)\b",
    ),
    ("small_bug", r"\b(bug pequeno|pequeno bug|small bug|corre[cç][aã]o pontual|quick fix|hotfix simples)\b"),
    ("simple_redirect", r"\b(redirect simples|simple redirect|redirecionamento simples)\b"),
    (
        "missing_test",
        r"\b(teste faltante|testes faltantes|missing tests?|adicione (um )?teste|cobrir com teste)\b",
    ),
    (
        "helper_tweak",
        r"\b(helper|util(it[aá]rio)?|fun[cç][aã]o auxiliar|pequena altera[cç][aã]o|small change)\b",
    ),
    (
        "explicitly_small_scope",
        r"\b(um arquivo|one file|poucos arquivos|few files|10 minutos|10 minutes|"
        r"altera[cç][aã]o localizada|localized change|melhoria localizada)\b",
    ),
)

#: Complexity worth reporting. It no longer *selects* `standard` — `standard` is
#: the default — but it explains the choice and argues against `fast`.
STANDARD_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("cross_session_work", r"\b(cross[- ]session|multiple sessions|varias sessoes|atravessar sessoes|retomada)\b"),
    ("dependent_steps", r"\b(dependent steps|etapas dependentes|multi[- ]step|multiplas etapas)\b"),
    ("distributed_feature", r"\b(distributed feature|feature distribuida|multiple modules|varios modulos)\b"),
    ("moderate_refactor", r"\b(moderate refactor|refatoracao moderada|refactor)\b"),
    ("new_endpoint_or_route", r"\b(new|novo|nova)\b.{0,30}\b(endpoint|route|rota|entidade|entity)\b"),
    ("moderate_regression_risk", r"\b(moderate regression|risco moderado de regressao)\b"),
    ("feature_work", r"\b(feature|funcionalidade|onboarding|importa[cç][aã]o|import|fluxo administrativo)\b"),
    ("integration_work", r"\b(integra[cç][aã]o|integration|contrato conhecido|known contract)\b"),
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


BLAST_RADII = ("local", "feature", "module", "application", "tenant-wide")
REVERSIBILITY_LEVELS = ("trivial", "straightforward", "hard", "irreversible")

#: Above this, work is not "one short task" any more, whatever it touches. Time
#: separates `fast` from `standard` and nothing else: a task that runs for hours
#: is still `standard` unless a failure would cause grave damage.
FAST_MINUTES = 15
FAST_FILES = 4


def classify_task(
    *,
    severe_harm_factors: Sequence[str] = (),
    sensitive_areas: Sequence[str] = (),
    reversibility: str = "straightforward",
    blast_radius: str = "feature",
    estimated_minutes: Optional[float] = None,
    files_touched: Optional[int] = None,
    localized: bool = False,
    architectural_decision: bool = False,
    splittable: bool = True,
    coupled_oversized_work: bool = False,
) -> Dict[str, Any]:
    """Classify one unit of work by the six ordered factors.

    The order is the policy: potential damage, sensitivity of the area,
    reversibility, blast radius, complexity and size, and only then time. Time
    separates `fast` from `standard`; damage is what reaches `critical`.

    A sensitive area on its own never escalates. Neither does size, a migration,
    a permission change or a long estimate — those are the reasons `critical`
    used to be handed out for ordinary features.
    """

    if reversibility not in REVERSIBILITY_LEVELS:
        raise ValueError("unknown reversibility: {!r}".format(reversibility))
    if blast_radius not in BLAST_RADII:
        raise ValueError("unknown blast radius: {!r}".format(blast_radius))

    harm = [factor for factor in severe_harm_factors if factor]
    unknown = sorted(set(harm) - SEVERE_HARM_FACTORS)
    if unknown:
        raise ValueError(
            "unknown severe harm factor(s): {}; known: {}".format(
                ", ".join(unknown), ", ".join(sorted(SEVERE_HARM_FACTORS))
            )
        )
    areas = [area for area in sensitive_areas if area]

    if harm:
        return _classification(
            "critical",
            "A defect here causes grave damage: {}.".format(", ".join(sorted(set(harm)))),
            harm,
            areas,
        )
    if reversibility == "irreversible" and blast_radius in {"application", "tenant-wide"}:
        return _classification(
            "critical",
            "The operation is irreversible with an application-wide blast radius.",
            harm,
            areas,
        )
    if coupled_oversized_work and not splittable:
        return _classification(
            "critical",
            "The work is oversized and coupled, and cannot be split into standard "
            "units safely.",
            harm,
            areas,
        )
    if coupled_oversized_work and splittable:
        return _classification(
            "standard",
            "Oversized work that can be split: classify each resulting unit on its "
            "own instead of escalating the whole.",
            harm,
            areas,
        )

    short = estimated_minutes is not None and estimated_minutes <= FAST_MINUTES
    contained = files_touched is not None and files_touched <= FAST_FILES
    if (
        localized
        and not architectural_decision
        and blast_radius in {"local", "feature"}
        and reversibility in {"trivial", "straightforward"}
        and (short or estimated_minutes is None)
        and (contained or files_touched is None)
    ):
        return _classification(
            "fast",
            "Short, contained and easily reverted change with no grave-damage path.",
            harm,
            areas,
        )
    return _classification(
        "standard",
        "Ordinary development risk: planning and proportional verification, not "
        "the critical lifecycle.",
        harm,
        areas,
    )


def _classification(
    mode: str, reason: str, harm: Sequence[str], areas: Sequence[str]
) -> Dict[str, Any]:
    return {
        "mode": mode,
        "reason": reason,
        "severe_harm_factors": sorted(set(harm)),
        "sensitive_areas": sorted(set(areas)),
    }


def route_execution(
    request: str,
    *,
    requested_mode: Optional[str] = None,
    persistence_requested: bool = False,
) -> Dict[str, Any]:
    """Select a mode from concrete signals, defaulting to standard.

    `standard` is the resting state of the router. `fast` needs positive evidence
    that the work is short and contained; `critical` needs a named grave-damage
    path. A sensitive area is reported and never escalates on its own.
    """

    clean = _normalized_text(request)
    explicit = requested_mode_from_text(request, requested_mode)
    harm_factors = _signals(clean, SEVERE_HARM_PATTERNS)
    sensitive_areas = _signals(clean, SENSITIVE_AREA_PATTERNS)
    fast_factors = _signals(clean, FAST_PATTERNS)
    complexity_factors = _signals(clean, STANDARD_PATTERNS)

    escalated = False
    if explicit == "critical":
        selected = "critical"
        reason = "User explicitly selected critical mode."
    elif explicit in {"fast", "standard"}:
        if harm_factors:
            selected = "critical"
            escalated = True
            reason = (
                "Escalated from explicit {} because a failure would cause grave "
                "damage: {}.".format(explicit, ", ".join(harm_factors))
            )
        else:
            selected = explicit
            reason = "User explicitly selected {} mode.".format(explicit)
    elif harm_factors:
        selected = "critical"
        reason = "A defect here would cause grave damage: {}.".format(
            ", ".join(harm_factors)
        )
    elif fast_factors and not complexity_factors:
        selected = "fast"
        reason = "Short, contained work: {}.".format(", ".join(fast_factors))
    else:
        selected = "standard"
        reason = (
            "Ordinary development: {}.".format(", ".join(complexity_factors))
            if complexity_factors
            else "Ordinary development with no grave-damage path and no evidence of "
            "a short contained change; standard is the default."
        )

    policy = deepcopy(MODE_POLICIES[selected])
    policy["verification_budget"] = deepcopy(VERIFICATION_BUDGETS[selected])
    policy["review_rounds"] = deepcopy(REVIEW_ROUNDS[selected])
    policy["session_scope"] = deepcopy(SESSION_SCOPE)
    policy["auto_advance_to_next_phase"] = False
    policy["create_persistent_state"] = should_create_persistent_state(
        selected,
        crosses_sessions="cross_session_work" in complexity_factors,
        dependent_tasks="dependent_steps" in complexity_factors,
        user_requested=persistence_requested,
    )

    return {
        "selected_mode": selected,
        "reason": reason,
        # Kept under the historical key so existing consumers keep reading the
        # same field; what changed is that only grave-damage paths land in it.
        "risk_factors": harm_factors,
        "sensitive_areas": sensitive_areas,
        "fast_factors": fast_factors,
        "complexity_factors": complexity_factors,
        "assets_selected": list(ASSETS_BY_MODE[selected]),
        "assets_skipped": list(SKIPPED_BY_MODE[selected]),
        "requested_mode": explicit,
        "escalated": escalated,
        "policy": policy,
    }


def review_policy(
    mode: str,
    *,
    localized_correction: bool = False,
    completed_review_rounds: int = 0,
    completed_correction_rounds: int = 0,
    unresolved_blockers: bool = False,
) -> Dict[str, Any]:
    selected = normalize_mode(mode, default="fast")
    if selected == "auto":
        raise ValueError("review policy requires a selected execution mode")
    rounds = REVIEW_ROUNDS[selected]
    another_review = completed_review_rounds < rounds["max_review_rounds"] or (
        unresolved_blockers
        and completed_correction_rounds < rounds["max_correction_rounds"]
        and completed_review_rounds <= rounds["max_review_rounds"]
    )
    return {
        "review_mode": "split" if selected == "critical" else "integrated",
        "depth": {"fast": "light", "standard": "normal", "critical": "deep"}[selected],
        "blocking_threshold": "BLOCKER",
        "scope": "affected-diff-and-criteria" if localized_correction else "full-current-diff",
        "independent_reviews": selected == "critical",
        "max_review_rounds": rounds["max_review_rounds"],
        "max_correction_rounds": rounds["max_correction_rounds"],
        "reviewers_per_diff": rounds["reviewers_per_diff"],
        "additional_reviewer_requires_evidence": True,
        "another_review_round_allowed": another_review,
        "another_correction_round_allowed": (
            unresolved_blockers
            and completed_correction_rounds < rounds["max_correction_rounds"]
        ),
        "escalate_instead_of_looping": not another_review and unresolved_blockers,
    }


def plan_session_scope(
    units: Sequence[str],
    *,
    elapsed_minutes: float = 0.0,
    minutes_to_finish_current_unit: float = 0.0,
    full_run_requested: bool = False,
    continuation_requested: bool = False,
) -> Dict[str, Any]:
    """Split work into session-sized units and decide when to stop at a checkpoint.

    Volume is never a blocker: extra units are deferred to further sessions the
    user may resume explicitly. A unit that is a few minutes from done is
    finished before the checkpoint instead of being cut in half.
    """

    pending = [unit for unit in units if str(unit).strip()]
    soft = float(SESSION_SCOPE["soft_checkpoint_minutes"])
    hard = float(SESSION_SCOPE["hard_checkpoint_minutes"])
    grace = float(SESSION_SCOPE["grace_minutes"])
    per_session = int(SESSION_SCOPE["max_units_per_session"])

    if full_run_requested:
        planned, deferred = list(pending), []
    else:
        planned, deferred = pending[:per_session], pending[per_session:]

    if full_run_requested:
        action = "continue"
        reason = "The user asked for a complete run, so the session is not cut at a checkpoint."
    elif elapsed_minutes + minutes_to_finish_current_unit <= hard:
        if elapsed_minutes < soft:
            action = "continue"
            reason = "Inside the session budget; keep working on the current unit."
        else:
            action = "finish-current-unit"
            reason = (
                "Past the soft checkpoint but the current unit still lands inside the budget; "
                "finish it, then stop."
            )
    elif minutes_to_finish_current_unit <= grace:
        action = "finish-current-unit"
        reason = (
            "Over the budget, but the current unit is minutes from done; finish it rather than "
            "leaving it half-applied."
        )
    else:
        action = "checkpoint-now"
        reason = (
            "Over the session budget with substantial work remaining; close the atomic unit "
            "reached so far and hand off."
        )

    stopping = action != "continue"
    return {
        "planned_units": planned,
        "deferred_units": deferred,
        "checkpoint": {
            "action": action,
            "reason": reason,
            "commit_required": stopping,
            "handoff_required": stopping,
            "soft_checkpoint_minutes": soft,
            "hard_checkpoint_minutes": hard,
        },
        "auto_advance_to_next_phase": False,
        "volume_is_blocker": False,
        "requires_explicit_continuation": bool(deferred) and not continuation_requested,
        "continuation_requested": continuation_requested,
        "full_run_requested": full_run_requested,
    }


def verification_scope_for_change(
    mode: str,
    *,
    change_size: str = "small",
    phase_closure: bool = False,
    pull_request: bool = False,
    full_suite_already_green: bool = False,
    failure_kind: str = "",
    environment_running: bool = True,
) -> Dict[str, Any]:
    """Pick verification proportional to the diff instead of replaying everything."""

    selected = normalize_mode(mode, default="fast")
    if selected == "auto":
        raise ValueError("test scope requires a selected execution mode")
    size = str(change_size).strip().lower() or "small"
    if size not in CHANGE_SIZES:
        raise ValueError("unknown change size: {}".format(change_size))

    closing = bool(phase_closure or pull_request)
    if closing:
        scope, run_full_suite = "full-suite", True
        reason = "Real phase closure or pull request: run the complete suite once."
    elif size == "small" and full_suite_already_green:
        scope, run_full_suite = "targeted", False
        reason = (
            "Small local change over an already green suite: rerun only the affected tests."
        )
    elif size == "small":
        scope, run_full_suite = "targeted", False
        reason = "Small local change: targeted tests covering the diff."
    else:
        scope, run_full_suite = "proportional", False
        reason = "Broader diff: run the affected areas and their integration points."

    kind = str(failure_kind).strip().lower()
    rebuild = not environment_running or kind in ENVIRONMENT_REBUILD_FAILURES
    return {
        "scope": scope,
        "run_full_suite": run_full_suite,
        "reason": reason,
        "rebuild_environment": rebuild,
        "rebuild_reason": (
            "Environment is not running or the failure comes from the build itself."
            if rebuild
            else "Failure is inside the test itself; reuse the running environment and rerun "
            "the affected spec."
        ),
        "rerun_failing_spec_only": bool(kind) and not rebuild,
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


#: What the persistent kernel actually demands of one task, per mode. Persistence
#: — state, decisions, contracts, evidence — is not in this table on purpose: it
#: is memory, and memory is never the thing to cut. What scales with the mode is
#: *ceremony*: the seal, the number of independent reviewers, the breadth of the
#: self-review checklist.
LIFECYCLE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    "fast": {
        "plan_seal": False,
        "independent_reviews": 0,
        "full_self_review_checklist": False,
        "contract_depth": "minimal",
    },
    "standard": {
        "plan_seal": False,
        "independent_reviews": 1,
        "full_self_review_checklist": True,
        "contract_depth": "proportional",
    },
    "critical": {
        "plan_seal": True,
        "independent_reviews": 2,
        "full_self_review_checklist": True,
        "contract_depth": "complete",
    },
}


def mode_requirements(mode: str) -> Dict[str, Any]:
    """The lifecycle obligations one task carries under ``mode``."""

    selected = normalize_mode(mode, default=DEFAULT_EXECUTION_MODE)
    if selected == "auto":
        raise ValueError("lifecycle requirements need a selected execution mode")
    return deepcopy(LIFECYCLE_REQUIREMENTS[selected])


def resolve_execution_mode(
    *,
    project: Optional[str] = None,
    phase: Optional[str] = None,
    task: Optional[str] = None,
    override: Optional[str] = None,
) -> Dict[str, str]:
    """Resolve the mode of one unit of work, most specific wins.

    The phase and the project supply a *default*, never a floor. Taking the
    maximum of the three — which is what a single project-level field amounts to
    in practice — is how a ten-file frontend task ended up running the critical
    lifecycle because the project it belonged to had been initialized as
    critical.
    """

    for value, source in (
        (override, "task-override"),
        (task, "task"),
        (phase, "phase"),
        (project, "project"),
    ):
        if value is None:
            continue
        mode = normalize_mode(value, default=DEFAULT_EXECUTION_MODE)
        if mode == "auto":
            continue
        return {"mode": mode, "source": source}
    return {"mode": DEFAULT_EXECUTION_MODE, "source": "default"}


MINIMUM_JUSTIFICATION = 12


def reclassify_execution_mode(
    current: str,
    target: str,
    *,
    justification: str = "",
    severe_harm_factors: Sequence[str] = (),
) -> Dict[str, Any]:
    """Decide whether a classification may move, and why.

    Escalating to `critical` costs a named grave-damage path — the same
    vocabulary `classify_task` uses — so "this feels risky" cannot become a
    classification. Coming back down costs a plain reason and nothing more: an
    over-classification is a mistake to correct, not a decision to defend.
    """

    source = normalize_mode(current, default=DEFAULT_EXECUTION_MODE)
    destination = normalize_mode(target, default=DEFAULT_EXECUTION_MODE)
    if "auto" in {source, destination}:
        raise ValueError("reclassification needs two selected execution modes")

    reason = justification.strip()
    issues: List[str] = []
    direction = (
        "unchanged"
        if MODE_SEVERITY[destination] == MODE_SEVERITY[source]
        else "escalation"
        if MODE_SEVERITY[destination] > MODE_SEVERITY[source]
        else "reduction"
    )

    if direction != "unchanged" and len(reason) < MINIMUM_JUSTIFICATION:
        issues.append(
            "reclassification requires a justification of at least {} characters".format(
                MINIMUM_JUSTIFICATION
            )
        )
    named = [factor for factor in severe_harm_factors if factor]
    unknown = sorted(set(named) - SEVERE_HARM_FACTORS)
    if unknown:
        issues.append(
            "unknown severe harm factor(s): {}; known: {}".format(
                ", ".join(unknown), ", ".join(sorted(SEVERE_HARM_FACTORS))
            )
        )
    if destination == "critical" and direction == "escalation" and not named:
        issues.append(
            "escalating to critical requires at least one named severe harm factor: "
            + ", ".join(sorted(SEVERE_HARM_FACTORS))
        )

    return {
        "allowed": not issues,
        "direction": direction,
        "from": source,
        "to": destination,
        "justification": reason,
        "severe_harm_factors": sorted(set(named)),
        "issues": issues,
    }


def is_persistent_state(state: Mapping[str, Any]) -> bool:
    """Whether this state carries the full kernel rather than the resume-only one.

    Read from the shape, not from the mode. The two were fused — only `critical`
    could own phases, contracts and gates — which left "I need the project to
    remember things" and "a defect here is catastrophic" as the same request.
    """

    return isinstance(state.get("gates"), Mapping)


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
    if mode == "critical":
        issue(
            "execution-mode",
            "a critical default cannot run on the resume-only state; initialize the "
            "persistent kernel instead",
        )
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
        "sensitive_areas",
        "fast_factors",
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
