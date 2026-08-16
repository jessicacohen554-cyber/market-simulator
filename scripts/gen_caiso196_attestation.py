"""Write the C6 governance attestation for the caiso-196 e1 keeper promotion.

``results/calibration/caiso196_e1_elsegundo`` (run
``2026-08-15-caiso-196-e1-elsegundo``) is promoted CAISO keeper by explicit owner
decision (2026-08-16, in-session: "Is this a recommended keeper candidate? If so
plz promote. If structural integrity improves but gates regress that may still
be a keeper.."). Its bundle carries only the ``free_parameters`` DOF ledger
``build_dof_ledger.py`` writes, so ``calibration_verdict.score_governance``
reads C6 UNATTESTED — the caiso-188 gap caiso-189 repaired post-hoc, here closed
AT promotion instead (the ``gen_caisoNNN_attestation.py`` series resumes).

**NOTHING HERE IS A NEW CLAIM.** caiso-196 is a rule 14 ``[R-ACCURATE]``
measured-input repair: ZERO ScenarioConfig fields differ between the arms, ZERO
DOF added; the delta is the (330 → 57901) El Segundo CEMS-history remap and the
+233 strictly-additive extract rows it adds. The governance assertions restate
the promotion record (`FINDING-caiso196-elsegundo-remap-2026-08-15.md`); the
exceptions are the incumbent caiso-188 keeper's, carried with
``classification``/``reason`` byte-identical and ``magnitude`` RE-MEASURED on
this bundle (the caiso-189 §8.3 rule).

Every premise is **COMPUTED, not typed**, and a failed leg aborts without
writing:

* **G-DELTA** — the arm's ``scenario_config`` differs from its paired control
  ``caiso196_e0_control`` in EXACTLY ZERO keys (the "no config lever moved"
  claim, proved);
* **G-EXTRACT** — the data delta is proven from each bundle's OWN
  ``resolved_inputs`` block (the caiso-190 provenance machinery, first used in
  anger here): the control solved against the committed pre-repair extract
  (sha256 ``25360e90…``) and this bundle against the repaired one
  (``5f3e35c5…``), both recorded at resolution time;
* **G-ENGAGE** — the repair engaged, read off the committed hourly sidecars:
  CC_REGULAR class dispatch differs between the arms in every year and system
  prices move in tens of thousands of zone-hours;
* **G-MACHINE** — the machine half of C6, evaluated with
  ``calibration_verdict``'s OWN constants;
* **G-DOF** — the DOF ledger is carried BYTE-IDENTICAL, still ``n_entries`` 11 /
  ``n_residual`` 8 with the caiso-188 census's ``n_scalars: 6`` on the
  ``IMPORT_TRANCHES`` row;
* **G-EXC** — every carried exception's ``magnitude`` is re-measured against
  this bundle's own scored records, quoting the carried text verbatim.

No LP is solved, no bundle regenerated, no data file touched. Training years
only (rule 22 ``[R-HOLDOUT]``).

Usage::

    python scripts/gen_caiso196_attestation.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

import scripts.calibration_verdict as cv  # noqa: E402

CAL = REPO / "results" / "calibration"
ARM = CAL / "caiso196_e1_elsegundo"
CONTROL = CAL / "caiso196_e0_control"
INCUMBENT = CAL / "caiso188_d1_micseam"

RUN_ID = "2026-08-15-caiso-196-e1-elsegundo"
INCUMBENT_RUN_ID = "2026-08-09-caiso-188-d1-micseam"
YEARS = (2023, 2024, 2025)

#: The pre-repair / repaired extract shas (PRECHECK-caiso196 §2; commit e68a70d).
COMMITTED_EXTRACT_SHA = (
    "25360e90a9d11f32c293edf3224047da0d6fab447b551fac81b983e2da1166c6"
)
REPAIRED_EXTRACT_SHA = (
    "5f3e35c5dad88da76be8f684973fd7c78009f63e84d3f5b23a609e93d45fb4ce"
)

#: G-DOF totals — caiso-196 adds no free parameter (both bundles measured 11/8).
LEDGER_N_ENTRIES, LEDGER_N_RESIDUAL = 11, 8
IMPORT_TRANCHE_ROW = "IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]"
IMPORT_TRANCHE_N_SCALARS = 6

ATTESTED_BY = (
    "caiso-196 promotion (2026-08-16): GOVERNANCE ATTESTATION WRITTEN AT THE "
    "PROMOTION ITSELF (the gen_caisoNNN_attestation.py series resumes after the "
    "caiso-188/189 gap). PROMOTED BY EXPLICIT OWNER DECISION, in-session verbatim: "
    "'Is this a recommended keeper candidate? If so plz promote. If structural "
    "integrity improves but gates regress that may still be a keeper..' — the "
    "owner adopting the rule-14/caiso-183 posture for exactly this arm, whose "
    "FINDING (section 5) had escalated the decision. THE ATTESTED SUBSTANCE IS "
    "THE caiso-196 PROMOTION RECORD, restated not re-derived: the (330 -> 57901) "
    "El Segundo CEMS-history remap repair. The 2013 El Segundo Energy Center CTs "
    "file CEMS under the fully-retired legacy steam ORIS 330 as units '5'/'7'; "
    "campd.CAMPD_UNIT_PLANT_REMAP carried the two sibling repowers (315 -> 62115 "
    "Alamitos, 335 -> 62116 Huntington Beach) but never El Segundo, so the outage "
    "derivation skipped facility 330 before detection and the keeper solved a "
    "537.4 MW CC_REGULAR plant with NO measured outage overlay. The repair adds "
    "two remap entries and re-derives the extract 2018-2026 with the committed "
    "recipe; the baseline was FIRST re-proven byte-identical (sha 25360e90..) at "
    "head with the edit stashed, so the remap is the only free variable, and the "
    "diff is +233 strictly-additive facility-57901 rows (units 5/7: 112/121, zero "
    "removed; layup companion window-set unchanged at 810). ZERO ScenarioConfig "
    "fields differ between the arms (G-DELTA below, computed); ZERO DOF added "
    "(G-DOF below, byte-carried at 11/8). THE COMPENSATING ERROR THIS REMOVES, "
    "measured per plant: the control (bit-zero identical to the caiso-188 keeper) "
    "dispatched the mostly-idle El Segundo at 3.265/3.245/2.746 TWh in 2023/24/25 "
    "against its measured CEMS gross of 0.169/0.192/0.053 TWh (19x/17x/52x); the "
    "repaired arm dispatches 0.694/0.636/0.087 TWh (1.6-4x). GATES REGRESS AND "
    "THE PROMOTION SAYS SO PLAINLY (the owner's clause covers exactly this): C1 "
    "fuel-mix flips PASS -> FAIL on ONE row, 2023 CC_REGULAR, e0 -3.57 TWh/-1.5pp "
    "(PASS at the band edge) -> e1 -4.44 TWh/-1.9pp — adjudicated ACCEPT-WITH-FLIP "
    "under integration-protocol section 5 (the input survives re-examination: no "
    "mis-citation, no coverage failure, no classifier deviation; the flip is the "
    "model reacting to accurate data, and what becomes visible is the KNOWN "
    "caiso-121/135/140-B over-import residual the phantom 3.2 TWh was masking). "
    "C3a moves ANTI-favorably, +3.4/+10.4/+12.9 -> +4.4/+11.7/+14.5 % — the "
    "pre-registered expected sign of an accuracy repair (direction-hazard clause; "
    "C3a was never consulted). C3b stays PASS all years (0.077/0.155/0.176). "
    "LOYO (rule 22 standing clause, protocol section 6) IS DISCHARGED "
    "BY CONSTRUCTION: the mechanism carries ZERO fitted parameters, the detector "
    "is per-year-independent, the remap is a static registry-identity fact "
    "(EIA-860 generator IDs 5/7 = CAMPD unit IDs), and there is NO in-sample gain "
    "anywhere (every headline metric moves anti-favorably), so the overfitting "
    "signature LOYO exists to catch — in-sample gain with held-out degradation — "
    "cannot be present on any leave-one-year-out split. Record: "
    "FINDING-caiso196-elsegundo-remap-2026-08-15.md (+ its promotion addendum), "
    "PRECHECK-caiso196-elsegundo-remap-2026-08-15.md (committed c80670d BEFORE "
    "any solve), commit e68a70d (the repair, byte-verified)."
)

NOTE = (
    "BASIS OF THIS ATTESTATION, stated plainly. It reflects the caiso-196 "
    "promotion record and is generated AT the promotion by the promoting session "
    "under the owner's explicit decision. The four assertions above rest on: "
    "(1) ZERO DOF ADDED — no ScenarioConfig field differs between the arms "
    "(G-DELTA, computed over the full config), no fitted scalar is introduced, "
    "and the ledger is carried byte-identical at 11/8 (G-DOF); the repair adds "
    "MEASURED DATA (a CEMS-observed plant's own outage record), not freedom. "
    "(2) LEVERS TRACE TO MEASURED INPUT more strongly after this promotion than "
    "before it: a 537.4 MW plant previously carried only the statistical WEFOR "
    "guess (x0.7 multiplier) while its measured windows sat unread on disk under "
    "a legacy ORIS; the repaired extract routes them through the SHIPPED loader "
    "(outages.unit_outage_derate_factors), and each bundle's resolved_inputs "
    "block — the caiso-190 provenance machinery — records WHICH extract the LP "
    "actually solved against (G-EXTRACT: control 25360e90.., this bundle "
    "5f3e35c5..), so an armed-but-inert repeat of the caiso-188 defect class is "
    "excluded by committed bytes. (3) NO FIT TO PRICE RESIDUALS and NO PINNING "
    "TO ACTUALS: the expected sign was pre-registered ANTI-C3a-favorable and "
    "measured so (+1.0/+1.3/+1.6 pp); PRECHECK-caiso196 section 0 bound the "
    "session to accept the repair regardless of fit direction, and no price was "
    "read before the PRECHECK and repair were committed and pushed. (4) OUTAGE "
    "FILTER EXOGENOUS: outage_source='historic', the CAMPD measured-outage "
    "overlay, checked below against calibration_verdict.EXOGENOUS_OUTAGE_SOURCES "
    "rather than asserted; the merit-order guard ran with its shipped frozen "
    "constants and classified ZERO El Segundo spans as layup (the fail-safe "
    "retaining ambiguous spans as mechanical — caiso-192 G-CONS behaviour). THE "
    "EXCEPTIONS BELOW ARE THE INCUMBENT'S, NOT NEW ONES: all four are carried "
    "from 2026-08-09-caiso-188-d1-micseam (which itself carried them from "
    "2026-08-09-caiso-184-c1-lpbasis) with classification and reason "
    "BYTE-IDENTICAL; this session creates no caveat and spends no ledger slot. "
    "Their magnitude fields ARE refreshed on THIS bundle's own scored records, "
    "quoting the carried text verbatim alongside (a carried magnitude measured "
    "on a superseded bundle is its own governance defect — caiso-189 section "
    "8.3, now the rule). Under rubric v3.1+ LEDGERABLE_CRITERIA is price_tail "
    "alone, so the two carried price_mean entries reclassify NOTHING and C3a's "
    "FAIL stands at full magnitude; the NEW C1-2023 FAIL is load-bearing, not "
    "ledgerable, receives NO invented entry, and stands at full magnitude as "
    "the ACCEPT-WITH-FLIP record requires."
)


def _cfg(bundle: Path) -> dict:
    """Return one bundle's recorded ``scenario_config``."""
    data = json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))
    return data.get("scenario_config", data)


