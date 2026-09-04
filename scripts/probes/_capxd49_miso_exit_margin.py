"""capx D49 half 2 — the MISO exit-side margin, read from committed ledgers (zero solve).

For every screened UNDATED thermal unit the D46 MISO T1-H ledgers record (the
FFR-5A ``pipeline_events`` bar decomposition: every unit that FAILED the bar in
a screen year), and for the actually-exited undated cohort in the published
record, this probe reports per screen year the attainable margin, the bar, the
gap, the capacity-revenue term at the position the screen consumed, and the
dispersion BAND a D43-type construction could move the energy leg by (the
run's own realized duals vs the stack signal it actually screened on, both
from the committed ``screen_signal_diag`` dumps). It then splits the
``retire.total_gw`` miss into the pre-declared H-FLOOR / H-BAR / H-WALL parts
(``docs/handoffs/PREDECL-capx-d49-2026-09-04.md`` §2.3).

Reads: ``results/hindcast/miso-2021-2025-realized-t1h-d46`` (D46, dates ON),
``…-d42-control`` (dates OFF — supplies the 2024 energy legs of units that
carry no D46 row because nothing fails there), the D46 npz dumps, and
``data/raw/_validation-source/capacity_actuals_miso.csv``. The capacity
price is evaluated through the model's own seam
(``MarketDesign.capacity_price_per_firm_mw_yr`` × ``thermal_accreditation_fraction``).

Usage::

    uv run python scripts/probes/_capxd49_miso_exit_margin.py \\
        --out results/calibration/capxd49_miso_exit_margin.json
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import EFORD, MARKET_DESIGN  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    thermal_accreditation_fraction,
)

D46 = ROOT / "results/hindcast/miso-2021-2025-realized-t1h-d46"
CTRL = ROOT / "results/hindcast/miso-2021-2025-realized-t1h-d42-control"
ACTUALS = ROOT / "data/raw/_validation-source/capacity_actuals_miso.csv"
THERMAL = ("coal", "gas_cc", "gas_ct", "gas_st", "oil")
BARS = {"coal": 45.0 * 1.3, "gas_cc": 30.0, "gas_ct": 21.0, "gas_st": 35.0, "oil": 25.0}
MISS_GW = 17.369 - 9.799  # D46 §4.2: actual − model retire.total_gw


class _Cfg:
    """Duck-typed config for the capacity-price seam (MISO curve gate ON)."""

    capacity_market_clearing = False
    capacity_market_clearing_by_iso = {"MISO": True}


def plant_of(unit_id: str) -> int | None:
    m = re.search(r"_p(\d+)_", unit_id)
    return int(m.group(1)) if m else None


def zone_of(unit_id: str) -> str | None:
    m = re.search(r"_(MISO-[A-Za-z]+)_p", unit_id)
    return m.group(1) if m else None


def load_ledgers(bundle: Path) -> dict[int, dict]:
    out = {}
    for p in sorted(glob.glob(str(bundle / "MISO" / "*" / "evolution_*.json"))):
        out[int(Path(p).stem.split("_")[1])] = json.loads(Path(p).read_text())
    return out


def capacity_term_per_kw(fuel: str, position: float | None, year: int) -> float:
    """$/kW-yr the screen credited a unit of ``fuel`` at ``position`` on ``year``'s vintage."""
    if position is None:
        return 0.0
    price = MARKET_DESIGN["MISO"].capacity_price_per_firm_mw_yr(
        _Cfg(), position, iso="MISO", year=year
    )
    return price * thermal_accreditation_fraction(fuel, EFORD.get(fuel, 0.0), "MISO") / 1000.0


