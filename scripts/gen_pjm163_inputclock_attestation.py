"""Write ``calibration_attestation.json`` for the pjm-162 input-clock replay.

DEBUG-B (``docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md``, chartered by
owner decision D-5 / plan §6 decision 2) repaired the PJM EIA-930 fueltype
input clock — the ``NG: *`` family was one hour early in local-2023/2024 —
and re-solved the incumbent keeper recipe at the corrected inputs:
``results/calibration/pjm_debugb_inputclock_A``, registered
``2026-08-15-pjm-162-inputclock``. Every criterion the rubric scores holds the
incumbent's grade (finding §9: PASS -> PASS, zero fails), but the bundle
shipped as a KEEPER CANDIDATE without a governance attestation, so
``calibration_verdict`` scores it **NOT-YET on C6 UNATTESTED alone**.

The owner signed the promotion on 2026-08-16 (DEBUG-manager reissue sitting,
in-session decision card; audit gap row O1). This script writes the
promotion-time attestation so the D-5(b) re-key can re-verify a determination
that is not worse than the incumbent's CALIBRATED.

**Nothing here is a new claim.** The repair is a value-preserving measured-
input re-placement (rules 13/14): no parameter is introduced or moved, so the
attestation is the incumbent keeper's carried forward with (1) a rewritten
``attested_by``/``note`` stating the input repair and its byte-verified
mechanics, and (2) a new measured-input entry for the corrected fueltype
clock. The **DOF ledger is carried VERBATIM** and this script ASSERTS that
rather than trusting it (rule 21) — the incumbent's own ledger notes record
that a blind ``build_dof_ledger.py`` rebuild drops curated measured/published
entries (the nyiso-8x/9x/10x failure mode), which is why carry-verbatim is
the convention.

Every premise is **COMPUTED, not typed**, and a failed assertion aborts
without writing:

* the arm's ``ScenarioConfig`` differs from the incumbent's in **zero** shared
  values; the only ``keeper_only`` fields are schema deletions (fields HEAD no
  longer has), and every ``arm_only`` field is post-incumbent schema drift
  sitting at its HEAD default, each non-falsy one verified PJM-unreachable;
* the committed extract still carries the corrected clock at promotion time:
  the July ``NG: SUN`` generation-weighted centroid is inside the
  astronomical gate [11.5, 12.3] in every scored year (the finding's §3 gate,
  recomputed here from the committed parquet via the model's own loader);
* verdict parity on committed artifacts: the incumbent re-scores CALIBRATED,
  and the arm's ONLY non-PASS criterion pre-attestation is C6 UNATTESTED.

No LP is solved and no bundle is regenerated. Training years only (rule 22).

Usage::

    PYTHONPATH=.:src python scripts/gen_pjm163_inputclock_attestation.py [--write]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

CAL = REPO / "results" / "calibration"
INCUMBENT = CAL / "pjm152_collapse_A"
INCUMBENT_ID = "2026-08-04-pjm-152-collapse"
ARM = CAL / "pjm_debugb_inputclock_A"
ARM_ID = "2026-08-15-pjm-162-inputclock"
FINDING = "docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md"

#: Fields the incumbent's recorded recipe carries that ScenarioConfig no longer
#: has (deleted by intervening lanes after pjm-152 solved). Their presence in
#: keeper_only is schema deletion, not a recipe change — and it is the same
#: replayability argument that promoted pjm-152 over pjm-151: the incumbent's
#: recorded recipe is no longer replayable as recorded at HEAD; the arm's is.
RETIRED_FIELDS = {
    "coal_tranche_1_frac",
    "coal_tranche_1_fuel_passthrough",
    "coal_tranche_2_frac",
    "coal_tranche_2_fuel_passthrough",
    "coal_tranche_3_frac",
    "coal_tranche_3_fuel_passthrough",
}

#: Fields ScenarioConfig gained after the incumbent solved. Each must sit at
#: its HEAD default in the arm; the non-falsy ones are individually verified
#: PJM-unreachable below. Listed as a literal so an unexpected field aborts.
EXPECTED_DRIFT = {
    "caiso_nqc_accreditation",
    "caiso_ra_mpb_capacity_anchor",
    "caiso_storage_nqc_accreditation",
    "capacity_screen_scarcity_restoration",
    "capacity_screen_unified_lookahead",
    "cc_steam_part_capacity",
    "cc_steam_part_reclass",
    "cc_winter_capability_basis",
    "coal_peak_offer_level_yearly",
    "coal_peak_offer_yearly_level",
    "coal_perplant_offer_curves_yearly",
    "coal_perplant_offer_yearly",
    "entry_pipeline_aware_signal",
    "ercot_dam_availability_event_cap_reconciliation",
    "ercot_dam_availability_event_cap_unit_scoped",
    "ercot_econ_curve_top_refine",
    "ercot_faststart_pool_plant_physics",
    "ercot_offer_surface_continuous",
    "ercot_offer_surface_position_tail",
    "ercot_offer_surface_top_scoped",
    "ercot_offline_commit_offer",
    "ercot_offline_commit_offer_path",
    "ercot_partial_outage_shaped_derate",
    "ercot_storage_as_soc_reserve",
    "ercot_storage_rt_offer_surface",
    "ercot_wtx_curtail_unpooled",
    "ercot_wtx_panhandle_owner",
    "ira_ptc_credit_window_years",
    "miso_clean_tier_rows",
    "miso_offer_surface_measured",
    "miso_offer_surface_netload_pcts",
    "miso_offer_surface_path",
    "miso_offer_surface_position_bins",
    "miso_rps_compliance_regions",
    "nyiso_li_tsl_n11_security",
    "nyiso_seam_deliverability_envelope",
    "nyiso_seam_par_attribution",
    "nyiso_solar_market_generator_basis",
    "nyiso_solar_registry_cod_dates",
    "pjm_measured_outage_event_cap",
    "smr_available_year",
    "storage_measured_base_fleet",
    "summer_derate_basis_aware",
    "unit_outage_lp_capacity_basis",
    "vre_procurement_additions_enabled",
}

#: Rule-25 name scoping: a field with another ISO's prefix never reaches a PJM
#: solve regardless of value.
_OTHER_ISO_PREFIXES = ("caiso_", "ercot_", "miso_", "nyiso_", "neiso_")

CENTROID_GATE = (11.5, 12.3)
YEARS = (2023, 2024, 2025)


def _cfg(bundle: Path) -> dict:
    data = json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))
    return data.get("scenario_config", data)


def _head_defaults() -> dict:
    """HEAD ScenarioConfig defaults via dataclass reflection (no instantiation)."""
    from market_sim.config.scenarios import ScenarioConfig

    out = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.default is not dataclasses.MISSING:
            out[f.name] = f.default
        elif f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            out[f.name] = f.default_factory()  # type: ignore[misc]
    return out


def assert_recipe_identity() -> dict:
    """Assert the arm is the incumbent's recipe modulo schema drift. Returns the diff."""
    inc, arm = _cfg(INCUMBENT), _cfg(ARM)
    keeper_only = sorted(set(inc) - set(arm))
    arm_only = sorted(set(arm) - set(inc))
    value_diffs = {k: (inc[k], arm[k]) for k in set(inc) & set(arm) if inc[k] != arm[k]}

    assert not value_diffs, f"recipe is NOT identical: {value_diffs}"
    assert set(keeper_only) == RETIRED_FIELDS, f"unexpected keeper_only: {keeper_only}"
    assert set(arm_only) == EXPECTED_DRIFT, f"unexpected arm_only drift: {arm_only}"

    defaults = _head_defaults()
    # keeper_only fields must be genuine schema deletions at HEAD.
    still_live = RETIRED_FIELDS & set(defaults)
    assert not still_live, f"'retired' fields still in ScenarioConfig: {still_live}"

    def _eq(a: object, b: object) -> bool:
        # run_config.json round-trips tuples as lists (YAML/JSON have no
        # tuple) — compare tuple-typed defaults through the same coercion the
        # cache-key repair (debug-sweep seed 7, commit 01d5748) canonicalised.
        if isinstance(b, tuple) and isinstance(a, list):
            return tuple(a) == b
        return a == b

    # Every drift field still in the schema must sit at its HEAD default —
    # the replay armed nothing. A drift field ScenarioConfig has since
    # DELETED (rule-26 collapses in other lanes, e.g. the ercot-204 and
    # nyiso solar-registry deletions) must be recorded falsy: it was at its
    # then-default when the arm solved and cannot be read at HEAD at all.
    deleted_since = sorted(k for k in arm_only if k not in defaults)
    armed_deleted = {k: arm[k] for k in deleted_since if arm[k] not in (False, None)}
    assert not armed_deleted, (
        f"since-deleted drift field recorded ARMED: {armed_deleted}"
    )
    off_default = {
        k: (arm[k], defaults[k])
        for k in arm_only
        if k in defaults and not _eq(arm[k], defaults[k])
    }
    assert not off_default, f"drift fields NOT at HEAD defaults: {off_default}"

    # Non-falsy drift fields each need a computed PJM-unreachability premise.
    unreachable: dict[str, str] = {}
    for k in arm_only:
        v = arm[k]
        if v in (False, None) or k in deleted_since:
            continue
        if k.startswith(_OTHER_ISO_PREFIXES):
            unreachable[k] = "rule-25 ISO-scoped by name; never read on a PJM solve"
            continue
        if k == "storage_measured_base_fleet":
            from market_sim.model.storage import STORAGE_MEASURED_BASE_FLEET_ISOS

            assert arm.get("mode") == "backcast", "arm is not a backcast"
            assert "PJM" not in STORAGE_MEASURED_BASE_FLEET_ISOS, (
                "PJM enrolled in STORAGE_MEASURED_BASE_FLEET_ISOS — premise dead"
            )
            unreachable[k] = (
                "backcast leg scoped to STORAGE_MEASURED_BASE_FLEET_ISOS="
                f"{sorted(STORAGE_MEASURED_BASE_FLEET_ISOS)} (PJM not enrolled, "
                "rule 25); hindcast leg needs mode='forecast'"
            )
            continue
        if k == "ira_ptc_credit_window_years":
            assert v == 10, f"non-statutory PTC window {v!r}"
            unreachable[k] = (
                "statutory 10-yr §45 window at its HEAD default; sole consumer "
                "is the forecast-mode economic new-entry screen "
                "(model/capacity_evolution/new_entry.py), unreachable in a "
                "2023-2025 backcast with the fleet pinned by year"
            )
            continue
        raise AssertionError(f"unhandled non-falsy drift field: {k}={v!r}")

    return {
        "keeper_only_schema_deletions": sorted(RETIRED_FIELDS),
        "arm_only": arm_only,
        "arm_only_deleted_since_solve_recorded_falsy": deleted_since,
        "shared_value_diffs": 0,
        "drift_fields_all_at_head_defaults": True,
        "nonfalsy_drift_unreachable": unreachable,
    }


