"""capx D52 pre-declaration instrument (ZERO solves, NO new code): the NYISO adequacy
requirement, entering CR-1 position, curve price and admission-cap exit budget per
scored year under the two D45 §5.2.4 requirement repairs, read off the COMMITTED
D45-R ledgers (``nyiso-2021-2025-realized-t1h-d45r`` = the bare ``nyiso-t1h``, and its
curve-ON probe ``…-curveon``) beside the published NYSRC Table D.2 record (the D45
instrument JSON) — evaluated with HEAD's EXISTING machinery only (``evaluate_demand_curve``,
``resolve_demand_curve_vintage``, ``thermal_accreditation_fraction``, the registry
composite), so the pre-declaration is fixed before the repair exists.

    uv run python docs/handoffs/d52/predecl-positions-2026-09-04.py

Arms per year: OFF (HEAD composite on the model's realized weather-year peak), PEAK
(the composite factor on the published ICAP-market forecast peak — item 1 alone),
FACTORS (the per-capability-year adopted IRM × (1 − derate) on the model's peak — item 2
alone), BOTH (= the published NYCA UCAP requirement, Table D.2). Positions are the
ledger identity ``firm_entering = peak_{y-1} × (1 + rm_{y-1})`` over each requirement.
The re-screen re-tests every ``decided`` / ``entry_capped`` row of the curve-ON ledger at
the BOTH-position curve price (the D45 §3(a) counterfactual, a bound — dynamics not
replayed). Rows + stdout are committed beside this file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.capacity_market import (  # noqa: E402
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.constants import EFORD  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    thermal_accreditation_fraction,
)

PUB = {
    int(r["capability_year"][:4]): r
    for r in json.loads(
        (Path(__file__).parent.parent / "d45" / "published-positions-2026-09-03.json").read_text()
    )["nyiso"]
}
HEAD_FACTOR = (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"]) * (
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]
)
L2 = REPO / "results/hindcast/nyiso-2021-2025-realized-t1h-d45r"
L3 = REPO / "results/hindcast/nyiso-2021-2025-realized-t1h-d45r-curveon"


def curve_price(year: int, pos: float | None) -> float | None:
    """HEAD's NYISO vintage curve ($/kW-yr) at ``pos`` for ``year``; None if no curve."""
    if pos is None:
        return None
    v = resolve_demand_curve_vintage("NYISO", year)
    if not v.demand_curve:
        return None
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr


def bundle_dir(run_dir: Path) -> Path:
    meta = json.loads((run_dir / "meta.json").read_text())
    return REPO / meta["bundle"]


def requirement_arms(year: int, model_peak: float) -> dict[str, float]:
    """The four requirement constructions for a scored year (MW)."""
    p = PUB[year]
    fac_cy = (1.0 + p["irm_adopted_pct"] / 100.0) * (1.0 - p["translation_factor"])
    return {
        "OFF": model_peak * HEAD_FACTOR,
        "PEAK": p["nysrc_peak_mw"] * HEAD_FACTOR,
        "FACTORS": model_peak * fac_cy,
        "BOTH": p["nysrc_peak_mw"] * fac_cy,  # == Table D.2 UCAP requirement
    }


def positions(run_dir: Path) -> list[dict]:
    b = bundle_dir(run_dir)
    rows, prev_firm = [], None
    for y in (2021, 2022, 2023, 2024, 2025):
        led = json.loads((b / f"evolution_{y}.json").read_text())
        peak, rm = led.get("peak_demand_mw"), led.get("reserve_margin")
        firm_after = peak * (1.0 + rm) if (peak and rm is not None) else None
        if led.get("bridge") or peak is None:
            rows.append(dict(year=y, bridge=True))
            continue
        arms = requirement_arms(y, peak)
        p = PUB[y]
        assert abs(arms["BOTH"] - p["ucap_requirement_mw"]) < 1.0, (y, arms["BOTH"])
        r = dict(
            year=y,
            model_peak_mw=peak,
            published_peak_mw=p["nysrc_peak_mw"],
            ledger_requirement_mw=led.get("adequacy_requirement_mw"),
            ledger_position=led.get("capacity_reserve_position"),
            requirement_mw=arms,
            firm_entering_mw=prev_firm,
            firm_after_mw=firm_after,
            published_position=p["pos_published"],
            published_ucap_supplied_mw=p["ucap_supplied_mw"],
            real_spot_kw_yr=p["spot_kw_yr"],
            curve_at_published_position=curve_price(y, p["pos_published"]),
        )
        if prev_firm:
            r["position_entering"] = {k: prev_firm / v for k, v in arms.items()}
            r["position_gap_pts"] = {
                k: (prev_firm / v - p["pos_published"]) * 100.0 for k, v in arms.items()
            }
            r["curve_at_entering"] = {k: curve_price(y, prev_firm / v) for k, v in arms.items()}
            r["exit_budget_mw"] = {k: prev_firm - v for k, v in arms.items()}
        rows.append(r)
        if firm_after:
            prev_firm = firm_after
    return rows


