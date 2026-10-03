"""Promote a solved bundle to an ISO's keeper in ONE command.

This replaces the hand-run chain every promotion used to walk — register,
attest, set the shard, stamp touchpoints, re-key the ``complete`` marker and
the forecast gate-(a) stamp, rebuild the status part, prune the outgoing
keeper, audit, run the parity gate — with a single ordered, checked run.
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
                    — and ``fleet_census_<year>.json`` for every year (W0
                    E.7, owner ruling R-2 / Q8): built here from the slim
                    layer when absent; a NEW keeper with neither is refused
  1. enumerate    — the ISO's registered year set BEFORE anything is deleted;
                    refuse a promotion that would shrink it (rule 35 (b)/(c));
                    and the outgoing keeper's attestation ``exceptions`` (its
                    folded runs included), each routed to the incoming bundle
                    carrying its year — an entry whose year left the span is
                    refused unless ``--drop-exception`` drops it with a reason
  2. register     — ``dashboard_add_run.py --no-prune`` for the keeper bundle
                    and every ``--fold`` touchpoint bundle
  3. attest       — write the governance block when ``--attested-by`` is
                    given and the bundle has none; then
                    ``build_dof_ledger.py`` fills ``free_parameters``; then
                    CARRY the outgoing ledger forward: every C3c entry is
                    re-measured on the incoming bundle (refused if it no longer
                    fails there), every other entry is carried verbatim and
                    labelled not re-measured; dropped entries are recorded under
                    ``exceptions_dropped`` with their reason
  4. designate    — ``keepers/<ISO>.json`` via ``scripts.lib.keeper_store``
  5. fold         — ``stamp_touchpoint_holdout.py`` for each fold (rule 30)
  6. re-key       — ``calibration-complete.json`` ``complete.<ISO>.keeper`` and
                    the forecast board's ``gate.a_keeper_marker`` detail
                    (identity only; the leg verdict never moves)
  7. status       — ``build_status.py --iso <ISO>``
  8. pre-audit    — ``audit_keepers.py --iso <ISO> --json``: any FAIL other
                    than E13 stops the run BEFORE the prune (rule 35 (e); E11
                    needs the former bundle on disk). E13 is expected to fail
                    here — the outgoing keeper is still registered
  9. prune        — ``prune_iso_runs.py --iso <ISO> --keep <new ids>
                    --force-uncite`` (rule 35 (a)/(d); own ISO only)
 10. audit        — ``audit_keepers.py --iso <ISO>`` again, now strict: any
                    FAIL, E13 included, refuses to finish (rule 35 (f))
 11. parity       — ``check_registry_payload_parity.py``
 12. print        — the exact ``git add`` list and the two reminders the
                    tooling cannot do for you (matrix keeper stamp, log entry)

``--dry-run`` performs steps 0-1 (the exception routing included) and prints
the plan for the rest; it re-measures C3c entries only for a bundle that is
already registered (nothing is written).

Usage::

    python scripts/promote_keeper.py --iso SPP \\
        --bundle results/calibration/spp101_span --label "spp-101 chp-scope" \\
        --fold results/calibration/spp101_tp_2019_2021="spp-101 touchpoints" \\
        --attested-by "lane SPP-101; owner ruling 'promote' 2026-10-02" \\
        --note "SPP keeper #N: <one line on what changed and why>" \\
        --drop-exception "price_tail:2019=year 2019 left the keeper span (owner ruling ...)"
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
from scripts.lib import attestation_schema  # noqa: E402
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
    ensure_fleet_census(bundle, years, new=existing_run_id(bundle) is None)
    ensure_replay_recipe(bundle, years)
    return years


def ensure_replay_recipe(bundle: Path, years: list[int]) -> None:
    """Step 0d: ``replay_keeper --years Y`` must reproduce every year's solved config.

    Zero LP (``scripts/lib/replay_recipe.py``): each year carrying a
    ``run_config_<year>.json`` is resolved the way the replay would resolve it
    and diffed against the recorded ``scenario_config``. A keeper whose
    ``meta.json`` base recipe or ``config_partition_overrides`` block does not
    reproduce its own legs is refused — its replays (and every downstream
    re-solve or forecast gate built on them) would solve a recipe that was
    never scored (the W0 phase-3 ``w0_ercot_span`` defect).
    """
    from scripts.lib.replay_recipe import replay_config_diffs

    bad: dict[int, dict] = {}
    for y in years:
        diffs = replay_config_diffs(bundle, y)
        if diffs:
            bad[y] = diffs
    if bad:
        lines = [
            f"  {y}: "
            + "; ".join(
                f"{k}: recorded={r!r} replay={p!r}" for k, (r, p) in list(d.items())[:6]
            )
            for y, d in sorted(bad.items())
        ]
        raise SystemExit(
            f"{bundle}: replay does not reproduce the solved config for "
            f"{sorted(bad)} — fix meta.json's base recipe and stamp "
            "config_partition_overrides (scripts/stamp_config_partition.py) "
            "before promoting:\n" + "\n".join(lines)
        )


def ensure_fleet_census(bundle: Path, years: list[int], *, new: bool) -> list[int]:
    """Step 0c: the keeper's committed fleet census, every year (W0 E.7).

    Owner ruling R-2 / Q8 (2026-10-02): a keeper bundle commits
    ``fleet_census_<year>.json`` for every year it carries — the per ISO-year
    ledger of what the LP carried against the year's EIA-860 vintage and the
    ISO's own report (``scripts/build_fleet_census.py``). A year missing it is
    built here from the bundle's committed ``hourly/unit_marginal_<year>``
    (zero LP). A NEW keeper with a year that has neither is refused; a
    re-designated, already-registered keeper only warns (prospective rule).

    Returns:
        The years still missing the census after derivation.
    """
    from scripts import build_fleet_census as bfc

    meta = json.loads((bundle / "meta.json").read_text())
    iso = str(meta.get("iso", "")).upper()
    missing: list[int] = []
    for y in years:
        out = bundle / f"fleet_census_{y}.json"
        if out.exists():
            continue
        if not (bundle / "hourly" / f"unit_marginal_{y}.parquet").exists():
            missing.append(y)
            continue
        census = bfc.build_census(
            iso,
            y,
            bfc.model_from_unit_marginal(bundle, y),
            f"unit_marginal:{bundle.name}",
        )
        out.write_text(json.dumps(census, indent=2) + "\n")
        print(f"    built {out.name} ({census['verdict']}) — commit it with the bundle")
    if missing and new:
        raise SystemExit(
            f"{bundle}: fleet_census_<year>.json missing for {missing} and no "
            "unit_marginal layer to build it from — a keeper bundle commits its "
            "fleet census for every year (W0 E.7, owner ruling R-2 / Q8)"
        )
    if missing:
        print(
            f"    WARNING: {bundle.name} lacks fleet_census for {missing} "
            "(pre-W0 keeper; gains it at its next re-solve)"
        )
    return missing


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
    # Fixed schema (owner ruling 2026-10-03; audit E16): migrate additively,
    # then refuse an attestation the schema rejects.
    if not dry:
        for change in attestation_schema.migrate(path):
            print(f"    attestation schema: {change}")
        problems = attestation_schema.validate(json.loads(path.read_text()))
        if problems:
            raise SystemExit(
                f"{path.name} violates calibration-attestation/v1: "
                + "; ".join(problems)
            )


# ---------------------------------------------------------------------------
# Exceptions ledger carry-forward (step 1 routing, step 3 re-measure + write)
# ---------------------------------------------------------------------------
# The fresh attestation step 3 used to write started ``exceptions`` empty, so
# an owner-signed C3c ledger entry on the outgoing keeper vanished and the
# incoming keeper read C3c FAIL where the ISO had read CAVEAT (CAISO C3c 2024,
# closeout-CAISO 2026-10-02; the same hand fix in #7041 and #7025). Each
# outgoing entry is now carried to the incoming bundle that carries its year:
# a C3c entry is re-measured there and refused if it no longer applies; an
# entry whose year left the span is refused. ``--drop-exception`` is the only
# way past a refusal, and it records the reason. Nothing is dropped silently
# and no stale number is kept silently.

LEDGERABLE = "price_tail"  # calibration_verdict.LEDGERABLE_CRITERIA (rubric v3.1)
STILL_APPLIES = ("FAIL", "CAVEAT")  # a ledger entry reclassifies a FAIL to CAVEAT


def exception_tag(entry: dict) -> str:
    """``criterion:year`` — the handle ``--drop-exception`` names an entry by."""
    return f"{entry.get('criterion')}:{entry.get('year')}"


def exception_year(entry: dict) -> int | None:
    """The entry's single scored year, or None (no year, or a span like '2020-2025')."""
    try:
        return int(entry.get("year"))
    except (TypeError, ValueError):
        return None


