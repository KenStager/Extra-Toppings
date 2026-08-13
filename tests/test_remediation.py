"""Evidence remediation machinery (§2.3, rev. 9): the shared prefix
iterator, retention dormancy, counsel's contest queue, settlements, the
paid-points cap, the institutional-suspicion floor, and the persistence
contracts for all of it."""

import random
import unittest

from extra_toppings import evidence as ev
from extra_toppings import models, phases, save, sitdown, straight
from extra_toppings.models import (CASE_FLOOR, REMEDIATION_CAP, BranchState,
                                   Evidence, case_prefix, fold_case,
                                   new_state, validate_branch_state,
                                   validate_evidence)
from extra_toppings.models import remediation_disposition as models_disposition
from extra_toppings.rng import Streams
from extra_toppings.ui import Console
from route_support import departed


class Quiet(Console):
    def __init__(self):
        super().__init__()
        self.quiet = True
        self.lines: list = []

    def say(self, text=""):
        self.lines.append(text)

    def bullet(self, text):
        self.lines.append(f"• {text}")

    def find(self, fragment):
        return next((line for line in self.lines if fragment in line), None)


def straight_state():
    from extra_toppings.models import SitdownSnapshot
    state = new_state()
    state.debt = 0
    state.debt_paid_day = 13
    state.day = 14
    state.act = 2
    state.sitdown_snapshot = SitdownSnapshot(13, 0.0, 0)
    state.branch = "straight"
    state.branch_state = BranchState.straight()
    validate_branch_state(state.branch, state.branch_state)
    return state


# ══ The shared prefix iterator ════════════════════════════════════

class TestPrefixIterator(unittest.TestCase):
    def test_fold_case_consumes_the_shared_iterator(self):
        # The 3.12-divergent sequence from round 6: sequential addition
        # gives 61.50000000000001; the iterator must reproduce it bit
        # for bit, and fold_case must agree with the last running total.
        mags = [12.3, 0.5, 0.5, 0.5, 8.2, 0.5, 0.5, 20.0, 0.5, 18.0]
        records = [Evidence(day=1, magnitude=m, kind="paper", why="")
                   for m in mags]
        sequential = 0.0
        for m in mags:
            sequential += m
        runnings = [running for _r, running in case_prefix(records)]
        self.assertEqual(runnings[-1], sequential)
        self.assertEqual(fold_case(records), max(0.0, min(100.0, sequential)))

    def test_telegraph_and_gate_crossing_agree_with_the_iterator(self):
        state = new_state()
        state.add_case(30, "first", kind="physical")
        state.evidence[-1].day = 3
        state.add_case(35, "the crossing record", kind="paper")
        state.evidence[-1].day = 7
        state.add_case(10, "later", kind="physical")
        state.evidence[-1].day = 9
        self.assertEqual(phases._case_first_crossed_60_day(state), 7)
        self.assertEqual(
            sitdown.gate_crossing_record(state.evidence,
                                         len(state.evidence), 60.0),
            "the crossing record")

    def test_derived_protection_halves_at_fold_time_only(self):
        # Rev. 10: dormancy is context, not state — the fold halves a
        # protected source's records; the prefix scans stay raw (they
        # only run pre-branch, where protection cannot exist).
        records = [
            Evidence(day=1, magnitude=40.0, kind="witness", why="w",
                     source="e0"),
            Evidence(day=2, magnitude=45.0, kind="paper", why="p"),
        ]
        self.assertEqual(fold_case(records), 85.0)
        self.assertEqual(fold_case(records, frozenset({"e0"})), 65.0)
        # Raw prefix: 40 crosses 60 at the second record regardless.
        self.assertEqual(
            sitdown.gate_crossing_record(records, 2, 60.0), "p")


# ══ Counsel ═══════════════════════════════════════════════════════

