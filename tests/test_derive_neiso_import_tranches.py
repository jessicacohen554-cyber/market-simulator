"""Tests for the NEISO measured seam-ladder derivation (audit C-6 closure).

Covers the frozen Q-Q duration-coupling formula on tiny synthetic samples
(trivial cases first, per the testing pattern) and the single-node no-wash
reconciliation, without touching the on-disk measured sources.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data"))

from derive_neiso_import_tranches import (  # noqa: E402
    derive,
    offline_score,
    qq_sink,
    qq_threshold,
)


def _frame(hours: int, da, hqt, nbso, nyis) -> pd.DataFrame:
    """Assemble a joined-frame fixture (EIA sign: negative = import)."""
    return pd.DataFrame(
        {
            "da": np.asarray(da, dtype=float),
            "rt": np.asarray(da, dtype=float),
            "HQT": np.asarray(hqt, dtype=float),
            "NBSO": np.asarray(nbso, dtype=float),
            "NYIS": np.asarray(nyis, dtype=float),
            "NYISO_HQ": np.full(hours, 20.0),
            "NYISO_NPX": np.full(hours, 30.0),
        }
    )


class TestQQCoupling(unittest.TestCase):
    def test_threshold_matches_exceedance_duration(self):
        """24-hour trivial case: flow > level half the time -> median price."""
        price = np.arange(24, dtype=float)  # 0..23
        flow = np.where(price >= 12, 1000.0, 0.0)  # in the money 50% of hours
        thr = qq_threshold(price, flow, 500.0)
        # P(flow > 500) = 0.5 -> the 50th price quantile.
        self.assertAlmostEqual(thr, float(np.quantile(price, 0.5)))

    def test_threshold_never_clears_gives_top_price(self):
        price = np.arange(24, dtype=float)
        flow = np.zeros(24)
        self.assertAlmostEqual(qq_threshold(price, flow, 100.0), 23.0)

    def test_sink_matches_export_duration(self):
        """Exports (flow < -level) 25% of hours -> 25th price quantile."""
        price = np.arange(100, dtype=float)
        flow = np.where(price < 25, -800.0, 200.0)
        thr = qq_sink(price, flow, 400.0)
        self.assertAlmostEqual(thr, float(np.quantile(price, 0.25)))


class TestDerive(unittest.TestCase):
    def test_ladder_shape_and_no_wash_ordering(self):
        """Synthetic year: price-coupled imports on all three seams plus a
        low-price export regime; every sink must clear below every rung."""
        rng = np.random.default_rng(7)
        n = 8760
        da = rng.gamma(4.0, 12.0, n)  # skewed positive price
        # Imports scale with price; exports in the cheapest hours.
        hq = -np.clip((da - 20) * 40, -500, 1800)
        nb = -np.clip((da - 35) * 10, -300, 700)
        ny = -np.clip((da - 30) * 30, -1100, 1600)
        g = _frame(n, da, hq, nb, ny)
        imports, exports, notes = derive(g)

        names = [n_ for n_, _, _ in imports]
        self.assertIn("Highgate", names)
        self.assertIn("HQ_PhaseII", names)
        self.assertIn("NB_north", names)
        self.assertIn("NYISO_CT_base", names)
        self.assertIn("NYISO_CT_peak", names)
        self.assertTrue(all(c > 0 for _, c, _ in imports))
        self.assertTrue(exports, "price-coupled fixture must yield sinks")
        self.assertLess(
            max(p for _, _, p in exports),
            min(p for _, _, p in imports),
            "no-wash ordering: every sink strictly below every import rung",
        )
        # Highgate carve: first rung carries the published 225 MW rating.
        self.assertEqual(imports[0][0], "Highgate")
        self.assertEqual(imports[0][1], 225.0)

    def test_offline_score_recovers_price_coupled_volume(self):
        """A perfectly price-coupled seam is reproduced within a few %."""
        rng = np.random.default_rng(11)
        n = 8760
        da = rng.gamma(4.0, 12.0, n)
        hq = -np.clip((da - 20) * 40, 0, 1800)  # import-only, price-coupled
        nb = np.zeros(n)
        ny = np.zeros(n)
        g = _frame(n, da, hq, nb, ny)
        imports, exports, _ = derive(g)
        s = offline_score(g, imports, exports)
        self.assertLess(abs(s["sim_twh"] - s["act_twh"]) / s["act_twh"], 0.10)
        self.assertGreater(s["hourly_corr"], 0.9)


if __name__ == "__main__":
    unittest.main()
