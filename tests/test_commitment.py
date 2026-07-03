"""Tests for the startup-cost bid markup and CC/CT commitment screen."""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.commitment import (
    apply_commitment_with_coal_pin,
    as_adequacy_commit,
    caiso_ra_mustoffer_min_gen,
    compute_commitment,
    compute_monthly_markup,
    find_runs,
    reserve_adequacy_commit,
)
from market_sim.model.dispatch import solve_dispatch

_CONFIG = ScenarioConfig()

# f-class commitment params (heat rate 6.5-7.5): min_run 8h, min_down 6h,
# startup 48.6 $/MW. IRR hurdle 7% -> 48.6 x 1.07 = 52.0 $/MW.


def _single_cc(heat_rate: float = 7.0, hours: int = 24):
    """Return a one-generator gas_cc fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CC",
        name="CC",
        zone="z",
        fuel_type="gas_cc",
        pmax_mw=300.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
    )
    return [gen], generators_to_fleet_arrays([gen], ["z"], hours=hours)


def _single_ct(heat_rate: float = 10.5, hours: int = 24):
    """Return a one-generator gas_ct fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="CT",
        name="CT",
        zone="z",
        fuel_type="gas_ct",
        pmax_mw=200.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
    )
    return [gen], generators_to_fleet_arrays([gen], ["z"], hours=hours)


def _single_coal(heat_rate: float = 10.0, hours: int = 24):
    """Return a one-generator coal fleet (list + FleetArrays)."""
    gen = Generator(
        unit_id="COAL",
        name="COAL",
        zone="z",
        fuel_type="coal",
        pmax_mw=500.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
    )
    return [gen], generators_to_fleet_arrays([gen], ["z"], hours=hours)


class TestReserveAdequacyCommit(unittest.TestCase):
    """Path B: the downstate spinning-reserve adequacy commit."""

    def _two_ct(self, hours=4):
        gens = [
            Generator(
                unit_id=f"CT{i}",
                name=f"CT{i}",
                zone="NYC",
                fuel_type="gas_ct",
                pmax_mw=200.0,
                pmin_mw=20.0,
                heat_rate=10.5,
                eford=0.0,
            )
            for i in range(2)
        ]
        return gens, generators_to_fleet_arrays(gens, ["NYC"], hours=hours)

    def test_commits_until_requirement_covered(self):
        gens, fa = self._two_ct()
        committed = np.zeros((2, 4), dtype=bool)  # both decommitted
        spin = np.array([True, True])
        # Requirement 150 MW < one CT's 200 MW pmax -> exactly one CT committed.
        out = reserve_adequacy_commit(committed, fa, gens, spin, 150.0)
        per_hour_committed = out.sum(axis=0)
        np.testing.assert_array_equal(per_hour_committed, [1, 1, 1, 1])
        # Committed headroom (200) covers the 150 requirement every hour.
        headroom = (fa.pmax[:, None] * fa.availability * out).sum(axis=0)
        self.assertTrue((headroom >= 150.0).all())

    def test_commits_both_when_one_insufficient(self):
        gens, fa = self._two_ct()
        committed = np.zeros((2, 4), dtype=bool)
        out = reserve_adequacy_commit(
            committed, fa, gens, np.array([True, True]), 350.0
        )
        np.testing.assert_array_equal(out.sum(axis=0), [2, 2, 2, 2])

    def test_noop_when_requirement_zero_or_no_eligible(self):
        gens, fa = self._two_ct()
        committed = np.zeros((2, 4), dtype=bool)
        np.testing.assert_array_equal(
            reserve_adequacy_commit(committed, fa, gens, np.array([True, True]), 0.0),
            committed,
        )
        np.testing.assert_array_equal(
            reserve_adequacy_commit(
                committed, fa, gens, np.array([False, False]), 150.0
            ),
            committed,
        )

    def test_preserves_already_committed(self):
        gens, fa = self._two_ct()
        committed = np.ones((2, 4), dtype=bool)  # both already on
        out = reserve_adequacy_commit(
            committed, fa, gens, np.array([True, True]), 150.0
        )
        np.testing.assert_array_equal(out, committed)  # nothing to add

    def test_as_adequacy_floor_covers_net_headroom(self):
        # Two 200-MW CTs; one committed running 180 MW (net headroom 20), the other
        # decommitted. A 150-MW AS requirement is not met by the running unit's 20
        # MW headroom, so the floor commits the idle unit (200 MW net headroom).
        gens, fa = self._two_ct()
        committed = np.array([[True] * 4, [False] * 4])
        p1 = np.zeros((2, 4))
        p1[0, :] = 180.0  # unit 0 runs hot -> only 20 MW headroom
        hr_elig = np.array([[True, True]])  # one row, both eligible
        hr_prod = np.array([[True]])  # one row bounds the one product
        req = np.full((1, 4), 150.0)  # (n_prod, T)
        out = as_adequacy_commit(committed, fa, gens, hr_elig, hr_prod, req, p1)
        self.assertTrue(out[1].all())  # idle unit committed to cover the AS req
        net_hr = np.maximum(fa.pmax[:, None] * fa.availability - p1, 0.0)
        cov = (net_hr * out).sum(axis=0)
        self.assertTrue((cov >= 150.0).all())

    def test_as_adequacy_floor_tier_aware_commits_from_rows_own_set(self):
        # Fast row eligible = unit 0 only (a CC); all row eligible = both. Fast
        # product req 150 must be covered from the FAST set (unit 0), not the cheap
        # peaker unit 1 — so unit 0 is committed even though unit 1 has more room.
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=200.0,
                pmin_mw=0.0,
                heat_rate=7.0,
                eford=0.0,
            ),
            Generator(
                unit_id="CT",
                name="CT",
                zone="Z",
                fuel_type="gas_ct",
                pmax_mw=300.0,
                pmin_mw=0.0,
                heat_rate=10.5,
                eford=0.0,
            ),
        ]
        fa = generators_to_fleet_arrays(gens, ["Z"], hours=4)
        committed = np.zeros((2, 4), dtype=bool)
        p1 = np.zeros((2, 4))
        hr_elig = np.array([[True, False], [True, True]])  # fast row: CC only
        hr_prod = np.array([[True, False], [True, True]])  # fast bounds prod 0
        req = np.zeros((2, 4))
        req[0, :] = 150.0  # fast product
        out = as_adequacy_commit(committed, fa, gens, hr_elig, hr_prod, req, p1)
        self.assertTrue(out[0].all())  # the fast-eligible CC is committed

    def test_as_adequacy_floor_noop_when_already_covered(self):
        # When committed net headroom already covers the requirement, nothing is
        # added — the floor never strips a genuinely-short hour's scarcity.
        gens, fa = self._two_ct()
        committed = np.array([[True] * 4, [False] * 4])
        p1 = np.zeros((2, 4))  # unit 0 idle -> 200 MW net headroom >= 150
        hr_elig = np.array([[True, True]])
        hr_prod = np.array([[True]])
        req = np.full((1, 4), 150.0)
        out = as_adequacy_commit(committed, fa, gens, hr_elig, hr_prod, req, p1)
        np.testing.assert_array_equal(out, committed)


