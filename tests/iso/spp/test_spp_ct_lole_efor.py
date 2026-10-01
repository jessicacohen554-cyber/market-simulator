"""Tests for the SPP CT_PEAKER LOLE-study EFOR replacement (SPP-104).

``spp_ct_lole_efor`` (``docs/records/spp/DESIGN-spp-104-ct-outage-2026-09-29.md``)
replaces the statistical CT_PEAKER WEFOR with SPP's own seasonal natural-gas EFOR
by unit size. Trivial cases first per the repo testing pattern: one or two
generators, a full-year hour index (the seasons are month-keyed).
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from market_sim.config.constants import SPP_LOLE_GAS_EFOR_BY_SIZE
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import arrays
from market_sim.data.fleet.ct_lole_efor import (
    efor_for_unit_mw,
    plant_efor,
    spp_ct_plant_efor,
)
from tests.helpers.builders import make_gen

T = 8760


def _gens():
    ct = make_gen(
        "CT_PEAKER_SPP-North_p7_peak",
        "SPP-North",
        fuel_type="gas_ct",
        pmax_mw=60.0,
        plant_group="CT_PEAKER",
        plant_code=7,
        online_year=2015,
    )
    cc = make_gen(
        "CC_REGULAR_SPP-North_p8_econlo",
        "SPP-North",
        fuel_type="gas_cc",
        pmax_mw=300.0,
        plant_group="CC_REGULAR",
        plant_code=8,
        online_year=2015,
    )
    return [ct, cc]


def _avail(cfg, lole=None):
    gens = _gens()
    a = np.ones((len(gens), T))
    with mock.patch(
        "market_sim.data.fleet.ct_lole_efor.spp_ct_plant_efor",
        return_value=lole or {},
    ):
        arrays._availability_matrix(gens, a, T, cfg, "SPP", 2024, set())
    return a


class TestTable(unittest.TestCase):
    """The table lookup and the plant weighting carry no free number."""

    def test_bins_and_edges(self):
        self.assertEqual(efor_for_unit_mw(50.0), (0.17, 0.23))
        self.assertEqual(efor_for_unit_mw(50.1), (0.23, 0.28))
        self.assertEqual(efor_for_unit_mw(600.0), (0.22, 0.27))
        self.assertEqual(len(SPP_LOLE_GAS_EFOR_BY_SIZE), 5)

    def test_refuses_unpublished_sizes(self):
        for mw in (0.0, -1.0, 600.5):
            with self.assertRaises(ValueError):
                efor_for_unit_mw(mw)

    def test_plant_capacity_weighting(self):
        s, w = plant_efor({"1": 40.0, "2": 80.0})
        self.assertAlmostEqual(s, (40 * 0.17 + 80 * 0.23) / 120)
        self.assertAlmostEqual(w, (40 * 0.23 + 80 * 0.28) / 120)

    def test_spp_only(self):
        with self.assertRaises(ValueError):
            spp_ct_plant_efor("MISO", 2024)
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="ERCOT", spp_ct_lole_efor=True)


class TestConfig(unittest.TestCase):
    """Default off keeps the key; armed earns a distinct one."""

    def test_default_off_keeps_key(self):
        a = ScenarioConfig(iso="SPP")
        self.assertFalse(a.spp_ct_lole_efor)
        b = ScenarioConfig(iso="SPP", spp_ct_lole_efor=True)
        self.assertNotEqual(a.cache_key(), b.cache_key())


class TestAvailability(unittest.TestCase):
    """The CT branch replaces WEFOR only, and nothing else moves."""

    def setUp(self):
        self.off = ScenarioConfig(iso="SPP", mode="backcast", wefor_multiplier=0.7)
        self.on = ScenarioConfig(
            iso="SPP", mode="backcast", wefor_multiplier=0.7, spp_ct_lole_efor=True
        )

    def test_off_is_byte_identical_to_empty_map(self):
        base = _avail(self.off)
        np.testing.assert_array_equal(base, _avail(self.on, lole={}))

    def test_armed_replaces_ct_wefor_by_season(self):
        base = _avail(self.off)
        armed = _avail(self.on, lole={7: (0.20, 0.30)})
        # The CC row is untouched.
        np.testing.assert_array_equal(base[1], armed[1])
        month = arrays._hour_to_month_index(T) + 1
        pof, _, derate = arrays._thermal_outage("CT_PEAKER", 2024 - 2015)
        sd = 1.0 - arrays._SUMMER_CLASS_DERATE["CT_PEAKER"]
        jan = armed[0, month == 1]
        jul = armed[0, month == 7]
        apr = armed[0, month == 4]
        np.testing.assert_allclose(jan, 1.0 - 0.30 - derate)
        np.testing.assert_allclose(jul, (1.0 - 0.20 - derate) * sd)
        np.testing.assert_allclose(apr, 1.0 - 0.30 - derate - pof)
        # wefor_multiplier no longer reaches the CT row: a 1.0 multiplier arms
        # to the same array.
        on1 = ScenarioConfig(
            iso="SPP", mode="backcast", wefor_multiplier=1.0, spp_ct_lole_efor=True
        )
        np.testing.assert_array_equal(armed[0], _avail(on1, lole={7: (0.20, 0.30)})[0])

    def test_plant_missing_from_roster_keeps_statistical(self):
        base = _avail(self.off)
        armed = _avail(self.on, lole={99: (0.20, 0.30)})
        np.testing.assert_array_equal(base, armed)


if __name__ == "__main__":
    unittest.main()
