"""Tests for the NEISO per-plant offer-curve tranches and bin assignments.

Pack P2: the CAMPD-derived committed / peaking shares (2023 + 2024 + 2025
NE-state facility-level CEMS), the emitted bin-assignment artifact with per-row
source tags, dual-fuel / mixed-facility splitting per ``Plant_Group``, and the
CHP behind-the-meter capacity removal.

NEISO carries no coal *must-run* layer. The fleet's lone coal unit — Merrimack
(EIA 2364, Bow NH) — survives in CEMS only as a winter-peaking unit (a few
hundred online hours/yr over the pooled window), so its derived must-run share
is 0.0: it cycles on economics, not a sunk take-or-pay floor. The genuinely
inflexible NEISO layer is therefore the CHP BTM steam hosts (P3), nuclear
(Seabrook, Millstone 2 & 3) on its monthly-CF model, hydro min-flows, and any
reliability-must-run designations — never a coal floor.

The oil / dual-fuel peaker band is *tagged*, not re-derived: the gas-primary
oil-switching units (Montville ST steam, the CT peakers Potter / Waters River /
A L Pierce / Bucksport / Waterbury / Exelon West Medway / MMWEC, ...) are
flagged by ``fleet.dual_fuel_plant_groups`` (the P13 EIA-860 multifuel tags) and
dispatch economically — switching to the oil price under ``dual_fuel_switching``
when winter gas spikes past distillate parity — with no must-run pin.
"""

from market_sim.config.plant_taxonomy import COAL_CLASSES
import unittest

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import chp_btm_pct
from market_sim.data.fleet import (
    bins_to_fleet,
    dual_fuel_plant_groups,
    fleet_to_bins,
    load_fleet_from_csv,
    thermal_tranche_overrides,
    thermal_tranche_peaking,
)
from market_sim.config.paths import PROCESSED_DIR
from scripts.export_iso_bin_assignments import build_bin_assignments
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
TRANCHES = PROCESSED_DIR / "thermal_tranches_NEISO.csv"
BIN_ASSIGNMENTS = PROCESSED_DIR / "bin_assignments_NEISO.csv"
ZONES = get_iso_config("NEISO").zone_names

# Merrimack (Bow, NH) — NEISO's last operating coal unit, a winter peaker by the
# 2023-2025 window. Present in the artifact but with a zero must-run share.
_COAL_CODE = 2364

# Mixed facilities: one EIA code spanning several fuel classes, split per
# Plant_Group into distinct LP bins (no cross-fuel re-key needed — all gas).
_MIXED = {
    52061: {"CC_CHP", "CT_CHP"},  # Hartford Hospital Cogeneration
    58084: {"CC_CHP", "CT_CHP"},  # Kimberly Clark
    52026: {"CC_REGULAR", "CT_PEAKER"},  # Dartmouth Power Associates
    10883: {"CT_CHP", "ST_CHP"},  # Medical Area Total Energy Plant
}

# Gas-primary oil-switching units the P13 EIA-860 multifuel tags flag as
# dual-fuel and that land in the NEISO offer-curve peaker / steam band. Montville
# is the ST_OIL-capable steamer; the rest are CT peakers.
_DUAL_FUEL_PEAKERS = {
    (546, "ST_GAS"),  # Montville Station
    (1660, "CT_PEAKER"),  # Potter Station 2
    (1678, "CT_PEAKER"),  # Waters River
    (6635, "CT_PEAKER"),  # A L Pierce
    (50243, "CT_PEAKER"),  # Bucksport Generation
    (56629, "CT_PEAKER"),  # Waterbury Generation
    (59882, "CT_PEAKER"),  # Exelon West Medway II
    (63559, "CT_PEAKER"),  # MMWEC Simple Cycle Gas Turbine
}


