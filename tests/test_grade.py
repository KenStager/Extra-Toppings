"""P4b.4 — the grade and the endings (design revisions 35 and 36).

Two contracts, and they are not the same contract:

  * THE REGISTRY — every terminal id is named, every id belongs to
    the chairs that can reach it, and the epilogue refuses BEFORE it
    prints a header. Failing closed on an unknown id was necessary
    and not sufficient: `partner` + `straight_exit` renders the
    Straight Path's earned exit for a run that never went straight,
    with every id in the table.
  * THE GRADE — one derived view behind the card, the grade, the
    epilogue header and the tier arm, so the card cannot promise
    `healthy` while the epilogue delivers `hollow`.

The terminal discriminator is ARREARS and the tier is a separate
question (§2.5, rev. 22 item 7), so the two are asserted apart
everywhere below.
"""

import unittest
from unittest import mock

from extra_toppings import (data, game, models, partner, phases, save,
                            sitdown)
from extra_toppings.config import GameConfig
from extra_toppings.models import (HOME_SHOP_KEY, PointsCycleRecord,
                                   SitdownSnapshot, new_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

PARTNER_ON = GameConfig(fork_enabled=True,
                        enabled_branches=frozenset({"partner"}))
POINTS = models.POINTS_PER_CYCLE
VIG = models.POINTS_VIG


class Listening(ScriptedConsole):
    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def header(self, text: str) -> None:
        self.lines.append(f"== {text}")

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)

    def ending(self) -> str:
        return next((ln for ln in self.lines if "ENDING:" in ln), "")


def _run_night(state, con=None):
    con = con or Listening()
    phases.night(state, {"routes": {}},
                 {"wagons": phases.WagonNight(state)}, con,
                 Streams(3), PARTNER_ON)
    return con


def seated(day: int = 31, payoff_day: int = 13, *, clean: int = 400_000,
           starve_from: int | None = None):
    """A real Partner run: the chair taken through the actual
    sit-down scene, then wound forward through REAL NIGHTS so the
    points ledger is the one production writes rather than a
    hand-built history that happens to validate.

    `starve_from` empties the till before that day's night, which is
    how a genuine arrears state is produced — by missing a bill, not
    by appending a record that says one was missed."""
    state = new_state()
    state.debt = 0
    state.debt_paid_day = payoff_day
    state.day = payoff_day + 1
    state.add_case(20.0, "prior seizures", kind="physical")
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=payoff_day, case_at_lockup=20.0,
        evidence_count_at_lockup=len(state.evidence))
    con = Listening([1, 1 + partner.SITE_DISTRICTS.index("university"), 1])
    sitdown.run_scene(state, con, PARTNER_ON)
    state.clean, state.dirty = clean, 0
    while state.day < day:
        if starve_from is not None and state.day >= starve_from:
            state.clean, state.dirty = 0, 0
        _run_night(state)
    return state


def hooked(day: int = 31):
    """A run that missed its LAST bill: one strike, arrears standing,
    and no second strike — so it reaches day 30 On the Hook rather
    than foreclosed."""
    return seated(day=day, starve_from=29)


def room(state):
    return partner.the_restaurant(state)


def set_terms(state, *, net: int, reputation: float):
    """Put the two terms exactly where a case wants them, through the
    fields the view actually reads."""
    state.dirty = 0
    for s in state.shops:
        s.stash = {}
    state.warehouse, state.warehouse_cash = None, 0
    state.clean = net + models.partner_ledger(state.branch_state).arrears
    room(state).reputation = reputation
    return state


# ══ the registry ══════════════════════════════════════════════════

