"""Capture current-HEAD golden baselines for the calibration keeper configs.

Stage 0 of the orchestrator-unification plan
(``docs/handoffs/orchestrator-unification-plan-2026-07.md`` §6-§7) needs a
deterministic, faithful re-solve of every registered keeper bundle *at the
current commit*, so a later refactor stage can capture an "after" set and diff
it against this "before" set for dispatch neutrality.

What this script does, per keeper:

1. Resolve the keeper id (``frontend/data/backcast/keepers.json``) to its frozen
   bundle (the registry sidecar's ``bundle`` field), then read that bundle's
   ``meta.json`` — the authoritative record of every argument the keeper was
   solved with (~134 keys, one per ``solve_and_persist`` parameter, four under
   a recorded-name alias).
2. Reconstruct the exact ``solve_and_persist`` keyword arguments from that
   ``meta.json`` (signature introspection + a four-entry alias map; every
   parameter absent from the record is left at its function default, which is
   verified benign — see the fidelity oracle below).
3. Re-solve at HEAD with determinism pinned
   (``MARKET_SIM_HIGHS_THREADS=1``, ``MARKET_SIM_WARMSTART=1``,
   ``MARKET_SIM_WARMSTART_XYEAR=0`` — cold-vs-cold at one thread is
   bit-identical; multi-threaded dual simplex is NOT — see
   ``docs/cross-year-warmstart.md``), writing the full P1 bundle
   (``dispatch/<year>_P1.parquet``, ``system.parquet``, ``flows.parquet``, …)
   into ``results/regression-goldens/<stage-tag>/<iso>/``.
4. **Fidelity oracle:** re-read the golden bundle's freshly-written
   ``meta.json`` / ``run_config.json`` and assert every key it shares with the
   keeper's record is identical. A single mismatch means a flag was dropped or
   mis-mapped; the capture fails loudly rather than emitting a worthless golden.
   Keys present only in the golden (new fields added to ``ScenarioConfig`` /
   ``meta`` since the keeper was frozen) are reported, not failed — goldens are
   current-HEAD baselines, not byte-reproductions of the July-3 bundles.
5. Write a hashes-only ``manifest.json`` (per-file *content* hashes, per-keeper
   fidelity summary, and a **per-entry** provenance + keeper snapshot). The
   multi-GB parquet bundles live under the gitignored goldens dir; only the
   manifest is committed.

Manifest schema v2 — per-entry provenance (2026-09-01). Schema v1 carried ONE
top-level ``git_sha`` / ``git_dirty`` / ``env`` / ``highspy_version`` block for
however many captures the manifest held. Because ``write_manifest`` merges a
single ISO's entry into the existing file, every capture silently RE-STAMPED
that one block for all the earlier captures — so a manifest with six captures
taken at six trees ended up asserting one tree for all six, and the five older
rows carried a sha that was *valid and wrong* (the perfb-stage0 defect;
``docs/FINDING-stage0-provenance-repair-2026-09.md``). In v2 those four fields
live inside ``keepers.<ISO>.provenance``, stamped by the capture that wrote the
entry and never touched again; the top level keeps only what is genuinely
global to the file (``schema_version``, ``stage_tag``, ``hash_scheme``,
``note``).

Config-partition entries (2026-09-02) — ADDITIVE to schema v2, no version bump.
An ISO whose keeper shard carries a ``config_partition`` block designates more
than one config, each covering a disjoint slice of the training window: ERCOT is
the first (owner ruling 2026-08-26,
``docs/FINDING-ercot-two-config-keeper-2026-08-26.md``) — a **forward** config
for {2024, 2025} and a 2023 **carve-out** for the ECRS-era regime. The manifest
keyed one entry per bare ISO, so only the designated ``keeper`` was reachable and
full coverage of such an ISO was structurally impossible.

The representation is a SIBLING entry in the same ``keepers`` map, keyed
``<ISO>__<role>`` (``ERCOT__carveout-2023``), where ``role`` is verbatim the
shard's ``config_partition.configs[].role``. Everything else about the entry is
an ordinary v2 entry, so every v2 invariant — per-entry provenance, the
``keeper_snapshot`` retention absorb, the content hashes — applies to it with no
new enforcement code, and the bare-ISO entries are untouched byte-for-byte. The
key is DERIVED from the shard rather than invented, so
``check_golden_manifest.live_keeper`` resolves it mechanically through
``config_partition.configs[].run_id``; a role that is renamed or retired
therefore reads STALE rather than silently CURRENT.

*Rejected alternative:* nesting a ``configs`` list inside the existing ``ERCOT``
entry. That changes the shape of an entry that already exists (so the forward
entry's bytes move), and every per-entry invariant would need a second,
parallel implementation for the nested rows. Sibling entries need neither.

A partition entry additionally carries a ``partition`` block naming its ISO,
role, the shard's DESIGNATED year span for that config, and the ruling that
declared the partition.

**Schema v3 (Y-25, 2026-09-06) — the config's IDENTITY on the entry.** The
ercot-248 consolidation composed both ERCOT roles onto ONE registered run, so
``keeper_id`` stopped identifying a configuration: forward and carve-out
entries carry the same run id, and which config a ``role`` names is answerable
only from the live shard — a file that moves. v3 stamps the answer into the
entry: ``partition.config_id`` (the run whose CONFIGURATION was replayed —
``config_partition.configs[].source_run_id``, else ``run_id``) with
``config_bundle``, ``shard_run_id`` (what was actually replayed) and
``composed`` / ``composed_roles``. ``designated_years`` → ``config_id`` is the
year-set-to-config map the partition needed and v2 could not express. Purely
ADDITIVE: ``check_golden_manifest.MIN_SCHEMA_VERSION`` stays 2, every committed
v2 entry parses and is enforced unchanged, and :func:`manifest_version` keeps a
file at v2 until every partition entry in it carries the identity keys, so
merging a v3 capture never re-labels an older entry.

**R-AW (owner ruling, audit-program director sitting 2026-09-05, card "ERCOT
key"), verbatim: "The golden config should be the 2024:2025 one not 2023".**
Read as: the ERCOT stage-0 golden captures the FORWARD config on its designated
span {2024, 2025}, and the ``ERCOT__carveout-2023`` capture key is RETIRED.
Since the ercot-248 consolidation (owner instruction 2026-09-05; both partition
roles' ``run_id`` now point at the one composed run
``2026-09-05-ercot248-two-config-keeper``, whose ``meta.json`` carries the
forward config verbatim), the rules this script applies are:

* **The bare key of a partitioned ISO resolves to its ``forward`` role**
  (``check_golden_manifest.FORWARD_ROLE``): the shard's designated ``keeper``
  (which the forward role's ``run_id`` must equal — a mismatch fails loud) is
  replayed on the forward role's DESIGNATED span, not the run's whole
  registered span. The composed run's registered span is 3-year because it
  carries 2023 under the carve-out config; replaying all three years of its
  forward ``meta.json`` would be a golden of a config the keeper never
  designates for 2023.
* **Every capture replays its config on its designated span**, and the entry
  records the run's REGISTERED span alongside as ``registered_years``. Rule 22
  holds as a hard assertion: the designated span is never a superset of the
  registered one (the slice can only narrow — {2024, 2025} ⊂ {2023, 2024,
  2025}). It never introduces a 2022 or 2026 solve.
* **A retired capture key is refused** (``check_golden_manifest.RETIRED_CAPTURE_KEYS``).
  The manifest entries already written under it are historical capture records
  — a ``keeper_id`` records which run's outputs were actually captured — and are
  never rewritten; the gate reports them without comparing them to the shard.

Record: ``docs/handoffs/FINDING-y14-ercot-golden-forward-2026-09-05.md``.

Each entry also carries a ``keeper_snapshot`` copied from the provenance run's
registry sidecar at capture time. Top-15-per-ISO registry retention will prune
that sidecar long before the golden is retired — five of the six perfb-stage0
rows were already orphaned this way, with every gate green — so the entry must
absorb the sidecar's identity *while it still exists* rather than pointing at
a file that will vanish. ``scripts/check_golden_manifest.py`` enforces both
halves in CI.

Determinism note: the manifest hashes the parquet *content* (canonical column
bytes), not the raw file, because parquet embeds library/version metadata that
varies run-to-run even when the data is identical. The authoritative
byte-identity check between two golden sets is
``scripts/regression_gate.py`` (which runs ``regression_check`` at
``--atol 0 --rtol 0``); the content hashes are a fast pre-screen.

Usage:
    # one keeper, in-process (all its years sequentially):
    python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag stage1-before

    # the ERCOT stage-0 golden: the forward config on {2024, 2025} (R-AW) —
    # the bare key resolves to the forward role and slices to its span:
    python scripts/capture_keeper_goldens.py --iso ERCOT --stage-tag perfb-stage0

    # a config-partition member by its <ISO>__<role> key (ERCOT__forward is the
    # same capture as the bare key; ERCOT__carveout-2023 is RETIRED and refused):
    python scripts/capture_keeper_goldens.py --iso ERCOT__forward \
        --stage-tag perfb-stage0

    # what an ISO's shard designates (no solve):
    python scripts/capture_keeper_goldens.py --list-configs

    # all six, ≤2 concurrent per-ISO subprocesses (CLAUDE.md rule 8 memory cap);
    # add --include-partitions to cover every designated config, not just the
    # bare ``keeper`` of each shard:
    python scripts/capture_keeper_goldens.py --all --stage-tag stage1-before

Holdout quarantine (CLAUDE.md rule 22): this only ever solves years already
recorded in the replayed run's ``meta.json`` (all within 2023-2025) — a
partitioned config's DESIGNATED span, asserted to be a subset of that run's
REGISTERED span, never a widened one. It never introduces a 2022 or 2026 solve.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Mirror run_calibration_full.py's bootstrap: src/ for the package, REPO for the
# `scripts.` namespace-package imports that run_calibration_full performs.
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

# --- Determinism pin. Set BEFORE any solve so dispatch.py's os.environ reads
#     (dispatch.py:MARKET_SIM_HIGHS_THREADS, runner/run_calibration WARMSTART)
#     see the pinned values. Cold-vs-cold at THREADS=1 is bit-identical;
#     multi-threaded dual simplex breaks marginal ties nondeterministically. ---
DETERMINISM_ENV = {
    "MARKET_SIM_HIGHS_THREADS": "1",
    "MARKET_SIM_WARMSTART": "1",
    "MARKET_SIM_WARMSTART_XYEAR": "0",
    # Same-year P1 basis seed, pinned EXPLICITLY since PERF-C S1 (2026-09-20).
    # It used to be armed inside the cross-year gate, so the line above
    # implied it OFF; ``pipeline.solve`` now gates it on its own env var, and
    # an implication that is no longer true is not a pin. A seeded P1 is
    # warm-start class (marginal-tie reshuffle), which is exactly what a
    # byte-identity golden may not carry.
    "MARKET_SIM_P1_BASIS_SEED": "0",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("capture_keeper_goldens")


from scripts.check_golden_manifest import (  # noqa: E402  (after sys.path insert)
    FORWARD_ROLE,
    REQUIRED_PARTITION_V3_KEYS,
    RETIRED_CAPTURE_KEYS,
)
from scripts.lib import keeper_store  # noqa: E402  (after sys.path insert)

REGISTRY_DIR = REPO / "frontend" / "data" / "backcast" / "registry"
GOLDENS_ROOT = REPO / "results" / "regression-goldens"

# Separator between the ISO and the config-partition role in a capture key
# (``ERCOT__forward``). Doubled underscore: it appears in no ISO name and in no
# ``config_partition.configs[].role`` value, so the split is unambiguous, and it
# is filesystem-safe because the key is also the golden subdirectory. The gate
# (stdlib-only, never imports this solve-side tool) carries its own copy; the
# retired-key table and the forward-role name are imported FROM the gate so the
# two scripts cannot disagree about either.
PARTITION_KEY_SEP = "__"

# ``meta.json`` records four ``solve_and_persist`` parameters under a different
# (historical / recorded) key name. Every other meta key that is also a
# parameter maps by identity. Verified against the meta-dict construction in
# ``scripts/run_calibration_full.py`` (~line 2240).
META_KEY_TO_PARAM = {
    "commitment_screen_coal": "screen_coal",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}

# Override-channel parameters whose dict values are replayed verbatim into
# ``ScenarioConfig.with_overrides``: a key deleted from ScenarioConfig since the
# keeper froze (rule 26 — deleted flags must not parse) raises TypeError there.
# Mapped to the meta key each channel is recorded under, so the fidelity oracle
# can compare the recorded dict modulo exactly the dropped keys.
OVERRIDE_CHANNEL_META_KEYS = {
    "prb_overrides": "coal_prb_sigmoid_overrides",
    "bit_overrides": "coal_bit_sigmoid_overrides",
}

# Meta keys that are NOT ``solve_and_persist`` parameters: run identity,
# positional args handled explicitly, gas prices (derived inside
# ``solve_and_persist`` from the reference), and two config-*derived* mirror
# values (not inputs). These are skipped when building kwargs.
META_NON_PARAM_KEYS = {
    "timestamp",
    "iso",
    "years",
    "hours",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",  # derived from _calibration_config, not a kwarg
    "td_loss_factor",  # derived from _calibration_config, not a kwarg
    "shared_inputs",
    "git_sha",
    "highspy_version",
}

# Volatile / derived keys excluded from the AUTHORITATIVE meta comparison. meta
# otherwise echoes the passed kwargs verbatim, so a golden-vs-keeper match on
# every remaining shared key proves each recorded flag was applied identically —
# and, unlike the resolved scenario_config, it does NOT drift with base-config
# code changes. ``coal_plant_monthly_pricing`` / ``td_loss_factor`` are the two
# meta values re-derived from ``_calibration_config`` (not kwarg echoes), so they
# can legitimately drift and are excluded here.
FIDELITY_IGNORE_KEYS = {
    "timestamp",
    # ``years`` is the REPLAY span, not a solve flag: since R-AW / Y-14 the
    # bare ``ERCOT`` key replays the forward config on its DESIGNATED span
    # (2024-2025) while the composed keeper's meta.json records the registered
    # span (2023-2025), so the two legitimately differ and the oracle refused
    # every post-Y-14 ERCOT capture on this one key (wallclock B, 2026-09-06).
    # Rule 22's "never widened" invariant is asserted at the solve site
    # (``capture_one``: replay span ⊆ recorded span) and recorded per entry as
    # ``years`` / ``registered_years``; it is not this oracle's question.
    "years",
    "git_sha",
    "highspy_version",
    "shared_inputs",
    "gas_prices",  # derived from the reference; compared informationally
    "coal_plant_monthly_pricing",  # re-derived from _calibration_config
    "td_loss_factor",  # re-derived from _calibration_config
    # A6 environment stamp (python/platform/package versions): definitionally
    # the capture host's, not a solve flag — same class as git_sha /
    # highspy_version above. replay_keeper.py owns the mismatch WARNING; the
    # oracle must not fail a golden because the keeper was frozen on an older
    # dependency set.
    "environment",
    # Origin-durable git basis of the solving checkout (`_basis_sha()`,
    # recorded since the ercot-204 era): a provenance stamp like git_sha, not
    # a solve flag — a current-HEAD golden legitimately records HEAD's basis.
    "basis_sha",
}


def _git_sha() -> str:
    """Return the short git SHA of HEAD, or ``"unknown"``."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True
        )
        return out.strip()
    except Exception:
        return "unknown"


