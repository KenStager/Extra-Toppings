"""Minimal PixelLab REST client (stdlib HTTP; token via environment only).

The token is read from PIXELLAB_API_KEY, or from the file named by
PIXELLAB_API_KEY_FILE. It is held only in memory, sent only as the
Authorization header, and stripped from any error text.
"""

from __future__ import annotations

import base64
import io
import json
import os
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
    if not token:
        raise PixelLabError(
            "no credential: set PIXELLAB_API_KEY or PIXELLAB_API_KEY_FILE"
        )
    return token


def _redact(text: str, token: str) -> str:
    return text.replace(token, "[REDACTED]") if token else text


def _request(path: str, payload: dict[str, Any] | None, timeout: int = 180) -> dict[str, Any]:
    token = _token()
    data = json.dumps(payload).encode() if payload is not None else None
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
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")[:500]
        raise PixelLabError(
            _redact(f"HTTP {err.code} from {path}: {body}", token)
        ) from None
    except urllib.error.URLError as err:
        raise PixelLabError(
            _redact(f"network error on {path}: {err.reason}", token)
        ) from None


def image_to_b64(image: Image.Image) -> dict[str, str]:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return {"type": "base64", "base64": base64.b64encode(buf.getvalue()).decode()}


def b64_to_image(payload: dict[str, str]) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(payload["base64"]))).convert("RGBA")


def get_balance() -> dict[str, Any]:
    return _request("/balance", None)


def generate_bitforge(params: dict[str, Any]) -> tuple[Image.Image, dict[str, Any]]:
    """Run one bitforge generation; returns (image, usage/meta without image)."""
    response = _request("/generate-image-bitforge", params)
    image = b64_to_image(response.pop("image"))
    return image, response
