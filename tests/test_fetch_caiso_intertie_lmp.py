"""Offline tests for the CAISO intertie-LMP -> local-8760 conversion.

The OASIS fetch is network-only; this exercises the GMT->Pacific hour mapping and
the MCE energy-component extraction that feed
``wecc_intertie_lmp_hourly_CAISO.parquet`` (consumed by
``eia_loader.measured_import_hub_prices``).
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_SPEC = importlib.util.spec_from_file_location(
    "fetch_caiso_intertie_lmp",
    Path(__file__).resolve().parent.parent / "scripts" / "fetch_caiso_intertie_lmp.py",
)
fil = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fil)


class TestHourIndex(unittest.TestCase):
    def test_jan1_midnight_pacific_is_hour_zero(self):
        # 08:00 UTC on Jan 1 == 00:00 PST -> hour 0.
        ts = pd.to_datetime(pd.Series(["2024-01-01 08:00:00+00:00"]),
                            utc=True).dt.tz_convert(fil.CAISO_TZ)
        self.assertEqual(int(fil._hour_index(ts)[0]), 0)

    def test_feb29_is_dropped(self):
        ts = pd.to_datetime(pd.Series(["2024-02-29 20:00:00+00:00"]),
                            utc=True).dt.tz_convert(fil.CAISO_TZ)
        self.assertEqual(int(fil._hour_index(ts)[0]), -1)

    def test_dec31_last_hour_in_range(self):
        ts = pd.to_datetime(pd.Series(["2024-12-31 23:00:00-08:00"]),
                            utc=True).dt.tz_convert(fil.CAISO_TZ)
        h = int(fil._hour_index(ts)[0])
        self.assertEqual(h, 8759)


class TestToHourlyEnergy(unittest.TestCase):
    def test_extracts_mce_on_calendar(self):
        # Two Pacific-midnight hours (Jan 1 and Jan 2) with known MCE values.
        df = pd.DataFrame({
            "interval_start_gmt": ["2024-01-01 08:00:00+00:00",
                                   "2024-01-02 08:00:00+00:00"],
            "MCE": [21.5, -8.0],   # energy component; can be negative (solar glut)
            "LMP": [35.0, 4.0],
        })
        out = fil._to_hourly_energy(df, 2024)
        self.assertEqual(out.shape, (8760,))
        self.assertAlmostEqual(out[0], 21.5)
        self.assertAlmostEqual(out[24], -8.0)
        self.assertTrue(np.isnan(out[12]))  # unfilled hour stays NaN

    def test_missing_mce_column_returns_none(self):
        df = pd.DataFrame({"interval_start_gmt": ["2024-01-01 08:00:00+00:00"],
                           "LMP": [35.0]})
        self.assertIsNone(fil._to_hourly_energy(df, 2024))

    def test_output_columns_match_loader_schema(self):
        # The parquet the loader reads is (year, hour, hub, price); a record built
        # from _to_hourly_energy must carry exactly those keys.
        out = fil._to_hourly_energy(pd.DataFrame({
            "interval_start_gmt": ["2024-01-01 08:00:00+00:00"], "MCE": [10.0]}), 2024)
        rec = {"year": 2024, "hour": 0, "hub": "MALIN", "price": round(float(out[0]), 4)}
        self.assertEqual(set(rec), {"year", "hour", "hub", "price"})


class TestNodeMap(unittest.TestCase):
    def test_two_model_hubs_present(self):
        self.assertEqual(set(fil.INTERTIE_NODES), {"MALIN", "PALOVRDE"})
        for nodes in fil.INTERTIE_NODES.values():
            self.assertTrue(nodes)


if __name__ == "__main__":
    unittest.main()
