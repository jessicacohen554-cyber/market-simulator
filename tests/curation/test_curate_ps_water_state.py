"""Tests for the ps-water-state intake on a tiny synthetic App-B1 fixture.

Builds a minimal HEC-DSS-shaped hourly workbook (the Helms FLA Appendix B1
layout) in a tmp raw tree, runs ``curate``, and asserts the written Parquet is
schema-valid and the tidy reconciliation is correct: drifted sub-second stamps
round to the hour, the -901/-902 sentinels land as nulls, the publisher-signed
negative pumping flow survives, a mode-changeover hour may carry both
generation and pumping, and layout / clock / sentinel-discipline violations
fail loudly. ``CLEAN_DIR`` is redirected to a tmp dir by
:class:`tests.helpers.base.RawFixtureTestCase` so nothing touches the real
trees.

Trivial case first (three hours, one plant), then the failure modes.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from scripts.data import curate_ps_water_state as curate_ps
from scripts.lib import ps_water_state as ps
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import RawFixtureTestCase

#: The eight series columns in sheet order (B Part, C Part).
_HEADS = (
    ("COURTRIGHT_RES(KI15)", "ELEVATION"),
    ("COURTRIGHT_RES(KI15)", "STORAGE"),
    ("WISHON_RES(KI19)", "ELEVATION"),
    ("WISHON_RES(KI19)", "STORAGE"),
    ("HELMS_PH(KI29)", "FLOW-GENERATION"),
    ("HELMS_PH(KI29)", "GENERATION"),
    ("HELMS_PH(KI30)", "FLOW-PUMPING"),
    ("HELMS_PH(KI30)", "PUMPING"),
)

# Three data rows: a clean generating hour; a sentinel-laden hour whose stamp
# carries the HEC-DSS sub-second drift AND a publisher-signed negative pumping
# flow; a mode-changeover hour with BOTH generation and pumping.
_ROWS = [
    (
        dt.datetime(2022, 1, 1, 1, 0, 0),
        8100.0,
        100000.0,
        6500.0,
        95000.0,
        2000.0,
        250.0,
        0.0,
        0.0,
    ),
    (
        dt.datetime(2022, 1, 1, 1, 59, 59, 970000),
        -902.0,
        100100.0,
        -902.0,
        94900.0,
        0.0,
        0.0,
        -43.98,
        0.0,
    ),
    (
        dt.datetime(2022, 1, 1, 3, 0, 0),
        8101.0,
        -901.0,
        6501.0,
        94800.0,
        500.0,
        60.0,
        4000.0,
        450.0,
    ),
]


def _write_workbook(path, rows=_ROWS, heads=_HEADS, sheet=None) -> None:
    """Write a minimal App-B1-shaped hourly workbook to ``path``."""
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet if sheet is not None else "Hourly PG&E Data"
    ws.append(["Part A:", *["NF_KINGS_R"] * len(heads)])
    ws.append(["Part B:", *[b for b, _ in heads]])
    ws.append(["Part C:", *[c for _, c in heads]])
    ws.append(["Part D:", *[""] * len(heads)])
    ws.append(["Part E:", *["1Hour"] * len(heads)])
    ws.append(["Part F:", *["PG&E"] * len(heads)])
    ws.append(["Units:", "FT", "AF", "FT", "AF", "CFS", "MWH", "CFS", "MWH"])
    ws.append(
        ["Data Type:", *["INST-VAL"] * 4, "PER-AVER", "PER-CUM", "PER-AVER", "PER-CUM"]
    )
    for row in rows:
        ws.append(list(row))
    wb.save(path)


class TestCuratePsWaterState(RawFixtureTestCase):
    def _write_fixture(self, **kwargs) -> None:
        d = ps.raw_dir_for("CAISO", self.raw_dir)
        d.mkdir(parents=True, exist_ok=True)
        _write_workbook(d / "helms_fla_appb1_hydrology.xlsx", **kwargs)

    def _curate(self) -> pd.DataFrame:
        written = curate_ps.curate(raw_root=self.raw_dir, isos=["CAISO"])
        self.assertEqual(len(written), 1, "expected one CAISO partition")
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "ps-water-state")
        return pd.read_parquet(written[0])

    def test_trivial_roundtrip(self) -> None:
        """Three hours curate to three schema-valid rows with the right key."""
        self._write_fixture()
        df = self._curate()
        self.assertEqual(len(df), 3)
        self.assertEqual(set(df["iso"]), {"CAISO"})
        self.assertEqual(set(df["plant"]), {"HELMS"})
        self.assertEqual(list(df.columns), list(ps.CANONICAL_COLUMNS))
        first = df.iloc[0]
        self.assertEqual(first["generation_mwh"], 250.0)
        self.assertEqual(first["upper_storage_af"], 100000.0)

    def test_drifted_stamp_rounds_to_hour(self) -> None:
        """The HEC-DSS sub-second drifted stamp lands on the exact hour."""
        self._write_fixture()
        df = self._curate()
        self.assertEqual(
            list(df["interval_end_local"]),
            [
                pd.Timestamp("2022-01-01 01:00"),
                pd.Timestamp("2022-01-01 02:00"),
                pd.Timestamp("2022-01-01 03:00"),
            ],
        )

    def test_sentinels_null_and_signed_flow_survives(self) -> None:
        """-901/-902 land as nulls; the negative pumping flow is kept."""
        self._write_fixture()
        df = self._curate()
        drifted = df.iloc[1]
        self.assertTrue(pd.isna(drifted["upper_elevation_ft"]))  # -902
        self.assertAlmostEqual(drifted["flow_pumping_cfs"], -43.98)
        self.assertTrue(pd.isna(df.iloc[2]["upper_storage_af"]))  # -901

    def test_mode_changeover_hour_keeps_both(self) -> None:
        """An hour may carry both generation and pumping (no exclusivity)."""
        self._write_fixture()
        df = self._curate()
        both = df.iloc[2]
        self.assertEqual(both["generation_mwh"], 60.0)
        self.assertEqual(both["pumping_mwh"], 450.0)

    def test_negative_energy_fails_loudly(self) -> None:
        """A non-sentinel negative in an energy column raises, never nulls."""
        rows = [(_ROWS[0][0], *_ROWS[0][1:5], 2000.0, -5.0, 0.0, 0.0)]
        self._write_fixture(rows=rows)
        with self.assertRaisesRegex(ValueError, "generation_mwh"):
            curate_ps.curate(raw_root=self.raw_dir, isos=["CAISO"])

    def test_clock_gap_fails_loudly(self) -> None:
        """A missing hour breaks the gap-free clock assertion."""
        rows = [_ROWS[0], _ROWS[2], (dt.datetime(2022, 1, 1, 4, 0), *_ROWS[0][1:])]
        self._write_fixture(rows=rows)
        with self.assertRaisesRegex(ValueError, "gap-free"):
            curate_ps.curate(raw_root=self.raw_dir, isos=["CAISO"])

    def test_layout_change_fails_loudly(self) -> None:
        """Swapped series headers are refused rather than mis-mapped."""
        heads = list(_HEADS)
        heads[4], heads[5] = heads[5], heads[4]
        self._write_fixture(heads=tuple(heads))
        with self.assertRaisesRegex(ValueError, "expected"):
            curate_ps.curate(raw_root=self.raw_dir, isos=["CAISO"])

    def test_missing_sheet_fails_loudly(self) -> None:
        """A renamed sheet is a format change, not an empty result."""
        self._write_fixture(sheet="Hourly Data")
        with self.assertRaisesRegex(ValueError, "sheet"):
            curate_ps.curate(raw_root=self.raw_dir, isos=["CAISO"])

    def test_absent_snapshot_skips_iso(self) -> None:
        """An ISO with no snapshot yields no partition (registered-not-fetched)."""
        written = curate_ps.curate(raw_root=self.raw_dir, isos=["CAISO"])
        self.assertEqual(written, [])

    def test_rerun_is_idempotent(self) -> None:
        """Curating twice rewrites the same partition with identical rows."""
        self._write_fixture()
        first = self._curate()
        second = self._curate()
        pd.testing.assert_frame_equal(first, second)
