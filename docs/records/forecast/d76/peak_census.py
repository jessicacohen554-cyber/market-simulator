#!/usr/bin/env python3
"""capx D76 phase 0 — the six-ISO capacity-screen SEAM PEAK census. Zero LP.

**The defect being measured.** ``runner.py`` builds the capacity screens' peak
at the TOP of its year loop (lines 2029-2031) as
``_scale_demand(base_demand, wx_config, year)`` + ``add_load_layers`` — the
GROWTH path — and only the LP's own ``year_demand``, 500 lines further down
(line 2540), takes the measured hindcast branch. With ``weather_year=2024``,
``crossover_solve_year_weather=False`` and ``demand_growth_vintage=None`` — the
resolution of EVERY committed T1-H recipe — ``_scale_demand`` compounds and
DE-GROWS the weather year's measured load across 2024↔Y, so in every year that
is not the weather year the capacity screens test a SYNTHESIZED peak while the
LP in the same year dispatches the MEASURED one.

This script measures that gap for all six ISOs, in both hindcast recipe shapes
(bare T1-H, ``weather_year=2024``; T1-X crossover, ``weather_year=2025``), at
HEAD. It reuses ``docs/handoffs/d67/gdrift_peak_probe.py``'s seam helpers
rather than re-deriving them, so the seam reproduced here is the same object
D67 measured to 0.000 MW on the 2024 row (charter: "extend, do not fork").

Zero LP, zero solve, read-only: it loads demand arrays and calls the shipped
requirement resolver. Nothing is armed and no config is changed.

Output: ``docs/handoffs/d76/peak_census.json`` + a printed table.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.model.capacity_evolution.retirements import (
    resolve_adequacy_requirement_mw,
)
from market_sim.runner import _get_growth_rate
from scripts.run_capacity_hindcast import build_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "d67"))
from gdrift_peak_probe import measured_peak_mw, seam_context, seam_peak_mw

ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM")

# The two committed hindcast recipe shapes. ``t1h`` is the bare plain hindcast
# every ISO's frontier T1-H bundle runs (``build_config`` leaves
# ``weather_year`` at the ScenarioConfig default 2024); ``t1x`` is the
# crossover, whose weather year is pinned to CROSSOVER_FORWARD_YEAR - 1 = 2025.
# ``first_screen_year`` is the first year the screen seam actually BINDS: the
# requirement/position block at runner.py:2125 is guarded on
# ``prior_results is not None``, so the window's first year writes a
# ``screen_peak_demand_mw`` no screen consumed (verified in every committed
# ledger: 2021's ``screen_adequacy_requirement_mw`` is null).
RECIPES = {
    "t1h": {"start": 2021, "end": 2025, "vintage": 2020, "crossover": False,
            "first_screen_year": 2022},
    "t1x": {"start": 2023, "end": 2027, "vintage": 2023, "crossover": True,
            "first_screen_year": 2024},
}


def build(iso: str, recipe: str):
    """Return the ISO-defaulted config for one recipe shape.

    Args:
        iso: ISO code.
        recipe: ``"t1h"`` or ``"t1x"``.

    Returns:
        The :class:`ScenarioConfig` the harness would hand ``run_scenario``.
    """
    r = RECIPES[recipe]
    return apply_iso_scenario_defaults(
        build_config(
            iso, r["start"], r["end"], "realized",
            vintage=r["vintage"], crossover=r["crossover"],
        ),
        iso,
    )


def census_one(iso: str, recipe: str) -> dict:
    """Measure the seam-vs-measured peak gap for one ISO × recipe, at HEAD.

    Args:
        iso: ISO code.
        recipe: ``"t1h"`` or ``"t1x"``.

    Returns:
        A dict with the config resolution and one row per year.
    """
    r = RECIPES[recipe]
    cfg = build(iso, recipe)
    ctx = seam_context(iso, cfg, r["start"])
    rows = {}
    for year in range(r["start"], r["end"] + 1):
        seam = seam_peak_mw(ctx, year)
        # The LP's measured branch fires only for a hindcast year that is not a
        # crossover FORWARD year; past the boundary both paths are the growth
        # path and there is no gap to measure (nor any measured load to read).
        forward = bool(cfg.is_crossover_forward_year(year))
        row = {
            "seam_peak_mw": round(seam, 3),
            "screen_binds": year >= r["first_screen_year"],
            "lp_branch": "forecast (growth)" if forward else "measured",
        }
        if forward:
            row["measured_peak_mw"] = None
            row["delta_mw"] = None
            row["delta_pct"] = None
        else:
            meas = measured_peak_mw(ctx, year)
            row["measured_peak_mw"] = round(meas, 3)
            row["delta_mw"] = round(seam - meas, 3)
            row["delta_pct"] = round(100.0 * (seam - meas) / meas, 4) if meas else None
            # The operand the screens actually consumed vs the one the measured
            # load implies, through the SHIPPED resolver at HEAD (published /
            # held-last FPR ladder, then the composite) — so an ISO/year whose
            # requirement is peak-INDEPENDENT shows a 0.0 requirement delta even
            # where the peak delta is large.
            req_seam = resolve_adequacy_requirement_mw(cfg, iso, seam, year)
            req_meas = resolve_adequacy_requirement_mw(cfg, iso, meas, year)
            row["req_on_seam_peak_mw"] = round(req_seam, 3)
            row["req_on_measured_peak_mw"] = round(req_meas, 3)
            row["req_delta_mw"] = round(req_seam - req_meas, 3)
            row["req_peak_independent"] = abs(req_seam - req_meas) < 1e-6
        rows[year] = row
    # The screen year for phase 1: the BINDING year whose measured footprint is
    # largest in MW (rule 29 [R-SCREEN] clause (1) — named before any solve and
    # chosen on the mechanism's own footprint, never on a residual).
    binding = [y for y, v in rows.items() if v["screen_binds"] and v["delta_mw"] is not None]
    screen_year = max(binding, key=lambda y: abs(rows[y]["delta_mw"])) if binding else None
    return {
        "iso": iso,
        "recipe": recipe,
        "weather_year": cfg.weather_year,
        "demand_growth_vintage": cfg.demand_growth_vintage,
        "crossover_solve_year_weather": bool(cfg.crossover_solve_year_weather),
        "hindcast": bool(cfg.hindcast),
        "growth_rate_near": round(_get_growth_rate(cfg, r["start"]), 8),
        "first_screen_year": r["first_screen_year"],
        "screen_year": screen_year,
        "screen_year_delta_mw": rows[screen_year]["delta_mw"] if screen_year else None,
        "years": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="*", default=list(ISOS))
    ap.add_argument("--recipe", nargs="*", default=list(RECIPES))
    ap.add_argument("--out", default="docs/handoffs/d76/peak_census.json")
    args = ap.parse_args()

    out, errors = [], {}
    for recipe in args.recipe:
        for iso in args.iso:
            try:
                out.append(census_one(iso, recipe))
            except Exception as exc:  # census must report, never abort mid-sweep
                errors[f"{iso}/{recipe}"] = f"{type(exc).__name__}: {exc}"
                print(f"!! {iso}/{recipe}: {type(exc).__name__}: {exc}", file=sys.stderr)

    hdr = (f"{'iso':<6} {'recipe':<5} {'yr':>5} {'seam peak':>13} {'measured':>13} "
           f"{'delta MW':>11} {'delta %':>8} {'req delta MW':>13} {'binds':>6}")
    print(hdr)
    print("-" * len(hdr))
    for blk in out:
        for year, row in blk["years"].items():
            d = row["delta_mw"]
            lead = (f"{blk['iso']:<6} {blk['recipe']:<5} {year:>5} "
                    f"{row['seam_peak_mw']:>13,.1f} ")
            binds = "Y" if row["screen_binds"] else "·"
            if d is None:
                print(lead + f"{'—':>13} {'—':>11} {'—':>8} {'—':>13} {binds:>6}"
                             "   (forward year: no measured load, no gap)")
            else:
                print(lead + f"{row['measured_peak_mw']:>13,.1f} {d:>11,.1f} "
                             f"{row['delta_pct']:>8.2f} {row['req_delta_mw']:>13,.1f} "
                             f"{binds:>6}")
        print()
    print("screen year (largest |delta| among binding years):")
    for blk in out:
        print(f"  {blk['iso']:<6} {blk['recipe']:<5} -> {blk['screen_year']} "
              f"({blk['screen_year_delta_mw']:,.1f} MW)")

    Path(args.out).write_text(
        json.dumps({"blocks": out, "errors": errors}, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
