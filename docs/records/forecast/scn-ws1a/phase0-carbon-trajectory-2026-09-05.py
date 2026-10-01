"""Phase-0 zero-solve: resolved carbon $/t per ISO per horizon year per policy_bundle at HEAD."""
import json, sys
sys.path.insert(0, "src")
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.scenario_resolvers import resolve_policy_bundle
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.policy.carbon import resolve_carbon_price, resolved_base_trajectory_price
from market_sim.policy.cap_and_trade import resolve_carbon_program, projected_price
from market_sim.config.constants import CAP_AND_TRADE_PROGRAMS, CARBON_PRICE_PATHS

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
YEARS = list(range(2026, 2051))
def rff(path, year):
    p = CARBON_PRICE_PATHS[path]; ks = sorted(p)
    if year <= ks[0]: return float(p[ks[0]])
    if year >= ks[-1]: return float(p[ks[-1]])
    for lo, hi in zip(ks, ks[1:]):
        if lo <= year <= hi: return p[lo] + (year-lo)/(hi-lo)*(p[hi]-p[lo])
out = {}
for iso in ISOS:
    out[iso] = {}
    prog = CAP_AND_TRADE_PROGRAMS.get(iso)
    for bundle in ["current", "tight", "rollback"]:
        cfg = ScenarioConfig(iso=iso, mode="forecast", policy_bundle=bundle)
        cfg = resolve_policy_bundle(cfg)
        cfg = apply_iso_scenario_defaults(cfg, iso)
        rows = {}
        for y in YEARS:
            head = resolve_carbon_price(cfg, y)
            program = projected_price(prog, iso, y) if (prog is not None and cfg.state_carbon_pricing) else 0.0
            path = rff(cfg.carbon_price_path, y)
            rows[y] = dict(head=round(head, 2), program=round(program, 2), path=round(path, 2),
                           floor=round(max(path, program), 2), additive=round(path + program, 2))
        out[iso][bundle] = dict(resolved_fields=dict(carbon_price_path=cfg.carbon_price_path,
                                state_carbon_pricing=cfg.state_carbon_pricing), rows=rows)
json.dump(out, open("docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.json", "w"), indent=1)
# markdown
show = [2026, 2027, 2028, 2030, 2035, 2040, 2045, 2050]
print("| ISO | bundle | path | state | " + " | ".join(str(y) for y in show) + " |")
print("|---|---|---|---|" + "---|"*len(show))
for iso in ISOS:
    for b in ["current", "tight", "rollback"]:
        r = out[iso][b]; f = r["resolved_fields"]
        print(f"| {iso} | {b} | {f['carbon_price_path']} | {f['state_carbon_pricing']} | " + " | ".join(f"{r['rows'][y]['head']:.2f}" for y in show) + " |")
print()
print("G-C1 check: tight - current per program ISO, every year")
for iso in ["CAISO", "NYISO", "NEISO"]:
    d = [out[iso]["tight"]["rows"][y]["head"] - out[iso]["current"]["rows"][y]["head"] for y in YEARS]
    print(iso, "min delta", min(d), "max delta", max(d), "cut in all years:", all(x < 0 for x in d))
print()
print("floor vs current (tight under FLOOR semantics = max(mid, program)) strict increase?")
for iso in ["CAISO", "NYISO", "NEISO"]:
    d = [out[iso]["tight"]["rows"][y]["floor"] - out[iso]["current"]["rows"][y]["head"] for y in YEARS]
    print(iso, "min", min(d), "max", max(d), "any year where mid > program:", [y for y in YEARS if out[iso]['tight']['rows'][y]['path'] > out[iso]['tight']['rows'][y]['program']])
