"""Deterministic Markdown frontmatter and repository helpers."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class DocumentError(ValueError):
    """Raised when a persistent kernel document is malformed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_frontmatter(path: Path) -> Tuple[Dict[str, Any], str]:
    """Load JSON-compatible YAML frontmatter and the Markdown body."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DocumentError("cannot read {}: {}".format(path, exc)) from exc

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise DocumentError("{} must start with frontmatter delimiter".format(path))

    closing = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing = index
            break
    if closing is None:
        raise DocumentError("{} has unclosed frontmatter".format(path))

    raw = "".join(lines[1:closing]).strip()
    if not raw:
        raise DocumentError("{} has empty frontmatter".format(path))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DocumentError(
            "{} frontmatter must be JSON-compatible YAML: {}".format(path, exc)
        ) from exc
    if not isinstance(data, dict):
        raise DocumentError("{} frontmatter must be an object".format(path))
    return data, "".join(lines[closing + 1 :])


def render_frontmatter(data: Dict[str, Any], body: str) -> str:
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    normalized_body = body.lstrip("\n")
    return "---\n{}\n---\n\n{}".format(serialized, normalized_body)


def write_frontmatter(path: Path, data: Dict[str, Any], body: str) -> None:
    """Atomically replace a persistent Markdown document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_frontmatter(data, body)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(path.name), dir=str(path.parent), text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()


def write_state(path: Path, data: Dict[str, Any], body: str) -> None:
    """Write ``STATE.md``, regenerating its body from the frontmatter.

    Every formal state write goes through here rather than through
    :func:`write_frontmatter`, so the prose can never describe a phase the
    frontmatter has already left. ``body`` is the *previous* body: only the
    regions it fenced for keeping survive.

    Nothing reads the body back, and the plan fingerprint covers ``PLAN.md`` and
    ``TASKS.md`` only, so regenerating it cannot change a kernel decision or
    break a seal.
    """

    from .state_body import project_state_body

    write_frontmatter(path, data, project_state_body(data, body))


def resolve_project_root(start: Path) -> Path:
    """Resolve the nearest initialized project, then the Git repository root.

    Works from the repository root, from any subdirectory, and from a linked
    worktree, because the fallback authority is `git rev-parse --show-toplevel`
    rather than a persisted path.
    """
    from .worktree import git_toplevel

    candidate = start.expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for directory in (candidate,) + tuple(candidate.parents):
        if (directory / ".agent" / "STATE.md").is_file():
            return directory
    return git_toplevel(candidate) or candidate


def safe_project_path(root: Path, relative: str) -> Path:
    """Resolve a project-relative path without allowing traversal."""
    if not relative or Path(relative).is_absolute():
        raise DocumentError("artifact path must be project-relative: {!r}".format(relative))
    root = root.resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise DocumentError("artifact path escapes project root: {}".format(relative)) from exc
    return resolved


def git_snapshot(root: Path) -> Dict[str, Any]:
    """Return observable Git state without failing outside a repository."""

    def run(*args: str, raw: bool = False) -> Optional[str]:
        completed = subprocess.run(
            ["git", "-C", str(root)] + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        if completed.returncode != 0:
            return None
        # Porcelain status is column-oriented: its leading space carries meaning,
        # so it must survive. Everything else is a single token.
        return completed.stdout if raw else completed.stdout.strip()

    inside = run("rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return {
            "is_repository": False,
            "branch": None,
            "commit": None,
            "dirty": False,
            "changed_files": [],
        }

    branch = run("symbolic-ref", "--short", "-q", "HEAD")
    commit = run("rev-parse", "HEAD")
    porcelain = run("status", "--porcelain=v1", raw=True) or ""
    changed = [line[3:] for line in porcelain.splitlines() if len(line) > 3]
    return {
        "is_repository": True,
        "branch": branch,
        "commit": commit,
        "dirty": bool(porcelain.strip()),
        "changed_files": changed,
    }

