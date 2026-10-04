"""closeout-CAISO-w3: 2021 own DSW clean depths and the daily-shaped unprinted hub formula.

``caiso_dsw_clean_depth_own_year`` gives each DSW clean rung its own measured
2021 depth (interchange spec ``CAISO_DSW_CLEAN_OWN_YEAR_DEPTH``) instead of the
pooled static; ``caiso_intertie_unprinted_daily_gas_shape`` multiplies the
R-CAISO-18 unprinted-hour formula's monthly gas by the measured CA citygate
within-month daily shape. Both default off and byte-identical off; both inert in
2022-2025 on. Trivial cases first. Record: ``docs/records/caiso/closeout-caiso-w3/``.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    CAISO_DSW_CLEAN_OWN_YEAR_DEPTH,
    CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC,
    CAISO_DSW_DAYTIME_CLEAN_NAME,
    CAISO_DSW_OVERNIGHT_CLEAN_NAME,
    CAISO_PER_HUB_IMPORT_ZONES,
    CAISO_PER_HUB_NEIGHBORS,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.eia930.envelopes import measured_import_hub_prices
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.fuel.hubs import caiso_citygate_daily_shape_factors
from market_sim.data.neighbor_price import caiso_hub_measured_gas_reference_price
from market_sim.model.transmission import (
    build_caiso_per_hub_intertie,
    inject_caiso_dsw_daytime_clean,
    inject_caiso_dsw_overnight_clean,
    inject_caiso_firm_import_shape,
)

HOURS = 8760
ZONE = CAISO_PER_HUB_IMPORT_ZONES["PALOVRDE"]
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
FLAGS = ("caiso_dsw_clean_depth_own_year", "caiso_intertie_unprinted_daily_gas_shape")


def _fleet():
    gens = build_caiso_per_hub_intertie(
        overnight_clean=True, daytime_clean=True, lateevening_clean=True
    )
    fleet = generators_to_fleet_arrays(
        gens, sorted({g.zone for g in gens}), hours=HOURS
    )
    inject_caiso_firm_import_shape(fleet, "CAISO", 2024)
    return fleet


def _pmax(fleet, name):
    return float(fleet.pmax[list(fleet.unit_ids).index(f"{ZONE}_{name}")])


class TestDailyShapeFactors(unittest.TestCase):
    def test_month_mean_is_exactly_one(self):
        f = caiso_citygate_daily_shape_factors(2021, HOURS)
        for m in range(1, 13):
            self.assertAlmostEqual(float(f[MONTH == m].mean()), 1.0, places=9)

    def test_uri_days_carry_the_february_spike(self):
        f = caiso_citygate_daily_shape_factors(2021, HOURS)
        feb = f[MONTH == 2]
        self.assertGreater(float(feb.max()), 2.0)
        self.assertLess(float(np.median(feb)), 1.0)

    def test_no_print_year_is_all_ones(self):
        np.testing.assert_array_equal(
            caiso_citygate_daily_shape_factors(1990, 48), np.ones(48)
        )


class TestFormula(unittest.TestCase):
    def test_off_is_byte_identical(self):
        spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
        a = caiso_hub_measured_gas_reference_price(
            spec, 2020, HOURS, eia923_fallback=True
        )
        b = caiso_hub_measured_gas_reference_price(
            spec, 2020, HOURS, eia923_fallback=True, daily_gas_shape=False
        )
        np.testing.assert_array_equal(a, b)

    def test_on_preserves_monthly_mean_up_to_shape_weighting(self):
        spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
        flat = caiso_hub_measured_gas_reference_price(
            spec, 2021, HOURS, eia923_fallback=True
        )
        shaped = caiso_hub_measured_gas_reference_price(
            spec, 2021, HOURS, eia923_fallback=True, daily_gas_shape=True
        )
        self.assertFalse(np.allclose(flat, shaped))
        # the gas operand is month-mean preserving; the electricity load shape re-weights within the month
        np.testing.assert_allclose(
            shaped / flat, caiso_citygate_daily_shape_factors(2021, HOURS), rtol=1e-9
        )

    def test_loader_2022_to_2025_byte_identical_on(self):
        kw = dict(
            gap_fill_measured_gas=True,
            gap_fill_measured_dam=True,
            partial_year_measured=True,
            unprinted_year_measured_gas=True,
        )
        for year in (2022, 2023, 2024, 2025):
            off = measured_import_hub_prices("CAISO", year, HOURS, **kw)
            on = measured_import_hub_prices(
                "CAISO", year, HOURS, unprinted_daily_gas_shape=True, **kw
            )
            self.assertEqual(set(off), set(on))
            for k in off:
                np.testing.assert_array_equal(off[k], on[k])

    def test_loader_2020_moves_on(self):
        kw = dict(
            gap_fill_measured_dam=True,
            partial_year_measured=True,
            unprinted_year_measured_gas=True,
        )
        off = measured_import_hub_prices("CAISO", 2020, HOURS, **kw)
        on = measured_import_hub_prices(
            "CAISO", 2020, HOURS, unprinted_daily_gas_shape=True, **kw
        )
        self.assertTrue(any(not np.allclose(off[k], on[k]) for k in off))


class TestOwnYearDepth(unittest.TestCase):
    def test_rows_are_the_preregistered_2021_derives(self):
        self.assertEqual(
            {k: v[2021] for k, v in CAISO_DSW_CLEAN_OWN_YEAR_DEPTH.items()},
            {
                "DSW_surplus_clean": 6644.0,
                "DSW_overnight_clean": 6892.0,
                "DSW_daytime_clean": 7426.0,
                "DSW_lateevening_clean": 7288.0,
            },
        )
        self.assertEqual(
            set().union(*(v.keys() for v in CAISO_DSW_CLEAN_OWN_YEAR_DEPTH.values())),
            {2021},
        )

    def test_2021_daytime_off_static_on_own(self):
        off, on = _fleet(), _fleet()
        inject_caiso_dsw_daytime_clean(off, "CAISO", 2021, gap_fill_measured_dam=True)
        inject_caiso_dsw_daytime_clean(
            on, "CAISO", 2021, gap_fill_measured_dam=True, own_year_depth=True
        )
        self.assertEqual(
            _pmax(off, CAISO_DSW_DAYTIME_CLEAN_NAME),
            CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC,
        )
        self.assertEqual(_pmax(on, CAISO_DSW_DAYTIME_CLEAN_NAME), 7426.0)

    def test_other_years_byte_identical_on(self):
        for year in (2019, 2022, 2024):
            off, on = _fleet(), _fleet()
            inject_caiso_dsw_overnight_clean(
                off, "CAISO", year, gap_fill_measured_dam=True, unprinted_year_arm=True
            )
            inject_caiso_dsw_overnight_clean(
                on,
                "CAISO",
                year,
                gap_fill_measured_dam=True,
                unprinted_year_arm=True,
                own_year_depth=True,
            )
            np.testing.assert_array_equal(off.availability, on.availability)
            self.assertEqual(
                _pmax(off, CAISO_DSW_OVERNIGHT_CLEAN_NAME),
                _pmax(on, CAISO_DSW_OVERNIGHT_CLEAN_NAME),
            )


class TestConfigSeam(unittest.TestCase):
    def test_default_off_and_cache_registered(self):
        cfg = ScenarioConfig(iso="CAISO")
        for f in FLAGS:
            self.assertFalse(getattr(cfg, f))
            self.assertIn(f, _CACHE_KEY_OPTIONAL_FIELDS)
            self.assertEqual(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[f], "False")


if __name__ == "__main__":
    unittest.main()
