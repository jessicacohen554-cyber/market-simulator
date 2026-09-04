"""capx D48 zero-solve instrument: the PJM adequacy position, curve price, floor
exit budget and screen re-test under the two D48 gates, read off the committed
D45 L1 ledgers (``results/hindcast/pjm-2021-2025-realized-t1h-d45``, key
``ea767a6254b8e4af`` — the last committed PJM live-posture T1-H at this
writing; D45-R's HEAD replay of the same recipe keys ``c6091bd5b62bbc3f`` and
had not landed on origin/main when this ran).

    uv run python docs/handoffs/d48/devintage-positions-2026-09-04.py [<run_dir>]

Zero solves. Every model quantity is a committed ledger field
(``fleet_by_fuel_before`` — the ENTERING fleet the year's screens priced —
``wind_cap_mw`` / ``solar_cap_mw`` / ``storage_firm_mw`` /
``firm_clean_accredited_mw`` / ``peak_demand_mw`` / ``pipeline_events``); every
mechanism quantity is HEAD's own committed machinery evaluated on those
fields — ``thermal_accreditation_fraction`` (config/year threaded, so the
devintage is the SAME resolver the solve will use), ``resolve_adequacy_
requirement_mw``, ``resolve_demand_response_supply_mw``, the R2 vintage
curves. The published side is the D45 instrument
(``../d45/published-positions-2026-09-03.json``). Four arms per year: OFF
(HEAD), V (accreditation-design devintage only), D (DR-as-supply only),
BOTH (the D48 A/B posture). The 2022 bridge year has no ledger peak; the
runner prices a bridge year against the prior-year peak, so 2022 uses the
2021 peak with the 2021 post-evolution fleet (labelled).

First-order reconstruction: thermal firm is ``Σ_fuel MW × fraction(fuel,
EFORD[fuel])`` at class EFORd (the ledger carries fleet MW by fuel, not
per-unit EFORd), so the OFF arm reproduces the ledger's own
``capacity_reserve_position`` to a stated residual rather than exactly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.capacity_market import (  # noqa: E402
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.constants import EFORD  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    gross_adequacy_requirement_mw,
    resolve_adequacy_requirement_mw,
    resolve_demand_response_supply_mw,
    thermal_accreditation_fraction,
)

PUB = json.loads(
    (Path(__file__).parent.parent / "d45" / "published-positions-2026-09-03.json").read_text()
)
DEFAULT_RUN = REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d45"

ARMS = {
    "OFF": dict(),
    "V": dict(pjm_accreditation_design_vintage=True),
    "D": dict(pjm_demand_response_supply=True),
    "BOTH": dict(pjm_accreditation_design_vintage=True, pjm_demand_response_supply=True),
}


def cfg(arm: str) -> ScenarioConfig:
    return ScenarioConfig(iso="PJM", mode="forecast", hindcast=True, **ARMS[arm])


def curve_price(year: int, pos: float | None) -> float | None:
    if pos is None:
        return None
    v = resolve_demand_curve_vintage("PJM", year)
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr


def published(year: int) -> dict | None:
    for r in PUB["pjm"]:
        if int(r["delivery_year"][:4]) == year:
            return r
    return None


def firm_and_position(c: ScenarioConfig, year: int, fleet: dict, led: dict, peak: float):
    thermal_by_fuel = {
        f: mw * thermal_accreditation_fraction(f, EFORD.get(f, 0.05), "PJM", c, year)
        for f, mw in fleet.items()
    }
    cred = led.get("renewable_credit_applied") or {}
    wind = float(led.get("wind_cap_mw") or 0.0) * float(cred.get("wind", 0.0))
    solar = float(led.get("solar_cap_mw") or 0.0) * float(cred.get("solar", 0.0))
    hydro = float(led.get("firm_clean_accredited_mw") or 0.0)
    storage = float(led.get("storage_firm_mw") or 0.0)
    tie = ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"]
    gross = gross_adequacy_requirement_mw(c, "PJM", peak, year)
    dr = resolve_demand_response_supply_mw(c, "PJM", year, gross) or 0.0
    firm = sum(thermal_by_fuel.values()) + wind + solar + hydro + storage + tie + dr
    req = resolve_adequacy_requirement_mw(c, "PJM", peak, year)
    return dict(
        thermal_firm_mw=sum(thermal_by_fuel.values()),
        thermal_firm_by_fuel=thermal_by_fuel,
        vre_hydro_storage_tie_mw=wind + solar + hydro + storage + tie,
        dr_supply_mw=dr,
        firm_mw=firm,
        requirement_mw=req,
        position=firm / req if req else None,
        exit_budget_mw=firm - req,
    )


def rescreen(led: dict, year: int, c: ScenarioConfig, pos: float) -> dict:
    """Re-test the year's FAILED candidates with the capacity leg at ``pos``.

    The D45 counterfactual pattern: capacity leg = mw × devintaged fraction ×
    curve(pos); pass iff net_revenue − old leg + new leg ≥ going-forward cost.
    A bound (year-to-year dynamics not replayed).
    """
    px = curve_price(year, pos) or 0.0
    rows = [
        r
        for r in (led.get("pipeline_events") or [])
        if isinstance(r, dict) and r.get("event") in ("decided", "entry_capped")
    ]
    failed = sum(float(r.get("mw") or 0.0) for r in rows)
    saved, by_fuel = 0.0, {}
    for r in rows:
        mw = float(r.get("mw") or 0.0)
        frac = thermal_accreditation_fraction(r.get("fuel", ""), EFORD.get(r.get("fuel", ""), 0.05), "PJM", c, year)
        nr = float(r.get("net_revenue_usd") or 0.0) - float(r.get("capacity_revenue_usd") or 0.0) + mw * frac * px * 1000.0
        if nr >= float(r.get("going_forward_cost_usd") or 0.0):
            saved += mw
            by_fuel[r["fuel"]] = by_fuel.get(r["fuel"], 0.0) + mw
    return dict(price_kw_yr=px, failed_mw=failed, would_pass_mw=saved, would_pass_by_fuel=by_fuel, n=len(rows))


def main(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text())
    bundle = REPO / meta["bundle"]
    leds = {int(p.stem.split("_")[1]): json.loads(p.read_text()) for p in bundle.glob("evolution_*.json")}
    out = dict(run=run_dir.name, cache_key=meta["cache_key"], years={})
    for year in sorted(leds):
        led = leds[year]
        if led.get("bridge"):
            # 2022: the 2021 post-evolution fleet against the prior-year peak.
            fleet = leds[year - 1].get("fleet_by_fuel_after") or {}
            base = leds[year - 1]
            peak = float(base["peak_demand_mw"])
            note = "bridge year: 2021 post-evolution fleet, 2021 peak (the runner's prior-year peak)"
        else:
            fleet = led.get("fleet_by_fuel_before") or {}
            base = led
            peak = float(led["peak_demand_mw"])
            note = "entering fleet (fleet_by_fuel_before) at the year's own peak"
        pub = published(year) or {}
        rec = dict(note=note, peak_mw=peak, ledger_position=led.get("capacity_reserve_position"),
                   ledger_requirement_mw=led.get("adequacy_requirement_mw"),
                   published=dict(pos_cleared=pub.get("pos_cleared"), pos_offered=pub.get("pos_offered"),
                                  pos_total_rm=pub.get("pos_total_rm"), real_price_kw_yr=pub.get("real_price_kw_yr"),
                                  zero_cross=pub.get("zero_cross")), arms={})
        for arm in ARMS:
            c = cfg(arm)
            fp = firm_and_position(c, year, fleet, base, peak)
            fp["curve_price_kw_yr"] = curve_price(year, fp["position"])
            fp["gap_to_cleared_pts"] = (
                100.0 * (fp["position"] - pub["pos_cleared"]) if pub.get("pos_cleared") and fp["position"] else None
            )
            if led.get("pipeline_events"):
                fp["rescreen_at_own_position"] = rescreen(led, year, c, fp["position"])
            rec["arms"][arm] = fp
        out["years"][year] = rec
    return out


if __name__ == "__main__":
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUN
    res = main(run_dir)
    Path(__file__).with_suffix(".json").write_text(json.dumps(res, indent=1, default=float))
    print(f"run {res['run']} key {res['cache_key']}")
    hdr = f"{'yr':>5} {'arm':>5} {'thermal':>9} {'other':>8} {'DR':>8} {'firm':>9} {'req':>9} {'pos':>7} {'$curve':>7} {'pubPos':>7} {'gap':>6} {'$real':>6} {'budget':>8} {'pass/failed MW':>18}"
    print(hdr)
    for y, rec in res["years"].items():
        for arm, fp in rec["arms"].items():
            rs = fp.get("rescreen_at_own_position") or {}
            pf = f"{rs.get('would_pass_mw', 0):,.0f}/{rs.get('failed_mw', 0):,.0f}" if rs else "-"
            print(
                f"{y:>5} {arm:>5} {fp['thermal_firm_mw']:>9,.0f} {fp['vre_hydro_storage_tie_mw']:>8,.0f} {fp['dr_supply_mw']:>8,.0f} "
                f"{fp['firm_mw']:>9,.0f} {fp['requirement_mw']:>9,.0f} {fp['position']:>7.4f} {fp['curve_price_kw_yr']:>7.2f} "
                f"{(rec['published']['pos_cleared'] or float('nan')):>7.4f} {(fp['gap_to_cleared_pts'] or float('nan')):>6.1f} "
                f"{(rec['published']['real_price_kw_yr'] or float('nan')):>6.1f} {fp['exit_budget_mw']:>8,.0f} {pf:>18}"
            )
        print(f"      ledger pos {rec['ledger_position']}  ledger req {rec['ledger_requirement_mw']}  ({rec['note']})")
