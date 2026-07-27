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

from market_sim.config.constants import NYISO_LOCAL_SELFSUPPLY_FRAC
from market_sim.config.interchange_config import NYISO_FIRM_IMPORT_FLOOR_FRAC
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.model.transmission import (
    NYISO_SELFSUPPLY_FLOOR_HOURS,
    inject_nyiso_firm_imports,
    inject_nyiso_local_selfsupply,
)

T = 24
_ON = NYISO_SELFSUPPLY_FLOOR_HOURS[0]  # an in-window hour (HB14-21)
_OFF = 0  # an out-of-window (overnight) hour


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
        # In-zone thermal floor sums to the target in the peak window, 0 outside.
        in_window = np.isin(np.arange(T), np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
        summed = fa.min_gen[1, :] + fa.min_gen[2, :]
        np.testing.assert_allclose(summed[in_window], target)
        np.testing.assert_allclose(summed[~in_window], 0.0)
        # Cheapest-first: the gas_st (HR 10) fills before the gas_ct (HR 12).
        self.assertAlmostEqual(fa.min_gen[1, _ON], min(target, 300.0))

    def test_overnight_hours_unfloored(self):
        """The narrowed floor no longer force-commits overnight (rule-17)."""
        fa = _fa()
        demand = np.zeros((3, T))
        demand[1, :] = 400.0
        inject_nyiso_local_selfsupply(fa, "NYISO", demand, _ZONES)
        # Every out-of-window hour carries no self-supply floor on the LI rows.
        self.assertAlmostEqual(float(fa.min_gen[1, _OFF] + fa.min_gen[2, _OFF]), 0.0)

    def test_floor_prefers_gas_over_cheaper_heatrate_oil(self):
        """A low-heat-rate OIL peaker is floored only after gas is exhausted.

        Distillate costs ~5x gas/MMBtu, so the self-supply floor must fill the
        in-zone GAS fleet first even when an oil unit has a lower heat rate —
        otherwise the LP force-commits oil for a summer reliability minimum
        (the flat year-round LI oil bug). Here LI has a gas_ct (HR 11) and an
        oil unit (HR 9); the gas unit must take the whole floor.
        """
        fa = _fa()
        # Swap LI rows to gas_ct (HR 11, 300 MW) and oil (HR 9, 300 MW).
        fa.heat_rate = np.array([7.0, 11.0, 9.0, 0.0])
        fa.fuel_type_idx = np.array(
            [
                FUEL_TYPE_MAP["gas_cc"],
                FUEL_TYPE_MAP["gas_ct"],
                FUEL_TYPE_MAP["oil"],
                FUEL_TYPE_MAP["import"],
            ]
        )
        fa.pmax = np.array([500.0, 300.0, 300.0, 900.0])
        demand = np.zeros((3, T))
        demand[1, :] = 400.0
        inject_nyiso_local_selfsupply(fa, "NYISO", demand, _ZONES)
        target = NYISO_LOCAL_SELFSUPPLY_FRAC["Long_Island"] * 400.0
        # Gas (row 1) carries the entire floor (target < its 300 MW); oil (row 2)
        # stays at zero despite its lower heat rate. Checked in the peak window.
        self.assertAlmostEqual(fa.min_gen[1, _ON], min(target, 300.0))
        self.assertAlmostEqual(fa.min_gen[2, _ON], max(0.0, target - 300.0))

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
        # The LI floor survives the firm-import pass (different rows), checked in
        # the peak window; the firm-import floor is all-hours.
        self.assertAlmostEqual(
            float(fa.min_gen[1, _ON] + fa.min_gen[2, _ON]),
            NYISO_LOCAL_SELFSUPPLY_FRAC["Long_Island"] * 400.0,
        )
        self.assertAlmostEqual(float(fa.min_gen[3, _ON]), 900.0)


if __name__ == "__main__":
    unittest.main()
