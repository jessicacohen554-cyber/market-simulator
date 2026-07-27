"""Tests for scripts/data/curate_emissions_unit_annual.py.

A tiny synthetic unit-level CAMPD fixture (1 unit, 48 h, one off->on start) is
rolled up end to end and checked for: schema validity through the frozen
clean_io contract, correct annual sums, op_hours, the single start, CO2
provenance, facility-grain ("ALL") handling, and the rule-22 quarantine skip.
CLEAN_DIR is redirected to a temp dir so nothing touches the real clean tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts.lib import clean_io
from scripts.data.curate_emissions_unit_annual import (
    QUARANTINED_YEARS,
    SHORT_TON_TO_KG,
    curate_year,
)


def _raw_unit_48h() -> pd.DataFrame:
    """One unit, 48 contiguous hours: off for the first 12 h, then on.

    Gap-free reported clock (explicit zeros early) so the roll-up sees exactly
    one off->on transition. CO2 reported for every on-hour -> co2_source measured.
    """
    n = 48
    ts = pd.date_range("2018-01-01 00:00", periods=n, freq="h")
    gross = np.where(np.arange(n) < 12, 0.0, 100.0)
    heat = gross * 9.0  # 9 MMBtu/MWh
    co2_tons = heat * 0.05  # short tons, proportional to heat (measured)
    return pd.DataFrame(
        {
            "stateCode": ["TX"] * n,
            "facilityName": ["Testplant"] * n,
            "facilityId": ["999"] * n,
            "unitId": ["1"] * n,
            "date": ts.normalize(),
            "hour": ts.hour,
            "opTime": np.where(gross > 0, 1.0, 0.0),
            "grossLoad": gross,
            "steamLoad": [None] * n,
            "so2Mass": gross * 0.01,  # pounds
            "co2Mass": co2_tons,
            "noxMass": gross * 0.02,  # pounds
            "heatInput": heat,
            "primaryFuelInfo": ["Pipeline Natural Gas"] * n,
            "unitType": ["Combustion turbine"] * n,
            "programCodeInfo": ["ARP"] * n,
        }
    )


class CleanDirRedirectMixin(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.unit_dir = self.root / "raw" / "campd-unit-level"
        self.unit_dir.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()


class TestCurateUnitAnnual(CleanDirRedirectMixin):
    def test_rollup_schema_and_values(self):
        _raw_unit_48h().to_parquet(self.unit_dir / "TX_2018.parquet")
        path = curate_year(2018, unit_dir=self.unit_dir)
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "emissions-unit-annual_2018.parquet")

        schema = clean_io.validate_clean(path)
        self.assertEqual(schema.datatype, "emissions-unit-annual")

        df = pd.read_parquet(path)
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(int(row["plant_id"]), 999)
        self.assertEqual(str(row["unit_id"]), "1")
        # 36 on-hours at 100 MW.
        self.assertAlmostEqual(row["gross_mwh"], 3600.0, places=3)
        self.assertEqual(int(row["op_hours"]), 36)
        self.assertEqual(int(row["starts"]), 1)  # one off->on transition
        self.assertEqual(str(row["co2_source"]), "measured")
        self.assertEqual(str(row["mw_source"]), "measured")
        # CO2: 36 h * 900 MMBtu/h * 0.05 tons/MMBtu -> kg.
        self.assertAlmostEqual(
            row["co2_kg"], 36 * 900.0 * 0.05 * SHORT_TON_TO_KG, places=1
        )

    def test_facility_grain_unit_id_all(self):
        raw = _raw_unit_48h().drop(columns=["unitId"])
        raw.to_parquet(self.unit_dir / "TX_2018.parquet")
        path = curate_year(2018, unit_dir=self.unit_dir)
        df = pd.read_parquet(path)
        self.assertEqual(list(df["unit_id"]), ["ALL"])

    def test_quarantined_year_refused(self):
        for yr in sorted(QUARANTINED_YEARS):
            with self.assertRaises(ValueError):
                curate_year(yr, unit_dir=self.unit_dir)

    def test_idempotent(self):
        _raw_unit_48h().to_parquet(self.unit_dir / "TX_2018.parquet")
        a = pd.read_parquet(curate_year(2018, unit_dir=self.unit_dir))
        b = pd.read_parquet(curate_year(2018, unit_dir=self.unit_dir))
        pd.testing.assert_frame_equal(a, b)


if __name__ == "__main__":
    unittest.main()
