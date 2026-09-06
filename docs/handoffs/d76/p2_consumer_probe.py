"""Why is PJM INERT? Probe accredited_firm_capacity_mw's peak-sensitivity. Zero LP."""
import json, sys
sys.path[:0] = ["src", "."]
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.model.capacity_evolution.retirements import (
    resolve_adequacy_requirement_mw, gross_adequacy_requirement_mw)
from scripts.run_capacity_hindcast import build_config

PRE = json.load(open("docs/handoffs/d76/p2_predeclare.json"))
for blk in PRE["predeclare"]:
    iso = blk["iso"]
    cfg = apply_iso_scenario_defaults(
        build_config(iso, blk["span"][0], blk["span"][1], "realized",
                     vintage=2020, entry_screen_diagnostics=True), iso)
    print(f"--- {iso} ---")
    for y, r in blk["years"].items():
        y = int(y); seam, meas = r["seam_peak_mw"], r["measured_peak_mw"]
        g_s = gross_adequacy_requirement_mw(cfg, iso, seam, y)
        g_m = gross_adequacy_requirement_mw(cfg, iso, meas, y)
        n_s = resolve_adequacy_requirement_mw(cfg, iso, seam, y)
        n_m = resolve_adequacy_requirement_mw(cfg, iso, meas, y)
        print(f"  {y}  gross req {g_s:12,.1f} -> {g_m:12,.1f}  d={g_m-g_s:10,.1f}"
              f"   net req {n_s:12,.1f} -> {n_m:12,.1f}  d={n_m-n_s:10,.1f}")
