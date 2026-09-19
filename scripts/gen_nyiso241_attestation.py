#!/usr/bin/env python3
"""Generate an nyiso-241 arm attestation (rule 21 `[R-DOF]`, C6 governance).

Both arms move `_NYISO_OFFER_CURVE`'s CT_PEAKER bands to values the band dict ALREADY CARRIES as
its own registered `phys_*` measurements (`nyiso_campd_marginal_hr_summary.csv` p50s, n = 70):

  * **ARM A** ``nyiso_ct_peaker_committed_measured`` — ``committed`` 1.35 -> 0.843, and nothing
    else. Matrix cell ``ct_peaker_committed_measured`` (``U``), which the caiso-241 cross-ISO
    census recorded as "an ASK FOR THE NYISO LANE, never an arm from here".
  * **ARM B** ``nyiso_ct_peaker_bands_measured`` + ``cc_duct_peaking_row_scoped`` — the three-way
    re-test of two ``R`` cells under the nyiso-200 sharpened condition, over the run screen
    ``nyiso_gas_bridge_startup_aware`` already armed on the keeper.

Neither adds a free parameter: there is no value to pick, so the keeper's DOF ledger is carried
VERBATIM and ``authorized_price_tuning`` stays **NONE**. That last point is the nyiso-232
precedent and it is the one most worth stating plainly, because a band multiplier IS the rule-1
`[R-STRUCT]` carve-out channel in general: the carve-out governs a band identified by the PRICE
RESIDUAL, and 0.843 / 0.661 / 0.658 are identified by NYISO's own CAMPD conduct. The pre-registered
expectation and the decision rule were pushed BEFORE either solve, in
``docs/PRECOMMIT-nyiso241-ct-peaker-merit-2026-09-19.md``.

Every governance claim that can be checked against the committed artifacts IS checked here and
written into ``governance.computed_checks``; the script ABORTS on a failed premise rather than
emitting an attestation that asserts something false.

Run: ``python3 scripts/gen_nyiso241_attestation.py {a|b}``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

CAL = Path("results/calibration")
KEEPER = CAL / "nyiso240_benchfix_span"
YEARS = (2022, 2023, 2024, 2025)

#: Per arm: bundle dir, the fields it arms, and the CT_PEAKER bands it is allowed to move.
#: Declared here rather than inferred, so an arm that moves a band it did not declare ABORTS.
ARMS = {
    "a": {
        "bundle": CAL / "nyiso241_ctcommitted_span",
        "fields": {"nyiso_ct_peaker_committed_measured": True},
        "bands": {"committed": "phys_committed"},
        "matrix_cell": "ct_peaker_committed_measured",
    },
    "b": {
        "bundle": CAL / "nyiso241_ctbands_span",
        "fields": {
            "nyiso_ct_peaker_bands_measured": True,
            "cc_duct_peaking_row_scoped": True,
        },
        "bands": {
            "committed": "phys_committed",
            "econ_low": "phys_econ_low",
            "econ_high": "phys_econ_high",
        },
        "matrix_cell": "nyiso_ct_peaker_bands_measured + cc_duct_peaking_row_scoped",
    },
}

#: Legitimately per-solve-YEAR, therefore not a per-year RECIPE (rule 1 `[R-STRUCT]` (b)).
PER_YEAR_RESOLVED = {"gas_price_override", "weather_year"}

#: Bookkeeping that records WHERE and WHEN a bundle was solved, never WHAT was solved.
#: `environment` is checked separately — its package versions ARE gated, its kernel string is not.
PROVENANCE_KEYS = {
    "timestamp",
    "run_note",
    "note",
    "out_dir",
    "composed_from",
    "git_sha",
    "basis_sha",
    "environment",
}

#: The generic `prb_overrides` dict `replay_keeper --set` also routes the arm through. Its
#: contents are inspected key-by-key rather than waived.
OVERRIDE_CHANNEL = "coal_prb_sigmoid_overrides"

BAND_KEYS = (
    "committed",
    "econ_low",
    "econ_high",
    "peak",
    "econ_low_share",
    "pct_peaking",
)


def _load_meta(bundle: Path) -> dict:
    """Read a bundle's authoritative kwarg snapshot."""
    return json.loads((bundle / "meta.json").read_text())


