"""SPP-81b (zero LP): where does the RT upper-tercile MEC sit in SPP's own offer stack?

Record: ``docs/handoffs/FINDING-spp-81-upper-tercile-residual-2026-09-25.md`` §4. Companion
of ``_spp81b_upper_tercile_marginal_unit.py`` (whose ``--cache`` supplies the keeper's
rebuilt fleets for the model-side comparison).

Source: SPP Marketplace ``historical-offers`` (anonymous HTTPS, 90-day lag, masked RCodes;
the product SPP-73 surveyed): one ``/<yr>/<yr>.zip`` per year (2.7 GB for 2024) holding one
``RTBM-ENERGY-OFFERS-<yyyymmdd>*.csv`` per operating day with every resource's 10-point
``MW<i>, Price<i>`` offer curve — hourly (``GMTHourEnd``) through 2022, five-minute
(``GMTINTVEND``) from 2023. Members are range-read (``fetch_spp_or_cleared.zip_members`` /
``_get``); nothing is downloaded whole and nothing is written under ``data/``.

Sample (fixed before reading any offer file): on SPP-80's non-scarcity upper-tercile hour set,
the ``--days`` days per month carrying the most tercile hours; every tercile hour on those days,
one offer snapshot per hour (the hourly row, or the five-minute interval ending at :30).

Per snapshot, over offer segments priced in ``[--lo, 500)`` $/MWh (``--lo`` 10 excludes the
zero/negative renewable and must-offer blocks; the $500+ caps are excluded), MW-weighted:
the p50 / p75 / p90 / p95 offer price, the offered GW, and ``mec_pct`` — the share of those
MW offered at or below the hour's measured hub MEC. Then per year: those quantiles over the
monthly delivered KS/OK/NE gas price; the within-year OLS of ``mec_pct`` on net load and the
RTBM binding shadow-price mass; and the keeper's own ``mec_pct`` (its P1 price inside its
available ``[--lo, 500)`` offer MW) in the same hours.

Usage: ``python scripts/probes/_spp81b_offer_stack_position.py --cache <dir> [--years ...]``
"""

from __future__ import annotations

import argparse
import io
import pickle
import struct
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
from fetch_spp_or_cleared import _get, zip_members  # noqa: E402

from scripts.probes._spp80_upper_tercile_premium import binding_hourly, model_hour  # noqa: E402
from scripts.probes._spp81_residual_upper_tercile import (  # noqa: E402
    delivered_gas_monthly,
    frame,
    upper,
)

URL = "https://portal.spp.org/file-browser-api/download/historical-offers?path=%2F{y}%2F{y}.zip"
PRICE_CAP = 500.0  # $/MWh: offer caps and scarcity-priced blocks sit above this
QS = (0.50, 0.75, 0.90, 0.95)


def read_member(y: int, m: tuple) -> pd.DataFrame:
    """Range-read and inflate one zip member (local header + deflate stream)."""
    name, meth, csz, off = m
    b = _get(URL.format(y=y), off, off + 30 + 2048 + csz)
    fl, el = struct.unpack("<HH", b[26:30])
    d = b[30 + fl + el : 30 + fl + el + csz]
    return pd.read_csv(io.BytesIO(zlib.decompress(d, -15) if meth == 8 else d))


def stack_stats(off: pd.DataFrame, mec: float, lo: float) -> dict:
    """MW-weighted offer-price quantiles and MEC's position in the ``[lo, cap)`` stack."""
    P = off[[f"Price{i}" for i in range(1, 11)]].to_numpy(float)
    M = off[[f"MW{i}" for i in range(1, 11)]].to_numpy(float)
    pr, w = [], []
    for p, m in zip(P, M):
        k = np.isfinite(p) & np.isfinite(m)
        if not k.any():
            continue
        o = np.argsort(m[k], kind="stable")
        p, m = p[k][o], m[k][o]
        pr.append(np.r_[p[0], (p[1:] + p[:-1]) / 2])  # first point, then segment midpoints
        w.append(np.maximum(np.diff(np.r_[0.0, m]), 0.0))
    pr, w = np.concatenate(pr), np.concatenate(w)
    k = (pr > lo) & (pr < PRICE_CAP)
    o = np.argsort(pr[k])
    pr, w = pr[k][o], w[k][o]
    cw = np.cumsum(w) / w.sum()
    out = {f"q{int(q * 100)}": pr[np.searchsorted(cw, q)] for q in QS}
    out["mec_pct"] = float(w[pr <= mec].sum() / w.sum())
    out["offered_gw"] = w.sum() / 1e3
    return out