class TestCaisoRaMustofferMinGen(unittest.TestCase):
    """The CAISO RA must-offer min-load bridge floor."""

    def _cc(self, hours, dispatch, heat_rate=7.0, plant_group="CC_REGULAR"):
        """One merchant CC, dispatched per ``dispatch`` (length ``hours``)."""
        gen = Generator(
            unit_id="CC",
            name="CC",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=heat_rate,
            eford=0.0,
            plant_group=plant_group,
        )
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        return [gen], fa, np.asarray(dispatch, dtype=float).reshape(1, hours)

    def test_bridges_short_midday_gap(self):
        # f-class CC (hr 7.0): min_down 6h. Run 6-9, idle 10-12 (gap 3 < 6),
        # run 13-18 -> the unit must stay online at min-load across 10-12.
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.40)
        expected = np.zeros(24)
        expected[10:13] = 0.40 * 300.0  # 120 MW across the bridged gap
        np.testing.assert_allclose(floor[0], expected)

    def test_no_bridge_for_long_gap(self):
        # Gap 10-19 is 9h >= 6h min-down: the unit can cycle off, no floor.
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[19:24] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.40)
        np.testing.assert_allclose(floor[0], np.zeros(24))

    def test_floor_scales_with_availability(self):
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        fa.availability[0, 11] = 0.5  # a derate mid-gap relaxes the floor there
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.40)
        self.assertAlmostEqual(floor[0, 10], 120.0)
        self.assertAlmostEqual(floor[0, 11], 60.0)
        self.assertAlmostEqual(floor[0, 12], 120.0)

    def test_ct_never_bridges(self):
        # CT min-down is 1h, so no integer gap is shorter than min-down.
        gen = Generator(
            unit_id="CT",
            name="CT",
            zone="z",
            fuel_type="gas_ct",
            pmax_mw=200.0,
            pmin_mw=0.0,
            heat_rate=10.5,
            eford=0.0,
            plant_group="CT_PEAKER",
        )
        fa = generators_to_fleet_arrays([gen], ["z"], hours=24)
        disp = np.zeros((1, 24))
        disp[0, 6:9] = 200.0
        disp[0, 11:15] = 200.0
        floor = caiso_ra_mustoffer_min_gen(disp, fa, [gen], min_load_frac=0.40)
        np.testing.assert_allclose(floor[0], np.zeros(24))

    def test_skips_cogens(self):
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp, plant_group="CC_CHP")
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.40)
        np.testing.assert_allclose(floor[0], np.zeros(24))

    def test_noop_when_frac_nonpositive(self):
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.0)
        np.testing.assert_allclose(floor, np.zeros((1, 24)))


