"""P4b.5 — the instruments (design revisions 38 and 39).

Bots are instruments, never tuning targets, so what is pinned here is
that the INSTRUMENT measures what it claims to: every strategic choice
resolved by identity rather than menu position, each ablation actually
performing its ablation, and the analysis-side probe attributing money
to the authority that moved it.

The bars themselves are NOT pinned here. A falsification bar belongs
in the study's output and in FINDINGS, where a miss is a finding that
returns to review — a test asserting "the branch passes" would turn
the one honest signal in the battery into a thing that must be made
green.
"""

import random
import unittest

from analysis.experiments import DayMoney, ProfileProbe
from extra_toppings import data, models, partner, raids, routes
from extra_toppings.bot import (NeglectPartnerBot, NoCovertPartnerBot,
                                PartnerBot)
from extra_toppings.config import GameConfig
from extra_toppings.game import run
from extra_toppings.models import HOME_SHOP_KEY, new_state
from extra_toppings.sitdown import CHAIR_LABELS

PARTNER_ON = GameConfig(fork_enabled=True,
                        enabled_branches=frozenset({"partner"}))


def _entered(seed: int, cls=PartnerBot):
    """A real run down the chair, driven through `game.run`."""
    bot = cls(random.Random(seed))
    state = run(seed, bot, config=PARTNER_ON)
    return bot, state


def _a_seed_that_enters(cls=PartnerBot) -> int:
    for seed in range(40):
        _bot, state = _entered(seed, cls)
        if state.branch == "partner":
            return seed
    raise AssertionError("no seed under 40 entered the chair")


class TestEveryStrategicChoiceIsByIdentity(unittest.TestCase):
    """Design rev. 33 item 2, restated rev. 38 item 1. Menu position
    must never decide branch strategy — rev. 33 rejected the
    last-option-defaults proposal precisely because a later reorder
    would silently move this study.

    Each case REORDERS the menu and asserts the bot picks the same
    thing, which is the only assertion that can tell identity
    resolution from an index that happens to be right today."""

    def test_the_chair_is_found_wherever_it_sits(self):
        options = [CHAIR_LABELS[c] for c in models.BRANCH_ORDER] + \
            [CHAIR_LABELS["stand_pat"]]
        bot = PartnerBot(random.Random(1))
        first = bot.scene_menu("sitdown", "Your chair:", list(options))
        self.assertEqual(options[first], CHAIR_LABELS["partner"])

        shuffled = list(reversed(options))
        bot2 = PartnerBot(random.Random(1))
        second = bot2.scene_menu("sitdown", "Your chair:", shuffled)
        self.assertEqual(shuffled[second], CHAIR_LABELS["partner"])
        # …and the two picks are DIFFERENT indices, so the test would
        # notice an index that merely happens to be correct.
        self.assertNotEqual(first, second)

    def test_the_site_is_university_hill_wherever_it_sits(self):
        cards = ["Reconsider"] + [partner.site_label(d)
                                  for d in partner.SITE_DISTRICTS]
        want = partner.site_label("university")
        bot = PartnerBot(random.Random(1))
        pick = bot.scene_menu("sitdown", "Where does the second room go?",
                              list(cards))
        self.assertEqual(cards[pick], want)

        shuffled = ["Reconsider"] + list(
            reversed(cards[1:]))
        bot2 = PartnerBot(random.Random(1))
        pick2 = bot2.scene_menu(
            "sitdown", "Where does the second room go?", shuffled)
        self.assertEqual(shuffled[pick2], want)
        self.assertNotEqual(pick, pick2)

    def test_a_real_run_opens_on_university_hill(self):
        # The pin that matters: driven through the whole scene, not
        # inspected on a posed option list.
        seed = _a_seed_that_enters()
        _bot, state = _entered(seed)
        rooms = [s.district for s in state.shops if s.key != HOME_SHOP_KEY]
        self.assertEqual(rooms, ["university"])

    def test_an_unmatched_label_falls_through_rather_than_guessing(self):
        # `_by_identity` returns None rather than a neighbour, so a
        # label that stopped matching lands on the scene's safe last
        # option and shows up as a missing entry in the harness counts
        # — never as a silent pick of the wrong chair.
        self.assertIsNone(
            PartnerBot._by_identity(["a", "b"], "not here"))


