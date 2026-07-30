"""miso-105 — is the DA virtual-bid mechanism IDENTIFIABLE and MOTIVATED in MISO?

Stage-1 census for the `da_virtual_bids` lever (matrix row `da_virtual_bids`,
MISO cell; queue item 3 of `docs/mechanism-testing-matrix.md` §5.4). Answers
the charter's branch point BEFORE any solve is spent, on the four questions
the nyiso-94 refusal (`docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md`)
established as the admissibility test for this mechanism family:

(a) **Grain + price axis.** Does MISO publish a SUBMITTED virtual bid/offer
    curve — MW *with a price axis* — at zone-hour grain? A cleared-only series
    FAILS rule 13 `[R-MEASURED]`; a single MW per zone-hour with no price axis
    FAILS rule 21 `[R-DOF]` (it would need a fitted price distribution).
(b) **Provenance cross-check.** Does the candidate series reproduce the MISO
    IMM's published *cleared* virtual volumes? In nyiso-94 that was the tell
    that a series was CLEARED. Here it is run in BOTH directions: the file's
    `MW` column should reproduce the IMM's cleared volume while the submitted
    ladder should be materially larger — a positive identification of the
    submitted half, not merely a failure to identify the cleared one.
(c) **Premise.** PJM's lever exists because its DA market clears MORE than the
    physical load the model serves (+7-11 GW net DEC at the top summer hours).
    Is that true in MISO? Measured in the mean hour, by hour-of-day, and in the
    measured RT>$300 tail.
(d) **Stiffness (this session's addition).** MISO's virtual book is an order of
    magnitude larger than NYISO's. If the measured net curve's local slope near
    its crossing price is much stiffer than the model's own supply stack, the
    curve would SET the model's price rather than deepen its demand — a
    rule-1 `[R-STRUCT]` / rule-13 objection that no ISO tested so far has had
    to face. Measured against the keeper's own hourly sidecars.

Source
------
`https://docs.misoenergy.org/marketreports/YYYYMMDD_bids_cb.zip` — MISO's
FERC-Order-719 masked demand-bid archive, released on a ~90-day lag (the
2023-06-15 market day was posted 2023-09-13). Public, no auth. Columns:
`Region, Market Participant Code, Date/Time Beginning (EST), Date/Time End
(EST), MW, LMP, Type of Bid, Bid ID, PRICE1..9, MW1..9`, where

* `Type of Bid` ∈ {D = virtual demand (DEC), I = virtual supply (INC),
  F = fixed physical demand, P = price-sensitive physical demand};
* `(PRICE_i, MW_i)` is the **submitted** ladder in INCREMENTAL blocks
  (identified here, not assumed — see `--semantics`);
* `MW` is the **cleared** quantity and `LMP` the clearing price.

Data is fetched at run time into a scratch directory and is deliberately NOT
committed under `data/raw/` by this probe: the `MW`/`LMP` columns are market
OUTCOMES, and a measured outcome sitting in the input tree is a re-armable
answer key (rule 26 `[R-DELETE]` in spirit). A Stage-2 intake would carry the
submitted ladder only.

Usage
-----
    # ladder-semantics identification on a single day (cheap)
    uv run python scripts/probes/miso105_da_virtual_identifiability.py --semantics

    # full 2023-2025 census (rule 22: training years only)
    uv run python scripts/probes/miso105_da_virtual_identifiability.py \
        --years 2023 2024 2025 --workers 8

    # stratified sample instead of the full corpus
    uv run python scripts/probes/miso105_da_virtual_identifiability.py \
        --years 2023 2024 2025 --sample 12
"""

from __future__ import annotations

import argparse
import io
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BASE = "https://docs.misoenergy.org/marketreports"
SCRATCH = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "95c88392-416f-5f97-b504-de0b4c6ac69c/scratchpad/miso105"
)

#: Price grid the per-hour net curve ``net(lambda)`` is evaluated on ($/MWh).
#: Resolution only — $1 through the body where every MISO dual lives, coarser
#: in the tails. Never a tunable.
PRICE_GRID = np.concatenate(
    [
        np.arange(-500.0, -50.0, 25.0),
        np.arange(-50.0, 0.0, 5.0),
        np.arange(0.0, 250.0, 1.0),
        np.arange(250.0, 1000.0, 10.0),
        np.arange(1000.0, 4001.0, 100.0),
    ]
)

