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

### Applying a review

Each review gate has exactly one formal writer, and it validates and applies in
the same operation:

| Gate | Writer | Refused by |
| --- | --- | --- |
| `spec_compliance` | `framework-next validate-spec-review` | `gate-status` |
| `code_quality` | `framework-next validate-quality-review` | `gate-status` |

Validation and application are one act. A durable state in which a review has
been validated but not recorded is the same half-truth the framework refuses
everywhere else: the verdict exists and nothing in the persisted state can be
asked about it. `--check` runs every guard and writes nothing.

Classifications map onto the gate states the transition guards already read. No
vocabulary is invented — there is no `REJECTED`, because `CHANGES_REQUIRED` is
the rejection this framework has.

| Classification | Gate state |
| --- | --- |
| `PASS` | `spec_compliance: passed` |
| `PASS_WITH_NOTES` | `spec_compliance: passed_with_notes` |
| `BLOCKED` | `spec_compliance: blocked` |
| `APPROVED` | `code_quality: approved` |
| `APPROVED_WITH_NOTES` | `code_quality: approved_with_notes` |
| `CHANGES_REQUIRED` | `code_quality: changes_required` |

Applying a review never moves the lifecycle. A spec approval leaves the phase
and the task in `reviewing` and points at `run-quality-review`. A quality
approval moves the task to `reviewed` — without it `reviewing → verifying` would
be refused at the index, because `TASK_STATUS_TRANSITIONS` has no
`reviewing → verifying` edge — and points at `verify-phase`. The transition
itself keeps its own actor, reason and guards.

An approving quality review cannot carry a finding that names a
`required_change`: a change that has not been made is not an approval, and
recording the gate would leave the demand with nothing to enforce it. Notes
without a required change stay legal — that is what `APPROVED_WITH_NOTES` is
for.

A blocking verdict records the gate, opens the blockers with their evidence and
points at `return-to-execution`; it does not perform it either. After the
correction, `transition --to executing` retires all five review gates, so
**both** reviews are earned again — no approval is inherited. The review that
approves the corrected work is what closes the blocker it raised; the earlier
review stays in `history` as the record of the finding. A code correction that
does not change the contract is not an amendment and must not go through
`amend-plan`.

Every application requires independence (reviewer ≠ executor), an inspected
diff, non-empty `files_inspected` and `evidence_inspected`, and correspondence
with the work actually under way: task, phase, `plan_revision`, reviewed commit,
bound branch, and a working tree that carries no product changes the reviewer
did not read. Reviews are stamped with the plan revision they were granted
under, so an approval from before an amendment is history and a revision-1
review is refused against revision 2.

Repeating the same application is a no-op. Repeating it with a different report,
result, reviewer, commit or revision is refused — including a report edited
after it was applied, because the document's digest is part of the identity.

Four documents move together — the ledger, `REVIEW.md`, `TASKS.md` and
`STATE.md`, in that order — and all four are restored byte for byte if any step
fails. The order is chosen by which half-written outcome is safest: a ledger
event and a review entry without the gate describe a review that did not take
effect, and repeating the command completes it. The reverse — a passed gate with
no trail — is the outcome this operation exists to make impossible. A process
killed between two writes is the residual risk; `validate` reports the state as
clean and the gate still blocks, so the command is simply run again.

The command refuses evidence that does not resolve to a file inside the project,
and evidence under `.agent/phases/<slug>/` that belongs to a phase other than the
active one. Repeating a change that already holds is a no-op; repeating it with a
different decision or evidence is refused rather than silently rewritten. Every
accepted change is appended to the phase's existing evidence ledger.

### Gates and their records

`gates` is the map a guard reads; `gate_records` is the ledger index behind it.
They used to drift: re-entering `executing` reset the map and left the records
alone, so a state could hold `acceptance: pending` beside a record still saying
`passed`, and which one answered the question depended on which code path
looked. Both now move together, in the transition and in `amend-plan` alike.

