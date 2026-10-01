"""R-ERCOT-12 phase 0: 2024 tight-hour under-pricing on committed keeper sidecars (zero LP).

Compares the keeper ``r_ercot11_parish_split_span`` with the superseded
``r_ercot10_parish_span`` (read from git history, ``fb116767^``) and the
committed actual LZ RT settlement series plus ERCOT's measured
lambda / RTORPA / RTORDPA / PRC split, hour by hour.

Usage: ``python3 scripts/probes/_r_ercot12_2024_tight_hours.py <old_hourly_dir>``.
Record: ``docs/records/ercot/FINDING-r-ercot-12-2024-tight-hours-2026-09-28.md``.
"""

import sys

sys.path[:0] = [".", "src", "scripts"]
import numpy as np
import pandas as pd
import scripts.data.derive_actual_lmp as D
from market_sim.config.iso_configs import get_iso_config

Y = 2024
NEW = "results/calibration/r_ercot11_parish_split_span/hourly"
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
    """Load-weighted model and actual RT price, both on the measured zone demand."""
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


def load(d):
    """Read one bundle's 2024 P1 hourlies into arrays/frames keyed by hour."""
    s = pd.read_parquet(f"{d}/system_{Y}.parquet")
    m, a = lw(s)
    s1 = s[s["pass"] == "P1"]
    g = s1.groupby("hour")
    rf = pd.read_parquet(f"{d}/reserve_family_{Y}.parquet")
    rf = rf[rf["pass"] == "P1"]
    fam = rf.pivot_table(index="hour", columns="family", values="dual", aggfunc="sum")
    sf = rf.pivot_table(
        index="hour", columns="family", values="shortfall_mw", aggfunc="sum"
    )
    held = rf.pivot_table(
        index="hour", columns="family", values="held_mw", aggfunc="sum"
    )
    req = rf.pivot_table(
        index="hour", columns="family", values="requirement_mw", aggfunc="sum"
    )
    ch = pd.read_parquet(f"{d}/class_hourly_{Y}.parquet")
    ch = ch[ch["pass"] == "P1"].pivot(index="hour", columns="klass", values="mw")
    st = pd.read_parquet(f"{d}/storage_{Y}.parquet")
    st = (
        st[st["pass"] == "P1"]
        .groupby("hour")[["charge_mw", "discharge_mw", "soc_mwh", "energy_cap_mwh"]]
        .sum()
    )
    return dict(
        m=m,
        a=a,
        slack=g.slack.sum().to_numpy(),
        dem=g.demand.sum().to_numpy(),
        rp=g.reserve_price.mean().to_numpy(),
        ordc=g.ordc_adder.mean().to_numpy(),
        fam=fam,
        sf=sf,
        held=held,
        req=req,
        ch=ch,
        st=st,
    )


N, O = load(NEW), load(OLD)
a = N["a"]
pd.set_option("display.width", 250)
print(
    f"LW model new {N['m'].mean():.2f} old {O['m'].mean():.2f} actual {a.mean():.2f}"
    f"  C3a new {(N['m'].mean() / a.mean() - 1) * 100:+.1f}% old {(O['m'].mean() / a.mean() - 1) * 100:+.1f}%"
)

print("\n(1) gap by ACTUAL band ($/MWh of annual LW mean; new | old):")
for lo, hi in (
    (-1e9, 0),
    (0, 25),
    (25, 50),
    (50, 100),
    (100, 200),
    (200, 1000),
    (1000, 1e9),
):
    k = (a >= lo) & (a < hi)
    print(
        f"  [{lo:>6},{hi:>6}) n={k.sum():5d} gap new={((N['m'] - a)[k]).sum() / 8760:+.2f} old={((O['m'] - a)[k]).sum() / 8760:+.2f}"
        f"  model new={N['m'][k].mean():7.1f} old={O['m'][k].mean():7.1f} act={a[k].mean():7.1f}"
    )

print("\n(2) gap by MODEL(new) band:")
for lo, hi in (
    (-1e9, 0),
    (0, 25),
    (25, 50),
    (50, 100),
    (100, 200),
    (200, 1000),
    (1000, 1e9),
):
    k = (N["m"] >= lo) & (N["m"] < hi)
    print(
        f"  [{lo:>6},{hi:>6}) n={k.sum():5d} gap={((N['m'] - a)[k]).sum() / 8760:+.2f}  model={N['m'][k].mean():7.1f} act={a[k].mean():7.1f}"
    )

