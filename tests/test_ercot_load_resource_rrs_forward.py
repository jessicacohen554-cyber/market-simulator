"""Tests for ERCOT's enrollment-driven forward load-resource RRS-UFR credit (G4).

The forward analogue of reading the measured NP3-911 cleared RRS-UFR MW: in
forecast mode the load-side Responsive-Reserve credit is
``lr_rrs(t) = enrolled_DR_MW(year) x availability_shape(t)``, an enrollment
trajectory that grows toward the protocol cap and responds to changed conditions;
in backcast mode it stays the measured series, byte-identical to the legacy path.
Built from the trivial case up (CLAUDE.md testing pattern): the enrollment
trajectory and mean-1 availability shape, the mode-aware selector, and the credit
wired into both the single-lumped and multi-product co-opt input builders, where
it nets off the RRS reserve-balance RHS without touching the demand curve.
"""

import unittest

import numpy as np

from market_sim.config import constants as C
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.results.scarcity import (
    ercot_as_plan_requirement_mw,
    ercot_load_resource_reserve_credit_mw,
    ercot_load_resource_reserve_forward_mw,
    ercot_load_resource_reserve_mw,
    ercot_lr_rrs_availability_shape,
    ercot_lr_rrs_enrolled_mw,
    ercot_multiproduct_reserve_coopt_inputs,
    ercot_reserve_coopt_inputs,
)

_RRS_IDX = next(i for i, (_n, c, _t) in enumerate(C.ERCOT_AS_PRODUCTS) if c == "RRS")


def _fleet(hours):
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone="Z0",
            fuel_type=f,
            pmax_mw=100.0,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, f in enumerate(["gas_cc", "gas_ct", "coal", "nuclear", "oil"])
    ]
    return generators_to_fleet_arrays(gens, ["Z0"], hours=hours)


class TestEnrollmentTrajectory(unittest.TestCase):
    """enrolled_DR_MW(year): present ~0.9 GW, growing, protocol-capped ~1.4 GW."""

    def test_anchor_year_is_base_mw(self):
        self.assertAlmostEqual(
            ercot_lr_rrs_enrolled_mw(C.ERCOT_LR_RRS_ENROLL_BASE_YEAR),
            C.ERCOT_LR_RRS_ENROLL_BASE_MW,
        )

    def test_grows_with_year(self):
        y0 = C.ERCOT_LR_RRS_ENROLL_BASE_YEAR
        self.assertGreater(
            ercot_lr_rrs_enrolled_mw(y0 + 3), ercot_lr_rrs_enrolled_mw(y0)
        )
        # Linear growth at the published rate before the cap binds.
        self.assertAlmostEqual(
            ercot_lr_rrs_enrolled_mw(y0 + 2) - ercot_lr_rrs_enrolled_mw(y0),
            2 * C.ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR,
        )

    def test_saturates_at_cap(self):
        self.assertLessEqual(
            ercot_lr_rrs_enrolled_mw(2100), C.ERCOT_LR_RRS_ENROLL_CAP_MW
        )
        self.assertAlmostEqual(
            ercot_lr_rrs_enrolled_mw(2100), C.ERCOT_LR_RRS_ENROLL_CAP_MW
        )

    def test_today_is_about_point9_gw(self):
        # The brief's ~0.8-0.9 GW present level.
        self.assertTrue(800.0 <= ercot_lr_rrs_enrolled_mw(2025) <= 1000.0)

    def test_never_negative(self):
        self.assertGreaterEqual(ercot_lr_rrs_enrolled_mw(1990), 0.0)


class TestAvailabilityShape(unittest.TestCase):
    """The hour-of-day availability shape redistributes, never rescales, the level."""

    def test_mean_is_exactly_one(self):
        shape = ercot_lr_rrs_availability_shape(8760)
        self.assertAlmostEqual(float(shape.mean()), 1.0, places=12)

    def test_length_and_tiling(self):
        self.assertEqual(ercot_lr_rrs_availability_shape(8760).size, 8760)
        # Non-24-multiple horizon truncates cleanly (no hour loop, just np.tile).
        self.assertEqual(ercot_lr_rrs_availability_shape(50).size, 50)
        full = ercot_lr_rrs_availability_shape(48)
        np.testing.assert_allclose(full[:24], full[24:48])

    def test_daytime_above_overnight(self):
        shape = ercot_lr_rrs_availability_shape(24)
        self.assertGreater(shape[10], shape[2])  # HE 11 (daytime) > HE 03 (overnight)


class TestForwardCredit(unittest.TestCase):
    """lr_rrs(t) = enrolled_DR_MW(year) x availability_shape(t)."""

    def test_annual_mean_equals_enrolled(self):
        for year in (2026, 2030, 2040):
            fwd = ercot_load_resource_reserve_forward_mw(year, 8760)
            self.assertAlmostEqual(
                float(fwd.mean()), ercot_lr_rrs_enrolled_mw(year), places=6
            )

    def test_grows_with_enrollment(self):
        # Forward response: more enrollment -> more load-side reserve supply.
        early = ercot_load_resource_reserve_forward_mw(2026, 8760)
        late = ercot_load_resource_reserve_forward_mw(2034, 8760)
        self.assertGreater(float(late.mean()), float(early.mean()))


