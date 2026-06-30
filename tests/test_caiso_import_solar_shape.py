"""Tests for the CAISO desert-SW solar-shaped import/export offer.

``caiso_import_solar_shape`` collapses the marginal long-neighbor import blocks
(DSW_solar_PV / Palo Verde, PNW_midC / Mid-C) and the export sinks toward the
negative keep-running floor (−renewable_keep_running_value) as CAISO net load
drops into its annual belly, so the marginal midday import bids sub-$0 in the
regional solar/hydro glut — restoring the CAISO negative midday tail. See
``results/calibration/RESULTS-caiso-negative-tail-solar-shape-2026-06-21.md``.
"""

from __future__ import annotations

import types
import unittest

import numpy as np

from market_sim.config.interchange_config import IMPORT_ZONE
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _CAISO_SOLAR_SHAPE_EXPORT_TRANCHES,
    _CAISO_SOLAR_SHAPE_TRANCHES,
    build_export_sinks,
    build_import_generators,
    inject_caiso_import_solar_shape,
)


class TestInjectCaisoImportSolarShape(unittest.TestCase):
    def _caiso_fleet(self, hours):
        gens = build_import_generators("CAISO") + build_export_sinks("CAISO")
        zone = IMPORT_ZONE["CAISO"]
        return generators_to_fleet_arrays(gens, ["NP15", zone], hours=hours), gens

    def _config(self, krv=20.0):
        return types.SimpleNamespace(iso="CAISO", renewable_keep_running_value=krv)

    def _net_load(self, hours):
        # Monotone ramp so percentile gating is deterministic: the lowest hours
        # are the belly (s -> 1), the highest are off-belly (s = 0).
        return np.linspace(0.0, 100.0, hours)

    def test_collapses_target_blocks_in_belly_only(self):
        hours = 100
        fa, gens = self._caiso_fleet(hours)
        base = np.tile(np.arange(len(gens), dtype=float)[:, None] + 50.0, (1, hours))
        mc = base.copy()
        applied = inject_caiso_import_solar_shape(
            fa, mc, self._config(), self._net_load(hours)
        )
        self.assertTrue(applied)
        zone = IMPORT_ZONE["CAISO"]
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        targets = {
            f"{zone}_{t}"
            for t in (*_CAISO_SOLAR_SHAPE_TRANCHES, *_CAISO_SOLAR_SHAPE_EXPORT_TRANCHES)
        }
        # Deepest-belly hour (lowest net load) -> full collapse to the -KRV floor.
        for uid in targets:
            self.assertAlmostEqual(mc[row[uid], 0], -20.0, places=6)
        # Off-belly hour (highest net load) -> untouched.
        for uid in targets:
            self.assertAlmostEqual(mc[row[uid], -1], base[row[uid], -1], places=6)

    def test_non_target_blocks_untouched(self):
        hours = 100
        fa, gens = self._caiso_fleet(hours)
        base = np.tile(np.arange(len(gens), dtype=float)[:, None] + 50.0, (1, hours))
        mc = base.copy()
        inject_caiso_import_solar_shape(fa, mc, self._config(), self._net_load(hours))
        zone = IMPORT_ZONE["CAISO"]
        row = {uid: r for r, uid in enumerate(fa.unit_ids)}
        # Firm baseload hydro and peak scarcity are NOT collapsed.
        for tr in ("PNW_hydro_base", "WECC_scarcity"):
            np.testing.assert_array_equal(
                mc[row[f"{zone}_{tr}"]], base[row[f"{zone}_{tr}"]]
            )

    def test_non_caiso_is_noop(self):
        hours = 50
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 42.0)
        before = mc.copy()
        cfg = types.SimpleNamespace(iso="PJM", renewable_keep_running_value=20.0)
        applied = inject_caiso_import_solar_shape(fa, mc, cfg, self._net_load(hours))
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, before)

    def test_length_mismatch_is_noop(self):
        hours = 50
        fa, gens = self._caiso_fleet(hours)
        mc = np.full((len(gens), hours), 42.0)
        before = mc.copy()
        applied = inject_caiso_import_solar_shape(
            fa, mc, self._config(), self._net_load(hours + 1)
        )
        self.assertFalse(applied)
        np.testing.assert_array_equal(mc, before)


if __name__ == "__main__":
    unittest.main()