# measured split
ms = (
    pd.read_parquet(f"data/raw/ercot/ercot_{Y}_ordc_reserves_hourly.parquet")
    .set_index("hour")
    .reindex(range(8760))
)
print("\nmeasured columns:", list(ms.columns))
lam, orpa, ordpa, prc = (
    ms[c].to_numpy(float) for c in ("system_lambda", "rtorpa", "rtordpa", "prc")
)
print(
    f"\n(3) annual means: actual LW {a.mean():.2f} | lambda {np.nanmean(lam):.2f} RTORPA {np.nanmean(orpa):.2f} RTORDPA {np.nanmean(ordpa):.2f}"
    f" | model LW {N['m'].mean():.2f} model ordc_adder {N['ordc'].mean():.2f} model reserve_price {N['rp'].mean():.2f}"
)
print(
    "  energy-only comparison: model(price-ordc) %.2f vs lambda %.2f"
    % (np.mean(N["m"] - N["ordc"]), np.nanmean(lam))
)
for lo, hi in ((-1e9, 50), (50, 100), (100, 200), (200, 1e9)):
    k = (a >= lo) & (a < hi)
    print(
        f"  actual[{lo},{hi}) n={k.sum()}: act {a[k].mean():.0f} = lam {np.nanmean(lam[k]):.0f} + orpa {np.nanmean(orpa[k]):.1f} + ordpa {np.nanmean(ordpa[k]):.1f}"
        f" | model {N['m'][k].mean():.0f} (ordc {N['ordc'][k].mean():.1f}); PRC act {np.nanmean(prc[k]):.0f}"
    )

# the tight hours: model(old) >100
T = O["m"] > 100
ti = np.where(T)[0]
print(
    f"\n(4) hours model(old)>$100: n={T.sum()} old {O['m'][T].mean():.0f} new {N['m'][T].mean():.0f} act {a[T].mean():.0f}"
    f" lam {np.nanmean(lam[T]):.0f} orpa {np.nanmean(orpa[T]):.1f} PRC {np.nanmean(prc[T]):.0f}"
)
Ta = a > 100
print(
    f"    hours actual>$100: n={Ta.sum()} old {O['m'][Ta].mean():.0f} new {N['m'][Ta].mean():.0f} act {a[Ta].mean():.0f}"
    f"; overlap with model(old)>100: {(T & Ta).sum()}; new>100 {(N['m'] > 100).sum()}"
)
ts = pd.to_datetime(f"{Y}-01-01") + pd.to_timedelta(ti, unit="h")
print(
    "    model(old)>100 by month:",
    pd.Series(ts.month).value_counts().sort_index().to_dict(),
)
print("    by hour-of-day:", pd.Series(ts.hour).value_counts().sort_index().to_dict())
tsa = pd.to_datetime(f"{Y}-01-01") + pd.to_timedelta(np.where(Ta)[0], unit="h")
print(
    "    actual>100 by month:",
    pd.Series(tsa.month).value_counts().sort_index().to_dict(),
)
print(
    "    actual>100 by hour-of-day:",
    pd.Series(tsa.hour).value_counts().sort_index().to_dict(),
)
print("  family duals mean in T  old/new:")
print(
    pd.DataFrame({"old": O["fam"].iloc[ti].mean(), "new": N["fam"].iloc[ti].mean()})
    .round(1)
    .to_string()
)
print("  family shortfall MW in T old/new:")
print(
    pd.DataFrame({"old": O["sf"].iloc[ti].mean(), "new": N["sf"].iloc[ti].mean()})
    .round(1)
    .to_string()
)
print("  class MW in T: old, new, delta")
cc = pd.DataFrame({"old": O["ch"].iloc[ti].mean(), "new": N["ch"].iloc[ti].mean()})
cc["d"] = cc.new - cc.old
print(cc.round(0).sort_values("d").to_string())
print(
    "  storage T old/new:",
    O["st"].iloc[ti].mean().round(0).to_dict(),
    N["st"].iloc[ti].mean().round(0).to_dict(),
)

# hour table for T sorted by gap
tt = pd.DataFrame(
    {
        "ts": ts,
        "act": a[ti].round(0),
        "lam": lam[ti].round(0),
        "orpa": orpa[ti].round(0),
        "prc": prc[ti].round(0),
        "old": O["m"][ti].round(0),
        "new": N["m"][ti].round(0),
        "n_ordc": N["ordc"][ti].round(0),
        "dem": N["dem"][ti].round(0),
    }
)
print("\n  hour table T (sorted by act):")
print(tt.sort_values("act", ascending=False).to_string())

# (5) where does the new-vs-old LW delta come from, by hour class
d = N["m"] - O["m"]
print(
    f"\n(5) LW delta new-old {d.mean():+.3f}: from T {d[T].sum() / 8760:+.3f}, rest {d[~T].sum() / 8760:+.3f}"
)

# (6) the single shed hour: how much of the old->new delta is the old keeper's load shed
shed_h = np.where(O["slack"] > 1e-6)[0]
print(
    f"\n(6) old-keeper shed hours {shed_h.tolist()} slack MWh {O['slack'][shed_h].round(2).tolist()}"
    f" price old {O['m'][shed_h].round(0).tolist()} new {N['m'][shed_h].round(0).tolist()} act {a[shed_h].round(0).tolist()}"
)
dh = d[shed_h].sum() / 8760
print(
    f"    LW delta from shed hour(s) {dh:+.3f} of total {d.mean():+.3f} ({dh / d.mean() * 100:.0f}%);"
    f" C3a pts from it {dh / a.mean() * 100:+.2f}, from all other hours {(d.mean() - dh) / a.mean() * 100:+.2f}"
)
