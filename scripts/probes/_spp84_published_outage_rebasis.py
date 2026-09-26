"""SPP-84 (zero LP): the keeper's thermal OUTAGE level against SPP's own published outage by fuel.

Record: ``docs/handoffs/FINDING-spp-84-published-outage-vs-keeper-2026-09-26.md``.

SPP-83 found the keeper treats ~8 GW as available that SPP's market had offline, ~6 GW of it gas,
and asked for a MEASURED, forward-reproducible availability input (rule 13) that could own it.
This probe measures the three candidates that exist, all against the keeper
``results/calibration/rspp_span`` rebuilt ``fleet_only`` (``_spp81b...rebuild``, no LP):

* **Leg A — SPP's published hourly outaged MW by fuel** (portal product
  ``capacity-of-generation-on-outage``, year zips; Coal / Natural Gas columns) against the keeper's
  own unavailable MW per family, ``pmax - pmax x availability``. ``pmax`` is taken as the row's
  maximum available MW over the year (a LOWER bound on unavailability for a row never fully
  available), and leading / trailing all-zero runs of >= 30 days are excluded as the COD /
  retirement mask rather than outage (``--edge-days``).
* **Leg B — EIA-860M monthly status** (``<month>_generator<year>.xlsx``, SWPP rows) for the
  keeper's own gas plants: MW that the monthly inventory flags SB / OS / OA in a month while the
  annual vintage the keeper reads flags OP (a seasonal lay-up the keeper cannot see).
* **Leg C — re-clear instrument** (SPP-83 §1.1's method over ALL hours): merit-clear the keeper's
  own stack at its own non-VER P1 generation, then rebase each family's unavailable MW to SPP's
  published hourly total PRO RATA (restore in proportion to each row's unavailable MW when SPP's
  total is lower; remove in proportion to each row's available MW when it is higher; the one
  zero-DOF allocation) and re-clear. Coal-only, gas-only and both. System-wide, one zone, no
  ramps: an instrument, not a solve. Only deltas are used.

Solves nothing. Usage:
``python scripts/probes/_spp84_published_outage_rebasis.py --cache <fleet pkl dir>
--outage <dir of o<y>.zip | parquet> [--m860 <dir of eia860m_swpp_<y>.parquet>] [--out <json>]``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp72_demand_tightness import CST_OFFSET_H, model_clock_index  # noqa: E402
from scripts.probes._spp81b_upper_tercile_marginal_unit import BUNDLE, rebuild  # noqa: E402

FINDING = "docs/handoffs/FINDING-spp-84-published-outage-vs-keeper-2026-09-26.md"
GAS = ("gas_cc", "gas_ct", "gas_st")
VER = ("WIND", "SOLAR", "STORAGE", "BATTERY")
SPP_COL = {"coal": "Coal MW", "gas": "Natural Gas MW"}


def load_outage_zips(zdir: Path) -> pd.DataFrame:
    """SPP ``capacity-of-generation-on-outage`` year zips (``o<y>.zip``) -> one hourly frame.

    Re-fetch: ``https://portal.spp.org/file-browser-api/download/capacity-of-generation-on-outage
    ?path=%2F<y>%2F<y>.zip`` (0.5-0.6 MB each; the 2025 zip downloads empty, 0 bytes, 2026-09-26).
    Daily files overlap at the day seam, so the LAST snapshot of each market hour is kept.
    """
    import io
    import zipfile

    frames = []
    for zp in sorted(zdir.glob("o*.zip")):
        if zp.stat().st_size == 0:
            continue
        z = zipfile.ZipFile(zp)
        for n in sorted(z.namelist()):
            if n.endswith(".csv"):
                d = pd.read_csv(io.BytesIO(z.read(n)))
                d.columns = [c.strip() for c in d.columns]
                frames.append(d)
    d = pd.concat(frames)
    d["t"] = pd.to_datetime(
        d["Market Hour"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
    )
    return d.dropna(subset=["t"]).drop_duplicates("t", keep="last")


def edge_mask(a: np.ndarray, min_run: int) -> np.ndarray:
    """True on leading / trailing all-zero runs of >= ``min_run`` hours (COD / retirement mask)."""
    z = a <= 1e-6
    m = np.zeros_like(z)
    if z.all():
        m[:] = True
        return m
    i = int(np.argmax(~z))
    if i >= min_run:
        m[:i] = True
    j = int(np.argmax(~z[::-1]))
    if j >= min_run:
        m[len(z) - j :] = True
    return m


def spp_outage_on_model_clock(o: pd.DataFrame, y: int) -> pd.DataFrame:
    """SPP published outage by fuel re-indexed onto the model's 8,760 CST slots (nearest hour)."""
    local = (model_clock_index(y) - pd.Timedelta(hours=CST_OFFSET_H)).tz_localize(None)
    s = o[o.t.dt.year == y].set_index("t").sort_index()
    s = s[~s.index.duplicated(keep="last")][list(SPP_COL.values())]
    return s.reindex(local, method="nearest", tolerance=pd.Timedelta(hours=3)).set_axis(
        range(8760)
    )


