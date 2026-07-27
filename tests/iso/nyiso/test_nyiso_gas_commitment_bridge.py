"""Validation of the NYISO gas commitment bridge (nyiso-87).

Covers :func:`market_sim.pipeline.commitment.build_nyiso_gas_bridge_p1_prep` and
the minimum-run-duration extension it adds to the shared detector
(:func:`market_sim.model.commitment.caiso_ra_mustoffer_min_gen`) — the P1-native
replacement for the h14-21 peak-window reliability floors (owner directive
2026-07-27). Contract:

* flag off / non-NYISO ⇒ ``None`` (byte-identical P1 — rules 14/26);
* ``min_run_hours=None`` is byte-identical on the shared detector, so CAISO and
  ERCOT are untouched;
* a P0 run shorter than the unit's minimum run is EXTENDED, the extension hours
  floored at minimum stable load, and the extension is what closes a following
  gap — never a second floor on the same hours (rule 19);
* the two eligible classes carry their OWN measured min-load fraction
  (CC 0.523 / ST_GAS 0.239) — the reason the bridge runs the detector per class;
* fast-start CT classes are NEVER bridged, and that exclusion comes from unit
  PHYSICS (min-down 1 h, cheap starts), not a class-name tuple (rule 18);
* D-2 attribution: floored gen-hours tagged
  ``MECH_NYISO_GAS_COMMITMENT_BRIDGE``, separate from the ERCOT leg's id.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_NAMES,
    MECH_NYISO_GAS_COMMITMENT_BRIDGE,
    assert_ablation_coverage,
)
from market_sim.model.commitment import caiso_ra_mustoffer_min_gen
from market_sim.pipeline.commitment import (
    _nyiso_bridge_min_run_hours,
    _nyiso_gas_bridge_floor,
    build_nyiso_gas_bridge_p1_prep,
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
    """A NYISO config with the bridge armed; ``over`` tweaks single legs."""
    cfg = ScenarioConfig(iso="NYISO")
    return cfg.with_overrides(nyiso_gas_commitment_bridge=True, **over)


class _R0:
    """The minimal ``r0`` shape the P1 fleet prep reads."""

    def __init__(self, dispatch, prices):
        self.dispatch = dispatch
        self.prices = prices


class TestMinRunExtension(unittest.TestCase):
    """The ``min_run_hours`` extension on the shared ISO-neutral detector."""

    def _fleet(self):
        gen = _gen("CC", "gas_cc", "CC_REGULAR")
        return [gen], generators_to_fleet_arrays([gen], ["z"], hours=_HOURS)

    def _two_short_runs(self):
        """Two 3 h runs separated by a 20 h gap — both under any CC min-run."""
        disp = np.zeros((1, _HOURS))
        disp[0, 10:13] = 300.0
        disp[0, 33:36] = 300.0
        return disp

    def test_default_none_is_byte_identical(self):
        gens, fa = self._fleet()
        p0 = self._two_short_runs()
        mc = np.full((1, _HOURS), 30.0)
        lmp = np.full((1, _HOURS), 25.0)
        kw = dict(p1_prices=lmp, base_mc=mc, startup_bridge=True)
        base = caiso_ra_mustoffer_min_gen(p0, fa, gens, 0.523, **kw)
        explicit_none = caiso_ra_mustoffer_min_gen(
            p0, fa, gens, 0.523, min_run_hours=None, **kw
        )
        np.testing.assert_array_equal(base, explicit_none)

    def test_extension_floors_the_hours_after_a_short_run(self):
        gens, fa = self._fleet()
        p0 = self._two_short_runs()
        mc = np.full((1, _HOURS), 30.0)
        lmp = np.full((1, _HOURS), 40.0)
        # startup_bridge OFF isolates the extension: the 20 h idle gap is
        # longer than this unit's 6 h min-down, so the physical restart bar
        # cannot fire and anything floored here is the min-run extension.
        floor = caiso_ra_mustoffer_min_gen(
            p0,
            fa,
            gens,
            0.523,
            p1_prices=lmp,
            base_mc=mc,
            startup_bridge=False,
            min_run_hours=np.array([8.0]),
        )
        # Run 1 is h10-12; an 8 h min-run extends it to h10-17, so h13-17 are
        # floored at min-load and the in-run hours are NOT (dispatch owns them).
        self.assertTrue(np.all(floor[0, 13:18] > 0.0))
        np.testing.assert_allclose(floor[0, 10:13], 0.0)
        # ... and the hours past the extension, before run 2, stay unfloored
        # (the gap that remains is a genuine idle gap, not the extension).
        np.testing.assert_allclose(floor[0, 18:33], 0.0)

    def test_economic_bridge_still_covers_the_remaining_gap(self):
        """With the economic leg ON, the post-extension gap bridges as usual."""
        gens, fa = self._fleet()
        p0 = self._two_short_runs()
        floor = caiso_ra_mustoffer_min_gen(
            p0,
            fa,
            gens,
            0.523,
            p1_prices=np.full((1, _HOURS), 40.0),  # in-merit: holding is cheap
            base_mc=np.full((1, _HOURS), 30.0),
            startup_bridge=True,
            min_run_hours=np.array([8.0]),
        )
        # Extension (h13-17) and the economic bridge (h18-32) compose to ONE
        # continuous min-load band at the same level — one mechanism, one id.
        np.testing.assert_allclose(
            floor[0, 13:33], np.full(20, 0.523 * 300.0), rtol=1e-9
        )

    def test_extension_target_is_the_min_load_fraction(self):
        gens, fa = self._fleet()
        p0 = self._two_short_runs()
        floor = caiso_ra_mustoffer_min_gen(
            p0,
            fa,
            gens,
            0.523,
            p1_prices=np.full((1, _HOURS), 40.0),
            base_mc=np.full((1, _HOURS), 30.0),
            min_run_hours=np.array([8.0]),
        )
        np.testing.assert_allclose(floor[0, 14], 0.523 * 300.0, rtol=1e-9)

    def test_extension_closes_the_gap_rather_than_double_flooring(self):
        """A min-run long enough to reach the next run must not re-bridge it."""
        gens, fa = self._fleet()
        p0 = self._two_short_runs()  # run1 h10-12, run2 h33-35
        floor = caiso_ra_mustoffer_min_gen(
            p0,
            fa,
            gens,
            0.523,
            p1_prices=np.full((1, _HOURS), 40.0),
            base_mc=np.full((1, _HOURS), 30.0),
            startup_bridge=True,
            min_run_hours=np.array([23.0]),  # h10 + 23 = h33 == run 2 start
        )
        # The whole span h13..h32 is floored exactly once, at min-load — the
        # extension. Nothing is floored above it, so no second mechanism
        # stacked on the same hours (rule 19).
        self.assertTrue(np.all(floor[0, 13:33] > 0.0))
        np.testing.assert_allclose(
            floor[0, 13:33], np.full(20, 0.523 * 300.0), rtol=1e-9
        )
        # In-run hours remain dispatch's, never floored.
        np.testing.assert_allclose(floor[0, 33:36], 0.0)

    def test_extension_is_clipped_at_the_horizon(self):
        gens, fa = self._fleet()
        p0 = np.zeros((1, _HOURS))
        p0[0, _HOURS - 3 :] = 300.0
        floor = caiso_ra_mustoffer_min_gen(
            p0,
            fa,
            gens,
            0.523,
            p1_prices=np.full((1, _HOURS), 40.0),
            base_mc=np.full((1, _HOURS), 30.0),
            min_run_hours=np.array([48.0]),
        )
        self.assertEqual(floor.shape, (1, _HOURS))
        np.testing.assert_allclose(floor, 0.0)  # nothing left to extend into


class TestClassScopeAndPhysics(unittest.TestCase):
    """Per-class min-load fractions and the rule-18 fast-start exclusion."""

    def test_min_run_table_lookup_skips_ineligible_units(self):
        gens = [
            _gen("CC", "gas_cc", "CC_REGULAR", heat_rate=7.0),
            _gen("ST", "gas_st", "ST_GAS", heat_rate=11.0),
            _gen("CT", "gas_ct", "CT_PEAKER", heat_rate=10.5),
            _gen("CHP", "gas_cc", "CC_CHP", heat_rate=7.0),
        ]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        mr = _nyiso_bridge_min_run_hours(_config(), gens, fa)
        self.assertGreater(mr[0], 0.0)  # CC from CC_COMMITMENT_PARAMS
        self.assertGreater(mr[1], 0.0)  # ST from ST_GAS_COMMITMENT_PARAMS
        self.assertEqual(mr[2], 0.0)  # CT is never bridged
        self.assertEqual(mr[3], 0.0)  # cogens follow their steam host

    def test_config_override_beats_the_class_table(self):
        gens = [_gen("CC", "gas_cc", "CC_REGULAR", heat_rate=7.0)]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        cfg = _config(nyiso_gas_bridge_cc_min_run_hours=24.0)
        np.testing.assert_allclose(_nyiso_bridge_min_run_hours(cfg, gens, fa), [24.0])

    def test_each_class_floors_at_its_own_measured_fraction(self):
        gens = [
            _gen("CC", "gas_cc", "CC_REGULAR", pmax=300.0, heat_rate=7.0),
            _gen("ST", "gas_st", "ST_GAS", pmax=300.0, heat_rate=11.0),
        ]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        # One short run each; the min-run extension is the cleanest way to see
        # the target level without the gap economics in the way.
        p0 = np.zeros((2, _HOURS))
        p0[:, 10:13] = 300.0
        cfg = _config(nyiso_gas_bridge_min_run=True, nyiso_gas_bridge_startup=False)
        floor = _nyiso_gas_bridge_floor(
            cfg,
            gens,
            fa,
            p0,
            np.full((1, _HOURS), 40.0),
            np.full((2, _HOURS), 30.0),
        )
        self.assertIsNotNone(floor)
        np.testing.assert_allclose(
            floor[0, 14], cfg.nyiso_gas_bridge_cc_min_load_frac * 300.0, rtol=1e-9
        )
        np.testing.assert_allclose(
            floor[1, 14], cfg.nyiso_gas_bridge_st_min_load_frac * 300.0, rtol=1e-9
        )
        # The two classes' fractions genuinely differ — the reason the bridge
        # runs the detector once per class rather than once for both.
        self.assertGreater(floor[0, 14], 2.0 * floor[1, 14])

    def test_fast_start_ct_is_never_floored(self):
        gens = [_gen("CT", "gas_ct", "CT_PEAKER", heat_rate=10.5)]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        p0 = np.zeros((1, _HOURS))
        p0[0, 10:13] = 300.0
        p0[0, 30:36] = 300.0
        floor = _nyiso_gas_bridge_floor(
            _config(nyiso_gas_bridge_min_run=True),
            gens,
            fa,
            p0,
            np.full((1, _HOURS), 40.0),
            np.full((1, _HOURS), 30.0),
        )
        self.assertIsNone(floor)


class TestPrepGating(unittest.TestCase):
    """Gate/ISO exclusivity and the D-2 attribution stamp."""

    def _setup(self):
        gens = [_gen("CC", "gas_cc", "CC_REGULAR", heat_rate=7.0)]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        return gens, fa, np.full((1, _HOURS), 30.0)

    def test_flag_off_returns_none(self):
        gens, fa, mc = self._setup()
        cfg = ScenarioConfig(iso="NYISO")
        self.assertIsNone(build_nyiso_gas_bridge_p1_prep(cfg, "NYISO", gens, fa, mc))

    def test_other_iso_returns_none(self):
        gens, fa, mc = self._setup()
        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NEISO"):
            self.assertIsNone(
                build_nyiso_gas_bridge_p1_prep(_config(), iso, gens, fa, mc),
                msg=iso,
            )

    def test_floored_hours_carry_the_nyiso_mechanism_id(self):
        gens, fa, mc = self._setup()
        prep = build_nyiso_gas_bridge_p1_prep(
            _config(nyiso_gas_bridge_min_run=True), "NYISO", gens, fa, mc
        )
        self.assertIsNotNone(prep)
        p0 = np.zeros((1, _HOURS))
        p0[0, 10:13] = 300.0
        floored = prep(_R0(p0, np.full((1, _HOURS), 40.0)))
        self.assertIsNotNone(floored)
        mech = floored.min_gen_mechanism
        tagged = mech == MECH_NYISO_GAS_COMMITMENT_BRIDGE
        self.assertTrue(tagged.any())
        # The stamped hours are exactly the ones the floor raised.
        self.assertTrue(np.all(floored.min_gen[tagged] > 0.0))
        # Availability is raised so min_gen <= pmax x availability stays feasible.
        need = floored.min_gen / np.maximum(fa.pmax, 1.0)[:, None]
        self.assertTrue(np.all(floored.availability + 1e-9 >= need))

    def test_mechanism_is_named_and_ablation_covered(self):
        self.assertEqual(
            MECH_NAMES[MECH_NYISO_GAS_COMMITMENT_BRIDGE],
            "nyiso_gas_commitment_bridge",
        )
        assert_ablation_coverage()


if __name__ == "__main__":
    unittest.main()
