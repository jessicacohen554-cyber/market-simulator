"""Commercial-operation-date ramp for the backcast fleet.

Covers :mod:`market_sim.data.cod_ramp`: the online-fraction rule, the per-plant
bin-capacity ramp, and the per-generator fleet ramp (drop future units, pro-rate
COD-year units, keep pre-existing ones).
"""
import unittest

import pandas as pd

from market_sim.data.cod_ramp import (
    COD_YEAR_DEFAULT_SHARE,
    online_fraction,
    ramp_bins,
    ramp_fleet,
)
from market_sim.data.fleet import Generator


class TestOnlineFraction(unittest.TestCase):
    def test_built_before_run_year_is_full(self):
        self.assertEqual(online_fraction(2018, 2023), 1.0)

    def test_built_after_run_year_is_zero(self):
        self.assertEqual(online_fraction(2024, 2023), 0.0)

    def test_built_in_run_year_is_prorated(self):
        self.assertEqual(online_fraction(2023, 2023), COD_YEAR_DEFAULT_SHARE)
        self.assertEqual(online_fraction(2023, 2023, cod_year_share=0.25), 0.25)

    def test_unknown_year_is_full(self):
        self.assertEqual(online_fraction(None, 2023), 1.0)


class TestRampBins(unittest.TestCase):
    def _bins(self):
        return pd.DataFrame({
            "Plant_Code": [100, 200, 300, 400],
            "capacity_mw": [500.0, 400.0, 300.0, 200.0],
        })

    def test_drops_future_and_prorates_cod_year(self):
        cod = {100: 2010, 200: 2023, 300: 2024, 400: 2025}
        out = ramp_bins(self._bins(), 2023, cod)
        cap = dict(zip(out["Plant_Code"], out["capacity_mw"]))
        # 100 built 2010 -> full; 200 built 2023 -> half; 300/400 future -> dropped
        self.assertEqual(cap[100], 500.0)
        self.assertAlmostEqual(cap[200], 400.0 * COD_YEAR_DEFAULT_SHARE)
        self.assertNotIn(300, cap)
        self.assertNotIn(400, cap)

    def test_no_op_when_all_built(self):
        cod = {100: 2000, 200: 2001, 300: 2002, 400: 2003}
        out = ramp_bins(self._bins(), 2023, cod)
        self.assertEqual(out["capacity_mw"].sum(), 1400.0)

    def test_unmapped_plant_kept_full(self):
        out = ramp_bins(self._bins(), 2023, {})  # empty map -> all unknown -> full
        self.assertEqual(out["capacity_mw"].sum(), 1400.0)


class TestRampFleet(unittest.TestCase):
    def _gen(self, code, oy, mw=100.0, pmin=20.0):
        return Generator(unit_id=f"u{code}", name=f"n{code}", zone="Z",
                         fuel_type="gas_cc", pmax_mw=mw, pmin_mw=pmin,
                         online_year=oy, plant_code=code)

    def test_drop_future_prorate_cod_keep_old_via_online_year(self):
        gens = [self._gen(1, 2010), self._gen(2, 2023), self._gen(3, 2024)]
        out = ramp_fleet(gens, 2023, cod_map={})  # fall back to online_year
        by = {g.plant_code: g for g in out}
        self.assertIn(1, by)
        self.assertEqual(by[1].pmax_mw, 100.0)
        self.assertAlmostEqual(by[2].pmax_mw, 100.0 * COD_YEAR_DEFAULT_SHARE)
        self.assertAlmostEqual(by[2].pmin_mw, 20.0 * COD_YEAR_DEFAULT_SHARE)
        self.assertNotIn(3, by)  # built 2024, dropped from a 2023 run

    def test_cod_map_overrides_online_year(self):
        # online_year says 2010 but the curated map says 2024 -> dropped.
        g = self._gen(7, 2010)
        out = ramp_fleet([g], 2023, cod_map={7: 2024})
        self.assertEqual(out, [])

    def test_sentinel_online_year_treated_as_unknown(self):
        # online_year == 2000 default sentinel must not drop a real unit.
        g = self._gen(9, 2000)
        out = ramp_fleet([g], 2023, cod_map={})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].pmax_mw, 100.0)


if __name__ == "__main__":
    unittest.main()
