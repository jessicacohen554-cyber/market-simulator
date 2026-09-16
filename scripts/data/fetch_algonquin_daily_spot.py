#!/usr/bin/env python3
"""Scrape the **daily** Algonquin Citygate (AGT) natural-gas spot price from the
EIA Natural Gas Weekly Update archive narrative, for the ISO-NE daily hub-basis
overlay.

ISO-NE's marginal gas unit prices off Algonquin Citygate, the pipeline-constrained
New England trading hub whose winter spot blows out to many multiples of Henry Hub
on the coldest days (gas-for-heating crowds gas-for-power off the Algonquin pipe).
The model has the measured *monthly* AGT basis (``gas_basis_by_iso_month.csv``,
EIA MA-citygate family) - the right level - but a flat monthly plateau never
reaches distillate parity, so the dual-fuel gas->oil switch and the winter LMP
tail are understated. The real daily AGT spot is an ICE/Platts product (paywalled),
but **EIA quotes it for free in the prose of every Weekly Update**, e.g.:

    "At the Algonquin Citygate, which serves Boston-area consumers, the price
     went up $9.31 from $4.04/MMBtu last Wednesday to $13.35/MMBtu yesterday,
     after reaching a weekly high of $17.27/MMBtu on Tuesday."

Each weekly page therefore carries two hard-dated AGT spot prints - the report
Wednesday ("yesterday") and the prior Wednesday ("last Wednesday") - plus, in
volatile (winter) weeks, a named-weekday weekly high and/or low. These are real
measured AGT quotes, densest exactly in the cold weeks that set the price tail.
This is the AGT analogue of ``fetch_transco_daily_spot.py`` (which reads the
structured "New York"/Transco Z6 NY row of the same pages); the compact EIA spot
table has no Algonquin row, so AGT is recovered from the narrative instead.

Source: ``https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/YYYY/MM_DD/`` (one
per publication Thursday). The five daily column dates in the page's "Spot Prices"
table header pin the calendar: the last (Wednesday) column is the narrative's
"yesterday", and "last Wednesday" is seven days earlier; weekly high/low weekday
names map onto the five column dates of the report week.

The 2022-era Weekly Updates phrase the main sentence with an intervening change
figure ("the price went up $3.73 from $18.96/MMBtu last Wednesday to
$22.69/MMBtu yesterday") and often state the cold-week peak/trough by an
absolute calendar date rather than a weekday ("a weekly high of $22.81/MMBtu on
February 3", "a monthly low of $0.74/MMBtu on November 4"). The main regex
therefore spans the change figure, and ``_AGT_CALDATE`` recovers the
calendar-dated extremes (``high_caldate``/``low_caldate``); a high/low with no
dateable anchor ("in advance of the holiday weekend") is left out rather than
guessed (rule 14). The compact EIA "Spot Prices" table carries no Algonquin row
in the 2022 pages either (verified), so the narrative remains the only source.

Output: ``data/raw/gas-prices/algonquin_citygate_daily.csv``
  columns ``date, algonquin_citygate_usd_mmbtu, source`` where ``source`` is the
  narrative anchor the print came from (``wednesday``/``last_wednesday``/
  ``weekly_high``/``weekly_low``/``high_caldate``/``low_caldate``) for
  provenance. Later pages win on a duplicate date (revisions).

``--merge`` seeds from the committed CSV and adds ONLY newly scraped dates,
asserting every pre-existing row survives byte-identical - so a holdout year can
be densified (e.g. ``--start-year 2022 --end-year 2022 --merge``) while the
in-sample 2023-2025 rows stay frozen. The default (no ``--merge``) REPLACES the
file, the original behaviour for a full 2023-2025 rebuild.

Usage:
    uv run python scripts/data/fetch_algonquin_daily_spot.py
    uv run python scripts/data/fetch_algonquin_daily_spot.py --start-year 2023 --end-year 2025
    uv run python scripts/data/fetch_algonquin_daily_spot.py --start-year 2022 --end-year 2022 --merge
"""

