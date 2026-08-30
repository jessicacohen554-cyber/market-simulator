"""miso-191 phase-0 (ZERO-SOLVE): binning-aware partial-plant exit timing — the
form choice's measured basis and the frozen witness ceilings.

The FINDING-miso190 §4 named successor, granted by the miso-191 handoff.
Computed BEFORE the PREREG and before any mechanism code exists; committed
sources only, no LP, no solve. Everything here regenerates from committed
parquets + the committed miso-190 census (`_miso190_partial_exit_phase0.json`,
which carries over unchanged per FINDING-miso190 §4).

What it measures:

1. **Witness ceilings (plant grain, frozen for PREREG-miso191 S-1).** For each
   witness plant, the committed operable snapshot's surviving same-technology
   capacity (net summer MW, the loader's pmax basis) — the hard plant-grain
   dispatch ceiling that must hold in every post-exit month of the arm. Unit
   ids do not exist in a binned LP (the miso-190 §5.1 vacuous-witness lesson),
   but a plant's post-exit dispatch cannot exceed its surviving capacity
   whatever the delivery mechanism, so these adjudicate form-independently.
2. **Whole-plant staggered-exit census (the scope disclosure).** The successor
   cohort-routes ONLY the leg-1 partial-exit injected units; whole-plant
   retiree-channel plants keep the plant-collapsed COD timing they have in the
   control (both legs identical there). This measures how much timing
   heterogeneity that deliberate non-scope leaves on the table in MISO.
3. **Leg-2 pooling facts.** Which snapshot rows the leg-2 re-carries pool with
   (Warrick 4's operable status; Big Cajun 2's surviving coal), so the re-keyed
   leg-2 witnesses are frozen at the grain that actually exists in the LP.

Output: results/calibration/_miso191_binning_phase0.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_sim.config.paths import active_eia860_dir
from market_sim.data.fleet.models import (
    EIA_860_PARQUET_NAME,
    EIA_860_RETIRED_WINDOW_PARQUET_NAME,
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_miso191_binning_phase0.json"
M190 = REPO / "results" / "calibration" / "_miso190_partial_exit_phase0.json"

MISO_BA = "MISO"

# The partial-exit witness plants (>= 40 MW units, from the committed miso-190
# census) with each unit's actual EIA-860 retirement month. The exited MW is
# restated from that census verbatim — nothing here is re-derived.
WITNESS_PLANTS: dict[int, dict] = {
    994: {"plant": "AES Petersburg", "tech": "coal", "exits": [("ST2", "2023-06", 421.8)]},
    1400: {"plant": "Teche", "tech": "gas_st", "exits": [("3", "2024-06", 250.0)]},
    1702: {
        "plant": "Dan E Karn",
        "tech": "coal",
        "exits": [
            ("1A", "2023-05", 127.5),
            ("1B", "2023-05", 127.5),
            ("2A", "2023-05", 115.5),
            ("2B", "2023-05", 115.5),
        ],
    },
    4014: {
        "plant": "Wheaton",
        "tech": "gas_ct",
        "exits": [
            ("1", "2025-05", 44.0),
            ("2", "2025-05", 51.0),
            ("3", "2025-05", 44.0),
            ("4", "2025-05", 47.0),
        ],
    },
    4041: {
        "plant": "South Oak Creek",
        "tech": "coal",
        "exits": [("5", "2024-05", 242.2), ("6", "2024-05", 253.8)],
    },
    6090: {"plant": "Sherburne County", "tech": "coal", "exits": [("2", "2023-12", 682.0)]},
    6137: {
        "plant": "A B Brown",
        "tech": "coal",
        "exits": [("1", "2023-10", 245.0), ("2", "2023-10", 240.0)],
    },
    8056: {"plant": "Waterford 1 & 2", "tech": "gas_st", "exits": [("1", "2024-03", 409.5)]},
}

# Technology filters at the grain the bins classify (coal steam vs gas steam vs
# gas CT), matching the class prefix the plant's LP unit ids will carry.
TECH_FILTER = {
    "coal": {"Conventional Steam Coal", "Coal Integrated Gasification Combined Cycle"},
    "gas_st": {"Natural Gas Steam Turbine"},
    "gas_ct": {"Natural Gas Fired Combustion Turbine"},
}


def main() -> None:
    d = active_eia860_dir()
    op = pd.read_parquet(d / EIA_860_PARQUET_NAME)
    op = op[op["balancing_authority_code"].astype(str).str.strip() == MISO_BA]
    op = op[op["status"].astype(str).str.strip().str.upper() == "OP"]
    op["plant_id"] = pd.to_numeric(op["plant_id"], errors="coerce").astype("Int64")

    census = json.loads(M190.read_text())

    # 1. Surviving-capacity ceilings per witness plant.
    ceilings: dict[str, dict] = {}
    for pid, spec in WITNESS_PLANTS.items():
        rows = op[op["plant_id"] == pid]
        tech_rows = rows[rows["technology"].isin(TECH_FILTER[spec["tech"]])]
        surviving = [
            {
                "generator_id": str(g).strip(),
                "technology": str(t),
                "net_summer_mw": float(mw),
            }
            for g, t, mw in zip(
                tech_rows["generator_id"],
                tech_rows["technology"],
                tech_rows["net_summer_capacity_mw"],
            )
        ]
        surviving_mw = float(sum(u["net_summer_mw"] for u in surviving))
        first_exit = min(m for _, m, _ in spec["exits"])
        last_exit = max(m for _, m, _ in spec["exits"])
        ceilings[str(pid)] = {
            "plant": spec["plant"],
            "tech": spec["tech"],
            "exited_units": [
                {"generator_id": g, "retirement": m, "net_summer_mw": mw}
                for g, m, mw in spec["exits"]
            ],
            "exited_mw": float(sum(mw for _, _, mw in spec["exits"])),
            "surviving_units": surviving,
            "surviving_same_tech_mw": surviving_mw,
            "first_exit_month": first_exit,
            "last_exit_month": last_exit,
            # The frozen S-1 plant-grain witness: in every month strictly
            # after last_exit_month, the arm's hourly dispatch summed over the
            # plant's same-tech LP units must not exceed this (small epsilon
            # for float noise). Zero where no same-tech unit survives.
            "post_exit_ceiling_mw": surviving_mw,
        }

    # 2. Whole-plant retiree channel: staggered-exit census (the deliberate
    # non-scope of the cohort routing — these plants keep plant-collapsed
    # timing in BOTH legs, unchanged from the keeper).
    wp = pd.read_parquet(d / EIA_860_RETIRED_WINDOW_PARQUET_NAME)
    if "balancing_authority_code" in wp.columns:
        wp = wp[wp["balancing_authority_code"].astype(str).str.strip() == MISO_BA]
    wp["plant_id"] = pd.to_numeric(wp["plant_id"], errors="coerce").astype("Int64")
    wp["ret"] = (
        pd.to_numeric(wp["planned_retirement_year"], errors="coerce").astype("Int64").astype(str)
        + "-"
        + pd.to_numeric(wp["planned_retirement_month"], errors="coerce")
        .astype("Int64")
        .astype(str)
        .str.zfill(2)
    )
    staggered: dict[str, dict] = {}
    for pid, grp in wp.groupby("plant_id"):
        months = sorted(set(grp["ret"]))
        if len(months) > 1:
            staggered[str(int(pid))] = {
                "plant": str(grp["plant_name"].iloc[0]),
                "n_units": int(len(grp)),
                "mw": float(
                    pd.to_numeric(grp["net_summer_capacity_mw"], errors="coerce")
                    .fillna(0.0)
                    .sum()
                ),
                "distinct_exit_months": months,
            }

    # 3. Leg-2 pooling facts: what the OS/SB re-carried units share a bin with.
    leg2_pool: dict[str, dict] = {}
    for pid, label in ((6055, "Big Cajun 2"), (6705, "Warrick")):
        rows = op[op["plant_id"] == pid]
        leg2_pool[str(pid)] = {
            "plant": label,
            "operable_rows": [
                {
                    "generator_id": str(g).strip(),
                    "technology": str(t),
                    "net_summer_mw": float(mw),
                    "status": str(s).strip(),
                }
                for g, t, mw, s in zip(
                    rows["generator_id"],
                    rows["technology"],
                    rows["net_summer_capacity_mw"],
                    rows["status"],
                )
            ],
            "operable_coal_mw": float(
                pd.to_numeric(
                    rows[rows["technology"].isin(TECH_FILTER["coal"])][
                        "net_summer_capacity_mw"
                    ],
                    errors="coerce",
                )
                .fillna(0.0)
                .sum()
            ),
        }

    out = {
        "probe": "_miso191_binning_phase0",
        "charter": "FINDING-miso190 §4 named successor (binning-aware unit-grain "
        "exit timing), granted by the miso-191 handoff",
        "ask_a_verdict_validation": {
            "run_id": "2026-08-30-miso-188-rvsscope",
            "determination": "NOT-YET",
            "failing_criteria": ["C3a-2025 -12.2965%"],
            "c1": "16/16 all / 12/12 free",
            "note": "reproduced zero-solve from committed artifacts this session",
        },
        "form_freeze": {
            "chosen": "a",
            "name": "date-scoped exit-cohort bins per plant x retirement month",
            "reasons": [
                "Rule 19 [R-ONE-MECH]: the COD ramp is THE single COD/exit-timing "
                "mechanism for the whole fleet (arrays.py cod-ramp block); form (a) "
                "delivers unit-grain timing THROUGH it via the existing "
                "effective_cod per-unit-retirement preference (the Homer City "
                "seam), while form (b) would mint a second, parallel exit-timing "
                "channel (a bin-level monthly availability mask) for the same "
                "phenomenon.",
                "Blast radius: form (a) touches only the two fleet-build "
                "functions (fleet_to_bins aggregation key + retirement column "
                "carry; bins_to_fleet retirement stamp + cohort bin id); form (b) "
                "would thread a new mask channel through the vectorized "
                "availability builder where it multiplies into outage overlays, "
                "seasonal derates and min_gen floors.",
                "Fidelity: under (a) the surviving plant's bin aggregates only "
                "surviving units, so its capacity-weighted heat rate and tranche "
                "split are computed on the capacity that actually survives; under "
                "(b) dead capacity stays inside the bin's heat-rate weighting and "
                "tranche percentages forever.",
                "Precedent: the whole-plant retiree channel already validates the "
                "'retiree rows form their own bins and the COD ramp ages them "
                "out' topology in production keepers (Mystic, Grand Tower) — "
                "form (a) is that topology at (plant x exit-month) grain.",
            ],
            "scope": "cohort routing applies ONLY to leg-1 partial-exit injected "
            "units (loader-stamped provenance); whole-plant retiree-channel "
            "plants keep plant-collapsed timing in both legs (identical to the "
            "keeper), and leg-2 OS/SB re-carries keep whole-year vintage scoping "
            "(they behaved in miso-190). Operable-fleet units with ANNOUNCED "
            "future planned retirements are untouched — routing them would "
            "restructure live plants' bins on announcement data, far beyond the "
            "charter.",
        },
        "witness_ceilings": ceilings,
        "wholeplant_staggered_exits_not_in_scope": staggered,
        "leg2_pooling": leg2_pool,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT}")
    for pid, c in ceilings.items():
        print(
            f"  plant {pid} {c['plant']}: exited {c['exited_mw']:.1f} MW "
            f"(last exit {c['last_exit_month']}), surviving same-tech "
            f"{c['surviving_same_tech_mw']:.1f} MW"
        )
    print(f"  whole-plant staggered (non-scope): {len(staggered)} plant(s)")
    for pid, s in staggered.items():
        print(f"    {pid} {s['plant']}: {s['n_units']} units, {s['distinct_exit_months']}")


if __name__ == "__main__":
    main()
