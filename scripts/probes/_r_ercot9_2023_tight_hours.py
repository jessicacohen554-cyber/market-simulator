"""R-ERCOT-9 phase 0: 2023 tight-hour decomposition on committed keeper sidecars (zero LP).

Compares the keeper ``r_ercot8_fusco_span`` (Fusco in) with the superseded
``r_ercot5_hourgrain_span`` (read from git history, ``f41f4eb5^``) and the
committed actual LZ RT settlement series, hour by hour.

Usage: ``python3 scripts/probes/_r_ercot9_2023_tight_hours.py <old_hourly_dir>``.
Record: ``docs/records/ercot/FINDING-r-ercot-9-2023-scarcity-2026-09-27.md``.
"""

import sys

sys.path[:0] = [".", "src", "scripts"]
import numpy as np
import pandas as pd
import scripts.data.derive_actual_lmp as D
from market_sim.config.iso_configs import get_iso_config

Y = 2023
NEW = "results/calibration/r_ercot8_fusco_span/hourly"
OLD = sys.argv[1]
zones = [z.name for z in get_iso_config("ERCOT").zones]
dem = D._measured_zone_demand("ERCOT", Y)
zp = pd.read_parquet(D.HOURLY_OUT / D.ERCOT_ZONAL_PARQUET)
zp = zp[zp.year == Y]
ser = {}
for sp, g in zp.groupby("settlement_point"):
    d = np.full(8760, np.nan)
    hr = g.hour.to_numpy(int)
    ok = hr < 8760
    d[hr[ok]] = g.rt.to_numpy(float)[ok]
    ser[str(sp)] = d


def lw(sysdf):
    s = sysdf[sysdf["pass"] == "P1"]
    P = s.pivot(index="hour", columns="zone", values="price")
    num = np.zeros(8760)
    den = np.zeros(8760)
    anum = np.zeros(8760)
    for zi, zn in enumerate(zones):
        lzs = D.ERCOT_MODEL_ZONE_TO_LZ.get(zn)
        w = dem[zi][:8760]
        if not lzs or w.sum() <= 0 or zn not in P:
            continue
        a = np.nanmean(np.vstack([ser[l] for l in lzs if l in ser]), 0)[:8760]
        num += P[zn].to_numpy()[:8760] * w
        anum += np.nan_to_num(a) * w
        den += w
    return num / den, anum / den


out = {}
for tag, d in (("new", NEW), ("old", OLD)):
    s = pd.read_parquet(f"{d}/system_{Y}.parquet")
    m, a = lw(s)
    s1 = s[s["pass"] == "P1"]
    g = s1.groupby("hour")
    rf = pd.read_parquet(f"{d}/reserve_family_{Y}.parquet")
    rf = rf[rf["pass"] == "P1"]
    fam = rf.pivot_table(index="hour", columns="family", values="dual", aggfunc="sum")
    sf = rf.pivot_table(index="hour", columns="family", values="shortfall_mw", aggfunc="sum")
    ch = pd.read_parquet(f"{d}/class_hourly_{Y}.parquet")
    ch = ch[ch["pass"] == "P1"].pivot(index="hour", columns="klass", values="mw")
    st = pd.read_parquet(f"{d}/storage_{Y}.parquet")
    st = st[st["pass"] == "P1"].groupby("hour")[["charge_mw", "discharge_mw", "soc_mwh", "energy_cap_mwh"]].sum()
    out[tag] = dict(
        m=m, a=a, slack=g.slack.sum().to_numpy(), dem=g.demand.sum().to_numpy(),
        rp=g.reserve_price.mean().to_numpy(), ordc=g.ordc_adder.mean().to_numpy(),
        fam=fam, sf=sf, ch=ch, st=st,
    )

N, O = out["new"], out["old"]
a = N["a"]
print(f"LW model new {N['m'].mean():.2f} old {O['m'].mean():.2f} actual {a.mean():.2f}")
for thr in (200, 1000, 3000):
    print(f"h>={thr}: new {(N['m']>=thr).sum()} old {(O['m']>=thr).sum()} actual {(a>=thr).sum()}"
          f"  both(new&act) {((N['m']>=thr)&(a>=thr)).sum()}")
lost = (O["m"] >= 1000) & (N["m"] < 1000)
print("lost >1k hours:", lost.sum())
idx = np.where(lost)[0]
ts = pd.to_datetime("2023-01-01") + pd.to_timedelta(idx, unit="h")
df = pd.DataFrame({
    "ts": ts, "old": O["m"][idx].round(0), "new": N["m"][idx].round(0), "act": a[idx].round(0),
    "old_rp": O["rp"][idx].round(0), "new_rp": N["rp"][idx].round(0),
    "old_ordc": O["ordc"][idx].round(0), "new_ordc": N["ordc"][idx].round(0),
    "slack_o": O["slack"][idx].round(0), "dem": N["dem"][idx].round(0),
})
pd.set_option("display.width", 250)
print(df.to_string())
print("families (new):", list(N["fam"].columns))
print("mean duals in lost hours old/new:")
print(pd.DataFrame({"old": O["fam"].iloc[idx].mean(), "new": N["fam"].iloc[idx].mean()}).round(1))
print("mean shortfall MW in lost hours old/new:")
print(pd.DataFrame({"old": O["sf"].iloc[idx].mean(), "new": N["sf"].iloc[idx].mean()}).round(1))
print("class MW delta (new-old) in lost hours:")
print((N["ch"].iloc[idx].mean() - O["ch"].iloc[idx].mean()).round(0).sort_values().to_string())
print("storage lost hours old/new:\n", O["st"].iloc[idx].mean().round(0).to_dict(), "\n", N["st"].iloc[idx].mean().round(0).to_dict())

