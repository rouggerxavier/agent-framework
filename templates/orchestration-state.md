---
{
  "schema_version": 1,
  "run_id": "ORCH-001",
  "status": "planning",
  "owner": "orchestrator",
  "mode": "standard",
  "goal": "",
  "artifacts": {
    "spec": null,
    "plan": null,
    "tasks": null,
    "decisions": ".agent/DECISIONS.md",
    "notes_index": ".agent/notes/INDEX.md",
    "questions": ".agent/notes/QUESTIONS.md",
    "progress": ".agent/notes/PROGRESS.md",
    "phases": ".agent/notes/PHASES.md"
  },
  "agents": {
    "developer": {"agent_id": "dev-1", "status": "idle"},
    "tester": {"agent_id": "test-1", "status": "idle"},
    "reviewer": {"agent_id": "review-1", "status": "idle"}
  },
  "lanes": [],
  "integration_batches": [],
  "dispatches": [],
  "awaiting_user": [],
  "eligible_work": [],
  "blockers": [],
  "waiting_for_events": [],
  "next_action": null
}
---

# Orchestration State

This file is owned by the orchestrator. Workers may read it but must not edit it.

## Status values

- `planning`
- `dispatching`
- `executing`
- `reviewing`
- `verifying`
- `awaiting_user`
- `waiting_for_event`
- `ready_to_integrate`
- `completed`
- `blocked`

## Dispatch record shape

Each item in `dispatches` should contain at least:

```json
{
  "id": "D-001",
  "task_id": "P1-T01",
  "role": "developer",
  "agent_id": "dev-1",
  "status": "queued",
  "packet": ".agent/dispatches/D-001.md",
  "result": null,
  "depends_on": []
}
```

Recommended dispatch statuses:

`queued -> assigned -> running -> returned -> accepted`

Alternative states:

`changes_required | awaiting_decision | blocked | cancelled`

## Lane record shape

Writable parallel work is tracked independently from the legacy kernel's single
`current_task`:

```json
{
  "id": "lane-dev-1",
  "role": "developer",
  "agent_id": "dev-1",
  "dispatch_id": "D-001",
  "task_id": "P1-T01",
  "workspace": {
    "kind": "worktree",
    "branch": "agent/ORCH-001/P1-T01-normalize",
    "base_commit": "<sha>"
  },
  "write_scope": ["app/example.py", "tests/test_example.py"],
  "status": "running",
  "blocked_on_question": null
}
```

Do not persist absolute worktree paths.

## Waiting-user record shape

```json
{
  "question_id": "Q-001",
  "phase_id": "P1",
  "task_ids": ["P1-T02"],
  "dispatch_ids": ["D-004"],
  "note": ".agent/notes/QUESTIONS.md#q-001",
  "status": "open"
}
```

A waiting-user record is not a global stop condition. Recompute
`eligible_work` and fill any independent lane.

## Waiting-event record shape

Use this when there is no immediately actionable orchestration work but the run
still owns unfinished work:

```json
{
  "kind": "worker_result",
  "dispatch_id": "D-001",
  "agent_id": "dev-1",
  "expected_event": "result | failure | blocker",
  "since": "<timestamp>",
  "diagnostic_check_after": null
}
```

`waiting_for_event` means **yield**, not periodic polling. A diagnostic check
is exceptional and should only be scheduled for a meaningful timeout or concrete
stall suspicion.

## Integration batch record shape

```json
{
  "id": "IB-001",
  "branch": "integration/ORCH-001/IB-001",
  "base_commit": "<sha>",
  "pull_requests": [
    {"number": 101, "head_sha": "<sha>"},
    {"number": 102, "head_sha": "<sha>"}
  ],
  "status": "running",
  "ci_profile": "targeted"
}
```

The orchestration state is coordination metadata. Product requirements,
contracts, decisions and evidence remain in their existing framework artifacts.
