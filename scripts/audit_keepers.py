"""Audit that the dashboard text matches each designated keeper's actual results.

The backcast dashboard shows three kinds of keeper text, with very different
trust levels:

* The **Calibration Status** page (``status.js``) is regenerated from the SAME
  scorer the gate uses (``scripts/build_status.py`` -> ``calibration_verdict``),
  so it can never *say* the wrong determination — but it goes **stale** the
  moment a keeper changes, a bundle is re-solved, or the benchmark/rubric moves.
* Each keeper's **run-report header** is the human-written ``definition`` in its
  registry sidecar (``frontend/data/backcast/registry/<id>.json``). This is the
  one surface that can silently *lie*: a placeholder, a copy from the wrong run,
  or a stale "NOT-YET" after the verdict turned green.
* The per-year scorecard / diagnostics are computed client-side from the run
  payload, so they are always faithful and are not audited here.

This module checks the editable surfaces against the bundle and the live
verdict. It is the deterministic core the ``calibration-keeper-auditor``
subagent runs (and is safe to wire into CI / a pre-commit ``--check``).

For every keeper id in ``frontend/data/backcast/keepers.json`` it verifies:

  E1  sidecar, run payload and bundle dir all exist.
  E2  sidecar ``iso`` matches the bundle's ``calibration_flags.iso``.
  E3  sidecar ``years`` matches the bundle's solved years AND, for a multi-year
      ISO, is the full span (claude.md #13: never a single-year keeper).
  E4  ``definition`` is real prose, not the auto-generated placeholder / empty.
  E5  any determination token the ``definition`` asserts ("NOT-YET",
      "CALIBRATED-WITH-CAVEATS", "CALIBRATED") matches the CURRENT verdict.
  E6  keepers.json names exactly one keeper per ISO.
  E7  (warn) the keeper is the newest-dated run for its ISO in the registry;
      a newer same-ISO sidecar means the keeper may be stale. Zero-forcing
      ablation twins (``*-ablation`` ids, rule 20 / D-3) are excluded from the
      comparison: a twin is a diagnostic shadow of its parent, never a keeper
      candidate, so registering a keeper's own twin must not flag it stale.
      Sidecars carrying ``"keeper_candidate": false`` are excluded the same
      way: a diagnostic probe (e.g. a D-7 statistical-mode A/B run, see
      docs/handoffs/forecast-validation-program-2026-07.md) is never a keeper
      candidate by design (CLAUDE.md rule 15/#1), so a probe landing after the
      keeper must not read as "keeper may be stale" — the probe stays on the
      dashboard (rule 15: mark, don't prune), it just doesn't compete for
      newest-run staleness. A keeper/newer-run pair the owner has separately
      adjudicated (gap G-04, docs/calibration-log.md 2026-07-06 entry) gets
      its WARN annotated with a pointer to that record via
      ``E7_STALENESS_ADJUDICATED`` — annotation only, the WARN is never
      suppressed.
  E8  the bundle attestation carries a ``free_parameters`` DOF ledger and every
      residual-sourced entry references an open root cause (CLAUDE.md rule 20).
  E9  the keeper carries a registered zero-forcing ablation twin
      (``registry/<id>-ablation.json``, linked from the sidecar
      ``ablation_twin`` field) — CLAUDE.md rule 20 / audit D-3. Mirrors E8.
      **Rollout:** E8 landed as an unconditional hard fail (every keeper already
      had a DOF ledger). E9 cannot, because no current keeper has a twin yet: an
      unconditional E9 would redden main before W2 solves the twins. So E9
      hard-fails only keepers NOT on ``E9_ABLATION_TWIN_GRANDFATHER`` (the six
      keepers current when D-3 landed), which WARN instead. The list is
      self-emptying — a re-registered keeper gets a new dated id that carries its
      twin, so the grandfathered id stops being a keeper — and once every ISO's
      keeper has a twin the list is deleted and E9 is unconditional, with no
      further edit to E9 itself.
  S1  ``status.js`` is in sync with the current verdicts
      (``build_status.py --check``).
  H1  holdout quarantine (CLAUDE.md rule 22 / audit D-6, amended 2026-07-04):
      NO registered bundle — keeper or probe — declares a solve year outside
      the 2023–2025 calibration window unless its ISO has a
      calibration-complete marker in
      ``frontend/data/backcast/calibration-complete.json``.

Usage:
    python scripts/audit_keepers.py                  # audit every keeper
    python scripts/audit_keepers.py --iso ERCOT PJM  # scope to ISOs
    python scripts/audit_keepers.py --check          # exit 1 on any FAIL
    python scripts/audit_keepers.py --json           # machine-readable report

Exit code is 0 when there are no FAILs (warnings allowed), 1 otherwise.
Stdlib-only; reuses ``scripts.calibration_verdict``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import calibration_verdict as cv  # noqa: E402  (after sys.path insert)

DATA = REPO / "frontend" / "data" / "backcast"
KEEPERS_FILE = DATA / "keepers.json"

# A sidecar whose definition still reads like this never described the run.
_PLACEHOLDER_RE = re.compile(r"^\s*calibration run from bundle\b", re.IGNORECASE)

# Determination tokens, longest-first so "CALIBRATED-WITH-CAVEATS" wins over
# the substring "CALIBRATED".
_DET_TOKENS = ("CALIBRATED-WITH-CAVEATS", "NOT-YET", "CALIBRATED")

# ISOs that must always carry the full backcast year span (claude.md #16).
_MULTI_YEAR_ISOS = {"CAISO", "PJM", "NEISO", "NYISO", "MISO"}

# E9 ablation-twin grandfather list (CLAUDE.md rule 20 / audit D-3). E8 was
# rolled out as an UNCONDITIONAL hard fail (every keeper already had a DOF
# ledger when it landed). E9 cannot: none of the six keepers current when D-3
# landed carries an ablation twin yet — an immediate unconditional E9 would turn
# CI red on main before W2 can solve the twins. So E9 hard-fails only keepers
# NOT on this list; the listed keepers WARN (grace) until re-registered.
#
# The list is self-emptying: a keeper is re-registered (W2+) under a NEW dated
# run id that carries its twin, and keepers.json swaps to that new id — so the
# grandfathered id stops being a keeper and E9's exemption no longer applies to
# anything. Once every ISO's keeper has been re-registered with a twin, this set
# is dead code: delete it and E9 is unconditional, with NO other edit to E9.
# Do not ADD ids here — only remove them as each ISO's keeper gains a twin.
E9_ABLATION_TWIN_GRANDFATHER = frozenset(
    {
        # 2026-07-03-ercot32-ordc-total-rtolcap: removed 2026-07-06 — superseded
        # as ERCOT keeper by 2026-07-06-ercot34-stage4-overlay-off (registered
        # with its zero-forcing twin).
        "2026-07-03-caiso-51-firm-base",
        # 2026-07-03-pjm-76-outage-fix: removed 2026-07-05 — superseded as PJM
        # keeper by 2026-07-05-pjm-77-ct-relfloor (registered with its twin).
        # 2026-07-03-nyiso-41-hub-prices: removed 2026-07-06 — superseded as
        # NYISO keeper by 2026-07-06-nyiso-53-li-tsl (registered with its
        # zero-forcing twin), taking the grandfathered E9 exemption with it.
        # 2026-07-03-neiso-47-fast-start: removed 2026-07-05 — superseded as
        # NEISO keeper by 2026-07-05-neiso-48-ct-floor (registered with twin).
        # 2026-07-03-miso-39-reserve-pergen: removed 2026-07-06 — superseded as
        # MISO keeper by 2026-07-05-miso-41-ct-evening (registered with its own
        # zero-forcing twin, 2026-07-06-miso-41-ct-evening-ablation), taking the
        # grandfathered E9 exemption with it.
    }
)

# E7 staleness adjudications (CLAUDE.md gap register G-04, 2026-07-06 owner
# decision — see docs/calibration-log.md "2026-07-06 — G-04: E7 staleness
# adjudication"). Each key is the (keeper_run_id, newer_run_id) pair E7 flags;
# a pair present here has been reviewed and adjudicated KEEP — the newer run
# is a diagnostic probe, not a keeper candidate. This ANNOTATES the E7 WARN
# message with a pointer to that record; it never suppresses the warning (E7
# stays WARN either way — mirrors E9's grandfather-list PATTERN, not its
# suppress-to-WARN effect). A pair not in this dict — including one where the
# newer run was registered AFTER the adjudication date below — gets the
# plain, unadjudicated warning, since it has not itself been reviewed.
# NYISO's pair was adjudicated PROMOTE-pending (not KEEP) and RESOLVED
# 2026-07-06 by the L-11 keeper swap (nyiso-41 → 2026-07-06-nyiso-53-li-tsl,
# registered with its zero-forcing twin) — no NYISO entry is needed here.
# Round 2 (2026-07-06): after the day's keeper swaps (ERCOT→ercot34,
# NEISO→neiso-49, NYISO→nyiso-53, MISO→miso-42-coal-econ-ablation) E7 flags a
# new (keeper, newest-run) pair per ISO; the round-1 pairs referenced superseded
# keepers/probes and are dropped as dead keys (git history preserves them). All
# five newer runs are diagnostic probes by their own registry definition — see
# calibration-log "2026-07-06 — G-04 round 2".
E7_STALENESS_ADJUDICATED: dict[tuple[str, str], str] = {
    (
        "2026-07-06-ercot34-stage4-overlay-off",
        "2026-07-06-ercot37-g22-surface-on",
    ): "2026-07-06",
    (
        "2026-07-03-caiso-51-firm-base",
        "2026-07-06-caiso51-statmode-v2",
    ): "2026-07-06",
    (
        "2026-07-05-pjm-77-ct-relfloor",
        "2026-07-06-pjm-82-commitment-posture",
    ): "2026-07-06",
    (
        "2026-07-06-neiso-49-stgas-netload",
        "2026-07-06-neiso-wfuelsec-ab-v2off",
    ): "2026-07-06",
    (
        "2026-07-06-miso-42-coal-econ-ablation",
        "2026-07-06-miso-43-commitment-posture",
    ): "2026-07-06",
}

# H1 holdout quarantine (CLAUDE.md rule 22 / audit D-6, amended 2026-07-04).
# Kept stdlib-inline (this module must run without numpy/model imports); a
# parity test asserts these match legitimacy_diagnostics.D6_CALIBRATION_YEARS
# / D6_MARKER_FILE — the same gate run by `legitimacy_diagnostics --keepers`.
CALIBRATION_YEARS = frozenset({2023, 2024, 2025})
MARKER_FILE = DATA / "calibration-complete.json"


def holdout_quarantine_failures() -> list[str]:
    """Return H1 failure strings: registered bundles breaching the holdout.

    A registry sidecar (keeper OR probe) declaring a solve year outside
    ``CALIBRATION_YEARS`` fails unless its ISO carries a calibration-complete
    marker in ``calibration-complete.json`` (which authorizes the one-shot
    frozen-config holdout score of 2022 / H1-2026).
    """
    complete = (_load_json(MARKER_FILE) or {}).get("complete", {})
    fails = []
    for path in sorted(cv.REGISTRY_DIR.glob("*.json")):
        side = _load_json(path) or {}
        iso = side.get("iso", "?")
        breach = sorted({int(y) for y in side.get("years", [])} - CALIBRATION_YEARS)
        if breach and iso not in complete:
            fails.append(
                f"{path.stem}: solve year(s) {breach} outside the calibration "
                f"window {sorted(CALIBRATION_YEARS)} with no {iso} "
                f"calibration-complete marker in {MARKER_FILE.name} — holdout "
                "quarantine breach (CLAUDE.md rule 22)"
            )
    return fails


def ablation_twin_finding(
    run_id: str, side: dict, registry_dir: Path
) -> tuple[str, str]:
    """Return the E9 (ablation-twin) finding for one keeper: (level, message).

    ``level`` is ``"OK"`` / ``"WARN"`` / ``"FAIL"``. A keeper passes E9 iff its
    sidecar ``ablation_twin`` names a run with a registry sidecar in
    ``registry_dir``. A keeper on :data:`E9_ABLATION_TWIN_GRANDFATHER` WARNs
    (grace) instead of FAILing while it still lacks a twin; every other keeper
    without a resolvable twin FAILs (CLAUDE.md rule 20 / audit D-3). Pure over
    its inputs so it is unit-testable without the live registry.
    """
    twin_id = side.get("ablation_twin")
    twin_side = _load_json(registry_dir / f"{twin_id}.json") if twin_id else None
    if twin_id and twin_side is not None:
        return "OK", f"ablation twin registered ({twin_id})"
    # A DECLARED-but-broken link fails regardless of the grandfather grace: the
    # grace excuses "no twin yet", not a sidecar that asserts a twin that does
    # not resolve (catches a typo / an unregistered twin).
    if twin_id and twin_side is None:
        return (
            "FAIL",
            f'sidecar "ablation_twin" points to {twin_id!r} but no '
            f"registry/{twin_id}.json exists — register the twin "
            "(run_calibration_full.py --zero-forcing-ablation).",
        )
    if run_id in E9_ABLATION_TWIN_GRANDFATHER:
        return (
            "WARN",
            "no registered ablation twin — GRANDFATHERED (predates the D-3 "
            "requirement); enforced when this keeper is next re-registered "
            "(W2+). CLAUDE.md rule 20 / audit D-3.",
        )
    return (
        "FAIL",
        "keeper has no registered ablation twin: solve it with "
        "run_calibration_full.py --zero-forcing-ablation, register it as "
        "registry/<id>-ablation.json, and set the keeper sidecar "
        '"ablation_twin" field (CLAUDE.md rule 20 / audit D-3).',
    )


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _bundle_flags(bundle: Path) -> dict | None:
    cfg = _load_json(bundle / "run_config.json")
    return (cfg or {}).get("calibration_flags") if cfg else None


def _asserted_determination(definition: str) -> str | None:
    """Return the determination token the definition prose claims, if any.

    We only treat a token as an *assertion about this run's status* when it is
    not merely naming another run's recipe. The common, checkable phrasings are
    "Still NOT-YET", "now CALIBRATED", "remains CALIBRATED-WITH-CAVEATS", or a
    trailing "... NOT-YET." — i.e. the token stands on its own near a status
    verb. To stay conservative (avoid false positives) we require the token to
    appear AND not be immediately followed by "recipe"/"keeper"/"run".
    """
    text = definition or ""
    for tok in _DET_TOKENS:
        for m in re.finditer(re.escape(tok), text):
            tail = text[m.end() : m.end() + 8].lower()
            if tail.lstrip().startswith(("recipe", "keeper", "run", "step")):
                continue
            return tok
    return None


def _registry_dates_by_iso() -> dict[str, list[tuple[str, str]]]:
    """Map ISO -> sorted [(date, run_id)] across every registry sidecar.

    Zero-forcing ablation twins (run ids ending ``-ablation``, the D-3 naming
    convention enforced by ``run_calibration_full.py --zero-forcing-ablation``)
    are skipped: a twin is by definition never a keeper candidate (rule 20), so
    it must not make its own keeper — or any other run — look stale under E7.

    Sidecars explicitly marked ``"keeper_candidate": false`` are skipped for
    the same reason: a diagnostic probe (D-7 statistical-mode A/B runs, CO2
    re-basis probes, etc. — CLAUDE.md rule 15/#1) is never a keeper candidate
    regardless of how it's named, so it must not make a same-ISO keeper look
    stale under E7. Absence of the field (the default for every pre-existing
    sidecar) means "is a keeper candidate" — this is opt-in, not opt-out.
    """
    by_iso: dict[str, list[tuple[str, str]]] = {}
    for path in sorted(cv.REGISTRY_DIR.glob("*.json")):
        if path.stem.endswith("-ablation"):
            continue
        side = _load_json(path)
        if not side:
            continue
        if side.get("keeper_candidate") is False:
            continue
        iso = side.get("iso")
        date = side.get("date") or path.stem[:10]
        if iso:
            by_iso.setdefault(iso, []).append((date, path.stem))
    for iso in by_iso:
        by_iso[iso].sort()
    return by_iso


class Report:
    """Accumulates FAIL/WARN/OK findings, grouped by keeper, for one audit run."""

    def __init__(self) -> None:
        self.findings: list[dict] = []

    def add(self, run_id: str, iso: str, level: str, code: str, msg: str) -> None:
        self.findings.append(
            {"run_id": run_id, "iso": iso, "level": level, "code": code, "msg": msg}
        )

    def ok(self, run_id, iso, code, msg):
        self.add(run_id, iso, "OK", code, msg)

    def warn(self, run_id, iso, code, msg):
        self.add(run_id, iso, "WARN", code, msg)

    def fail(self, run_id, iso, code, msg):
        self.add(run_id, iso, "FAIL", code, msg)

    @property
    def n_fail(self) -> int:
        return sum(1 for f in self.findings if f["level"] == "FAIL")

    @property
    def n_warn(self) -> int:
        return sum(1 for f in self.findings if f["level"] == "WARN")


def audit_keeper(run_id: str, rep: Report, newest_by_iso: dict) -> None:
    """Run every per-keeper check (E1–E7) for one run id, recording findings."""
    side_path = cv.REGISTRY_DIR / f"{run_id}.json"
    side = _load_json(side_path)
    if side is None:
        rep.fail(run_id, "?", "E1", f"missing/unreadable sidecar {side_path.name}")
        return
    iso = side.get("iso", "?")

    # E1: payload + bundle exist.
    payload = REPO / side.get("file", "")
    if not side.get("file") or not payload.exists():
        rep.fail(run_id, iso, "E1", f"run payload missing: {side.get('file')!r}")
    bundle = REPO / side.get("bundle", "")
    if not side.get("bundle") or not bundle.exists():
        rep.fail(run_id, iso, "E1", f"bundle dir missing: {side.get('bundle')!r}")
        flags = None
    else:
        rep.ok(run_id, iso, "E1", "sidecar, payload and bundle present")
        flags = _bundle_flags(bundle)
        meta = _load_json(bundle / "meta.json")

    # E2 / E3: iso + years agree with the bundle the run was solved from.
    if flags is not None:
        if flags.get("iso") and flags["iso"] != iso:
            rep.fail(
                run_id, iso, "E2", f"sidecar iso={iso} but bundle iso={flags['iso']}"
            )
        else:
            rep.ok(run_id, iso, "E2", f"iso matches bundle ({iso})")
        side_years = sorted(side.get("years") or [])
        # meta.json["years"] is the authoritative solved span (what the verdict
        # scores and the dashboard renders); calibration_flags["years"] is an
        # invocation echo that some probe wrappers leave incomplete, so it is
        # only a cross-check, never the basis for a text-accuracy FAIL.
        meta_years = sorted((meta or {}).get("years") or [])
        flag_years = sorted(flags.get("years") or [])
        bundle_years = meta_years or flag_years
        if meta_years and flag_years and meta_years != flag_years:
            rep.warn(
                run_id,
                iso,
                "E3",
                f"bundle metadata inconsistent: meta.json years {meta_years} != "
                f"calibration_flags years {flag_years} (using meta.json)",
            )
        if bundle_years and side_years != bundle_years:
            rep.fail(
                run_id,
                iso,
                "E3",
                f"sidecar years {side_years} != bundle years {bundle_years}",
            )
        elif iso in _MULTI_YEAR_ISOS and len(side_years) < 2:
            rep.fail(
                run_id,
                iso,
                "E3",
                f"{iso} keeper covers only {side_years} — multi-year ISOs must "
                "register the full year span (claude.md #13)",
            )
        else:
            rep.ok(run_id, iso, "E3", f"years {side_years} match bundle")

    # E4: definition is real prose.
    definition = (side.get("definition") or "").strip()
    if not definition:
        rep.fail(run_id, iso, "E4", "definition is empty")
    elif _PLACEHOLDER_RE.match(definition):
        rep.fail(
            run_id,
            iso,
            "E4",
            "definition is the auto-generated placeholder "
            f'("{definition[:60]}…") — describe what the run actually changed',
        )
    else:
        rep.ok(run_id, iso, "E4", "definition is descriptive prose")

    # E5: definition's asserted determination matches the live verdict.
    try:
        verdict = cv.determine(run_id)
        live_det = verdict["determination"]
    except Exception as exc:  # scoring failure is itself a finding
        rep.fail(run_id, iso, "E5", f"verdict could not be computed: {exc}")
        live_det = None
    if live_det is not None:
        asserted = _asserted_determination(definition)
        if asserted and asserted != live_det:
            rep.fail(
                run_id,
                iso,
                "E5",
                f'definition asserts "{asserted}" but current verdict is '
                f'"{live_det}" — update the sidecar text',
            )
        else:
            note = f" (text says {asserted})" if asserted else ""
            rep.ok(run_id, iso, "E5", f"verdict {live_det}{note}")

    # E8: DOF ledger (CLAUDE.md rule 20 / audit D-12): the attestation must
    # carry a free_parameters section, and every residual-sourced parameter
    # must reference an open root cause — a residual that can only be closed
    # by a tuned value is an open root-cause issue, not a parameter.
    if side.get("bundle") and (REPO / side["bundle"]).exists():
        att = _load_json(REPO / side["bundle"] / "calibration_attestation.json")
        ledger = (att or {}).get("free_parameters")
        if ledger is None:
            rep.fail(
                run_id,
                iso,
                "E8",
                "attestation carries no free_parameters DOF ledger — seed it "
                "with scripts/build_dof_ledger.py (CLAUDE.md rule 20)",
            )
        else:
            bare = [
                e.get("name", "?")
                for e in ledger.get("entries", [])
                if e.get("identification") == "residual"
                and not str(e.get("root_cause", "")).strip()
            ]
            if bare:
                rep.fail(
                    run_id,
                    iso,
                    "E8",
                    "residual-sourced free parameter(s) without an open "
                    f"root-cause reference: {', '.join(bare)}",
                )
            else:
                n_res = sum(
                    1
                    for e in ledger.get("entries", [])
                    if e.get("identification") == "residual"
                )
                rep.ok(
                    run_id,
                    iso,
                    "E8",
                    f"DOF ledger present ({len(ledger.get('entries', []))} "
                    f"entries, {n_res} residual, all with root causes)",
                )

    # E9: ablation twin (CLAUDE.md rule 20 / audit D-3). A keeper must have a
    # registered zero-forcing ablation twin — registry/<id>-ablation.json,
    # linked from the keeper sidecar "ablation_twin" field — so the keeper-vs-
    # twin per-class delta is on the dashboard. Mirrors E8. Keepers on the
    # E9_ABLATION_TWIN_GRANDFATHER list (those predating D-3) WARN instead of
    # FAIL until they are re-registered with a twin (W2+); see the list docstring
    # for how the grace self-empties.
    level, msg = ablation_twin_finding(run_id, side, cv.REGISTRY_DIR)
    {"OK": rep.ok, "WARN": rep.warn, "FAIL": rep.fail}[level](run_id, iso, "E9", msg)

    # E7: staleness — is this the newest-dated run for its ISO?
    newest_date, newest_id = newest_by_iso.get(iso, (None, None))
    if newest_id and newest_id != run_id:
        adjudicated_on = E7_STALENESS_ADJUDICATED.get((run_id, newest_id))
        note = (
            f" — E7: adjudicated {adjudicated_on}, see calibration-log"
            if adjudicated_on
            else ""
        )
        rep.warn(
            run_id,
            iso,
            "E7",
            f"a newer {iso} run exists in the registry "
            f"({newest_id}, {newest_date}); keeper may be stale{note}",
        )
    elif newest_id:
        rep.ok(run_id, iso, "E7", "keeper is the newest run for its ISO")


def audit(isos: list[str] | None) -> Report:
    """Audit every keeper in keepers.json (optionally filtered to ``isos``)."""
    rep = Report()
    spec = _load_json(KEEPERS_FILE)
    if not spec:
        rep.fail("-", "-", "E0", f"cannot read {KEEPERS_FILE}")
        return rep
    keeper_ids = spec.get("keepers", [])

    # E6: exactly one keeper per ISO.
    seen: dict[str, list[str]] = {}
    for run_id in keeper_ids:
        side = _load_json(cv.REGISTRY_DIR / f"{run_id}.json")
        iso = (side or {}).get("iso", "?")
        seen.setdefault(iso, []).append(run_id)
    for iso, ids in seen.items():
        if len(ids) > 1:
            rep.fail(ids[0], iso, "E6", f"{iso} has {len(ids)} keepers: {ids}")

    newest_by_iso = _registry_dates_by_iso()
    newest_by_iso = {k: v[-1] for k, v in newest_by_iso.items()}

    want = {s.upper() for s in isos} if isos else None
    for run_id in keeper_ids:
        side = _load_json(cv.REGISTRY_DIR / f"{run_id}.json")
        iso = (side or {}).get("iso", "?")
        if want and iso.upper() not in want:
            continue
        audit_keeper(run_id, rep, newest_by_iso)

    # H1: holdout quarantine across EVERY registered bundle (keeper or probe).
    for msg in holdout_quarantine_failures():
        rep.fail("holdout", "-", "H1", msg)
    if not any(f["code"] == "H1" for f in rep.findings):
        rep.ok(
            "holdout",
            "-",
            "H1",
            f"no registered bundle breaches the {sorted(CALIBRATION_YEARS)} "
            "holdout quarantine",
        )

    # S1: global status.js sync check.
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_status.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        rep.ok("status.js", "-", "S1", proc.stdout.strip() or "status.js in sync")
    else:
        rep.fail(
            "status.js",
            "-",
            "S1",
            (proc.stdout + proc.stderr).strip()
            or "status.js stale — run scripts/build_status.py",
        )
    return rep


def _print_human(rep: Report) -> None:
    icons = {"OK": "✓", "WARN": "!", "FAIL": "✗"}
    # Group by run_id preserving first-seen order.
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for f in rep.findings:
        if f["run_id"] not in groups:
            order.append(f["run_id"])
            groups[f["run_id"]] = []
        groups[f["run_id"]].append(f)
    print("=" * 72)
    print("KEEPER TEXT AUDIT")
    print("=" * 72)
    for run_id in order:
        items = groups[run_id]
        iso = items[0]["iso"]
        worst = (
            "FAIL"
            if any(i["level"] == "FAIL" for i in items)
            else ("WARN" if any(i["level"] == "WARN" for i in items) else "OK")
        )
        print(f"\n[{icons[worst]}] {iso:6} {run_id}")
        for i in items:
            if i["level"] == "OK":
                continue  # keep the human view focused on problems
            print(f"      {icons[i['level']]} {i['code']}: {i['msg']}")
        if all(i["level"] == "OK" for i in items):
            print("      all checks passed")
    print("\n" + "-" * 72)
    verdict = "PASS" if rep.n_fail == 0 else "FAIL"
    print(f"{verdict}: {rep.n_fail} failure(s), {rep.n_warn} warning(s)")
    print("=" * 72)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--iso", nargs="+", help="restrict to these ISOs")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit 1 on any FAIL (same as default exit code)",
    )
    args = ap.parse_args()

    rep = audit(args.iso)
    if args.json:
        print(
            json.dumps(
                {"fail": rep.n_fail, "warn": rep.n_warn, "findings": rep.findings},
                indent=2,
            )
        )
    else:
        _print_human(rep)
    sys.exit(1 if rep.n_fail else 0)


if __name__ == "__main__":
    main()
