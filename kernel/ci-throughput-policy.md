# CI Throughput Policy

```text
CI gates integration, not continuous development.
```

CI blocks a **merge**. It does not, by itself, block coding. The framework
optimises for high development throughput without turning "less CI" into a goal
of its own:

1. do not wait for CI unnecessarily;
2. do not duplicate work;
3. run only the gates the change actually owes;
4. preserve the safety of integration.

## Two axes, not one

| Axis | Question | Values |
| --- | --- | --- |
| `execution_mode` | How much ceremony does a defect here deserve? | `fast`, `standard`, `critical` |
| `ci_profile` | Which gates does this diff owe? | `minimal`, `targeted`, `full` |

They are related and not equal. `critical` does imply `full`. `standard` implies
nothing: a `standard` task may run `minimal` (a README), `targeted` (most
implementation work) or `full` (it carries a migration). Reading `standard` as
"full pipeline, then wait" is what made every ordinary feature pay for a
complete suite and then idle until it came back.

The executable reference is `kernel/runtime/ci_policy.py`. Like routing, it is
side-effect free: choosing a profile runs no command and touches nothing.

## Profiles

**`minimal`** — the change alters no executable behaviour: docs, metadata, a
mechanical refactor that has been *proven* mechanical. Runs only the gates the
scope needs. A refactor merely *claimed* mechanical gets `targeted`; the gates
are what prove it.

**`targeted`** — the default for ordinary implementation. Focal and affected
tests, typecheck/lint/contract checks where they are relevant, the remote jobs
the touched surface maps to, and E2E only when the changed surface demands it.

**`full`** — critical execution mode, migrations, the auth/security core, data
protection, cross-cutting core changes, releases, and any change whose blast
radius is application- or tenant-wide or whose effect is irreversible.

Selecting `minimal` explicitly on a change that owes `full` raises it back to
`full` and says why. The floor is real; the ceiling belongs to the requester.

## Change classification

CI is impact-based. A change is classified as `docs`, `metadata`,
`mechanical_refactor`, `frontend`, `backend`, `contracts`, `database`,
`security_core`, `e2e_relevant`, `release` — as many as apply — and each impact
brings its own gates. A complete pipeline is never owed for the sake of
uniformity.

`security_core` is claimed by a **named grave-damage path** from
`SEVERE_HARM_FACTORS`, never by proximity to a sensitive area. A copy fix on a
login screen is not a change to the authentication core; a sensitive area adds a
security scan to a `targeted` run and nothing more.

## Blocking point is not wait policy

Two fields, two questions. Coupling them is the defect this section exists to
prevent.

| Field | Question | Values |
| --- | --- | --- |
| `ci_blocking_point` | Where is integration gated? | `before_merge`, `now`, `none` |
| `ci_wait_policy` | What does the agent do while it runs? | `background`, `blocking_before_merge`, `blocking_now` |
| `publication_hold` | May anything be published on top of this unit? | true / false |

A `full` profile does **not** produce a wait by itself. It raises
`publication_hold` — nothing merges or publishes on top of this unit until it is
green — and if safe work exists the wait policy stays `background`:

```yaml
ci_profile: full
ci_blocking_point: before_merge
ci_wait_policy: background      # safe next unit exists
publication_hold: true
```

`blocking_before_merge` is the honest answer only when there is nothing safe left
to do, so the wait lands at the merge boundary rather than on a named blocker.

`blocking_now` is never a side effect. It is earned by a named condition, and
this is the complete list:

- the CI result changes the next decision;
- a release is in progress;
- a deploy is in progress;
- an external dependency blocks continuation;
- critical risk explicitly forbids speculative work.

Deliberately absent from that list: a `full` profile, a `critical` mode, and "CI
is still running". None of the three is a reason to stop typing.

## Three blockers, never fused

- **merge blocker** — a gate that must be green before integration;
- **next-work blocker** — a reason the *next unit* cannot start, which is rare;
- **post-merge observation** — a run that reports rather than authorises.

The decision reports them as three separate lines, so no reader can turn one
into another:

```text
MERGE BLOCKER: lint, typecheck, component-tests-affected pending
NEXT-WORK BLOCKER: none — stack_local permitted
POST-MERGE OBSERVATION: main CI: observation
```

"Cannot merge" and "cannot keep working" are different sentences. Only the
second one stops the keyboard.

## Next-work policy

Push the pull request, then classify the next unit's dependency instead of
waiting:

```text
push PR → classify the next unit's dependency → continue when safe
        → return to CI at the merge boundary
```

**`continue_independent`** — the next unit does not depend on the pending pull
request. Start it from the integration base, in its own worktree.

**`stack_local`** — the next unit depends on it. Branch **locally** from the
pending head and keep working. Do not publish the dependent pull request before
the parent integrates, unless the workflow is explicitly stacked. Once the
parent merges, rebase onto the integration base, then validate and publish.

**`wait`** — only when the CI result changes the next decision, critical risk
forbids speculative work, or an external dependency blocks continuation.

## Shared self-hosted runner

A self-hosted runner that shares the development machine competes with local
work for the same cores. While a remote run is executing there:

- **allowed**: reading, editing, writing tests, planning, analysis, diff review,
  documentation — these consume the developer, not the machine;
- **held**: the full test suite, Playwright/Cypress, Docker builds, Next/Vite
  builds, local E2E and other heavy loads.

Do not confuse **resource contention** with **runner instability**. A slow or
timing-sensitive result while local heavy jobs are running is contention until
proven otherwise.

