"""Append-only evidence ledger events."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from .documents import DocumentError, utc_now


VALID_EVIDENCE_KINDS = {
    "command",
    "test",
    "diff-inspection",
    "screenshot",
    "database-query",
    "api-response",
    "log",
    "self-review",
    "spec-compliance",
    "code-quality",
    "manual-validation",
    "waiver",
    "blocker",
    "correction",
    "commit",
    "task-start",
    "gate",
    "plan-amendment",
}


def append_evidence_event(ledger: Path, event: Dict[str, Any]) -> Dict[str, Any]:
    if event.get("kind") not in VALID_EVIDENCE_KINDS:
        raise DocumentError("invalid evidence kind: {!r}".format(event.get("kind")))
    for field in ("task_id", "actor", "status", "summary", "source"):
        if not event.get(field):
            raise DocumentError("evidence event requires {}".format(field))
    criteria = event.get("acceptance_criteria", [])
    if not isinstance(criteria, list):
        raise DocumentError("acceptance_criteria must be an array")

    recorded = dict(event)
    recorded.setdefault("recorded_at", utc_now())
    try:
        existing = ledger.read_text(encoding="utf-8")
    except OSError as exc:
        raise DocumentError("cannot read evidence ledger: {}".format(exc)) from exc
    block = (
        "\n\n### Event {time} — {kind}\n\n```json\n{payload}\n```\n".format(
            time=recorded["recorded_at"],
            kind=recorded["kind"],
            payload=json.dumps(recorded, ensure_ascii=False, indent=2),
        )
    )
    descriptor, name = tempfile.mkstemp(
        prefix=".{}.".format(ledger.name), dir=str(ledger.parent), text=True
    )
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(existing)
            handle.write(block)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(ledger))
    finally:
        if temporary.exists():
            temporary.unlink()
    return recorded

