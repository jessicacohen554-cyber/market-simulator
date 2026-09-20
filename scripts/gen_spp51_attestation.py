"""Emit the SPP-51 calibration attestations for the coal synchronization floor.

SPP-51 arms exactly TWO existing, already-registered ``ScenarioConfig`` booleans
on top of SPP keeper 12's recipe (``2026-09-16-spp-42-commitment-feasibility``),
across **both** of SPP's registered year sets:

* ``results/calibration/spp51_syncfloor_span`` — 2023, 2024, 2025 (keeper 12's span);
* ``results/calibration/spp51_syncfloor_rung`` — 2019-2022, the rung SPP-49 registered.

The pair is ``coal_mustrun_online_pmin`` + ``coal_sync_srmc_tranche``: the coal
min-load band is re-sized from the all-hours available-CF ``mustrun_pct`` to the
MEASURED online-net-MW synchronization Pmin (``thermal_tranches_SPP.csv``
``mustrun_online_pct``), split by the measured take-or-pay share, and both
layers are forced on via ``coal_sync_pmin_mw -> FleetArrays.min_gen`` so coal
holds synchronized instead of price-following to zero.

**Why this exists rather than the shared helper** — the identical two reasons
``gen_spp42_attestation.py`` records: ``gen_touchpoint_attestation.py`` refuses a
run spanning more than one ``holdout_policy.tier_for_year`` tier (a guard SPP-40
recorded as STALE after ``[R-HOLDOUT]``'s removal), and ``replay_keeper
--out-dir`` does not propagate ``calibration_attestation.json`` into the out-dir,
so without this both bundles would score C6 ``UNATTESTED`` for a plumbing reason
rather than a governance one.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` /
24 ``[R-REGISTRY]``). Machine-confirmed, not asserted: ``build_dof_ledger.py
--iso SPP`` at HEAD emits **5 entries / 3 residual** on both bundles, with the
same five entry names as keeper 12's own ledger. ``offer_curve_by_group`` is
byte-identical to keeper 12's in both bundles (whole-mapping
``json.dumps(sort_keys=True)`` SHA-256 ``090abd79…``), so the rule-1 authorized
price-tuning channel was not touched, re-cut or swept.

Usage:
    python scripts/gen_spp51_attestation.py            # both bundles
    python scripts/gen_spp51_attestation.py --bundle results/calibration/spp51_syncfloor_span
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
SPAN = CAL / "spp51_syncfloor_span"
RUNG = CAL / "spp51_syncfloor_rung"
KEEPER = CAL / "spp42_span_a" / "calibration_attestation.json"

_GATES = ("coal_mustrun_online_pmin", "coal_sync_srmc_tranche")
OFFER_SHA = "090abd793b5fa5a7"

_ATTESTED = (
    "SPP-51 (2026-09-20), lane 'R-bc: curtailment as an LP constraint whose dual "
    "reaches the zonal price'. The chartered object was KILLED AT PHASE 0 with no "
    "LP spent — a per-hour wind cap row W[z,t] <= K[z,t] defines the IDENTICAL "
    "feasible region as lowering the bound, so its dual never enters the "
    "energy-balance price; it is the SPP-63 ceiling renamed. The lane then routed "
    "to the object SPP-51c had already root-caused ('the binding limb is R-2, the "
    "thermal-commitment floor') and armed it through two EXISTING measured gates. "
    "PRECOMMIT + window ADDENDUM pushed BEFORE any solve (f80de3e1 / 0a7f5c06); "
    "record docs/handoffs/RESULT-spp-51-coal-sync-floor-2026-09-20.md."
)


def _offer_sha(bundle: Path) -> str:
    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    blob = json.dumps(sc.get("offer_curve_by_group"), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def build(bundle: Path) -> dict:
    """Return the SPP-51 attestation for one bundle: keeper 12's ledger + this run's governance."""
    att_path = bundle / "calibration_attestation.json"
    att = (
        json.loads(att_path.read_text())
        if att_path.exists()
        else json.loads(KEEPER.read_text())
    )
    fp = att["free_parameters"]
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    for g in _GATES:
        if sc.get(g) is not True:
            raise RuntimeError(f"{bundle.name}: {g} is not True — this is not the arm")
    got = _offer_sha(bundle)
    if got != OFFER_SHA:
        raise RuntimeError(
            f"{bundle.name}: offer_curve_by_group SHA-256 {got} != keeper 12's "
            f"{OFFER_SHA} — the authorized price-tuning channel MOVED, which this "
            "lane does not do."
        )

    gov = att["governance"]

    # Rule 1 [R-STRUCT] (b): `years_held` is an EXACT SET EQUALITY against the
    # run's OWN scored years in calibration_verdict._authorized_tuning_finding.
    # Re-cut it off the bundle's dispatch parquets so it cannot drift.
    apt = gov["authorized_price_tuning"]
    solved_years = sorted(
        int(f.name.split("_")[0])
        for f in (bundle / "dispatch").glob("*_P1.parquet")
        if f.name.split("_")[0].isdigit()
    )
    if not solved_years:
        raise RuntimeError(f"no dispatch/<year>_P1.parquet under {bundle}")
    apt["years_held"] = solved_years
    apt["years_held_basis"] = (
        "SPP-51 (2026-09-20). Re-cut to THIS run's own solved years, read off "
        "dispatch/<year>_P1.parquet. A statement about WHICH YEARS THIS RUN HOLDS "
        f"THE CONFIG ACROSS, never a re-tuning: offer_curve_by_group SHA-256 "
        f"{OFFER_SHA} is byte-identical to keeper 12's, this lane passes only "
        f"--set {_GATES[0]}=true --set {_GATES[1]}=true, and no band, class or "
        "value moved. Condition (c) is untouched — the 0.93 was set ex ante by an "
        "earlier lane and was NOT swept here."
    )

    gov["dof_inherited_from"] = "spp42_span_a (SPP keeper 12)"
    gov["dof_inheritance_basis"] = (
        "SPP-51 arms TWO booleans that select between two ALREADY-COMMITTED "
        "MEASURED COLUMNS of thermal_tranches_SPP.csv (mustrun_online_pct in "
        "place of mustrun_pct) and force the resulting band on via "
        "coal_sync_pmin_mw -> min_gen, scaled by the measured online_frac and "
        "split by the measured take-or-pay share. NO threshold, share, "
        "multiplier, length, artifact, loader or CLI number is introduced. "
        "Machine-confirmed rather than asserted: build_dof_ledger.py --iso SPP at "
        "HEAD emits 5 entries / 3 residual on this bundle, the same five entry "
        "names as keeper 12's. Rule 23 [R-FROZEN-DERIVE]: thermal_tranches_SPP.csv "
        "is READ, never regenerated — no derive script ran in this lane."
    )
    gov["attested_by"] = _ATTESTED

    sw = gov.setdefault("measured_input_switches", {})
    sw["coal_mustrun_online_pmin"] = {
        "value": True,
        "basis": (
            "Sizes the coal must-run band to the MEASURED online-net-MW "
            "synchronization Pmin (thermal_tranches_SPP.csv mustrun_online_pct, "
            "derived from SPP's own CAMPD unit conduct) instead of the all-hours "
            "available-CF mustrun_pct. Rule 14 [R-ACCURATE]: 12 of SPP's 24 "
            "status=ok COAL plants carry mustrun_pct = 0.0, i.e. NO min-load band "
            "at all, while CAMPD says every one of the 24 holds 7.9-60.0 % of "
            "nameplate when synchronized. Band 2,855.2 -> 4,090.3 MW."
        ),
    }
    sw["coal_sync_srmc_tranche"] = {
        "value": True,
        "basis": (
            "Splits that band into a fuel-free contracted _mustrun tranche and a "
            "full-SRMC _sync tranche by the MEASURED take-or-pay share, and forces "
            "both on (coal_sync_pmin_mw -> FleetArrays.min_gen, scaled by the "
            "measured online_frac) so coal holds synchronized at min-load instead "
            "of price-following to zero. Inert without the first gate "
            "(fleet/assembly.py conjoins them)."
        ),
    }

    gov["mechanism_basis"] = (
        "Rules 1 [R-STRUCT] / 14 [R-ACCURATE], NEVER the residual. The model took "
        "SPP's entire PRB coal fleet — must-run band included — to EXACTLY 0.0 MW "
        "for 151-290 h/yr in six of seven registered years, at a mean price of "
        "-$22.5..-$25.4, while SPP's real PRB fleet never falls below 8.1-17.5 % of "
        "its own annual max in ANY year. The arm ELIMINATES that state (151-290 -> "
        "0 h in every year). The lane's PRECOMMIT predicted BEFORE the solve that it "
        "would close only ~8.5 % of C1 and pre-committed to keeping it regardless; "
        "it closes 4.4 %, and the run is kept on the structural ground, not the fit."
    )

    gov["iso_scope"] = (
        "Rule 25 [R-ISO-SCOPE]: both gates ship default False and are armed here "
        "per-run via the CLI only. NO code was changed by this lane, so every other "
        "ISO's keeper is byte-identical BY CONSTRUCTION. PJM and MISO arm members of "
        "this family in their own runs; rule 28(d) means neither verdict transferred "
        "— SPP derived its band from its OWN thermal_tranches_SPP.csv."
    )
    gov["registry"] = (
        "Rule 24 [R-REGISTRY]: both fields were already registered in ScenarioConfig "
        "with CLI flags (--coal-mustrun-online-pmin / --coal-sync-srmc-tranche) and "
        "appear in this bundle's run_config.json. No env-var knob, no hardcoded "
        "per-plant dict, no getattr fallback literal."
    )
    gov["one_mechanism"] = (
        "Rule 19 [R-ONE-MECH]: this is SPP's FIRST commitment floor — it replaces "
        "nothing and stacks on nothing. The control bundles carry NO coal_mustrun "
        "D-2 row at all, and keeper 12 ships reliability_floor=false, "
        "class_commitment_overrides={}, reliability_floor_overrides={} and "
        "spp_gas_commitment_bridge=false. It is RECONCILED with the already-armed "
        "vre_curtailment_oversupply_allocation water-fill exactly as SPP-51c "
        "required: the allocation concentrates the headroom into the low-net-load "
        "hours and this floor is what stops the LP absorbing it there."
    )

    att["disclosures"] = {
        "note": (
            "SPP-51 disclosures — reported, not patched (rules 1 / 13 / 14). "
            "Supersedes SPP-62's inherited block; every item below is a COST of this "
            "arm stated at full magnitude."
        ),
        "it_does_not_close_C1_and_this_was_predicted_before_the_solve": (
            "The arm closes only 4.4 % of SPP's mean fossil miss (-8.400 -> -8.029 "
            "TWh over seven years). The PRECOMMIT predicted ~8.5 % ex ante and "
            "pre-committed to keeping the mechanism regardless of the residual."
        ),
        "the_coal_comes_from_GAS_not_from_WIND": (
            "Mean coal +2.205 TWh against mean wind only -0.350 TWh: 84 % of the "
            "coal gain is displaced gas, and the wind excess this lane was chartered "
            "on moves just 3.4 % of its +10.144 TWh. In 2019 wind moves EXACTLY "
            "0.000. So the arithmetic identity between SPP's wind excess and its "
            "fossil miss is NOT converted by a thermal floor, and the "
            "vre_reference_rate_curtailment_grossup object stays open."
        ),
        "ST_GAS_gets_WORSE_in_every_year": (
            "SPP's most persistent C1 row degrades in all seven years (-4.588 -> "
            "-4.662, -4.891 -> -5.183, -3.943 -> -4.048, -5.168 -> -5.324, -5.062 -> "
            "-5.281, -7.115 -> -7.370, -8.655 -> -8.954 TWh). The ST_GAS/CT_PEAKER "
            "merit-order inversion (successor R-ba) is untouched and is now the "
            "strongest remaining C1 candidate."
        ),
        "summed_C1_error_RISES_in_three_of_seven_years": (
            "Sum of |class error| improves in 2019/2020/2023/2024 and WORSENS in "
            "2021 (+1.641), 2022 (+3.221) and 2025 (+1.903) — exactly the three "
            "years COAL_PRB was already LONG, where adding ~2.2 TWh of coal "
            "overshoots further."
        ),
        "two_criteria_move_the_wrong_way": (
            "C3a |error| improves in 6 of 7 years but WORSENS in 2022 (-0.9 % -> "
            "-4.4 %). C3b improves in 6 of 7 but WORSENS in 2021 (0.213 -> 0.245). "
            "NO criterion flips status in either direction in any year."
        ),
        "the_structural_repair_is_INCOMPLETE": (
            "The arm's coal minimum reaches only 0.15-1.93 % of its own annual max "
            "against the real SPP PRB fleet's 8.1-17.5 %. It removes the IMPOSSIBLE "
            "state without reproducing the OBSERVED one. Root cause is measured and "
            "routed as successor R-bd: fleet/arrays.py:2884-2903 ranks the floor's "
            "top-k window on system LOAD and no SPP plant reaches the 0.99 "
            "_COAL_SYNC_FORCE_ALL override, so the aggregate floor is 0.840 GW in "
            "the lowest-load decile and 0.000 GW in the lowest-load hour. The "
            "physically right driver is NET load. NOT repaired here because that "
            "function is shared and PJM/MISO runs arm this family (rule 25)."
        ),
        "the_price_floor_below_-26_remains_unreachable": (
            "The model's minimum price is EXACTLY -ira_ptc_wind = -26.000 in every "
            "year and both zones, with dump_cost ~ 26.001 capping it; the market "
            "goes below -26 in 22-118 h/yr. No floor, ceiling or allocation reaches "
            "this (successor R-be)."
        ),
        "negative_price_hours_still_fall_SHORT_of_the_market": (
            "The arm roughly DOUBLES them (+129 to +268) but lands at 170-518 "
            "against an actual RT 547-1,172. The direction is right and the level is "
            "not yet."
        ),
        "the_lane_scored_two_of_its_OWN_predictions_WRONG": (
            "P-1 understated the coal gain by 2.6x (+0.849 predicted, +2.205 "
            "measured, outside the stated range in every year). And the window "
            "ADDENDUM revised a CORRECT prediction into an incorrect one — it argued "
            "negative hours would not move and the zero-coal hours would remain; they "
            "doubled and went to zero. The error was conflating LOAD rank with "
            "NET-LOAD rank. Both are recorded in the RESULT rather than quietly "
            "dropped."
        ),
        "rule_36_contamination_in_SPP_is_ZERO": (
            "Rule 36(f) flags the cross-year warm-start artifact as UNMEASURED. "
            "Measured here: control (year-isolated at HEAD) minus keeper (committed, "
            "multi-year, warm-start ON) is 0.0000 TWh in 2019-2022 and +-0.0028 TWh "
            "in 2023-2025, a pure COAL_PRB <-> COAL_LIGNITE reclassification summing "
            "to 0.0000. That simultaneously bounds HEAD drift (8,701 changed lines "
            "across 62 solve-path files) at zero."
        ),
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=None)
    args = ap.parse_args()
    targets = [args.bundle] if args.bundle else [SPAN, RUNG]
    for b in targets:
        att = build(b)
        (b / "calibration_attestation.json").write_text(
            json.dumps(att, indent=2) + "\n"
        )
        fp = att["free_parameters"]
        print(
            f"{b.name}: attestation written — "
            f"years_held={att['governance']['authorized_price_tuning']['years_held']} "
            f"n_entries={fp['n_entries']} n_residual={fp['n_residual']} "
            f"offer_sha={_offer_sha(b)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