def assert_zero_config_delta() -> dict:
    """G-DELTA — the arm differs from its control on exactly ZERO config keys."""
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = sorted(k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k))
    if diff:
        raise SystemExit(
            f"G-DELTA FAILED: scenario_config differs on {diff}, expected NO "
            "difference — a config lever moved and the 'data-only delta' claim "
            "is not attestable."
        )
    return {"differing_keys": [], "n_keys": len(a_cfg)}


def assert_extract_provenance() -> dict:
    """G-EXTRACT — each bundle's resolved_inputs records the right extract."""
    out: dict[str, dict] = {}
    for bundle, want, tag in (
        (CONTROL, COMMITTED_EXTRACT_SHA, "control"),
        (ARM, REPAIRED_EXTRACT_SHA, "arm"),
    ):
        rc = json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))
        blk = rc.get("resolved_inputs", {}).get("campd_unit_outages", {})
        got = blk.get("sha256")
        if got != want:
            raise SystemExit(
                f"G-EXTRACT FAILED: {bundle.name} resolved_inputs records extract "
                f"sha {got!r}, expected {want!r} — the bundle did not solve "
                "against the extract this attestation claims."
            )
        if not blk.get("armed") or not blk.get("present"):
            raise SystemExit(
                f"G-EXTRACT FAILED: {bundle.name} extract not armed/present in "
                "resolved_inputs — the overlay did not run."
            )
        out[tag] = {"sha256": got[:16] + "…", "bytes": blk.get("bytes")}
    return out


