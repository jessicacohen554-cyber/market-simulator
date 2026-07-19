"""CAISO zonal-sufficiency test — hub-spread duration curves (doc-06 DD3).

Design decision 3 of the CAISO prompt pack (doc 06) asks whether CAISO must
be modelled zonally (NP15 / ZP26 / SP15) or whether a single copper-plate
price is good enough. The evidence is the **congestion between the trading
hubs**: if the day-ahead hub LMPs rarely diverge, one system price suffices;
if they part by tens of $/MWh for a meaningful share of hours, the zonal
topology is carrying real information and a single-zone model would miss it.

This reads the committed DAM hourly aggregates
(``scripts/data/postprocess_oasis_downloads.py`` -> ``CAISO_dam_hourly_{year}.csv``)
and, per year, builds the duration curve of each pairwise hub spread
(TH_NP15 - TH_SP15, TH_NP15 - TH_ZP26, and TH_SP15 - TH_ZP26 for reference).
For each it reports the signed mean (which hub is dear), the |spread|
duration-curve percentiles p50/p90/p99, and the share of hours the
*absolute* spread exceeds $5 and $20.

Years without a full DAM year are skipped with a note: OASIS's ~39-month
retention had aged most of 2023 DAM out by the mid-2026 pull, so 2023 is a
~3-trade-date stub, not a year (see ``docs/multi-iso/caiso-data-audit.md``).

Usage:
    python scripts/caiso_zonal_sufficiency.py [--years 2024 2025] [--md]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402

# Committed CAISO DAM hourly aggregates under the single W1 data root
# (paths.RAW_DIR = data/raw); the pre-W1 ``inputs/raw-data`` path was removed by
# the relocation.
DAM_DIR = RAW_DIR / "lmp-data" / "CAISO"

HUBS = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "SP15": "TH_SP15_GEN-APND",
}
# Pairwise spreads to report, in the order the prompt frames them (NP15 as the
# northern reference; SP15-ZP26 last as the "do the two southern hubs move
# together?" control).
PAIRS = (("NP15", "SP15"), ("NP15", "ZP26"), ("SP15", "ZP26"))
# A year needs near-full DAM coverage to stand for a duration curve.
MIN_HOURS = 8000


def _hub_wide(year: int) -> pd.DataFrame | None:
    """Per-hub DAM price wide frame for ``year`` (rows with all three hubs)."""
    path = DAM_DIR / f"CAISO_dam_hourly_{year}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["interval_start_gmt", "node", "LMP"])
    wide = df.pivot_table(
        index="interval_start_gmt", columns="node", values="LMP", aggfunc="mean"
    )
    if not set(HUBS.values()) <= set(wide.columns):
        return None
    wide = wide[list(HUBS.values())].dropna()
    wide.columns = list(HUBS)
    return wide if len(wide) >= MIN_HOURS else None


def _spread_stats(spread: pd.Series) -> dict:
    """Signed mean + |spread| duration-curve percentiles + threshold shares."""
    a = spread.abs()
    return {
        "hours": int(len(spread)),
        "signed_mean": round(float(spread.mean()), 2),
        "p50": round(float(a.quantile(0.50)), 2),
        "p90": round(float(a.quantile(0.90)), 2),
        "p99": round(float(a.quantile(0.99)), 2),
        "pct_gt_5": round(100.0 * float((a > 5).mean()), 1),
        "pct_gt_20": round(100.0 * float((a > 20).mean()), 1),
    }


def analyze(years: list[int]) -> dict[int, dict[str, dict]]:
    """Return ``{year: {"A-B": stats}}`` for the years with a full DAM curve."""
    out: dict[int, dict[str, dict]] = {}
    for year in years:
        wide = _hub_wide(year)
        if wide is None:
            print(
                f"  {year}: no full DAM year — skipped "
                f"(retention-aged stub or unfetched)"
            )
            continue
        out[year] = {f"{a}-{b}": _spread_stats(wide[a] - wide[b]) for a, b in PAIRS}
    return out


def _render(results: dict[int, dict[str, dict]], markdown: bool) -> str:
    """Plain or markdown table of the spread duration curves."""
    bar = "| " if markdown else ""
    sep = " | " if markdown else "  "
    end = " |" if markdown else ""
    head = [
        "year",
        "spread",
        "signed mean",
        "|s| p50",
        "|s| p90",
        "|s| p99",
        "% |s|>$5",
        "% |s|>$20",
    ]
    lines = [bar + sep.join(head) + end]
    if markdown:
        lines.append("|" + "|".join("---" for _ in head) + "|")
    for year, pairs in results.items():
        for name, s in pairs.items():
            row = [
                str(year),
                name,
                f"{s['signed_mean']:+.2f}",
                f"{s['p50']:.2f}",
                f"{s['p90']:.2f}",
                f"{s['p99']:.2f}",
                f"{s['pct_gt_5']:.1f}%",
                f"{s['pct_gt_20']:.1f}%",
            ]
            lines.append(bar + sep.join(row) + end)
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    ap.add_argument(
        "--md",
        action="store_true",
        help="emit a markdown table (for the data audit doc)",
    )
    args = ap.parse_args()
    results = analyze(args.years)
    if results:
        print(_render(results, args.md))


if __name__ == "__main__":
    main()
