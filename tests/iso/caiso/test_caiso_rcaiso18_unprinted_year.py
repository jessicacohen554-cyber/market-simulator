"""R-CAISO-18: measured-gas pricing of a >25 %-unprinted WECC intertie hub year.

``caiso_intertie_unprinted_year_measured_gas`` prices the unprinted hours of a
hub whose gap exceeds the 25 % bound (2019-2020 entirely; Jan-Apr 2021) on the
measured-gas reference formula, with the host state's N3045 rebuilt from its
own EIA-923 receipts where EIA withholds it. Default off and byte-identical
off; inert in 2022-2025 on. Trivial cases first. Record:
``docs/handoffs/r-caiso-18/PRECOMMIT-r-caiso-18-2026-09-30.md``.
"""

from __future__ import annotations

import types
import unittest
from unittest import mock

import numpy as np
import pandas as pd

import market_sim.data.eia930.envelopes as envelopes
import market_sim.data.neighbor_price as neighbor_price
from market_sim.config.interchange_config import CAISO_PER_HUB_NEIGHBORS
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel.electric_power import (
    state_electric_power_monthly_gas_eia923,
)
from market_sim.model.interchange.caiso import _caiso_measured_hub_unprinted_masks

HOURS = 8760
KW = dict(
    gap_fill_measured_gas=True, gap_fill_measured_dam=True, partial_year_measured=True
)


class TestEia923Rebuild(unittest.TestCase):
    """Quantity-weighted monthly delivered gas of one state's plants."""

    def test_two_plants_one_month(self):
        frame = pd.DataFrame(
            {
                "year": [2019, 2019, 2019, 2019],
                "month": [1, 1, 1, 2],
                "plant_id": [1, 2, 3, 1],
                "state": ["AZ", "AZ", "OR", "AZ"],
                "fuel_group": ["Natural Gas", "Natural Gas", "Natural Gas", "Coal"],
                "price_per_mmbtu": [2.0, 4.0, 9.0, 1.0],
                "quantity": [3.0, 1.0, 5.0, 7.0],
            }
        )
        with (
            mock.patch.object(pd, "read_parquet", return_value=frame),
            mock.patch(
                "market_sim.data.fuel.electric_power.Path.exists", return_value=True
            ),
        ):
            out = state_electric_power_monthly_gas_eia923("AZ", 2019)
        self.assertAlmostEqual(out[0], (2.0 * 3 + 4.0 * 1) / 4)
        self.assertTrue(np.all(np.isnan(out[1:])))  # coal row and other months ignored

    def test_committed_az_covers_the_withheld_years(self):
        for year in (2019, 2020, 2021):
            out = state_electric_power_monthly_gas_eia923("AZ", year)
            self.assertIsNotNone(out, year)
            self.assertTrue(np.all(np.isfinite(out)), year)


class TestFormulaFallback(unittest.TestCase):
    """The EIA-923 rebuild fills only months N3045 does not print."""

    def _spec(self):
        return next(s for s in CAISO_PER_HUB_NEIGHBORS.values() if s.hub == "PALOVRDE")

    def test_printed_month_is_never_replaced(self):
        n3045 = np.array([5.0] + [np.nan] * 11)
        rebuilt = np.full(12, 2.0)
        with (
            mock.patch(
                "market_sim.data.fuel.electric_power.state_electric_power_monthly_gas",
                return_value=n3045,
            ),
            mock.patch(
                "market_sim.data.fuel.electric_power.state_electric_power_monthly_gas_eia923",
                return_value=rebuilt,
            ),
            mock.patch.object(
                neighbor_price, "caiso_hub_load_shape", return_value=np.ones(48)
            ),
        ):
            spec = self._spec()
            off = neighbor_price.caiso_hub_measured_gas_reference_price(spec, 2019, 48)
            on = neighbor_price.caiso_hub_measured_gas_reference_price(
                spec, 2019, 48, eia923_fallback=True
            )
        hr = spec.marginal_heat_rate
        np.testing.assert_allclose(off, np.full(48, 5.0 * hr))  # 48 h all January
        np.testing.assert_allclose(on, off)

    def test_off_returns_none_when_n3045_absent(self):
        spec = self._spec()
        self.assertIsNone(
            neighbor_price.caiso_hub_measured_gas_reference_price(spec, 2020, HOURS)
        )
        on = neighbor_price.caiso_hub_measured_gas_reference_price(
            spec, 2020, HOURS, eia923_fallback=True
        )
        self.assertTrue(np.all(np.isfinite(on)))


