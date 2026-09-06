"""Scoring-provenance stamp for forecast verdict + board artifacts (FR-21).

The forecast-readiness audit's FR-21 finding is that **the T1 gate evidence went
stale and nothing detected it**: FF-2D scored on 2026-07-20, and over the ten
days that followed ~20 keeper promotions landed, the pinned default config cache
key moved twice (``2a1cb710`` → ``edbc1b10`` → ``603c2498``) and was
broken-and-restored once, and the NYISO forecast orchestrator was rewired — with
no FC verdict re-scored and no signal anywhere that the board had gone dark.

Nothing detected it because no artifact recorded **when, and against what, it was
scored**. This module is that record. Every verdict and board artifact carries::

    {"scored_at_sha": "<12-char HEAD sha>",     # the code the score ran against
     "scored_at_date": "YYYY-MM-DDTHH:MM:SSZ",  # UTC, when it ran
     "cache_epoch": "<config cache key>",       # the config identity it scored
     "solve_surface": {...},                    # the registry surface it solved on
     "schema": "forecast-provenance/v1"}

``cache_epoch`` is READ from the run's own artifacts (``run_config.json``'s
``cache_key``), never recomputed — the epoch that matters is the one the run
actually solved under, not whatever the code would produce today. It is ``None``
when the artifact does not carry one; an absent epoch is recorded as absent
rather than guessed.

``solve_surface`` (capx D79) is read the SAME way, from the artifact's own
``solve_surface`` block, and for the same reason: it is the registry surface the
run solved on, which today's code may no longer have. A run scored before the
fingerprint existed records ``None`` and keeps its historical stamp, exactly as
D60 §7 treats the hex-less t1x ``cache_epoch``s.

Consumers:

* ``scripts/forecast_verdict.py`` stamps every verdict it produces (and carries
  the stamp through ``condensed_sidecar`` into ``ff-verdicts.json``).
* ``scripts/register_forecast_run.py`` stamps each generated registry sidecar,
  run payload and the manifest meta.
* ``scripts/check_forecast_staleness.py`` reads the stamps back and WARNs when
  solve-affecting paths have moved N commits past the newest ``scored_at_sha``.

Stdlib-only (``json``/``subprocess``/``datetime``/``pathlib``) so it runs on the
bare ``python3`` the Pages deploy and the stdlib CI checks use. Every helper is
total: a missing git binary, a detached worktree or a malformed artifact yields
``None`` fields, never an exception — a provenance stamp must never be able to
fail a scoring run.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "forecast-provenance/v1"

REPO = Path(__file__).resolve().parents[2]

#: Fields every stamped artifact carries. Named once so the CI staleness check
#: and the tests agree with the emitters instead of re-listing string literals.
PROVENANCE_FIELDS = (
    "scored_at_sha",
    "scored_at_date",
    "cache_epoch",
    "solve_surface",
)

#: Where a provenance stamp is stored inside a stamped artifact.
PROVENANCE_KEY = "provenance"


def head_sha(short: int = 12) -> str | None:
    """Return the repo's current HEAD sha (``short`` chars), or ``None``.

    ``None`` whenever git cannot answer — no binary, no repo, a shallow or
    detached checkout that fails the call. Callers record the absence; they
    never substitute a placeholder that would read as a real commit.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    sha = out.stdout.strip()
    return sha[:short] if sha else None


def utc_now() -> str:
    """UTC scoring timestamp, second resolution (``YYYY-MM-DDTHH:MM:SSZ``)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cache_epoch_from(*artifacts: object) -> str | None:
    """Return the config cache key carried by the first artifact that has one.

    Searches, in order per artifact: a top-level ``cache_key``; a
    ``scenario_config``/``config`` wrapper's ``cache_key``; and a
    ``meta.cache_key`` (the shape ``full_horizon_summary.json`` uses). Returns
    ``None`` when no artifact carries an epoch — recorded as absent, never
    recomputed from today's code, because the epoch that matters is the one the
    run actually solved under.
    """
    for art in artifacts:
        if not isinstance(art, dict):
            continue
        key = art.get("cache_key")
        if isinstance(key, str) and key:
            return key
        for wrapper in ("scenario_config", "config", "meta", "run_config"):
            inner = art.get(wrapper)
            if isinstance(inner, dict):
                key = inner.get("cache_key")
                if isinstance(key, str) and key:
                    return key
    return None


def solve_surface_from(*artifacts: object) -> dict | None:
    """Return the ``solve_surface`` block carried by the first artifact with one.

    Searched exactly like :func:`cache_epoch_from`, and READ rather than
    recomputed for the same reason (capx D79): the surface that matters is the
    one the run solved on. ``None`` when no artifact carries one — a run scored
    before the fingerprint existed, recorded as absent rather than guessed.
    """
    for art in artifacts:
        if not isinstance(art, dict):
            continue
        for candidate in (art, *(art.get(w) for w in ("meta", "run_config"))):
            if not isinstance(candidate, dict):
                continue
            block = candidate.get("solve_surface")
            if isinstance(block, dict) and block:
                return block
    return None


def stamp(*artifacts: object, cache_epoch: str | None = None) -> dict:
    """Build the provenance stamp for an artifact about to be written.

    ``artifacts`` are searched for a ``cache_key`` (see :func:`cache_epoch_from`)
    unless ``cache_epoch`` is passed explicitly, and for a ``solve_surface``
    block (see :func:`solve_surface_from`). Always returns every field in
    :data:`PROVENANCE_FIELDS`, using ``None`` for anything unavailable, so a
    consumer can distinguish "not recorded" from "recorded as empty".
    """
    return {
        "schema": SCHEMA,
        "solve_surface": solve_surface_from(*artifacts),
        "scored_at_sha": head_sha(),
        "scored_at_date": utc_now(),
        "cache_epoch": (
            cache_epoch if cache_epoch is not None else cache_epoch_from(*artifacts)
        ),
    }


def read_stamp(obj: object) -> dict | None:
    """Return the provenance stamp inside ``obj``, or ``None`` if unstamped.

    Accepts the stamped object itself (``{"provenance": {...}}``) or a bare
    stamp. An object carrying a ``provenance`` value that is not a dict reads as
    unstamped rather than raising — the staleness check must survive any
    hand-edited board file.
    """
    if not isinstance(obj, dict):
        return None
    prov = obj.get(PROVENANCE_KEY)
    if isinstance(prov, dict):
        return prov
    if any(f in obj for f in PROVENANCE_FIELDS):
        return {f: obj.get(f) for f in PROVENANCE_FIELDS}
    return None


def collect_stamps(paths: list[Path]) -> list[tuple[Path, dict]]:
    """Read every provenance stamp reachable from ``paths`` (files or dirs).

    A JSON file may hold one stamped object or a mapping of stamped objects
    (``ff-verdicts.json`` is the latter: one verdict per key); both are walked
    one level deep. Unreadable/unstamped files are skipped silently — this is a
    WARN-level detector, and a file with no stamp is simply not evidence.
    """
    found: list[tuple[Path, dict]] = []
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.json")))
        elif p.is_file():
            files.append(p)
    for f in files:
        try:
            doc = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        top = read_stamp(doc)
        if top:
            found.append((f, top))
            continue
        if isinstance(doc, dict):
            for value in doc.values():
                nested = read_stamp(value)
                if nested:
                    found.append((f, nested))
    return found
