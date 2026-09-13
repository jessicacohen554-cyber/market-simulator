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
    _load_unit_cod_map,
    _registry_year_built,
    bin_online_fraction,
    class_cod_coverage,
    effective_cod,
    generator_online_mask,
    load_cod_map,
    load_unit_cod_map,
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
    """Resolving a generator's COD: its own measured date first, the plant map second.

    SOCO-15 (owner card S12, 2026-09-13): a raw EIA-860 unit's own
    ``Operating Year`` / ``Operating Month`` is the measured input and the
    plant-collapsed mean is the estimate, so the unit's own online date wins
    (rule 14 [R-ACCURATE]). The plant map still owns the online date of a
    PLANT-LEVEL object (``is_plant_level=True`` — a CAMPD bin, whose
    ``online_year`` is a registry / COD-year estimate, not a unit record).
    """

    def test_plant_map_wins_only_for_plant_level_objects(self):
        cod_map = {7: (2024, 9, None, None)}
        # A CAMPD bin claims the registry vintage 2010; it has no own date,
        # so the plant map's Sept-2024 record is its COD.
        self.assertEqual(
            effective_cod(7, 2010, 1, None, None, cod_map, is_plant_level=True),
            (2024, 9, None, None),
        )
        # A raw EIA-860 unit with the SAME attributes keeps its own 2010-01
        # record: the map is a plant mean, the unit's own date is measured.
        self.assertEqual(
            effective_cod(7, 2010, 1, None, None, cod_map),
            (2010, 1, None, None),
        )

    def test_brownfield_unit_prefers_own_online_date_over_plant_mean(self):
        """The card-S12 regression: Vogtle 3 (plant 649, own COD 2023-07).

        The plant-collapsed map reads (2005, 5) — the capacity-weighted mean
        of units 1/2 (1987/1989) and 3/4 (2023/2024). Before SOCO-15 the map
        ALWAYS won the online date, so this unit was online all of 2023
        (12.98 TWh of phantom nuclear); it must ramp on its own month.
        """
        cod_map = {649: (2005, 5, None, None)}
        self.assertEqual(
            effective_cod(649, 2023, 7, None, None, cod_map),
            (2023, 7, None, None),
        )
        self.assertEqual(
            monthly_online_mask(*effective_cod(649, 2023, 7, None, None, cod_map), 2023)
            .astype(int)
            .tolist(),
            [0] * 6 + [1] * 6,
        )

    def test_raw_unit_keeps_plant_map_retirement_when_it_carries_none(self):
        # Own online date, but no own retirement: the whole-plant retirement
        # from the map still applies (only the ONLINE half of the seam moved).
        cod_map = {9: (1990, 1, 2024, 6)}
        self.assertEqual(
            effective_cod(9, 2023, 7, None, None, cod_map),
            (2023, 7, 2024, 6),
        )

    def test_sentinel_raw_unit_falls_back_to_plant_map(self):
        # online_year == 2000 is "vintage unknown" -> the plant map is the
        # only record, exactly as before the seam.
        cod_map = {7: (2024, 9, None, None)}
        self.assertEqual(
            effective_cod(7, 2000, 1, None, None, cod_map),
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
            effective_cod(3122, 2010, 1, None, None, cod_map, is_plant_level=True),
            (1972, 5, 2024, 4),
        )


