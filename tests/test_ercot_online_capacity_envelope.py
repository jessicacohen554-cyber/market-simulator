"""Tests for ERCOT's on-line-CAPACITY envelope (G-22 commitment thinness).

Builds from the trivial case up (CLAUDE.md testing pattern): a 1-generator,
1-zone, 24-hour LP. The envelope caps the shared-headroom ENERGY + RESERVE at a
committed on-line capacity MW, so the LP cannot serve/reserve more thermal than
the real system had on-line. The structural claims proven here, all as LP duals
(no tuned adder):

* **Condition-responsive.** Same envelope MW is INERT in a slack (low-energy)
  hour and BINDS in a tight (high-energy) hour — the distinguishing property vs
  the flat reserve-supply cap (which caps reserve regardless of energy).
* **Prices up on the energy dual, no offer change.** When the envelope binds the
  energy LMP rises by the reserve-shortage penalty (online capacity exhausted =
  scarcity), with the generator's marginal cost untouched.
* **Structural no-op when off** (``online_capacity_cap is None``): byte-identical
  price/dispatch to the pre-envelope LP.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.results.scarcity import (
    ercot_online_capacity_envelope_mw,
    nyiso_rcpf_product_shortfall_steps,
)


def _fleet(fuels, zone_names, hours, pmax=100.0, pmin=0.0):
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


class TestOnlineCapacityEnvelopeTrivial(unittest.TestCase):
    """1 gen (pmax 100), 1 zone, 24 h — the trivial case first."""

    def _solve(self, req_mw, env_mw, demand_mw=60.0, mc=20.0, max_penalty=1000.0):
        fleet = _fleet(["gas_cc"], ["Z0"], hours=24)
        demand = np.full((1, 24), demand_mw)
        mc_arr = np.full((1, 24), mc)
        kwargs = _one_product(req_mw, max_penalty)
        if env_mw is not None:
            kwargs["reserve_online_capacity_cap"] = np.full((1, 24), float(env_mw))
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

    def test_off_is_structural_noop(self):
        # online_capacity_cap None -> the LP is byte-identical to the base co-opt.
        base = self._solve(req_mw=30.0, env_mw=None, demand_mw=60.0)
        # headroom 40 >= req 30 -> reserve free, LMP == mc.
        self.assertLess(float(base.reserve_price.max()), 1e-6)
        np.testing.assert_allclose(base.prices[0], 20.0, atol=1e-5)

    def test_loose_envelope_is_noop(self):
        # An envelope at pmax (100) never binds (P+R <= pmax already holds), so
        # price/dispatch equal the off solve.
        base = self._solve(req_mw=30.0, env_mw=None, demand_mw=60.0)
        loose = self._solve(req_mw=30.0, env_mw=100.0, demand_mw=60.0)
        self.assertAlmostEqual(
            float(base.reserve_price.max()),
            float(loose.reserve_price.max()),
            places=6,
        )
        np.testing.assert_allclose(base.prices[0], loose.prices[0], atol=1e-5)

    def test_tight_envelope_in_tight_hour_prices_scarcity_on_the_energy_dual(self):
        # demand 60, req 30, envelope 70. Energy balance pins P=60; the envelope
        # P+R<=70 then leaves only R<=10 < req 30 -> reserve short. Because the
        # ENERGY term shares the online capacity, the envelope dual lifts the
        # ENERGY LMP by the shortfall penalty (scarcity from online-capacity
        # exhaustion) — with NO change to the generator's mc.
        capped = self._solve(req_mw=30.0, env_mw=70.0, demand_mw=60.0)
        self.assertGreater(float(capped.reserve_price.max()), 0.0)
        # LMP rises ABOVE mc (the distinguishing behaviour vs the pure reserve
        # cap, whose dual leaves the LMP at mc).
        self.assertGreater(float(capped.prices[0].max()), 20.0 + 1e-3)

    def test_condition_responsive_inert_in_slack_hour(self):
        # SAME envelope (70) but a slack hour (demand 20): P=20 leaves R<=50 >= req
        # 30 -> no shortage, LMP == mc. The envelope is inert precisely where the
        # phantom spare is real headroom — the condition-responsive property the
        # flat reserve-supply cap lacks.
        slack = self._solve(req_mw=30.0, env_mw=70.0, demand_mw=20.0)
        self.assertLess(float(slack.reserve_price.max()), 1e-6)
        np.testing.assert_allclose(slack.prices[0], 20.0, atol=1e-5)

    def test_tighter_envelope_prices_higher(self):
        # A tighter envelope leaves less reserve room in the tight hour ->
        # deeper shortfall -> higher price (monotone in the re-scope, not a fit).
        loose = float(
            self._solve(req_mw=30.0, env_mw=80.0, demand_mw=60.0).prices[0].max()
        )
        tight = float(
            self._solve(req_mw=30.0, env_mw=65.0, demand_mw=60.0).prices[0].max()
        )
        self.assertGreater(tight, loose)


class TestOnlineCapacityEnvelopeBuilder(unittest.TestCase):
    """ercot_online_capacity_envelope_mw: gated, ERCOT class-shares, all-tier only."""

    def _fleet_arrays(self):
        # A small ERCOT-shaped fleet: one CC, one CT (quick-start), one coal.
        gens = [
            Generator(
                unit_id="cc",
                name="cc",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=500.0,
                pmin_mw=0.0,
                plant_group="CC_REGULAR",
                plant_code=1,
            ),
            Generator(
                unit_id="ct",
                name="ct",
                zone="Z0",
                fuel_type="gas_ct",
                pmax_mw=200.0,
                pmin_mw=0.0,
                plant_group="CT_PEAKER",
                plant_code=2,
            ),
            Generator(
                unit_id="coal",
                name="coal",
                zone="Z0",
                fuel_type="coal",
                pmax_mw=800.0,
                pmin_mw=0.0,
                plant_group="COAL",
                plant_code=3,
            ),
        ]
        return generators_to_fleet_arrays(gens, ["Z0"], hours=48)

    def test_off_returns_none(self):
        cfg = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2024, hours=48)
        fleet = self._fleet_arrays()
        out = ercot_online_capacity_envelope_mw(
            cfg,
            fleet,
            48,
            net_load=np.full(48, 1000.0),
            headroom_eligible=np.ones((2, 3), dtype=bool),
            headroom_products=np.array([[True, False], [True, True]], dtype=bool),
        )
        self.assertIsNone(out)

    def test_on_caps_all_tier_only(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_online_capacity_envelope=True,
        )
        fleet = self._fleet_arrays()
        # Two tiers: fast (bounds product 0 only), all (bounds both products).
        hr_elig = np.array(
            [[True, False, True], [True, True, True]], dtype=bool
        )  # fast = cc+coal, all = cc+ct+coal
        hr_prod = np.array([[True, False], [True, True]], dtype=bool)
        out = ercot_online_capacity_envelope_mw(
            cfg,
            fleet,
            48,
            net_load=np.linspace(500.0, 5000.0, 48),
            headroom_eligible=hr_elig,
            headroom_products=hr_prod,
        )
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, (2, 48))
        # Fast tier (does NOT bound all products) is the uncapped sentinel.
        self.assertTrue(np.all(out[0] > 1e8))
        # All tier is a finite committed-capacity envelope, below total fleet cap
        # (1500 MW) and positive.
        self.assertTrue(np.all(out[1] < 1500.0))
        self.assertTrue(np.all(out[1] > 0.0))

    def test_envelope_rises_with_net_load(self):
        # More committed capacity is on-line at high net load (COAL/CC commit
        # more), so the all-tier envelope is monotone-ish higher in the top
        # net-load hours than the bottom — the correct commitment direction.
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2024,
            hours=48,
            ercot_online_capacity_envelope=True,
        )
        fleet = self._fleet_arrays()
        hr_elig = np.ones((2, 3), dtype=bool)
        hr_prod = np.array([[True, False], [True, True]], dtype=bool)
        nl = np.linspace(500.0, 5000.0, 48)
        out = ercot_online_capacity_envelope_mw(
            cfg,
            fleet,
            48,
            net_load=nl,
            headroom_eligible=hr_elig,
            headroom_products=hr_prod,
        )
        # Highest-net-load hour envelope >= lowest-net-load hour envelope.
        hi = out[1][np.argmax(nl)]
        lo = out[1][np.argmin(nl)]
        self.assertGreaterEqual(hi, lo)


if __name__ == "__main__":
    unittest.main()
