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
``<ISO>__<role>``, resolved against that block's ``configs[].run_id``. ERCOT is
the first such ISO: a forward config for {2024, 2025} plus a 2023 carve-out,
owner ruling 2026-08-26. Both key forms go through :func:`live_keeper`, so a
partition golden reports CURRENT/STALE against the config it was actually
captured against instead of the perpetual ``STALE (live keeper: None)`` that a
bare-ISO-only lookup would produce
(``docs/FINDING-stage0-capture-neiso-ercot-2026-09.md`` §2 blocker 4). Partition
entries are ordinary schema-v2 entries in every other respect and are validated
identically — the representation is additive, so nothing here special-cases
them beyond the key split.

**Schema v3: the entry names WHICH CONFIG it captured (Y-25, 2026-09-06).**
The ercot-248 consolidation composed both of ERCOT's designated configs onto
ONE registered run, so ``keeper_id`` stopped identifying a config: the forward
and carve-out entries carry the same run id, and only the shard could say which
config each ``role`` currently stands for. That is defect B's shape again — a
manifest entry whose meaning lives in a file that moves — and it is why the two
configs could not both be represented at v2 in any way that survives a shard
edit. Schema v3 pins the config identity INTO the entry's ``partition`` block:
``designated_years`` → ``config_id`` (the run whose configuration this is: the
shard's ``source_run_id``, else its ``run_id``), alongside ``shard_run_id`` (the
run the shard designates for the role, composed or not). ADDITIVE and
BACKWARD-COMPATIBLE: ``MIN_SCHEMA_VERSION`` stays 2, every committed v2 entry
parses and is enforced exactly as before, and the v3 identity keys are required
only of a manifest that declares v3 (:data:`REQUIRED_PARTITION_V3_KEYS`). A
version above :data:`MAX_SCHEMA_VERSION` FAILS rather than passing unread.

**Per-config coverage (Y-25, 2026-09-06).** For an ISO whose shard designates
more than one config, a bare ``golden CURRENT`` line answered a question nobody
asked: it reported the FORWARD config and said nothing about the rest of the
partition, so a manifest covering one of ERCOT's two configs read exactly like
full coverage. :func:`config_coverage` adds one report line per partitioned ISO
present in a manifest, stating each designated config as CURRENT / STALE /
UNCOVERED with its reason — ERCOT reads *"forward CURRENT; carveout-2023
UNCOVERED"*. It is a REPORT, never a failure: the carve-out is uncovered by
ruling (R-AW retired its capture key), and a gate cannot demand a capture the
owner retired. It changes no entry count.

**The bare key of a partitioned ISO is its FORWARD role (R-AW, 2026-09-05).**
Owner ruling, audit-program director sitting 2026-09-05 (card "ERCOT key"),
verbatim: *"The golden config should be the 2024:2025 one not 2023"*. Read as:
the ERCOT stage-0 golden captures the FORWARD config on its designated span
{2024, 2025}, and the ``ERCOT__carveout-2023`` capture key is RETIRED
(:data:`RETIRED_CAPTURE_KEYS`). Consequences enforced here: for a partitioned
ISO the bare key resolves through the ``forward`` role (:data:`FORWARD_ROLE`)
rather than the ``keeper`` field alone; a CURRENT golden of a partitioned config
must replay exactly that role's designated span
(:func:`designated_years`) — never the composed run's whole registered span,
which would replay the carve-out year under the forward config; an entry that
records ``registered_years`` must have ``years`` inside it (rule 22, the
designated span is never a superset of the registered one); and a RETIRED key is
still held to every v2 invariant but is reported as a historical capture record
instead of being compared to the live shard — a manifest ``keeper_id`` records
which run's outputs were actually captured, so retiring the key never rewrites
the entries written under it. Record:
``docs/handoffs/FINDING-y14-ercot-golden-forward-2026-09-05.md``.

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

# The highest schema this gate can read. A manifest declaring more is FAILED,
# not waved through: a future field this gate silently ignores is exactly the
# class of silence defects A and B were.
MAX_SCHEMA_VERSION = 3

# The schema at which a partition entry must carry its config IDENTITY, not
# just its role. Below it the identity keys are optional (every committed v2
# entry predates them); at or above it they are required of any entry carrying
# a ``partition`` block.
PARTITION_IDENTITY_SCHEMA_VERSION = 3