def year_sample(y: int, ns: pd.DataFrame, n_days: int, lo: float) -> pd.DataFrame:
    """Offer-stack statistics for every tercile hour on the sampled days of year ``y``."""
    ns = ns.assign(day=ns.index // 24)
    cnt = ns.groupby(["mon", "day"]).size().reset_index(name="n")
    days = cnt.sort_values("n", ascending=False).groupby("mon").head(n_days).day.tolist()
    for attempt in range(4):  # the portal's HEAD on a 2.7 GB zip times out now and then
        try:
            listing = zip_members(URL.format(y=y))
            break
        except OSError:
            if attempt == 3:
                raise
    members = {m[0].split("-")[-1][:8]: m for m in listing if "RTBM-ENERGY-OFFERS" in m[0]}

    def work(day: int) -> list[dict]:
        dt = pd.Timestamp(f"{y}-01-01") + pd.Timedelta(days=int(day))
        if y % 4 == 0 and dt >= pd.Timestamp(f"{y}-02-29"):
            dt += pd.Timedelta(days=1)  # model clock drops Feb 29
        res = []
        for d in (dt, dt + pd.Timedelta(days=1)):  # a CST day spans two GMT-dated files' edges
            m = members.get(d.strftime("%Y%m%d"))
            if m is None:
                continue
            off = read_member(y, m)
            col = "GMTHourEnd" if "GMTHourEnd" in off else "GMTINTVEND"
            if col == "GMTINTVEND":
                off = off[pd.to_datetime(off[col]).dt.minute == 30]
            off["h"] = model_hour(off[col], y)
            for h, g in off.groupby("h"):
                if h in ns.index and h // 24 == day:
                    r = ns.loc[h]
                    res.append({"h": h, "mec": r.mec, "gas": r.gas, "net": r.net, "m": r.m, **stack_stats(g, r.mec, lo)})
        return res

    with ThreadPoolExecutor(6) as ex:
        rows = [x for rr in ex.map(work, days) for x in rr]
    return pd.DataFrame(rows).drop_duplicates("h").set_index("h")


def model_position(cache: Path, y: int, Q: pd.DataFrame, lo: float) -> float | None:
    """The keeper's P1 price position inside its own available ``[lo, cap)`` offer MW."""
    p = cache / f"fleet_{y}.pkl"
    if not p.exists():
        return None
    fl = pickle.loads(p.read_bytes())
    mc, av = fl["mc"], fl["avail"]
    pc = []
    for h in Q.index:
        k = (mc[:, h] >= lo) & (mc[:, h] < PRICE_CAP) & (av[:, h] > 0)
        pc.append(av[k, h][mc[k, h] <= Q.m[h]].sum() / av[k, h].sum())
    return float(np.mean(pc))


def main() -> None:
    """Per-year offer-stack position of the RT upper-tercile MEC."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2021, 2022, 2023, 2024])
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--lo", type=float, default=10.0)
    a = ap.parse_args()
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    comp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet")
    rows = []
    for y in a.years:
        ns = upper(frame(y, lmp, comp))
        ns = ns[~ns.scar].copy()
        ns["gas"] = ns.mon.map(delivered_gas_monthly(y))
        Q = year_sample(y, ns, a.days, a.lo).join(binding_hourly(y))
        r = {"year": y, "n_hours": len(Q), "mec": Q.mec.mean(), "gas": Q.gas.mean(), "net_gw": Q.net.mean() / 1e3,
             "offered_gw": Q.offered_gw.mean(), "mec_pct": Q.mec_pct.mean(),
             "offered_below_mec_gw": (Q.mec_pct * Q.offered_gw).mean(), "bc_sp": Q.bc_sp.mean()}
        for q in QS:
            c = f"q{int(q * 100)}"
            r[c], r[c + "_over_gas"] = Q[c].mean(), (Q[c] / Q.gas).mean()
        r["mec_over_gas"] = (Q.mec / Q.gas).mean()
        X = np.c_[np.ones(len(Q)), Q.net / 1e3, Q.bc_sp / 1e3]
        k = np.isfinite(X).all(1) & np.isfinite(Q.mec_pct)
        b = np.linalg.lstsq(X[k], Q.mec_pct[k], rcond=None)[0]
        r["ols_pct_per_gw_net"], r["ols_pct_per_k_bc"] = b[1], b[2]
        r["model_mec_pct"] = model_position(a.cache, y, Q, a.lo)
        rows.append(r)
        print(f"{y} done ({len(Q)} hours)", flush=True)
    T = pd.DataFrame(rows).set_index("year")
    pd.set_option("display.width", 250)
    print(T.round(3).T.to_string())


if __name__ == "__main__":
    main()
