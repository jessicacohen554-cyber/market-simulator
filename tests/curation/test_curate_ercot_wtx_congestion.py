"""Tests for the ERCOT West Texas Export corridor curtailment-share driver.

Covers scripts/data/curate_ercot_wtx_congestion.py (NP6-86 SCED congestion geo-
attributed via a synthetic ERCOT SP/bus load-zone mapping) and the solve-time
reader market_sim.data.curtailment_share. Builds a tiny synthetic NP6-86 parquet
plus a synthetic Settlement Points zip against a tmp raw root with CLEAN_DIR
redirected (as in tests/curation/test_clean_io.py), and asserts:

* a LZ_WEST-endpoint nodal constraint and the WESTEX/PNHNDL export GTCs count
  toward the West-corridor congestion fraction, while a LZ_SOUTH constraint (Rio
  Grande Valley / Eagle Ford) is excluded;
* the reader curtails only the West/Panhandle zones and leaves the rest at 1.0,
  and depth=0 is inert (the zero-forcing ablation).
"""

import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts.data import curate_ercot_wtx_congestion as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_NP686_COLS = [
    "SCEDTimeStamp",
    "ConstraintName",
    "ShadowPrice",
    "FromStation",
    "ToStation",
    "FromStationkV",
    "ToStationkV",
]


def _np686_row(ts, name, shadow, f_st, t_st, fkv=138.0, tkv=138.0):
    return {
        "SCEDTimeStamp": ts,
        "ConstraintName": name,
        "ShadowPrice": shadow,
        "FromStation": f_st,
        "ToStation": t_st,
        "FromStationkV": fkv,
        "ToStationkV": tkv,
    }


class CurateWtxCongestionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / "iso-specific-transmission").mkdir(parents=True)
        (self.raw_root / "ercot-settlement-points").mkdir(parents=True)

        # Clock hour 05:00 (position 5): interval A binds a West nodal
        # (ODEHV->YARBR, both LZ_WEST) + the WESTEX GTC + a South nodal
        # (RIOHONDO->LAPALMA, LZ_SOUTH, excluded); interval B binds nothing West
        # (a slack WESTEX row shadow=0). -> n_intervals=2, n_binding_west=1.
        rows = [
            _np686_row("01/01/2023 05:05:13", "6520__E", 12.0, "ODEHV", "YARBR"),
            _np686_row("01/01/2023 05:05:13", "WESTEX", 80.0, None, None, 0.0, 0.0),
            _np686_row(
                "01/01/2023 05:05:13", "RIOHONDO_1", 40.0, "RIOHONDO", "LAPALMA"
            ),
            _np686_row("01/01/2023 05:10:13", "WESTEX", 0.0, None, None, 0.0, 0.0),
            _np686_row(
                "01/01/2023 05:10:13", "RIOHONDO_1", 30.0, "RIOHONDO", "LAPALMA"
            ),
        ]
        pd.DataFrame(rows, columns=_NP686_COLS).to_parquet(
            self.raw_root
            / "iso-specific-transmission"
            / "SCEDBTCNP686_SCEDBTCNP686_2023.parquet",
            index=False,
        )

        # Synthetic Settlement Points bundle: SUBSTATION -> SETTLEMENT_LOAD_ZONE.
        sp = pd.DataFrame(
            {
                "SUBSTATION": ["ODEHV", "YARBR", "RIOHONDO", "LAPALMA"],
                "SETTLEMENT_LOAD_ZONE": ["LZ_WEST", "LZ_WEST", "LZ_SOUTH", "LZ_SOUTH"],
            }
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "SP_List_EB_Mapping/Settlement_Points_test.csv",
                sp.to_csv(index=False),
            )
        (
            self.raw_root
            / "ercot-settlement-points"
            / "SP_List_and_EB_Mapping_test.zip"
        ).write_bytes(buf.getvalue())

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_attributes_west_corridor_only(self):
        written = curate_mod.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        df = pd.read_parquet(written[0]).set_index("hour")
        # Hour 5: 2 SCED executions, 1 with a West-corridor binding -> 0.5.
        self.assertEqual(int(df.loc[5, "n_intervals"]), 2)
        self.assertEqual(int(df.loc[5, "n_binding_west"]), 1)
        self.assertAlmostEqual(float(df.loc[5, "congestion_frac"]), 0.5, places=6)
        self.assertAlmostEqual(
            float(df.loc[5, "interface_binding_frac"]), 0.5, places=6
        )
        # The LZ_SOUTH (Rio Grande Valley) constraint is never counted, even in
        # interval B where it is the only binding row.
        self.assertEqual(int(df["n_binding_west"].sum()), 1)
        # Dense 8760, zero elsewhere.
        self.assertEqual(len(df), 8760)
        self.assertEqual(int((df["congestion_frac"] > 0).sum()), 1)

    def test_isos_gate_is_noop_for_non_ercot(self):
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root, isos=["CAISO"]), [])


class CurtailShareReaderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.ref = Path(self._tmp.name)
        # A trivial share table: full congestion in every cell so depth maps
        # directly to the curtailed fraction.
        cells = [
            {
                "net_load_decile": d,
                "hour_of_day": h,
                "season": s,
                "congestion_share": 1.0,
            }
            for d in range(10)
            for h in range(24)
            for s in range(4)
        ]
        pd.DataFrame(cells).to_csv(
            self.ref / "ercot_wtx_curtailment_share.csv", index=False
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_multipliers_curtail_only_corridor(self):
        from market_sim.data.curtailment_share import wtx_curtail_multipliers

        nl = np.linspace(20000, 60000, 8760)
        zones = ["North", "West", "Panhandle", "Houston", "South"]
        wind, solar = wtx_curtail_multipliers(
            nl, zones, depth_wind=0.10, depth_solar=0.20, reference_dir=self.ref
        )
        self.assertEqual(wind.shape, (5, 8760))
        # Corridor rows curtail (share==1 everywhere -> mult == 1-depth).
        np.testing.assert_allclose(wind[zones.index("West")], 0.90)
        np.testing.assert_allclose(wind[zones.index("Panhandle")], 0.90)
        np.testing.assert_allclose(solar[zones.index("West")], 0.80)
        # Non-corridor rows are untouched.
        np.testing.assert_allclose(wind[zones.index("North")], 1.0)
        np.testing.assert_allclose(solar[zones.index("Houston")], 1.0)

    def test_zero_depth_is_inert(self):
        from market_sim.data.curtailment_share import wtx_curtail_multipliers

        nl = np.linspace(20000, 60000, 8760)
        zones = ["North", "West", "Panhandle"]
        wind, solar = wtx_curtail_multipliers(
            nl, zones, depth_wind=0.0, depth_solar=0.0, reference_dir=self.ref
        )
        np.testing.assert_allclose(wind, 1.0)
        np.testing.assert_allclose(solar, 1.0)

    def test_missing_table_returns_none(self):
        from market_sim.data.curtailment_share import wtx_curtail_multipliers

        missing = Path(self._tmp.name) / "nope"
        self.assertIsNone(
            wtx_curtail_multipliers(
                np.zeros(8760),
                ["West"],
                depth_wind=0.1,
                depth_solar=0.1,
                reference_dir=missing,
            )
        )


class FamilySplitTest(unittest.TestCase):
    """The ercot-165 diurnal-family split rule (curate side).

    The rule is a threshold-free LIFT test against the year's measured
    SCED-execution exposure, so these fixtures pin the boundary at the null:
    an element binding only in daytime hours is D, one binding only overnight
    is N, and PNHNDL is held out of the split entirely.
    """

    def _rows(self):
        rows = []
        # Exposure: one execution in every hour of 01/01 -> daytime (h9-17)
        # exposure is 9/24. DAY_ELEM binds h10-h16 only (day_share 1.0 -> D);
        # NIGHT_ELEM binds h22-h23 only (day_share 0.0 -> N); PNHNDL binds at
        # h12 but is excluded from the split by FAMILY_SPLIT_EXCLUDE.
        for hh in range(24):
            ts = f"01/01/2023 {hh:02d}:05:13"
            rows.append(_np686_row(ts, "FILLER_1", 0.0, "ODEHV", "YARBR"))
            if 10 <= hh <= 16:
                rows.append(_np686_row(ts, "DAY_ELEM", 15.0, "ODEHV", "YARBR"))
            if hh >= 22:
                rows.append(_np686_row(ts, "NIGHT_ELEM", 15.0, "ODEHV", "YARBR"))
            if hh == 12:
                rows.append(_np686_row(ts, "PNHNDL", 55.0, None, None, 0.0, 0.0))
        return rows

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / "iso-specific-transmission").mkdir(parents=True)
        (self.raw_root / "ercot-settlement-points").mkdir(parents=True)
        pd.DataFrame(self._rows(), columns=_NP686_COLS).to_parquet(
            self.raw_root
            / "iso-specific-transmission"
            / "SCEDBTCNP686_SCEDBTCNP686_2023.parquet",
            index=False,
        )
        sp = pd.DataFrame(
            {
                "SUBSTATION": ["ODEHV", "YARBR"],
                "SETTLEMENT_LOAD_ZONE": ["LZ_WEST", "LZ_WEST"],
            }
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "SP_List_EB_Mapping/Settlement_Points_test.csv", sp.to_csv(index=False)
            )
        (
            self.raw_root / "ercot-settlement-points" / "SP_List_and_EB_Mapping_t.zip"
        ).write_bytes(buf.getvalue())
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_lift_rule_separates_day_and_night_elements(self):
        written = curate_mod.curate(raw_root=self.raw_root)
        validate_clean(written[0])
        df = pd.read_parquet(written[0]).set_index("hour")
        # h12: the daytime element AND PNHNDL bind; the overnight one does not.
        self.assertEqual(int(df.loc[12, "n_binding_family_d"]), 1)
        self.assertEqual(int(df.loc[12, "n_binding_family_n"]), 0)
        self.assertEqual(int(df.loc[12, "n_binding_pnhndl"]), 1)
        # h23: only the overnight element.
        self.assertEqual(int(df.loc[23, "n_binding_family_d"]), 0)
        self.assertEqual(int(df.loc[23, "n_binding_family_n"]), 1)
        # PNHNDL is never pooled into either family.
        self.assertEqual(int(df["n_binding_family_d"].sum()), 7)  # h10-h16
        self.assertEqual(int(df["n_binding_family_n"].sum()), 2)  # h22-h23
        self.assertEqual(int(df["n_binding_pnhndl"].sum()), 1)
        # The pooled column still counts every corridor element (families+PNHNDL).
        self.assertEqual(int(df["n_binding_west"].sum()), 9)

    def test_assign_families_is_threshold_free(self):
        df = curate_mod.pd.DataFrame(self._rows(), columns=_NP686_COLS)
        df = df.assign(ts=curate_mod._sced_ts_to_cst(df))
        df = df.assign(binding=df["ShadowPrice"] > 0)
        mask = ~df["ConstraintName"].isin(curate_mod.FAMILY_SPLIT_EXCLUDE)
        fams, exposure = curate_mod.assign_families(df, mask)
        self.assertAlmostEqual(exposure, 9 / 24, places=6)
        self.assertEqual(fams["DAY_ELEM"], "D")
        self.assertEqual(fams["NIGHT_ELEM"], "N")
        self.assertNotIn("PNHNDL", fams)


