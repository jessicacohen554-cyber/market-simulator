"""Validation of the ERCOT G-22 conditional-offer-distribution LOW leg (v2).

Covers :func:`market_sim.data.fleet.build_ercot_offer_surface_lowcurve_markdown`
— the P0-conditioned, P1-only additive MARKDOWN that reprices the gas committed
(LSL) tranches (and, where the measured rel-band medians sit below the model's
ramp, the lower econ rungs) to the measured net-load-binned lower-tail bands —
the trough-price-formation mirror of the adopted top surface. Contract:

* flag off / non-ERCOT ⇒ ``None`` (byte-identical P1 — rules 14/26);
* only gas ``committed``/econ-ramp rows move, never peak rungs / other classes
  (rule 19 — disjoint with the top leg by construction);
* the ratio is clamped <= 1: a class whose resolved committed band already sits
  at or below the measured value is byte-identical (ST_GAS/CT_PEAKER case);
* condition-responsive: the committed markdown deepens with the net-load bin;
* econ rungs positioned past rel 0.67 within their plant are untouched (the
  upper ramp belongs to the top leg);
* the P0 online gate masks the markdown to plant-hours the plant runs in P0;
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
RESOLVED_COMMITTED = 1.0  # the model's resolved committed band multiplier


def _surface_json(path: Path, edges=(0.8, 0.9, 0.97)) -> None:
    # 4 bins. Committed p50 falls with tightness (measured LSL stay-on
    # bidding); the low-body rel-band medians straddle the model ramp so only
    # rungs whose own multiplier exceeds the band value move.
    payload = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "rel_bands": [0.0, 0.22, 0.44, 0.67],
        },
        "CC_REGULAR": {
            "base_hr": BASE_HR,
            "binned_committed_p50": [0.55, 0.40, 0.25, 0.12],
            "binned_low_body": [[0.90, 1.10, 1.30]] * 4,
        },
        "ST_GAS": {
            "base_hr": 11.0,
            # measured LSL at/above the resolved band -> clamp to no-op
            "binned_committed_p50": [1.35, 1.35, 1.5, 1.4],
            "binned_low_body": [[1.0, 1.1, 1.2]] * 4,
        },
    }
    path.write_text(json.dumps(payload))


class TestLowcurveOfferSurface(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.jpath = Path(self.tmp.name) / "lowcurve.json"
        _surface_json(self.jpath)
        # One CC plant (committed + a 4-rung econ ramp + a peak rung), one
        # ST_GAS plant (committed — measured band above resolved, untouched),
        # and an unpriced-class row.
        self.gens = [
            _gen("CC_North_p1_committed", "CC_REGULAR"),  # row 0
            _gen("CC_North_p1_econc00", "CC_REGULAR"),  # row 1: rel .084 band 0
            _gen("CC_North_p1_econc01", "CC_REGULAR"),  # row 2: rel .25  band 1
            _gen("CC_North_p1_econc02", "CC_REGULAR"),  # row 3: rel .42  band 1
            _gen("CC_North_p1_econc03", "CC_REGULAR"),  # row 4: rel .59  band 2
            _gen("CC_North_p1_peak", "CC_REGULAR"),  # row 5: top leg's, untouched
            _gen("ST_South_p2_committed", "ST_GAS"),  # row 6: clamped no-op
            _gen("CT_West_p3_committed", "CT_CHP"),  # row 7: class not priced
        ]
        self.T = 100
        # CC plant base HR = 8.0 (committed row hr = base * resolved 1.0).
        # Econ rungs: mults 0.85 / 1.00 / 1.20 / 1.40 (rows 1-4).
        self.fa = types.SimpleNamespace(
            heat_rate=np.array(
                [
                    8.0,  # committed (mult 1.0)
                    8.0 * 0.85,  # econc00 — band 0 measured .90 > .85 -> no-op
                    8.0 * 1.00,  # econc01 — band 1 measured 1.10 > 1.0 -> no-op
                    8.0 * 1.20,  # econc02 — band 1 measured 1.10 < 1.2 -> markdown
                    8.0 * 1.40,  # econc03 — band 2 measured 1.30 < 1.4 -> markdown
                    8.0 * 4.0,  # peak
                    11.0,  # ST committed (mult 1.0 < measured 1.35)
                    9.0,  # CT_CHP committed
                ]
            ),
            pmax=np.full(8, 100.0),
        )
        self.fuel = np.full((8, self.T), 3.0)
        self.net = np.arange(self.T, dtype=float)  # rising -> hour 99 tightest
        self.cfg = ScenarioConfig(iso="ERCOT").with_overrides(
            ercot_offer_surface_lowcurve=True,
            ercot_offer_surface_lowcurve_path=str(self.jpath),
            offer_curve_by_group={
                "CC_REGULAR": {"committed": RESOLVED_COMMITTED},
                "ST_GAS": {"committed": 1.0},
            },
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _markdown(self, cfg=None, p0=None):
        return build_ercot_offer_surface_lowcurve_markdown(
            self.fa, self.gens, self.fuel, self.net, cfg or self.cfg, p0_dispatch=p0
        )

    def test_flag_off_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(ercot_offer_surface_lowcurve=False)
        self.assertIsNone(self._markdown(cfg))

    def test_non_ercot_returns_none(self) -> None:
        cfg = self.cfg.with_overrides(iso="PJM")
        self.assertIsNone(self._markdown(cfg))

    def test_row_scope_and_clamp(self) -> None:
        md = self._markdown()
        self.assertIsNotNone(md)
        self.assertTrue(np.all(md <= 0.0))  # a markdown can only lower
        # CC committed moves (measured LSL far below the resolved band)
        self.assertTrue(np.any(md[0] < 0.0))
        # econ rungs at/below their measured band value are byte-identical
        self.assertTrue(np.all(md[1] == 0.0))
        self.assertTrue(np.all(md[2] == 0.0))
        # econ rungs above their band value are marked down to it
        self.assertTrue(np.any(md[3] < 0.0))
        self.assertTrue(np.any(md[4] < 0.0))
        # peak rung (top leg), ST committed (measured >= resolved, clamp) and
        # the unpriced class never move
        self.assertTrue(np.all(md[5] == 0.0))
        self.assertTrue(np.all(md[6] == 0.0))
        self.assertTrue(np.all(md[7] == 0.0))

    def test_condition_responsive_committed(self) -> None:
        md = self._markdown()
        # committed markdown deepens with tightness: bin 0 (hour 0) shallower
        # than the tightest bin (hour 99).
        self.assertLess(md[0, 99], md[0, 0])
        self.assertLess(md[0, 0], 0.0)
        # hour 0: ratio .55 -> energy 8*3=24 -> adj = 24*(.55-1) = -10.8
        self.assertAlmostEqual(md[0, 0], 24.0 * (0.55 - 1.0), places=6)

    def test_p0_online_gate(self) -> None:
        # plant p1 offline in P0 for the first 50 hours -> no markdown there.
        p0 = np.ones((8, self.T))
        p0[[0, 1, 2, 3, 4, 5], :50] = 0.0
        md = self._markdown(p0=p0)
        self.assertTrue(np.all(md[0, :50] == 0.0))
        self.assertTrue(np.any(md[0, 50:] < 0.0))

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