def rescreen(run_dir: Path, pos_by_year: dict[int, float]) -> list[dict]:
    """Re-test the curve-ON ledger's failed rows at the BOTH-position curve price."""
    b = bundle_dir(run_dir)
    out = []
    for y, pos_cf in pos_by_year.items():
        led = json.loads((b / f"evolution_{y}.json").read_text())
        px_cf = curve_price(y, pos_cf) or 0.0
        by = {}
        for r in led.get("pipeline_events") or []:
            if not isinstance(r, dict) or r.get("event") not in ("decided", "entry_capped"):
                continue
            mw = float(r.get("mw") or 0.0)
            frac = thermal_accreditation_fraction(r["fuel"], EFORD.get(r["fuel"], 0.0), "NYISO")
            cap_cf = mw * frac * px_cf * 1000.0
            nr = float(r.get("net_revenue_usd") or 0.0) - float(r.get("capacity_revenue_usd") or 0.0) + cap_cf
            k = f"{r['event']}:{r['fuel']}"
            d = by.setdefault(k, dict(n=0, mw=0.0, pass_mw=0.0, nr_kw=0.0, gfc_kw=0.0, frac=frac))
            d["n"] += 1
            d["mw"] += mw
            d["nr_kw"] += float(r.get("net_revenue_usd") or 0.0) / 1000.0
            d["gfc_kw"] += float(r.get("going_forward_cost_usd") or 0.0) / 1000.0
            if nr >= float(r.get("going_forward_cost_usd") or 0.0):
                d["pass_mw"] += mw
        for d in by.values():
            d["nr_kw_per_kw"] = d["nr_kw"] / d["mw"] if d["mw"] else None
            d["gfc_kw_per_kw"] = d["gfc_kw"] / d["mw"] if d["mw"] else None
            d["capacity_leg_kw_yr_at_cf"] = d["frac"] * px_cf
        out.append(dict(year=y, position_cf=pos_cf, curve_price_cf=px_cf, rows=by))
    return out


if __name__ == "__main__":
    l2 = positions(L2)
    l3 = positions(L3)
    both_pos = {r["year"]: r["position_entering"]["BOTH"] for r in l2 if r.get("position_entering")}
    res = dict(
        head_factor=HEAD_FACTOR,
        published=PUB,
        l2_bare_nyiso_t1h=l2,
        l3_curveon=l3,
        rescreen_l3_at_l2_both_position=rescreen(L3, both_pos),
        accreditation_fraction={f: thermal_accreditation_fraction(f, EFORD[f], "NYISO") for f in ("gas_st", "gas_ct", "gas_cc")},
    )
    Path(__file__).with_suffix(".json").write_text(json.dumps(res, indent=1, default=float))
    print("HEAD factor", round(HEAD_FACTOR, 4))
    for r in l2:
        if r.get("bridge"):
            print(r["year"], "bridge")
            continue
        print(r["year"], "peak model/pub", round(r["model_peak_mw"]), round(r["published_peak_mw"]),
              "req", {k: round(v) for k, v in r["requirement_mw"].items()},
              "pos_enter", {k: round(v, 4) for k, v in r.get("position_entering", {}).items()},
              "pub", r["published_position"],
              "curve", {k: (round(v, 2) if v is not None else None) for k, v in r.get("curve_at_entering", {}).items()},
              "budget", {k: round(v) for k, v in r.get("exit_budget_mw", {}).items()})
    for s in res["rescreen_l3_at_l2_both_position"]:
        print("rescreen", s["year"], "pos", round(s["position_cf"], 4), "px", round(s["curve_price_cf"], 2),
              {k: (d["n"], round(d["mw"]), round(d["pass_mw"]), round(d["nr_kw_per_kw"], 1), round(d["gfc_kw_per_kw"], 1), round(d["capacity_leg_kw_yr_at_cf"], 1)) for k, d in s["rows"].items()})
