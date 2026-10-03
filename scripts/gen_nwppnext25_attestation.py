"""Emit the NWPP-NEXT-25 calibration attestation for the served-schedule zonal attribution span bundle.

NWPP-NEXT-25 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext25-served-schedule-2019-2025-2026-10-03.md``) is keeper
``2026-10-03-nwpp-next-24-head``'s recipe (:mod:`gen_nwppnext24_attestation`) plus
``nwpp_served_schedule_zonal_attribution``: each measured leg of the NWPP served schedule is
placed at the zone of the member BA that reports it instead of the load-share spread. **ZERO NEW
FREE PARAMETERS** (rules 21 / 24): the member's zone is ``zone_assignment._NWPP_BA_ZONES`` and its
clock is measured (``constants.NWPP_MEMBER_LOCAL_TZ``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext24_attestation as n24  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "d3965589f5d0b400e05560380de64d49ae0c6959"

_SOURCES = {
    "nwpp_served_schedule_zonal_attribution": (
        "The served schedule's measured EIA-930 per-DIBA legs (data/raw/eia-930-interchange, "
        "keyless bulk) placed at each reporting member's zone (zone_assignment._NWPP_BA_ZONES), "
        "priced-seam legs skipped in their priced years (rule 19), the remainder spread by the "
        "demand weights; column sums unchanged by construction. Rule 14: measured per-counterparty "
        "legs over a location-blind spread (the ERCOT tie-zone / PJM border-zone precedent)."
    ),
}


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the NWPP-NEXT-25 attestation built on NEXT-24's generator."""
    for key, src in _SOURCES.items():
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = src
    att = n24.build(bundle, pin)
    run_config = json.loads((bundle / "run_config.json").read_text())
    sc = run_config.get("scenario_config", run_config)
    if sc.get("nwpp_served_schedule_zonal_attribution") is not True:
        raise SystemExit(
            "run_config nwpp_served_schedule_zonal_attribution is not True -- not the NEXT-25 arm"
        )
    att["lane"] = "NWPP-NEXT-25"
    att["governance"]["notes"] = (
        "Keeper 2026-10-03-nwpp-next-24-head recipe with the served schedule placed at its "
        "reporting members' zones (owner card 2026-10-03 'Build and solve'). Offer-curve "
        "multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]}: main 3bec7bd4 "
        "(keeper NEXT-24) + the NEXT-25 key, tests and the 2019-22 per-DIBA back-fill of "
        "NEVP/PACE/NWMT/WAUW, on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config key moved against keeper 2026-10-03-nwpp-next-24-head: "
        "nwpp_served_schedule_zonal_attribution -> True. Input added: the 2019-22 per-DIBA legs of "
        "NEVP/PACE/NWMT/WAUW (read only by the armed key). System demand unchanged; zonal demand "
        "moves. Same libraries; other drift INERT (PRECOMMIT G-DRIFT)."
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
