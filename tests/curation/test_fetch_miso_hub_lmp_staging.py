"""Tests for the empty-staging guards in ``scripts/data/fetch_miso_hub_lmp.py``.

The staging loop drops a day that fails every retry rather than aborting the
year (cheap to re-fetch one day, expensive to re-run 365). That tolerance had a
trap: a year where EVERY day fails -- a pre-2023 year, whose daily reports
``docs.misoenergy.org`` no longer serves, fetched without the
``MISO_PRICING_API_KEY`` the documented Data Exchange fallback needs -- still
wrote its full set of chunk files, header-only and 0 rows. Those files are named
exactly like a real staging and ``derive_miso_hub_lmp.py`` reads them without
complaint, so an absent source could masquerade as a staged year.

Nothing here touches the network: ``_hub_rows`` is patched.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import fetch_miso_hub_lmp as f  # noqa: E402


def _rows(day: date) -> list[list[str]]:
    """One minimal staged record for ``day`` (one hub, LMP row, 24 hours)."""
    return [[day.isoformat(), "INDIANA.HUB", "Hub", "LMP", *["21.60"] * 24]]


class StagingGuards(unittest.TestCase):
    """``stage_year`` must not present an absent source as a staged year."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._out = f.OUT_DIR
        f.OUT_DIR = Path(self._tmp.name)

    def tearDown(self) -> None:
        f.OUT_DIR = self._out
        self._tmp.cleanup()

    def _patch(self, fn) -> None:
        self._real = f._hub_rows
        f._hub_rows = fn
        self.addCleanup(lambda: setattr(f, "_hub_rows", self._real))

    def test_every_day_failing_raises_and_writes_nothing(self) -> None:
        """A year with no fetchable day raises, leaving no chunk file behind."""

        def boom(day, market, api_key):
            raise f._NotFound("aged off")

        self._patch(boom)
        with self.assertRaises(RuntimeError) as ctx:
            f.stage_year(2020, "da", None, through=date(2020, 1, 20))
        self.assertIn("MISO_PRICING_API_KEY", str(ctx.exception))
        self.assertEqual(sorted(Path(self._tmp.name).iterdir()), [])

    def test_a_fully_failed_window_writes_no_chunk_file(self) -> None:
        """Days 1-7 stage; 8-20 all fail -> only the covered chunk is written."""

        def partial(day, market, api_key):
            if day.day <= 7:
                return _rows(day)
            raise f._NotFound("aged off")

        self._patch(partial)
        paths = f.stage_year(2020, "da", None, through=date(2020, 1, 20))
        names = sorted(p.name for p in Path(self._tmp.name).iterdir())
        self.assertEqual(names, ["miso_hub_lmp_2020_da_p01.csv"])
        self.assertEqual([p.name for p in paths], names)
        # The one written chunk carries its header plus the seven real days.
        lines = (Path(self._tmp.name) / names[0]).read_text().splitlines()
        self.assertEqual(len(lines), 1 + 7)


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
