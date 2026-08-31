"""Tests for the D11-R margin-exhaustion entry volume rule.

The L-1b closure productionized (``docs/FINDING-entry-signal-l1-2026-08.md``
§2, gated ``ScenarioConfig.entry_margin_exhaustion``): both entry allocators
build in repriced tranches until the screen's own margin is exhausted,
bounded by the same caps. Covered here:

* the unarmed path (``entry_reprice=None``) is the bang-bang loop, untouched;
* an INERT repricer (prices never move) makes the walk reproduce the
  bang-bang totals exactly — the walk changes volumes only through the
  repricing feedback, never through its own bookkeeping;
* a depressing repricer exhausts entry below the caps, in both allocators;
* the tranche size is a resolution constant: halving it moves no tech's
  build by more than one tranche (the probe's measured invariance property,
  re-asserted on the live walk);
* the reserve-leg walk floor: wiping the reserve leg through the walk's
  adder delta shrinks thermal entry relative to a kept leg;
* the real ``_EntryRepriceWalk`` over the real lookahead instrument anchors
  bitwise at zero additions and prices added capacity downward.

The config refusal (requires ``entry_lookahead_reprice``) and the backcast
coercion are asserted alongside the cache-key registration.
"""

import types
import unittest
from unittest import mock

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import apply_economic_new_entry
from market_sim.model.storage import apply_storage_new_entry, build_default_storage
from market_sim.runner import _EntryRepriceWalk, _lookahead_reprice_signal

HOURS = 8760


class _StubWalk:
    """Duck-typed repricer: flat linear price depression per committed MW.

    ``depress_per_mw`` is the flat $/MWh drop per MW committed (all classes);
    ``reserve_wipe`` replaces the reserve delta with the negative of a given
    leg so the walk's max(0, r + delta) floor path is exercised.
    """

    def __init__(self, depress_per_mw=0.0, reserve_delta=None, compress_per_mw=0.0):
        self.added_mw = 0.0
        self.k = float(depress_per_mw)
        # Spread compression per committed MW: storage margins are
        # spread-based, so a flat level drop alone cannot exhaust them.
        self.c = float(compress_per_mw)
        self._reserve_delta = reserve_delta

    def add_thermal(self, var_cost, mw, availability):
        self.added_mw += float(mw)

    def add_net_load_reduction(self, profile_mw):
        # Credit the tranche at its mean output — monotone is all the stub
        # needs (the real walk uses the lookahead stack, tested separately).
        self.added_mw += float(np.mean(profile_mw))

    def add_storage(self, mw, duration_hr, rte):
        self.added_mw += float(mw)

    def signal(self, consumed):
        arr = np.asarray(consumed, dtype=float) - self.k * self.added_mw
        if self.c > 0.0 and self.added_mw > 0.0:
            mean = arr.mean()
            arr = mean + (arr - mean) / (1.0 + self.c * self.added_mw)
        return arr

    def reserve_delta(self):
        if self._reserve_delta is not None:
            return np.asarray(self._reserve_delta, dtype=float)
        return np.zeros(HOURS)


def _entry_by_tech(new_fleet, renewable_additions):
    """Collapse a new-entry result into ``{fuel: total_mw}``."""
    by_tech: dict[str, float] = {}
    for g in new_fleet:
        by_tech[g.fuel_type] = by_tech.get(g.fuel_type, 0.0) + g.pmax_mw
    for by_fuel in renewable_additions.values():
        for fuel, mw in by_fuel.items():
            by_tech[fuel] = by_tech.get(fuel, 0.0) + mw
    return by_tech


def _config(**kw):
    # Emerging techs pushed out so only the classic candidates are screened.
    return ScenarioConfig(
        iso="ERCOT",
        h2_available_year=2099,
        ccs_available_year=2099,
        egs_available_year=2099,
        offshore_wind_available_year=2099,
        **kw,
    )


