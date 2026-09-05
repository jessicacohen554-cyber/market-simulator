"""Commercial-operation-date (COD) vintage ramp — the single COD mechanism.

Covers :mod:`market_sim.data.cod_ramp` (the pure month-mask helper, the COD
resolver, and the EIA-860 plant-code map) and its application inside
:func:`market_sim.data.fleet.generators_to_fleet_arrays`: month-precise online/
retirement masking, the ERCOT CAMPD-bin coverage path (a bin gets its COD from
the plant-code map), and the must-run-floor (min_gen) zeroing in offline months.
"""

import unittest
from unittest import mock

import numpy as np
import pandas as pd
import pytest

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.cod_ramp import (
    COD_FALLBACK_MONTH,
    _RETIRED_WINDOW_NAME,
    _cod_work_frame,
    _load_cod_map,
    _reduce_cod_groups,
    _registry_year_built,
    class_cod_coverage,
    effective_cod,
    load_cod_map,
    log_class_cod_coverage,
    monthly_online_mask,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from tests.helpers.base import requires_raw


class TestMonthlyOnlineMask(unittest.TestCase):
    """The pure ``(12,)`` online mask for one unit in one run year."""

    def test_built_before_run_year_is_all_online(self):
        m = monthly_online_mask(2018, 6, None, None, 2023)
        self.assertTrue(m.all())

    def test_built_after_run_year_is_all_offline(self):
        m = monthly_online_mask(2024, 1, None, None, 2023)
        self.assertFalse(m.any())

    def test_built_in_run_year_online_from_month(self):
        # September COD -> offline Jan-Aug, online Sep-Dec.
        m = monthly_online_mask(2023, 9, None, None, 2023)
        self.assertFalse(m[:8].any())
        self.assertTrue(m[8:].all())

    def test_retired_before_run_year_is_all_offline(self):
        m = monthly_online_mask(2000, 1, 2022, 12, 2023)
        self.assertFalse(m.any())

    def test_retired_in_run_year_online_through_month(self):
        # March retirement -> online Jan-Mar, offline Apr-Dec.
        m = monthly_online_mask(2000, 1, 2023, 3, 2023)
        self.assertTrue(m[:3].all())
        self.assertFalse(m[3:].any())

    def test_unknown_online_year_is_all_online(self):
        m = monthly_online_mask(None, 1, None, None, 2023)
        self.assertTrue(m.all())

    def test_missing_retirement_month_retires_end_of_year(self):
        # ry == run_year with no month -> online all twelve months.
        m = monthly_online_mask(2000, 1, 2023, None, 2023)
        self.assertTrue(m.all())


class TestEffectiveCod(unittest.TestCase):
    """Resolving a generator's COD: plant-code map wins, own attrs fall back."""

    def test_plant_in_map_overrides_own_attrs(self):
        cod_map = {7: (2024, 9, None, None)}
        # The gen claims 2010, but the curated map says built Sept 2024.
        self.assertEqual(
            effective_cod(7, 2010, 1, None, None, cod_map),
            (2024, 9, None, None),
        )

    def test_plant_absent_from_map_uses_own_attrs(self):
        self.assertEqual(
            effective_cod(7, 2010, 4, 2030, 6, {}),
            (2010, 4, 2030, 6),
        )

    def test_sentinel_online_year_is_unknown(self):
        # online_year == 2000 default sentinel -> vintage unknown (None).
        oy, om, ry, rm = effective_cod(7, 2000, 1, None, None, {})
        self.assertIsNone(oy)

    def test_zero_plant_code_never_hits_map(self):
        cod_map = {0: (2024, 9, None, None)}  # plant_code 0 is "no plant"
        self.assertEqual(
            effective_cod(0, 2015, 1, None, None, cod_map),
            (2015, 1, None, None),
        )

    def test_own_per_unit_retirement_overrides_plant_collapse(self):
        # The plant map collapses heterogeneous unit retirements to the LATEST
        # (2024-04). A generator carrying its OWN earlier retirement (2023-08)
        # must age out on its true date — keeping the online date from the map.
        cod_map = {3122: (1972, 5, 2024, 4)}
        self.assertEqual(
            effective_cod(3122, 1969, 8, 2023, 8, cod_map),
            (1972, 5, 2023, 8),
        )

    def test_no_own_retirement_keeps_plant_map_record(self):
        # ERCOT CAMPD bins carry no retirement -> the plant-map record is kept
        # verbatim (the online-date contract for build-date-less bins).
        cod_map = {3122: (1972, 5, 2024, 4)}
        self.assertEqual(
            effective_cod(3122, 2010, 1, None, None, cod_map),
            (1972, 5, 2024, 4),
        )


class TestLoadCodMap(unittest.TestCase):
    """The EIA-860 plant-code COD map (integration: reads the committed file)."""

    def test_map_is_plant_keyed_with_valid_entries(self):
        cod_map = load_cod_map()
        self.assertGreater(len(cod_map), 100)
        # Spot-check structure on a handful of entries.
        for code, entry in list(cod_map.items())[:50]:
            self.assertIsInstance(code, int)
            oy, om, ry, rm = entry
            self.assertGreaterEqual(om, 1)
            self.assertLessEqual(om, 12)
            self.assertGreaterEqual(oy, 1900)
            if ry is not None:
                self.assertGreaterEqual(ry, oy)

    def test_fallback_month_is_mid_year(self):
        # Documented neutral default for year-only (registry-only) plants.
        self.assertEqual(COD_FALLBACK_MONTH, 7)

    def test_within_window_retiree_aged_out(self):
        """A whole-plant mid-window exit is in the map with its real exit date.

        Mystic (plant 1588, a ~1.4 GW CC that ran through 2023 and retired in
        mid-2024) is absent from the single recent operable vintage; the COD
        map unions it from the within-window retiree parquet so the ramp can
        age it out. Online through 2023, gone after its 2024 retirement month.
        """
        cod_map = load_cod_map()
        self.assertIn(1588, cod_map)
        oy, om, ry, rm = cod_map[1588]
        self.assertLess(oy, 2023)  # online well before the window
        self.assertEqual(ry, 2024)
        self.assertIn(rm, (4, 5, 6))  # EIA-860 records June 2024
        self.assertEqual(monthly_online_mask(oy, om, ry, rm, 2023).sum(), 12)
        masked_2024 = monthly_online_mask(oy, om, ry, rm, 2024).sum()
        self.assertGreater(masked_2024, 0)
        self.assertLessEqual(masked_2024, 6)
        self.assertEqual(monthly_online_mask(oy, om, ry, rm, 2025).sum(), 0)


class TestCodRampInFleetArrays(unittest.TestCase):
    """End-to-end masking inside generators_to_fleet_arrays."""

    # 1-based month -> cumulative hour boundary for a 2023 non-leap year.
    _starts = np.cumsum(
        [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)]
    )

    def _coal_gen(self, **kw) -> Generator:
        base = dict(
            unit_id="c1",
            name="Test Coal",
            zone="North",
            fuel_type="coal",
            pmax_mw=500.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            eford=0.05,
        )
        base.update(kw)
        return Generator(**base)

    def _fa(self, enabled: bool, cod_map=None, mode="backcast", **gen_kw):
        cfg = ScenarioConfig(
            mode=mode,
            weather_year=2024,
            cod_ramp_enabled=enabled,
        )
        # Patch the EIA-860 map so the unit tests are hermetic and fast; the
        # individual coal gens carry plant_code 0, so they fall back to their
        # own online_year/month regardless of the (default empty) map.
        with mock.patch(
            "market_sim.data.fleet.load_cod_map", return_value=cod_map or {}
        ):
            return generators_to_fleet_arrays(
                [self._coal_gen(**gen_kw)],
                ["North"],
                config=cfg,
                year=2024,
            )

    def test_disabled_flag_ignores_midyear_online(self):
        """With cod_ramp_enabled off a mid-year COD is ignored (flat)."""
        fa = self._fa(False, online_year=2024, online_month=6)
        np.testing.assert_allclose(fa.availability[0], 1.0 - 0.05)

    def test_forecast_mode_does_not_ramp(self):
        """Forecast weather_year is not a calendar year -> no COD ramp."""
        fa = self._fa(True, mode="forecast", online_year=2024, online_month=6)
        np.testing.assert_allclose(fa.availability[0], 1.0 - 0.05)

    def test_midyear_cod_masks_pre_online_months(self):
        """A June COD zeros Jan-May and leaves Jun-Dec at the baseline."""
        off = self._fa(False, online_year=2024, online_month=6)
        on = self._fa(True, online_year=2024, online_month=6)
        jun = self._starts[5]  # first June hour
        self.assertEqual(on.availability[0, :jun].max(), 0.0)
        np.testing.assert_allclose(on.availability[0, jun:], off.availability[0, jun:])

    def test_midyear_retirement_masks_post_months(self):
        """A March retirement keeps Jan-Mar and zeros Apr-Dec."""
        off = self._fa(False, online_year=2000)
        on = self._fa(
            True,
            online_year=2000,
            retirement_year=2024,
            retirement_month=3,
        )
        apr = self._starts[3]  # first April hour
        np.testing.assert_allclose(on.availability[0, :apr], off.availability[0, :apr])
        self.assertEqual(on.availability[0, apr:].max(), 0.0)

    def test_full_year_unit_unaffected(self):
        """A unit online before the year with no retirement is unchanged."""
        off = self._fa(False, online_year=2010)
        on = self._fa(True, online_year=2010)
        np.testing.assert_allclose(on.availability[0], off.availability[0])

    def test_not_yet_built_unit_fully_offline(self):
        """A unit whose COD year is after the sim year is offline all year."""
        on = self._fa(True, online_year=2025, online_month=1)
        self.assertEqual(on.availability[0].max(), 0.0)

    def test_campd_bin_ramped_via_plant_code_map(self):
        """A CAMPD bin (no build date of its own) is ramped by the map COD.

        The bin claims online_year 2010 (registry vintage) but the EIA-860
        plant-code map says the plant came online Sept 2024 -> the August
        scarcity hours must see it offline.
        """
        cod_map = {4242: (2024, 9, None, None)}
        on = self._fa(
            True,
            cod_map=cod_map,
            is_campd_bin=True,
            plant_code=4242,
            plant_group="CC_REGULAR",
            online_year=2010,
            online_month=1,
        )
        jun = self._starts[5]
        self.assertEqual(on.availability[0, :jun].max(), 0.0)
        self.assertGreater(on.availability[0, jun:].max(), 0.0)

    def test_min_gen_zeroed_in_offline_months(self):
        """The hard must-run floor cannot force a not-yet-built unit to run."""
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2024,
            cod_ramp_enabled=True,
        )
        gen = Generator(
            unit_id="s1",
            name="ST",
            zone="North",
            fuel_type="gas_st",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=11.0,
            eford=0.05,
            plant_group="ST_GAS",
            online_year=2024,
            online_month=8,
            # A flat grid-steam must-run floor (90 MW all year) stands in for any
            # hard min-gen source; the COD ramp must still zero it before COD.
            chp_grid_pmin_mw=90.0,
        )
        with mock.patch("market_sim.data.fleet.load_cod_map", return_value={}):
            fa = generators_to_fleet_arrays(
                [gen],
                ["North"],
                config=cfg,
                year=2024,
                load_shape=np.ones(8760) * 1000.0,
            )
        # The 90 MW floor would otherwise bind in July; the unit is not online
        # until August, so the COD ramp must zero July's floor.
        jul = self._starts[6]
        aug = self._starts[7]
        self.assertIsNotNone(fa.min_gen)
        self.assertEqual(fa.min_gen[0, jul:aug].max(), 0.0)


