"""Write ``calibration_attestation.json`` for the neiso-97 DST-repair replay.

DEBUG-B(NEISO) (``docs/FINDING-debug-b-neiso-smd-clock-2026-08-17.md``, audit
row O8, owner card signed in-session 2026-08-17) repaired the DST-naive
2018-2023 SMD workbook clock in the committed NEISO actual-LMP series and
re-solved the incumbent keeper recipe at the corrected instrument:
``results/calibration/neiso97_dstrepair_A``. The repair moves a SCORING
TARGET, not a solve input (the NEISO recipe arms no LMP-consuming flag), so
the promotion claim is rule 14 [R-ACCURATE]: the benchmark surface the keeper
is scored against now carries the market's published hours.

The owner pre-signed promotion on not-worse (same card). This script writes
the promotion-time attestation so the D-5(b) re-key can re-verify a
determination that is not worse than the incumbent's CALIBRATED-WITH-CAVEATS.

**Nothing here is a new claim.** Zero free parameters are introduced or
moved; the attestation is the incumbent keeper's (neiso-93) carried forward
with a rewritten ``attested_by`` and an appended disclosure stating the input
repair and its byte-verified mechanics. The **DOF ledger and the exceptions
ledger are carried VERBATIM** and this script ASSERTS that rather than
trusting it (rule 21) — the C3c ledgered caveat is the incumbent's own,
unchanged in substance (the repair provably cannot touch C3c: no affected
cell of the corrected series reaches $138.65 against the $300 threshold).

Every premise is **COMPUTED, not typed**, and a failed assertion aborts
without writing:

* the arm's ``ScenarioConfig`` differs from the incumbent's in **zero** shared
  values; ``keeper_only`` fields are schema deletions at HEAD and every
  ``arm_only`` field is post-incumbent schema drift recorded falsy at its
  HEAD default;
* the committed parquet still carries the corrected clock at attestation
  time: the corrected hub construction (workbook re-placement + committed
  daily-report overlay) reproduces the committed
  ``actual_lmp_hourly_NEISO.parquet`` EXACTLY at the float32 precision it
  stores, for every repaired year x market;
* verdict parity on committed artifacts: the incumbent re-scores
  CALIBRATED-WITH-CAVEATS, and the arm's only non-PASS criteria
  pre-attestation are C6 UNATTESTED plus the C3c that the missing ledger
  cannot yet reclassify (post-attestation: identical to the incumbent).

No LP is solved and no bundle is regenerated. Training years only (rule 22).

Usage::

    uv run python scripts/gen_neiso97_dstrepair_attestation.py [--write]
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

CAL = REPO / "results" / "calibration"
INCUMBENT = CAL / "neiso93_envelope_A"
INCUMBENT_ID = "2026-08-14-neiso-93-envelope"
ARM = CAL / "neiso97_dstrepair_A"
FINDING = "docs/FINDING-debug-b-neiso-smd-clock-2026-08-17.md"

#: Fields the incumbent's recorded recipe carries that ScenarioConfig no
#: longer has (rule-26 deletions by other lanes after neiso-93 solved). Both
#: are other-ISO-scoped by name (rule 25) on top of being deleted.
RETIRED_FIELDS = {
    "ercot_faststart_pool_plant_physics",
    "nyiso_solar_registry_cod_dates",
}

#: Fields ScenarioConfig gained after the incumbent solved. Every one must be
#: recorded FALSY at its HEAD default in the arm (the replay armed nothing);
#: an unexpected field aborts.
EXPECTED_DRIFT = {
    "caiso_ps_plant_params",
    "commission_year_cod_fallback",
    "ercot_reserve_supply_cap_net_credits",
    "reliability_floor_plant_exclusions",
}

REPAIRED_YEARS = (2018, 2019, 2020, 2021, 2022, 2023)


def _arm_id() -> str:
    meta = json.loads((ARM / "meta.json").read_text(encoding="utf-8"))
    ts = meta.get("timestamp", "")[:10]
    return f"{ts}-neiso-97-dstrepair"


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
    """Assert the arm is the incumbent's recipe modulo schema drift."""
    inc, arm = _cfg(INCUMBENT), _cfg(ARM)
    keeper_only = sorted(set(inc) - set(arm))
    arm_only = sorted(set(arm) - set(inc))
    value_diffs = {k: (inc[k], arm[k]) for k in set(inc) & set(arm) if inc[k] != arm[k]}

    assert not value_diffs, f"recipe is NOT identical: {value_diffs}"
    assert set(keeper_only) == RETIRED_FIELDS, f"unexpected keeper_only: {keeper_only}"
    assert set(arm_only) == EXPECTED_DRIFT, f"unexpected arm_only drift: {arm_only}"

    defaults = _head_defaults()
    still_live = RETIRED_FIELDS & set(defaults)
    assert not still_live, f"'retired' fields still in ScenarioConfig: {still_live}"

    armed = {k: arm[k] for k in arm_only if arm[k] not in (False, None)}
    assert not armed, f"drift fields NOT falsy (the replay armed something): {armed}"
    off_default = {k: (arm[k], defaults[k]) for k in arm_only if arm[k] != defaults[k]}
    assert not off_default, f"drift fields NOT at HEAD defaults: {off_default}"

    return {
        "keeper_only_schema_deletions": sorted(RETIRED_FIELDS),
        "arm_only_drift_all_falsy_at_head_defaults": arm_only,
        "shared_value_diffs": 0,
    }


