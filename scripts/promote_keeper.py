"""Promote a solved bundle to an ISO's keeper in ONE command.

This replaces the hand-run chain every promotion used to walk — register,
attest, set the shard, stamp touchpoints, re-key the ``complete`` marker and
the forecast gate-(a) stamp, rebuild the status part, audit, prune the
outgoing keeper, run the parity gate — with a single ordered, checked run.
Every step still calls the existing tool for that step, so nothing scored or
rendered changes; what changes is that a promotion is one command and one
checklist instead of ten commands gathered from six documents.

Order (CLAUDE.md rule 35 ``[R-PROMOTE]``: enumerate, promote, verify, THEN
delete):

  0. preflight    — bundle has ``meta.json`` + ``dispatch/<year>_P1.parquet``
                    for every solved year (registration needs them), and the
                    committed per-unit layer ``hourly/unit_marginal_<year>``
                    for every year (rule 15, owner 2026-10-01): derived here
                    from ``unit_hourly`` when absent; a NEW keeper with
                    neither is refused
  1. enumerate    — the ISO's registered year set BEFORE anything is deleted;
                    refuse a promotion that would shrink it (rule 35 (b)/(c))
  2. register     — ``dashboard_add_run.py --no-prune`` for the keeper bundle
                    and every ``--fold`` touchpoint bundle
  3. attest       — write the governance block when ``--attested-by`` is
                    given and the bundle has none; then
                    ``build_dof_ledger.py`` fills ``free_parameters``
  4. designate    — ``keepers/<ISO>.json`` via ``scripts.lib.keeper_store``
  5. fold         — ``stamp_touchpoint_holdout.py`` for each fold (rule 30)
  6. re-key       — ``calibration-complete.json`` ``complete.<ISO>.keeper`` and
                    the forecast board's ``gate.a_keeper_marker`` detail
                    (identity only; the leg verdict never moves)
  7. status       — ``build_status.py --iso <ISO>``
  8. audit        — ``audit_keepers.py --iso <ISO> --check`` (a FAIL stops
                    the run BEFORE the prune, rule 35 (e))
  9. prune        — ``prune_iso_runs.py --iso <ISO> --keep <new ids>
                    --force-uncite`` (rule 35 (a)/(d))
 10. parity       — ``check_registry_payload_parity.py``
 11. print        — the exact ``git add`` list and the two reminders the
                    tooling cannot do for you (matrix keeper stamp, log entry)

``--dry-run`` performs steps 0-1 and prints the plan for the rest.

Usage::

    python scripts/promote_keeper.py --iso SPP \\
        --bundle results/calibration/spp101_span --label "spp-101 chp-scope" \\
        --fold results/calibration/spp101_tp_2019_2021="spp-101 touchpoints" \\
        --attested-by "lane SPP-101; owner ruling 'promote' 2026-10-02" \\
        --note "SPP keeper #N: <one line on what changed and why>"
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import keeper_store  # noqa: E402
from scripts.lib.unit_marginal import write_unit_marginal  # noqa: E402

DATA = REPO / "frontend" / "data" / "backcast"
REGISTRY = DATA / "registry"
COMPLETE = DATA / "calibration-complete.json"
PROGRAM_STATUS = REPO / "frontend" / "data" / "forecast" / "program-status.json"
PY = sys.executable

GOVERNANCE_ASSERTIONS = (
    "levers_trace_to_measured_input",
    "no_fit_to_price_residuals",
    "no_pinning_to_actuals",
    "outage_filter_exogenous_net_load",
)


def _run(args: list[str], *, dry: bool, capture: bool = False) -> str:
    """Run one tool as a subprocess from the repo root; print the command."""
    shown = " ".join(a if " " not in a else repr(a) for a in args)
    print(f"\n$ {shown}")
    if dry:
        return ""
    res = subprocess.run(args, cwd=REPO, text=True, capture_output=capture, check=False)
    out = (res.stdout or "") if capture else ""
    if capture:
        sys.stdout.write(out)
        if res.stderr:
            sys.stderr.write(res.stderr)
    if res.returncode != 0:
        raise SystemExit(f"step failed (exit {res.returncode}): {shown}")
    return out


def _bundle_years(bundle: Path) -> list[int]:
    meta = json.loads((bundle / "meta.json").read_text())
    years = meta.get("years") or meta.get("solved_years") or []
    if not years:
        years = sorted(
            int(p.name.split("_")[0])
            for p in (bundle / "dispatch").glob("*_P1.parquet")
        )
    return sorted(int(y) for y in years)


def existing_run_id(bundle: Path) -> str | None:
    """The run id already registered for ``bundle``, if any (re-promotion)."""
    rel = str(bundle.relative_to(REPO))
    for p in REGISTRY.glob("*.json"):
        rec = json.loads(p.read_text())
        if rec.get("bundle") == rel:
            return rec.get("id", p.stem)
    return None


def preflight(bundle: Path) -> list[int]:
    """Step 0: the artifacts registration reads must exist.

    A bundle that is ALREADY registered (a sidecar names it) is accepted
    without its dispatch parquets — committed keepers do not carry them
    (``.gitignore`` drops ``results/calibration/*/dispatch/``) and such a
    bundle is re-designated, never re-rendered.
    """
    if not (bundle / "meta.json").exists():
        raise SystemExit(f"{bundle}: no meta.json — not a solved bundle")
    years = _bundle_years(bundle)
    missing = [
        y for y in years if not (bundle / "dispatch" / f"{y}_P1.parquet").exists()
    ]
    if missing and existing_run_id(bundle) is None:
        raise SystemExit(
            f"{bundle}: dispatch/<year>_P1.parquet missing for {missing} — "
            "registration raises without it (rule 34 (a)); the shard did not "
            "push its full bundle"
        )
    ensure_unit_marginal(bundle, years, new=existing_run_id(bundle) is None)
    return years


def ensure_unit_marginal(bundle: Path, years: list[int], *, new: bool) -> list[int]:
    """Step 0b: the keeper's committed per-unit layer, every year (rule 15).

    Owner instruction 2026-10-01 ("Moving forward for all ISOs"; card "Slim
    layer"): a keeper bundle commits ``hourly/unit_marginal_<year>.parquet``
    for every year it carries. A year missing it is derived here from the
    bundle's own ``unit_hourly_<year>.parquet`` (``scripts/lib/unit_marginal``).
    A NEW keeper with a year that has neither is refused; a re-designated,
    already-registered keeper only warns (the rule is prospective).

    Returns:
        The years still missing the layer after derivation.
    """
    hourly = bundle / "hourly"
    missing: list[int] = []
    for y in years:
        out = hourly / f"unit_marginal_{y}.parquet"
        if out.exists():
            continue
        if write_unit_marginal(hourly / f"unit_hourly_{y}.parquet", out) is None:
            missing.append(y)
        else:
            print(f"    derived {out} — commit it with the bundle")
    if missing and new:
        raise SystemExit(
            f"{bundle}: hourly/unit_marginal_<year>.parquet missing for {missing} "
            "and no unit_hourly to derive it from — a keeper bundle commits the "
            "per-unit layer for every year (CLAUDE.md rule 15); the shard did not "
            "push its full bundle"
        )
    if missing:
        print(
            f"    WARNING: {bundle.name} lacks unit_marginal for {missing} "
            "(pre-2026-10-01 keeper; gains it at its next re-solve)"
        )
    return missing


def registered_years(iso: str) -> tuple[set[int], list[str]]:
    """Step 1: the union of ``years`` over every sidecar registered for ``iso``."""
    years: set[int] = set()
    ids: list[str] = []
    for p in sorted(REGISTRY.glob("*.json")):
        rec = json.loads(p.read_text())
        if rec.get("iso") != iso:
            continue
        ids.append(rec.get("id", p.stem))
        years.update(int(y) for y in rec.get("years", []))
    return years, ids


def register(label: str, bundle: Path, *, dry: bool) -> str:
    """Step 2: register one bundle; return its run id (reused if registered)."""
    rid = existing_run_id(bundle)
    if rid:
        print(f"\n{bundle.name} is already registered as {rid} — not re-rendered")
        return rid
    out = _run(
        [
            PY,
            "scripts/dashboard_add_run.py",
            "--label",
            label,
            "--bundle",
            str(bundle.relative_to(REPO)),
            "--no-prune",
        ],
        dry=dry,
        capture=True,
    )
    if dry:
        return f"<run-id of {bundle.name}>"
    m = re.search(r"^RUN_ID=(\S+)$", out, re.M)
    if not m:
        raise SystemExit("dashboard_add_run printed no RUN_ID")
    return m.group(1)


def attest(bundle: Path, iso: str, attested_by: str | None, *, dry: bool) -> None:
    """Step 3: governance block (if needed) + DOF ledger."""
    path = bundle / "calibration_attestation.json"
    att = json.loads(path.read_text()) if path.exists() else {}
    gov = att.get("governance") or {}
    # Complete = every assertion present as a boolean (False is a legitimate
    # value under rule 1's authorized price-tuning channel, declared in
    # ``authorized_price_tuning``) plus an ``attested_by``. Existing keys are
    # never overwritten; a lane that needs a False asserts it by hand.
    has_gov = all(isinstance(gov.get(k), bool) for k in GOVERNANCE_ASSERTIONS) and bool(
        gov.get("attested_by")
    )
    if not has_gov:
        if not attested_by:
            raise SystemExit(
                f"{path.name} carries no complete governance block and no "
                "--attested-by was given. C6 FAILS unattested. Pass "
                "--attested-by '<lane; owner ruling; date>' (asserts the four "
                "rule-13/14 governance statements as true for this bundle; "
                "edit the JSON by hand if one must be False under rule 1's "
                "authorized channel)."
            )
        att.setdefault("schema", "calibration-attestation/v1")
        gov.setdefault("attested_by", attested_by)
        for k in GOVERNANCE_ASSERTIONS:
            gov.setdefault(k, True)
        att["governance"] = gov
        att.setdefault("exceptions", [])
        att.setdefault("disclosures", {})
        print(f"\nwriting governance block -> {path.relative_to(REPO)}")
        if not dry:
            path.write_text(json.dumps(att, indent=2) + "\n")
    _run(
        [
            PY,
            "scripts/build_dof_ledger.py",
            str(bundle.relative_to(REPO)),
            "--iso",
            iso,
        ],
        dry=dry,
    )


def rekey_complete(iso: str, run_id: str, *, dry: bool) -> None:
    """Step 6a: ``complete.<ISO>.keeper`` names the new keeper (if the ISO has one)."""
    if not COMPLETE.exists():
        return
    doc = json.loads(COMPLETE.read_text())
    entry = (doc.get("complete") or {}).get(iso)
    if not entry:
        print(f"\n{iso} holds no `complete` entry — nothing to re-key")
        return
    old = entry.get("keeper")
    if old == run_id:
        return
    print(f"\ncalibration-complete.json: complete.{iso}.keeper {old} -> {run_id}")
    entry["keeper"] = run_id
    entry["keeper_rekeyed"] = (
        f"{_dt.date.today().isoformat()} by promote_keeper.py (identity only): "
        f"{old} -> {run_id}"
    )
    if not dry:
        COMPLETE.write_text(json.dumps(doc, indent=2) + "\n")


def rekey_gate_a(iso: str, run_id: str, *, dry: bool) -> None:
    """Step 6b: the forecast board's gate-(a) stamp names the new keeper."""
    if not PROGRAM_STATUS.exists():
        return
    doc = json.loads(PROGRAM_STATUS.read_text())
    row = (
        ((doc.get("isos") or {}).get(iso) or {}).get("gate", {}).get("a_keeper_marker")
    )
    if not row:
        print(f"\n{iso}: no gate.a_keeper_marker row on the forecast board — skipped")
        return
    detail = row.get("detail", "")
    m = re.search(r"keeper (20\d\d-\d\d-\d\d-[\w.-]+)", detail)
    old = m.group(1) if m else None
    if old == run_id:
        return
    new_detail = re.sub(
        r"keeper 20\d\d-\d\d-\d\d-[\w.-]+", f"keeper {run_id}", detail, count=1
    )
    new_detail = (
        f"RE-KEYED {_dt.date.today().isoformat()} by promote_keeper.py (identity "
        f"only): {old} -> {run_id}; leg verdict unchanged. " + new_detail
    )
    row["detail"] = new_detail
    print(f"\nprogram-status.json: {iso} gate.a_keeper_marker {old} -> {run_id}")
    if not dry:
        PROGRAM_STATUS.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--iso", required=True)
    ap.add_argument("--bundle", required=True, help="results/calibration/<name>")
    ap.add_argument(
        "--label", required=True, help="dashboard label (run id = date-shorthand)"
    )
    ap.add_argument(
        "--fold",
        action="append",
        default=[],
        metavar="BUNDLE=LABEL",
        help="touchpoint bundle folded to the keeper (rule 30); repeatable",
    )
    ap.add_argument(
        "--attested-by", help="governance attestation text (lane; ruling; date)"
    )
    ap.add_argument("--note", help="keeper shard note (one line: what changed, why)")
    ap.add_argument(
        "--allow-year-shrink",
        action="store_true",
        help="permit a registered year set smaller than before (rule 35 (c) says don't)",
    )
    ap.add_argument(
        "--skip-prune", action="store_true", help="leave the outgoing keeper registered"
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    iso = args.iso.upper()
    dry = args.dry_run
    bundle = (REPO / args.bundle).resolve()
    folds: list[tuple[Path, str]] = []
    for spec in args.fold:
        b, _, label = spec.partition("=")
        if not label:
            raise SystemExit(f"--fold needs BUNDLE=LABEL, got {spec!r}")
        folds.append(((REPO / b).resolve(), label))

    # 0 — preflight
    years = preflight(bundle)
    fold_years = {b: preflight(b) for b, _ in folds}
    incoming = set(years) | {y for ys in fold_years.values() for y in ys}
    print(
        f"[0] {bundle.name}: years {years}"
        + "".join(f"; fold {b.name}: {ys}" for b, ys in fold_years.items())
    )

    # 1 — enumerate BEFORE deleting anything (rule 35 (b))
    before, before_ids = registered_years(iso)
    print(f"[1] {iso} registered before: {sorted(before)} across {before_ids}")
    print(f"    incoming: {sorted(incoming)}")
    lost = before - incoming
    if lost and not args.allow_year_shrink:
        raise SystemExit(
            f"promotion would DROP years {sorted(lost)} from {iso}'s registered set "
            "(rule 35 (c)). Solve them (one shard per year) or fold the run that "
            "carries them, or pass --allow-year-shrink deliberately."
        )

    # 2 — register
    run_id = register(args.label, bundle, dry=dry)
    fold_ids = [(b, register(label, b, dry=dry)) for b, label in folds]
    print(f"[2] keeper run id: {run_id}; folds: {[r for _, r in fold_ids]}")

    # 3 — attest
    attest(bundle, iso, args.attested_by, dry=dry)
    for b, _ in folds:
        attest(b, iso, args.attested_by, dry=dry)

    # 4 — designate
    print(f"\n[4] keepers/{iso}.json keeper -> {run_id}")
    if not dry:
        keeper_store.write_keeper(iso, run_id, note=args.note)

    # 5 — fold
    for b, rid in fold_ids:
        _run(
            [
                PY,
                "scripts/stamp_touchpoint_holdout.py",
                "--run-id",
                rid,
                "--keeper-id",
                run_id,
                "--holdout-year",
                str(min(fold_years[b])),
            ],
            dry=dry,
        )

    # 6 — re-key
    rekey_complete(iso, run_id, dry=dry)
    rekey_gate_a(iso, run_id, dry=dry)

    # 7 — status
    _run([PY, "scripts/build_status.py", "--iso", iso], dry=dry)

    # 8 — audit (stops before the prune on FAIL)
    _run([PY, "scripts/audit_keepers.py", "--iso", iso, "--check"], dry=dry)

    # 9 — prune the outgoing keeper + anything else registered for the ISO
    if not args.skip_prune:
        keep = [run_id] + [r for _, r in fold_ids]
        cmd = [PY, "scripts/prune_iso_runs.py", "--iso", iso, "--force-uncite"]
        for k in keep:
            cmd += ["--keep", k]
        _run(cmd, dry=dry)

    # 10 — parity
    _run([PY, "scripts/check_registry_payload_parity.py"], dry=dry)

    # 11 — what the tooling cannot do for you
    after, after_ids = registered_years(iso) if not dry else (incoming, [run_id])
    print(f"\n[done] {iso} registered after: {sorted(after)} across {after_ids}")
    adds = [
        str(bundle.relative_to(REPO)),
        *[str(b.relative_to(REPO)) for b, _ in folds],
        "frontend/data/backcast/registry/",
        "frontend/data/backcast/runs/",
        "frontend/data/backcast/bench/",
        f"frontend/data/backcast/keepers/{iso}.json",
        f"frontend/data/backcast/status/{iso}.js",
        "frontend/data/backcast/status/shared.js",
        str(COMPLETE.relative_to(REPO)),
        str(PROGRAM_STATUS.relative_to(REPO)),
    ]
    print("\ngit add -A -- " + " ".join(adds))
    print(
        "\nSTILL YOURS (no tool writes these):\n"
        f"  * stamp the keeper in docs/codebase-site/data/mechanism-matrix/{iso}.js "
        "(keeper id + open gates) and set the cell verdict of the mechanism this run tested\n"
        f"  * one entry in docs/calibration-log/{iso.lower()}.md (what changed, why, the gate table)\n"
        "  * delete the superseded keeper's gen_*_attestation.py / per-run scripts, if any"
    )


if __name__ == "__main__":
    main()