def assert_input_clock_gates() -> dict:
    """Recompute the finding §3 solar-centroid gate from the committed extract."""
    import numpy as np

    from market_sim.data import eia_loader

    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_start = [0]
    for d in month_days[:-1]:
        month_start.append(month_start[-1] + d * 24)
    hours = 8760
    month_of_hoy = np.zeros(hours, dtype=int)
    for i in range(12):
        month_of_hoy[month_start[i] : month_start[i] + month_days[i] * 24] = i + 1
    hour_of_day = np.arange(hours) % 24

    lo, hi = CENTROID_GATE
    cents = {}
    for y in YEARS:
        frame = eia_loader._eia_hourly_frame_filled("PJM", y)
        assert frame is not None, f"no PJM extract frame for {y}"
        sun = frame["NG: SUN"].to_numpy(dtype=float)
        k = (month_of_hoy == 7) & np.isfinite(sun) & (sun > 0)
        cent = float((sun[k] * hour_of_day[k]).sum() / sun[k].sum())
        assert lo <= cent <= hi, f"{y} July NG:SUN centroid {cent:.2f} outside gate"
        cents[str(y)] = round(cent, 2)
    return cents


def assert_verdict_parity() -> dict:
    """Score both runs on committed artifacts; assert the promotion premises.

    Two valid states, so the committed script stays a re-runnable verification
    record after the promotion lands:

    * **pre-attestation** (the state the ``--write`` ran against): the arm's
      ONLY non-PASS criterion is C6 UNATTESTED, determination NOT-YET;
    * **post-attestation** (any later re-run): the written attestation scores
      C6 PASS and the arm re-verifies CALIBRATED with zero non-PASS criteria.

    Anything else — a FAIL, a caveat, a data-blocked year, a worse incumbent —
    aborts.
    """
    from scripts import calibration_verdict as cv

    inc = cv.determine_from_artifacts(INCUMBENT_ID, cv.load_artifacts(INCUMBENT_ID))
    arm = cv.determine_from_artifacts(ARM_ID, cv.load_artifacts(ARM_ID))

    assert inc["determination"] == "CALIBRATED", (
        f"incumbent re-scores {inc['determination']!r}, not CALIBRATED — "
        "the O2-corrected baseline is dead; stop"
    )
    non_pass = {
        cid: c["status"] for cid, c in arm["criteria"].items() if c["status"] != "PASS"
    }
    if non_pass == {"governance": "UNATTESTED"}:
        state = "pre-attestation"
        assert arm["determination"] == "NOT-YET", arm["determination"]
    elif not non_pass:
        state = "post-attestation"
        assert arm["determination"] == "CALIBRATED", arm["determination"]
    else:
        raise AssertionError(f"arm has disqualifying non-PASS criteria: {non_pass}")
    assert not arm["data_blocked_years"], arm["data_blocked_years"]
    return {
        "incumbent": {
            "run_id": INCUMBENT_ID,
            "determination": inc["determination"],
            "grade_summary": inc["grade_summary"],
        },
        "arm_scored": {
            "state": state,
            "run_id": ARM_ID,
            "determination": arm["determination"],
            "reasons": arm["reasons"],
            "grade_summary": arm["grade_summary"],
        },
        "rubric_version": arm["rubric_version"],
    }


