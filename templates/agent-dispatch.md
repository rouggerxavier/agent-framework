---
{
  "schema_version": 1,
  "dispatch_id": "D-001",
  "task_id": "P1-T01",
  "role": "developer",
  "agent_id": "dev-1",
  "status": "queued",
  "objective": "",
  "workspace": {
    "kind": "worktree",
    "lane_id": "lane-dev-1",
    "branch": "agent/ORCH-001/P1-T01-normalize",
    "base_commit": "<sha>"
  },
  "session": {
    "fresh_context_required": true,
    "previous_task_must_be_persisted": true,
    "terminal_visual_clear": true
  },
  "source_of_truth": {
    "spec": ".agent/phases/P1/SPEC.md",
    "tasks": ".agent/phases/P1/TASKS.md",
    "decisions": ".agent/DECISIONS.md",
    "notes_index": ".agent/notes/INDEX.md"
  },
  "required_skills": [],
  "required_workflows": [],
  "read_first": [],
  "allowed_files": [],
  "forbidden_changes": [],
  "depends_on_dispatches": [],
  "acceptance": [],
  "verification": [],
  "decision_authority": "local_only",
  "stop_conditions": [],
  "output": {
    "result_path": ".agent/results/D-001.md",
    "max_status": "implementation_complete"
  }
}
---

# Dispatch Notes

The frontmatter is the executable delegation packet.

## Rules

- The worker performs only the role named in `role`.
- A new task starts with a fresh agent context when the harness supports it. A
  shell `clear` is visual hygiene only and never counts as a model-context reset.
- The previous task result must be persisted before reusing a lane.
- `required_skills` and `required_workflows` are the worker's focused toolset;
  do not load the whole framework unless a listed asset routes there.
- `allowed_files` is the write boundary. Reading related files is allowed when
  necessary to understand the task.
- A worker with `decision_authority: local_only` may make only local choices
  defined by `kernel/orchestration-policy.md`.
- Material discoveries are returned to the orchestrator. Workers do not edit the
  global plan, orchestration state or accepted project decisions.
- Stop instead of guessing when a stop condition is met.
- Keep prompts token-efficient: do not replay old conversations, full logs or the
  whole skill catalog when the focused packet is sufficient.

## Recommended role bundles

### developer
- `task-runner`
- implementation-specific workflow/skills selected by the orchestrator
- targeted test skill when needed

### tester
- `test-strategy-builder`
- `test-confidence-mapper`
- `runtime-qa-audit` or domain-specific QA skill

### reviewer
- `spec-compliance-reviewer`
- `code-quality-reviewer`
- `diff-reviewer`
- specialized rubric selected by `code-review-gate`
