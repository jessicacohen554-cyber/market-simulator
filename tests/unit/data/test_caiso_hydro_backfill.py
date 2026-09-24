"""EIA-930 CISO ``NG: WAT`` gap repair from CAISO's Outlook fuel mix (i-caiso).

Covers :func:`market_sim.data.eia930.caiso_hydro_backfill.repair_measured_gaps`
and its source reader. Every fixture is synthetic and lives in a tempdir.
"""

from __future__ import annotations

import gzip
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import market_sim.data.eia930.caiso_hydro_backfill as hb


def _write_outlook(root: Path, year: int, day: str, large: float, small: float) -> None:
    """One day of 5-minute Outlook rows with constant hydro."""
    times = [f"{h}:{m:02d}" for h in range(24) for m in range(0, 60, 5)]
    df = pd.DataFrame(
        {
            "date": day,
            "time": times,
            "large_hydro": large,
            "small_hydro": small,
            "natural_gas": 1000.0,
        }
    )
    (root / f"fuelsource_{year}.csv.gz").write_bytes(
        gzip.compress(df.to_csv(index=False).encode())
    )


def _frame(
    day_utc_start: str, hours: int, wat: list[float], gas: float
) -> pd.DataFrame:
    """A tiny EIA-930-shaped frame whose Net generation = sum of reported cells."""
    utc = pd.date_range(day_utc_start, periods=hours, freq="h")
    wat_arr = np.array(wat, dtype=float)
    ng = gas + np.nan_to_num(wat_arr)
    return pd.DataFrame(
        {
            "UTC time": utc,
            "Net generation": ng,
            "NG: NG": gas,
            "NG: WAT": wat_arr,
        }
    )


class TestRepairMeasuredGaps(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        hb.outlook_hourly_hydro.cache_clear()
        self._patch = mock.patch.object(hb, "CAISO_OUTLOOK_FUELSOURCE_DIR", self.root)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        hb.outlook_hourly_hydro.cache_clear()
        self._tmp.cleanup()

    def test_fills_nan_cell_and_restores_net_generation(self):
        # 2019-11-01 00:00 PDT == 07:00 UTC; hydro 2000 + 300 MW all day.
        _write_outlook(self.root, 2019, "2019-11-01", 2000.0, 300.0)
        f = _frame("2019-11-01 07:00", 3, [np.nan, np.nan, 2250.0], gas=5000.0)
        out = hb.repair_measured_gaps(f, "CISO", 2019)
        self.assertEqual(out["NG: WAT"].tolist(), [2300.0, 2300.0, 2250.0])
        # Net generation excluded hydro in the NaN hours -> hydro added there only.
        self.assertEqual(out["Net generation"].tolist(), [7300.0, 7300.0, 7250.0])
        self.assertTrue(np.isnan(f["NG: WAT"].iloc[0]))  # input not mutated

    def test_net_generation_already_carrying_hydro_is_left_alone(self):
        _write_outlook(self.root, 2019, "2019-11-01", 2000.0, 300.0)
        f = _frame("2019-11-01 07:00", 1, [np.nan], gas=5000.0)
        f["Net generation"] = 7300.0  # the filing already counts hydro
        out = hb.repair_measured_gaps(f, "CISO", 2019)
        self.assertEqual(out["NG: WAT"].tolist(), [2300.0])
        self.assertEqual(out["Net generation"].tolist(), [7300.0])

    def test_no_source_year_returns_same_object(self):
        f = _frame("2022-01-01 08:00", 2, [np.nan, 1000.0], gas=5000.0)
        self.assertIs(hb.repair_measured_gaps(f, "CISO", 2022), f)

    def test_unregistered_ba_returns_same_object(self):
        _write_outlook(self.root, 2019, "2019-11-01", 2000.0, 300.0)
        f = _frame("2019-11-01 07:00", 2, [np.nan, np.nan], gas=5000.0)
        self.assertIs(hb.repair_measured_gaps(f, "MISO", 2019), f)

    def test_complete_cell_returns_same_object(self):
        _write_outlook(self.root, 2019, "2019-11-01", 2000.0, 300.0)
        f = _frame("2019-11-01 07:00", 2, [2100.0, 2200.0], gas=5000.0)
        self.assertIs(hb.repair_measured_gaps(f, "CISO", 2019), f)


if __name__ == "__main__":
    unittest.main()
