"""Tests for the eGRID fossil CO2 emission-rate loader and class intensity."""

import unittest

import pandas as pd

from market_sim.data import egrid


class VintageTests(unittest.TestCase):
    def test_vintage_for_year(self):
        # 2023 anchors itself; later years use the latest released vintage.
        self.assertEqual(egrid.egrid_vintage_for_year(2023), 2023)
        self.assertEqual(egrid.egrid_vintage_for_year(2024), 2024)
        self.assertEqual(egrid.egrid_vintage_for_year(2025), 2024)
        self.assertEqual(egrid.egrid_vintage_for_year(2030), 2024)


class LoaderTests(unittest.TestCase):
    """Exercise the real eGRID workbook (committed under data/raw/fleet-egrid)."""

    def test_load_egrid_plant_co2_shape_and_positivity(self):
        df = egrid.load_egrid_plant_co2(2024)
        self.assertFalse(df.empty)
        self.assertEqual(
            set(df.columns),
            {"plant_id", "fuel_cat", "net_mwh", "co2_tons", "co2_kg_per_mwh_net"},
        )
        # Only fossil categories, all with positive generation and a finite rate.
        self.assertTrue(df["fuel_cat"].isin(egrid.FOSSIL_FUEL_CATEGORIES).all())
        self.assertTrue((df["net_mwh"] > 0).all())
        self.assertTrue((df["co2_kg_per_mwh_net"] > 0).all())
        # Coal is far more carbon-intensive than gas — a sanity check on units
        # (kg CO2 / net MWh): coal ~900-1300, gas CC/CT ~350-650.
        coal = df[df["fuel_cat"] == "COAL"]["co2_kg_per_mwh_net"].median()
        gas = df[df["fuel_cat"] == "GAS"]["co2_kg_per_mwh_net"].median()
        self.assertGreater(coal, gas)
        self.assertGreater(coal, 700.0)
        self.assertLess(gas, 900.0)

    def test_fossil_rate_map_covers_many_plants(self):
        rate = egrid.fossil_co2_rate_map(2024)
        self.assertGreater(len(rate), 1000)
        self.assertTrue(all(v > 0 for v in rate.values()))

    def test_build_fossil_co2_rates(self):
        df = egrid.build_fossil_co2_rates([2023, 2024])
        self.assertFalse(df.empty)
        self.assertEqual(set(df["year"]), {2023, 2024})
        self.assertTrue(set(df["source"]) <= {"campd", "egrid"})
        # CAMPD-measured rows are the override layer; eGRID is the base.
        self.assertGreater((df["source"] == "egrid").sum(), 0)


class CampdOverrideTests(unittest.TestCase):
    def test_campd_overrides_egrid(self):
        # When a plant appears in both layers the CAMPD-measured rate wins.
        egrid._EGRID_RATE_CACHE[2024] = {10: 500.0, 20: 900.0}
        egrid._CAMPD_RATE_CACHE = {10: 480.0}
        try:
            m = {**egrid._egrid_rate_map(2024), **egrid._campd_rate_map()}
            self.assertEqual(m[10], 480.0)  # CAMPD override
            self.assertEqual(m[20], 900.0)  # eGRID base unchanged
        finally:
            egrid._EGRID_RATE_CACHE.clear()
            egrid._CAMPD_RATE_CACHE = None


class ClassIntensityTests(unittest.TestCase):
    def test_generation_weighted_intensity(self):
        # Two coal plants of differing intensity; the class intensity is the
        # net-generation-weighted mean, converted kg -> tonnes (/1000).
        gen = pd.DataFrame(
            {
                "plant_id": [1, 2, 3],
                "klass": ["COAL_BIT", "COAL_BIT", "CC_REGULAR"],
                "annual_mwh": [1000.0, 3000.0, 2000.0],
            }
        )
        rate = {1: 1000.0, 2: 1200.0, 3: 400.0}  # kg / net MWh
        out = egrid.class_co2_intensity(gen, rate)
        # COAL_BIT: (1000*1000 + 1200*3000) / 4000 = 1150 kg/MWh -> 1.15 t/MWh
        self.assertAlmostEqual(out["COAL_BIT"], 1.15, places=6)
        self.assertAlmostEqual(out["CC_REGULAR"], 0.40, places=6)

    def test_plant_without_rate_excluded_from_weighting(self):
        gen = pd.DataFrame(
            {
                "plant_id": [1, 2],
                "klass": ["CC_REGULAR", "CC_REGULAR"],
                "annual_mwh": [1000.0, 9999.0],
            }
        )
        rate = {1: 500.0}  # plant 2 has no rate
        out = egrid.class_co2_intensity(gen, rate)
        # Only plant 1 contributes: 500 kg/MWh -> 0.5 t/MWh.
        self.assertAlmostEqual(out["CC_REGULAR"], 0.5, places=6)

    def test_empty_frame(self):
        self.assertEqual(egrid.class_co2_intensity(pd.DataFrame(), {}), {})


if __name__ == "__main__":
    unittest.main()
