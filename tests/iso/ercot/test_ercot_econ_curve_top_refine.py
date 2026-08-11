"""ercot-188: SCHEME R1, the top-refined econ-curve slicing (``(c2)``).

Pins the construction pre-registered in
``docs/PRECOMMIT-ercot188-cliff-offer-curve-refinement-2026-08-11.md`` §2.2 and
the containment §2.5 that keeps a change on the **ISO-agnostic** assembly path
from re-slicing five other ISOs' fleets (rule 25 ``[R-ISO-SCOPE]``).

What R1 is, exactly: the econ ramp's **top 1/n block re-sliced n ways**, the
body's ``n-1`` blocks left expression-for-expression identical, total curve MW
preserved. At the keeper's ``offer_curve_smoothing_n = 6`` that is 11 slices
whose top block spans 2.778 % of the ramp.

**Rule 23 ``[R-DOF]``: R1 introduces NO new numeric parameter.** The split point
is ``1 - 1/n`` — the boundary the ramp is already sliced at — and the sub-slice
count is ``n``; both are the already-registered ``offer_curve_smoothing_n``.
:meth:`TestR1Geometry.test_shape_is_pinned_to_registered_n_only` is that claim
made executable: change ``n`` and the whole scheme follows it.
"""

import unittest


from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import bins_to_fleet
from market_sim.data.offer_curves import _econ_curve_steps

from tests.unit.data.test_campd_bins import _synthetic_bin

ZONE_NAMES = get_iso_config("ERCOT").zone_names

#: The keeper's offer-curve shape (``ercot185_shapedarm_B.meta.curve_smoothing``).
KEEPER_N = 6
KEEPER_MID = 0.35

_OFFER = {
    "committed": 0.9,
    "econ_low": 1.0,
    "econ_high": 1.3,
    "econ_low_share": 0.5,
    "pct_peaking": 10.0,
}


def _steps(n=KEEPER_N, cap=600.0, top_refine=False, mid=KEEPER_MID):
    return _econ_curve_steps(10.0, 1.0, 1.3, cap, n, 1.0, mid, top_refine=top_refine)


class TestR1Geometry(unittest.TestCase):
    """The slicer's own output, independent of any fleet assembly."""

    def test_default_is_byte_identical_to_the_coarse_form(self):
        # The gate is OFF by default and must change nothing anywhere.
        base = _econ_curve_steps(10.0, 1.0, 1.3, 600.0, KEEPER_N, 1.0, KEEPER_MID)
        self.assertEqual(base, _steps(top_refine=False))

    def test_slice_count_is_2n_minus_1(self):
        self.assertEqual(len(_steps(top_refine=False)), KEEPER_N)
        self.assertEqual(len(_steps(top_refine=True)), 2 * KEEPER_N - 1)

    def test_body_is_byte_identical_and_the_delta_is_confined_to_the_top(self):
        """SP-4: the first n-1 slices move in neither capacity nor heat rate."""
        coarse = _steps(top_refine=False)
        fine = _steps(top_refine=True)
        for k in range(KEEPER_N - 1):
            self.assertEqual(coarse[k][1], fine[k][1], f"slice {k} capacity moved")
            self.assertEqual(coarse[k][2], fine[k][2], f"slice {k} heat rate moved")
        # And the refinement really is a refinement: the top block's sub-slices
        # are strictly finer and strictly dearer than the coarse top slice.
        self.assertLess(fine[KEEPER_N - 1][1], coarse[KEEPER_N - 1][1])
        self.assertGreater(fine[-1][2], coarse[-1][2])

    def test_total_mw_is_preserved(self):
        """SP-3, at the slicer's own grain."""
        coarse = sum(s[1] for s in _steps(top_refine=False))
        fine = sum(s[1] for s in _steps(top_refine=True))
        self.assertAlmostEqual(fine, coarse, delta=1e-9 * coarse)
        self.assertAlmostEqual(fine, 600.0, delta=1e-9 * 600.0)

    def test_top_block_spans_exactly_the_coarse_top_slice(self):
        """The refinement re-slices the top 1/n and nothing below it."""
        fine = _steps(top_refine=True)
        top = fine[KEEPER_N - 1 :]
        self.assertEqual(len(top), KEEPER_N)
        # The top block's MW is exactly the coarse top slice's MW.
        self.assertAlmostEqual(sum(s[1] for s in top), 600.0 / KEEPER_N, places=9)
        # Each sub-slice is 1/n^2 of the ramp — 2.778 % at n = 6, the value
        # MEMO-ercot184 §4.5 costed R1 at.
        self.assertAlmostEqual(top[0][1] / 600.0, 1.0 / KEEPER_N**2, places=12)

    def test_prices_rise_monotonically_across_the_whole_ladder(self):
        # `econc00..econcNN` is an ascending ladder by construction — relied on
        # by legacy_bins._coal_tranche_rank and the offer-surface position read.
        hrs = [s[2] for s in _steps(top_refine=True)]
        self.assertEqual(hrs, sorted(hrs))
        self.assertEqual([s[0] for s in _steps(top_refine=True)][-1], "econc10")

    def test_suffix_ranks_stay_below_econhi(self):
        """The memo §3.3 item 1 latent ceiling: econcNN collides with econhi at NN>=100."""
        from market_sim.data.fleet.legacy_bins import _coal_tranche_rank

        ranks = [_coal_tranche_rank(f"P_{s[0]}") for s in _steps(top_refine=True)]
        self.assertEqual(ranks, sorted(ranks))
        self.assertLess(max(ranks), 3.0)  # econhi

    def test_shape_is_pinned_to_registered_n_only(self):
        """Rule 23: R1 carries no free parameter of its own — it follows ``n``."""
        for n in (4, 6, 8):
            fine = _steps(n=n, top_refine=True)
            self.assertEqual(len(fine), 2 * n - 1)
            self.assertAlmostEqual(fine[-1][1] / 600.0, 1.0 / n**2, places=12)
            body = _steps(n=n, top_refine=False)
            for k in range(n - 1):
                self.assertEqual(body[k], fine[k])

    def test_n_of_one_is_a_no_op(self):
        # Degenerate guard: a single-slice ramp has no top block to refine.
        self.assertEqual(_steps(n=1, top_refine=True), _steps(n=1, top_refine=False))


