"""Tests for the LOYO CO2-rate validation harness (scripts/loyo_co2_rates.py).

Synthetic per-plant-year frames exercise the estimator predictions, the class
regression slope, and the gen-weighted wMAPE / fleet-bias scoring — no data
files or keeper bundles are read.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.data.emission_rates import CF_BANDS
from scripts.loyo_co2_rates import _class_slopes, _wmape_bias, predict


def _flat():
    return np.full(CF_BANDS, 1.0 / CF_BANDS)


def _df():
    rows = []
    for plant, base, group in ((1, 400.0, "CC_REGULAR"), (2, 1000.0, "COAL")):
        for i, year in enumerate((2023, 2024, 2025)):
            rate = base + (i - 1) * 10.0  # 390/400/410-style spread
            rows.append(
                {
                    "plant_id": plant,
                    "year": year,
                    "net_mwh": 1000.0,
                    "co2_kg": rate * 1000.0,
                    "net_rate": rate,
                    "starts": 20.0,
                    "group": group,
                    "campd_cf": _flat(),
                    "model_cf": _flat(),
                    "model_gwh": np.nan,
                    "cf_mean": 0.5 + (i - 1) * 0.05,
                }
            )
    return pd.DataFrame(rows)


class TestEstimators(unittest.TestCase):
    def test_a_gw_leaves_target_out(self):
        df = _df()
        tgt = df[(df["plant_id"] == 1) & (df["year"] == 2024)].iloc[0]
        # LOYO 2024: history 2023(390)+2025(410), gen-weighted = 400.
        p = predict(df, 1, 2024, tgt, "a_gw", {})
        self.assertAlmostEqual(p, 400.0)

    def test_a_sm_and_a_rw_differ_from_gw_when_gen_varies(self):
        df = _df()
        # equal gen here so a_sm == a_gw; recency weights the later year more.
        tgt = df[(df["plant_id"] == 1) & (df["year"] == 2024)].iloc[0]
        self.assertAlmostEqual(predict(df, 1, 2024, tgt, "a_sm", {}), 400.0)
        rw = predict(df, 1, 2024, tgt, "a_rw", {})
        # history 2023(390 w=1) + 2025(410 w=3) -> (390+1230)/4 = 405.
        self.assertAlmostEqual(rw, 405.0)

    def test_frozen_reads_artifact_map(self):
        df = _df()
        tgt = df[(df["plant_id"] == 1) & (df["year"] == 2024)].iloc[0]
        self.assertEqual(predict(df, 1, 2024, tgt, "frozen", {1: 377.0}), 377.0)
        self.assertTrue(np.isnan(predict(df, 1, 2024, tgt, "frozen", {})))

    def test_class_slope_is_finite(self):
        slopes = _class_slopes(_df())
        self.assertIn("CC_REGULAR", slopes)
        self.assertTrue(np.isfinite(slopes["CC_REGULAR"]))


class TestScoring(unittest.TestCase):
    def test_wmape_and_bias(self):
        preds = np.array([110.0, 90.0])
        actual = np.array([100.0, 100.0])
        gen = np.array([1.0, 1.0])
        wmape, bias = _wmape_bias(preds, actual, gen)
        # |10|/100 and |10|/100 -> 10% wMAPE; +10 and -10 net to 0 bias.
        self.assertAlmostEqual(wmape, 10.0)
        self.assertAlmostEqual(bias, 0.0)

    def test_ignores_invalid_rows(self):
        preds = np.array([np.nan, 100.0])
        actual = np.array([100.0, 100.0])
        gen = np.array([1.0, 1.0])
        wmape, bias = _wmape_bias(preds, actual, gen)
        self.assertAlmostEqual(wmape, 0.0)


if __name__ == "__main__":
    unittest.main()
