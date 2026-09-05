"""capx D54 zero-solve pre-declaration instrument: the PJM clearing half on the committed ledgers.

Reads the committed T1-H bundles (D45-R control `pjm-t1h`, D48 arm `pjm-t1h-d48-devintage`) and
the D48 zero-solve position instrument (BOTH arm = the D48 basis), builds the per-unit sell-offer
stack from the retirement screen's own operands (going-forward cost, E&AS net revenue), clears it
against the committed vintage VRR curve, and prints the clearing price / cleared quantity beside
the published BRA record (validation observables, never inputs). Zero solves; zero free parameters.
"""
import json, sys, glob
sys.path.insert(0, "src")
from market_sim.config.capacity_market import (resolve_demand_curve_vintage, evaluate_demand_curve,
    THERMAL_ELCC_CLASS_RATING_BY_ISO)
from market_sim.config.constants import EFORD

D48 = json.load(open("docs/handoffs/d48/devintage-positions-d45r-2026-09-04.json"))["years"]
PUB = {r["delivery_year"]: r for r in json.load(open("docs/handoffs/d45/published-positions-2026-09-03.json"))["pjm"]}
# BRA 2024/2025 Report Table 7 (RPM-only, UCAP): offered / cleared by resource type, 2021/22..2024/25
T7 = {"2021/2022": {"coal": (44936, 39022), "gas": (77514, 74814), "nuclear": (30561, 19918), "oil": (5218, 3955), "dr": (11887, 11126)},
      "2022/2023": {"coal": (33935, 27411), "gas": (75526, 69292), "nuclear": (26855, 21050), "oil": (2419, 2271), "dr": (10513, 8812)},
      "2023/2024": {"coal": (26968, 21615), "gas": (74552, 70978), "nuclear": (26365, 26365), "oil": (1901, 1820), "dr": (10117, 8096)},
      "2024/2025": {"coal": (25060, 21478), "gas": (73714, 71489), "nuclear": (26024, 25818), "oil": (2150, 1899), "dr": (10146, 7985)}}
DY = {2022: "2022/2023", 2023: "2023/2024", 2024: "2024/2025", 2025: "2025/2026"}
ELCC = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]

def accr(fuel, year):  # D48 basis: UCAP (class EFORd) through DY 2024/25, ELCC class from 2025/26
    return (1.0 - EFORD.get(fuel, 0.08)) if year <= 2024 else ELCC.get(fuel, 1.0 - EFORD.get(fuel, 0.08))

def curve_kw_yr(year, pos):
    v = resolve_demand_curve_vintage("PJM", year)
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr

def clear(stack, req, year, zero_mw):
    stack = sorted(stack, key=lambda r: r[0]); q = zero_mw
    d = lambda Q: curve_kw_yr(year, Q / req) * 1000.0 / 365.0
    cleared = set()
    if d(q) <= 0.0:
        return 0.0, q, cleared, "zero_block_past_zero_cross"
    for offer, mw, tag in stack:
        q0, q1 = q, q + mw
        if d(q0) < offer: return d(q0), q0, cleared, "curve_sets_price_between_offers"
        if d(q1) >= offer: q = q1; cleared.add(tag); continue
        lo, hi = q0, q1
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if d(mid) >= offer: lo = mid
            else: hi = mid
        cleared.add(tag); return offer, lo, cleared, "marginal_offer_sets_price"
    return d(q), q, cleared, "all_offers_clear_curve_sets_price"

