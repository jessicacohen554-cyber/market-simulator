"""Tests for the T1-X crossover instrument (FF-0E, plan §2.2).

Trivial-first: the crossover *contract* is verified at each seam without a real
LP solve —

* config predicate + validation + cache-key neutrality
  (:class:`ScenarioConfig.is_crossover_forward_year`);
* the fuel path switch — realized "hindcast_realized" gas for the in-sample
  years (< boundary), the AEO forward path for forward years (>= boundary);
* the F923 plant-monthly overlay (a backcast-gated MEASURED loader) is SKIPPED
  for a crossover forward year and REACHED for an in-sample year;
* the harness helpers ``_validate_window`` / ``build_config`` /
  ``assert_forward_drivers`` / ``assert_pipeline_from_vintage`` (the 2023-vintage
  leakage guard);
* a fake-solve run of ``run_scenario_iso`` down the crossover path proving the
  realized per-year demand loader fires ONLY for the in-sample years and the
  2026 forward year is SOLVED, not bridged.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from market_sim import runner
from market_sim.config.constants import (
    GAS_BASIS_DIFFERENTIAL,
    HENRY_HUB_TRAJECTORIES,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import fuel as fuelmod
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel import _hold_flat_extrapolate, resolve_annual_gas_price
from market_sim.pipeline import commitment as pipeline_commitment
from market_sim.pipeline import solve as pipeline_solve
from market_sim.results import cache
from scripts import run_capacity_hindcast as H
from tests.test_runner import _fake_solve, _FakeDispatchModel


def _crossover_config(**overrides) -> ScenarioConfig:
    """A minimal ERCOT crossover config (2023 vintage, boundary 2026)."""
    base = ScenarioConfig(
        iso="ERCOT",
        mode="forecast",
        hindcast=True,
        start_year=2023,
        end_year=2027,
        eia860_vintage_year=2023,
        gas_price_path="hindcast_realized",
        crossover_forward_year=2026,
        crossover_forward_gas_path="mid",
        weather_year=2025,
    )
    return base.with_overrides(**overrides) if overrides else base


# --------------------------------------------------------------------------- #
# Config predicate + validation + cache-key neutrality
# --------------------------------------------------------------------------- #
class TestCrossoverConfig(unittest.TestCase):
    def test_forward_year_predicate(self):
        c = _crossover_config()
        for y in (2023, 2024, 2025):
            self.assertFalse(c.is_crossover_forward_year(y))
        for y in (2026, 2027):
            self.assertTrue(c.is_crossover_forward_year(y))

    def test_plain_config_never_forward(self):
        """A plain hindcast/forecast (no boundary) is never a forward year."""
        plain = ScenarioConfig()
        self.assertIsNone(plain.crossover_forward_year)
        self.assertFalse(plain.is_crossover_forward_year(2026))

    def test_default_cache_key_unchanged_by_new_fields(self):
        """The new fields are cache-neutral at their defaults (no key change)."""
        d = ScenarioConfig()
        self.assertIsNone(d.crossover_forward_year)
        self.assertEqual(d.crossover_forward_gas_path, "mid")
        # A plain hindcast carrying the defaults keys identically to one built
        # before the fields existed (they are popped when default).
        h = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            start_year=2021,
            end_year=2025,
            eia860_vintage_year=2020,
            gas_price_path="hindcast_realized",
        )
        self.assertNotEqual(_crossover_config().cache_key(), h.cache_key())

    def test_boundary_requires_hindcast_forecast(self):
        with pytest.raises(ValueError, match="requires hindcast=True"):
            ScenarioConfig(mode="forecast", crossover_forward_year=2026)
        with pytest.raises(ValueError, match="requires hindcast=True"):
            ScenarioConfig(mode="backcast", hindcast=True, crossover_forward_year=2026)

    def test_forward_gas_path_validated(self):
        with pytest.raises(ValueError, match="AEO path"):
            ScenarioConfig(
                mode="forecast",
                hindcast=True,
                crossover_forward_year=2026,
                crossover_forward_gas_path="hindcast_realized",
            )


# --------------------------------------------------------------------------- #
# Fuel path switch at the boundary
# --------------------------------------------------------------------------- #
class TestCrossoverGasPath(unittest.TestCase):
    def test_realized_then_aeo(self):
        c = _crossover_config()
        basis = GAS_BASIS_DIFFERENTIAL.get("ERCOT", 0.0)
        # In-sample years price on the realized ("hindcast_realized") path.
        for y in (2023, 2024, 2025):
            expect = (
                _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES["hindcast_realized"], y)
                + basis
            )
            self.assertAlmostEqual(resolve_annual_gas_price(c, y), expect, places=6)
        # Forward years price on the AEO forward path, NOT the realized one held
        # flat (2025 realized 3.53 != AEO 2026).
        for y in (2026, 2027):
            expect_aeo = (
                _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES["mid"], y) + basis
            )
            realized_flat = (
                _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES["hindcast_realized"], y)
                + basis
            )
            self.assertAlmostEqual(resolve_annual_gas_price(c, y), expect_aeo, places=6)
            self.assertNotAlmostEqual(
                resolve_annual_gas_price(c, y), realized_flat, places=3
            )

    def test_plain_hindcast_gas_unchanged(self):
        """A plain hindcast (no boundary) always uses gas_price_path."""
        h = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            start_year=2021,
            end_year=2025,
            gas_price_path="hindcast_realized",
        )
        basis = GAS_BASIS_DIFFERENTIAL.get("ERCOT", 0.0)
        # Even at 2026 the plain hindcast holds the realized path flat (no AEO
        # switch) — the crossover branch never fires.
        expect = (
            _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES["hindcast_realized"], 2026)
            + basis
        )
        self.assertAlmostEqual(resolve_annual_gas_price(h, 2026), expect, places=6)


# --------------------------------------------------------------------------- #
# F923 plant-monthly overlay skip (the key backcast-gated MEASURED loader)
# --------------------------------------------------------------------------- #
class TestF923OverlaySkip(unittest.TestCase):
    def _coal_fleet(self):
        gens = [
            Generator(
                unit_id="COAL",
                name="Coal",
                zone="north",
                fuel_type="coal",
                pmax_mw=600.0,
            )
        ]
        return generators_to_fleet_arrays(gens, ["north", "south"], hours=24)

    def test_forward_year_skips_overlay(self):
        """A crossover forward year returns BEFORE touching the F923 cache."""
        fleet = self._coal_fleet()
        prices = np.full((fleet.n_gen, 24), 2.0)
        c = _crossover_config(hours=24)

        def _boom(*a, **k):
            raise AssertionError("_load_monthly_cache reached for a forward year")

        with patch.object(fuelmod, "_load_monthly_cache", side_effect=_boom):
            # Forward year: must return early (no raise, prices untouched).
            fuelmod.apply_plant_monthly_fuel_prices(prices, fleet, c, 2026)
        self.assertTrue(np.allclose(prices, 2.0))

    def test_in_sample_year_reaches_overlay(self):
        """An in-sample crossover year DOES reach the F923 cache loader."""
        fleet = self._coal_fleet()
        prices = np.full((fleet.n_gen, 24), 2.0)
        c = _crossover_config(hours=24)
        with patch.object(
            fuelmod, "_load_monthly_cache", side_effect=RuntimeError("reached")
        ):
            with pytest.raises(RuntimeError, match="reached"):
                fuelmod.apply_plant_monthly_fuel_prices(prices, fleet, c, 2024)


# --------------------------------------------------------------------------- #
# Harness helpers
# --------------------------------------------------------------------------- #
class TestHarnessHelpers(unittest.TestCase):
    def test_validate_window_crossover_ok(self):
        H._validate_window(2023, 2027, crossover=True)  # no raise
        H._validate_window(2023, 2026, crossover=True)  # no raise

    def test_validate_window_crossover_rejects_out_of_window(self):
        with pytest.raises(SystemExit):
            H._validate_window(2023, 2028, crossover=True)  # 2028 out
        with pytest.raises(SystemExit):
            H._validate_window(2022, 2027, crossover=True)  # start < 2023

    def test_validate_window_hindcast_holdout_intact(self):
        """Plain-hindcast guard unchanged: 2026 is still a rule-22 holdout."""
        H._validate_window(2021, 2025, crossover=False)  # no raise
        with pytest.raises(SystemExit):
            H._validate_window(2021, 2026, crossover=False)  # 2026 rejected

    def test_build_config_crossover_fields(self):
        c = H.build_config(
            "ERCOT",
            2023,
            2027,
            "realized",
            vintage=2023,
            crossover=True,
        )
        self.assertTrue(c.hindcast)
        self.assertEqual(c.mode, "forecast")
        self.assertEqual(c.eia860_vintage_year, 2023)
        self.assertEqual(c.crossover_forward_year, H.CROSSOVER_FORWARD_YEAR)
        self.assertEqual(c.crossover_forward_gas_path, "mid")
        # Forward demand anchors on the last realized year (boundary - 1 = 2025).
        self.assertEqual(c.weather_year, H.CROSSOVER_FORWARD_YEAR - 1)

    def test_build_config_plain_unchanged(self):
        c = H.build_config("ERCOT", 2021, 2025, "realized")
        self.assertIsNone(c.crossover_forward_year)
        self.assertEqual(c.eia860_vintage_year, H.DEFAULT_VINTAGE_YEAR)
        self.assertEqual(c.weather_year, ScenarioConfig().weather_year)

    def test_assert_forward_drivers_clean(self):
        c = H.build_config(
            "ERCOT", 2023, 2027, "realized", vintage=2023, crossover=True
        )
        self.assertEqual(H.assert_forward_drivers(c, 2023, 2027), [])

    def test_assert_forward_drivers_noop_plain(self):
        c = H.build_config("ERCOT", 2021, 2025, "realized")
        self.assertEqual(H.assert_forward_drivers(c, 2021, 2025), [])


# --------------------------------------------------------------------------- #
# 2023-vintage leakage guard (item 3)
# --------------------------------------------------------------------------- #
class TestVintage2023Leakage(unittest.TestCase):
    def _ledger(self, plant_code: str):
        return {
            2026: {
                "thermal_additions": [
                    {
                        "source": "planned",
                        "eia860_id": f"planned_{plant_code}_1",
                        "fuel": "gas_cc",
                        "mw": 500.0,
                    }
                ]
            }
        }

    def test_absent_unit_flags_violation(self):
        """A planned unit whose plant is absent from the 2023 proposed sheet is
        a leakage violation (a forecast started at 2023 can't know it)."""
        viol = H.assert_pipeline_from_vintage(
            "ERCOT", Path("."), self._ledger("999999999"), vintage=2023
        )
        self.assertTrue(viol)
        self.assertIn("2023 vintage", viol[0])

    def test_present_unit_is_clean(self):
        """A planned unit whose plant IS in the 2023 proposed sheet is clean."""
        proposed = pd.read_parquet(
            "data/raw/eia-860/vintage_2023/eia860_generator_proposed.parquet"
        )
        codes = pd.to_numeric(proposed["Plant Code"], errors="coerce").dropna()
        assert len(codes), "2023 proposed sheet unexpectedly empty"
        present = str(int(codes.iloc[0]))
        viol = H.assert_pipeline_from_vintage(
            "ERCOT", Path("."), self._ledger(present), vintage=2023
        )
        self.assertEqual(viol, [])


# --------------------------------------------------------------------------- #
# Fake-solve run down the crossover path (item 1 end-to-end routing)
# --------------------------------------------------------------------------- #
class TestCrossoverRunnerPath(unittest.TestCase):
    """The realized per-year demand loader fires only for in-sample years; the
    2026 forward year is SOLVED (not bridged) on forward drivers."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)
        _FakeDispatchModel.n_solves = 0

    def tearDown(self):
        cache.CACHE_ROOT = self._orig_root
        self._tmp.cleanup()

    def test_forward_year_demand_not_from_realized_loader(self):
        # ERCOT crossover 2023->2026 (one forward year) — real data loading,
        # faked LP solve. Spy the realized per-year demand loader.
        # Disable the confirmed-exit channel: it reads the derived (gitignored)
        # data/clean registry, absent in a fresh checkout, and is orthogonal to
        # the demand routing this test exercises.
        config = H.build_config(
            "ERCOT",
            2023,
            2026,
            "realized",
            vintage=2023,
            crossover=True,
        ).with_overrides(confirmed_exits_enabled=False)
        real_load_demand = runner.load_demand
        per_year_calls: list[int] = []

        def spy_load_demand(iso, year, *a, **k):
            per_year_calls.append(year)
            return real_load_demand(iso, year, *a, **k)

        with (
            patch.object(runner, "load_demand", side_effect=spy_load_demand),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            key = runner.run_scenario_iso(config, "ERCOT")

        # The realized per-year demand loader (config.hindcast branch) fires for
        # the in-sample years 2023-2025 and the weather-year base (2025), but
        # NEVER for the 2026 forward year.
        self.assertNotIn(2026, per_year_calls)
        self.assertIn(2025, per_year_calls)
        # 2026 is SOLVED (a year_2026 parquet exists), not bridged.
        self.assertTrue(cache.is_cached("ERCOT", key, 2026))
        bundle = cache.CACHE_ROOT / "ERCOT" / key
        self.assertTrue((bundle / "year_2026.parquet").exists())


if __name__ == "__main__":
    unittest.main()
