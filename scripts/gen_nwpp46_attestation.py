"""Emit the NWPP-46 calibration attestation for ``results/calibration/nwpp46_hydroenv_span``.

NWPP-46 is NWPP-44's frozen recipe plus **exactly two** solve-affecting fields,
which are the two mirrored halves of ONE mechanism and are never armed apart:

* ``hydro_dispatch_envelope`` (caiso-72) — cap the conventional-hydro fleet's
  hourly dispatch at the measured per-(month x hour-of-day) p95 of NWPP's OWN
  EIA-930 ``NG: WAT`` series: the head/flow/scheduling deliverability ceiling
  the nameplate ``pmax`` bound ignores;
* ``hydro_min_flow_floor`` (caiso-124) — hold each plant at a MONTH-CONSTANT
  pro-rata share of the fleet's own measured monthly Q95 sustained level: the
  run-of-river inflow that cannot be stored plus the environmental / FERC
  licence minimum releases the budget LP's energy-only cap ignores.

**ZERO FREE PARAMETERS** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``), and the
floor adds none on top of the ceiling: ``HYDRO_MIN_FLOW_PERCENTILE`` is defined
in ``constants.py`` as ``100.0 - HYDRO_ENVELOPE_PERCENTILE``, so the two-sided
envelope is identified by the ONE percentile the ceiling already carries. Read
as an exceedance level the floor is Q95, the standard hydrological low-flow
index environmental / FERC minimum-flow conditions are themselves written
against. Neither half is a magnitude, neither was swept, and NO code changed:
both are existing ``ScenarioConfig`` fields reached from the calibration CLI.

**RULE 25 [R-ISO-SCOPE]: NOTHING IS TRANSFERRED FROM CAISO.** The envelope and
the floor are built from NWPP's own meter; the percentile is the shared
structural convention in ``constants.py``, not an ISO-fitted number.

**THE LANE RE-DIAGNOSED ITS OWN CHARTER, ON MEASUREMENT** (PRECOMMIT §§1-4).
It was chartered to close C4 on the coal offer stack's vertical extent. NWPP's
own data falsified that: per plant ``econlo == econhi == peak`` EXACTLY (the
``$0.51/MWh`` in the record is a fleet MIX artifact), NWPP's own CAMPD meters
only a 10.4 % ladder across the dispatchable range, and three of five NWPP
zones carry exactly TWELVE distinct prices per YEAR — one per month — so no
coal offer ladder could be anything but inert. The re-routed mechanism is the
one the measurement names.

**The run is three year-isolated shards** (rule 36 ``[R-YEAR-ISOLATION]``)
solved through ``replay_keeper.py --set`` against the keeper's own
``meta.json`` and composed by the parent at zero LP.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp46_hydroenv_span"

#: Armed by this lane. Both must read True or the attestation refuses — they are
#: two halves of one mechanism and arming one alone is a different experiment.
_ARMED = ("hydro_dispatch_envelope", "hydro_min_flow_floor")

#: Deliberately NOT armed. Each is a SEPARATE identified object in the hydro
#: family; a True here means the one-mechanism scope (rule 19) drifted.
_REFUSED = (
    "hydro_ror_split",
    "hydro_budget_period_by_instrument",
    "hydro_budget_nameplate_aware",
)

#: Inherited from NWPP-44 and unchanged; re-checked so a silent drift cannot
#: ride this attestation. hydro_cascade_coupling is the one most at risk: it
#: travels the same prb_overrides channel the arm is applied through.
_INHERITED = {
    "hydro_cascade_coupling": True,
    "coal_takeorpay_from_data": True,
    "coal_committed_takeorpay_regulated": True,
    "measured_coal_heat_rates": True,
    "coal_prb_proxy_own_iso": True,
    "coal_prb_passthrough_sigmoid": True,
    "coal_prb_passthrough_tiered": True,
    "coal_mustrun_per_plant": True,
    "coal_drop_pof": True,
    "plant_level_fleet": True,
    "use_campd_bins": True,
    "mode": "backcast",
}


def _check_recipe(bundle: Path) -> dict:
    """Re-check the arm and the inherited recipe against the bundle's own config."""
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    bad = []
    for f in _ARMED:
        if sc.get(f) is not True:
            bad.append(f"{f} = {sc.get(f)!r}, expected True (this lane's arm)")
    for f in _REFUSED:
        if sc.get(f) not in (False, None):
            bad.append(
                f"{f} = {sc.get(f)!r}, expected off (rule 19 one-mechanism scope)"
            )
    for f, want in _INHERITED.items():
        if sc.get(f) != want:
            bad.append(
                f"{f} = {sc.get(f)!r}, expected {want!r} (inherited from NWPP-44)"
            )
    if bad:
        raise SystemExit(
            "gen_nwpp46_attestation refuses this bundle:\n  " + "\n  ".join(bad)
        )
    return {
        "scenario_config": sc,
        "meta": json.loads((bundle / "meta.json").read_text()),
    }


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-46 attestation (after seeding the canonical DOF ledger)."""
    _check_recipe(bundle)
    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"
    att["lane"] = "NWPP-46"
    att["bundle"] = bundle.name

    att["switches"] = {
        "hydro_dispatch_envelope": {
            "value": True,
            "where": (
                "ScenarioConfig.hydro_dispatch_envelope, armed from the calibration "
                "CLI (--hydro-dispatch-envelope) through the generic prb_overrides "
                "channel; consumed by scripts/run_calibration.py via "
                "data.eia930.envelopes.measured_hydro_hourly_envelope -> the LP's "
                "hydro_envelope_mw row family"
            ),
            "identification": "measured-physical",
            "source": (
                "NWPP's OWN EIA-930 hourly NG:WAT series, per (month x hour-of-day) "
                "p95 (constants.HYDRO_ENVELOPE_PERCENTILE = 95.0, the shared "
                "convention, not an NWPP number). Measured binding: 21.7 / 23.7 / "
                "23.4 % of hours in 2023 / 2024 / 2025, 1.864 / 2.359 / 2.684 TWh "
                "above the ceiling, concentrated on the evening ramp (h16-h22, "
                "29-47 % of those hours) — the perfect-foresight hoarding the "
                "energy-only budget cap permits."
            ),
        },
        "hydro_min_flow_floor": {
            "value": True,
            "where": (
                "ScenarioConfig.hydro_min_flow_floor, armed from the calibration CLI "
                "(--hydro-min-flow-floor) through the same channel; consumed by "
                "data.eia930.envelopes.measured_hydro_min_flow_level -> "
                "data.hydro.allocate_min_flow_floor -> FleetArrays.min_gen, "
                "mechanism id MECH_HYDRO_MIN_FLOW"
            ),
            "identification": "measured-physical",
            "source": (
                "The SAME EIA-930 NG:WAT series, per CALENDAR MONTH, at "
                "constants.HYDRO_MIN_FLOW_PERCENTILE = 100.0 - "
                "HYDRO_ENVELOPE_PERCENTILE = 5.0 — the exact mirror, so the floor "
                "adds ZERO free parameters on top of the ceiling. The bucket is the "
                "month ALONE, never (month x hour-of-day): a floor carrying the "
                "measured diurnal shape would pin dispatch to the measured outcome "
                "(rule 13), while a month-constant level is what a minimum-flow "
                "condition physically is and leaves the LP free to choose WHEN to "
                "generate above it. Measured binding: 10.4 / 12.9 / 14.0 % of hours, "
                "0.866 / 1.185 / 1.526 TWh below the sustained level, concentrated "
                "in the midday solar belly and the overnight shoulder — DISJOINT "
                "from the ceiling's hours, which is the rule-19 evidence that the "
                "two are one reconciled family and not a stack."
            ),
        },
    }

    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "authorized_price_tuning": None,
        "notes": (
            "levers_trace_to_measured_input: both halves are percentile statistics of "
            "NWPP's own published EIA-930 NG:WAT hourly series. Neither is a "
            "magnitude a lane chose; the single percentile is a shared constant and "
            "the floor's is its arithmetic mirror. Neither was swept — the arm was "
            "declared in PRECOMMIT-nwpp-46 §5 with its predicted effect computed "
            "exactly in §6 BEFORE the solve, and the kill condition in §7 was coded "
            "and committed (scripts/probes/_nwpp46_gates.py) before the first leg "
            "landed. no_fit_to_price_residuals: NWPP is PRICE UNSCORED (rubric v3.8, "
            "owner card S2) — C3a/b/c are not scored in any year and no "
            "offer_curve_by_group band multiplier is touched, so the rule 1 "
            "[R-STRUCT] authorized-tuning channel is NOT used and "
            "authorized_price_tuning is declared NONE. The lane DID measure the "
            "model's own price formation (PRECOMMIT §3: three of five zones carry 12 "
            "distinct prices per year), and that is evidence about the model, never a "
            "claim about NWPP's real prices and never a residual tuned against. "
            "no_pinning_to_actuals: the envelope is a CEILING the LP clears below and "
            "the floor is a month-constant LEVEL, so no measured outcome is pinned; "
            "hydro annual energy is unchanged to 0.000 TWh in every year, which is "
            "the direct evidence that this is a shape constraint and not a volume "
            "mechanism. Both regenerate for a forward year from the pooled "
            "HYDRO_CLIMATOLOGY_YEARS percentile and respond to the water year through "
            "the budget they are clipped against, so rule 13's forward test is met. "
            "outage_filter_exogenous_net_load: outage_source='historic', unchanged "
            "from NWPP-44."
        ),
    }

    att["exceptions"] = []

    disc = att.setdefault("disclosures", {})
    disc["kill_condition_pre_registered_and_survived"] = (
        "Pre-registered in PRECOMMIT-nwpp-46 §7 and CODED AND COMMITTED BEFORE THE "
        "FIRST LEG LANDED (scripts/probes/_nwpp46_gates.py, commit 9cd108d9), "
        "deliberately, so it could not be written to fit the numbers. INERT limb: the "
        "hydro amplitude ratio had to fall by >= 0.03 in EVERY year (2023 < 1.11, "
        "2024 < 1.17, 2025 < 1.35). It reads 1.048 / 1.107 / 1.148 against a keeper "
        "1.138 / 1.200 / 1.383 — the limb does not fire. OVERSHOOT (a): below 0.90 in "
        "any year would have made it R; the minimum is 1.048. OVERSHOOT (c): hydro "
        "annual energy moving > 5.0 TWh would have made it R; it moved 0.000 TWh in "
        "every year. OVERSHOOT (b), the C1 COAL rows, is scored on the registered run. "
        "The evaluator SELF-TESTS against the keeper, where it correctly reads I."
    )
    disc["the_prediction_was_made_ex_ante_and_landed"] = (
        "PRECOMMIT §6a predicted the hydro amplitude ratio at 1.05 / 1.10 / 1.16 from "
        "a static clip of the keeper's own hourly hydro. The SOLVE returned 1.048 / "
        "1.107 / 1.148 — within 0.002 / 0.007 / 0.012. §6d predicted C4 r at "
        "0.61-0.66 / 0.60-0.65 / 0.62-0.67 and NRMSE at 0.24-0.28 / 0.23-0.27 / "
        "0.26-0.30; the solve returned r 0.658 / 0.617 / 0.637 and NRMSE 0.244 / "
        "0.240 / 0.276, every one INSIDE the pre-registered band."
    )
    disc["c4_improves_in_every_year_and_STILL_FAILS"] = (
        "C4 coal improves on BOTH metrics in ALL THREE years: r 0.605 -> 0.658, "
        "0.595 -> 0.617, 0.610 -> 0.637; NRMSE 0.260 -> 0.244, 0.246 -> 0.240, "
        "0.284 -> 0.276. The mechanism's own signature moved as claimed: the coal "
        "diurnal amplitude ratio 0.100 -> 0.223, 0.052 -> 0.096, 0.037 -> 0.089, i.e. "
        "coal's peak-to-trough swing roughly DOUBLED in every year. C4 NONETHELESS "
        "STILL FAILS — r remains below the 0.70 floor in all three years, EXACTLY as "
        "PRECOMMIT §6d predicted it would. It is reported as a FAIL, not a near-miss, "
        "and per rule 1 [R-STRUCT] C4 was never the reason to arm this: a head/flow "
        "deliverability ceiling and a licence minimum-flow release are real features "
        "of how this fleet operates."
    )
    disc["the_intra_day_term_does_not_uniformly_improve"] = (
        "REPORTED BECAUSE IT COMPLICATES THE STORY, not smoothed into it. The within-"
        "day correlation r_intra goes 0.218 -> 0.371 in 2023 (a large gain), but "
        "0.376 -> 0.375 in 2024 (flat) and 0.425 -> 0.374 in 2025 (WORSE). So the "
        "amplitude roughly doubled in every year while the intra-day CORRELATION rose "
        "only in 2023; 2024/2025's r gain comes mostly from the daily-mean term "
        "(0.664 -> 0.679, 0.715 -> 0.732) and from amplitude. Getting the size of the "
        "swing right is not the same as getting its hour right, and this arm did the "
        "first more than the second. That is a real limit on what it closed."
    )
    disc["hydro_energy_is_exactly_conserved"] = (
        "Hydro annual energy: 106.872 / 107.879 / 113.077 TWh in BOTH the keeper and "
        "the arm, unchanged to 0.000 TWh. The budget row reallocated every clipped "
        "MWh into hours below the ceiling, which is the direct evidence that the "
        "two-sided envelope is a SHAPE constraint and not a volume mechanism — and it "
        "is why the released duty lands on the thermal classes as a re-shaping rather "
        "than as new energy."
    )
    disc["what_it_does_not_close"] = (
        "Stated at the gate. The model's price is still a near-monthly step function "
        "in the hydro-set zones, and the coal offer stack is still the IDENTITY "
        "(econlo == econhi == peak at every plant, because backcast_config merges "
        "_SPP_OFFER_CURVE for NWPP). PRECOMMIT §2.1 measured the correct ladder from "
        "NWPP's own CAMPD — committed 0.821 / econ_low 0.932 / econ_high 1.004 / peak "
        "1.029 — and this lane deliberately did NOT arm it, because §3 shows it would "
        "be inert against a within-month-constant price. It is routed as a successor "
        "question for AFTER the price acquires intra-day variation, not dismissed. "
        "The NWPP-45 C1 demand-basis gap (-9.645 / -12.144 / -9.107 TWh) is an OPEN "
        "OWNER DECISION and was not touched."
    )
    disc["composer_defect_found_and_fixed_en_route"] = (
        "scripts/probes/_nwpp42_compose_span.py copied the BASE leg's "
        "meta.shared_inputs onto the composite, so a span assembled from year-isolated "
        "shards claimed years [2023,2024,2025] while pointing at SINGLE-YEAR benchmark "
        "frames — the exact sibling of the gas_prices defect nwpp-44 found, one field "
        "along, and it makes the composite unscorable. Caught by "
        "--restore-shared-inputs, which correctly REFUSED rather than re-pointing. "
        "Fixed in the composer (_respan_shared_inputs). Proven safe before adopting: "
        "the three-year frame is the exact row-wise UNION of the per-year leg frames "
        "(every year's slice byte-identical, all three names), and the re-spanned "
        "hashes land on the keeper's own three-year frames. No benchmark was re-based "
        "and --rebuild-benchmark was NOT used."
    )
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
