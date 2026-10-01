"""SPP-44 phase 0 (zero-LP): the rule-18 [R-PHYSICS] eligibility census of the
SPP gas commitment bridge on the CONTROL keeper's recipe.

Rebuilds the keeper-2 (spp42_crosswalk_B) LP fleet with ``run_year(fleet_only=True)``
for each year and resolves, per LP row, what the shared detector
(``model.commitment.caiso_ra_mustoffer_min_gen``) would see through
``_ra_bridge_unit_params``: the unit's physical minimum-down time and per-MW
startup cost, the two physics quantities the bridge gates on. A row is
BRIDGE-ELIGIBLE iff it is merchant gas (``gas_cc`` / ``gas_st``, no ``*_CHP``
group), resolves a min-down > 0 and carries a committable startup cost; the
ECONOMIC leg additionally needs min-down >= RA_BRIDGE_ECON_MIN_DOWN_HOURS.
CT rows are reported so the record shows them failing on PHYSICS (1 h min-down),
never on their class name.

Also prints, per eligible plant, the floor level the detector would apply:
min(min_load_frac x PLANT pmax, base-tranche pmax) on both measured bases, so
the PRECOMMIT can state which basis the consumer's denominator is on.

Usage: uv run python docs/handoffs/spp44/census_eligibility.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402
from market_sim.model.commitment import (  # noqa: E402
    RA_BRIDGE_ECON_MIN_DOWN_HOURS,
    _ra_bridge_unit_params,
)

BUNDLE = REPO / "results/calibration/spp42_crosswalk_B"
OUT = REPO / "docs/handoffs/spp44"
PROC = REPO / "data/raw/_processed-legacy"

FUELS = ("gas_cc", "gas_st", "gas_ct")


def main() -> None:
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    unit_stats = pd.read_csv(PROC / "campd_gas_commitment_params_SPP_units.csv")
    plant_stats = pd.read_csv(PROC / "campd_gas_commitment_params_plant_SPP_units.csv")
    class_unit = pd.read_csv(PROC / "campd_gas_commitment_params_SPP.csv").set_index(
        "plant_class"
    )
    class_plant = pd.read_csv(
        PROC / "campd_gas_commitment_params_plant_SPP.csv"
    ).set_index("plant_class")
    pd.set_option("display.width", 250)
    rows = []
    for year in (2023, 2024, 2025):
        kw_y = dict(kw)
        kw_y.update(derived_run_year_inputs(BUNDLE, year))
        r = run_year(
            year,
            "SPP",
            8760,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw_y,
        )
        fleet = r["fleet"]
        fa = r["fleet_arrays"]
        for g, gen in enumerate(fleet):
            if gen.fuel_type not in FUELS:
                continue
            res = _ra_bridge_unit_params(gen, float(fa.heat_rate[g]))
            rows.append(
                {
                    "year": year,
                    "g": g,
                    "unit_id": gen.unit_id,
                    "plant_code": int(gen.plant_code or 0),
                    "name": gen.name,
                    "zone": gen.zone,
                    "plant_group": gen.plant_group,
                    "fuel_type": gen.fuel_type,
                    "is_campd_bin": bool(getattr(gen, "is_campd_bin", False)),
                    "pmax_mw": float(gen.pmax_mw),
                    "heat_rate": float(fa.heat_rate[g]),
                    "startup_cost_per_mw": float(
                        getattr(gen, "startup_cost_per_mw", 0.0) or 0.0
                    ),
                    "unit_min_down": float(getattr(gen, "min_down_hours", 0) or 0),
                    "resolved_min_down": None if res is None else res[0],
                    "resolved_startup": None if res is None else res[1],
                    "chp": gen.plant_group.endswith("_CHP"),
                }
            )
    df = pd.DataFrame(rows)
    df["eligible"] = (
        df["resolved_min_down"].notna()
        & ~df["chp"]
        & df["fuel_type"].isin(["gas_cc", "gas_st"])
    )
    df["econ_eligible"] = df["eligible"] & (
        df["resolved_min_down"].fillna(0) >= RA_BRIDGE_ECON_MIN_DOWN_HOURS
    )
    df["ct_physics_fail"] = (df["fuel_type"] == "gas_ct") & (
        df["resolved_min_down"].fillna(0) < RA_BRIDGE_ECON_MIN_DOWN_HOURS
    )
    df.to_csv(OUT / "eligibility_rows.csv", index=False)

    # Per-year, per-class census.
    print("\n=== rule-18 eligibility census (LP rows on keeper-2's recipe) ===")
    for year, sub in df.groupby("year"):
        print(f"\n--- {year}: {len(sub)} gas rows")
        tab = (
            sub.groupby(["plant_group", "fuel_type"])
            .agg(
                rows=("g", "size"),
                plants=("plant_code", "nunique"),
                mw=("pmax_mw", "sum"),
                eligible_rows=("eligible", "sum"),
                eligible_mw=(
                    "pmax_mw",
                    lambda s: s[sub.loc[s.index, "eligible"]].sum(),
                ),
                econ_rows=("econ_eligible", "sum"),
                min_down_set=(
                    "resolved_min_down",
                    lambda s: sorted(set(s.dropna().tolist())),
                ),
                startup_set=(
                    "resolved_startup",
                    lambda s: sorted(set(round(x, 1) for x in s.dropna().tolist())),
                ),
            )
            .round(1)
        )
        print(tab.to_string())

    # Per-plant floor level on the two measured bases (base tranche cap applies).
    print("\n=== per-plant floor level, eligible plants (keeper-2 2024 fleet) ===")
    sub = df[(df.year == 2024) & df.fuel_type.isin(["gas_cc", "gas_st"]) & ~df.chp]
    plant_pmax = sub.groupby("plant_code")["pmax_mw"].sum()
    base = sub[sub.eligible].groupby("plant_code")["pmax_mw"].sum()
    klass = sub.groupby("plant_code")["plant_group"].first()
    frac_unit = {
        "CC_REGULAR": class_unit.loc["CC_REGULAR", "min_load_frac"],
        "ST_GAS": class_unit.loc["ST_GAS", "min_load_frac"],
    }
    frac_plant = {
        "CC_REGULAR": class_plant.loc["CC_REGULAR", "min_load_frac"],
        "ST_GAS": class_plant.loc["ST_GAS", "min_load_frac"],
    }
    lsl_plant = plant_stats.set_index("plant_code")["lsl_frac"]
    out = []
    for pc in plant_pmax.index:
        k = klass[pc]
        if k not in frac_unit:
            continue
        pp = float(plant_pmax[pc])
        bp = float(base.get(pc, 0.0))
        out.append(
            {
                "plant_code": pc,
                "class": k,
                "plant_pmax": round(pp, 1),
                "base_tranche_pmax": round(bp, 1),
                "base_share": round(bp / pp, 3) if pp else None,
                "floor_unit_basis": round(min(frac_unit[k] * pp, bp), 1),
                "floor_plant_basis": round(min(frac_plant[k] * pp, bp), 1),
                "own_plant_lsl_frac": (
                    round(float(lsl_plant[pc]), 3) if pc in lsl_plant.index else None
                ),
                "eligible": bp > 0,
            }
        )
    pt = pd.DataFrame(out).sort_values(["class", "plant_pmax"], ascending=[True, False])
    pt.to_csv(OUT / "floor_levels_2024.csv", index=False)
    print(pt.to_string(index=False))
    for k in ("CC_REGULAR", "ST_GAS"):
        s = pt[(pt["class"] == k) & pt.eligible]
        print(
            f"{k}: eligible plants {len(s)}, plant MW {s.plant_pmax.sum():.0f}, "
            f"base-tranche MW {s.base_tranche_pmax.sum():.0f}; floor sum unit-basis "
            f"{s.floor_unit_basis.sum():.0f} MW, plant-basis {s.floor_plant_basis.sum():.0f} MW "
            f"(cap binds on {int((s.floor_unit_basis >= s.base_tranche_pmax - 0.05).sum())} / "
            f"{int((s.floor_plant_basis >= s.base_tranche_pmax - 0.05).sum())} plants)"
        )
    print(
        "\nCAMPD coverage: unit-basis artifact plants",
        unit_stats.plant_code.nunique(),
        "; plant-basis artifact plants",
        plant_stats.plant_code.nunique(),
        "; eligible fleet plants (2024)",
        int(pt.eligible.sum()),
        "; eligible plants WITHOUT a CAMPD series:",
        sorted(set(pt[pt.eligible].plant_code) - set(plant_stats.plant_code)),
    )


if __name__ == "__main__":
    main()
