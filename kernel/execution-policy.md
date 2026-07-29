# Kernel Execution Policy

This complete policy governs `critical`. For `fast` and `standard`, use
`adaptive-execution-policy.md` and apply only the proportional scope, test, diff
review, and risk controls selected there.

## Scope and concurrency

- One active task per executor.
- Parallel tasks require disjoint `allowed_files`, no shared mutable contract,
  satisfied dependencies, and isolated workspaces.
- The task contract is the hard scope boundary. An executor stops when a needed
  change is outside `allowed_files` or contradicts `forbidden_changes`.
- Scope expansion requires a recorded discovery, explicit plan/contract revision,
  and a fresh plan gate before execution resumes.

Allowed files are exact project-relative paths unless the contract explicitly
defines a narrow directory prefix. Paths outside the project root, secrets,
unrelated user changes, generated caches, and files listed in
`forbidden_changes` are prohibited.

## Execution loop

1. Validate state, Git, context freshness, task contract, and dependencies.
2. Read every `read_first` file.
3. Apply the central test policy and record RED/characterization evidence when
   required.
4. Make only authorized changes.
5. Run required tests and runtime checks.
6. Inspect the complete diff and perform the mandatory self-review.
7. Produce the structured result and append evidence, including failures.
8. Mark only `implementation_complete` and return control to the runner.

No role may conclude by inference. A command without its result, a claimed test
without execution output, or an implementer summary without direct inspection is
not proof.

## Retry, interruption, and escalation

- Retry only when the failure is plausibly transient and the operation is safe or
  idempotent. Record each retry and stop after the task contract limit, default 2.
- Never retry deterministic test, schema, permission, or contract failures without
  a change that addresses the cause.
- Interrupt on scope expansion, stale context, conflicting parallel changes,
  failing required verification, missing evidence, unsafe Git state, or policy
  violation.
- Escalate after retries are exhausted, authority is missing, requirements
  conflict, rollback is unsafe, or risk exceeds the approved classification.
- Escalation creates a blocker with evidence and explicit unblock conditions.

## Git and isolation

Use a worktree when a subagent implements, tasks run in parallel, the primary
working tree contains unrelated changes, risk is high, or the selected workflow
requires isolation. Record base branch, branch, worktree, and starting commit in
`STATE.md`. Reuse only after validating ownership and repository state. Cleanup is
explicit after integration; the kernel never removes an ambiguous worktree.

After the plan gate, the runner seals `PLAN.md` and `TASKS.md` with a SHA-256
fingerprint, revision, decision ID, and evidence reference in `STATE.md`.
Any later content change blocks execution until the planner records a revision,
reruns the plan gate, and seals the new content.
