"""Tests for the capacity-deliverability intake on a tiny synthetic fixture.

Writes a minimal unified PJM CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and the tidy reconciliation
(native CETO/CETL -> canonical requirement/import_limit, area_type / season
defaults, dtype coercion) is correct. NOT a full-data run: CLEAN_DIR is
redirected to a tmp dir (as in tests/test_curate_outages.py) so it never
touches the real tree. Also covers the vocabulary guard and the skip-empty path.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_deliverability as curate_cd
from scripts.lib import capacity_deliverability as cd
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# Two LDAs x two delivery years, native PJM metric labels (ceto/cetl) so the
# alias-mapping path is exercised; area_type/season left blank to test defaults.
# The last row is deliberately value-less (an unpublished cell) and must be
# dropped by the parser rather than written or raised on.
_PJM_CSV = """iso,delivery_year,season,area,area_type,metric,value_mw,value_pu,source_doc,source_page
PJM,2024/2025,,MAAC,,ceto,5100,,params-2024-2025.pdf,Table 7
PJM,2024/2025,,MAAC,,cetl,5960,,params-2024-2025.pdf,Table 7
PJM,2025/2026,,MAAC,,ceto,5000,,params-2025-2026.pdf,Table 7
PJM,2025/2026,,MAAC,,cetl,3217,,params-2025-2026.pdf,Table 7
PJM,2025/2026,,BGE,,cetl,5900,,params-2025-2026.pdf,Table 7
PJM,2025/2026,,DEOK,,cetl,,,params-2025-2026.pdf,Table 7
"""


def _write_pjm_fixture(raw_root: Path) -> None:
    d = cd.raw_dir_for("PJM", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "pjm.csv").write_text(_PJM_CSV)


class TestCurateCapacityDeliverability(unittest.TestCase):
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

    def _curate_pjm(self) -> pd.DataFrame:
        _write_pjm_fixture(self.raw_root)
        written = curate_cd.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1, "expected one PJM partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-deliverability")
        return pd.read_parquet(path)

    def test_schema_valid_and_partitioned_by_iso(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(set(df["iso"]), {"PJM"})
        self.assertEqual(list(df.columns), list(cd.CANONICAL_COLUMNS))

    def test_native_metric_aliases_mapped(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(set(df["metric"]), {"requirement", "import_limit"})
        self.assertNotIn("ceto", set(df["metric"]))

    def test_defaults_and_values(self) -> None:
        df = self._curate_pjm()
        # area_type defaulted to the PJM spec default; season defaulted annual.
        self.assertEqual(set(df["area_type"]), {"lda"})
        self.assertEqual(set(df["season"]), {"annual"})
        cetl = df[(df["area"] == "MAAC") & (df["metric"] == "import_limit")]
        self.assertEqual(
            dict(zip(cetl["delivery_year"], cetl["value_mw"])),
            {"2024/2025": 5960.0, "2025/2026": 3217.0},
        )

    def test_valueless_row_dropped(self) -> None:
        df = self._curate_pjm()
        # The blank DEOK cetl row carried no value -> not materialized.
        self.assertTrue(df[(df["area"] == "DEOK")].empty)

    def test_empty_iso_is_skipped(self) -> None:
        # No CSV dropped for PJM -> curate writes nothing, does not raise.
        written = curate_cd.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(written, [])

    def test_unregistered_iso_raises(self) -> None:
        # An ISO whose module hasn't landed yet is an explicit error.
        with self.assertRaises(ValueError):
            curate_cd.curate(raw_root=self.raw_root, isos=["NOTANISO"])

    def test_vocab_guard_rejects_bad_metric(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "area": ["MAAC"],
                "area_type": ["lda"],
                "delivery_year": ["2025/2026"],
                "season": ["annual"],
                "metric": ["not_a_metric"],
                "value_mw": [1.0],
                "value_pu": [pd.NA],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            cd.validate_tidy(cd.finalize(bad))

    def test_pjm_registered(self) -> None:
        registry = cd.load_registry()
        self.assertIn("PJM", registry)
        self.assertEqual(registry["PJM"].default_area_type, "lda")


if __name__ == "__main__":
    unittest.main()
