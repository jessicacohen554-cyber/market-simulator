"""NYISO-NEXT-4 phase 0 (ZERO LP): decompose the keeper's C3a 2022/2025 mean-price miss.

Reads the designated keeper's COMMITTED hourly sidecars
(``results/calibration/nyisonext3_span/hourly``) and the RT bench
(``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``) and splits the
load-weighted miss  sum_h D_h (m_h - a_h) / sum_h D_h  into additive contributions
($/MWh of the annual mean) by month, by ACTUAL-price decile, by hour class
(tail / dear-gas day / ordinary) and by a marginal class-band proxy. Zonal split
uses NYISO's published 5-min zonal RT prices (2022 in repo; 2023-2025 fetched,
NYRT_DIR).

Definitions fixed before any number is read:
* tail hour: actual RT > $300/MWh.
* dear-gas day: the day's Transco Z6 NY daily print >= the year's p90 of daily
  prints (the nyiso-248 DAILY coordinate; Iroquois has no daily series in repo).
* marginal proxy: among thermal class-bands partially loaded in the hour
  (0 < mw < 0.99 x that band's annual max), the one with the highest median model
  price over its partially-loaded hours. A proxy - the sidecars carry no offers.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUN = REPO / "results/calibration/nyisonext3_span/hourly"
ACT = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
GAS = REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv"
LMPDIR = REPO / "data/raw/lmp-data/NYISO"
# 2023-2025 zonal RT zips are not in the repo (the dartmonthlylmpindex_*.csv files under
# lmp-data/NYISO are ISO-NE data, misfiled); fetched from mis.nyiso.com/public/csv/realtime/.
import os

EXTRA = Path(os.environ.get("NYRT_DIR", "/nonexistent"))
OUT = REPO / "results/phase0/nyiso/_nyisonext4_c3a_decompose.json"
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
THERMAL = ("CC_", "CT_", "ST_", "oil")


def _system(y: int):
    s = pd.read_parquet(BUN / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    n = s.assign(pw=s.price * s.demand).groupby("hour")[["pw", "demand"]].sum()
    a = pd.read_parquet(ACT)
    a = a[a.year == y].set_index("hour")["rt"]
    d = (
        pd.DataFrame({"model": n.pw / n.demand, "D": n.demand})
        .join(a.rename("act"))
        .dropna()
    )
    d["ts"] = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(d.index, unit="h")
    return s, d


def _contrib(d: pd.DataFrame, key) -> pd.DataFrame:
    W = d.D.sum()
    g = d.assign(c=d.D * (d.model - d.act) / W, w=d.D / W).groupby(key)
    return pd.DataFrame(
        {
            "contrib_usd": g.c.sum(),
            "load_share": g.w.sum(),
            "model": g.apply(lambda x: np.average(x.model, weights=x.D)),
            "act": g.apply(lambda x: np.average(x.act, weights=x.D)),
        }
    ).round(3)


def _marginal(y: int, d: pd.DataFrame) -> pd.Series:
    cb = pd.read_parquet(BUN / f"class_band_hourly_{y}.parquet")
    cb = cb[(cb["pass"] == "P1") & cb.klass.astype(str).str.startswith(THERMAL)]
    cb["key"] = cb.klass.astype(str) + ":" + cb.band.astype(str)
    p = cb.pivot_table(index="hour", columns="key", values="mw", aggfunc="sum").fillna(
        0
    )
    part = (p > 1.0) & (p < 0.99 * p.max())
    price = d.model.reindex(p.index)
    rank = {
        k: float(np.nanmedian(price[part[k]])) if part[k].any() else -1
        for k in p.columns
    }
    order = sorted(p.columns, key=lambda k: rank[k])
    lab = pd.Series("none", index=p.index)
    for k in order:  # later (dearer) overwrites
        lab[part[k]] = k
    return lab


def _zonal_hourly(y: int, s: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for zf in sorted(
        list(LMPDIR.glob(f"{y}*realtime_zone_csv.zip"))
        + list(EXTRA.glob(f"{y}*realtime_zone_csv.zip"))
    ):
        with zipfile.ZipFile(zf) as z:
            for n in z.namelist():
                rows.append(pd.read_csv(io.BytesIO(z.read(n))))
    r = pd.concat(rows)
    r["zone"] = r["Name"].map(ZMAP)
    r = r.dropna(subset=["zone"])
    r["ts"] = pd.to_datetime(r["Time Stamp"]).dt.floor("h")
    # interval-ending 5-min stamps: HE convention matches the bench's hour index
    hz = r.groupby(["ts", "zone"])["LBMP ($/MWHr)"].mean().rename("act").reset_index()
    ld = s[["hour", "zone", "demand", "price"]].copy()
    ld["ts"] = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(ld.hour, unit="h")
    m = ld.merge(hz, on=["ts", "zone"])
    return m


def main() -> None:
    gas = pd.read_csv(GAS, parse_dates=["date"]).set_index("date")[
        "transco_z6_ny_usd_mmbtu"
    ]
    out = {}
    for y in (2022, 2023, 2024, 2025):
        s, d = _system(y)
        W = d.D.sum()
        tot = float((d.D * (d.model - d.act)).sum() / W)
        abar = float(np.average(d.act, weights=d.D))
        d["month"] = d.ts.dt.month
        d["decile"] = pd.qcut(d.act.rank(method="first"), 10, labels=False) + 1
        gy = gas[gas.index.year == y].asfreq("D").ffill()
        dear = set(gy[gy >= gy.quantile(0.9)].index.date)
        d["cls"] = np.where(
            d.act > 300,
            "tail>$300",
            np.where([t in dear for t in d.ts.dt.date], "dear-gas day", "ordinary"),
        )
        d["winter"] = d.month.isin([12, 1, 2])
        d["marg"] = _marginal(y, d)
        mk = d.marg.str.split(":").str[0]
        d["marg_class"] = mk
        res = {
            "total_usd": round(tot, 3),
            "act_mean": round(abar, 3),
            "pct": round(100 * tot / abar, 2),
            "month": _contrib(d, "month").to_dict("index"),
            "decile": _contrib(d, "decile").to_dict("index"),
            "hourclass": _contrib(d, "cls").to_dict("index"),
            "dear_x_winter": _contrib(d, ["cls", "winter"])
            .reset_index()
            .to_dict("records"),
            "marg_class": _contrib(d, "marg_class").to_dict("index"),
            "marg_band": _contrib(d, "marg")
            .sort_values("contrib_usd")
            .head(8)
            .to_dict("index"),
            "n_dear_days": len(dear),
        }
        # zonal, on a monthly grain (consistent across years)
        m = _zonal_hourly(y, s)
        m["month"] = m.ts.dt.month
        zm = (
            m.groupby(["month", "zone"])
            .apply(
                lambda x: pd.Series(
                    {
                        "demand": x.demand.sum(),
                        "model": np.average(x.price, weights=x.demand),
                        "act": np.average(x.act, weights=x.demand),
                    }
                )
            )
            .reset_index()
        )
        zm = zm.dropna(subset=["act"])
        ZW = zm.demand.sum()
        zm["c"] = zm.demand * (zm.model - zm.act) / ZW
        zz = (
            zm.groupby("zone")
            .apply(
                lambda x: pd.Series(
                    {
                        "contrib_usd": x.c.sum(),
                        "load_share": x.demand.sum() / ZW,
                        "model": np.average(x.model, weights=x.demand),
                        "act": np.average(x.act, weights=x.demand),
                    }
                )
            )
            .round(3)
        )
        res["zone_basis"] = "hourly, NYISO 5-min zonal RT zips"
        res["zone"] = zz.to_dict("index")
        res["zone_total_usd"] = round(float(zm.c.sum()), 3)
        out[y] = res
    OUT.write_text(json.dumps(out, indent=1, default=str))
    for y, r in out.items():
        print(
            f"\n===== {y}: miss {r['total_usd']:+.2f} $/MWh on {r['act_mean']:.2f} ({r['pct']:+.1f} %)"
        )
        for k in ("hourclass", "marg_class", "zone"):
            print(f"  -- {k}")
            for kk, v in r[k].items():
                print(
                    f"     {str(kk):22s} {v['contrib_usd']:+7.2f}  share {v['load_share']:.3f}  model {v['model']:7.2f} act {v['act']:7.2f}"
                )
        print(
            "  -- month: "
            + " ".join(f"{m}:{v['contrib_usd']:+.2f}" for m, v in r["month"].items())
        )
        print(
            "  -- decile: "
            + " ".join(f"{m}:{v['contrib_usd']:+.2f}" for m, v in r["decile"].items())
        )
        print(
            "  -- dear x winter: "
            + "; ".join(
                f"{v['cls']}/{'W' if v['winter'] else 'nonW'}:{v['contrib_usd']:+.2f}"
                for v in r["dear_x_winter"]
            )
        )
        print(
            "  -- worst marginal bands: "
            + "; ".join(
                f"{k}:{v['contrib_usd']:+.2f}({v['load_share']:.2f})"
                for k, v in r["marg_band"].items()
            )
        )


if __name__ == "__main__":
    main()
