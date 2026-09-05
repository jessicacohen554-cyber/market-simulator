"""Reconciliation + provenance tests for
``scripts/data/derive_miso_adequacy_accounting_ratio.py`` (capx D51).

Three guarantees (CLAUDE.md rules 21/23/24 — the ratio is an accounting
identity over committed operands, re-derived only when a source or the
fleet's posture changes, and registry-resident):

1. D31 REPRODUCTION — the derive rebuilds D31's own denominators
   (143,822.1 / 143,749.5) from the committed D27 ledgers to the decimal and
   its D31 ratio equals ``ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO``.
   The known-answer check on the method.
2. THE ONE TERM MOVED is the dated channel and nothing else — the D27 − D46
   per-fuel difference equals the D46 ledgers' own step-1b rows (pre-start
   backlog + announced drops + announced derates, fossil only; the non-fossil
   announced channel is identical in both).
3. PROVENANCE FREEZE — ``ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_
   BY_ISO["MISO"]`` equals the derivation. Editing the literal to chase a
   residual (instead of re-running the derive on updated sources) fails here —
   the honesty gate.

Skips cleanly when the committed bundles or the raw PRA rows are absent
(a ``code``-profile checkout without ``results/`` or ``data/raw``).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from market_sim.config.constants import (
    ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO,
    ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO,
    EFORD,
)
from scripts.data import derive_miso_adequacy_accounting_ratio as d

REPO = Path(__file__).resolve().parents[2]
_RAW_CSV = (
    REPO / "data" / "raw" / "capacity-market" / "auction-supply" / "miso" / "miso.csv"
)


def _inputs_present() -> bool:
    try:
        return (
            _RAW_CSV.exists()
            and (d._ledger_dir(d.D27_BUNDLE) / "evolution_2024.json").exists()
            and (d._ledger_dir(d.D46_BUNDLE) / "evolution_2024.json").exists()
        )
    except FileNotFoundError:
        return False


@unittest.skipUnless(_inputs_present(), "committed D27/D46 ledgers or PRA rows absent")
class TestDeriveMisoAdequacyAccountingRatio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = d.derive()
        cls.rows = {r["fleet_year"]: r for r in cls.out["rows"]}

    def test_d31_denominators_and_ratio_reproduce_exactly(self):
        # D31 §2 cites 143,822.1 (2023) / 143,749.5 (2024) — the ledgers give
        # them back to the decimal, and the combined ratio IS the registry.
        self.assertAlmostEqual(
            self.rows[2023]["d31_denominator_mw"], 143_822.1, places=1
        )
        self.assertAlmostEqual(
            self.rows[2024]["d31_denominator_mw"], 143_749.5, places=1
        )
        self.assertAlmostEqual(
            self.out["ratio_d31"],
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"],
            places=6,
        )

    def test_numerators_are_the_committed_pra_rows(self):
        self.assertEqual(self.rows[2023]["offered_generation_mw"], 122_375.6)
        self.assertEqual(self.rows[2024]["offered_generation_mw"], 123_395.6)

    def test_the_moved_term_is_exactly_the_dated_channel(self):
        # D27 − D46 per fuel == the D46 ledgers' own dated-channel rows:
        # 2021 base-fleet backlog (D27 − D46 at 2021 entering) + cumulative
        # fossil announced drops + announced derates through the prior year.
        backlog = {
            f: d.load_ledger(d.D27_BUNDLE, 2021)["fleet_by_fuel_before"][f]
            - d.load_ledger(d.D46_BUNDLE, 2021)["fleet_by_fuel_before"][f]
            for f in EFORD
            if f in d.load_ledger(d.D27_BUNDLE, 2021)["fleet_by_fuel_before"]
        }
        fossil = {"coal", "gas_cc", "gas_ct", "gas_st", "oil"}
        for year, upto in ((2023, (2022,)), (2024, (2022, 2023))):
            expected = dict(backlog)
            for y in upto:
                led = d.load_ledger(d.D46_BUNDLE, y)
                for r in led["retirements"]:
                    if r["reason"] == "announced" and r["fuel"] in fossil:
                        expected[r["fuel"]] = expected.get(r["fuel"], 0.0) + r["mw"]
                for r in led["announced_derates"]:
                    expected[r["fuel"]] = expected.get(r["fuel"], 0.0) + r["derate_mw"]
            got = self.rows[year]["dated_exits_nameplate_by_fuel_mw"]
            for f in fossil | {"nuclear", "biomass"}:
                self.assertAlmostEqual(
                    got.get(f, 0.0), expected.get(f, 0.0), places=1, msg=f"{year} {f}"
                )
        # And the accredited totals the finding quotes.
        self.assertAlmostEqual(
            self.rows[2023]["dated_exits_accredited_mw"], 4_508.5, places=1
        )
        self.assertAlmostEqual(
            self.rows[2024]["dated_exits_accredited_mw"], 7_977.6, places=1
        )

    def test_registry_constant_equals_the_derivation(self):
        self.assertAlmostEqual(
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO["MISO"],
            self.out["ratio_dated_net"],
            places=6,
        )
        # Strictly above D31's and inside the pre-declared STOP band.
        self.assertGreater(self.out["ratio_dated_net"], self.out["ratio_d31"])
        self.assertTrue(0.80 <= self.out["ratio_dated_net"] <= 0.95)

    def test_json_operands_round_trip(self):
        # The --json surface is what the finding's derivation table is built from.
        blob = json.loads(json.dumps(self.out))
        self.assertEqual({r["fleet_year"] for r in blob["rows"]}, {2023, 2024})


if __name__ == "__main__":
    unittest.main()
