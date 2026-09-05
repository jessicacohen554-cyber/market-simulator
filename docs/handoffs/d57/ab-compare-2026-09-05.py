"""capx D57 A/B instrument: the clearing arms vs the census control and the D48 arm, zero solves.

Reads the committed T1-H bundles (control ``pjm-t1h`` D45-R, the D48 arm, and the two D57 arms once
solved) and prints, per screen year: the ``capacity_clearing`` ledger block beside the published BRA
record (VALIDATION OBSERVABLES, never inputs); the §3.5 identity (the screen's failing set vs the
auction's uncleared set) asserted off the ``pipeline_events`` rows; the offer stack above the
published price by fuel and the E&AS margin per unit that would put the cleared position AND the
price on the published pair (a statement about the operand, never a value applied); the pipeline
decision composition (decided / entry_capped nameplate by fuel); and the FC-3 score rows of every
leg side by side. Zero free parameters.

Run from the repo root: ``uv run python docs/handoffs/d57/ab-compare-2026-09-05.py [out.json]``
"""
import glob
import json
import sys

PUB = {
    r["delivery_year"]: r
    for r in json.load(open("docs/handoffs/d45/published-positions-2026-09-03.json"))["pjm"]
}
DY = {2022: "2022/2023", 2023: "2023/2024", 2024: "2024/2025", 2025: "2025/2026"}
LEGS = [
    ("control pjm-t1h", "results/hindcast/pjm-2021-2025-realized-t1h-d45r"),
    ("d48 pjm-t1h-d48-devintage", "results/hindcast/pjm-2021-2025-realized-t1h-d48-devintage"),
    ("arm A pjm-t1h-d57-clearing", "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing"),
    (
        "arm B pjm-t1h-d57-clearing-headbasis",
        "results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing-headbasis",
    ),
]
# The screen bars ($/kW-yr, nameplate) the offers are built from — read for the operand statement
# only (the ScenarioConfig defaults; identical in every leg).
sys.path.insert(0, "src")
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

_cfg = ScenarioConfig(iso="PJM", mode="forecast", hindcast=True)
BAR = {
    "coal": _cfg.fixed_om_coal * _cfg.retirement_fom_multiplier_coal,
    "gas_cc": _cfg.fixed_om_gas_cc,
    "gas_ct": _cfg.fixed_om_gas_ct,
    "gas_st": _cfg.fixed_om_gas_st,
    "oil": _cfg.fixed_om_oil,
    "nuclear": _cfg.fixed_om_nuclear,
}


def ledgers(bundle):
    out = {}
    for y in (2021, 2022, 2023, 2024, 2025):
        p = glob.glob(f"{bundle}/PJM/*/evolution_{y}.json")
        if p:
            out[y] = json.load(open(p[0]))
    return out


def score(bundle):
    p = glob.glob(f"{bundle}/PJM/*/score.json")
    return json.load(open(p[0])) if p else None


def fmt_by_fuel(d):
    return ", ".join(f"{k} {v:,.0f}" for k, v in sorted(d.items())) or "none"


