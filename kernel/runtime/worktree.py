"""Single source of truth for resolving the project worktree at runtime.

The shared, versioned state never stores a machine-specific absolute path.
`git.worktree` is portable: `"."` means "the Git repository that contains
`.agent/`". The concrete absolute path is discovered at runtime through
`git rev-parse --show-toplevel` and kept in memory only.

Absolute values remain readable as a legacy format so that states written by
older kernels keep loading on any machine; they are reported for explicit
normalization instead of being treated as an invalid project.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, NamedTuple, Optional

from .documents import DocumentError, load_frontmatter


PORTABLE_WORKTREE = "."

FORM_UNSET = "unset"
FORM_PORTABLE = "portable"
FORM_LEGACY_ABSOLUTE = "legacy-absolute"
FORM_INVALID = "invalid"

NORMALIZE_HINT = (
    "run `framework-next normalize-worktree` to rewrite the field as {!r}".format(
        PORTABLE_WORKTREE
    )
)


class WorktreeResolution(NamedTuple):
    """Outcome of resolving the persisted `git.worktree` field."""

    declared: Any
    form: str
    path: Optional[Path]
    repository_root: Optional[Path]
    code: Optional[str]
    message: Optional[str]
    severity: str

    @property
    def is_portable(self) -> bool:
        return self.form in {FORM_UNSET, FORM_PORTABLE}

    @property
    def needs_normalization(self) -> bool:
        return self.form == FORM_LEGACY_ABSOLUTE


def git_toplevel(start: Path) -> Optional[Path]:
    """Runtime authority for the repository root.

    Equivalent to `git rev-parse --show-toplevel`, evaluated from ``start``.
    Returns ``None`` outside a work tree. Linked worktrees report their own
    root, which is exactly what the kernel operates on.
    """
    directory = start.expanduser()
    if directory.is_file():
        directory = directory.parent
    if not directory.is_dir():
        return None
    completed = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if completed.returncode != 0:
        return None
    output = completed.stdout.strip()
    if not output:
        return None
    return Path(output).resolve()


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def repository_identity(project_root: Path):
    """Prove which repository owns ``.agent/``, without any persisted path.

    Identity is established from Git plus the real location of ``.agent/``:
    the directory must live inside the repository that Git reports for the
    project root. A ``.agent/`` reached through a symlink that leaves the
    repository is rejected, so state belonging to another project is never
    adopted just because a branch or directory name matches.

    Returns ``(repository_root, reason)``; ``repository_root`` is ``None``
    when ownership cannot be proven and ``reason`` explains why.
    """
    root = project_root.expanduser().resolve()
    top = git_toplevel(root)
    if top is None:
        return None, "{} is not inside a Git work tree".format(root)
    if not _is_inside(root, top):
        return None, "{} resolves outside its own repository {}".format(root, top)
    agent_dir = root / ".agent"
    if agent_dir.exists() and not _is_inside(agent_dir.resolve(), top):
        return (
            None,
            "{} resolves to {}, which belongs to another repository than {}".format(
                agent_dir, agent_dir.resolve(), top
            ),
        )
    return top, ""


def repository_root_for(project_root: Path) -> Optional[Path]:
    """Repository root that owns ``.agent/``, or ``None`` when unprovable."""
    return repository_identity(project_root)[0]


def _looks_absolute(value: str) -> bool:
    """Detect POSIX and Windows absolute paths from any host platform."""
    if value.startswith("/") or value.startswith("\\"):
        return True
    if len(value) >= 3 and value[1] == ":" and value[2] in "/\\" and value[0].isalpha():
        return True
    return False


def _has_traversal(value: str) -> bool:
    return any(part == ".." for part in value.replace("\\", "/").split("/"))


def resolve_worktree(declared: Any, project_root: Path) -> WorktreeResolution:
    """Resolve the persisted `git.worktree` field for the current machine.

    Never rewrites the field and never returns a path outside the repository.
    """
    root = project_root.expanduser().resolve()
    repository, reason = repository_identity(root)

    def result(form, path, code=None, message=None, severity="error"):
        return WorktreeResolution(
            declared=declared,
            form=form,
            path=path,
            repository_root=repository,
            code=code,
            message=message,
            severity=severity,
        )

    if declared is None or declared == "":
        return result(FORM_UNSET, repository)

    if not isinstance(declared, str):
        return result(
            FORM_INVALID,
            None,
            "git-worktree-invalid",
            "git.worktree must be the portable string {!r}; got {!r}".format(
                PORTABLE_WORKTREE, declared
            ),
        )

    value = declared.strip()

    if value == PORTABLE_WORKTREE:
        if repository is None:
            return result(
                FORM_PORTABLE,
                None,
                "git-worktree-unresolved",
                "cannot resolve git.worktree {!r}: {}. Run the kernel from inside "
                "the clone that owns .agent/".format(PORTABLE_WORKTREE, reason),
            )
        return result(FORM_PORTABLE, repository)

    if _looks_absolute(value):
        if repository is None:
            return result(
                FORM_LEGACY_ABSOLUTE,
                None,
                "git-worktree-mismatch",
                "git.worktree records the legacy absolute path {!r} and the state "
                "cannot be attributed to a repository here: {}".format(value, reason),
            )
        return result(
            FORM_LEGACY_ABSOLUTE,
            repository,
            "git-worktree-legacy",
            "git.worktree records the legacy absolute path {!r}; the repository "
            "root resolved at runtime is {}. The state is valid here — {}.".format(
                value, repository, NORMALIZE_HINT
            ),
            severity="warning",
        )

    if _has_traversal(value):
        return result(
            FORM_INVALID,
            None,
            "git-worktree-invalid",
            "git.worktree must not escape the repository with '..': {!r}".format(value),
        )

    return result(
        FORM_INVALID,
        None,
        "git-worktree-invalid",
        "git.worktree accepts only the portable value {!r} or a legacy absolute "
        "path; got the relative path {!r} — {}".format(
            PORTABLE_WORKTREE, value, NORMALIZE_HINT
        ),
    )


_WORKTREE_LINE = re.compile(
    r'^(?P<head>[ \t]*"worktree"[ \t]*:[ \t]*)'
    r'(?P<value>"(?:[^"\\]|\\.)*")'
    r"(?P<tail>[ \t]*,?[ \t]*)$"
)


def _frontmatter_bounds(lines):
    """Return the half-open line range covering the frontmatter payload."""
    if not lines or lines[0].strip() != "---":
        raise DocumentError("STATE.md must start with frontmatter delimiter")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return 1, index
    raise DocumentError("STATE.md has unclosed frontmatter")


def normalize_worktree(
    state_path: Path, project_root: Path, *, apply: bool = True
) -> Dict[str, Any]:
    """Rewrite a legacy absolute `git.worktree` as the portable value.

    Touches nothing else: the single field line is substituted in place, so the
    rest of the document stays byte-for-byte identical. Idempotent, and refused
    outright when the owning repository cannot be proven.
    """
    state, _ = load_frontmatter(state_path)
    git_state = state.get("git")
    if not isinstance(git_state, dict) or "worktree" not in git_state:
        return {
            "changed": False,
            "reason": "no-field",
            "before": None,
            "after": None,
            "message": "git.worktree is not present; nothing to normalize",
        }

    declared = git_state.get("worktree")
    resolution = resolve_worktree(declared, project_root)

    if resolution.form in {FORM_UNSET, FORM_PORTABLE} and resolution.code is None:
        return {
            "changed": False,
            "reason": "already-portable",
            "before": declared,
            "after": declared,
            "message": "git.worktree is already portable",
        }
    if resolution.form == FORM_INVALID:
        raise DocumentError(resolution.message)
    if resolution.repository_root is None:
        raise DocumentError(
            "refusing to normalize: {}".format(
                resolution.message
                or "the repository owning .agent/ could not be proven"
            )
        )

    text = state_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines)

    matches = []
    for index in range(start, end):
        match = _WORKTREE_LINE.match(lines[index].rstrip("\r\n"))
        if match and json.loads(match.group("value")) == declared:
            matches.append((index, match))
    if len(matches) != 1:
        raise DocumentError(
            "refusing to normalize: expected exactly one git.worktree line in "
            "{}, found {}".format(state_path, len(matches))
        )

    index, match = matches[0]
    original = lines[index]
    ending = original[len(original.rstrip("\r\n")) :]
    lines[index] = "{}{}{}{}".format(
        match.group("head"),
        json.dumps(PORTABLE_WORKTREE),
        match.group("tail"),
        ending,
    )
    updated_text = "".join(lines)

    expected = json.loads(json.dumps(state))
    expected["git"]["worktree"] = PORTABLE_WORKTREE
    verified, _ = load_frontmatter_from_text(updated_text, state_path)
    if verified != expected:
        raise DocumentError(
            "refusing to normalize: the rewritten frontmatter of {} does not "
            "match the expected single-field change".format(state_path)
        )

    if apply:
        _replace_atomically(state_path, updated_text)
    return {
        "changed": True,
        "reason": "normalized",
        "before": declared,
        "after": PORTABLE_WORKTREE,
        "message": "git.worktree {!r} -> {!r}".format(declared, PORTABLE_WORKTREE),
    }


def load_frontmatter_from_text(text: str, path: Path):
    """Parse frontmatter from in-memory text, mirroring `load_frontmatter`."""
    lines = text.splitlines(keepends=True)
    start, end = _frontmatter_bounds(lines)
    raw = "".join(lines[start:end]).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DocumentError(
            "{} frontmatter must be JSON-compatible YAML: {}".format(path, exc)
        ) from exc
    if not isinstance(data, dict):
        raise DocumentError("{} frontmatter must be an object".format(path))
    return data, "".join(lines[end + 1 :])


def _replace_atomically(path: Path, text: str) -> None:
    """Replace the document without re-rendering its frontmatter."""
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(path.name), dir=str(path.parent), text=True
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
    finally:
        if temporary.exists():
            temporary.unlink()
