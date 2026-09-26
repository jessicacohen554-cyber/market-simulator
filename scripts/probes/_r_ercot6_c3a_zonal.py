"""R-ERCOT-6 Step 2: zone-resolved C3a decomposition of the keeper (zero LP).

Mirrors the scorer exactly (calibration_verdict C3a vs the committed ``rt_lw``:
each model zone P1 price vs the mean of its LZ RT settlement series, weighted by
measured zonal demand), then splits the load-weighted gap by month, by actual
and model price band, by zone, and into a body (both sides capped at $200 /
$1,000) and a tail. Keeper bundle ``r_ercot5_hourgrain_span``.

Usage: ``python3 scripts/probes/_r_ercot6_c3a_zonal.py 2023 2024 2025``.
Record: ``docs/handoffs/FINDING-r-ercot-6-double-count-retest-2026-09-26.md``.
"""

import sys

sys.path[:0] = [".", "src", "scripts"]
import pandas as pd
import numpy as np
import scripts.data.derive_actual_lmp as D
from market_sim.config.iso_configs import get_iso_config

B = "results/calibration/r_ercot5_hourgrain_span/hourly"
zp = pd.read_parquet(D.HOURLY_OUT / D.ERCOT_ZONAL_PARQUET)
zones = [z.name for z in get_iso_config("ERCOT").zones]
bands = [-1e9, 0, 20, 30, 40, 50, 75, 100, 200, 1000, 1e9]
lab = [
    "<0",
    "0-20",
    "20-30",
    "30-40",
    "40-50",
    "50-75",
    "75-100",
    "100-200",
    "200-1k",
    ">1k",
]
for y in [int(a) for a in sys.argv[1:]]:
    dem = D._measured_zone_demand("ERCOT", y)
    z = zp[zp.year == y]
    ser = {}
    for sp, g in z.groupby("settlement_point"):
        d = np.full(8760, np.nan)
        hr = g.hour.to_numpy(int)
        ok = hr < 8760
        d[hr[ok]] = g.rt.to_numpy(float)[ok]
        ser[str(sp)] = d
    s = pd.read_parquet(f"{B}/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    P = s.pivot(index="hour", columns="zone", values="price")
    rows = []
    for zi, zn in enumerate(zones):
        lzs = D.ERCOT_MODEL_ZONE_TO_LZ.get(zn)
        w = dem[zi]
        if not lzs or w.sum() <= 0 or zn not in P:
            continue
        have = [ser[l] for l in lzs if l in ser and not np.isnan(ser[l]).all()]
        if not have:
            continue
        a = np.nanmean(np.vstack(have), 0)[: len(w)]
        m = P[zn].to_numpy()[: len(w)]
        ok = ~np.isnan(a)
        rows.append(
            pd.DataFrame(
                {
                    "zone": zn,
                    "h": np.arange(len(w))[ok],
                    "m": m[ok],
                    "a": a[ok],
                    "w": w[ok],
                }
            )
        )
    df = pd.concat(rows)
    W = df.w.sum()
    # scorer: model = zone-demand-weighted mean of per-zone LW means == sum(m w)/sum(w)
    M = (df.m * df.w).sum() / W
    A = (df.a * df.w).sum() / W
    df["g"] = (df.m - df.a) * df.w / W
    df["mon"] = pd.to_datetime(f"{y}-01-01") + pd.to_timedelta(df.h, unit="h")
    df["mon"] = df.mon.dt.month
    cap = lambda c: ((np.minimum(df.m, c) - np.minimum(df.a, c)) * df.w).sum() / W
    print(
        f"==== {y}: model {M:.2f} actual {A:.2f} gap {M - A:+.2f} $/MWh ({(M - A) / A * 100:+.1f}%)"
    )
    print(
        f"   capped both@200: {cap(200):+.2f}  @1000: {cap(1000):+.2f}  => tail>200 {M - A - cap(200):+.2f}, tail>1000 {M - A - cap(1000):+.2f}"
    )
    mon = df.groupby("mon").g.sum()
    print("   by month:", " ".join(f"{k}:{v:+.2f}" for k, v in mon.items()))
    mcap = (
        df.assign(g2=(np.minimum(df.m, 200) - np.minimum(df.a, 200)) * df.w / W)
        .groupby("mon")
        .g2.sum()
    )
    print("   by month, body<=200:", " ".join(f"{k}:{v:+.2f}" for k, v in mcap.items()))
    ab = pd.cut(df.a, bands, labels=lab, right=False)
    t = df.groupby(ab, observed=False).agg(
        gap=("g", "sum"), zh=("g", "size"), m=("m", "mean"), a=("a", "mean")
    )
    print("   by ACTUAL band:\n" + t.round(2).to_string())
    mb = pd.cut(df.m, bands, labels=lab, right=False)
    print(
        "   by MODEL band:",
        " ".join(
            f"{k}:{v:+.2f}" for k, v in df.groupby(mb, observed=False).g.sum().items()
        ),
    )
    zg = df.groupby("zone").agg(gap=("g", "sum"), m=("m", "mean"), a=("a", "mean"))
    print("   by zone:\n" + zg.round(2).to_string())
    q = [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    print(
        "   LW quantiles model",
        [round(float(np.quantile(df.m, x)), 1) for x in q],
        "actual",
        [round(float(np.quantile(df.a, x)), 1) for x in q],
    )
