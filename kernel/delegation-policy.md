# Kernel Delegation Policy

## Single control plane

Exactly one control plane owns a phase at a time. In the ordinary single-agent
flow that control plane is the workflow runner. In an explicit multi-agent flow
it is the team orchestrator, which may delegate lifecycle operations to the
workflow runner while retaining scheduling authority.

Subagents are executors, testers, reviewers or specialists, not competing
orchestrators. A delegated actor cannot change `STATE.md`, orchestration state,
the plan, accepted decisions or task ownership unless the control plane
explicitly grants that operation.

## When to use clean context

Use a new context for independent task implementation, independent review,
parallel non-conflicting tasks, or when prior conversation is noisy or stale.
Do not delegate unresolved product decisions, lifecycle authority, plan
revisions, secret-bearing operations, ambiguous destructive actions, or final
verification ownership.

## Required context package

Every delegated worker receives content, not merely paths. Multi-agent runs use
the dispatch contract in `templates/agent-dispatch.md`; ordinary delegated
implementers receive the equivalent focused package:

- complete task contract;
- relevant project context and spec excerpts;
- applicable requirements, decisions, and invariants;
- test and evidence policies;
- current state and next authorized operation;
- starting commit, branch/worktree, and exact file list;
- prior results or failures that affect this task.

Exclude unrelated conversation, unrelated phases and decisions, the entire skill
catalog, and documentation with no bearing on the contract. The runner checks the
package against the task contract so requirement loss is visible.

## Return contract

Executors return the structured task result defined by
`templates/task-result.md`, including changed files, commands/results,
acceptance evidence, deviations, discovered risk, and review notes. Reviewers
return their own structured reports after direct inspection. The runner validates
each result, appends it to the evidence ledger, and alone requests lifecycle
transitions.

Delegated claims are untrusted until backed by direct evidence under
`evidence-policy.md`.

For multi-agent scheduling, decision authority and Maestri-style lanes, also
apply `orchestration-policy.md`.

