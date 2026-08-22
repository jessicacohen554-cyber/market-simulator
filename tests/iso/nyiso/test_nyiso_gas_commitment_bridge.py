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
* fast-start CT classes are NEVER bridged BY DEFAULT, and that exclusion comes
  from unit PHYSICS (min-down 1 h, cheap starts), not a class-name tuple
  (rule 18). ``nyiso_gas_bridge_ct`` (nyiso-90) adds the CT class to the
  detector for BLOCK COMMITMENT only: it can reach the ``min_run_hours``
  extension and NOTHING else, because a 1 h min-down makes the physical bridge
  unreachable and fails ``RA_BRIDGE_ECON_MIN_DOWN_HOURS`` for the economic one.
  ``TestCTBlockCommitment`` pins that separation;
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


class TestCTBlockCommitment(unittest.TestCase):
    """The ``nyiso_gas_bridge_ct`` leg (nyiso-90): min-run extension ONLY.

    The physics claim this class pins is the whole justification for admitting
    a fast-start class to the bridge: minimum-DOWN and minimum-RUN are
    independent properties, so giving a CT a minimum run does NOT re-open
    nyiso-87's exclusion of CTs from being HELD ACROSS an idle gap.
    """

    def _ct(self):
        gens = [_gen("CT", "gas_ct", "CT_PEAKER", heat_rate=10.5)]
        return gens, generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)

    def _armed(self, **over):
        return _config(nyiso_gas_bridge_min_run=True, nyiso_gas_bridge_ct=True, **over)

    def _floor(self, cfg, gens, fa, p0):
        return _nyiso_gas_bridge_floor(
            cfg,
            gens,
            fa,
            p0,
            np.full((1, _HOURS), 40.0),
            np.full((1, _HOURS), 30.0),
        )

    def test_off_by_default(self):
        """The gate is default-off, so every prior NYISO run is unchanged."""
        self.assertFalse(ScenarioConfig(iso="NYISO").nyiso_gas_bridge_ct)

    def test_short_run_is_extended_to_the_measured_min_run(self):
        gens, fa = self._ct()
        p0 = np.zeros((1, _HOURS))
        p0[0, 10] = 300.0  # a single-hour run, shorter than the 2 h min-run
        floor = self._floor(self._armed(), gens, fa, p0)
        self.assertIsNotNone(floor)
        # Hour 11 is the extension; it is floored at the CT min-load fraction.
        self.assertAlmostEqual(floor[0, 11], 0.238 * 300.0, places=6)
        # The run hour itself and everything else stay unfloored.
        self.assertEqual(floor[0, 10], 0.0)
        self.assertEqual(floor[0, 12], 0.0)
        self.assertEqual(int((floor[0] > 0.0).sum()), 1)

    def test_run_already_at_min_run_is_untouched(self):
        """A 2 h run needs no extension — the leg must be exactly inert."""
        gens, fa = self._ct()
        p0 = np.zeros((1, _HOURS))
        p0[0, 10:12] = 300.0
        self.assertIsNone(self._floor(self._armed(), gens, fa, p0))

    def test_long_idle_gap_is_never_bridged(self):
        """The core physics claim: a CT is still never HELD ACROSS a gap.

        Two runs already at/above the min-run, separated by a long idle gap that
        a CC would be economically bridged across. The CT must come back with
        NO floor at all — ``RA_BRIDGE_ECON_MIN_DOWN_HOURS`` still excludes it.
        """
        gens, fa = self._ct()
        p0 = np.zeros((1, _HOURS))
        p0[0, 10:14] = 300.0
        p0[0, 30:36] = 300.0
        self.assertIsNone(self._floor(self._armed(), gens, fa, p0))

    def test_inert_without_the_min_run_leg(self):
        """``nyiso_gas_bridge_ct`` alone has no reachable leg, so it must not arm."""
        gens, fa = self._ct()
        p0 = np.zeros((1, _HOURS))
        p0[0, 10] = 300.0
        self.assertIsNone(self._floor(_config(nyiso_gas_bridge_ct=True), gens, fa, p0))

    def test_min_run_array_uses_the_measured_ct_horizon(self):
        gens = [
            _gen("CT", "gas_ct", "CT_PEAKER", heat_rate=10.5),
            _gen("CC", "gas_cc", "CC_REGULAR", heat_rate=7.0),
        ]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        mr = _nyiso_bridge_min_run_hours(
            self._armed(nyiso_gas_bridge_cc_min_run_hours=21.0), gens, fa
        )
        self.assertEqual(mr[0], 2.0)  # the CT measured p25_capwtd
        self.assertEqual(mr[1], 21.0)
        # Off, the CT row carries no horizon at all.
        mr_off = _nyiso_bridge_min_run_hours(
            _config(nyiso_gas_bridge_min_run=True), gens, fa
        )
        self.assertEqual(mr_off[0], 0.0)

    def test_cogen_ct_is_still_excluded(self):
        """CT_CHP follows its steam host, armed or not (rule 19)."""
        gens = [_gen("CT", "gas_ct", "CT_CHP", heat_rate=10.5)]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        p0 = np.zeros((1, _HOURS))
        p0[0, 10] = 300.0
        self.assertIsNone(self._floor(self._armed(), gens, fa, p0))


