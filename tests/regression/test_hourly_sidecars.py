"""Committable ``hourly/`` bundle sidecars (run_calibration_full).

The slim-bundle gitignore rules drop every heavy solve output
(``dispatch/``, ``system.parquet``), so before these sidecars every
diagnostic session replayed the keeper to read its own hourlies. The
sidecar writers must (a) reconcile exactly with the unit-hour dispatch
frames they summarize, (b) cover every pass label written for the year,
and (c) write per-year system slices identical to the year's rows of the
full frame.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts import run_calibration_full as rcf


def _unit_frame(year: int, pass_label: str, n_units: int = 3, T: int = 4):
    """Tiny synthetic unit-hour dispatch frame in the bundle schema."""
    rows = []
    for g in range(n_units):
        for t in range(T):
            rows.append(
                {
                    "year": year,
                    "pass": pass_label,
                    "unit_id": f"u{g}",
                    "klass": "CC_REGULAR" if g % 2 == 0 else "CT_PEAKER",
                    "hour": t,
                    "mw": float(10 * g + t),
                }
            )
    return pd.DataFrame(rows)


class ClassHourlySidecarTest(unittest.TestCase):
    def test_reconciles_with_unit_frames_across_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "dispatch").mkdir()
            for label in ("P0", "P1"):
                _unit_frame(2024, label).to_parquet(
                    run_dir / "dispatch" / f"2024_{label}.parquet", index=False
                )
            out = rcf._write_class_hourly_sidecar(run_dir, 2024, ["P0", "P1"])
            self.assertEqual(out, run_dir / "hourly" / "class_hourly_2024.parquet")
            ch = pd.read_parquet(out)
            self.assertEqual(
                sorted(ch.columns), ["hour", "klass", "mw", "pass", "year"]
            )
            self.assertEqual(set(ch["pass"]), {"P0", "P1"})
            # Class-hour totals reconcile with the unit frame they summarize.
            unit = pd.read_parquet(run_dir / "dispatch" / "2024_P1.parquet")
            want = unit.groupby(["klass", "hour"])["mw"].sum()
            got = (
                ch[ch["pass"] == "P1"]
                .groupby(["klass", "hour"])["mw"]
                .sum()
                .reindex(want.index)
            )
            np.testing.assert_allclose(got.to_numpy(), want.to_numpy())


class SystemYearSidecarTest(unittest.TestCase):
    def test_per_year_slices_match_full_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            sysdf = pd.DataFrame(
                {
                    "year": [2024, 2024, 2025],
                    "pass": ["P1", "P1", "P1"],
                    "zone": ["North", "West", "North"],
                    "hour": [0, 0, 0],
                    "price": [30.0, 31.0, 45.0],
                    "demand": [100.0, 50.0, 110.0],
                }
            )
            rcf._write_system_year_sidecars(run_dir, sysdf)
            for year in (2024, 2025):
                got = pd.read_parquet(run_dir / "hourly" / f"system_{year}.parquet")
                want = sysdf[sysdf["year"] == year].reset_index(drop=True)
                pd.testing.assert_frame_equal(
                    got.reset_index(drop=True), want, check_dtype=False
                )


if __name__ == "__main__":
    unittest.main()
