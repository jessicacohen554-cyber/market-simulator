"""Tests for ERCOT's multi-product energy+AS co-optimization.

Builds from the trivial case up (CLAUDE.md testing pattern): a 1-generator,
1-zone, 24-hour LP with a single binding AS product, then additivity, the
quality cascade, and the scarcity-input builder. Every price in these tests is
recovered as an LP dual — the honesty gate of the whole build is that the
binding product's reserve price forms from the shared-headroom/reserve-balance
duals, never an exogenous adder tuned to a target.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.results.scarcity import (
    ercot_as_forward_drivers,
    ercot_as_forward_requirement_mw,
    ercot_multiproduct_reserve_coopt_inputs,
    nyiso_rcpf_product_shortfall_steps,
)


def _fleet(fuels, zone_names, hours, pmax=100.0, pmin=0.0):
    """One generator per fuel in ``fuels``, all in zone ``zone_names[0]``."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone_names[0],
            fuel_type=f,
            pmax_mw=pmax,
            pmin_mw=pmin,
            eford=0.0,  # no derate -> headroom is exactly pmax - dispatch
        )
        for i, f in enumerate(fuels)
    ]
    return generators_to_fleet_arrays(gens, zone_names, hours=hours)


def _one_product(req_mw, max_penalty, n_ramp=10):
    """A single-product co-opt parameter bundle for solve_dispatch."""
    pen, wid = nyiso_rcpf_product_shortfall_steps(req_mw, 0.0, max_penalty, n_ramp)
    return dict(
        reserve_requirement=np.full((1, 24), float(req_mw)),
        reserve_eligible=np.ones((1, 1), dtype=bool),
        ordc_penalties=pen,
        ordc_step_widths=wid,
        reserve_balance_zone_mask=np.ones((1, 1), dtype=bool),
        reserve_balance_ordc_counts=np.array([pen.size]),
        reserve_balance_class=np.array([0]),
        reserve_headroom_eligible=np.ones((1, 1), dtype=bool),
        reserve_headroom_products=np.ones((1, 1), dtype=bool),
    )


class TestTrivialBindingProduct(unittest.TestCase):
    """1 gen, 1 zone, 24 h, one AS product — the trivial case first."""

    def _solve(self, req_mw, demand_mw=60.0, mc=20.0, max_penalty=1000.0):
        fleet = _fleet(["gas_cc"], ["Z0"], hours=24)
        demand = np.full((1, 24), demand_mw)
        mc_arr = np.full((1, 24), mc)
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc_arr,
            voll=5000.0,
            **_one_product(req_mw, max_penalty),
        )

    def test_slack_reserve_does_not_price(self):
        # Headroom = 100 - 60 = 40 MW > 30 MW requirement -> reserve met free.
        r = self._solve(req_mw=30.0)
        self.assertIsNotNone(r.reserve_price)
        self.assertLess(float(r.reserve_price.max()), 1e-6)
        # Energy price is just the marginal cost — no scarcity lift.
        np.testing.assert_allclose(r.prices[0], 20.0, atol=1e-6)

    def test_binding_reserve_prices_and_lifts_lmp(self):
        # Requirement 90 MW > 40 MW headroom -> 50 MW shortfall, reserve prices.
        r = self._solve(req_mw=90.0)
        rp = float(r.reserve_price[0])
        self.assertGreater(rp, 0.0)
        # Co-optimization identity: a marginal MWh of energy gives up a MW of
        # reserve worth the reserve price, so LMP = mc + reserve price exactly.
        np.testing.assert_allclose(r.prices[0], 20.0 + rp, atol=1e-5)

    def test_reserve_price_monotonic_in_requirement(self):
        # A tighter AS requirement clears reserve lower on the demand curve ->
        # a higher reserve price (the scarcity is endogenous to headroom).
        low = float(self._solve(req_mw=70.0).reserve_price[0])
        high = float(self._solve(req_mw=95.0).reserve_price[0])
        self.assertGreater(high, low)

    def test_price_is_a_dual_not_an_adder(self):
        # Honesty gate: with the offer cap (max penalty) raised, the *same*
        # physical shortfall prices higher — the price tracks the demand curve
        # the LP clears against, not a fixed exogenous number.
        cheap = float(self._solve(req_mw=90.0, max_penalty=1000.0).reserve_price[0])
        dear = float(self._solve(req_mw=90.0, max_penalty=4000.0).reserve_price[0])
        self.assertGreater(dear, cheap + 1.0)


