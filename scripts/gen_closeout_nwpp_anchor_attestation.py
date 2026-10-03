"""Emit the closeout-nwpp-anchor calibration attestation for the anchor re-solve span.

closeout-nwpp-anchor (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-closeout-nwpp-anchor-2026-10-03.md``) replays the incumbent
keeper ``2026-10-03-nwpp-next-22b-w0`` (``results/calibration/nwppnext22b_span``) unchanged.
The one LIVE input is ``data/raw/reference/nwpp_plant_basis_energy.csv``, re-derived from the
sources on a roster-free plant -> class map (owner ruling R-28, PR #7103). **ZERO NEW FREE
PARAMETERS and no config key moved**: the attestation is NEXT-22b's, with this lane's
provenance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext22_attestation as n22  # noqa: E402

PIN = "dad1205a2a75a3079874880c879846a346c54dc5"


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the closeout-nwpp-anchor attestation built on NEXT-22b's generator."""
    att = n22.build(bundle, pin, "w0")
    att["lane"] = "closeout-nwpp-anchor"
    att["governance"]["notes"] = (
        "The incumbent keeper's recipe (2026-10-03-nwpp-next-22b-w0) replayed unchanged; the "
        "nwpp_demand_plant_basis anchor CSV re-derived from EIA-923 / CAMPD / EIA-930 on a "
        "roster-free plant -> class map (owner ruling R-28 'Keep old figures, fix later', "
        "PR #7103). Offer-curve multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]} (main after "
        "PR #7103): the NEXT-22b keeper recipe; G-DRIFT vs its leg SHA 2b8da72a classifies "
        "only the anchor CSV (and SolveEpoch 2026-10-03a, key only) LIVE (PRECOMMIT s5)."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "No config key moved against 2026-10-03-nwpp-next-22b-w0. Input moved: "
        "nwpp_plant_basis_energy.csv, COL / NG / OTH by 0.002-0.126 TWh per year (net anchored "
        "requirement <= 0.0054 TWh/yr; FINDING-closeout-nwpp-anchor s3)."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--pin", default=PIN, help="full 40-char solve pin")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle, args.pin)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
