"""Tests for the ``coal-receipts`` curation (EIA-923 Page 5 Fuel Receipts).

Trivial case first (one plant, one lot), then the aggregation, sentinel and
vintage behaviours the real EIA record actually exhibits — and last the rule-13
read seam, which is the one thing about this datatype that can go wrong
silently.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.data.coal_receipts import (  # noqa: E402
    CONTRACT_PURCHASE_TYPES,
    footprint_receipts,
    prior_years_delivery_rate,
)
from scripts.data.curate_coal_receipts import curate  # noqa: E402
from scripts.lib.clean_io import read_clean  # noqa: E402
from tests.helpers.base import CleanDirTestCase  # noqa: E402

_COLS = [
    "YEAR",
    "MONTH",
    "Plant Id",
    "Plant Name",
    "Plant State",
    "Purchase Type",
    "ENERGY_SOURCE",
    "FUEL_GROUP",
    "QUANTITY",
    "Average Heat Content",
    "FUEL_COST",
    "Primary Transportation Mode",
]


def _lot(
    plant_id,
    month=1,
    quantity=100,
    heat=18.0,
    cost=200.0,
    fuel="SUB",
    purchase="C",
    mode="RR",
    year=2022,
):
    return {
        "YEAR": year,
        "MONTH": month,
        "Plant Id": plant_id,
        "Plant Name": f"Plant {plant_id}",
        "Plant State": "IL",
        "Purchase Type": purchase,
        "ENERGY_SOURCE": fuel,
        "FUEL_GROUP": "Coal",
        "QUANTITY": quantity,
        "Average Heat Content": heat,
        "FUEL_COST": cost,
        "Primary Transportation Mode": mode,
    }


def _write_raw(raw_root: Path, year: int, rows, with_ba=True):
    d = raw_root / "coal-receipts"
    d.mkdir(parents=True, exist_ok=True)
    cols = list(_COLS)
    if with_ba:
        cols += ["Balancing Authority Code"]
        for r in rows:
            r.setdefault("Balancing Authority Code", "MISO")
    path = d / f"coal_receipts_{year}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


class CurateCoalReceiptsTest(CleanDirTestCase):
    def setUp(self):
        super().setUp()
        self.raw = self.tmp_path / "raw"

    def _curate(self, year=2022):
        out = curate(raw_root=self.raw)
        self.assertEqual(len(out), 1)
        return read_clean("coal-receipts", year=year)

    def test_one_plant_one_lot(self):
        """Trivial case: a single receipt lot survives as a single tidy row."""
        _write_raw(self.raw, 2022, [_lot(1001)])
        df = self._curate()
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row["plant_id"], 1001)
        self.assertEqual(row["energy_source"], "SUB")
        self.assertEqual(row["month"], 1)
        self.assertEqual(row["purchase_type"], "C")
        self.assertEqual(row["primary_transportation_mode"], "RR")
        self.assertEqual(row["quantity_tons"], 100.0)
        self.assertAlmostEqual(row["heat_content_mmbtu_per_ton"], 18.0)

    def test_lots_sum_and_heat_content_is_quantity_weighted(self):
        """Two mines into one plant-month: tons add, heat content weights."""
        _write_raw(
            self.raw,
            2022,
            [
                _lot(1001, quantity=100, heat=18.0),
                _lot(1001, quantity=300, heat=22.0),
            ],
        )
        df = self._curate()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["quantity_tons"], 400.0)
        # (100*18 + 300*22) / 400 = 21.0 — not the unweighted 20.0.
        self.assertAlmostEqual(df.iloc[0]["heat_content_mmbtu_per_ton"], 21.0)

    def test_purchase_type_and_mode_stay_separate_keys(self):
        """Contract vs spot, and rail vs truck, must not be summed together."""
        _write_raw(
            self.raw,
            2022,
            [
                _lot(1001, quantity=100, purchase="C", mode="RR"),
                _lot(1001, quantity=50, purchase="S", mode="RR"),
                _lot(1001, quantity=20, purchase="C", mode="TR"),
            ],
        )
        df = self._curate()
        self.assertEqual(len(df), 3)
        self.assertFalse(
            df.duplicated(
                subset=[
                    "plant_id",
                    "energy_source",
                    "year",
                    "month",
                    "purchase_type",
                    "primary_transportation_mode",
                ]
            ).any()
        )
        contracted = df[df.purchase_type.isin(CONTRACT_PURCHASE_TYPES)]
        self.assertEqual(contracted["quantity_tons"].sum(), 120.0)

    def test_synthetic_state_increment_plant_is_excluded(self):
        """Plant 999999 is EIA's imputed state residual, not a plant."""
        _write_raw(self.raw, 2022, [_lot(1001), _lot(999999, quantity=5000)])
        df = self._curate()
        self.assertEqual(set(df["plant_id"]), {1001})
        self.assertEqual(df["quantity_tons"].sum(), 100.0)

    def test_withheld_quantity_dropped_but_withheld_cost_keeps_the_tons(self):
        """`.`/`W` are withheld. A withheld tonnage drops; a withheld cost does not."""
        _write_raw(
            self.raw,
            2022,
            [
                _lot(1001, month=1, quantity="."),
                _lot(1001, month=2, quantity=80, cost="W"),
                _lot(1001, month=3, quantity=60, heat="."),
            ],
        )
        df = self._curate()
        self.assertEqual(sorted(df["month"]), [2, 3])
        feb = df[df.month == 2].iloc[0]
        self.assertEqual(feb["quantity_tons"], 80.0)
        self.assertTrue(pd.isna(feb["fuel_cost_cents_per_mmbtu"]))
        mar = df[df.month == 3].iloc[0]
        self.assertEqual(mar["quantity_tons"], 60.0)
        self.assertTrue(pd.isna(mar["heat_content_mmbtu_per_ton"]))

    def test_blank_transport_mode_becomes_unk_not_dropped(self):
        """A blank provenance field is not a reason to lose a real delivery."""
        _write_raw(self.raw, 2022, [_lot(1001, mode="")])
        df = self._curate()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["primary_transportation_mode"], "UNK")
        self.assertEqual(df.iloc[0]["quantity_tons"], 100.0)

    def test_pre_2020_vintage_without_balancing_authority_column(self):
        """2018/2019 predate the BA column; it is nullable, so the year curates."""
        _write_raw(self.raw, 2018, [_lot(1001, year=2018)], with_ba=False)
        self.assertEqual(len(curate(raw_root=self.raw)), 1)
        df = read_clean("coal-receipts", year=2018)
        self.assertEqual(len(df), 1)
        self.assertTrue(pd.isna(df["balancing_authority_code"]).all())

    def test_curate_is_idempotent(self):
        _write_raw(self.raw, 2022, [_lot(1001)])
        pd.testing.assert_frame_equal(self._curate(), self._curate())


