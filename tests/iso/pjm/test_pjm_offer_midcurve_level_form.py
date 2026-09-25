"""Regression contract of the PJM mid-curve LEVEL-form scope (pjm-121 §5).

Covers the ``ScenarioConfig.pjm_offer_midcurve_level_segments`` branch of
:func:`market_sim.data.fleet.build_pjm_offer_midcurve_conditional_markup` — the
default-off construction that SETS a targeted row's bid to the measured
capacity-share offer level (signed markup) instead of flooring it there
(``max(0, .)``). Refuted as the C3a-2025 dispersion lever
(docs/FINDING-pjm121-ccbelt-c3a-close-2026-07.md §5) but kept as the correct
construction for a fleet whose fitted bands sit BELOW measured. Contract:

* the floor form never lowers a bid (markup >= 0 by construction);
* the level form pulls an over-priced band DOWN to the measured target;
* the level form still raises an under-priced band to the same target;
* the level scope is intersected with the floor scope — a segment absent from
  ``pjm_offer_midcurve_segments`` is never priced by either form (rule 19);
* ``pjm_offer_midcurve_level_segments=None`` (and ``()``) is byte-identical to
  the pure floor form;
* the VOLL cap (0.95 x voll) binds the level bid exactly like the floor bid.

Trivial cases per the repo testing pattern: 3 tranche rows, 24 hours.
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
from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup

YEAR = 2025
T = 24  # trivial case: one day
MULT = 2.0  # flat measured multiplier (x delivered gas) across shares and bins


def _gen(uid: str, group: str):
    return types.SimpleNamespace(unit_id=uid, plant_group=group)


def _surface_json(path: Path, mult: float = MULT) -> None:
    """Two net-load bins, two share knots, flat multiplier ``mult``."""
    lad = [[0.25, mult], [0.75, mult]]
    payload = {
        "_provenance": {"netload_pct_edges": [0.5], "shares": [0.25, 0.75]},
        "CC_LIKE": {"years": {str(YEAR): [lad, lad]}},
        "LONG_RUN": {"years": {str(YEAR): [lad, lad]}},
    }
    path.write_text(json.dumps(payload))


class TestPjmMidcurveLevelForm(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.jpath = tmp / "surf.json"
        _surface_json(self.jpath)
        # Constant Henry Hub daily series spanning the test day, so the
        # delivered-gas day series is a single known scalar.
        hh = tmp / "hh.csv"
        days = pd.date_range("2024-12-25", "2025-01-05", freq="D")
        pd.DataFrame({"date": days, "price_usd_mmbtu": 3.0}).to_csv(hh, index=False)
        self._hh_orig = fuel_pkg.HENRY_HUB_DAILY_PATH
        fuel_pkg.HENRY_HUB_DAILY_PATH = hh
        self.gas_day = 3.0 + float(GAS_BASIS_DIFFERENTIAL["PJM"])
        self.target = MULT * self.gas_day  # flat measured target, both bins

        # One CC plant (committed scaffolding + econ) and one coal econ row.
        self.gens = [
            _gen("CCA_committed", "CC_REGULAR"),  # never touched
            _gen("CCA_econ", "CC_REGULAR"),  # CC_LIKE target row
            _gen("COALA_econ", "COAL_BIT"),  # LONG_RUN target row
        ]
        self.fa = types.SimpleNamespace(pmax=np.array([100.0, 100.0, 100.0]))
        self.net = np.arange(T, dtype=float)  # rising net load -> 2 clean bins

    def tearDown(self) -> None:
        fuel_pkg.HENRY_HUB_DAILY_PATH = self._hh_orig
        self.tmp.cleanup()

    def _cfg(self, segments, level, **over):
        return ScenarioConfig(iso="PJM").with_overrides(
            pjm_offer_midcurve_conditional=True,
            pjm_offer_midcurve_path=str(self.jpath),
            pjm_offer_midcurve_segments=segments,
            pjm_offer_midcurve_level_segments=level,
            **over,
        )

    def _markup(self, mc_econ: float, segments, level, coal_mc: float = 1.0, cfg=None):
        mc = np.tile(
            np.array([[5.0], [mc_econ], [coal_mc]]), (1, T)
        )  # committed / CC econ / coal econ
        m = build_pjm_offer_midcurve_conditional_markup(
            self.fa,
            self.gens,
            mc,
            self.net,
            cfg or self._cfg(segments, level),
            YEAR,
        )
        return mc, m

    def test_floor_never_lowers_a_bid(self) -> None:
        # CC econ priced ABOVE the target: the floor form leaves it alone;
        # markups are non-negative everywhere.
        mc, m = self._markup(100.0, ("LONG_RUN", "CC_LIKE"), None)
        self.assertIsNotNone(m)
        self.assertTrue(np.all(m >= 0.0))
        self.assertTrue(np.all(m[1] == 0.0))  # over-priced band untouched
        self.assertTrue(np.allclose(m[2], self.target - 1.0))  # coal floored up
        self.assertTrue(np.all(m[0] == 0.0))  # committed scaffolding untouched

    def test_level_pulls_overpriced_band_down(self) -> None:
        mc, m = self._markup(100.0, ("LONG_RUN", "CC_LIKE"), ("CC_LIKE",))
        self.assertIsNotNone(m)
        self.assertTrue(np.all(m[1] < 0.0))  # signed markup lowers the band
        self.assertTrue(np.allclose(mc[1] + m[1], self.target))  # bid == target
        self.assertTrue(np.allclose(m[2], self.target - 1.0))  # floor row intact
        self.assertTrue(np.all(m[0] == 0.0))

    def test_level_still_raises_underpriced_band(self) -> None:
        mc, m = self._markup(1.0, ("LONG_RUN", "CC_LIKE"), ("CC_LIKE",))
        self.assertIsNotNone(m)
        self.assertTrue(np.all(m[1] > 0.0))
        self.assertTrue(np.allclose(mc[1] + m[1], self.target))  # same target

    def test_level_scope_intersected_with_floor_scope(self) -> None:
        # CC_LIKE is level-listed but NOT floor-scoped: it must not be priced
        # by either form (rule 19 — the floor scope owns segment eligibility).
        mc, m = self._markup(100.0, ("LONG_RUN",), ("CC_LIKE",))
        self.assertIsNotNone(m)  # coal floor row keeps the surface alive
        self.assertTrue(np.all(m[1] == 0.0))  # over-priced CC NOT pulled down
        self.assertTrue(np.allclose(m[2], self.target - 1.0))

    def test_level_none_byte_identical_to_floor_form(self) -> None:
        _, m_none = self._markup(100.0, ("LONG_RUN", "CC_LIKE"), None)
        _, m_empty = self._markup(100.0, ("LONG_RUN", "CC_LIKE"), ())
        self.assertIsNotNone(m_none)
        self.assertIsNotNone(m_empty)
        self.assertTrue(np.array_equal(m_none, m_empty))
        # Explicit floor-form expectation: max(0, target - mc) per row.
        self.assertTrue(np.all(m_none[1] == 0.0))
        self.assertTrue(np.allclose(m_none[2], self.target - 1.0))

    def test_voll_cap_holds(self) -> None:
        # A huge measured multiplier drives the target above 0.95 x VOLL; both
        # forms cap the resulting bid there.
        big = Path(self.tmp.name) / "surf_big.json"
        _surface_json(big, mult=1e4)
        cfg = self._cfg(("LONG_RUN", "CC_LIKE"), ("CC_LIKE",)).with_overrides(
            pjm_offer_midcurve_path=str(big)
        )
        mc, m = self._markup(100.0, None, None, cfg=cfg)
        self.assertIsNotNone(m)
        voll_cap = 0.95 * ScenarioConfig(iso="PJM").voll
        self.assertLess(voll_cap, 1e4 * self.gas_day)  # the cap actually binds
        self.assertTrue(np.allclose(mc[1] + m[1], voll_cap))  # level bid capped
        self.assertTrue(np.allclose(mc[2] + m[2], voll_cap))  # floor bid capped


if __name__ == "__main__":
    unittest.main()
