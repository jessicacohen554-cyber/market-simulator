"""Tests for the forward per-plant CO2-rate estimator (data/emission_rates.py)."""

import unittest

import numpy as np
import pandas as pd

from market_sim.data.emission_rates import (
    CF_BANDS,
    OperatingPoint,
    PlantHistory,
    class_median_rates,
    forward_plant_co2_rate,
    fuel_class,
    measured_plant_rates,
)


def _flat_cf() -> np.ndarray:
    return np.full(CF_BANDS, 1.0 / CF_BANDS)


def _hist(
    rows: list[tuple], ops: dict | None = None, group="", fuel=""
) -> PlantHistory:
    """rows: (unit_id, year, net_mwh, co2_kg)."""
    df = pd.DataFrame(rows, columns=["unit_id", "year", "net_mwh", "co2_kg"])
    return PlantHistory(unit_years=df, ops=ops or {}, group=group, fuel=fuel)


class TestBaseTrailingAverage(unittest.TestCase):
    def test_gen_weighted_over_all_years(self):
        # Two years: high-output year dominates the pooled rate.
        h = _hist(
            [
                ("1", 2023, 1000.0, 400000.0),  # 400 kg/MWh
                ("1", 2024, 3000.0, 900000.0),  # 300 kg/MWh
            ]
        )
        r = forward_plant_co2_rate(h, None, None)
        self.assertEqual(r.method, "trailing_avg")
        self.assertEqual(r.n_years, 2)
        # gen-weighted = 1.3e6 / 4000 = 325, not the simple mean 350.
        self.assertAlmostEqual(r.rate_kg_per_mwh_net, 1_300_000.0 / 4000.0)

    def test_trailing_window_truncates(self):
        h = _hist(
            [
                ("1", 2019, 1000.0, 100000.0),  # 100 kg/MWh (old, should drop)
                ("1", 2023, 1000.0, 400000.0),
                ("1", 2024, 1000.0, 400000.0),
            ]
        )
        r = forward_plant_co2_rate(h, None, None, window=2)
        self.assertAlmostEqual(r.rate_kg_per_mwh_net, 400000.0 / 1000.0)
        self.assertEqual(r.n_years, 2)


class TestUnitCompositionMask(unittest.TestCase):
    def test_retired_unit_mask_shifts_parish_style_rate(self):
        # A Parish-style facility: a coal unit and a gas unit under one plant.
        # The blended facility rate mixes them; masking to only the gas unit
        # (coal retired / a separate bin) must move the rate toward gas.
        h = _hist(
            [
                ("coal1", 2024, 1000.0, 1_000_000.0),  # 1000 kg/MWh (coal)
                ("gas1", 2024, 1000.0, 350_000.0),  # 350 kg/MWh (gas)
            ]
        )
        blended = forward_plant_co2_rate(h, None, None)
        self.assertAlmostEqual(blended.rate_kg_per_mwh_net, 1_350_000.0 / 2000.0)
        gas_only = forward_plant_co2_rate(h, None, {"gas1"})
        self.assertAlmostEqual(gas_only.rate_kg_per_mwh_net, 350.0)
        coal_only = forward_plant_co2_rate(h, None, {"coal1"})
        self.assertAlmostEqual(coal_only.rate_kg_per_mwh_net, 1000.0)
        self.assertLess(gas_only.rate_kg_per_mwh_net, blended.rate_kg_per_mwh_net)


class TestClassFallback(unittest.TestCase):
    def test_uncovered_plant_uses_class_median(self):
        h = _hist([("1", 2024, 1000.0, 400000.0)])
        # Mask excludes the only unit -> no history -> class fallback.
        r = forward_plant_co2_rate(h, None, {"other_unit"}, class_median=555.0)
        self.assertEqual(r.method, "class_fallback")
        self.assertEqual(r.rate_kg_per_mwh_net, 555.0)

    def test_class_median_rates_gen_weighted(self):
        annual = pd.DataFrame(
            {
                "group": ["CC_REGULAR", "CC_REGULAR", "COAL"],
                "fuel": ["gas_cc", "gas_cc", "coal"],
                "net_mwh": [1000.0, 9000.0, 5000.0],
                "co2_kg": [400_000.0, 3_150_000.0, 5_000_000.0],
            }
        )
        med = class_median_rates(annual)
        # The 9 GWh plant at 350 dominates -> class median near 350, not 375.
        self.assertLess(med[("CC_REGULAR", "gas_cc")], 375.0)
        self.assertAlmostEqual(med[("COAL", "coal")], 1000.0)


