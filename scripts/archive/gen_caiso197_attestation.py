"""caiso-197 — governance attestation for the Wave-2 composed-rung promotion.

The `gen_caisoNNN` series continues (E10: an attestation is generated AT the
promotion, every premise computed, never typed — the caiso-189 lesson made
machinery at caiso-196). This generator writes the C6 governance attestation
for the close-out campaign's final accepted rung, refusing on any failed leg:

* **G-DELTA** — the rung's ``scenario_config`` differs from the campaign
  control on EXACTLY the accepted lanes' fields (computed over the full
  config; the composed ladder is the whole delta, nothing rides along).
* **G-EXTRACT** — both bundles' ``resolved_inputs`` record the SAME committed
  CAMPD extract sha: the campaign base never moved under the ladder (the
  Desert Star NV re-derive is deferred post-ladder by charter).
* **G-ENGAGE** — the composed mechanisms engaged, read off the committed
  hourly sidecars (CC_REGULAR/ST_GAS dispatch deltas + price zone-hours).
* **G-MACHINE** — the machine half of C6, using the scorer's own constants.
* **G-DOF** — the composed ledger equals the ARITHMETIC composition of the
  accepted lanes' ledger moves: lane 2 retires ``wefor_multiplier``
  (11/8 → 10/7); lanes 3 and 5 add cited inputs, no rows. The caiso-188
  import-tranche census row (``n_scalars`` 6) must be preserved.
* **G-EXC** — the incumbent keeper's exceptions carry with magnitudes
  RE-MEASURED on this bundle (caiso-189 §8.3; integration protocol §6).

Usage::

    python scripts/gen_caiso197_attestation.py [--arm results/calibration/caiso197_w2_r5] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts import calibration_verdict as cv  # noqa: E402

CONTROL = REPO / "results" / "calibration" / "caiso197_l2_control"
INCUMBENT = REPO / "results" / "calibration" / "caiso196_e1_elsegundo"
INCUMBENT_RUN_ID = "2026-08-15-caiso-196-e1-elsegundo"
YEARS = [2023, 2024, 2025]

# Expected composed config delta vs the campaign control, per rung id. The
# control's recorded config PREDATES caiso_ps_plant_params (absent ≡ default
# False by the cache-key identity), so its expected control-side value is
# None-from-absence, normalized below.
_EXPECTED_BY_RUNG = {
    "caiso197_w2_r3": {
        "wefor_multiplier": (0.7, 1.0),
        "wefor_residual": (None, 0.0),
        "wefor_residual_groups": (None, ["CC_REGULAR"]),
        "gas_st_wefor_base_override": (None, 0.1591),
    },
    "caiso197_w2_r5": {
        "wefor_multiplier": (0.7, 1.0),
        "wefor_residual": (None, 0.0),
        "wefor_residual_groups": (None, ["CC_REGULAR"]),
        "gas_st_wefor_base_override": (None, 0.1591),
        "caiso_ps_plant_params": (None, True),
    },
}

# Composed-ledger arithmetic: lane 2's retirement is the only ledger move.
LEDGER_N_ENTRIES = 10
LEDGER_N_RESIDUAL = 7
IMPORT_TRANCHE_ROW = "IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]"
IMPORT_TRANCHE_N_SCALARS = 6

ATTESTED_BY = (
    "caiso-197 close-out session (Wave-2 composed-rung promotion under "
    "caiso191-integration-protocol-2026-08-11.md §6 — C3a-blind structural "
    "superiority; gates computed by scripts/gen_caiso197_attestation.py)"
)


def _note(arm_name: str, expected: dict) -> str:
    fields = ", ".join(sorted(expected))
    return (
        f"PROMOTION ATTESTATION, generated at the caiso-197 Wave-2 promotion "
        f"(2026-08-16) for {arm_name} — the close-out campaign's final accepted "
        f"rung on the re-anchored caiso-196 base. THE COMPOSED DELTA IS THE "
        f"LADDER AND NOTHING ELSE (G-DELTA, computed over the full config): "
        f"{fields}. Every lane was accepted on its own pre-registered "
        f"structural gates BEFORE composition (lane 2: FINDING-caiso197-wefor-"
        f"rerun-2026-08-16.md, 4/4; lane 3: FINDING-caiso197-stgas-wefor-"
        f"2026-08-16.md, 5/5; lane 5: FINDING-caiso197-ps-physical-2026-08-16"
        f".md, 6/6), each with the campaign direction-hazard clause verbatim "
        f"and C3a never consulted. STRUCTURAL SUPERIORITY over the incumbent "
        f"({INCUMBENT_RUN_ID}): the fitted wefor_multiplier=0.7 (identification "
        f"'residual', ERCOT-derived, lineage >=52 solves) is RETIRED from the "
        f"ledger (11/8 -> 10/7); the ERCOT-fitted ST_GAS base 0.21 stops "
        f"governing CAISO (replaced by the GADS 2020-2024 Gas Primary EFORd "
        f"0.1591, cited document-and-table from CAISO's own EIA-860 census); "
        f"the unrestrained NP15 PS aggregate (fleet-average constants) is "
        f"replaced by six per-plant cited-physical parameterizations (PG&E "
        f"Helms deck, DWR Bulletin 132-22, USBR EWA EIS; zero MW added, "
        f"G-AGG exact). The extract sha is UNCHANGED control-vs-arm "
        f"(G-EXTRACT): the campaign base never moved under the ladder. LOYO "
        f"discharged by construction: zero fitted parameters anywhere in the "
        f"composed delta — the lane-2 value is the frozen caiso-187 record's "
        f"arithmetic identity (X_c >= 4.9x W in EVERY year singly), the "
        f"lane-3 value is a published 5-year class table x a static census, "
        f"and lane 5 is time-invariant plant physics; no in-sample gain "
        f"enters any identification, so the overfitting signature LOYO "
        f"exists to catch cannot be present on any split."
    )


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))


def _norm(v):
    if isinstance(v, (list, tuple, set, frozenset)):
        return sorted(str(x) for x in v)
    return v


def assert_composed_delta(arm: Path, expected: dict) -> dict:
    """G-DELTA — the rung differs from the control on exactly the ladder."""
    c = _cfg(CONTROL)["scenario_config"]
    a = _cfg(arm)["scenario_config"]
    diffs = {}
    for k in sorted(set(c) | set(a)):
        cv_, av = _norm(c.get(k)), _norm(a.get(k))
        if cv_ != av:
            diffs[k] = (cv_, av)
    exp = {k: (_norm(cv_), _norm(av)) for k, (cv_, av) in expected.items()}
    if diffs != exp:
        raise SystemExit(
            f"G-DELTA FAILED: composed diff {sorted(diffs)} != expected ladder "
            f"{sorted(exp)}; mismatches: "
            + json.dumps(
                {k: v for k, v in diffs.items() if exp.get(k) != v}, default=str
            )
        )
    return {"n_keys": len(set(c) | set(a)), "composed_fields": sorted(diffs)}


def assert_extract_provenance(arm: Path) -> dict:
    """G-EXTRACT — both bundles solved against the SAME committed extract."""
    out = {}
    for name, bundle in (("control", CONTROL), ("arm", arm)):
        ri = _cfg(bundle).get("resolved_inputs", {})
        ex = ri.get("campd_unit_outages") or {}
        if not ex.get("sha256"):
            raise SystemExit(
                f"G-EXTRACT FAILED: {bundle.name} resolved_inputs carries no "
                "campd_unit_outages sha record."
            )
        out[name] = ex
    sha_c = json.dumps(out["control"], sort_keys=True)
    sha_a = json.dumps(out["arm"], sort_keys=True)
    if sha_c != sha_a:
        raise SystemExit(
            "G-EXTRACT FAILED: control and arm record DIFFERENT extract "
            "provenance — the campaign base moved under the ladder."
        )
    return out


def assert_engaged(arm: Path) -> dict:
    """G-ENGAGE — the composed mechanisms ran, per committed sidecars."""
    per_year: dict[str, dict] = {}
    for year in YEARS:
        c_cls = pd.read_parquet(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
        a_cls = pd.read_parquet(arm / "hourly" / f"class_hourly_{year}.parquet")
        ccol = next(c for c in c_cls.columns if c in ("klass", "class", "plant_group"))
        mcol = next(c for c in c_cls.columns if c in ("mw", "gen_mw", "dispatch_mw"))
        deltas = {}
        for klass in ("CC_REGULAR", "ST_GAS"):
            c_k = float(c_cls[c_cls[ccol] == klass][mcol].sum())
            a_k = float(a_cls[a_cls[ccol] == klass][mcol].sum())
            deltas[klass] = round((a_k - c_k) / 1e6, 4)
        c_sys = pd.read_parquet(CONTROL / "hourly" / f"system_{year}.parquet")
        a_sys = pd.read_parquet(arm / "hourly" / f"system_{year}.parquet")
        pc = [c for c in c_sys.select_dtypes("number").columns if "price" in c]
        moved = int(((c_sys[pc] - a_sys[pc]).abs() > 1e-9).any(axis=1).sum())
        if moved == 0 and all(abs(d) < 1e-6 for d in deltas.values()):
            raise SystemExit(
                f"G-ENGAGE FAILED {year}: rung is bit-identical to the control."
            )
        per_year[str(year)] = {
            "class_delta_twh": deltas,
            "price_hours_moved": moved,
        }
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


def assert_ledger_composed(ledger: dict) -> dict:
    """G-DOF — the composed ledger equals the lanes' arithmetic composition."""
    got = (ledger.get("n_entries"), ledger.get("n_residual"))
    if got != (LEDGER_N_ENTRIES, LEDGER_N_RESIDUAL):
        raise SystemExit(
            f"G-DOF FAILED: composed ledger reads {got[0]}/{got[1]}, expected "
            f"{LEDGER_N_ENTRIES}/{LEDGER_N_RESIDUAL} (= incumbent 11/8 with the "
            "lane-2 wefor_multiplier retirement and NOTHING else)."
        )
    if any("wefor" in json.dumps(e).lower() for e in ledger.get("entries", [])):
        raise SystemExit(
            "G-DOF FAILED: a wefor row survives in the composed ledger — the "
            "lane-2 retirement did not compose."
        )
    row = next(
        (e for e in ledger.get("entries", []) if e.get("name") == IMPORT_TRANCHE_ROW),
        None,
    )
    if row is None or row.get("n_scalars") != IMPORT_TRANCHE_N_SCALARS:
        raise SystemExit(
            f"G-DOF FAILED: {IMPORT_TRANCHE_ROW} n_scalars "
            f"{None if row is None else row.get('n_scalars')!r} != "
            f"{IMPORT_TRANCHE_N_SCALARS} — the caiso-188 census repair must carry."
        )
    return {
        "n_entries": ledger["n_entries"],
        "n_residual": ledger["n_residual"],
        "import_tranches_n_scalars": row["n_scalars"],
    }


