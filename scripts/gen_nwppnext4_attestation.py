"""Emit the NWPP-NEXT-4 calibration attestation for ``results/calibration/nwppnext4_span``.

NWPP-NEXT-4 (PRECOMMIT ``docs/handoffs/PRECOMMIT-nwppnext4-coal-nested-2019-2025-2026-09-25.md``)
is keeper #10's recipe (NWPP-NEXT-3) plus ONE gated field,
``coal_committed_nested_on_mustrun`` (owner card D3): a coal plant with a
measured thermal-tranche row sizes its committed band as the increment above
its must-run band, because the artifact defines both shares as levels from
0 MW.

It reuses :mod:`gen_nwppnext3_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): the arm re-reads a measured
artifact's units; it introduces no scalar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext3_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwppnext4_span"
FIELD = "coal_committed_nested_on_mustrun"


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-NEXT-4 attestation built on the NWPP-NEXT-3 generator."""
    if FIELD not in base._ARMED:
        base._ARMED = (*base._ARMED, FIELD)
    base._SOURCES[FIELD] = (
        "Owner card D3 (FINDING-nwpp-48 s6). scripts/data/derive_thermal_tranches.py "
        "defines committed_pct (P5 of online-hour CF) and mustrun_pct (P5 of all-hour CF) "
        "as LEVELS from 0 MW; bins_to_fleet stacked _committed on top of _mustrun. Armed, "
        "a coal plant with a measured row takes pct_mc = max(0, committed - mustrun), so the "
        "two bands sum to the measured committed level. 2,047.9 MW move to the econ band at "
        "9 plants; the nested block equals the CAMPD running-hour p10 within 5 MW at Bonanza, "
        "Huntington, North Valmy and TS Power (scripts/probes/_nwppnext4_coal_census.py)."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-4"
    att["governance"]["notes"] = (
        "Keeper #10 recipe plus one gated fleet-construction field (owner card D3): the coal "
        "committed band is nested on the must-run band instead of stacked on it (rule 14, a "
        "units misread of a measured artifact). Offer-curve multipliers unchanged (sha256 "
        f"{prev.prev.prev.OFFER_CURVE_SHA256[:12]}...); nothing swept, nothing selected on a "
        "gate. The zero-LP prediction was that C4 gets WORSE (PRECOMMIT s3); solved as a "
        "structural repair under the owner's standing ruling. Short-gas outage windows still "
        "NOT armed."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned fac3d392."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "Only the coal committed-band sizes move (9 plants, 2,047.9 MW to the econ band); "
        "demand, offers and every other input are keeper #10's (G-DRIFT form 4, PRECOMMIT s4)."
    )
    disc.pop("rule_13_proximity", None)
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
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
