"""Emit the NWPP-NEXT-10 calibration attestation for the exit-month-routing span bundle.

NWPP-NEXT-10 (PRECOMMIT
``docs/records/nwpp/PRECOMMIT-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md``) is
keeper #15's recipe (NWPP-NEXT-8) plus ``unit_outage_exit_ym_from_eia860``: a
retired unit's CAMPD post-exit darkness derates its own dated exit bin instead of
its surviving siblings (Colstrip 6076 units 1-2, 2020).

It reuses :mod:`gen_nwppnext8_attestation` and applies this lane's delta.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): EIA-860's retirement month and the
fleet's own dated exit bins.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext8_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "0ec8eb79e1202a8d1e815d2bf33d8722e5d5ffa9"
ARMED = "unit_outage_exit_ym_from_eia860"


def build(bundle: Path) -> dict:
    """Return the NWPP-NEXT-10 attestation built on the NWPP-NEXT-8 generator."""
    if ARMED not in base._ARMED:
        base._ARMED = (*base._ARMED, ARMED)
    base._SOURCES[ARMED] = (
        "Routing of the >= 5-day CAMPD unit-outage extract: each row's exit_ym is EIA-860's own "
        "per-unit retirement month (active vintage's Retired-and-Canceled sheet), stamped only "
        "where that month is one of its facility's dated exit bins (mid_vintage_exit_carry), and "
        "routing is live only at plants with a stamped row overlapping the solved year. "
        "PJM-NEXT-8's dated-bin accumulator is reused unchanged. Rule-19 double-count repair "
        "(the exit already zeroes the retiree); rule-14 physics: Colstrip 2020 available 5.855 "
        "-> 7.913 TWh against its own EIA-923 net 7.935."
    )
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-10"
    att["governance"]["notes"] = (
        "Keeper #15 recipe plus EIA-860 exit-month routing of the CAMPD outage layer (owner "
        "decision card 2026-09-29, 'Close lever 1, pivot' to the Colstrip 2020 availability "
        "lever). Offer-curve multipliers unchanged; nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "One config key (unit_outage_exit_ym_from_eia860) moves against keeper #15. Its "
        "zero-LP census moves only Colstrip 2020; the other six years are byte-inert by "
        "construction (G-DRIFT form 4, PRECOMMIT s3)."
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
