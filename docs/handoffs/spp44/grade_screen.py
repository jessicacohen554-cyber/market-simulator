"""SPP-44 PRECOMMIT §4: grade the rule-29(a) screen (or any full-span year) against
the ex-ante STOP gate, beside its control.

usage: uv run python docs/handoffs/spp44/grade_screen.py <arm_bundle> <control_bundle> <year>

Reads ONLY: the two bundles' ``hourly/class_hourly_<year>.parquet`` and
``hourly/system_<year>.parquet``; the arm's ``floors/<year>_P1.npz`` (the LP's
own min_gen + mechanism ids) and ``legitimacy_diagnostics.json`` (written by
``scripts/legitimacy_diagnostics.py --bundle <arm> --iso SPP --years <year>``
before this runs); the CAMPD plant online matrix
``docs/handoffs/spp44/campd_online_<year>.parquet``; the committed bench part
``frontend/data/backcast/bench/SPP/<year>.json.gz``; and the EIA-930 family
hourlies through the SAME loader the registration path uses. Every number is
printed; each leg is graded exactly as the PRECOMMIT wrote it.
"""

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.plant_taxonomy import classes_for_fuel930  # noqa: E402
from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402
from market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_SPP_GAS_COMMITMENT_BRIDGE,
)
from scripts.calibration_verdict import (  # noqa: E402
    DISP_R_FLOOR,
    FUELMIX_SHARE_PP,
    _fuelmix_vol_band,
)

arm = Path(sys.argv[1])
ctl = Path(sys.argv[2])
year = int(sys.argv[3])
T = 8760
TARGET = ("CC_REGULAR", "ST_GAS", "CT_PEAKER")
NON_TARGET = ("COAL_PRB", "COAL_LIGNITE", "COAL_BIT", "CC_CHP", "CT_CHP", "ST_CHP")
pd.set_option("display.width", 250)


def class_hourly(b: Path) -> pd.DataFrame:
    d = pd.read_parquet(b / "hourly" / f"class_hourly_{year}.parquet")
    d = d[(d["pass"] == "P1") & (d["year"] == year)]
    return d.pivot_table(
        index="hour", columns="klass", values="mw", aggfunc="sum"
    ).reindex(range(T), fill_value=0.0)


def system(b: Path) -> pd.DataFrame:
    d = pd.read_parquet(b / "hourly" / f"system_{year}.parquet")
    return d[(d["pass"] == "P1") & (d["year"] == year)]


