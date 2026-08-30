"""Toy-system tests for the O7 attribution harness (scripts/probes).

The trivial-first ladder of ``docs/testing.md`` for
``scripts/probes/o7_attribution_harness.py``: the pure mapping / de-laddering
functions on hand-built fleets, then the REAL ``run_energy_solve`` seam on a
1-zone / 24-hour system — proving on a system small enough to inspect that

* merging the Δmc component into ``mc_bid_adjust`` leaves the P0 solution
  bitwise identical (the HP-1 mechanism of
  ``docs/PRECOMMIT-o7-attribution-harness-2026-08-30.md``), and
* the de-laddered P1 clears the coarse top-block price on the refined
  geometry (the finding-§5 construction), visible directly in the toy duals.

Nothing here touches ``data/`` or solves a real year; the real-year exercise
is the probe's own job.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes import o7_attribution_harness as h  # noqa: E402
from tests.helpers.builders import base_scenario, make_gen  # noqa: E402

from market_sim.data.fleet import generators_to_fleet_arrays  # noqa: E402
from market_sim.pipeline.solve import run_energy_solve  # noqa: E402

T = 24

#: The toy refined plant: 2 body blocks (30 MW @ $20/$30) + 3 sub-slices
#: (10 MW @ $38/$40/$42 — capacity-mean-preserving around the $40 coarse top
#: block), plus a $200 peaker backstop in both fleets.
COARSE_ROWS = [
    ("CC_REGULAR_Z0_p1_econc00", 30.0, 20.0),
    ("CC_REGULAR_Z0_p1_econc01", 30.0, 30.0),
    ("CC_REGULAR_Z0_p1_econc02", 30.0, 40.0),
    ("CT_PEAKER_Z0_p2_peak", 100.0, 200.0),
]
REFINED_ROWS = [
    ("CC_REGULAR_Z0_p1_econc00", 30.0, 20.0),
    ("CC_REGULAR_Z0_p1_econc01", 30.0, 30.0),
    ("CC_REGULAR_Z0_p1_econc02", 10.0, 38.0),
    ("CC_REGULAR_Z0_p1_econc03", 10.0, 40.0),
    ("CC_REGULAR_Z0_p1_econc04", 10.0, 42.0),
    ("CT_PEAKER_Z0_p2_peak", 100.0, 200.0),
]


def _fleet(rows):
    """Build ``(generators, FleetArrays, mc_base)`` for one toy fleet spec."""
    gens = [
        # is_campd_bin=True with the zero startup_cost_per_mw default: the
        # toy rows are startup-free like real econ slices, so the markup is
        # zero and the price assertions read the LP duals directly.
        make_gen(uid, "Z0", pmax_mw=cap, pmin_mw=0.0, eford=0.0, is_campd_bin=True)
        for uid, cap, _ in rows
    ]
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=T)
    mc = np.vstack([np.full(T, mc_r) for _, _, mc_r in rows])
    return gens, fa, mc


def _ids(rows):
    return [uid for uid, _, _ in rows]


def _pmax(rows):
    return np.array([cap for _, cap, _ in rows])


class TestCanonHash(unittest.TestCase):
    """Content-addressed hashing: deterministic, bit-sensitive, None-safe."""

    def test_deterministic_and_value_sensitive(self):
        a = np.arange(12, dtype=float).reshape(3, 4)
        self.assertEqual(h.canon_hash(a), h.canon_hash(a.copy()))
        b = a.copy()
        b[2, 3] += 1e-12
        self.assertNotEqual(h.canon_hash(a), h.canon_hash(b))

    def test_shape_and_dtype_sensitive(self):
        a = np.zeros(6)
        self.assertNotEqual(h.canon_hash(a), h.canon_hash(a.reshape(2, 3)))
        self.assertNotEqual(h.canon_hash(a), h.canon_hash(a.astype(np.float32)))

    def test_none_sentinel(self):
        self.assertEqual(h.canon_hash(None), h.canon_hash(None))
        self.assertNotEqual(h.canon_hash(None), h.canon_hash(np.zeros(1)))


class TestRunStats(unittest.TestCase):
    """The 188-convention (starts, on_hours) reducer."""

    def test_patterns(self):
        self.assertEqual(h.run_stats(np.zeros(8)), (0, 0))
        self.assertEqual(h.run_stats(np.array([0, 5, 5, 0, 3, 0, 0, 9.0])), (3, 4))
        self.assertEqual(h.run_stats(np.full(8, 2.0)), (1, 8))
        # Dispatch dust below ON_MW is not a commitment decision.
        self.assertEqual(h.run_stats(np.full(8, h.ON_MW / 2)), (0, 0))


class TestDeladderMap(unittest.TestCase):
    """Row-mapping logic on hand-built id lists (precommit §1.2)."""

    def test_refined_plant_maps_subslices_to_parent(self):
        m = h.build_deladder_map(_ids(COARSE_ROWS), _ids(REFINED_ROWS))
        self.assertEqual(m["refined_plants"], ["CC_REGULAR_Z0_p1"])
        # Sub-slices econc02..04 (refined rows 2,3,4) -> coarse econc02 (row 2).
        np.testing.assert_array_equal(m["target_refined"], [2, 3, 4])
        np.testing.assert_array_equal(m["target_parent_coarse"], [2, 2, 2])
        # Body rows 0,1 pair positionally; the peaker pairs by id.
        pairs = set(zip(m["equal_pairs_coarse"], m["equal_pairs_refined"]))
        self.assertEqual(pairs, {(0, 0), (1, 1), (3, 5)})

    def test_unrefined_plant_is_identity(self):
        m = h.build_deladder_map(_ids(COARSE_ROWS), _ids(COARSE_ROWS))
        self.assertEqual(m["refined_plants"], [])
        self.assertEqual(m["target_refined"].size, 0)
        self.assertEqual(m["equal_pairs_coarse"].size, len(COARSE_ROWS))

    def test_bad_count_relation_is_a_stop(self):
        refined = _ids(REFINED_ROWS) + ["CC_REGULAR_Z0_p1_econc05"]
        with self.assertRaisesRegex(ValueError, "stop-report"):
            h.build_deladder_map(_ids(COARSE_ROWS), refined)

    def test_noncandidate_mismatch_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "non-econc"):
            h.build_deladder_map(
                _ids(COARSE_ROWS), _ids(REFINED_ROWS) + ["CT_PEAKER_Z0_p9_peak"]
            )

    def test_prefix_mismatch_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "prefixes differ"):
            h.build_deladder_map(
                _ids(COARSE_ROWS) + ["ST_GAS_Z0_p3_econc00"], _ids(REFINED_ROWS)
            )

    def test_noncontiguous_indices_are_an_error(self):
        coarse = [u.replace("econc01", "econc07") for u in _ids(COARSE_ROWS)]
        refined = [u.replace("econc01", "econc07") for u in _ids(REFINED_ROWS)]
        with self.assertRaisesRegex(ValueError, "non-contiguous"):
            h.build_deladder_map(coarse, refined)


class TestDeladderDelta(unittest.TestCase):
    """Δmc values and the equality/capacity asserts (precommit §1.1–§1.2)."""

    def setUp(self):
        self.map = h.build_deladder_map(_ids(COARSE_ROWS), _ids(REFINED_ROWS))
        _, _, self.c_mc = _fleet(COARSE_ROWS)
        _, _, self.r_mc = _fleet(REFINED_ROWS)

    def test_delta_values(self):
        delta, diag = h.compute_deladder_delta(
            self.map, self.c_mc, self.r_mc, _pmax(COARSE_ROWS), _pmax(REFINED_ROWS)
        )
        # Rungs 38/40/42 de-laddered to the $40 coarse top block.
        np.testing.assert_array_equal(delta[2], np.full(T, 2.0))
        np.testing.assert_array_equal(delta[3], np.zeros(T))
        np.testing.assert_array_equal(delta[4], np.full(T, -2.0))
        # Zero everywhere the refinement cannot touch.
        np.testing.assert_array_equal(delta[[0, 1, 5]], 0.0)
        self.assertEqual(diag["rows_targeted"], 3)
        self.assertEqual(diag["plants_refined"], 1)
        self.assertAlmostEqual(diag["delta_abs_max_usd_mwh"], 2.0)

    def test_body_inequality_is_a_stop(self):
        bad = self.r_mc.copy()
        bad[1, 5] += 1e-9  # a body row differing from its coarse pair
        with self.assertRaisesRegex(ValueError, "more than SCHEME R1"):
            h.compute_deladder_delta(
                self.map, self.c_mc, bad, _pmax(COARSE_ROWS), _pmax(REFINED_ROWS)
            )

    def test_capacity_violation_is_a_stop(self):
        bad = _pmax(REFINED_ROWS)
        bad[3] = 12.0  # sub-slice no longer parent/n
        with self.assertRaisesRegex(ValueError, "parent/n"):
            h.compute_deladder_delta(
                self.map, self.c_mc, self.r_mc, _pmax(COARSE_ROWS), bad
            )


class TestSeamBitIdentity(unittest.TestCase):
    """The real ``run_energy_solve`` seam on the toy system (1 zone, 24 h)."""

    @classmethod
    def setUpClass(cls):
        cls.gens, cls.fa, cls.r_mc = _fleet(REFINED_ROWS)
        _, _, cls.c_mc = _fleet(COARSE_ROWS)
        cls.map = h.build_deladder_map(_ids(COARSE_ROWS), _ids(REFINED_ROWS))
        cls.delta, _ = h.compute_deladder_delta(
            cls.map, cls.c_mc, cls.r_mc, _pmax(COARSE_ROWS), _pmax(REFINED_ROWS)
        )
        # 8 h inside the ramp body ($30 both legs), 8 h on the first rung
        # (ladder $38 vs de-laddered $40), 8 h on the third rung ($42 vs $40).
        cls.demand = np.concatenate(
            [np.full(8, 50.0), np.full(8, 65.0), np.full(8, 85.0)]
        )[None, :]
        cls.config = base_scenario(mode="forecast", iso="ERCOT", hours=T)
        cls.kwargs = dict(
            T=T,
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
        )

    def _solve(self, adjust):
        return run_energy_solve(
            self.gens,
            self.fa,
            self.demand,
            self.r_mc,
            dict(self.kwargs),
            self.config,
            mc_bid_adjust=adjust,
        )

    def test_p0_bit_identity_and_delad_prices(self):
        leg_a = self._solve(None)
        leg_l = self._solve(self.delta)

        # HP-1 mechanism: the Δmc merge cannot reach P0 — bitwise identical.
        pa, pl = h.p0_hashes(leg_a.r0), h.p0_hashes(leg_l.r0)
        self.assertEqual(pa["composite"], pl["composite"])
        self.assertEqual(h.canon_hash(leg_a.markup), h.canon_hash(leg_l.markup))

        # The de-laddered P1 bid on the sub-slices IS the coarse top block
        # (plus the row's own markup, zero for econ slices by construction).
        tgt = self.map["target_refined"]
        par = self.map["target_parent_coarse"]
        np.testing.assert_allclose(
            leg_l.mc_bid[tgt], self.c_mc[par] + leg_l.markup[tgt], atol=1e-12
        )

        # Price formation: rung 1 marginal -> $38 armed vs $40 de-laddered;
        # rung 3 marginal -> $42 vs $40; ramp body -> $30 in both.
        np.testing.assert_allclose(leg_a.p1.prices[0, :8], 30.0, atol=1e-6)
        np.testing.assert_allclose(leg_l.p1.prices[0, :8], 30.0, atol=1e-6)
        np.testing.assert_allclose(leg_a.p1.prices[0, 8:16], 38.0, atol=1e-6)
        np.testing.assert_allclose(leg_l.p1.prices[0, 8:16], 40.0, atol=1e-6)
        np.testing.assert_allclose(leg_a.p1.prices[0, 16:], 42.0, atol=1e-6)
        np.testing.assert_allclose(leg_l.p1.prices[0, 16:], 40.0, atol=1e-6)

        # Residual-rung-spread disclosure: the keeper leg carries the $4
        # ladder; the de-laddered leg is flat.
        sp_a = h.rung_spread(leg_a.mc_bid, self.map, self.fa.pmax)
        sp_l = h.rung_spread(leg_l.mc_bid, self.map, self.fa.pmax)
        self.assertAlmostEqual(sp_a["max_hourly_spread_usd_mwh"], 4.0)
        self.assertAlmostEqual(sp_l["max_hourly_spread_usd_mwh"], 0.0)


if __name__ == "__main__":
    unittest.main()
