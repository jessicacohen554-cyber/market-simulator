"""Tests for the ERCOT West Texas Export corridor curtailment-share driver.

Covers scripts/data/curate_ercot_wtx_congestion.py (NP6-86 SCED congestion geo-
attributed via a synthetic ERCOT SP/bus load-zone mapping) and the solve-time
reader market_sim.data.curtailment_share. Builds a tiny synthetic NP6-86 parquet
plus a synthetic Settlement Points zip against a tmp raw root with CLEAN_DIR
redirected (as in tests/test_clean_io.py), and asserts:

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


if __name__ == "__main__":
    unittest.main()
