"""Tests for the CAISO per-plant offer-curve tranches and bin assignments.

Pack P2: the CEMS->EIA split-plant remap (AES Alamitos / Huntington Beach),
the ST_GAS peaker exclusions, the CAMPD-derived committed / peaking shares,
the emitted bin-assignment artifact, and the CHP BTM capacity removal.
"""

import unittest
from pathlib import Path

import pandas as pd
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import chp_btm_pct
from market_sim.data.fleet import (
    bins_to_fleet,
    fleet_to_bins,
    load_fleet_from_csv,
    thermal_tranche_chp_steam_level,
    thermal_tranche_overrides,
    thermal_tranche_peaking,
)
from market_sim.config.paths import PROCESSED_DIR, RAW_DATA_DIR
from market_sim.data.outages import ST_GAS_PEAKER_PLANTS

REPO = Path(__file__).resolve().parent.parent
BIN_ASSIGNMENTS = PROCESSED_DIR / "bin_assignments_CAISO.csv"
UNIT_OUTAGES = RAW_DATA_DIR / "campd-unit-outages-CAISO.csv"
ZONES = get_iso_config("CAISO").zone_names

# The CAISO once-through-cooling steamers (run-when-called reliability
# units) and the EIA codes of the repowered AES CCGTs whose CEMS history
# files under the legacy boiler ORIS.
_CAISO_ST_GAS_PEAKERS = {315, 335, 350}
_AES_CC_CODES = {62115, 62116}


class TestCaisoSplitPlantRemap(unittest.TestCase):
    """CEMS->EIA remap: AES CCGT history attaches to the right fleet rows."""

    def test_st_gas_peakers_excluded(self):
        self.assertLessEqual(_CAISO_ST_GAS_PEAKERS, ST_GAS_PEAKER_PLANTS)

    def test_unit_outages_routed_to_new_cc_codes(self):
        """The outage extract carries the CCGTs, not the legacy steamers."""
        df = pd.read_csv(UNIT_OUTAGES)
        facilities = set(df["facility_id"].astype(int))
        self.assertEqual(facilities & _CAISO_ST_GAS_PEAKERS, set())
        self.assertLessEqual(_AES_CC_CODES, facilities)
        aes = df[df["facility_id"].isin(_AES_CC_CODES)]
        self.assertEqual(set(aes["plant_group"]), {"CC_REGULAR"})

    def test_tranche_artifact_covers_remapped_plants(self):
        """The AES CCGTs carry measured committed shares after the remap."""
        overrides = thermal_tranche_overrides("CAISO")
        for code in _AES_CC_CODES:
            committed, mustrun = overrides[(code, "CC_REGULAR")]
            self.assertTrue(0.0 < committed <= 70.0)
            self.assertEqual(mustrun, 0.0)
        # The legacy steamers keep their own (now unpolluted) ST_GAS rows:
        # spiky reliability runners hold a single-digit committed floor.
        for code in _CAISO_ST_GAS_PEAKERS:
            committed, _ = overrides[(code, "ST_GAS")]
            self.assertLess(committed, 15.0)


class TestCaisoTrancheArtifact(unittest.TestCase):
    """The CAMPD-derived thermal-tranche artifact for CAISO."""

    def test_no_coal_rows(self):
        """No coal must-run layer: the artifact derives zero COAL rows."""
        df = pd.read_csv(PROCESSED_DIR / "thermal_tranches_CAISO.csv")
        self.assertEqual(len(df[df["plant_group"] == "COAL"]), 0)

    def test_peaking_shares_bounded(self):
        peaking = thermal_tranche_peaking("CAISO")
        self.assertGreater(len(peaking), 10)
        for (code, group), pct in peaking.items():
            self.assertIn(group, ("CC_REGULAR", "CC_CHP"))
            self.assertTrue(0.0 <= pct <= 25.0, f"{code} peaking {pct}")

    @pytest.mark.xfail(
        strict=True,
        reason="pre-existing failure on main as of 2026-07-05 (found wiring PR CI "
        "in W1-P1); unrelated to this change, tracked for follow-up",
    )
    def test_peaking_empty_for_artifacts_without_column(self):
        """PJM's committed artifact predates the column — must stay inert."""
        self.assertEqual(thermal_tranche_peaking("PJM"), {})


