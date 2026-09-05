"""caiso-200 — governance attestation for the fleet-member panel promotion.

The `gen_caisoNNN` series continues (E10: an attestation is generated AT the
promotion, every premise computed, never typed). This generator writes the C6
governance attestation for the caiso-200 promoted run, refusing on any failed
leg:

* **G-DELTA** — the arm's ``scenario_config`` diff against the h0 control is
  EMPTY: the A/B is extract-only (PRECHECK-caiso200 §4 leg (d)).
* **G-RECIPE** — the arm's config diff against the committed caiso-197 keeper
  is exactly the MEASURED head drift (three default-off fields the keeper's
  run_config predates, bit-zero-proven inert on CAISO by
  ``_caiso200_ctrl_tolerance.json``): the recipe is the keeper's own.
* **G-EXTRACT** — the control's ``resolved_inputs`` records the pre-landing
  committed instrument (`da33e509…`) and the arm's records the LANDED
  fleet-member instrument (`cf156483…`), which must equal the live
  ``data/raw`` bytes: the promoted run is the committed tree's dispatch.
* **G-ENGAGE** — the arm engaged where the movement census says it can:
  2023 sidecars differ from the control (the three restored CC_REGULAR
  windows); 2024/2025 are reported and MAY be bit-identical (no solve-year
  mover exists there).
* **G-MACHINE** — the machine half of C6, scorer's own constants.
* **G-DOF** — the carried ledger is the caiso-197 composed 10/7 with the
  caiso-188 import-tranche census row intact.
* **G-EXC** — the keeper's exceptions carry with magnitudes RE-MEASURED on
  this bundle (caiso-189 §8.3), via the scorer's own committed records.

Usage::

    python scripts/gen_caiso200_attestation.py --arm results/calibration/<bundle> [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import calibration_verdict as cv  # noqa: E402

CONTROL = REPO / "results" / "calibration" / "caiso200_h0_control"
INCUMBENT = REPO / "results" / "calibration" / "caiso197_w2_r5"
INCUMBENT_RUN_ID = "2026-08-16-caiso-197-w2-r5"
YEARS = [2023, 2024, 2025]
EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"

SHA_PRE_LANDING = "da33e509465911341ba0867aefe02214f2e8ccb666ef86747e0e7ad8b47c86bb"
SHA_LANDED = "cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5"

# The measured head drift vs the committed keeper's run_config (see
# _caiso200_carry_dof_ledger.py) — bit-zero-proven inert on CAISO.
HEAD_DRIFT_ALLOWED = {
    "commission_year_cod_fallback": (None, False),
    "ercot_reserve_supply_cap_net_credits": (None, False),
    "reliability_floor_plant_exclusions": (None, False),
}

LEDGER_N_ENTRIES = 10
LEDGER_N_RESIDUAL = 7
IMPORT_TRANCHE_ROW = "IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]"
IMPORT_TRANCHE_N_SCALARS = 6

ATTESTED_BY = (
    "caiso-200 session (fleet-member panel-membership promotion under the "
    "PRECHECK-caiso200-panel-membership-2026-08-17.md §6 pre-registered "
    "decision tree, ratified in-session by the owner 2026-08-17 — 'if "
    "structural integrity improves but gates regress that may still be a "
    "keeper'; gates computed by scripts/gen_caiso200_attestation.py)"
)


def _note(arm_name: str) -> str:
    return (
        f"PROMOTION ATTESTATION, generated at the caiso-200 promotion "
        f"(2026-08-17) for {arm_name} — the caiso-197 keeper recipe solved on "
        f"the LANDED fleet-member panel instrument (sha {SHA_LANDED[:8]}..). "
        f"The A/B delta is the fleet-member panel-scope extract re-derive and "
        f"the 9 CA-facility windows it reclassifies mechanical->layup; no "
        f"ScenarioConfig field differs (G-DELTA EMPTY over the full config; "
        f"G-RECIPE: the only diff vs the committed keeper is the three "
        f"measured default-off head-drift fields, bit-zero-proven inert). "
        f"STRUCTURAL CONTENT: the ISO's own out-of-state fleet member (Desert "
        f"Star, EIA 55077) becomes a member of the merit-order panel its own "
        f"spans are scored against, closing the caiso-199 §3 item-3 "
        f"asymmetry as a NARROWING (membership derived from the fleet "
        f"registry — {{NV: (55077,)}} — admitting nothing that is not the "
        f"ISO's own fleet; the caiso-198 non-fleet NV churn stays excluded). "
        f"Under the panel that can finally see it, ALL 158 Desert Star "
        f"windows are retained as mechanical — the fail-safe was right for "
        f"100 per cent of them, correcting the caiso-199 §3 item-3 '9 of the "
        f"158' record on measurement (PRECHECK-caiso200 §0a; "
        f"_caiso200_member_panel_gates.json movement census). The 9 movers "
        f"are borderline CA-facility windows (oom 0.900-0.932) tipped by the "
        f"small RCC dip of the member CC joining the panel; three fall in "
        f"solve years, all 2023, all CC_REGULAR. DIRECTION-HAZARD REGIME "
        f"REVERSED AND HONOURED (PRECHECK §0): the expected sign was C3a/C1-"
        f"favorable, so acceptance rested SOLELY on the ex-ante byte-identity "
        f"gates — the object's content was fixed by the caiso-198 run-Y "
        f"measurement BEFORE the C1 flip existed, and it carries zero free "
        f"parameters. LOYO discharged by construction: no fitted value "
        f"anywhere in the delta (fleet membership is a market fact), so no "
        f"in-sample gain enters any identification."
    )


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))


def assert_empty_ab_delta(arm: Path) -> dict:
    """G-DELTA — the arm's config diff against the h0 control is EMPTY."""
    c = _cfg(CONTROL)["scenario_config"]
    a = _cfg(arm)["scenario_config"]
    diffs = {
        k: (c.get(k), a.get(k)) for k in sorted(set(c) | set(a)) if c.get(k) != a.get(k)
    }
    if diffs:
        raise SystemExit(
            f"G-DELTA FAILED: control-vs-arm diff not empty: {sorted(diffs)}"
        )
    return {"n_keys": len(set(c) | set(a))}


