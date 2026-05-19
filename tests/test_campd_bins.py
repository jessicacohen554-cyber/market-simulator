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
        "plant_codes": [1],  # flat list of plant codes, as load_campd_bins emits
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

    def test_chp_mr_derate_removes_must_run_capacity(self):
        # CC_CHP must-run is 60% (host steam obligation, served off-grid),
        # so its LP grid capacity is 40% of nameplate and no ``_mustrun``
        # tranche appears in the LP.
        cc_chp = self.bins[self.bins["Plant_Group"] == "CC_CHP"]
        nameplate = cc_chp["capacity_mw"].sum()
        grid = sum(
            g.pmax_mw for g in self.fleet
            if g.plant_group == "CC_CHP"
        )
        self.assertAlmostEqual(grid, nameplate * 0.40, places=3)
        mustrun = [
            g for g in self.fleet
            if g.plant_group == "CC_CHP" and g.unit_id.endswith("_mustrun")
        ]
        self.assertEqual(mustrun, [])

    def test_coal_mustrun_stays_in_lp(self):
        # Coal must-run (mine-mouth take-or-pay, cycling avoidance, ERCOT
        # RUC) is an LP tranche, so the bin's total LP capacity equals
        # its full nameplate.
        coal = self.bins[self.bins["Plant_Group"] == "COAL"]
        nameplate = coal["capacity_mw"].sum()
        lp_total = sum(
            g.pmax_mw for g in self.fleet
            if g.plant_group == "COAL"
        )
        self.assertAlmostEqual(lp_total, nameplate, places=3)
        mustrun = [
            g for g in self.fleet
            if g.plant_group == "COAL" and g.unit_id.endswith("_mustrun")
        ]
        self.assertGreater(len(mustrun), 0)

    def test_cc_regular_committed_tranche_is_half_grid_cap(self):
        # CC_REGULAR: MR 0, MC 50 -> the _committed tranche is 50% of grid
        # capacity, and no tranche carries a Pmin floor.
        b = _synthetic_bin()
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        grid_cap = sum(g.pmax_mw for g in fleet)
        committed = next(
            g for g in fleet if g.unit_id.endswith("_committed")
        )
        self.assertAlmostEqual(committed.pmax_mw, grid_cap * 0.50, places=6)
        self.assertTrue(all(g.pmin_mw == 0.0 for g in fleet))

    def test_coal_committed_tranche_is_40pct_grid_cap(self):
        # CAMPD coal MC% is 40: the _committed tranche is 40% of grid cap.
        b = _synthetic_bin(
            Plant_Group="COAL", pct_mc=40, pct_econ=45, pct_peak=15,
        )
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        grid_cap = sum(g.pmax_mw for g in fleet)
        committed = next(
            g for g in fleet if g.unit_id.endswith("_committed")
        )
        self.assertAlmostEqual(committed.pmax_mw, grid_cap * 0.40, places=6)
        self.assertTrue(all(g.pmin_mw == 0.0 for g in fleet))

    def test_each_bin_splits_into_three_stepped_tranches(self):
        committed = [
            g for g in self.fleet if g.unit_id.endswith("_committed")
        ]
        econ = [g for g in self.fleet if g.unit_id.endswith("_econ")]
        peak = [g for g in self.fleet if g.unit_id.endswith("_peak")]
        self.assertGreater(len(committed), 80)
        self.assertLessEqual(len(committed), len(self.bins))
        self.assertGreater(len(econ), 0)
        self.assertGreater(len(peak), 0)
        # No tranche carries a Pmin floor.
        self.assertTrue(all(g.pmin_mw == 0.0 for g in self.fleet))

    def test_per_tranche_heat_rates_come_from_csv(self):
        # bins_to_fleet reads ``hr_mc``, ``hr_econ`` and ``hr_peak`` from
        # the aggregated bins frame (capacity-weighted CSV HR columns),
        # falling back to ``hr_weighted`` if a column is blank.
        b = _synthetic_bin(hr_mc=7.5, hr_econ=6.4, hr_peak=10.2)
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        committed = next(
            g for g in fleet if g.unit_id.endswith("_committed")
        )
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))
        peak = next(g for g in fleet if g.unit_id.endswith("_peak"))
        self.assertAlmostEqual(committed.heat_rate, 7.5, places=6)
        self.assertAlmostEqual(econ.heat_rate, 6.4, places=6)
        self.assertAlmostEqual(peak.heat_rate, 10.2, places=6)

    def test_tranche_hr_falls_back_to_bin_average(self):
        # When a CSV HR_<tranche> column is blank for every plant in a
        # bin, the tranche inherits the bin's weighted-average HR.
        b = _synthetic_bin()  # no hr_mc/hr_econ/hr_peak overrides
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        committed = next(
            g for g in fleet if g.unit_id.endswith("_committed")
        )
        self.assertAlmostEqual(committed.heat_rate, 6.6, places=6)

    def test_unknown_zone_defaults(self):
        b = _synthetic_bin(ERCOT_Zone="Unknown")
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        for g in fleet:
            self.assertEqual(g.zone, self.config.unknown_zone_default)

    def test_coal_bins_tagged_with_fuel_supply(self):
        # Every coal tranche carries a fuel-supply tag (mine-mouth lignite
        # or PRB by rail) resolved from its plant code.
        coal = [g for g in self.fleet if g.plant_group == "COAL"]
        self.assertGreater(len(coal), 0)
        for g in coal:
            self.assertIn(g.coal_supply, ("lignite", "prb"))
        # Non-coal generators carry no supply tag.
        gas = [g for g in self.fleet if g.plant_group != "COAL"]
        self.assertTrue(all(g.coal_supply == "" for g in gas))

    def test_gas_steam_maps_to_gas_st(self):
        gs = [g for g in self.fleet if g.plant_group in ("ST_GAS", "ST_CHP")]
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
        self.committed = next(
            g for g in self.fleet if g.unit_id.endswith("_committed")
        )
        self.econ = next(g for g in self.fleet if g.unit_id.endswith("_econ"))
        self.peak = next(g for g in self.fleet if g.unit_id.endswith("_peak"))

    def test_committed_tranche_uses_bin_commitment_params(self):
        params = _commitment_params(self.committed, self.committed.heat_rate)
        self.assertIsNotNone(params)
        self.assertEqual(params["min_run_hours"], 12)
        self.assertEqual(params["min_down_hours"], 6)

    def test_econ_and_peak_tranches_not_screened(self):
        # Only the committed tranche carries a min run; ECON and PEAK are
        # incremental output and stay out of the commitment screen.
        self.assertIsNone(_commitment_params(self.econ, self.econ.heat_rate))
        self.assertIsNone(_commitment_params(self.peak, self.peak.heat_rate))

    def test_coal_committed_tranche_is_commitment_screened(self):
        # CAMPD coal participates in the P2 commitment screen: the
        # _committed tranche carries the bin's 36h minimum run and a
        # startup cost, while ECON and PEAK stay out of the screen.
        bins = load_campd_bins(BINS_CSV)
        coal = bins[bins["Plant_Group"] == "COAL"]
        fleet, _ = bins_to_fleet(coal, ZONE_NAMES, self.config)
        committed = [g for g in fleet if g.unit_id.endswith("_committed")]
        others = [g for g in fleet if not g.unit_id.endswith("_committed")]
        self.assertGreater(len(committed), 0)
        for g in committed:
            params = _commitment_params(g, g.heat_rate)
            self.assertIsNotNone(params)
            self.assertEqual(params["min_run_hours"], 36)
            self.assertGreater(params["startup_per_mw"], 0.0)
        for g in others:
            self.assertIsNone(_commitment_params(g, g.heat_rate))

    def test_startup_cost_only_on_committed_tranche(self):
        self.assertGreater(
            _startup_cost(self.committed, self.committed.heat_rate), 0.0
        )
        self.assertEqual(_startup_cost(self.econ, self.econ.heat_rate), 0.0)
        self.assertEqual(_startup_cost(self.peak, self.peak.heat_rate), 0.0)

    def test_campd_coal_decommits_in_pass2(self):
        # CAMPD coal is screened, so apply_commitment_with_coal_pin zeros
        # its availability in decommitted hours rather than pinning it.
        bins = load_campd_bins(BINS_CSV)
        coal = bins[bins["Plant_Group"] == "COAL"].head(1)
        fleet, _ = bins_to_fleet(coal, ZONE_NAMES, self.config)
        base = next(g for g in fleet if g.unit_id.endswith("_committed"))
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
        # Only non-coal CHP bins (MR% > 0) appear -- coal must-run is in
        # the LP, so post-processing excludes it.
        self.assertTrue((mr["pct_mr"] > 0).all())
        self.assertTrue((mr["fuel"] != "coal").all())
        self.assertTrue((mr["mr_gen_mwh"] > 0).all())
        self.assertTrue((mr["mr_co2_tons"] > 0).all())
        # Must-run MW is the must-run share of nameplate, over non-coal
        # bins.
        chp = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")]
        expected = chp["capacity_mw"] * chp["pct_mr"] / 100.0
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