def _entry_key(entry: dict) -> str | None:
    return entry.get("klass") or entry.get("family") or entry.get("key")


def _same_entry(a: dict, b: dict) -> bool:
    """Same (criterion, year, class/family) — ``calibration_verdict._ledger_match``."""
    if a.get("criterion") != b.get("criterion"):
        return False
    if str(a.get("year")) != str(b.get("year")):
        return False
    ka, kb = _entry_key(a), _entry_key(b)
    return ka is None or kb is None or str(ka) == str(kb)


def outgoing_exceptions(
    iso: str,
    keeper_id: str | None,
    registry_dir: Path,
    repo: Path,
    incoming: list[Path],
) -> list[tuple[str, dict]]:
    """Every ``exceptions`` entry on the outgoing keeper and the runs stamped to it.

    Returns ``(source run id, entry)`` pairs. A run whose bundle IS one of the
    incoming bundles (a re-designation) is skipped: its ledger is already the
    incoming ledger.
    """
    if not keeper_id:
        return []
    incoming_resolved = {p.resolve() for p in incoming}
    out: list[tuple[str, dict]] = []
    for path in sorted(registry_dir.glob("*.json")):
        rec = json.loads(path.read_text())
        if str(rec.get("iso", "")).upper() != iso.upper():
            continue
        rid = rec.get("id", path.stem)
        stamped = (rec.get("holdout") or {}).get("keeper")
        if rid != keeper_id and stamped != keeper_id:
            continue
        bundle = (repo / rec.get("bundle", "")).resolve()
        if not rec.get("bundle") or bundle in incoming_resolved:
            continue
        att_path = bundle / "calibration_attestation.json"
        if not att_path.exists():
            continue
        for entry in json.loads(att_path.read_text()).get("exceptions") or []:
            out.append((rid, entry))
    return out


