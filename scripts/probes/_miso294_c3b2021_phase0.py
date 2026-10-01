#!/usr/bin/env python3
"""miso-294 Part B phase 0 (ZERO LP): what carries C3b 2021, and is C3a 2020 the same object?

Reads only committed artifacts: the keeper's hourly sidecars
(``results/calibration/miso280_span/hourly/{system,class_hourly}_<y>.parquet``),
the zonal hub archive (``actual_lmp_hourly_zonal_MISO.parquet``) and the EIA-930
BALANCE files. Prints, per year 2019-2025:

1. the hour-level gap (model minus zone-resolved actual, both weighted by the
   model's own zonal demand) by system-load quintile, and p10/p50 of each side;
2. monthly MISO coal TWh, model minus EIA-930 (adjusted net generation).

For 2021 it also prints the per-zone monthly means for Sep-Nov. The actual is
a benchmark, never an input (rule 13).

Usage::

    uv run python scripts/probes/_miso294_c3b2021_phase0.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOURLY = REPO / "results/calibration/miso280_span/hourly"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
EIA930 = REPO / "data/raw/eia-930"
ZONES = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]
PLAINS_PROXY = ("MINN.HUB", "ILLINOIS.HUB")


def zone_prices(year: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Model price, model demand and actual RT price, hour x zone, for one year."""
    s = pd.read_parquet(HOURLY / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    pm = s.pivot(index="hour", columns="zone", values="price")[ZONES]
    dm = s.pivot(index="hour", columns="zone", values="demand")[ZONES]
    z = pd.read_parquet(ZONAL)
    z = z[z["year"] == year]
    az = z.groupby(["hour", "zone"])["rt"].mean().unstack()
    az["MISO-Plains"] = z[z["hub"].isin(PLAINS_PROXY)].groupby("hour")["rt"].mean()
    return pm, dm, az.reindex(pm.index)[ZONES]


def coal_gap_by_month(year: int) -> pd.Series:
    """Monthly MISO coal TWh, model P1 minus EIA-930 adjusted net generation."""
    b = pd.concat(
        pd.read_parquet(EIA930 / f"EIA930_BALANCE_{year}_{h}.parquet")
        for h in ("Jan_Jun", "Jul_Dec")
    )
    b = b[b["Balancing Authority"] == "MISO"]
    mon = pd.to_datetime(b["Data Date"].astype(str)).dt.month
    col = "Net Generation (MW) from Coal (Adjusted)"
    actual = pd.to_numeric(b[col], errors="coerce").groupby(mon).sum() / 1e6
    c = pd.read_parquet(HOURLY / f"class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & c["klass"].str.startswith("COAL")]
    cm = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(c["hour"], unit="h")).dt.month
    model = c.groupby(cm)["mw"].sum() / 1e6
    return model - actual


def main() -> None:
    """CLI entry point."""
    for y in range(2019, 2026):
        pm, dm, az = zone_prices(y)
        ok = az.notna().all(axis=1)
        w = dm.sum(axis=1)
        d = pd.DataFrame(
            {"m": (pm * dm).sum(axis=1) / w, "a": (az * dm).sum(axis=1) / w, "L": w}
        )[ok]
        q = pd.qcut(d["L"], 5, labels=False)
        gap = (d["m"] - d["a"]).groupby(q).mean()
        print(
            f"{y} gap by load quintile "
            + " ".join(f"{v:+5.1f}" for v in gap)
            + f" | p10 m/a {d.m.quantile(0.1):.1f}/{d.a.quantile(0.1):.1f}"
            + f" p50 {d.m.median():.1f}/{d.a.median():.1f}"
        )
        cg = coal_gap_by_month(y)
        print("     coal model-EIA930 TWh " + " ".join(f"{v:+5.1f}" for v in cg))
    pm, dm, az = zone_prices(2021)
    mon = (pd.Timestamp("2021-01-01") + pd.to_timedelta(pm.index, unit="h")).month
    for m in (9, 10, 11):
        sel = np.asarray(mon == m)
        print(
            f"2021-{m:02d} model/actual "
            + " ".join(
                f"{zn.split('-')[1]} {pm[sel][zn].mean():.1f}/{az[sel][zn].mean():.1f}"
                for zn in ZONES
            )
        )


if __name__ == "__main__":
    main()
