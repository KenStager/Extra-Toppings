import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from tools.art_pipeline import pixellab_client as client
from tools.art_pipeline.provenance import (
    attach_hashes,
    file_sha256,
    missing_v2_fields,
    scrub,
)


def _response(payload: dict) -> mock.MagicMock:
    resp = mock.MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__ = lambda self: self
    resp.__exit__ = lambda self, *a: None
    return resp


class RequestRetry(unittest.TestCase):
    def setUp(self) -> None:
        self.env = mock.patch.dict(
            "os.environ", {"PIXELLAB_API_KEY": "test-token"}, clear=False
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_transient_network_error_retries_then_succeeds(self) -> None:
        calls = [urllib.error.URLError("boom"), _response({"ok": True})]

        def fake_urlopen(req, timeout=0):
            item = calls.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen), \
                mock.patch.object(client.time, "sleep"):
            self.assertEqual(client._request("/balance", None), {"ok": True})
        self.assertEqual(calls, [])

    def test_client_error_never_retries(self) -> None:
        attempts = []

        def fake_urlopen(req, timeout=0):
            attempts.append(1)
            raise urllib.error.HTTPError(
                "url", 422, "bad", {}, io.BytesIO(b'{"detail": "nope"}')
            )

        with mock.patch.object(client.urllib.request, "urlopen", fake_urlopen):
            with self.assertRaises(client.PixelLabError):
                client._request("/generate-image-pixflux", {"seed": 1})
        self.assertEqual(len(attempts), 1)

    def test_spend_ledger_appends_on_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = str(Path(tmp) / "ledger.jsonl")
            with mock.patch.dict("os.environ", {"PIXELLAB_SPEND_LEDGER": ledger}), \
                    mock.patch.object(
                        client.urllib.request, "urlopen",
                        lambda req, timeout=0: _response(
                            {"usage": {"type": "generations", "generations": 1.0}}
                        ),
                    ):
                client._request("/generate-image-pixflux", {"seed": 7})
            lines = Path(ledger).read_text().splitlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry["seed"], 7)
            self.assertEqual(entry["usage"]["generations"], 1.0)


class ProvenanceV2(unittest.TestCase):
    def test_file_sha256_and_attach(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.bin"
            f.write_bytes(b"pizza")
            record = attach_hashes({"asset": "x"}, {"output": f})
            self.assertEqual(record["artifact_sha256"]["output"], file_sha256(f))
            self.assertEqual(len(record["artifact_sha256"]["output"]), 64)

    def test_missing_v2_fields_reports_gaps(self) -> None:
        self.assertIn("engine", missing_v2_fields({"asset": "x"}))
        complete = {k: "v" for k in (
            "asset", "engine", "params", "seed", "validator_version",
            "donor_derived", "artifact_sha256", "timestamp_utc", "usage",
        )}
        self.assertEqual(missing_v2_fields(complete), [])

    def test_scrub_still_strips_credential_keys(self) -> None:
        clean = scrub({"asset": "x", "api_key": "no", "nested": {"bearer_token": "no"}})
        self.assertEqual(clean, {"asset": "x", "nested": {}})


if __name__ == "__main__":
    unittest.main()