def plan_exception_carry(
    outgoing: list[tuple[str, dict]],
    targets: dict[Path, list[int]],
    keeper_bundle: Path,
    existing: dict[Path, list[dict]],
    drops: dict[str, str],
    measure,
    today: str,
) -> tuple[dict[Path, list[dict]], dict[Path, list[dict]], list[str]]:
    """Route, re-measure and stamp every outgoing ledger entry; refuse what no longer applies.

    Pure over its inputs (``measure`` is injected) so it is unit-testable
    without the registry or the scorer.

    Args:
        outgoing: ``(source run id, entry)`` from :func:`outgoing_exceptions`.
        targets: incoming bundle -> the years it carries (keeper and folds).
        keeper_bundle: where an entry with no single year is carried.
        existing: incoming bundle -> its own current ``exceptions``.
        drops: ``criterion:year`` -> recorded reason (``--drop-exception``).
        measure: ``(bundle, year) -> C3c record | None`` (the scorer's gated
            ``price_tail`` row for that bundle-year), or None when the incoming
            bundle is not yet registered (dry run) — routing is still checked.
        today: ISO date stamped on every carried / dropped entry.

    Returns:
        ``(add, dropped, log)`` — entries to append per bundle, entries to
        record under ``exceptions_dropped`` per bundle, and one line per entry.

    Raises:
        SystemExit: listing every entry that no longer applies and was not
        dropped, and every ``--drop-exception`` that named no outgoing entry.
    """
    add: dict[Path, list[dict]] = {}
    dropped: dict[Path, list[dict]] = {}
    log: list[str] = []
    problems: list[str] = []
    used: set[str] = set()
    for src, entry in outgoing:
        tag = exception_tag(entry)
        year = exception_year(entry)
        target = (
            keeper_bundle
            if year is None
            else next((b for b, ys in targets.items() if year in ys), None)
        )
        if tag in drops:
            used.add(tag)
            dropped.setdefault(target or keeper_bundle, []).append(
                {
                    **entry,
                    "dropped": {
                        "reason": drops[tag],
                        "source_run": src,
                        "date": today,
                        "by": "promote_keeper.py --drop-exception",
                    },
                }
            )
            log.append(f"DROPPED {tag} (from {src}): {drops[tag]}")
            continue
        if target is None:
            problems.append(
                f"{tag} (from {src}): year {year} is not carried by the incoming "
                f"bundle(s) {[b.name for b in targets]} — the entry no longer applies"
            )
            continue
        own = next((e for e in existing.get(target, []) if _same_entry(e, entry)), None)
        if entry.get("criterion") != LEDGERABLE or year is None:
            if own is not None:
                log.append(f"KEPT {tag}: {target.name} already ledgers it")
                continue
            carried = {
                **entry,
                "carried_forward": {
                    "source_run": src,
                    "date": today,
                    "remeasured": False,
                    "why": (
                        "carried verbatim, NOT re-measured: "
                        + (
                            "the entry names no single year"
                            if year is None
                            else f"{entry.get('criterion')} is not ledgerable "
                            "under rubric v3.1, so the scorer never applies "
                            "this entry (record only)"
                        )
                    ),
                },
            }
            add.setdefault(target, []).append(carried)
            log.append(f"CARRIED {tag} -> {target.name} (verbatim; not re-measured)")
            continue
        if measure is None:
            log.append(
                f"ROUTED {tag} -> {target.name} (re-measured after registration)"
            )
            continue
        rec = measure(target, year)
        status = (rec or {}).get("status")
        if status not in STILL_APPLIES:
            problems.append(
                f"{tag} (from {src}): C3c {year} reads {status or 'NOT SCORED'} on "
                f"{target.name}"
                + (f" ({rec.get('magnitude')})" if rec else "")
                + " — the entry no longer applies"
            )
            continue
        stamp = {
            "source_run": src,
            "date": today,
            "remeasured": True,
            "model": rec.get("model"),
            "actual": rec.get("actual"),
            "magnitude_outgoing": entry.get("magnitude"),
        }
        if own is not None:
            # The incoming bundle already ledgers it (a lane wrote it by hand):
            # its text stands, the re-measured numbers are stamped beside it.
            own["carried_forward"] = {**stamp, "magnitude_outgoing": None}
            log.append(
                f"KEPT {tag}: {target.name} already ledgers it; re-measured "
                f"{rec.get('magnitude')}"
            )
            continue
        carried = {
            **entry,
            "magnitude": (
                f"{rec.get('magnitude')} (RE-MEASURED on {target.name} by "
                f"promote_keeper.py {today}; carried from {src})"
            ),
            "carried_forward": stamp,
        }
        add.setdefault(target, []).append(carried)
        log.append(
            f"CARRIED {tag} -> {target.name}; re-measured {rec.get('magnitude')}"
        )
    stray = sorted(set(drops) - used)
    if stray:
        problems.append(
            f"--drop-exception {stray} named no outgoing ledger entry "
            f"(have: {sorted({exception_tag(e) for _, e in outgoing})})"
        )
    if problems:
        raise SystemExit(
            "outgoing keeper's exceptions ledger cannot be carried forward:\n  "
            + "\n  ".join(problems)
            + "\nRe-solve the year, or drop the entry deliberately with "
            "--drop-exception 'criterion:year=<recorded reason>'."
        )
    return add, dropped, log


