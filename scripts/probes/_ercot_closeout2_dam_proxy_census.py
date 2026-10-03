"""ERCOT closeout-2: the R-25 DAM-proxy census (zero LP).

Asks whether the free NP3-966 60-Day DAM Gen Resource energy-offer curves
(gap G2) are an adequate licence-free proxy for the NP3-965 60-Day SCED
``Submitted TPO`` curves that the keeper's coal construction is built on
(ERCOT-144 static levels, ercot-168 2023 year table), and what the deferred
2019-22 intake (R-7) would buy for 2019/20 C1 COAL_PRB.

Readings and thresholds are fixed in
``docs/records/ercot/closeout/PRECOMMIT-closeout-ercot2-dam-proxy-census-2026-10-03.md``.

Outputs (``docs/records/ercot/closeout/data/``):
    dam_proxy_coverage.csv   per plant-year: share of ON hours with a curve,
                             offered-curve MW share of ON HSL-hours
    dam_proxy_levels.csv     per plant-year DAM modal level vs SCED basis
    dam_proxy_summary.json   Δ*, P1 bias / counts, Q3 slope

Usage::

    python scripts/probes/_ercot_closeout2_dam_proxy_census.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "ercot"
BUNDLE = REPO / "results" / "calibration" / "closeout_ercot_l1_span"
OUT = REPO / "docs" / "records" / "ercot" / "closeout" / "data"

#: Resource-name prefix -> EIA plant (the ERCOT-144 crosswalk,
#: ``scripts/data/derive_coal_perplant_offer.py::PREFIX_TO_PLANT``).
PREFIX_TO_PLANT = {
    "OGSES": 6180,
    "SANMIGL": 6183,
    "TNP_ONE": 7030,
    "MLSES": 6146,
    "LEG": 298,
    "WAP": 3470,
    "COLETO": 6178,
    "FPPYD": 6179,
    "CALAVERS": 7097,
    "SCES": 56611,
}
PLANT_NAMES = {
    298: "Limestone",
    3470: "W A Parish",
    6146: "Martin Lake",
    6178: "Coleto Creek",
    6179: "Fayette",
    6180: "Oak Grove",
    6183: "San Miguel",
    7030: "Major Oak",
    7097: "JK Spruce",
    56611: "Sandy Creek",
}
#: Self-schedule floor excluded from level statistics
#: (``constants.COAL_PERPLANT_SELF_SCHED_FLOOR`` convention).
FLOOR = -249.0
MW = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
PR = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
#: C1 COAL_PRB misses on the keeper (charter), TWh.
PRB_MISS = {2019: 10.5, 2020: 11.8}
WINDOW = (2022, 2025)


def load_dam_coal() -> pd.DataFrame:
    """Every on-disk delivery-2022..2025 CLLIG row of the 60-Day DAM disclosure."""
    files = sorted(
        set(RAW.glob("60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"))
        | set(
            (RAW / "DAM").glob(
                "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"
            )
        )
    )
    cols = (
        [
            "Delivery Date",
            "Hour Ending",
            "Resource Name",
            "Resource Type",
            "HSL",
            "LSL",
            "Resource Status",
            "Awarded Quantity",
        ]
        + MW
        + PR
    )
    frames = []
    for f in files:
        t = pq.read_table(f, columns=cols).to_pandas()
        frames.append(t[t["Resource Type"].astype(str) == "CLLIG"])
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d["Delivery Date"].astype(str), format="mixed")
    d = d.drop_duplicates(["date", "Hour Ending", "Resource Name"])
    d["plant"] = (
        d["Resource Name"]
        .astype(str)
        .map(
            lambda r: next(
                (c for p, c in PREFIX_TO_PLANT.items() if r.startswith(p)), None
            )
        )
    )
    d = d[d["plant"].notna()]
    for c in MW + PR + ["HSL", "LSL", "Awarded Quantity"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["year"] = d["date"].dt.year
    return d[d["year"].between(*WINDOW)].reset_index(drop=True)


def curve_points(d: pd.DataFrame) -> pd.DataFrame:
    """Attach each row's modal-construction key and (mw, price) points."""
    P, M = d[PR].to_numpy(float), d[MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    keys, pts = [], []
    for i in range(len(d)):
        if ok[i].any():
            o = np.argsort(M[i][ok[i]])
            keys.append(tuple(np.round(np.sort(P[i][ok[i]]), 2)))
            pts.append(list(zip(M[i][ok[i]][o], P[i][ok[i]][o])))
        else:
            keys.append(None)
            pts.append(None)
    d = d.assign(key=keys, pts=pts)
    return d[d["key"].notna()]


def merge(curves: list) -> list[tuple[float, float]]:
    """Merge unit step curves into one price-sorted plant curve (ERCOT-144 form)."""
    segs = []
    for pts in curves:
        mw = np.array([p[0] for p in pts], float)
        pr = np.array([p[1] for p in pts], float)
        w = np.diff(np.concatenate([[0.0], mw]))
        segs += [(float(w[k]), float(pr[k])) for k in range(len(pr)) if w[k] > 0]
    segs.sort(key=lambda s: s[1])
    out, cum = [], 0.0
    for w, p in segs:
        cum += w
        out.append((cum, p))
    return out


def level(curve) -> tuple[float, float]:
    """Capacity-weighted mean price over a cumulative curve, floor points excluded."""
    cm = np.array([c[0] for c in curve], float)
    pr = np.array([c[1] for c in curve], float)
    w = np.diff(np.concatenate([[0.0], cm]))
    m = (pr > FLOOR) & (w > 0)
    if not m.any():
        return float("nan"), 0.0
    return float((w[m] * pr[m]).sum() / w[m].sum()), float(w[m].sum())


def modal(g: pd.DataFrame):
    """The most-submitted curve of one resource and its row share."""
    k, n = Counter(g["key"]).most_common(1)[0]
    return g[g["key"] == k]["pts"].iloc[0], n / len(g)


def coverage(d: pd.DataFrame) -> pd.DataFrame:
    """Per plant-year DAM curve coverage of the plant's ON HSL-hours."""
    d = d.assign(
        on=d["Resource Status"].astype(str).str.startswith("ON"),
        has=d[PR].notna().any(axis=1),
        cmax=d[MW].max(axis=1),
    )
    on = d[d["on"]]
    rows = []
    for (pl, y), g in on.groupby(["plant", "year"]):
        offered = (g["cmax"] - g["LSL"]).clip(lower=0)[g["has"]].sum()
        rows.append(
            {
                "plant": int(pl),
                "name": PLANT_NAMES[int(pl)],
                "year": int(y),
                "on_hours_share_with_curve": round(float(g["has"].mean()), 3),
                "offered_mw_share_of_on_hsl": round(
                    float(offered / max(g["HSL"].sum(), 1)), 3
                ),
                "dam_awarded_twh": round(float(g["Awarded Quantity"].sum() / 1e6), 2),
            }
        )
    fleet = {
        int(y): round(
            float(
                ((g["cmax"] - g["LSL"]).clip(lower=0)[g["has"]].sum()) / g["HSL"].sum()
            ),
            3,
        )
        for y, g in on.groupby("year")
    }
    return pd.DataFrame(rows), fleet


def dam_levels(d: pd.DataFrame) -> pd.DataFrame:
    """Per plant-year DAM modal merged-curve level (PRECOMMIT §2)."""
    rows = []
    for (y, pl), g in d.groupby(["year", "plant"]):
        cur, sh = zip(*[modal(gr) for _, gr in g.groupby("Resource Name")])
        lv, mw = level(merge(list(cur)))
        rows.append(
            {
                "year": int(y),
                "plant": int(pl),
                "name": PLANT_NAMES[int(pl)],
                "dam_level": round(lv, 2),
                "dam_mw": round(mw),
                "modal_share": round(float(np.mean(sh)), 2),
            }
        )
    return pd.DataFrame(rows)


def sced_levels() -> pd.DataFrame:
    """The keeper's SCED-basis levels: static 2024-25 curves and the 2023 table."""
    sc = json.loads((BUNDLE / "run_config_2024.json").read_text())["scenario_config"]
    static = sc["coal_perplant_offer_curves"]
    y23 = sc["coal_perplant_offer_curves_yearly"]["2023"]
    rows = []
    for p, c in static.items():
        lv, _ = level(c)
        acc = tot = 0.0
        for months, hours, curve in y23.get(p, []):
            n = len(months) * len(hours)
            acc += n * level(curve)[0]
            tot += n
        rows.append(
            {
                "plant": int(p),
                "static_level": round(lv, 2),
                "static_mw": float(c[-1][0]),
                "y2023_level": round(acc / tot, 2) if tot else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def required_shift() -> dict:
    """Δ*: static re-dispatch gain of COAL_PRB committed/econ tranches vs offer shift."""
    out = {}
    for y, miss in PRB_MISS.items():
        u = pd.read_parquet(BUNDLE / "hourly" / f"unit_marginal_{y}.parquet")
        u = u[u["pass"].astype(str) == "P1"]
        s = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
        s = s[s["pass"].astype(str) == "P1"][["zone", "hour", "price"]]
        c = u[u["plant_group"].astype(str) == "COAL_PRB"].merge(s, on=["zone", "hour"])
        tr = c["unit_id"].astype(str).str.extract(r"_(committed|econ\w*)$")[0]
        c = c[tr.notna()]
        head = (c["cap_mw"] - c["mw"]).clip(lower=0)
        gap = c["mc"] - c["price"]
        grid = np.round(np.arange(0, 20.01, 0.05), 2)
        gain = np.array([head[(gap < g) & (head > 0.5)].sum() / 1e6 for g in grid])
        dstar = float(np.interp(miss, gain, grid))
        out[y] = {
            "miss_twh": miss,
            "delta_star": round(dstar, 2),
            "gain_at": {
                str(g): round(float(v), 2)
                for g, v in zip(grid, gain)
                if g in (1.0, 2.0, 3.0, 4.0, 5.0, 10.0)
            },
        }
    return out


def main() -> None:
    """Run the census and write the three outputs."""
    OUT.mkdir(parents=True, exist_ok=True)
    d = load_dam_coal()
    cov, fleet_cov = coverage(d)
    lv = dam_levels(curve_points(d)).merge(sced_levels(), on="plant", how="left")
    hh = pd.read_csv(REPO / "data" / "raw" / "gas-prices" / "henry_hub_monthly.csv")
    hh = hh.groupby("year")["price_usd_mmbtu"].mean()
    ds = required_shift()
    thr = max(1.0, 0.25 * min(v["delta_star"] for v in ds.values()))

    a = lv[lv["year"] == 2023].assign(bias=lambda x: x["dam_level"] - x["y2023_level"])
    b = lv[lv["year"].isin([2024, 2025])].assign(
        bias=lambda x: x["dam_level"] - x["static_level"]
    )
    p1 = {}
    for tag, x in (("a_2023_vs_ercot168", a), ("b_2024_25_vs_static", b)):
        fb = float(np.average(x["bias"], weights=x["dam_mw"]))
        n2 = int((x["bias"].abs() <= 2.0).sum())
        p1[tag] = {
            "fleet_bias": round(fb, 2),
            "within_2": n2,
            "n": len(x),
            "pass": bool(abs(fb) <= thr and n2 >= 8),
        }

    q = lv[lv.groupby("plant")["year"].transform("count") >= 3].copy()
    q["hh"] = q["year"].map(hh)
    x = (q["hh"] - q.groupby("plant")["hh"].transform("mean")).to_numpy()
    yv = (q["dam_level"] - q.groupby("plant")["dam_level"].transform("mean")).to_numpy()
    w = q["dam_mw"].to_numpy(float)
    bh = float((w * x * yv).sum() / (w * x * x).sum())
    dof = len(q) - q["plant"].nunique() - 1
    se = float(np.sqrt((w * (yv - bh * x) ** 2).sum() / dof / (w * x * x).sum()))
    fl = q.groupby("year").apply(
        lambda g: np.average(g["dam_level"], weights=g["dam_mw"])
    )
    base = float(hh.loc[[2024, 2025]].mean())
    q3 = {
        "slope": round(bh, 2),
        "se": round(se, 2),
        "t": round(bh / se, 2),
        "n_plant_years": len(q),
        "n_plants": int(q["plant"].nunique()),
        "fleet_level_by_year": {int(k): round(float(v), 2) for k, v in fl.items()},
        "predicted_shift": {y: round(bh * (float(hh[y]) - base), 2) for y in PRB_MISS},
    }

    cov.to_csv(OUT / "dam_proxy_coverage.csv", index=False)
    lv.to_csv(OUT / "dam_proxy_levels.csv", index=False)
    summary = {
        "henry_hub": {int(k): round(float(v), 2) for k, v in hh.loc[2019:2025].items()},
        "fleet_offered_mw_share_of_on_hsl": fleet_cov,
        "delta_star": ds,
        "p1_threshold": round(thr, 2),
        "p1": p1,
        "q3": q3,
    }
    (OUT / "dam_proxy_summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
