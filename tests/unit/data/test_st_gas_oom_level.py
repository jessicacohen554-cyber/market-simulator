"""Tests for the OUT-OF-MERIT conditioning of the ST_GAS must-run floor level.

``ScenarioConfig.st_gas_mustrun_oom_level`` (miso-198) replaces the level SOURCE
of the existing ``st_gas_mustrun_p25_level`` floor: the same frozen percentile
family over the same pooled window, taken over the plant's online hours **in
which the class's economic signal says off** (the miso-197 W3b CC-headroom set)
instead of over every hour it was online. Rule 19 ``[R-ONE-MECH]``: the level is
REPLACED in the same slot — membership, window, mechanism id and the
cheapest-first ``pmax x availability`` clip are untouched and no second floor is
stacked.

These tests pin the properties the A/B's single-delta claim rests on:
  * the artifact accessor reads the derived CSV and rejects junk rows;
  * the flag is inert while off (byte-identical floors);
  * arming it changes the LEVEL and nothing else — same floored plants, same
    mechanism id, same window hours;
  * both level flags on => the out-of-merit level wins (re-conditioned, not
    stacked).
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    bins_to_fleet,
    generators_to_fleet_arrays,
    thermal_tranche_oom_level,
    thermal_tranche_p25_measured_level,
)
from market_sim.data.floor_mechanisms import MECH_ST_GAS_MUSTRUN_PER_PLANT

ZONES = ["MISO-South"]
# Nine Mile Point — the largest ST_GAS floor carrier in the MISO keeper; it
# holds both an incumbent measured-MW level and an out-of-merit level.
_ST_CODE = 1403
HOURS = 8760


def _bin_row(code: int, group: str, name: str) -> dict:
    """One synthetic per-plant bin row in the schema bins_to_fleet consumes."""
    return {
        "Plant_Group": group,
        "ERCOT_Zone": ZONES[0],
        "Bin_Number": 1,
        "Bin_Label": name,
        "Plant_Code": code,
        "Plant_Name": name,
        "Turbine_Class": "",
        "capacity_mw": 1465.4,
        "hr_weighted": 11.0,
        "pct_mr": 0.0,
        "pct_mc": 32.0,
        "pct_econ": 63.0,
        "pct_peak": 5.0,
        "min_run": 0,
        "min_down": 0,
        "hr_mr": 11.0,
        "hr_mc": 10.6,
        "hr_econ": 11.0,
        "hr_peak": 12.5,
        "plant_count": 1,
        "plant_codes": [code],
        "fuel": "gas_st",
    }


def _floor(oom: bool, measured: bool = True) -> np.ndarray:
    """Build the ST_GAS floor row-sum with the level flags as given."""
    bins = pd.DataFrame([_bin_row(_ST_CODE, "ST_GAS", "Nine Mile Point")])
    cfg = ScenarioConfig(
        iso="MISO",
        weather_year=2024,
        mode="backcast",
        hours=HOURS,
        st_gas_mustrun_per_plant=True,
        st_gas_mustrun_p25_level=True,
        st_gas_mustrun_p25_measured_level=measured,
        st_gas_mustrun_oom_level=oom,
    )
    fleet, _ = bins_to_fleet(bins, ZONES, cfg)
    # A rising synthetic load shape: the floor's window is the top-online_frac
    # fraction of hours by SYSTEM LOAD, so one must be supplied or the runtime
    # falls through to an all-hours target.
    load = np.linspace(40_000.0, 90_000.0, HOURS)
    fa = generators_to_fleet_arrays(
        fleet, ZONES, HOURS, iso="MISO", config=cfg, load_shape=load, year=2024
    )
    return fa


class TestArtifactAccessor(unittest.TestCase):
    """thermal_tranche_oom_level reads the derived out-of-merit level rows."""

    def test_miso_st_gas_rows_present(self):
        lv = thermal_tranche_oom_level("MISO")
        self.assertIn((_ST_CODE, "ST_GAS"), lv)
        for v in lv.values():
            self.assertGreater(v, 0.0)

    def test_missing_iso_is_empty(self):
        self.assertEqual(thermal_tranche_oom_level("NOSUCHISO"), {})

    def test_level_is_at_or_below_the_incumbent(self):
        """The re-conditioned p25 never exceeds the all-online p25 for MISO.

        Not a design constraint of the mechanism — a measured property of the
        MISO artifact pair, pinned so a future re-derivation that inverts it
        is caught and read rather than absorbed silently.
        """
        oom = thermal_tranche_oom_level("MISO")
        inc = thermal_tranche_p25_measured_level("MISO")
        shared = [k for k in oom if k in inc and k[1] == "ST_GAS"]
        self.assertTrue(shared)
        for k in shared:
            self.assertLessEqual(oom[k], inc[k] + 1e-9, msg=str(k))


class TestFloorWiring(unittest.TestCase):
    """The flag swaps the LEVEL and nothing else (rule 19)."""

    @staticmethod
    def _plant_floor_and_cap(fa) -> tuple[np.ndarray, np.ndarray]:
        """Plant-hour floor MW and available MW over the floored hours."""
        rows = (fa.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT).any(axis=1)
        floor = fa.min_gen[rows].sum(axis=0)
        cap = (fa.availability[rows] * fa.pmax[rows, None]).sum(axis=0)
        hrs = floor > 0.0
        return floor[hrs], cap[hrs]

    def test_off_holds_the_incumbent_level_under_the_availability_clip(self):
        """The runtime contract is floor == min(level, available) each hour."""
        fa = _floor(oom=False)
        self.assertIsNotNone(fa.min_gen)
        self.assertTrue((fa.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT).any())
        floor, cap = self._plant_floor_and_cap(fa)
        level = thermal_tranche_p25_measured_level("MISO")[(_ST_CODE, "ST_GAS")]
        np.testing.assert_allclose(floor, np.minimum(level, cap), rtol=1e-6)

    def test_on_holds_the_out_of_merit_level_under_the_same_clip(self):
        fa = _floor(oom=True)
        self.assertTrue((fa.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT).any())
        floor, cap = self._plant_floor_and_cap(fa)
        level = thermal_tranche_oom_level("MISO")[(_ST_CODE, "ST_GAS")]
        np.testing.assert_allclose(floor, np.minimum(level, cap), rtol=1e-6)

    def test_membership_and_window_unchanged(self):
        """Same mechanism id, same floored hours — only the level moves."""
        off = _floor(oom=False)
        on = _floor(oom=True)
        m_off = off.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT
        m_on = on.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT
        np.testing.assert_array_equal(m_off, m_on)
        self.assertLess(float(on.min_gen[m_on].sum()), float(off.min_gen[m_off].sum()))

    def test_wins_over_the_incumbent_level_not_stacked(self):
        """Both level flags on: the re-conditioned level replaces, never adds."""
        both = _floor(oom=True, measured=True)
        only = _floor(oom=True, measured=False)
        np.testing.assert_allclose(both.min_gen, only.min_gen, rtol=0, atol=1e-9)


class TestInertWhileOff(unittest.TestCase):
    """A run that does not arm the flag is byte-identical to today."""

    def test_default_is_off(self):
        self.assertFalse(ScenarioConfig(iso="MISO").st_gas_mustrun_oom_level)

    def test_no_st_gas_floor_without_the_parent_gate(self):
        bins = pd.DataFrame([_bin_row(_ST_CODE, "ST_GAS", "Nine Mile Point")])
        cfg = ScenarioConfig(
            iso="MISO",
            weather_year=2024,
            mode="backcast",
            hours=HOURS,
            st_gas_mustrun_oom_level=True,
        )
        fleet, _ = bins_to_fleet(bins, ZONES, cfg)
        fa = generators_to_fleet_arrays(
            fleet, ZONES, HOURS, iso="MISO", config=cfg,
            load_shape=np.linspace(40_000.0, 90_000.0, HOURS), year=2024,
        )
        if fa.min_gen_mechanism is not None:
            self.assertFalse(
                (fa.min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT).any()
            )


if __name__ == "__main__":
    unittest.main()
