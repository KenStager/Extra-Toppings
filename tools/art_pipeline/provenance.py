"""Credential-free provenance records for generated candidates."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_FORBIDDEN_KEY = re.compile(
    r"(key|token|secret|password|credential|authorization|bearer)", re.IGNORECASE
)


def scrub(record: Any) -> Any:
    """Drop any field whose name suggests it could carry a credential."""
    if isinstance(record, dict):
        return {
            k: scrub(v) for k, v in record.items() if not _FORBIDDEN_KEY.search(k)
        }
    if isinstance(record, list):
        return [scrub(v) for v in record]
    return record


def write_record(record: dict[str, Any], path: str | Path) -> dict[str, Any]:
    """Scrub and persist one provenance record; returns what was written."""
    clean = scrub(record)
    Path(path).write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n")
    return clean
