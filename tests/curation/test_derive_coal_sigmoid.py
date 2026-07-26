"""Freeze + provenance tests for scripts/data/derive_coal_sigmoid.py.

Two guarantees (CLAUDE.md rules 23/24 — the sigmoid re-derives only when its
SOURCE DATA updates, and its numbers are registry-resident, reproducible from
that data):

1. FORMULA freeze — on a tiny synthetic fixture, the derive reproduces the
   documented closed form (gas_mid = deliv × HR_coal / HR_cc; floor =
   gas_min / gas_mid; ceil = 1.0; single-region slope = baseline). Locks the
   math against silent drift.

2. PROVENANCE freeze — the committed ``COAL_SIGMOID_DEFAULTS[("MISO", …)]``
   literals in ``config/scenarios.py`` are byte-reproducible from the real
   committed #1803 coal-price data + crosswalk. If anyone edits the MISO
   sigmoid literals to chase a residual (instead of re-running the derive on
   updated source data), this fails — that is the honesty gate.
"""

import unittest

import pandas as pd

from market_sim.config.constants import (
    COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU,
    COAL_SIGMOID_BASELINE_SLOPE,
    COAL_SIGMOID_REP_HR_GAS_CC,
)
from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS
from scripts.data import derive_coal_sigmoid as d


class TestFormulaFreeze(unittest.TestCase):
    """The closed-form derivation on a controlled single-region PRB fixture."""

    def setUp(self):
        # One producing region (PRB), two plants, known heat rate.
        self._orig_regions = d._plant_regions
        self._orig_cap = d._plant_capacity_hr
        d._plant_regions = lambda iso: pd.DataFrame(
            {
                "plant_code": [1, 2],
                "region_id": ["PRB", "PRB"],
                "coal_supply_class": ["prb", "prb"],
            }
        )
        d._plant_capacity_hr = lambda iso: pd.DataFrame(
            {"plant_code": [1, 2], "pmax_mw": [500.0, 500.0], "heat_rate": [10.0, 10.0]}
        )
        # f.o.b. SUB = $17.46/ton at 17.46 MMBtu/ton -> exactly $1.00/MMBtu fob.
        self.rank = pd.DataFrame(
            {
                "region_id": ["PRB", "PRB"],
                "coal_rank_id": ["SUB", "SUB"],
                "year": [2023, 2024],
                "price_usd_per_ton": [17.46, 17.46],
            }
        )

    def tearDown(self):
        d._plant_regions = self._orig_regions
        d._plant_capacity_hr = self._orig_cap

    def test_closed_form(self):
        rows = d._derive_iso("ERCOT", self.rank, ppi_cv=0.0)
        prb = next(r for r in rows if r["supply"] == "prb")
        # deliv = fob(1.00) / PRB commodity share(0.42) = 2.381; HR ratio 10/6.7.
        deliv = 1.0 / 0.42
        gas_mid = deliv * 10.0 / COAL_SIGMOID_REP_HR_GAS_CC
        gas_min = COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU["ERCOT"]
        self.assertAlmostEqual(prb["gas_mid"], round(gas_mid, 3), places=3)
        self.assertEqual(prb["ceil"], 1.0)
        self.assertAlmostEqual(prb["floor"], round(gas_min / gas_mid, 3), places=3)
        # Single region + zero PPI -> baseline slope (no manufactured slope).
        self.assertEqual(prb["gas_slope"], COAL_SIGMOID_BASELINE_SLOPE)
        # Follower tier is a strictly-deeper cheap-gas discount.
        foll = next(r for r in rows if r["supply"] == "prb_follower")
        self.assertLess(foll["floor"], prb["floor"])
        self.assertEqual(foll["gas_mid"], prb["gas_mid"])


class TestProvenanceFreeze(unittest.TestCase):
    """The committed MISO literals reproduce from the real #1803 data."""

    def test_miso_defaults_match_derive(self):
        rank = d._rank_price_table()
        ppi_cv = d._ppi_intra_year_cv()
        rows = {r["supply"]: r for r in d._derive_iso("MISO", rank, ppi_cv)}
        for supply in ("prb", "prb_follower", "bituminous"):
            got = COAL_SIGMOID_DEFAULTS[("MISO", supply)]
            want = rows[supply]
            for p in ("floor", "ceil", "gas_mid", "gas_slope"):
                self.assertAlmostEqual(
                    got[p],
                    want[p],
                    places=3,
                    msg=f"MISO {supply} {p}: literal {got[p]} != derived {want[p]} "
                    "— re-run scripts/data/derive_coal_sigmoid.py; do NOT hand-edit "
                    "the literal (rule 23).",
                )

    def test_miso_is_cost_tracking(self):
        # Provenance invariant: MISO coal never bids above full delivered cost.
        for supply in ("prb", "prb_follower", "bituminous"):
            params = COAL_SIGMOID_DEFAULTS[("MISO", supply)]
            self.assertEqual(params["ceil"], 1.0)
            self.assertGreater(params["gas_mid"], 0.0)
            self.assertLessEqual(params["floor"], params["ceil"])

    def test_miso_gas_mid_not_ercot_copy(self):
        # The whole point of #1347: MISO's crossover must no longer be ERCOT's
        # 2.85 byte-copy.
        for supply in ("prb", "prb_follower", "bituminous"):
            self.assertNotAlmostEqual(
                COAL_SIGMOID_DEFAULTS[("MISO", supply)]["gas_mid"], 2.85, places=2
            )


if __name__ == "__main__":
    unittest.main()
