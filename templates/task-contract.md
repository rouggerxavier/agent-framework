---
{
  "schema_version": 1,
  "id": "P1-T03",
  "title": "Normalize property types",
  "status": "pending",
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
