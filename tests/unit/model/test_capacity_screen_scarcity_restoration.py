"""FFR-8A ``capacity_screen_scarcity_restoration``: the lookahead scarcity tail.

Owner decision D-21(a), re-opened at sitting Addendum AC.1 (2026-08-07);
handoff ``docs/handoffs/ffr-8a-scarcity-restoration-2026-08-08.md``. The gate
repairs the unified lookahead's ORDC tail with three published-design
elements, all from existing model state:

* **E1** — the tail's reserve quantity becomes the forward COMMITTED
  capability (RTOLCAP/RTOFFCAP share tables + the storage AS share), bounded
  by the physical stack headroom
  (:func:`market_sim.results.scarcity.ercot_lookahead_committed_reserves`);
* **E2** — the energy-stack search runs at net load + the thermal-held
  responsive AS plan (forward NP3-160-CD requirement model;
  :func:`market_sim.results.scarcity.ercot_lookahead_as_hold_mw`);
* **E4** — the tail prices ``E[adder(R + eps)]`` over the fleet's own
  forced-outage realization distribution
  (:func:`market_sim.results.scarcity.ercot_fleet_forced_outage_sigma_mw`,
  :func:`market_sim.results.scarcity.ercot_lookahead_expected_ordc_adder`).

Default OFF and the OFF path byte-identical: the first class reproduces the
shipped hand-computed series with the new arguments omitted AND at their
explicit defaults, and pins the default cache key (the nyiso-128 discipline).
Trivial-first per CLAUDE.md: 2-3-unit stacks, 4/24/48-hour horizons,
hand-computed reserves and quadrature checks.
"""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.results.scarcity import (
    ercot_fleet_forced_outage_sigma_mw,
    ercot_lookahead_as_hold_mw,
    ercot_lookahead_committed_reserves,
    ercot_lookahead_expected_ordc_adder,
    ercot_rtolcap_forward_supply_cap_mw,
)
from market_sim.runner import _lookahead_reprice_signal

# The pinned default-config cache key (tests/regression/test_persisted_identity
# .PINNED_DEFAULT_CACHE_KEY) — asserted here too so this mechanism's own suite
# fails loudly if its field ever enters the default hash.
# ADVANCED 2026-09-06, e5ecd4105ada3e58 -> 547053bdfccd4264 — capx D65-B's
# COUPLED ccs_retrofit_fixed_cost_co2_scaling (Act A, a declared (b'-1)
# default flip) + ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$ (Act B, a
# plain value field with no drop value, so it re-keys unconditionally).
# Nothing about THIS file's mechanism moved — the pin advances because the
# global default did. Rationale and provenance live on the pin in
# tests/regression/test_persisted_identity.py; pre-declared BEFORE the solve
# in docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md §3. Re-pinned here by
# capx D65-B-R, completing the partial re-key fb93b76e left behind.
_PINNED_DEFAULT_KEY = "547053bdfccd4264"


def _three_unit_fixture(T=4):
    """The test_price_signal.py stack: mc [10, 20, 50], 5 GW each, avail 1."""
    fleet_arrays = SimpleNamespace(
        pmax=np.array([5000.0, 5000.0, 5000.0]),
        availability=np.ones((3, T)),
    )
    mc_cost = np.tile(np.array([[10.0], [20.0], [50.0]]), (1, T))
    result = SimpleNamespace(
        wind_dispatched=np.zeros((1, T)),
        solar_dispatched=np.zeros((1, T)),
    )
    base_demand = np.array([[2000.0, 7000.0, 12000.0, 20000.0]])
    return fleet_arrays, mc_cost, result, base_demand