class TestErcotGate(unittest.TestCase):
    """§2.5 containment: default OFF, ERCOT-gated, committed band never armed."""

    def _fleet(self, iso, armed):
        # The synthetic bin carries an ERCOT zone, so ZONE_NAMES stays ERCOT's
        # for every ISO here: the ONLY thing varying across the loop is
        # ``config.iso``, which is exactly the variable the gate reads. Real
        # per-ISO fleets are covered by the seam proof's SP-2 panel
        # (scripts/probes/ercot188_topfine_seamproof.py), which reconstructs
        # each ISO's own committed bundle.
        config = ScenarioConfig(
            iso=iso,
            offer_curve_by_group={"CC_REGULAR": _OFFER},
            offer_curve_smoothing_n=KEEPER_N,
            offer_curve_smoothing_exp=1.0,
            offer_curve_smoothing_mid=KEEPER_MID,
            ercot_econ_curve_top_refine=armed,
        )
        b = _synthetic_bin(Plant_Group="CC_REGULAR", pct_mr=0, pct_mc=50, pct_peak=15)
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, config)
        return [g for g in fleet if "_econc" in g.unit_id]

    def test_default_off(self):
        self.assertIs(ScenarioConfig().ercot_econ_curve_top_refine, False)

    def test_ercot_armed_refines(self):
        self.assertEqual(len(self._fleet("ERCOT", False)), KEEPER_N)
        self.assertEqual(len(self._fleet("ERCOT", True)), 2 * KEEPER_N - 1)

    def test_non_ercot_is_inert_even_when_set(self):
        """SP-2 in miniature: the gate cannot fire outside ERCOT."""
        for iso in ("CAISO", "PJM", "MISO", "NYISO", "NEISO"):
            off = self._fleet(iso, False)
            on = self._fleet(iso, True)
            self.assertEqual(len(off), len(on), iso)
            self.assertEqual(
                [(g.unit_id, g.pmax_mw, g.heat_rate) for g in off],
                [(g.unit_id, g.pmax_mw, g.heat_rate) for g in on],
                f"{iso} fleet moved with the ERCOT gate armed",
            )

    def test_capacity_preserved_through_assembly(self):
        off = self._fleet("ERCOT", False)
        on = self._fleet("ERCOT", True)
        tot_off = sum(g.pmax_mw for g in off)
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in on), tot_off, delta=1e-9 * tot_off
        )


