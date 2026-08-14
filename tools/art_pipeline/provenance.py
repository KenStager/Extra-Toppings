"""Credential-free provenance records for generated candidates.

Schema v2 (P2 ruling): every generation record must be replayable and
byte-verifiable. Required fields are listed in V2_REQUIRED; use
missing_v2_fields() before writing and attach_hashes() to bind the
record to the exact artifacts it describes.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_FORBIDDEN_KEY = re.compile(
    r"(key|token|secret|password|credential|authorization|bearer)", re.IGNORECASE
)

V2_REQUIRED = (
    "asset",            # logical asset name
    "engine",           # e.g. "pixflux (REST v1)" / "mcp:create_image_pro"
    "params",           # complete replayable request params (no image payloads)
    "seed",
    "validator_version",
    "donor_derived",    # True when any init/style input derives from Omega
    "artifact_sha256",  # {role: sha256} — output + init/style/palette inputs
    "timestamp_utc",
    "usage",
)


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def attach_hashes(record: dict[str, Any], files: dict[str, str | Path]) -> dict[str, Any]:
    """Bind the record to its exact artifacts: {role: path} -> sha256 per role."""
    record.setdefault("artifact_sha256", {})
    for role, path in files.items():
        record["artifact_sha256"][role] = file_sha256(path)
    return record


def missing_v2_fields(record: dict[str, Any]) -> list[str]:
    """Names of required v2 fields absent from the record (empty = compliant)."""
    return [field for field in V2_REQUIRED if field not in record]


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