class TestAdditivity(unittest.TestCase):
    """Additive products (shared headroom) create scarcity independent ones don't."""

    def _two_products(self, additive):
        fleet = _fleet(["gas_cc"], ["Z0"], hours=24)
        demand = np.full((1, 24), 60.0)  # headroom = 40 MW
        mc = np.full((1, 24), 20.0)
        pen, wid = nyiso_rcpf_product_shortfall_steps(30.0, 0.0, 1000.0, 10)
        # Two products, each requiring 30 MW. Together 60 MW > 40 MW headroom.
        kwargs = dict(
            reserve_requirement=np.full((2, 24), 30.0),
            reserve_eligible=np.ones((2, 1), dtype=bool),
            ordc_penalties=np.concatenate([pen, pen]),
            ordc_step_widths=np.concatenate([wid, wid]),
            reserve_balance_zone_mask=np.ones((2, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([pen.size, pen.size]),
            reserve_balance_class=np.array([0, 1]),
        )
        if additive:
            # Both products share ONE headroom row -> compete for the 40 MW.
            kwargs["reserve_headroom_eligible"] = np.ones((1, 1), dtype=bool)
            kwargs["reserve_headroom_products"] = np.ones((1, 2), dtype=bool)
        else:
            # Each product its own headroom row -> each independently reuses 40.
            kwargs["reserve_headroom_eligible"] = np.ones((2, 1), dtype=bool)
            kwargs["reserve_headroom_products"] = np.eye(2, dtype=bool)
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            **kwargs,
        )

    def test_independent_products_do_not_price(self):
        # 30 MW each <= 40 MW headroom when each gets its own pool -> no scarcity.
        r = self._two_products(additive=False)
        self.assertLess(float(r.reserve_price.max()), 1e-6)

    def test_additive_products_price(self):
        # 30 + 30 = 60 MW > 40 MW shared headroom -> scarcity forms.
        r = self._two_products(additive=True)
        self.assertGreater(float(r.reserve_price.max()), 0.0)


class TestQualityCascade(unittest.TestCase):
    """Higher-quality substitutes down: a slow product reaches the peaker pool."""

    def _solve(self, products_in_slow_only):
        # gas_cc (fast/spinning, 30 MW) + gas_ct (quick-start peaker, 400 MW).
        # Demand 180 MW. The fast pool (gas_cc, 30 MW) is smaller than the 45 MW
        # fast requirement, so the fast product is short no matter how the LP
        # redispatches; the slow product reaches the large peaker pool and is met.
        gens = [
            Generator(
                unit_id="CC",
                name="CC",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=30.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="CT",
                name="CT",
                zone="Z0",
                fuel_type="gas_ct",
                pmax_mw=400.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, ["Z0"], hours=24)
        demand = np.full((1, 24), 180.0)
        mc = np.full((2, 24), 20.0)
        pen, wid = nyiso_rcpf_product_shortfall_steps(45.0, 0.0, 1000.0, 10)
        # Two products: index 0 "fast" (gas_cc only), index 1 "slow" (both).
        fast_elig = np.array([[True, False]])  # row 0: gas_cc only
        all_elig = np.array([[True, True]])  # row 1: both
        kwargs = dict(
            reserve_requirement=np.full((2, 24), 45.0),
            reserve_eligible=np.ones((2, 2), dtype=bool),
            ordc_penalties=np.concatenate([pen, pen]),
            ordc_step_widths=np.concatenate([wid, wid]),
            reserve_balance_zone_mask=np.ones((2, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([pen.size, pen.size]),
            reserve_balance_class=np.array([0, 1]),
            reserve_headroom_eligible=np.vstack([fast_elig, all_elig]),
            # Row 0 (fast pool) bounds product 0; row 1 (all pool) bounds both.
            reserve_headroom_products=np.array(
                [[True, False], [True, True]], dtype=bool
            ),
        )
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            **kwargs,
        )

    def test_fast_product_prices_higher_than_slow(self):
        # The fast pool (gas_cc, 30 MW) cannot cover the 45 MW fast requirement,
        # so the fast product is short and prices; the slow product reaches the
        # 400 MW peaker pool and is met free. Fast dual must exceed slow dual.
        r = self._solve(products_in_slow_only=False)
        by_fam = r.reserve_price_by_family  # (T, 2): col 0 fast, col 1 slow
        self.assertIsNotNone(by_fam)
        self.assertGreater(float(by_fam[0, 0]), float(by_fam[0, 1]))
        # The binding MCPC is the per-hour max across products.
        self.assertAlmostEqual(
            float(r.reserve_price_by_family.max(axis=1)[0]),
            float(by_fam[0, 0]),
            places=6,
        )


class TestMultiProductInputs(unittest.TestCase):
    """The scarcity input builder shapes and cascade membership."""

    def _fleet(self):
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
        return generators_to_fleet_arrays(gens, ["Z0"], hours=48)

    def test_builder_shapes_and_cascade(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2024, hours=48)
        fleet = self._fleet()
        (
            req,
            elig,
            pen,
            wid,
            zmask,
            counts,
            rclass,
            hr_elig,
            hr_prod,
        ) = ercot_multiproduct_reserve_coopt_inputs(cfg, fleet, 48)
        n_prod = 4  # RegUp/RRS/ECRS/NonSpin
        self.assertEqual(req.shape, (n_prod, 48))
        self.assertEqual(elig.shape, (n_prod, fleet.n_gen))
        self.assertEqual(zmask.shape, (n_prod, 1))
        self.assertTrue(zmask.all())
        self.assertEqual(rclass.tolist(), [0, 1, 2, 3])
        self.assertEqual(int(counts.sum()), pen.size)
        self.assertEqual(pen.shape, wid.shape)
        # Two nested headroom rows: fast (excludes quick-start peakers) and all.
        self.assertEqual(hr_elig.shape, (2, fleet.n_gen))
        self.assertEqual(hr_prod.shape, (2, n_prod))
        # The "all" row (index 1) bounds every product; the "fast" row only the
        # three fast products (RegUp/RRS/ECRS), not Non-Spin.
        self.assertTrue(hr_prod[1].all())
        self.assertEqual(hr_prod[0].tolist(), [True, True, True, False])
        # Fast pool excludes the gas_ct/oil quick-start peakers; all pool keeps
        # them (offline quick-start can back Non-Spin).
        self.assertGreater(int(hr_elig[1].sum()), int(hr_elig[0].sum()))

    def test_requirements_match_measured_as_plan(self):
        # The per-product requirement is the measured ASPLANNP433 realization —
        # a validation target, not a fit. 2024 means are well-known (REGUP ~406,
        # RRS ~2722, ECRS ~1747, NSPIN ~2688 MW).
        cfg = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=8760
        )
        fleet = self._fleet()
        req = ercot_multiproduct_reserve_coopt_inputs(cfg, fleet, 8760)[0]
        means = req.mean(axis=1)
        self.assertGreater(means[0], 300.0)  # RegUp
        self.assertGreater(means[1], 2000.0)  # RRS
        self.assertGreater(means[2], 1000.0)  # ECRS (active 2024)
        self.assertGreater(means[3], 2000.0)  # NonSpin


class TestForwardRequirement(unittest.TestCase):
    """The forward AS requirement formula (G3) — driver-responsive, not measured."""

    def _fleet(self):
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
        return generators_to_fleet_arrays(gens, ["Z0"], hours=48)

    def _drivers(self, load, wind, solar, hours=48):
        return ercot_as_forward_drivers(
            np.full(hours, load), np.full(hours, wind), np.full(hours, solar)
        )

    def test_off_returns_none_falls_back_to_measured(self):
        # Default off → the forward formula returns None so the co-opt reads the
        # measured ASPLANNP433 (keeper/backcast path unchanged).
        cfg = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2024, hours=48)
        d = self._drivers(50000, 10000, 5000)
        for code in ("REGUP", "RRS", "ECRS", "NSPIN"):
            self.assertIsNone(ercot_as_forward_requirement_mw(cfg, code, 48, d))

    def test_on_but_no_drivers_returns_none(self):
        # Forward requested but drivers not threaded → defer to measured, never
        # guess.
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        self.assertIsNone(ercot_as_forward_requirement_mw(cfg, "REGUP", 48, None))

    def test_products_in_published_bands(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        d = self._drivers(50000, 13000, 6000)
        reg = ercot_as_forward_requirement_mw(cfg, "REGUP", 48, d)
        rrs = ercot_as_forward_requirement_mw(cfg, "RRS", 48, d)
        ecrs = ercot_as_forward_requirement_mw(cfg, "ECRS", 48, d)
        nspin = ercot_as_forward_requirement_mw(cfg, "NSPIN", 48, d)
        # Published-order levels (cf. measured 2024 means REGUP~406, RRS~2722,
        # ECRS~1747, NSPIN~2688 MW).
        self.assertTrue(200 < reg.mean() < 900)
        self.assertTrue(2300 <= rrs.mean() < 3300)  # floor = largest contingency
        self.assertTrue(900 < ecrs.mean() < 2800)
        self.assertTrue(2000 < nspin.mean() < 3600)
        self.assertEqual(reg.shape, (48,))

    def test_unknown_product_defers(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        d = self._drivers(50000, 10000, 5000)
        self.assertIsNone(ercot_as_forward_requirement_mw(cfg, "REGDN", 48, d))

    def test_more_vre_raises_requirement(self):
        # Forward response: more VRE → larger forecast-error / ramp / VRE-share →
        # larger requirement, automatically (the whole point of the forward seam).
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        low = self._drivers(50000, 8000, 2000)
        high = self._drivers(50000, 20000, 14000)
        # RegUp (forecast-error), RRS (inertia) and ECRS (forecast-error + ramp)
        # rise with VRE at fixed load. Non-Spin is a load-ratio product (driven by
        # load + ramp, not VRE level), so it is checked separately below.
        for code in ("REGUP", "RRS", "ECRS"):
            lo = ercot_as_forward_requirement_mw(cfg, code, 48, low).mean()
            hi = ercot_as_forward_requirement_mw(cfg, code, 48, high).mean()
            self.assertGreater(hi, lo, f"{code} should rise with VRE")

    def test_nspin_rises_with_load(self):
        # Non-Spin is a load-ratio product: it rises with system load (the
        # published Non-Spin driver), not VRE level.
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        lo = ercot_as_forward_requirement_mw(
            cfg, "NSPIN", 48, self._drivers(45000, 10000, 5000)
        ).mean()
        hi = ercot_as_forward_requirement_mw(
            cfg, "NSPIN", 48, self._drivers(70000, 10000, 5000)
        ).mean()
        self.assertGreater(hi, lo)

    def test_ramp_drives_ecrs(self):
        # ECRS carries a net-load up-ramp term: a swinging net-load profile must
        # raise ECRS above a flat one with the same mean drivers.
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=24,
            ercot_as_forward_requirement=True,
        )
        load = np.full(24, 50000.0)
        wind = np.full(24, 10000.0)
        # Solar that collapses across the evening → a large net-load up-ramp.
        solar_flat = np.full(24, 6000.0)
        solar_swing = 6000.0 + 8000.0 * np.sin(np.linspace(0, np.pi, 24))
        d_flat = ercot_as_forward_drivers(load, wind, solar_flat)
        d_swing = ercot_as_forward_drivers(load, wind, solar_swing)
        e_flat = ercot_as_forward_requirement_mw(cfg, "ECRS", 24, d_flat).mean()
        e_swing = ercot_as_forward_requirement_mw(cfg, "ECRS", 24, d_swing).mean()
        self.assertGreater(e_swing, e_flat)

    def test_builder_uses_forward_when_enabled(self):
        # End-to-end through the co-opt input builder: with the flag on and
        # profiles supplied, the requirement differs from the measured one and
        # tracks the forward drivers.
        fleet = self._fleet()
        load = np.full(48, 55000.0)
        wind = np.full(48, 14000.0)
        solar = np.full(48, 7000.0)
        cfg_meas = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=48
        )
        cfg_fwd = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        req_meas = ercot_multiproduct_reserve_coopt_inputs(cfg_meas, fleet, 48)[0]
        req_fwd = ercot_multiproduct_reserve_coopt_inputs(
            cfg_fwd, fleet, 48, system_load=load, wind_gen=wind, solar_gen=solar
        )[0]
        self.assertEqual(req_fwd.shape, req_meas.shape)
        # Forward path produced a genuinely different requirement (not the read).
        self.assertFalse(np.allclose(req_fwd, req_meas))
        # All four products are positive (active) under the forward formula.
        self.assertTrue((req_fwd.mean(axis=1) > 0).all())

    def test_builder_flag_on_but_no_profiles_falls_back(self):
        # Flag on but the builder called without profiles (e.g. a path that does
        # not thread them) → measured fallback, byte-identical to the flag-off
        # requirement.
        fleet = self._fleet()
        cfg_meas = ScenarioConfig(
            iso="ERCOT", mode="backcast", weather_year=2024, hours=48
        )
        cfg_fwd = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_as_forward_requirement=True,
        )
        req_meas = ercot_multiproduct_reserve_coopt_inputs(cfg_meas, fleet, 48)[0]
        req_fwd = ercot_multiproduct_reserve_coopt_inputs(cfg_fwd, fleet, 48)[0]
        np.testing.assert_array_equal(req_fwd, req_meas)