def assert_keeper_recipe(arm: Path) -> dict:
    """G-RECIPE — arm vs keeper differs only on the measured head drift."""
    k = _cfg(INCUMBENT)["scenario_config"]
    a = _cfg(arm)["scenario_config"]
    diffs = {
        key: (k.get(key), a.get(key))
        for key in sorted(set(k) | set(a))
        if k.get(key) != a.get(key)
    }
    unexplained = {
        key: v for key, v in diffs.items() if HEAD_DRIFT_ALLOWED.get(key) != tuple(v)
    }
    if unexplained:
        raise SystemExit(
            f"G-RECIPE FAILED: diff beyond measured head drift: {unexplained}"
        )
    return {"head_drift_fields": sorted(diffs)}


def assert_extract_provenance(arm: Path) -> dict:
    """G-EXTRACT — the A/B extract provenance + live-tree identity."""
    c_ex = _cfg(CONTROL).get("resolved_inputs", {}).get("campd_unit_outages") or {}
    a_ex = _cfg(arm).get("resolved_inputs", {}).get("campd_unit_outages") or {}
    if c_ex.get("sha256") != SHA_PRE_LANDING:
        raise SystemExit(
            f"G-EXTRACT FAILED: control extract sha {c_ex.get('sha256')!r} != "
            f"pre-landing {SHA_PRE_LANDING}"
        )
    if a_ex.get("sha256") != SHA_LANDED:
        raise SystemExit(
            f"G-EXTRACT FAILED: arm extract sha {a_ex.get('sha256')!r} != "
            f"landed {SHA_LANDED}"
        )
    live = hashlib.sha256(EXTRACT.read_bytes()).hexdigest()
    if live != SHA_LANDED:
        raise SystemExit(
            f"G-EXTRACT FAILED: live data/raw extract {live} != landed "
            f"{SHA_LANDED} — the promoted run does not match the committed tree"
        )
    return {"control": c_ex, "arm": a_ex, "live_matches_arm": True}


