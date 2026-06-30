"""Tests for CAISO measured-hub import pricing.

The static priced-import ladder (IMPORT_TRANCHES["CAISO"]) was re-fit against the
model's own solved price; ``caiso_import_hub_prices`` replaces it with the
measured WECC neighbor-hub LMP each tranche proxies (Mid-C / Palo Verde). See
``results/calibration/DIAGNOSIS-caiso-import-ladder-2026-06-19.md``.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import pandas as pd

import market_sim.data.eia_loader as eia_loader
from market_sim.config.interchange_config import IMPORT_TRANCHE_EF, IMPORT_ZONE
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    build_import_generators,
    inject_caiso_import_hub_prices,
)


class TestMeasuredImportHubPrices(unittest.TestCase):
    """The loader maps the measured intertie parquet to the import tranches."""

    def _write_fixture(self, tmp, year=2024, hours=48):
        rows = []
        # MALIN cheap (PNW), PALOVRDE dearer, one negative midday hour each.
        for hub, base in (("MALIN", 18.0), ("PALOVRDE", 30.0)):
            for h in range(hours):
                price = -25.0 if h % 24 == 12 else base
                rows.append({"year": year, "hour": h, "hub": hub, "price": price})
        path = tmp / "wecc_intertie_lmp_hourly_CAISO.parquet"
        pd.DataFrame(rows).to_parquet(path)
        return path

    def test_non_caiso_and_missing_file_are_none(self):
        self.assertIsNone(eia_loader.measured_import_hub_prices("PJM", 2024, 48))
        with mock.patch.object(
            eia_loader, "CALIBRATION_DIR", eia_loader.CALIBRATION_DIR / "does-not-exist"
        ):
            self.assertIsNone(eia_loader.measured_import_hub_prices("CAISO", 2024, 48))

    def test_maps_hubs_to_tranches(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write_fixture(tmp)
            with mock.patch.object(eia_loader, "CALIBRATION_DIR", tmp):
                out = eia_loader.measured_import_hub_prices("CAISO", 2024, 48)
        self.assertIsNotNone(out)
        # PNW tranches take MALIN ($18 off-peak, -$25 at hr 12); DSW take PALOVRDE.
        self.assertEqual(out["PNW_hydro_base"][0], 18.0)
        self.assertEqual(out["PNW_midC"][12], -25.0)
        self.assertEqual(out["DSW_solar_PV"][0], 30.0)
        self.assertEqual(out["DSW_CCGT"][12], -25.0)

    def test_incomplete_series_skipped(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write_fixture(tmp, hours=48)
            with mock.patch.object(eia_loader, "CALIBRATION_DIR", tmp):
                # ask for more hours than the fixture covers -> None (no partial)
                self.assertIsNone(
                    eia_loader.measured_import_hub_prices("CAISO", 2024, 8760)
                )


class TestInjectCaisoImportHubPrices(unittest.TestCase):
    """The injector overwrites the import tranche mc rows with hub price+carbon."""

    def _caiso_fleet(self, hours):
        gens = build_import_generators("CAISO", border_carbon_per_mwh=15.0)
        zone = IMPORT_ZONE["CAISO"]
        zone_names = ["NP15", zone]
        return generators_to_fleet_arrays(gens, zone_names, hours=hours), gens

    def test_no_data_is_noop(self):
        hours = 48
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 99.0)
        before = mc.copy()
        with mock.patch.object(
            eia_loader, "measured_import_hub_prices", return_value=None
        ):
            applied = inject_caiso_import_hub_prices(fa, mc, "CAISO", 2024, 35.23)
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, before)

    def test_overwrites_rows_with_hub_price_plus_carbon(self):
        hours = 48
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 99.0)
        hub = {
            "PNW_hydro_base": np.full(hours, 18.0),
            "DSW_solar_PV": np.full(hours, 30.0),
            "DSW_CCGT": np.full(hours, 40.0),
        }
        with mock.patch.object(
            eia_loader, "measured_import_hub_prices", return_value=hub
        ):
            applied = inject_caiso_import_hub_prices(fa, mc, "CAISO", 2024, 35.23)
        self.assertTrue(applied)
        zone = IMPORT_ZONE["CAISO"]
        ef = IMPORT_TRANCHE_EF["CAISO"]
        from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
        from market_sim.config.interchange_config import CAISO_IMPORT_DELIVERY_BASIS
        from market_sim.model.transmission import wecc_border_carbon_adder

        # The injector delivers each measured nodal hub price to the CAISO
        # border by adding ONLY the OATT wheeling charge — the modeled line-loss
        # markup is dropped because the hub price is now the full nodal LMP whose
        # MCL component already carries the measured loss (see the injector). The
        # border adder at carbon 35.23 would be 0.428*35.23 ~ 15.08, but the
        # injector recomputes it; assert the clean blocks pay none.
        row_by_uid = {uid: r for r, uid in enumerate(fa.unit_ids)}
        # PNW_hydro_base: EF 0 -> hub price + wheel only, no carbon, no loss markup
        _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS["PNW_hydro_base"]
        r = row_by_uid[f"{zone}_PNW_hydro_base"]
        self.assertAlmostEqual(mc[r, 0], 18.0 + wheel, places=3)
        # DSW_CCGT: EF 0.37 -> hub price + wheel + 0.37/0.428 * border
        r = row_by_uid[f"{zone}_DSW_CCGT"]
        border = wecc_border_carbon_adder(35.23)
        _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS["DSW_CCGT"]
        expected = 40.0 + wheel + border * (ef["DSW_CCGT"] / CARB_UNSPECIFIED_IMPORT_EF)
        self.assertAlmostEqual(mc[r, 0], expected, places=3)
        # A tranche with no measured series (DSW_CT) keeps its ladder mc (99).
        r = row_by_uid[f"{zone}_DSW_CT"]
        self.assertEqual(mc[r, 0], 99.0)


if __name__ == "__main__":
    unittest.main()
