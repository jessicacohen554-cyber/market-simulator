"""Prune an ISO's dashboard runs down to the keeper + an explicit keep-list.

``dashboard_add_run.prune_iso`` enforces the standing top-15-per-ISO retention
by AGE. This is the different operation: an owner-directed clear-out of a
lane's probe/control runs, keeping only the runs that still carry meaning.

The safety rule this adds, and the reason it is not a plain ``rm``: a run id is
not only a dashboard row, it is a CITATION. The keeper determinations in
``calibration-complete.json`` and the per-ISO ``keepers/<ISO>.json`` shards name
specific runs as the evidence a verdict rests on (superseded bases, zero-delta
controls, promotion comparisons). Deleting those leaves a governance file
asserting a determination against a run that no longer exists. So this script
refuses to prune any run cited by those two governance surfaces unless
``--force-uncite`` is passed, and always PRINTS what it is protecting and why.

Citations in ``mechanism-matrix.js`` are reported but do NOT block: the matrix's
durable evidence is the ``results/calibration/FINDING-*.md`` record, which is
not touched here.

Deletes the registry sidecar, the ``runs/<id>.js`` payload and the mapped
``results/calibration/<bundle>/`` directory together, so the three stores cannot
drift into orphans — the same three-store discipline ``prune_iso`` keeps.

Usage:
    python scripts/prune_iso_runs.py --iso NEISO \
        --keep 2026-08-05-neiso-83-ca1-reclass \
        --keep 2026-08-05-neiso-2022-touchpoint --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DATA = REPO / "frontend" / "data" / "backcast"
REGISTRY = DATA / "registry"
RUNS = DATA / "runs"
CALIB = REPO / "results" / "calibration"

# Governance surfaces whose run-id citations must not be left dangling.
GOVERNANCE_FILES = [
    DATA / "calibration-complete.json",
    DATA / "keepers",  # directory — every <ISO>.json shard
]
# Reported, never blocking (see module docstring). Base + the per-ISO shard
# directory (run-id citations live in the shards' `ev` since 2026-08-11).
ADVISORY_FILES = [
    REPO / "docs" / "codebase-site" / "data" / "mechanism-matrix.js",
    REPO / "docs" / "codebase-site" / "data" / "mechanism-matrix",
]


def _texts(paths: list[Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in paths:
        if p.is_dir():
            # keepers/ holds <ISO>.json shards; mechanism-matrix/ holds
            # <ISO>.js shards — scan both shard shapes.
            for f in sorted(list(p.glob("*.json")) + list(p.glob("*.js"))):
                out[str(f.relative_to(REPO))] = f.read_text()
        elif p.exists():
            out[str(p.relative_to(REPO))] = p.read_text()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument(
        "--keep",
        action="append",
        default=[],
        help="run id to keep (repeatable). The ISO's keeper is always kept.",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--force-uncite",
        action="store_true",
        help="prune even runs cited by a governance file, leaving those "
        "citations dangling. Requires deliberate intent.",
    )
    args = ap.parse_args()

    from scripts.lib import keeper_store

    keepers = set(keeper_store.keeper_list())
    keep = set(args.keep) | keepers

    gov = _texts(GOVERNANCE_FILES)
    adv = _texts(ADVISORY_FILES)

    entries = []
    for path in sorted(REGISTRY.glob("*.json")):
        rec = json.loads(path.read_text())
        if rec.get("iso") != args.iso:
            continue
        entries.append((rec.get("id", path.stem), rec, path))

    kept, pruned, blocked = [], [], []
    for rid, rec, sidecar in entries:
        if rid in keep:
            kept.append(rid)
            continue
        cited_gov = [f for f, t in gov.items() if rid in t]
        if cited_gov and not args.force_uncite:
            blocked.append((rid, cited_gov))
            continue
        pruned.append((rid, rec, sidecar))

    # Bundles still referenced by a surviving sidecar are never deleted.
    pruned_ids = {r for r, _, _ in pruned}
    live_bundles = set()
    for path in REGISTRY.glob("*.json"):
        rec = json.loads(path.read_text())
        if rec.get("id", path.stem) in pruned_ids:
            continue
        if rec.get("bundle"):
            live_bundles.add((REPO / rec["bundle"]).resolve())

    print(f"=== {args.iso}: {len(entries)} registered run(s) ===")
    print(f"KEEP ({len(kept)}):")
    for rid in sorted(kept):
        print(f"  {rid}{'  [KEEPER]' if rid in keepers else ''}")
    if blocked:
        print(f"\nPROTECTED — cited by a governance file ({len(blocked)}):")
        for rid, files in blocked:
            print(f"  {rid}  <- {', '.join(files)}")
        print("  (pass --force-uncite to prune these and dangle the citations)")

    print(f"\nPRUNE ({len(pruned)}):")
    for rid, rec, sidecar in pruned:
        payload = RUNS / f"{rid}.js"
        bundle = (REPO / rec["bundle"]).resolve() if rec.get("bundle") else None
        drop = bundle if (bundle and bundle not in live_bundles) else None
        targets = [t for t in [sidecar, payload, drop] if t and t.exists()]
        note = [f for f, t in adv.items() if rid in t]
        print(
            f"  {rid}: "
            + (
                ", ".join(str(t.relative_to(REPO)) for t in targets)
                or "(nothing on disk)"
            )
            + (
                f"   [also cited in {', '.join(note)} — FINDING docs retained]"
                if note
                else ""
            )
        )
        if args.dry_run:
            continue
        for t in targets:
            shutil.rmtree(t) if t.is_dir() else t.unlink()

    if args.dry_run:
        print("\n[dry-run] nothing deleted")
    else:
        print(f"\npruned {len(pruned)} run(s) for {args.iso}")


if __name__ == "__main__":
    main()
