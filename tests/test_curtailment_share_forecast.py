"""Tests for the forecast leg of the WP-B WTX curtailment-share driver.

The backcast leg (scripts/run_calibration.py, guarded on a measured-HSL year)
is covered by tests/test_curate_ercot_wtx_congestion.py; this file covers the
forecast wiring added for runner.py:

* :func:`market_sim.data.curtailment_share.forecast_wtx_curtail_multipliers` —
  the gate (ERCOT-only, driver flag, forecast mode) and the ceiling shape
  (corridor rows < 1 in congested cells, other zones exactly 1.0);
* self-scaling — growing the West VRE build deepens the net-load troughs and
  re-composes the decile cells, so the potential-weighted corridor congestion
  share (the driver's forced-curtailment rate up to the depth factor) does not
  decrease and the absolute curtailed energy grows with the build-out;
* the ``load_renewable_profiles`` forecast gross-up — with the driver on, the
  ERCOT forecast wind/solar CF bound rides the *uncurtailed* potential basis
  (delivered / (1 - reference rate)), strictly above the delivered basis, and
  is byte-identical with the driver off (no double-curtailment: the gross-up
  and the ceiling share one gate).

Uses the committed derived share table (data/raw/reference/
ercot_wtx_curtailment_share.csv) and the committed EIA extracts — no solve.
"""

import unittest

import numpy as np

from market_sim.config import paths
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.curtailment_share import (
    WEST_CORRIDOR_ZONES,
    forecast_wtx_curtail_multipliers,
    load_share_table,
)

_REFERENCE_DIR = paths.RAW_DIR / "reference"

ERCOT_ZONES = get_iso_config("ERCOT").zone_names
_T = 8760


def _synthetic_state(rng: np.random.Generator, vre_scale: float = 1.0):
    """Return (demand, wind_cf, wind_cap, solar_cf, solar_cap) for ERCOT zones.

    A stylized but ERCOT-shaped year: sinusoidal demand with diurnal + seasonal
    ripple, windy-night wind CF and midday solar CF; ``vre_scale`` grows the
    West/Panhandle build so tests can compare penetration levels.
    """
    n_zones = len(ERCOT_ZONES)
    t = np.arange(_T, dtype=float)
    diurnal = np.sin(2 * np.pi * (t % 24) / 24 - np.pi / 2)
    seasonal = np.cos(2 * np.pi * (t / _T) * 2)
    demand_sys = 55_000 + 12_000 * diurnal + 8_000 * seasonal
    demand = np.tile(demand_sys / n_zones, (n_zones, 1))

    wind_cf_row = np.clip(
        0.45 - 0.25 * diurnal + 0.15 * rng.standard_normal(_T), 0.0, 1.0
    )
    solar_cf_row = np.clip(0.5 * (diurnal + 1.0) - 0.3, 0.0, 1.0)
    wind_cf = np.tile(wind_cf_row, (n_zones, 1))
    solar_cf = np.tile(solar_cf_row, (n_zones, 1))

    wind_cap = np.zeros(n_zones)
    solar_cap = np.zeros(n_zones)
    for i, z in enumerate(ERCOT_ZONES):
        if z in WEST_CORRIDOR_ZONES:
            wind_cap[i] = 15_000 * vre_scale
            solar_cap[i] = 8_000 * vre_scale
        elif z in ("South", "Coast"):
            wind_cap[i] = 4_000
            solar_cap[i] = 2_000
    return demand, wind_cf, wind_cap, solar_cf, solar_cap


class TestForecastGate(unittest.TestCase):
    """forecast_wtx_curtail_multipliers gating and ceiling shape."""

    def setUp(self):
        self.rng = np.random.default_rng(7)
        self.state = _synthetic_state(self.rng)
        if load_share_table(_REFERENCE_DIR) is None:
            self.skipTest("derived share table not present")

    def _mult(self, config, iso="ERCOT"):
        demand, wind_cf, wind_cap, solar_cf, solar_cap = self.state
        return forecast_wtx_curtail_multipliers(
            config,
            iso,
            2030,
            demand,
            wind_cf,
            wind_cap,
            solar_cf,
            solar_cap,
            list(ERCOT_ZONES),
        )

    def test_gate_closed_by_default(self):
        self.assertIsNone(self._mult(ScenarioConfig()))

    def test_gate_closed_in_backcast_mode(self):
        cfg = ScenarioConfig(mode="backcast", ercot_wtx_curtailment_driver=True)
        self.assertIsNone(self._mult(cfg))

    def test_gate_closed_off_ercot(self):
        cfg = ScenarioConfig(ercot_wtx_curtailment_driver=True)
        self.assertIsNone(self._mult(cfg, iso="CAISO"))

    def test_ceiling_corridor_only(self):
        cfg = ScenarioConfig(ercot_wtx_curtailment_driver=True)
        mult = self._mult(cfg)
        self.assertIsNotNone(mult)
        wind_mult, solar_mult = mult
        self.assertEqual(wind_mult.shape, (len(ERCOT_ZONES), _T))
        for i, z in enumerate(ERCOT_ZONES):
            if z in WEST_CORRIDOR_ZONES:
                self.assertLess(wind_mult[i].min(), 1.0)
                self.assertGreater(wind_mult[i].min(), 0.0)
            else:
                np.testing.assert_array_equal(wind_mult[i], 1.0)
                np.testing.assert_array_equal(solar_mult[i], 1.0)

    def test_depth_zero_is_inert(self):
        cfg = ScenarioConfig(
            ercot_wtx_curtailment_driver=True,
            ercot_wtx_curtail_depth_wind=0.0,
            ercot_wtx_curtail_depth_solar=0.0,
        )
        mult = self._mult(cfg)
        self.assertIsNotNone(mult)
        np.testing.assert_array_equal(mult[0], 1.0)
        np.testing.assert_array_equal(mult[1], 1.0)


