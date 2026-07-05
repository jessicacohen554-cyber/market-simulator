"""Tests for the confirmed-retirements intake on a tiny synthetic fixture.

Writes a minimal ERCOT registry CSV plus a fixture EIA-860 spine parquet into a
tmp raw tree, runs ``curate``, and asserts the written Parquet is schema-valid
and the tidy reconciliation (dtypes, superseded coercion, class vocabulary) is
correct. NOT a full-data run: CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_capacity_deliverability.py) so it never touches the real tree.
Also covers the spine cross-check (unknown plant / MW off > 5 % fail curation),
the closed confirmation-class vocabulary, and the skip-empty path.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_confirmed_retirements as curate_cr
from scripts.lib import clean_io
from scripts.lib import confirmed_retirements as cr
from scripts.lib.clean_io import validate_clean

# One live row + one superseded row (must cite its superseding instrument). The
# native class label "nso" exercises the ERCOT alias -> rto_deactivation.
_ERCOT_CSV = """iso,plant_id,generator_id,unit_name,capacity_mw,exit_year,exit_month,confirmation_class,instrument_id,instrument,instrument_date,superseded,superseding_instrument,source_url,source_doc,accessed,notes
ERCOT,111,1,Alpha 1,100.0,2027,3,nso,ercot-nso-alpha-1,ERCOT NSO acceptance,2024-01-01,false,,https://ercot.example/1,posting,2026-07-05,seed
ERCOT,111,2,Alpha 2,200.0,2026,,consent_decree,cd-alpha-2,Consent decree,2023-06-01,true,DOE 202(c) order keeps it running,https://ercot.example/2,posting,2026-07-05,superseded example
"""

# Spine: the two Alpha units exist with the stated nameplates.
_SPINE = pd.DataFrame(
    {
        "plant_id": [111, 111],
        "generator_id": ["1", "2"],
        "nameplate_capacity_mw": [100.0, 200.0],
    }
)


class TestCurateConfirmedRetirements(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        (self.raw_root / cr.DATATYPE).mkdir(parents=True)
        self.spine_path = root / "spine.parquet"
        _SPINE.to_parquet(self.spine_path, index=False)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _write(self, text: str, iso: str = "ercot") -> None:
        (self.raw_root / cr.DATATYPE / f"{iso}.csv").write_text(text)

    def _curate(self) -> pd.DataFrame:
        self._write(_ERCOT_CSV)
        written = curate_cr.curate(
            raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
        )
        self.assertEqual(len(written), 1)
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "confirmed-retirements")
        return pd.read_parquet(written[0])

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate()
        self.assertEqual(list(df.columns), list(cr.CANONICAL_COLUMNS))
        self.assertEqual(set(df["iso"]), {"ERCOT"})

    def test_class_alias_and_superseded(self) -> None:
        df = self._curate()
        # Native "nso" mapped to canonical rto_deactivation; superseded coerced.
        self.assertIn("rto_deactivation", set(df["confirmation_class"]))
        self.assertEqual(sorted(df["superseded"].tolist()), [False, True])

    def test_spine_unknown_plant_fails(self) -> None:
        bad = _ERCOT_CSV.replace("ERCOT,111,1", "ERCOT,999,1")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_cr.curate(
                raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
            )
        self.assertIn("not in EIA-860 spine", str(ctx.exception))

    def test_spine_mw_mismatch_fails(self) -> None:
        # 100 -> 130 is 30 % off the 100 MW nameplate (> 5 %).
        bad = _ERCOT_CSV.replace("Alpha 1,100.0", "Alpha 1,130.0")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_cr.curate(
                raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
            )
        self.assertIn("off", str(ctx.exception))

    def test_pre_window_exit_year_fails(self) -> None:
        bad = _ERCOT_CSV.replace(",2027,3,", ",2019,3,")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_cr.curate(
                raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
            )
        self.assertIn("window start", str(ctx.exception))

    def test_bad_confirmation_class_fails(self) -> None:
        bad = _ERCOT_CSV.replace("consent_decree", "announced")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_cr.curate(
                raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
            )
        self.assertIn("confirmation_class", str(ctx.exception))

    def test_superseded_without_citation_fails(self) -> None:
        bad = _ERCOT_CSV.replace("true,DOE 202(c) order keeps it running", "true,")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_cr.curate(
                raw_root=self.raw_root, isos=["ERCOT"], spine_path=self.spine_path
            )
        self.assertIn("superseding_instrument", str(ctx.exception))

    def test_missing_csv_skips(self) -> None:
        # No CSV for MISO -> empty frame -> skipped, nothing written.
        written = curate_cr.curate(
            raw_root=self.raw_root, isos=["MISO"], spine_path=self.spine_path
        )
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
