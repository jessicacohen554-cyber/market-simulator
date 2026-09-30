"""Emit the NWPP-NEXT-13 calibration attestation for the per-unit attribution span bundle.

NWPP-NEXT-13 (PRECOMMIT
``docs/handoffs/PRECOMMIT-nwppnext13-perunit-attribution-2019-2025-2026-09-30.md``) is
keeper #17's recipe (NWPP-NEXT-12) plus ``campd_per_unit_attribution``: the committed
NWPP CAMPD outage extract routed Clark 2322's and Silverhawk 55841's GT simple-cycle
peakers onto CC_REGULAR, and the tranche artifact attributed facility-summed CAMPD net to
the plant's largest bin, leaving Jim Bridger without a measured COAL row.

It reuses :mod:`gen_nwppnext12_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): a crosswalk on EIA-860 prime movers, CAMPD
unit types and CAMPD ``primaryFuelInfo``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext12_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "f2cfda468a0c43c522195d976a6b082d233ba213"
ARMED = "campd_per_unit_attribution"


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-13 attestation built on the NWPP-NEXT-12 generator."""
    if ARMED not in base._ARMED:
        base._ARMED = (*base._ARMED, ARMED)
    base._SOURCES[ARMED] = (
        "Per-unit CAMPD attribution (both artifacts, rule 19): "
        "data/raw/campd-unit-outages-perunit-NWPP.csv (derive_campd_unit_outages.py "
        "--per-unit-crosswalk: keeper #17's extract minus Clark 2322's 2,951 and Silverhawk "
        "55841's 46 GT-peaker windows) and data/raw/_processed-legacy/"
        "thermal_tranches-perunit-NWPP.csv (derive_thermal_tranches.py --per-unit-attribution "
        "with the COAL-SUB family-token repair and the coal-fuel guard). Rule-14: EIA-860 prime "
        "movers classify the routed units as GT peakers; rule-23 new derive outputs."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-13"
    att["governance"]["notes"] = (
        "Keeper #17 recipe plus CAMPD per-unit attribution (handoff lever 2, Clark 2322 CC "
        "routing; FINDING-nwppnext13 §2). Offer-curve multipliers unchanged; nothing swept, "
        "nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "One config key (campd_per_unit_attribution) moves against keeper #17. Its zero-LP "
        "census moves CC_REGULAR availability +3.0-3.7 TWh/yr (Clark) and +2.8-3.0 TWh "
        "(Silverhawk 2024-25), and the tranche split at seven plants, Jim Bridger's take-or-pay "
        "must-run 953.5 -> 351.8 MW among them (G-DRIFT form 4, PRECOMMIT s3)."
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