from __future__ import annotations

import argparse
import csv
import io
import datetime as dt
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import GAS_PRICES_DIR  # noqa: E402

OUT_PATH = GAS_PRICES_DIR / "algonquin_citygate_daily.csv"

ARCHIVE_INDEX = "https://www.eia.gov/naturalgas/weekly/includes/archive.php"
PAGE_TMPL = "https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/{y}/{m:02d}_{d:02d}/"

_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}
_WEEKDAY = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

# Main AGT sentence: two dated Wednesday prints.
#
# SPAN SCOPING, AND WHY IT IS THE HUB NAMES AND NOT A CHARACTER BOUND.
# The span from "Algonquin Citygate" to the price pair must cross an intervening
# change figure ("the price went up $3.73 from $18.96/MMBtu last Wednesday to
# ...") - a ``$``- AND ``.``-bearing delta that both a ``[^$]*?`` and a
# ``[^.]*?`` choke on - while never reaching a DIFFERENT hub's own "last
# Wednesday ... yesterday" pair, which every Weekly Update also carries.
#
# This was a bounded ``.{0,220}?`` character window, and a character count is a
# proxy for "still talking about Algonquin" rather than the thing itself. It
# failed in BOTH directions, measured over all 389 archive pages 2018-2026:
#   * TOO TIGHT - real Algonquin sentences run to 292 characters, so the window
#     truncated them;
#   * TOO LOOSE, and this is the damaging half - EIA opens a regional paragraph
#     with a summary clause naming Algonquin ("...to a decline of $5.01/MMBtu at
#     Algonquin Citygate.") and then prices a DIFFERENT hub in the next sentence.
#     Inside 220 characters the pattern reached that hub and wrote ITS price into
#     this series. **Sixteen committed rows are another hub's price**: Sumas
#     (2022-11-30 $16.46, which is a Canada-Washington border quote standing in
#     the Boston citygate series through Winter Storm Elliott week), PG&E
#     Citygate, SoCal Citygate, Waha, FGT Citygate, Florida Gas Zone 3 and
#     Transco Z6 NY. The largest single error is 2023-07-26, committed at Waha's
#     $2.27 where Algonquin was $6.31.
# The span is therefore scoped by what it must not cross - :data:`_OTHER_HUBS`,
# a tempered-dot over the hub vocabulary the archive actually uses. A sentence
# boundary is the wrong scope: EIA also writes the price anaphorically across one
# ("Algonquin Citygate ... had a significant price increase. It rose from
# $8.08/MMBtu last Wednesday to $25.00/MMBtu yesterday", 2025-12-04), and a
# sentence-scoped span drops that real print while the hub-scoped span keeps it.
#
# PHRASE VARIANTS. The committed pattern required, literally,
# ``$X/MMBtu last Wednesday to $Y/MMBtu yesterday``, and EIA writes that
# sentence four other ways. Each variant below is a shape MEASURED on the
# archive, not a speculative widening (counts are pages gained, 2018-2026):
#   * an intervening extremum clause on EITHER price - "to their weekly low of
#     $3.85/MMBtu yesterday", "from a high of $1.75/MMBtu last Wednesday" (39);
#   * the unit spelled out on first use - "$1.90 per million British thermal
#     units (MMBtu) last Wednesday" (2);
#   * "this Wednesday" for the report Wednesday in place of "yesterday" (1) -
#     the same calendar day, and the 2025-01-10 page that carries the January
#     2025 cold-snap print ($4.86 -> $16.55) uses it;
#   * "last week" for the prior report Wednesday in place of "last Wednesday"
#     (2). Unambiguous in EIA's Thu..Wed report week, and the chain guard in
#     :func:`main` VERIFIES each one against the previous page's own Wednesday
#     print rather than trusting the reading.
# Deliberately NOT matched, per rule 14 (prefer the real datum; never guess one):
# "last Thursday" (2024-06-27) anchors the first price to a day this parser
# cannot resolve from the report week alone, so that page yields its Wednesday
# print through the ``yesterday`` limb and its first price is left out.
#: How EIA names the hub. "Algonquin City Gate" (three words) occurs alongside
#: "Algonquin Citygate" — measured on pages 2022-02-17 and 2023-02-02, both of
#: which carry a real cold-week extreme the one-word spelling misses.
_AGT_NAME = r"Algonquin\s+City\s?gate"
#: Every OTHER trading hub EIA prices in these narratives, harvested from the
#: archive's own "the price at <hub>" constructions rather than assumed. The
#: span may not cross one: past a different hub's name the numbers stop being
#: Algonquin's. (Algonquin itself is deliberately absent — a second mention of
#: it is how the real sentence is reached after a summary clause.)
_OTHER_HUBS = (
    r"Transco|Transcontinental|PG&E|SoCal|Sumas|Waha|Malin|Opal|FGT|Florida Gas|"
    r"Tennessee Zone|Eastern Gas|Dominion South|Chicago Citygate|Houston Ship|Katy|"
    r"Cheyenne|Mont Belvieu|Tetco|AECO|Kingsgate|Westcoast|Henry Hub|Nymex|"
    r"El Paso|Kern River"
)
#: Tempered dot: any run of text that does not reach another hub's name.
_SPAN = r"(?:(?!" + _OTHER_HUBS + r").)*?"
#: Optional "a / their / the [weekly] high|low of" before a price.
_HILO_CLAUSE = r"(?:(?:a|their|the)\s+(?:weekly\s+)?(?:high|low)\s+of\s+)?"
#: A price with the unit either abbreviated or spelled out on first use.
_PRICE = r"\$([0-9]+\.?[0-9]*)(?:/MMBtu|\s+per million British thermal units \(MMBtu\))"
_AGT_MAIN = re.compile(
    _AGT_NAME
    + _SPAN
    + _HILO_CLAUSE
    + _PRICE
    + r"\s+last\s+(?:Wednesday|week)\s+to\s+"
    + _HILO_CLAUSE
    + _PRICE
    + r"\s+(?:yesterday|this Wednesday)",
    flags=re.S | re.I,
)
# A standalone "reaching a weekly high of $X/MMBtu on Day" can follow the main
# sentence, and its subject is still Algonquin — BUT ONLY IF NO OTHER HUB HAS
# BEEN NAMED IN BETWEEN.
#
# **THIS PATTERN HAD NO ALGONQUIN ANCHOR AT ALL** and was applied to the whole
# page, so it captured *whichever hub's* weekly extreme the page happened to
# state and filed it as an Algonquin print. Measured over the archive: of 120
# matches, **95 had a different hub as the nearest preceding hub name**, and
# **69 of the 89 committed `weekly_high`/`weekly_low` rows are a foreign hub's
# extreme** — Henry Hub (15), Chicago Citygate (15), Transco Z6 NY (14), SoCal
# (9), PG&E (6), Waha (3), Dominion South (2), Tennessee Zone (2), Eastern Gas
# (2), Katy (1). Two land on days the model leans on:
#   * **2023-02-02 $28.36** — the arctic-outbreak spike
#     ``hubs.iso_hub_daily_gas_prices``'s own docstring cites as "the $28/MMBtu
#     2023-02-02 arctic print". It is **Transco Z6 NY**, a New York price.
#   * **2024-01-16 $23.90** — likewise Transco.
# It is the same cross-hub class as the main sentence's (see ``_AGT_MAIN``),
# and it was larger.
#
# The fix is :func:`agt_regions` — the span from an Algonquin mention up to the
# next OTHER hub's name — with the extremum patterns run INSIDE a region rather
# than over the page. A region is used instead of one anchored regex because EIA
# states two extremes in a single sentence ("reached a weekly low of $3.22/MMBtu
# on Friday, before rising to a weekly high of $13.49/MMBtu on Tuesday",
# 2023-02-02), and an anchored pattern captures only the first.
#
# (The unused ``_AGT_HIGH``/``_AGT_LOW`` that sat here were correctly anchored
# and never called — dead code is a re-armable answer key, rule 26 ``[R-DELETE]``
# — so they are DELETED rather than left parsing.)
_AGT_HILO = re.compile(
    r"(?:weekly|monthly)\s+(high|low)\s+of\s+" + _PRICE + r"\s+on\s+(\w+day)",
    flags=re.S | re.I,
)
_AGT_REGION_START = re.compile(_AGT_NAME, flags=re.I)
_AGT_REGION_END = re.compile(_OTHER_HUBS, flags=re.I)


