"""SPP-82 (zero LP): split SPP-81b's +7.5 GW of offered-below-MEC capacity that does not set price.

Record: ``docs/handoffs/FINDING-spp-82-offered-not-setting-2026-09-25.md``. Companion of
``_spp81b_offer_stack_position.py``, whose sample it reproduces exactly (same hour set, same
``--days`` days per month, same offer snapshot, same ``[--lo, 500)`` stack).

Why aggregate, not resource-level: SPP publishes no resource-level RTBM dispatch, commitment
status or economic limit that could be joined to the masked ``historical-offers`` RCodes (the
source survey is in the FINDING §1). What it does publish, anonymously, per hour:

* ``hourly-generation-capacity-by-fuel-type`` — the ONLINE (committed) capacity by fuel,
  SPP BA (it swings with commitment through the day while the offer file does not);
* ``generation-mix-historical`` (``data/raw/spp-genmix``) — generation by fuel;
* ``rtbm-lmp-by-location`` — five-minute MEC (system-wide, read from the first row of
  each interval file; range-read, nothing downloaded whole).

Per sampled hour, with ``B10`` = offered MW in ``[lo, 500)`` at or below the hour's MEC
(SPP-81b's quantity), ``C_th`` / ``G_th`` = online capacity / generation of every fuel but
wind and solar:

* ``off_lb`` = ``max(0, B10 - C_th)`` — a hard LOWER bound on the offline part of ``B10``
  (online resources cannot offer more ≥$lo MW than their online capacity);
* ``hdr`` = ``C_th - G_th`` — online, undispatched thermal headroom: the most that
  "online but not dispatched" (ramp- or limit-bound, or constrained off) can hold;
* the offline offered MW total ``T_all - C_all`` (the offer file lists every resource every
  interval, offline ones included — verified here by the flat resource count).

Five-minute leg: per sampled hour, the 12 interval MECs; the hourly mean minus the interval
median, the share of the mean's excess over the median carried by the top two intervals,
and ``mec_pct`` recomputed at the interval MEDIAN rather than the mean.

Usage: ``python scripts/probes/_spp82_offered_not_setting.py [--years ...] [--out <json>]``
"""

from __future__ import annotations

import argparse
import io
import json
import pickle
import struct
import sys
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "data"))
from fetch_spp_or_cleared import _get, zip_members  # noqa: E402

from scripts.probes._spp80_upper_tercile_premium import model_hour  # noqa: E402
from scripts.probes._spp81_residual_upper_tercile import frame, upper  # noqa: E402
from scripts.probes._spp81b_offer_stack_position import PRICE_CAP, URL, read_member  # noqa: E402

DL = "https://portal.spp.org/file-browser-api/download/{fs}?path=%2F{y}%2F{y}.zip"
LMP_URL = DL.replace("{fs}", "rtbm-lmp-by-location")
VER = ("Wind", "Solar")


LISTING_CACHE: dict[str, list[tuple]] = {}


def listing(url: str) -> list[tuple]:
    """Zip central directory, retried (the portal's HEAD on a multi-GB zip times out now and then)."""
    if url in LISTING_CACHE:
        return LISTING_CACHE[url]
    for attempt in range(6):
        try:
            LISTING_CACHE[url] = zip_members(url)
            return LISTING_CACHE[url]
        except OSError:
            if attempt == 5:
                raise
    raise RuntimeError("unreachable")