def _git_sha_full() -> str:
    """Return the full git SHA of HEAD, or ``"unknown"``."""
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True)
        return out.strip()
    except Exception:
        return "unknown"


def _basis_sha() -> str:
    """Return the origin-durable basis of this checkout, or ``"unknown"``.

    Mirrors ``market_sim.pipeline.persist.basis_sha``: ``merge-base(HEAD,
    origin/main)``, the newest ancestor of this capture that main's history
    retains, falling back to full ``HEAD`` when ``origin/main`` is not visible.
    A capture's own ``git_sha`` is routinely a session-local branch commit that
    is squashed away on merge, so ``basis_sha`` is the anchor that still
    resolves a month later.
    """
    for args in (["merge-base", "HEAD", "origin/main"], ["rev-parse", "HEAD"]):
        try:
            out = subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()
            if out:
                return out
        except Exception:
            continue
    return "unknown"


def _git_dirty() -> bool:
    """Return True if the working tree has uncommitted changes."""
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=REPO, text=True
        )
        return bool(out.strip())
    except Exception:
        return False


def _provenance() -> dict:
    """Return this capture's own provenance block (manifest schema v2).

    Stamped into the ISO entry the capture writes, so a later capture of a
    different ISO can never re-label it. ``recorded_at`` is the manifest-write
    instant, which for a single-ISO capture is the moment the solve finished.
    """
    import highspy

    return {
        "git_sha": _git_sha(),
        "git_sha_full": _git_sha_full(),
        "basis_sha": _basis_sha(),
        "git_dirty": _git_dirty(),
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "env": dict(DETERMINISM_ENV),
        "highspy_version": getattr(highspy, "__version__", "unknown"),
        "source": "stamped-at-capture",
    }


