"""SPP-57b PRECOMMIT §4: grade the rule-29(a) screen against the STOP gate (SPP-57's instrument; the OK<->S
named direction is OK->S per the sps_tie-alone identification; census read from spp57b/), beside the keeper-2 control.

usage: grade_screen.py <bundle_dir> <year> [control_bundle_dir]
Reads the bundle's flows.parquet (gitignored, per-link hourly MW), hourly/system_<year>.parquet,
hourly/class_hourly_<year>.parquet; the wind potential from docs/handoffs/spp57b/census.csv; the
measured spreads from spread_identification.csv; the EIA-923/930 family actuals from
calibration_reference.json. Every number is printed; the gate verdict is graded as written."""

import calendar
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
bundle = Path(sys.argv[1])
year = int(sys.argv[2])
control = (
    Path(sys.argv[3])
    if len(sys.argv) > 3
    else REPO / "results/calibration/spp42_crosswalk_B"
)
pd.set_option("display.width", 250)

# ---- link liveness + direction (leg i) -------------------------------------------------------
fl = pd.read_parquet(bundle / "flows.parquet")
fl = fl[(fl["pass"] == "P1") & (fl["year"] == year)]
from market_sim.config.iso_configs import get_iso_config  # noqa: E402

cfg = get_iso_config("SPP")
ttc = {(ln.from_zone, ln.to_zone): ln.ttc_mw for ln in cfg.links}
NAMED = {
    ("SPP-North", "SPP-Oklahoma"): +1,
    ("SPP-Oklahoma", "SPP-South"): +1,
}  # +1 = positive flow: N->OK on link 1, OK->S on link 2 (both data-named, PRECOMMIT-spp-57b §3.2)
mstart = np.cumsum([0] + [calendar.monthrange(2023, m)[1] * 24 for m in range(1, 13)])
leg_i = {}
print(f"\n=== LEG (i) links, {year} ===")
for (a, b), grp in fl.groupby(["from_zone", "to_zone"]):
    mw = grp.sort_values("hour")["mw"].to_numpy()
    T = ttc[(a, b)]
    pos = mw >= T - 1.0
    neg = mw <= -T + 1.0
    at = pos | neg
    named_sign = NAMED[(a, b)]
    named_hours = int(pos.sum()) if named_sign > 0 else int(neg.sum())
    share_named = named_hours / max(int(at.sum()), 1)
    live = at.mean() >= 0.05
    direction_ok = share_named >= 0.55
    leg_i[(a, b)] = (live, direction_ok)
    print(
        f"{a}->{b} TTC {T:,.0f}: at bound {int(at.sum())} h ({at.mean() * 100:.1f} %) — positive {int(pos.sum())} h, negative {int(neg.sum())} h; "
        f"named direction {'+' if named_sign > 0 else '-'} share {share_named * 100:.1f} % | flow mean {mw.mean():+.0f} p10 {np.percentile(mw, 10):+.0f} p50 {np.median(mw):+.0f} p90 {np.percentile(mw, 90):+.0f} | "
        f"live(>=5%)={live} direction(>=55%)={direction_ok}"
    )
    hoy = np.arange(len(mw))
    month = np.searchsorted(mstart, hoy, side="right")
    hod = hoy % 24
    print("   by month +bound:", [int(pos[month == m].sum()) for m in range(1, 13)])
    print("   by month -bound:", [int(neg[month == m].sum()) for m in range(1, 13)])
    print("   by hour-of-day +bound:", [int(pos[hod == h].sum()) for h in range(24)])
    print("   by hour-of-day -bound:", [int(neg[hod == h].sum()) for h in range(24)])

# ---- prices / spreads (leg ii) -------------------------------------------------------------------
sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
sy = sy[sy["pass"] == "P1"]
P = sy.pivot_table(index="hour", columns="zone", values="price")
dem = sy.pivot_table(index="hour", columns="zone", values="demand")
ok_n = P["SPP-Oklahoma"] - P["SPP-North"]
s_ok = P["SPP-South"] - P["SPP-Oklahoma"]
spread = pd.read_csv(REPO / "docs/handoffs/spp57/spread_identification.csv")
meas = spread[spread.year == year].set_index("spread")
print(f"\n=== LEG (ii) spreads, {year} ===")
leg_ii = True
for name, s, key in (("OK-N", ok_n, "ok_n"), ("S-OK", s_ok, "s_ok")):
    m = float(meas.loc[key, "signed_mean"])
    ok = np.sign(s.mean()) == np.sign(m)
    leg_ii &= bool(ok)
    print(
        f"{name}: model annual mean {s.mean():+.2f} (mean|.| {s.abs().mean():.2f}, p90|.| {s.abs().quantile(0.9):.2f}) vs measured {m:+.2f} (mean|.| {meas.loc[key, 'mean_abs']:.2f}, p90 {meas.loc[key, 'p90_abs']:.2f}) -> sign {'MATCH' if ok else 'MISMATCH'}"
    )
    month = np.searchsorted(mstart, s.index.to_numpy(), side="right")
    print(
        "   model monthly mean:",
        [round(float(s[month == mm].mean()), 1) for mm in range(1, 13)],
    )
