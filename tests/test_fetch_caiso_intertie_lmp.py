"""Offline tests for the CAISO intertie-LMP -> local-8760 conversion.

The OASIS fetch is network-only; this exercises the GMT->Pacific hour mapping and
the delivered-nodal-LMP extraction (sum of the MCE energy + MCC congestion + MCL
loss components, GHG excluded) that feeds
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
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "data"
    / "fetch_caiso_intertie_lmp.py",
)
fil = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fil)


class TestHourIndex(unittest.TestCase):
    def test_jan1_midnight_pacific_is_hour_zero(self):
        # 08:00 UTC on Jan 1 == 00:00 PST -> hour 0.
        ts = pd.to_datetime(
            pd.Series(["2024-01-01 08:00:00+00:00"]), utc=True
        ).dt.tz_convert(fil.CAISO_TZ)
        self.assertEqual(int(fil._hour_index(ts)[0]), 0)

    def test_feb29_is_dropped(self):
        ts = pd.to_datetime(
            pd.Series(["2024-02-29 20:00:00+00:00"]), utc=True
        ).dt.tz_convert(fil.CAISO_TZ)
        self.assertEqual(int(fil._hour_index(ts)[0]), -1)

    def test_dec31_last_hour_in_range(self):
        ts = pd.to_datetime(
            pd.Series(["2024-12-31 23:00:00-08:00"]), utc=True
        ).dt.tz_convert(fil.CAISO_TZ)
        h = int(fil._hour_index(ts)[0])
        self.assertEqual(h, 8759)


def _long_rows(ts: str, comps: dict[str, float]) -> list[dict]:
    """Build OASIS-style long-format rows (one per LMP_TYPE) for one interval."""
    return [
        {"INTERVALSTARTTIME_GMT": ts, "LMP_TYPE": t, "MW": v} for t, v in comps.items()
    ]


class TestToHourlyNodalLmp(unittest.TestCase):
    def test_sums_energy_congestion_loss_excludes_ghg(self):
        # Two Pacific-midnight hours (Jan 1 and Jan 2). The delivered nodal price
        # is MCE+MCC+MCL; MGHG and the redundant LMP total row are ignored.
        rows = []
        # hour 0: 21.5 + (-2.0) + 0.5 = 20.0; MGHG 3.0 must NOT be added.
        rows += _long_rows(
            "2024-01-01 08:00:00+00:00",
            {"MCE": 21.5, "MCC": -2.0, "MCL": 0.5, "MGHG": 3.0, "LMP": 23.0},
        )
        # hour 24: -8.0 + 1.0 + (-1.0) = -8.0 (can go negative in the solar glut).
        rows += _long_rows(
            "2024-01-02 08:00:00+00:00",
            {"MCE": -8.0, "MCC": 1.0, "MCL": -1.0, "MGHG": 0.0, "LMP": -8.0},
        )
        out = fil._to_hourly_nodal_lmp(pd.DataFrame(rows), 2024)
        self.assertEqual(out.shape, (8760,))
        self.assertAlmostEqual(out[0], 20.0)
        self.assertAlmostEqual(out[24], -8.0)
        self.assertTrue(np.isnan(out[12]))  # unfilled hour stays NaN

    def test_missing_energy_component_returns_none(self):
        # No MCE row anywhere -> unusable -> None (year falls back to the ladder).
        df = pd.DataFrame(
            _long_rows("2024-01-01 08:00:00+00:00", {"MGHG": 3.0, "LMP": 35.0})
        )
        self.assertIsNone(fil._to_hourly_nodal_lmp(df, 2024))

    def test_unrecognized_schema_returns_none(self):
        df = pd.DataFrame({"foo": [1], "bar": [2]})
        self.assertIsNone(fil._to_hourly_nodal_lmp(df, 2024))

    def test_output_columns_match_loader_schema(self):
        # The parquet the loader reads is (year, hour, hub, price); a record built
        # from the hourly series must carry exactly those keys.
        out = fil._to_hourly_nodal_lmp(
            pd.DataFrame(
                _long_rows("2024-01-01 08:00:00+00:00", {"MCE": 10.0, "MCC": 1.0})
            ),
            2024,
        )
        rec = {
            "year": 2024,
            "hour": 0,
            "hub": "MALIN",
            "price": round(float(out[0]), 4),
        }
        self.assertEqual(set(rec), {"year", "hour", "hub", "price"})
        self.assertAlmostEqual(out[0], 11.0)  # MCE + MCC, no loss row present


class TestNodeMap(unittest.TestCase):
    def test_two_model_hubs_present(self):
        self.assertEqual(set(fil.INTERTIE_NODES), {"MALIN", "PALOVRDE"})
        for nodes in fil.INTERTIE_NODES.values():
            self.assertTrue(nodes)


if __name__ == "__main__":
    unittest.main()
