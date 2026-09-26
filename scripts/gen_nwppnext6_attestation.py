"""Emit the NWPP-NEXT-6 calibration attestation for an arm-A or arm-AB span bundle.

NWPP-NEXT-6 (PRECOMMIT
``docs/handoffs/PRECOMMIT-nwppnext6-path76-and-ct-rederive-2019-2025-2026-09-26.md``)
is keeper #12's recipe (NWPP-NEXT-5) plus ONE gated field,
``nwpp_path76_alturas_link`` (arm A). Arm AB adds the rule-23 re-derive of
``campd_ct_heat_rates_NWPP.csv`` on the SB-admitted fleet (owner ruling
2026-09-26). That is a measured-input population change, not a config key.

It reuses :mod:`gen_nwppnext5_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): the link's rating is the WECC
catalogue's, and the re-derive adds measured rows under an unchanged method.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext5_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

FIELD = "nwpp_path76_alturas_link"
PINS = {
    "A": "e29efd5f3bd563ba37d548b57087b433f603c381",
    "AB": "0a84941d9dbc605d9f6b52894cba9597b3e85d68",
}


def build(bundle: Path, arm: str) -> dict:
    """Return the NWPP-NEXT-6 attestation for ``arm`` built on the NWPP-NEXT-5 generator."""
    if FIELD not in base._ARMED:
        base._ARMED = (*base._ARMED, FIELD)
    base._SOURCES[FIELD] = (
        "WECC 2024 Path Rating Catalog (public) p. 69: Path 76 'Alturas Project', Hilltop "
        "230/345 kV + Hilltop-Fort Sage 345 kV, Accepted Rating 300/300 MW. Booked NWPP-NW <-> "
        "NWPP-SNV by the EIA-930 BA pair for the seam (NEVP<->BPAT, -246...+182 MW 2023-2025; "
        "NEVP has no PACW leg). One bidirectional 300 MW link, no scalar chosen."
    )
    att = prev.build(bundle)
    att["lane"] = f"NWPP-NEXT-6 arm {arm}"
    notes = (
        "Keeper #12 recipe plus one gated topology field: the WECC Path 76 link NW<->SNV "
        "(rule 14: a published rating over an absent link). Offer-curve multipliers unchanged; "
        "nothing swept, nothing selected on a gate."
    )
    if arm == "AB":
        notes += (
            " Plus the owner-ruled (rule 23, 2026-09-26) re-derive of campd_ct_heat_rates_NWPP.csv "
            "on the SB-admitted fleet: the 86 existing rows are byte-identical, and 16 rows are added "
            "(Fredonia 607 pooled 10.413 replacing the 9.0 floor; Sun Peak 54854 pooled 12.893 "
            "replacing eGRID 13.436)."
        )
    att["governance"]["notes"] = notes
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PINS[arm][:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "One link is added (300 MW NW<->SNV). Demand, offers and every other input are "
        "keeper #12's (G-DRIFT form 4, PRECOMMIT s3)"
        + (
            "; the measured-CT artifact gains rows for 607 and 54854 only."
            if arm == "AB"
            else "."
        )
    )
    disc["path76_overflow"] = (
        "The LP arbitrages the link to its 300 MW rating, while the measured BPAT->NEVP seam "
        "averages 20-28 MW. This is stated before the solve (PRECOMMIT s1.3) and is never "
        "re-rated to a residual."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--arm", choices=sorted(PINS), required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle, args.arm)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
