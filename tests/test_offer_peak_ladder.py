"""Validation of the measured peak-band quantile ladder plumbing.

The ladder (``peak_ladder`` band, ``derive_dam_offer_hrmults.py
--peak-ladder``) rides the ``--offer-curve-json`` channel; the CLI validator
must accept the ``[[capacity_share, multiplier], ...]`` shape and reject
malformed rungs loudly (CLAUDE.md rule 23 — no silently-dead knobs). The
fleet-side tranche split is covered in ``test_campd_bins.py``
(``test_peak_ladder_splits_band_into_quantile_rungs``).
"""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "run_calibration_full", REPO / "scripts" / "run_calibration_full.py"
)
rcf = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("run_calibration_full", rcf)
_spec.loader.exec_module(rcf)


class TestPeakLadderJsonValidation(unittest.TestCase):
    """``_parse_offer_curve_json`` accepts a well-formed ladder, rejects junk."""

    def _parse(self, curve: dict):
        return rcf._parse_offer_curve_json(json.dumps(curve))

    def test_valid_ladder_passes(self):
        curve = {
            "CT_PEAKER": {
                "committed": 1.3,
                "peak": 5.4,
                "peak_ladder": [
                    [0.2, 2.0],
                    [0.2, 3.4],
                    [0.2, 5.4],
                    [0.2, 9.8],
                    [0.2, 124.6],
                ],
            }
        }
        parsed = self._parse(curve)
        self.assertEqual(len(parsed["CT_PEAKER"]["peak_ladder"]), 5)

    def test_shares_must_sum_to_one(self):
        curve = {"CT_PEAKER": {"peak_ladder": [[0.5, 2.0], [0.2, 5.0]]}}
        with self.assertRaises(SystemExit):
            self._parse(curve)

    def test_rungs_must_be_pairs_of_numbers(self):
        for bad in ([[0.5, "x"], [0.5, 2.0]], [[1.0]], "notalist", []):
            with self.assertRaises(SystemExit):
                self._parse({"CT_PEAKER": {"peak_ladder": bad}})

    def test_nonpositive_share_rejected(self):
        curve = {"CT_PEAKER": {"peak_ladder": [[0.0, 2.0], [1.0, 5.0]]}}
        with self.assertRaises(SystemExit):
            self._parse(curve)

    def test_committed_hrmults_json_ladder_is_valid(self):
        # Both committed derive artifacts must always parse via the run path
        # (--offer-curve-json): the keeper-lineage p50 file stays ladder-free,
        # the opt-in ladder variant carries p50-clamped rising rungs.
        vs = REPO / "data" / "raw" / "_validation-source"
        base = rcf._parse_offer_curve_json(str(vs / "offer_curve_dam_hrmults.json"))
        parsed = rcf._parse_offer_curve_json(
            str(vs / "offer_curve_dam_hrmults_ladder.json")
        )
        for group in ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS"):
            self.assertNotIn("peak_ladder", base[group])
            self.assertIn(group, parsed)
            ladder = parsed[group].get("peak_ladder")
            self.assertTrue(ladder and len(ladder) == 5)
            mults = [m for _s, m in ladder]
            self.assertEqual(mults, sorted(mults))  # rising rungs
            # p50-clamped: no rung below the single peak height; p50 preserved
            self.assertGreaterEqual(mults[0], parsed[group]["peak"] - 1e-9)
            self.assertEqual(base[group]["peak"], parsed[group]["peak"])


if __name__ == "__main__":
    unittest.main()
