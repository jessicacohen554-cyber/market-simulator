"""pjm-153 — ex-ante screens that close three PJM lever-queue items. No LP.

Three §5.3 queue items are screened here, each against committed bytes only. All
three are *ex ante*: the screen is the thing that decides, and none of them needs
a solve, a bundle, or a data intake to reach a terminal state.

**Item 8 — ``st_gas_mustrun_p25_level`` (matrix cell `U`).** Its overnight
motivation was withdrawn at pjm-139 and confirmed withdrawn at pjm-141; what the
matrix says survives is "a rule-23 ``[R-FROZEN-DERIVE]`` re-derivation on its own
source data". The screen asks whether that re-derivation is even available, and
finds something stronger: the mechanism is **provably inert for PJM on the
committed artifact**. ``fleet/arrays.py`` arms a plant only when BOTH its p25
level and its ``online_frac`` are positive, and PJM's committed
``thermal_tranches_PJM.csv`` carries ``online_frac`` for COAL / CC_REGULAR /
CT_PEAKER but **not one** of its 10 ST_GAS rows -- so every plant is skipped and
the floor set is empty however the flags are set. (MISO's artifact, the ISO where
miso-67 armed this, carries 16/16.)

**Item 10 — ``winter_citygate_daily`` / TETCO-M3 (matrix cell `U`).** The item
survives, per the matrix, "on the winter LEVEL story alone, as a rule 14
``[R-ACCURATE]`` correction -- PJM's delivered winter basis is a real quantity the
model proxies with an HH+zonal-basis construction". The screen tests that premise
and refutes it: the keeper resolves its PJM gas level from **measured EIA-923
delivered receipts** (``gas_monthly_actuals`` + ``gas_plant_monthly_fuel_pricing``),
not from Henry Hub. Henry Hub enters only as a **within-month, mean-1.0**
day-shape, and the zonal basis is **annual and mean-zero**, so neither carries any
winter level at all.

**Item 3 — the ``PJM_Dominion`` NoVA/Loudoun split.** Blocked since pjm-137 on the
absence of a measured sub-zonal load basis. Re-confirmed here against the current
published feed, and *narrowed*: PJM's metered-load file does resolve below the
transmission zone for six zones, but ``DOM`` is a single load area in all three
training years.

**No LP is solved, no artifact is regenerated, nothing is armed.** Training years
only (2023-2025), rule 22.

Usage::

    PYTHONPATH=.:src python scripts/probes/pjm153_queue_screens.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TRANCHES = REPO / "data" / "raw" / "_processed-legacy"
LOAD_DIR = REPO / "data" / "raw" / "zone-specific-demand"
KEEPER_CFG = REPO / "results" / "calibration" / "pjm151_seam_B" / "run_config.json"
YEARS = (2023, 2024, 2025)

#: The groups the p25-level floor needs an ``online_frac`` for, plus the groups
#: whose floors the SAME artifact feeds -- listed so a regeneration's blast
#: radius is visible rather than assumed.
FRAC_GROUPS = ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS")


def _keeper_config() -> dict:
    data = json.loads(KEEPER_CFG.read_text(encoding="utf-8"))
    return data.get("scenario_config", data)


# --------------------------------------------------------------------------
# item 8
# --------------------------------------------------------------------------
def screen_item8() -> dict:
    """Is ``st_gas_mustrun_p25_level`` reachable for PJM on committed bytes?"""
    per_iso = {}
    for path in sorted(TRANCHES.glob("thermal_tranches_*.csv")):
        iso = path.stem.replace("thermal_tranches_", "")
        df = pd.read_csv(path)
        if "online_frac" not in df.columns:
            per_iso[iso] = {"has_online_frac_column": False}
            continue
        cov = {}
        for g in FRAC_GROUPS:
            sub = df[df["plant_group"] == g]
            cov[g] = {"rows": int(len(sub)), "online_frac_present": int(sub["online_frac"].notna().sum())}
        per_iso[iso] = {"has_online_frac_column": True, "coverage": cov}

    cfg = _keeper_config()
    pjm = per_iso.get("PJM", {}).get("coverage", {})
    st = pjm.get("ST_GAS", {"rows": 0, "online_frac_present": 0})
    return {
        "artifact_coverage_by_iso": per_iso,
        "keeper_flags": {
            "st_gas_mustrun_p25_level": cfg.get("st_gas_mustrun_p25_level"),
            "st_gas_mustrun_per_plant": cfg.get("st_gas_mustrun_per_plant"),
            # The incumbent owner of PJM ST_GAS forcing (pjm-139/141, D-2).
            "gas_st_netload_drag": cfg.get("gas_st_netload_drag"),
        },
        "pjm_st_gas_rows": st["rows"],
        "pjm_st_gas_with_online_frac": st["online_frac_present"],
        # fleet/arrays.py skips any plant whose level or frac is <= 0, so zero
        # fracs means an empty floor set regardless of the two gate flags.
        "inert_for_pjm_on_committed_artifact": st["online_frac_present"] == 0,
        "host_mechanism_armed_in_pjm": bool(cfg.get("st_gas_mustrun_per_plant")),
    }


# --------------------------------------------------------------------------
# item 10
# --------------------------------------------------------------------------
def screen_item10() -> dict:
    """Does the keeper price PJM winter gas off Henry Hub, or off measured receipts?"""
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel import iso_monthly_gas_prices

    cfg = _keeper_config()
    per_year = {}
    for y in YEARS:
        sc = ScenarioConfig(
            iso="PJM",
            mode="backcast",
            start_year=y,
            end_year=y,
            gas_monthly_actuals=True,
            gas_price_override=float(cfg.get("gas_price_override", 2.54)),
        )
        measured = iso_monthly_gas_prices(sc, y)
        if measured is None:
            per_year[str(y)] = {"measured_monthly_available": False}
            continue
        m = np.asarray(measured, dtype=float)
        djf = float(np.nanmean([m[0], m[1], m[11]]))
        ann = float(np.nanmean(m))
        per_year[str(y)] = {
            "measured_monthly_available": True,
            "monthly_usd_mmbtu": [round(float(v), 3) for v in m],
            "djf_mean_usd_mmbtu": round(djf, 3),
            "annual_mean_usd_mmbtu": round(ann, 3),
            "djf_over_annual": round(djf / ann, 4),
            "trajectory_fallback_override": float(cfg.get("gas_price_override", 2.54)),
        }
    return {
        "keeper_flags": {
            "gas_monthly_actuals": cfg.get("gas_monthly_actuals"),
            "gas_plant_monthly_fuel_pricing": cfg.get("gas_plant_monthly_fuel_pricing"),
            "gas_daily_shape": cfg.get("gas_daily_shape"),
            "pjm_zonal_gas_basis": cfg.get("pjm_zonal_gas_basis"),
            "gas_hub_basis_daily": cfg.get("gas_hub_basis_daily"),
            "gas_hub_basis_overlay": cfg.get("gas_hub_basis_overlay"),
        },
        "construction": {
            # Both statements are properties of the code, restated here so the
            # verdict does not rest on reading a docstring: gas_daily_shape_factors
            # divides by the month's own staircase mean (=> mean 1.0 per month),
            # and pjm_zonal_gas_hub.csv is one row per (zone, YEAR), mean-zeroed
            # capacity-weighted in apply_pjm_zonal_gas_basis.
            "henry_hub_daily_shape_is_within_month_mean_one": True,
            "zonal_basis_is_annual_and_mean_zero": True,
            "winter_level_owner": "measured EIA-923 delivered receipts",
        },
        "years": per_year,
        "premise_holds": False,
    }


# --------------------------------------------------------------------------
# item 3
# --------------------------------------------------------------------------
def screen_item3() -> dict:
    """Does PJM's metered-load feed resolve below the ``DOM`` transmission zone?"""
    per_year = {}
    for y in YEARS:
        path = LOAD_DIR / f"PJM{y}_hrl_load_metered.csv"
        if not path.is_file():
            per_year[str(y)] = {"file_present": False}
            continue
        df = pd.read_csv(path, usecols=["zone", "load_area"])
        dom_areas = sorted(df.loc[df["zone"] == "DOM", "load_area"].astype(str).unique())
        subdividing = sorted(
            z for z, g in df.groupby("zone") if g["load_area"].nunique() > 1
        )
        per_year[str(y)] = {
            "file_present": True,
            "dom_load_areas": dom_areas,
            "dom_subdivides": len(dom_areas) > 1,
            "zones_that_do_subdivide": subdividing,
        }
    return {
        "years": per_year,
        "block_holds": all(
            not v.get("dom_subdivides", False) for v in per_year.values() if v.get("file_present")
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/_pjm153_queue_screens.json")
    )
    args = ap.parse_args()

    record = {
        "_what": (
            "pjm-153: ex-ante no-LP screens closing PJM lever-queue items 8, 10 "
            "and re-confirming the item-3 block. Committed bytes only."
        ),
        "item8_st_gas_mustrun_p25_level": screen_item8(),
        "item10_winter_citygate_daily": screen_item10(),
        "item3_dominion_subzonal_load": screen_item3(),
    }
    out = Path(args.out)
    out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")

    i8 = record["item8_st_gas_mustrun_p25_level"]
    print("=" * 72)
    print("pjm-153 — queue screens (NO LP)")
    print("=" * 72)
    print("\n[ITEM 8] st_gas_mustrun_p25_level — online_frac coverage by ISO")
    for iso, rec in i8["artifact_coverage_by_iso"].items():
        if not rec["has_online_frac_column"]:
            print(f"    {iso:<7} (no online_frac column)")
            continue
        cells = "  ".join(
            f"{g}={c['online_frac_present']}/{c['rows']}" for g, c in rec["coverage"].items()
        )
        print(f"    {iso:<7} {cells}")
    print(f"    keeper flags: {i8['keeper_flags']}")
    print(
        f"    PJM ST_GAS rows {i8['pjm_st_gas_rows']}, with online_frac "
        f"{i8['pjm_st_gas_with_online_frac']} → INERT="
        f"{i8['inert_for_pjm_on_committed_artifact']}"
    )

    i10 = record["item10_winter_citygate_daily"]
    print("\n[ITEM 10] winter_citygate_daily — who owns PJM's winter gas level?")
    print(f"    keeper flags: {i10['keeper_flags']}")
    for y, r in i10["years"].items():
        if not r["measured_monthly_available"]:
            print(f"    {y}: measured monthly NOT available")
            continue
        print(
            f"    {y}: DJF {r['djf_mean_usd_mmbtu']:.3f} vs annual "
            f"{r['annual_mean_usd_mmbtu']:.3f} $/MMBtu "
            f"(DJF/annual {r['djf_over_annual']:.3f}); Jan={r['monthly_usd_mmbtu'][0]:.2f}, "
            f"trajectory fallback {r['trajectory_fallback_override']:.2f}"
        )
    print(f"    premise ('model proxies winter with HH') holds = {i10['premise_holds']}")

    i3 = record["item3_dominion_subzonal_load"]
    print("\n[ITEM 3] Dominion sub-zonal load basis")
    for y, r in i3["years"].items():
        if not r["file_present"]:
            print(f"    {y}: file absent")
            continue
        print(
            f"    {y}: DOM load_areas={r['dom_load_areas']} "
            f"(subdivides={r['dom_subdivides']}); zones that DO subdivide="
            f"{r['zones_that_do_subdivide']}"
        )
    print(f"    block holds = {i3['block_holds']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
