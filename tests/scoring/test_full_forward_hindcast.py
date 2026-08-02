"""Tests for the T1-FF full-forward hindcast instrument (FH-1).

Trivial-first, no LP solve — the full-forward *contract* is verified at each
seam (``docs/hindcast-forward-plan-2026-07.md`` §2, §4 rows 2/7/11/12, §5):

* the config predicate (``ScenarioConfig.is_full_forward_hindcast``), the Arm R
  weather-posture field's validation, the relaxed forward-gas validation, and
  cache-key byte-stability at the defaults;
* the harness (``--forward-from-base`` window rules, arm wiring, the as-known
  intake hard error, the holdout-policy parity);
* the four FH-1 leak closures — planned-additions vintage bound, emission-rate
  as-of window + T1-FF quarantine trim, hydro climatology as-of trim, and the
  §4-row-7 gas back-hold trap;
* the generalized ``assert_forward_drivers`` guard covering EVERY solve year;
* the scorer's symmetric ``< 2023`` refusal (rule 22 both bounds).
"""

from __future__ import annotations

import unittest

import pandas as pd
import pytest

from market_sim import runner
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.emission_rates import (
    QUARANTINE_RATE_BASIS_FROM,
    QUARANTINED_RATE_BASIS_YEARS,
    measured_plant_rates,
)
from market_sim.data.fleet import EIA860_OPERABLE_VINTAGE, operable_vintage_year
from market_sim.data.fuel import resolve_annual_gas_price
from market_sim.data.hydro import full_forward_climatology_years
from scripts import run_capacity_hindcast as H
from scripts import run_calibration_full as RCF
from scripts.lib import holdout_policy


def _t1ff_config(**overrides) -> ScenarioConfig:
    """A minimal ERCOT full-forward config (base 2023, Arm R)."""
    base = ScenarioConfig(
        iso="ERCOT",
        mode="forecast",
        hindcast=True,
        start_year=2023,
        end_year=2025,
        eia860_vintage_year=2023,
        gas_price_path="hindcast_realized",
        crossover_forward_year=2023,
        crossover_forward_gas_path="hindcast_realized",
        crossover_solve_year_weather=True,
        weather_year=2023,
    )
    return base.with_overrides(**overrides) if overrides else base


# --------------------------------------------------------------------------- #
# Config predicate + validation + cache-key stability
# --------------------------------------------------------------------------- #
class TestFullForwardConfig(unittest.TestCase):
    def test_predicate_boundary_at_start(self):
        c = _t1ff_config()
        self.assertTrue(c.is_full_forward_hindcast)
        for y in (2023, 2024, 2025):
            self.assertTrue(c.is_crossover_forward_year(y))

    def test_predicate_false_for_crossover_and_plain(self):
        x = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            start_year=2023,
            end_year=2027,
            crossover_forward_year=2026,
        )
        self.assertFalse(x.is_full_forward_hindcast)
        plain = ScenarioConfig(iso="ERCOT", mode="forecast", hindcast=True)
        self.assertFalse(plain.is_full_forward_hindcast)
        self.assertFalse(ScenarioConfig().is_full_forward_hindcast)

    def test_solve_year_weather_requires_full_forward(self):
        with pytest.raises(ValueError, match="full-forward"):
            ScenarioConfig(
                iso="ERCOT",
                mode="forecast",
                hindcast=True,
                start_year=2023,
                end_year=2027,
                crossover_forward_year=2026,
                crossover_solve_year_weather=True,
            )

    def test_hindcast_gas_path_full_forward_only(self):
        # Full-forward: hindcast_* forward gas is legal.
        self.assertEqual(_t1ff_config().crossover_forward_gas_path, "hindcast_realized")
        # Plain crossover: still AEO-only (byte-identical contract).
        with pytest.raises(ValueError, match="AEO path"):
            ScenarioConfig(
                iso="ERCOT",
                mode="forecast",
                hindcast=True,
                start_year=2023,
                end_year=2027,
                crossover_forward_year=2026,
                crossover_forward_gas_path="hindcast_realized",
            )

    def test_cache_key_neutral_at_default_distinct_when_armed(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast", hindcast=True)
        explicit = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            crossover_solve_year_weather=False,
        )
        self.assertEqual(base.cache_key(), explicit.cache_key())
        armed = _t1ff_config()
        off = _t1ff_config(crossover_solve_year_weather=False)
        self.assertNotEqual(armed.cache_key(), off.cache_key())


