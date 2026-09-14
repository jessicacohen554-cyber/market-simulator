"""Tests for the ``coal-stocks`` curation (EIA-923 Page 2 Coal Stocks Data).

Trivial case first (one plant, one rank), then the vintage and sentinel
behaviours the real EIA record actually exhibits.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.data.curate_coal_stocks import curate  # noqa: E402
from scripts.lib.clean_io import read_clean  # noqa: E402
from tests.helpers.base import CleanDirTestCase  # noqa: E402

_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

_BASE_COLS = [
    "Plant Id",
    "Combined Heat And Power Plant",
    "Plant Name",
    "Operator Name",
    "Operator Id",
    "Plant State",
    "Census Region",
    "NERC Region",
    "NAICS Code",
    "EIA Sector Number",
    "Sector Name",
    "Reported Fuel Type Code",
    "AER Fuel Type Code",
    "Physical Unit Label",
]


def _row(plant_id, fuel, quantities, sector="1", state="IL"):
    return {
        "Plant Id": plant_id,
        "Combined Heat And Power Plant": "N",
        "Plant Name": f"Plant {plant_id}",
        "Operator Name": "Op",
        "Operator Id": "1",
        "Plant State": state,
        "Census Region": "ENC",
        "NERC Region": "MRO",
        "NAICS Code": "22",
        "EIA Sector Number": sector,
        "Sector Name": "Electric Utility",
        "Reported Fuel Type Code": fuel,
        "AER Fuel Type Code": "COL",
        "Physical Unit Label": "short tons",
        **{f"Quantity {m}": q for m, q in zip(_MONTHS, quantities)},
    }


def _write_raw(raw_root: Path, year: int, rows, with_ba=True):
    d = raw_root / "coal-stocks"
    d.mkdir(parents=True, exist_ok=True)
    cols = list(_BASE_COLS) + [f"Quantity {m}" for m in _MONTHS]
    if with_ba:
        cols += ["Balancing Authority Code"]
        for r in rows:
            r.setdefault("Balancing Authority Code", "MISO")
    cols += ["YEAR"]
    for r in rows:
        r.setdefault("YEAR", year)
    path = d / f"coal_stocks_{year}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


class CurateCoalStocksTest(CleanDirTestCase):
    def setUp(self):
        super().setUp()
        self.raw = self.tmp_path / "raw"

    def _curate(self, year=2022):
        out = curate(raw_root=self.raw)
        self.assertEqual(len(out), 1)
        return read_clean("coal-stocks", year=year)

    def test_one_plant_one_rank_melts_to_twelve_rows(self):
        """Trivial case: 1 plant x 1 rank -> 12 tidy rows carrying each month."""
        _write_raw(self.raw, 2022, [_row(1001, "SUB", list(range(100, 112)))])
        df = self._curate()
        self.assertEqual(len(df), 12)
        self.assertEqual(sorted(df["month"]), list(range(1, 13)))
        self.assertEqual(set(df["year"]), {2022})
        jan = df[df.month == 1].iloc[0]
        self.assertEqual(jan["plant_id"], 1001)
        self.assertEqual(jan["energy_source"], "SUB")
        self.assertEqual(jan["ending_stock_tons"], 100.0)
        self.assertEqual(df[df.month == 12].iloc[0]["ending_stock_tons"], 111.0)

    def test_key_is_unique_across_two_ranks(self):
        """A plant holding two ranks files two rows; both survive, key unique."""
        _write_raw(
            self.raw,
            2022,
            [
                _row(1001, "SUB", [10] * 12),
                _row(1001, "BIT", [20] * 12),
            ],
        )
        df = self._curate()
        self.assertEqual(len(df), 24)
        self.assertFalse(
            df.duplicated(subset=["plant_id", "energy_source", "year", "month"]).any()
        )

    def test_synthetic_state_increment_plant_is_excluded(self):
        """Plant 999999 is EIA's imputed state residual, not a plant."""
        _write_raw(
            self.raw,
            2022,
            [
                _row(1001, "SUB", [10] * 12),
                _row(999999, "BIT", [5000] * 12),
            ],
        )
        df = self._curate()
        self.assertEqual(set(df["plant_id"]), {1001})
        self.assertEqual(df["ending_stock_tons"].sum(), 120.0)

    def test_withheld_and_dot_cells_are_dropped_not_zeroed(self):
        """`.` / `W` are withheld, never an empty stockpile."""
        q = [10] * 12
        q[3], q[7] = ".", "W"
        _write_raw(self.raw, 2022, [_row(1001, "SUB", q)])
        df = self._curate()
        self.assertEqual(len(df), 10)
        self.assertNotIn(4, set(df["month"]))
        self.assertNotIn(8, set(df["month"]))
        self.assertTrue((df["ending_stock_tons"] == 10.0).all())

    def test_pre_2020_vintage_without_balancing_authority_column(self):
        """2018/2019 predate the BA column; it is nullable, so the year curates."""
        _write_raw(self.raw, 2018, [_row(1001, "BIT", [7] * 12)], with_ba=False)
        out = curate(raw_root=self.raw)
        self.assertEqual(len(out), 1)
        df = read_clean("coal-stocks", year=2018)
        self.assertEqual(len(df), 12)
        self.assertTrue(pd.isna(df["balancing_authority_code"]).all())

    def test_curate_is_idempotent(self):
        _write_raw(self.raw, 2022, [_row(1001, "SUB", [10] * 12)])
        first = self._curate()
        second = self._curate()
        pd.testing.assert_frame_equal(first, second)
