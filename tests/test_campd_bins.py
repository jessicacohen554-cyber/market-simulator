"""Tests for CAMPD operational binning and 4-tranche dispatch."""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import CAMPD_BINS_CSV
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
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

BINS_CSV = str(CAMPD_BINS_CSV)
ZONE_NAMES = get_iso_config("ERCOT").zone_names


def _synthetic_bin(**overrides) -> pd.DataFrame:
    """Return a one-row per-plant bin frame, for targeted unit tests.

    Each bin in the new schema is one EIA plant, so every row carries a
    ``Plant_Code`` and ``Plant_Name`` and the per-tranche heat rates
    (``hr_mr`` / ``hr_mc`` / ``hr_econ`` / ``hr_peak``) default to the
    plant's own ``hr_weighted``.
    """
    hr = float(overrides.get("hr_weighted", 6.6))
    row = {
        "Plant_Group": "CC_REGULAR",
        "ERCOT_Zone": "Houston",
        "Bin_Number": 1,
        "Bin_Label": "TEST1",
        "Plant_Code": 1,
        "Plant_Name": "Test Plant",
        "capacity_mw": 1000.0,
        "hr_weighted": hr,
        "hr_mr": hr,
        "hr_mc": hr,
        "hr_econ": hr,
        "hr_peak": hr,
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
        # One row per (plant, plant-group): the per-plant bin schema means
        # every plant gets its own dispatch generator. A plant whose coal
        # and gas-steam units coexist (e.g. W A Parish 3470) splits across
        # two rows, one per fuel/group.
        self.assertGreater(len(self.bins), 250)
        self.assertEqual(
            len(self.bins),
            self.bins.drop_duplicates(["Plant_Code", "Plant_Group"]).shape[0],
        )

    def test_tranches_sum_to_100(self):
        total = (
            self.bins["pct_mr"]
            + self.bins["pct_mc"]
            + self.bins["pct_econ"]
            + self.bins["pct_peak"]
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
        cls.fleet, cls.arrays = bins_to_fleet(cls.bins, ZONE_NAMES, cls.config)

    def test_chp_mr_derate_removes_must_run_capacity(self):
        # CC_CHP must-run is 60% (host steam obligation, served off-grid),
        # so its LP grid capacity is 40% of nameplate and no ``_mustrun``
        # tranche appears in the LP.
        cc_chp = self.bins[self.bins["Plant_Group"] == "CC_CHP"]
        nameplate = cc_chp["capacity_mw"].sum()
        grid = sum(g.pmax_mw for g in self.fleet if g.plant_group == "CC_CHP")
        self.assertAlmostEqual(grid, nameplate * 0.40, places=3)
        mustrun = [
            g
            for g in self.fleet
            if g.plant_group == "CC_CHP" and g.unit_id.endswith("_mustrun")
        ]
        self.assertEqual(mustrun, [])

    def test_coal_mustrun_stays_in_lp(self):
        # Coal must-run (mine-mouth take-or-pay, cycling avoidance, ERCOT
        # RUC) is an LP tranche, so the bin's total LP capacity equals
        # its full nameplate.
        coal = self.bins[self.bins["Plant_Group"] == "COAL"]
        nameplate = coal["capacity_mw"].sum()
        lp_total = sum(g.pmax_mw for g in self.fleet if g.plant_group == "COAL")
        self.assertAlmostEqual(lp_total, nameplate, places=3)
        mustrun = [
            g
            for g in self.fleet
            if g.plant_group == "COAL" and g.unit_id.endswith("_mustrun")
        ]
        self.assertGreater(len(mustrun), 0)

    def test_cc_regular_committed_tranche_is_half_grid_cap(self):
        # CC_REGULAR: MR 0, MC 50 -> the _committed tranche is 50% of grid
        # capacity, and no tranche carries a Pmin floor.
        b = _synthetic_bin()
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        grid_cap = sum(g.pmax_mw for g in fleet)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        self.assertAlmostEqual(committed.pmax_mw, grid_cap * 0.50, places=6)
        self.assertTrue(all(g.pmin_mw == 0.0 for g in fleet))

    def test_coal_committed_tranche_is_40pct_grid_cap(self):
        # CAMPD coal MC% is 40: the _committed tranche is 40% of grid cap.
        b = _synthetic_bin(
            Plant_Group="COAL",
            pct_mc=40,
            pct_econ=45,
            pct_peak=15,
        )
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        grid_cap = sum(g.pmax_mw for g in fleet)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        self.assertAlmostEqual(committed.pmax_mw, grid_cap * 0.40, places=6)
        self.assertTrue(all(g.pmin_mw == 0.0 for g in fleet))

    def test_each_bin_splits_into_three_stepped_tranches(self):
        committed = [g for g in self.fleet if g.unit_id.endswith("_committed")]
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
        # the per-plant bins frame: each is ``Plant_Avg_HR ×
        # HR_Mult_<tranche>`` assembled in ``load_campd_bins``.
        b = _synthetic_bin(hr_mc=7.5, hr_econ=6.4, hr_peak=10.2)
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))
        peak = next(g for g in fleet if g.unit_id.endswith("_peak"))
        self.assertAlmostEqual(committed.heat_rate, 7.5, places=6)
        self.assertAlmostEqual(econ.heat_rate, 6.4, places=6)
        self.assertAlmostEqual(peak.heat_rate, 10.2, places=6)

    def test_co2_rate_uses_physical_hr_not_tranche_pricing_hr(self):
        # R2/EM-4: emission_rate_co2 must be booked at the plant's physical heat
        # rate (hr_weighted), NOT the bid-tranche heat rate — so the offer-curve
        # pricing multipliers (a peak HR of 10.2 vs a physical 6.6) never inflate
        # CO2. Every tranche of the plant shares one physical CO2 rate.
        b = _synthetic_bin(hr_weighted=6.6, hr_mc=7.5, hr_econ=6.4, hr_peak=10.2)
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        plant = [g for g in fleet if g.plant_code == 1]
        self.assertGreater(len(plant), 1)
        physical = get_emission_rate("gas_cc", 6.6)
        for g in plant:
            self.assertAlmostEqual(g.emission_rate_co2, physical, places=9)
        # The peak tranche prices at the inflated HR but does NOT emit at it.
        peak = next(g for g in plant if g.unit_id.endswith("_peak"))
        self.assertAlmostEqual(peak.heat_rate, 10.2, places=6)
        self.assertLess(peak.emission_rate_co2, get_emission_rate("gas_cc", 10.2))
        # No generator's CO2 rate embeds a >1.0 pricing multiplier over physical.
        for g in fleet:
            self.assertLessEqual(
                g.emission_rate_co2, get_emission_rate(g.fuel_type, 6.6) + 1e-9
            )

    def test_tranche_hr_defaults_to_plant_hr_when_mult_blank(self):
        # When a CSV HR_Mult_<tranche> column is blank (a zero-capacity
        # tranche), the per-plant HR loader applies the group-default
        # multiplier; in this synthetic bin every tranche shares the
        # plant's own HR (1.0× multiplier), so each tranche carries the
        # plant's measured heat rate.
        b = _synthetic_bin()
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, self.config)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
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

    def test_emission_rate_uses_physical_hr_uniform_across_tranches(self):
        # R2/EM-4: CO2 is booked at the plant's PHYSICAL heat rate, not the
        # bid-tranche heat rate, so every tranche of one plant/group shares a
        # single physical CO2 rate — even where the peak tranche's pricing HR is
        # inflated. (Before R2 each tranche emitted at its own bid HR.)
        by_plant: dict[tuple, list] = {}
        for g in self.fleet:
            by_plant.setdefault((g.plant_code, g.plant_group, g.fuel_type), []).append(
                g
            )
        for (plant_code, _group, fuel), gens in by_plant.items():
            if plant_code <= 0:
                continue  # multi-plant / legacy aggregate bins
            rates = {round(g.emission_rate_co2, 9) for g in gens}
            self.assertEqual(
                len(rates), 1, f"plant {plant_code} has non-uniform CO2 rates {rates}"
            )
            # And the shared rate never exceeds the CO2 implied by the plant's
            # highest bid-tranche HR (it is derived from the lower physical HR).
            max_hr = max(g.heat_rate for g in gens)
            self.assertLessEqual(
                next(iter(rates)), get_emission_rate(fuel, max_hr) + 1e-9
            )


