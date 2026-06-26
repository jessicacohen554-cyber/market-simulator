"""Tests for the Manitoba Hydro firm-hydro import block (MISO-North).

Manitoba Hydro sells ~10-15 TWh/yr of FIRM contracted hydro into MISO-North —
MISO's single largest import source and the structural reason MISO is a net
importer. It sits OUTSIDE the gas-margin reference-price seam, so it is a
SEPARATE import block priced as firm hydro (a low, near-constant offer) landed
directly in MISO-North and floored as must-flow baseload:

* :func:`build_miso_firm_imports` returns the block as a ``fuel_type="import"``
  pseudo-generator (counted as net interchange, not in-state generation).
* :func:`inject_miso_firm_imports` floors it as must-flow firm baseload via an
  hour-varying ``FleetArrays.min_gen`` lower bound.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC,
    MISO_MANITOBA_FIRM_IMPORT_MW,
    MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR,
    MISO_MANITOBA_FIRM_IMPORT_OFFER,
    MISO_MANITOBA_FIRM_IMPORT_ZONE,
    resolve_miso_firm_imports,
    resolve_miso_manitoba_firm_import_mw,
)
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.transmission import (
    _miso_firm_import_uid,
    build_miso_firm_imports,
    inject_miso_firm_imports,
)

T = 24


def _fa():
    """A MISO-North gas_cc plus the Manitoba firm-hydro import row; 24 h."""
    return FleetArrays(
        pmax=np.array([500.0, MISO_MANITOBA_FIRM_IMPORT_MW]),
        pmin=np.zeros(2),
        heat_rate=np.array([7.0, 0.0]),
        vom=np.array([0.0, MISO_MANITOBA_FIRM_IMPORT_OFFER]),
        emission_rate=np.zeros(2),
        nox_rate=np.zeros(2),
        so2_rate=np.zeros(2),
        zone_idx=np.array([0, 0]),  # both in MISO-North
        fuel_type_idx=np.array([FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["import"]]),
        availability=np.ones((2, T)),
        unit_ids=["MISO-North_cc", _miso_firm_import_uid()],
        efficiency_bin=np.zeros(2, dtype=int),
        plant_code=np.zeros(2, dtype=int),
    )


class TestBuildBlock(unittest.TestCase):
    def test_miso_block_lands_in_north_as_import(self):
        gens = build_miso_firm_imports("MISO")
        self.assertEqual(len(gens), 1)
        g = gens[0]
        self.assertEqual(g.zone, MISO_MANITOBA_FIRM_IMPORT_ZONE)
        self.assertEqual(g.fuel_type, "import")  # counted as net interchange
        self.assertEqual(g.pmax_mw, MISO_MANITOBA_FIRM_IMPORT_MW)
        self.assertEqual(g.vom, MISO_MANITOBA_FIRM_IMPORT_OFFER)
        # Priced as firm hydro — low offer, well below MISO's gas-set LMP, above
        # the $0 dump floor (inframarginal, never games negative-MC credits).
        self.assertGreater(g.vom, 0.0)
        self.assertLess(g.vom, 25.0)

    def test_non_miso_empty(self):
        self.assertEqual(build_miso_firm_imports("PJM"), [])
        self.assertEqual(build_miso_firm_imports("ERCOT"), [])

    def test_volume_in_contract_band(self):
        # The firm block at constant flow delivers within Manitoba Hydro's
        # ~10-15 TWh/yr US export band (the forecast-native contract midpoint).
        twh = MISO_MANITOBA_FIRM_IMPORT_MW * 8760 / 1e6
        self.assertGreaterEqual(twh, 10.0)
        self.assertLessEqual(twh, 15.0)

    def test_forecast_uses_flat_contract_mw(self):
        # Forecast (default) keeps the flat contract midpoint regardless of year.
        for g in (
            build_miso_firm_imports("MISO")[0],
            build_miso_firm_imports("MISO", year=2024, mode="forecast")[0],
            build_miso_firm_imports("MISO", year=2099, mode="backcast")[0],
        ):
            self.assertEqual(g.pmax_mw, MISO_MANITOBA_FIRM_IMPORT_MW)

    def test_backcast_uses_measured_per_year_delivery(self):
        # Backcast overlays the measured per-year firm delivery (drought-
        # responsive: 2025 << 2023, well below the flat contract midpoint).
        for year, mw in MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR.items():
            g = build_miso_firm_imports("MISO", year=year, mode="backcast")[0]
            self.assertEqual(g.pmax_mw, mw)
            self.assertLess(g.pmax_mw, MISO_MANITOBA_FIRM_IMPORT_MW)
        self.assertLess(
            MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR[2025],
            MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR[2023],
        )

    def test_resolver_matches_build(self):
        self.assertEqual(
            resolve_miso_manitoba_firm_import_mw(2023, "backcast"),
            MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR[2023],
        )
        self.assertEqual(
            resolve_miso_manitoba_firm_import_mw(2023, "forecast"),
            MISO_MANITOBA_FIRM_IMPORT_MW,
        )
        self.assertEqual(
            resolve_miso_manitoba_firm_import_mw(None, "backcast"),
            MISO_MANITOBA_FIRM_IMPORT_MW,
        )


class TestFirmFloor(unittest.TestCase):
    def test_manitoba_firm_floor(self):
        fa = _fa()
        applied = inject_miso_firm_imports(fa, "MISO", 2023)
        self.assertTrue(applied)
        np.testing.assert_allclose(
            fa.min_gen[1, :],
            MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC * MISO_MANITOBA_FIRM_IMPORT_MW,
        )
        # The in-state gas row is untouched by the firm-import floor.
        self.assertTrue(np.all(fa.min_gen[0, :] == 0.0))

    def test_non_miso_noop(self):
        fa = _fa()
        self.assertFalse(inject_miso_firm_imports(fa, "NYISO", 2023))
        self.assertIsNone(fa.min_gen)

    def test_floor_respects_availability(self):
        fa = _fa()
        fa.availability[1, :12] = 0.5  # half-derated first 12 hours
        inject_miso_firm_imports(fa, "MISO", 2023)
        floor = MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC * MISO_MANITOBA_FIRM_IMPORT_MW
        np.testing.assert_allclose(fa.min_gen[1, :12], 0.5 * floor)
        np.testing.assert_allclose(fa.min_gen[1, 12:], floor)


class TestResolver(unittest.TestCase):
    def test_default_on_for_miso_only(self):
        self.assertTrue(resolve_miso_firm_imports(None, "MISO"))
        self.assertFalse(resolve_miso_firm_imports(None, "PJM"))
        self.assertFalse(resolve_miso_firm_imports(None, "ERCOT"))

    def test_explicit_flag_wins(self):
        self.assertFalse(resolve_miso_firm_imports(False, "MISO"))
        self.assertTrue(resolve_miso_firm_imports(True, "PJM"))


if __name__ == "__main__":
    unittest.main()
