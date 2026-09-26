"""Emit the NWPP-NEXT-5 calibration attestation for ``results/calibration/nwppnext5_span``.

NWPP-NEXT-5 (PRECOMMIT ``docs/handoffs/PRECOMMIT-nwppnext5-standby-admission-2019-2025-2026-09-26.md``)
is keeper #11's recipe (NWPP-NEXT-4) plus ONE gated field, ``admit_standby_units``:
EIA-860 standby (``SB``) generators enter the fleet by status alone.

It reuses :mod:`gen_nwppnext4_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): the arm widens a published-status
filter; it introduces no scalar and selects nothing on an outcome.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext4_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwppnext5_span"
FIELD = "admit_standby_units"


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-NEXT-5 attestation built on the NWPP-NEXT-4 generator."""
    if FIELD not in base._ARMED:
        base._ARMED = (*base._ARMED, FIELD)
    base._SOURCES[FIELD] = (
        "EIA-860 generator Status (published, known ex ante from the solve year's own "
        "vintage): SB = 'Standby/Backup - available for service but not normally used'. "
        "Armed, the fleet admits {OP, SB} instead of {OP}. NWPP: Fredonia 607 (PSEI -> "
        "NWPP-NW, 280 MW summer) and Sun Peak 54854 (NEVP -> NWPP-SNV, 222 MW), SB in every "
        "vintage 2018-2025, plus ~78-90 MW of small SB units "
        "(FINDING-nwppnext2-standby-census-2026-09-25). No unit selected on EIA-923 output."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-5"
    att["governance"]["notes"] = (
        "Keeper #11 recipe plus one gated fleet-membership field: EIA-860 standby (SB) "
        "generators are admitted by status alone (rule 14: units that exist, are available "
        "and are counted by the C1 benchmark). Offer-curve multipliers unchanged (sha256 "
        f"{prev.prev.prev.prev.OFFER_CURVE_SHA256[:12]}...); nothing swept, nothing selected "
        "on a gate. Fredonia's eGRID heat rate (4.918, CT1/CT2 heat input missing from CAMPD) "
        "takes the SPP-49 simple-cycle floor 9.0; the measured-CT artifact is not re-derived "
        "(rule 23). Short-gas outage windows still NOT armed."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned 19f2eace."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Only fleet membership moves (+579.5 to +592.1 MW of SB units per year); demand, "
        "offers and every other input are keeper #11's (G-DRIFT form 4, PRECOMMIT s2)."
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