if __name__ == "__main__":
    unittest.main()


class TestPlantMembershipExclusions(unittest.TestCase):
    """``nyiso_gas_bridge_plant_exclusions`` — the lay-up MEMBERSHIP correction.

    The bridge's half of a correction that previously existed only on the
    reliability floor (``reliability_floor_plant_exclusions``), so the same
    economically-laid-up plants were still floored by the OTHER mechanism
    (nyiso-140 fixed one mechanism, not the plant — rule 19 ``[R-ONE-MECH]``).

    Contract: default OFF is byte-identical; armed, a listed plant is dropped
    from the bridge population entirely while its unlisted neighbours keep the
    floor they had. Expressed through the detector's existing population gate
    (a non-positive ``min_load_frac_by_gen`` entry), so no class-name tuple and
    no new detector parameter is involved (rule 18 ``[R-PHYSICS]``).
    """

    def _fleet(self):
        """Two identical CC plants, one of which the artifact will exclude."""
        keep = _gen("KEEP", "gas_cc", "CC_REGULAR")
        keep.plant_code = 1111
        drop = _gen("DROP", "gas_cc", "CC_REGULAR")
        drop.plant_code = 2222
        gens = [keep, drop]
        return gens, generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)

    def _dispatch(self):
        """One 6 h run then a 4 h gap then another run — a bridgeable pattern."""
        disp = np.zeros((2, _HOURS))
        for g in (0, 1):
            disp[g, 10:16] = 300.0
            disp[g, 20:26] = 300.0
        return disp

    def _floor(self, cfg, monkeypatch_codes=None):
        # The consuming import is function-local, so the SOURCE module is what
        # a stub has to replace — patching the caller's namespace would miss it.
        import market_sim.data.bridge_layup_exclusions as seam

        gens, fa = self._fleet()
        p0 = self._dispatch()
        mc = np.full((2, _HOURS), 30.0)
        lmp = np.full((1, _HOURS), 25.0)
        if monkeypatch_codes is not None:
            original = seam.load_layup_exclusions
            seam.load_layup_exclusions = lambda iso: frozenset(monkeypatch_codes)
            try:
                return _nyiso_gas_bridge_floor(cfg, gens, fa, p0, lmp, mc)
            finally:
                seam.load_layup_exclusions = original
        return _nyiso_gas_bridge_floor(cfg, gens, fa, p0, lmp, mc)

    def test_default_off_is_byte_identical(self):
        """The flag defaults off, so the artifact is never even read."""
        base = self._floor(_config())
        off = self._floor(_config(nyiso_gas_bridge_plant_exclusions=False), [2222])
        self.assertIsNotNone(base)
        np.testing.assert_array_equal(base, off)

    def test_armed_drops_only_the_listed_plant(self):
        base = self._floor(_config())
        armed = self._floor(_config(nyiso_gas_bridge_plant_exclusions=True), [2222])
        self.assertIsNotNone(base)
        self.assertIsNotNone(armed)
        # The excluded plant loses its floor entirely...
        self.assertGreater(float(base[1].sum()), 0.0)
        self.assertEqual(float(armed[1].sum()), 0.0)
        # ...and its neighbour keeps exactly the floor it had.
        np.testing.assert_array_equal(base[0], armed[0])

    def test_empty_artifact_is_a_no_op(self):
        """A missing/empty artifact must not silently disarm the mechanism."""
        base = self._floor(_config())
        armed = self._floor(_config(nyiso_gas_bridge_plant_exclusions=True), [])
        np.testing.assert_array_equal(base, armed)

    def test_artifact_reader_selects_only_laid_up_rows(self):
        """The seam reads the real committed artifact and filters on laid_up."""
        from market_sim.data.bridge_layup_exclusions import load_layup_exclusions

        codes = load_layup_exclusions("NYISO")
        # The committed NYISO artifact is non-empty and every row it yields is
        # a plant the derive script marked laid_up.
        self.assertTrue(codes)
        # Roseton (8006) and Danskammer (2480) are the two large laid-up steam
        # stations the nyiso-143 D-4 rider convicted on this mechanism.
        self.assertIn(8006, codes)
        self.assertIn(2480, codes)
        # Port Jefferson (2517) is a temperature-conditional CYCLER, not a
        # laid-up plant: it is excluded from the RELIABILITY FLOOR (whose
        # always-on baseline it does not have) but must stay in the BRIDGE
        # population, which is keyed to detected runs it genuinely performs.
        self.assertNotIn(2517, codes)

    def test_unknown_iso_yields_no_exclusions(self):
        from market_sim.data.bridge_layup_exclusions import load_layup_exclusions

        self.assertEqual(load_layup_exclusions("NOSUCHISO"), frozenset())


