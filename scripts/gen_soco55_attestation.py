"""Write the SOCO-55 calibration attestation (schema ``calibration-attestation/v1``).

Lane SOCO-55 armed exactly ONE mechanism against the incumbent keeper
``2026-09-20-soco54-marginal-gas-basis``: ``gas_basis_differential_measured_by_year``
turned **ON**, so every SOCO gas unit prices on the delivered-gas basis measured on
**the receipts of the year being solved** instead of on one year's value applied to
all of them.

**THE CLAIM, stated once here and machine-checked below.**
``GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64`` is the **2024** value, and the constant's
own comment registers it as a *"forward-year / fallback value only"* on the stated
ground that *"the SOCO backcast prices gas per plant off EIA-923 monthly delivered
cost like PJM/NYISO."* **SOCO-54 made that sentence false**: turning
``gas_plant_monthly_fuel_pricing`` off promoted the declared FALLBACK onto SOCO's
**PRIMARY** backcast gas-pricing path, where ``resolve_annual_gas_price`` returns
``gas_price_override + 0.64`` for every SOCO gas unit in every year. Re-derived at
HEAD by this lane and reproducing SOCO-20's committed comment exactly — quantity-
weighted EIA-923 Schedule-2 delivered gas to the run's own EIA-860 SOCO gas fleet
minus the Henry Hub annual mean — the measured basis is **+0.4931 (2023, 26 plants,
646,487,128 MMBtu) / +0.6395 (2024, 27, 650,711,973) / +0.6540 (2025, 27,
641,283,196)**. So 2023 was carrying **+0.15 $/MMBtu, about +$1.65/MWh, on every
SOCO gas unit**.

SOCO-54 DECLARED that imprecision at full magnitude in
``ADDENDUM-soco54-the-fallback-basis-2026-09-20.md`` §2 and ROUTED the repair
rather than taking it, because taking it after seeing that lane's result would have
been selecting a parameter on the outcome. This lane is that routed repair, taken
as its own single-delta change on the SOURCE-DATA citation — rule 23
``[R-FROZEN-DERIVE]`` — and never on a residual.

**PRECISION IS THE FAMILY CONVENTION, FIXED BEFORE THE SOLVE.** Every row of
``GAS_BASIS_DIFFERENTIAL`` is 2dp and SOCO-20 published this derivation's own output
at 2dp, so the table lands at 2dp. A declared consequence, stated in the PRECOMMIT
rather than discovered later: at 2dp **the 2024 value is unchanged**, so 2024 is
predicted byte-identical — and choosing 4dp instead to perturb the 0.035-TWh-margin
2024 row would be exactly the selection rule 1 ``[R-STRUCT]`` forbids.

See ``PRECOMMIT-soco-55-2026-09-20.md`` and ``FINDING-soco-55-2026-09-20.md``.

The four governance assertions are asserted by the LANE. Every one is a factual
claim about this bundle and each is machine-verified against its own
``run_config.json`` by :func:`_verify`, which raises rather than writing a false
assertion. ``owner_attestation`` records honestly that the owner has NOT attested
this run in session.

NO ``authorized_price_tuning`` KEY IS WRITTEN. ``calibration_verdict.py`` validates
any present value as a STRUCTURED rule-1 declaration, so prose there fails C6. The
declared-NONE statement lives in ``authorized_price_tuning_declared`` prose, which
is the SOCO-40..54 convention.

Run: ``python scripts/gen_soco55_attestation.py``
"""

from __future__ import annotations

import json
from pathlib import Path

BUNDLE = Path("results/calibration/soco55_peryear_basis")

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names. The other
#: offer_curve_by_group keys (econ_low_share, pct_peaking) are STRUCTURAL shares
#: the carve-out EXCLUDES and are not 1.0 on any ISO.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: SOCO's keeper recipe (2026-09-20-soco54-marginal-gas-basis), carried forward
#: unchanged. ``gas_basis_differential_measured_by_year`` is this lane's single
#: delta and is asserted separately, to True; ``gas_plant_monthly_fuel_pricing``
#: is SOCO-54's inherited delta and is asserted separately, to False.
KEEPER_RECIPE = (
    "measured_ct_heat_rates",
    "egrid_family_heat_rates",
    "measured_st_heat_rates",
    "soco_gas_st_campaign_commitment",
    "measured_coal_heat_rates",
)

