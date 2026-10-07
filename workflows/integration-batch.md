# Integration Batch Workflow

Use when two or more pull requests are open concurrently and combined validation
can reduce integration latency or duplicated CI.

## Sequence

1. List open PRs and exact head SHAs.
2. Exclude drafts/not-ready PRs unless their combined behavior must be tested.
3. Build a dependency/conflict graph.
4. Select compatible candidates.
5. Create an ephemeral integration branch/worktree from the current base.
6. Compose candidate heads in dependency order.
7. Select CI profile from the union of impacts.
8. Run combined integration CI.
9. While it runs, continue independent development according to
   `ci-throughput.md`.
10. If green, merge real PRs sequentially in dependency order.
11. After each real merge, verify that the remaining composition still matches
    what the batch proved.
12. Rebuild when any included SHA changes or the base changes materially.
13. Update notebook/progress and clean the ephemeral batch workspace.

## Safety

An integration batch may reduce duplicate optional validation. It does not bypass
required checks, reviews, branch protection, release gates or per-PR policies.

## Orchestrator rule

Whenever there are 2+ open PRs, the orchestrator must at least evaluate and
record one of:

- `batch_now`;
- `batch_later` with condition;
- `no_batch` with reason.

Silently allowing multiple ready PRs to queue behind independent full CI runs is
not the default.
