"""closeout-SOCO-w2 zero-LP reach: SOCO coal econ/peak tranches at same-month EIA-923 Page-5 spot receipts.

Plan docs/backcast-closeout-plan-2026-10.md §3.8 step 1 (L1). Method and bars fixed ex ante in
docs/records/soco/closeout-soco-w2/PRECOMMIT-phase0-closeout-soco-w2-2026-10-03.md:

1. per coal econ/peak unit, HR = OLS slope of monthly mean P1 mc on the plant-month F923 coal price;
2. Δmc = HR x (spot - blended), forms F1 (plant same-month spot) and F2 (F1 else plant same-year spot);
3. hourly copperplate restack of the econ/peak tranches (everything else, and floor-bound coal, held at keeper mw);
4. delta method onto the keeper's prices and class energies; C1 via calibration_verdict.score_fuelmix, C3a/C3b via
   score_price_mean / score_price_shape on an edited payload.

Keeper: results/calibration/closeout_soco_3_span (2026-10-03-closeout-soco-3-coalpile). No LP.
Outputs: docs/records/soco/closeout-soco-w2/{spot_hr,spot_reach,spot_validity}.csv.
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
sys.path.insert(0, str(REPO / "scripts"))
import calibration_verdict as cv  # noqa: E402

KEEPER = REPO / "results/calibration/closeout_soco_3_span/hourly"
RUN = "2026-10-03-closeout-soco-3-coalpile"
OUT = REPO / "docs/records/soco/closeout-soco-w2"
YEARS = range(2019, 2026)
COAL = ("COAL_BIT", "COAL_PRB")
FLEX = ("econlo", "econhi", "econ", "peak")
FLOOR_TOL = 1.0  # $/MWh above zone price that marks a floor-bound coal unit-hour (PRECOMMIT §3.3)
HR_BAND = (
    8.0,
    14.0,
)  # MMBtu/MWh plausibility band for the fitted slope (PRECOMMIT §3.1)
HR_R2 = 0.8
GM_KEYS = [
    "CC_REGULAR",
    "COAL_BIT",
    "COAL_PRB",
    "ST_GAS",
    "CT_PEAKER",
    "CC_CHP",
    "ST_CHP",
    "CT_CHP",
]


def load_payload() -> dict:
    """Return the keeper's decoded dashboard payload."""
    t = (REPO / f"frontend/data/backcast/runs/{RUN}.js").read_text()
    return json.loads(
        gzip.decompress(
            base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1))
        )
    )


def spot_prices(y: int) -> tuple[pd.Series, pd.Series]:
    """Return (plant-month, plant-year) MMBtu-weighted Page-5 spot delivered $/MMBtu for year ``y``."""
    r = pd.read_csv(
        REPO / f"data/raw/coal-receipts/coal_receipts_{y}.csv", low_memory=False
    )
    for c in ("QUANTITY", "Average Heat Content", "FUEL_COST"):
        r[c] = pd.to_numeric(r[c], errors="coerce")
    r = r[(r["Purchase Type"].astype(str).str.strip() == "S") & r.FUEL_COST.notna()]
    r["mm"] = r.QUANTITY * r["Average Heat Content"]
    r["usd"] = r.mm * r.FUEL_COST / 100.0
    g = r.groupby(["Plant Id", "MONTH"])[["usd", "mm"]].sum()
    a = r.groupby("Plant Id")[["usd", "mm"]].sum()
    return (g.usd / g.mm).rename("spot"), (a.usd / a.mm).rename("spot_y")