# Keys a v3 ``partition`` block must carry. ``config_id`` is the identity the
# composed keeper took away from ``keeper_id``: the run whose CONFIGURATION
# this entry replayed (keepers/<ISO>.json config_partition.configs[].
# source_run_id, else run_id). ``shard_run_id`` is the run the shard designates
# for the role — equal to ``keeper_id`` at capture time, and the two differ
# from ``config_id`` whenever several roles are composed onto one run.
REQUIRED_PARTITION_V3_KEYS = (
    "iso",
    "role",
    "designated_years",
    "config_id",
    "shard_run_id",
)

# Separator between the ISO and the config-partition role in a manifest key
# (``ERCOT__carveout-2023``). Must match
# ``capture_keeper_goldens.PARTITION_KEY_SEP``; duplicated rather than imported
# because this gate is deliberately stdlib-only and importable with no solve
# dependencies (the capture tool pulls in numpy/highspy at import time).
PARTITION_KEY_SEP = "__"

# Marker that identifies a per-config COVERAGE line among the notes. Coverage
# lines are a separate report about the capture programme, not entry findings,
# so they are filtered out before every entry tally: adding them must not move
# one count this gate prints.
COVERAGE_MARK = " partition coverage): "

# The config_partition role a partitioned ISO's BARE capture key resolves to:
# the config the model uses going forward. Named in the shard verbatim
# (keepers/ERCOT.json config_partition.configs[].role == "forward"). R-AW.
FORWARD_ROLE = "forward"

# Capture keys RETIRED by owner ruling, with the citation. A retired key's
# manifest entries are historical capture records: still validated against
# every schema-v2 invariant (per-entry provenance, keeper_snapshot), but never
# compared to the live keeper shard, and refused by capture_keeper_goldens.py
# for any NEW capture. An explicit constant rather than a shard field because
# the shard is a calibration-lane surface this gate only reads, and the ruling
# is about the GOLDEN, not the keeper: keepers/ERCOT.json still designates the
# carve-out for 2023 — what is retired is the stage-0 capture of it.
RETIRED_CAPTURE_KEYS: dict[str, str] = {
    "ERCOT__carveout-2023": (
        "R-AW (owner, audit-program director sitting 2026-09-05, card "
        '"ERCOT key"): "The golden config should be the 2024:2025 one not '
        '2023" — the ERCOT stage-0 golden is the FORWARD config on its '
        "designated span {2024, 2025} under the bare ERCOT key; "
        "docs/handoffs/FINDING-y14-ercot-golden-forward-2026-09-05.md"
    ),
}

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


def _load_shard(iso: str) -> dict | None:
    """Return the parsed ``keepers/<ISO>.json``, or None if missing/unreadable."""
    shard = KEEPERS_DIR / f"{iso.upper()}.json"
    if not shard.is_file():
        return None
    try:
        rec = json.loads(shard.read_text())
    except Exception:
        return None
    return rec if isinstance(rec, dict) else None


def _partition_config(rec: dict, role: str) -> dict | None:
    """Return the shard's ``config_partition.configs[]`` entry for ``role``."""
    for cfg in (rec.get("config_partition") or {}).get("configs") or []:
        if isinstance(cfg, dict) and str(cfg.get("role", "")).lower() == role.lower():
            return cfg
    return None


def resolve_role(key: str) -> tuple[str, str | None]:
    """Split a manifest key into ``(ISO, role)``, applying R-AW to bare keys.

    A bare ISO whose shard carries a ``config_partition`` block resolves to the
    :data:`FORWARD_ROLE` config — the config the model uses going forward is
    what the bare golden captures (owner ruling R-AW, 2026-09-05). A bare ISO
    with no partition block, or no readable shard, has no role (``None``); a
    ``<ISO>__<role>`` key keeps its role verbatim.
    """
    iso, _, role = key.partition(PARTITION_KEY_SEP)
    iso = iso.upper()
    if role:
        return iso, role
    rec = _load_shard(iso)
    if rec is not None and _partition_config(rec, FORWARD_ROLE) is not None:
        return iso, FORWARD_ROLE
    return iso, None


