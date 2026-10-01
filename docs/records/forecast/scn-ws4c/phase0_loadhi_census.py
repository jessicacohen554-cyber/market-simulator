"""SCN-WS4c rule-29 phase 0 (zero LP): the LOAD-HI / LOAD-HI-ORGANIC load census.

Reproduces the SCN-WS4b pre-declared arithmetic
(docs/handoffs/load-hi-adequacy-reading-2026-09-06.md §2) directly from the
resolvers at HEAD, so every arm this lane spends an LP on is already known to
have a non-degenerate footprint. Kills the redundant arms BEFORE any solve:
an ISO whose LOAD-HI and LOAD-HI-ORGANIC DC curves coincide in the T1 window
gets no ORGANIC arm (WS-4b §3 / FINDING §5 routed item 2).
"""

from __future__ import annotations

import json

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.datacenter import resolve_datacenter_mw

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
YEARS = list(range(2026, 2031))
CASES = {
    "REF": {},
    "LOAD-HI": {"demand_growth_path": "high", "datacenter_load_path": "high"},
    "LOAD-HI-ORGANIC": {"demand_growth_path": "high", "datacenter_load_path": "mid"},
}


def cfg_for(iso: str, overrides: dict) -> ScenarioConfig:
    """Build the campaign REF posture for ``iso``, then apply the case overrides."""
    base = apply_iso_scenario_defaults(
        ScenarioConfig(iso=iso.upper(), mode="forecast", start_year=2026, end_year=2030),
        iso.upper(),
    )
    if not overrides:
        return base
    # Use the runner's OWN override seam so the census cannot drift from
    # what `--set` will actually apply at solve time.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_rfh", "scripts/run_full_horizon.py"
    )
    rfh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rfh)
    return rfh.apply_set_overrides(base, dict(overrides))


def main() -> None:
    out: dict = {}
    for iso in ISOS:
        row: dict = {}
        for case, ov in CASES.items():
            c = cfg_for(iso, ov)
            row[case] = {
                "growth_rate": {
                    y: round(float(_growth(c, iso, y)), 6) for y in YEARS
                },
                "dc_mw": {y: round(float(resolve_datacenter_mw(c, iso, y)), 3) for y in YEARS},
                "dc_block_mw": {
                    y: round(
                        float(resolve_datacenter_mw(c, iso, y)) * c.datacenter_load_factor, 3
                    )
                    for y in YEARS
                },
                "electrification_path": getattr(c, "electrification_path", None),
                "demand_growth_path": getattr(c, "demand_growth_path", None),
                "datacenter_load_path": getattr(c, "datacenter_load_path", None),
            }
        row["organic_is_degenerate"] = (
            row["LOAD-HI"]["dc_block_mw"] == row["LOAD-HI-ORGANIC"]["dc_block_mw"]
        )
        out[iso] = row
    dest = "docs/handoffs/scn-ws4c/phase0_loadhi_census.json"
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {dest}")


def _growth(c: ScenarioConfig, iso: str, year: int) -> float:
    from market_sim.config.scenario_resolvers import resolve_demand_growth_rate

    return resolve_demand_growth_rate(c, year)


if __name__ == "__main__":
    main()
