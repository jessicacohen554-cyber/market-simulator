"""Tests for the reference curation script (scripts/data/curate_reference.py).

Drives the curator over a *tiny synthetic* raw fixture (not the real data) and
asserts each lookup table writes schema-valid Parquet with the expected key
normalization. CLEAN_DIR is redirected to a temp dir (as in test_clean_io.py) so
the test never touches the real data/clean tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_reference
from scripts.lib import clean_io
from scripts.lib.clean_io import read_clean_metadata, validate_clean

# A 2-row stand-in for master-plant-registry.csv (only the columns the curator
# renames/derives need to be present for the normalization assertions).
_REGISTRY_CSV = (
    "plantid,nameplate_capacity_mw,fuel_type,annual_heat_rate,"
    "annual_capacity_factor,chp_flag,has_campd_data,plant_group\n"
    "10154,141.0,NG,5.13,0.71,Yes,False,CT_CHP\n"
    "10167,7.6,PC,6.98,0.26,,True,OTHER\n"
)

# A 2-row stand-in for custom-bin-assignments.csv.
_BINS_CSV = (
    "Plant_Group,ERCOT_Zone,Bin_Number,Bin_Label,Plant_Code,Plant_Name,"
    "Nameplate_MW,Plant_Avg_HR_MMBtu_MWh,Pct_Must_Run,HR_Mult_Must_Run\n"
    "CC_CHP,Houston,1,H_CHP1,56152,Freeport,260.0,5.63,60.0,1.05\n"
    "CC,South,2,S_CC2,50043,Battleground,380.7,5.67,0.0,1.0\n"
)

# A 2-row stand-in for coal_region_crosswalk.csv (scripts/data/derive_coal_region_crosswalk.py).
_COAL_CROSSWALK_CSV = (
    "iso,plant_code,plant_name,state,coal_supply_class,region_id,region_name,"
    "confidence,note\n"
    "ERCOT,298,Limestone,TX,prb,PRB,PRB,high,PRB-by-rail\n"
    "PJM,3130,Seward (PA),PA,waste,,,none,culm/gob reclamation fuel\n"
)


class TestCurateReference(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        tmp = Path(self._tmp.name)

        # Synthetic raw/reference fixture.
        self.raw_dir = tmp / "raw" / "reference"
        self.raw_dir.mkdir(parents=True)
        (self.raw_dir / "master-plant-registry.csv").write_text(_REGISTRY_CSV)
        (self.raw_dir / "custom-bin-assignments.csv").write_text(_BINS_CSV)
        (self.raw_dir / "coal_region_crosswalk.csv").write_text(_COAL_CROSSWALK_CSV)

        # Redirect the clean tree so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = tmp / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid_tables(self):
        written = curate_reference.curate(raw_dir=self.raw_dir)

        # One file per lookup table, each under its own `market` partition.
        self.assertEqual(
            set(written), {"plant-registry", "bin-assignments", "coal-region-crosswalk"}
        )
        for name, path in written.items():
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "reference.parquet")
            self.assertIn(name, path.parts)
            # Round-trips against the embedded reference schema.
            self.assertEqual(validate_clean(path).datatype, "reference")
            # Per-table provenance points back at the raw source.
            self.assertTrue(read_clean_metadata(path)["source"].endswith(".csv"))

    def test_plant_registry_normalization(self):
        written = curate_reference.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(written["plant-registry"])

        # Standard key + stable, unique, self-describing `key`.
        self.assertIn("plant_id", df.columns)
        self.assertNotIn("plantid", df.columns)
        self.assertTrue(df["key"].is_unique)
        self.assertEqual(
            df.loc[df["plant_id"] == 10154, "key"].iloc[0], "plant-registry:10154"
        )

        # Unit suffixes added; original unsuffixed names gone.
        self.assertIn("annual_heat_rate_mmbtu_per_mwh", df.columns)
        self.assertIn("annual_capacity_factor_frac", df.columns)
        self.assertNotIn("annual_heat_rate", df.columns)
        self.assertNotIn("annual_capacity_factor", df.columns)

        # CHP flag coerced "Yes"/blank -> real boolean.
        self.assertTrue(pd.api.types.is_bool_dtype(df["chp_flag"]))
        self.assertTrue(df.loc[df["plant_id"] == 10154, "chp_flag"].iloc[0])
        self.assertFalse(df.loc[df["plant_id"] == 10167, "chp_flag"].iloc[0])

    def test_bin_assignments_normalization(self):
        written = curate_reference.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(written["bin-assignments"])

        # Plant code -> plant_id, ERCOT_Zone -> zone, iso stamped for context.
        self.assertIn("plant_id", df.columns)
        self.assertNotIn("Plant_Code", df.columns)
        self.assertEqual(set(df["zone"]), {"Houston", "South"})
        self.assertEqual(set(df["iso"]), {"ERCOT"})
        self.assertEqual(
            df.loc[df["plant_id"] == 56152, "key"].iloc[0], "bin-assignments:56152"
        )

        # Table-specific columns renamed with explicit unit suffixes.
        self.assertIn("plant_avg_heat_rate_mmbtu_per_mwh", df.columns)
        self.assertIn("must_run_pct", df.columns)
        self.assertIn("heat_rate_mult_must_run", df.columns)
        # No leftover TitleCase columns.
        self.assertFalse([c for c in df.columns if any(ch.isupper() for ch in c)])

    def test_coal_region_crosswalk_normalization(self):
        written = curate_reference.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(written["coal-region-crosswalk"])

        # plant_code -> plant_id; iso carried straight through (multi-ISO table).
        self.assertIn("plant_id", df.columns)
        self.assertNotIn("plant_code", df.columns)
        self.assertEqual(set(df["iso"]), {"ERCOT", "PJM"})
        self.assertEqual(
            df.loc[df["plant_id"] == 298, "key"].iloc[0],
            "coal-region-crosswalk:ERCOT:298",
        )

        # PRB-tagged plant resolves to the PRB region; waste-tagged plant has
        # no region match (culm/gob is not commodity-traded).
        self.assertEqual(df.loc[df["plant_id"] == 298, "region_id"].iloc[0], "PRB")
        self.assertEqual(df.loc[df["plant_id"] == 3130, "confidence"].iloc[0], "none")


if __name__ == "__main__":
    unittest.main()