class TestPerPlantMinRun(unittest.TestCase):
    """``nyiso_gas_bridge_plant_min_run`` — the per-plant min-run identification.

    nyiso-146: the class is not one run-length population (measured per-plant
    p25 spans 7-646 h against a 21 h class scalar), so when the gate is on a
    slow-start row whose plant appears in the measured artifact takes ITS OWN
    plant's value, REPLACING the class scalar (rule 19 ``[R-ONE-MECH]``);
    uncovered plants keep the class fallback, and the armed CT leg keeps its
    own required measured horizon. Default OFF is byte-identical.
    """

    def _fleet(self):
        """Two CC plants (one covered by the artifact) and one CT."""
        covered = _gen("COVERED", "gas_cc", "CC_REGULAR")
        covered.plant_code = 1111
        uncovered = _gen("UNCOVERED", "gas_cc", "CC_REGULAR")
        uncovered.plant_code = 2222
        ct = _gen("CT", "gas_ct", "CT_PEAKER")
        ct.plant_code = 1111  # same plant code — must NOT take the CC value
        gens = [covered, uncovered, ct]
        return gens, generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)

    def _min_run(self, cfg, mapping=None):
        # The consuming import is function-local, so the SOURCE module is what
        # a stub has to replace — patching the caller's namespace would miss it.
        import market_sim.data.perplant_min_run as seam

        gens, fa = self._fleet()
        if mapping is None:
            return _nyiso_bridge_min_run_hours(cfg, gens, fa)
        original = seam.load_perplant_min_run
        seam.load_perplant_min_run = lambda iso: dict(mapping)
        try:
            return _nyiso_bridge_min_run_hours(cfg, gens, fa)
        finally:
            seam.load_perplant_min_run = original

    def test_default_off_is_byte_identical(self):
        """The flag defaults off, so the artifact is never even read."""
        cfg = _config(nyiso_gas_bridge_cc_min_run_hours=21.0)
        base = self._min_run(cfg)
        off = self._min_run(
            cfg.with_overrides(nyiso_gas_bridge_plant_min_run=False),
            {1111: 134.75},
        )
        np.testing.assert_array_equal(base, off)

    def test_armed_replaces_the_scalar_for_covered_plants_only(self):
        cfg = _config(
            nyiso_gas_bridge_cc_min_run_hours=21.0,
            nyiso_gas_bridge_plant_min_run=True,
        )
        mr = self._min_run(cfg, {1111: 134.75})
        # Covered plant takes its own measured value, replacing the scalar...
        self.assertEqual(mr[0], 134.75)
        # ...the uncovered plant keeps the class scalar...
        self.assertEqual(mr[1], 21.0)
        # ...and the CT row never matches (leg off here: CT carries 0).
        self.assertEqual(mr[2], 0.0)

    def test_ct_leg_keeps_its_own_measured_horizon(self):
        """A CT sharing a covered plant code keeps the required CT horizon."""
        cfg = _config(
            nyiso_gas_bridge_min_run=True,
            nyiso_gas_bridge_ct=True,
            nyiso_gas_bridge_cc_min_run_hours=21.0,
            nyiso_gas_bridge_plant_min_run=True,
        )
        mr = self._min_run(cfg, {1111: 134.75})
        self.assertEqual(mr[0], 134.75)
        self.assertEqual(mr[2], float(cfg.nyiso_gas_bridge_ct_min_run_hours))

    def test_empty_artifact_falls_back_to_the_class_scalar(self):
        """A missing/empty artifact must not silently zero the extension."""
        cfg = _config(
            nyiso_gas_bridge_cc_min_run_hours=21.0,
            nyiso_gas_bridge_plant_min_run=True,
        )
        mr = self._min_run(cfg, {})
        self.assertEqual(mr[0], 21.0)
        self.assertEqual(mr[1], 21.0)

    def test_committed_artifact_reads_and_covers_the_object(self):
        """The real committed NYISO artifact carries the nyiso-145 objects."""
        from market_sim.data.perplant_min_run import load_perplant_min_run

        values = load_perplant_min_run("NYISO")
        self.assertTrue(values)
        # Bethlehem (2539), the over-cycling object: measured p25 far above
        # the class scalar; Flynn (7314) measures BELOW it.
        self.assertGreater(values[2539], 100.0)
        self.assertLess(values[7314], 21.0)
        # The misaligned Astoria campus pair is deliberately absent (the CAMPD
        # facility series spans two EIA plants — nyiso-145 §5).
        self.assertNotIn(55375, values)
        self.assertNotIn(57664, values)

    def test_unknown_iso_yields_no_coverage(self):
        from market_sim.data.perplant_min_run import load_perplant_min_run

        self.assertEqual(load_perplant_min_run("NOSUCHISO"), {})


