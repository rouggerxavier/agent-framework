# Kernel Evidence Policy

The append-only ledger is required in `critical`, optional/lightweight in
`standard`, and not instantiated in `fast`. Every mode still requires observable
verification before success; evidence need not become a persistent document.

Review findings use `BLOCKER`, `IMPORTANT`, `NOTE`, or `SPECULATIVE`. A blocker
requires a real execution path, plausible likelihood, material impact, and
supporting evidence. `SPECULATIVE` never blocks.

## Evidence types

Valid evidence includes executed commands with results, test output, direct diff
inspection, screenshots, database queries, API responses, logs, compliance
review, quality review, manual validation, and explicit waivers with alternative
evidence. Evidence records source, timestamp, actor, outcome, and the acceptance
criterion or gate it supports. Failures are retained with later corrections.

## Evidence vocabulary

| Term | Definition | Counts as proof? |
| --- | --- | --- |
| Claim | Statement that something is true | No |
| Evidence | Reproducible observation with source and result | Yes, within its scope |
| Inference | Conclusion derived from named evidence | Only when labeled; not direct proof |
| Assumption | Unverified premise accepted temporarily | No |
| Decision | Chosen course with context and consequences | Authorizes work; does not prove it |
| Waiver | Approved exception with reason and alternative evidence | Only for the waived gate |
| Blocker | Proven condition that prohibits progress | Yes, for stopping |

An implementer assertion never becomes evidence merely because it is structured.
Reviewers inspect code, artifacts, and command results directly rather than
reviewing only the implementer summary.

## Ledger rules

- Use the active phase `EVIDENCE.md`; group entries by task and preserve history.
- Associate every acceptance criterion with concrete evidence or mark it missing.
- Store commands, outcome, timestamp, concise output, and a log reference when
  full output is external.
- Record self-review, spec compliance, quality review, waivers, blockers, and
  corrections separately.
- Never invent a result, rewrite a failure as success, or reuse stale evidence
  after material changes.
- Sensitive data and secrets are redacted; the record states that redaction
  occurred.

Evidence is fresh only for the inspected content/commit. Material repository
changes invalidate affected context, tests, and reviews until revalidation.
