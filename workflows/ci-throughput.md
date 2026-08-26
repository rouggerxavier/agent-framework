# From a finished unit to an integrated one

The operational sequence of the CI Throughput Policy: what happens between "the
work is done" and "it is on `main`", and — the part that used to be missing —
what happens *during* it.

```text
CI gates integration, not continuous development.
```

Policy: `kernel/ci-throughput-policy.md`. Decision asset:
`skills/ci-throughput-controller`. Executable reference:
`kernel/runtime/ci_policy.py`.

## The sequence

1. **Close the unit.** Implementation complete, self-review done, the review the
   mode owes applied.

2. **Classify the change.** Which impacts does it carry — docs, metadata,
   mechanical refactor, frontend, backend, contracts, database, security core,
   E2E-relevant, release? That selects the `ci_profile`: `minimal`, `targeted`
   or `full`. The execution mode is an input here, never a synonym.

3. **Run the local gates.** The light ones the profile selected. Not the
   complete suite — under `minimal` or `targeted` CI owns that, and under a
   shared runner already executing, the moderate ones wait too.

4. **Publish the pull request.** With its `concurrency` group set so a superseded
   run of the same unit is cancelled rather than validated.

5. **Remote CI runs in the background.** This is the step that used to be a
   wait. It is a wait now only under a named condition — a release or deploy in
   flight, an external dependency, a result that changes the next decision, or
   critical risk that forbids speculative work.

6. **Classify the next unit and continue.** Independent, dependent, or genuinely
   blocked. See the three paths below.

7. **Return at the merge boundary.** Not before. Read the result, and audit
   **incrementally**: if the head has not moved, the scope has not changed and
   the previous gates still hold, audit the new evidence and any open blockers —
   not the whole diff again.

8. **Merge** once the merge blockers are green.

9. **Observe `main`.** If the exact merged tree was already validated and the
   workflow on `main` adds no gate the pull request did not run, that run
   reports; it does not authorise, and it does not hold the next safe unit. A
   red `main` is an incident: stop and investigate.

## The three paths at step 6

**`continue_independent`** — the next unit does not depend on the pending pull
request.

```bash
git switch --detach origin/main   # the integration base, not the pending head
git switch -c <next-unit>
```

Its own worktree when isolation is warranted. Publish normally.

**`stack_local`** — the next unit builds on the pending one.

```bash
git switch -c <next-unit>         # from the pending head, locally
```

Keep it local. Do **not** publish the dependent pull request before the parent
integrates, unless the workflow is explicitly stacked. After the parent merges:

```bash
git rebase origin/main            # then validate, then publish
```

Validating before the rebase validates a base that no longer exists.

**`wait`** — a named condition holds. Say which one; "CI is running" is not one.

## Superseded runs

A new head replaces the previous one: the previous run is no longer a gate, and
its verdict cannot integrate. Prefer `concurrency` with `cancel-in-progress`
scoped to the unit or pull request. Re-running a superseded SHA spends a runner
on an answer nobody can use — and on a shared runner, spends it against the
developer waiting for the machine.

## While a self-hosted runner shares this machine

Allowed throughout: reading, editing, writing code and tests, planning,
analysis, diff review, documentation.

Held until the remote run finishes: the full suite, Playwright/Cypress, Docker
builds, Next/Vite builds, local E2E, load tests.

A slow or timing-sensitive result while local heavy jobs were running is
**resource contention**, not runner instability. Do not report the second when
you observed the first.

## Documentation checkpoints

A docs pull request runs `minimal` and lands in the background. It holds the next
functional unit only when the stale state would drive an incorrect
implementation, when the document is the contract the next unit reads, or when it
ships with a release — and then the blocking reason is named.

## When CI proves the contract wrong

A failure that shows the *contract* was wrong, not the code, is not this
workflow: use `workflows/ci-contract-correction.md`.
