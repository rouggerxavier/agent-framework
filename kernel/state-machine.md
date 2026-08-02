# Kernel State Machine

`STATE.md.status` is the canonical lifecycle value. When a phase is active,
`phase.status` mirrors it. The runtime in `kernel/runtime/state_machine.py`
enforces this table and the guards below.

## States

| State | Meaning |
| --- | --- |
| `proposed` | Project or milestone exists but discovery has not started. |
| `discussing` | Material requirements or decisions remain open. |
| `specified` | Requirements and acceptance are frozen for planning. |
| `planned` | Task graph and contracts passed the plan gate. |
| `executing` | Exactly one task per executor is active. |
| `reviewing` | Independent review is active or pending. |
| `verifying` | Phase-level goal and runtime verification is active. |
| `ready_to_ship` | Acceptance and required checks passed. |
| `shipped` | Configured integration or release completed. |
| `blocked` | Progress is prohibited until explicit conditions are met. |
| `cancelled` | Work intentionally stopped without replacement. |
| `superseded` | A newer milestone, phase, or decision replaced this work. |

## Allowed transitions

| From | Allowed destinations |
| --- | --- |
| `proposed` | `discussing`, `blocked`, `cancelled`, `superseded` |
| `discussing` | `specified`, `blocked`, `cancelled`, `superseded` |
| `specified` | `discussing`, `planned`, `blocked`, `cancelled`, `superseded` |
| `planned` | `specified`, `executing`, `blocked`, `cancelled`, `superseded` |
| `executing` | `reviewing`, `blocked`, `cancelled`, `superseded` |
| `reviewing` | `executing`, `verifying`, `blocked`, `cancelled`, `superseded` |
| `verifying` | `executing`, `reviewing`, `ready_to_ship`, `blocked`, `cancelled`, `superseded` |
| `ready_to_ship` | `verifying`, `shipped`, `blocked`, `cancelled`, `superseded` |
| `shipped` | `superseded` |
| `blocked` | recorded `blocked_from`, `cancelled`, or `superseded` |
| `cancelled` | `superseded` |
| `superseded` | none |

Every destination not listed is prohibited. The runner requests transitions;
the kernel validates them. Planner-owned transitions end at `planned`; the
verifier alone requests `ready_to_ship`; shipping skills request `shipped`.

## Transition preconditions and evidence

| Transition | Required preconditions and evidence | Responsible role |
| --- | --- | --- |
| `proposed → discussing` | project initialized; grounding started or unknowns recorded | planner |
| `discussing → specified` | requirements and acceptance persisted; material decisions resolved or explicitly open | planner |
| `specified → planned` | plan and full task contracts exist; dependencies are acyclic; risk and test policy recorded; `plan-quality-checker` passed | planner + plan gate |
| `planned → executing` | plan gate passed; dependencies satisfied; selected task contract exists; risk classified; Git/context valid | runner |
| `executing → reviewing` | result is `implementation_complete`; required tests/waiver and acceptance evidence exist; self-review passed | runner |
| `reviewing → executing` | spec is `BLOCKED` or quality is `CHANGES_REQUIRED`; blocker contains direct evidence | reviewer + runner |
| `reviewing → verifying` | spec is `PASS`/`PASS_WITH_NOTES`; quality is `APPROVED`/`APPROVED_WITH_NOTES`; no blocker | runner |
| `verifying → executing` | verification failed with evidence, or current task is verified and the next eligible contract/dependencies are valid | verifier + runner |
| `verifying → reviewing` | review/evidence defect recorded; affected review invalidated | verifier + runner |
| `verifying → ready_to_ship` | every acceptance criterion has evidence; required verification passed; blockers resolved; waivers reviewed | verifier |
| `ready_to_ship → shipped` | release gate passed and configured commit/PR/handoff completed | shipping role |
| `* → blocked` | blocker, evidence, unblock condition, and `blocked_from` recorded | current role or runner |
| `blocked → blocked_from` | blockers empty; repository/state revalidated | runner |

Plan revisions use `planned → specified`, record a decision, update plan/contracts,
rerun the plan gate, then return through `specified → planned`. They never mutate
an executing workflow silently.