class TestOnlineHoursLeg(unittest.TestCase):
    """``nyiso_gas_bridge_online_hours`` — the ercot141 LSL state leg, NYISO.

    nyiso-146's A/B measured that every gap/extension floor covers only
    P0-OFF hours while the CC over-cycling lives in P1 shutting committed
    plants INSIDE P0-on hours; this leg floors that state. Default OFF is
    byte-identical; armed, every hour of a detected run carries the min-load
    floor (capped at the base tranche), composing with the gap legs by
    maximum.
    """

    def _floor(self, cfg):
        gens = [_gen("CC", "gas_cc", "CC_REGULAR")]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)
        disp = np.zeros((1, _HOURS))
        disp[0, 10:16] = 300.0
        disp[0, 20:26] = 300.0
        mc = np.full((1, _HOURS), 30.0)
        lmp = np.full((1, _HOURS), 25.0)
        return _nyiso_gas_bridge_floor(cfg, gens, fa, disp, lmp, mc)

    def test_default_off_is_byte_identical(self):
        base = self._floor(_config())
        off = self._floor(_config(nyiso_gas_bridge_online_hours=False))
        np.testing.assert_array_equal(base, off)

    def test_armed_floors_the_detected_run_hours(self):
        base = self._floor(_config())
        armed = self._floor(_config(nyiso_gas_bridge_online_hours=True))
        # The gap floor is unchanged (maximum-composition never lowers)...
        self.assertTrue(np.all(armed >= base))
        # ...and the run hours themselves now carry a floor.
        self.assertTrue(np.all(armed[0, 10:16] > 0.0))
        self.assertTrue(np.all(armed[0, 20:26] > 0.0))
        self.assertEqual(float(base[0, 10:16].sum()), 0.0)

    def test_offline_hours_stay_unfloored(self):
        armed = self._floor(_config(nyiso_gas_bridge_online_hours=True))
        # Hours outside runs and outside the bridged gap carry no floor.
        self.assertEqual(float(armed[0, 40:].sum()), 0.0)


