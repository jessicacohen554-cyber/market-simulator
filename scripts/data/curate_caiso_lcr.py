#!/usr/bin/env python3
"""Transcribe CAISO's published Local Capacity Technical (LCT) study results.

Reads the annual ``Final<Y>LocalCapacityTechnicalReport.pdf`` and emits the
non-``branch_group`` rows of the capacity-deliverability registry
``data/raw/capacity-deliverability/caiso/caiso.csv`` — the RA-saturation half
of ``capacity_deliverability_limits`` (the MIC/seam-import half is
``curate_caiso_mic.py``). Three row families:

* ``local_area`` / ``requirement`` — the 10 local areas' LCR need, from the
  executive summary's "<Y> Local Capacity Needs" table (each delivery year is
  read from **its own** study report, never from a neighbouring report's
  estimated columns);
* ``zone`` / ``peak_load`` — NP26 and SP26 CEC load forecast, from §3.2's
  "Total Zonal Resource Needs" table;
* ``rto`` / ``system_requirement`` — the planning reserve margin the same
  §3.2 table applies, as a per-unit fraction. **Citation caveat:** the
  committed 2023-2025 rows take the PRM from a CPUC fact sheet (0.16 / 0.17 /
  0.17) rather than from the study, because each study is published a year
  ahead and its stated margin can predate a later CPUC decision — the 2023
  study (April 2022) still says 15%, but D.23-06-029 raised the PRM before
  that delivery year. For 2018-2022 there is no such lag: 15% was the
  operative CPUC minimum for the whole window and every study that carries
  the §3.2 table states it, so the study is a sound primary citation for
  those years. ``--verify`` therefore checks the requirement and zone rows
  only; the PRM row is a deliberate, documented source substitution.

**Table vintage (why the value taken is "the last number on the area row").**
The needs table was restructured twice inside 2018-2025:

* 2018-2019: Category B and Category C(with operating procedure), each split
  into ``Existing Capacity Needed`` / ``Deficiency`` / ``Total``; area names
  wrap across two lines;
* 2020: ``Capacity Needed`` given separately for Category B and Category C;
* 2021+: NERC TPL-001-4 P-categories collapsed the table to ONE
  ``Capacity Needed`` column, which carries the deficiency inside the value
  (flagged with ``*``).

Across all three layouts the **last numeric cell of an area row** is the same
quantity: the most-severe-criterion total LCR need including any deficiency —
which is what the 2021+ single column reports. That is the value transcribed,
and ``--verify`` asserts it reproduces the committed 2023-2025 rows exactly.
Pre-2021 rows are still a *criterion-vintage* difference (Category C vs the
P-category studies), so they are labelled as such in ``source_page`` and
graded DEGRADED in the holdout register rather than passed off as equivalent.

Usage:
    python scripts/data/curate_caiso_lcr.py --verify 2023 2024 2025
    python scripts/data/curate_caiso_lcr.py --years 2018 2019 2020 2021 2022 --merge
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

OUT_PATH = RAW_DATA_DIR / "capacity-deliverability" / "caiso" / "caiso.csv"

FIELDNAMES = [
    "iso",
    "delivery_year",
    "season",
    "area",
    "area_type",
    "metric",
    "value_mw",
    "value_pu",
    "source_doc",
    "source_page",
]

# CAISO moved the report between hosts and renamed it repeatedly; the pattern
# that actually serves the year is what lands in each row's ``source_doc``.
LCR_URL_PATTERNS: tuple[str, ...] = (
    "https://www.caiso.com/Documents/Final{year}LocalCapacityTechnicalReport.pdf",
    "https://stakeholdercenter.caiso.com/InitiativeDocuments/"
    "Final{year}LocalCapacityTechnicalReport.pdf",
    "https://stakeholdercenter.caiso.com/InitiativeDocuments/"
    "Final-{year}-Local-Capacity-Technical-Report.pdf",
)

# Registry display name -> the regex matching CAISO's own row label. The
# report inserts stray spaces around the slashes and wraps the longer names
# across two lines (2018/2019 layout), so each name is matched loosely.
AREA_PATTERNS: dict[str, str] = {
    "Humboldt": r"Humboldt",
    "North Coast/North Bay": r"North\s*Coast\s*/\s*\n?\s*North\s*Bay",
    "Sierra": r"Sierra",
    "Stockton": r"Stockton",
    "Greater Bay": r"Greater\s*Bay",
    "Greater Fresno": r"Greater\s*Fresno",
    "Kern": r"Kern",
    "Big Creek/Ventura": r"Big\s*Creek\s*/\s*\n?\s*Ventura",
    "LA Basin": r"LA\s*Basin",
    "San Diego/Imperial Valley": r"San\s*Diego\s*/\s*\n?\s*Imperial\s*Valley",
}

# One area row: the label, then 3-9 numeric cells (layout-dependent), each
# optionally deficiency-flagged with ``*``. Only the LAST cell is used.
_CELLS = r"((?:\s+-?\d+\*?){3,9})\s*(?:\n|$)"

# §3.2 zonal table rows: ``SP26 <load> <reserves> …`` / ``NP26=NP15+ZP26 …``.
_ZONE_ROW = re.compile(r"^\s*(SP26|NP26)(?:=[\w+]+)?\s+(\d+)\s+(\d+)", re.M)
# The reserve-margin percentage, from the same table's header or its legend.
_RESERVE_PCT = re.compile(r"(\d+)%\s*\n?\s*reserves|Reserve Margin is (\d+)%")


def fetch_lcr_pdf(year: int, cache_dir: Path) -> tuple[Path, str]:
    """Download the year's LCT report, returning ``(local_path, source_url)``."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"caiso_lcr_{year}.pdf"
    for pattern in LCR_URL_PATTERNS:
        url = pattern.format(year=year)
        try:
            with urllib.request.urlopen(url, timeout=180) as resp:
                payload = resp.read()
        except Exception:  # noqa: BLE001 — try the next naming pattern
            continue
        if payload[:4] == b"%PDF" and len(payload) > 100_000:
            path.write_bytes(payload)
            return path, url
    raise FileNotFoundError(f"no LCT report found for {year} (tried every pattern)")


