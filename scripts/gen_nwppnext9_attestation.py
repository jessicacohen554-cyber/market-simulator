"""Emit the NWPP-NEXT-9 calibration attestation for the measured-receipts span bundle.

NWPP-NEXT-9 (PRECOMMIT
``docs/handoffs/PRECOMMIT-nwppnext9-coal-measured-receipts-2019-2025-2026-09-28.md``) is
keeper #15's recipe (NWPP-NEXT-8) plus ``coal_monthly_pile_measured_receipts``: the
monthly pile's inflow read from the year's own EIA-923 Page 5 receipts instead of
the ratable prior-years proxy, ruled by the owner on a decision card 2026-09-28
("Backcast receipts overlay").

It reuses :mod:`gen_nwppnext8_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): every term is a measured Page 2 /
Page 5 quantity; the fallback rule (no same-year row -> ratable) is fixed ex ante.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext8_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "677273fb0f2d5d73f1ae79f3be6fd41d3c86de4d"
ARMED = "coal_monthly_pile_measured_receipts"


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-9 attestation built on the NWPP-NEXT-8 generator."""
    if ARMED not in base._ARMED:
        base._ARMED = (*base._ARMED, ARMED)
    base._SOURCES[ARMED] = (
        "The monthly pile's inflow in a backcast year: cumulative same-year EIA-923 Page 5 "
        "receipts per yard by month (all lots -> ceiling; contract lots C/NC/T -> floor), each "
        "at its own reported heat content, replacing m/12 of the Y-1/Y-2 proxies. A yard with "
        "no same-year row, and every yard in a year with no curated receipts file (2025), keeps "
        "the ratable profile. Rule-13 backcast overlay of a realised physical fuel-supply "
        "quantity (the same Page 5 table as the F923 delivered-price overlay). Owner decision "
        "card 2026-09-28."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-9"
    att["governance"]["notes"] = (
        "Keeper #15 recipe plus same-year measured receipts on the monthly coal pile (owner "
        "decision card 2026-09-28, reopening NEXT-8's 'flat ratable C/12' on the NEXT-9 "
        "census: 2023 PacifiCorp coal-supply shortfall). Offer-curve multipliers unchanged; "
        "nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "One config key (coal_monthly_pile_measured_receipts) moves against keeper #15. "
        "Demand, offers and every other input are keeper #15's (G-DRIFT form 4, PRECOMMIT s4a)."
    )
    disc["measured_same_year_input"] = (
        "Backcast overlay: the pile reads year Y's own Page 5 receipts. At mine-mouth yards "
        "(Jim Bridger) receipts partly follow burn, so this input is not fully exogenous; "
        "it is never a forecast methodology (the pile rows are backcast-only)."
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