PCOLS = [f"PRICE{i}" for i in range(1, 10)]
MCOLS = [f"MW{i}" for i in range(1, 10)]
USECOLS = [
    "Region",
    "Date/Time Beginning (EST)",
    "MW",
    "LMP",
    "Type of Bid",
    *PCOLS,
    *MCOLS,
]
REGIONS = ("North", "Central", "South", "UNMAPPED")


def _fetch_day(day: date) -> pd.DataFrame | None:
    """Read one market day's masked demand-bid archive, virtual rows only.

    Returns a frame of the D/I (DEC/INC) rows with the submitted ladder, the
    cleared MW and the clearing LMP, or ``None`` when MISO has no file for the
    day (the archive is a rolling ~3.5-year window).
    """
    ymd = day.strftime("%Y%m%d")
    cache = SCRATCH / "raw" / f"{ymd}_bids_cb.zip"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        # docs.misoenergy.org resets the connection under sustained parallel
        # pulls; retry with backoff rather than losing the whole census.
        last: Exception | None = None
        for attempt in range(5):
            try:
                r = requests.get(f"{BASE}/{ymd}_bids_cb.zip", timeout=180)
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                tmp = cache.with_suffix(".part")
                tmp.write_bytes(r.content)
                tmp.rename(cache)  # atomic: never leave a truncated cache entry
                break
            except Exception as exc:  # noqa: BLE001 — network, retried below
                last = exc
                time.sleep(2.0 * 2**attempt)
        else:
            print(f"    [skip] {ymd}: {last}", flush=True)
            return None
    with zipfile.ZipFile(io.BytesIO(cache.read_bytes())) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            df = pd.read_csv(fh, usecols=USECOLS, low_memory=False)
    return df[df["Type of Bid"].isin(("D", "I"))].copy()