def c3c_measurer(run_ids: dict[Path, str]):
    """``(bundle, year) -> the scorer's gated C3c row`` for registered incoming bundles."""
    from scripts import calibration_verdict as cv

    cache: dict[str, dict] = {}

    def measure(bundle: Path, year: int) -> dict | None:
        rid = run_ids[bundle]
        if rid not in cache:
            cache[rid] = cv.determine(rid)
        for rec in cache[rid]["criteria"]["price_tail"]["records"]:
            if rec.get("key") is None and int(rec["year"]) == int(year):
                return rec
        return None

    return measure


def write_exception_carry(
    add: dict[Path, list[dict]],
    dropped: dict[Path, list[dict]],
    existing: dict[Path, list[dict]],
    *,
    touched: set[Path],
    dry: bool,
) -> None:
    """Append carried entries to ``exceptions`` and drops to ``exceptions_dropped``.

    ``touched`` names bundles whose own entries gained a re-measurement stamp;
    a bundle with nothing added, dropped or stamped is not rewritten.
    """
    for bundle in sorted(set(add) | set(dropped) | touched):
        path = bundle / "calibration_attestation.json"
        att = json.loads(path.read_text()) if path.exists() else {}
        att["exceptions"] = list(existing.get(bundle, [])) + add.get(bundle, [])
        if dropped.get(bundle):
            att["exceptions_dropped"] = (att.get("exceptions_dropped") or []) + dropped[
                bundle
            ]
        print(
            f"    {bundle.name}: exceptions {len(att['exceptions'])} "
            f"(+{len(add.get(bundle, []))} carried), "
            f"{len(dropped.get(bundle, []))} dropped"
        )
        if not dry:
            path.write_text(json.dumps(att, indent=2) + "\n")


