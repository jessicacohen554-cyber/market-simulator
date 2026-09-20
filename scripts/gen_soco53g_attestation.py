"""Write the SOCO-53g calibration attestation (schema ``calibration-attestation/v1``).

Lane SOCO-53g armed exactly ONE mechanism — ``coal_prb_proxy_own_iso``, which
pools the PRB delivered-cost proxy over SOCO's OWN EIA-923 reporters instead of
the hand-curated, Texas-only ``COAL_PLANT_SUPPLY`` — as a rule 25
``[R-ISO-SCOPE]`` / rule 14 ``[R-ACCURATE]`` input repair. The mechanism predates
this lane (nwpp-41, 2026-09-17). This lane wrote NO ``ScenarioConfig`` field and
added NO free parameter.

**What is unusual about this attestation, and it is stated rather than buried:
the mechanism is INERT on two of the three years.** The parent measured, at zero
LP and before the solve, that ``mc_base`` moves ZERO rows in 2023 and 2024 at
max |delta| exactly 0.000000000000, because ``apply_plant_monthly_fuel_prices``
overwrites the proxy on every SOCO PRB row with each plant's own filed monthly
delivered cost. The whole live footprint is 744 hours of ONE plant in 2025.
See ``PRECOMMIT-soco-53g-2026-09-20.md`` §4 and the disclosures below.

The four governance assertions are asserted by the LANE. Every one is a factual
claim about this bundle and each is machine-verified against its own
``run_config.json`` by :func:`_verify`, which raises rather than writing a false
assertion. ``owner_attestation`` records honestly that the owner has NOT attested
this run in session.

NO ``authorized_price_tuning`` KEY IS WRITTEN. ``calibration_verdict.py`` validates
any present value as a STRUCTURED rule-1 declaration, so prose there fails C6. The
declared-NONE statement lives in ``authorized_price_tuning_declared`` prose, which
is the SOCO-53/53c/53d/53e/53f convention.

Run: ``python scripts/gen_soco53g_attestation.py``
"""

from __future__ import annotations

import json
from pathlib import Path

BUNDLE = Path("results/calibration/soco53g_prb_own")

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names. The other
#: offer_curve_by_group keys (econ_low_share, pct_peaking) are STRUCTURAL shares
#: the carve-out EXCLUDES and are not 1.0 on any ISO.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: SOCO's keeper recipe (2026-09-20-soco53f-measured-coal-hr), which this lane
#: carries forward unchanged. ``coal_prb_proxy_own_iso`` is the single delta and
#: is asserted separately.
KEEPER_RECIPE = (
    "measured_ct_heat_rates",
    "egrid_family_heat_rates",
    "measured_st_heat_rates",
    "soco_gas_st_campaign_commitment",
    "measured_coal_heat_rates",
)


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
    if not sc.get("coal_prb_proxy_own_iso"):
        raise SystemExit("coal_prb_proxy_own_iso is not armed — wrong bundle")
    # `--set` routes this field through the generic prb_overrides channel, which
    # meta.json records as a coal_prb_sigmoid_overrides diff and audit_keepers
    # E11 flags. Benign — but the RESOLVED value must stay null, or the override
    # bag leaked into the PRB sigmoid registry for real.
    if sc.get("coal_prb_sigmoid_overrides") not in (None, {}):
        raise SystemExit(
            "resolved coal_prb_sigmoid_overrides is "
            f"{sc.get('coal_prb_sigmoid_overrides')!r}, expected null"
        )
    # The proxy is a FALLBACK. It can only reach a plant-month the per-plant
    # EIA-923 overlay does not, so a bundle with that overlay OFF is not the
    # run this attestation describes.
    if not sc.get("coal_plant_monthly_pricing"):
        raise SystemExit(
            "coal_plant_monthly_pricing is OFF — this attestation's whole "
            "inertness account assumes the per-plant overlay is live"
        )
    if not sc.get("coal_supply_repricing"):
        raise SystemExit("coal_supply_repricing is OFF — the mechanism cannot fire")
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
    ):
        if sc.get(name):
            raise SystemExit(f"{name} is armed — not this lane's recipe")


