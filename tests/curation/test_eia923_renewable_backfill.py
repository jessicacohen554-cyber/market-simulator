"""Bundle-side EIA-923 renewable / biomass backfill for incomplete vintages.

The dashboard's per-class ``classFull`` benchmark is built from the bundle's
``eia923.parquet`` (``render_calibration_html``), NOT the reference. The current-
year early monthly survey under-counts every non-thermal class there too — wind /
solar / hydro have no CEMS backfill and biomass is in neither CAMPD nor EIA-930.
``_backfill_renewables_eia930`` sources wind/solar/hydro from the EIA-930 grid
total (the basis the model's grid LP is scored on) and carries biomass from the
prior complete year scaled by the vintage completeness, so every class keeps a
full-year benchmark. These tests pin that logic (synthetic) plus the live CAISO
2025 behaviour against the committed extracts.
"""

import importlib.util
import unittest

import numpy as np
import pandas as pd
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
_spec = importlib.util.spec_from_file_location(
    "rcf_bk", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_MCOLS = [f"m{i:02d}" for i in range(1, 13)]


def _e923_row(year, plant_id, klass, annual, monthly=None):
    monthly = monthly if monthly is not None else [annual / 12.0] * 12
    return {
        "year": np.int16(year),
        "plant_id": plant_id,
        "klass": klass,
        "annual_mwh": float(annual),
        **{c: float(monthly[i]) for i, c in enumerate(_MCOLS)},
    }


def _e930_long(year, series_totals):
    """Build a flat-shaped EIA-930 long frame: each series' annual spread over
    8760 equal hours (so the monthly split is proportional to month length)."""
    rows = []
    for series, annual in series_totals.items():
        per_hour = annual / 8760.0
        for h in range(8760):
            rows.append((year, series, h, per_hour))
    return pd.DataFrame(rows, columns=["year", "series", "hour", "mw"])


class TestReplaceClassTotal(unittest.TestCase):
    def test_drops_rows_and_inserts_one_total(self):
        e923 = pd.DataFrame(
            [
                _e923_row(2025, 10, "wind", 1.0),
                _e923_row(2025, 11, "wind", 2.0),
                _e923_row(2025, 12, "solar", 5.0),
            ]
        )
        out = rcf._replace_class_total(e923, "wind", 2025, 30.0, [2.5] * 12)
        wind = out[out["klass"] == "wind"]
        self.assertEqual(len(wind), 1)  # collapsed to one
        self.assertAlmostEqual(float(wind["annual_mwh"].iloc[0]), 30.0)
        self.assertAlmostEqual(float(wind[_MCOLS].sum(axis=1).iloc[0]), 30.0)
        # other classes untouched
        self.assertAlmostEqual(
            float(out[out["klass"] == "solar"]["annual_mwh"].sum()), 5.0
        )


class TestRenewableBackfill(unittest.TestCase):
    """``_backfill_renewables_eia930`` swaps only the under-counted classes."""

    _MONTHS = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]

    def _row(self, year, plant_id, pm, fc, annual):
        r = {
            "year": year,
            "plant_id": plant_id,
            "prime_mover": pm,
            "fuel_type": fc,
            "chp": "N",
            "netgen_annual_mwh": annual,
        }
        r.update({f"netgen_{m}_mwh": annual / 12.0 for m in self._MONTHS})
        return r

    def _gen(self, year, iso_total, biomass):
        """``generation`` frame for ``year`` and ``year-1``: a wind plant carrying
        the bulk of the ISO total and a biomass (WDS) plant, both in the ISO set.
        The prior year is complete (full ``iso_total``) so the biomass carry has a
        donor; the current year may be truncated."""
        frames = []
        for y, tot, bio in ((year - 1, iso_total, biomass), (year, iso_total, biomass)):
            frames.append(self._row(y, 1, "WT", "WND", tot - bio))
            frames.append(self._row(y, 2, "ST", "WDS", bio))
        return pd.DataFrame(frames)

    def _gen_with_solar(self, year, iso_total, biomass, solar_cur, solar_prior):
        """``generation`` for ``year`` and ``year-1`` carrying a solar plant too.

        The zero-EIA-930 carry-forward needs a prior-year donor for the class, so
        the solar row must exist in BOTH years (unlike :meth:`_gen`).
        """
        frames = []
        for y, sol in ((year - 1, solar_prior), (year, solar_cur)):
            frames.append(self._row(y, 1, "WT", "WND", iso_total - biomass - sol))
            frames.append(self._row(y, 2, "ST", "WDS", biomass))
            frames.append(self._row(y, 3, "PV", "SUN", sol))
        return pd.DataFrame(frames)

    def setUp(self):
        self._orig_ids = rcf._iso_plant_ids
        # Plant 3 (solar) is only present in the _gen_with_solar frames, so
        # widening the set is a no-op for every other test here.
        # spp-49 widened the seam to (iso, year, vintage_union).
        rcf._iso_plant_ids = lambda iso, *_a, **_kw: frozenset({1, 2, 3})

    def tearDown(self):
        rcf._iso_plant_ids = self._orig_ids

    def test_under_counted_renewables_swapped_complete_untouched(self):
        e923 = pd.DataFrame(
            [
                _e923_row(2025, 10, "wind", 4.0e6),  # truncated -> swap
                _e923_row(2025, 11, "solar", 49.0e6),  # above 90% of 50 -> keep
                _e923_row(2025, 12, "hydro", 12.0e6),  # truncated -> swap
                _e923_row(2025, 13, "CC_REGULAR", 37.0e6),  # thermal -> keep
            ]
        )
        e930 = _e930_long(
            2025, {"wind": 20.0e6, "solar": 50.0e6, "hydro": 21.0e6, "net_gen": 200.0e6}
        )
        gen = self._gen(2025, 140.0e6, 1.2e6)  # 140/200 = 70% incomplete
        out = rcf._backfill_renewables_eia930(e923, 2025, "CAISO", gen, e930)
        by = out.groupby("klass")["annual_mwh"].sum()
        self.assertAlmostEqual(by["wind"], 20.0e6, delta=1e4)  # -> EIA-930
        self.assertAlmostEqual(by["solar"], 49.0e6)  # kept
        self.assertAlmostEqual(by["hydro"], 21.0e6, delta=1e4)  # -> EIA-930
        self.assertAlmostEqual(by["CC_REGULAR"], 37.0e6)  # thermal kept

    def test_complete_vintage_renewables_unchanged(self):
        e923 = pd.DataFrame(
            [
                _e923_row(2024, 10, "wind", 19.0e6),  # 95% of 930 -> keep
                _e923_row(2024, 11, "solar", 49.0e6),
            ]
        )
        e930 = _e930_long(2024, {"wind": 20.0e6, "solar": 50.0e6, "net_gen": 200.0e6})
        gen = self._gen(2024, 196.0e6, 4.0e6)  # 98% -> complete
        out = rcf._backfill_renewables_eia930(e923.copy(), 2024, "CAISO", gen, e930)
        by = out.groupby("klass")["annual_mwh"].sum()
        self.assertAlmostEqual(by["wind"], 19.0e6)  # NOT swapped (complete)
        self.assertAlmostEqual(by["solar"], 49.0e6)

    def test_none_e930_is_noop(self):
        e923 = pd.DataFrame([_e923_row(2025, 10, "wind", 4.0e6)])
        out = rcf._backfill_renewables_eia930(
            e923.copy(), 2025, "CAISO", self._gen(2025, 140e6, 1e6), None
        )
        self.assertAlmostEqual(
            float(out[out["klass"] == "wind"]["annual_mwh"].sum()), 4.0e6
        )

    def test_zero_eia930_series_falls_through_to_carry_forward(self):
        """A class with NO EIA-930 authority is carried forward, not skipped.

        The nyiso-106 defect: the swap keys on EIA-930, so a BA reporting the
        class as identically zero (NYIS ``NG: SUN``) made the guard ``continue``
        and left the truncated vintage scoring. Such a class is in biomass's
        position and takes biomass's repair.
        """
        e923 = pd.DataFrame(
            [
                _e923_row(2025, 12, "solar", 1.0e6),  # truncated survey
                _e923_row(2025, 13, "CC_REGULAR", 37.0e6),
            ]
        )
        # No "solar" key -> the EIA-930 series is absent (annual 0.0).
        e930 = _e930_long(2025, {"wind": 20.0e6, "net_gen": 200.0e6})
        gen = self._gen_with_solar(2025, 140.0e6, 1.2e6, 1.0e6, 10.0e6)
        out = rcf._backfill_renewables_eia930(e923, 2025, "NYISO", gen, e930)
        by = out.groupby("klass")["annual_mwh"].sum()
        # completeness 140/200 = 0.70; prior 10.0 x 0.70 = 7.0 TWh > the 1.0 read
        self.assertAlmostEqual(by["solar"], 7.0e6, delta=1e3)
        self.assertAlmostEqual(by["CC_REGULAR"], 37.0e6)  # thermal untouched

    def test_zero_eia930_series_complete_vintage_unchanged(self):
        """The carry-forward is gated on the vintage, so a complete year no-ops."""
        e923 = pd.DataFrame([_e923_row(2024, 12, "solar", 9.0e6)])
        e930 = _e930_long(2024, {"wind": 20.0e6, "net_gen": 200.0e6})
        gen = self._gen_with_solar(2024, 196.0e6, 4.0e6, 9.0e6, 10.0e6)  # 98%
        out = rcf._backfill_renewables_eia930(e923.copy(), 2024, "NYISO", gen, e930)
        self.assertAlmostEqual(
            float(out[out["klass"] == "solar"]["annual_mwh"].sum()), 9.0e6
        )


