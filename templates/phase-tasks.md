---
{
  "schema_version": 1,
  "phase": {
    "id": "{{PHASE_ID}}",
    "name": "{{PHASE_NAME}}"
  },
  "tasks": []
}
---

# {{PHASE_ID}} — {{PHASE_NAME}} Task Contracts

Every item in `tasks` must contain the contract its execution mode requires, as
defined by `templates/task-contract.md`. Paths alone are not executable
contracts.

## Execution mode

An optional `"default_execution_mode": "fast" | "standard" | "critical"` beside
`tasks` applies to every task that declares no `execution_mode` of its own. It is
a default, not a floor: a phase may hold `fast`, `standard` and `critical` tasks
at once, and a critical task does not raise its neighbours.

The field is deliberately absent from this template. Without it the phase
inherits the project default in `STATE.md`, so a project already running the
critical lifecycle keeps every guarantee it had — including the plan seal and the
two independent reviews — until someone classifies a task or a phase
deliberately. Lowering ceremony is an explicit act, never a template default.

Add it before the plan is sealed. Afterwards the classification of one task moves
through `framework-next set-execution-mode`, which writes to `STATE.md` and
leaves the sealed index untouched.