out = {}
for bundle, label in (("results/hindcast/pjm-2021-2025-realized-t1h-d45r", "control pjm-t1h"),
                      ("results/hindcast/pjm-2021-2025-realized-t1h-d48-devintage", "arm pjm-t1h-d48-devintage")):
    print(f"\n#### {label} ({bundle})"); out[label] = {}
    for year in (2022, 2023, 2024, 2025):
        p = glob.glob(f"{bundle}/PJM/*/evolution_{year}.json")
        led = json.load(open(p[0])); ev = led.get("pipeline_events") or []
        rows = [e for e in ev if e["event"] in ("decided", "entry_capped", "re_confirmed")]
        base = D48[str(year)]["arms"]["BOTH"]; req = base["requirement_mw"]; firm = base["firm_mw"]
        pub = PUB[DY[year]]; pub_day = pub["real_price_kw_yr"] * 1000 / 365
        if not rows:  # every unit passes: every offer is $0, clearing == census evaluation
            pos = firm / req; price = curve_kw_yr(year, pos) * 1000 / 365
            print(f"{year} DY {DY[year]}: no failing unit — all offers $0; clearing = census: pos {pos:.4f}, price {price:.2f} $/MW-day ({price*365/1000:.2f} $/kW-yr); published {pub_day:.2f} $/MW-day at pos {pub['pos_cleared']:.4f}")
            out[label][year] = {"all_zero_offers": True, "position": pos, "price_mw_day": price, "published_price_mw_day": pub_day, "published_pos_cleared": pub["pos_cleared"]}
            continue
        stack = []; fail_firm = 0.0; fuel_of = {}; name_of = {}; eas = {}; gfc = {}
        for e in rows:
            a = accr(e["fuel"], year); fmw = e["mw"] * a; fail_firm += fmw
            net_eas = e["net_revenue_usd"] - e.get("capacity_revenue_usd", 0.0)
            offer = max(0.0, e["going_forward_cost_usd"] - net_eas) / fmw / 365.0 if fmw > 0 else 0.0
            stack.append((offer, fmw, e["unit_id"])); fuel_of[e["unit_id"]] = e["fuel"]; name_of[e["unit_id"]] = e["mw"]; eas[e["unit_id"]] = net_eas; gfc[e["unit_id"]] = e["going_forward_cost_usd"]
        zero = firm - fail_firm
        price, q, cleared, how = clear(stack, req, year, zero)
        pay = price * 365.0
        unc_firm, unc_name, above_pub = {}, {}, {}
        for o, m, t in stack:
            f = fuel_of[t]
            if t not in cleared: unc_firm[f] = unc_firm.get(f, 0) + m; unc_name[f] = unc_name.get(f, 0) + name_of[t]
            if o > pub_day: above_pub[f] = above_pub.get(f, 0) + m
        # cleared units that still fail the bar at the cleared price (they retire anyway)
        cleared_fail = {}
        for o, m, t in stack:
            if t in cleared and eas[t] + pay * m < gfc[t]:
                cleared_fail[fuel_of[t]] = cleared_fail.get(fuel_of[t], 0) + name_of[t]
        # inverse: the model stack's offer at the PUBLISHED cleared position
        target = pub["pos_cleared"] * req; cum = zero; at_pub = 0.0
        for o, m, t in sorted(stack):
            if cum + m >= target: at_pub = o; break
            cum += m
        t7 = T7[DY[year]]
        print(f"{year} DY {DY[year]}: req {req:,.0f} firm {firm:,.0f} zero-offer {zero:,.0f} failing {fail_firm:,.0f} firm / {sum(name_of.values()):,.0f} nameplate ({len(rows)} units)")
        print(f"   DESIGN: price {price:7.2f} $/MW-day ({price*365/1000:5.2f} $/kW-yr)  cleared {q:,.0f}  pos {q/req:.4f}  [{how}]")
        print(f"   PUBLISHED (observable): price {pub_day:7.2f} $/MW-day ({pub['real_price_kw_yr']:5.2f} $/kW-yr)  pos cleared {pub['pos_cleared']:.4f}  pos offered {pub['pos_offered']:.4f}  Δpos {100*(q/req-pub['pos_cleared']):+.2f} pts")
        print(f"   uncleared firm MW by fuel: " + ", ".join(f"{k} {v:,.0f}" for k, v in sorted(unc_firm.items())) + f"  | total {sum(unc_firm.values()):,.0f} (nameplate {sum(unc_name.values()):,.0f})")
        print(f"   BRA Table 7 uncleared (offered−cleared, UCAP): coal {t7['coal'][0]-t7['coal'][1]:,} gas {t7['gas'][0]-t7['gas'][1]:,} nuclear {t7['nuclear'][0]-t7['nuclear'][1]:,} oil {t7['oil'][0]-t7['oil'][1]:,} DR {t7['dr'][0]-t7['dr'][1]:,}")
        print(f"   model offers ABOVE the published price, firm MW by fuel: " + ", ".join(f"{k} {v:,.0f}" for k, v in sorted(above_pub.items())) + f" | total {sum(above_pub.values()):,.0f}")
        print(f"   model stack's marginal offer AT the published cleared position: {at_pub:.2f} $/MW-day (published price {pub_day:.2f})")
        print(f"   cleared-but-still-failing nameplate (retire anyway): " + (", ".join(f"{k} {v:,.0f}" for k, v in sorted(cleared_fail.items())) or "none"))
        out[label][year] = {"requirement_mw": req, "firm_mw": firm, "zero_offer_mw": zero, "failing_firm_mw": fail_firm, "failing_nameplate_mw": sum(name_of.values()),
            "n_failing": len(rows), "price_mw_day": price, "cleared_mw": q, "position": q / req, "how": how,
            "published": {"price_mw_day": pub_day, "pos_cleared": pub["pos_cleared"], "pos_offered": pub["pos_offered"], "table7_uncleared": {k: v[0]-v[1] for k, v in t7.items()}},
            "uncleared_firm_by_fuel": unc_firm, "uncleared_nameplate_by_fuel": unc_name, "offers_above_published_by_fuel": above_pub,
            "marginal_offer_at_published_pos": at_pub, "cleared_but_failing_nameplate_by_fuel": cleared_fail}
json.dump(out, open(sys.argv[1], "w"), indent=1) if len(sys.argv) > 1 else None
# forward: the 2028/29 floor vs a zero-E&AS offer on the ELCC basis
print("\n2028/29+ floor check (175 $/MW-day UCAP) vs a ZERO-E&AS offer at the screen bar on the ELCC class basis:")
bar = {"coal": 45*1.3, "gas_cc": 30.0, "gas_ct": 21.0, "gas_st": 35.0, "oil": 25.0, "nuclear": 130.0}
for f, b in bar.items():
    print(f"   {f:8s} bar {b:6.1f} $/kW-yr / ELCC {ELCC.get(f, 1-EFORD.get(f,0.08)):.2f} = {b/ELCC.get(f,1-EFORD.get(f,0.08))*1000/365:7.1f} $/MW-day  -> {'ABOVE floor: uncleared when E&AS≈0' if b/ELCC.get(f,1-EFORD.get(f,0.08))*1000/365 > 175 else 'below floor: always clears'}")