class TestCaisoRaStartupBridge(unittest.TestCase):
    """The startup-cost-aware extension of the RA must-offer bridge (caiso-44).

    Extends :class:`TestCaisoRaMustofferMinGen`: a gap LONGER than min-down is
    bridged only when the restart is uneconomic per
    ``startup_per_mw > (MC - LMP_gap) * min_load_frac * gap_hours``.
    """

    def _cc(self, hours, dispatch, heat_rate=7.0, plant_group="CC_REGULAR"):
        """One merchant CC, dispatched per ``dispatch`` (length ``hours``)."""
        gen = Generator(
            unit_id="CC",
            name="CC",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=heat_rate,
            eford=0.0,
            plant_group=plant_group,
        )
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        return [gen], fa, np.asarray(dispatch, dtype=float).reshape(1, hours)

    # f-class CC (hr 7.0): startup 48.6 $/MW, min_down 6h. Run 6-9, idle 10-17
    # (gap 8h >= 6h min-down), run 18-23. The gap is a legal cold cycle, so the
    # plain bridge leaves it cold; the startup branch decides on economics.
    def _long_gap_dispatch(self):
        disp = np.zeros(24)
        disp[6:10] = 300.0  # first run, end (exclusive) = 10
        disp[18:24] = 300.0  # second run, start = 18  ->  gap hours 10..17 = 8h
        return disp

    def test_uneconomic_long_gap_is_bridged(self):
        # MC ~ LMP (gas near-marginal): RHS = (30-25)*0.40*8 = 16 < 48.6 startup
        # -> cheaper to hold at min-load than restart, so the gap IS bridged.
        gens, fa, p1 = self._cc(24, self._long_gap_dispatch())
        mc = np.full((1, 24), 30.0)
        lmp = np.full((1, 24), 25.0)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
        )
        expected = np.zeros(24)
        expected[10:18] = 0.40 * 300.0  # 120 MW held across the bridged gap
        np.testing.assert_allclose(floor[0], expected)

    def test_economic_long_gap_is_not_bridged(self):
        # MC >> LMP (gas deeply out-of-merit midday): RHS = (60-10)*0.40*8 = 160
        # > 48.6 startup -> cheaper to cycle off and re-pay the start, no floor.
        gens, fa, p1 = self._cc(24, self._long_gap_dispatch())
        mc = np.full((1, 24), 60.0)
        lmp = np.full((1, 24), 10.0)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
        )
        np.testing.assert_allclose(floor[0], np.zeros(24))

    def test_off_by_default_leaves_long_gap_cold(self):
        # startup_bridge off (default) reproduces the physical-only bridge: the
        # 8h gap >= min-down is never floored regardless of economics.
        gens, fa, p1 = self._cc(24, self._long_gap_dispatch())
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.40)
        np.testing.assert_allclose(floor[0], np.zeros(24))

    def test_short_gap_still_bridged_with_startup_on(self):
        # A gap SHORTER than min-down stays a physical bridge even with the
        # startup branch on and economics that would otherwise skip it.
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0  # gap 10..12 = 3h < 6h min-down
        gens, fa, p1 = self._cc(24, disp)
        mc = np.full((1, 24), 60.0)  # economics say "cycle", but gap < min-down
        lmp = np.full((1, 24), 10.0)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
        )
        expected = np.zeros(24)
        expected[10:13] = 0.40 * 300.0
        np.testing.assert_allclose(floor[0], expected)

    def test_requires_prices_when_enabled(self):
        gens, fa, p1 = self._cc(24, self._long_gap_dispatch())
        with self.assertRaises(ValueError):
            caiso_ra_mustoffer_min_gen(
                p1, fa, gens, min_load_frac=0.40, startup_bridge=True
            )

    def test_binned_fleet_floors_committed_tranche_only(self):
        # CAISO per-plant CAMPD tranches carry min_run/min_down = 0, so the bridge
        # must resolve min-down from the class table and floor ONLY the base
        # (committed, startup>0) tranche at min_load_frac x PLANT pmax — never the
        # incremental econ tranche (startup=0), which would pad midday gas.
        def bin_gen(suffix, pmax, startup, hr=7.0):
            return Generator(
                unit_id=f"CC_REGULAR_z_p99_{suffix}",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=pmax,
                pmin_mw=0.0,
                heat_rate=hr,
                eford=0.0,
                plant_group="CC_REGULAR",
                is_campd_bin=True,
                startup_cost_per_mw=startup,
            )

        # One plant: committed (200 MW, startup 50) + econ (300 MW, startup 0).
        committed = bin_gen("committed", 200.0, 50.0)
        econ = bin_gen("econc00", 300.0, 0.0)
        gens = [committed, econ]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=24)
        # Both tranches run 6-9 and 18-23, cold across the 8h belly 10-17
        # (> f-class 6h min-down). Uneconomic cycle (MC ~ LMP).
        disp = np.zeros((2, 24))
        disp[0, 6:10] = 200.0
        disp[0, 18:24] = 200.0
        disp[1, 6:10] = 300.0
        disp[1, 18:24] = 300.0
        mc = np.full((2, 24), 35.0)
        lmp = np.full((1, 24), 33.0)
        floor = caiso_ra_mustoffer_min_gen(
            disp,
            fa,
            gens,
            min_load_frac=0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
        )
        # Committed tranche floored at min_load_frac x PLANT pmax (0.40 x 500 =
        # 200), clipped to its own 200 MW capacity -> 200 MW across the belly.
        np.testing.assert_allclose(floor[0, 10:18], 200.0)
        np.testing.assert_allclose(floor[0, :10], 0.0)
        # Econ tranche (startup 0) is never floored.
        np.testing.assert_allclose(floor[1], np.zeros(24))


