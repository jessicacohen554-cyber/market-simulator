"""Write the SOCO-53f calibration attestation (schema ``calibration-attestation/v1``).

Lane SOCO-53f armed exactly ONE mechanism — ``measured_coal_heat_rates``, on
SOCO's own CAMPD-derived artifact — as a rule 14 ``[R-ACCURATE]`` data repair.
The mechanism itself predates this lane (nwpp-42, 2026-09-19); SOCO had no
artifact, so the flag was a strict no-op here until now. This lane wrote NO
``ScenarioConfig`` field and added NO free parameter.

The four governance assertions are asserted by the LANE. Every one is a factual
claim about this bundle and each is machine-verified against its own
``run_config.json`` by :func:`_verify`, which raises rather than writing a false
assertion. ``owner_attestation`` records honestly that the owner has NOT attested
this run in session.

NO ``authorized_price_tuning`` KEY IS WRITTEN. ``calibration_verdict.py`` validates
any present value as a STRUCTURED rule-1 declaration, so prose there fails C6. The
declared-NONE statement lives in ``authorized_price_tuning_declared`` prose, which
is the SOCO-53/53c/53d/53e convention.

Run: ``python scripts/gen_soco53f_attestation.py``
"""

from __future__ import annotations

import json
from pathlib import Path

BUNDLE = Path("results/calibration/soco53f_coal_hr")

#: The measured artifact this lane applies, pinned so the attestation cannot
#: silently describe a different derive (rule 23 [R-FROZEN-DERIVE]).
ARTIFACT_SHA16 = "efd5926eecc62d8f"

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names. The other
#: offer_curve_by_group keys (econ_low_share, pct_peaking) are STRUCTURAL shares
#: the carve-out EXCLUDES and are not 1.0 on any ISO.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")


def _verify(sc: dict) -> None:
    """Raise unless every governance assertion is true of this bundle."""
    oc = sc.get("offer_curve_by_group") or {}
    for band in PRICE_TUNING_BANDS:
        vals = {oc[g][band] for g in oc if band in oc[g]}
        if vals != {1.0}:
            raise SystemExit(f"band {band} is not the identity: {sorted(vals)}")
    if sc.get("offer_curve_overrides") or sc.get("offer_curve_deltas"):
        raise SystemExit("offer-curve overrides/deltas present")
    if sc.get("offer_curve_smoothing") or sc.get("curve_smoothing"):
        raise SystemExit("offer-curve smoothing set")
    if sc.get("outage_source") != "historic":
        raise SystemExit(f"outage_source not exogenous: {sc.get('outage_source')}")
    if not sc.get("measured_coal_heat_rates"):
        raise SystemExit("measured_coal_heat_rates is not armed — wrong bundle")
    # The keeper's recipe must be carried forward unchanged, or this is not an
    # A/B against the control of record.
    for name in (
        "measured_ct_heat_rates",
        "egrid_family_heat_rates",
        "measured_st_heat_rates",
        "soco_gas_st_campaign_commitment",
    ):
        if not sc.get(name):
            raise SystemExit(
                f"{name} is not armed — the keeper's recipe is not carried"
            )
    # ...and nothing ELSE from the upstream lanes the G-DRIFT audit classified
    # INERT may be on, or that audit does not describe this run.
    for name in (
        "mid_vintage_exit_carry",
        "benchmark_membership_vintage_union",
        "nyiso_ct_peaker_committed_measured",
        "coal_prb_proxy_own_iso",
    ):
        if sc.get(name):
            raise SystemExit(f"{name} is armed — not this lane's recipe")


