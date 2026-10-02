"""Emit the NWPP-NEXT-21 calibration attestation for the priced-interface span bundle.

NWPP-NEXT-21 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext21-priced-interface-2019-2025-2026-10-02.md``) is keeper
#20's recipe (NWPP-NEXT-16 arm C) with the priced interface armed (lever NWPP-56):
``reference_price_interface`` (a ``scenario_config`` key) and ``priced_interchange`` (a solve
kwarg recorded in ``meta.json``; the runner CLI implies it from the first key, ``replay_keeper``
does not). Three seams (CAISO_COI, CAISO_NEVP, WECC_CAN in anchored years) clear against
measured counterparty prices in their own external zones; every unpriced counterparty is served
at its measured flow (``eia930.envelopes.nwpp_unpriced_residual_interchange``).

It reuses :mod:`gen_nwppnext16_attestation` arm ``c`` (keeper #20's generator) and adds this
lane's keys. **ZERO NEW FREE PARAMETERS** (rules 21 / 24): the seam anchors are measured prices
(OASIS MALIN, CAISO net load, the BCHA WEIM ELAP), the limits are WECC path ratings and the
hurdles are the registered ``NeighborInterface`` values, none set on this lane.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext16_attestation as k20  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "86b73d6f910d4b3a179f6158727b5e31b5f8c265"

_SOURCES = {
    "reference_price_interface": (
        "NWPP priced seams (model/interchange/spec.INTERFACE_NEIGHBORS['NWPP'], NWPP-NEXT-20): "
        "CAISO_COI 4,800 MW (NW+OR) and CAISO_NEVP 1,933 MW (SNV) on the OASIS MALIN anchor x "
        "CAISO net-load shape, hurdle 3; WECC_CAN 3,150 MW (NW) on the BCHA WEIM ELAP anchor, "
        "priced 2023-2025 only. One external zone per seam (IMPORT_SEAM_ZONES). Unpriced "
        "counterparties served at the measured EIA-930 residual (rule 19). Rule 13: every "
        "input is a forward-reproducible measured price or rating."
    ),
}


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-21 attestation built on keeper #20's (NEXT-16 arm C) generator."""
    for key, src in _SOURCES.items():
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = src
    att = k20.build(bundle, "c")
    meta = json.loads((bundle / "meta.json").read_text())
    years = meta["years"]
    if meta.get("priced_interchange") is not True:
        raise SystemExit(
            "meta.json priced_interchange is not True -- not the NEXT-21 arm"
        )
    att["switches"]["priced_interchange"] = {
        "value": True,
        "where": "solve_and_persist kwarg priced_interchange, pinned through replay_keeper --set",
        "identification": "measured-physical",
        "source": (
            "Serves the seams through the priced external zones instead of the measured "
            "schedule; the runner CLI implies it from reference_price_interface."
        ),
    }
    att["lane"] = "NWPP-NEXT-21"
    att["governance"]["notes"] = (
        "Keeper #20 recipe with the priced interface armed (owner cards 2026-10-02, NEXT-20). "
        "Offer-curve multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]} "
        "(keeper #20's pin 33014efc + the NEXT-19/20 interface code, INERT for the keeper), "
        "on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config keys moved against keeper #20: reference_price_interface -> True, "
        "priced_interchange -> True. Same libraries; code drift classified INERT (PRECOMMIT s2)."
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
