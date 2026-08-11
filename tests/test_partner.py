"""P4b.1b — the site, the deal, and the address it builds.

§2.4.2's branch begins with one transaction: Carmine's $20,000, of
which $13,000 is committed to his own contractor in the same act that
creates the second address and its wagon, and only the float and the
reserve reach the player. This file carries that PR's local proof —
the gates from here on are containment and say nothing about whether
the branch works (rev. 30 item 1).

Every district here is named by IDENTITY, never by menu position
(rev. 31 item 2): a positional literal would claim identity and mean
position, and a card reorder would silently change which world these
tests build.
"""

import random
import unittest
from unittest import mock

from extra_toppings import (data, market, models, partner, phases,
                            save, sitdown)
from extra_toppings.config import GameConfig
from extra_toppings.models import (CONSTRUCTION_DAYS, HOME_SHOP_KEY,
                                   Shop, SitdownSnapshot, Wagon, new_state)
from extra_toppings.rng import Streams
from extra_toppings.ui import ScriptedConsole

PARTNER_ON = GameConfig(fork_enabled=True,
                        enabled_branches=frozenset({"partner"}))


class Listening(ScriptedConsole):
    """Scripted answers plus everything said — the deal's numbers are
    prose, and prose never reaches `transcript`."""

    def __init__(self, script=None):
        super().__init__(script)
        self.lines: list = []
        self.scenes: list = []

    def say(self, text: str = "") -> None:
        self.lines.append(text)

    def bullet(self, text: str) -> None:
        self.lines.append(f"• {text}")

    def scene_menu(self, namespace, prompt, options):
        self.scenes.append((prompt, list(options)))
        return super().scene_menu(namespace, prompt, options)

    def offered(self, prompt):
        return next((o for p, o in self.scenes if p == prompt), [])

    def said(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


def table_state(payoff_day: int = 13, case: float = 20.0):
    """A world standing at the sit-down morning, one address, debt
    dead — the only state from which the deal may be struck. The
    Case is a REAL ledger record, so the snapshot's count is a true
    prefix of the evidence it was frozen from."""
    state = new_state()
    state.debt = 0
    state.debt_paid_day = payoff_day
    state.day = payoff_day + 1
    if case:
        state.add_case(case, "prior seizures", kind="physical")
    state.sitdown_snapshot = SitdownSnapshot(
        payoff_day=payoff_day, case_at_lockup=case,
        evidence_count_at_lockup=len(state.evidence))
    return state


def site_answer(district: str) -> int:
    """The scripted scene answer for a named site — derived from the
    card order, never written down as a number."""
    return 1 + partner.SITE_DISTRICTS.index(district)


def seat_partner(state, district="university", con=None):
    """The REAL scene: chair, site, handshake."""
    con = con or Listening()
    con.script = [1, site_answer(district), 1]
    sitdown.run_scene(state, con, PARTNER_ON)
    return con


# ══ identity minting (rev. 31 item 1) ═════════════════════════════

class TestIdentityMinting(unittest.TestCase):
    def test_the_first_minted_pair_is_two(self):
        state = new_state()
        self.assertEqual(models.mint_shop_key(state), "shop2")
        self.assertEqual(models.mint_wagon_key(state), "wagon2")

    def test_a_sparse_key_set_takes_the_hole_not_the_next_number(self):
        # `shop1` + `shop3` must mint `shop2`. "Last plus one" or a
        # count would mint `shop4` here and, worse, would mint an
        # ALREADY TAKEN key the moment a set is sparse the other way.
        state = new_state()
        state.shops.append(Shop(key="shop3", district="university",
                                acceptance_day=1,
                                opening_day=1 + CONSTRUCTION_DAYS))
        state.wagons.append(Wagon(key="wagon3", shop_key="shop3"))
        self.assertEqual(models.mint_shop_key(state), "shop2")
        self.assertEqual(models.mint_wagon_key(state), "wagon2")

    def test_reordering_the_lists_changes_nothing(self):
        state = new_state()
        state.shops.append(Shop(key="shop2", district="university",
                                acceptance_day=1,
                                opening_day=1 + CONSTRUCTION_DAYS))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        before = (models.mint_shop_key(state), models.mint_wagon_key(state))
        state.shops.reverse()
        state.wagons.reverse()
        self.assertEqual(
            (models.mint_shop_key(state), models.mint_wagon_key(state)),
            before)
        self.assertEqual(before, ("shop3", "wagon3"))

    def test_minting_twice_returns_the_same_key(self):
        # THE reason there may be exactly one caller: minting is a
        # calculation, not a claim. Pinned as the hazard it is, so
        # nobody reads the authority as reserving anything.
        state = new_state()
        self.assertEqual(models.mint_shop_key(state),
                         models.mint_shop_key(state))

    def test_the_deal_is_the_only_production_caller(self):
        # The call-site scope guard (rev. 31 item 1), the same shape
        # as the founding-key guard: minting is unclaimed, so a
        # second caller would be handed a key the first is about to
        # use and would overwrite that record.
        import ast
        import pathlib
        root = pathlib.Path(models.__file__).parent
        seen = set()
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            scopes: dict = {}

            def walk(node, scope):
                for child in ast.iter_child_nodes(node):
                    here = child.name if isinstance(
                        child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                ast.ClassDef)) else scope
                    scopes[id(child)] = here
                    walk(child, here)

            walk(tree, "<module>")
            for node in ast.walk(tree):
                name = (node.id if isinstance(node, ast.Name) else
                        node.attr if isinstance(node, ast.Attribute)
                        else None)
                if name in ("mint_shop_key", "mint_wagon_key"):
                    where = scopes.get(id(node))
                    if f"{path.name}:{where}" != "models.py:None":
                        seen.add(f"{path.name}:{where}")
        self.assertEqual(seen, {"partner.py:accept_deal"})


