"""Minimal PixelLab REST client (stdlib HTTP; token never stored here).

The token is resolved in order: the PIXELLAB_API_KEY environment
variable, the file named by PIXELLAB_API_KEY_FILE, then the macOS
Keychain item with service name `pixellab-api` (store it with
`security add-generic-password -a "$USER" -s pixellab-api -w`). It is
held only in memory, sent only as the Authorization header, and
stripped from any error text.
"""

from __future__ import annotations

import base64
import io
import json
import os
import time
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

from PIL import Image

API_ROOT = "https://api.pixellab.ai/v1"


class PixelLabError(RuntimeError):
    pass


def _token() -> str:
    token = os.environ.get("PIXELLAB_API_KEY", "").strip()
    if not token:
        key_file = os.environ.get("PIXELLAB_API_KEY_FILE", "").strip()
        if key_file and os.path.exists(key_file):
            with open(key_file) as fh:
                token = fh.read().strip()
    if not token and sys.platform == "darwin":
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "pixellab-api", "-w"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
    if not token:
        raise PixelLabError(
            "no credential: set PIXELLAB_API_KEY, PIXELLAB_API_KEY_FILE, "
            "or a macOS Keychain item with service name 'pixellab-api'"
        )
    return token


def _redact(text: str, token: str) -> str:
    return text.replace(token, "[REDACTED]") if token else text


def _ledger_write(path: str, entry: dict[str, Any]) -> None:
    with open(path, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def _request(
    path: str,
    payload: dict[str, Any] | None,
    timeout: int = 180,
    attempts: int = 3,
) -> dict[str, Any]:
    """POST/GET with retry on transient failures (network errors and 5xx).

    4xx errors never retry — they are caller mistakes and usually uncharged.
    Every successful call that reports `usage` is appended to the local
    spend ledger named by PIXELLAB_SPEND_LEDGER (if set), so our own spend
    record cannot silently diverge from the vendor's on a lost response.
    """
    token = _token()
    data = json.dumps(payload).encode() if payload is not None else None
    last_error = ""
    for attempt in range(attempts):
        req = urllib.request.Request(
            API_ROOT + path,
            data=data,
            method="POST" if payload is not None else "GET",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result: dict[str, Any] = json.loads(resp.read().decode())
        except urllib.error.HTTPError as err:
            body = err.read().decode(errors="replace")[:500]
            last_error = _redact(f"HTTP {err.code} from {path}: {body}", token)
            if err.code < 500:
                raise PixelLabError(last_error) from None
        except urllib.error.URLError as err:
            last_error = _redact(f"network error on {path}: {err.reason}", token)
        else:
            ledger = os.environ.get("PIXELLAB_SPEND_LEDGER", "").strip()
            if ledger and isinstance(result.get("usage"), dict):
                _ledger_write(ledger, {
                    "path": path,
                    "usage": result["usage"],
                    "seed": (payload or {}).get("seed"),
                    "size": (payload or {}).get("image_size"),
                    "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
            return result
        if attempt < attempts - 1:
            time.sleep(2 * (attempt + 1))
    raise PixelLabError(f"{last_error} (after {attempts} attempts)")


def image_to_b64(image: Image.Image) -> dict[str, str]:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return {"type": "base64", "base64": base64.b64encode(buf.getvalue()).decode()}


def b64_to_image(payload: dict[str, str]) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(payload["base64"]))).convert("RGBA")


def get_balance() -> dict[str, Any]:
    return _request("/balance", None)


def generate_pixflux(params: dict[str, Any]) -> tuple[Image.Image, dict[str, Any]]:
    """Run one pixflux generation; returns (image, usage/meta without image).

    Pixflux is the DEFAULT engine (see art_specs/decision_32px_world.md,
    engine scorecard): general-purpose, 400px/axis, wins most cells.
    """
    response = _request("/generate-image-pixflux", params)
    image = b64_to_image(response.pop("image"))
    return image, response


def generate_bitforge(params: dict[str, Any]) -> tuple[Image.Image, dict[str, Any]]:
    """Run one bitforge generation; returns (image, usage/meta without image).

    Niche engine: same-object style variants and canon-adjacent props
    only — its style_image leaks content across object types and it caps
    at 200px/axis.
    """
    response = _request("/generate-image-bitforge", params)
    image = b64_to_image(response.pop("image"))
    return image, response