class TestSelfScaling(unittest.TestCase):
    """More West VRE -> the driver's forced-curtailment volume grows.

    The within-year percentile axis fixes the hour-count per decile, so the
    self-scaling channel is compositional (which hours land in the deep
    deciles) plus the potential itself: the potential-weighted corridor share
    must not fall as the build grows, and the absolute curtailed energy
    (share x potential) must grow materially. The *rate* under-escalating at
    deep penetration is the documented percentile-normalization assumption
    (handoff §8), not a target of this test.
    """

    def test_curtailed_energy_grows_with_buildout(self):
        if load_share_table(_REFERENCE_DIR) is None:
            self.skipTest("derived share table not present")
        rng = np.random.default_rng(7)
        cfg = ScenarioConfig(ercot_wtx_curtailment_driver=True)

        def curtailed(vre_scale: float) -> tuple[float, float]:
            demand, wind_cf, wind_cap, solar_cf, solar_cap = _synthetic_state(
                rng, vre_scale
            )
            mult = forecast_wtx_curtail_multipliers(
                cfg,
                "ERCOT",
                2030,
                demand,
                wind_cf,
                wind_cap,
                solar_cf,
                solar_cap,
                list(ERCOT_ZONES),
            )
            assert mult is not None
            wind_mult = mult[0]
            pot = wind_cap[:, None] * wind_cf  # (n_zones, T) potential MW
            forced = (pot * (1.0 - wind_mult)).sum()  # driver-forced MWh
            rate = forced / pot[wind_cap > 0].sum()
            return forced, rate

        forced_1x, rate_1x = curtailed(1.0)
        forced_2x, rate_2x = curtailed(2.0)
        self.assertGreater(forced_1x, 0.0)
        # Absolute forced-curtailed energy grows materially with the build.
        self.assertGreater(forced_2x, 1.8 * forced_1x)
        # The energy-weighted rate does not decrease as troughs deepen
        # (compositional self-scaling; small tolerance for re-binning noise).
        self.assertGreaterEqual(rate_2x, rate_1x * 0.98)


class TestForecastGrossUp(unittest.TestCase):
    """load_renewable_profiles hands the uncurtailed basis under the gate."""

    def test_gross_up_only_with_driver_on(self):
        from market_sim.data.renewables import (
            _reference_curtailment_rate,
            load_renewable_profiles,
        )

        if _reference_curtailment_rate("ERCOT", "wind") is None:
            self.skipTest("no ERCOT HSL reference year present")
        iso_config = get_iso_config("ERCOT")
        base = ScenarioConfig()  # forecast mode, driver off
        on = ScenarioConfig(ercot_wtx_curtailment_driver=True)
        wind_cf_off, wind_cap_off, solar_cf_off, solar_cap_off = (
            load_renewable_profiles("ERCOT", base.weather_year, iso_config, base)
        )
        wind_cf_on, wind_cap_on, solar_cf_on, _ = load_renewable_profiles(
            "ERCOT", on.weather_year, iso_config, on
        )
        np.testing.assert_array_equal(wind_cap_on, wind_cap_off)
        rate_w, _ = _reference_curtailment_rate("ERCOT", "wind")
        rate_s, _ = _reference_curtailment_rate("ERCOT", "solar")
        # Uncurtailed potential basis: never below delivered, mean strictly
        # above, and exactly delivered/(1-rate) wherever the gross-up did not
        # clip at CF=1 before the vintage-ramp/zone distribution (the clip is
        # applied at the ISO-profile level, so ramped cells inherit it).
        for on_cf, off_cf, rate, held in (
            (wind_cf_on, wind_cf_off, rate_w, wind_cap_off > 0),
            (solar_cf_on, solar_cf_off, rate_s, solar_cap_off > 0),
        ):
            self.assertTrue(np.all(on_cf[held] >= off_cf[held] - 1e-12))
            self.assertGreater(on_cf[held].mean(), off_cf[held].mean())
            # Elementwise the uplift is bounded by the reference-rate gross-up
            # (cells clipped at CF=1 pre-ramp uplift less), and the typical
            # (median) cell carries exactly 1/(1-rate).
            pos = held[:, None] & (off_cf > 1e-6)
            ratio = on_cf[pos] / off_cf[pos]
            self.assertTrue(np.all(ratio <= 1.0 / (1.0 - rate) + 1e-9))
            self.assertTrue(np.all(ratio >= 1.0 - 1e-12))
            self.assertAlmostEqual(
                float(np.median(ratio)), 1.0 / (1.0 - rate), places=9
            )

    def test_backcast_basis_unchanged_by_flag(self):
        # The backcast bound is the measured HSL potential; the gross-up gate
        # must not touch it (run_calibration.py owns the backcast ceiling).
        from market_sim.data.renewables import load_renewable_profiles

        iso_config = get_iso_config("ERCOT")
        off = ScenarioConfig(mode="backcast", weather_year=2023)
        on = ScenarioConfig(
            mode="backcast", weather_year=2023, ercot_wtx_curtailment_driver=True
        )
        wind_off, *_ = load_renewable_profiles("ERCOT", 2023, iso_config, off)
        wind_on, *_ = load_renewable_profiles("ERCOT", 2023, iso_config, on)
        np.testing.assert_array_equal(wind_on, wind_off)


if __name__ == "__main__":
    unittest.main()
