"""G-22 A'-vs-B adjudication sweep: model stack price at deeper procurement.

pjm-99 proved the measured TOP-of-curve surface (lever A) is inert: the
model's margin at the missed summer peaks sits at $30-45 with 21-24 GW of
idle thermal offered BELOW the actual DA price
(docs/FINDING-pjm-offer-surface-noop-2026-07.md). The re-scoped candidates
are A' (reprice the ECON bands to the measured mid-curve distribution) and
B (DA procurement depth: the real DA market clears ~9-10 GW deeper than the
model's served load). This probe adjudicates them WITHOUT an LP solve:

  For each top-N system-load hour of a solved baseline, sort the idle
  thermal stack (avail - dispatched) by the LP's own offer price (mc_base,
  the audit pattern) and read the merit-order-implied clearing price if the
  hour's served depth were Delta GW deeper, for Delta in --deltas. The
  marginal class at each depth says WHOSE econ band caps the dual there.

Interpretation:
  * implied price at Delta ~ 9-10 GW ~= actual DA  -> B alone closes the
    gap (the model's mid-curve is priced right at the real margin).
  * implied price at Delta ~ 9-10 GW << actual DA  -> the mid-curve is
    too cheap even at depth -> A' is needed (alone or with B); the
    marginal-class table lists the bands A' must reprice.
  * implied price already ~ actual at Delta=0 after an A' repricing
    overlay (--surface-json, optional) -> A' alone suffices.

First-order local approximation: ignores transmission, storage and
interchange re-dispatch (a zonal LP would relieve some of the depth
through imports/storage). Treat the implied price as an UPPER bound on
the LP's response at each depth. Pure rule-16 throwaway diagnostic:
writes depth_price_sweep_<year>.json into the bundle dir and prints
tables; never registered.

Usage:
    python scripts/probes/_g22_depth_price_sweep.py \
        results/calibration/pjm98_baseline_20260712 \
        [--years 2023 2024 2025] [--top 150] [--deltas 0 3 6 8 10 12]
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
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.interchange_config import IMPORT_ZONE  # noqa: E402

CAL_DIR = REPO / "data" / "raw" / "_validation-source"


def _actual_da(year: int, hours: int) -> np.ndarray:
    """Hourly measured PJM DA system LMP ($/MWh) from the validation source."""
    df = pd.read_parquet(CAL_DIR / "actual_lmp_hourly_PJM.parquet")
    df = df[df["year"] == year]
    out = np.full(hours, np.nan)
    idx = df["hour"].to_numpy(dtype=int)
    keep = (idx >= 0) & (idx < hours)
    out[idx[keep]] = df["da"].to_numpy(dtype=float)[keep]
    return out


def sweep_year(
    bundle: Path, year: int, top_n: int, deltas_gw: list[float], meta: dict
) -> dict:
    """Merit-order-implied price at each extra-depth Delta for one year."""
    from derive_pjm_ordc_overlay import _run_year_kwargs
    from run_calibration import run_year

    hours = int(meta["hours"])
    state = run_year(
        year,
        meta["iso"],
        hours,
        meta["gas_prices"][str(year)],
        **_run_year_kwargs(meta),
    )
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)  # (n_gen, T)
    avail = fa.pmax[:, None] * fa.availability  # (n_gen, T)
    uids = np.asarray(fa.unit_ids, dtype=object)
    grp = (
        np.asarray(fa.plant_group, dtype=object)
        if fa.plant_group is not None
        else np.array([""] * len(uids), dtype=object)
    )
    ext_zone = IMPORT_ZONE.get(meta["iso"], "")

    sysf = pd.read_parquet(bundle / "system.parquet")
    sysf = sysf[(sysf["year"] == year) & (sysf["pass"] == "P1")]
    internal = sysf[sysf["zone"] != ext_zone]
    load = internal.groupby("hour")["demand"].sum().to_numpy()
    pxd = (internal["price"] * internal["demand"]).groupby(internal["hour"]).sum()
    lw_price = (pxd / internal.groupby("hour")["demand"].sum()).to_numpy()

    da = _actual_da(year, hours)
    top = np.argsort(load)[-top_n:]
    top = top[np.isfinite(da[top])]

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    disp = disp[disp["pass"] == "P1"]
    dmat = (
        disp[disp["unit_id"].isin(set(map(str, uids)))]
        .pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )
    unit_zone = (
        disp.drop_duplicates("unit_id")
        .set_index("unit_id")["zone"]
        .reindex(uids)
        .astype(object)
        .fillna("")
        .to_numpy()
    )
    thermal = unit_zone != ext_zone

    mc_t = mc[thermal]
    idle_t = np.clip(avail[thermal] - dmat[thermal], 0.0, None)
    grp_t = grp[thermal]

    deltas_mw = [float(d) * 1e3 for d in deltas_gw]
    implied = np.full((len(deltas_gw), len(top)), np.nan)
    marg_class = np.full((len(deltas_gw), len(top)), "", dtype=object)
    for j, h in enumerate(top):
        idle_h = idle_t[:, h]
        on = idle_h > 0.5
        order = np.argsort(mc_t[on, h])
        offers = mc_t[on, h][order]
        caps = idle_h[on][order]
        classes = grp_t[on][order]
        cum = np.cumsum(caps)
        for i, dmw in enumerate(deltas_mw):
            if dmw <= 0.0:
                implied[i, j] = lw_price[h]
                marg_class[i, j] = "(model)"
                continue
            k = int(np.searchsorted(cum, dmw))
            if k >= len(cum):  # depth exhausts the idle stack
                implied[i, j] = np.inf
                marg_class[i, j] = "(stack exhausted)"
            else:
                # LP duals never fall below the pre-depth price.
                implied[i, j] = max(offers[k], lw_price[h])
                marg_class[i, j] = str(classes[k])

    rows = []
    for i, dgw in enumerate(deltas_gw):
        vals = implied[i]
        fin = np.isfinite(vals)
        cls, cnt = np.unique(marg_class[i][fin], return_counts=True)
        top3 = sorted(zip(cnt, cls), reverse=True)[:3]
        rows.append(
            {
                "delta_gw": dgw,
                "implied_mean": float(vals[fin].mean()),
                "implied_p50": float(np.median(vals[fin])),
                "implied_p90": float(np.quantile(vals[fin], 0.9)),
                "implied_max": float(vals[fin].max()),
                "hours_exhausted": int((~fin).sum()),
                "hours_ge_actual": int((vals[fin] >= da[top][fin]).sum()),
                "marginal_classes": {c: int(n) for n, c in top3},
            }
        )
    table = pd.DataFrame(rows)

    out = {
        "year": year,
        "top_n": int(len(top)),
        "load_gw_mean": float(load[top].mean() / 1e3),
        "model_lw_price": float(lw_price[top].mean()),
        "actual_da_lw": float(np.nanmean(da[top])),
        "actual_da_p90": float(np.nanquantile(da[top], 0.9)),
        "actual_da_max": float(np.nanmax(da[top])),
        "sweep": rows,
    }
    print(
        f"\n=== {year} top-{len(top)} load hours: model LW ${out['model_lw_price']:.1f} "
        f"vs actual DA LW ${out['actual_da_lw']:.1f} "
        f"(p90 ${out['actual_da_p90']:.0f} / max ${out['actual_da_max']:.0f}) ==="
    )
    print(table.to_string(index=False, float_format=lambda x: f"{x:.1f}"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=None)
    ap.add_argument("--top", type=int, default=150)
    ap.add_argument(
        "--deltas", type=float, nargs="+", default=[0.0, 3.0, 6.0, 8.0, 10.0, 12.0]
    )
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    years = args.years or meta["years"]
    results = []
    for year in years:
        if not (args.bundle / "dispatch" / f"{year}_P1.parquet").exists():
            print(f"{year}: no dispatch parquet yet — skipping")
            continue
        results.append(sweep_year(args.bundle, int(year), args.top, args.deltas, meta))

    out_path = args.bundle / "depth_price_sweep.json"
    out_path.write_text(json.dumps(results, indent=1))
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
