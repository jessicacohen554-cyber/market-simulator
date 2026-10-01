"""R-CAISO-8: partial-year measured intertie pricing, trivial cases first.

``caiso_intertie_partial_year_measured`` keeps a WECC intertie hub whose year is
more than 25 % unprinted (2021: 5,976 of 8,760 h) instead of dropping it: the
printed hours are priced at the measured hub, the unprinted hours keep the
static ladder (and, under ``caiso_import_gas_coupling_ladder_only``, the gas
coupling). Default off and byte-identical off. Record:
``docs/records/caiso/r-caiso-8/PRECOMMIT-r-caiso-8-2026-09-27.md``.
"""

from __future__ import annotations

import types
import unittest
from unittest import mock

import numpy as np
import pandas as pd

import market_sim.data.eia930.envelopes as envelopes
import market_sim.data.fuel as fuel
import market_sim.model.interchange.caiso as caiso_mod
from market_sim.config.interchange_config import IMPORT_ZONE
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _CAISO_IMPORT_COUPLE_HR,
    build_import_generators,
    inject_caiso_import_gas_coupling,
)

HOURS = 8760
PRINT_FROM = 3000  # hours [0, 3000) unprinted: a 34 % gap, over the 25 % bound


def _frame(year: int, gap_hours: int) -> pd.DataFrame:
    rows = [
        (year, h, hub, np.nan if h < gap_hours else 50.0)
        for hub in ("MALIN", "PALOVRDE")
        for h in range(HOURS)
    ]
    return pd.DataFrame(rows, columns=["year", "hour", "hub", "price"])


def _prices(flag: bool, gap_hours: int = PRINT_FROM):
    with (
        mock.patch.object(
            envelopes.pd, "read_parquet", return_value=_frame(2021, gap_hours)
        ),
        mock.patch.object(envelopes.Path, "exists", return_value=True),
    ):
        return envelopes.measured_import_hub_prices(
            "CAISO", 2021, HOURS, partial_year_measured=flag
        )


class TestLoader(unittest.TestCase):
    def test_off_drops_a_mostly_unprinted_year(self):
        self.assertIsNone(_prices(False))

    def test_on_keeps_printed_hours_and_leaves_gap_nan(self):
        out = _prices(True)
        self.assertIsNotNone(out)
        series = out["DSW_CCGT"]
        self.assertTrue(np.all(np.isnan(series[: PRINT_FROM - 2])))
        self.assertTrue(np.all(series[PRINT_FROM:] == 50.0))
        self.assertIn("PNW_midC", out)

    def test_fully_unprinted_year_is_all_nan(self):
        out = _prices(True, gap_hours=HOURS)
        self.assertTrue(np.all(np.isnan(out["DSW_CCGT"])))


class TestInjector(unittest.TestCase):
    """The per-hub injector writes printed hours only; unprinted keep the ladder."""

    def _run(self, flag: bool, hub_prices):
        hours = 4
        gens = build_import_generators("CAISO", border_carbon_per_mwh=0.0)
        zone = IMPORT_ZONE["CAISO"]
        fa = generators_to_fleet_arrays(gens, ["NP15", zone], hours=hours)
        # Re-key the pooled import rows onto the south per-hub corridor.
        fa.unit_ids = [u.replace(f"{zone}_", "WECC_DSW_") for u in fa.unit_ids]
        mc = np.full((len(fa.unit_ids), hours), 99.0)
        with mock.patch(
            "market_sim.data.eia_loader.measured_import_hub_prices",
            return_value=hub_prices,
        ):
            applied = caiso_mod.inject_caiso_per_hub_intertie_prices(
                fa, mc, "CAISO", 2021, 0.0, partial_year_measured=flag
            )
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        return applied, mc[row["WECC_DSW_DSW_CCGT"]]

    def test_on_prices_printed_hours_only(self):
        hub = np.array([np.nan, np.nan, 40.0, 41.0])
        applied, out = self._run(True, {"DSW_CCGT": hub})
        self.assertTrue(applied)
        self.assertEqual(out[0], 99.0)
        self.assertEqual(out[1], 99.0)
        self.assertGreater(out[2], 40.0)
        self.assertLess(out[2], 99.0)
        self.assertAlmostEqual(out[3] - out[2], 1.0, places=9)

    def test_off_with_a_full_series_is_the_incumbent_write(self):
        hub = np.array([40.0, 41.0, 42.0, 43.0])
        _, on = self._run(True, {"DSW_CCGT": hub})
        _, off = self._run(False, {"DSW_CCGT": hub})
        np.testing.assert_array_equal(on, off)


