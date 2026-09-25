"""PJM-NEXT card 1 phase 0 (zero LP): the benchmark membership gap on the R-PJM-2 keeper.

Rebuilds the keeper's EIA-923 benchmark frame twice through the single builder
(``run_calibration_full.build_benchmark_frames``) on scratch copies of its
meta -- ``benchmark_membership_vintage_union`` off (the keeper as registered)
and on -- and reports the per-year, per-class TWh the union ADDS. The union is
additive by construction (SPP-49), so every delta must be >= 0. No LP.

Usage:
    python scripts/probes/_pjmnext_bench_union_phase0.py --scratch <dir> --out <json>
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/rpjm2_span"


def _frame(scratch: Path, union: bool):
    """EIA-923 benchmark frame for the keeper meta with the union flag set."""
    from scripts.run_calibration_full import build_benchmark_frames

    d = scratch / f"union_{int(union)}"
    d.mkdir(parents=True, exist_ok=True)
    meta = json.loads((BUNDLE / "meta.json").read_text())
    meta["benchmark_membership_vintage_union"] = union
    (d / "meta.json").write_text(json.dumps(meta))
    shutil.copy(BUNDLE / "run_config.json", d / "run_config.json")
    if not union:
        rc = json.loads((d / "run_config.json").read_text())
        (d / "run_config.json").write_text(json.dumps(rc))
    _, frames = build_benchmark_frames(d)
    return frames["eia923"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    s = Path(a.scratch)
    off, on = _frame(s, False), _frame(s, True)
    off.to_parquet(s / "e923_off.parquet")
    on.to_parquet(s / "e923_on.parquet")
    go = off.groupby(["year", "klass"])["annual_mwh"].sum() / 1e6
    gn = on.groupby(["year", "klass"])["annual_mwh"].sum() / 1e6
    d = gn.sub(go, fill_value=0.0).round(4)
    added = sorted(set(on["plant_id"]) - set(off["plant_id"]))
    out = {
        "delta_twh": {f"{y}|{k}": v for (y, k), v in d.items() if abs(v) > 1e-4},
        "min_delta_twh": float(d.min()),
        "added_plants_n": len(added),
        "off_total": {int(k): v for k, v in go.groupby(level=0).sum().round(3).items()},
        "on_total": {int(k): v for k, v in gn.groupby(level=0).sum().round(3).items()},
    }
    Path(a.out).write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
