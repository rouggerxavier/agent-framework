# Correcting a contract that CI proved wrong

For the case where the work is finished, reviewed and published — and then CI
fails, and the fix is not to the code but to the contract.

## When this is the right workflow

All of these hold:

- the task is `executing`, `reviewing` or `verifying`, and **not integrated**;
- the plan was sealed, and `PLAN.md` or `TASKS.md` genuinely needs to change:
  an acceptance criterion is wrong, `allowed_files` is too narrow, a requirement
  was mis-stated;
- the change corrects **the task under way**, and does not start another one.

If the code is wrong and the contract is right, this is not the workflow —
correct the code and re-run the reviews. If the change is large enough to need a
new task or a new phase, `amend-plan` refuses, and the honest route is formal
replanning.

## What not to do

Two shortcuts exist and both destroy the record:

- **Editing `plan_revision.fingerprint` by hand.** The fingerprint is the only
  proof that the approved plan and the plan on disk are the same document.
  Writing it by hand produces a value that describes nothing, and `validate`
  will report `plan-changed-without-revision` against artifacts nobody can
  reconstruct.
- **Filing a `BLOCKED` spec review to reach `blocked`, then returning to
  `specified` and re-sealing.** A blocking review is a reviewer's verdict about
  a diff. CI failing is not that verdict. This route also claims nobody had
  started, and releases the execution binding — so the task re-enters execution
  with a new `bound_at`, as if the work had restarted. It did not. Only the
  contract changed.

## The sequence

1. **Record the decision.** The amendment needs a real `D-nnn` heading in
   `DECISIONS.md` explaining what the contract got wrong and what replaces it.
   Say plainly that CI produced the evidence, and what the previous approvals
   missed.

2. **Record the failure in the ledger.** A `blocker` event referencing the CI
   run. This is the evidence the amendment will point at, and it must live under
   the active phase.

3. **Edit the artifacts.** Change `TASKS.md` and `PLAN.md` directly — the
   acceptance criteria, `allowed_files`, requirements or description of the task
   under way. `amend-plan` seals what is there; it never writes contract content
   itself.

4. **Amend.**

   ```sh
   framework-next amend-plan \
     --decision D-047 \
     --evidence ".agent/phases/<slug>/EVIDENCE.md#event-<timestamp>" \
     --actor planner \
     --reason "CI exposed a defective active-task contract."
   ```

   The revision advances by one, the fingerprint is computed from the artifacts
   on disk, the five review gates reopen, and the phase and task return to
   `executing` with the binding untouched. `validate` should come back clean and
   the next operation should be `resume-task -> <id>`.

5. **Correct the work** against the amended contract.

6. **Re-review.** The old approvals belong to the old revision — they are in the
   record's `history` and in the ledger, and they do not approve the new diff.
   Run the spec and quality reviews again, and let verification pass against the
   revision that is now current.

7. **Push, and let CI answer.** The gate that failed is the gate that has to
   pass. Waiting on it is not part of the step: the amendment is published, and
   `kernel/ci-throughput-policy.md` decides what happens while the run executes —
   the failing gate blocks the merge, not the next safe unit of work.

## What the amendment is allowed to change

| Accepted | Refused |
| --- | --- |
| acceptance criteria of the current task | removing or renaming the current task |
| widening or narrowing `allowed_files` | marking another task `executing` |
| requirements and `forbidden_changes` | marking downstream work complete |
| the contract's description | a task graph with cycles or dangling deps |
| adding the tests the correction needs | anything while the task is integrated |

## Blockers

The amendment neither requires nor invents a blocker. If one is open for the CI
failure it stays open — the amendment changes the contract, not the fact that
the regression is unproven until the new run is green. Close it formally once it
is, and never by deleting the entry.
