"""PJM 85 (G-20b path B) instrumentation — the pjm-84 report, path-B edition.

Reads a completed pjm-85 bundle (no LP re-solve) and prints the A/B evidence
the G-20b work order asks for, mirroring the pjm-84 SUMMARY tables:

* reserve dual: hours > 0, max/mean-when-binding, per year (system.parquet
  ``reserve_price`` — the PJM RTO balance-row dual, folded into the LMP via
  the shared-headroom coupling);
* C3c tail: model hours with demand-weighted RTO LMP > $200 (and the bundle's
  scored metrics.json numbers where present);
* the bind-gate reserve-supply measures re-computed on the P1 dispatch
  (plant-online headroom, online ∧ 10-min-ramp-deliverable with the bundle's
  measured_ramp_capability ramp10), min / p50 / hours below the measured
  Primary requirement — directly comparable to the pjm-84 table and the
  docs/multi-iso/pjm-reserve-ordc.md bind-gate table;
* fuel-mix deltas vs the pjm-83 keeper (its committed dashboard run payload).

Usage: python scripts/probes/_pjm85_pathb_report.py <bundle> [years...]
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
from derive_pjm_ordc_overlay import _run_year_kwargs  # noqa: E402

from market_sim.config.plant_taxonomy import fuel930_of  # noqa: E402
from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    RESERVE_FUEL_TYPES,
    load_pjm_measured_reserve_requirement,
)

PJM83_RUN_JS = REPO / "frontend/data/backcast/runs/2026-07-06-pjm-83-srmc-reground.js"


def _load_run_payload(js_path: Path) -> dict:
    """Decode a dashboard runGz JS payload (base64(gzip(json)))."""
    s = js_path.read_text()
    m = re.search(r'runGz\[[^\]]+\]="([^"]+)"', s)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _system_stats(bundle: Path, year: int) -> dict:
    sys_df = pd.read_parquet(bundle / "system.parquet")
    d = sys_df[(sys_df["year"] == year) & (sys_df["pass"] == "P1")]
    # reserve_price is system-wide (identical per zone): one zone's series.
    z0 = d[d["zone"] == d["zone"].iloc[0]].sort_values("hour")
    rp = z0["reserve_price"].to_numpy()
    # Demand-weighted RTO LMP per hour.
    pv = d.pivot_table(index="hour", columns="zone", values="price")
    dv = d.pivot_table(index="hour", columns="zone", values="demand")
    lmp = (pv * dv).sum(axis=1) / dv.sum(axis=1)
    return {
        "dual_hours": int((rp > 1e-6).sum()),
        "dual_max": float(rp.max()),
        "dual_mean_binding": float(rp[rp > 1e-6].mean()) if (rp > 1e-6).any() else 0.0,
        "lmp_max": float(lmp.max()),
        "lmp_mean": float(lmp.mean()),
        "lmp_gt200_h": int((lmp > 200.0).sum()),
        "lmp_gt75_h": int((lmp > 75.0).sum()),
    }


def _bindgate_measures(bundle: Path, year: int, meta: dict) -> dict:
    """Online / online+deliverable reserve supply on the P1 dispatch pattern."""
    from run_calibration import run_year  # heavy import

    hours = int(meta["hours"])
    kw = _run_year_kwargs(meta)
    # The pjm-84/85 recipes reconcile ramp10 against the measured datatype;
    # _run_year_kwargs predates the flag, so forward it from meta explicitly.
    if meta.get("measured_ramp_capability"):
        kw["measured_ramp_capability"] = True
    state = run_year(year, meta["iso"], hours, meta["gas_prices"][str(year)], **kw)
    fa = state["fleet_arrays"]
    fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
    elig = np.isin(fuel, sorted(RESERVE_FUEL_TYPES))
    cap = fa.pmax[:, None] * fa.availability
    uids = np.asarray(fa.unit_ids, dtype=object)

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    disp = disp[disp["unit_id"].isin(set(uids))]
    dmat = (
        disp.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )
    headroom = np.clip(cap - dmat, 0.0, None)
    # Plant online when any of its tranches dispatch (>0.5 MW this hour).
    plant = np.asarray(fa.plant_code, dtype=int)
    keys = np.where(plant > 0, plant, -(np.arange(plant.size) + 1))
    _, inv = np.unique(keys, return_inverse=True)
    plant_disp = np.zeros((inv.max() + 1, dmat.shape[1]))
    np.add.at(plant_disp, inv, dmat)
    online_unit = (plant_disp > 0.5)[inv]
    online_hr = np.where(elig[:, None] & online_unit, headroom, 0.0)
    sys_online = online_hr.sum(axis=0)
    ramp10 = getattr(fa, "ramp10", None)
    if ramp10 is not None:
        r = np.asarray(ramp10, dtype=float)[:, None] * fa.availability
        deliverable = np.minimum(online_hr, np.where(elig[:, None], r, 0.0)).sum(axis=0)
    else:
        deliverable = sys_online
    req = load_pjm_measured_reserve_requirement(year, hours)
    req = np.zeros(hours) if req is None else np.asarray(req, dtype=float)
    return {
        "req_mean": float(req.mean()),
        "online_min": float(sys_online.min()),
        "online_p50": float(np.median(sys_online)),
        "deliv_min": float(deliverable.min()),
        "deliv_p50": float(np.median(deliverable)),
        "deliv_h_below_req": int((deliverable < req).sum()),
        "deliv_min_ratio": float((deliverable / np.maximum(req, 1.0)).min()),
    }


def main() -> int:
    bundle = Path(sys.argv[1])
    meta = json.loads((bundle / "meta.json").read_text())
    years = [int(y) for y in sys.argv[2:]] or [int(y) for y in meta["years"]]

    base = _load_run_payload(PJM83_RUN_JS) if PJM83_RUN_JS.exists() else None

    print(f"=== PJM 85 path-B report: {bundle} ===")
    for year in years:
        s = _system_stats(bundle, year)
        print(
            f"\n--- {year} ---\n"
            f"reserve dual: {s['dual_hours']} h > 0"
            f" (max ${s['dual_max']:.2f}, mean-when-binding"
            f" ${s['dual_mean_binding']:.2f})\n"
            f"LMP (demand-weighted RTO): mean ${s['lmp_mean']:.2f},"
            f" max ${s['lmp_max']:.2f}, >$200: {s['lmp_gt200_h']} h,"
            f" >$75: {s['lmp_gt75_h']} h"
        )
        b = _bindgate_measures(bundle, year, meta)
        print(
            f"measured Primary req mean {b['req_mean']:.0f} MW\n"
            f"plant-online eligible headroom: min {b['online_min']:.0f},"
            f" p50 {b['online_p50']:.0f} MW\n"
            f"online+10-min-deliverable: min {b['deliv_min']:.0f},"
            f" p50 {b['deliv_p50']:.0f} MW; hours < req:"
            f" {b['deliv_h_below_req']}; min supply/req"
            f" {b['deliv_min_ratio']:.2f}x"
        )
        # Fuel-mix / class deltas vs the pjm-83 keeper payload (its volErr
        # zone-month grids: .m = model TWh, .a = EIA-923 actual TWh).
        disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
        model_twh = disp.groupby("class")["mw"].sum() / 1e6
        ybase = (base or {}).get("years", {}).get(str(year))
        if ybase:
            print("fuel TWh (model, delta vs pjm-83 keeper model, actual):")
            for row in ybase.get("fuelRows", []):
                cls = [k for k in model_twh.index if fuel930_of(k) == row["fuel"]]
                m85 = float(model_twh.reindex(cls).fillna(0.0).sum())
                print(
                    f"  {row['fuel']:10s} {m85:7.2f}"
                    f"  ({m85 - float(row['m']):+6.2f})  actual {row['b']:.2f}"
                )
            print("class TWh (model, delta vs pjm-83 keeper model, actual):")
            for k, grid in sorted(ybase.get("volErr", {}).items()):
                zm = grid.get("zoneMon", {})
                m83 = sum(sum(z.get("m", [])) for z in zm.values())
                a = sum(sum(z.get("a", [])) for z in zm.values())
                m85 = float(model_twh.get(k, 0.0))
                print(f"  {k:16s} {m85:7.2f}  ({m85 - m83:+6.2f})  actual {a:7.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