# ══ the site cards (rev. 31 item 2) ═══════════════════════════════

class TestTheSiteCards(unittest.TestCase):
    def test_the_order_is_the_storys_safe_to_dangerous(self):
        self.assertEqual(partner.SITE_DISTRICTS,
                         ("university", "little_sicily", "meadows"))

    def test_the_card_set_is_every_district_but_the_founding_one(self):
        # The rule is the SET; the tuple is the telling. They cannot
        # drift without the module refusing to import — this asserts
        # the same equality the import-time check enforces.
        self.assertEqual(set(partner.SITE_DISTRICTS),
                         set(data.DISTRICTS) - {data.HOME_DISTRICT})
        self.assertNotIn(data.HOME_DISTRICT, partner.SITE_DISTRICTS)

    def test_no_district_is_offered_twice(self):
        # Set equality alone accepts a repeated card — (…, "meadows",
        # "meadows") covers exactly the same districts — and the
        # player would be offered Vinnie's floor twice, the second
        # copy answering to a different menu index. Coverage AND
        # uniqueness; the import-time check enforces both.
        self.assertEqual(len(partner.SITE_DISTRICTS),
                         len(set(partner.SITE_DISTRICTS)))
        self.assertEqual(len(partner.SITE_DISTRICTS),
                         len(data.DISTRICTS) - 1)

    def test_the_owners_are_the_districts_own(self):
        owners = {d: data.DISTRICTS[d]["rival"]
                  for d in partner.SITE_DISTRICTS}
        self.assertEqual(owners, {"university": None,
                                  "little_sicily": "sal",
                                  "meadows": "vinnie"})

    def test_the_scene_offers_the_cards_in_that_order(self):
        state = table_state()
        con = seat_partner(state, "university")
        shown = con.offered("Where does the second room go?")
        self.assertEqual(shown[0], "Reconsider")
        for card, district in zip(shown[1:], partner.SITE_DISTRICTS):
            self.assertIn(data.DISTRICTS[district]["label"], card)

    def test_a_raw_district_key_never_reaches_the_player(self):
        state = table_state()
        con = seat_partner(state, "university")
        shown = " ".join(con.offered("Where does the second room go?"))
        for district in partner.SITE_DISTRICTS:
            self.assertNotIn(district, shown)


# ══ the points schedule (rev. 31 item 3) ══════════════════════════

