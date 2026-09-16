#!/usr/bin/env python3
"""Confirm a registration moved NO benchmark (actual) value — the miso-257 lesson.

`dashboard_add_run.py` re-renders `frontend/data/backcast/bench/<ISO>/<year>.json.gz`
for every year the registered run covers, and a bench part is the ACTUAL side of
C1/C2/C4. miso-257 found a broken bench part that moved C1 by 19 TWh and read
exactly like a model result. So before any registration is committed, the newly
written parts are diffed against the committed ones and the actual side must not
move.

Run AFTER `dashboard_add_run.py` and BEFORE `git commit`:

    python scripts/probes/_miso260_bench_parity.py --iso MISO --base origin/main
"""

from __future__ import annotations

import argparse
import gzip
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _load_blob(ref: str, rel: str) -> dict | None:
    got = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        capture_output=True, cwd=REPO, check=False,
    )
    if got.returncode != 0 or not got.stdout:
        return None
    return json.loads(gzip.decompress(got.stdout))


def _class_totals(part: dict) -> dict[str, float]:
    """Per-class actual grid-delivered TWh — the number C1 scores against."""
    cf = (part.get("bench") or {}).get("classFull") or {}
    return {str(k): float(v) for k, v in cf.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--tol", type=float, default=1e-6, help="TWh")
    args = ap.parse_args()

    root = REPO / "frontend" / "data" / "backcast" / "bench" / args.iso
    if not root.is_dir():
        print(f"no bench dir for {args.iso}")
        return 1
    worst = 0.0
    n_years = 0
    failures: list[str] = []
    for path in sorted(root.glob("*.json.gz")):
        rel = path.relative_to(REPO).as_posix()
        base = _load_blob(args.base, rel)
        if base is None:
            print(f"  {path.name}: NEW part (no {args.base} blob) — nothing to compare")
            continue
        head = json.loads(gzip.decompress(path.read_bytes()))
        b, h = _class_totals(base), _class_totals(head)
        n_years += 1
        keys = sorted(set(b) | set(h))
        moves = {k: h.get(k, 0.0) - b.get(k, 0.0) for k in keys}
        mx = max((abs(v) for v in moves.values()), default=0.0)
        worst = max(worst, mx)
        flag = "OK " if mx <= args.tol else "MOVED"
        print(f"  {path.name}: {flag} max |d actual class TWh| = {mx:.6f}")
        if mx > args.tol:
            for k, v in sorted(moves.items(), key=lambda kv: -abs(kv[1]))[:6]:
                if abs(v) > args.tol:
                    print(f"      {k}: {b.get(k, 0.0):.4f} -> {h.get(k, 0.0):.4f} ({v:+.4f})")
            failures.append(path.name)
    print(
        f"\n{args.iso}: {n_years} part(s) compared against {args.base}; "
        f"max |d| = {worst:.6f} TWh"
    )
    if failures:
        print(
            "BENCH MOVED — do NOT commit this registration until the move is explained. "
            "A moving actual side reads exactly like a model result (the miso-257 lesson)."
        )
        return 1
    print("bench parity OK — the actual side did not move.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
