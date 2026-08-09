"""Rev. 19 item 4: the active-baseline contract is independent, not
self-asserted — every field of the golden's provenance is mutated in
turn and the gate must reject each one, plus a wholesale byte flip."""

import json
import os
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


if __name__ == "__main__":
    unittest.main()