class TestGasCouplingPerHour(unittest.TestCase):
    """Under ladder-only coupling the unprinted hours keep the coupling."""

    def _run(self, partial: bool, hub):
        hours = 4
        gens = build_import_generators("CAISO", border_carbon_per_mwh=15.0)
        zone = IMPORT_ZONE["CAISO"]
        fa = generators_to_fleet_arrays(gens, ["NP15", zone], hours=hours)
        mc = np.full((len(gens), hours), 99.0)
        cfg = types.SimpleNamespace(
            iso="CAISO",
            caiso_import_gas_coupling=True,
            caiso_import_gas_coupling_ladder_only=True,
            caiso_per_hub_intertie=True,
            caiso_intertie_reference_price=False,
            caiso_perhub_firm_base=True,
            caiso_import_hub_prices=False,
            caiso_intertie_gap_fill_measured_gas=False,
            caiso_intertie_gap_fill_measured_dam=False,
            caiso_intertie_partial_year_measured=partial,
        )
        with (
            mock.patch.object(
                fuel, "iso_hub_monthly_gas_prices", return_value=np.full(12, 3.0)
            ),
            mock.patch.object(
                fuel, "iso_monthly_gas_prices", return_value=np.full(12, 4.0)
            ),
            mock.patch(
                "market_sim.data.eia_loader.measured_import_hub_prices",
                return_value={"DSW_CCGT": hub, "DSW_CT": hub},
            ),
        ):
            inject_caiso_import_gas_coupling(fa, mc, cfg, 2021)
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        return mc[row[f"{zone}_DSW_CCGT"]]

    def test_partial_hub_couples_unprinted_hours_only(self):
        hub = np.array([np.nan, np.nan, 40.0, 41.0])
        out = self._run(True, hub)
        hr = _CAISO_IMPORT_COUPLE_HR["DSW_CCGT"]
        np.testing.assert_allclose(out, [99.0 - hr, 99.0 - hr, 99.0, 99.0])

    def test_full_hub_is_skipped_either_way(self):
        hub = np.array([40.0, 41.0, 42.0, 43.0])
        np.testing.assert_array_equal(self._run(True, hub), np.full(4, 99.0))
        np.testing.assert_array_equal(self._run(False, hub), np.full(4, 99.0))


class TestCommittedSeries(unittest.TestCase):
    """On the committed hub parquet only 2021 changes."""

    def test_only_2021_moves(self):
        for year in (2019, 2020, 2022, 2023, 2024, 2025):
            off = envelopes.measured_import_hub_prices("CAISO", year, HOURS)
            on = envelopes.measured_import_hub_prices(
                "CAISO", year, HOURS, partial_year_measured=True
            )
            if off is None:
                self.assertIsNone(on, year)
                continue
            self.assertEqual(set(off), set(on), year)
            for name in off:
                np.testing.assert_array_equal(off[name], on[name])

    def test_2021_prints_its_measured_hours(self):
        self.assertIsNone(envelopes.measured_import_hub_prices("CAISO", 2021, HOURS))
        on = envelopes.measured_import_hub_prices(
            "CAISO", 2021, HOURS, partial_year_measured=True
        )
        self.assertIsNotNone(on)
        # 5,976 printed hours (May-Dec); limit=2 interpolation adds none at the
        # bulk-gap edge beyond the two hours it may bridge.
        printed = int(np.isfinite(on["DSW_CCGT"]).sum())
        self.assertGreaterEqual(printed, 5976)
        self.assertLessEqual(printed, 5978)


class TestField(unittest.TestCase):
    def test_default_off(self):
        self.assertFalse(
            ScenarioConfig(iso="CAISO").caiso_intertie_partial_year_measured
        )


if __name__ == "__main__":
    unittest.main()