class TestBinOnlineFraction(unittest.TestCase):
    """A (plant, group) bin's measured monthly online-capacity fraction."""

    def test_greenfield_bin_steps_exactly_like_the_plant_mean(self):
        # Lowman (plant 56): every CC unit came online 2023-09 -> the fraction
        # is the same 000000001111 step the plant-collapsed date produced.
        units = ((459.0, 2023, 9), (273.7, 2023, 9))
        self.assertEqual(
            bin_online_fraction(units, 2023).tolist(), [0.0] * 8 + [1.0] * 4
        )

    def test_brownfield_bin_takes_the_intermediate_fraction(self):
        # Barry (plant 3) CC: 1,071 MW of 2000-05 units plus A3 (774 MW,
        # 2023-11) -> 1071/1845 through October, 1.0 from November.
        units = (
            (170.1, 2000, 5),
            (195.2, 2000, 5),
            (705.7, 2000, 5),
            (774.0, 2023, 11),
        )
        frac = bin_online_fraction(units, 2023)
        self.assertAlmostEqual(frac[0], 1071.0 / 1845.0, places=12)
        self.assertAlmostEqual(frac[9], 1071.0 / 1845.0, places=12)
        self.assertEqual(frac[10], 1.0)
        self.assertEqual(frac[11], 1.0)

    def test_all_units_predating_the_year_is_exactly_ones(self):
        # Exact endpoints: no 1 - 1e-16 residue may reach the LP.
        units = ((7.4, 2005, 3), (6.7, 2001, 1), (1.064, 2010, 5))
        frac = bin_online_fraction(units, 2023)
        self.assertTrue(np.array_equal(frac, np.ones(12)))
        self.assertEqual(frac.tolist(), [1.0] * 12)

    def test_not_yet_built_bin_is_exactly_zeros(self):
        self.assertEqual(
            bin_online_fraction(((100.0, 2026, 1),), 2024).tolist(), [0.0] * 12
        )

    def test_zero_nameplate_falls_back_to_equal_weights(self):
        units = ((0.0, 2000, 1), (0.0, 2023, 7))
        self.assertEqual(
            bin_online_fraction(units, 2023).tolist(), [0.5] * 6 + [1.0] * 6
        )

    def test_empty_units_is_all_online(self):
        self.assertEqual(bin_online_fraction((), 2023).tolist(), [1.0] * 12)


class TestGeneratorOnlineMask(unittest.TestCase):
    """The single resolver: unit grain for raw units, constituent fraction for bins."""

    _map = {
        649: (2005, 5, None, None),
        3: (1991, 3, None, None),
        56: (2023, 9, None, None),
    }
    _units = {
        (3, "gas_cc"): ((1071.0, 2000, 5), (774.0, 2023, 11)),
        (3, "coal"): ((1500.0, 1970, 1),),
        (56, "gas_cc"): ((459.0, 2023, 9), (273.7, 2023, 9)),
    }

    def test_raw_brownfield_unit_ramps_on_its_own_month(self):
        mask, oy = generator_online_mask(
            649, None, 2023, 7, None, None, False, self._map, self._units, 2023
        )
        self.assertEqual(mask.tolist(), [0.0] * 6 + [1.0] * 6)
        self.assertEqual(oy, 2023)

    def test_brownfield_bin_takes_constituent_fraction(self):
        mask, _ = generator_online_mask(
            3, "CC_REGULAR", 1991, 1, None, None, True, self._map, self._units, 2023
        )
        self.assertAlmostEqual(mask[0], 1071.0 / 1845.0, places=12)
        self.assertEqual(mask[11], 1.0)

    def test_sibling_bin_of_another_group_is_untouched(self):
        # Barry's COAL bin never sees Barry A3's 2023-11 COD.
        mask, _ = generator_online_mask(
            3, "COAL", 1991, 1, None, None, True, self._map, self._units, 2023
        )
        self.assertEqual(mask.tolist(), [1.0] * 12)

    def test_greenfield_bin_ramps_identically_with_and_without_constituents(self):
        # Exit condition (b): the greenfield case still ramps 000000001111 —
        # through the constituent fraction AND through the plant-map fallback.
        with_units, _ = generator_online_mask(
            56, "CC_REGULAR", 2010, 1, None, None, True, self._map, self._units, 2023
        )
        without_units, _ = generator_online_mask(
            56, "CC_REGULAR", 2010, 1, None, None, True, self._map, {}, 2023
        )
        self.assertEqual(with_units.tolist(), [0.0] * 8 + [1.0] * 4)
        self.assertEqual(without_units.tolist(), [0.0] * 8 + [1.0] * 4)

    def test_bin_without_constituents_keeps_plant_collapsed_date(self):
        # An ERCOT curated-sheet bin at a plant the unit map has no matching
        # fuel for -> the plant mean, exactly as before.
        mask, _ = generator_online_mask(
            3, "ST_GAS", 1991, 1, None, None, True, self._map, self._units, 2023
        )
        self.assertEqual(mask.tolist(), [1.0] * 12)

    def test_bin_fraction_is_scaled_by_the_plant_retirement(self):
        cod_map = {3: (1991, 3, 2023, 6)}
        mask, _ = generator_online_mask(
            3, "CC_REGULAR", 1991, 1, None, None, True, cod_map, self._units, 2023
        )
        self.assertAlmostEqual(mask[0], 1071.0 / 1845.0, places=12)
        self.assertEqual(mask[6:].tolist(), [0.0] * 6)

    def test_bin_own_cohort_retirement_still_wins(self):
        # partial_plant_exit_carry cohort: the bin's own retirement is kept.
        mask, _ = generator_online_mask(
            3, "CC_REGULAR", 1991, 1, 2023, 3, True, self._map, self._units, 2023
        )
        self.assertEqual(mask[3:].tolist(), [0.0] * 9)
        self.assertAlmostEqual(mask[0], 1071.0 / 1845.0, places=12)


