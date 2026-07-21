"""Derive the WECC-West neighbor hourly balance (CAISO endogenous-import node
foundation, caiso-110).

Aggregates the western-interconnect balancing authorities OUTSIDE CAISO
(EIA-930 BALANCE Region NW + SW) to one hourly series per UTC hour — demand,
net generation by fuel, and the West net export (net_generation - demand) —
and writes it through the clean-data contract (``wecc-west-supply`` schema,
one file per year, iso=CAISO).

This is the DATA foundation for the endogenous WECC_import zone (design:
docs/handoffs/caiso-endogenous-wecc-node-design-2026-07-21.md). The LP wiring
(caiso-110, Option A) consumes the demand + solar/wind/hydro columns as the
neighbor zone's load and renewable availability and the gas/coal columns for its
thermal fleet, aligning UTC -> model clock via the corridor loaders' map;
``net_export_mw`` is the measured net interchange the co-optimized zone must
reproduce. (A "clean surplus over demand" is degenerately ~0 — West solar ~3-5
GW vs demand ~55 GW — so the export is a price/congestion outcome, not a
surplus threshold.)

The BALANCE files are schema-heterogeneous across vintages (old single-solar vs
new split with/without integrated battery; hydro combined vs excl-pumped +
pumped; int/float drift) — handled defensively per fuel.

Usage: PYTHONPATH=. .venv/bin/python scripts/data/derive_wecc_west_supply.py
"""

from __future__ import annotations

import glob

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from market_sim.config.paths import EIA_930_DIR
from scripts.lib.clean_io import write_clean

YEARS = (2023, 2024, 2025)
WEST_REGIONS = ("NW", "SW")  # western interconnect outside CAISO (CISO excluded)

# fuel -> substring test on the "(Adjusted)" net-generation columns (Imputed excl.)
_FUEL_MATCH = {
    "solar_mw": lambda c: c.startswith("Net Generation (MW) from Solar"),
    "wind_mw": lambda c: c.startswith("Net Generation (MW) from Wind"),
    "hydro_mw": lambda c: ("Hydropower" in c) or ("Pumped Storage" in c),
    "gas_mw": lambda c: c.startswith("Net Generation (MW) from Natural Gas"),
    "coal_mw": lambda c: c.startswith("Net Generation (MW) from Coal"),
    "nuclear_mw": lambda c: c.startswith("Net Generation (MW) from Nuclear"),
}


def _adj(names: set[str], pred) -> list[str]:
    return [c for c in names if "(Adjusted)" in c and "Imputed" not in c and pred(c)]


def _read_balance_file(path: str) -> pd.DataFrame:
    """One BALANCE file -> WECC-West rows with normalized fuel columns."""
    names = set(pq.ParquetFile(path).schema.names)
    base = [
        "Balancing Authority",
        "Region",
        "UTC Time at End of Hour",
        "Demand (MW) (Adjusted)",
        "Net Generation (MW) (Adjusted)",
    ]
    fuel_cols = {k: _adj(names, pred) for k, pred in _FUEL_MATCH.items()}
    read = [c for c in base if c in names] + sorted(
        {c for cols in fuel_cols.values() for c in cols}
    )
    df = pd.read_parquet(path, columns=read)
    df = df[
        df["Region"].isin(WEST_REGIONS) & (df["Balancing Authority"] != "CISO")
    ].copy()
    out = pd.DataFrame()
    out["interval_start_utc"] = pd.to_datetime(df["UTC Time at End of Hour"], utc=True)
    out["demand_mw"] = pd.to_numeric(df["Demand (MW) (Adjusted)"], errors="coerce")
    out["net_generation_mw"] = pd.to_numeric(
        df["Net Generation (MW) (Adjusted)"], errors="coerce"
    )
    for k, cols in fuel_cols.items():
        out[k] = (
            df[cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
            if cols
            else np.nan
        )
    return out


def build_year(files: list[str], year: int) -> pd.DataFrame:
    parts = [_read_balance_file(f) for f in files]
    d = pd.concat(parts, ignore_index=True)
    d = d[d["interval_start_utc"].dt.year == year]
    agg = d.groupby("interval_start_utc", as_index=False).sum(min_count=1)
    # West net export = net generation - demand (the measured net interchange the
    # co-optimized WECC_import zone must reproduce). A renewable "surplus over
    # demand" is degenerately ~0 (West solar ~3-5 GW vs demand ~70 GW), so the
    # export to CAISO is a price/congestion outcome, not a surplus threshold.
    agg["net_export_mw"] = agg["net_generation_mw"] - agg["demand_mw"]
    cols = [
        "interval_start_utc",
        "demand_mw",
        "solar_mw",
        "wind_mw",
        "hydro_mw",
        "gas_mw",
        "coal_mw",
        "nuclear_mw",
        "net_generation_mw",
        "net_export_mw",
    ]
    return agg.sort_values("interval_start_utc")[cols].reset_index(drop=True)


def main() -> None:
    files = sorted(glob.glob(str(EIA_930_DIR / "EIA930_BALANCE_*.parquet")))
    for year in YEARS:
        yf = [f for f in files if str(year) in f]
        df = build_year(yf, year)
        # verification: West solar belly-peaked and growing; net export sign
        df["hod"] = df["interval_start_utc"].dt.tz_convert("US/Pacific").dt.hour
        belly = df[df.hod.isin((10, 11, 12, 13, 14))]["solar_mw"].mean()
        night = df[df.hod.isin((0, 1, 2, 3, 4))]["solar_mw"].mean()
        df = df.drop(columns="hod")
        path = write_clean(
            df,
            "wecc-west-supply",
            iso="CAISO",
            year=year,
            source="EIA-930 BALANCE Region NW+SW aggregate",
        )
        print(
            f"{year}: {len(df)} hrs -> {path.name} | West solar belly {belly / 1e3:.1f} GW "
            f"vs overnight {night / 1e3:.1f} GW | demand {df.demand_mw.mean() / 1e3:.0f} GW "
            f"| net export mean {df.net_export_mw.mean() / 1e3:+.1f} GW"
        )


if __name__ == "__main__":
    main()
