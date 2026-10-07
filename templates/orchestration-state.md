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
    "decisions": ".agent/DECISIONS.md"
  },
  "agents": {
    "developer": {"agent_id": "dev-1", "status": "idle"},
    "tester": {"agent_id": "test-1", "status": "idle"},
    "reviewer": {"agent_id": "review-1", "status": "idle"}
  },
  "dispatches": [],
  "awaiting_user": [],
  "blockers": [],
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

Alternative terminal states:

`changes_required | blocked | cancelled`

The orchestration state is coordination metadata. Product requirements,
contracts, decisions and evidence remain in their existing framework artifacts.
