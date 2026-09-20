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
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

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
    """Re-tag the two offer-curve DOF entries, and LIST the measured basis.

    ``build_dof_ledger.py`` tags ``offer_curve_by_group`` and
    ``offer_curve_smoothing`` ``residual`` by default, because on every other
    ISO they ARE the rule-1 price-tuning surface. On SOCO they cannot be: the
    identity 1.0 on all four bands is not a tuned value, and there is no price
    residual in existence to have tuned it against. The re-tag is therefore a
    statement about THIS bundle, and it is re-verified by execution here rather
    than inherited — :func:`_verify` has already raised if any band is off the
    identity or any override, delta or smoothing is set.

    SOCO-55 additionally LISTS the three measured per-year basis values as
    explicit entries. The builder enumerates the ``ScenarioConfig`` surface and
    a ``constants.py`` table is not on it, so SOCO-54 disclosed its own scalar
    basis in ``dof_basis`` prose instead. This lane lists them, because rule 21
    ``[R-DOF]`` asks for EVERY free parameter with its identification source and
    these three ARE registered, solve-affecting numbers — listing is the more
    disclosing of the two conventions. They are tagged ``measured-physical``,
    so **n_residual is UNCHANGED at 1**, which is what rule 21 actually gates on.
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
                "machine-verified by gen_soco55_attestation._verify, which raises "
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
                    f"${value:+.2f}/MMBtu. MEASURED, not fitted: the quantity-weighted "
                    "EIA-923 Schedule-2 delivered natural-gas cost to the run's own "
                    "EIA-860 SOCO gas fleet in THIS year, minus the Henry Hub annual "
                    "mean for THIS year. Sources, both committed: "
                    "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet and "
                    "data/raw/gas-prices/henry_hub_monthly.csv. Re-derived at HEAD by "
                    "lane SOCO-55 and reproducing lane SOCO-20's committed comment "
                    "exactly (2023: 26 plants, 646,487,128 MMBtu, 3.0288 vs 2.5357 = "
                    "+0.4931; 2024: 27, 650,711,973, 2.8320 vs 2.1925 = +0.6395; 2025: "
                    "27, 641,283,196, 4.1829 vs 3.5289 = +0.6540), registered at the "
                    "2dp of every other GAS_BASIS_DIFFERENTIAL row. "
                    "NOT A RESIDUAL AND NOT SWEPT: no variant was solved, no value was "
                    "selected, the precision convention was fixed before the solve, and "
                    "SOCO has no price benchmark to have fitted any of it against. "
                    "Rule 23 [R-FROZEN-DERIVE]: the re-derivation is cited to SOURCE "
                    "DATA — the three years' own receipts, already computed and "
                    "committed in the scalar's own comment by SOCO-20 — never to a "
                    "moved residual."
                ),
            }
        )

    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    fp["retag_note"] = (
        "SOCO-55 re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40..54 used and re-verified here by "
        "execution. "
        "IT THEN ADDED THREE ENTRIES THE KEEPER'S LEDGER DOES NOT CARRY — the three "
        "measured per-year basis values — so n_entries reads 6 against the keeper's 3. "
        "THAT IS A DISCLOSURE CHOICE, NOT A NEW DEGREE OF FREEDOM: all three are "
        "tagged measured-physical, so **n_residual is UNCHANGED at 1** (the inherited "
        "wefor_multiplier), which is the figure rule 21 [R-DOF] gates on. "
        "build_dof_ledger.py enumerates the ScenarioConfig surface and a constants.py "
        "table is not on it, which is why SOCO-54 disclosed its own scalar basis in "
        "dof_basis prose rather than as an entry; this lane lists them instead, "
        "because they are registered solve-affecting numbers and listing is the more "
        "disclosing of the two conventions. "
        "THE ONE NEW ScenarioConfig FIELD, gas_basis_differential_measured_by_year, is "
        "NOT a free parameter and is deliberately not listed as one: it is a BOOLEAN "
        "GATE over two aggregations of the SAME measured receipts — one year's basis "
        "applied to every year, or each year's own — with no value, threshold, year "
        "scope or class scope to choose. It ships False, is registered in "
        "_CACHE_KEY_OPTIONAL_FIELDS at 'False' in the same commit as the field, and "
        "moves no pre-existing cache key. "
        "WHAT THIS LANE REMOVES from the keeper's ledger is the imprecision SOCO-54 "
        "disclosed against itself in dof_basis: the keeper's 0.64 is the 2024 value "
        "applied to every year, so its 2023 gas block carried +0.15 $/MMBtu — about "
        "+$1.65/MWh — that no measurement supports."
    )


def _disclosures() -> dict:
    """SOCO-55 determination basis. The items that cut against the lane lead."""
    return {
        "note": (
            "SOCO-55 determination basis. Everything the run does not establish, at "
            "full magnitude. The first three items are unflattering to this lane — the "
            "residual gets WORSE in the year the arm bites, the run does not change "
            "the determination at all, and the plant this lane's predecessor already "
            "flagged as over-dispatched is pushed further out — and they lead for that "
            "reason. The SOCO keeper's inherited basis lines follow."
        ),
        "1_THE_FIT_GETS_WORSE_IN_2023_AND_THE_ACCURATE_INPUT_IS_KEPT_ANYWAY": (
            "THIS IS THE HEADLINE AND IT IS AGAINST THE LANE. On the 2023 C1 rows the "
            "arm moves three of four the WRONG way and one the right way: CT_PEAKER "
            "+6.165 -> +6.910 TWh against actual (share +2.56 -> +2.87pp of a "
            "+/-3.00pp cap), COAL_PRB -0.429 -> -1.708, CC_REGULAR +4.166 -> +4.352, "
            "and only ST_GAS improves, -6.456 -> -6.149. Every row still PASSES and the "
            "determination does not move, but the 2023 residual is LARGER after the "
            "repair than before it. "
            "RULE 14 [R-ACCURATE] IS THE GOVERNING TEXT AND IT ANTICIPATES EXACTLY "
            "THIS: 'If swapping a hand estimate for real data makes the backcast worse, "
            "that is a signal that something else in the model is miscalibrated and the "
            "estimate was silently compensating for it. Treat the worse fit as a "
            "discovered bug: keep the accurate input, find and fix the real root cause. "
            "Do not bury the error back inside an inaccurate input.' The keeper's 2023 "
            "gas block was carrying +0.15 $/MMBtu of basis error that no measurement "
            "supports, and it was CANCELLING a real mispricing elsewhere. Reverting to "
            "0.64 to recover the fit is the thing rule 14 forbids, and rule 1 "
            "[R-STRUCT] forbids it a second time. "
            "WHAT THE ARM LOCALIZES — the successor's object, named at plant grain. "
            "The 1.279 TWh of 2023 coal displacement is 95 % ONE PLANT: 6002 James H "
            "Miller Jr, 15.838 -> 14.626 TWh against a 15.701 actual, i.e. the keeper "
            "had it nearly exact (+0.137) and the arm moves it to -1.075. Of the energy "
            "it sheds, roughly HALF lands on merchant turbines that are already far "
            "above their own actuals: 55409 Calhoun +0.115 (actual 0.026), 55061 "
            "Tenaska Georgia +0.111 (0.238), 7709 Dahlberg +0.109 (0.243), 55267 "
            "Addison +0.096 (0.200). The other half lands where it belongs: 2049 Jack "
            "Watson +0.147 toward a 3.270 actual and 728 Yates +0.087 toward 2.239. "
            "SO THE DISCOVERED BUG IS NAMED: SOCO's merchant CT tranche is priced too "
            "cheap against James H Miller's PRB coal, so ANY general reduction in the "
            "gas level lands disproportionately on a class that is already 2.5x its "
            "actual. That is a merit-order defect between CT_PEAKER and COAL_PRB, it is "
            "NOT the gas basis, and it is what a successor should attack."
        ),
        "2_THE_DETERMINATION_DOES_NOT_MOVE_AND_THIS_LANE_SAID_SO_BEFORE_SOLVING": (
            "The arm reads NOT-YET, exactly as the keeper does on the same rebuilt "
            "bench, and for the SAME single reason: 2024 CC_REGULAR at +7.505 TWh "
            "against a +/-7.47 TWh band. PRECOMMIT-soco-55 §4 P7 pre-registered this "
            "verbatim — 'THE 2024 CC_REGULAR C1 ROW IS UNCHANGED AT +7.505 TWh OF "
            "+/-7.47 AND STILL FAILS. THE DETERMINATION STAYS NOT-YET. This arm CANNOT "
            "close SOCO's failing row and is NOT TAKEN TO' — because at the registered "
            "2dp the 2024 measured basis equals the scalar exactly, so the 2024 LP "
            "input is identical. CONFIRMED: all eight 2024 artifacts are byte-identical "
            "to the keeper's, dispatch/2024_P1.parquet and floors/2024_P1.npz included. "
            "A lane that cannot move the failing row and says so first is not claiming "
            "a fit gain it did not earn."
        ),
        "3_55061_TENASKA_GEORGIA_IS_MADE_WORSE_AGAIN": (
            "SOCO-54 routed it at 1.412 -> 2.690 TWh against a 0.237 actual — 11x. This "
            "lane pushes it to 2.801, 12x. The mechanism is the same one SOCO-54 "
            "described: its own mc barely moves, the turbines above it fall further, "
            "and it is pulled in. 55409 Calhoun likewise goes 1.383 -> 1.498 against "
            "0.026. NEITHER IS FIXED HERE and both stay routed. "
            "AGAINST THAT: SOCO-54's OTHER routed plant, 2049 Jack Watson — the one "
            "ST_GAS unit that lane pushed the wrong way, 2.355 -> 1.256 against a 3.270 "
            "actual — recovers to 1.403 here. Partial, and reported as partial."
        ),
        "4_EVERY_ONE_OF_THIS_LANE_S_FOURTEEN_PRE_REGISTERED_PREDICTIONS_HELD_AND_TWO_WERE_CLOSE": (
            "P1 coal falls, banded -0.05 to -1.6 TWh: delivered -1.279. P2 CC_REGULAR "
            "rises, 0.0 to +1.2: +0.187. P3 CT_PEAKER rises, 0.0 to +0.8: +0.744 — "
            "inside, but at 93 % of the band's upper edge, and the band was nearly too "
            "tight. P4 ST_GAS within +/-0.6: +0.307. P5 2024 byte-identical: CONFIRMED "
            "on all eight artifacts. P6 every 2025 class under 0.15 TWh: max 0.0032. P7 "
            "2024 CC_REGULAR unchanged and still failing, determination NOT-YET: exact. "
            "P8 no 2025 C1 row scored: all SKIPPED. P9 C2/C4/C6/C8 PASS, 0 ledgered, 0 "
            "protective: held. P10 DOF gains three measured entries, n_residual 1, zero "
            "free parameters: 6/1. P11 rule 17 holds in all fifteen plant-years: it "
            "does, with positive margin everywhere — and the DIRECTION was deliberately "
            "NOT predicted (SOCO-54's P11 got the gate right and the direction wrong); "
            "728 Yates binds MORE (0.482 -> 0.514) and 2049 Watson slightly LESS (0.557 "
            "-> 0.548). P12 ST_GAS forced share stays under the 0.30 cap, direction "
            "unpredicted: 0.1375 -> 0.1241 in 2023, unchanged in 2024/2025. P13 peers "
            "byte-identical, no key moves. P14 SOCO 182 -> 183 surface rows with "
            "moved_rows {}. "
            "P3-RISK — the lane's declared #1 risk, that 2023 CT_PEAKER might cross to "
            "FAIL — MATERIALISED SHORT OF A FLIP and is stated at full magnitude: the "
            "row still PASSES, but its SHARE headroom collapses from 0.44pp to 0.13pp "
            "of the +/-3.00pp cap. It is now the thinnest row in the run after 2024 "
            "CC_REGULAR, and the next thing that moves 2023 gas up will break it."
        ),
        "5_D_1_DIURNAL_SHAPE_IS_UNCHANGED_IN_COUNT_AND_SLIGHTLY_WORSE_IN_LEVEL": (
            "D-1 is REPORTED, not gated — the standalone C7 gate was retired at rubric "
            "v3.1 and D-1 now binds only through rule 20 [R-FORCED-BUDGET]'s shape leg "
            "for a class over its forced-energy budget, which no SOCO class is. Both "
            "the keeper and the arm carry THREE D-1 failures, the same three: 2023 "
            "COAL_BIT profile r (0.469 -> 0.438, slightly WORSE), 2023 COAL_BIT off-peak "
            "CV ratio (0.003 -> 0.002), and 2025 COAL_BIT profile r (0.785, unchanged). "
            "No class clears and none is added."
        ),
        "6_THE_SOLVE_SURFACE_FINGERPRINT_MOVED_AND_ONE_ROW_OF_IT_IS_THIS_LANE_S": (
            "SOCO's capx-D79 fingerprint reads 36087ac69210fdb2 / 183 rows on all three "
            "legs, against the keeper's 60895cac1f7c8879 / 182. moved_rows('SOCO') is "
            "{} — ZERO existing rows changed value. The +1 row is THIS lane's new "
            "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR, DECLARED at its live hash in "
            "solve_surface_declared, which is the designed capx-D79 behaviour: adding a "
            "table moves no key. The scalar GAS_BASIS_DIFFERENTIAL row is UNMOVED and "
            "machine-verified still 0.64, because this lane GATES the scalar rather "
            "than editing it — so every unarmed run, every peer ISO and every forecast "
            "year keeps its key and its number. "
            "STILL RED AT HEAD AND STILL NOT THIS LANE'S: PPA_COST_RECOVERY_YR and "
            "REGIONAL_RENEWABLE_CF have no DECLARED entry (commit 3fc20b97, the "
            "MAC-sidecar lane). This lane declared its OWN name only and left those two "
            "to their lane. tests/regression/test_persisted_identity.py and "
            "tests/unit/config together fail 11 tests at origin/main and 11 with this "
            "change — measured both ways, in a clean worktree: ZERO new failures."
        ),
        "7_THE_E11_SET_TRANSPORT_IS_DECLARED_AND_THE_RESOLVED_VALUE_IS_NULL": (
            "replay_keeper --set routes a ScenarioConfig field that is not a "
            "solve_and_persist kwarg through the generic prb_overrides channel, so each "
            "leg's meta.json records a coal_prb_sigmoid_overrides diff and "
            "audit_keepers E11 flags it. DECLARED IN THE PRECOMMIT BEFORE THE SOLVE and "
            "machine-verified benign on every leg and on the composite: the RESOLVED "
            "scenario_config.coal_prb_sigmoid_overrides is null. Both the composer and "
            "_verify raise on a non-null value."
        ),
        "8_OTHER_ISOs_DO_CARRY_CONSTANT_MULTIPLIER_CONTRACT_FAMILIES_AND_THAT_IS_REPORTED_NOT_TAKEN": (
            "SOCO-54 §9 item 9 routed the cross-ISO question and this lane MEASURED it, "
            "zero LP, using SOCO-54's own method — try every reporting plant as the "
            "reference row and report the largest set whose monthly delivered-price "
            "ratio series is flat (CV <= 0.001) over 10-12 months. Largest family, by "
            "ISO and year (2023 / 2024 / 2025, of that year's reporting plants): "
            "SOCO 7/24, 8/25, 8/26 — the family SOCO-54 found. "
            "SPP 6/63, **50/60**, **50/54**. ERCOT 9/20, 10/23, **26/26**. "
            "MISO 7/102, 7/98, 6/100. PJM 6/26, 6/25, 6/23. NWPP 3/28, 4/29, 3/26. "
            "NYISO and CAISO: NONE in any year (largest family is the reference row "
            "alone, 5 and 6-7 reporting plants). NEISO: VOID, 1 reporting plant. "
            "SPP's keeper ARMS gas_plant_monthly_fuel_pricing and 50 of its 60 reporting "
            "plants file one common shape; ERCOT's cell is already G for an unrelated, "
            "documented reason. RULES 25 [R-ISO-SCOPE] / 28(d): THIS IS REPORTED AND "
            "NOTHING ELSE. No other ISO's cell is filled, no other ISO's parameter is "
            "derived, and no verdict transfers. Each lane owns its own footprint's "
            "receipts and must measure them itself before concluding anything."
        ),
        "9_WHAT_IS_STILL_BROKEN_AFTER_THIS_LANE": (
            "SOCO is NOT-YET on the only benchmark that reproduces from the builder at "
            "HEAD, and this lane does not change that. The failing row is 2024 "
            "CC_REGULAR, +7.505 TWh of +/-7.47 — a 0.035 TWh miss, 0.47 % over band, "
            "and this arm is provably inert in 2024. The standing misallocation is "
            "unchanged in character: CC_REGULAR runs 7.5 TWh too hard in 2024 while "
            "ST_GAS is 5.3 TWh short and COAL_PRB 4.1 TWh short. The named successors, "
            "in order: (a) THE CT_PEAKER / COAL_PRB MERIT ORDER at James H Miller, "
            "which item 1 localizes and which is new evidence this lane produced; (b) "
            "55061 Tenaska Georgia and 55409 Calhoun, both worsened here; (c) the 2024 "
            "CC_REGULAR level itself, which no lane has yet attacked directly."
        ),
        "10_derive_parasitic_load_has_never_been_run_for_SOCO": (
            "Unchanged from FINDING-soco-53f §2.4, -53g §9.3 and -54 §9.6, re-routed "
            "with its numbers: SOCO's coal plants' own meter reads 0.866-0.928 against "
            "the committed 0.93 class default, so every SOCO coal heat rate is biased "
            "LOW by 1.5-5.9 %. NOTE THE SIGN, because it matters to item 1: a heat rate "
            "biased LOW makes coal look CHEAPER than it is, so correcting it would move "
            "coal DOWN — the wrong direction for a 2024 COAL_PRB that is already 4.1 TWh "
            "short. It is a cross-ISO intake (544 plants, 7 ISOs) and is reported, never "
            "taken by a lane."
        ),
        "11_SOCO_53b_the_2025_hydro_input_hole": (
            "0.327 TWh modelled against 6.012 measured; coal backfills it and the LP "
            "posts 8,930.2 MWh of VOLL slack, which is what makes the 2025 model price "
            "uninterpretable. This lane touches hydro not at all — byte-identical in "
            "all three years, and the slack is identical to the keeper's to the MWh. "
            "Instruments: --hydro-backfill-year / --hydro-eia930-monthly."
        ),
        "12_Barry_unit_4": (
            "A 362 MW COAL model row that CAMPD files as Pipeline Natural Gas and the "
            "model charges a COAL fuel price. Outside this lane's gas-basis seam by "
            "construction; still routed."
        ),
        "13_audit_keepers_E13_fires_for_the_SEVENTH_consecutive_SOCO_lane": (
            "2026-09-20-soco53g-prb-own-iso is a registered CANDIDATE the owner has not "
            "ruled on, so it is neither the keeper nor stamped to one. Rule 31 "
            "[R-RETAIN] forbids deleting it and rule 30 (a) forbids inventing a "
            "holdout.keeper stamp for it, so E13 is RE-RAISED rather than cleared, and "
            "THE OWNER IS ASKED FOR A RULING IN THE FINDING. It clears when the owner "
            "rules, not before. This lane's own run adds a SECOND unruled candidate for "
            "the same reason, and says so rather than pruning either."
        ),
        "14_THE_BENCHMARK_WAS_STALE_AND_THIS_LANE_REBUILT_IT_RATHER_THAN_SCORING_ON_BOTH": (
            "SOCO-54 scored on BOTH benches and routed the rebuild to the desk as 'the "
            "desk's call, not a lane's'. THIS LANE TOOK IT. check_bench_freshness was "
            "RED for SOCO ALONE repo-wide — 3 STALE parts of 44, a hard ::error against "
            "41 warning-level engine drift elsewhere — and now reads 0 STALE. The "
            "consequence is stated rather than softened: the incumbent keeper's "
            "published headline moves from PHYSICALLY-CALIBRATED (PRICE UNSCORED) to "
            "NOT-YET, because 2024 CC_REGULAR crosses +7.417 -> +7.505 TWh against a "
            "+/-7.47 band on a -0.088 TWh change in that row's benchmark ACTUAL. "
            "PRECOMMIT-soco-54 P4 pre-registered exactly that row at 81 % of its "
            "margin. NO DISPATCH MOVED: every keeper hourly sidecar is byte-identical "
            "to the day it was solved and its run payload re-renders byte-identical. "
            "ONLY THE BENCHMARK MOVED, and the ISO's ceiling reading rested on a "
            "benchmark that could not be reproduced from the builder at HEAD."
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
            "1,306.6 MW of pumped storage UNOBSERVABLE in EIA-930; Southern Power (186) "
            "excluded from the FERC-714 zonal shares as a documented NO, its 3.211 / "
            "3.401 / 3.084 TWh named and never absorbed; and the Vogtle 3/4 COD month "
            "grain leaving nuclear -0.220 / -0.144 / -0.245 TWh. Nuclear, hydro, wind, "
            "solar and biomass are byte-identical to the keeper in all three years."
        ),
        "17_the_price_gap_is_structural_and_permanent": (
            "NO PUBLIC SOCO PRICE EXISTS AND NONE EVER WILL. actual_lmp.json carries no "
            "SOCO block and must not gain one — a placeholder breaks "
            "calibration_verdict._price_reference_absent and silently moves SOCO onto "
            "the ordinary determination path. C3a / C3b / C3c are UNSCORABLE, NOT "
            "FAILED, in every year. The ceiling is rubric v3.8 PHYSICALLY-CALIBRATED "
            "(PRICE UNSCORED); SOCO can NEVER read CALIBRATED. Scored on C1 / C2 / C4 / "
            "C6 / C8 only. Gate G17 absolute: no neighbouring hub, no proxy, no "
            "cost-stack price, ever. The model's own load-weighted mean LMP is "
            "MODEL-ONLY and UNVERIFIED and is never quoted as price skill — and this "
            "lane moved it, 34.040 -> 32.785 $/MWh in 2023 and 197.253 -> 197.336 in "
            "2025, with 2024 unchanged at 30.153. That movement certifies NOTHING, is "
            "reported as a model-only number, and is NOT evidence for or against the "
            "lever."
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
            "SOCO-55 (lane). ONE mechanism moves against the incumbent keeper "
            "2026-09-20-soco54-marginal-gas-basis: ScenarioConfig."
            "gas_basis_differential_measured_by_year, turned ON. Everything else is "
            "that keeper's recipe unchanged, machine-verified by _verify — including "
            "SOCO-54's own gas_plant_monthly_fuel_pricing=False, without which this "
            "is not a single-delta arm off that keeper. "
            "THE CLAIM IS ABOUT THE INPUT'S VINTAGE, NOT ABOUT THE RESIDUAL. "
            "GAS_BASIS_DIFFERENTIAL['SOCO'] = 0.64 is the 2024 value, and the "
            "constant's own comment registers it as a 'forward-year / fallback value "
            "only' on the stated ground that 'the SOCO backcast prices gas per plant "
            "off EIA-923 monthly delivered cost like PJM/NYISO'. SOCO-54 made that "
            "sentence false: turning the per-plant print off promoted the declared "
            "FALLBACK onto SOCO's PRIMARY backcast gas-pricing path, where "
            "resolve_annual_gas_price returns gas_price_override + 0.64 for every "
            "SOCO gas unit in every year. Measured, the basis is +0.4931 / +0.6395 / "
            "+0.6540 for 2023 / 2024 / 2025, so 2023 was carrying +0.15 $/MMBtu — "
            "about +$1.65/MWh — on every SOCO gas unit. Rule 14 [R-ACCURATE] governs: "
            "prefer the accurate input, and if the fit worsens treat that as a "
            "discovered bug rather than burying it back in an inaccurate input. "
            "IT IS A RULE 23 [R-FROZEN-DERIVE] RE-DERIVATION CITED TO SOURCE DATA. "
            "The three values are the quantity-weighted EIA-923 Schedule-2 delivered "
            "gas cost to the run's own EIA-860 SOCO gas fleet minus the Henry Hub "
            "annual mean, re-run at HEAD by this lane and reproducing SOCO-20's "
            "committed comment exactly. They were already computed and committed in "
            "the scalar's own comment before this lane existed. NOTHING WAS SWEPT: no "
            "variant was solved, and the 2dp precision is the convention every other "
            "GAS_BASIS_DIFFERENTIAL row carries — fixed before the solve, declared in "
            "the PRECOMMIT, and not selectable by a result. A declared consequence of "
            "that convention, stated ex ante rather than discovered: at 2dp the 2024 "
            "value is unchanged, so the 2024 leg is byte-identical — CONFIRMED on all "
            "eight artifacts including dispatch/2024_P1.parquet and floors/2024_P1.npz. "
            "Rule 13 [R-MEASURED]'s forward test is met: the same quantity is "
            "producible for a forward year from that year's own receipts and responds "
            "to changed conditions, and where receipts do not exist the forward scalar "
            "is used unchanged — verified zero-LP, SOCO 2030 armed = 5.12 = SOCO 2030 "
            "unarmed. It measures fuel PURCHASED and a published market price, never "
            "dispatch, so no model output enters it. "
            "Rule 19 [R-ONE-MECH]: ONE seam, and the measured basis REPLACES the "
            "scalar rather than adjusting it. Machine-verified at two grains on "
            "fuel_prices AND mc_base before the solve — the six GAS classes move "
            "(CC_REGULAR, CT_PEAKER, ST_GAS, CC_CHP, CT_CHP, ST_CHP) and COAL_PRB, "
            "COAL_BIT, oil, nuclear, hydro, wind, solar and biomass are at max |delta| "
            "EXACTLY 0.000000000000 in all three years; 2024 is 0.000000000000 at BOTH "
            "grains. "
            "Rule 25 [R-ISO-SCOPE]: GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR carries a "
            "SOCO row AND NOTHING ELSE — machine-verified — so every other ISO falls "
            "through to its own scalar unchanged and is inert by construction and by "
            "measurement. No peer ISO's basis is derived, transferred or filled here. "
            "Rule 21 [R-DOF]: ZERO free parameters added. n_residual is UNCHANGED at 1."
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
            "scripts/gen_soco55_attestation.py::_verify, which raises rather than "
            "writing a false assertion — including that the single delta is on the ARM "
            "side of the A/B; that the live GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR "
            "['SOCO'] table is the one this attestation describes; that the SCALAR "
            "GAS_BASIS_DIFFERENTIAL['SOCO'] is untouched at 0.64, because this lane "
            "GATES the scalar rather than editing it and every unarmed run must keep "
            "it; that no non-SOCO row exists in the measured table; that SOCO-54's "
            "gas_plant_monthly_fuel_pricing=False and the keeper's five heat-rate / "
            "commitment flags are carried forward; that the COAL print path this lane "
            "does NOT touch is still live; that the resolved coal_prb_sigmoid_overrides "
            "is null; that SOCO-53g's open coal_prb_proxy_own_iso candidate is NOT "
            "armed; and that none of the eight fields classified INERT is armed. "
            'The SOCO-40 owner sitting of 2026-09-16 (verbatim: "I attest") covers the '
            "INHERITED posture this run does not change — the price posture, the "
            "identity offer bands, the three-zone topology, the served measured "
            "interchange, the coal split — but it predates and cannot speak to this "
            "lane's one lever, so it is cited for what it covers and stretched no "
            "further. The promotion question is open and is put to the owner in the "
            "FINDING."
        ),
        "dof_basis": (
            "n_entries 6, n_residual 1. The RESIDUAL count — the figure rule 21 "
            "[R-DOF] gates on — is UNCHANGED from the keeper, because this lane added "
            "no fitted value. n_entries rises 3 -> 6 purely because this lane LISTS "
            "the three measured per-year basis values as explicit measured-physical "
            "entries where SOCO-54 disclosed its single scalar in this prose block "
            "instead; see free_parameters.retag_note. "
            "gas_basis_differential_measured_by_year is a BOOLEAN GATE over two "
            "aggregations of the SAME measured receipts — one year's basis applied to "
            "every year, or each year's own — with no value, threshold, year scope or "
            "class scope to choose. It ships False and is registered in "
            "_CACHE_KEY_OPTIONAL_FIELDS at 'False' in the same commit as the field, so "
            "no pre-existing cached run is re-keyed. "
            "WHAT IT REMOVES is the imprecision SOCO-54 disclosed against itself in "
            "this same field: its 0.64 is the 2024 value applied to every year, so its "
            "2023 gas block carried +0.15 $/MMBtu that no measurement supports. "
            "WHAT IT DOES NOT REMOVE, stated here because it cuts against the lane: "
            "the SOCO backcast still prices every gas unit off ONE footprint-wide "
            "delivered level per year. A plant-specific delivered cost with a credible "
            "basis — a daily hub index plus measured variable transport — does not "
            "exist for this footprint (no free public daily index at SONAT or "
            "Transco/Dalton, SOCO-12 §4), so the remaining within-footprint dispersion "
            "is unmodelled and is a successor's object, not this lane's."
        ),
    }
    att["disclosures"] = _disclosures()
    _retag(att, sc)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