class TestReserveSupplyCap(unittest.TestCase):
    """The RTOLCAP reserve-supply re-scope: cap cleared reserve to a measured MW."""

    def _solve(self, req_mw, cap_mw, demand_mw=60.0, mc=20.0, max_penalty=1000.0):
        # 1 gas_cc, 1 zone, 24 h. Headroom = 100 - demand. The supply cap is a
        # SYSTEM-WIDE upper bound on the single tier's cleared reserve.
        fleet = _fleet(["gas_cc"], ["Z0"], hours=24)
        demand = np.full((1, 24), demand_mw)
        mc_arr = np.full((1, 24), mc)
        kwargs = _one_product(req_mw, max_penalty)
        if cap_mw is not None:
            kwargs["reserve_supply_cap"] = np.full((1, 24), float(cap_mw))
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc_arr,
            voll=5000.0,
            **kwargs,
        )

    def test_loose_cap_is_noop(self):
        # Headroom 40 >= req 30 -> normally free; a cap of 100 MW (>= headroom)
        # binds nothing, so the price is identical to the uncapped solve.
        base = float(self._solve(req_mw=30.0, cap_mw=None).reserve_price.max())
        loose = float(self._solve(req_mw=30.0, cap_mw=100.0).reserve_price.max())
        self.assertLess(base, 1e-6)
        self.assertAlmostEqual(base, loose, places=6)

    def test_tight_cap_prices_reserve_without_lifting_lmp(self):
        # Headroom 40 >= req 30 -> uncapped it does NOT price. Capping cleared
        # reserve to 20 MW (< the 30 MW requirement) re-scopes the SUPPLY below the
        # requirement, so reserve falls short and the reserve dual prices — exactly
        # the RTOLCAP-tightens-the-band mechanism. Crucially the energy LMP does
        # NOT move: energy cancels out of a pure reserve cap, so the cap forms an
        # ADDITIVE ORDC adder (RTORPA), which the ORDC-regime price assembly adds
        # to the LMP — the energy-only-SCED-plus-adder design of pre-RTC+B ERCOT.
        uncapped = self._solve(req_mw=30.0, cap_mw=None)
        capped = self._solve(req_mw=30.0, cap_mw=20.0)
        self.assertLess(float(uncapped.reserve_price.max()), 1e-6)
        self.assertGreater(float(capped.reserve_price.max()), 0.0)
        # LMP unchanged by the cap (the additive-adder property, not a bug).
        np.testing.assert_allclose(capped.prices[0], 20.0, atol=1e-5)
        np.testing.assert_allclose(uncapped.prices[0], 20.0, atol=1e-5)

    def test_tighter_cap_prices_higher(self):
        # A tighter supply cap clears reserve lower on the demand curve -> a
        # higher reserve price (monotone in the supply re-scope, not a fit).
        loose = float(self._solve(req_mw=30.0, cap_mw=25.0).reserve_price.max())
        tight = float(self._solve(req_mw=30.0, cap_mw=10.0).reserve_price.max())
        self.assertGreater(tight, loose)

    def test_energy_dispatch_unaffected_by_reserve_cap(self):
        # The cap limits RESERVE only — energy can still use the full fleet, so
        # the energy served is unchanged (the cap is a supply-definition re-scope,
        # not a generation limit).
        capped = self._solve(req_mw=30.0, cap_mw=10.0)
        self.assertAlmostEqual(float(capped.dispatch[0, 0]), 60.0, places=4)