def merit(c: np.ndarray, w: np.ndarray, q: float) -> float:
    """System merit price: the offer of the MW serving quantity ``q`` (nan if short)."""
    o = np.argsort(c, kind="stable")
    j = np.searchsorted(np.cumsum(w[o]), q - 1e-6)
    return float(c[o][j]) if j < o.size else np.nan


def rebase(
    av: np.ndarray, pm: np.ndarray, sel: np.ndarray, target: float
) -> np.ndarray:
    """Pro-rata rebase of the ``sel`` rows' unavailable MW to ``target`` for one hour."""
    w = av.copy()
    un = np.where(sel, pm - av, 0.0)
    cur = un.sum()
    if not np.isfinite(target):
        return w
    if target < cur and cur > 0:  # restore availability in proportion to unavailability
        w = w + un * (cur - target) / cur
    elif target > cur:  # remove availability in proportion to availability
        a = np.where(sel, av, 0.0)
        tot = a.sum()
        if tot > 0:
            w = w - a * min(1.0, (target - cur) / tot)
    return w


def year_legs(
    y: int, cache: Path, o: pd.DataFrame, edge_days: int, lmp: pd.DataFrame
) -> dict:
    """Legs A and C for one year."""
    fl = rebuild(y, cache, False)
    r = pd.DataFrame(fl["rows"])
    av = fl["avail"].astype(float)
    mc = fl["mc"].astype(float)
    pm = av.max(1)
    ft = r.fuel_type.to_numpy()
    fam = {"gas": np.isin(ft, GAS), "coal": ft == "coal"}
    mask = np.array([edge_mask(a, edge_days * 24) for a in av])
    pm_h = np.where(
        mask, av, pm[:, None]
    )  # masked hours: pmax := av (no outage counted)
    # A year counts as measured only at >= 90 % hourly coverage (the empty 2025 zip leaves
    # just the 2024 file's day-seam hours, which must not read as a 2025 measurement).
    sp = spp_outage_on_model_clock(o, y)
    if sp[SPP_COL["gas"]].notna().mean() < 0.9:
        sp = None
    out: dict = {"year": y}
    mon = (
        pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    ).month
    for f, sel in fam.items():
        un = (pm_h - av)[sel].sum(0)
        out[f"{f}_pmax_gw"] = float(pm[sel].sum() / 1e3)
        out[f"{f}_keeper_unavail_gw"] = float(un.mean() / 1e3)
        out[f"{f}_keeper_unavail_monthly_gw"] = (
            (pd.Series(un).groupby(mon).mean() / 1e3).round(3).tolist()
        )
        if sp is not None:
            s = sp[SPP_COL[f]].to_numpy()
            out[f"{f}_spp_outage_gw"] = float(np.nanmean(s) / 1e3)
            out[f"{f}_spp_outage_monthly_gw"] = (
                (pd.Series(s).groupby(mon).mean() / 1e3).round(3).tolist()
            )
            out[f"{f}_keeper_minus_spp_gw"] = float(np.nanmean(un - s) / 1e3)
    if sp is None:
        return out
    # Leg C: re-clear at the keeper's own non-VER P1 generation.
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{y}.parquet")
    ch = ch[(ch["pass"] == "P1") & ~ch.klass.str.upper().str.startswith(VER)]
    q = ch.groupby("hour").mw.sum().reindex(range(8760)).to_numpy()
    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    p1 = (
        (s.price * s.demand).groupby(s.hour).sum() / s.groupby("hour").demand.sum()
    ).reindex(range(8760))
    rt = lmp[lmp.year == y].set_index("hour").rt.reindex(range(8760))
    rec = []
    tc, tg = sp[SPP_COL["coal"]].to_numpy(), sp[SPP_COL["gas"]].to_numpy()
    for t in range(8760):
        if not np.isfinite(q[t]):
            continue
        c, a, p = mc[:, t], av[:, t], pm_h[:, t]
        wc = rebase(a, p, fam["coal"], tc[t])
        wg = rebase(a, p, fam["gas"], tg[t])
        wb = rebase(wc, p, fam["gas"], tg[t])
        rec.append(
            {
                "h": t,
                "p_full": merit(c, a, q[t]),
                "p_coal": merit(c, wc, q[t]),
                "p_gas": merit(c, wg, q[t]),
                "p_both": merit(c, wb, q[t]),
            }
        )
    R = pd.DataFrame(rec).set_index("h").join(p1.rename("p1")).join(rt.rename("rt"))
    R["mon"] = mon[R.index]
    ok = R.rt.notna()
    q67, q99 = R.loc[ok & (R.mon != 2), "rt"].quantile([0.67, 0.99])
    seg = {
        "all": ok,
        "body_rt_lt_p67": ok & (R.rt < q67),
        "upper_p67_p99_exFeb": ok & (R.mon != 2) & (R.rt >= q67) & (R.rt < q99),
    }
    for k, m in seg.items():
        d = R[m]
        out[f"C_{k}"] = {
            "n": int(m.sum()),
            "rt": float(d.rt.mean()),
            "keeper_p1": float(d.p1.mean()),
            "p_full": float(d.p_full.mean()),
            "d_coal": float((d.p_coal - d.p_full).mean()),
            "d_gas": float((d.p_gas - d.p_full).mean()),
            "d_both": float((d.p_both - d.p_full).mean()),
        }
    return out


