"""SOCO-58: write ``calibration_attestation.json`` for the warm-boiler-exemption arm.

Adapted from :mod:`scripts.gen_soco57_attestation`, which is the SOCO desk's
convention. What differs is the delta being attested, the disclosures, and the
FORM the by-execution verification has to take.

THE DELTA. ``ScenarioConfig.coal_warm_committed``, turned ON against the
incumbent keeper ``2026-09-20-soco57-measured-cc-heat``. It exempts a CAMPD coal
bin whose per-plant must-run floor holds its boiler online from the P1
startup-amortization markup, because dispatching its ``_committed`` tranche is an
output ramp on a hot unit rather than a cold start.

WHY, IN ONE SENTENCE: the model was charging SOCO's coal fleet a $100/MW COLD
START — amortized to EXACTLY $100.00/MWh at four of six plants in 2024, the
``startup / max(avg_run, 1.0)`` floor reached when a tranche has ZERO P0 runs —
on a boiler that the model's own dispatch holds at must-run load fraction 1.00
in 100.0 % of the hours the charge applies, pricing 19.8 TWh of available coal
capacity at $140–177/MWh into a $28.27/MWh market.

**THE VERIFICATION HAS A DIFFERENT SHAPE HERE, AND THAT IS THE POINT.** SOCO-53e
… SOCO-57 each shipped a committed CSV, so their attestations verified an
ARTIFACT's identity. This lane ships no artifact: it arms an existing registered
boolean over a fleet the keeper already carries. What :func:`_verify_scope`
checks by execution is therefore the two factual claims the attestation actually
makes — (a) the exemption's scope is exactly the set of tranches that pay the
markup, 6 of 6, with 0 coal tranches missed and 0 non-coal tranches touched, and
(b) the warm-boiler PREDICATE holds at 100.0 % in every coal plant-year — both
recomputed from the composed bundle's own recipe and its own committed hourlies.
It RAISES rather than writing a false assertion.

**THE FLEET GRAINS ARE EXPECTED TO READ ZERO, AND THAT IS THE CORRECT SIGNATURE,
NOT AN INERT ARM.** This mechanism lives entirely at the P0→P1 seam
(``model/commitment.py::compute_monthly_markup``, one call site,
``pipeline/solve.py:518``), so ``fuel_prices`` / ``mc_base`` / ``pmax`` /
``availability`` / ``heat_rate`` all move by exactly zero and P0 is
byte-identical. That is the inverse of SOCO-57 §4's wiring defect, where
all-grains-zero meant an arm that never armed; the resolved-config assertion in
:func:`_verify` is what separates the two cases.

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
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BUNDLE = Path("results/calibration/soco58_warm_committed")

#: The four price-tuning bands rule 1 [R-STRUCT]'s carve-out names.
PRICE_TUNING_BANDS = ("committed", "econ_low", "econ_high", "peak")

#: SOCO's keeper recipe (2026-09-20-soco57-measured-cc-heat), carried forward
#: unchanged. ``coal_warm_committed`` is this lane's single delta and is
#: asserted separately, to True.
KEEPER_RECIPE = (
    "measured_ct_heat_rates",
    "egrid_family_heat_rates",
    "measured_st_heat_rates",
    "soco_gas_st_campaign_commitment",
    "measured_coal_heat_rates",
    "measured_cc_heat_rates",
    "gas_basis_differential_measured_by_year",
    "coal_plant_monthly_pricing",
    "campd_per_unit_attribution",
)

#: SOCO-55's measured per-year gas basis, INHERITED. Asserted against the live
#: constant so this attestation cannot describe a table the run did not use.
MEASURED_BASIS = {2023: 0.49, 2024: 0.64, 2025: 0.65}

#: soco-72: the SAME construction's 2019-2022 rows, added when the keeper's span
#: reached 2019 (docs/handoffs/r-soco/PRECOMMIT-soco-72-2026-09-26.md §2). The live
#: table must equal SOCO-55's rows plus these; the ledger keeps SOCO-55's three
#: inherited entries and soco-72's single entry is appended by that lane.
SOCO72_BASIS = {2019: 0.27, 2020: 0.32, 2021: 0.30, 2022: 1.20}

#: The scope this attestation claims, verified by execution in
#: :func:`_verify_scope`. Six coal ``_committed`` tranches, one per plant.
EXPECTED_EXEMPT_TRANCHES = 6
EXPECTED_EXEMPT_MW = 3464.0
EXPECTED_COAL_PLANTS = (3, 26, 703, 6002, 6073, 6257)

#: The NREL coal cold-start cost the exemption removes, $/MW. Not a parameter of
#: this lane — it is the value the markup path already carried.
COAL_STARTUP_PER_MW = 100.0


def _verify_scope(years: list[int]) -> dict:
    """Raise unless the exemption's scope and its physics predicate are as claimed.

    (a) SCOPE. Rebuild the fleet off the bundle's own recipe and apply the
    exemption's own predicate (``fuel_type == 'coal' and must_run_pct > 0``,
    transcribed from ``compute_monthly_markup``). The tranches it exempts must be
    EXACTLY the coal tranches that carry a startup cost — no coal tranche paying
    the markup may be missed, and no non-coal tranche may be touched.

    (b) PREDICATE. From the bundle's own committed ``unit_hourly_<y>.parquet``:
    in every hour a plant's ``_committed`` tranche carries capacity, that plant's
    ``_mustrun`` tranche must be generating. Anything below 100 % would mean the
    boiler is sometimes dark when the charge applies, and the warm-boiler
    argument would be false for those hours.
    """
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: PLC0415
    from scripts.run_calibration import run_year  # noqa: PLC0415

    meta = json.loads((BUNDLE / "meta.json").read_text())
    probe_year = years[0]
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, probe_year))
    built = run_year(
        probe_year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )
    fleet, fa = built["fleet"], built["fleet_arrays"]

    exempt, coal_paying, noncoal_touched, exempt_mw = [], [], [], 0.0
    for i, g in enumerate(fleet):
        is_coal = str(getattr(g, "fuel_type", "")) == "coal"
        mrp = float(getattr(g, "must_run_pct", 0.0) or 0.0)
        pays = float(getattr(g, "startup_cost_per_mw", 0.0) or 0.0) > 0.0
        predicate = is_coal and mrp > 0.0
        if predicate:
            exempt.append(str(getattr(g, "unit_id", "")))
            exempt_mw += float(np.asarray(fa.pmax)[i])
            if not is_coal:
                noncoal_touched.append(str(getattr(g, "unit_id", "")))
        if is_coal and pays and not predicate:
            coal_paying.append(str(getattr(g, "unit_id", "")))
        if predicate and not is_coal:
            noncoal_touched.append(str(getattr(g, "unit_id", "")))

    if len(exempt) != EXPECTED_EXEMPT_TRANCHES:
        raise SystemExit(
            f"the exemption covers {len(exempt)} tranches, expected "
            f"{EXPECTED_EXEMPT_TRANCHES}: {sorted(exempt)!r}"
        )
    if coal_paying:
        raise SystemExit(
            "coal tranches pay the markup but are NOT exempted — the exemption's "
            f"scope is not the set it claims: {sorted(coal_paying)!r}"
        )
    if noncoal_touched:
        raise SystemExit(
            f"non-coal tranches are touched by the exemption: {sorted(noncoal_touched)!r}"
        )
    if not all(u.endswith("_committed") for u in exempt):
        raise SystemExit(
            f"an exempted tranche is not a _committed band: {sorted(exempt)!r}"
        )
    if round(exempt_mw, 1) != EXPECTED_EXEMPT_MW:
        raise SystemExit(
            f"exempted capacity is {exempt_mw:.1f} MW, expected {EXPECTED_EXEMPT_MW}"
        )

    # (b) the warm-boiler PREDICATE, on the bundle's own committed hourlies.
    predicate_rows = {}
    for y in years:
        uh = pd.read_parquet(BUNDLE / f"hourly/unit_hourly_{y}.parquet")
        uh = uh[(uh["pass"] == "P1") & uh.plant_group.eq("COAL")]
        for pl, d in uh.groupby("plant_code"):
            cm = (
                d[d.unit_id.str.endswith("_committed")]
                .set_index("hour")[["cap_mw"]]
                .rename(columns={"cap_mw": "cap_cm"})
            )
            mr = (
                d[d.unit_id.str.endswith("_mustrun")]
                .set_index("hour")[["mw"]]
                .rename(columns={"mw": "mw_mr"})
            )
            live = cm.join(mr, how="inner")
            live = live[live.cap_cm > 0.01]
            if not len(live):
                continue
            pct = round(100.0 * float((live.mw_mr > 0.01).sum()) / len(live), 2)
            predicate_rows[f"{y}:{int(pl)}"] = pct
            if pct < 100.0:
                raise SystemExit(
                    f"{y} plant {int(pl)}: the warm-boiler predicate holds in only "
                    f"{pct}% of the hours its _committed tranche carries capacity — "
                    "the boiler is sometimes DARK when the exempted charge would "
                    "apply, so this attestation's physical claim is false"
                )

    return {
        "exempt_tranches": sorted(exempt),
        "exempt_mw": round(exempt_mw, 1),
        "coal_tranches_paying_but_not_exempted": len(coal_paying),
        "noncoal_tranches_touched": len(noncoal_touched),
        "warm_boiler_predicate_pct_by_plant_year": predicate_rows,
        "warm_boiler_predicate_min_pct": (
            min(predicate_rows.values()) if predicate_rows else None
        ),
        "plant_years_checked": len(predicate_rows),
        "startup_cost_removed_per_mw": COAL_STARTUP_PER_MW,
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

    # --- the single delta, asserted to the side of the A/B this lane solved.
    # This is the ONLY thing that can tell an armed leg from a control: the
    # mechanism moves no fleet grain, by construction.
    if not sc.get("coal_warm_committed"):
        raise SystemExit(
            "coal_warm_committed is OFF — this bundle is the CONTROL, not the "
            "SOCO-58 arm"
        )
    # Rule 19 [R-ONE-MECH]: exactly one mechanism may act on the coal committed
    # band's PRICE. The take-or-pay family reprices the same tranche's fuel and
    # would stack with this exemption on one object, so every limb stays off.
    for name in (
        "coal_takeorpay_from_data",
        "coal_bit_committed_takeorpay",
        "coal_committed_takeorpay_all",
        "coal_committed_takeorpay_regulated",
        "coal_committed_takeorpay_sunk_fixed",
        "coal_fuel_inventory",
        "committed_ramp_spread",
    ):
        if sc.get(name):
            raise SystemExit(
                f"{name} is armed alongside coal_warm_committed — that is a "
                "second mechanism on the coal committed band (rule 19)"
            )
    # The family's OTHER class-scoped gate. SOCO's ST_GAS carries no startup
    # markup (measured at -0.000), and arming it would ADD start costs to a
    # footprint with no clearing price — the object SOCO's tranche_startup_
    # amortization `G` cell refuses.
    if sc.get("gas_st_startup_cost"):
        raise SystemExit(
            "gas_st_startup_cost is armed — that ADDS start costs to SOCO's bids, "
            "which is what the tranche_startup_amortization G cell refuses"
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
    if live != {**SOCO72_BASIS, **MEASURED_BASIS}:
        raise SystemExit(
            f"GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR['SOCO'] is {live!r}, "
            f"expected { ({**SOCO72_BASIS, **MEASURED_BASIS})!r}"
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
    # --- rule 25: the DOF ledger must cite SOCO's OWN identification source.
    from build_dof_ledger import (  # noqa: PLC0415
        _COAL_WARM_COMMITTED_SOURCE,
        _COAL_WARM_COMMITTED_SOURCE_DEFAULT,
    )

    src = _COAL_WARM_COMMITTED_SOURCE.get("SOCO")
    if not src or src == _COAL_WARM_COMMITTED_SOURCE_DEFAULT:
        raise SystemExit(
            "build_dof_ledger has no SOCO-specific identification source for "
            "coal_warm_committed — the ledger would publish another ISO's "
            "evidence as SOCO's (rule 25 [R-ISO-SCOPE])"
        )
    if "MISO" in src or "miso-" in src:
        raise SystemExit(
            "SOCO's coal_warm_committed identification source cites MISO — "
            "rule 25 [R-ISO-SCOPE] / 28(d): no verdict transfers"
        )


def _retag(att: dict, sc: dict, scope: dict) -> None:
    """Re-tag the offer-curve DOF entries and carry SOCO-55's measured basis.

    ``build_dof_ledger.py`` tags ``offer_curve_by_group`` and
    ``offer_curve_smoothing`` ``residual`` by default, because on every other ISO
    they ARE the rule-1 price-tuning surface. On SOCO they cannot be: the identity
    1.0 on all four bands is not a tuned value, and there is no price residual in
    existence to have tuned it against. :func:`_verify` has already raised if any
    band is off the identity.

    THIS LANE ADDS ONE ENTRY AND NO DEGREE OF FREEDOM. ``coal_warm_committed`` is
    a BOOLEAN GATE over a PHYSICAL PREDICATE, with no value, threshold, year
    scope or class scope to choose — ``build_dof_ledger`` already ships it
    ``measured-physical`` with ``n_scalars=0`` — so ``n_residual`` is unchanged
    at 1 (the inherited ``wefor_multiplier``).
    """
    fp = att.get("free_parameters")
    if not fp:
        raise SystemExit(
            "free_parameters absent — run "
            f"`PYTHONPATH=src python3 scripts/build_dof_ledger.py {BUNDLE} --iso SOCO` first"
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
                "machine-verified by gen_soco58_attestation._verify, which raises "
                f"otherwise: the distinct values per band are {bands}. "
                "offer_curve_overrides and offer_curve_deltas are null. The two "
                "non-identity keys, econ_low_share and pct_peaking, are NOT the "
                "authorized channel — rule 1's carve-out excludes structural shares "
                "— and arrive verbatim from the ISO-agnostic GENERIC_BASE_OFFER_CURVE."
            )
            entry.pop("root_cause", None)
        elif entry["name"] == "offer_curve_smoothing":
            entry["identification"] = "measured-physical"
            entry["basis"] = (
                "Unset on this run — both offer_curve_smoothing and curve_smoothing "
                "are null (machine-verified). Nothing was tuned because nothing was set."
            )
            entry.pop("root_cause", None)

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
        "SOCO-58 re-tagged offer_curve_by_group and offer_curve_smoothing from the "
        "builder's default 'residual' to 'measured-physical', on the same "
        "machine-verified identities SOCO-40..57 used and re-verified here by "
        "execution, and CARRIED FORWARD SOCO-55's three measured per-year gas-basis "
        "entries unchanged. "
        "THIS LANE ADDS ONE ENTRY AND NO DEGREE OF FREEDOM. coal_warm_committed is a "
        "BOOLEAN GATE over a PHYSICAL PREDICATE: it removes the P1 "
        "startup-amortization markup from a CAMPD coal bin whose own must-run floor "
        "holds its boiler online. There is no value, threshold, year scope or class "
        "scope to choose — the scope is the predicate 'fuel_type == coal and "
        "must_run_pct > 0', and build_dof_ledger ships the entry measured-physical "
        "with n_scalars=0. "
        f"The predicate is verified BY EXECUTION on this bundle's own committed "
        f"hourlies: it holds at {scope['warm_boiler_predicate_min_pct']}% across all "
        f"{scope['plant_years_checked']} coal plant-years, at must-run load fraction "
        "1.00, so the boiler is never dark when the exempted charge applies. The "
        "SCOPE is verified by execution too: the exemption covers "
        f"{len(scope['exempt_tranches'])} tranches ({scope['exempt_mw']} MW), all "
        f"_committed, with {scope['coal_tranches_paying_but_not_exempted']} coal "
        "tranches paying the markup but not exempted and "
        f"{scope['noncoal_tranches_touched']} non-coal tranches touched — "
        "_verify_scope raises on any drift in either direction. "
        "WHAT IT REMOVES IS NOT THIS LANE'S PARAMETER EITHER: the $100/MW NREL coal "
        "cold start was already on the markup path, and the amortization that turns "
        "it into $100.00/MWh is startup / max(avg P0 run, 1.0 h), a quantity the P0 "
        "solve produces rather than one anybody chose. "
        "coal_warm_committed ships False and is ALREADY in the cache key (it is not "
        "in _CACHE_KEY_OPTIONAL_FIELDS), so arming it re-keys SOCO's configs only and "
        "no peer ISO's key moves. "
        "RULE 25 [R-ISO-SCOPE]: the entry's identification SOURCE is per-ISO and "
        "SOCO's cites SOCO's own measurement. build_dof_ledger.py previously "
        "hardcoded MISO's dispatch forensics for every ISO; that was found in this "
        "lane's phase 0 and repaired in the same PR, and _verify raises if SOCO's "
        "source is missing or cites MISO. "
        "n_residual is UNCHANGED at 1 (the inherited wefor_multiplier), which is the "
        "figure rule 21 [R-DOF] gates on."
    )


def _disclosures(scope: dict) -> dict:
    """SOCO-58 determination basis. The items that cut against the lane lead."""
    return {
        "note": (
            "SOCO-58 determination basis. Everything the run does not establish, at "
            "full magnitude. THE FIRST ITEM IS THE ONE THAT CUTS HARDEST AGAINST THIS "
            "LANE and it is unusual for this desk: unlike SOCO-55, -56 and -57, which "
            "were promoted on runs whose residual got WORSE because the input was "
            "right, this arm is EXPECTED TO IMPROVE the failing criterion. A lever "
            "that improves the fit must clear the same structural bar as one that "
            "does not, and this document states the bar rather than the improvement."
        ),
        "1_THIS_ARM_IMPROVES_THE_FIT_WHICH_IS_A_REASON_FOR_MORE_SCRUTINY_NOT_LESS": (
            "THE HEADLINE CAUTION, STATED AGAINST THE LANE. Rule 1 [R-STRUCT]'s "
            "discipline is usually exercised in one direction — keeping a structurally "
            "correct mechanism whose residual moved the wrong way. This lane runs the "
            "OTHER way: the arm is expected to flip the failing C4 2024 coal row to "
            "PASS. That is precisely the situation in which a fitted mechanism would "
            "be easiest to mistake for a real one. "
            "THE BAR IT CLEARS IS NOT THE RESIDUAL. (a) The cost being removed is "
            "FICTITIOUS, measured rather than argued: the warm-boiler predicate — in "
            f"every hour a plant's _committed tranche carries capacity, that plant's "
            f"_mustrun tranche is generating — holds at "
            f"{scope['warm_boiler_predicate_min_pct']}% across all "
            f"{scope['plant_years_checked']} coal plant-years checked, at must-run "
            "load fraction 1.00. The boiler is NEVER dark when the charge applies. "
            "(b) The charge's MAGNITUDE is not a physical quantity either: it is "
            "$100/MW / max(avg P0 run length, 1.0 h), which SATURATES at exactly "
            "$100.00/MWh when a tranche has zero P0 runs and collapses to $0.13 when "
            "it has many. Inverting it gives implied P0 run lengths of 1.0 h at four "
            "plants in 2024 against 769.2 h at plant 6002 in 2025 — the markup is "
            "ANTI-CORRELATED with the year's need for coal, so its year-to-year "
            "variation is a P0 FEEDBACK ARTIFACT and not a driver. That is the mirror "
            "image of the v2 circularity model/commitment.py::_amortized's own "
            "docstring records being removed for fast starts; coal carries no "
            "fast_start_run_hours basis, so coal still runs on v2 — in the direction "
            "that self-REINFORCES. "
            "IF THE ONLY ARGUMENT FOR THIS ARM WERE THAT C4 2024 COAL FLIPS, IT WOULD "
            "NOT BE TAKEN."
        ),
        "2_IT_DEEPENS_AN_ALREADY_SHORT_CLASS_AND_MAY_COST_A_NEW_C1_ROW": (
            "THE SECOND THING AGAINST THIS LANE, PRE-REGISTERED AS P4 BEFORE THE "
            "SOLVE. Coal correctly under-cutting SOCO's gas steam takes energy from "
            "ST_GAS, which is ALREADY -6.47 TWh short in 2023 and -5.75 in 2024. The "
            "2023 ST_GAS row is the thinnest passing row on the whole run (0.71 TWh "
            "and 0.29 pp of margin) and it moves in the direction the arm pushes; "
            "PRECOMMIT-soco-58 §7 P4 put the chance of it crossing to FAIL at ~40 % "
            "and refused to predict which way. "
            "ITS CAUSE IS SEPARATELY KNOWN AND IS NOT THIS ARM. SOCO-54 §4 measured a "
            "$1.0-1.7/MMBtu delivered-fuel separation between SOCO's gas steam "
            "($3.39-3.76/MMBtu) and its combustion turbines ($2.06-2.40) — the "
            "unmodelled within-footprint gas dispersion of SOCO-12 §4, for which no "
            "free public daily index exists at SONAT or Transco/Dalton. Coal "
            "under-cutting an over-priced steam fleet does not create that defect; it "
            "exposes it, which is the SOCO-57 pattern exactly. It is ROUTED, not "
            "absorbed."
        ),
        "3_IT_MAKES_2025_COAL_WORSE_AND_2025_IS_UNGATED_WHICH_IS_NOT_A_DEFENCE": (
            "2025 COAL_PRB is ALREADY +3.251 TWh OVER its actual, and this arm pushes "
            "it further over. Every 2025 C1 row is SKIPPED on the preliminary EIA-923 "
            "vintage and the C2 2025 coal family reads a SKIPPED +13.8 % diagnostic, "
            "so no gate registers the cost — THAT IS A FACT ABOUT THE VINTAGE, NOT AN "
            "ARGUMENT THAT THE COST IS ABSENT. It is reported here at full magnitude "
            "for that reason. "
            "ITS CAUSE IS MEASURED AND ROUTED: SOCO-53b's 2025 hydro input hole — "
            "0.327 TWh modelled against 6.012 measured — and coal is what backfills "
            "it. Correcting hydro would push 2025 coal DOWN by up to ~5.7 TWh, which "
            "is the direction that would absorb this arm's 2025 overshoot. It is NOT "
            "armed here: rule 19 [R-ONE-MECH] forbids two mechanisms on one "
            "phenomenon in one lane, and it is this lane's NAMED SUCCESSOR."
        ),
        "4_WHAT_THE_EXEMPTION_DOES_NOT_REACH": (
            "The arm does NOT close the coal gap and does not claim to. Scherer (703) "
            "and Gaston (26) do not move even after the exemption, because their "
            "de-marked-up committed bids are $57.58 and $57.54 against a $28.27 median "
            "price — Scherer's delivered coal is $5.10/MMBtu against Miller's $2.10. "
            "That is a per-plant coal fuel-price question this lane does not touch. "
            "Barry (3) carries the fleet's largest per-plant coal OVER-run, 3.48x its "
            "own actual in 2024 and 5.67x in 2025, and the arm does not touch that "
            "either; its fleet row still follows a stale EIA-860 that files unit 4 as "
            "Conventional Steam Coal while CAMPD measures it burning Pipeline Natural "
            "Gas (SOCO-56 §3 resolved the OUTAGE routing in favour of CAMPD; the FLEET "
            "row is untouched)."
        ),
        "5_THE_SAME_ARITHMETIC_APPLIES_TO_CT_PEAKER_AND_IS_DELIBERATELY_NOT_TAKEN": (
            "Ten CT_PEAKER plants carry a +$20.00/MWh committed markup on implied "
            "1.0 h P0 runs — the identical saturation. It is NOT extended to them, for "
            "two independent reasons, and the one that binds is the physical one: a "
            "combustion turbine with no must-run floor GENUINELY DOES cold-start, so "
            "no warm-boiler argument exists for it. (The other, which is NOT the "
            "reason, is that CT_PEAKER is already +2.97 TWh over in 2024 so the "
            "direction would be wrong — recorded so the scoping reads as physics "
            "rather than convenience.)"
        ),
        "6_THE_GOVERNANCE_READING_IS_SURFACED_NOT_SETTLED": (
            "coal_warm_committed is not a matrix row: the base matrix registers it "
            "INSIDE the tranche_startup_amortization row's def, as a sub-scalar of "
            "that family (rule 28(c), xiso-3 census). SOCO's cell for that family is "
            "G — GOVERNANCE-REFUSED EX ANTE, NO REOPEN CONDITION (SOCO-53), on the "
            "ground that the mechanism puts start costs INTO A CLEARING PRICE and "
            "SOCO has none. "
            "THIS LANE'S READING, STATED SO IT CAN BE OVERRULED: the family's two "
            "class-scoped gates have OPPOSITE POLARITY. gas_st_startup_cost OFF means "
            "NO markup (SOCO's ST_GAS committed markup measures at exactly -0.000, "
            "confirming the family is genuinely off there). coal_warm_committed OFF "
            "means the markup IS APPLIED (SOCO's coal committed markup measures at "
            "+$100.00). So arming the exemption ENFORCES the G cell's own position "
            "rather than reopening it — and SOCO-53's note that 'with "
            "tranche_startup_amortization off the CT_PEAKER econ and peak tranches "
            "carry ZERO start cost' rested on a premise this lane's measurement "
            "corrects: the family is NOT off for SOCO's coal, it is ON BY DEFAULT, and "
            "no master gate turns it off. "
            "THE CELL IS NOT FLIPPED. tranche_startup_amortization stays G for SOCO; "
            "only its evidence text is extended. The boundary is genuinely ambiguous "
            "and is put to the owner in the RESULT rather than settled by this lane."
        ),
        "7_INHERITED_AND_UNTOUCHED": (
            "Carried unchanged from SOCO-57 §9: the over-dispatched CC tail (Tenaska "
            "Lindsay Hill 2.060x, Central Alabama 1.455x, Ratcliffe 1.431x, E B Harris "
            "1.404x), on heat rates now MEASURED correct to within +/-$0.30/MWh, so "
            "heat rate is excluded as their cause and no admissible input names it; "
            "the two boundary-refused CC plants (533 McWilliams, 7946 Wansley U9), "
            "whose steam turbines CAMPD does not meter; the ST_GAS denominator "
            "(unit_outage_extract_basis_share), bounded at <= 0.0071 TWh; the tranche "
            "half of campd_per_unit_attribution, still a live landmine because the "
            "flag is ON for SOCO while thermal_tranche_csv_for_iso returns the "
            "INCUMBENT artifact; and derive_parasitic_load.py, never run for SOCO's "
            "coal or gas-steam classes. "
            "AND THE DEFINING CONSTRAINT, UNCHANGED: SOCO HAS NO PRICE BENCHMARK AND "
            "NEVER WILL. C3a / C3b / C3c are UNSCORABLE, not failed, in every year. "
            "This determination certifies NO price level, shape or tail."
        ),
    }


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-58 bundle."""
    att_path = BUNDLE / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    _verify(sc)
    years = sorted(
        int(y) for y in json.loads((BUNDLE / "meta.json").read_text())["years"]
    )
    scope = _verify_scope(years)
    print(f"scope verification: {json.dumps(scope, indent=1)}")

    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-58 (lane). ONE mechanism moves against the incumbent keeper "
            "2026-09-20-soco57-measured-cc-heat: ScenarioConfig.coal_warm_committed, "
            "turned ON. Everything else is that keeper's recipe unchanged, "
            "machine-verified by _verify — including SOCO-54's "
            "gas_plant_monthly_fuel_pricing=False, SOCO-55's "
            "gas_basis_differential_measured_by_year=True, SOCO-56's "
            "campd_per_unit_attribution=True and SOCO-57's "
            "measured_cc_heat_rates=True, without which this is not a single-delta "
            "arm off that keeper. "
            "THE CLAIM IS ABOUT A COST THAT IS NOT BEING INCURRED, NOT ABOUT THE "
            "RESIDUAL. model/commitment.py::compute_monthly_markup adds a P1 "
            "startup-amortization markup of startup_cost / max(avg P0 run length, "
            "1.0 h). SOCO's six coal _committed tranches each carry an NREL $100/MW "
            "cold start, and in 2024 four of the six had ZERO P0 runs, so the "
            "amortization hit its floor and the markup was EXACTLY $100.00/MWh — "
            "pricing those bands at $140.04 / $141.90 / $157.58 / $176.96 into a "
            "market whose median clearing price that year was $28.27/MWh, and leaving "
            "20.73 TWh of available committed coal capacity producing 0.909 TWh. That "
            "is the run-97b inversion model/commitment.py's own warm-boiler comment "
            "names: 'turning the design's cheap base band into a near-peak band'. "
            "THE PHYSICS PREDICATE IS MEASURED, NOT ASSERTED. In every hour in which a "
            "plant's _committed tranche carries capacity, that plant's _mustrun "
            "tranche is generating at load fraction 1.00 — verified here by execution "
            f"on the bundle's own committed hourlies at "
            f"{scope['warm_boiler_predicate_min_pct']}% across all "
            f"{scope['plant_years_checked']} coal plant-years. The boiler is never "
            "dark when the charge applies, so dispatching the committed band is an "
            "output ramp on a hot unit and the cold start is a cost the plant does not "
            "incur. A vertically-integrated, cost-based utility does not decline to "
            "raise output on an already-synchronised boiler because of a start it is "
            "not paying for. "
            "THE STRUCTURAL SIGNATURE, WHICH IS WHY THIS IS A MECHANISM AND NOT A FIT. "
            "The markup's magnitude is not a physical quantity: it SATURATES at "
            "exactly $100.00/MWh when a tranche has zero P0 runs and collapses toward "
            "zero when it has many. Inverting it gives each tranche's own implied P0 "
            "run length — 1.0 h at four plants in 2024 against 769.2 h at plant 6002 "
            "in 2025 — so the charge is ANTI-CORRELATED with the year's need for coal: "
            "a self-reinforcing lockout that bites hardest in the lowest-price year. "
            "It is the mirror of the v2 circularity _amortized's own docstring records "
            "being removed for fast starts ('too-cheap offers -> long P0 blocks -> ~0 "
            "markup -> the lever self-disables'); coal carries no fast_start_run_hours "
            "basis, so coal still runs on v2, in the self-REINFORCING direction. "
            "RULE 25 [R-ISO-SCOPE] / 28(d): NO VERDICT TRANSFERS. MISO's keeper arms "
            "this same gate and that transfers NOTHING. Every number above is SOCO's "
            "own, measured in this lane on SOCO's own committed keeper hourlies. A "
            "rule-25 defect in the published record was found in phase 0 and repaired "
            "in the same PR: build_dof_ledger.py hardcoded MISO's dispatch forensics "
            "as this field's identification source for EVERY ISO, so SOCO arming it "
            "would have published MISO's evidence as SOCO's; the source is now "
            "per-ISO, SOCO's cites its own measurement, and an unlisted ISO gets an "
            "explicit NOT IDENTIFIED FOR THIS ISO. _verify raises if SOCO's entry is "
            "missing or cites MISO. "
            "RULE 13 [R-MEASURED]: nothing measured is fed back. The exemption removes "
            "a modelled charge; it adds no input, pins no actual, and regenerates "
            "identically for a forward year, where the same must-run floors produce "
            "the same predicate. "
            "RULE 19 [R-ONE-MECH]: ONE seam, ONE call site (pipeline/solve.py:518). "
            "The exemption's scope is verified BY EXECUTION to be exactly the set of "
            f"tranches that pay the markup — {scope['exempt_tranches']} "
            f"({scope['exempt_mw']} MW), with "
            f"{scope['coal_tranches_paying_but_not_exempted']} coal tranches paying "
            f"but not exempted and {scope['noncoal_tranches_touched']} non-coal "
            "tranches touched. Every take-or-pay limb, coal_fuel_inventory and "
            "committed_ramp_spread are asserted OFF so no second mechanism acts on the "
            "coal committed band, and gas_st_startup_cost is asserted OFF because "
            "arming it would ADD start costs to a footprint with no clearing price. "
            "P0 IS BYTE-IDENTICAL to the control — P0 solves on mc_base and mc_base "
            "does not move — so the displaced classes' own P0 run lengths, and "
            "therefore their own markups, are unchanged. "
            "THE FLEET GRAINS READ ZERO AND THAT IS THE CORRECT SIGNATURE. Because the "
            "mechanism lives entirely at the P0->P1 seam, fuel_prices, mc_base, pmax, "
            "availability and heat_rate all move by EXACTLY 0.000000000000 with zero "
            "rows moved. That is the INVERSE of SOCO-57 §4's wiring defect, where "
            "all-grains-zero meant an arm that never armed; here it is required, and "
            "the resolved-config assertion in _verify is the only thing that "
            "distinguishes an armed leg from a control. "
            "RULE 21 [R-DOF] / 24 [R-REGISTRY]: ZERO free parameters added. "
            "coal_warm_committed is an existing registered ScenarioConfig boolean "
            "(scenarios.py:12202) with no scalar of its own; build_dof_ledger "
            "classifies it measured-physical with n_scalars=0. It is already in the "
            "cache key, so arming it re-keys SOCO's configs ONLY and no peer ISO's key "
            "moves. n_residual is unchanged at 1. "
            "GATE G17 — SOCO HAS NO PRICE BENCHMARK AND GAINS NONE. Every "
            "offer_curve_by_group band is exactly 1.0 on all 13 groups, "
            "offer_curve_overrides / offer_curve_deltas / smoothing are null, and "
            "AUTHORIZED PRICE TUNING IS DECLARED NONE — no authorized_price_tuning key "
            "is written, because with no price benchmark in existence the rule 1 "
            "[R-STRUCT] channel is unreachable rather than merely unused. "
            "WHAT THIS LANE DOES NOT CLAIM, stated because it cuts against it: UNLIKE "
            "SOCO-55, -56 AND -57, THIS ARM IS EXPECTED TO IMPROVE THE FAILING "
            "CRITERION, which is a reason for more scrutiny and not less; it deepens "
            "ST_GAS, an already-short class whose 2023 row is the thinnest passing row "
            "on the run and may cross to FAIL; it pushes 2025 coal further above an "
            "actual it already exceeds, where only the preliminary EIA-923 vintage "
            "keeps the cost ungated; it does NOT close the coal gap, since Scherer and "
            "Gaston stay out of merit on a $5.10-vs-$2.10/MMBtu delivered-coal "
            "separation it does not touch; and the same $100-over-1-hour arithmetic "
            "applies to ten CT_PEAKER committed tranches, which are deliberately NOT "
            "exempted because a combustion turbine without a must-run floor genuinely "
            "does cold-start."
        ),
    }
    att["disclosures"] = _disclosures(scope)
    _retag(att, sc, scope)
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