class TestTheTerminalRegistry(unittest.TestCase):
    def test_every_registered_id_has_an_epilogue_arm(self):
        # The coverage check rev. 36 item 3 asks for: an id added to
        # the registry without a text fails HERE, not in a player's
        # epilogue. Each id is rendered on a chair that owns it.
        for ending, owners in models.TERMINAL_OWNERS.items():
            with self.subTest(ending=ending):
                state = _rendering_state(ending, sorted(
                    o for o in owners if o is not None)[0]
                    if any(o is not None for o in owners) else None)
                con = Listening()
                game.epilogue(state, con)
                self.assertIn("ENDING:", "".join(con.lines), ending)

    def test_a_registered_id_with_no_arm_fails_in_the_suite(self):
        # The coverage contract rev. 36 item 3 asks for, asserted
        # where it bites: an id ADDED to the registry without a text
        # must fail here rather than borrow somebody else's arm. The
        # test above proves today's ids render; this proves tomorrow's
        # cannot slip through.
        state = seated()
        state.game_over = "a_quiet_retirement"
        owners = dict(models.TERMINAL_OWNERS)
        owners["a_quiet_retirement"] = frozenset({"partner"})
        with mock.patch.object(models, "TERMINAL_OWNERS", owners):
            with self.assertRaises(ValueError) as caught:
                game.epilogue(state, Listening())
        self.assertIn("no epilogue arm renders", str(caught.exception))

    def test_an_unregistered_id_is_refused(self):
        state = seated()
        state.game_over = "a_quiet_retirement"
        with self.assertRaises(ValueError) as caught:
            models.validate_terminal(state)
        self.assertIn("unknown terminal", str(caught.exception))

    def test_a_known_id_on_the_wrong_chair_is_refused(self):
        # THE case that proves unknown-id checking was not enough.
        state = seated()
        state.game_over = "straight_exit"
        with self.assertRaises(ValueError) as caught:
            game.epilogue(state, Listening())
        self.assertIn("cannot reach it", str(caught.exception))

    def test_the_refusal_emits_no_partial_ending(self):
        # Half an epilogue reads as a real one, so the check runs
        # before the header.
        state = seated()
        state.game_over = "syndicate"
        con = Listening()
        with self.assertRaises(ValueError):
            game.epilogue(state, con)
        self.assertEqual(con.lines, [])

    def test_the_registry_binds_at_the_save_boundary_too(self):
        state = seated()
        state.game_over = "harbor_yours"
        with self.assertRaises(ValueError):
            save.state_from_dict(save.state_to_dict(state))

    def test_a_live_run_carries_no_terminal_and_is_fine(self):
        state = seated()
        self.assertIsNone(state.game_over)
        models.validate_terminal(state)

    def test_the_latch_and_insolvency_reach_every_chair(self):
        for ending in ("arrested", "broke"):
            for chair in (None, models.STAND_PAT) + models.BRANCH_ORDER:
                with self.subTest(ending=ending, chair=chair):
                    self.assertIn(chair, models.TERMINAL_OWNERS[ending])


def _rendering_state(ending: str, chair):
    """A state that can legitimately render `ending`, built through
    real constructors rather than posed where a real path exists."""
    if chair == "partner":
        state = seated()
        if ending == models.ON_THE_HOOK_ENDING:
            state.branch_state.points_cycles = [
                PointsCycleRecord(due_day=19, bill=POINTS, vig=0,
                                  paid=False)]
            state.branch_state.points_due_day = 24
        state.game_over = ending
        return state
    state = new_state()
    state.day = data.DEBT_DUE_DAY + 1
    state.debt = 0
    state.debt_paid_day = 13
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=13, case_at_lockup=0.0, evidence_count_at_lockup=0)
    if chair is not None:
        state.branch = chair
        state.branch_state = {
            "straight": models.BranchState.straight,
            "war": lambda: models.BranchState.war(
                war_target="sal", declared_day=14,
                starting_strength=60.0),
            "quiet_sale": models.BranchState.quiet_sale,
            models.STAND_PAT: lambda: None,
        }[chair]() if chair != models.STAND_PAT else None
    if ending == "arrested":
        state.day = 20
        state.add_case(100.0, "the file closes", kind="physical")
    if ending in ("harbor_yours", "syndicate"):
        # These render FROM the campaign ledger, so the capture has to
        # be RECORDED — a rival at strength 0 with no `broken_day` is
        # not a captured campaign, and the epilogue would print
        # nothing. Driven through the real damage authority.
        models.apply_rival_damage(state, "sal", "jobs", 999.0)
        if ending == "syndicate":
            state.branch_state.campaigns.append(models.WarCampaignState(
                rival_key="vinnie", declared_day=15,
                starting_hundredths=7000))
            models.apply_rival_damage(state, "vinnie", "jobs", 999.0)
    state.game_over = ending
    return state