def _keeper_snapshot(info: dict) -> dict:
    """Return the entry's self-contained copy of its provenance run's sidecar.

    Registry retention (top-15 per ISO) prunes the sidecar on its own schedule
    and knows nothing about this manifest, so an entry that only *references*
    ``registry/<keeper_id>.json`` becomes unreadable the moment the prune runs.
    Copying the sidecar's identity here at capture time keeps the entry
    meaningful afterwards; the prune then costs nothing.
    """
    reg = info.get("sidecar") or {}
    snap = {
        "id": info["keeper_id"],
        "iso": reg.get("iso", ""),
        "label": reg.get("label", ""),
        "date": reg.get("date", ""),
        "shorthand": reg.get("shorthand", ""),
        "definition": reg.get("definition", ""),
        # The span this capture replayed (== the entry's ``years``; the gate
        # asserts the two agree). The sidecar's own registered span is kept
        # beside it so a slice (R-AW) stays visible after the sidecar is pruned.
        "years": [int(y) for y in info["years"]],
        "registered_years": [
            int(y) for y in info.get("registered_years", info["years"])
        ],
        "bundle": str(info["bundle"].relative_to(REPO)),
        "sidecar_at_capture": (
            "present"
            if (REGISTRY_DIR / f"{info['keeper_id']}.json").is_file()
            else "absent"
        ),
    }
    return snap


def parse_capture_key(key: str) -> tuple[str, str | None]:
    """Split a capture key into ``(ISO, role)``.

    ``"ERCOT"`` → ``("ERCOT", None)`` (the shard's designated ``keeper``);
    ``"ERCOT__carveout-2023"`` → ``("ERCOT", "carveout-2023")`` (that config
    partition member). The ISO half is upper-cased; the role is preserved
    verbatim, because it is matched against the shard's own ``role`` string.
    """
    iso, _, role = key.partition(PARTITION_KEY_SEP)
    return iso.upper(), (role or None)


def capture_key(iso: str, role: str | None = None) -> str:
    """Inverse of :func:`parse_capture_key` — the manifest key / golden dir name."""
    return iso.upper() if not role else f"{iso.upper()}{PARTITION_KEY_SEP}{role}"


