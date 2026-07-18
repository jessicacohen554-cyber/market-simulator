"""Fetch NRC daily Power Reactor Status annual files.

Downloads the NRC's public Power Reactor Status Report cumulative annual
text files (pipe-delimited ``ReportDt|Unit|Power`` — one row per US power
reactor per day, ``Power`` = percent of licensed thermal power at the
morning report) into ``data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt``.

These are the immutable raw source for
``scripts/data/derive_nuclear_availability.py`` (the per-ISO per-reactor daily
nuclear availability overlay, PJM first). NRC status reports are US
government public-domain works, so the raw files are committed to the repo
(no redistribution restriction — unlike the PJM energy-offers corpus, see
docs/data-licensing.md).

Source: https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/

Usage::

    python scripts/data/fetch_nrc_reactor_status.py               # 2023-2025
    python scripts/data/fetch_nrc_reactor_status.py --years 2024
    python scripts/data/fetch_nrc_reactor_status.py --force       # re-download
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO / "data" / "raw" / "nrc-reactor-status"
URL_TMPL = (
    "https://www.nrc.gov/reading-rm/doc-collections/event-status/"
    "reactor-status/{year}/{year}PowerStatus.txt"
)
RETRIES = 4


def fetch_year(year: int, force: bool = False) -> Path:
    """Download one annual file (skipped when present unless ``force``)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{year}PowerStatus.txt"
    if out.exists() and not force:
        print(f"  {out.name}: exists ({out.stat().st_size:,} bytes) — skipped")
        return out
    url = URL_TMPL.format(year=year)
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                data = resp.read()
            break
        except OSError as exc:  # includes HTTP/URL errors
            if attempt == RETRIES - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  {year}: {exc} — retry in {wait}s")
            time.sleep(wait)
    text = data.decode("utf-8-sig")
    header = text.splitlines()[0].strip()
    if header != "ReportDt|Unit|Power":
        raise ValueError(f"{year}: unexpected header {header!r}")
    out.write_text(text)
    print(f"  {out.name}: {len(data):,} bytes, {text.count(chr(10)):,} lines")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    for year in args.years:
        fetch_year(year, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