report = {}
for label, bundle in LEGS:
    L = ledgers(bundle)
    if not L:
        print(f"\n#### {label}: NOT SOLVED ({bundle} absent)")
        continue
    print(f"\n#### {label} ({bundle}; key {list(glob.glob(f'{bundle}/PJM/*'))[0].split('/')[-1]})")
    report[label] = {"years": {}}
    for y in (2022, 2023, 2024, 2025):
        led = L.get(y)
        if led is None:
            continue
        rows = led.get("pipeline_events") or []
        cc = led.get("capacity_clearing")
        pub = PUB[DY[y]]
        pub_day = pub["real_price_kw_yr"] * 1000.0 / 365.0
        dec = {}
        cap = {}
        for e in rows:
            if e["event"] == "decided":
                dec[e["fuel"]] = dec.get(e["fuel"], 0.0) + e["mw"]
            elif e["event"] == "entry_capped":
                cap[e["fuel"]] = cap.get(e["fuel"], 0.0) + e["mw"]
        failing = {
            e["unit_id"]: e
            for e in rows
            if e["event"] in ("decided", "entry_capped", "re_confirmed")
        }
        yr = {
            "capacity_reserve_position": led.get("capacity_reserve_position"),
            "decided_mw_by_fuel": dec,
            "entry_capped_mw_by_fuel": cap,
            "n_failing": len(failing),
            "floor_retained_mw": sum(r["mw"] for r in led.get("floor_retained", [])),
            "published": {"price_mw_day": pub_day, "pos_cleared": pub["pos_cleared"]},
        }
        print(
            f"{y} DY {DY[y]}: entering census pos {led.get('capacity_reserve_position')}  "
            f"| decided {fmt_by_fuel(dec)} | entry_capped {fmt_by_fuel(cap)} "
            f"| floor_retained {yr['floor_retained_mw']:,.0f} MW | failing rows {len(failing)}"
        )
        if cc is None:
            print("   (no capacity_clearing block: the census evaluation priced this screen)")
            report[label]["years"][y] = yr
            continue
        ratio = cc["price_usd_per_mw_day"] / pub_day if pub_day > 0 else float("nan")
        print(
            f"   CLEARING: price {cc['price_usd_per_mw_day']:7.2f} $/MW-day "
            f"({cc['price_per_firm_mw_yr'] / 1000:6.2f} $/kW-yr)  cleared {cc['cleared_mw']:,.0f} "
            f"pos {cc['cleared_position']:.4f}  census(screen fleet) {cc['census_position']:.4f}  "
            f"Q_0 {cc['price_takers_mw']:,.0f}  offers {cc['n_offers']} / uncleared {cc['n_uncleared']}  "
            f"[{cc['how']}, marginal {cc['marginal_unit']}]"
        )
        print(
            f"   PUBLISHED (observable): {pub_day:6.2f} $/MW-day at pos {pub['pos_cleared']:.4f}  "
            f"-> ratio {ratio:.2f}x, Δpos {100 * (cc['cleared_position'] - pub['pos_cleared']):+.2f} pt; "
            f"uncleared firm by fuel: {fmt_by_fuel(cc['uncleared_mw_by_fuel'])}"
        )
        # §3.5 identity: failing rows <-> uncleared offers (marginal unit excepted).
        stack = cc.get("offer_stack") or []
        uncleared = {r[0] for r in stack if not r[4]}
        cleared = {r[0] for r in stack if r[4]}
        fail_ids = set(failing)
        fail_but_cleared = sorted(fail_ids & cleared)
        unc_but_passing = sorted(uncleared - fail_ids)
        ident_ok = (not fail_but_cleared) and (not unc_but_passing)
        bad_flag = [u for u, e in failing.items() if e.get("capacity_cleared") is not False]
        print(
            f"   IDENTITY: failing {len(fail_ids)} vs uncleared {len(uncleared)} -> "
            f"{'HOLDS' if ident_ok and not bad_flag else 'VIOLATED'}"
            + (f" (failing-but-cleared {fail_but_cleared[:5]})" if fail_but_cleared else "")
            + (f" (uncleared-but-passing {unc_but_passing[:5]})" if unc_but_passing else "")
            + (f" (rows with capacity_cleared != False: {bad_flag[:5]})" if bad_flag else "")
        )
        # The E&AS operand: offers above the published price by fuel, and the per-unit margin
        # that would put the stack's marginal offer at the published price at the published
        # cleared quantity.
        above = {}
        above_n = {}
        full_bar = {}
        for uid, fuel, offer, a_mw, is_cleared in stack:
            if offer > pub_day:
                above[fuel] = above.get(fuel, 0.0) + a_mw
                above_n[fuel] = above_n.get(fuel, 0) + 1
        # The stack's offer at the published cleared quantity (walk from Q_0).
        target = pub["pos_cleared"] * cc["requirement_mw"]
        cum = cc["price_takers_mw"]
        at_pub = 0.0
        for uid, fuel, offer, a_mw, is_cleared in stack:
            if cum + a_mw >= target:
                at_pub = offer
                break
            cum += a_mw
        # Per-fuel E&AS uplift that would lower a FULL-BAR offer to the published price:
        # ΔE_f = bar_f − P* × 365 × a_f / 1000 ($/kW-yr), a_f the class accreditation observed on
        # the stack (firm/nameplate not stored; use the fuel's median offer-implied A from rows
        # where offer == bar/(A×365), i.e. the zero-margin units).
        need = {}
        for fuel, bar in BAR.items():
            units = [
                (offer, a_mw)
                for uid, f, offer, a_mw, _c in stack
                if f == fuel and offer > 0
            ]
            if not units:
                continue
            # offer = (bar×1000×pmax − EAS)/(A×365); at zero E&AS offer = bar×1000/(a×365)
            # with a = A/pmax. The highest offer in the class is the zero-E&AS offer.
            o_max = max(o for o, _a in units)
            a_frac = bar * 1000.0 / (o_max * 365.0)
            need[fuel] = {
                "zero_eas_offer_mw_day": o_max,
                "implied_class_accreditation": a_frac,
                "eas_kw_yr_to_reach_published_price": max(
                    0.0, bar - pub_day * 365.0 * a_frac / 1000.0
                ),
                "firm_mw_above_published": above.get(fuel, 0.0),
                "n_above_published": above_n.get(fuel, 0),
            }
        print(
            f"   E&AS OPERAND: offers ABOVE the published price, firm MW by fuel: {fmt_by_fuel(above)} "
            f"| total {sum(above.values()):,.0f}; the stack's offer AT the published cleared position: "
            f"{at_pub:.2f} $/MW-day (published {pub_day:.2f})"
        )
        for fuel, v in sorted(need.items()):
            print(
                f"      {fuel:8s} zero-E&AS offer {v['zero_eas_offer_mw_day']:7.2f} $/MW-day "
                f"(class accreditation {v['implied_class_accreditation']:.3f}); an E&AS margin of "
                f">= {v['eas_kw_yr_to_reach_published_price']:5.1f} $/kW-yr per zero-margin unit would put "
                f"its offer AT the published price ({v['n_above_published']} units / "
                f"{v['firm_mw_above_published']:,.0f} firm MW above it today)"
            )
        yr.update(
            {
                "clearing": {k: v for k, v in cc.items() if k != "offer_stack"},
                "identity": {
                    "holds": bool(ident_ok and not bad_flag),
                    "n_failing": len(fail_ids),
                    "n_uncleared": len(uncleared),
                    "failing_but_cleared": fail_but_cleared,
                    "uncleared_but_passing": unc_but_passing,
                },
                "ratio_to_published": ratio,
                "delta_pos_pts": 100 * (cc["cleared_position"] - pub["pos_cleared"]),
                "offers_above_published_firm_by_fuel": above,
                "offer_at_published_pos": at_pub,
                "eas_operand": need,
            }
        )
        report[label]["years"][y] = yr
    s = score(bundle)
    if s:
        r = s["retirements"]
        a = s["additions"]["by_tech"]
        fc3 = {
            "retire_total_gw": r["total_gw"]["model"],
            "retire_band": r["total_gw"]["band"],
            "per_fuel_model_gw": {k: v["model_gw"] for k, v in r["per_fuel"].items()},
            "recall": f"{r['unit_recall_gt300']['matched']}/{r['unit_recall_gt300']['n_big_actual']}",
            "recall_band": r["unit_recall_gt300"]["band"],
            "false_retire_gw": r["false_retire"]["false_gw"],
            "false_retire_band": r["false_retire"]["band"],
            "add_by_tech_model_gw": {k: v["model_gw"] for k, v in a.items()},
            "blk10_backstop_mw": s.get("blk10_backstop", {}).get("fired_mw_total"),
            "loyo": {
                k: (v.get("recall"), v.get("false_retire_gw_raw"))
                for k, v in (s.get("loyo", {}).get("folds") or {}).items()
            },
        }
        report[label]["fc3"] = fc3
        print(
            f"   FC-3: retire.total {fc3['retire_total_gw']} GW ({fc3['retire_band']}; actual "
            f"{r['total_gw']['actual']}) per fuel {fc3['per_fuel_model_gw']} | recall {fc3['recall']} "
            f"({fc3['recall_band']}) | false_retire {fc3['false_retire_gw']} ({fc3['false_retire_band']}) "
            f"| add {fc3['add_by_tech_model_gw']} | backstop {fc3['blk10_backstop_mw']} MW | LOYO {fc3['loyo']}"
        )
    v = glob.glob(f"{bundle}/forecast_verdict.json")
    if v:
        fv = json.load(open(v[0]))
        report[label]["determination"] = fv.get("determination")
        print(f"   determination: {fv.get('determination')}")
if len(sys.argv) > 1:
    json.dump(report, open(sys.argv[1], "w"), indent=1)