def _bundle_info(keeper_id: str, *, what: str) -> dict:
    """Resolve one run id to its frozen bundle via its registry sidecar.

    Args:
        keeper_id: The provenance run id.
        what: Human label for error messages (``"ERCOT"`` / the capture key).

    Returns:
        ``{"keeper_id", "bundle", "years", "sidecar"}`` — ``years`` is the run's
        REGISTERED span from the sidecar (rule 22: never widened here).
    """
    sidecar = REGISTRY_DIR / f"{keeper_id}.json"
    if not sidecar.is_file():
        raise FileNotFoundError(f"{what}: registry sidecar missing: {sidecar}")
    reg = json.loads(sidecar.read_text())
    bundle = REPO / reg["bundle"]
    if not (bundle / "meta.json").is_file():
        raise FileNotFoundError(f"{keeper_id}: bundle meta.json missing at {bundle}")
    return {
        "keeper_id": keeper_id,
        "bundle": bundle,
        "years": [int(y) for y in reg["years"]],
        # Kept whole so ``_keeper_snapshot`` can copy the sidecar's identity
        # into the manifest entry before retention prunes the sidecar.
        "sidecar": reg,
    }


def partition_configs(iso: str) -> list[dict]:
    """Return the ISO's ``config_partition.configs`` list (empty when absent).

    The keeper shard is the single source of truth for what an ISO designates;
    a shard with no ``config_partition`` block is an ordinary one-config ISO.
    """
    shard = keeper_store.load_shard(iso, REPO) or {}
    cfgs = (shard.get("config_partition") or {}).get("configs") or []
    return [c for c in cfgs if isinstance(c, dict) and c.get("run_id")]


def partition_run_id(iso: str, role: str) -> str | None:
    """Resolve ``(ISO, role)`` to the run id the shard designates, or None."""
    for cfg in partition_configs(iso):
        if str(cfg.get("role", "")).lower() == role.lower():
            return str(cfg["run_id"])
    return None


def _partition_config(iso: str, role: str) -> dict | None:
    """Return the shard's ``config_partition.configs[]`` entry for ``role``."""
    for cfg in partition_configs(iso):
        if str(cfg.get("role", "")).lower() == role.lower():
            return cfg
    return None


def slice_to_designated_span(info: dict, cfg: dict, *, what: str) -> dict:
    """Narrow ``info["years"]`` to the partition config's DESIGNATED span.

    ``info["years"]`` arrives as the run's REGISTERED span (from its sidecar);
    it is kept as ``registered_years`` and replaced by ``cfg["years"]``. Rule
    22 as a hard assertion: the designated span must be a subset of the
    registered one — a partition can only carve a registered run narrower,
    never solve a year the run never registered (which is how a 2022 or 2026
    solve would otherwise sneak in through a shard edit).

    Args:
        info: Resolved bundle info (mutated and returned).
        cfg: The shard's partition config for this capture.
        what: Label for error messages (the capture key).

    Raises:
        ValueError: if the designated span is not a subset of the registered
            span, or is empty.
    """
    registered = sorted(int(y) for y in info["years"])
    designated = sorted(int(y) for y in cfg.get("years") or [])
    if not designated:
        raise ValueError(f"{what}: partition config designates no years")
    if not set(designated) <= set(registered):
        raise ValueError(
            f"{what}: designated span {designated} is not a subset of the run's "
            f"registered span {registered} — a designated span is never a "
            f"superset of the registered span (rule 22)"
        )
    info["registered_years"] = registered
    info["years"] = designated
    return info


def resolve_capture_targets(keys: list[str]) -> dict[str, dict]:
    """Resolve capture keys (bare ISO or ``<ISO>__<role>``) to bundle info.

    A bare ISO resolves through the shard's designated ``keeper``; a partition
    key resolves through ``config_partition.configs[].run_id``. Both land on the
    same ``{"keeper_id", "bundle", "years", "sidecar"}`` shape, plus ``iso`` /
    ``role`` / ``partition_config`` so the caller can solve the right ISO and
    stamp the entry's ``partition`` block.

    R-AW: for an ISO whose shard carries a ``config_partition`` block, the bare
    key IS the ``forward`` role — the designated ``keeper`` (which must equal
    the forward role's ``run_id``) replayed on the forward role's DESIGNATED
    span, with the run's registered span kept as ``registered_years``. Every
    ``<ISO>__<role>`` key is likewise sliced to its role's designated span, so
    ``ERCOT__forward`` and ``ERCOT`` resolve identically. A key in
    ``check_golden_manifest.RETIRED_CAPTURE_KEYS`` is refused.

    Args:
        keys: Capture keys, e.g. ``["NEISO", "ERCOT", "ERCOT__forward"]``.

    Returns:
        ``{capture_key: info}``, one entry per requested key.

    Raises:
        KeyError: if a partition key names a role the ISO's shard does not
            designate (fail loud — a typo'd role must never write a golden that
            the CI gate would then report STALE forever); if the key is retired;
            or if a partitioned shard has no forward role / a forward role whose
            run_id is not the designated keeper (a shard inconsistency).
        ValueError: if a designated span is not a subset of the registered span.
    """
    out: dict[str, dict] = {}
    for raw in keys:
        iso, role = parse_capture_key(raw)
        key = capture_key(iso, role)
        if key in RETIRED_CAPTURE_KEYS:
            raise KeyError(f"{key}: RETIRED capture key — {RETIRED_CAPTURE_KEYS[key]}")
        if role is None:
            bundles = resolve_keeper_bundles(only_isos={iso})
            if iso not in bundles:
                raise KeyError(f"{iso}: no designated keeper in keepers/{iso}.json")
            info = dict(bundles[iso])
            info.update({"iso": iso, "role": None, "partition_config": None})
            if partition_configs(iso):
                fwd = _partition_config(iso, FORWARD_ROLE)
                if fwd is None:
                    have = [c.get("role") for c in partition_configs(iso)]
                    raise KeyError(
                        f"{key}: keepers/{iso}.json declares a config_partition "
                        f"with no {FORWARD_ROLE!r} role (roles present: {have}); "
                        f"the bare key resolves to the forward role (R-AW)"
                    )
                if str(fwd["run_id"]) != info["keeper_id"]:
                    raise KeyError(
                        f"{key}: keepers/{iso}.json designates keeper "
                        f"{info['keeper_id']} but its {FORWARD_ROLE!r} role names "
                        f"{fwd['run_id']} — the two must agree (R-AW)"
                    )
                info.update({"role": FORWARD_ROLE, "partition_config": fwd})
                slice_to_designated_span(info, fwd, what=key)
        else:
            run_id = partition_run_id(iso, role)
            if run_id is None:
                have = [c.get("role") for c in partition_configs(iso)]
                raise KeyError(
                    f"{key}: keepers/{iso}.json declares no config_partition "
                    f"role {role!r} (roles present: {have or 'none'})"
                )
            cfg = _partition_config(iso, role)
            info = _bundle_info(run_id, what=key)
            info.update({"iso": iso, "role": role, "partition_config": cfg})
            slice_to_designated_span(info, cfg, what=key)
        out[key] = info
    return out


