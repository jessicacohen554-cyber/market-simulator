"""Emit the NWPP-NEXT-14 calibration attestation for the Clark-HR + Bridger-vintage span bundle.

NWPP-NEXT-14 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext14-clark-hr-bridger-vintage-2019-2025-2026-09-30.md``) is
keeper #18's recipe (NWPP-NEXT-13) plus two rule-14 repairs:
``eia923_cc_family_heat_rates`` (Clark 2322's CC rows loaded an impossible eGRID 3.007
MMBtu/MWh; EIA-923 measures the block at 9.0-9.6) and ``campd_unit_fuel_split`` composed with
per-unit attribution (Jim Bridger's per-unit COAL row divided 2023 four-unit coal conduct by
the 2025 bin).

It reuses :mod:`gen_nwppnext13_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): EIA-923 fuel and net generation by prime mover,
a physical floor that aliases an existing cited constant, and EIA-860 vintage bins.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext13_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "54edd9e324913a2c915199ca2af8e46abfed582b"
ARMED = ("eia923_cc_family_heat_rates", "campd_unit_fuel_split")


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-14 attestation built on the NWPP-NEXT-13 generator."""
    for key in ARMED:
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
    base._SOURCES["eia923_cc_family_heat_rates"] = (
        "EIA-923 CC-family heat rate (data/raw/_processed-legacy/"
        "eia923_cc_family_heat_rates_NWPP.csv, derive_eia923_cc_family_heat_rates.py): a "
        "non-CHP plant's CT/CA/CS/CC rows whose eGRID plant rate is below the CC physical "
        "floor (HEAT_RATE_BINS gas_cc h_class) take the plant's own EIA-923 electric fuel / "
        "net generation over those prime movers. Moves Clark 2322 only. Rule 14."
    )
    base._SOURCES["campd_unit_fuel_split"] = (
        "Per-unit fuel-split tranche companion (data/raw/_processed-legacy/"
        "thermal_tranches-perunit-fuelsplit-NWPP.csv, derive_thermal_tranches.py "
        "--per-unit-attribution --unit-fuel-split): mixed-fuel plants' rows on each window "
        "year's own EIA-860 vintage bin, per-unit outage derate. Moves Jim Bridger's COAL "
        "row only. Rule 14."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-14"
    att["governance"]["notes"] = (
        "Keeper #18 recipe plus two rule-14 repairs (FINDING-nwppnext14 s2-s3; owner cards "
        "'EIA-923 CC-family HR' and 'Both', 2026-09-30). Offer-curve multipliers unchanged; "
        "nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Two config keys (eia923_cc_family_heat_rates, campd_unit_fuel_split) move against "
        "keeper #18. Zero-LP LP-array delta: Clark 2322's three CC bins (heat rate 3.007 -> "
        "9.0-9.6) and Jim Bridger's must-run split (351.8 -> 343.3 MW in 2023; 174.1 -> 169.9 "
        "in 2024-25) only (PRECOMMIT s2, G-DRIFT s3)."
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
