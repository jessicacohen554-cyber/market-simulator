"""Tests for the coal `_peak`-tranche gas-anchored offer margin (ERCOT-140).

``ScenarioConfig.coal_peak_offer_margin`` — the coal offer-curve UPPER-TAIL
successor ERCOT-123 §7.2 chartered: the CAMPD coal ``_peak*`` tranche is
repriced from its band-multiplier × sigmoid composition to the measured
top-decile level at the SHARED gas anchor, with the corpus's own measured GAS
slope (the top tracks gas — gas-parity opportunity pricing — not coal fuel).
Trivial fixtures first, per the repo testing pattern (2 generators, 24 hours:
one coal peak row + one CC_REGULAR row supplying the gas reference series).
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.legacy_bins import apply_coal_tranches, assemble_mc

ANCHOR = 2.2494  # constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"] (SHARED)
LEVEL = 35.1989  # constants.COAL_PEAK_OFFER_LEVEL_BY_ISO["ERCOT"]
GAS_HR = 10.4100  # constants.COAL_PEAK_OFFER_GAS_HR_BY_ISO["ERCOT"]
HOURS = 24
COAL_HR = 16.0  # trivial hr_peak (base × peak multiplier)
COAL_VOM = 4.5
COAL_FUEL = 1.7  # delivered coal $/MMBtu — must NOT reach the repriced bid


def _gen(
    unit_id: str,
    fuel_type: str,
    plant_group: str,
    heat_rate: float,
    campd: bool = True,
) -> Generator:
    """One trivial tranche generator."""
    return Generator(
        unit_id=unit_id,
        name="t",
        zone="N",
        fuel_type=fuel_type,
        efficiency_bin="subcritical" if fuel_type == "coal" else "f_class",
        pmax_mw=100.0,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        vom=COAL_VOM if fuel_type == "coal" else 2.0,
        emission_rate_co2=0.0,
        nox_rate=0.0,
        eford=0.05,
        online_year=1980,
        is_campd_bin=campd,
        plant_group=plant_group,
        bin_label="X",
        plant_code=1,
    )


def _fleet(gas_price: float):
    """(generators, fuel_prices): coal `_peak` row 0, CC_REGULAR row 1."""
    gens = [
        _gen("COAL_N_p1_peak", "coal", "COAL_BIT", COAL_HR),
        _gen("CC_N_p1_committed", "gas_cc", "CC_REGULAR", 7.0),
    ]
    fuel = np.vstack(
        [
            np.full(HOURS, COAL_FUEL),
            np.full(HOURS, gas_price),
        ]
    )
    return gens, fuel


def _mc_after_tranches(config: ScenarioConfig, gas_price: float):
    """Assemble base MC for the two-row fleet and apply the tranche seam."""
    gens, fuel = _fleet(gas_price)
    fa = generators_to_fleet_arrays(gens, ["N"], config=config, hours=HOURS)
    mc = assemble_mc(fa, fuel, 0.0, 0.0)
    apply_coal_tranches(mc, gens, fa, [1.0, 1.0], fuel, config)
    return mc


def _armed(**kw) -> ScenarioConfig:
    return ScenarioConfig(
        hours=HOURS,
        coal_peak_offer_margin=True,
        coal_peak_offer_level=LEVEL,
        coal_peak_offer_gas_hr=GAS_HR,
        gas_offer_margin_anchor=ANCHOR,
        **kw,
    )


class TestCoalPeakOfferMargin(unittest.TestCase):
    """The gas-parity top-of-curve form's identity, gating and hard errors."""

    def test_flag_off_keeps_full_srmc_bid(self):
        cfg = ScenarioConfig(hours=HOURS)
        mc = _mc_after_tranches(cfg, gas_price=ANCHOR)
        self.assertAlmostEqual(
            float(mc[0, 0]), COAL_HR * COAL_FUEL + COAL_VOM, places=9
        )

    def test_bid_at_gas_anchor_is_exactly_the_measured_level(self):
        mc = _mc_after_tranches(_armed(), gas_price=ANCHOR)
        self.assertAlmostEqual(float(mc[0, 0]), LEVEL, places=9)

    def test_bid_tracks_gas_not_coal(self):
        # The slope basis is GAS at GAS_HR (the corpus's own measured
        # response); the plant's own coal heat rate / fuel never enter.
        for dgas in (-0.5, 0.25, 1.0):
            mc = _mc_after_tranches(_armed(), gas_price=ANCHOR + dgas)
            self.assertAlmostEqual(float(mc[0, 0]), LEVEL + GAS_HR * dgas, places=9)

    def test_armed_without_constants_is_a_hard_error(self):
        cfg = ScenarioConfig(hours=HOURS, coal_peak_offer_margin=True)
        gens, fuel = _fleet(ANCHOR)
        fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        with self.assertRaises(ValueError):
            apply_coal_tranches(mc, gens, fa, [1.0, 1.0], fuel, cfg)

    def test_armed_without_cc_rows_is_a_hard_error(self):
        # No CC_REGULAR CAMPD row → the gas reference series is undefined.
        cfg = _armed()
        gens = [_gen("COAL_N_p1_peak", "coal", "COAL_BIT", COAL_HR)]
        fuel = np.full((1, HOURS), COAL_FUEL)
        fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        with self.assertRaises(ValueError):
            apply_coal_tranches(mc, gens, fa, [1.0], fuel, cfg)

    def test_non_peak_coal_tranches_untouched(self):
        cfg = _armed()
        gens, fuel = _fleet(ANCHOR)
        gens[0] = _gen("COAL_N_p1_econ01", "coal", "COAL_BIT", COAL_HR)
        fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        apply_coal_tranches(mc, gens, fa, [1.0, 1.0], fuel, cfg)
        self.assertAlmostEqual(
            float(mc[0, 0]), COAL_HR * COAL_FUEL + COAL_VOM, places=9
        )

    def test_legacy_non_campd_peak_row_is_inert(self):
        cfg = _armed()
        gens, fuel = _fleet(ANCHOR)
        gens[0] = _gen("COAL_N_p1_peak", "coal", "COAL_BIT", COAL_HR, campd=False)
        fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        apply_coal_tranches(mc, gens, fa, [1.0, 1.0], fuel, cfg)
        self.assertAlmostEqual(
            float(mc[0, 0]), COAL_HR * COAL_FUEL + COAL_VOM, places=9
        )

    def test_sigmoid_passthrough_never_composes_on_the_repriced_row(self):
        # A fuel_frac < 1 (the supply sigmoid) must NOT discount the repriced
        # bid — the margin branch exits before the fuel-frac seam (rule 19).
        cfg = _armed()
        gens, fuel = _fleet(ANCHOR)
        fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        apply_coal_tranches(mc, gens, fa, [0.76, 1.0], fuel, cfg)
        self.assertAlmostEqual(float(mc[0, 0]), LEVEL, places=9)

    def test_peak_ladder_suffixes_covered(self):
        cfg = _armed()
        gens, fuel = _fleet(ANCHOR)
        gens[0] = _gen("COAL_N_p1_peak2", "coal", "COAL_BIT", COAL_HR)
        fa = generators_to_fleet_arrays(gens, ["N"], config=cfg, hours=HOURS)
        mc = assemble_mc(fa, fuel, 0.0, 0.0)
        apply_coal_tranches(mc, gens, fa, [1.0, 1.0], fuel, cfg)
        self.assertAlmostEqual(float(mc[0, 0]), LEVEL, places=9)

    def test_default_cache_key_is_unmoved_and_armed_hashes_distinct(self):
        base = ScenarioConfig()
        armed = ScenarioConfig(
            coal_peak_offer_margin=True,
            coal_peak_offer_level=LEVEL,
            coal_peak_offer_gas_hr=GAS_HR,
        )
        self.assertNotEqual(base.cache_key(), armed.cache_key())


if __name__ == "__main__":
    unittest.main()
