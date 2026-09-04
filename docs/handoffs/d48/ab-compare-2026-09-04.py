"""capx D48 Phase-1 instrument: the A/B comparison of the devintage arm against
its control, read entirely off the two committed bundles (zero solves).

    uv run python docs/handoffs/d48/ab-compare-2026-09-04.py <control_run_dir> <arm_run_dir>

Reads, per bundle: ``meta.json`` (key, wall), ``run_config.json`` (the two
gate fields), the per-year ``evolution_<year>.json`` ledgers (the D45
observability rows ``capacity_reserve_position`` / ``adequacy_requirement_mw``
/ ``reserve_margin`` / ``peak_demand_mw``, the retirements by reason and fuel,
the additions, the ``pipeline_events`` screen rows with their
``capacity_revenue_usd`` leg, and the ``entry_screen_diagnostics`` rows'
``capacity_revenue_per_mw_yr``), and ``score.json`` (the FC-3 band rows, the
per-fuel table, the LOYO folds). Emits the PREDECL §2/§4 grading quantities:

* the position / requirement / curve-price table per screen year, both arms,
  with the published cleared / offered positions beside them (validation
  observables, rule 13 — never targets);
* the FC-3 rows (``retire.total_gw``, by fuel, ``unit_recall_gt300``,
  ``false_retire``, ``add.by_tech``) side by side with their delta;
* the capacity-revenue leg every screen candidate saw ($/kW-yr, by year);
* the P9 sign test: |position − published cleared| per year, arm vs control,
  which is the LOYO construction for a mechanism with zero free parameters.

Writes ``<this file>.json`` beside itself.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PUB = json.loads(
    (Path(__file__).parent.parent / "d45" / "published-positions-2026-09-03.json").read_text()
)
FIELDS = ("pjm_accreditation_design_vintage", "pjm_demand_response_supply")


def published(year: int) -> dict:
    for r in PUB["pjm"]:
        if int(r["delivery_year"][:4]) == year:
            return r
    return {}


def load_bundle(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text())
    bundle = REPO / meta["bundle"]
    if not bundle.exists():
        bundle = run_dir / meta["iso"] / meta["cache_key"]
    rc = json.loads((run_dir / "run_config.json").read_text())
    cfg = rc.get("scenario_config", rc.get("config", rc))
    leds = {int(p.stem.split("_")[1]): json.loads(p.read_text()) for p in bundle.glob("evolution_*.json")}
    score = json.loads((bundle / "score.json").read_text()) if (bundle / "score.json").exists() else {}
    return dict(run=run_dir.name, meta=meta, gates={f: cfg.get(f) for f in FIELDS}, ledgers=leds, score=score)


def year_rows(b: dict) -> dict:
    out = {}
    for y, led in sorted(b["ledgers"].items()):
        ret = led.get("retirements") or []
        by_reason = defaultdict(float)
        by_fuel = defaultdict(float)
        for r in ret:
            by_reason[r.get("reason")] += float(r.get("mw") or 0.0)
            by_fuel[r.get("fuel")] += float(r.get("mw") or 0.0)
        pe = [r for r in (led.get("pipeline_events") or []) if isinstance(r, dict)]
        ev = Counter(r.get("event") for r in pe)
        cap_leg = sorted(
            {round(float(r.get("capacity_revenue_usd") or 0.0) / max(float(r.get("mw") or 0.0), 1e-9) / 1000.0, 2) for r in pe}
        )
        decided = defaultdict(float)
        capped = defaultdict(float)
        for r in pe:
            if r.get("event") == "decided":
                decided[r.get("fuel")] += float(r.get("mw") or 0.0)
            elif r.get("event") == "entry_capped":
                capped[r.get("fuel")] += float(r.get("mw") or 0.0)
        esd = {r.get("tech"): round(float(r.get("capacity_revenue_per_mw_yr") or 0.0) / 1000.0, 2)
               for r in (led.get("entry_screen_diagnostics") or []) if isinstance(r, dict)}
        peak = led.get("peak_demand_mw")
        rm = led.get("reserve_margin")
        pub = published(y)
        pos = led.get("capacity_reserve_position")
        out[y] = dict(
            bridge=bool(led.get("bridge")),
            peak_mw=peak,
            position=pos,
            requirement_mw=led.get("adequacy_requirement_mw"),
            reserve_margin_after=rm,
            firm_after_mw=(round(float(peak) * (1.0 + float(rm)), 1) if peak and rm is not None else None),
            gap_to_cleared_pts=(round(100.0 * (float(pos) - pub["pos_cleared"]), 2) if pos is not None and pub.get("pos_cleared") == pub.get("pos_cleared") and pub.get("pos_cleared") else None),
            pub_cleared=pub.get("pos_cleared"),
            pub_offered=pub.get("pos_offered"),
            pub_zero_cross=pub.get("zero_cross"),
            retire_mw_by_reason=dict(by_reason),
            retire_mw_by_fuel=dict(by_fuel),
            screen_events=dict(ev),
            screen_capacity_leg_kw_yr=cap_leg,
            decided_mw_by_fuel=dict(decided),
            capped_mw_by_fuel=dict(capped),
            entry_capacity_rev_kw_yr=esd,
            entry_decided=led.get("entry_decided_mw_by_tech"),
            thermal_additions=[(a.get("fuel"), a.get("mw"), a.get("source")) for a in (led.get("thermal_additions") or [])],
            storage_additions_mw=sum(float(a.get("mw") or 0.0) for a in (led.get("storage_additions") or [])),
            fleet_before=led.get("fleet_by_fuel_before"),
            fleet_after=led.get("fleet_by_fuel_after"),
            renewable_credit=led.get("renewable_credit_applied"),
            storage_firm_mw=led.get("storage_firm_mw"),
            firm_clean_accredited_mw=led.get("firm_clean_accredited_mw"),
        )
    return out


def fc3_rows(score: dict) -> dict:
    r = score.get("retirements") or {}
    a = score.get("additions") or {}
    out = {
        "retire.total_gw": (r.get("total_gw") or {}).get("model"),
        "retire.total_band": (r.get("total_gw") or {}).get("band"),
        "retire.err_frac": (r.get("total_gw") or {}).get("err_frac"),
        "retire.unit_recall_gt300": (r.get("unit_recall_gt300") or {}).get("recall"),
        "retire.recall_matched": (r.get("unit_recall_gt300") or {}).get("matched"),
        "retire.recall_band": (r.get("unit_recall_gt300") or {}).get("band"),
        "retire.false_retire_gw": (r.get("false_retire") or {}).get("false_gw"),
        "retire.false_retire_band": (r.get("false_retire") or {}).get("band"),
    }
    for f, v in (r.get("per_fuel") or {}).items():
        out[f"retire.by_fuel.{f}"] = v.get("model_gw")
    for t, v in (a.get("by_tech") or {}).items():
        out[f"add.by_tech.{t}"] = v.get("model_gw")
        out[f"add.by_tech.{t}.band"] = v.get("band")
    out["add.model_total_gw"] = a.get("model_total_gw")
    loyo = (score.get("loyo") or {}).get("folds") or {}
    for y, f in loyo.items():
        out[f"loyo.{y}.recall"] = f.get("recall")
        out[f"loyo.{y}.matched"] = f.get("matched")
        out[f"loyo.{y}.false_gw"] = f.get("false_retire_gw_raw")
    return out


def main(control: Path, arm: Path) -> dict:
    c, a = load_bundle(control), load_bundle(arm)
    cy, ay = year_rows(c), year_rows(a)
    cf, af = fc3_rows(c["score"]), fc3_rows(a["score"])
    fc_delta = {}
    for k in sorted(set(cf) | set(af)):
        if cf.get(k) != af.get(k):
            fc_delta[k] = dict(control=cf.get(k), arm=af.get(k))
    # P9 sign test: |pos - published cleared| per screen year, arm vs control.
    sign = {}
    for y in sorted(set(cy) & set(ay)):
        gc, ga = cy[y].get("gap_to_cleared_pts"), ay[y].get("gap_to_cleared_pts")
        if gc is None or ga is None:
            continue
        sign[y] = dict(control_abs_gap=abs(gc), arm_abs_gap=abs(ga), arm_minus_control=round(abs(ga) - abs(gc), 3),
                       verdict=("improves" if abs(ga) < abs(gc) - 1e-9 else "degrades" if abs(ga) > abs(gc) + 1e-9 else "unchanged"))
    return dict(control=dict(run=c["run"], key=c["meta"]["cache_key"], gates=c["gates"]),
                arm=dict(run=a["run"], key=a["meta"]["cache_key"], gates=a["gates"]),
                years={y: dict(control=cy.get(y), arm=ay.get(y)) for y in sorted(set(cy) | set(ay))},
                fc3=dict(control=cf, arm=af, moved=fc_delta), p9_sign_test=sign)


def fmt(v, nd=1):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:,.{nd}f}"
    return str(v)


if __name__ == "__main__":
    control = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d45r"
    arm = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d48-devintage"
    res = main(control, arm)
    Path(__file__).with_suffix(".json").write_text(json.dumps(res, indent=1, default=float))
    print(f"control {res['control']['run']} {res['control']['key']} gates {res['control']['gates']}")
    print(f"arm     {res['arm']['run']} {res['arm']['key']} gates {res['arm']['gates']}")
    print(f"\n{'yr':>5} {'arm':>8} {'peak':>9} {'position':>9} {'req':>10} {'rm_after':>9} {'firm_after':>11} {'gap→clr':>8} {'pub clr':>8} {'zero':>7} {'screen $/kW-yr':>15} {'retire by reason':>40}")
    for y, rows in res["years"].items():
        for label, r in (("control", rows["control"]), ("arm", rows["arm"])):
            if r is None:
                continue
            print(f"{y:>5} {label:>8} {fmt(r['peak_mw'],0):>9} {fmt(r['position'],4):>9} {fmt(r['requirement_mw'],0):>10} {fmt(r['reserve_margin_after'],4):>9} {fmt(r['firm_after_mw'],0):>11} {fmt(r['gap_to_cleared_pts'],2):>8} {fmt(r['pub_cleared'],4):>8} {fmt(r['pub_zero_cross'],4):>7} {str(r['screen_capacity_leg_kw_yr']):>15} {str({k: round(v) for k, v in r['retire_mw_by_reason'].items()}):>40}")
    print("\nFC-3 rows that MOVED (arm vs control):")
    if not res["fc3"]["moved"]:
        print("  none — byte-identical on every scored row")
    for k, v in res["fc3"]["moved"].items():
        print(f"  {k}: {v['control']} -> {v['arm']}")
    print("\nP9 sign test (|position - published cleared|, pts):")
    for y, s in res["p9_sign_test"].items():
        print(f"  {y}: control {s['control_abs_gap']:.2f}  arm {s['arm_abs_gap']:.2f}  Δ {s['arm_minus_control']:+.2f}  {s['verdict']}")
    print("\nentry-screen capacity revenue ($/kW-yr) by tech:")
    for y, rows in res["years"].items():
        for label, r in (("control", rows["control"]), ("arm", rows["arm"])):
            if r:
                print(f"  {y} {label:>8} {r['entry_capacity_rev_kw_yr']}  thermal_adds {r['thermal_additions']}  decided_vre {r['entry_decided']}")
