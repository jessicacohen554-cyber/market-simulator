"""Fetch + consolidate MISO's Binding Sub-Regional Power Balance Constraint reports.

Source: the public daily market reports
``https://docs.misoenergy.org/marketreports/YYYYMMDD_{da,rt}_pbc.csv``
(no auth) — the measured binding record for the Regional Directional
Transfer (RDT) constraint: one row per (constraint, interval) with a nonzero
preliminary shadow price, plus the live demand-curve breakpoints in force
(the $40/$500 TCDC; 2024 MISO SOM §III.B).

Filename date is the PUBLISH date: a DA file carries market date
publish+1 day; an RT file carries market date publish-1 day. This script
downloads the padded publish window for the requested market-date years,
then consolidates rows VERBATIM (no transformation — the raw home stays a
faithful source mirror) into one gzipped CSV per (market, market-date-year):

    data/raw/transfer-constraint-binding/MISO/miso_pbc_<market>_<year>.csv.gz

Quarantine guard (CLAUDE.md rule 22): market dates outside the 2023-2025
train window are REFUSED unless ``--allow-out-of-train`` is passed under a
session-logged owner authorization — edge publish-window files naturally
contain a few out-of-train rows (e.g. the 2026-01-01 market date inside the
RT file published 2026-01-02), and those rows are dropped at consolidation.

Offline re-consolidation from an existing download directory:
``--from-dir <dir>`` skips the network entirely.
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "transfer-constraint-binding" / "MISO"
BASE_URL = "https://docs.misoenergy.org/marketreports"

# CLAUDE.md rule 22: the calibration train window. Intake outside it needs
# explicit, session-logged owner authorization (--allow-out-of-train).
TRAIN_YEARS = (2023, 2024, 2025)

# Publish-window padding around the market-date span (DA leads by 1 day,
# RT lags by 1 day; a few extra days absorb publication hiccups).
PUBLISH_PAD_DAYS = 5

HEADER = (
    "MARKET_HOUR_EST, CONSTRAINT_NAME, PRELIMINARY_SHADOW_PRICE, CURVETYPE,"
    " BP1, PC1, BP2, PC2, BP3, PC3, BP4, PC4, OVERRIDE, REASON"
)

_DATA_ROW = re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2},")


def _daterange(start: date, end: date):
    """Yield dates from ``start`` to ``end`` inclusive."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def download(years: list[int], dest: Path) -> None:
    """Download the padded publish window for ``years`` into ``dest``."""
    dest.mkdir(parents=True, exist_ok=True)
    start = date(min(years), 1, 1) - timedelta(days=PUBLISH_PAD_DAYS)
    end = date(max(years), 12, 31) + timedelta(days=PUBLISH_PAD_DAYS)
    n = 0
    for d in _daterange(start, end):
        for market in ("da", "rt"):
            name = f"{d.strftime('%Y%m%d')}_{market}_pbc.csv"
            out = dest / name
            if out.exists() and out.stat().st_size > 0:
                continue
            url = f"{BASE_URL}/{name}"
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    out.write_bytes(resp.read())
                n += 1
            except Exception as exc:  # noqa: BLE001 — log and continue
                print(f"WARN {name}: {exc}", file=sys.stderr)
    print(f"downloaded {n} new files into {dest}")


def consolidate(src: Path, years: list[int]) -> list[Path]:
    """Concatenate verbatim data rows into per-(market, year) raw files.

    Rows are kept exactly as posted; the only selection is (a) the market
    run from the source filename and (b) the row's own market-date year.
    Rows are de-duplicated verbatim and sorted by their timestamp prefix
    (files can overlap at publish-window edges).
    """
    rows: dict[tuple[str, int], set[str]] = {}
    for f in sorted(src.glob("*_pbc.csv")):
        market = "da" if f.name.endswith("_da_pbc.csv") else "rt"
        for line in f.read_text(errors="replace").splitlines():
            line = line.strip()
            if not _DATA_ROW.match(line):
                continue
            year = int(line[6:10])
            if year not in years:
                continue
            rows.setdefault((market, year), set()).add(line)
    out_paths: list[Path] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for (market, year), lines in sorted(rows.items()):
        # Sort by parsed timestamp (MM/DD/YYYY HH:MM:SS prefix).
        def _key(ln: str) -> tuple:
            ts = ln.split(",", 1)[0]
            return (ts[6:10], ts[0:2], ts[3:5], ts[11:])

        out = RAW_DIR / f"miso_pbc_{market}_{year}.csv.gz"
        with gzip.open(out, "wt") as fh:
            fh.write(HEADER + "\n")
            for ln in sorted(lines, key=_key):
                fh.write(ln + "\n")
        print(f"{out.name}: {len(lines)} rows")
        out_paths.append(out)
    return out_paths


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(TRAIN_YEARS),
        help="market-date years to consolidate (default: the train window)",
    )
    ap.add_argument(
        "--from-dir",
        type=Path,
        default=None,
        help="consolidate an existing download directory (no network)",
    )
    ap.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="where to stage per-day downloads (default: <raw>/_daily)",
    )
    ap.add_argument(
        "--allow-out-of-train",
        action="store_true",
        help=(
            "permit market-date years outside 2023-2025 (rule 22: requires "
            "explicit session-logged owner authorization)"
        ),
    )
    args = ap.parse_args()

    bad = [y for y in args.years if y not in TRAIN_YEARS]
    if bad and not args.allow_out_of_train:
        raise SystemExit(
            f"years {bad} are outside the 2023-2025 train window (CLAUDE.md "
            "rule 22). Pass --allow-out-of-train ONLY under explicit, "
            "session-logged owner authorization."
        )

    src = args.from_dir
    if src is None:
        src = args.download_dir or (RAW_DIR / "_daily")
        download(args.years, src)
    consolidate(src, args.years)


if __name__ == "__main__":
    main()
