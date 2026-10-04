"""Emit the NWPP-NEXT-28 calibration attestation for the BA contingency-reserve span bundle.

NWPP-NEXT-28 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext28-ba-reserve-2019-2025-2026-10-04.md``) is keeper
``2026-10-03-nwpp-next-27-path76``'s recipe (:mod:`gen_nwppnext27_attestation`) plus the per-BA
WECC BAL-002-WECC-2a contingency reserve (``nwpp_ba_contingency_reserve``, through the shared
``energy_reserve_coopt`` gate). **ZERO NEW FREE PARAMETERS** (rules 21 / 24): published 3 % / 3 %
/ half-spinning fractions, the CAMPD-measured online rho, hydro ramp class physics, and the
region's registered voll as the shortfall price.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext27_attestation as n27  # noqa: E402

PIN = "971685b4ee2a48e0f838c4d9c2135e5bb34773b5"
FIELD = "nwpp_ba_contingency_reserve"
GATE = "energy_reserve_coopt"

_SOURCES = {
    FIELD: (
        "WECC Regional Reliability Standard BAL-002-WECC-2a: Contingency Reserve of 3 % of hourly "
        "load + 3 % of hourly net generation per member BA (R1), at least half spinning (R2), "
        "over the members' own EIA-930 Demand / Net generation (Adjusted) "
        "(envelopes.nwpp_ba_contingency_basis), held in each member's zone on (zone, fuel-class) "
        "thermal + hydro pools; spinning columns online-gated at the CAMPD-measured rho 0.2130 "
        "(data/raw/_processed-legacy/campd_online_reserve_rho_NWPP.csv, family set nwpp_spin); "
        "hydro 10-minute ramp = nameplate (NWPP_HYDRO_RAMP10_FRAC, NREL/TP-5500-55588 App. H); "
        "shortfall priced at the region's registered voll (no NWPP demand curve exists)."
    ),
    GATE: (
        "The shared energy+reserve co-optimisation gate; on NWPP it builds only the "
        "nwpp_ba_contingency_reserve design (reserves/spec._nwpp_design) and is refused without it."
    ),
}


def build(bundle: Path, pin: str = PIN) -> dict:
    """Return the NWPP-NEXT-28 attestation built on NEXT-27's generator."""
    base = n27.n26.n25.base
    for key, src in _SOURCES.items():
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = src
    att = n27.build(bundle, pin)
    for key, src in _SOURCES.items():
        if key in att.get("switches", {}):
            att["switches"][key]["source"] = src
    att["lane"] = "NWPP-NEXT-28"
    att["governance"]["notes"] = (
        "Keeper 2026-10-03-nwpp-next-27-path76 recipe plus the per-BA BAL-002-WECC contingency "
        "reserve (owner card 2026-10-04 'Build reserve, solve'). Offer-curve multipliers "
        "unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {pin[:8]}: main bba28607 "
        "(keeper NEXT-27) + the NEXT-28 key and tests, on the requirements.txt library pins."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Config keys moved against keeper 2026-10-03-nwpp-next-27-path76: energy_reserve_coopt "
        "-> True and nwpp_ba_contingency_reserve -> True (one new mechanism; NWPP had no reserve "
        "design). Every year moves. Same libraries; other drift INERT (PRECOMMIT G-DRIFT)."
    )
    disc["reserve_scope"] = (
        "Regulation reserve, storage eligibility and the MSSC branch of BAL-002-WECC R1 are not "
        "modelled (no WECC numeric regulation standard or measured NWPP series; the 3 % + 3 % "
        "term exceeds every footprint single contingency). The forward requirement basis is not "
        "wired: the runner refuses the key."
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
