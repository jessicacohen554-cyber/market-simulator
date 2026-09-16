"""Tests for the Algonquin (AGT) narrative scraper's neiso-109 repair.

Each case is a MEASURED shape from the real EIA Natural Gas Weekly Update
archive, cited to the page it came from — never a synthetic string invented to
make a pattern pass. Evidence:
``docs/FINDING-neiso109-the-agt-series-is-contaminated-2026-09-16.md``.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "fetch_algonquin_daily_spot",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "data"
    / "fetch_algonquin_daily_spot.py",
)
agt = importlib.util.module_from_spec(_SPEC)
sys.modules["fetch_algonquin_daily_spot"] = agt
_SPEC.loader.exec_module(agt)


def _pair(text: str) -> tuple[float, float] | None:
    m = agt._AGT_MAIN.search(text)
    return (float(m.group(1)), float(m.group(2))) if m else None


# --------------------------------------------------------------------------
# DEFECT 1 — cross-hub contamination
# --------------------------------------------------------------------------

#: Real prose, page 2022-12-08. The committed ``.{0,220}?`` window crossed the
#: sentence boundary and wrote SUMAS's $16.46 into the Boston series.
_SUMAS_2022_12_08 = (
    "to a decline of $5.01/MMBtu at Algonquin Citygate. Prices in the West, already at "
    "elevated levels for several report weeks relative to other major U.S. markets, rose "
    "above $20.00/MMBtu this week. The price at Sumas on the Canada-Washington state "
    "border rose $4.73 from $16.46/MMBtu last Wednesday to $21.19/MMBtu yesterday, while "
    "the price at Malin, Oregon, rose $3.55 from $17.10/MMBtu last Wednesday to "
    "$20.65/MMBtu yesterday. In the Northeast, at the Algonquin Citygate, which serves "
    "Boston-area consumers , the price fell $5.01 from $9.91/MMBtu last Wednesday to "
    "$4.90/MMBtu yesterday."
)


def test_summary_clause_does_not_latch_onto_another_hub():
    """The span must reach Algonquin's OWN sentence, not Sumas's."""
    assert _pair(_SUMAS_2022_12_08) == (9.91, 4.90)


@pytest.mark.parametrize(
    "hub_sentence",
    [
        "The price at PG&E Citygate in Northern California rose $2.41, up from "
        "$5.03/MMBtu last Wednesday to $7.44/MMBtu yesterday.",
        "The price at the Waha Hub in West Texas fell 19 cents this report week, from "
        "$2.27/MMBtu last Wednesday to $2.08/MMBtu yesterday.",
        "At the Transco Zone 6 NY trading point for New York City, the price increased "
        "17 cents from $1.34/MMBtu last Wednesday to $1.51/MMBtu yesterday.",
    ],
)
def test_no_algonquin_price_yields_no_match(hub_sentence: str):
    """A page naming Algonquin only in a summary clause must yield NOTHING."""
    assert _pair(f"Algonquin Citygate to an increase elsewhere. {hub_sentence}") is None


def test_anaphoric_price_across_a_sentence_boundary_is_kept():
    """Page 2025-12-04: the price arrives in the NEXT sentence, and is real."""
    text = (
        "The price at the Algonquin Citygate, which serves the Boston area , had a "
        "significant price increase. It rose from $8.08/MMBtu last Wednesday to "
        "$25.00/MMBtu yesterday."
    )
    assert _pair(text) == (8.08, 25.00)


# --------------------------------------------------------------------------
# DEFECT 3 — the four unmatched EIA phrasings
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        # intervening extremum clause on the SECOND price (page 2018-12-20)
        (
            "Algonquin Citygate, which serves Boston-area consumers, prices went down "
            "$3.30 from $7.15/MMBtu last Wednesday to their weekly low of $3.85/MMBtu "
            "yesterday.",
            (7.15, 3.85),
        ),
        # ... and on the FIRST price (page 2020-03-19)
        (
            "Algonquin Citygate, which serves Boston-area consumers , the price went "
            "down 33 cents from a high of $1.75/MMBtu last Wednesday to a low of "
            "$1.42/MMBtu yesterday.",
            (1.75, 1.42),
        ),
        # unit spelled out on first use (page 2024-10-31)
        (
            "Algonquin Citygate, which serves Boston-area consumers , the price fell 10 "
            "cents from $1.90 per million British thermal units (MMBtu) last Wednesday "
            "to $1.80/MMBtu yesterday.",
            (1.90, 1.80),
        ),
        # "this Wednesday" for the report Wednesday (page 2025-01-10, the Jan-2025 snap)
        (
            "At the Algonquin Citygate, which serves Boston-area consumers , the price "
            "rose $11.69 from $4.86/MMBtu last Wednesday to $16.55/MMBtu this Wednesday.",
            (4.86, 16.55),
        ),
        # "last week" for the prior report Wednesday (page 2024-10-03)
        (
            "The price at the Algonquin Citygate, which serves Boston-area consumers , "
            "fell 35 cents from $1.97/MMBtu last week to $1.62/MMBtu yesterday.",
            (1.97, 1.62),
        ),
        # the committed shape must keep working: change figure inside the span
        (
            "At the Algonquin Citygate, which serves Boston-area consumers, the price "
            "went up $3.73 from $18.96/MMBtu last Wednesday to $22.69/MMBtu yesterday.",
            (18.96, 22.69),
        ),
    ],
)
def test_measured_phrase_variants(text: str, expected: tuple[float, float]):
    assert _pair(text) == expected


def test_last_thursday_first_price_is_not_guessed():
    """Page 2024-06-27 anchors the first price to an unresolvable day (rule 14)."""
    text = (
        "Algonquin Citygate, which serves Boston-area consumers , the price fell 38 "
        "cents from $2.40/MMBtu last Thursday to $2.02/MMBtu yesterday."
    )
    assert _pair(text) is None


# --------------------------------------------------------------------------
# DEFECT 2 — stale republish
# --------------------------------------------------------------------------

_SENTENCE_HTML = (
    "<p>At the <a>Algonquin Citygate</a>, which serves Boston-area consumers , the "
    "price went up 11 cents from $2.35/MMBtu last Wednesday to $2.46/MMBtu yesterday.</p>"
)


def test_agt_sentence_is_tag_insensitive_and_identifies_a_republish():
    """Pages 2024-02-29 and 2024-03-07 carry the identical sentence."""
    s1 = agt.agt_sentence(_SENTENCE_HTML)
    s2 = agt.agt_sentence(_SENTENCE_HTML.replace("<p>", "<p><b></b>"))
    assert s1 is not None and s1 == s2


def test_agt_sentence_none_when_absent():
    assert agt.agt_sentence("<p>The price at the Waha Hub fell 19 cents.</p>") is None


# --------------------------------------------------------------------------
# THE EXTREMUM REGIONS — the larger of the two cross-hub channels
# --------------------------------------------------------------------------


def _hilo(text: str) -> list[tuple[str, str, str]]:
    return [h for r in agt.agt_regions(text) for h in agt._AGT_HILO.findall(r)]


def test_region_stops_at_the_next_hub_name():
    """Page 2023-02-09: the $28.36 weekly high is TRANSCO's, not Algonquin's."""
    text = (
        "...at the Algonquin Citygate, which serves Boston-area consumers , the price "
        "fell $7.13 from $12.16/MMBtu last Wednesday to $5.03/MMBtu yesterday. At the "
        "Transcontinental Pipeline Zone 6 trading point for New York City, the price "
        "reached a weekly high of $28.36/MMBtu on Thursday."
    )
    assert _hilo(text) == []


def test_two_extremes_in_one_sentence_are_both_found():
    """Page 2023-02-02 — an anchored regex finds only the first."""
    text = (
        "The Algonquin Citygate price reached a weekly low of $3.22/MMBtu on Friday, "
        "before rising to a weekly high of $13.49/MMBtu on Tuesday."
    )
    assert _hilo(text) == [("low", "3.22", "Friday"), ("high", "13.49", "Tuesday")]


def test_three_word_spelling_is_recognised():
    """Page 2022-02-17 writes 'Algonquin City Gate'."""
    text = (
        "The Algonquin City Gate price rose to a weekly high of $22.48/MMBtu on Monday "
        "as a result of below-normal temperatures in the region."
    )
    assert _hilo(text) == [("high", "22.48", "Monday")]


def test_region_survives_an_intervening_non_hub_sentence():
    """Page 2019-04-04: the extremes follow a sentence with no hub in it."""
    text = (
        "At the Algonquin Citygate, which serves Boston-area consumers, prices went "
        "down 3 cents from $2.73/MMBtu last Wednesday to $2.70/MMBtu yesterday. "
        "Despite the small week-on-week change, Algonquin experienced intra-week price "
        "volatility. Prices went from a weekly low of $2.57/MMBtu on Thursday to a "
        "weekly high of $3.12/MMBtu on Friday."
    )
    assert ("high", "3.12", "Friday") in _hilo(text)


def test_caldate_extreme_stays_inside_its_region():
    """Page 2022-12-01: the Nov-4 monthly low is Algonquin's, dated absolutely."""
    text = (
        "Prices in the Northeast have fluctuated in recent weeks, with the price at "
        "Algonquin Citygate falling to a monthly low of $0.74/MMBtu on November 4 and "
        "rising as high as $11.60/MMBtu on November 18."
    )
    hits = [h for r in agt.agt_regions(text) for h in agt._AGT_CALDATE.findall(r)]
    assert hits == [("low", "0.74", "November", "4")]


