"""Rev. 19 item 4: the active-baseline contract is independent, not
self-asserted — every field of the golden's provenance is mutated in
turn and the gate must reject each one, plus a wholesale byte flip."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

from analysis import equivalence as eq


def _mutated(**changes):
    with open(eq.GOLDEN_PATH) as f:
        payload = json.load(f)
    payload["meta"].update(changes)
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, sort_keys=True)
    return path


class TestBaselineContract(unittest.TestCase):
    def test_the_sanctioned_baseline_passes(self):
        self.assertEqual(eq.validate_baseline(), [])

    def test_every_field_mutation_is_rejected(self):
        for changes in ({"version": -9},
                        {"generated_at_commit": "banana"},
                        {"predecessor_sha256": "garbage"},
                        {"reason": "x"},
                        {"seeds": 1},
                        {"bots": ["greedy"]}):
            path = _mutated(**changes)
            try:
                errors = eq.validate_baseline(path)
                self.assertTrue(errors, f"{changes} was accepted")
            finally:
                os.unlink(path)

    def test_a_byte_flip_is_rejected(self):
        with open(eq.GOLDEN_PATH, "rb") as f:
            raw = bytearray(f.read())
        raw[len(raw) // 2] ^= 0x01
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "wb") as f:
            f.write(bytes(raw))
        try:
            self.assertTrue(eq.validate_baseline(path))
        finally:
            os.unlink(path)

    def test_a_missing_field_is_rejected(self):
        with open(eq.GOLDEN_PATH) as f:
            payload = json.load(f)
        del payload["meta"]["reason"]
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, sort_keys=True)
        try:
            self.assertTrue(eq.validate_baseline(path))
        finally:
            os.unlink(path)


class TestRegenerationMustNameItself(unittest.TestCase):
    """A sanctioned act names itself. `generate` used to default the
    reason and silently stamp the PREVIOUS act's text onto whatever
    came next — the exact provenance failure the contract exists to
    prevent. It is refused now, before the golden is even opened."""

    def setUp(self):
        # This suite asserts that a refused regeneration writes
        # nothing — so when the contract is BROKEN (a pin-proof run
        # against the pre-fix engine, say) the command under test
        # really does overwrite the live baseline. The bytes are held
        # here and restored unconditionally: a test that guards an
        # artifact must never be the thing that destroys it.
        with open(eq.GOLDEN_PATH, "rb") as f:
            self._original = f.read()
        self.addCleanup(self._restore)

    def _restore(self):
        with open(eq.GOLDEN_PATH, "rb") as f:
            if f.read() == self._original:
                return
        with open(eq.GOLDEN_PATH, "wb") as f:
            f.write(self._original)

    def _golden_sha(self):
        with open(eq.GOLDEN_PATH, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def _generate_cli(self, *extra):
        return subprocess.run(
            [sys.executable, "-m", "analysis.equivalence",
             "generate", "--seeds", "2", *extra],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True)

    def test_the_api_refuses_a_missing_reason(self):
        before = self._golden_sha()
        for empty in (None, "", "   ", "\n"):
            with self.assertRaises(ValueError, msg=repr(empty)):
                eq.generate(2, empty)
        self.assertEqual(self._golden_sha(), before,
                         "a refused regeneration must not touch the file")

    def test_the_cli_refuses_before_touching_the_golden(self):
        before = self._golden_sha()
        proc = self._generate_cli()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--reason", proc.stderr)
        self.assertEqual(self._golden_sha(), before,
                         "the CLI must fail before writing anything")

    def test_a_blank_reason_through_the_cli_is_refused_too(self):
        before = self._golden_sha()
        proc = self._generate_cli("--reason", "   ")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self._golden_sha(), before)

    def test_no_historical_reason_survives_as_a_default(self):
        # The retired fallback must not be reachable from anywhere.
        with open(eq.__file__) as f:
            source = f.read()
        self.assertNotIn("RouteManifest inventory contract replaced",
                         source)


if __name__ == "__main__":
    unittest.main()
