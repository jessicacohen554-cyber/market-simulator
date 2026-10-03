"""Emit the NWPP-NEXT-24 calibration attestation for the HEAD data re-solve span bundle.

NWPP-NEXT-24 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext24-data-resolve-2019-2025-2026-10-03.md``) replays keeper
``2026-10-03-nwpp-next-23-coi``'s recipe UNCHANGED (:mod:`gen_nwppnext23_attestation`) at main
HEAD. Only two data inputs move: #7134 EIA-923 coal stocks 2015-17 and the SolveEpoch
2026-10-03b NWPP 2019-22 ``NUCLEAR_MONTHLY_CF_BY_YEAR`` rows. It is a rule-14 data re-solve
with **ZERO NEW FREE PARAMETERS** (rules 21 / 24).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext23_attestation as n23  # noqa: E402

PIN = "23beba2ac9c1baa00f276a6723e5af47217739ff"


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the NWPP-NEXT-24 attestation built on NEXT-23's generator."""
    att = n23.build(bundle, pin)
    att["lane"] = "NWPP-NEXT-24"
    att["governance"]["notes"] = (
        "Keeper 2026-10-03-nwpp-next-23-coi recipe replayed unchanged at main HEAD (close-out "
        "desk ruling '7-shard replay at HEAD'). Rule-14 data re-solve; offer-curve multipliers "
        "unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]}: main b54e1d84 "
        "(keeper NEXT-23 + #7134 coal stocks + SolveEpoch 2026-10-03b NWPP nuclear rows) + "
        "records only, on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "No config key moved against keeper 2026-10-03-nwpp-next-23-coi (scenario_config diff "
        "empty in every year). Inputs moved: EIA-923 coal stocks 2015-17 (yard maxima for the take "
        "floor / monthly pile) and the NWPP 2019-22 measured nuclear monthly CF rows. Same "
        "libraries; other drift INERT (PRECOMMIT G-DRIFT)."
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
