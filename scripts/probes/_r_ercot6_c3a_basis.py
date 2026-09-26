"""R-ERCOT-6 Step 2: the actual LZ congestion basis inside C3a (zero LP).

Same weights as the scorer; compares the model against the zonal LZ benchmark
(``rt_lw``) and against the HB_HUBAVG series on identical zone-demand weights,
so the difference is the actual LZ-over-hub basis a model zone price must carry.

Usage: ``python3 scripts/probes/_r_ercot6_c3a_basis.py 2023 2024 2025``.
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
hub = pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet")
zones = [z.name for z in get_iso_config("ERCOT").zones]
for y in map(int, sys.argv[1:]):
    dem = D._measured_zone_demand("ERCOT", y)
    z = zp[zp.year == y]
    ser = {}
    for sp, g in z.groupby("settlement_point"):
        d = np.full(8760, np.nan)
        hr = g.hour.to_numpy(int)
        ok = hr < 8760
        d[hr[ok]] = g.rt.to_numpy(float)[ok]
        ser[str(sp)] = d
    hb = np.full(8760, np.nan)
    hh = hub[hub.year == y]
    hb[hh.hour.to_numpy(int)] = hh.rt.to_numpy(float)
    s = pd.read_parquet(f"{B}/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    P = s.pivot(index="hour", columns="zone", values="price")
    num_m = num_a = num_h = W = 0
    spread = []
    for zi, zn in enumerate(zones):
        lzs = D.ERCOT_MODEL_ZONE_TO_LZ.get(zn)
        w = dem[zi]
        if not lzs or w.sum() <= 0:
            continue
        have = [ser[l] for l in lzs if l in ser and not np.isnan(ser[l]).all()]
        if not have:
            continue
        n = len(w)
        a = np.nanmean(np.vstack(have), 0)[:n]
        m = P[zn].to_numpy()[:n]
        h = hb[:n]
        ok = ~np.isnan(a) & ~np.isnan(h)
        num_m += (m[ok] * w[ok]).sum()
        num_a += (a[ok] * w[ok]).sum()
        num_h += (h[ok] * w[ok]).sum()
        W += w[ok].sum()
    M, A, H = num_m / W, num_a / W, num_h / W
    mz = P.mean()
    print(
        f"{y}: model {M:.2f}  actual-LZ {A:.2f} ({(M - A) / A * 100:+.1f}%)  actual-HUB same weights {H:.2f} ({(M - H) / H * 100:+.1f}%)  LZ basis over hub {A - H:+.2f} $/MWh = {(A - H) / (A - M) * 100:.0f}% of the C3a gap"
    )
    print(
        "    model zone mean spread max-min $/MWh:",
        round(float(mz.max() - mz.min()), 3),
        " hours any model zone differs by >$1:",
        int(((P.max(1) - P.min(1)) > 1).sum()),
    )
