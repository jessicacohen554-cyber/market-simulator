"""Parser tests for the EIA New England Dashboard Algonquin tile (closeout-NEISO wave 1).

Fixtures are trimmed ``pdftotext -layout`` excerpts of real archive snapshots, one per
layout seen 2019-2025.
"""

from scripts.data.fetch_eia_ne_dashboard_agt_daily import parse_snapshot

# 2019-01-31: four tiles share a row; a utilization "%" sits between Bcf/d and the price.
_LAYOUT_2019 = (
    "   4.90 Bcf/d          0.75 Bcf/d          82.70 %          10.15 $/MMBtu\n"
    "   Demand              Demand change       Regional pipeline utilization   "
    "Spot natural gas price (Algonquin Citygate)\n"
    "   1/30/19             1/30/19             1/31/19          1/31/19\n"
)
# 2020-01-15: the caption wraps "(Algonquin / Citygate)" and the label drops a line.
_LAYOUT_2020 = (
    ".28 Bcf/d                                   2.39 $/MMBtu\n"
    "  Demand change                             Spot natural gas price (Algonquin\n"
    "  1/15/20        79.50%                     Citygate)\n"
    "                                            1/15/20\n"
)
# 2025-07-01: the value sits six lines above the caption.
_LAYOUT_2025 = (
    "   2.83 Bcf/d          0.36 Bcf/d                       3.38 $/MMBtu\n"
    "   Demand\n"
    "   7/1/25\n"
    "                       Demand change\n"
    "                       7/1/25\n"
    "                                         63.30%\n"
    "                                         63.30%          Spot natural gas price\n"
    "                                                         (Algonquin Citygate)\n"
    "                                         Regional        7/1/25\n"
)
# 2023-07-12: a blank dashboard — every tile prints "--" and there is no label.
_BLANK = (
    "  -- Bcf/d          -- Bcf/d                    -- $/MMBtu\n"
    "   Demand            Demand change               Spot natural gas price\n"
    "                                                 (Algonquin Citygate)\n"
)
# The notes page names the indicator but carries no tile; it must be skipped.
_NOTES = "Spot natural gas price (Algonquin Citygate)\nThis indicator shows the most recent spot price\n"


def test_parses_each_layout():
    assert parse_snapshot(_LAYOUT_2019)[:2] == ("10.15", "2019-01-31")
    assert parse_snapshot(_LAYOUT_2020)[:2] == ("2.39", "2020-01-15")
    assert parse_snapshot(_LAYOUT_2025)[:2] == ("3.38", "2025-07-01")


def test_blank_dashboard_is_no_print():
    assert parse_snapshot(_BLANK)[:2] == ("--", None)


def test_notes_page_is_skipped_and_update_stamp_is_kept():
    text = _NOTES + "\f" + _LAYOUT_2019 + "Last daily update: January 31,\n2019 Next"
    value, label, stamp = parse_snapshot(text.replace("\n2019 Next", " 2019 Next"))
    assert (value, label) == ("10.15", "2019-01-31")
    assert stamp == "January 31, 2019"


def test_missing_tile_returns_none():
    assert parse_snapshot(_NOTES)[:2] == (None, None)
