#!/usr/bin/env python3
"""G-DRIFT probe (capx D67): does the PJM T1-H SCREEN SEAM PEAK reproduce at HEAD?

Zero LP. Rebuilds the screen-seam peak the way ``runner.py`` does at the top of
its year loop (``_scale_demand`` over the once-loaded weather-year base, then
``add_load_layers``) and compares it to the committed D57 arm A ledger's
``screen_peak_demand_mw``. A 0.000 MW match proves the demand path -- and with
it every SCN load-table hunk in the drift window -- INERT for this recipe by
measurement rather than by argument (rule 29 [R-SCREEN] clause (b), G-DRIFT).
"""

import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.iso_configs import (
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.paths import set_eia860_vintage
from market_sim.data.datacenter import add_load_layers
from market_sim.data.eia_loader import load_demand
from market_sim.model.interchange.spec import (
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.runner import _get_growth_rate, _scale_demand
from scripts.run_capacity_hindcast import build_config

ARM_A = Path("results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a")
ISO = "PJM"
YEARS = range(2021, 2026)


def main() -> int:
    cfg = apply_iso_scenario_defaults(
        build_config(ISO, 2021, 2025, "realized", vintage=2020,
                     entry_screen_diagnostics=True),
        ISO,
    )
    # Reproduce runner.run_scenario's preamble exactly: interchange topology
    # first (it can extend the node set), then the vintage pin, then the
    # once-loaded weather-year base.
    iso_config = get_iso_config(ISO)
    spec = get_interchange_spec(cfg, ISO)
    import_generators = build_interchange_fleet(spec, 0.0)
    iso_config = apply_interchange_topology(
        iso_config, spec, cfg, year=2021, extend_node=bool(import_generators)
    )
    zone_names = iso_config.zone_names
    set_eia860_vintage(
        cfg.eia860_vintage_year if (cfg.mode == "backcast" or cfg.hindcast) else None
    )

    base = load_demand(ISO, cfg.weather_year, iso_config,
                       td_loss_factor=cfg.td_loss_factor,
                       include_interchange=not import_generators,
                       strict_demand_profile=cfg.strict_demand_profile,
                       ercot_tie_zonal_interchange=cfg.ercot_tie_zonal_interchange)
    if cfg.hours < base.shape[1]:
        base = base[:, : cfg.hours]

    print(f"weather_year={cfg.weather_year}  growth_vintage={cfg.demand_growth_vintage}")
    print("growth rates read: " +
          ", ".join(f"{y}:{_get_growth_rate(cfg, y):.6f}" for y in range(2021, 2026)))
    print()
    hdr = f"{'year':>6} {'screen peak @HEAD':>19} {'arm A committed':>17} {'delta MW':>12}"
    print(hdr); print("-" * len(hdr))
    out, worst = {}, 0.0
    for year in YEARS:
        dem = _scale_demand(base, cfg, year)
        dem = add_load_layers(dem, cfg, ISO, year, zone_names)
        peak = float(dem.sum(axis=0).max())
        committed = json.loads((ARM_A / f"evolution_{year}.json").read_text())
        ref = float(committed["screen_peak_demand_mw"])
        delta = peak - ref
        worst = max(worst, abs(delta))
        out[year] = {"head": peak, "arm_a": ref, "delta": delta}
        print(f"{year:>6} {peak:>19.3f} {ref:>17.3f} {delta:>12.3f}")
    print()
    verdict = "INERT (0.000 MW)" if worst < 5e-4 else f"LIVE (max |delta| {worst:.3f} MW)"
    print(f"VERDICT: demand path @HEAD vs D57 arm A -> {verdict}")
    Path("docs/handoffs/d67/gdrift_peak_probe.json").write_text(
        json.dumps({"iso": ISO, "years": out, "max_abs_delta_mw": worst,
                    "verdict": verdict}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
