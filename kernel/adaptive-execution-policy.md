# Adaptive Execution Policy

The framework preserves the complete persistent kernel, but does not apply it to
every task.

## Selection rule

```text
When in doubt → fast
Proven complexity → standard
Proven critical risk → critical
```

File count, theoretical edge cases, or the claim that more process might improve
quality are not escalation evidence. The router accepts `--fast`, `--standard`,
`--critical`, and `--auto`; no option means `auto` with a preference for `fast`.
An explicit lighter mode may be escalated only for grave security or data-loss
risk, with the evidence stated.

## Execution matrix

| Capability | Fast | Standard | Critical |
| --- | --- | --- | --- |
| Persistent state | no | optional by concrete need | required |
| Formal spec | no | lightweight | required |
| Task contract | no | optional/lightweight | required |
| Plan seal | no | no | required |
| Evidence ledger | no | lightweight or none | required |
| Independent reviews | no | no | required |
| Worktree | no | conditional | proportional |
| Review | integrated/light | integrated/normal | split/deep |
| Verification | targeted | proportional | complete |

The templates remain available. Instantiate them only when the selected row calls
for them:

| Template | Fast | Standard | Critical |
| --- | --- | --- | --- |
| Project state | no | optional | yes |
| Roadmap | no | no by default | yes |
| Phase spec | no | lightweight/optional | yes |
| Phase plan | no | short plan | yes |
| Task contract | no | optional | yes |
| Evidence ledger | no | optional and summarized | yes |
| Separate review | no | no | yes |
| Handoff | no | when needed | yes |

## Verification budget

```yaml
verification_budget:
  fast:
    target_ratio: 0.20
    max_full_review_passes: 1
  standard:
    target_ratio: 0.30
    max_full_review_passes: 1
  critical:
    target_ratio: null
    max_full_review_passes: proportional
```

Ratios are operational guidance, not time accounting. When the budget is
exceeded, check for concrete residual risk, stop speculative verification,
record non-blocking notes, and finish if important acceptance criteria are met.

## Review findings

Use `BLOCKER`, `IMPORTANT`, `NOTE`, or `SPECULATIVE`. A blocker must show:

```yaml
reachability:
likelihood:
impact:
supporting_evidence:
```

It must also concern an explicit requirement, security, data loss/corruption, a
reproducible regression, material operational impact, or failed acceptance.
`SPECULATIVE` never blocks. After a localized correction, review the new diff,
affected criteria, and related regressions rather than repeating the whole audit.

## Context reuse

After relevant files have been read, pass reviewers only:

```yaml
goal:
mode:
diff:
files_changed:
tests_run:
acceptance_or_expected_behavior:
known_risks:
```

Repeat full grounding only after a material commit change, scope change, newly
discovered core files, stale context, or a contradiction.

The executable reference is `kernel/runtime/execution_modes.py`; routing is
side-effect free and never creates `.agent/`.