Every record written since carries a `plan_revision` stamp — the revision the
judgement was made against, because a gate approves a contract and contracts are
versioned. `validate` reports `gate-record-divergence` when a **stamped** record
disagrees with the map. Records written before the stamp existed are left alone:
their absence identifies them, and no project needs migrating.

### What `shipped` means

`shipped` means the phase is integrated and closed in the controlled development
cycle. It does **not** mean released to production. External blockers — secret
managers, production benchmarks, TLS termination — stay recorded as open
blockers against production readiness without reopening a phase that is
genuinely finished, and `verifying → ready_to_ship` already refuses to move
while lifecycle blockers are open.

## Starting a task

`execute-task -> <id>` is an operation, not only a recommendation.
`framework-next start-task` performs it.

`current_task.id` has no other prospective writer, and that is deliberate.
`initialize_project` and `activate-phase` clear it; `reconcile-phase` fills it
from work already `verified`; everything else touches only `.status`. Without
`start-task`, a phase that reached `planned` honestly had no legal move —
`task-status` refuses a task that is not yet current, and `transition --to
executing` refuses because none is selected.

**The target comes from the kernel, not the operator.** `start-task` reads it
from `determine_next_operation`; a `--task-id` may be passed, but only as a
confirmation that must match. There is no `select-task`, and no way to name a
different task.

Selection and start are one operation because the state between them is not a
state the lifecycle can read: a selected task that is not executing and not
bound to a branch. The selection is made in memory and spent immediately on the
guarded `planned → executing` transition, which owns the hard checks — plan
seal, plan gate, risk, dirty worktree, detached HEAD, integration branch,
contract and dependencies — and captures the execution binding.

| Writer | Effect on `current_task` |
| --- | --- |
| `start-task` | selects the eligible task and starts it, with binding |
| `task-status` | changes `.status` of the task already current |
| `transition` | changes `.status` as the phase moves |
| `amend-plan` | returns the task under way to `executing`, binding intact |
| `reconcile-phase` | back-fills from work already `verified` |
| `activate-phase`, `init` | clear it |

Three documents move together: `TASKS.md`, `STATE.md` and the phase ledger. The
first two are read as bytes before the first write and restored if any later
step fails, the ledger append included — so a failure cannot leave a phase
executing a task the index still calls pending, nor an execution with no trail.
Repeating a start that already holds is a no-op; repeating it for another task,
branch or worktree is refused.

After starting, the next operation is `resume-task`, and no other task becomes
eligible while one is under way.

## Branch and worktree affinity

Affinity begins with execution, not with planning. `git.working_branch` records
the branch a project or phase was created on; it is not a claim about where the
work must happen, and treating it as one made a merged planning branch outlive
its own work — leaving the integration branch permanently invalid in the one
state where nothing had started yet.

| Class | States | Branch affinity |
| --- | --- | --- |
| Bound | `executing`, `reviewing`, `verifying` | strict — the checkout must be the bound branch |
| Unbound | `proposed`, `discussing`, `specified`, `planned`, `ready_to_ship`, `shipped`, `cancelled`, `superseded` | none |

`planned` is deliberately unbound: a sealed plan is an approved plan, not a
running one, and the implementation branch may not exist yet. The rest of the
`git` section is still validated in every state — repository presence and
worktree resolution do not depend on affinity.

Starting a task is what binds it. `transition --to executing` reads the branch
from Git and records it on `current_task.execution` together with the task id,
the portable worktree value, a timestamp and the actor. It is **captured, never
declared**: no command accepts a branch argument, so the binding cannot name a
branch that is not checked out. Starting is refused on a detached HEAD and on
the project's own `base_branch` — the integration branch is where work arrives,
not where it is written.

While bound, a mismatch is an error: switching to the integration branch, to
another feature branch, or detaching HEAD all fail, as does a binding that names
a different task or a `git.worktree` that changed underneath it.