class TestCaisoRaBridgeDecommit(unittest.TestCase):
    """The solar-proportional / seasonal decommitment control (caiso-48).

    Extends :class:`TestCaisoRaStartupBridge`: with ``bridge_decommit`` on,
    (1) an economic bridge is bounded to the 24-h day-ahead commitment horizon,
    and (2) gap hours where the candidate floors exceed the P1 import/export
    absorption reprice to ``surplus_floor_value`` and uneconomic bridges
    decommit cheapest-startup-first (RUC order).
    """

    def _fleet(self, hours, import_mw=0.0, export_cap=0.0):
        """Two merchant CCs (f-class + h-class) plus optional intertie rows.

        Returns ``(gens, fa, p1)`` with both CCs running 6-9 and 18-23, cold
        across the 8-h belly 10-17 (>= min-down, <= the 24-h DA horizon). The
        import row dispatches ``import_mw`` flat; the export sink (capacity
        ``export_cap``) sits unused, so its full capacity is absorption
        headroom.
        """
        gens = [
            Generator(
                unit_id="CC_F",
                name="CC_F",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                pmin_mw=0.0,
                heat_rate=7.0,  # f-class: startup 48.6 $/MW, min_down 6h
                eford=0.0,
                plant_group="CC_REGULAR",
            ),
            Generator(
                unit_id="CC_H",
                name="CC_H",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                pmin_mw=0.0,
                heat_rate=6.4,  # h-class: startup 63.8 $/MW, min_down 8h
                eford=0.0,
                plant_group="CC_REGULAR",
            ),
            Generator(
                unit_id="ext_import",
                name="ext_import",
                zone="z",
                fuel_type="import",
                pmax_mw=1000.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="ext_export",
                name="ext_export",
                zone="z",
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-export_cap if export_cap else 0.0,
                heat_rate=0.0,
                eford=0.0,
            ),
        ]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=hours)
        p1 = np.zeros((4, hours))
        for g in (0, 1):
            p1[g, 6:10] = 300.0
            p1[g, 18:24] = 300.0
        p1[2, :] = import_mw
        return gens, fa, p1

    # MC 30 vs LMP 25 (gas near-marginal): plain hold cost (30-25)*0.40*8 = 16
    # < both startups, so WITHOUT the surplus screen both 8-h belly gaps bridge.
    def _mc_lmp(self, hours, n_gen=4):
        return np.full((n_gen, hours), 30.0), np.full((1, hours), 25.0)

    def test_off_reproduces_startup_bridge(self):
        # bridge_decommit off: both CCs bridge the belly even with ZERO
        # absorption (the caiso-45 behaviour, byte-identical).
        gens, fa, p1 = self._fleet(24)
        mc, lmp = self._mc_lmp(24)
        floor = caiso_ra_mustoffer_min_gen(
            p1, fa, gens, 0.40, p1_prices=lmp, base_mc=mc, startup_bridge=True
        )
        np.testing.assert_allclose(floor[0, 10:18], 120.0)
        np.testing.assert_allclose(floor[1, 10:18], 120.0)

    def test_surplus_decommits_ruc_order(self):
        # Absorption 200 MW (imports that can back down) < candidate floors
        # 240 MW -> surplus. RUC order: the cheap-start f-class (48.6) is
        # checked first at full surplus — repriced hold (30-(-20))*0.40*8 =
        # 160 > 48.6 -> decommitted. Its removal drops the floors to 120 <=
        # 200, so the dear-start h-class sees NO surplus and holds (16 < 63.8).
        gens, fa, p1 = self._fleet(24, import_mw=200.0)
        mc, lmp = self._mc_lmp(24)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
            bridge_decommit=True,
            surplus_floor_value=-20.0,
        )
        np.testing.assert_allclose(floor[0], np.zeros(24))  # f-class cycled off
        np.testing.assert_allclose(floor[1, 10:18], 120.0)  # h-class holds

    def test_deep_surplus_decommits_all(self):
        # Zero absorption: even after the f-class decommits the h-class floors
        # still exceed absorption, the gap stays repriced at the renewable
        # keep-running offer, and 160 > 63.8 cycles it off too.
        gens, fa, p1 = self._fleet(24)
        mc, lmp = self._mc_lmp(24)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
            bridge_decommit=True,
            surplus_floor_value=-20.0,
        )
        np.testing.assert_allclose(floor, np.zeros((4, 24)))

    def test_export_headroom_is_absorption(self):
        # An unused 300-MW export sink absorbs the full 240 MW of candidate
        # floors -> no surplus, both bridges hold at the plain-LMP economics.
        gens, fa, p1 = self._fleet(24, export_cap=300.0)
        mc, lmp = self._mc_lmp(24)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
            bridge_decommit=True,
            surplus_floor_value=-20.0,
        )
        np.testing.assert_allclose(floor[0, 10:18], 120.0)
        np.testing.assert_allclose(floor[1, 10:18], 120.0)

    def test_da_horizon_caps_economic_bridge(self):
        # A 30-h idle spell (> one 24-h DAM operating day) is a next-day
        # decommit/re-offer decision: never bridged with the control on, even
        # with abundant absorption — the SEASONAL decommitment. With the
        # control off the plain restart inequality bridges it (16*30/8 = 60 vs
        # ... (30-25)*0.40*30 = 60 -> use a slightly cheaper hold: LMP 26 ->
        # (30-26)*0.40*30 = 48 < 48.6, bridged).
        hours = 60
        gens, fa, p1 = self._fleet(hours, import_mw=2000.0)
        p1[:2, :] = 0.0
        p1[0, 6:10] = 300.0
        p1[0, 40:46] = 300.0  # gap 10..39 = 30 h
        mc = np.full((4, hours), 30.0)
        lmp = np.full((1, hours), 26.0)
        floor_off = caiso_ra_mustoffer_min_gen(
            p1, fa, gens, 0.40, p1_prices=lmp, base_mc=mc, startup_bridge=True
        )
        np.testing.assert_allclose(floor_off[0, 10:40], 120.0)  # padded 30 h
        floor_on = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
            bridge_decommit=True,
            surplus_floor_value=-20.0,
        )
        np.testing.assert_allclose(floor_on[0], np.zeros(hours))

    def test_physical_bridge_survives_decommit(self):
        # A gap SHORTER than min-down is a physical restart bar — it holds
        # through the surplus screen regardless of economics.
        gens, fa, p1 = self._fleet(24)
        p1[:2, :] = 0.0
        p1[0, 6:10] = 300.0
        p1[0, 13:19] = 300.0  # gap 10..12 = 3 h < 6 h f-class min-down
        mc, lmp = self._mc_lmp(24)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            0.40,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=True,
            bridge_decommit=True,
            surplus_floor_value=-20.0,
        )
        np.testing.assert_allclose(floor[0, 10:13], 120.0)