def _needs_page(pdf_path: Path, year: int) -> tuple[str, int]:
    """Return ``(text, 1-based page)`` of the year's own LCR-needs table.

    The executive summary prints the studied year's table first and several
    comparison years (a future year, the prior year, sometimes two estimated
    years) after it, so the page is located by the studied year's own heading
    and the text is truncated at the next table heading — otherwise a
    comparison year's numbers would be read instead.
    """
    from pypdf import PdfReader

    heading = re.compile(
        rf"{year}\s+Local\s+Capacity\s+(?:Needs|Requirements)", re.IGNORECASE
    )
    for i, page in enumerate(PdfReader(pdf_path).pages[:12]):
        text = page.extract_text() or ""
        m = heading.search(text)
        if not m:
            continue
        rest = text[m.end() :]
        nxt = re.search(r"\d{4}\s+Local\s+Capacity\s+(?:Needs|Requirements)", rest)
        return (rest[: nxt.start()] if nxt else rest), i + 1
    raise ValueError(f"{pdf_path.name}: no '{year} Local Capacity Needs' table found")


def parse_requirements(pdf_path: Path, year: int) -> tuple[dict[str, int], int]:
    """Return ``({area: lcr_need_mw}, source_page)`` for one study report."""
    text, page = _needs_page(pdf_path, year)
    out: dict[str, int] = {}
    for area, pattern in AREA_PATTERNS.items():
        m = re.search(pattern + _CELLS, text)
        if not m:
            raise ValueError(f"{pdf_path.name}: no row parsed for {area!r}")
        out[area] = int(m.group(1).split()[-1].rstrip("*"))
    return out, page


def parse_zonal(pdf_path: Path) -> tuple[dict[str, int], float | None, int] | None:
    """Return ``({zone: peak_load_mw}, reserve_pu, page)``, or None if absent.

    The §3.2 zonal-needs table was introduced in the 2020 study; the 2018 and
    2019 reports carry no zonal section at all, so those years legitimately
    have no zone/rto rows rather than a substituted value.
    """
    from pypdf import PdfReader

    for i, page in enumerate(PdfReader(pdf_path).pages[:60]):
        text = page.extract_text() or ""
        if "Total Zonal Resource Need" not in text:
            continue
        zones = {z: int(load) for z, load, _ in _ZONE_ROW.findall(text)}
        if not zones:
            continue
        m = _RESERVE_PCT.search(text)
        pct = int(m.group(1) or m.group(2)) / 100.0 if m else None
        return zones, pct, i + 1
    return None


