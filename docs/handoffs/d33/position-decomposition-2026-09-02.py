"""D33 position decomposition: model vs real FCA, per delivery year (zero solves).

Reads the committed neiso-2023-2027-crossover-rcrepair evolution ledgers and the
committed published FCA record; evaluates HEAD's own vintage curves via the
repo's config machinery. All published numbers cite
data/raw/capacity-market/demand-curve/neiso/neiso.csv +
data/raw/capacity-market/icr-ara/neiso/ara_requirement_values.csv +
src/market_sim/config/capacity_market.py registry comments.
"""

import json
import sys

sys.path.insert(0, "src")
from market_sim.config.capacity_market import (  # noqa: E402
    MARKET_DESIGN,
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)

BASE = "results/hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c"

# Published record (committed rows; $ = $/kW-mo)
REAL = {
    2023: dict(
        fca=14, ccp="2023-2024", net_icr=32490.0, cleared=33956.0, price_mo=2.001
    ),
    2024: dict(
        fca=15, ccp="2024-2025", net_icr=33270.0, cleared=34621.0, price_mo=2.611
    ),
    2025: dict(
        fca=16, ccp="2025-2026", net_icr=31645.0, cleared=32810.0, price_mo=2.591
    ),
    2026: dict(
        fca=17, ccp="2026-2027", net_icr=30305.0, cleared=31370.0, price_mo=2.590
    ),
    2027: dict(
        fca=18, ccp="2027-2028", net_icr=30550.0, cleared=31556.0, price_mo=3.580
    ),
}
# Committed demand-resource CSO points ($ MW): FCA-17 initial 2,940 (capacity_market.py
# NEISO DR comment); ARA-3 CCP 2026/27 2,639.682 (2026 CELT 4.1); CCP 2027/28
# 2,604.224 (2025 CELT, incl. FCA-18) / 2,540.066 (2026 CELT, incl. ARA-1).
DR_REAL = {2026: 2940.0, 2027: 2604.224}  # FCA-vintage committed values
DR_BRACKET = (2600.0, 4000.0)  # FCAs 14-16: NOT in-repo; bracket only

PRM = PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]  # 30050/26648 - 1
F_DR = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]  # 2639.682/30050
TIE = ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]
ONE_PLUS = 1.0 + PRM  # 1.127666  (NetICR/CELT peak)
COMPOSITE = (1.0 - F_DR) * ONE_PLUS  # 1.028607
md = MARKET_DESIGN["NEISO"]

print(
    f"PRM={PRM:.6f}  f_DR={F_DR:.6f}  (1+PRM)={ONE_PLUS:.6f}  composite={COMPOSITE:.6f}  tie={TIE}"
)


def vintage_pay(year: int, pos: float) -> float:
    """$/kW-yr the HEAD vintage curve pays at reserve position pos."""
    v = resolve_demand_curve_vintage("NEISO", year)
    curve = v.demand_curve if v is not None else md.demand_curve
    anchor = (
        v.net_cone_curve_per_kw_yr if v is not None else md.net_cone_curve_per_kw_yr
    )
    return evaluate_demand_curve(curve, pos) * anchor


led = {y: json.load(open(f"{BASE}/evolution_{y}.json")) for y in range(2023, 2028)}