class TestFeasibilityGuard(unittest.TestCase):
    """Amendment 1: refining a curve must never DELETE capacity from it.

    ``bins_to_fleet`` drops any tranche at or below
    :data:`MIN_TRANCHE_CAPACITY_MW`. R1's sub-slices are ``curve_cap / n**2``,
    so below ``0.5 * n**2`` MW of econ ramp the whole top block would vanish —
    measured on the real ERCOT fleet before the guard: 36 of 144 plant-groups
    truncated and 40.27 MW deleted per year.
    """

    def test_threshold_is_the_assembly_tranche_floor(self):
        from market_sim.data.fleet.assembly import (
            MIN_TRANCHE_CAPACITY_MW,
            _top_refine_ok,
        )

        # Exactly at the floor a sub-slice would be dropped, so R1 is withheld.
        edge = MIN_TRANCHE_CAPACITY_MW * KEEPER_N**2
        self.assertFalse(_top_refine_ok(edge, KEEPER_N, True))
        self.assertTrue(_top_refine_ok(edge * 1.001, KEEPER_N, True))
        self.assertFalse(_top_refine_ok(edge * 0.999, KEEPER_N, True))
        # Disarmed and degenerate cases stay off.
        self.assertFalse(_top_refine_ok(1e6, KEEPER_N, False))
        self.assertFalse(_top_refine_ok(1e6, 1, True))

    def test_small_plant_keeps_the_coarse_form_byte_identically(self):
        from market_sim.data.fleet.assembly import MIN_TRANCHE_CAPACITY_MW

        # An econ ramp under 0.5 * 36 = 18 MW cannot carry R1.
        tiny = MIN_TRANCHE_CAPACITY_MW * KEEPER_N**2 * 0.5

        def build(armed):
            config = ScenarioConfig(
                iso="ERCOT",
                offer_curve_by_group={"CC_REGULAR": _OFFER},
                offer_curve_smoothing_n=KEEPER_N,
                offer_curve_smoothing_exp=1.0,
                offer_curve_smoothing_mid=KEEPER_MID,
                ercot_econ_curve_top_refine=armed,
            )
            # pct_econ is 35 % of capacity_mw, so this sizes the ECON RAMP to
            # `tiny` — half the 18 MW R1 needs at n = 6.
            b = _synthetic_bin(
                Plant_Group="CC_REGULAR",
                pct_mr=0,
                pct_mc=50,
                pct_peak=15,
                capacity_mw=tiny / 0.35,
            )
            fleet, _ = bins_to_fleet(b, ZONE_NAMES, config)
            return [g for g in fleet if "_econc" in g.unit_id]

        off, on = build(False), build(True)
        self.assertEqual(
            [(g.unit_id, g.pmax_mw, g.heat_rate) for g in off],
            [(g.unit_id, g.pmax_mw, g.heat_rate) for g in on],
            "a plant too small for R1 must keep the coarse ramp byte-identically",
        )
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in on), sum(g.pmax_mw for g in off), places=9
        )

    def test_committed_band_never_refined(self):
        """MEMO-ercot184 §6 item 3: the dormant ``committed_ramp_spread`` coupling.

        ``_econ_curve_steps`` is also the committed-band slicer. An ISO that
        later arms ``committed_ramp_spread`` must not silently inherit the
        refinement, so the committed call site passes ``top_refine=False``.
        """
        config = ScenarioConfig(
            iso="ERCOT",
            offer_curve_by_group={"CC_REGULAR": _OFFER},
            offer_curve_smoothing_n=KEEPER_N,
            offer_curve_smoothing_exp=1.0,
            offer_curve_smoothing_mid=KEEPER_MID,
            committed_ramp_spread=0.1,
            ercot_econ_curve_top_refine=True,
        )
        b = _synthetic_bin(Plant_Group="CC_REGULAR", pct_mr=0, pct_mc=50, pct_peak=15)
        fleet, _ = bins_to_fleet(b, ZONE_NAMES, config)
        cmt = [g for g in fleet if "_committed" in g.unit_id]
        self.assertEqual(len(cmt), KEEPER_N)  # NOT 2n-1
        econ = [g for g in fleet if "_econc" in g.unit_id]
        self.assertEqual(len(econ), 2 * KEEPER_N - 1)  # the econ ramp IS refined


class TestCacheKey(unittest.TestCase):
    """SP-7 / rule 24: registered dropped-at-default in BOTH registries."""

    def test_registered_in_both_registries(self):
        from market_sim.config.scenarios import (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
            _CACHE_KEY_OPTIONAL_FIELDS,
        )

        self.assertIn("ercot_econ_curve_top_refine", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["ercot_econ_curve_top_refine"], "False"
        )

    def test_default_key_unmoved_and_armed_key_distinct(self):
        base = ScenarioConfig()
        armed = ScenarioConfig(ercot_econ_curve_top_refine=True)
        off = ScenarioConfig(ercot_econ_curve_top_refine=False)
        self.assertEqual(base.cache_key(), off.cache_key())
        self.assertNotEqual(base.cache_key(), armed.cache_key())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
