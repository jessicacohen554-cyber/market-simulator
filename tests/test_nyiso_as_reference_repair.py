"""Tests for the NYISO AS calibration-reference repair (nyiso-166, rule 14 [R-ACCURATE]).

``scripts/data/process_nyiso_as.py::build_reference`` writes
``data/raw/_validation-source/actual_as_reserve_NYISO.parquet`` — the measured
RT reserve-adder reference every NYISO reserve diagnostic validates against. It
carried two independent defects in every column and every year, both repaired by
nyiso-166 (``docs/FINDING-nyiso166-as-reference-repair-2026-08-31.md``):

* **Cascade summed, not maxed.** NYISO's three posted operating-reserve
  products NEST by duration, so their posted prices are CUMULATIVE:
  ``spin_10 >= nonsync_10 >= op_30``. A reserve MW earns the largest of the
  three, never their sum; summing triple-counted one shadow price wherever the
  three were equal (82-84 % of rows).
* **Naive positional clock.** The published ``Time Stamp`` is naive PREVAILING
  Eastern; the model's NYISO clock is fixed standard time ``Etc/GMT+5``.
  Mapping the former positionally onto the latter mis-indexes the whole DST
  season — 65.2 % of the year, and where NYISO's price tail sits.

These tests pin both invariants. The synthetic-CSV tests need no committed data
and are the standing regression guard; the parity tests against
``scripts/probes/nyiso164_nyca_shortage_check.py`` — the independent measurement
of record, which reads the raw CSVs directly — skip when the NYISO data profile
is not hydrated. Nothing here solves, scores, or touches the network.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import process_nyiso_as as pna  # noqa: E402
from scripts.data.derive_actual_lmp import (  # noqa: E402
    _EASTERN_TZ,
    _STD_TZ,
    _std_hour_index,
)

AS_DIR = REPO / "data/raw/NYISO-AS"
REF = REPO / "data/raw/_validation-source/actual_as_reserve_NYISO.parquet"
LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
YEARS = (2023, 2024, 2025)
TAIL_THRESHOLD = 300.0  # the C3c criterion's own, RT hourly

# Non-leap month-start hours — ONLY to reconstruct the retired naive positional
# map, so the test can prove the two clocks genuinely disagree. Never used to
# index anything.
_NAIVE_MONTH_START = list(
    np.cumsum([0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)])
)

_HAVE_CSVS = all((AS_DIR / f"NYISO_as_rt_{y}.csv").exists() for y in YEARS)
_HAVE_REF = REF.exists() and LMP.exists()


def _naive_positional_hour(ts: pd.Series) -> np.ndarray:
    """The RETIRED map: naive prevailing wall-clock -> 8760 index, positionally."""
    return (
        np.array(_NAIVE_MONTH_START)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )


def _std_hour(ts: pd.Series, year: int) -> np.ndarray:
    """The repaired map: localize to prevailing Eastern, index on Etc/GMT+5."""
    aware = pd.DatetimeIndex(ts).tz_localize(
        _EASTERN_TZ, ambiguous=True, nonexistent="shift_forward"
    )
    return _std_hour_index(aware, year, _STD_TZ["NYISO"])


def _synthetic_csv(
    path: Path, rows: list[tuple[str, str, float, float, float]]
) -> None:
    """Write a per-year NYISO_as_rt CSV in the shape ``process()`` emits."""
    pd.DataFrame(
        rows, columns=["Time Stamp", "Name", "spin_10", "nonsync_10", "op_30"]
    ).to_csv(path, index=False)


class TestCascadeAggregation(unittest.TestCase):
    """The cleared price is the cascade MAX, never the sum of the three products."""

    def test_builder_takes_the_max_not_the_sum(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # One WEST hour, mid-winter (no DST offset), all three equal at $100:
            # the summed reading would be $300, the cleared price is $100.
            _synthetic_csv(
                tmp / "NYISO_as_rt_2023.csv",
                [("2023-01-01 00:00:00", "WEST", 100.0, 100.0, 100.0)],
            )
            ref = _build_in(tmp)
        row = ref[(ref.year == 2023) & (ref.hour == 0)]
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(float(row.nyca_reserve_adder.iloc[0]), 100.0, places=3)

    def test_builder_max_holds_when_the_cascade_is_strict(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            _synthetic_csv(
                tmp / "NYISO_as_rt_2023.csv",
                [("2023-01-01 00:00:00", "WEST", 90.0, 50.0, 25.0)],
            )
            ref = _build_in(tmp)
        val = float(
            ref[(ref.year == 2023) & (ref.hour == 0)].nyca_reserve_adder.iloc[0]
        )
        self.assertAlmostEqual(val, 90.0, places=3)  # spin_10, not 165.0

    @unittest.skipUnless(_HAVE_CSVS, "NYISO data profile not hydrated")
    def test_published_cascade_is_monotone_in_every_row(self):
        """spin_10 >= nonsync_10 >= op_30 — the invariant the MAX rests on.

        If this ever fails the products are no longer cumulative and the
        aggregation must be re-derived from the posting convention, not patched.
        """
        for year in YEARS:
            df = pd.read_csv(AS_DIR / f"NYISO_as_rt_{year}.csv")
            spin = df.spin_10.to_numpy(float)
            nons = df.nonsync_10.to_numpy(float)
            op30 = df.op_30.to_numpy(float)
            mono = (spin >= nons - 1e-9) & (nons >= op30 - 1e-9)
            self.assertTrue(
                mono.all(),
                f"{year}: cascade non-monotone in {int((~mono).sum())} of {len(df)} rows",
            )
            # And the max is exactly spin_10 — the equivalence the repair claims.
            self.assertTrue(
                np.allclose(
                    df[list(pna._CASCADE_PRODUCTS)].max(axis=1).to_numpy(float), spin
                )
            )


class TestStandardTimeClock(unittest.TestCase):
    """The reference rides the model's fixed standard-time 8760 clock."""

    def test_dst_hour_lands_one_hour_earlier_than_the_naive_map(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            # 2023-09-05 17:00 EDT == 16:00 EST. The retired positional map put
            # this at the 17:00 slot; the std clock puts it at 16:00.
            _synthetic_csv(
                tmp / "NYISO_as_rt_2023.csv",
                [("2023-09-05 17:00:00", "WEST", 661.77, 661.77, 661.77)],
            )
            ref = _build_in(tmp)
        ts = pd.Series(pd.to_datetime(["2023-09-05 17:00:00"]))
        naive = int(_naive_positional_hour(ts)[0])
        std = int(_std_hour(ts, 2023)[0])
        self.assertEqual(std, naive - 1)
        y = ref[ref.year == 2023].set_index("hour").nyca_reserve_adder
        self.assertAlmostEqual(float(y.loc[std]), 661.77, places=2)
        self.assertTrue(np.isnan(float(y.loc[naive])))

    def test_winter_hour_is_unmoved(self):
        ts = pd.Series(pd.to_datetime(["2023-01-15 08:00:00"]))
        self.assertEqual(
            int(_std_hour(ts, 2023)[0]), int(_naive_positional_hour(ts)[0])
        )

    @unittest.skipUnless(_HAVE_CSVS, "NYISO data profile not hydrated")
    def test_the_two_clocks_disagree_across_the_dst_season(self):
        """~65 % of the year — the magnitude that makes the naive map a defect."""
        for year in YEARS:
            df = pd.read_csv(AS_DIR / f"NYISO_as_rt_{year}.csv")
            df = df[df.Name == "WEST"]
            ts = pd.to_datetime(df["Time Stamp"])
            keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
            ts = ts[keep]
            std = _std_hour(ts, year)
            naive = _naive_positional_hour(ts)
            share = float(np.mean(std != naive))
            self.assertGreater(share, 0.6, f"{year}: only {share:.1%} of hours differ")
            # The std index is injective over the year it keeps.
            kept = std[std >= 0]
            self.assertEqual(len(set(kept.tolist())), len(kept))


@unittest.skipUnless(_HAVE_CSVS and _HAVE_REF, "NYISO data profile not hydrated")
class TestParityWithMeasurementOfRecord(unittest.TestCase):
    """The committed reference reproduces nyiso-164, the measurement of record.

    ``scripts/probes/nyiso164_nyca_shortage_check.py`` measures the same
    quantity straight from the raw CSVs by a different construction (the
    minimum across zones A-E rather than WEST alone). Agreement hour by hour is
    the repair's acceptance test; a mismatch means the reference is wrong, not
    the probe.
    """

    @classmethod
    def setUpClass(cls):
        from scripts.probes import nyiso164_nyca_shortage_check as probe

        cls.probe = probe
        cls.ref = pd.read_parquet(REF)
        cls.lmp = pd.read_parquet(LMP)

    def test_hourly_parity_in_both_tiers(self):
        for year in YEARS:
            dec = self.probe.nyca_and_local(self.probe.load_as_rt(year)).reindex(
                np.arange(8760)
            )
            got = self.ref[self.ref.year == year].sort_values("hour")
            for col, tier in (
                ("nyca_reserve_adder", "nyca_max"),
                ("nyc_reserve_adder", "nyc_max"),
            ):
                a = dec[tier].to_numpy(float)
                b = got[col].to_numpy(float)
                self.assertTrue(
                    (np.isnan(a) == np.isnan(b)).all(),
                    f"{year} {col}: coverage differs from the probe",
                )
                m = ~np.isnan(a)
                # atol carries the reference's float32 storage; rtol is float32 eps.
                self.assertTrue(
                    np.allclose(a[m], b[m], rtol=1e-6, atol=1e-3),
                    f"{year} {col}: max |diff| {np.abs(a[m] - b[m]).max():.2e}",
                )

    def test_nyca_tier_in_the_price_tail(self):
        """The published tail-hour NYCA tier, per year (nyiso-164 sec 'reality')."""
        expected = {
            2023: (306.74, 248.22, 761.73, 10),
            2024: (254.62, 239.96, 552.89, 13),
            2025: (393.31, 403.74, 1101.85, 42),
        }
        ceiling_hits = 0
        for year, (mean, median, mx, n_tail) in expected.items():
            rt = self.lmp[self.lmp.year == year].sort_values("hour").rt.to_numpy(float)
            tail = np.flatnonzero(rt > TAIL_THRESHOLD)
            self.assertEqual(len(tail), n_tail, f"{year}: tail-hour count moved")
            v = (
                self.ref[self.ref.year == year]
                .set_index("hour")["nyca_reserve_adder"]
                .reindex(tail)
                .to_numpy(float)
            )
            self.assertAlmostEqual(float(np.nanmean(v)), mean, delta=0.01)
            self.assertAlmostEqual(float(np.nanmedian(v)), median, delta=0.01)
            self.assertAlmostEqual(float(np.nanmax(v)), mx, delta=0.01)
            ceiling_hits += int(np.nansum(v > rt[tail]))
        # The ceiling test: the NYCA-tier reserve price never exceeds the
        # concurrent LMP in any of the 65 tail hours, so it is the opportunity
        # cost of scarce ENERGY, not RCPF demand-curve shortage. The summed
        # reference broke exactly this test.
        self.assertEqual(ceiling_hits, 0)

    def test_model_zone_alias_matches_its_legacy_alias(self):
        same = self.ref.nyca_reserve_adder.equals(self.ref.reserve_Upstate_West)
        self.assertTrue(same)
        self.assertTrue(self.ref.nyc_reserve_adder.equals(self.ref.reserve_NYC))


def _build_in(tmp: Path) -> pd.DataFrame:
    """Run ``build_reference`` against a temp AS dir and return the parquet."""
    out_dir = tmp / "out"
    out_dir.mkdir()
    as_dir, cal_dir = pna.AS_DIR, pna.CAL_DIR
    pna.AS_DIR, pna.CAL_DIR = tmp, out_dir
    try:
        path = pna.build_reference([2023])
    finally:
        pna.AS_DIR, pna.CAL_DIR = as_dir, cal_dir
    assert path is not None
    return pd.read_parquet(path)


if __name__ == "__main__":
    unittest.main()
