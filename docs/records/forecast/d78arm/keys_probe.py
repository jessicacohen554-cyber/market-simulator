#!/usr/bin/env python3
"""capx D78-ARM — the recipe-leg key table, at zero LP, through the shipped
harness path (``build_config`` -> ``apply_iso_scenario_defaults`` ->
``cache_key()``), the same path ``test_pjm_iso_override_arms_forecast_only``
uses.

Run ``--simulate-arm`` BEFORE ``iso_configs.py`` is edited (the ex-ante
expectation recorded in ``PRECOMMIT-capx-d78arm-2026-09-06.md`` §2) and again
with the flag omitted AFTER the edit (the measurement); the two must agree.

    uv run python docs/handoffs/d78arm/keys_probe.py --simulate-arm --out docs/handoffs/d78arm/keys_expectation.json
    uv run python docs/handoffs/d78arm/keys_probe.py --out docs/handoffs/d78arm/keys_measured.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config import iso_configs  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

FIELD = "retirement_sector_gate"


def _install_simulated_arm() -> None:
    inner = iso_configs.get_iso_config

    def patched(iso: str):
        cfg = inner(iso)
        if iso.upper() == "PJM" and FIELD not in cfg.default_scenario_overrides:
            cfg.default_scenario_overrides[FIELD] = True
        return cfg

    iso_configs.get_iso_config = patched


def _key(iso: str, **kw) -> tuple[str, dict]:
    from scripts.run_capacity_hindcast import build_config

    cfg = build_config(
        iso, 2021, 2025, "realized", vintage=2020, entry_screen_diagnostics=True, **kw
    )
    res = iso_configs.apply_iso_scenario_defaults(cfg, iso)
    posture = {
        FIELD: res.retirement_sector_gate,
        "pjm_vre_accreditation_vintage": res.pjm_vre_accreditation_vintage,
        "pjm_accreditation_design_vintage": res.pjm_accreditation_design_vintage,
        "pjm_demand_response_supply": res.pjm_demand_response_supply,
        "capacity_market_supply_clearing_by_iso": res.capacity_market_supply_clearing_by_iso,
        "capacity_adequacy_requirement_published_by_iso": res.capacity_adequacy_requirement_published_by_iso,
    }
    return res.cache_key(), posture


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate-arm", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    if args.simulate_arm:
        _install_simulated_arm()
    nogate = dict(retirement_sector_gate=False)
    novre = dict(pjm_vre_accreditation_vintage=False)
    off3 = dict(
        pjm_accreditation_design_vintage=False,
        pjm_demand_response_supply=False,
        capacity_market_supply_clearing=False,
    )
    off2 = dict(
        pjm_accreditation_design_vintage=False, pjm_demand_response_supply=False
    )
    noreq = dict(capacity_adequacy_requirement_published=False)
    legs = {
        "pjm bare": _key("PJM"),
        "pjm --no-retirement-sector-gate": _key("PJM", **nogate),
        "pjm --no-pjm-vre-accreditation-vintage": _key("PJM", **novre),
        "pjm --no-vre --no-gate": _key("PJM", **novre, **nogate),
        "pjm off3 (D57 control legs)": _key("PJM", **off3),
        "pjm off3 --no-gate": _key("PJM", **off3, **nogate),
        "pjm off3 --no-vre --no-gate": _key("PJM", **off3, **novre, **nogate),
        "pjm off3 --no-req-pub --no-vre --no-gate (D45-R bare)": _key(
            "PJM", **off3, **novre, **noreq, **nogate
        ),
        "pjm off2 (arm B legs)": _key("PJM", **off2),
        "pjm off2 --no-gate": _key("PJM", **off2, **nogate),
        "pjm off2 --no-req-pub --no-vre --no-gate (arm B)": _key(
            "PJM", **off2, **novre, **noreq, **nogate
        ),
    }
    for iso in ("MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
        legs[f"{iso.lower()} bare"] = _key(iso)
    back = ScenarioConfig(iso="PJM", mode="backcast")
    resb = iso_configs.apply_iso_scenario_defaults(back, "PJM")
    legs["pjm plain backcast"] = (
        resb.cache_key(),
        {
            FIELD: resb.retirement_sector_gate,
            "unresolved_key": back.cache_key(),
            "unmoved": resb.cache_key() == back.cache_key(),
        },
    )
    record = {
        "simulated": bool(args.simulate_arm),
        "override_present_on_disk": FIELD
        in iso_configs.get_iso_config("PJM").default_scenario_overrides,
        "scenario_config_default_key": ScenarioConfig().cache_key(),
        "legs": {k: {"cache_key": v[0], "posture": v[1]} for k, v in legs.items()},
    }
    for k, v in legs.items():
        print(f"  {k:58s} {v[0]}  gate={v[1].get(FIELD)}")
    if args.out:
        Path(args.out).write_text(json.dumps(record, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