Leaving the bound states releases the binding into `git.last_execution`, which
is history and is never validated. That is what keeps the two meanings apart:
`current_task.execution` is the branch work **must** be on, `git.last_execution`
is the branch work **was** on. A merged branch may then be deleted and the
integration branch still validates — no hand-edit, at any point.

States written before the binding existed fall back to `git.working_branch`
while in bound states, so a project already mid-execution keeps its protection
and needs no migration.

When a bound checkout has moved, the next operation is
`restore-execution-branch` targeting the bound branch — not `repair-state`.
The state is right and the checkout is wrong; pointing at `STATE.md` would
invite an edit that hides the divergence. `validate` never writes, in any state.

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

## Amending the plan of a task under way

A contract can be wrong, and the fact that proves it is often produced by the
work itself — a CI run reaching paths no local verification reaches is the
ordinary case. `framework-next amend-plan` re-seals `PLAN.md` and `TASKS.md`
**in place**, without pretending the work has not started.

Before it existed, the only routes were both dishonest. `seal-plan` refuses
outside `specified`, and `reconcile-phase` describes work already integrated, so
reaching a second seal meant manufacturing a `BLOCKED` review to obtain the
blocker that `blocked` requires, then returning to `specified` — which claims
nobody had begun and releases the execution binding — or editing the fingerprint
by hand, which forges the one thing the seal exists to prove. **Neither is a
replanning mechanism, and a `BLOCKED` review must never be used as one.**

A second dead end sat underneath: `TASK_STATUS_TRANSITIONS` gives `verified` no
outgoing edge, so a task whose local verification passed and whose CI then
failed had no way back into execution at all. `amend-plan` owns that move, and
the shared table stays closed so nothing else can un-verify a task.

It applies only from `executing`, `reviewing` or `verifying`, with a
`current_task` that is not integrated, over a plan that was already sealed and
whose artifacts have actually changed, against a decision recorded in
`DECISIONS.md` and an evidence file belonging to the active phase, from the
checkout the execution is bound to. Every other state error refuses the
amendment rather than being sealed over — the stale fingerprint is the one
condition it is allowed to find, because repairing it is the point.

**The fingerprint is computed, never supplied.** It comes from
`compute_plan_fingerprint`, the same function `seal-plan` and `validate` use,
over the artifacts as they are on disk. There is no argument through which one
could be named. `--version` is optional and is a confirmation, not a choice: the
kernel advances the revision by one and refuses anything else.

What it moves and what it keeps:

| Kept | Moved |
| --- | --- |
| `current_task.id` | `plan_revision` advances one revision |
| `current_task.execution`, byte for byte | phase and task return to `executing` |
| `specification`, `plan_quality` | the five review gates reopen to `pending` |
| every ledger event already written | `next_action` becomes `resume-task` |

The binding is carried across, not released and recaptured: the work did not
restart, so `bound_at` and `bound_by` still describe when and by whom it began,
and nothing is archived into `git.last_execution`.

`specification` and `plan_quality` are deliberately preserved. An amendment made
under a recorded decision is the plan process working, not evidence against it —
and reopening `plan_quality` would strand the phase, since that gate is what
`specified → planned` and `planned → executing` require.

**An old approval belongs to the old revision.** Gate records carry a
`plan_revision` stamp, and reopening pushes the previous status onto the
record's `history` with the revision it was granted under. Gates written by the
review appliers keep no record of their own, so their previous values are
recorded in the amendment's ledger event instead. Nothing is deleted.

No blocker is required or invented. A recorded decision and real evidence
already explain the amendment, and existing blockers are left untouched — they
stay open until whatever closes them formally does.

Three documents move together, and the write order is ledger, index, state, with
all three restored from bytes if any step fails. A process that dies mid-write
leaves at most a ledger event without the re-seal: `validate` still reports the
stale fingerprint, the operator sees both, and repeating the command is a no-op
when the amendment landed and a completion when it did not.

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