def assert_engaged() -> dict:
    """G-ENGAGE — CC_REGULAR dispatch and system prices differ, per committed sidecars."""
    per_year: dict[str, dict] = {}
    for year in YEARS:
        c_cls = pd.read_parquet(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
        a_cls = pd.read_parquet(ARM / "hourly" / f"class_hourly_{year}.parquet")
        ccol = next(c for c in c_cls.columns if c in ("klass", "class", "plant_group"))
        mcol = next(c for c in c_cls.columns if c in ("mw", "gen_mw", "dispatch_mw"))
        c_cc = float(c_cls[c_cls[ccol] == "CC_REGULAR"][mcol].sum())
        a_cc = float(a_cls[a_cls[ccol] == "CC_REGULAR"][mcol].sum())
        d_twh = (a_cc - c_cc) / 1e6
        c_sys = pd.read_parquet(CONTROL / "hourly" / f"system_{year}.parquet")
        a_sys = pd.read_parquet(ARM / "hourly" / f"system_{year}.parquet")
        pc = [c for c in c_sys.select_dtypes("number").columns if "price" in c]
        moved = int(((c_sys[pc] - a_sys[pc]).abs() > 1e-9).any(axis=1).sum())
        if abs(d_twh) < 1e-6 and moved == 0:
            raise SystemExit(
                f"G-ENGAGE FAILED {year}: arm is bit-identical to control — the "
                "repair is INERT and the promotion claim is false."
            )
        per_year[str(year)] = {
            "cc_regular_delta_twh": round(d_twh, 4),
            "price_hours_moved": moved,
        }
    return per_year


def assert_machine_gate_clean(cfg_blob: dict) -> dict:
    """G-MACHINE — the machine half of C6, using the scorer's own constants."""
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
        raise SystemExit(
            "G-MACHINE FAILED: " + "; ".join(issues) + " — the machine cross-check "
            "trips, so C6 would read FAIL and no attestation may be written."
        )
    return {"outage_source": outage, "forbidden_flags_active": [], "machine_issues": []}


def assert_ledger_preserved(ledger: dict) -> dict:
    """G-DOF — the carried ledger still reads the incumbent totals."""
    got = (ledger.get("n_entries"), ledger.get("n_residual"))
    if got != (LEDGER_N_ENTRIES, LEDGER_N_RESIDUAL):
        raise SystemExit(
            f"G-DOF FAILED: ledger reads {got[0]}/{got[1]}, expected "
            f"{LEDGER_N_ENTRIES}/{LEDGER_N_RESIDUAL} — caiso-196 adds no free "
            "parameter, so a move is a defect this session must not paper over."
        )
    row = next(
        (e for e in ledger.get("entries", []) if e.get("name") == IMPORT_TRANCHE_ROW),
        None,
    )
    if row is None:
        raise SystemExit(f"G-DOF FAILED: ledger has no {IMPORT_TRANCHE_ROW!r} row.")
    if row.get("n_scalars") != IMPORT_TRANCHE_N_SCALARS:
        raise SystemExit(
            f"G-DOF FAILED: {IMPORT_TRANCHE_ROW} carries n_scalars "
            f"{row.get('n_scalars')!r}, expected {IMPORT_TRANCHE_N_SCALARS} — the "
            "caiso-188 census repair is not present in this ledger."
        )
    return {
        "n_entries": ledger["n_entries"],
        "n_residual": ledger["n_residual"],
        "import_tranches_n_scalars": row["n_scalars"],
    }


def _measured_records() -> dict[tuple[str, int], dict]:
    """This bundle's own scored (criterion, year) records, gated rows only."""
    verdict = cv.determine(RUN_ID)
    out: dict[tuple[str, int], dict] = {}
    for cid in ("price_tail", "price_mean"):
        for rec in verdict["criteria"][cid]["records"]:
            if rec.get("key") is not None:  # skip the DA report-only companions
                continue
            out[(cid, int(rec["year"]))] = rec
    return out


def _refresh_magnitude(entry: dict, rec: dict) -> tuple[str, bool]:
    """Return this bundle's magnitude text for one carried entry, and whether it moved."""
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
            " INERT UNDER RUBRIC v3.1: LEDGERABLE_CRITERIA is price_tail alone, so "
            "this entry reclassifies nothing and C3a's FAIL stands at full "
            "magnitude; it is carried as the historical record."
        )
    verdict_word = "REFRESHED" if moved else "UNCHANGED"
    return (
        f"RE-MEASURED on caiso196_e1_elsegundo at the caiso-196 promotion "
        f"(2026-08-16), from the bundle's own committed scored records via "
        f"calibration_verdict — no solve: {measured}. The carried magnitude is "
        f"{verdict_word} against this bundle.{inert} CARRIED MAGNITUDE, verbatim "
        f"from {INCUMBENT_RUN_ID}: {carried}"
    ), moved


