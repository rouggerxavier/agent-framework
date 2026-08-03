# Workflow — Classifying and reclassifying execution modes

```text
Fast optimises speed.
Standard organises ordinary development.
Critical protects the application from grave damage.
```

Use this when choosing the mode of a task, when a phase is being planned, or
when a classification already recorded turns out to be wrong.

## Choosing at planning time

Apply the factors in order: potential damage of a failure, sensitivity of the
area, reversibility, blast radius, complexity and size, estimated time. Time
separates `fast` from `standard`; only damage reaches `critical`.

```bash
agent-framework-route --auto "<the request>"
```

The router is side-effect free and prints `selected_mode`, the named
grave-damage paths in `risk_factors`, the `sensitive_areas` (which rule out
`fast` but never escalate to `critical` on their own), and the assets worth
loading. `standard` is the answer when nothing argues otherwise.

Record the classification where the work lives:

- **per task** — `execution_mode: fast | standard | critical` in the task entry
  of `TASKS.md`;
- **per phase** — `default_execution_mode` in the `TASKS.md` frontmatter, as a
  default for tasks that declare nothing;
- **per project** — `execution_mode` in `STATE.md`, as the outermost default.

Most specific wins. A phase with one critical task keeps its other tasks at their
own classification.

## Correcting a classification

`framework-next set-execution-mode` is the only formal writer. It records the
change and its justification in `STATE.md`, appends a `classification` event to
the evidence ledger, and touches nothing else — not the sealed plan, not a
review, not an existing evidence entry.

Reduce an over-classification:

```bash
framework-next set-execution-mode \
  --scope task --task-id U3A --to standard \
  --reason "Frontend delimitado em 10 arquivos, sem backend, sem migration" \
  --actor "<who>"
```

Escalate after discovering a real grave-damage path:

```bash
framework-next set-execution-mode \
  --scope task --task-id U3B1 --to critical \
  --risk cross_tenant_exposure \
  --reason "A consulta nova atravessa o filtro de tenant" \
  --actor "<who>"
```

Lower the project default without losing the persistent kernel:

```bash
framework-next set-execution-mode \
  --scope project --to standard \
  --reason "Desenvolvimento normal; critical fica reservado a dano grave" \
  --actor "<who>"
```

`--check` runs every guard and writes nothing. Repeating a classification that
already holds is a no-op. The previous classification is kept in the record's
`history`.

## What each mode changes inside the kernel

| Obligation | Fast task | Standard task | Critical task |
| --- | --- | --- | --- |
| `allowed_files` and acceptance in the contract | yes | yes | yes |
| `read_first`, `forbidden_changes`, `requirements`, `runtime_verification` | optional | optional | required |
| Rollback strategy | optional (trivially reversible) | proportional — required only when applicable | required (or containment) |
| Self-review checklist | core checks | full | full |
| Plan seal for the phase | not required | not required | required |
| Reviews before `verifying` | none beyond self-review | one integrated | spec **and** quality |

Below `critical`, an approving spec review closes the round: it records
`code_quality: not_required` against the same review document, moves the task to
`reviewed`, and points at `verify-phase`. A blocking verdict still returns the
task to `executing` in every mode.

## Starting a project that needs memory but not ceremony

```bash
framework-next init --project . --name "<name>" --mode standard --persistent
```

This creates the full kernel — phases, contracts, gates, evidence — with
`standard` as the default task mode. Without `--persistent`, `standard` gets the
resume-only state it always had, and `critical` gets the full kernel as before.

## Acceptance

- The mode is recorded where the unit of work lives, not inferred per session.
- Every escalation to `critical` names a grave-damage path.
- Every reduction states its reason.
- No review, evidence entry or sealed plan was rewritten to change a label.
- `framework-next validate` is clean afterwards.

## Related

- Policy: `kernel/adaptive-execution-policy.md`
- Guards: `kernel/state-machine.md`
- Routers: `skills/agent-framework-router`, `skills/task-mode-router`
