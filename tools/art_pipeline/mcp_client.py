"""Minimal MCP (JSON-RPC over streamable HTTP) client for PixelLab.

Reaches the MCP-only surface (Pro model, object registry, tileset
tools) directly from the pipeline, reusing the same credential
resolution as the REST client — no Claude Code MCP attachment, no
credential in any config file. Stdlib only.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from tools.art_pipeline.pixellab_client import PixelLabError, _redact, _token

MCP_URL = "https://api.pixellab.ai/mcp"
PROTOCOL_VERSION = "2025-03-26"


class McpSession:
    """One initialized MCP session; use as a context manager or call close()."""

    def __init__(self, timeout: int = 300) -> None:
        self._timeout = timeout
        self._session_id: str | None = None
        self._next_id = 0
        init = self._rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "extra-toppings-art-pipeline", "version": "1.0"},
        })
        self.server_info = init.get("serverInfo", {})
        self._notify("notifications/initialized")

    # ------------------------------------------------------------ transport
    def _post(self, payload: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, str]]:
        token = _token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        req = urllib.request.Request(
            MCP_URL, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                resp_headers = {k.lower(): v for k, v in resp.headers.items()}
                body = resp.read().decode()
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")[:400]
            raise PixelLabError(
                _redact(f"MCP HTTP {err.code}: {detail}", token)
            ) from None
        except urllib.error.URLError as err:
            raise PixelLabError(
                _redact(f"MCP network error: {err.reason}", token)
            ) from None
        content_type = resp_headers.get("content-type", "")
        if not body:
            return None, resp_headers
        if "text/event-stream" in content_type:
            message = None
            for line in body.splitlines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data and data != "[DONE]":
                        message = json.loads(data)
            return message, resp_headers
        return json.loads(body), resp_headers

    def _rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._next_id += 1
        message, headers = self._post({
            "jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params,
        })
        if sid := headers.get("mcp-session-id"):
            self._session_id = sid
        if message is None:
            raise PixelLabError(f"MCP: empty response to {method}")
        if "error" in message:
            raise PixelLabError(f"MCP error on {method}: {message['error']}")
        return message.get("result", {})

    def _notify(self, method: str) -> None:
        self._post({"jsonrpc": "2.0", "method": method})

    # ------------------------------------------------------------ public API
    def list_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"cursor": cursor} if cursor else {}
            result = self._rpc("tools/list", params)
            tools.extend(result.get("tools", []))
            cursor = result.get("nextCursor")
            if not cursor:
                return tools

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            texts = [c.get("text", "") for c in result.get("content", [])
                     if c.get("type") == "text"]
            raise PixelLabError(f"MCP tool {name} errored: {' '.join(texts)[:400]}")
        return result

    def close(self) -> None:
        if self._session_id:
            try:
                req = urllib.request.Request(
                    MCP_URL, method="DELETE",
                    headers={"Authorization": f"Bearer {_token()}",
                             "Mcp-Session-Id": self._session_id},
                )
                urllib.request.urlopen(req, timeout=30).close()
            except (urllib.error.URLError, OSError):
                pass  # session cleanup is best-effort
        self._session_id = None

    def __enter__(self) -> McpSession:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
