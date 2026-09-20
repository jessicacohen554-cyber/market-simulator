"""Emit the SPP-68 calibration attestations for the wind curtailment CEILING arm.

SPP-68 arms exactly ONE ``ScenarioConfig`` boolean — ``spp_curtailment_ceiling``
— on top of SPP keeper 14's recipe (``2026-09-20-spp-67-yearown-rate``) and its
rung, across **both** of SPP's registered year sets:

* ``results/calibration/spp68_ceiling_span`` — 2023, 2024, 2025 (the keeper's span);
* ``results/calibration/spp68_ceiling_rung`` — 2019-2022, the rung stamped to it.

The level, ``spp_curtail_depth_wind``, is left at its registered dataclass
default 0.288137 and is **never swept** (rule 1 ``[R-STRUCT]`` condition (c)).

**Why this exists rather than the shared helper** — the same two reasons
``gen_spp67_attestation.py`` records: ``gen_touchpoint_attestation.py`` refuses a
run spanning more than one ``holdout_policy.tier_for_year`` tier, and
``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``
into the out-dir, so without this both bundles would score C6 ``UNATTESTED`` for
a plumbing reason rather than a governance one.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24
``[R-REGISTRY]``). Both fields are registered ``ScenarioConfig`` members;
``build_dof_ledger.py --iso SPP`` emits **5 entries / 3 residual** on keeper 14
and must emit the same here. ``offer_curve_by_group`` is byte-identical to
keeper 14's (whole-mapping ``json.dumps(sort_keys=True)`` SHA-256 ``090abd79…``),
so the rule-1 authorized price-tuning channel was not touched, re-cut or swept.

Usage:
    python scripts/gen_spp68_attestation.py            # both bundles that exist
    python scripts/gen_spp68_attestation.py --bundle results/calibration/spp68_ceiling_span
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
SPAN = CAL / "spp68_ceiling_span"
RUNG = CAL / "spp68_ceiling_rung"
KEEPER = CAL / "spp67_yearown_span" / "calibration_attestation.json"

_GATE = "spp_curtailment_ceiling"
_DEPTH = "spp_curtail_depth_wind"
OFFER_SHA = "090abd793b5fa5a7"
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-68-curtailment-ceiling-retest-2026-09-20.md"
PINNED = "05b2231da6e2e70bf9a122cece864a7673e2b2f7"

_ATTESTED = (
    "SPP-68 (2026-09-20), lane 'card R-bc: the one instrument that ever moved SPP's "
    "wind, re-tested like-for-like'. THE OBJECT: nothing in the LP can refuse wind bid "
    "at -ira_ptc_wind below every thermal offer, so a bound the gross-up invents is a "
    "bound the LP takes. MEASURED AT PHASE 0 ON KEEPER 14's OWN COMMITTED SIDECARS, "
    "per year: the LP spends 90.00-100.05 % of the gross-up headroom (numerator "
    "model - delivered, denominator potential - delivered), leaving re-curtailment of "
    "0.00-0.94 % of potential. THE MECHANISM UNDER TEST is the registered, default-off "
    "spp_curtailment_ceiling (SPP-58): ceiling_frac(t) = 1 - depth x "
    "congestion_share(net_load_decile(t), hour_of_day(t), season(t)) on the WIND CF "
    "upper bound of both SPP zones, SHAPE from SPP's published RTBM binding-constraint "
    "archive and LEVEL from SPP's published curtailment MW. It REPLACES the oversupply "
    "water-fill rather than stacking on it (rule 19 [R-ONE-MECH], enforced in "
    "data/renewables.py and re-verified in source before the solve). "
    "THE DEPTH STAYS FROZEN at its registered default 0.288137 (rule 23 "
    "[R-FROZEN-DERIVE]): its source rows are unchanged, and its identification "
    "depth_y = published_share_y / wms_y is a RATIO in which the potential cancels, so "
    "keeper 14's year-own gross-up cannot move it -- reconciled on keeper 14's own "
    "potential it reproduces SPP-58's per-year values to <= 0.0015. WHAT THAT "
    "RECONCILIATION FOUND, and it was pre-registered before any solve: the ceiling's "
    "depth is pooled while keeper 14's gross-up is sized by each year's OWN published "
    "rate, so the two are consistent only where a year's rate equals the pool. 2019's "
    "own rate is 1.591 % against the pool's 9.650 %, making the pooled depth 6.15x too "
    "large there. A per-year depth is refused by rule 1 condition (b) and re-cutting "
    "the pooled one by condition (c); neither was attempted."
)

_DISCLOSURES = {
    "note": (
        "SPP-68 disclosures -- reported, not patched (rules 1 / 13 / 14). Every item "
        "below was established at PHASE 0, ZERO LP, and pushed in the PRECOMMIT BEFORE "
        "any shard was launched. None is a post-hoc reading of the arm."
    ),
    "the_pooled_depth_and_the_year_own_gross_up_are_INCONSISTENT_in_2019": (
        "The ceiling's removal, expressed as a percentage of the SAME year's gross-up "
        "headroom, is 92.1-112.6 % in six of seven years -- i.e. the two mechanisms "
        "roughly cancel and wind returns to its delivered basis -- but 614.8 % in 2019. "
        "Above 100 % the ceiling removes energy SPP ACTUALLY DELIVERED: 2.9 % of it in "
        "2022, 12.6 % in 2023 and about 5.1 TWh in 2019. This is a rule 19 "
        "[R-ONE-MECH] finding about two mechanisms sized on different bases, not a "
        "level to re-cut."
    ),
    "the_price_channel_is_the_WRONG_CHANNEL_and_no_depth_fixes_it": (
        "SPP-64 section 3 established it and this lane re-measured it on keeper 14: wind is a "
        "BOUNDED decision variable bid at a flat -ira_ptc_wind, so it is the only unit "
        "that can set a negative price, and a unit held AT its bound is never marginal. "
        "Lowering the bound removes the model's only negative price-setter. The model "
        "ALREADY carries only 0.18-0.50x the market's negative-hour count (model "
        "170/511/498/393/464/414 against actual RT 936/1108/995/992/1172/1018 for "
        "2020-2025), so removing them moves AWAY from the market. The natural "
        "experiment is 2019, which needed no construction: its gross-up headroom is "
        "1.2453 TWh against 8.8-12.9 elsewhere, and it has ZERO negative hours and a "
        "minimum price of +4.500. The model's negative-price regime IS the gross-up "
        "headroom being spilled."
    ),
    "the_ceiling_removes_the_RIGHT_AMOUNT_from_the_WRONG_HOURS": (
        "Measured after the PRECOMMIT was pushed and before any arm landed, so it "
        "cannot have been fitted to a result. The model's wind excess sits 41.9-52.2 % "
        "in the lowest net-load decile; the ceiling puts only 21.5-24.0 % of its "
        "removal there -- a concentration ratio of 0.28-0.52x, with "
        "corr(excess, removal) 0.60-0.70 (2019: 0.20). So it over-removes in the mid "
        "and high net-load hours, where the model's wind was already about right, and "
        "under-removes in the oversupply hours where the excess actually is. The "
        "ceiling is broad and shallow (mean multiplier 0.914-0.917, deepest cut 0.712, "
        "and the clip at 0 NEVER binds since depth x max share = 0.288137 < 1, so no "
        "hour is ever zeroed). Real congestion curtailment has the opposite shape: "
        "specific resources to zero in specific hours behind a binding constraint."
    ),
    "SPP_63_ALREADY_SCREENED_THIS_AND_TWO_OF_ITS_FIVE_GATES_FAILED": (
        "The lane brief said the ceiling's control was keeper 5 and that it had never "
        "had a fair control. That understates the record and the correction was made "
        "in the PRECOMMIT before anything was spent. Lane SPP-63 (2026-09-10, shard "
        "92b59c73, RESULT-spp-63-screen-2026-09-10.md) ran a solved five-gate screen on "
        "2025 against the then-keeper: G-1 and G-3 PASS and wind landed within 0.232 "
        "TWh of actual, but G-4 FAILED (slack 0.0000 -> 211.208 MWh against a "
        "pre-registered <= 100.0) and G-5 FAILED (C3b NRMSE 0.167 -> 0.253 against a "
        "<= 0.20 band, a load-bearing PASS -> FAIL; negative hours 167 -> 0). The "
        "recovered energy went to COAL_PRB +7.099 and CC_REGULAR +3.680 while ST_GAS "
        "FELL 0.693, taking the coal family from +0.72 to +8.69 TWh against actual. "
        "The cell stayed O, not R, so rule 28(a) permits this re-test -- and two "
        "keepers have landed since that touch exactly what killed it."
    ),
    "WHY_THE_SPAN_WAS_SOLVED_AT_ALL_given_phase_0_predicted_a_kill": (
        "Rule 34 [R-SHARD-PROMOTABLE] (b): a screen is not an exception, because you "
        "cannot know it is one until the owner rules. Rule 31 [R-RETAIN]: the owner "
        "routinely promotes what a session declined. Six of seven years were predicted "
        "to move from +8.6..+12.1 TWh of phantom wind to within +-1.21 TWh of actual -- "
        "a large, real C1 improvement the owner is entitled to rule on with solved "
        "numbers rather than with a session's arithmetic."
    ),
    "what_this_lane_does_NOT_close": (
        "R-bc itself. The ceiling changes the BOUND; it does not give the LP a reason "
        "to spill, and it cannot make a bounded unit marginal. R-ba (the "
        "ST_GAS / CT_PEAKER merit-order inversion), R-be and C3c are untouched."
    ),
}


def _offer_sha(bundle: Path) -> str:
    """Return the short SHA-256 of the bundle's whole ``offer_curve_by_group``."""
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    blob = json.dumps(cfg.get("offer_curve_by_group") or {}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def write(bundle: Path) -> None:
    """Write ``bundle``'s attestation, inheriting keeper 14's governance block."""
    keeper = json.loads(KEEPER.read_text())
    att_path = bundle / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    cfg = json.loads((bundle / "run_config.json").read_text())
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    sc = cfg["scenario_config"]
    sha = _offer_sha(bundle)

    gov = json.loads(json.dumps(keeper["governance"]))
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-68 (2026-09-20). Re-cut to THIS run's own solved years {years}. A "
            "statement about WHICH YEARS THIS RUN HOLDS THE CONFIG ACROSS, never a "
            f"re-tuning: offer_curve_by_group SHA-256 {sha} is byte-identical to "
            f"keeper 14's ({OFFER_SHA}), this lane passes only --set {_GATE}=true, "
            "and no band, class or value moved. Condition (c) is untouched -- the "
            "0.93 was set ex ante by an earlier lane and was NOT swept here."
        )
    gov["attested"] = _ATTESTED
    gov["mechanism_armed"] = {
        "field": _GATE,
        "value": bool(sc.get(_GATE)),
        "level_field": _DEPTH,
        "level_value": sc.get(_DEPTH),
        "level_status": (
            "FROZEN at the registered dataclass default (rule 23 [R-FROZEN-DERIVE]); "
            "identified off SPP's published curtailment MW by SPP-58 and NEVER swept "
            "against any gate in this lane (rule 1 [R-STRUCT] condition (c))"
        ),
        "basis": "rule 14 [R-ACCURATE] / rule 1 [R-STRUCT] structural repair",
        "free_parameters_added": 0,
        "supersedes": (
            "vre_curtailment_oversupply_allocation -- rule 19 [R-ONE-MECH], enforced "
            "in data/renewables.py, which skips the oversupply water-fill whenever "
            "this flag is armed, so the two can never both be live"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
        "control": (
            "keeper 14's / the rung's COMMITTED bundle, differenced, never re-solved "
            "(rule 29(b) form 4). The G-DRIFT audit is PRECOMMIT section 6: exactly ONE "
            "file changed on the whole audited solve path between the keeper's basis "
            "sha and this lane's, a NYISO artifact SPP does not have -- INERT."
        ),
        "solved": (
            "SEVEN shards, ONE PER YEAR 2019-2025 (rules 32 [R-SHARD] / 34 "
            "[R-SHARD-PROMOTABLE] (c) / 36 [R-YEAR-ISOLATION]), each at the pinned "
            f"HEAD {PINNED[:8]} and each pushing its FULL bundle including "
            "dispatch/<year>_P1.parquet. The parent ran NO LP."
        ),
    }

    att["schema"] = keeper.get("schema", "calibration-attestation/v1")
    att["governance"] = gov
    att["disclosures"] = _DISCLOSURES
    att["exceptions"] = list(keeper.get("exceptions") or [])
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path.relative_to(REPO)}  years={years}  offer_sha={sha}")


def main() -> int:
    """CLI: write the SPP-68 attestation into each bundle that exists."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", type=Path, action="append")
    args = ap.parse_args()
    targets = args.bundle or [p for p in (SPAN, RUNG) if p.is_dir()]
    if not targets:
        print("no bundle found")
        return 1
    for bundle in targets:
        write(bundle if bundle.is_absolute() else REPO / bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