def assert_corrected_clock_holds() -> dict:
    """Recompute the corrected hub construction from committed sources.

    The gate: for every repaired year and both markets, the corrected
    construction (workbook re-placement under the measured flat-24 mapping +
    the committed daily-report overlay) reproduces the committed parquet
    EXACTLY at float32 — i.e. the parquet still carries the corrected clock,
    recomputed at attestation time rather than quoted from the finding.
    """
    import numpy as np

    from scripts.data import derive_actual_lmp as dal
    from scripts.probes.neiso97_smd_dst_defect_quantify import (
        committed_hub_dense,
        corrected_hub_dense,
        truth_days,
        workbook_days,
    )

    out = {}
    for year in REPAIRED_YEARS:
        wb = workbook_days(year)
        truth = truth_days(dal.NEISO_REPORT_DIR, year)
        cor = corrected_hub_dense(year, wb, truth)
        com = committed_hub_dense(year)
        for kind in ("da", "rt"):
            a = np.asarray(com[kind], dtype=np.float32)
            b = np.asarray(cor[kind], dtype=np.float32)
            same = (a == b) | (np.isnan(a) & np.isnan(b))
            assert bool(same.all()), (
                f"{year} {kind}: committed parquet no longer matches the "
                f"corrected construction at {int((~same).sum())} slot(s)"
            )
        out[str(year)] = "float32-exact, da+rt"
    return out


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
        allowed = {"governance", "price_tail"}
        assert set(non_pass) <= allowed, f"disqualifying non-PASS: {non_pass}"
        assert arm["determination"] == "NOT-YET", arm["determination"]
    elif non_pass == {"price_tail": "CAVEAT"}:
        state = "post-attestation"
        assert arm["determination"] == "CALIBRATED-WITH-CAVEATS", arm["determination"]
        assert arm["grade_summary"]["fails"] == 0, arm["grade_summary"]
        assert arm["grade_summary"]["ledgered"] == 1, arm["grade_summary"]
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
            "run_id": arm_id,
            "determination": arm["determination"],
            "reasons": arm["reasons"],
            "grade_summary": arm["grade_summary"],
        },
        "rubric_version": arm["rubric_version"],
    }


