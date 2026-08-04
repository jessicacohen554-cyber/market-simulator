"""FFR-3M probes around the FF-3E part-c kill-resume drill.

Two diagnostic cells, both NEISO 2026-2028 (the drill's own T0 window):

* ``drill``   — the pre-specified drill, optionally with
  ``forecast_xyear_warmstart`` forced off, to test whether the cross-year
  warm start is the cause.
* ``control`` — two INDEPENDENT full-window runs in separate cache roots, no
  kill at all. This is the experiment the drill cannot do: if two fresh runs of
  the same config already disagree, the resume path is not implicated and the
  divergence is plain solver nondeterminism.

Diagnostic only: nothing here is registered, and no model parameter is changed
in response to any score.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve()
sys.path.insert(0, "/home/user/market-simulator")

import scripts.ff_readiness_battery as B  # noqa: E402


_ORIG_GOLDEN = B.golden_posture_config


def _no_xyear_config(iso, start_year, end_year):
    """golden_posture_config with the cross-year warm start disarmed.

    Binds the ORIGINAL up front: this replaces the module attribute, so
    calling it through ``B.`` would recurse into itself.
    """
    cfg = _ORIG_GOLDEN(iso, start_year, end_year)
    return dataclasses.replace(cfg, forecast_xyear_warmstart=False)


def run_control(iso: str, start: int, end: int, work_dir: Path) -> dict:
    """Solve the SAME config twice in two cache roots; compare signatures."""
    from market_sim.pipeline.api import run_scenario
    from market_sim.results import cache as cachemod

    work_dir.mkdir(parents=True, exist_ok=True)
    orig_root = cachemod.CACHE_ROOT
    sigs = {}
    keys = {}
    try:
        for leg in ("a", "b"):
            root = work_dir / f"control_{leg}"
            cachemod.CACHE_ROOT = root
            key = run_scenario(B.golden_posture_config(iso, start, end), iso)
            keys[leg] = key
            sigs[leg] = B._bundle_signature(root / iso / key)
    finally:
        cachemod.CACHE_ROOT = orig_root

    years = sorted(set(sigs["a"]) | set(sigs["b"]))
    per_year = [
        {
            "year": y,
            "equal": sigs["a"].get(y) == sigs["b"].get(y),
            "a": sigs["a"].get(y),
            "b": sigs["b"].get(y),
        }
        for y in years
    ]
    return {
        "instrument": "control-vs-control",
        "iso": iso,
        "window": [start, end],
        "cache_key_match": keys["a"] == keys["b"],
        "identical": all(r["equal"] for r in per_year),
        "per_year": per_year,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cell", choices=("drill", "drill-noxyear", "control"))
    ap.add_argument("--iso", default="NEISO")
    ap.add_argument("--start-year", type=int, default=2026)
    ap.add_argument("--end-year", type=int, default=2028)
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    if args.cell == "control":
        rep = run_control(args.iso, args.start_year, args.end_year, args.work_dir)
    else:
        if args.cell == "drill-noxyear":
            B.golden_posture_config = _no_xyear_config
        rep = B.kill_resume_drill(
            args.iso, args.start_year, args.end_year, args.work_dir
        )
        rep["cell"] = args.cell

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