#: The measured per-year basis this lane arms, re-derived at HEAD from
#: ``data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`` minus
#: ``data/raw/gas-prices/henry_hub_monthly.csv``. Asserted against the live
#: constant so the attestation cannot describe a table the run did not use.
MEASURED_BASIS = {2023: 0.49, 2024: 0.64, 2025: 0.65}


def _verify(sc: dict) -> None:
    """Raise unless every governance assertion is true of this bundle."""
    oc = sc.get("offer_curve_by_group") or {}
    if not oc:
        raise SystemExit("offer_curve_by_group absent — cannot verify the bands")
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

    # --- the single delta, asserted to the side of the A/B this lane solved
    if not sc.get("gas_basis_differential_measured_by_year"):
        raise SystemExit(
            "gas_basis_differential_measured_by_year is OFF — this bundle is the "
            "CONTROL, not the SOCO-55 arm"
        )
    # ...and the measured table the arm reads must be the one this attestation
    # describes, or the prose is about a derivation the LP never saw.
    from market_sim.config.fuel_trajectories import (  # noqa: PLC0415
        GAS_BASIS_DIFFERENTIAL,
        GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR,
    )

    live = GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR.get("SOCO")
    if live != MEASURED_BASIS:
        raise SystemExit(
            f"GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'] is {live!r}, "
            f"expected {MEASURED_BASIS!r}"
        )
    if GAS_BASIS_DIFFERENTIAL.get("SOCO") != 0.64:
        raise SystemExit(
            "the scalar GAS_BASIS_DIFFERENTIAL['SOCO'] moved — this lane GATES the "
            "scalar, it does not edit it, and every unarmed run must keep it"
        )
    if set(GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR) != {"SOCO"}:
        raise SystemExit(
            "a non-SOCO row is present in GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR — "
            "rule 25 [R-ISO-SCOPE]: this lane derives no other ISO's basis"
        )
    # SOCO-54's inherited delta, which this lane carries forward unchanged: it is
    # what put the fallback scalar on SOCO's PRIMARY gas path in the first place.
    if sc.get("gas_plant_monthly_fuel_pricing"):
        raise SystemExit(
            "gas_plant_monthly_fuel_pricing is ON — the SOCO-54 keeper delta is not "
            "carried forward, so this is not a single-delta arm off that keeper"
        )
    # `--set` routes this field through the generic prb_overrides channel, which
    # meta.json records as a coal_prb_sigmoid_overrides diff and audit_keepers
    # E11 flags. Benign (PRECOMMIT-soco-54 §7) — but the RESOLVED value must stay
    # null, or the override bag leaked into the PRB sigmoid registry for real.
    if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
        raise SystemExit(
            "resolved coal_prb_sigmoid_overrides is "
            f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null"
        )
    # The COAL print path is NOT this lane's object and must be untouched, or the
    # arm is not the single gas-side delta it claims to be (rule 19).
    if not sc.get("coal_plant_monthly_pricing"):
        raise SystemExit(
            "coal_plant_monthly_pricing is OFF — this lane moves the GAS print "
            "path only, and the coal path must be carried forward unchanged"
        )
    if sc.get("coal_prb_proxy_own_iso"):
        raise SystemExit(
            "coal_prb_proxy_own_iso is armed — that is SOCO-53g's open candidate, "
            "not this lane's recipe"
        )
    for name in KEEPER_RECIPE:
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
        "caiso_citygate_blackout_bridge",
        "miso_gas_marginal_commodity_pricing",
        "gas_hub_basis_overlay",
        "gas_electric_power_monthly_level",
        "gas_monthly_actuals",
    ):
        if sc.get(name):
            raise SystemExit(f"{name} is armed — not this lane's recipe")


