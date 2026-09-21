"""SOCO-57: write ``calibration_attestation.json`` for the measured-CC-heat-rate arm.

Adapted from :mod:`scripts.gen_soco56_attestation`, which is the SOCO desk's
convention. What differs is the delta being attested and the disclosures.

THE DELTA. ``ScenarioConfig.measured_cc_heat_rates``, turned ON against the
incumbent keeper ``2026-09-20-soco56-perunit-outage``. It replaces the eGRID
plant-average (or prime-mover-family) ANNUAL heat rate on ``CC_REGULAR`` rows
with each plant's own CAMPD-metered steady-state operating rate, on the same
seam and the same identification as the CT / COAL / ST_GAS siblings already in
the keeper's recipe. With it, CC_REGULAR stops being the last thermal class in
the footprint still priced off an unmeasured annual average.

WHY, IN ONE SENTENCE: eGRID's level moves with the plant's capacity factor in
the vintage year, and for a combined cycle that has a sharp form — Charles R
Lowman (plant 56) carries EIA-860 ``Operating Year`` 2023 on BOTH its
generators, so eGRID's 2023 vintage is its COMMISSIONING-year average and the
model prices a new H-class machine at 8.105 MMBtu/MWh (42 % HHV) against a
meter reading 6.30 net, stable to ±0.03 across three years.

Every governance assertion is re-verified against the bundle's own
``run_config.json`` by :func:`_verify`, which RAISES rather than writing a false
assertion. The artifact identity is verified too, BY EXECUTION: the committed
CSV must carry exactly the population, the applied set and the two boundary
refusals the PRECOMMIT names, and the loader's applied map must agree with it —
or this attestation describes a derivation the LP never saw.

GATE G17. SOCO has no price benchmark and gains none, so the rule 1 [R-STRUCT]
authorized price-tuning channel is unreachable rather than merely unused. NO
``authorized_price_tuning`` KEY IS WRITTEN — ``calibration_verdict.py`` validates
that key's SHAPE when present and a declared-NONE dict would not validate. The
declared-NONE statement lives in ``attested_by`` prose, which is the SOCO
convention from SOCO-40 onward.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BUNDLE = Path("results/calibration/soco57_measured_cc_hr")

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: SOCO's keeper recipe (2026-09-20-soco56-perunit-outage), carried forward
#: unchanged. ``measured_cc_heat_rates`` is this lane's single delta and is
#: asserted separately, to True.
KEEPER_RECIPE = (
    "measured_ct_heat_rates",
    "egrid_family_heat_rates",
    "measured_st_heat_rates",
    "soco_gas_st_campaign_commitment",
    "measured_coal_heat_rates",
    "gas_basis_differential_measured_by_year",
    "coal_plant_monthly_pricing",
    "campd_per_unit_attribution",
)

#: SOCO-55's measured per-year gas basis, INHERITED. Asserted against the live
#: constant so this attestation cannot describe a table the run did not use.
MEASURED_BASIS = {2023: 0.49, 2024: 0.64, 2025: 0.65}

ARTIFACT = _ROOT / "data/raw/_processed-legacy/campd_cc_heat_rates_SOCO.csv"

#: The artifact's identity, as this attestation describes it. Verified by
#: execution in :func:`_verify_artifact`, which raises on any drift.
EXPECTED_PLANTS = 18
EXPECTED_APPLIED = 16
EXPECTED_APPLIED_MW = 17540.1
EXPECTED_TOTAL_MW = 18652.9

#: The ONLY plants the BOUNDARY GUARD refuses: CAMPD meters their combustion
#: turbines but not their unfired steam generators, so ``heatInput/grossLoad``
#: is the CT rate rather than the plant's combined-cycle rate.
EXPECTED_REFUSALS = {533: "steam_not_metered", 7946: "steam_not_metered"}


def _verify_artifact() -> dict:
    """Raise unless the committed artifact is the one this attestation describes.

    The attestation's factual claims are (a) that the measurement covers 94 % of
    the CC fleet, (b) that exactly two plants are refused and refused FOR THE
    BOUNDARY REASON, and (c) that what the LP actually applied is the artifact's
    ``flag == 'ok'`` set and nothing else. All three are checked here by
    execution, so a re-derivation with a different population, a different
    refusal set or a loader disagreement cannot pass silently.
    """
    import pandas as pd  # noqa: PLC0415

    if not ARTIFACT.exists():
        raise SystemExit(f"missing committed artifact: {ARTIFACT}")
    df = pd.read_csv(ARTIFACT)
    if len(df) != EXPECTED_PLANTS:
        raise SystemExit(
            f"artifact carries {len(df)} plants, expected {EXPECTED_PLANTS}"
        )
    ok = df[df["flag"] == "ok"]
    if len(ok) != EXPECTED_APPLIED:
        raise SystemExit(
            f"artifact applies {len(ok)} plants, expected {EXPECTED_APPLIED}"
        )
    refused = {
        int(r.plant_code): str(r.flag)
        for r in df[df["flag"] != "ok"].itertuples(index=False)
    }
    if refused != EXPECTED_REFUSALS:
        raise SystemExit(
            f"the boundary guard refuses {refused!r}, expected "
            f"{EXPECTED_REFUSALS!r} — this attestation describes a different "
            "derivation than the one committed"
        )
    applied_mw = round(float(ok["class_capacity_mw"].sum()), 1)
    total_mw = round(float(df["class_capacity_mw"].sum()), 1)
    if (applied_mw, total_mw) != (EXPECTED_APPLIED_MW, EXPECTED_TOTAL_MW):
        raise SystemExit(
            f"applied/total capacity is {applied_mw}/{total_mw} MW, expected "
            f"{EXPECTED_APPLIED_MW}/{EXPECTED_TOTAL_MW}"
        )

    # (c) the LOADER must agree with the artifact -- the seam the LP reads.
    from market_sim.data.fleet import measured_cc_heat_rates  # noqa: PLC0415

    measured_cc_heat_rates.cache_clear()
    live = measured_cc_heat_rates("SOCO")
    want = {int(r.plant_code): float(r.heat_rate) for r in ok.itertuples(index=False)}
    if live != want:
        raise SystemExit(
            "the loader's applied map disagrees with the committed artifact's "
            f"flag=='ok' rows: {sorted(set(live) ^ set(want))!r}"
        )

    return {
        "sha256_16": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()[:16],
        "plants_measured": int(len(df)),
        "plants_applied": int(len(ok)),
        "applied_mw": applied_mw,
        "total_mw": total_mw,
        "applied_pct": round(100.0 * applied_mw / total_mw, 1),
        "boundary_refusals": {
            int(r.plant_code): round(float(r.boundary_gross_over_net), 4)
            for r in df[df["flag"] != "ok"].itertuples(index=False)
        },
        "steady_hours": int(df["steady_hours"].sum()),
    }


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
    if not sc.get("measured_cc_heat_rates"):
        raise SystemExit(
            "measured_cc_heat_rates is OFF — this bundle is the CONTROL, not the "
            "SOCO-57 arm"
        )
    # Rule 19 [R-ONE-MECH]: the measured CC rate REPLACES whatever eGRID
    # construction reached the CC rows (the plant average, or the prime-mover
    # FAMILY rate where egrid_family_heat_rates covers the site) because it is
    # the later assignment to the same field -- exactly as the ST_GAS sibling
    # does. The two OTHER eGRID reconstructions are alternatives to that same
    # object and must stay off, or two constructions would compete for one row.
    for name in (
        "egrid_identity_heat_rates",
        "egrid_steam_collapse_heat_rates",
        "measured_chp_heat_rates",
    ):
        if sc.get(name):
            raise SystemExit(
                f"{name} is armed alongside measured_cc_heat_rates — that is a "
                "second heat-rate construction on the same rows (rule 19)"
            )
    if sc.get("coal_prb_proxy_own_iso"):
        raise SystemExit(
            "coal_prb_proxy_own_iso is armed — that is SOCO-53g's open candidate"
        )
    if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
        raise SystemExit(
            "resolved coal_prb_sigmoid_overrides is "
            f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null"
        )

    # --- SOCO-55's delta, INHERITED and carried forward unchanged
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
        raise SystemExit("the scalar GAS_BASIS_DIFFERENTIAL['SOCO'] moved")
    if set(GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR) != {"SOCO"}:
        raise SystemExit(
            "a non-SOCO row is present in GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR "
            "— rule 25 [R-ISO-SCOPE]"
        )
    # --- SOCO-54's delta, INHERITED
    if sc.get("gas_plant_monthly_fuel_pricing"):
        raise SystemExit(
            "gas_plant_monthly_fuel_pricing is ON — SOCO-54's keeper delta is not "
            "carried forward, so this is not a single-delta arm off the keeper"
        )
    for name in KEEPER_RECIPE:
        if not sc.get(name):
            raise SystemExit(
                f"{name} is not armed — the keeper's recipe is not carried"
            )


def _retag(att: dict, sc: dict, art: dict) -> None:
    """Re-tag the offer-curve DOF entries and carry SOCO-55's measured basis.

    ``build_dof_ledger.py`` tags ``offer_curve_by_group`` and
    ``offer_curve_smoothing`` ``residual`` by default, because on every other ISO
    they ARE the rule-1 price-tuning surface. On SOCO they cannot be: the identity
    1.0 on all four bands is not a tuned value, and there is no price residual in
    existence to have tuned it against. :func:`_verify` has already raised if any
    band is off the identity.

    THIS LANE ADDS NO FREE PARAMETER. ``measured_cc_heat_rates`` is a BOOLEAN GATE
    over a MEASUREMENT — every applied number is ``sum(heatInput)/sum(grossLoad)``
    over the plant's own steady hours — with no value, threshold, year scope or
    class scope to choose, so ``n_residual`` is unchanged at 1 (the inherited
    ``wefor_multiplier``).
    """
    fp = att.get("free_parameters")
    if not fp:
        raise SystemExit(
            "free_parameters absent — run "
            f"`PYTHONPATH=src python3 scripts/build_dof_ledger.py --iso SOCO {BUNDLE}` first"
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
                "machine-verified by gen_soco57_attestation._verify, which raises "
                f"otherwise: the distinct values per band are {bands}. "
                "offer_curve_overrides and offer_curve_deltas are null. The two "
                "non-identity keys, econ_low_share and pct_peaking, are NOT the "
                "authorized channel — rule 1's carve-out excludes structural shares "
                "— and arrive verbatim from the ISO-agnostic GENERIC_BASE_OFFER_CURVE."
            )
        elif entry["name"] == "offer_curve_smoothing":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "Unset on this run — both offer_curve_smoothing and curve_smoothing "
                "are null (machine-verified). Nothing was tuned because nothing was set."
            )

    have = {e["name"] for e in fp["entries"]}
    for year, value in sorted(MEASURED_BASIS.items()):
        name = f"GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'][{year}]"
        if name in have:
            continue
        fp["entries"].append(
            {
                "name": name,
                "value": value,
                "identification": "measured-physical",
                "basis": (
                    f"${value:+.2f}/MMBtu. INHERITED FROM SOCO-55, not re-derived "
                    "here. The quantity-weighted EIA-923 Schedule-2 delivered "
                    "natural-gas cost to the run's own EIA-860 SOCO gas fleet in THIS "
                    "year, minus the Henry Hub annual mean for THIS year. Sources, "
                    "both committed: data/raw/_processed-legacy/"
                    "eia923_monthly_fuel_costs.parquet and "
                    "data/raw/gas-prices/henry_hub_monthly.csv. Listed rather than "
                    "left to prose because rule 21 [R-DOF] asks for every free "
                    "parameter with its identification source; tagged "
                    "measured-physical, so n_residual is unchanged."
                ),
            }
        )

    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    fp["retag_note"] = (
        "SOCO-57 re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40..56 used and re-verified here by "
        "execution, and CARRIED FORWARD SOCO-55's three measured per-year gas-basis "
        "entries unchanged. "
        "THIS LANE ADDS NO ENTRY OF ITS OWN AND NO DEGREE OF FREEDOM. "
        "measured_cc_heat_rates is a BOOLEAN GATE over a MEASUREMENT: every applied "
        "number is sum(heatInput)/sum(grossLoad) over that plant's own steady-state "
        "CAMPD hours, converted to the net basis by the COMMITTED parasitic chain "
        "(per-plant map where one exists, else the CC_REGULAR class default 0.975). "
        "There is no value, threshold, year scope or class scope to choose. The two "
        "screens it does carry are DATA-INTEGRITY guards fixed on physics ex ante and "
        "never swept: the gross-basis band [5.0, 20.0] (5.0 implies > 68 % HHV, which "
        "no combined cycle reaches; 20.0 is 17 %, below any operating point a CC "
        "holds), and THE BOUNDARY GUARD [0.90, 1.25] on CAMPD CC gross over EIA-923 "
        "CC net, whose band sits inside an EMPTY measured gap — SOCO's two clusters "
        f"are {art['boundary_refusals']} against 1.014..1.116, so no value in "
        "[0.75, 1.00] would change the partition. "
        "It ships False and is already registered in _CACHE_KEY_OPTIONAL_FIELDS at "
        "'False', so no pre-existing cached run is re-keyed and no solve-surface row "
        "moves (moved_rows('SOCO') == {} machine-verified at HEAD). "
        f"The artifact (campd_cc_heat_rates_SOCO.csv, sha256[:16] {art['sha256_16']}) "
        f"measures {art['plants_measured']} plants and APPLIES {art['plants_applied']} "
        f"= {art['applied_mw']} of {art['total_mw']} MW ({art['applied_pct']} %) over "
        f"{art['steady_hours']:,} steady hours, verified by execution in "
        "_verify_artifact — which raises if the population, the refusal set or the "
        "loader's applied map differs from what this attestation describes. "
        "n_residual is UNCHANGED at 1 (the inherited wefor_multiplier), which is the "
        "figure rule 21 [R-DOF] gates on."
    )


def _disclosures(art: dict) -> dict:
    """SOCO-57 determination basis. The items that cut against the lane lead."""
    return {
        "note": (
            "SOCO-57 determination basis. Everything the run does not establish, at "
            "full magnitude. The first item is the worst thing that can be said about "
            "this lane — the arm moves the lane's OWN TARGET ROW the wrong way and "
            "cannot close it, which the PRECOMMIT quantified before the solve — and "
            "it leads for that reason. THE SECOND names a NEW FAILING CRITERION this lane introduced and did not predict."
        ),
        "1_THE_ARM_CANNOT_CLOSE_THE_TARGET_ROW_AND_MOVES_IT_THE_WRONG_WAY": (
            "THIS IS THE HEADLINE AND IT IS AGAINST THE LANE. SOCO-57 was chartered at "
            "the single failing C1 row, 2024 CC_REGULAR, which needs -2.712 TWh of "
            "volume and -0.88 pp of share to pass. Repricing three under-priced CC "
            "plants CHEAPER raises CC_REGULAR, so the arm moves that row FURTHER out "
            "of band rather than closing it. PRECOMMIT-soco-57 §4 states this in "
            "those words BEFORE the solve, with a +0.356 TWh point estimate from a "
            "zero-LP greedy re-stack, and §5 P1 pre-registers the row still failing "
            "BOTH legs. "
            "RULES 1 [R-STRUCT] AND 14 [R-ACCURATE] ARE THE GOVERNING TEXTS. Rule 14: "
            "'if swapping a hand estimate for real data makes the backcast worse, that "
            "is a signal that something else in the model is miscalibrated and the "
            "estimate was silently compensating for it. Treat the worse fit as a "
            "discovered bug: keep the accurate input.' Rule 1 forbids rejecting a "
            "structurally-correct mechanism because the residual moved the wrong way. "
            "A model that prices a 2023-vintage H-class combined cycle at a "
            "42 %-efficiency rate is not modelling that machine, whatever its class "
            "total reads."
        ),
        "2_IT_ADDS_A_NEW_FAILING_CRITERION_C4_AND_THE_LANE_DID_NOT_PREDICT_IT": (
            "THE SECOND THING AGAINST THIS LANE, AND IT IS A PREDICTION THIS LANE GOT "
            "WRONG. C4 fleet hourly dispatch correlation goes PASS -> FAIL on ONE row: "
            "2024 coal, NRMSE 0.296 -> 0.309 against a <= 0.30 gate, with r essentially "
            "unchanged (0.832 -> 0.829). grade_summary target_grade therefore drops 4 "
            "-> 3 and fails 1 -> 2. PRECOMMIT-soco-57 §5 P13 pre-registered 'C2 / C4 / "
            "C6 PASS' and IS FALSIFIED; P4 pre-registered 2024 COAL_PRB worsening by "
            "< 0.45 TWh and IS ALSO FALSIFIED (it moved -0.638). Both are reported as "
            "misses rather than re-read as successes. "
            "THE ROOT OF THE MISS IS NAMED: the lane's ex-ante thinnest-row analysis "
            "(the handoff's check D) enumerated only C1 rows, and named 2024 COAL_PRB "
            "and 2023 ST_GAS. THE ACTUAL THINNEST ROW ON THE WHOLE RUN WAS C4 2024 "
            "COAL, PASSING BY 0.004 OF NRMSE, and this lane never looked at it. A "
            "successor's check D must enumerate EVERY scored criterion's margin, not "
            "C1's. "
            "WHAT THE NUMBER IS AND IS NOT. It is one row of one criterion in one year, "
            "crossing a gate the control held by 0.004; the same criterion's coal rows "
            "IMPROVE in the other two years (2023 r 0.867 -> 0.882; 2025 NRMSE 0.170 -> "
            "0.167), so two of three years get better and one crosses a hairline. It is "
            "NOT dismissed on that basis: C4 fails, it is a supporting-tier criterion "
            "with no standing-rule relief (rule 22 [R-C3C] covers C3c only), and it "
            "costs a grade point. "
            "ITS MECHANISM IS UNDERSTOOD AND IT IS A REAL COST. Repricing three CC "
            "plants cheaper displaces coal -- 2024 COAL_PRB -0.638 TWh -- from a class "
            "that was ALREADY 5.143 TWh SHORT of its actual, so the arm takes energy "
            "from a short class and gives it to a long one, and perturbs coal's hourly "
            "shape doing it. Under rule 14 [R-ACCURATE] that is the DISCOVERED BUG "
            "signal, not a reason to revert: SOCO's coal is under-dispatched for a "
            "reason this lane has not found, and the CC heat-rate error was partially "
            "masking it. THE NAMED SUCCESSOR IS SOCO'S COAL UNDER-DISPATCH, not this "
            "input."
        ),
        "3_IT_REPAIRS_ONE_TAIL_AND_PROVABLY_LEAVES_THE_OTHER_ALONE": (
            "This is the lane's positive claim and its limit in one sentence. The "
            "correction is largest at exactly the three plants the model most "
            "UNDER-dispatches, in rank order — Lowman +1.801 MMBtu/MWh at a 2024 "
            "dispatch ratio of 0.602, Barry +0.770 at 0.729, Daniel +0.701 at 0.843 — "
            "while every other applied plant sits inside +/-0.24. It is ~zero at the "
            "plants the model already dispatches correctly (McDonough 0.966x, "
            "Chattahoochee 0.977x, Hog Bayou 0.949x) AND ~zero at the plants it "
            "OVER-dispatches: Tenaska Lindsay Hill, at 2.506x the single largest "
            "outlier in the class, measures -0.107 MMBtu/MWh, i.e. the model is "
            "$0.30/MWh CHEAP there — a rounding error. "
            "SO THE OVER TAIL IS UNEXPLAINED AND THIS LANE DOES NOT EXPLAIN IT. "
            "corr(delta heat rate, dispatch ratio) = -0.505 over the 16 applied "
            "plants. A lever that repaired both tails would be a curve fit; this one "
            "repairs one and is silent on the other, which is ROUTED, not closed."
        ),
        "4_TWO_PLANTS_ARE_REFUSED_AND_THE_MEASUREMENT_DOES_NOT_REACH_THEM": (
            "STATED AT THE GATE RATHER THAN LEFT TO BE DISCOVERED. At McWilliams (533) "
            "and Wansley U9 (7946) CAMPD meters the combustion turbines but NOT the "
            "unfired steam generator, so heatInput/grossLoad reads 10.78 and 10.94 "
            f"MMBtu/MWh — the CT rate, about 1.5x the true CC rate. The boundary guard "
            f"refuses them on the measured evidence ({art['boundary_refusals']} against "
            "1.014..1.116 at the other sixteen), so they keep their eGRID rate and the "
            "measurement reaches 94.0 % of CC capacity rather than 100 %. "
            "WHAT THAT COSTS: those two plants' true operating heat rates are UNKNOWN "
            "to this model and no claim is made about them. They are not repaired; "
            "they are merely not corrupted."
        ),
        "5_THE_SPREAD_TEST_AS_POSED_FAILED_AND_THE_LANE_SAYS_SO": (
            "The handoff routed this lane on the hypothesis that the model's CC "
            "heat-rate SPREAD would be flatter than the measured spread. IT IS NOT: "
            "model 1.381 against measured 1.403 MMBtu/MWh, essentially identical, and "
            "the capacity-weighted LEVEL barely moves (7.217 -> 7.040). The lane is "
            "not built on that hypothesis. What phase 0 found instead is that the "
            "error is CONCENTRATED — three plants carry it and thirteen do not — and "
            "that where it sits is what makes it a mechanism. Recorded because a "
            "successor reading the handoff would otherwise expect the spread result."
        ),
        "6_SOCO_HAS_NO_PRICE_BENCHMARK_AND_GAINS_NONE": (
            "GATE G17 stands absolutely. data/raw/_validation-source/actual_lmp.json "
            "carries NO SOCO block and MUST NOT GAIN ONE. C3a mean LMP, C3b price "
            "duration/shape and C3c price tail are UNSCORABLE — not failed — in every "
            "year, so this determination is scored on C1 / C2 / C4 / C6 / C8 ONLY and "
            "certifies NO price level, shape or tail. The model's own load-weighted "
            "mean LMP is MODEL-ONLY and UNVERIFIED and is never quoted as price skill. "
            "No neighbouring hub, no proxy, no cost-stack price, ever. "
            "Because there is no price residual in existence, the rule 1 [R-STRUCT] "
            "authorized price-tuning channel is UNREACHABLE here rather than merely "
            "unused: every offer_curve_by_group band is exactly 1.0, and "
            "authorized_price_tuning is DECLARED NONE."
        ),
        "7_NO_YEAR_IN_THIS_RUN_IS_AN_OUT_OF_SAMPLE_SKILL_CLAIM": (
            "Rule 22 [R-C3C]'s coda: [R-HOLDOUT] was removed 2026-09-09, so no year is "
            "protected from being iterated against and there is no certified "
            "out-of-sample number anywhere in this program. 2023-2025 are model-"
            "SELECTION evidence. Nothing here is quoted as forecast skill."
        ),
        "8_A_WIRING_DEFECT_WAS_FOUND_IN_LANE_AND_A_SUCCESSOR_MUST_KNOW_IT": (
            "scripts/run_calibration.py's fleet_to_bins call site passed the other "
            "three measured-heat-rate flags but not the new one, so this lane's FIRST "
            "rule-19 run read all four grains at EXACTLY zero — an arm that looked "
            "perfectly inert while simply never arming. It was caught by toggling a "
            "KNOWN-armed flag (measured_coal_heat_rates) through the same channel, "
            "which moved 24 rows and proved the channel sound. A FIFTH SIBLING MUST "
            "PATCH FOUR CALL SITES, NOT THREE. Recorded because 'max|delta| == 0' is "
            "indistinguishable from 'inert' unless something asserts the RESOLVED "
            "value, which is why soco57_compose_span.assert_delta reads "
            "scenario_config rather than the prb_overrides bag."
        ),
    }


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-57 bundle."""
    att_path = BUNDLE / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    _verify(sc)
    art = _verify_artifact()
    print(f"artifact verification: {art}")

    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-57 (lane). ONE mechanism moves against the incumbent keeper "
            "2026-09-20-soco56-perunit-outage: ScenarioConfig.measured_cc_heat_rates, "
            "turned ON. Everything else is that keeper's recipe unchanged, "
            "machine-verified by _verify — including SOCO-54's "
            "gas_plant_monthly_fuel_pricing=False, SOCO-55's "
            "gas_basis_differential_measured_by_year=True and SOCO-56's "
            "campd_per_unit_attribution=True, without which this is not a "
            "single-delta arm off that keeper. "
            "THE CLAIM IS ABOUT A MEASURED MACHINE CHARACTERISTIC, NOT ABOUT THE "
            "RESIDUAL. The fleet loader gives every combined-cycle generator eGRID's "
            "plant rate PLHTIAN/PLNGENAN — or, at a multi-family site, the eGRID "
            "prime-mover-FAMILY rate — an ANNUAL average that folds startup fuel, "
            "shutdown tails and the offline hours' fuel into the number that sets the "
            "plant's offer, and whose LEVEL moves with the plant's capacity factor in "
            "the vintage year. CC_REGULAR was the LAST thermal class in this footprint "
            "still priced that way: CT, ST_GAS and COAL took their own CAMPD meters at "
            "SOCO-53, SOCO-53e and SOCO-53f. "
            "THE TRACED CASE. For a combined cycle the vintage-year defect has a sharp "
            "form — a unit COMMISSIONED in the vintage year is published at its "
            "commissioning-year average, carrying first-fire, tuning and "
            "acceptance-test fuel against a part-year denominator. Charles R Lowman "
            "(plant 56) carries EIA-860 Operating Year 2023 on BOTH generators (LEC1, "
            "CT, 459.0 MW; LEC2, CA, 273.7 MW), so eGRID's 2023 vintage prices it at "
            "8.105 MMBtu/MWh — 42 % HHV, an F-class number — while its own meter reads "
            "6.35 / 6.30 / 6.29 net across 2023 / 2024 / 2025, stable to +/-0.03, which "
            "is ~54 % and what a new H-class machine does. That is a $5.10/MWh error on "
            "a new machine, and it is why the model runs it at 0.620 of its own "
            "availability against a measured capacity factor of 0.763. "
            "THE STRUCTURAL SIGNATURE, WHICH IS WHY THIS IS A MECHANISM AND NOT A FIT. "
            "The correction is largest at the three plants the model most "
            "under-dispatches, IN RANK ORDER (Lowman +1.801 at ratio 0.602, Barry "
            "+0.770 at 0.729, Daniel +0.701 at 0.843); it is ~zero at the plants the "
            "model already dispatches correctly; and it is ~zero at the plants it "
            "OVER-dispatches, including Tenaska Lindsay Hill, the class's single "
            "largest outlier at 2.506x, where the model is $0.30/MWh CHEAP against its "
            "own meter. A lever that repaired both tails would be a curve fit. "
            "THE BOUNDARY GUARD, this deriver's own addition and the reason the "
            "measurement can be trusted at all. heatInput/grossLoad is a plant's "
            "COMBINED-CYCLE rate only if CAMPD's gross load includes the steam "
            "turbine; at some sites the combustion turbines report and the unfired "
            "steam generator does not, so the ratio is the COMBUSTION-TURBINE rate, "
            "about 1.5x too high. The guard is an identity test against an independent "
            "source — pooled CAMPD CC gross over the SAME year's EIA-923 CC net, read "
            "through the benchmark's own _eia923_frame, so the comparator is exactly "
            "the series the run is scored against — and it refuses McWilliams (0.719) "
            "and Wansley U9 (0.675) against sixteen plants reading 1.014..1.116. Two "
            "clusters separated by a factor of 1.4 with NOTHING between 0.72 and 1.01, "
            "so the band [0.90, 1.25] sits inside an empty gap and no value in "
            "[0.75, 1.00] would change the partition: it is fixed on physics ex ante "
            "and is not a swept parameter. "
            "RULE 25 [R-ISO-SCOPE] / 28(d): NO VERDICT TRANSFERS. SOCO entered this "
            "cell as U (untested) — the mechanism is NEW in this PR — and its artifact "
            "was derived in this lane from SOCO's OWN CAMPD and EIA-860: "
            "`scripts/data/derive_campd_cc_heat_rates.py --iso SOCO "
            "--egrid-family-heat-rates --measured-ct-heat-rates "
            "--measured-st-heat-rates --measured-coal-heat-rates --detail`. Every "
            "peer ISO's cell is seeded U with nothing transferred, and the field is a "
            "STRICT NO-OP for any ISO without its own artifact. "
            "RULE 13 [R-MEASURED]: a machine's operating heat rate is a physical "
            "characteristic that regenerates for a forward year from the same pipeline "
            "and responds to changed conditions (a retrofit moves it; a repowered unit "
            "re-meters), so it is admissible as an INPUT, not a measured outcome fed "
            "back to close a residual. No actual is pinned: the rate is a COST, and "
            "the LP chooses its dispatch against it. "
            "RULE 19 [R-ONE-MECH]: the branch is gated on group == 'CC_REGULAR', "
            "disjoint by construction from the CT / COAL / ST_GAS branches because a "
            "row resolves to exactly one group, and it REPLACES the eGRID construction "
            "on the rows it covers rather than stacking, being the later assignment to "
            "the same field — exactly as the ST_GAS sibling does. CC_CHP is out of "
            "scope by design: no unfired-plant meter can speak for a cogenerator's "
            "host-steam boundary. egrid_identity_heat_rates, "
            "egrid_steam_collapse_heat_rates and measured_chp_heat_rates are asserted "
            "OFF so no second construction competes for the same rows. "
            "Machine-verified at FOUR grains on a fleet_only rebuild BEFORE the solve, "
            "in all three years: fuel_prices, pmax and availability at global max "
            "|delta| EXACTLY 0.000000000000 with ZERO rows moved, while mc_base and "
            "heat_rate move 59 rows — ALL CC_REGULAR, at exactly the 16 applied "
            "plants, with the two boundary-refused plants absent on every grain. "
            "RULE 21 [R-DOF] / 24 [R-REGISTRY]: ZERO free parameters added. Every "
            "applied number is sum(heatInput)/sum(grossLoad) over the plant's own "
            "steady hours; the two screens are data-integrity guards fixed on physics "
            "ex ante. It is registered in _CACHE_KEY_OPTIONAL_FIELDS at 'False' so no "
            "pre-existing cache key moves, explicit-False reproduces the default key, "
            "and moved_rows('SOCO') == {} is machine-verified at HEAD. n_residual is "
            "unchanged at 1. "
            "GATE G17 — SOCO HAS NO PRICE BENCHMARK AND GAINS NONE. Every "
            "offer_curve_by_group band is exactly 1.0 on all 13 groups, "
            "offer_curve_overrides / offer_curve_deltas / smoothing are null, and "
            "AUTHORIZED PRICE TUNING IS DECLARED NONE — no authorized_price_tuning key "
            "is written, because with no price benchmark in existence the rule 1 "
            "[R-STRUCT] channel is unreachable rather than merely unused. "
            "WHAT THIS LANE DOES NOT CLAIM, stated because it cuts against it: the arm "
            "moves the lane's own target row (2024 CC_REGULAR) the WRONG WAY and "
            "CANNOT close it, exactly as PRECOMMIT-soco-57 §4 stated before the solve; "
            "the handoff's spread hypothesis FAILED as posed (model 1.381 vs measured "
            "1.403); the over-dispatched tail, including the class's largest outlier, "
            "is left unexplained and ROUTED; and two plants are refused by the "
            "boundary guard, so their true operating rates remain unknown to this "
            "model."
        ),
    }
    att["disclosures"] = _disclosures(art)
    _retag(att, sc, art)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
