"""Tests for the CAISO per-hub WECC export-leg envelope cap (caiso-112 L1a′).

``inject_caiso_wecc_export_leg_envelope`` (gated by
``config.caiso_wecc_export_floor``) tightens each per-hub export leg's hourly
``min_gen`` from its static ``-corridor TTC`` bound up to ``-envelope`` — the
same measured p95 net-export deliverability ceiling the corridor flow groups
use — so the leg net-exports at most the measured surplus each hour (and 0 in
the evening-ramp buckets whose measured net-export collapses to ~0), instead of
wheeling its full physical TTC out. Byte-identical when the flag is off (the
injector is simply not called) or when the fleet carries no export legs.
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.interchange.caiso import (
    build_caiso_per_hub_intertie,
    inject_caiso_wecc_export_leg_envelope,
)

T = 24


def _synthetic_export_env():
    """A per-zone (T,) net-export ceiling: PNW a flat 300 MW, DSW belly-only."""
    pnw = np.full(T, 300.0)
    dsw = np.zeros(T)
    dsw[10:16] = 800.0  # belly hours only, 0 elsewhere (evening ramp collapses)
    return {"WECC_PNW": pnw, "WECC_DSW": dsw}


def _fleet_from(gens, hours):
    zone_names = sorted({g.zone for g in gens})
    return generators_to_fleet_arrays(gens, zone_names, hours=hours)


class TestExportLegEnvelopeCap(unittest.TestCase):
    def _fleet(self):
        # The two per-hub export legs (+ their import tranches).
        return _fleet_from(build_caiso_per_hub_intertie(), T)

    def test_caps_each_export_leg_at_negative_envelope(self):
        fleet = self._fleet()
        env = _synthetic_export_env()
        with mock.patch(
            "market_sim.data.eia_loader.measured_corridor_flow_envelope",
            return_value=env,
        ):
            applied = inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2024)
        self.assertTrue(applied)
        self.assertIsNotNone(fleet.min_gen)
        for r, uid in enumerate(fleet.unit_ids):
            if "export" not in uid:
                continue
            zone = "WECC_PNW" if "PNW" in uid else "WECC_DSW"
            # min_gen raised from -TTC up to -envelope (the measured surplus is
            # far below the line rating, so -env always wins).
            np.testing.assert_allclose(fleet.min_gen[r, :], -env[zone])
            # Export magnitude (=-min_gen) never exceeds the physical TTC bound.
            self.assertTrue(np.all(-fleet.min_gen[r, :] <= -fleet.pmin[r] + 1e-6))

    def test_zero_export_bucket_pins_leg_to_zero(self):
        fleet = self._fleet()
        env = _synthetic_export_env()  # DSW is 0 outside the belly
        with mock.patch(
            "market_sim.data.eia_loader.measured_corridor_flow_envelope",
            return_value=env,
        ):
            inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2024)
        dsw_row = next(
            r for r, u in enumerate(fleet.unit_ids) if "DSW_export" in u
        )
        # Evening/overnight buckets (env 0) pin the leg's lower bound to 0 → no
        # export; belly buckets allow the measured 800 MW.
        self.assertTrue(np.all(fleet.min_gen[dsw_row, :6] == 0.0))
        np.testing.assert_allclose(fleet.min_gen[dsw_row, 10:16], -800.0)

    def test_non_export_rows_untouched(self):
        fleet = self._fleet()
        env = _synthetic_export_env()
        with mock.patch(
            "market_sim.data.eia_loader.measured_corridor_flow_envelope",
            return_value=env,
        ):
            inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2024)
        for r, uid in enumerate(fleet.unit_ids):
            if "export" in uid:
                continue
            # Import tranches keep their broadcast pmin lower bound (0.0).
            np.testing.assert_allclose(fleet.min_gen[r, :], fleet.pmin[r])

    def test_no_mechanism_tag_for_export_cap(self):
        fleet = self._fleet()
        env = _synthetic_export_env()
        with mock.patch(
            "market_sim.data.eia_loader.measured_corridor_flow_envelope",
            return_value=env,
        ):
            inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2024)
        # A negative export bound is a deliverability cap, not a must-run floor,
        # so it carries no MECH_* tag (nothing to ablation-attribute).
        self.assertIsNone(fleet.min_gen_mechanism)

    def test_no_envelope_is_byte_identical_noop(self):
        fleet = self._fleet()
        before = None if fleet.min_gen is None else fleet.min_gen.copy()
        with mock.patch(
            "market_sim.data.eia_loader.measured_corridor_flow_envelope",
            return_value=None,
        ):
            applied = inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2099)
        self.assertFalse(applied)
        self.assertEqual(before, fleet.min_gen)  # both None → untouched

    def test_no_export_legs_returns_false(self):
        # A fleet with no export legs (empty) is a byte-identical no-op.
        gens = [g for g in build_caiso_per_hub_intertie() if "export" not in g.unit_id]
        fleet = _fleet_from(gens, T)
        with mock.patch(
            "market_sim.data.eia_loader.measured_corridor_flow_envelope",
            return_value=_synthetic_export_env(),
        ):
            applied = inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2024)
        self.assertFalse(applied)


class TestExportLegEnvelopeRealData(unittest.TestCase):
    """Data-backed smoke: the real measured envelope caps the real legs."""

    def test_real_envelope_caps_legs(self):
        from market_sim.data.eia_loader import measured_corridor_flow_envelope

        env = measured_corridor_flow_envelope("CAISO", 2024, 8760, direction="export")
        if not env:
            self.skipTest("CISO interchange parquet not present")
        gens = build_caiso_per_hub_intertie()
        fleet = _fleet_from(gens, 8760)
        applied = inject_caiso_wecc_export_leg_envelope(fleet, "CAISO", 2024)
        self.assertTrue(applied)
        for r, uid in enumerate(fleet.unit_ids):
            if "export" not in uid:
                continue
            zone = "WECC_PNW" if "PNW" in uid else "WECC_DSW"
            cap_mag = -fleet.min_gen[r, :]
            # Never negative, never above the physical TTC, equals the envelope.
            self.assertTrue(np.all(cap_mag >= -1e-9))
            self.assertTrue(np.all(cap_mag <= -fleet.pmin[r] + 1e-6))
            np.testing.assert_allclose(cap_mag, env[zone])


if __name__ == "__main__":
    unittest.main()
