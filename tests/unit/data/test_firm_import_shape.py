"""Tests for the CAISO shaped firm import base (caiso-73).

Covers the measured revealed-base shape loader
(:func:`market_sim.data.eia_loader.measured_firm_import_shape` — unit-mean
weights, same-year vs pooled-climatology resolution, non-CAISO no-op) and the
availability injector
(:func:`market_sim.model.transmission.inject_caiso_firm_import_shape` —
hour-varying pmax capability on the firm tranches only, DMM year-level anchor,
eford preservation, byte-identity when off or when no shape resolves).
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    CAISO_PER_HUB_IMPORT_ZONES,
    IMPORT_TRANCHES_BY_YEAR,
)
from market_sim.data.eia_loader import measured_firm_import_shape
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    CAISO_FIRM_IMPORT_TRANCHES,
    build_caiso_per_hub_intertie,
    inject_caiso_firm_import_shape,
)

HOURS = 8760


def _per_hub_fleet(hours=HOURS):
    """The real per-hub intertie generator set as fleet arrays."""
    gens = build_caiso_per_hub_intertie()
    zones = sorted({g.zone for g in gens})
    return generators_to_fleet_arrays(gens, zones, hours=hours), gens


class TestMeasuredFirmImportShape(unittest.TestCase):
    def test_unit_mean_and_nonnegative(self):
        for year in (2023, 2024, 2025):
            w = measured_firm_import_shape("CAISO", year, HOURS)
            self.assertIsNotNone(w)
            self.assertEqual(w.shape, (HOURS,))
            self.assertAlmostEqual(float(w.mean()), 1.0, places=9)
            self.assertGreaterEqual(float(w.min()), 0.0)

    def test_shape_is_diurnal_overnight_over_midday(self):
        """Measured revealed base: overnight weight far above midday weight."""
        w = measured_firm_import_shape("CAISO", 2024, HOURS)
        hod = np.arange(HOURS) % 24
        overnight = w[np.isin(hod, [0, 1, 2, 3])].mean()
        midday = w[np.isin(hod, [12, 13, 14])].mean()
        evening = w[np.isin(hod, [20, 21, 22])].mean()
        self.assertGreater(overnight, 2.5 * midday)
        self.assertGreater(evening, 2.5 * midday)

    def test_forecast_year_falls_back_to_climatology(self):
        w = measured_firm_import_shape("CAISO", 2035, HOURS)
        self.assertIsNotNone(w)
        self.assertAlmostEqual(float(w.mean()), 1.0, places=9)

    def test_non_caiso_returns_none(self):
        self.assertIsNone(measured_firm_import_shape("PJM", 2024, HOURS))

    def test_partial_horizon(self):
        w = measured_firm_import_shape("CAISO", 2024, 48)
        self.assertEqual(w.shape, (48,))


class TestInjectCaisoFirmImportShape(unittest.TestCase):
    def test_firm_rows_shaped_to_dmm_level_times_weight(self):
        fleet, gens = _per_hub_fleet()
        base_avail = fleet.availability.copy()
        base_pmax = fleet.pmax.copy()
        year = 2024
        self.assertTrue(inject_caiso_firm_import_shape(fleet, "CAISO", year))
        w = measured_firm_import_shape("CAISO", year, HOURS)
        ladder = {n: c for n, c, _ in IMPORT_TRANCHES_BY_YEAR["CAISO"][year]}
        zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
        n_firm = 0
        for row, uid in enumerate(fleet.unit_ids):
            zone = next((z for z in zones if uid.startswith(f"{z}_")), None)
            name = uid[len(zone) + 1 :] if zone else ""
            cap_now = fleet.pmax[row] * fleet.availability[row, :]
            cap_before = base_pmax[row] * base_avail[row, :]
            if name in CAISO_FIRM_IMPORT_TRANCHES:
                n_firm += 1
                # capability = eford-derated DMM year level × unit-mean weight
                expected = ladder[name] * w * base_avail[row, :]
                np.testing.assert_allclose(cap_now, expected, rtol=1e-9)
                # annual energy capability conserved at the DMM year level
                self.assertAlmostEqual(
                    float(cap_now.mean()),
                    ladder[name] * float(base_avail[row, 0]),
                    delta=1e-6 * ladder[name],
                )
            else:
                # spot tranches and export legs untouched
                np.testing.assert_array_equal(cap_now, cap_before)
        self.assertEqual(n_firm, len(CAISO_FIRM_IMPORT_TRANCHES))

    def test_year_level_is_year_grounded(self):
        """2023 uses the 2023 DMM firm volumes, not the static ladder."""
        fleet, _ = _per_hub_fleet()
        self.assertTrue(inject_caiso_firm_import_shape(fleet, "CAISO", 2023))
        ladder = {n: c for n, c, _ in IMPORT_TRANCHES_BY_YEAR["CAISO"][2023]}
        w = measured_firm_import_shape("CAISO", 2023, HOURS)
        for row, uid in enumerate(fleet.unit_ids):
            for name in CAISO_FIRM_IMPORT_TRANCHES:
                if uid.endswith(f"_{name}"):
                    cap = fleet.pmax[row] * fleet.availability[row, :]
                    # eford 0.02 derate preserved multiplicatively
                    np.testing.assert_allclose(cap, ladder[name] * w * 0.98, rtol=1e-9)

    def test_non_caiso_fleet_is_untouched(self):
        fleet, _ = _per_hub_fleet()
        base = fleet.availability.copy()
        self.assertFalse(inject_caiso_firm_import_shape(fleet, "PJM", 2024))
        np.testing.assert_array_equal(fleet.availability, base)

    def test_gate_off_is_byte_identical_via_shared_seam(self):
        """apply_interchange_injections without the flag leaves the fleet as-is."""
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.transmission import apply_interchange_injections

        fleet, _ = _per_hub_fleet()
        base_avail = fleet.availability.copy()
        base_pmax = fleet.pmax.copy()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        config = ScenarioConfig().with_overrides(
            caiso_per_hub_intertie=True, caiso_perhub_firm_base=True
        )
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        np.testing.assert_array_equal(fleet.availability, base_avail)
        np.testing.assert_array_equal(fleet.pmax, base_pmax)

    def test_gate_on_shapes_via_shared_seam(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.transmission import apply_interchange_injections

        fleet, _ = _per_hub_fleet()
        base_avail = fleet.availability.copy()
        mc = np.zeros((len(fleet.unit_ids), HOURS))
        config = ScenarioConfig().with_overrides(
            caiso_per_hub_intertie=True,
            caiso_perhub_firm_base=True,
            caiso_firm_import_shape=True,
        )
        apply_interchange_injections(fleet, mc, config, "CAISO", 2024)
        self.assertFalse(np.array_equal(fleet.availability, base_avail))


if __name__ == "__main__":
    unittest.main()
