"""Tests for the MISO reference-price seam deliverability cap.

Each priced seam (PJM / SPP / South) has its import-band availability scaled to
the per-(month × hour-of-day) p90 measured EIA-930 BA-to-BA net-import envelope
(an ATC/transfer-capability proxy from the directed-flow series). The cap is
one-sided: a seam MISO net-exports over (SPP, South) clips toward ~0 import,
while every seam's export bands keep their priced economics. Mirrors the CAISO
corridor-flow-limit tests.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    INTERFACE_NEIGHBORS,
    MISO_SEAM_DIBA,
)
from market_sim.data.eia_loader import measured_seam_import_envelope
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_miso_seam_flow_limit,
)

T = 8760


class TestSeamEnvelopeLoader(unittest.TestCase):
    """The measured per-seam envelope is present, non-negative, and MISO-only."""

    def test_scope_and_clip(self):
        # Unmapped ISO and forecast year both fall through to None.
        self.assertIsNone(measured_seam_import_envelope("PJM", 2024, T))
        self.assertIsNone(measured_seam_import_envelope("MISO", 2030, T))
        env = measured_seam_import_envelope("MISO", 2024, T)
        self.assertIsNotNone(env)
        for name in MISO_SEAM_DIBA:
            self.assertIn(name, env)
            cap = env[name]
            self.assertEqual(cap.shape, (T,))
            # Import-direction ceiling: never negative.
            self.assertTrue(np.all(cap >= 0.0))

    def test_pjm_is_the_dominant_import_seam(self):
        # PJM is the real net-import seam; SPP/South (MISO net-exports there)
        # carry a far smaller import deliverability.
        env = measured_seam_import_envelope("MISO", 2024, T)
        self.assertGreater(env["PJM"].mean(), env["SPP"].mean())
        self.assertGreater(env["SPP"].mean(), env["South"].mean())
        # South nets to export → its import ceiling is near zero.
        self.assertLess(env["South"].mean(), 500.0)

    def test_export_envelope_mirrors_import(self):
        # The export envelope is the symmetric counterpart: the PJM seam (which
        # MISO net-IMPORTS over) has a ~0 EXPORT ceiling, while South (MISO's real
        # net-export seam) carries the largest export deliverability.
        exp = measured_seam_import_envelope("MISO", 2024, T, direction="export")
        self.assertIsNotNone(exp)
        for name in MISO_SEAM_DIBA:
            self.assertEqual(exp[name].shape, (T,))
            self.assertTrue(np.all(exp[name] >= 0.0))  # one-sided export ceiling
        self.assertLess(exp["PJM"].mean(), 100.0)  # PJM cannot net-export
        self.assertGreater(exp["South"].mean(), exp["PJM"].mean())
        self.assertGreater(exp["South"].mean(), 1000.0)  # ~2 GW measured headroom

    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            measured_seam_import_envelope("MISO", 2024, T, direction="sideways")


class TestSeamInjection(unittest.TestCase):
    """``inject_miso_seam_flow_limit`` caps import bands, leaves exports alone."""

    def _fleet(self):
        node = build_reference_price_node("MISO")
        zone_names = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, zone_names, hours=T)

    def test_import_bands_capped_to_envelope(self):
        node, fleet = self._fleet()
        env = measured_seam_import_envelope("MISO", 2024, T)
        self.assertTrue(inject_miso_seam_flow_limit(fleet, "MISO", 2024))
        for neighbor in INTERFACE_NEIGHBORS["MISO"]:
            name = neighbor.name
            imp_rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_IMPORT_MARK in uid
                and uid.rsplit(_REF_IMPORT_MARK, 1)[1].partition("#")[0] == name
            ]
            self.assertTrue(imp_rows)
            limit = float(fleet.pmax[imp_rows].sum())
            # Summed import availability (MW) per hour ≤ the clipped envelope cap.
            avail_mw = (
                fleet.availability[imp_rows, :] * fleet.pmax[imp_rows, None]
            ).sum(axis=0)
            expected = np.clip(env[name], 0.0, limit)
            np.testing.assert_allclose(avail_mw, expected, atol=1.0)

    def test_export_bands_untouched(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        inject_miso_seam_flow_limit(fleet, "MISO", 2024)
        exp_rows = [
            r for r, uid in enumerate(fleet.unit_ids) if _REF_EXPORT_MARK in uid
        ]
        self.assertTrue(exp_rows)
        np.testing.assert_array_equal(
            fleet.availability[exp_rows, :], before[exp_rows, :]
        )

    def test_noop_off_scope(self):
        # Forecast year → no measured envelope → no-op (False, unchanged).
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        self.assertFalse(inject_miso_seam_flow_limit(fleet, "MISO", 2030))
        np.testing.assert_array_equal(fleet.availability, before)


class TestSeamExportInjection(unittest.TestCase):
    """``inject_miso_seam_flow_limit(direction="export")`` caps export bands."""

    def _fleet(self):
        node = build_reference_price_node("MISO")
        zone_names = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, zone_names, hours=T)

    def test_export_bands_capped_to_envelope(self):
        node, fleet = self._fleet()
        exp = measured_seam_import_envelope("MISO", 2024, T, direction="export")
        self.assertTrue(
            inject_miso_seam_flow_limit(fleet, "MISO", 2024, direction="export")
        )
        self.assertIsNotNone(fleet.min_gen)
        for neighbor in INTERFACE_NEIGHBORS["MISO"]:
            name = neighbor.name
            exp_rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_EXPORT_MARK in uid
                and uid.rsplit(_REF_EXPORT_MARK, 1)[1].partition("#")[0] == name
            ]
            self.assertTrue(exp_rows)
            limit = -float(fleet.pmin[exp_rows].sum())
            # Summed max export (MW) per hour = -Σ min_gen ≤ the clipped cap.
            max_export = -fleet.min_gen[exp_rows, :].sum(axis=0)
            expected = np.clip(exp[name], 0.0, limit)
            np.testing.assert_allclose(max_export, expected, atol=1.0)

    def test_import_bands_untouched_by_export_cap(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        inject_miso_seam_flow_limit(fleet, "MISO", 2024, direction="export")
        imp_rows = [
            r for r, uid in enumerate(fleet.unit_ids) if _REF_IMPORT_MARK in uid
        ]
        self.assertTrue(imp_rows)
        # Export cap only touches min_gen; import-band availability is unchanged.
        np.testing.assert_array_equal(
            fleet.availability[imp_rows, :], before[imp_rows, :]
        )

    def test_export_cap_noop_off_scope(self):
        node, fleet = self._fleet()
        self.assertFalse(
            inject_miso_seam_flow_limit(fleet, "MISO", 2030, direction="export")
        )


if __name__ == "__main__":
    unittest.main()
