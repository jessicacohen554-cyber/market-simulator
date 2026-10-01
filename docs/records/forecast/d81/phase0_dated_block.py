"""capx D81 phase 0 (ZERO LP): size the PENDING owner-filed dated block in the
PJM hindcast fleets of delivery years 2022-2025.

The block is the set the charter's one-line fix moves from ``exempt_unit_ids``
(out of the screen entirely, a $0 price taker in ``Q_0`` through
:func:`_settle_capacity_supply_clearing`'s residual) to
``exit_exempt_unit_ids`` (evaluated, OFFERED at its net-ACR cap, never
decided) — DESIGN-capx-d78 §4 row 2, the channel D54 §4.2 read as a price
taker.

Construction, and why it needs no LP: the pending dated set in delivery year
Y is ``dated_plant_unit_ids(fleet_Y, announced_fossil_exits, Y)`` where
``fleet_Y`` is the run's own base fleet walked through evolve steps 0 / 1 / 1b
for every year up to Y — the only fleet mutations that can add to or remove
from it. Step 3 (the economic screen) cannot: a dated unit is exempt from it
at HEAD, which is precisely the seam this lane repairs. Steps 4/5 (additions,
entry) only add units whose plant carries no pending row (a new plant code is
absent from the registry). So the census is exact for the block, modulo the
two limits stated in ``limits`` below.

The base fleet, both registries and the config are the RUN'S OWN — captured by
patching :func:`market_sim.runner.build_base_fleet` and aborting before the
first solve, so nothing here is a re-derivation of the recipe.

Usage:
    uv run python docs/handoffs/d81/phase0_dated_block.py \
        --out docs/handoffs/d81/phase0_dated_block.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import market_sim.runner as runner  # noqa: E402
from market_sim.config.capacity_market import (  # noqa: E402
    resolve_capacity_going_forward_bar_published,
    resolve_capacity_market_supply_clearing,
    resolve_capacity_no_default_cap_convention,
)
from market_sim.config.constants import NONFOSSIL_ANNOUNCED_HORIZON_YEARS  # noqa: E402
from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402
from market_sim.data.confirmed_retirements import (  # noqa: E402
    load_announced_reversal_plants,
)
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    _THERMAL_FOM,
    _thermal_firm_mw,
    dated_plant_unit_ids,
    resolve_internal_supply_accounting_ratio,
)

ISO = "PJM"
START_YEAR = 2021
END_YEAR = 2025


class _StopAtBaseFleet(Exception):
    """Sentinel: the base fleet is captured, abort before any LP."""


def capture_recipe() -> dict:
    """Run the D78/D57 hindcast recipe up to the base fleet and stop.

    Returns a dict with the resolved ``config``, the base ``fleet`` and the two
    exogenous-exit registries exactly as the runner loaded them.
    """
    from run_capacity_hindcast import build_config  # noqa: PLC0415

    from market_sim.pipeline.api import run_scenario  # noqa: PLC0415

    config = build_config(
        iso=ISO,
        start_year=START_YEAR,
        end_year=END_YEAR,
        variant="realized",
        vintage=2020,
        entry_screen_diagnostics=True,
    )
    config = apply_iso_scenario_defaults(config, ISO)

    box: dict = {}
    orig = runner.build_base_fleet

    def _capture(*args, **kwargs):
        fleet = orig(*args, **kwargs)
        box["fleet"] = fleet
        box["confirmed_exits"] = list(kwargs.get("confirmed_exits") or [])
        box["announced_fossil_exits"] = list(kwargs.get("announced_fossil_exits") or [])
        box["base_year"] = args[7] if len(args) > 7 else kwargs.get("year")
        raise _StopAtBaseFleet

    runner.build_base_fleet = _capture
    try:
        run_scenario(config, ISO)
    except _StopAtBaseFleet:
        pass
    finally:
        runner.build_base_fleet = orig
    if "fleet" not in box:
        raise SystemExit("build_base_fleet was never reached — recipe changed?")
    box["config"] = config
    return box


def walk_steps_0_1(fleet, year: int, config, confirmed_exits, afx, reversed_plants):
    """Apply evolve steps 0 / 1 / 1b for ``year`` exactly as evolve_fleet does."""
    from market_sim.model import capacity as capacity  # noqa: PLC0415

    confirmed_on = bool(
        getattr(config, "confirmed_exits_enabled", False) and confirmed_exits
    )
    if confirmed_on:
        fleet = capacity.apply_confirmed_exits(fleet, year, confirmed_exits)
    fleet = capacity.apply_announced_retirements(
        fleet,
        year,
        fossil_economic=getattr(config, "forecast_fossil_retirement_economic", True),
        horizon_years=(NONFOSSIL_ANNOUNCED_HORIZON_YEARS if confirmed_on else None),
        confirmed_plant_codes=(
            frozenset(e.plant_id for e in confirmed_exits)
            if confirmed_on
            else frozenset()
        ),
        reversed_plant_codes=reversed_plants,
    )
    if bool(getattr(config, "fossil_announced_exits_enabled", False) and afx):
        fleet = capacity.apply_confirmed_exits(fleet, year, afx)
    return fleet


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    box = capture_recipe()
    config = box["config"]
    fleet = box["fleet"]
    afx = box["announced_fossil_exits"]
    confirmed_exits = box["confirmed_exits"]

    reversal_as_of = None
    if getattr(config, "hindcast", False) and config.eia860_vintage_year is not None:
        reversal_as_of = _dt.date(config.eia860_vintage_year, 12, 31)
    if getattr(config, "hindcast", False) and getattr(
        config, "hindcast_verified_announced_exits", False
    ):
        reversal_as_of = None
    reversed_plants = load_announced_reversal_plants(
        ISO, as_of=reversal_as_of, required=False
    )

    ratio = resolve_internal_supply_accounting_ratio(ISO, config)
    bar_armed = resolve_capacity_going_forward_bar_published(config, ISO)
    ndc_armed = resolve_capacity_no_default_cap_convention(config, ISO)
    clearing_armed = resolve_capacity_market_supply_clearing(config, ISO)

    out: dict = {
        "iso": ISO,
        "recipe": {
            "window": f"{START_YEAR}-{END_YEAR}",
            "vintage": config.eia860_vintage_year,
            "variant": "realized",
            "base_year": box["base_year"],
            "fossil_announced_exits_enabled": bool(
                getattr(config, "fossil_announced_exits_enabled", False)
            ),
            "confirmed_exits_enabled": bool(
                getattr(config, "confirmed_exits_enabled", False)
            ),
            "capacity_market_supply_clearing": clearing_armed,
            "capacity_going_forward_bar_published": bar_armed,
            "capacity_no_default_cap_convention": ndc_armed,
            "ccs_retrofit_available_year": int(
                getattr(config, "ccs_retrofit_available_year", 0) or 0
            ),
            "internal_supply_accounting_ratio": ratio,
        },
        "registries": {
            "announced_fossil_exit_rows": len(afx),
            "announced_fossil_exit_mw": round(sum(r.mw or 0.0 for r in afx), 1),
            "confirmed_exit_rows": len(confirmed_exits),
            "reversal_plants": len(reversed_plants),
        },
        "base_fleet_units": len(fleet),
        "years": {},
        "limits": [
            "The census walks evolve steps 0/1/1b only: it carries no economic "
            "exit (a dated unit is exempt from the screen at HEAD — the seam "
            "this lane repairs) and no new entry (a new plant code carries no "
            "pending registry row), so it is exact for the dated block itself.",
            "A unit reaches the sell-offer stack only if it ALSO has dispatch "
            "rows in the screen year; the census cannot see those without a "
            "solve, so the offering counts below are an upper bound on the "
            "screen-eligible subset.",
            "Nameplate is the post-derate pmax the walk carries (step 1b "
            "derates a plant-binned tranche in place).",
        ],
    }

    for year in range(START_YEAR + 1, END_YEAR + 1):
        fleet = walk_steps_0_1(
            fleet, year, config, confirmed_exits, afx, reversed_plants
        )
        dated = dated_plant_unit_ids(fleet, afx, year)
        rows = []
        for g in fleet:
            if g.unit_id not in dated:
                continue
            screenable = g.fuel_type in _THERMAL_FOM
            a_mw = (
                float(_thermal_firm_mw(g, ISO, config, year)) * ratio
                if screenable
                else 0.0
            )
            rows.append(
                {
                    "unit_id": g.unit_id,
                    "plant_code": int(getattr(g, "plant_code", 0) or 0),
                    "fuel": g.fuel_type,
                    "pmax_mw": round(float(g.pmax_mw), 3),
                    "screenable": screenable,
                    "accredited_mw": round(a_mw, 3),
                }
            )
        offering = [r for r in rows if r["screenable"] and r["accredited_mw"] > 0.0]
        by_fuel: dict[str, dict] = {}
        for r in offering:
            b = by_fuel.setdefault(
                r["fuel"], {"units": 0, "pmax_mw": 0.0, "accredited_mw": 0.0}
            )
            b["units"] += 1
            b["pmax_mw"] += r["pmax_mw"]
            b["accredited_mw"] += r["accredited_mw"]
        out["years"][str(year)] = {
            "fleet_units": len(fleet),
            "dated_units": len(rows),
            "dated_pmax_mw": round(sum(r["pmax_mw"] for r in rows), 1),
            "offering_units": len(offering),
            "offering_pmax_mw": round(sum(r["pmax_mw"] for r in offering), 1),
            "offering_accredited_mw": round(
                sum(r["accredited_mw"] for r in offering), 1
            ),
            "by_fuel": {
                k: {
                    "units": v["units"],
                    "pmax_mw": round(v["pmax_mw"], 1),
                    "accredited_mw": round(v["accredited_mw"], 1),
                }
                for k, v in sorted(by_fuel.items())
            },
            "units": sorted(rows, key=lambda r: -r["pmax_mw"]),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    for y, blk in out["years"].items():
        print(
            f"{y}: dated {blk['dated_units']} units / {blk['dated_pmax_mw']} MW "
            f"nameplate; offering {blk['offering_units']} / "
            f"{blk['offering_accredited_mw']} MW accredited"
        )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
