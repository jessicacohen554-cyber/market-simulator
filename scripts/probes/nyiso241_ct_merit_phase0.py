"""NYISO lane phase 0 (zero LP): decompose the CT_PEAKER merit collapse from 2023.

Rule 29 `[R-SCREEN]` clause (0): an offer-array / committed-sidecar decomposition costs
~seconds and answers more than a solve. The object handed to session nyiso-241 is the
CT_PEAKER energy collapse that survived the nyiso-240 benchmark repairs:

    model CT_PEAKER TWh   2.429 / 0.246 / 0.300 / 0.771
    actual                2.829 / 2.114 / 1.911 / 2.812

with model CT capacity intact (~2,000 MW peak every year), so the cause is merit order,
not availability (docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md §7).

This probe reads only COMMITTED artifacts — the four nyiso-240 MER legs, whose
``dispatch/<yr>_P1.parquet`` are sha256-identical to the keeper's — and answers:

  Q1  Where does each class's offer (LP ``mc``) sit, year by year, and what is the
      CT_PEAKER-vs-ST_GAS / CC_REGULAR spread in $/MWh?
  Q2  Does the spread collapse across the 2022→2023 boundary the way the gas price does,
      i.e. is the model's CT displacement the arithmetic consequence of a multiplicative
      band applied to a falling fuel price?
  Q3  How many hours does the zonal LMP clear each class's cheapest offer — the merit
      position that decides dispatch — and does that reproduce the observed hour counts?
  Q4  Counterfactual, arithmetic only: re-price the CT_PEAKER ``committed`` band at
      NYISO's own measured ``phys_committed`` 0.843 in place of the transferred 1.35 and
      re-read Q3's hour counts. NO LP IS SOLVED and nothing is swept — this is a bound on
      the lever's reach, not a selection of it (rule 1 `[R-STRUCT]` (c)).

Usage:
    python3 scripts/probes/nyiso241_ct_merit_phase0.py \
        --legs results/calibration/nyiso_mer_2026-09-19_{2022,2023,2024,2025} \
        --out results/calibration/_nyiso241_ct_merit_phase0.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# The four fossil classes the object spans. CT_PEAKER is the class that collapses;
# ST_GAS and CC_REGULAR carry the two C1 rows still inside half a band.
FOSSIL_CLASSES = ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP")

# The registered band multiplier and NYISO's own measured counterpart, both read from
# `pipeline/backcast_config._NYISO_OFFER_CURVE["CT_PEAKER"]`. Quoted here so the
# counterfactual in Q4 carries no literal of its own (rule 21 `[R-DOF]`).
CT_COMMITTED_REGISTERED = 1.35
CT_COMMITTED_MEASURED = 0.843


def _year_of(leg: Path) -> int:
    """Return the four-digit year a per-year leg bundle name ends with."""
    return int(leg.name.rsplit("_", 1)[-1])


def _load_unit_hourly(leg: Path, year: int) -> pd.DataFrame:
    """Load the leg's per-unit hourly dispatch (mw, cap_mw, mc) for the P1 pass."""
    path = leg / "hourly" / f"unit_hourly_{year}.parquet"
    df = pd.read_parquet(
        path,
        columns=[
            "pass",
            "unit_id",
            "plant_code",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    return df[df["pass"] == "P1"]


def _load_system(leg: Path, year: int) -> pd.DataFrame:
    """Load the leg's per-zone hourly system sidecar (price, load)."""
    return pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")


def offer_position(unit: pd.DataFrame) -> dict:
    """Per-class offer statistics, capacity-weighted where a weight is meaningful.

    `mc` is the LP's own marginal cost for the row, i.e. the offer the merit order sorts
    on. The cheapest row of a class is what decides whether the class enters at all.
    """
    out: dict[str, dict] = {}
    for klass in FOSSIL_CLASSES:
        sub = unit[unit["plant_group"] == klass]
        if sub.empty:
            continue
        mc = sub["mc"].to_numpy()
        cap = sub["cap_mw"].to_numpy()
        # Capacity-weighted median offer: sort by mc, take the 50 % capacity crossing.
        order = np.argsort(mc)
        mc_s, cap_s = mc[order], cap[order]
        cum = np.cumsum(cap_s)
        p50 = (
            float(mc_s[np.searchsorted(cum, cum[-1] * 0.5)])
            if cum[-1] > 0
            else float("nan")
        )
        out[klass] = {
            "rows": int(sub["unit_id"].nunique()),
            "cap_mw": float(sub.groupby("unit_id")["cap_mw"].max().sum()),
            "mc_min": float(np.min(mc)),
            "mc_p05": float(np.percentile(mc, 5)),
            "mc_p50_capwt": p50,
            "mc_p50": float(np.percentile(mc, 50)),
            "mc_p95": float(np.percentile(mc, 95)),
            "mc_max": float(np.max(mc)),
        }
    return out


def clearing_hours(unit: pd.DataFrame, system: pd.DataFrame) -> dict:
    """For each class, the hours its cheapest offer is at or below its zone's LMP.

    This is the merit position that decides entry: a class whose cheapest row never
    clears never dispatches, whatever its capacity. Measured per zone-hour and summed
    over the class's own zones, so a locational class is not credited with another
    zone's price.
    """
    price_col = "price" if "price" in system.columns else "lmp"
    prices = system[["zone", "hour", price_col]].rename(columns={price_col: "price"})
    out: dict[str, dict] = {}
    for klass in FOSSIL_CLASSES:
        sub = unit[unit["plant_group"] == klass]
        if sub.empty:
            continue
        # Cheapest offer per zone-hour for this class.
        cheapest = sub.groupby(["zone", "hour"], as_index=False)["mc"].min()
        joined = cheapest.merge(prices, on=["zone", "hour"], how="inner")
        clears = joined["price"] >= joined["mc"]
        # Hours the class actually produced, for the like-for-like comparison.
        produced = sub.groupby("hour")["mw"].sum()
        out[klass] = {
            "zone_hours": int(len(joined)),
            "zone_hours_cheapest_clears": int(clears.sum()),
            "clear_share": float(clears.mean()) if len(joined) else float("nan"),
            "hours_gt_1mw": int((produced > 1.0).sum()),
            "twh": float(produced.sum() / 1e6),
            "mean_mw_when_on": float(produced[produced > 1.0].mean())
            if (produced > 1.0).any()
            else 0.0,
            "peak_mw": float(produced.max()),
        }
    return out


def ct_committed_counterfactual(unit: pd.DataFrame, system: pd.DataFrame) -> dict:
    """Arithmetic bound on grounding CT_PEAKER `committed` on NYISO's own 0.843.

    The band multiplies the class's heat rate, so the offer scales with it: an offer
    written at 1.35 re-prices to `mc * 0.843 / 1.35` at the measured basis. This is a
    BOUND on the merit-position change, NOT a dispatch prediction — the LP re-solves the
    whole stack and nothing here is swept against any gate (rule 1 `[R-STRUCT]` (c)).
    """
    ratio = CT_COMMITTED_MEASURED / CT_COMMITTED_REGISTERED
    price_col = "price" if "price" in system.columns else "lmp"
    prices = system[["zone", "hour", price_col]].rename(columns={price_col: "price"})
    sub = unit[unit["plant_group"] == "CT_PEAKER"]
    if sub.empty:
        return {}
    cheapest = sub.groupby(["zone", "hour"], as_index=False)["mc"].min()
    joined = cheapest.merge(prices, on=["zone", "hour"], how="inner")
    return {
        "band_ratio": ratio,
        "zone_hours": int(len(joined)),
        "clears_at_registered": int((joined["price"] >= joined["mc"]).sum()),
        "clears_at_measured": int((joined["price"] >= joined["mc"] * ratio).sum()),
        "mean_offer_registered": float(joined["mc"].mean()),
        "mean_offer_measured": float((joined["mc"] * ratio).mean()),
        "mean_offer_drop": float(joined["mc"].mean() * (1.0 - ratio)),
    }


def main() -> None:
    """Run the four phase-0 questions over each committed per-year leg."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True, help="per-year leg bundle dirs")
    ap.add_argument("--out", required=True, help="JSON output path")
    args = ap.parse_args()

    report: dict[str, dict] = {}
    for leg_str in args.legs:
        leg = Path(leg_str)
        year = _year_of(leg)
        unit = _load_unit_hourly(leg, year)
        system = _load_system(leg, year)
        report[str(year)] = {
            "offer_position": offer_position(unit),
            "clearing": clearing_hours(unit, system),
            "ct_counterfactual": ct_committed_counterfactual(unit, system),
        }
        print(f"--- {year} ---")
        for klass, row in report[str(year)]["offer_position"].items():
            clr = report[str(year)]["clearing"].get(klass, {})
            print(
                f"  {klass:<12} rows {row['rows']:>4} cap {row['cap_mw']:>8.1f} MW | "
                f"mc min {row['mc_min']:>7.2f} p50cw {row['mc_p50_capwt']:>7.2f} "
                f"p95 {row['mc_p95']:>8.2f} | clears {clr.get('clear_share', float('nan')):.3f} "
                f"| {clr.get('twh', float('nan')):.3f} TWh, {clr.get('hours_gt_1mw', 0)} h"
            )
        cf = report[str(year)]["ct_counterfactual"]
        if cf:
            print(
                f"  CT counterfactual: offer {cf['mean_offer_registered']:.2f} -> "
                f"{cf['mean_offer_measured']:.2f} $/MWh; zone-hours clearing "
                f"{cf['clears_at_registered']} -> {cf['clears_at_measured']}"
            )

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
