# Kernel Delegation Policy

## Single control plane

Exactly one workflow runner owns a phase at a time. Subagents are executors or
reviewers, not competing orchestrators. A delegated actor cannot change
`STATE.md`, the plan, or task ownership unless the runner explicitly grants that
operation.

## When to use clean context

Use a new context for independent task implementation, independent review,
parallel non-conflicting tasks, or when prior conversation is noisy or stale.
Do not delegate unresolved product decisions, lifecycle authority, plan
revisions, secret-bearing operations, ambiguous destructive actions, or final
verification ownership.

## Required context package

Every implementer receives content, not merely paths:

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