def test_no_region_when_algonquin_is_absent():
    assert (
        agt.agt_regions("The price at the Waha Hub reached a weekly high of $3.00.")
        == []
    )


# --------------------------------------------------------------------------
# THE ALIGNMENT GUARD
# --------------------------------------------------------------------------


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def test_chain_guard_silent_on_a_consistent_chain():
    pairs = {
        (2024, 1, 11): (_d("2024-01-03"), 6.86, _d("2024-01-10"), 4.04),
        (2024, 1, 18): (_d("2024-01-10"), 4.04, _d("2024-01-17"), 13.35),
        (2024, 1, 25): (_d("2024-01-17"), 13.35, _d("2024-01-24"), 2.44),
    }
    assert agt.chain_guard(pairs) == []


def test_chain_guard_reports_a_date_anchoring_slip():
    """The 2022-12-08 contamination, as the guard sees it."""
    pairs = {
        (2022, 12, 1): (_d("2022-11-23"), 6.80, _d("2022-11-30"), 9.91),
        (2022, 12, 8): (_d("2022-11-30"), 16.46, _d("2022-12-07"), 21.19),
    }
    warns = agt.chain_guard(pairs)
    assert len(warns) == 1
    assert "2022-11-30" in warns[0] and "16.4600" in warns[0] and "9.9100" in warns[0]