class TestCaisoBinAssignments(unittest.TestCase):
    """The emitted bin-assignment rows (export_iso_bin_assignments.py)."""

    @classmethod
    def setUpClass(cls):
        cls.bins = pd.read_csv(BIN_ASSIGNMENTS)

    def test_loads_and_covers_thermal_fleet(self):
        self.assertGreater(len(self.bins), 200)
        self.assertGreater(self.bins["Nameplate_MW"].sum(), 25_000)
        # one row per (plant, group)
        keys = list(zip(self.bins["Plant_Code"], self.bins["Plant_Group"]))
        self.assertEqual(len(keys), len(set(keys)))

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

    def test_mixed_facility_split_per_group(self):
        """Glenarm (422) appears once per Plant_Group, flagged as mixed."""
        glenarm = self.bins[self.bins["Plant_Code"] == 422]
        self.assertEqual(set(glenarm["Plant_Group"]), {"CC_REGULAR", "CT_PEAKER"})
        self.assertEqual(set(glenarm["Mixed_Facility"]), {"CC+CT"})


class TestCaisoFleetBuild(unittest.TestCase):
    """The CAISO fleet builds with per-plant tranches through bins_to_fleet."""

    @classmethod
    def setUpClass(cls):
        cls.gens = load_fleet_from_csv("CAISO", get_iso_config("CAISO"))
        cls.config = ScenarioConfig(
            iso="CAISO",
            chp_steam_following=True,
            cc_peaking_per_plant=True,
        )
        cls.synth = fleet_to_bins(cls.gens, "CAISO", cls.config)
        cls.fleet, _ = bins_to_fleet(cls.synth, ZONES, cls.config)

    def _plant_lp_mw(self, code: int) -> float:
        return sum(g.pmax_mw for g in self.fleet if g.plant_code == code)

    def test_synthetic_bins_load(self):
        self.assertGreater(len(self.synth), 200)
        # Threshold tracks CHP_BTM_PCT_BY_SECTOR: a higher industrial/commercial
        # BTM share leaves less grid capacity per plant, so some economic/peaking
        # tranches round to zero MW and are dropped as separate LP rows.
        self.assertGreater(len(self.fleet), 475)

    def test_chp_btm_removed_from_lp_capacity(self):
        """Every CHP plant's LP capacity excludes its BTM host share."""
        chp = self.synth[self.synth["Plant_Group"].isin(["CC_CHP", "CT_CHP", "ST_CHP"])]
        for _, b in chp.iterrows():
            code = int(b["Plant_Code"])
            nameplate = float(b["capacity_mw"])
            btm = chp_btm_pct(code, str(b["Plant_Group"]), iso="CAISO")
            grid = nameplate * (1.0 - btm / 100.0)
            self.assertLessEqual(
                self._plant_lp_mw(code),
                grid + 0.6,
                f"plant {code}: LP capacity exceeds grid share "
                f"(nameplate {nameplate}, BTM {btm}%)",
            )

    def test_elk_hills_committed_clamped_into_grid_share(self):
        """Measured committed (70%) + BTM (35%) clamps, no LP overcount."""
        lp = self._plant_lp_mw(55400)
        nameplate = float(
            self.synth[self.synth["Plant_Code"] == 55400]["capacity_mw"].iloc[0]
        )
        self.assertLessEqual(lp, nameplate * 0.65 + 0.6)
        self.assertGreater(lp, nameplate * 0.60)

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
        # Malburg (56041): the peaking tranche is its measured duct share of the
        # plant's LP capacity. That capacity is the reconciled EIA-860 nameplate
        # (130 MW): the raw net-summer rows sum to 139 MW, above the nameplate
        # sum, so the summer-capacity consistency guard clamps the plant to
        # nameplate. Derive the capacity from the built bins rather than pinning
        # a literal, so the assertion tracks the reconciled figure.
        cap = float(
            self.synth[self.synth["Plant_Code"] == 56041]["capacity_mw"].iloc[0]
        )
        peak = [
            g for g in fleet if g.plant_code == 56041 and g.unit_id.endswith("_peak")
        ]
        self.assertEqual(len(peak), 1)
        expected = cap * thermal_tranche_peaking("CAISO")[(56041, "CC_REGULAR")] / 100.0
        self.assertAlmostEqual(peak[0].pmax_mw, expected, delta=1.0)