def rows_for_year(year: int, cache_dir: Path) -> list[dict]:
    """Return every registry row this script owns for one delivery year."""
    pdf_path, url = fetch_lcr_pdf(year, cache_dir)
    reqs, page = parse_requirements(pdf_path, year)
    # Pre-2021 reports report Category B/C rather than the P-category study
    # the 2021+ single column reports; stamp the criterion into the citation
    # so the vintage difference is visible in the data, not only in the docs.
    tag = f"p{page}" if year >= 2021 else f"p{page} Category C total"
    rows = [
        {
            "iso": "CAISO",
            "delivery_year": year,
            "season": "annual",
            "area": area,
            "area_type": "local_area",
            "metric": "requirement",
            "value_mw": mw,
            "value_pu": "",
            "source_doc": url,
            "source_page": tag,
        }
        for area, mw in reqs.items()
    ]

    zonal = parse_zonal(pdf_path)
    if zonal is None:
        print(f"    {year}: no §3.2 zonal table (section postdates this report)")
        return rows
    zones, reserve_pu, zpage = zonal
    rows += [
        {
            "iso": "CAISO",
            "delivery_year": year,
            "season": "annual",
            "area": zone,
            "area_type": "zone",
            "metric": "peak_load",
            "value_mw": load,
            "value_pu": "",
            "source_doc": url,
            "source_page": "Table 3.2-1",
        }
        for zone, load in zones.items()
    ]
    if reserve_pu is not None:
        rows.append(
            {
                "iso": "CAISO",
                "delivery_year": year,
                "season": "annual",
                "area": "CAISO",
                "area_type": "rto",
                "metric": "system_requirement",
                "value_mw": "",
                "value_pu": reserve_pu,
                "source_doc": url,
                "source_page": f"Table 3.2-1 (p{zpage}) CPUC minimum PRM",
            }
        )
    return rows


def verify(years: list[int], cache_dir: Path) -> int:
    """Assert the parser reproduces the committed rows for ``years``."""
    import pandas as pd

    committed = pd.read_csv(OUT_PATH)
    bad = 0
    for year in years:
        pdf_path, _ = fetch_lcr_pdf(year, cache_dir)
        sub = committed[committed["delivery_year"] == year]

        want = dict(
            zip(
                sub[(sub.area_type == "local_area") & (sub.metric == "requirement")][
                    "area"
                ],
                sub[(sub.area_type == "local_area") & (sub.metric == "requirement")][
                    "value_mw"
                ].astype(int),
                strict=True,
            )
        )
        got, _ = parse_requirements(pdf_path, year)
        want_z = dict(
            zip(
                sub[sub.area_type == "zone"]["area"],
                sub[sub.area_type == "zone"]["value_mw"].astype(int),
                strict=True,
            )
        )
        zonal = parse_zonal(pdf_path)
        got_z = zonal[0] if zonal else {}

        if got == want and got_z == want_z:
            print(f"  {year}: MATCH ({len(got)} local areas, {len(got_z)} zones)")
            continue
        bad += 1
        print(f"  {year}: MISMATCH")
        for area in sorted(set(want) | set(got)):
            if want.get(area) != got.get(area):
                print(
                    f"    {area:26s} committed={want.get(area)} parsed={got.get(area)}"
                )
        for zone in sorted(set(want_z) | set(got_z)):
            if want_z.get(zone) != got_z.get(zone):
                print(
                    f"    {zone:26s} committed={want_z.get(zone)} parsed={got_z.get(zone)}"
                )
    return 1 if bad else 0


def main() -> None:
    """Verify against committed years, or transcribe new delivery years."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--verify",
        nargs="+",
        type=int,
        default=None,
        help="assert the parser reproduces these already-committed delivery "
        "years exactly, then exit (the lineage proof for a back-year run)",
    )
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--merge",
        action="store_true",
        help="append to the committed registry, keeping every existing row "
        "byte-identical (a row already present is left alone)",
    )
    ap.add_argument("--cache-dir", type=Path, default=Path("/tmp/caiso-lcr-pdfs"))
    args = ap.parse_args()

    if args.verify:
        print("verifying parser against committed rows:")
        sys.exit(verify(args.verify, args.cache_dir))
    if not args.years:
        ap.error("pass --years or --verify")

    new_rows: list[dict] = []
    for year in sorted(args.years):
        year_rows = rows_for_year(year, args.cache_dir)
        print(f"  {year}: {len(year_rows)} rows")
        new_rows.extend(year_rows)

    if not args.merge:
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(new_rows)
        return

    existing = list(csv.DictReader(OUT_PATH.open()))
    have = {
        (r["delivery_year"], r["area"], r["area_type"], r["metric"]) for r in existing
    }
    added = [
        r
        for r in new_rows
        if (str(r["delivery_year"]), r["area"], r["area_type"], r["metric"]) not in have
    ]
    # Byte-APPEND, never rewrite (see curate_caiso_mic.py): the committed file
    # carries mixed line endings from successive hand-appends.
    blob = OUT_PATH.read_bytes()
    buf = io.StringIO()
    csv.DictWriter(buf, fieldnames=FIELDNAMES).writerows(added)
    with OUT_PATH.open("ab") as fh:
        if blob and not blob.endswith((b"\n", b"\r")):
            fh.write(b"\r\n")
        fh.write(buf.getvalue().encode())
    print(
        f"merged: kept {len(existing)} committed rows byte-frozen, added {len(added)}"
    )


if __name__ == "__main__":
    main()
