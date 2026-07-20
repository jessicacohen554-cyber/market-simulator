"""Tests for the emissions curation script (scripts/data/curate_emissions.py).

A tiny synthetic CAMPD raw fixture (NOT a full-data run) is curated end to end
and checked for: schema validity through the frozen clean_io contract, correct
CAMPD->kg mass conversion, the Local-Standard-Time->UTC offset, facility rows
getting unit_id="ALL", and the unit-first reconciliation that keeps a plant's
unit rows over its facility "ALL" summary. CLEAN_DIR is redirected to a temp
dir (as in tests/test_clean_io.py) so nothing touches the real clean tree.
"""

import unittest
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.data.curate_emissions import (
    SHORT_TON_TO_KG,
    LB_TO_KG,
    clean_campd_frame,
    curate_year,
)
from tests.helpers.base import CleanDirTestCase


def _raw_unit() -> pd.DataFrame:
    """A 2-row unit-level CAMPD extract for a Connecticut (Eastern) plant."""
    return pd.DataFrame(
        {
            "stateCode": ["CT", "CT"],
            "facilityName": ["Devon", "Devon"],
            "facilityId": ["544", "544"],
            "unitId": ["11", "12"],
            "date": pd.to_datetime(["2023-06-01", "2023-06-01"]),
            "hour": [0, 0],
            "opTime": [1.0, 1.0],
            "grossLoad": [100.0, 50.0],
            "steamLoad": [None, None],
            "so2Mass": [10.0, 4.0],  # pounds
            "co2Mass": [2.0, 1.0],  # short tons
            "noxMass": [6.0, 2.0],  # pounds
            "heatInput": [900.0, 450.0],
            "primaryFuelInfo": ["Pipeline Natural Gas", "Pipeline Natural Gas"],
            "unitType": ["Combustion turbine", "Combustion turbine"],
            "programCodeInfo": ["ARP", "ARP"],
        }
    )


def _raw_facility() -> pd.DataFrame:
    """A 2-row facility-level extract: plant 544 (overlaps unit) + 1588 (only here)."""
    return pd.DataFrame(
        {
            "stateCode": ["CT", "MA"],
            "facilityName": ["Devon", "Mystic"],
            "facilityId": ["544", "1588"],
            "date": pd.to_datetime(["2023-06-01", "2023-06-01"]),
            "hour": [0, 0],
            "grossLoad": [150.0, 80.0],
            "steamLoad": [None, None],
            "so2Mass": [14.0, 1.0],
            "co2Mass": [3.0, 9.842],
            "noxMass": [8.0, 26.486],
            "heatInput": [1350.0, 165.49],
            "persefoniOrganizationName": ["Eversource", "Mystic"],
        }
    )


def _write_fixture(root: Path) -> tuple[Path, Path]:
    """Write the synthetic raw extracts into a campd-{unit,facility}-level tree."""
    unit_dir = root / "campd-unit-level"
    fac_dir = root / "campd-facility-level"
    unit_dir.mkdir(parents=True)
    fac_dir.mkdir(parents=True)
    _raw_unit().to_parquet(unit_dir / "CT_2023.parquet")
    _raw_facility().to_parquet(fac_dir / "CT_2023.parquet")
    return unit_dir, fac_dir


class CleanDirRedirectMixin(CleanDirTestCase):
    """Redirect CLEAN_DIR to a temp dir so writes never touch the repo.

    Thin adapter over the shared :class:`tests.helpers.base.CleanDirTestCase`
    that keeps this module's ``self.root`` (== the tempdir) contract for its
    subclasses.
    """

    def setUp(self):
        super().setUp()  # redirects paths.CLEAN_DIR to self.tmp_path / "clean"
        self.root = self.tmp_path


