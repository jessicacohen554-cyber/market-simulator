#!/usr/bin/env python3
"""miso-267 STEP 1: attribute MISO's bench-part move to its builder causes, ZERO LP.

``docs/FINDING-miso266-bench-regeneration-hazard-2026-09-23.md`` measured what
re-registering a MISO run would do to the committed
``frontend/data/backcast/bench/MISO/<year>.json.gz`` parts and could not say WHY:
its gate failed on two plants (1393, 1743) and the table mixed their contribution
with everything else. This probe separates the causes by construction.

THE CONTROL. The bundle is a slim bundle reconstructed by
``scripts/probes/_miso257_bench_rebuild.py``, whose dispatch is read off the
COMMITTED part's own ``plants`` keys — so the plant -> class map is the committed
part's by construction and cannot contribute a single moved number. Anything that
still moves is the benchmark builder.

THE VARIANTS. The benchmark frames are rebuilt in-process at HEAD through the real
single builder (``run_calibration_full.build_benchmark_frames``) with the
nyiso-240 boundary repairs (``03eed7e9c``, 2026-09-19 — after the committed parts
were written at ``408c363a5``, 2026-09-17) individually switched off:

* ``head``      — the builder as it stands;
* ``no_r2``     — ``_reattribute_dual_fuel_oil`` replaced by the identity;
* ``no_r1``     — ``_backfill_eia923_missing_months`` replaced by the identity;
* ``no_r1_r2``  — both.

If ``no_r1_r2`` reproduces the committed parts, the entire move is those two
repairs and nothing else, and each field's owner follows from the single-switch
variants. Each variant's frames go to the bundle-local shared store under their
own content hash; nothing under ``frontend/`` is written.

Usage::

    .venv/bin/python scripts/probes/_miso267_bench_move_decomposition.py <bundle> \
        --out <json>
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib.bundle_io import write_shared_input  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"
#: Per-plant fields whose value can move only through the frames or the class map.
PLANT_FIELDS = (
    "name",
    "zone",
    "group",
    "npl",
    "nodata",
    "campd",
    "c_ann",
    "c_mon",
    "e_ann",
    "e_mon",
)


def _identity_r2(e923, group_by_code, class_shares=None):
    """``_reattribute_dual_fuel_oil`` switched off."""
    return e923


def _identity_r1(e923, campd_year, group_by_code, year, generation, class_shares=None):
    """``_backfill_eia923_missing_months`` switched off."""
    return e923


VARIANTS: dict[str, dict[str, object]] = {
    "head": {},
    "no_r2": {"_reattribute_dual_fuel_oil": _identity_r2},
    "no_r1": {"_backfill_eia923_missing_months": _identity_r1},
    "no_r1_r2": {
        "_reattribute_dual_fuel_oil": _identity_r2,
        "_backfill_eia923_missing_months": _identity_r1,
    },
}


def _clone_bundle(src: Path, dst: Path) -> None:
    """Copy the slim bundle's small files; symlink the large read-only ones."""
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for p in src.iterdir():
        if p.is_dir():
            (dst / p.name).symlink_to(p.resolve(), target_is_directory=True)
        elif p.suffix == ".parquet":
            (dst / p.name).symlink_to(p.resolve())
        else:
            shutil.copy2(p, dst / p.name)


def build_variant(src: Path, name: str, patches: dict[str, object]) -> dict:
    """Rebuild the frames under ``patches`` and return ``build_payload``'s bench."""
    import scripts.render_calibration_html as rch
    import scripts.run_calibration_full as rcf

    dst = src.parent / f"{src.name}__{name}"
    _clone_bundle(src, dst)
    saved = {k: getattr(rcf, k) for k in patches}
    try:
        for k, fn in patches.items():
            setattr(rcf, k, fn)
        iso, frames = rcf.build_benchmark_frames(dst)
    finally:
        for k, fn in saved.items():
            setattr(rcf, k, fn)
    meta = json.loads((dst / "meta.json").read_text())
    for n, f in frames.items():
        meta["shared_inputs"][n] = write_shared_input(f, n, iso, dst)
    (dst / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return {int(y): b for y, b in rch.build_payload([(name, dst)])["bench"].items()}


def diff_year(committed: dict, rebuilt: dict) -> dict:
    """Every moved classFull / e930 entry and every moved per-plant field."""
    out: dict = {"classFull": {}, "e930": {}, "plants": {}, "plant_keys": None}
    for block in ("classFull", "e930"):
        a, b = committed.get(block) or {}, rebuilt.get(block) or {}
        for k in sorted(set(a) | set(b)):
            va, vb = a.get(k), b.get(k)
            if va != vb:
                out[block][k] = [va, vb]
    pa, pb = committed.get("plants") or {}, rebuilt.get("plants") or {}
    if set(pa) != set(pb):
        out["plant_keys"] = {
            "missing": sorted(set(pa) - set(pb)),
            "extra": sorted(set(pb) - set(pa)),
        }
    for key in sorted(set(pa) & set(pb)):
        moved = [f for f in PLANT_FIELDS if pa[key].get(f) != pb[key].get(f)]
        if moved:
            out["plants"][key] = moved
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--variants", nargs="*", default=list(VARIANTS))
    args = ap.parse_args()
    src = args.bundle.resolve()
    iso = json.loads((src / "meta.json").read_text())["iso"]

    report: dict = {"iso": iso, "bundle": str(src), "variants": {}}
    for name in args.variants:
        bench = build_variant(src, name, VARIANTS[name])
        per_year = {}
        for year, rebuilt in sorted(bench.items()):
            committed = ba.load_bench_part(BENCH / iso / f"{year}.json.gz")["bench"]
            d = diff_year(committed, rebuilt)
            per_year[year] = d
            n = len(d["classFull"]) + len(d["e930"]) + len(d["plants"])
            print(
                f"[{name}] {iso} {year}: {len(d['classFull'])} classFull, "
                f"{len(d['e930'])} e930, {len(d['plants'])} plant(s) moved"
                + ("" if n else "  -- REPRODUCES the committed part")
            )
        report["variants"][name] = per_year
    args.out.write_text(json.dumps(report, indent=1, default=str) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
