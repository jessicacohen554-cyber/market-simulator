"""Validation of the MISO merchant-CC EcoMin online floor (miso-286).

Covers :func:`market_sim.pipeline.commitment.build_miso_gas_ecomin_p1_prep` and
:func:`market_sim.pipeline.commitment._miso_gas_ecomin_floor`. Contract:

* flag off / non-MISO ⇒ ``None`` (byte-identical P1);
* trivial case first: one CC committed tranche, 24 h — floored at
  ``min(frac × plant_pmax, tranche pmax) × availability`` in exactly the hours
  its P0 dispatch is above the detector's 5 % run threshold, zero elsewhere;
* no gap-bridge: an idle gap shorter than min-down is NOT floored (the
  window is the online hours only, charter §2);
* eligibility by physics: incremental tranches (startup 0), CHP rows and
  non-gas_cc fuels are never floored (rules 18 / 19);
* D-2 attribution tags floored gen-hours ``MECH_MISO_GAS_ECOMIN_ONLINE``;
* arming it together with ``miso_coal_night_floor`` is refused (one P1 slot).
"""

import unittest

import numpy as np

from market_sim.config.constants import MISO_GAS_ECOMIN_MIN_LOAD_FRAC
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_MISO_GAS_ECOMIN_ONLINE,
    MECH_NAMES,
    assert_ablation_coverage,
)
from market_sim.pipeline.commitment import (
    _bridge_floored_fleet,
    _miso_gas_ecomin_floor,
    build_miso_gas_ecomin_p1_prep,
)

_T = 24


def _cc(
    unit_id="P55000_committed",
    pmax=200.0,
    startup=40.0,
    group="CC_REGULAR",
    heat_rate=7.2,
):
    """A CC CAMPD tranche; the committed band carries a startup cost."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="z",
        fuel_type="gas_cc",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
        is_campd_bin=True,
        plant_group=group,
        startup_cost_per_mw=startup,
        plant_code=55000,
    )


class TestTrivialOneGen(unittest.TestCase):
    """1 gen, 1 zone, 24 h."""

    def test_floor_only_in_online_hours(self):
        gens = [_cc()]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        disp = np.zeros((1, _T))
        disp[0, 6:18] = 150.0  # online h6-17
        floor = _miso_gas_ecomin_floor(gens, fa, disp, 0.5)
        self.assertIsNotNone(floor)
        # plant pmax = 200 (single tranche), target = min(0.5*200, 200) = 100
        np.testing.assert_allclose(floor[0, 6:18], 100.0)
        self.assertEqual(float(floor[0, :6].sum() + floor[0, 18:].sum()), 0.0)

    def test_short_gap_not_bridged(self):
        gens = [_cc()]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        disp = np.zeros((1, _T))
        disp[0, 2:8] = 150.0
        disp[0, 9:20] = 150.0  # 1 h gap at h8, shorter than any CC min-down
        floor = _miso_gas_ecomin_floor(gens, fa, disp, 0.5)
        self.assertEqual(float(floor[0, 8]), 0.0)
        self.assertTrue(np.all(floor[0, 2:8] > 0) and np.all(floor[0, 9:20] > 0))

    def test_capped_at_tranche_capacity(self):
        gens = [_cc("P55000_committed", 60.0), _cc("P55000_econ", 140.0, 0.0)]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        disp = np.full((2, _T), 50.0)
        floor = _miso_gas_ecomin_floor(gens, fa, disp, MISO_GAS_ECOMIN_MIN_LOAD_FRAC)
        # plant 200 MW x 0.3238 = 64.8 > committed 60 -> capped at 60
        np.testing.assert_allclose(floor[0], 60.0)
        # incremental tranche (startup 0) is never floored
        self.assertEqual(float(floor[1].sum()), 0.0)


class TestEligibility(unittest.TestCase):
    """Physics gate and population."""

    def test_peak_block_with_startup_not_floored(self):
        # MISO CC _peak tranches (duct-firing) carry a startup cost too; the
        # floor must land on the plant's base block only.
        gens = [
            _cc("P55000_committed", 100.0),
            _cc("P55000_peak", 100.0, 50.0, heat_rate=17.0),
        ]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        disp = np.full((2, _T), 90.0)
        floor = _miso_gas_ecomin_floor(gens, fa, disp, 0.3)
        np.testing.assert_allclose(floor[0], 60.0)  # 0.3 x plant 200
        self.assertEqual(float(floor[1].sum()), 0.0)

    def test_chp_and_other_fuels_excluded(self):
        chp = _cc("P1_committed", group="CC_CHP")
        gens = [chp]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        disp = np.full((1, _T), 150.0)
        self.assertIsNone(_miso_gas_ecomin_floor(gens, fa, disp, 0.5))

    def test_offline_is_inert(self):
        gens = [_cc()]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        self.assertIsNone(_miso_gas_ecomin_floor(gens, fa, np.zeros((1, _T)), 0.5))


class TestGateAndAttribution(unittest.TestCase):
    """Config gate, ISO scope, D-2 id and the one-slot guard."""

    def test_gate(self):
        gens = [_cc()]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        off = ScenarioConfig(iso="MISO")
        self.assertFalse(off.miso_gas_ecomin_online_floor)
        self.assertIsNone(build_miso_gas_ecomin_p1_prep(off, "MISO", gens, fa))
        on = off.with_overrides(miso_gas_ecomin_online_floor=True)
        self.assertIsNone(build_miso_gas_ecomin_p1_prep(on, "SPP", gens, fa))
        self.assertIsNotNone(build_miso_gas_ecomin_p1_prep(on, "MISO", gens, fa))
        both = on.with_overrides(miso_coal_night_floor=True)
        with self.assertRaises(ValueError):
            build_miso_gas_ecomin_p1_prep(both, "MISO", gens, fa)

    def test_attribution(self):
        self.assertEqual(
            MECH_NAMES[MECH_MISO_GAS_ECOMIN_ONLINE], "miso_gas_ecomin_online_floor"
        )
        assert_ablation_coverage()
        gens = [_cc()]
        fa = generators_to_fleet_arrays(gens, ["z"], _T)
        disp = np.zeros((1, _T))
        disp[0, 6:18] = 150.0
        floor = _miso_gas_ecomin_floor(gens, fa, disp, 0.5)
        out = _bridge_floored_fleet(
            fa, floor, MECH_MISO_GAS_ECOMIN_ONLINE, preserve_absorption=True
        )
        self.assertEqual(int(out.min_gen_mechanism[0, 10]), MECH_MISO_GAS_ECOMIN_ONLINE)
        self.assertAlmostEqual(float(out.min_gen[0, 10]), 100.0)
        self.assertEqual(float(out.min_gen[0, 2]), 0.0)


if __name__ == "__main__":
    unittest.main()
