"""PJM RUBRIC-RESIDUAL phase 0 — the E&AS operand, measured and re-cleared at ZERO LP.

Rule 29 [R-SCREEN] step 0. Reads ONLY committed artifacts:

  * ``results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm`` — the
    registered bare ``pjm-t1h`` (key ``fb16fda2ddb0a94a``), which under rule
    29(b) form 4 IS this lane's control;
  * ``results/calibration/pjm169_tp2022_2021_f2arm/hourly`` — a committed PJM
    2021 BACKCAST solve whose config carries ``energy_reserve_coopt=True`` /
    ``pjm_reserve_pergen=True`` / ``pjm_reserve_supply_cap=True``, i.e. the
    reserve co-optimization the hindcast lane runs WITHOUT.

Four measurements, in order:

  A. the operand as the T1-H screen saw it (per year, per fuel);
  B. the committed 2022 clearing REPRODUCED offline from its own offer stack
     (identity gate — nothing downstream is read unless this is exact);
  C. the counterfactual: uncleared set vs a per-class E&AS uplift, swept;
  D. the supply side: what a reserve-co-optimized PJM price surface would pay
     the SAME units on their OWN marginal costs.

No solve, no config change, no mechanism armed.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

HC = ROOT / "results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm"
LEDGERS = HC / "PJM/fb16fda2ddb0a94a"
BC_HOURLY = ROOT / "results/calibration/pjm169_tp2022_2021_f2arm/hourly"

OUT: dict = {"lane": "pjm-rubric-residual", "phase": 0, "control_key": "fb16fda2ddb0a94a"}


def _ledger(year: int) -> dict:
    return json.loads((LEDGERS / f"evolution_{year}.json").read_text())


# ---------------------------------------------------------------------------
# A. The operand as the screen saw it
# ---------------------------------------------------------------------------
def measure_operand() -> dict:
    rows = []
    for year in (2021, 2022, 2023, 2024, 2025):
        led = _ledger(year)
        decided = [e for e in led["pipeline_events"] if e["event"] == "decided"]
        by_fuel: dict[str, list] = defaultdict(list)
        for e in decided:
            by_fuel[e["fuel"]].append(e)
        for fuel, es in sorted(by_fuel.items()):
            mw = sum(e["mw"] for e in es)
            gfc = sum(e["going_forward_cost_usd"] for e in es)
            eas_energy = sum(e["energy_margin_usd"] for e in es)
            eas_res = sum(e["reserve_uplift_usd"] for e in es)
            rows.append(
                {
                    "year": year,
                    "fuel": fuel,
                    "n_units": len(es),
                    "mw": round(mw, 1),
                    "gfc_usd": round(gfc, 0),
                    "energy_margin_usd": round(eas_energy, 0),
                    "reserve_uplift_usd": round(eas_res, 0),
                    "eas_over_gfc": round((eas_energy + eas_res) / gfc, 6) if gfc else None,
                    "eas_per_mw_yr": round((eas_energy + eas_res) / mw, 2) if mw else None,
                    "reserve_signal_mean_usd_mwh": round(
                        float(np.mean([e["reserve_signal_mean_usd_mwh"] for e in es])), 4
                    ),
                    "screen_price_max_usd_mwh": round(
                        float(np.max([e["screen_price_max_usd_mwh"] for e in es])), 4
                    ),
                    "screen_price_mean_usd_mwh": round(
                        float(np.mean([e["screen_price_mean_usd_mwh"] for e in es])), 4
                    ),
                    "mc_mean_min": round(float(np.min([e["mc_mean_usd_mwh"] for e in es])), 2),
                    "mc_mean_max": round(float(np.max([e["mc_mean_usd_mwh"] for e in es])), 2),
                }
            )
    return {"decided_rows_by_year_fuel": rows}


# ---------------------------------------------------------------------------
# B. Reproduce the committed clearing offline (identity gate)
# ---------------------------------------------------------------------------
def reproduce_clearing(year: int, uplift_per_mw_day: dict[str, float] | None = None) -> dict:
    """Re-clear the committed offer stack, optionally with a per-fuel E&AS uplift.

    ``uplift_per_mw_day`` is stated in $/MW-day OF ACCREDITED CAPACITY, the same
    unit the offer is in: an E&AS increment of D lowers the offer
    ``max(0, GFC - EAS)/(A*365)`` by exactly D when the unit is above its floor.
    No other quantity is needed, so nothing is assumed about pmax or the bar.
    """
    from market_sim.model.capacity_evolution.adequacy import (
        capacity_supply_curve,
        clear_capacity_supply_stack,
    )
    from market_sim.config.scenarios import ScenarioConfig

    led = _ledger(year)
    cc = led["capacity_clearing"]
    cfg_raw = json.loads((HC / "run_config.json").read_text())["scenario_config"]
    import dataclasses

    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    cfg = ScenarioConfig(**{k: v for k, v in cfg_raw.items() if k in names})

    up = uplift_per_mw_day or {}
    offers = []
    for uid, fuel, offer, a_mw, _cleared in cc["offer_stack"]:
        offers.append((uid, fuel, max(0.0, float(offer) - up.get(fuel, 0.0)), float(a_mw), 0.0))

    clearing = clear_capacity_supply_stack(
        offers,
        float(cc["price_takers_mw"]),
        float(cc["requirement_mw"]),
        capacity_supply_curve(cfg, "PJM", year),
    )
    uncleared: dict[str, float] = defaultdict(float)
    for uid, fuel, _o, a_mw, _n in offers:
        if uid not in clearing.cleared_unit_ids:
            uncleared[fuel] += a_mw
    return {
        "year": year,
        "uplift_per_mw_day": up,
        "price_usd_per_mw_day": round(clearing.price_usd_per_mw_day, 6),
        "cleared_position": round(clearing.cleared_position, 6),
        "n_uncleared": clearing.n_uncleared,
        "uncleared_mw_by_fuel": {k: round(v, 3) for k, v in sorted(uncleared.items())},
        "how": clearing.how,
        "marginal_unit": clearing.marginal_unit_id,
    }


# ---------------------------------------------------------------------------
# D. What a reserve-co-optimized PJM price surface would pay the same units
# ---------------------------------------------------------------------------
def measure_supply(year_ledger: int = 2022, bc_year: int = 2021) -> dict:
    """Pro-forma E&AS for the T1-H decided units on the BACKCAST price surface.

    Same units, same marginal costs, same availability — only the hourly price
    and reserve series change, from the hindcast lane's co-opt-less duals to a
    committed PJM solve that carries the co-optimization. Order-of-magnitude
    instrument only: the backcast fleet, demand and offer curves are its own.
    """
    sysdf = pd.read_parquet(BC_HOURLY / f"system_{bc_year}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    price = {z: g.sort_values("hour")["price"].to_numpy() for z, g in sysdf.groupby("zone")}
    resv = {z: g.sort_values("hour")["reserve_price"].to_numpy() for z, g in sysdf.groupby("zone")}

    led = _ledger(year_ledger)
    decided = [e for e in led["pipeline_events"] if e["event"] == "decided"]
    zones = sorted(price)

    def zone_of(uid: str) -> str | None:
        hits = [z for z in zones if z != "PJM_external" and f"_{z}_" in uid]
        return max(hits, key=len) if hits else None

    per_unit, unmapped = [], []
    for e in decided:
        z = zone_of(e["unit_id"])
        if z is None:
            unmapped.append(e["unit_id"])
            continue
        cap = e["mw"] * e["availability_mean"]
        energy = float(np.dot(np.maximum(price[z] - e["mc_mean_usd_mwh"], 0.0), np.full(8760, cap)))
        joint = float(
            np.dot(
                np.maximum(np.maximum(price[z] - e["mc_mean_usd_mwh"], 0.0), resv[z]),
                np.full(8760, cap),
            )
        )
        a_mw = e["capacity_accredited_mw"]
        per_unit.append(
            {
                "unit_id": e["unit_id"],
                "fuel": e["fuel"],
                "zone": z,
                "mw": e["mw"],
                "mc": e["mc_mean_usd_mwh"],
                "accredited_mw": a_mw,
                "hc_eas_usd": e["energy_margin_usd"] + e["reserve_uplift_usd"],
                "bc_energy_eas_usd": energy,
                "bc_joint_eas_usd": joint,
                "bc_eas_per_accredited_mw_day": (joint / (a_mw * 365.0)) if a_mw > 0 else None,
                "hc_offer_per_mw_day": e["capacity_offer_usd_per_mw_day"],
            }
        )

    vals = [
        u["bc_eas_per_accredited_mw_day"]
        for u in per_unit
        if u["bc_eas_per_accredited_mw_day"] is not None
    ]
    return {
        "ledger_year": year_ledger,
        "backcast_price_year": bc_year,
        "n_units_mapped": len(per_unit),
        "n_unmapped": len(unmapped),
        "unmapped_sample": unmapped[:5],
        "total_mw": round(sum(u["mw"] for u in per_unit), 1),
        "hc_eas_total_usd": round(sum(u["hc_eas_usd"] for u in per_unit), 0),
        "bc_energy_eas_total_usd": round(sum(u["bc_energy_eas_usd"] for u in per_unit), 0),
        "bc_joint_eas_total_usd": round(sum(u["bc_joint_eas_usd"] for u in per_unit), 0),
        "bc_eas_per_accredited_mw_day": {
            "min": round(float(np.min(vals)), 3),
            "p25": round(float(np.percentile(vals, 25)), 3),
            "median": round(float(np.median(vals)), 3),
            "p75": round(float(np.percentile(vals, 75)), 3),
            "max": round(float(np.max(vals)), 3),
            "mw_weighted_mean": round(
                float(
                    np.average(
                        vals,
                        weights=[
                            u["accredited_mw"]
                            for u in per_unit
                            if u["bc_eas_per_accredited_mw_day"] is not None
                        ],
                    )
                ),
                3,
            ),
        },
        "per_unit": per_unit,
    }


def main() -> None:
    OUT["A_operand"] = measure_operand()

    # B — identity gate on every year that cleared.
    ident = []
    for year in (2022, 2023, 2024, 2025):
        led = _ledger(year)
        cc = led.get("capacity_clearing")
        if not cc:
            continue
        repro = reproduce_clearing(year)
        ident.append(
            {
                "year": year,
                "committed_price": round(cc["price_usd_per_mw_day"], 6),
                "repro_price": repro["price_usd_per_mw_day"],
                "price_abs_err": abs(cc["price_usd_per_mw_day"] - repro["price_usd_per_mw_day"]),
                "committed_position": round(cc["cleared_position"], 6),
                "repro_position": repro["cleared_position"],
                "position_abs_err": abs(cc["cleared_position"] - repro["cleared_position"]),
                "committed_uncleared": {k: round(v, 3) for k, v in cc["uncleared_mw_by_fuel"].items()},
                "repro_uncleared": repro["uncleared_mw_by_fuel"],
            }
        )
    OUT["B_identity"] = ident
    # The gate's tolerance is the LEDGER's own serialization, not a chosen
    # slack: ``offer_stack`` writes ``round(o, 4)`` $/MW-day and
    # ``round(a_mw, 3)`` MW (adequacy.py CapacityClearing.to_dict), so a
    # reproduction from the ledger cannot beat 1e-4 on price. Position is
    # required EXACT — it carries no such rounding path.
    OUT["B_tolerance"] = {
        "price_usd_per_mw_day": 1e-3,
        "position": 0.0,
        "uncleared_mw_per_fuel": 0.01,
        "basis": "offer_stack serializes round(o, 4) $/MW-day and round(a_mw, 3) MW",
    }
    exceptions = []
    for r in ident:
        if r["price_abs_err"] >= 1e-3 or r["position_abs_err"] > 0.0:
            exceptions.append({"year": r["year"], "kind": "price_or_position"})
        fuels = set(r["committed_uncleared"]) | set(r["repro_uncleared"])
        for f in sorted(fuels):
            d = abs(r["committed_uncleared"].get(f, 0.0) - r["repro_uncleared"].get(f, 0.0))
            if d > 0.01:
                exceptions.append(
                    {"year": r["year"], "fuel": f, "mw_delta": round(d, 3), "kind": "uncleared_mw"}
                )
    OUT["B_exceptions"] = exceptions
    screen_year_clean = not [e for e in exceptions if e["year"] == 2022]
    OUT["B_gate_screen_year_2022_clean"] = screen_year_clean
    if not screen_year_clean:
        OUT["STOP"] = "B identity gate failed on the screen year 2022"
        print(json.dumps(OUT, indent=1))
        return

    # C — the sweep, on the zero-E&AS classes only (gas_ct / gas_st / oil).
    sweep = []
    for delta in (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 75.0, 100.0):
        up = {"gas_ct": delta, "gas_st": delta, "oil": delta}
        r = reproduce_clearing(2022, up)
        r["delta_per_mw_day"] = delta
        r["delta_per_kw_yr"] = round(delta * 365.0 / 1000.0, 3)
        sweep.append(r)
    OUT["C_sweep_2022"] = sweep

    OUT["D_supply"] = measure_supply(2022, 2021)

    out_path = Path(__file__).with_suffix(".json")
    out_path.write_text(json.dumps(OUT, indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
