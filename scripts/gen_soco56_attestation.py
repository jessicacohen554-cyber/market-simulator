"""SOCO-56: write ``calibration_attestation.json`` for the per-unit-outage arm.

Adapted from :mod:`scripts.gen_soco55_attestation`, which is the SOCO desk's
convention. What differs is the delta being attested and the disclosures.

THE DELTA. ``ScenarioConfig.campd_per_unit_attribution``, turned ON against the
incumbent keeper ``2026-09-20-soco55-peryear-gas-basis``. It selects the
``-perunit-`` companion unit-outage extract, in which every CAMPD unit routes by
the shared ``scripts/lib/campd_measured_classes`` crosswalk instead of the
deriver's plant-level ``fac_group`` short-circuit.

WHY, IN ONE SENTENCE: the incumbent extract routes Barry (plant 3) units 1, 2
and 4 — which CAMPD files as ``Tangentially-fired`` BOILERS, never ``Combined
cycle`` — to ``CC_REGULAR``, so their idleness is charged as a forced outage on
Barry's combined-cycle block and the model is physically forbidden from
reproducing that plant's measured output in 8,548 of 8,760 hours of 2024.

Every governance assertion is re-verified against the bundle's own
``run_config.json`` by :func:`_verify`, which RAISES rather than writing a false
assertion. The artifact identity is verified too: the committed ``-perunit-``
extract must differ from the incumbent in EXACTLY the three Barry unit rows the
PRECOMMIT names, or this attestation describes a derivation the LP never saw.

GATE G17. SOCO has no price benchmark and gains none, so the rule 1 [R-STRUCT]
authorized price-tuning channel is unreachable rather than merely unused. NO
``authorized_price_tuning`` KEY IS WRITTEN — ``calibration_verdict.py`` validates
that key's SHAPE when present and a declared-NONE dict would not validate. The
declared-NONE statement lives in ``attested_by`` prose, which is the SOCO
convention from SOCO-40 onward.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BUNDLE = Path("results/calibration/soco56_perunit_outage")

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: SOCO's keeper recipe (2026-09-20-soco55-peryear-gas-basis), carried forward
#: unchanged. ``campd_per_unit_attribution`` is this lane's single delta and is
#: asserted separately, to True.
KEEPER_RECIPE = (
    "measured_ct_heat_rates",
    "egrid_family_heat_rates",
    "measured_st_heat_rates",
    "soco_gas_st_campaign_commitment",
    "measured_coal_heat_rates",
    "gas_basis_differential_measured_by_year",
    "coal_plant_monthly_pricing",
)

#: SOCO-55's measured per-year gas basis, INHERITED here. Asserted against the
#: live constant so this attestation cannot describe a table the run did not use.
MEASURED_BASIS = {2023: 0.49, 2024: 0.64, 2025: 0.65}

#: The ONLY unit rows whose routing the ``-perunit-`` companion changes, verified
#: by execution against both committed extracts. ``facility_id`` 3 is Barry.
EXPECTED_ROUTING_MOVES = {
    ("3", "1"): ("CC_REGULAR", "ST_GAS"),
    ("3", "2"): ("CC_REGULAR", "ST_GAS"),
    ("3", "4"): ("CC_REGULAR", "ST_GAS"),
}

INCUMBENT_EXTRACT = _ROOT / "data/raw/campd-unit-outages-SOCO.csv"
PERUNIT_EXTRACT = _ROOT / "data/raw/campd-unit-outages-perunit-SOCO.csv"


def _verify_extracts() -> dict:
    """Raise unless the committed extracts differ in EXACTLY the Barry rows.

    The attestation's whole factual claim is that this is a surgical unit->class
    re-attribution at one facility. That claim is checked here by execution, not
    asserted, so a re-derivation with a wider blast radius cannot pass silently.
    """
    import pandas as pd  # noqa: PLC0415

    for p in (INCUMBENT_EXTRACT, PERUNIT_EXTRACT):
        if not p.exists():
            raise SystemExit(f"missing committed extract: {p}")
    a = pd.read_csv(INCUMBENT_EXTRACT)
    b = pd.read_csv(PERUNIT_EXTRACT)
    if len(a) != len(b):
        raise SystemExit(
            f"extract row counts differ ({len(a)} vs {len(b)}) — the -perunit- "
            "companion must RE-ROUTE rows, never add or drop them"
        )
    key = ["facility_id", "unit_id"]
    am = a.drop_duplicates(key).set_index(key)["plant_group"]
    bm = b.drop_duplicates(key).set_index(key)["plant_group"]
    moved = {
        (str(k[0]), str(k[1])): (str(am[k]), str(bm[k]))
        for k in am.index
        if k in bm.index and am[k] != bm[k]
    }
    if moved != EXPECTED_ROUTING_MOVES:
        raise SystemExit(
            f"the -perunit- companion re-routes {moved!r}, expected "
            f"{EXPECTED_ROUTING_MOVES!r} — this attestation describes a different "
            "derivation than the one committed"
        )
    # Count WINDOW rows, not merge pairs: a unit carries several windows per
    # year and a naive merge on (facility_id, unit_id) is a cross product.
    moved_keys = {(str(f), str(u)) for f, u in moved}
    n_rows_moved = int(
        sum(
            1
            for f, u in zip(b["facility_id"], b["unit_id"])
            if (str(f), str(u)) in moved_keys
        )
    )
    return {
        "extract_rows": int(len(a)),
        "unit_rows_rerouted": len(moved),
        "window_rows_rerouted": n_rows_moved,
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
    if not sc.get("campd_per_unit_attribution"):
        raise SystemExit(
            "campd_per_unit_attribution is OFF — this bundle is the CONTROL, not "
            "the SOCO-56 arm"
        )
    # Rule 19 [R-ONE-MECH]: the per-unit crosswalk REPLACES the fac_group
    # short-circuit. The narrower -unitroute- companion repairs a strict subset
    # of the same object; arming both would be two mechanisms on one seam.
    if sc.get("unit_outage_mixed_gas_routing"):
        raise SystemExit(
            "unit_outage_mixed_gas_routing is ON alongside campd_per_unit_"
            "attribution — that is two mechanisms on ONE seam (rule 19)"
        )
    # The five sibling extract-consistency repairs are NOT this lane's object and
    # must stay off, or the arm is not the single re-attribution it claims to be.
    for name in (
        "campd_outage_merit_order_guard",
        "unit_outage_per_unit_clip",
        "unit_outage_extract_basis_share",
        "unit_outage_st_capacity_basis",
        "unit_outage_window_hour_grain",
        "unit_outage_short_windows",
        "unit_outage_short_windows_gas",
        "unit_outage_fleet_status_scope",
        "unit_outage_lp_capacity_basis",
        "unit_outage_maxgen_events",
        "unit_partial_outage_windows",
        "historic_outage_overlay",
        "miso_native_outage_source",
        "caiso_dam_outages",
    ):
        if sc.get(name):
            raise SystemExit(f"{name} is armed — not this lane's recipe")

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
    if sc.get("gas_plant_monthly_fuel_pricing"):
        raise SystemExit(
            "gas_plant_monthly_fuel_pricing is ON — SOCO-54's keeper delta is not "
            "carried forward, so this is not a single-delta arm off the keeper"
        )
    if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
        raise SystemExit(
            "resolved coal_prb_sigmoid_overrides is "
            f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null"
        )
    if sc.get("coal_prb_proxy_own_iso"):
        raise SystemExit(
            "coal_prb_proxy_own_iso is armed — that is SOCO-53g's open candidate"
        )
    for name in KEEPER_RECIPE:
        if not sc.get(name):
            raise SystemExit(
                f"{name} is not armed — the keeper's recipe is not carried"
            )


def _retag(att: dict, sc: dict, extracts: dict) -> None:
    """Re-tag the offer-curve DOF entries and carry SOCO-55's measured basis.

    ``build_dof_ledger.py`` tags ``offer_curve_by_group`` and
    ``offer_curve_smoothing`` ``residual`` by default, because on every other ISO
    they ARE the rule-1 price-tuning surface. On SOCO they cannot be: the identity
    1.0 on all four bands is not a tuned value, and there is no price residual in
    existence to have tuned it against. :func:`_verify` has already raised if any
    band is off the identity.

    THIS LANE ADDS NO FREE PARAMETER. ``campd_per_unit_attribution`` is a BOOLEAN
    GATE over two ROUTINGS of the same measured CAMPD windows, with no value,
    threshold, year scope or class scope to choose, so ``n_residual`` is unchanged
    at 1 (the inherited ``wefor_multiplier``).
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
                "machine-verified by gen_soco56_attestation._verify, which raises "
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
        "SOCO-56 re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40..55 used and re-verified here by "
        "execution, and CARRIED FORWARD SOCO-55's three measured per-year gas-basis "
        "entries unchanged. "
        "THIS LANE ADDS NO ENTRY OF ITS OWN AND NO DEGREE OF FREEDOM. "
        "campd_per_unit_attribution is a BOOLEAN GATE over two ROUTINGS of the same "
        "measured CAMPD outage windows — the deriver's plant-level fac_group "
        "short-circuit, or the per-unit campd_measured_classes crosswalk — with no "
        "value, threshold, year scope or class scope to choose. It ships False and is "
        "already registered in _CACHE_KEY_OPTIONAL_FIELDS at 'False', so no "
        "pre-existing cached run is re-keyed and no solve-surface row moves "
        "(moved_rows('SOCO') == {} machine-verified at HEAD). "
        f"The companion extract re-routes {extracts['unit_rows_rerouted']} unit rows "
        f"({extracts['window_rows_rerouted']} window rows) of "
        f"{extracts['extract_rows']}, all at facility 3 (Barry), verified by "
        "execution in _verify_extracts — which raises if the blast radius is any "
        "wider than the three rows the PRECOMMIT names. "
        "n_residual is UNCHANGED at 1 (the inherited wefor_multiplier), which is the "
        "figure rule 21 [R-DOF] gates on."
    )