class TestEia860VintageSelection(unittest.TestCase):
    """Year-matched EIA-860 vintage switch (config.eia860_vintage_year)."""

    def tearDown(self):
        from market_sim.config.paths import set_eia860_vintage

        set_eia860_vintage(None)  # never leak a vintage into other tests

    def test_switch_redirects_and_cache_rekeys(self):
        from market_sim.config.paths import (
            EIA_860_DIR,
            active_eia860_dir,
            set_eia860_vintage,
        )

        v2023 = EIA_860_DIR / "vintage_2023"
        if not v2023.is_dir():
            self.skipTest("vintage_2023 EIA-860 directory not committed")
        set_eia860_vintage(None)
        default_map = load_cod_map()
        set_eia860_vintage(2023)
        self.assertEqual(active_eia860_dir(), v2023)
        v_map = load_cod_map()
        # A real, earlier vintage has strictly fewer plants than the 2025ER
        # snapshot — proves the cache re-keyed on the directory rather than
        # serving the first-cached map.
        self.assertLess(len(v_map), len(default_map))

    def test_missing_vintage_falls_back_to_default(self):
        from market_sim.config.paths import (
            EIA_860_DIR,
            active_eia860_dir,
            set_eia860_vintage,
        )

        set_eia860_vintage(1999)  # no vintage_1999/ directory exists
        self.assertEqual(active_eia860_dir(), EIA_860_DIR)


