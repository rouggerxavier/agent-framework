# Integration Batch Workflow

Use whenever two or more pull requests are open concurrently. The workflow
always creates/updates a batch record; combined CI runs for the compatible
integration-eligible subset.

## Sequence

1. List **all** open PRs and exact head SHAs into an integration batch record.
2. Mark drafts/not-ready/incompatible PRs explicitly; do not silently omit them.
3. Build a dependency/conflict graph.
4. Select the largest compatible integration-eligible candidate set.
5. When at least two candidates are compatible, create an ephemeral integration
   branch/worktree from the current base.
6. Compose candidate heads in dependency order.
7. If the repository's CI requires a PR event, open/update an ephemeral batch PR.
8. Select CI profile from the union of impacts.
9. Run combined integration CI.
10. While it runs, continue independent development according to
    `ci-throughput.md`.
11. If green, merge real PRs sequentially in dependency order.
12. After each real merge, verify that the remaining composition still matches
    what the batch proved.
13. Rebuild when any included SHA changes or the base changes materially.
14. Update notebook/progress and clean the ephemeral batch workspace/PR when the
    batch is exhausted.
15. If two or more PRs are still open, immediately create/refresh the next batch.

## Safety

An integration batch may reduce duplicate optional validation. It does not bypass
required checks, reviews, branch protection, release gates or per-PR policies.

## Orchestrator rule

Whenever there are 2+ open PRs, the orchestrator must maintain an integration
batch record. The executable composition may be:

- `running`: at least two compatible heads are being validated;
- `waiting_candidates`: fewer than two heads are integration-ready yet;
- `split`: open PRs require separate compatibility groups.

Silently allowing multiple open PRs to exist without a batch inventory is not
allowed.
