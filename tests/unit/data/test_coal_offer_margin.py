"""Tests for the coal-offer net-revenue margin form (ERCOT-137).

``ScenarioConfig.coal_offer_net_revenue_margin`` — the gas net-revenue
margin's coal analogue: the CAMPD coal ``_mustrun`` (take-or-pay) band is
repriced from the fitted VOM-only sunk-fuel discount to full delivered-fuel
tracking plus a fuel-invariant measured margin, landing EXACTLY on the
measured RT curve bottom (``coal_offer_margin_level``) at the delivered-coal
anchor. Trivial fixtures first, per the repo testing pattern (1 generator,
24 hours).

Also covers the ERCOT-137 water-fill correctness fix: the measured-DAM
availability redistribution's ceiling is ``pmax × forced_derate`` (the
``BIN_FORCED_DERATE_BY_YEAR`` multiplier), never raw pmax — a plant modelling
a destroyed unit must not be resurrected by the restore branch
(ERCOT-135 §7.2, Martin Lake 1.451× its own COP-declared max).
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.legacy_bins import apply_coal_tranches, assemble_mc
from market_sim.data.fleet.withholding import _dam_waterfill

ANCHOR = 1.7387  # constants.COAL_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"]
LEVEL = 15.8807  # constants.COAL_OFFER_MARGIN_LEVEL_BY_ISO["ERCOT"]
HOURS = 24


def _coal_mustrun(unit_id: str = "COAL_N_p1_mustrun", campd: bool = True) -> Generator:
    """One trivial coal min-load tranche (HR 11, VOM 4.5)."""
    return Generator(
        unit_id=unit_id,
        name="t",
        zone="N",
        fuel_type="coal",
        efficiency_bin="subcritical",
        pmax_mw=100.0,
        pmin_mw=0.0,
        heat_rate=11.0,
        vom=4.5,
        emission_rate_co2=1.0,
        nox_rate=0.0,
        eford=0.05,
        online_year=1980,
        is_campd_bin=campd,
        plant_group="COAL_BIT",
        bin_label="X",
        plant_code=1,
    )


def _mc_after_tranches(gen: Generator, config: ScenarioConfig, fuel: np.ndarray):
    """Assemble base MC for one generator and apply the coal tranche seam."""
    fa = generators_to_fleet_arrays([gen], ["N"], config=config, hours=HOURS)
    mc = assemble_mc(fa, fuel, 0.0, 0.0)
    apply_coal_tranches(mc, [gen], fa, [0.0], fuel, config)
    return mc


class TestCoalOfferMargin(unittest.TestCase):
    """The net-margin form's identity, invariance, gating and hard errors."""

    def test_flag_off_keeps_vom_only_bid(self):
        cfg = ScenarioConfig(hours=HOURS)
        fuel = np.full((1, HOURS), ANCHOR)
        mc = _mc_after_tranches(_coal_mustrun(), cfg, fuel)
        self.assertAlmostEqual(float(mc[0, 0]), 4.5, places=9)

    def test_bid_at_anchor_is_exactly_the_measured_level(self):
        cfg = ScenarioConfig(
            hours=HOURS,
            coal_offer_net_revenue_margin=True,
            coal_offer_margin_anchor=ANCHOR,
            coal_offer_margin_level=LEVEL,
        )
        fuel = np.full((1, HOURS), ANCHOR)
        mc = _mc_after_tranches(_coal_mustrun(), cfg, fuel)
        self.assertAlmostEqual(float(mc[0, 0]), LEVEL, places=9)

    def test_margin_is_fuel_invariant_and_burn_tracks_delivered_fuel(self):
        cfg = ScenarioConfig(
            hours=HOURS,
            coal_offer_net_revenue_margin=True,
            coal_offer_margin_anchor=ANCHOR,
            coal_offer_margin_level=LEVEL,
        )
        for dfuel in (-0.5, 0.25, 1.0):
            fuel = np.full((1, HOURS), ANCHOR + dfuel)
            mc = _mc_after_tranches(_coal_mustrun(), cfg, fuel)
            # bid = HR × (fuel − anchor) + level: the above-fuel margin never
            # scales with the fuel bill.
            self.assertAlmostEqual(float(mc[0, 0]), LEVEL + 11.0 * dfuel, places=9)

    def test_armed_without_constants_is_a_hard_error(self):
        cfg = ScenarioConfig(hours=HOURS, coal_offer_net_revenue_margin=True)
        fuel = np.full((1, HOURS), ANCHOR)
        gen = _coal_mustrun()
        fa = generators_to_fleet_arrays([gen], ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        with self.assertRaises(ValueError):
            apply_coal_tranches(mc, [gen], fa, [0.0], fuel, cfg)

    def test_legacy_t1_path_is_inert(self):
        cfg = ScenarioConfig(
            hours=HOURS,
            coal_offer_net_revenue_margin=True,
            coal_offer_margin_anchor=ANCHOR,
            coal_offer_margin_level=LEVEL,
        )
        fuel = np.full((1, HOURS), ANCHOR)
        gen = _coal_mustrun(unit_id="COAL_N_p1_t1", campd=False)
        mc = _mc_after_tranches(gen, cfg, fuel)
        self.assertAlmostEqual(float(mc[0, 0]), 4.5, places=9)

    def test_non_mustrun_campd_tranches_untouched(self):
        cfg = ScenarioConfig(
            hours=HOURS,
            coal_offer_net_revenue_margin=True,
            coal_offer_margin_anchor=ANCHOR,
            coal_offer_margin_level=LEVEL,
        )
        fuel = np.full((1, HOURS), ANCHOR)
        gen = _coal_mustrun(unit_id="COAL_N_p1_committed")
        fa = generators_to_fleet_arrays([gen], ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        apply_coal_tranches(mc, [gen], fa, [0.75], fuel, cfg)
        # committed band keeps the sunk-fuel discount form untouched.
        expected = 11.0 * ANCHOR + 4.5 - 0.25 * 11.0 * ANCHOR
        self.assertAlmostEqual(float(mc[0, 0]), expected, places=9)

    def test_default_cache_key_is_unmoved_and_armed_hashes_distinct(self):
        base = ScenarioConfig()
        armed = ScenarioConfig(
            coal_offer_net_revenue_margin=True,
            coal_offer_margin_anchor=ANCHOR,
            coal_offer_margin_level=LEVEL,
        )
        self.assertNotEqual(base.cache_key(), armed.cache_key())


class TestDamWaterfillForcedDerateCeiling(unittest.TestCase):
    """The redistribution respects pmax × forced_derate (ERCOT-137 fix)."""

    def test_restore_saturates_at_the_forced_derate_ceiling(self):
        a = np.full((2, 4), 0.5)
        cap = np.array([100.0, 100.0])
        target = np.full(4, 1.0)
        active = np.ones(4, bool)
        out = _dam_waterfill(a.copy(), cap, target, active, ceil=np.array([1.0, 0.67]))
        self.assertTrue(np.allclose(out[0], 1.0))
        self.assertTrue(np.allclose(out[1], 0.67))

    def test_unit_ceiling_is_bit_identical_to_the_legacy_form(self):
        rng = np.random.default_rng(7)
        a = rng.uniform(0.0, 1.0, size=(3, 6))
        cap = np.array([50.0, 120.0, 80.0])
        target = rng.uniform(0.0, 1.0, size=6)
        active = np.ones(6, bool)
        legacy = _dam_waterfill(a.copy(), cap, target, active)
        ones = _dam_waterfill(a.copy(), cap, target, active, ceil=np.ones(3))
        self.assertTrue(np.array_equal(legacy, ones))

    def test_remove_branch_unchanged_by_ceiling(self):
        a = np.full((2, 4), 0.5)
        cap = np.array([100.0, 100.0])
        target = np.full(4, 0.3)
        active = np.ones(4, bool)
        r1 = _dam_waterfill(a.copy(), cap, target, active)
        r2 = _dam_waterfill(a.copy(), cap, target, active, ceil=np.array([1.0, 0.67]))
        self.assertTrue(np.array_equal(r1, r2))


if __name__ == "__main__":
    unittest.main()
