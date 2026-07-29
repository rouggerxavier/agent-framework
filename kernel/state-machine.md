# Kernel State Machine

`STATE.md.status` is the canonical lifecycle value. When a phase is active,
`phase.status` mirrors it. The runtime in `kernel/runtime/state_machine.py`
enforces this table and the guards below.

## States

| State | Meaning |
| --- | --- |
| `proposed` | Project or milestone exists but discovery has not started. |
| `discussing` | Material requirements or decisions remain open. |
| `specified` | Requirements and acceptance are frozen for planning. |
| `planned` | Task graph and contracts passed the plan gate. |
| `executing` | Exactly one task per executor is active. |
| `reviewing` | Independent review is active or pending. |
| `verifying` | Phase-level goal and runtime verification is active. |
| `ready_to_ship` | Acceptance and required checks passed. |
| `shipped` | Configured integration or release completed. |
| `blocked` | Progress is prohibited until explicit conditions are met. |
| `cancelled` | Work intentionally stopped without replacement. |
| `superseded` | A newer milestone, phase, or decision replaced this work. |

## Allowed transitions

| From | Allowed destinations |
| --- | --- |
| `proposed` | `discussing`, `blocked`, `cancelled`, `superseded` |
| `discussing` | `specified`, `blocked`, `cancelled`, `superseded` |
| `specified` | `discussing`, `planned`, `blocked`, `cancelled`, `superseded` |
| `planned` | `specified`, `executing`, `blocked`, `cancelled`, `superseded` |
| `executing` | `reviewing`, `blocked`, `cancelled`, `superseded` |
| `reviewing` | `executing`, `verifying`, `blocked`, `cancelled`, `superseded` |
| `verifying` | `executing`, `reviewing`, `ready_to_ship`, `blocked`, `cancelled`, `superseded` |
| `ready_to_ship` | `verifying`, `shipped`, `blocked`, `cancelled`, `superseded` |
| `shipped` | `superseded` |
| `blocked` | recorded `blocked_from`, `cancelled`, or `superseded` |
| `cancelled` | `superseded` |
| `superseded` | none |

Every destination not listed is prohibited. The runner requests transitions;
the kernel validates them. Planner-owned transitions end at `planned`; the
verifier alone requests `ready_to_ship`; shipping skills request `shipped`.

## Transition preconditions and evidence

| Transition | Required preconditions and evidence | Responsible role |
| --- | --- | --- |
| `proposed → discussing` | project initialized; grounding started or unknowns recorded | planner |
| `discussing → specified` | requirements and acceptance persisted; material decisions resolved or explicitly open | planner |
| `specified → planned` | plan and full task contracts exist; dependencies are acyclic; risk and test policy recorded; `plan-quality-checker` passed | planner + plan gate |
| `planned → executing` | plan gate passed; dependencies satisfied; selected task contract exists; risk classified; Git/context valid | runner |
| `executing → reviewing` | result is `implementation_complete`; required tests/waiver and acceptance evidence exist; self-review passed | runner |
| `reviewing → executing` | spec is `BLOCKED` or quality is `CHANGES_REQUIRED`; blocker contains direct evidence | reviewer + runner |
| `reviewing → verifying` | spec is `PASS`/`PASS_WITH_NOTES`; quality is `APPROVED`/`APPROVED_WITH_NOTES`; no blocker | runner |
| `verifying → executing` | verification failed with evidence, or current task is verified and the next eligible contract/dependencies are valid | verifier + runner |
| `verifying → reviewing` | review/evidence defect recorded; affected review invalidated | verifier + runner |
| `verifying → ready_to_ship` | every acceptance criterion has evidence; required verification passed; blockers resolved; waivers reviewed | verifier |
| `ready_to_ship → shipped` | release gate passed and configured commit/PR/handoff completed | shipping role |
| `* → blocked` | blocker, evidence, unblock condition, and `blocked_from` recorded | current role or runner |
| `blocked → blocked_from` | blockers empty; repository/state revalidated | runner |

Plan revisions use `planned → specified`, record a decision, update plan/contracts,
rerun the plan gate, then return through `specified → planned`. They never mutate
an executing workflow silently.

## Failure behavior

- A blocking spec review or required quality change returns the task to
  `executing`. The failing review and correction history remain in the ledger.
- A test failure during execution stays `executing`; repeated investigation may
  enter `blocked`.
- After a task is verified, `verifying → executing` may select the next eligible
  task. When no task remains, phase verification continues toward `ready_to_ship`.
- A verification failure returns to `executing` for code defects or `reviewing`
  for review defects. All invalidated approvals must be rerun.
- `ready_to_ship` is rejected when any blocker, missing acceptance evidence,
  failed required check, or unreviewed waiver exists.
