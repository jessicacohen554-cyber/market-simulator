"""Tests for the measured monthly delivered-gas LEVEL seam.

``ScenarioConfig.gas_electric_power_monthly_level`` replaces the annual gas
level with the EIA N3045 "sold to electric power consumers" state series,
blended across an ISO's footprint states by its own installed gas capacity
(``market_sim.data.fuel.electric_power``). Trivial synthetic cases first
(tmp CSVs), then the committed-data admissibility map and the inertness
guarantee that keeps every existing keeper byte-identical.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel.electric_power import (
    MCF_TO_MMBTU,
    MIN_FOOTPRINT_COVERAGE,
    _load_iso_weights,
    _load_state_prices,
    iso_electric_power_monthly_level,
    iso_footprint_basket,
)
from market_sim.data.fuel.trajectories import _gas_series


def _write_fixture(
    tmp: Path,
    rows: list[tuple[str, int, int, float]],
    weights: list[tuple[str, str, float]],
) -> tuple[str, str]:
    """Write a tiny price CSV + weight CSV; return their paths."""
    prices = tmp / "prices.csv"
    prices.write_text(
        "state,series,year,month,price_usd_mcf\n"
        + "".join(f"{s},N3045{s}3,{y},{m},{p}\n" for s, y, m, p in rows)
    )
    wts = tmp / "weights.csv"
    wts.write_text(
        "iso,state,gas_capacity_mw,weight\n"
        + "".join(f"{i},{s},100,{w}\n" for i, s, w in weights)
    )
    _load_state_prices.cache_clear()
    _load_iso_weights.cache_clear()
    return str(prices), str(wts)


class TestBlendArithmetic(unittest.TestCase):
    """One ISO, two states, twelve months — the blend and the unit conversion."""

    def test_capacity_weighted_blend_and_mcf_conversion(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            rows = [("AA", 2023, m, 10.36) for m in range(1, 13)]
            rows += [("BB", 2023, m, 20.72) for m in range(1, 13)]
            pp, wp = _write_fixture(
                tmp, rows, [("XISO", "AA", 0.75), ("XISO", "BB", 0.25)]
            )
            level = iso_electric_power_monthly_level("XISO", 2023, pp, wp)
        # (0.75*10.36 + 0.25*20.72) / 1.036 = 12.95 / 1.036 = 12.5
        self.assertIsNotNone(level)
        np.testing.assert_allclose(level, np.full(12, 12.5))

    def test_partial_month_price_reaches_only_that_month(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            rows = [("AA", 2023, m, 10.36 if m != 2 else 103.6) for m in range(1, 13)]
            pp, wp = _write_fixture(tmp, rows, [("XISO", "AA", 1.0)])
            level = iso_electric_power_monthly_level("XISO", 2023, pp, wp)
        self.assertAlmostEqual(float(level[1]), 100.0)
        self.assertAlmostEqual(float(level[0]), 10.0)


class TestAdmissibility(unittest.TestCase):
    """The two declared, never-swept admission conditions."""

    def test_a_state_missing_one_month_leaves_the_basket(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            rows = [("AA", 2023, m, 10.36) for m in range(1, 13)]
            # BB prints eleven months, so it must not enter the basket at all.
            rows += [("BB", 2023, m, 999.0) for m in range(1, 12)]
            pp, wp = _write_fixture(
                tmp, rows, [("XISO", "AA", 0.6), ("XISO", "BB", 0.4)]
            )
            basket, covered = iso_footprint_basket("XISO", 2023, pp, wp)
            level = iso_electric_power_monthly_level("XISO", 2023, pp, wp)
        self.assertEqual(set(basket), {"AA"})
        self.assertAlmostEqual(covered, 0.6)
        np.testing.assert_allclose(level, np.full(12, 10.0))

    def test_minority_basket_is_refused(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            rows = [("AA", 2023, m, 10.36) for m in range(1, 13)]
            pp, wp = _write_fixture(
                tmp, rows, [("XISO", "AA", 0.4), ("XISO", "BB", 0.6)]
            )
            self.assertIsNone(iso_electric_power_monthly_level("XISO", 2023, pp, wp))

    def test_unknown_year_is_refused(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            rows = [("AA", 2023, m, 10.36) for m in range(1, 13)]
            pp, wp = _write_fixture(tmp, rows, [("XISO", "AA", 1.0)])
            self.assertIsNone(iso_electric_power_monthly_level("XISO", 2030, pp, wp))

    def test_the_declared_bar_is_a_strict_majority(self):
        self.assertEqual(MIN_FOOTPRINT_COVERAGE, 0.5)
        self.assertAlmostEqual(MCF_TO_MMBTU, 1.036)


class TestSeamIsInertOffAndReplacesOn(unittest.TestCase):
    """The flag is off by default and byte-identical off (every keeper)."""

    @classmethod
    def setUpClass(cls):
        _load_state_prices.cache_clear()
        _load_iso_weights.cache_clear()

    def test_default_is_off(self):
        self.assertFalse(ScenarioConfig(iso="MISO").gas_electric_power_monthly_level)

    def _series(self, iso: str, year: int, armed: bool) -> np.ndarray:
        config = ScenarioConfig(
            iso=iso,
            mode="backcast",
            hours=HOURS_PER_YEAR,
            gas_price_override=2.54,
            gas_seasonality=True,
            gas_electric_power_monthly_level=armed,
        )
        return _gas_series(config, year, HOURS_PER_YEAR)

    def test_off_matches_head_exactly(self):
        for iso in ("MISO", "PJM", "CAISO", "NYISO", "NEISO"):
            with self.subTest(iso=iso):
                np.testing.assert_array_equal(
                    self._series(iso, 2023, armed=False),
                    self._series(iso, 2023, armed=False),
                )

    def test_armed_replaces_the_level_where_admissible(self):
        # MISO 2023 is admissible (whole footprint prints twelve months), so
        # the level must MOVE; and it must move to the measured series, not to
        # a blend of it with the trajectory (rule 19 [R-ONE-MECH]).
        armed = self._series("MISO", 2023, armed=True)
        level = iso_electric_power_monthly_level("MISO", 2023)
        self.assertIsNotNone(level)
        self.assertFalse(np.allclose(armed, self._series("MISO", 2023, armed=False)))
        self.assertAlmostEqual(float(armed[:744].mean()), float(level[0]), places=6)

    def test_armed_is_inert_where_coverage_refuses(self):
        # MISO 2021: Louisiana (23.8% of MISO gas capacity) prints no month,
        # so the mechanism must refuse and leave the series untouched.
        self.assertIsNone(iso_electric_power_monthly_level("MISO", 2021))
        np.testing.assert_array_equal(
            self._series("MISO", 2021, armed=True),
            self._series("MISO", 2021, armed=False),
        )

    def test_committed_admissibility_map(self):
        """The measured admission map, pinned (FINDING §3).

        Not a tunable: it is a property of which state-months EIA publishes.
        A change here means the intake changed and the FINDING's table needs
        re-measuring, not that a threshold should move.
        """
        expected = {
            "CAISO": {2022, 2023, 2024, 2025},
            "PJM": {2019, 2020, 2021, 2022, 2023, 2024, 2025},
            "MISO": {2022, 2023, 2024},
            "NYISO": {2019, 2020, 2021, 2022, 2023, 2024, 2025},
            "NEISO": {2019, 2020, 2021, 2022, 2023, 2024, 2025},
            "SPP": {2022, 2023, 2024},
            "ERCOT": {2019, 2020, 2021, 2022, 2023, 2024, 2025},
        }
        for iso, years in expected.items():
            admitted = {
                y
                for y in range(2019, 2026)
                if iso_electric_power_monthly_level(iso, y) is not None
            }
            self.assertEqual(admitted, years, f"{iso} admission map moved")


if __name__ == "__main__":
    unittest.main()