lw = (P * dem).sum().sum() / dem.sum().sum()
print(
    f"load-weighted price {lw:.2f}; zone means N {P['SPP-North'].mean():.2f} OK {P['SPP-Oklahoma'].mean():.2f} S {P['SPP-South'].mean():.2f}"
)
neg_hours = {z: int((P[z] < 0).sum()) for z in P.columns}
print(
    f"negative-price hours by zone {neg_hours}; total zone-hours {sum(neg_hours.values())}; hours any zone < 0: {int((P < 0).any(axis=1).sum())}; hours > $200 (any zone) {int((P > 200).any(axis=1).sum())}; > $1000 {int((P > 1000).any(axis=1).sum())}; min {P.min().min():.2f} max {P.max().max():.2f}"
)

# ---- unserved (leg iv) -------------------------------------------------------------------------
sl = sy[sy["slack"] > 1e-6]
print(f"\n=== LEG (iv) unserved, {year} ===")
print(
    f"slack hours {sl['hour'].nunique()}, MWh {sl['slack'].sum():.1f}, by zone {sl.groupby('zone')['slack'].sum().round(1).to_dict()}; hours {sorted(sl['hour'].unique().tolist())[:20]}"
)
allowed = {8507}
leg_iv = set(sl["hour"].unique().tolist()) <= allowed
print(
    f"dump MWh {sy['dump'].sum():.1f}; leg (iv) inside the control set {allowed}: {leg_iv}"
)

# ---- fuel families + re-curtailment (legs iii, v) ------------------------------------------------
ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
ch = ch[ch["pass"] == "P1"]
twh = (ch.groupby("klass", observed=True)["mw"].sum() / 1e6).round(3)
census = pd.read_csv(REPO / "docs/handoffs/spp57b/census.csv")
wpot = float(census[census.year == year]["wind_potential_twh"].sum())
wdel = float(twh.get("wind", 0.0))
recurt = 1 - wdel / wpot
fam = {
    "coal": sum(float(twh.get(k, 0.0)) for k in twh.index if str(k).startswith("COAL")),
    "gas_cc": float(twh.get("CC_REGULAR", 0.0)) + float(twh.get("CC_CHP", 0.0)),
    "gas_ct": float(twh.get("CT_PEAKER", 0.0)) + float(twh.get("CT_CHP", 0.0)),
    "gas_st": float(twh.get("ST_GAS", 0.0)) + float(twh.get("ST_CHP", 0.0)),
    "nuclear": float(twh.get("nuclear", 0.0)),
    "hydro": float(twh.get("hydro", 0.0)),
    "wind": wdel,
    "solar": float(twh.get("solar", 0.0)),
}
ref = json.loads(
    (REPO / "data/raw/_validation-source/calibration_reference.json").read_text()
)
actual = ref["isos"]["SPP"][str(year)]["generation_twh"]
print(
    f"\n=== LEG (iii) re-curtailment, {year} === wind delivered {wdel:.2f} TWh / potential {wpot:.2f} -> re-curtailment {recurt * 100:.2f} % (STOP if exactly 0.0)"
)
print(f"=== LEG (v) fuel families vs reference, {year} ===")
leg_v = True
for k, v in fam.items():
    a = actual.get(k)
    r = v / a if a else float("nan")
    inband = (0.1 <= r <= 10) if a else True
    leg_v &= inband
    print(
        f"  {k:8s} model {v:7.2f} actual {a if a is not None else float('nan'):7.2f} ratio {r:5.2f} {'ok' if inband else 'OUT'}"
    )
print("by class TWh:", twh.to_dict())

# ---- control (form 4) ----------------------------------------------------------------------------
cs = pd.read_parquet(control / "hourly" / f"system_{year}.parquet")
cs = cs[cs["pass"] == "P1"]
CP = cs.pivot_table(index="hour", columns="zone", values="price")
cch = pd.read_parquet(control / "hourly" / f"class_hourly_{year}.parquet")
cch = cch[cch["pass"] == "P1"]
ctwh = (cch.groupby("klass", observed=True)["mw"].sum() / 1e6).round(3)
csl = cs[cs["slack"] > 1e-6]
print(
    f"\n=== CONTROL {control.name}, {year} === load-weighted price {((CP * cs.pivot_table(index='hour', columns='zone', values='demand')).sum().sum() / cs['demand'].sum()):.2f}; "
    f"|S-N| mean {(CP['SPP-South'] - CP['SPP-North']).abs().mean():.2f}; negative hours (any zone) {int((CP < 0).any(axis=1).sum())}; unserved {csl['slack'].sum():.1f} MWh in {csl['hour'].nunique()} h; by class {ctwh.to_dict()}"
)

verdict = (
    all(v for pair in leg_i.values() for v in pair)
    and leg_ii
    and (recurt > 0)
    and leg_iv
    and leg_v
)
print(
    f"\n===== STOP GATE {year}: leg(i) {leg_i} | leg(ii) {leg_ii} | leg(iii) recurt>0 {recurt > 0} | leg(iv) {leg_iv} | leg(v) {leg_v} -> {'PASS (nothing promoted)' if verdict else 'STOP'}"
)
