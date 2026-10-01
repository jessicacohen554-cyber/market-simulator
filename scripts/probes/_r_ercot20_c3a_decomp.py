"""R-ERCOT-20 phase 0 (zero LP): where the 2024 C3a load-weighted price deficit lives.

Reads only the committed keeper hourlies (``results/calibration/r_ercot19a_span``)
and the committed zonal RT actual (``actual_lmp_zonal_ERCOT.parquet``), rebuilt on
the scorer's own basis (``derive_actual_lmp._lw_fields`` for the actual, the
payload's demand-weighted zonal mean for the model; the weight is the model's
own zonal demand, which is the measured series ``eia_loader.load_demand``).

Splits the annual gap Σ d·(model − actual) / Σ d into additive shares by hour
class (actual-RT level buckets, and hour-of-day windows), by month and by zone,
and reports the per-bucket mean prices. 2025 and 2022 are run as comparators.
Solves nothing. Record: docs/handoffs/r-ercot/r_ercot20_phase0.json.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

BUNDLE = "results/calibration/r_ercot19a_span/hourly"
ZONE_TO_LZ = {  # scripts/data/derive_actual_lmp.ERCOT_MODEL_ZONE_TO_LZ
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}
OUT = "docs/handoffs/r-ercot/r_ercot20_phase0.json"


def load_year(y: int, zact: pd.DataFrame) -> pd.DataFrame:
    """Return long (zone, hour) frame of model price, actual RT and demand for ``y``."""
    s = pd.read_parquet(f"{BUNDLE}/system_{y}.parquet")
    s = s[s["pass"] == "P1"][["zone", "hour", "price", "demand"]].copy()
    z = zact[zact.year == y]
    piv = z.pivot_table(index="hour", columns="settlement_point", values="rt")
    parts = []
    for zone, g in s.groupby("zone"):
        lzs = [lz for lz in ZONE_TO_LZ.get(zone, ()) if lz in piv.columns]
        if not lzs:
            continue
        a = piv[lzs].mean(axis=1).reindex(g.hour.values).to_numpy()
        parts.append(g.assign(actual=a))
    df = pd.concat(parts)
    df = df[(df.demand > 0) & df.actual.notna()]
    ts = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(df.hour, unit="h")
    df["month"] = ts.dt.month.values
    df["hod"] = ts.dt.hour.values
    return df


def shares(df: pd.DataFrame, key: pd.Series) -> pd.DataFrame:
    """Additive decomposition of the LW gap by ``key``: $/MWh contribution + share."""
    D = df.demand.sum()
    gap = (df.demand * (df.price - df.actual)).sum() / D
    g = df.assign(k=key.values, wm=df.demand * df.price, wa=df.demand * df.actual)
    r = g.groupby("k").agg(d=("demand", "sum"), wm=("wm", "sum"), wa=("wa", "sum"),
                           n=("hour", "nunique"))
    r["model"] = r.wm / r.d
    r["actual"] = r.wa / r.d
    r["contrib_usd"] = (r.wm - r.wa) / D
    r["share_of_gap"] = r.contrib_usd / gap
    r["load_share"] = r.d / D
    return r[["n", "load_share", "model", "actual", "contrib_usd", "share_of_gap"]].round(3)


def main(years=(2024, 2025, 2022)) -> None:
    """Print and record the decompositions."""
    zact = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_zonal_ERCOT.parquet")
    rec: dict = {}
    for y in years:
        df = load_year(y, zact)
        D = df.demand.sum()
        M = (df.demand * df.price).sum() / D
        A = (df.demand * df.actual).sum() / D
        # System-hour actual (demand-weighted over zones) sets the level buckets.
        sysa = (df.demand * df.actual).groupby(df.hour).sum() / df.demand.groupby(df.hour).sum()
        lvl = pd.cut(df.hour.map(sysa), [-np.inf, 15, 25, 40, 100, np.inf],
                     labels=["trough<=15", "15-25", "25-40", "40-100", "tight>100"])
        hod = pd.cut(df.hod, [-1, 5, 9, 15, 20, 23],
                     labels=["00-05", "06-09", "10-15", "16-20", "21-23"])
        out = {"model_lw": round(M, 3), "actual_lw": round(A, 3),
               "gap_usd": round(M - A, 3), "err_pct": round(100 * (M / A - 1), 2)}
        print(f"\n===== {y}: model {M:.2f} actual {A:.2f} gap {M - A:+.2f} ({100 * (M / A - 1):+.1f}%)")
        for name, key in (("level", lvl), ("hod", hod), ("month", df.month), ("zone", df.zone)):
            t = shares(df, key)
            print(f"-- by {name}\n{t.to_string()}")
            out[name] = json.loads(t.to_json(orient="index"))
        # Clip counterfactual: gap with actual capped at $100 in tight hours both sides.
        cap = np.minimum
        out["gap_if_both_capped_100"] = round(
            float((df.demand * (cap(df.price, 100) - cap(df.actual, 100))).sum() / D), 3)
        rec[str(y)] = out
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main(tuple(int(a) for a in sys.argv[1:]) or (2024, 2025, 2022))