class TestNeisoWithinWindowRetireeFleetPath(unittest.TestCase):
    """The NEISO backcast fleet ages a mid-window plant exit out by month.

    Integration over the real loader + COD ramp: builds the NEISO fleet the way
    the calibration runner does (operable snapshot + within-window retirees),
    then checks the ramp masks Mystic (plant 1588) on through 2023, partway
    through 2024, and off in 2025 -- and that the modeled CC_REGULAR plant set
    differs by year (not the identical post-retirement set every year).
    """

    @classmethod
    def setUpClass(cls):
        import numpy as np

        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.fleet import (
            load_fleet_from_csv,
            load_retired_within_window,
        )

        cls.np = np
        cls.iso_config = get_iso_config("NEISO")
        cls.zone_names = [z.name for z in cls.iso_config.zones]
        retirees = load_retired_within_window("NEISO", cls.iso_config)
        cls.fleet = load_fleet_from_csv("NEISO", cls.iso_config) + retirees
        cls.has_mystic = any(int(g.plant_code) == 1588 for g in retirees)
        # 1-based month -> cumulative hour boundary (non-leap year).
        cls.month_start = np.cumsum(
            [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)]
        )

    def _arrays(self, year):
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=year,
            cod_ramp_enabled=True,
            plant_level_fleet=True,
        )
        return generators_to_fleet_arrays(
            self.fleet,
            self.zone_names,
            hours=8760,
            iso="NEISO",
            config=cfg,
            year=year,
        )

    def _mystic_mw_by_month(self, fa):
        idx = self.np.where(fa.plant_code == 1588)[0]
        return [
            float(
                sum(fa.pmax[i] * fa.availability[i, self.month_start[m]] for i in idx)
            )
            for m in range(12)
        ]

    def test_retiree_injected_into_snapshot(self):
        self.assertTrue(
            self.has_mystic, "Mystic (1588) not injected — retiree parquet?"
        )

    def test_mystic_online_all_of_2023(self):
        mw = self._mystic_mw_by_month(self._arrays(2023))
        self.assertTrue(all(m > 0 for m in mw), mw)

    def test_mystic_retires_mid_2024(self):
        mw = self._mystic_mw_by_month(self._arrays(2024))
        self.assertTrue(all(m > 0 for m in mw[:5]), mw)  # online Jan-May
        self.assertEqual(max(mw[6:]), 0.0, mw)  # gone by July

    def test_mystic_absent_in_2025(self):
        mw = self._mystic_mw_by_month(self._arrays(2025))
        self.assertEqual(max(mw), 0.0, mw)

    def test_cc_regular_set_differs_by_year(self):
        def cc_codes(year):
            fa = self._arrays(year)
            on = fa.availability.max(axis=1) > 0
            return {
                int(c)
                for c, g, o in zip(fa.plant_code, self.fleet, on)
                if g.plant_group == "CC_REGULAR" and o
            }

        c23, c25 = cc_codes(2023), cc_codes(2025)
        self.assertIn(1588, c23)
        self.assertNotIn(1588, c25)
        self.assertNotEqual(c23, c25)


