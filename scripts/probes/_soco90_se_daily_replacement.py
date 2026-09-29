"""soco-90 zero-LP greedy: SOCO gas units at a daily REPLACEMENT fuel price.

Owner rulings 2026-09-29 (soco-89 cards): "Reopen joint repair" and "License SE
daily gas". Southern's FERC-714 Sch. 6 lambda is incremental cost x REPLACEMENT
fuel; the keeper prices gas at EIA-923 DELIVERED (monthly level x Henry Hub
daily shape). This probe re-prices every SOCO gas unit at a daily replacement
price and re-scores C3a / C3b / C1 on the keeper's committed bundle. Rule 32
``[R-SHARD]`` (a): it never solves. It writes only under ``--out``.

Series (``--series``):

``hh``        Henry Hub daily (committed, public domain). This is the SE-basis = 0
              REFERENCE, not a candidate: "replacement = Henry Hub commodity" is
              refused (FINDING-soco-85 §7, not year-consistent). It fixes what the
              licensed series can add on top of Henry Hub: SE hub minus HH.
``licensed``  The owner-licensed Southeast daily hub file (gitignored, never
              committed; contract in ``data/raw/gas-prices/licensed/README.md``).
              ``--hub`` picks the hub column value (default SNG).

Replacement delivered price, per calendar day d (one construction, every year):

    fuel_d = hub_d / (1 - retention_y) + usage_y

``retention_y`` / ``usage_y`` are the pipeline's published FERC-tariff fuel
retention and firm usage (commodity) charge, from ``--transport-csv``
(``year,usage_usd_mmbtu,fuel_retention_frac``). No such table is committed for
SOCO, so the default is 0 / 0 and the output is flagged ``transport=none``.
Nothing is fitted: there is no free parameter in this construction.

Day -> hour mapping: calendar day d prices CST hours 0-23 of d, the same clock
the armed ``gas_daily_shape`` uses. Non-trading days carry the last print
forward (the ``_trade_date_staircase`` convention) unless the file supplies a
flow-date row for them.

Outputs per year: C3a / C3b / C1 keeper -> arm, the soco-89 lambda-quintile
decomposition (low 40 % / top 20 %) before and after, and the REQUIRED hub
premium over the arm's series in gas-marginal hours (the gap divided by the
greedy marginal unit's heat rate; a first-order bound, no re-ordering).

Usage::

    uv run python scripts/probes/_soco90_se_daily_replacement.py --out S --series hh
    uv run python scripts/probes/_soco90_se_daily_replacement.py --out S --series licensed \
        --hub SNG --transport-csv data/raw/gas-prices/licensed/sng_transport.csv
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

KEEPER = "2026-09-29-soco87-gas-hh-monthly"
SPAN = ROOT / "results/calibration/soco87_span"
YEARS = tuple(range(2019, 2026))
T = 8760
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH = np.repeat(np.arange(12), np.array(_DAYS) * 24)
HH_DAILY = ROOT / "data/raw/gas-prices/henry_hub_daily.csv"
LICENSED = ROOT / "data/raw/gas-prices/licensed/se_daily_hub.csv"
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
RESTACK = GAS + ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC", "oil")
C1_KEYS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB")


def _band(uid: str) -> str:
    s = uid.rsplit("_", 1)[-1]
    for b in ("committed", "econlo", "econhi", "peak", "mustrun", "econ"):
        if s.startswith(b):
            return b
    return s


def rebuild(year: int, cache: Path) -> dict:
    """``fleet_only`` rebuild of the keeper recipe (cached per year)."""
    f = cache / f"fleet_{year}.npz"
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
    mc = np.asarray(st["mc_base"], float)
    fuel = np.asarray(st["fuel_prices"], float)
    r = dict(
        ids=np.array([str(g.unit_id) for g in st["fleet"]]),
        klass=np.asarray(fa.plant_group).astype(str),
        hr=np.asarray(fa.heat_rate, float),
        fuel=fuel if fuel.ndim == 2 else np.repeat(fuel[:, None], T, 1),
        mc=mc if mc.ndim == 2 else np.repeat(mc[:, None], T, 1),
        pmax=np.asarray(fa.pmax, float),
        avail=np.asarray(fa.availability, float),
    )
    np.savez(f, **r)
    return r


def daily_series(path: Path, year: int, hub: str | None) -> np.ndarray:
    """Hourly replacement hub price: calendar-day staircase, CST hours 0-23 of d."""
    d = pd.read_csv(path, parse_dates=["date"])
    if hub is not None:
        d = d[d["hub"] == hub]
        col = "price_usd_mmbtu"
    else:
        col = [c for c in d.columns if c != "date"][0]
    s = d.set_index("date")[col].astype(float).sort_index()
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[~((days.month == 2) & (days.day == 29))]
    v = s.reindex(s.index.union(days)).sort_index().ffill().reindex(days)
    if v.isna().any():
        raise ValueError(f"{path.name}: {int(v.isna().sum())} unpriced days in {year}")
    return np.repeat(v.to_numpy(float), 24)[:T]


def transport(path: Path | None, year: int) -> tuple[float, float]:
    """(usage $/MMBtu, fuel retention fraction) for ``year``; (0, 0) when absent."""
    if path is None:
        return 0.0, 0.0
    t = pd.read_csv(path).set_index("year")
    return float(t.loc[year, "usage_usd_mmbtu"]), float(
        t.loc[year, "fuel_retention_frac"]
    )


def _greedy(demand, cap, mc):
    """Merit-order fill (vectorized over t); dispatch, marginal offer, marginal unit."""
    order = np.argsort(mc, axis=0, kind="stable")
    cs = np.take_along_axis(cap, order, axis=0)
    ms = np.take_along_axis(mc, order, axis=0)
    cum = np.cumsum(cs, axis=0)
    fill = np.clip(demand[None, :] - (cum - cs), 0.0, cs)
    out = np.zeros_like(cap)
    np.put_along_axis(out, order, fill, axis=0)
    k = np.clip((cum < demand[None, :] - 1e-6).sum(axis=0), 0, cap.shape[0] - 1)
    ar = np.arange(cap.shape[1])
    return out, ms[k, ar], order[k, ar]


def lambda_cst(year: int) -> np.ndarray:
    """Southern's lambda on the bench builder's dense CST 8760 calendar."""
    from data.derive_actual_lmp import _soco

    _rec, hourly = _soco(year)
    return hourly["rt"].to_numpy(float)


def decompose(P: np.ndarray, D: np.ndarray, lam: np.ndarray) -> dict:
    """soco-89 §2.1: $/MWh contribution of the low 40 % / top 20 % lambda hours."""
    W = D / D.sum()
    gap = W * (P - lam[None, :])
    q = np.quantile(lam, [0.4, 0.8])
    lo = np.broadcast_to(lam <= q[0], P.shape)
    hi = np.broadcast_to(lam > q[1], P.shape)
    return dict(
        low40=round(float(gap[lo].sum()), 2),
        top20=round(float(gap[hi].sum()), 2),
        total=round(float(gap.sum()), 2),
        c3a_pct=round(100 * float((W * P).sum() / (W * lam[None]).sum() - 1), 1),
    )


def run(out: Path, series: str, hub: str | None, tpath: Path | None, years) -> None:
    """Arm minus control per year, re-scored against the committed keeper bench."""
    import calibration_verdict as cv

    art = cv.load_artifacts(KEEPER)
    src = HH_DAILY if series == "hh" else LICENSED
    res = []
    for y in years:
        f = rebuild(y, out)
        band = np.array([_band(u) for u in f["ids"]])
        sel = np.isin(f["klass"], RESTACK) & (band != "mustrun") & (f["pmax"] > 0)
        cap = (f["pmax"][:, None] * f["avail"])[sel]
        mc0 = f["mc"][sel]
        k, hr = f["klass"][sel], f["hr"][sel]
        gas = np.isin(k, GAS)
        usage, ret = transport(tpath, y)
        rep = daily_series(src, y, hub if series == "licensed" else None)
        rep = rep / (1.0 - ret) + usage
        mc1 = mc0.copy()
        mc1[gas] = mc0[gas] + hr[gas, None] * (rep[None, :] - f["fuel"][sel][gas])
        cb = pd.read_parquet(SPAN / f"hourly/class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"] == "P1") & cb.klass.isin(RESTACK) & (cb.band != "mustrun")]
        dem = cb.groupby("hour").mw.sum().reindex(range(T), fill_value=0.0).to_numpy()
        g0, p0, _ = _greedy(dem, cap, mc0)
        g1, p1, m1 = _greedy(dem, cap, mc1)
        dp = p1 - p0
        dcls = {c: float((g1[k == c] - g0[k == c]).sum() / 1e6) for c in set(k)}

        s = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"].sort_values(["zone", "hour"])
        zn = sorted(s.zone.unique())
        P = np.vstack([s[s.zone == z].price.to_numpy() for z in zn])
        D = np.vstack([s[s.zone == z].demand.to_numpy() for z in zn])
        lam = lambda_cst(y)
        before, after = decompose(P, D, lam), decompose(P + dp[None, :], D, lam)

        # required replacement premium over this series in gas-marginal hours
        W = D.sum(0)
        gap_t = ((P + dp[None, :]) * D).sum(0) / W - lam
        gm = gas[m1]
        req = np.where(gm, -gap_t / np.where(hr[m1] > 0, hr[m1], np.nan), np.nan)
        qs = np.quantile(lam, [0.4, 0.8])
        winter = np.isin(MONTH, (0, 1, 11))

        def _wm(mask):
            m = mask & np.isfinite(req)
            return (
                round(float((req[m] * W[m]).sum() / W[m].sum()), 2) if m.any() else None
            )

        # rescore through the verdict's own scorers
        ypay = copy.deepcopy(art["payload"]["years"][str(y)])
        yb = art["bench"].get(y, {})
        base = {
            r["key"]: r
            for r in cv.score_fuelmix(y, ypay, yb, "SOCO")
            if r["status"] != "SKIPPED"
        }
        c3a0 = cv.score_price_mean(y, ypay, yb, "SOCO")
        c3b0 = cv.score_price_shape(y, ypay, yb, "SOCO")
        for c, dv in dcls.items():
            if c in ypay["gmModel"]:
                ypay["gmModel"][c] = float(ypay["gmModel"][c]) + dv
        for zi, z in enumerate(zn):
            if z not in ypay["lmp"]:
                continue
            d, zz = D[zi], ypay["lmp"][z]
            zz["p"] = float(zz["p"]) + float((dp * d).sum() / d.sum())
            zz["pMon"] = [
                float(pm)
                + float((dp[MONTH == i] * d[MONTH == i]).sum() / d[MONTH == i].sum())
                if pm is not None
                else None
                for i, pm in enumerate(zz["pMon"])
            ]
        arm = {
            r["key"]: r
            for r in cv.score_fuelmix(y, ypay, yb, "SOCO")
            if r["status"] != "SKIPPED"
        }
        c3a1 = cv.score_price_mean(y, ypay, yb, "SOCO")
        c3b1 = cv.score_price_shape(y, ypay, yb, "SOCO")
        row = dict(
            year=y,
            series=series if series == "hh" else f"licensed:{hub}",
            transport="none" if tpath is None else tpath.name,
            c3a=f"{c3a0['magnitude']} {c3a0['status']} -> {c3a1['magnitude']} {c3a1['status']}",
            c3b=f"{c3b0.get('model')} {c3b0['status']} -> {c3b1.get('model')} {c3b1['status']}",
            dp_lw=round(float((dp * dem).sum() / dem.sum()), 2),
            low40=f"{before['low40']} -> {after['low40']}",
            top20=f"{before['top20']} -> {after['top20']}",
            req_prem_top20=_wm(lam > qs[1]),
            req_prem_top20_djf=_wm((lam > qs[1]) & winter),
            req_prem_top20_other=_wm((lam > qs[1]) & ~winter),
            req_prem_low40=_wm(lam <= qs[0]),
            gas_marginal_share=round(float(gm.mean()), 2),
            c1=" | ".join(
                f"{c} {base[c]['magnitude']}->{arm[c]['magnitude']} {arm[c]['status']}"
                for c in C1_KEYS
                if c in base and c in arm
            ),
        )
        res.append(row)
        print(json.dumps(row), flush=True)
    tag = series if series == "hh" else f"licensed_{hub}"
    pd.DataFrame(res).to_csv(out / f"soco90_greedy_{tag}.csv", index=False)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--series", choices=("hh", "licensed"), default="hh")
    ap.add_argument("--hub", default="SNG")
    ap.add_argument("--transport-csv", type=Path, default=None)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.series == "licensed" and not LICENSED.exists():
        sys.exit(f"licensed file absent: {LICENSED} (see its README contract)")
    run(a.out, a.series, a.hub, a.transport_csv, tuple(a.years))


if __name__ == "__main__":
    main()