class TestReserveSupplyCapLoader(unittest.TestCase):
    """ercot_rtolcap_supply_cap_mw: measured RTOLCAP/RTOFFCAP, gated, no-fit."""

    def test_off_returns_none(self):
        from market_sim.results.scarcity import ercot_rtolcap_supply_cap_mw

        cfg = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2024, hours=48)
        self.assertIsNone(ercot_rtolcap_supply_cap_mw(cfg, 48))

    def test_gated_off_before_from_year(self):
        from market_sim.results.scarcity import ercot_rtolcap_supply_cap_mw

        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2022,
            hours=48,
            ercot_reserve_supply_cap=True,
            ercot_reserve_supply_cap_from_year=2023,
        )
        # 2022 < from_year 2023 -> gated off even with the flag on.
        self.assertIsNone(ercot_rtolcap_supply_cap_mw(cfg, 48))

    def test_multiproduct_returns_two_tier_cap(self):
        from market_sim.results.scarcity import ercot_rtolcap_supply_cap_mw

        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=8760,
            ercot_reserve_supply_cap=True,
            ercot_multiproduct_as_coopt=True,
        )
        cap = ercot_rtolcap_supply_cap_mw(cfg, 8760)
        self.assertIsNotNone(cap)
        self.assertEqual(cap.shape, (2, 8760))
        # The "all" tier (row 1 = RTOLCAP + RTOFFCAP) is >= the "fast" tier
        # (row 0 = RTOLCAP) everywhere RTOFFCAP >= 0.
        self.assertTrue((cap[1] >= cap[0] - 1e-6).all())
        # 2024 measured RTOLCAP mean ~16.7 GW (validation, not a fit).
        self.assertGreater(cap[0].mean(), 12_000.0)
        self.assertLess(cap[0].mean(), 22_000.0)

    def test_single_product_returns_one_row_cap(self):
        from market_sim.results.scarcity import ercot_rtolcap_supply_cap_mw

        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=8760,
            ercot_reserve_supply_cap=True,  # multiproduct OFF -> single lumped
        )
        cap = ercot_rtolcap_supply_cap_mw(cfg, 8760)
        self.assertIsNotNone(cap)
        self.assertEqual(cap.shape, (1, 8760))
        self.assertGreater(cap[0].mean(), 12_000.0)  # RTOLCAP, ~16.7 GW 2024
        self.assertLess(cap[0].mean(), 22_000.0)