class TestClassCodCoverage(unittest.TestCase):
    """Per-class COD-coverage guardrail (so a vintage can't drop a class)."""

    def test_trivial_single_class_fully_covered(self):
        cov = class_cod_coverage(["gas_cc"], [2012])
        self.assertEqual(cov, {"gas_cc": (1, 1)})
        self.assertEqual(log_class_cod_coverage(cov, "CAISO", 2024), [])

    def test_class_with_no_cod_is_flagged_uncovered(self):
        # Two gas_cc units have a COD, every coal unit is vintage-unknown.
        cov = class_cod_coverage(
            ["gas_cc", "gas_cc", "coal", "coal"], [2012, 2018, None, None]
        )
        self.assertEqual(cov["gas_cc"], (2, 2))
        self.assertEqual(cov["coal"], (2, 0))
        uncovered = log_class_cod_coverage(cov, "CAISO", 2024)
        self.assertEqual(uncovered, ["coal"])

    def test_partial_coverage_within_a_class_is_not_flagged(self):
        # A class is only flagged when it has ZERO COD dates; one is enough.
        cov = class_cod_coverage(["oil", "oil"], [None, 1998])
        self.assertEqual(cov["oil"], (2, 1))
        self.assertEqual(log_class_cod_coverage(cov, "CAISO", 2024), [])

    def test_blank_label_falls_back_to_unknown(self):
        cov = class_cod_coverage([""], [2005])
        self.assertEqual(cov, {"unknown": (1, 1)})