def sample_days(ns: pd.DataFrame, n_days: int) -> list[int]:
    """SPP-81b's day selection, verbatim: per month the ``n_days`` days with most tercile hours."""
    ns = ns.assign(day=ns.index // 24)
    cnt = ns.groupby(["mon", "day"]).size().reset_index(name="n")
    return cnt.sort_values("n", ascending=False).groupby("mon").head(n_days).day.tolist()


def day_dates(y: int, day: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Calendar date of model day ``day`` (Feb 29 dropped) and the next date."""
    dt = pd.Timestamp(f"{y}-01-01") + pd.Timedelta(days=int(day))
    if y % 4 == 0 and dt >= pd.Timestamp(f"{y}-02-29"):
        dt += pd.Timedelta(days=1)
    return dt, dt + pd.Timedelta(days=1)


def curve_arrays(off: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Segment price (first point, then midpoints) and MW width of every offer, flattened."""
    P = off[[f"Price{i}" for i in range(1, 11)]].to_numpy(float)
    M = off[[f"MW{i}" for i in range(1, 11)]].to_numpy(float)
    pr, w = [], []
    for p, m in zip(P, M):
        k = np.isfinite(p) & np.isfinite(m)
        if not k.any():
            continue
        o = np.argsort(m[k], kind="stable")
        p, m = p[k][o], m[k][o]
        pr.append(np.r_[p[0], (p[1:] + p[:-1]) / 2])
        w.append(np.maximum(np.diff(np.r_[0.0, m]), 0.0))
    return np.concatenate(pr), np.concatenate(w)


def stack_ext(off: pd.DataFrame, mec: float, mec_med: float, lo: float) -> dict:
    """SPP-81b's position plus the quantities the aggregate split needs (MW)."""
    pr, w = curve_arrays(off)
    s = (pr > lo) & (pr < PRICE_CAP)  # SPP-81b's stack, identical filter
    return {
        "mec_pct": float(w[s & (pr <= mec)].sum() / w[s].sum()),
        "mec_pct_med": float(w[s & (pr <= mec_med)].sum() / w[s].sum()),
        "T10": float(w[s].sum()),
        "B10": float(w[s & (pr <= mec)].sum()),
        "T_all": float(w[pr < PRICE_CAP].sum()),
        "n_res": int(off.RCode.nunique()),
    }


def mec_5min(y: int, days: list[int], hours: set[int]) -> pd.DataFrame:
    """Five-minute system MEC for every interval of the sampled hours (first row of each file)."""
    url = LMP_URL.format(y=y)
    want = {d.strftime("%Y%m%d") for day in days for d in day_dates(y, day)}
    mem = [m for m in listing(url) if "By_Interval" in m[0] and m[0].split("-")[-1][:8] in want]

    def one(m: tuple) -> dict | None:
        name, meth, csz, off = m
        b = _get(url, off, off + 30 + 2048 + min(csz, 4096))
        fl, el = struct.unpack("<HH", b[26:30])
        raw = b[30 + fl + el :]
        txt = (zlib.decompressobj(-15).decompress(raw) if meth == 8 else raw).decode(errors="ignore")
        lines = txt.splitlines()
        hdr, row = lines[0].split(","), lines[1].split(",")
        h = int(model_hour(pd.Series([row[hdr.index("GMTIntervalEnd")]]), y)[0])
        if h not in hours:
            return None
        return {"h": h, "gmt": row[hdr.index("GMTIntervalEnd")], "mec": float(row[hdr.index("MEC")])}

    # Prefilter by the file-name CPT hour (±1 h covers CST vs CDT) before any range read.
    hod = {h % 24 for h in hours}
    keep = [m for m in mem if any((int(m[0].split("-")[-1][8:10]) - k) % 24 in hod for k in (0, 1, 2))]
    with ThreadPoolExecutor(24) as ex:
        rows = [r for r in ex.map(one, keep) if r is not None]
    return pd.DataFrame(rows).drop_duplicates("gmt")


def gencap_hourly(y: int, zdir: Path) -> pd.DataFrame:
    """Online capacity by fuel, SPP BA, on the model clock (stamp read as hour-BEGINNING)."""
    z = zipfile.ZipFile(zdir / f"hourly-generation-capacity-by-fuel-type-{y}.zip")
    parts = []
    for n in z.namelist():
        if not n.lower().endswith(".csv"):
            continue
        f = pd.read_csv(io.BytesIO(z.read(n)), skipinitialspace=True)
        f.columns = [c.strip() for c in f.columns]
        if "BAA" in f:
            f = f[f.BAA == "SPP"].drop(columns="BAA")
        parts.append(f)
    f = pd.concat(parts)
    end = pd.to_datetime(f.pop("GMT TIME"), utc=True) + pd.Timedelta(hours=1)
    f["hour"] = model_hour(end.dt.strftime("%Y-%m-%dT%H:%M:%S"), y)
    f = f[f.hour >= 0].groupby("hour").mean()
    return pd.DataFrame(
        {"C_all": f.sum(axis=1), "C_th": f.drop(columns=[c for c in VER if c in f]).sum(axis=1),
         "C_gas": f["Natural Gas"], "C_coal": f["Coal Market"] + f["Coal Self"]}
    ).reindex(range(8760))


def genmix_th(y: int) -> pd.DataFrame:
    """Hourly generation (GenMix, market + self), thermal (non-wind/solar) and total."""
    g = pd.read_csv(RAW_DATA_DIR / f"spp-genmix/GenMix_{y}.csv", skipinitialspace=True)
    g.columns = [c.strip() for c in g.columns]
    gen = [c for c in g.columns if c not in ("GMT MKT Interval", "Load")]
    ver = [c for c in gen if c.startswith(VER)]
    out = pd.DataFrame({"hour": model_hour(g["GMT MKT Interval"], y),
                        "G_all": g[gen].sum(axis=1), "G_th": g[[c for c in gen if c not in ver]].sum(axis=1)})
    return out[out.hour >= 0].groupby("hour").mean().reindex(range(8760))


def year_run(y: int, lmp: pd.DataFrame, comp: pd.DataFrame, n_days: int, lo: float, zdir: Path) -> pd.DataFrame:
    """Every sampled hour of ``y``: the SPP-81b stack stats, the aggregate split and the 5-min MEC."""
    ns = upper(frame(y, lmp, comp))
    ns = ns[~ns.scar].copy()
    days = sample_days(ns, n_days)
    hours = {h for h in ns.index if h // 24 in set(days)}
    m5 = mec_5min(y, days, hours)
    g5 = m5.groupby("h").mec
    five = pd.DataFrame({"mec5_mean": g5.mean(), "mec5_med": g5.median(), "n_int": g5.size(),
                         "mec5_top2": g5.apply(lambda s: np.sort(s.to_numpy())[-2:].mean() if len(s) >= 2 else np.nan)})
    listing_ = listing(URL.format(y=y))
    members = {m[0].split("-")[-1][:8]: m for m in listing_ if "RTBM-ENERGY-OFFERS" in m[0]}

    def work(day: int) -> list[dict]:
        res = []
        for d in day_dates(y, day):
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
                    med = five.mec5_med.get(h, np.nan)
                    res.append({"h": h, "mec": ns.mec[h], **stack_ext(g, ns.mec[h], med if np.isfinite(med) else ns.mec[h], lo)})
        return res

    with ThreadPoolExecutor(6) as ex:
        rows = [x for rr in ex.map(work, days) for x in rr]
    Q = pd.DataFrame(rows).drop_duplicates("h").set_index("h")
    return Q.join(five).join(gencap_hourly(y, zdir)).join(genmix_th(y)).join(ns[["net"]])


def summarise(y: int, Q: pd.DataFrame) -> dict:
    """Per-year means of the split (GW) and of the five-minute statistics ($/MWh)."""
    k = 1e3
    ex = (Q.mec5_mean - Q.mec5_med).clip(lower=0)
    return {
        "year": y, "n_hours": int(len(Q)), "n_res_min_max": [int(Q.n_res.min()), int(Q.n_res.max())],
        "mec_pct": Q.mec_pct.mean(), "B10_gw": Q.B10.mean() / k, "T10_gw": Q.T10.mean() / k,
        "T_all_gw": Q.T_all.mean() / k, "C_all_gw": Q.C_all.mean() / k, "C_th_gw": Q.C_th.mean() / k,
        "C_gas_gw": Q.C_gas.mean() / k, "C_coal_gw": Q.C_coal.mean() / k,
        "G_th_gw": Q.G_th.mean() / k, "G_all_gw": Q.G_all.mean() / k, "net_gw": Q.net.mean() / k,
        "offline_offered_gw": (Q.T_all - Q.C_all).mean() / k,
        "off_lb_gw": (Q.B10 - Q.C_th).clip(lower=0).mean() / k,
        "B10_minus_Cth_gw": (Q.B10 - Q.C_th).mean() / k,
        "hdr_th_gw": (Q.C_th - Q.G_th).mean() / k,
        "B10_minus_Gth_gw": (Q.B10 - Q.G_th).mean() / k,
        "mec_hourly": Q.mec.mean(), "mec5_mean": Q.mec5_mean.mean(), "mec5_med": Q.mec5_med.mean(),
        "mean_minus_med": (Q.mec5_mean - Q.mec5_med).mean(),
        "top2_share_of_excess": float((Q.mec5_top2 - Q.mec5_mean).clip(lower=0).sum() / 6 / ex.sum()) if ex.sum() > 0 else None,
        "hours_mean_gt_med_by_5": float(((Q.mec5_mean - Q.mec5_med) > 5).mean()),
        "mec_pct_at_median": Q.mec_pct_med.mean(), "n_int_mean": Q.n_int.mean(),
        "hourly_vs_5min_mean_gap": (Q.mec - Q.mec5_mean).abs().mean(),
    }


def main() -> None:
    """Aggregate split + five-minute leg for the requested years; prints and writes JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2023, 2024])
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--lo", type=float, default=10.0)
    ap.add_argument("--zdir", type=Path, required=True, help="dir holding hourly-generation-capacity-by-fuel-type-<y>.zip")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--listing-cache", type=Path, help="pickle of {url: members}, read if present, rewritten after")
    a = ap.parse_args()
    if a.listing_cache and a.listing_cache.exists():
        LISTING_CACHE.update(pickle.loads(a.listing_cache.read_bytes()))
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    comp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet")
    rows = []
    for y in a.years:
        Q = year_run(y, lmp, comp, a.days, a.lo, a.zdir)
        rows.append(summarise(y, Q))
        print(f"{y} done ({len(Q)} hours)", flush=True)
        if a.listing_cache:
            a.listing_cache.write_bytes(pickle.dumps(LISTING_CACHE))
    T = pd.DataFrame(rows).set_index("year")
    pd.set_option("display.width", 250)
    print(T.T.to_string())
    if a.out:
        a.out.write_text(json.dumps(rows, indent=1, default=float))


if __name__ == "__main__":
    main()