class TestModeAwareSelector(unittest.TestCase):
    """Backcast = measured NP3-911 (byte-identical); forecast = enrollment forward."""

    def test_backcast_is_byte_identical_to_measured(self):
        cfg = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=8760
        )
        got = ercot_load_resource_reserve_credit_mw(cfg, 8760)
        measured = ercot_load_resource_reserve_mw(2024, 8760)
        np.testing.assert_array_equal(got, measured)

    def test_forecast_is_the_forward_forecast(self):
        cfg = ScenarioConfig(
            iso="ERCOT", mode="forecast", weather_year=2024, hours=8760
        )
        got = ercot_load_resource_reserve_credit_mw(cfg, 8760, year=2030)
        np.testing.assert_array_equal(
            got, ercot_load_resource_reserve_forward_mw(2030, 8760)
        )

    def test_year_defaults_to_weather_year(self):
        cfg = ScenarioConfig(
            iso="ERCOT", mode="forecast", weather_year=2031, hours=8760
        )
        got = ercot_load_resource_reserve_credit_mw(cfg, 8760)
        np.testing.assert_array_equal(
            got, ercot_load_resource_reserve_forward_mw(2031, 8760)
        )


class TestSingleProductCredit(unittest.TestCase):
    """The credit nets off the single-lumped reserve-balance RHS (mode-aware)."""

    def test_off_then_on_lowers_requirement(self):
        fleet = _fleet(8760)
        off = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=8760
        )
        on = off.with_overrides(ercot_load_resource_reserve=True)
        req_off = ercot_reserve_coopt_inputs(off, fleet, 8760)[0]
        req_on = ercot_reserve_coopt_inputs(on, fleet, 8760)[0]
        self.assertLess(float(req_on.mean()), float(req_off.mean()))
        # Reduced by exactly the measured credit, clipped to the MCL floor.
        measured = ercot_load_resource_reserve_mw(2024, 8760)
        np.testing.assert_allclose(
            req_on, np.maximum(req_off - measured, float(on.ordc_mcl_mw))
        )

    def test_forecast_uses_enrollment(self):
        fleet = _fleet(8760)
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            weather_year=2024,
            hours=8760,
            ercot_load_resource_reserve=True,
        )
        req_off = ercot_reserve_coopt_inputs(
            cfg.with_overrides(ercot_load_resource_reserve=False), fleet, 8760
        )[0]
        req_near = ercot_reserve_coopt_inputs(cfg, fleet, 8760, sim_year=2026)[0]
        req_far = ercot_reserve_coopt_inputs(cfg, fleet, 8760, sim_year=2034)[0]
        # More enrollment (later year) -> more credit -> lower requirement.
        self.assertLess(float(req_far.mean()), float(req_near.mean()))
        self.assertLess(float(req_near.mean()), float(req_off.mean()))


class TestMultiProductCredit(unittest.TestCase):
    """The credit nets off only the RRS product RHS; the demand curve is untouched."""

    def _build(self, cfg, fleet, sim_year=None):
        return ercot_multiproduct_reserve_coopt_inputs(
            cfg, fleet, 8760, sim_year=sim_year
        )

    def test_flag_off_is_byte_identical(self):
        fleet = _fleet(8760)
        cfg = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=8760
        )
        req = self._build(cfg, fleet)[0]
        # With the flag off, the RRS row is the bare measured ASPLANNP433 series.
        np.testing.assert_array_equal(
            req[_RRS_IDX], ercot_as_plan_requirement_mw(2024, 8760, "RRS")
        )

    def test_backcast_reduces_only_rrs_by_measured(self):
        fleet = _fleet(8760)
        off = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=8760
        )
        on = off.with_overrides(ercot_load_resource_reserve=True)
        req_off, _, pen_off, wid_off, *_ = self._build(off, fleet)
        req_on, _, pen_on, wid_on, *_ = self._build(on, fleet)
        measured = ercot_load_resource_reserve_mw(2024, 8760)
        # RRS row drops by the measured credit (clipped at 0).
        np.testing.assert_allclose(
            req_on[_RRS_IDX], np.maximum(req_off[_RRS_IDX] - measured, 0.0)
        )
        # Every other product is untouched.
        for p in range(req_off.shape[0]):
            if p != _RRS_IDX:
                np.testing.assert_array_equal(req_on[p], req_off[p])
        # The demand curve (sized to the GROSS requirement peak) is unchanged —
        # only the balance RHS drops, preserving the steep tail.
        np.testing.assert_array_equal(pen_on, pen_off)
        np.testing.assert_array_equal(wid_on, wid_off)

    def test_forecast_grows_with_sim_year(self):
        fleet = _fleet(8760)
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            weather_year=2024,
            hours=8760,
            ercot_load_resource_reserve=True,
            ercot_as_forward_requirement=True,
        )
        # Forward AS requirement needs drivers; without them it falls back to the
        # measured RRS plan, which is enough to exercise the credit growth.
        near = self._build(cfg, fleet, sim_year=2026)[0][_RRS_IDX]
        far = self._build(cfg, fleet, sim_year=2034)[0][_RRS_IDX]
        self.assertLess(float(far.mean()), float(near.mean()))


if __name__ == "__main__":
    unittest.main()