def live_keeper(key: str) -> str | None:
    """Return the run id the keeper shards currently designate for ``key``.

    Two key forms, both resolved against ``keepers/<ISO>.json``:

    * a bare ISO (``"ERCOT"``) → the shard's ``keeper`` field, i.e. the ISO's
      single designated keeper — EXCEPT that a shard carrying a
      ``config_partition`` block resolves through its :data:`FORWARD_ROLE`
      config's ``run_id`` (R-AW: the bare golden IS the forward config; the
      ercot-248 consolidation keeps the two equal, and when they ever differ
      the role the ruling names wins);
    * a config-partition key (``"ERCOT__forward"``) → the ``run_id`` of the
      ``config_partition.configs[]`` entry whose ``role`` matches the half
      after the separator. This is the lookup that makes a partition golden
      report its true state instead of ``STALE (live keeper: None)`` forever
      (``docs/FINDING-stage0-capture-neiso-ercot-2026-09.md`` §2 blocker 4).

    Returns None when the shard is missing/unreadable, or when the named role is
    not (or is no longer) designated — which the caller reports as STALE, the
    correct reading: a golden captured against an un-ruled config is exactly
    what staleness means. (A key RETIRED by ruling — :data:`RETIRED_CAPTURE_KEYS`
    — still resolves here; :func:`check_manifest` is what skips the comparison.)
    """
    iso, role = resolve_role(key)
    rec = _load_shard(iso)
    if rec is None:
        return None
    if role is None:
        return rec.get("keeper")
    cfg = _partition_config(rec, role)
    return cfg.get("run_id") if cfg is not None else None


def designated_years(key: str) -> list[int] | None:
    """Return the shard's DESIGNATED year span for the config ``key`` names.

    The span a CURRENT golden under this key must replay (R-AW): for a
    partitioned ISO's bare key, the forward role's ``years``; for a
    ``<ISO>__<role>`` key, that role's. None when the key resolves to no
    partition config (an ordinary one-config ISO, or an undesignated role) —
    then the entry's ``years`` is the run's registered span and nothing here
    constrains it.
    """
    iso, role = resolve_role(key)
    if role is None:
        return None
    rec = _load_shard(iso)
    cfg = _partition_config(rec, role) if rec is not None else None
    if cfg is None or not isinstance(cfg.get("years"), list):
        return None
    return sorted(int(y) for y in cfg["years"])


def shard_config_identity(key: str) -> str | None:
    """Return the run whose CONFIGURATION the shard designates for ``key``.

    The schema-v3 identity (:data:`REQUIRED_PARTITION_V3_KEYS`), read live:
    ``config_partition.configs[].source_run_id`` when the role's config came
    from an earlier run (ERCOT's consolidation kept both), else the role's own
    ``run_id``. None for a key that resolves to no partition config.

    Why it is not simply ``live_keeper``: after the ercot-248 consolidation
    BOTH ERCOT roles designate the one composed ``run_id``, so ``live_keeper``
    returns the same string for both and cannot distinguish a golden of the
    forward config from a golden of the carve-out. This can.
    """
    iso, role = resolve_role(key)
    if role is None:
        return None
    rec = _load_shard(iso)
    cfg = _partition_config(rec, role) if rec is not None else None
    if cfg is None:
        return None
    ident = cfg.get("source_run_id") or cfg.get("run_id")
    return str(ident) if ident else None


def live_state(key: str, entry: dict) -> tuple[str, str]:
    """Return ``(state, detail)`` for one entry against the live keeper shards.

    ``state`` is ``"CURRENT"`` or ``"STALE"``; ``detail`` is the parenthetical
    that explains a STALE reading (empty when CURRENT). Extracted so
    :func:`check_manifest` and :func:`config_coverage` cannot drift into two
    answers for one question. A retired capture key never reaches here —
    :func:`check_manifest` reports those as historical records instead.

    Two things make an entry stale: the shard designates a different RUN, or
    (schema v3) it designates the same run but a different CONFIG. The second
    only became possible when the ercot-248 consolidation composed several
    roles onto one run id; an entry that stamped its ``config_id`` can be
    judged on it, and one that did not (every v2 entry) is judged on the run
    id alone, exactly as before.
    """
    keeper_id = entry.get("keeper_id")
    part = entry.get("partition")
    current = live_keeper(key)
    state = "CURRENT" if current == keeper_id else "STALE"
    stamped = part.get("config_id") if isinstance(part, dict) else None
    live_ident = shard_config_identity(key)
    if state == "CURRENT" and stamped and live_ident and stamped != live_ident:
        return "STALE", (
            f" (run {keeper_id} is still designated, but its "
            f"{resolve_role(key)[1]!r} config is now {live_ident}; this golden "
            f"captured {stamped})"
        )
    if state == "CURRENT":
        return state, ""
    if current is None and PARTITION_KEY_SEP in key:
        # Distinguish "the shard no longer designates this role" from an
        # ordinary supersession — otherwise a typo'd or retired role reads
        # identically to a golden that simply aged.
        _iso, _, _role = key.partition(PARTITION_KEY_SEP)
        return state, (
            f" (keepers/{_iso.upper()}.json designates no config_partition "
            f"role {_role!r})"
        )
    return state, f" (live keeper: {current})"


