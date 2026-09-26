"""R-CAISO-3: the two import-gas repairs, trivial cases first.

``caiso_import_gas_coupling_ladder_only`` skips the gas coupling on tranches a
measured hub series has repriced; ``caiso_intertie_gap_fill_measured_gas`` fills
the intertie hub's bulk retention gap on the host state's measured monthly gas.
Both default off and byte-identical off. Record:
``docs/handoffs/r-caiso-3/PRECOMMIT-r-caiso-3-2026-09-25.md``.
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
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.interchange.spec import (
    CAISO_INTERTIE_HUB_GAS_STATE,
    CAISO_PER_HUB_NEIGHBORS,
)
from market_sim.model.transmission import (
    _CAISO_IMPORT_COUPLE_HR,
    build_import_generators,
    inject_caiso_import_gas_coupling,
)


def _cfg(**kw):
    base = dict(
        iso="CAISO",
        caiso_import_gas_coupling=True,
        caiso_per_hub_intertie=True,
        caiso_intertie_reference_price=False,
        caiso_perhub_firm_base=True,
        caiso_import_hub_prices=False,
        caiso_intertie_gap_fill_measured_gas=False,
    )
    base.update(kw)
    return types.SimpleNamespace(**base)


class TestLadderOnlyCoupling(unittest.TestCase):
    """The coupling skips hub-priced tranches only when the flag is on."""

    def _run(self, config, hub_prices):
        hours = 48
        gens = build_import_generators("CAISO", border_carbon_per_mwh=15.0)
        zone = IMPORT_ZONE["CAISO"]
        fa = generators_to_fleet_arrays(gens, ["NP15", zone], hours=hours)
        mc = np.full((len(gens), hours), 99.0)
        with (
            mock.patch.object(
                fuel, "iso_hub_monthly_gas_prices", return_value=np.full(12, 3.0)
            ),
            mock.patch.object(
                fuel, "iso_monthly_gas_prices", return_value=np.full(12, 4.0)
            ),
            mock.patch.object(
                caiso_mod,
                "_caiso_measured_hub_priced_tranches",
                wraps=caiso_mod._caiso_measured_hub_priced_tranches,
            ),
            mock.patch(
                "market_sim.data.eia_loader.measured_import_hub_prices",
                return_value=hub_prices,
            ),
        ):
            inject_caiso_import_gas_coupling(fa, mc, config, 2024)
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        return {tr: mc[row[f"{zone}_{tr}"], 0] for tr in _CAISO_IMPORT_COUPLE_HR}

    def test_flag_off_is_the_incumbent_shift(self):
        out = self._run(_cfg(), {"DSW_CCGT": np.zeros(48), "DSW_CT": np.zeros(48)})
        for tr, hr in _CAISO_IMPORT_COUPLE_HR.items():
            self.assertAlmostEqual(out[tr], 99.0 - hr, places=4)

    def test_flag_on_skips_hub_priced_keeps_ladder(self):
        hubs = {name: np.zeros(48) for name in ("DSW_solar_PV", "DSW_CCGT", "DSW_CT")}
        out = self._run(_cfg(caiso_import_gas_coupling_ladder_only=True), hubs)
        self.assertEqual(out["DSW_CCGT"], 99.0)
        self.assertEqual(out["DSW_CT"], 99.0)
        # DSW_solar_PV is a firm static-ladder block under caiso_perhub_firm_base:
        # the per-hub injector never reprices it, so it keeps the coupling.
        self.assertAlmostEqual(
            out["DSW_solar_PV"],
            99.0 - _CAISO_IMPORT_COUPLE_HR["DSW_solar_PV"],
            places=4,
        )

    def test_flag_on_without_measured_series_is_unchanged(self):
        out = self._run(_cfg(caiso_import_gas_coupling_ladder_only=True), None)
        for tr, hr in _CAISO_IMPORT_COUPLE_HR.items():
            self.assertAlmostEqual(out[tr], 99.0 - hr, places=4)

    def test_forward_reference_seam_is_not_hub_priced(self):
        cfg = _cfg(
            caiso_import_gas_coupling_ladder_only=True,
            caiso_intertie_reference_price=True,
        )
        self.assertEqual(
            caiso_mod._caiso_measured_hub_priced_tranches(cfg, 2024, 48), frozenset()
        )


class TestGapFillMeasuredGas(unittest.TestCase):
    """The retention-gap fill rides the host state's measured gas when armed."""

    def _frame(self, year, gap_hours):
        rows = []
        for hub in ("MALIN", "PALOVRDE"):
            for h in range(8760):
                rows.append((year, h, hub, np.nan if h < gap_hours else 50.0))
        return pd.DataFrame(rows, columns=["year", "hour", "hub", "price"])

    def _prices(self, flag):
        frame = self._frame(2023, 744)  # January missing
        shape = np.ones(8760)
        state_gas = np.full(12, 2.0)
        state_gas[0] = 20.0  # a January spike in the measured state series
        with (
            mock.patch.object(envelopes.pd, "read_parquet", return_value=frame),
            mock.patch.object(envelopes.Path, "exists", return_value=True),
            mock.patch(
                "market_sim.data.neighbor_price.caiso_hub_load_shape",
                return_value=shape,
            ),
            mock.patch(
                "market_sim.data.fuel.electric_power.state_electric_power_monthly_gas",
                return_value=state_gas,
            ),
        ):
            return envelopes.measured_import_hub_prices(
                "CAISO", 2023, 8760, gap_fill_measured_gas=flag
            )

    def test_off_keeps_forward_fill_and_measured_hours(self):
        out = self._prices(False)
        self.assertEqual(out["DSW_CCGT"][800], 50.0)
        hr = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"].marginal_heat_rate
        self.assertLess(out["DSW_CCGT"][0], 20.0 * hr)  # forward HH, no spike

    def test_on_fills_gap_from_measured_state_gas_only(self):
        out = self._prices(True)
        hr = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"].marginal_heat_rate
        self.assertAlmostEqual(out["DSW_CCGT"][0], 20.0 * hr, places=6)
        self.assertEqual(out["DSW_CCGT"][800], 50.0)  # measured hour untouched
        hr_pnw = CAISO_PER_HUB_NEIGHBORS["WECC_PNW"].marginal_heat_rate
        self.assertAlmostEqual(out["PNW_midC"][0], 20.0 * hr_pnw, places=6)

    def test_hub_state_crosswalk(self):
        self.assertEqual(
            CAISO_INTERTIE_HUB_GAS_STATE, {"PALOVRDE": "AZ", "MALIN": "OR"}
        )


class TestStateGasHelper(unittest.TestCase):
    def test_reads_committed_series_in_mmbtu(self):
        from market_sim.data.fuel.electric_power import (
            MCF_TO_MMBTU,
            state_electric_power_monthly_gas,
        )

        az = state_electric_power_monthly_gas("AZ", 2022)
        self.assertIsNotNone(az)
        self.assertAlmostEqual(az[11], 18.65 / MCF_TO_MMBTU, places=6)
        self.assertIsNone(state_electric_power_monthly_gas("AZ", 1990))


if __name__ == "__main__":
    unittest.main()
