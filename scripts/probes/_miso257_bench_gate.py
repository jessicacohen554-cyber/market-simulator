#!/usr/bin/env python3
"""Regenerate MISO's committed bench parts at zero LP, behind a hard gate.

miso-257, following ``docs/RESULT-pjm-h4-bench-move-landed-2026-09-13.md`` §2.1.
``_miso257_bench_rebuild.py`` reconstructs the three gitignored solve artifacts
a SLIM bundle is missing; this script then runs the real payload builder and
writes the resulting bench parts through the real writer — but ONLY if the
reconstruction provably reproduced the dispatch-scoped half of the part.

THE GATE. The rebuilt part's plant key set and every dispatch-scoped field
(``name / zone / group / npl / nodata / campd / c_ann / c_mon``) must come back
byte-identical to the committed part. Identity there proves the reconstructed
dispatch reproduced ``classes_p`` / ``zone_p`` exactly, so anything that then
moves in ``classFull`` / ``e930`` / ``avgLMP`` is the benchmark builder and
nothing else. A mismatch ABORTS and writes nothing.

``runs/<id>.js`` is deliberately NOT rewritten: the model side of the payload
is built from the synthetic zero-MW dispatch and is meaningless. Only the
bench part is a pure function of the benchmark frames plus the plant map.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"

#: Fields of a bench-part ``plants`` record that the reconstructed dispatch
#: determines (directly, or through the class/zone map the measured series is
#: split on). Identity across all of them is the admissibility gate.
DISPATCH_SCOPED = ("name", "zone", "group", "npl", "nodata", "campd", "c_ann", "c_mon")


def _gate(iso: str, year: int, new_bench: dict) -> tuple[bool, list[str]]:
    """Return (ok, notes) for one year's rebuilt bench payload."""
    old = ba.load_bench_part(BENCH / iso / f"{year}.json.gz")["bench"]
    op, np_ = old.get("plants", {}), new_bench.get("plants", {})
    notes: list[str] = []
    if set(op) != set(np_):
        miss, extra = sorted(set(op) - set(np_)), sorted(set(np_) - set(op))
        notes.append(f"plant key set MOVED: -{len(miss)} +{len(extra)} {miss[:6]} {extra[:6]}")
        return False, notes
    moved = []
    for key in sorted(op):
        for f in DISPATCH_SCOPED:
            if op[key].get(f) != np_[key].get(f):
                moved.append(f"{key}.{f}")
    if moved:
        notes.append(f"{len(moved)} dispatch-scoped field(s) MOVED: {moved[:10]}")
        return False, notes
    notes.append(f"{len(op)} plants — key set + dispatch-scoped fields IDENTICAL")
    return True, notes


def _deltas(iso: str, year: int, new_bench: dict) -> list[str]:
    """Human-readable report of what DID move in the non-dispatch half."""
    old = ba.load_bench_part(BENCH / iso / f"{year}.json.gz")["bench"]
    out: list[str] = []
    for block in ("classFull", "e930"):
        a, b = old.get(block) or {}, new_bench.get(block) or {}
        for k in sorted(set(a) | set(b)):
            va, vb = a.get(k), b.get(k)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                if abs(va - vb) > 1e-9:
                    out.append(f"  {block}.{k}: {va:.4f} -> {vb:.4f} ({vb - va:+.4f})")
            elif va != vb:
                out.append(f"  {block}.{k}: {va!r} -> {vb!r}")
    a, b = old.get("avgLMP") or {}, new_bench.get("avgLMP") or {}
    for k in sorted(set(a) | set(b)):
        if isinstance(a.get(k), (int, float)) and isinstance(b.get(k), (int, float)):
            if abs(a[k] - b[k]) > 1e-9:
                out.append(f"  avgLMP.{k}: {a[k]:.4f} -> {b[k]:.4f}")
    e_a, e_b = json.dumps(old.get("plants"), sort_keys=True), json.dumps(
        new_bench.get("plants"), sort_keys=True
    )
    if e_a != e_b:
        out.append("  plants: NON-dispatch-scoped field(s) moved (e923 side)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--label", default="miso 257 bench rebuild")
    ap.add_argument("--write", action="store_true", help="write the parts (gate must pass)")
    ap.add_argument("--dump", type=Path, default=None, help="also dump the rebuilt bench blocks as JSON")
    args = ap.parse_args()
    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle

    import scripts.render_calibration_html as rch

    iso = json.loads((bundle / "meta.json").read_text())["iso"]
    D = rch.build_payload([(args.label, bundle)])
    part_meta = {
        "groups": D["groups"],
        "groupLabel": D["groupLabel"],
        "zones": D["zones"],
        "years": D["years"],
    }

    if args.dump:
        args.dump.write_text(json.dumps({str(k): v for k, v in D["bench"].items()}, indent=1))
        print(f"dumped rebuilt bench blocks to {args.dump}")

    ok_all = True
    for year, bench_year in sorted(D["bench"].items(), key=lambda kv: int(kv[0])):
        year = int(year)
        ok, notes = _gate(iso, year, bench_year)
        ok_all &= ok
        print(f"[{'PASS' if ok else 'FAIL'}] {iso} {year}: " + "; ".join(notes))
        for line in _deltas(iso, year, bench_year):
            print(line)

    if not ok_all:
        print("\nGATE FAILED — nothing written.", file=sys.stderr)
        return 1
    print("\nGATE PASSED in every year.")
    if not args.write:
        print("(dry run — pass --write to commit the parts to disk)")
        return 0
    for year, bench_year in sorted(D["bench"].items(), key=lambda kv: int(kv[0])):
        out = ba.write_bench_part(BENCH, iso, int(year), part_meta, bench_year)
        print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
