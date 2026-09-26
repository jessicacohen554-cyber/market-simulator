#!/usr/bin/env python3
"""miso-276 phase 0 (zero LP): offer-stack depth for C3a 2022 and C1 ST_GAS 2019.

Rebuilds the keeper fleet (``run_year(fleet_only=True)``, the keeper recipe via
the miso-271 helpers, KEEPER re-pointed at ``miso275_span``) and joins it to the
keeper's committed hourly sidecars.

Per year it reports, per class:

* available TWh (``pmax x availability``), dispatched TWh (keeper P1), the
  hours dispatch is within 1 % of availability, and headroom TWh;
* the capacity-weighted mean offer (``mc_base``, the assembled P0 objective the
  LP solved on) per class, annual and by season;
* for the top-decile actual-RT hours (Indiana Hub system reference, the C3a
  actual): the model's system price, and the fossil headroom by class with its
  offer — i.e. whether the model is LONG on supply at the peak (merit depth) or
  simply priced lower (offer level);
* the ST_GAS merit position: hours ST_GAS headroom coincides with a cheaper-offer
  or dearer-offer class on the margin.

Usage::

    uv run python scripts/probes/_miso276_stack_phase0.py --years 2022 2019 \
        --out results/calibration/_miso276_stack_phase0.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _miso271_cc_decomp as dec  # noqa: E402

dec.KEEPER = REPO / "results/calibration/miso275_span"
SYS_ACT = REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
FOSSIL = (
    "COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC", "CC_REGULAR", "CC_CHP",
    "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP", "OTHER",
)
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
          6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}


def fleet(year: int, hh: float) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Unit meta, hourly available MW and hourly offer $/MWh for the keeper fleet."""
    from scripts.run_calibration import run_year  # type: ignore

    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(year, {}))
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], 8760, axis=1)
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], 8760, axis=1)
    meta = pd.DataFrame({"group": list(fa.plant_group), "pmax": pmax,
                         "unit": list(fa.unit_ids)})
    return meta, pmax[:, None] * avail, mc


def sys_actual(year: int) -> np.ndarray:
    """System-reference (Indiana Hub) RT hourly actual; NaN where unstaged."""
    df = pd.read_parquet(SYS_ACT)
    cols = df.columns.tolist()
    df = df[df["year"] == year] if "year" in cols else df
    col = "rt" if "rt" in cols else [c for c in cols if "rt" in c.lower()][0]
    s = df.groupby("hour")[col].mean().reindex(range(8760))
    return s.to_numpy(float)


def probe(year: int) -> dict:
    """Stack depth for one year."""
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    meta, mw, mc = fleet(year, _henry_hub_actual(_load_reference(), year))
    ch = pd.read_parquet(dec.KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"].pivot_table(index="hour", columns="klass",
                                            values="mw", aggfunc="sum").reindex(range(8760)).fillna(0)
    sysd = pd.read_parquet(dec.KEEPER / "hourly" / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    pv = sysd.pivot(index="hour", columns="zone", values="price").reindex(range(8760))
    dv = sysd.pivot(index="hour", columns="zone", values="demand").reindex(range(8760))
    zs = [z for z in dv.columns if dv[z].sum() > 0]
    m_sys = ((pv[zs] * dv[zs]).sum(axis=1) / dv[zs].sum(axis=1)).to_numpy()
    act = sys_actual(year)
    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(8760), "h")
    season = np.array([SEASON[m] for m in ts.month])
    ok = np.isfinite(act)
    top = ok & (act >= np.nanquantile(act, 0.9))
    out: dict = {"top_decile_hours": int(top.sum()),
                 "top_model_sys_mean": round(float(m_sys[top].mean()), 2),
                 "top_actual_mean": round(float(act[top].mean()), 2),
                 "model_price_max": round(float(m_sys.max()), 2),
                 "classes": {}}
    for g in FOSSIL:
        k = (meta.group == g).to_numpy()
        if not k.any():
            continue
        av = mw[k].sum(axis=0)
        d = ch[g].to_numpy() if g in ch.columns else np.zeros(8760)
        head = np.clip(av - d, 0, None)
        w = mw[k]
        offer = (mc[k] * w).sum(axis=0) / np.maximum(w.sum(axis=0), 1e-9)
        # offer of the headroom: MW-weighted offer of the undispatched tail is not
        # observable per unit from class sidecars; report the class mean offer.
        rec = {
            "mw": round(float(meta.pmax[k].sum()), 1),
            "avail_twh": round(float(av.sum()) / 1e6, 3),
            "disp_twh": round(float(d.sum()) / 1e6, 3),
            "binding_hours": int((d >= 0.99 * av).sum()),
            "headroom_twh": round(float(head.sum()) / 1e6, 3),
            "offer_mean": round(float(offer.mean()), 2),
            "offer_by_season": {s: round(float(offer[season == s].mean()), 2)
                                for s in ("DJF", "MAM", "JJA", "SON")},
            "top_decile": {
                "avail_gw": round(float(av[top].mean()) / 1e3, 2),
                "disp_gw": round(float(d[top].mean()) / 1e3, 2),
                "headroom_gw": round(float(head[top].mean()) / 1e3, 2),
                "offer_mean": round(float(offer[top].mean()), 2),
            },
        }
        # offer percentiles of available capacity at top-decile hours
        oo = mc[k][:, top].ravel()
        ww = w[:, top].ravel()
        if ww.sum() > 0:
            srt = np.argsort(oo)
            cw = np.cumsum(ww[srt]) / ww.sum()
            rec["top_decile"]["offer_p50_p90_max"] = [
                round(float(oo[srt][np.searchsorted(cw, q)]), 1) for q in (0.5, 0.9)
            ] + [round(float(oo.max()), 1)]
        out["classes"][g] = rec
    imp = ch["import"].to_numpy() if "import" in ch.columns else np.zeros(8760)
    out["import_top_decile_gw"] = round(float(imp[top].mean()) / 1e3, 2)
    out["import_twh"] = round(float(imp.sum()) / 1e6, 3)
    tot_head = sum(v["top_decile"]["headroom_gw"] for v in out["classes"].values())
    out["fossil_headroom_top_decile_gw"] = round(tot_head, 2)
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2019])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = {}
    for y in args.years:
        res[str(y)] = probe(y)
        print(json.dumps({y: res[str(y)]}, indent=1), flush=True)
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
