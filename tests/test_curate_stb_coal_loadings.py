"""Tests for the ``stb-coal-loadings`` curation (STB EP 724 Category 9) and its reader.

Trivial case first (one carrier, one region, one week), then the behaviours the real workbook exhibits:
other categories ignored, region spelling variants joined, blank weeks dropped rather than read as zero.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.data.stb_ep724 import annual_loadings_ratio, load_coal_loadings  # noqa: E402
from scripts.data.curate_stb_coal_loadings import curate  # noqa: E402
from tests.helpers.base import CleanDirTestCase  # noqa: E402

_HEAD = ["Railroad/\nRegion", "Category No.", "Sub-Category", "Measure", "Variable", "Sub-Variable"]
_C9 = "Coal Unit Train Loadings or Carloadings by Coal Production Region (Count)"


def _write(root: Path, weeks: list[datetime], rows: list[list]) -> None:
    """Write a minimal consolidated workbook with ``rows`` under ``root/stb-ep724``."""
    d = root / "stb-ep724"
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([_HEAD + weeks, *rows]).to_excel(
        d / "EP724_Consolidated_Data_through_2022-12-28.xlsx", header=False, index=False
    )


class TestCurateStbCoalLoadings(CleanDirTestCase):
    """Curation and reader behaviour on synthetic workbooks."""

    def test_single_series(self) -> None:
        """One carrier, one region, one week: plan and actual land as two rows."""
        _write(
            self.tmp_path,
            [datetime(2022, 1, 5)],
            [
                ["BNSF", 9, None, _C9, "Powder River Basin", "Loadings Plan", 40],
                ["BNSF", 9, None, _C9, "Powder River Basin", "Loadings Average", 30],
            ],
        )
        curate(raw_root=self.tmp_path)
        d = load_coal_loadings()
        self.assertEqual(len(d), 2)
        self.assertEqual(set(d.measure), {"plan", "actual"})
        self.assertEqual(float(d[d.measure == "actual"].value.iloc[0]), 30.0)

    def test_filters_and_normalises(self) -> None:
        """Other categories are ignored, region case variants join, blank weeks are dropped."""
        _write(
            self.tmp_path,
            [datetime(2021, 1, 6), datetime(2022, 1, 5)],
            [
                ["BNSF", 1, None, "Average Train Speed", "Coal unit", None, 24.1, 23.0],
                ["UP", 9, None, _C9, "Uinta basin", "Loadings Plan", 2, None],
                ["UP", 9, None, _C9, "Uinta Basin", "Loadings Average", 1, 1],
                ["UP", 9, None, _C9, "Powder River Basin", "Loadings Plan", 20, 20],
                ["UP", 9, None, _C9, "Powder River Basin", "Loadings Average", 18, 15],
            ],
        )
        curate(raw_root=self.tmp_path)
        d = load_coal_loadings()
        self.assertEqual(set(d.region), {"Uinta Basin", "Powder River Basin"})
        self.assertEqual(len(d[(d.region == "Uinta Basin") & (d.measure == "plan")]), 1)
        yr = annual_loadings_ratio(("UP",), "Powder River Basin")
        self.assertAlmostEqual(float(yr.loc[2021, "ratio"]), 0.9)
        self.assertAlmostEqual(float(yr.loc[2022, "ratio"]), 0.75)