def resolve_keeper_bundles(only_isos: set[str] | None = None) -> dict[str, dict]:
    """Map each ISO to its keeper id and frozen bundle path.

    Reads the sharded keeper store (``keepers/<ISO>.json``, via
    ``scripts.lib.keeper_store``) for the current keeper ids and each keeper's
    registry sidecar for the bundle directory (the sidecar's ``bundle`` field —
    NOT the id-named directory, which is empty).

    Args:
        only_isos: When given, resolve (and validate) only these ISOs, so a
            scoped ``--iso`` capture does not fail on an unrelated ISO whose
            keeper bundle is missing from the tree.

    Returns:
        ``{iso: {"keeper_id": str, "bundle": Path, "years": list[int]}}``.
    """
    ids = keeper_store.keeper_list(REPO)
    out: dict[str, dict] = {}
    for keeper_id in ids:
        sidecar = REGISTRY_DIR / f"{keeper_id}.json"
        if not sidecar.is_file():
            raise FileNotFoundError(f"registry sidecar missing: {sidecar}")
        reg = json.loads(sidecar.read_text())
        iso = reg["iso"].upper()
        if only_isos is not None and iso not in only_isos:
            continue
        bundle = REPO / reg["bundle"]
        if not (bundle / "meta.json").is_file():
            raise FileNotFoundError(
                f"{keeper_id}: bundle meta.json missing at {bundle}"
            )
        out[iso] = {
            "keeper_id": keeper_id,
            "bundle": bundle,
            "years": [int(y) for y in reg["years"]],
            # Kept whole so ``_keeper_snapshot`` can copy the sidecar's identity
            # into the manifest entry before retention prunes the sidecar.
            "sidecar": reg,
        }
    return out


def build_solve_kwargs(meta: dict, solve_fn) -> tuple[dict, list[str]]:
    """Reconstruct ``solve_and_persist`` kwargs from a keeper's ``meta.json``.

    For every ``solve_and_persist`` parameter, use the value recorded in
    ``meta`` (mapping the four alias keys), else leave it at the function
    default. Returns the kwargs and the list of parameters left at default that
    are *invisible* to the record (params with no meta key at all) — the
    explicit, documented residual blind-spot for the fidelity report.

    Args:
        meta: The keeper bundle's parsed ``meta.json``.
        solve_fn: The ``solve_and_persist`` callable (for signature
            introspection).

    Returns:
        ``(kwargs, defaulted_unrecorded_params)``.
    """
    sig = inspect.signature(solve_fn)
    params = set(sig.parameters)
    # Positional / explicitly-handled args are not filled from the generic scan.
    handled = {
        "years",
        "iso",
        "hours",
        "reference",
        "commitment",
        "screen_coal",
        "run_dir",
        "note",
        "persist_p2_state",
    }

    kwargs: dict = {}
    for meta_key, value in meta.items():
        if meta_key in META_NON_PARAM_KEYS:
            continue
        param = META_KEY_TO_PARAM.get(meta_key, meta_key)
        if param in params and param not in handled:
            kwargs[param] = value

    # Params with no representation anywhere in meta → left at default. Record
    # which ones so the fidelity report names the exact blind spot instead of
    # silently dropping. (Verified across all six keepers: every such param is
    # ISO-irrelevant or default-only — see the plan §7.3 note.)
    recorded_params = {
        META_KEY_TO_PARAM.get(k, k) for k in meta if k not in META_NON_PARAM_KEYS
    }
    defaulted = sorted(
        p for p in params if p not in handled and p not in recorded_params
    )
    return kwargs, defaulted


def drop_dead_config_keys(kwargs: dict) -> dict[str, list[str]]:
    """Drop rule-26-deleted ScenarioConfig fields from override-channel dicts.

    A keeper's ``prb_overrides``/``bit_overrides`` dict rides the generic
    ScenarioConfig override channel (``run_year`` replays it verbatim into
    ``config.with_overrides``), so a key whose field was deleted from
    ``ScenarioConfig`` after the keeper froze fails the replay with TypeError —
    by design (rule 26: a deleted flag must not parse). Goldens are current-HEAD
    baselines, and the deletions this covers collapsed the gated behavior to
    unconditional (e.g. ``nyiso_solar_registry_cod_dates``, 67a25ae), so the
    HEAD replay without the key is the faithful one. Drop such keys from the
    kwargs in place — loudly — and return ``{meta_key: [dropped keys]}`` for
    the manifest entry and the fidelity comparison.
    """
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    dropped: dict[str, list[str]] = {}
    for param, meta_key in OVERRIDE_CHANNEL_META_KEYS.items():
        d = kwargs.get(param)
        if not isinstance(d, dict):
            continue
        dead = sorted(k for k in d if k not in fields)
        if dead:
            kwargs[param] = {k: v for k, v in d.items() if k in fields}
            dropped[meta_key] = dead
            logger.warning(
                "dropping rule-26-deleted ScenarioConfig key(s) %s from the "
                "recorded %s channel (deleted at HEAD; replay without them is "
                "the current-HEAD behavior)",
                dead,
                param,
            )
    return dropped


def _content_hash(path: Path) -> str:
    """Hash a parquet file's *content* (stable across library metadata).

    Reads the frame, sorts columns, and hashes each column's float64 bytes in
    order plus the shape — reproducible whenever the underlying data is
    identical, unlike a raw-file hash which picks up parquet's embedded
    creation metadata.
    """
    import numpy as np
    import pandas as pd

    df = pd.read_parquet(path)
    h = hashlib.sha256()
    h.update(str(df.shape).encode())
    for col in sorted(map(str, df.columns)):
        h.update(col.encode())
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            h.update(np.ascontiguousarray(series.to_numpy(dtype="float64")).tobytes())
        else:
            h.update(series.astype(str).str.cat(sep="\x00").encode())
    return h.hexdigest()


def _hash_bundle(run_dir: Path) -> dict[str, str]:
    """Content-hash every result parquet in a golden bundle."""
    hashes: dict[str, str] = {}
    for pat in ("dispatch/*.parquet", "*.parquet"):
        for p in sorted(run_dir.glob(pat)):
            rel = str(p.relative_to(run_dir))
            hashes[rel] = _content_hash(p)
    return hashes


