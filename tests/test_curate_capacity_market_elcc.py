"""Tests for the capacity-market-elcc intake on a tiny synthetic fixture.

Writes a minimal unified MISO CSV (chosen because it is the strongest
penetration-curve candidate) into a tmp raw tree, runs ``curate``, and asserts
the written Parquet is schema-valid, the resource_class alias maps, and a
multi-point penetration curve round-trips. CLEAN_DIR is redirected to a tmp
dir.

A second test class exercises the real on-disk PJM raw CSV (not a synthetic
fixture) to confirm the thermal class-rating rows added by the 2026-07-14
intake (accreditation-basis-memo-2026-07-12.md §4.3 R3) resolve and
round-trip cleanly through the same seam.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_market_elcc as curate_elcc
from scripts.lib import capacity_market_elcc as elcc
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# Two resource classes, one a 3-point penetration curve (wind), one a single
# current-fleet point (storage, native battery_4hr alias). The trailing row
# has no elcc_pct and must be dropped.
_MISO_CSV = """iso,resource_class,study_vintage,penetration_pct,penetration_unit,elcc_pct,elcc_type,source_doc,source_page
MISO,wind,2024 Accreditation Reform,5.0,pct_of_installed_capacity,42.0,marginal,miso-wind-elcc-2024.pdf,Table 2
MISO,wind,2024 Accreditation Reform,15.0,pct_of_installed_capacity,28.5,marginal,miso-wind-elcc-2024.pdf,Table 2
MISO,wind,2024 Accreditation Reform,25.0,pct_of_installed_capacity,19.1,marginal,miso-wind-elcc-2024.pdf,Table 2
MISO,battery_4hr,2024 Accreditation Reform,,,95.0,class_average,miso-storage-elcc-2024.pdf,Table 5
MISO,solar,2024 Accreditation Reform,,,,class_average,miso-solar-elcc-2024.pdf,Table 3
"""


def _write_miso_fixture(raw_root: Path) -> None:
    d = elcc.raw_dir_for("MISO", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "miso.csv").write_text(_MISO_CSV)


class TestCurateCapacityMarketElcc(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_miso(self) -> pd.DataFrame:
        _write_miso_fixture(self.raw_root)
        written = curate_elcc.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(len(written), 1, "expected one MISO partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-market-elcc")
        return pd.read_parquet(path)

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate_miso()
        self.assertEqual(set(df["iso"]), {"MISO"})
        self.assertEqual(list(df.columns), list(elcc.CANONICAL_COLUMNS))

    def test_native_resource_class_alias_mapped(self) -> None:
        df = self._curate_miso()
        self.assertIn("storage_4hr", set(df["resource_class"]))
        self.assertNotIn("battery_4hr", set(df["resource_class"]))

    def test_penetration_curve_multi_point(self) -> None:
        df = self._curate_miso()
        wind = df[df["resource_class"] == "wind"].sort_values("penetration_pct")
        self.assertEqual(list(wind["penetration_pct"]), [5.0, 15.0, 25.0])
        self.assertEqual(list(wind["elcc_pct"]), [42.0, 28.5, 19.1])
        # ELCC declines as penetration rises (the marginal-curve signature).
        self.assertTrue(wind["elcc_pct"].is_monotonic_decreasing)

    def test_single_point_rating_has_null_penetration(self) -> None:
        df = self._curate_miso()
        storage = df[df["resource_class"] == "storage_4hr"]
        self.assertTrue(storage["penetration_pct"].isna().all())
        self.assertEqual(storage["elcc_pct"].iloc[0], 95.0)

    def test_valueless_row_dropped(self) -> None:
        df = self._curate_miso()
        self.assertTrue(df[df["resource_class"] == "solar"].empty)

    def test_empty_iso_is_skipped(self) -> None:
        written = curate_elcc.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(written, [])

    def test_unregistered_iso_raises(self) -> None:
        with self.assertRaises(ValueError):
            curate_elcc.curate(raw_root=self.raw_root, isos=["NOTANISO"])

    def test_vocab_guard_rejects_bad_resource_class(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["MISO"],
                "resource_class": ["not_a_class"],
                "study_vintage": ["2024"],
                "penetration_pct": [pd.NA],
                "penetration_unit": [pd.NA],
                "elcc_pct": [50.0],
                "elcc_type": ["class_average"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            elcc.validate_tidy(elcc.finalize(bad))

    def test_miso_registered(self) -> None:
        registry = elcc.load_registry()
        self.assertIn("MISO", registry)


_PJM_THERMAL_CLASSES = {
    "nuclear",
    "coal",
    "gas_cc",
    "gas_ct",
    "gas_ct_dual_fuel",
    "diesel",
    "oil_ct",
    "steam",
    "waste_to_energy",
}


class TestPjmThermalElccIntake(unittest.TestCase):
    """Loader-resolvability + schema round-trip for the real on-disk PJM CSV.

    Unlike :class:`TestCurateCapacityMarketElcc`, this reads the actual
    ``data/raw/capacity-market/elcc/pjm/pjm.csv`` (not a synthetic fixture) so
    the 2026-07-14 thermal intake (accreditation-basis-memo-2026-07-12.md
    §4.3 R3) is exercised end to end. Only ``CLEAN_DIR`` is redirected to a
    tmp dir; ``raw_root`` is the repo's real raw tree.
    """

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_pjm(self) -> pd.DataFrame:
        written = curate_elcc.curate(isos=["PJM"])
        self.assertEqual(len(written), 1, "expected one PJM partition")
        path = written[0]
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-market-elcc")
        return pd.read_parquet(path)

    def test_thermal_classes_present_and_rated(self) -> None:
        df = self._curate_pjm()
        present = set(df["resource_class"]) & _PJM_THERMAL_CLASSES
        self.assertEqual(present, _PJM_THERMAL_CLASSES)
        thermal = df[df["resource_class"].isin(_PJM_THERMAL_CLASSES)]
        self.assertTrue((thermal["elcc_pct"] > 0).all())
        self.assertTrue((thermal["elcc_pct"] <= 100).all())

    def test_official_final_2026_2027_thermal_ratings(self) -> None:
        df = self._curate_pjm()
        vintage = df[df["study_vintage"] == "2026/2027 BRA (official/final)"]
        rated = dict(zip(vintage["resource_class"], vintage["elcc_pct"]))
        # PJM ELCC Class Ratings for the 2026/2027 BRA (final ratings doc p.1).
        self.assertEqual(rated["nuclear"], 95.0)
        self.assertEqual(rated["coal"], 83.0)
        self.assertEqual(rated["gas_cc"], 74.0)
        self.assertEqual(rated["gas_ct"], 60.0)
        self.assertEqual(rated["gas_ct_dual_fuel"], 78.0)
        self.assertEqual(rated["diesel"], 91.0)
        self.assertEqual(rated["steam"], 73.0)
        # Not itemized until the 2027/2028 portfolio.
        self.assertNotIn("waste_to_energy", rated)
        self.assertNotIn("oil_ct", rated)

    def test_gas_cc_penetration_left_null_both_official_vintages(self) -> None:
        # Table 5's Gas Combined Cycle installed-MW row combines Single+Dual
        # Fuel capacity, and Dual Fuel CC is a separately-unrated class — no
        # clean single-fuel-only MW split is published, so it must stay null
        # rather than be guessed (rule 13 / never-guess).
        df = self._curate_pjm()
        gas_cc_official = df[
            (df["resource_class"] == "gas_cc")
            & df["study_vintage"].str.contains("official/final")
        ]
        self.assertEqual(len(gas_cc_official), 2)
        self.assertTrue(gas_cc_official["penetration_pct"].isna().all())
        self.assertTrue(gas_cc_official["penetration_unit"].isna().all())
        self.assertTrue((gas_cc_official["elcc_pct"] == 74.0).all())

    def test_preliminary_er24_99_marginal_trend_nine_years(self) -> None:
        df = self._curate_pjm()
        coal_marginal = df[
            (df["resource_class"] == "coal") & (df["elcc_type"] == "marginal")
        ].sort_values("study_vintage")
        self.assertEqual(len(coal_marginal), 9)
        self.assertTrue(coal_marginal["penetration_pct"].isna().all())

    def test_dec2021_tranche_has_no_thermal_rows(self) -> None:
        # The Dec-2021 report predates the reform that extended ELCC class
        # ratings to thermal at all — a real methodology gap, not a retrieval
        # miss (docs/handoffs/pjm-thermal-elcc-intake-2026-07-14.md).
        df = self._curate_pjm()
        dec2021 = df[df["study_vintage"].str.contains("Dec 2021 ELCC Report")]
        self.assertFalse(dec2021.empty)
        self.assertTrue(set(dec2021["resource_class"]).isdisjoint(_PJM_THERMAL_CLASSES))

    def test_no_key_collisions_among_thermal_rows(self) -> None:
        df = self._curate_pjm()
        thermal = df[df["resource_class"].isin(_PJM_THERMAL_CLASSES)]
        key = thermal[
            ["iso", "resource_class", "study_vintage", "penetration_pct"]
        ].astype(str)
        self.assertEqual(len(key), len(key.drop_duplicates()))


if __name__ == "__main__":
    unittest.main()
