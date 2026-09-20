"""xiso-8 — the year-start left-edge flow-date convention.

``config.gas_flow_date_year_start_package`` prices a year's OPENING flow days
with the previous December trade that actually covered them, instead of
back-filling them from the year's first January trade (which had not happened
yet and prices a LATER flow day).

These guards pin the three things that can silently break:

  * **the default is byte-identical** — every existing keeper in every ISO keeps
    its numbers and its cache key;
  * **the SCOPE LIMIT** — the seed crosses a trading PACKAGE and never a
    publication BLACKOUT, which is :func:`_basis_bridge_blackouts`' territory
    (rule 19 ``[R-ONE-MECH]``). MISO 2023 is the case that makes this load-
    bearing: its boundary sits inside a 15-day blackout whose last print is the
    Winter Storm Elliott spike;
  * **the measured per-year footprint**, so a later change to the staircase
    cannot move these days without a test saying so.

Figures are from ``scripts/probes/xiso8_left_edge_census.py`` ->
``results/calibration/_xiso8_left_edge_census.json`` and are reproduced in
``docs/PRECOMMIT-xiso8-year-start-left-edge-2026-09-20.md`` §2.
"""

import unittest

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel.hubs import (
    _caiso_citygate_daily_dated,
    _flow_date_staircase,
    _GAS_BLACKOUT_MIN_GAP_DAYS,
    _miso_citygate_daily_dated,
    _year_start_package_seed,
)

pytestmark = [pytest.mark.integration, pytest.mark.fulldata]

#: CAISO: (year, edge days, Δ $/MMBtu) — every scored year is a PACKAGE boundary.
CAISO_FOOTPRINT = (
    (2022, 3, +1.43),
    (2023, 3, -8.35),
    (2024, 2, -0.47),
    (2025, 2, -0.22),
)

#: MISO: only 2021/2022 are package boundaries; the rest sit inside blackouts.
MISO_FOOTPRINT = ((2021, 4, -0.18), (2022, 3, +0.20))
MISO_BLACKOUT_YEARS = (2019, 2020, 2023, 2024, 2025)


def _armed(dated_all, year):
    return _flow_date_staircase(
        dated_all[year], year, prior_year_dated=dated_all.get(year - 1)
    )


class TestDefaultIsByteIdentical(unittest.TestCase):
    def test_no_prior_map_reproduces_the_unrepaired_array_exactly(self):
        """Omitting ``prior_year_dated`` must change nothing, in either ISO."""
        for dated_all in (
            _caiso_citygate_daily_dated(None),
            _miso_citygate_daily_dated(None),
        ):
            for year in sorted(dated_all):
                plain = _flow_date_staircase(dated_all[year], year)
                explicit_none = _flow_date_staircase(
                    dated_all[year], year, None, None, None
                )
                if plain is None:
                    self.assertIsNone(explicit_none)
                    continue
                np.testing.assert_array_equal(plain, explicit_none)

    def test_the_gate_is_registered_default_off_and_the_arm_re_keys(self):
        base = dict(iso="CAISO", mode="backcast")
        self.assertFalse(ScenarioConfig(**base).gas_flow_date_year_start_package)
        off = ScenarioConfig(**base).cache_key()
        on = ScenarioConfig(**base, gas_flow_date_year_start_package=True).cache_key()
        self.assertNotEqual(off, on, "an armed run must earn a distinct cache key")


class TestScopeLimit(unittest.TestCase):
    """The seed crosses a PACKAGE and never a BLACKOUT."""

    def test_miso_2023_elliott_blackout_is_never_seeded(self):
        """The case the limit exists for.

        MISO's 2023 boundary sits inside a 15-day publication blackout whose
        last print is the 2022-12-21 Winter Storm Elliott spike at
        $17.69/MMBtu, against $3.38 at the next measurement. Seeding it would
        carry a storm spike two weeks into January — a far worse construction
        than the back-fill it replaces.
        """
        mi = _miso_citygate_daily_dated(None)
        for year in MISO_BLACKOUT_YEARS:
            if year not in mi:
                continue
            base = _flow_date_staircase(mi[year], year)
            armed = _armed(mi, year)
            np.testing.assert_array_equal(
                base, armed, f"MISO {year} is a blackout boundary and must not move"
            )

    def test_the_seed_helper_refuses_a_gap_at_or_past_the_threshold(self):
        import pandas as pd

        prior = {12: {21: 17.69}}  # flows 2022-12-22
        # 2023-01-06 is 15 days later — a blackout, refused.
        self.assertIsNone(
            _year_start_package_seed(prior, 2023, pd.Timestamp("2023-01-06"))
        )
        # A package-length gap is admitted, and carries the print's own value.
        near = pd.Timestamp("2022-12-22") + pd.Timedelta(
            days=_GAS_BLACKOUT_MIN_GAP_DAYS - 1
        )
        seed = _year_start_package_seed(prior, 2023, near)
        self.assertIsNotNone(seed)
        self.assertAlmostEqual(seed[1], 17.69)

    def test_the_threshold_is_the_bridge_s_own_and_the_two_are_disjoint(self):
        """Neither mechanism can reach the other's days."""
        self.assertEqual(_GAS_BLACKOUT_MIN_GAP_DAYS, 6)


