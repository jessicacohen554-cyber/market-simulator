"""capx D37 grading instrument: the armed NEISO T1-H re-measure vs its control.

Reads both arms' committed bundles and produces (a) the per-year position /
requirement / capacity-revenue table in the same shape as D40 §2, and (b) the
per-year exit and entry trajectory the P1-P6 predictions are graded on.

ZERO solves; every number is read from a bundle written by this session's two
runs, or computed by evaluating HEAD's own committed resolvers on them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from market_sim.config.capacity_market import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    NET_ICR_REQUIREMENT_MW_BY_ISO,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.constants import PLANNING_RESERVE_MARGIN_BY_ISO

REPO = Path(__file__).resolve().parents[3]
F_DR = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
PRM = PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]
COMPOSITE = (1.0 - F_DR) * (1.0 + PRM)
NET_ICR = NET_ICR_REQUIREMENT_MW_BY_ISO["NEISO"]
REAL = {2023: (33956.0, 32490.0, 24.01), 2024: (34621.0, 33270.0, 31.33),
        2025: (32810.0, 31645.0, 31.09)}
YEARS = (2021, 2022, 2023, 2024, 2025)


def bundle_dir(run: str) -> Path:
    root = REPO / "results/hindcast" / run / "NEISO"
    subs = [p for p in root.iterdir() if p.is_dir()]
    if len(subs) != 1:
        raise SystemExit(f"{run}: expected one cache-key dir, got {subs}")
    return subs[0]


def price(year: int, pos: float) -> float:
    v = resolve_demand_curve_vintage("NEISO", year)
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr


def read_arm(run: str, armed: bool) -> dict:
    bd = bundle_dir(run)
    out = {"run": run, "armed": armed, "cache_key": bd.name, "years": {}}
    for y in YEARS:
        p = bd / f"evolution_{y}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        exits: dict[str, float] = {}
        reasons: dict[str, int] = {}
        for r in d.get("retirements", []):
            exits[r.get("fuel")] = exits.get(r.get("fuel"), 0.0) + float(r.get("mw", 0.0))
            reasons[r.get("reason")] = reasons.get(r.get("reason"), 0) + 1
        peak = d.get("peak_demand_mw")
        rm = d.get("reserve_margin")
        firm = peak * (1.0 + rm) if (peak and rm is not None) else None
        req_on = (NET_ICR.get(f"{y}/{y + 1}") or 0.0) * (1.0 - F_DR) or None
        req_off = peak * COMPOSITE if peak else None
        req = req_on if armed else req_off
        pos_raw = F_DR + (1.0 - F_DR) * (firm / req) if (firm and req) else None
        ev = d.get("pipeline_events", [])
        kinds: dict[str, int] = {}
        for e in ev:
            k = e.get("event", e.get("kind", "?"))
            kinds[k] = kinds.get(k, 0) + 1
        out["years"][y] = dict(
            bridge=d.get("bridge"), peak=peak, reserve_margin=rm, firm=firm,
            req_off=req_off, req_on=req_on, req_used=req, pos_raw=pos_raw,
            price=price(y, pos_raw) if pos_raw else None,
            budget=(firm - req) if (firm and req) else None,
            exits_mw=round(sum(exits.values()), 1), exits_by_fuel={k: round(v, 1) for k, v in exits.items()},
            exit_reasons=reasons, n_exits=len(d.get("retirements", [])),
            floor_retained=len(d.get("floor_retained", [])),
            floor_retained_mw=round(sum(float(r.get("ucap_mw", r.get("mw", 0.0)) or 0.0)
                                        for r in d.get("floor_retained", [])), 1),
            entry=d.get("entry_decided_mw_by_tech"),
            ccs_retrofits=len(d.get("ccs_retrofits", [])),
            thermal_before=round(sum(d.get("fleet_by_fuel_before", {}).values()), 1),
            thermal_after=round(sum(d.get("fleet_by_fuel_after", {}).values()), 1),
            screen_diag_rows=len(d.get("entry_screen_diagnostics", []) or []),
            pipeline_event_kinds=kinds,
        )
    sp = bd / "score.json"
    out["score"] = json.loads(sp.read_text()) if sp.exists() else None
    return out


def bands(score: dict) -> dict:
    if not score:
        return {}
    r = score.get("retirements", {})
    a = score.get("additions", {})
    got = {
        "retire.total_gw": r.get("total_gw"),
        "retire.unit_recall_gt300": r.get("unit_recall_gt300"),
        "retire.false_retire": r.get("false_retire"),
    }
    for t, v in (a.get("by_tech") or {}).items():
        got[f"add.by_tech.{t}"] = v
    for t, v in (a.get("shares") or {}).items():
        got[f"add.shares.{t}"] = v
    return got


def main(armed_run: str, control_run: str) -> None:
    arm = read_arm(armed_run, armed=True)
    ctl = read_arm(control_run, armed=False)
    print(f"ARM     {arm['run']}  cache_key={arm['cache_key']}")
    print(f"CONTROL {ctl['run']}  cache_key={ctl['cache_key']}")
    print()
    print("=== per-year trajectory ===")
    hdr = (f"{'yr':>5} {'arm':>4} {'peak':>9} {'rm':>9} {'firm':>9} {'reqUsed':>9} "
           f"{'posRaw':>8} {'$/kW-yr':>8} {'budget':>9} {'exitsMW':>9} {'floorRet':>9} {'diagRows':>9}")
    print(hdr)
    for label, a in (("CTL", ctl), ("ARM", arm)):
        for y in YEARS:
            r = a["years"].get(y)
            if not r:
                continue
            f = lambda v, w=9, p=1: (f"{v:>{w},.{p}f}" if v is not None else " " * w)
            rm = r["reserve_margin"]
            rm_s = f"{rm:>9.6f}" if rm is not None else " " * 9
            print(f"{y:>5} {label:>4} {f(r['peak'])} {rm_s} "
                  f"{f(r['firm'])} {f(r['req_used'])} {f(r['pos_raw'],8,4)} {f(r['price'],8,2)} "
                  f"{f(r['budget'])} {f(r['exits_mw'])} {r['floor_retained']:>9} {r['screen_diag_rows']:>9}")
        print()
    print("=== exits by fuel ===")
    for label, a in (("CTL", ctl), ("ARM", arm)):
        tot = 0.0
        for y in YEARS:
            r = a["years"].get(y)
            if r and r["exits_mw"]:
                tot += r["exits_mw"]
                print(f"{label} {y}: {r['exits_mw']:>9,.1f} MW  {r['exits_by_fuel']}  reasons={r['exit_reasons']}")
        print(f"{label} cumulative: {tot:,.1f} MW = {tot / 1000:.3f} GW\n")
    print("=== bands ===")
    ba, bc = bands(arm["score"]), bands(ctl["score"])
    for k in sorted(set(ba) | set(bc)):
        va, vc = ba.get(k, {}), bc.get(k, {})
        print(f"{k:<28} CTL {str(vc.get('band')):<6} {str(vc.get('model', vc.get('model_gw', vc.get('frac_of_model', vc.get('recall'))))):<10}"
              f"  ARM {str(va.get('band')):<6} {str(va.get('model', va.get('model_gw', va.get('frac_of_model', va.get('recall'))))):<10}"
              f"  actual {va.get('actual', va.get('actual_gw', va.get('actual_share')))}")
    Path(__file__).with_suffix(".json").write_text(json.dumps({"arm": arm, "control": ctl}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