def restack(
    mc: np.ndarray, cap: np.ndarray, energy: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Fill ``energy[t]`` from units (rows) in ascending ``mc[:, t]``; return (dispatch, marginal mc per hour)."""
    n, T = mc.shape
    disp = np.zeros_like(cap)
    price = np.zeros(T)
    for t in range(T):
        o = np.argsort(mc[:, t], kind="stable")
        cs = np.cumsum(cap[o, t])
        k = int(np.searchsorted(cs, energy[t] - 1e-6))
        k = min(k, n - 1)
        d = np.zeros(n)
        d[o[:k]] = cap[o[:k], t]
        d[o[k]] = max(0.0, energy[t] - (cs[k - 1] if k > 0 else 0.0))
        disp[:, t] = d
        price[t] = mc[o[k], t]
    return disp, price


def year_reach(y: int, fc: pd.DataFrame) -> tuple[list[dict], dict, list[dict]]:
    """Return (HR rows, per-form arm deltas, validity rows) for year ``y``."""
    u = pd.read_parquet(
        KEEPER / f"unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    u["tr"] = u.unit_id.astype(str).str.extract(r"_([a-z]+)$")[0]
    s = pd.read_parquet(KEEPER / f"system_{y}.parquet")
    zp = s.groupby("hour").price.mean().reindex(range(8760)).to_numpy()
    month = pd.date_range(f"{y}-01-01", periods=8760, freq="h").month.to_numpy()
    u["m"] = month[u.hour.to_numpy()]
    flex = u[u.tr.isin(FLEX) & ~u.plant_group.isin(["hydro", ""])].copy()
    # floor-bound coal unit-hours are held at keeper mw (PRECOMMIT §3.3)
    iscoal = flex.plant_group.isin(COAL).to_numpy()
    bound = (
        iscoal
        & (flex.mw.to_numpy() > 0)
        & (flex.mc.to_numpy() > zp[flex.hour.to_numpy()] + FLOOR_TOL)
    )
    flex = flex[~bound]
    units = sorted(flex.unit_id.astype(str).unique())
    idx = {k: i for i, k in enumerate(units)}
    ui = flex.unit_id.astype(str).map(idx).to_numpy()
    h = flex.hour.to_numpy()
    MC = np.full((len(units), 8760), 1e4)
    CAP = np.zeros((len(units), 8760))
    MW = np.zeros((len(units), 8760))
    MC[ui, h], CAP[ui, h], MW[ui, h] = flex.mc, flex.cap_mw, flex.mw
    meta = flex.drop_duplicates("unit_id").set_index(
        flex.drop_duplicates("unit_id").unit_id.astype(str)
    )
    E = MW.sum(axis=0)
    # HR per coal econ/peak unit: slope of monthly mean mc on F923 blended coal price
    blend = (
        fc[(fc.year == y) & (fc.fuel_group == "Coal")]
        .groupby(["plant_id", "month"])
        .price_per_mmbtu.mean()
    )
    sp_m, sp_y = spot_prices(y)
    hr_rows = []
    dmc = {"F1": np.zeros_like(MC), "F2": np.zeros_like(MC)}
    cu = u[u.plant_group.isin(COAL) & u.tr.isin(FLEX)]
    mm = (
        cu.groupby(["unit_id", "plant_code", "plant_group", "m"], observed=True)
        .mc.mean()
        .reset_index()
    )
    fits = {}
    for (uid, pc, pg), g in mm.groupby(
        ["unit_id", "plant_code", "plant_group"], observed=True
    ):
        b = np.array([blend.get((pc, m), np.nan) for m in g.m])
        ok = np.isfinite(b) & (g.mc.to_numpy() < 1e3)
        slope, r2 = np.nan, np.nan
        if ok.sum() >= 4 and np.ptp(b[ok]) > 0.05:
            x, yv = b[ok], g.mc.to_numpy()[ok]
            slope, icpt = np.polyfit(x, yv, 1)
            r2 = 1 - ((yv - (slope * x + icpt)) ** 2).sum() / max(
                ((yv - yv.mean()) ** 2).sum(), 1e-9
            )
        fits[str(uid)] = dict(unit_id=str(uid), plant=pc, cls=pg, hr_fit=slope, r2=r2)
    fdf = pd.DataFrame(fits.values())
    good = fdf.hr_fit.between(*HR_BAND) & (fdf.r2 >= HR_R2)
    med = fdf[good].groupby("plant").hr_fit.median()
    cls_med = fdf[good].groupby("cls").hr_fit.median()
    fdf["hr"] = np.where(
        good, fdf.hr_fit, fdf.plant.map(med).fillna(fdf.cls.map(cls_med))
    )
    fdf["hr_src"] = np.where(good, "fit", "plant/class median")
    for r in fdf.itertuples():
        hr_rows.append(dict(year=y, **r._asdict()))
        if r.unit_id not in idx or not np.isfinite(r.hr):
            continue
        i = idx[r.unit_id]
        for mo in range(1, 13):
            bl = blend.get((r.plant, mo), np.nan)
            if not np.isfinite(bl):
                continue
            sel = month == mo
            s1 = sp_m.get((r.plant, mo), np.nan)
            s2 = s1 if np.isfinite(s1) else sp_y.get(r.plant, np.nan)
            if np.isfinite(s1):
                dmc["F1"][i, sel] = r.hr * (s1 - bl)
            if np.isfinite(s2):
                dmc["F2"][i, sel] = r.hr * (s2 - bl)
    disp0, p0 = restack(MC, CAP, E)
    # validity (PRECOMMIT §3.5): restack base vs keeper load-weighted price
    dem = s.groupby("hour").demand.sum().reindex(range(8760)).to_numpy()
    lw_k = (zp * dem).sum() / dem.sum()
    lw_r = (p0 * dem).sum() / dem.sum()
    valid = dict(
        year=y,
        lw_keeper=lw_k,
        lw_restack=lw_r,
        err_pct=100 * (lw_r / lw_k - 1),
        r_hourly=float(np.corrcoef(p0, zp)[0, 1]),
        floor_bound_unit_hours=int(bound.sum()),
    )
    valid["ok"] = abs(valid["err_pct"]) <= 5.0 and valid["r_hourly"] >= 0.85
    cls = meta.plant_group.astype(str).reindex(units).to_numpy()
    # keeper marginal unit per hour (unit_marginal flag) for the same-setter reading and the coal-setter share
    marg = pd.read_parquet(
        KEEPER / f"unit_marginal_{y}.parquet", columns=["unit_id", "hour", "marginal"]
    )
    marg = (
        marg[marg.marginal == 1]
        .drop_duplicates("hour")
        .set_index("hour")
        .unit_id.astype(str)
        .reindex(range(8760))
    )
    mi = marg.map(idx)
    coal_set = np.array(
        [
            isinstance(v, str) and v in idx and cls[idx[v]] in COAL
            for v in marg.to_numpy()
        ]
    )
    valid["coal_setter_hour_share"] = float(coal_set.mean())
    arms = {}
    for f in ("F1", "F2"):
        disp1, p1 = restack(MC + dmc[f], CAP, E)
        dE = {c: float((disp1 - disp0)[cls == c].sum()) / 1e6 for c in set(cls)}
        dp = p1 - p0
        if not valid["ok"]:
            # same-setter greedy (PRECOMMIT §3.5): price moves by the setter's Δmc, capped at the next stack unit
            dp = np.zeros(8760)
            for t in np.flatnonzero(coal_set):
                i = int(mi.iloc[t])
                d = dmc[f][i, t]
                if d > 0:
                    above = MC[:, t][
                        (MC[:, t] > MC[i, t]) & (CAP[:, t] > MW[:, t] + 1e-6)
                    ]
                    d = min(d, (above.min() - MC[i, t]) if above.size else d)
                dp[t] = d
        arms[f] = dict(
            dp=dp,
            dE=dE,
            n_spot_unit_months=int((np.abs(dmc[f]) > 0).any(axis=1).sum()),
            mean_dmc_coal=float(dmc[f][np.abs(dmc[f]) > 0].mean())
            if (np.abs(dmc[f]) > 0).any()
            else 0.0,
        )
    return hr_rows, dict(arms=arms, s=s, valid=valid), [valid]


def score_year(
    y: int, P: dict, yb: dict, s: pd.DataFrame, dp: np.ndarray | None, dE: dict | None
) -> dict:
    """Return C1 / C3a / C3b records for the keeper (dp None) or an arm."""
    yp = json.loads(json.dumps(P["years"][str(y)]))
    if dp is not None:
        month = pd.date_range(f"{y}-01-01", periods=8760, freq="h").month.to_numpy() - 1
        for z, zd in yp["lmp"].items():
            sz = s[s.zone == z].set_index("hour").reindex(range(8760))
            p = sz.price.to_numpy() + dp
            d = sz.demand.to_numpy()
            zd["p"] = float((p * d).sum() / d.sum())
            zd["pMon"] = [
                float((p[month == m] * d[month == m]).sum() / d[month == m].sum())
                for m in range(12)
            ]
        for c, v in (dE or {}).items():
            if c in yp["gmModel"]:
                yp["gmModel"][c] = yp["gmModel"][c] + v
    out = {}
    for r in cv.score_fuelmix(y, yp, yb, iso="SOCO"):
        out[("C1", r.get("key"))] = (r.get("status"), r.get("magnitude"))
    r = cv.score_price_mean(y, yp, yb, "SOCO")
    out[("C3a", None)] = (r.get("status"), r.get("magnitude"))
    r = cv.score_price_shape(y, yp, yb, "SOCO")
    out[("C3b", None)] = (r.get("status"), r.get("magnitude"))
    return out


def main() -> None:
    """Run the reach for every keeper year and write the three CSVs."""
    fc = pd.read_parquet(
        REPO / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
    )
    P = load_payload()
    hr_all, val_all, rows = [], [], []
    for y in YEARS:
        hr_rows, res, val = year_reach(y, fc)
        hr_all += hr_rows
        val_all += val
        yb = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SOCO/{y}.json.gz")
        )["bench"]
        base = score_year(y, P, yb, res["s"], None, None)
        for f, a in res["arms"].items():
            arm = score_year(
                y, P, yb, res["s"], a["dp"], a["dE"] if res["valid"]["ok"] else None
            )
            for k in base:
                rows.append(
                    dict(
                        year=y,
                        form=f,
                        crit=k[0],
                        key=k[1],
                        keeper=base[k][0],
                        keeper_mag=base[k][1],
                        arm=arm.get(k, (None, None))[0],
                        arm_mag=arm.get(k, (None, None))[1],
                    )
                )
            rows.append(
                dict(
                    year=y,
                    form=f,
                    crit="dE_TWh",
                    key=json.dumps({c: round(v, 3) for c, v in a["dE"].items()}),
                    keeper=None,
                    keeper_mag=None,
                    arm=a["n_spot_unit_months"],
                    arm_mag=round(a["mean_dmc_coal"], 2),
                )
            )
        print(
            y,
            res["valid"],
            {
                f: (a["n_spot_unit_months"], round(a["mean_dmc_coal"], 2))
                for f, a in res["arms"].items()
            },
        )
    pd.DataFrame(hr_all).to_csv(OUT / "spot_hr.csv", index=False)
    pd.DataFrame(val_all).to_csv(OUT / "spot_validity.csv", index=False)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "spot_reach.csv", index=False)
    pd.set_option("display.width", 250, "display.max_rows", 500)
    print(
        df[
            (df.crit != "C1")
            | df.key.isin(["CC_REGULAR", "COAL_BIT", "COAL_PRB", "ST_GAS", "CT_PEAKER"])
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
