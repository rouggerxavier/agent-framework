# Adaptive Execution Policy

```text
Fast optimises speed.
Standard organises ordinary development.
Critical protects the application from grave damage.
```

The framework preserves the complete persistent kernel and does not apply it to
every task. Its job is memory, scope and objective guardrails — not to replace
the reasoning of the model executing the work, and not to charge more ceremony
than the feature costs to build.

## What the framework is for

- keeping context across sessions;
- holding decisions and requirements that are expensive to rediscover;
- stopping parts of the scope from being forgotten;
- continuity and traceability;
- preventing objective mistakes, such as working on the wrong task or branch;
- asking for verification proportional to the risk.

Persistence is never the thing to cut. What scales with the mode is *ceremony*.

## Selection rule

```text
Grave damage if it fails      → critical
Short, contained, low impact  → fast
Everything else               → standard
```

`standard` is the default and the resting state of the router. `fast` is claimed
with positive evidence that the work is short and contained; `critical` is
claimed with a named grave-damage path. The router accepts `--fast`,
`--standard`, `--critical` and `--auto`; no option means `auto`.

Expected distribution, as a calibration reference and not a quota:

| Mode | Share |
| --- | --- |
| `fast` | ~30% |
| `standard` | ~65–70% |
| `critical` | ~1–5% |

## Classification criteria, in order

1. potential damage of a failure;
2. sensitivity of the affected area;
3. reversibility;
4. blast radius;
5. complexity and size;
6. estimated time.

Time separates `fast` from `standard` and nothing else. A task that runs for
hours can stay `standard`. A ten-minute change inside the payment or
authentication core can be `critical`.

A sensitive area (authentication, sessions, authorization/permissions, tenant
isolation, financial data, personal data, migrations, secrets, account
recovery, billing, integrations that write important data) never escalates to
`critical` by itself, but it does rule out `fast`: the floor for work touching
one is `standard`.

```text
1. severe harm identified                      → critical
2. sensitive area identified, no severe harm    → at least standard
3. short, contained, non-sensitive work         → may be fast
4. everything else                              → standard
```

## Fast

Short, simple, localized work — around ten minutes, few files, predictable
behaviour, low impact, easy to revert, **no sensitive area**, no architectural
decision, quick and proportional tests.

Typical: small bugs, visual adjustments, copy fixes, simple redirects, missing
tests, small helper changes, localized improvements inside an existing feature.

A request for `fast` that touches a sensitive area is rejected and raised to
`standard`, with the reason `fast rejected: sensitive area requires at least
standard`. The area alone still does not make it `critical` — that needs a
named severe harm factor.

Fast is not the absence of quality. It is the absence of ceremony: the context,
the result and the tests are preserved; the planning cycle, the seal, multiple
reviews and intermediate gates are not.

## Standard

Most medium and large features: more than fifteen minutes, several files,
possibly more than one session, real planning and context, a complete feature,
ordinary development risk, understandable scope and acceptance criteria.

Frontend and backend features, onboarding, new entities and endpoints,
controlled migrations, authorization following established patterns,
integrations with known contracts, administrative flows, imports, larger but
bounded refactors, changes that need E2E.

A standard task may need a plan, `allowed_files`, persisted decisions, targeted
tests, E2E, a self-review, one independent review, and CI. **None of those turn
it into `critical`.**

### Rollback, proportional to the change

`fast` never needs a formal rollback — the change only has to be trivially
reversible.

`standard` owes a rollback or mitigation plan only when it is applicable:

- a migration;
- writing, transforming, or deleting data;
- an incompatible change;
- an external integration with persistent effects;
- an infrastructure change;
- a production operational change;
- a launch that needs a feature flag;
- a relevant, hard-to-undo regression risk.

For ordinary standard work — a frontend feature, a new screen, a navigation
flow, onboarding without destructive persistence, an additive endpoint, a
bounded refactor, tests, interface tweaks — the field is optional, or
`not_applicable` with a short reason.

