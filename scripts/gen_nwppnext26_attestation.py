"""Emit the NWPP-NEXT-26 calibration attestation for the NEVP seam in-service vintage span bundle.

NWPP-NEXT-26 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext26-nevp-hae-2019-2025-2026-10-03.md``) is keeper
``2026-10-03-nwpp-next-25-served``'s recipe (:mod:`gen_nwppnext25_attestation`) plus
``nwpp_seam_in_service_vintage``: the CAISO_NEVP seam is priced only in the hours after the
Harry Allen-Eldorado intertie entered service (2020-08-12, FERC ER20-1514); before it the
seam's measured leg is served and its net flow capped at zero. **ZERO NEW FREE PARAMETERS**
(rules 21 / 24): the in-service instant is a dated physical event
(``constants.NWPP_SEAM_IN_SERVICE_UTC``), never fitted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext25_attestation as n25  # noqa: E402

PIN = "30c0e01790f3ee4085042193be816d47cc704c31"

_SOURCES = {
    "nwpp_seam_in_service_vintage": (
        "CAISO_NEVP priced only after the DesertLink Harry Allen-Eldorado 500 kV intertie entered "
        "service (constants.NWPP_SEAM_IN_SERVICE_UTC 2020-08-12; FERC ER20-1514 CAISO-NEVP ABAOA "
        "Amendment No. 5 and the measured EIA-930 NEVP->CISO step); before it the measured leg is "
        "served at SNV and the seam's net flow capped at zero, one hourly mask (rule 19). Rule 14: "
        "a physical in-service date over a rating applied before its path existed."
    ),
}


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the NWPP-NEXT-26 attestation built on NEXT-25's generator."""
    base = n25.base
    for key, src in _SOURCES.items():
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = src
    att = n25.build(bundle, pin)
    run_config = json.loads((bundle / "run_config.json").read_text())
    sc = run_config.get("scenario_config", run_config)
    if sc.get("nwpp_seam_in_service_vintage") is not True:
        raise SystemExit(
            "run_config nwpp_seam_in_service_vintage is not True -- not the NEXT-26 arm"
        )
    att["lane"] = "NWPP-NEXT-26"
    att["governance"]["notes"] = (
        "Keeper 2026-10-03-nwpp-next-25-served recipe with CAISO_NEVP priced only after its "
        "physical path entered service (owner card 2026-10-03 'Serve pre-HAE'). Offer-curve "
        "multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]}: main 005aa03c "
        "(keeper NEXT-25) + the NEXT-26 key and tests, on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config key moved against keeper 2026-10-03-nwpp-next-25-served: "
        "nwpp_seam_in_service_vintage -> True. Moves 2019 (all hours) and 2020 (before 2020-08-12) "
        "only; 2021-2025 inputs identical. Same libraries; other drift INERT (PRECOMMIT G-DRIFT)."
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