rows = []
prev_firm_post = None
for y in range(2023, 2028):
    d = led[y]
    peak = d["peak_demand_mw"]
    firm_post = peak * (1.0 + d["reserve_margin"])  # post-evolution accredited firm
    firm_enter = prev_firm_post if prev_firm_post is not None else firm_post
    prev_firm_post = firm_post

    req_net = peak * COMPOSITE  # HEAD requirement (DR-netted)
    req_raw = peak * ONE_PLUS  # before DR netting
    dr_model = req_raw - req_net  # model's own netted DR MW

    r = REAL[y]
    pos_model_net = firm_post / req_net  # what D28 reported
    pos_enter_net = firm_enter / req_net  # what the year's screen saw
    pos_model_raw = (firm_post + dr_model) / req_raw
    pos_real = r["cleared"] / r["net_icr"]
    price_real = r["price_mo"] * 12.0

    # two-term split of (model_raw - real): supply at model denom + requirement
    num_m, den_m, num_r, den_r = (
        firm_post + dr_model,
        req_raw,
        r["cleared"],
        r["net_icr"],
    )
    t_supply = (num_m - num_r) / den_m
    t_req = num_r * (den_r - den_m) / (den_m * den_r)
    t_conv = pos_model_net - pos_model_raw

    # repaired-denominator positions (net convention): firm / (NetICR - DR)
    dr_known = DR_REAL.get(y)
    if dr_known is not None:
        rp = firm_post / (r["net_icr"] - dr_known)
        rp_lo = rp_hi = rp
    else:
        rp_lo = firm_post / (r["net_icr"] - DR_BRACKET[0])
        rp_hi = firm_post / (r["net_icr"] - DR_BRACKET[1])
        rp = firm_post / (r["net_icr"] - sum(DR_BRACKET) / 2.0)

    rows.append(
        dict(
            y=y,
            fca=r["fca"],
            peak=peak,
            firm_post=firm_post,
            firm_enter=firm_enter,
            req_net=req_net,
            req_raw=req_raw,
            dr_model=dr_model,
            pos_model_net=pos_model_net,
            pos_enter_net=pos_enter_net,
            pos_model_raw=pos_model_raw,
            pos_real=pos_real,
            net_icr=r["net_icr"],
            cleared=r["cleared"],
            price_real=price_real,
            t_supply=t_supply,
            t_req=t_req,
            t_conv=t_conv,
            pay_head=vintage_pay(y, pos_model_net),
            pay_enter=vintage_pay(y, pos_enter_net),
            pay_repair=vintage_pay(y, rp),
            pay_repair_lo=vintage_pay(y, rp_lo),
            pay_repair_hi=vintage_pay(y, rp_hi),
            pay_at_real=vintage_pay(y, pos_real),
            rp=rp,
            rp_lo=rp_lo,
            rp_hi=rp_hi,
        )
    )

hdr = (
    "yr  FCA | peak    firmPost firmEnter| reqNet  reqRaw   NetICR | posNet posEnt posRaw posReal | "
    "gapNet  = conv + supply + req"
)
print("\n" + hdr)
for r in rows:
    gap = r["pos_model_net"] - r["pos_real"]
    print(
        f"{r['y']} FCA{r['fca']} | {r['peak']:7.0f} {r['firm_post']:8.0f} {r['firm_enter']:8.0f} | "
        f"{r['req_net']:7.0f} {r['req_raw']:7.0f} {r['net_icr']:7.0f} | "
        f"{r['pos_model_net']:.4f} {r['pos_enter_net']:.4f} {r['pos_model_raw']:.4f} {r['pos_real']:.4f} | "
        f"{gap * 100:+6.2f} = {r['t_conv'] * 100:+5.2f} {r['t_supply'] * 100:+6.2f} {r['t_req'] * 100:+6.2f} (pts)"
    )

print("\nsupply/requirement MW ledger (raw convention):")
for r in rows:
    print(
        f"{r['y']} FCA{r['fca']}: model supply {r['firm_post'] + r['dr_model']:8.0f} vs cleared {r['cleared']:8.0f} "
        f"(delta {r['firm_post'] + r['dr_model'] - r['cleared']:+7.0f}); "
        f"model req(raw) {r['req_raw']:8.0f} vs NetICR {r['net_icr']:8.0f} (delta {r['req_raw'] - r['net_icr']:+7.0f})"
    )

print("\ncurve pay $/kW-yr (HEAD vintage curves):")
print("yr  FCA | @modelNet @enterNet | @repaired [lo..hi] | @realPos | real clearing")
for r in rows:
    print(
        f"{r['y']} FCA{r['fca']} | {r['pay_head']:8.2f} {r['pay_enter']:9.2f} | "
        f"{r['pay_repair']:8.2f} [{r['pay_repair_hi']:6.2f}..{r['pay_repair_lo']:6.2f}] | "
        f"{r['pay_at_real']:8.2f} | {r['price_real']:8.2f}   (repaired pos {r['rp']:.4f} [{r['rp_lo']:.4f}..{r['rp_hi']:.4f}])"
    )

json.dump(
    rows,
    open(
        "docs/handoffs/d33/position-decomposition-rows-2026-09-02.json",
        "w",
    ),
    indent=1,
)
print("\nrows dumped.")