`critical` always owes a rollback or containment plan. When a real rollback is
impossible, it owes containment instead: a feature flag, a kill switch, a
restore, a recovery procedure, plus an explicit justification.

## Critical

Reserved for changes where a defect causes grave damage:

- breaking the authentication or session core;
- allowing intrusion or privilege escalation;
- exposing data across tenants;
- serious data loss or corruption;
- moving money incorrectly;
- compromising a payment gateway;
- material financial loss;
- a destructive or hard-to-reverse migration;
- compromising cryptography or secret management;
- breaking account recovery;
- taking down an essential part of production;
- an irreversible operation with a large blast radius.

It also covers work that is genuinely oversized and coupled — but only when it
cannot be split into standard units safely. When it can be split, split it and
classify each unit.

`critical` is **not** justified by: the feature being large, indirectly touching
authentication, having a migration, touching permissions, involving financial
data, carrying risk, needing many tests, or changing many files. Those are areas
and sizes, not damage.

The executable vocabulary of grave-damage paths is
`SEVERE_HARM_FACTORS` in `kernel/runtime/execution_modes.py`. An escalation names
one of them.

## Granularity

The mode belongs to the **task**. One phase may hold `fast`, `standard` and
`critical` tasks at once, and a critical task does not raise the rigour of its
neighbours.

Resolution is most-specific-wins, never the maximum:

```text
task override (STATE.md) → task contract → phase default → project default
```

- a task declares `execution_mode` in its contract in `TASKS.md`;
- a phase declares `default_execution_mode` in its `TASKS.md` frontmatter;
- the project's `execution_mode` in `STATE.md` is a **default**, not a floor.

## Escalation and reduction

`framework-next set-execution-mode` records a change of classification with its
justification, for one task (`--scope task --task-id`) or for the project default
(`--scope project`). It writes to `STATE.md` and the evidence ledger; it never
rewrites the sealed plan, a review, or an existing evidence entry.

- **Escalating to `critical`** costs a named grave-damage path (`--risk`) plus a
  reason. "It feels risky" is not a classification.
- **Reducing** costs a plain reason. An over-classification is a mistake to
  correct, not a decision to defend.

## Execution matrix

| Capability | Fast | Standard | Critical |
| --- | --- | --- | --- |
| Persistent state | no | optional by concrete need | required |
| Formal spec | no | lightweight | required |
| Task contract | no | proportional | complete |
| Plan seal | no | no | required |
| Evidence ledger | no | lightweight or none | required |
| Independent reviews | 0 | 1 (integrated) | 2 (split) |
| Worktree | no | conditional | proportional |
| Review | integrated/light | integrated/normal | split/deep |
| Verification | targeted | proportional | complete |

Inside the persistent kernel the same table applies per task:

| Obligation | Fast task | Standard task | Critical task |
| --- | --- | --- | --- |
| `allowed_files` and acceptance | yes | yes | yes |
| `read_first`, `forbidden_changes`, `requirements`, `runtime_verification` | optional | optional | required |
| Rollback strategy | optional (trivially reversible) | proportional — required only when applicable | required (or containment) |
| Self-review checklist | core checks | full | full |
| Plan seal for the phase | not required | not required | required |
| Reviews before `verifying` | none beyond self-review | one integrated | spec **and** quality |

A phase owes a seal when any of its tasks is `critical`. A phase that already
carries a seal keeps being held to it — lowering a mode never lets a sealed plan
be rewritten under its own approval.

## Guards by mode

**Fast** — right task, right branch when applicable, scope, proportional tests,
result, short handoff. No formal seal, no multiple reviews, no evidence for each
transition, no intermediate gates.

**Standard** — context and decisions, contract and acceptance criteria,
`allowed_files` when useful, branch, tests, self-review, one proportional review,
CI, continuity across sessions. Not two independent reviews, not a plan revision
and gate for every small correction, not evidence for every status, not a
lifecycle as heavy as critical.