class TestTheFirstPointsDate(unittest.TestCase):
    """The four recorded boundary pins, so the early-payoff edge is
    tested rather than believed."""

    CASES = ((10, 11, 21), (11, 12, 17), (13, 14, 19), (20, 21, 26))

    def test_the_recorded_boundaries(self):
        for payoff, acceptance, due in self.CASES:
            with self.subTest(payoff=payoff):
                shop = Shop(key="shop2", district="university",
                            acceptance_day=acceptance,
                            opening_day=acceptance + CONSTRUCTION_DAYS)
                self.assertEqual(partner.first_points_due(shop, payoff),
                                 due)

    def test_the_boundaries_hold_through_the_real_scene(self):
        # Not the authority alone: the same four cases driven through
        # the table, so the schedule the player actually gets is the
        # one the ruling names.
        for payoff, acceptance, due in self.CASES:
            with self.subTest(payoff=payoff):
                state = table_state(payoff_day=payoff)
                seat_partner(state)
                site = state.shops[-1]
                self.assertEqual(site.acceptance_day, acceptance)
                self.assertEqual(state.branch_state.points_due_day, due)

    def test_the_early_compliment_is_one_whole_cycle(self):
        early = partner.first_points_due(
            Shop(key="s", district="university", acceptance_day=11,
                 opening_day=13), 10)
        ordinary = partner.first_points_due(
            Shop(key="s", district="university", acceptance_day=11,
                 opening_day=13), 11)
        self.assertEqual(early - ordinary, partner.POINTS_CYCLE_DAYS)

    def test_the_founding_address_strikes_no_deal(self):
        # Its acceptance day is ABSENT, and absence is the founding
        # identity — there is no date to schedule from, so this
        # refuses rather than inventing one.
        with self.assertRaises(ValueError):
            partner.first_points_due(new_state().shops[0], 13)

    def test_the_schedule_reads_the_persisted_date_not_the_scene(self):
        # Move the record and the schedule moves with it: proof that
        # the address's own field is the source, not a reconstruction
        # from the sit-down morning.
        shop = Shop(key="shop2", district="university",
                    acceptance_day=20, opening_day=22)
        self.assertEqual(partner.first_points_due(shop, 13), 25)


# ══ the deal itself ═══════════════════════════════════════════════

class TestTheItemizationReconciles(unittest.TestCase):
    def test_the_parts_add_up_to_what_he_fronts(self):
        self.assertEqual(partner.COMMITTED + partner.TO_CLEAN,
                         partner.FRONTED)

    def test_the_committed_and_arriving_halves_are_canon(self):
        self.assertEqual(partner.COMMITTED, 13_000)
        self.assertEqual(partner.TO_CLEAN, 7_000)
        self.assertEqual(
            (partner.BUILD_OUT, partner.PERMITS, partner.SECOND_WAGON,
             partner.OPENING_FLOAT, partner.RESERVE),
            (9_000, 1_500, 2_500, 3_000, 4_000))


