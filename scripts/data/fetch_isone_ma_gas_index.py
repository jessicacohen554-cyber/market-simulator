#!/usr/bin/env python3
"""Fetch the measured **ISO-NE Massachusetts natural gas index** monthly price and
rebuild NEISO's rows in ``data/raw/gas_basis_by_iso_month.csv`` from it.

WHY THIS EXISTS (neiso-86; diagnosis in
``results/calibration/FINDING-neiso85-2022-seasonal-inversion-2026-08-05.md``).
NEISO's hub-basis rows were sourced from the EIA ``N3050MA3`` city-gate series for
2015-2022 and 2026, and from the measured ISO-NE MA gas index only for 2023-2025.
``N3050MA3`` is an LDC city-gate **purchase-portfolio AVERAGE**: New England LDC
throughput collapses in summer, fixed pipeline reservation/demand charges spread
over a small volume, and the average $/Mcf balloons -- while the **marginal**
Algonquin basis a gas unit's offer actually tracks goes to roughly zero. Subtract
Henry Hub and the resulting "basis" is seasonally **INVERTED**: measured
``winter(Jan,Feb,Dec) - summer(Jun,Jul,Aug)`` runs -0.58 to -8.56 $/MMBtu across
2015-2022, against +2.83 / +4.54 / +10.97 in the correctly-sourced 2023-2025 rows.

This is CLAUDE.md rule 14 ``[R-ACCURATE]``'s misalignment clause exactly -- a real
measured series used on the **wrong boundary**. The remedy is a correctly-bounded
measured series, carrying **zero new degrees of freedom**: no ``ScenarioConfig``
field, no mechanism, no fitted scalar. The same swap was made for CAISO on a
different leg at caiso-84 (``caiso_citygate_spot_level``), and this repo already
rejected the ``N3050MA3`` proxy once for a single month -- see the ``source`` field
of the ``NEISO,2025,8`` row.

THE SOURCE. ISO-NE publishes a monthly "Monthly wholesale electricity prices and
demand in New England" recap on ISO Newswire. Each carries a "By the numbers"
table whose ``Average Natural Gas Price ($/MMBtu)`` row is the **Massachusetts
natural gas index price**, defined in the posts as "a volume-weighted average of
trades at four natural gas delivery points in Massachusetts, including two
Algonquin points, the Tennessee Gas Pipeline, and the Dracut Interconnect". That
is the marginal New England trading hub, and it is the SAME series and the SAME
provenance style already committed for 2023-2025.

THE TRANSFORMATION, verified against a committed row before adoption::

    basis_usd_mmbtu = (ISO-NE MA gas index) - (Henry Hub monthly mean)

    Jan-2023 recap $4.73/MMBtu - HH 3.273 = 1.457 -> 1.46 == the committed
    ``NEISO,2023,1`` row. Exact.

Henry Hub monthly means come from ``data/raw/gas-prices/henry_hub_monthly.csv``,
the same series the overlay itself reads, so the basis is consistent with how
:func:`market_sim.data.fuel.hubs.iso_hub_monthly_gas_prices` recombines it.

EXTRACTION AND ITS SELF-CHECK. Two independent figures are pulled from each post
where both exist: the "By the numbers" table row, and the narrative sentence
("The average natural gas price during January was $4.73 per million British
thermal units"). When both are present they must **agree**; a disagreement raises
rather than silently preferring one. This guards against grabbing a
prior-year/prior-month comparison column out of the same table.

WRITE SAFETY (the neiso-86 pre-registered V2/V5 gates). ``--write-basis`` rewrites
``gas_basis_by_iso_month.csv`` **line by line from the original bytes**, replacing
only NEISO rows whose year is in the authorized window and re-emitting every other
line unchanged. Non-authorized NEISO years (notably the in-sample 2023-2025 rows)
and every other ISO's rows are therefore byte-identical by construction, not by
inspection. The script re-asserts this before writing and refuses on any mismatch.

Usage::

    python scripts/data/fetch_isone_ma_gas_index.py --years 2018 2019 2020 2021 2022 2026
    python scripts/data/fetch_isone_ma_gas_index.py --years 2022 --write-basis
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
BASIS_PATH = REPO_ROOT / "data" / "raw" / "gas_basis_by_iso_month.csv"
HENRY_HUB_PATH = REPO_ROOT / "data" / "raw" / "gas-prices" / "henry_hub_monthly.csv"
INDEX_PATH = (
    REPO_ROOT / "data" / "raw" / "gas-prices" / "isone_ma_gas_index_monthly.csv"
)

# ISO Newswire exposes posts through the standard WordPress REST API, so a recap
# is addressable by its slug without knowing the (variable) publication date.
_API = "https://isonewswire.com/wp-json/wp/v2/posts"
_SLUG = "monthly-wholesale-electricity-prices-and-demand-in-new-england-{month}-{year}"
_UA = {"User-Agent": "Mozilla/5.0 (market-sim data fetch)"}

_MONTH_NAMES = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]

# "Average Natural Gas Price | ($/MMBtu**) | $8.37 | 113.0% | 11.7%" -- the
# ($/MMBtu) unit marker itself contains a '$', so anchor past it before taking
# the first dollar figure, and never cross into the percent-change columns.
_TABLE_RE = re.compile(
    r"Average\s+Natural\s+Gas\s+Price.{0,120}?\(\s*\$\s*/\s*MMBtu[^)]*\)"
    r".{0,60}?\$\s*([0-9][0-9,]*\.[0-9]+)",
    re.I | re.S,
)
# "The average natural gas price during January was $4.73 per million British
# thermal units (MMBtu)" -- the independent narrative figure.
_PROSE_RE = re.compile(
    r"average\s+natural\s+gas\s+price\s+(?:during|for|in)\s+\w+\s+"
    r"(?:was|averaged)\s+\$\s*([0-9][0-9,]*\.[0-9]+)",
    re.I | re.S,
)
# Tolerance for the table-vs-prose cross-check. The two quote the same published
# figure, so they agree exactly or to a single rounding step; this is a
# disagreement detector, not a fitted parameter.
_AGREE_TOL = 0.011


def _fetch(url: str, timeout: int = 60, retries: int = 4) -> str:
    """Return the body of ``url``, retrying transient network failures.

    Args:
        url: Absolute URL to fetch.
        timeout: Per-attempt socket timeout in seconds.
        retries: Maximum attempts before re-raising.

    Returns:
        The decoded response body.
    """
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(Request(url, headers=_UA), timeout=timeout) as fh:
                return fh.read().decode("utf-8", "replace")
        except (HTTPError, URLError, TimeoutError) as exc:  # pragma: no cover
            last = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def _plain_text(rendered_html: str) -> str:
    """Return ``rendered_html`` flattened to whitespace-normalised plain text.

    Tags become separators (not deletions) so adjacent table cells never fuse
    into a single spurious number.

    Args:
        rendered_html: The post's rendered HTML body.

    Returns:
        Unescaped, whitespace-collapsed text.
    """
    text = re.sub(r"<[^>]+>", " | ", rendered_html)
    return re.sub(r"[ \t]+", " ", html.unescape(text))


def fetch_month_index(year: int, month: int) -> tuple[float, str]:
    """Return the measured ISO-NE MA gas index ($/MMBtu) and its source URL.

    Extracts the "By the numbers" table figure and, when the post also states it
    in prose, cross-checks the two and raises on disagreement.

    Args:
        year: Calendar year of the reported month.
        month: 1-based calendar month.

    Returns:
        ``(ma_gas_index_usd_mmbtu, source_url)``.

    Raises:
        LookupError: The recap does not exist or carries no gas-price figure.
        ValueError: The table and narrative figures disagree.
    """
    slug = _SLUG.format(month=_MONTH_NAMES[month - 1], year=year)
    payload = json.loads(_fetch(f"{_API}?slug={slug}&_fields=link,content"))
    if not payload:
        raise LookupError(f"no ISO-NE recap published for {year}-{month:02d}")
    link = payload[0]["link"]
    text = _plain_text(payload[0]["content"]["rendered"])

    table = _TABLE_RE.search(text)
    prose = _PROSE_RE.search(text)
    if table is None and prose is None:
        raise LookupError(f"no gas-price figure found in {link}")

    t_val = float(table.group(1).replace(",", "")) if table else None
    p_val = float(prose.group(1).replace(",", "")) if prose else None
    if t_val is not None and p_val is not None and abs(t_val - p_val) > _AGREE_TOL:
        raise ValueError(
            f"{year}-{month:02d}: table ${t_val} disagrees with narrative "
            f"${p_val} in {link} -- refusing to guess"
        )
    return (t_val if t_val is not None else p_val), link


def load_henry_hub_monthly() -> dict[tuple[int, int], float]:
    """Return ``{(year, month): henry_hub_monthly_mean_usd_mmbtu}``.

    Returns:
        The measured Henry Hub monthly series backing the basis subtraction.
    """
    out: dict[tuple[int, int], float] = {}
    with HENRY_HUB_PATH.open(newline="") as fh:
        for row in csv.DictReader(fh):
            out[(int(row["year"]), int(row["month"]))] = float(row["price_usd_mmbtu"])
    return out


def build_rows(years: list[int], sleep: float = 0.4) -> list[dict[str, object]]:
    """Fetch every available month for ``years`` and derive the NEISO basis rows.

    Months with no published recap are skipped with a warning rather than
    guessed (rule 14: never invent a measured value).

    Args:
        years: Calendar years to cover.
        sleep: Delay between requests, to stay polite to the source.

    Returns:
        One dict per resolved month with the index, the basis and the source URL.
    """
    hh = load_henry_hub_monthly()
    rows: list[dict[str, object]] = []
    for year in years:
        for month in range(1, 13):
            try:
                index, link = fetch_month_index(year, month)
            except LookupError as exc:
                print(f"  .. skip {year}-{month:02d}: {exc}", file=sys.stderr)
                continue
            hh_m = hh.get((year, month))
            if hh_m is None:
                print(
                    f"  .. skip {year}-{month:02d}: no Henry Hub monthly mean",
                    file=sys.stderr,
                )
                continue
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "ma_gas_index_usd_mmbtu": round(index, 4),
                    "henry_hub_usd_mmbtu": round(hh_m, 4),
                    "basis_usd_mmbtu": round(index - hh_m, 4),
                    "source_url": link,
                }
            )
            print(
                f"  {year}-{month:02d}  index ${index:>7.2f}  "
                f"- HH ${hh_m:>6.3f}  = basis {index - hh_m:>+8.4f}"
            )
            time.sleep(sleep)
    return rows


def write_index_csv(rows: list[dict[str, object]]) -> None:
    """Write the measured index series to ``isone_ma_gas_index_monthly.csv``.

    Existing years are merged, not dropped, so repeated runs over different
    windows accumulate rather than truncate.

    Args:
        rows: Rows from :func:`build_rows`.
    """
    fields = [
        "year",
        "month",
        "ma_gas_index_usd_mmbtu",
        "henry_hub_usd_mmbtu",
        "basis_usd_mmbtu",
        "source_url",
    ]
    merged: dict[tuple[int, int], dict[str, object]] = {}
    if INDEX_PATH.exists():
        with INDEX_PATH.open(newline="") as fh:
            for row in csv.DictReader(fh):
                merged[(int(row["year"]), int(row["month"]))] = row
    for row in rows:
        merged[(int(row["year"]), int(row["month"]))] = row
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for key in sorted(merged):
            writer.writerow(merged[key])
    print(f"wrote {INDEX_PATH.relative_to(REPO_ROOT)} ({len(merged)} rows)")


def write_basis_csv(rows: list[dict[str, object]], years: list[int]) -> None:
    """Rewrite NEISO's authorized-year rows in ``gas_basis_by_iso_month.csv``.

    Rebuilds the file from its ORIGINAL LINES, substituting only NEISO rows whose
    year is in ``years``. Every other line -- other ISOs, and NEISO years outside
    the authorized window such as the in-sample 2023-2025 rows -- is re-emitted
    unchanged, so the pre-registered V2/V5 invariance gates hold by construction.
    New months inside an authorized year are inserted in (year, month) order.

    Args:
        rows: Rows from :func:`build_rows`.
        years: The authorized year window; NEISO rows outside it are untouched.

    Raises:
        RuntimeError: A line outside the authorized NEISO scope would change.
    """
    hub_label = "Algonquin Citygate (ISO-NE MA gas index)"
    target = {
        (int(r["year"]), int(r["month"])): r for r in rows if int(r["year"]) in years
    }
    original = BASIS_PATH.read_text().splitlines(keepends=True)
    header, body = original[0], original[1:]

    out: list[str] = [header]
    seen: set[tuple[int, int]] = set()
    emitted_years: set[int] = set()

    def _new_line(key: tuple[int, int]) -> str:
        row = target[key]
        return (
            f"NEISO,{key[0]},{key[1]},{hub_label},"
            f"{row['basis_usd_mmbtu']},{row['source_url']}\n"
        )

    def _authorized(line: str) -> tuple[int, int] | None:
        """Return the (year, month) key of an authorized NEISO line, else None."""
        parts = line.split(",", 3)
        if len(parts) < 3 or parts[0] != "NEISO" or not parts[1].isdigit():
            return None
        return (int(parts[1]), int(parts[2])) if int(parts[1]) in years else None

    # Index the authorized block's existing lines first, so each year is emitted
    # exactly once as a whole month-ordered block. Emitting per-line and
    # opportunistically inserting "the next month" double-writes any month that
    # already has a row and whose predecessor is also in the window.
    existing: dict[int, dict[int, str]] = {}
    for line in body:
        key = _authorized(line)
        if key is not None:
            existing.setdefault(key[0], {})[key[1]] = line

    for line in body:
        key = _authorized(line)
        if key is None:
            out.append(line)  # untouched bytes: other ISOs / other NEISO years
            continue
        year = key[0]
        if year in emitted_years:
            continue  # this year's whole block was emitted at its first row
        emitted_years.add(year)
        months = sorted(
            set(existing.get(year, {})) | {m for (y, m) in target if y == year}
        )
        for month in months:
            if (year, month) in target:
                out.append(_new_line((year, month)))
                seen.add((year, month))
            else:
                # Authorized year, but no measured recap for this month: keep the
                # existing row rather than deleting measured coverage.
                print(f"  !! {year}-{month:02d}: no measured index; row LEFT AS-IS")
                out.append(existing[year][month])

    missing = sorted(set(target) - seen)
    if missing:
        raise RuntimeError(f"rows could not be placed in row order: {missing}")

    keys = [ln.split(",", 3)[:3] for ln in out[1:] if ln.strip()]
    if len(keys) != len({tuple(k) for k in keys}):
        raise RuntimeError(
            "REFUSING TO WRITE: duplicate (iso, year, month) rows produced"
        )

    # Re-assert the pre-registered gates against the ORIGINAL bytes before writing.
    def _outside(lines: list[str]) -> list[str]:
        return [
            ln
            for ln in lines
            if not (
                len(ln.split(",", 3)) >= 3
                and ln.split(",", 3)[0] == "NEISO"
                and ln.split(",", 3)[1].isdigit()
                and int(ln.split(",", 3)[1]) in years
            )
        ]

    if _outside(body) != _outside(out[1:]) or out[0] != header:
        raise RuntimeError(
            "REFUSING TO WRITE: a line outside the authorized NEISO window changed"
        )
    BASIS_PATH.write_text("".join(out))
    print(
        f"wrote {BASIS_PATH.relative_to(REPO_ROOT)} "
        f"({len(seen)} NEISO rows in {sorted(years)})"
    )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--years", type=int, nargs="+", required=True)
    parser.add_argument("--sleep", type=float, default=0.4)
    parser.add_argument(
        "--write-basis",
        action="store_true",
        help="also rewrite NEISO's authorized-year rows in gas_basis_by_iso_month.csv",
    )
    args = parser.parse_args()

    print(f"fetching ISO-NE MA gas index for {sorted(args.years)} ...")
    rows = build_rows(sorted(args.years), sleep=args.sleep)
    if not rows:
        raise SystemExit("no months resolved -- nothing written")
    write_index_csv(rows)
    if args.write_basis:
        write_basis_csv(rows, sorted(args.years))


if __name__ == "__main__":
    main()