# --------------------------------------------------------------------------- #
# Harness: window rules, arm wiring, governance parity
# --------------------------------------------------------------------------- #
class TestHarness(unittest.TestCase):
    def test_window_rules(self):
        H._validate_window(2023, 2025, False, True)  # Phase A
        H._validate_window(2021, 2025, False, True)  # Phase B (2022 bridged)
        with pytest.raises(SystemExit):
            H._validate_window(2023, 2026, False, True)  # end past 2025
        with pytest.raises(SystemExit):
            H._validate_window(2020, 2025, False, True)  # below demand floor
        with pytest.raises(SystemExit):
            H._validate_window(2023, 2027, True, True)  # both modes at once

    def test_build_config_arm_r(self):
        c = H.build_config(
            "ERCOT",
            2023,
            2025,
            "realized",
            vintage=2023,
            forward_from_base=True,
            arm="realized",
        )
        self.assertTrue(c.is_full_forward_hindcast)
        self.assertEqual(c.crossover_forward_year, 2023)
        self.assertEqual(c.gas_price_path, "hindcast_realized")
        self.assertEqual(c.crossover_forward_gas_path, "hindcast_realized")
        self.assertEqual(c.weather_year, 2023)
        self.assertTrue(c.crossover_solve_year_weather)
        self.assertEqual(c.hindcast_fuel_variant, "realized")

    def test_build_config_arm_k_base_2021(self):
        c = H.build_config(
            "ERCOT",
            2021,
            2025,
            "realized",
            vintage=2020,
            forward_from_base=True,
            arm="asknown",
        )
        self.assertEqual(c.gas_price_path, "hindcast_asknown_aeo2021")
        self.assertEqual(c.crossover_forward_gas_path, "hindcast_asknown_aeo2021")
        self.assertEqual(c.weather_year, 2021)
        self.assertFalse(c.crossover_solve_year_weather)

    def test_arm_k_base_2023_intake_landed(self):
        # FH-3 landed the AEO2023 Reference vintage, so Arm K at base 2023
        # resolves instead of refusing (this is what unblocked Phase A's Arm K).
        self.assertEqual(
            H.full_forward_gas_path("asknown", 2023), "hindcast_asknown_aeo2023"
        )

    def test_arm_k_missing_intake_hard_errors(self):
        # The refusal itself must survive the intake: a base year whose AEO
        # vintage has NOT been intaken still hard-errors rather than falling
        # back to a different-vintage path (rule 13). 2022 is such a base — no
        # hindcast solves it (rule-22 bridge), so no AEO2022 path exists.
        with pytest.raises(SystemExit, match="hindcast_asknown_aeo2022"):
            H.full_forward_gas_path("asknown", 2022)

    def test_policy_parity(self):
        self.assertEqual(
            holdout_policy.HINDCAST_BRIDGE_YEARS, runner.HINDCAST_BRIDGE_YEARS
        )
        self.assertEqual(H.ALLOWED_SOLVE_YEARS, holdout_policy.HINDCAST_SOLVE_YEARS)
        self.assertEqual(
            holdout_policy.HINDCAST_SOLVE_YEARS,
            holdout_policy.CALIBRATION_YEARS | holdout_policy.HINDCAST_SEED_YEARS,
        )
        self.assertEqual(holdout_policy.FREEZE_FILE, RCF.HOLDOUT_FREEZE_FILE)
        # The emission-rate quarantine trim mirrors the bridge set.
        self.assertEqual(
            QUARANTINED_RATE_BASIS_YEARS | {QUARANTINE_RATE_BASIS_FROM},
            holdout_policy.HINDCAST_BRIDGE_YEARS,
        )

    def test_policy_fails_closed(self):
        v = holdout_policy.hindcast_solve_year_violations([2020, 2022, 2023])
        self.assertEqual(len(v), 2)  # 2020 + 2022 refused, 2023 fine
        self.assertTrue(any("2020" in s for s in v))
        self.assertTrue(any("2022" in s for s in v))


# --------------------------------------------------------------------------- #
# Leak 2: vintage-derived operable bound (plan §4 row 2)
# --------------------------------------------------------------------------- #
class TestOperableVintage(unittest.TestCase):
    def test_vintage_dir_maps_to_its_year(self):
        self.assertEqual(operable_vintage_year("data/raw/eia-860/vintage_2021"), 2021)
        self.assertEqual(operable_vintage_year("data/raw/eia-860/vintage_2023"), 2023)

    def test_top_level_maps_to_constant(self):
        self.assertEqual(
            operable_vintage_year("data/raw/eia-860"), EIA860_OPERABLE_VINTAGE
        )


# --------------------------------------------------------------------------- #
# Leak 12: emission-rate as-of window + quarantine trim (plan §4 row 12)
# --------------------------------------------------------------------------- #
class TestEmissionRateWindow(unittest.TestCase):
    def _v2(self) -> pd.DataFrame:
        rows = []
        for y in range(2019, 2027):
            rows.append(
                {
                    "iso": "PJM",
                    "year": y,
                    "plant_id": 1,
                    "primary_fuel": "gas",
                    # Rate encodes the year so the selected basis is readable
                    # off the result: mean over selected (400 + y - 2019).
                    "co2_kg": float(400 + y - 2019),
                    "net_mwh": 1.0,
                }
            )
        return pd.DataFrame(rows)

    def _basis_sum(self, target, **kw) -> float:
        r = measured_plant_rates(self._v2(), "PJM", target, "forecast", window=3, **kw)
        return round(r[(1, "gas")] * 1000 * 3 - 3 * 400, 6)

    def test_forecast_lane_unbounded_is_unchanged(self):
        # as_of None (the plain forecast lane): last-3-in-artifact basis
        # {2024, 2025, 2026} regardless of target — byte-identical to pre-FH-1.
        self.assertEqual(self._basis_sum(2024), 5 + 6 + 7)

    def test_as_of_bound(self):
        # Hindcast lane, target 2023: basis {2021, 2022, 2023}.
        self.assertEqual(self._basis_sum(2023, as_of_year=2023), 2 + 3 + 4)

    def test_t1ff_quarantine_trim(self):
        # T1-FF: 2022 leaves the basis -> {2020, 2021, 2023}; asserting no
        # quarantined year can enter (2026 is excluded by the same trim).
        self.assertEqual(
            self._basis_sum(2023, as_of_year=2023, exclude_quarantined=True),
            1 + 2 + 4,
        )

    def test_backcast_branch_untouched(self):
        r = measured_plant_rates(self._v2(), "PJM", 2023, "backcast")
        self.assertAlmostEqual(r[(1, "gas")] * 1000, 404.0)


