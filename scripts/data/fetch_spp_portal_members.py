#!/usr/bin/env python
"""Fetch the SPP portal payloads published as ZIP MEMBERS or in the 2025 live
per-month / per-day layout — the shapes ``fetch_spp_alt_portal.py`` does NOT write.

**There are TWO SPP portal producers and they are complements, not alternatives.**
Lane SPP-14 ran as two parallel sessions and both landings are in ``data/raw/spp-*``,
so both scripts are needed to regenerate those directories:

* ``fetch_spp_alt_portal.py`` — writes SPP's **whole published archives**
  (``hourly-load-<yr>.zip``, ``da-mcp-<yr>.zip``, root-level ``GenMix_<yr>.csv``),
  reading single members by HTTP ``Range`` off the zip central directory.
* ``fetch_spp_portal_members.py`` (this file) — **extracts members** from those same
  archives (monthly ``HOURLY_LOAD-YYYYMM.csv``, ``RTBM_MCP_<yr>.csv.zip``,
  ``RTBM-BC-YEARLY-<yr>.csv.zip``) and fetches the **2025 live layout**, which SPP has
  not yet rolled into a year-zip (12 monthly load CSVs, 12 monthly BC roll-ups, 365
  daily ``DA-MCP-*.csv``).

It deliberately does **not** write ``DA-MCP-<yr>.zip``: byte-identical to the
``da-mcp-<yr>.zip`` the other producer writes, differing only in filename case, which
collides on a case-insensitive filesystem. Dropped in the PR #5342 salvage 2026-09-07.

The route (anonymous HTTPS, no UI token, no cookie)::

    listing   GET https://portal.spp.org/file-browser-api/?fsName=<fs>&path=<p>&type=folder
    download  GET https://portal.spp.org/file-browser-api/download/<fs>?path=<p>

Usage::

    python scripts/data/fetch_spp_portal_members.py --out-root data/raw [--only hourly-load ...]
    python scripts/data/fetch_spp_portal_members.py --dry-run

Verify against the directory's ``SHA256SUMS.txt`` afterwards; a mismatch means SPP
re-published the file (they do replace files in place) and is a finding, not something
to overwrite silently.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import subprocess
import sys
import urllib.parse
import zipfile
from pathlib import Path

BASE = "https://portal.spp.org/file-browser-api/download/"
YEARS_ARCHIVED = (2023, 2024)
MONTHS = [f"{m:02d}" for m in range(1, 13)]


def _dl(fs: str, path: str, timeout: int = 1800) -> bytes:
    """Download one portal file (whole) via curl; raise on HTTP failure."""
    url = BASE + fs + "?path=" + urllib.parse.quote(path, safe="")
    p = subprocess.run(
        ["curl", "-sS", "--fail", "-m", str(timeout), url], capture_output=True
    )
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"curl failed {url}: {p.stderr[:200]!r}")
    return p.stdout


def _members(zip_bytes: bytes, pred) -> dict[str, bytes]:
    """Return ``{basename: bytes}`` for the zip members ``pred(name)`` selects."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    return {n.rsplit("/", 1)[-1]: z.read(n) for n in z.namelist() if pred(n)}


def plan(only: set[str] | None):
    """Yield ``(product_dir, filename, fetcher)`` triples for every landed payload."""
    want = lambda k: (only is None) or (k in only)  # noqa: E731
    if want("hourly-load"):
        for y in YEARS_ARCHIVED:
            yield (
                "spp-hourly-load",
                f"HOURLY_LOAD-{y}.zip",
                lambda y=y: _members(
                    _dl("hourly-load", f"/{y}/{y}.zip"),
                    lambda n: n.rsplit("/", 1)[-1].startswith("HOURLY_LOAD-"),
                ),
            )
        for m in MONTHS:
            yield (
                "spp-hourly-load",
                f"HOURLY_LOAD-2025{m}.csv",
                lambda m=m: _dl("hourly-load", f"/2025/HOURLY_LOAD-2025{m}.csv"),
            )
    if want("or-mcp"):
        for y in YEARS_ARCHIVED:
            yield (
                "spp-or-mcp",
                f"RTBM_MCP_{y}.csv.zip",
                lambda y=y: _members(
                    _dl("rtbm-mcp", f"/{y}/{y}.zip"),
                    lambda n: n.endswith(f"RTBM_MCP_{y}.csv.zip"),
                ),
            )
        yield (
            "spp-or-mcp",
            "RTBM_MCP_2025.csv.zip",
            lambda: _dl("rtbm-mcp", "/2025/2025AnnualRollup/RTBM_MCP_2025.csv.zip"),
        )
        d = dt.date(2025, 1, 1)
        while d.year == 2025:
            ymd = d.strftime("%Y%m%d")
            yield (
                "spp-or-mcp/da-mcp-2025",
                f"DA-MCP-{ymd}0100.csv",
                lambda d=d, ymd=ymd: _dl(
                    "da-mcp", f"/2025/{d:%m}/DA-MCP-{ymd}0100.csv"
                ),
            )
            d += dt.timedelta(days=1)
    if want("genmix"):
        for y in (2023, 2024, 2025):
            yield (
                "spp-genmix",
                f"GenMix_{y}.csv",
                lambda y=y: _dl("generation-mix-historical", f"/GenMix_{y}.csv"),
            )
    if want("binding-constraints"):
        for y in YEARS_ARCHIVED:
            yield (
                "spp-binding-constraints",
                f"RTBM-BC-YEARLY-{y}.csv.zip",
                lambda y=y: _members(
                    _dl("rtbm-binding-constraints", f"/{y}/{y}.zip"),
                    lambda n: n.endswith(f"RTBM-BC-YEARLY-{y}.csv.zip"),
                ),
            )
        for m in MONTHS:
            yield (
                "spp-binding-constraints",
                f"RTBM-BC-MONTHLY-2025{m}.csv.zip",
                lambda m=m: _dl(
                    "rtbm-binding-constraints",
                    f"/2025/{m}/RTBM-BC-MONTHLY-2025{m}.csv.zip",
                ),
            )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out-root", type=Path, default=Path("data/raw"))
    ap.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="subset of: hourly-load or-mcp genmix binding-constraints",
    )
    ap.add_argument("--dry-run", action="store_true", help="print the plan only")
    args = ap.parse_args(argv)
    only = set(args.only) if args.only else None
    n = 0
    for product_dir, name, fetch in plan(only):
        target_dir = args.out_root / product_dir
        if args.dry_run:
            print(f"{target_dir}/{name}")
            continue
        got = fetch()
        target_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(
            got, dict
        ):  # zip members -> one file each (the yearly archive itself is not kept)
            for member, data in got.items():
                (target_dir / member).write_bytes(data)
                print(f"wrote {target_dir / member} ({len(data)} B)")
                n += 1
        else:
            (target_dir / name).write_bytes(got)
            print(f"wrote {target_dir / name} ({len(got)} B)")
            n += 1
    print(f"{n} files written" if not args.dry_run else "dry run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
