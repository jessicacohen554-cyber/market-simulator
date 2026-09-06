"""SCN-WS5A-POLICY-NYISO phase 0 (rule 29 [R-SCREEN] clause 0) — zero LP.

Resolves every chartered case at THE PIN through the SAME chain a solve uses
(``matrix_configs`` -> ``resolve_policy_bundle`` -> ``set_caiso_fsno_partition``
-> ``apply_iso_scenario_defaults``), then measures, per case and per year:

* the cache key the solve would compute;
* the resolved carbon $/tCO2 (ruling S2's ``max(state program, RFF path)``);
* the resolved carbon PROGRAM object (price adder vs mass-cap row) and, for
  ``CAP-STATE-TIGHT``, the scheduled budget in metric tonnes;
* the voluntary volume ``V(ISO, y)`` from the run's OWN demand chain
  (``load_demand`` -> ``_scale_demand`` -> ``add_load_layers``), never from a
  re-derivation of the memo's arithmetic;
* the CES premium / target row presence.

Run:  PYTHONPATH=. python3 docs/handoffs/scn-ws5a-policy-nyiso/phase0-nyiso-2026-09-06.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402

from market_sim.config.constants import (  # noqa: E402
    VOLUNTARY_BASELINE_ISO_WEIGHT,
    VOLUNTARY_BASELINE_SHARE,
    VOLUNTARY_COMMITTED_DC_FRACTION,
    VOLUNTARY_ELIGIBLE_FUELS_DEFAULT,
    VOLUNTARY_WTP_CEILING_USD_PER_MWH,
)
from market_sim.config.fuel_trajectories import CARBON_PRICE_PATHS  # noqa: E402
from market_sim.config.iso_configs import (  # noqa: E402
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition  # noqa: E402
from market_sim.config.topology_variant import set_caiso_fsno_partition  # noqa: E402
from market_sim.data.eia_loader import load_demand  # noqa: E402
from market_sim.matrix import matrix_configs  # noqa: E402
from market_sim.policy.cap_and_trade import (  # noqa: E402
    resolve_carbon_program,
    scheduled_power_sector_budget,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.federal_ces import premium_for_year  # noqa: E402
from market_sim.policy.voluntary_demand import resolve_voluntary_volume  # noqa: E402
from market_sim.runner import _scale_demand  # noqa: E402
from market_sim.data.datacenter import add_load_layers  # noqa: E402
from market_sim.config.scenarios import resolve_policy_bundle  # noqa: E402

ISO = "NYISO"
YEARS = [2026, 2027, 2028, 2029, 2030]
BASE = REPO / "configs/scenarios/nyiso_scenario_base_2026_2030.yaml"
MATRIX = REPO / "configs/scenario_campaign_matrix.yaml"

CASES = [
    "REF",
    "CARB-LO",
    "CARB-MID",
    "CARB-HI",
    "CES-P10",
    "CES-P20",
    "CES-P30",
    "CES-T80",
    "CARB-MID+LOAD-HI",
    "LOAD-HI",
    "VOL-MID",
    "VOL-HI",
    "CES-P20+VOL-HI",
    "ALL-CLEAN",
    "CAP-STATE-TIGHT",
]


def resolve(cfg: ScenarioConfig, iso: str) -> ScenarioConfig:
    """The runner's own resolution chain, up to cache_key()."""
    if cfg.iso != iso:
        cfg = cfg.with_overrides(iso=iso)
    cfg = resolve_policy_bundle(cfg)
    set_caiso_fsno_partition(False)
    return apply_iso_scenario_defaults(cfg, iso)


def demand_for(cfg: ScenarioConfig, iso: str) -> tuple[list[str], dict[int, np.ndarray]]:
    """year -> (n_zones, T) demand the LP is handed, per the runner's chain."""
    from market_sim.config.interchange_config import (
        build_interchange_fleet,
        get_interchange_spec,
    )
    from market_sim.model.transmission import apply_interchange_topology

    iso_config = get_iso_config(iso)
    spec = get_interchange_spec(cfg, iso)
    import_gens = build_interchange_fleet(spec, 0.0)
    iso_config = apply_interchange_topology(
        iso_config, spec, cfg, year=cfg.start_year, extend_node=bool(import_gens)
    )
    zone_names = iso_config.zone_names
    base = load_demand(
        iso,
        cfg.weather_year,
        iso_config,
        td_loss_factor=cfg.td_loss_factor,
        include_interchange=not import_gens,
        strict_demand_profile=cfg.strict_demand_profile,
        ercot_tie_zonal_interchange=cfg.ercot_tie_zonal_interchange,
    )
    if cfg.hours < base.shape[1]:
        base = base[:, : cfg.hours]
    out = {}
    for y in YEARS:
        d = _scale_demand(base, cfg, y)
        d = add_load_layers(d, cfg, iso, y, zone_names)
        out[y] = d
    return zone_names, out