# ══ the grading view ══════════════════════════════════════════════

class TestTheGradeIsOneDerivation(unittest.TestCase):
    def test_the_net_term_is_strictly_greater(self):
        # rev. 36 item 1: $8,000 FAILS, $8,001 passes. Revision 24's
        # inclusive draft was superseded by revision 25 item 2 before
        # anything was built on it.
        state = seated()
        set_terms(state, net=models.OPERATION_NET_THRESHOLD,
                  reputation=10.0)
        self.assertFalse(partner.grade_view(state).net_met)
        set_terms(state, net=models.OPERATION_NET_THRESHOLD + 1,
                  reputation=10.0)
        self.assertTrue(partner.grade_view(state).net_met)

    def test_the_released_grade_compares_the_same_way(self):
        # The other consumer of the one home, at the same boundary.
        for net, expected in ((models.OPERATION_NET_THRESHOLD, False),
                              (models.OPERATION_NET_THRESHOLD + 1, True)):
            with self.subTest(net=net):
                state = new_state()
                state.day = data.DEBT_DUE_DAY + 1
                state.debt = 0
                state.clean, state.dirty = net, 0
                for s in state.shops:
                    s.stash = {}
                state.add_case(40.0, "enough to miss the clean exit",
                               kind="physical")
                state.game_over = "survived"
                con = Listening()
                game.epilogue(state, con)
                self.assertEqual("The operation holds" in con.ending(),
                                 expected)

    def test_the_reputation_term_is_inclusive(self):
        state = seated()
        set_terms(state, net=0,
                  reputation=models.PARTNER_REPUTATION_THRESHOLD)
        self.assertTrue(partner.grade_view(state).reputation_met)
        set_terms(state, net=0,
                  reputation=models.PARTNER_REPUTATION_THRESHOLD - 0.5)
        self.assertFalse(partner.grade_view(state).reputation_met)

    def test_the_gate_is_and_not_a_trade(self):
        # Money must not compensate for a dead restaurant.
        cases = [
            (500_000, 10.0, "working"),      # money, no room
            (0, 90.0, "working"),            # room, no money
            (500_000, 90.0, "healthy"),
            (0, 10.0, "hollow"),
        ]
        for net, rep, tier in cases:
            with self.subTest(net=net, rep=rep):
                state = seated()
                set_terms(state, net=net, reputation=rep)
                self.assertEqual(partner.grade_view(state).tier, tier)

    def test_the_net_term_subtracts_arrears(self):
        state = hooked()
        set_terms(state, net=20_000, reputation=90.0)
        view = partner.grade_view(state)
        self.assertGreater(view.arrears, 0)
        self.assertEqual(view.net, 20_000)
        # Gross net is HIGHER by exactly the arrears: the two numbers
        # genuinely differ, which is what makes item 4's pin real.
        self.assertEqual(state.net_worth(), view.net + view.arrears)

    def test_the_terminal_is_arrears_and_the_tier_is_separate(self):
        # §2.5 / rev. 22 item 7: a paid catch-up bill leaves a strike
        # and earns The Operation anyway.
        state = seated()
        state.branch_state.points_cycles = [
            PointsCycleRecord(due_day=19, bill=POINTS, vig=0, paid=False),
            PointsCycleRecord(due_day=24, bill=POINTS * 2 + VIG, vig=VIG,
                              paid=True, paid_day=24)]
        state.branch_state.points_due_day = 29
        set_terms(state, net=0, reputation=0.0)
        view = partner.grade_view(state)
        self.assertEqual(models.partner_ledger(state.branch_state).strikes, 1)
        self.assertEqual(view.arrears, 0)
        self.assertEqual(view.ending, models.OPERATION_ENDING)
        self.assertEqual(view.tier, "hollow")       # earned, and hollow

    def test_grade_returns_the_view_s_id(self):
        state = seated()
        set_terms(state, net=99_999, reputation=99.0)
        self.assertEqual(partner.grade(state),
                         partner.grade_view(state).ending)

    def test_the_restaurant_is_the_non_founding_room_by_identity(self):
        state = seated()
        self.assertNotEqual(room(state).key, HOME_SHOP_KEY)
        chosen = room(state).key
        state.shops.reverse()
        self.assertEqual(room(state).key, chosen)

    def test_more_than_one_second_room_refuses_rather_than_choosing(self):
        state = seated()
        state.shops.append(models.Shop(key="shop3", district="meadows",
                                       acceptance_day=14, opening_day=16))
        with self.assertRaises(ValueError) as caught:
            partner.grade_view(state)
        self.assertIn("a ruling, not an inference", str(caught.exception))


