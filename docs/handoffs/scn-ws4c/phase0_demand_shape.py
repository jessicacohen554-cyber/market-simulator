"""SCN-WS4c rule-29 phase 0 (zero LP), part 2 — the realized demand series.

Part 1 (``phase0_loadhi_census.py``) checked the LEVERS. This checks what those
levers do to the 8760 the LP will actually see: it walks the runner's OWN
demand-assembly seam — ``load_demand`` -> ``_scale_demand`` ->
``add_load_layers`` — and reports energy, peak, minimum and load factor per
case.

It is the direct pre-solve test of SCN-WS4b's central construction claim: that
under ``LOAD-HI`` the RELOCATED data-centre block raises energy while LOWERING
the peak (ERCOT, NYISO) because the block is flat and the peaky organic
component is scaled down by the block's energy share. No LP is solved.
"""

from __future__ import annotations

import argparse
import importlib.util
import json

import numpy as np

from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.datacenter import add_load_layers
from market_sim.data.eia930.demand import load_demand
from market_sim.runner import _scale_demand

CASES = {
    "REF": {},
    "LOAD-HI": {"demand_growth_path": "high", "datacenter_load_path": "high"},
    "LOAD-HI-ORGANIC": {"demand_growth_path": "high", "datacenter_load_path": "mid"},
}


def build_cfg(iso: str, overrides: dict, start: int, end: int) -> ScenarioConfig:
    """Return the campaign REF posture for ``iso`` with the case applied."""
    base = apply_iso_scenario_defaults(
        ScenarioConfig(iso=iso.upper(), mode="forecast", start_year=start, end_year=end),
        iso.upper(),
    )
    if not overrides:
        return base
    spec = importlib.util.spec_from_file_location("_rfh", "scripts/run_full_horizon.py")
    rfh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rfh)
    return rfh.apply_set_overrides(base, dict(overrides))


def stats(arr: np.ndarray) -> dict:
    """Return energy / peak / min / load-factor of one zonal demand matrix."""
    total = arr.sum(axis=0)
    return {
        "energy_twh": round(float(total.sum()) / 1e6, 3),
        "peak_gw": round(float(total.max()) / 1e3, 3),
        "min_gw": round(float(total.min()) / 1e3, 3),
        "load_factor": round(float(total.mean() / total.max()), 4),
    }


def main() -> None:
    """Emit per-ISO, per-case, per-year demand-series statistics."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--isos", nargs="+", default=["ERCOT", "NYISO", "MISO", "NEISO"])
    ap.add_argument("--years", nargs="+", type=int, default=[2026])
    ap.add_argument("--out", default="docs/handoffs/scn-ws4c/phase0_demand_shape.json")
    args = ap.parse_args()

    out: dict = {}
    for iso in args.isos:
        iso_config = get_iso_config(iso.upper())
        row: dict = {}
        for case, ov in CASES.items():
            cfg = build_cfg(iso, ov, min(args.years), max(args.years))
            base = load_demand(
                iso.upper(),
                cfg.weather_year,
                iso_config,
                td_loss_factor=cfg.td_loss_factor,
                strict_demand_profile=cfg.strict_demand_profile,
                ercot_tie_zonal_interchange=cfg.ercot_tie_zonal_interchange,
            )
            zone_names = list(iso_config.zone_names)
            per_year = {}
            for year in args.years:
                dem = _scale_demand(base, cfg, year)
                dem = add_load_layers(dem, cfg, iso.upper(), year, zone_names)
                per_year[str(year)] = stats(np.asarray(dem, dtype=float))
            row[case] = per_year
        out[iso] = row
        print(iso, json.dumps(row))
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