class TestCleanFrame(unittest.TestCase):
    def test_unit_level_conversions_and_utc(self):
        df = clean_campd_frame(_raw_unit(), facility_level=False)
        self.assertEqual(len(df), 2)
        r = df.set_index("unit_id").loc["11"]
        # short tons -> kg, pounds -> kg.
        self.assertAlmostEqual(r["co2_kg"], 2.0 * SHORT_TON_TO_KG, places=6)
        self.assertAlmostEqual(r["so2_kg"], 10.0 * LB_TO_KG, places=6)
        self.assertAlmostEqual(r["nox_kg"], 6.0 * LB_TO_KG, places=6)
        # heat input and gross load pass through unconverted.
        self.assertAlmostEqual(r["heat_input_mmbtu"], 900.0)
        self.assertAlmostEqual(r["gross_mw"], 100.0)
        # CT is Eastern: 00:00 LST -> 05:00 UTC; local wall-clock carried naive.
        self.assertEqual(
            r["interval_start_utc"], pd.Timestamp("2023-06-01 05:00", tz="UTC")
        )
        self.assertEqual(r["interval_start_local"], pd.Timestamp("2023-06-01 00:00"))
        self.assertTrue(df["iso"].isna().all())

    def test_facility_level_unit_id_is_all(self):
        df = clean_campd_frame(_raw_facility(), facility_level=True)
        self.assertTrue((df["unit_id"] == "ALL").all())
        # Central-time MA plant? No — MA is Eastern; row 1588 -> 05:00 UTC too.
        mystic = df.set_index("plant_id").loc[1588]
        self.assertAlmostEqual(mystic["co2_kg"], 9.842 * SHORT_TON_TO_KG, places=6)

    def test_central_state_offset(self):
        raw = _raw_unit().assign(stateCode=["TX", "TX"])
        df = clean_campd_frame(raw, facility_level=False)
        # TX is Central: 00:00 LST -> 06:00 UTC.
        self.assertTrue(
            (
                df["interval_start_utc"] == pd.Timestamp("2023-06-01 06:00", tz="UTC")
            ).all()
        )

    def test_unknown_state_raises(self):
        raw = _raw_unit().assign(stateCode=["ZZ", "ZZ"])
        with self.assertRaises(ValueError):
            clean_campd_frame(raw, facility_level=False)


class TestCurateYear(CleanDirRedirectMixin):
    def test_curate_is_schema_valid_and_reconciles(self):
        unit_dir, fac_dir = _write_fixture(self.root / "raw")
        path = curate_year(2023, unit_dir=unit_dir, fac_dir=fac_dir)
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "emissions_2023.parquet")

        # Round-trips against the embedded schema through the frozen contract.
        schema = clean_io.validate_clean(path)
        self.assertEqual(schema.datatype, "emissions")

        df = pd.read_parquet(path)
        # Plant 544 is covered at unit grain -> its two units kept, NO "ALL" row.
        p544 = df[df["plant_id"] == 544]
        self.assertEqual(sorted(p544["unit_id"]), ["11", "12"])
        # Plant 1588 has only facility coverage -> a single "ALL" row.
        p1588 = df[df["plant_id"] == 1588]
        self.assertEqual(list(p1588["unit_id"]), ["ALL"])
        # No facility "ALL" row leaked in for the unit-covered plant.
        self.assertFalse(((df["plant_id"] == 544) & (df["unit_id"] == "ALL")).any())
        # Keys are unique.
        self.assertFalse(
            df.duplicated(subset=["plant_id", "unit_id", "interval_start_utc"]).any()
        )

    def test_idempotent_rerun(self):
        unit_dir, fac_dir = _write_fixture(self.root / "raw")
        p1 = curate_year(2023, unit_dir=unit_dir, fac_dir=fac_dir)
        first = pd.read_parquet(p1)
        p2 = curate_year(2023, unit_dir=unit_dir, fac_dir=fac_dir)
        second = pd.read_parquet(p2)
        self.assertEqual(p1, p2)
        pd.testing.assert_frame_equal(first, second)


if __name__ == "__main__":
    unittest.main()
