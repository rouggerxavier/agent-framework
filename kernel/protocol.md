# Agent Framework Kernel Protocol

## Adaptive entry

Apply `adaptive-execution-policy.md` before this lifecycle. `fast` is the default
for ordinary work, `standard` uses a short proportional flow, and the lifecycle
below is mandatory only for `critical`. The complete kernel is a capability, not
the default entry path.

## Purpose

The kernel coordinates existing skills, workflows, rubrics, and templates through
persistent project artifacts. Conversation memory may help an executor, but it is
never the source of truth for lifecycle state, task scope, decisions, blockers, or
evidence.

## Operational cycle

```text
Route
→ Ground
→ Discuss
→ Specify
→ Plan
→ Execute
→ Review
→ Verify
→ Ship
→ Learn
```

| Stage | Primary responsibility | Persistent output |
| --- | --- | --- |
| Route | `agent-framework-router` selects the entry asset | next operation in `STATE.md` |
| Ground | `project-context-loader` observes repository facts | `CONTEXT.md` |
| Discuss | planner resolves material uncertainty | `PROJECT.md`, decisions, assumptions |
| Specify | planner freezes requirements and acceptance | `REQUIREMENTS.md`, phase `SPEC.md` |
| Plan | `workflow-planner` creates task graph and contracts | `PLAN.md`, `TASKS.md` |
| Execute | `workflow-runner` selects; `task-runner` implements | result and `EVIDENCE.md` entries |
| Review | independent reviewers assess spec, then quality | `REVIEW.md`, evidence entries |
| Verify | verifier traces requirements to fresh evidence | verification gates and ledger |
| Ship | Git/release skills apply final gates | commit/PR/release evidence |
| Learn | maintainer records reusable decisions or follow-up | decisions, handoff, task memory |

## Roles and authority

- Router: chooses the protocol entry point. It does not plan or implement.
- Planner: owns workflow selection, risk classification, dependency graph, task
  contracts, and plan revisions. It cannot approve its own plan without the
  `plan-quality-checker` gate.
- Runner: owns eligible-task selection, context packages, state transitions,
  review routing, and evidence registration. It does not redesign the plan.
- Implementer: may produce `implementation_complete`; it may not mark work
  `reviewed` or `verified`.
- Spec compliance reviewer: independently checks code and evidence against the
  contract, spec, requirements, and decisions.
- Code quality reviewer: runs only after spec compliance and checks engineering
  quality using the relevant rubrics.
- Verifier: owns acceptance and phase verification and alone may authorize
  `ready_to_ship`.

One actor may perform multiple roles only when independence is not required.
The implementer must never act as either independent reviewer for the same task.

## Persistent artifacts

An initialized consumer project owns `.agent/STATE.md` plus the project and phase
documents defined in `templates/`. `STATE.md` is the compact index; it references
full documents and must not duplicate their prose.

- Decisions are appended to `DECISIONS.md` with ID, date, status, context,
  decision, consequences, and actor.
- Claims, failures, commands, reviews, waivers, and acceptance evidence are
  appended to the active phase `EVIDENCE.md`.
- Plan changes are recorded as decisions and revisions to `PLAN.md`/`TASKS.md`.
- Handoffs complement `STATE.md`; they never override it.

`STATE.md` is shared state and must stay portable. Branch, commit, milestone,
phase, tasks, decisions, evidence, gates, and repository-relative references
belong there. Machine-specific facts — absolute paths, caches, sockets, local
executables — must not be persisted. The local clone path is never shared state:
Git already knows it, so it is discovered at runtime instead.

## Repository root resolution

`git.worktree` is portable. `"."` means "the Git repository that contains
`.agent/`"; `null` means no worktree is registered. Absolute paths are a legacy
format that still loads and is reported for explicit normalization.

The runtime authority is `git rev-parse --show-toplevel`, evaluated from the
project root, never the persisted string. Resolution proves that the repository
owns the state before using it: the real location of `.agent/` must lie inside
the repository Git reports, so a `.agent/` symlinked in from another project is
refused, as is any value that escapes the clone with `..`. Nothing resolved this
way is ever written back to the versioned file.

## Start and resume

1. Resolve the nearest initialized project root, falling back to
   `git rev-parse --show-toplevel`.
2. If `.agent/STATE.md` is absent, return to `agent-framework-router`; initialize
   only after a concrete persistence need or explicit `critical` selection.
3. Load `STATE.md` and every referenced artifact needed by the current phase.
4. Observe Git branch, commit, and working-tree changes.
5. Reject missing, escaping, malformed, or stale references.
6. Select exactly one next operation with `framework-next`.
7. Invoke the required skill only after its preconditions are satisfied.

If the current commit differs from the grounded context during an active phase,
the context must be revalidated and persisted before execution continues.
Conversation summaries with conflicting information are stale; persistent state
and direct repository evidence win. If persistent artifacts conflict with direct
evidence, block and repair the artifacts rather than guessing.

## Blocking and recovery

A blocker contains an ID, summary, evidence, owner or escalation target, unblock
conditions, and the state to resume. Entering `blocked` records `blocked_from`.
Resume is allowed only after all blockers are resolved and only to that recorded
state. Investigative blockers route to `persistent-debug-session`.

Failed spec or quality review returns `reviewing → executing` with recorded
evidence. Failed verification returns to the state that owns the defect:
`executing` for implementation corrections or `reviewing` for invalid review
evidence. Earlier approvals are not reused automatically after a correction.
Successful task verification may select the next eligible contract through
`verifying → executing`; phase verification begins when no task remains.

## Completion rule

A task is complete only after implementation, mandatory tests or a valid waiver,
self-review, spec compliance review, code quality review, acceptance evidence,
and required commit handling are recorded. A phase is complete only after the
verifier confirms all acceptance criteria, required checks, resolved blockers,
and reviewed waivers. Passing tests alone, an implementer claim, or a prose
summary is never sufficient.

All lifecycle mutations must obey `state-machine.md`; execution and evidence
rules are defined in the remaining kernel policies.
