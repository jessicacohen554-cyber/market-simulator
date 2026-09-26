"""R-CAISO-3 lever C: refused gross-net CC rows fall back to EIA-923 fuel / net.

Trivial cases first. Record: ``docs/handoffs/r-caiso-3/``.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.fleet import campd_bins

REPO = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "derive_cc", REPO / "scripts/data/derive_campd_cc_heat_rates.py"
)
derive = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(derive)


class TestIdentityRates(unittest.TestCase):
    def _write(self, tmp: Path) -> Path:
        p = tmp / "g.csv"
        pd.DataFrame(
            [
                (2023, 1, "CA", "CT", "NG", 700.0, 700.0, 70.0),
                (2023, 1, "CA", "CA", "NG", 0.0, 0.0, 30.0),
                (2023, 1, "CA", "GT", "NG", 999.0, 999.0, 1.0),  # not a CC mover
                (2024, 1, "CA", "CT", "NG", 800.0, 800.0, 100.0),
            ],
            columns=[
                "year",
                "plant_id",
                "plant_state",
                "prime_mover",
                "fuel_type",
                "total_fuel_mmbtu",
                "elec_fuel_mmbtu",
                "net_generation_mwh",
            ],
        ).to_csv(p, index=False)
        return p

    def test_year_and_pooled(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            r = derive.eia923_identity_rates({1}, [2023, 2024], self._write(Path(d)))
        self.assertAlmostEqual(r[2023][1], 7.0)
        self.assertAlmostEqual(r[2024][1], 8.0)
        self.assertAlmostEqual(r[0][1], 1500.0 / 200.0)

    def test_missing_intake_is_empty(self):
        self.assertEqual(
            derive.eia923_identity_rates({1}, [2023], Path("/nope.csv")), {}
        )


class TestApply(unittest.TestCase):
    def test_only_refused_rows_swap(self):
        t = pd.DataFrame(
            {
                "plant_code": [1, 2, 3],
                "year": [2023, 2023, 2023],
                "heat_rate": [8.5, 7.2, 9.0],
                "model_heat_rate_egrid": [7.7, 7.3, 9.1],
                "model_over_measured": [0.9, 1.0, 1.0],
                "flag": ["gross_below_net", "ok", "steam_not_metered"],
            }
        )
        rates = {2023: {1: 7.04, 2: 7.5, 3: 7.0}}
        out = derive.apply_eia923_identity(t, rates)
        self.assertEqual(
            list(out["flag"]), ["eia923_identity", "ok", "steam_not_metered"]
        )
        self.assertEqual(list(out["heat_rate"]), [7.04, 7.2, 9.0])
        self.assertTrue(np.isfinite(out["heat_rate_eia923_identity"]).all())

    def test_out_of_band_identity_stays_refused(self):
        t = pd.DataFrame(
            {
                "plant_code": [1],
                "year": [2023],
                "heat_rate": [8.5],
                "model_heat_rate_egrid": [7.7],
                "model_over_measured": [0.9],
                "flag": ["gross_below_net"],
            }
        )
        out = derive.apply_eia923_identity(t, {2023: {1: 30.0}})
        self.assertEqual(out["flag"].iloc[0], "gross_below_net")


class TestModelAppliesIdentityFlag(unittest.TestCase):
    def test_rate_map_reads_identity_rows(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.csv"
            pd.DataFrame(
                {
                    "plant_code": [1, 1, 2, 3],
                    "year": [0, 2023, 0, 0],
                    "heat_rate": [7.1, 7.0, 7.5, 9.9],
                    "flag": [
                        "eia923_identity",
                        "eia923_identity",
                        "ok",
                        "gross_below_net",
                    ],
                }
            ).to_csv(p, index=False)
            m = campd_bins._measured_rate_map(p, 2023)
        self.assertEqual(m, {1: 7.0, 2: 7.5})


if __name__ == "__main__":
    unittest.main()
