#!/usr/bin/env python3
"""capx D76 phase 2 — the PRE-DECLARATION instrument. Zero LP, read-only.

Resolves, at the phase-2 HEAD and **before any solve**, the two things the
phase-2 PRECOMMIT must fix in writing so neither can be written to fit a
result:

1. **The eight legs' cache keys** — PJM 2021-2025 and CAISO / ERCOT / MISO
   2021-2023, each as an explicit-OFF control and an armed leg — plus the
   STOP-1 re-assertion that the gate moves no pre-existing recipe key (all six
   ISOs × T1-H/T1-X: explicit-OFF == bare, armed distinct).
2. **Each ISO's pre-declared requirement move**, read from the phase-0 census
   seam re-derived at THIS head: the seam peak, the measured peak, their delta,
   and the shipped requirement resolver evaluated on both — so the solve's
   ``screen_adequacy_requirement_mw`` delta has a number to reproduce that was
   fixed before the LP ran.

The requirement column is re-derived at HEAD rather than quoted from phase 0
because **D67-ARM landed since** (``capacity_adequacy_requirement_published_by_iso``
= ``{"PJM": True}`` in ``_pjm_config``): PJM's requirement is now the published
whole-RTO Reliability Requirement and is peak-INDEPENDENT in every in-table
delivery year, so PJM's pre-declared requirement move is **0.0 MW** and the
gate's remaining effect there runs through accreditation, the reliability
floor / backstop and the CR-1 position. That change is the whole reason this
must be re-measured rather than carried forward.

Output: ``docs/handoffs/d76/p2_predeclare.json`` + a printed table.
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
from scripts.run_capacity_hindcast import build_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "d67"))
from gdrift_peak_probe import measured_peak_mw, seam_context, seam_peak_mw

ALL_ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM")

# The phase-2 legs, as released by the director (§0au.3): PJM gets the FULL
# 2021-2025 span because its rule-29 screen passed; CAISO, ERCOT and MISO get
# the 2021-2023 window, whose 2022 bridge year exercises the mechanism's second
# largest binding delta at half the LP. NEISO and NYISO are DEFERRED.
LEGS = {
    "PJM": (2021, 2025),
    "CAISO": (2021, 2023),
    "ERCOT": (2021, 2023),
    "MISO": (2021, 2023),
}

# Both legs of every A/B carry this flag; it is decision-neutral (the harness
# help: "Byte-identical fleet outcome") and it is what makes the whole-ledger
# diff explicable on the entry side. It is on BOTH sides, so it cancels.
ENTRY_SCREEN_DIAGNOSTICS = True

# runner.py:2125 guards the requirement/position block on ``prior_results is not
# None``, so the window's first year writes a ``screen_peak_demand_mw`` no
# screen consumed. The binding years are the window minus its first year.
FIRST_SCREEN_YEAR = 2022


def cfg_for(iso: str, span: tuple[int, int], **over):
    """Return the ISO-defaulted config for one phase-2 leg."""
    return apply_iso_scenario_defaults(
        build_config(
            iso, span[0], span[1], "realized", vintage=2020,
            entry_screen_diagnostics=ENTRY_SCREEN_DIAGNOSTICS, **over,
        ),
        iso,
    )


def leg_keys() -> dict:
    """Cache keys for the eight phase-2 legs (control = explicit OFF, arm = ON)."""
    out = {}
    for iso, span in LEGS.items():
        bare = cfg_for(iso, span).cache_key()
        control = cfg_for(
            iso, span, capacity_screen_peak_measured_hindcast=False
        ).cache_key()
        arm = cfg_for(
            iso, span, capacity_screen_peak_measured_hindcast=True
        ).cache_key()
        out[iso] = {
            "span": list(span),
            "bare_key": bare,
            "control_key": control,
            "arm_key": arm,
            "control_equals_bare": control == bare,
            "arm_distinct": arm != bare,
        }
    return out


def stop1() -> tuple[bool, list[str]]:
    """STOP 1 re-assertion at THIS head — no pre-existing recipe key moves."""
    notes, ok = [], True
    for iso in ALL_ISOS:
        for label, kw in (("t1h", {}), ("t1x", {"crossover": True})):
            span = (2023, 2027) if kw else (2021, 2025)
            vintage = 2023 if kw else 2020

            def key(**over):
                return apply_iso_scenario_defaults(
                    build_config(iso, span[0], span[1], "realized",
                                 vintage=vintage, **kw, **over),
                    iso,
                ).cache_key()

            bare = key()
            if key(capacity_screen_peak_measured_hindcast=False) != bare:
                ok = False
                notes.append(f"{iso}/{label}: explicit-OFF != bare")
            if key(capacity_screen_peak_measured_hindcast=True) == bare:
                ok = False
                notes.append(f"{iso}/{label}: armed key did not move")
    return ok, notes or ["12 recipe keys: explicit-OFF == bare, armed distinct"]


def predeclare_one(iso: str) -> dict:
    """The seam-vs-measured peak and requirement move for one leg, at HEAD."""
    span = LEGS[iso]
    cfg = cfg_for(iso, span)
    ctx = seam_context(iso, cfg, span[0])
    rows = {}
    for year in range(span[0], span[1] + 1):
        seam = seam_peak_mw(ctx, year)
        meas = measured_peak_mw(ctx, year)
        req_seam = resolve_adequacy_requirement_mw(cfg, iso, seam, year)
        req_meas = resolve_adequacy_requirement_mw(cfg, iso, meas, year)
        rows[year] = {
            "seam_peak_mw": round(seam, 3),
            "measured_peak_mw": round(meas, 3),
            "delta_mw": round(seam - meas, 3),
            "delta_pct": round(100.0 * (seam - meas) / meas, 4) if meas else None,
            "req_on_seam_peak_mw": round(req_seam, 3),
            "req_on_measured_peak_mw": round(req_meas, 3),
            "req_delta_mw": round(req_seam - req_meas, 3),
            "req_peak_independent": abs(req_seam - req_meas) < 1e-6,
            "screen_binds": year >= FIRST_SCREEN_YEAR,
        }
    return {
        "iso": iso,
        "span": list(span),
        "weather_year": cfg.weather_year,
        "demand_growth_vintage": cfg.demand_growth_vintage,
        "hindcast": bool(cfg.hindcast),
        "years": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="docs/handoffs/d76/p2_predeclare.json")
    args = ap.parse_args()

    ok, notes = stop1()
    keys = leg_keys()
    blocks = [predeclare_one(iso) for iso in LEGS]

    print(f"STOP 1 (no pre-existing key moves): {'PASS' if ok else 'FAIL'}")
    for n in notes:
        print("   ", n)
    print()
    print(f"{'iso':<6} {'span':<10} {'control (OFF)':>18} {'arm (ON)':>18} {'ctl==bare':>10}")
    for iso, k in keys.items():
        print(f"{iso:<6} {k['span'][0]}-{k['span'][1]:<5} {k['control_key']:>18} "
              f"{k['arm_key']:>18} {str(k['control_equals_bare']):>10}")
    print()
    hdr = (f"{'iso':<6} {'yr':>5} {'seam peak':>13} {'measured':>13} {'delta MW':>11} "
           f"{'delta %':>8} {'req delta MW':>13} {'req peak-indep':>15} {'binds':>6}")
    print(hdr)
    print("-" * len(hdr))
    for blk in blocks:
        for year, r in blk["years"].items():
            print(f"{blk['iso']:<6} {year:>5} {r['seam_peak_mw']:>13,.1f} "
                  f"{r['measured_peak_mw']:>13,.1f} {r['delta_mw']:>11,.1f} "
                  f"{r['delta_pct']:>8.2f} {r['req_delta_mw']:>13,.1f} "
                  f"{str(r['req_peak_independent']):>15} "
                  f"{('Y' if r['screen_binds'] else '·'):>6}")
        print()

    Path(args.out).write_text(json.dumps(
        {"stop1_pass": ok, "stop1_notes": notes, "leg_keys": keys,
         "predeclare": blocks}, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
