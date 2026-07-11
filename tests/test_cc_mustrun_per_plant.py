"""Tests for the per-plant gas local-reliability commitment floor.

``ScenarioConfig.cc_mustrun_per_plant`` forces each merchant CC_REGULAR /
CT_PEAKER committed tranche on as a min-gen floor within the plant's measured
committed window — its top ``online_frac`` fraction of hours ranked by system
load (thermal_tranches_<ISO>.csv gas ``online_frac``, CEMS synchronization
fraction). G-20 eastern CC/CT under-run follow-up; see
docs/handoffs/pjm-eastern-ccct-underrun-g20-2026-07.md §5 and the
ScenarioConfig field docstring for the rule-12/13 grounding.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    bins_to_fleet,
    generators_to_fleet_arrays,
    thermal_tranche_online_frac,
)
from market_sim.data.floor_mechanisms import MECH_CC_MUSTRUN_PER_PLANT

ZONES = ["Dominion"]

# Chesterfield (Dominion CC) and a real PJM CT: both carry a measured gas
# online_frac in the committed thermal_tranches_PJM.csv artifact.
_CC_CODE = 3797
_CT_CODE = 54


def _bin_row(code: int, group: str, name: str, pct_mc: float) -> dict:
    """One synthetic per-plant bin row in the schema bins_to_fleet consumes."""
    return {
        "Plant_Group": group,
        "ERCOT_Zone": "Dominion",
        "Bin_Number": 1,
        "Bin_Label": name,
        "Plant_Code": code,
        "Plant_Name": name,
        "Turbine_Class": "",
        "capacity_mw": 1000.0,
        "hr_weighted": 7.5,
        "pct_mr": 0.0,
        "pct_mc": pct_mc,
        "pct_econ": 100.0 - pct_mc - 5.0,
        "pct_peak": 5.0,
        "min_run": 0,
        "min_down": 0,
        "hr_mr": 7.5,
        "hr_mc": 7.2,
        "hr_econ": 7.5,
        "hr_peak": 9.0,
        "plant_count": 1,
        "plant_codes": [code],
        "fuel": "gas_cc" if group == "CC_REGULAR" else "gas_ct",
    }


def _build(flag_on: bool, codes_groups=None):
    rows = codes_groups or [
        (_CC_CODE, "CC_REGULAR", "Chesterfield", 40.0),
        (_CT_CODE, "CT_PEAKER", "SomeCT", 20.0),
    ]
    bins = pd.DataFrame([_bin_row(c, g, n, p) for c, g, n, p in rows])
    cfg = ScenarioConfig(
        iso="PJM",
        weather_year=2024,
        mode="backcast",
        hours=8760,
        cc_mustrun_per_plant=flag_on,
    )
    return bins_to_fleet(bins, ZONES, cfg)


def _suffix(gen: Generator) -> str:
    return gen.unit_id.rsplit("_", 1)[1]


class TestArtifactAccessor(unittest.TestCase):
    """thermal_tranche_online_frac reads the gas online_frac rows."""

    def test_pjm_gas_rows_present(self):
        frac = thermal_tranche_online_frac("PJM")
        self.assertIn((_CC_CODE, "CC_REGULAR"), frac)
        self.assertIn((_CT_CODE, "CT_PEAKER"), frac)
        for v in frac.values():
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_missing_iso_is_empty(self):
        self.assertEqual(thermal_tranche_online_frac("NOSUCHISO"), {})


class TestBinsTagging(unittest.TestCase):
    """bins_to_fleet pins the floor on the committed tranche only."""

    def test_flag_off_no_floor(self):
        fleet, fa = _build(flag_on=False)
        for g in fleet:
            self.assertEqual(g.cc_mustrun_pmin_mw, 0.0)
        self.assertIsNone(fa.min_gen)

    def test_committed_tranche_carries_floor(self):
        fleet, _ = _build(flag_on=True)
        for code, committed_cap in ((_CC_CODE, 400.0), (_CT_CODE, 200.0)):
            tranches = [g for g in fleet if g.plant_code == code]
            committed = [g for g in tranches if _suffix(g).startswith("committed")]
            self.assertTrue(committed)
            for g in committed:
                self.assertAlmostEqual(g.cc_mustrun_pmin_mw, g.pmax_mw, places=1)
                self.assertGreater(g.cc_mustrun_online_frac, 0.0)
            self.assertAlmostEqual(
                sum(g.pmax_mw for g in committed), committed_cap, places=1
            )
            for g in tranches:
                if not _suffix(g).startswith("committed"):
                    self.assertEqual(g.cc_mustrun_pmin_mw, 0.0)

    def test_uncovered_plant_gets_no_floor(self):
        """Rule 18: self-targeting by the measurement — no artifact row, no floor."""
        fleet, _ = _build(
            flag_on=True, codes_groups=[(999999, "CC_REGULAR", "Phantom", 40.0)]
        )
        for g in fleet:
            self.assertEqual(g.cc_mustrun_pmin_mw, 0.0)


class TestWindowPlacement(unittest.TestCase):
    """generators_to_fleet_arrays places the floor in the top-load window."""

    def _gen(self, pmin_mw: float, frac: float) -> Generator:
        return Generator(
            unit_id="CC_REGULAR_Dominion_p3797_committed",
            name="Chesterfield committed",
            zone="Dominion",
            fuel_type="gas_cc",
            pmax_mw=100.0,
            plant_group="CC_REGULAR",
            plant_code=_CC_CODE,
            is_campd_bin=True,
            cc_mustrun_pmin_mw=pmin_mw,
            cc_mustrun_online_frac=frac,
        )

    def test_top_load_hours_forced(self):
        hours = 8760
        # Strictly decreasing load: hour 0 is the peak, so the top-25% window
        # is exactly hours [0, 2190).
        load = np.arange(hours, 0, -1, dtype=float)
        fa = generators_to_fleet_arrays(
            [self._gen(50.0, 0.25)],
            ZONES,
            hours=hours,
            iso="PJM",
            load_shape=load,
        )
        self.assertIsNotNone(fa.min_gen)
        k = int(round(0.25 * hours))
        in_window = fa.min_gen[0, :k]
        out_window = fa.min_gen[0, k:]
        # Availability (WEFOR etc.) may derate below 50 in some hours, but the
        # window must be floored strictly positive and the rest exactly zero.
        self.assertTrue((in_window > 0.0).all())
        self.assertTrue((out_window == 0.0).all())
        mech = fa.min_gen_mechanism
        self.assertIsNotNone(mech)
        self.assertTrue(
            (mech[0, :k][in_window > 0.0] == MECH_CC_MUSTRUN_PER_PLANT).all()
        )
        self.assertTrue((mech[0, k:] == 0).all())

    def test_zero_frac_disables(self):
        fa = generators_to_fleet_arrays(
            [self._gen(50.0, 0.0)],
            ZONES,
            hours=8760,
            iso="PJM",
            load_shape=np.arange(8760, 0, -1, dtype=float),
        )
        # A zero measured window means no forcing (the allocation gate may
        # still allocate the matrix; it must stay all-zero).
        if fa.min_gen is not None:
            self.assertTrue((fa.min_gen == 0.0).all())


if __name__ == "__main__":
    unittest.main()
