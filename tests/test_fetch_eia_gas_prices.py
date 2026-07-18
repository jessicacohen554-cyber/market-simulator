"""Offline tests for the EIA gas-price fetcher's parse/convert/merge logic.

The network call (``_get``) is mocked; this exercises the citygate $/Mcf ->
$/MMBtu conversion, the basis = citygate - Henry Hub computation, and the merge
that preserves existing measured rows (e.g. NEISO's licensed AGT index).
"""

from __future__ import annotations

import csv
import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

_SPEC = importlib.util.spec_from_file_location(
    "fetch_eia_gas_prices",
    Path(__file__).resolve().parent.parent / "scripts" / "data" / "fetch_eia_gas_prices.py",
)
feg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(feg)


class TestCitygateBasis(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        d = Path(self._tmp.name)
        feg.GAS_DIR = d / "gas-prices"
        feg.GAS_DIR.mkdir()
        feg.BASIS_PATH = d / "gas_basis_by_iso_month.csv"
        (feg.GAS_DIR / "henry_hub_monthly.csv").write_text(
            "year,month,price_usd_mmbtu\n2024,1,3.00\n2024,2,2.50\n"
        )
        # An existing measured row that must survive the merge.
        feg.BASIS_PATH.write_text(
            "iso,year,month,hub,basis_usd_mmbtu,source\n"
            "NEISO,2024,1,Algonquin (measured),1.46,licensed\n"
        )
        # $/Mcf citygate values chosen so basis lands on $1.00 after conversion.
        feg._get = lambda route, params, key, s: [
            {"period": "2024-01", "value": "4.144"},  # /1.036 = 4.00 ; -3.00 = 1.00
            {"period": "2024-02", "value": "3.626"},  # /1.036 = 3.50 ; -2.50 = 1.00
        ]

    def tearDown(self):
        self._tmp.cleanup()

    def _rows(self):
        with feg.BASIS_PATH.open() as fh:
            return list(csv.DictReader(fh))

    def test_basis_conversion_and_value(self):
        feg.fetch_citygate("key", ["CAISO"], 2024, 0)
        caiso = {
            (int(r["year"]), int(r["month"])): float(r["basis_usd_mmbtu"])
            for r in self._rows()
            if r["iso"] == "CAISO"
        }
        self.assertAlmostEqual(caiso[(2024, 1)], 1.00, places=2)
        self.assertAlmostEqual(caiso[(2024, 2)], 1.00, places=2)

    def test_existing_measured_rows_preserved(self):
        feg.fetch_citygate("key", ["NEISO"], 2024, 0)
        rows = self._rows()
        jan = [r for r in rows if r["iso"] == "NEISO" and r["month"] == "1"]
        self.assertEqual(len(jan), 1)
        self.assertEqual(jan[0]["source"], "licensed")  # not clobbered
        self.assertAlmostEqual(float(jan[0]["basis_usd_mmbtu"]), 1.46)
        # Feb had no measured row -> EIA proxy fills it.
        feb = [r for r in rows if r["iso"] == "NEISO" and r["month"] == "2"]
        self.assertEqual(len(feb), 1)
        self.assertIn("EIA", feb[0]["source"])

    def test_start_year_filter(self):
        feg.fetch_citygate("key", ["CAISO"], 2025, 0)  # later than the data
        self.assertEqual([r for r in self._rows() if r["iso"] == "CAISO"], [])

    def test_every_iso_has_a_citygate_mapping(self):
        # Guards against an ISO config drifting out of the fetch map.
        for iso in ("CAISO", "ERCOT", "PJM", "MISO", "NYISO", "NEISO"):
            self.assertIn(iso, feg.ISO_CITYGATE)
            state, hub = feg.ISO_CITYGATE[iso]
            self.assertTrue(state.isalpha() and len(state) == 2)
            self.assertTrue(hub)


if __name__ == "__main__":
    unittest.main()
