"""Write ``calibration_attestation.json`` for the neiso-99 joint arm.

neiso-99 settles the two standing NEISO owner escalations in ONE re-solve
(``results/calibration/PREREG-neiso99-p2basis-routing-2026-08-17.md``;
``ASSESSMENT-neiso98-frontier-verification-2026-08-17.md`` §4.1/§4.2):

* **audit row O5** — the incumbent is the only keeper of six that runs, and is
  SCORED ON, the archived P2 commitment pass. The candidate moves the recipe
  onto the production P1 basis (``commitment=false``), which CLAUDE.md
  "Dispatch & Commitment" says every run is scored on.
* **the Stony Brook 6081 routing defect** — a liquid-fuel combustion turbine's
  outage window was routed into a sibling GAS bin, derating a 305.1 MW combined
  cycle by 48.7 % of the 2024 and 56.0 % of the 2025 capacity-year on machines
  that are not in it. Rule 14 ``[R-ACCURATE]``.

**Nothing here is a new claim, and ZERO free parameters are introduced or
moved.** The DOF ledger and the exceptions ledger are carried from the
incumbent and this script ASSERTS that rather than trusting it (rule 21): 7
DOF entries / 5 residual, 7 exceptions, the same criterion set. The routing
guard is a predicate over a CLOSED CAMPD fuel vocabulary, not a fitted value;
the basis change REMOVES a solve pass rather than adding a knob.

**One inherited text defect IS repaired here, deliberately.** All 7 exception
entries open by attributing the carry-forward to *caiso-159* — reported by
neiso-98 §5, which declined to repair it because editing a REGISTERED run's
evidence record would falsify what that run asserted at its own promotion.
That reason does not apply to a NEW attestation for a NEW run, and the
sentence's substance is true of neiso-99 verbatim (an input correction with
zero free parameters, spending no new slot). The repair is asserted to be the
attribution token and NOTHING else: entry count, criterion set, and every
other character of every entry are checked unchanged.

Every premise is **COMPUTED, not typed**, and a failed assertion aborts
without writing:

* the candidate's ``ScenarioConfig`` differs from the incumbent's in EXACTLY
  the one intended value (``commitment`` True → False) and in nothing else;
* the archived pass is genuinely gone — the candidate persists ``["P1"]``
  where the incumbent persists ``["P1","P2"]``;
* the basis change is a pure RE-RENDER, not a different solve: the
  basis-only arm's hourly sidecars are BIT-IDENTICAL to the incumbent's own
  persisted P1 in every year (P2 runs after P1 and cannot move it);
* the routing repair still holds in the committed extract at attestation
  time: ZERO NEISO rows remain in which a CAMPD unit whose own ``unitType``
  is a combustion turbine and whose own ``primaryFuelInfo`` is liquid-only
  sits in a non-CT bin;
* verdict parity on committed artifacts: the incumbent re-scores
  CALIBRATED-WITH-CAVEATS, and the candidate's only non-PASS criteria
  pre-attestation are C6 UNATTESTED plus the C3c the missing ledger cannot
  yet reclassify.

No LP is solved and no bundle is regenerated. Training years only (rule 22).

Usage::

    uv run python scripts/gen_neiso99_attestation.py [--write]
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
INCUMBENT = CAL / "neiso97_dstrepair_A"
INCUMBENT_ID = "2026-08-17-neiso-97-dstrepair"
BASIS_ARM = CAL / "neiso99_basis_A"
ARM = CAL / "neiso99_joint_B"
PREREG = "results/calibration/PREREG-neiso99-p2basis-routing-2026-08-17.md"

#: The ONE intended recipe delta: the archived-P2 pass, disarmed. It lives in
#: the bundle's ``meta.json`` solve-kwarg snapshot, NOT in ``ScenarioConfig``
#: (``commitment`` is a solve_and_persist parameter), so the two grains are
#: asserted separately: the ScenarioConfig must differ in NOTHING at all.
INTENDED_META_DELTA = {"commitment": (True, False)}

#: Fields ScenarioConfig gained after the incumbent solved (here: the MISO
#: wefor lane's, landed between neiso-97's solve and this HEAD). Every one must
#: be recorded FALSY at its HEAD default in the candidate — i.e. the replay
#: armed nothing new — and an unexpected field aborts.
EXPECTED_DRIFT: set[str] = {"summer_wefor_share_override"}

#: The mis-attributed session token in every inherited exception entry, and
#: its repair. See the module docstring.
ATTRIB_WRONG = "caiso-159 promotes an INPUT CORRECTION"
ATTRIB_RIGHT = "neiso-99 promotes an INPUT CORRECTION"

YEARS = (2023, 2024, 2025)


def _arm_id(bundle: Path, shorthand: str) -> str:
    meta = json.loads((bundle / "meta.json").read_text(encoding="utf-8"))
    return f"{meta.get('timestamp', '')[:10]}-{shorthand}"


def _cfg(bundle: Path) -> dict:
    data = json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))
    return data.get("scenario_config", data)


def _head_defaults() -> dict:
    from market_sim.config.scenarios import ScenarioConfig

    out = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.default is not dataclasses.MISSING:
            out[f.name] = f.default
        elif f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            out[f.name] = f.default_factory()  # type: ignore[misc]
    return out


def assert_recipe_identity() -> dict:
    """Assert the candidate's ScenarioConfig is the incumbent's, unchanged.

    The intended delta is a SOLVE KWARG, not a config field, so at this grain
    the correct assertion is that NOTHING moved — every armed mechanism stays
    armed and unchanged, and no mechanism-matrix cell verdict can move
    (rule 28d). :func:`assert_intended_meta_delta` carries the other grain.
    """
    inc, arm = _cfg(INCUMBENT), _cfg(ARM)
    keeper_only = sorted(set(inc) - set(arm))
    arm_only = sorted(set(arm) - set(inc))
    value_diffs = {k: (inc[k], arm[k]) for k in set(inc) & set(arm) if inc[k] != arm[k]}

    assert not value_diffs, f"ScenarioConfig is NOT identical: {value_diffs}"
    assert not keeper_only, f"unexpected keeper_only: {keeper_only}"
    assert set(arm_only) == EXPECTED_DRIFT, f"unexpected arm_only drift: {arm_only}"

    defaults = _head_defaults()
    armed = {k: arm[k] for k in arm_only if arm[k] not in (False, None)}
    assert not armed, f"drift fields NOT falsy (the replay armed something): {armed}"
    off_default = {k: (arm[k], defaults[k]) for k in arm_only if arm[k] != defaults[k]}
    assert not off_default, f"drift fields NOT at HEAD defaults: {off_default}"
    return {
        "scenario_config_shared_value_diffs": 0,
        "keeper_only": keeper_only,
        "arm_only_drift_all_falsy_at_head_defaults": arm_only,
    }


#: ``meta.json`` keys that are provenance rather than recipe, and are EXPECTED
#: to differ between any two solves of the same recipe. ``shared_inputs`` is
#: excluded here only because it gets its OWN, stricter assertion
#: (:func:`assert_only_the_outage_inputs_moved`) — it is never waved through.
_META_PROVENANCE = {
    "timestamp",
    "run_dir",
    "note",
    "passes",
    "reuse",
    "ablation_of",
    "basis_sha",
    "git_sha",
    "shared_inputs",
}

#: Solve-kwarg keys the snapshot schema gained after the incumbent solved.
#: Each must be recorded FALSY in the candidate (the replay armed nothing);
#: both are other-ISO-scoped by name on top of being falsy (rule 25).
EXPECTED_META_DRIFT = {"ercot_ordc_adder_family_counterpart"}


def assert_intended_meta_delta() -> dict:
    """Assert the meta-grain recipe delta is EXACTLY ``commitment`` True → False.

    ``meta.json`` is the authoritative snapshot of every ``solve_and_persist``
    kwarg (it is what a replay reconstructs from), so this is the grain at
    which the basis change is expressible — and the grain at which a second,
    unintended delta would hide.
    """
    inc = json.loads((INCUMBENT / "meta.json").read_text(encoding="utf-8"))
    arm = json.loads((ARM / "meta.json").read_text(encoding="utf-8"))
    keys = (set(inc) | set(arm)) - _META_PROVENANCE
    diffs = {
        k: (inc.get(k, "<absent>"), arm.get(k, "<absent>"))
        for k in keys
        if inc.get(k, "<absent>") != arm.get(k, "<absent>")
    }
    drift = {k: v for k, v in diffs.items() if k in EXPECTED_META_DRIFT}
    armed = {k: v for k, v in drift.items() if v[1] not in (False, None)}
    assert not armed, f"schema-drift kwargs NOT falsy in the candidate: {armed}"
    real = {k: v for k, v in diffs.items() if k not in EXPECTED_META_DRIFT}
    assert real == INTENDED_META_DELTA, (
        f"meta deltas are not exactly the intended one: {real}"
    )
    return {
        "delta": {k: {"incumbent": v[0], "candidate": v[1]} for k, v in real.items()},
        "schema_drift_all_falsy": sorted(drift),
        "keys_compared": len(keys),
        "provenance_keys_excluded": sorted(_META_PROVENANCE),
    }


#: The content-addressed shared-input keys the routing repair is ALLOWED to
#: move: the re-derived CAMPD unit-outage extract and its layup companion.
OUTAGE_INPUT_KEYS = {"unit_outages", "unit_outages_layup"}


def assert_only_the_outage_inputs_moved() -> dict:
    """Assert the ONLY measured input that changed is the outage extract pair.

    ``meta.json``'s ``shared_inputs`` records each resolved input as a
    CONTENT-ADDRESSED path, so this is a hash-level proof rather than an
    argument: every other input the solve consumed — EIA-930, EIA-923, CAMPD,
    and the short / partial / e923 outage companions — must be byte-identical
    between the incumbent and the candidate.
    """
    inc = json.loads((INCUMBENT / "meta.json").read_text(encoding="utf-8"))
    arm = json.loads((ARM / "meta.json").read_text(encoding="utf-8"))
    a, b = inc.get("shared_inputs", {}), arm.get("shared_inputs", {})
    assert set(a) == set(b), f"shared_inputs key set moved: {set(a) ^ set(b)}"
    moved = sorted(k for k in a if a[k] != b[k])
    assert set(moved) == OUTAGE_INPUT_KEYS, (
        f"inputs moved beyond the outage extract pair: {moved}"
    )
    return {
        "inputs_compared": len(a),
        "moved": {k: {"incumbent": a[k], "candidate": b[k]} for k in moved},
        "unchanged": sorted(k for k in a if a[k] == b[k]),
    }


def _passes(bundle: Path, year: int) -> list[str]:
    import pandas as pd

    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return sorted(df["pass"].unique().tolist())


def assert_p2_is_gone() -> dict:
    """Assert the candidate persists only P1 where the incumbent persisted P2."""
    out = {}
    for y in YEARS:
        inc, arm = _passes(INCUMBENT, y), _passes(ARM, y)
        assert inc == ["P1", "P2"], f"{y}: incumbent passes {inc}, expected P1+P2"
        assert arm == ["P1"], f"{y}: candidate passes {arm}, expected P1 only"
        out[str(y)] = {"incumbent": inc, "candidate": arm}
    return out


def assert_basis_change_is_a_pure_rerender() -> dict:
    """Assert the basis-only arm reproduces the incumbent's own P1 to the bit.

    P2 runs AFTER P1, so disarming it cannot move P1. Measuring that rather
    than asserting it is what makes the basis arm separable from the routing
    arm: any nonzero cell here would mean the archived pass feeds back into the
    production one, which is a finding in its own right.
    """
    import numpy as np
    import pandas as pd

    out = {}
    for y in YEARS:
        per_file = {}
        for name in ("system", "class_hourly", "reserve_family"):
            a = pd.read_parquet(BASIS_ARM / "hourly" / f"{name}_{y}.parquet")
            b = pd.read_parquet(INCUMBENT / "hourly" / f"{name}_{y}.parquet")
            a = a[a["pass"] == "P1"].drop(columns=["pass"]).reset_index(drop=True)
            b = b[b["pass"] == "P1"].drop(columns=["pass"]).reset_index(drop=True)
            assert a.shape == b.shape, f"{y} {name}: shape {a.shape} vs {b.shape}"
            num = a.select_dtypes("number").columns
            diff = a[num].to_numpy(float) - b[num].to_numpy(float)
            ndiff = int((diff != 0).sum())
            assert ndiff == 0, f"{y} {name}: {ndiff} differing cells — P2 moved P1"
            per_file[name] = {"rows": int(len(a)), "differing_cells": 0}
            assert float(np.abs(diff).max()) == 0.0
        out[str(y)] = per_file
    return out


def assert_routing_repair_holds() -> dict:
    """Recompute the routing invariant over the COMMITTED extract.

    The property the guard guarantees, recomputed from committed sources at
    attestation time rather than quoted from the finding: NO row of
    ``campd-unit-outages-NEISO.csv`` carries a unit whose own CAMPD
    ``unitType`` is a combustion turbine and whose own ``primaryFuelInfo`` is
    liquid-only into a non-CT ``plant_group``.
    """
    import pandas as pd

    from market_sim.config.paths import RAW_DATA_DIR
    from market_sim.data import campd
    from scripts.data.derive_campd_unit_outages import _is_liquid_only_fuel

    attrs: dict[tuple[int, str], dict] = {}
    for st in campd.states_for_iso("NEISO"):
        for y in range(2018, 2027):
            f = RAW_DATA_DIR / "campd-unit-level" / f"{st}_{y}.parquet"
            if not f.exists():
                continue
            df = pd.read_parquet(
                f, columns=["facilityId", "unitId", "unitType", "primaryFuelInfo"]
            ).drop_duplicates()
            for r in df.itertuples(index=False):
                attrs[(int(r.facilityId), str(r.unitId))] = {
                    "ut": str(r.unitType),
                    "fuel": str(r.primaryFuelInfo),
                }

    ext = pd.read_csv(RAW_DATA_DIR / "campd-unit-outages-NEISO.csv")
    offenders: dict[str, int] = {}
    for r in ext.itertuples(index=False):
        a = attrs.get((int(r.facility_id), str(r.unit_id)))
        if a is None:
            continue
        grp = str(r.plant_group)
        if (
            "combustion turbine" in a["ut"].strip().lower()
            and _is_liquid_only_fuel(a["fuel"])
            and not grp.startswith("CT")
        ):
            offenders[f"{r.facility_id}:{r.unit_id}->{grp}"] = (
                offenders.get(f"{r.facility_id}:{r.unit_id}->{grp}", 0) + 1
            )
    assert not offenders, f"liquid-fuel CT rows still in a gas bin: {offenders}"
    return {
        "extract_rows": int(len(ext)),
        "campd_units_resolved": len(attrs),
        "liquid_fuel_ct_rows_in_a_non_ct_bin": 0,
    }


def assert_verdict_parity(arm_id: str) -> dict:
    """Score both runs on committed artifacts; assert the promotion premises."""
    from scripts import calibration_verdict as cv

    inc = cv.determine_from_artifacts(INCUMBENT_ID, cv.load_artifacts(INCUMBENT_ID))
    arm = cv.determine_from_artifacts(arm_id, cv.load_artifacts(arm_id))

    assert inc["determination"] == "CALIBRATED-WITH-CAVEATS", (
        f"incumbent re-scores {inc['determination']!r} — baseline dead; stop"
    )
    inc_np = {
        cid: c["status"] for cid, c in inc["criteria"].items() if c["status"] != "PASS"
    }
    assert inc_np == {"price_tail": "CAVEAT"}, f"incumbent non-PASS set moved: {inc_np}"

    non_pass = {
        cid: c["status"] for cid, c in arm["criteria"].items() if c["status"] != "PASS"
    }
    if non_pass.get("governance") == "UNATTESTED":
        state = "pre-attestation"
        assert set(non_pass) <= {"governance", "price_tail"}, (
            f"disqualifying non-PASS: {non_pass}"
        )
        assert arm["determination"] == "NOT-YET", arm["determination"]
    elif non_pass == {"price_tail": "CAVEAT"}:
        state = "post-attestation"
        assert arm["determination"] == "CALIBRATED-WITH-CAVEATS", arm["determination"]
        assert arm["grade_summary"]["fails"] == 0, arm["grade_summary"]
        assert arm["grade_summary"]["ledgered"] == 1, arm["grade_summary"]
    else:
        raise AssertionError(f"candidate has disqualifying non-PASS: {non_pass}")
    assert not arm["data_blocked_years"], arm["data_blocked_years"]
    return {
        "incumbent": {
            "run_id": INCUMBENT_ID,
            "determination": inc["determination"],
            "grade_summary": inc["grade_summary"],
        },
        "arm_scored": {
            "state": state,
            "run_id": arm_id,
            "determination": arm["determination"],
            "reasons": arm["reasons"],
            "grade_summary": arm["grade_summary"],
        },
        "rubric_version": arm["rubric_version"],
    }


def _repair_attribution(exceptions: list[dict]) -> int:
    """Repair the inherited caiso-159 attribution; assert nothing else moves."""
    n = 0
    for e in exceptions:
        reason = e.get("reason", "")
        if ATTRIB_WRONG not in reason:
            continue
        fixed = reason.replace(ATTRIB_WRONG, ATTRIB_RIGHT)
        # The ONLY permitted change is the attribution token itself.
        assert fixed.replace(ATTRIB_RIGHT, ATTRIB_WRONG) == reason, (
            "attribution repair changed more than the token"
        )
        e["reason"] = fixed
        n += 1
    return n


def build(arm_id: str, basis_id: str, evidence: dict) -> dict:
    """Carry the incumbent attestation forward; DOF + exceptions asserted."""
    att = json.loads(
        (INCUMBENT / "calibration_attestation.json").read_text(encoding="utf-8")
    )
    before = (att["free_parameters"]["n_entries"], att["free_parameters"]["n_residual"])
    n_exceptions = len(att["exceptions"])
    criteria_before = [e.get("criterion") for e in att["exceptions"]]

    n_repaired = _repair_attribution(att["exceptions"])

    att["governance"]["attested_by"] = (
        f"neiso-99 (2026-08-17) — promotion-time governance attestation for "
        f"{arm_id}, the JOINT arm that settles the two standing NEISO owner "
        f"escalations in ONE re-solve so they are not confounded (audit row O5 "
        f"and the Stony Brook 6081 outage routing; "
        f"ASSESSMENT-neiso98-frontier-verification-2026-08-17.md §4.1/§4.2). "
        f"A replay_keeper re-solve of the designated keeper {INCUMBENT_ID} from "
        f"that bundle's OWN meta.json kwargs snapshot, --years 2023 2024 2025 "
        f"in ONE invocation (rules 12 / 16 [R-ALLYEARS]), all years fresh (no "
        f"--reuse-solved), with EXACTLY ONE ScenarioConfig delta — commitment "
        f"True -> False, i.e. the recipe moved OFF the archived P2 pass and "
        f"onto the production P1 basis every other ISO's keeper already uses "
        f"and that CLAUDE.md 'Dispatch & Commitment' says every run is scored "
        f"on — and one MEASURED INPUT correction, the liquid-fuel "
        f"combustion-turbine routing guard in the CAMPD unit-outage extract. "
        f"THE TWO ARE DECOMPOSED, NOT CONFLATED: the basis-only arm {basis_id} "
        f"was solved at the same HEAD on the pre-fix extract and is "
        f"BIT-IDENTICAL to the incumbent's own persisted P1 in every hourly "
        f"sidecar of every year (asserted here, not assumed), so the basis "
        f"change is a pure RE-RENDER and every difference between the two arms "
        f"is the routing repair. ZERO free parameters introduced or moved: the "
        f"routing guard is a predicate over a CLOSED CAMPD fuel vocabulary and "
        f"the basis change REMOVES a solve pass. The DOF ledger (n_entries "
        f"{before[0]}, n_residual {before[1]}) and the exceptions ledger "
        f"({n_exceptions} entries, the C3c caveat included) are carried from "
        f"the incumbent and ASSERTED unchanged in count, criterion set and "
        f"text by scripts/gen_neiso99_attestation.py — every premise in that "
        f"script is COMPUTED, none typed. THE ONE DELIBERATE TEXT REPAIR: "
        f"{n_repaired} exception entries attributed their carry-forward to "
        f"'caiso-159', an inherited defect neiso-98 §5 reported but could not "
        f"repair without falsifying a REGISTERED run's evidence record; a NEW "
        f"attestation for a NEW run is the right place, the sentence's "
        f"substance is true of neiso-99 verbatim, and the repair is asserted "
        f"to be the attribution token and nothing else. Prereg {PREREG}, "
        f"pushed before either arm solved."
    )

    att["disclosures"]["note"] += (
        " || neiso-99 JOINT DISCLOSURE (2026-08-17, audit row O5 + the Stony "
        "Brook routing defect). (1) THE SCORING BASIS MOVES OFF THE ARCHIVED "
        "P2 PASS. The incumbent was the only keeper of six that ran, and was "
        "RENDERED FROM, P2; this run persists ['P1'] alone. The effect on the "
        "means is small (mean lambda -0.0575 / -0.0110 / -0.0378 $/MWh for "
        "2023/2024/2025) but the 2024 ANNUAL MAXIMUM of the max-across-zones "
        "price moves $256.93 -> $218.24, i.e. P2 was standing 17.7 % above P1 "
        "on that statistic. That is a PRICE-FORMATION statistic and it is "
        "reported at full magnitude, not tuned around. (2) THE OUTAGE "
        "ROUTING REPAIR. _resolve_unit_group's fac_group short-circuit was a "
        "pjm-75 conservatism, not a physical claim, and it handed a "
        "liquid-fuel combustion turbine's outage window to a sibling gas bin: "
        "plant 6081 Stony Brook's two Diesel Oil CTs (83 MW each, 74 windows "
        "each) derated a 305.1 MW combined cycle they are not in for 48.7 % of "
        "the 2024 and 56.0 % of the 2025 capacity-year — years in which the CC "
        "units 001/002/003 have no windows of their own at all. Three further "
        "NEISO plants are affected (1595 Kendall S6, 568 Bridgeport BHB4, 1588 "
        "Mystic MJ-1). The discriminator is the unit's OWN primaryFuelInfo and "
        "NOT unitType, measured: across all six ISOs 35 CAMPD units filed "
        "'Combustion turbine' sit in a non-CT bin and 27 are GAS-fired members "
        "of a genuine block that must keep inheriting it. Extract diff, exact: "
        "3,189 -> 2,932 rows, 0 added, 257 dropped = 236 the fix + 21 "
        "reclassified standard->layup in 2019/2020/2026 only, the latter "
        "reproduced by a PRE-FIX control re-derivation at HEAD and therefore "
        "ambient drift, not this change; within 2023-2025 the ONLY change is "
        "the 236 rows and all 2,932 surviving rows are byte-identical on every "
        "column. (3) THE ROUTING ARM'S DISPATCH EFFECT IS DOMINATED BY KENDALL, "
        "NOT STONY BROOK, WHICH REFUTES THE PREREG'S OWN P3 EXPECTATION AND IS "
        "REPORTED AS SUCH: restoring 6081's availability barely moves its "
        "dispatch because that block's heat rate 10.6062 sits above 97.5 % of "
        "NEISO's CC_REGULAR capacity (cap-weighted p50 7.340) — it is deep out "
        "of merit whether or not it is available, the same fact neiso-83 "
        "measured at the same plant. (4) CROSS-ISO, FILED NOT ACTED ON (rule "
        "25 [R-ISO-SCOPE]): the same guard would drop mis-routed rows at PJM "
        "593 Edge Moor 10, MISO 2001 New Ulm 7 and 8056 Waterford 4, and NYISO "
        "2516 Northport UGT001. Only NEISO's extract is re-derived here; those "
        "are their lanes' calls. (5) THE REPLAY SEAM IS CLOSED IN THE SAME "
        "CHANGE: run_replay_bundle and replay_keeper.main rebuilt their kwargs "
        "from meta.json AFTER the CLI's P2 gate ran, so commitment=true "
        "re-armed the archived pass invisibly on every replay — which is how "
        "it propagated across three keeper generations with no operator "
        "decision. enforce_legacy_p2_kwargs now gates the RECONSTRUCTED recipe "
        "at both entry points and HARD-FAILS rather than silently rewriting it."
    )

    after = (att["free_parameters"]["n_entries"], att["free_parameters"]["n_residual"])
    assert before == after == (7, 5), f"DOF ledger moved {before} -> {after}"
    assert len(att["exceptions"]) == n_exceptions == 7, "exceptions ledger moved"
    assert [e.get("criterion") for e in att["exceptions"]] == criteria_before, (
        "exceptions criterion set moved"
    )

    att.pop("dstrepair_verification", None)
    att["neiso99_verification"] = {
        "prereg": PREREG,
        "audit_row": "docs/audit/third-party-audit-2026-08.md §8 row O5",
        "incumbent": INCUMBENT_ID,
        "basis_only_arm": basis_id,
        "attribution_entries_repaired": n_repaired,
        **evidence,
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write the attestation")
    args = ap.parse_args()

    arm_id = _arm_id(ARM, "neiso-99-joint-p1")
    basis_id = _arm_id(BASIS_ARM, "neiso-99-basis-p1")
    evidence = {
        "recipe_diff_vs_incumbent": assert_recipe_identity(),
        "intended_meta_delta": assert_intended_meta_delta(),
        "only_the_outage_inputs_moved": assert_only_the_outage_inputs_moved(),
        "persisted_passes": assert_p2_is_gone(),
        "basis_change_is_pure_rerender": assert_basis_change_is_a_pure_rerender(),
        "routing_invariant_recomputed": assert_routing_repair_holds(),
    }
    evidence["verdict_parity"] = assert_verdict_parity(arm_id)
    att = build(arm_id, basis_id, evidence)

    print("=" * 72)
    print(f"neiso-99 — attestation for {arm_id} (premises COMPUTED)")
    print("=" * 72)
    rd = evidence["recipe_diff_vs_incumbent"]
    print(
        "  ScenarioConfig deltas vs incumbent : "
        f"{rd['scenario_config_shared_value_diffs']}"
    )
    print(
        f"  intended meta delta                : {evidence['intended_meta_delta']['delta']}"
    )
    print(f"  persisted passes (candidate)       : {evidence['persisted_passes']}")
    print("  basis arm vs incumbent P1          : 0 differing cells, every year")
    print(
        f"  routing invariant                  : {evidence['routing_invariant_recomputed']}"
    )
    print(
        f"  incumbent re-score                 : {evidence['verdict_parity']['incumbent']['determination']}"
    )
    print(
        f"  candidate ({evidence['verdict_parity']['arm_scored']['state']}) : "
        f"{evidence['verdict_parity']['arm_scored']['determination']} "
        f"{evidence['verdict_parity']['arm_scored']['reasons']}"
    )
    if args.write:
        out = ARM / "calibration_attestation.json"
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE {out}")
    else:
        print("(dry run — pass --write to write the attestation)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