def build(recipe: dict, cents: dict, parity: dict) -> dict:
    """Carry the incumbent attestation forward; DOF ledger verbatim (asserted)."""
    att = json.loads(
        (INCUMBENT / "calibration_attestation.json").read_text(encoding="utf-8")
    )
    before = (att["free_parameters"]["n_entries"], att["free_parameters"]["n_residual"])

    gov = att["governance"]
    gov["attested_by"] = (
        "pjm-163 (2026-08-16) — promotion-time governance attestation for the "
        "DEBUG-B input-clock replay 2026-08-15-pjm-162-inputclock, promoted by "
        "owner decision card this sitting (audit gap row O1). Carried forward "
        "from the incumbent keeper 2026-08-04-pjm-152-collapse (itself attested "
        "at pjm-153); every premise recomputed by "
        "scripts/gen_pjm163_inputclock_attestation.py, none typed."
    )
    gov["note"] = (
        "MEASURED-INPUT REPAIR REPLAY, NOT A MECHANISM AND NOT A LEVER "
        "(rules 13 [R-MEASURED] / 14 [R-ACCURATE]; the neiso-85/86 gas-basis "
        "precedent). DEBUG-B repaired the committed PJM EIA-930 wide extract's "
        "fueltype input clock — the NG:* family ran one hour EARLY at the "
        "source in local-2023/2024 — by value-preserving UTC re-placement "
        "(each cell keeps its measured value and moves to the hour it "
        "measures; byte-verified cell-for-cell in the finding §2a: region "
        "family + all rows outside the two blocks IDENTICAL, every in-block "
        "cell == pristine value at T-1h, NaN count unchanged), and switched "
        "four PJM DataMiner read sites onto the files' own absolute UTC "
        "stamps. ZERO free parameters added or removed; the DOF ledger is "
        "carried VERBATIM (n_entries 19, n_residual 6, ASSERTED here rather "
        "than claimed). The recipe is IDENTICAL to the incumbent's on every "
        "shared field (zero value diffs, asserted); keeper_only fields are "
        "schema DELETIONS at HEAD (the six coal_tranche_* fields), so the "
        "incumbent's recorded recipe is no longer replayable as recorded "
        "while this bundle's is — the same structural-integrity argument "
        "that promoted pjm-152 over pjm-151; every arm_only field is "
        "post-incumbent schema drift recorded at its default (each "
        "non-falsy one verified PJM-unreachable; the since-deleted ones "
        "recorded falsy). WHY THIS IS THE BETTER "
        "KEEPER: rule 14 — the accurate measured input replaces the "
        "defective one, and NOTHING worsened at the corrected inputs "
        "(finding §9: every shared criterion PASS -> PASS, zero fails; "
        "rule 14's accurate-input-vs-residual trade was never invoked). "
        "Blast radius exactly as predicted: bench/PJM 2023+2024 recomputed, "
        "2025 byte-identical (its source clock was already correct). The "
        "solve is a full-span fresh re-solve of all three years in ONE "
        "bundle (rule 16 [R-ALLYEARS], meta.json reuse: null), registered "
        "same-session (rule 15 [R-DASHBOARD]). LOYO is structurally n/a: "
        "no parameter exists to identify (finding §5)."
    )
    gov["residuals_note"] = (
        "The like-for-like §9 verdict table is the A/B record: on the seven "
        "criteria rubric v3.2 scores, the corrected inputs hold the "
        "incumbent's PASS on all of them, with the C8 grounded-above-budget "
        "notes carrying over essentially unchanged (CT_PEAKER 16.2/16.4/16.7% "
        "vs the incumbent's 16.2/16.4/16.7%; 2025 ST_GAS 39.9%). The "
        "incumbent's own residuals_note (pjm-133/pjm-121 pre-guard envelope "
        "lineage) is superseded here by the input repair but remains in the "
        "incumbent bundle's attestation as the historical record."
    )

    mi = gov.get("measured_inputs_verified_present", {})
    mi["pjm_eia930_fueltype_input_clock (DEBUG-B repair)"] = (
        "APPLIED — the committed extract carries the corrected fueltype "
        "clock for 2023-2025 at promotion time: July NG:SUN "
        "generation-weighted centroids "
        + ", ".join(f"{y} {c}" for y, c in cents.items())
        + f" all inside the astronomical gate [{CENTROID_GATE[0]}, "
        f"{CENTROID_GATE[1]}] (recomputed from the committed parquet via "
        "eia_loader at attestation time, not quoted). Wind/solar/gas "
        "diff-lag 0 vs the PJM UTC feed and demand daily-peak mode-0 "
        ">=95% per the finding §3. Years <=2022 remain on the early source "
        "clock — chartered separately (finding §6, audit row O3)."
    )
    mi["_carried_from_incumbent"] = (
        "The six recipe measured-input entries below/above are carried from "
        "the incumbent attestation: the recipe is asserted value-identical, "
        "and the replay's application evidence is the finding §9 "
        "registration (e.g. §8 records the live DA-virtuals fetch and "
        "data/clean rebuild the replay required)."
    )
    gov["measured_inputs_verified_present"] = mi

    after = (att["free_parameters"]["n_entries"], att["free_parameters"]["n_residual"])
    assert before == after == (19, 6), f"DOF ledger moved {before} -> {after}"

    att.pop("collapse_verification", None)
    att["inputclock_verification"] = {
        "finding": FINDING,
        "charter": "docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md",
        "byte_verification": (
            "finding §2a: 74,470 rows x 16 cols — region family + time "
            "columns identical everywhere; NG:* outside the two blocks "
            "identical (56,927 rows); every in-block cell == pristine value "
            "at UTC T-1h (17,543 rows); NaN count 49,305 unchanged"
        ),
        "recipe_diff_vs_incumbent": recipe,
        "july_ng_sun_centroids_at_attestation": cents,
        "verdict_parity": parity,
        "incumbent": INCUMBENT_ID,
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write the attestation")
    args = ap.parse_args()

    recipe = assert_recipe_identity()
    cents = assert_input_clock_gates()
    parity = assert_verdict_parity()
    att = build(recipe, cents, parity)

    print("=" * 72)
    print(
        "pjm-163 — attestation for the pjm-162 input-clock replay (premises COMPUTED)"
    )
    print("=" * 72)
    print(f"  shared-value diffs vs incumbent : {recipe['shared_value_diffs']}")
    print(
        f"  keeper_only (schema deletions)  : {len(recipe['keeper_only_schema_deletions'])}"
    )
    print(f"  arm_only drift at HEAD defaults : {len(recipe['arm_only'])}")
    for k, why in recipe["nonfalsy_drift_unreachable"].items():
        print(f"    non-falsy {k}: {why[:80]}")
    print(f"  July NG:SUN centroids           : {cents} (gate {CENTROID_GATE})")
    print(f"  incumbent re-score              : {parity['incumbent']['determination']}")
    print(
        f"  arm ({parity['arm_scored']['state']})  : "
        f"{parity['arm_scored']['determination']} "
        f"{parity['arm_scored']['reasons']}"
    )
    fp = att["free_parameters"]
    print(
        f"  DOF ledger carried VERBATIM: n_entries {fp['n_entries']}, "
        f"n_residual {fp['n_residual']}"
    )

    out = ARM / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {out}")
    else:
        print(f"\n(dry run — pass --write to write {out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