class TestFindRuns(unittest.TestCase):
    """Tests for the consecutive-True segment finder."""

    def test_empty_and_all_false(self):
        self.assertEqual(find_runs(np.array([], dtype=bool)), [])
        self.assertEqual(find_runs(np.zeros(5, dtype=bool)), [])

    def test_segments_have_exclusive_end(self):
        mask = np.array([0, 1, 1, 1, 0, 0, 1, 1], dtype=bool)
        self.assertEqual(find_runs(mask), [(1, 4), (6, 8)])

    def test_full_run(self):
        self.assertEqual(find_runs(np.ones(4, dtype=bool)), [(0, 4)])


class TestComputeCommitment(unittest.TestCase):
    """The commitment screen on gas CC units: margin = price - base MC."""

    def test_flat_price_above_mc_commits_all_hours(self):
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 50.0)
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertEqual(committed.shape, (1, 24))
        self.assertTrue(committed.all())

    def test_price_below_mc_commits_no_hours(self):
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_long_spike_commits_those_hours(self):
        # A 12-hour profitable spike clears both the min-run (8h) and the
        # startup-cost filters, so exactly those hours commit.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 6:18] = 50.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 6:18].all())
        self.assertFalse(committed[0, :6].any())
        self.assertFalse(committed[0, 18:].any())

    def test_short_spike_too_short_to_commit(self):
        # A 3-hour spike is below the 8-hour min-run threshold.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 10:13] = 50.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_spike_revenue_below_startup_cost_rejected(self):
        # A 10-hour run clears the min-run filter but its total margin
        # (4 $/MWh x 10h = 40) falls short of the 52.0 $/MW IRR hurdle.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 34.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

    def test_runs_within_min_down_are_merged(self):
        # Two accepted 8-hour runs separated by a 3-hour gap (< 6h min-down)
        # merge into one committed block that bridges the gap.
        gens, arrays = _single_cc(hours=30)
        base_mc = np.full((1, 30), 30.0)
        prices = np.full((1, 30), 20.0)
        prices[0, 0:8] = 40.0
        prices[0, 11:19] = 40.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, :19].all())
        self.assertFalse(committed[0, 19:].any())

    def test_irr_hurdle_rejects_run_below_startup_cost_plus_irr(self):
        # f-class CC: startup 48.6 $/MW, IRR 7% -> hurdle 52.0 $/MW.
        # A 10-hour run at 5 $/MWh margin totals 50 -- above breakeven
        # (48.6) but below the IRR hurdle, so it is rejected.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # margin 5 x 10h = 50 total
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(committed.any())

        # Lift the margin to 6 $/MWh (total 60 > 52) and the run commits.
        prices[0, 5:15] = 36.0
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 5:15].all())

    def test_ct_commits_for_a_single_profitable_hour(self):
        # CTs have min_run 1h: one high-margin hour justifies a start.
        gens, arrays = _single_ct(heat_rate=10.5, hours=24)
        base_mc = np.full((1, 24), 80.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 12] = 180.0  # margin 100 for one hour
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 12])
        self.assertEqual(int(committed.sum()), 1)

    def test_margin_uses_base_mc_not_bid_mc(self):
        # The same prices screened against base MC commit the run, but
        # screened against a higher bid MC (base + markup) they do not:
        # the margin must use the generator's actual cost.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        prices = np.full((1, 24), 50.0)
        base_mc = np.full((1, 24), 45.0)  # margin 5 x 24h = 120 > 52
        bid_mc = np.full((1, 24), 50.0)  # margin 0 -> nothing commits

        committed_base = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        committed_bid = compute_commitment(prices, bid_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed_base.all())
        self.assertFalse(committed_bid.any())