class TestCounsel(unittest.TestCase):
    def test_fee_charged_and_contest_on_every_third_day(self):
        state = straight_state()
        state.branch_state.counsel_retained = True
        state.clean = 2000
        state.add_case(20, "the register claimed too much", kind="paper")
        state.add_case(15, "prior seizure", kind="physical")
        con = Quiet()
        for _ in range(3):
            ev.counsel_nightly(state, con)
        self.assertEqual(state.clean, 2000 - 3 * ev.COUNSEL_FEE)
        self.assertEqual(state.branch_state.counsel_days, 3)
        # -60% of the 20-point paper record; physical untouched.
        record = state.evidence[0]
        self.assertTrue(record.contested)
        self.assertAlmostEqual(record.magnitude, 8.0)
        self.assertEqual(state.evidence[1].magnitude, 15)
        self.assertAlmostEqual(state.branch_state.remediation_used, 12.0)

    def test_flagged_records_beat_older_routine_ticks(self):
        # §3.1 D16: the over-ceiling record is first in the queue even
        # though routine ticks predate it (rev. 9 item 2).
        state = straight_state()
        for _ in range(6):
            state.add_case(0.5, "", kind="paper")
        state.add_case(10, "the over-ceiling wash", kind="paper")
        con = Quiet()
        ev.contest_next(state, con)
        self.assertTrue(state.evidence[6].contested)
        self.assertAlmostEqual(state.evidence[6].magnitude, 4.0)
        self.assertTrue(all(not r.contested for r in state.evidence[:6]))

    def test_the_routine_hum_contests_once_as_one_record(self):
        state = straight_state()
        for _ in range(10):
            state.add_case(2.0, "", kind="paper")
        con = Quiet()
        ev.contest_next(state, con)
        ticks = [r for r in state.evidence if r.kind == "paper"]
        self.assertTrue(all(r.contested for r in ticks))
        for r in ticks:
            self.assertAlmostEqual(r.magnitude, 0.8)
        # One contest, one cap charge: 60% of the 20-point hum.
        self.assertAlmostEqual(state.branch_state.remediation_used, 12.0)
        self.assertIsNotNone(con.find(ev.HUM_LABEL))
        # The queue is now empty; the next contest argues nothing.
        ev.contest_next(state, con)
        self.assertIsNotNone(con.find("nothing left worth arguing"))

    def test_contest_truncates_at_the_cap(self):
        state = straight_state()
        state.branch_state.remediation_used = REMEDIATION_CAP - 2.0
        state.add_case(20, "big paper record", kind="paper")
        state.add_case(30, "ballast", kind="physical")
        con = Quiet()
        ev.contest_next(state, con)
        # Wanted 12 points, room 2: the record loses exactly 2.
        self.assertAlmostEqual(state.evidence[0].magnitude, 18.0)
        self.assertAlmostEqual(state.branch_state.remediation_used,
                               REMEDIATION_CAP)
        # And with the cap spent, the next contest refuses.
        state.add_case(20, "another paper record", kind="paper")
        ev.contest_next(state, con)
        self.assertEqual(state.evidence[-1].magnitude, 20)
        self.assertIsNotNone(con.find("every argument"))

    def test_contest_refuses_at_the_floor(self):
        state = straight_state()
        state.add_case(8, "small paper record", kind="paper")
        con = Quiet()
        ev.contest_next(state, con)
        self.assertEqual(state.evidence[0].magnitude, 8)
        self.assertFalse(state.evidence[0].contested)
        self.assertIsNotNone(con.find("as cold as they will let it get"))

    def test_unpaid_counsel_quits(self):
        state = straight_state()
        state.branch_state.counsel_retained = True
        state.clean = ev.COUNSEL_FEE - 1
        con = Quiet()
        ev.counsel_nightly(state, con)
        self.assertFalse(state.branch_state.counsel_retained)
        self.assertEqual(state.clean, ev.COUNSEL_FEE - 1)

    def test_counsel_is_a_dead_letter_after_the_latch(self):
        state = straight_state()
        state.branch_state.counsel_retained = True
        state.branch_state.counsel_days = 2   # next night would contest
        state.clean = 2000
        state.add_case(60, "seizures", kind="physical")
        state.add_case(45, "the register claimed too much", kind="paper")
        self.assertEqual(state.game_over, "arrested")
        ev.counsel_nightly(state, Quiet())
        self.assertEqual(state.clean, 2000)
        self.assertFalse(state.evidence[1].contested)
        self.assertEqual(state.game_over, "arrested")


# ══ Settlements ═══════════════════════════════════════════════════

