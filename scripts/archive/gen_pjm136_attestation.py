"""Write ``calibration_attestation.json`` for both pjm-136 A/B arms.

Both arms replay the ``2026-07-28-pjm-135-netpos-keeper`` recipe
(``pjm135_netpos_keeper_C``), so the governance posture and the
accepted-limitation ledger are the keeper's, inherited unchanged:

* **arm A** (``pjm136_control_A``) is the keeper recipe VERBATIM — no delta, and
  verified byte-identical to the committed keeper on the class hourlies
  (0.000000000 MW over 166,440 class-hours, each of 2023/2024/2025). Its
  attestation is therefore the keeper's, re-attested as the A/B control.
* **arm B** (``pjm136_lossurf_B``) adds ONE delta,
  ``pjm_zonal_loss_surface=true``, and therefore ONE ledger entry.

The delta adds **zero residual-identified degrees of freedom** (rule 23
``[R-DOF]``). The per-link receiving-side loss fraction is a pure function of
PJM's own published per-zone marginal-loss component: the frozen derive
(``scripts/data/derive_pjm_loss_surface.py``) reduces the measured MLC record to
the dimensionless delivery-factor deviation ``dev_z,m = sum(MLC_z)/sum(MEC)``,
and the LP consumes it as ``eps_(x->y),m = max(0, (dev_y-dev_x)/(1+dev_y))``.
No scale, no haircut, no blend, no percentile, no fitted anchor. So the ledger
gains a ``measured-physical`` entry and ``n_residual`` is unchanged — the same
posture as the already-ledgered PJM EAST / net-position interface cuts.

Usage:
    python scripts/gen_pjm136_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = (
    REPO / "results/calibration/pjm135_netpos_keeper_C/calibration_attestation.json"
)
ARM_A = REPO / "results/calibration/pjm136_control_A/calibration_attestation.json"
ARM_B = REPO / "results/calibration/pjm136_lossurf_B/calibration_attestation.json"

NEW_ENTRY = {
    "name": "PJM zonal marginal-loss surface (delivery-factor physics)",
    "where": "run_config.scenario_config.pjm_zonal_loss_surface",
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — the surface is derived from "
        "PJM's published per-zone LMP component record by a frozen derive "
        "(rule 23 [R-FROZEN-DERIVE]) whose only re-derivation trigger is a "
        "source-data change. Nothing was swept, and PREREG §4's no-feedback "
        "ceiling forbids ever applying a multiplier, percentile, haircut, "
        "blend, scale, floor, cap or scarcity exemption to it."
    ),
    "value": (
        "data.loss_surface.load_zone_month_deviation('PJM', year) -> "
        "transmission.apply_pjm_zonal_loss_links + build_pjm_link_loss -> "
        "dispatch.build_constraints(link_loss): each internal PJM link splits "
        "into a one-way pair whose receiving-end energy-balance coefficient is "
        "1 - eps, eps_(x->y),m = max(0, (dev_y,m - dev_x,m)/(1 + dev_y,m)). "
        "Realised 2025 fractions: ComEd->AEP_Ohio 4.16 %, AEP_Ohio->Dominion "
        "3.81 %, West_APS->SWMAAC 3.50 %, West_APS->Dominion 2.14 %, reverse "
        "legs 0.00-0.29 %. The only non-measured device is the 0.001 $/MWh "
        "loss-pair flow tiebreak (storage-eps class, rule 9 [R-EPSILON])."
    ),
    "source": (
        "PJM Data Miner 2 da_hrl_lmps, type=ZONE — all 21 transmission zones, "
        "hourly, 2023-2025 (data/raw/pjm-zonal-lmp/, gitignored bulk with a "
        "committed sha256 manifest; only the dimensionless derived surface "
        "data/raw/iso-specific-transmission/PJM_loss_surface.csv is committed). "
        "Transmission zones roll up to model zones load-weighted by the metered "
        "hrl_load_metered series through the canonical "
        "eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS crosswalk — every model zone "
        "is real, NONE interpolated. MEC identity checked uniform across zones "
        "per UTC interval to 0.000000 $/MWh."
    ),
    "forward_story": (
        "A marginal delivery-factor surface is a physical network property that "
        "regenerates for a forward year from the same published feed and "
        "responds to changed grid conditions (topology, loading, upgrades). "
        "Backcast train years read their own year's rows — the same-year "
        "measured-physical class as CEMS emission rates; every other year "
        "(all forecast years) falls back to the pooled year-0 rows, the stable "
        "multi-year property that regenerates from rolling history."
    ),
    "rule_13_admissibility": (
        "A published marginal-loss component is a physical/market input, not an "
        "outcome pinned to a residual: it enters the ENERGY BALANCE as a loss "
        "coefficient, so transported energy consumes MWh and the zonal duals "
        "separate by the measured delivery-factor ratio. Prices remain LP duals "
        "(rule 4 [R-DUALS]) — nothing is added to a price, and no volume is "
        "pinned to an actual. The measured quantity reproduced is the LOSS "
        "component only; the congestion component stays owned by the measured "
        "interface limits and the joint EAST / AP-South / net-position cuts "
        "(rule 19 [R-ONE-MECH])."
    ),
}

_SHARED_EVIDENCE = (
    "EVIDENCE (arms pjm136_control_A / pjm136_lossurf_B, all three years in one "
    "invocation, arms sequential): P1 the PRIMARY — the arm-B minus arm-A change "
    "in each internal link's mean dual difference reproduces the measured DA "
    "loss component in [0.5x, 1.5x] on 31 of 33 link-years (10/11, 11/11, "
    "10/11), and on all NINE Dominion-facing link-years (AEP_Ohio->Dominion "
    "1.00/0.77/0.76; West_APS->Dominion 0.99/0.93/0.84; SWMAAC->Dominion "
    "1.03/0.90/0.84). P2 the copper-plate BREAKS OUTRIGHT: the share of hours "
    "in which all eight PJM zones sit at ONE dual falls 96.4/97.6/97.0 % -> "
    "0.00 % in every year, against PJM's own measured 0.0 %. K2 zero slack and "
    "zero dump in BOTH arms, ALL years — the pre-registered principal risk, "
    "since losses consume 1.5-2.3 TWh/yr the fleet must make up. K3 net "
    "interchange moves +0.31/+0.18/+0.53 TWh, inside the 1.0 TWh tolerance. K5 "
    "arm A reproduces the committed keeper BYTE-IDENTICALLY (0.000000000 MW "
    "over 166,440 class-hours, each year). K6 solve cost +1.8 % overall "
    "(2,032 -> 2,070 s; 2025 was FASTER with the mechanism on). "
    "CARRIED CAVEATS, never dropped: (a) P1 misses 2 of 33 link-years — "
    "AEP_Ohio->ATSI 2023 (ratio -0.22 on a +0.140 measured loss) and "
    "West_APS->Central_PA 2025 (0.50x, at the band edge); (b) K1's sign clause "
    "FAILS on SWMAAC->Dominion 2025 (model +0.591 vs a measured TOTAL of "
    "-3.009) — the exact link-year the PREREG's exception table pre-declared "
    "with its numbers, because congestion there offsets loss, but the K1 "
    "sentence itself did not carve it out; (c) C3c's flip is THIN — 0.56x and "
    "0.54x against a 0.50x floor, i.e. 1 h of margin in 2024 and 2.5 h in 2025."
)

ATTESTED_BY_A = (
    "pjm-136 arm A (CONTROL) 2026-07-28: the 2026-07-28-pjm-135-netpos-keeper "
    "recipe replayed VERBATIM with no delta, as the A/B baseline for "
    "pjm_zonal_loss_surface. Verified byte-identical to the committed keeper on "
    "the class hourlies — 0.000000000 MW over 166,440 class-hours in each of "
    "2023/2024/2025 (PREREG-pjm136-zonal-loss-surface-2026-07-28.md K5), so the "
    "keeper's governance posture and accepted-limitation ledger carry over "
    "unchanged and this arm adds no parameter of any kind. Its purpose is to "
    "isolate the single delta; it is NOT a candidate."
)

ATTESTED_BY_B = (
    "pjm-136 PJM zonal marginal-loss surface 2026-07-28: the "
    "2026-07-28-pjm-135-netpos-keeper recipe replayed with a SINGLE delta, "
    "pjm_zonal_loss_surface=true. Chartered by "
    "FINDING-pjm136-zonal-dual-structure-2026-07-28.md and gated by "
    "PREREG-pjm136-zonal-loss-surface-2026-07-28.md, committed and pushed "
    "BEFORE any arm solved. "
    "DRIVER: the model's PJM cleared as a COPPER-PLATE. All eight zones sat at "
    "ONE dual in 96.4/97.6/97.0 % of hours and the three Dominion-facing links "
    "separated in 0.0 % of ALL 26,280 hours, while PJM's own day-ahead prices "
    "separate on every one of them in 100.0 % (mean max zonal spread $0.29/"
    "$0.63/$0.97 model vs $16.83/$18.06/$29.64 measured). The flow-space read "
    "shows why no flow lever could reach it: AEP_Ohio->Dominion is PINNED AT "
    "ITS BOUND in 84.4/90.7 % of hours at a shadow price of EXACTLY 0.000 — "
    "bound-but-priceless, a degenerate face the simplex re-routes across at "
    "zero cost (which is precisely what pjm-134 observed and pjm-135 measured). "
    "Exactly one internal link ever prices (ComEd->AEP_Ohio, 0.35 % of 2025). "
    "The loss component separates duals with NOTHING binding, carries 20/24/"
    "23 % of the measured DOM-vs-AEP gap, exceeds $1 on its own in 24/33/54 % "
    "of hours, and is sign-stable (Dominion positive 12/12 months, SWMAAC "
    "12/12, ComEd negative 12/12) — unlike the cancelling MISO pair-year that "
    "tripped miso-76's R2. Offline acceptance 12/12 pair-years in [0.5x, 1.5x] "
    "(ratios 0.95-1.07) BEFORE any solve. "
    + _SHARED_EVIDENCE
    + " RESULT ON THE CHARTERED DEFECT — and this is the first mechanism in the "
    "lineage that actually REALLOCATES ZONALLY rather than moving an ISO-wide "
    "level. Dominion CC_REGULAR +0.537/+1.410/+1.764 TWh, which is 115/82/78 % "
    "of the ISO-wide CC_REGULAR move (pjm-135 landed only ~15 % in Dominion), "
    "with ComEd — the measured upstream generation pocket — losing "
    "-0.978/-1.521/-1.512. Dominion CT_PEAKER +0.015/+0.096/+0.411 TWh while "
    "the ISO-wide CT total FALLS in 2024-25, i.e. pure reallocation toward "
    "Dominion. Gap closure vs actual: CC_REGULAR -9.885->-9.348, "
    "-8.089->-6.679 (17.4 %), -0.907->+0.857 (crosses over, |gap| 0.907->"
    "0.857); CT_PEAKER -6.671->-6.656, -7.396->-7.300, -7.128->-6.717 (5.8 %). "
    "The CT leg remains largely open, exactly as PREREG §4 pre-registered "
    "INERT-on-the-CT-leg as the expected outcome. "
    "Rule 1 [R-STRUCT]: the delta was chartered as structurally correct and "
    "zero-DOF before any result existed; the rubric movement is a consequence, "
    "not the justification, and PREREG §4's no-feedback ceiling was honoured — "
    "no multiplier, percentile, haircut, blend, scale, floor, cap or scarcity "
    "exemption was applied to the surface, and none may be."
)


def _write(dest: Path, attested_by: str, *, add_entry: bool) -> None:
    """Write one arm's attestation from the keeper's."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=attested_by)
    fp = att["free_parameters"]
    if add_entry:
        names = {e["name"] for e in fp["entries"]}
        if NEW_ENTRY["name"] not in names:
            fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["n_entries"] = len(fp["entries"])
    # Unchanged on purpose: the delta adds no residual-identified parameter.
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {dest.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )


def main() -> int:
    """Write both arms' attestations from the keeper's."""
    keeper_residual = json.loads(KEEPER.read_text())["free_parameters"]["n_residual"]
    _write(ARM_A, ATTESTED_BY_A, add_entry=False)
    _write(ARM_B, ATTESTED_BY_B, add_entry=True)
    print(f"keeper n_residual = {keeper_residual} (unchanged in both arms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
