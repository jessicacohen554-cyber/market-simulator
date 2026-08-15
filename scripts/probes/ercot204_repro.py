"""ERCOT-204 G-REPRO: byte-identity of the rule-26 re-solve against the keeper.

The precommit's PRIMARY gate and its whole deliverable in one measurement. Part
B deletes ``ercot_faststart_pool_plant_physics`` and the pre-repair row-grain
branch it selected, making the plant-grain rule-18 gate unconditional. The
keeper already ran with that flag ARMED, so removing the flag removes only the
dead branch and the re-solve must reproduce the keeper **byte for byte**.

Compares the sha256 of all 12 committed hourly sidecars (``class_hourly``,
``system``, ``storage``, ``reserve_family`` x 2023/2024/2025). Read-only:
solves nothing.

P-1 falsifier (precommit §2.3): ANY sidecar differing means the deletion was
not behaviour-preserving -- the retained pre-repair branch was reachable on the
keeper's own armed path. That is a finding about the keeper, reported
unrewritten; the deletion is NOT adjusted until it matches.

Usage::

    python scripts/probes/ercot204_repro.py \
        --keeper results/calibration/ercot202_plantphysics_B \
        --resolve results/calibration/ercot204_rule26_delete
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
YEARS = (2023, 2024, 2025)
SIDECARS = ("class_hourly", "system", "storage", "reserve_family")


def _sha256(path: Path) -> str:
    """Stream a file's sha256 (the sidecars are hundreds of MB)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keeper", required=True)
    ap.add_argument("--resolve", required=True)
    ap.add_argument(
        "--out", default="results/calibration/ercot204_repro.json"
    )
    args = ap.parse_args()

    keeper, resolve = Path(args.keeper), Path(args.resolve)
    rows, identical, missing = [], 0, 0
    for year in YEARS:
        for name in SIDECARS:
            rel = f"hourly/{name}_{year}.parquet"
            a, b = keeper / rel, resolve / rel
            if not a.exists() or not b.exists():
                rows.append(
                    {
                        "sidecar": rel,
                        "match": None,
                        "note": (
                            f"missing: keeper={a.exists()} resolve={b.exists()}"
                        ),
                    }
                )
                missing += 1
                continue
            ha, hb = _sha256(a), _sha256(b)
            same = ha == hb
            identical += int(same)
            rows.append(
                {
                    "sidecar": rel,
                    "match": same,
                    "keeper_sha256": ha,
                    "resolve_sha256": hb,
                    "keeper_bytes": a.stat().st_size,
                    "resolve_bytes": b.stat().st_size,
                }
            )

    n = len(YEARS) * len(SIDECARS)
    verdict = "PASS" if identical == n else "FAIL"
    out = {
        "gate": "G-REPRO (PRIMARY)",
        "precommit": (
            "docs/PRECOMMIT-ercot204-rtorpa-gate-and-rule26-successor-"
            "2026-08-15.md Part B, prediction P-1"
        ),
        "keeper_bundle": str(keeper),
        "resolve_bundle": str(resolve),
        "sidecars_compared": n,
        "sidecars_identical": identical,
        "sidecars_missing": missing,
        "verdict": verdict,
        "rows": rows,
    }
    path = REPO / args.out
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path.relative_to(REPO)}")
    print(f"G-REPRO {verdict}: {identical}/{n} sidecars byte-identical")
    for r in rows:
        if r["match"] is not True:
            print(f"  DIFFERS/MISSING: {r['sidecar']} {r.get('note','')}")


if __name__ == "__main__":
    main()