def _retag(att: dict, sc: dict) -> None:
    """Re-tag the two offer-curve DOF entries, as SOCO-40/53/53c/53d/53e did.

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
        for band in PRICE_TUNING_BANDS
    }
    for entry in fp["entries"]:
        if entry["name"] == "offer_curve_by_group":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "All four price-tuning bands (committed / econ_low / econ_high / "
                f"peak) are at the identity 1.0 on all {len(oc)} groups — "
                "machine-verified by gen_soco53f_attestation._verify, which raises "
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
        "SOCO-53f re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40/53/53c/53d/53e used and re-verified here "
        "by execution. n_entries 3 / n_residual 1, UNCHANGED from the control: this "
        "lane added NO free parameter, and no ScenarioConfig field either — "
        "measured_coal_heat_rates already existed at HEAD (nwpp-42) and was a strict "
        "no-op for SOCO until this lane derived SOCO's artifact. It is a "
        "measured-physical input with zero degrees of freedom: every applied number "
        "is sum(heatInput)/sum(grossLoad) over the plant's own steady hours, it "
        "regenerates for a forward year from the same pipeline and responds to "
        "changed conditions, and no residual can be closed by it (there is no price "
        "residual in existence at all, and the deriver's physical band is measurably "
        "inert). The single remaining residual entry is the inherited "
        "wefor_multiplier, untouched here."
    )


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-53f bundle."""
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
            "SOCO-53f (lane), run 2026-09-20-soco53f-measured-coal-hr. ONE mechanism "
            "is armed against the SOCO-53e keeper: "
            "ScenarioConfig.measured_coal_heat_rates, on this lane's own derive of "
            "SOCO's CAMPD coal record (campd_coal_heat_rates_SOCO.csv, sha256[:16] "
            f"{ARTIFACT_SHA16}, 6 of 6 plants / 11,512.0 of 11,512.0 MW = 100 % of "
            "COAL capacity, MMBtu per NET MWh pooled 2023-2025 over 252,093 in-band "
            "steady hours at 15 units). Everything else is the keeper's recipe "
            "unchanged, and NO ScenarioConfig field was written: the mechanism "
            "already existed at HEAD (nwpp-42, 2026-09-19) and was a STRICT NO-OP for "
            "SOCO because no SOCO artifact existed. "
            "THE MECHANISM IS A rule 14 [R-ACCURATE] DATA REPAIR, NOT A TUNING "
            "CHANNEL: eGRID's plant rate is PLHTIAN / PLNGENAN, an ANNUAL average "
            "that folds startup fuel, shutdown tails and the offline hours' bank fuel "
            "into the number that sets the offer, and whose level moves with the "
            "plant's capacity factor in the vintage year. The rate that sets an offer "
            "is the rate at which the machine burns fuel WHILE RUNNING. "
            "THE MEASUREMENT REVERSED THE SIGN OF THE PREMISE THAT COMMISSIONED THIS "
            "LANE, and that was registered in the PRECOMMIT before the solve rather "
            "than discovered after it: FINDING-soco-53e §7.1 routed this lane on the "
            "reading that E C Gaston's coal boiler, left on the blended ST family "
            "rate 11.5505, is 'roughly 0.5 MMBtu/MWh too CHEAP'. Its own meter reads "
            "11.0505 — 0.5000 too DEAR, the magnitude right to four decimals with the "
            "sign inverted — because the blend is an annual average sitting ABOVE "
            "both machines' operating rates, not a weighted mean between them. ALL "
            "SIX PLANTS MOVE THE SAME WAY: Barry -1.8711, Daniel -0.9687, Scherer "
            "-0.8690, Gaston -0.5000, Bowen -0.4040, Miller -0.1022; "
            "capacity-weighted 11.5267 -> 10.8926, -5.5 %, on five times the capacity "
            "the gas-steam sibling touched. Rule 19 [R-ONE-MECH]: ONE seam, "
            "machine-verified at TWO grains — 16 of 393 built-fleet rows and 25 of "
            "327 LP rows move, all COAL, and ST_GAS (repriced by soco-53e one day "
            "earlier, and sharing plant codes 3 and 26 with this population), "
            "CT_PEAKER, CC_REGULAR, CC_CHP, CT_CHP, ST_CHP and hydro are "
            "byte-identical at max |delta| exactly 0.000000000000. Rule 25 "
            "[R-ISO-SCOPE] / 28(d): SOCO's own measurement over SOCO's own plants; "
            "NWPP's fills no cell here and this fills none of NWPP's. Rule 21 "
            "[R-DOF]: ZERO free parameters added, and zero ScenarioConfig fields."
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
            "scripts/gen_soco53f_attestation.py::_verify, which raises rather than "
            "writing a false assertion — including that the keeper's own four flags "
            "are carried forward and that none of the four default-off fields the "
            "PRECOMMIT's G-DRIFT audit classified INERT is armed. The SOCO-40 owner "
            'sitting of 2026-09-16 (verbatim: "I attest") covers the INHERITED '
            "posture this run does not change — the price posture, the identity offer "
            "bands, the three-zone topology, the served measured interchange, the "
            "coal split — but it predates and cannot speak to this lane's one new "
            "lever, so it is cited for what it covers and stretched no further. The "
            "promotion question is open and is put to the owner in the FINDING."
        ),
        "dof_basis": (
            "n_entries 3, n_residual 1 — UNCHANGED from the control, because this lane "
            "added no free parameter and no ScenarioConfig field. "
            "measured_coal_heat_rates is a measured-physical INPUT (a committed "
            "per-plant measurement of a machine's operating heat rate) with zero "
            "degrees of freedom: every applied number is "
            "sum(heatInput)/sum(grossLoad) over the plant's own steady hours, and the "
            "gross-to-net factor is the COMMITTED class default, not a value this "
            "lane chose. The deriver's four constants are nwpp-42's data-integrity "
            "guards, inherited rather than selected, and shown INERT by measurement "
            "on SOCO's own fleet — every plausible physical band moves the "
            "capacity-weighted result by less than 0.029 MMBtu/MWh and the UNBANDED "
            "value sits 0.0002 away — so the band is not a degree of freedom. "
            "REPORTED AGAINST THIS ENTRY, because it cuts against the lane: the "
            "committed COAL class parasitic default 0.93 does NOT reproduce SOCO's "
            "own meter, which reads 0.914-0.928 at Bowen and Miller and 0.866-0.885 "
            "at Scherer and Daniel. The committed chain is used anyway — it is the "
            "SAME factor the benchmark's net actual is built with, so the derived "
            "rate and the generation it is scored against share one boundary, and "
            "substituting a this-lane-measured number would BE the new free parameter "
            "this entry says there is none of. The consequence is stated rather than "
            "buried: the applied rates are biased LOW by 1.5 % (Bowen, Miller) to "
            "5.9 % (Scherer, Daniel) against each plant's own factor, so this arm's "
            "cheapening is if anything UNDERSTATED. The real repair is "
            "derive_parasitic_load.py --iso SOCO, a cross-ISO intake re-keying 544 "
            "plants in seven ISOs, and it is ROUTED."
        ),
    }

    att["disclosures"] = {
        "note": (
            "SOCO-53f determination basis. Everything the run does not establish, at "
            "full magnitude. The first three items are unflattering to this lane — one "
            "falsified ex-ante prediction, one untouched headline defect and one "
            "routed lever three times this one's size — and they lead for that reason. "
            "The SOCO keeper's inherited basis lines follow and are unchanged."
        ),
        "1_A_PREDICTION_OF_THIS_LANE_S_OWN_WAS_FALSIFIED_AND_IS_SCORED_AS_FALSIFIED": (
            "PRECOMMIT §6 P9 predicted the marginal emission rate would RISE — 'the "
            "P1 load-weighted mean moves +0.003 to +0.060 tCO2/MWh in every year', on "
            "the reasoning that coal (about 0.95 t/MWh) takes marginal hours from gas "
            "steam and peakers (0.45-0.65). IT FELL IN ALL THREE YEARS: 0.6263 -> "
            "0.6255 (-0.0008), 0.6090 -> 0.5921 (-0.0169), 0.6369 -> 0.6161 "
            "(-0.0207), and the p90 fell in 2024 (0.8717 -> 0.7121) and 2025 (1.0896 "
            "-> 1.0244) while rising in 2023 (0.8194 -> 0.8635). The prediction "
            "reasoned about which machine produces the ENERGY; what sets the MARGINAL "
            "rate is which machine sets the PRICE. Cheaper coal runs more "
            "INFRAMARGINALLY, so in the hours it takes over, the marginal unit "
            "becomes a combined cycle (about 0.37) rather than a peaker. The "
            "mechanism is coherent and the sign was mine to get right; it is recorded "
            "as a miss, not re-narrated as a success. Every value stays well inside "
            "the declared |delta| < 0.10 falsifier."
        ),
        "2_THE_ARM_DOES_NOT_FIX_SOCO_S_HEADLINE_DEFECT_AND_SAID_SO_FIRST": (
            "PRECOMMIT §4.3 registered, BEFORE the solve, that 2023's displaced class "
            "is 64 % ST_GAS and only 9 % CT_PEAKER, so a CT_PEAKER bound of 0.053 TWh "
            "closes about 0.5 % of a +9.8 TWh failure. Delivered: 2023 CT_PEAKER "
            "-0.0952 TWh, the row +9.85 -> +9.76 TWh and still the single C1 FAIL. "
            "SOCO's headline defect is untouched by this arm, as it was by SOCO-53c "
            "and SOCO-53e, and for the reason all three lanes recorded: the CT/ST "
            "misallocation is absent commitment physics, not a cost-side error. This "
            "arm is taken on rules 1 [R-STRUCT] and 14 [R-ACCURATE] and on no other "
            "ground."
        ),
        "3_A_LARGER_LEVER_ON_THE_SAME_ROWS_IS_ROUTED_NOT_TAKEN_AND_POINTS_THE_OTHER_WAY": (
            "SOCO's three PRB plants — 6002 Miller, 6073 Daniel, 6257 Scherer, "
            "6,361.5 MW = 55 % of SOCO's coal capacity — are priced off the "
            "hand-curated ERCOT-ONLY reporter pool at 1.8228 / 1.7520 / 1.6147 "
            "$/MMBtu (2023/24/25). SOCO's OWN three reporters paid 2.6711 / 2.4982 / "
            "2.4610, so the model under-prices their fuel by +0.85 / +0.75 / +0.85 "
            "$/MMBtu — 47-52 %, or about $9.7/MWh at a measured heat rate of 11.4, "
            "against this lane's -$2.95 at Scherer. coal_prb_proxy_own_iso is "
            "default-off, already built, and nwpp-42 left it for each ISO's own lane. "
            "SO THIS ARM MAKES COAL CHEAPER ON THREE PLANTS THE MODEL ALREADY PRICES "
            "FAR TOO CHEAP ON FUEL. That is stated at the gate. It is a reason to run "
            "SOCO-53g next and NOT a reason to stack it here: a single-delta arm is "
            "what makes either result attributable (rule 19 [R-ONE-MECH])."
        ),
        "4_the_rule_17_re_measurement_this_lane_OWED_was_performed_and_holds": (
            "The campaign floor reads a P0 pattern this arm perturbs, so the rule 17 "
            "[R-FLOOR-WINDOW] evidence had to be re-measured. Performed on this "
            "bundle's own floors/<year>_P1.npz with the tool first validated by "
            "reproducing the keeper's own table exactly: in ALL TWELVE plant-years "
            "the binding share stays at or below that plant's own measured "
            "synchronized share, and it FALLS OR HOLDS in every one — Greene County "
            "0.312/0.300/0.506 -> 0.309/0.295/0.496 (vs 0.752), E C Gaston "
            "0.203/0.106/0.184 -> 0.197/0.078/0.184 (vs 0.639), Yates "
            "0.134/0.536/0.749 -> 0.074/0.478/0.749 (vs 0.843), Jack Watson "
            "0.808/0.652/0.762 -> 0.808/0.652/0.753 (vs 0.920). Barry still carries "
            "ZERO floored unit-hours in all three years, the floored blocks keep a "
            "median length of 64-342 hours (campaigns, not gap fills), and the "
            "mechanism still touches ST_GAS and nothing else. ZERO exceedances. The "
            "direction was predicted: a cheaper coal fleet commits less gas steam in "
            "P0, so the campaigns the floor detects get shorter."
        ),
        "5_rule_20_forced_share_is_essentially_unmoved": (
            "ST_GAS forced share 0.0855 / 0.0966 / 0.1167 against the 30 % merchant "
            "cap (control 0.0917 / 0.0999 / 0.1157), so C8 passes on the budget and "
            "the escalation path is never entered. No COAL class carries a forced "
            "mechanism row at all, so the cap is not reached by the class this lane "
            "reprices."
        ),
        "6_D1_TRADES_A_VERDICT_IN_2024_AND_THE_2023_COAL_BIT_FAIL_IS_INHERITED": (
            "D-1 COAL_BIT 2023 FAILS on BOTH sides (profile_r 0.474 -> 0.469 against "
            "a 0.80 gate, cv_ratio 0.001 -> 0.003) — inherited, not this lane's, and "
            "the control reproduces the keeper's value to three decimals. In 2024 a "
            "verdict TRADES PLACES: COAL_BIT goes FAIL -> pass (profile_r 0.941 -> "
            "0.965, cv_ratio 0.179 -> 0.772) and COAL_PRB goes pass -> FAIL (cv_ratio "
            "0.521 -> 0.469, just under the 0.5 gate). Neither gates anything here: "
            "the standalone C7 diurnal-shape gate was retired at rubric v3.1, and D-1 "
            "binds through rule 20 [R-FORCED-BUDGET] only for a class OVER its "
            "forced-share cap, which no COAL class is — no COAL class carries a "
            "forced mechanism row at all. Reported because it moved, not because it "
            "scores."
        ),
        "7_THE_ARM_MAKES_THE_2025_COAL_EXCESS_WORSE_AND_THE_CAUSE_IS_A_MISSING_INPUT": (
            "2025 model coal is ALREADY above actual (COAL_PRB +2.75, COAL_BIT +0.88 "
            "TWh on the control) and this arm adds +1.5632 TWh more. The cause is not "
            "coal pricing: it is SOCO-53b's 2025 EIA-923 HYDRO INPUT HOLE — 2025 "
            "model hydro is 0.327 TWh against 6.012 TWh measured, and coal backfills "
            "the missing 5.68 TWh. The arm makes an artifact of a missing input "
            "worse. The fix is the input (--hydro-backfill-year / "
            "--hydro-eia930-monthly) and it is ROUTED, not absorbed; it was "
            "deliberately not taken here because it is a second delta on a different "
            "input, and it bites only in a year whose C1 rows are SKIPPED."
        ),
        "8_barry_unit_4_the_model_prices_362_MW_as_coal_and_CAMPD_files_it_as_gas": (
            "UNCHANGED FROM SOCO-53d/53e, AND THIS LANE NOW MEASURES WHAT IT COSTS. "
            "CAMPD files Barry unit 4 (a 330 MW boiler) as Pipeline Natural Gas while "
            "the model carries it as a 362 MW COAL row, so nwpp-42's primaryFuelInfo "
            "selection EXCLUDES it and Barry's applied rate comes from unit 5 alone "
            "(7,789 steady hours). The artifact is at plant grain, so that rate lands "
            "on both COAL rows. Measured: unit 4's own operating rate over 10,422 "
            "in-band steady hours is 11.0878 gross -> 11.9224 net. So the arm takes "
            "3_5 (756.5 MW) from 1.87 wrong to EXACTLY right and 3_4 (362.0 MW) from "
            "0.69 too dear to 1.18 too cheap — a +1.11 MMBtu/MWh capacity-weighted "
            "improvement on the plant. Both legs are at full magnitude. The deeper "
            "defect is that unit 4 burns GAS and the model charges it a COAL fuel "
            "price; that is a class-assignment question and belongs to a lane that "
            "can change the assignment, not to one that reads it."
        ),
        "9_marginal_emission_rate_is_carried_by_this_bundle": (
            "Every hourly/system_<year>.parquet carries marginal_emission_rate. P1 "
            "load-weighted mean 0.6255 / 0.5921 / 0.6161 tCO2/MWh on this arm against "
            "0.6263 / 0.6090 / 0.6369 on the control; p10 0.4187 / 0.3833 / 0.3833 "
            "(unchanged in every year); median 0.5905 / 0.5810 / 0.5848; p90 0.8635 / "
            "0.7121 / 1.0244 against the control's 0.8194 / 0.8717 / 1.0896; "
            "zero-share 0.00 / 0.00 / 0.15 %, unchanged. See disclosure 1 — this is "
            "the falsified prediction, reported at full magnitude."
        ),
        "10_THE_BENCHMARK_MOVED_UNDER_THIS_LANE_AND_IT_IS_ANOTHER_LANE_S_REPAIR": (
            "This run and its control are scored on an EIA-923 snapshot rebuilt at "
            "HEAD, which carries nyiso-240's benchmark repairs "
            "(_backfill_eia923_missing_months and _reattribute_dual_fuel_oil, commit "
            "03eed7e9) — a shared BENCHMARK path, not a solve path. On SOCO that adds "
            "+2.616 TWh of benchmark generation across 126 of about 1,048 rows, "
            "concentrated in January (+1.048), June (+1.023), February (+0.296) and "
            "August (+0.249) — the signature of respondent-withheld months being "
            "backfilled. The campd and eia930 snapshots rebuild BYTE-IDENTICAL to the "
            "keeper's. THE DECOMPOSITION IS EXACT AND IS THE POINT: the control's "
            "DISPATCH is identical to the keeper's to 0.000000 MWh on every class in "
            "every year, so every difference between the keeper's registered C1 "
            "numbers and this control's is the benchmark repair and NONE of it is "
            "this lane's mechanism."
        ),
        "11_THE_KEEPER_S_E14_DEPENDENCY_QUESTION_IS_CLOSED_BY_MEASUREMENT": (
            "SOCO's keeper solved on UNPINNED dependencies (highspy 1.15.1 / pandas "
            "3.0.6 / pyarrow 25.0.1 / pydantic 2.13.5 against requirements.txt's "
            "1.14.0 / 3.0.3 / 24.0.0 / 2.13.4), which fires audit_keepers E14 four "
            "times, and FINDING-soco-53e §10.3 recorded the confirming re-solve as "
            "ABANDONED, so the question was BOUNDED and not closed. This lane closed "
            "it directly: a seventh shard solved the control recipe for 2023 on the "
            "keeper's OFF-PIN set, everything else identical. The result is "
            "BIT-IDENTICAL to the pinned control — 0 of 131,400 class-hourly cells "
            "moved, 0 of 26,280 price cells, 0 of 26,280 marginal-emission cells. The "
            "four E14 warnings on SOCO's keeper are cosmetic provenance: no scored "
            "quantity depends on them."
        ),
        "12_RULE_36_YEAR_ISOLATION_COSTS_SOCO_NOTHING_MEASURABLE": (
            "SOCO's keeper was solved as ONE three-year span at a basis where "
            "cross-year warm start and the same-year P1 basis seed both defaulted ON; "
            "rule 36 [R-YEAR-ISOLATION] withdrew their neutrality claim on 2026-09-19 "
            "and says the cost is 'unmeasured outside MISO'. Measured here, on SOCO: "
            "the year-isolated control reproduces the keeper's annual class "
            "generation to EXACTLY 0.000000 MWh on all 45 class-years. What does move "
            "is intra-class timing — 279 / 364 / 32 distinct hours of 8,760 (3.18 / "
            "4.16 / 0.37 %), every moved cell offset within its own class, mostly "
            "hydro (monthly-energy-budgeted by construction) — and prices on 1,119 / "
            "1,734 / 123 cells of 26,280 by at most 1.4e-14 / 0.0136 / 0.141 $/MWh. "
            "That is the degenerate-alternate-optimum signature, four orders of "
            "magnitude below MISO's 7-24 TWh, and immaterial to every scored "
            "quantity."
        ),
        "13_2025_IS_REPORTED_BUT_NOT_GATED_AND_THAT_BINDS_THIS_LANE_S_RESULT": (
            "INHERITED FROM SOCO-40, UNCHANGED. On the preliminary EIA-923 vintage "
            "every 2025 C1 row is SKIPPED by the scorer (CT_PEAKER 17/23 plants "
            "unfiled, ST_GAS 1/7, CC_CHP 5/6, ST_CHP 17/26). 2025 is where this arm "
            "moves the most (COAL +1.5632 TWh), and NONE of it is gated. The gated "
            "evidence is 2023 and 2024 only."
        ),
        "14_pre_existing_defects_inherited_unchanged": (
            "The 2025 EIA-923 hydro input hole (see disclosure 7; hydro is "
            "byte-identical in all three years here, confirming this seam does not "
            "touch it); 1,306.6 MW of pumped storage UNOBSERVABLE in EIA-930; "
            "Southern Power (186) excluded from the FERC-714 zonal shares as a "
            "documented NO, its 3.211 / 3.401 / 3.084 TWh named and never absorbed; "
            "and the Vogtle 3/4 COD month grain leaving nuclear -0.220 / -0.144 / "
            "-0.245 TWh, byte-identical here."
        ),
        "15_a_shared_contract_test_gains_one_more_offender_and_was_NOT_patched": (
            "tests/unit/config/test_data_profiles_tokens.py::"
            "test_soco_token_collides_with_no_other_raw_name is RED at HEAD and this "
            "lane's artifact adds one more offender, in the established convention "
            "(campd_coal_heat_rates_SOCO.csv, exactly as the committed "
            "campd_ct_heat_rates_SOCO.csv and campd_st_heat_rates_SOCO.csv). Verified: "
            "it fails identically with and without this lane's file. The fix is a "
            "naming-convention decision across every SOCO artifact and belongs to the "
            "SOCO desk, not to a lane that would be silently patching a shared "
            "contract test to make its own PR green."
        ),
        "16_the_price_gap_is_structural_and_permanent": (
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