class TestEnvelopeGatedConditioning(unittest.TestCase):
    def _hist_with_ops(self):
        rows = [
            ("1", 2023, 1000.0, 400_000.0),  # 400 kg/MWh, low output
            ("1", 2024, 4000.0, 1_400_000.0),  # 350 kg/MWh, high output
        ]
        ops = {
            2023: OperatingPoint(1000.0, 50.0, _flat_cf()),
            2024: OperatingPoint(4000.0, 20.0, _flat_cf()),
        }
        return _hist(rows, ops=ops)

    def test_inside_envelope_keeps_base(self):
        h = self._hist_with_ops()
        # sim op inside the historical gen range -> base (gen-weighted) kept.
        sim = OperatingPoint(2500.0, 35.0, _flat_cf())
        r = forward_plant_co2_rate(h, sim, None, conditioning_enabled=True)
        self.assertEqual(r.method, "trailing_avg")
        self.assertAlmostEqual(r.rate_kg_per_mwh_net, 1_800_000.0 / 5000.0)

    def test_outside_envelope_adopts_nearest_year(self):
        h = self._hist_with_ops()
        # sim op far above the historical gen envelope -> NN = 2024 (high output).
        sim = OperatingPoint(50000.0, 20.0, _flat_cf())
        r = forward_plant_co2_rate(
            h, sim, None, conditioning_enabled=True, envelope_gate_l1=0.5
        )
        self.assertEqual(r.method, "nn_conditioned")
        self.assertAlmostEqual(r.rate_kg_per_mwh_net, 350.0)

    def test_conditioning_off_by_default_flag(self):
        h = self._hist_with_ops()
        sim = OperatingPoint(50000.0, 20.0, _flat_cf())
        r = forward_plant_co2_rate(h, sim, None, conditioning_enabled=False)
        self.assertEqual(r.method, "trailing_avg")


def _v2_parish() -> pd.DataFrame:
    """A Parish-style coal+gas facility (plant 3470) over two years, one ISO.

    Rows carry all three pollutant masses so the NOx/SO2 path (plan §5 R7) is
    exercised on the same fixture as CO2. Coal units emit NOx/SO2; the gas
    units carry NOx but ~0 SO2 (a legitimate gas value).
    """
    rows = []
    for year in (2023, 2024):
        # (iso, plant, unit, year, fuel, net_mwh, co2_kg, nox_kg, so2_kg)
        rows += [
            ("ERCOT", 3470, "WAP5", year, "Coal", 1000.0, 1_000_000.0, 800.0, 900.0),
            (
                "ERCOT",
                3470,
                "WAP1",
                year,
                "Pipeline Natural Gas",
                1000.0,
                400_000.0,
                200.0,
                0.0,
            ),
            (
                "ERCOT",
                100,
                "1",
                year,
                "Pipeline Natural Gas",
                1000.0,
                350_000.0,
                150.0,
                0.0,
            ),
        ]
    return pd.DataFrame(
        rows,
        columns=[
            "iso",
            "plant_id",
            "unit_id",
            "year",
            "primary_fuel",
            "net_mwh",
            "co2_kg",
            "nox_kg",
            "so2_kg",
        ],
    )


