"""Validation of the SPP gas commitment bridge (lane SPP-44).

Covers :func:`market_sim.pipeline.commitment.build_spp_gas_bridge_p1_prep` and
its floor :func:`market_sim.pipeline.commitment._spp_gas_bridge_floor` — the
SPP leg of the P1-native committed-state bridge family on the shared detector
:func:`market_sim.model.commitment.caiso_ra_mustoffer_min_gen`. Contract
(PRECOMMIT-spp-44-2026-09-07 §3):

* flag off / non-SPP ⇒ ``None`` (byte-identical P1 — rules 14/26); the field is
  registered in the cache-key drop set at its declared default so the default
  key is unmoved;
* the two eligible classes carry their OWN measured plant-basis fraction and
  min-run (``constants.SPP_GAS_BRIDGE_MIN_LOAD_FRAC`` / ``_MIN_RUN_HOURS``) —
  the reason the bridge runs the detector per class; every other row carries 0;
* fast-start CT units are NEVER floored, and that exclusion comes from unit
  PHYSICS (min-down 1 h, cheap starts), not a class-name tuple (rule 18) — a
  CT-classed unit that somehow carried slow-start physics would be caught by
  the fuel-type population filter, and a gas_cc unit with fast-start physics
  is refused by the physics gate;
* a P0 run shorter than the measured min-run is extended at min-load; a
  phantom P0 run whose margin cannot repay its startup is dropped by the
  commitment-real screen and extends nothing;
* D-2 attribution: floored gen-hours tagged ``MECH_SPP_GAS_COMMITMENT_BRIDGE``,
  a separate id from the ERCOT / NYISO legs; the mechanism is named and
  ablation-covered.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    SPP_GAS_BRIDGE_MIN_LOAD_FRAC,
    SPP_GAS_BRIDGE_MIN_RUN_HOURS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_ABLATION_FIELDS,
    MECH_NAMES,
    MECH_NYISO_GAS_COMMITMENT_BRIDGE,
    MECH_SPP_GAS_COMMITMENT_BRIDGE,
    assert_ablation_coverage,
)
from market_sim.pipeline.commitment import (
    _spp_bridge_min_run_hours,
    _spp_gas_bridge_floor,
    build_spp_gas_bridge_p1_prep,
)

_HOURS = 72


def _gen(unit_id, fuel, plant_group, pmax=300.0, heat_rate=7.0):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="z",
        fuel_type=fuel,
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
        plant_group=plant_group,
    )


def _config(**over):
    """An SPP config with the bridge armed; ``over`` tweaks single fields."""
    cfg = ScenarioConfig(iso="SPP")
    return cfg.with_overrides(spp_gas_commitment_bridge=True, **over)


class _R0:
    """The minimal ``r0`` shape the P1 fleet prep reads."""

    def __init__(self, dispatch, prices):
        self.dispatch = dispatch
        self.prices = prices


def _fleet():
    """One CC (heat rate 7 → f-class, min-down 6 h, $48.6/MW), one gas steamer
    (heat rate 11 → older subcritical, 12 h / $75), one CT (1 h / $19), one
    cogen CC."""
    gens = [
        _gen("cc1", "gas_cc", "CC_REGULAR", pmax=400.0, heat_rate=7.0),
        _gen("st1", "gas_st", "ST_GAS", pmax=500.0, heat_rate=11.0),
        _gen("ct1", "gas_ct", "CT_PEAKER", pmax=100.0, heat_rate=10.5),
        _gen("chp1", "gas_cc", "CC_CHP", pmax=200.0, heat_rate=7.0),
    ]
    fa = generators_to_fleet_arrays(gens, ["z"], _HOURS)
    return gens, fa


def _rich_p0(fa):
    """A P0 pattern where every unit runs h0-24 and h40-72 with a 16 h gap, and
    prices sit far above MC so every run is commitment-real and every economic
    bridge holds."""
    d = np.zeros((len(fa.pmax), _HOURS))
    d[:, :24] = fa.pmax[:, None]
    d[:, 40:] = fa.pmax[:, None]
    prices = np.full((1, _HOURS), 500.0)
    mc = np.full(d.shape, 20.0)
    return d, prices, mc


class TestMinRunVector(unittest.TestCase):
    def test_measured_constants_per_fuel_and_zero_elsewhere(self):
        gens, fa = _fleet()
        mr = _spp_bridge_min_run_hours(gens, fa)
        self.assertEqual(mr[0], SPP_GAS_BRIDGE_MIN_RUN_HOURS["gas_cc"])
        self.assertEqual(mr[1], SPP_GAS_BRIDGE_MIN_RUN_HOURS["gas_st"])
        self.assertEqual(mr[2], 0.0)  # CT: not in the population
        self.assertEqual(mr[3], 0.0)  # cogen: follows its steam host

    def test_constants_are_the_measured_plant_basis_values(self):
        # PRECOMMIT-spp-44 §2.2: plant-basis cap-weighted p50 / p25 from
        # campd_gas_commitment_params_plant_SPP.csv, frozen (rule 23).
        self.assertAlmostEqual(SPP_GAS_BRIDGE_MIN_LOAD_FRAC["gas_cc"], 0.209)
        self.assertAlmostEqual(SPP_GAS_BRIDGE_MIN_LOAD_FRAC["gas_st"], 0.090)
        self.assertEqual(SPP_GAS_BRIDGE_MIN_RUN_HOURS, {"gas_cc": 15.0, "gas_st": 5.0})


class TestFloorPhysicsAndScope(unittest.TestCase):
    def test_each_class_floors_at_its_own_measured_fraction(self):
        gens, fa = _fleet()
        d, prices, mc = _rich_p0(fa)
        floor = _spp_gas_bridge_floor(gens, fa, d, prices, mc)
        self.assertIsNotNone(floor)
        # The 16 h gap (h24-40) is >= min-down for both (6 h / 12 h) and within
        # the 24 h DA horizon; at LMP >> MC the hold cost is negative, so the
        # economic leg floors the gap at frac x pmax.
        self.assertTrue(np.allclose(floor[0, 24:40], 0.209 * 400.0))
        self.assertTrue(np.allclose(floor[1, 24:40], 0.090 * 500.0))
        # Outside the gap the unit is dispatched by P0 itself: no floor.
        self.assertTrue(np.all(floor[0, :24] == 0.0))
        self.assertTrue(np.all(floor[0, 40:] == 0.0))

    def test_fast_start_ct_and_cogen_are_never_floored(self):
        gens, fa = _fleet()
        d, prices, mc = _rich_p0(fa)
        floor = _spp_gas_bridge_floor(gens, fa, d, prices, mc)
        self.assertTrue(np.all(floor[2] == 0.0))  # CT: 1 h min-down, physics
        self.assertTrue(np.all(floor[3] == 0.0))  # cogen: detector rule

    def test_ct_exclusion_is_physics_not_the_name(self):
        # A gas_cc-fuelled CAMPD-bin row carrying a CT's fast-start physics on
        # its own bin (min-down 1 h, $19/MW start — the values every SPP
        # gas_ct tranche resolves) is refused by the physics gate even though
        # it is in the offered population: a legacy row reads the class table
        # by heat rate, a bin reads its own physics, and the gate is the same.
        gens, fa = _fleet()
        gens[0].is_campd_bin = True
        gens[0].min_down_hours = 1
        gens[0].min_run_hours = 1
        gens[0].startup_cost_per_mw = 19.0
        d, prices, mc = _rich_p0(fa)
        floor = _spp_gas_bridge_floor(gens, fa, d, prices, mc)
        # min-down 1 h: a 16 h gap is >= min-down (physical leg unreachable)
        # and the economic leg needs RA_BRIDGE_ECON_MIN_DOWN_HOURS (4 h) — so
        # nothing bridges the gap, while the slow-start steamer still does.
        self.assertTrue(np.all(floor[0, 24:40] == 0.0))
        self.assertTrue(np.allclose(floor[1, 24:40], 0.090 * 500.0))

    def test_short_run_is_extended_to_the_measured_min_run(self):
        gens, fa = _fleet()
        d = np.zeros((4, _HOURS))
        d[0, 10:13] = 400.0  # a 3 h CC run; min-run 15 h
        prices = np.full((1, _HOURS), 500.0)
        mc = np.full(d.shape, 20.0)
        floor = _spp_gas_bridge_floor(gens, fa, d, prices, mc)
        self.assertIsNotNone(floor)
        self.assertTrue(np.allclose(floor[0, 13:25], 0.209 * 400.0))
        self.assertTrue(np.all(floor[0, 25:] == 0.0))
        self.assertTrue(np.all(floor[0, :10] == 0.0))

    def test_phantom_run_is_dropped_by_the_commitment_real_screen(self):
        gens, fa = _fleet()
        d = np.zeros((4, _HOURS))
        d[0, 10:13] = 400.0
        # Margin per MW over the run = 3 h x (LMP - MC) x 1.0 = 3 x 5 = $15,
        # below the f-class $48.6/MW startup: a phantom, extends nothing.
        prices = np.full((1, _HOURS), 25.0)
        mc = np.full(d.shape, 20.0)
        floor = _spp_gas_bridge_floor(gens, fa, d, prices, mc)
        self.assertIsNone(floor)


class TestPrepGating(unittest.TestCase):
    def test_flag_off_returns_none(self):
        gens, fa = _fleet()
        cfg = ScenarioConfig(iso="SPP")
        self.assertFalse(cfg.spp_gas_commitment_bridge)
        self.assertIsNone(build_spp_gas_bridge_p1_prep(cfg, "SPP", gens, fa, None))

    def test_other_iso_returns_none(self):
        gens, fa = _fleet()
        cfg = ScenarioConfig(iso="NYISO").with_overrides(spp_gas_commitment_bridge=True)
        for iso in ("NYISO", "ERCOT", "CAISO", "PJM", "MISO", "NEISO"):
            self.assertIsNone(build_spp_gas_bridge_p1_prep(cfg, iso, gens, fa, None))

    def test_floored_hours_carry_the_spp_mechanism_id(self):
        gens, fa = _fleet()
        d, prices, mc = _rich_p0(fa)
        prep = build_spp_gas_bridge_p1_prep(_config(), "SPP", gens, fa, mc)
        self.assertIsNotNone(prep)
        fa1 = prep(_R0(d, prices))
        self.assertIsNotNone(fa1)
        tagged = fa1.min_gen_mechanism[0, 24:40]
        self.assertTrue(np.all(tagged == MECH_SPP_GAS_COMMITMENT_BRIDGE))
        self.assertNotEqual(
            MECH_SPP_GAS_COMMITMENT_BRIDGE, MECH_NYISO_GAS_COMMITMENT_BRIDGE
        )
        self.assertTrue(np.all(fa1.min_gen_mechanism[2] == 0))

    def test_mechanism_is_named_and_ablation_covered(self):
        self.assertEqual(
            MECH_NAMES[MECH_SPP_GAS_COMMITMENT_BRIDGE], "spp_gas_commitment_bridge"
        )
        self.assertEqual(
            MECH_ABLATION_FIELDS[MECH_SPP_GAS_COMMITMENT_BRIDGE],
            {"spp_gas_commitment_bridge": False},
        )
        assert_ablation_coverage()

    def test_default_cache_key_is_unmoved_by_the_field(self):
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS at its declared False: the
        # default config's key must not carry the field, and an armed config
        # must key distinctly.
        base = ScenarioConfig(iso="SPP")
        armed = base.with_overrides(spp_gas_commitment_bridge=True)
        self.assertEqual(base.cache_key(), ScenarioConfig(iso="SPP").cache_key())
        self.assertNotEqual(base.cache_key(), armed.cache_key())


if __name__ == "__main__":
    unittest.main()
