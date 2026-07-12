"""Validation of the ERCOT G-22 conditional-offer-distribution LOW leg.

Covers :func:`market_sim.data.fleet.build_ercot_offer_surface_lowcurve_markdown`
— the P1-only additive MARKDOWN that reprices the gas committed (LSL) tranches
and lower econ-ramp rungs to the measured net-load-binned lower-tail quantile
ladders (the trough-price-formation mirror of the adopted top surface).
Contract:

* flag off / non-ERCOT ⇒ ``None`` (byte-identical P1 — rules 14/26);
* only gas ``committed``/econ-ramp rows move, never peak rungs / other classes
  (rule 19 — disjoint with the top leg by construction);
* the ratio is clamped <= 1: a row whose baked multiplier already sits at or
  below the measured value is byte-identical (the markdown can only lower);
* condition-responsive: the committed markdown deepens with the net-load bin
  (the measured LSL bids fall in tight bins);
* rows rank-mapped past the ladder's top quantile are untouched (the upper
  half of the band belongs to the top leg);
* the repriced energy part is floored at $1/MWh;
* a config/JSON bin-edge disagreement fails loudly.
"""

import json
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import build_ercot_offer_surface_lowcurve_markdown


def _gen(uid: str, group: str):
    return types.SimpleNamespace(unit_id=uid, plant_group=group, efficiency_bin=group)


BASE_HR = 8.0  # measured class divisor recorded in the JSON


def _surface_json(path: Path, edges=(0.8, 0.9, 0.97)) -> None:
    # 4 bins. Committed ladder (p25/p50/p75) falls with tightness (measured LSL
    # stay-on bidding); low-body ladder (p10/p25/p50) is bin-stable and cheap.
    def committed(scale):
        return [[0.25, 0.30 * scale], [0.50, 0.55 * scale], [0.75, 1.20 * scale]]

    low_body = [[0.10, 0.65], [0.25, 0.84], [0.50, 0.96]]
    payload = {
        "_provenance": {"netload_pct_edges": list(edges)},
        "CC_REGULAR": {
            "base_hr": BASE_HR,
            "binned_committed": [
                committed(1.0),
                committed(0.7),
                committed(0.5),
                committed(0.25),
            ],
            "binned_low_ladder": [low_body] * 4,
        },
    }
    path.write_text(json.dumps(payload))


class TestLowcurveOfferSurface(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.jpath = Path(self.tmp.name) / "lowcurve.json"
        _surface_json(self.jpath)
        # Two CC plants: committed rows at multiplier 1.0 (hr = BASE_HR), a
        # cheap and an expensive econ rung, a peak rung (untouched), plus an
        # unpriced-class row.
        self.gens = [
            _gen("P1_committed", "CC_REGULAR"),  # rank ~0.25 of committed cap
            _gen("P2_committed", "CC_REGULAR"),  # rank ~0.75
            _gen("P1_econc00", "CC_REGULAR"),  # cheap econ rung (below measured)
            _gen("P1_econc05", "CC_REGULAR"),  # expensive econ rung, rank <= 0.5
            _gen("P2_econc07", "CC_REGULAR"),  # top-ranked econ rung (> p50) untouched
            _gen("P1_peak", "CC_REGULAR"),  # top leg's row, untouched here
            _gen("P3_committed", "CT_CHP"),  # class not priced, untouched
        ]
        self.T = 100
        self.fa = types.SimpleNamespace(
            heat_rate=np.array(
                [
                    BASE_HR * 1.0,  # P1_committed (mult 1.0 > measured 0.30-0.55)
                    BASE_HR * 1.0,  # P2_committed
                    BASE_HR * 0.60,  # P1_econc00 (mult .60 < measured p10 .65)
                    BASE_HR * 1.20,  # P1_econc05 (mult 1.20 > measured)
                    BASE_HR * 1.40,  # P2_econc07 (ranked past p50 -> untouched)
                    BASE_HR * 4.0,  # P1_peak
                    BASE_HR * 1.0,  # P3_committed (CT_CHP)
                ]
            ),
            pmax=np.array([100.0, 100.0, 50.0, 50.0, 60.0, 40.0, 80.0]),
        )
        self.fuel = np.full((7, self.T), 3.0)
        self.net = np.arange(self.T, dtype=float)  # rising -> hour 99 tightest
        self.cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_offer_surface_lowcurve=True,
            ercot_offer_surface_lowcurve_path=str(self.jpath),
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _markdown(self, cfg=None):
        return build_ercot_offer_surface_lowcurve_markdown(
            self.fa, self.gens, self.fuel, self.net, cfg or self.cfg
        )

    def test_flag_off_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(ercot_offer_surface_lowcurve=False)
        self.assertIsNone(self._markdown(cfg))

    def test_non_ercot_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(iso="PJM")
        self.assertIsNone(self._markdown(cfg))

    def test_only_committed_and_low_econ_rows_move(self) -> None:
        md = self._markdown()
        self.assertIsNotNone(md)
        self.assertTrue(np.all(md <= 0.0))  # a markdown can only lower
        # committed rows move (measured LSL below the model band)
        self.assertTrue(np.any(md[0] < 0.0))
        self.assertTrue(np.any(md[1] < 0.0))
        # the expensive in-scope econ rung moves
        self.assertTrue(np.any(md[3] < 0.0))
        # the cheap econ rung is already below the measured value -> clamped
        self.assertTrue(np.all(md[2] == 0.0))
        # the top-ranked econ rung (past the ladder's p50) is untouched
        self.assertTrue(np.all(md[4] == 0.0))
        # peak rung and other-class rows never move (rule 19 disjointness)
        self.assertTrue(np.all(md[5] == 0.0))
        self.assertTrue(np.all(md[6] == 0.0))

    def test_condition_responsive_committed(self) -> None:
        md = self._markdown()
        # committed markdown deepens with tightness: hour 0 (bin 0) shallower
        # than hour 99 (tightest bin) on the same row.
        self.assertLess(md[0, 99], md[0, 0])
        self.assertLess(md[0, 0], 0.0)

    def test_rank_heterogeneity_preserved(self) -> None:
        md = self._markdown()
        # equal-multiplier committed rows split by rank: the lower-ranked row
        # (P1, pos ~0.25) reprices to the p25 value, deeper than P2 (pos ~0.75
        # -> p75 value 1.20, clamped to no-op in bin 0).
        self.assertLess(md[0, 0], md[1, 0])
        self.assertEqual(md[1, 0], 0.0)  # p75 measured 1.20 >= mult 1.0 -> clamp

    def test_energy_floor_one_dollar(self) -> None:
        md = self._markdown()
        energy = self.fa.heat_rate[:, None] * self.fuel
        repriced = energy + md
        self.assertTrue(np.all(repriced[md < 0.0] >= 1.0 - 1e-9))

    def test_edge_mismatch_raises(self) -> None:
        _surface_json(self.jpath, edges=(0.5, 0.9, 0.97))
        with self.assertRaises(ValueError):
            self._markdown()


if __name__ == "__main__":
    unittest.main()
