"""Tests for the MISO ASM-MCP nested-cascade correction (xiso-cascade, rule 14 [R-ACCURATE]).

MISO's three generator ancillary MCPs are a nested cumulative cascade —
regulating resources clear spin, spin clears supplemental (BPM-002 product
substitution) — so ``GENREGMCP >= GENSPINMCP >= GENSUPPMCP`` and a reserve MW
earns the cascade TOP, never the SUM of the posted product prices. Two
committed MISO instruments summed them
(``_miso167_summer_scarcity_instrument.py``'s ``asm_sum`` /
``asm_share_of_energy_gap_pct`` and
``_miso171_reserve_product_decomposition.py``'s ``regspin``/``total``),
overstating the published scarce-hour reserve price ~2.5x and the
"share of the energy gap" headline by the same factor (118.8 % -> 47.3 % in
2025). Corrected 2026-09-01; measured and independently reproduced by
``scripts/probes/_xiso1_miso_asm_cascade_check.py``; record:
``docs/FINDING-xiso-cascade-scan-2026-09-01.md`` (the nyiso-166 §2 instrument
rule carried cross-ISO).

These tests pin:

* **The cascade invariant** on every committed MISO-AS MCP year and market at
  cell grain. If this ever fails the products are no longer cumulative and the
  aggregation must be re-derived from the posting convention, not patched
  (the same contract as ``tests/test_nyiso_as_reference_repair.py``).
* **Cascade MAX end-to-end, synthetically** — the repaired constructions in
  both instruments return the top, never the sum, and the retired summed
  fields are gone (rule 23 [R-DELETE]).
* **The CORRECTION keys** in the three committed records stay present and
  self-consistent (the frozen summed fields are never silently re-armed).

The synthetic tests need no committed data and are the standing guard; the
data-backed tests skip when the MISO data profile is not hydrated. Nothing here
solves, scores, or touches the network.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

PROBES = REPO / "scripts" / "probes"
ASDIR = REPO / "data" / "raw" / "MISO-AS"
CAL = REPO / "results" / "calibration"
CORRECTION_KEY = "CORRECTION_2026-09-01_xiso-cascade"

MCP_YEARS = (2023, 2024, 2025, 2026)
_HAVE_MCP = all(
    (ASDIR / f"asm_{m}mcp_zonal_{y}.parquet").exists()
    for y in MCP_YEARS
    for m in ("rt", "da")
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, PROBES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCascadeInvariant(unittest.TestCase):
    """GENREGMCP >= GENSPINMCP >= GENSUPPMCP, cell grain, every committed file."""

    @unittest.skipUnless(_HAVE_MCP, "MISO data profile not hydrated")
    def test_gen_cascade_monotone_everywhere(self):
        chk = _load("_xiso1_miso_asm_cascade_check")
        for year in MCP_YEARS:
            for market in ("da", "rt"):
                rec = chk.stage_a_invariant(year, market, chk.GEN_CASCADE)
                self.assertEqual(
                    rec["n_violations"],
                    0,
                    f"{year} {market}: cascade no longer monotone "
                    f"({rec['n_violations']} of {rec['n_cells']} cells) — the "
                    "posted products are no longer cumulative; re-derive the "
                    "aggregation from the posting convention, do not patch",
                )
                self.assertGreater(rec["n_cells"], 0)


class TestCascadeTopNotSum(unittest.TestCase):
    """The repaired constructions aggregate by per-hour MAX, never SUM."""

    def test_m167_cascade_top_synthetic(self):
        m167 = _load("_miso167_summer_scarcity_instrument")
        frame = pd.DataFrame(
            {
                "GENREGMCP": [100.0, 90.0, 0.0],
                "GENSPINMCP": [100.0, 50.0, 0.0],
                "GENSUPPMCP": [100.0, 25.0, 0.0],
            }
        )
        top = m167.cascade_top(frame, list(frame.columns))
        # All three equal $100 -> $100, never $300; 90/50/25 -> $90, never $165.
        self.assertEqual(list(top), [100.0, 90.0, 0.0])

    def test_m171_cascade_price_stats_synthetic(self):
        m171 = _load("_miso171_reserve_product_decomposition")
        hours = np.array([0, 1])
        series = {
            "reg": np.array([100.0, 90.0]),
            "spin": np.array([100.0, 50.0]),
            "supp": np.array([100.0, 25.0]),
        }
        vals = m171.cascade_price_stats(series, hours)
        self.assertEqual(vals["top"], 95.0)  # mean(100, 90), never mean(300, 165)
        self.assertEqual(vals["sync_only_increment"], 32.5)  # mean(0, 65)
        self.assertNotIn("total", vals)
        self.assertNotIn("regspin", vals)

    def test_summed_fields_deleted_from_instruments(self):
        # Rule 23 [R-DELETE]: the defective aggregations are gone from the
        # live instruments, not kept alongside the corrected ones.
        m167_src = (PROBES / "_miso167_summer_scarcity_instrument.py").read_text()
        self.assertNotIn('df["asm_sum"]', m167_src)
        self.assertNotIn('miso_asm_mcp_sum": float', m167_src)
        m171_src = (PROBES / "_miso171_reserve_product_decomposition.py").read_text()
        self.assertNotIn('vals["total"]', m171_src)
        self.assertNotIn('vals["regspin"]', m171_src)


class TestCommittedCorrections(unittest.TestCase):
    """The three frozen records carry the dated CORRECTION key, self-consistent."""

    RECORDS = (
        "_miso167_summer_scarcity_instrument.json",
        "_miso171_reserve_product_decomposition.json",
        "_miso178_c3a2025_anatomy.json",
    )

    def test_correction_keys_present_and_first(self):
        for name in self.RECORDS:
            d = json.loads((CAL / name).read_text())
            self.assertIn(CORRECTION_KEY, d, name)
            self.assertEqual(next(iter(d)), CORRECTION_KEY, name)
            self.assertIn("statement", d[CORRECTION_KEY], name)

    def test_m167_correction_matches_frozen_by_product(self):
        # top == GENREGMCP on the committed data, so the corrected value must
        # equal the record's own (untouched) per-product field.
        d = json.loads((CAL / self.RECORDS[0]).read_text())
        for year, corr in d[CORRECTION_KEY]["corrected"].items():
            frozen = d[year]["reserves"]["summer_scarce"]
            self.assertAlmostEqual(
                corr["summer_scarce_miso_asm_mcp_top"],
                frozen["miso_asm_by_product"]["GENREGMCP"],
                places=2,
                msg=year,
            )
            self.assertAlmostEqual(
                corr["was_sum"], frozen["miso_asm_mcp_sum"], places=2, msg=year
            )

    def test_m171_correction_covers_every_summed_field(self):
        d = json.loads((CAL / self.RECORDS[1]).read_text())
        corr = d[CORRECTION_KEY]["corrected"]
        for block in (
            "stage4_published_mcp_by_product",
            "stage4_published_mcp_by_product_rt200",
        ):
            frozen = d["years"]["2025"][block]
            for label in ("scarce47", "da_foreseen", "rt_only"):
                for market in ("rt_mcp", "da_mcp"):
                    c = corr[block][label][market]
                    f = frozen[label][market]
                    self.assertAlmostEqual(c["was_total"], f["total"], places=2)
                    # The correction is the frozen record's own reg mean (top ==
                    # GENREGMCP in every hour of these sets, probe-verified).
                    self.assertAlmostEqual(c["top"], f["reg"], places=2)
                    self.assertLess(c["top"], f["total"] + 1e-9)


if __name__ == "__main__":
    unittest.main()
