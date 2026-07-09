"""Validation of the ERCOT G-22 §8 heterogeneity-preserving conditional offer surface.

Covers :func:`market_sim.data.fleet.build_ercot_offer_surface_conditional_markup`
— the P1-only additive markup that reprices the gas peak-band UPPER rungs to the
measured net-load-binned wall in anticipated-tight hours (design:
``docs/FINDING-ercot-priceshape-2026-07.md`` §5.1 / conclusion #1). Contract:

* flag off / non-ERCOT ⇒ ``None`` (byte-identical P1 — rules 14/26);
* only gas peak-rung rows (``peak``/``peakN``) move, never other tranches/classes;
* the lower rungs (measured multiplier <= the resolved peak) stay at the resolved
  peak (ratio clamped >= 1) so the loose stack is byte-identical — heterogeneity
  preserved; only the upper rungs reach the wall;
* the wall is condition-responsive: markup rises with the net-load bin;
* the repriced offer never reaches VOLL (``ercot_offer_surface_price_cap_frac``);
* a config/JSON bin-edge disagreement fails loudly.
"""

import json
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import build_ercot_offer_surface_conditional_markup


def _gen(uid: str, group: str):
    return types.SimpleNamespace(unit_id=uid, plant_group=group, efficiency_bin=group)


# One CC plant split into 5 flat peak rungs (the backcast-config no-op), plus a
# committed row (scaffolding) and a CT plant of another class.
PEAK = 4.0  # resolved peak multiplier the rungs were built at
BASE_HR = 8.0


def _surface_json(path: Path, edges=(0.8, 0.9, 0.97)) -> None:
    # 4 bins; lower 3 rungs at/below PEAK (=> clamp to no-op), upper 2 rungs rise
    # with tightness. Values are heat-rate multipliers on BASE_HR.
    def ladder(top):
        return [[0.2, 2.0], [0.2, 3.0], [0.2, 4.0], [0.2, top / 2.0], [0.2, top]]

    payload = {
        "_provenance": {"netload_pct_edges": list(edges)},
        "CC_REGULAR": {
            "base_hr": BASE_HR,
            "peak_p50": 4.0,
            "binned_ladder": [ladder(10.0), ladder(20.0), ladder(40.0), ladder(80.0)],
        },
    }
    path.write_text(json.dumps(payload))


class TestConditionalOfferSurface(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.jpath = Path(self.tmp.name) / "surf.json"
        _surface_json(self.jpath)
        self.gens = [
            _gen("P1_peak", "CC_REGULAR"),
            _gen("P1_peak2", "CC_REGULAR"),
            _gen("P1_peak3", "CC_REGULAR"),
            _gen("P1_peak4", "CC_REGULAR"),
            _gen("P1_peak5", "CC_REGULAR"),
            _gen("P1_committed", "CC_REGULAR"),  # scaffolding, untouched
            _gen("P2_peak", "CT_CHP"),  # class not priced, untouched
        ]
        self.T = 100
        # peak rung heat_rate == BASE_HR * resolved_peak; committed/other arbitrary
        rung_hr = BASE_HR * PEAK
        self.fa = types.SimpleNamespace(
            heat_rate=np.array([rung_hr] * 5 + [BASE_HR, BASE_HR])
        )
        self.fuel = np.full((7, self.T), 3.0)
        self.net = np.arange(self.T, dtype=float)  # strictly rising -> hour 99 tightest
        self.cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_offer_surface_conditional=True,
            ercot_offer_surface_binned_path=str(self.jpath),
            offer_curve_by_group={
                "CC_REGULAR": {"peak": PEAK, "peak_ladder": [[0.2, PEAK]] * 5}
            },
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _markup(self, cfg=None):
        return build_ercot_offer_surface_conditional_markup(
            self.fa, self.gens, self.fuel, self.net, cfg or self.cfg
        )

    def test_flag_off_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(ercot_offer_surface_conditional=False)
        self.assertIsNone(self._markup(cfg))

    def test_non_ercot_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(iso="PJM")
        self.assertIsNone(self._markup(cfg))

    def test_only_upper_peak_rungs_move(self) -> None:
        m = self._markup()
        self.assertIsNotNone(m)
        # committed (row 5) and other-class peak (row 6) never move.
        self.assertTrue(np.all(m[5] == 0.0))
        self.assertTrue(np.all(m[6] == 0.0))
        # lower 3 rungs (mult <= resolved peak 4.0) clamp to no-op everywhere.
        self.assertTrue(np.all(m[0] == 0.0))
        self.assertTrue(np.all(m[1] == 0.0))
        self.assertTrue(np.all(m[2] == 0.0))
        # upper 2 rungs (rows 3,4) are positive in the tightest hour.
        self.assertGreater(m[3, 99], 0.0)
        self.assertGreater(m[4, 99], m[3, 99])

    def test_condition_responsive(self) -> None:
        m = self._markup()
        # top rung markup rises monotonically across the 4 net-load bins.
        # bins on rising net-load: hours ~0 (bin0), ~85 (bin1), ~95 (bin2), 99 (bin3)
        vals = [m[4, 0], m[4, 85], m[4, 95], m[4, 99]]
        self.assertTrue(all(vals[i] <= vals[i + 1] for i in range(3)), vals)

    def test_price_cap_below_voll(self) -> None:
        m = self._markup()
        # repriced offer = rung fuel MC + markup must stay < price_cap_frac * VOLL.
        cap = self.cfg.ercot_offer_surface_price_cap_frac * self.cfg.voll
        priced = self.fa.heat_rate[:5, None] * self.fuel[:5] + m[:5]
        self.assertLessEqual(float(priced.max()), cap + 1e-6)

    def test_min_bin_gates_mild_hours(self) -> None:
        cfg = self.cfg.with_overrides(ercot_offer_surface_min_bin=3)
        m = build_ercot_offer_surface_conditional_markup(
            self.fa, self.gens, self.fuel, self.net, cfg
        )
        # only the tightest bin (hour 99) reprices; a bin-2 hour (~95) is inert.
        self.assertEqual(float(m[4, 95]), 0.0)
        self.assertGreater(m[4, 99], 0.0)

    def test_edge_mismatch_raises(self) -> None:
        cfg = self.cfg.with_overrides(ercot_offer_surface_netload_pcts=(0.5, 0.9, 0.97))
        with self.assertRaises(ValueError):
            self._markup(cfg)


if __name__ == "__main__":
    unittest.main()
