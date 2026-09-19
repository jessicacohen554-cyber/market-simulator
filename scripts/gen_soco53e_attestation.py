"""Write the SOCO-53e calibration attestation (schema ``calibration-attestation/v1``).

Lane SOCO-53e armed exactly ONE mechanism — ``measured_st_heat_rates``, on SOCO's
own CAMPD-derived artifact — as a rule 14 ``[R-ACCURATE]`` data repair. Unlike its
predecessor SOCO-53, whose effect on the target row was predicted adverse, this
lane's effect was predicted small and favourable, and it is reported at full
magnitude either way.

The four governance assertions are asserted by the LANE. Every one is a factual
claim about this bundle and each is machine-verified against its own
``run_config.json`` by :func:`_verify`, which raises rather than writing a false
assertion. ``owner_attestation`` records honestly that the owner has NOT attested
this run in session.

NO ``authorized_price_tuning`` KEY IS WRITTEN. ``calibration_verdict.py`` validates
any present value as a STRUCTURED rule-1 declaration, so prose there fails C6. The
declared-NONE statement lives in ``authorized_price_tuning_declared`` prose, which
is the SOCO-53/53c/53d convention.

Run: ``python scripts/gen_soco53e_attestation.py``
"""

from __future__ import annotations

import json
from pathlib import Path

BUNDLE = Path("results/calibration/soco53e_st_hr")

#: The measured artifact this lane applies, pinned so the attestation cannot
#: silently describe a different derive (rule 23 [R-FROZEN-DERIVE]).
ARTIFACT_SHA16 = "3755b4becfd9f460"


def _verify(sc: dict) -> None:
    """Raise unless every governance assertion is true of this bundle."""
    oc = sc.get("offer_curve_by_group") or {}
    for band in ("committed", "econ_low", "econ_high", "peak"):
        vals = {oc[g][band] for g in oc if band in oc[g]}
        if vals != {1.0}:
            raise SystemExit(f"band {band} is not the identity: {sorted(vals)}")
    if sc.get("offer_curve_overrides") or sc.get("offer_curve_deltas"):
        raise SystemExit("offer-curve overrides/deltas present")
    if sc.get("offer_curve_smoothing") or sc.get("curve_smoothing"):
        raise SystemExit("offer-curve smoothing set")
    if sc.get("outage_source") != "historic":
        raise SystemExit(f"outage_source not exogenous: {sc.get('outage_source')}")
    if not sc.get("measured_st_heat_rates"):
        raise SystemExit("measured_st_heat_rates is not armed — wrong bundle")
    # The keeper's recipe must be carried forward unchanged, or this is not an
    # A/B against the control of record.
    for name in (
        "measured_ct_heat_rates",
        "egrid_family_heat_rates",
        "soco_gas_st_campaign_commitment",
    ):
        if not sc.get(name):
            raise SystemExit(
                f"{name} is not armed — the keeper's recipe is not carried"
            )
    # ...and nothing ELSE from the two upstream lanes may be on, or the G-DRIFT
    # inertness audit in the PRECOMMIT does not describe this run.
    for name in ("measured_coal_heat_rates", "mid_vintage_exit_carry"):
        if sc.get(name):
            raise SystemExit(f"{name} is armed — not this lane's recipe")


