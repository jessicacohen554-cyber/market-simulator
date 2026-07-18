"""Tests for the NYISO capacity-deliverability parser on a small fixture.

Writes the same rows as the real ``data/raw/capacity-deliverability/nyiso/
nyiso.csv`` (already canonical unified form) into a tmp raw tree, runs
``curate``, and asserts the written Parquet is schema-valid and that the
NYISO-specific shape holds: locality requirement rows carry both ``value_mw``
(ICAP requirement) and ``value_pu`` (LCR%), and the statewide NYCA row is an
``rto``-area-type ``system_requirement`` (IRM) with ``value_pu`` only. CLEAN_DIR
is redirected to a tmp dir (as in ``tests/test_curate_capacity_deliverability.py``)
so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_deliverability as curate_cd
from scripts.lib import capacity_deliverability as cd
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# One delivery year's worth of the real NYISO unified CSV shape: three
# localities each with a requirement (MW + LCR%) and an import_limit (MW
# only) row, plus the statewide NYCA IRM row (value_pu only).
_NYISO_CSV = """iso,delivery_year,season,area,area_type,metric,value_mw,value_pu,source_doc,source_page
NYISO,2025/2026,annual,NYC,locality,requirement,8673,0.785,2025-2026-LCR-Report-Clean.pdf,2
NYISO,2025/2026,annual,Long Island,locality,requirement,5423,1.065,2025-2026-LCR-Report-Clean.pdf,2
NYISO,2025/2026,annual,G-J,locality,requirement,11980,0.788,2025-2026-LCR-Report-Clean.pdf,2
NYISO,2025/2026,annual,NYC,locality,import_limit,2875,,2025-26-Locality-Bulk-Power-Transmission-Capability-Report_Final.pdf,7
NYISO,2025/2026,annual,Long Island,locality,import_limit,275,,2025-26-Locality-Bulk-Power-Transmission-Capability-Report_Final.pdf,7
NYISO,2025/2026,annual,G-J,locality,import_limit,4500,,2025-26-Locality-Bulk-Power-Transmission-Capability-Report_Final.pdf,7
NYISO,2025/2026,annual,NYCA,rto,system_requirement,,0.244,2025-2026-LCR-Report-Clean.pdf,2
"""


def _write_nyiso_fixture(raw_root: Path) -> None:
    """Drop the fixture CSV where the NYISO spec expects to find it."""
    d = cd.raw_dir_for("NYISO", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "nyiso.csv").write_text(_NYISO_CSV)


class TestCapacityDeliverabilityNyiso(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        # Redirect CLEAN_DIR so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_nyiso(self) -> pd.DataFrame:
        _write_nyiso_fixture(self.raw_root)
        written = curate_cd.curate(raw_root=self.raw_root, isos=["NYISO"])
        self.assertEqual(len(written), 1, "expected one NYISO partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-deliverability")
        return pd.read_parquet(path)

    def test_schema_valid_and_partitioned_by_iso(self) -> None:
        df = self._curate_nyiso()
        self.assertEqual(set(df["iso"]), {"NYISO"})
        self.assertEqual(list(df.columns), list(cd.CANONICAL_COLUMNS))

    def test_requirement_row_carries_mw_and_pu(self) -> None:
        df = self._curate_nyiso()
        nyc_req = df[(df["area"] == "NYC") & (df["metric"] == "requirement")]
        self.assertEqual(len(nyc_req), 1)
        row = nyc_req.iloc[0]
        self.assertEqual(row["value_mw"], 8673.0)
        self.assertEqual(row["value_pu"], 0.785)

    def test_nyca_rto_row_present_with_pu_only(self) -> None:
        df = self._curate_nyiso()
        nyca = df[df["area"] == "NYCA"]
        self.assertEqual(len(nyca), 1)
        row = nyca.iloc[0]
        self.assertEqual(row["area_type"], "rto")
        self.assertEqual(row["metric"], "system_requirement")
        self.assertTrue(pd.isna(row["value_mw"]))
        self.assertEqual(row["value_pu"], 0.244)

    def test_locality_default_area_type(self) -> None:
        df = self._curate_nyiso()
        localities = df[df["area"].isin(["NYC", "Long Island", "G-J"])]
        self.assertEqual(set(localities["area_type"]), {"locality"})

    def test_nyiso_registered(self) -> None:
        registry = cd.load_registry()
        self.assertIn("NYISO", registry)
        self.assertEqual(registry["NYISO"].default_area_type, "locality")
        self.assertEqual(registry["NYISO"].metric_aliases, {})


if __name__ == "__main__":
    unittest.main()