class TestASAwareUnitValue(unittest.TestCase):
    """The AS-aware commitment value: reserve price x headroom, cascade-aware."""

    def _fleet(self):
        gens = [
            Generator(
                unit_id=f"G{i}",
                name=f"G{i}",
                zone="Z0",
                fuel_type=f,
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,  # no derate -> availability 1.0
            )
            # fast: gas_cc/coal/nuclear; quick-start: gas_ct/oil; none: wind
            for i, f in enumerate(
                ["gas_cc", "gas_ct", "coal", "nuclear", "oil", "wind"]
            )
        ]
        return generators_to_fleet_arrays(gens, ["Z0"], hours=4)

    def test_none_reserve_price_is_zero(self):
        from market_sim.results.scarcity import ercot_as_aware_unit_value

        fleet = self._fleet()
        av = ercot_as_aware_unit_value(fleet, np.zeros((fleet.n_gen, 4)), None, 4)
        self.assertEqual(av.shape, (fleet.n_gen, 4))
        self.assertFalse(av.any())

    def test_value_is_price_times_headroom_with_cascade(self):
        from market_sim.results.scarcity import ercot_as_aware_unit_value

        fleet = self._fleet()
        # Products RegUp/RRS/ECRS (fast) / NonSpin (slow). One hour priced.
        rp = np.zeros((4, 4))  # (T, n_prod)
        rp[1, 0] = 10.0  # a FAST product (RegUp) prices at $10 in hour 1
        rp[1, 3] = 4.0  # NonSpin (slow) prices at $4 in hour 1
        p1 = np.zeros((fleet.n_gen, 4))
        p1[0, 1] = 40.0  # gas_cc runs 40 MW in hour 1 -> headroom 60
        av = ercot_as_aware_unit_value(fleet, p1, rp, 4)
        # gas_cc (fast): proxy = max over all products = $10, headroom 60 -> 600.
        self.assertAlmostEqual(av[0, 1], 600.0)
        # coal/nuclear (fast, full 100 headroom): 10 x 100 = 1000.
        self.assertAlmostEqual(av[2, 1], 1000.0)
        self.assertAlmostEqual(av[3, 1], 1000.0)
        # gas_ct/oil (quick-start): only the NonSpin (slow) price applies -> 4x100.
        self.assertAlmostEqual(av[1, 1], 400.0)
        self.assertAlmostEqual(av[4, 1], 400.0)
        # wind holds no responsive reserve -> zero everywhere.
        self.assertFalse(av[5].any())
        # No AS value in the unpriced hours.
        self.assertFalse(av[:, [0, 2, 3]].any())


if __name__ == "__main__":
    unittest.main()