class TestTheAblationsActuallyAblate(unittest.TestCase):
    """An ablation that does not ablate measures the complete bot
    against itself, which is how a 0-point drop gets reported as a
    result. Each is asserted on a real run."""

    def test_the_neglect_bot_neglects_BOTH_rooms(self):
        # "At either address" is the whole point of the row (§2.7
        # criterion 5): a neglect run that quietly kept the second
        # pantry stocked is the complete bot wearing the ablation's
        # name.
        seed = _a_seed_that_enters(NeglectPartnerBot)
        _bot, state = _entered(seed, NeglectPartnerBot)
        self.assertEqual(state.branch, "partner")
        self.assertGreater(len(state.shops), 1)
        second = [s for s in state.shops if s.key != HOME_SHOP_KEY][0]
        self.assertEqual(second.ingredients, 0)

    def test_the_complete_bot_is_the_positive_control(self):
        # Without this the test above passes for a bot that cannot
        # stock a pantry at all.
        seed = _a_seed_that_enters()
        _bot, state = _entered(seed)
        second = [s for s in state.shops if s.key != HOME_SHOP_KEY][0]
        self.assertGreater(second.ingredients, 0)

    def test_the_no_covert_bot_resolves_no_covert_sale_after_the_fork(self):
        seed = _a_seed_that_enters(NoCovertPartnerBot)
        bot = NoCovertPartnerBot(random.Random(seed))
        with ProfileProbe() as probe:
            state = run(seed, bot, config=PARTNER_ON)
        fork_day = state.sitdown_snapshot.payoff_day + 1
        after = sum(row.covert for day, row in probe.days.items()
                    if day >= fork_day)
        self.assertEqual(after, 0)

    def test_the_complete_bot_does_take_covert_revenue(self):
        # The positive control for the row above: the knob is what
        # silences the covert income, not the branch.
        seed = _a_seed_that_enters()
        bot = PartnerBot(random.Random(seed))
        with ProfileProbe() as probe:
            state = run(seed, bot, config=PARTNER_ON)
        fork_day = state.sitdown_snapshot.payoff_day + 1
        after = sum(row.covert for day, row in probe.days.items()
                    if day >= fork_day)
        self.assertGreater(after, 0)

    def test_neither_knob_touches_act_one(self):
        # Rev. 15's ruling, which invalidated a whole war study: an
        # ablation must enter the fork from a state-hash-identical
        # month. Asserted on the pre-chair night, through real runs.
        from extra_toppings import save
        seed = _a_seed_that_enters()
        hashes = {}
        for name, cls in (("complete", PartnerBot),
                          ("no-covert", NoCovertPartnerBot),
                          ("neglect", NeglectPartnerBot)):
            seen = {}

            def on_night(state, streams, seen=seen):
                seen[state.day - 1] = save.state_to_dict(state)
            bot = cls(random.Random(seed))
            state = run(seed, bot, config=PARTNER_ON, on_night=on_night)
            payoff = state.sitdown_snapshot.payoff_day
            hashes[name] = repr(seen[payoff])
        self.assertEqual(hashes["complete"], hashes["no-covert"])
        self.assertEqual(hashes["complete"], hashes["neglect"])


class TestActOneIsUntouchedByTheBotItself(unittest.TestCase):
    """Design rev. 39 item 4, implemented by rev. 40 item 2. Revision
    38's bot applied its one-ride-a-night rule from DAY 1, so
    replanning a one-address route changed Act I: 45 of 150 seeds
    reached the table from a different month, and seed 5's payoff
    moved from day 5 to day 6. That is rev. 15's defect class, in a
    bot whose own docstring cites rev. 15."""

    def test_the_one_ride_rule_is_silent_before_the_branch(self):
        bot = PartnerBot(random.Random(1))
        self.assertFalse(bot._in_branch)
        # Act I: the smart bot's answer, every time, however often the
        # route is replanned.
        for _ in range(4):
            self.assertTrue(bot.confirm("Ride along yourself?"))

    def test_it_binds_once_the_branch_is_open(self):
        bot = PartnerBot(random.Random(1))
        bot._in_branch = True
        self.assertTrue(bot.confirm("Ride along yourself?"))
        self.assertFalse(bot.confirm("Ride along yourself?"))

    def test_the_four_complete_fleets_share_a_pre_chair_month(self):
        # The bar the study prints, asserted on a slice of seeds so a
        # regression fails HERE rather than in a battery nobody reran.
        from extra_toppings import save
        from extra_toppings.bot import EscrowBot, StraightBot, WarBot
        fleets = (("straight", StraightBot), ("partner", PartnerBot),
                  ("war", WarBot), ("quiet_sale", EscrowBot))
        for seed in range(6):
            seen = set()
            for branch, cls in fleets:
                nights: dict = {}

                def on_night(state, streams, nights=nights):
                    nights[state.day - 1] = repr(save.state_to_dict(state))
                state = run(seed, cls(random.Random(seed)),
                            config=GameConfig(
                                fork_enabled=True,
                                enabled_branches=frozenset({branch})),
                            on_night=on_night)
                snap = state.sitdown_snapshot
                if snap is not None:
                    seen.add(nights[snap.payoff_day])
            self.assertLessEqual(len(seen), 1, f"seed {seed} diverged")


