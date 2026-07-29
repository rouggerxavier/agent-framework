"""Re-point persistent state at a phase whose work already exists in Git.

Work sometimes lands before the phase has an executable index: the commits, the
tests, and the reviews exist, but the kernel never occupied the intermediate
states, so the canonical status is stranded on an earlier phase. Nothing in the
normal lifecycle can express that, because a plan may only be sealed from
``specified`` and a phase may only be initialized before execution starts.

This operation closes that gap without weakening any gate. It refuses to run
unless the work is genuinely finished and committed, and it stops at
``verifying`` so the ordinary shipping gate — required verification, acceptance
evidence, waivers, and blockers — still decides whether the phase ships.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .contracts import load_task_index
from .documents import DocumentError, git_snapshot, load_frontmatter, utc_now, write_frontmatter
from .state_machine import compute_plan_fingerprint


PHASE_ARTIFACT_FILES = {
    "spec": "SPEC.md",
    "plan": "PLAN.md",
    "tasks": "TASKS.md",
    "evidence": "EVIDENCE.md",
    "review": "REVIEW.md",
    "handoff": "HANDOFF.md",
}

RECONCILABLE_FROM = {"executing", "reviewing", "verifying"}


def _open_blockers(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    blockers = state.get("blockers", [])
    if not isinstance(blockers, list):
        return []
    return [
        blocker
        for blocker in blockers
        if isinstance(blocker, dict) and blocker.get("status") not in {"resolved", "waived"}
    ]


def reconciliation_issues(
    state: Dict[str, Any],
    root: Path,
    *,
    slug: str,
    decision_id: str,
    evidence: str,
    version: int,
) -> List[str]:
    issues: List[str] = []

    status = state.get("status")
    if status not in RECONCILABLE_FROM:
        issues.append(
            "reconciliation requires an active phase; status is {!r}".format(status)
        )

    phase_dir = root / ".agent" / "phases" / slug
    if not phase_dir.is_dir():
        issues.append("phase directory does not exist: .agent/phases/{}".format(slug))
    else:
        for name in sorted(PHASE_ARTIFACT_FILES.values()):
            if not (phase_dir / name).is_file():
                issues.append("phase artifact is missing: {}/{}".format(slug, name))

    tasks_path = phase_dir / "TASKS.md"
    if tasks_path.is_file():
        try:
            index, _ = load_task_index(tasks_path)
        except DocumentError as exc:
            issues.append(str(exc))
        else:
            tasks = index["tasks"]
            if not tasks:
                issues.append("reconciled phase requires at least one task")
            unfinished = [
                str(task.get("id"))
                for task in tasks
                if isinstance(task, dict) and task.get("status") not in {"verified", "cancelled"}
            ]
            if unfinished:
                issues.append(
                    "reconciliation requires finished work; unfinished: {}".format(
                        ", ".join(unfinished)
                    )
                )

    decisions_path = root / ".agent" / "DECISIONS.md"
    if not decisions_path.is_file():
        issues.append("DECISIONS.md is missing")
    elif not re.search(
        r"^#{{2,6}}\s+{}\b".format(re.escape(decision_id)),
        decisions_path.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        issues.append("decision {} is not recorded in DECISIONS.md".format(decision_id))

    evidence_path = root / evidence.split("#", 1)[0]
    if not evidence_path.is_file():
        issues.append("reconciliation evidence file is missing: {}".format(evidence))

    current_version = state.get("plan_revision", {})
    current_version = (
        current_version.get("version") if isinstance(current_version, dict) else None
    )
    if isinstance(current_version, int) and version <= current_version:
        issues.append(
            "plan revision must increase; current is {}".format(current_version)
        )

    if _open_blockers(state):
        issues.append("resolve or waive open blockers before reconciling")

    snapshot = git_snapshot(root)
    if snapshot.get("is_repository"):
        material = [
            path
            for path in snapshot.get("changed_files", [])
            if not path.startswith(".agent/")
        ]
        if material:
            issues.append(
                "reconciliation describes committed work; uncommitted changes: {}".format(
                    ", ".join(sorted(material)[:5])
                )
            )

    return issues


def reconcile_phase(
    project_root: Path,
    *,
    phase_id: str,
    phase_name: str,
    slug: str,
    decision_id: str,
    evidence: str,
    version: int,
    actor: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Point the state at an already-executed phase and re-seal its plan.

    Returns the updated state and the issues that stopped it. When issues are
    present, nothing is written.
    """

    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)

    issues = reconciliation_issues(
        state,
        project_root,
        slug=slug,
        decision_id=decision_id,
        evidence=evidence,
        version=version,
    )
    if issues:
        return state, issues

    relative = ".agent/phases/{}".format(slug)
    state["artifacts"].update(
        {
            name: "{}/{}".format(relative, filename)
            for name, filename in PHASE_ARTIFACT_FILES.items()
        }
    )
    state["phase"] = {"id": phase_id, "name": phase_name, "status": "verifying"}
    state["status"] = "verifying"

    index, _ = load_task_index(project_root / relative / "TASKS.md")
    verified = [
        task
        for task in index["tasks"]
        if isinstance(task, dict) and task.get("status") == "verified"
    ]
    if verified:
        state["current_task"] = {"id": verified[-1]["id"], "status": "verified"}

    state["plan_revision"] = {
        "version": version,
        "decision_id": decision_id,
        "fingerprint": compute_plan_fingerprint(state, project_root),
        "evidence": evidence,
        "reconciled": True,
    }
    state["next_action"] = {"operation": "verify-phase", "target": phase_id}
    state["last_transition"] = {
        "from": "reconciliation",
        "to": "verifying",
        "at": utc_now(),
        "by": actor,
        "reason": "phase {} reconciled from committed work under {}".format(
            phase_id, decision_id
        ),
    }
    state["updated_at"] = utc_now()
    state["updated_by"] = actor
    write_frontmatter(state_path, state, body)
    return state, []
