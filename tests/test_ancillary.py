"""ERCOT ancillary-service revenue: gating, calibration, saturation."""

import unittest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.ancillary import (
    as_revenue_per_mw_yr,
    as_saturation_factor,
)


class TestASRevenue(unittest.TestCase):
    def _cfg(self, **kw):
        return ScenarioConfig(iso="ERCOT", as_revenue_enabled=True, **kw)

    def test_disabled_by_default(self):
        cfg = ScenarioConfig(iso="ERCOT")  # as_revenue_enabled defaults False
        self.assertEqual(as_revenue_per_mw_yr("storage", 4000.0, cfg), 0.0)

    def test_non_ercot_earns_nothing(self):
        cfg = ScenarioConfig(iso="PJM", as_revenue_enabled=True)
        self.assertEqual(as_revenue_per_mw_yr("storage", 4000.0, cfg), 0.0)

    def test_unknown_tech_earns_nothing(self):
        self.assertEqual(as_revenue_per_mw_yr("wind", 4000.0, self._cfg()), 0.0)

    def test_storage_base_rate_at_reference_fleet(self):
        # At the 4 GW calibration point the saturation factor is 1.0, so
        # storage earns the full $169/kW-yr ($169,000/MW-yr) anchor.
        self.assertAlmostEqual(
            as_revenue_per_mw_yr("storage", 4000.0, self._cfg()),
            169_000.0,
            places=0,
        )

    def test_saturation_falls_with_a_growing_fleet(self):
        # Per-kW AS revenue declines steeply as the storage fleet grows past
        # the reference, reproducing the observed 2023->2025 crash.
        r4 = as_revenue_per_mw_yr("storage", 4_000.0, self._cfg())
        r10 = as_revenue_per_mw_yr("storage", 10_000.0, self._cfg())
        r16 = as_revenue_per_mw_yr("storage", 16_000.0, self._cfg())
        self.assertGreater(r4, r10)
        self.assertGreater(r10, r16)
        # ~10 GW lands near the observed 2025 ~$15-20/kW.
        self.assertLess(r10, 25_000.0)

    def test_saturation_capped_at_one_below_reference(self):
        # A fleet smaller than the reference does not inflate revenue above
        # the base rate.
        self.assertEqual(as_saturation_factor(1_000.0), 1.0)
        self.assertAlmostEqual(
            as_revenue_per_mw_yr("storage", 0.0, self._cfg()),
            169_000.0,
            places=0,
        )

    def test_multiplier_scales_revenue(self):
        base = as_revenue_per_mw_yr("storage", 4_000.0, self._cfg())
        doubled = as_revenue_per_mw_yr(
            "storage", 4_000.0, self._cfg(as_revenue_multiplier=2.0)
        )
        self.assertAlmostEqual(doubled, 2.0 * base, places=0)

    def test_thermal_rates_below_storage(self):
        cfg = self._cfg()
        s = as_revenue_per_mw_yr("storage", 4_000.0, cfg)
        ct = as_revenue_per_mw_yr("gas_ct", 4_000.0, cfg)
        st = as_revenue_per_mw_yr("gas_st", 4_000.0, cfg)
        cc = as_revenue_per_mw_yr("gas_cc", 4_000.0, cfg)
        self.assertTrue(s > ct > st > cc > 0.0)


if __name__ == "__main__":
    unittest.main()
