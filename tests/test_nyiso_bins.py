"""Tests for the NYISO per-plant offer-curve tranches and bin assignments.

Pack P2: the CAMPD-derived committed / peaking shares (2023 + 2024 + 2025
facility-level CEMS), the emitted bin-assignment artifact with per-row source
tags, dual-fuel / mixed-facility splitting per ``Plant_Group``, and the CHP
behind-the-meter capacity removal.

NYISO has no coal, so there is no coal must-run layer: the inflexible layer is
the CHP BTM steam hosts (P3), nuclear, hydro min-flows, and the Gowanus 2 & 3 /
Narrows 1 & 2 reliability-must-run barges. Those four NYC barges were given an
RMR designation only past their 1 May 2025 deactivation date (NYISO Q2-2025
STAR); across the 2023 + 2025 backcast window they dispatch as ordinary
economic CT peakers and carry no must-run floor.
"""

import unittest
from pathlib import Path

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import chp_btm_pct
from market_sim.data.fleet import (
    bins_to_fleet,
    fleet_to_bins,
    load_fleet_from_csv,
    thermal_tranche_overrides,
    thermal_tranche_peaking,
)
from market_sim.config.paths import PROCESSED_DIR

REPO = Path(__file__).resolve().parent.parent
TRANCHES = PROCESSED_DIR / "thermal_tranches_NYISO.csv"
BIN_ASSIGNMENTS = PROCESSED_DIR / "bin_assignments_NYISO.csv"
ZONES = get_iso_config("NYISO").zone_names

# The Gowanus 2 & 3 and Narrows 1 & 2 NYC peaking barges — NYISO's RMR units
# (kept past their 1 May 2025 retirement). Modeled as economic CT peakers in
# the backcast window, not a must-run floor.
_RMR_BARGES = {2494, 2499}

# Mixed facilities: one EIA code spanning several fuel classes, split per
# Plant_Group into distinct LP bins (no cross-fuel re-key needed).
_MIXED = {
    2500: {"CC_REGULAR", "ST_GAS"},  # Ravenswood (gas CC + gas steam)
    50292: {"CC_REGULAR", "CT_PEAKER"},  # Bethpage (gas CC + gas CT)
    2493: {"CT_CHP", "ST_CHP"},  # East River (Con Ed steam cogen)
}


class TestNyisoTrancheArtifact(unittest.TestCase):
    """The CAMPD-derived thermal-tranche artifact for NYISO."""

    def test_no_coal_rows(self):
        """No coal must-run layer: the artifact derives zero COAL rows."""
        df = pd.read_csv(TRANCHES)
        self.assertEqual(len(df[df["plant_group"] == "COAL"]), 0)

    def test_committed_shares_bounded_no_coal_mustrun(self):
        """Every NYISO committed share is a sane fraction; must-run is zero
        everywhere (no coal take-or-pay floor in the fleet)."""
        overrides = thermal_tranche_overrides("NYISO")
        self.assertGreater(len(overrides), 50)
        for (code, group), (committed, mustrun) in overrides.items():
            self.assertTrue(0.0 < committed <= 70.0, f"{code} committed {committed}")
            self.assertEqual(mustrun, 0.0, f"{code} {group} mustrun {mustrun}")

    def test_peaking_shares_bounded(self):
        """Duct-firing peaking shares are bounded and CC-only."""
        peaking = thermal_tranche_peaking("NYISO")
        self.assertGreater(len(peaking), 10)
        for (code, group), pct in peaking.items():
            self.assertIn(group, ("CC_REGULAR", "CC_CHP"))
            self.assertTrue(0.0 <= pct <= 25.0, f"{code} peaking {pct}")

    def test_rmr_barges_are_economic_ct_peakers(self):
        """The Gowanus / Narrows RMR barges carry a measured single-digit
        committed share and no must-run floor — economic, not pinned on."""
        overrides = thermal_tranche_overrides("NYISO")
        for code in _RMR_BARGES:
            committed, mustrun = overrides[(code, "CT_PEAKER")]
            self.assertLess(committed, 15.0, f"barge {code} committed {committed}")
            self.assertEqual(mustrun, 0.0)


