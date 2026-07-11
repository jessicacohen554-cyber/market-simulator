"""Tests for the storage-as-awards intake on a tiny synthetic fixture.

Writes a minimal CAISO Daily-Energy-Storage-Report-shaped xlsx into a tmp raw
tree, runs ``curate``, and asserts the written Parquet is schema-valid and the
reconciliation is correct: EN/SOC rows excluded, RTPD 15-minute intervals
hourly-averaged, product/class/market vocabulary mapped, and the DST fall-back
25-hour day producing 25 distinct physical UTC hours. NOT a full-data run:
CLEAN_DIR is redirected to a tmp dir so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_storage_as_awards as curate_saw
from scripts.lib import clean_io
from scripts.lib import storage_as_awards as saw
from scripts.lib.storage_as_awards import caiso as saw_caiso
from scripts.lib.clean_io import validate_clean


def _fixture_frame() -> pd.DataFrame:
    rows = []
    # IFM hourly awards, one ordinary day: HE1 and HE2.
    for hour, ru in ((1, 100.0), (2, 150.0)):
        rows.append(("2024-07-01", hour, 1, "IFM", "LESR", "RU", ru))
        rows.append(("2024-07-01", hour, 1, "IFM", "LESR", "SR", 50.0))
    # An energy-schedule and a state-of-charge row: both must be excluded.
    rows.append(("2024-07-01", 1, 1, "IFM", "LESR", "EN", -400.0))
    rows.append(("2024-07-01", 1, 1, "RTD", "LESR", "SOC", 5000.0))
    # RTPD 15-minute intervals -> hourly mean 20.
    for interval, mw in ((1, 10.0), (2, 20.0), (3, 20.0), (4, 30.0)):
        rows.append(("2024-07-01", 1, interval, "RTPD", "LESR", "RD", mw))
    # Hybrid class, mapped separately.
    rows.append(("2024-07-01", 1, 1, "IFM", "HYBD", "NR", 5.0))
    # DST fall-back day: 25 physical hours; HE25 must land 1h after HE24.
    for hour in (24, 25):
        rows.append(("2024-11-03", hour, 1, "IFM", "LESR", "RU", float(hour)))
    # DST spring-forward day: clock label HE3 does not exist; HE2 and HE4 are
    # ADJACENT physical hours.
    for hour in (2, 4):
        rows.append(("2024-03-10", hour, 1, "IFM", "LESR", "SR", float(hour)))
    return pd.DataFrame(
        rows,
        columns=[
            "TRADE_DATE",
            "HOUR",
            "INTERVAL",
            "MARKET",
            "RES_TYPE",
            "TYPE",
            "VALUE",
        ],
    )


class TestCurateStorageAsAwards(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        d = self.raw_root / saw_caiso.RAW_SUBDIR
        d.mkdir(parents=True)
        _fixture_frame().to_excel(
            d / "storage-report-2024q9.xlsx", sheet_name="market_output", index=False
        )
        # Redirect CLEAN_DIR so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_reconciles_and_validates(self) -> None:
        written = curate_saw.curate(raw_root=self.raw_root, isos=["CAISO"])
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        df = pd.read_parquet(written[0])

        # EN/SOC excluded; only award products present.
        self.assertTrue(set(df["product"]) <= saw.PRODUCT_VOCAB)
        self.assertTrue(set(df["resource_class"]) <= saw.RESOURCE_CLASS_VOCAB)

        # IFM HE1 2024-07-01: local 00:00 PDT == 07:00 UTC.
        he1 = df[
            (df["market"] == "DAM")
            & (df["product"] == "reg_up")
            & (df["resource_class"] == "battery")
            & (df["interval_start_utc"] == pd.Timestamp("2024-07-01 07:00", tz="UTC"))
        ]
        self.assertEqual(len(he1), 1)
        self.assertAlmostEqual(float(he1["award_mw"].iloc[0]), 100.0)

        # RTPD intervals hourly-averaged onto RTM.
        rtm = df[(df["market"] == "RTM") & (df["product"] == "reg_down")]
        self.assertEqual(len(rtm), 1)
        self.assertAlmostEqual(float(rtm["award_mw"].iloc[0]), 20.0)

        # Hybrid class mapped.
        hyb = df[df["resource_class"] == "hybrid"]
        self.assertEqual(len(hyb), 1)
        self.assertAlmostEqual(float(hyb["award_mw"].iloc[0]), 5.0)

        # DST fall-back day: HE24 and HE25 are consecutive physical UTC hours.
        fb = df[
            (df["product"] == "reg_up")
            & (df["interval_start_local"].dt.strftime("%Y-%m-%d") == "2024-11-03")
            & (df["award_mw"].isin([24.0, 25.0]))
        ].sort_values("award_mw")
        self.assertEqual(len(fb), 2)
        delta = fb["interval_start_utc"].iloc[1] - fb["interval_start_utc"].iloc[0]
        self.assertEqual(delta, pd.Timedelta(hours=1))

        # DST spring-forward day: HE2 and HE4 (HE3 skipped) are ADJACENT.
        sf = df[
            (df["product"] == "spin") & (df["award_mw"].isin([2.0, 4.0]))
        ].sort_values("award_mw")
        self.assertEqual(len(sf), 2)
        delta = sf["interval_start_utc"].iloc[1] - sf["interval_start_utc"].iloc[0]
        self.assertEqual(delta, pd.Timedelta(hours=1))
        # No duplicate physical hours anywhere in the partition.
        key = ["iso", "resource_class", "market", "product", "interval_start_utc"]
        self.assertFalse(df.duplicated(key).any())

    def test_skip_when_raw_absent(self) -> None:
        with TemporaryDirectory() as empty:
            written = curate_saw.curate(raw_root=Path(empty), isos=["CAISO"])
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
