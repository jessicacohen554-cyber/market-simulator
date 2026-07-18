"""Tests for the RA must-offer bridge's startup-trajectory extension (caiso-96 WP-1).

A measured CC start-to-load lead floors the L pre-start hours of each detected
run-start at the linear ramp-in toward min-load
(``model.commitment.caiso_ra_mustoffer_min_gen`` ``startup_lead_hours``).
Separate file by the ``test_ercot_gas_commitment_bridge`` convention (a
commitment-module mechanism with its own gate).
"""

import unittest

import numpy as np

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.commitment import caiso_ra_mustoffer_min_gen


class TestRaStartupTrajectory(unittest.TestCase):
    """The startup-trajectory extension (caiso-96 WP-1): a measured
    start-to-load lead floors the L pre-start hours of each detected run-start
    at the linear ramp-in toward min-load."""

    def _cc(self, hours, dispatch, heat_rate=7.0, plant_group="CC_REGULAR"):
        gen = Generator(
            unit_id="CC",
            name="CC",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=heat_rate,
            eford=0.0,
            plant_group=plant_group,
        )
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        return [gen], fa, np.asarray(dispatch, dtype=float).reshape(1, hours)

    def test_lead_floors_ramp_before_single_start(self):
        # One evening run 13-18, lead 3 h: hours 10/11/12 floor at the linear
        # ramp-in toward min-load, target x (1/4, 2/4, 3/4) of 120 MW. A
        # single-run unit still physically ramps in (no two-run requirement).
        disp = np.zeros(24)
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            startup_lead_hours=np.array([3]),
        )
        expected = np.zeros(24)
        expected[10] = 120.0 * 1 / 4
        expected[11] = 120.0 * 2 / 4
        expected[12] = 120.0 * 3 / 4
        np.testing.assert_allclose(floor[0], expected)

    def test_none_lead_is_byte_identical(self):
        disp = np.zeros(24)
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(p1, fa, gens, min_load_frac=0.40)
        np.testing.assert_allclose(floor[0], np.zeros(24))

    def test_lead_clips_at_hour_zero(self):
        # Run starting at t=1 with lead 3: only hour 0 exists, floored at the
        # j=1 rung (3/4 of target).
        disp = np.zeros(24)
        disp[1:7] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            startup_lead_hours=np.array([3]),
        )
        self.assertAlmostEqual(floor[0, 0], 120.0 * 3 / 4)
        np.testing.assert_allclose(floor[0, 1:], np.zeros(23))

    def test_lead_composes_with_gap_bridge_by_maximum(self):
        # Short gap 10-12 (bridged at full min-load 120): the second run's
        # lead hours overlap the bridged gap — maximum composition keeps the
        # HIGHER gap floor, never a downgrade to the ramp value.
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            startup_lead_hours=np.array([3]),
        )
        expected = np.zeros(24)
        expected[10:13] = 120.0  # gap bridge wins over the 30/60/90 ramp
        # first run's own lead (hours 3-5) still ramps in
        expected[3] = 120.0 * 1 / 4
        expected[4] = 120.0 * 2 / 4
        expected[5] = 120.0 * 3 / 4
        np.testing.assert_allclose(floor[0], expected)

    def test_lead_scales_with_availability(self):
        disp = np.zeros(24)
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        fa.availability[0, 12] = 0.5  # a derate halves the pre-start rung
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            startup_lead_hours=np.array([3]),
        )
        self.assertAlmostEqual(floor[0, 12], 120.0 * 3 / 4 * 0.5)
        self.assertAlmostEqual(floor[0, 11], 120.0 * 2 / 4)

    def test_zero_lead_row_is_untouched(self):
        disp = np.zeros(24)
        disp[13:19] = 300.0
        gens, fa, p1 = self._cc(24, disp)
        floor = caiso_ra_mustoffer_min_gen(
            p1,
            fa,
            gens,
            min_load_frac=0.40,
            startup_lead_hours=np.array([0]),
        )
        np.testing.assert_allclose(floor[0], np.zeros(24))


if __name__ == "__main__":
    unittest.main()
