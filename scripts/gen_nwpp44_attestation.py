"""Emit the NWPP-44 calibration attestation for ``results/calibration/nwpp44_takeorpay_reg``.

NWPP-44 is NWPP-42's frozen recipe plus **exactly two** solve-affecting fields,
both booleans over measured inputs:

* ``coal_takeorpay_from_data`` — each coal plant's own MEASURED EIA-923
  Schedule-5 contracted share, in place of the uniform assumed 100 %-sunk first
  tranche (``data/raw/_processed-legacy/coal_takeorpay_NWPP.csv``, derived by
  nwpp-43 from the committed ``data/raw/coal-receipts/`` corpus by the identical
  quantity-weighted construction the other seven ISOs' tables use);
* ``coal_committed_takeorpay_regulated`` — the committed-band limb of the same
  contract, scoped by the plant's published EIA-860 ``Regulatory Status`` (RE).

**SCOPE WAS FIXED EX ANTE BY OWNER RULING, NOT BY THE RESIDUAL** (2026-09-20, on
``PRECOMMIT-nwpp-43`` §7): Option B, ALL regulated coal. So
``coal_prb_committed_dispatchable`` is NOT armed and no rank carve-out is
applied — and the ruling went to the option that is HARDER on this lane's own
gate, because NWPP's measured conduct does not discriminate between ranks
(p25→median CF spread ~9–20 pts in both) and picking the carve-out that makes a
gate pass is the fitted-mechanism selection rule 1 ``[R-STRUCT]`` forbids.

**ZERO FREE PARAMETERS** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``). Neither
arm is a magnitude: the discount is the plant's own measured tonnage share and
the scope is a published boolean. Neither was swept. Both regenerate for a
forward year from forward filings, so rule 13 ``[R-MEASURED]``'s forward test is
met.

**The run is three year-isolated shards** (rule 36 ``[R-YEAR-ISOLATION]``)
composed by the parent, then regenerated through ``--reuse-solved`` at the legs'
own solve commit so the bundle carries its shared input frames. **Zero LP was
spent on the regeneration** and the composite is byte-identical to the legs on
every scored quantity (verified: COAL_BIT 18.264 / 12.381 / 11.440 and hydro
106.872 / 107.879 / 113.077 in 2023 / 2024 / 2025).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp44_takeorpay_reg"

#: Armed by this lane. Both must read True or the attestation refuses.
_ARMED = ("coal_takeorpay_from_data", "coal_committed_takeorpay_regulated")

#: Deliberately NOT armed. A True here means the owner's Option B scope drifted
#: into a rank carve-out, which would make the run a different experiment.
_REFUSED = (
    "coal_prb_committed_dispatchable",
    "coal_committed_takeorpay_sunk_fixed",
    "coal_bit_committed_takeorpay",
    "coal_committed_takeorpay_all",
)

#: Inherited from NWPP-42 and unchanged; re-checked so a silent drift cannot
#: ride this attestation.
_INHERITED = {
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
        if sc.get(f) is not False:
            bad.append(f"{f} = {sc.get(f)!r}, expected False (owner Option B scope)")
    for f, want in _INHERITED.items():
        if sc.get(f) != want:
            bad.append(
                f"{f} = {sc.get(f)!r}, expected {want!r} (inherited from NWPP-42)"
            )
    if bad:
        raise SystemExit(
            "gen_nwpp44_attestation refuses this bundle:\n  " + "\n  ".join(bad)
        )
    return {
        "scenario_config": sc,
        "meta": json.loads((bundle / "meta.json").read_text()),
    }


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-44 attestation (after seeding the canonical DOF ledger)."""
    _check_recipe(bundle)

    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"
    att["lane"] = "NWPP-44"
    att["bundle"] = bundle.name

    att["switches"] = {
        "coal_takeorpay_from_data": {
            "value": True,
            "where": (
                "ScenarioConfig.coal_takeorpay_from_data, set for NWPP in "
                "pipeline/backcast_config.py; consumed by "
                "data/fleet/assembly.campd_tranche_fuel_frac via takeorpay_by_plant"
            ),
            "identification": "measured-physical",
            "source": (
                "data/raw/_processed-legacy/coal_takeorpay_NWPP.csv — each plant's "
                "own quantity-weighted EIA-923 Schedule-5 contracted share. 13 of 17 "
                "NWPP coal plants classify; the fleet is 94 % contract on tonnage "
                "(10 plants at 100 %), with North Valmy 0.5611, Hardin 0.7612 and "
                "TS Power 0.9047 the spot-heavy counter-examples."
            ),
        },
        "coal_committed_takeorpay_regulated": {
            "value": True,
            "where": (
                "ScenarioConfig.coal_committed_takeorpay_regulated, set for NWPP in "
                "pipeline/backcast_config.py; scope from "
                "data/fleet/eia860.eia860_selfcommit_scope_plants()"
            ),
            "identification": "measured-physical",
            "source": (
                "EIA-860 Regulatory Status == RE, read at the run's active vintage. "
                "Scoped by OWNERSHIP, never by coal rank (owner ruling 2026-09-20, "
                "Option B). Structural driver: COAL_BIT, the deficit class, is 81.7 % "
                "regulated (2,998 of 3,668 MW) against 44.3 % for PRB."
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
            "levers_trace_to_measured_input: both arms are booleans over published "
            "measured data — EIA-923 Schedule-5 tonnage and the EIA-860 Regulatory "
            "Status boolean. Neither is a magnitude and neither was swept. "
            "no_fit_to_price_residuals: NWPP is PRICE UNSCORED (rubric v3.8, owner "
            "card S2) — C3a/b/c are not scored in any year, this lane did not look at "
            "price, and no offer_curve_by_group band multiplier is touched, so the "
            "rule 1 [R-STRUCT] authorized-tuning channel is NOT used and "
            "authorized_price_tuning is declared NONE. no_pinning_to_actuals: no "
            "measured outcome enters the solve; the contract share and the regulatory "
            "boolean are INPUTS that regenerate for a forward year. "
            "outage_filter_exogenous_net_load: outage_source='historic', the CAMPD "
            "measured availability overlay, unchanged from NWPP-42."
        ),
    }

    # Nothing is ledgered as an exception: the arm carries no caveat, no
    # authorized price tuning and no waived gate. The C1 regression is a
    # REPORTED gate failure, not a ledgered exception — it is scored as a FAIL
    # and shown as one, which is the opposite of being excepted from the gate.
    att["exceptions"] = []

    disc = att.setdefault("disclosures", {})
    disc["kill_condition_pre_registered_and_survived"] = (
        "Pre-registered VERBATIM in PRECOMMIT-nwpp-44 §7, carried unchanged from "
        "NWPP-43 §6, and reported at full magnitude. INERT limb: 2024 COAL_BIT rising "
        "< 2.0 TWh would have made the verdict I. It rose +4.898 TWh (7.482 -> 12.381), "
        "so the limb did not fire. OVERSHOOT limb (a): 2024 COAL_BIT > 14.83 TWh would "
        "have made it R. It reads 12.381 against an actual 12.832 — 0.451 UNDER, not "
        "over. OVERSHOOT limb (b): any C1 COAL row outside its band in any year would "
        "have made it R. All coal rows are inside; C1's single failing row is "
        "2023 CC_REGULAR, a GAS row (see c1_regression_at_full_magnitude). The "
        "condition therefore does not fire in either direction. IT WAS NOT RELAXED: "
        "the PRECOMMIT's own zero-LP measurement said the overshoot limb was out of "
        "reach and the INERT limb was the live risk, and the condition was carried "
        "verbatim anyway rather than re-tuned once that was known."
    )
    disc["c1_regression_at_full_magnitude"] = (
        "THE COST OF THIS ARM, STATED AS A REGRESSION AND NOT SOFTENED. C1 fuel-mix "
        "goes PASS (keeper) -> FAIL (arm) on ONE row: 2023 CC_REGULAR, -8.22 TWh / "
        "-2.3 pp, volume out of band. C1 is LOAD-BEARING. The row is not a surprise: "
        "PRECOMMIT-nwpp-44 §6.2 named CC_REGULAR before any solve as the row this arm "
        "could push out of band from the other side, because coal displacing gas is "
        "the mechanism's intended effect and CC_REGULAR is what absorbs it. 17 of 18 "
        "C1 rows pass. The arm is promoted, if it is promoted, WITH this regression on "
        "the record, under the owner's standing instruction that structural gains may "
        "justify gate regressions — not because the regression is small."
    )
    disc["c4_the_lane_goal_improves_in_every_year"] = (
        "C4 coal, the failure this lane was chartered to close, improves on BOTH "
        "metrics in ALL THREE years: r 0.570 -> 0.605 (2023), 0.559 -> 0.595 (2024), "
        "0.524 -> 0.610 (2025); NRMSE 0.292 -> 0.260, 0.387 -> 0.246, 0.408 -> 0.284. "
        "NRMSE is now INSIDE the 0.30 gate in all three years, where the keeper cleared "
        "only 2023. C4 nonetheless still FAILS, because r remains below the 0.70 floor "
        "in every year. Reported as a FAIL, not as a near-miss."
    )
    disc["coal_volume_error_falls_57_percent"] = (
        "Coal total against actual (42.27 / 38.30 / 42.26 TWh): keeper -0.721 / "
        "-10.910 / -13.943, arm +2.028 / -1.587 / -7.251. Sum of absolute error "
        "25.574 -> 10.866 TWh. 2024 and 2025 improve substantially; 2023 moves from "
        "0.721 under to 2.028 OVER, which is the pre-registered cost."
    )
    disc["dispatch_response_is_confined_to_the_intended_seam"] = (
        "The offer delta moves 13 LP rows of 641-646 and ZERO non-coal rows, with "
        "|delta pmax| = 0.000000 MW, identical in all three years. In dispatch, coal "
        "displaces gas ONE-FOR-ONE (2025: coal +6.692 TWh against gas -6.694) while "
        "hydro, nuclear, wind, solar, biomass and OTHER are unchanged to 0.000 TWh and "
        "the system total is conserved to 0.003 TWh. The arm is TWO-SIDED and is not a "
        "subsidy: the spot-heavy plants' must-run band gets DEARER (North Valmy "
        "$4.50 -> $27.47/MWh on its measured 0.5611 share, leaving the money in 6,600 "
        "hours of 2024; TS Power $4.50 -> $8.99)."
    )
    disc["what_it_does_not_close"] = (
        "Stated at the gate, not absorbed. This arm does NOT build the rising coal "
        "offer curve that NWPP-43 §4.1 diagnosed as the C4 root cause. It ENLARGES the "
        "cheap block — _mustrun and _committed collapse to one price at every regulated "
        "contracted plant — and leaves the econlo/econhi/peak shelf where it was, "
        "within $0.51/MWh of itself. If C4 improves it is because coal's volume and its "
        "gas-price-independence improve, NOT because the stack started rising. That "
        "defect remains open and is not closed by this run. The miso-96 objection to "
        "discounting the committed band (a take-or-pay contract is an obligation over "
        "an accounting period, not a per-hour price) is ANSWERED in PRECOMMIT §3 on the "
        "ground that this limb's driver is REGULATORY CONDUCT rather than contract "
        "accounting — but where miso-96 lands (the discounted committed band binds in "
        "all 8760 h with no window) is recorded there rather than claimed away."
    )
    disc["solver_and_environment"] = (
        "highspy 1.15.1 in the shard containers against 1.14.0 in the NWPP-42 keeper. "
        "Unpinnable from this lane and disclosed rather than glossed: the arm's effects "
        "are 1.5-6.7 TWh, far above any plausible solver-version noise, so it does not "
        "threaten the readings — but it is on the record. Separately, 2024's P1 ran "
        "11,600 s against its own P0's 1,400 s (8.3x), in the year this arm flips the "
        "merit order hardest; that is a real observation about the warm-started P1 and "
        "is routed, not absorbed."
    )
    return att


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    args = ap.parse_args()
    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att.get("free_parameters", {})
    print(f"wrote {out}")
    print(f"  DOF ledger: {len(fp.get('entries', []))} entries")
    print("  governance: 4/4 assertions true; authorized_price_tuning = NONE")
    print("  arm: coal_takeorpay_from_data + coal_committed_takeorpay_regulated")
    print("  refused (owner Option B): coal_prb_committed_dispatchable = False")


if __name__ == "__main__":
    main()
