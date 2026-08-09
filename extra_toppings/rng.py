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
    # sitdown/brokers/war/straight are reserved for the Act II fork (the
    # sit-down scene, the escrow buyer, the harbor war, the Straight
    # Path's meeting dice — rev. 9 item 1). They exist so the save
    # schema is final, and each stays undrawn until its branch actually
    # draws it — the equivalence harness asserts exactly that.
    PERSISTENT = ("routes", "rivals", "raids", "staff",
                  "sitdown", "brokers", "war", "straight")

    def __init__(self, seed: int | None) -> None:
        if seed is None:
            seed = random.randrange(2**32)
        self.seed = seed
        self.routes = random.Random(f"{seed}/routes")
        self.rivals = random.Random(f"{seed}/rivals")
        self.raids = random.Random(f"{seed}/raids")
        self.staff = random.Random(f"{seed}/staff")
        self.sitdown = random.Random(f"{seed}/sitdown")
        self.brokers = random.Random(f"{seed}/brokers")
        self.war = random.Random(f"{seed}/war")
        self.straight = random.Random(f"{seed}/straight")

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
        """A stream missing from the payload (a pre-fork save) keeps its
        fresh seed-derived state — that IS the migration for streams."""
        s = cls(d["seed"])
        for name in cls.PERSISTENT:
            if name in d["streams"]:
                getattr(s, name).setstate(
                    _rng_state_from_json(d["streams"][name]))
        return s


def _rng_state_to_json(rng: random.Random) -> list:
    version, internal, gauss = rng.getstate()
    return [version, list(internal), gauss]


def _rng_state_from_json(blob: list) -> tuple:
    version, internal, gauss = blob
    return (version, tuple(internal), gauss)
