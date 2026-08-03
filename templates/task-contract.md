---
{
  "schema_version": 1,
  "id": "P1-T03",
  "title": "Normalize property types",
  "status": "pending",
  "execution_mode": "critical",
  "change_type": "business_logic",
  "goal": {
    "description": "Normalize external property types into canonical internal types."
  },
  "depends_on": [
    "P1-T02"
  ],
  "read_first": [
    "app/integrations/example/mapper.py",
    "tests/integrations/test_mapper.py"
  ],
  "allowed_files": [
    "app/integrations/example/mapper.py",
    "tests/integrations/test_mapper.py"
  ],
  "forbidden_changes": [
    "External API client contract",
    "Database schema",
    "Authentication behavior"
  ],
  "requirements": [
    "REQ-004",
    "REQ-007"
  ],
  "acceptance": [
    {
      "id": "AC-01",
      "criterion": "Known external types map to canonical internal values."
    },
    {
      "id": "AC-02",
      "criterion": "Unknown values remain observable and traceable."
    },
    {
      "id": "AC-03",
      "criterion": "Existing mappings do not regress."
    }
  ],
  "test_policy": {
    "mode": "red-green-required",
    "commands": [
      "pytest tests/integrations/test_mapper.py"
    ],
    "retry_limit": 2
  },
  "runtime_verification": [],
  "rollback": {
    "strategy": "revert-task-commit"
  },
  "review": {
    "self_review": "required",
    "spec_compliance": "required",
    "code_quality": "required"
  },
  "execution": {
    "parallel_group": null,
    "isolation": "auto"
  },
  "completion": {
    "requires": [
      "acceptance-evidence",
      "passing-tests",
      "reviewed-diff",
      "atomic-commit"
    ]
  }
}
---

# Task Contract Notes

The frontmatter is the complete executable contract. Record discoveries here,
then revise the plan and contract before expanding scope.

`execution_mode` classifies this task alone. Omit it to inherit the phase's
`default_execution_mode` and then the project default; it is never raised by a
critical neighbour. The example above shows the `critical` shape — every field is
required there.

A `standard` task needs `id`, `title`, `status`, `change_type`, `goal`,
`depends_on`, `allowed_files`, `acceptance`, `test_policy`, `review` and
`completion`, with `self_review: required` plus one of `spec_compliance` or
`code_quality` marked `required` or `integrated`. A `fast` task needs `id`,
`title`, `status`, `change_type`, `goal`, `allowed_files`, `acceptance`,
`test_policy` and `completion`.

`rollback` is proportional for `standard`: it is required only when applicable
— a migration, a destructive data effect, an incompatible change, a persistent
external integration, an infrastructure change, a production operational
change, a feature-flag launch, or a hard-to-reverse regression risk (a
`database_migration` or `external_integration` `change_type` implies it
automatically; anything else declares it via `rollback_signals`). Otherwise the
field is optional, or `{"strategy": "not_applicable", "reason": "..."}`.
`critical` always needs a real `rollback.strategy`, or, when a real rollback is
impossible, `containment`/`justification` describing the feature flag, kill
switch, restore, or recovery procedure instead.

`allowed_files` and `acceptance` are required in every mode: they are the scope
boundary and the definition of done, and they cost one line each.

To correct a classification after the plan is sealed, use
`framework-next set-execution-mode` — never a hand edit of this file.
