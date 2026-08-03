"""Tests for ``data.build_exit_throughput.max_annual_exit_gw``.

The externally identified seed of the FFR-3F exit-rate cap
(``ScenarioConfig.exit_rate_limits``; owner decision D-8, 2026-08-03): each
ISO's measured maximum single-year thermal DEACTIVATION (GW) from the EIA-860
retired sheet. These tests build tiny EIA-860 fixtures and pin the contract
the docstring promises: max-annual (not sum-across-years), the ``Status ==
"RE"`` filter that keeps cancelled/postponed units out, thermal-only, ISO
filtering by balancing authority, trailing-window bounds, and the rule-25
"no measurement means NO cap, never a zero cap" guarantee.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from market_sim.data.build_exit_throughput import max_annual_exit_gw


def _retired(rows) -> pd.DataFrame:
    """rows: (plant_code, mw, energy_source, prime_mover, retire_year, status)."""
    return pd.DataFrame(
        rows,
        columns=[
            "Plant Code",
            "Nameplate Capacity (MW)",
            "Energy Source 1",
            "Prime Mover",
            "Retirement Year",
            "Status",
        ],
    )


def _plants(pairs) -> pd.DataFrame:
    """pairs: list of (plant_code, ba_code)."""
    return pd.DataFrame(pairs, columns=["Plant Code", "Balancing Authority Code"])


class TestMaxAnnualExit(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, retired: pd.DataFrame, plants: pd.DataFrame) -> None:
        retired.to_parquet(
            self.dir / "eia860_generator_retired_and_canceled.parquet", index=False
        )
        plants.to_parquet(self.dir / "eia860_plant.parquet", index=False)

    def test_max_annual_not_sum_across_years_and_iso_filter(self):
        # 0.3 GW retires in 2021 and 0.5 GW in 2022 -> the seed is the MAX
        # single year (0.5), not the 0.8 total. The MISO unit is filtered out.
        self._write(
            _retired(
                [
                    (100, 300.0, "BIT", "ST", 2021, "RE"),
                    (200, 500.0, "NG", "CA", 2022, "RE"),
                    (300, 900.0, "BIT", "ST", 2022, "RE"),  # MISO, not ERCOT
                ]
            ),
            _plants([(100, "ERCO"), (200, "ERCO"), (300, "MISO")]),
        )
        self.assertAlmostEqual(max_annual_exit_gw("ERCOT", 2023, 5, self.dir), 0.5)
        self.assertAlmostEqual(max_annual_exit_gw("MISO", 2023, 5, self.dir), 0.9)

    def test_same_year_units_sum_within_the_year(self):
        # Two units retiring in ONE year are one deactivation year of 0.8 GW —
        # the quantity the cap bounds is MW per year, not MW per unit.
        self._write(
            _retired(
                [
                    (100, 300.0, "BIT", "ST", 2022, "RE"),
                    (200, 500.0, "BIT", "ST", 2022, "RE"),
                ]
            ),
            _plants([(100, "ERCO"), (200, "ERCO")]),
        )
        self.assertAlmostEqual(max_annual_exit_gw("ERCOT", 2023, 5, self.dir), 0.8)

    def test_only_retired_status_counts(self):
        # "CN" (cancelled — never built) and "IP" (indefinitely postponed) are
        # not deactivations and must not inflate the seed.
        self._write(
            _retired(
                [
                    (100, 200.0, "BIT", "ST", 2022, "RE"),
                    (200, 900.0, "BIT", "ST", 2022, "CN"),
                    (300, 800.0, "BIT", "ST", 2022, "IP"),
                ]
            ),
            _plants([(100, "ERCO"), (200, "ERCO"), (300, "ERCO")]),
        )
        self.assertAlmostEqual(max_annual_exit_gw("ERCOT", 2023, 5, self.dir), 0.2)

    def test_non_thermal_is_excluded(self):
        # The cap bounds the retirement screen, which screens dispatchable
        # thermal only; a retiring wind farm is not exit throughput for it.
        self._write(
            _retired(
                [
                    (100, 200.0, "BIT", "ST", 2022, "RE"),
                    (200, 900.0, "WND", "WT", 2022, "RE"),
                ]
            ),
            _plants([(100, "ERCO"), (200, "ERCO")]),
        )
        self.assertAlmostEqual(max_annual_exit_gw("ERCOT", 2023, 5, self.dir), 0.2)

    def test_trailing_window_bounds_the_seed(self):
        # A 3-yr window through 2023 spans 2021-2023: the 2019 year is out.
        self._write(
            _retired(
                [
                    (100, 900.0, "BIT", "ST", 2019, "RE"),
                    (200, 200.0, "BIT", "ST", 2022, "RE"),
                ]
            ),
            _plants([(100, "ERCO"), (200, "ERCO")]),
        )
        self.assertAlmostEqual(max_annual_exit_gw("ERCOT", 2023, 3, self.dir), 0.2)
        # Widen the window and the older, larger year is back in scope.
        self.assertAlmostEqual(max_annual_exit_gw("ERCOT", 2023, 10, self.dir), 0.9)

    def test_no_measurement_returns_none_not_zero(self):
        # Rule 25 [R-ISO-SCOPE]: a missing measurement must not invent a zero
        # cap that forbids exit entirely. None means NO cap, and the caller
        # relies on that distinction.
        self._write(
            _retired([(100, 200.0, "BIT", "ST", 2022, "RE")]),
            _plants([(100, "ERCO")]),
        )
        self.assertIsNone(max_annual_exit_gw("NYISO", 2023, 5, self.dir))

    def test_missing_sheets_return_none(self):
        self.assertIsNone(max_annual_exit_gw("ERCOT", 2023, 5, self.dir))


if __name__ == "__main__":
    unittest.main()
