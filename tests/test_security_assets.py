import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest

from tests.helpers import FRAMEWORK_ROOT


SECURITY_SKILLS = (
    "injection-vulnerability-auditor",
    "authn-authz-auditor",
    "crypto-secrets-auditor",
    "infra-security-auditor",
    "security-privacy-audit",
    "agent-security-auditor",
)

REQUIRED_HEADINGS = (
    "## Objetivo",
    "## Quando usar",
    "## Quando nao usar",
    "## Workflow",
    "## Saida obrigatoria",
    "## Criterios de aceite",
    "## Arquivos de apoio",
)


def skill_text(name: str) -> str:
    return (FRAMEWORK_ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class SecuritySkillTests(unittest.TestCase):
    def test_security_skills_follow_the_skill_standard(self) -> None:
        for name in SECURITY_SKILLS:
            with self.subTest(skill=name):
                content = skill_text(name)
                self.assertIn(f"name: {name}\n", content)
                description = re.search(r"^description: (.+)$", content, re.M)
                self.assertIsNotNone(description, "missing description")
                self.assertTrue(description.group(1).startswith("Use para"))
                self.assertLessEqual(len(description.group(1)), 240)
                for heading in REQUIRED_HEADINGS:
                    self.assertIn(heading, content, heading)

    def test_security_skill_support_files_resolve(self) -> None:
        """A referencia quebrada some do relatorio e leva o auditor a improvisar."""

        for name in SECURITY_SKILLS:
            content = skill_text(name)
            skill_dir = FRAMEWORK_ROOT / "skills" / name
            for reference in re.findall(r"\.\./\.\./[\w./-]+\.md", content):
                with self.subTest(skill=name, reference=reference):
                    self.assertTrue(
                        (skill_dir / reference).resolve().exists(),
                        f"{name} points at missing {reference}",
                    )

    def test_new_auditors_do_not_overlap_in_scope(self) -> None:
        specialists = SECURITY_SKILLS[:4]
        for name in specialists:
            content = skill_text(name)
            others = [other for other in specialists if other != name]
            with self.subTest(skill=name):
                section = content.split("## Quando nao usar")[1].split("##")[0]
                self.assertTrue(
                    any(other in section for other in others),
                    f"{name} does not route away from the sibling auditors",
                )

    def test_router_offers_every_security_auditor(self) -> None:
        router = skill_text("agent-framework-router")
        for name in SECURITY_SKILLS + ("dependency-risk-auditor",):
            self.assertIn(name, router, name)


class SecurityWorkflowTests(unittest.TestCase):
    def test_workflow_binds_each_trigger_to_an_auditor(self) -> None:
        workflow = (FRAMEWORK_ROOT / "workflows" / "security-review.md").read_text(
            encoding="utf-8"
        )
        for name in SECURITY_SKILLS + (
            "dependency-risk-auditor",
            "feature-logging-planner",
        ):
            self.assertIn(name, workflow, name)

    def test_lifecycle_workflows_make_security_non_discretionary(self) -> None:
        """Um gatilho de seguranca no diff nao pode depender de lembrar de pedir."""

        for name in ("high-risk-change.md", "release.md", "backend-change.md"):
            content = (FRAMEWORK_ROOT / "workflows" / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("security-review.md", content)

    def test_review_gate_checks_security_triggers(self) -> None:
        gate = skill_text("code-review-gate")
        self.assertIn("workflows/security-review.md", gate)

    def test_orphan_security_layer_is_gone(self) -> None:
        self.assertFalse((FRAMEWORK_ROOT / ".security").exists())


class SecurityCoverageDocTests(unittest.TestCase):
    def test_every_listed_class_names_an_existing_skill(self) -> None:
        doc = (FRAMEWORK_ROOT / "docs" / "security-coverage.md").read_text(
            encoding="utf-8"
        )
        rows = re.findall(r"^\| (\d+) \| ([^|]+)\| `([\w-]+)` \| ([^|]+)\|", doc, re.M)
        self.assertEqual(
            [str(number) for number in range(1, 21)],
            [row[0] for row in rows],
            "coverage table must map classes 1 through 20",
        )
        for number, _, skill, rubric in rows:
            with self.subTest(vulnerability=number):
                self.assertTrue(
                    (FRAMEWORK_ROOT / "skills" / skill / "SKILL.md").exists(),
                    f"class {number} points at missing skill {skill}",
                )
                referenced = re.search(r"`(rubrics/[\w-]+\.md)`", rubric)
                if referenced:
                    self.assertTrue(
                        (FRAMEWORK_ROOT / referenced.group(1)).exists(),
                        f"class {number} points at missing {referenced.group(1)}",
                    )

    def test_prompt_injection_eval_covers_the_release_blocking_cases(self) -> None:
        eval_template = (
            FRAMEWORK_ROOT / "templates" / "prompt-injection-eval.md"
        ).read_text(encoding="utf-8")
        for case in ("PI-03", "PI-04", "PI-05"):
            self.assertIn(case, eval_template, case)
        self.assertIn(
            "prompt-injection-eval.md", skill_text("agent-security-auditor")
        )


class SecurityCheckScriptTests(unittest.TestCase):
    """O script e a primeira passada automatica; se ele nao acusa, nada acusa."""

    def _fixture_repo(self, root: Path) -> None:
        subprocess.run(
            ["git", "init", "--quiet", str(root)], check=True, capture_output=True
        )
        scripts = root / "scripts"
        scripts.mkdir()
        script = scripts / "security-check"
        script.write_bytes((FRAMEWORK_ROOT / "scripts" / "security-check").read_bytes())
        script.chmod(0o755)

    def _run(self, root: Path, strict: bool = False) -> subprocess.CompletedProcess:
        environment = dict(os.environ)
        if strict:
            environment["SECURITY_STRICT"] = "1"
        return subprocess.run(
            [str(root / "scripts" / "security-check")],
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_clean_repository_passes(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixture_repo(root)
            (root / "app.py").write_text("def add(a, b):\n    return a + b\n", "utf-8")

            result = self._run(root)
            self.assertEqual(0, result.returncode, result.stdout)
            self.assertIn("security check: ok", result.stdout)

    def test_planted_issues_are_reported(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixture_repo(root)

            (root / "crypto.py").write_text(
                "import hashlib\n"
                "import requests\n\n"
                "def digest(value):\n"
                "    return hashlib.md5(value).hexdigest()\n\n"
                "def fetch(url):\n"
                "    return requests.get(url, verify=False)\n",
                "utf-8",
            )
            (root / "run.py").write_text(
                "import os\nimport pickle\n\n"
                "def run(name):\n"
                "    os.system('echo ' + name)\n\n"
                "def load(blob):\n"
                "    return pickle.loads(blob)\n",
                "utf-8",
            )
            (root / "settings.py").write_text(
                "DEBUG = True\nALLOWED_HOSTS = ['*']\n", "utf-8"
            )
            (root / "Dockerfile").write_text(
                "FROM python:latest\nCOPY . /app\nCMD ['python', 'run.py']\n", "utf-8"
            )
            (root / "deploy.yaml").write_text(
                "spec:\n  containers:\n    - name: api\n"
                "      securityContext:\n        privileged: true\n",
                "utf-8",
            )

            result = self._run(root)
            self.assertEqual(0, result.returncode, "warnings alone must not fail")
            for expected in (
                "weak crypto",
                "dangerous sinks",
                "insecure configuration",
                "privileged",
                "no USER directive",
                "base image pinned to :latest",
            ):
                self.assertIn(expected, result.stdout, expected)

            strict = self._run(root, strict=True)
            self.assertEqual(1, strict.returncode, strict.stdout)
            self.assertIn("SECURITY_STRICT=1", strict.stdout)

    def test_secret_and_tracked_env_fail_the_check(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixture_repo(root)
            (root / "config.py").write_text(
                'API_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "utf-8"
            )

            result = self._run(root)
            self.assertEqual(1, result.returncode, result.stdout)
            self.assertIn("possible secrets found", result.stdout)
            self.assertNotIn("AKIAIOSFODNN7EXAMPLE", result.stdout)

    def test_ignored_paths_are_skipped_but_always_announced(self) -> None:
        """Supressao silenciosa transformaria a checagem em teatro."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixture_repo(root)
            fixtures = root / "fixtures"
            fixtures.mkdir()
            (fixtures / "vulnerable.py").write_text(
                "import hashlib\n\n"
                "def digest(value):\n"
                "    return hashlib.md5(value).hexdigest()\n",
                "utf-8",
            )

            noisy = self._run(root)
            self.assertIn("weak crypto", noisy.stdout)

            (root / ".security-ignore").write_text(
                "# deliberate insecure samples\nfixtures/*\n", "utf-8"
            )

            quiet = self._run(root)
            self.assertIn(".security-ignore active", quiet.stdout)
            self.assertIn("fixtures/*", quiet.stdout)
            self.assertIn("weak crypto / disabled TLS verification: nothing found", quiet.stdout)

    def test_framework_declares_its_own_ignored_fixtures(self) -> None:
        ignore_file = FRAMEWORK_ROOT / ".security-ignore"
        self.assertTrue(ignore_file.exists())
        self.assertIn(
            "tests/test_security_assets.py",
            ignore_file.read_text(encoding="utf-8"),
            "the fixture file must be declared, not silently tolerated",
        )

    def test_missing_python_scanner_is_a_declared_gap(self) -> None:
        """Sem scanner disponivel o relatorio registra lacuna, nunca 'sem CVE'."""

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._fixture_repo(root)
            (root / "requirements.txt").write_text("requests==2.31.0\n", "utf-8")

            result = self._run(root)
            self.assertNotIn("no dependency manifest", result.stdout)
            if "pip-audit completed" not in result.stdout:
                self.assertIn("pip-audit not installed", result.stdout)


if __name__ == "__main__":
    unittest.main()
