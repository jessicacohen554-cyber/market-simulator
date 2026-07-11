"""Tests for the CAISO firm-import self-schedule floor (caiso-77).

Covers :func:`market_sim.model.transmission.inject_caiso_firm_import_selfschedule`
— the must-flow ``min_gen`` floor at the shaped firm capability (the
Manitoba/HQ firm-import pattern applied to the CAISO contracted base): floor
equals ``pmax × availability`` on the firm tranches only, ``MECH_FIRM_IMPORT``
attribution, byte-identity when off / for non-firm rows, and the
``apply_interchange_injections`` gating (requires ``caiso_perhub_firm_base`` +
``caiso_firm_import_shape``).
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import CAISO_PER_HUB_IMPORT_ZONES
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import MECH_ABLATION_KEPT, MECH_FIRM_IMPORT
from market_sim.model.transmission import (
    CAISO_FIRM_IMPORT_TRANCHES,
    build_caiso_per_hub_intertie,
    inject_caiso_firm_import_selfschedule,
    inject_caiso_firm_import_shape,
)

HOURS = 8760


def _per_hub_fleet(hours=HOURS):
    """The real per-hub intertie generator set as fleet arrays."""
    gens = build_caiso_per_hub_intertie()
    zones = sorted({g.zone for g in gens})
    return generators_to_fleet_arrays(gens, zones, hours=hours), gens


class TestInjectCaisoFirmImportSelfschedule(unittest.TestCase):
    def test_firm_rows_floored_at_shaped_capability(self):
        fleet, _ = _per_hub_fleet()
        self.assertTrue(inject_caiso_firm_import_shape(fleet, "CAISO", 2024))
        self.assertTrue(inject_caiso_firm_import_selfschedule(fleet, "CAISO", 2024))
        zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
        n_firm = 0
        for row, uid in enumerate(fleet.unit_ids):
            zone = next((z for z in zones if uid.startswith(f"{z}_")), None)
            name = uid[len(zone) + 1 :] if zone else ""
            cap = fleet.pmax[row] * fleet.availability[row, :]
            if name in CAISO_FIRM_IMPORT_TRANCHES:
                n_firm += 1
                # must-flow: min_gen == the full shaped capability, every hour
                np.testing.assert_allclose(fleet.min_gen[row, :], cap, rtol=1e-12)
                floored = fleet.min_gen[row, :] > 0.0
                self.assertTrue(floored.any())
                self.assertTrue(
                    (fleet.min_gen_mechanism[row, floored] == MECH_FIRM_IMPORT).all()
                )
            else:
                # spot tranches / export legs keep their pmin (zero) floor
                np.testing.assert_array_equal(
                    fleet.min_gen[row, :],
                    np.full(HOURS, fleet.pmin[row]),
                )
        self.assertEqual(n_firm, len(CAISO_FIRM_IMPORT_TRANCHES))

    def test_mechanism_is_ablation_kept(self):
        """The floor is a contract: the zero-forcing ablation must keep it."""
        self.assertIn(MECH_FIRM_IMPORT, MECH_ABLATION_KEPT)

    def test_no_firm_rows_returns_false(self):
        fleet, _ = _per_hub_fleet()
        keep = [
            r
            for r, uid in enumerate(fleet.unit_ids)
            if not any(uid.endswith(f"_{n}") for n in CAISO_FIRM_IMPORT_TRANCHES)
        ]
        fleet.unit_ids = [fleet.unit_ids[r] for r in keep]
        fleet.pmax = fleet.pmax[keep]
        fleet.pmin = fleet.pmin[keep]
        fleet.availability = fleet.availability[keep]
        self.assertFalse(inject_caiso_firm_import_selfschedule(fleet, "CAISO", 2024))

    def test_gate_off_is_byte_identical_via_shared_seam(self):
        """Shape on but selfschedule off: no floor appears."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.transmission import apply_interchange_injections

        fleet, _ = _per_hub_fleet()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        config = ScenarioConfig().with_overrides(
            caiso_per_hub_intertie=True,
            caiso_perhub_firm_base=True,
            caiso_firm_import_shape=True,
        )
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        if fleet.min_gen is not None:
            self.assertLessEqual(float(fleet.min_gen.max()), 0.0)

    def test_gate_on_floors_via_shared_seam(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.transmission import apply_interchange_injections

        fleet, _ = _per_hub_fleet()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        config = ScenarioConfig().with_overrides(
            caiso_per_hub_intertie=True,
            caiso_perhub_firm_base=True,
            caiso_firm_import_shape=True,
            caiso_firm_import_selfschedule=True,
        )
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        self.assertIsNotNone(fleet.min_gen)
        self.assertGreater(float(fleet.min_gen.max()), 0.0)
        floored_rows = {
            fleet.unit_ids[r] for r in np.nonzero(fleet.min_gen.max(axis=1) > 0.0)[0]
        }
        for uid in floored_rows:
            self.assertTrue(
                any(uid.endswith(f"_{n}") for n in CAISO_FIRM_IMPORT_TRANCHES)
            )


if __name__ == "__main__":
    unittest.main()
