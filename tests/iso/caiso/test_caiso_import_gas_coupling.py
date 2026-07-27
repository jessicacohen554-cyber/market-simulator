"""Tests for CAISO gas-coupled import pricing.

``caiso_import_gas_coupling`` shifts the desert-SW gas import tranches (DSW_CCGT,
DSW_CT) by the measured commodity-gas delta so they track the same Henry-Hub-
plus-citygate-basis spot the hub-basis overlay applies to in-state gas — the
forecast-consistent, no-OASIS replacement for the desert-SW leg of lever A. See
``results/calibration/PLAN-caiso-gas-coupled-imports-2026-06-20.md``.
"""

from __future__ import annotations

import types
import unittest
from unittest import mock

import numpy as np

import market_sim.data.fuel as fuel
from market_sim.config.interchange_config import IMPORT_ZONE
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _CAISO_IMPORT_COUPLE_HR,
    build_import_generators,
    inject_caiso_import_gas_coupling,
)


class TestInjectCaisoImportGasCoupling(unittest.TestCase):
    def _caiso_fleet(self, hours):
        gens = build_import_generators("CAISO", border_carbon_per_mwh=15.0)
        zone = IMPORT_ZONE["CAISO"]
        return generators_to_fleet_arrays(gens, ["NP15", zone], hours=hours), gens

    def _config(self):
        return types.SimpleNamespace(iso="CAISO")

    def test_shifts_only_gas_tranches_by_delta_times_heatrate(self):
        hours = 48  # both days in January -> month 0 for every hour
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 99.0)
        # spot $3 < delivered $4 -> delta -1.0 $/MMBtu in every month
        spot = np.full(12, 3.0)
        f923 = np.full(12, 4.0)
        with mock.patch.object(fuel, "iso_hub_monthly_gas_prices", return_value=spot):
            with mock.patch.object(fuel, "iso_monthly_gas_prices", return_value=f923):
                applied = inject_caiso_import_gas_coupling(fa, mc, self._config(), 2024)
        self.assertTrue(applied)
        zone = IMPORT_ZONE["CAISO"]
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        # desert-SW blocks shifted by delta(-1.0) * representative SW heat rate
        for tr in ("DSW_solar_PV", "DSW_CCGT", "DSW_CT"):
            hr = _CAISO_IMPORT_COUPLE_HR[tr]
            self.assertAlmostEqual(mc[row[f"{zone}_{tr}"], 0], 99.0 - hr, places=4)
        # PNW (hydro) and WECC_scarcity (peak) not gas-coupled -> untouched
        for tr in ("PNW_hydro_base", "PNW_midC", "WECC_scarcity"):
            self.assertEqual(mc[row[f"{zone}_{tr}"], 0], 99.0)

    def test_missing_series_is_noop(self):
        hours = 48
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 99.0)
        before = mc.copy()
        with mock.patch.object(fuel, "iso_hub_monthly_gas_prices", return_value=None):
            with mock.patch.object(fuel, "iso_monthly_gas_prices", return_value=None):
                applied = inject_caiso_import_gas_coupling(fa, mc, self._config(), 2024)
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, before)

    def test_zero_delta_is_noop(self):
        hours = 48
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 99.0)
        before = mc.copy()
        same = np.full(12, 3.5)
        with mock.patch.object(fuel, "iso_hub_monthly_gas_prices", return_value=same):
            with mock.patch.object(fuel, "iso_monthly_gas_prices", return_value=same):
                applied = inject_caiso_import_gas_coupling(fa, mc, self._config(), 2024)
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, before)

    def test_nan_month_contributes_zero_shift(self):
        hours = 48
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 99.0)
        spot = np.full(12, 3.0)
        f923 = np.full(12, 4.0)
        spot[0] = np.nan  # January uncovered -> delta 0 for these hours
        with mock.patch.object(fuel, "iso_hub_monthly_gas_prices", return_value=spot):
            with mock.patch.object(fuel, "iso_monthly_gas_prices", return_value=f923):
                applied = inject_caiso_import_gas_coupling(fa, mc, self._config(), 2024)
        # other months have a real delta, so it still applies overall...
        self.assertTrue(applied)
        zone = IMPORT_ZONE["CAISO"]
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        # ...but the January hours (0..47) see a zero shift
        self.assertEqual(mc[row[f"{zone}_DSW_CCGT"], 0], 99.0)


if __name__ == "__main__":
    unittest.main()
