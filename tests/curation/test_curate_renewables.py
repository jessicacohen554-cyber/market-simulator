"""Tests for scripts/data/curate_renewables.py.

Drives the curation on tiny synthetic raw fixtures (never the real data tree):
a wide HSL frame is unpivoted to the long ``renewables`` schema, written through
``clean_io.write_clean`` into a redirected temp CLEAN_DIR, and round-trip
validated. Covers the schema contract (dtypes, keys, tz-aware UTC), the
``curtailment_mw = hsl_mw - generation_mw`` reconciliation, the
``hour`` -> ``interval_start_utc`` / ``interval_start_local`` mapping
(standard-time offset, Feb 29 dropped in a leap year), and the CAISO 5-minute
curtailment cross-check against a synthetic workbook.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean
from scripts.data.curate_renewables import (
    FUELS,
    IsoSource,
    curate_iso_year,
    reconcile_caiso_curtailment,
    reconstruct_interval_starts,
    unpivot_to_long,
)


def _non_leap_hours(year: int) -> pd.DatetimeIndex:
    """The year's hourly wall-clock calendar with Feb 29 dropped (8760 hours)."""
    rng = pd.date_range(
        f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left"
    )
    return rng[~((rng.month == 2) & (rng.day == 29))]


def _synthetic_wide(year: int) -> pd.DataFrame:
    """A tiny synthetic wide HSL frame: a full 8760-hour year of toy values.

    ``hour`` is the contiguous index the curator expects; generation and HSL
    are deterministic so the implied curtailment (hsl - gen) is known per hour.
    """
    n = len(_non_leap_hours(year))
    h = np.arange(n)
    return pd.DataFrame(
        {
            "hour": h.astype("int64"),
            "wind_gen_mw": 100.0 + (h % 24).astype(float),
            "wind_hsl_mw": 100.0 + (h % 24).astype(float) + (h % 5) * 2.0,
            "solar_gen_mw": (h % 24).astype(float) * 3.0,
            "solar_hsl_mw": (h % 24).astype(float) * 3.0 + (h % 7) * 1.0,
        }
    )