# ══ the day-30 pair, and when it may exist ═══════════════════════

class TestTheDayThirtyPair(unittest.TestCase):
    def test_the_operation_owes_nothing(self):
        square = seated()
        square.game_over = models.OPERATION_ENDING
        save.state_from_dict(save.state_to_dict(square))     # baseline
        # The SAME grade claimed by a run that genuinely missed its
        # last bill — a real arrears state, not an appended record.
        owing = hooked()
        owing.game_over = models.OPERATION_ENDING
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(owing))
        self.assertIn("square with him", str(caught.exception))

    def test_the_hook_needs_a_debt(self):
        owing = hooked()
        owing.game_over = models.ON_THE_HOOK_ENDING
        save.state_from_dict(save.state_to_dict(owing))       # baseline
        state = seated()                                      # owes nothing
        state.game_over = models.ON_THE_HOOK_ENDING
        with self.assertRaises(ValueError) as caught:
            save.state_from_dict(save.state_to_dict(state))
        self.assertIn("no hook without arrears", str(caught.exception))

    def test_neither_may_be_recorded_before_day_thirty_completes(self):
        for ending in (models.OPERATION_ENDING, models.ON_THE_HOOK_ENDING):
            with self.subTest(ending=ending):
                state = (hooked(day=data.DEBT_DUE_DAY)
                         if ending == models.ON_THE_HOOK_ENDING
                         else seated(day=data.DEBT_DUE_DAY))
                state.game_over = ending
                with self.assertRaises(ValueError) as caught:
                    models.validate_terminal(state)
                self.assertIn("played out", str(caught.exception))

    def test_mid_month_arrears_demand_no_terminal_at_all(self):
        # Owing Carmine on day 20 is an ordinary state; a validator
        # that required an ending would refuse a save the player
        # reached by playing correctly.
        state = seated(day=20, starve_from=19)
        self.assertGreater(
            models.partner_ledger(state.branch_state).arrears, 0)
        self.assertIsNone(state.game_over)
        save.state_from_dict(save.state_to_dict(state))


# ══ the epilogue ═════════════════════════════════════════════════

class TestTheEpilogueRendersTheGrade(unittest.TestCase):
    def _epilogue(self, state):
        con = Listening()
        game.epilogue(state, con)
        return con

    def test_operation_no_longer_prints_the_legitimate_exit(self):
        # THE measured defect: before the fail-closed dispatcher, a
        # Partner run carrying `operation` printed the Straight
        # Path's rarest outcome.
        state = seated()
        set_terms(state, net=99_999, reputation=99.0)
        state.game_over = models.OPERATION_ENDING
        con = self._epilogue(state)
        self.assertNotIn("legitimate exit", con.ending())
        self.assertIn("The Operation", con.ending())

    def test_each_tier_has_its_own_text(self):
        seen = {}
        for net, rep, tier in ((99_999, 99.0, "healthy"),
                               (99_999, 1.0, "working"),
                               (0, 99.0, "working"),
                               (0, 1.0, "hollow")):
            state = seated()
            set_terms(state, net=net, reputation=rep)
            state.game_over = models.OPERATION_ENDING
            self.assertEqual(partner.grade_view(state).tier, tier)
            seen[(net, rep)] = self._epilogue(state).ending()
        # Four cases, FOUR distinct texts: `working`'s two arms are
        # different stories, not one text reached twice.
        self.assertEqual(len(set(seen.values())), 4)
        self.assertIn("money without a room", seen[(99_999, 1.0)])
        self.assertIn("a room without money", seen[(0, 99.0)])

    def test_the_header_prints_the_grade_s_net_not_the_gross_one(self):
        # rev. 36 item 4, with the two numbers made to DIFFER so a
        # header reading the wrong one is visible.
        state = hooked()
        set_terms(state, net=12_000, reputation=90.0)
        state.game_over = models.ON_THE_HOOK_ENDING
        view = partner.grade_view(state)
        self.assertNotEqual(view.net, state.net_worth())
        con = self._epilogue(state)
        header = next(ln for ln in con.lines if "Net position" in ln)
        self.assertIn(f"${view.net:,}", header)
        self.assertNotIn(f"${state.net_worth():,}", header)

    def test_the_hook_names_what_is_owed(self):
        state = hooked()
        state.game_over = models.ON_THE_HOOK_ENDING
        owed = partner.grade_view(state).arrears
        con = self._epilogue(state)
        self.assertIn("On the Hook", con.ending())
        self.assertTrue(con.said(f"${owed:,}"))

    def test_the_arrest_carries_partner_flavour(self):
        state = seated(day=20)
        state.add_case(100.0, "the file closes", kind="physical")
        self.assertEqual(state.game_over, "arrested")
        con = self._epilogue(state)
        self.assertTrue(con.said("Carmine is never in the report"))

    def test_the_arrest_elsewhere_is_untouched(self):
        state = new_state()
        state.day = 20
        state.add_case(100.0, "the file closes", kind="physical")
        con = self._epilogue(state)
        self.assertFalse(con.said("Carmine is never in the report"))
        self.assertIn("The Case closed — on you", con.ending())

    def test_no_raw_key_reaches_the_epilogue(self):
        state = seated()
        set_terms(state, net=99_999, reputation=99.0)
        state.game_over = models.OPERATION_ENDING
        con = self._epilogue(state)
        for line in con.lines:
            for shop in state.shops:
                self.assertNotIn(shop.key, line)


