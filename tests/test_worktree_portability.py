"""Portable, machine-independent resolution of git.worktree.

The same versioned `.agent/STATE.md` must validate on macOS, Linux and Windows
clones without being edited, so no local absolute path may be persisted.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from kernel.runtime.documents import (
    DocumentError,
    load_frontmatter,
    resolve_project_root,
    write_frontmatter,
)
from kernel.runtime.state_machine import validate_state
from kernel.runtime.worktree import (
    FORM_INVALID,
    FORM_LEGACY_ABSOLUTE,
    FORM_PORTABLE,
    PORTABLE_WORKTREE,
    git_toplevel,
    normalize_worktree,
    repository_identity,
    resolve_worktree,
)
from tests.helpers import FRAMEWORK_ROOT, initialized_project, read_state


MAC_LIKE = ("Users", "rougger", "dev", "fluxo-nexo")
LINUX_LIKE = ("home", "inovatecjp", "rougger", "fluxo-nexo")
WINDOWS_LEGACY = "C:\\Users\\rougger\\dev\\fluxo-nexo"


def make_repository(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(root)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    for key, value in (("user.email", "tests@example.com"), ("user.name", "tests")):
        subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
    (root / "README.md").write_text("# repo\n", encoding="utf-8")
    commit(root, "README.md", "init")
    return root


def commit(root: Path, pathspec: str, message: str) -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A", pathspec], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "--quiet", "-m", message],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def project_repository(base: Path, *parts: str) -> Path:
    root = make_repository(base.joinpath(*parts))
    initialized_project(root)
    return root


def state_path(root: Path) -> Path:
    return root / ".agent" / "STATE.md"


def set_worktree(root: Path, value) -> None:
    state, body = read_state(root)
    state["git"]["worktree"] = value
    write_frontmatter(state_path(root), state, body)


def issues_for(root: Path):
    state, _ = load_frontmatter(state_path(root))
    return validate_state(state, root)


def codes(root: Path, severity=None):
    return {
        issue["code"]
        for issue in issues_for(root)
        if severity is None or issue["severity"] == severity
    }


def worktree_codes(root: Path):
    return {code for code in codes(root) if code.startswith("git-worktree")}


def run_cli(*args: str):
    return subprocess.run(
        [sys.executable, "-m", "kernel.runtime.cli", *args],
        cwd=str(FRAMEWORK_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


class PortableResolutionTests(unittest.TestCase):
    """`worktree: "."` resolves through Git wherever the clone lives."""

    def test_portable_worktree_validates_at_repository_root(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, PORTABLE_WORKTREE)

            resolution = resolve_worktree(PORTABLE_WORKTREE, root)
            self.assertEqual(FORM_PORTABLE, resolution.form)
            self.assertEqual(root.resolve(), resolution.path)
            self.assertEqual(set(), worktree_codes(root))

    def test_resolves_when_invoked_from_a_subdirectory(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, PORTABLE_WORKTREE)
            deep = root / "apps" / "api" / "src"
            deep.mkdir(parents=True)

            self.assertEqual(root.resolve(), resolve_project_root(deep).resolve())
            resolution = resolve_worktree(PORTABLE_WORKTREE, deep)
            self.assertEqual(root.resolve(), resolution.path)

    def test_same_state_validates_from_two_different_paths(self) -> None:
        with TemporaryDirectory() as temporary:
            first = project_repository(Path(temporary), "clone-a")
            set_worktree(first, PORTABLE_WORKTREE)

            second = Path(temporary) / "elsewhere" / "clone-b"
            second.parent.mkdir(parents=True)
            shutil.copytree(str(first), str(second))

            self.assertEqual(set(), worktree_codes(first))
            self.assertEqual(set(), worktree_codes(second))
            self.assertEqual(
                state_path(first).read_bytes(), state_path(second).read_bytes()
            )

    def test_macos_like_and_linux_like_layouts_share_one_state(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            mac = project_repository(base, *MAC_LIKE)
            set_worktree(mac, PORTABLE_WORKTREE)

            linux = base.joinpath(*LINUX_LIKE)
            linux.parent.mkdir(parents=True)
            shutil.copytree(str(mac), str(linux))

            self.assertEqual(set(), worktree_codes(mac))
            self.assertEqual(set(), worktree_codes(linux))
            self.assertEqual(
                state_path(mac).read_bytes(), state_path(linux).read_bytes()
            )

    def test_git_show_toplevel_is_the_runtime_authority(self) -> None:
        with TemporaryDirectory() as temporary:
            root = make_repository(Path(temporary) / "clone-a")
            deep = root / "packages" / "core"
            deep.mkdir(parents=True)
            expected = subprocess.run(
                ["git", "-C", str(deep), "rev-parse", "--show-toplevel"],
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()

            self.assertEqual(Path(expected).resolve(), git_toplevel(deep))
            self.assertEqual(Path(expected).resolve(), resolve_project_root(deep))

    def test_linked_worktree_resolves_to_its_own_root(self) -> None:
        with TemporaryDirectory() as temporary:
            main = project_repository(Path(temporary), "main")
            set_worktree(main, PORTABLE_WORKTREE)
            commit(main, ".agent", "add agent state")

            linked = Path(temporary) / "linked"
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(main),
                    "worktree",
                    "add",
                    "--quiet",
                    "-b",
                    "feature",
                    str(linked),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )

            self.assertTrue((linked / ".git").is_file())
            self.assertEqual(linked.resolve(), git_toplevel(linked))
            self.assertEqual(
                linked.resolve(), resolve_worktree(PORTABLE_WORKTREE, linked).path
            )
            self.assertEqual(set(), worktree_codes(linked))


class LegacyAbsoluteStateTests(unittest.TestCase):
    """States written by older kernels keep loading everywhere."""

    def test_legacy_absolute_path_still_loads_in_its_original_clone(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, str(root))

            self.assertEqual(set(), codes(root, severity="error"))
            self.assertEqual({"git-worktree-legacy"}, worktree_codes(root))

    def test_legacy_absolute_path_survives_a_relocated_clone(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            mac = project_repository(base, *MAC_LIKE)
            set_worktree(mac, "/" + "/".join(MAC_LIKE))

            linux = base.joinpath(*LINUX_LIKE)
            linux.parent.mkdir(parents=True)
            shutil.copytree(str(mac), str(linux))

            self.assertEqual(set(), codes(linux, severity="error"))
            self.assertEqual({"git-worktree-legacy"}, worktree_codes(linux))

    def test_legacy_diagnostic_names_the_corrective_operation(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, "/home/other/fluxo-nexo")
            messages = [
                issue["message"]
                for issue in issues_for(root)
                if issue["code"] == "git-worktree-legacy"
            ]
            self.assertEqual(1, len(messages))
            self.assertIn("normalize-worktree", messages[0])

    def test_windows_absolute_paths_parse_as_legacy_not_invalid(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            for legacy in (WINDOWS_LEGACY, "\\\\server\\share\\fluxo-nexo"):
                resolution = resolve_worktree(legacy, root)
                self.assertEqual(FORM_LEGACY_ABSOLUTE, resolution.form, legacy)
                self.assertEqual("warning", resolution.severity, legacy)

    def test_windows_style_traversal_is_still_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            resolution = resolve_worktree("..\\other-project", root)
            self.assertEqual(FORM_INVALID, resolution.form)
            self.assertEqual("git-worktree-invalid", resolution.code)


class BoundaryTests(unittest.TestCase):
    """The resolver never leaves the repository that owns .agent/."""

    def test_outside_a_repository_fails_clearly(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "loose"
            root.mkdir()
            initialized_project(root)
            set_worktree(root, PORTABLE_WORKTREE)

            resolution = resolve_worktree(PORTABLE_WORKTREE, root)
            self.assertIsNone(resolution.path)
            self.assertEqual("git-worktree-unresolved", resolution.code)
            self.assertIn("not inside a Git work tree", resolution.message)
            self.assertIn("git-worktree-unresolved", worktree_codes(root))

    def test_agent_directory_of_another_repository_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            owner = project_repository(base, "owner")
            set_worktree(owner, PORTABLE_WORKTREE)
            intruder = make_repository(base / "intruder")
            os.symlink(str(owner / ".agent"), str(intruder / ".agent"))

            repository, reason = repository_identity(intruder)
            self.assertIsNone(repository)
            self.assertIn("another repository", reason)
            self.assertEqual(
                "git-worktree-unresolved",
                resolve_worktree(PORTABLE_WORKTREE, intruder).code,
            )

    def test_symlinked_agent_directory_outside_any_repository_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = make_repository(base / "clone-a")
            outside = base / "outside"
            outside.mkdir()
            initialized_project(outside)
            os.symlink(str(outside / ".agent"), str(root / ".agent"))

            self.assertIsNone(repository_identity(root)[0])
            self.assertEqual(
                "git-worktree-unresolved",
                resolve_worktree(PORTABLE_WORKTREE, root).code,
            )

    def test_relative_traversal_is_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = project_repository(base, "clone-a")
            make_repository(base / "other")
            for escape in ("../other", "../../etc", "sub/../../other"):
                resolution = resolve_worktree(escape, root)
                self.assertEqual(FORM_INVALID, resolution.form, escape)
                self.assertIsNone(resolution.path, escape)

    def test_relative_paths_other_than_dot_are_refused(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            for value in ("sub", "./sub", "apps/api", 42, ["."]):
                resolution = resolve_worktree(value, root)
                self.assertEqual(FORM_INVALID, resolution.form, value)
                self.assertEqual("git-worktree-invalid", resolution.code, value)


class NormalizationTests(unittest.TestCase):
    """Normalization is explicit, minimal and idempotent."""

    def test_validation_never_modifies_the_state_file(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, "/home/other/fluxo-nexo")
            before = state_path(root).read_bytes()

            issues_for(root)
            resolve_worktree("/home/other/fluxo-nexo", root)
            normalize_worktree(state_path(root), root, apply=False)

            self.assertEqual(before, state_path(root).read_bytes())

    def test_legacy_state_normalizes_to_the_portable_value(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, str(root))

            outcome = normalize_worktree(state_path(root), root)
            self.assertTrue(outcome["changed"])
            self.assertEqual(PORTABLE_WORKTREE, outcome["after"])

            state, _ = load_frontmatter(state_path(root))
            self.assertEqual(PORTABLE_WORKTREE, state["git"]["worktree"])
            self.assertEqual(set(), worktree_codes(root))

    def test_normalization_changes_only_the_worktree_line(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, "/home/inovatecjp/rougger/fluxo-nexo")
            before = state_path(root).read_text(encoding="utf-8").splitlines()

            normalize_worktree(state_path(root), root)
            after = state_path(root).read_text(encoding="utf-8").splitlines()

            self.assertEqual(len(before), len(after))
            differing = [
                index for index, line in enumerate(before) if line != after[index]
            ]
            self.assertEqual(1, len(differing))
            self.assertIn('"worktree"', after[differing[0]])
            self.assertIn('"."', after[differing[0]])

    def test_normalization_is_idempotent(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, str(root))

            normalize_worktree(state_path(root), root)
            once = state_path(root).read_bytes()
            second = normalize_worktree(state_path(root), root)

            self.assertFalse(second["changed"])
            self.assertEqual("already-portable", second["reason"])
            self.assertEqual(once, state_path(root).read_bytes())

    def test_normalization_never_writes_another_absolute_path(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            mac = project_repository(base, *MAC_LIKE)
            set_worktree(mac, "/" + "/".join(LINUX_LIKE))

            normalize_worktree(state_path(mac), mac)
            text = state_path(mac).read_text(encoding="utf-8")

            self.assertNotIn(str(mac), text)
            self.assertNotIn("/".join(LINUX_LIKE), text)
            self.assertIn('"worktree": "."', text)

    def test_normalization_is_refused_without_a_provable_repository(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary) / "loose"
            root.mkdir()
            initialized_project(root)
            set_worktree(root, "/home/other/fluxo-nexo")
            before = state_path(root).read_bytes()

            with self.assertRaises(DocumentError) as raised:
                normalize_worktree(state_path(root), root)
            self.assertIn("refusing to normalize", str(raised.exception))
            self.assertEqual(before, state_path(root).read_bytes())


class SerializationTests(unittest.TestCase):
    """Nothing machine-specific ever reaches the versioned document."""

    def test_initialization_never_serializes_a_local_absolute_path(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), *MAC_LIKE)
            text = state_path(root).read_text(encoding="utf-8")

            self.assertNotIn(str(root), text)
            self.assertNotIn(temporary, text)
            self.assertIsNone(json.loads(text.split("---")[1])["git"]["worktree"])

    def test_switching_machines_produces_no_diff(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            mac = project_repository(base, *MAC_LIKE)
            set_worktree(mac, PORTABLE_WORKTREE)
            commit(mac, ".agent", "add portable agent state")

            work = base.joinpath("mnt", "work", "fluxo-nexo")
            work.parent.mkdir(parents=True)
            subprocess.run(
                ["git", "clone", "--quiet", str(mac), str(work)],
                check=True,
                stdout=subprocess.DEVNULL,
            )

            self.assertEqual(set(), worktree_codes(work))
            normalize_worktree(state_path(work), work)
            porcelain = subprocess.run(
                ["git", "-C", str(work), "status", "--porcelain=v1", "--", ".agent"],
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout
            self.assertEqual("", porcelain)


class CommandLineTests(unittest.TestCase):
    """End-to-end CLI behaviour across repositories at different paths."""

    def test_validate_and_normalize_across_two_clone_paths(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            mac = project_repository(base, *MAC_LIKE)
            set_worktree(mac, "/" + "/".join(MAC_LIKE))

            linux = base.joinpath(*LINUX_LIKE)
            linux.parent.mkdir(parents=True)
            shutil.copytree(str(mac), str(linux))

            for root in (mac, linux):
                validated = run_cli("validate", "--project", str(root))
                self.assertEqual(0, validated.returncode, validated.stdout)

            checked = run_cli("normalize-worktree", "--project", str(linux), "--check")
            self.assertEqual(0, checked.returncode, checked.stdout)
            self.assertIn("not written", checked.stdout)
            self.assertEqual(
                state_path(mac).read_bytes(), state_path(linux).read_bytes()
            )

            applied = run_cli("normalize-worktree", "--project", str(linux))
            self.assertEqual(0, applied.returncode, applied.stdout)
            self.assertIn("'.'", applied.stdout)

            repeated = run_cli("normalize-worktree", "--project", str(linux))
            self.assertEqual(0, repeated.returncode, repeated.stdout)
            self.assertIn("already portable", repeated.stdout)

            state, _ = load_frontmatter(state_path(linux))
            self.assertEqual(PORTABLE_WORKTREE, state["git"]["worktree"])

            revalidated = run_cli("validate", "--project", str(linux))
            self.assertEqual(0, revalidated.returncode, revalidated.stdout)

    def test_cli_resolves_the_project_from_a_subdirectory(self) -> None:
        with TemporaryDirectory() as temporary:
            root = project_repository(Path(temporary), "clone-a")
            set_worktree(root, PORTABLE_WORKTREE)
            deep = root / "apps" / "api"
            deep.mkdir(parents=True)

            validated = run_cli("validate", "--project", str(deep))
            self.assertEqual(0, validated.returncode, validated.stdout)
            self.assertIn("state: valid", validated.stdout)

    def test_framework_verifier_reports_no_problems(self) -> None:
        completed = subprocess.run(
            ["bash", str(FRAMEWORK_ROOT / "installers" / "verify-framework.sh")],
            cwd=str(FRAMEWORK_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout)
        self.assertIn("problems: 0", completed.stdout)


if __name__ == "__main__":
    unittest.main()
