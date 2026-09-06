#!/usr/bin/env python
"""Re-fetch the SPP Integrated Marketplace public files lane SPP-14 landed under
``data/raw/spp-{hourly-load,or-mcp,genmix,binding-constraints}/``, byte-for-byte,
from SPP's own portal file browser over HTTPS.

Lane SPP-14 (``docs/handoffs/FINDING-spp-14-2026-09-06.md``) found the portal
route SPP-12 / SPP-13 measured as ``200 []`` / ``404`` on 2026-09-06 **serving
data again to an anonymous caller the same day** — no UI token, no cookie, no
User-Agent dependence (curl default, ``python-requests`` and a browser UA all
return the same bytes). This script is the PRODUCER for the landed payloads so
the landing is reproducible (rule 13 ``[R-MEASURED]``: a third-party copy is
admissible only as SPP's own published series — here the series IS SPP's own).
It does NOT touch the LMP products: those belong to
``scripts/data/build_spp_lmp_reference.py`` (unchanged; run ``--per-hub`` for
the zonal parquet).

The route (re-discovered from ``portal.spp.org/static/js/main.<hash>.js`` by
SPP-12, unchanged):

    listing   GET https://portal.spp.org/file-browser-api/?fsName=<fs>&path=<p>&type=folder
    download  GET https://portal.spp.org/file-browser-api/download/<fs>?path=<p>

Products and the exact members fetched (2023 / 2024 are SPP's yearly zips or
members thereof; 2025 is the live per-month / per-day layout):

* ``hourly-load``: ``/<yr>/<yr>.zip`` members ``HOURLY_LOAD-<yr><mm>.csv`` (2023,
  2024); ``/2025/HOURLY_LOAD-2025<mm>.csv`` (wide format, 17 EIA-930 sub-BA
  columns, UTC ``MarketHour``).
* ``rtbm-mcp``: ``/<yr>/<yr>.zip`` member ``<yr>/<yr>AnnualRollup/RTBM_MCP_<yr>.csv.zip``
  (2023, 2024); ``/2025/2025AnnualRollup/RTBM_MCP_2025.csv.zip``.
* ``da-mcp``: ``/<yr>/<yr>.zip`` (2023, 2024, whole archive, 0.4 MB); the 365
  ``/2025/<mm>/DA-MCP-2025<mm><dd>0100.csv`` daily files.
* ``generation-mix-historical``: ``/GenMix_<yr>.csv`` (root-level yearly, 5-min,
  complete 105,120 intervals; NOT the ``SPP/`` sub-folder product SPP-13 landed).
* ``rtbm-binding-constraints``: ``/<yr>/<yr>.zip`` member ``<yr>/RTBM-BC-YEARLY-<yr>.csv.zip``
  (2023, 2024); ``/2025/<mm>/RTBM-BC-MONTHLY-2025<mm>.csv.zip``. All carry the
  10-column schema (no effective limits / Interconnect — those columns begin
  with the 2026-01-28 daily file).

Usage::

    python scripts/data/fetch_spp_alt_portal.py --out-root data/raw [--only hourly-load ...]
    python scripts/data/fetch_spp_alt_portal.py --dry-run

Verify against each directory's ``SHA256SUMS.txt`` afterwards; a mismatch means
SPP re-published the file (they do replace files in place) and is a finding,
not something to overwrite silently.
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
                f"DA-MCP-{y}.zip",
                lambda y=y: _dl("da-mcp", f"/{y}/{y}.zip"),
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
