"""PSEI's double-booked Colstrip share and non-balance demand hours (lane NWPP-NEXT-2).

``frames._repair_double_booked_generation`` removes a registered member's
remote fuel column from its net generation and demand (interchange untouched);
``frames._mask_unbalanced_demand`` turns an hour whose demand is just the
member's generation (interchange missing, ``D == NG``) into a missing reading
for the pool's gap guard; ``frames._pool_member_demand`` is the single
construction the pool total and the NWPP zonal regroup both read. Record:
``docs/handoffs/FINDING-nwppnext2-psei-basis-2026-09-25.md``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import EIA_HOURLY_DIR, FERC_714_DIR
from market_sim.data.eia930 import frames

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _frame(**cols) -> pd.DataFrame:
    return pd.DataFrame({k: np.asarray(v, dtype=float) for k, v in cols.items()})


class TestDoubleBookedRepair(unittest.TestCase):
    def test_unregistered_ba_is_returned_unchanged(self):
        df = _frame(**{"Net generation": [1.0], "NG: COL": [1.0]})
        self.assertIs(frames._repair_double_booked_generation(df, "NWMT"), df)

    def test_psei_col_leaves_ng_and_demand_keeps_interchange(self):
        df = _frame(
            **{
                "Net generation": [500.0, 400.0, np.nan],
                "Net generation (Adjusted)": [500.0, 400.0, np.nan],
                "Demand": [2000.0, 1900.0, np.nan],
                "Demand (Adjusted)": [2000.0, 1900.0, np.nan],
                "Total interchange": [-1500.0, -1500.0, -1500.0],
                "Total interchange (Adjusted)": [-1500.0, -1500.0, -1500.0],
                "NG: COL": [300.0, np.nan, 200.0],
            }
        )
        out = frames._repair_double_booked_generation(df, "PSEI")
        self.assertIsNot(out, df)
        np.testing.assert_array_equal(out["Net generation"], [200.0, 400.0, np.nan])
        np.testing.assert_array_equal(out["Demand (Adjusted)"], [1700.0, 1900.0, np.nan])
        np.testing.assert_array_equal(out["Total interchange"], df["Total interchange"])
        np.testing.assert_array_equal(out["NG: COL"], [0.0, np.nan, 0.0])
        # identity D = NG - TI preserved where it held
        self.assertEqual(out["Demand"][0], out["Net generation"][0] - out["Total interchange"][0])
        self.assertEqual(df["NG: COL"][0], 300.0)  # input never edited


class TestUnbalancedDemandMask(unittest.TestCase):
    def test_masks_only_missing_ti_with_demand_equal_generation(self):
        df = _frame(
            **{
                "Demand (Adjusted)": [1000.0, 1000.0, 2500.0, 900.0],
                "Net generation (Adjusted)": [1000.0, 1000.0, 1000.0, 1000.0],
                "Total interchange (Adjusted)": [np.nan, 0.0, np.nan, np.nan],
            }
        )
        got = frames._mask_unbalanced_demand(df)
        np.testing.assert_array_equal(got, [np.nan, 1000.0, 2500.0, 900.0])


def _hydrated() -> bool:
    return (EIA_HOURLY_DIR / "PSEI hourly.parquet").exists() and (
        FERC_714_DIR / "psei_hourly_planning_area_demand_2018_2024.csv"
    ).exists()


@unittest.skipUnless(_hydrated(), "NWPP member extracts / FERC 714 not hydrated")
class TestMeasuredEffect(unittest.TestCase):
    def test_2019_pool_books_colstrip_once(self):
        frames._pool_hourly_frame.cache_clear()
        frame = frames._pool_hourly_frame("NWPP", 2019)
        members = frames._pool_member_frames("NWPP", 2019)
        self.assertEqual(float(np.nansum(members["PSEI"]["NG: COL"])), 0.0)
        # Pool coal 58.996 -> 54.516 TWh: PSEI's 4.480 TWh local-year Colstrip
        # share is gone; NWMT still books the whole plant.
        self.assertAlmostEqual(float(frame["NG: COL"].sum()) / 1e6, 54.516, delta=0.01)

    def test_2021_psei_non_balance_window_is_filled_from_ferc714(self):
        members = frames._pool_member_frames("NWPP", 2021)
        utc = pd.DatetimeIndex(members["BPAT"]["UTC time"])
        psei = members["PSEI"]
        self.assertEqual(int(np.isnan(frames._mask_unbalanced_demand(psei)).sum()), 336)
        d = frames._pool_member_demand(psei, utc, pool="NWPP", member="PSEI", year=2021)
        raw = psei["Demand (Adjusted)"].to_numpy(dtype=float)
        self.assertAlmostEqual((d.sum() - raw.sum()) / 1e6, 0.570, delta=0.01)

    def test_2022_2025_members_carry_no_repair(self):
        for year in range(2022, 2026):
            members = frames._pool_member_frames("NWPP", year)
            for ba, df in members.items():
                if ba in frames._POOL_GENERATION_ONLY_BAS:
                    continue
                d = frames._mask_unbalanced_demand(df)
                raw = df["Demand (Adjusted)"].to_numpy(dtype=float)
                np.testing.assert_array_equal(np.isnan(d), np.isnan(raw), err_msg=f"{ba} {year}")

    def test_zonal_regroup_reproduces_pool_demand(self):
        from market_sim.config.iso_configs import get_iso_config
        from scripts.data.curate_zonal_shares import parse_nwpp_shares

        zones = get_iso_config("NWPP").zone_names
        for year in (2019, 2020, 2021):
            frames._pool_hourly_frame.cache_clear()
            pool = frames._pool_hourly_frame("NWPP", year)["Demand"].to_numpy(dtype=float)
            members = frames._pool_member_frames("NWPP", year)
            utc = pd.DatetimeIndex(members["BPAT"]["UTC time"])
            psei = frames._pool_member_demand(
                members["PSEI"], utc, pool="NWPP", member="PSEI", year=year
            )
            shares = parse_nwpp_shares(year, zones)
            nw = zones.index("NWPP-NW")
            # PSEI sits in NWPP-NW: its share can never be below PSEI's own demand share.
            self.assertTrue(np.all(shares[nw] * pool >= psei - 1e-6), year)


if __name__ == "__main__":
    unittest.main()