class TestStateFloorDutyScoping(unittest.TestCase):
    """``nyiso_gas_bridge_state_floor_min_run`` — duty scoping of the state leg.

    The online-hours floor holds only plants whose measured run-length p25
    clears the population gap; the rest keep gap/extension floors only.
    """

    def _fleet(self):
        base = _gen("BASE", "gas_cc", "CC_REGULAR")
        base.plant_code = 1111  # in the state cohort
        cyc = _gen("CYC", "gas_cc", "CC_REGULAR")
        cyc.plant_code = 2222  # below the gap
        gens = [base, cyc]
        return gens, generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)

    def _floor(self, cfg):
        import market_sim.data.perplant_min_run as seam

        gens, fa = self._fleet()
        disp = np.zeros((2, _HOURS))
        for g in (0, 1):
            disp[g, 10:16] = 300.0
            disp[g, 20:26] = 300.0
        mc = np.full((2, _HOURS), 30.0)
        lmp = np.full((1, _HOURS), 25.0)
        original = seam.load_perplant_min_run
        # 1111 measures p25 = 200 h (clears the 100 h gap); 2222 = 12 h.
        seam.load_perplant_min_run = lambda iso: {1111: 200.0, 2222: 12.0}
        try:
            return _nyiso_gas_bridge_floor(cfg, gens, fa, disp, lmp, mc)
        finally:
            seam.load_perplant_min_run = original

    def test_scoped_holds_only_the_cohort_run_hours(self):
        armed = self._floor(
            _config(
                nyiso_gas_bridge_online_hours=True,
                nyiso_gas_bridge_state_floor_min_run=True,
            )
        )
        # The cohort plant's run hours carry the state floor...
        self.assertTrue(np.all(armed[0, 10:16] > 0.0))
        # ...the cycler's run hours do NOT (its gap floor is untouched)...
        self.assertEqual(float(armed[1, 10:16].sum()), 0.0)
        self.assertTrue(np.all(armed[1, 16:20] > 0.0))  # the bridged gap

    def test_unscoped_still_holds_everyone(self):
        armed = self._floor(_config(nyiso_gas_bridge_online_hours=True))
        self.assertTrue(np.all(armed[0, 10:16] > 0.0))
        self.assertTrue(np.all(armed[1, 10:16] > 0.0))

    def test_scoping_flag_alone_is_inert(self):
        base = self._floor(_config())
        scoped_only = self._floor(
            _config(nyiso_gas_bridge_state_floor_min_run=True)
        )
        np.testing.assert_array_equal(base, scoped_only)