class TestSettlements(unittest.TestCase):
    def _departed_witness(self, state, key="e3", magnitude=8.0):
        e = next(x for x in state.employees if x.key == key)
        e.aware = True
        e.hired = False
        e.morale = 3
        state.add_case(magnitude, f"{e.name} left knowing everything",
                       kind="witness", source=e.key)
        return e

    def test_settlement_halves_records_permanently(self):
        state = straight_state()
        e = self._departed_witness(state, magnitude=8.0)
        state.add_case(20, "ballast", kind="physical")
        state.clean = 2000
        con = Quiet()
        ev.settle_witness(state, e, con)
        self.assertEqual(state.clean, 2000 - 6 * e.wage)
        self.assertIn(e.key, state.branch_state.settled_witnesses)
        record = state.evidence[0]
        self.assertAlmostEqual(record.magnitude, 4.0)
        self.assertAlmostEqual(state.branch_state.remediation_used, 4.0)
        # Two outcomes, both stated (rev. 10 item 6).
        self.assertIsNotNone(con.find("peace is bought"))
        self.assertIsNotNone(con.find("go dormant for good"))

    def test_settling_out_a_current_witness_books_no_firing_record(self):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        state.add_case(10, f"{e.name} had a long talk with a detective",
                       kind="witness", source=e.key)
        state.add_case(20, "ballast", kind="physical")
        state.clean = 2000
        before_count = len(state.evidence)
        ev.settle_witness(state, e, Quiet())
        self.assertFalse(e.hired)
        self.assertEqual(len(state.evidence), before_count)
        self.assertIn(e.key, state.branch_state.settled_witnesses)

    def test_unaffordable_settlement_is_refused(self):
        state = straight_state()
        e = self._departed_witness(state)
        state.clean = 6 * e.wage - 1
        ev.settle_witness(state, e, Quiet())
        self.assertNotIn(e.key, state.branch_state.settled_witnesses)
        self.assertEqual(state.evidence[0].magnitude, 8.0)

    def test_a_protected_record_locks_in_for_free(self):
        # Derived retention already halves it; the settlement makes
        # the same half permanent and charges the cap nothing
        # (rev. 9 item 4, derived per rev. 10).
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 6
        state.add_case(10, "detective talk", kind="witness", source=e.key)
        state.add_case(20, "ballast", kind="physical")
        state.clean = 2000
        self.assertEqual(state.case, 25.0)      # derived halving live
        con = Quiet()
        ev.settle_witness(state, e, con)
        self.assertEqual(state.case, 25.0)      # unchanged, now permanent
        self.assertAlmostEqual(state.evidence[0].magnitude, 5.0)
        self.assertEqual(state.branch_state.remediation_used, 0.0)
        self.assertIsNotNone(con.find("no longer depends on their mood"))

    def test_below_the_floor_a_settlement_signs_but_relieves_nothing(self):
        state = straight_state()
        e = self._departed_witness(state, magnitude=6.0)
        state.clean = 2000
        con = Quiet()
        ev.settle_witness(state, e, con)
        self.assertIn(e.key, state.branch_state.settled_witnesses)
        self.assertEqual(state.evidence[0].magnitude, 6.0)
        self.assertEqual(state.branch_state.remediation_used, 0.0)
        self.assertIsNotNone(con.find("buys peace, not arithmetic"))

    def test_cap_exhausted_settlement_states_both_outcomes(self):
        # The review's exhibit: cap spent, Marcus paid — the old line
        # said his knowledge went "quiet for good" while the file
        # never moved. Both outcomes must now be stated (rev. 10).
        state = straight_state()
        e = self._departed_witness(state, magnitude=8.0)
        state.add_case(24, "ballast", kind="physical")
        state.branch_state.remediation_used = 25.0
        state.clean = 2000
        con = Quiet()
        ev.settle_witness(state, e, con)
        self.assertIn(e.key, state.branch_state.settled_witnesses)
        self.assertEqual(state.evidence[0].magnitude, 8.0)   # unmoved
        self.assertIsNotNone(con.find("peace is bought"))
        self.assertIsNotNone(con.find("every point the cap allows"))
        self.assertIsNone(con.find("quiet for good"))

    def test_the_informants_tip_is_paper_and_contestable(self):
        # Rev. 10 ruling: a tip in a file is a report, not testimony.
        import random as _random
        from extra_toppings import rivals as _rivals
        state = straight_state()
        seed = next(k for k in range(200)
                    if _random.Random(k).random() < 0.3)
        _rivals._plant(state, state.rivals["vinnie"], {"short": "Vinnie"},
                       Quiet(), _random.Random(seed))
        tip = state.evidence[-1]
        self.assertEqual(tip.kind, "paper")
        self.assertEqual(models_disposition(tip), "contestable")
        # And counsel's queue reaches it ahead of the hum.
        state.add_case(0.5, "", kind="paper")
        self.assertEqual(ev._contest_queue(state), [tip])

    def test_settlement_never_unlatches_an_arrest(self):
        state = straight_state()
        e = self._departed_witness(state, magnitude=40.0)
        state.add_case(60, "seizures", kind="physical")
        self.assertEqual(state.game_over, "arrested")
        state.clean = 5000
        ev.settle_witness(state, e, Quiet())
        self.assertEqual(state.game_over, "arrested")
        self.assertEqual(state.evidence[0].magnitude, 40.0)
        self.assertNotIn(e.key, state.branch_state.settled_witnesses)


# ══ The floor ═════════════════════════════════════════════════════

