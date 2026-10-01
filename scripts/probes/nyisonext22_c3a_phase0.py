"""NYISO-NEXT-22 phase 0 (ZERO LP): where does the keeper's C3a over-price live?

Reads the designated keeper's COMMITTED hourly sidecars (NEXT-21:
``nyisonext21_2021`` for 2021, ``nyisonext21_span`` for 2022-2025) and NYISO's
public 5-minute zonal RT LBMP archive (``data/raw/lmp-data/NYISO``, staged by
``scripts/data/fetch_nyiso_zonal_lmp.py``, gitignored). The load-weighted miss

    sum_{z,h} D_zh (m_zh - a_zh) / sum D

is the zone-resolved basis the scorer's ``rt_lw`` uses (rubric v2.4), split
into additive $/MWh contributions by zone, month, hour band, actual-price
decile and a marginal class-band proxy (the nyisonext4 definition: the dearest
thermal class-band partially loaded in the hour).

Definitions fixed before any number is read:
* hour bands (model hour-of-day): night 0-5, morning 6-11, afternoon 12-17,
  evening 18-23.
* decile: of the zone-hour actual RT price, within the year.
* "floor" hours: actual deciles 1-8; "tail" hours: decile 10.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results/calibration"
LMPDIR = REPO / "data/raw/lmp-data/NYISO"
OUT = REPO / "results/phase0/nyiso/_nyisonext22_c3a_phase0.json"
ZMAP = {  # iso_configs._nyiso: A-E, F-G, H-I, J, K
    "WEST": "Upstate_West",
    "GENESE": "Upstate_West",
    "CENTRL": "Upstate_West",
    "NORTH": "Upstate_West",
    "MHK VL": "Upstate_West",
    "CAPITL": "Capital_Hudson",
    "HUD VL": "Capital_Hudson",
    "MILLWD": "Lower_Hudson",
    "DUNWOD": "Lower_Hudson",
    "N.Y.C.": "NYC",
    "LONGIL": "Long_Island",
}
THERMAL = ("CC_", "CT_", "ST_", "oil", "COAL")


def _bundle(y: int) -> Path:
    return CAL / ("nyisonext21_2021" if y == 2021 else "nyisonext21_span") / "hourly"


def _actual(y: int, kind: str = "realtime") -> pd.DataFrame:
    rows = []
    for zf in sorted(LMPDIR.glob(f"{y}??01{kind}_zone_csv.zip")):
        with zipfile.ZipFile(zf) as z:
            for n in z.namelist():
                rows.append(pd.read_csv(io.BytesIO(z.read(n))))
    r = pd.concat(rows)
    r["zone"] = r["Name"].map(ZMAP)
    r = r.dropna(subset=["zone"])
    r["ts"] = pd.to_datetime(r["Time Stamp"]).dt.floor("h")
    return r.groupby(["ts", "zone"])["LBMP ($/MWHr)"].mean().rename("act").reset_index()


def _marginal(y: int, price: pd.Series) -> pd.Series:
    cb = pd.read_parquet(_bundle(y) / f"class_band_hourly_{y}.parquet")
    cb = cb[(cb["pass"] == "P1") & cb.klass.astype(str).str.startswith(THERMAL)]
    cb["key"] = cb.klass.astype(str) + ":" + cb.band.astype(str)
    p = cb.pivot_table(index="hour", columns="key", values="mw", aggfunc="sum").fillna(0)
    part = (p > 1.0) & (p < 0.99 * p.max())
    pr = price.reindex(p.index)
    rank = {k: float(np.nanmedian(pr[part[k]])) if part[k].any() else -1 for k in p.columns}
    lab = pd.Series("none", index=p.index)
    for k in sorted(p.columns, key=lambda k: rank[k]):
        lab[part[k]] = k
    return lab


def _contrib(d: pd.DataFrame, key) -> dict:
    W = d.D.sum()
    g = d.assign(c=d.D * (d.model - d.act) / W, w=d.D / W).groupby(key)
    return (
        pd.DataFrame(
            {
                "contrib_usd": g.c.sum(),
                "load_share": g.w.sum(),
                "model": g.apply(lambda x: np.average(x.model, weights=x.D)),
                "act": g.apply(lambda x: np.average(x.act, weights=x.D)),
            }
        )
        .round(3)
        .reset_index()
        .astype({c: str for c in ([key] if isinstance(key, str) else key)})
        .to_dict("records")
    )


def run_year(y: int) -> dict:
    s = pd.read_parquet(_bundle(y) / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"].copy()
    s["ts"] = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(s.hour, unit="h")
    a = _actual(y)
    d = s.merge(a, on=["ts", "zone"]).rename(columns={"price": "model", "demand": "D"})
    da = _actual(y, "damlbmp").rename(columns={"act": "act_da"})
    d = d.merge(da, on=["ts", "zone"], how="left")
    W = d.D.sum()
    tot = float((d.D * (d.model - d.act)).sum() / W)
    abar = float(np.average(d.act, weights=d.D))
    d["month"] = d.ts.dt.month
    d["hod"] = d.hour % 24
    d["band"] = pd.cut(d.hod, [-1, 5, 11, 17, 23], labels=["night", "morning", "afternoon", "evening"])
    d["decile"] = d.groupby("zone").act.transform(
        lambda x: pd.qcut(x.rank(method="first"), 10, labels=False) + 1
    )
    sysp = d.assign(pw=d.model * d.D).groupby("hour").pw.sum() / d.groupby("hour").D.sum()
    d["marg"] = d.hour.map(_marginal(y, sysp))
    d["marg_class"] = d.marg.str.split(":").str[0]
    # how much of the miss is a level offset common to all hours vs dispersion
    dd = d.assign(err=d.model - d.act)
    res = {
        "n_zone_hours": int(len(d)),
        "total_usd": round(tot, 3),
        "act_lw": round(abar, 3),
        "pct": round(100 * tot / abar, 2),
        "act_da_lw": round(float(np.average(d.act_da.fillna(d.act), weights=d.D)), 3),
        "median_err": round(float(dd.err.median()), 3),
        "zone": _contrib(d, "zone"),
        "month": _contrib(d, "month"),
        "band": _contrib(d, "band"),
        "decile": _contrib(d, "decile"),
        "marg_class": _contrib(d, "marg_class"),
        "zone_x_band": _contrib(d, ["zone", "band"]),
        "zone_x_month": _contrib(d, ["zone", "month"]),
    }
    return res


def main() -> None:
    out = {y: run_year(y) for y in (2021, 2022, 2023, 2024, 2025)}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    for y, r in out.items():
        print(f"\n===== {y}: miss {r['total_usd']:+.2f} on rt_lw {r['act_lw']:.2f} ({r['pct']:+.1f} %); DA_lw {r['act_da_lw']:.2f}; median err {r['median_err']:+.2f}")
        for k in ("zone", "band", "marg_class"):
            print("  -- " + k + ": " + "; ".join(
                f"{v[k]}:{v['contrib_usd']:+.2f}({v['load_share']:.2f} m{v['model']:.1f}/a{v['act']:.1f})" for v in r[k]))
        print("  -- decile: " + " ".join(f"{v['decile']}:{v['contrib_usd']:+.2f}" for v in r["decile"]))
        print("  -- month: " + " ".join(f"{v['month']}:{v['contrib_usd']:+.2f}" for v in r["month"]))


if __name__ == "__main__":
    main()
