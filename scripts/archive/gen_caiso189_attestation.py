"""Write the C6 governance attestation the caiso-188 promotion shipped without.

``results/calibration/caiso188_d1_micseam`` is the CAISO keeper
(``2026-08-09-caiso-188-d1-micseam``), but its ``calibration_attestation.json``
carries **only** a ``free_parameters`` DOF ledger — the file
``scripts/build_dof_ledger.py`` writes. Every CAISO promotion before it shipped a
bespoke ``scripts/gen_caisoNNN_attestation.py`` that added the ``schema`` /
``governance`` / ``exceptions`` blocks; the series stops at ``caiso-184``,
because the owner promoted caiso-188 in the same session that wrote its FINDING
and nobody wrote the generator.

Two rubric consequences follow from that ONE missing block, and they are the only
reason this script exists:

* ``calibration_verdict.score_governance`` reads **C6 UNATTESTED** — "a bundle
  whose attestation carries no governance block is exactly as unattested as one
  with no file" — which alone forces ``NOT-YET``;
* the incumbent keeper's C3c exceptions never carried forward, so the keeper's
  ``ledger_entries`` is ``[]`` and its two failing C3c years read as undocumented
  FAILs. (The owner's C3c standing rule cannot cover them either: it requires a
  passing governance gate AND a lone failure, and C3a fails here.)

**PRECEDENT.** ``scripts/gen_pjm153_collapse_attestation.py`` did exactly this for
``pjm152_collapse_A``, which shipped its bundle and gate record but never its
attestation. Post-hoc generation is a bookkeeping repair, not a new claim.

**NOTHING HERE IS A NEW CLAIM.** caiso-188 is a rule 14 ``[R-ACCURATE]`` seam-cap
provenance repair: ZERO DOF added, ONE ``ScenarioConfig`` flag flipped
(``capacity_deliverability_limits``), whose Part A resolves the seam limit through
the published branch-group Maximum Import Capability partition instead of the
fitted 7,500 MW ``WECC_import_simultaneous`` scalar. The governance assertions
restate that promotion record; the exceptions are the incumbent's, carried with
their ``classification``/``reason`` byte-identical and their ``magnitude``
RE-MEASURED on this bundle; the DOF ledger is preserved byte-for-byte.

Every premise is **COMPUTED, not typed**, and a failed leg aborts without writing:

* **G-DELTA** — the arm's ``scenario_config`` differs from its paired control
  ``caiso188_d0_control`` in EXACTLY ONE key, ``capacity_deliverability_limits``
  (False -> True). That is the "one flag flipped, zero DOF added" claim, proved
  rather than asserted;
* **G-SEAM** — Part A actually RESOLVED, read off each arm's own committed
  ``hourly/network_<year>.parquet``: the control's simultaneous-import group sits
  at the fitted 7,500.0 MW limit and binds, while this bundle's carries the
  published per-year MIC and its dual is EXACTLY 0.0 in every hour of every year.
  A bundle whose Part A silently no-oped could not pass this;
* **G-MACHINE** — the machine half of C6, evaluated with
  ``calibration_verdict``'s OWN constants so the generator cannot drift from the
  gate it is feeding: exogenous outage source, no forbidden fitted-mechanism flag;
* **G-DOF** — the DOF ledger is carried BYTE-IDENTICAL (the rendered
  ``free_parameters`` block of the written file must equal the on-disk block
  byte-for-byte), and still reads ``n_entries`` 11 / ``n_residual`` 8 with the
  caiso-188 repair's ``n_scalars: 6`` on the ``IMPORT_TRANCHES`` row;
* **G-EXC** — every carried exception's ``magnitude`` is re-measured against this
  bundle's own scored records. A carried magnitude measured on a superseded
  bundle is itself a governance defect, so the refreshed text states this
  bundle's value AND quotes the carried one verbatim.

No LP is solved, no bundle is regenerated, no data file is touched. Training
years only (rule 22 ``[R-HOLDOUT]``).

Usage::

    python scripts/gen_caiso189_attestation.py [--dry-run]
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
ARM = CAL / "caiso188_d1_micseam"
CONTROL = CAL / "caiso188_d0_control"
INCUMBENT = CAL / "caiso184_c1_lpbasis"

RUN_ID = "2026-08-09-caiso-188-d1-micseam"
INCUMBENT_RUN_ID = "2026-08-09-caiso-184-c1-lpbasis"
YEARS = (2023, 2024, 2025)

#: The ONE ScenarioConfig key the promoted arm may differ from its control on.
DELTA_KEY = "capacity_deliverability_limits"

#: The simultaneous-import interface group whose limit Part A replaces. Its name
#: is the signed member list, so it identifies the constraint without a magic id.
SEAM_GROUP = "grp:+WECC_PNW>NP15+WECC_DSW>SP15_rest"

#: The fitted ``WECC_import_simultaneous`` scalar Part A retires (iso_configs.py
#: labels it "a fitted scalar"; the DOF ledger carries it as a residual row).
FITTED_SEAM_CAP_MW = 7500.0

#: PRECHECK-caiso188 §G-DOF. caiso-188 adds no free parameter; the census only
#: RE-COUNTS an existing row (7 -> 6 scalars) and rewrites two ``root_cause``
#: texts, so both totals must be exactly the incumbent's.
LEDGER_N_ENTRIES, LEDGER_N_RESIDUAL = 11, 8
IMPORT_TRANCHE_ROW = "IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]"
IMPORT_TRANCHE_N_SCALARS = 6

ATTESTED_BY = (
    "caiso-189 (2026-08-11): POST-HOC GOVERNANCE ATTESTATION FOR THE caiso-188 "
    "PROMOTION, WHICH SHIPPED WITHOUT ONE. This is a BOOKKEEPING REPAIR AND NOT A "
    "NEW CLAIM: no LP was solved, no bundle regenerated, no data file or "
    "ScenarioConfig default touched. The owner promoted "
    "2026-08-09-caiso-188-d1-micseam in the same session that wrote "
    "FINDING-caiso188-import-tranche-dof-2026-08-09.md, after that finding's own "
    "text had already been written on the pre-promotion assumption that the "
    "keeper would not change; the bespoke gen_caisoNNN_attestation.py every CAISO "
    "promotion ships was therefore never written, and the series stops at "
    "caiso-184. The gap is MECHANICAL and it is the SOLE cause of two rubric "
    "readings on this keeper: C6 scored UNATTESTED (score_governance treats a "
    "free_parameters-only attestation as exactly as unattested as no file at "
    "all), and the incumbent's C3c exceptions never carried forward, leaving "
    "ledger_entries empty. PRECEDENT: gen_pjm153_collapse_attestation.py did the "
    "same for pjm152_collapse_A, which likewise shipped its bundle and gate "
    "record without its attestation. THE ATTESTED SUBSTANCE IS THE caiso-188 "
    "PROMOTION RECORD, restated, not re-derived: caiso-188 is the SEAM-CAP "
    "PROVENANCE REPAIR, a rule-14 [R-ACCURATE] / rule-1 [R-STRUCT] correction "
    "with ZERO free parameters and ZERO fitted scalars ADDED, which REMOVES a "
    "residual-identified fitted scalar from the binding path. The keeper's own "
    "run_config recorded capacity_deliverability_limits: true while Part A "
    "silently no-oped through a gitignored clean partition no solve auto-builds, "
    "so the baked 7,500 MW WECC_import_simultaneous cap -- which iso_configs.py "
    "itself labels 'a fitted scalar' and the DOF ledger carries as a RESIDUAL row "
    "reading 'Not in the keeper binding path' -- governed every CAISO run from "
    "caiso-175 onward. The rule-14 falsification is measured from the same "
    "EIA-930 bytes the corridor envelopes are built from: the real CAISO system "
    "exceeded 7,500 MW of net import in 271/293/681 hours of 2023/24/25, reaching "
    "13,136/13,312/15,080 MW, all inside the published MIC. WHAT THIS GENERATOR "
    "PROVES RATHER THAN ASSERTS, each computed from committed bytes: G-DELTA -- "
    "the arm differs from its paired control 2026-08-09-caiso-188-d0-control in "
    "EXACTLY ONE ScenarioConfig key, capacity_deliverability_limits False -> "
    "True; G-SEAM -- Part A ACTUALLY RESOLVED, read off each arm's own "
    "hourly/network_<year>.parquet: the control's simultaneous-import group sits "
    "at the fitted 7,500.0 MW limit and binds, while this bundle carries the "
    "published per-year branch-group MIC and its dual is EXACTLY 0.0 in every "
    "hour of every year; G-MACHINE -- the machine half of C6 evaluated with "
    "calibration_verdict's OWN constants; G-DOF -- the ledger carried "
    "BYTE-IDENTICAL at n_entries 11 / n_residual 8 with the census's n_scalars 6 "
    "on the IMPORT_TRANCHES row. NOTHING ABOUT THE MODEL'S FIT CHANGES AND NONE "
    "IS CLAIMED: C3a mean LMP remains the sole load-bearing FAIL at "
    "+3.4/+10.4/+12.9 % against a +/-10 % band, the determination remains NOT-YET, "
    "and the named open root cause is unchanged -- the WALLED hourly "
    "pumped-storage water state (FINDING-caiso140 §B / caiso-141 A2), an "
    "owner-funded intake and not a session lever. Record: "
    "FINDING-caiso189-c6-attestation-2026-08-11.md."
)

NOTE = (
    "BASIS OF THIS ATTESTATION, stated plainly. It reflects the caiso-188 "
    "promotion record -- FINDING-caiso188-import-tranche-dof-2026-08-09.md, "
    "PRECHECK-caiso188-mic-seam-2026-08-09.md and the committed probe outputs "
    "_caiso188_import_tranche_census.json / _caiso188_seam_cap_forensics.json -- "
    "and it is generated POST-HOC by caiso-189 (2026-08-11) because no generator "
    "was written at the promotion itself. The four assertions above rest on: "
    "(1) ZERO DOF ADDED -- caiso-188 introduces no free parameter and no fitted "
    "scalar; the census only RE-COUNTS an existing residual row (IMPORT_TRANCHES/"
    "EXPORT_TRANCHES[CAISO], 7 -> 6 live fitted scalars, measured on the built "
    "fleet) and rewrites two root_cause texts, and the ledger totals are asserted "
    "UNCHANGED below rather than claimed. (2) ONE ScenarioConfig FLAG FLIPPED, "
    "capacity_deliverability_limits False -> True, verified here as the arms' "
    "only config difference; its Part A resolves the seam limit through the "
    "PUBLISHED branch-group Maximum Import Capability partition "
    "(data/raw/capacity-deliverability/caiso/caiso.csv via "
    "scripts/data/curate_caiso_mic.py) -- a per-year, forward-reproducible, "
    "primary-sourced object -- replacing a scalar identified against a residual. "
    "That substitution is why levers_trace_to_measured_input holds MORE strongly "
    "after this promotion than before it. (3) NO FIT TO PRICE RESIDUALS and NO "
    "PINNING TO ACTUALS: C3a moved +10.5 -> +10.4 % (2024) and +13.1 -> +12.9 % "
    "(2025) as a rounding-scale BY-PRODUCT against a zero same-head noise floor; "
    "PRECHECK-caiso188 registered before the solve that the repair was kept "
    "regardless of the backcast, and a degradation would not have been a reason "
    "to revert it (rules 1 [R-STRUCT] / 13 [R-MEASURED]). (4) OUTAGE FILTER "
    "EXOGENOUS: outage_source='historic', the CAMPD measured-outage overlay, "
    "checked below against calibration_verdict.EXOGENOUS_OUTAGE_SOURCES rather "
    "than asserted. THE EXCEPTIONS BELOW ARE THE INCUMBENT'S, NOT NEW ONES: all "
    "four are carried from 2026-08-09-caiso-184-c1-lpbasis with classification "
    "and reason BYTE-IDENTICAL; this session creates no caveat and spends no "
    "ledger slot. Their magnitude fields ARE refreshed, because a carried "
    "magnitude measured on a superseded bundle is its own governance defect: each "
    "is re-measured on THIS bundle's own scored records and quotes the carried "
    "text verbatim alongside. Note that under rubric v3.1 LEDGERABLE_CRITERIA is "
    "price_tail alone, so the two price_mean entries reclassify NOTHING -- they "
    "are carried as the historical record and C3a's FAIL stands at full "
    "magnitude."
)


def _cfg(bundle: Path) -> dict:
    """Return one bundle's recorded ``scenario_config``."""
    data = json.loads((bundle / "run_config.json").read_text(encoding="utf-8"))
    return data.get("scenario_config", data)


