"""Tests for the ``vlr-pocket-groups`` intake on a tiny synthetic fixture.

CLEAN_DIR is redirected to a tempdir (``CleanDirTestCase``), so the real tree
is never touched. Trivial case first (one unit), then a two-group pocket, the
family derivation, and the guards (one unit in two groups; unknown prime mover;
absent ISO file skipped).
"""

import pandas as pd
import pytest

from scripts.data import curate_vlr_pocket_groups as curate_vpg
from scripts.lib import vlr_pocket_groups as vpg
from scripts.lib.clean_io import read_clean, validate_clean
from tests.helpers.base import CleanDirTestCase

_HEADER = (
    "iso,pocket,group_id,plant_code,plant_name,unit_id,eia860_prime_mover,"
    "eia860_energy_source,eia860_retirement_year,source_doc,source_page\n"
)


def _row(group, plant, unit, pm="ST", es="NG", ret=""):
    return f"MISO,P1,{group},{plant},Plant {plant},{unit},{pm},{es},{ret},doc.pdf,p.1\n"


class TestCurateVlrPocketGroups(CleanDirTestCase):
    """Curate round trip on a fixture raw tree."""

    def _write(self, body: str) -> None:
        d = vpg.raw_dir_for("MISO", self.tmp_path / "raw")
        d.mkdir(parents=True, exist_ok=True)
        (d / "miso.csv").write_text(_HEADER + body)

    def _curate(self) -> pd.DataFrame:
        written = curate_vpg.curate(raw_root=self.tmp_path / "raw", isos=["MISO"])
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        return read_clean(vpg.DATATYPE, iso="MISO")

    def test_one_unit(self) -> None:
        self._write(_row("A", 100, "1"))
        df = self._curate()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, "uc_family"], "st_gas")
        self.assertEqual(int(df.loc[0, "plant_code"]), 100)
        self.assertTrue(pd.isna(df.loc[0, "eia860_retirement_year"]))

    def test_two_groups_and_families(self) -> None:
        self._write(
            _row("A", 100, "1", ret="2016")
            + _row("A", 100, "4", pm="GT", es="DFO")
            + _row("B", 200, "6", es="SUB")
            + _row("B", 300, "1", pm="CA")
        )
        df = self._curate()
        fam = dict(zip(zip(df.plant_code, df.unit_id), df.uc_family))
        self.assertEqual(fam[(100, "1")], "st_gas")
        self.assertEqual(fam[(100, "4")], "ct")
        self.assertEqual(fam[(200, "6")], "coal")
        self.assertEqual(fam[(300, "1")], "cc")
        self.assertEqual(df.loc[df.unit_id == "1"].eia860_retirement_year.max(), 2016.0)

    def test_unit_in_two_groups_refused(self) -> None:
        self._write(_row("A", 100, "1") + _row("B", 100, "1"))
        with self.assertRaises(ValueError):
            curate_vpg.curate(raw_root=self.tmp_path / "raw", isos=["MISO"])

    def test_absent_file_skipped(self) -> None:
        self.assertEqual(
            curate_vpg.curate(raw_root=self.tmp_path / "raw", isos=["MISO"]), []
        )


def test_unknown_prime_mover_raises() -> None:
    with pytest.raises(ValueError):
        vpg.uc_family_for("HY", "WAT")