def energy_leg_per_kw(prices_row: np.ndarray, mc_mean: float, avail: float) -> float:
    """Σ max(0, p − mc) × avail, $/kW-yr, at a flat time-mean mc (stated approximation)."""
    return float(np.maximum(prices_row - mc_mean, 0.0).sum() * avail) / 1000.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    d46 = load_ledgers(D46)
    ctrl = load_ledgers(CTRL)
    zones = get_iso_config("MISO").zone_names

    # ---- 1. positions and capacity terms the screens consumed -----------------
    positions = {y: d46[y].get("capacity_reserve_position") for y in d46}
    cap_terms = {
        y: {f: capacity_term_per_kw(f, positions[y], y) for f in THERMAL} for y in d46
    }
    print("== capacity term the D46 screens consumed ($/kW-yr, by fuel)")
    for y in sorted(d46):
        print(f"  {y}: position {positions[y]}  " + "  ".join(f"{f}={cap_terms[y][f]:.1f}" for f in THERMAL))
    market = {  # MISO PRA cleared, annualized $/kW-yr (D31 §4/§5; data/raw/miso-pra)
        2023: 3.65, 2024: 7.33, 2025: 79.07,
    }

    # ---- 2. the dated (exempt) plants ------------------------------------------
    sched = d46[2021].get("announced_fossil_schedule", [])
    dated_plants = {int(r["plant_id"]) for r in sched if r["disposition"] not in ("cancelled", "reversed")}
    print(f"\n== dated schedule: {len(sched)} rows, {len(dated_plants)} live plants (exempt from the screen)")

    # ---- 3. per-unit screen rows -----------------------------------------------
    def rows_of(ledgers: dict[int, dict]) -> dict[int, dict[str, dict]]:
        out: dict[int, dict[str, dict]] = {}
        for y, led in ledgers.items():
            out[y] = {e["unit_id"]: e for e in led.get("pipeline_events", [])}
        return out

    r46, rct = rows_of(d46), rows_of(ctrl)

    # ---- 4. dispersion band from the D46 dumps ---------------------------------
    dumps = {}
    for p in glob.glob(str(D46 / "MISO" / "*" / "screen_signal_diag_*_for_*.npz")):
        z = np.load(p)
        dumps[int(z["entering_year"])] = z
    band_rows = {}
    for entering, z in dumps.items():  # the dump for year y feeds the screen run in year y+1
        stack = z["price_base_usd_mwh"] + z["adder_usd_mwh"]
        duals = z["econ_prices_usd_mwh"]
        band_rows[entering] = (stack, duals)
        print(
            f"\n== dump for entering {entering}: stack mean {stack.mean():.2f} max {stack.max():.1f} | "
            f"duals zone means {np.round(duals.mean(axis=1), 2).tolist()} max {duals.max():.0f} "
            f"h>=100 {(duals >= 100).sum(axis=1).tolist()} neg {(duals < 0).sum(axis=1).tolist()}"
        )

    # ---- 5. cohort table --------------------------------------------------------
    # Universe of screened units = every unit id with any ledger row in either bundle.
    seen: dict[str, dict] = {}
    for src, rr in (("d46", r46), ("ctrl", rct)):
        for y, m in rr.items():
            for uid, e in m.items():
                seen.setdefault(uid, {"fuel": e["fuel"], "mw": e["mw"], "plant": plant_of(uid), "zone": zone_of(uid)})

    def unit_year(uid: str, y: int) -> dict:
        """Gap / band for one unit in screen year y (D46 posture)."""
        info = seen[uid]
        fuel = info["fuel"]
        bar = BARS[fuel]
        e = r46.get(y, {}).get(uid)
        out = {"year": y, "unit_id": uid, "fuel": fuel, "mw": info["mw"], "plant": info["plant"]}
        if e is not None:
            out.update(
                event=e["event"],
                net=e["net_revenue_usd"] / e["mw"] / 1000.0,
                energy=e["energy_margin_usd"] / e["mw"] / 1000.0,
                cap=e["capacity_revenue_usd"] / e["mw"] / 1000.0,
                bar=e["going_forward_cost_usd"] / e["mw"] / 1000.0,
                mc_mean=e.get("mc_mean_usd_mwh"),
                avail=e.get("availability_mean"),
                basis="d46_row",
            )
        else:
            # No D46 row: the unit did not fail this year. Reconstruct from the
            # control's 2024 row (same screen price object, dates OFF) when it
            # exists; otherwise the unit is known only to have cleared.
            c = rct.get(2024, {}).get(uid) or rct.get(2023, {}).get(uid) or rct.get(2022, {}).get(uid)
            cap = cap_terms[y][fuel] if y in cap_terms else 0.0
            if c is not None and y in (2024, 2025) and (y - 1) in band_rows and info["zone"] in zones:
                stack, duals = band_rows[y - 1]
                zi = zones.index(info["zone"])
                mc, av = float(c.get("mc_mean_usd_mwh", 0.0)), float(c.get("availability_mean", 1.0))
                en_stack = energy_leg_per_kw(stack, mc, av)
                en_duals = energy_leg_per_kw(duals[zi], mc, av)
                out.update(
                    event="cleared", energy=en_stack, cap=cap, net=en_stack + cap, bar=bar,
                    mc_mean=mc, avail=av, band=en_duals - en_stack, basis="reconstructed",
                )
            else:
                out.update(event="cleared", cap=cap, bar=bar, basis="cleared_no_row")
        if "net" in out:
            out["gap"] = out["net"] - out["bar"]
        # Band for units WITH a D46 row (2024/2025 never have one; 2022/2023 rows
        # have no matching dump — the 2021 signal is not committed). Use the
        # 2023 dump as the bound for the 2022/2023 screens, stated in the finding.
        if "band" not in out and out.get("mc_mean") is not None and info["zone"] in zones:
            key = (y - 1) if (y - 1) in band_rows else min(band_rows)
            stack, duals = band_rows[key]
            zi = zones.index(info["zone"])
            out["band"] = energy_leg_per_kw(duals[zi], out["mc_mean"], out["avail"]) - energy_leg_per_kw(
                stack, out["mc_mean"], out["avail"]
            )
            out["band_dump_year"] = key
        return out

    # ---- 6. whole-cohort census per year ----------------------------------------
    print("\n== D46 screen census by year (all ledger-known UNDATED units)")
    census = {}
    for y in (2022, 2023, 2024, 2025):
        rows = [unit_year(u, y) for u in seen if seen[u]["plant"] not in dated_plants]
        rows = [r for r in rows if r["fuel"] in THERMAL]
        failing = [r for r in rows if r.get("event") in ("entry_capped", "decided", "re_confirmed", "executed")]
        capped = [r for r in failing if r["event"] == "entry_capped"]
        mw_all = sum(r["mw"] for r in rows)
        mw_fail = sum(r["mw"] for r in failing)
        with_gap = [r for r in rows if "gap" in r]
        in_band = [r for r in with_gap if "band" in r and abs(r["gap"]) <= abs(r["band"])]
        # Sign-aware (PREDECL §2.3): the construction produces an EXIT only when
        # the band is NEGATIVE (duals leg < stack leg) and large enough to take
        # a unit at/above the bar below it, or to deepen a failing unit. A
        # positive band on a failing unit moves it TOWARD passing.
        exit_band = [r for r in in_band if r["band"] < 0.0]
        rescue_band = [r for r in in_band if r["band"] > 0.0]
        census[y] = {
            "n_units": len(rows), "mw": mw_all, "n_fail": len(failing), "mw_fail": mw_fail,
            "mw_entry_capped": sum(r["mw"] for r in capped),
            "mw_in_band": sum(r["mw"] for r in in_band),
            "mw_in_band_exit_direction": sum(r["mw"] for r in exit_band),
            "mw_in_band_rescue_direction": sum(r["mw"] for r in rescue_band),
            "mw_cap_alone_ge_bar": sum(r["mw"] for r in rows if r.get("cap", 0.0) >= r.get("bar", BARS[r["fuel"]])),
            "gap_pct": {
                f: np.percentile([r["gap"] for r in with_gap if r["fuel"] == f], [10, 50, 90]).round(1).tolist()
                for f in THERMAL if any(r["fuel"] == f for r in with_gap)
            },
            "band_abs_p90": float(np.percentile([abs(r["band"]) for r in with_gap if "band" in r], 90)) if any("band" in r for r in with_gap) else None,
            "band_abs_max": float(max([abs(r["band"]) for r in with_gap if "band" in r], default=0.0)),
            "cap_term": cap_terms.get(y),
            "position": positions.get(y),
        }
        print(
            f"  {y}: units {len(rows)} / {mw_all/1000:.1f} GW; failing {len(failing)} / {mw_fail/1000:.1f} GW "
            f"(entry_capped {census[y]['mw_entry_capped']/1000:.1f} GW); within band {census[y]['mw_in_band']/1000:.2f} GW "
            f"(exit-direction {census[y]['mw_in_band_exit_direction']/1000:.2f}, rescue-direction {census[y]['mw_in_band_rescue_direction']/1000:.2f}); "
            f"cap term alone >= bar {census[y]['mw_cap_alone_ge_bar']/1000:.1f} GW; "
            f"|band| p90 {census[y]['band_abs_p90']} max {census[y]['band_abs_max']:.1f} $/kW-yr; gap p10/50/90 by fuel {census[y]['gap_pct']}"
        )

    # ---- 7. the actually-exited undated cohort -----------------------------------
    act = pd.read_csv(ACTUALS, comment="#")
    act = act[(act["kind"] == "retirement") & (act["year"].between(2021, 2025)) & (act["fuel"].isin(THERMAL))]
    act["plant"] = act["plant_id"].astype(int)
    by_plant = act.groupby(["plant", "fuel"], as_index=False).agg(mw=("mw", "sum"), year=("year", "min"), n=("unit_id", "count"))
    total_actual = float(act["mw"].sum())
    dated_mw = float(by_plant[by_plant["plant"].isin(dated_plants)]["mw"].sum())
    undated = by_plant[~by_plant["plant"].isin(dated_plants)].copy()
    fleet_plants = {seen[u]["plant"] for u in seen}
    undated["in_model_fleet"] = undated["plant"].isin(fleet_plants)
    print(
        f"\n== actual thermal exits 2021-2025: {total_actual/1000:.3f} GW; at dated plants {dated_mw/1000:.3f} GW; "
        f"UNDATED {undated['mw'].sum()/1000:.3f} GW ({len(undated)} plant-fuels), of which in the ledger-known fleet "
        f"{undated[undated['in_model_fleet']]['mw'].sum()/1000:.3f} GW"
    )

    # model exits by channel (D46)
    model_exits = defaultdict(float)
    for y, led in d46.items():
        for r in led.get("retirements", []):
            model_exits[r.get("reason", "economic")] += r["mw"]
        for r in led.get("announced_derates", []) or []:
            model_exits["announced_derate"] += r["derate_mw"]
        for r in led.get("confirmed_derates", []) or []:
            model_exits["confirmed_derate"] += r["derate_mw"]
    print("== D46 model exits by channel (MW):", {k: round(v, 1) for k, v in model_exits.items()})

    # per-plant, per-year reading for the undated exited cohort
    cohort_rows = []
    for _, p in undated.sort_values("mw", ascending=False).iterrows():
        units = [u for u in seen if seen[u]["plant"] == p["plant"] and seen[u]["fuel"] == p["fuel"]]
        per_year = {}
        for y in (2022, 2023, 2024, 2025):
            ys = [unit_year(u, y) for u in units]
            if not ys:
                continue
            per_year[y] = {
                "events": sorted({r.get("event") for r in ys}),
                "mw_fail": sum(r["mw"] for r in ys if r.get("event") in ("entry_capped", "decided", "re_confirmed", "executed")),
                "mw_capped": sum(r["mw"] for r in ys if r.get("event") == "entry_capped"),
                "gap_mw_weighted": (sum(r["gap"] * r["mw"] for r in ys if "gap" in r) / sum(r["mw"] for r in ys if "gap" in r)) if any("gap" in r for r in ys) else None,
                "band_mw_weighted": (sum(r["band"] * r["mw"] for r in ys if "band" in r) / sum(r["mw"] for r in ys if "band" in r)) if any("band" in r for r in ys) else None,
                "cap": cap_terms[y][p["fuel"]] if y in cap_terms else 0.0,
                "mw_in_band": sum(r["mw"] for r in ys if "gap" in r and "band" in r and abs(r["gap"]) <= abs(r["band"])),
                "mw_in_band_exit_direction": sum(r["mw"] for r in ys if "gap" in r and "band" in r and abs(r["gap"]) <= abs(r["band"]) and r["band"] < 0.0),
            }
        cohort_rows.append({
            "plant": int(p["plant"]), "fuel": p["fuel"], "actual_mw": float(p["mw"]), "actual_year": int(p["year"]),
            "model_units": units, "model_mw": sum(seen[u]["mw"] for u in units), "per_year": per_year,
        })

    print("\n== undated actually-exited cohort, per plant (screen reading by year; gap/band $/kW-yr MW-weighted)")
    hdr = f"  {'plant':>6} {'fuel':6} {'act MW':>7} {'yr':>4} {'model MW':>8} | " + " | ".join(f"{y}: fail/capped MW  gap  band  cap" for y in (2022, 2023, 2024, 2025))
    print(hdr)
    for c in cohort_rows:
        cells = []
        for y in (2022, 2023, 2024, 2025):
            v = c["per_year"].get(y)
            if v is None:
                cells.append("   —   ")
                continue
            g = "" if v["gap_mw_weighted"] is None else f"{v['gap_mw_weighted']:+.1f}"
            b = "" if v["band_mw_weighted"] is None else f"{v['band_mw_weighted']:+.1f}"
            cells.append(f"{v['mw_fail']:.0f}/{v['mw_capped']:.0f} {g} {b} {v['cap']:.0f}")
        print(f"  {c['plant']:>6} {c['fuel']:6} {c['actual_mw']:7.1f} {c['actual_year']:>4} {c['model_mw']:8.1f} | " + " | ".join(cells))

    # ---- 8. the decomposition ---------------------------------------------------
    # (iii) the undated cohort's actual exits present in the model fleet; split by
    # what the screen did with them: H-FLOOR (failed and entry-capped in 2022/2023),
    # H-BAR (cleared in 2024/2025 with the capacity term alone ≥ bar), H-WALL (within band).
    reach = [c for c in cohort_rows if c["model_units"]]
    mw_reach = sum(min(c["actual_mw"], c["model_mw"]) for c in reach)
    def share(cond) -> float:
        return sum(min(c["actual_mw"], c["model_mw"]) for c in reach if cond(c))
    h_floor = share(lambda c: any(c["per_year"].get(y, {}).get("mw_capped", 0) > 0 for y in (2022, 2023)))
    h_bar = share(lambda c: all(c["per_year"].get(y, {}).get("mw_fail", 0) == 0 for y in (2024, 2025) if y in c["per_year"]) and any(c["per_year"].get(y, {}).get("cap", 0) >= BARS[c["fuel"]] for y in (2024, 2025)))
    h_wall_any = share(lambda c: any(c["per_year"].get(y, {}).get("mw_in_band", 0) > 0 for y in c["per_year"]))
    h_wall = share(lambda c: any(c["per_year"].get(y, {}).get("mw_in_band_exit_direction", 0) > 0 for y in c["per_year"]))
    decomposition = {
        "miss_gw": MISS_GW,
        "actual_thermal_exits_gw": total_actual / 1000.0,
        "actual_at_dated_plants_gw": dated_mw / 1000.0,
        "actual_undated_gw": float(undated["mw"].sum()) / 1000.0,
        "actual_undated_in_model_fleet_gw": float(undated[undated["in_model_fleet"]]["mw"].sum()) / 1000.0,
        "reachable_gw": mw_reach / 1000.0,
        "H_FLOOR_gw": h_floor / 1000.0, "H_BAR_gw": h_bar / 1000.0, "H_WALL_gw": h_wall / 1000.0,
        "H_WALL_any_direction_gw": h_wall_any / 1000.0,
        "market_position_counterfactual_kw_yr": {
            "2024_at_market_1.034": capacity_term_per_kw("coal", 1.034, 2024),
            "2025_at_market_1.0174": capacity_term_per_kw("coal", 1.0174, 2025),
            "2025_at_d31_dates_off_1.0571": capacity_term_per_kw("coal", 1.0571, 2025),
        },
        "H_FLOOR_frac_of_miss": h_floor / 1000.0 / MISS_GW,
        "H_BAR_frac_of_miss": h_bar / 1000.0 / MISS_GW,
        "H_WALL_frac_of_miss": h_wall / 1000.0 / MISS_GW,
        "model_exits_by_channel_mw": dict(model_exits),
        "market_capacity_price_kw_yr": market,
    }
    print("\n== decomposition against the 7.570 GW miss")
    for k, v in decomposition.items():
        if isinstance(v, float):
            print(f"  {k:40s} {v:.3f}")
    print("  (H_FLOOR and H_BAR are the same MW read in different years — 2022/23 vs 2024/25 — so they are not additive; H_WALL is the within-band MW in any year.)")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "positions": positions, "cap_terms": cap_terms, "census": census,
            "dated_plants_n": len(dated_plants), "cohort": cohort_rows, "decomposition": decomposition,
        }, indent=1, default=float))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