def assert_single_flag_delta() -> dict:
    """G-DELTA — the arm differs from its control on exactly ``DELTA_KEY``."""
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = sorted(k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k))
    if diff != [DELTA_KEY]:
        raise SystemExit(
            f"G-DELTA FAILED: scenario_config differs on {diff}, expected exactly "
            f"[{DELTA_KEY!r}] — any other difference means a second lever moved and "
            "the 'one flag flipped, zero DOF added' claim is not attestable."
        )
    if c_cfg.get(DELTA_KEY) is not False or a_cfg.get(DELTA_KEY) is not True:
        raise SystemExit(
            f"G-DELTA FAILED: delta key misarmed — control={c_cfg.get(DELTA_KEY)!r}, "
            f"arm={a_cfg.get(DELTA_KEY)!r}; expected False -> True."
        )
    return {"delta_key": DELTA_KEY, "control": False, "arm": True, "n_keys": len(a_cfg)}


def _seam_rows(bundle: Path, year: int) -> pd.DataFrame:
    """P1 hourly rows for the simultaneous-import interface group."""
    df = pd.read_parquet(bundle / "hourly" / f"network_{year}.parquet")
    rows = df[(df["name"] == SEAM_GROUP) & (df["pass"] == "P1")]
    if rows.empty:
        raise SystemExit(
            f"{bundle.name} {year}: no P1 rows for {SEAM_GROUP!r} — the seam group "
            "is absent, so G-SEAM cannot be evaluated."
        )
    return rows