# ══ the card, after the night is settled ═════════════════════════

class TestTheDayThirtyCard(unittest.TestCase):
    def _night(self, state, con=None, seed=5):
        con = con or Listening()
        phases.night(state, {"routes": {}},
                     {"wagons": phases.WagonNight(state)}, con,
                     Streams(seed), PARTNER_ON)
        return con

    def _open_run(self, day: int = 20):
        state = seated(day=day)
        state.clean, state.dirty = 40_000, 0
        return state

    def test_it_speaks_prospectively_and_names_the_room(self):
        state = self._open_run()
        con = self._night(state)
        self.assertTrue(con.said("The day-30 track"))
        self.assertTrue(con.said("where this month is pointing"))
        self.assertTrue(con.said("University Hill reputation"))
        self.assertFalse(con.said("ENDING"))

    def test_the_tier_and_the_arrears_are_two_readings(self):
        state = seated(day=20, starve_from=19)
        state.clean = 40_000
        con = self._night(state)
        self.assertTrue(con.said("On this track: the"))
        self.assertTrue(con.said("day thirty is On the Hook"))

    def test_a_square_run_says_so_separately(self):
        con = self._night(self._open_run())
        self.assertTrue(con.said("Carmine is square"))

    def test_it_reflects_the_post_law_view(self):
        # THE reason it renders where it does (rev. 36 item 2): the
        # law still moves money AFTER the points bill has run, so a
        # card rendered beside that bill would be stale.
        #
        # The discriminator is exact and does not depend on which
        # other night charges happen to land: the net is captured AT
        # THE MOMENT THE LAW PHASE BEGINS, and the card must print
        # something different — proving it was rendered downstream of
        # the law rather than upstream of it.
        state = self._open_run()
        # Over the 85 that freezes deposits, and UNDER the 100 that
        # closes the file — an arrest would suppress the card, which
        # is a different case (below) and would prove nothing here.
        state.add_case(88.0 - state.case, "a thick file", kind="physical")
        self.assertGreater(state.case, 85.0)
        self.assertLess(state.case, 100.0)
        set_terms(state, net=models.OPERATION_NET_THRESHOLD + 200,
                  reputation=90.0)
        self.assertTrue(partner.grade_view(state).net_met)
        seen = {}
        real_law = phases._law_phase

        def watched(st, con, streams):
            seen["at_law"] = partner.grade_view(st).net
            return real_law(st, con, streams)

        with mock.patch.object(phases, "_law_phase", watched):
            con = self._night(state)
        after = partner.grade_view(state).net
        # The law froze deposits: the file is over 85.
        self.assertTrue(con.said("under review"))
        self.assertEqual(seen["at_law"] - after, 500)
        self.assertTrue(con.said(f"Combined net ${after:,}"))
        self.assertFalse(con.said(f"Combined net ${seen['at_law']:,}"))
        # …and the verdict itself flipped, so this is not cosmetic.
        self.assertFalse(partner.grade_view(state).net_met)

    def test_an_arrest_that_night_suppresses_it(self):
        state = self._open_run()
        state.add_case(99.5, "almost the whole file", kind="physical")
        con = Listening()
        # The law phase closes the file this night on a hot district.
        state.districts["old_harbor"].heat = 100.0
        for seed in range(40):
            probe = save.state_from_dict(save.state_to_dict(state))
            probe.shop_by_key(HOME_SHOP_KEY).stash = {"mushrooms": 8}
            con = self._night(probe, Listening(), seed=seed)
            if probe.game_over == "arrested":
                self.assertFalse(con.said("The day-30 track"))
                return
        self.skipTest("no seed closed the file this night")

    def test_a_building_site_shows_no_restaurant_term(self):
        state = seated(day=14)          # accepted today, opens day 16
        state.clean = 40_000
        con = self._night(state)
        self.assertFalse(con.said("The day-30 track"))

    def test_a_stand_pat_night_shows_nothing(self):
        state = new_state()
        state.day = 20
        con = Listening()
        phases.night(state, {"routes": {}},
                     {"wagons": phases.WagonNight(state)}, con, Streams(5))
        self.assertFalse(con.said("The day-30 track"))


