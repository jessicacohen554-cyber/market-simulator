#!/usr/bin/env python3
"""Gate the regression-golden manifests: per-entry provenance + retention safety.

Two defects this gate exists to stop, both observed live on
``results/regression-goldens/perfb-stage0/manifest.json`` and recorded in
``docs/FINDING-stage0-provenance-repair-2026-09.md``:

**A. Wrong-tree provenance.** Schema v1 carried ONE top-level ``git_sha`` for
however many captures the manifest held. ``capture_keeper_goldens.write_manifest``
merges a single ISO's entry into the existing file, so every capture silently
re-stamped that shared field for all the earlier ones. Six captures taken at six
trees ended up asserting one tree; the five older rows carried a sha that was
*valid and wrong*, which is strictly harder to notice than one that does not
resolve. Schema v2 moves provenance into each entry, and this gate refuses a
manifest that reintroduces the shared field.

**B. Orphaned provenance runs.** Top-15-per-ISO registry retention and these
manifests reference the same run ids and know nothing about each other. Correct,
policy-compliant prunes left five of six perfb-stage0 captures with no registered
provenance run — and every program gate stayed green throughout, because nothing
checked. The fix is on the MANIFEST side (exempting golden runs from retention
would re-create the dead-bundle class the parity gate already struggles with):
each entry carries a ``keeper_snapshot`` copied from the sidecar at capture time,
so the entry survives the prune with its meaning intact. This gate FAILS an entry
whose sidecar is gone AND which never absorbed that snapshot — the only state in
which a prune actually destroys information — and REPORTS, without failing, every
entry whose sidecar has been pruned or whose keeper has since moved on.

**Entry keys, and config partitions (2026-09-02).** A manifest entry is keyed
either by a bare ISO — resolved against ``keepers/<ISO>.json``'s ``keeper`` —
or, for an ISO whose shard carries a ``config_partition`` block, by
``<ISO>__<role>`` (``ERCOT__carveout-2023``), resolved against that block's
``configs[].run_id``. ERCOT is the first such ISO: a forward config for
{2024, 2025} plus a 2023 carve-out, owner ruling 2026-08-26. Both key forms go
through :func:`live_keeper`, so a partition golden reports CURRENT/STALE against
the config it was actually captured against instead of the perpetual
``STALE (live keeper: None)`` that a bare-ISO-only lookup would produce
(``docs/FINDING-stage0-capture-neiso-ercot-2026-09.md`` §2 blocker 4). Partition
entries are ordinary schema-v2 entries in every other respect and are validated
identically — the representation is additive, so nothing here special-cases
them beyond the key split.

Exit codes:
    0 — every manifest conforms (pruned sidecars and stale keepers are reported,
        not failed: retention is correct policy and goldens are allowed to age).
    1 — at least one hard violation.

Usage:
    python scripts/check_golden_manifest.py
    python scripts/check_golden_manifest.py --manifest results/regression-goldens/perfb-stage0/manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLDENS_ROOT = REPO / "results" / "regression-goldens"
REGISTRY_DIR = REPO / "frontend" / "data" / "backcast" / "registry"
KEEPERS_DIR = REPO / "frontend" / "data" / "backcast" / "keepers"

# Fields a v2 entry's provenance block must carry. ``git_sha`` may be the literal
# "unknown" (an honest unrecoverable) but the key must be present and explicit.
REQUIRED_PROVENANCE_KEYS = (
    "git_sha",
    "basis_sha",
    "git_dirty",
    "recorded_at",
    "env",
    "source",
)

# Fields the entry must have absorbed from the provenance run's registry sidecar
# for it to stay meaningful after that sidecar is pruned.
REQUIRED_SNAPSHOT_KEYS = ("id", "iso", "label", "date", "years", "bundle")

# The v1 top-level keys whose presence IS the defect: capture-specific values at
# a scope shared by every entry.
FORBIDDEN_TOP_LEVEL_KEYS = ("git_sha", "git_dirty", "env", "highspy_version")

MIN_SCHEMA_VERSION = 2

# Separator between the ISO and the config-partition role in a manifest key
# (``ERCOT__carveout-2023``). Must match
# ``capture_keeper_goldens.PARTITION_KEY_SEP``; duplicated rather than imported
# because this gate is deliberately stdlib-only and importable with no solve
# dependencies (the capture tool pulls in numpy/highspy at import time).
PARTITION_KEY_SEP = "__"

# THE RATCHET. Every manifest written since the 2026-09-01 repair is schema v2,
# because ``capture_keeper_goldens.write_manifest`` can no longer write anything
# else. These 37 are the pre-repair stage/wave/A-A goldens that predate it —
# retired stage artifacts, not live baselines. They are ENUMERATED rather than
# pattern-matched so the exemption cannot grow silently: a manifest under any
# stage tag not on this list must be v2 or this gate fails.
#
# They are NOT clean. Measured at the repair pin, 67 of 70 entries across all 38
# manifests have a pruned provenance run and no keeper_snapshot — the perfb-stage0
# five-wide condition is repo-wide at 96 %. Migrating them needs the same
# per-manifest historical recovery perfb-stage0 got and is a separate, owner-
# scoped job; see docs/FINDING-stage0-provenance-repair-2026-09.md §6.
LEGACY_V1_MANIFESTS = frozenset(
    {
        "3e-after",
        "3e-before",
        "3f-transmission-after",
        "3f-transmission-before",
        "aa-run1",
        "aa-run2",
        "constants-split-after",
        "constants-split-before",
        "dispatch-lp-after",
        "dispatch-lp-before",
        "eia930-after",
        "eia930-before",
        "fleet-split-after",
        "fleet-split-before",
        "fleetdup-after",
        "fleetdup-before",
        "fuel-after",
        "fuel-before",
        "lane-after",
        "lane-before",
        "perfb-d-after",
        "perfb-d-before",
        "perfb-e-after",
        "stage1-before",
        "stage2-after",
        "stage23-before",
        "stage3-after",
        "stage4-after",
        "stage4-before",
        "stage4-probe-after",
        "stage4-probe-before",
        "stage6-before-e46ab11",
        "stage7-after-140c61f",
        "wave4c-after",
        "wave4c-before",
        "wave4d-after",
        "wave4d-before",
    }
)


def live_keeper(key: str) -> str | None:
    """Return the run id the keeper shards currently designate for ``key``.

    Two key forms, both resolved against ``keepers/<ISO>.json``:

    * a bare ISO (``"ERCOT"``) → the shard's ``keeper`` field, i.e. the ISO's
      single designated keeper;
    * a config-partition key (``"ERCOT__carveout-2023"``) → the ``run_id`` of
      the ``config_partition.configs[]`` entry whose ``role`` matches the half
      after the separator. This is the lookup that makes a partition golden
      report its true state instead of ``STALE (live keeper: None)`` forever
      (``docs/FINDING-stage0-capture-neiso-ercot-2026-09.md`` §2 blocker 4).

    Returns None when the shard is missing/unreadable, or when the named role is
    not (or is no longer) designated — which the caller reports as STALE, the
    correct reading: a golden captured against a retired config is exactly what
    staleness means.
    """
    iso, _, role = key.partition(PARTITION_KEY_SEP)
    shard = KEEPERS_DIR / f"{iso.upper()}.json"
    if not shard.is_file():
        return None
    try:
        rec = json.loads(shard.read_text())
    except Exception:
        return None
    if not role:
        return rec.get("keeper")
    for cfg in (rec.get("config_partition") or {}).get("configs") or []:
        if isinstance(cfg, dict) and str(cfg.get("role", "")).lower() == role.lower():
            return cfg.get("run_id")
    return None


def find_manifests() -> list[Path]:
    """Return every committed golden manifest, sorted by path."""
    return sorted(GOLDENS_ROOT.glob("*/manifest.json"))


def check_manifest(path: Path) -> tuple[list[str], list[str]]:
    """Validate one manifest.

    Returns:
        ``(failures, notes)`` — failures are hard violations; notes are the
        visible-coupling report (pruned sidecars, stale keepers) that this gate
        surfaces without failing.
    """
    rel = path.relative_to(REPO)
    fails: list[str] = []
    notes: list[str] = []

    try:
        man = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - unparseable manifest
        return [f"{rel}: unreadable ({exc})"], []

    legacy = path.parent.name in LEGACY_V1_MANIFESTS
    version = man.get("schema_version")

    if legacy:
        # Grandfathered: report its coupling state, enforce nothing. It may still
        # opt in by being migrated to v2 — then it is enforced like any other.
        if not isinstance(version, int) or version < MIN_SCHEMA_VERSION:
            for key in sorted(man.get("keepers", {})):
                entry = man["keepers"][key]
                kid = entry.get("keeper_id")
                pruned = not (REGISTRY_DIR / f"{kid}.json").is_file()
                notes.append(
                    f"{rel} [{key}]: {kid} — LEGACY v1 (pre-repair, grandfathered), "
                    f"provenance run {'PRUNED from registry' if pruned else 'registered'}"
                )
            return fails, notes

    if not isinstance(version, int) or version < MIN_SCHEMA_VERSION:
        fails.append(
            f"{rel}: schema_version is {version!r}; per-entry provenance requires "
            f">= {MIN_SCHEMA_VERSION} (see the module docstring, defect A). Stage "
            f"tag {path.parent.name!r} is not on the LEGACY_V1_MANIFESTS ratchet "
            f"list, so it must be written by the current capture tool."
        )

    for key in FORBIDDEN_TOP_LEVEL_KEYS:
        if key in man:
            fails.append(
                f"{rel}: top-level {key!r} is forbidden — it is capture-specific "
                f"and one capture re-stamps it for every other entry. Move it to "
                f"keepers.<ISO>.provenance."
            )

    keepers = man.get("keepers")
    if not isinstance(keepers, dict) or not keepers:
        fails.append(f"{rel}: no 'keepers' entries")
        return fails, notes

    for key in sorted(keepers):
        entry = keepers[key]
        where = f"{rel} [{key}]"

        prov = entry.get("provenance")
        if not isinstance(prov, dict):
            fails.append(f"{where}: missing 'provenance' block (schema v2)")
        else:
            for req in REQUIRED_PROVENANCE_KEYS:
                if req not in prov:
                    fails.append(f"{where}: provenance missing {req!r}")
            sha = prov.get("git_sha")
            if not isinstance(sha, str) or not sha:
                fails.append(f"{where}: provenance.git_sha must be a non-empty string")
            elif sha == "unknown" and not prov.get("provenance_note"):
                fails.append(
                    f"{where}: provenance.git_sha is 'unknown' with no "
                    f"'provenance_note' — an unrecoverable sha must say why"
                )

        snap = entry.get("keeper_snapshot")
        keeper_id = entry.get("keeper_id")
        sidecar = REGISTRY_DIR / f"{keeper_id}.json"
        pruned = not sidecar.is_file()

        if not isinstance(snap, dict):
            # THE retention invariant. A snapshot is required either way, but the
            # message names the consequence that is already real when pruned.
            fails.append(
                f"{where}: missing 'keeper_snapshot'"
                + (
                    f" AND its provenance run {keeper_id} has been pruned from the "
                    f"registry — the entry no longer records what it was captured "
                    f"against (defect B)"
                    if pruned
                    else " (required before retention prunes the sidecar)"
                )
            )
        else:
            for req in REQUIRED_SNAPSHOT_KEYS:
                if req not in snap:
                    fails.append(f"{where}: keeper_snapshot missing {req!r}")
            # The snapshot must describe the entry it lives in, or it is a copy
            # of the wrong run and worse than none.
            if snap.get("id") != keeper_id:
                fails.append(
                    f"{where}: keeper_snapshot.id {snap.get('id')!r} != keeper_id "
                    f"{keeper_id!r}"
                )
            if "bundle" in snap and snap["bundle"] != entry.get("bundle"):
                fails.append(
                    f"{where}: keeper_snapshot.bundle {snap['bundle']!r} != entry "
                    f"bundle {entry.get('bundle')!r}"
                )
            if "years" in snap and snap["years"] != entry.get("years"):
                fails.append(
                    f"{where}: keeper_snapshot.years {snap['years']} != entry years "
                    f"{entry.get('years')}"
                )

        # --- The visible coupling. Reported, never failed. ---
        current = live_keeper(key)
        state = "CURRENT" if current == keeper_id else "STALE"
        if state == "CURRENT":
            detail = ""
        elif current is None and PARTITION_KEY_SEP in key:
            # Distinguish "the shard no longer designates this role" from an
            # ordinary supersession — otherwise a typo'd or retired role reads
            # identically to a golden that simply aged.
            _iso, _, _role = key.partition(PARTITION_KEY_SEP)
            detail = (
                f" (keepers/{_iso.upper()}.json designates no config_partition "
                f"role {_role!r})"
            )
        else:
            detail = f" (live keeper: {current})"
        notes.append(
            f"{where}: {keeper_id} — provenance run "
            f"{'PRUNED from registry' if pruned else 'registered'}, "
            f"golden {state}{detail}"
        )

    return fails, notes


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        nargs="+",
        default=None,
        help="Manifest path(s) to check. Default: every results/regression-goldens/*/manifest.json.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="List every grandfathered legacy-v1 entry instead of summarizing them.",
    )
    args = parser.parse_args()

    paths = (
        [Path(p) if Path(p).is_absolute() else REPO / p for p in args.manifest]
        if args.manifest
        else find_manifests()
    )
    if not paths:
        print("golden-manifest: no manifests found — nothing to check")
        return 0

    all_fails: list[str] = []
    all_notes: list[str] = []
    for path in paths:
        if not path.is_file():
            all_fails.append(f"{path}: not found")
            continue
        fails, notes = check_manifest(path)
        all_fails += fails
        all_notes += notes

    legacy_notes = [n for n in all_notes if "LEGACY v1" in n]
    live_notes = [n for n in all_notes if "LEGACY v1" not in n]

    for note in live_notes:
        print(f"  {note}")
    if legacy_notes and args.verbose:
        for note in legacy_notes:
            print(f"  {note}")
    elif legacy_notes:
        lp = sum(1 for n in legacy_notes if "PRUNED" in n)
        print(
            f"  {len(legacy_notes)} legacy v1 entr(ies) grandfathered by the "
            f"ratchet ({lp} with a pruned provenance run) — rerun with --verbose "
            f"to list them"
        )

    pruned = sum(1 for n in live_notes if "PRUNED" in n)
    stale = sum(1 for n in live_notes if "golden STALE" in n)
    print(
        f"golden-manifest: {len(paths)} manifest(s), {len(all_notes)} entr(ies) "
        f"({len(live_notes)} enforced / {len(legacy_notes)} legacy); of the "
        f"enforced, {pruned} with a pruned provenance run, {stale} stale vs the "
        f"live keeper"
    )
    if pruned:
        print(
            "  note: a pruned provenance run is NOT a failure — keeper-only retention "
            "is correct policy (rule 15 as amended 2026-09-05). It is "
            "survivable only because each entry carries its own "
            "keeper_snapshot, which is what this gate enforces."
        )

    if all_fails:
        for f in all_fails:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"golden-manifest: {len(all_fails)} violation(s)", file=sys.stderr)
        return 1
    print("golden-manifest: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