class CoalReceiptsReaderTest(CleanDirTestCase):
    """The rule-13 read seam: the admissible rate reads only prior years."""

    def setUp(self):
        super().setUp()
        self.raw = self.tmp_path / "raw"
        # 2020: 100 t @ 20 MMBtu/t.  2021: 300 t @ 24.  2022 (the TARGET year):
        # a deliberately absurd 9,000 t, so any read that touches it is obvious.
        for year, tons, heat in (
            (2020, 100, 20.0),
            (2021, 300, 24.0),
            (2022, 9000, 30.0),
        ):
            _write_raw(
                self.raw,
                year,
                [_lot(1001, quantity=tons, heat=heat, year=year)],
            )
        curate(raw_root=self.raw)

    def test_footprint_join_is_read_time_and_scoped_to_the_caller(self):
        self.assertTrue(footprint_receipts([9999]).empty)
        df = footprint_receipts([1001], years=[2021])
        self.assertEqual(df.iloc[0]["quantity_tons"], 300.0)

    def test_prior_years_rate_never_reads_the_target_year(self):
        rate = prior_years_delivery_rate([1001], 2022)
        self.assertEqual(rate.source_years, (2020, 2021))
        self.assertEqual(rate.tons_per_year, 200.0)  # mean(100, 300)
        # Quantity-weighted over the SOURCE years: (100*20 + 300*24)/400 = 23.0.
        self.assertAlmostEqual(rate.mmbtu_per_ton, 23.0)
        self.assertAlmostEqual(rate.mmbtu_per_year, 4600.0)

    def test_prior_years_rate_returns_none_when_no_source_year_is_curated(self):
        self.assertIsNone(prior_years_delivery_rate([1001], 2019))

    def test_purchase_type_filter_reaches_the_rate(self):
        _write_raw(
            self.raw,
            2021,
            [
                _lot(1001, quantity=300, heat=24.0, purchase="C", year=2021),
                _lot(1001, quantity=700, heat=24.0, purchase="S", year=2021),
            ],
        )
        curate(raw_root=self.raw, years=[2021])
        every = prior_years_delivery_rate([1001], 2022)
        contracted = prior_years_delivery_rate(
            [1001], 2022, purchase_types=CONTRACT_PURCHASE_TYPES
        )
        self.assertEqual(every.tons_per_year, 550.0)  # mean(100, 1000)
        self.assertEqual(contracted.tons_per_year, 200.0)  # mean(100, 300)
        self.assertEqual(contracted.purchase_types, CONTRACT_PURCHASE_TYPES)