Hosted runners — and dedicated self-hosted hardware — are independent machines,
so local validation runs in parallel with remote CI. That is a capability of the
executor, not a universal rule: nothing here requires GitHub-hosted runners, and
nothing assumes them.

### A worked example of contention

A `standard` frontend unit is pushed. The self-hosted runner shares this laptop
and its run is executing.

```text
runner_kind: self_hosted_shared        local_gates: lint, typecheck
remote_ci_running: true                local_gates_on_hold: component-tests-affected
contention: true                       remote_gates: lint, typecheck,
allow_local_heavy_jobs: false                        component-tests-affected
```

The next unit is written, reviewed and committed on a local branch during those
minutes. `pnpm test:e2e` and `docker compose build` wait. When CI comes back
slower than usual, the first hypothesis is the two Vite processes that were
running, not the runner — **resource contention, not runner instability**.
Reaching for "the runner is flaky" here replaces a scheduling fact with an
infrastructure theory, and the theory sends someone to debug the wrong machine.

## E2E tiers

| Tier | When |
| --- | --- |
| focal | the changed surface has E2E coverage (`targeted`) |
| operational | critical user paths are touched, or the profile is `full` |
| full regression | nightly, release, or an explicit `full` profile |

Full regression is not the default for every small change. Critical paths are
never weakened silently: touching one pulls in the operational tier even under
`targeted`.

## Superseded runs

Keep `concurrency` with `cancel-in-progress` for runs of the same unit or pull
request. A run whose commit can no longer integrate spends a runner on a verdict
nobody will read — and on a shared runner it spends it against the developer.

## Main CI

Separate the pull request's merge gate from watching `main` afterwards. When the
exact merged tree was already validated by the pull request and the branch
workflow adds no gate the pull request did not run, the run on `main` is an
**observation**: it does not hold the next safe unit of work.

A red `main` is still an incident to investigate. An observation that fails is
work, not noise. Nothing here says ignore a failure.

## Audit after green

Prefer an incremental audit. Do not repeat a complete audit when the head has
not moved, the scope has not changed and the previous gates still hold; audit
the new evidence, the new diff and any open blockers instead.

## Context and defaults

The policy needs operational facts the request text cannot carry. They arrive as
**data** — `--ci-context-json`, or the explicit flags on
`scripts/agent-framework-route` — never as prose inside the task description.

| Field | Default | What the default means |
| --- | --- | --- |
| `runner_kind` | `unknown` | treated as sharing this machine; conservative about heavy local jobs, never about editing |
| `remote_ci_running` | `false` | nothing is executing remotely, so nothing is held |
| `next_unit_depends_on_current` | `false` | **not declared dependent** — never read as a confirmed dependency |
| `has_next_unit` | `true` | there is work to continue with |
| `unit_merged` | `false` | nothing has merged, so there is nothing on `main` to observe |
| `merge_tree_validated_by_pr` | `false` | unknown, so the run on `main` is a gate until declared otherwise |
| `main_status` | `unknown` | not read as red, and not read as green |
| `release_in_progress` / `deploy_in_progress` | `false` | no named reason to wait now |
| `blast_radius` / `reversibility` | `feature` / `straightforward` | ordinary change |

Nothing is invented from silence. An absent field takes the default above, and
the default is stated in the decision's own reason so a reader can see what was
assumed.

`unknown` for `runner_kind` costs some throughput in repositories that never
declare it: heavy local jobs are held while a remote run executes, even on
hardware that would not have contended. It never holds reading, editing,
planning or review. This is a **revisable** default — evidence that it costs
more than it protects is enough to change it — not a permanent rule.

## Where the policy stops

Gate names here are **kinds**, not commands: `unit-tests-affected`, not
`pnpm vitest run --changed`. Binding a kind to a repository's real script is
`test-confidence-mapper`'s job, per repository. The framework deliberately ships
no repository-specific CI configuration and no `.agent/ci-profile.yml`; adding
one is a separate decision with its own persistence cost.

## Documentation checkpoints

A non-critical documentation checkpoint does not automatically hold the next
functional unit — the docs pull request may land in the background. It becomes
blocking when stale documentation would drive an incorrect implementation, when
the document *is* the contract other work reads, or when it ships with a
release. Record which of the two it is.

This sequence is not the default and is what the policy exists to prevent:

```text
feature merge → docs CI → wait → docs merge → main CI → wait → next feature
```

The docs pull request runs `minimal` in the background while the next functional
unit starts. When the documentation genuinely is the input to the next unit, the
blocking reason is *named* — and then it is worth the wait.

## Worked examples

| # | Situation | Profile | Blocking point | Wait | Next work |
| --- | --- | --- | --- | --- | --- |
| A | `standard` frontend, next unit builds on it | `targeted` | `before_merge` | `background` | `stack_local` |
| B | docs-only update | `minimal` | `before_merge` | `background` | `continue_independent` |
| C | `critical` migration, safe next unit exists | `full` | `before_merge` | `background` (`publication_hold: true`) | `continue_independent` |
| D | release under way | `full` | `now` | `blocking_now` | `wait` |
| E | `standard` frontend, shared runner busy | `targeted` | `before_merge` | `background`, heavy local gates on hold | editing continues |

Case C is the one worth reading twice: `full` gates integration and still leaves
the keyboard free. Case D is the one that earns its wait — and it earns it by a
named condition, not by its profile.