def _ref_reduce_cod_groups(work):
    """The SHIPPED (pre-A-1) per-group reduction, verbatim, as the reference.

    Frozen copy of the ``for code, grp in work.groupby("pc")`` loop that
    :func:`market_sim.data.cod_ramp._reduce_cod_groups` replaced (wall-clock
    item A-1, ``docs/handoffs/wallclock-opportunities-2026-09.md`` §2 A-1).
    The vectorized reducer is BYTE-IDENTICAL, so this stays as the oracle —
    do not "modernize" it to match the new code; if the two ever diverge, the
    new code is what changed.
    """
    cod = {}
    for code, grp in work.groupby("pc"):
        code = int(code)
        weights = grp["w"].to_numpy()
        if weights.sum() <= 0.0:
            weights = np.ones(len(grp))
        cont = grp["oy"].to_numpy() + (grp["om"].to_numpy() - 1.0) / 12.0
        mean = float(np.average(cont, weights=weights))
        online_year = int(np.floor(mean))
        online_month = int(round((mean - online_year) * 12.0)) + 1
        online_month = min(max(online_month, 1), 12)
        ret_year = ret_month = None
        ret = grp.dropna(subset=["ry"])
        if len(ret) == len(grp) and len(ret) > 0:
            last = ret.sort_values(["ry", "rm"]).iloc[-1]
            ret_year = int(last["ry"])
            ret_month = int(last["rm"]) if pd.notna(last["rm"]) else 12
        cod[code] = (online_year, online_month, ret_year, ret_month)
    return cod


def _ref_load_cod_map(eia860_dir):
    """The shipped ``_load_cod_map`` body around :func:`_ref_reduce_cod_groups`."""
    cod = {}
    frames = [
        _cod_work_frame(
            eia860_dir / "eia860_generator_operable.parquet",
            {
                "pc": "Plant Code",
                "oy": "Operating Year",
                "om": "Operating Month",
                "cap": "Nameplate Capacity (MW)",
                "ry": "Planned Retirement Year",
                "rm": "Planned Retirement Month",
            },
        ),
        _cod_work_frame(
            eia860_dir / _RETIRED_WINDOW_NAME,
            {
                "pc": "plant_id",
                "oy": "operating_year",
                "om": "operating_month",
                "cap": "nameplate_capacity_mw",
                "ry": "planned_retirement_year",
                "rm": "planned_retirement_month",
            },
        ),
    ]
    frames = [f for f in frames if f is not None]
    work = pd.concat(frames, ignore_index=True) if frames else None

    if work is not None and not work.empty:
        work["om"] = work["om"].fillna(COD_FALLBACK_MONTH).clip(1, 12)
        work["w"] = work["cap"].where(work["cap"] > 0.0, 0.0)
        cod.update(_ref_reduce_cod_groups(work))

    reg = _registry_year_built()
    for code, year in zip(reg["plant_id"], reg["year_built"]):
        code = int(code)
        if code not in cod:
            cod[code] = (int(year), COD_FALLBACK_MONTH, None, None)

    return cod


