# Multi-Agent Orchestration Policy

## Purpose

This policy governs one orchestrator coordinating multiple coding agents, test
agents and reviewers. It is designed for environments such as Maestri where one
control agent can dispatch work to multiple isolated terminals.

The orchestration layer does not replace the existing task lifecycle. It decides
who receives each operation, what context they receive, what they are allowed to
change, and when control returns to the orchestrator.

## Single control plane

Exactly one orchestrator owns global coordination for a run.

Only the orchestrator may:

- change orchestration state;
- select or reassign work;
- revise the plan or task graph;
- accept recorded decisions;
- route findings back to an implementer;
- decide that a task is ready for the next role;
- escalate a material decision to the user.

Workers may edit product files inside their dispatch scope. They do not compete
for lifecycle ownership and do not silently redesign the plan.

## Worker roles

The default team is:

- **developer** — implements the authorized task and performs self-review;
- **tester** — designs/runs targeted validation and reports evidence;
- **reviewer** — independently checks spec compliance and code quality;
- **specialist** — optional temporary worker for security, migration, UI, infra,
  research or another narrow concern.

A model is not a role. Codex, Claude or another model may fill any role when its
capabilities fit the dispatch.

## Dispatch is the unit of delegation

Every delegated operation receives a dispatch packet. The packet contains the
actual context required to do the work, not merely references to a conversation.

A dispatch must define:

- dispatch id and task id;
- role and objective;
- required skills/workflows;
- source-of-truth artifacts;
- files to read first;
- allowed and forbidden changes;
- acceptance criteria;
- required verification;
- decision authority for the worker;
- stop/escalation conditions;
- output contract.

The worker must stop when the task requires a change outside the packet.

## Decision authority

Not every implementation choice is a project decision.

### Local choice

The worker may decide without writing to `DECISIONS.md` when the choice:

- stays inside accepted requirements and contracts;
- does not change externally observable behavior;
- is cheap to reverse;
- does not alter security, data ownership, provider, cost or release behavior;
- does not expand the allowed file/scope boundary.

Examples: local naming, helper extraction, test fixture shape, internal function
layout, equivalent library API usage already allowed by the repository.

### Recorded decision

The orchestrator may accept and record a decision without asking the user when
the choice is material enough to be worth remembering but still follows the
approved goal and is reasonably reversible.

Examples: choosing one internal module boundary over another, selecting a
documented retry strategy inside an already approved integration, choosing
between equivalent implementation patterns with maintenance consequences.

Recorded decisions go to `DECISIONS.md` with actor, context, consequences and
the dispatch/task that discovered them.

### User-required decision

The orchestrator must ask the user when a choice changes intent or carries
meaningful external consequences, including:

- product behavior, scope or UX semantics not already specified;
- public API or integration contract;
- destructive or hard-to-reverse data change;
- authentication, authorization, privacy or security boundary;
- new external provider, paid dependency or recurring cost;
- production/release/deployment action not already authorized;
- secret or credential handling;
- legal/compliance posture;
- conflicting requirements where either interpretation is plausible;
- architecture with major lock-in or migration cost.

Only the dependent dispatches pause. Independent work must continue when an
eligible lane exists. The orchestrator records the question in the project
notebook, marks the affected dispatch/task `awaiting_decision`, and immediately
re-runs scheduling for unrelated tasks, specs or already-approved phases.

## Project notebook

Multi-agent projects keep a human-readable notebook under `.agent/notes/`.

- `INDEX.md` is the dashboard;
- `QUESTIONS.md` is the queue of user-required decisions;
- `PROGRESS.md` explains what was completed and what happens next;
- `PHASES.md` summarizes active and completed phases/specs.

The notebook is not a second source of truth. Accepted choices still live in
`DECISIONS.md`; lifecycle state remains in kernel/orchestration state; evidence
stays in the evidence ledger.

When a user-required choice appears, create a `Q-###` note before asking. Keep
the branch/worktree intact, block only dependent dispatches, and name which
independent work can proceed. After the answer, link the question to the formal
Decision ID and resume the dependent queue.

## Results are untrusted until inspected

Each worker returns a structured result. The orchestrator validates the result
against the dispatch before changing orchestration state.

A worker claim is not evidence by itself. Test output, diff inspection, runtime
observations and reviewer findings remain subject to the framework evidence
policy.

## Concurrency and worktree lanes

The orchestrator should prefer useful parallelism instead of waiting when work is
independent.

Writable dispatches may run concurrently when:

- dependencies are satisfied;
- write scopes do not overlap, including shared generated/config artifacts;
- shared mutable contracts are not being edited concurrently;
- each writer has its own branch and Git worktree;
- every lane records its base commit and logical owner;
- integration order is explicit.

Use `worktree-lane-manager` to allocate lanes. Persist the lane id, branch, base
commit and write scope; keep absolute worktree paths runtime-only.

The legacy kernel still exposes one canonical `current_task`. Therefore
multi-writer concurrency is owned by the orchestration layer: do not pretend each
parallel writer independently owns the kernel lifecycle. Before integration,
serialize/reconcile the formal lifecycle transitions and preserve evidence per
dispatch/task.

If a lane becomes `awaiting_decision`, preserve its branch/worktree and schedule
another eligible lane. A blocked task does not freeze the project.

Serialize work when scopes overlap, dependencies are not landed, or central
resources such as schema/migrations/lockfiles make concurrent writes unsafe.

## Maestri mapping

A common four-lane setup is:

- orchestrator: control plane;
- developer: implementation;
- tester: validation and regression design;
- reviewer: independent spec/quality review.

The orchestrator sends role-specific dispatches and consumes structured results.
Workers should not receive the entire skill catalog; only the skills and
workflows required by the dispatch are named.