class TestGate(unittest.TestCase):
    """Field default, registration, cache-key pins, and posture validation."""

    def test_field_defaults_off(self):
        self.assertFalse(ScenarioConfig().capacity_screen_scarcity_restoration)

    def test_field_is_registered_cache_key_optional(self):
        self.assertIn(
            "capacity_screen_scarcity_restoration", _CACHE_KEY_OPTIONAL_FIELDS
        )

    def test_default_cache_key_is_unmoved(self):
        self.assertEqual(ScenarioConfig().cache_key(), _PINNED_DEFAULT_KEY)

    def test_armed_run_gets_a_distinct_cache_key(self):
        armed = ScenarioConfig(
            iso="ERCOT",
            capacity_screen_unified_lookahead=True,
            capacity_screen_scarcity_restoration=True,
        )
        control = ScenarioConfig(iso="ERCOT", capacity_screen_unified_lookahead=True)
        self.assertNotEqual(armed.cache_key(), control.cache_key())

    def test_requires_unified_lookahead(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="ERCOT", capacity_screen_scarcity_restoration=True)

    def test_requires_ercot(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="PJM",
                capacity_screen_unified_lookahead=True,
                capacity_screen_scarcity_restoration=True,
            )


class TestOffPathByteIdentical(unittest.TestCase):
    """The unarmed signal path is byte-identical through the new code."""

    def test_shipped_hand_computed_series_unchanged(self):
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        signal = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=2
        )
        np.testing.assert_allclose(signal[0], [10.0, 20.0, 50.0, 50.0])
        np.testing.assert_allclose(signal[1], signal[0])

    def test_explicit_defaults_are_byte_identical(self):
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        implicit = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        explicit = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            scarcity_restoration=None,
            diagnostics=None,
        )
        self.assertTrue(np.array_equal(implicit, explicit))

    def test_diagnostics_dict_does_not_change_the_signal(self):
        # The dump channel is observation-only: passing a diagnostics dict
        # returns the identical signal and fills the stack internals.
        fleet_arrays, mc_cost, result, base_demand = _three_unit_fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        plain = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        diag: dict = {}
        observed = _lookahead_reprice_signal(
            config,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            diagnostics=diag,
        )
        self.assertTrue(np.array_equal(plain, observed))
        self.assertEqual(diag["entering_year"], 2024)
        np.testing.assert_allclose(diag["net_load_mw"], base_demand.sum(axis=0))
        np.testing.assert_allclose(
            diag["installed_headroom_mw"],
            15000.0 - base_demand.sum(axis=0),
        )
        np.testing.assert_allclose(diag["adder_usd_mwh"], np.zeros(4))