class TestConfigField(unittest.TestCase):
    """Field registration, refusal, and backcast coercion."""

    def test_default_off_and_cache_key_stable(self):
        cfg = ScenarioConfig()
        self.assertFalse(cfg.entry_margin_exhaustion)
        self.assertEqual(cfg.cache_key(), ScenarioConfig().cache_key())

    def test_armed_moves_cache_key(self):
        self.assertNotEqual(
            ScenarioConfig(entry_margin_exhaustion=True).cache_key(),
            ScenarioConfig().cache_key(),
        )

    def test_composes_with_disarmed_reprice(self):
        """The C-1 joint posture (owner ruling R-B, 2026-08-31).

        This pair was refused until R-B; the walk is delta-only, so armed
        without the reprice the screens keep the raw prior-year zonal duals
        as their level and this rule supplies the capacity response
        (``docs/PRECOMMIT-c1-joint-wind-2026-08-31.md`` §1.3).
        """
        cfg = ScenarioConfig(
            entry_margin_exhaustion=True, entry_lookahead_reprice=False
        )
        self.assertTrue(cfg.entry_margin_exhaustion)
        self.assertFalse(cfg.entry_lookahead_reprice)
        # A posture of its own: distinct from both singles and the default.
        self.assertNotIn(
            cfg.cache_key(),
            {
                ScenarioConfig().cache_key(),
                ScenarioConfig(entry_lookahead_reprice=False).cache_key(),
                ScenarioConfig(entry_margin_exhaustion=True).cache_key(),
            },
        )

    def test_backcast_coerces_off(self):
        cfg = ScenarioConfig(mode="backcast", entry_margin_exhaustion=True)
        self.assertFalse(cfg.entry_margin_exhaustion)


class TestThermalWalk(unittest.TestCase):
    """The margin-exhaustion walk in ``apply_economic_new_entry``."""

    PRICES = np.full(HOURS, 250.0)

    def _run(self, entry_reprice=None, prices=None):
        return apply_economic_new_entry(
            [],
            self.PRICES if prices is None else prices,
            2030,
            _config(),
            "ERCOT",
            entry_reprice=entry_reprice,
        )

    def test_inert_walk_matches_bang_bang(self):
        # A repricer that never moves prices must reproduce the bang-bang
        # totals exactly: the walk changes volumes only through repricing.
        base = _entry_by_tech(*self._run())
        walk = _entry_by_tech(*self._run(entry_reprice=_StubWalk(0.0)))
        self.assertEqual(set(base), set(walk))
        for tech, mw in base.items():
            self.assertAlmostEqual(mw, walk[tech], places=6, msg=tech)

    def test_depressing_walk_exhausts_below_cap(self):
        base = _entry_by_tech(*self._run())
        walk = _entry_by_tech(*self._run(entry_reprice=_StubWalk(0.5)))
        self.assertLess(
            sum(walk.values()),
            sum(base.values()),
            "a falling repriced signal must exhaust entry below the caps",
        )
        # Nothing may exceed its bang-bang (cap-bound) build.
        for tech, mw in walk.items():
            self.assertLessEqual(mw, base.get(tech, 0.0) + 1e-6, msg=tech)

    def test_tranche_resolution_invariance(self):
        # The probe's measured property, re-asserted live: halving the
        # tranche moves no tech's build by more than one (full) tranche.
        walk_250 = _entry_by_tech(*self._run(entry_reprice=_StubWalk(0.5)))
        with mock.patch(
            "market_sim.model.capacity_evolution.new_entry.ENTRY_EXHAUSTION_TRANCHE_MW",
            125.0,
        ):
            walk_125 = _entry_by_tech(*self._run(entry_reprice=_StubWalk(0.5)))
        for tech in set(walk_250) | set(walk_125):
            self.assertLessEqual(
                abs(walk_250.get(tech, 0.0) - walk_125.get(tech, 0.0)),
                250.0 + 1e-6,
                msg=tech,
            )

    def test_reserve_leg_walk_floor(self):
        # With prices below variable cost, thermal entry is carried by the
        # reserve leg alone. A walk whose adder delta wipes that leg (the
        # max(0, r + delta) floor) must build less than one that keeps it.
        prices = np.full(HOURS, 1.0)
        r_leg = np.full(HOURS, 40.0)

        def run(stub):
            return apply_economic_new_entry(
                [],
                prices,
                2030,
                _config(),
                "ERCOT",
                reserve_price_signal=r_leg,
                reserve_price_signal_slow=r_leg,
                entry_reprice=stub,
            )

        kept = _entry_by_tech(*run(_StubWalk(0.0)))
        wiped = _entry_by_tech(*run(_StubWalk(0.0, reserve_delta=-r_leg)))
        gas_kept = kept.get("gas_cc", 0.0) + kept.get("gas_ct", 0.0)
        gas_wiped = wiped.get("gas_cc", 0.0) + wiped.get("gas_ct", 0.0)
        self.assertGreater(gas_kept, 0.0)
        self.assertLess(gas_wiped, gas_kept)


