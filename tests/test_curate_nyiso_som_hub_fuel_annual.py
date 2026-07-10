"""Tests for the nyiso-som-hub-fuel-annual intake on a tiny synthetic fixture.

Writes a two-row transcription fixture into a tmp raw tree, runs ``curate``,
and asserts the written Parquet partition is schema-valid and round-trips the
values. CLEAN_DIR is redirected to a tmp dir so the real tree is never
touched.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_nyiso_som_hub_fuel_annual as curate_som
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_CSV = """year,fuel,hub,price_usd_per_mmbtu,source_doc,source_page
2024,gas,IROQUOIS_Z2,2.90,NYISO-2024-SOM-Full-Report_5-14-2025-final.pdf,190
2024,oil,ULSK,21.03,NYISO-2024-SOM-Full-Report_5-14-2025-final.pdf,190
"""


class TestCurateNyisoSomHubFuelAnnual(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / "gas-prices").mkdir(parents=True)
        (self.raw_root / "gas-prices" / "nyiso_som_hub_fuel_annual.csv").write_text(
            _CSV
        )
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_round_trips(self) -> None:
        """The spanning partition writes through the seam and re-validates."""
        written = curate_som.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "nyiso-som-hub-fuel-annual")
        df = pd.read_parquet(written[0])
        z2 = df[df["hub"] == "IROQUOIS_Z2"].iloc[0]
        self.assertEqual(z2["price_usd_per_mmbtu"], 2.90)
        self.assertEqual(z2["year"], 2024)
        self.assertEqual(z2["iso"], "NYISO")


if __name__ == "__main__":
    unittest.main()
