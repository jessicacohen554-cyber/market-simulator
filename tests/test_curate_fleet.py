"""Tests for the fleet curation script (scripts/data/curate_fleet.py).

A tiny synthetic EIA-860 raw fixture (the spaced/parenthesized headers) is run
through the curator and the result is asserted to be schema-valid and correctly
header-normalized — NOT a full-data run. ``clean_io.paths.CLEAN_DIR`` is
redirected to a temp dir (as in ``tests/test_clean_io.py``) so the test never
writes the real ``data/clean`` tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_fleet
from scripts.lib import clean_io


def _synthetic_generators() -> pd.DataFrame:
    """A tiny EIA-860 generator_operable frame with the raw spaced headers.

    Mixes a gas CC, a coal steam, a solar PV, a battery and a trailing all-blank
    summary row (which curation must drop), plus a string-typed Summer/Winter
    column exactly as the raw parquet carries them.
    """
    return pd.DataFrame(
        {
            "Plant Code": [10, 10, 20, 30, None],
            "Generator ID": ["GT1", "ST1", "PV1", "BA1", None],
            "Plant Name": ["Alpha", "Alpha", "Sunny", "Powerwall", None],
            "Technology": [
                "Natural Gas Fired Combined Cycle",
                "Conventional Steam Coal",
                "Solar Photovoltaic",
                "Batteries",
                None,
            ],
            "Prime Mover": ["CA", "ST", "PV", "BA", None],
            "Nameplate Capacity (MW)": [200.0, 150.0, 50.0, 25.0, None],
            "Summer Capacity (MW)": ["190", "145", "48", "25", None],
            "Winter Capacity (MW)": ["205", "150", "47", "25", None],
            "Operating Year": [2015.0, 1980.0, 2021.0, 2023.0, None],
            "Energy Source 1": ["NG", "SUB", "SUN", "MWH", None],
            "Associated with Combined Heat and Power System": [
                "N",
                "N",
                "N",
                "N",
                None,
            ],
        }
    )


def _synthetic_storage() -> pd.DataFrame:
    """A tiny energy_storage_operable frame carrying the MWh energy capacity."""
    return pd.DataFrame(
        {
            "Plant Code": [30.0],
            "Generator ID": ["BA1"],
            "Nameplate Energy Capacity (MWh)": [100.0],
        }
    )


class TestBuildFleetFrame(unittest.TestCase):
    def test_header_normalization_and_schema(self):
        df = curate_fleet.build_fleet_frame(
            _synthetic_generators(), _synthetic_storage()
        )

        # Spaced/parenthesized EIA-860 headers reconciled to snake_case + units.
        self.assertEqual(list(df.columns), curate_fleet.FLEET_COLUMNS)
        self.assertIn("plant_id", df.columns)
        self.assertIn("nameplate_capacity_mw", df.columns)
        self.assertIn("energy_capacity_mwh", df.columns)
        self.assertNotIn("Plant Code", df.columns)
        self.assertNotIn("Nameplate Capacity (MW)", df.columns)

        # Trailing blank row dropped; one row per (plant_id, unit_id).
        self.assertEqual(len(df), 4)
        self.assertFalse(df.duplicated(["plant_id", "unit_id"]).any())

        # The frame validates against the canonical fleet schema.
        clean_io.validate_df(df, "fleet")

    def test_fuel_mapped_to_canonical_vocabulary(self):
        df = curate_fleet.build_fleet_frame(
            _synthetic_generators(), _synthetic_storage()
        )
        fuel = dict(zip(zip(df["plant_id"], df["unit_id"]), df["fuel"]))
        self.assertEqual(fuel[(10, "GT1")], "gas")
        self.assertEqual(fuel[(10, "ST1")], "coal")
        self.assertEqual(fuel[(20, "PV1")], "solar")
        self.assertEqual(fuel[(30, "BA1")], "storage")
        for value in df["fuel"]:
            self.assertIn(value, curate_fleet.EIA930_FUELS)

    def test_string_capacities_coerced_and_storage_joined(self):
        df = curate_fleet.build_fleet_frame(
            _synthetic_generators(), _synthetic_storage()
        )
        row = df[df["unit_id"] == "GT1"].iloc[0]
        self.assertAlmostEqual(float(row["summer_capacity_mw"]), 190.0)
        self.assertAlmostEqual(float(row["winter_capacity_mw"]), 205.0)
        # Storage energy capacity joined onto the battery unit only.
        battery = df[df["unit_id"] == "BA1"].iloc[0]
        self.assertAlmostEqual(float(battery["energy_capacity_mwh"]), 100.0)
        self.assertTrue(
            pd.isna(df[df["unit_id"] == "GT1"].iloc[0]["energy_capacity_mwh"])
        )

    def test_iso_enrichment_from_map(self):
        df = curate_fleet.build_fleet_frame(
            _synthetic_generators(), _synthetic_storage(), iso_map={10: "ERCOT"}
        )
        self.assertEqual(df[df["plant_id"] == 10].iloc[0]["iso"], "ERCOT")
        self.assertTrue(pd.isna(df[df["plant_id"] == 20].iloc[0]["iso"]))


class TestCurateEndToEnd(unittest.TestCase):
    """Run curate() over a synthetic raw tree with CLEAN_DIR redirected."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"

        # Two synthetic vintages: a top-level snapshot and a vintage_2024 subdir.
        self.raw = Path(self._tmp.name) / "eia-860"
        for sub in (self.raw, self.raw / "vintage_2024"):
            sub.mkdir(parents=True, exist_ok=True)
            _synthetic_generators().to_parquet(sub / curate_fleet.GENERATOR_OPERABLE)
            _synthetic_storage().to_parquet(sub / curate_fleet.ENERGY_STORAGE_OPERABLE)

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_partitioned_and_validates(self):
        # No eGRID dir / registry in the fixture -> iso stays null (nullable).
        written = curate_fleet.curate(
            eia860_root=self.raw,
            egrid_dir=Path(self._tmp.name) / "missing-egrid",
            registry_csv=Path(self._tmp.name) / "missing-registry.csv",
        )

        years = {p.name for p in written}
        self.assertEqual(
            years,
            {
                f"fleet_{curate_fleet.TOP_LEVEL_VINTAGE_YEAR}.parquet",
                "fleet_2024.parquet",
            },
        )
        # Every written file round-trips against its embedded schema.
        for path in written:
            self.assertTrue(path.is_file())
            schema = clean_io.validate_clean(path)
            self.assertEqual(schema.datatype, "fleet")


if __name__ == "__main__":
    unittest.main()
