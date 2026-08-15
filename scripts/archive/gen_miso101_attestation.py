"""Write ``calibration_attestation.json`` for the miso-101 hour-grain temperature arm.

``miso101_tempgrain_B`` is the ``2026-07-28-miso-99b-chp-power`` keeper recipe
(rebuilt from its ``meta.json`` by ``replay_keeper``) with ONE mechanism change:
the hour-grain, mean-anchored leg of the existing ``temp_dependent_derate``,
scoped to ``ST_CHP`` + ``CT_CHP`` and carrying MISO's OWN measured slope. The
governance posture and the accepted-limitation ledger are that keeper's,
inherited unchanged — no exception is added, widened, or re-scoped, and none
needed to be: the two arms score IDENTICALLY on every C-series criterion
(``scored 6 / target_grade 4 / fails 2``, C1 all 16/16 · free 12/12), so the
ledgered-caveat budget stays exactly where the miso-90 owner re-gate left it
(3/3: C3a, C3b, C3c).

The delta adds **zero free parameters** (rule 21 ``[R-DOF]``): the slope is a
measured unit-conduct statistic derived from MISO's own CAMPD record by
``scripts/data/derive_campd_temp_derate_params.py``, stable under
leave-one-year-out at ±8 %, and frozen against residuals by rule 23
``[R-FROZEN-DERIVE]``. The onset was likewise measured, not chosen — and
measured ABSENT, which is why the committed 15 °C hinge is replaced by the
mean-anchored form rather than re-tuned. The ``free_parameters`` ledger is
refreshed from THIS bundle's ``run_config.json`` by
``scripts/build_dof_ledger.py`` (run separately).

Usage:
    python scripts/gen_miso101_attestation.py
    python scripts/build_dof_ledger.py results/calibration/miso101_tempgrain_B --iso MISO
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/miso99_chp_hr_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso101_tempgrain_B/calibration_attestation.json"

ATTESTED_BY = (
    "miso-101 hour-grain diurnal temperature capability 2026-07-28: the "
    "2026-07-28-miso-99b-chp-power keeper recipe, rebuilt from its meta.json "
    "by replay_keeper, solved fresh for 2023/2024/2025 as one process per year "
    "into one bundle (rule 16), with ONE mechanism change carried on both the "
    "explicit kwarg and the generic prb_overrides channel so it round-trips "
    "through meta.json: temp_dependent_derate=True + temp_derate_hourly_grain="
    "True + temp_derate_mean_anchored=True, scoped by temp_derate_classes="
    "{ST_CHP, CT_CHP}, with temp_derate_slope_st_chp = temp_derate_slope_ct_chp "
    "= 0.00141/C. "
    "WHAT IT REPLACES: nothing was replaced -- a MISSING INPUT GRAIN was added. "
    "The temperature-derate curve is fed by iso_zone_tmax, which broadcasts the "
    "daily TMAX FLAT WITHIN THE DAY, so even when armed the mechanism carried "
    "ZERO hour-of-day signal and no channel in the availability chain could "
    "produce a diurnal capability wave (FINDING-miso100 SS4/SS5). "
    "iso_zone_hourly_drybulb reconstructs the within-day wave from the SAME "
    "curated daily TMIN/TMAX via the standard climatological two-piece cosine "
    "bridge (Parton & Logan 1981; constants.DIURNAL_TMIN_HOUR/TMAX_HOUR), whose "
    "h05/h15 phase anchors are VALIDATED on MISO's own CAMPD conduct at best-fit "
    "lag 0. This is an input-grain refinement of an EXISTING mechanism, NOT a "
    "new floor and NOT a second mechanism (rule 19 [R-ONE-MECH]): MECH_CHP_STEAM "
    "is already clipped to pmax x availability, so the finer availability shape "
    "propagates to every floored cogen by itself. "
    "MEASURED, NOT ASSERTED, AND MEASURED ON MISO (rule 25 [R-ISO-SCOPE]): "
    "pjm-95 REFUTED the committed literature slopes on PJM's own CAMPD, so they "
    "do not transfer and MISO had to identify its own. Within-day, PLANT-DAY "
    "FIXED-EFFECTS regression of log(CEMS gross load) on the hour-grain dry-bulb "
    "over the six CEMS-identifiable MISO cogens, 2023-2025: demeaning inside each "
    "(plant, day) differences away every day-level confounder (outage, host steam "
    "demand, fuel switch, maintenance season), so the coefficient is directly a "
    "fractional capability response per degC. Capacity-weighted p50 = 0.00141/C "
    "-- the same population statistic derive_campd_gas_commitment_params.py uses "
    "for min_load_frac, and ~5x BELOW the committed literature CC slope "
    "(0.0076/C). MISO's own confirmation of the pjm-95 non-transferability "
    "finding. "
    "THE ONSET WAS MEASURED ABSENT, NOT CHOSEN: the non-parametric onset scan "
    "re-estimates the within-day slope inside day-mean-temperature bins and finds "
    "the response unambiguously present BELOW 15 degC -- 0.00359/C in the 5-10 C "
    "bin (r -0.381) and 0.00295/C in 10-15 C (r -0.278) -- exactly where the "
    "committed max(0, T - 15) hinge is identically flat. The hinge would erase "
    "the measured winter wave, which is why the mean-anchored form (curve about "
    "the zone's own annual-mean dry-bulb, annual mean exactly 1.0) is used "
    "instead. Mean-anchoring is also the LEVEL-NEUTRALITY guarantee: it composes "
    "ON TOP of the existing level treatment rather than replacing it, so the arm "
    "claims ONLY the shape its within-day estimator identifies and claims NOTHING "
    "about class level -- deliberately the smaller claim. "
    "THE METERED MACHINE IS A GAS TURBINE, NOT A BOILER, which redirects "
    "FINDING-miso100's condenser framing: Beaumont's CEMS units are 3 x COMBINED "
    "CYCLE and the only other substantial CEMS cogen meter is a 26 MW CT, so the "
    "response is the GT air-density / mass-flow effect -- and GT physics is "
    "precisely why the response continues through the ISO rating point with no "
    "onset. R S Nelson 1393, the other CEMS entry in the D-1 ST_CHP row, is a "
    "TANGENTIALLY-FIRED COAL boiler whose ST_CHP slice is an EIA-923 monthly "
    "split off that coal meter, so the derivation DROPS it as a different "
    "machine. "
    "NO SCREEN WAS APPLIED, AND THE HYPOTHESIS THAT WOULD HAVE JUSTIFIED ONE IS "
    "REFUTED BY THE DATA. The tempting move is to pin the identification to the "
    "most capability-limited plant (arguing merchant dispatch biases the other "
    "meters downward), which would have licensed Beaumont's own 0.00399/C -- 3x "
    "larger. That premise predicts the most-pinned plants show the LARGEST slope. "
    "MISO's most-pinned cogens show the SMALLEST (Primient, online CV 0.094, "
    "+0.00060; Portside, CV 0.058, +0.00080) against Beaumont (CV 0.159) "
    "+0.00399; and Beaumont and Dearborn are indistinguishable on every a-priori "
    "pinnedness metric (loading ratio 0.80 vs 0.81) yet have opposite-signed "
    "slopes. So the class-population statistic stands and the armed slope "
    "deliberately UNDER-claims. "
    "WHY THIS IS THE KEEPER ON RULE 1, AND NO GATE OBJECTS: against a same-HEAD "
    "flag-off control (2026-07-28-miso-101a-control) which reproduces the "
    "outgoing keeper at 0.00000 % on EVERY class in EVERY year -- so every arm-B "
    "movement is attributable to the single mechanism, and the five new "
    "ScenarioConfig fields are PROVABLY INERT when off -- all four PRE-REGISTERED "
    "gates pass in all three years. Beaumont's floored ST_CHP grid slice goes "
    "from BYTE-FLAT (amplitude 0.000000 MW) to a wave troughing h15, the meter's "
    "OWN trough hour, correlating +0.964 / +0.958 / +0.984 with its CEMS "
    "hour-of-day profile. G2 level neutrality: in-scope max |move| 0.396 % "
    "(bound 1.0 %). G3 scope containment: out-of-scope max |move| 0.068 % "
    "(bound 0.1 %), and out-of-scope AVAILABILITY change is exactly 0.000 % "
    "(verified no-LP), so that residual is the LP rebalancing, not a scope leak. "
    "D-1 profile_r improves in EVERY year for BOTH in-scope classes: ST_CHP "
    "-0.797/-0.762/-0.771 -> -0.587/-0.647/-0.680, CT_CHP +0.652/-0.104/+0.171 "
    "-> +0.684/-0.033/+0.298. Every C-series criterion verdict is IDENTICAL "
    "between arms; NO CRITERION REGRESSES AND NONE IMPROVES. "
    "RULE 22 LOO: re-deriving the class slope on each 2-year subset gives "
    "0.00153 / 0.00140 / 0.00130 against 0.00141 full-sample (+-8 %) -- no year "
    "drives it. Scope note stated plainly: this is LOO on the parameter "
    "identification, which is where the fitting risk lives; a solve-level LOO "
    "would need three further 2-year re-solves and was NOT run. "
    "2023-2025 only, all three FRESH in one bundle (rule 16), no holdout year "
    "touched, MISO freeze active. Evidence: "
    "results/calibration/FINDING-miso101-stchp-temp-grain-2026-07-28.md; "
    "pre-registration committed BEFORE either solve: "
    "results/calibration/PREREG-miso101-stchp-temp-grain-2026-07-28.md; "
    "log: docs/calibration-log/miso.md 2026-07-28 miso-101."
)

DISCLOSURE = (
    "miso-101 disclosures, reported rather than patched. (a) ONE PRE-REGISTERED "
    "PREDICTION WAS WRONG IN DIRECTION: P6 predicted the model's within-day "
    "variance would RISE toward the actual; it FELL (ST_CHP model_offpeak_cv "
    "0.0120/0.0130/0.0130 -> 0.0080/0.0100/0.0090, so cv_ratio "
    "0.386/1.345/1.019 -> 0.253/1.041/0.664 -- closer to 1.0 in 2024, further "
    "in 2023 and 2025). The cause was not anticipated and is now understood: the "
    "arm's temperature wave is ANTI-CORRELATED with R S Nelson's merchant "
    "afternoon hump, so the class composite partially CANCELS -- the same "
    "cancellation that moves profile_r the right way. Recorded as wrong; neither "
    "class is D-1-gated. (b) ST_CHP profile_r remains NEGATIVE in all three "
    "years, exactly as pre-registered (P2): the statistic composites Nelson's "
    "anti-phase merchant hump and the flat report-side BTM add-back, channels "
    "the lever does not own. The lever was NOT widened to chase it (rule 1). "
    "(c) The modelled amplitude UNDER-claims the meter by construction: 1.56-1.62 "
    "% against a measured 3.67-5.68 % (28-43 %), the direct consequence of arming "
    "the class-population slope rather than Beaumont's own. It is NOT to be "
    "closed by raising the slope. (d) MATERIALITY, PLAINLY: ST_CHP is 0.29-0.43 % "
    "and CT_CHP 0.81-0.84 % of MISO load, both under the rule-20 2 % line, which "
    "is why they are D-1-ungated and D-2-exempt -- NO GATE WAS AT RISK IN EITHER "
    "DIRECTION, and a reader who values only headline fit should read this run as "
    "neutral. The case for it is rule-1 structural fidelity: the model now "
    "represents a real, measured physical behaviour it previously could not "
    "represent at all, and the same missing hour-grain input flattens every "
    "floored steam cogen in every ISO. (e) 2024 mean slack rose 0.87 % with a "
    "single-hour delta of 4,273 MW -- one scarcity hour reshuffling at the margin "
    "on a 645 TWh year whose mean slack is 0.27 MW, not a reliability change. "
    "(f) The ledgered-caveat budget is UNCHANGED at 3/3 (C3a, C3b, C3c) from the "
    "miso-90 owner re-gate; no exception was added, widened or re-scoped, and "
    "none was needed since every criterion verdict is identical to the control's."
)


def main() -> int:
    """Write the arm's attestation, inheriting the keeper's ledger unchanged."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=ATTESTED_BY)
    att["disclosures"] = dict(att.get("disclosures", {}), note=DISCLOSURE)
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM.relative_to(REPO)}")
    print(f"  exceptions inherited unchanged: {len(att.get('exceptions', []))}")
    print(
        "now run: python scripts/build_dof_ledger.py "
        "results/calibration/miso101_tempgrain_B --iso MISO"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
