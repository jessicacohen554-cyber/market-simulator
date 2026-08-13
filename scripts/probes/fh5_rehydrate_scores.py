#!/usr/bin/env python
"""FH-5 — rebuild the horizon table's INPUT tree from committed sidecars.

``scripts/probes/fh5_horizon_table.py`` globs
``results/hindcast/<run_id>/*/*/crossover_score.json``. That path is a SOLVE
artifact: ``results/`` is gitignored and dies with its container, so in any
fresh container the probe finds only the arms that container happened to solve
and silently renders every other cell as an em dash. The FH-5 §4 table was
therefore reproducible exactly once, in the container that produced it.

It need not be. Every registered arm's sidecar
(``frontend/data/hindcast/<run_id>.json``) is COMMITTED, and its ``score`` block
**is** that arm's ``crossover_score.json`` document verbatim — the registrar
stores the scorer's output unmodified. This script writes those committed score
documents back into the directory shape the probe globs, so the probe runs
**verbatim, on the same numbers, in any container**.

**This re-derives nothing** (rules 1 / 13 [R-MEASURED]). It computes no metric,
reads no parquet, runs no solve and touches no bundle. It is a pure
copy of committed bytes into a different path. Verified against the landed
table: rehydrating the 23 sidecars registered before CAISO Arm K and running the
probe reproduces FH-5 §4.1's 13 dominance rows cell-for-cell.

By default it writes OUTSIDE the repo, because ``crossover_score.json`` is NOT
covered by ``.gitignore``'s hindcast rules — rehydrating in place would create
committable duplicates of the sidecars.

Usage::

    python scripts/probes/fh5_rehydrate_scores.py --out /tmp/fh5tableroot
    cd /tmp/fh5tableroot && python <repo>/scripts/probes/fh5_horizon_table.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

#: Committed registration sidecars — the hindcast namespace (rule 15).
SIDECAR_DIR = Path("frontend/data/hindcast")
#: The path shape ``fh5_horizon_table.find_score`` globs.
BUNDLE_ROOT = Path("results/hindcast")


def rehydrate(sidecar_dir: Path, out_root: Path, pattern: str) -> list[str]:
    """Write each sidecar's committed ``score`` block to its bundle path.

    Args:
        sidecar_dir: Directory of committed registration sidecars.
        out_root: Root to write under; the tree lands at
            ``<out_root>/results/hindcast/<run_id>/<iso>/<cache_key>/``.
        pattern: Glob selecting which sidecars to rehydrate.

    Returns:
        The run ids written, sorted.
    """
    written: list[str] = []
    for path in sorted(sidecar_dir.glob(pattern)):
        doc = json.loads(path.read_text())
        score = doc.get("score")
        meta = doc.get("meta") or {}
        iso, key = meta.get("iso"), meta.get("cache_key")
        if not score or not iso or not key:
            # A sidecar with no score (or no ledger path) is skipped rather
            # than defaulted — a fabricated zero is worse than a missing cell.
            continue
        # The RUNTIME key is the key of record and is read from the sidecar,
        # never reconstructed from the config (the D-13 hazard).
        target = out_root / BUNDLE_ROOT / doc["run_id"] / iso / key
        target.mkdir(parents=True, exist_ok=True)
        (target / "crossover_score.json").write_text(json.dumps(score, indent=2))
        written.append(doc["run_id"])
    return written


def main(argv: "list[str] | None" = None) -> int:
    """Rehydrate committed scores into a probe-readable tree.

    Args:
        argv: Command-line arguments, or ``None`` for ``sys.argv``.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Root to write the rehydrated tree under (keep it OUTSIDE the repo).",
    )
    parser.add_argument(
        "--sidecar-dir", type=Path, default=SIDECAR_DIR, help="Committed sidecars."
    )
    parser.add_argument(
        "--pattern",
        default="*t1ff*.json",
        help="Which sidecars to rehydrate (default: every T1-FF arm).",
    )
    args = parser.parse_args(argv)

    ids = rehydrate(args.sidecar_dir, args.out, args.pattern)
    for run_id in ids:
        print(f"[rehydrate] {run_id}")
    print(f"[rehydrate] {len(ids)} arms -> {args.out / BUNDLE_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