class TestTheDealBuildsTheAddress(unittest.TestCase):
    def _seated(self, district="university", payoff_day=13):
        state = table_state(payoff_day=payoff_day)
        clean_before = state.clean
        con = seat_partner(state, district)
        return state, con, clean_before

    def test_the_address_and_its_wagon_arrive_together(self):
        state, _con, _clean = self._seated()
        site = state.shops[-1]
        self.assertEqual([s.key for s in state.shops],
                         [HOME_SHOP_KEY, "shop2"])
        self.assertEqual([w.shop_key for w in state.wagons],
                         [models.HOME_SHOP_KEY, "shop2"])
        self.assertEqual(site.district, "university")

    def test_only_the_float_and_reserve_reach_clean_cash(self):
        state, _con, clean_before = self._seated()
        self.assertEqual(state.clean - clean_before, partner.TO_CLEAN)

    def test_the_initial_state_is_canons(self):
        state, _con, _clean = self._seated()
        site = state.shops[-1]
        self.assertEqual(site.reputation, 20.0)
        self.assertEqual(site.pantry_quality, "standard")
        self.assertEqual(site.ingredients, 0)
        self.assertEqual(site.stash, {})
        self.assertEqual(site.upgrades, set())
        self.assertEqual((site.demand_today, site.delivery_pool,
                          site.legit_revenue_today), (0, 0, 0))

    def test_the_dates_are_the_scene_morning_and_two_days_on(self):
        state, _con, _clean = self._seated(payoff_day=13)
        site = state.shops[-1]
        self.assertEqual(site.acceptance_day, 14)
        self.assertEqual(site.opening_day, 14 + CONSTRUCTION_DAYS)
        self.assertFalse(models.shop_is_open(site, state.day))

    def test_the_world_it_builds_survives_a_round_trip(self):
        state, _con, _clean = self._seated()
        loaded = save.state_from_dict(save.state_to_dict(state))
        site = loaded.shop_by_key("shop2")
        self.assertEqual(site.acceptance_day, 14)
        self.assertEqual(loaded.branch, "partner")
        self.assertEqual(loaded.branch_state.points_due_day, 19)

    def test_opening_on_owned_turf_is_a_declaration(self):
        for district, owner in (("little_sicily", "sal"),
                                ("meadows", "vinnie")):
            with self.subTest(district):
                state = table_state()
                before = state.rivals[owner].relation
                seat_partner(state, district)
                self.assertEqual(state.rivals[owner].relation - before,
                                 partner.TURF_RELATION_DELTA)

    def test_the_unowned_site_costs_no_relation_anywhere(self):
        state = table_state()
        before = {k: r.relation for k, r in state.rivals.items()}
        seat_partner(state, "university")
        self.assertEqual({k: r.relation for k, r in state.rivals.items()},
                         before)

    def test_a_dead_owner_mounts_no_counterplay(self):
        state = table_state()
        state.rivals["sal"].strength = 0.0      # `alive` derives
        self.assertFalse(state.rivals["sal"].alive)
        before = state.rivals["sal"].relation
        seat_partner(state, "little_sicily")
        self.assertEqual(state.rivals["sal"].relation, before)

    def test_the_entry_scene_states_the_split(self):
        _state, con, _clean = self._seated()
        self.assertTrue(con.said("$20,000 fronted"), con.lines)
        self.assertTrue(con.said("$13,000"), con.lines)
        self.assertTrue(con.said("$7,000"), con.lines)


# ══ atomicity ═════════════════════════════════════════════════════

