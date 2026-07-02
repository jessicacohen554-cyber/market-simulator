"""Tests for scripts/curate_gtc_limits.py and the market_sim.data.gtc seam.

Builds a tiny synthetic NP6-86 monthly archive (outer zip -> daily zip ->
per-interval CSVs, the Data Portal bundle layout), runs ``curate`` against a
tmp raw root with CLEAN_DIR redirected (as in tests/test_clean_io.py), and
asserts the written Parquet is schema-valid and the hourly aggregation
(GTC-row filter, active/binding counts, DST-safe clock mapping) is correct.
Then exercises the consumer: :func:`market_sim.data.gtc.ercot_gtc_ttc_hourly`
must map PNHNDL/WESTEX onto the ERCOT links with the measured hourly mean on
active hours and the static derived rating on unobserved hours, keep unmapped
links static, and return the static array as the import-direction bound.
"""

import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from scripts import curate_gtc_limits
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_HEADER = (
    "SCEDTimeStamp,RepeatedHourFlag,ConstraintID,ConstraintName,"
    "ContingencyName,ShadowPrice,MaxShadowPrice,Limit,Value,ViolatedMW,"
    "FromStation,ToStation,FromStationkV,ToStationkV,CCTStatus"
)


def _interval_csv(ts: str, rows: list[tuple[str, float, float]]) -> bytes:
    """One NP6-86 interval CSV: (name, shadow, limit) rows + one non-GTC row."""
    lines = [_HEADER]
    for name, shadow, limit in rows:
        # GTC rows carry an empty FromStation/ToStation.
        lines.append(
            f"{ts},N,19,{name},BASE CASE,{shadow},5251,{limit},{limit},0.0"
            f",,,0,0,NONCOMP"
        )
    # A line-level (non-GTC) constraint that must be filtered out.
    lines.append(
        f"{ts},N,8,SOME_LINE_A,DWAP_BI5,10.0,4500,1311.5,1311.5,0.0,"
        f"JN,BI,345,345,NONCOMP"
    )
    return ("\n".join(lines) + "\n").encode()


def _monthly_archive(path: Path, intervals: dict[str, bytes]) -> None:
    """Write outer-zip(daily-zip(csv...)) exactly like a Data Portal bundle."""
    daily = io.BytesIO()
    with zipfile.ZipFile(daily, "w") as dz:
        for stamp, payload in intervals.items():
            dz.writestr(f"cdr.00012302.{stamp}.SCEDBTCNP686.csv", payload)
    with zipfile.ZipFile(path, "w") as oz:
        oz.writestr("day1.zip", daily.getvalue())


class CurateGtcLimitsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        arch_dir = self.raw_root / "iso-specific-transmission"
        arch_dir.mkdir(parents=True)

        # Hour 01/01/2023 05:00 local -> clock position 5. Two PNHNDL
        # intervals (one binding, one merely active) and one WESTEX binding
        # interval; a second hour (06:00, position 6) with one PNHNDL row.
        intervals = {
            "20230101.050500": _interval_csv(
                "01/01/2023 05:05:13",
                [("PNHNDL", 25.0, 2400.0), ("WESTEX", 100.0, 9000.0)],
            ),
            "20230101.051000": _interval_csv(
                "01/01/2023 05:10:13", [("PNHNDL", 0.0, 2600.0)]
            ),
            "20230101.060500": _interval_csv(
                "01/01/2023 06:05:13", [("PNHNDL", 50.0, 3000.0)]
            ),
        }
        _monthly_archive(arch_dir / "SCEDBTCNP686_202301.zip", intervals)

        # Redirect CLEAN_DIR so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curated(self) -> pd.DataFrame:
        written = curate_gtc_limits.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        return pd.read_parquet(written[0])

    def test_hourly_aggregation(self):
        df = self._curated()
        # Only GTC rows survive; the line constraint is filtered.
        self.assertEqual(set(df["gtc"]), {"PNHNDL", "WESTEX"})

        pn5 = df[(df["gtc"] == "PNHNDL") & (df["hour"] == 5)].iloc[0]
        self.assertEqual(pn5["n_active"], 2)
        self.assertEqual(pn5["n_binding"], 1)
        self.assertAlmostEqual(pn5["limit_mean_mw"], 2500.0)
        self.assertAlmostEqual(pn5["limit_min_mw"], 2400.0)
        self.assertAlmostEqual(pn5["shadow_price_mean"], 25.0)

        pn6 = df[(df["gtc"] == "PNHNDL") & (df["hour"] == 6)].iloc[0]
        self.assertEqual(pn6["n_active"], 1)
        self.assertAlmostEqual(pn6["limit_mean_mw"], 3000.0)

        wx = df[df["gtc"] == "WESTEX"]
        self.assertEqual(len(wx), 1)
        self.assertEqual(wx.iloc[0]["hour"], 5)

    def test_iso_gate_no_op(self):
        self.assertEqual(curate_gtc_limits.curate(self.raw_root, isos=["PJM"]), [])

    def test_consumer_hourly_ttc(self):
        self._curated()
        from market_sim.data.gtc import ercot_gtc_ttc_hourly

        iso_config = get_iso_config("ERCOT")
        links = [(lk.from_zone, lk.to_zone) for lk in iso_config.links]
        static = np.array([lk.ttc_mw for lk in iso_config.links])
        hours = 24
        out = ercot_gtc_ttc_hourly(static, iso_config, 2023, hours)
        self.assertIsNotNone(out)
        ttc_hourly, ttc_import = out
        self.assertEqual(ttc_hourly.shape, (hours, len(links)))
        np.testing.assert_array_equal(ttc_import, static)

        i_pn = links.index(("Panhandle", "North"))
        static_pn = static[i_pn]  # 2,680 MW derived limit-at-bind
        # Active hours ride the measured hourly mean; unobserved hours the
        # static limit (never a year-max envelope).
        self.assertAlmostEqual(ttc_hourly[5, i_pn], 2500.0)  # 2 intervals, mean 2500
        self.assertAlmostEqual(ttc_hourly[6, i_pn], 3000.0)  # 1 interval at 3000
        self.assertAlmostEqual(ttc_hourly[0, i_pn], static_pn)  # unobserved -> static

        i_wn = links.index(("West", "North"))
        i_wsc = links.index(("West", "South_Central"))
        # WESTEX active hour 5: measured 9000 split 8:3 across the two links.
        self.assertAlmostEqual(ttc_hourly[5, i_wn], 9000.0 * 8.0 / 11.0)
        self.assertAlmostEqual(ttc_hourly[5, i_wsc], 9000.0 * 3.0 / 11.0)
        # Unobserved WESTEX hours revert to each link's static rating.
        self.assertAlmostEqual(ttc_hourly[0, i_wn], static[i_wn])
        self.assertAlmostEqual(ttc_hourly[0, i_wsc], static[i_wsc])

        # Unmapped links keep the static rating in every hour.
        i_nh = links.index(("North", "Houston"))
        np.testing.assert_allclose(ttc_hourly[:, i_nh], static[i_nh])

    def test_consumer_missing_year_returns_none(self):
        self._curated()
        from market_sim.data.gtc import ercot_gtc_ttc_hourly

        iso_config = get_iso_config("ERCOT")
        static = np.array([lk.ttc_mw for lk in iso_config.links])
        self.assertIsNone(ercot_gtc_ttc_hourly(static, iso_config, 2024, 24))


if __name__ == "__main__":
    unittest.main()