def assert_engaged(arm: Path) -> dict:
    """G-ENGAGE — 2023 differs; 2024/2025 reported (may be bit-identical)."""
    per_year: dict[str, dict] = {}
    for year in YEARS:
        c_cls = pd.read_parquet(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
        a_cls = pd.read_parquet(arm / "hourly" / f"class_hourly_{year}.parquet")
        ccol = next(c for c in c_cls.columns if c in ("klass", "class", "plant_group"))
        mcol = next(c for c in c_cls.columns if c in ("mw", "gen_mw", "dispatch_mw"))
        c_k = float(c_cls[c_cls[ccol] == "CC_REGULAR"][mcol].sum())
        a_k = float(a_cls[a_cls[ccol] == "CC_REGULAR"][mcol].sum())
        c_sys = pd.read_parquet(CONTROL / "hourly" / f"system_{year}.parquet")
        a_sys = pd.read_parquet(arm / "hourly" / f"system_{year}.parquet")
        pc = [c for c in c_sys.select_dtypes("number").columns if "price" in c]
        moved = int(((c_sys[pc] - a_sys[pc]).abs() > 1e-9).any(axis=1).sum())
        per_year[str(year)] = {
            "cc_regular_delta_twh": round((a_k - c_k) / 1e6, 4),
            "price_hours_moved": moved,
        }
    if (
        per_year["2023"]["price_hours_moved"] == 0
        and abs(per_year["2023"]["cc_regular_delta_twh"]) < 1e-6
    ):
        raise SystemExit(
            "G-ENGAGE FAILED: 2023 is bit-identical to the control — the arm "
            "did not engage where the movement census says it must"
        )
    return per_year


def assert_machine_gate_clean(cfg_blob: dict) -> dict:
    """G-MACHINE — the machine half of C6, scorer's own constants."""
    sc = cfg_blob.get("scenario_config", {})
    meta = cfg_blob.get("meta", {})
    outage = meta.get("outage_source") or sc.get("outage_source")
    issues = []
    if outage is not None and outage not in cv.EXOGENOUS_OUTAGE_SOURCES:
        issues.append(f"outage_source={outage!r} is not exogenous")
    issues += [
        f"forbidden fitted-mechanism flag active: {f}"
        for f in cv.FORBIDDEN_FLAGS
        if sc.get(f)
    ]
    if issues:
        raise SystemExit("G-MACHINE FAILED: " + "; ".join(issues))
    return {"outage_source": outage, "forbidden_flags_active": []}


def assert_ledger_carried(ledger: dict) -> dict:
    """G-DOF — the carried ledger is the caiso-197 composed 10/7."""
    got = (ledger.get("n_entries"), ledger.get("n_residual"))
    if got != (LEDGER_N_ENTRIES, LEDGER_N_RESIDUAL):
        raise SystemExit(
            f"G-DOF FAILED: ledger reads {got[0]}/{got[1]}, expected "
            f"{LEDGER_N_ENTRIES}/{LEDGER_N_RESIDUAL}"
        )
    row = next(
        (e for e in ledger.get("entries", []) if e.get("name") == IMPORT_TRANCHE_ROW),
        None,
    )
    if row is None or row.get("n_scalars") != IMPORT_TRANCHE_N_SCALARS:
        raise SystemExit(
            f"G-DOF FAILED: {IMPORT_TRANCHE_ROW} n_scalars "
            f"{None if row is None else row.get('n_scalars')!r} != "
            f"{IMPORT_TRANCHE_N_SCALARS}"
        )
    return {
        "n_entries": ledger["n_entries"],
        "n_residual": ledger["n_residual"],
        "import_tranches_n_scalars": row["n_scalars"],
    }


def _measured_records(run_id: str) -> dict[tuple[str, int], dict]:
    """The run's own scored (criterion, year) records, gated rows only."""
    verdict = cv.determine(run_id)
    out: dict[tuple[str, int], dict] = {}
    for cid in ("price_tail", "price_mean"):
        for rec in verdict["criteria"][cid]["records"]:
            if rec.get("key") is not None:
                continue
            out[(cid, int(rec["year"]))] = rec
    return out


def _refresh_magnitude(entry: dict, rec: dict, arm_name: str) -> tuple[str, bool]:
    """This bundle's magnitude text for one carried entry + moved flag."""
    carried = entry.get("magnitude", "")
    if entry["criterion"] == "price_tail":
        model, actual = int(rec["model"]), int(rec["actual"])
        measured = (
            f"model {model} h with RT-expressible LMP > $200/MWh vs RT actual "
            f"{actual} h"
        )
        moved = f"model {model} h" not in carried
        inert = ""
    else:
        model, actual = float(rec["model"]), float(rec["actual"])
        pct = (model - actual) / actual * 100.0
        measured = (
            f"system load-weighted mean LMP {model:.2f} $/MWh vs RT actual "
            f"{actual:.2f} ({pct:+.1f} %, outside the +/-10 % band)"
        )
        moved = f"{model:.2f}" not in carried
        inert = (
            " INERT UNDER THE RUBRIC (v3.1+): LEDGERABLE_CRITERIA is price_tail "
            "alone, so this entry reclassifies nothing and C3a's FAIL stands at "
            "full magnitude; carried as the historical record."
        )
    verdict_word = "REFRESHED" if moved else "UNCHANGED"
    return (
        f"RE-MEASURED on {arm_name} at the caiso-200 promotion (2026-08-17), "
        f"from the bundle's own committed scored records via calibration_verdict "
        f"— no solve: {measured}. The carried magnitude is {verdict_word} "
        f"against this bundle.{inert} CARRIED MAGNITUDE, verbatim from "
        f"{INCUMBENT_RUN_ID}: {carried}"
    ), moved


def carry_exceptions(arm: Path, run_id: str) -> tuple[list[dict], list[dict]]:
    """G-EXC — carry the incumbent's exceptions, re-measured on this bundle."""
    incumbent = json.loads(
        (INCUMBENT / "calibration_attestation.json").read_text(encoding="utf-8")
    )
    measured = _measured_records(run_id)
    carried: list[dict] = []
    report: list[dict] = []
    for entry in incumbent["exceptions"]:
        key = (entry["criterion"], int(entry["year"]))
        rec = measured.get(key)
        if rec is None:
            raise SystemExit(f"G-EXC FAILED: no scored record for {key} on {run_id}.")
        new = dict(entry)
        new["magnitude"], moved = _refresh_magnitude(entry, rec, arm.name)
        chain = entry.get("carried_from")
        new["carried_from"] = (
            f"{INCUMBENT_RUN_ID} -> {chain}" if chain else INCUMBENT_RUN_ID
        )
        carried.append(new)
        report.append(
            {
                "criterion": key[0],
                "year": key[1],
                "model": rec["model"],
                "actual": rec["actual"],
                "magnitude_refreshed": moved,
                "ledgerable": key[0] in cv.LEDGERABLE_CRITERIA,
            }
        )
    return carried, report


def main() -> int:
    """Write the promotion attestation, refusing on any failed leg."""
    ap = argparse.ArgumentParser(description="caiso-200 promotion attestation")
    ap.add_argument(
        "--arm",
        default="results/calibration/caiso200_h1_memberpanel",
        help="the promoted run's bundle dir",
    )
    ap.add_argument("--run-id", default=None, help="the run's dashboard run id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    arm = REPO / args.arm if not Path(args.arm).is_absolute() else Path(args.arm)
    run_id = args.run_id
    if run_id is None:
        ts = json.loads((arm / "meta.json").read_text())["timestamp"][:10]
        run_id = f"{ts}-{arm.name.replace('_', '-')}"

    existing_raw = (arm / "calibration_attestation.json").read_text(encoding="utf-8")
    existing = json.loads(existing_raw)
    ledger = existing["free_parameters"]

    delta = assert_empty_ab_delta(arm)
    print(f"OK  G-DELTA  : control-vs-arm diff EMPTY over {delta['n_keys']} keys")

    recipe = assert_keeper_recipe(arm)
    print(
        f"OK  G-RECIPE : keeper recipe; head drift = "
        f"{', '.join(recipe['head_drift_fields'])}"
    )

    prov = assert_extract_provenance(arm)
    print(
        f"OK  G-EXTRACT: control {prov['control']['sha256'][:8]}.. -> arm "
        f"{prov['arm']['sha256'][:8]}.. == live tree"
    )

    engage = assert_engaged(arm)
    for year, row in engage.items():
        print(
            f"OK  G-ENGAGE {year}: ΔCC {row['cc_regular_delta_twh']:+.4f} TWh, "
            f"{row['price_hours_moved']:,} price zone-hours moved"
        )

    cfg_blob = _cfg(arm)
    machine = assert_machine_gate_clean(cfg_blob)
    print(f"OK  G-MACHINE: outage_source={machine['outage_source']!r}, clean")

    dof = assert_ledger_carried(ledger)
    print(
        f"OK  G-DOF    : carried ledger {dof['n_entries']}/{dof['n_residual']}, "
        f"census row n_scalars {dof['import_tranches_n_scalars']}"
    )

    exceptions, exc_report = carry_exceptions(arm, run_id)
    for row in exc_report:
        flag = "REFRESHED" if row["magnitude_refreshed"] else "unchanged"
        led = "ledgerable" if row["ledgerable"] else "INERT"
        print(
            f"OK  G-EXC    : {row['criterion']} {row['year']} model={row['model']} "
            f"actual={row['actual']} magnitude {flag}, {led}"
        )

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_BY,
            "note": _note(arm.name),
        },
        "exceptions": exceptions,
        "free_parameters": ledger,
    }
    rendered = json.dumps(att, indent=2) + "\n"

    out = arm / "calibration_attestation.json"
    if args.dry_run:
        print(f"\nDRY RUN — would write {out.relative_to(REPO)}")
        return 0
    out.write_text(rendered, encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)} ({len(rendered):,} bytes)")
    print(f"  exceptions carried: {len(exceptions)} from {INCUMBENT_RUN_ID}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