def leg_b(y: int, cache: Path, m860: Path) -> dict | None:
    """860M: keeper gas plants' MW flagged non-OP in a month, by month (GW).

    Input: ``eia860m_swpp_<y>.parquet``, the SWPP rows of the twelve monthly inventories
    ``https://www.eia.gov/electricity/data/eia860m/archive/xls/<month>_generator<y>.xlsx``
    (sheets Operating + Retired, header row located by 'Plant ID'; ~9 MB per month, not landed).
    """
    f = m860 / f"eia860m_swpp_{y}.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    d = d[d.sheet == "Operating"].copy()
    d["mw"] = pd.to_numeric(d["Net Summer Capacity (MW)"], errors="coerce").fillna(0.0)
    d["pid"] = pd.to_numeric(d["Plant ID"], errors="coerce")
    d["gas"] = d["Energy Source Code"].isin(["NG"])
    d["st"] = d.Status.str.extract(r"\((\w\w)\)")[0]
    fl = rebuild(y, cache, False)
    r = pd.DataFrame(fl["rows"])
    kp = set(
        pd.to_numeric(
            r.loc[r.fuel_type.isin(GAS), "plant_code"], errors="coerce"
        ).dropna()
    )
    g = d[d.gas & d.pid.isin(kp)]
    tab = (
        g.pivot_table(index="month", columns="st", values="mw", aggfunc="sum").fillna(
            0.0
        )
        / 1e3
    )
    return {
        "months": [int(m) for m in tab.index],
        "by_status_gw": {k: tab[k].round(3).tolist() for k in tab.columns},
        "non_op_mean_gw": float(
            tab.drop(columns=["OP"], errors="ignore").sum(axis=1).mean()
        ),
        "non_op_max_gw": float(
            tab.drop(columns=["OP"], errors="ignore").sum(axis=1).max()
        ),
    }


def main() -> None:
    """Run legs A-C for the requested years; print and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--outage", type=Path, required=True)
    ap.add_argument("--m860", type=Path)
    ap.add_argument("--edge-days", type=int, default=30)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "results/calibration/_spp84_published_outage_phase0.json",
    )
    a = ap.parse_args()
    o = load_outage_zips(a.outage) if a.outage.is_dir() else pd.read_parquet(a.outage)
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    res = {"lane": "SPP-84", "finding": FINDING, "bundle": str(BUNDLE), "per_year": {}}
    for y in a.years:
        row = year_legs(y, a.cache, o, a.edge_days, lmp)
        if a.m860:
            row["B_860m_gas"] = leg_b(y, a.cache, a.m860)
        res["per_year"][str(y)] = row
        print(
            json.dumps(
                {k: v for k, v in row.items() if "monthly" not in k}, default=str
            ),
            flush=True,
        )
    a.out.write_text(json.dumps(res, indent=1, default=float))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