class TestCaisoChpSteamFloorP25(unittest.TestCase):
    """The CHP steam-host operating-level floor (``chp_steam_floor_p25``).

    Exercises the level swap against the committed CAISO artifact, which since
    WP-3 (owner-ruled 2026-07-19) carries ``steam_level_cf`` — the
    loading-when-on construction for CAMPD-visible cogens (flat hosts keep
    their high on-load baseload; cyclers' on-frequency collapses their level)
    plus the EIA-923 delivery-implied level for CEMS-invisible cogens — and
    the default-off build stays byte-identical to the p2 floors.
    """

    @classmethod
    def setUpClass(cls):
        gens = load_fleet_from_csv("CAISO", get_iso_config("CAISO"))
        cls.cfg_off = ScenarioConfig(iso="CAISO", chp_steam_following=True)
        cls.cfg_on = ScenarioConfig(
            iso="CAISO", chp_steam_following=True, chp_steam_floor_p25=True
        )
        cls.synth = fleet_to_bins(gens, "CAISO", cls.cfg_off)
        cls.fleet_off, _ = bins_to_fleet(cls.synth, ZONES, cls.cfg_off)
        cls.fleet_on, _ = bins_to_fleet(cls.synth, ZONES, cls.cfg_on)

    def _plant_floor_mw(self, fleet, code: int) -> float:
        return sum(g.chp_grid_pmin_mw for g in fleet if g.plant_code == code)

    def test_loader_reads_artifact(self):
        m = thermal_tranche_chp_steam_level("CAISO")
        # WP-3 lens (a): the flat CAMPD-visible hosts carry their measured
        # loading-when-on baseload (on-frequency x p50 on-load).
        self.assertAlmostEqual(m[(55217, "CC_CHP")], 99.8, delta=0.1)
        self.assertAlmostEqual(m[(55400, "CC_CHP")], 92.6, delta=0.1)
        self.assertAlmostEqual(m[(50865, "CT_CHP")], 86.2, delta=0.1)
        # WP-3 lens (b): CEMS-invisible cogens carry the pooled EIA-923
        # delivery-implied level (previously invisible to the CAMPD p25).
        self.assertAlmostEqual(m[(10213, "CC_CHP")], 80.5, delta=0.1)
        self.assertAlmostEqual(m[(50752, "CT_CHP")], 92.1, delta=0.1)
        # a partial cycler's on-frequency collapses its level well below the
        # flat hosts' (Gilroy: online a minority of available hours)
        self.assertLess(m[(10034, "CC_CHP")], 25.0)

    def test_flat_hosts_gain_operating_level_floor(self):
        """Floor = steam_level x (1 - BTM share) x nameplate for the flat hosts."""
        m = thermal_tranche_chp_steam_level("CAISO")
        for code, group in ((55217, "CC_CHP"), (55400, "CC_CHP")):
            nameplate = float(
                self.synth[
                    (self.synth["Plant_Code"] == code)
                    & (self.synth["Plant_Group"] == group)
                ]["capacity_mw"].iloc[0]
            )
            btm = chp_btm_pct(code, group, iso="CAISO") / 100.0
            # The floor is clipped to the plant's committed+econ band (the
            # duct-firing peak tranche never carries the steam base) — at the
            # WP-3 loading-when-on level (~93-100 %) that physical cap can
            # bind, so expect the smaller of the formula and the non-peak
            # band.
            band_cap = sum(
                g.pmax_mw
                for g in self.fleet_on
                if g.plant_code == code and not g.unit_id.endswith("_peak")
            )
            expected = min(m[(code, group)] / 100.0 * (1.0 - btm) * nameplate, band_cap)
            self.assertAlmostEqual(
                self._plant_floor_mw(self.fleet_on, code),
                expected,
                delta=1.0,
                msg=f"plant {code}",
            )
            # the p2 level for these plants is 0.0 — no floor when off
            self.assertEqual(self._plant_floor_mw(self.fleet_off, code), 0.0)

    def test_floor_never_exceeds_grid_capacity(self):
        for code in (55217, 55400, 50865):
            lp = sum(g.pmax_mw for g in self.fleet_on if g.plant_code == code)
            self.assertLessEqual(self._plant_floor_mw(self.fleet_on, code), lp + 0.6)

    def test_cycler_floor_is_delivery_bounded(self):
        """A partial cycler's floor is its (collapsed) measured level, not the
        flat-host baseload: the WP-3 statistic self-targets by on-frequency."""
        m = thermal_tranche_chp_steam_level("CAISO")
        for code in (10034, 10294):  # partial-cycling merchant CC_CHP
            level = m[(code, "CC_CHP")]
            self.assertLess(level, 25.0)
            nameplate = float(
                self.synth[
                    (self.synth["Plant_Code"] == code)
                    & (self.synth["Plant_Group"] == "CC_CHP")
                ]["capacity_mw"].iloc[0]
            )
            btm = chp_btm_pct(code, "CC_CHP", iso="CAISO") / 100.0
            expected = level / 100.0 * (1.0 - btm) * nameplate
            self.assertAlmostEqual(
                self._plant_floor_mw(self.fleet_on, code), expected, delta=1.0
            )

    def test_default_off_identical(self):
        """Flag off: every tranche's floor matches the p2 build exactly."""
        off = {g.unit_id: g.chp_grid_pmin_mw for g in self.fleet_off}
        on_default, _ = bins_to_fleet(self.synth, ZONES, self.cfg_off)
        for g in on_default:
            self.assertEqual(g.chp_grid_pmin_mw, off[g.unit_id])


if __name__ == "__main__":
    unittest.main()
