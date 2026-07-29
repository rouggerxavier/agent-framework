---
{
  "schema_version": 1,
  "status": "executing",
  "project": {
    "name": "example-project",
    "mode": "full"
  },
  "milestone": {
    "id": "M1",
    "name": "Example milestone",
    "status": "active"
  },
  "phase": {
    "id": "P1",
    "name": "Example phase",
    "status": "executing"
  },
  "current_task": {
    "id": "P1-T03",
    "status": "executing"
  },
  "next_action": {
    "operation": "resume-task",
    "target": "P1-T03"
  },
  "risk": {
    "level": "high",
    "reasons": []
  },
  "verification": {
    "last_verified_commit": null,
    "required": [],
    "results": {}
  },
  "blockers": [],
  "open_decisions": [],
  "assumptions": [],
  "artifacts": {
    "project": ".agent/PROJECT.md",
    "roadmap": ".agent/ROADMAP.md",
    "context": ".agent/CONTEXT.md",
    "requirements": ".agent/REQUIREMENTS.md",
    "decisions": ".agent/DECISIONS.md",
    "spec": ".agent/phases/01-example/SPEC.md",
    "plan": ".agent/phases/01-example/PLAN.md",
    "tasks": ".agent/phases/01-example/TASKS.md",
    "evidence": ".agent/phases/01-example/EVIDENCE.md",
    "review": ".agent/phases/01-example/REVIEW.md",
    "handoff": ".agent/phases/01-example/HANDOFF.md"
  },
  "git": {
    "base_branch": "main",
    "working_branch": null,
    "worktree": null,
    "starting_commit": null
  },
  "context": {
    "source_commit": null,
    "status": "fresh",
    "generated_at": null,
    "stale_after": "material-repository-change"
  },
  "gates": {
    "specification": "passed",
    "plan_quality": "passed",
    "self_review": "pending",
    "spec_compliance": "pending",
    "code_quality": "pending",
    "acceptance": "pending",
    "verification": "pending",
    "waivers": "not_required",
    "release": "pending"
  },
  "plan_revision": {
    "version": 1,
    "decision_id": "DEC-001",
    "fingerprint": "sha256:replace-after-plan-gate",
    "evidence": ".agent/phases/01-example/EVIDENCE.md#plan-gate"
  },
  "blocked_from": null,
  "last_transition": null,
  "updated_at": null,
  "updated_by": null
}
---

# Project State

The frontmatter is the compact source of lifecycle state. Keep detailed
requirements, plans, decisions, evidence, and handoff prose in their referenced
artifacts.