def assert_seam_released() -> dict:
    """G-SEAM — Part A resolved: fitted cap in the control, published MIC here.

    Read off each arm's OWN committed network sidecar, never from a mutable
    on-disk partition: a bundle whose Part A silently no-oped would still carry
    the fitted 7,500 MW limit here, so this is the test that distinguishes an
    armed flag from a resolved one.
    """
    per_year: dict[str, dict] = {}
    for year in YEARS:
        ctl, arm = _seam_rows(CONTROL, year), _seam_rows(ARM, year)

        ctl_limits = sorted({round(float(v), 4) for v in ctl["limit_up"]})
        if ctl_limits != [FITTED_SEAM_CAP_MW]:
            raise SystemExit(
                f"G-SEAM FAILED {year}: the control's seam limit is {ctl_limits}, "
                f"expected the fitted {FITTED_SEAM_CAP_MW} MW scalar — without it "
                "the control does not evidence the defect this promotion repairs."
            )
        ctl_binding = int((ctl["dual"].abs() > 0).sum())
        if ctl_binding == 0:
            raise SystemExit(
                f"G-SEAM FAILED {year}: the fitted cap never binds in the control, "
                "so there is no measured defect to attest a repair of."
            )

        arm_limits = sorted({round(float(v), 4) for v in arm["limit_up"]})
        if len(arm_limits) != 1 or arm_limits[0] <= FITTED_SEAM_CAP_MW:
            raise SystemExit(
                f"G-SEAM FAILED {year}: this bundle's seam limit is {arm_limits} — "
                f"Part A did NOT resolve to a published MIC above the fitted "
                f"{FITTED_SEAM_CAP_MW} MW fallback, so the attestation may not "
                "claim the published partition is in force."
            )
        arm_binding = int((arm["dual"].abs() > 0).sum())
        if arm_binding != 0:
            raise SystemExit(
                f"G-SEAM FAILED {year}: the seam still binds in {arm_binding} h "
                "with a nonzero dual; the released-seam claim is false."
            )

        per_year[str(year)] = {
            "control_limit_mw": ctl_limits[0],
            "control_binding_hours": ctl_binding,
            "control_mean_dual": round(float(ctl["dual"].mean()), 6),
            "keeper_limit_mw": arm_limits[0],
            "keeper_binding_hours": 0,
            "keeper_max_group_flow_mw": round(float(arm["mw"].max()), 4),
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
    """G-DOF — the carried ledger still reads the caiso-188 totals."""
    got = (ledger.get("n_entries"), ledger.get("n_residual"))
    if got != (LEDGER_N_ENTRIES, LEDGER_N_RESIDUAL):
        raise SystemExit(
            f"G-DOF FAILED: ledger reads {got[0]}/{got[1]}, expected "
            f"{LEDGER_N_ENTRIES}/{LEDGER_N_RESIDUAL} — caiso-188 adds no free "
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
    """This bundle's own scored (criterion, year) records, gated rows only.

    Sourced from :mod:`calibration_verdict` on the COMMITTED artifacts — no
    solve. ``model``/``actual`` are read rather than ``status``, so the function
    is idempotent: writing the exceptions changes a record's status but never its
    measurement.
    """
    verdict = cv.determine(RUN_ID)
    out: dict[tuple[str, int], dict] = {}
    for cid in ("price_tail", "price_mean"):
        for rec in verdict["criteria"][cid]["records"]:
            if rec.get("key") is not None:  # skip the DA report-only companions
                continue
            out[(cid, int(rec["year"]))] = rec
    return out


def _refresh_magnitude(entry: dict, rec: dict) -> tuple[str, bool]:
    """Return this bundle's magnitude text for one carried entry, and whether it moved.

    The carried text is quoted verbatim alongside the new measurement — the
    record is annotated, never overwritten (a carried magnitude measured on a
    superseded bundle is its own governance defect, but so is deleting it).
    """
    carried = entry.get("magnitude", "")
    if entry["criterion"] == "price_tail":
        model, actual = int(rec["model"]), int(rec["actual"])
        measured = (
            f"model {model} h with RT-expressible LMP > $200/MWh vs RT actual "
            f"{actual} h"
        )
        # A carried price_tail magnitude always states "model N h"; compare on N.
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
        f"RE-MEASURED on caiso188_d1_micseam by caiso-189 (2026-08-11), from the "
        f"bundle's own committed scored records via calibration_verdict — no solve: "
        f"{measured}. The carried magnitude is {verdict_word} against this bundle."
        f"{inert} CARRIED MAGNITUDE, verbatim from {INCUMBENT_RUN_ID}: {carried}"
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
    ap = argparse.ArgumentParser(description="caiso-189 C6 attestation repair")
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

    delta = assert_single_flag_delta()
    print(
        f"OK  G-DELTA  : arms differ on exactly [{DELTA_KEY}] of {delta['n_keys']} keys"
    )

    seam = assert_seam_released()
    for year, row in seam.items():
        print(
            f"OK  G-SEAM {year}: control {row['control_limit_mw']:,.1f} MW binding "
            f"{row['control_binding_hours']} h (mean dual {row['control_mean_dual']}) "
            f"-> keeper {row['keeper_limit_mw']:,.1f} MW binding 0 h, max flow "
            f"{row['keeper_max_group_flow_mw']:,.1f} MW"
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

    # G-DOF byte identity: the rendered free_parameters block must be the SAME
    # BYTES as the on-disk one. Both sit one level deep at indent=2, so the
    # section is directly comparable and any silent re-serialisation is caught.
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
