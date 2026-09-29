#!/usr/bin/env python3
"""miso-283 phase 0 (ZERO LP): footprint of ``committed_band_measured_basis`` on the MISO keeper.

Two fleet-only rebuilds of the designated keeper's recipe (control, and the
same recipe with ``committed_band_measured_basis=True``) for one year. Reports,
per class, the MW-weighted mean assembled P0 offer (``mc_base``) of the
``_committed`` tranches in both, the hour-of-day profile of the change, which
tranches move at all, and a STATIC first-order night-price read: in each
MISO-South / MISO-Illinois hour whose keeper price is matched (within ``TOL``)
by a tranche's control offer, that tranche's offer change. Static, not a
re-dispatch: it bounds the direct offer effect and says nothing about re-merit.

Output: ``<out-dir>/committed_delta_<Y>.json``.  Rule 13: nothing feeds a solve.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
TOL = 0.5  # $/MWh offer-match tolerance (probe resolution, not a model value)
FLAG = "committed_band_measured_basis"


def build(y: int, hh: float, flips: dict):
    """Fleet-only rebuild; returns (unit_ids, groups, zones, pmax, mc)."""
    from scripts.run_calibration import run_year  # type: ignore

    st = run_year(y, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(y, flips))
    fa, isoc = st["fleet_arrays"], st["iso_config"]
    n = len(fa.pmax)
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, 8760, axis=1)
    zn = list(isoc.zone_names)
    zone = np.array([zn[i] for i in np.asarray(fa.zone_idx).astype(int)])
    return (
        np.asarray(list(fa.unit_ids)),
        np.asarray(list(fa.plant_group)),
        zone,
        np.asarray(fa.pmax, dtype=float),
        mc,
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    y = args.year
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hh = _henry_hub_actual(_load_reference(), y)
    u0, g0, z0, p0, mc0 = build(y, hh, {})
    u1, g1, z1, p1, mc1 = build(y, hh, {FLAG: True})
    assert (u0 == u1).all(), "unit order differs between rebuilds"
    d = mc1 - mc0
    moved = np.abs(d).max(axis=1) > 1e-6
    band = np.array([s.rsplit("_", 1)[-1] for s in u0])
    res: dict = {"year": y, "n_units": int(len(u0)), "n_moved": int(moved.sum())}
    res["moved_by_class_band"] = (
        pd.DataFrame(
            {
                "g": g0[moved],
                "b": band[moved],
                "mw": p0[moved],
                "d": d[moved].mean(axis=1),
            }
        )
        .groupby(["g", "b"])
        .apply(
            lambda x: pd.Series(
                {
                    "mw": x.mw.sum(),
                    "n": len(x),
                    "d_mw_wtd": (x.d * x.mw).sum() / max(x.mw.sum(), 1e-9),
                    "off0": None,
                }
            )
        )
        .drop(columns="off0")
        .round(2)
        .reset_index()
        .to_dict("records")
    )
    com = band == "committed"
    rows = []
    for g in np.unique(g0[com]):
        m = com & (g0 == g) & (p0 > 0)
        w = p0[m]
        rows.append(
            {
                "g": g,
                "mw": round(float(w.sum()), 1),
                "offer0": round(float((mc0[m].mean(axis=1) * w).sum() / w.sum()), 2),
                "offer1": round(float((mc1[m].mean(axis=1) * w).sum() / w.sum()), 2),
            }
        )
    res["committed_offer_by_class"] = rows
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    sysd = (
        sysd[sysd["pass"] == "P1"]
        .pivot(index="hour", columns="zone", values="price")
        .sort_index()
    )
    hod = np.arange(8760) % 24
    for z in ("MISO-South", "MISO-Illinois"):
        m = (z0 == z) & (p0 > 0)
        pz = sysd[z].to_numpy()
        gap = np.abs(mc0[m] - pz[None, :])
        best = gap.argmin(axis=0)
        t = np.arange(8760)
        hit = gap[best, t] <= TOL
        dd = np.where(hit, d[m][best, t], 0.0)
        df = pd.DataFrame({"hod": hod, "dd": dd, "hit": hit})
        res[f"{z}_static_dprice_hod"] = df.groupby("hod").dd.mean().round(2).tolist()
        res[f"{z}_static_dprice_night"] = round(float(df[df.hod < 6].dd.mean()), 2)
        res[f"{z}_static_dprice_all"] = round(float(df.dd.mean()), 2)
    (out / f"committed_delta_{y}.json").write_text(
        json.dumps(res, indent=1, default=str)
    )
    print(
        json.dumps(
            {k: v for k, v in res.items() if "hod" not in k}, indent=1, default=str
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
