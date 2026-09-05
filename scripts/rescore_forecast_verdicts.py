#!/usr/bin/env python
"""Re-score the forecast board's verdicts that still have surviving artifacts (FFR-3A).

FR-21 gave every forecast board artifact a provenance stamp
(``scripts/lib/forecast_provenance``) so staleness could be detected. FFR-3A is
the other half: **re-score the T1 battery through the stamped scorer** so the
board's verdicts carry a real ``scored_at_sha`` / ``scored_at_date`` instead of a
bare epoch label or nothing at all.

Most of the battery cannot be re-scored, and that is a measurement, not a gap in
this script. The FFR-3A-2 / FFR-3A-3 bundles are **gitignored by design**
(``results/ffr3a2/README.md``: "Everything under here except this README is
gitignored") — only their README and scorecard are tracked. Their
``full_horizon_summary.json`` / invariants / ``run_config.json`` never entered the
repository, so no re-score is possible from a checkout and manufacturing one
would need an LP solve. This script therefore re-scores **only** the verdicts
whose source bundle is tracked, and reports the rest as unrecoverable.

Which verdicts those are is not inferred here. ``register_forecast_run.VERDICT_MAP``
is the committed run_id -> verdict-key mapping the registrar itself uses; this
script reads it and keeps every verdict whose mapped run_id has a tracked score
artifact under ``results/hindcast/``. At the time of writing that is 7 of the 39
board verdicts — and they are exactly the 7 that carry no provenance stamp at
all, which is the reason FFR-3A exists.

**Re-scoring may legitimately move a verdict**, and this script never suppresses
that: it prints the before/after category diff for every entry it writes. Two
movements are expected and are properties of the scorer, not of the model:

* the scorer now emits an explicit ``run_config absent`` FAIL row in FC-7 where
  the older one silently omitted the row (FC-7 CAVEAT -> FAIL), and
* FC-1 / FC-2 read SKIPPED wherever the original score consumed a
  ``check_forecast_invariants.py`` output that was never committed — the board's
  old reading rests on an artifact no checkout holds, which is precisely the
  unverifiable evidence FR-21 exists to surface.

Nothing here re-grades, widens a band, or hand-edits a determination
(CLAUDE.md rule 1 ``[R-STRUCT]``): every value written is the scorer's own output
on committed artifacts.

It also normalizes the board's short ``scored_at_sha`` values to the 12-char
``forecast-provenance/v1`` convention, but only where the prefix provably names
one commit (:data:`SHA_EXPANSIONS`) — an unresolvable prefix is left alone and
reported, because an unreachable true sha beats a reachable false one.

Usage::

    python scripts/rescore_forecast_verdicts.py            # dry run (default)
    python scripts/rescore_forecast_verdicts.py --apply    # write ff-verdicts.json
    # expand short shas on an already-re-scored board, without re-stamping it:
    python scripts/rescore_forecast_verdicts.py --no-rescore --normalize-shas --apply

Stdlib-only, so it runs on the bare ``python3`` the stdlib CI jobs use.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:  # resolve ``scripts.lib`` when run as a plain script
    sys.path.insert(0, str(REPO))

VERDICTS = REPO / "frontend/data/forecast/ff-verdicts.json"
#: The §2.1b board seed. A committed board input that carries its own
#: ``scored_at_sha``, so sha normalization must cover it too.
SEED = REPO / "frontend/data/forecast/program-status.json"
HINDCAST_ROOT = REPO / "results/hindcast"

#: Score-artifact filename per tier. FC-3 (t1h) reads ``score.json``; FC-4 (t1x)
#: reads ``crossover_score.json`` — the two primary instruments the rubric names.
SCORE_FILE_BY_TIER = {"t1h": "score.json", "t1x": "crossover_score.json"}

#: CLI flag each tier's score artifact is passed under.
SCORE_FLAG_BY_TIER = {"t1h": "--hindcast-score", "t1x": "--crossover-score"}

#: The ONLY years a score artifact may cover (CLAUDE.md rule 22 ``[R-HOLDOUT]``:
#: train = 2023-2025, the only years scored without a per-ISO tier marker). This
#: script never solves, but it does SCORE, and rule 22 gates scoring too — so it
#: fails closed on any artifact whose ``scored_years`` leaves the window. The
#: 2021 hindcast seed and 2022 bridge are legal *solve* years that are never
#: scored (``scripts/lib/holdout_policy`` HINDCAST_SEED_YEARS / _BRIDGE_YEARS),
#: which is why a 2021-2025 bundle still passes this check.
SCORED_YEARS_ALLOWED = frozenset({2023, 2024, 2025})

#: 8-char scored-at shas on the board, expanded to the 12-char
#: ``forecast_provenance`` convention. Both were written by tools that stamp with
#: ``git rev-parse --short HEAD`` (``scripts/merge_ffr3a2_verdicts._sha`` and
#: ``scripts/build_ffr3a2_scorecard.scored_at_sha``) instead of
#: ``forecast_provenance.head_sha()``, which is why they are short.
#:
#: These are EXPANSIONS OF THE SAME COMMIT, never substitutions. Each prefix was
#: resolved against the GitHub commit API on 2026-08-24 and returned exactly one
#: 40-char sha whose commit corroborates the stamping session — an ambiguous
#: prefix returns an error rather than a commit, so a unique resolution is proof:
#:
#:   8ba59281 -> 8ba592814d921122cf9cb1121a0f3c080f7c6938
#:       "FFR-3A-2: the per-ISO section-2.1b gate scorecard", 2026-08-04, which
#:       is the session recorded in those 13 verdicts' own ``session`` field.
#:   e2a422c1 -> e2a422c191aa693a3fbc4f94b407deee99b8268f
#:       "FFR-3A-3: PJM T1-X post-FFR-3F", 2026-08-04, the FFR-3A-3 session
#:       recorded in those 6 verdicts' ``session`` field.
#:
#: Neither is reachable in a shallow checkout and neither appears in
#: ``docs/governance/citation-commit-map.txt``, so local absence proves nothing
#: either way (docs/FINDING-history-rewrite-2026-08-16.md). A prefix that cannot
#: be resolved to exactly one commit is NOT listed here and stays 8 chars: an
#: unreachable true sha beats a reachable false one.
SHA_EXPANSIONS = {
    "8ba59281": "8ba592814d92",
    "e2a422c1": "e2a422c191aa",
}


def _load_registrar():
    """Import ``register_forecast_run`` for its committed ``VERDICT_MAP``.

    Loaded by path rather than imported as a module because ``scripts`` is not a
    package on every checkout, and executed defensively: the registrar is a CLI
    and must never be able to take this process down at import time.
    """
    spec = importlib.util.spec_from_file_location(
        "_rfr", REPO / "scripts/register_forecast_run.py"
    )
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:  # a CLI module that argparses at import must not kill us
        pass
    return mod


def find_score_artifact(run_id: str, tier: str) -> Path | None:
    """Return the tracked score artifact for ``run_id`` at ``tier``, else ``None``.

    Refuses an ambiguous bundle: a run whose directory holds more than one score
    artifact is reported as unresolvable rather than guessed at, because picking
    one would attach a stamp to a verdict that may not describe it.
    """
    name = SCORE_FILE_BY_TIER.get(tier)
    if not name:
        return None
    hits = sorted((HINDCAST_ROOT / run_id).glob(f"*/*/{name}"))
    return hits[0] if len(hits) == 1 else None


def holdout_violations(artifact: Path) -> list[str]:
    """Return rule-22 ``[R-HOLDOUT]`` violations in an artifact's scored years.

    Fails closed: an artifact that records no ``scored_years`` at all is a
    violation, because an unknown scoring window cannot be shown to be in-window.
    """
    try:
        doc = json.loads(artifact.read_text())
    except (OSError, ValueError) as exc:
        return [f"unreadable score artifact ({exc})"]
    years = doc.get("scored_years")
    if not isinstance(years, list) or not years:
        return ["artifact records no scored_years — cannot prove it is in-window"]
    out = [
        f"scored year {y} is outside the training window "
        f"{sorted(SCORED_YEARS_ALLOWED)} (rule 22 [R-HOLDOUT])"
        for y in sorted({int(y) for y in years})
        if int(y) not in SCORED_YEARS_ALLOWED
    ]
    return out


def rescore(artifact: Path, tier: str, run_id: str) -> dict | None:
    """Run ``forecast_verdict.py`` on one bundle and return its condensed sidecar.

    Invoked as a subprocess rather than in-process so the verdict written to the
    board is byte-for-byte what the documented CLI produces; ``None`` when the
    scorer cannot be parsed. A ``run_config.json`` is passed only when the bundle
    actually tracks one — never substituted from elsewhere.
    """
    cmd = [
        sys.executable,
        str(REPO / "scripts/forecast_verdict.py"),
        "--tier",
        tier,
        SCORE_FLAG_BY_TIER[tier],
        str(artifact),
        "--json",
    ]
    run_config = HINDCAST_ROOT / run_id / "run_config.json"
    if run_config.exists():
        cmd += ["--run-config", str(run_config)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO))
    try:
        verdict = json.loads(proc.stdout)
    except ValueError:
        return None
    spec = importlib.util.spec_from_file_location(
        "_fv", REPO / "scripts/forecast_verdict.py"
    )
    fv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fv)
    return fv.condensed_sidecar(verdict)


def _statuses(entry: dict) -> dict:
    """Return ``{category: status}`` for a board entry in either sidecar schema."""
    return {
        c: (v or {}).get("status") for c, v in (entry.get("categories") or {}).items()
    }


def plan() -> list[dict]:
    """Return one record per board verdict describing whether it is re-scorable.

    Each record carries the verdict id, its tier, the ``VERDICT_MAP`` run_id (or
    ``None`` when the verdict is unmapped), the tracked score artifact (or
    ``None``), and any rule-22 violation that blocks it.
    """
    board = json.loads(VERDICTS.read_text())
    reverse: dict[str, str] = {}
    for run_id, key in _load_registrar().VERDICT_MAP.items():
        reverse.setdefault(key, run_id)
    out = []
    for vid in sorted(board):
        tier = board[vid].get("tier")
        run_id = reverse.get(vid)
        artifact = find_score_artifact(run_id, tier) if run_id else None
        out.append(
            {
                "id": vid,
                "tier": tier,
                "run_id": run_id,
                "artifact": artifact,
                "blocked": holdout_violations(artifact) if artifact else [],
            }
        )
    return out


def normalize_shas(doc, where: str = "") -> list[tuple[str, str, str]]:
    """Expand short ``scored_at_sha`` values in ``doc`` in place, recursively.

    Walks any nested dict/list so one code path covers both board inputs
    (``ff-verdicts.json``'s per-verdict ``provenance`` blocks and
    ``program-status.json``'s ``refresh`` block). Only ``scored_at_sha`` is
    touched, and only for a prefix with a proven unique expansion in
    :data:`SHA_EXPANSIONS`; every other short sha is left exactly as written.
    ``derived_at_sha`` is deliberately NOT touched — the records lane keeps those
    field names outside ``forecast-provenance/v1`` precisely so a re-key can
    never be misread as a re-score (docs/FINDING-fr21-provenance-not-lost).

    Returns ``(location, before, after)`` per change, so the caller reports each
    one rather than making it silently.
    """
    changed: list[tuple[str, str, str]] = []
    if isinstance(doc, dict):
        for key in sorted(doc):
            value = doc[key]
            if key == "scored_at_sha" and isinstance(value, str):
                new = SHA_EXPANSIONS.get(value)
                if new and new != value:
                    doc[key] = new
                    changed.append((where or key, value, new))
            else:
                changed += normalize_shas(value, f"{where}.{key}" if where else key)
    elif isinstance(doc, list):
        for i, value in enumerate(doc):
            changed += normalize_shas(value, f"{where}[{i}]")
    return changed


def remaining_short_shas(doc) -> list[str]:
    """Return every ``scored_at_sha`` in ``doc`` still shorter than 12 chars.

    Reported rather than fixed: a short sha with no proven unique expansion is
    left alone deliberately, and naming it is how that stays visible.
    """
    out: list[str] = []
    if isinstance(doc, dict):
        for key, value in doc.items():
            if key == "scored_at_sha" and isinstance(value, str) and len(value) < 12:
                out.append(value)
            else:
                out += remaining_short_shas(value)
    elif isinstance(doc, list):
        for value in doc:
            out += remaining_short_shas(value)
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: report the re-score plan and, with ``--apply``, write the board."""
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--apply", action="store_true", help="write ff-verdicts.json (default: dry run)"
    )
    ap.add_argument(
        "--normalize-shas",
        action="store_true",
        help="also expand the short scored-at shas with a proven unique "
        "expansion (SHA_EXPANSIONS) to the 12-char convention",
    )
    ap.add_argument(
        "--no-rescore",
        action="store_true",
        help="skip the re-score pass. Use with --normalize-shas to expand shas "
        "on an already-re-scored board without re-stamping it with a fresh "
        "timestamp for no change in content.",
    )
    args = ap.parse_args(argv)

    board = json.loads(VERDICTS.read_text())
    records = plan()
    doable = [r for r in records if r["artifact"] and not r["blocked"]]
    blocked = [r for r in records if r["artifact"] and r["blocked"]]

    print(f"board verdicts       : {len(records)}")
    print(f"re-scorable          : {len(doable)}")
    print(f"blocked by rule 22   : {len(blocked)}")
    print(f"no tracked artifact  : {len(records) - len(doable) - len(blocked)}")
    for r in blocked:
        print(f"  BLOCKED {r['id']}: {'; '.join(r['blocked'])}")
    print("-" * 78)

    written = 0
    for r in [] if args.no_rescore else doable:
        sidecar = rescore(r["artifact"], r["tier"], r["run_id"])
        if sidecar is None:
            print(f"  SCORER FAILED {r['id']} — left untouched")
            continue
        before, after = _statuses(board[r["id"]]), _statuses(sidecar)
        moved = {
            c: (before.get(c), after.get(c))
            for c in sorted(set(before) | set(after))
            if before.get(c) != after.get(c)
        }
        prov = sidecar.get("provenance") or {}
        print(
            f"  {r['id']}\n"
            f"      source      : {r['artifact'].relative_to(REPO)}\n"
            f"      determination: {board[r['id']].get('determination')} -> "
            f"{sidecar.get('determination')}\n"
            f"      stamp       : {prov.get('scored_at_sha')} @ {prov.get('scored_at_date')}\n"
            f"      moved       : {moved or 'nothing'}"
        )
        board[r["id"]] = sidecar
        written += 1

    seed_doc = None
    if args.normalize_shas:
        print("-" * 78)
        expanded = normalize_shas(board)
        # The seed carries the same prefix in its own `refresh` block and is a
        # watched board input, so it is normalized in the same pass.
        seed_doc = json.loads(SEED.read_text())
        seed_changes = normalize_shas(seed_doc, SEED.name)
        for where, old, new in expanded + seed_changes:
            print(f"  sha {old} -> {new}  ({where})")
        still_short = sorted(
            set(remaining_short_shas(board)) | set(remaining_short_shas(seed_doc))
        )
        print(
            f"  expanded {len(expanded) + len(seed_changes)} stamp(s); "
            f"still short: {still_short or 'none'}"
        )

    if args.apply:
        # indent=1 + sort_keys is the board file's canonical on-disk format
        # (the retired merge_ffr3a2_verdicts.py wrote it the same way), so the diff
        # shows only the re-scored entries instead of reflowing all 39.
        VERDICTS.write_text(json.dumps(board, indent=1, sort_keys=True) + "\n")
        print(f"\nwrote {VERDICTS.relative_to(REPO)} ({written} verdict(s) re-scored)")
        if seed_doc is not None:
            # The seed's own canonical format (indent=1, key order preserved —
            # NOT sort_keys, unlike the verdicts file), matched so the diff is
            # the sha line alone rather than a whole-file reflow.
            SEED.write_text(json.dumps(seed_doc, indent=1) + "\n")
            print(f"wrote {SEED.relative_to(REPO)}")
    else:
        print(f"\nDRY RUN — {written} verdict(s) would be re-scored. Pass --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