class TestTheTransactionIsAtomic(unittest.TestCase):
    """Either the deal commits AND validates, or nothing moved. The
    refusals below are checked against a COMPLETE snapshot of what
    the transaction touches, because a rollback that misses one field
    is the half-built branch this contract exists to forbid."""

    def _snapshot(self, state):
        return ([s.key for s in state.shops],
                [w.key for w in state.wagons], state.clean, state.dirty,
                state.branch, state.branch_state, state.act,
                {k: r.relation for k, r in state.rivals.items()})

    def _refused(self, state, district, exc=ValueError):
        before = self._snapshot(state)
        with self.assertRaises(exc):
            partner.accept_deal(state, district)
        self.assertEqual(self._snapshot(state), before)

    def test_an_unknown_district_moves_nothing(self):
        self._refused(table_state(), "atlantis")

    def test_the_founding_district_is_not_a_site(self):
        self._refused(table_state(), data.HOME_DISTRICT)

    def test_a_chair_already_taken_moves_nothing(self):
        state = table_state()
        state.branch = "war"
        self._refused(state, "university")

    def test_a_world_with_no_table_moves_nothing(self):
        # The payoff day is the SNAPSHOT's, so a state that never sat
        # down has no schedule to start from.
        state = table_state()
        state.sitdown_snapshot = None
        self._refused(state, "university")

    def test_a_day_that_is_not_the_scene_morning_moves_nothing(self):
        state = table_state(payoff_day=13)
        state.day = 20
        self._refused(state, "university")

    def test_a_world_that_already_has_two_addresses_moves_nothing(self):
        state = table_state()
        state.shops.append(Shop(key="shop2", district="meadows",
                                acceptance_day=1,
                                opening_day=1 + CONSTRUCTION_DAYS))
        state.wagons.append(Wagon(key="wagon2", shop_key="shop2"))
        self._refused(state, "university")

    def test_an_empty_chair_moves_nothing_calendar_gate(self):
        # Standing in the right room on the right morning is not
        # being offered the deal. A payoff on day 21 leaves R = 9,
        # under Partner's calendar gate, and the chair is EMPTY —
        # a direct call must not build a branch the scene would
        # never have seated.
        state = table_state(payoff_day=21)
        self._refused(state, "university")

    def test_an_empty_chair_moves_nothing_case_gate(self):
        # A file over Partner's Case gate closes the chair too:
        # nobody invests in a burning building.
        state = table_state(payoff_day=13, case=72.0)
        self._refused(state, "university")

    def test_the_gates_are_the_scenes_own_never_a_second_copy(self):
        # The verdict is CONSUMED from the canonical evaluator. Two
        # copies of MIN_R or CASE_GATE would be free to disagree with
        # the chair the player was shown, so the boundary is asserted
        # against `sitdown`'s own numbers rather than against
        # literals repeated here.
        # Derived from the canonical gate: the payoff day that
        # leaves exactly MIN_R days seats, and one day later does
        # not. Both numbers come from `sitdown`, never from here.
        at_the_gate = 30 - sitdown.MIN_R["partner"]
        for payoff in (at_the_gate, at_the_gate + 1):
            with self.subTest(payoff=payoff):
                state = table_state(payoff_day=payoff)
                verdict = next(
                    v for v in sitdown.evaluate_chairs(
                        state.sitdown_snapshot, state.evidence)
                    if v.chair == "partner")
                if verdict.available:
                    partner.accept_deal(state, "university")
                    self.assertEqual(state.branch, "partner")
                else:
                    self._refused(state, "university")

    def test_the_case_gate_boundary_seats_exactly_at_the_edge(self):
        # The gate is `case >= CASE_GATE`, so one tick under it is
        # still a chair — pinned so a future off-by-one is visible.
        edge = sitdown.CASE_GATE["partner"]
        state = table_state(payoff_day=13, case=edge - 0.1)
        partner.accept_deal(state, "university")
        self.assertEqual(state.branch, "partner")

    def test_a_postcondition_failure_unwinds_the_whole_deal(self):
        # Preflight alone does not make a transaction atomic: the
        # world-level validators run AFTER the records exist. There is
        # no DATA that reaches this — every reachable refusal is in
        # the preflight — so the validator is made to refuse, which
        # is the only honest way to exercise the unwind.
        state = table_state()
        before = self._snapshot(state)
        with mock.patch.object(models, "validate_cross_state",
                               side_effect=ValueError("refused")):
            with self.assertRaises(ValueError):
                partner.accept_deal(state, "little_sicily")
        # Cash, both records, the branch fields AND the turf delta.
        self.assertEqual(self._snapshot(state), before)

    def test_a_refused_deal_leaves_a_loadable_world(self):
        state = table_state()
        with mock.patch.object(models, "validate_cross_state",
                               side_effect=ValueError("refused")):
            with self.assertRaises(ValueError):
                partner.accept_deal(state, "meadows")
        save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(len(state.shops), 1)


# ══ the D14–D17 walkthrough ═══════════════════════════════════════

