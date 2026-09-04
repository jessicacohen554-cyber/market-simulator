"""``caiso_citygate_spot_coverage`` — the spot-level overlay covers a month on its own prints.

caiso-246 (``PRECOMMIT-caiso246-spot-coverage-2026-09-04.md``): under
``caiso_citygate_spot_level`` a covered month's gas price comes entirely from
the measured CA Composite daily citygate spot, yet a month counted as covered
only where the EIA N3050CA3 monthly SURVEY had a basis row — and EIA publishes
that survey as NA for 2025-09/10/11. These tests pin, on a tiny synthetic
basis / Henry-Hub / daily-print fixture:

* flag OFF: a month with prints but no survey row stays UNCOVERED (NaN) —
  byte-identical to the pre-caiso-246 gate;
* flag ON: that month is covered from its own prints (calendar-interpolated
  absolute daily spot), every other month's hours are UNCHANGED, and a month
  with neither a survey row nor prints stays uncovered;
* the flag is inert without ``spot_level`` (the monthly leg never reads it).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import hubs

HOURS = 8760
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_START = np.cumsum([0, *_DAYS[:-1]]) * 24


def _month_hours(m: int) -> slice:
    return slice(int(_START[m - 1]), int(_START[m - 1] + _DAYS[m - 1] * 24))


class TestSpotCoverage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        # Survey basis rows for every 2025 month EXCEPT Sep, Oct, Nov (EIA NA).
        rows = ["iso,year,month,hub,basis_usd_mmbtu,source"]
        for m in range(1, 13):
            if m in (9, 10, 11):
                continue
            rows.append(f"CAISO,2025,{m},CA citygate,0.50,test")
        (d / "basis.csv").write_text("\n".join(rows) + "\n")
        hh = ["year,month,price_usd_mmbtu"] + [f"2025,{m},3.00" for m in range(1, 13)]
        (d / "hh.csv").write_text("\n".join(hh) + "\n")
        # Daily prints: every month except OCTOBER has prints (Oct has neither
        # a survey row nor prints and must stay uncovered under both flags).
        daily = ["date,ca_composite_usd_mmbtu,henry_hub_usd_mmbtu"]
        for m in range(1, 13):
            if m == 10:
                continue
            for day in (3, 17):
                daily.append(f"2025-{m:02d}-{day:02d},{2.0 + m / 10:.2f},3.00")
        (d / "daily.csv").write_text("\n".join(daily) + "\n")
        self.paths = dict(
            basis_path=d / "basis.csv",
            henry_hub_path=d / "hh.csv",
            citygate_path=d / "daily.csv",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _config(self, coverage: bool) -> ScenarioConfig:
        return ScenarioConfig(
            iso="CAISO",
            hours=HOURS,
            mode="backcast",
            gas_hub_basis_overlay=True,
            caiso_citygate_spot_level=True,
            caiso_citygate_spot_coverage=coverage,
        )

    def _series(self, coverage: bool) -> np.ndarray:
        out = hubs._caiso_hub_daily_gas_prices(
            self._config(coverage),
            2025,
            spot_level=True,
            spot_coverage=coverage,
            **self.paths,
        )
        self.assertIsNotNone(out)
        return out

    def test_flag_off_keeps_the_survey_gate(self) -> None:
        off = self._series(False)
        for m in (9, 10, 11):
            self.assertTrue(np.isnan(off[_month_hours(m)]).all(), m)
        for m in (1, 8, 12):
            self.assertTrue(np.isfinite(off[_month_hours(m)]).all(), m)

    def test_flag_on_covers_own_print_months_only(self) -> None:
        off = self._series(False)
        on = self._series(True)
        # Sep and Nov: prints, no survey row -> covered from the prints.
        for m in (9, 11):
            seg = on[_month_hours(m)]
            self.assertTrue(np.isfinite(seg).all(), m)
            # the calendar interpolation of two equal prints is that value
            self.assertAlmostEqual(float(seg.mean()), 2.0 + m / 10, places=6)
        # Oct: neither -> still uncovered.
        self.assertTrue(np.isnan(on[_month_hours(10)]).all())
        # Every other month is byte-identical to the flag-off series.
        for m in (1, 2, 3, 4, 5, 6, 7, 8, 12):
            np.testing.assert_array_equal(on[_month_hours(m)], off[_month_hours(m)])

    def test_flag_inert_without_spot_level(self) -> None:
        cfg = self._config(True)
        a = hubs._caiso_hub_daily_gas_prices(
            cfg, 2025, spot_level=False, spot_coverage=True, **self.paths
        )
        b = hubs._caiso_hub_daily_gas_prices(
            cfg, 2025, spot_level=False, spot_coverage=False, **self.paths
        )
        np.testing.assert_array_equal(np.isnan(a), np.isnan(b))
        self.assertTrue(np.isnan(a[_month_hours(9)]).all())


if __name__ == "__main__":
    unittest.main()