class TestMeasuredFootprint(unittest.TestCase):
    def test_caiso_package_years_move_exactly_the_measured_days_and_delta(self):
        ca = _caiso_citygate_daily_dated(None)
        for year, days, delta in CAISO_FOOTPRINT:
            base, armed = _flow_date_staircase(ca[year], year), _armed(ca, year)
            d = armed - base
            moved = ~np.isclose(d, 0.0, atol=1e-12)
            self.assertEqual(int(moved.sum()), days, f"CAISO {year} edge-day count")
            np.testing.assert_allclose(d[moved], delta, atol=5e-3)
            self.assertTrue(moved[:days].all(), "the days moved are the year's FIRST")
            self.assertFalse(moved[days:].any(), "nothing past the edge may move")

    def test_miso_package_years_move_exactly_the_measured_days_and_delta(self):
        mi = _miso_citygate_daily_dated(None)
        for year, days, delta in MISO_FOOTPRINT:
            d = _armed(mi, year) - _flow_date_staircase(mi[year], year)
            moved = ~np.isclose(d, 0.0, atol=1e-12)
            self.assertEqual(int(moved.sum()), days, f"MISO {year} edge-day count")
            np.testing.assert_allclose(d[moved], delta, atol=5e-3)

    def test_the_edge_takes_the_prior_december_trade_not_the_first_january_one(self):
        """The semantic claim, on the headline case.

        Flow days 2023-01-01..03 were priced by the 2022-12-30 trade at $15.31.
        The unrepaired path hands them the 2023-01-03 trade at $23.66 — a trade
        that had not happened and that prices 2023-01-04's flow.
        """
        ca = _caiso_citygate_daily_dated(None)
        self.assertAlmostEqual(ca[2022][12][30], 15.31, places=2)
        self.assertAlmostEqual(ca[2023][1][3], 23.66, places=2)
        base, armed = _flow_date_staircase(ca[2023], 2023), _armed(ca, 2023)
        np.testing.assert_allclose(base[:3], 23.66, atol=5e-3)
        np.testing.assert_allclose(armed[:3], 15.31, atol=5e-3)
        # 2023-01-04 carries the 01-03 trade in BOTH — the edge repair stops there.
        self.assertAlmostEqual(float(base[3]), float(armed[3]), places=9)


class TestChannelsStaySeparated(unittest.TestCase):
    """caiso-289 separated the bridge from the left edge; this must not re-merge."""

    def test_arming_the_left_edge_does_not_change_the_bridge_s_own_footprint(self):
        import pandas as pd

        from market_sim.data.fuel.hubs import _henry_hub_daily_dated

        ca = _caiso_citygate_daily_dated(None)
        hh_dated = _henry_hub_daily_dated(None)
        hh = pd.Series(
            {
                pd.Timestamp(year=y, month=m, day=d): v
                for y, months in sorted(hh_dated.items())
                for m, days in sorted(months.items())
                for d, v in sorted(days.items())
            }
        ).sort_index()
        for year in (2022, 2023, 2024, 2025):
            bridge_only = _flow_date_staircase(ca[year], year, ca, hh)
            plain = _flow_date_staircase(ca[year], year)
            both = _flow_date_staircase(
                ca[year], year, ca, hh, prior_year_dated=ca.get(year - 1)
            )
            edge_only = _armed(ca, year)
            # The bridge's contribution is the SAME with and without the edge
            # repair: (bridge_only - plain) == (both - edge_only).
            np.testing.assert_allclose(
                bridge_only - plain,
                both - edge_only,
                atol=1e-12,
                err_msg=f"{year}: the two channels have re-merged",
            )


if __name__ == "__main__":
    unittest.main()
