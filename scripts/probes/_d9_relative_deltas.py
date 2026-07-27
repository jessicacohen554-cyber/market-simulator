#!/usr/bin/env python
"""D-9 multi-ISO: max relative warm-vs-cold delta per trajectory quantity.

``_d9_forecast_warmstart_ab.py --compare`` answers the guardrail question
(identical or not) but only lists the keys that moved. The D-9 record also
quotes the *size* of the residual on the keys that are allowed to move (prices,
CO2), which is what separates "dual noise three orders inside the golden bands"
from "the trajectory shifted". This produces that table for one ISO pair.

Usage::

    python scripts/probes/_d9_relative_deltas.py \\
        --cold results/d9-ab/full-miso-cold/full_horizon_summary.json \\
        --warm results/d9-ab/full-miso-warm/full_horizon_summary.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SCALARS = (
    "total_cap_mw",
    "thermal_mw",
    "firm_clean_mw",
    "vre_mw",
    "storage_mw",
    "builds_thermal_mw",
    "builds_renew_mw",
    "builds_storage_mw",
    "retire_mw",
    "peak_demand_mw",
    "reserve_margin",
    "max_hourly_price",
    "lw_price",
    "co2_mt",
)


def _rel(cold: float, warm: float) -> float:
    """Relative delta, falling back to the absolute one at a zero base."""
    if cold == warm:
        return 0.0
    denom = abs(cold)
    return abs(warm - cold) / denom if denom > 0 else abs(warm - cold)


def table(cold: dict, warm: dict) -> dict:
    """Max relative delta per quantity, with the year it occurs in."""
    c = {int(r["year"]): r for r in cold.get("trajectory", [])}
    w = {int(r["year"]): r for r in warm.get("trajectory", [])}
    years = sorted(set(c) & set(w))
    out: dict[str, dict] = {}
    for key in SCALARS:
        best = (0.0, None)
        for year in years:
            cv, wv = c[year].get(key), w[year].get(key)
            if not isinstance(cv, (int, float)) or not isinstance(wv, (int, float)):
                continue
            r = _rel(float(cv), float(wv))
            if r > best[0]:
                best = (r, year)
        out[key] = {"max_rel_delta": best[0], "year": best[1]}
    fuel_best = (0.0, None, None)
    for year in years:
        cf = c[year].get("capacity_by_fuel_mw") or {}
        wf = w[year].get("capacity_by_fuel_mw") or {}
        for fuel in sorted(set(cf) | set(wf)):
            r = _rel(float(cf.get(fuel, 0.0)), float(wf.get(fuel, 0.0)))
            if r > fuel_best[0]:
                fuel_best = (r, year, fuel)
    out["capacity_by_fuel_mw"] = {
        "max_rel_delta": fuel_best[0],
        "year": fuel_best[1],
        "fuel": fuel_best[2],
    }
    return {"years": years, "quantities": out}


def concurrent_window(cold: dict, warm: dict) -> dict:
    """Restrict the wall-clock comparison to the genuinely side-by-side years.

    Two arms launched together do not finish together: the warm arm ends first
    and every cold year after that point runs on a free box, which biases the
    cold total DOWNWARD and makes the headline speedup conservative. §H3 reports
    both numbers; this computes the restricted one — the leading years whose
    cumulative COLD wall still falls inside the warm arm's total run time, i.e.
    the years during which both arms were actually competing for the box.

    Returns an empty ``years`` list when the arms were run sequentially (no
    contention to correct for) — the caller then quotes the totals directly.
    """
    cp = cold.get("per_year_perf") or []
    wp = warm.get("per_year_perf") or []
    warm_total = float(warm.get("total_wall_s") or 0.0)
    if not cp or not wp or warm_total <= 0:
        return {"years": [], "cold_s": 0.0, "warm_s": 0.0, "speedup": None}
    cum, years = 0.0, []
    for row in cp:
        cum += float(row.get("wall_s") or 0.0)
        if cum > warm_total:
            break
        years.append(int(row["year"]))
    wall_by_year = {int(r["year"]): float(r.get("wall_s") or 0.0) for r in wp}
    cold_s = sum(float(r.get("wall_s") or 0.0) for r in cp if int(r["year"]) in years)
    warm_s = sum(wall_by_year.get(y, 0.0) for y in years)
    return {
        "years": years,
        "cold_s": round(cold_s, 1),
        "warm_s": round(warm_s, 1),
        "speedup": round(cold_s / warm_s, 3) if warm_s else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cold", type=Path, required=True)
    ap.add_argument("--warm", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    cold = json.loads(args.cold.read_text())
    warm = json.loads(args.warm.read_text())
    result = table(cold, warm)
    result["wall"] = {
        "cold_total_s": cold.get("total_wall_s"),
        "warm_total_s": warm.get("total_wall_s"),
        "speedup": (
            round(cold["total_wall_s"] / warm["total_wall_s"], 3)
            if cold.get("total_wall_s") and warm.get("total_wall_s")
            else None
        ),
        "cold_peak_rss_mb": cold.get("global_peak_rss_mb"),
        "warm_peak_rss_mb": warm.get("global_peak_rss_mb"),
        "concurrent_window": concurrent_window(cold, warm),
    }
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
