"""Validation of the ERCOT gas-CC commitment bridge (ERCOT-63).

Covers :func:`market_sim.pipeline.commitment.ercot_gas_bridge_p1_floor_fleet` /
:func:`build_ercot_gas_bridge_p1_prep` — the P1-native committed-state floor
promoted from the ERCOT-62b probe (the CAISO RA must-offer internals routed
onto the ERCOT merchant gas-CC fleet with the measured committed-CC LSL/HSL
p50 min-load) — plus the two default-neutral internals extensions it uses
(``fuel_types`` scope, ``max_econ_gap_hours`` DA-horizon cap on
:func:`model.commitment.caiso_ra_mustoffer_min_gen`). Contract:

* flag off / non-ERCOT ⇒ ``None`` (byte-identical P1 — rules 14/26);
* the physical (< min-down) restart bar and the economic (≥ min-down)
  startup-restart bridge both floor gas-CC only — CT/ST/CHP/coal never
  (the recorded ERCOT-63 class adjudication + rule-18 physics);
* the economic leg is bounded to one DA operating day when
  ``ercot_gas_bridge_da_horizon`` is on (default); off reproduces the
  ERCOT-62b uncapped construction;
* D-2 attribution: floored gen-hours tagged ``MECH_GAS_COMMITMENT_BRIDGE``,
  maximum-composition with pre-existing floors (an incumbent higher floor
  keeps its id);
* availability is raised where the floor exceeds ``pmax × availability``
  (LP feasibility guard);
* the internals extensions default to the CAISO behaviour byte-identically
  (``fuel_types=("gas_cc","gas_ct")``, ``max_econ_gap_hours=None``).
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_GAS_COMMITMENT_BRIDGE,
    MECH_NAMES,
    assert_ablation_coverage,
)
from market_sim.model.commitment import caiso_ra_mustoffer_min_gen
from market_sim.pipeline.commitment import (
    build_ercot_gas_bridge_p1_prep,
    build_ercot_gas_bridge_p1_preps,
    ercot_gas_bridge_p1_floor_fleet,
)


def _cc_gen(pmax=300.0, heat_rate=7.0, plant_group="CC_REGULAR", fuel="gas_cc"):
    return Generator(
        unit_id="CC",
        name="CC",
        zone="z",
        fuel_type=fuel,
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
        plant_group=plant_group,
    )


def _overnight_dispatch(hours=48):
    """Two run-days with an 8 h overnight gap (>= the f-class 6 h min-down)."""
    disp = np.zeros(hours)
    disp[6:22] = 300.0  # day 1 run, ends h22
    disp[30:46] = 300.0  # day 2 run, starts h30 -> gap h22..29 = 8 h
    return disp


class TestInternalsExtensions(unittest.TestCase):
    """``fuel_types`` and ``max_econ_gap_hours`` on the shared detector."""

    def _fleet(self, hours=48):
        gen = _cc_gen()
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        return [gen], fa

    def test_fuel_scope_excludes_out_of_scope_fuel(self):
        # The same CC pattern floors under the default scope but not when the
        # caller scopes to a different fuel — the ERCOT CC-only adjudication.
        gens, fa = self._fleet()
        p0 = _overnight_dispatch().reshape(1, 48)
        mc = np.full((1, 48), 30.0)
        lmp = np.full((1, 48), 25.0)
        kw = dict(p1_prices=lmp, base_mc=mc, startup_bridge=True)
        base = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, **kw)
        self.assertTrue(np.any(base > 0.0))
        scoped = caiso_ra_mustoffer_min_gen(
            p0, fa, gens, 0.574, fuel_types=("gas_ct",), **kw
        )
        np.testing.assert_allclose(scoped, np.zeros_like(scoped))

    def test_max_econ_gap_hours_caps_economic_bridge_only(self):
        # A 35 h idle gap with near-marginal gas: hold cost
        # (26-25) x 0.574 x 35 = 20.1 < 48.6 startup -> bridged when uncapped,
        # dropped under the one-DA-operating-day cap.
        hours = 72
        gens, fa = self._fleet(hours)
        disp = np.zeros(hours)
        disp[0:6] = 300.0
        disp[41:48] = 300.0  # gap h6..40 = 35 h
        p0 = disp.reshape(1, hours)
        mc = np.full((1, hours), 26.0)
        lmp = np.full((1, hours), 25.0)
        kw = dict(p1_prices=lmp, base_mc=mc, startup_bridge=True)
        uncapped = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, **kw)
        self.assertTrue(np.all(uncapped[0, 6:41] > 0.0))
        capped = caiso_ra_mustoffer_min_gen(
            p0, fa, gens, 0.574, max_econ_gap_hours=24.0, **kw
        )
        np.testing.assert_allclose(capped, np.zeros_like(capped))

    def test_max_econ_gap_hours_never_caps_physical_bridge(self):
        # A 3 h gap < the 6 h min-down is a restart bar — floored regardless
        # of any economic-gap cap (physics, not commitment horizon).
        gens, fa = self._fleet(24)
        disp = np.zeros(24)
        disp[6:10] = 300.0
        disp[13:19] = 300.0
        p0 = disp.reshape(1, 24)
        floor = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, max_econ_gap_hours=1.0)
        self.assertTrue(np.all(floor[0, 10:13] > 0.0))


class TestOnlineHoursLeg(unittest.TestCase):
    """``floor_online_hours`` — the ercot141 committed-STATE window extension.

    The gap legs floor the idle hours BETWEEN runs; this leg floors the runs
    themselves, because a synchronized unit cannot operate below its minimum
    stable load. Contract: default-off byte identity, run hours floored at the
    same measured target as the gaps, an offline plant never floored (the leg
    cannot force a start), and composition by maximum with the gap legs.
    """

    def _fleet(self, hours=48):
        gen = _cc_gen()
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        return [gen], fa

    def test_default_off_is_byte_identical(self):
        # Rule 14/26: the flag must be a no-op at its default.
        gens, fa = self._fleet()
        p0 = _overnight_dispatch().reshape(1, 48)
        kw = dict(
            p1_prices=np.full((1, 48), 25.0),
            base_mc=np.full((1, 48), 30.0),
            startup_bridge=True,
        )
        base = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, **kw)
        explicit_off = caiso_ra_mustoffer_min_gen(
            p0, fa, gens, 0.574, floor_online_hours=False, **kw
        )
        np.testing.assert_array_equal(base, explicit_off)

    def test_online_hours_floored_at_the_gap_target(self):
        # The two detected runs (h6-21, h30-45) carry NO floor from the gap
        # legs; with the leg on they are floored at the same min-load target.
        gens, fa = self._fleet()
        p0 = _overnight_dispatch().reshape(1, 48)
        kw = dict(
            p1_prices=np.full((1, 48), 25.0),
            base_mc=np.full((1, 48), 30.0),
            startup_bridge=True,
        )
        base = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, **kw)
        self.assertTrue(np.all(base[0, 6:22] == 0.0))  # runs unfloored today
        on = caiso_ra_mustoffer_min_gen(
            p0, fa, gens, 0.574, floor_online_hours=True, **kw
        )
        target = 0.574 * 300.0
        np.testing.assert_allclose(on[0, 6:22], target)
        np.testing.assert_allclose(on[0, 30:46], target)
        # The bridged overnight gap keeps its own floor — composition, not
        # replacement (rule 19: one mechanism, two placements).
        np.testing.assert_allclose(on[0, 22:30], base[0, 22:30])
        self.assertTrue(np.all(on >= base))

    def test_offline_hours_never_floored(self):
        # The leg cannot force a start: hours the P0 pattern has the plant OFF
        # and which no gap leg bridges stay at zero. h0-5 and h46-47 are
        # outside every detected run and are not gaps between two runs.
        gens, fa = self._fleet()
        p0 = _overnight_dispatch().reshape(1, 48)
        on = caiso_ra_mustoffer_min_gen(
            p0,
            fa,
            gens,
            0.574,
            floor_online_hours=True,
            p1_prices=np.full((1, 48), 25.0),
            base_mc=np.full((1, 48), 30.0),
            startup_bridge=True,
        )
        np.testing.assert_allclose(on[0, 0:6], 0.0)
        np.testing.assert_allclose(on[0, 46:48], 0.0)

    def test_never_floors_an_always_off_unit(self):
        gens, fa = self._fleet(24)
        p0 = np.zeros((1, 24))
        on = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, floor_online_hours=True)
        np.testing.assert_allclose(on, np.zeros_like(on))

    def test_single_run_unit_is_floored(self):
        # A unit with ONE run has no gap, so the gap legs skip it entirely
        # (len(runs) < 2); the STATE leg must still floor its online hours.
        gens, fa = self._fleet(24)
        disp = np.zeros(24)
        disp[8:16] = 300.0
        p0 = disp.reshape(1, 24)
        base = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574)
        np.testing.assert_allclose(base, np.zeros_like(base))
        on = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.574, floor_online_hours=True)
        np.testing.assert_allclose(on[0, 8:16], 0.574 * 300.0)
        np.testing.assert_allclose(on[0, 0:8], 0.0)
        np.testing.assert_allclose(on[0, 16:24], 0.0)

    def test_out_of_scope_fuel_never_floored(self):
        # Rule 25/18: the leg inherits the detector's own scope, so a fuel
        # outside fuel_types is untouched however wide the window.
        gens, fa = self._fleet(24)
        disp = np.zeros(24)
        disp[8:16] = 300.0
        on = caiso_ra_mustoffer_min_gen(
            disp.reshape(1, 24),
            fa,
            gens,
            0.574,
            fuel_types=("gas_ct",),
            floor_online_hours=True,
        )
        np.testing.assert_allclose(on, np.zeros_like(on))

    def test_target_clips_to_tranche_capacity(self):
        # The ERCOT-64 pinning arithmetic the lane rests on: the floor target
        # is min(min_load_frac x plant_pmax, tranche_pmax), so a base tranche
        # smaller than the measured LSL share is pinned at its OWN capacity —
        # zero headroom, hence unable to set the margin.
        base_tr = Generator(
            unit_id="P1_committed",
            name="P1_committed",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=100.0,  # 25 % of the 400 MW plant — below 0.574
            pmin_mw=0.0,
            heat_rate=7.0,
            eford=0.0,
            plant_group="CC_REGULAR",
            is_campd_bin=True,
            startup_cost_per_mw=48.6,  # only the base tranche carries a start
        )
        econ = Generator(
            unit_id="P1_econ",
            name="P1_econ",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=6.8,
            eford=0.0,
            plant_group="CC_REGULAR",
            is_campd_bin=True,
        )
        gens = [base_tr, econ]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=24)
        disp = np.zeros((2, 24))
        disp[0, 8:16] = 100.0
        disp[1, 8:16] = 50.0
        on = caiso_ra_mustoffer_min_gen(disp, fa, gens, 0.574, floor_online_hours=True)
        # min(0.574 x 400, 100) = 100 -> pinned at the tranche bound.
        np.testing.assert_allclose(on[0, 8:16], 100.0)
        # The incremental econ tranche is never a committable base band.
        np.testing.assert_allclose(on[1, :], 0.0)


class TestErcotGasBridgeFloorFleet(unittest.TestCase):
    """The ERCOT-gated P1-native wrapper."""

    def _setup(self, hours=48, **overrides):
        gen = _cc_gen()
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_gas_commitment_bridge=True, **overrides
        )
        p0 = _overnight_dispatch(hours).reshape(1, hours)
        mc = np.full((1, hours), 30.0)
        lmp = np.full((1, hours), 25.0)
        return cfg, [gen], fa, p0, lmp, mc

    def test_gate_off_returns_none(self):
        cfg, gens, fa, p0, lmp, mc = self._setup()
        cfg = cfg.with_overrides(ercot_gas_commitment_bridge=False)
        self.assertIsNone(
            ercot_gas_bridge_p1_floor_fleet(cfg, "ERCOT", gens, fa, p0, lmp, mc)
        )
        self.assertIsNone(build_ercot_gas_bridge_p1_prep(cfg, "ERCOT", gens, fa, mc))

    def test_non_ercot_returns_none(self):
        cfg, gens, fa, p0, lmp, mc = self._setup()
        self.assertIsNone(
            ercot_gas_bridge_p1_floor_fleet(cfg, "CAISO", gens, fa, p0, lmp, mc)
        )
        self.assertIsNone(build_ercot_gas_bridge_p1_prep(cfg, "CAISO", gens, fa, mc))

    def test_online_hours_flag_reaches_the_detector(self):
        # The ercot141 wiring test: the ScenarioConfig flag must actually widen
        # the floor through the pipeline wrapper, not merely be recorded (the
        # "recorded_cfg alone does not reach the solve" failure mode). Run hours
        # h6-21 / h30-45 are unfloored off, floored on, and the bridged gap is
        # unchanged either way.
        cfg, gens, fa, p0, lmp, mc = self._setup()
        off = ercot_gas_bridge_p1_floor_fleet(cfg, "ERCOT", gens, fa, p0, lmp, mc)
        on_cfg = cfg.with_overrides(ercot_gas_bridge_online_hours=True)
        on = ercot_gas_bridge_p1_floor_fleet(on_cfg, "ERCOT", gens, fa, p0, lmp, mc)
        self.assertIsNotNone(on)
        self.assertTrue(np.all(off.min_gen[0, 6:22] == 0.0))
        np.testing.assert_allclose(on.min_gen[0, 6:22], 0.574 * 300.0)
        np.testing.assert_allclose(on.min_gen[0, 30:46], 0.574 * 300.0)
        np.testing.assert_allclose(on.min_gen[0, 22:30], off.min_gen[0, 22:30])
        # Same mechanism id — a wider window, not a new mechanism (rule 19).
        self.assertTrue(
            np.all(on.min_gen_mechanism[0, 6:22] == MECH_GAS_COMMITMENT_BRIDGE)
        )
        # Still no floor where the plant is offline and unbridged.
        np.testing.assert_allclose(on.min_gen[0, 0:6], 0.0)

    def test_online_hours_without_bridge_fails_loud(self):
        # It widens the bridge's own floor: without the bridge there is nothing
        # to widen, so it must raise rather than silently solve the keeper.
        cfg, gens, fa, p0, lmp, mc = self._setup()
        bad = cfg.with_overrides(
            ercot_gas_commitment_bridge=False,
            ercot_gas_bridge_online_hours=True,
        )
        with self.assertRaises(ValueError) as ctx:
            build_ercot_gas_bridge_p1_preps(bad, "ERCOT", gens, fa, mc)
        self.assertIn("ercot_gas_bridge_online_hours", str(ctx.exception))

    def test_overnight_economic_bridge_floors_and_tags(self):
        # Near-marginal gas: hold (30-25) x 0.574 x 8 = 23 < 48.6 startup ->
        # the overnight gap is held at min-load; measured p50 x pmax = 172.2.
        cfg, gens, fa, p0, lmp, mc = self._setup()
        out = ercot_gas_bridge_p1_floor_fleet(cfg, "ERCOT", gens, fa, p0, lmp, mc)
        self.assertIsNotNone(out)
        np.testing.assert_allclose(out.min_gen[0, 22:30], 0.574 * 300.0)
        self.assertTrue(np.all(out.min_gen[0, :22] == 0.0))
        self.assertTrue(
            np.all(out.min_gen_mechanism[0, 22:30] == MECH_GAS_COMMITMENT_BRIDGE)
        )
        self.assertTrue(np.all(out.min_gen_mechanism[0, :22] == 0))
        # LP feasibility: availability covers the floor on floored hours.
        need = out.min_gen[0, 22:30] / 300.0
        self.assertTrue(np.all(out.availability[0, 22:30] >= need - 1e-12))
        # Input fleet untouched (dataclasses.replace, not mutation).
        self.assertTrue(fa.min_gen is None or np.all(fa.min_gen == 0.0))

    def test_startup_leg_off_drops_overnight_gap(self):
        # The 8 h gap >= the 6 h min-down: the physical bar alone catches
        # nothing (the ERCOT-62b "physical-only is near-inert" arm).
        cfg, gens, fa, p0, lmp, mc = self._setup(ercot_gas_bridge_startup=False)
        out = ercot_gas_bridge_p1_floor_fleet(cfg, "ERCOT", gens, fa, p0, lmp, mc)
        self.assertIsNone(out)

    def test_da_horizon_caps_multiday_gap(self):
        # A 35 h gap bridges without the horizon (62b construction) and is
        # dropped with it (the default market-design bound).
        hours = 72
        gen = _cc_gen()
        fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
        disp = np.zeros(hours)
        disp[0:6] = 300.0
        disp[41:48] = 300.0
        p0 = disp.reshape(1, hours)
        mc = np.full((1, hours), 26.0)
        lmp = np.full((1, hours), 25.0)
        on = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_gas_commitment_bridge=True
        )
        off = on.with_overrides(ercot_gas_bridge_da_horizon=False)
        self.assertIsNone(
            ercot_gas_bridge_p1_floor_fleet(on, "ERCOT", [gen], fa, p0, lmp, mc)
        )
        out = ercot_gas_bridge_p1_floor_fleet(off, "ERCOT", [gen], fa, p0, lmp, mc)
        self.assertIsNotNone(out)
        self.assertTrue(np.all(out.min_gen[0, 6:41] > 0.0))

    def test_ct_and_chp_never_floored(self):
        # CT (fast-start physics) and CC_CHP (steam host) with the same
        # bridgeable pattern: the bridge never touches them.
        hours = 48
        for fuel, group, hr in (
            ("gas_ct", "CT_PEAKER", 10.5),
            ("gas_cc", "CC_CHP", 7.0),
        ):
            gen = _cc_gen(plant_group=group, fuel=fuel, heat_rate=hr)
            fa = generators_to_fleet_arrays([gen], ["z"], hours=hours)
            cfg = ScenarioConfig(iso="ERCOT").with_overrides(
                ercot_gas_commitment_bridge=True
            )
            p0 = _overnight_dispatch(hours).reshape(1, hours)
            mc = np.full((1, hours), 30.0)
            lmp = np.full((1, hours), 25.0)
            self.assertIsNone(
                ercot_gas_bridge_p1_floor_fleet(cfg, "ERCOT", [gen], fa, p0, lmp, mc),
                msg=f"{fuel}/{group} must never be bridged",
            )

    def test_max_composition_keeps_incumbent_higher_floor(self):
        cfg, gens, fa, p0, lmp, mc = self._setup()
        fa.min_gen = np.zeros((1, 48))
        fa.min_gen[0, 25] = 250.0  # incumbent floor above the bridge's 172.2
        fa.min_gen_mechanism = np.zeros((1, 48), dtype=np.int8)
        fa.min_gen_mechanism[0, 25] = 3  # e.g. coal_mustrun id
        out = ercot_gas_bridge_p1_floor_fleet(cfg, "ERCOT", gens, fa, p0, lmp, mc)
        self.assertAlmostEqual(float(out.min_gen[0, 25]), 250.0)
        self.assertEqual(int(out.min_gen_mechanism[0, 25]), 3)
        self.assertAlmostEqual(float(out.min_gen[0, 24]), 0.574 * 300.0)
        self.assertEqual(int(out.min_gen_mechanism[0, 24]), MECH_GAS_COMMITMENT_BRIDGE)

    def test_prep_hook_wraps_floor_fleet(self):
        cfg, gens, fa, p0, lmp, mc = self._setup()
        prep = build_ercot_gas_bridge_p1_prep(cfg, "ERCOT", gens, fa, mc)
        self.assertIsNotNone(prep)

        class _R0:
            dispatch = p0
            prices = lmp

        out = prep(_R0())
        self.assertIsNotNone(out)
        self.assertTrue(np.any(out.min_gen_mechanism == MECH_GAS_COMMITMENT_BRIDGE))


class TestRegistry(unittest.TestCase):
    def test_mechanism_registered_and_ablated(self):
        self.assertEqual(
            MECH_NAMES[MECH_GAS_COMMITMENT_BRIDGE], "gas_commitment_bridge"
        )
        # A new merchant floor must carry an ablation decision (D-3 guard).
        assert_ablation_coverage()
        from market_sim.data.floor_mechanisms import MECH_ABLATION_FIELDS

        self.assertEqual(
            MECH_ABLATION_FIELDS[MECH_GAS_COMMITMENT_BRIDGE],
            {"ercot_gas_commitment_bridge": False},
        )


if __name__ == "__main__":
    unittest.main()
