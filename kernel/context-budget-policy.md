# Context Budget Policy

## Purpose

Minimize token cost and stale-context errors across a long-running multi-agent
project without dropping source-of-truth information.

The default is **fresh task context**: a worker starts each new task with a clean
agent session and a focused dispatch package.

## Terminal clear is not context reset

A shell `clear` only changes what is visible on screen. It does not erase the
model conversation/context.

Before assigning a new task to a lane, the orchestrator should use the strongest
reset primitive the harness supports:

1. close/archive the previous worker turn after its structured result is saved;
2. reset/clear the agent conversation if the harness exposes that operation;
3. otherwise open a fresh agent session/terminal for the next task;
4. optionally clear terminal scrollback for human readability;
5. send only the new dispatch package.

Never assume `clear`, `cls` or ANSI terminal reset reduced model tokens.

## What persists across resets

Persist durable context before resetting:

- task/dispatch result;
- accepted findings;
- test/evidence references;
- decisions and open questions;
- project notebook progress;
- branch/worktree/base commit;
- next authorized operation.

Do not preserve the whole conversation merely because it exists.

## Minimum-context dispatch

A new worker receives only what it needs:

- objective and acceptance criteria;
- relevant spec/task excerpts;
- accepted decisions/invariants that affect the task;
- exact files to read first;
- allowed write scope;
- required skills/workflows;
- test/evidence requirements;
- open findings that this dispatch must close;
- stop/escalation conditions.

Prefer references plus focused excerpts over copying whole documents. The worker
may read additional repository files on demand.

## Token economy rules

- Do not send the full skill catalog.
- Do not replay old worker conversations to a new task.
- Do not paste full logs when a concise result + log reference is sufficient.
- Do not duplicate formal decisions in every prompt; include only applicable
  decisions.
- Summarize completed phases in the notebook; do not inject their full histories.
- Use `context-compressor` when a same-task session must continue and a clean
  restart would lose useful local reasoning.
- Prefer a fresh session over compression when starting a different task.
- Cache/reuse stable repository facts through project artifacts rather than
  repeatedly explaining them in natural language.
- Read large files/rubrics only when the dispatch requires them.

## When not to reset

Keep the same context only when:

- the worker is still on the same task;
- it is applying a tightly-scoped correction/review round;
- recent local reasoning materially reduces risk;
- the context is not already noisy or oversized.

Changing task id, role, spec or worktree is a strong default signal to reset.

## Orchestrator context

The orchestrator itself should also compact periodically. Its durable memory is
the project state + notebook + dispatch/result artifacts, not its chat transcript.

At a phase boundary or after a large integration batch:

1. update notebook/state;
2. compress unresolved context;
3. discard completed-task conversational detail;
4. continue from artifacts.