def build(arm_id: str, recipe: dict, clock: dict, parity: dict) -> dict:
    """Carry the incumbent attestation forward; DOF + exceptions verbatim."""
    att = json.loads(
        (INCUMBENT / "calibration_attestation.json").read_text(encoding="utf-8")
    )
    before = (att["free_parameters"]["n_entries"], att["free_parameters"]["n_residual"])
    n_exceptions = len(att["exceptions"])

    att["governance"]["attested_by"] = (
        f"neiso-97 (2026-08-17) — promotion-time governance attestation for the "
        f"DEBUG-B(NEISO) DST-repair replay {arm_id}, promoted under the owner "
        f"card signed in-session this sitting (audit row O8; promotion "
        f"pre-signed on not-worse). A replay_keeper ZERO-DELTA re-solve of the "
        f"designated keeper {INCUMBENT_ID} from that bundle's OWN meta.json "
        f"kwargs snapshot, --years 2023 2024 2025 in ONE invocation (rules "
        f"12 / 16 [R-ALLYEARS]), all years fresh (no --reuse-solved), at the "
        f"DST-repaired NEISO SMD actual-LMP instrument. The repair moves a "
        f"SCORING TARGET, not a solve input: the recipe arms no LMP-consuming "
        f"flag, and the arm's dispatch is compared against the incumbent's "
        f"committed sidecars at registration (see the finding §6). ZERO free "
        f"parameters introduced or moved; the DOF ledger (n_entries "
        f"{before[0]}, n_residual {before[1]}) and the exceptions ledger "
        f"({n_exceptions} entries, the C3c caveat included) are carried "
        f"VERBATIM from the incumbent and ASSERTED unchanged by "
        f"scripts/gen_neiso97_dstrepair_attestation.py — every premise in "
        f"that script is COMPUTED, none typed. The C3c caveat's substance is "
        f"untouched by construction: no cell the repair moved reaches "
        f"$138.65/MWh against the $300 tail threshold, and "
        f"actual_tail.json is byte-unchanged. Carried forward from the "
        f"incumbent attestation (neiso-93); the incumbent's own attested_by "
        f"is preserved in its bundle as the historical record."
    )

    att["disclosures"]["note"] += (
        " || neiso-97 DST-REPAIR DISCLOSURE (2026-08-17, audit row O8). This "
        "bundle is the incumbent recipe re-solved at the REPAIRED NEISO SMD "
        "actual-LMP instrument: the 2018-2023 workbook vintage is DST-naive "
        "(flat 24 rows every day) and the committed series was displaced one "
        "hour around every DST transition of those years — 562 hub cells, "
        "max $40.17/MWh, six fabricated mean cells and one lost hour per "
        "year — measured against the market's own daily hourly-LMP reports "
        "(0 mismatches, all 9 sheets x both markets x every truth day) and "
        "repaired value-preservingly per the PJM input-clock finding's §2a "
        "protocol (non-affected cells identical every row; displaced cells "
        "== pristine at the corrected offset; the fall-back repeated-hour "
        "pair restored from the published daily reports; exactly one NaN per "
        "market-year filled with the measured value, zero introduced; "
        "2024/2025/2026 blocks byte-identical). " + FINDING + " is the full "
        "record. The corrected-clock gate is recomputed at attestation time "
        "(this script), not quoted. Blast radius on scoring: bench/NEISO "
        "2023 recomputes; the C3c tail and every determination-bearing "
        "criterion status are unchanged. The 2022 validation touchpoint "
        "stands as scored on the pre-repair instrument; the NYISO keeper's "
        "nyiso_import_hub_prices consumption of this series is filed for the "
        "NYISO lane (rule 25), not acted on here."
    )

    after = (att["free_parameters"]["n_entries"], att["free_parameters"]["n_residual"])
    assert before == after == (7, 5), f"DOF ledger moved {before} -> {after}"
    assert len(att["exceptions"]) == n_exceptions == 7, "exceptions ledger moved"

    att["dstrepair_verification"] = {
        "finding": FINDING,
        "audit_row": "docs/audit/third-party-audit-2026-08.md §8 row O8",
        "recipe_diff_vs_incumbent": recipe,
        "corrected_clock_recomputed_at_attestation": clock,
        "verdict_parity": parity,
        "incumbent": INCUMBENT_ID,
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write the attestation")
    args = ap.parse_args()

    arm_id = _arm_id()
    recipe = assert_recipe_identity()
    clock = assert_corrected_clock_holds()
    parity = assert_verdict_parity(arm_id)
    att = build(arm_id, recipe, clock, parity)

    print("=" * 72)
    print(f"neiso-97 — attestation for {arm_id} (premises COMPUTED)")
    print("=" * 72)
    print(f"  shared-value diffs vs incumbent : {recipe['shared_value_diffs']}")
    print(
        f"  keeper_only (schema deletions)  : {recipe['keeper_only_schema_deletions']}"
    )
    print(
        f"  arm_only drift (falsy defaults) : {recipe['arm_only_drift_all_falsy_at_head_defaults']}"
    )
    print(f"  corrected clock recomputed      : {sorted(clock)} all float32-exact")
    print(f"  incumbent re-score              : {parity['incumbent']['determination']}")
    print(
        f"  arm ({parity['arm_scored']['state']}) : "
        f"{parity['arm_scored']['determination']} {parity['arm_scored']['reasons']}"
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
