"""The Harbor War: campaigns, corners, side-picking, and the board.

The branch's mechanics live here the way the Straight Path lives in
straight.py. The state model (WarCampaignState, the damage and
relation authorities, the heat policy) lives in models.py; this
module owns the §2.4.3 numbers and the war's behavior.

Every constant below is a placeholder in the §6.3 sense: structure is
the decision, numbers are tuning, and the §2.7 war rows move them
only on a recorded ruling.
"""

from . import data, models
from .models import State

# ── The four channels' numbers (rev. 2 item 5, verbatim) ──────────
CORNER_RATE = 0.15        # strength per unit sold in the target's turf
CORNER_CAP = 4.0          # per night; their corner customers are finite
OUTAGE_MULT = 2           # corners count double while their ovens are cold

# ── War posture (rev. 13 items 6-9; rev. 14 item 4) ───────────────
WAR_AGGRESSION = 1.5      # target act-chance multiplier while at war
WAR_VIOLENT = 1.5         # target violent-share multiplier while at war
WAR_RAID_EDGE = 2.0       # their raid's attack-roll bonus while at war
LAW_CALM_ACT = 0.5        # act-chance multiplier while their lawyers work
VIOLENCE_RISE = 1.5       # permanent, after the ledger goes to the law
OPPORTUNIST_MULT = 1.25   # bystander Vinnie, when you look weak
TIP_RUNG_MULT = 3.0       # bystander Sal's tip rung, while uninsured
TIP_RUNG_MAX = 0.60       # ...but tipping never swallows his whole ladder
RAID_RUNG_CAP = 0.95      # no rung may swallow the ladder (rev. 14 item 4)

# ── The paid-loyalty primitive's third face (rev. 13 item 7) ──────
WAR_PAY_PER_HEAD = 20     # per read-in name, per night at war
INSURANCE_RATE = 800      # Sal's invoice: seven nights of coverage
INSURANCE_NIGHTS = 7

# ── Capture (rev. 13 item 10; rev. 14 item 7) ─────────────────────
CAPTURE_UNDERGROUND = 0.5  # their coded customers call your board


# ── Campaign lookups (all derived — no duplicate state) ───────────

def campaigns(state: State) -> list:
    if state.branch != "war" or state.branch_state is None:
        return []
    return state.branch_state.campaigns


def campaign_for(state: State, rival_key: str):
    """The campaign naming this rival, live or broken; None outside
    the branch or for an undeclared rival."""
    for c in campaigns(state):
        if c.rival_key == rival_key:
            return c
    return None


def target_key(state: State) -> str | None:
    """The live campaign's rival — the one front (rev. 14 item 9)."""
    camp = models.live_campaign(state)
    return camp.rival_key if camp else None


def bystander_key(state: State) -> str | None:
    """The other rival, while a campaign is live and they still stand."""
    tk = target_key(state)
    if tk is None:
        return None
    for k, r in state.rivals.items():
        if k != tk and r.alive and campaign_for(state, k) is None:
            return k
    return None


def broken_keys(state: State) -> list:
    return [c.rival_key for c in campaigns(state)
            if c.broken_day is not None]


def district_captured(state: State, dk: str) -> bool:
    """A district whose owner fell to a campaign: their underground is
    yours (§6.4 — the underground only; never a second shop)."""
    owner = data.DISTRICTS[dk]["rival"]
    return owner is not None and owner in broken_keys(state)


def underground_bonus(state: State, dk: str) -> float:
    """The capture bonus to the district's underground factor — 0.0
    everywhere outside a captured district, so every flag-off consumer
    adds exactly zero (bit-identity preserved by construction)."""
    return CAPTURE_UNDERGROUND if district_captured(state, dk) else 0.0


def raid_edge(state: State, rival_key: str) -> float:
    """The attack-roll modifier for this rival's raid tonight — one
    computation, consumed by the policy view AND by incoming_raid, so
    execution and explanation cannot drift. 0.0 flag-off: every
    existing attack roll adds exactly zero."""
    return WAR_RAID_EDGE if target_key(state) == rival_key else 0.0


def insurance_paid(state: State) -> bool:
    bs = state.branch_state
    return (state.branch == "war" and bs is not None
            and bs.insurance_paid_until is not None
            and state.day <= bs.insurance_paid_until)


# ── The corner channel (rev. 2 item 5) ────────────────────────────

def corner_diversion(state: State, dk: str, owner: str, sold: int,
                     report: dict) -> float:
    """Units sold in the target's turf divert their income: strength
    −CORNER_RATE per unit, capped per night, doubled while their ovens
    are cold — the §2.4.3 outage window. One route runs per night, so
    the per-route cap IS the per-night cap. Books to the 'corners'
    channel through the one damage authority."""
    camp = models.live_campaign(state, owner)
    if camp is None or data.DISTRICTS[dk]["rival"] != owner or sold <= 0:
        return 0.0
    outage = state.rivals[owner].ovens_wrecked_days > 0
    mult = OUTAGE_MULT if outage else 1
    amount = min(CORNER_CAP * mult, sold * CORNER_RATE * mult)
    applied = models.apply_rival_damage(state, owner, "corners", amount)
    if applied > 0:
        window = (" — his ovens are cold and his customers keep your number"
                  if outage else "")
        report["lines"].append(
            f"His corner customers took your number tonight{window} "
            f"(strength −{applied:g}).")
    return applied
