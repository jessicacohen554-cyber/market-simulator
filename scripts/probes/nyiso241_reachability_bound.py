"""nyiso-241 phase 0 (ZERO LP): can ANY offer lever reach the CT_PEAKER object?

The object is ~1.9 TWh/yr of CT_PEAKER energy the model does not make (2023: 0.25 against a
2.11 TWh actual), with capacity intact. The recommended lever is an offer-curve band multiplier,
so before spending an LP this probe asks the question a band multiplier cannot answer for itself:

    Given the keeper's OWN hourly prices, how much energy could the CT fleet make AT BEST as a
    function of the offer it posts?

The bound is deliberately generous — it assumes the fleet runs at FULL available capacity in
every zone-hour its offer clears its own zone's price, with no min-run, no ramp, no start and no
competition for the same MW. Anything the LP does is at or below it. So:

  * if the actual 2.11 TWh sits BELOW the bound at an offer the lever can reach, the lever is
    sized to the object and an LP is worth spending;
  * if the actual sits ABOVE the bound even at an offer of ZERO, then no offer-side lever of any
    magnitude can reproduce the dispatch, and the missing mechanism is on the PRICE side (the
    ledgered C3c tail) or is a commitment/reliability obligation — in which case aiming an offer
    lever at it would be reaching the right number through a mechanism that is not real, which
    rule 1 `[R-STRUCT]` forbids however good the residual looks.

Also reports the delivered fuel price by class and zone, because the anatomy probe found the CT
fleet charged $4.167/MMBtu in 2023 against CC_REGULAR's $2.769 — a premium that is roughly
CONSTANT IN DOLLARS while the commodity falls 68 %, which is what actually reorders the stack.

Reads only committed artifacts (the nyiso-240 MER legs). No LP is solved; nothing is swept.

Usage:
    python3 scripts/probes/nyiso241_reachability_bound.py \
        --legs results/calibration/nyiso_mer_2026-09-19_{2022,2023,2024,2025} \
        --out results/calibration/_nyiso241_reachability_bound.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

# CT_PEAKER energy actually metered, from the committed benchmark the keeper is scored on
# (docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md §7). Quoted as the TARGET the
# bound is read against; no value from it enters any config.
ACTUAL_TWH = {2022: 2.829, 2023: 2.114, 2024: 1.911, 2025: 2.812}

# Offer levels the bound is evaluated at, as a fraction of the class's own posted offer. 1.00 is
# the keeper itself; 0.0 is the unreachable limit where the fleet offers at zero. Declared here
# so the probe reports a CURVE rather than a point anyone could mistake for a proposal.
OFFER_SCALES = (1.00, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.25, 0.00)


def _is_plant_token(tok: str) -> bool:
    """True for the ``p<digits>`` plant segment of an LP row id (``peak`` also starts with p)."""
    return len(tok) > 1 and tok[0] == "p" and tok[1:].isdigit()


def band_of(unit_id: str) -> str:
    """Return the band segment of an LP row id ``<CLASS>_<ZONE>_p<plant>_<band>``."""
    tail = str(unit_id).rsplit("_", 1)[-1]
    return "" if _is_plant_token(tail) else tail


def bound_for_year(leg: Path, year: int) -> dict:
    """Best-case CT_PEAKER energy against its own zone prices, over a curve of offer levels."""
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=[
            "pass",
            "unit_id",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    unit = unit[unit["pass"] == "P1"]
    system = pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")
    price_col = "price" if "price" in system.columns else "lmp"
    prices = system[["zone", "hour", price_col]].rename(columns={price_col: "price"})

    ct = unit[unit["plant_group"] == "CT_PEAKER"].merge(
        prices, on=["zone", "hour"], how="left"
    )
    ct = ct[ct["price"].notna()]

    curve: dict[str, dict] = {}
    for scale in OFFER_SCALES:
        clears = ct["price"] >= ct["mc"] * scale
        # `cap_mw` is the row's available capacity in that hour, so summing it over the clearing
        # rows is the fleet running flat out wherever it is in the money.
        twh = float(ct.loc[clears, "cap_mw"].sum() / 1e6)
        curve[f"{scale:.2f}"] = {
            "energy_twh_upper_bound": twh,
            "row_hours_clearing": int(clears.sum()),
            "share_of_actual": twh / ACTUAL_TWH[year]
            if year in ACTUAL_TWH
            else float("nan"),
        }

    # Where does the bound first cover the actual? Reported as the offer level a lever would have
    # to reach, so the lever can be sized rather than argued about.
    covering = [s for s in OFFER_SCALES if curve[f"{s:.2f}"]["share_of_actual"] >= 1.0]
    return {
        "actual_twh": ACTUAL_TWH.get(year),
        "model_twh": float(ct.groupby("hour")["mw"].sum().sum() / 1e6),
        "curve": curve,
        "offer_scale_needed": max(covering) if covering else None,
        "reachable_at_any_offer": bool(covering),
    }


def fuel_by_class_zone(leg: Path, year: int) -> dict:
    """Implied delivered-fuel premium per class and zone, from the keeper's own offers.

    Uses the peak-to-econ band spread within a plant, which cancels the plant's own base heat
    rate and the flat part of its offer, leaving the fuel charge each class faces.
    """
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "plant_group", "zone", "hour", "mc", "cap_mw"],
    )
    unit = unit[unit["pass"] == "P1"].copy()
    unit["band"] = [band_of(u) for u in unit["unit_id"]]
    out: dict[str, dict] = {}
    for (klass, zone), grp in unit.groupby(["plant_group", "zone"]):
        if klass not in ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP"):
            continue
        econ = grp[grp["band"].isin(("econlo", "econhi", "econc00", "econc05"))]
        if econ.empty:
            continue
        out.setdefault(str(klass), {})[str(zone)] = {
            "cap_mw": float(grp.groupby("unit_id")["cap_mw"].max().sum()),
            "econ_offer_mean": float(econ["mc"].mean()),
        }
    return out


def main() -> None:
    """Report the reachability bound and the fuel cut for each committed per-year leg."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report: dict[str, dict] = {}
    for leg_str in args.legs:
        leg = Path(leg_str)
        year = int(leg.name.rsplit("_", 1)[-1])
        bound = bound_for_year(leg, year)
        report[str(year)] = {
            "bound": bound,
            "fuel_by_class_zone": fuel_by_class_zone(leg, year),
        }
        print(
            f"=== {year}  model {bound['model_twh']:.3f} TWh vs actual {bound['actual_twh']:.3f} TWh ==="
        )
        for scale, row in bound["curve"].items():
            print(
                f"   offer x{scale}  upper bound {row['energy_twh_upper_bound']:>7.3f} TWh"
                f"  ({row['share_of_actual'] * 100:>6.1f} % of actual)"
            )
        print(
            f"   -> reachable by an offer lever alone: {bound['reachable_at_any_offer']}"
            + (
                f" (needs offer x{bound['offer_scale_needed']:.2f})"
                if bound["reachable_at_any_offer"]
                else ""
            )
        )

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
