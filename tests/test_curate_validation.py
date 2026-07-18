"""Tests for scripts/data/curate_validation.py.

A tiny synthetic ``_validation-source`` fixture is curated into a temp clean
tree and the result is asserted to be schema-valid and correctly reconciled into
the tidy long form (every heterogeneous benchmark -> one metric row with the
right value, unit, dimensions and ``source`` publisher). This is a unit check on
the reconciliation logic, NOT a full-data run.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_validation
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# One ISO-year carrying every benchmark, plus a price-only ISO-year.
_CALIB_REFERENCE = {
    "egrid_benchmark": {
        "ZZ": {
            "benchmark_year": 2023,
            # 1 Mt -> 1e9 kg; wind emits ~0.
            "co2_mt": {"coal": 2.0, "wind": 0.0},
        }
    },
    "isos": {
        "ZZ": {
            "2023": {
                "henry_hub_actual": 2.54,
                "demand": {
                    "total_mwh": 1000.0,
                    "peak_mw": 90.0,
                    "min_mw": 30.0,
                    "avg_mw": 50.0,
                    "total_twh": 0.001,  # TWh echo — intentionally dropped
                },
                # 0.5 TWh -> 5e5 MWh.
                "generation_twh": {"wind": 0.5, "coal": 1.5},
            }
        }
    },
}

_ACTUAL_LMP = {
    "ZZ": {
        "2023": {
            "src": "ZZ test hub price",
            "da": 40.0,
            "da_mon": [
                10.0,
                20.0,
                None,
                40.0,
                50.0,
                60.0,
                70.0,
                80.0,
                90.0,
                100.0,
                110.0,
                120.0,
            ],
        }
    },
    # Price-only ISO-year: no capacity CSV, no calibration block.
    "QQ": {
        "2024": {"src": "QQ test hub price", "da": 33.0, "da_mon": [33.0] * 12},
    },
}

# Per-zone/month renewable capacity CSV (the EIA-860 benchmark).
_CAPACITY_CSV = (
    "iso,year,fuel,zone,month,capacity_mw\n"
    "ZZ,2023,wind,North,1,100.0\n"
    "ZZ,2023,wind,North,2,110.0\n"
    "ZZ,2023,solar,South,1,200.0\n"
)


class TestCurateValidation(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_dir = root / "raw"
        self.raw_dir.mkdir()
        (self.raw_dir / "ZZ_2023_renewable_capacity.csv").write_text(_CAPACITY_CSV)
        (self.raw_dir / "calibration_reference.json").write_text(
            json.dumps(_CALIB_REFERENCE)
        )
        (self.raw_dir / "actual_lmp.json").write_text(json.dumps(_ACTUAL_LMP))

        # Redirect the clean tree to the temp dir so nothing touches the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate(self) -> dict[tuple[str, int], pd.DataFrame]:
        paths = curate_validation.curate(raw_dir=self.raw_dir)
        out: dict[tuple[str, int], pd.DataFrame] = {}
        for p in paths:
            # validate_clean re-checks every file against its embedded schema.
            self.assertEqual(validate_clean(p).datatype, "validation")
            df = pd.read_parquet(p)
            iso = df["iso"].iloc[0]
            year = int(df["year"].iloc[0])
            out[(iso, year)] = df
        return out

    def test_schema_valid_and_partitioned(self):
        frames = self._curate()
        # ZZ-2023 (full) and QQ-2024 (price-only) each get their own partition.
        self.assertIn(("ZZ", 2023), frames)
        self.assertIn(("QQ", 2024), frames)

    def test_no_duplicate_keys(self):
        key = ["iso", "zone", "year", "month", "fuel", "metric"]
        for df in self._curate().values():
            self.assertFalse(df.duplicated(key).any())

    def test_reconciliation_values(self):
        df = self._curate()[("ZZ", 2023)]

        def one(metric, **filt):
            sub = df[df["metric"] == metric]
            for k, v in filt.items():
                sub = sub[sub[k] == v]
            self.assertEqual(len(sub), 1, f"{metric} {filt} -> {len(sub)} rows")
            return sub.iloc[0]

        # capacity_mw: straight pass-through, per zone/month/fuel.
        cap = one("capacity_mw", zone="North", month=2, fuel="wind")
        self.assertEqual(cap["value"], 110.0)
        self.assertEqual(cap["unit"], "mw")
        self.assertEqual(cap["source"], "EIA-860")

        # generation_mwh: 0.5 TWh -> 5e5 MWh, annual SYSTEM total.
        gen = one("generation_mwh", fuel="wind")
        self.assertEqual(gen["value"], 0.5 * 1e6)
        self.assertEqual(gen["unit"], "mwh")
        self.assertEqual((gen["zone"], gen["month"]), ("SYSTEM", 0))

        # co2_kg: 2.0 Mt -> 2e9 kg (eGRID 2023 benchmark year).
        co2 = one("co2_kg", fuel="coal")
        self.assertEqual(co2["value"], 2.0 * 1e9)
        self.assertEqual(co2["unit"], "kg")
        self.assertEqual(co2["source"], "EPA eGRID 2023")

        # demand: total_mwh -> demand_mwh, fuel=ALL; total_twh echo dropped.
        dem = one("demand_mwh")
        self.assertEqual(dem["value"], 1000.0)
        self.assertEqual((dem["fuel"], dem["zone"], dem["month"]), ("ALL", "SYSTEM", 0))
        self.assertEqual(one("peak_demand_mw")["value"], 90.0)

        # henry hub gas price (fuel=gas).
        hh = one("henry_hub_usd_per_mmbtu")
        self.assertEqual(
            (hh["value"], hh["fuel"], hh["unit"]), (2.54, "gas", "usd_per_mmbtu")
        )

        # avg_price_usd_per_mwh: annual at month=0 plus the monthly series; the
        # null March (index 3) is dropped, so 1 annual + 11 monthly = 12 rows.
        price = df[df["metric"] == "avg_price_usd_per_mwh"]
        self.assertEqual(len(price), 12)
        self.assertEqual(one("avg_price_usd_per_mwh", month=0)["value"], 40.0)
        self.assertEqual(one("avg_price_usd_per_mwh", month=4)["value"], 40.0)
        self.assertTrue((price["source"] == "ZZ test hub price").all())
        self.assertEqual(
            sorted(price["month"]), [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        )

    def test_price_only_iso_year(self):
        # QQ-2024 has only the LMP benchmark -> 1 annual + 12 monthly price rows.
        df = self._curate()[("QQ", 2024)]
        self.assertEqual(set(df["metric"]), {"avg_price_usd_per_mwh"})
        self.assertEqual(len(df), 13)

    def test_idempotent(self):
        first = self._curate()
        second = self._curate()
        self.assertEqual(set(first), set(second))
        for k in first:
            pd.testing.assert_frame_equal(
                first[k].sort_values(first[k].columns.tolist()).reset_index(drop=True),
                second[k]
                .sort_values(second[k].columns.tolist())
                .reset_index(drop=True),
            )


if __name__ == "__main__":
    unittest.main()