def _measured_records(run_id: str) -> dict[tuple[str, int], dict]:
    """The rung's own scored (criterion, year) records, gated rows only."""
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
        f"RE-MEASURED on {arm_name} at the caiso-197 promotion (2026-08-16), "
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
    ap = argparse.ArgumentParser(description="caiso-197 promotion attestation")
    ap.add_argument(
        "--arm",
        default="results/calibration/caiso197_w2_r5",
        help="the final accepted rung's bundle dir",
    )
    ap.add_argument("--run-id", default=None, help="the rung's dashboard run id")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    arm = REPO / args.arm if not Path(args.arm).is_absolute() else Path(args.arm)
    expected = _EXPECTED_BY_RUNG.get(arm.name)
    if expected is None:
        raise SystemExit(f"unknown rung {arm.name!r}: no expected ladder delta")
    run_id = args.run_id
    if run_id is None:
        ts = json.loads((arm / "meta.json").read_text())["timestamp"][:10]
        run_id = f"{ts}-{arm.name.replace('_', '-')}"

    existing_raw = (arm / "calibration_attestation.json").read_text(encoding="utf-8")
    existing = json.loads(existing_raw)
    ledger = existing["free_parameters"]

    delta = assert_composed_delta(arm, expected)
    print(
        f"OK  G-DELTA  : composed diff == the ladder "
        f"({', '.join(delta['composed_fields'])}) over {delta['n_keys']} keys"
    )

    assert_extract_provenance(arm)
    print("OK  G-EXTRACT: control and arm record IDENTICAL extract provenance")

    engage = assert_engaged(arm)
    for year, row in engage.items():
        print(
            f"OK  G-ENGAGE {year}: ΔCC {row['class_delta_twh']['CC_REGULAR']:+.3f} "
            f"/ ΔST_GAS {row['class_delta_twh']['ST_GAS']:+.3f} TWh, "
            f"{row['price_hours_moved']:,} price zone-hours moved"
        )

    cfg_blob = _cfg(arm)
    machine = assert_machine_gate_clean(cfg_blob)
    print(f"OK  G-MACHINE: outage_source={machine['outage_source']!r}, clean")

    dof = assert_ledger_composed(ledger)
    print(
        f"OK  G-DOF    : composed ledger {dof['n_entries']}/{dof['n_residual']}, "
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
            "note": _note(arm.name, expected),
        },
        "exceptions": exceptions,
        "free_parameters": ledger,
    }
    rendered = json.dumps(att, indent=2) + "\n"

    marker = '  "free_parameters": {'
    if existing_raw.count(marker) != 1 or rendered.count(marker) != 1:
        raise SystemExit("G-DOF FAILED: free_parameters block not locatable.")
    if rendered[rendered.index(marker) :] != existing_raw[existing_raw.index(marker) :]:
        raise SystemExit(
            "G-DOF FAILED: rendered free_parameters not byte-identical to disk."
        )
    print("OK  G-DOF    : free_parameters block byte-identical to the on-disk section")

    out = arm / "calibration_attestation.json"
    if args.dry_run:
        print(f"\nDRY RUN — would write {out.relative_to(REPO)}")
        return 0
    out.write_text(rendered, encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)} ({len(rendered):,} bytes)")
    print(f"  exceptions carried: {len(exceptions)} from {INCUMBENT_RUN_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
