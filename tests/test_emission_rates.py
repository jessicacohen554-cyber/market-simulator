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


if __name__ == "__main__":
    unittest.main()