class TestTheFloor(unittest.TestCase):
    def test_suspicion_record_written_by_exactly_the_difference(self):
        state = straight_state()
        state.add_case(12, "the register claimed too much", kind="paper")
        con = Quiet()
        ev.contest_next(state, con)          # 12 → 4.8, below the floor
        self.assertEqual(state.case, CASE_FLOOR)
        suspicion = [r for r in state.evidence if r.kind == "suspicion"]
        self.assertEqual(len(suspicion), 1)
        self.assertEqual(suspicion[0].why, ev.SUSPICION_WHY)
        self.assertIn(f"day {state.day}: {ev.SUSPICION_WHY}",
                      state.case_flags)

    def test_topped_up_in_place_never_a_second_record(self):
        # Two sub-floor remediations, one suspicion record, both
        # differences accumulated in place.
        state = straight_state()
        for _ in range(10):
            state.add_case(0.5, "", kind="paper")       # the hum: 5.0
        state.add_case(12, "over-ceiling wash", kind="paper")
        con = Quiet()
        ev.contest_next(state, con)      # flagged: 17 → 9.8, top to 10
        self.assertEqual(state.case, CASE_FLOOR)
        suspicion = [r for r in state.evidence if r.kind == "suspicion"]
        self.assertEqual(len(suspicion), 1)
        self.assertAlmostEqual(suspicion[0].magnitude, 0.2)
        # Pinned at exactly the floor, the verb refuses (evidence-only
        # verbs never fire at or below 10)...
        ev.contest_next(state, con)
        self.assertEqual(state.case, CASE_FLOOR)
        # ...but once the world warms the file past the floor, the next
        # contest can overshoot below it — and the SAME record tops up.
        state.add_case(2, "a squad car's notes", kind="physical")
        ev.contest_next(state, con)      # the hum: 12 → 9, top to 10
        self.assertEqual(state.case, CASE_FLOOR)
        suspicion = [r for r in state.evidence if r.kind == "suspicion"]
        self.assertEqual(len(suspicion), 1)
        self.assertAlmostEqual(suspicion[0].magnitude, 1.2)


# ══ Derived retention protection (rev. 10) ════════════════════════

class TestDerivedDormancy(unittest.TestCase):
    def _protected_state(self):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 6
        state.add_case(10, "detective talk", kind="witness", source=e.key)
        state.add_case(20, "ballast", kind="physical")
        return state, e

    def test_protection_follows_the_live_roster_with_no_event(self):
        state, e = self._protected_state()
        self.assertEqual(state.case, 25.0)     # halved, right now
        e.morale = 4                           # no reconciliation runs
        self.assertEqual(state.case, 30.0)     # and none is needed
        e.morale = 6
        self.assertEqual(state.case, 25.0)

    def test_a_poach_wakes_the_record_instantly(self):
        state, e = self._protected_state()
        self.assertEqual(state.case, 25.0)
        e.hired = False                        # poached mid-night
        self.assertEqual(state.case, 30.0)

    def test_the_reviewers_final_night_repro(self):
        # The review's exhibit: a protected 20-point record over 30
        # physical read Case 40 and graded straight_exit after a late
        # morale slip; the true file reads 50 and grades almost_out.
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 5
        state.add_case(20, "detective talk", kind="witness", source=e.key)
        state.add_case(30, "seizures", kind="physical")
        state.shop_stash = {}
        state.dirty = 0
        for r in state.rivals.values():
            r.relation = -10.0
        state.shop.reputation = 60.0
        self.assertEqual(state.case, 40.0)
        self.assertEqual(straight.grade(state), "straight_exit")
        e.morale = 4                           # the search's last word
        self.assertEqual(state.case, 50.0)
        self.assertEqual(straight.grade(state), "almost_out")

    def test_relief_is_partial_at_the_boundary_and_monotone(self):
        # Rev. 11 item 1: allowance = raw − floor; the boundary record
        # takes PARTIAL relief, so total relief is exactly
        # min(halvable, allowance) and the display is monotone.
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 8
        # Raw 12, allowance 2, halvable 4 → partial cut 2 → display 10.
        state.add_case(8, "detective talk", kind="witness", source=e.key)
        state.add_case(4, "tip", kind="paper")
        self.assertEqual(state.case, 10.0)
        # More raw total → more allowance → the halving completes.
        state.add_case(8, "seizure", kind="physical")
        self.assertEqual(state.case, 16.0)     # 20 raw − 4 relief

    def test_settled_sources_are_not_double_halved(self):
        state, e = self._protected_state()
        state.clean = 2000
        ev.settle_witness(state, e, Quiet())   # locks 10 → 5, permanent
        self.assertEqual(state.case, 25.0)
        # Even rehired at high morale, a settled source never re-enters
        # the derived set — no quarter-weighting through the back door.
        e.hired = True
        e.morale = 9
        self.assertNotIn(e.key, state.dormant_sources())
        self.assertEqual(state.case, 25.0)


# ══ Monotone Case (rev. 11 item 1) ════════════════════════════════