def agt_regions(text: str) -> list[str]:
    """Return the stretches of ``text`` that are still speaking about Algonquin.

    Each region runs from an Algonquin mention to the next OTHER hub's name (or
    the end of the text). Extremum prints are harvested inside a region, so they
    can never be another hub's — the same invariant ``_SPAN`` gives
    :data:`_AGT_MAIN`, expressed so that SEVERAL prints per region are found.
    """
    ends = [m.start() for m in _AGT_REGION_END.finditer(text)]
    out: list[str] = []
    for m in _AGT_REGION_START.finditer(text):
        stop = next((e for e in ends if e > m.start()), len(text))
        out.append(text[m.start() : stop])
    return out


# Explicit-calendar-date weekly/monthly high/low, the dominant 2022-era shape:
# "Algonquin Citygate price reached a weekly high of $22.81/MMBtu on February 3"
# / "monthly low of $0.74/MMBtu on November 4". Unlike ``_HILO_TAIL`` (which
# pins a weekday name onto a report-week column), this carries an absolute
# ``Month Day`` that dates the print directly - so it recovers the cold-week
# extremes on the many 2022 pages that state the peak/trough by calendar date
# rather than by weekday. It was anchored to "Algonquin Citygate" by ``[^.]*?``,
# which is the right INTENT but the wrong SCOPE twice over: ``[^.]`` stops at the
# first decimal point (so a "$22.81" inside the span truncates it), and a
# sentence is not what bounds a hub's subject anyway. It now shares ``_SPAN``
# with ``_AGT_MAIN`` and ``_AGT_HILO``, so all three are scoped by the same
# measured rule - the span may not reach past another hub's name.
_MONTHS_FULL = {
    m: i
    for i, m in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}
