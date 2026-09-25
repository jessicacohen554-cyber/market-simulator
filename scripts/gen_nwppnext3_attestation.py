"""Emit the NWPP-NEXT-3 calibration attestation for ``results/calibration/nwppnext3_span``.

NWPP-NEXT-3 (PRECOMMIT ``docs/handoffs/PRECOMMIT-nwppnext3-plant-basis-2019-2025-2026-09-25.md``)
is keeper #9's recipe (NWPP-NEXT-2 + the 2019-2022 hydro cascade) plus ONE
gated field, ``nwpp_demand_plant_basis``: the owner's framing-2 ruling on
``FINDING-nwpp-45`` §8 — anchor the served requirement to the plant basis C1
scores on (EIA-930 hourly shape, EIA-923 plant energy, per fuel family).

It reuses :mod:`gen_nwppnext2_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): every term is a measured series
or a measured annual total from the committed bench parts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext2_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwppnext3_span"
FIELD = "nwpp_demand_plant_basis"


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-NEXT-3 attestation built on the NWPP-NEXT-2 generator."""
    if FIELD not in base._ARMED:
        base._ARMED = (*base._ARMED, FIELD)
    base._SOURCES[FIELD] = (
        "Owner ruling 2026-09-25 on FINDING-nwpp-45 s8 = framing 2. Per EIA-930 fuel family "
        "(COL; NG net of GRID's Southwest legs; NUC; WAT; OTH+OIL — wind/solar are EIA-930-"
        "native and untouched) the served schedule's annual energy is moved onto the family's "
        "grid-delivered EIA-923 plant total (data/raw/reference/nwpp_plant_basis_energy.csv, "
        "derived from the committed bench parts' classFull by "
        "scripts/data/derive_nwpp_plant_basis_energy.py) on its own EIA-930 hourly shape. On the "
        "preliminary 2025 vintage only COL and NG are anchored. Requirement +4.59 / +7.47 / "
        "+5.55 / +5.08 / +7.73 / +10.40 / +11.83 TWh 2019-2025."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-3"
    att["governance"]["notes"] = (
        "Keeper #9 recipe plus one gated demand-construction field (owner ruling, framing 2): "
        "the NWPP served requirement is anchored per fuel family to the EIA-923 plant basis "
        "(rule 14 misalignment reconciliation, adopted by explicit owner ruling given its "
        "proximity to rule 13). Offer-curve multipliers unchanged (sha256 "
        f"{prev.prev.OFFER_CURVE_SHA256[:12]}...); nothing swept, nothing selected on a gate. "
        "Short-gas outage windows still NOT armed."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned dad798cd."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Every year's requirement moves by the plant-basis anchor (+4.59 to +11.83 TWh); no "
        "other input moves (G-DRIFT form 4, PRECOMMIT s4)."
    )
    disc["rule_13_proximity"] = (
        "The anchor reconciles a measured input toward the basis C1 scores on, so total "
        "generation lands near the benchmark total by construction. The class, zonal and "
        "hourly split stay the LP's. Adopted by explicit owner ruling (framing 2); the C1 "
        "movement is not evidence of skill on the total."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
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