class TestStorageWalk(unittest.TestCase):
    """The margin-exhaustion walk in ``apply_storage_new_entry``."""

    @staticmethod
    def _high_spread_prices():
        day = np.concatenate([np.full(12, 10.0), np.full(12, 300.0)])
        return np.tile(day, 365)

    @staticmethod
    def _total_mw(units):
        return sum(u.power_cap_mw for u in units)

    def _run(self, entry_reprice=None):
        cfg = ScenarioConfig()
        iso = get_iso_config("ERCOT")
        existing = build_default_storage(iso, cfg)
        return existing, apply_storage_new_entry(
            existing,
            self._high_spread_prices(),
            2027,
            cfg,
            "ERCOT",
            entry_reprice=entry_reprice,
        )

    def test_inert_walk_matches_split(self):
        _, base = self._run()
        _, walk = self._run(entry_reprice=_StubWalk(0.0))
        self.assertAlmostEqual(self._total_mw(base), self._total_mw(walk), places=6)

    def test_depressing_walk_exhausts_below_budget(self):
        existing, base = self._run()
        _, walk = self._run(entry_reprice=_StubWalk(compress_per_mw=0.01))
        built_base = self._total_mw(base) - self._total_mw(existing)
        built_walk = self._total_mw(walk) - self._total_mw(existing)
        self.assertGreater(built_base, 0.0)
        self.assertLess(built_walk, built_base)


class TestEntryRepriceWalk(unittest.TestCase):
    """The real walk object over the real lookahead instrument."""

    T = 240  # 10 whole days — the shave and stack paths need full days

    def _make_walk(self, alpha=1.0):
        cfg = ScenarioConfig(scarcity_pricing_enabled=False)
        fleet_arrays = types.SimpleNamespace(
            pmax=np.array([500.0, 500.0, 300.0]),
            availability=np.ones((3, self.T)),
        )
        mc_cost = np.tile(np.array([[10.0], [30.0], [80.0]]), (1, self.T))
        result = types.SimpleNamespace(
            wind_dispatched=np.zeros((1, self.T)),
            solar_dispatched=np.zeros((1, self.T)),
        )
        demand = np.full(self.T, 900.0)
        demand[::24] = 1250.0  # one near-scarcity hour per day

        def reprice(extra_stack, extra_vre, d_p, d_e, rte_added):
            d: dict = {}
            sig = _lookahead_reprice_signal(
                cfg,
                2030,
                np.zeros((1, self.T)),
                fleet_arrays,
                mc_cost,
                result,
                1,
                demand_next_total=demand,
                diagnostics=d,
                extra_stack=extra_stack,
                extra_vre=extra_vre,
            )
            return sig[0], np.asarray(d["adder_usd_mwh"], dtype=float)

        return _EntryRepriceWalk(reprice, alpha)

    def test_zero_state_is_anchored(self):
        walk = self._make_walk()
        consumed = np.full((2, self.T), 55.0)
        np.testing.assert_array_equal(walk.signal(consumed), consumed)
        np.testing.assert_array_equal(walk.reserve_delta(), np.zeros(self.T))

    def test_thermal_tranche_prices_downward(self):
        walk = self._make_walk()
        consumed = np.full(self.T, 55.0)
        walk.add_thermal(var_cost=20.0, mw=400.0, availability=0.95)
        shifted = walk.signal(consumed)
        self.assertTrue(np.all(shifted <= consumed + 1e-9))
        self.assertTrue(np.any(shifted < consumed - 1e-9))

    def test_alpha_scales_the_delta(self):
        walk_full = self._make_walk(alpha=1.0)
        walk_half = self._make_walk(alpha=0.5)
        consumed = np.full(self.T, 55.0)
        for w in (walk_full, walk_half):
            w.add_thermal(var_cost=20.0, mw=400.0, availability=0.95)
        d_full = consumed - walk_full.signal(consumed)
        d_half = consumed - walk_half.signal(consumed)
        np.testing.assert_allclose(d_half, 0.5 * d_full, rtol=1e-12)

    def test_vre_tranche_prices_downward(self):
        walk = self._make_walk()
        consumed = np.full(self.T, 55.0)
        walk.add_net_load_reduction(np.full(self.T, 300.0))
        shifted = walk.signal(consumed)
        self.assertTrue(np.all(shifted <= consumed + 1e-9))
        self.assertTrue(np.any(shifted < consumed - 1e-9))


if __name__ == "__main__":
    unittest.main()