def _retag(att: dict, sc: dict) -> None:
    """Re-tag the two offer-curve DOF entries, as SOCO-40/53/53c/53d did.

    ``build_dof_ledger.py`` tags ``offer_curve_by_group`` and
    ``offer_curve_smoothing`` ``residual`` by default, because on every other
    ISO they ARE the rule-1 price-tuning surface. On SOCO they cannot be: the
    identity 1.0 on all four bands is not a tuned value, and there is no price
    residual in existence to have tuned it against. The re-tag is therefore a
    statement about THIS bundle, and it is re-verified by execution here rather
    than inherited — :func:`_verify` has already raised if any band is off the
    identity or any override, delta or smoothing is set.
    """
    fp = att.get("free_parameters")
    if not fp:
        raise SystemExit(
            "free_parameters absent — run "
            "`PYTHONPATH=src python3 scripts/build_dof_ledger.py --iso SOCO "
            f"{BUNDLE}` first"
        )
    oc = sc.get("offer_curve_by_group") or {}
    bands = {
        band: sorted({oc[g][band] for g in oc if band in oc[g]})
        for band in ("committed", "econ_low", "econ_high", "peak")
    }
    for entry in fp["entries"]:
        if entry["name"] == "offer_curve_by_group":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "All four price-tuning bands (committed / econ_low / econ_high / "
                f"peak) are at the identity 1.0 on all {len(oc)} groups — "
                "machine-verified by gen_soco53e_attestation._verify, which raises "
                f"otherwise: the distinct values per band are {bands}. "
                "offer_curve_overrides and offer_curve_deltas are null. The two "
                "non-identity keys, econ_low_share and pct_peaking, are NOT the "
                "authorized channel — rule 1's carve-out excludes structural shares "
                "— and arrive verbatim from the ISO-agnostic GENERIC_BASE_OFFER_CURVE. "
                "There is no soco.py delta module, so rule 25 [R-ISO-SCOPE] holds by "
                "construction."
            )
        elif entry["name"] == "offer_curve_smoothing":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "Unset on this run — both offer_curve_smoothing and curve_smoothing "
                "are null (machine-verified). Nothing was tuned because nothing was "
                "set."
            )
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    fp["retag_note"] = (
        "SOCO-53e re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40/53/53c/53d used and re-verified here by "
        "execution. n_entries 3 / n_residual 1, UNCHANGED from the control: this lane "
        "added NO free parameter. measured_st_heat_rates is a measured-physical input "
        "with zero degrees of freedom, not a parameter — its value is a committed "
        "per-plant measurement of a machine's operating heat rate, it regenerates for "
        "a forward year from the same pipeline and responds to changed conditions, and "
        "no residual can be closed by it (there is no price residual in existence at "
        "all, and the deriver's physical band is measurably inert). The single "
        "remaining residual entry is the inherited wefor_multiplier, untouched here."
    )


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-53e bundle."""
    att_path = BUNDLE / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    _verify(sc)

    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-53e (lane), run 2026-09-19-soco53e-measured-st-hr. ONE mechanism is "
            "armed against the SOCO-53d keeper: ScenarioConfig.measured_st_heat_rates, "
            "on this lane's own derive of SOCO's CAMPD boiler record "
            f"(campd_st_heat_rates_SOCO.csv, sha256[:16] {ARTIFACT_SHA16}, 5 of 5 "
            "plants / 3,131.1 of 3,131.1 MW = 100 % of ST_GAS capacity, MMBtu per NET "
            "MWh pooled 2023-2025 over 160,139 in-band steady boiler hours at 12 "
            "units). Everything else is the keeper's recipe unchanged. "
            "THE MECHANISM IS A rule 14 [R-ACCURATE] DATA REPAIR, NOT A TUNING "
            "CHANNEL, and it reaches what NO eGRID construction can: a southeastern "
            "steam station is routinely a coal boiler and a gas boiler behind ONE ORIS "
            "code, and because both machines are prime mover ST, the eGRID PLANT rate "
            "blends them AND SO DOES THE PRIME-MOVER-FAMILY rate this lane's own "
            "predecessor armed (egrid_family_heat_rates). Only a per-UNIT meter "
            "separates two boilers inside one family. E C Gaston (26) is the case: its "
            "ST family rate 11.5505 blends an 832 MW coal boiler with four ~255 MW gas "
            "boilers, and the gas boilers' own metered rate is 11.0744 — which "
            "independently corroborates the 10.887 eGRID gas-steam SUB-family rate "
            "SOCO-53c routed as a separate lever, so this mechanism SUBSUMES it. "
            "THE MEASURED ERRORS RUN IN BOTH DIRECTIONS (Gaston -0.4761, Jack Watson "
            "-0.0532, Greene County -0.0489, Yates -0.0172, and Barry +1.3745 the "
            "other way), which is why no multiplier substitutes for the measurement. "
            "THIS LANE ALSO CORRECTED THE PREMISE IT WAS HANDED, before solving: "
            "FINDING-soco-53d §8.1 routed '+0.539 MMBtu/MWh, +5.2 %' but had converted "
            "SOCO's BOILERS at the CT_PEAKER parasitic factor 0.99 where the ST_GAS "
            "class factor is 0.95. Re-derived from scratch (reproducing 53d to +/-0.03 "
            "at 0.99) and settled by measurement rather than convention — SOCO's own "
            "metered net/gross over its eight unambiguous plant-years is 0.938-0.943 "
            "(EIA-923 ST/NG net over CAMPD gas-boiler gross), which 0.95 reproduces to "
            "1.2 % and 0.99 misses by 5.5 % — the capacity-weighted level moves "
            "10.9613 -> 10.8522, -1.0 %, NOT -5.2 %. Rule 19 [R-ONE-MECH]: ONE seam, "
            "machine-verified at TWO grains — 12 of 393 built-fleet rows and 20 of 327 "
            "LP rows move, all ST_GAS, and COAL, CT_PEAKER, CC_REGULAR, CC_CHP, "
            "CT_CHP, ST_CHP and hydro are byte-identical at max |delta| exactly "
            "0.0000000000. Rule 25 [R-ISO-SCOPE]: SOCO's own measurement, and a NEW "
            "default-off field rather than a widened measured_ct_heat_rates precisely "
            "because widening would arm five other ISOs' keepers on a measurement "
            "their lanes never made (rule 28(d)). Rule 21 [R-DOF]: ZERO free "
            "parameters added."
        ),
        "authorized_price_tuning_declared": (
            "NONE. No authorized price-tuning channel is in use on this run, and none "
            "CAN be: SOCO publishes no price, actual_lmp.json carries no SOCO block, "
            "so there is no price residual to tune against and none was computed. "
            "That matters more than usual for THIS mechanism, because a measured heat "
            "rate is the one input that could look like price tuning — and here it "
            "cannot be, since there is no price to tune to. Every "
            "offer_curve_by_group band is machine-verified at the identity 1.0 across "
            "all 13 groups (committed / econ_low / econ_high / peak each resolve to "
            "the single distinct value {1.0}); offer_curve_overrides and "
            "offer_curve_deltas are null; offer_curve_smoothing and curve_smoothing "
            "are null. The rule 1 [R-STRUCT] / rule 13 [R-MEASURED] carve-out is "
            "UNREACHABLE here, not merely unused, so no authorized_price_tuning "
            "declaration block is present."
        ),
        "owner_attestation": (
            "THE OWNER HAS NOT ATTESTED THIS RUN IN SESSION, and this field says so "
            "rather than borrowing an attestation that does not cover it. The four "
            "assertions above are the LANE's, and each is machine-verified against "
            "this bundle's own run_config.json by "
            "scripts/gen_soco53e_attestation.py::_verify, which raises rather than "
            "writing a false assertion — including that the keeper's own three flags "
            "are carried forward and that neither upstream lane's new default-off "
            'field is armed. The SOCO-40 owner sitting of 2026-09-16 (verbatim: "I '
            'attest") covers the INHERITED posture this run does not change — the '
            "price posture, the identity offer bands, the three-zone topology, the "
            "served measured interchange, the coal split — but it predates and cannot "
            "speak to this lane's one new lever, so it is cited for what it covers and "
            "stretched no further. The promotion question is open and is put to the "
            "owner in the FINDING."
        ),
        "dof_basis": (
            "n_entries 3, n_residual 1 — UNCHANGED from the control, because this lane "
            "added no free parameter. measured_st_heat_rates is a measured-physical "
            "INPUT (a committed per-plant measurement of a machine's operating heat "
            "rate) with zero degrees of freedom, not a parameter: every applied number "
            "is sum(heatInput)/sum(grossLoad) over the plant's own steady hours, and "
            "the gross-to-net factor is the COMMITTED class default, not a value this "
            "lane chose. The deriver's four constants are data-integrity guards fixed "
            "on physics ex ante and shown INERT by measurement — every plausible "
            "physical band moves the capacity-weighted result by less than 0.03 "
            "MMBtu/MWh, and the unbanded value sits inside that spread — so the band "
            "is not a degree of freedom. The membership rule likewise has no numeric "
            "parameter, and --check-pairing proves the within-plant pairing cannot "
            "move an applied row."
        ),
    }

    att["disclosures"] = {
        "note": (
            "SOCO-53e determination basis. Everything the run does not establish, at "
            "full magnitude. The first two items are unflattering to this lane's own "
            "arm and to the handoff that commissioned it, and they lead for that "
            "reason. The SOCO keeper's inherited basis lines follow and are unchanged."
        ),
        "1_THE_LANE_CORRECTED_ITS_OWN_COMMISSIONING_NUMBER_DOWN_BY_A_FACTOR_OF_FIVE": (
            "This lane was commissioned on FINDING-soco-53d §8.1's claim that the "
            "model is '+0.539 MMBtu/MWh, +5.2 %, too dear on 3,131 MW … worth "
            "$1.5-3.3/MWh'. That figure converted SOCO's BOILERS to a net basis at "
            "0.99, the CT_PEAKER parasitic factor; the ST_GAS class factor is 0.95, so "
            "every rate was understated by 4.2 %. Phase 0 re-derived from scratch "
            "rather than inheriting, reproduced 53d's table to +/-0.03 at 0.99 (so the "
            "number was right and the basis was wrong), and settled the basis by "
            "measurement: SOCO's gas-steam fleet's own metered net/gross over its "
            "eight unambiguous plant-years is 0.938-0.943. On the right basis the "
            "capacity-weighted level moves 10.9613 -> 10.8522, -1.0 %. THE LEVER IS "
            "REAL BUT AN ORDER OF MAGNITUDE SMALLER THAN ADVERTISED, and that was "
            "registered in the PRECOMMIT before the solve, not discovered after it."
        ),
        "2_THE_ARM_DOES_NOT_FIX_SOCO_S_HEADLINE_DEFECT_AND_SAID_SO_FIRST": (
            "PRECOMMIT §4.3 registered, BEFORE the solve, that this arm closes at most "
            "0.7 % of the single remaining C1 failure (2023 CT_PEAKER, +9.898 TWh / "
            "+4.12pp on the control), and measured why: the headroom-capped hourly "
            "displacement UPPER BOUND was +0.066 / +0.154 / +0.053 TWh. Delivered: "
            "CT_PEAKER -0.0761 / -0.1769 / -0.0789 TWh, ST_GAS +0.0897 / +0.1878 / "
            "+0.0846. The direction is right and the magnitude is what was declared. "
            "It is armed on rules 1 [R-STRUCT] and 14 [R-ACCURATE] — a measured "
            "physical input replacing an estimate that is demonstrably a blend of two "
            "different machines — and on no other ground."
        ),
        "3_THE_SHAPE_EVIDENCE_IS_MIXED_AND_IS_REPORTED_AS_MIXED": (
            "D-1 ST_GAS cv_ratio moves 1.942 -> 2.026 in 2023 (AWAY from 1.0), 2.499 "
            "-> 2.413 in 2024 and 2.166 -> 2.091 in 2025 (toward it). Two years "
            "improve and one degrades. All six values clear the >= 0.5 gate and "
            "profile_r stays at 0.981-0.992 against a 0.8 floor, so D-1 passes on both "
            "sides — but this lane does NOT claim the shape win its predecessor could. "
            "Unlike SOCO-53d, whose object WAS the conduct, this lane's object is the "
            "cost of a machine, and the shape is a second-order consequence."
        ),
        "4_the_rule_17_re_measurement_this_lane_OWED_was_performed_and_holds": (
            "SOCO-53d §8.1 recorded that its rule 17 [R-FLOOR-WINDOW] evidence was "
            "measured on a P0 pattern priced with the wrong ST_GAS heat rate, and owed "
            "a re-measurement once this arm landed. Performed on this bundle's own "
            "floors/<year>_P1.npz: in ALL TWELVE plant-years the campaign floor's "
            "binding share stays at or below that plant's own measured synchronized "
            "share (Jack Watson 0.808/0.652/0.762 vs 0.920; Yates 0.134/0.536/0.749 vs "
            "0.843; Greene County 0.312/0.300/0.506 vs 0.752; E C Gaston "
            "0.203/0.106/0.184 vs 0.639), Barry still carries ZERO floored unit-hours "
            "in all three years, and the floored blocks keep a median length of 87-459 "
            "hours, so what the mechanism places are still campaigns rather than gap "
            "fills. ZERO exceedances. D-4 off-window share is exactly 0.0 in all three "
            "years and the mechanism still touches ST_GAS and nothing else."
        ),
        "5_rule_20_forced_share_is_essentially_unmoved": (
            "ST_GAS forced share 0.0917 / 0.0999 / 0.1157 against the 30 % merchant "
            "cap (control 0.0944 / 0.1001 / 0.1160), so C8 passes on the budget and "
            "the escalation path is never entered. CT_PEAKER carries 0.0000 forced "
            "share in every year on both sides."
        ),
        "6_THIS_ARM_CREATES_AN_ASYMMETRY_AT_GASTON_THAT_IT_DOES_NOT_CLOSE": (
            "E C Gaston's blended ST family rate 11.5505 is carried by its COAL row "
            "(26_5, 832 MW) as well as by its four gas boilers. Repricing only the gas "
            "side means the coal boiler is now left on a rate that the same arithmetic "
            "says is roughly 0.5 MMBtu/MWh too CHEAP for a coal machine. Closing it is "
            "measured_coal_heat_rates — a mechanism that ALREADY EXISTS at HEAD "
            "(nwpp-42) and needs only a SOCO artifact — and stacking it here would be "
            "the rule 19 [R-ONE-MECH] violation this lane spent its phase 0 "
            "disproving. It is ROUTED, not absorbed, and it is named here rather than "
            "left for a reader to infer."
        ),
        "7_barry_is_applied_at_full_magnitude_and_rule_14_s_exception_does_NOT_apply": (
            "Barry (3) moves the other way, +1.3745 MMBtu/MWh: its two 1954-vintage "
            "80 MW boilers meter at 13.9845 over 2,521 steady hours with 98 % of their "
            "operating hours inside the physical band. Unlike SOCO-53c's cogens, this "
            "rate is on the SAME boundary as the rate it replaces (net MWh, same "
            "parasitic convention), so rule 14's misalignment exception does not apply "
            "and the number is used as measured. It is a genuinely poor machine run "
            "1.6 % of the time, and it independently corroborates SOCO-53d's "
            "campaign-duty gate refusing Barry at a 6.3 % synchronized share. "
            "Delivered: Barry's energy falls 0.0038 -> 0.0010, 0.0096 -> 0.0007 and "
            "0.0671 -> 0.0376 TWh."
        ),
        "8_barry_unit_4_the_model_prices_362_MW_as_coal_and_CAMPD_files_it_as_gas": (
            "UNCHANGED FROM SOCO-53d, AND THIS LANE DEPENDS ON THE CURRENT ASSIGNMENT. "
            "CAMPD files Barry unit 4 (a 330 MW tangentially-fired boiler) as Pipeline "
            "Natural Gas while the model carries it as a 362 MW COAL row. That is "
            "exactly why membership here is a capacity-rank pairing to the plant's own "
            "model boiler rows and NOT the coal sibling's primaryFuelInfo tag, which "
            "would have priced the model's two 80 MW ST_GAS rows off a boiler the "
            "model dispatches as coal. The underlying fuel-class question is REPORTED "
            "AND ROUTED, not adopted: it is 362 MW of SOCO coal and it belongs to a "
            "lane that can change the assignment, not to one that reads it."
        ),
        "9_marginal_emission_rate_is_carried_by_this_bundle": (
            "Every hourly/system_<year>.parquet carries marginal_emission_rate. P1 "
            "load-weighted mean 0.6263 / 0.6090 / 0.6369 tCO2/MWh on this arm against "
            "0.6240 / 0.6092 / 0.6363 on the control; p10 / median / p90 0.4187 / "
            "0.5905 / 0.8194 (2023), 0.3833 / 0.5818 / 0.8717 (2024), 0.3833 / 0.5848 "
            "/ 1.0896 (2025); zero-share 0.00 / 0.00 / 0.15 %, unchanged. The mean "
            "moves by at most 0.0023 and every percentile is unchanged or within "
            "0.003, which is the expected signature of swapping one thermal machine's "
            "cost for another at a near-identical emission rate."
        ),
        "10_2025_IS_REPORTED_BUT_NOT_GATED_AND_THAT_BINDS_THIS_LANE_S_RESULT": (
            "INHERITED FROM SOCO-40, UNCHANGED. 2025 carries no eia923_incomplete flag "
            "but only 6 of 23 CT_PEAKER and 1 of 6 ST_GAS plants have filed, so the "
            "2025 CT_PEAKER and ST_GAS C1 rows are SKIPPED by the scorer — the two "
            "rows this lane moves most. The 2025 column of this A/B is REPORTED BUT "
            "NOT GATED, and the gated evidence is 2023 and 2024 only."
        ),
        "11_pre_existing_defects_inherited_unchanged": (
            "The 2025 EIA-923 hydro input hole (5 plants / 0.327 TWh against 6.012 "
            "measured; hydro is byte-identical in all three years here, confirming "
            "this seam does not touch it); 1,306.6 MW of pumped storage UNOBSERVABLE "
            "in EIA-930; Southern Power (186) excluded from the FERC-714 zonal shares "
            "as a documented NO, its 3.211 / 3.401 / 3.084 TWh named and never "
            "absorbed; the Vogtle 3/4 COD month grain leaving nuclear -0.220 / -0.144 "
            "/ -0.245 TWh, byte-identical here; and NWPP-41's ERCOT-pooled PRB proxy "
            "reaching SOCO's 6002 Miller, 6073 Daniel and 6257 Scherer, which "
            "coal_prb_proxy_own_iso would close and which this lane does not touch."
        ),
        "12_bench_parts_are_STALE_repo_wide_and_were_NOT_rebuilt": (
            "check_bench_freshness is RED across every ISO from commit ed96378e "
            "(caiso-284) editing scripts/render_calibration_html.py, a PAYLOAD_SOURCE. "
            "This lane touched no fingerprint source. SOCO's parts were deliberately "
            "NOT rebuilt — dashboard_add_run.py's auto-rebuild was reverted and "
            "metrics.json re-written on the COMMITTED bench, exactly as SOCO-53c and "
            "SOCO-53d did — because rebuilding SOCO's alone would score this arm "
            "against a different benchmark from its control and destroy the G-CTRL "
            "form-4 comparison. The verdict on the rebuilt bench is reported "
            "separately in the FINDING, labelled."
        ),
        "13_a_shared_contract_test_gains_one_more_offender_and_was_NOT_patched": (
            "tests/unit/config/test_data_profiles_tokens.py::"
            "test_soco_token_collides_with_no_other_raw_name is RED at HEAD and this "
            "lane's artifact adds one more offender, in the established convention "
            "(campd_st_heat_rates_SOCO.csv, exactly as the committed "
            "campd_ct_heat_rates_SOCO.csv and campd_gas_st_campaign_params_SOCO.csv). "
            "Verified: it fails identically with and without this lane's file. The fix "
            "is a naming-convention decision across every SOCO artifact and belongs to "
            "the SOCO desk, not to a lane that would be silently patching a shared "
            "contract test to make its own PR green."
        ),
        "14_the_price_gap_is_structural_and_permanent": (
            "NO PUBLIC SOCO PRICE EXISTS AND NONE EVER WILL. actual_lmp.json carries "
            "no SOCO block and must not gain one — a placeholder breaks "
            "calibration_verdict._price_reference_absent and silently moves SOCO onto "
            "the ordinary determination path. C3a / C3b / C3c are UNSCORABLE, NOT "
            "FAILED, in every year. The ceiling is rubric v3.8 PHYSICALLY-CALIBRATED "
            "(PRICE UNSCORED); SOCO can NEVER read CALIBRATED. Scored on C1 / C2 / C4 "
            "/ C6 / C8 only. Gate G17 absolute: no neighbouring hub, no proxy, no "
            "cost-stack price, ever. The model's own load-weighted mean LMP is "
            "MODEL-ONLY and UNVERIFIED and is never quoted as price skill."
        ),
    }

    _retag(att, sc)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