class TestNeisoTrancheArtifact(unittest.TestCase):
    """The CAMPD-derived thermal-tranche artifact for NEISO."""

    def test_no_coal_mustrun_layer(self):
        """No coal take-or-pay floor: every derived must-run share is 0.0,
        including the lone winter-peaking coal unit (Merrimack)."""
        overrides = thermal_tranche_overrides("NEISO")
        self.assertGreater(len(overrides), 30)
        for (code, group), (committed, mustrun) in overrides.items():
            self.assertEqual(mustrun, 0.0, f"{code} {group} mustrun {mustrun}")

    def test_coal_is_winter_peaker_not_baseload(self):
        """Merrimack is present as a COAL row but carries no must-run pin —
        it cycles on economics like a winter peaker, not a sunk baseload."""
        overrides = thermal_tranche_overrides("NEISO")
        self.assertIn((_COAL_CODE, "COAL"), overrides)
        _committed, mustrun = overrides[(_COAL_CODE, "COAL")]
        self.assertEqual(mustrun, 0.0)
        df = pd.read_csv(TRANCHES)
        coal = df[df["plant_group"] == "COAL"]
        # The only coal row is Merrimack, and its CEMS run-time is a small
        # fraction of an 8760 (winter-only), confirming it is not baseload.
        self.assertEqual(set(coal["plant_code"]), {_COAL_CODE})
        self.assertLess(int(coal["online_hours"].iloc[0]), 8760)

    def test_committed_shares_bounded(self):
        """Every NEISO committed share is a sane fraction of nameplate."""
        overrides = thermal_tranche_overrides("NEISO")
        for (code, group), (committed, _mustrun) in overrides.items():
            self.assertTrue(
                0.0 < committed <= 70.0, f"{code} {group} committed {committed}"
            )

    def test_peaking_shares_bounded_and_cc_only(self):
        """Duct-firing peaking shares are bounded and combined-cycle-only."""
        peaking = thermal_tranche_peaking("NEISO")
        self.assertGreater(len(peaking), 10)
        for (code, group), pct in peaking.items():
            self.assertIn(group, ("CC_REGULAR", "CC_CHP"))
            self.assertTrue(0.0 <= pct <= 25.0, f"{code} peaking {pct}")


class TestNeisoBinAssignments(unittest.TestCase):
    """The emitted bin-assignment rows (export_iso_bin_assignments.py)."""

    @classmethod
    def setUpClass(cls):
        cls.bins = pd.read_csv(BIN_ASSIGNMENTS)

    def test_loads_and_covers_thermal_fleet(self):
        self.assertGreater(len(self.bins), 100)
        self.assertGreater(self.bins["Nameplate_MW"].sum(), 10_000)
        # one row per (plant, group)
        keys = list(zip(self.bins["Plant_Code"], self.bins["Plant_Group"]))
        self.assertEqual(len(keys), len(set(keys)))

    def test_committed_artifact_is_deterministic(self):
        """The committed bin-assignment CSV regenerates byte-for-byte from the
        current code + tranche artifact (no stale hand-edits)."""
        regen = build_bin_assignments("NEISO")
        committed = pd.read_csv(BIN_ASSIGNMENTS)
        # The blank Mixed_Facility cells round-trip through CSV as NaN; normalise
        # both sides to empty strings so the compare is on real content.
        for frame in (regen, committed):
            frame["Mixed_Facility"] = frame["Mixed_Facility"].fillna("")
        pd.testing.assert_frame_equal(
            regen.reset_index(drop=True),
            committed.reset_index(drop=True),
            check_dtype=False,
        )

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
        # The bulk of CC_REGULAR capacity carries measured committed shares.
        cc = self.bins[self.bins["Plant_Group"] == "CC_REGULAR"]
        measured = cc[cc["Committed_Source"] == "campd"]["Nameplate_MW"].sum()
        self.assertGreater(measured / cc["Nameplate_MW"].sum(), 0.8)

    def test_coal_row_carries_no_mustrun(self):
        """The single COAL row (Merrimack) carries a zero must-run share."""
        coal = self.bins[self.bins["Plant_Group"].isin(COAL_CLASSES)]
        self.assertEqual(len(coal), 1)
        self.assertEqual(float(coal["Pct_Must_Run"].iloc[0]), 0.0)

    def test_mixed_facility_split_per_group(self):
        """Each mixed EIA code appears once per Plant_Group, flagged mixed."""
        for code, groups in _MIXED.items():
            rows = self.bins[self.bins["Plant_Code"] == code]
            self.assertEqual(set(rows["Plant_Group"]), groups, f"code {code}")
            self.assertTrue((rows["Mixed_Facility"] != "").all(), f"code {code}")