class TestMonotoneCase(unittest.TestCase):
    """The six ruled properties, including both review repros: the
    meter must never move the wrong way around the floor."""

    def _protected(self, witness=12.0, paper=3.0):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 8
        state.add_case(witness, "detective talk", kind="witness",
                       source=e.key)
        if paper:
            state.add_case(paper, "flagged paper", kind="paper")
        return state, e

    def test_adding_evidence_cannot_lower_the_case(self):
        # Review repro 1: witness 12 + paper 3 read Case 15 under the
        # all-or-nothing allocation and FELL to 10 when a point of
        # paper arrived. Partial allocation: 10 before, 10 after.
        state, _e = self._protected()
        before = state.case
        self.assertEqual(before, 10.0)      # partial relief engages
        state.add_case(1, "new paper", kind="paper")
        self.assertGreaterEqual(state.case, before)

    def test_reducing_a_record_cannot_raise_the_case(self):
        # Review repro 2: witness 12 + paper 4.1 read 10.1; a −2.46
        # contest RAISED it to 13.6. Partial allocation: it falls.
        state, _e = self._protected(paper=4.1)
        self.assertAlmostEqual(state.case, 10.1)
        before = state.case
        ev.contest_next(state, Quiet())
        self.assertLessEqual(state.case, before)

    def test_losing_protection_cannot_lower_the_case(self):
        state, e = self._protected()
        before = state.case
        e.morale = 3
        self.assertGreaterEqual(state.case, before)

    def test_gaining_protection_cannot_raise_the_case(self):
        state, e = self._protected()
        e.morale = 3
        before = state.case
        e.morale = 8
        self.assertLessEqual(state.case, before)

    def test_docket_effective_magnitudes_sum_to_the_meter(self):
        state, _e = self._protected(paper=4.1)
        for _ in range(4):
            state.add_case(0.5, "", kind="paper")
        view = ev.build_ledger_view(state)
        self.assertEqual(view.total, state.case)
        self.assertAlmostEqual(
            max(0.0, min(100.0, sum(line.effective for line in view.lines))),
            view.total)

    def test_floor_limited_protection_renders_as_partial(self):
        state, _e = self._protected()          # cut 5 of the halvable 6
        view = ev.build_ledger_view(state)
        line = next(li for li in view.lines if li.why == "detective talk")
        self.assertTrue(line.relieved)
        self.assertTrue(line.partial)
        self.assertAlmostEqual(line.effective, 7.0)   # 12 − 5, not 6
        con = Quiet()
        straight.show_case_file(state, con)
        self.assertIsNotNone(con.find("holds part of it down"))


# ══ The witness lifecycle (rev. 11 item 2) ════════════════════════

class TestWitnessLifecycle(unittest.TestCase):
    def _settled_out(self):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        state.add_case(10, "detective talk", kind="witness", source=e.key)
        state.add_case(20, "ballast", kind="physical")
        state.clean = 5000
        ev.settle_witness(state, e, Quiet())
        return state, e

    def test_settled_records_stop_reading_settleable(self):
        from extra_toppings.models import remediation_disposition
        state, _e = self._settled_out()
        record = state.evidence[0]
        self.assertEqual(remediation_disposition(record, state), "settled")
        view = ev.build_ledger_view(state)
        line = next(li for li in view.lines if li.why == "detective talk")
        self.assertEqual(line.disposition, "settled")

    def test_arrested_witnesses_read_beyond_reach_and_are_no_target(self):
        from extra_toppings.models import remediation_disposition
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.arrested = True
        state.add_case(10, "detective talk", kind="witness", source=e.key)
        self.assertEqual(remediation_disposition(state.evidence[0], state),
                         "beyond_reach")
        self.assertNotIn(e, ev.settle_targets(state))

    def test_settled_out_names_never_rehire_in_branch(self):
        state, e = self._settled_out()
        # Drive the real staff menu: the hire list must not offer them.
        sc = _Scripted([0, 4])    # Hire -> (list) -> Back out
        phases._staff_menu(state, sc, Streams(3).staff)
        self.assertFalse(e.hired)
        self.assertTrue(sc.applicants)
        self.assertTrue(all(e.name not in line for line in sc.applicants))

    def test_a_settled_and_hired_payload_is_refused(self):
        state, e = self._settled_out()
        payload = save.state_to_dict(state)
        for row in payload["employees"]:
            if row["key"] == e.key:
                row["hired"] = True
        with self.assertRaises(ValueError):
            save.state_from_dict(payload)

    def test_duplicate_keys_and_naive_sources_are_refused(self):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        state.add_case(10, "detective talk", kind="witness", source=e.key)
        payload = save.state_to_dict(state)
        doctored = dict(payload)
        doctored["employees"] = list(payload["employees"]) \
            + [dict(payload["employees"][0])]
        with self.assertRaises(ValueError):
            save.state_from_dict(doctored)
        doctored2 = save.state_to_dict(state)
        doctored2["evidence"][0]["source"] = "e6"   # never read in
        with self.assertRaises(ValueError):
            save.state_from_dict(doctored2)


class _Scripted(Quiet):
    """A Quiet console that also answers menus from a script and
    remembers the applicant lists it was shown."""

    def __init__(self, script):
        super().__init__()
        self.script = list(script)
        self.applicants: list = []

    def menu(self, prompt, options):
        if prompt.startswith("Applicants:"):
            self.applicants.extend(options)
            return len(options) - 1
        ans = self.script.pop(0) if self.script else len(options) - 1
        return max(0, min(ans, len(options) - 1))


# ══ The status matrix and the arrest (rev. 12 item 1) ═════════════

