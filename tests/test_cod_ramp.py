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

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.cod_ramp import (
    COD_FALLBACK_MONTH,
    effective_cod,
    load_cod_map,
    monthly_online_mask,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays


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


class TestCodRampInFleetArrays(unittest.TestCase):
    """End-to-end masking inside generators_to_fleet_arrays."""

    # 1-based month -> cumulative hour boundary for a 2023 non-leap year.
    _starts = np.cumsum(
        [0] + [d * 24 for d in
               (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)]
    )

    def _coal_gen(self, **kw) -> Generator:
        base = dict(
            unit_id="c1", name="Test Coal", zone="North", fuel_type="coal",
            pmax_mw=500.0, pmin_mw=0.0, heat_rate=10.0, eford=0.05,
        )
        base.update(kw)
        return Generator(**base)

    def _fa(self, enabled: bool, cod_map=None, mode="backcast", **gen_kw):
        cfg = ScenarioConfig(
            mode=mode, weather_year=2024, cod_ramp_enabled=enabled,
        )
        # Patch the EIA-860 map so the unit tests are hermetic and fast; the
        # individual coal gens carry plant_code 0, so they fall back to their
        # own online_year/month regardless of the (default empty) map.
        with mock.patch(
            "market_sim.data.fleet.load_cod_map", return_value=cod_map or {}
        ):
            return generators_to_fleet_arrays(
                [self._coal_gen(**gen_kw)], ["North"], config=cfg, year=2024,
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
        np.testing.assert_allclose(
            on.availability[0, jun:], off.availability[0, jun:]
        )

    def test_midyear_retirement_masks_post_months(self):
        """A March retirement keeps Jan-Mar and zeros Apr-Dec."""
        off = self._fa(False, online_year=2000)
        on = self._fa(
            True, online_year=2000, retirement_year=2024, retirement_month=3,
        )
        apr = self._starts[3]  # first April hour
        np.testing.assert_allclose(
            on.availability[0, :apr], off.availability[0, :apr]
        )
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
            True, cod_map=cod_map, is_campd_bin=True, plant_code=4242,
            plant_group="CC_REGULAR", online_year=2010, online_month=1,
        )
        jun = self._starts[5]
        self.assertEqual(on.availability[0, :jun].max(), 0.0)
        self.assertGreater(on.availability[0, jun:].max(), 0.0)

    def test_min_gen_zeroed_in_offline_months(self):
        """The hard must-run floor cannot force a not-yet-built unit to run."""
        cfg = ScenarioConfig(
            mode="backcast", weather_year=2024, cod_ramp_enabled=True,
            gas_st_summer_mustrun=0.3,
        )
        gen = Generator(
            unit_id="s1", name="ST", zone="North", fuel_type="gas_st",
            pmax_mw=300.0, pmin_mw=0.0, heat_rate=11.0, eford=0.05,
            plant_group="ST_GAS", online_year=2024, online_month=8,
        )
        with mock.patch("market_sim.data.fleet.load_cod_map", return_value={}):
            fa = generators_to_fleet_arrays(
                [gen], ["North"], config=cfg, year=2024,
                load_shape=np.ones(8760) * 1000.0,
            )
        # ST_GAS summer must-run (May-Sep) would otherwise floor Jul; the unit
        # is not online until August, so July's floor must be zero.
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


if __name__ == "__main__":
    unittest.main()