class TestLoaderSynthetic(unittest.TestCase):
    """A >25 % gap is filled on the flag; off it keeps the R-CAISO-8 behaviour."""

    def _frame(self, year, gap_hours):
        rows = [
            (year, h, hub, np.nan if h < gap_hours else 50.0)
            for hub in ("MALIN", "PALOVRDE")
            for h in range(HOURS)
        ]
        return pd.DataFrame(rows, columns=["year", "hour", "hub", "price"])

    def _prices(self, flag, frame, year=2021):
        with (
            mock.patch.object(envelopes.pd, "read_parquet", return_value=frame),
            mock.patch.object(envelopes.Path, "exists", return_value=True),
            mock.patch.object(
                neighbor_price,
                "caiso_hub_measured_gas_reference_price",
                return_value=np.full(HOURS, 30.0),
            ),
        ):
            return envelopes.measured_import_hub_prices(
                "CAISO",
                year,
                HOURS,
                partial_year_measured=True,
                unprinted_year_measured_gas=flag,
            )

    def test_gap_filled_printed_kept(self):
        on = self._prices(True, self._frame(2021, 3000))["DSW_CCGT"]
        self.assertTrue(np.all(on[:2998] == 30.0))
        self.assertTrue(np.all(on[3000:] == 50.0))
        off = self._prices(False, self._frame(2021, 3000))["DSW_CCGT"]
        self.assertTrue(np.all(np.isnan(off[:2998])))

    def test_year_absent_from_extract(self):
        empty = self._frame(2021, 0).iloc[0:0]
        self.assertIsNone(self._prices(False, empty, year=2019))
        on = self._prices(True, empty, year=2019)
        self.assertEqual(set(on), set(envelopes._CAISO_IMPORT_TRANCHE_HUB))
        self.assertTrue(np.all(on["DSW_CT"] == 30.0))


class TestCommittedSeries(unittest.TestCase):
    """On the committed hub parquet 2022-2025 are byte-identical; 2019-2021 fill."""

    def test_2022_2025_identical(self):
        for year in (2022, 2023, 2024, 2025):
            off = envelopes.measured_import_hub_prices("CAISO", year, HOURS, **KW)
            on = envelopes.measured_import_hub_prices(
                "CAISO", year, HOURS, unprinted_year_measured_gas=True, **KW
            )
            self.assertEqual(set(off), set(on), year)
            for name in off:
                np.testing.assert_array_equal(off[name], on[name])

    def test_2019_2021_fully_priced(self):
        for year in (2019, 2020, 2021):
            on = envelopes.measured_import_hub_prices(
                "CAISO", year, HOURS, unprinted_year_measured_gas=True, **KW
            )
            self.assertTrue(np.all(np.isfinite(on["DSW_CCGT"])), year)
            self.assertTrue(np.all(np.isfinite(on["PNW_midC"])), year)
        self.assertIsNone(
            envelopes.measured_import_hub_prices("CAISO", 2019, HOURS, **KW)
        )


class TestCouplingMask(unittest.TestCase):
    """The gas-coupling mask sees the filled hours as hub-priced (no double count)."""

    def _cfg(self, flag):
        return types.SimpleNamespace(
            iso="CAISO",
            caiso_per_hub_intertie=True,
            caiso_intertie_reference_price=False,
            caiso_import_hub_prices=False,
            caiso_perhub_firm_base=True,
            caiso_intertie_gap_fill_measured_gas=True,
            caiso_intertie_gap_fill_measured_dam=True,
            caiso_intertie_partial_year_measured=True,
            caiso_intertie_unprinted_year_measured_gas=flag,
        )

    def test_2019(self):
        self.assertEqual(
            _caiso_measured_hub_unprinted_masks(self._cfg(False), 2019, HOURS), {}
        )
        on = _caiso_measured_hub_unprinted_masks(self._cfg(True), 2019, HOURS)
        self.assertIn("DSW_CCGT", on)
        self.assertIsNone(on["DSW_CCGT"])  # hub-priced in every hour


class TestField(unittest.TestCase):
    def test_default_off(self):
        self.assertFalse(
            ScenarioConfig(iso="CAISO").caiso_intertie_unprinted_year_measured_gas
        )


if __name__ == "__main__":
    unittest.main()