class TestWitnessStatusMatrix(unittest.TestCase):
    def _state_with(self, *, settled=False, arrested=False, hired=True,
                    morale=8):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.hired = hired
        e.morale = morale
        e.arrested = arrested
        if settled:
            state.branch_state.settled_witnesses.append(e.key)
            e.hired = False      # the closed lifecycle: settled-out
        return state, e

    def test_the_complete_ordered_matrix(self):
        from extra_toppings.models import witness_status
        cases = [
            (dict(settled=True), "settled"),
            (dict(settled=True, arrested=True), "settled"),
            (dict(arrested=True), "beyond_reach"),
            (dict(arrested=True, morale=9), "beyond_reach"),
            (dict(arrested=True, hired=False), "beyond_reach"),
            (dict(), "protected"),
            (dict(morale=5), "protected"),
            (dict(morale=4), "reachable"),
            (dict(hired=False), "reachable"),
            (dict(hired=False, morale=2), "reachable"),
        ]
        for kwargs, expected in cases:
            state, e = self._state_with(**kwargs)
            self.assertEqual(witness_status(state, e.key), expected,
                             msg=f"{kwargs} -> {expected}")

    def test_arrested_witnesses_receive_no_loyalty_relief(self):
        # The review's exhibit: arrested Rosa, morale 8, 20 witness +
        # 30 physical — the ledger read 40 while the docket cited
        # custody. The one authority now answers for both.
        state, e = self._state_with(arrested=True)
        state.add_case(20, "detective talk", kind="witness", source=e.key)
        state.add_case(30, "seizures", kind="physical")
        self.assertNotIn(e.key, state.dormant_sources())
        self.assertEqual(state.case, 50.0)
        view = ev.build_ledger_view(state)
        line = next(li for li in view.lines if li.why == "detective talk")
        self.assertEqual(line.disposition, "beyond_reach")
        self.assertFalse(line.relieved)

    def test_the_real_route_bust_raises_the_case_as_the_cuffs_close(self):
        # Through the actual solo-route arrest transition, not a
        # hand-set flag: the driver's protection dies with the bust.
        from extra_toppings import routes
        for seed in range(200):
            state = straight_state()
            phases.market.roll_prices(state, random.Random(7))
            rosa = next(x for x in state.employees
                        if x.name.startswith("Rosa"))
            rosa.aware = True
            rosa.morale = 8
            state.add_case(20, "detective talk", kind="witness",
                           source=rosa.key)
            state.add_case(30, "seizures", kind="physical")
            self.assertEqual(state.case, 40.0)     # protection live
            state.shop_stash = {"mushrooms": 6}
            plan = {"district": "university", "driver": rosa,
                    "ride_along": False, "cargo": {"mushrooms": 6},
                    "legit": 0, "disposal": True,
                    "origin_shop": models.HOME_SHOP_KEY,
                    "wagon_key": models.HOME_WAGON_KEY}
            departure = departed(state, plan)
            routes.resolve_route(departure, Quiet(),
                                 random.Random(seed))
            if rosa.arrested:
                break
        else:
            self.fail("no seed produced the route arrest")
        # The bust books its own physical record AND wakes hers.
        self.assertGreaterEqual(state.case, 50.0)
        self.assertNotIn(rosa.key, state.dormant_sources())


# ══ The closed-form allocator (rev. 12 item 2) ════════════════════