def _fidelity_check(
    keeper_bundle: Path,
    golden_dir: Path,
    dropped_meta_keys: dict[str, list[str]] | None = None,
) -> dict:
    """Assert the golden re-solve applied every recorded keeper flag.

    Compares the golden's freshly-written ``meta.json`` and
    ``run_config.json`` (``scenario_config``) against the keeper's on the
    intersection of keys. Any mismatch is a dropped/mis-mapped flag → the
    returned dict carries a non-empty ``mismatched`` list and the caller fails.

    ``dropped_meta_keys`` (from :func:`drop_dead_config_keys`) names, per
    recorded override-channel meta key, the rule-26-deleted inner keys the
    replay could not pass; the channel dicts are compared modulo exactly those
    keys, so the intentional, loudly-reported drop does not read as a
    dropped-flag failure while any OTHER divergence in the dict still does.

    Returns a summary dict with ``matched`` / ``mismatched`` / ``golden_only`` /
    ``keeper_only`` for both meta and scenario_config.
    """

    def _load(d: Path, name: str) -> dict:
        p = d / name
        return json.loads(p.read_text()) if p.is_file() else {}

    def _compare(keep: dict, gold: dict, ignore: set) -> dict:
        kk = set(keep) - ignore
        gk = set(gold) - ignore
        shared = kk & gk
        mismatched = []
        for k in sorted(shared):
            a, b = keep[k], gold[k]
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if abs(float(a) - float(b)) > 1e-12:
                    mismatched.append({"key": k, "keeper": a, "golden": b})
            elif a != b:
                mismatched.append({"key": k, "keeper": a, "golden": b})
        return {
            "matched": len(shared) - len(mismatched),
            "mismatched": mismatched,
            "keeper_only": sorted(kk - gk),
            "golden_only": sorted(gk - kk),
        }

    keep_meta = _load(keeper_bundle, "meta.json")
    gold_meta = _load(golden_dir, "meta.json")
    for meta_key, dead in (dropped_meta_keys or {}).items():
        chan = keep_meta.get(meta_key)
        if isinstance(chan, dict):
            keep_meta[meta_key] = {k: v for k, v in chan.items() if k not in dead}
    keep_cfg = _load(keeper_bundle, "run_config.json").get("scenario_config", {})
    gold_cfg = _load(golden_dir, "run_config.json").get("scenario_config", {})

    return {
        "meta": _compare(keep_meta, gold_meta, FIDELITY_IGNORE_KEYS),
        "scenario_config": _compare(keep_cfg, gold_cfg, set()),
    }


def _partition_block(info: dict) -> dict | None:
    """Return the entry's ``partition`` block, or None for a bare-ISO capture.

    **Schema v3 (Y-25, 2026-09-06)** adds the config IDENTITY, which the
    ercot-248 consolidation took away from ``keeper_id``: both ERCOT roles now
    designate one composed run, so the run id no longer says which of the two
    configurations a golden replayed. The block therefore records
    ``designated_years`` → ``config_id`` — the run whose CONFIGURATION this is
    (``source_run_id`` when the role was composed from an earlier run, else the
    role's own ``run_id``) — plus ``shard_run_id`` (what the shard designates,
    i.e. the run actually replayed) and ``composed`` (whether that run carries
    more than one role). Stamped into the entry for the same reason
    ``keeper_snapshot`` is: a shard edit must not be able to change what an
    already-written golden claims to be.

    ``designated_years`` is the span the ISO's shard assigns to THIS config —
    since R-AW also the span the capture replays, so it equals the entry's
    ``years``; the replayed run's REGISTERED span is recorded separately as the
    entry's ``registered_years``. They legitimately differ (ERCOT's forward
    config is registered 3-year but designated {2024, 2025}), and conflating
    them is exactly the gloss ``docs/FINDING-stage0-capture-neiso-ercot-2026-09.md``
    §2 warns against. Present on a partitioned ISO's bare entry too, since that
    entry is its forward role.
    """
    cfg = info.get("partition_config")
    if not cfg:
        return None
    shard = keeper_store.load_shard(info["iso"], REPO) or {}
    part = shard.get("config_partition") or {}
    shard_run_id = str(cfg.get("run_id", ""))
    roles_on_this_run = [
        c.get("role")
        for c in partition_configs(info["iso"])
        if str(c.get("run_id", "")) == shard_run_id
    ]
    return {
        "iso": info["iso"],
        "role": info["role"],
        "designated_years": [int(y) for y in cfg.get("years", [])],
        # v3 identity: WHICH config, independent of the run it is registered
        # under. ``config_id`` survives a later consolidation or re-keying of
        # the shard; ``shard_run_id`` is what was replayed.
        "config_id": str(cfg.get("source_run_id") or cfg.get("run_id", "")),
        "config_bundle": str(cfg.get("source_bundle") or cfg.get("bundle", "")),
        "shard_run_id": shard_run_id,
        "composed": len(roles_on_this_run) > 1,
        "composed_roles": sorted(r for r in roles_on_this_run if r),
        "label": cfg.get("label", ""),
        "declared": part.get("declared", ""),
        "ruling_source": part.get("ruling_source", ""),
    }


def pin_determinism_env() -> None:
    """Apply :data:`DETERMINISM_ENV` to ``os.environ``.

    Called from :func:`main` and from :func:`capture_one` — i.e. at every entry
    that can reach a solve — rather than at import time. The pin is right for
    this script's own process and wrong for anyone else's: a by-path load
    (``spec_from_file_location`` + ``exec_module``, which
    ``tests/scoring/test_golden_manifest_provenance.py`` does three times) used
    to leak ``MARKET_SIM_HIGHS_THREADS=1`` into the whole pytest process, and
    HiGHS then refused every later LP whose ``threads`` differed from the
    already-initialized process-global scheduler (``model status 'Not Set'``) —
    the latent, scheduling-dependent CI red behind every inflated local test
    count the program has recorded (``docs/FINDING-fast-tier-repair-2026-09.md``
    §4b/§7.6). The test side wraps its loads in an environ snapshot; this closes
    the same hole at the source, so a future by-path load is safe by
    construction.
    """
    for _k, _v in DETERMINISM_ENV.items():
        os.environ[_k] = _v


