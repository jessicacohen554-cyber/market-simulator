"""G-C2 zero-LP census: what spec.py:1931's Corridor.carbon_adder resolves to, and what the
offer path actually prices, under the CAISO 2026 forecast posture, base vs carbon_price_delta=25."""
import sys; sys.path.insert(0, "src")
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.model.interchange.spec import get_interchange_spec, build_interchange_fleet
from market_sim.model.interchange.import_nodes import wecc_border_carbon_adder
from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
for delta in (0.0, 25.0):
    for per_hub in (False, True):
        cfg = apply_iso_scenario_defaults(ScenarioConfig(iso="CAISO", mode="forecast", start_year=2026, end_year=2026,
                                          carbon_price_delta=delta, caiso_per_hub_intertie=per_hub), "CAISO")
        price = resolve_carbon_price(cfg, 2026)
        spec = get_interchange_spec(cfg, "CAISO", year=2026)
        corr = [(c.name, c.carbon_adder) for c in spec.corridors]
        border = wecc_border_carbon_adder(price)
        gens = build_interchange_fleet(spec, border)
        unspec = [(g.unit_id, round(g.vom, 3)) for g in gens if "unspec" in g.unit_id.lower() or "spot" in g.unit_id.lower()][:6]
        print(f"delta={delta:>4} per_hub={per_hub}: resolved carbon={price:.4f} $/t; expected adder={CARB_UNSPECIFIED_IMPORT_EF*price:.4f}; "
              f"spec.corridors carbon_adder={corr}; runner-path border={border:.4f}; sample import gens vom={unspec}")
        print("   all import gen ids:", [g.unit_id for g in gens][:12], "... n=", len(gens))