class TestReserveDutyMembershipExclusions(unittest.TestCase):
    """``nyiso_gas_bridge_reserve_duty_exclusions`` — the duty MEMBERSHIP channel.

    nyiso-152: the measured capacity-only CC cohort (``reserve_duty_cc_NYISO``)
    is not in the day-ahead energy-commitment population, and the CAMPD lay-up
    channel cannot reach a plant with no CAMPD series (Allegany 7784 is
    e923-basis). Same population-gate expression as the lay-up channel — a
    second measured membership signal on ONE mechanism (rules 17/18/19).

    Contract: default OFF is byte-identical (the artifact is never read);
    armed, a duty-cohort plant is dropped from the bridge population entirely
    while its unlisted neighbour keeps the floor it had; the two membership
    channels compose by union.
    """

    def _fleet(self):
        keep = _gen("KEEP", "gas_cc", "CC_REGULAR")
        keep.plant_code = 1111
        drop = _gen("DROP", "gas_cc", "CC_REGULAR")
        drop.plant_code = 7784
        gens = [keep, drop]
        return gens, generators_to_fleet_arrays(gens, ["z"], hours=_HOURS)

    def _dispatch(self):
        disp = np.zeros((2, _HOURS))
        for g in (0, 1):
            disp[g, 10:16] = 300.0
            disp[g, 20:26] = 300.0
        return disp

    def _floor(self, cfg, duty_codes=None, layup_codes=None):
        # Both consuming imports are function-local, so the SOURCE modules are
        # what a stub has to replace (the lay-up test's own convention).
        import market_sim.data.bridge_layup_exclusions as layup_seam
        import market_sim.data.reserve_duty as duty_seam

        gens, fa = self._fleet()
        p0 = self._dispatch()
        mc = np.full((2, _HOURS), 30.0)
        lmp = np.full((1, _HOURS), 25.0)
        orig_duty = duty_seam.load_reserve_duty_cc
        orig_layup = layup_seam.load_layup_exclusions
        if duty_codes is not None:
            duty_seam.load_reserve_duty_cc = lambda iso: frozenset(duty_codes)
        if layup_codes is not None:
            layup_seam.load_layup_exclusions = lambda iso: frozenset(layup_codes)
        try:
            return _nyiso_gas_bridge_floor(cfg, gens, fa, p0, lmp, mc)
        finally:
            duty_seam.load_reserve_duty_cc = orig_duty
            layup_seam.load_layup_exclusions = orig_layup

    def test_default_off_is_byte_identical(self):
        base = self._floor(_config())
        off = self._floor(
            _config(nyiso_gas_bridge_reserve_duty_exclusions=False), [7784]
        )
        self.assertIsNotNone(base)
        np.testing.assert_array_equal(base, off)

    def test_armed_drops_only_the_duty_plant(self):
        base = self._floor(_config())
        armed = self._floor(
            _config(nyiso_gas_bridge_reserve_duty_exclusions=True), [7784]
        )
        self.assertIsNotNone(base)
        self.assertIsNotNone(armed)
        self.assertGreater(float(base[1].sum()), 0.0)
        self.assertEqual(float(armed[1].sum()), 0.0)
        np.testing.assert_array_equal(base[0], armed[0])

    def test_empty_artifact_is_a_no_op(self):
        base = self._floor(_config())
        armed = self._floor(
            _config(nyiso_gas_bridge_reserve_duty_exclusions=True), []
        )
        np.testing.assert_array_equal(base, armed)

    def test_channels_compose_by_union(self):
        """Lay-up excludes one plant, duty the other — both floors go."""
        armed = self._floor(
            _config(
                nyiso_gas_bridge_plant_exclusions=True,
                nyiso_gas_bridge_reserve_duty_exclusions=True,
            ),
            duty_codes=[7784],
            layup_codes=[1111],
        )
        self.assertIsNone(armed)  # nobody left to floor

    def test_artifact_reader_selects_only_duty_rows(self):
        """The seam reads the real committed artifact and filters on duty."""
        from market_sim.data.reserve_duty import load_reserve_duty_cc

        codes = load_reserve_duty_cc("NYISO")
        self.assertTrue(codes)
        # Allegany — the CEMS-invisible plant this channel exists to reach.
        self.assertIn(7784, codes)
        # High-CF baseload CCs are not duty plants.
        self.assertNotIn(2500, codes)  # Ravenswood, online share 0.9492
        self.assertNotIn(55375, codes)  # Astoria Energy, 0.9919