class TestTheProbeBooksMoneyToTheRightAuthority(unittest.TestCase):
    """Design rev. 39 item 6. The probe is the instrument that
    replaced transcript tallying, so the thing to pin is that it
    attributes to the authority that actually moved the money."""

    def test_it_restores_every_patch_even_when_the_run_raises(self):
        before = {name: getattr({"routes": routes, "raids": raids}[mod],
                                name)
                  for mod, name in (("routes", "resolve_route"),
                                    ("raids", "incoming_raid"))}
        with self.assertRaises(RuntimeError):
            with ProfileProbe():
                raise RuntimeError("boom")
        self.assertIs(routes.resolve_route, before["resolve_route"])
        self.assertIs(raids.incoming_raid, before["incoming_raid"])

    def test_stolen_cash_is_never_booked_as_tribute(self):
        # `incoming_raid` moves dirty money TWICE: the tribute the
        # player chooses to pay, and the cash the raiders grab. Only
        # the first is an obligation, and the probe tells them apart
        # by the TYPED outcome rather than by re-testing the engine's
        # own condition.
        probe = ProfileProbe()
        state = new_state()
        state.day = 7
        state.dirty = 5_000

        class Grabbed:
            outcome = "landed"
            damage_added = 2

        def fake(st, *a, **k):
            st.dirty -= 900          # raiders take it
            return Grabbed()
        wrapped = probe._wrap("incoming_raid", fake)
        wrapped(state)
        self.assertEqual(probe.days[7].tribute, 0)
        # A LANDED raid damaged the address, so it IS an incident.
        self.assertEqual(probe.days[7].raid_damage, 1)

    def test_an_averted_raid_books_its_tribute(self):
        # The positive control: the same authority, the same cash
        # movement, the outcome that means the player paid.
        probe = ProfileProbe()
        state = new_state()
        state.day = 7
        state.dirty = 5_000

        class Averted:
            outcome = "averted"
            damage_added = 0

        def fake(st, *a, **k):
            st.dirty -= 900
            return Averted()
        probe._wrap("incoming_raid", fake)(state)
        self.assertEqual(probe.days[7].tribute, 900)
        # …and an AVERTED raid damaged nothing, so it is not an
        # incident (rev. 40 item 4). Counting every call inflated the
        # component with the two outcomes where the address survived
        # untouched.
        self.assertEqual(probe.days[7].raid_damage, 0)

    def test_wages_exclude_EVERY_rent_the_authority_pays(self):
        # §2.7's staff component is wages, raises, settlements and war
        # pay. Rent is not staff spend, and `_payroll_and_rent` pays
        # BOTH kinds: `RENT_PER_DAY` per rent-charged address and the
        # warehouse. Subtracting only the warehouse booked every
        # restaurant rent as wages (rev. 40 item 4).
        probe = ProfileProbe()
        state = new_state()
        state.day = 9
        state.clean = 10_000
        state.warehouse = {"mushrooms": 1}
        rent = data.RENT_PER_DAY * len(
            models.addresses_allowing(state, "rent"))

        def fake(st, *a, **k):
            st.clean -= 500 + rent + data.WAREHOUSE_RENT
            return False
        probe._wrap("_payroll_and_rent", fake)(state)
        self.assertEqual(probe.days[9].wages, 500)

    def test_a_second_address_carries_a_second_rent(self):
        # THE case the correction exists for: Partner pays two
        # restaurant rents, and the first spelling booked the second
        # one as wages every single night.
        from extra_toppings.models import Shop
        probe = ProfileProbe()
        state = new_state()
        state.day = 16
        state.clean = 10_000
        state.shops.append(Shop(key="shop2", district="university",
                                acceptance_day=14, opening_day=16))
        charged = len(models.addresses_allowing(state, "rent"))
        self.assertEqual(charged, 2)

        def fake(st, *a, **k):
            st.clean -= 500 + data.RENT_PER_DAY * charged
            return False
        probe._wrap("_payroll_and_rent", fake)(state)
        self.assertEqual(probe.days[16].wages, 500)

    def test_a_day_row_starts_at_zero_on_every_field(self):
        row = DayMoney()
        self.assertEqual(
            [row.covert, row.wages, row.settlements, row.counsel,
             row.tribute, row.raid_damage],
            [0, 0, 0, 0, 0, 0])
        # The per-address rows start empty and are NOT shared between
        # instances — a mutable default would have every day of every
        # run booking into one dict.
        self.assertEqual((row.pantry_spend, row.cover_stops), ({}, {}))
        row.pantry_spend["shop1"] = 5
        self.assertEqual(DayMoney().pantry_spend, {})


if __name__ == "__main__":
    unittest.main()
