"""The other half: is PJM's accreditation census peak-sensitive? Zero LP."""
import json, sys
sys.path[:0] = ["src", "."]
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.model.capacity_evolution.retirements import (
    gross_adequacy_requirement_mw, resolve_demand_response_supply_mw,
    resolve_renewable_capacity_credit)
from scripts.run_capacity_hindcast import build_config

PRE = json.load(open("docs/handoffs/d76/p2_predeclare.json"))
LED = "results/hindcast/d76p2-{}-control/{}/{}/evolution_{}.json"
KEYS = {"PJM": ("d76p2-pjm-control", "a9c66d8ea25acb9d")}
for blk in PRE["predeclare"]:
    iso = blk["iso"]
    if iso not in KEYS: continue
    cfg = apply_iso_scenario_defaults(
        build_config(iso, blk["span"][0], blk["span"][1], "realized",
                     vintage=2020, entry_screen_diagnostics=True), iso)
    print(f"--- {iso} ---")
    for y, r in blk["years"].items():
        y = int(y); seam, meas = r["seam_peak_mw"], r["measured_peak_mw"]
        try:
            led = json.load(open(f"results/hindcast/{KEYS[iso][0]}/{iso}/{KEYS[iso][1]}/evolution_{y}.json"))
        except FileNotFoundError:
            continue
        wind, solar = led.get("wind_cap_mw") or 0.0, led.get("solar_cap_mw") or 0.0
        row = []
        for fuel, cap in (("wind", wind), ("solar", solar)):
            a = resolve_renewable_capacity_credit(fuel, iso, installed_mw=cap, peak_demand_mw=seam,
                curves_enabled=cfg.renewable_elcc_curves, nqc_curves_enabled=cfg.caiso_nqc_accreditation, config=cfg, year=y)
            b = resolve_renewable_capacity_credit(fuel, iso, installed_mw=cap, peak_demand_mw=meas,
                curves_enabled=cfg.renewable_elcc_curves, nqc_curves_enabled=cfg.caiso_nqc_accreditation, config=cfg, year=y)
            row.append(f"{fuel} {a}->{b}")
        dr_a = resolve_demand_response_supply_mw(cfg, iso, y, gross_adequacy_requirement_mw(cfg, iso, seam, y))
        dr_b = resolve_demand_response_supply_mw(cfg, iso, y, gross_adequacy_requirement_mw(cfg, iso, meas, y))
        print(f"  {y}  " + "  ".join(row) + f"   DR {dr_a}->{dr_b}")