# --------------------------------------------------------------------------- #
# Leak 11: hydro climatology as-of trim (plan §4 row 11)
# --------------------------------------------------------------------------- #
class TestHydroClimatology(unittest.TestCase):
    def test_base_2023_window(self):
        self.assertEqual(full_forward_climatology_years(2023), (2021, 2023))

    def test_base_2021_window_is_thin_not_widened(self):
        # A single water year — the disclosed Phase-B thinness finding; the
        # window regenerates from the as-of date, it is never widened by hand.
        self.assertEqual(full_forward_climatology_years(2021), (2021,))

    def test_2022_never_enters(self):
        for base in (2022, 2023, 2024, 2025):
            self.assertNotIn(2022, full_forward_climatology_years(base))


# --------------------------------------------------------------------------- #
# Leak 7 guard: gas back-hold trap (plan §4 row 7)
# --------------------------------------------------------------------------- #
class TestGasBackHoldTrap(unittest.TestCase):
    def test_full_forward_below_earliest_knot_raises(self):
        c = _t1ff_config(
            start_year=2021,
            end_year=2025,
            crossover_forward_year=2021,
            weather_year=2021,
            eia860_vintage_year=2020,
            crossover_forward_gas_path="mid",  # knots start 2023
        )
        with pytest.raises(ValueError, match="back-hold"):
            resolve_annual_gas_price(c, 2021)

    def test_full_forward_covered_trajectory_resolves(self):
        c = _t1ff_config(
            start_year=2021,
            end_year=2025,
            crossover_forward_year=2021,
            weather_year=2021,
            eia860_vintage_year=2020,
        )
        self.assertGreater(resolve_annual_gas_price(c, 2021), 0.0)

    def test_plain_crossover_unaffected(self):
        x = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            start_year=2023,
            end_year=2027,
            gas_price_path="hindcast_realized",
            crossover_forward_year=2026,
        )
        self.assertGreater(resolve_annual_gas_price(x, 2026), 0.0)


# --------------------------------------------------------------------------- #
# Generalized forward-driver guard
# --------------------------------------------------------------------------- #
class TestAssertForwardDrivers(unittest.TestCase):
    def test_t1ff_arm_r_clean(self):
        c = H.build_config(
            "ERCOT",
            2023,
            2025,
            "realized",
            vintage=2023,
            forward_from_base=True,
            arm="realized",
        )
        self.assertEqual(H.assert_forward_drivers(c, 2023, 2025), [])

    def test_t1ff_base_2021_bridge_skipped_and_clean(self):
        c = H.build_config(
            "ERCOT",
            2021,
            2025,
            "realized",
            vintage=2020,
            forward_from_base=True,
            arm="realized",
        )
        self.assertEqual(H.assert_forward_drivers(c, 2021, 2025), [])

    def test_back_hold_surfaces_as_violation(self):
        # A hand-built full-forward config on an AEO path that cannot cover
        # its window: the guard reports the trap instead of crashing.
        c = _t1ff_config(
            start_year=2021,
            end_year=2025,
            crossover_forward_year=2021,
            weather_year=2021,
            eia860_vintage_year=2020,
            gas_price_path="mid",
            crossover_forward_gas_path="mid",
            crossover_solve_year_weather=False,
        )
        v = H.assert_forward_drivers(c, 2021, 2025)
        self.assertTrue(any("back-hold" in s for s in v), v)

    def test_plain_hindcast_noop(self):
        c = H.build_config("ERCOT", 2021, 2025, "realized")
        self.assertEqual(H.assert_forward_drivers(c, 2021, 2025), [])


# --------------------------------------------------------------------------- #
# Scorer: symmetric lower bound (rule 22 both sides)
# --------------------------------------------------------------------------- #
class TestScorerBounds(unittest.TestCase):
    def test_lower_and_upper_refusals(self):
        from scripts import score_crossover as SC

        for y in (2019, 2021, 2022):
            with pytest.raises(ValueError, match="below the scoring window"):
                SC._assert_scoreable_year(y)
        for y in (2026, 2027):
            with pytest.raises(ValueError, match="quarantined"):
                SC._assert_scoreable_year(y)
        for y in (2023, 2024, 2025):
            self.assertEqual(SC._assert_scoreable_year(y), y)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(unittest.main())