class TestMeasuredPlantRates(unittest.TestCase):
    def test_fuel_class_mapping(self):
        self.assertEqual(fuel_class("Coal"), "coal")
        self.assertEqual(fuel_class("Lignite Coal"), "coal")
        self.assertEqual(fuel_class("Pipeline Natural Gas"), "gas")
        self.assertEqual(fuel_class("gas_st"), "gas")
        self.assertEqual(fuel_class("coal"), "coal")

    def test_parish_split_coal_and_gas(self):
        v2 = _v2_parish()
        rates = measured_plant_rates(v2, "ERCOT", 2024, "backcast")
        # Coal units 1000 kg/MWh -> 1.0 t; gas units 400 -> 0.4 t.
        self.assertAlmostEqual(rates[(3470, "coal")], 1.0)
        self.assertAlmostEqual(rates[(3470, "gas")], 0.4)

    def test_backcast_uses_target_year_only(self):
        v2 = _v2_parish().copy()
        # Make 2023 coal cheaper; backcast 2024 must ignore it.
        v2.loc[(v2.year == 2023) & (v2.unit_id == "WAP5"), "co2_kg"] = 500_000.0
        bk = measured_plant_rates(v2, "ERCOT", 2024, "backcast")
        self.assertAlmostEqual(bk[(3470, "coal")], 1.0)  # 2024 only
        fc = measured_plant_rates(v2, "ERCOT", 2024, "forecast")
        # forecast pools both years: (1.0e6 + 0.5e6) / 2000 / 1000 = 0.75 t.
        self.assertAlmostEqual(fc[(3470, "coal")], 0.75)

    def test_other_iso_excluded(self):
        v2 = _v2_parish()
        self.assertEqual(measured_plant_rates(v2, "PJM", 2024, "backcast"), {})


class TestMeasuredNoxSo2Rates(unittest.TestCase):
    """NOx/SO2 ride the identical mode/composition-mask path as CO2 (plan §5 R7)."""

    def test_nox_rate_reproduces_campd_mass(self):
        # The core R7 acceptance: measured NOx rate x net MWh == CAMPD nox_kg.
        v2 = _v2_parish()
        rates = measured_plant_rates(v2, "ERCOT", 2024, "backcast", pollutant="nox")
        # Coal unit: 800 kg NOx / 1000 MWh = 0.8 kg/MWh -> 0.0008 t/MWh.
        self.assertAlmostEqual(rates[(3470, "coal")], 0.0008)
        # Round-trip: rate (t/MWh) x net MWh x 1000 kg/t == the measured mass.
        self.assertAlmostEqual(rates[(3470, "coal")] * 1000.0 * 1000.0, 800.0)
        # Gas units: 200 kg / 1000 MWh -> 0.0002 t/MWh.
        self.assertAlmostEqual(rates[(3470, "gas")], 0.0002)

    def test_so2_zero_for_gas_positive_for_coal(self):
        v2 = _v2_parish()
        rates = measured_plant_rates(v2, "ERCOT", 2024, "backcast", pollutant="so2")
        self.assertAlmostEqual(rates[(3470, "coal")], 0.0009)  # 900 kg / 1e6
        self.assertAlmostEqual(rates[(3470, "gas")], 0.0)  # legitimate gas zero

    def test_nox_mode_policy_matches_co2(self):
        v2 = _v2_parish().copy()
        v2.loc[(v2.year == 2023) & (v2.unit_id == "WAP5"), "nox_kg"] = 400.0
        bk = measured_plant_rates(v2, "ERCOT", 2024, "backcast", pollutant="nox")
        self.assertAlmostEqual(bk[(3470, "coal")], 0.0008)  # 2024 only
        fc = measured_plant_rates(v2, "ERCOT", 2024, "forecast", pollutant="nox")
        # forecast pools both years: (800 + 400) / 2000 MWh -> 0.0006 t/MWh.
        self.assertAlmostEqual(fc[(3470, "coal")], 0.0006)

    def test_entrant_nox_rate_equals_class_median(self):
        # A new entrant / uncovered plant gets the gen-weighted class median NOx.
        annual = pd.DataFrame(
            {
                "group": ["CC_REGULAR", "CC_REGULAR", "COAL"],
                "fuel": ["gas_cc", "gas_cc", "coal"],
                "net_mwh": [1000.0, 9000.0, 5000.0],
                "nox_kg": [500.0, 1800.0, 5000.0],
            }
        )
        med = class_median_rates(annual, pollutant="nox")
        # The 9 GWh gas plant at 0.2 kg/MWh dominates -> gen-weighted median
        # pulled below the 0.35 simple mean of {0.5, 0.2}.
        self.assertLess(med[("CC_REGULAR", "gas_cc")], 0.35)
        self.assertAlmostEqual(med[("COAL", "coal")], 1.0)  # 5000/5000


if __name__ == "__main__":
    unittest.main()