class TestNyisoBinAssignments(unittest.TestCase):
    """The emitted bin-assignment rows (export_iso_bin_assignments.py)."""

    @classmethod
    def setUpClass(cls):
        cls.bins = pd.read_csv(BIN_ASSIGNMENTS)

    def test_loads_and_covers_thermal_fleet(self):
        self.assertGreater(len(self.bins), 100)
        self.assertGreater(self.bins["Nameplate_MW"].sum(), 20_000)
        # one row per (plant, group)
        keys = list(zip(self.bins["Plant_Code"], self.bins["Plant_Group"]))
        self.assertEqual(len(keys), len(set(keys)))

    def test_no_coal_rows(self):
        self.assertEqual(len(self.bins[self.bins["Plant_Group"] == "COAL"]), 0)

    def test_shares_sum_to_100(self):
        total = self.bins[
            ["Pct_Must_Run", "Pct_Committed", "Pct_Economic", "Pct_Peaking"]
        ].sum(axis=1)
        self.assertTrue(((total - 100.0).abs() <= 0.25).all())

    def test_source_tags(self):
        self.assertLessEqual(
            set(self.bins["Committed_Source"]), {"campd", "class_default"}
        )
        self.assertLessEqual(
            set(self.bins["Peaking_Source"]), {"campd", "class_default"}
        )
        self.assertLessEqual(
            set(self.bins["Must_Run_Source"]),
            {
                "chp_campd_p2",
                "chp_eia923_cf",
                "chp_sector_default",
                "campd",
                "class_default",
                "none",
            },
        )
        # No coal in NYISO, so every measured must-run source is a CHP floor;
        # no bin carries the coal "campd"/"class_default" must-run tag.
        self.assertEqual(
            set(self.bins["Must_Run_Source"]) & {"campd", "class_default"},
            set(),
        )
        # The bulk of CC_REGULAR capacity carries measured committed shares.
        cc = self.bins[self.bins["Plant_Group"] == "CC_REGULAR"]
        measured = cc[cc["Committed_Source"] == "campd"]["Nameplate_MW"].sum()
        self.assertGreater(measured / cc["Nameplate_MW"].sum(), 0.8)

    def test_mixed_facility_split_per_group(self):
        """Each mixed EIA code appears once per Plant_Group, flagged mixed."""
        for code, groups in _MIXED.items():
            rows = self.bins[self.bins["Plant_Code"] == code]
            self.assertEqual(set(rows["Plant_Group"]), groups, f"code {code}")
            self.assertTrue((rows["Mixed_Facility"] != "").all(), f"code {code}")