class TestTheWalkthrough(unittest.TestCase):
    """§3.2's D14–D17, scripted through the REAL day loop: the deal is
    struck on the sit-down morning, the site stands for two days, and
    it opens on the third — with every capability following the
    lifecycle rather than a flag."""

    def _walk(self, district="university"):
        state = table_state(payoff_day=13)
        seat_partner(state, district)
        market.roll_prices(state, random.Random(3))
        return state

    def test_the_deal_lands_on_D14(self):
        state = self._walk()
        self.assertEqual(state.day, 14)
        self.assertEqual(state.shops[-1].acceptance_day, 14)
        self.assertEqual(state.branch, "partner")

    def test_D14_to_D15_the_site_stands_and_serves_nobody(self):
        state = self._walk()
        site = state.shops[-1]
        for day in (14, 15):
            state.day = day
            self.assertFalse(models.shop_is_open(site, day))
            self.assertEqual(
                [s.key for s in models.addresses_allowing(state, "service")],
                [HOME_SHOP_KEY])
            # It may still be prepared — canon allows exactly that.
            self.assertIn(site, models.addresses_allowing(
                state, "pantry_supply"))
            self.assertIn(site, models.addresses_allowing(
                state, "staffing"))

    def test_D16_it_opens_and_does_everything(self):
        state = self._walk()
        state.day = 16
        site = state.shops[-1]
        self.assertTrue(models.shop_is_open(site, state.day))
        for capability in models.ADDRESS_CAPABILITIES:
            self.assertTrue(
                models.address_allows(site, state.day, capability),
                capability)

    def test_the_morning_service_and_night_run_through_D17(self):
        # The real loop, four days, no exception and no game over —
        # the walkthrough's actual claim.
        state = self._walk()
        streams = Streams(3)
        for day in (14, 15, 16, 17):
            state.day = day
            con = ScriptedConsole([8])
            plans = phases.morning(state, con, streams)
            report = phases.service(state, plans, con, streams)
            phases.night(state, plans, report, con, streams, PARTNER_ON)
            self.assertIsNone(state.game_over)
        self.assertEqual(len(state.shops), 2)
        save.state_from_dict(save.state_to_dict(state))

    def _stock_the_site_through_the_morning(self, state, streams, day):
        """Day 15, the real morning: buy the site a pantry while it is
        still a building site — canon ALLOWS exactly that, and it is
        what makes the day-16 till a measurement rather than a hope.
        The picker answer is derived from the eligible list, never
        written as an index."""
        state.day = day
        able = [a.key for a in
                models.addresses_allowing(state, "pantry_supply")]
        con = ScriptedConsole([2, able.index("shop2"), 40, 8])
        return phases.morning(state, con, streams)

    def test_the_second_till_is_silent_on_15_and_rings_on_16(self):
        # The vacuous version of this asserted `>= 0`, which passes
        # when the second shop earns nothing at all. Deterministic
        # now: stock bought on 15 through the real morning, and on 16
        # the till, the clean cash and the pantry all move together.
        state = self._walk()
        streams = Streams(3)
        site = state.shops[-1]

        plans = self._stock_the_site_through_the_morning(state, streams, 15)
        self.assertEqual(site.ingredients, 40)     # prepared, not trading
        phases.service(state, plans, ScriptedConsole([]), streams)
        self.assertEqual(site.legit_revenue_today, 0)
        self.assertEqual(site.ingredients, 40)     # nothing was baked
        self.assertEqual(site.demand_today, 0)

        state.day = 16
        clean_before = state.clean
        plans = phases.morning(state, ScriptedConsole([8]), streams)
        self.assertGreater(site.demand_today, 0)   # an order book at last
        phases.service(state, plans, ScriptedConsole([]), streams)
        self.assertGreater(site.legit_revenue_today, 0)
        self.assertLess(site.ingredients, 40)      # the kitchen baked
        self.assertGreaterEqual(state.clean - clean_before,
                                site.legit_revenue_today)

    def _two_route_night(self, state):
        """Two REAL routes, one per address, distinct drivers, each
        carrying its own address's stock — the night §7 asks for."""
        drivers = [e for e in state.employees if e.driving >= 4][:2]
        for e in drivers:
            e.hired = e.aware = True
        home = state.shop_by_key(HOME_SHOP_KEY)
        site = state.shop_by_key("shop2")
        home.stash = {"mushrooms": 4}
        site.stash = {"oregano": 3}
        home.ingredients = site.ingredients = 40
        home.delivery_pool = site.delivery_pool = 10
        plans = {"routes": {}}
        for shop_key, driver, cargo in (
                (HOME_SHOP_KEY, drivers[0], {"mushrooms": 2}),
                ("shop2", drivers[1], {"oregano": 2})):
            # The wagon KEPT at that address, by identity — not the
            # claimable list, which is empty while the site is under
            # construction and would turn this fixture into a ghost.
            wagon = state.wagons_at(shop_key)
            plans["routes"][shop_key] = {
                "district": "old_harbor", "driver": driver,
                "ride_along": False, "cargo": dict(cargo), "legit": 2,
                "origin_shop": shop_key,
                # The wagon is named from the address's OWN fleet, so
                # this fixture cannot quietly pair the wrong pair.
                "wagon_key": wagon[0].key}
        return plans, drivers, home, site

    def test_two_real_routes_run_the_night_it_opens(self):
        # §7's own words, executed rather than inspected: two plans,
        # two drivers, through the REAL service.
        state = self._walk()
        state.day = 16
        plans, _drivers, home, site = self._two_route_night(state)
        before = (dict(home.stash), dict(site.stash),
                  home.ingredients, site.ingredients)
        report = phases.service(state, plans, ScriptedConsole([]),
                                Streams(3))
        # Both EXACT wagons were claimed, each by its own address.
        self.assertEqual(report["wagons"].claims,
                         {models.HOME_WAGON_KEY: "route",
                          "wagon2": "route"})
        # Two execution records, one per origin.
        self.assertEqual(len(state.route_log), 2)
        self.assertEqual({r.origin_shop for r in state.route_log},
                         {HOME_SHOP_KEY, "shop2"})
        # Each address spent ITS OWN stock, in EXACT amounts. Asking
        # only whether home holds no oregano and the site holds no
        # mushrooms would pass on a night where neither wagon loaded
        # anything at all — the cross-address check is necessary and
        # nowhere near sufficient. Both halves are asserted: each
        # room's own good went down by the two units its route
        # loaded, and neither room acquired the other's.
        self.assertEqual(before[0]["mushrooms"] - home.stash["mushrooms"],
                         2)
        self.assertEqual(before[1]["oregano"] - site.stash["oregano"], 2)
        self.assertEqual((home.stash["mushrooms"], site.stash["oregano"]),
                         (2, 1))
        self.assertEqual(home.stash.get("oregano", 0), 0)
        self.assertEqual(site.stash.get("mushrooms", 0), 0)
        # And each oven baked its own cover: two pantries down, two
        # tills up, neither paying for the other's pizzas.
        self.assertLess(home.ingredients, before[2])
        self.assertLess(site.ingredients, before[3])
        self.assertGreater(home.legit_revenue_today, 0)
        self.assertGreater(site.legit_revenue_today, 0)

    def test_the_same_night_one_day_early_never_leaves_the_yard(self):
        # Day 15: the site's wagon is at the contractor's yard, so
        # that route is scrubbed BEFORE it commits — its stock and
        # pantry never move, and no record is written for it. The
        # founding address's route is unaffected: one address's
        # lifecycle never grounds the other's wagon.
        state = self._walk()
        state.day = 15
        plans, _drivers, home, site = self._two_route_night(state)
        site_before = (dict(site.stash), site.ingredients)
        report = phases.service(state, plans, ScriptedConsole([]),
                                Streams(3))
        self.assertEqual(report["wagons"].claims,
                         {models.HOME_WAGON_KEY: "route"})
        self.assertEqual((dict(site.stash), site.ingredients),
                         site_before)
        self.assertEqual([r.origin_shop for r in state.route_log],
                         [HOME_SHOP_KEY])
        self.assertNotIn("shop2", plans["routes"])
        self.assertGreater(home.legit_revenue_today, 0)

    def test_two_wagons_only_after_the_doors_open(self):
        # §7's "two real routes only after opening", at the lifecycle
        # boundary that decides it: the site's wagon exists from
        # acceptance and cannot roll until the address opens.
        state = self._walk()
        state.day = 15
        self.assertEqual(models.claimable_wagons(state, "shop2"), ())
        self.assertFalse(models.wagon_claim(state, "wagon2").available)
        state.day = 16
        self.assertEqual(models.claimable_wagons(state, "shop2"),
                         ("wagon2",))
        self.assertTrue(models.wagon_claim(state, "wagon2").available)

    def test_both_addresses_can_hold_a_route_the_morning_it_opens(self):
        state = self._walk()
        state.day = 16
        for shop_key in (HOME_SHOP_KEY, "shop2"):
            with self.subTest(shop_key):
                view = phases.planned_wagon(state, {"routes": {}}, shop_key)
                self.assertTrue(view.available)


if __name__ == "__main__":
    unittest.main()