def test_chain_guard_skips_pages_with_no_predecessor():
    """A gap in the archive is visible on its own and is not flagged."""
    pairs = {(2023, 1, 12): (_d("2022-12-28"), 6.51, _d("2023-01-04"), 4.04)}
    assert agt.chain_guard(pairs) == []


def test_main_sentence_pair_anchors_on_the_report_wednesday():
    cols = [_d("2025-01-02"), _d("2025-01-03"), _d("2025-01-06"), _d("2025-01-08")]
    html = (
        "<p>At the Algonquin Citygate, which serves Boston-area consumers , the price "
        "rose $11.69 from $4.86/MMBtu last Wednesday to $16.55/MMBtu this Wednesday.</p>"
    )
    assert agt.main_sentence_pair(html, cols) == (
        _d("2025-01-01"),
        4.86,
        _d("2025-01-08"),
        16.55,
    )


def test_main_sentence_pair_none_without_column_dates():
    assert agt.main_sentence_pair("<p>Algonquin Citygate</p>", []) is None


# --------------------------------------------------------------------------
# THE EXTREMUM GUARD — catches a hub missing from the _OTHER_HUBS vocabulary
# --------------------------------------------------------------------------


def test_extremum_guard_silent_on_a_consistent_week():
    by_date = {
        _d("2021-02-10"): (10.60, "last_wednesday"),
        _d("2021-02-16"): (14.20, "weekly_high"),
        _d("2021-02-17"): (11.56, "wednesday"),
    }
    assert agt.extremum_guard(by_date) == []


def test_extremum_guard_flags_a_high_below_its_own_week():
    """The real 2021-02-16 row: $5.97, which is Tennessee Zone 4's."""
    by_date = {
        _d("2021-02-10"): (10.60, "last_wednesday"),
        _d("2021-02-16"): (5.97, "weekly_high"),
        _d("2021-02-17"): (11.56, "wednesday"),
    }
    warns = agt.extremum_guard(by_date)
    assert len(warns) == 1 and "weekly HIGH 5.9700 is BELOW" in warns[0]


def test_extremum_guard_flags_a_low_above_its_own_week():
    by_date = {
        _d("2021-06-02"): (2.23, "last_wednesday"),
        _d("2021-06-08"): (3.81, "weekly_low"),
        _d("2021-06-09"): (2.62, "wednesday"),
    }
    warns = agt.extremum_guard(by_date)
    assert len(warns) == 1 and "weekly LOW 3.8100 is ABOVE" in warns[0]


def test_extremum_guard_skips_a_row_with_no_bracketing_week():
    """A gap wider than a report week gives nothing to test against."""
    by_date = {
        _d("2021-01-06"): (5.00, "wednesday"),
        _d("2021-02-16"): (1.00, "weekly_high"),
        _d("2021-03-31"): (5.00, "wednesday"),
    }
    assert agt.extremum_guard(by_date) == []
