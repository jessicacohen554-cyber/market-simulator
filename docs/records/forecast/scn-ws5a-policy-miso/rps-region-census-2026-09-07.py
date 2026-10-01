"""SCN-WS5A-POLICY-MISO — RPS / clean-tier region census at THE PIN (zero LP).

Reads MISO_RPS_COMPLIANCE_REGIONS and MISO_CLEAN_TIER_REGIONS at the pin and
computes each region's obligation (obligated_load_share x floor(year) x the
obligated zone's own annual demand, on the runner's own demand chain) against
the ISO-wide eligible pool, plus the zone -> admitting-regions map that decides
where rps_credit_for_zone can be non-zero at all.

Backs ADDENDUM A of PRECOMMIT-scn-ws5a-policy-miso-2026-09-07.md.
"""

import sys, json
sys.path.insert(0, "/tmp/claude-0/-home-user-market-simulator/77771263-ea5e-509f-b311-24ce0ef12ab9/scratchpad/pin/src")
sys.path.insert(0, "/tmp/claude-0/-home-user-market-simulator/77771263-ea5e-509f-b311-24ce0ef12ab9/scratchpad/pin")
from pathlib import Path
import numpy as np
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition, resolve_policy_bundle
from market_sim.matrix import matrix_configs
from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.topology_variant import set_caiso_fsno_partition
from market_sim.config.capacity_market import MISO_RPS_COMPLIANCE_REGIONS, MISO_CLEAN_TIER_REGIONS
from market_sim.data.eia_loader import load_demand
from market_sim.runner import _scale_demand
from market_sim.data.datacenter import add_load_layers
from market_sim.config.interchange_config import build_interchange_fleet, get_interchange_spec
from market_sim.model.transmission import apply_interchange_topology
R = Path("/tmp/claude-0/-home-user-market-simulator/77771263-ea5e-509f-b311-24ce0ef12ab9/scratchpad/pin")
base = ScenarioConfig.from_yaml(R/"configs/scenarios/miso_scenario_base_2026_2030.yaml")
cfgs = matrix_configs(base, SweepDefinition.from_yaml(R/"configs/scenario_campaign_matrix.yaml"))
cfg = resolve_policy_bundle(cfgs["REF"]); set_caiso_fsno_partition(False)
cfg = apply_iso_scenario_defaults(cfg, "MISO")
ic = get_iso_config("MISO"); spec = get_interchange_spec(cfg, "MISO")
imp = build_interchange_fleet(spec, 0.0)
ic = apply_interchange_topology(ic, spec, cfg, year=cfg.start_year, extend_node=bool(imp))
zn = ic.zone_names
d0 = load_demand("MISO", cfg.weather_year, ic, td_loss_factor=cfg.td_loss_factor,
                 include_interchange=not imp, strict_demand_profile=cfg.strict_demand_profile,
                 ercot_tie_zonal_interchange=cfg.ercot_tie_zonal_interchange)
if cfg.hours < d0.shape[1]: d0 = d0[:, :cfg.hours]
def interp(floors, y):
    ks = sorted(floors)
    if y <= ks[0]: return float(floors[ks[0]])
    if y >= ks[-1]: return float(floors[ks[-1]])
    for a, b in zip(ks, ks[1:]):
        if a <= y <= b:
            return float(floors[a] + (floors[b]-floors[a])*(y-a)/(b-a))
out = {"zone_names": zn, "rps_regions": {}, "clean_regions": {}, "zonal_demand_twh": {}}
G = {2026:103.5691, 2027:103.5691, 2028:103.5691, 2029:114.4560, 2030:127.5060}
for y in range(2026, 2031):
    d = add_load_layers(_scale_demand(d0, cfg, y), cfg, "MISO", y, zn)
    zt = {zn[i]: float(d[i].sum())/1e6 for i in range(len(zn))}
    out["zonal_demand_twh"][y] = {k: round(v,4) for k,v in zt.items()}
    for label, sp in MISO_RPS_COMPLIANCE_REGIONS.items():
        f = interp(sp["floors"], y)
        ob = sp["obligated_load_share"] * f * zt[sp["obligated_zone"]]
        out["rps_regions"].setdefault(label, {})[y] = {
            "floor": round(f,6), "obligation_twh": round(ob,4),
            "n_eligible_zones": len(sp["eligible_zones"]),
            "iso_wide_eligible_twh": G[y],
            "must_escape_vs_iso_pool": bool(ob > G[y]),
        }
    for label, sp in MISO_CLEAN_TIER_REGIONS.items():
        f = interp(sp["floors"], y)
        ob = sp["obligated_load_share"] * f * zt[sp["obligated_zone"]]
        out["clean_regions"].setdefault(label, {})[y] = {
            "floor": round(f,6), "obligation_twh": round(ob,4),
            "n_eligible_zones": len(sp["eligible_zones"]),
            "qualifying_fuels": list(sp["qualifying_fuels"]),
        }
# which zones are in NO rps region's eligible set
admit = {z: [r for r, sp in MISO_RPS_COMPLIANCE_REGIONS.items() if z in sp["eligible_zones"]] for z in zn}
out["zone_admitting_rps_regions"] = admit
print(json.dumps(out, indent=1, default=str))