# ══ the whole month, through the real loop ═══════════════════════

class TestTheDayThirtyDispatch(unittest.TestCase):
    """§2.5 precedence 5: the run loop's own matrix, not
    `partner.grade` called directly beside it. The probe sweep found
    this arm unexercised — `grade` was proved and the DISPATCH that
    reaches it was not."""

    def test_a_partner_run_is_graded_by_its_own_matrix(self):
        square = seated()
        set_terms(square, net=99_999, reputation=99.0)
        self.assertEqual(game.day_thirty_grade(square),
                         models.OPERATION_ENDING)
        owing = hooked()
        set_terms(owing, net=99_999, reputation=99.0)
        self.assertEqual(game.day_thirty_grade(owing),
                         models.ON_THE_HOOK_ENDING)

    def test_a_partner_run_no_longer_falls_through_to_stand_pat(self):
        # Before P4b.4 every chair but straight and war reached the
        # `survived` grades here.
        for state in (seated(), hooked()):
            self.assertNotEqual(game.day_thirty_grade(state), "survived")

    def test_the_other_chairs_are_unmoved(self):
        state = new_state()
        state.day = data.DEBT_DUE_DAY
        state.debt = 0
        self.assertEqual(game.day_thirty_grade(state), "survived")
        state.debt = 5_000
        self.assertEqual(game.day_thirty_grade(state), "kneecaps")
        state.branch = models.STAND_PAT
        self.assertEqual(game.day_thirty_grade(state), "kneecaps")


class TestTheRunEndsWhereTheLedgerSays(unittest.TestCase):
    def test_a_square_partner_run_grades_operation(self):
        state = seated()
        set_terms(state, net=99_999, reputation=99.0)
        self.assertEqual(partner.grade(state), models.OPERATION_ENDING)
        state.game_over = partner.grade(state)
        save.state_from_dict(save.state_to_dict(state))

    def test_an_indebted_partner_run_grades_on_the_hook(self):
        state = hooked()
        set_terms(state, net=99_999, reputation=99.0)
        self.assertEqual(partner.grade(state), models.ON_THE_HOOK_ENDING)
        state.game_over = partner.grade(state)
        save.state_from_dict(save.state_to_dict(state))

    def test_a_partner_run_never_grades_survived_again(self):
        # Before P4b.4 the day-30 dispatch fell through to the
        # stand-pat grades for every chair but straight and war.
        state = seated()
        set_terms(state, net=0, reputation=0.0)
        self.assertNotEqual(partner.grade(state), "survived")
        self.assertIn(partner.grade(state),
                      (models.OPERATION_ENDING, models.ON_THE_HOOK_ENDING))


if __name__ == "__main__":
    unittest.main()