class UnpooledReaderTest(unittest.TestCase):
    """The ercot-165 unpooled reader: per-zone ownership, two depths, no new DOF."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.ref = Path(self._tmp.name)
        # D = 0.5, N = 0.5 (West sees the SUM = 1.0), PNHNDL = 1.0, in every
        # cell, so depth maps directly onto the curtailed fraction.
        shares = {"D": 0.5, "N": 0.5, "PNHNDL": 1.0}
        cells = [
            {
                "family": fam,
                "net_load_decile": d,
                "hour_of_day": h,
                "season": s,
                "congestion_share": v,
            }
            for fam, v in shares.items()
            for d in range(10)
            for h in range(24)
            for s in range(4)
        ]
        pd.DataFrame(cells).to_csv(
            self.ref / "ercot_wtx_curtailment_share_family.csv", index=False
        )
        self.nl = np.linspace(20000, 60000, 8760)
        self.zones = ["North", "West", "Panhandle", "Houston"]

    def tearDown(self):
        self._tmp.cleanup()

    def _mult(self, owner, dw=0.10, ds=0.20):
        from market_sim.data.curtailment_share import wtx_family_curtail_multipliers

        return wtx_family_curtail_multipliers(
            self.nl,
            self.zones,
            depth_wind=dw,
            depth_solar=ds,
            panhandle_owner=owner,
            reference_dir=self.ref,
        )

    def test_tie_arm_leaves_panhandle_to_the_tie(self):
        wind, solar = self._mult("tie")
        # West takes D+N = 1.0 -> mult = 1 - depth.
        np.testing.assert_allclose(wind[self.zones.index("West")], 0.90)
        np.testing.assert_allclose(solar[self.zones.index("West")], 0.80)
        # Panhandle carries NO driver ceiling: the endogenous tie owns it.
        np.testing.assert_allclose(wind[self.zones.index("Panhandle")], 1.0)
        np.testing.assert_allclose(solar[self.zones.index("Panhandle")], 1.0)
        # Non-corridor zones are untouched in both arms.
        np.testing.assert_allclose(wind[self.zones.index("North")], 1.0)

    def test_share_arm_gives_panhandle_its_own_measured_shape(self):
        wind, solar = self._mult("share")
        np.testing.assert_allclose(wind[self.zones.index("West")], 0.90)
        # Panhandle takes the PNHNDL share (1.0 here) -> 1 - depth.
        np.testing.assert_allclose(wind[self.zones.index("Panhandle")], 0.90)
        np.testing.assert_allclose(solar[self.zones.index("Panhandle")], 0.80)
        np.testing.assert_allclose(wind[self.zones.index("Houston")], 1.0)

    def test_zero_depth_is_inert_in_both_arms(self):
        for owner in ("tie", "share"):
            wind, solar = self._mult(owner, dw=0.0, ds=0.0)
            np.testing.assert_allclose(wind, 1.0)
            np.testing.assert_allclose(solar, 1.0)

    def test_unknown_owner_raises(self):
        with self.assertRaises(ValueError):
            self._mult("both")

    def test_missing_family_table_returns_none(self):
        from market_sim.data.curtailment_share import wtx_family_curtail_multipliers

        self.assertIsNone(
            wtx_family_curtail_multipliers(
                np.zeros(8760),
                ["West"],
                depth_wind=0.1,
                depth_solar=0.1,
                panhandle_owner="tie",
                reference_dir=Path(self._tmp.name) / "nope",
            )
        )

    def test_default_config_keeps_the_pooled_path(self):
        """Default-off: a stock ScenarioConfig must not select the unpooled path."""
        from market_sim.config.scenarios import ScenarioConfig

        cfg = ScenarioConfig()
        self.assertFalse(cfg.ercot_wtx_curtail_unpooled)
        self.assertEqual(cfg.ercot_wtx_panhandle_owner, "tie")


if __name__ == "__main__":
    unittest.main()