class CleanDirRedirect(unittest.TestCase):
    """Redirect CLEAN_DIR to a temp dir so writes never touch the repo tree."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.tmp / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()


class TestUnpivotAndMapping(unittest.TestCase):
    def test_unpivot_shapes_and_reconciliation(self):
        wide = _synthetic_wide(2023)
        long = unpivot_to_long(wide, "CAISO", 2023, std_offset_hours=8)

        self.assertEqual(len(long), 2 * len(wide))
        self.assertEqual(set(long["fuel"].unique()), set(FUELS))
        self.assertEqual(set(long["zone"].unique()), {"SYSTEM"})
        self.assertEqual(set(long["iso"].unique()), {"CAISO"})

        # curtailment_mw == hsl_mw - generation_mw, exactly, per fuel.
        for fuel in FUELS:
            sub = long[long["fuel"] == fuel]
            np.testing.assert_allclose(
                sub["curtailment_mw"].to_numpy(),
                (sub["hsl_mw"] - sub["generation_mw"]).to_numpy(),
                atol=0,
            )

    def test_standard_time_offset_and_calendar(self):
        wide = _synthetic_wide(2023)
        utc, local = reconstruct_interval_starts(
            wide["hour"].to_numpy(), 2023, std_offset_hours=8
        )
        # tz-aware UTC vs tz-naive local, offset by exactly the standard offset.
        self.assertEqual(str(utc.dt.tz), "UTC")
        self.assertIsNone(local.dt.tz)
        self.assertEqual(local.iloc[0], pd.Timestamp("2023-01-01 00:00"))
        self.assertEqual(utc.iloc[0], pd.Timestamp("2023-01-01 08:00", tz="UTC"))
        delta = utc.dt.tz_localize(None) - local
        self.assertTrue((delta == pd.Timedelta(hours=8)).all())

    def test_ercot_offset_is_six_hours(self):
        wide = _synthetic_wide(2023)
        utc, local = reconstruct_interval_starts(
            wide["hour"].to_numpy(), 2023, std_offset_hours=6
        )
        self.assertEqual(utc.iloc[0], pd.Timestamp("2023-01-01 06:00", tz="UTC"))

    def test_leap_year_drops_feb_29(self):
        wide = _synthetic_wide(2024)  # leap year
        long = unpivot_to_long(wide, "CAISO", 2024, std_offset_hours=8)
        local = pd.DatetimeIndex(long["interval_start_local"].unique())
        self.assertEqual(len(local), 8760)
        self.assertFalse(((local.month == 2) & (local.day == 29)).any())
        # The 2024 labels still run to the true year end.
        self.assertEqual(local.min(), pd.Timestamp("2024-01-01 00:00"))
        self.assertEqual(local.max(), pd.Timestamp("2024-12-31 23:00"))

    def test_non_contiguous_hour_rejected(self):
        wide = _synthetic_wide(2023)
        wide.loc[0, "hour"] = 99999  # break the 0..n-1 contract
        with self.assertRaises(ValueError):
            unpivot_to_long(wide, "CAISO", 2023, std_offset_hours=8)


class TestCurateWritesSchemaValid(CleanDirRedirect):
    def _write_wide(self, prefix: str, year: int) -> Path:
        raw = self.tmp / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        path = raw / f"{prefix}_{year}_hsl_hourly.parquet"
        _synthetic_wide(year).to_parquet(path)
        return raw

    def test_curate_iso_year_roundtrips(self):
        raw = self._write_wide("ercot", 2023)
        spec = IsoSource(
            iso="ERCOT",
            hsl_dir=raw,
            file_prefix="ercot",
            std_offset_hours=6,
            curtailment_dir=None,  # no workbook cross-check for the fixture
        )
        out = curate_iso_year(spec, 2023)

        # Written under the redirected clean tree, partitioned by iso + year.
        self.assertTrue(out.exists())
        self.assertEqual(out.name, "renewables_2023.parquet")
        self.assertIn("ERCOT", out.parts)
        self.assertIn(str(clean_io.paths.CLEAN_DIR), str(out))

        schema = validate_clean(out)  # round-trip schema check
        self.assertEqual(schema.datatype, "renewables")

        df = pd.read_parquet(out)
        self.assertEqual(len(df), 2 * 8760)
        np.testing.assert_allclose(
            df["curtailment_mw"].to_numpy(),
            (df["hsl_mw"] - df["generation_mw"]).to_numpy(),
            atol=0,
        )


class TestCaisoCurtailmentCrossCheck(unittest.TestCase):
    """The CAISO 5-minute workbook cross-check (reconcile_caiso_curtailment)."""

    def _write_workbook(self, path: Path) -> dict[str, np.ndarray]:
        """Write a minimal Curtailments workbook; return the hourly series it
        aggregates to (wind/solar, length 8760)."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Curtailments"
        ws.append(
            [
                "Date",
                "Hour",
                "Interval",
                "Wind Curtailment",
                "Solar Curtailment",
                "Reason",
            ]
        )
        # Single 5-min interval of curtailment at hour-of-year 0 (Jan 1, Hour 1,
        # Interval 1): the loader averages over 12 intervals/hour, so 24 -> 2.0.
        ws.append(["2023-01-01", 1, 1, 24.0, 12.0, "System"])
        # A December row (zero curtailment) so the sheet spans the full year and
        # the cross-check runs rather than skipping a partial-year workbook.
        ws.append(["2023-12-31", 24, 1, 0.0, 0.0, "System"])
        wb.save(path)

        wind = np.zeros(8760)
        solar = np.zeros(8760)
        wind[0] = 24.0 / 12.0
        solar[0] = 12.0 / 12.0
        return {"wind": wind, "solar": solar}

    def test_cross_check_passes_and_detects_mismatch(self):
        with TemporaryDirectory() as tmp:
            workbook = Path(tmp) / "productionandcurtailmentsdata_2023.xlsx"
            expected = self._write_workbook(workbook)

            # Build a wide frame whose hsl - gen equals the workbook curtailment.
            wide = _synthetic_wide(2023)
            for fuel in FUELS:
                wide[f"{fuel}_hsl_mw"] = wide[f"{fuel}_gen_mw"] + expected[fuel]
            long = unpivot_to_long(wide, "CAISO", 2023, std_offset_hours=8)

            # Consistent frame: cross-check passes silently.
            reconcile_caiso_curtailment(long, workbook, 2023)

            # Tamper one curtailment value: the cross-check must raise.
            bad = long.copy()
            bad.loc[bad.index[0], "curtailment_mw"] += 5.0
            with self.assertRaises(AssertionError):
                reconcile_caiso_curtailment(bad, workbook, 2023)


if __name__ == "__main__":
    unittest.main()
