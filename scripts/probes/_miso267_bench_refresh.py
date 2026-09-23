#!/usr/bin/env python3
"""miso-267 STEP 1: regenerate MISO's bench parts ONCE, behind a corrected gate.

The builder the parts are regenerated with is the repaired one
(``docs/FINDING-miso267-the-oil-reattribution-was-one-sided-2026-09-23.md``):
nyiso-240's two boundary repairs, with the dual-fuel oil re-attribution made
two-sided, supply-classed and run FIRST. Everything that moves is attributed,
field by field, by ``scripts/probes/_miso267_bench_move_decomposition.py``.

THE CONTROL is the same as that probe's: a slim bundle whose dispatch was
reconstructed by ``scripts/probes/_miso257_bench_rebuild.py`` from the
COMMITTED part's own plant keys, so the plant -> class map cannot move.

THE GATE, CORRECTED. ``_miso257_bench_gate.py`` requires ``campd / c_ann /
c_mon / nodata`` to be byte-identical as "dispatch-scoped". That is true of a
single-class plant and FALSE of a multi-class plant whose facility CEMS series
is split across its classes by EIA-923 monthly shares (``split == "e923_monthly"``
— ``render_calibration_html.build_payload`` -> ``bench_multiclass.
split_measured_series``): there those fields are a function of the 923 frame
too, so any frame repair that touches the plant's 923 rows moves them (it is
exactly what failed miso-266's gate on plants 1393 and 1743). This gate keeps
the old condition everywhere else and, for those slices, requires the thing the
split must conserve — the plant's CEMS total, summed over its slices — to be
identical to 1e-4 TWh (the payload's own rounding). Plant key set and
``name / zone / group / npl`` stay byte-identical everywhere.

Default is a DRY RUN into ``--out-bench`` (a scratch bench root); ``--write``
writes the real ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` parts
through the real writer, and only when the gate passes in every year.
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
IDENTITY = ("name", "zone", "group", "npl")
SPLIT_FIELDS = ("nodata", "campd", "c_ann", "c_mon")
#: ``c_ann`` is rounded to 4 decimals (TWh) in the payload, so a conserved
#: facility total can differ by at most one rounding step per slice.
C_ANN_TOL = 1e-4


def gate_year(committed: dict, rebuilt: dict) -> tuple[bool, list[str]]:
    """Return ``(ok, notes)`` for one year under the corrected gate."""
    op, np_ = committed.get("plants", {}), rebuilt.get("plants", {})
    notes: list[str] = []
    if set(op) != set(np_):
        miss, extra = sorted(set(op) - set(np_)), sorted(set(np_) - set(op))
        return False, [f"plant key set MOVED: -{miss[:6]} +{extra[:6]}"]
    bad: list[str] = []
    split_codes: dict[str, list[str]] = {}
    for key in sorted(op):
        for f in IDENTITY:
            if op[key].get(f) != np_[key].get(f):
                bad.append(f"{key}.{f}")
        moved = [f for f in SPLIT_FIELDS if op[key].get(f) != np_[key].get(f)]
        if not moved:
            continue
        if np_[key].get("split") == "e923_monthly" and ":" in key:
            split_codes.setdefault(key.split(":")[0], []).append(key)
        else:
            bad.extend(f"{key}.{f}" for f in moved)
    for code, keys in sorted(split_codes.items()):
        slices = [k for k in op if k.split(":")[0] == code]
        a = sum(float(op[k]["c_ann"]) for k in slices)
        b = sum(float(np_[k]["c_ann"]) for k in slices)
        if abs(a - b) > C_ANN_TOL * len(slices):
            bad.append(
                f"{code}: CEMS facility total {a:.4f} -> {b:.4f} (not conserved)"
            )
        else:
            notes.append(
                f"{code}: split moved across {len(keys)} e923_monthly slice(s), "
                f"CEMS facility total conserved ({a:.4f} -> {b:.4f} TWh)"
            )
    if bad:
        return False, [
            f"{len(bad)} field(s) MOVED outside the frame-dependent split: {bad[:8]}"
        ]
    notes.insert(0, f"{len(op)} plants — key set + identity fields IDENTICAL")
    return True, notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--out-bench", type=Path, help="dry-run bench root (scratch)")
    ap.add_argument("--write", action="store_true", help="write the REAL parts")
    ap.add_argument("--label", default="miso-267 bench refresh")
    args = ap.parse_args()
    if not args.write and not args.out_bench:
        ap.error("pass --out-bench <scratch dir> for a dry run, or --write")
    bundle = args.bundle.resolve()

    import scripts.render_calibration_html as rch

    iso = json.loads((bundle / "meta.json").read_text())["iso"]
    D = rch.build_payload([(args.label, bundle)])

    def part_meta(year: int) -> dict:
        """The committed part's DISPATCH-derived display meta, carried unchanged.

        ``groups`` / ``groupLabel`` / ``zones`` come from the registering run's
        full dispatch class list, which a dispatch reconstructed from the bench
        part's own plant keys cannot reproduce (MISO's generic ``COAL`` dispatch
        class has no benched plant, so it would silently drop out). Nothing this
        refresh changes can move them.
        """
        old = ba.load_bench_part(BENCH / iso / f"{year}.json.gz")["meta"]
        return {k: old[k] for k in ("groups", "groupLabel", "zones")}

    ok_all = True
    for year, rebuilt in sorted(D["bench"].items(), key=lambda kv: int(kv[0])):
        committed = ba.load_bench_part(BENCH / iso / f"{int(year)}.json.gz")["bench"]
        ok, notes = gate_year(committed, rebuilt)
        ok_all &= ok
        print(f"[{'PASS' if ok else 'FAIL'}] {iso} {year}: " + "; ".join(notes))
    if not ok_all:
        print("\nGATE FAILED — nothing written.", file=sys.stderr)
        return 1
    root = BENCH if args.write else args.out_bench
    metas = {int(y): part_meta(int(y)) for y in D["bench"]}
    for year, rebuilt in sorted(D["bench"].items(), key=lambda kv: int(kv[0])):
        out = ba.write_bench_part(root, iso, int(year), metas[int(year)], rebuilt)
        print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
