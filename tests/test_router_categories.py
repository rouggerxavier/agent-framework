from __future__ import annotations

import unittest

from kernel.runtime.categories import load_categories
from kernel.runtime.execution_modes import route_execution
from tests.helpers import FRAMEWORK_ROOT, router_text

ROUTER = FRAMEWORK_ROOT / "skills" / "agent-framework-router"


class RouterCategoryTests(unittest.TestCase):
    def test_index_lists_every_category_file_and_its_floor(self) -> None:
        core = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
        categories = load_categories()
        self.assertEqual(
            len(list((ROUTER / "categories").glob("*.md"))), len(categories)
        )
        for category in categories:
            with self.subTest(category=category["category"]):
                self.assertIn(category["file"].split("/", 2)[2], core)
                for asset in category["required"]:
                    name = asset.split("/")[1] if asset.startswith("skills/") else asset
                    self.assertIn(name, core)

    def test_every_skill_is_reachable_from_the_router(self) -> None:
        text = router_text()
        for skill in sorted((FRAMEWORK_ROOT / "skills").iterdir()):
            if (skill / "SKILL.md").is_file():
                self.assertIn(skill.name, text, skill.name)

    def test_frontend_request_returns_the_frontend_floor(self) -> None:
        decision = route_execution("Implemente a tela de fornecedores com animacao.")
        self.assertEqual("frontend", decision["category"])
        for asset in (
            "skills/apple-design/SKILL.md",
            "impeccable:impeccable",
            "design-taste-frontend",
        ):
            self.assertIn(asset, decision["assets_selected"])

    def test_agent_request_returns_the_agent_design_rubric(self) -> None:
        decision = route_execution("O chatbot encaminha demais; ajuste o prompt.")
        self.assertEqual("agentes", decision["category"])
        self.assertIn("rubrics/agent-design.md", decision["assets_selected"])

    def test_specific_category_beats_generic_software_on_a_tie(self) -> None:
        decision = route_execution("Corrija o typo no titulo da pagina.")
        self.assertEqual("frontend", decision["category"])

    def test_no_keyword_hit_leaves_the_category_empty(self) -> None:
        decision = route_execution("Ajuste o helper de datas.")
        self.assertEqual("", decision["category"])
        self.assertEqual("", decision["category_file"])


if __name__ == "__main__":
    unittest.main()