def _ladder(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(price, mw, is_dec) arrays of every submitted incremental block."""
    price = df[PCOLS].to_numpy(dtype=float)
    mw = df[MCOLS].to_numpy(dtype=float)
    is_dec = (df["Type of Bid"].to_numpy() == "D")[:, None] & np.ones_like(price, bool)
    ok = np.isfinite(price) & np.isfinite(mw) & (mw > 0.0)
    return price[ok], mw[ok], is_dec[ok]


def _day_summary(day: date) -> dict | None:
    """Per-hour aggregates for one market day.

    Returns a dict of ``(24, ...)`` arrays: the submitted net curve on
    ``PRICE_GRID``, submitted/cleared MW by side and region, and the
    MW-weighted clearing LMP.
    """
    df = _fetch_day(day)
    if df is None or df.empty:
        return None
    ts = pd.to_datetime(df["Date/Time Beginning (EST)"], format="%m/%d/%Y %H:%M:%S")
    df["_h"] = ts.dt.hour.to_numpy()
    df["_reg"] = df["Region"].fillna("UNMAPPED")

    nh = 24
    net = np.zeros((nh, PRICE_GRID.size))
    dec_curve = np.zeros((nh, PRICE_GRID.size))
    inc_curve = np.zeros((nh, PRICE_GRID.size))
    sub = np.zeros((nh, 2, len(REGIONS)))  # [h, (D,I), region]
    clr = np.zeros((nh, 2, len(REGIONS)))
    lmp = np.zeros(nh)
    lmp_w = np.zeros(nh)

    for h, g in df.groupby("_h", sort=True):
        h = int(h)
        if h >= nh:
            continue
        p, m, is_dec = _ladder(g)
        # net(lambda) = sum_{DEC price >= lambda} MW - sum_{INC price <= lambda} MW
        # Evaluated by cumulating each side's MW mass over the price grid.
        d_mass, _ = np.histogram(p[is_dec], bins=np.append(PRICE_GRID, np.inf), weights=m[is_dec])
        i_mass, _ = np.histogram(p[~is_dec], bins=np.append(PRICE_GRID, np.inf), weights=m[~is_dec])
        dec_ge = d_mass[::-1].cumsum()[::-1]  # DEC MW bid at or above each grid price
        inc_le = i_mass.cumsum()  # INC MW offered at or below each grid price
        dec_curve[h] = dec_ge
        inc_curve[h] = inc_le
        net[h] = dec_ge - inc_le
        for si, side in enumerate(("D", "I")):
            gs = g[g["Type of Bid"] == side]
            for ri, reg in enumerate(REGIONS):
                gr = gs[gs["_reg"] == reg]
                if gr.empty:
                    continue
                sub[h, si, ri] = np.nansum(gr[MCOLS].to_numpy(dtype=float))
                clr[h, si, ri] = gr["MW"].sum()
        w = g["MW"].to_numpy(dtype=float)
        if w.sum() > 0:
            lmp[h] = float(np.average(g["LMP"].to_numpy(dtype=float), weights=w))
            lmp_w[h] = w.sum()
    return {
        "day": day,
        "net": net,
        "dec": dec_curve,
        "inc": inc_curve,
        "sub": sub,
        "clr": clr,
        "lmp": lmp,
        "lmp_w": lmp_w,
    }


def _dates(years: list[int], sample: int | None) -> list[date]:
    out: list[date] = []
    for y in years:
        d, end = date(y, 1, 1), date(y, 12, 31)
        days = []
        while d <= end:
            days.append(d)
            d += timedelta(days=1)
        if sample:
            # stratified: `sample` evenly-spaced days per year
            idx = np.linspace(0, len(days) - 1, sample).round().astype(int)
            days = [days[i] for i in dict.fromkeys(idx)]
        out.extend(days)
    return out


def run_census(years: list[int], sample: int | None, workers: int) -> dict:
    """Fetch + aggregate the corpus; returns stacked per-hour arrays."""
    days = _dates(years, sample)
    print(f"[miso-105] fetching {len(days)} market days ({workers} workers) …", flush=True)
    res: list[dict] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(_day_summary, days, chunksize=2)):
            if r is not None:
                res.append(r)
            if (i + 1) % 60 == 0:
                print(f"    {i + 1}/{len(days)} days", flush=True)
    res.sort(key=lambda r: r["day"])
    print(f"[miso-105] {len(res)} days returned data", flush=True)
    stamp = pd.to_datetime([f"{r['day']} {h:02d}:00" for r in res for h in range(24)])
    return {
        "stamp": stamp,
        "net": np.concatenate([r["net"] for r in res]),
        "dec": np.concatenate([r["dec"] for r in res]),
        "inc": np.concatenate([r["inc"] for r in res]),
        "sub": np.concatenate([r["sub"] for r in res]),
        "clr": np.concatenate([r["clr"] for r in res]),
        "lmp": np.concatenate([r["lmp"] for r in res]),
        "lmp_w": np.concatenate([r["lmp_w"] for r in res]),
    }


def identify_semantics(day: date) -> None:
    """(a) ladder semantics — INCREMENTAL vs CUMULATIVE, from the file itself.

    The cleared `MW` column is an exact function of the submitted ladder and
    the clearing `LMP`: a DEC block clears when its price is at or above the
    LMP, an INC block when its price is at or below. Whichever reading of
    `MW_i` reproduces the published cleared MW *is* the file's semantics —
    identified, not assumed.
    """
    df = _fetch_day(day)
    assert df is not None
    p = df[PCOLS].to_numpy(dtype=float)
    m = df[MCOLS].to_numpy(dtype=float)
    keep = np.isfinite(p).any(axis=1)
    df, p, m = df[keep], p[keep], m[keep]
    lmp = df["LMP"].to_numpy(dtype=float)
    cleared = df["MW"].to_numpy(dtype=float)
    is_dec = df["Type of Bid"].to_numpy() == "D"
    inb = np.where(is_dec[:, None], p >= lmp[:, None], p <= lmp[:, None]) & np.isfinite(p)
    incr = np.where(inb, np.nan_to_num(m), 0.0).sum(axis=1)
    cum = np.where(inb, np.nan_to_num(m), -np.inf).max(axis=1)
    cum = np.where(np.isfinite(cum), cum, 0.0)
    print(f"\n=== (a) ladder semantics — {day} ({len(df):,} priced virtual bid-hours)")
    for nm, pred in (("INCREMENTAL", incr), ("CUMULATIVE", cum)):
        print(
            f"    {nm:<12} reproduces cleared MW: "
            f"{np.isclose(cleared, pred, atol=0.05).mean():.4%}   MAE {np.abs(cleared - pred).mean():.4f} MW"
        )
    print(
        "    -> the winner is the file's semantics; note this ALSO proves the ladder is "
        "SUBMITTED (it contains uncleared blocks) and the clearing is a function of it."
    )
    n_uncleared = (cleared < np.nansum(m, axis=1) - 1e-9).mean()
    print(f"    submitted-but-not-fully-cleared share of bid-hours: {n_uncleared:.2%}")


def _physical_day(day: date) -> tuple[date, np.ndarray, np.ndarray] | None:
    """Cleared PHYSICAL demand (F + P) and net virtual per EST hour, one day.

    Cached files only — this pass re-reads what the census already pulled so it
    costs no extra fetch. Used for the nyiso-94 blocker-3 test in MISO: does the
    whole DA book sit above or below RT actual load?
    """
    ymd = day.strftime("%Y%m%d")
    cache = SCRATCH / "raw" / f"{ymd}_bids_cb.zip"
    if not cache.exists():
        return None
    with zipfile.ZipFile(io.BytesIO(cache.read_bytes())) as zf:
        with zf.open(zf.namelist()[0]) as fh:
            df = pd.read_csv(
                fh,
                usecols=["Date/Time Beginning (EST)", "MW", "Type of Bid"],
                low_memory=False,
            )
    h = pd.to_datetime(df["Date/Time Beginning (EST)"], format="%m/%d/%Y %H:%M:%S").dt.hour
    piv = df.assign(_h=h).pivot_table(
        index="_h", columns="Type of Bid", values="MW", aggfunc="sum"
    )
    piv = piv.reindex(index=range(24), columns=["D", "I", "F", "P"]).fillna(0.0)
    return day, (piv["F"] + piv["P"]).to_numpy(), (piv["D"] - piv["I"]).to_numpy()


def physical_book(years: list[int], workers: int = 4) -> None:
    """(c-ii) Does MISO's whole DA book clear above or below RT actual load?"""
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    print("\n" + "=" * 78)
    print("(c-ii) DA BOOK vs RT ACTUAL LOAD  (nyiso-94 blocker-3 test, MISO)")
    print("=" * 78)
    for y in years:
        days = _dates([y], None)
        with ProcessPoolExecutor(max_workers=workers) as ex:
            rows = [r for r in ex.map(_physical_day, days, chunksize=4) if r is not None]
        if not rows:
            print(f"    {y}: no cached days")
            continue
        stamp = pd.DatetimeIndex([pd.Timestamp(d) + pd.Timedelta(hours=h) for d, _, _ in rows for h in range(24)])
        phys = np.concatenate([p for _, p, _ in rows])
        virt = np.concatenate([v for _, _, v in rows])
        eia = _eia_hourly_frame_filled("MISO", y)
        utc_m = pd.DatetimeIndex(pd.to_datetime(eia["UTC time"], utc=True)).tz_localize(None)
        rt = pd.DataFrame({"utc": utc_m, "rt_load": eia["Demand"].to_numpy(dtype=float)})
        j = pd.DataFrame(
            {"utc": stamp + pd.Timedelta(hours=5), "da_phys": phys, "net_virt": virt}
        ).merge(rt, on="utc", how="inner")
        j["da_total"] = j["da_phys"] + j["net_virt"]
        hod = j["utc"].dt.tz_localize("UTC").dt.tz_convert("US/Eastern").dt.hour
        pk = hod.isin((15, 16, 17))
        print(
            f"    {y} ({len(j):,} h): DA physical {j['da_phys'].mean() / 1000:5.1f} GW  "
            f"+ net virtual {j['net_virt'].mean() / 1000:+5.2f}  = DA book {j['da_total'].mean() / 1000:5.1f}  "
            f"vs RT actual {j['rt_load'].mean() / 1000:5.1f}  ->  DA-RT {(j['da_total'] - j['rt_load']).mean():+7.0f} MW"
        )
        print(
            f"          peak HE16-18: DA book {j.loc[pk, 'da_total'].mean() / 1000:5.1f} GW  "
            f"vs RT {j.loc[pk, 'rt_load'].mean() / 1000:5.1f}  ->  {(j.loc[pk, 'da_total'] - j.loc[pk, 'rt_load']).mean():+7.0f} MW"
        )


def _model_clock(year: int) -> pd.DataFrame:
    """Model-hour index keyed on UTC, from the EIA-930 frame the LP clocks on.

    MISO's market reports are stamped EST year-round; the model's 8760 clock is
    the EIA-930 *local* (DST-observing Eastern) frame. Joining through UTC is
    the only alignment that is right in both halves of the year.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    df = _eia_hourly_frame_filled("MISO", year)
    utc = pd.DatetimeIndex(pd.to_datetime(df["UTC time"], utc=True)).tz_localize(None)
    return pd.DataFrame({"utc": utc, "t": np.arange(len(utc)), "year": year})


def _keeper_price(bundle: Path, year: int) -> np.ndarray:
    """Load-weighted ISO-mean P1 dual per model hour from a keeper's sidecars."""
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    w = s.pivot(index="hour", columns="zone", values="demand")
    p = s.pivot(index="hour", columns="zone", values="price")
    return ((p * w).sum(axis=1) / w.sum(axis=1)).to_numpy(dtype=float)


def _interp_net(grid: np.ndarray, net: np.ndarray, lam: np.ndarray) -> np.ndarray:
    """net(lambda) per hour, linearly interpolated on the price grid."""
    out = np.empty(len(lam))
    for i in range(len(lam)):
        out[i] = np.interp(lam[i], grid, net[i])
    return out


def _crossing(grid: np.ndarray, net: np.ndarray) -> np.ndarray:
    """Crossing price lambda0 where net(lambda) changes sign, per hour."""
    out = np.full(len(net), np.nan)
    for i in range(len(net)):
        n = net[i]
        j = np.argmax(n <= 0.0)
        if n[0] <= 0.0 or not (n <= 0.0).any():
            out[i] = grid[0] if n[0] <= 0.0 else grid[-1]
            continue
        a, b = grid[j - 1], grid[j]
        na, nb = n[j - 1], n[j]
        out[i] = a if na == nb else a + (b - a) * na / (na - nb)
    return out


def _slope(grid: np.ndarray, net: np.ndarray, lam: np.ndarray, half: float = 5.0) -> np.ndarray:
    """Local |d net / d lambda| in MW per $/MWh over a +/- ``half`` $ window."""
    lo = _interp_net(grid, net, np.maximum(lam - half, grid[0]))
    hi = _interp_net(grid, net, np.minimum(lam + half, grid[-1]))
    return (lo - hi) / (2.0 * half)


def analyse(npz: Path, bundle: Path, years: list[int]) -> None:
    """Report the four Stage-1 questions from a completed census."""
    z = np.load(npz, allow_pickle=True)
    grid = z["grid"]
    stamp = pd.DatetimeIndex(z["stamp"].astype("datetime64[ns]"))  # EST wall clock
    net, dec, inc = z["net"].astype(float), z["dec"].astype(float), z["inc"].astype(float)
    sub, clr, lmp = z["sub"].astype(float), z["clr"].astype(float), z["lmp"].astype(float)
    regions = list(z["regions"])
    utc = stamp + pd.Timedelta(hours=5)  # MISO market clock is EST year-round
    # Hour-of-day is taken on the MODEL's clock (EIA-930 Eastern local, DST
    # observing) so peak/night windows line up with the C3b metric, not on the
    # market file's EST stamp — the two differ by an hour all summer.
    local = utc.tz_localize("UTC").tz_convert("US/Eastern")
    hod = local.hour.to_numpy()
    yr = local.year.to_numpy()

    print("\n" + "=" * 78)
    print("(a) GRAIN + PRICE AXIS")
    print("=" * 78)
    print(f"    bid-hours covered: {len(stamp):,} EST hours, {sorted(set(yr))}")
    print(f"    price grid rendered: {grid.min():.0f} .. {grid.max():.0f} $/MWh, {grid.size} points")
    ssum = sub.sum(axis=(0, 1))
    csum = clr.sum(axis=(0, 1))
    print("    region shares of submitted / cleared virtual MW:")
    for ri, reg in enumerate(regions):
        print(f"      {reg:<10} submitted {ssum[ri] / ssum.sum():6.1%}   cleared {csum[ri] / csum.sum():6.1%}")

    print("\n" + "=" * 78)
    print("(b) PROVENANCE — submitted ladder vs cleared column vs IMM published")
    print("=" * 78)
    print("    (IMM 2024 Table A2: MISO cleared virtual LOAD 15.8 % of load, SUPPLY 14.5 %)")
    for y in years:
        m = yr == y
        if not m.any():
            continue
        load = np.nan
        try:
            s = pd.read_parquet(bundle / "hourly" / f"system_{y}.parquet")
            load = s[s["pass"] == "P1"].groupby("hour")["demand"].sum().mean()
        except FileNotFoundError:
            pass
        sd, si = sub[m, 0].sum(1).mean(), sub[m, 1].sum(1).mean()
        cd, ci = clr[m, 0].sum(1).mean(), clr[m, 1].sum(1).mean()
        print(
            f"    {y}: submitted D {sd / 1000:6.2f} GW/h  I {si / 1000:6.2f}   "
            f"cleared D {cd / 1000:5.2f}  I {ci / 1000:5.2f}   "
            f"cleared as % of {load / 1000:.1f} GW load: D {cd / load:5.1%}  I {ci / load:5.1%}   "
            f"submitted/cleared {(sd + si) / (cd + ci):.2f}x"
        )

    print("\n" + "=" * 78)
    print("(c) PREMISE — is MISO's DA deeper than physical load, like PJM's?")
    print("=" * 78)
    print("    (PJM's lever exists on +7-11 GW net DEC at the top summer hours)")
    net_clr = clr[:, 0].sum(1) - clr[:, 1].sum(1)
    season = np.select(
        [np.isin(local.month, [12, 1, 2]), np.isin(local.month, [6, 7, 8])],
        ["winter", "summer"],
        "shoulder",
    )
    for y in years:
        m = yr == y
        if not m.any():
            continue
        pk = m & np.isin(hod, (15, 16, 17))  # HE16-18
        ng = m & np.isin(hod, (0, 1, 2))  # HE01-03
        print(
            f"    {y}: net cleared virtual  mean {net_clr[m].mean():+8.0f} MW   "
            f"peak HE16-18 {net_clr[pk].mean():+8.0f}   night HE01-03 {net_clr[ng].mean():+8.0f}   "
            f"peak-minus-night {net_clr[pk].mean() - net_clr[ng].mean():+8.0f}"
        )
        for sn in ("winter", "shoulder", "summer"):
            ms = m & (season == sn)
            pk_s, ng_s = ms & np.isin(hod, (15, 16, 17)), ms & np.isin(hod, (0, 1, 2))
            print(
                f"          {sn:<9} peak {net_clr[pk_s].mean():+7.0f}  night {net_clr[ng_s].mean():+7.0f}  "
                f"delta {net_clr[pk_s].mean() - net_clr[ng_s].mean():+7.0f}"
            )

    # measured RT>$300 tail (the nyiso-94 framing), on the model's own benchmark
    act = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet")
    print("\n    net cleared virtual in the measured RT>$300 tail:")
    for y in years:
        a = act[act["year"] == y]
        rt = a.groupby("hour")["rt"].mean()
        tail_t = rt.index[rt > 300.0].to_numpy()
        if tail_t.size == 0:
            print(f"      {y}: 0 tail hours")
            continue
        ck = _model_clock(y)
        j = pd.DataFrame({"utc": utc, "net": net_clr}).merge(ck, on="utc", how="inner")
        sel = j[j["t"].isin(tail_t)]
        print(
            f"      {y}: {len(sel):4d} of {tail_t.size} tail hours matched   "
            f"net cleared {sel['net'].mean():+8.0f} MW"
        )

    print("\n" + "=" * 78)
    print("(d) STIFFNESS — would the curve DEEPEN the model's demand, or SET its price?")
    print("=" * 78)
    lam0 = _crossing(grid, net)
    for y in years:
        try:
            mp = _keeper_price(bundle, y)
        except FileNotFoundError:
            continue
        ck = _model_clock(y)
        idx = pd.DataFrame({"utc": utc, "row": np.arange(len(utc))}).merge(ck, on="utc", how="inner")
        rows = idx["row"].to_numpy()
        t = idx["t"].to_numpy()
        lam_m = mp[t]
        n_at_model = _interp_net(grid, net[rows], lam_m)
        n_at_lmp = _interp_net(grid, net[rows], lmp[rows])
        sl0 = _slope(grid, net[rows], lam0[rows])
        slm = _slope(grid, net[rows], lam_m)
        pk = np.isin(hod[rows], (15, 16, 17))
        print(
            f"    {y}: crossing lambda0 mean ${np.nanmean(lam0[rows]):6.2f} vs measured DA LMP "
            f"${lmp[rows].mean():6.2f} vs model dual ${lam_m.mean():6.2f}"
        )
        print(
            f"        net(lambda) at the MEASURED LMP {n_at_lmp.mean():+8.0f} MW   "
            f"at the MODEL's own dual {n_at_model.mean():+8.0f} MW   (peak hours {n_at_model[pk].mean():+8.0f})"
        )
        print(
            f"        |d net/d lambda| at lambda0 {np.nanmean(sl0) / 1000:6.2f} GW per $/MWh   "
            f"at the model dual {np.nanmean(slm) / 1000:6.2f}   (peak hours {np.nanmean(slm[pk]) / 1000:6.2f})"
        )
        # Gross book straddling the crossing: how much submitted mass sits
        # within +/- $5 of lambda0 on each side (the marginal virtual block).
        d_hi = _interp_net(grid, dec[rows], lam0[rows] + 5.0)
        d_lo = _interp_net(grid, dec[rows], lam0[rows] - 5.0)
        i_hi = _interp_net(grid, inc[rows], lam0[rows] + 5.0)
        i_lo = _interp_net(grid, inc[rows], lam0[rows] - 5.0)
        print(
            f"        gross submitted mass within +/-$5 of lambda0: DEC {np.nanmean(d_lo - d_hi) / 1000:5.2f} GW  "
            f"INC {np.nanmean(i_hi - i_lo) / 1000:5.2f} GW"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--sample", type=int, default=None, help="days per year (stratified)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--semantics", action="store_true", help="run (a) only, one day")
    ap.add_argument("--analyze", action="store_true", help="report (a)-(d) from a census")
    ap.add_argument("--physical", action="store_true", help="run the (c-ii) DA-book test only")
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/miso101_tempgrain_B",
        help="keeper bundle whose hourly sidecars supply the model-side comparison",
    )
    ap.add_argument("--out", type=Path, default=SCRATCH / "census.npz")
    args = ap.parse_args()

    SCRATCH.mkdir(parents=True, exist_ok=True)
    if args.semantics:
        identify_semantics(date(2023, 6, 15))
        return
    if args.analyze:
        analyse(args.out, args.keeper, args.years)
        physical_book(args.years, args.workers)
        return
    if args.physical:
        physical_book(args.years, args.workers)
        return

    for y in args.years:
        if y not in (2023, 2024, 2025):
            raise SystemExit(
                f"rule 22 [R-HOLDOUT]: MISO carries no calibration-complete marker; "
                f"year {y} is quarantined for solve, score AND registration."
            )
    c = run_census(args.years, args.sample, args.workers)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        stamp=c["stamp"].astype("datetime64[ns]").astype("int64"),
        grid=PRICE_GRID,
        net=c["net"].astype("float32"),
        dec=c["dec"].astype("float32"),
        inc=c["inc"].astype("float32"),
        sub=c["sub"].astype("float32"),
        clr=c["clr"].astype("float32"),
        lmp=c["lmp"].astype("float32"),
        lmp_w=c["lmp_w"].astype("float32"),
        regions=np.array(REGIONS),
    )
    print(f"[miso-105] wrote {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