def carry_exceptions() -> tuple[list[dict], list[dict]]:
    """G-EXC — carry the incumbent's exceptions, re-measured on this bundle."""
    incumbent = json.loads(
        (INCUMBENT / "calibration_attestation.json").read_text(encoding="utf-8")
    )
    measured = _measured_records()
    carried: list[dict] = []
    report: list[dict] = []
    for entry in incumbent["exceptions"]:
        key = (entry["criterion"], int(entry["year"]))
        rec = measured.get(key)
        if rec is None:
            raise SystemExit(
                f"G-EXC FAILED: no scored record for {key} on {RUN_ID} — an "
                "exception cannot be carried onto a bundle that does not measure it."
            )
        new = dict(entry)  # classification / reason / ledgered_by kept verbatim
        new["magnitude"], moved = _refresh_magnitude(entry, rec)
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
    """Write the keeper's governance attestation, refusing on any failed leg."""
    ap = argparse.ArgumentParser(description="caiso-196 promotion attestation")
    ap.add_argument(
        "--dry-run", action="store_true", help="run every leg but write nothing"
    )
    args = ap.parse_args()

    existing_raw = (ARM / "calibration_attestation.json").read_text(encoding="utf-8")
    existing = json.loads(existing_raw)
    if set(existing) != {"free_parameters"}:
        print(
            f"NOTE: attestation already carries {sorted(existing)} — re-running is "
            "idempotent (free_parameters is preserved, the rest is rewritten)."
        )
    ledger = existing["free_parameters"]

    delta = assert_zero_config_delta()
    print(f"OK  G-DELTA  : arms differ on ZERO of {delta['n_keys']} config keys")

    prov = assert_extract_provenance()
    print(
        f"OK  G-EXTRACT: control solved on {prov['control']['sha256']} "
        f"({prov['control']['bytes']:,} B), arm on {prov['arm']['sha256']} "
        f"({prov['arm']['bytes']:,} B) — resolved_inputs, recorded at solve time"
    )

    engage = assert_engaged()
    for year, row in engage.items():
        print(
            f"OK  G-ENGAGE {year}: CC_REGULAR {row['cc_regular_delta_twh']:+.3f} TWh, "
            f"{row['price_hours_moved']:,} price zone-hours moved"
        )

    cfg_blob = json.loads((ARM / "run_config.json").read_text(encoding="utf-8"))
    machine = assert_machine_gate_clean(cfg_blob)
    print(
        f"OK  G-MACHINE: outage_source={machine['outage_source']!r}, no forbidden flags"
    )

    dof = assert_ledger_preserved(ledger)
    print(
        f"OK  G-DOF    : ledger {dof['n_entries']}/{dof['n_residual']}, "
        f"{IMPORT_TRANCHE_ROW} n_scalars {dof['import_tranches_n_scalars']}"
    )

    exceptions, exc_report = carry_exceptions()
    for row in exc_report:
        flag = "REFRESHED" if row["magnitude_refreshed"] else "unchanged"
        led = "ledgerable" if row["ledgerable"] else "INERT (v3.1)"
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
            "note": NOTE,
        },
        "exceptions": exceptions,
        "free_parameters": ledger,
    }
    rendered = json.dumps(att, indent=2) + "\n"

    marker = '  "free_parameters": {'
    if existing_raw.count(marker) != 1 or rendered.count(marker) != 1:
        raise SystemExit(
            "G-DOF FAILED: free_parameters block not locatable for byte diff."
        )
    if rendered[rendered.index(marker) :] != existing_raw[existing_raw.index(marker) :]:
        raise SystemExit(
            "G-DOF FAILED: the rendered free_parameters block is not byte-identical "
            "to the on-disk one — the DOF ledger must be carried, never rewritten."
        )
    print("OK  G-DOF    : free_parameters block byte-identical to the on-disk section")

    out = ARM / "calibration_attestation.json"
    if args.dry_run:
        print(
            f"\nDRY RUN — would write {out.relative_to(REPO)} ({len(rendered):,} bytes)"
        )
        return 0
    out.write_text(rendered, encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)} ({len(rendered):,} bytes)")
    print(f"  top-level keys: {sorted(att)}")
    print(f"  exceptions carried: {len(exceptions)} from {INCUMBENT_RUN_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
