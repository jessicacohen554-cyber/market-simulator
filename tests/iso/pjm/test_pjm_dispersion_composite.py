"""Regression contract of the pjm-123 dispersion-composite legs 2 and 3.

The composite (docs/FINDING-pjm122-marginal-ownership-2026-07.md §4) re-owns
the $40-150 region the measured corpus assigns to the CC top belt and fast-start
CT. Leg 1 needs no code (the already-landed
``pjm_offer_midcurve_level_segments``); this file is the contract for the two
that do:

* **leg 2** — ``ScenarioConfig.pjm_offer_midcurve_peak_segments``: extends the
  mid-curve targeting to a segment's own ``peak*`` rungs, in LEVEL form, so the
  measured s0.95-0.99 belt lands on the rows the pjm-121 §5 arm excluded.
  Contract: default-off is byte-identical; an armed segment's peak rows are SET
  to the measured level (pulled down from a fitted rung above it, raised from
  one below); the scope is intersected with the floor scope (rule 19); the
  LONG_RUN ``peak`` row keeps its pre-existing floor-form behaviour; arming it
  alongside the pjm-99 top-of-curve surface is rejected at config construction
  (both price the same rows and their markups SUM).
* **leg 3** — ``ScenarioConfig.pjm_ct_measured_max_reprice`` +
  :func:`market_sim.pipeline.solve.apply_bid_max_target`: the measured CT_FAST
  level as a max() against the FULL P1 bid. Contract: the target covers the CT
  econ/peak rows only; the seam is a strict max() that NEVER adds to the
  startup amortization (the pjm-101/102 stacking failure) and is a no-op where
  the model already prices above measured or the corpus has no coverage.

Trivial cases per the repo testing pattern: a handful of tranche rows, 24 hours.
"""

import json
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

import market_sim.data.fuel as fuel_pkg
from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    build_pjm_ct_measured_max_target,
    build_pjm_offer_midcurve_conditional_markup,
)
from market_sim.pipeline.solve import apply_bid_max_target

YEAR = 2025
T = 24  # trivial case: one day
MULT = 2.0  # flat measured multiplier (x delivered gas) across shares and bins


def _gen(uid: str, group: str):
    return types.SimpleNamespace(unit_id=uid, plant_group=group)


def _surface_json(path: Path, mult: float = MULT, segments=("CC_LIKE", "LONG_RUN")):
    """Two net-load bins, two share knots, flat multiplier ``mult``."""
    lad = [[0.25, mult], [0.75, mult]]
    payload = {"_provenance": {"netload_pct_edges": [0.5], "shares": [0.25, 0.75]}}
    for seg in segments:
        payload[seg] = {"years": {str(YEAR): [lad, lad]}}
    path.write_text(json.dumps(payload))


class _SurfaceCase(unittest.TestCase):
    """Shared frozen-surface + constant-gas fixture."""

    SEGMENTS = ("CC_LIKE", "LONG_RUN", "CT_FAST")

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.jpath = tmp / "surf.json"
        _surface_json(self.jpath, segments=self.SEGMENTS)
        # Constant Henry Hub daily series spanning the test day, so the
        # delivered-gas day series is a single known scalar.
        hh = tmp / "hh.csv"
        days = pd.date_range("2024-12-25", "2025-01-05", freq="D")
        pd.DataFrame({"date": days, "price_usd_mmbtu": 3.0}).to_csv(hh, index=False)
        self._hh_orig = fuel_pkg.HENRY_HUB_DAILY_PATH
        fuel_pkg.HENRY_HUB_DAILY_PATH = hh
        self.gas_day = 3.0 + float(GAS_BASIS_DIFFERENTIAL["PJM"])
        self.target = MULT * self.gas_day  # flat measured target, both bins
        self.net = np.arange(T, dtype=float)  # rising net load -> 2 clean bins

    def tearDown(self) -> None:
        fuel_pkg.HENRY_HUB_DAILY_PATH = self._hh_orig
        self.tmp.cleanup()