## Reconciliation

A phase whose work is already committed but was executed before the phase had an
executable index cannot be expressed by the ordinary lifecycle: a plan may be
sealed only from `specified`, and a phase may be initialized only before
execution starts. `framework-next reconcile-phase` covers that case alone. It
re-points the phase artifacts, re-seals `PLAN.md` and `TASKS.md` under a recorded
decision with an increased revision, and leaves the status at `verifying` so the
`verifying → ready_to_ship` gate still decides.

It refuses to run when any task of the phase is unfinished, a blocker is open,
the decision is absent from `DECISIONS.md`, the evidence file is missing, the
plan revision does not increase, or the working tree carries uncommitted product
changes. Reconciliation records finished work; it never approves it.

## Gates

Gates are read by transition guards; `ready_to_ship → shipped` is the one that
reads `release`. `framework-next gate-status` is the only formal writer for the
gates that have no dedicated command, and it never performs the transition it
unblocks — passing the release gate and shipping stay two deliberate acts.

| Target | Cost | Meaning |
| --- | --- | --- |
| `passed` | decision + evidence | a guard may trust this gate |
| `not_required` | decision + evidence | the gate does not apply to this phase |
| `failed` | evidence | recorded observation, not an approval |
| `blocked` | evidence | the gate cannot be evaluated yet |

`pending` is not a valid target: it is the initial value, and accepting it would
let a recorded gate be un-recorded through the same door that wrote it. The
lifecycle already resets gates when a task starts executing.

`spec_compliance` and `code_quality` are refused. They belong to
`validate-spec-review` and `validate-quality-review`, which validate the review
document itself; a second writer would let a review be recorded without one
being written.

The command refuses evidence that does not resolve to a file inside the project,
and evidence under `.agent/phases/<slug>/` that belongs to a phase other than the
active one. Repeating a change that already holds is a no-op; repeating it with a
different decision or evidence is refused rather than silently rewritten. Every
accepted change is appended to the phase's existing evidence ledger.

### What `shipped` means

`shipped` means the phase is integrated and closed in the controlled development
cycle. It does **not** mean released to production. External blockers — secret
managers, production benchmarks, TLS termination — stay recorded as open
blockers against production readiness without reopening a phase that is
genuinely finished, and `verifying → ready_to_ship` already refuses to move
while lifecycle blockers are open.

## Phase rotation

A milestone is often contracted before it is executed, so the next phase already
has SPEC, PLAN, TASKS and a ledger on disk. Nothing in the ordinary lifecycle
reaches it: `init-phase` refuses an existing directory (running it would
overwrite those documents), `seal-plan` only seals the active phase, and
`reconcile-phase` requires finished work. `framework-next activate-phase` covers
that case alone.

It requires the current phase to be `shipped` or `superseded`. `ready_to_ship`
is excluded deliberately: it means a ship decision is still pending, and
rotating away would strand it. The target phase must exist with all six
artifacts, appear in the roadmap, differ from the active phase, hold no task in
an executed state, and carry a structurally valid task graph.

Where it lands is what keeps it honest. The plan counts as sealed only when the
stored fingerprint, recomputed against the phase being activated, still matches.
Anything else is an unsealed plan: `plan_revision` is reset and the state lands
on `specified`, so the plan gate is paid again through `seal-plan`. The next
operation is `build-plan`, never `execute-task` — a contracted plan is not an
approved one.

The phase left behind keeps every document and is appended to
`completed_phases`. Rotation moves the pointer; it never rewrites history.

## Failure behavior

- A blocking spec review or required quality change returns the task to
  `executing`. The failing review and correction history remain in the ledger.
- A test failure during execution stays `executing`; repeated investigation may
  enter `blocked`.
- After a task is verified, `verifying → executing` may select the next eligible
  task. When no task remains, phase verification continues toward `ready_to_ship`.
- A verification failure returns to `executing` for code defects or `reviewing`
  for review defects. All invalidated approvals must be rerun.
- `ready_to_ship` is rejected when any blocker, missing acceptance evidence,
  failed required check, or unreviewed waiver exists.
