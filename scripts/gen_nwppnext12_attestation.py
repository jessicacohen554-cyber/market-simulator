"""Emit the NWPP-NEXT-12 calibration attestation for the Boardman membership-repair span bundle.

NWPP-NEXT-12 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext12-boardman-membership-2019-2025-2026-09-29.md``) is
keeper #16's recipe (NWPP-NEXT-10) plus ``unit_outage_membership_repair``: the
committed NWPP CAMPD outage extract never scanned Boardman 6106, so its measured
whole-plant stops (2019-2020) were absent and the LP ran it fully available.

It reuses :mod:`gen_nwppnext10_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): the same deriver's windows for a
never-scanned facility, appended to the unchanged committed extract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext10_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "0b1d2cfea74e255113047608fb7bf35fa1f37443"
ARMED = "unit_outage_membership_repair"


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-12 attestation built on the NWPP-NEXT-10 generator."""
    if ARMED not in base._ARMED:
        base._ARMED = (*base._ARMED, ARMED)
    base._SOURCES[ARMED] = (
        "Membership repair of the >= 5-day CAMPD unit-outage extract: "
        "data/raw/campd-unit-outages-memberrepair-NWPP.csv = the committed extract's 5,058 rows "
        "byte-identical plus the 6 windows the same deriver produces at HEAD for Boardman 6106, "
        "the one facility the committed extract never scanned (built by "
        "scripts/data/build_outage_membership_repair.py). Rule-14 measured availability; rule-23 "
        "new derive output from the same source. Live in 2019-2020 only (Boardman exited "
        "2020-10-15)."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-12"
    att["governance"]["notes"] = (
        "Keeper #16 recipe plus the Boardman membership repair of the CAMPD outage layer (owner "
        "decision card 2026-09-29, 'Fidelity levers', lever 3 item 3). Offer-curve multipliers "
        "unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "One config key (unit_outage_membership_repair) moves against keeper #16. Its zero-LP "
        "census moves only 2019-2020 coal availability (-1.60 / -2.02 TWh); 2021-2025 inputs are "
        "byte-identical (G-DRIFT form 4, PRECOMMIT s3)."
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