class TestASAwareCommitment(unittest.TestCase):
    """AS revenue keeps energy-marginal units committed (AS-aware commitment)."""

    def test_none_as_value_is_byte_identical(self):
        # Passing as_value=None reproduces the energy-only screen exactly.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # 10-h run, margin 5x10=50 < 52 hurdle -> reject
        baseline = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        explicit_none = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=None
        )
        self.assertFalse(baseline.any())
        np.testing.assert_array_equal(baseline, explicit_none)

    def test_as_value_lifts_run_over_hurdle(self):
        # Energy margin alone (5x10=50) is below the 52.0 IRR hurdle, so the run
        # is rejected. Adding AS revenue to those hours clears the hurdle.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 35.0  # margin 5 x 10h = 50
        rejected = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertFalse(rejected.any())

        as_value = np.zeros((1, 24))
        as_value[0, 5:15] = 1.0  # +10 AS -> 60 > 52 hurdle
        committed = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=as_value
        )
        self.assertTrue(committed[0, 5:15].all())

    def test_as_value_extends_online_unit_into_as_hours(self):
        # A unit online for energy (one in-merit run) has its commitment EXTENDED
        # into the adjacent AS-priced hours it earns reserve.
        gens, arrays = _single_ct(heat_rate=10.5, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 8:10] = 200.0  # a short, very profitable energy run (CT min_run 1)
        energy_only = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(energy_only[0, 8:10].all())
        self.assertFalse(energy_only[0, 10:14].any())

        as_value = np.zeros((1, 24))
        as_value[0, 8:14] = 100.0  # AS priced through hour 13
        committed = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=as_value
        )
        # The online unit now stays committed through its AS-earning hours.
        self.assertTrue(committed[0, 8:14].all())

    def test_as_value_does_not_resurrect_a_cold_unit(self):
        # A unit the LP never runs for energy (no in-merit hour) is NOT brought
        # online by its idle headroom's AS credit — it is the phantom headroom the
        # screen must drop out of the reserve pool.
        gens, arrays = _single_cc(hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)  # energy margin always negative -> cold
        as_value = np.zeros((1, 24))
        as_value[0, 8:20] = 5000.0  # huge idle AS credit
        committed = compute_commitment(
            prices, base_mc, gens, arrays, _CONFIG, as_value=as_value
        )
        self.assertFalse(committed.any())