def capture_one(key: str, stage_tag: str, info: dict) -> dict:
    """Re-solve one keeper config at HEAD into its golden dir; return its entry.

    Args:
        key: The capture key — a bare ISO, or ``<ISO>__<role>`` for a
            config-partition member. It names both the golden subdirectory and
            the manifest key, so two configs of one ISO never collide.
        stage_tag: Golden subdir tag.
        info: Resolved bundle info from :func:`resolve_capture_targets`.

    Raises:
        RuntimeError: if the fidelity oracle finds any applied-flag mismatch.
    """
    iso = info.get("iso") or key
    # Pin here as well as in main(): this is the solve site, so a programmatic
    # caller must not be able to capture a golden without the determinism env.
    # It must precede the deferred heavy import below, exactly as the
    # import-time pin did.
    pin_determinism_env()
    # Heavy import deferred until after the determinism env is pinned.
    from scripts.run_calibration import _load_reference
    from scripts.run_calibration_full import solve_and_persist

    meta = json.loads((info["bundle"] / "meta.json").read_text())
    registered_years = sorted(int(y) for y in meta["years"])
    # The span to replay: the resolved info's ``years`` — for a partitioned
    # config, its DESIGNATED span (R-AW); otherwise the run's registered span.
    # Rule 22, asserted at the solve site as well as at resolution: never a
    # year the replayed run's own record does not carry.
    years = sorted(int(y) for y in info.get("years") or registered_years)
    if not set(years) <= set(registered_years):
        raise ValueError(
            f"{key}: replay span {years} is not a subset of the bundle's recorded "
            f"span {registered_years} (rule 22: never widened)"
        )
    hours = int(meta["hours"])
    kwargs, defaulted = build_solve_kwargs(meta, solve_and_persist)
    dropped_dead = drop_dead_config_keys(kwargs)

    golden_dir = GOLDENS_ROOT / stage_tag / key
    golden_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "[%s] re-solving keeper %s years=%s hours=%s (%d recorded flags, "
        "%d params defaulted)",
        key,
        info["keeper_id"],
        years,
        hours,
        len(kwargs),
        len(defaulted),
    )

    reference = _load_reference()
    solve_and_persist(
        years,
        iso,
        hours,
        reference,
        commitment=bool(meta["commitment"]),
        screen_coal=bool(meta["commitment_screen_coal"]),
        run_dir=golden_dir,
        note=f"regression-golden {stage_tag} (Stage-0 baseline; not a keeper)",
        **kwargs,
    )

    fidelity = _fidelity_check(info["bundle"], golden_dir, dropped_dead)
    meta_bad = fidelity["meta"]["mismatched"]
    cfg_bad = fidelity["scenario_config"]["mismatched"]

    # HARD gate: the meta comparison. meta echoes the passed kwargs verbatim, so
    # any mismatch on a shared key is a dropped or mis-mapped flag — fail.
    if meta_bad:
        for m in meta_bad[:30]:
            logger.error(
                "[%s] META FLAG MISMATCH %s: keeper=%r golden=%r",
                key,
                m["key"],
                m["keeper"],
                m["golden"],
            )
        raise RuntimeError(
            f"{key}: fidelity oracle failed — {len(meta_bad)} recorded flag(s) "
            f"diverged between keeper and golden meta.json; the golden does not "
            f"faithfully replay the keeper's flags."
        )

    # INFORMATIONAL: scenario_config is the RESOLVED config, which legitimately
    # drifts with HEAD base-config changes (goldens are current-HEAD baselines,
    # not byte-reproductions of the July-3 bundles). Surface the drift so a
    # reviewer can sanity-check it, but do not fail on it.
    if cfg_bad:
        logger.warning(
            "[%s] scenario_config drift vs keeper on %d field(s) (expected if "
            "base config moved since the keeper was frozen): %s",
            key,
            len(cfg_bad),
            ", ".join(m["key"] for m in cfg_bad[:15]),
        )

    logger.info(
        "[%s] fidelity OK: %d recorded flags replayed identically "
        "(%d HEAD-only meta keys); scenario_config %d matched, %d drifted",
        key,
        fidelity["meta"]["matched"],
        len(fidelity["meta"]["golden_only"]),
        fidelity["scenario_config"]["matched"],
        len(cfg_bad),
    )

    entry = {
        "keeper_id": info["keeper_id"],
        "bundle": str(info["bundle"].relative_to(REPO)),
        "years": years,
        # The replayed run's own recorded span; ``years`` ⊆ this (rule 22),
        # and the gate re-checks the inclusion on every run.
        "registered_years": registered_years,
        "hours": hours,
        "recorded_flag_count": len(kwargs),
        "defaulted_unrecorded_params": defaulted,
        "dropped_dead_config_keys": dropped_dead,
        "fidelity": {
            "meta_matched": fidelity["meta"]["matched"],
            "meta_head_only": fidelity["meta"]["golden_only"],
            "meta_keeper_only": fidelity["meta"]["keeper_only"],
            "scenario_config_matched": fidelity["scenario_config"]["matched"],
            "scenario_config_head_only": fidelity["scenario_config"]["golden_only"],
            "scenario_config_drift": [
                m["key"] for m in fidelity["scenario_config"]["mismatched"]
            ],
        },
        "content_hashes": _hash_bundle(golden_dir),
        # Schema v2: provenance belongs to THIS entry. A later capture of a
        # different ISO merges its own entry and leaves this one untouched.
        "provenance": _provenance(),
        "keeper_snapshot": _keeper_snapshot(info),
    }
    part = _partition_block(info)
    if part is not None:
        entry["partition"] = part
    return entry


def _run_subprocess(key: str, stage_tag: str) -> int:
    """Re-invoke this script for a single capture key in its own process."""
    iso = key  # the CLI takes the capture key verbatim under --iso
    env = dict(os.environ)
    env.update(DETERMINISM_ENV)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--iso",
        iso,
        "--stage-tag",
        stage_tag,
        "--_single",
    ]
    logger.info("[%s] launching subprocess", iso)
    return subprocess.call(cmd, env=env, cwd=REPO)


# v3 (2026-09-06): a partition entry carries its config IDENTITY
# (partition.config_id / shard_run_id), because a composed keeper's run id no
# longer identifies a config. Additive — check_golden_manifest still reads and
# enforces every v2 manifest unchanged (its MIN_SCHEMA_VERSION stays 2).
MANIFEST_SCHEMA_VERSION = 3


def manifest_version(entries: dict[str, dict]) -> int:
    """Return the schema version the merged ``entries`` actually satisfy.

    :data:`MANIFEST_SCHEMA_VERSION` when every partition entry carries the v3
    identity keys (:data:`check_golden_manifest.REQUIRED_PARTITION_V3_KEYS`),
    else 2. A manifest declares the version its CONTENTS meet, never the
    version of the tool that last touched it: merging one new v3 capture into
    a file holding pre-v3 partition entries must not re-label those entries as
    something they are not — the same defect-A reasoning that moved provenance
    per-entry, applied to the schema stamp itself. A mixed file therefore stays
    v2 (where the identity keys are optional) until every partition entry in it
    is re-captured, and the gate still reads ``config_id`` wherever one is
    present, so a v2-declared file gets the v3 benefit for the entries that
    have it.
    """
    for entry in entries.values():
        part = entry.get("partition")
        if isinstance(part, dict) and not all(
            k in part for k in REQUIRED_PARTITION_V3_KEYS
        ):
            return 2
    return MANIFEST_SCHEMA_VERSION


