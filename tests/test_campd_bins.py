"""Tests for CAMPD operational binning and 4-tranche dispatch."""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    bins_to_fleet,
    generators_to_fleet_arrays,
    get_emission_rate,
    get_eford,
    get_nox_rate,
    get_vom,
    load_campd_bins,
)
from market_sim.model.commitment import (
    _commitment_params,
    _startup_cost,
    apply_commitment_with_coal_pin,
)
from market_sim.results.emissions import compute_must_run_emissions

BINS_CSV = "inputs/custom-bin-assignments.csv"
ZONE_NAMES = get_iso_config("ERCOT").zone_names


def _synthetic_bin(**overrides) -> pd.DataFrame:
    """Return a one-row aggregated bin frame, for targeted unit tests."""
    row = {
        "Plant_Group": "CC_REGULAR",
        "ERCOT_Zone": "Houston",
        "Bin_Number": 1,
        "Bin_Label": "TEST1",
        "capacity_mw": 1000.0,
        "hr_weighted": 6.6,
        "pct_mr": 0,
        "pct_mc": 50,
        "pct_econ": 35,
        "pct_peak": 15,
        "min_run": 10,
        "min_down": 4,
        "plant_count": 1,
        "plant_codes": [[1]],
        "fuel": "gas_cc",
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestLoadCampdBins(unittest.TestCase):
    """Tests for ``load_campd_bins`` aggregation."""

    @classmethod
    def setUpClass(cls):
        cls.bins = load_campd_bins(BINS_CSV)

    def test_bins_load(self):
        # One row per unique (group, zone, bin number, label).
        self.assertGreater(len(self.bins), 100)
        self.assertEqual(len(self.bins), self.bins.drop_duplicates(
            ["Plant_Group", "ERCOT_Zone", "Bin_Number", "Bin_Label"]
        ).shape[0])

    def test_tranches_sum_to_100(self):
        total = (
            self.bins["pct_mr"] + self.bins["pct_mc"]
            + self.bins["pct_econ"] + self.bins["pct_peak"]
        )
        self.assertTrue((total == 100).all())

    def test_no_nan_heat_rates(self):
        # Blank weighted HRs in the CSV must be filled, never reach the LP.
        self.assertFalse(self.bins["hr_weighted"].isna().any())
        self.assertTrue((self.bins["hr_weighted"] > 0).all())

    def test_every_bin_has_a_fuel(self):
        self.assertFalse(self.bins["fuel"].isna().any())
        self.assertIn("gas_st", set(self.bins["fuel"]))


class TestBinsToFleet(unittest.TestCase):
    """Tests for ``bins_to_fleet`` generator construction."""

    @classmethod
    def setUpClass(cls):
        cls.config = ScenarioConfig()
        cls.bins = load_campd_bins(BINS_CSV)
        cls.fleet, cls.arrays = bins_to_fleet(
            cls.bins, ZONE_NAMES, cls.config
        )

    def test_mr_derate_removes_must_run_capacity(self):
        # CC_CHP must-run is 60%, so grid capacity is 40% of nameplate.
        cc_chp = self.bins[self.bins["Plant_Group"] == "CC_CHP"]
        nameplate = cc_chp["capacity_mw"].sum()
        grid = sum(
            g.pmax_mw for g in self.fleet
            if g.plant_group == "CC_CHP"
        )
        self.assertAlmostEqual(grid, nameplate * 0.40, places=3)

    def test_cc_regular_pmin_is_half_grid_cap(self):
        # CC_REGULAR: MR 0, MC 50 -> Pmin = 50% of grid capacity.
        b = _synthetic_bin()
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        base = next(g for g in fleet if g.unit_id.endswith("_base"))
        peak = next(g for g in fleet if g.unit_id.endswith("_peak"))
        grid_cap = base.pmax_mw + peak.pmax_mw
        self.assertAlmostEqual(base.pmin_mw, grid_cap * 0.50, places=6)

    def test_coal_pmin_is_40pct_grid_cap(self):
        for g in self.fleet:
            if g.plant_group == "COAL" and g.unit_id.endswith("_base"):
                peak = next(
                    (p for p in self.fleet
                     if p.unit_id == g.unit_id[:-5] + "_peak"),
                    None,
                )
                grid_cap = g.pmax_mw + (peak.pmax_mw if peak else 0.0)
                self.assertAlmostEqual(g.pmin_mw, grid_cap * 0.40, places=3)

    def test_peak_splitting_produces_base_and_peak(self):
        base = [g for g in self.fleet if g.unit_id.endswith("_base")]
        peak = [g for g in self.fleet if g.unit_id.endswith("_peak")]
        # One base per bin; a peak generator for each bin with a peak tranche.
        self.assertEqual(len(base), len(self.bins))
        self.assertGreater(len(peak), 0)
        self.assertLessEqual(len(peak), len(base))
        # Peak generators carry no minimum and a penalized heat rate.
        for g in peak:
            self.assertEqual(g.pmin_mw, 0.0)

    def test_peak_heat_rate_penalty(self):
        b = _synthetic_bin()
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        base = next(g for g in fleet if g.unit_id.endswith("_base"))
        peak = next(g for g in fleet if g.unit_id.endswith("_peak"))
        self.assertAlmostEqual(
            peak.heat_rate, base.heat_rate * self.config.cc_peak_hr_penalty,
            places=6,
        )

    def test_unknown_zone_defaults(self):
        b = _synthetic_bin(ERCOT_Zone="Unknown")
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        for g in fleet:
            self.assertEqual(g.zone, self.config.unknown_zone_default)

    def test_gas_steam_maps_to_gas_st(self):
        gs = [g for g in self.fleet if g.plant_group == "GAS_STEAM"]
        self.assertGreater(len(gs), 0)
        for g in gs:
            self.assertEqual(g.fuel_type, "gas_st")
        self.assertIn("gas_st", FUEL_TYPE_MAP)

    def test_emission_rate_derived_from_heat_rate(self):
        for g in self.fleet:
            self.assertAlmostEqual(
                g.emission_rate_co2,
                get_emission_rate(g.fuel_type, g.heat_rate),
                places=6,
            )


class TestCommitmentParams(unittest.TestCase):
    """Per-bin commitment parameters flow through to the screen."""

    def setUp(self):
        self.config = ScenarioConfig()
        self.fleet, _ = bins_to_fleet(
            _synthetic_bin(min_run=12, min_down=6), ZONE_NAMES, self.config
        )
        self.base = next(
            g for g in self.fleet if g.unit_id.endswith("_base")
        )
        self.peak = next(
            g for g in self.fleet if g.unit_id.endswith("_peak")
        )

    def test_base_generator_uses_bin_commitment_params(self):
        params = _commitment_params(self.base, self.base.heat_rate)
        self.assertIsNotNone(params)
        self.assertEqual(params["min_run_hours"], 12)
        self.assertEqual(params["min_down_hours"], 6)

    def test_peak_generator_not_screened(self):
        # Peak generators carry min_run = 0 and stay out of the screen.
        self.assertIsNone(_commitment_params(self.peak, self.peak.heat_rate))

    def test_coal_base_is_commitment_screened(self):
        # CAMPD coal participates in the P2 commitment screen: the base
        # generator carries the bin's 36h minimum run and a startup cost,
        # while the peak slice stays out of the screen.
        bins = load_campd_bins(BINS_CSV)
        coal = bins[bins["Plant_Group"] == "COAL"]
        fleet, _ = bins_to_fleet(coal, ZONE_NAMES, self.config)
        base = [g for g in fleet if g.unit_id.endswith("_base")]
        peak = [g for g in fleet if g.unit_id.endswith("_peak")]
        self.assertGreater(len(base), 0)
        for g in base:
            params = _commitment_params(g, g.heat_rate)
            self.assertIsNotNone(params)
            self.assertEqual(params["min_run_hours"], 36)
            self.assertGreater(params["startup_per_mw"], 0.0)
        for g in peak:
            self.assertIsNone(_commitment_params(g, g.heat_rate))

    def test_startup_cost_from_bin(self):
        self.assertGreater(_startup_cost(self.base, self.base.heat_rate), 0.0)
        self.assertEqual(_startup_cost(self.peak, self.peak.heat_rate), 0.0)

    def test_campd_coal_decommits_in_pass2(self):
        # CAMPD coal is screened, so apply_commitment_with_coal_pin zeros
        # its availability in decommitted hours rather than pinning it.
        bins = load_campd_bins(BINS_CSV)
        coal = bins[bins["Plant_Group"] == "COAL"].head(1)
        fleet, _ = bins_to_fleet(coal, ZONE_NAMES, self.config)
        base = next(g for g in fleet if g.unit_id.endswith("_base"))
        arrays = generators_to_fleet_arrays([base], ZONE_NAMES, hours=8)
        committed = np.ones((1, 8), dtype=bool)
        committed[0, 2:5] = False  # a 3-hour decommit window
        p1 = np.full((1, 8), base.pmax_mw * 0.6)
        out = apply_commitment_with_coal_pin(arrays, committed, p1, [base])
        self.assertTrue(np.all(out.availability[0, 2:5] == 0.0))
        self.assertTrue(np.all(out.availability[0, :2] > 0.0))
        self.assertTrue(np.all(out.availability[0, 5:] > 0.0))


class TestMustRunEmissions(unittest.TestCase):
    """CHP must-run post-processing."""

    def test_must_run_emissions_positive_for_chp(self):
        bins = load_campd_bins(BINS_CSV)
        mr = compute_must_run_emissions(bins, year=2026, must_run_cf=0.85)
        self.assertFalse(mr.empty)
        # Only CHP bins (MR% > 0) appear.
        self.assertTrue((mr["pct_mr"] > 0).all())
        self.assertTrue((mr["mr_gen_mwh"] > 0).all())
        self.assertTrue((mr["mr_co2_tons"] > 0).all())
        # Must-run MW is the must-run share of nameplate.
        expected = bins.loc[bins["pct_mr"] > 0, "capacity_mw"] \
            * bins.loc[bins["pct_mr"] > 0, "pct_mr"] / 100.0
        self.assertAlmostEqual(
            mr["mr_mw"].sum(), expected.sum(), places=3
        )

    def test_must_run_emissions_empty_without_chp(self):
        bins = load_campd_bins(BINS_CSV)
        non_chp = bins[bins["pct_mr"] == 0]
        mr = compute_must_run_emissions(non_chp, year=2026)
        self.assertTrue(mr.empty)


class TestFuelHelpers(unittest.TestCase):
    """Tests for the fuel-attribute helper functions."""

    def test_helpers_cover_gas_st(self):
        self.assertGreater(get_vom("gas_st"), 0.0)
        self.assertGreater(get_nox_rate("gas_st"), 0.0)
        self.assertGreater(get_eford("gas_st"), 0.0)
        self.assertGreater(get_emission_rate("gas_st", 11.0), 0.0)

    def test_emission_rate_scales_with_heat_rate(self):
        self.assertAlmostEqual(
            get_emission_rate("gas_cc", 14.0),
            2.0 * get_emission_rate("gas_cc", 7.0),
            places=6,
        )


class TestBackwardCompatibility(unittest.TestCase):
    """``use_campd_bins=False`` keeps the legacy aggregate_fleet path."""

    def test_campd_bins_enabled_by_default(self):
        self.assertTrue(ScenarioConfig().use_campd_bins)

    def test_campd_bins_can_be_disabled(self):
        config = ScenarioConfig(use_campd_bins=False)
        self.assertFalse(config.use_campd_bins)


if __name__ == "__main__":
    unittest.main()