def config_coverage(rel: str, keepers: dict) -> list[str]:
    """Report per-config golden coverage for each partitioned ISO in a manifest.

    A bare ``golden CURRENT`` line reports the ISO's FORWARD config and says
    nothing about the rest of its partition, so a manifest covering one of
    ERCOT's two configs reads exactly like full coverage. One line per
    partitioned ISO states every config the shard designates as
    ``CURRENT`` / ``STALE`` / ``UNCOVERED`` with its reason — ERCOT reads
    *"forward CURRENT …; carveout-2023 UNCOVERED …"*.

    ``UNCOVERED`` covers three distinct situations, named in the reason so they
    are never conflated: no entry at all; only entries under a capture key
    RETIRED by ruling (a historical record, deliberately not compared); or a
    role whose capture key is retired outright. The ERCOT carve-out is the
    third-plus-second case — uncovered BY RULING (R-AW), not by oversight.

    Returns:
        Report lines (possibly empty). This is a REPORT, never a failure: a
        gate cannot demand a capture the owner retired, and coverage is not an
        invariant of the manifest but of the capture programme.
    """
    lines: list[str] = []
    for iso in sorted({resolve_role(k)[0] for k in keepers}):
        rec = _load_shard(iso)
        cfgs = [
            c
            for c in ((rec or {}).get("config_partition") or {}).get("configs") or []
            if isinstance(c, dict) and c.get("role")
        ]
        if len(cfgs) < 2:
            continue  # a one-config ISO has no coverage question to answer
        parts: list[str] = []
        for cfg in cfgs:
            role = str(cfg["role"])
            keys = sorted(
                k
                for k in keepers
                if resolve_role(k)[0] == iso
                and (resolve_role(k)[1] or "").lower() == role.lower()
            )
            live = [k for k in keys if k not in RETIRED_CAPTURE_KEYS]
            if live:
                key = live[0]
                state, detail = live_state(key, keepers[key])
                parts.append(f"{role} {state} [{key}]{detail}")
                continue
            retired_key = f"{iso}{PARTITION_KEY_SEP}{role}"
            ruling = RETIRED_CAPTURE_KEYS.get(retired_key, "").split(" ", 1)[0]
            if keys:
                why = (
                    f"only the RETIRED capture key {keys[0]} ({ruling}) — a "
                    f"historical capture record, not compared to the live shard"
                )
            elif ruling:
                why = f"capture key {retired_key} RETIRED ({ruling}); no entry"
            else:
                why = "no entry in this manifest"
            parts.append(f"{role} UNCOVERED ({why})")
        lines.append(f"{rel} ({iso}{COVERAGE_MARK}" + "; ".join(parts))
    return lines


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
    elif version > MAX_SCHEMA_VERSION:
        fails.append(
            f"{rel}: schema_version is {version!r} but this gate reads at most "
            f"{MAX_SCHEMA_VERSION} — a manifest written by a newer capture tool "
            f"must not be validated against fields this gate cannot see."
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

        # Rule 22, recorded on the entry itself: a capture that sliced the
        # replayed run to a designated span records the run's registered span
        # alongside, and the slice can only ever be a subset of it.
        years = entry.get("years")
        registered = entry.get("registered_years")
        if registered is not None:
            if not isinstance(registered, list) or not isinstance(years, list):
                fails.append(f"{where}: registered_years / years must both be lists")
            elif not set(years) <= set(registered):
                fails.append(
                    f"{where}: years {years} is not a subset of registered_years "
                    f"{registered} — a designated span is never a superset of "
                    f"the run's registered span (rule 22)"
                )

        # Schema v3: a partition entry says WHICH CONFIG it captured, in its
        # own bytes. Optional at v2 (every committed v2 entry predates it) and
        # required at v3 — the ratchet, applied to the block's contents and to
        # its presence on a partition-keyed entry alike.
        part = entry.get("partition")
        v3 = isinstance(version, int) and version >= PARTITION_IDENTITY_SCHEMA_VERSION
        if part is not None and not isinstance(part, dict):
            fails.append(f"{where}: 'partition' must be an object, got {type(part)}")
        elif isinstance(part, dict):
            _iso, _role = resolve_role(key)
            if part.get("iso") not in (None, _iso):
                fails.append(
                    f"{where}: partition.iso {part.get('iso')!r} != the key's ISO "
                    f"{_iso!r}"
                )
            if (
                PARTITION_KEY_SEP in key
                and part.get("role") != key.partition(PARTITION_KEY_SEP)[2]
            ):
                fails.append(
                    f"{where}: partition.role {part.get('role')!r} does not match "
                    f"the role in the key"
                )
            if v3:
                for req in REQUIRED_PARTITION_V3_KEYS:
                    if req not in part:
                        fails.append(
                            f"{where}: schema v{version} partition block missing "
                            f"{req!r} — a composed keeper's run id does not "
                            f"identify a config, so the entry must name it "
                            f"(config_id)"
                        )
                if not part.get("designated_years"):
                    fails.append(f"{where}: partition.designated_years is empty")
        elif v3 and PARTITION_KEY_SEP in key:
            fails.append(
                f"{where}: schema v{version} requires a 'partition' block on a "
                f"config-partition entry — without it the entry names a role "
                f"but not the config the role stood for"
            )

        # --- A RETIRED capture key (owner ruling): a historical record. Every
        #     v2 invariant above still applied; the live-shard comparison does
        #     not, because the ruling retired the CAPTURE, not the record of
        #     what was captured. Reported, never compared. ---
        if key in RETIRED_CAPTURE_KEYS:
            marked = isinstance(entry.get("retired"), dict)
            notes.append(
                f"{where}: {keeper_id} — provenance run "
                f"{'PRUNED from registry' if pruned else 'registered'}, "
                f"capture key RETIRED ({RETIRED_CAPTURE_KEYS[key].split(' ', 1)[0]}"
                f"; historical capture record, not compared to the live shard"
                f"{'' if marked else '; entry carries no retired block'})"
            )
            continue

        # --- The visible coupling. Reported, never failed. ---
        state, detail = live_state(key, entry)
        if state == "CURRENT":
            # R-AW: a CURRENT golden of a partitioned config replays exactly
            # the span the shard designates to that config — for the bare key,
            # the forward role's. The composed run's registered span is wider
            # (it carries the carve-out year under the carve-out config), so a
            # whole-span replay of the forward config would be a golden of a
            # config the keeper does not designate for that year. HARD.
            span = designated_years(key)
            if span is not None and sorted(int(y) for y in (years or [])) != span:
                _iso, _role = resolve_role(key)
                fails.append(
                    f"{where}: golden is CURRENT but replays years {years}; the "
                    f"shard designates {span} to keepers/{_iso}.json role "
                    f"{_role!r} — a partitioned config's golden replays exactly "
                    f"its designated span (R-AW)"
                )
        notes.append(
            f"{where}: {keeper_id} — provenance run "
            f"{'PRUNED from registry' if pruned else 'registered'}, "
            f"golden {state}{detail}"
        )

    notes += config_coverage(str(rel), keepers)
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

    # Coverage lines are a report about the capture PROGRAMME, not entry
    # findings — split off before any tally so they move no count.
    coverage_notes = [n for n in all_notes if COVERAGE_MARK in n]
    entry_notes = [n for n in all_notes if COVERAGE_MARK not in n]
    legacy_notes = [n for n in entry_notes if "LEGACY v1" in n]
    live_notes = [n for n in entry_notes if "LEGACY v1" not in n]

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

    for note in coverage_notes:
        print(f"  {note}")

    pruned = sum(1 for n in live_notes if "PRUNED" in n)
    stale = sum(1 for n in live_notes if "golden STALE" in n)
    retired = sum(1 for n in live_notes if "capture key RETIRED" in n)
    print(
        f"golden-manifest: {len(paths)} manifest(s), {len(entry_notes)} entr(ies) "
        f"({len(live_notes)} enforced / {len(legacy_notes)} legacy); of the "
        f"enforced, {pruned} with a pruned provenance run, {stale} stale vs the "
        f"live keeper, {retired} under a retired capture key (historical, not "
        f"compared)"
    )
    if coverage_notes:
        uncovered = sum(n.count("UNCOVERED") for n in coverage_notes)
        print(
            f"  partition coverage: {len(coverage_notes)} partitioned-ISO "
            f"report(s), {uncovered} designated config(s) UNCOVERED — reported, "
            f"never failed (the ERCOT carve-out is uncovered BY RULING: R-AW "
            f"retired its capture key, so the gate must not demand it)"
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
