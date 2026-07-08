"""Tests for the nyiso-renewable-curtailment intake on a tiny synthetic fixture.

Writes minimal raw annual/monthly curtailment fixtures into a tmp raw tree,
runs ``curate``, and asserts both written Parquet partitions are schema-valid
and round-trip the fixture values. CLEAN_DIR is redirected to a tmp dir so it
never touches the real tree. Trivial case first (one year, one zone), then
the schema round-trip.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_nyiso_renewable_curtailment as curate_nrc
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_ANNUAL_CSV = """iso,resource_type,geographic_scope,year,curtailed_energy_gwh,curtailed_pct,source_doc,source_page,notes
NYISO,wind,NYCA,2023,161.9,3.4,fixture-deck.pdf,12,
NYISO,wind,WEST,2023,0.36,,fixture-deck.pdf,15,
NYISO,ftm_solar,NYCA,2023,0.42,,fixture-deck.pdf,31,percent not printed by source
"""

_MONTHLY_CSV = """iso,resource_type,geographic_scope,year,month,curtailed_energy_gwh,curtailed_pct,source_doc,source_page
NYISO,wind,NYCA,2023,1,,5.8,fixture-deck.pdf,13
NYISO,wind,NYCA,2023,2,,9.5,fixture-deck.pdf,13
NYISO,wind,WEST,2023,1,0.02,,fixture-deck.pdf,15
NYISO,wind,WEST,2023,2,0.06,,fixture-deck.pdf,15
"""


def _write_fixture(raw_root: Path) -> None:
    raw_dir = raw_root / "nyiso-renewable-curtailment"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "nyiso_curtailment_annual.csv").write_text(_ANNUAL_CSV)
    (raw_dir / "nyiso_curtailment_monthly.csv").write_text(_MONTHLY_CSV)


class TestCurateNyisoRenewableCurtailment(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        _write_fixture(self.raw_root)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_builder_frames(self) -> None:
        """Annual and monthly frames parse with the expected dtypes/values."""
        annual = curate_nrc.build_annual_frame(self.raw_root)
        self.assertEqual(len(annual), 3)
        nyca_wind = annual[
            (annual["geographic_scope"] == "NYCA") & (annual["resource_type"] == "wind")
        ].iloc[0]
        self.assertAlmostEqual(nyca_wind["curtailed_energy_gwh"], 161.9, places=3)
        self.assertAlmostEqual(nyca_wind["curtailed_pct"], 3.4, places=3)
        west_wind = annual[annual["geographic_scope"] == "WEST"].iloc[0]
        self.assertTrue(pd.isna(west_wind["curtailed_pct"]))

        monthly = curate_nrc.build_monthly_frame(self.raw_root)
        self.assertEqual(len(monthly), 4)
        jan_nyca = monthly[
            (monthly["geographic_scope"] == "NYCA") & (monthly["month"] == 1)
        ].iloc[0]
        self.assertAlmostEqual(jan_nyca["curtailed_pct"], 5.8, places=3)
        self.assertTrue(pd.isna(jan_nyca["curtailed_energy_gwh"]))
        jan_west = monthly[
            (monthly["geographic_scope"] == "WEST") & (monthly["month"] == 1)
        ].iloc[0]
        self.assertAlmostEqual(jan_west["curtailed_energy_gwh"], 0.02, places=3)
        self.assertTrue(pd.isna(jan_west["curtailed_pct"]))

    def test_curate_writes_valid_partitions(self) -> None:
        """curate() writes both schema-valid Parquet partitions through write_clean."""
        written = curate_nrc.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 2)
        for path in written:
            validate_clean(path)  # raises on any schema mismatch

        annual_path = next(p for p in written if "monthly" not in p.parent.parent.name)
        got_annual = pd.read_parquet(annual_path)
        self.assertEqual(len(got_annual), 3)
        self.assertTrue((got_annual["iso"] == "NYISO").all())

        monthly_path = next(p for p in written if "monthly" in p.parent.parent.name)
        got_monthly = pd.read_parquet(monthly_path)
        self.assertEqual(len(got_monthly), 4)


if __name__ == "__main__":
    unittest.main()