def _disclosures(extracts: dict) -> dict:
    """SOCO-56 determination basis. The items that cut against the lane lead."""
    return {
        "note": (
            "SOCO-56 determination basis. Everything the run does not establish, at "
            "full magnitude. The first item is the worst thing that can be said about "
            "this lane — the arm makes the lane's OWN TARGET ROW worse, which the "
            "PRECOMMIT predicted before the solve — and it leads for that reason."
        ),
        "1_THE_ARM_MAKES_THE_LANES_OWN_TARGET_ROW_WORSE_AND_IS_TAKEN_ANYWAY": (
            "THIS IS THE HEADLINE AND IT IS AGAINST THE LANE. SOCO-56 was chartered at "
            "the single failing C1 row, 2024 CC_REGULAR at +7.505 TWh of a +/-7.47 TWh "
            "band. Repairing Barry's availability RAISES CC_REGULAR, so the arm pushes "
            "that row FURTHER out of band rather than closing it. "
            "PRECOMMIT-soco-56 §4 P1 pre-registered this verbatim, with a point "
            "estimate of +2.9 TWh and a +1.5 to +4.5 band, from a zero-LP greedy "
            "re-stack run BEFORE the solve — and P2 pre-registered that the row would "
            "begin failing the SHARE leg as well as the volume leg. "
            "RULES 1 [R-STRUCT] AND 14 [R-ACCURATE] ARE THE GOVERNING TEXTS. Rule 14: "
            "'if swapping a hand estimate for real data makes the backcast worse, that "
            "is a signal that something else in the model is miscalibrated and the "
            "estimate was silently compensating for it. Treat the worse fit as a "
            "discovered bug: keep the accurate input, find and fix the real root "
            "cause.' Rule 1 forbids rejecting a structurally-correct mechanism because "
            "the residual moved the wrong way. A model that is PHYSICALLY FORBIDDEN "
            "from reproducing a 1.8 GW plant's measured output in 97.6 % of the hours "
            "of a year is not modelling that plant, whatever its class total reads."
        ),
        "2_WHAT_THE_SPURIOUS_OUTAGE_WAS_COMPENSATING_FOR": (
            "Barry's spurious derate was HIDING a real merchant-CC over-dispatch, and "
            "removing it exposes that at full size. Measured on the control, 2024, "
            "model vs the bench's own CAMPD series: the CC fleet's per-plant ratio "
            "spans 0.49x (3 Barry) to 2.45x (55271 Tenaska Lindsay Hill), and the "
            "plants above 1.35x — Tenaska Lindsay Hill 2.45, McWilliams 1.57, Wansley "
            "9 1.52, Central Alabama 1.42, Ratcliffe 1.41, E B Harris 1.38 — all run "
            "at 0.97-1.00 of their model availability while their measured capacity "
            "factors are 0.22-0.59. "
            "THE OWNERSHIP READING IS TESTED AND DOES NOT HOLD, and that is stated "
            "here because it corrects an inference a successor would otherwise draw "
            "from SOCO-55 §5. Aggregated on EIA-860 Utility Name, the 2024 CC tilt is "
            "mild and the CT tilt runs the OTHER way: Southern-affiliated CC 79.602 vs "
            "80.851 TWh actual (0.985x), non-Southern CC 32.814 vs 29.397 (1.116x); "
            "but Southern-affiliated CT_PEAKER is 2.219x against non-Southern 1.705x. "
            "So the CC misallocation is a PER-PLANT question, not an ownership one, "
            "and the successor's object is per-plant CC allocation — heat rate, offer "
            "surface, availability — rather than a merchant/utility partition."
        ),
        "3_THE_ARM_INTRODUCES_A_NEW_OVER_DERATE_ON_BARRYS_ST_GAS_BIN": (
            "STATED AT THE GATE RATHER THAN LEFT TO BE DISCOVERED. The three re-routed "
            "units total 709.9 MW and land on Barry's ST_GAS bin, whose EIA-860 "
            "nameplate basis (306.2 MW) is smaller, so the removed share clips and "
            "that bin's availability falls to ~0.02 mean. Its cost is BOUNDED BY "
            "MEASUREMENT rather than argued: Barry ST_GAS carries 2.349 / 0.000 / "
            "7.149 GWh of model energy in 2023 / 2024 / 2025 and is in merit in 18 / 3 "
            "/ 88 hours of 8,760, so the loss is at most 0.0023 / 0.0000 / 0.0071 TWh "
            "— under 0.18 % of the ST_GAS class in the worst year. Rule 17: plant 3's "
            "campaign-floor share is 0.000 with a 0.0632 margin in all three years, so "
            "no forced energy is at stake either. "
            "THE CORRECT REPAIR IS A SIBLING GATE — unit_outage_extract_basis_share "
            "(nyiso-196) or unit_outage_st_capacity_basis — and arming either here "
            "would be a SECOND mechanism on the same object. ROUTED, NOT STACKED "
            "(rule 19 [R-ONE-MECH])."
        ),
        "4_WHAT_THE_ARM_DOES_NOT_REPAIR": (
            "2023 is deliberately NOT brought to its actual. Barry unit 8's 345-day "
            "2023 commissioning outage is a GENUINE combined-cycle outage and the "
            "per-unit crosswalk correctly leaves it in the CC_REGULAR bin, so the "
            "repaired 2023 availability (4.471 TWh) stays far below the 7.303 TWh "
            "measured. That asymmetry is the mechanism's signature: 2024 and 2025 land "
            "on their measured output to within 0.07 % and 0.30 %, and 2023 does not. "
            "A mechanism that repaired all three to their actuals would be a fit. "
            "It also does not touch the model's FLEET-side treatment of Barry unit 4, "
            "which EIA-860 still files as Conventional Steam Coal (Energy Source BIT) "
            "while CAMPD measures it burning Pipeline Natural Gas (152.02 GWh, 2024). "
            "The outage overlay now routes it correctly; the fleet row does not. "
            "ROUTED, not taken."
        ),
        "5_SOCO_HAS_NO_PRICE_BENCHMARK_AND_GAINS_NONE": (
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
        "6_NO_YEAR_IN_THIS_RUN_IS_AN_OUT_OF_SAMPLE_SKILL_CLAIM": (
            "Rule 22 [R-C3C]'s coda: [R-HOLDOUT] was removed 2026-09-09, so no year is "
            "protected from being iterated against and there is no certified "
            "out-of-sample number anywhere in this program. 2023-2025 are model-"
            "SELECTION evidence. Nothing here is quoted as forecast skill."
        ),
    }


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-56 bundle."""
    att_path = BUNDLE / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    _verify(sc)
    extracts = _verify_extracts()
    print(f"extract verification: {extracts}")

    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-56 (lane). ONE mechanism moves against the incumbent keeper "
            "2026-09-20-soco55-peryear-gas-basis: ScenarioConfig."
            "campd_per_unit_attribution, turned ON. Everything else is that keeper's "
            "recipe unchanged, machine-verified by _verify — including SOCO-54's "
            "gas_plant_monthly_fuel_pricing=False and SOCO-55's "
            "gas_basis_differential_measured_by_year=True, without which this is not a "
            "single-delta arm off that keeper. "
            "THE CLAIM IS ABOUT A UNIT->CLASS ATTRIBUTION, NOT ABOUT THE RESIDUAL. "
            "data/raw/campd-unit-outages-SOCO.csv routes Barry (plant 3) units 1, 2 "
            "and 4 to plant_group CC_REGULAR. CAMPD files all three as unitType "
            "'Tangentially-fired' — BOILERS, never 'Combined cycle' — and EIA-860 "
            "files units 1 and 2 as Natural Gas Steam Turbine (prime mover ST) and "
            "unit 4 as Conventional Steam Coal (ST). They are mostly idle (17.01 / "
            "10.08 / 152.02 GWh in 519 / 303 / 1,539 hours of 2024) and the deriver's "
            "plant-level fac_group short-circuit charges that idleness as a forced "
            "outage on Barry's COMBINED-CYCLE block: 4.4 + 4.4 + 11.5 = 20.3 "
            "percentage points of derate for 342 / 353 / 298 days of 366. "
            "THE CONSEQUENCE IS PHYSICAL, NOT STATISTICAL. Barry's model availability "
            "ceiling sits BELOW the plant's own measured CAMPD output in 8,548 of "
            "8,760 hours of 2024, by up to 1,513 MW and 5.080 TWh (2023: 5.031, 2025: "
            "4.598). Its availability p50 is 1,028 MW against a measured output p50 of "
            "1,624 MW; it reaches full capacity in 144 hours where every peer CC "
            "reaches it in 1,800-2,160. "
            "IT IS THE SAME DEFECT TWO OTHER LANES HAVE ALREADY ADJUDICATED: pjm-75 "
            "(Chesterfield 3797 — 1,036 MW of retiring coal tagged CC_REGULAR, ~2.35 "
            "TWh of CC under-run) and miso-200 (Ninemile Point 1403 — two gas-steam "
            "boilers dumped on a 649.5 MW CC bin). The deriver's own docstring names "
            "the short-circuit as the cause in both. "
            "RULE 25 [R-ISO-SCOPE] / 28(d): NO VERDICT TRANSFERS. SOCO entered this "
            "cell as U (untested) and its artifact was derived in this lane from "
            "SOCO's OWN CAMPD extracts and EIA-860 vintage — "
            "`scripts/data/derive_campd_unit_outages.py --iso SOCO --years 2023 2024 "
            "2025 --per-unit-crosswalk` — never carried from NYISO, where the gate was "
            "built. "
            "RULE 13 [R-MEASURED]: the windows are a physical availability event "
            "derived from measured unit output, and the crosswalk is a unit->class "
            "map. Both regenerate for a forward year from the same deriver and the "
            "then-current EIA-860, and neither reads a model output. No actual is "
            "pinned: the repaired availability is a CEILING, not a target, and the LP "
            "chooses its dispatch under it. "
            "RULE 19 [R-ONE-MECH]: the crosswalk REPLACES the fac_group short-circuit "
            "rather than adjusting it, and the narrower -unitroute- companion "
            "(unit_outage_mixed_gas_routing) is asserted OFF so the two routings can "
            "never stack. Machine-verified at THREE grains on a fleet_only rebuild "
            "before the solve: fuel_prices and mc_base at global max |delta| EXACTLY "
            "0.000000000000 in all three years, and availability moving exactly 2 of "
            "128 (plant, group) keys — both at plant 3 — in every year. "
            "RULE 21 [R-DOF] / 24 [R-REGISTRY]: ZERO free parameters added. The gate "
            "is a boolean over two routings of the same measured windows, with no "
            "value, threshold, year scope or class scope to choose; it is already "
            "registered in _CACHE_KEY_OPTIONAL_FIELDS at 'False' so no pre-existing "
            "cache key moves, and moved_rows('SOCO') == {} is machine-verified at "
            "HEAD. n_residual is unchanged at 1. "
            "GATE G17 — SOCO HAS NO PRICE BENCHMARK AND GAINS NONE. Every "
            "offer_curve_by_group band is exactly 1.0 on all 13 groups, "
            "offer_curve_overrides / offer_curve_deltas / smoothing are null, and "
            "AUTHORIZED PRICE TUNING IS DECLARED NONE — no authorized_price_tuning key "
            "is written, because with no price benchmark in existence the rule 1 "
            "[R-STRUCT] channel is unreachable rather than merely unused. "
            "WHAT THIS LANE DOES NOT CLAIM, stated because it cuts against it: the arm "
            "makes the lane's own target row (2024 CC_REGULAR) WORSE, exactly as "
            "PRECOMMIT-soco-56 §4 P1 predicted; it introduces a new, measurably "
            "bounded over-derate on Barry's ST_GAS bin (<= 0.0071 TWh in the worst "
            "year) whose correct repair is a sibling gate and is ROUTED, not stacked; "
            "and it leaves the model's FLEET-side treatment of Barry unit 4 untouched."
        ),
    }
    att["disclosures"] = _disclosures(extracts)
    _retag(att, sc, extracts)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