def _retag(att: dict, sc: dict) -> None:
    """Re-tag the two offer-curve DOF entries, as SOCO-40..53f did.

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
                "machine-verified by gen_soco53g_attestation._verify, which raises "
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
        "SOCO-53g re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40/53/53c/53d/53e/53f used and re-verified "
        "here by execution. n_entries 3 / n_residual 1, UNCHANGED from the keeper: "
        "this lane added NO free parameter, and no ScenarioConfig field either — "
        "coal_prb_proxy_own_iso already existed at HEAD (nwpp-41, 2026-09-17) with "
        "its frozen declared default 'False', so no cache key moves at any default. "
        "IT IS A ZERO-DOF SELECTION, NOT A VALUE: the flag chooses WHICH measured "
        "series the fallback pools, using the IDENTICAL quantity-weighted "
        "construction ERCOT already uses, over this market's own filed EIA-923 "
        "Schedule-2 receipts. Nothing is fitted, scaled, offset or swept, and there "
        "is no price residual in existence it could have been fitted to. The single "
        "remaining residual entry is the inherited wefor_multiplier, untouched here."
    )


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-53g bundle."""
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
            "SOCO-53g (lane), run 2026-09-20-soco53g-prb-own-iso. ONE mechanism is "
            "armed against the SOCO-53f keeper: ScenarioConfig.coal_prb_proxy_own_iso, "
            "which pools the PRB delivered-cost FALLBACK over SOCO's own EIA-923 "
            "Schedule-2 reporters (6002 Miller, 6073 Daniel, 6257 Scherer) instead of "
            "the hand-curated COAL_PLANT_SUPPLY map, EVERY plant of which is in Texas. "
            "Everything else is the keeper's recipe unchanged, and NO ScenarioConfig "
            "field was written: the mechanism already existed at HEAD (nwpp-41, "
            "2026-09-17) at bool = False with its frozen declared default, so no cache "
            "key moves at any default. "
            "THE MECHANISM IS A rule 25 [R-ISO-SCOPE] / rule 14 [R-ACCURATE] INPUT "
            "REPAIR WITH ZERO DEGREES OF FREEDOM: it selects WHICH measured series a "
            "fallback pools, by the identical quantity-weighted construction ERCOT "
            "already uses, over this market's own filed fuel receipts. Rule 13's "
            "forward test is met explicitly — the same quantity regenerates for a "
            "forward year from forward drivers (_build_coal_price_trajectories' PRB "
            "commodity / rail-diesel / rail-non-diesel limbs), _prb_monthly_actuals "
            "returns {} for a forward year so the trajectory takes over, and the "
            "series responds to a coal or rail-diesel shock. It is a measurement of "
            "fuel PURCHASED, never of dispatch, so no model output enters it. "
            "THE LANE'S COMMISSIONING PREMISE WAS FALSE AND THE PRECOMMIT SAID SO "
            "BEFORE THE SOLVE. FINDING-soco-53f §9 item 1 routed this lane on the "
            "reading that SOCO's three PRB plants are under-priced by 47-52 %, about "
            "$9.7/MWh. Both pooled numbers reproduce exactly (ERCOT 1.8228/1.7520/"
            "1.6147, SOCO 2.6711/2.4982/2.4610 $/MMBtu) but NEITHER REACHES THE LP: "
            "apply_coal_supply_pricing writes the proxy onto SOCO's 15 PRB tranche "
            "rows and apply_plant_monthly_fuel_prices then overwrites 8760/8760 cells "
            "on every one of them with each plant's own filed monthly cost. The model "
            "prices Miller at 2.1886, Daniel at 3.8505 and Scherer at 3.3945 (2023) — "
            "each plant's own receipts. MEASURED CONSEQUENCE: mc_base moves ZERO rows "
            "in 2023 and 2024 at max |delta| EXACTLY 0.000000000000, and in 2025 it "
            "moves four tranche rows of ONE plant (6073 Daniel) for 744 contiguous "
            "January hours, +0.6500 $/MMBtu / +7.7512 $/MWh, because Daniel filed no "
            "January-2025 receipt and the nearby-plant fallback did not reach it. "
            "Rule 19 [R-ONE-MECH]: ONE seam, machine-verified on fuel_prices AND "
            "mc_base, with every non-COAL class — ST_GAS, CT_PEAKER, CC_REGULAR, all "
            "three CHP classes, hydro — at max |delta| exactly 0.000000000000 in all "
            "three years, plant 6073's own 1,132 MW gas CC_REGULAR rows included. "
            "Barry (bituminous) is outside the mechanism by construction: "
            "price_by_supply carries only lignite and prb keys. Rule 25 / 28(d): "
            "SOCO's own measurement over SOCO's own plants; NWPP's fills no cell here "
            "and this fills none of NWPP's. Rule 21 [R-DOF]: ZERO free parameters "
            "added, and zero ScenarioConfig fields."
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
            "scripts/gen_soco53g_attestation.py::_verify, which raises rather than "
            "writing a false assertion — including that the keeper's own five flags "
            "are carried forward, that the per-plant EIA-923 overlay this lane's "
            "whole inertness account depends on is live, that the resolved "
            "coal_prb_sigmoid_overrides is null, and that none of the four "
            "default-off fields the PRECOMMIT's G-DRIFT audit classified INERT is "
            'armed. The SOCO-40 owner sitting of 2026-09-16 (verbatim: "I attest") '
            "covers the INHERITED posture this run does not change — the price "
            "posture, the identity offer bands, the three-zone topology, the served "
            "measured interchange, the coal split — but it predates and cannot speak "
            "to this lane's one new lever, so it is cited for what it covers and "
            "stretched no further. The promotion question is open and is put to the "
            "owner in the FINDING."
        ),
        "dof_basis": (
            "n_entries 3, n_residual 1 — UNCHANGED from the keeper, because this lane "
            "added no free parameter and no ScenarioConfig field. "
            "coal_prb_proxy_own_iso is a BOOLEAN SELECTOR over two measured series, "
            "not a value: armed, the fallback pools the quantity-weighted delivered "
            "cost of THIS market's own EIA-923 Schedule-2 coal receipts, by the "
            "identical construction the unarmed path applies to ERCOT's. Nothing is "
            "fitted, scaled, offset or swept. REPORTED AGAINST THIS ENTRY, because it "
            "cuts against the lane: the arm's only live consumer is one plant in one "
            "month, so the ledger entry it would have justified is, at SOCO today, "
            "almost entirely a FORWARD-LOOKING posture rather than a present "
            "correction — and that is the honest reading of its value."
        ),
    }

    att["disclosures"] = {
        "note": (
            "SOCO-53g determination basis. Everything the run does not establish, at "
            "full magnitude. The first three items are unflattering to this lane — a "
            "commissioning premise falsified, a cell already adjudicated INERT that "
            "the lane did not check before launching, and a mechanism that cannot "
            "move a single scored number — and they lead for that reason. The SOCO "
            "keeper's inherited basis lines follow and are unchanged."
        ),
        "1_THE_PREMISE_THAT_COMMISSIONED_THIS_LANE_IS_FALSE_AND_THE_PRECOMMIT_SAID_SO": (
            "FINDING-soco-53f §9 item 1 routed this lane on the claim that SOCO's "
            "three PRB plants (6,361.5 MW, 55 % of its coal capacity) are priced off "
            "the ERCOT-only pool and under-priced by +0.85 / +0.75 / +0.85 $/MMBtu, "
            "about $9.7/MWh — 'THREE TIMES SOCO-53f's lever, IN THE OPPOSITE "
            "DIRECTION'. Both pooled numbers are correct and reproduce exactly. THE "
            "INFERENCE IS WRONG, because neither pool reaches the LP. In the "
            "calibration path (run_calibration.py:4484-4495) apply_coal_supply_pricing "
            "writes the proxy and apply_plant_monthly_fuel_prices OVERWRITES it three "
            "lines later with each plant's own filed EIA-923 monthly delivered cost. "
            "Measured by replaying that exact mutation sequence with the proxy OFF and "
            "ON: step 2 moves 15 rows by 0.958 / 0.832 / 1.054 $/MMBtu, and step 3 "
            "returns 0.000000000000 (2023), 0.000000000000 (2024) and 0.649940697470 "
            "(2025). The overlay writes 8760/8760 cells on every one of those rows in "
            "2023 and 2024. The '47-52 % too cheap' reading compared two pool proxies "
            "to each other."
        ),
        "2_THE_MATRIX_CELL_WAS_ALREADY_ADJUDICATED_I_AND_THIS_LANE_DID_NOT_CHECK_IT_FIRST": (
            "docs/codebase-site/data/mechanism-matrix/SOCO.js already carried "
            "coal_prb_proxy_own_iso at cell 'I' (INERT), written by NWPP-41 on "
            "2026-09-17: 'SOCO has 3 prb-ranked plants and ALL THREE file their own "
            "EIA-923 delivered cost in every year 2023-2025, so "
            "apply_plant_monthly_fuel_prices overwrites the proxy on every one of "
            "them and the pool never reaches a SOCO plant.' Rule 28 [R-MECH-MATRIX] "
            "(a) forbids re-testing a cell adjudicated I without NEW evidence, and "
            "THIS LANE READ THE CELL ONLY AFTER LAUNCHING ITS SHARDS. That is a "
            "process miss and it is recorded as one. What makes the work admissible "
            "rather than a redo is that the measurement DID produce new evidence, and "
            "it corrects the cell: NWPP-41's census is at the PLANT-YEAR grain, and "
            "the grain that matters is the PLANT-MONTH. All three SOCO plants do file "
            "every year — and 6073 Daniel still skips JANUARY 2025, where the pool "
            "reaches it for 744 hours. The cell's closing sentence, 'Nothing to arm "
            "unless a SOCO PRB plant stops reporting', is therefore FALSIFIED: a "
            "plant that keeps reporting but misses one month is enough."
        ),
        "3_THIS_ARM_CANNOT_MOVE_A_SINGLE_SCORED_NUMBER_AND_THAT_WAS_REGISTERED_BEFORE_THE_SOLVE": (
            "2023 and 2024 were predicted BIT-IDENTICAL to the keeper (PRECOMMIT §6 "
            "P1/P2) on the measured ground that mc_base moves zero rows and that, for "
            "a SOCO backcast, fuel_prices reaches the LP ONLY through mc_base — its "
            "last functional use is run_calibration.py:4990, both "
            "build_*_offer_surface_conditional_markup calls, and both are PJM/CAISO-"
            "gated and off here. 2025 is the only year the mechanism is live, and "
            "EVERY 2025 C1 row is SKIPPED on the preliminary EIA-923 vintage. So the "
            "gated evidence (2023 and 2024) is unmoved by construction, the "
            "determination is unmoved, and the 2023 CT_PEAKER row remains SOCO's "
            "single C1 FAIL at +9.73 TWh. This arm neither fixes SOCO's headline "
            "defect nor worsens it. It is taken on rules 14 [R-ACCURATE] and 25 "
            "[R-ISO-SCOPE] and on no other ground, and its value today is 744 hours "
            "of one plant in an unscored year — its value FORWARD is that SOCO's PRB "
            "fallback becomes SOCO's own in every future gap-month."
        ),
        "4_the_live_2025_footprint_pinned_exactly": (
            "ONE plant, ONE month, 744 contiguous hours (2025-01-01 00:00 .. "
            "2025-01-31 23:00, hours 0-743, zero hours in any other month). Rows: "
            "Victor J Daniel Jr committed / econlo / econhi / peak (the mustrun row "
            "moves on fuel_prices but not on mc_base). Cause: the plant-monthly "
            "overlay wrote 8,016 of 8,760 cells on Daniel's rows — 744 short, exactly "
            "January — because Daniel filed no January-2025 receipt and the "
            "nearby_fuel_price_fallback did not reach it. Scherer ALSO missed a "
            "reporting month in 2025 (October) and the fallback DID cover it "
            "(8,760/8,760), so this is a per-plant gap and a missing receipt is an "
            "UPPER BOUND on the live footprint, not the footprint. Size: fuel +0.6500 "
            "$/MMBtu (1.7441 -> 2.3941), offer +7.7512 $/MWh, flat across the window. "
            "Exposure: Daniel's COAL tranches generated 0.2811 TWh in those hours "
            "under the keeper, of which 0.1405 TWh is at-risk econ/peak energy (the "
            "mustrun 0.1265 TWh is floored and cannot move). Absolute displacement "
            "bound 0.4108 TWh."
        ),
        "5_THERE_IS_NO_CIRCULARITY_AND_IT_IS_MEASURED_RATHER_THAN_ARGUED": (
            "The step-3 risk was real and named in the handoff: SOCO's pool IS the "
            "three plants being repriced. Three things dispose of it. (a) SOURCE: "
            "EIA-923 Schedule 2 fuel RECEIPTS AND COSTS — the delivered price and "
            "quantity of coal a plant PURCHASED. The model's dispatch, generation and "
            "prices do not enter it at any point. (b) RULE 13's FORWARD TEST is met "
            "and the code already implements it (see attested_by). (c) THE "
            "SELF-REFERENCE IS MEASURED AND IS EXACTLY ZERO: the arm's only live "
            "consumer is Daniel in January 2025, and DANIEL FILES NOTHING IN JANUARY "
            "2025 (its 2025 reported months are 2-12), so the January pool value is "
            "built from Miller and Scherer alone and the LEAVE-ONE-OUT value "
            "excluding Daniel is 2.3941 against the pooled 2.3941 — identical, "
            "because Daniel contributes no rows to that month by construction. The "
            "plant being priced contributes nothing to the number that prices it. "
            "AND THE ARM MOVES TOWARD TRUTH WITHOUT REACHING IT: Daniel's own nearest "
            "filed month is February 2025 at 3.4190 $/MMBtu, so the control's 1.7441 "
            "becomes 2.3941 against about 3.42 — roughly 39 % of the gap closed, and "
            "the residual understated rather than overstated."
        ),
        "6_the_pool_is_DEEPER_than_the_default_it_replaces_and_nothing_is_gap_filled": (
            "_prb_monthly_actuals fills a month with no report from the year's mean of "
            "the reported months, which would be a rule 14 [R-ACCURATE] misalignment "
            "concern if it were exercised. It is NOT, on either side: both pools "
            "report 12/12 months in all three years, so ZERO months are NaN-filled and "
            "the fill path never runs. And the finding runs the other way from the "
            "concern — SOCO's pool is backed by THREE reporters where the ERCOT "
            "default is backed by TWO. Five of the seven hand-curated COAL_PLANT_SUPPLY "
            "PRB plants file no coal receipt at all in 2023-2025, so 'the ERCOT pool' "
            "is in fact a two-plant Texas pool (6179, 7097). On pool depth the arm is "
            "the stronger input, not the weaker one. Quantity weights inside SOCO's "
            "pool (2023): Miller 0.6252, Scherer 0.3072, Daniel 0.0676."
        ),
        "7_level_or_shape_the_write_up_says_which": (
            "Overwhelmingly LEVEL, with a real shape limb in 2025 only. The monthly "
            "SOCO/ERCOT ratio stays inside 1.373-1.680 across all 36 months — a "
            "roughly uniform +40-60 % lift. Month-to-month correlation is +0.82 (2023) "
            "and +0.90 (2024), so the two series move together; but -0.32 in 2025, "
            "where the ERCOT series falls through the year (1.744 -> 1.550) while "
            "SOCO's rises mid-year. Both series are low-variance (cv 0.021-0.045)."
        ),
        "8_BARRY_UNIT_4_IS_PROVABLY_OUTSIDE_THIS_LANE_S_BLAST_RADIUS": (
            "The handoff flagged Barry unit 4 — a 362 MW COAL model row that CAMPD "
            "files as Pipeline Natural Gas and the model charges a COAL fuel price — "
            "as 'squarely in your blast radius' because this is a coal fuel-price "
            "lever. It is not, and the reason is structural: apply_coal_supply_pricing "
            "builds price_by_supply with exactly two keys, lignite and prb, and a "
            "'bituminous' row returns None and is skipped entirely. "
            "coal_supply_by_iso('SOCO') tags 3 Barry, 26 Gaston and 703 Bowen "
            "bituminous; only 6002/6073/6257 are prb. Measured: Barry's rows are not "
            "among the 15 that move at step 2 in any year, at max |delta| exactly "
            "0.000000000000. Barry unit 4's real defect is UNTOUCHED by this lane and "
            "stays ROUTED, exactly as FINDING-soco-53f §9 item 4 left it."
        ),
        "9_the_rule_17_re_measurement_this_lane_OWED_was_performed": (
            "The SOCO campaign floor reads a P0 pattern any arm can perturb, so the "
            "rule 17 [R-FLOOR-WINDOW] evidence had to be re-measured rather than "
            "inherited. Performed on this bundle's own floors/<year>_P1.npz with "
            "scripts/probes/_soco53g_floor_shares.py, first VALIDATED by reproducing "
            "the keeper's own table exactly — all fifteen cells, shares and median "
            "block lengths. The measured result is in the FINDING; the direction "
            "predicted before the solve was that 2023 and 2024 reproduce the keeper "
            "EXACTLY (they are bit-identical) and that only 2025 can move, RISING or "
            "holding, since a dearer Daniel commits marginally more gas steam in P0."
        ),
        "10_THE_CROSS_ISO_CENSUS_IN_THE_MECHANISM_S_OWN_DOCSTRING_IS_AT_THE_WRONG_GRAIN": (
            "_prb_monthly_actuals' docstring records the ERCOT series as sticking to "
            "non-reporting PRB plants in 'MISO (12 plants), PJM (2) and SPP (3-5) as "
            "well as NWPP (5)'. Re-censused here at the PLANT-MONTH grain over "
            "2023-2025, the PRB populations and missing plant-months are: MISO 38 "
            "plants / 36 fully-silent plant-years / 484 missing plant-months; SPP 29 / "
            "11 / 216; NWPP 9 / 15 / 180; ERCOT 7 / 15 / 181; PJM 2 / 6 / 72; SOCO 3 / "
            "0 / 2. TWO CORRECTIONS FOLLOW, and both are MEASUREMENTS ROUTED TO THOSE "
            "ISOS' OWN LANES, never verdicts (rules 25 [R-ISO-SCOPE] / 28(d)). First, "
            "the plant-count census UNDERSTATES the populations badly (MISO 38 not 12, "
            "SPP 29 not 3-5). Second, and cutting the other way, a missing receipt is "
            "an UPPER BOUND on the live footprint rather than the footprint, because "
            "nearby_fuel_price_fallback covers some of them — at SOCO it covered "
            "Scherer's October 2025 and not Daniel's January, so 2 missing "
            "plant-months yield 1 live one. THE ONLY TRUE MEASUREMENT IS THE "
            "MUTATION-SEQUENCE DECOMPOSITION (scripts/probes/_soco53g_phase0.py "
            "decompose), and each ISO's lane should run it on its own fleet before "
            "spending a solve. NWPP-41's own armed NWPP cell deserves the same "
            "re-measurement."
        ),
        "11_the_E11_recipe_diff_is_expected_declared_and_benign": (
            "coal_prb_proxy_own_iso is a ScenarioConfig field but NOT a "
            "solve_and_persist kwarg, so replay_keeper's --set routes it through the "
            "generic prb_overrides channel alone and meta.json records "
            "coal_prb_sigmoid_overrides {} -> {'coal_prb_proxy_own_iso': true}. "
            "audit_keepers E11 flags that at promotion. It was declared in the "
            "PRECOMMIT BEFORE the solve, the composer refuses any leg whose RESOLVED "
            "coal_prb_sigmoid_overrides is non-null, and _verify above re-checks it: "
            "the resolved value is null and the resolved coal_prb_proxy_own_iso is "
            "true. Nothing leaked into the PRB sigmoid registry."
        ),
        "12_2025_IS_REPORTED_BUT_NOT_GATED_AND_THAT_BINDS_THIS_LANE_S_RESULT": (
            "INHERITED FROM SOCO-40, UNCHANGED, and it binds this lane harder than any "
            "predecessor. On the preliminary EIA-923 vintage every 2025 C1 row is "
            "SKIPPED by the scorer (CT_PEAKER 17/23 plants unfiled, ST_GAS 1/7, CC_CHP "
            "5/6, ST_CHP 17/26). 2025 is the ONLY year this arm moves at all, and NONE "
            "of it is gated. The gated evidence is 2023 and 2024, where the arm is "
            "provably inert."
        ),
        "13_the_2025_hydro_input_hole_is_inherited_and_this_arm_nudges_it": (
            "SOCO-53b's 2025 EIA-923 hydro input hole is unchanged: 0.327 TWh modelled "
            "against 6.012 TWh measured, with coal backfilling the missing 5.68 TWh, "
            "which is why 2025 model coal already sits above actual. This arm makes "
            "Daniel's coal DEARER in January 2025, so it nudges that excess DOWN "
            "rather than up — the opposite of SOCO-53f's effect. That is a direction, "
            "not a repair, and it is not claimed as one: the fix is the input "
            "(--hydro-backfill-year / --hydro-eia930-monthly) and it stays ROUTED."
        ),
        "14_the_parasitic_load_factor_has_never_been_derived_for_SOCO": (
            "UNCHANGED FROM SOCO-53f §2.4 and re-routed with its numbers. SOCO's coal "
            "plants' own meter reads 0.866-0.928 against the committed class default "
            "0.93, so every SOCO coal heat rate in the current keeper is biased LOW by "
            "1.5-5.9 %. The committed chain is used anyway because it is the same "
            "factor the benchmark's net actual is built with. The real repair is "
            "derive_parasitic_load.py --iso SOCO, a cross-ISO intake re-keying 544 "
            "plants across seven ISOs. This lane does not touch heat rates at all."
        ),
        "15_THE_BENCHMARK_IS_STALE_AND_WAS_DELIBERATELY_NOT_REBUILT": (
            "SOCO's committed bench does not carry nyiso-240's EIA-923 repair "
            "(_backfill_eia923_missing_months, _reattribute_dual_fuel_oil), which "
            "FINDING-soco-53f §7 measured at +2.616 TWh of SOCO benchmark generation "
            "across 126 rows, and check_bench_freshness therefore flags all three SOCO "
            "parts STALE. dashboard_add_run.py's auto-rebuild was REVERTED and "
            "metrics.json re-written on the committed bench, exactly as SOCO-53c/53d/"
            "53e/53f did, so this run is scored on the same bench as the keeper it is "
            "differenced against. BOTH verdicts are computed and reported, labelled. "
            "Rebuilding SOCO's bench re-scores the keeper and is the desk's call, not "
            "a lane's."
        ),
        "16_a_shared_contract_test_is_RED_at_HEAD_and_was_NOT_patched": (
            "tests/unit/config/test_data_profiles_tokens.py::"
            "test_soco_token_collides_with_no_other_raw_name is RED at HEAD, "
            "independently of this lane — which adds no data artifact at all. The fix "
            "is a naming-convention decision across every SOCO artifact and belongs to "
            "the SOCO desk, not to a lane that would be silently patching a shared "
            "contract test to make its own PR green."
        ),
        "17_pre_existing_defects_inherited_unchanged": (
            "1,306.6 MW of pumped storage UNOBSERVABLE in EIA-930; Southern Power "
            "(186) excluded from the FERC-714 zonal shares as a documented NO, its "
            "3.211 / 3.401 / 3.084 TWh named and never absorbed; the Vogtle 3/4 COD "
            "month grain leaving nuclear -0.220 / -0.144 / -0.245 TWh; and the "
            "CT/ST misallocation that is SOCO's headline C1 defect, whose diagnosis "
            "across SOCO-53c/53e/53f is absent commitment physics rather than a "
            "cost-side error — untouched here, as it must be by a fuel-price lever."
        ),
        "18_the_price_gap_is_structural_and_permanent": (
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
