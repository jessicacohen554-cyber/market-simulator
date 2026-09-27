"""Emit the NWPP-NEXT-7 calibration attestation for the coal take-floor span bundle.

NWPP-NEXT-7 (PRECOMMIT
``docs/handoffs/PRECOMMIT-nwppnext7-coal-take-floor-2019-2025-2026-09-27.md``) is
keeper #13's recipe (NWPP-NEXT-6 arm AB) plus the per-coal-yard annual coal TAKE
floor, ruled by the owner on 2026-09-27 (Q1-Q5):
``coal_fuel_inventory_plant_grain`` and ``coal_fuel_inventory_take_floor`` armed,
``coal_takeorpay_from_data`` and ``coal_committed_takeorpay_regulated`` retired.

It reuses :mod:`gen_nwppnext6_attestation` (arm AB) and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): every floor and ceiling quantity is
the yard's own EIA-923 Page 2 / Page 5 record from years before the solve year.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext6_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "2162cef52b4c4667a2be4ca288d38ea77e19186a"
ARMED = ("coal_fuel_inventory_plant_grain", "coal_fuel_inventory_take_floor")
RETIRED = ("coal_takeorpay_from_data", "coal_committed_takeorpay_regulated")


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-7 attestation built on the NWPP-NEXT-6 arm-AB generator."""
    for f in ARMED:
        if f not in base._ARMED:
            base._ARMED = (*base._ARMED, f)
    base._SOURCES["coal_fuel_inventory_plant_grain"] = (
        "EIA-923 Page 2 December(Y-1) coal stock + mean Y-2..Y-1 Page 5 receipts, per coal "
        "yard, x the yard's own heat content: the per-yard annual CEILING (miso-268 "
        "construction; NWPP added to COAL_PLANT_GRAIN_ISOS by owner ruling Q1, 2026-09-27)."
    )
    base._SOURCES["coal_fuel_inventory_take_floor"] = (
        "EIA-923 Page 5 Y-1 contract tonnage (purchase types C/NC/T), renewed at volume "
        "(estimator B, owner ruling Q4), net of stock slack: max(0, contract + Dec(Y-1) stock "
        "- max month-end stock <= Y-1) x the yard's Y-1 heat content, clipped to the yard "
        "ceiling and to sum HR x pmax x availability. Owner rulings Q1-Q5, 2026-09-27. "
        "SOFT (owner ruling 2026-09-27): shortfall priced per yard at the yard's own "
        "model coal fuel price, capability-weighted (take-or-pay)."
    )
    att = prev.build(bundle, "AB")
    att["lane"] = "NWPP-NEXT-7"
    for f in RETIRED:
        att["switches"][f] = {
            "value": False,
            "where": f"ScenarioConfig.{f}, pinned through replay_keeper --set",
            "identification": "structural",
            "source": (
                "Retired by owner ruling Q5 (2026-09-27, rule 19): the take-or-pay contract "
                "is carried once, by the yard take-floor row's dual."
            ),
        }
    att["governance"]["notes"] = (
        "Keeper #13 recipe plus the per-coal-yard annual coal take floor (owner rulings "
        "Q1-Q5, 2026-09-27): the yard row bounded on both sides by measured EIA-923 "
        "quantities that predate the solve year; the per-hour take-or-pay discounts retired "
        "in the same arm (rule 19). Offer-curve multipliers unchanged; nothing swept, nothing "
        "selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Four config keys move together as one mechanism (PRECOMMIT s1): the yard rows and "
        "their ceiling, the take floor, and the two retired per-hour discounts. Demand, "
        "offers and every other input are keeper #13's (G-DRIFT form 4, PRECOMMIT s3)."
    )
    disc["take_floor_capacity_clip"] = (
        "The floor is clipped to what the yard's rowed units can burn. In 2020 this binds at "
        "Colstrip (5.86 vs 13.26 TWh), whose model available energy is below its measured "
        "2020 generation (7.94 TWh): an availability-input question, routed, not absorbed."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