class TestNyisoFleetBuild(unittest.TestCase):
    """The NYISO fleet builds with per-plant tranches through bins_to_fleet."""

    @classmethod
    def setUpClass(cls):
        cls.gens = load_fleet_from_csv("NYISO", get_iso_config("NYISO"))
        cls.config = ScenarioConfig(
            iso="NYISO",
            chp_steam_following=True,
            cc_peaking_per_plant=True,
        )
        cls.synth = fleet_to_bins(cls.gens, "NYISO", cls.config)
        cls.fleet, _ = bins_to_fleet(cls.synth, ZONES, cls.config)

    def _group_lp_mw(self, code: int, group: str) -> float:
        return sum(
            g.pmax_mw
            for g in self.fleet
            if g.plant_code == code and g.plant_group == group
        )

    def test_synthetic_bins_load(self):
        self.assertGreater(len(self.synth), 100)
        self.assertGreater(len(self.fleet), 250)

    def test_chp_btm_removed_from_lp_capacity(self):
        """Every CHP (plant, group)'s LP capacity excludes its BTM host
        share — the behind-the-meter steam load never enters the dispatch."""
        chp = self.synth[self.synth["Plant_Group"].isin(["CC_CHP", "CT_CHP", "ST_CHP"])]
        self.assertGreater(len(chp), 20)
        for _, b in chp.iterrows():
            code, group = int(b["Plant_Code"]), str(b["Plant_Group"])
            nameplate = float(b["capacity_mw"])
            btm = chp_btm_pct(code, group, iso="NYISO")
            grid = nameplate * (1.0 - btm / 100.0)
            self.assertLessEqual(
                self._group_lp_mw(code, group),
                grid + 0.6,
                f"plant {code} {group}: LP capacity exceeds grid share "
                f"(nameplate {nameplate}, BTM {btm}%)",
            )

    def test_chp_committed_clamped_into_grid_share(self):
        """A cogen whose measured committed floor exceeds its grid share
        (Indeck Corinth 50458) is clamped into the grid: committed keeps its
        measured level, the scarcity peak gives way, no LP overcount."""
        code, group = 50458, "CC_CHP"
        nameplate = float(
            self.synth[
                (self.synth["Plant_Code"] == code)
                & (self.synth["Plant_Group"] == group)
            ]["capacity_mw"].iloc[0]
        )
        btm = chp_btm_pct(code, group, iso="NYISO")
        grid = nameplate * (1.0 - btm / 100.0)
        lp = self._group_lp_mw(code, group)
        self.assertLessEqual(lp, grid + 0.6)
        self.assertGreater(lp, grid * 0.95)

    def test_per_plant_peaking_survives_offer_curve(self):
        """The artifact's measured duct share beats the class pct_peaking."""
        config = self.config.with_overrides(
            offer_curve_by_group={
                "CC_REGULAR": {
                    "committed": 0.92,
                    "econ_low": 1.06,
                    "econ_high": 1.27,
                    "peak": 2.25,
                    "econ_low_share": 0.5,
                    "pct_peaking": 8.0,
                },
            },
        )
        fleet, _ = bins_to_fleet(self.synth, ZONES, config)
        # Saranac (54574): measured peaking capped at 25% of its nameplate.
        code = 54574
        nameplate = float(
            self.synth[self.synth["Plant_Code"] == code]["capacity_mw"].iloc[0]
        )
        peak = [
            g for g in fleet if g.plant_code == code and g.unit_id.endswith("_peak")
        ]
        self.assertEqual(len(peak), 1)
        expected = (
            nameplate * thermal_tranche_peaking("NYISO")[(code, "CC_REGULAR")] / 100.0
        )
        self.assertAlmostEqual(peak[0].pmax_mw, expected, delta=1.0)


class TestNyisoBinsPlantEmissionRatesV2(unittest.TestCase):
    """The v2 measured plant CO2 rates reach the CAMPD-bins (backcast) path.

    G-39 §9.6 backcast-reachability fix: `use_plant_emission_rates_v2` was
    silently unreachable from `bins_to_fleet` (the nyiso-53 v2-on/off twin
    pair solved byte-identical). Flag off must stay byte-identical; flag on
    must override binned NYISO plants' CO2 rates from the committed artifact.
    """

    @classmethod
    def setUpClass(cls):
        cls.gens = load_fleet_from_csv("NYISO", get_iso_config("NYISO"))

    def _fleet(self, **overrides):
        config = ScenarioConfig(
            iso="NYISO",
            mode="backcast",
            weather_year=2024,
            chp_steam_following=True,
            cc_peaking_per_plant=True,
            **overrides,
        )
        synth = fleet_to_bins(self.gens, "NYISO", config)
        fleet, _ = bins_to_fleet(synth, ZONES, config)
        return fleet

    def test_flag_off_is_byte_identical(self):
        base = self._fleet()
        off = self._fleet(use_plant_emission_rates_v2=False)
        self.assertEqual(
            [(g.unit_id, g.emission_rate_co2) for g in base],
            [(g.unit_id, g.emission_rate_co2) for g in off],
        )

    def test_flag_on_overrides_binned_plant_rates(self):
        base = {g.unit_id: g.emission_rate_co2 for g in self._fleet()}
        on = self._fleet(use_plant_emission_rates_v2=True)
        changed = [
            g
            for g in on
            if g.plant_code > 0 and base.get(g.unit_id) != g.emission_rate_co2
        ]
        # The committed artifact carries measured rates for most of the CAMPD
        # NYISO fleet — a material share of binned tranches must move.
        self.assertGreater(len(changed), 50)
        # And a moved rate is a physical CO2 intensity, not a garbage value.
        for g in changed[:20]:
            self.assertGreater(g.emission_rate_co2, 0.0)
            self.assertLess(g.emission_rate_co2, 2.0)  # tonnes/MWh sanity


if __name__ == "__main__":
    unittest.main()
