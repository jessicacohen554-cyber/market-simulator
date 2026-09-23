#!/usr/bin/env python3
"""miso-267: what the benchmark-builder repair does to EVERY ISO (rule 25), ZERO LP.

The repair (``docs/FINDING-miso267-the-oil-reattribution-was-one-sided-2026-09-23.md``)
is in the shared bench path, so it reaches every ISO's parts at that ISO's next
registration. nyiso-240 set the precedent this follows: measure each ISO's
exposure and re-score each registered run against a repaired copy of its own
bench BEFORE landing, and refresh no other ISO's parts.

FOR EACH registered run, its bundle's benchmark frames are rebuilt ONCE through
the real single builder (``run_calibration_full.build_benchmark_frames``) with
``_benchmark_eia923_frame`` wrapped so the PRE-repair builder (``--old``, the
module as it stood at ``origin/main``) runs on the identical inputs — same
generation table, CAMPD frame, EIA-930 frame, fleet map and flags. The two EIA-923
frames are rolled to classes exactly as ``render_calibration_html.build_payload``
does (``apply_other_fossil_scoring``, minus the part's own ``btmClass``, the
EIA-930 VRE override, then ``reconcile_vintage_classes`` against the part's own
``e930``), so ``delta`` is the repair's own classFull increment, isolated from
every other difference between a committed part and HEAD.

THE CANDIDATE BENCH (``--bench-out``): each committed part with ``delta`` added to
its ``classFull`` and nothing else changed, so ``_miso267_rescore.py`` can score
every registered run against it. It is a census instrument, never a part to
commit: a real refresh is the owning ISO lane's (``--rebuild-benchmark`` then
``dashboard_add_run.py``).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"
REGISTRY = REPO / "frontend" / "data" / "backcast" / "registry"


def _load_old(path: Path):
    spec = importlib.util.spec_from_file_location("rcf_pre_miso267", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _class_full(e923, year: int, part: dict, iso: str) -> dict[str, float]:
    """Roll an EIA-923 benchmark frame to ``classFull`` the way the payload does."""
    import scripts.render_calibration_html as rch
    from market_sim.data.fleet import apply_other_fossil_scoring

    e = apply_other_fossil_scoring(
        e923[e923["year"] == year], year, plant_col="plant_id"
    )
    cls = e.groupby("klass")["annual_mwh"].sum()
    btm = part.get("btmClass") or {}
    cf = {
        str(g): round(float(v) / 1e6 - float(btm.get(str(g), 0.0)), 4)
        for g, v in cls.items()
    }
    e930 = dict(part.get("e930") or {})
    for vre in ("wind", "solar"):
        if rch.actuals_source(vre, iso) == rch.EIA930_SOURCE:
            if vre in cf and vre in e930:
                cf[vre] = round(float(e930[vre]), 4)
    rch.reconcile_vintage_classes(cf, e930, iso)
    return cf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--old", type=Path, required=True, help="pre-repair run_calibration_full.py"
    )
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--bench-out", type=Path, required=True)
    ap.add_argument("--iso", nargs="*", help="restrict to these ISOs")
    args = ap.parse_args()
    logging.disable(logging.WARNING)

    import scripts.run_calibration_full as rcf

    old = _load_old(args.old)
    runs = [json.loads(p.read_text()) for p in sorted(REGISTRY.glob("*.json"))]
    report: dict = {}
    for run in runs:
        iso = run["iso"]
        if args.iso and iso not in args.iso:
            continue
        bundle = REPO / run["bundle"]
        captured: dict[int, tuple] = {}
        new_fn = rcf._benchmark_eia923_frame

        def both(year, generation, iso_, campd_year, group_by_code, e930, **kw):
            n = new_fn(year, generation, iso_, campd_year, group_by_code, e930, **kw)
            o = old._benchmark_eia923_frame(
                year, generation, iso_, campd_year, group_by_code, e930, **kw
            )
            captured[int(year)] = (o, n)
            return n

        rcf._benchmark_eia923_frame = both
        try:
            rcf.build_benchmark_frames(bundle)
        finally:
            rcf._benchmark_eia923_frame = new_fn
        for year, (o, n) in sorted(captured.items()):
            part_path = BENCH / iso / f"{year}.json.gz"
            if not part_path.exists():
                continue
            part = ba.load_bench_part(part_path)
            cf_o = _class_full(o, year, part["bench"], iso)
            cf_n = _class_full(n, year, part["bench"], iso)
            delta = {
                g: round(cf_n.get(g, 0.0) - cf_o.get(g, 0.0), 4)
                for g in sorted(set(cf_o) | set(cf_n))
                if abs(cf_n.get(g, 0.0) - cf_o.get(g, 0.0)) >= 1e-4
            }
            committed = part["bench"].get("classFull", {})
            cand = dict(committed)
            for g, d in delta.items():
                if g not in cf_n:
                    # The repaired builder no longer produces this class (the
                    # generic-COAL leak). A real refresh drops the key, so the
                    # candidate drops it too: adding the delta to a part that
                    # never carried the key would invent a NEGATIVE class, and a
                    # non-zero `COAL` entry flips C8's plant-group materiality.
                    cand.pop(g, None)
                    continue
                cand[g] = round(float(cand.get(g, 0.0)) + d, 4)
            report.setdefault(iso, {})[year] = {
                "run": run["id"],
                "delta": delta,
                "oil": [committed.get("oil"), cand.get("oil")],
                "negative_after": {g: v for g, v in cand.items() if v < 0},
            }
            b = dict(part["bench"])
            b["classFull"] = cand
            ba.write_bench_part(args.bench_out, iso, year, part["meta"], b)
            big = {g: d for g, d in delta.items() if abs(d) >= 0.01}
            print(
                f"{iso} {year} ({run['id']}): max|d| {max([abs(v) for v in delta.values()] or [0]):.4f} TWh; >=0.01: {big}"
            )
    args.out.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