# price decomposition of the gap into tails, and tight-hour tabulation vs actual
tight_a = a >= 1000
print("\nACTUAL >=1k hours:", tight_a.sum(), " model new mean there", N["m"][tight_a].mean().round(0),
      " old", O["m"][tight_a].mean().round(0), " actual", a[tight_a].mean().round(0))
print("  new model price dist there:", np.percentile(N["m"][tight_a], [10, 25, 50, 75, 90]).round(0))
print("  new reserve_price there mean", N["rp"][tight_a].mean().round(0), " ordc", N["ordc"][tight_a].mean().round(0))
print("  new family duals there:\n", N["fam"].iloc[np.where(tight_a)[0]].mean().round(1).to_string())
print("  new family shortfall MW there:\n", N["sf"].iloc[np.where(tight_a)[0]].mean().round(1).to_string())
ta = pd.to_datetime("2023-01-01") + pd.to_timedelta(np.where(tight_a)[0], unit="h")
print("  actual>=1k by month:", pd.Series(ta.month).value_counts().sort_index().to_dict())
print("  actual>=1k by hour-of-day:", pd.Series(ta.hour).value_counts().sort_index().to_dict())
tm = pd.to_datetime("2023-01-01") + pd.to_timedelta(np.where(N["m"] >= 1000)[0], unit="h")
print("  model(new)>=1k by month:", pd.Series(tm.month).value_counts().sort_index().to_dict())
contrib = (N["m"] - a)
print("\ngap contribution by actual band ($/MWh of annual mean):")
for lo, hi in ((-1e9, 200), (200, 1000), (1000, 3000), (3000, 1e9)):
    k = (a >= lo) & (a < hi)
    print(f"  [{lo},{hi}) n={k.sum()} gap={contrib[k].sum()/8760:+.2f} model={N['m'][k].mean():.0f} act={a[k].mean():.0f}")

# ---- (a2) measured split: RT settlement = system lambda (+congestion) + RTORPA + RTORDPA
ms = pd.read_parquet(f"data/raw/ercot/ercot_{Y}_ordc_reserves_hourly.parquet").set_index("hour").reindex(range(8760))
lam, orpa, ordpa, prc = (ms[c].to_numpy(float) for c in ("system_lambda", "rtorpa", "rtordpa", "prc"))
print("\n(a2) measured split in ACTUAL>=1k hours (n=%d):" % tight_a.sum())
k = tight_a
print(f"  actual LW {a[k].mean():.0f} = lambda {np.nanmean(lam[k]):.0f} + RTORPA {np.nanmean(orpa[k]):.0f} + RTORDPA {np.nanmean(ordpa[k]):.0f}  (+basis rest)")
print(f"  model   LW {N['m'][k].mean():.0f}; model ordc_adder {N['ordc'][k].mean():.0f}; model price-ordc {np.mean(N['m'][k]-N['ordc'][k]):.0f}")
print(f"  measured PRC mean {np.nanmean(prc[k]):.0f} MW, p10 {np.nanpercentile(prc[k],10):.0f}")
for thr in (200, 1000):
    kk = a >= thr
    print(f" actual>={thr}: n={kk.sum()}  lambda>={thr}: {(lam>=thr).sum()}   hours where RTORPA>=100: {(orpa>=100).sum()}")
print("  sum over year: RTORPA contributes %.2f $/MWh, RTORDPA %.2f, lambda mean %.2f" % (np.nanmean(orpa), np.nanmean(ordpa), np.nanmean(lam)))
print("  model: ordc_adder annual mean %.2f" % N["ordc"].mean())
# model energy-component vs measured lambda in actual-tight hours
print("\n  hour table (actual>=1k): ts, act, lam, rtorpa, prc | model, model_ordc")
ti = np.where(k)[0]
tt = pd.DataFrame({"ts": pd.to_datetime("2023-01-01") + pd.to_timedelta(ti, unit="h"), "act": a[ti].round(0), "lam": lam[ti].round(0),
                   "rtorpa": orpa[ti].round(0), "prc": prc[ti].round(0), "model": N["m"][ti].round(0), "m_ordc": N["ordc"][ti].round(0),
                   "m_rp": N["rp"][ti].round(0), "m_ordc_sf": N["sf"]["ercot_ordc_total"].iloc[ti].round(0).to_numpy()})
print(tt.to_string())
