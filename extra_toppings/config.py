"""Engine configuration: immutable, explicit, never persisted.

The fork flag gates ENTRY into the sit-down — the lock-up snapshot is
captured only while it is on. It never gates continuation: a save
carrying a pending snapshot or act == 2 is authoritative and resumes
correctly whatever the launch configuration says, so no save silently
becomes unplayable after a flag rollback (design §8 rev. 5).

Engine code never reads the environment; the CLI translates it into a
GameConfig and passes that down.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameConfig:
    fork_enabled: bool = False
    # Branch keys the sit-down scene will actually let the player enter.
    # Chairs outside this set still render with their true gate verdicts
    # (a development-build marker, outside the fiction, explains why they
    # cannot be taken) — an implementation limitation must never be
    # converted into a permanent player decision.
    enabled_branches: frozenset = frozenset()