class TestStorageWeightedCommitment(unittest.TestCase):
    """The commitment hurdle discounts margin in storage net-charging hours."""

    def _scenario(self):
        # f-class CC, hurdle 52.0. A 10-hour run at 6 $/MWh margin totals 60,
        # which clears the hurdle when unweighted (see the IRR-hurdle test).
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:15] = 36.0
        demand = np.full((1, 24), 1000.0)
        return gens, arrays, base_mc, prices, demand

    def test_net_charging_discounts_hurdle_and_rejects_run(self):
        # Storage charges 200 MW into a 1000 MW zone during the run, so the
        # weight is 0.8: weighted margin 60 x 0.8 = 48 < 52 -> rejected.
        gens, arrays, base_mc, prices, demand = self._scenario()
        charge = np.zeros((1, 24))
        charge[0, 5:15] = 200.0
        committed = compute_commitment(
            prices,
            base_mc,
            gens,
            arrays,
            _CONFIG,
            storage_charge=charge,
            storage_discharge=np.zeros((1, 24)),
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        self.assertFalse(committed.any())

    def test_net_discharging_keeps_full_weight_and_commits(self):
        # Storage discharging keeps weight 1.0 (storage and thermal are
        # complements at the peak): the 60-total run still clears 52.
        gens, arrays, base_mc, prices, demand = self._scenario()
        discharge = np.zeros((1, 24))
        discharge[0, 5:15] = 200.0
        committed = compute_commitment(
            prices,
            base_mc,
            gens,
            arrays,
            _CONFIG,
            storage_charge=np.zeros((1, 24)),
            storage_discharge=discharge,
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        self.assertTrue(committed[0, 5:15].all())

    def test_zero_weight_disables_storage_discount(self):
        # commitment_storage_weight = 0 recovers the plain margin sum even
        # with heavy net charging: the run commits.
        gens, arrays, base_mc, prices, demand = self._scenario()
        charge = np.zeros((1, 24))
        charge[0, 5:15] = 200.0
        config = ScenarioConfig(commitment_storage_weight=0.0)
        committed = compute_commitment(
            prices,
            base_mc,
            gens,
            arrays,
            config,
            storage_charge=charge,
            storage_discharge=np.zeros((1, 24)),
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        self.assertTrue(committed[0, 5:15].all())

    def test_omitted_storage_inputs_are_a_noop(self):
        # Without the storage arguments the screen is unchanged: the run
        # clears the hurdle exactly as in the non-storage IRR-hurdle test.
        gens, arrays, base_mc, prices, _ = self._scenario()
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)
        self.assertTrue(committed[0, 5:15].all())

    def _trough_scenario(self):
        # A 12-hour positive-margin run (hours 5-16) with a 4-hour storage
        # net-charging trough in its middle (hours 9-12). Net charge there
        # is 60% of zone demand, so the storage weight is 0.4.
        gens, arrays = _single_cc(heat_rate=7.0, hours=24)
        base_mc = np.full((1, 24), 30.0)
        prices = np.full((1, 24), 20.0)
        prices[0, 5:17] = 50.0
        demand = np.full((1, 24), 1000.0)
        charge = np.zeros((1, 24))
        charge[0, 9:13] = 600.0
        kwargs = dict(
            storage_charge=charge,
            storage_discharge=np.zeros((1, 24)),
            storage_zone_idx=np.array([0]),
            demand=demand,
        )
        return gens, arrays, base_mc, prices, kwargs

    def test_in_merit_floor_breaks_a_run_through_a_charging_trough(self):
        # Floor off: the 12-hour run commits whole. Floor on: the trough
        # drops out and the two 4-hour pieces each fall short of the
        # 8-hour min run, so nothing commits.
        gens, arrays, base_mc, prices, kwargs = self._trough_scenario()
        off = compute_commitment(prices, base_mc, gens, arrays, _CONFIG, **kwargs)
        self.assertTrue(off[0, 5:17].all())

        cfg = ScenarioConfig(commitment_storage_in_merit_floor=0.5)
        on = compute_commitment(prices, base_mc, gens, arrays, cfg, **kwargs)
        self.assertFalse(on.any())

    def test_in_merit_floor_leaves_shallow_charging_untouched(self):
        # A shallow trough (net charge 20% of demand -> weight 0.8) stays
        # above the 0.5 floor, so the run is not broken and still commits.
        gens, arrays, base_mc, prices, kwargs = self._trough_scenario()
        kwargs["storage_charge"] = kwargs["storage_charge"].copy()
        kwargs["storage_charge"][0, 9:13] = 200.0
        cfg = ScenarioConfig(commitment_storage_in_merit_floor=0.5)
        committed = compute_commitment(prices, base_mc, gens, arrays, cfg, **kwargs)
        self.assertTrue(committed[0, 5:17].all())


class TestCoalAndNuclearAlwaysCommitted(unittest.TestCase):
    """Coal, nuclear and non-thermal fuels are never commitment-screened."""

    def test_coal_and_nuclear_stay_committed_at_deep_loss(self):
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                heat_rate=7.0,
                eford=0.0,
            ),
            Generator(
                unit_id="COAL",
                name="COAL",
                zone="z",
                fuel_type="coal",
                pmax_mw=500.0,
                heat_rate=10.0,
                eford=0.0,
            ),
            Generator(
                unit_id="NUC",
                name="NUC",
                zone="z",
                fuel_type="nuclear",
                pmax_mw=1000.0,
                heat_rate=10.0,
                eford=0.0,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=24)
        # Price far below every thermal MC.
        base_mc = np.array(
            [
                np.full(24, 60.0),
                np.full(24, 55.0),
                np.full(24, 10.0),
            ]
        )
        prices = np.full((1, 24), 5.0)
        committed = compute_commitment(prices, base_mc, gens, arrays, _CONFIG)

        self.assertFalse(committed[0].any())  # CC screened off
        self.assertTrue(committed[1].all())  # coal always committed
        self.assertTrue(committed[2].all())  # nuclear always committed


class TestComputeMonthlyMarkup(unittest.TestCase):
    """The monthly startup-amortization markup from P0 run lengths."""

    def test_coal_and_nuclear_get_zero_markup(self):
        gens, arrays = _single_coal(hours=744)
        dispatch = np.full((1, 744), 300.0)
        markup = compute_monthly_markup(gens, arrays, dispatch, 744)
        self.assertEqual(markup.shape, (1, 744))
        self.assertTrue((markup == 0.0).all())

    def test_markup_equals_startup_over_run_length(self):
        # f-class CC, startup 48.6 $/MW. A January of uninterrupted running
        # amortizes the startup over the whole 744-hour run.
        gens, arrays = _single_cc(heat_rate=7.0, hours=744)
        dispatch = np.full((1, 744), 200.0)  # always on (> 5% of 300 MW)
        markup = compute_monthly_markup(gens, arrays, dispatch, 744)
        np.testing.assert_allclose(markup[0], 48.6 / 744.0)

    def test_shoulder_month_markup_exceeds_summer(self):
        # Two-month horizon (Jan 744h + Feb 672h). Month 1 runs continuously
        # (long run, low markup); month 2 runs in 4-hour bursts (short runs,
        # high markup).
        hours = 744 + 672
        gens, arrays = _single_cc(heat_rate=7.0, hours=hours)
        dispatch = np.zeros((1, hours))
        dispatch[0, :744] = 200.0  # month 1: continuous
        for start in range(744, hours, 8):
            dispatch[0, start : start + 4] = 200.0  # month 2: 4h on / 4h off
        markup = compute_monthly_markup(gens, arrays, dispatch, hours)

        summer = markup[0, 0]
        shoulder = markup[0, 744]
        self.assertLess(summer, shoulder)
        np.testing.assert_allclose(shoulder, 48.6 / 4.0)

    def test_idle_month_amortizes_over_unit_run(self):
        # A month with no running hours has no run to amortize over; the
        # markup falls back to startup / 1.0 rather than dividing by zero.
        gens, arrays = _single_cc(heat_rate=7.0, hours=744)
        dispatch = np.zeros((1, 744))
        markup = compute_monthly_markup(gens, arrays, dispatch, 744)
        np.testing.assert_allclose(markup[0], 48.6)


class TestApplyCommitmentWithCoalPin(unittest.TestCase):
    """Tests for applying the commitment screen to the fleet arrays."""

    def test_cc_availability_zeroed_only_where_decommitted(self):
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                heat_rate=7.0,
                eford=0.05,
            ),
            Generator(
                unit_id="CT",
                name="CT",
                zone="z",
                fuel_type="gas_ct",
                pmax_mw=200.0,
                heat_rate=10.5,
                eford=0.05,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=10)
        committed = np.ones((2, 10), dtype=bool)
        committed[0, 3:6] = False
        p1_dispatch = np.zeros((2, 10))

        out = apply_commitment_with_coal_pin(arrays, committed, p1_dispatch, gens)
        self.assertTrue((out.availability[0, 3:6] == 0.0).all())
        np.testing.assert_array_equal(
            out.availability[0, :3], arrays.availability[0, :3]
        )
        np.testing.assert_array_equal(out.availability[1], arrays.availability[1])
        # The input arrays must not be mutated in place.
        self.assertTrue((arrays.availability[0, 3:6] != 0.0).all())

    def test_coal_availability_pinned_to_pass1_dispatch(self):
        coal = Generator(
            unit_id="COAL",
            name="COAL",
            zone="z",
            fuel_type="coal",
            pmax_mw=400.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            eford=0.0,
        )
        arrays = generators_to_fleet_arrays([coal], ["z"], hours=4)
        committed = np.ones((1, 4), dtype=bool)
        p1_dispatch = np.array([[400.0, 200.0, 0.0, 100.0]])

        out = apply_commitment_with_coal_pin(arrays, committed, p1_dispatch, [coal])
        # availability = clip(P1 / Pmax), with a tiny floor for the zero hour.
        np.testing.assert_allclose(out.availability[0], [1.0, 0.5, 1e-6, 0.25])

    def test_nuclear_pmin_preserved(self):
        # Nuclear is not screened; its must-run Pmin survives into P2.
        nuc = Generator(
            unit_id="NUC",
            name="NUC",
            zone="z",
            fuel_type="nuclear",
            pmax_mw=1000.0,
            pmin_mw=900.0,
            heat_rate=10.0,
            eford=0.0,
        )
        arrays = generators_to_fleet_arrays([nuc], ["z"], hours=4)
        out = apply_commitment_with_coal_pin(
            arrays, np.ones((1, 4), dtype=bool), np.zeros((1, 4)), [nuc]
        )
        self.assertEqual(out.pmin[0], 900.0)


