#!/usr/bin/env python
"""Register forecast-family runs on the forecast run explorer + status dashboard.

This is the SINGLE registration path for the Forecast Finalization Program
(FF) dashboard (plan `docs/forecast-development-plan-2026-07.md` §8, FF-5A). It
supersedes the two former helpers as the one entry point — `register_hindcast.py`
(capacity-hindcast / crossover sidecars) and `register_forecast_baseline.py`
(T1-F / CES-POC full-horizon summaries) now delegate here — while keeping the
existing self-contained `frontend/data/hindcast/<id>.json` sidecars working
verbatim (they stay the canonical committed per-run record; rule 19 spirit: one
registration path, one wire format).

Two namespaces, deliberately separate from the CI-gated backcast registry
(plan §7.5 — the backcast quarantine gates never learn a forecast id):

  * ``frontend/data/hindcast/<id>.json``  — the CANONICAL per-run record
    (run meta + score + forecast-invariant summary). Unchanged; produced by the
    ``--bundle`` / ``--summary`` registration paths (which reuse
    ``register_hindcast.build_sidecar`` / ``register_forecast_baseline`` so the
    invariant/scoring logic lives in exactly one place).
  * ``frontend/data/forecast/``            — the NEW run-explorer namespace,
    mirroring the backcast sidecar/payload split so the shell HTML stays small
    and lazy-loads run detail. The registry/runs/manifest/program-status.js are
    GENERATED (gitignored — the Pages deploy is their single writer; regenerate
    locally with ``--reindex`` for the ``file://`` preview); they are fully
    derivable from the two COMMITTED inputs below plus the hindcast sidecars:
      - ``registry/<id>.json`` — generated lean index sidecar (id/iso/kind/tier
        + baked rubric-verdict summary). The manifest is assembled from these.
      - ``runs/<id>.js``       — generated gzip+base64 full-detail payload
        (``window.FF.runGz[<id>]``): meta, invariants I1–I14, the rubric verdict
        (FC-1..FC-8 gating rows), score, evolution-ledger trajectory.
      - ``manifest.js``        — generated (``window.FF.meta`` + ``window.FF.manifest``).
      - ``program-status.js``  — generated from the committed ``program-status.json``
        seed (``window.FF.programStatus``) — the per-ISO §2.1b evidence board.
    COMMITTED inputs (the source, NOT output): ``program-status.json`` (the
    §2.1b board seed) and ``ff-verdicts.json`` (the FF-2D rubric-verdict snapshot).

**Verdict provenance & the deploy split.** The rubric verdicts
(``docs/handoffs/ff-t1-gate-verdicts.json``) are NOT in the Pages sparse-checkout,
so a COMMITTED snapshot ``frontend/data/forecast/ff-verdicts.json`` is read instead
and the FC-1..FC-8 verdicts are BAKED into the generated registry sidecars + run
payloads. ``--reindex`` (stdlib-only: json/gzip/base64) is therefore ALSO the
Pages-deploy assembly step — it reads only committed ``frontend/`` files (hindcast
sidecars + the two snapshots) and regenerates the whole namespace into ``_site``,
with no ``docs/handoffs`` dependency and no LP/numpy deps.

Usage::

    # register one run (writes the hindcast sidecar + refreshes the namespace)
    python scripts/register_forecast_run.py --bundle results/hindcast/pjm-2021-2025-curve
    python scripts/register_forecast_run.py --summary results/ff-t1f-baseline/miso/full_horizon_summary.json --label ff-t1f-baseline

    # (re)generate the whole forecast namespace from the committed inputs
    python scripts/register_forecast_run.py --reindex                 # repo checkout (preview)
    python scripts/register_forecast_run.py --reindex --site-dir _site  # Pages deploy staging
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:  # resolve ``scripts.lib`` when run as a plain script
    sys.path.insert(0, str(REPO))

from scripts.lib import forecast_provenance as fp  # noqa: E402  (after sys.path)

# --- namespaces -----------------------------------------------------------
HINDCAST_DIR = REPO / "frontend" / "data" / "hindcast"  # canonical per-run record
FORECAST_DIR = REPO / "frontend" / "data" / "forecast"  # new run-explorer namespace
REGISTRY_DIR = FORECAST_DIR / "registry"
RUNS_DIR = FORECAST_DIR / "runs"
MANIFEST_JS = FORECAST_DIR / "manifest.js"
PROGRAM_STATUS_JSON = FORECAST_DIR / "program-status.json"
PROGRAM_STATUS_JS = FORECAST_DIR / "program-status.js"

# Rubric verdicts (FF-2D). In-session only — never read by --build.
VERDICTS_PATH = REPO / "docs" / "handoffs" / "ff-t1-gate-verdicts.json"

# Canonical forecast-invariant names I1..I14 (from check_forecast_invariants;
# baseline sidecars carry the full set, gate sidecars store only the non-PASS
# rows + an ``invariants_note`` listing which idents are PASS-omitted).
INV_NAMES = {
    "I1": "energy balance",
    "I2": "no NaN/inf",
    "I3": "unserved/dump",
    "I4": "capacity accounting",
    "I5": "no retire-and-reenter",
    "I6": "econ-retirement sanity",
    "I7": "reliability floor",
    "I8": "planned-additions gating",
    "I9": "storage integrity",
    "I10": "RPS dual sign+stability",
    "I11": "one-pass",
    "I12": "reserve-margin band",
    "I13": "cobweb detector",
    "I14": "price sanity",
}

# Explicit run_id -> verdict-key map for the FF-2D gate battery. The verdict
# keys (``ercot-t1f``, ``pjm-t1x``, ``pjm-2021-2025-curve-ff2c-t1h``) do NOT
# uniformly match run ids, and a wrong attachment would mislabel a run, so the
# gate runs are mapped explicitly rather than heuristically. A run's meta may
# also carry ``verdict_key`` to override (future runs); ``--verdict-key`` sets it.
VERDICT_MAP = {
    "ercot-2026-2030-ff-t1-gate": "ercot-t1f",
    "caiso-2026-2030-ff-t1-gate": "caiso-t1f",
    "pjm-2026-2030-ff-t1-gate": "pjm-t1f",
    "miso-2026-2030-ff-t1-gate": "miso-t1f",
    "nyiso-2026-2030-ff-t1-gate": "nyiso-t1f",
    "neiso-2026-2030-ff-t1-gate": "neiso-t1f",
    # Only the FF-2D re-solve (-ff2d) carries the FF-2D t1x verdict. The older
    # plain FF-0E crossover solves have their OWN (different) dispatch-skill score,
    # so attaching the ff2d verdict to them would contradict the run's own score
    # on the same page (a PASS/FAIL flip) — they render score-only, no verdict.
    "ercot-2023-2027-crossover-ff2d": "ercot-t1x",
    "pjm-2023-2027-crossover-ff2d": "pjm-t1x",
    # FFR-2A re-solved the T1-X battery at post-Wave-1 HEAD (audit FR-21: the
    # FF-2D comparators predate ~20 keeper promotions and the Wave-1 forecast
    # fixes) and added MISO, which FF-2D launched but never registered. Each
    # carries its OWN re-measured verdict key for exactly the reason the ff2d
    # comment above gives — a run must never render a verdict its own score
    # contradicts. The -ff2d rows stay pointed at the -ff2d verdicts.
    "ercot-2023-2027-crossover-ffr2a": "ercot-t1x-ffr2a",
    "pjm-2023-2027-crossover-ffr2a": "pjm-t1x-ffr2a",
    "miso-2023-2027-crossover-ffr2a": "miso-t1x-ffr2a",
    "pjm-2021-2025-curve-ff2c": "pjm-2021-2025-curve-ff2c-t1h",
    "miso-2021-2025-curve-ff2c": "miso-2021-2025-curve-ff2c-t1h",
    "neiso-2021-2025-curve": "neiso-2021-2025-curve-t1h",
    "nyiso-2021-2025-curve": "nyiso-2021-2025-curve-t1h",
    # FFR-3A-3 re-measured the T1-H and T1-X halves at the post-FFR-3F HEAD,
    # because FFR-3A-2's own provenance ceiling recorded that its battery had
    # measured a SUPERSEDED configuration: the G3 cap-grain fix (`2adfb49`) is
    # unconditional and changes the admitted exit set — the economic-retirement
    # screen every T1-H finding rests on. Each leg carries its OWN verdict key
    # for the same reason the FFR-2A block above gives: a run must never render
    # a verdict its own score contradicts, and these scores differ from the
    # pre-fix ones (MISO's `retire.total_gw` flips PASS -> FAIL, PJM's depth
    # moves 22.415 -> 18.862 GW). The pre-fix rows stay pointed at their own
    # verdicts and remain valid at the sha they record.
    "neiso-2021-2025-realized-ffr3a3": "neiso-2021-2025-realized-ffr3a3-t1h",
    "nyiso-2021-2025-realized-ffr3a3": "nyiso-2021-2025-realized-ffr3a3-t1h",
    "pjm-2021-2025-realized-ffr3a3": "pjm-2021-2025-realized-ffr3a3-t1h",
    "miso-2021-2025-realized-ffr3a3": "miso-2021-2025-realized-ffr3a3-t1h",
    "ercot-2023-2027-crossover-ffr3a3": "ercot-2023-2027-crossover-ffr3a3-t1x",
    "pjm-2023-2027-crossover-ffr3a3": "pjm-2023-2027-crossover-ffr3a3-t1x",
    # FFR-3A-4 measured the ONE leg the FFR-3A battery never got: MISO T1-X,
    # which FFR-3A-3 launched twice and lost twice to OOM and correctly left as
    # a null board cell rather than a stale value. Its own verdict key, for the
    # same reason every block above gives — a run must never render a verdict
    # its own score contradicts. It is NOT pointed at the generic `miso-t1x`
    # (an older FF-0E solve with a different dispatch-skill score) nor at
    # `miso-t1x-ffr2a`; the pre-fix `miso-2023-2027-crossover-ffr3a2` stays
    # unmapped and renders score-only, exactly as it did before.
    "miso-2023-2027-crossover-ffr3a4": "miso-2023-2027-crossover-ffr3a4-t1x",
    # capx-D10 (2026-08-30) measured NYISO's FIRST-EVER T1-X crossover — no
    # prior `nyiso-t1x` key existed anywhere, so the bare per-tier key IS this
    # run's own verdict (the LIVE-vintage convention) and cannot contradict any
    # other run's score. Chartered by owner card A (A-A, 2026-08-25) so §2.1b
    # leg (c) closes on a MEASURED FC-4 rather than an absent one.
    "nyiso-2023-2027-crossover-capxd10": "nyiso-t1x",
    # capx-D14 (2026-08-30) measured NEISO's FIRST-EVER T1-X crossover.
    # NEISO-RC-R Phase B (2026-08-31) re-solved the crossover at post-repair
    # HEAD (R1 confirmed-registry intake + R2 published-evidence FCA curve +
    # R3 dual-basis scorer); the bare live key moves to the NEW run (the
    # LIVE-vintage convention) and the capxd14 control keeps its OWN verdict
    # under the preserved `-pre-rcrepair` key (the -pre-d5r
    # preserve-then-overwrite precedent) — a run never renders a verdict its
    # own score contradicts. Determination HOLD on both, no flip.
    "neiso-2023-2027-crossover-capxd14": "neiso-t1x-pre-rcrepair",
    "neiso-2023-2027-crossover-rcrepair": "neiso-t1x",
    # capx-D27 (2026-09-01) re-measured MISO's T1-H leg at HEAD, executing
    # D17-R's routed PRIMARY R1: the committed MISO T1-H numbers predate the
    # S-123 adequacy package, whose three operands are registry constants the
    # admission cap and execution floor already read at HEAD. The bare live key
    # moves to the NEW run (the LIVE-vintage convention) and the prior
    # FFR-3A-2-vintage record keeps its OWN verdict under the preserved
    # `-pre-d27` key (the -pre-d5r / -pre-rcrepair precedent) — a run never
    # renders a verdict its own score contradicts, and these scores differ
    # sharply from the pre-fix ones (`retire.total_gw` 12.716 -> 26.431 GW,
    # its band FAIL flipping sign from under- to OVER-retirement).
    # Determination HOLD on both, no flip.
    "miso-2021-2025-realized-t1h-d27": "miso-t1h",
}


# --------------------------------------------------------------------------- #
# gzip+base64 codec (matches scripts/lib/backcast_artifacts.gzb64 — inlined so
# --build stays a bare-python3, zero-import stdlib step for the Pages deploy).
# --------------------------------------------------------------------------- #
def _gzb64(obj) -> str:
    """gzip+base64 of a JSON-serializable object (byte-deterministic, mtime=0)."""
    return base64.b64encode(
        gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)
    ).decode()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Classification — (kind, tier, family) from a canonical hindcast sidecar.
# --------------------------------------------------------------------------- #
def classify(run_id: str, meta: dict, has_score: bool) -> tuple[str, str, str]:
    """Return ``(kind, tier, family)`` for a forecast-family run.

    ``kind`` is the run family the explorer filters by (t1f/t1x/t1h/ces-poc/
    adequacy/readiness/t3-golden); ``tier`` places it on the §2.1 ladder
    (t1f/t1x/t1h/poc/battery/t3); ``family`` distinguishes gate vs baseline
    within t1f. Of the schema-ready tiers (t2/t3-golden/pb-band), ``t3-golden``
    is populated by §2.1b-authorized campaigns (the first: the Q13-authorized
    NEISO 2026–2050 BAU golden, lane T3-NEISO-GOLDEN); t2/pb-band remain
    unpopulated until their owner-gated waves.
    """
    mk = (meta or {}).get("kind")
    label = (meta or {}).get("label") or ""
    if mk == "readiness":
        return "readiness", "battery", "battery"
    if mk == "t3":
        # §2.1b-authorized full-horizon golden campaign (matches the
        # schema_ready kind "t3-golden" / tier "t3" the explorer already maps).
        return "t3-golden", "t3", "golden"
    if mk == "crossover":
        return "t1x", "t1x", "crossover"
    if mk == "ces-poc":
        return "ces-poc", "poc", "ces"
    if mk == "t1f":
        if label == "ff-2b-adequacy":
            return "adequacy", "t1f", "adequacy"
        if label == "ff-t1-gate":
            return "t1f", "t1f", "gate"
        return "t1f", "t1f", "baseline"
    # kind None/'hindcast' with a capacity score => a T1-H capacity hindcast leg.
    if has_score or mk == "hindcast":
        return "t1h", "t1h", "hindcast"
    # Fallback: forecast-mode with a year_summary but no score => t1f baseline.
    if (meta or {}).get("mode") == "forecast":
        return "t1f", "t1f", "baseline"
    return "t1h", "t1h", "hindcast"


def _verdict_key(run_id: str, meta: dict) -> str | None:
    """Resolve the FF-2D verdict key for a run (explicit map > meta override)."""
    if meta.get("verdict_key"):
        return meta["verdict_key"]
    return VERDICT_MAP.get(run_id)


def _load_verdicts() -> dict:
    """Load the FF-2D rubric verdicts ({} when absent).

    Prefers the committed snapshot ``frontend/data/forecast/ff-verdicts.json``
    (which IS in the Pages sparse-checkout, so ``--reindex`` bakes verdicts at
    deploy time with no ``docs/handoffs`` access) and falls back to the in-repo
    ``docs/handoffs/ff-t1-gate-verdicts.json`` source for an in-session refresh.
    """
    for path in (FORECAST_DIR / "ff-verdicts.json", VERDICTS_PATH):
        if path.exists():
            return json.loads(path.read_text())
    return {}


def _fc_summary(verdict: dict | None) -> dict | None:
    """Compact ``{FC-1: 'FAIL', ...}`` category-status map from a verdict."""
    if not verdict:
        return None
    cats = verdict.get("categories", {})
    return {k: (v or {}).get("status") for k, v in cats.items()}


def _full_invariants(sidecar: dict) -> list[dict]:
    """Return the full I1..I14 chip list for a run.

    Baseline sidecars carry all 14; gate/crossover-stub sidecars store only the
    non-PASS rows plus an ``invariants_note`` naming the PASS-omitted idents. When
    a note is present, unlisted idents are filled in as PASS (their omission is
    the note's own claim). When neither is present (e.g. a crossover stub), the
    stored list is returned as-is.
    """
    stored = sidecar.get("invariants") or []
    by_id = {r.get("ident"): r for r in stored if r.get("ident")}
    note = sidecar.get("invariants_note")
    if not note and len(stored) < 14:
        # No basis to infer the rest — return what we have, tagged.
        return [
            {
                "ident": r.get("ident"),
                "name": r.get("name") or INV_NAMES.get(r.get("ident"), ""),
                "status": r.get("status"),
                "detail": r.get("detail", ""),
            }
            for r in stored
        ]
    out = []
    for ident, name in INV_NAMES.items():
        if ident in by_id:
            r = by_id[ident]
            out.append(
                {
                    "ident": ident,
                    "name": r.get("name") or name,
                    "status": r.get("status"),
                    "detail": r.get("detail", ""),
                }
            )
        else:
            out.append(
                {
                    "ident": ident,
                    "name": name,
                    "status": "PASS",
                    "detail": "PASS (omitted from sidecar; per invariants_note)",
                }
            )
    return out


# --------------------------------------------------------------------------- #
# Per-run artifacts (registry sidecar + runs payload) — verdict baked in.
# --------------------------------------------------------------------------- #
def _run_provenance(sidecar: dict, meta: dict, verdict: dict | None) -> dict:
    """Resolve one run's scoring-provenance stamp — PRESERVE, never mint (FR-21).

    Precedence: the rubric verdict's own stamp (the authoritative "when was this
    scored", populated when the battery is re-scored) > the canonical hindcast
    sidecar's stamp (written once at registration, when "now" is honest) > an
    explicitly UNSCORED stamp.

    The unscored stamp records ``scored_at_sha``/``scored_at_date`` as ``None``
    with a note, but still carries ``cache_epoch`` — the run's own config
    identity IS recoverable from its artifacts at any time, and it is the second
    staleness signal. Minting a fresh sha/date here would make every ``--reindex``
    reset the board's apparent freshness, which is the FR-21 failure itself.
    """
    for source in (verdict, sidecar):
        existing = fp.read_stamp(source)
        if existing and existing.get("scored_at_date"):
            return existing
    return {
        "schema": fp.SCHEMA,
        "scored_at_sha": None,
        "scored_at_date": None,
        "cache_epoch": fp.cache_epoch_from(meta, sidecar),
        "note": (
            "UNSCORED under the FR-21 staleness machinery: this run predates it, "
            "or its verdict carries no stamp. Not evidence of freshness — it is "
            "the absence of evidence. A re-score through scripts/forecast_verdict.py "
            "stamps it."
        ),
    }


def build_run_artifacts(sidecar: dict, verdicts: dict) -> tuple[dict, dict]:
    """Return ``(registry_entry, run_payload)`` for one canonical sidecar.

    ``registry_entry`` is the lean committed index sidecar; ``run_payload`` is
    the full-detail object gzipped into ``runs/<id>.js``. The rubric verdict is
    resolved from ``verdicts`` (FF-2D) and baked into both, so the stdlib
    ``--build`` step needs no access to the verdict doc.
    """
    run_id = sidecar.get("run_id") or sidecar.get("id")
    meta = sidecar.get("meta", {}) or {}
    has_score = sidecar.get("score") is not None
    kind, tier, family = classify(run_id, meta, has_score)
    # A readiness battery is program-wide, not per-ISO — file it under ALL so it
    # isn't mistaken for an unknown-ISO run in the facet filter.
    iso = meta.get("iso") or ("ALL" if kind == "readiness" else "?")

    vkey = _verdict_key(run_id, meta)
    verdict = verdicts.get(vkey) if vkey else None
    fc = _fc_summary(verdict)
    determination = (verdict or {}).get("determination")

    invariants = _full_invariants(sidecar)
    year_summary = meta.get("year_summary") or []
    solved = meta.get("solved_years") or []
    start = meta.get("start_year")
    end = meta.get("end_year")
    years = solved or ([start, end] if start and end else [])

    registry_entry = {
        "id": run_id,
        "iso": iso,
        "kind": kind,
        "tier": tier,
        "family": family,
        "label": meta.get("label") or "",
        "mode": meta.get("mode") or ("backcast" if kind == "t1h" else "forecast"),
        "variant": meta.get("variant") or "",
        "start_year": start,
        "end_year": end,
        "years": years,
        "n_solved_years": meta.get("n_solved_years") or (len(solved) or None),
        "wall_s": meta.get("total_wall_s"),
        "rss_mb": meta.get("global_peak_rss_mb"),
        "capacity_market_clearing": meta.get("capacity_market_clearing"),
        "determination": determination,
        "verdict_key": vkey,
        "fc": fc,
        "has_score": has_score,
        "has_invariants": bool(invariants),
        "has_ledger": bool(year_summary),
        "n_inv": len(invariants),
        "file": f"frontend/data/forecast/runs/{run_id}.js",
        "registered_utc": sidecar.get("registered_utc") or _now(),
        # FR-21 staleness machinery: WHEN and against WHAT this run's board entry
        # was SCORED. `registered_utc` cannot answer that — --reindex refreshes
        # it without re-scoring anything. So the stamp is PRESERVED, never
        # minted here: it comes from the verdict that scored the run (FFR-3A
        # populates those), else from the run's own canonical sidecar. A run
        # predating the machinery records sha/date None with a note — stamping
        # a reindex as "scored now" would make the board perpetually look fresh,
        # which is precisely the failure FR-21 names.
        fp.PROVENANCE_KEY: _run_provenance(sidecar, meta, verdict),
    }

    # Full payload — everything the per-run detail view renders. Top-level stub
    # fields (a crossover-ff2d stub carries fc4/dispatch_skill at top level, no
    # ``score``) are passed through under ``extras`` so nothing is dropped.
    extras = {
        k: v
        for k, v in sidecar.items()
        if k
        not in (
            "run_id",
            "id",
            "meta",
            "score",
            "invariants",
            "invariants_note",
            "registered_utc",
        )
    }
    run_payload = {
        "id": run_id,
        "iso": iso,
        "kind": kind,
        "tier": tier,
        "family": family,
        "label": meta.get("label") or "",
        "determination": determination,
        "meta": meta,
        "invariants": invariants,
        "invariants_note": sidecar.get("invariants_note"),
        "verdict": verdict,
        "verdict_key": vkey,
        "score": sidecar.get("score"),
        "extras": extras or None,
        "registered_utc": registry_entry["registered_utc"],
        # Same stamp object as the registry sidecar, so the payload the run
        # explorer renders and the index the manifest is built from can never
        # disagree about when this run was scored (FR-21).
        fp.PROVENANCE_KEY: registry_entry[fp.PROVENANCE_KEY],
    }
    return registry_entry, run_payload


def _registry_dir(root: Path) -> Path:
    return root / "frontend" / "data" / "forecast" / "registry"


def _runs_dir(root: Path) -> Path:
    return root / "frontend" / "data" / "forecast" / "runs"


def write_run(sidecar: dict, verdicts: dict, root: Path = REPO) -> str:
    """Write one run's registry sidecar + runs payload under ``root``. Returns id."""
    entry, payload = build_run_artifacts(sidecar, verdicts)
    run_id = entry["id"]
    reg, runs = _registry_dir(root), _runs_dir(root)
    reg.mkdir(parents=True, exist_ok=True)
    runs.mkdir(parents=True, exist_ok=True)
    (reg / f"{run_id}.json").write_text(
        json.dumps(entry, indent=2, ensure_ascii=False) + "\n"
    )
    js = (
        "window.FF=window.FF||{};window.FF.runGz=window.FF.runGz||{};"
        f"window.FF.runGz[{json.dumps(run_id)}]=" + json.dumps(_gzb64(payload)) + ";\n"
    )
    (runs / f"{run_id}.js").write_text(js)
    return run_id


# --------------------------------------------------------------------------- #
# Assembly — manifest.js + program-status.js (stdlib-only; the deploy step).
# --------------------------------------------------------------------------- #
_TIER_ORDER = {"t1f": 0, "t1x": 1, "t1h": 2, "poc": 3, "battery": 4, "t3": 5}
_KIND_ORDER = {
    "t1f": 0,
    "t1x": 1,
    "t1h": 2,
    "adequacy": 3,
    "ces-poc": 4,
    "readiness": 5,
    "t3-golden": 6,
}


def _load_registry_entries(registry_dir: Path) -> list[dict]:
    entries = []
    if registry_dir.exists():
        for p in sorted(registry_dir.glob("*.json")):
            try:
                entries.append(json.loads(p.read_text()))
            except json.JSONDecodeError as exc:
                print(f"  skip {p.name}: invalid JSON ({exc})", file=sys.stderr)
    return entries


def _board_provenance(entries: list[dict]) -> dict:
    """Summarize the scoring provenance across every registered run (FR-21).

    Returns the manifest-level block: when the board was assembled, the NEWEST
    ``scored_at_date``/``scored_at_sha`` any run carries (the board's freshness
    frontier — what the CI staleness check measures HEAD against), the distinct
    ``cache_epoch`` values in play, and how many runs are unstamped. The
    distinct-epoch count is the second signal: more than one means the board is
    comparing runs solved under different config identities.
    """
    stamps = [s for s in (fp.read_stamp(e) for e in entries) if isinstance(s, dict)]
    dated = [s for s in stamps if s.get("scored_at_date")]
    newest = max(dated, key=lambda s: s["scored_at_date"], default=None)
    epochs = sorted({s["cache_epoch"] for s in stamps if s.get("cache_epoch")})
    return {
        "schema": fp.SCHEMA,
        "assembled_at": fp.utc_now(),
        "assembled_at_sha": fp.head_sha(),
        "newest_scored_at_date": (newest or {}).get("scored_at_date"),
        "newest_scored_at_sha": (newest or {}).get("scored_at_sha"),
        "cache_epochs": epochs,
        "n_stamped": len(stamps),
        "n_unstamped": len(entries) - len(stamps),
    }


def _manifest_meta(entries: list[dict]) -> dict:
    """Assemble the ``window.FF.meta`` facet block from the entries."""
    isos = sorted({e["iso"] for e in entries})
    kinds = sorted({e["kind"] for e in entries}, key=lambda k: _KIND_ORDER.get(k, 9))
    tiers = sorted({e["tier"] for e in entries}, key=lambda t: _TIER_ORDER.get(t, 9))
    # Schema-ready-but-unpopulated tiers/kinds (later owner-gated waves), surfaced
    # so the explorer's filter UI can show them as present-but-empty (plan §8).
    schema_ready = {
        "kinds": ["t2", "t3-golden", "pb-band"],
        "tiers": ["t2", "t3", "pb"],
    }
    return {
        "isos": isos,
        "kinds": kinds,
        "tiers": tiers,
        "schema_ready": schema_ready,
        "inv_names": INV_NAMES,
        "n_runs": len(entries),
        # FR-21: the board's OWN staleness position — the newest scored sha and
        # epoch across every registered run, plus when the manifest was
        # assembled. This is what makes "the board has been dark for ten days"
        # a readable number instead of an archaeology exercise.
        fp.PROVENANCE_KEY: _board_provenance(entries),
    }


def build_manifest(site_dir: Path) -> int:
    """Assemble ``manifest.js`` from the registry sidecars under ``site_dir``.

    Stdlib-only, byte-deterministic; the Pages deploy runs this on a bare
    ``python3``. Reads ``<site_dir>/frontend/data/forecast/registry/*.json``
    (verdicts already baked in) and writes ``manifest.js`` alongside — so the
    ``--reindex --site-dir _site`` deploy path reads back exactly the registry
    it just generated into the staging root.
    """
    entries = _load_registry_entries(_registry_dir(site_dir))
    # Order: tier, then iso, then id — stable and human-scannable.
    entries.sort(key=lambda e: (_TIER_ORDER.get(e["tier"], 9), e["iso"], e["id"]))
    meta = _manifest_meta(entries)
    out_dir = site_dir / "frontend" / "data" / "forecast"
    out_dir.mkdir(parents=True, exist_ok=True)
    js = (
        "window.FF=window.FF||{};window.FF.meta="
        + json.dumps(meta, sort_keys=True)
        + ";window.FF.manifest="
        + json.dumps(entries, sort_keys=True)
        + ";\n"
    )
    (out_dir / "manifest.js").write_text(js)
    return len(entries)


def build_program_status(site_dir: Path) -> bool:
    """Wrap the committed ``program-status.json`` seed into ``program-status.js``.

    Returns False (with a note) when the seed is absent — the status page then
    renders its own "no program-status seed" message rather than blanking.
    """
    if not PROGRAM_STATUS_JSON.exists():
        print(
            f"  note: {PROGRAM_STATUS_JSON} absent — program-status.js not written",
            file=sys.stderr,
        )
        return False
    seed = json.loads(PROGRAM_STATUS_JSON.read_text())
    out_dir = site_dir / "frontend" / "data" / "forecast"
    out_dir.mkdir(parents=True, exist_ok=True)
    js = (
        "window.FF=window.FF||{};window.FF.programStatus="
        + json.dumps(seed, sort_keys=True)
        + ";\n"
    )
    (out_dir / "program-status.js").write_text(js)
    return True


# --------------------------------------------------------------------------- #
# Reindex — backfill the namespace from every committed hindcast sidecar.
# --------------------------------------------------------------------------- #
def reindex(site_dir: Path = REPO) -> int:
    """Rebuild the whole forecast namespace from the committed hindcast sidecars.

    Reads ``frontend/data/hindcast/*.json`` + the rubric verdicts and writes
    ``registry/<id>.json`` + ``runs/<id>.js`` + ``manifest.js`` +
    ``program-status.js`` under ``site_dir``. Stdlib-only, so it is ALSO the
    Pages-deploy assembly step (``--reindex --site-dir _site``): the registry /
    runs are generated data (gitignored — deploy is their single writer), fully
    derivable from the committed sidecars + the ``ff-verdicts.json`` snapshot.
    Run with no ``site_dir`` to regenerate the repo checkout for local preview.
    """
    verdicts = _load_verdicts()
    if not verdicts:
        print(
            f"  WARNING: no verdict source ({FORECAST_DIR / 'ff-verdicts.json'} or "
            f"{VERDICTS_PATH}) — runs registered without rubric verdicts.",
            file=sys.stderr,
        )
    n = 0
    for p in sorted(HINDCAST_DIR.glob("*.json")):
        try:
            sidecar = json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            print(f"  skip {p.name}: invalid JSON ({exc})", file=sys.stderr)
            continue
        if not (sidecar.get("run_id") or sidecar.get("id")):
            print(f"  skip {p.name}: no run_id", file=sys.stderr)
            continue
        write_run(sidecar, verdicts, root=site_dir)
        n += 1
    build_manifest(site_dir)
    build_program_status(site_dir)
    print(
        f"[reindex] wrote {n} runs to {_registry_dir(site_dir)} + "
        f"{_runs_dir(site_dir)}; assembled manifest.js + program-status.js"
    )
    return n


def _stamp_sidecar(sidecar: dict) -> dict:
    """Stamp a FRESHLY-BUILT canonical sidecar with its scoring provenance.

    This is the one place "now" is an honest answer: the sidecar was just built
    from a bundle that just finished, at this HEAD. Mutates and returns
    ``sidecar`` so the caller writes the stamped object. An already-stamped
    sidecar is left alone (re-registering an existing run must not reset its
    scoring date). ``--reindex`` never reaches here — it PRESERVES stamps via
    :func:`_run_provenance`.
    """
    if not fp.read_stamp(sidecar):
        sidecar[fp.PROVENANCE_KEY] = fp.stamp(sidecar.get("meta"), sidecar)
    return sidecar


def register_one(sidecar: dict) -> str:
    """Register a newly-written canonical sidecar by regenerating the namespace.

    The caller writes the canonical ``frontend/data/hindcast/<id>.json`` first
    (the ``--bundle`` / ``--summary`` paths do so via the legacy builders); this
    then runs a full ``reindex`` so the new run — and every existing one — is
    (re)generated into the repo checkout's forecast namespace (correct even on a
    fresh checkout where the generated files were absent). Returns the run id.
    """
    run_id = sidecar.get("run_id") or sidecar.get("id")
    reindex()
    print(f"[register] {run_id}: registered; forecast namespace regenerated")
    return run_id


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--bundle",
        type=Path,
        help="run_capacity_hindcast / crossover out-dir to register "
        "(delegates to register_hindcast.build_sidecar).",
    )
    src.add_argument(
        "--summary",
        type=Path,
        help="full_horizon_summary.json (T1-F / CES-POC / adequacy) — delegates "
        "to register_forecast_baseline.build_sidecar.",
    )
    src.add_argument(
        "--reindex",
        action="store_true",
        help="Rebuild the forecast namespace from every committed hindcast "
        "sidecar (bakes FF-2D verdicts; in-session).",
    )
    src.add_argument(
        "--build",
        action="store_true",
        help="Assemble ONLY manifest.js + program-status.js from an existing "
        "registry/*.json + program-status.json under --site-dir (stdlib-only; a "
        "lighter refresh — the deploy uses --reindex to regenerate everything).",
    )
    parser.add_argument(
        "--label",
        default="ff-t1f-baseline",
        help="Campaign tag for a --summary registration.",
    )
    parser.add_argument(
        "--kind",
        default="t1f",
        help="Run family for a --summary registration (t1f/ces-poc/adequacy).",
    )
    parser.add_argument(
        "--extra-meta",
        default=None,
        help="JSON object merged into a --summary run's meta.",
    )
    parser.add_argument(
        "--preserve-invariants",
        action="store_true",
        help="For --bundle: reuse the committed sidecar's "
        "invariants (scoring-only re-scores; see register_hindcast).",
    )
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=REPO,
        help="Root to write the assembled data into (repo root "
        "for preview, the Pages staging dir for deploys).",
    )
    args = parser.parse_args(argv)

    if args.build:
        n = build_manifest(args.site_dir)
        build_program_status(args.site_dir)
        print(
            f"[build] assembled manifest.js ({n} runs) + program-status.js "
            f"under {args.site_dir}/frontend/data/forecast"
        )
        return 0

    if args.reindex:
        reindex(args.site_dir)
        return 0

    if args.bundle is not None:
        # Reuse the canonical hindcast sidecar builder (invariants/scoring live
        # there), write the canonical record, then register into the namespace.
        from scripts import register_hindcast as RH  # noqa: PLC0415

        RH.SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
        sidecar = RH.build_sidecar(
            args.bundle, preserve_invariants=args.preserve_invariants
        )
        _stamp_sidecar(sidecar)
        (RH.SIDECAR_DIR / f"{sidecar['run_id']}.json").write_text(
            json.dumps(sidecar, indent=2) + "\n"
        )
        print(f"[register] wrote canonical sidecar for {sidecar['run_id']}")
        register_one(sidecar)
        return 0

    if args.summary is not None:
        sys.path.insert(0, str(REPO))
        from scripts import register_forecast_baseline as RB  # noqa: PLC0415

        extra = json.loads(args.extra_meta) if args.extra_meta else None
        sidecar = RB.build_sidecar(
            args.summary, args.label, kind=args.kind, extra_meta=extra
        )
        _stamp_sidecar(sidecar)
        HINDCAST_DIR.mkdir(parents=True, exist_ok=True)
        (HINDCAST_DIR / f"{sidecar['run_id']}.json").write_text(
            json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n"
        )
        print(f"[register] wrote canonical sidecar for {sidecar['run_id']}")
        register_one(sidecar)
        return 0

    parser.error("one of --bundle / --summary / --reindex / --build is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
