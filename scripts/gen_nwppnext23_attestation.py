"""Emit the NWPP-NEXT-23 calibration attestation for the COI delivery-basis span bundle.

NWPP-NEXT-23 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext23-coi-pnw-basis-2019-2025-2026-10-03.md``) is the
NEXT-22b keeper's recipe (:mod:`gen_nwppnext22_attestation`, basis ``w0``) plus
``nwpp_coi_pnw_delivery_basis``: the CAISO_COI seam's NW->CA export bands pay CAISO's
registered PNW delivered-cost basis (``CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]``, loss 0.05,
wheel $5) instead of the symmetric 3.0 hurdle. **ZERO NEW FREE PARAMETERS** (rules 21 / 24):
the basis is CAISO's own registry constant for the same physical corridor (rule 19), never
fitted to an NWPP residual.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext22_attestation as n22  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "33dc564771e1006ce69ffd2789053107ed4801cc"

_SOURCES = {
    "nwpp_coi_pnw_delivery_basis": (
        "CAISO_COI export leg priced at (band - wheel) / (1 + loss) with CAISO's registered PNW "
        "delivered-cost basis CAISO_IMPORT_DELIVERY_BASIS['PNW_midC'] = (0.05, 5.0) "
        "(spec.NWPP_SEAM_EXPORT_DELIVERY_TRANCHE), replacing the 3.0 hurdle on that leg only. "
        "Rule 19: one physical path, one delivery basis on both sides. Rule 13: a tariff wheel "
        "and loss factor, forward-reproducible."
    ),
}


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the NWPP-NEXT-23 attestation built on NEXT-22's generator (w0 basis)."""
    for key, src in _SOURCES.items():
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = src
    att = n22.build(bundle, pin, "w0")
    run_config = json.loads((bundle / "run_config.json").read_text())
    sc = run_config.get("scenario_config", run_config)
    if sc.get("nwpp_coi_pnw_delivery_basis") is not True:
        raise SystemExit(
            "run_config nwpp_coi_pnw_delivery_basis is not True -- not the NEXT-23 arm"
        )
    att["lane"] = "NWPP-NEXT-23"
    att["governance"]["notes"] = (
        "NEXT-22b keeper recipe with the COI export leg on CAISO's registered PNW delivered-cost "
        "basis (owner card 2026-10-03 'Solve H2 PNW basis'). Offer-curve multipliers unchanged; "
        "nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]}: main a50ffae8 "
        "(NEXT-22b keeper + the close-out roster-free plant-basis anchor, SolveEpoch "
        "2026-10-03a) + the NEXT-23 code, on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config key moved against keeper 2026-10-03-nwpp-next-22b-w0: "
        "nwpp_coi_pnw_delivery_basis -> True. Input moved: the plant-basis anchor CSV "
        "(#7103, <= 0.0054 TWh/yr of requirement). Same libraries; other drift INERT "
        "(PRECOMMIT s1)."
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
