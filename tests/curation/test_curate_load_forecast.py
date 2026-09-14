"""Tests for the ``load-forecast`` intake on tiny synthetic fixtures.

Builds a minimal raw tree in a tmp dir (a transcription CSV for MISO, a
two-sheet workbook standing in for the CEC's CAISO forms), runs ``curate``, and
asserts the written Parquet is schema-valid and the tidy contract holds. NOT a
full-data run: :class:`tests.helpers.base.RawFixtureTestCase` redirects
``paths.CLEAN_DIR`` to a tmp dir so nothing touches the real tree.

Trivial case first (one ISO, one series), then the native-workbook parser and
the vocabulary / duplicate-key / metric-unit guards.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from scripts.data import curate_load_forecast as curate_lf
from scripts.lib import load_forecast as lf
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import RawFixtureTestCase

# One ISO, one series, three years — the trivial case. Deliberately uses the
# canonical column set exactly as a transcription session produces it.
_MISO_CSV = """iso,edition,vintage,scenario,published_case,area,area_type,component,metric,year,value,unit,basis,source_doc,source_page
MISO,2026 LTLF,2026,mid,Current Trajectory,MISO,iso,total,energy_gwh,2026,677700.0,gwh,net,deck.pdf,slide 15
MISO,2026 LTLF,2026,mid,Current Trajectory,MISO,iso,total,energy_gwh,2030,868700.0,gwh,net,deck.pdf,slide 15
MISO,2026 LTLF,2026,mid,Current Trajectory,MISO,iso,total,energy_gwh,2046,1104000.0,gwh,net,deck.pdf,slide 15
MISO,2026 LTLF,2026,low,Low Trajectory,MISO,iso,total,energy_gwh,2046,885000.0,gwh,net,deck.pdf,slide 15
"""


def _write_miso(raw_root: Path) -> None:
    d = lf.raw_dir_for("MISO", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "miso.csv").write_text(_MISO_CSV)


def _write_caiso_workbook(raw_root: Path) -> None:
    """A minimal stand-in for one CEC planning-area workbook (Forms 1.2 + 1.5)."""
    d = lf.raw_dir_for("CAISO", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    energy = wb.active
    energy.title = "Form 1.2"
    energy.append(["Form 1.2 - PGE Planning Area"])
    energy.append(["Total Energy to Serve Load (GWh)"])
    energy.append(["Year", "Total_Consumption", "Total_Energy_to_Serve_Load"])
    energy.append([2026, 90000.0, 100000.0])
    energy.append([2031, 99000.0, 110000.0])
    peak = wb.create_sheet("Form 1.5")
    peak.append(["Form 1.5 - PGE Planning Area"])
    peak.append(["Year", "Historical_Net_Peak", "Forecasted_1.in.2_Peak"])
    peak.append([2025, 20718.0, None])
    peak.append([2026, None, 21234.0])
    wb.save(d / "CED2025-Baseline-PGE.xlsx")


class TestCurateLoadForecast(RawFixtureTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.raw_root = self.tmp_path / "raw"
        self.raw_root.mkdir(parents=True, exist_ok=True)

    # -- trivial case: one ISO, the transcription route ---------------------
    def _curate_miso(self) -> pd.DataFrame:
        _write_miso(self.raw_root)
        written = curate_lf.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(len(written), 1, "expected one MISO partition")
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "load-forecast")
        return pd.read_parquet(written[0])

    def test_schema_valid_and_partitioned_by_iso(self) -> None:
        df = self._curate_miso()
        self.assertEqual(set(df["iso"]), {"MISO"})
        self.assertEqual(list(df.columns), list(lf.CANONICAL_COLUMNS))
        self.assertEqual(len(df), 4)

    def test_year_and_vintage_are_integers(self) -> None:
        """The shared finalizer coerces every numeric column to float; the
        package restores the two the schema declares int64."""
        df = self._curate_miso()
        self.assertTrue(pd.api.types.is_integer_dtype(df["year"]))
        self.assertTrue(pd.api.types.is_integer_dtype(df["vintage"]))

    def test_idempotent(self) -> None:
        first = self._curate_miso()
        second = curate_lf.curate(raw_root=self.raw_root, isos=["MISO"])
        pd.testing.assert_frame_equal(first, pd.read_parquet(second[0]))

    def test_missing_iso_is_skipped_not_raised(self) -> None:
        """An ISO whose sources have not landed yields nothing, quietly."""
        written = curate_lf.curate(raw_root=self.raw_root, isos=["NYISO"])
        self.assertEqual(written, [])

    # -- the native-workbook route -----------------------------------------
    def test_native_workbook_parsed_without_a_csv(self) -> None:
        _write_caiso_workbook(self.raw_root)
        written = curate_lf.curate(raw_root=self.raw_root, isos=["CAISO"])
        self.assertEqual(len(written), 1)
        self.assertEqual(validate_clean(written[0]).datatype, "load-forecast")
        df = pd.read_parquet(written[0])
        energy = df[(df["metric"] == "energy_gwh") & (df["year"] == 2031)]
        self.assertEqual(float(energy["value"].iloc[0]), 110000.0)
        self.assertEqual(set(energy["area"]), {"PGE"})
        # Form 1.5's historical column lands as scenario "actual", never "mid" —
        # a published actual is never a forecast row (rule 13 posture).
        actual = df[df["scenario"] == "actual"]
        self.assertEqual(list(actual["year"]), [2025])
        self.assertEqual(float(actual["value"].iloc[0]), 20718.0)

    # -- the value-level guards --------------------------------------------
    def test_unknown_component_is_rejected(self) -> None:
        _write_miso(self.raw_root)
        path = lf.raw_dir_for("MISO", self.raw_root) / "miso.csv"
        path.write_text(
            _MISO_CSV.replace(",total,energy_gwh,2026", ",hydrogen,energy_gwh,2026")
        )
        with pytest.raises(ValueError, match="component"):
            curate_lf.curate(raw_root=self.raw_root, isos=["MISO"])

    def test_metric_unit_disagreement_is_rejected(self) -> None:
        _write_miso(self.raw_root)
        path = lf.raw_dir_for("MISO", self.raw_root) / "miso.csv"
        path.write_text(
            _MISO_CSV.replace(
                "energy_gwh,2026,677700.0,gwh", "energy_gwh,2026,677700.0,mw"
            )
        )
        with pytest.raises(ValueError, match="metric/unit"):
            curate_lf.curate(raw_root=self.raw_root, isos=["MISO"])

    def test_duplicate_key_is_rejected(self) -> None:
        """`basis` is in the key precisely so a Gross/Net pair does not collide;
        a genuine repeat still must not pass silently."""
        _write_miso(self.raw_root)
        path = lf.raw_dir_for("MISO", self.raw_root) / "miso.csv"
        lines = _MISO_CSV.strip().splitlines()
        path.write_text("\n".join(lines + [lines[1]]) + "\n")
        with pytest.raises(ValueError, match="duplicate key"):
            curate_lf.curate(raw_root=self.raw_root, isos=["MISO"])

    def test_unknown_iso_names_the_missing_module(self) -> None:
        # TVA is the unregistered example: SPP became the seventh model ISO on
        # 2026-09-06 (lane SPP-20), so it is no longer a valid "unknown" fixture.
        # (matched without the `scripts/` prefix so the refactor guard's
        # script-reference scanner does not read a fixture path as a reference)
        with pytest.raises(ValueError, match=r"lib/load_forecast/tva\.py present"):
            lf.parse_iso("TVA", self.raw_root)


class TestRegistryContract(unittest.TestCase):
    """The registry is the seam that keeps shared code free of ISO branching."""

    def test_every_model_iso_is_registered(self) -> None:
        self.assertEqual(
            set(lf.load_registry()),
            {"ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP"},
        )

    def test_specs_declare_an_edition_and_a_vintage(self) -> None:
        for iso, spec in lf.load_registry().items():
            self.assertTrue(spec.edition, iso)
            self.assertGreaterEqual(spec.vintage, 2020, iso)
            self.assertIn(spec.default_basis, lf.BASES, iso)

    def test_metric_unit_map_covers_the_metric_vocabulary(self) -> None:
        for metric, unit in lf.METRIC_UNITS.items():
            self.assertIn(unit, {"gwh", "mw", "count"}, metric)
