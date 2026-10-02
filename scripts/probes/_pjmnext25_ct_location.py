"""PJM-NEXT-25 card 2 (zero LP): is real CT run-time across plants explained by location?

NEXT-23/24 found the keeper's CT_PEAKER ordering across plants 2-3.5x steeper in cost than
real: cheap CTs over-run and dear ones under-run. This asks whether the real ordering
follows the plant's LOCAL price instead of the system price. Per CT_PEAKER plant-year
(C1 bench plants with a CAMPD shape):

- ``real_runh`` / ``model_runh``: hours with output > 5 % of the plant's mean LP capacity;
- ``offer``: the keeper's capacity-weighted P1 offer, averaged over available hours;
- ``inm_sys_da`` / ``inm_zon_da`` / ``inm_zon_rt``: hours in which actual system DA,
  actual zonal DA or actual zonal RT is at or above the plant's own hourly offer. Zonal
  prices are PJM DataMiner2 transmission-zone LMPs averaged over each model zone's pnodes
  (``_pjmnext22_coal_zonal_margin.PNODE_TO_ZONE``), on the keeper's hour axis.

Across plants (capacity-weighted): Pearson r of real and model run-hours against each
in-money count, and the zone means of real - model run-hours after the zonal-DA predictor
(a location residual no price explains points at out-of-market commitment).

Writes ``results/phase0/pjm/_pjmnext25_ct_location.json``.
Run: ``python3 scripts/probes/_pjmnext25_ct_location.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext22_coal_zonal_margin import PNODE_TO_ZONE  # noqa: E402
from _pjmnext24_loading_margin import ACTUAL, T, YEARS, plant_hours  # noqa: E402

ZONAL = REPO / "data/raw/pjm-zonal-lmp"
OUT = REPO / "results/phase0/pjm/_pjmnext25_ct_location.json"
RUN_FRAC = 0.05


def zonal(y: int, feed: str) -> pd.DataFrame | None:
    """Model-zone x hour actual LMP for one feed (``da_hrl_lmps`` / ``rt_hrl_lmps``)."""
    files = sorted(ZONAL.glob(f"{feed}_{y}_*.parquet"))
    if len(files) < 12:
        return None
    col = "total_lmp_da" if feed.startswith("da") else "total_lmp_rt"
    z = pd.concat(
        pd.read_parquet(f, columns=["datetime_beginning_utc", "pnode_name", col])
        for f in files
    ).reset_index(drop=True)
    # Fixed EST, Feb 29 dropped: the keeper / actual_lmp_hourly_PJM hour axis.
    ts = pd.to_datetime(
        z.datetime_beginning_utc, format="%m/%d/%Y %I:%M:%S %p"
    ) - pd.Timedelta(hours=5)
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    z, ts = z[keep].copy(), ts[keep]
    doy = ts.dt.dayofyear - ((ts.dt.month > 2) & ts.dt.is_leap_year).astype(int)
    z["hour"] = ((doy - 1) * 24 + ts.dt.hour).to_numpy()
    z = z[(z.hour >= 0) & (z.hour < T)]
    z["zone"] = z.pnode_name.map(PNODE_TO_ZONE)
    zz = z.dropna(subset=["zone"]).groupby(["zone", "hour"])[col].mean()
    return zz.unstack("hour").reindex(columns=range(T)).ffill(axis=1).bfill(axis=1)


def _r(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    """Weighted Pearson correlation."""
    w = w / w.sum()
    mx, my = (w * x).sum(), (w * y).sum()
    c = (w * (x - mx) * (y - my)).sum()
    return float(c / np.sqrt((w * (x - mx) ** 2).sum() * (w * (y - my) ** 2).sum()))


def year(y: int, act: pd.DataFrame) -> dict | None:
    """One year's CT location table."""
    zda, zrt = zonal(y, "da_hrl_lmps"), zonal(y, "rt_hrl_lmps")
    if zda is None or zrt is None:
        return None
    p = plant_hours(y, act)
    p = p[(p.k == "CT") & (p.cap > 0)].copy()
    h = p.hour.to_numpy()
    zi = {z: i for i, z in enumerate(zda.index)}
    rows = p.zone.map(zi)
    ok = rows.notna().to_numpy()
    p = p[ok]
    h, ri = h[ok], rows[ok].astype(int).to_numpy()
    p["zda"] = zda.to_numpy()[ri, h]
    p["zrt"] = zrt.to_numpy()[ri, h]
    sda = act[act.year == y].sort_values("hour").da.to_numpy()[:T]
    p["sda"] = sda[h]
    out = []
    for code, g in p.groupby("plant_code"):
        mcap = g.cap.mean()
        out.append(
            {
                "plant": int(code),
                "zone": str(g.zone.iloc[0]),
                "cap": float(mcap),
                "offer": float((g.offer * g.cap).sum() / g.cap.sum()),
                "real_runh": int((g.real > RUN_FRAC * mcap).sum()),
                "model_runh": int((g.mw > RUN_FRAC * mcap).sum()),
                "real_twh": float(g.real.sum()) / 1e6,
                "model_twh": float(g.mw.sum()) / 1e6,
                "inm_sys_da": int((g.sda >= g.offer).sum()),
                "inm_zon_da": int((g.zda >= g.offer).sum()),
                "inm_zon_rt": int((g.zrt >= g.offer).sum()),
            }
        )
    d = pd.DataFrame(out)
    w = d.cap.to_numpy()
    corr = {
        who: {
            k: round(_r(d[k].to_numpy(float), d[who].to_numpy(float), w), 3)
            for k in ("offer", "inm_sys_da", "inm_zon_da", "inm_zon_rt")
        }
        for who in ("real_runh", "model_runh")
    }
    # Location residual: real run-hours minus a capacity-weighted linear fit on zonal DA.
    x = d.inm_zon_da.to_numpy(float)
    X = np.c_[np.ones_like(x), x] * np.sqrt(w)[:, None]
    for who in ("real_runh", "model_runh"):
        b = np.linalg.lstsq(X, d[who].to_numpy(float) * np.sqrt(w), rcond=None)[0]
        d[f"{who}_resid"] = d[who] - (b[0] + b[1] * x)
    zone = (
        d.groupby("zone")
        .apply(
            lambda g: pd.Series(
                {
                    "plants": len(g),
                    "cap_gw": g.cap.sum() / 1e3,
                    "real_runh": np.average(g.real_runh, weights=g.cap),
                    "model_runh": np.average(g.model_runh, weights=g.cap),
                    "inm_zon_da": np.average(g.inm_zon_da, weights=g.cap),
                    "inm_sys_da": np.average(g.inm_sys_da, weights=g.cap),
                    "real_resid": np.average(g.real_runh_resid, weights=g.cap),
                    "real_minus_model_twh": (g.real_twh - g.model_twh).sum(),
                }
            ),
            include_groups=False,
        )
        .round(2)
    )
    return {
        "plants": len(d),
        "corr_across_plants": corr,
        "by_zone": zone.reset_index().to_dict(orient="records"),
        "plant_rows": d.round(3).to_dict(orient="records"),
    }


def main() -> None:
    """Every year with both zonal feeds on disk."""
    act = pd.read_parquet(ACTUAL)
    res: dict = {"what": "PJM-NEXT-25 card 2: CT run-hours vs local price. ZERO LP."}
    for y in YEARS:
        r = year(y, act)
        if r is None:
            print(y, "zonal feeds missing", flush=True)
            continue
        res[str(y)] = r
        print(y, r["plants"], json.dumps(r["corr_across_plants"]), flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
