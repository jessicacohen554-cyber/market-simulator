"""CAISO's published whole-class storage accreditation — source reconciliation.

Reconciles :data:`STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO` against the
committed, first-party-digitized SLRA Table 1.1 artifact, so the registry
literal can never drift from the published source it cites (the same
digitize-then-reconcile discipline the CAISO NQC class factors and the PJM /
MISO / NYISO ELCC curves already follow).

Rule 23 [R-FROZEN-DERIVE]: these expectations move only when CAISO publishes a
new assessment and it is intaken — never because a model residual moved.
"""

from __future__ import annotations

import csv
import unittest

from market_sim.config.constants import (
    STORAGE_BASE_FLEET_MW,
    STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO,
)
from market_sim.config.paths import RAW_DIR

# CAISO, 2026 Summer Loads and Resources Assessment Technical Appendix,
# Table 1.1 "Existing resources by fuel type and deliverability status",
# Battery row (September NQC; NDC as of April 1, 2026 from the Master File).
_PUBLISHED_BATTERY_NDC_MW = 14_131
_PUBLISHED_BATTERY_NQC_MW = 13_365
# The published Total row's NQC, which the fuel rows foot to EXACTLY — the
# check that proves the digitization, not merely the one row this test needs.
_PUBLISHED_TOTAL_NQC_MW = 59_069
# EIA-860 2025 Early Release, BA CISO, Status "OP" battery nameplate — the
# model's own multiplicand and the object STORAGE_BASE_FLEET_MW["CAISO"] is
# built from (FFR-4D §4.1).
_EIA860_CISO_BATTERY_NAMEPLATE_MW = 15_448.4

_CSV = (
    RAW_DIR
    / "capacity-market"
    / "loads-resources"
    / "caiso"
    / "caiso_slra_class_accreditation.csv"
)


class CaisoSlraClassAccreditationTest(unittest.TestCase):
    """The committed artifact, and the registry literal derived from it."""

    def setUp(self) -> None:
        with _CSV.open() as fh:
            self.rows = {r["fuel_type"]: r for r in csv.DictReader(fh)}

    def test_committed_artifact_carries_the_published_battery_row(self) -> None:
        """The digitized CSV reproduces Table 1.1's battery row exactly."""
        battery = self.rows["Battery"]
        self.assertEqual(int(battery["total_ndc_mw"]), _PUBLISHED_BATTERY_NDC_MW)
        self.assertEqual(int(battery["total_nqc_mw"]), _PUBLISHED_BATTERY_NQC_MW)
        # The deliverability split, which is why the whole-class ratio is below
        # the ~0.989 full-capacity-deliverable factor.
        self.assertEqual(int(battery["full_capacity_ndc_mw"]), 8_864)
        self.assertEqual(int(battery["full_capacity_nqc_mw"]), 8_764)
        self.assertEqual(int(battery["energy_only_nqc_mw"]), 0)

    def test_fuel_rows_foot_to_the_published_nqc_total(self) -> None:
        """The NQC column reconciles to the megawatt — the parse's own proof."""
        summed = sum(
            int(r["total_nqc_mw"]) for k, r in self.rows.items() if k != "Total"
        )
        self.assertEqual(summed, _PUBLISHED_TOTAL_NQC_MW)
        self.assertEqual(int(self.rows["Total"]["total_nqc_mw"]), summed)

    def test_registry_is_published_nqc_over_eia860_nameplate(self) -> None:
        """The registry value is NQC/NAMEPLATE, not the published NQC/NDC.

        The basis correction is the substance of the reconciliation (FFR-4E):
        the model multiplies nameplate, so quoting the published NQC/NDC ratio
        would over-credit the class.
        """
        expected = _PUBLISHED_BATTERY_NQC_MW / _EIA860_CISO_BATTERY_NAMEPLATE_MW
        self.assertAlmostEqual(
            STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"], expected, places=12
        )
        self.assertAlmostEqual(
            STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"], 0.865138, places=6
        )

    def test_registry_is_not_the_published_ndc_basis_ratio(self) -> None:
        """Guards the exact substitution FFR-4D §6.1 warned against."""
        ndc_basis = _PUBLISHED_BATTERY_NQC_MW / _PUBLISHED_BATTERY_NDC_MW
        self.assertAlmostEqual(ndc_basis, 0.945793, places=6)
        self.assertNotAlmostEqual(
            STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO["CAISO"], ndc_basis, places=3
        )

    def test_denominator_is_the_same_fleet_the_base_row_is_built_from(self) -> None:
        """Numerator and denominator describe ONE fleet (rule 14 reconciliation)."""
        self.assertAlmostEqual(
            STORAGE_BASE_FLEET_MW["CAISO"]["mid"],
            round(_EIA860_CISO_BATTERY_NAMEPLATE_MW, -1),
            places=6,
        )

    def test_caiso_is_the_only_iso_on_the_whole_class_rung(self) -> None:
        """Rule 25 [R-ISO-SCOPE]: no verdict or parameter crosses ISO lines."""
        self.assertEqual(set(STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO), {"CAISO"})


if __name__ == "__main__":
    unittest.main()
