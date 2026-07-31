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


class TestSelfschedClip(unittest.TestCase):
    """caiso-151: the floor clipped at the measured price-insensitive ceiling.

    The clip caps the FLOOR and never the CAPABILITY — above the measured
    ceiling the import is still available, just price-elastic — and it composes
    with the caiso-138 envelope clip as a SECOND pointwise min (rule 19).
    """

    def _clipped(self, ceiling_mw, year=2024):
        """Run the injector with a patched ceiling of ``ceiling_mw`` every hour."""
        import market_sim.data.caiso_intertie_bids as bids_mod

        fleet, _ = _per_hub_fleet()
        inject_caiso_firm_import_shape(fleet, "CAISO", year)
        cap = {
            uid: fleet.pmax[r] * fleet.availability[r, :].copy()
            for r, uid in enumerate(fleet.unit_ids)
        }
        orig = bids_mod.measured_intertie_selfsched_ceiling
        bids_mod.measured_intertie_selfsched_ceiling = lambda iso, yr, hours: (
            None if ceiling_mw is None else np.full(hours, float(ceiling_mw))
        )
        try:
            applied = inject_caiso_firm_import_selfschedule(
                fleet, "CAISO", year, selfsched_clip=True
            )
        finally:
            bids_mod.measured_intertie_selfsched_ceiling = orig
        return fleet, cap, applied

    def _firm_rows(self, fleet):
        zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
        out = []
        for r, uid in enumerate(fleet.unit_ids):
            zone = next((z for z in zones if uid.startswith(f"{z}_")), None)
            if zone and uid[len(zone) + 1 :] in CAISO_FIRM_IMPORT_TRANCHES:
                out.append(r)
        return out

    def test_clip_off_is_byte_identical_to_the_unclipped_floor(self):
        """The default path must be bit-for-bit the caiso-77 floor."""
        base, _ = _per_hub_fleet()
        inject_caiso_firm_import_shape(base, "CAISO", 2024)
        inject_caiso_firm_import_selfschedule(base, "CAISO", 2024)

        armed, _ = _per_hub_fleet()
        inject_caiso_firm_import_shape(armed, "CAISO", 2024)
        inject_caiso_firm_import_selfschedule(
            armed, "CAISO", 2024, selfsched_clip=False
        )
        np.testing.assert_array_equal(base.min_gen, armed.min_gen)

    def test_generous_ceiling_leaves_the_floor_untouched(self):
        """A ceiling above the block's own capability can never bind."""
        fleet, cap, applied = self._clipped(1e6)
        self.assertTrue(applied)
        for r in self._firm_rows(fleet):
            np.testing.assert_allclose(
                fleet.min_gen[r, :], cap[fleet.unit_ids[r]], rtol=1e-12
            )

    def test_binding_ceiling_clips_the_floor_to_the_system_total(self):
        """Summed across firm tranches the floor lands exactly on the ceiling."""
        ceiling = 500.0
        fleet, cap, _ = self._clipped(ceiling)
        rows = self._firm_rows(fleet)
        total_cap = np.sum([cap[fleet.unit_ids[r]] for r in rows], axis=0)
        total_floor = np.sum([fleet.min_gen[r, :] for r in rows], axis=0)
        binding = total_cap > ceiling
        self.assertTrue(binding.any(), "test ceiling should bind somewhere")
        np.testing.assert_allclose(total_floor[binding], ceiling, rtol=1e-9)
        # Never raises the floor where the ceiling is slack.
        self.assertTrue(np.all(total_floor <= total_cap + 1e-9))

    def test_clip_never_touches_capability(self):
        """pmax x availability is unchanged — only min_gen moves."""
        fleet, cap, _ = self._clipped(500.0)
        for r in self._firm_rows(fleet):
            np.testing.assert_allclose(
                fleet.pmax[r] * fleet.availability[r, :],
                cap[fleet.unit_ids[r]],
                rtol=1e-12,
            )
            self.assertTrue(
                np.all(fleet.min_gen[r, :] <= fleet.pmax[r] * fleet.availability[r, :])
            )

    def test_missing_artifact_leaves_the_floor_unclipped(self):
        """A year with no measured ceiling is left unclipped (byte-identical)."""
        fleet, cap, applied = self._clipped(None)
        self.assertTrue(applied)
        for r in self._firm_rows(fleet):
            np.testing.assert_allclose(
                fleet.min_gen[r, :], cap[fleet.unit_ids[r]], rtol=1e-12
            )

    def test_mechanism_attribution_survives_the_clip(self):
        fleet, _, _ = self._clipped(500.0)
        for r in self._firm_rows(fleet):
            floored = fleet.min_gen[r, :] > 0.0
            self.assertTrue(floored.any())
            self.assertTrue(
                (fleet.min_gen_mechanism[r, floored] == MECH_FIRM_IMPORT).all()
            )

    def test_d4_window_declared_for_firm_import(self):
        """caiso-151: the floor is finally visible to the D-4 check."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
        from legitimacy_diagnostics import D4_WINDOWS

        self.assertIn((MECH_FIRM_IMPORT, None), D4_WINDOWS)


if __name__ == "__main__":
    unittest.main()