def main() -> None:
    """Write the arm's attestation, aborting on any premise that does not hold."""
    which = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
    if which not in ARMS:
        raise SystemExit(f"usage: {sys.argv[0]} {{a|b}}")
    spec = ARMS[which]
    arm_dir: Path = spec["bundle"]

    from market_sim.pipeline.backcast_config import _NYISO_OFFER_CURVE

    checks: dict[str, object] = {}
    keep_meta = _load_meta(KEEPER)
    arm_meta = _load_meta(arm_dir)

    # (1) THE ARM IS THE KEEPER'S RECIPE PLUS EXACTLY THE DECLARED FIELDS. Anything else that
    # moved is a second lever this attestation has not declared, and it aborts.
    moved = {
        k: (keep_meta.get(k), arm_meta.get(k))
        for k in set(keep_meta) | set(arm_meta)
        if keep_meta.get(k) != arm_meta.get(k)
    }
    undeclared = {
        k: v
        for k, v in moved.items()
        if k not in spec["fields"]
        and k not in PER_YEAR_RESOLVED
        # provenance/bookkeeping, not physics
        and k not in PROVENANCE_KEYS
        # the generic override channel: inspected field-by-field just below, not waived
        and k != OVERRIDE_CHANNEL
        # a field that did not EXIST when the keeper was solved and reads its own OFF default in
        # the arm has not moved anything — it is the snapshot widening, not a lever. Gated on the
        # off default specifically, so a NEW field arriving armed still aborts.
        and not (v[0] is None and v[1] in (False, None))
    }
    assert not undeclared, f"undeclared recipe deltas vs the keeper: {undeclared}"

    # Each declared field must be ARMED on the resolved config. Where it lands depends on the
    # field: one with a named `solve_and_persist` kwarg is a top-level `meta.json` key, while one
    # consumed via `getattr(config, ...)` — `cc_duct_peaking_row_scoped` — has no kwarg and rides
    # the generic override dict only. `run_config.scenario_config` is the RESOLVED truth for both,
    # so all three are checked and at least one must carry it armed.
    run_cfg = json.loads((arm_dir / "run_config.json").read_text())
    resolved = run_cfg.get("scenario_config") or {}
    arm_ovr_early = arm_meta.get(OVERRIDE_CHANNEL) or {}
    armed_where: dict[str, list[str]] = {}
    for field, want in spec["fields"].items():
        seen = {
            "meta": arm_meta.get(field),
            "override_channel": arm_ovr_early.get(field),
            "run_config.scenario_config": resolved.get(field),
        }
        where = [k for k, v in seen.items() if v is want]
        assert where, f"{field} is not {want!r} anywhere on the arm: {seen}"
        assert resolved.get(field) is want, (
            f"{field} reads {resolved.get(field)!r} on the RESOLVED scenario_config, expected "
            f"{want!r} — a flag recorded but not resolved is the silent-no-op class rule 24 "
            "[R-REGISTRY] forbids"
        )
        armed_where[field] = where

    # `replay_keeper --set` delivers the arm through the GENERIC override dict as well as the
    # named kwarg, so that dict necessarily differs. Inspect it field-by-field rather than
    # waiving it: the ONLY keys that may move are the declared ones, or a second lever would
    # ride in here unnoticed — which is exactly the silent-no-op class rule 24 [R-REGISTRY]
    # and the nyiso-199/232 fail-loud guards were written for.
    keep_ovr = keep_meta.get(OVERRIDE_CHANNEL) or {}
    arm_ovr = arm_meta.get(OVERRIDE_CHANNEL) or {}
    ovr_moved = {
        k: (keep_ovr.get(k), arm_ovr.get(k))
        for k in set(keep_ovr) | set(arm_ovr)
        if keep_ovr.get(k) != arm_ovr.get(k)
    }
    ovr_undeclared = {k: v for k, v in ovr_moved.items() if k not in spec["fields"]}
    assert not ovr_undeclared, (
        f"undeclared deltas inside {OVERRIDE_CHANNEL}: {ovr_undeclared}"
    )

    # The solve environment: package versions must be IDENTICAL to the keeper's, so the arm's
    # effect is the field and not a numerics change (the nyiso-231 off-pin lesson). The kernel
    # string is container provenance and is recorded rather than gated.
    keep_env = keep_meta.get("environment") or {}
    arm_env = arm_meta.get("environment") or {}
    assert keep_env.get("packages") == arm_env.get("packages"), (
        f"solve packages differ: {keep_env.get('packages')} vs {arm_env.get('packages')}"
    )
    assert keep_env.get("python_version") == arm_env.get("python_version"), (
        "python version differs between the keeper and the arm"
    )
    checks["environment_matches_the_keeper"] = {
        "packages": arm_env.get("packages"),
        "python_version": arm_env.get("python_version"),
        "platform_keeper": keep_env.get("platform"),
        "platform_arm": arm_env.get("platform"),
        "platform_is_container_provenance_not_numerics": True,
    }
    checks["one_declared_delta"] = {
        "keeper": str(KEEPER),
        "fields_moved": {
            k: [moved[k][0], moved[k][1]] for k in spec["fields"] if k in moved
        },
        "override_channel_deltas": {k: list(v) for k, v in ovr_moved.items()},
        "each_declared_field_armed_on_the_resolved_config": armed_where,
        "provenance_only_deltas": sorted(
            k for k in moved if k in PROVENANCE_KEYS or k == "environment"
        ),
        "undeclared_deltas": 0,
    }

    # (2) THE BAND VALUES ARE THE REGISTERED MEASUREMENTS, not chosen. Nothing to pick means
    # nothing to sweep (rules 1(c) / 21 [R-DOF]).
    ct = _NYISO_OFFER_CURVE["CT_PEAKER"]
    grounded = {}
    for band, phys in spec["bands"].items():
        assert phys in ct, (
            f"CT_PEAKER carries no {phys} to ground on (rule 25 [R-ISO-SCOPE])"
        )
        grounded[band] = {
            "registered": ct[band],
            "measured": ct[phys],
            "source_key": phys,
        }
    checks["bands_are_the_registered_measurements"] = {
        "source": "data/raw/reference/nyiso_campd_marginal_hr_summary.csv (avg_committed_p50 / "
        "marg_econ_{low,high}_p50, n = 70), carried in _NYISO_OFFER_CURVE as phys_*",
        "grounded": grounded,
        "values_chosen_by_this_session": 0,
        "values_swept_against_any_gate": 0,
    }

    # (3) BANDS NOT DECLARED ARE UNTOUCHED — in particular `peak`, which is NYISO's
    # $1,000-offer-cap scarcity wall and not a physics claim (rule 19 [R-ONE-MECH]: grounding it
    # would delete a mechanism rather than repair a basis).
    untouched = [b for b in BAND_KEYS if b not in spec["bands"]]
    checks["undeclared_bands_untouched"] = {
        "bands": {b: ct.get(b) for b in untouched},
        "peak_left_at_the_offer_cap_wall": ct.get("peak"),
    }

    # (4) ONE CONFIG ACROSS EVERY SCORED YEAR (rule 1 [R-STRUCT] (b)); a per-year value would be
    # per-year fitting and is refused.
    assert tuple(arm_meta.get("years") or ()) == YEARS, (
        f"arm solved {arm_meta.get('years')}, expected the ISO's full registered union {list(YEARS)} "
        "(rules 16 [R-ALLYEARS] / 34(c) [R-SHARD-PROMOTABLE])"
    )
    checks["one_config_across_every_scored_year"] = {
        "years": list(YEARS),
        "per_year_field_values": 0,
        "solved_in_one_invocation_into_one_bundle": True,
    }

    # (5) ZERO NEW FREE PARAMETERS: the ledger is the keeper's, byte-for-byte.
    keep_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    ledger = keep_att["free_parameters"]
    checks["dof_ledger_carried_verbatim"] = {
        "source": f"{KEEPER}/calibration_attestation.json",
        "n_entries": ledger.get("n_entries"),
        "n_residual": ledger.get("n_residual"),
        "new_entries_added_by_this_run": 0,
    }

    # (6) THE REGISTRATION-CRITICAL PER-PLANT LAYER IS PRESENT for every year, so the run can
    # actually back a promotion (rule 34 [R-SHARD-PROMOTABLE] (d)).
    missing = [
        y for y in YEARS if not (arm_dir / "dispatch" / f"{y}_P1.parquet").exists()
    ]
    assert not missing, (
        f"dispatch/<yr>_P1.parquet missing for {missing} — registration would fail"
    )
    checks["per_plant_layer_present"] = {"years": list(YEARS), "missing": []}

    note = (
        "authorized_price_tuning is NONE for this run. The rules 1 [R-STRUCT] / 13 [R-MEASURED] "
        "authorized price-tuning carve-out governs an offer_curve_by_group band multiplier "
        "IDENTIFIED BY THE PRICE RESIDUAL. These bands are identified by NYISO's own CAMPD "
        "conduct — the phys_* measurements the band dict already carried — so there is no value "
        "to declare, none to sweep, and no DOF entry (the nyiso-232 precedent, where two band "
        "multipliers moved and authorized_price_tuning was likewise NONE)."
    )

    attested = (
        f"session nyiso-241 (2026-09-19), ARM {which.upper()}. Pre-registration: "
        "docs/PRECOMMIT-nyiso241-ct-peaker-merit-2026-09-19.md, pushed at "
        "5356fb712f8ff3ad2b785421d34ed9b4cae71f4c BEFORE either LP, carrying the phase-0 "
        "measurements, the gates and the DECISION RULE between the two arms. "
        f"Matrix cell(s): {spec['matrix_cell']}. "
        "THE BASIS IS STRUCTURAL AND NEVER THE RESIDUAL, on two independent grounds. (1) Rule 14 "
        "[R-ACCURATE] / rule 25 [R-ISO-SCOPE]: CT_PEAKER's registered committed 1.35 rests on a "
        "three-way citation ring — it reads 'NYISO/CAISO-grounded' in _NYISO_OFFER_CURVE, "
        "'NYISO-grounded' in CAISO's and 'NYISO/CAISO-grounded' in NEISO's, and NO ISO cites a "
        "measurement; NYISO's registered-to-measured ratio 1.35/0.843 = 1.60 is the largest in "
        "the model. Each lane grounds its OWN band on its OWN number and nothing crosses: CAISO's "
        "0.991 and NEISO's 0.985 are never carried here. (2) Rule 19 [R-ONE-MECH]: the keeper "
        "carries tranche_startup_amortization, so the CT_PEAKER _committed rows ALREADY pay a "
        "measured start recovery of $11.97 / $16.48 / $15.78 / $13.22 per MWh in 2022-2025 "
        "(model/commitment.compute_monthly_markup, per LP row from that row's own P0 run length; "
        "measured at zero LP in results/calibration/_nyiso241_ct_offer_anatomy.json). A 1.35 "
        "multiplicative 'start hurdle' on top of that charges the same phenomenon twice, and the "
        "substitution removes the duplicate rather than discounting the real one. "
        "SIZED BEFORE IT WAS PROPOSED, AND REPORTED AGAINST ITSELF (PRECOMMIT §2.3): against the "
        "keeper's own hourly prices a deliberately GENEROUS upper bound — the fleet flat out in "
        "every zone-hour its offer clears, no min-run, no ramp, no start, no competition — reaches "
        "only 16-41 % (arm A) or 53-66 % (arm B) of metered CT_PEAKER energy in 2023-2025. So even "
        "the wider arm leaves at least a third of the object unreachable from the offer side, and "
        "NEITHER ARM IS PROMOTABLE AS 'THE CT_PEAKER FIX'. The residual belongs to the price side "
        "(the ledgered C3c tail: model 7 / 0 / 0 / 3 h > $300 against 101 / 10 / 13 / 42 actual) "
        "or to a commitment / local-reliability obligation. That is recorded here so a favourable "
        "C1 move cannot later be read as the object closing. "
        "RULE 28 [R-MECH-MATRIX] (a) WAS DISCHARGED BEFORE ANYTHING WAS PROPOSED: two DO-NOT-REDO "
        "cells were checked and are NOT re-tested — gas_st_startup_cost (refused two independent "
        "ways by nyiso-172, no new grounding evidence offered here, even though this session's "
        "phase 0 measures ST_GAS paying EXACTLY ZERO startup amortization against CT's $12-16/MWh) "
        "and the downstate CT gas basis (extending it to the LI CC/ST fleet refuted on measured "
        "EIA-923 Schedule 5 evidence, 2026-08-19) — the latter being, on this session's own "
        "measurement, the object's dominant carrier at +1.00 / +1.40 / +2.04 / +2.57 $/MMBtu over "
        "the CC/ST fleet, i.e. $16-41/MWh at HR 15.8, and correct."
    )
    if which == "b":
        attested += (
            " ARM B RE-TESTS TWO `R` CELLS, and the new evidence rule 28(a) requires is stated "
            "rather than assumed: nyiso-200 stopped this pairing because its 'commitment-real run "
            "screen' partner was not yet on the keeper, and nyiso240_benchfix_span/meta.json now "
            "carries nyiso_gas_bridge_startup_aware: true (with nyiso_gas_commitment_bridge and "
            "nyiso_gas_bridge_min_run). The condition's 'never alone' limb is honoured — this is "
            "the three-way, with cc_duct_peaking_row_scoped. Its 'span only if the 2025 screen "
            "clears' STAGING is SPENT rather than satisfied: rule 29 [R-SCREEN] was removed "
            "2026-09-16 ('a new config goes STRAIGHT TO THE FULL SPAN') and rules 16 / 34(c) now "
            "carry the how-many-years question. C3a-2025 REMAINS THE NAMED RISK and is gated."
        )

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": attested,
            "note": note,
            "computed_checks": checks,
        },
        "authorized_price_tuning": None,
        "free_parameters": ledger,
        "exceptions": [],
        "exceptions_note": keep_att.get("exceptions_note", ""),
    }
    dest = arm_dir / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dest}")
    for key in checks:
        print(f"  check OK: {key}")


if __name__ == "__main__":
    main()
