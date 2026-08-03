"""Safe project and phase initialization."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

from .documents import DocumentError, git_snapshot, load_frontmatter, utc_now, write_frontmatter
from .execution_modes import is_persistent_state, normalize_mode


PHASE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _render_template(path: Path, values: Dict[str, Any]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def _initial_state(
    project_name: str,
    mode: str,
    snapshot: Dict[str, Any],
    timestamp: str,
    *,
    execution_mode: str = "critical",
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        # The default mode for the project's tasks, not a floor: each task
        # resolves its own, and `set-execution-mode` records a correction.
        "execution_mode": execution_mode,
        "status": "proposed",
        "project": {"name": project_name, "mode": mode},
        "milestone": {"id": None, "name": None, "status": "proposed"},
        "phase": {"id": None, "name": None, "status": "proposed"},
        "current_task": {"id": None, "status": None},
        "next_action": {"operation": "discuss-requirements", "target": ".agent/PROJECT.md"},
        "risk": {"level": "unclassified", "reasons": []},
        "verification": {
            "last_verified_commit": None,
            "required": [],
            "results": {},
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
            "spec": None,
            "plan": None,
            "tasks": None,
            "evidence": None,
            "review": None,
            "handoff": None,
        },
        "git": {
            "base_branch": snapshot["branch"],
            "working_branch": snapshot["branch"],
            "worktree": None,
            "starting_commit": snapshot["commit"],
        },
        "context": {
            "source_commit": snapshot["commit"],
            "status": "fresh",
            "generated_at": timestamp,
            "stale_after": "material-repository-change",
        },
        "gates": {
            "specification": "pending",
            "plan_quality": "pending",
            "self_review": "pending",
            "spec_compliance": "pending",
            "code_quality": "pending",
            "acceptance": "pending",
            "verification": "pending",
            "waivers": "not_required",
            "release": "pending",
        },
        "plan_revision": {
            "version": 0,
            "decision_id": None,
            "fingerprint": None,
            "evidence": None,
        },
        "blocked_from": None,
        "last_transition": None,
        "updated_at": timestamp,
        "updated_by": "framework-next:init",
    }


def _initial_standard_state(
    project_name: str, mode: str, snapshot: Dict[str, Any], timestamp: str
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "execution_mode": normalize_mode(mode, default="standard"),
        "status": "proposed",
        "project": {"name": project_name, "mode": mode},
        "current_task": {"id": None, "status": None},
        "next_action": {"operation": "build-short-plan", "target": ".agent/PLAN.md"},
        "artifacts": {"plan": ".agent/PLAN.md"},
        "blockers": [],
        "git": {
            "base_branch": snapshot["branch"],
            "working_branch": snapshot["branch"],
            "starting_commit": snapshot["commit"],
        },
        "context": {
            "source_commit": snapshot["commit"],
            "status": "fresh",
            "generated_at": timestamp,
            "stale_after": "material-repository-change",
        },
        "verification": {"required": [], "results": {}},
        "updated_at": timestamp,
        "updated_by": "framework-next:init",
    }


def initialize_project(
    project_root: Path,
    framework_root: Path,
    *,
    project_name: str,
    mode: str = "full",
    persistent: bool = False,
) -> Path:
    """Create ``.agent`` for a project.

    ``persistent`` asks for the full kernel — phases, contracts, gates, evidence
    — at a `standard` default mode. Without it, `standard` gets the resume-only
    state it always had. The flag exists because "this project has to remember
    things across sessions" and "a defect here is catastrophic" were the same
    request: the full kernel was reachable only through `critical`, so every task
    of every phase inherited the critical lifecycle to buy memory.
    """

    project_root = project_root.expanduser().resolve()
    if not project_root.is_dir():
        raise DocumentError("project root does not exist: {}".format(project_root))
    agent_dir = project_root / ".agent"
    if agent_dir.exists():
        raise DocumentError(
            "{} already exists; initialization never overwrites it".format(agent_dir)
        )
    if mode not in {
        "fast",
        "standard",
        "critical",
        "quick",
        "full",
        "audit",
    }:
        raise DocumentError("invalid project mode: {}".format(mode))
    execution_mode = normalize_mode(mode, default="critical")
    if execution_mode == "auto":
        execution_mode = "critical"
    if execution_mode == "fast":
        raise DocumentError(
            "fast mode does not initialize .agent; use agent-framework-router"
        )

    templates = framework_root / "templates"
    timestamp = utc_now()
    snapshot = git_snapshot(project_root)
    if execution_mode == "standard" and not persistent:
        short_plan = templates / "short-plan.md"
        if not short_plan.is_file():
            raise DocumentError("missing initialization template: short-plan.md")
        temporary = Path(
            tempfile.mkdtemp(prefix=".agent-init-", dir=str(project_root))
        )
        try:
            (temporary / "PLAN.md").write_text(
                short_plan.read_text(encoding="utf-8"), encoding="utf-8"
            )
            write_frontmatter(
                temporary / "STATE.md",
                _initial_standard_state(project_name, mode, snapshot, timestamp),
                "# Standard Execution State\n\n"
                "Lightweight resume state; no formal kernel lifecycle.\n",
            )
            os.replace(str(temporary), str(agent_dir))
        except Exception:
            shutil.rmtree(str(temporary), ignore_errors=True)
            raise
        return agent_dir

    required_templates = {
        "PROJECT.md": "project.md",
        "ROADMAP.md": "project-roadmap.md",
        "CONTEXT.md": "project-context.md",
        "DECISIONS.md": "project-decisions.md",
        "REQUIREMENTS.md": "project-requirements.md",
    }
    for template in required_templates.values():
        if not (templates / template).is_file():
            raise DocumentError("missing initialization template: {}".format(template))

    temporary = Path(tempfile.mkdtemp(prefix=".agent-init-", dir=str(project_root)))
    values = {
        "PROJECT_NAME": project_name,
        "GENERATED_AT": timestamp,
        "SOURCE_COMMIT": snapshot["commit"] or "null",
        "BRANCH": snapshot["branch"] or "null",
    }
    try:
        (temporary / "phases").mkdir()
        for destination, template in required_templates.items():
            rendered = _render_template(templates / template, values)
            (temporary / destination).write_text(rendered, encoding="utf-8")
        write_frontmatter(
            temporary / "STATE.md",
            _initial_state(
                project_name,
                mode,
                snapshot,
                timestamp,
                execution_mode=execution_mode,
            ),
            "# Project State\n\nThis file is managed by the Agent Framework kernel.\n",
        )
        os.replace(str(temporary), str(agent_dir))
    except Exception:
        shutil.rmtree(str(temporary), ignore_errors=True)
        raise
    return agent_dir


def initialize_phase(
    project_root: Path,
    framework_root: Path,
    *,
    phase_id: str,
    phase_name: str,
    slug: str,
    actor: str,
) -> Path:
    project_root = project_root.expanduser().resolve()
    state_path = project_root / ".agent" / "STATE.md"
    state, body = load_frontmatter(state_path)
    if not is_persistent_state(state):
        raise DocumentError(
            "phase artifacts require the persistent kernel; this project holds the "
            "resume-only state"
        )
    if state.get("status") not in {"proposed", "discussing", "specified"}:
        raise DocumentError("cannot initialize a phase from {}".format(state.get("status")))
    if not PHASE_SLUG.match(slug):
        raise DocumentError("phase slug must be kebab-case")

    phase_dir = project_root / ".agent" / "phases" / slug
    if phase_dir.exists():
        raise DocumentError("phase directory already exists: {}".format(phase_dir))

    template_map = {
        "SPEC.md": "phase-spec.md",
        "PLAN.md": "phase-plan.md",
        "TASKS.md": "phase-tasks.md",
        "EVIDENCE.md": "evidence-ledger.md",
        "REVIEW.md": "phase-review.md",
        "HANDOFF.md": "phase-handoff.md",
    }
    values = {
        "PHASE_ID": phase_id,
        "PHASE_NAME": phase_name,
        "GENERATED_AT": utc_now(),
    }
    phase_dir.mkdir(parents=False)
    try:
        for destination, template in template_map.items():
            source = framework_root / "templates" / template
            if not source.is_file():
                raise DocumentError("missing phase template: {}".format(template))
            (phase_dir / destination).write_text(
                _render_template(source, values), encoding="utf-8"
            )
    except Exception:
        shutil.rmtree(str(phase_dir), ignore_errors=True)
        raise

    try:
        relative = phase_dir.relative_to(project_root).as_posix()
        state["phase"] = {"id": phase_id, "name": phase_name, "status": "discussing"}
        state["status"] = "discussing"
        state["artifacts"].update(
            {
                "spec": relative + "/SPEC.md",
                "plan": relative + "/PLAN.md",
                "tasks": relative + "/TASKS.md",
                "evidence": relative + "/EVIDENCE.md",
                "review": relative + "/REVIEW.md",
                "handoff": relative + "/HANDOFF.md",
            }
        )
        state["next_action"] = {"operation": "continue-discussion", "target": phase_id}
        state["updated_at"] = utc_now()
        state["updated_by"] = actor
        write_frontmatter(state_path, state, body)
    except Exception:
        shutil.rmtree(str(phase_dir), ignore_errors=True)
        raise
    return phase_dir