def _own_exceptions(bundle: Path) -> list[dict]:
    path = bundle / "calibration_attestation.json"
    if not path.exists():
        return []
    return list(json.loads(path.read_text()).get("exceptions") or [])


def _parse_drops(specs: list[str]) -> dict[str, str]:
    drops: dict[str, str] = {}
    for spec in specs:
        tag, _, reason = spec.partition("=")
        if not reason.strip() or ":" not in tag:
            raise SystemExit(
                f"--drop-exception needs 'criterion:year=<reason>', got {spec!r}"
            )
        drops[tag.strip()] = reason.strip()
    return drops


def audit(iso: str, *, tolerate: tuple[str, ...], dry: bool) -> None:
    """Run ``audit_keepers.py --iso`` and stop on any FAIL whose code is not tolerated."""
    args = [PY, "scripts/audit_keepers.py", "--iso", iso, "--json"]
    print(
        f"\n$ {' '.join(args)}"
        + (f"  (tolerating {list(tolerate)})" if tolerate else "")
    )
    if dry:
        return
    res = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    try:
        findings = json.loads(res.stdout)["findings"]
    except (json.JSONDecodeError, KeyError):
        sys.stderr.write(res.stdout[-2000:] + res.stderr[-2000:])
        raise SystemExit(f"audit_keepers produced no JSON (exit {res.returncode})")
    fails = [f for f in findings if f["level"] == "FAIL"]
    blocking = [f for f in fails if f["code"] not in tolerate]
    for f in fails:
        mark = "FAIL" if f in blocking else "tolerated"
        print(f"    [{mark}] {f['code']} {f['run_id']}: {f['msg']}")
    if blocking:
        raise SystemExit(f"audit_keepers: {len(blocking)} FAIL(s) — promotion stopped")
    print(f"    audit clean ({len(fails) - len(blocking)} tolerated FAIL(s))")


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
    ap.add_argument(
        "--drop-exception",
        action="append",
        default=[],
        metavar="CRITERION:YEAR=REASON",
        help=(
            "drop one outgoing exceptions-ledger entry that no longer applies "
            "(e.g. its year left the span); the reason is recorded under "
            "exceptions_dropped. Repeatable"
        ),
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

    # 1b — the outgoing exceptions ledger, routed BEFORE anything is written
    targets = {bundle: years, **fold_years}
    drops = _parse_drops(args.drop_exception)
    today = _dt.date.today().isoformat()
    outgoing = outgoing_exceptions(
        iso,
        (keeper_store.load_shard(iso, REPO) or {}).get("keeper"),
        REGISTRY,
        REPO,
        list(targets),
    )
    existing = {b: _own_exceptions(b) for b in targets}
    print(f"[1] outgoing exceptions ledger: {[exception_tag(e) for _, e in outgoing]}")
    plan_exception_carry(outgoing, targets, bundle, existing, drops, None, today)

    # 2 — register
    run_id = register(args.label, bundle, dry=dry)
    fold_ids = [(b, register(label, b, dry=dry)) for b, label in folds]
    print(f"[2] keeper run id: {run_id}; folds: {[r for _, r in fold_ids]}")

    # 3 — attest, then carry the outgoing ledger forward (re-measured)
    attest(bundle, iso, args.attested_by, dry=dry)
    for b, _ in folds:
        attest(b, iso, args.attested_by, dry=dry)
    run_ids = {bundle: run_id, **dict(fold_ids)}
    registered = {b: r for b, r in run_ids.items() if not r.startswith("<")}
    if outgoing:
        existing = {b: _own_exceptions(b) for b in targets}
        before = json.dumps({str(b): e for b, e in existing.items()}, sort_keys=True)
        measure = c3c_measurer(registered) if len(registered) == len(run_ids) else None
        add, dropped, log = plan_exception_carry(
            outgoing, targets, bundle, existing, drops, measure, today
        )
        print("\n[3] exceptions ledger carried forward:")
        for line in log:
            print(f"    {line}")
        touched = {
            b
            for b in targets
            if json.dumps(existing[b], sort_keys=True)
            != json.dumps(json.loads(before)[str(b)], sort_keys=True)
        }
        write_exception_carry(add, dropped, existing, touched=touched, dry=dry)

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

    # 8 — pre-prune audit: every check but E13 must pass while the former
    # bundle is still on disk (E11 diffs against it). E13 cannot pass yet: the
    # outgoing keeper is still registered and is no longer the keeper.
    audit(iso, tolerate=("E13",), dry=dry)

    # 9 — prune the outgoing keeper + anything else registered for the ISO
    if not args.skip_prune:
        keep = [run_id] + [r for _, r in fold_ids]
        cmd = [PY, "scripts/prune_iso_runs.py", "--iso", iso, "--force-uncite"]
        for k in keep:
            cmd += ["--keep", k]
        _run(cmd, dry=dry)

    # 10 — post-prune audit, strict: the registered set is keeper-only (E13)
    if args.skip_prune:
        print(
            "\n[10] --skip-prune: the outgoing keeper stays registered, so E13 "
            "fails by construction — rule 35 says this promotion is NOT done"
        )
        audit(iso, tolerate=("E13",), dry=dry)
    else:
        audit(iso, tolerate=(), dry=dry)

    # 11 — parity
    _run([PY, "scripts/check_registry_payload_parity.py"], dry=dry)

    # 12 — what the tooling cannot do for you
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