class TestCoalPinnedInPass2(unittest.TestCase):
    """Coal dispatch is identical between P1 and the P2 re-solve."""

    def test_coal_dispatch_pinned_to_pass1_levels(self):
        hours = 12
        gens = [
            Generator(
                unit_id="COAL",
                name="COAL",
                zone="z",
                fuel_type="coal",
                pmax_mw=300.0,
                pmin_mw=0.0,
                heat_rate=10.0,
                eford=0.0,
            ),
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=1000.0,
                pmin_mw=0.0,
                heat_rate=7.0,
                eford=0.0,
            ),
        ]
        arrays = generators_to_fleet_arrays(gens, ["z"], hours=hours)
        # Coal cheap (20) < CC (50). Demand swings above and below coal Pmax.
        mc = np.array([np.full(hours, 20.0), np.full(hours, 50.0)])
        demand = np.full((1, hours), 250.0)
        demand[0, 3:6] = 500.0  # spikes pull in CC
        demand[0, 8] = 150.0  # dip below coal Pmax

        kwargs = dict(
            wind_cf=np.zeros((1, hours)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, hours)),
            solar_cap=np.zeros(1),
            mc=mc,
            T=hours,
        )
        pass1 = solve_dispatch(arrays, demand, **kwargs)

        committed = np.ones((2, hours), dtype=bool)
        fleet_p2 = apply_commitment_with_coal_pin(
            arrays, committed, pass1.dispatch, gens
        )
        pass2 = solve_dispatch(fleet_p2, demand, **kwargs)

        coal_p1 = pass1.dispatch[0].sum()
        coal_p2 = pass2.dispatch[0].sum()
        self.assertGreater(coal_p1, 0.0)
        self.assertAlmostEqual(coal_p2, coal_p1, delta=0.01 * coal_p1)


if __name__ == "__main__":
    unittest.main()


class TestCouplePeakTranche(unittest.TestCase):
    """couple_peak: a cold plant's peak tranche shuts with its committed tranche."""

    def _bin_gens(self):
        def bin_gen(suffix, pmax, startup, min_run=4.0):
            return Generator(
                unit_id=f"CC_REGULAR_z_p77_{suffix}",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=pmax,
                pmin_mw=0.0,
                heat_rate=7.0,
                eford=0.0,
                plant_group="CC_REGULAR",
                is_campd_bin=True,
                startup_cost_per_mw=startup,
            )

        return [
            bin_gen("committed", 200.0, 50.0),
            bin_gen("econc00", 300.0, 0.0),
            bin_gen("peak", 50.0, 0.0),
        ]

    def test_peak_coupled_when_enabled(self):
        gens = self._bin_gens()
        fa = generators_to_fleet_arrays(gens, ["z"], hours=8)
        committed = np.ones((3, 8), dtype=bool)
        committed[0, 2:5] = False  # committed tranche decommitted hours 2-4
        p1 = np.zeros((3, 8))
        out = apply_commitment_with_coal_pin(fa, committed, p1, gens, couple_peak=True)
        self.assertTrue((out.availability[1, 2:5] == 0.0).all())  # econ coupled
        self.assertTrue((out.availability[2, 2:5] == 0.0).all())  # peak coupled
        self.assertTrue((out.availability[2, :2] > 0.0).all())

    def test_peak_untouched_by_default(self):
        gens = self._bin_gens()
        fa = generators_to_fleet_arrays(gens, ["z"], hours=8)
        committed = np.ones((3, 8), dtype=bool)
        committed[0, 2:5] = False
        p1 = np.zeros((3, 8))
        out = apply_commitment_with_coal_pin(fa, committed, p1, gens)
        self.assertTrue((out.availability[2] > 0.0).all())  # legacy behaviour
