"""G-B1, zero LP: the ENTRY attribute fold at THE PIN, REF vs the CES ladder vs CES-P60.

attr = max( effective_eac_price_for_tech(config, tech, year),
            rps_credit_for_zone(rps_shadow_price, zone_idx),
            _clean_credit_for_tech(tech, ...) )
  -- model/capacity_evolution/new_entry.py, the fold with NO fuel gate.
rps_shadow_price is the solved RPS row dual; the committed REF bundle records
rps_dual = 40.0 (= STATE_RPS_ACP['NYISO'], the escape ceiling) in ALL FIVE years.

Reproduce (zero LP, THE PIN's code, no worktree and no blob fetch):

    PIN=$(mktemp -d)
    git archive bdfb3095e9fa0cd2bec3f4e843f320b42588c72b src configs scripts \
        | tar -x -C "$PIN"
    PYTHONPATH="$PIN/src:$PIN" uv run python <this file> "$PIN"

Committed output beside this file as the matching .txt (SCN-WS5A-POLICY-NYISO
ADDENDUM 2, 2026-09-07).
"""
from __future__ import annotations
import sys
from pathlib import Path

PIN = Path(sys.argv[1])
sys.path.insert(0, str(PIN / "src"))
sys.path.insert(0, str(PIN))

from market_sim.config.capacity_market import STATE_RPS_ACP
from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import (
    ScenarioConfig, SweepDefinition, resolve_policy_bundle,
)
from market_sim.config.topology_variant import set_caiso_fsno_partition
from market_sim.matrix import matrix_configs
from market_sim.policy.federal_ces import (
    effective_eac_price_for_tech, tech_credit_fraction,
)
from market_sim.model.capacity_evolution.new_entry import (
    rps_credit_for_zone, _clean_credit_for_tech,
)
from scripts.run_full_horizon import apply_set_overrides, parse_set_overrides

ISO, YEARS = "NYISO", [2026, 2027, 2028, 2029, 2030]
PIN_BASE = PIN / "configs/scenarios/nyiso_scenario_base_2026_2030.yaml"
MATRIX = PIN / "configs/scenario_campaign_matrix.yaml"

def resolve(cfg, iso=ISO):
    if cfg.iso != iso:
        cfg = cfg.with_overrides(iso=iso)
    cfg = resolve_policy_bundle(cfg)
    set_caiso_fsno_partition(False)
    return apply_iso_scenario_defaults(cfg, iso)

base = ScenarioConfig.from_yaml(PIN_BASE)
if base.iso != ISO:
    base = base.with_overrides(iso=ISO)
cfgs = matrix_configs(base, SweepDefinition.from_yaml(MATRIX))
cfgs["CES-P60"] = apply_set_overrides(
    cfgs["CES-P30"], parse_set_overrides(["federal_ces_premium_usd_per_mwh=60.0"])
)

iso_config = get_iso_config(ISO)
zones = list(iso_config.zone_names)
RPS_DUAL = 40.0                       # measured, committed REF bundle, all 5 yrs
assert STATE_RPS_ACP[ISO] == RPS_DUAL, STATE_RPS_ACP[ISO]
print(f"zones = {zones}")
print(f"rps_shadow_price = {RPS_DUAL}  (= STATE_RPS_ACP['{ISO}'] = the escape ceiling)\n")

CASES = ["REF", "CES-P10", "CES-P20", "CES-P30", "CES-P60"]
rows = {}
for case in CASES:
    c = resolve(cfgs[case])
    rows[case] = {}
    for tech in ("wind", "solar"):
        for y in YEARS:
            eac = effective_eac_price_for_tech(c, tech, y)
            clean = max(
                _clean_credit_for_tech(tech, iso_config, zones, None, zone_override=z)
                for z in zones
            )
            per_zone = [max(eac, rps_credit_for_zone(RPS_DUAL, zi), clean)
                        for zi in range(len(zones))]
            rows[case][(tech, y)] = (eac, clean, per_zone)

hdr = f"{'case':9s} {'tech':6s} " + " ".join(f"{y:>7d}" for y in YEARS)
print("EAC leg  = effective_eac_price_for_tech (= premium x credit fraction)")
print(hdr)
for case in CASES:
    for tech in ("wind", "solar"):
        v = " ".join(f"{rows[case][(tech,y)][0]:7.2f}" for y in YEARS)
        print(f"{case:9s} {tech:6s} {v}")

print("\nattr = the FOLD (identical in every zone; the RPS dual is a scalar)")
print(hdr)
for case in CASES:
    for tech in ("wind", "solar"):
        v = " ".join(f"{max(rows[case][(tech,y)][2]):7.2f}" for y in YEARS)
        assert len(set(rows[case][(tech, YEARS[0])][2])) == 1
        print(f"{case:9s} {tech:6s} {v}")

print("\nG-B1: attr(CES-P60) - attr(REF), per tech-zone-year")
ok = False
for tech in ("wind", "solar"):
    d = []
    for y in YEARS:
        a_ref = max(rows["REF"][(tech, y)][2])
        a_60 = max(rows["CES-P60"][(tech, y)][2])
        d.append(a_60 - a_ref)
        ok = ok or (a_60 > a_ref)
    print(f"  {tech:6s} " + " ".join(f"{x:+7.2f}" for x in d))
print(f"\nG-B1 {'CLEARS' if ok else 'FAILS'}: attr strictly exceeds REF's for "
      f"{'at least one' if ok else 'NO'} eligible tech-zone-year.")

print("\nThe MASK, stated per year: is rps_dual >= the CES dual the leg carries?")
for case in ("CES-P10", "CES-P20", "CES-P30", "CES-P60"):
    prem = resolve(cfgs[case]).federal_ces_premium_usd_per_mwh
    marks = ["MASKED" if RPS_DUAL >= prem else "LIVE" for _ in YEARS]
    print(f"  {case:9s} premium={prem:5.1f}  vs rps_dual=40.0  -> " + " ".join(
        f"{y}:{m}" for y, m in zip(YEARS, marks)))
