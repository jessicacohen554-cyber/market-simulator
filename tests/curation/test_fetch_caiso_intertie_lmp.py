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

import numpy as np
import pandas as pd
from tests.helpers import REPO_ROOT

_SPEC = importlib.util.spec_from_file_location(
    "fetch_caiso_intertie_lmp",
    REPO_ROOT / "scripts" / "data" / "fetch_caiso_intertie_lmp.py",
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


class TestFromHourlyAggregate(unittest.TestCase):
    """The ``--from-hourly-aggregate`` route (i-caiso): the tracked GroupZip-folded
    ``CAISO_dam_hourly_<year>.csv`` melted back to long form."""

    def test_melts_components_and_keeps_local_year(self):
        import tempfile
        from pathlib import Path
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pd.DataFrame(
                {
                    # 07:00 UTC Jan 1 2021 is 23:00 PST Dec 31 2020 -> dropped.
                    "interval_start_gmt": [
                        "2021-01-01 07:00:00+00:00",
                        "2021-01-01 08:00:00+00:00",
                        "2021-01-01 08:00:00+00:00",
                    ],
                    "node": ["MALIN_5_N101", "MALIN_5_N101", "TH_NP15_GEN-APND"],
                    "LMP": [0.0, 12.5, 30.0],
                    "MCC": [0.0, 1.0, 0.0],
                    "MCE": [0.0, 12.0, 30.0],
                    "MCL": [0.0, -0.5, 0.0],
                }
            ).to_csv(root / "CAISO_dam_hourly_2021.csv", index=False)
            import scripts.data.fold_caiso_oasis_grp_zips as fold

            with mock.patch.object(fold, "LMP_DIR", root):
                raw = fil._raw_from_hourly_aggregate("MALIN_5_N101", 2021)
        self.assertEqual(sorted(raw["LMP_TYPE"].unique()), ["MCC", "MCE", "MCL"])
        out = fil._to_hourly_nodal_lmp(raw, 2021)
        self.assertAlmostEqual(out[0], 12.5)  # MCE + MCC + MCL
        self.assertEqual(int(np.isfinite(out).sum()), 1)

    def test_absent_aggregate_returns_none(self):
        import tempfile
        from pathlib import Path
        from unittest import mock

        import scripts.data.fold_caiso_oasis_grp_zips as fold

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(fold, "LMP_DIR", Path(tmp)):
                self.assertIsNone(fil._raw_from_hourly_aggregate("MALIN_5_N101", 2019))


class TestNodeMap(unittest.TestCase):
    def test_two_model_hubs_present(self):
        self.assertEqual(set(fil.INTERTIE_NODES), {"MALIN", "PALOVRDE"})
        for nodes in fil.INTERTIE_NODES.values():
            self.assertTrue(nodes)


if __name__ == "__main__":
    unittest.main()
