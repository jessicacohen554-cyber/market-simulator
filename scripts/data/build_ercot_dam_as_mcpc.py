"""Build ERCOT's measured hourly Day-Ahead AS Market Clearing Price (MCPC) series.

Derives, per year, the published DAM ancillary-service clearing prices that mark
the hours ERCOT's day-ahead market co-optimized energy and AS *into scarcity* —
the measured driver behind the May-2024-style DAM AS-co-optimized price spikes the
energy-only / energy+reserve LP cannot form (see
``market_sim.results.scarcity.ercot_dam_as_overlay_series``).

Source: the ERCOT **60-Day DAM Disclosure — Gen Resource Data** reports
(``data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_<year>_*.parquet``).
Each per-resource row carries that hour's market-wide MCPC for every AS product it
could clear: ``RegUp MCPC``, ``RRS MCPC``, ``ECRS MCPC`` (from the ECRS launch on
2023-06-10; absent in the pre-launch 2023 schema), ``NonSpin MCPC``. The MCPC is a
single market-clearing price per product per hour, but the column is only populated
on rows for resources that actually offered/cleared that product (others carry 0),
so the hourly MCPC is recovered as the **max across resources** in each
(DeliveryDate, HourEnding). This is the same measured-series build pattern as
``scripts/data/derive_ercot_zonal_lmp.py`` / ``scripts/data/derive_reliability_deployment.py``
— a published quantity reduced to the model's hourly clock, never fitted to a price
residual.

Output: ``data/raw/ercot/ercot_<year>_dam_as_mcpc_hourly.parquet`` with columns
``hour`` (non-leap 8760 hour-of-year), ``regup_mcpc``, ``rrs_mcpc``, ``ecrs_mcpc``,
``nonspin_mcpc`` and ``binding_mcpc`` (the per-hour max across the four up/contingency
products — the binding AS clearing price whose co-optimization scarcity rent lifts the
energy price; RegDown is excluded, a down product does not lift energy). Hours absent
from the disclosure (the 60-day lag leaves a year's Nov-Dec tail unpublished) are
left NaN and read as 0 (no overlay) downstream — never fabricated.

The clock matches the fleet's non-leap 8760-hour convention (Feb-29 dropped); the
DAM runs on the standard 24-hour clock (HourEnding 1-24 → hour-of-day 0-23), with no
DST fall-back duplicate hour in these reports.

Usage:
    python scripts/data/build_ercot_dam_as_mcpc.py [year ...]   # default 2023 2024 2025
"""

from __future__ import annotations

import glob
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from market_sim.config.paths import RAW_DATA_DIR

_GENRES_GLOB = "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet"
# DAM AS up/contingency products whose scarcity rent lifts the energy price, mapped
# to the output column names. RegDown is deliberately excluded.
_MCPC_COLS: dict[str, str] = {
    "RegUp MCPC": "regup_mcpc",
    "RRS MCPC": "rrs_mcpc",
    "ECRS MCPC": "ecrs_mcpc",
    "NonSpin MCPC": "nonspin_mcpc",
}

_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _hour_of_year(month: int, day: int, hour_of_day: int) -> int:
    """Non-leap hour-of-year index (Feb-29 dropped) for a calendar slot."""
    doy = sum(_DAYS_IN_MONTH[: month - 1]) + (day - 1)
    return doy * 24 + hour_of_day


def build_year(year: int, hours: int = 8760) -> pd.DataFrame:
    """Return the hourly DAM AS MCPC frame for ``year`` on the non-leap clock."""
    files = sorted(
        glob.glob(str(RAW_DATA_DIR / "ercot" / _GENRES_GLOB.format(year=year)))
    )
    if not files:
        raise FileNotFoundError(
            f"no 60-Day DAM Gen Resource Data files for {year} under {RAW_DATA_DIR / 'ercot'}"
        )
    frames = []
    for f in files:
        avail = set(pq.ParquetFile(f).schema.names)
        present = [c for c in _MCPC_COLS if c in avail]
        df = pd.read_parquet(f, columns=["Delivery Date", "Hour Ending"] + present)
        for c in present:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        dt = pd.to_datetime(df["Delivery Date"])
        df = df[dt.dt.year == int(year)].copy()
        if df.empty:
            continue
        df["dt"] = pd.to_datetime(df["Delivery Date"])
        # MCPC is one clearing price per (date, hour); recover it as the max over
        # resources (unpopulated rows are 0). HourEnding 1..24 -> hour-of-day 0..23.
        g = df.groupby([df["dt"].dt.month, df["dt"].dt.day, df["Hour Ending"]])[
            present
        ].max()
        frames.append(g)
    g = pd.concat(frames)
    # Files overlap at their delivery-date seams; keep one row per calendar slot.
    g = g[~g.index.duplicated(keep="first")]

    out = pd.DataFrame({"hour": np.arange(hours, dtype=np.int32)})
    for src, dst in _MCPC_COLS.items():
        out[dst] = np.nan
    for (month, day, he), row in g.iterrows():
        if month == 2 and day == 29:  # fleet clock is non-leap
            continue
        h = _hour_of_year(int(month), int(day), int(he) - 1)
        if 0 <= h < hours:
            for src, dst in _MCPC_COLS.items():
                if src in row.index:
                    out.at[h, dst] = row[src]
    # Binding AS clearing price = max across the up/contingency products present.
    present_dst = [d for s, d in _MCPC_COLS.items()]
    out["binding_mcpc"] = out[present_dst].max(axis=1, skipna=True)
    return out


def main(argv: list[str]) -> int:
    years = [int(a) for a in argv] if argv else [2023, 2024, 2025]
    for year in years:
        out = build_year(year)
        path = RAW_DATA_DIR / "ercot" / f"ercot_{year}_dam_as_mcpc_hourly.parquet"
        out.to_parquet(path, index=False)
        b = out["binding_mcpc"]
        n_cov = int(b.notna().sum())
        n_scarce = int((b.fillna(0.0) > 150.0).sum())
        print(
            f"{year}: wrote {path.name}  hours_covered={n_cov}/{len(out)}  "
            f"binding>150={n_scarce}  max={np.nanmax(b.to_numpy()):.1f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
