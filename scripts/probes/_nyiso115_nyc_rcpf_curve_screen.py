"""nyiso-115 EX-ANTE screen: is the NYC locational RCPF demand curve the published one?

Task 1 of the nyiso-115 brief. nyiso-114's per-family reserve-dual sidecar
(``hourly/reserve_family_<year>.parquet``) showed that NYISO's binding reserve
constraint is overwhelmingly the **NYC locational pair** — ``nyc_10min_total``
priced in 17/6/29 hours of 2023/24/25 and ``nyc_30min_total`` in 8/6/10 — with
LARGE shortfalls (max 307/358/317 MW against a 500 MW requirement) clearing at
SMALL duals ($15.63/$18.75). That is a rule 14 ``[R-ACCURATE]`` question about a
MEASURED input — does ``NYISO_RCPF_LOCATIONAL`` reproduce the published NYC
Reserve Capacity Penalty Factors? — and it is answerable WITHOUT a solve.

The screen, run entirely on already-committed artifacts:

* **The measured side** is ``data/raw/NYISO-AS/NYISO_as_da_<year>.csv`` — NYISO's
  own posted Day-Ahead ancillary-service clearing prices, **per zone** and per
  product (``spin_10``, ``nonsync_10``, ``op_30``). Because NYISO's locational
  reserve regions NEST (NYCA ⊃ East ⊃ SENY ⊃ NYC), the difference between zone
  J (``N.Y.C.``) and any zone that shares every region EXCEPT NYC isolates the
  **NYC-only** locational shadow price. Zones H/I/G (``MILLWD``/``DUNWOD``/
  ``HUD VL``) are exactly those references: all in SENY, none in NYC. Using
  three independent references makes the isolation falsifiable rather than
  assumed — they must agree, and a zone OUTSIDE SENY (``CAPITL``, ``WEST``)
  must NOT.

* **The model side** is ``reserve_family_<year>.parquet`` from
  ``results/calibration/nyiso114_lilocational_confirm`` — the nyiso-114
  reference bundle (the keeper RECIPE re-solved; per FINDING-nyiso114 §2 the
  keeper itself carries no sidecar and cannot be faithfully backfilled).

Two questions are separable and are reported separately, because they have
different answers:

1. **LEVEL** — is the max penalty right? A single-step curve's ceiling is
   observable directly as the maximum of the isolated adder.
2. **SHAPE** — is the curve a linear ramp (the model:
   ``critical_mw = 0``, so ``nyiso_rcpf_product_shortfall_steps`` builds an
   ``n_ramp=8`` ladder $3.125 … $25.00 over the whole 500 MW) or a single step
   (any shortage prices at the full RCPF)? These are distinguishable in the
   measured distribution WITHOUT knowing NYISO's clearing engine: a ramp puts
   ATOMS at its interior rungs, a step puts one atom at the ceiling and leaves
   everything below it a smooth opportunity-cost continuum.

Nothing here is fitted and nothing is tuned to a residual: the output is a
comparison of a model input against the market's own posted prices for the same
quantity (rule 13 ``[R-MEASURED]`` — the published RCPF regenerates for any
forward year, which is why it is admissible as an input at all).

Run:
    PYTHONPATH=.:src python scripts/probes/_nyiso115_nyc_rcpf_curve_screen.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

# NYISO load zones sharing every nested locational region with zone J EXCEPT
# NYC itself (all in SENY ⊂ East ⊂ NYCA), so J-minus-reference isolates the
# NYC-only locational shadow price. Three of them, so the isolation is checked
# rather than assumed.
SENY_REFERENCE_ZONES = ("DUNWOD", "MILLWD", "HUD VL")
# Zones OUTSIDE SENY: the same difference must pick up the SENY component too,
# which is the negative control on the isolation.
NON_SENY_ZONES = ("CAPITL", "WEST")
NYC_ZONE = "N.Y.C."

YEARS = (2023, 2024, 2025)

# The model's own construction, restated here so the screen is self-contained:
# reserves/spec.py NYISO_RCPF_LOCATIONAL["NYC"] carries (req, critical, penalty)
# = (500, 0, 25) for nyc_10min_total and (1000, 0, 25) for nyc_30min_total, and
# results/scarcity.py::nyiso_rcpf_product_shortfall_steps discretizes the
# critical=0 linear ramp into n_ramp=8 equal-width bands whose penalties are
# max_penalty*(k+1)/n_ramp — REQUIREMENT-INDEPENDENT, so both NYC families share
# one rung ladder.
MODEL_MAX_PENALTY = 25.0
MODEL_N_RAMP = 8
MODEL_RUNGS = tuple(MODEL_MAX_PENALTY * (k + 1) / MODEL_N_RAMP for k in range(MODEL_N_RAMP))

REFERENCE_BUNDLE = "results/calibration/nyiso114_lilocational_confirm"

# Below this the isolated adder is dominated by ordinary opportunity-cost
# differences between the marginal reserve providers in the two zones; the
# shape question is only asked of material values.
MATERIAL_ADDER = 2.0
ATOM_TOL = 0.01


def _load_as_prices(year: int) -> pd.DataFrame:
    """Pivot one year of NYISO posted DA ancillary-service prices to zone columns."""
    path = REPO_ROOT / "data" / "raw" / "NYISO-AS" / f"NYISO_as_da_{year}.csv"
    raw = pd.read_csv(path)
    raw["Time Stamp"] = pd.to_datetime(raw["Time Stamp"])
    return raw.pivot_table(
        index="Time Stamp",
        columns="Name",
        values=["spin_10", "nonsync_10", "op_30"],
        aggfunc="mean",
    )


def _isolated_adder(pivot: pd.DataFrame, product: str, reference: str) -> pd.Series:
    """NYC-minus-reference price for one product: the NYC-only locational adder."""
    return (pivot[(product, NYC_ZONE)] - pivot[(product, reference)]).dropna()


def _shape_evidence(adder: pd.Series, ceiling: float) -> dict:
    """Distinguish a stepped demand curve from a linear ramp in one adder series.

    A single-step curve prices EVERY shortage at the full RCPF, so the measured
    distribution is a smooth opportunity-cost continuum below the ceiling plus a
    single ATOM exactly at it. An n_ramp linear ramp instead places atoms at each
    interior rung. Counting mass at the model's own rungs is therefore a direct
    test of the model's construction against the market's posted prices.
    """
    material = adder[adder > MATERIAL_ADDER]
    at_ceiling = int(np.isclose(material, ceiling, atol=ATOM_TOL).sum())
    interior = [r for r in MODEL_RUNGS if r < MODEL_MAX_PENALTY - ATOM_TOL]
    at_interior_rungs = int(
        sum(np.isclose(material, rung, atol=ATOM_TOL).sum() for rung in interior)
    )
    sub = material[material < ceiling - ATOM_TOL]
    return {
        "material_hours": int(len(material)),
        "hours_at_ceiling": at_ceiling,
        "hours_at_model_interior_rungs": at_interior_rungs,
        "model_interior_rungs": [round(r, 4) for r in interior],
        "distinct_values_below_ceiling": int(sub.round(2).nunique()),
        "sub_ceiling_quantiles": (
            [round(float(v), 2) for v in np.percentile(sub, [50, 75, 90, 99])]
            if len(sub)
            else None
        ),
        "max": round(float(adder.max()), 4),
        "hours_above_ceiling": int((adder > ceiling + ATOM_TOL).sum()),
    }


def screen_measured() -> dict:
    """Run the whole measured-side screen across all three training years."""
    out: dict = {}
    for year in YEARS:
        pivot = _load_as_prices(year)
        year_out: dict = {"reference_zone_agreement": {}, "products": {}}

        # (a) Isolation control: the three SENY references must agree, and the
        #     two non-SENY zones must not (they carry the SENY component too).
        for zone in SENY_REFERENCE_ZONES + NON_SENY_ZONES:
            adder = _isolated_adder(pivot, "op_30", zone)
            year_out["reference_zone_agreement"][zone] = {
                "in_seny": zone in SENY_REFERENCE_ZONES,
                "max": round(float(adder.max()), 4),
                "hours_at_25": int(np.isclose(adder, 25.0, atol=ATOM_TOL).sum()),
                "hours_above_25": int((adder > 25.0 + ATOM_TOL).sum()),
            }

        # (b) The two published NYC products. op_30 sees the NYC 30-minute
        #     family alone; nonsync_10 sees the 10-minute family STACKED on the
        #     30-minute one, because a 10-minute reserve also satisfies the
        #     30-minute requirement — so its ceiling is the SUM of the two RCPFs.
        ref = SENY_REFERENCE_ZONES[0]
        a30 = _isolated_adder(pivot, "op_30", ref)
        a10 = _isolated_adder(pivot, "nonsync_10", ref)
        year_out["products"]["nyc_30min_total"] = _shape_evidence(a30, 25.0)
        year_out["products"]["nyc_10min_total_stacked"] = _shape_evidence(a10, 50.0)

        # (c) The stacking itself, verified rather than asserted: every hour in
        #     which the 10-minute adder sits at $50 must be an hour in which the
        #     30-minute adder sits at $25.
        joint = pd.concat([a10.rename("a10"), a30.rename("a30")], axis=1).dropna()
        at50 = joint[np.isclose(joint["a10"], 50.0, atol=ATOM_TOL)]
        at25 = joint[np.isclose(joint["a10"], 25.0, atol=ATOM_TOL)]
        year_out["stacking_check"] = {
            "hours_a10_at_50": int(len(at50)),
            "of_which_a30_at_25": int(np.isclose(at50["a30"], 25.0, atol=ATOM_TOL).sum()),
            "hours_a10_at_25": int(len(at25)),
            "of_which_a30_at_0": int((at25["a30"].abs() < ATOM_TOL).sum()),
        }

        # (d) Is there a NYC locational SPINNING family the model omits? ASM §6.8
        #     item 2 prices "Eastern, Southeastern, New York City, or Long Island
        #     Spinning Reserves" at $40/MW. spin_10 minus nonsync_10 removes every
        #     10-min-TOTAL family, leaving only spin-specific requirements; doing
        #     that in NYC and upstate and differencing isolates a NYC-only spin
        #     RCPF, which would show a $40 atom if such a family were enforced.
        nyc_spin_only = pivot[("spin_10", NYC_ZONE)] - pivot[("nonsync_10", NYC_ZONE)]
        ref_spin_only = pivot[("spin_10", "WEST")] - pivot[("nonsync_10", "WEST")]
        loc_spin = (nyc_spin_only - ref_spin_only).dropna()
        year_out["nyc_spin_family_probe"] = {
            "max": round(float(loc_spin.max()), 4),
            "hours_positive": int((loc_spin > ATOM_TOL).sum()),
            "hours_at_40": int(np.isclose(loc_spin, 40.0, atol=ATOM_TOL).sum()),
        }
        out[str(year)] = year_out
    return out


def screen_model() -> dict:
    """The model's own NYC family duals, from the nyiso-114 reference bundle."""
    root = REPO_ROOT / REFERENCE_BUNDLE / "hourly"
    out: dict = {}
    for year in YEARS:
        path = root / f"reserve_family_{year}.parquet"
        if not path.exists():
            out[str(year)] = {"error": f"missing {path}"}
            continue
        df = pd.read_parquet(path)
        year_out: dict = {}
        for family, ceiling in (("nyc_10min_total", 25.0), ("nyc_30min_total", 25.0)):
            fam = df[df["family"].astype(str) == family]
            live = fam[fam["dual"] > 1e-9]
            year_out[family] = {
                "hours_dual_positive": int(len(live)),
                "max_dual": round(float(fam["dual"].max()), 4),
                "published_rcpf": ceiling,
                "hours_at_published_rcpf": int(
                    np.isclose(fam["dual"], ceiling, atol=ATOM_TOL).sum()
                ),
                "max_shortfall_mw": round(float(fam["shortfall_mw"].max()), 2),
                "requirement_mw": round(float(fam["requirement_mw"].max()), 2),
                # What a single-step curve would have charged in exactly the
                # hours the model already prices — the LEVEL gap, with the set of
                # binding hours held fixed (a step and a ramp are both $0 at or
                # above the requirement, so they bind in the SAME hours).
                "mean_dual_when_binding": (
                    round(float(live["dual"].mean()), 4) if len(live) else None
                ),
                "step_curve_would_charge": ceiling,
                "underprice_factor": (
                    round(ceiling / float(live["dual"].mean()), 3)
                    if len(live) and live["dual"].mean() > 0
                    else None
                ),
            }
        out[str(year)] = year_out
    return out


def main() -> None:
    result = {
        "probe": "nyiso-115 NYC locational RCPF curve screen",
        "measured_source": "data/raw/NYISO-AS/NYISO_as_da_<year>.csv (NYISO posted DA AS prices, per zone)",
        "model_source": f"{REFERENCE_BUNDLE}/hourly/reserve_family_<year>.parquet",
        "model_construction": {
            "max_penalty": MODEL_MAX_PENALTY,
            "critical_mw": 0.0,
            "n_ramp": MODEL_N_RAMP,
            "rungs": [round(r, 4) for r in MODEL_RUNGS],
        },
        "measured": screen_measured(),
        "model": screen_model(),
    }
    out_path = (
        REPO_ROOT / "results" / "calibration" / "nyiso115_nyc_rcpf_curve_screen.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
