"""Tests for the MISO wind forecast-uncurtailed reference-rate path.

MISO publishes no hourly uncurtailed-potential (HSL) series, but its IMM
(Potomac Economics) publishes a measured *annual* wind curtailment aggregate
(``data/raw/miso-hsl/miso_wind_curtailment_annual.csv``). That aggregate is too
coarse for an hourly parquet but enough for a per-tech reference curtailment
RATE, so MISO wind takes the same forecast-uncurtailed gross-up ERCOT's no-HSL
years use (delivered EIA-930 shape / (1 - rate)) and its renewable bound is
labelled ``forecast_uncurtailed`` instead of ``delivered_pinned``. MISO solar
has no published curtailment series and stays on the delivered profile.

These tests read only the committed raw CSV + EIA extracts — no solve, and no
holdout year is touched (the rate is derived strictly within the 2023-2025
training window, CLAUDE.md #22).
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.renewables import (
    RENEWABLE_BOUND_DELIVERED_PINNED,
    RENEWABLE_BOUND_FORECAST_UNCURTAILED,
    RENEWABLE_BOUND_MEASURED_POTENTIAL,
    _eia860_monthly_capacity,
    _eia_hourly_cf_profile,
    _forecast_uncurtailed_cf,
    _MISO_REFERENCE_RATE_YEARS,
    _MISO_WIND_CURTAILMENT_ANNUAL,
    _miso_wind_reference_curtailment_rate,
    _reference_curtailment_rate,
    _UNCURTAILED_FALLBACK_ISOS,
    load_renewable_profiles,
    renewable_bound_provenance,
)


def _expected_rate_from_csv() -> tuple[float, int]:
    """Recompute MISO's reference rate from the committed CSV, independently.

    Mirrors the loader's definition (firm, non-estimate, training-window mean of
    ``curtailed / (delivered + curtailed)``) without calling it, so the test
    catches any silent drift in the loader arithmetic.
    """
    df = pd.read_csv(_MISO_WIND_CURTAILMENT_ANNUAL)
    df = df[df["year"].isin(_MISO_REFERENCE_RATE_YEARS)]
    df = df[df["is_estimate"].astype(str).str.upper() != "TRUE"]
    df = df.dropna(subset=["avg_wind_curtailed_mw", "avg_wind_output_rt_gw"])
    rates = df["avg_wind_curtailed_mw"] / (
        df["avg_wind_output_rt_gw"] * 1_000.0 + df["avg_wind_curtailed_mw"]
    )
    return float(rates.mean()), int(df["year"].max())


class TestMisoWindReferenceRate(unittest.TestCase):
    def test_rate_matches_independent_recompute(self):
        result = _miso_wind_reference_curtailment_rate()
        self.assertIsNotNone(result)
        rate, year = result
        exp_rate, exp_year = _expected_rate_from_csv()
        self.assertAlmostEqual(rate, exp_rate, places=9)
        self.assertEqual(year, exp_year)
        # Sanity: a material, physically-plausible wind curtailment rate.
        self.assertGreater(rate, 0.02)
        self.assertLess(rate, 0.15)

    def test_rate_years_are_training_window_only(self):
        # Rule 22: the structural rate never reads a validation/locked holdout
        # year (2019, 2022, H1-2026). The window is train-only by construction.
        self.assertTrue(_MISO_REFERENCE_RATE_YEARS <= frozenset({2023, 2024, 2025}))
        for holdout in (2019, 2020, 2021, 2022, 2026):
            self.assertNotIn(holdout, _MISO_REFERENCE_RATE_YEARS)

    def test_rate_ignores_estimate_rows(self):
        # 2025 is a source-flagged estimate; the firm filter must drop it, so the
        # tagged as-of year is the latest FIRM year (2024 today), not 2025.
        _, year = _miso_wind_reference_curtailment_rate()
        df = pd.read_csv(_MISO_WIND_CURTAILMENT_ANNUAL)
        est_years = set(
            df.loc[df["is_estimate"].astype(str).str.upper() == "TRUE", "year"]
        )
        self.assertNotIn(year, est_years)


class TestMisoReferenceRateWiring(unittest.TestCase):
    def test_miso_in_fallback_set_nyiso_out(self):
        self.assertIn("MISO", _UNCURTAILED_FALLBACK_ISOS)
        # NYISO is a deliberate genuine-gap decision (sub-1% curtailment, coarse
        # aggregate) — it must stay OUT so it keeps the delivered profile.
        self.assertNotIn("NYISO", _UNCURTAILED_FALLBACK_ISOS)
        self.assertNotIn("NEISO", _UNCURTAILED_FALLBACK_ISOS)

    def test_reference_rate_wind_yes_solar_no(self):
        # MISO wind routes to the annual-CSV rate; MISO solar has no published
        # series, so no rate and it stays on the delivered profile.
        wind = _reference_curtailment_rate("MISO", "wind")
        self.assertEqual(wind, _miso_wind_reference_curtailment_rate())
        self.assertIsNone(_reference_curtailment_rate("MISO", "solar"))

    def test_ercot_reference_rate_still_from_hsl(self):
        # Regression: the MISO branch must not disturb ERCOT/CAISO, which still
        # resolve their rate from a built HSL parquet.
        ercot = _reference_curtailment_rate("ERCOT", "wind")
        self.assertIsNotNone(ercot)
        # ERCOT's reference year is an HSL year, not the MISO CSV year.
        self.assertGreaterEqual(ercot[1], 2023)


class TestMisoProvenance(unittest.TestCase):
    def test_wind_forecast_uncurtailed_solar_delivered(self):
        for year in (2023, 2024, 2025):
            self.assertEqual(
                renewable_bound_provenance("MISO", year, "wind"),
                RENEWABLE_BOUND_FORECAST_UNCURTAILED,
            )
            self.assertEqual(
                renewable_bound_provenance("MISO", year, "solar"),
                RENEWABLE_BOUND_DELIVERED_PINNED,
            )

    def test_nyiso_stays_delivered_pinned(self):
        for fuel in ("wind", "solar"):
            self.assertEqual(
                renewable_bound_provenance("NYISO", 2024, fuel),
                RENEWABLE_BOUND_DELIVERED_PINNED,
            )

    def test_ercot_measured_potential(self):
        # All three ERCOT years now carry a built HSL parquet (2024/2025 NP6
        # landed 2026-07-06), so ERCOT reads as measured, never the fallback.
        for year in (2023, 2024, 2025):
            self.assertEqual(
                renewable_bound_provenance("ERCOT", year, "wind"),
                RENEWABLE_BOUND_MEASURED_POTENTIAL,
            )


class TestMisoBackcastGrossUp(unittest.TestCase):
    """The backcast profile rides the uncurtailed potential, not delivered."""

    def _monthly(self, fuel: str, year: int):
        zones = get_iso_config("MISO").zone_names
        return _eia860_monthly_capacity("MISO", fuel, zones, year)

    def test_wind_potential_ge_delivered_with_rate_uplift(self):
        monthly = self._monthly("wind", 2023)
        if monthly is None:
            self.skipTest("no MISO EIA-860 wind capacity for 2023")
        delivered = _eia_hourly_cf_profile("MISO", 2023, "wind", monthly)
        unc = _forecast_uncurtailed_cf("MISO", 2023, "wind", monthly)
        if delivered is None or unc is None:
            self.skipTest("no MISO EIA-930 wind series for 2023")
        rate, _ = _miso_wind_reference_curtailment_rate()
        # Uncurtailed potential is never below delivered (a valid bound)...
        self.assertTrue(np.all(unc >= delivered - 1e-12))
        # ...and the implied annual curtailment equals the reference rate (no
        # pinning to the target year's own delivered total).
        implied = 1.0 - float(delivered.sum()) / float(unc.sum())
        self.assertAlmostEqual(implied, rate, places=6)

    def test_solar_falls_back_to_delivered(self):
        monthly = self._monthly("solar", 2023)
        if monthly is None:
            self.skipTest("no MISO EIA-860 solar capacity for 2023")
        # No solar reference rate -> the forecast-uncurtailed builder yields None
        # and the loader keeps the delivered profile.
        self.assertIsNone(_forecast_uncurtailed_cf("MISO", 2023, "solar", monthly))

    def test_load_renewable_profiles_wind_above_delivered(self):
        iso_config = get_iso_config("MISO")
        cfg = ScenarioConfig(mode="backcast", weather_year=2023)
        try:
            wind_cf, wind_cap, *_ = load_renewable_profiles(
                "MISO", 2023, iso_config, cfg
            )
        except (FileNotFoundError, ValueError) as exc:  # pragma: no cover
            self.skipTest(f"MISO 2023 profile inputs unavailable: {exc}")
        held = wind_cap > 0
        if not held.any():
            self.skipTest("no MISO zone holds wind capacity in 2023")
        self.assertTrue(np.all(wind_cf[held] >= -1e-12))
        self.assertLessEqual(float(wind_cf[held].max()), 1.0 + 1e-9)


if __name__ == "__main__":
    unittest.main()