def pearson(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


ch_a, ch_c = class_hourly(arm), class_hourly(ctl)
sy_a, sy_c = system(arm), system(ctl)
bench = json.load(
    gzip.open(REPO / "frontend/data/backcast/bench/SPP" / f"{year}.json.gz")
)
cfull = bench["bench"]["classFull"]
e930 = load_eia_hourly_benchmark("SPP", year) or {}

verdicts = {}

# ---- leg (i): window agreement with CAMPD --------------------------------------------------
print(f"\n=== leg (i) window agreement — {year} ===")
z = np.load(arm / "floors" / f"{year}_P1.npz", allow_pickle=False)
mg, mech = z["min_gen"], z["mechanism"]
pcode = z["plant_code"]
pgroup = z["plant_group"] if "plant_group" in z else np.array([""] * len(pcode))
on = pd.read_parquet(REPO / "docs/handoffs/spp44" / f"campd_online_{year}.parquet")
bridge = (mech == MECH_SPP_GAS_COMMITMENT_BRIDGE) & (mg > 0)
V_twh = float(mg[bridge].sum()) / 1e6
print(
    f"bridge-floored unit-hours {int(bridge.sum())}, floor volume V = {V_twh:.4f} TWh"
)
uncond = {}
for k in ("CC_REGULAR", "ST_GAS"):
    rows = np.flatnonzero(pgroup == k)
    w_on = w_all = 0.0
    n_cov = n_unc = 0
    cov_mw = 0.0
    cols = set(on.columns)
    for g in rows:
        pc = str(int(pcode[g]))
        h = np.flatnonzero(bridge[g])
        if h.size == 0:
            continue
        if pc not in cols:
            n_unc += 1
            continue
        n_cov += 1
        w = mg[g, h]
        w_all += float(w.sum())
        w_on += float(w[on[pc].to_numpy()[h]].sum())
        cov_mw += float(w.sum())
    agree = w_on / w_all if w_all > 0 else float("nan")
    plants_k = [c for c in on.columns if c in {str(int(p)) for p in pcode[pgroup == k]}]
    uncond[k] = float(on[plants_k].to_numpy().mean()) if plants_k else float("nan")
    bar = max(0.60, uncond[k] + 0.10)
    ok = agree >= bar if agree == agree else True
    verdicts[f"(i) {k}"] = "pass" if ok else "STOP"
    print(
        f"{k}: floored plants with CAMPD series {n_cov} (without {n_unc}); "
        f"agreement (floor-MWh-weighted) {agree:.3f} vs unconditional online {uncond[k]:.3f} "
        f"(lift {agree - uncond[k]:+.3f}); bar {bar:.2f} -> {verdicts[f'(i) {k}']}"
    )

# ---- leg (ii): direction and magnitude ------------------------------------------------------
print(f"\n=== leg (ii) direction / magnitude — {year} ===")
E_a = ch_a.sum() / 1e6
E_c = ch_c.sum() / 1e6
dE = (E_a - E_c).reindex(sorted(set(E_a.index) | set(E_c.index)), fill_value=0.0)
tab = pd.DataFrame({"control_twh": E_c, "arm_twh": E_a, "delta_twh": dE}).round(3)
print(tab.to_string())
d_slow = float(dE.get("CC_REGULAR", 0.0) + dE.get("ST_GAS", 0.0))
d_ct = float(dE.get("CT_PEAKER", 0.0))
ok_dir = d_slow > 0 and (0.25 * V_twh <= d_slow <= 2.0 * V_twh) and d_ct <= 0.05
verdicts["(ii)"] = "pass" if ok_dir else "STOP"
print(
    f"dE(CC+ST) = {d_slow:+.4f} TWh vs band [{0.25 * V_twh:.4f}, {2.0 * V_twh:.4f}] (V {V_twh:.4f}); "
    f"dE(CT) = {d_ct:+.4f} TWh (STOP if > +0.05; |dE| < 0.05 reported as 'CT not displaced') -> {verdicts['(ii)']}"
)

# ---- leg (iii): C8 forced share + D-4 -------------------------------------------------------
print(f"\n=== leg (iii) C8 / D-4 — {year} ===")
lp = arm / "legitimacy_diagnostics.json"
if lp.exists():
    ld = json.load(open(lp))
    d2 = [
        r
        for r in ld["diagnostics"]["D2"]["rows"]
        if r.get("year") == year and r.get("mechanism") == "spp_gas_commitment_bridge"
    ]
    for r in d2:
        print(
            f"D-2 {r['class']}: forced {r['forced_twh']:.4f} / class {r['class_total_twh']:.3f} TWh "
            f"= {r['share_of_class']:.3f}"
        )
    over = [
        r
        for r in d2
        if r["class"] in ("CC_REGULAR", "ST_GAS") and r["share_of_class"] > 0.30
    ]
    d4 = [
        r
        for r in ld["diagnostics"]["D4"]["rows"]
        if r.get("year") == year
        and "spp_gas_commitment_bridge" in str(r.get("floor", ""))
    ]
    for r in d4:
        print(f"D-4 {r}")
    d4_bad = [r for r in d4 if r.get("offwindow_share", 0.0) > 0.05]
    verdicts["(iii)"] = "STOP" if (over or d4_bad) else "pass"
    print(f"-> {verdicts['(iii)']}")
else:
    verdicts["(iii)"] = "NOT RUN"
    print("legitimacy_diagnostics.json absent on the arm — run the diagnostics first")

# ---- leg (iv): non-target load-bearing rows -------------------------------------------------
print(f"\n=== leg (iv) non-target C1 / C2 / C4 — {year} ===")


def c1_rows(E: pd.Series, demand_twh: float):
    m_gen = float(E.sum())
    a_gen = float(sum(v for v in cfull.values()))
    band = _fuelmix_vol_band(demand_twh, a_gen)
    out = {}
    for c, a in cfull.items():
        m = float(E.get(c, 0.0))
        pp = 100.0 * m / m_gen - 100.0 * float(a) / a_gen
        out[c] = (
            m,
            float(a),
            m - float(a),
            pp,
            abs(m - a) <= band and abs(pp) <= FUELMIX_SHARE_PP,
        )
    return out, band


dem_a = float(sy_a.groupby("hour")["demand"].sum().sum()) / 1e6
dem_c = float(sy_c.groupby("hour")["demand"].sum().sum()) / 1e6
r_a, band_a = c1_rows(E_a, dem_a)
r_c, band_c = c1_rows(E_c, dem_c)
print(f"C1 band: volume ±{band_a:.2f} TWh, share ±{FUELMIX_SHARE_PP} pp")
flip = []
for c in sorted(set(r_a) | set(r_c)):
    ma, aa, da, ppa, oka = r_a.get(c, (0, 0, 0, 0, True))
    mc, ac, dc, ppc, okc = r_c.get(c, (0, 0, 0, 0, True))
    tag = "target" if c in TARGET else ("non-target" if c in NON_TARGET else "other")
    print(
        f"  {c:13s} actual {aa:7.2f} | control {mc:7.2f} ({dc:+6.2f}, {ppc:+5.2f} pp, {'in' if okc else 'OUT'}) "
        f"| arm {ma:7.2f} ({da:+6.2f}, {ppa:+5.2f} pp, {'in' if oka else 'OUT'})  [{tag}]"
    )
    if c in NON_TARGET and okc and not oka:
        flip.append(c)
# C4 family hourly fit (the registration path's construction, reproduced)
c4 = {}
for fuel in ("gas", "coal"):
    classes = classes_for_fuel930(fuel)
    ob = e930.get(fuel)
    if ob is None:
        continue
    ob = np.asarray(ob, float)
    if fuel == "gas" and "other" in e930:
        fold = max(
            0.0,
            float(cfull.get("OTHER", 0.0))
            + float(cfull.get("biomass", 0.0))
            - float(np.asarray(e930["other"]).sum()) / 1e6,
        )
        ob = ob - fold * 1e6 / T
    for name, ch in (("control", ch_c), ("arm", ch_a)):
        ms = sum(
            (ch[c].to_numpy(float) for c in classes if c in ch.columns), np.zeros(T)
        )
        c4[(fuel, name)] = pearson(ms, ob)
    print(
        f"C4 {fuel}: r control {c4[(fuel, 'control')]:.3f} | arm {c4[(fuel, 'arm')]:.3f} (floor {DISP_R_FLOOR})"
    )
c4_flip = [
    f
    for f in ("gas", "coal")
    if (f, "control") in c4
    and c4[(f, "control")] is not None
    and c4[(f, "control")] >= DISP_R_FLOOR
    and (c4[(f, "arm")] or 0) < DISP_R_FLOOR
]
verdicts["(iv)"] = "STOP" if (flip or c4_flip) else "pass"
print(f"non-target C1 flips in->OUT: {flip}; C4 flips: {c4_flip} -> {verdicts['(iv)']}")

# ---- reported, never gated -----------------------------------------------------------------
print(f"\n=== reported (never gated) — {year} ===")
for name, sy in (("control", sy_c), ("arm", sy_a)):
    lw = float((sy["price"] * sy["demand"]).sum() / sy["demand"].sum())
    zm = sy.groupby("hour")["price"].mean()
    print(
        f"{name}: load-weighted price ${lw:.2f}; hours > $200 (zone mean) {int((zm > 200).sum())}; "
        f"negative hours {int((zm < 0).sum())}; unserved {float(sy['slack'].sum()):.1f} MWh in "
        f"{int((sy.groupby('hour')['slack'].sum() > 0).sum())} h; dump {float(sy['dump'].sum()):.1f} MWh"
    )
print("\nVERDICTS:", verdicts)
print(
    "SCREEN:",
    "KILLED" if any(v == "STOP" for v in verdicts.values()) else "CLEARS the STOP gate",
)
