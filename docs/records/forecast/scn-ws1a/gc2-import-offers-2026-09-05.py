import sys; sys.path.insert(0, "src")
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.model.interchange.spec import get_interchange_spec, build_interchange_fleet
from market_sim.model.interchange.import_nodes import wecc_border_carbon_adder
from market_sim.config.constants import CAP_AND_TRADE_PROGRAMS, CARBON_PRICE_PATHS
from market_sim.policy.cap_and_trade import projected_price
rows = {}
for delta in (0.0, 25.0):
    cfg = apply_iso_scenario_defaults(ScenarioConfig(iso="CAISO", mode="forecast", start_year=2026, end_year=2026, carbon_price_delta=delta), "CAISO")
    price = resolve_carbon_price(cfg, 2026)
    gens = build_interchange_fleet(get_interchange_spec(cfg, "CAISO", year=2026), wecc_border_carbon_adder(price))
    for g in gens:
        rows.setdefault(g.unit_id, {})[delta] = (round(g.vom, 4), round(g.heat_rate, 4), g.pmax_mw, g.fuel_type)
print("| import unit | vom @ base (carbon 30.02) | vom @ delta=25 (55.02) | Δvom | hr | MW |")
print("|---|---|---|---|---|---|")
for uid, d in rows.items():
    b, h = d[0.0], d[25.0]
    print(f"| {uid} | {b[0]} | {h[0]} | {round(h[0]-b[0],4)} | {b[1]} | {b[2]} |")
print()
print("RFF path vs program trajectory crossing years (path > program):")
def rff(path, year):
    p = CARBON_PRICE_PATHS[path]; ks = sorted(p)
    if year <= ks[0]: return float(p[ks[0]])
    if year >= ks[-1]: return float(p[ks[-1]])
    for lo, hi in zip(ks, ks[1:]):
        if lo <= year <= hi: return p[lo] + (year-lo)/(hi-lo)*(p[hi]-p[lo])
for iso in ("CAISO", "NYISO", "NEISO"):
    prog = CAP_AND_TRADE_PROGRAMS[iso]
    for path in ("low", "mid", "high"):
        yrs = [y for y in range(2026, 2051) if rff(path, y) > projected_price(prog, iso, y)]
        print(iso, path, "years where RFF path exceeds program:", yrs if yrs else "none", "| max gap", round(max(rff(path,y)-projected_price(prog,iso,y) for y in range(2026,2051)),2))
