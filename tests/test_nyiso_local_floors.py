"""Tests for the NYISO local self-supply and firm-import floors.

Both impose an hour-varying ``FleetArrays.min_gen`` lower bound:

* :func:`inject_nyiso_local_selfsupply` forces a cable-islanded downstate
  pocket (Long Island) to meet a forward fraction of its own load with in-zone
  dispatchable thermal generation (NYISO's LMIC / local-reliability rule).
* :func:`inject_nyiso_firm_imports` floors the cheap HQ/Ontario priced-node
  tranches as must-flow baseload.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    NYISO_FIRM_IMPORT_FLOOR_FRAC,
    NYISO_LOCAL_SELFSUPPLY_FRAC,
)
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.transmission import (
    inject_nyiso_firm_imports,
    inject_nyiso_local_selfsupply,
)

T = 24


def _fa():
    """NYC gas_cc, LI gas_st + gas_ct, and an HQ import row; lossless, 24 h."""
    return FleetArrays(
        pmax=np.array([500.0, 300.0, 200.0, 900.0]),
        pmin=np.zeros(4),
        heat_rate=np.array([7.0, 10.0, 12.0, 0.0]),
        vom=np.zeros(4),
        emission_rate=np.zeros(4),
        nox_rate=np.zeros(4),
        so2_rate=np.zeros(4),
        zone_idx=np.array([0, 1, 1, 2]),  # NYC=0, Long_Island=1, external=2
        fuel_type_idx=np.array(
            [
                FUEL_TYPE_MAP["gas_cc"],
                FUEL_TYPE_MAP["gas_st"],
                FUEL_TYPE_MAP["gas_ct"],
                FUEL_TYPE_MAP["import"],
            ]
        ),
        availability=np.ones((4, T)),
        unit_ids=["NYC_cc", "LI_st", "LI_ct", "NYISO_external_HQ_hydro"],
        efficiency_bin=np.zeros(4, dtype=int),
        plant_code=np.zeros(4, dtype=int),
    )


_ZONES = ["NYC", "Long_Island", "NYISO_external"]


class TestLocalSelfSupply(unittest.TestCase):
    def test_li_floor_meets_fraction_cheapest_first(self):
        fa = _fa()
        demand = np.zeros((3, T))
        demand[1, :] = 400.0  # Long Island load
        applied = inject_nyiso_local_selfsupply(fa, "NYISO", demand, _ZONES)
        self.assertTrue(applied)
        frac = NYISO_LOCAL_SELFSUPPLY_FRAC["Long_Island"]
        target = frac * 400.0
        # In-zone thermal floor sums to the target every hour.
        np.testing.assert_allclose(fa.min_gen[1, :] + fa.min_gen[2, :], target)
        # Cheapest-first: the gas_st (HR 10) fills before the gas_ct (HR 12).
        self.assertAlmostEqual(fa.min_gen[1, 0], min(target, 300.0))

    def test_nyc_untouched(self):
        fa = _fa()
        demand = np.zeros((3, T))
        demand[0, :] = 5000.0  # NYC load — no floor configured for NYC
        demand[1, :] = 400.0
        inject_nyiso_local_selfsupply(fa, "NYISO", demand, _ZONES)
        self.assertTrue(np.all(fa.min_gen[0, :] == 0.0))

    def test_floor_capped_at_availability(self):
        fa = _fa()
        demand = np.zeros((3, T))
        demand[1, :] = 5000.0  # demand far above LI fleet (500 MW available)
        inject_nyiso_local_selfsupply(fa, "NYISO", demand, _ZONES)
        # Never exceeds the in-zone available capacity (300 + 200).
        self.assertLessEqual(
            float(fa.min_gen[1, :].max() + fa.min_gen[2, :].max()), 500.0
        )

    def test_non_nyiso_noop(self):
        fa = _fa()
        demand = np.zeros((3, T))
        demand[1, :] = 400.0
        self.assertFalse(inject_nyiso_local_selfsupply(fa, "PJM", demand, _ZONES))
        self.assertIsNone(fa.min_gen)


class TestFirmImports(unittest.TestCase):
    def test_hq_firm_floor(self):
        fa = _fa()
        applied = inject_nyiso_firm_imports(fa, "NYISO", 2023)
        self.assertTrue(applied)
        frac = NYISO_FIRM_IMPORT_FLOOR_FRAC["HQ_hydro"]
        np.testing.assert_allclose(fa.min_gen[3, :], frac * 900.0)
        # Non-import rows are untouched by the firm-import floor.
        self.assertTrue(np.all(fa.min_gen[0, :] == 0.0))

    def test_non_nyiso_noop(self):
        fa = _fa()
        self.assertFalse(inject_nyiso_firm_imports(fa, "CAISO", 2023))
        self.assertIsNone(fa.min_gen)

    def test_composes_with_existing_min_gen(self):
        fa = _fa()
        demand = np.zeros((3, T))
        demand[1, :] = 400.0
        inject_nyiso_local_selfsupply(fa, "NYISO", demand, _ZONES)
        inject_nyiso_firm_imports(fa, "NYISO", 2023)
        # The LI floor survives the firm-import pass (different rows).
        self.assertAlmostEqual(
            float(fa.min_gen[1, 0] + fa.min_gen[2, 0]),
            NYISO_LOCAL_SELFSUPPLY_FRAC["Long_Island"] * 400.0,
        )
        self.assertAlmostEqual(float(fa.min_gen[3, 0]), 900.0)


if __name__ == "__main__":
    unittest.main()