class TestUnifiedOfferCurve(unittest.TestCase):
    """The offer-curve ramp spans econ_low -> econ_high for every group, with
    the duct-firing peak kept as a SEPARATE band that jumps up above the ramp
    (no fold-peak); committed % and the CC peak HR are configurable."""

    BASE_HR = 6.6  # _synthetic_bin default hr_weighted

    def _build(self, group, offer, **cfg):
        config = ScenarioConfig(
            offer_curve_by_group={group: offer},
            offer_curve_smoothing_n=6,
            offer_curve_smoothing_exp=1.0,
            **cfg,
        )
        b = _synthetic_bin(Plant_Group=group, pct_mr=0, pct_mc=50, pct_peak=15)
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, config)
        return fleet

    def test_ramp_tops_at_econ_high_with_separate_peak(self):
        # CC ramps econ_low (1.0) -> econ_high (1.3); the duct-burner peak
        # (F-class default 2.25x) is a separate band ABOVE the ramp, not its
        # top. Pre-change, the ramp ran straight up to 2.25 and emitted no peak.
        offer = {
            "committed": 0.9,
            "econ_low": 1.0,
            "econ_high": 1.3,
            "econ_low_share": 0.5,
            "pct_peaking": 10.0,
        }
        fleet = self._build("CC_REGULAR", offer)
        econ = [g for g in fleet if "_econc" in g.unit_id]
        peak = [g for g in fleet if g.unit_id.endswith("_peak")]
        self.assertEqual(len(econ), 6)  # n=6 rising slices
        self.assertEqual(len(peak), 1)  # separate peak band survives
        # The whole ramp sits at or below econ_high; the peak jumps above it.
        top_econ = max(g.heat_rate for g in econ)
        self.assertLessEqual(top_econ, self.BASE_HR * 1.3 + 1e-6)
        self.assertAlmostEqual(peak[0].heat_rate, self.BASE_HR * 2.25, places=6)
        self.assertGreater(peak[0].heat_rate, top_econ)

    def test_cc_peak_mult_is_configurable(self):
        # An explicit "peak" key overrides the per-class duct-burner default.
        offer = {
            "committed": 0.9,
            "econ_low": 1.0,
            "econ_high": 1.3,
            "peak": 1.8,
            "econ_low_share": 0.5,
            "pct_peaking": 10.0,
        }
        fleet = self._build("CC_CHP", offer)
        peak = next(g for g in fleet if g.unit_id.endswith("_peak"))
        self.assertAlmostEqual(peak.heat_rate, self.BASE_HR * 1.8, places=6)

    def test_pct_committed_is_configurable(self):
        # "pct_committed" overrides the CSV Pct_Committed (here 50 -> 30).
        offer = {
            "committed": 0.9,
            "econ_low": 1.0,
            "econ_high": 1.3,
            "pct_committed": 30.0,
            "econ_low_share": 0.5,
            "pct_peaking": 10.0,
        }
        fleet = self._build("CC_REGULAR", offer)
        grid_cap = sum(g.pmax_mw for g in fleet)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        self.assertAlmostEqual(committed.pmax_mw, grid_cap * 0.30, places=6)

    def test_midpoint_anchor_reshapes_the_ramp(self):
        # offer_curve_smoothing_mid = 0.25 sags the ramp below linear in the
        # bottom half and concentrates the rise in the top slices, while the
        # endpoints (econ_low / econ_high reach) are unchanged.
        offer = {
            "committed": 0.9,
            "econ_low": 1.0,
            "econ_high": 1.3,
            "econ_low_share": 0.5,
            "pct_peaking": 10.0,
        }
        lin = sorted(
            g.heat_rate
            for g in self._build("CC_REGULAR", offer)
            if "_econc" in g.unit_id
        )
        mid = sorted(
            g.heat_rate
            for g in self._build("CC_REGULAR", offer, offer_curve_smoothing_mid=0.25)
            if "_econc" in g.unit_id
        )
        self.assertEqual(len(mid), 6)
        # Bottom half cheaper than the linear ramp, same lo->hi span overall.
        for m, l in zip(mid[:3], lin[:3]):
            self.assertLess(m, l)
        self.assertLess(mid[-1], self.BASE_HR * 1.3 + 1e-6)
        # Monotone rising slices (a valid offer curve).
        self.assertEqual(mid, sorted(mid))

    def test_peak_ladder_splits_band_into_quantile_rungs(self):
        # A measured ``peak_ladder`` replaces the single flat peak tranche
        # with equal-capacity rungs at the ladder multipliers; total peak
        # capacity is conserved and each rung prices base_hr x its multiplier
        # (docs/FINDING-ercot-priceshape-2026-07.md §4).
        ladder = [[0.2, 1.6], [0.2, 2.6], [0.2, 4.3], [0.2, 43.9], [0.2, 144.2]]
        offer = {
            "committed": 0.9,
            "econ_low": 1.0,
            "econ_high": 1.3,
            "peak": 4.3,
            "peak_ladder": ladder,
            "econ_low_share": 0.5,
            "pct_peaking": 10.0,
        }
        fleet = self._build("CC_REGULAR", offer)
        flat = self._build(
            "CC_REGULAR", {k: v for k, v in offer.items() if k != "peak_ladder"}
        )
        rungs = [g for g in fleet if g.unit_id.rpartition("_")[2].startswith("peak")]
        flat_peak = [g for g in flat if g.unit_id.rpartition("_")[2].startswith("peak")]
        self.assertEqual(len(rungs), 5)
        self.assertEqual(len(flat_peak), 1)
        # capacity conserved vs the single flat band
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in rungs), flat_peak[0].pmax_mw, places=6
        )
        # every rung is 20% of the band, priced at base_hr x mult, rising
        hrs = sorted(g.heat_rate for g in rungs)
        for hr, (share, mult) in zip(hrs, ladder):
            self.assertAlmostEqual(hr, self.BASE_HR * mult, places=6)
        for g in rungs:
            self.assertAlmostEqual(g.pmax_mw, flat_peak[0].pmax_mw * 0.2, places=6)
        # CO2 rate stays the physical rate — identical across rungs (R2/EM-4)
        self.assertEqual(len({round(g.emission_rate_co2, 9) for g in rungs}), 1)