class TestNeisoDualFuelPeakers(unittest.TestCase):
    """Oil / dual-fuel peaker band — tagged from P13, not re-derived."""

    @classmethod
    def setUpClass(cls):
        cls.bins = pd.read_csv(BIN_ASSIGNMENTS)
        cls.dual = dual_fuel_plant_groups()

    def test_p13_tags_flag_the_neiso_oil_switchers(self):
        """The expected gas-primary oil-switching peakers/steamers are flagged
        by the shared EIA-860 multifuel tagger (Montville + the CT peakers)."""
        for key in _DUAL_FUEL_PEAKERS:
            self.assertIn(key, self.dual, f"{key} not flagged dual-fuel")

    def test_dual_fuel_peakers_dispatch_economically(self):
        """Every tagged oil/dual-fuel peaker is an ordinary economic bin — it
        appears in the assignment frame with no must-run pin (the oil switch is
        a fuel-price overlay under dual_fuel_switching, not a capacity floor)."""
        bin_keys = {
            (int(c), str(g))
            for c, g in zip(self.bins["Plant_Code"], self.bins["Plant_Group"])
        }
        for code, group in _DUAL_FUEL_PEAKERS:
            self.assertIn((code, group), bin_keys, f"{code} {group} missing")
            row = self.bins[
                (self.bins["Plant_Code"] == code) & (self.bins["Plant_Group"] == group)
            ]
            self.assertEqual(float(row["Pct_Must_Run"].iloc[0]), 0.0)
            self.assertEqual(row["Must_Run_Source"].iloc[0], "none")


class TestNeisoFleetBuild(unittest.TestCase):
    """The NEISO fleet builds with per-plant tranches through bins_to_fleet."""

    @classmethod
    def setUpClass(cls):
        cls.gens = load_fleet_from_csv("NEISO", get_iso_config("NEISO"))
        cls.config = ScenarioConfig(
            iso="NEISO",
            chp_steam_following=True,
            cc_peaking_per_plant=True,
        )
        cls.synth = fleet_to_bins(cls.gens, "NEISO", cls.config)
        cls.fleet, _ = bins_to_fleet(cls.synth, ZONES, cls.config)

    def _group_lp_mw(self, code: int, group: str) -> float:
        return sum(
            g.pmax_mw
            for g in self.fleet
            if g.plant_code == code and g.plant_group == group
        )

    def test_synthetic_bins_load(self):
        self.assertGreater(len(self.synth), 100)
        self.assertGreater(len(self.fleet), 200)

    def test_chp_btm_removed_from_lp_capacity(self):
        """Every CHP (plant, group)'s LP capacity excludes its BTM host
        share — the behind-the-meter steam load never enters the dispatch."""
        chp = self.synth[self.synth["Plant_Group"].isin(["CC_CHP", "CT_CHP", "ST_CHP"])]
        self.assertGreater(len(chp), 20)
        for _, b in chp.iterrows():
            code, group = int(b["Plant_Code"]), str(b["Plant_Group"])
            nameplate = float(b["capacity_mw"])
            btm = chp_btm_pct(code, group, iso="NEISO")
            grid = nameplate * (1.0 - btm / 100.0)
            self.assertLessEqual(
                self._group_lp_mw(code, group),
                grid + 0.6,
                f"plant {code} {group}: LP capacity exceeds grid share "
                f"(nameplate {nameplate}, BTM {btm}%)",
            )

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
        # Stony Brook (6081): measured peaking 21.5% of its nameplate.
        code = 6081
        nameplate = float(
            self.synth[self.synth["Plant_Code"] == code]["capacity_mw"].iloc[0]
        )
        peak = [
            g for g in fleet if g.plant_code == code and g.unit_id.endswith("_peak")
        ]
        self.assertEqual(len(peak), 1)
        expected = (
            nameplate * thermal_tranche_peaking("NEISO")[(code, "CC_REGULAR")] / 100.0
        )
        self.assertAlmostEqual(peak[0].pmax_mw, expected, delta=1.0)


if __name__ == "__main__":
    unittest.main()
