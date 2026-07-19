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
duration-curve percentiles p50/p90/p99, the share of hours the *absolute*
spread exceeds $5 and $20, and (like the NYISO/NEISO siblings) where the
> $20 hours concentrate. The statistics/renderers are the shared
``scripts.lib.zonal_sufficiency`` helpers; this script supplies only the
CAISO hub frame and the pairs to report. The DAM aggregates are GMT-stamped,
so the concentration's season / hour-of-day are on the GMT clock.

Years without a full DAM year are skipped with a note: OASIS's ~39-month
retention had aged most of 2023 DAM out by the mid-2026 pull, so 2023 is a
~3-trade-date stub, not a year (see ``docs/multi-iso/caiso-data-audit.md``).

Usage:
    python scripts/caiso_zonal_sufficiency.py [--years 2024 2025] [--md]
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from market_sim.config.paths import RAW_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.zonal_sufficiency import (  # noqa: E402
    analyze,
    render_concentration,
    render_table,
)

# Committed CAISO DAM hourly aggregates under the single W1 data root
# (paths.RAW_DIR = data/raw); the pre-W1 ``inputs/raw-data`` path was removed by
# the relocation.
DAM_DIR = RAW_DIR / "lmp-data" / "CAISO"

HUBS = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "SP15": "TH_SP15_GEN-APND",
}
# Pairwise spreads to report as (zone_a, zone_b, label), in the order the prompt
# frames them (NP15 as the northern reference; SP15-ZP26 last as the "do the two
# southern hubs move together?" control). Labels keep the historical "A-B" key.
PAIRS = (
    ("NP15", "SP15", "NP15-SP15"),
    ("NP15", "ZP26", "NP15-ZP26"),
    ("SP15", "ZP26", "SP15-ZP26"),
)
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
    if len(wide) < MIN_HOURS:
        return None
    # Datetime index so the shared concentration helper can read season / HB
    # hour (GMT clock — the DAM aggregates are GMT-stamped).
    wide.index = pd.to_datetime(wide.index)
    return wide


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    ap.add_argument(
        "--md",
        action="store_true",
        help="emit a markdown table (for the data audit doc)",
    )
    args = ap.parse_args()
    # CAISO is day-ahead only; the frame provider ignores ``kind``.
    stats, conc = analyze(lambda year, kind: _hub_wide(year), args.years, PAIRS, "da")
    if stats:
        print(render_table(stats, args.md))
        print()
        print(render_concentration(conc))


if __name__ == "__main__":
    main()
