"""soco-94 zero-LP C3a year-pattern diagnosis: why does SOCO's C3a miss flip sign with
the gas year (over at HH $2.0-2.6 in 2019/2020, under at $6.45 in 2022)?

Owner ruling 2026-09-30 (soco-93 card "Next lane"): "C3a year-pattern diagnosis".
Rule 32 ``[R-SHARD]`` (a): this never solves. Per year it does one ``fleet_only``
rebuild of the keeper recipe (``results/calibration/soco96_span``, the soco-89/91
construction) and reads the keeper's committed hourly sidecars and Southern's FERC-714
lambda on the bench's dense CST 8760.

Decompositions of the load-weighted gap ``P - lambda``:

1. by lambda band (low-40 % / mid / top-20 %, the soco-89 instrument);
2. by price-setting class (soco-91 setter rule: offer within ``TOL`` of the price AND
   the setter's class-band interior that hour);
3. in setter-matched hours, the setter offer is split into
   ``HR x fuel_model + (mc_base - HR x fuel_model)`` and the model fuel is compared
   with the delivered price that SAME PLANT paid that MONTH (EIA-923 Schedule 2,
   ``_processed-legacy/eia923_monthly_fuel_costs.parquet``, gas and coal separately).
   ``fuel_err = HR x (fuel_model - fuel_F923)`` is the part of the gap a measured
   plant-month delivered price would remove, first order (same setter, no re-stack).

It also reports the fleet-level fuel check (model fuel vs quantity-weighted F923
delivered, by fuel and year) and an across-year regression of the annual gaps on the
gas price, which states the year pattern as intercept vs slope.

Usage::

    uv run python scripts/probes/_soco94_year_pattern.py --out DIR [--years ...]
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

from probes import _soco91_intraday_census as p91  # noqa: E402

SPAN = p91.SPAN
T = p91.T
TOL = p91.TOL
EPS_MW = p91.EPS_MW
MONTH = p91.MONTH
YEARS = p91.YEARS
F923 = ROOT / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
GAS = set(p91.GAS)
COAL = set(p91.COAL)


def rebuild(year: int, cache: Path) -> dict:
    """``fleet_only`` rebuild of the keeper recipe with plant codes (cached per year)."""
    f = cache / f"fleet94_{year}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=True)
        return {k: z[k] for k in z.files}
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = copy.deepcopy(json.loads((SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    clear_fleet_caches()
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    fa = st["fleet_arrays"]
    ids = np.array([str(g.unit_id) for g in st["fleet"]])
    klass = np.array(
        [p91._klass(str(g.plant_group), str(g.fuel_type)) for g in st["fleet"]]
    )

    def _2d(a):
        a = np.asarray(a, float)
        return a if a.ndim == 2 else np.repeat(a[:, None], T, 1)

    r = dict(
        ids=ids,
        klass=klass,
        band=np.array([p91._band(u, k) for u, k in zip(ids, klass)]),
        plant=np.array([int(g.plant_code) for g in st["fleet"]]),
        fueltype=np.array([str(g.fuel_type) for g in st["fleet"]]),
        hr=np.asarray(fa.heat_rate, float),
        vom=np.asarray(fa.vom, float),
        fuel=_2d(st["fuel_prices"]).astype(np.float32),
        mc=_2d(st["mc_base"]).astype(np.float32),
        cap=(np.asarray(fa.pmax, float)[:, None] * _2d(fa.availability)).astype(
            np.float32
        ),
        floor=_2d(fa.min_gen).astype(np.float32),
    )
    np.savez(f, **r)
    return r


def f923_plant_month(year: int) -> pd.DataFrame:
    """EIA-923 Sch. 2 delivered $/MMBtu per (plant, month, fuel group), quantity-weighted."""
    d = pd.read_parquet(F923)
    d = d[(d.year == year) & d.fuel_group.isin(["Coal", "Natural Gas"])].copy()
    d = d[np.isfinite(d.price_per_mmbtu) & (d.quantity > 0)]
    d["pq"] = d.price_per_mmbtu * d.quantity
    g = d.groupby(["plant_id", "month", "fuel_group"], as_index=False)[
        ["pq", "quantity"]
    ].sum()
    g["price"] = g.pq / g.quantity
    return g


def _fuel_group(klass: str) -> str | None:
    if klass in GAS:
        return "Natural Gas"
    if klass in COAL:
        return "Coal"
    return None


def setters(year: int, f: dict) -> dict:
    """soco-91 setter attribution; returns per-hour setter unit index (or -1) and labels."""
    s = pd.read_parquet(SPAN / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"].sort_values(["zone", "hour"])
    zn = sorted(s.zone.unique())
    Pz = np.vstack([s[s.zone == z].price.to_numpy() for z in zn])
    Dz = np.vstack([s[s.zone == z].demand.to_numpy() for z in zn])
    D = Dz.sum(0)
    P = (Pz * Dz).sum(0) / D
    cb = pd.read_parquet(SPAN / f"hourly/class_band_hourly_{year}.parquet")
    cb = cb[cb["pass"] == "P1"]
    cb["band"] = cb["band"].astype(str).replace({"": "_"})
    cb["klass"] = cb["klass"].astype(str)
    mw_b = {
        kb: g.set_index("hour").mw.reindex(range(T), fill_value=0.0).to_numpy(float)
        for kb, g in cb.groupby(["klass", "band"])
    }
    stg = pd.read_parquet(SPAN / f"hourly/storage_{year}.parquet")
    stg = stg[stg["pass"] == "P1"]
    ps = stg[stg.tech.astype(str) == "pumped_storage"]
    ps_net = (
        (ps.groupby("hour").discharge_mw.sum() - ps.groupby("hour").charge_mw.sum())
        .reindex(range(T), fill_value=0.0)
        .to_numpy(float)
    )
    kband = np.array(
        [f"{k}|{b if b else '_'}" for k, b in zip(f["klass"], f["band"])], dtype=object
    )
    mc, cap, flo = f["mc"].astype(float), f["cap"].astype(float), f["floor"]
    interior = {}
    for kb in np.unique(kband):
        k, b = kb.split("|")
        m = kband == kb
        c_b = cap[m].sum(0)
        f_b = np.minimum(flo[m].astype(float), cap[m]).sum(0)
        mw = mw_b.get((k, b), np.zeros(T))
        interior[kb] = (mw > f_b + EPS_MW) & (mw < c_b - EPS_MW)
    cand = np.abs(mc - P[None, :]) <= TOL
    ok = cand & np.vstack([interior[kb] for kb in kband])
    dist = np.where(ok, np.abs(mc - P[None, :]), np.inf)
    iu = dist.argmin(0)
    has = np.isfinite(dist[iu, np.arange(T)])
    hyd = interior.get("hydro|_", np.zeros(T, bool)) | (np.abs(ps_net) > EPS_MW)
    label = np.where(
        has, f["klass"][iu], np.where(hyd, "hydro/storage", "UNMATCHED")
    ).astype(object)
    return dict(P=P, D=D, iu=np.where(has, iu, -1), label=label)


def analyse(year: int, cache: Path) -> dict:
    """Year-pattern decomposition for one year."""
    f = rebuild(year, cache)
    st = setters(year, f)
    P, D, iu, label = st["P"], st["D"], st["iu"], st["label"]
    lam = p91.lambda_cst(year)
    gap = P - lam
    W = D / D.sum()
    q40, q80 = np.quantile(lam, [0.4, 0.8])
    bands = {"low40": lam <= q40, "mid": (lam > q40) & (lam <= q80), "top20": lam > q80}
    ar = np.arange(T)
    has = iu >= 0
    iuc = np.where(has, iu, 0)

    # --- setter offer components and measured plant-month delivered fuel ------------
    hr = np.where(has, f["hr"][iuc], np.nan)
    fuel_m = np.where(has, f["fuel"][iuc, ar].astype(float), np.nan)
    mc_s = np.where(has, f["mc"][iuc, ar].astype(float), np.nan)
    other = mc_s - hr * fuel_m  # VOM + any adders in mc_base
    grp = np.array([_fuel_group(str(k)) for k in f["klass"]], dtype=object)
    fg = np.where(has, grp[iuc], None)
    plant = np.where(has, f["plant"][iuc], -1)
    pm = f923_plant_month(year)
    key = {
        (int(r.plant_id), int(r.month), r.fuel_group): float(r.price)
        for r in pm.itertuples()
    }
    fuel_meas = np.full(T, np.nan)
    for h in np.flatnonzero(has & (fg != None)):  # noqa: E711
        fuel_meas[h] = key.get((int(plant[h]), int(MONTH[h]) + 1, fg[h]), np.nan)
    fuel_err = hr * (fuel_m - fuel_meas)  # $/MWh a measured plant-month fuel removes

    def tab(mask: np.ndarray) -> dict:
        w = W * mask
        tot = w.sum()
        out = dict(
            share_of_load=round(float(tot), 3),
            gap_contrib=round(float((W * gap)[mask].sum()), 3),
            P=round(float(np.average(P[mask], weights=D[mask])), 2),
            lam=round(float(np.average(lam[mask], weights=D[mask])), 2),
        )
        cls = {}
        for c in pd.unique(label[mask]):
            m = mask & (label == c)
            mm = m & np.isfinite(fuel_meas)
            e = dict(
                share=round(float(w[m].sum() / tot), 3),
                contrib=round(float((W * gap)[m].sum()), 3),
                P=round(float(np.average(P[m], weights=D[m])), 2),
                lam=round(float(np.average(lam[m], weights=D[m])), 2),
            )
            if np.isfinite(hr[m]).any():
                e.update(
                    hr=round(float(np.average(hr[m], weights=D[m])), 3),
                    fuel_model=round(float(np.average(fuel_m[m], weights=D[m])), 3),
                    other=round(float(np.average(other[m], weights=D[m])), 2),
                )
            if mm.any():
                e.update(
                    f923_cover=round(float(D[mm].sum() / D[m].sum()), 3),
                    fuel_f923=round(float(np.average(fuel_meas[mm], weights=D[mm])), 3),
                    fuel_model_cov=round(
                        float(np.average(fuel_m[mm], weights=D[mm])), 3
                    ),
                    fuel_err=round(float(np.average(fuel_err[mm], weights=D[mm])), 2),
                    fuel_err_contrib=round(float((W * fuel_err)[mm].sum()), 3),
                )
            cls[str(c)] = e
        out["by_setter"] = dict(sorted(cls.items(), key=lambda kv: -kv[1]["share"]))
        mm = mask & np.isfinite(fuel_meas)
        out["fuel_err_contrib"] = round(float((W * fuel_err)[mm].sum()), 3)
        return out

    res = dict(
        year=year,
        model_lw=round(float((W * P).sum()), 3),
        lam_lw=round(float((W * lam).sum()), 3),
        matched=round(float(W[has].sum()), 3),
        f923_covered=round(float(W[np.isfinite(fuel_meas)].sum()), 3),
    )
    res["c3a_pct"] = round(100 * (res["model_lw"] / res["lam_lw"] - 1), 2)
    res["all"] = tab(np.ones(T, bool))
    res["bands"] = {b: tab(m) for b, m in bands.items()}
    fe_all = float((W * np.nan_to_num(fuel_err))[np.isfinite(fuel_meas)].sum())
    res["c3a_if_setter_fuel_f923_pct"] = round(
        100 * ((res["model_lw"] - fe_all) / res["lam_lw"] - 1), 2
    )

    # --- fleet-level fuel check: model vs F923, quantity-weighted, by fuel ----------
    fleet = {}
    live = f["cap"].astype(float).sum(1) > 0
    for fgn in ("Natural Gas", "Coal"):
        u = live & (grp == fgn)
        plants = np.unique(f["plant"][u])
        mrows, rows = [], []
        for p in plants:
            k = u & (f["plant"] == p)
            for mth in range(12):
                v = key.get((int(p), mth + 1, fgn))
                if v is None:
                    continue
                q = pm[
                    (pm.plant_id == p) & (pm.month == mth + 1) & (pm.fuel_group == fgn)
                ].quantity.iloc[0]
                hrs = MONTH == mth
                fm = float(
                    np.average(
                        f["fuel"][k][:, hrs].mean(1), weights=f["cap"][k].sum(1) + 1e-9
                    )
                )
                mrows.append(fm * q)
                rows.append((v * q, q))
        if rows:
            qsum = sum(r[1] for r in rows)
            fleet[fgn] = dict(
                plants=int(len(plants)),
                f923=round(float(sum(r[0] for r in rows) / qsum), 3),
                model=round(float(sum(mrows) / qsum), 3),
            )
    res["fleet_fuel"] = fleet
    return res


def regress(rows: list[dict], hh: dict) -> dict:
    """Across-year OLS of annual model and lambda LW means on the HH price."""
    x = np.array([hh[r["year"]] for r in rows])
    out = {}
    for k in ("model_lw", "lam_lw"):
        y = np.array([r[k] for r in rows])
        b, a = np.polyfit(x, y, 1)
        out[k] = dict(intercept=round(float(a), 2), slope=round(float(b), 3))
    return out


def main() -> None:
    """Run the diagnosis for the requested years and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads((SPAN / "meta.json").read_text())
    rows = []
    for y in a.years:
        r = analyse(y, out)
        r["gas_override"] = float(meta["gas_prices"][str(y)])
        (out / f"year_{y}.json").write_text(json.dumps(r, indent=1))
        rows.append(r)
        print(
            f"{y} HH {r['gas_override']:.2f}: C3a {r['c3a_pct']:+.1f} -> "
            f"{r['c3a_if_setter_fuel_f923_pct']:+.1f} (setter fuel=F923) "
            f"matched {r['matched']:.2f} f923 {r['f923_covered']:.2f} "
            f"fleet {r['fleet_fuel']}"
        )
    if len(rows) > 2:
        reg = regress(rows, {r["year"]: r["gas_override"] for r in rows})
        (out / "regression.json").write_text(json.dumps(reg, indent=1))
        print(reg)


if __name__ == "__main__":
    main()
