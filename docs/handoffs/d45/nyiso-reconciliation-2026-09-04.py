"""capx D45-R instrument (ZERO solves): NYISO stage 2 — the model's adequacy position and
evaluation quantity beside the published NYCA ICAP/IRM/UCAP record, and the published
locality (LCR) record the model does not represent at default.

    uv run python docs/handoffs/d45/nyiso-reconciliation-2026-09-04.py <L2 run_dir> <L3 run_dir>

Published side: the sibling instrument's JSON (published-positions-2026-09-03.json, NYISO
block: NYSRC Table D.2 peak / adopted IRM / derate / ICAP+UCAP requirement, Potomac SOM
summer UCAP margin) and the committed capacity-deliverability rows (LCR %, import limits).
Model side: the committed evolution ledgers (peak_demand_mw, adequacy_requirement_mw,
reserve_margin identity firm = peak x (1 + rm), capacity_reserve_position when the clearing
gate is on) and the HEAD requirement construction (PLANNING_RESERVE_MARGIN_BY_ISO x
PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO).
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.capacity_market import (  # noqa: E402
    PLANNING_RESERVE_MARGIN_BY_ISO, PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW, evaluate_demand_curve, resolve_demand_curve_vintage,
)

PUB = {int(r["capability_year"][:4]): r for r in json.loads(
    (Path(__file__).parent / "published-positions-2026-09-03.json").read_text())["nyiso"]}
HEAD_FACTOR = (1 + PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"]) * PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]


def curve_price(year: int, pos: float | None) -> float | None:
    if pos is None:
        return None
    v = resolve_demand_curve_vintage("NYISO", year)
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr if v.demand_curve else None


def ledger_rows(run_dir: Path) -> list[dict]:
    meta = json.loads((run_dir / "meta.json").read_text())
    bundle = REPO / meta["bundle"]
    rows, prev_firm = [], None
    for y in sorted(int(p.stem.split("_")[1]) for p in bundle.glob("evolution_*.json")):
        led = json.loads((bundle / f"evolution_{y}.json").read_text())
        peak, rm, req = led.get("peak_demand_mw"), led.get("reserve_margin"), led.get("adequacy_requirement_mw")
        firm_after = peak * (1 + rm) if (peak and rm is not None) else None
        pub = PUB.get(y)
        pos_enter = led.get("capacity_reserve_position")
        pos_enter_id = prev_firm / req if (prev_firm and req) else None
        r = dict(
            year=y, bridge=bool(led.get("bridge")), model_peak_mw=peak, model_req_mw=req,
            model_req_over_peak=(req / peak if (req and peak) else None), head_factor=HEAD_FACTOR,
            model_firm_after_mw=firm_after, model_pos_after=(firm_after / req if (firm_after and req) else None),
            model_pos_entering_ledger=pos_enter, model_pos_entering_identity=pos_enter_id,
            curve_at_model_entering=curve_price(y, pos_enter if pos_enter is not None else pos_enter_id),
        )
        if pub:
            preq, psup, ppos = pub["ucap_requirement_mw"], pub["ucap_supplied_mw"], pub["pos_published"]
            entering = pos_enter if pos_enter is not None else pos_enter_id
            r.update(
                pub_nysrc_peak_mw=pub["nysrc_peak_mw"], pub_irm_adopted_pct=pub["irm_adopted_pct"],
                pub_derate=pub["translation_factor"], pub_ucap_req_mw=preq, pub_ucap_supplied_mw=psup,
                pub_pos=ppos, pub_spot_kw_yr=pub["spot_kw_yr"], curve_at_pub_pos=curve_price(y, ppos),
                req_gap_mw=(req - preq) if req else None,
                supply_gap_entering_mw=(prev_firm - psup) if prev_firm else None,
                supply_gap_after_mw=(firm_after - psup) if firm_after else None,
                pos_gap_points=((entering - ppos) * 100) if entering else None,
                pos_model_firm_over_pub_req=(prev_firm / preq) if prev_firm else None,
                pos_pub_supply_over_model_req=(psup / req) if req else None,
            )
        exits = {}
        for e in led.get("retirements") or []:
            if isinstance(e, dict):
                k = f"{e.get('fuel')}:{e.get('reason') or e.get('channel') or '?'}"
                exits[k] = exits.get(k, 0.0) + float(e.get("mw") or 0)
        r["retirements_mw"] = exits
        rows.append(r)
        if firm_after:
            prev_firm = firm_after
    return rows


def lcr_rows() -> list[dict]:
    out = []
    with open(REPO / "data/raw/capacity-deliverability/nyiso/nyiso.csv") as fh:
        for r in csv.DictReader(fh):
            if r["metric"] in ("requirement", "import_limit", "system_requirement"):
                out.append({k: r[k] for k in ("delivery_year", "area", "metric", "value_mw", "value_pu", "source_doc")})
    return out


if __name__ == "__main__":
    res = {"head_requirement_factor_of_peak": HEAD_FACTOR,
           "head_external_tie_ucap_mw": ADEQUACY_EXTERNAL_TIE_FIRM_MW.get("NYISO"),
           "runs": {Path(a).name: ledger_rows(Path(a)) for a in sys.argv[1:]},
           "published_lcr": lcr_rows()}
    Path(__file__).with_suffix(".json").write_text(json.dumps(res, indent=1, default=float))
    for name, rows in res["runs"].items():
        print("==", name)
        for r in rows:
            print(" ", r["year"], "bridge" if r["bridge"] else "     ",
                  f"peak {r['model_peak_mw']:.0f} req {r['model_req_mw'] or 0:.0f} firm_after {r['model_firm_after_mw'] or 0:.0f}",
                  f"pos_enter {r['model_pos_entering_ledger'] or r['model_pos_entering_identity'] or 0:.3f} pos_after {r['model_pos_after'] or 0:.3f}",
                  f"pub_pos {r.get('pub_pos')} req_gap {r.get('req_gap_mw')} supply_gap_enter {r.get('supply_gap_entering_mw')}",
                  f"curve@model {r['curve_at_model_entering']} curve@pub {r.get('curve_at_pub_pos')} exits {r['retirements_mw']}")