class TestPjmMidcurvePeakScope(_SurfaceCase):
    """Leg 2 — the measured top belt on the CC/CT ``peak*`` rungs."""

    def setUp(self) -> None:
        super().setUp()
        # One CC plant (committed scaffolding / econ / peak) and one coal
        # plant (econ / peak) — the two segments the keeper floor scopes.
        self.gens = [
            _gen("CCA_committed", "CC_REGULAR"),  # never touched
            _gen("CCA_econ", "CC_REGULAR"),  # CC_LIKE econ row
            _gen("CCA_peak", "CC_REGULAR"),  # CC_LIKE peak row (leg 2)
            _gen("COALA_econ", "COAL_BIT"),  # LONG_RUN econ row
            _gen("COALA_peak", "COAL_BIT"),  # LONG_RUN peak row (pre-existing)
        ]
        self.fa = types.SimpleNamespace(pmax=np.full(5, 100.0))
        # committed / CC econ / CC peak / coal econ / coal peak. The CC peak
        # rung is priced FAR above the measured belt (the model's 31.9 x gas
        # against a measured 11-19 x) — only a level form can pull it down.
        self.mc = np.tile(
            np.array([[5.0], [30.0], [200.0], [1.0], [1.0]]), (1, T)
        ).astype(float)

    def _markup(self, peak_segments, segments=("LONG_RUN", "CC_LIKE"), level=None):
        cfg = ScenarioConfig(iso="PJM").with_overrides(
            pjm_offer_midcurve_conditional=True,
            pjm_offer_midcurve_path=str(self.jpath),
            pjm_offer_midcurve_segments=segments,
            pjm_offer_midcurve_level_segments=level,
            pjm_offer_midcurve_peak_segments=peak_segments,
        )
        return build_pjm_offer_midcurve_conditional_markup(
            self.fa, self.gens, self.mc, self.net, cfg, YEAR
        )

    def test_default_off_is_byte_identical(self) -> None:
        m_none = self._markup(None)
        m_empty = self._markup(())
        self.assertIsNotNone(m_none)
        self.assertTrue(np.array_equal(m_none, m_empty))
        # The CC peak rung is NOT a target without the scope — the over-priced
        # fitted rung survives, which is exactly the pjm-122 §3 hole.
        self.assertTrue(np.all(m_none[2] == 0.0))

    def test_peak_scope_sets_cc_peak_to_measured_level(self) -> None:
        m = self._markup(("CC_LIKE",))
        self.assertIsNotNone(m)
        # LEVEL form: the fitted rung above measured is pulled DOWN onto it.
        self.assertTrue(np.all(m[2] < 0.0))
        self.assertTrue(np.allclose(self.mc[2] + m[2], self.target))
        # The econ rows keep their floor-form behaviour (raise-only).
        self.assertTrue(np.all(m[1] >= 0.0))
        self.assertTrue(np.all(m[3] >= 0.0))
        # Commitment scaffolding is never touched (rule 19).
        self.assertTrue(np.all(m[0] == 0.0))

    def test_peak_scope_still_raises_an_underpriced_peak_rung(self) -> None:
        self.mc[2, :] = 1.0  # fitted rung BELOW the measured belt
        m = self._markup(("CC_LIKE",))
        self.assertIsNotNone(m)
        self.assertTrue(np.all(m[2] > 0.0))
        self.assertTrue(np.allclose(self.mc[2] + m[2], self.target))

    def test_peak_scope_intersected_with_floor_scope(self) -> None:
        # CC_LIKE is peak-listed but NOT floor-scoped: no CC row may be priced
        # by either form (rule 19 — the floor scope owns segment eligibility).
        m = self._markup(("CC_LIKE",), segments=("LONG_RUN",))
        self.assertIsNotNone(m)  # the coal rows keep the surface alive
        self.assertTrue(np.all(m[1] == 0.0))
        self.assertTrue(np.all(m[2] == 0.0))
        self.assertTrue(np.allclose(m[3], self.target - 1.0))

    def test_long_run_peak_row_keeps_floor_form(self) -> None:
        # The LONG_RUN ``peak`` rung has been a floor-form target since
        # pjm-104; arming the CC peak scope must not silently convert it to
        # level form.
        self.mc[4, :] = 500.0  # coal peak far above the measured ceiling
        m = self._markup(("CC_LIKE",))
        self.assertIsNotNone(m)
        self.assertTrue(np.all(m[4] == 0.0))  # raise-only: untouched
        # ... and it DOES convert when LONG_RUN is level-scoped (leg 1).
        m_level = self._markup(("CC_LIKE",), level=("LONG_RUN",))
        self.assertTrue(np.all(m_level[4] < 0.0))
        self.assertTrue(np.allclose(self.mc[4] + m_level[4], self.target))

    def test_rejects_stacking_with_top_of_curve_surface(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ScenarioConfig(iso="PJM").with_overrides(
                pjm_offer_midcurve_conditional=True,
                pjm_offer_midcurve_peak_segments=("CC_LIKE",),
                pjm_offer_surface_conditional=True,
            )
        self.assertIn("rule 19", str(ctx.exception))


class TestPjmCtMeasuredMaxTarget(_SurfaceCase):
    """Leg 3 — the CT_FAST measured level at the max() seam."""

    def setUp(self) -> None:
        super().setUp()
        self.gens = [
            _gen("CTA_committed", "CT_PEAKER"),  # never targeted
            _gen("CTA_econ", "CT_PEAKER"),  # idle-shelf row
            _gen("CTA_peak", "CT_PEAKER"),  # top-of-curve row
            _gen("CCA_econ", "CC_REGULAR"),  # a different segment
        ]
        self.fa = types.SimpleNamespace(pmax=np.full(4, 100.0))
        # The CT econ row is the too-cheap idle shelf (below the measured
        # level); the CT peak row is already priced far above the corpus.
        self.mc = np.tile(np.array([[5.0], [1.0], [200.0], [30.0]]), (1, T)).astype(
            float
        )

    def _cfg(self, **over):
        # mode="backcast": the surface reprices off a MEASURED CT max-offer
        # corpus, a backcast-only overlay (FFR-1D rule-13 guard, audit FR-11).
        return ScenarioConfig(iso="PJM", mode="backcast").with_overrides(
            pjm_ct_measured_max_reprice=True,
            pjm_offer_midcurve_path=str(self.jpath),
            **over,
        )

    def _target(self, cfg=None):
        return build_pjm_ct_measured_max_target(
            self.fa, self.gens, self.mc, self.net, cfg or self._cfg(), YEAR
        )

    def test_gate_off_and_wrong_iso_return_none(self) -> None:
        off = self._cfg().with_overrides(pjm_ct_measured_max_reprice=False)
        self.assertIsNone(self._target(off))
        # A non-PJM ISO never sees the surface (rule 25, no cross-ISO fallback).
        other = self._cfg().with_overrides(iso="ERCOT")
        self.assertIsNone(self._target(other))

    def test_targets_ct_econ_and_peak_rows_only(self) -> None:
        tgt = self._target()
        self.assertIsNotNone(tgt)
        self.assertTrue(np.allclose(tgt[1], self.target))  # CT econ
        self.assertTrue(np.allclose(tgt[2], self.target))  # CT peak
        self.assertTrue(np.all(tgt[0] == 0.0))  # committed scaffolding
        self.assertTrue(np.all(tgt[3] == 0.0))  # CC row is not CT_FAST

    def test_seam_is_a_strict_max_never_additive(self) -> None:
        # The whole point of leg 3 (rule 19): the measured level must never
        # SUM with the startup amortization the CT stack already carries.
        tgt = self._target()
        markup = np.full_like(self.mc, 2.0)  # a stand-in startup amortization
        bid = self.mc + markup
        out = apply_bid_max_target(bid, tgt)
        self.assertTrue(np.all(out >= bid))  # never lowers a bid
        self.assertTrue(np.all(out == np.maximum(bid, np.where(tgt > 0, tgt, -np.inf))))
        # No row-hour is the SUM of the two mechanisms.
        self.assertFalse(np.any(np.isclose(out, bid + tgt) & (tgt > 0.0)))
        # The cheap CT econ row is lifted to the measured level; the expensive
        # CT peak row keeps its amortized bid (the model already prices above
        # the corpus there).
        self.assertTrue(np.allclose(out[1], self.target))
        self.assertTrue(np.allclose(out[2], bid[2]))

    def test_uncovered_entries_are_no_ops(self) -> None:
        bid = self.mc.copy()
        zeros = np.zeros_like(self.mc)
        self.assertTrue(np.array_equal(apply_bid_max_target(bid, zeros), bid))
        nans = np.full_like(self.mc, np.nan)
        self.assertTrue(np.array_equal(apply_bid_max_target(bid, nans), bid))


if __name__ == "__main__":
    unittest.main()