class TestLiveCaiso2025(unittest.TestCase):
    """Live committed-data check: every CAISO 2025 class gets a full-year value."""

    def test_full_year_per_class_benchmark(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia923 import load_monthly_generation

        generation = load_monthly_generation()
        if 2025 not in set(generation["year"].unique()):
            self.skipTest("no 2025 EIA-923 vintage in this checkout")
        iso, hours = "CAISO", 8760
        ic = get_iso_config(iso)
        pf = rcf._parasitic_factor_map()
        gbc = rcf._fleet_group_by_code(iso, ic, 2025)
        cy = rcf._campd_hourly_frame(2025, iso, pf, hours)
        e930 = rcf._eia930_frame(2025, iso, ic)
        e = rcf._benchmark_eia923_frame(2025, generation, iso, cy, gbc, e930)
        by = e.groupby("klass")["annual_mwh"].sum() / rcf._MWH_PER_TWH
        # The truncated survey read wind 4.2 / hydro 12.4 / biomass 1.2; after
        # backfill every non-thermal class carries a sane full-year benchmark.
        self.assertGreater(by.get("wind", 0.0), 15.0)
        self.assertGreater(by.get("solar", 0.0), 45.0)
        self.assertGreater(by.get("hydro", 0.0), 18.0)
        self.assertGreater(by.get("biomass", 0.0), 2.5)
        # Thermal stays on its full-year CAMPD backfill (CC_REGULAR genuinely
        # ~37-38 TWh in 2025 — confirmed by CEMS, not a truncation artifact).
        self.assertGreater(by.get("CC_REGULAR", 0.0), 35.0)
        self.assertLess(by.get("CC_REGULAR", 0.0), 42.0)


class TestLiveNyiso2025Solar(unittest.TestCase):
    """NYISO solar is the one cell with a zero EIA-930 authority (nyiso-106).

    EIA-930 ``NYIS`` ``NG: SUN`` is identically 0.0 in every hour of every year,
    so the EIA-930 swap can never fire and the 2025 vintage — 8 of 565 plants,
    0.662 TWh against 2.901 in 2024 — used to reach the scorecard intact
    (solar +437 %). The carry-forward must repair it.
    """

    def test_solar_carried_forward_not_left_truncated(self):
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia923 import load_monthly_generation

        generation = load_monthly_generation()
        if 2025 not in set(generation["year"].unique()):
            self.skipTest("no 2025 EIA-923 vintage in this checkout")
        e930 = rcf._eia930_frame(2025, "NYISO", get_iso_config("NYISO"))
        raw = rcf._eia923_frame(2025, generation, "NYISO")
        out = rcf._backfill_renewables_eia930(
            raw.copy(), 2025, "NYISO", generation, e930
        )
        by = out.groupby("klass")["annual_mwh"].sum() / rcf._MWH_PER_TWH
        # The truncated survey reads 0.66 TWh; 2024 was 2.90 and the vintage is
        # ~88.5% complete, so the repair lands ~2.57 TWh.
        self.assertGreater(by.get("solar", 0.0), 2.0)
        self.assertLess(by.get("solar", 0.0), 3.0)

    def test_complete_vintages_are_byte_identical(self):
        """2023 / 2024 are complete NYISO vintages — the repair must not move."""
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia923 import load_monthly_generation

        generation = load_monthly_generation()
        ic = get_iso_config("NYISO")
        for year in (2023, 2024):
            if year not in set(generation["year"].unique()):
                self.skipTest(f"no {year} EIA-923 vintage in this checkout")
            raw = rcf._eia923_frame(year, generation, "NYISO")
            out = rcf._backfill_renewables_eia930(
                raw.copy(),
                year,
                "NYISO",
                generation,
                rcf._eia930_frame(year, "NYISO", ic),
            )
            before = float(raw[raw["klass"] == "solar"]["annual_mwh"].sum())
            after = float(out[out["klass"] == "solar"]["annual_mwh"].sum())
            self.assertAlmostEqual(before, after, places=6, msg=f"{year} moved")


class TestPerYearChp(unittest.TestCase):
    """``_chp_by_plant`` reads the year's own EIA-860 CHP vintage when present."""

    def test_year_selects_vintage_falls_back_to_snapshot(self):
        from market_sim.config.paths import EIA_860_DIR, PROCESSED_DIR
        from market_sim.data.chp import _chp_by_plant

        if not (PROCESSED_DIR / "eia860_chp_by_year.parquet").exists():
            self.skipTest("no per-year CHP lookup in this checkout")
        years = {y: _chp_by_plant(EIA_860_DIR, y) for y in (2023, 2024, 2025)}
        # each year resolves a non-empty, CHP-flagged plant set
        for y, s in years.items():
            self.assertGreater(len(s), 0, f"empty CHP map for {y}")
            self.assertGreater(int((s == "Y").sum()), 0)
        # the vintages are not all identical (cogen status / fleet changes)
        self.assertNotEqual(len(years[2023]), len(years[2025]))
        # year=None falls back to the latest committed snapshot
        snap = _chp_by_plant(EIA_860_DIR, None)
        self.assertGreater(len(snap), 0)


if __name__ == "__main__":
    unittest.main()
