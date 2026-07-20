"""Tests for ``data.build_throughput.max_annual_build_gw_by_tech``.

The module had zero tests. It derives each entry technology's historical
maximum single-year COD build (GW) by ISO from the EIA-860 record — the
externally-identified seed of the FF-2A entry growth ladder. These tests build
tiny EIA-860 fixtures (via :mod:`tests.helpers.raw_fixtures`) and pin the
contract the docstring promises: per-tech max-annual (not sum-across-years),
trailing-window bounds, ISO filtering by balancing authority, and the
rule-25 "missing tech is ABSENT, never a zero cap" guarantee.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from market_sim.data.build_throughput import max_annual_build_gw_by_tech
from tests.helpers.raw_fixtures import write_eia860


def _gens(rows) -> pd.DataFrame:
    """rows: list of (plant_code, mw, energy_source, prime_mover, op_year)."""
    return pd.DataFrame(
        rows,
        columns=[
            "Plant Code",
            "Nameplate Capacity (MW)",
            "Energy Source 1",
            "Prime Mover",
            "Operating Year",
        ],
    )


def _plants(pairs) -> pd.DataFrame:
    """pairs: list of (plant_code, ba_code)."""
    return pd.DataFrame(pairs, columns=["Plant Code", "Balancing Authority Code"])


class TestMaxAnnualBuild(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_per_tech_gw_and_iso_filter(self):
        write_eia860(
            self.dir,
            generators=_gens(
                [
                    (100, 500.0, "NG", "CA", 2021),  # ERCOT gas_cc
                    (200, 250.0, "NG", "GT", 2021),  # ERCOT gas_ct
                    (300, 1000.0, "NUC", "ST", 2021),  # MISO nuclear (filtered out)
                ]
            ),
            plants=_plants([(100, "ERCO"), (200, "ERCO"), (300, "MISO")]),
        )
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertAlmostEqual(out["gas_cc"], 0.5)
        self.assertAlmostEqual(out["gas_ct"], 0.25)
        self.assertNotIn("nuclear", out)  # the nuclear unit is MISO, not ERCOT

    def test_max_annual_not_sum_across_years(self):
        # Same tech builds 0.3 GW in 2021 and 0.5 GW in 2022 -> max is 0.5, not 0.8.
        write_eia860(
            self.dir,
            generators=_gens(
                [
                    (100, 300.0, "NG", "CA", 2021),
                    (200, 500.0, "NG", "CA", 2022),
                ]
            ),
            plants=_plants([(100, "ERCO"), (200, "ERCO")]),
        )
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertAlmostEqual(out["gas_cc"], 0.5)

    def test_same_year_same_tech_sums(self):
        # Two gas_cc plants both COD 2022 -> the single-year total is 0.8 GW.
        write_eia860(
            self.dir,
            generators=_gens(
                [
                    (100, 300.0, "NG", "CA", 2022),
                    (200, 500.0, "NG", "CA", 2022),
                ]
            ),
            plants=_plants([(100, "ERCO"), (200, "ERCO")]),
        )
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertAlmostEqual(out["gas_cc"], 0.8)

    def test_window_excludes_out_of_range_years(self):
        write_eia860(
            self.dir,
            generators=_gens([(100, 500.0, "NG", "CA", 2015)]),
            plants=_plants([(100, "ERCO")]),
        )
        # window [2018, 2022] excludes a 2015 COD -> empty.
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertEqual(out, {})

    def test_missing_tech_absent_not_zero(self):
        # Only gas_cc built; solar/wind must be ABSENT (rule 25: no zero cap).
        write_eia860(
            self.dir,
            generators=_gens([(100, 500.0, "NG", "CA", 2021)]),
            plants=_plants([(100, "ERCO")]),
        )
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertIn("gas_cc", out)
        self.assertNotIn("solar", out)
        self.assertNotIn("wind", out)

    def test_solar_and_wind_sheets_read(self):
        write_eia860(
            self.dir,
            generators=_gens([(100, 500.0, "NG", "CA", 2021)]),
            plants=_plants([(100, "ERCO"), (400, "ERCO"), (500, "ERCO")]),
            solar=pd.DataFrame(
                {
                    "Plant Code": [400],
                    "Nameplate Capacity (MW)": [150.0],
                    "Operating Year": [2022],
                }
            ),
            wind=pd.DataFrame(
                {
                    "Plant Code": [500],
                    "Nameplate Capacity (MW)": [200.0],
                    "Operating Year": [2020],
                }
            ),
        )
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertAlmostEqual(out["solar"], 0.15)
        self.assertAlmostEqual(out["wind"], 0.20)

    def test_missing_sheets_return_empty(self):
        # No parquet written at all -> loader logs and returns {} (not a crash).
        out = max_annual_build_gw_by_tech("ERCOT", 2022, 5, data_dir=self.dir)
        self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main()
