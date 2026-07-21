"""Trivial (no-solve) tests for the hardened CES leg harness ``run_ces_leg.py``.

FF-3F: the premium ladder is a config LIST expanded through
``matrix_configs`` (campaign-is-data), each leg its own invocation. These tests
exercise the harness plumbing — ladder expansion, leg-provenance metadata,
fail-loud case selection, and cache-only bundle assembly — with NO LP solve
(CLAUDE.md testing pattern). The actual T1 solve lives in the session run, not
the suite.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import run_ces_leg as L

REPO = Path(__file__).resolve().parent.parent
BASE_CONFIG = REPO / "configs" / "scenarios" / "ercot_ces_poc_2026_2030.yaml"
POC_MATRIX = REPO / "configs" / "ces_premium_matrix_poc.yaml"


class TestLadderExpansion(unittest.TestCase):
    """The campaign-is-data seam: matrix YAML → {case: config}."""

    def test_poc_ladder_three_cases(self) -> None:
        base, configs, iso = L._load_ladder(BASE_CONFIG, POC_MATRIX, None)
        self.assertEqual(iso, "ERCOT")
        self.assertEqual(list(configs), ["BAU", "CES-20", "CES-40"])
        # Each leg is a distinct config (distinct cache key) over the same window.
        keys = {c: cfg.cache_key() for c, cfg in configs.items()}
        self.assertEqual(len(set(keys.values())), 3)
        for cfg in configs.values():
            self.assertEqual((cfg.start_year, cfg.end_year), (2026, 2030))

    def test_iso_override(self) -> None:
        _, _, iso = L._load_ladder(BASE_CONFIG, POC_MATRIX, "ercot")
        self.assertEqual(iso, "ERCOT")


class TestLegMeta(unittest.TestCase):
    """The CES-provenance block that rides into the summary + sidecar."""

    def test_bau_is_zero_premium_disabled(self) -> None:
        _, configs, _ = L._load_ladder(BASE_CONFIG, POC_MATRIX, None)
        meta = L._leg_meta("BAU", configs["BAU"], "camp")
        self.assertFalse(meta["federal_ces_enabled"])
        self.assertEqual(meta["premium_usd_per_mwh"], 0.0)
        self.assertEqual(meta["campaign"], "camp")

    def test_ces20_carries_premium(self) -> None:
        _, configs, _ = L._load_ladder(BASE_CONFIG, POC_MATRIX, None)
        meta = L._leg_meta("CES-20", configs["CES-20"], "camp")
        self.assertTrue(meta["federal_ces_enabled"])
        self.assertEqual(meta["premium_usd_per_mwh"], 20.0)


class TestFailLoud(unittest.TestCase):
    """A bad case name is refused before any solve (rules 5/13)."""

    def test_unknown_case_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(SystemExit) as ctx:
                L.run_leg(
                    BASE_CONFIG,
                    POC_MATRIX,
                    "CES-99",
                    Path(td),
                    None,
                    False,
                    0.5,
                    None,
                )
            self.assertIn("CES-99", str(ctx.exception))


class TestAssembleBundle(unittest.TestCase):
    """Assembly reads the REAL solved key from each leg summary (no recompute).

    The runner resolves the policy bundle + ISO overrides before hashing the
    config, so ``config.cache_key()`` in a fresh process does not reproduce the
    solved key — assembly must read it from the leg's summary. These synthetic
    summaries stand in for solved legs (no LP).
    """

    def _write_leg(self, legs_dir: Path, case: str, key: str) -> None:
        d = legs_dir / case
        d.mkdir(parents=True)
        (d / "full_horizon_summary.json").write_text(
            json.dumps({"iso": "ERCOT", "case": case, "cache_key": key})
        )

    def test_meta_maps_case_to_recorded_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            legs = Path(td) / "legs"
            # Keys deliberately unlike config.cache_key() — proves we read the
            # summary, not recompute.
            self._write_leg(legs, "BAU", "realkeyBAU00")
            self._write_leg(legs, "CES-20", "realkeyCES20")
            self._write_leg(legs, "CES-40", "realkeyCES40")
            out = Path(td) / "bundle"
            L.assemble_bundle(BASE_CONFIG, POC_MATRIX, out, None, legs)
            meta = json.loads((out / "meta.json").read_text())
            self.assertEqual(meta["iso"], "ERCOT")
            self.assertEqual(
                meta["cases"],
                {
                    "BAU": "realkeyBAU00",
                    "CES-20": "realkeyCES20",
                    "CES-40": "realkeyCES40",
                },
            )

    def test_no_summaries_is_fail_loud(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            legs = Path(td) / "empty"
            legs.mkdir()
            with self.assertRaises(SystemExit):
                L.assemble_bundle(BASE_CONFIG, POC_MATRIX, Path(td) / "b", None, legs)


if __name__ == "__main__":
    unittest.main()
