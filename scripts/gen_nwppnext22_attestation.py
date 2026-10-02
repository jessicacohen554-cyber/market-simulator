"""Emit the NWPP-NEXT-22 calibration attestation for the seam-headroom span bundle.

NWPP-NEXT-22 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext22-seam-headroom-2019-2025-2026-10-02.md``) is NEXT-21's arm
(keeper #20's recipe with the priced interface, :mod:`gen_nwppnext21_attestation`) plus
``nwpp_seam_measured_limits``: each priced seam's net flow is capped at its measured hourly
operating limit (CAISO's share of COI; BPA's BC Intertie) instead of the full path rating.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): the caps are published operating limits, and the
2/3 COI share is the Path 66 ownership split (``constants.NWPP_COI_CAISO_SHARE``), checked
against CAISO's own OTC, never fitted to a flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext21_attestation as n21  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "a5a72ec04be06ef8cb861aa6d5c68689dfc9c688"

_SOURCES = {
    "nwpp_seam_measured_limits": (
        "Measured hourly operating limits on the priced NWPP seams, one aggregate interface row "
        "per seam on its net flow: CAISO_COI = CAISO OASIS TRNS_USAGE MALIN500_ISL + CASCADE_ITC "
        "OTC (2023-06-19 on), else 2/3 (Path 66 ownership) x BPA's whole-path COI operating limit; "
        "WECC_CAN = BPA's BC Intertie operating limit (BPA OPI, data/raw/nwpp-intertie-otc); "
        "CAISO_NEVP keeps 1,933 MW. Rule 13: an operating limit is a physical operating condition "
        "(forward analogue: the seasonal path rating), never a flow or a schedule."
    ),
}


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-22 attestation built on NEXT-21's generator."""
    for key, src in _SOURCES.items():
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = src
    att = n21.build(bundle)
    run_config = json.loads((bundle / "run_config.json").read_text())
    sc = run_config.get("scenario_config", run_config)
    if sc.get("nwpp_seam_measured_limits") is not True:
        raise SystemExit(
            "run_config nwpp_seam_measured_limits is not True -- not the NEXT-22 arm"
        )
    att["lane"] = "NWPP-NEXT-22"
    att["governance"]["notes"] = (
        "Keeper #20 recipe with the priced interface and the measured seam headroom armed "
        "(owner cards 2026-10-02: NEXT-21 'Hold #20, fix seam headroom'; NEXT-22 'CAISO share + "
        "BPA BC'). Offer-curve multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]} "
        "(NEXT-21's pin 86b73d6f + the CAISO TRNS_USAGE intake + the NEXT-22 code, INERT for "
        "the keeper; PRECOMMIT s2), on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config keys moved against keeper #20: reference_price_interface -> True, "
        "priced_interchange -> True, nwpp_seam_measured_limits -> True. Same libraries; code "
        "drift classified INERT (PRECOMMIT s2)."
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