class TestIncludeOfflineExtension(unittest.TestCase):
    """``include_offline`` forces the tier shape; ``None`` keeps legacy."""

    def _fleet(self, T=24):
        return SimpleNamespace(
            pmax=np.array([1000.0, 500.0]),
            plant_group=np.array(["COAL", "CT_PEAKER"], dtype=object),
        )

    def test_none_keeps_legacy_single_row_without_coopt(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        rows = ercot_rtolcap_forward_supply_cap_mw(
            cfg, self._fleet(), 24, net_load=np.linspace(100.0, 1200.0, 24)
        )
        self.assertEqual(rows.shape[0], 1)

    def test_true_forces_two_rows_and_false_forces_one(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        nl = np.linspace(100.0, 1200.0, 24)
        two = ercot_rtolcap_forward_supply_cap_mw(
            cfg, self._fleet(), 24, net_load=nl, include_offline=True
        )
        one = ercot_rtolcap_forward_supply_cap_mw(
            cfg, self._fleet(), 24, net_load=nl, include_offline=False
        )
        self.assertEqual(two.shape[0], 2)
        self.assertEqual(one.shape[0], 1)
        # The offline tier adds on top of the online tier.
        self.assertTrue(np.all(two[1] >= two[0]))
        np.testing.assert_allclose(one[0], two[0])


class TestCommittedReserves(unittest.TestCase):
    """E1: the min() of committed capability and physical headroom."""

    def test_physical_bound_binds_in_shortage_hours(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        fleet = SimpleNamespace(
            pmax=np.array([20000.0, 8000.0]),
            plant_group=np.array(["CC_REGULAR", "CT_PEAKER"], dtype=object),
        )
        T = 24
        nl = np.full(T, 15000.0)
        # Physical headroom collapses to 500 MW in hour 3 and goes negative
        # in hour 4 — the committed-capability tables cannot exceed it.
        phys = np.full(T, 12000.0)
        phys[3] = 500.0
        phys[4] = -250.0
        r_on, r_full = ercot_lookahead_committed_reserves(
            cfg, fleet, T, net_load=nl, phys_headroom=phys, storage_as_mw=0.0
        )
        self.assertEqual(r_on[3], 500.0)
        self.assertEqual(r_on[4], -250.0)
        self.assertEqual(r_full[3], 500.0)
        # In unconstrained hours the committed tables bind (below 12 GW here).
        self.assertLess(r_on[0], 12000.0)
        self.assertTrue(np.all(r_full >= r_on))

    def test_storage_as_adds_to_the_online_tier(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        fleet = SimpleNamespace(
            pmax=np.array([20000.0]),
            plant_group=np.array(["CC_REGULAR"], dtype=object),
        )
        T = 24
        nl = np.full(T, 10000.0)
        phys = np.full(T, 50000.0)  # never binds
        r0, _ = ercot_lookahead_committed_reserves(
            cfg, fleet, T, net_load=nl, phys_headroom=phys, storage_as_mw=0.0
        )
        r1, _ = ercot_lookahead_committed_reserves(
            cfg, fleet, T, net_load=nl, phys_headroom=phys, storage_as_mw=750.0
        )
        np.testing.assert_allclose(r1 - r0, 750.0)

    def test_missing_plant_group_raises(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        fleet = SimpleNamespace(pmax=np.array([1000.0]), plant_group=None)
        with self.assertRaises(ValueError):
            ercot_lookahead_committed_reserves(
                cfg,
                fleet,
                4,
                net_load=np.full(4, 500.0),
                phys_headroom=np.full(4, 500.0),
                storage_as_mw=0.0,
            )


class TestExpectedAdder(unittest.TestCase):
    """E4: the Gauss-Hermite expectation of the published curve."""

    def _cfg(self):
        return ScenarioConfig(iso="ERCOT", mode="forecast")

    def test_zero_sigma_reproduces_the_point_evaluation(self):
        cfg = self._cfg()
        T = 6
        r = np.array([2000.0, 4000.0, 6000.0, 8000.0, 12000.0, 20000.0])
        lam = np.full(T, 30.0)
        from market_sim.results.scarcity import floor_active_mask, ordc_adder
        from market_sim.results.scarcity import resolve_lolp_params

        mu, sigma = resolve_lolp_params(cfg, T)
        point = ordc_adder(
            r,
            lam,
            voll=cfg.ordc_voll,
            mcl_mw=cfg.ordc_mcl_mw,
            mu_mw=mu,
            sigma_mw=sigma,
            shift_sigma=cfg.ordc_lolp_shift_sigma,
            multistep_floor=cfg.ordc_multistep_floor,
            floor_active=floor_active_mask(2024, T),
            reserves_online_mw=r,
        )
        expected = ercot_lookahead_expected_ordc_adder(
            cfg,
            2024,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=np.zeros(T),
        )
        np.testing.assert_allclose(expected, point, rtol=1e-12)

    def test_uncertainty_lifts_the_convex_tail(self):
        # At reserves comfortably above the knee the curve is convex, so the
        # expectation exceeds the point value (Jensen) — the LOLP-bearing
        # behaviour the charter demands: a smooth object prices zero where
        # the distribution of realizations prices the dip risk.
        cfg = self._cfg()
        T = 1
        r = np.array([9000.0])
        lam = np.array([30.0])
        point = ercot_lookahead_expected_ordc_adder(
            cfg,
            2024,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=np.zeros(T),
        )
        expected = ercot_lookahead_expected_ordc_adder(
            cfg,
            2024,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=np.full(T, 1800.0),
        )
        self.assertLess(float(point[0]), 1.0)
        self.assertGreater(float(expected[0]), float(point[0]) + 1.0)

    def test_expectation_respects_the_voll_cap(self):
        cfg = self._cfg()
        T = 1
        r = np.array([-500.0])  # deep shortage: adder pins to VOLL - lambda
        lam = np.array([120.0])
        expected = ercot_lookahead_expected_ordc_adder(
            cfg,
            2024,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=np.full(T, 2000.0),
        )
        self.assertLessEqual(float(expected[0]), cfg.ordc_voll - 120.0 + 1e-9)

    def test_floor_is_date_gated_by_entering_year(self):
        # OBDRR048 took effect 2023-11-01: an entering-2022 pro-forma carries
        # no floor; an entering-2024 one carries it in every hour. At the
        # shipped fallback sigma the curve sits above the floor throughout the
        # floor band (the floor is inert there), so the mask is exercised at a
        # tighter sigma where the unfloored tail is ~$0 inside the band and
        # the $20 step is the entire adder.
        cfg = self._cfg().with_overrides(ordc_lolp_sigma_mw=700.0)
        T = 1
        r = np.array([6400.0])  # inside the $20 floor band; tail ~ $0 here
        lam = np.array([25.0])
        e22 = ercot_lookahead_expected_ordc_adder(
            cfg,
            2022,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=np.zeros(T),
        )
        e24 = ercot_lookahead_expected_ordc_adder(
            cfg,
            2024,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=np.zeros(T),
        )
        self.assertGreaterEqual(float(e24[0]), 20.0)
        self.assertLess(float(e22[0]), 1.0)

    def test_quadrature_order_is_converged(self):
        # Doubling the order does not move the result materially — the fixed
        # order is a resolution constant, not a tunable. The worst case (the
        # administrative LOLP=1 pin near the MCL) is included: measured
        # 31-vs-61 agreement is <= 0.3 % there and < 0.1 % elsewhere.
        import market_sim.results.scarcity as sc

        cfg = self._cfg()
        r = np.array([5000.0, 7000.0, 9000.0, 12000.0])
        lam = np.full(4, 40.0)
        sig = np.full(4, 1600.0)
        base = ercot_lookahead_expected_ordc_adder(
            cfg,
            2024,
            r_online_mw=r,
            r_full_mw=r,
            system_lambda=lam,
            sigma_r_mw=sig,
        )
        orig = sc._FFR8A_GH_ORDER
        try:
            sc._FFR8A_GH_ORDER = 61
            fine = ercot_lookahead_expected_ordc_adder(
                cfg,
                2024,
                r_online_mw=r,
                r_full_mw=r,
                system_lambda=lam,
                sigma_r_mw=sig,
            )
        finally:
            sc._FFR8A_GH_ORDER = orig
        np.testing.assert_allclose(base, fine, rtol=1e-2, atol=0.1)


class TestSigmaR(unittest.TestCase):
    """The fleet forced-outage sigma from the model's own rates."""

    def _gen(self, pmax, group="", eford=0.05, plant_code=0, fuel="gas_cc"):
        return SimpleNamespace(
            pmax_mw=pmax,
            plant_group=group,
            eford=eford,
            plant_code=plant_code,
            online_year=2000,
            fuel_type=fuel,
        )

    def test_hand_computed_single_unit(self):
        # One 1,000 MW unit outside the WEFOR table at eford 0.05:
        # sigma = sqrt(0.05 * 0.95) * 1000 in every season.
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        sig = ercot_fleet_forced_outage_sigma_mw([self._gen(1000.0)], cfg, 2024, 8760)
        np.testing.assert_allclose(sig, np.sqrt(0.05 * 0.95) * 1000.0)

    def test_plant_grain_aggregates_tranches(self):
        # Two 500 MW tranches of ONE plant share the outage state: variance
        # q(1-q) * 1000^2, strictly larger than two independent 500 MW units.
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        same_plant = [
            self._gen(500.0, plant_code=77),
            self._gen(500.0, plant_code=77),
        ]
        two_plants = [
            self._gen(500.0, plant_code=77),
            self._gen(500.0, plant_code=88),
        ]
        s_same = ercot_fleet_forced_outage_sigma_mw(same_plant, cfg, 2024, 24)
        s_two = ercot_fleet_forced_outage_sigma_mw(two_plants, cfg, 2024, 24)
        np.testing.assert_allclose(s_same, np.sqrt(0.05 * 0.95) * 1000.0)
        np.testing.assert_allclose(s_two, np.sqrt(2 * 0.05 * 0.95 * 500.0**2))
        self.assertGreater(float(s_same[0]), float(s_two[0]))

    def test_non_reserve_fuels_are_excluded(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        sig = ercot_fleet_forced_outage_sigma_mw(
            [self._gen(1000.0, fuel="wind")], cfg, 2024, 24
        )
        np.testing.assert_allclose(sig, 0.0)

    def test_seasonal_composition_follows_the_wefor_split(self):
        # A WEFOR-table unit carries the availability builder's seasonal
        # reallocation: summer rate = SUMMER_WEFOR_SHARE x annual.
        from market_sim.data.fleet.arrays import (
            _SUMMER_WEFOR_SHARE,
            _thermal_outage,
        )

        cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
        gen = self._gen(1000.0, group="CC_REGULAR", fuel="gas_cc")
        sig = ercot_fleet_forced_outage_sigma_mw([gen], cfg, 2024, 8760)
        _, wefor, _ = _thermal_outage("CC_REGULAR", 24.0)
        q_summer = _SUMMER_WEFOR_SHARE * wefor
        # July 1 12:00 (non-leap hour 181*24+12) is a summer hour.
        expect_summer = np.sqrt(q_summer * (1 - q_summer)) * 1000.0
        self.assertAlmostEqual(float(sig[181 * 24 + 12]), expect_summer, places=6)
        # January 1 00:00 is winter: the full annual rate.
        expect_winter = np.sqrt(wefor * (1 - wefor)) * 1000.0
        self.assertAlmostEqual(float(sig[0]), expect_winter, places=6)


class TestAsHold(unittest.TestCase):
    """E2: the thermal-held responsive AS quantity."""

    def _series(self, T=8760):
        load = np.full(T, 50000.0)
        wind = np.full(T, 9000.0)
        solar = np.full(T, 4000.0)
        return load, wind, solar

    def test_ecrs_is_zero_before_its_launch_year(self):
        load, wind, solar = self._series()
        h22 = ercot_lookahead_as_hold_mw(
            2022,
            8760,
            load_mw=load,
            wind_mw=wind,
            solar_mw=solar,
            storage_as_mw=0.0,
        )
        h24 = ercot_lookahead_as_hold_mw(
            2024,
            8760,
            load_mw=load,
            wind_mw=wind,
            solar_mw=solar,
            storage_as_mw=0.0,
        )
        # Constant drivers: the ECRS requirement is the whole difference.
        self.assertGreater(float(h24.mean() - h22.mean()), 500.0)

    def test_launch_year_gates_at_the_go_live_hour(self):
        from market_sim.config.reserve_config import ERCOT_ECRS_LAUNCH_HOUR

        load, wind, solar = self._series()
        h23 = ercot_lookahead_as_hold_mw(
            2023,
            8760,
            load_mw=load,
            wind_mw=wind,
            solar_mw=solar,
            storage_as_mw=0.0,
        )
        self.assertGreater(float(h23[ERCOT_ECRS_LAUNCH_HOUR]), float(h23[0]) + 500.0)

    def test_storage_and_lr_net_out_and_clip_at_zero(self):
        load, wind, solar = self._series(T=24)
        base = ercot_lookahead_as_hold_mw(
            2024,
            24,
            load_mw=load[:24],
            wind_mw=wind[:24],
            solar_mw=solar[:24],
            storage_as_mw=0.0,
        )
        netted = ercot_lookahead_as_hold_mw(
            2024,
            24,
            load_mw=load[:24],
            wind_mw=wind[:24],
            solar_mw=solar[:24],
            storage_as_mw=1500.0,
        )
        self.assertTrue(np.all(base - netted >= 0.0))
        huge = ercot_lookahead_as_hold_mw(
            2024,
            24,
            load_mw=load[:24],
            wind_mw=wind[:24],
            solar_mw=solar[:24],
            storage_as_mw=1e6,
        )
        np.testing.assert_allclose(huge, 0.0)


class TestArmedEndToEnd(unittest.TestCase):
    """The armed lookahead on a realistic-classed trivial fleet."""

    def _armed_fixture(self, T=24):
        fleet_arrays = SimpleNamespace(
            pmax=np.array([20000.0, 15000.0, 10000.0]),
            availability=np.ones((3, T)),
            plant_group=np.array(["CC_REGULAR", "COAL", "CT_PEAKER"], dtype=object),
        )
        mc_cost = np.tile(np.array([[15.0], [25.0], [45.0]]), (1, T))
        result = SimpleNamespace(
            wind_dispatched=np.zeros((1, T)),
            solar_dispatched=np.zeros((1, T)),
        )
        # A moderately loaded day: net load runs to 36 GW against 45 GW
        # installed, so the installed-headroom point tail stays >= 9 GW
        # (adder ~ $0) while the committed-capability tables and the
        # outage-uncertainty expectation price the dip risk.
        base_demand = np.linspace(20000.0, 36000.0, T).reshape(1, T)
        return fleet_arrays, mc_cost, result, base_demand

    def _configs(self):
        control = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            scarcity_pricing_enabled=True,
            scarcity_price_overlay=True,
            capacity_screen_unified_lookahead=True,
        )
        armed = control.with_overrides(capacity_screen_scarcity_restoration=True)
        return control, armed

    def test_armed_tail_prices_scarcity_the_point_tail_misses(self):
        fleet_arrays, mc_cost, result, base_demand = self._armed_fixture()
        control, armed = self._configs()
        T = 24
        kwargs = dict(
            demand_next_total=base_demand.sum(axis=0),
            hourly_availability=True,
        )
        diag_control: dict = {}
        sig_control = _lookahead_reprice_signal(
            control,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            1,
            diagnostics=diag_control,
            **kwargs,
        )
        bundle = {
            "wind_potential_mw": np.zeros(T),
            "solar_potential_mw": np.zeros(T),
            "sigma_r_mw": np.full(T, 1500.0),
            "storage_as_mw": 0.0,
        }
        diag: dict = {}
        sig_armed = _lookahead_reprice_signal(
            armed,
            2024,
            base_demand,
            fleet_arrays,
            mc_cost,
            result,
            1,
            scarcity_restoration=bundle,
            diagnostics=diag,
            **kwargs,
        )
        # The control's installed-headroom point tail sits at ~$0 on this
        # fixture; the armed tail prices the committed-capability dip risk.
        self.assertLess(float(diag_control["adder_usd_mwh"].max()), 1.0)
        self.assertGreater(float(diag["adder_usd_mwh"].max()), 1.0)
        self.assertGreater(float(sig_armed.mean()), float(sig_control.mean()))
        self.assertIn("r_online_mw", diag)
        self.assertIn("as_hold_mw", diag)
        # E2 shifts the marginal position: the armed base price (pre-tail) in
        # the tightest hour reaches at least the control's base tranche.
        self.assertGreaterEqual(
            float(diag["price_base_usd_mwh"][-1]),
            float(diag_control["price_base_usd_mwh"][-1]),
        )
        # Committed reserves never exceed the physical headroom.
        self.assertTrue(
            np.all(diag["r_full_mw"] <= diag["installed_headroom_mw"] + 1e-9)
        )


if __name__ == "__main__":
    unittest.main()
