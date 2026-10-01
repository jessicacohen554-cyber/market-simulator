"""The other half: is an ISO's accreditation census peak-sensitive? Zero LP.

Evaluates the shipped accreditation resolvers at BOTH peaks — the seam peak the
control screens against and the measured peak the arm screens against — on the
control leg's own committed VRE pools, so a census that does not move is
measured rather than inferred.

Phase 3 (2026-09-06) added ``--predeclare`` and ``--bundle ISO=PATH`` so the
same probe serves the two deferred ISOs; the cache-key directory is now globbed
from the bundle (as ``p2_gate.ledgers`` does) instead of being pasted in, which
is what made the phase-2 form single-ISO. A bare invocation keeps phase 2's
defaults.
"""
import argparse, json, sys
from pathlib import Path
sys.path[:0] = ["src", "."]
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.model.capacity_evolution.retirements import (
    gross_adequacy_requirement_mw, resolve_demand_response_supply_mw,
    resolve_renewable_capacity_credit)
from scripts.run_capacity_hindcast import build_config

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--predeclare", default="docs/handoffs/d76/p2_predeclare.json")
ap.add_argument("--bundle", nargs="+", default=["PJM=results/hindcast/d76p2-pjm-control"],
                help="ISO=CONTROL_BUNDLE_DIR pairs.")
args = ap.parse_args()

BUNDLES = dict(b.split("=", 1) for b in args.bundle)


def ledger(iso: str, year: int):
    """Load one control-leg year ledger, globbing the single cache-key dir."""
    root = Path(BUNDLES[iso]) / iso
    keys = [p for p in root.iterdir() if p.is_dir()]
    if len(keys) != 1:
        raise RuntimeError(f"{root}: expected one cache-key dir, got {keys}")
    return json.loads((keys[0] / f"evolution_{year}.json").read_text())


PRE = json.load(open(args.predeclare))
for blk in PRE["predeclare"]:
    iso = blk["iso"]
    if iso not in BUNDLES:
        continue
    cfg = apply_iso_scenario_defaults(
        build_config(iso, blk["span"][0], blk["span"][1], "realized",
                     vintage=2020, entry_screen_diagnostics=True), iso)
    print(f"--- {iso} ---")
    for y, r in blk["years"].items():
        y = int(y); seam, meas = r["seam_peak_mw"], r["measured_peak_mw"]
        try:
            led = ledger(iso, y)
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
