"""EIA-930 balance-identity demand screen (lane pjm-h19, 2026-09-23).

``demand._screen_demand_balance`` repairs an hour whose metered ``Demand``
makes an isolated reversal larger than the BA-year's own Tukey far-out hourly
ramp AND departs from its neighbours more than the independent balance
measurement ``NG - TI`` does. ``ScenarioConfig.demand_balance_screen`` gates
it (default off). This file pins (1) the synthetic logic, trivial case first,
(2) the default path is byte-identical, and (3) on the hydrated PJM extract
the screen flags exactly the four pjm-h18 hours over 2020-2025
(``docs/PRECOMMIT-pjm-h19-demand-balance-screen-2026-09-23.md`` §3).
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import EIA_HOURLY_DIR
from market_sim.data.eia930 import demand as dm


def _frame(ng: np.ndarray, ti: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"Net generation": ng, "Total interchange": ti})


def _diurnal(n: int) -> np.ndarray:
    t = np.arange(n, dtype=float)
    return 100.0 + 10.0 * np.sin(2.0 * np.pi * t / 24.0)


class TestScreenLogic(unittest.TestCase):
    """Synthetic series: one bad hour, generation side clean."""

    def _run(self, d: np.ndarray, s: np.ndarray) -> np.ndarray:
        with mock.patch.object(
            dm, "_eia_hourly_frame_filled", return_value=_frame(s, np.zeros_like(s))
        ):
            return dm._screen_demand_balance(d, iso="PJM", year=2020)

    def test_isolated_spike_is_interpolated(self):
        s = _diurnal(240)
        d = s.copy()
        d[100] += 60.0
        out = self._run(d, s)
        self.assertAlmostEqual(out[100], 0.5 * (d[99] + d[101]))
        np.testing.assert_array_equal(np.delete(out, 100), np.delete(d, 100))

    def test_isolated_dropout_is_interpolated(self):
        s = _diurnal(240)
        d = s.copy()
        d[50] -= 40.0
        out = self._run(d, s)
        self.assertAlmostEqual(out[50], 0.5 * (d[49] + d[51]))

    def test_reading_consistent_with_supply_is_left_alone(self):
        # The same excursion in NG - TI: the identity cannot blame demand.
        s = _diurnal(240)
        s[100] += 60.0
        d = s.copy()
        out = self._run(d, s)
        self.assertIs(out, d)

    def test_clean_series_returns_same_object(self):
        s = _diurnal(240)
        d = s.copy()
        self.assertIs(self._run(d, s), d)

    def test_iso_without_balance_frame_is_inert(self):
        d = _diurnal(240)
        d[100] += 60.0
        self.assertIs(dm._screen_demand_balance(d, iso="NWPP", year=2024), d)


class TestDefaultOff(unittest.TestCase):
    def test_field_defaults_false(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig().demand_balance_screen)

    def test_load_demand_default_never_calls_screen(self):
        with mock.patch.object(dm, "_screen_demand_balance") as screen:
            try:
                dm.load_demand("PJM", 2024)
            except Exception:  # noqa: BLE001 - data may be absent; call check only
                pass
            screen.assert_not_called()


@unittest.skipUnless(
    (EIA_HOURLY_DIR / "PJM hourly.parquet").exists(), "PJM extract not hydrated"
)
class TestPjmMeasured(unittest.TestCase):
    """The declared phase-0 census: exactly the four pjm-h18 hours in 2020-2025."""

    EXPECTED = {2020: [5003, 5031, 5383], 2024: [7787]}

    def test_flags_exactly_the_four_hours(self):
        for year in range(2020, 2026):
            raw = dm._load_pjm_hourly_demand(year)
            out = dm._screen_demand_balance(raw, iso="PJM", year=year)
            changed = np.flatnonzero(out != raw).tolist()
            self.assertEqual(changed, self.EXPECTED.get(year, []), year)
            self.assertEqual(out.size, HOURS_PER_YEAR)


if __name__ == "__main__":
    unittest.main()
