"""Category routing read from the router skill's own category files.

The files under ``skills/agent-framework-router/categories`` are the single
source: their frontmatter carries the keywords and the mandatory assets, their
body carries the table the agent reads. Nothing here repeats that content.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from .documents import DocumentError, load_frontmatter

ROUTER_RELATIVE = Path("skills") / "agent-framework-router"
CATEGORIES_DIR = Path(__file__).resolve().parents[2] / ROUTER_RELATIVE / "categories"

# Matches every ordinary change, so it only wins when nothing specific does.
GENERIC_CATEGORY = "software"


def load_categories(directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    directory = directory or CATEGORIES_DIR
    categories = []
    for path in sorted(directory.glob("*.md")):
        try:
            meta, _ = load_frontmatter(path)
        except DocumentError:
            continue
        categories.append(
            {
                "category": meta["category"],
                "keywords": list(meta.get("keywords", [])),
                "required": list(meta.get("required", [])),
                "file": (ROUTER_RELATIVE / "categories" / path.name).as_posix(),
            }
        )
    return categories


def route_category(
    normalized_request: str, directory: Optional[Path] = None
) -> Dict[str, Any]:
    """Pick the category whose keywords hit the request most often.

    ``normalized_request`` is casefolded and accent-free. No hit returns an empty
    category: the agent then reads the index instead of trusting a guess.
    """

    best: Optional[Dict[str, Any]] = None
    best_rank = (0, False)
    for category in load_categories(directory):
        # shortcut: counts keyword hits, no semantics; the agent confirms the
        # category against the index. Upgrade if misroutes show up in practice.
        hits = sum(
            1
            for keyword in category["keywords"]
            if re.search(r"\b(?:{})".format(keyword), normalized_request)
        )
        rank = (hits, category["category"] != GENERIC_CATEGORY)
        if hits and rank > best_rank:
            best, best_rank = category, rank
    if best is None:
        return {"category": "", "category_file": "", "required": []}
    return {
        "category": best["category"],
        "category_file": best["file"],
        "required": best["required"],
    }