def _work_frame(rows):
    """Build the reducer's prepared work frame from ``(pc, oy, om, cap, ry, rm)``."""
    work = pd.DataFrame(
        [dict(zip(("pc", "oy", "om", "cap", "ry", "rm"), r)) for r in rows],
        columns=["pc", "oy", "om", "cap", "ry", "rm"],
    ).astype("float64")
    work["om"] = work["om"].fillna(COD_FALLBACK_MONTH).clip(1, 12)
    work["w"] = work["cap"].where(work["cap"] > 0.0, 0.0)
    return work


class TestReduceCodGroupsMatchesShippedLoop(unittest.TestCase):
    """A-1: the vectorized per-plant reduction is byte-identical to the loop.

    Hermetic (fast-tier) half of the A-1 gate — the real-vintage half is
    :class:`TestLoadCodMapVintageParity` below. Every case is checked against
    :func:`_ref_reduce_cod_groups`, the frozen shipped implementation.
    """

    def _assert_parity(self, rows, msg=""):
        work = _work_frame(rows)
        self.assertEqual(
            _reduce_cod_groups(work), _ref_reduce_cod_groups(work.copy()), msg
        )

    def test_single_unit_plants(self):
        self._assert_parity([(1.0, 2001, 3, 100.0, None, None)])

    def test_capacity_weighted_multi_unit_plant(self):
        # Bulk of the nameplate is the 2019 unit -> COD tracks it.
        self._assert_parity(
            [
                (7.0, 1998, 4, 12.0, None, None),
                (7.0, 2019, 11, 800.0, None, None),
                (7.0, 2005, 1, 30.0, None, None),
            ]
        )

    def test_zero_and_missing_capacity_falls_back_to_equal_weight(self):
        # Every unit reports no capacity -> the np.ones(len(grp)) branch.
        self._assert_parity(
            [
                (9.0, 1990, 2, 0.0, None, None),
                (9.0, 2010, 8, None, None, None),
                (9.0, 2000, 5, -3.0, None, None),
            ]
        )

    def test_half_integer_rounding_boundary(self):
        """The cases a sequential segment sum gets wrong.

        Eight equal-capacity units whose mean lands exactly on a half-month,
        and a mean landing exactly on a year boundary — measured on the live
        vintage as 15 of 14,334 plants (e.g. plant 448: ref month 9, a
        sequential sum gives 10). Guards the reducer's summation order.
        """
        self._assert_parity(
            [
                (448.0, y, m, 53.0, None, None)
                for y, m in (
                    (1968, 6),
                    (1968, 3),
                    (1967, 11),
                    (1967, 9),
                    (1967, 8),
                    (1967, 7),
                    (1967, 5),
                    (1967, 3),
                )
            ],
            "half-month boundary",
        )
        self._assert_parity(
            [
                (2004.0, 1949, 1, 0.6, None, None),
                (2004.0, 1954, 1, 1.1, None, None),
                (2004.0, 1974, 1, 2.0, None, None),
            ],
            "exact year boundary",
        )
        self._assert_parity(
            [
                (1478.0, y, 1, cap, None, None)
                for y, cap in ((1913, 0.4), (1913, 0.4), (1916, 0.4), (1929, 0.6))
            ],
            "december/january boundary",
        )

    def test_whole_plant_retirement_takes_the_latest_date(self):
        self._assert_parity(
            [
                (11.0, 1980, 1, 100.0, 2027.0, 6.0),
                (11.0, 1982, 1, 100.0, 2029.0, 3.0),
                (11.0, 1981, 1, 100.0, 2029.0, 1.0),
            ]
        )

    def test_partial_retirement_leaves_plant_online(self):
        # One unit without a planned retirement -> no plant retirement at all.
        self._assert_parity(
            [
                (12.0, 1980, 1, 100.0, 2027.0, 6.0),
                (12.0, 1982, 1, 100.0, None, None),
            ]
        )

    def test_missing_retirement_month_sorts_last_and_defaults_to_december(self):
        # NaN `rm` is na_position="last" in the shipped sort_values, so it wins
        # the tie on the latest `ry` and resolves to month 12.
        self._assert_parity(
            [
                (13.0, 1980, 1, 100.0, 2030.0, None),
                (13.0, 1981, 1, 100.0, 2030.0, 4.0),
            ]
        )

    def test_retirement_month_ties_on_the_same_year(self):
        self._assert_parity(
            [
                (14.0, 1980, 1, 100.0, 2030.0, 7.0),
                (14.0, 1981, 1, 100.0, 2030.0, 7.0),
            ]
        )

    def test_many_plants_of_mixed_shapes_together(self):
        rng = np.random.default_rng(20260905)
        rows = []
        for code in range(1, 400):
            for _ in range(int(rng.integers(1, 14))):
                retires = bool(rng.integers(0, 2))
                rows.append(
                    (
                        float(code),
                        int(rng.integers(1950, 2025)),
                        int(rng.integers(1, 13)),
                        float(rng.choice([0.0, 0.4, 53.0, 800.0])),
                        float(rng.integers(2026, 2040)) if retires else None,
                        float(rng.integers(1, 13))
                        if retires and rng.integers(0, 4)
                        else None,
                    )
                )
        self._assert_parity(rows)

    def test_group_sizes_spanning_the_pairwise_summation_blocks(self):
        # numpy's pairwise sum changes shape at 8 and 128 elements; the reducer
        # buckets plants by unit count so each cohort reduces the same way.
        rng = np.random.default_rng(7)
        rows = []
        for code, size in enumerate((1, 2, 7, 8, 9, 127, 128, 129, 300), start=1):
            for _ in range(size):
                rows.append(
                    (
                        float(code),
                        int(rng.integers(1950, 2025)),
                        int(rng.integers(1, 13)),
                        float(rng.choice([1.0, 1e-6, 1e6])),
                        None,
                        None,
                    )
                )
        self._assert_parity(rows)