def write_manifest(stage_tag: str, entries: dict[str, dict]) -> Path:
    """Write / merge the hashes-only manifest for a stage tag.

    Only the keys in ``entries`` are rewritten. Under schema v2 the top level
    holds nothing capture-specific, so merging one entry cannot re-label any
    other — the v1 failure mode this function used to have. The same merge is
    what makes a config-partition entry (keyed ``<ISO>__<role>``) purely
    additive: it lands beside the bare-ISO entry rather than replacing it.

    The declared ``schema_version`` is :func:`manifest_version` of the MERGED
    entries, so a v3 capture merged into a file with pre-v3 partition entries
    leaves the file honestly at v2.
    """
    manifest_path = GOLDENS_ROOT / stage_tag / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text()).get("keepers", {})
    existing.update(entries)
    payload = {
        "schema_version": manifest_version(existing),
        "stage_tag": stage_tag,
        "hash_scheme": "sha256-of-canonical-column-float64-bytes",
        "note": (
            "Current-HEAD regression baselines (Stage-0). NOT byte-reproductions "
            "of the registered July-3 keeper bundles. Multi-GB bundles are "
            "gitignored; only this manifest is committed. Provenance (git sha, "
            "basis sha, env pins, timestamp) and the provenance run's identity "
            "are PER ENTRY under keepers.<ISO>.provenance / .keeper_snapshot — "
            "there is deliberately no shared top-level git_sha. An entry keyed "
            "<ISO>__<role> (e.g. ERCOT__forward) is a CONFIG-PARTITION "
            "member: the role is verbatim that ISO's "
            "keepers/<ISO>.json config_partition.configs[].role, the entry "
            "carries an extra 'partition' block naming the CONFIG it captured "
            "(schema v3: designated_years -> config_id, plus shard_run_id — a "
            "composed keeper's run id is shared by several roles and does not "
            "identify a config), and it is an ordinary entry "
            "in every other respect — additive, so the bare-ISO entries are "
            "untouched. check_golden_manifest.live_keeper resolves both key "
            "forms. A partitioned ISO's BARE entry is its forward config "
            "replayed on the forward role's designated span (owner ruling "
            "R-AW, 2026-09-05), with the run's registered span kept in "
            "registered_years; a capture key retired by ruling "
            "(check_golden_manifest.RETIRED_CAPTURE_KEYS) keeps its entries as "
            "historical capture records."
        ),
        "keepers": existing,
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    logger.info("manifest written: %s (%d keepers)", manifest_path, len(existing))
    return manifest_path


def main() -> int:
    """Entry point."""
    # Determinism pin, applied here (this process is the script's own) rather
    # than at import — see pin_determinism_env.
    pin_determinism_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iso",
        nargs="+",
        default=None,
        help="Capture key(s): a bare ISO (NEISO, or ERCOT CAISO) for that "
        "shard's designated keeper, or <ISO>__<role> (ERCOT__carveout-2023) "
        "for a config-partition member. Omit with --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Capture every ISO's designated keeper (six).",
    )
    parser.add_argument(
        "--include-partitions",
        action="store_true",
        help="With --all, also capture every config_partition member that is "
        "not already the ISO's designated keeper (e.g. ERCOT__carveout-2023).",
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="Print every capture key the keeper shards designate, and exit "
        "(no solve). --stage-tag is not required with this flag.",
    )
    parser.add_argument(
        "--stage-tag",
        default=None,
        help="Golden subdir tag, e.g. stage1-before / stage1-after / aa-run1. "
        "Required for every mode except --list-configs.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=2,
        help="Max concurrent per-ISO subprocesses (CLAUDE.md rule 8: ≤2 for "
        "per-plant multi-zone LPs). Default 2.",
    )
    parser.add_argument(
        "--_single",
        action="store_true",
        help=argparse.SUPPRESS,  # internal: in-process single-ISO solve
    )
    args = parser.parse_args()

    if args.list_configs:
        for iso in keeper_store.iso_list(REPO):
            rec = keeper_store.load_shard(iso, REPO) or {}
            designated = rec.get("keeper")
            fwd = (
                _partition_config(iso, FORWARD_ROLE) if partition_configs(iso) else None
            )
            bare = (
                f"; bare key = {FORWARD_ROLE!r} role on its designated years "
                f"{fwd.get('years', [])} (R-AW)"
                if fwd is not None
                else ""
            )
            print(f"{iso:6} {designated}   (capture key: {iso}{bare})")
            for cfg in partition_configs(iso):
                role = cfg.get("role", "")
                key = capture_key(iso, role)
                mark = " [= designated keeper]" if cfg["run_id"] == designated else ""
                if key in RETIRED_CAPTURE_KEYS:
                    mark += " [RETIRED capture key — refused]"
                print(
                    f"       {cfg['run_id']}   (capture key: {key}; designated "
                    f"years {cfg.get('years', [])}){mark}"
                )
        return 0

    if not args.stage_tag:
        parser.error("--stage-tag is required (except with --list-configs)")

    if args.all:
        keys = sorted(resolve_keeper_bundles())
        if args.include_partitions:
            designated = set(keeper_store.keeper_list(REPO))
            extra = [
                capture_key(iso, cfg["role"])
                for iso in keeper_store.iso_list(REPO)
                for cfg in partition_configs(iso)
                # A partition member that IS the ISO's designated keeper is
                # already covered by the bare-ISO key (the forward role, R-AW);
                # capturing it twice would solve the same config into two
                # golden dirs. A retired key is never captured.
                if cfg["run_id"] not in designated
                and capture_key(iso, cfg["role"]) not in RETIRED_CAPTURE_KEYS
            ]
            keys += sorted(extra)
    elif args.iso:
        keys = [capture_key(*parse_capture_key(i)) for i in args.iso]
    else:
        parser.error("provide --iso <KEY...>, --all, or --list-configs")

    try:
        bundles = resolve_capture_targets(keys)
    except KeyError as exc:
        parser.error(str(exc.args[0]))

    # Single in-process capture (also the subprocess-child path).
    if args._single or len(keys) == 1:
        rc = 0
        for key in keys:
            try:
                entry = capture_one(key, args.stage_tag, bundles[key])
                write_manifest(args.stage_tag, {key: entry})
            except Exception:
                logger.exception("[%s] capture failed", key)
                rc = 1
        return rc

    # Multiple captures: fan out to ≤max_concurrency subprocesses (memory cap).
    rc = 0
    with ThreadPoolExecutor(max_workers=max(1, args.max_concurrency)) as ex:
        futures = {ex.submit(_run_subprocess, k, args.stage_tag): k for k in keys}
        for fut in as_completed(futures):
            key = futures[fut]
            code = fut.result()
            if code != 0:
                logger.error("[%s] subprocess exited %d", key, code)
                rc = 1
    logger.info(
        "all captures complete (rc=%d); manifest at %s",
        rc,
        GOLDENS_ROOT / args.stage_tag / "manifest.json",
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())