_AGT_CALDATE = re.compile(
    r"(?:weekly|monthly)\s+(high|low)\s+of\s+"
    + _PRICE
    + r"\s+on\s+("
    + "|".join(_MONTHS_FULL)
    + r")\s+(\d{1,2})",
    flags=re.S | re.I,
)


def _fetch(url: str, timeout: int = 60) -> str:
    """GET a URL with a browser-ish UA, returning decoded text. Raises on error."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-sim data fetch)"})
    with urlopen(req, timeout=timeout) as fh:
        return fh.read().decode("utf-8", errors="replace")


def archive_pages(start_year: int, end_year: int) -> list[tuple[int, int, int]]:
    """Return sorted ``(year, month, day)`` publication dates of archive pages.

    A page published in month M reports the prior week, so a late-December week is
    published the following January; we keep pages through the first weeks of
    ``end_year + 1`` to capture every day in ``[start_year, end_year]``.
    """
    html = _fetch(ARCHIVE_INDEX)
    seen = sorted(set(re.findall(r"archivenew_ngwu/(\d{4})/(\d{2})_(\d{2})", html)))
    out = []
    for y, m, d in seen:
        yi = int(y)
        if start_year <= yi <= end_year + 1:
            out.append((yi, int(m), int(d)))
    return out


def _resolve_year(month: int, page_year: int, page_month: int) -> int:
    """Year of a column whose month is ``month`` on a page published in
    ``page_year``/``page_month`` (handle the Dec/Jan boundary the week straddles)."""
    if month == 12 and page_month == 1:
        return page_year - 1
    if month == 1 and page_month == 12:
        return page_year + 1
    return page_year


def column_dates(html: str, page_year: int, page_month: int) -> list[dt.date]:
    """Return the five ``date`` objects (Thu..Wed) of the page's Spot Prices table.

    These pin the narrative calendar: the last/Wednesday column is "yesterday",
    "last Wednesday" is seven days earlier, and weekly high/low weekday names map
    onto these five report-week days. Mirrors the header parse in
    ``fetch_transco_daily_spot.py``.
    """
    idx = html.find('id="tabs-prices-2"')
    seg = html[idx : idx + 24000] if idx >= 0 else html[:24000]
    seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)  # drop commented templates
    head = seg[: seg.find("</thead>") + 8] if "</thead>" in seg else seg
    out: list[dt.date] = []
    for day_s, mon_s in re.findall(r"(\d{1,2})-([A-Z][a-z]{2})", head):
        mon = _MONTHS.get(mon_s)
        if mon is None:
            continue
        yr = _resolve_year(mon, page_year, page_month)
        try:
            out.append(dt.date(yr, mon, int(day_s)))
        except ValueError:
            continue
    return sorted(set(out))


def main_sentence_pair(
    html: str, cols: list[dt.date]
) -> tuple[dt.date, float, dt.date, float] | None:
    """Return ``(last_wed, last_wed_price, wednesday, wednesday_price)`` or None.

    The two hard-dated prints of the main AGT narrative sentence, exposed so
    :func:`chain_guard` can cross-check consecutive pages. Same anchoring as
    :func:`parse_agt`, which is the consumer that actually emits them.
    """
    if not cols:
        return None
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    m = _AGT_MAIN.search(text)
    if not m:
        return None
    wednesdays = [d for d in cols if d.weekday() == _WEEKDAY["Wednesday"]]
    yesterday = wednesdays[-1] if wednesdays else cols[-1]
    return (
        yesterday - dt.timedelta(days=7),
        float(m.group(1)),
        yesterday,
        float(m.group(2)),
    )


def chain_guard(
    pairs: dict[tuple[int, int, int], tuple[dt.date, float, dt.date, float]],
    tol: float = 0.005,
) -> list[str]:
    """Return one warning line per page whose prints disagree with its neighbour.

    **The AGT analogue of the header/value ALIGNMENT GUARD in
    ``fetch_transco_daily_spot.py``, and it has to be a different shape because
    AGT is a different kind of source.** Transco Z6 NY is a row of EIA's compact
    "Spot Prices" table, so alignment there means column *i* of the value row is
    column *i* of the header, checkable inside one table. Algonquin has **no row
    in that table at all** (verified on the 2023-01-12 / 2024-01-11 / 2025-01-10
    catch-up pages: the rows are Henry Hub, New York, Chicago), which is why this
    fetcher reads the narrative - and a narrative carries no columns to align.

    What it carries instead is a REDUNDANT OVERLAP: each weekly page states the
    prior report Wednesday's price as well as its own, so consecutive pages quote
    the same date twice. That overlap is the invariant, and it checks the same
    property the Transco guard checks - that a price is attached to the right day
    - across pages rather than across columns::

        page(w).last_wednesday_price  ==  page(w-1).wednesday_price

    A date-anchoring slip (a mis-resolved report Wednesday, a Dec/Jan boundary
    error, a phrase variant read against the wrong anchor) breaks it, so the
    silent failure mode becomes a loud one. Pages seven days apart are the only
    ones compared; a gap in the archive is skipped rather than flagged, because a
    missing week is visible on its own.

    Returns the warning lines (empty when the chain is clean) instead of raising:
    a mismatch is a data-quality signal for the operator to adjudicate, and this
    fetcher's committed-row freeze is what protects the file.
    """
    out: list[str] = []
    for key in sorted(pairs):
        prev_wed, prev_price, wed, _price = pairs[key]
        # The page that reported ``prev_wed`` as its OWN report Wednesday.
        prior = next((v for v in pairs.values() if v[2] == prev_wed), None)
        if prior is None:
            continue
        if abs(prior[3] - prev_price) > tol:
            out.append(
                f"  WARN: chain break at {prev_wed} - page {key[0]}-{key[1]:02d}-"
                f"{key[2]:02d} reads {prev_price:.4f} as last Wednesday, but the "
                f"page that reported {prev_wed} as its own Wednesday read "
                f"{prior[3]:.4f}"
            )
    return out


def extremum_guard(by_date: dict[dt.date, tuple[float, str]]) -> list[str]:
    """Return one warning per extremum row that cannot be Algonquin's own.

    The SECOND guard, and it checks what :func:`agt_regions` structurally cannot:
    a region is bounded by :data:`_OTHER_HUBS`, so a hub MISSING from that
    vocabulary could still leak an extreme in. This test needs no vocabulary at
    all - it is arithmetic on the series itself. A weekly HIGH must be at least
    the bracketing Wednesday prints and a weekly LOW at most them, because all
    three are prices for the same hub within the same week.

    Measured on the pre-repair file it flags 10 of the 91 extremum rows, and
    every one is independently confirmed as a foreign hub's print by the region
    analysis (Tennessee Zone, Waha, Chicago Citygate, ...) - so the two
    instruments agree without sharing an assumption.

    Warnings only, like :func:`chain_guard`: the operator adjudicates.
    """
    wed = {d for d, (_p, s) in by_date.items() if s in ("wednesday", "last_wednesday")}
    out: list[str] = []
    for d, (price, src) in sorted(by_date.items()):
        if src in ("wednesday", "last_wednesday"):
            continue
        prior = max((x for x in wed if x <= d), default=None)
        later = min((x for x in wed if x >= d), default=None)
        if prior is None or later is None or (later - prior).days > 9:
            continue  # no bracketing week - nothing to test against
        lo, hi = sorted((by_date[prior][0], by_date[later][0]))
        if "high" in src and price < lo - 1e-9:
            out.append(
                f"  WARN: {d} weekly HIGH {price:.4f} is BELOW both bracketing "
                f"Wednesday prints ({lo:.4f}, {hi:.4f}) - probably another hub's"
            )
        elif "low" in src and price > hi + 1e-9:
            out.append(
                f"  WARN: {d} weekly LOW {price:.4f} is ABOVE both bracketing "
                f"Wednesday prints ({lo:.4f}, {hi:.4f}) - probably another hub's"
            )
    return out


def parse_agt(
    html: str, cols: list[dt.date], page_year: int, page_month: int
) -> list[tuple[dt.date, float, str]]:
    """Return ``[(date, price, source)]`` AGT prints from one weekly narrative.

    ``cols`` are the report-week column dates; the Wednesday among them is the
    narrative "yesterday" and anchors the two main Wednesday prints. Weekday
    high/lows map onto ``cols``; explicit ``Month Day`` extremes are dated
    directly (``page_year``/``page_month`` resolve the Dec/Jan boundary the
    report week straddles). Returns ``[]`` when the column dates are absent.
    """
    if not cols:
        return []
    text = re.sub(r"<[^>]+>", " ", html)  # strip tags/links inside the prose
    text = re.sub(r"\s+", " ", text)
    wednesdays = [d for d in cols if d.weekday() == _WEEKDAY["Wednesday"]]
    yesterday = wednesdays[-1] if wednesdays else cols[-1]
    last_wed = yesterday - dt.timedelta(days=7)
    by_date: dict[dt.date, tuple[float, str]] = {}

    m = _AGT_MAIN.search(text)
    if m:
        by_date[last_wed] = (float(m.group(1)), "last_wednesday")
        by_date[yesterday] = (float(m.group(2)), "wednesday")

    # Extremum prints are harvested ONLY inside an Algonquin region (see
    # :func:`agt_regions`), never over the whole page — over the page they pick
    # up whichever hub EIA happened to quote, which is how 69 of the committed
    # file's 89 extremum rows became a foreign hub's price.
    regions = agt_regions(text)

    # Weekly high/low on a named weekday within the report week (cols).
    col_by_wd = {d.weekday(): d for d in cols}
    for region in regions:
        for kind, price_s, wd_s in _AGT_HILO.findall(region):
            wd = _WEEKDAY.get(wd_s.capitalize())
            if wd is None or wd not in col_by_wd:
                continue
            d = col_by_wd[wd]
            src = f"weekly_{kind.lower()}"
            # Don't let a high/low overwrite a primary Wednesday print.
            if d not in by_date or by_date[d][1].startswith("weekly"):
                by_date[d] = (float(price_s), src)

    # Explicit-calendar-date weekly/monthly high/low (the dominant 2022 shape).
    for region in regions:
        for kind, price_s, mon_s, day_s in _AGT_CALDATE.findall(region):
            mon = _MONTHS_FULL[mon_s.capitalize()]
            try:
                d = dt.date(_resolve_year(mon, page_year, page_month), mon, int(day_s))
            except ValueError:
                continue
            src = f"{kind.lower()}_caldate"
            # Never overwrite a primary Wednesday print; a dated extreme is a more
            # precise anchor than a weekday-mapped high/low, so it may replace one.
            if d not in by_date or by_date[d][1] not in ("wednesday", "last_wednesday"):
                by_date[d] = (float(price_s), src)

    return [(d, p, s) for d, (p, s) in sorted(by_date.items())]


def _load_existing(path: Path) -> dict[dt.date, tuple[float, str]]:
    """Read a committed AGT CSV into ``{date: (price, source)}`` for merging."""
    out: dict[dt.date, tuple[float, str]] = {}
    with path.open(newline="") as fh:
        r = csv.reader(fh)
        next(r, None)  # header
        for row in r:
            if len(row) >= 3 and row[0]:
                out[dt.date.fromisoformat(row[0])] = (float(row[1]), row[2])
    return out


#: The Algonquin sentence, normalised, used to detect a STALE REPUBLISH.
#: ``(?:[^.]|\.(?=\d))`` admits a period only when a digit follows, so the
#: signature spans the sentence's own decimals ("$2.35") and stops at the
#: sentence end — a ``[^.]`` alone truncates at the first price and two
#: different weeks whose prose opens identically would collide. Whitespace
#: around the comma is tolerated because tag-stripping leaves it there
#: ("Citygate</a>, which" -> "Citygate , which").
_AGT_SENTENCE = re.compile(
    r"Algonquin Citygate\s*,\s*which serves (?:the )?Boston(?:[^.]|\.(?=\d)){0,260}",
    flags=re.I,
)


def agt_sentence(html: str) -> str | None:
    """Return the page's Algonquin narrative sentence, or ``None``.

    The identity used by the stale-republish check in :func:`main`: EIA
    occasionally publishes a new Weekly Update whose *Spot Prices* table carries
    the new report week while the **prose is last week's, verbatim**. Measured on
    the archive: 7 such pages 2018-2026 (2018-01-18, 2018-03-15, 2019-04-18,
    2022-05-12, 2022-06-23, 2023-09-14, 2024-03-07). Because the column dates
    advance and the sentence does not, every print such a page yields lands
    exactly SEVEN DAYS LATE — wrong data on ordinary days, the same class of harm
    ``fetch_transco_daily_spot``'s one-day shift did, arriving by a completely
    different route (a stale source page, not a dropped header date). A duplicate
    sentence carries no new information, so the page is skipped rather than dated.
    """
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    m = _AGT_SENTENCE.search(text)
    return m.group(0) if m else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start-year", type=int, default=2023)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument(
        "--merge",
        action="store_true",
        help="MERGE into the committed CSV instead of REPLACING it: seed from "
        "the existing file, add ONLY newly scraped dates, and assert every "
        "pre-existing row survives byte-identical. Use with a holdout-year "
        "window (e.g. --start-year 2022 --end-year 2022) to densify one year "
        "while the in-sample 2023-2025 rows stay frozen.",
    )
    args = ap.parse_args()

    # Freeze anchor: the committed data lines that must survive a merge verbatim.
    frozen_lines: set[bytes] = set()
    by_date: dict[dt.date, tuple[float, str]] = {}
    if args.merge and args.out.exists():
        by_date = _load_existing(args.out)
        raw = args.out.read_bytes().split(b"\r\n")
        frozen_lines = {ln for ln in raw[1:] if ln}  # data lines, sans header
        print(f"merge: seeded {len(by_date)} committed AGT prints (frozen)")
    seeded_dates = set(by_date)

    try:
        pages = archive_pages(args.start_year, args.end_year)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: archive index fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"archive: {len(pages)} weekly pages {args.start_year}..{args.end_year + 1}")

    fetched = failed = no_agt = added = stale = 0
    prev_sentence: str | None = None
    pairs: dict[tuple[int, int, int], tuple[dt.date, float, dt.date, float]] = {}
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL - {exc}", file=sys.stderr)
            failed += 1
            continue
        # STALE REPUBLISH: this page's prose is the previous page's, verbatim, so
        # its prints would be dated a week late (see :func:`agt_sentence`).
        sentence = agt_sentence(html)
        if sentence is not None and sentence == prev_sentence:
            print(
                f"  WARN: {y}-{m:02d}-{d:02d} repeats the previous page's "
                f"Algonquin sentence verbatim - skipped (stale republish)",
                file=sys.stderr,
            )
            stale += 1
            fetched += 1
            time.sleep(args.sleep)
            continue
        prev_sentence = sentence
        cols = column_dates(html, y, m)
        prints = parse_agt(html, cols, y, m)
        pair = main_sentence_pair(html, cols)
        if pair is not None:
            pairs[(y, m, d)] = pair
        if not prints:
            no_agt += 1
        for date, price, src in prints:
            if not (args.start_year <= date.year <= args.end_year):
                continue
            # In merge mode a committed (in-sample) date is frozen: never touch it.
            if args.merge and date in seeded_dates:
                continue
            if date not in by_date:
                added += 1
            by_date[date] = (price, src)  # later page wins (revisions)
        fetched += 1
        time.sleep(args.sleep)

    # ALIGNMENT GUARD (see :func:`chain_guard`): consecutive pages quote the same
    # Wednesday twice, so the overlap cross-checks every date anchoring. Reported,
    # never silently absorbed.
    warnings = chain_guard(pairs)
    for line in warnings:
        print(line, file=sys.stderr)
    print(
        f"chain guard: {len(warnings)} break(s) over {len(pairs)} paired pages; "
        f"{stale} stale republish page(s) skipped"
    )
    # SECOND GUARD: an extremum that cannot belong to this hub's own week.
    ext_warnings = extremum_guard(by_date)
    for line in ext_warnings:
        print(line, file=sys.stderr)
    print(f"extremum guard: {len(ext_warnings)} implausible extremum row(s)")

    # Render the merged CSV in memory first so a failed freeze-check can never
    # leave a corrupted committed file behind.
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["date", "algonquin_citygate_usd_mmbtu", "source"])
    for date in sorted(by_date):
        price, src = by_date[date]
        w.writerow([date.isoformat(), f"{price:.4f}", src])
    out_bytes = buf.getvalue().encode()

    if args.merge:
        # Byte-freeze proof: every committed data line must reappear verbatim.
        new_lines = set(out_bytes.split(b"\r\n"))
        dropped = [ln for ln in frozen_lines if ln not in new_lines]
        if dropped:
            raise SystemExit(
                f"MERGE ABORTED: {len(dropped)} committed rows would change, e.g. "
                f"{dropped[0][:60]!r} - refusing to write"
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out_bytes)
    if args.merge:
        print(
            f"fetched {fetched} pages ({failed} failed, {no_agt} without an AGT "
            f"print); merged +{added} new AGT prints, {len(frozen_lines)} committed "
            f"rows frozen -> {args.out} ({len(by_date)} total)"
        )
    else:
        print(
            f"fetched {fetched} pages ({failed} failed, {no_agt} without an AGT "
            f"print); wrote {len(by_date)} daily AGT prints -> {args.out}"
        )


if __name__ == "__main__":
    main()