def main() -> int:
    base_cfg = ScenarioConfig.from_yaml(BASE)
    sweep = SweepDefinition.from_yaml(MATRIX)
    configs = matrix_configs(base_cfg, sweep)

    missing = [c for c in CASES if c not in configs]
    if missing:
        raise SystemExit(f"cases absent from the matrix: {missing}")

    out: dict = {
        "iso": ISO,
        "years": YEARS,
        "base_config": str(BASE.relative_to(REPO)),
        "matrix": str(MATRIX.relative_to(REPO)),
        "constants": {
            "CARBON_PRICE_PATHS": {
                k: {str(y): v for y, v in p.items()}
                for k, p in CARBON_PRICE_PATHS.items()
            },
            "VOLUNTARY_BASELINE_SHARE": {
                k: {str(y): v for y, v in p.items()}
                for k, p in VOLUNTARY_BASELINE_SHARE.items()
            },
            "VOLUNTARY_COMMITTED_DC_FRACTION": {
                k: {str(y): v for y, v in p.items()}
                for k, p in VOLUNTARY_COMMITTED_DC_FRACTION.items()
            },
            "VOLUNTARY_WTP_CEILING_USD_PER_MWH": VOLUNTARY_WTP_CEILING_USD_PER_MWH,
            "VOLUNTARY_ELIGIBLE_FUELS_DEFAULT": list(VOLUNTARY_ELIGIBLE_FUELS_DEFAULT),
            "VOLUNTARY_BASELINE_ISO_WEIGHT_NYISO": VOLUNTARY_BASELINE_ISO_WEIGHT.get(
                ISO
            ),
        },
        "cases": {},
    }

    # Demand is a function of (demand_growth_path, datacenter_load_path,
    # electrification_path) only, so cache it by that triple.
    demand_cache: dict[tuple, tuple[list[str], dict[int, np.ndarray]]] = {}

    for case in CASES:
        cfg = resolve(configs[case], ISO)
        key = cfg.cache_key()
        row: dict = {
            "cache_key": key,
            "overrides": dict(sweep.cases[case]) if hasattr(sweep, "cases") else {},
            "resolved": {
                "carbon_price_path": cfg.carbon_price_path,
                "demand_growth_path": cfg.demand_growth_path,
                "datacenter_load_path": cfg.datacenter_load_path,
                "electrification_path": cfg.electrification_path,
                "federal_ces_enabled": bool(cfg.federal_ces_enabled),
                "federal_ces_premium_usd_per_mwh": getattr(
                    cfg, "federal_ces_premium_usd_per_mwh", None
                ),
                "federal_ces_target_by_year": (
                    {str(k): v for k, v in cfg.federal_ces_target_by_year.items()}
                    if getattr(cfg, "federal_ces_target_by_year", None)
                    else None
                ),
                "federal_ces_acp_usd_per_mwh": getattr(
                    cfg, "federal_ces_acp_usd_per_mwh", None
                ),
                "voluntary_clean_demand_path": cfg.voluntary_clean_demand_path,
                "voluntary_wtp_ceiling_usd_per_mwh": getattr(
                    cfg, "voluntary_wtp_ceiling_usd_per_mwh", None
                ),
                "mass_cap_enabled": bool(getattr(cfg, "mass_cap_enabled", False)),
                "state_carbon_pricing": bool(getattr(cfg, "state_carbon_pricing", False)),
                "mass_cap_tons_by_year": (
                    {
                        k: {str(y): v for y, v in d.items()}
                        for k, d in cfg.mass_cap_tons_by_year.items()
                    }
                    if getattr(cfg, "mass_cap_tons_by_year", None)
                    else None
                ),
                "ccs_retrofit_vom_adder": getattr(cfg, "ccs_retrofit_vom_adder", None),
                "mode": cfg.mode,
                "start_year": cfg.start_year,
                "end_year": cfg.end_year,
            },
            "per_year": {},
        }

        for y in YEARS:
            prog = resolve_carbon_program(cfg, y)
            row["per_year"][str(y)] = {
                "carbon_usd_per_t": resolve_carbon_price(cfg, y),
                "ces_premium_usd_per_mwh": premium_for_year(cfg, y),
                "carbon_program": (
                    None
                    if prog is None
                    else {
                        "price_adder": getattr(prog, "price_adder", None),
                        "cap_spec": (
                            None
                            if getattr(prog, "cap_spec", None) is None
                            else {
                                k: v
                                for k, v in asdict(prog.cap_spec).items()
                                if not isinstance(v, np.ndarray)
                            }
                        ),
                    }
                ),
                "scheduled_budget_tons": scheduled_power_sector_budget(cfg, y),
            }

        # Voluntary volume, from the run's own demand.
        dkey = (
            cfg.demand_growth_path,
            cfg.datacenter_load_path,
            cfg.electrification_path,
        )
        if dkey not in demand_cache:
            demand_cache[dkey] = demand_for(cfg, ISO)
        zone_names, dem = demand_cache[dkey]
        row["demand_key"] = list(dkey)
        row["zone_names"] = zone_names
        for y in YEARS:
            # The case's own path when armed, plus mid/high on THIS case's
            # demand posture so the regime test has both levels for every arm.
            slot = {}
            for label in ("mid", "high", cfg.voluntary_clean_demand_path):
                if label == "off":
                    continue
                probe = cfg.with_overrides(voluntary_clean_demand_path=label)
                vol = resolve_voluntary_volume(probe, ISO, y, zone_names, dem[y])
                slot[label] = {
                    "baseline_share": vol.baseline_share,
                    "iso_weight": vol.iso_weight,
                    "committed_fraction": vol.committed_fraction,
                    "energy_total_twh": vol.energy_total_mwh / 1e6,
                    "energy_dc_twh": vol.energy_dc_mwh / 1e6,
                    "energy_non_dc_twh": vol.energy_non_dc_mwh / 1e6,
                    "volume_twh": vol.volume_mwh / 1e6,
                }
            slot["armed_path"] = cfg.voluntary_clean_demand_path
            row["per_year"][str(y)]["voluntary"] = slot
        out["cases"][case] = row

    dest = Path(__file__).with_suffix(".json")
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
