"""Tests for the D12 scarcity-consistent entry reserve leg.

``ScenarioConfig.entry_forward_reserve_leg`` (GATED default-OFF;
``docs/handoffs/FINDING-capx-d12-scarcity-basis-2026-08-30.md``): the thermal
entry screens' hourly reserve legs read the entering year's OWN expected-ORDC
adder — the same lookahead-instrument invocation that priced the energy leg —
instead of the prior solved year's realized post-solve adder. Covered here:

* field registration: default off, cache-key stable at default, armed hashes
  distinctly (the nyiso-119 discipline);
* the two refusals (requires ``entry_lookahead_reprice``; requires
  ``screen_reserve_value_enabled``) and the backcast coercion;
* evolve_fleet routing: armed with a captured adder, the NEW-ENTRY call
  receives the adder as BOTH reserve tiers while the RETIREMENT call keeps
  the realized pair; unarmed (or armed with no captured adder) both calls
  receive the shipped realized pair byte-identically;
* the margin identity the basis rests on:
  ``max(S - vc, adder) == adder + max(base - vc, 0)`` for ``S = base + adder``,
  ``adder >= 0`` — the expected-ORDC revenue decomposition;
* the walk composition: with the leg seeded at the zero-additions adder, the
  existing ``max(0, r + reserve_delta)`` closure yields exactly the walk's
  CURRENT adder (no new walk code — the D11-R shift becomes the identity).
"""

import unittest
from unittest import mock

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity_evolution import evolve as evolve_mod

HOURS = 8760


class TestConfigField(unittest.TestCase):
    """Field registration, refusals, and backcast coercion."""

    def test_default_off_and_cache_key_stable(self):
        cfg = ScenarioConfig()
        self.assertFalse(cfg.entry_forward_reserve_leg)
        self.assertEqual(cfg.cache_key(), ScenarioConfig().cache_key())

    def test_armed_moves_cache_key(self):
        self.assertNotEqual(
            ScenarioConfig(entry_forward_reserve_leg=True).cache_key(),
            ScenarioConfig().cache_key(),
        )

    def test_requires_lookahead_reprice(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                entry_forward_reserve_leg=True, entry_lookahead_reprice=False
            )

    def test_requires_screen_reserve_value(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                entry_forward_reserve_leg=True, screen_reserve_value_enabled=False
            )

    def test_backcast_coerces_off(self):
        cfg = ScenarioConfig(mode="backcast", entry_forward_reserve_leg=True)
        self.assertFalse(cfg.entry_forward_reserve_leg)


class TestMarginIdentity(unittest.TestCase):
    """The decomposition the scarcity-consistent basis rests on."""

    def test_expected_ordc_revenue_identity(self):
        rng = np.random.default_rng(7)
        base = rng.uniform(0.0, 120.0, size=HOURS)
        adder = np.where(
            rng.uniform(size=HOURS) < 0.02, rng.uniform(0, 5000, HOURS), 0.0
        )
        vc = 35.0
        s = base + adder
        lhs = np.maximum(s - vc, adder)
        rhs = adder + np.maximum(base - vc, 0.0)
        np.testing.assert_allclose(lhs, rhs, rtol=0, atol=1e-9)


class TestWalkComposition(unittest.TestCase):
    """Seeding r at the zero-additions adder makes the D11-R shift exact."""

    def test_shift_closure_becomes_current_adder(self):
        adder0 = np.array([0.0, 10.0, 500.0, 0.0])
        adder_now = np.array([0.0, 4.0, 120.0, 0.0])  # walk repriced downward
        reserve_delta = adder_now - adder0  # _EntryRepriceWalk.reserve_delta
        r_walk = np.maximum(0.0, adder0 + reserve_delta)  # new_entry's closure
        np.testing.assert_array_equal(r_walk, adder_now)


class TestEvolveRouting(unittest.TestCase):
    """Armed vs unarmed reserve-leg routing through evolve_fleet.

    The step functions are patched on the shared package namespace (the
    ``_pkg_ns`` seam every historical ``mock.patch`` uses); ``prior_results``
    is a plain dict — the supported bare-dict caller path.
    """

    T = 24

    def _run(self, config, prior_extra):
        calls = {}

        def fake_retire(fleet, *a, **k):
            calls["retirement"] = (
                k.get("reserve_price_signal"),
                k.get("reserve_price_signal_slow"),
            )
            return fleet, {}, {}

        def fake_entry(fleet, *a, **k):
            calls["entry"] = (
                k.get("reserve_price_signal"),
                k.get("reserve_price_signal_slow"),
            )
            return fleet, {}

        prior = {
            "fleet_arrays": object(),
            "dispatch_result": object(),
            "prices": np.full((1, self.T), 40.0),
            "mc_cost": np.full((1, self.T), 20.0),
            "peak_demand": 1000.0,
            "reserve_price_signal": np.full(self.T, 7.0),
            "reserve_price_signal_slow": np.full(self.T, 5.0),
            **prior_extra,
        }
        ns = "market_sim.model.capacity_evolution"
        with (
            mock.patch(
                f"{ns}.apply_announced_retirements",
                side_effect=lambda fleet, *a, **k: fleet,
            ),
            mock.patch(
                f"{ns}.apply_ccs_retrofit",
                side_effect=lambda fleet, *a, **k: (fleet, []),
            ),
            mock.patch(f"{ns}.apply_economic_retirements", side_effect=fake_retire),
            mock.patch(f"{ns}.apply_economic_new_entry", side_effect=fake_entry),
        ):
            evolve_mod.evolve_fleet([], prior, 2030, config, {})
        self.assertIn("retirement", calls)
        self.assertIn("entry", calls)
        return calls

    def test_armed_swaps_entry_legs_only(self):
        cfg = ScenarioConfig(entry_forward_reserve_leg=True)
        fwd = np.full(self.T, 99.0)
        calls = self._run(cfg, {"entry_reserve_price_signal": fwd})
        # Entry: both tiers are the entering year's adder.
        np.testing.assert_array_equal(calls["entry"][0], fwd)
        np.testing.assert_array_equal(calls["entry"][1], fwd)
        # Retirement: the realized pair, untouched.
        np.testing.assert_array_equal(calls["retirement"][0], np.full(self.T, 7.0))
        np.testing.assert_array_equal(calls["retirement"][1], np.full(self.T, 5.0))

    def test_armed_without_captured_adder_degrades_to_shipped(self):
        cfg = ScenarioConfig(entry_forward_reserve_leg=True)
        calls = self._run(cfg, {"entry_reserve_price_signal": None})
        np.testing.assert_array_equal(calls["entry"][0], np.full(self.T, 7.0))
        np.testing.assert_array_equal(calls["entry"][1], np.full(self.T, 5.0))

    def test_unarmed_ignores_a_present_adder(self):
        cfg = ScenarioConfig()
        fwd = np.full(self.T, 99.0)
        calls = self._run(cfg, {"entry_reserve_price_signal": fwd})
        np.testing.assert_array_equal(calls["entry"][0], np.full(self.T, 7.0))
        np.testing.assert_array_equal(calls["entry"][1], np.full(self.T, 5.0))


if __name__ == "__main__":
    unittest.main()
