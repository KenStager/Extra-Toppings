"""Split RNG streams.

The world must not flinch when the player changes their mind. Prices,
events, rumors, suppliers and the day's customer demand are drawn from
per-day derived generators — pure functions of (seed, day, channel) — so
the same seed produces the same city no matter what the player does.
Encounters, rivals, raids and staff use persistent per-domain streams:
player actions consume their own dice without shifting anyone else's.
"""

import random


class Streams:
    PERSISTENT = ("routes", "rivals", "raids", "staff")

    def __init__(self, seed: int | None) -> None:
        if seed is None:
            seed = random.randrange(2**32)
        self.seed = seed
        self.routes = random.Random(f"{seed}/routes")
        self.rivals = random.Random(f"{seed}/rivals")
        self.raids = random.Random(f"{seed}/raids")
        self.staff = random.Random(f"{seed}/staff")

    def daily(self, day: int, channel: str) -> random.Random:
        """A fresh generator for one (day, channel) — action-independent."""
        return random.Random(f"{self.seed}/{channel}/{day}")

    # ── save/load ────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "streams": {name: _rng_state_to_json(getattr(self, name))
                        for name in self.PERSISTENT},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Streams":
        s = cls(d["seed"])
        for name in cls.PERSISTENT:
            getattr(s, name).setstate(_rng_state_from_json(d["streams"][name]))
        return s


def _rng_state_to_json(rng: random.Random) -> list:
    version, internal, gauss = rng.getstate()
    return [version, list(internal), gauss]


def _rng_state_from_json(blob: list) -> tuple:
    version, internal, gauss = blob
    return (version, tuple(internal), gauss)
