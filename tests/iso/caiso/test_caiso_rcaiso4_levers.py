"""R-CAISO-4: the two measured-input repairs, trivial cases first.

``caiso_intertie_gap_fill_measured_dam`` fills the intertie hub's retention gap
from the measured DAM prints of the sibling gap-fill artifact before any formula
fill; ``cc_eia923_identity_emission_basis`` re-bases an EIA-923-identity CC's
CO2 onto that same fuel basis. Both default off and byte-identical off. Record:
``docs/handoffs/r-caiso-4/PRECOMMIT-r-caiso-4-2026-09-26.md``.
"""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import market_sim.data.eia930 as eia930_pkg
import market_sim.data.eia930.envelopes as envelopes
from market_sim.data.fleet import campd_bins

_H = 24


def _write_intertie(d: Path, gap_hours: range, fill_hours: range | None) -> None:
    """Main series with NaN at ``gap_hours``; sibling fill at ``fill_hours``."""
    rows = []
    for hub in ("MALIN", "PALOVRDE"):
        for h in range(_H):
            rows.append(
                {
                    "year": 2023,
                    "hour": h,
                    "hub": hub,
                    "price": np.nan if h in gap_hours else 50.0,
                }
            )
    pd.DataFrame(rows).to_parquet(d / "wecc_intertie_lmp_hourly_CAISO.parquet")
    if fill_hours is not None:
        frows = [
            {"year": 2023, "hour": h, "hub": hub, "price": 7.0}
            for hub in ("MALIN", "PALOVRDE")
            for h in list(fill_hours) + [0]  # hour 0 is printed: never overwritten
        ]
        pd.DataFrame(frows).to_parquet(
            d / "wecc_intertie_lmp_hourly_CAISO_gapfill_dam.parquet"
        )


class TestDamGapFill(unittest.TestCase):
    """The raw loader fills NaN hours from the sibling artifact, only when armed."""

    def _raw(self, d: Path, armed: bool) -> np.ndarray:
        with mock.patch.object(eia930_pkg, "CALIBRATION_DIR", d):
            return envelopes.measured_intertie_hub_price_raw(
                "CAISO", 2023, _H, "MALIN", gap_fill_measured_dam=armed
            )

    def test_off_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _write_intertie(d, range(5, 15), range(5, 10))
            off = self._raw(d, armed=False)
            # interpolate(limit=2) reaches two hours into a run; the rest stays NaN
            self.assertTrue(np.isnan(off[7:15]).all())
            self.assertTrue((off[:5] == 50.0).all())

    def test_armed_fills_only_gap_hours(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _write_intertie(d, range(5, 15), range(5, 10))
            on = self._raw(d, armed=True)
            np.testing.assert_array_equal(on[5:10], 7.0)
            self.assertTrue(np.isnan(on[12:15]).all())  # unprinted hours stay NaN
            self.assertEqual(on[0], 50.0)  # a printed hour is never overwritten

    def test_missing_sibling_is_identity(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            _write_intertie(d, range(5, 15), None)
            np.testing.assert_array_equal(
                self._raw(d, armed=True), self._raw(d, armed=False)
            )


def _gen(code: int, group: str) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        plant_code=code,
        fuel_type="gas",
        plant_group=group,
        ccs_capture_fraction=0.0,
        emission_rate_co2=0.0,
        nox_rate=0.0,
        so2_rate=0.0,
    )


class TestIdentityEmissionBasis(unittest.TestCase):
    """An eia923_identity CC_REGULAR's CO2 = identity HR x CEMS CO2/MMBtu, armed only."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        pd.DataFrame(
            {
                "plant_code": [1, 2],
                "year": [0, 0],
                "heat_rate": [7.0, 7.2],
                "flag": ["eia923_identity", "ok"],
            }
        ).to_csv(d / "campd_cc_heat_rates_CAISO.csv", index=False)
        self.v2 = d / "v2.parquet"
        pd.DataFrame(
            {
                "iso": ["CAISO", "CAISO"],
                "plant_id": [1, 2],
                "unit_id": ["a", "b"],
                "year": [2023, 2023],
                "primary_fuel": ["Pipeline Natural Gas"] * 2,
                "net_mwh": [1000.0, 1000.0],
                "heat_mmbtu": [8000.0, 7200.0],  # plant 1 CEMS reads 8.0 / MWh
                "co2_kg": [8000.0 * 53.9, 7200.0 * 53.9],
                "co2_kg_per_mwh_net": [431.2, 388.08],
                "nox_kg_per_mwh_net": [0.0, 0.0],
                "so2_kg_per_mwh_net": [0.0, 0.0],
            }
        ).to_parquet(self.v2)
        self.patch = mock.patch.object(campd_bins, "PROCESSED_DIR", d)
        self.patch.start()
        for fn in (
            campd_bins.measured_cc_identity_heat_rates,
            campd_bins._plant_gas_co2_per_mmbtu,
            campd_bins._measured_plant_rate_map_v2,
        ):
            fn.cache_clear()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def _apply(self, armed: bool) -> list:
        gens = [_gen(1, "CC_REGULAR"), _gen(1, "CT_PEAKER"), _gen(2, "CC_REGULAR")]
        cfg = types.SimpleNamespace(
            cc_eia923_identity_emission_basis=armed,
            measured_cc_heat_rates=True,
            hindcast=False,
            is_full_forward_hindcast=False,
        )
        with mock.patch(
            "market_sim.data.emission_rates.measured_plant_rates",
            side_effect=lambda df, iso, year, mode, pollutant, **kw: (
                {(1, "gas"): 0.4312, (2, "gas"): 0.38808} if pollutant == "co2" else {}
            ),
        ):
            campd_bins.apply_plant_emission_rates_v2(
                gens, self.v2, iso="CAISO", year=2023, mode="backcast", config=cfg
            )
        return [g.emission_rate_co2 for g in gens]

    def test_identity_map(self):
        self.assertEqual(
            campd_bins.measured_cc_identity_heat_rates("CAISO", 2023), {1: 7.0}
        )

    def test_off_keeps_cems_rate(self):
        self.assertEqual(self._apply(False), [0.4312, 0.4312, 0.38808])

    def test_armed_rebases_identity_cc_only(self):
        cc1, ct1, cc2 = self._apply(True)
        self.assertAlmostEqual(cc1, 7.0 * 0.0539, places=6)
        self.assertEqual(ct1, 0.4312)  # another class at the same plant: untouched
        self.assertEqual(cc2, 0.38808)  # an ``ok`` row: untouched


if __name__ == "__main__":
    unittest.main()
