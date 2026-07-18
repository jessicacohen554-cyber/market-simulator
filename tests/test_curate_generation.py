"""Tests for scripts/data/curate_generation.py.

A tiny *synthetic* raw fixture (one small EIA-930 BA parquet + one PJM
gen-by-fuel CSV) is curated through the real transform + write path and the
result is asserted schema-valid and correctly reconciled. This is deliberately
NOT a full-data run: it exercises the unpivot, the fuel-vocabulary mapping, the
storage/"other" roll-up, the is_renewable handling and the UTC-year
partitioning on a handful of rows.

``clean_io.paths.CLEAN_DIR`` is redirected to a temp dir (as in
tests/test_clean_io.py) so the test never writes the real data/clean tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_generation as cg
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _synthetic_eia930(path: Path) -> None:
    """Write a 3-hour synthetic EIA-930 BA parquet (wide ``NG: <CODE>``).

    Two hours fall in 2024 and one in 2025 (to exercise year partitioning).
    Includes a storage pair (BAT + PS -> one ``storage`` bucket), a geothermal
    code, and a NaN coal value that must be dropped rather than written.
    """
    utc = pd.to_datetime(["2024-06-01 00:00", "2024-06-01 01:00", "2025-06-01 00:00"])
    local = utc - pd.Timedelta(hours=7)  # arbitrary naive local wall clock
    df = pd.DataFrame(
        {
            "UTC time": utc.astype("datetime64[us]"),
            "Local time": local.astype("datetime64[us]"),
            "NG: COL": [100.0, float("nan"), 120.0],  # NaN -> dropped that hour
            "NG: NG": [200.0, 210.0, 220.0],
            "NG: SUN": [10.0, 20.0, 30.0],
            "NG: GEO": [5.0, 6.0, 7.0],
            "NG: BAT": [1.0, 2.0, 3.0],
            "NG: PS": [4.0, 5.0, 6.0],  # BAT + PS -> storage
        }
    )
    df.to_parquet(path)


def _synthetic_pjm(path: Path) -> None:
    """Write a synthetic PJM gen-by-fuel CSV (one UTC hour, 2024).

    ``Other`` (not renewable) + ``Other Renewables`` (renewable) both fold into
    the canonical ``other`` bucket, so its is_renewable must collapse to null;
    ``Solar`` stays renewable.
    """
    rows = [
        ("1/1/2024 5:00:00 AM", "1/1/2024 12:00:00 AM", "Coal", 50, False),
        ("1/1/2024 5:00:00 AM", "1/1/2024 12:00:00 AM", "Solar", 30, True),
        ("1/1/2024 5:00:00 AM", "1/1/2024 12:00:00 AM", "Other", 7, False),
        ("1/1/2024 5:00:00 AM", "1/1/2024 12:00:00 AM", "Other Renewables", 3, True),
    ]
    df = pd.DataFrame(
        rows,
        columns=[
            "datetime_beginning_utc",
            "datetime_beginning_ept",
            "fuel_type",
            "mw",
            "is_renewable",
        ],
    )
    df.to_csv(path, index=False)


class CurateGenerationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.tmp / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    # -- EIA-930 unpivot ----------------------------------------------------
    def test_eia930_unpivot_reconciles_and_validates(self):
        raw = self.tmp / "TEST hourly.parquet"
        _synthetic_eia930(raw)

        df = cg.curate_eia930_ba(raw, "CAISO")
        written = cg.write_by_year(df, "CAISO", source=str(raw))

        # Partitioned into 2024 and 2025 files, both schema-valid round-trips.
        self.assertEqual(
            {p.name for p in written},
            {"generation_2024.parquet", "generation_2025.parquet"},
        )
        for p in written:
            self.assertEqual(validate_clean(p).datatype, "generation")

        g2024 = pd.read_parquet(
            self.tmp / "clean/generation/CAISO/generation_2024.parquet"
        )
        # Canonical vocabulary, SYSTEM zone, EIA carries no renewable flag.
        self.assertEqual(set(g2024["zone"]), {"SYSTEM"})
        self.assertEqual(set(g2024["iso"]), {"CAISO"})
        self.assertTrue(g2024["is_renewable"].isna().all())
        self.assertTrue(set(g2024["fuel"]).issubset(set(cg.EIA_FUEL_MAP.values())))

        # Hour 0: storage = BAT(1) + PS(4) = 5; geothermal present.
        h0 = g2024[
            g2024["interval_start_utc"] == pd.Timestamp("2024-06-01 00:00", tz="UTC")
        ]
        by_fuel = dict(zip(h0["fuel"], h0["generation_mw"]))
        self.assertEqual(by_fuel["storage"], 5.0)
        self.assertEqual(by_fuel["geothermal"], 5.0)
        self.assertEqual(by_fuel["coal"], 100.0)

        # Hour 1 had NaN coal -> no coal row that hour (dropped, not zero/null).
        h1 = g2024[
            g2024["interval_start_utc"] == pd.Timestamp("2024-06-01 01:00", tz="UTC")
        ]
        self.assertNotIn("coal", set(h1["fuel"]))
        self.assertEqual(dict(zip(h1["fuel"], h1["generation_mw"]))["storage"], 7.0)

        # Local wall clock carried tz-naive.
        self.assertIsNone(g2024["interval_start_local"].dt.tz)

    def test_eia930_unmapped_code_raises(self):
        raw = self.tmp / "BAD hourly.parquet"
        pd.DataFrame(
            {
                "UTC time": pd.to_datetime(["2024-06-01 00:00"]).astype(
                    "datetime64[us]"
                ),
                "Local time": pd.to_datetime(["2024-05-31 17:00"]).astype(
                    "datetime64[us]"
                ),
                "NG: ZZZ": [1.0],  # no canonical home
            }
        ).to_parquet(raw)
        with self.assertRaises(ValueError):
            cg.curate_eia930_ba(raw, "CAISO")

    # -- PJM ---------------------------------------------------------------
    def test_pjm_rollup_and_renewable_flag(self):
        raw = self.tmp / "PJM_2024_gen_by_fuel.csv"
        _synthetic_pjm(raw)

        df = cg.curate_pjm([raw])
        written = cg.write_by_year(df, "PJM", source=str(raw))
        self.assertEqual(len(written), 1)
        self.assertEqual(validate_clean(written[0]).datatype, "generation")

        g = pd.read_parquet(written[0])
        by_fuel = dict(zip(g["fuel"], g["generation_mw"]))
        # Other (7) + Other Renewables (3) roll up into one canonical "other".
        self.assertEqual(by_fuel["other"], 10.0)
        self.assertEqual(by_fuel["solar"], 30.0)

        ren = dict(zip(g["fuel"], g["is_renewable"]))
        self.assertTrue(bool(ren["solar"]))
        self.assertFalse(bool(ren["coal"]))
        # Mixed renewable/non-renewable folded into "other" -> null flag.
        self.assertTrue(pd.isna(ren["other"]))

        # UTC at 5:00 falls in 2024; Eastern local is the prior midnight.
        self.assertEqual(g["interval_start_utc"].dt.year.unique().tolist(), [2024])
        self.assertEqual(set(g["zone"]), {"SYSTEM"})


if __name__ == "__main__":
    unittest.main()
