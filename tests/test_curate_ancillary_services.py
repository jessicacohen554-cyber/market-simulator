"""Tests for scripts/data/curate_ancillary_services.py.

Builds a tiny synthetic raw fixture (one small file per ISO source layout),
curates it into a redirected temp clean tree, and asserts the output is
schema-valid and that each ISO's products land in the right reconciled columns.
This is deliberately NOT a full-data run: it exercises the reconciliation
mapping, the tz handling and the clean-write contract on a handful of rows.
"""

import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.data import curate_ancillary_services as cas  # noqa: E402
from scripts.lib import clean_io  # noqa: E402


def _write_nyiso(raw_root: Path) -> None:
    d = raw_root / "NYISO-AS"
    d.mkdir(parents=True, exist_ok=True)
    # Two zones, two hours, day-ahead. Eastern wall-clock hour-beginning.
    pd.DataFrame(
        {
            "Time Stamp": [
                "2024-06-01 00:00:00",
                "2024-06-01 00:00:00",
                "2024-06-01 01:00:00",
                "2024-06-01 01:00:00",
            ],
            "Name": ["CAPITL", "N.Y.C.", "CAPITL", "N.Y.C."],
            "spin_10": [1.0, 2.0, 3.0, 4.0],
            "nonsync_10": [0.5, 0.6, 0.7, 0.8],
            "op_30": [10.0, 11.0, 12.0, 13.0],
            "reg_cap": [20.0, 21.0, 22.0, 23.0],
        }
    ).to_csv(d / "NYISO_as_da_2024.csv", index=False)


def _write_pjm(raw_root: Path) -> None:
    d = raw_root / "PJM-AS"
    d.mkdir(parents=True, exist_ok=True)
    # Day-ahead long format: one hour, RTO (SYSTEM) products.
    pd.DataFrame(
        {
            "datetime_beginning_utc": ["1/1/2024 5:00:00 AM"] * 4,
            "datetime_beginning_ept": ["1/1/2024 12:00:00 AM"] * 4,
            "ancillary_service": [
                "PJM RTO Synchronized Reserve",
                "PJM RTO Thirty Minutes Reserve",
                "PJM RTO Primary Reserve",  # aggregate -> intentionally dropped
                "Mid-Atlantic/Dominion Synchronized Reserve",
            ],
            "unit": ["price", "price", "price", "price"],
            "value": [7.0, 30.0, 99.0, 5.0],
            "row_is_current": [True, True, True, True],
            "version_nbr": [1, 1, 1, 1],
        }
    ).to_parquet(d / "da_ancillary_services_2024.parquet")
    # Real-time long format: regulation + non-sync + a non-price ratio row.
    pd.DataFrame(
        {
            "datetime_beginning_utc": ["1/1/2024 5:00:00 AM"] * 3,
            "datetime_beginning_ept": ["1/1/2024 12:00:00 AM"] * 3,
            "ancillary_service": [
                "RTO Regulation Capability",
                "RTO Non-Synchronized Reserve",
                "RTO Mileage Ratio",  # unit Ratio -> dropped
            ],
            "unit": ["Price", "Price", "Ratio"],
            "value": [22.0, 1.5, 3.4],
            "row_is_current": [True, True, True],
            "version_nbr": [1, 1, 1],
        }
    ).to_parquet(d / "ancillary_services_2024.parquet")


def _write_ercot(raw_root: Path) -> None:
    # Cleared MW (2-day disclosure) under data/raw/ercot.
    ed = raw_root / "ercot"
    ed.mkdir(parents=True, exist_ok=True)
    for code, mw in (("REGUP", 100.0), ("RRSPFR", 200.0), ("NSPIN", 300.0)):
        pd.DataFrame(
            {
                "Delivery Date": ["01/15/2024", "01/15/2024"],
                "Hour Ending": [1, 2],
                f"Total Cleared AS - {code}": [mw, mw + 1],
            }
        ).to_parquet(ed / f"2_DAY_AS_DISCLOSURE_2d_Cleared_DAM_AS_{code}_2024.parquet")

    # MCPC prices (60-day awards JSON zip) under data/raw/ercot-AS.
    asd = raw_root / "ercot-AS"
    asd.mkdir(parents=True, exist_ok=True)
    fields = [
        {"name": "deliveryDate"},
        {"name": "hourEnding"},
        {"name": "ASType"},
        {"name": "MCPC"},
    ]
    # Two QSEs share the uniform MCPC for each (date, hour, ASType).
    data = [
        ["2024-01-15", 1, "REGUP", 9.0],
        ["2024-01-15", 1, "REGUP", 9.0],
        ["2024-01-15", 1, "NSPIN", 4.0],
        ["2024-01-15", 2, "REGUP", 9.5],
    ]
    payload = {"fields": fields, "data": data}
    zpath = asd / "00099999.np3-966-er.60d_dam_as_only_awards.20240316.000000_json.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("awards.json", json.dumps(payload))


class CurateAncillaryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.raw = self.tmp / "raw"
        self.raw.mkdir()
        _write_nyiso(self.raw)
        _write_pjm(self.raw)
        _write_ercot(self.raw)
        # Redirect the clean tree so writes never touch the real repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.tmp / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _read(self, iso: str, market: str, year: int) -> pd.DataFrame:
        path = clean_io.paths.clean_path(
            "ancillary-services", iso=iso, year=year, market=market
        )
        return pd.read_parquet(path)

    def test_curate_writes_schema_valid_partitions(self):
        written = cas.curate(raw_root=self.raw)
        self.assertTrue(written)
        # Every written file round-trips against its embedded schema.
        for path in written:
            schema = clean_io.validate_clean(path)
            self.assertEqual(schema.datatype, "ancillary-services")
        # Partitioned by iso / market / year.
        parts = {(p.parts[-3], p.parts[-2], p.name) for p in written}
        self.assertIn(("NYISO", "DAM", "ancillary-services_2024.parquet"), parts)
        self.assertIn(("PJM", "DAM", "ancillary-services_2024.parquet"), parts)
        self.assertIn(("PJM", "RTM", "ancillary-services_2024.parquet"), parts)
        self.assertIn(("ERCOT", "DAM", "ancillary-services_2024.parquet"), parts)

    def test_nyiso_reconciliation_and_tz(self):
        cas.curate(raw_root=self.raw, isos=["NYISO"])
        df = self._read("NYISO", "DAM", 2024)
        row = df[(df["zone"] == "CAPITL")].sort_values("interval_start_utc").iloc[0]
        # spin_10->spin, nonsync_10->nonspin, op_30->supp_30min, reg_cap->reg_up.
        self.assertAlmostEqual(row["spin_price_usd_per_mw"], 1.0)
        self.assertAlmostEqual(row["nonspin_price_usd_per_mw"], 0.5)
        self.assertAlmostEqual(row["supp_30min_price_usd_per_mw"], 10.0)
        self.assertAlmostEqual(row["reg_up_price_usd_per_mw"], 20.0)
        # NYISO has no cleared MW.
        self.assertTrue(df["spin_mw"].isna().all())
        # 00:00 EDT (summer) -> 04:00 UTC; local carried tz-naive.
        self.assertEqual(
            row["interval_start_utc"], pd.Timestamp("2024-06-01 04:00:00", tz="UTC")
        )
        self.assertEqual(
            row["interval_start_local"], pd.Timestamp("2024-06-01 00:00:00")
        )

    def test_pjm_pivot_zones_and_dropped_products(self):
        cas.curate(raw_root=self.raw, isos=["PJM"])
        da = self._read("PJM", "DAM", 2024)
        self.assertEqual(set(da["zone"].unique()), {"SYSTEM", "MAD"})
        sysrow = da[da["zone"] == "SYSTEM"].iloc[0]
        self.assertAlmostEqual(sysrow["spin_price_usd_per_mw"], 7.0)
        self.assertAlmostEqual(sysrow["supp_30min_price_usd_per_mw"], 30.0)
        # Primary Reserve is an aggregate, not in the taxonomy -> no column for it.
        self.assertNotIn("primary", da.columns)
        madrow = da[da["zone"] == "MAD"].iloc[0]
        self.assertAlmostEqual(madrow["spin_price_usd_per_mw"], 5.0)

        rt = self._read("PJM", "RTM", 2024)
        rtrow = rt[rt["zone"] == "SYSTEM"].iloc[0]
        # Regulation Capability -> reg_up; Non-Synchronized -> nonspin; Ratio dropped.
        self.assertAlmostEqual(rtrow["reg_up_price_usd_per_mw"], 22.0)
        self.assertAlmostEqual(rtrow["nonspin_price_usd_per_mw"], 1.5)
        # No reg_down for PJM.
        self.assertTrue(rt["reg_down_price_usd_per_mw"].isna().all())

    def test_ercot_mcpc_joined_to_mw(self):
        cas.curate(raw_root=self.raw, isos=["ERCOT"])
        df = self._read("ERCOT", "DAM", 2024)
        self.assertEqual(set(df["zone"].unique()), {"SYSTEM"})
        first = df.sort_values("interval_start_utc").iloc[0]
        # MW from cleared disclosure: REGUP->reg_up, RRSPFR->spin, NSPIN->nonspin.
        self.assertAlmostEqual(first["reg_up_mw"], 100.0)
        self.assertAlmostEqual(first["spin_mw"], 200.0)
        self.assertAlmostEqual(first["nonspin_mw"], 300.0)
        # MCPC prices from the awards zip (uniform across the two QSE rows).
        self.assertAlmostEqual(first["reg_up_price_usd_per_mw"], 9.0)
        self.assertAlmostEqual(first["nonspin_price_usd_per_mw"], 4.0)
        # No RRS price was published -> spin price stays null.
        self.assertTrue(pd.isna(first["spin_price_usd_per_mw"]))
        # Hour Ending 1 = 00:00 CST -> 06:00 UTC (Jan, no DST).
        self.assertEqual(
            first["interval_start_utc"], pd.Timestamp("2024-01-15 06:00:00", tz="UTC")
        )

    def test_idempotent_rerun(self):
        first = cas.curate(raw_root=self.raw, isos=["NYISO"])
        second = cas.curate(raw_root=self.raw, isos=["NYISO"])
        self.assertEqual(sorted(first), sorted(second))
        for path in second:
            clean_io.validate_clean(path)


if __name__ == "__main__":
    unittest.main()
