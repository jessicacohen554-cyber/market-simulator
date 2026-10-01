"""Emit the NWPP-NEXT-8 calibration attestation for the monthly coal-pile span bundle.

NWPP-NEXT-8 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext8-coal-monthly-pile-2019-2025-2026-09-28.md``) is
keeper #14's recipe (NWPP-NEXT-7) plus ``coal_fuel_inventory_monthly_pile``: the
per-coal-yard pile identity at month-end grain, ruled by the owner on decision
cards 2026-09-28 (monthly pile balance; flat ratable receipts; floor and ceiling).

It reuses :mod:`gen_nwppnext7_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): month 12 is exactly keeper #14's
annual floor and ceiling, and the month-end rows read no quantity the annual rows
do not already read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext7_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "e7478536f46cade23e0aea71e79a329c0e29202a"
ARMED = "coal_fuel_inventory_monthly_pile"


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-8 attestation built on the NWPP-NEXT-7 generator."""
    if ARMED not in base._ARMED:
        base._ARMED = (*base._ARMED, ARMED)
    base._SOURCES[ARMED] = (
        "The per-coal-yard pile identity at month-end grain: cumulative burn through month m "
        "bounded by max(0, (Dec(Y-1) stock - max month-end stock <= Y-1) + m/12 x Y-1 contract "
        "tons) x hc from below and by (Dec(Y-1) stock + m/12 x mean Y-2..Y-1 receipts) x hc "
        "from above -- the same EIA-923 Page 2 / Page 5 quantities as the annual rows, receipts "
        "flat ratable. Month 12 equals the annual floor and ceiling exactly. Owner decision "
        "cards 2026-09-28."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-8"
    att["governance"]["notes"] = (
        "Keeper #14 recipe plus the monthly grain of the per-coal-yard pile identity (owner "
        "decision cards 2026-09-28, reopening Q2 'annual'): the take floor and the ceiling "
        "hold at every month-end, receipts flat ratable, month 12 identical to the annual "
        "rows. Offer-curve multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "One config key (coal_fuel_inventory_monthly_pile) moves against keeper #14. Demand, "
        "offers and every other input are keeper #14's (G-DRIFT form 4, PRECOMMIT s4)."
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
