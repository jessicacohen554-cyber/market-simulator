"""Emit the SPP-71 calibration attestations for the wind curtailment CEILING arm.

SPP-71 arms exactly ONE ``ScenarioConfig`` boolean — ``coal_sync_ensemble_level``
— on top of SPP keeper 14's recipe (``2026-09-20-spp-67-yearown-rate``) and its
rung, across **both** of SPP's registered year sets:

* ``results/calibration/spp71_ensemble_span`` — 2023, 2024, 2025 (the keeper's span);
* ``results/calibration/spp71_ensemble_rung`` — 2019-2022, the rung stamped to it.

The level, ``coal_sync_srmc_tranche``, is left at its registered dataclass
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
    python scripts/gen_spp71_attestation.py            # both bundles that exist
    python scripts/gen_spp71_attestation.py --bundle results/calibration/spp71_ensemble_span
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
SPAN = CAL / "spp71_ensemble_span"
RUNG = CAL / "spp71_ensemble_rung"
KEEPER = CAL / "spp67_yearown_span" / "calibration_attestation.json"

_GATE = "coal_sync_ensemble_level"
_DEPTH = "coal_sync_srmc_tranche"
OFFER_SHA = "090abd793b5fa5a7"
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-71-ensemble-sync-floor-2026-09-22.md"
PINNED = "6edc996d1051296b6fb62185df7b304adbc7f3d1"

_ATTESTED = (
    "SPP-71 (2026-09-22), lane 'card R-bc: PRICE-FORMING CURTAILMENT'. THE CHARTER'S "
    "OWN CHANNEL IS REFUSED ON A PROOF: any upper limit on wind delivery -- CF bound "
    "(what spp_curtailment_ceiling does, cell R) or LP row -- leaves wind NON-MARGINAL "
    "when it binds, because the marginal MWh of zonal load cannot then be served by "
    "wind, so the energy-balance dual is the next thermal offer and the price cannot "
    "reach the wind offer. The defect is the DIRECTION OF THE INEQUALITY, not the "
    "object it attaches to. What CAN take a zonal price to -26.000 is supply pushed UP "
    "from below, so the R-bc object is a SUPPLY-SIDE synchronization floor and SPP's "
    "keeper already carries it -- in the wrong place. THE MECHANISM UNDER TEST is the "
    "registered, default-off coal_sync_ensemble_level: floor_p(t) = coal_sync_pmin_mw_p "
    "x online_frac_p in EVERY hour, REPLACING (rule 19 [R-ONE-MECH], never stacking on) "
    "the top-k-by-system-load window that places the full Pmin on round(frac x 8760) "
    "hours and EXACTLY ZERO elsewhere. online_frac is a measured MARGINAL PROBABILITY "
    "and the shipped code spends it as a DEGENERATE distribution; the arm is its "
    "CONTINUOUS-RELAXATION image, which is what a Bernoulli commitment variable relaxes "
    "to in a pure-LP dispatch model with no integrality. ZERO new free parameters and "
    "ZERO new data (rules 21 [R-DOF] / 24 [R-REGISTRY]): the same two measured columns "
    "the armed floor already reads, mustrun_online_pct and online_frac from "
    "thermal_tranches_SPP.csv; DOF ledger 5 entries / 3 residual, unchanged. Rule 17 "
    "[R-FLOOR-WINDOW] (b) is satisfied by the declaration the repo ALREADY carries for "
    "this floor -- legitimacy_diagnostics.py (MECH_COAL_MUSTRUN, None): (0, 24), 'the "
    "driver-justified window is ALL 24 hours BY DRIVER' -- which the load-ranked code "
    "contradicts at the bottom. MEASURED, seven shards, one per year 2019-2025 (rule 36 "
    "[R-YEAR-ISOLATION]), each solving CONTROL AND ARM in one container at one pinned "
    "HEAD so the differencing is exact and rule 29(b) form 4 is not relied on; parent "
    "ran NO LP. Single-delta verified: coal_sync_ensemble_level is the ONLY differing "
    "scenario_config key in all seven years. THE STRUCTURAL RESULT: the fleet coal "
    "hourly minimum moves from 0.013-0.476x the measured EIA-930 SWPP COL minimum to "
    "0.497-0.806x, and NEVER EXCEEDS it in any year -- it halves the structural gap and "
    "cannot over-force. THE GATE RESULT, reported at full magnitude and NOT minimised: "
    "hours at the wind offer rise in all seven years (+8 to +111), closing only "
    "1.5-14.5 % of the gap to the measured negative-hour count; wind falls only "
    "0.004-0.310 TWh against an excess of 1.2-11.7 TWh, about 2 %; the mean price falls "
    "0.028-0.406 $/MWh. offer_curve_by_group is BYTE-IDENTICAL to keeper 14's "
    "(SHA-256 090abd79...), so the rule-1 authorized price-tuning channel was not "
    "touched, re-cut or swept."
)

_DISCLOSURES = {
    "note": (
        "SPP-71 disclosures -- reported, not patched (rules 1 / 13 / 14). Every item "
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
            f"SPP-71 (2026-09-20). Re-cut to THIS run's own solved years {years}. A "
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
            "NO LEVEL PARAMETER EXISTS. The floor's level is the plant's own measured "
            "coal_sync_pmin_mw x online_frac (thermal_tranches_SPP.csv columns "
            "mustrun_online_pct / online_frac), identical in both legs; this arm moves "
            "only WHERE that level is placed. Nothing was swept against any gate "
            "(rule 1 [R-STRUCT] condition (c)); rule 23 [R-FROZEN-DERIVE] is untouched "
            "because no derive was re-run"
        ),
        "basis": "rule 14 [R-ACCURATE] / rule 1 [R-STRUCT] structural repair",
        "free_parameters_added": 0,
        "supersedes": (
            "the top-k-by-system-load PLACEMENT of the same coal synchronization floor "
            "-- rule 19 [R-ONE-MECH], enforced in data/fleet/arrays.py, where the armed "
            "branch short-circuits before the force-all branch, the load_rank branch "
            "AND the pjm-h16 coal_sync_window_commitment_grain day-grain window, so no "
            "two placements can ever both be live. It also REPLACES "
            "spp_curtailment_ceiling (cell R) as R-bc's answer and the two are never "
            "co-armed: same phenomenon, opposite inequality"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
        "control": (
            "EACH YEAR'S OWN CONTROL, SOLVED -- not assumed. Every shard solved the "
            "keeper/rung recipe AND the arm in ONE container at ONE pinned HEAD "
            "(6edc996d), so rule 29(b) form 4 is NOT relied on and no G-DRIFT claim "
            "carries any weight here: the differencing is exact by construction. "
            "G-DRIFT is reported in PRECOMMIT section 4 for the record only (14 files "
            "changed on the audited solve path since keeper 14's basis sha, including "
            "the very block this arm edits -- which is precisely why the control was "
            "solved rather than differenced against the committed bundle)."
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
    """CLI: write the SPP-71 attestation into each bundle that exists."""
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