@requires_raw(paths.EIA_860_DIR)
class TestLoadCodMapVintageParity(unittest.TestCase):
    """A-1 gate (1): dict equality vs the shipped loop on EVERY vintage dir.

    Enumerates the canonical ``data/raw/eia-860`` (whose map is the union of
    the operable schedule AND the within-window retiree parquet) plus every
    committed ``vintage_<year>/`` directory, and asserts the vectorized
    ``_load_cod_map`` returns a dict equal to the frozen shipped
    implementation's. Marked ``fulldata``/``slow``: the reference loop alone is
    ~20 s per vintage.
    """

    def test_every_committed_vintage_is_dict_identical(self):
        dirs = [paths.EIA_860_DIR] + sorted(
            p for p in paths.EIA_860_DIR.glob("vintage_*") if p.is_dir()
        )
        # The canonical dir plus the committed year-matched vintages.
        self.assertGreater(len(dirs), 1, "no EIA-860 vintage directories found")
        for eia860_dir in dirs:
            with self.subTest(vintage=eia860_dir.name):
                _load_cod_map.cache_clear()
                vec = _load_cod_map(eia860_dir)
                self.assertGreater(len(vec), 100)
                self.assertEqual(vec, _ref_load_cod_map(eia860_dir))


TestLoadCodMapVintageParity = pytest.mark.slow(TestLoadCodMapVintageParity)


if __name__ == "__main__":
    unittest.main()
