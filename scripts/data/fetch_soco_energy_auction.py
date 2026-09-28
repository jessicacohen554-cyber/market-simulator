#!/usr/bin/env python3
"""Fetch Southern Company Energy Auction clearing-price files, 2019-2025, as published.

Writes the files verbatim under ``data/raw/soco-energy-auction/`` (``hourly/`` for the
hour-ahead auction, ``daily/`` for the day-ahead auction), plus ``links.csv`` (every
index link in the window with its HTTP status and byte count) and ``SHA256SUMS.txt``.
REPORTED-ONLY (owner ruling 2026-09-28, "Yes, reported-only"; lane soco-84): the series
feeds no gate, no scorer and no LP.

Source: the public auction index ``https://www.southerngeneration.com/auctionpub/index.html``
links one file per auction date and kind, ``ClearingData/YYYY-MM-DD_{HOURLY,DAILY}_
CLEARING_PRICES.CSV`` (file spec: ``auctionpub/FileSpecification.doc``). Only dates on
which an auction cleared are listed, so the series is sparse by construction. Some
listed links return HTTP 404; they are recorded in ``links.csv`` and skipped.

Usage::

    python3 scripts/data/fetch_soco_energy_auction.py [--years 2019 ... 2025]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))
from market_sim.config.paths import SOCO_ENERGY_AUCTION_DIR  # noqa: E402

BASE = "https://www.southerngeneration.com/auctionpub/"
INDEX = BASE + "index.html"
LINK_RE = re.compile(
    r"ClearingData/(\d{4})-(\d{2})-(\d{2})_(HOURLY|DAILY)_CLEARING_PRICES\.CSV"
)
KIND_DIR = {"HOURLY": "hourly", "DAILY": "daily"}
DEFAULT_YEARS = tuple(range(2019, 2026))


def _get(url: str, tries: int = 4) -> tuple[int, bytes]:
    """GET with a small retry on transport errors; returns (status, body)."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except urllib.error.URLError:
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"transport failure: {url}")


def fetch(years=DEFAULT_YEARS, out: Path = SOCO_ENERGY_AUCTION_DIR) -> list[dict]:
    """Download every in-window file the index links; return the link records."""
    status, body = _get(INDEX)
    if status != 200:
        raise RuntimeError(f"index HTTP {status}")
    links = sorted({m.group(0) for m in LINK_RE.finditer(body.decode("latin-1"))})
    rows = []
    for rel in links:
        m = LINK_RE.fullmatch(rel)
        if int(m.group(1)) not in years:
            continue
        st, data = _get(BASE + rel)
        name = rel.split("/", 1)[1]
        rec = {"file": name, "kind": m.group(4), "http_status": st, "bytes": len(data)}
        if st == 200:
            d = out / KIND_DIR[m.group(4)]
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_bytes(data)
        rows.append(rec)
    with (out / "links.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "kind", "http_status", "bytes"])
        w.writeheader()
        w.writerows(rows)
    files = sorted(p for p in out.rglob("*.CSV"))
    (out / "SHA256SUMS.txt").write_text(
        "".join(
            f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}\n"
            for p in files
        )
    )
    return rows


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    a = ap.parse_args()
    rows = fetch(set(a.years))
    ok = sum(r["http_status"] == 200 for r in rows)
    print(f"{len(rows)} links, {ok} HTTP 200, {len(rows) - ok} other")


if __name__ == "__main__":
    main()
