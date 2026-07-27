"""nyiso-85 Task 1c — what the NYISO keeper prices IN the actual C3c tail hours.

Reads the keeper's committed hourly sidecars (rule 14 [R-DASHBOARD]:
``results/calibration/<bundle>/hourly/system_<year>.parquet``, P1) and puts the
model's zonal duals side by side with the actual zonal prices in the exact hours
the C3c criterion scores — the hours whose actual 11-zone-mean hub cleared the
threshold.

Answers the question that decides whether the C3c residual is a *ceiling*
(unreachable by an hourly LP) or a *mechanism* gap:

* Where is the model in those hours — near the threshold, or nowhere near it?
* Is the model's OWN tail in the same hours and the same zones as the actual's?
* Is the actual tail broad (all zones) while the model's is one zone?

No LP is solved; a keeper replay is not needed for a zonal-price question
(rule 14). Rule 22 [R-HOLDOUT]: 2023-2025 only.

Usage:
    PYTHONPATH=$PWD:$PWD/src .venv/bin/python scripts/probes/nyiso85_model_vs_tail.py \
        --bundle results/calibration/nyiso81_floor_rederive \
        --fetch-cache <dir> [--json-out o.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from nyiso85_tail_anatomy import NYISO_ZONE_MAP, YEARS, _hub_hourly  # noqa: E402
from nyiso85_zonal_tail_basis import _zonal_hourly  # noqa: E402

# The five model zones, straight off the deriver's fold — the same keys the LP's
# system sidecar uses, so model and actual are named identically end to end.
MODEL_ZONES = tuple(NYISO_ZONE_MAP)


def _model_zonal(bundle: Path, year: int) -> pd.DataFrame | None:
    """Wide (hour x model zone) P1 energy dual frame from the keeper sidecar."""
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    d = pd.read_parquet(p)
    if "pass" in d.columns:
        d = d[d["pass"] == "P1"]
    # NYISO_external is an import node, not an NY load zone — excluded from the
    # model tail exactly as the four external proxy buses are from the actual hub.
    d = d[d["zone"].isin(MODEL_ZONES)]
    return d.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--threshold", type=float, default=300.0)
    ap.add_argument("--fetch-cache", type=Path, default=None)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args(argv)
    thr = float(args.threshold)

    out: dict = {"threshold": thr, "bundle": str(args.bundle), "years": {}}
    for year in YEARS:
        mod = _model_zonal(args.bundle, year)
        act = _zonal_hourly(year, args.fetch_cache)
        if mod is None or act is None:
            continue
        hub = _hub_hourly(year).set_index("hour")["rt"].reindex(range(8760))
        tail_hours = np.flatnonzero((hub > thr).to_numpy())

        mod_max = mod.max(axis=1).reindex(range(8760))
        model_tail = np.flatnonzero((mod_max > thr).to_numpy())
        # Which model zone carries the model's own tail hours.
        mod_tail_zone = (
            mod.loc[model_tail].idxmax(axis=1).value_counts().to_dict()
            if len(model_tail)
            else {}
        )

        rows = []
        for k in tail_hours:
            mrow = mod.loc[k] if k in mod.index else None
            if mrow is None:
                continue
            rows.append(
                {
                    "hour": int(k),
                    "actual_hub": round(float(hub.iloc[k]), 1),
                    "model_max": round(float(mrow.max()), 1),
                    "model_mean": round(float(mrow.mean()), 1),
                    "model_top_zone": str(mrow.idxmax()),
                    "model_zones_gt": int((mrow > thr).sum()),
                    "model_by_zone": {z: round(float(mrow.get(z, np.nan)), 1) for z in MODEL_ZONES if z in mrow.index},
                }
            )
        mm = np.array([r["model_max"] for r in rows]) if rows else np.array([])
        hit = int((mm > thr).sum())
        rec = {
            "actual_tail_hours": int(len(tail_hours)),
            "model_tail_hours_maxzonal": int(len(model_tail)),
            "model_tail_zone_counts": {str(k): int(v) for k, v in mod_tail_zone.items()},
            "model_hits_inside_actual_tail": hit,
            "model_max_in_actual_tail": {
                "median": round(float(np.median(mm)), 1) if mm.size else None,
                "p90": round(float(np.percentile(mm, 90)), 1) if mm.size else None,
                "max": round(float(mm.max()), 1) if mm.size else None,
            },
            "hours": rows,
        }
        out["years"][str(year)] = rec

        print(f"\n=== {year} ===")
        print(
            f"  actual tail (hub>thr): {rec['actual_tail_hours']:>3} h   |   "
            f"model tail (max-zonal>thr): {rec['model_tail_hours_maxzonal']:>3} h"
        )
        print(f"  model tail zones: {rec['model_tail_zone_counts']}")
        print(
            f"  inside the actual tail hours, model max-zonal: "
            f"median {rec['model_max_in_actual_tail']['median']}, "
            f"p90 {rec['model_max_in_actual_tail']['p90']}, "
            f"max {rec['model_max_in_actual_tail']['max']} $/MWh "
            f"({hit}/{len(rows)} hours above ${thr:.0f})"
        )
        # Per-zone detail on the worst actual hours.
        worst = sorted(rows, key=lambda r: -r["actual_hub"])[:8]
        zs = [z for z in MODEL_ZONES]
        print(f"  {'hour':>5} {'act_hub':>8} {'mdl_max':>8}  " + " ".join(f"{z[:9]:>9}" for z in zs))
        for r in worst:
            print(
                f"  {r['hour']:>5} {r['actual_hub']:>8.0f} {r['model_max']:>8.0f}  "
                + " ".join(f"{r['model_by_zone'].get(z, float('nan')):>9.0f}" for z in zs)
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