**Critical** — the complete lifecycle: strong alignment, formal plan, explicit
decisions, checkpoints, rollback plan, independent reviewers, strict gates,
evidence, E2E and complete validation, approval before advancing.

The templates stay available; instantiate them only when the selected row calls
for them:

| Template | Fast | Standard | Critical |
| --- | --- | --- | --- |
| Project state | no | optional | yes |
| Roadmap | no | no by default | yes |
| Phase spec | no | lightweight/optional | yes |
| Phase plan | no | short plan | yes |
| Task contract | no | proportional | yes |
| Evidence ledger | no | optional and summarized | yes |
| Separate review | no | no | yes |
| Handoff | no | when needed | yes |

## Verification budget

```yaml
verification_budget:
  fast:
    target_ratio: 0.20
    max_full_review_passes: 1
  standard:
    target_ratio: 0.30
    max_full_review_passes: 1
  critical:
    target_ratio: null
    max_full_review_passes: proportional
```

Ratios are operational guidance, not time accounting. When the budget is
exceeded, check for concrete residual risk, stop speculative verification,
record non-blocking notes, and finish if important acceptance criteria are met.

## Session scope and checkpoints

Large work is split into coherent units before execution starts. A session
delivers one phase or one functional slice and stops at a checkpoint; it never
runs several complete phases without an explicit request.

```yaml
session_scope:
  max_units_per_session: 1
  soft_checkpoint_minutes: 30
  hard_checkpoint_minutes: 45
  grace_minutes: 10
  auto_advance_to_next_phase: false
```

Around the soft checkpoint, finish the atomic unit in progress, commit it, and
write the handoff instead of continuing indefinitely. The limits are adaptive: a
correction that is minutes from done is finished first, and a unit still landing
inside the budget is not cut in half. Past the budget with substantial work
remaining, close the last coherent unit and stop.

Volume is never a blocker. Remaining units are deferred to further sessions the
user resumes explicitly, with no extra ceremony beyond the handoff. When the user
asks for a complete run, the full mode stays available and the session is not cut
at a checkpoint.

## Review and correction rounds

```yaml
review_rounds:
  max_review_rounds: 1
  max_correction_rounds: 1
  reviewers_per_diff:
    fast: 1
    standard: 1
    critical: 2
```

One normal review round and one correction round is the budget. Do not invoke
several reviewers over the same diff when one is enough; an extra reviewer needs
stated evidence that the first could not cover the risk. If blockers survive the
correction round, escalate with evidence instead of looping.

Below `critical`, one reviewer closes the round: the same pass judges conformance
and quality, and the second gate is recorded as `not_required` against that
review document rather than left pending.

## Test scope

Verification is proportional to the diff:

- targeted tests for a small local change, even when the suite was green before;
- affected areas and their integration points for a broader diff;
- the complete suite only at a real phase closure or when opening the PR.

Do not replay the whole suite after every small local change. When an E2E test
fails on a selector, fixture, or assertion, reuse the running environment and
rerun the affected spec; rebuild Docker or the E2E stack only when the
environment is down or the failure comes from the build, dependencies, image, or
schema.

## Review findings

Use `BLOCKER`, `IMPORTANT`, `NOTE`, or `SPECULATIVE`. A blocker must show:

```yaml
reachability:
likelihood:
impact:
supporting_evidence:
```

It must also concern an explicit requirement, security, data loss/corruption, a
reproducible regression, material operational impact, or failed acceptance.
`SPECULATIVE` never blocks. After a localized correction, review the new diff,
affected criteria, and related regressions rather than repeating the whole audit.

## Context reuse

After relevant files have been read, pass reviewers only:

```yaml
goal:
mode:
diff:
files_changed:
tests_run:
acceptance_or_expected_behavior:
known_risks:
```

Repeat full grounding only after a material commit change, scope change, newly
discovered core files, stale context, or a contradiction.

The executable reference is `kernel/runtime/execution_modes.py`; routing is
side-effect free and never creates `.agent/`.