class TestLiveCardS12Cases(unittest.TestCase):
    """The three measured cases of SOCO-10 §2, on the committed root vintage.

    Integration: reads ``data/raw/eia-860`` exactly as :class:`TestLoadCodMap`
    does. The plant-collapsed map is UNCHANGED (its numbers are the ones
    SOCO-10 measured); what changed is which grain the resolver serves.
    """

    @classmethod
    def setUpClass(cls):
        cls.cod_map = load_cod_map()
        cls.unit_map = load_unit_cod_map()

    def test_plant_collapsed_map_is_unchanged(self):
        self.assertEqual(self.cod_map[649][:2], (2005, 5))
        self.assertEqual(self.cod_map[3][:2], (1991, 3))
        self.assertEqual(self.cod_map[56][:2], (2023, 9))

    def test_vogtle_3_and_4_ramp_on_their_own_months(self):
        v3, _ = generator_online_mask(
            649, None, 2023, 7, None, None, False, self.cod_map, self.unit_map, 2023
        )
        v4_2023, _ = generator_online_mask(
            649, None, 2024, 4, None, None, False, self.cod_map, self.unit_map, 2023
        )
        v4_2024, _ = generator_online_mask(
            649, None, 2024, 4, None, None, False, self.cod_map, self.unit_map, 2024
        )
        self.assertEqual(v3.tolist(), [0.0] * 6 + [1.0] * 6)
        self.assertEqual(v4_2023.tolist(), [0.0] * 12)
        self.assertEqual(v4_2024.tolist(), [0.0] * 3 + [1.0] * 9)

    def test_barry_cc_bin_carries_a3_from_november(self):
        units = self.unit_map[(3, "gas_cc")]
        self.assertIn((464.0, 2023, 11), units)
        self.assertIn((310.0, 2023, 11), units)
        mask, _ = generator_online_mask(
            3,
            "CC_REGULAR",
            1991,
            1,
            None,
            None,
            True,
            self.cod_map,
            self.unit_map,
            2023,
        )
        total = sum(u[0] for u in units)
        self.assertAlmostEqual(mask[0], (total - 774.0) / total, places=9)
        self.assertEqual(mask[10:].tolist(), [1.0, 1.0])
        coal, _ = generator_online_mask(
            3, "COAL", 1991, 1, None, None, True, self.cod_map, self.unit_map, 2023
        )
        self.assertEqual(coal.tolist(), [1.0] * 12)

    def test_greenfield_lowman_still_ramps(self):
        mask, _ = generator_online_mask(
            56,
            "CC_REGULAR",
            2010,
            1,
            None,
            None,
            True,
            self.cod_map,
            self.unit_map,
            2023,
        )
        self.assertEqual(mask.tolist(), [0.0] * 8 + [1.0] * 4)

    def test_unit_map_is_operable_thermal_only(self):
        self.assertGreater(len(self.unit_map), 1000)
        fuels = {fuel for _, fuel in self.unit_map}
        self.assertTrue(
            fuels <= {"gas_cc", "gas_ct", "gas_st", "coal", "oil", "biomass", "nuclear"}
        )
        for units in list(self.unit_map.values())[:200]:
            for cap, oy, om in units:
                self.assertGreaterEqual(cap, 0.0)
                self.assertGreaterEqual(oy, 1880)
                self.assertTrue(1 <= om <= 12)

    def test_unit_map_rekeys_on_vintage_directory(self):
        vintage = paths.EIA_860_DIR / "vintage_2023"
        if not vintage.is_dir():
            self.skipTest("vintage_2023 not committed")
        _load_unit_cod_map.cache_clear()
        v23 = _load_unit_cod_map(vintage)
        # Vogtle 4 (2024-04) cannot be in the end-2023 operable snapshot.
        self.assertNotIn((1114.0, 2024, 4), v23.get((649, "nuclear"), ()))

    def test_loader_bridges_each_units_own_operating_month(self):
        from market_sim.data.fleet.eia860 import _operating_month_by_unit

        months = _operating_month_by_unit(paths.EIA_860_DIR)
        self.assertEqual(months[(649, "3")], 7)
        self.assertEqual(months[(649, "4")], 4)
        self.assertEqual(months[(3, "A3C1")], 11)


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

    def _fa(
        self, enabled: bool, cod_map=None, mode="backcast", unit_map=None, **gen_kw
    ):
        cfg = ScenarioConfig(
            mode=mode,
            weather_year=2024,
            cod_ramp_enabled=enabled,
        )
        # Patch the EIA-860 maps so the unit tests are hermetic and fast; the
        # individual coal gens carry plant_code 0, so they fall back to their
        # own online_year/month regardless of the (default empty) maps.
        with (
            mock.patch(
                "market_sim.data.fleet.load_cod_map", return_value=cod_map or {}
            ),
            mock.patch(
                "market_sim.data.fleet.load_unit_cod_map", return_value=unit_map or {}
            ),
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

    def test_brownfield_raw_unit_ramps_on_own_month_not_plant_mean(self):
        """Card S12 in the fleet arrays: a Vogtle-3-like unit at a 2005-mean plant.

        FAILS on the pre-SOCO-15 seam (the plant map won, so the unit was
        available all year) and PASSES on the repaired one.
        """
        on = self._fa(
            True,
            cod_map={649: (2005, 5, None, None)},
            fuel_type="nuclear",
            plant_code=649,
            online_year=2024,
            online_month=7,
        )
        jul = self._starts[6]
        self.assertEqual(on.availability[0, :jul].max(), 0.0)
        self.assertGreater(on.availability[0, jul:].max(), 0.0)

    def test_brownfield_bin_availability_is_the_constituent_fraction(self):
        """A Barry-like CC bin runs at its measured online share until A3's month."""
        units = {(3, "gas_cc"): ((1071.0, 2000, 5), (774.0, 2024, 11))}
        on = self._fa(
            True,
            cod_map={3: (1991, 3, None, None)},
            unit_map=units,
            is_campd_bin=True,
            plant_code=3,
            plant_group="CC_REGULAR",
            fuel_type="gas_cc",
            online_year=1991,
            online_month=1,
        )
        flat = self._fa(
            False,
            is_campd_bin=True,
            plant_code=3,
            plant_group="CC_REGULAR",
            fuel_type="gas_cc",
            online_year=1991,
            online_month=1,
        )
        nov = self._starts[10]
        ratio = on.availability[0, :nov] / flat.availability[0, :nov]
        self.assertTrue(np.allclose(ratio, 1071.0 / 1845.0))
        self.assertTrue(
            np.array_equal(on.availability[0, nov:], flat.availability[0, nov:])
        )

    def test_greenfield_bin_still_ramps_through_constituents(self):
        """Exit condition (b): the greenfield step is unchanged by the seam."""
        units = {(56, "gas_cc"): ((459.0, 2024, 9), (273.7, 2024, 9))}
        for unit_map in (units, {}):
            on = self._fa(
                True,
                cod_map={56: (2024, 9, None, None)},
                unit_map=unit_map,
                is_campd_bin=True,
                plant_code=56,
                plant_group="CC_REGULAR",
                online_year=2010,
                online_month=1,
            )
            sep = self._starts[8]
            self.assertEqual(on.availability[0, :sep].max(), 0.0)
            self.assertGreater(on.availability[0, sep:].max(), 0.0)

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
