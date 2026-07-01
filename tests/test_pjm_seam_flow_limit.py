"""Tests for the PJM reference-price seam deliverability cap.

Each of PJM's 5 priced seams (MISO / NYISO / Carolinas / TVA / LGEE) has its
import-band availability scaled to the measured per-neighbor deliverability
envelope from the PJM tie-line file (border zones summed to neighbor level, per
(month x hod) p90). The cap is applied per-direction: import caps scale
availability; export caps raise min_gen. Mirrors the MISO seam flow limit tests.
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.eia_loader import pjm_zonal_interchange_envelope
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_pjm_seam_flow_limit,
)

T = 8760
PJM_NEIGHBORS = INTERFACE_NEIGHBORS.get("PJM", [])
PJM_ZONE_NAMES = [
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_ComEd",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_MAAC",
    "PJM_West_APS",
    "PJM_external",
]


class TestPjmEnvelopeLoader(unittest.TestCase):
    """The PJM per-zone interchange envelope loads and is non-negative."""

    def test_envelope_present_for_backcast_year(self):
        env = pjm_zonal_interchange_envelope(2024, PJM_ZONE_NAMES, T)
        self.assertIsNotNone(env)
        import_cap, export_cap = env
        self.assertEqual(import_cap.shape, (len(PJM_ZONE_NAMES), T))
        self.assertEqual(export_cap.shape, (len(PJM_ZONE_NAMES), T))
        self.assertTrue(np.all(import_cap >= 0.0))
        self.assertTrue(np.all(export_cap >= 0.0))

    def test_envelope_none_for_future_year(self):
        self.assertIsNone(pjm_zonal_interchange_envelope(2030, PJM_ZONE_NAMES, T))


class TestPjmSeamInjection(unittest.TestCase):
    """``inject_pjm_seam_flow_limit`` caps import bands per neighbor."""

    def _fleet(self):
        node = build_reference_price_node("PJM")
        fleet_zones = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, fleet_zones, hours=T)

    def test_import_bands_capped(self):
        node, fleet = self._fleet()
        self.assertTrue(
            inject_pjm_seam_flow_limit(fleet, "PJM", 2024, PJM_ZONE_NAMES, T)
        )
        for neighbor in PJM_NEIGHBORS:
            imp_rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_IMPORT_MARK in uid
                and uid.rsplit(_REF_IMPORT_MARK, 1)[1].partition("#")[0]
                == neighbor.name
            ]
            self.assertTrue(imp_rows, f"no import rows for {neighbor.name}")
            avail_mw = (
                fleet.availability[imp_rows, :] * fleet.pmax[imp_rows, None]
            ).sum(axis=0)
            limit = float(fleet.pmax[imp_rows].sum())
            self.assertTrue(np.all(avail_mw <= limit + 1.0))

    def test_export_bands_untouched_by_import_cap(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        inject_pjm_seam_flow_limit(fleet, "PJM", 2024, PJM_ZONE_NAMES, T)
        exp_rows = [
            r for r, uid in enumerate(fleet.unit_ids) if _REF_EXPORT_MARK in uid
        ]
        self.assertTrue(exp_rows)
        np.testing.assert_array_equal(
            fleet.availability[exp_rows, :], before[exp_rows, :]
        )

    def test_noop_for_non_pjm(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        self.assertFalse(
            inject_pjm_seam_flow_limit(fleet, "MISO", 2024, PJM_ZONE_NAMES, T)
        )
        np.testing.assert_array_equal(fleet.availability, before)

    def test_noop_for_future_year(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        self.assertFalse(
            inject_pjm_seam_flow_limit(fleet, "PJM", 2030, PJM_ZONE_NAMES, T)
        )
        np.testing.assert_array_equal(fleet.availability, before)


class TestPjmSeamExportInjection(unittest.TestCase):
    """``inject_pjm_seam_flow_limit(direction="export")`` caps export bands."""

    def _fleet(self):
        node = build_reference_price_node("PJM")
        fleet_zones = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, fleet_zones, hours=T)

    def test_export_bands_capped(self):
        node, fleet = self._fleet()
        self.assertTrue(
            inject_pjm_seam_flow_limit(
                fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="export"
            )
        )
        self.assertIsNotNone(fleet.min_gen)
        for neighbor in PJM_NEIGHBORS:
            exp_rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_EXPORT_MARK in uid
                and uid.rsplit(_REF_EXPORT_MARK, 1)[1].partition("#")[0]
                == neighbor.name
            ]
            self.assertTrue(exp_rows, f"no export rows for {neighbor.name}")
            max_export = -fleet.min_gen[exp_rows, :].sum(axis=0)
            limit = -float(fleet.pmin[exp_rows].sum())
            self.assertTrue(np.all(max_export <= limit + 1.0))

    def test_import_bands_untouched_by_export_cap(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        inject_pjm_seam_flow_limit(
            fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="export"
        )
        imp_rows = [
            r for r, uid in enumerate(fleet.unit_ids) if _REF_IMPORT_MARK in uid
        ]
        self.assertTrue(imp_rows)
        np.testing.assert_array_equal(
            fleet.availability[imp_rows, :], before[imp_rows, :]
        )

    def test_invalid_direction_raises(self):
        node, fleet = self._fleet()
        with self.assertRaises(ValueError):
            inject_pjm_seam_flow_limit(
                fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="sideways"
            )


if __name__ == "__main__":
    unittest.main()
