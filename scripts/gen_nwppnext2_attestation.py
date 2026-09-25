"""Emit the NWPP-NEXT-2 calibration attestation for ``results/calibration/nwppnext2_span``.

NWPP-NEXT-2 (PRECOMMIT ``docs/handoffs/PRECOMMIT-nwppnext2-psei-colstrip-2019-2025-2026-09-25.md``)
is the NWPP-NEXT keeper recipe unchanged, plus one data-construction repair
(``docs/handoffs/FINDING-nwppnext2-psei-basis-2026-09-25.md``):

* PSEI's Colstrip share, which NWMT already books in full, is removed from
  PSEI's EIA-930 net generation and demand
  (``constants.EIA930_REMOTE_GENERATION_DOUBLE_BOOKED``);
* PSEI's 2021-08 non-balance demand hours (interchange missing, ``D == NG``)
  are treated as missing readings and filled from FERC 714 by the existing gap
  guard; and
* the pool total and the zonal regroup share one member-demand builder.

It reuses :mod:`gen_nwppnext_attestation` and applies this lane's deltas.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): the subtracted series is PSEI's
own published column, and the flag is an exact equality on two published
columns.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext_attestation as prev  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwppnext2_span"


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-NEXT-2 attestation built on the NWPP-NEXT generator."""
    att = prev.build(bundle)
    att["lane"] = "NWPP-NEXT-2"
    att["switches"]["pool_member_gap_guard"]["source"] = (
        "FERC Form 714 Part III Schedule 2 PSEI hourly load (PUDL), reconciled to PSEI's "
        "same-year EIA-930 basis (after the double-booking repair) by the data's own clock "
        "offset and median ratio; net generation from PSEI's own EIA-930 fuel columns. "
        "Fires in 2019 (384 h, scale 1.0251), 2020 (8,659 h, scale 1.0619) and 2021 (the "
        "336 non-balance hours, scale 0.9973)."
    )
    att["switches"]["eia930_remote_generation_double_booked"] = {
        "value": {"PSEI": {"NG: COL": "NWMT"}},
        "where": (
            "market_sim.config.constants.EIA930_REMOTE_GENERATION_DOUBLE_BOOKED via "
            "data.eia930.frames._repair_published_extract (data path, not a ScenarioConfig field)"
        ),
        "identification": "measured-physical",
        "source": (
            "PSEI's own published EIA-930 NG: COL (its Colstrip share); NWMT NG: COL books all of "
            "Colstrip (14.167 TWh 2019 vs CAMPD ORIS 6076 gross 14.777). The 2019 PSEI demand "
            "excess over FERC 714 tracks the column hourly (r 0.927). Moves 2019 (-4.48 TWh "
            "requirement) and 2020 (-2.15 TWh); 2022-2025 byte-identical."
        ),
    }
    att["switches"]["pool_nonbalance_demand_mask"] = {
        "value": True,
        "where": "market_sim.data.eia930.frames._mask_unbalanced_demand (data path)",
        "identification": "measured-physical",
        "source": (
            "EIA-930 member hours with Total interchange (Adjusted) missing and Demand (Adjusted) "
            "== Net generation (Adjusted): PSEI 2021-08-02..16, 336 h, no other member or year. "
            "Energy-neutral for the LP (the served export is sum(NG - D))."
        ),
    }
    att["governance"]["notes"] = (
        "NWPP-NEXT keeper recipe plus one measured-input repair (rules 13/14/19): PSEI's "
        "double-booked Colstrip share removed, its 2021-08 non-balance demand hours filled from "
        "FERC 714, one member-demand builder for the pool and its zonal regroup. Offer-curve "
        f"multipliers unchanged (sha256 {prev.OFFER_CURVE_SHA256[:12]}...); nothing swept, "
        "nothing selected on a gate. Short-gas outage windows still NOT armed."
    )
    disc = att["disclosures"]
    years = json.loads((bundle / "meta.json").read_text())["years"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned 2b8a6bc3."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "2022-2025 LP inputs are byte-identical to the keeper's (array-level old/new diff), so "
        "they read as a drift check; 2019/2020 lose the phantom Colstrip requirement; 2021 moves "
        "336 hours of zonal split only."
    )
    disc["psei_2021_august_defect"] = (
        "REPAIRED: the 336 non-balance hours are filled from FERC 714 (+0.570 TWh PSEI demand, "
        "matching export change; system requirement unchanged)."
    )
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