class TestClosedFormRelief(unittest.TestCase):
    def _protected_ledger(self, magnitudes, extra=()):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 8
        for m in magnitudes:
            state.evidence.append(Evidence(
                day=1, magnitude=m, kind="witness", why="w",
                source=e.key))
        for m in extra:
            state.evidence.append(Evidence(
                day=2, magnitude=m, kind="physical", why="p"))
        return state, e

    def test_a_legal_zero_record_is_skipped_not_a_stop(self):
        # The review's exhibit: 0.6, 0.6, 12, 8 protected read 10.6;
        # zeroing the second record ABORTED every later cut and jumped
        # the Case to 20.3. Skip means it falls to 10.3 instead.
        state, _e = self._protected_ledger([0.6, 0.6, 12.0, 8.0])
        self.assertAlmostEqual(state.case, 10.6)
        state.evidence[0 + 1].magnitude = 0.0     # the second record
        self.assertAlmostEqual(state.case, 10.3)

    def test_floor_bound_displays_are_exactly_the_floor(self):
        # Deterministic probing over legal values: whenever relief is
        # floor-bound, the display is 10.0 — never an ulp under.
        rng = random.Random(0)
        pool = [0.0, 0.1, 0.3, 0.5, 0.6, 2.0, 4.1, 8.0, 12.0, 45.7]
        found_bound = 0
        for _trial in range(300):
            mags = [rng.choice(pool) for _ in range(rng.randint(1, 6))]
            extra = [rng.choice(pool) for _ in range(rng.randint(0, 3))]
            state, _e = self._protected_ledger(mags, extra)
            raw = sum(r.magnitude for r in state.evidence)
            halvable = sum(m * 0.5 for m in mags)
            if raw > 10.0 and halvable >= raw - 10.0:
                found_bound += 1
                self.assertEqual(state.case, 10.0)
        self.assertGreater(found_bound, 20)       # the probe has teeth

    def test_generated_monotonicity_over_accepted_magnitudes(self):
        # Generated, not single examples (rev. 12): accrual never
        # lowers, reduction never raises, protection toggles never
        # move the display the wrong way — zeros included.
        rng = random.Random(1)
        pool = [0.0, 0.2, 0.5, 0.6, 1.0, 3.0, 8.0, 12.0, 20.0]
        for _trial in range(200):
            mags = [rng.choice(pool) for _ in range(rng.randint(1, 5))]
            extra = [rng.choice(pool) for _ in range(rng.randint(0, 3))]
            state, e = self._protected_ledger(mags, extra)
            before = state.case
            # (a) accrual never lowers
            state.add_case(rng.choice(pool[1:]), "new", kind="paper")
            self.assertGreaterEqual(state.case, before - 1e-9)
            # (b) reducing any record never raises
            target = rng.randrange(len(state.evidence))
            before = state.case
            state.evidence[target].magnitude *= rng.choice([0.0, 0.4])
            self.assertLessEqual(state.case, before + 1e-9)
            # (c) losing protection never lowers; regaining never
            # raises
            before = state.case
            e.morale = 3
            self.assertGreaterEqual(state.case, before - 1e-9)
            lost = state.case
            e.morale = 8
            self.assertLessEqual(state.case, lost + 1e-9)

    def test_generated_docket_sums_match_the_meter(self):
        rng = random.Random(2)
        pool = [0.0, 0.5, 0.6, 2.0, 8.0, 12.0]
        for _trial in range(100):
            mags = [rng.choice(pool) for _ in range(rng.randint(1, 5))]
            extra = [rng.choice(pool) for _ in range(rng.randint(0, 3))]
            state, _e = self._protected_ledger(mags, extra)
            view = ev.build_ledger_view(state)
            self.assertEqual(view.total, state.case)
            self.assertAlmostEqual(
                max(0.0, min(100.0,
                             sum(li.effective for li in view.lines))),
                view.total)


# ══ Persistence ═══════════════════════════════════════════════════

class TestPersistence(unittest.TestCase):
    def test_round_trip_of_remediated_state(self):
        state = straight_state()
        bs = state.branch_state
        bs.counsel_retained = True
        bs.counsel_days = 4
        bs.remediation_used = 7.5
        e3 = next(x for x in state.employees if x.key == "e3")
        e3.aware = True
        bs.settled_witnesses = ["e3"]
        bs.ad_days_left = 2
        state.add_case(10, "contested paper", kind="paper")
        state.evidence[0].contested = True
        state.evidence[0].magnitude = 4.0
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        e.morale = 7
        state.add_case(10, "detective talk", kind="witness", source=e.key)
        state.add_case(20, "ballast", kind="physical")
        loaded = save.state_from_dict(save.state_to_dict(state))
        self.assertEqual(loaded.branch_state, bs)
        self.assertTrue(loaded.evidence[0].contested)
        # The derived protection travels through the roster, not the
        # record: the loaded state halves the same source.
        self.assertEqual(loaded.dormant_sources(), state.dormant_sources())
        self.assertEqual(loaded.case, state.case)

    def _refused(self, mutate):
        state = straight_state()
        e = next(x for x in state.employees if x.name.startswith("Rosa"))
        e.aware = True
        state.add_case(10, "a record", kind="witness", source=e.key)
        payload = save.state_to_dict(state)
        mutate(payload)
        with self.assertRaises(ValueError):
            save.state_from_dict(payload)

    def test_doctored_evidence_payloads_are_refused(self):
        def negative(p):
            p["evidence"][0]["magnitude"] = -50.0
        def contested_witness(p):
            p["evidence"][0]["contested"] = True
        def unknown_kind(p):
            p["evidence"][0]["kind"] = "hearsay"
        def twin_suspicion(p):
            rec = {"day": 3, "magnitude": 2.0, "kind": "suspicion",
                   "why": ev.SUSPICION_WHY, "source": "",
                   "contested": False}
            p["evidence"].extend([dict(rec), dict(rec)])
        for mutate in (negative, contested_witness, unknown_kind,
                       twin_suspicion):
            self._refused(mutate)

    def test_cross_state_incoherence_is_refused(self):
        # Rev. 10 item 2: ledger, roster, settlements and branch state
        # must cohere as one payload.
        def phantom_witness_source(p):
            p["evidence"][0]["source"] = "e99"
        def settled_nobody(p):
            p["branch_state"]["settled_witnesses"] = ["e99"]
        def settled_never_aware(p):
            # e6 exists but was never read in.
            p["branch_state"]["settled_witnesses"] = ["e6"]
        for mutate in (phantom_witness_source, settled_nobody,
                       settled_never_aware):
            self._refused(mutate)

    def test_doctored_straight_payloads_are_refused(self):
        def too_many_runs(p):
            p["branch_state"]["disposal_runs_left"] = 5
        def bool_runs(p):
            p["branch_state"]["disposal_runs_left"] = True
        def overspent_cap(p):
            p["branch_state"]["remediation_used"] = 30.0
        def negative_cap(p):
            p["branch_state"]["remediation_used"] = -1.0
        def live_insolvency(p):
            p["branch_state"]["insolvent_days"] = 2
        def duplicate_settled(p):
            p["branch_state"]["settled_witnesses"] = ["e3", "e3"]
        def nonstring_settled(p):
            p["branch_state"]["settled_witnesses"] = [7]
        for mutate in (too_many_runs, bool_runs, overspent_cap, negative_cap,
                       live_insolvency, duplicate_settled, nonstring_settled):
            self._refused(mutate)

    def test_older_v3_payloads_load_with_machinery_defaults(self):
        state = new_state()
        state.add_case(5, "a record", kind="physical")
        payload = save.state_to_dict(state)
        for rec in payload["evidence"]:
            del rec["contested"]
        del payload["branch_state"]
        payload["branch_state"] = None
        loaded = save.state_from_dict(payload)
        self.assertFalse(loaded.evidence[0].contested)

    def test_cross_branch_mix_with_straight_fields_is_refused(self):
        state = straight_state()
        payload = save.state_to_dict(state)
        payload["branch"] = "quiet_sale"
        payload["branch_state"]["diligence_day"] = 1
        payload["branch_state"]["counsel_days"] = 3
        with self.assertRaises(ValueError):
            save.state_from_dict(payload)

    def test_validate_evidence_direct(self):
        good = [Evidence(day=1, magnitude=5.0, kind="paper", why="x")]
        validate_evidence(good)      # no raise
        with self.assertRaises(ValueError):
            validate_evidence(
                [Evidence(day=1, magnitude=True, kind="paper", why="x")])