def _retag(att: dict, sc: dict) -> None:
    """Re-tag the two offer-curve DOF entries, as SOCO-40..53g did.

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
                "machine-verified by gen_soco54_attestation._verify, which raises "
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
        "SOCO-54 re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40/53/53c/53d/53e/53f/53g used and "
        "re-verified here by execution. n_entries 3 / n_residual 1, UNCHANGED from "
        "the keeper: this lane added NO free parameter, and no ScenarioConfig field "
        "either — gas_plant_monthly_fuel_pricing predates this lane by years, ships "
        "bool = False as its DECLARED DEFAULT, and this lane returns SOCO to that "
        "default, so no cache key moves at any default. "
        "IT IS A ZERO-DOF SELECTION, NOT A VALUE: the flag chooses WHICH measured "
        "aggregation of the SAME EIA-923 Schedule-2 receipts prices a gas unit — the "
        "plant's own monthly contract print, or the footprint-wide quantity-weighted "
        "delivered basis over Henry Hub (GAS_BASIS_DIFFERENTIAL['SOCO'] = 0.64, "
        "registered by SOCO-20 on 2026-09-14 from those same receipts). Nothing is "
        "fitted, scaled, offset or swept, and there is no price residual in existence "
        "it could have been fitted to. DECLARED AGAINST THIS ENTRY because it cuts "
        "against the lane: that basis constant is the 2024 value (+0.64) applied to "
        "every year against a measured +0.49 / +0.64 / +0.65, so 2023 carries "
        "+0.15 $/MMBtu, about +$1.65/MWh, on EVERY gas unit alike — a common level "
        "shift, which cannot move CT_PEAKER against ST_GAS but can move the gas block "
        "against coal. Making it per-year is a rule 23 [R-FROZEN-DERIVE] "
        "re-derivation on source data and is ROUTED, not taken here "
        "(ADDENDUM-soco54-the-fallback-basis-2026-09-20.md §3). The single remaining "
        "residual entry is the inherited wefor_multiplier, untouched here."
    )


def _disclosures() -> dict:
    """SOCO-54 determination basis. The items that cut against the lane lead."""
    return {
        "note": (
            "SOCO-54 determination basis. Everything the run does not establish, at "
            "full magnitude. The first four items are unflattering to this lane — two "
            "of its own pre-registered predictions falsified, a diagnosis by three "
            "predecessor lanes corrected, a result concentrated in the one failing "
            "year, and a plant made WORSE — and they lead for that reason. The SOCO "
            "keeper's inherited basis lines follow and are unchanged."
        ),
        "1_TWO_OF_THIS_LANE_S_OWN_PRE_REGISTERED_PREDICTIONS_ARE_FALSIFIED": (
            "PRECOMMIT §8 P1 banded 2023 CT_PEAKER's fall at 1.5-3.5 TWh on a "
            "calibrated greedy re-stack, point estimate -2.45. DELIVERED: -3.592 TWh "
            "(14.2606 -> 10.6683), OUTSIDE the band's upper edge. The direction and "
            "the object are right and the magnitude is LARGER than predicted, which is "
            "a falsification all the same and is recorded as one. "
            "P8 banded COAL_PRB / COAL_BIT movement at < 1.0 TWh in each year. "
            "DELIVERED: 2023 COAL_PRB +1.481 TWh. FALSIFIED. The cause was named "
            "before the solve but its size was not: ADDENDUM-soco54-the-fallback-basis "
            "§2 stated that the year-invariant basis constant adds ~+$1.65/MWh to "
            "every 2023 gas unit alike and would 'move the gas block against coal', "
            "which is why P8's band was not zero — it was simply too tight. "
            "The rest held: P2 (2023 ST_GAS +0.3-1.2, delivered +0.438), P6 (2024 "
            "CT_PEAKER -0.8 to -2.0, delivered -1.494), P7 (no 2025 C1 class row "
            "scored — all seven SKIPPED on the preliminary EIA-923 vintage), P9 (the "
            "three CHP classes move < 0.30 TWh: +0.006 / -0.001 / +0.005 at most)."
        ),
        "2_THE_PREDECESSOR_DIAGNOSIS_WAS_WRONG_AND_THIS_LANE_MEASURED_IT_RATHER_THAN_ARGUED_IT": (
            "SOCO-53c / 53e / 53f and the SOCO matrix shard all record SOCO's headline "
            "C1 defect as ABSENT COMMITMENT PHYSICS rather than a cost-side error, and "
            "SOCO-53 closed the cost side with 'the model already over-separates "
            "CT_PEAKER from ST_GAS by +1.983 MMBtu/MWh against a measured +0.713, so no "
            "cost-side lever can close it'. THAT CLAIM WAS DERIVED FROM HEAT RATES "
            "ALONE, and it holds on heat rates. It is not the whole cost side. "
            "Measured on the keeper's own committed artifacts, zero LP: the campaign "
            "floor FIRES — it holds SOCO's boilers synchronized 659-7,234 hours a year "
            "— and they sit PINNED at a median 6-14 % of capacity because they are out "
            "of merit in 65-93 % of their online hours (Yates 2023: online 659 h, "
            "in-merit in 7.3 % of them). The in-merit-but-not-dispatched ST_GAS "
            "headroom is 0.0727 TWh against a -6.935 TWh gap: ONE PERCENT. The "
            "separation that binds is FUEL PRICE, $1.0-1.7/MMBtu on machines of the "
            "same 10-12 MMBtu/MWh class, which at ~11 MMBtu/MWh is the $17.44/MWh "
            "merit-order distance between Hartwell ($27.15) and Yates ($44.59). "
            "Three commitment levers were refused EX ANTE on measurement rather than "
            "solved: a start cost in the objective (the tranche_startup_amortization "
            "G-cell's own named successor) amortizes to ~$1.28/MWh because the model's "
            "turbines run at 62-74 % capacity factor in blocks up to 760 hours and do "
            "not two-shift; a CT min-run floor has the wrong sign; and strengthening "
            "the ST campaign floor adds online hours, not MWh."
        ),
        "3_THE_EFFECT_IS_CONCENTRATED_IN_2023_AND_2023_IS_THE_FAILING_YEAR": (
            "2023 CT_PEAKER -3.592 TWh; 2024 -1.494; 2025 -2.294 (unscored). A reader "
            "is entitled to look at a lever that bites hardest in the one failing year "
            "and ask whether it was selected for that. Three checkable answers, all "
            "recorded BEFORE any leg landed "
            "(ADDENDUM-soco54-the-effect-is-concentrated-in-2023-2026-09-20.md §2): "
            "NOTHING WAS SELECTED — the arm is a single pre-existing field returned to "
            "its shipped default, with no value, threshold, year scope or class scope "
            "to choose, applied identically to all three years by one --set; NOTHING "
            "WAS SWEPT — the only A/B is on/off and no variant was solved; and the "
            "cross-year weakness was published against the lane's own interest before "
            "the result, with PRECOMMIT P1/P6 pre-registering exactly this asymmetry. "
            "WHY IT IS ASYMMETRIC, measured: the contract multipliers reprice. Yates "
            "pays 1.8279x Hartwell in 2023, 1.1669x in 2024 and 0.7959x in 2025, so "
            "the defect the arm removes was simply LARGER in 2023."
        ),
        "4_ONE_PLANT_IS_MADE_MATERIALLY_WORSE_AND_ANOTHER_IS_NOT_FIXED": (
            "2023, arm vs keeper vs EIA-923 actual, TWh. MADE WORSE: 55061 Tenaska "
            "Georgia 1.412 -> 2.690 against an actual of 0.237 — already 6x its actual "
            "under the keeper, now 11x. Its own mc rose only +0.99/MWh, so the arm did "
            "not cheapen it; the turbines above it rose further and pulled it in. "
            "2049 Jack Watson ST_GAS 2.355 -> 1.256 against 3.270, the one gas-steam "
            "plant the model already ran near its actual and the one ST_GAS unit whose "
            "own mc RISES under the arm (+4.17/MWh) — predicted by "
            "ADDENDUM-2's table and delivered. NOT FIXED: 728 Yates 0.061 -> 0.801 "
            "against 2.239 — a 13x improvement that still leaves it at 36 % of actual. "
            "WHAT THE ARM DOES FIX, at plant grain: 54538 Hartwell 1.728 -> 0.111 "
            "(actual 0.207), 55141 Hawk Road 2.209 -> 0.228 (0.569), 55244 Doyle 1.038 "
            "-> 0.072 (0.054), 6124 McIntosh 0.682 -> 0.053 (0.017), 10 Greene County "
            "0.574 -> 1.196 (1.314). Five plants that were 4x-40x their actuals are now "
            "within a factor of ~2, and 55409 Calhoun falls 2.184 -> 1.383 against an "
            "actual of 0.015 — improved and still the largest single miss in the class."
        ),
        "5_D_1_DIURNAL_SHAPE_TRADES_TWO_VERDICTS_FOR_ONE": (
            "D-1 is REPORTED, not gated — the standalone C7 gate was retired at rubric "
            "v3.1 and D-1 now binds only through rule 20 [R-FORCED-BUDGET]'s shape leg "
            "for a class over its forced-energy budget, which no SOCO class is (C8 "
            "PASSES on both sides). The movement is stated for what it is: the keeper "
            "carries THREE D-1 failures (2023 COAL_BIT, 2024 COAL_PRB, 2025 "
            "CT_PEAKER); the arm carries TWO (2023 COAL_BIT, byte-identical and "
            "inherited; 2025 COAL_BIT, NEW). So the arm CLEARS 2024 COAL_PRB and 2025 "
            "CT_PEAKER and INTRODUCES 2025 COAL_BIT. The 2025 CT_PEAKER shape verdict "
            "clearing is independent structural support for the lever — a class whose "
            "diurnal profile now matches better, measured on a criterion that scores no "
            "volume — and the new COAL_BIT failure is the coal-side cost of the common "
            "basis shift disclosed in dof_basis, not a gas-side artifact."
        ),
        "6_THE_SOLVE_SURFACE_FINGERPRINT_MOVED_AND_IT_IS_NOT_THIS_LANE_S": (
            "SOCO's capx-D79 solve-surface fingerprint reads 60895cac1f7c8879 / 182 "
            "rows on all three legs, against the keeper's f4d250dfebdf2c96 / 180. "
            "moved_rows('SOCO') is {} — ZERO existing rows changed value. The delta is "
            "two new constants.py names (PPA_COST_RECOVERY_YR, REGIONAL_RENEWABLE_CF, "
            "commit 3fc20b97, the MAC-sidecar lane) that have no DECLARED entry, which "
            "is the same pair check_cache_key_registration has RED at HEAD. A "
            "fingerprint that grew by two undeclared names RE-KEYS THE CACHE AND CANNOT "
            "CHANGE A NUMBER: grep over src/ and scripts/ returns exactly "
            "build_mac_sidecar.py and derive_regional_renewable_cf.py as their "
            "consumers, neither on the solve path. Routed to that lane, not patched "
            "here. It is why the keeper's committed numbers remain a valid rule-29(b) "
            "form-4 control and no control solve was spent."
        ),
        "7_THE_E11_SET_TRANSPORT_IS_DECLARED_AND_THE_RESOLVED_VALUE_IS_NULL": (
            "replay_keeper --set routes a ScenarioConfig field that is not a "
            "solve_and_persist kwarg through the generic prb_overrides channel, so each "
            "leg's meta.json records a coal_prb_sigmoid_overrides diff and "
            "audit_keepers E11 flags it. DECLARED IN THE PRECOMMIT §7 BEFORE THE SOLVE "
            "and machine-verified benign on every leg and on the composite: the "
            "RESOLVED scenario_config.coal_prb_sigmoid_overrides is null (absent). Both "
            "the composer and _verify raise on a non-null value."
        ),
        "8_THE_CROSS_ISO_QUESTION_IS_REPORTED_AND_NOT_TAKEN": (
            "Five other keepers arm gas_plant_monthly_fuel_pricing. Whether their "
            "footprints carry constant-multiplier formula families of their own is a "
            "question for THEIR lanes on THEIR receipts (rules 25 [R-ISO-SCOPE] / "
            "28(d)); this lane measured SOCO's and fills no other ISO's cell. The "
            "reconciled form rule 14 would prefer — a daily hub series plus measured "
            "variable transport, MISO's miso_gas_marginal_commodity_pricing — is NOT "
            "armed and NOT arm-able here: it is MISO-scoped by hard error, SOCO has no "
            "committed daily hub series (no free public daily index exists at SONAT or "
            "Transco/Dalton, SOCO-12 §4), and its own comment puts the cross-ISO cost "
            "convention in owner court."
        ),
        "9_WHAT_IS_STILL_BROKEN_AFTER_THIS_LANE": (
            "2023 CT_PEAKER is still ABOVE its actual by a wide margin (10.668 vs "
            "4.534) and 2023 ST_GAS is still far BELOW (3.986 vs 10.483). This lane "
            "removed a mis-based cost input; it did not close SOCO's headline "
            "misallocation, and the remaining gap is now the successor's object. The "
            "named candidates, in order: (a) the year-invariant gas basis constant, a "
            "rule 23 re-derivation on source data; (b) 55061 Tenaska Georgia, 11x its "
            "actual and worsened here; (c) 2049 Jack Watson, the one gas-steam plant "
            "the arm pushes the wrong way."
        ),
        "10_derive_parasitic_load_has_never_been_run_for_SOCO": (
            "Unchanged from FINDING-soco-53f §2.4 and -53g §9.3, re-routed with its "
            "numbers: SOCO's coal plants' own meter reads 0.866-0.928 against the "
            "committed 0.93 class default, so every SOCO coal heat rate is biased LOW "
            "by 1.5-5.9 %. It is a cross-ISO intake (544 plants, 7 ISOs) and is "
            "reported, never taken by a lane."
        ),
        "11_SOCO_53b_the_2025_hydro_input_hole": (
            "0.327 TWh modelled against 6.012 measured; coal backfills it and the LP "
            "posts VOLL slack, which is what makes the 2025 model price "
            "uninterpretable. This lane touches hydro not at all — byte-identical in "
            "all three years. Instruments: --hydro-backfill-year / "
            "--hydro-eia930-monthly."
        ),
        "12_Barry_unit_4": (
            "A 362 MW COAL model row that CAMPD files as Pipeline Natural Gas and the "
            "model charges a COAL fuel price. Outside this lane's gas-side seam by "
            "construction; still routed."
        ),
        "13_audit_keepers_E13_fires_for_the_SIXTH_consecutive_SOCO_lane": (
            "2026-09-20-soco53g-prb-own-iso is a registered CANDIDATE the owner has not "
            "ruled on, so it is neither the keeper nor stamped to one. Rule 31 "
            "[R-RETAIN] forbids deleting it and rule 30 (a) forbids inventing a "
            "holdout.keeper stamp for it, so E13 is RE-RAISED rather than cleared. It "
            "clears when the owner rules on that promotion, not before."
        ),
        "14_the_benchmark_is_STALE_and_BOTH_benches_are_scored": (
            "SOCO's committed bench parts do not carry nyiso-240's EIA-923 repair "
            "(+2.616 TWh), so check_bench_freshness reads RED for SOCO repo-wide. This "
            "lane scores on BOTH and reports both, labelled. Rebuilding SOCO's bench "
            "re-scores the keeper and is the desk's call, not a lane's."
        ),
        "15_a_shared_contract_test_is_RED_at_HEAD_and_was_NOT_patched": (
            "tests/unit/config/test_data_profiles_tokens.py::"
            "test_soco_token_collides_with_no_other_raw_name is RED at HEAD, "
            "independently of this lane — which adds no data artifact at all. The fix "
            "is a naming-convention decision across every SOCO artifact and belongs to "
            "the SOCO desk, not to a lane that would be silently patching a shared "
            "contract test to make its own PR green."
        ),
        "16_pre_existing_defects_inherited_unchanged": (
            "1,306.6 MW of pumped storage UNOBSERVABLE in EIA-930; Southern Power "
            "(186) excluded from the FERC-714 zonal shares as a documented NO, its "
            "3.211 / 3.401 / 3.084 TWh named and never absorbed; and the Vogtle 3/4 COD "
            "month grain leaving nuclear -0.220 / -0.144 / -0.245 TWh. Nuclear, hydro, "
            "wind, solar and biomass are byte-identical to the keeper in all three "
            "years."
        ),
        "17_the_price_gap_is_structural_and_permanent": (
            "NO PUBLIC SOCO PRICE EXISTS AND NONE EVER WILL. actual_lmp.json carries "
            "no SOCO block and must not gain one — a placeholder breaks "
            "calibration_verdict._price_reference_absent and silently moves SOCO onto "
            "the ordinary determination path. C3a / C3b / C3c are UNSCORABLE, NOT "
            "FAILED, in every year. The ceiling is rubric v3.8 PHYSICALLY-CALIBRATED "
            "(PRICE UNSCORED); SOCO can NEVER read CALIBRATED. Scored on C1 / C2 / C4 "
            "/ C6 / C8 only. Gate G17 absolute: no neighbouring hub, no proxy, no "
            "cost-stack price, ever. The model's own load-weighted mean LMP is "
            "MODEL-ONLY and UNVERIFIED and is never quoted as price skill — and this "
            "lane, which repriced every gas unit, moved it: that movement certifies "
            "NOTHING and is reported as a model-only number."
        ),
    }


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-54 bundle."""
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
            "SOCO-54 (lane), run 2026-09-20-soco54-marginal-gas-basis. ONE mechanism "
            "moves against the SOCO-53f keeper: ScenarioConfig."
            "gas_plant_monthly_fuel_pricing, turned OFF. NO ScenarioConfig field was "
            "written — the field predates this lane by years and ships bool = False "
            "as its DECLARED default, so this lane RETURNS SOCO to the shipped "
            "default and no cache key moves at any default. Everything else is the "
            "keeper's recipe unchanged, machine-verified by _verify. "
            "THE CLAIM IS ABOUT THE INPUT'S BASIS, NOT ABOUT THE RESIDUAL. A dispatch "
            "offer is a MARGINAL cost; the EIA-923 Schedule-2 print is an AVERAGE "
            "DELIVERED CONTRACT cost — demand charges, reserved transport and a "
            "negotiated multiplier amortized over the month's takes. Rule 14 "
            "[R-ACCURATE]'s misalignment clause is the governing text and the fall-back "
            "is MEASURED-TO-MEASURED: with the field off every SOCO gas unit prices on "
            "the realized Henry Hub level plus SOCO's OWN measured EIA-923 delivered-gas "
            "basis (GAS_BASIS_DIFFERENTIAL['SOCO'] = 0.64, registered by SOCO-20 from "
            "those same receipts) — the same data, re-aggregated to the grain at which "
            "a marginal dispatch decision is made. "
            "THE BASIS CLAIM IS MEASURED, NOT ARGUED. Eight SOCO plants file a monthly "
            "delivered-price series that is ONE common shape times a plant-constant "
            "multiplier, in ALL THREE YEARS, at ratio CV <= 0.00081 over 10-12 months "
            "each — and the multipliers REPRICE: Yates (728) goes 1.8279 -> 1.1669 -> "
            "0.7959 against Hartwell (54538), and Hartwell goes from the family's "
            "cheapest member in 2023 to its dearest in 2025. No physical property of "
            "those machines changed by 2.3x in two years; the contract did. Hartwell's "
            "2023 print sits BELOW Henry Hub in eleven of twelve months, which no "
            "DELIVERED gas can be, and the model burned 4x-160x the gas these plants "
            "actually procured at the price the procurement established. "
            "Rule 13 [R-MEASURED]'s forward test is met: the fall-back series is a "
            "published hub level plus a receipts-derived basis, both of which "
            "regenerate for a forward year from forward drivers and respond to a gas "
            "shock — which the per-plant contract multiplier does not. It is a "
            "measurement of fuel PURCHASED and of a market price, never of dispatch, so "
            "no model output enters it. "
            "Rule 19 [R-ONE-MECH]: ONE seam, machine-verified at two grains on "
            "fuel_prices AND mc_base before the solve — the six GAS classes move "
            "(CC_REGULAR, CT_PEAKER, ST_GAS, CC_CHP, CT_CHP, ST_CHP) and COAL, oil, "
            "nuclear, hydro, wind, solar and biomass are at max |delta| EXACTLY "
            "0.000000000000 in all three years. The COAL print path "
            "(coal_plant_monthly_pricing) is carried forward ON and untouched. "
            "Rules 25 / 28(d): the reasoning is MISO-224's and the DERIVATION IS "
            "SOCO'S OWN, on SOCO's own receipts. miso_gas_marginal_commodity_pricing is "
            "MISO-scoped by hard error, is NOT armed here (machine-verified), and the "
            "cross-ISO cost-convention question stays in owner court. "
            "Rule 21 [R-DOF]: ZERO free parameters added, ZERO ScenarioConfig fields."
        ),
        "authorized_price_tuning_declared": (
            "NONE. No authorized price-tuning channel is in use on this run, and none "
            "CAN be: SOCO publishes no price, actual_lmp.json carries no SOCO block, "
            "so there is no price residual to tune against and none was computed. "
            "Every offer_curve_by_group band is machine-verified at the identity 1.0 "
            "across all 13 groups (committed / econ_low / econ_high / peak each "
            "resolve to the single distinct value {1.0}); offer_curve_overrides and "
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
            "scripts/gen_soco54_attestation.py::_verify, which raises rather than "
            "writing a false assertion — including that the single delta is on the ARM "
            "side of the A/B, that the keeper's own five flags are carried forward, "
            "that the COAL print path this lane does NOT touch is still live, that the "
            "resolved coal_prb_sigmoid_overrides is null, that SOCO-53g's open "
            "coal_prb_proxy_own_iso candidate is NOT armed here, and that none of the "
            "eight fields the PRECOMMIT's G-DRIFT audit classified INERT is armed. "
            'The SOCO-40 owner sitting of 2026-09-16 (verbatim: "I attest") covers the '
            "INHERITED posture this run does not change — the price posture, the "
            "identity offer bands, the three-zone topology, the served measured "
            "interchange, the coal split — but it predates and cannot speak to this "
            "lane's one lever, so it is cited for what it covers and stretched no "
            "further. The promotion question is open and is put to the owner in the "
            "FINDING."
        ),
        "dof_basis": (
            "n_entries 3, n_residual 1 — UNCHANGED from the keeper, because this lane "
            "added no free parameter and no ScenarioConfig field. "
            "gas_plant_monthly_fuel_pricing is a BOOLEAN SELECTOR over two "
            "aggregations of the SAME measured receipts, not a value: on, each gas "
            "unit pays its own plant-month contract print; off, every gas unit pays "
            "the realized Henry Hub level plus the footprint's own quantity-weighted "
            "delivered basis. Nothing is fitted, scaled, offset or swept, and there is "
            "no price residual in existence it could have been fitted to. "
            "REPORTED AGAINST THIS ENTRY, because it cuts against the lane: that basis "
            "constant (GAS_BASIS_DIFFERENTIAL['SOCO'] = 0.64) is the 2024 value applied "
            "to every year, against a measured +0.49 / +0.64 / +0.65, so 2023 carries "
            "+0.15 $/MMBtu — about +$1.65/MWh — on EVERY gas unit alike. It is a COMMON "
            "level shift, so it cannot move CT_PEAKER against ST_GAS, but it does move "
            "the gas block against coal, and the 2023 COAL_PRB +1.481 TWh this run "
            "delivers is partly that. Making the constant per-year is a rule 23 "
            "[R-FROZEN-DERIVE] re-derivation on SOURCE DATA and is ROUTED, not taken "
            "here — taking it after seeing this result would be selecting a parameter "
            "on the outcome. See ADDENDUM-soco54-the-fallback-basis-2026-09-20.md."
        ),
    }
    att["disclosures"] = _disclosures()
    _retag(att, sc)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
