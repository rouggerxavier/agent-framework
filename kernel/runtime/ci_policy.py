"""CI throughput policy: what CI gates, and what it does not gate.

```text
CI gates integration, not continuous development.
```

The execution mode answers "how much ceremony does a defect here deserve?".
This module answers a different question — "which gates does *this* change owe,
and what is allowed to happen while they run?" — and the two were fused. A
`standard` task inherited a full pipeline and a synchronous wait, so every
ordinary feature paid for a complete suite and then idled until it returned.

The two axes are kept apart on purpose:

- ``execution_mode`` (``fast``/``standard``/``critical``) stays a statement
  about risk and ceremony, exactly as before;
- ``ci_profile`` (``minimal``/``targeted``/``full``) is a statement about which
  gates the diff actually needs.

Everything here is side-effect free: deciding a CI profile never runs a command,
never touches ``.agent/`` and never talks to a forge.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


CI_PROFILES = ("minimal", "targeted", "full")

#: What ordinary implementation work runs. `minimal` is claimed by a change with
#: no executable behaviour; `full` is claimed by blast radius or by a named
#: grave-damage path. Everything between them is `targeted`.
DEFAULT_CI_PROFILE = "targeted"

CI_WAIT_POLICIES = ("background", "blocking_before_merge", "blocking_now")

NEXT_WORK_POLICIES = ("continue_independent", "stack_local", "wait")

CI_BLOCKING_POINTS = ("before_merge", "now", "none")

RUNNER_KINDS = (
    "hosted",
    "self_hosted_dedicated",
    "self_hosted_shared",
    "unknown",
)

CHANGE_IMPACTS = (
    "docs",
    "metadata",
    "mechanical_refactor",
    "frontend",
    "backend",
    "contracts",
    "database",
    "security_core",
    "e2e_relevant",
    "release",
)

#: Impacts that change no executable behaviour. A change made only of these is
#: the whole justification for `minimal`: running a full pipeline over a README
#: buys nothing and costs a runner.
NON_EXECUTABLE_IMPACTS = frozenset({"docs", "metadata", "mechanical_refactor"})

#: Impacts whose failure mode is not "a test goes red later". These pull the
#: profile to `full` even when the diff is small.
FULL_PROFILE_IMPACTS = frozenset({"database", "security_core", "release"})

#: Names from ``execution_modes.SEVERE_HARM_FACTORS`` that mean the change is in
#: the security core rather than merely near a sensitive area. Mirrored as plain
#: strings so this module stays dependency-free; ``tests/test_ci_throughput_policy``
#: asserts the mirror still matches the source vocabulary.
SECURITY_CORE_HARM_FACTORS = frozenset(
    {
        "auth_core_breakage",
        "privilege_escalation",
        "cross_tenant_exposure",
        "secrets_or_cryptography",
        "account_recovery",
    }
)

#: Gate kinds, not commands. A repository binds them to its own scripts through
#: `test-confidence-mapper`; the policy only decides which kinds this diff owes.
GATE_COST: Dict[str, str] = {
    "docs-check": "light",
    "lint": "light",
    "typecheck": "light",
    "unit-tests-focal": "light",
    "unit-tests-affected": "moderate",
    "component-tests-affected": "moderate",
    "contract-tests": "moderate",
    "integration-tests-affected": "moderate",
    "security-scan": "moderate",
    "e2e-focal": "moderate",
    "migration-forward-and-rollback": "heavy",
    "build": "heavy",
    "e2e-operational": "heavy",
    "e2e-full-regression": "heavy",
    "full-suite": "heavy",
    "release-checks": "heavy",
}

GATES_BY_IMPACT: Dict[str, Tuple[str, ...]] = {
    "docs": ("docs-check",),
    "metadata": ("docs-check",),
    "mechanical_refactor": ("lint", "typecheck"),
    "frontend": ("lint", "typecheck", "component-tests-affected"),
    "backend": ("lint", "typecheck", "unit-tests-affected", "integration-tests-affected"),
    "contracts": ("typecheck", "contract-tests"),
    "database": ("migration-forward-and-rollback", "integration-tests-affected"),
    "security_core": ("security-scan", "integration-tests-affected"),
    "e2e_relevant": ("e2e-focal",),
    "release": ("build", "release-checks"),
}

#: Added on top of the impact gates when the profile is `full`. `full` is the
#: profile that says "validate the whole thing", so it is the only one that
#: earns the complete suite by default.
FULL_PROFILE_GATES: Tuple[str, ...] = ("full-suite", "e2e-operational")

#: Local work that a busy shared runner never has a reason to stop. Reading,
#: editing, planning and reviewing consume the developer, not the machine.
ALWAYS_ALLOWED_LOCAL_WORK: Tuple[str, ...] = (
    "read",
    "edit",
    "write-tests",
    "plan",
    "analyse",
    "review-diff",
    "documentation",
)

#: Local workloads that genuinely compete with a self-hosted runner sharing the
#: machine. Matched by substring so `pnpm test:e2e` and `docker build .` land in
#: the right bucket without a taxonomy of every project's script names.
HEAVY_LOCAL_WORKLOAD_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("full_test_suite", r"(full[- ]?suite|suite completa|test:all|all tests|pytest\b(?!.*::))"),
    ("browser_e2e", r"(playwright|cypress|puppeteer|\be2e\b|end[- ]to[- ]end)"),
    ("container_build", r"(docker|podman|compose\b|container build)"),
    ("bundler_build", r"(next build|vite build|webpack|turbopack|\bbuild\b|bundle)"),
    ("load_or_perf", r"(load test|k6|benchmark|perf(ormance)? run)"),
    ("local_ci_replica", r"(act\b|local ci|ci replica)"),
)

IMPACT_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (
        "docs",
        r"\b(docs?|documenta[cç][aã]o|readme|changelog|adr|guia|guide|"
        r"coment[aá]rios?|comments?)\b",
    ),
    (
        "metadata",
        r"\b(metadata|metadados|frontmatter|codeowners|license|licen[cç]a|"
        r"version bump|bump de vers[aã]o)\b",
    ),
    (
        "mechanical_refactor",
        r"\b(rename|renomear|mover arquivos?|move files?|"
        r"refator(a[cç][aã]o)? mec[aâ]nic[ao]|mechanical refactor|"
        r"formata[cç][aã]o|formatting|lint fix)\b",
    ),
    (
        "frontend",
        r"\b(frontend|front[- ]end|ui|tela|telas|p[aá]gina|page|componente|"
        r"component|css|tailwind|react|next\.js)\b",
    ),
    (
        "backend",
        r"\b(backend|back[- ]end|api|endpoint|rota|route|servi[cç]o|service|"
        r"handler|worker|job|fila|queue)\b",
    ),
    (
        "contracts",
        r"\b(contrato|contract|openapi|swagger|graphql|protobuf|dto|payload|"
        r"interface p[uú]blica|public interface|schema de resposta)\b",
    ),
    (
        "database",
        r"\b(migration|migra[cç][aã]o|backfill|banco de dados|database|"
        r"schema do banco|sql|[ií]ndice de tabela)\b",
    ),
    (
        "e2e_relevant",
        r"\b(e2e|end[- ]to[- ]end|playwright|cypress|fluxo de usu[aá]rio|"
        r"user flow|checkout|onboarding)\b",
    ),
    (
        "release",
        r"\b(release|deploy|rollout|publica[cç][aã]o em produ[cç][aã]o|"
        r"tag de vers[aã]o|hotfix de produ[cç][aã]o)\b",
    ),
)


def _matched(text: str, patterns: Iterable[Tuple[str, str]]) -> List[str]:
    return [
        name
        for name, pattern in patterns
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def _ordered(values: Iterable[str], order: Sequence[str]) -> List[str]:
    present = {value for value in values if value}
    ranked = [value for value in order if value in present]
    return ranked + sorted(present - set(order))


def _validate_impacts(impacts: Sequence[str]) -> List[str]:
    unknown = sorted({impact for impact in impacts if impact} - set(CHANGE_IMPACTS))
    if unknown:
        raise ValueError(
            "unknown change impact(s): {}; known: {}".format(
                ", ".join(unknown), ", ".join(CHANGE_IMPACTS)
            )
        )
    return _ordered(impacts, CHANGE_IMPACTS)


def classify_change_impacts(
    request: str,
    *,
    severe_harm_factors: Sequence[str] = (),
    sensitive_areas: Sequence[str] = (),
) -> List[str]:
    """Classify what a request touches, so CI can run the gates it owes.

    ``security_core`` is claimed by a named grave-damage path from the router's
    own vocabulary, never by a sensitive area. Mentioning a login screen is not
    a change to the authentication core, and treating it as one is how a copy
    fix would end up paying for the complete pipeline.
    """

    impacts = set(_matched(request, IMPACT_PATTERNS))
    if set(severe_harm_factors) & SECURITY_CORE_HARM_FACTORS:
        impacts.add("security_core")
    if sensitive_areas and not impacts:
        # A sensitive area with nothing else recognised is still executable
        # work; `targeted` covers it, and the security scan is added by
        # `select_gates`.
        impacts.add("backend")
    return _ordered(impacts, CHANGE_IMPACTS)


def select_ci_profile(
    *,
    impacts: Sequence[str] = (),
    execution_mode: str = "standard",
    requested_profile: Optional[str] = None,
    mechanical_change_proven: bool = False,
    blast_radius: str = "feature",
    reversibility: str = "straightforward",
) -> Dict[str, Any]:
    """Pick the validation profile for one change.

    The execution mode is an input, not a synonym: `critical` does imply `full`,
    but `standard` implies nothing at all. An explicit request is honoured
    upwards without argument and only overridden downwards when the change owes
    `full` for a reason the requester cannot wish away.
    """

    resolved = _validate_impacts(impacts)
    if requested_profile is not None and requested_profile not in CI_PROFILES:
        raise ValueError("unknown ci profile: {!r}".format(requested_profile))

    forced: List[str] = []
    if execution_mode == "critical":
        forced.append("critical execution mode")
    forced.extend(sorted(set(resolved) & FULL_PROFILE_IMPACTS))
    if blast_radius in {"application", "tenant-wide"}:
        forced.append("blast radius {}".format(blast_radius))
    if reversibility == "irreversible":
        forced.append("irreversible change")

    if requested_profile is not None:
        if forced and requested_profile != "full":
            return _profile(
                "full",
                "requested {} raised to full: {}.".format(
                    requested_profile, ", ".join(forced)
                ),
                resolved,
                escalated_from=requested_profile,
            )
        return _profile(
            requested_profile,
            "Explicitly selected {} profile.".format(requested_profile),
            resolved,
        )

    if forced:
        return _profile("full", "Full validation required: {}.".format(", ".join(forced)), resolved)

    executable = [impact for impact in resolved if impact not in NON_EXECUTABLE_IMPACTS]
    if resolved and not executable:
        if "mechanical_refactor" in resolved and not mechanical_change_proven:
            return _profile(
                "targeted",
                "Refactor claimed mechanical but not proven; targeted gates confirm it.",
                resolved,
            )
        return _profile(
            "minimal",
            "No executable behaviour changes: {}.".format(", ".join(resolved)),
            resolved,
        )

    return _profile(
        DEFAULT_CI_PROFILE,
        "Ordinary implementation: gates for the affected surface only."
        if resolved
        else "Ordinary implementation with no classified impact; targeted is the default.",
        resolved,
    )


def _profile(
    profile: str,
    reason: str,
    impacts: Sequence[str],
    *,
    escalated_from: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "ci_profile": profile,
        "reason": reason,
        "change_impacts": list(impacts),
        "escalated_from": escalated_from,
    }


def select_gates(
    *,
    ci_profile: str,
    impacts: Sequence[str] = (),
    sensitive_areas: Sequence[str] = (),
    critical_user_paths_touched: bool = False,
    e2e_available: bool = True,
) -> Dict[str, Any]:
    """Turn a profile plus a set of impacts into gate kinds.

    ``deferred_gates`` is the honest half of the answer: a gate that is not run
    for this change is named, with where it *is* run, so "we skipped it" never
    silently becomes "nobody runs it".
    """

    if ci_profile not in CI_PROFILES:
        raise ValueError("unknown ci profile: {!r}".format(ci_profile))
    resolved = _validate_impacts(impacts)

    selected: List[str] = []
    for impact in resolved:
        for gate in GATES_BY_IMPACT[impact]:
            if gate not in selected:
                selected.append(gate)
    if not selected:
        selected = ["lint", "typecheck", "unit-tests-affected"]
    if sensitive_areas and "security-scan" not in selected:
        selected.append("security-scan")
    if critical_user_paths_touched and e2e_available and "e2e-operational" not in selected:
        selected.append("e2e-operational")

    deferred: List[Dict[str, str]] = []
    if ci_profile == "full":
        for gate in FULL_PROFILE_GATES:
            if gate == "e2e-operational" and not e2e_available:
                continue
            if gate not in selected:
                selected.append(gate)
        if e2e_available and "e2e-full-regression" not in selected:
            selected.append("e2e-full-regression")
    else:
        if e2e_available:
            deferred.append(
                {
                    "gate": "e2e-full-regression",
                    "runs_at": "nightly, release, or an explicit full profile",
                    "reason": "Full regression is not a per-change gate.",
                }
            )
        deferred.append(
            {
                "gate": "full-suite",
                "runs_at": "release or an explicit full profile",
                "reason": "The affected surface is covered by the selected gates.",
            }
        )
        if ci_profile == "minimal":
            deferred.append(
                {
                    "gate": "unit-tests-affected",
                    "runs_at": "the next change with executable behaviour",
                    "reason": "This change alters no executable behaviour.",
                }
            )

    ordered = [gate for gate in GATE_COST if gate in selected]
    ordered += [gate for gate in selected if gate not in GATE_COST]
    return {
        "gates": ordered,
        "deferred_gates": deferred,
        "e2e_tier": _e2e_tier(ordered),
    }


def _e2e_tier(gates: Sequence[str]) -> str:
    if "e2e-full-regression" in gates:
        return "full_regression"
    if "e2e-operational" in gates:
        return "operational"
    if "e2e-focal" in gates:
        return "focal"
    return "none"


def runner_policy(
    *,
    runner_kind: str = "unknown",
    remote_ci_running: bool = False,
    planned_local_workloads: Sequence[str] = (),
) -> Dict[str, Any]:
    """Decide what may run locally while remote CI occupies the same machine.

    A self-hosted runner sharing the development machine makes local heavy jobs
    and remote CI compete for the same cores. That contention is a scheduling
    fact, not a broken runner — and reading it as instability is how a green
    pipeline gets blamed for a laptop that was building two things at once.
    """

    if runner_kind not in RUNNER_KINDS:
        raise ValueError("unknown runner kind: {!r}".format(runner_kind))

    shared = runner_kind in {"self_hosted_shared", "unknown"}
    contention = bool(shared and remote_ci_running)

    allowed: List[str] = []
    on_hold: List[Dict[str, str]] = []
    for workload in planned_local_workloads:
        matches = _matched(str(workload), HEAVY_LOCAL_WORKLOAD_PATTERNS)
        if contention and matches:
            on_hold.append({"workload": str(workload), "kind": matches[0]})
        else:
            allowed.append(str(workload))

    if runner_kind == "hosted":
        reason = (
            "Hosted runners are independent machines: local validation runs in "
            "parallel with remote CI."
        )
    elif runner_kind == "self_hosted_dedicated":
        reason = "The self-hosted runner is dedicated hardware; no local contention."
    elif contention:
        reason = (
            "A self-hosted runner shares this machine and remote CI is running: "
            "keep local work light until it finishes."
        )
    else:
        reason = (
            "Runner kind is unknown; assumed shared, but nothing is running, so "
            "local work is unrestricted. Declare the runner kind to remove the "
            "assumption."
            if runner_kind == "unknown"
            else "Nothing is running remotely; local work is unrestricted."
        )

    return {
        "runner_kind": runner_kind,
        "shares_development_machine": shared,
        "remote_ci_running": bool(remote_ci_running),
        "contention": contention,
        "allow_local_heavy_jobs": not contention,
        "allowed_local_work": list(ALWAYS_ALLOWED_LOCAL_WORK),
        "local_workloads_allowed": allowed,
        "local_workloads_on_hold": on_hold,
        "reason": reason,
        "interpretation_note": (
            "Slow or timing-sensitive results while local heavy jobs run are "
            "resource contention until proven otherwise; do not report them as "
            "runner instability."
            if contention
            else "No contention to confuse with runner instability."
        ),
    }


def blocking_now_reasons(
    *,
    next_decision_depends_on_ci: bool = False,
    release_in_progress: bool = False,
    deploy_in_progress: bool = False,
    external_dependency_blocks: bool = False,
    speculative_work_forbidden: bool = False,
) -> List[str]:
    """The named conditions — and the only ones — that make an agent idle on CI.

    Deliberately not on this list: a `full` profile, a `critical` mode, and "CI
    is still running". None of those is a reason to stop typing; they are
    reasons to stop *merging*, which is a different field.
    """

    reasons: List[str] = []
    if next_decision_depends_on_ci:
        reasons.append("the CI result changes the next decision")
    if release_in_progress:
        reasons.append("a release is in progress")
    if deploy_in_progress:
        reasons.append("a deploy is in progress")
    if external_dependency_blocks:
        reasons.append("an external dependency blocks continuation")
    if speculative_work_forbidden:
        reasons.append("critical risk forbids speculative work")
    return reasons


def select_wait_policy(
    *,
    ci_profile: str = DEFAULT_CI_PROFILE,
    execution_mode: str = "standard",
    safe_next_work_available: bool = True,
    next_decision_depends_on_ci: bool = False,
    release_in_progress: bool = False,
    deploy_in_progress: bool = False,
    external_dependency_blocks: bool = False,
    speculative_work_forbidden: bool = False,
) -> Dict[str, Any]:
    """Decide what happens *now*, separately from what gates the merge.

    Two axes, and coupling them is the defect this function exists to avoid:

    - ``ci_blocking_point`` — where integration is gated. Practically always
      ``before_merge``; ``now`` only when the agent genuinely has to stop.
    - ``ci_wait_policy`` — what the agent does while the run executes.

    A `full` profile therefore does **not** produce a wait by itself. It raises
    ``publication_hold`` — nothing merges or publishes on top of this unit until
    it is green — and if safe work exists, the wait policy stays `background`.
    `blocking_before_merge` is the honest answer only when there is nothing safe
    left to do, so the wait lands at the merge boundary.
    """

    if ci_profile not in CI_PROFILES:
        raise ValueError("unknown ci profile: {!r}".format(ci_profile))

    named = blocking_now_reasons(
        next_decision_depends_on_ci=next_decision_depends_on_ci,
        release_in_progress=release_in_progress,
        deploy_in_progress=deploy_in_progress,
        external_dependency_blocks=external_dependency_blocks,
        speculative_work_forbidden=speculative_work_forbidden,
    )
    gated = ci_profile == "full" or execution_mode == "critical"

    if named:
        return {
            "ci_wait_policy": "blocking_now",
            "ci_blocking_point": "now",
            "idle_wait_allowed": True,
            "merge_requires_green": True,
            "publication_hold": True,
            "next_work_blocked": True,
            "blocking_now_reasons": named,
            "reason": "Waiting now: {}.".format(", ".join(named)),
        }

    if gated and not safe_next_work_available:
        return {
            "ci_wait_policy": "blocking_before_merge",
            "ci_blocking_point": "before_merge",
            "idle_wait_allowed": True,
            "merge_requires_green": True,
            "publication_hold": True,
            "next_work_blocked": False,
            "blocking_now_reasons": [],
            "reason": (
                "Full validation gates integration and no safe next unit exists: "
                "the wait lands at the merge boundary, not on a named blocker."
            ),
        }

    return {
        "ci_wait_policy": "background",
        "ci_blocking_point": "before_merge",
        "idle_wait_allowed": False,
        "merge_requires_green": True,
        "publication_hold": gated,
        "next_work_blocked": False,
        "blocking_now_reasons": [],
        "reason": (
            "Full validation gates integration — nothing merges or publishes on "
            "top of this unit until it is green — but safe work continues."
            if gated
            else "CI gates the merge, not the next unit of work."
        ),
    }


def classify_next_work(
    *,
    has_next_unit: bool = True,
    depends_on_pending_unit: bool = False,
    ci_wait_policy: str = "background",
    next_decision_depends_on_ci: bool = False,
    critical_risk_forbids_speculation: bool = False,
    external_dependency_blocks: bool = False,
    stacked_prs_supported: bool = False,
) -> Dict[str, Any]:
    """Classify the next unit against the pull request still in flight.

    Dependency, not politeness, decides. An independent unit starts from the
    integration base in its own worktree; a dependent one is built on a *local*
    branch off the pending head and only published once the parent integrates.
    """

    if ci_wait_policy not in CI_WAIT_POLICIES:
        raise ValueError("unknown ci wait policy: {!r}".format(ci_wait_policy))

    wait_reasons: List[str] = []
    if next_decision_depends_on_ci:
        wait_reasons.append("the CI result changes the next decision")
    if critical_risk_forbids_speculation:
        wait_reasons.append("critical risk forbids speculative work")
    if external_dependency_blocks:
        wait_reasons.append("an external dependency blocks continuation")
    if ci_wait_policy == "blocking_now":
        wait_reasons.append("the wait policy is blocking_now")

    if wait_reasons:
        return _next_work(
            "wait",
            "Wait: {}.".format(", ".join(wait_reasons)),
            branch_base="none",
            publish_dependent_pr=False,
            rebase_after_parent_merge=False,
            worktree="none",
        )

    if not has_next_unit:
        return _next_work(
            "continue_independent",
            "No queued unit; nothing is being blocked by the pending pull request.",
            branch_base="integration-base",
            publish_dependent_pr=False,
            rebase_after_parent_merge=False,
            worktree="new-from-integration-base",
            safe_work_available=False,
        )

    if depends_on_pending_unit:
        return _next_work(
            "stack_local",
            "The next unit builds on the pending pull request: branch locally from "
            "its head and keep the dependent pull request unpublished until the "
            "parent integrates."
            if not stacked_prs_supported
            else "The next unit builds on the pending pull request and the workflow "
            "is explicitly stacked: publishing the dependent pull request is allowed.",
            branch_base="pending-head",
            publish_dependent_pr=bool(stacked_prs_supported),
            rebase_after_parent_merge=True,
            worktree="new-from-pending-head",
        )

    return _next_work(
        "continue_independent",
        "The next unit is not declared dependent on the pending pull request: "
        "start it from the integration base. An undeclared dependency is read as "
        "independent, never as a confirmed dependency.",
        branch_base="integration-base",
        publish_dependent_pr=True,
        rebase_after_parent_merge=False,
        worktree="new-from-integration-base",
    )


def _next_work(
    policy: str,
    reason: str,
    *,
    branch_base: str,
    publish_dependent_pr: bool,
    rebase_after_parent_merge: bool,
    worktree: str,
    safe_work_available: Optional[bool] = None,
) -> Dict[str, Any]:
    return {
        "next_work_policy": policy,
        "reason": reason,
        "branch_base": branch_base,
        "publish_dependent_pr": publish_dependent_pr,
        "rebase_after_parent_merge": rebase_after_parent_merge,
        "worktree": worktree,
        "safe_work_available": (
            policy != "wait" if safe_work_available is None else safe_work_available
        ),
    }


def post_merge_observation(
    *,
    merge_tree_validated_by_pr: bool = False,
    main_adds_new_gate: bool = False,
    main_status: str = "unknown",
) -> Dict[str, Any]:
    """Separate the pull request's merge gate from watching `main` afterwards.

    When the exact merged tree was already validated and the branch workflow
    adds no gate the pull request did not run, the run on `main` observes; it
    does not re-authorise. A red `main` is still an incident — an observation
    that fails is work, not noise.
    """

    if str(main_status).strip().lower() in {"red", "failing", "failed"}:
        return {
            "role": "incident",
            "blocks_next_unit": True,
            "investigate_on_red": True,
            "reason": "main is red: investigate before starting the next unit.",
        }
    if not merge_tree_validated_by_pr or main_adds_new_gate:
        return {
            "role": "gate",
            "blocks_next_unit": True,
            "investigate_on_red": True,
            "reason": (
                "The run on main is a real gate: "
                + (
                    "it runs jobs the pull request did not."
                    if main_adds_new_gate
                    else "the merged tree was not the validated one."
                )
            ),
        }
    return {
        "role": "observation",
        "blocks_next_unit": False,
        "investigate_on_red": True,
        "reason": (
            "The merged tree was validated by the pull request and main adds no new "
            "functional gate: observe it, do not idle on it."
        ),
    }


def audit_scope_after_green(
    *,
    head_changed: bool = False,
    scope_changed: bool = False,
    previous_gates_valid: bool = True,
    open_blockers: bool = False,
    new_evidence: bool = False,
) -> Dict[str, Any]:
    """Prefer an incremental audit once CI is green.

    Repeating a complete audit over an unchanged head re-reads work that already
    has a verdict, and the second verdict is not more true than the first.
    """

    reasons: List[str] = []
    if head_changed:
        reasons.append("the head moved")
    if scope_changed:
        reasons.append("the scope changed")
    if not previous_gates_valid:
        reasons.append("previous gates no longer hold")

    if reasons:
        return {
            "audit_scope": "full",
            "reason": "Full audit: {}.".format(", ".join(reasons)),
            "audit_targets": ["complete diff", "all acceptance criteria", "all gates"],
        }

    targets = ["new evidence" if new_evidence else "no new evidence"]
    if open_blockers:
        targets.append("open blockers")
    return {
        "audit_scope": "incremental",
        "reason": (
            "Head, scope and gates are unchanged: audit only what is new."
        ),
        "audit_targets": targets,
    }


def documentation_checkpoint_policy(
    *,
    stale_docs_risk_incorrect_implementation: bool = False,
    documents_contract_or_interface: bool = False,
    release_documentation: bool = False,
) -> Dict[str, Any]:
    """Decide whether a documentation checkpoint holds the next functional unit.

    Docs that are temporarily behind are a cost. Docs that would make the next
    implementation wrong are a blocker. Only the second one stops work.
    """

    blocking_reasons: List[str] = []
    if stale_docs_risk_incorrect_implementation:
        blocking_reasons.append("stale docs would drive an incorrect implementation")
    if documents_contract_or_interface:
        blocking_reasons.append("the document is the contract other work reads")
    if release_documentation:
        blocking_reasons.append("release documentation ships with the release")

    if blocking_reasons:
        return {
            "documentation_checkpoint": "blocking",
            "blocks_next_unit": True,
            "reason": "Blocking checkpoint: {}.".format(", ".join(blocking_reasons)),
        }
    return {
        "documentation_checkpoint": "background",
        "blocks_next_unit": False,
        "reason": (
            "Documentation may land in its own pull request; the temporary stale "
            "state carries no risk of an incorrect implementation."
        ),
    }


def concurrency_recommendation(
    *, unit_ref: str = "pull-request", cancel_in_progress: bool = True
) -> Dict[str, Any]:
    """Recommend cancelling superseded runs of the same unit.

    A run whose commit can no longer integrate is a runner spent on a verdict
    nobody will read — and on a shared runner it is spent against the developer.
    """

    return {
        "group": "ci-{}".format(unit_ref),
        "cancel_in_progress": bool(cancel_in_progress),
        "reason": (
            "Superseded runs of the same unit cannot integrate; cancel them instead "
            "of validating a commit that is already replaced."
        ),
    }


def ci_decision(
    *,
    execution_mode: str = "standard",
    impacts: Sequence[str] = (),
    sensitive_areas: Sequence[str] = (),
    requested_profile: Optional[str] = None,
    mechanical_change_proven: bool = False,
    blast_radius: str = "feature",
    reversibility: str = "straightforward",
    critical_user_paths_touched: bool = False,
    e2e_available: bool = True,
    runner_kind: str = "unknown",
    remote_ci_running: bool = False,
    planned_local_workloads: Sequence[str] = (),
    has_next_unit: bool = True,
    next_unit_depends_on_current: bool = False,
    next_decision_depends_on_ci: bool = False,
    release_in_progress: bool = False,
    deploy_in_progress: bool = False,
    external_dependency_blocks: bool = False,
    speculative_work_forbidden: bool = False,
    stacked_prs_supported: bool = False,
    unit_merged: bool = False,
    merge_tree_validated_by_pr: bool = False,
    main_adds_new_gate: bool = False,
    main_status: str = "unknown",
    unit_ref: str = "pull-request",
) -> Dict[str, Any]:
    """Compose the complete CI throughput report for one unit of work."""

    profile = select_ci_profile(
        impacts=impacts,
        execution_mode=execution_mode,
        requested_profile=requested_profile,
        mechanical_change_proven=mechanical_change_proven,
        blast_radius=blast_radius,
        reversibility=reversibility,
    )
    gates = select_gates(
        ci_profile=profile["ci_profile"],
        impacts=profile["change_impacts"],
        sensitive_areas=sensitive_areas,
        critical_user_paths_touched=critical_user_paths_touched,
        e2e_available=e2e_available,
    )
    runner = runner_policy(
        runner_kind=runner_kind,
        remote_ci_running=remote_ci_running,
        planned_local_workloads=planned_local_workloads,
    )
    # The next unit is classified first, and the wait policy reads its answer.
    # Reversing the two is what couples `full` to "stop working": the profile
    # would decide the wait before anyone asked whether safe work existed.
    named_now = blocking_now_reasons(
        next_decision_depends_on_ci=next_decision_depends_on_ci,
        release_in_progress=release_in_progress,
        deploy_in_progress=deploy_in_progress,
        external_dependency_blocks=external_dependency_blocks,
        speculative_work_forbidden=speculative_work_forbidden,
    )
    next_work = classify_next_work(
        has_next_unit=has_next_unit,
        depends_on_pending_unit=next_unit_depends_on_current,
        ci_wait_policy="blocking_now" if named_now else "background",
        next_decision_depends_on_ci=next_decision_depends_on_ci,
        critical_risk_forbids_speculation=speculative_work_forbidden,
        external_dependency_blocks=external_dependency_blocks,
        stacked_prs_supported=stacked_prs_supported,
    )
    wait = select_wait_policy(
        ci_profile=profile["ci_profile"],
        execution_mode=execution_mode,
        safe_next_work_available=next_work["safe_work_available"],
        next_decision_depends_on_ci=next_decision_depends_on_ci,
        release_in_progress=release_in_progress,
        deploy_in_progress=deploy_in_progress,
        external_dependency_blocks=external_dependency_blocks,
        speculative_work_forbidden=speculative_work_forbidden,
    )

    remote = list(gates["gates"])
    local_budget = {"light"} if runner["contention"] else {"light", "moderate"}
    local = [gate for gate in remote if GATE_COST.get(gate) in local_budget]
    local_on_hold = [
        {"gate": gate, "cost": GATE_COST.get(gate, "unknown")}
        for gate in remote
        if GATE_COST.get(gate) == "moderate" and runner["contention"]
    ]

    observation = (
        post_merge_observation(
            merge_tree_validated_by_pr=merge_tree_validated_by_pr,
            main_adds_new_gate=main_adds_new_gate,
            main_status=main_status,
        )
        if unit_merged
        else {
            "role": "not_applicable",
            "blocks_next_unit": False,
            "investigate_on_red": True,
            "reason": "The unit has not merged yet; there is nothing on main to observe.",
        }
    )
    next_work_blockers = (
        list(remote)
        if wait["next_work_blocked"]
        else ["main CI is a real gate"]
        if observation["blocks_next_unit"]
        else []
    )

    return {
        "selected_mode": execution_mode,
        "ci_profile": profile["ci_profile"],
        "ci_profile_reason": profile["reason"],
        "ci_profile_escalated_from": profile["escalated_from"],
        "change_impacts": profile["change_impacts"],
        "ci_blocking_point": wait["ci_blocking_point"],
        "ci_wait_policy": wait["ci_wait_policy"],
        "ci_wait_reason": wait["reason"],
        "next_work_policy": next_work["next_work_policy"],
        "next_work": next_work,
        "local_gates": local,
        "remote_gates": remote,
        "deferred_gates": gates["deferred_gates"],
        "local_gates_on_hold": local_on_hold,
        "e2e_tier": gates["e2e_tier"],
        "publication_hold": wait["publication_hold"],
        "merge_blockers": remote,
        "next_work_blockers": next_work_blockers,
        "runner_policy": runner,
        "post_merge_observation": observation,
        "concurrency": concurrency_recommendation(unit_ref=unit_ref),
        "blocker_report": blocker_report(
            merge_blockers=remote,
            next_work_blockers=next_work_blockers,
            next_work=next_work,
            observation=observation,
        ),
    }


def blocker_report(
    *,
    merge_blockers: Sequence[str],
    next_work_blockers: Sequence[str],
    next_work: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> Dict[str, Any]:
    """State the three things separately, so no reader can fuse them.

    "Cannot merge" and "cannot keep working" were the same sentence in practice,
    and a run on `main` that only reports was read as a third gate. Each line
    below answers exactly one question.
    """

    merge = (
        "{} pending".format(", ".join(merge_blockers))
        if merge_blockers
        else "none"
    )
    if next_work_blockers:
        work = ", ".join(next_work_blockers)
    else:
        work = "none — {} permitted".format(next_work["next_work_policy"])
    return {
        "merge_blocker": merge,
        "next_work_blocker": work,
        "post_merge_observation": "main CI: {}".format(observation["role"]),
        "lines": [
            "MERGE BLOCKER: {}".format(merge),
            "NEXT-WORK BLOCKER: {}".format(work),
            "POST-MERGE OBSERVATION: main CI: {}".format(observation["role"]),
        ],
    }


def ci_decision_for_request(
    request: str,
    *,
    execution_mode: str = "standard",
    severe_harm_factors: Sequence[str] = (),
    sensitive_areas: Sequence[str] = (),
    context: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """The router's entry point: classify impacts from text, then decide.

    ``context`` carries what text cannot know — which runner this repository
    uses, whether the next unit depends on this one, whether a release is under
    way. Absent it, the answer is the throughput default: targeted gates, a
    background wait, and an independent next unit.
    """

    impacts = classify_change_impacts(
        request,
        severe_harm_factors=severe_harm_factors,
        sensitive_areas=sensitive_areas,
    )
    arguments: Dict[str, Any] = {
        "execution_mode": execution_mode,
        "impacts": impacts,
        "sensitive_areas": list(sensitive_areas),
    }
    for key, value in validated_ci_context(context).items():
        arguments[key] = value
    return ci_decision(**arguments)


#: Context fields the caller may supply, with the default each one falls back to.
#: The defaults are the documented "unknown" answers: an undeclared runner is
#: treated as sharing the machine, and an undeclared dependency is read as *not
#: declared dependent* — never as a confirmed dependency.
CI_CONTEXT_DEFAULTS: Dict[str, Any] = {
    key: value
    for key, value in (ci_decision.__kwdefaults__ or {}).items()
    if key not in {"execution_mode", "impacts", "sensitive_areas"}
}


def validated_ci_context(context: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Accept only known fields, of the right type, with the right values.

    Operational context is data, not prose. Letting it arrive as free text in
    the request is how "the runner is busy" became something the policy had to
    guess at.
    """

    resolved: Dict[str, Any] = {}
    for key, value in dict(context or {}).items():
        if key not in CI_CONTEXT_DEFAULTS:
            raise ValueError(
                "unknown ci context field: {!r}; known: {}".format(
                    key, ", ".join(sorted(CI_CONTEXT_DEFAULTS))
                )
            )
        default = CI_CONTEXT_DEFAULTS[key]
        if isinstance(default, bool) and not isinstance(value, bool):
            raise ValueError(
                "ci context field {!r} must be a boolean, got {!r}".format(key, value)
            )
        if isinstance(default, str) and not isinstance(value, str):
            raise ValueError(
                "ci context field {!r} must be a string, got {!r}".format(key, value)
            )
        if key == "runner_kind" and value not in RUNNER_KINDS:
            raise ValueError(
                "unknown runner kind: {!r}; known: {}".format(
                    value, ", ".join(RUNNER_KINDS)
                )
            )
        if key == "requested_profile" and value is not None and value not in CI_PROFILES:
            raise ValueError(
                "unknown ci profile: {!r}; known: {}".format(
                    value, ", ".join(CI_PROFILES)
                )
            )
        if key == "planned_local_workloads" and isinstance(value, str):
            raise ValueError(
                "ci context field 'planned_local_workloads' must be a list of strings"
            )
        resolved[key] = value
    return resolved
