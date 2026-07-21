"""Trivial fresh-checkout tests for ``scripts/generate_financial_reports.py``.

FF-3B finding F-3: the script was not runnable on a fresh checkout because
``--eia860-path`` / ``--ownership-map`` were required and pointed at a
hand-laid ``data/fleet/*.xlsx`` layout that a fresh clone does not have.
FF-3F makes both inputs resolve through the on-disk path registry by default,
fail-loud on absence. These tests exercise the resolvers only — NO LP solve
(CLAUDE.md testing pattern: trivial cases first) — so they prove the
fresh-checkout path without a multi-minute dispatch run.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from market_sim.config.paths import active_eia860_dir
from scripts import generate_financial_reports as G


class TestParseYears(unittest.TestCase):
    """The shared ``2026-2030`` / ``2026,2030`` year-spec parser."""

    def test_range_form(self) -> None:
        self.assertEqual(G._parse_years("2026-2030"), [2026, 2027, 2028, 2029, 2030])

    def test_comma_form(self) -> None:
        self.assertEqual(G._parse_years("2026,2030"), [2026, 2030])


class TestRequireInput(unittest.TestCase):
    """The fail-loud input guard (rules 5/13 — refuse, never silently skip)."""

    def test_returns_existing_path(self) -> None:
        here = Path(__file__).resolve()
        self.assertEqual(G._require_input(here, "this test", "n/a"), here)

    def test_raises_on_missing(self) -> None:
        missing = Path(__file__).resolve().parent / "does-not-exist-xyz.parquet"
        with self.assertRaises(SystemExit) as ctx:
            G._require_input(missing, "phantom input", "do the thing")
        msg = str(ctx.exception)
        self.assertIn("phantom input", msg)
        self.assertIn("do the thing", msg)  # remedy is surfaced


class TestRegistryDefaults(unittest.TestCase):
    """The registry-default resolution that makes a fresh checkout runnable."""

    def test_eia860_dir_defaults_to_registry(self) -> None:
        # No --eia860-dir override → the path-registry active vintage dir,
        # which is committed (data/raw/eia-860) so a fresh checkout resolves.
        resolved = G._resolve_eia860_dir(None)
        self.assertEqual(resolved, active_eia860_dir())
        self.assertTrue(resolved.is_dir())

    def test_ownership_builds_from_registry(self) -> None:
        # No --ownership-map → build the parent-company map in-process from the
        # committed EIA-860 ownership schedules. The fresh-checkout proof.
        eia_dir = G._resolve_eia860_dir(None)
        ownership = G._resolve_ownership(None, eia_dir)
        self.assertIsInstance(ownership, pd.DataFrame)
        self.assertFalse(ownership.empty)
        # build_parent_mapping's contract: adds parent_company + ownership_mw.
        self.assertIn("parent_company", ownership.columns)
        self.assertIn("ownership_mw", ownership.columns)

    def test_missing_ownership_map_is_fail_loud(self) -> None:
        missing = Path(__file__).resolve().parent / "no-such-ownership.parquet"
        with self.assertRaises(SystemExit):
            G._resolve_ownership(missing, active_eia860_dir())


if __name__ == "__main__":
    unittest.main()
