"""capx D74 SCREEN GATE (rule 29): structural STOP-only checks G1-G5, read from
the three screen-span bundles solved at HEAD (arm / control-P / control-B),
DY 2022/23. Also used on the full-window bundles with --years 2022 2023 2024
2025. Every number the FINDING cites from a screen or control bundle is
written here (rule 29(c): the bundles are deleted before merge).

Usage (repo root):
  PYTHONPATH=.:src .venv/bin/python docs/handoffs/d74/screen-gate-2026-09-06.py \
      --arm results/hindcast/d74-screen-arm --ctlp results/hindcast/d74-screen-ctlP \
      [--ctlb results/hindcast/d74-screen-ctlB] [--years 2022] [--out out.json]
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict

PUBLISHED = {2022: (50.00, 1.0510), 2023: (34.13, 1.0552), 2024: (28.92, 1.0555), 2025: (269.92, 1.0049)}
CLASS_FUELS = ("gas_st", "oil")


def bundle(out_dir: str) -> str:
    hits = glob.glob(f"{out_dir}/PJM/*/")
    assert len(hits) == 1, (out_dir, hits)
    return hits[0]


def ledger(b: str, year: int) -> dict:
    with open(f"{b}/evolution_{year}.json") as fh:
        return json.load(fh)


def stack(cc: dict) -> dict[str, tuple]:
    return {row[0]: tuple(row) for row in cc["offer_stack"]}


def pe_by(pe: list[dict], key: str) -> dict:
    out: dict = defaultdict(float)
    for r in pe:
        out[(r["event"], r[key])] += float(r["mw"])
    return {f"{e}:{f}": round(v, 1) for (e, f), v in sorted(out.items())}


def compare(arm_b: str, ctl_b: str, year: int, label: str) -> dict:
    A, C = ledger(arm_b, year), ledger(ctl_b, year)
    ca, cc = A["capacity_clearing"], C["capacity_clearing"]
    sa, sc = stack(ca), stack(cc)
    moved = {u: sc[u] for u in sc if sc[u][1] in CLASS_FUELS}
    class_in_arm = [u for u in sa if sa[u][1] in CLASS_FUELS]
    same_offers = [u for u in sa if u in sc and abs(sa[u][2] - sc[u][2]) <= 1e-9 and abs(sa[u][3] - sc[u][3]) <= 1e-6]
    diff_offers = [u for u in sa if u in sc and u not in same_offers]
    new_in_arm = [u for u in sa if u not in sc]
    moved_a = sum(v[3] for v in moved.values())
    unc_a = {u for u, v in sa.items() if not v[4]}
    pe_a = A.get("pipeline_events", [])
    rows_a = {r["unit_id"] for r in pe_a if r["event"] in ("decided", "entry_capped", "re_confirmed")}
    class_rows = [r for r in pe_a if r["fuel"] in CLASS_FUELS]
    ndc = A.get("no_default_cap_price_takers")
    pub_p, pub_pos = PUBLISHED.get(year, (float("nan"), float("nan")))
    res = {
        "label": label, "year": year,
        "price": {"arm": ca["price_usd_per_mw_day"], "ctl": cc["price_usd_per_mw_day"], "published": pub_p},
        "position": {"arm": ca["cleared_position"], "ctl": cc["cleared_position"], "published": pub_pos},
        "how": {"arm": ca["how"], "ctl": cc["how"]},
        "price_takers_mw": {"arm": ca["price_takers_mw"], "ctl": cc["price_takers_mw"], "ctl_plus_class": cc["price_takers_mw"] + moved_a, "class_moved_mw": moved_a},
        "requirement_mw": {"arm": ca["requirement_mw"], "ctl": cc["requirement_mw"]},
        "census_mw": {"arm": ca["census_mw"], "ctl": cc["census_mw"]},
        "uncleared_mw_by_fuel": {"arm": ca["uncleared_mw_by_fuel"], "ctl": cc["uncleared_mw_by_fuel"]},
        "n_offers": {"arm": ca["n_offers"], "ctl": cc["n_offers"]},
        "n_uncleared": {"arm": ca["n_uncleared"], "ctl": cc["n_uncleared"]},
        "G2_offers": {"identical": len(same_offers), "changed": len(diff_offers), "new_in_arm": len(new_in_arm), "class_units_in_arm_stack": len(class_in_arm), "changed_ids": diff_offers[:20]},
        "G3_identity": {"uncleared": len(unc_a), "pipeline_rows": len(rows_a), "uncleared_not_in_rows": sorted(unc_a - rows_a)[:20], "rows_not_uncleared": sorted(rows_a - unc_a)[:20]},
        "G4_class_rows": {"n": len(class_rows), "mw": round(sum(r["mw"] for r in class_rows), 1), "ledger_block": (None if ndc is None else {k: ndc[k] for k in ("units", "mw", "accredited_mw", "mw_by_fuel", "accredited_mw_by_fuel")})},
        "G5_nontarget": {
            "entry_decided_mw_by_tech": {"arm": A.get("entry_decided_mw_by_tech"), "ctl": C.get("entry_decided_mw_by_tech")},
            "renewable_additions": {"arm": A.get("renewable_additions"), "ctl": C.get("renewable_additions")},
            "floor_retained_n": {"arm": len(A.get("floor_retained", [])), "ctl": len(C.get("floor_retained", []))},
            "screen_peak_demand_mw": {"arm": A.get("screen_peak_demand_mw"), "ctl": C.get("screen_peak_demand_mw")},
            "screen_adequacy_requirement_mw": {"arm": A.get("screen_adequacy_requirement_mw"), "ctl": C.get("screen_adequacy_requirement_mw")},
            "fleet_by_fuel_after": {"arm": A.get("fleet_by_fuel_after"), "ctl": C.get("fleet_by_fuel_after")},
            "retirements_by_reason_fuel": {"arm": pe_by([{"event": r.get("reason", "?"), "fuel": r["fuel"], "mw": r["mw"]} for r in A.get("retirements", [])], "fuel"),
                                            "ctl": pe_by([{"event": r.get("reason", "?"), "fuel": r["fuel"], "mw": r["mw"]} for r in C.get("retirements", [])], "fuel")},
        },
        "pipeline_events_mw": {"arm": pe_by(pe_a, "fuel"), "ctl": pe_by(C.get("pipeline_events", []), "fuel")},
    }
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True); ap.add_argument("--ctlp", required=True); ap.add_argument("--ctlb")
    ap.add_argument("--years", type=int, nargs="+", default=[2022]); ap.add_argument("--out")
    a = ap.parse_args()
    arm_b, ctlp_b = bundle(a.arm), bundle(a.ctlp)
    out = {"arm": arm_b, "ctlP": ctlp_b, "ctlB": bundle(a.ctlb) if a.ctlb else None, "years": {}}
    for y in a.years:
        r = compare(arm_b, ctlp_b, y, "arm vs control-P")
        out["years"][y] = {"vs_ctlP": r}
        if a.ctlb:
            out["years"][y]["vs_ctlB"] = compare(arm_b, out["ctlB"], y, "arm vs control-B")
        p, q = r["price"], r["position"]
        print(f"\nDY {y}/{y+1-2000:02d} arm vs control-P: price {p['arm']:.4f} vs {p['ctl']:.4f} (pub {p['published']}); "
              f"pos {q['arm']:.4f} vs {q['ctl']:.4f} (pub {q['published']}); how {r['how']}")
        pt = r["price_takers_mw"]
        print(f"  Q0 arm {pt['arm']:.1f} vs ctl {pt['ctl']:.1f} (+class {pt['class_moved_mw']:.1f} = {pt['ctl_plus_class']:.1f}); R {r['requirement_mw']}; census {r['census_mw']}")
        print(f"  uncleared by fuel arm {r['uncleared_mw_by_fuel']['arm']} | ctl {r['uncleared_mw_by_fuel']['ctl']}")
        print(f"  G2 offers identical {r['G2_offers']['identical']} changed {r['G2_offers']['changed']} new {r['G2_offers']['new_in_arm']} class-in-arm-stack {r['G2_offers']['class_units_in_arm_stack']}")
        print(f"  G3 uncleared {r['G3_identity']['uncleared']} vs rows {r['G3_identity']['pipeline_rows']}; unc-not-rows {r['G3_identity']['uncleared_not_in_rows']}; rows-not-unc {r['G3_identity']['rows_not_uncleared']}")
        print(f"  G4 class pipeline rows {r['G4_class_rows']['n']} ({r['G4_class_rows']['mw']} MW); ledger block {r['G4_class_rows']['ledger_block']}")
        print(f"  G5 entry {r['G5_nontarget']['entry_decided_mw_by_tech']}; floor_retained {r['G5_nontarget']['floor_retained_n']}; peak {r['G5_nontarget']['screen_peak_demand_mw']}")
        print(f"  pipeline MW arm {r['pipeline_events_mw']['arm']}\n              ctl {r['pipeline_events_mw']['ctl']}")
        print(f"  retirements arm {r['G5_nontarget']['retirements_by_reason_fuel']['arm']} | ctl {r['G5_nontarget']['retirements_by_reason_fuel']['ctl']}")
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True, default=str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
