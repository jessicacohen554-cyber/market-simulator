"""Tests for the EIA NGWU Transco Z6 NY spot-table parser (nyiso-234 repair).

Covers the pure part of ``scripts/data/fetch_transco_daily_spot.py`` — the
parse of a page body into dated prices. Nothing here touches the network; the
fixtures are trimmed transcriptions of the real EIA markup.

The two defects this file pins are the ones that put a wrong delivered gas price
in front of the whole NYISO gas fleet
(``docs/FINDING-nyiso234b-the-gas-series-was-published-2026-09-14.md``):

1. **A page can carry MORE THAN ONE live table, and the extra ones are the only
   published record of the weeks EIA skips.** EIA publishes no Weekly Update over
   the Christmas/New Year weeks and carries them as additional live tables when it
   resumes. The parser took ``re.search`` — the first table only — so every
   catch-up week was dropped, leaving a 14-15 day hole across every year-end and a
   flat interpolated fill through Winter Storm Elliott, whose real prints were
   **$32.12 (Dec 22 2022)** and **$35.61 (Dec 23 2022)** against the $8.05 the
   model burned.

2. **A header may separate day and month with a SPACE, not only a hyphen**
   (``"Thu, 5 Jan"`` beside ``"Fri, 6-Jan"``, sometimes in one table). The
   hyphen-only pattern dropped the spaced date, leaving four dates against five
   values — so every price in that week landed on the FOLLOWING trading day.
   Measured: the committed series carried Jan 6 2023 = 3.17 where EIA published
   3.50, and the same shift through Jan 9/10/11.

The alignment guard is the durable half of the repair and is asserted hardest
here: a table whose dates and values disagree must be SKIPPED, never emitted.
A gap is visible to anyone who counts rows; a one-day shift looks like good data.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import fetch_transco_daily_spot as f  # noqa: E402


def _table(header_cells: list[str], hh: list[str], ny: list[str]) -> str:
    """Render one EIA-shaped spot table."""
    head = "".join(f"<td>{c}</td>" for c in header_cells)
    return (
        "<table>"
        f"<thead><tr><td>Spot Prices ($/MMBtu)</td>{head}</tr></thead>"
        "<tbody>"
        "<tr><td><strong>Henry Hub</strong></td>"
        + "".join(f'<td align="right">{v}</td>' for v in hh)
        + "</tr>"
        "<tr><td><strong>New York</strong></td>"
        + "".join(f'<td align="right">{v}</td>' for v in ny)
        + "</tr>"
        "</tbody></table>"
    )


def _page(*tables: str) -> str:
    return '<div id="tabs-prices-2">' + "".join(tables) + "</div>"


# The real 2023-01-12 catch-up page, trimmed: current week + the two EIA skipped.
CURRENT = _table(
    ["Thu, 5 Jan", "Fri, 6-Jan", "Mon, 9-Jan", "Tue, 10-Jan", "Wed, 11-Jan"],
    ["3.76", "3.42", "3.67", "3.32", "3.35"],
    ["3.17", "3.50", "3.98", "3.37", "2.79"],
)
NEW_YEAR = _table(
    ["Thu, 29-Dec", "Fri, 30-Dec", "Mon, 2-Jan", "Tue, 3-Jan", "Wed, 4-Jan"],
    ["3.70", "3.55", "Holiday", "3.65", "3.81"],
    ["3.29", "2.77", "Holiday", "2.56", "3.35"],
)
ELLIOTT = _table(
    ["Thu, 22-Dec", "Fri, 23-Dec", "Mon, 26-Dec", "Tue, 27-Dec", "Wed, 28-Dec"],
    ["7.30", "6.56", "Holiday", "4.90", "4.12"],
    ["32.12", "35.61", "Holiday", "6.29", "5.15"],
)


class MultipleLiveTablesTest(unittest.TestCase):
    """Defect 1: the catch-up weeks are extra LIVE tables, not comments."""

    def test_every_live_table_is_parsed_not_just_the_first(self) -> None:
        rows = f.parse_spot_table(_page(CURRENT, NEW_YEAR, ELLIOTT), 2023, 1)
        got = {r["date"]: r["transco"] for r in rows}
        # 15 columns - 2 holidays (Dec 26, Jan 2) = 13 dated prices.
        self.assertEqual(len(rows), 13)
        self.assertIn("2022-12-23", got)

    def test_the_elliott_prints_are_recovered_at_their_published_values(self) -> None:
        """The whole point of the repair: the largest gas event is in table 3."""
        rows = f.parse_spot_table(_page(CURRENT, NEW_YEAR, ELLIOTT), 2023, 1)
        got = {r["date"]: r["transco"] for r in rows}
        self.assertAlmostEqual(got["2022-12-22"], 32.12)
        self.assertAlmostEqual(got["2022-12-23"], 35.61)

    def test_the_december_january_boundary_resolves_to_the_right_year(self) -> None:
        """A Dec column on a January page belongs to the PREVIOUS year."""
        rows = f.parse_spot_table(_page(CURRENT, NEW_YEAR, ELLIOTT), 2023, 1)
        got = {r["date"]: r["transco"] for r in rows}
        self.assertAlmostEqual(got["2022-12-29"], 3.29)  # Dec -> 2022
        self.assertAlmostEqual(got["2023-01-04"], 3.35)  # Jan -> 2023

    def test_holiday_columns_yield_no_row(self) -> None:
        """No trade, so no price — a holiday must not become a dated value."""
        rows = f.parse_spot_table(_page(ELLIOTT), 2023, 1)
        self.assertNotIn("2022-12-26", {r["date"] for r in rows})


class DateAlignmentTest(unittest.TestCase):
    """Defect 2: a spaced header date must not shift the week by a day."""

    def test_a_spaced_header_date_is_read_not_dropped(self) -> None:
        """``"Thu, 5 Jan"`` is a date; the hyphen-only pattern lost it."""
        rows = f.parse_spot_table(_page(CURRENT), 2023, 1)
        got = {r["date"]: r["transco"] for r in rows}
        self.assertIn("2023-01-05", got)
        self.assertAlmostEqual(got["2023-01-05"], 3.17)

    def test_values_land_on_their_own_dates(self) -> None:
        """The regression: every price was previously one trading day late."""
        rows = f.parse_spot_table(_page(CURRENT), 2023, 1)
        got = {r["date"]: r["transco"] for r in rows}
        self.assertAlmostEqual(got["2023-01-06"], 3.50)  # was 3.17
        self.assertAlmostEqual(got["2023-01-09"], 3.98)  # was 3.50
        self.assertAlmostEqual(got["2023-01-10"], 3.37)  # was 3.98
        self.assertAlmostEqual(got["2023-01-11"], 2.79)  # was 3.37

    def test_a_misaligned_table_is_skipped_not_emitted(self) -> None:
        """The guard. Four header dates against five values must yield NOTHING.

        This is the durable half of the repair: the failure mode that produced
        defect 2 was silent, and a silently shifted gas price is worse than a
        gap because a gap is visible.
        """
        broken = _table(
            ["Thu, ?? Jan", "Fri, 6-Jan", "Mon, 9-Jan", "Tue, 10-Jan", "Wed, 11-Jan"],
            ["3.76", "3.42", "3.67", "3.32", "3.35"],
            ["3.17", "3.50", "3.98", "3.37", "2.79"],
        )
        self.assertEqual(f.parse_spot_table(_page(broken), 2023, 1), [])

    def test_one_bad_table_does_not_discard_the_good_ones(self) -> None:
        """Per-table parsing: the Elliott week survives a malformed neighbour."""
        broken = _table(
            ["Thu, ?? Jan", "Fri, 6-Jan", "Mon, 9-Jan", "Tue, 10-Jan", "Wed, 11-Jan"],
            ["3.76", "3.42", "3.67", "3.32", "3.35"],
            ["3.17", "3.50", "3.98", "3.37", "2.79"],
        )
        rows = f.parse_spot_table(_page(broken, ELLIOTT), 2023, 1)
        got = {r["date"]: r["transco"] for r in rows}
        self.assertAlmostEqual(got["2022-12-23"], 35.61)
        self.assertNotIn("2023-01-06", got)


class NonSpotContentTest(unittest.TestCase):
    """A page without a usable New York row yields nothing, never an exception."""

    def test_no_prices_block(self) -> None:
        self.assertEqual(f.parse_spot_table("<html>nothing</html>", 2023, 1), [])

    def test_a_table_with_no_new_york_row_is_ignored(self) -> None:
        page = _page(
            "<table><thead><tr><td>Spot Prices ($/MMBtu)</td><td>Thu, 5-Jan</td>"
            "</tr></thead><tbody><tr><td><strong>Chicago</strong></td>"
            '<td align="right">3.10</td></tr></tbody></table>'
        )
        self.assertEqual(f.parse_spot_table(page, 2023, 1), [])


if __name__ == "__main__":
    unittest.main()
