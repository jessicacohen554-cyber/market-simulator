"""Tests for the eGRID plant-heat-rate boundary reconciliation.

Covers :func:`market_sim.data.fleet.eia860._egrid_boundary_hr_repairs` and its
frame-level applier. The reconciliation repairs plant heat rates that eGRID
computes as a ratio of two different boundaries — CEMS facility heat input over
single-EIA-plant net generation — where co-located plants share a CEMS
facilityId. See ``docs/handoffs/miso-88-egrid-hr-boundary-plan-2026-07.md``.
"""

import unittest

import pandas as pd

from market_sim.config.constants import EGRID_CC_HR_PHYSICAL_CEILING
from market_sim.data.fleet import load_fleet_from_csv
from market_sim.data.fleet.eia860 import (
    _apply_egrid_boundary_hr_repairs,
    _egrid_boundary_hr_repairs,
)

# Riverside Energy Center: eGRID PLHTRT 14,963.7 Btu/kWh, reconciled from its own
# UNT23 rows (CT-01 + CT-02 = 24,376,259 MMBtu over PLNGENAN 3,543,044 MWh).
RIVERSIDE = 55641
RIVERSIDE_RECONCILED = 6.880
# Coyote Springs (PGE, OR, 296 MW CC, 1995): the SECOND provable instance,
# reachable only since NWPP-20 (2026-09-14) put the NWPP footprint into the
# EIA-860 generator table the detector scans. eGRID PLHTRT 13,795.8 Btu/kWh:
# PLHTIAN 26,414,170 MMBtu covers CEMS facility 7350, which also stacks the
# co-located Coyote Springs II (ORISPL 7931, BPAT, 287 MW, 6 m away, its own
# PLHTIAN 15,602,260 > 0 and PLHTRT 6,894), while PLNGENAN 1,914,656 MWh is the
# PGE plant alone. All four conditions hold and the reconciled 6.918 sits
# beside the sibling's own 6.894 — the same double-count pattern as Riverside.
COYOTE_SPRINGS = 7350
COYOTE_SPRINGS_RECONCILED = 6.918


class TestEgridBoundaryRepairSet(unittest.TestCase):
    """The accepted repair set is exactly the provable double-count."""

    def test_riverside_is_repaired(self) -> None:
        repairs = _egrid_boundary_hr_repairs()
        self.assertIn(RIVERSIDE, repairs)
        self.assertAlmostEqual(repairs[RIVERSIDE], RIVERSIDE_RECONCILED, places=3)

    def test_repair_resolves_the_impossibility(self) -> None:
        """Condition 4 — every accepted value lands inside the physical band."""
        for code, hr in _egrid_boundary_hr_repairs().items():
            self.assertGreater(hr, 0.0, f"plant {code}")
            self.assertLessEqual(hr, EGRID_CC_HR_PHYSICAL_CEILING, f"plant {code}")

    def test_false_positives_are_rejected(self) -> None:
        """Devon fails condition 4; King City fails condition 1.

        Both are co-located pairs whose units eGRID cross-files, so the
        double-count detector alone would fire on them. Devon 544 repairs
        876.6 -> 340.1 MMBtu/MWh (garbage either way); King City 10294 would be
        *degraded* from an already-plausible 7.855 to 8.998. Neither may appear.
        """
        repairs = _egrid_boundary_hr_repairs()
        self.assertNotIn(544, repairs)
        self.assertNotIn(10294, repairs)

    def test_repair_set_is_minimal(self) -> None:
        """Scope is exactly the two provable double-counts — a third is
        stop-the-line. (One plant across the six ISOs until NWPP-20; Coyote
        Springs entered with the NWPP footprint, evidence at its constant.)"""
        repairs = _egrid_boundary_hr_repairs()
        self.assertEqual(set(repairs), {RIVERSIDE, COYOTE_SPRINGS})
        self.assertAlmostEqual(
            repairs[COYOTE_SPRINGS], COYOTE_SPRINGS_RECONCILED, places=3
        )


class TestEgridBoundaryRepairApplier(unittest.TestCase):
    """The frame applier is total and side-effect free."""

    def test_repairs_the_target_plant_only(self) -> None:
        df = pd.DataFrame(
            {
                "plant_id": [RIVERSIDE, RIVERSIDE, 55358],
                "heat_rate": [14.963746, 14.963746, 7.491377],
            }
        )
        out = _apply_egrid_boundary_hr_repairs(df)
        self.assertAlmostEqual(out.loc[0, "heat_rate"], RIVERSIDE_RECONCILED, places=3)
        self.assertAlmostEqual(out.loc[1, "heat_rate"], RIVERSIDE_RECONCILED, places=3)
        # An untargeted plant keeps eGRID's published value byte-for-byte.
        self.assertEqual(out.loc[2, "heat_rate"], 7.491377)

    def test_does_not_mutate_the_input_frame(self) -> None:
        df = pd.DataFrame({"plant_id": [RIVERSIDE], "heat_rate": [14.963746]})
        _apply_egrid_boundary_hr_repairs(df)
        self.assertEqual(df.loc[0, "heat_rate"], 14.963746)

    def test_frame_without_a_targeted_plant_is_returned_unchanged(self) -> None:
        df = pd.DataFrame({"plant_id": [55358], "heat_rate": [7.491377]})
        self.assertIs(_apply_egrid_boundary_hr_repairs(df), df)

    def test_missing_columns_are_tolerated(self) -> None:
        df = pd.DataFrame({"plant_id": [RIVERSIDE]})
        self.assertIs(_apply_egrid_boundary_hr_repairs(df), df)
        df = pd.DataFrame({"heat_rate": [14.963746]})
        self.assertIs(_apply_egrid_boundary_hr_repairs(df), df)


class TestEgridBoundaryRepairInFleet(unittest.TestCase):
    """The correction reaches the built fleet, and reaches nothing else."""

    def test_riverside_generators_carry_the_reconciled_rate(self) -> None:
        fleet = load_fleet_from_csv("MISO", year=2023)
        riverside = [g for g in fleet if int(g.plant_code) == RIVERSIDE]
        self.assertEqual(len(riverside), 3, "EIA-860 records 3 operable generators")
        for gen in riverside:
            self.assertAlmostEqual(gen.heat_rate, RIVERSIDE_RECONCILED, places=3)

    def test_other_isos_are_untouched(self) -> None:
        """Riverside is MISO-only; no other ISO fleet may carry a repair."""
        for iso in ("ERCOT", "CAISO", "PJM", "NYISO", "NEISO"):
            codes = {int(g.plant_code) for g in load_fleet_from_csv(iso, year=2023)}
            self.assertNotIn(RIVERSIDE, codes, iso)

    def test_reconciled_rate_is_plausible_against_its_own_class(self) -> None:
        """The repaired value must sit inside the MISO CC heat-rate spread."""
        fleet = load_fleet_from_csv("MISO", year=2023)
        cc = [g for g in fleet if g.fuel_type == "gas_cc" and g.heat_rate > 0]
        rates = sorted(g.heat_rate for g in cc)
        self.assertGreaterEqual(RIVERSIDE_RECONCILED, rates[0])
        self.assertLessEqual(RIVERSIDE_RECONCILED, rates[-1])


if __name__ == "__main__":
    unittest.main()
