"""Write the miso-250 bundle's attestation — the measured monthly gas LEVEL arm.

The bundle needs a C6 attestation (an unattested C6 makes C3c FAIL outright
instead of reclassifying to a ledgered CAVEAT under the rule-22 standing rule's
guard (b)), so this is generated AT the promotion and never typed by hand.

Pattern unchanged from ``gen_caiso267_attestation.py`` / ``gen_caiso260_
attestation.py`` (E10): the incumbent keeper's committed attestation is carried
verbatim, ``governance.attested_by`` is re-stamped with THIS bundle's
narrative, and every ``price_tail`` / ``price_mean`` exception magnitude is
RE-MEASURED from this bundle's own scored records rather than copied.
``free_parameters`` is rebuilt afterwards by ``scripts/build_dof_ledger.py``.

The rule-1 ``[R-STRUCT]`` carve-out declaration
(``governance.authorized_price_tuning``) is **carried verbatim from the
keeper**. This arm's own delta touches no band multiplier, but the recipe it
inherits carries the miso-220 x1.10 non-steam offer lift, so the declaration is
still required and C6 fails without it. The single
ScenarioConfig delta against the incumbent keeper is
``gas_electric_power_monthly_level=True``, a measured input carrying ZERO free
parameters (frozen EIA-860 weight table, the EIA 1.036 MMBtu/Mcf heat content,
and two admission conditions declared ex ante in
``market_sim.data.fuel.electric_power`` and never swept).

Usage::

    PYTHONPATH=.:src python scripts/gen_miso250_attestation.py \
        --bundle results/calibration/miso_fuelvintage_A \
        --run-id 2026-09-09-miso-250-ep-gas
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: The incumbent keeper whose attestation is carried (recipe-identical apart
#: from the single armed field).
KEEPER = REPO / "results/calibration/miso248_fullspan_K"

ATTESTED_BY = (
    "miso-250 KEEPER CANDIDATE (2026-09-09): THE MEASURED MONTHLY GAS LEVEL, ARMED ON "
    "THE OWNER'S RULING AND MEASURED INERT. Full span 2023-2025 in ONE invocation and "
    "ONE bundle (rule 16 [R-ALLYEARS]), replayed from the miso-248 keeper recipe with "
    "EXACTLY ONE ScenarioConfig delta: gas_electric_power_monthly_level=True, applied "
    "through the generic prb_overrides channel and recorded verbatim in "
    "run_config.json (rule 24 [R-REGISTRY]). "
    "WHY IT IS ARMED: the owner ruling of 2026-09-09 (handoff ADDENDUM A7, verbatim "
    "'these should be promoted as keepers on both 860 and gas shape counts regardless "
    "of inertness'), which SUPERSEDES miso-249's disposition of 41 minutes earlier "
    "(commit 7577449a 04:44 UTC 'keep BUILT and DEFAULT-OFF'; the ruling is ff3afcf3 "
    "05:25 UTC and explicitly overrides 'the disposition guidance in PROMPT 1-5 and in "
    "A2'). NEVER a residual: no criterion, band or actual entered the decision. "
    "THE ARM IS INERT, REPORTED AT FULL MAGNITUDE AND NOT HIDDEN. Phase 0 (rule 29 "
    "[R-SCREEN] clause (0), zero LP): 100.000% of MISO gas capacity-hours are F923 "
    "PRINT-DERIVED in 2023, 2024 AND 2025 (all 1,609 / 1,616 / 1,614 gas rows), so "
    "apply_plant_monthly_fuel_prices runs AFTER this seam and overwrites every gas "
    "cell; the delivered-gas array moves 0.0 and non-gas fuels move 0.0 in every year, "
    "and the whole pre-LP state (fuel_prices, mc_base, demand, CFs, capacities, every "
    "FleetArrays field) is identical arm-vs-control in all three years. The harness's "
    "power was demonstrated rather than assumed on the same tree: "
    "gas_plant_monthly_fuel_pricing=False moves mc_base 292.467, "
    "coal_plant_monthly_pricing=False 60.855, f923_gas_price_plausibility_screen=False "
    "2730.599. CONFIRMED ON REAL SOLVES: the rule-29 screen (year 2024, named ex ante "
    "in the PRECOMMIT on the mechanism's largest measured footprint -- Jan +1.551 "
    "$/MMBtu vs 2023's +1.000 -- and never on a residual) plus its EARNED control "
    "(clause (b): G-DRIFT found a LIVE hunk) give ARM vs CONTROL both at HEAD = 0 "
    "differing cells across system / class_hourly / class_band_hourly / reserve_family "
    "/ storage, the SAME simplex iteration count 388,398 and the SAME objective "
    "4,777,088,612.6964. THE SEAM DOES FIRE, on the ISO-level _gas_series alone: 2023 "
    "annual 2.8392 -> 3.0187 (max month gap +1.0003 Jan), 2024 2.4893 -> 2.5580 "
    "(+1.5513 Jan), reproducing FINDING-xiso section 3's MISO rows to three decimals; "
    "2025 is BYTE-IDENTICAL, the pre-registered inert-by-coverage check confirmed "
    "(basket 0.400 -- the drop-outs are dominated by LA .238 and MI .147). Every "
    "_gas_series consumer is off on this recipe (coal_prb/bit_passthrough_sigmoid "
    "False, coal_prb_passthrough_tiered False, miso_offer_surface_measured False), and "
    "miso_zonal_gas_basis is a MEAN-ZERO spread orthogonal to a level. "
    "WHAT MOVED AGAINST THE INCUMBENT KEEPER IS HEAD DRIFT, NOT THIS ARM, AND THE "
    "DECOMPOSITION IS EXACT: ARM vs the committed keeper equals CONTROL vs the "
    "committed keeper CELL FOR CELL, so 100% of the deviation is drift and 0% is the "
    "arm. G-DRIFT attributes it to two changes absent from the keeper's tree -- "
    "commit 7934e92c (the Card A retiree parquet, 477 -> 1,094 rows, a data/raw/eia-860 "
    "change the prescribed G-DRIFT path list does not cover) and commit 43edf7b1 "
    "(ercot-261's _PARTIAL_EXIT_WINDOW_START 2023 -> 2019, live here because this "
    "recipe carries partial_plant_exit_carry=True). Measured at zero LP through the "
    "real run_year(fleet_only=True) path on stable unit_ids, they add 171 rows / "
    "3,298.899 MW nameplate to the 2023, 2024 and 2025 fleets at EXACTLY 0.000000000 "
    "effective MW in every hour, 0.0 min_gen, 0.0 pmin, 0 rows removed and every "
    "shared row byte-identical including mc_base -- yet the LP solution still moves "
    "through DEGENERACY (2024: 6,920 of 70,080 price cells, mean -0.008560 $/MWh, max "
    "8.1215, total energy +0.000038%, slack total identical at 19,566.9151 MWh but "
    "4,678.43 MW reallocated between zones, dump 0.0 both). At criterion grain the "
    "drift is visible in 2023 ONLY: C3a +5.2% -> +4.9%, C3b 0.092 -> 0.091, C3c 3h -> "
    "1h; 2024 and 2025 score IDENTICALLY to the incumbent keeper on every criterion. "
    "Rules 1 [R-STRUCT] / 14 [R-ACCURATE]: the widened window is the more accurate "
    "input and stays; the incumbent keeper's committed numbers were simply stale at "
    "HEAD, which this bundle also repairs. "
    "GOVERNANCE: rule 22 [R-HOLDOUT] -- MISO holds NO complete marker, so only 2023, "
    "2024 and 2025 were solved, --holdout-authorized was never passed and no marker "
    "file was touched. Rule 21 [R-DOF] -- the armed field adds ZERO free parameters. "
    "Rule 19 [R-ONE-MECH] -- worked out in writing before the solve (PRECOMMIT 2c): "
    "the per-plant F923 print is a fourth and more-local measured level that "
    "supersedes the state-average monthly, an omission in the seam module's declared "
    "ordering that is REPORTED and recommended for repair, not patched here. "
    "Record: docs/RESULT-miso-fuelvintage-ep-level-2026-09-09.md, "
    "docs/PRECOMMIT-miso-fuelvintage-ep-level-2026-09-09.md."
)

DISCLOSURES = {
    "note": (
        "miso-250 disclosures, reported rather than patched. (a) THE ARM IS INERT IN "
        "DISPATCH and is promoted anyway on the owner's ruling; the inertness is the "
        "headline of the result, not a footnote. (b) MY OWN GATE G-0 FAILED -- the "
        "screen did not reproduce the committed keeper bit-identically -- and that "
        "failure is what earned the control solve under rule 29 [R-SCREEN] clause (b), "
        "exactly as the PRECOMMIT pre-registered it would. The control proved the miss "
        "was 100% HEAD drift and 0% the arm. (c) A CROSS-ISO FINDING THIS LANE DID NOT "
        "SET OUT TO MAKE: the xiso program's Card A and ercot-261's partial-exit window "
        "are both asserted to have 'ZERO effect on 2023-2025 by construction'. On "
        "capacity that is exactly true (0.000000000 effective MW); on the LP SOLUTION "
        "it is not, because 171 extra fixed-at-zero columns change HiGHS's path through "
        "a degenerate optimum -- max |class-hour delta| 854.720 MW. This contradicts the "
        "STOP condition pre-registered in the sibling PJM / NYISO / NEISO / CAISO "
        "prompts ('max |class-hour delta| = 0.000000 MW ... A nonzero delta is a STOP'); "
        "a lane treating its nonzero delta as that STOP would halt on a non-defect. "
        "Recommended replacement: a CAPACITY identity plus a bounded dispatch tolerance. "
        "(d) A GOVERNANCE OBSERVATION, reported and NOT acted on because it is another "
        "ISO's change (rule 25 [R-ISO-SCOPE]): _PARTIAL_EXIT_WINDOW_START is a bare "
        "module constant with no ScenarioConfig field, and data/fleet/eia860.py is not "
        "one of the seven config/solve_surface.py SURFACE_MODULES, so a fleet-composition "
        "change of this class moves NO cache key in any ISO arming partial_plant_exit_carry. "
        "(e) THE D-2 CT_PEAKER OVER-BUDGET ROWS ARE PRE-EXISTING, not this arm's: the "
        "incumbent keeper carries the same three failures (29.9% / 19.5% / 21.2% against "
        "this bundle's 30.8% / 19.8% / 21.7%, the difference being the same HEAD drift), "
        "and C8 passes on both through rule 20's grounded-above-budget escalation."
    )
}


def main() -> int:
    """Write the miso-250 attestation from the keeper's, re-measuring magnitudes."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    # The incumbent keeper's bundle may already have been pruned off disk by the
    # rule-15 keeper-only retention sweep at this promotion, so fall back to git
    # (git history is the record — CLAUDE.md rule 15 [R-DASHBOARD]).
    rel = KEEPER.relative_to(REPO) / "calibration_attestation.json"
    src = KEEPER / "calibration_attestation.json"
    if src.exists():
        att = json.loads(src.read_text())
    else:
        # Several refs are tried because the rule-15 keeper-only prune deletes the
        # incumbent bundle in the SAME commit that promotes this one, so `HEAD`
        # stops carrying it the moment the promotion lands.
        blob = None
        for ref in ("HEAD", "origin/main", "HEAD~1", "HEAD~2", "HEAD~3"):
            got = subprocess.run(
                ["git", "show", f"{ref}:{rel.as_posix()}"],
                capture_output=True,
                text=True,
                cwd=REPO,
                check=False,
            )
            if got.returncode == 0 and got.stdout.strip():
                blob = got
                break
        if blob is None:
            raise SystemExit(
                f"incumbent keeper attestation not on disk at {src} and not in git at "
                f"HEAD / origin/main / HEAD~1..3 for {rel.as_posix()} — refusing to "
                "write an attestation without the ledger it must carry (rule 21 [R-DOF])"
            )
        att = json.loads(blob.stdout)

    # NOTE: calibration_verdict exits 1 on a NOT-YET determination, which is
    # exactly the state this bundle is in BEFORE its attestation exists (an
    # unattested C6). The JSON on stdout is complete either way, so the exit
    # status is deliberately not checked.
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            args.run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=False,
    )
    if not proc.stdout.strip():
        raise SystemExit(
            f"calibration_verdict produced no JSON:\n{proc.stderr[-2000:]}"
        )
    scored = json.loads(proc.stdout)["criteria"]

    # RE-MEASURE every carried exception magnitude on THIS bundle's own scored
    # records; classification and reason are the standing MISO adjudications.
    measured: dict[tuple[str, int], str] = {}
    for crit in ("price_tail", "price_mean"):
        for rec in scored[crit]["records"]:
            if rec.get("key") or rec.get("year") is None:
                continue
            measured[(crit, int(rec["year"]))] = rec["magnitude"]

    # The carried price_mean/2025 exception's PROSE was stale across several
    # keeper generations: it asserted "2023 (-2.2 pct) and 2024 (-8.0 pct) both
    # PASS; only 2025 fails" and quoted model/actual dollars matching no recent
    # run. The magnitude re-measurement below only ever touched `magnitude`, so
    # the wrong narrative flowed verbatim onto the Calibration Status page via
    # status/MISO.js `ledger_entries`. Found by the miso-250 keeper-text audit and
    # corrected HERE, in the generator, so a regeneration cannot restore it.
    price_mean_2025_classification = "WITHIN BAND, DOWNSTREAM OF C3c (the residual is the unrepresentable administrative scarcity tail; magnitude no longer fails price_mean at this keeper's HEAD)"
    price_mean_2025_reason = "CORRECTED 2026-09-09 (miso-250 keeper-text audit): this entry's 2023/2024 comparator values and its 2025 model/actual dollar figures were stale, carried unchanged since an earlier keeper generation that predates this run and predates the miso-248 incumbent it was inherited from; price_mean now PASSES all three years at the \u00b110% band and no year fails. The 2025 mean-LMP gap (model $42.64 vs actual $45.46 load-weighted, -6.2%) remains the arithmetic tail of the C3c residual, NOT an independent level error: 2023 (+4.9%) and 2024 (+1.8%) also PASS, and 2025 carries the largest actual RT>$200 count (88 hrs). Those 88 Indiana-Hub spike hours (actual up to $1,783; model ~$50 median) contribute materially to the remaining $2.82/MWh gap between the actual and model load-weighted means. Closes only DOWNSTREAM of C3c (never via an offer/level adder tuned to the mean) - the same administrative Monte-Carlo-LOLP ORDC/RCPF tail a deterministic perfect-foresight LP cannot form (rules #1/#10). Frontier designation 2026-07-20; see the C3c ledger entries above + docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md. miso-88 note: the widening is the expected cost of a structurally-correct input and is KEPT per rule 1 -- the accurate heat rate stays in even though it worsened this crossing at the time it was written. Per rule 11 a worse fit is a discovered-bug signal to root-cause separately (the 2025 summer-body price formation lane, FINDING-miso87-c3b-summer-2025-body-2026-07.md), never to be offset with a tuned adder."

    for exc in att["exceptions"]:
        key = (str(exc.get("criterion")), int(exc.get("year", 0)))
        if key == ("price_mean", 2025):
            exc["classification"] = price_mean_2025_classification
            exc["reason"] = price_mean_2025_reason
        if key in measured:
            exc["magnitude"] = measured[key]
            exc["magnitude_basis"] = (
                "this run's own scored value (miso-250); the classification and reason "
                "are the standing MISO adjudication carried forward"
            )

    # RULE 21 [R-DOF]: the keeper's ledger is CARRIED VERBATIM and the new field
    # appended. It is deliberately NOT rebuilt by scripts/build_dof_ledger.py:
    # that script regenerates from a fixed derivation and silently DROPS the 16
    # hand-declared MISO entries (cc_committed_band_measured, cc_steam_part_capacity,
    # coal_mustrun_online_pmin, dual_fuel_switching, the laid-up plant census,
    # nuclear_unit_availability, online_rho, partial_plant_exit_carry,
    # retiree_vintage_status_scope, st_gas_mustrun_oom_level, summer_derate_basis_aware,
    # summer_wefor_share_override and the four unit_outage_* boolean arms), taking the
    # ledger 41 -> 25. Losing a declared free parameter at a promotion is a rule-21
    # regression, so the ledger is inherited instead.
    entries = att["free_parameters"]["entries"]
    if not any(
        e.get("name", "").startswith("gas_electric_power_monthly_level")
        for e in entries
    ):
        entries.append(
            {
                "name": "gas_electric_power_monthly_level (boolean arm; miso-250)",
                "where": (
                    "ScenarioConfig.gas_electric_power_monthly_level -> "
                    "data/fuel/resolve.py::resolve_fuel_prices and "
                    "data/fuel/trajectories.py::_gas_series -> "
                    "data/fuel/electric_power.py::iso_electric_power_monthly_level"
                ),
                "identification": "measured-physical",
                "value": (
                    "ZERO free parameters. The EIA N3045<ST>3 monthly delivered-to-electric-"
                    "power series blended across MISO's footprint states by the frozen "
                    "EIA-860 gas-capacity weight table "
                    "(data/raw/reference/iso-gas-capacity-state-weights.csv, "
                    "scripts/data/derive_iso_gas_state_weights.py); the unit conversion is "
                    "the EIA heat content 1.036 MMBtu/Mcf; the two admission conditions "
                    "(all twelve months printed, strict majority of the ISO's gas capacity) "
                    "are declared ex ante in the module docstring and are NEVER swept "
                    "against a gate (rule 1 [R-STRUCT] condition (c))."
                ),
                "lineage_solves": (
                    "1 solve (miso-250 full span); measured INERT on this recipe -- 0 "
                    "differing cells arm vs control at HEAD"
                ),
            }
        )
        att["free_parameters"]["n_entries"] = len(entries)

    att["governance"]["attested_by"] = ATTESTED_BY
    att["disclosures"] = DISCLOSURES
    # governance.authorized_price_tuning is CARRIED VERBATIM, never stripped.
    # This arm's own delta touches no band multiplier, but the RECIPE it
    # inherits does use the rule-1 [R-STRUCT] authorized price-tuning channel
    # (the miso-220 x1.10 non-steam offer lift), so the declaration is required
    # here exactly as in the incumbent keeper -- C6 FAILS without it (rule 1
    # condition (e); calibration_verdict.score_governance AUTHORIZED_TUNING_FIELDS).
    if "authorized_price_tuning" not in att["governance"]:
        raise SystemExit(
            "keeper attestation carries no governance.authorized_price_tuning, but its "
            "recipe uses offer_curve_by_group band multipliers -- refusing to write an "
            "attestation that would pass C6 without the rule-1 declaration"
        )

    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=2) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
