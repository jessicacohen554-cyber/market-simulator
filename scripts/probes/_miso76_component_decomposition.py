"""miso-76 Phase-A probe 2 — hub-spread decomposition into congestion (MCC) vs loss (MLC).

Derive-only (NO LP). Samples MISO's public daily DA ex-post LMP reports
(``https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv`` —
per-node LMP/MCC/MLC rows) on the 15th of every month 2023-2025 (36 files,
train window only, CLAUDE.md rule 22) and decomposes each Midwest hub's mean
spread vs INDIANA.HUB into its congestion and loss components.

Phase-A finding (2026-07-19 run): congestion carries ~62-105% of the
persistent spread, marginal losses $0.2-2.9/MWh (~20-38%) — the two
components the design charter's mechanisms M3/M4 divide between them.

Files are cached in ``--cache-dir`` (default: a local ``_miso76_lmp_sample``
next to this script's repo checkout is NOT used; pass an explicit dir or the
scratchpad). A full-history intake is the Phase-A2 `lmp-components` datatype
(data-intake skill), at which point this sampled probe is superseded.

Run: ``.venv/bin/python scripts/probes/_miso76_component_decomposition.py --cache-dir /tmp/miso76_lmp``
"""

from __future__ import annotations

import argparse
import csv
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

BASE = "https://docs.misoenergy.org/marketreports"
HUBS = ["MINN.HUB", "ILLINOIS.HUB", "INDIANA.HUB", "MICHIGAN.HUB"]
YEARS = (2023, 2024, 2025)  # train window ONLY (rule 22)


def fetch(cache: Path) -> list[Path]:
    """Download the 36 sampled daily files (15th of each month) into ``cache``."""
    cache.mkdir(parents=True, exist_ok=True)
    out = []
    for y in YEARS:
        for m in range(1, 13):
            name = f"{y}{m:02d}15_da_expost_lmp.csv"
            dest = cache / name
            if not dest.exists() or dest.stat().st_size == 0:
                with urllib.request.urlopen(f"{BASE}/{name}", timeout=60) as r:
                    dest.write_bytes(r.read())
            out.append(dest)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-dir", required=True, help="download/cache directory")
    args = ap.parse_args()

    comp: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for f in fetch(Path(args.cache_dir)):
        year = int(f.name[:4])
        for row in csv.reader(f.open()):
            if (
                row
                and row[0] in HUBS
                and len(row) >= 27
                and row[2] in ("LMP", "MCC", "MLC")
            ):
                comp[year][row[0]][row[2]].extend(
                    float(x) if x.strip() else np.nan for x in row[3:27]
                )

    means: dict = {}
    print(f"{'year':<6}{'hub':<14}{'LMP':>8}{'MCC':>8}{'MLC':>8}")
    for y in YEARS:
        for h in HUBS:
            m = {v: float(np.nanmean(comp[y][h][v])) for v in ("LMP", "MCC", "MLC")}
            means[(y, h)] = m
            print(f"{y:<6}{h:<14}{m['LMP']:>8.2f}{m['MCC']:>8.2f}{m['MLC']:>8.2f}")

    print("\n=== spread vs INDIANA.HUB decomposed (sampled DA days) ===")
    print(f"{'year':<6}{'hub':<14}{'dLMP':>8}{'dMCC':>8}{'dMLC':>8}{'cong%':>7}")
    for y in YEARS:
        ind = means[(y, "INDIANA.HUB")]
        for h in ["MINN.HUB", "ILLINOIS.HUB", "MICHIGAN.HUB"]:
            s = means[(y, h)]
            dl = s["LMP"] - ind["LMP"]
            dc = s["MCC"] - ind["MCC"]
            dm = s["MLC"] - ind["MLC"]
            print(
                f"{y:<6}{h:<14}{dl:>8.2f}{dc:>8.2f}{dm:>8.2f}"
                f"{100 * dc / dl if dl else 0:>7.0f}"
            )


if __name__ == "__main__":
    main()
