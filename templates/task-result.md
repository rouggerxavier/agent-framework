---
{
  "schema_version": 1,
  "task": {
    "id": "P1-T03",
    "result": "implementation_complete",
    "executor": "agent-or-person-id",
    "starting_commit": null
  },
  "changes": {
    "files_modified": [],
    "files_created": [],
    "files_deleted": []
  },
  "verification": {
    "commands_run": [
      {
        "command": "pytest tests/integrations/test_mapper.py",
        "stage": "red",
        "type": "unit",
        "outcome": "failed",
        "expected_failure": true,
        "output_summary": "Failed for the expected missing behavior.",
        "log_reference": null
      },
      {
        "command": "pytest tests/integrations/test_mapper.py",
        "stage": "green",
        "type": "unit",
        "outcome": "passed",
        "expected_failure": false,
        "output_summary": "Passed.",
        "log_reference": null
      },
      {
        "command": "pytest tests/integrations/test_mapper.py",
        "stage": "refactor",
        "type": "unit",
        "outcome": "passed",
        "expected_failure": false,
        "output_summary": "Passed after refactor.",
        "log_reference": null
      }
    ],
    "runtime": [],
    "passed": [],
    "failed": []
  },
  "acceptance_evidence": {
    "AC-01": [],
    "AC-02": [],
    "AC-03": []
  },
  "scope": {
    "unexpected_changes": [],
    "deviations": []
  },
  "risks": {
    "discovered": []
  },
  "self_review": {
    "result": "PASS",
    "checklist": {
      "complete_diff": true,
      "modified_files": true,
      "scope": true,
      "acceptance": true,
      "tests": true,
      "temporary_logs": true,
      "debug_code": true,
      "todos": true,
      "secrets": true,
      "error_behavior": true,
      "compatibility": true,
      "documentation": true
    },
    "notes": []
  },
  "test_waiver": null,
  "review_notes": []
}
---

# Task Result

The executor may report only `implementation_complete`. The runner validates this
frontmatter and records it before requesting independent review.