class TestCommitmentParams(unittest.TestCase):
    """Per-bin commitment parameters flow through to the screen."""

    def setUp(self):
        self.config = ScenarioConfig()
        self.fleet, _ = bins_to_fleet(
            _synthetic_bin(min_run=12, min_down=6), ZONE_NAMES, self.config
        )
        self.committed = next(g for g in self.fleet if g.unit_id.endswith("_committed"))
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
        self.assertGreater(_startup_cost(self.committed, self.committed.heat_rate), 0.0)
        self.assertEqual(_startup_cost(self.econ, self.econ.heat_rate), 0.0)
        self.assertEqual(_startup_cost(self.peak, self.peak.heat_rate), 0.0)

    def test_campd_coal_decommits_in_pass2(self):
        # CAMPD coal is screened, so apply_commitment_with_coal_pin zeros its
        # availability in decommitted hours rather than pinning it — as long
        # as other capacity in the zone covers the P1 load, so the adequacy
        # backstop does not need to restore it.
        bins = load_campd_bins(BINS_CSV)
        coal = bins[bins["Plant_Group"] == "COAL"].head(1)
        fleet, _ = bins_to_fleet(coal, ZONE_NAMES, self.config)
        base = next(g for g in fleet if g.unit_id.endswith("_committed"))
        # A large gas unit in the same zone, committed every hour, covers the
        # zone's P1 thermal load so decommitting coal creates no shortfall.
        gas = Generator(
            unit_id="GAS",
            name="GAS",
            zone=base.zone,
            fuel_type="gas_cc",
            pmax_mw=base.pmax_mw * 5.0,
            pmin_mw=0.0,
            heat_rate=7.0,
            eford=0.0,
        )
        gens = [base, gas]
        arrays = generators_to_fleet_arrays(gens, ZONE_NAMES, hours=8)
        committed = np.ones((2, 8), dtype=bool)
        committed[0, 2:5] = False  # a 3-hour coal decommit window
        p1 = np.zeros((2, 8))
        p1[0] = base.pmax_mw * 0.6  # coal ran in P1; gas idle
        out = apply_commitment_with_coal_pin(arrays, committed, p1, gens)
        self.assertTrue(np.all(out.availability[0, 2:5] == 0.0))
        self.assertTrue(np.all(out.availability[0, :2] > 0.0))
        self.assertTrue(np.all(out.availability[0, 5:] > 0.0))

    def test_backstop_prevents_coal_decommit_when_zone_would_be_short(self):
        # If decommitting screened coal would drop zone capacity below the P1
        # thermal level, the adequacy backstop restores coal to its P1
        # availability so P2 cannot create unmet demand.
        bins = load_campd_bins(BINS_CSV)
        coal = bins[bins["Plant_Group"] == "COAL"].head(1)
        fleet, _ = bins_to_fleet(coal, ZONE_NAMES, self.config)
        base = next(g for g in fleet if g.unit_id.endswith("_committed"))
        arrays = generators_to_fleet_arrays([base], ZONE_NAMES, hours=8)
        committed = np.ones((1, 8), dtype=bool)
        committed[0, 2:5] = False
        p1 = np.full((1, 8), base.pmax_mw * 0.6)  # only unit in the zone
        out = apply_commitment_with_coal_pin(arrays, committed, p1, [base])
        np.testing.assert_allclose(out.availability[0, 2:5], 0.6)


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
        self.assertAlmostEqual(mr["mr_mw"].sum(), expected.sum(), places=3)

    def test_must_run_emissions_empty_without_chp(self):
        bins = load_campd_bins(BINS_CSV)
        non_chp = bins[bins["pct_mr"] == 0]
        mr = compute_must_run_emissions(non_chp, year=2026)
        self.assertTrue(mr.empty)

    def test_chp_export_floor_measured_sets_grid_floor(self):
        # chp_export_floor_measured (backcast overlay): a CHP bin's grid
        # steam-following floor is its measured EIA-923 class CF for the year
        # times the sector grid-delivery share, superseding the pooled CAMPD
        # p2 minimum. Off (default) keeps the p2/artifact floor.
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.chp import chp_btm_pct, chp_class_netgen_mwh

        year = 2023
        netgen = chp_class_netgen_mwh(year)
        bins = load_campd_bins(BINS_CSV, year=year)
        cc_chp = bins[bins["Plant_Group"] == "CC_CHP"]
        code = next(
            int(c)
            for c in cc_chp["Plant_Code"]
            if netgen.get((int(c), "CC_CHP"), 0.0) > 0.0
        )
        row = cc_chp[cc_chp["Plant_Code"] == code]
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=year,
            chp_steam_following=True,
            chp_export_floor_measured=True,
        )
        fleet, _ = bins_to_fleet(row, ZONE_NAMES, cfg)
        floor = sum(getattr(g, "chp_grid_pmin_mw", 0.0) for g in fleet)
        nameplate = float(row["capacity_mw"].iloc[0])
        total_cf = min(1.0, netgen[(code, "CC_CHP")] / (nameplate * 8760.0))
        btm = chp_btm_pct(code, "CC_CHP") / 100.0
        expected = total_cf * (1.0 - btm) * nameplate
        # min(floor, econ_cap) can clamp the floor below the measured level;
        # it must never exceed it.
        self.assertLessEqual(floor, expected + 1e-6)
        self.assertGreater(floor, 0.0)
        # Off by default: the same build without the flag keeps the p2 floor
        # (different unless the plant's p2 happens to equal its annual CF).
        cfg_off = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=year,
            chp_steam_following=True,
        )
        fleet_off, _ = bins_to_fleet(row, ZONE_NAMES, cfg_off)
        floor_off = sum(getattr(g, "chp_grid_pmin_mw", 0.0) for g in fleet_off)
        self.assertNotAlmostEqual(floor, floor_off, places=1)

    def test_measured_share_mode_is_total_times_share(self):
        # Measured-share mode (rule #13): BTM = 923 class total x host share,
        # never a function of the model's own dispatch. Plants absent from the
        # share map fall back to their bin pct_mr share.
        bins = load_campd_bins(BINS_CSV)
        chp = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")]
        first = int(chp["Plant_Code"].iloc[0])
        totals = {int(c): 1_000_000.0 for c in chp["Plant_Code"]}
        mr = compute_must_run_emissions(
            bins,
            year=2023,
            total_gen_by_plant=totals,
            btm_share_by_plant={first: 0.35},
        )
        by_code = dict(zip(mr["Plant_Code"].astype(int), mr["mr_gen_mwh"]))
        self.assertAlmostEqual(by_code[first], 350_000.0, places=3)
        second = int(chp["Plant_Code"].iloc[1])
        expected = 1_000_000.0 * float(chp["pct_mr"].iloc[1]) / 100.0
        self.assertAlmostEqual(by_code[second], expected, places=3)

    def test_covered_chp_books_measured_grid_rate(self):
        # EM-7 / plan §5 R5: a covered CHP plant's behind-the-meter CO2 intensity
        # equals its measured (v2) grid rate, not the fuel-class default.
        bins = load_campd_bins(BINS_CSV)
        chp = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")]
        code = int(chp["Plant_Code"].iloc[0])
        grid_rate = 0.371  # tCO2/MWh net, the same rate the plant's grid bins use
        mr = compute_must_run_emissions(
            bins,
            year=2026,
            must_run_cf=0.85,
            measured_rate_by_plant={code: grid_rate},
        )
        row = mr[mr["Plant_Code"].astype(int) == code].iloc[0]
        btm_rate = row["mr_co2_tons"] / row["mr_gen_mwh"]
        self.assertAlmostEqual(btm_rate, grid_rate, places=6)
        # An uncovered CHP bin keeps its fuel-class default (rate != grid_rate).
        other = mr[mr["Plant_Code"].astype(int) != code].iloc[0]
        other_rate = other["mr_co2_tons"] / other["mr_gen_mwh"]
        self.assertNotAlmostEqual(other_rate, grid_rate, places=6)

    def test_class_cf_replaces_flat_fallback(self):
        # R5b: the forecast fallback sizes BTM with a measured CHP class CF,
        # not the flat must_run_cf, when class_cf_by_group covers the group.
        bins = load_campd_bins(BINS_CSV)
        chp = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")]
        grp = str(chp["Plant_Group"].iloc[0])
        mr = compute_must_run_emissions(
            bins,
            year=2026,
            must_run_cf=0.85,
            class_cf_by_group={grp: 0.5},
        )
        row = mr[mr["Plant_Group"].astype(str) == grp].iloc[0]
        expected = row["mr_mw"] * 8760.0 * 0.5
        self.assertAlmostEqual(row["mr_gen_mwh"], expected, places=3)

    def test_measured_class_cf_from_steam_units(self):
        # measured_class_cf keys CHP off measured steam output and CAMPD
        # unit_type, returning a gen-weighted op-hours utilization per group.
        import pandas as pd

        from market_sim.results.emissions import measured_class_cf

        annual = pd.DataFrame(
            {
                "unit_type": ["Combined cycle", "Combustion turbine", "Boiler"],
                "steam_load_klbh_sum": [100.0, 50.0, 0.0],  # last: not CHP
                "gross_mwh": [1_000_000.0, 200_000.0, 500_000.0],
                "op_hours": [8000, 4000, 8760],
            }
        )
        cf = measured_class_cf(annual)
        self.assertAlmostEqual(cf["CC_CHP"], 8000 / 8760.0, places=6)
        self.assertAlmostEqual(cf["CT_CHP"], 4000 / 8760.0, places=6)
        self.assertNotIn("ST_CHP", cf)  # zero-steam boiler is excluded


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