# ══ The straight stream ═══════════════════════════════════════════

class TestStraightStream(unittest.TestCase):
    def test_reserved_and_persisted_like_brokers(self):
        streams = Streams(11)
        self.assertIn("straight", Streams.PERSISTENT)
        blob = streams.to_dict()
        self.assertIn("straight", blob["streams"])
        streams.straight.random()
        restored = Streams.from_dict(streams.to_dict())
        self.assertEqual(restored.straight.getstate(),
                         streams.straight.getstate())

    def test_missing_stream_in_old_payload_stays_fresh(self):
        streams = Streams(11)
        blob = streams.to_dict()
        del blob["streams"]["straight"]
        restored = Streams.from_dict(blob)
        self.assertEqual(restored.straight.getstate(),
                         Streams(11).straight.getstate())




class TestAccruedTruth(unittest.TestCase):
    """Rev. 16 item 1: every record carries an immutable accrual
    beside the mutable effective magnitude — remediation moves only
    the effective value, and the institutional floor's top-up is
    genuine accrual that moves both in lockstep."""

    def test_a_contest_moves_effective_and_never_the_accrual(self):
        state = straight_state()
        state.branch_state.counsel_retained = True
        state.clean = 2000
        state.add_case(20, "the register claimed too much", kind="paper")
        state.add_case(15, "prior seizure", kind="physical")
        con = Quiet()
        for _ in range(3):
            ev.counsel_nightly(state, con)
        record = state.evidence[0]
        self.assertAlmostEqual(record.magnitude, 8.0)
        self.assertAlmostEqual(record.accrued, 20.0)
        self.assertAlmostEqual(state.evidence[1].accrued, 15.0)

    def test_a_settlement_moves_effective_and_never_the_accrual(self):
        state = straight_state()
        e = next(x for x in state.employees if x.key == "e3")
        e.aware = True
        e.hired = False
        e.morale = 3
        state.add_case(8.0, f"{e.name} left knowing everything",
                       kind="witness", source=e.key)
        state.add_case(20, "ballast", kind="physical")
        state.clean = 2000
        ev.settle_witness(state, e, Quiet())
        record = state.evidence[0]
        self.assertAlmostEqual(record.magnitude, 4.0)
        self.assertAlmostEqual(record.accrued, 8.0)

    def test_the_floor_topup_is_accrual_and_moves_both(self):
        state = straight_state()
        e = next(x for x in state.employees if x.key == "e3")
        e.aware = True
        e.hired = False
        e.morale = 3
        state.add_case(8.0, f"{e.name} left knowing everything",
                       kind="witness", source=e.key)
        state.add_case(4.0, "ballast", kind="physical")
        state.clean = 2000
        # Case 12 → the halving takes it to 8, under the 10-point
        # floor; the top-up is genuine accrual, so BOTH fields move.
        ev.settle_witness(state, e, Quiet())
        record = next(r for r in state.evidence
                      if r.kind == "suspicion")
        self.assertAlmostEqual(record.magnitude, 2.0)
        self.assertAlmostEqual(record.accrued, 2.0)


if __name__ == "__main__":
    unittest.main()
