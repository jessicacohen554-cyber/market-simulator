"""R-CAISO-17 phase 0 (zero LP): pre-2022 EIA-930 CISO clock scan.

Is any EIA-930 CISO column family (NG cells / Net generation, Total
interchange, Demand) stamped off its true clock in 2019-2022, outside the
registered ``EIA930_CISO_CLOCK_LATE_WINDOWS_UTC``?

Everything is placed on one grid: UTC interval-START hours. Lag convention:
``lag = +1`` means the EIA-930 value stamped at hour t+1 is the true value of
hour t (the publisher is one hour LATE); the scan reports the lag in
{-2..+2} maximising corr(d EIA shifted, d reference). Differenced series are
used so a slow seasonal level cannot hide a 1-hour phase error.

References, each with a clock independent of the EIA-930 extract:
  TAC   OASIS SLD actual ``CA ISO-TAC`` (``interval_start_gmt``) - its own clock
        is verified first: UTC continuity across every DST transition and its
        best lag against the Outlook supply sum (Outlook is CAISO's own
        5-minute publication on the wall clock, converted independently).
  OUT   CAISO Today's Outlook fuel mix, 5-min, Pacific wall clock (2019-2021
        only; the corpus holds no 2022 file): solar, natural_gas, imports and
        the supply sum.
  CEMS  EPA CAMPD unit-level gross load, California gas units (local STANDARD
        time, hour-beginning; EPA's own clock, a different publisher entirely).
  SUN   solar geometry: the ``NG: SUN`` production centroid in PST.
Counterparty BA-to-BA legs (BPAT / PACW / NEVP) exist in the corpus only from
2023, so they cannot reach 2019-2022; that is stated, not substituted.

Reads measured inputs only; zero fitted parameters (rule 23). Writes the
monthly and daily tables to the directory given as argv[1].
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402

RAW = paths.RAW_DATA_DIR
YEARS = range(2019, 2023)
LAGS = range(-2, 3)


def eia() -> pd.DataFrame:
    """The raw CISO extract on UTC interval-start (UTC time is hour-ending)."""
    e = pd.read_parquet(RAW / "eia-930-hourly" / "CISO hourly.parquet")
    utc = pd.DatetimeIndex(e["UTC time"])
    utc = utc.tz_convert("UTC").tz_localize(None) if utc.tz is not None else utc
    cols = {
        "D": "Demand",
        "NG": "Net generation",
        "TI": "Total interchange",
        "SUN": "NG: SUN",
        "GAS": "NG: NG",
    }
    x = pd.DataFrame(
        {k: pd.to_numeric(e[v], errors="coerce").to_numpy() for k, v in cols.items()},
        index=utc - pd.Timedelta(hours=1),
    )
    x["IMP"] = -x["TI"]
    return x[~x.index.duplicated()].asfreq("h")


def tac() -> tuple[pd.Series, pd.DataFrame]:
    """OASIS CA ISO-TAC actual, plus its own UTC-continuity audit per year."""
    parts, audit = [], []
    for yr in range(2018, 2026):
        t = pd.read_csv(
            RAW / "zone-specific-demand" / "CAISO" / f"CAISO_tac_load_hourly_{yr}.csv"
        )
        t = t[t["tac_area"] == "CA ISO-TAC"]
        idx = pd.to_datetime(t["interval_start_gmt"], utc=True).dt.tz_localize(None)
        s = pd.Series(t["mw"].to_numpy(float), index=idx.to_numpy()).sort_index()
        full = pd.date_range(s.index.min(), s.index.max(), freq="h")
        audit.append(
            {
                "year": yr,
                "rows": len(s),
                "dup_utc": int(s.index.duplicated().sum()),
                "missing_utc": int(len(full.difference(s.index))),
                "missing_list": ";".join(str(m) for m in full.difference(s.index)[:6]),
            }
        )
        parts.append(s)
    s = pd.concat(parts)
    return s[~s.index.duplicated()].sort_index(), pd.DataFrame(audit)


def outlook() -> pd.DataFrame:
    """Outlook 5-min, wall clock -> hourly means on UTC interval-start."""
    out = []
    for yr in (2019, 2020, 2021):
        o = pd.read_csv(RAW / "caiso-outlook-fuelsource" / f"fuelsource_{yr}.csv.gz")
        wall = pd.to_datetime(o["date"] + " " + o["time"], errors="coerce")
        o = o.assign(wall=wall).dropna(subset=["wall"])
        num = ["solar", "natural_gas", "imports"]
        sup = [c for c in o.columns if c not in ("date", "time", "wall")]
        o[sup] = o[sup].apply(pd.to_numeric, errors="coerce")
        o["supply"] = o[sup].sum(axis=1, min_count=1)
        # fall-back day repeats 01:xx; keep the unambiguous hours only
        loc = pd.DatetimeIndex(o["wall"]).tz_localize(
            "US/Pacific", ambiguous="NaT", nonexistent="NaT"
        )
        o["utc"] = loc.tz_convert("UTC").tz_localize(None)
        o = o.dropna(subset=["utc"])
        h = o.groupby(o["utc"].dt.floor("h"))[num + ["supply"]].mean()
        out.append(h)
    h = pd.concat(out)
    h = h[~h.index.duplicated()].asfreq("h")
    return h.rename(
        columns={
            "solar": "o_sun",
            "natural_gas": "o_gas",
            "imports": "o_imp",
            "supply": "o_sup",
        }
    )


def cems() -> pd.Series:
    """CAMPD California gas-fired gross load, local standard time -> UTC start."""
    parts = []
    for yr in YEARS:
        c = pd.read_parquet(
            RAW / "campd-unit-level" / f"CA_{yr}.parquet",
            columns=["date", "hour", "grossLoad", "primaryFuelInfo"],
        )
        c = c[c["primaryFuelInfo"].astype(str).str.contains("Natural Gas", na=False)]
        t = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        parts.append(c["grossLoad"].groupby(t + pd.Timedelta(hours=8)).sum())
    s = pd.concat(parts)
    return s[~s.index.duplicated()].sort_index().asfreq("h")


def best_lag(a: pd.Series, r: pd.Series) -> dict:
    """Best lag of EIA series ``a`` against reference ``r`` (diff-correlation)."""
    res = {}
    dr = r.diff()
    for lag in LAGS:
        da = a.shift(-lag).diff()
        j = pd.concat([da, dr], axis=1, join="inner").dropna()
        res[lag] = (j.iloc[:, 0].corr(j.iloc[:, 1]) if len(j) > 48 else np.nan, len(j))
    corrs = {k: v[0] for k, v in res.items()}
    good = {k: v for k, v in corrs.items() if not np.isnan(v)}
    if not good:
        return {"best": np.nan, "c_best": np.nan, "c0": np.nan, "n": 0}
    b = max(good, key=good.get)
    return {"best": b, "c_best": good[b], "c0": corrs[0], "n": res[0][1]}


PAIRS = [
    # (eia column, reference column, label)
    ("D", "tac", "Demand~TAC"),
    ("SUN", "o_sun", "SUN~OUT.solar"),
    ("GAS", "o_gas", "NG:NG~OUT.gas"),
    ("GAS", "cems", "NG:NG~CEMS"),
    ("IMP", "o_imp", "-TI~OUT.imports"),
    ("NG", "cems", "NetGen~CEMS"),
]


def main() -> None:
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    outdir.mkdir(parents=True, exist_ok=True)
    x = eia()
    t, audit = tac()
    o = outlook()
    c = cems()
    ref = (
        pd.concat({"tac": t}, axis=1)
        .join(o, how="outer")
        .join(c.rename("cems"), how="outer")
    )
    df = x.join(ref, how="left")
    df = df[(df.index >= "2019-01-01") & (df.index < "2023-01-01")]

    print("== TAC own-clock audit (UTC continuity per file) ==")
    print(audit.to_string(index=False))

    # TAC vs the Outlook supply sum: an EIA-free check of TAC's own clock.
    rows = []
    for (y, m), g in df.groupby([df.index.year, df.index.month]):
        r = best_lag(g["o_sup"], g["tac"]) if g["o_sup"].notna().sum() > 48 else None
        if r:
            rows.append(
                {"year": y, "month": m, **{f"tacclk_{k}": v for k, v in r.items()}}
            )
    tacclk = pd.DataFrame(rows)

    # Monthly best lag per pair.
    mrows = []
    for (y, m), g in df.groupby([df.index.year, df.index.month]):
        row = {"year": y, "month": m}
        for a, r, lab in PAIRS:
            if g[a].notna().sum() > 48 and g[r].notna().sum() > 48:
                b = best_lag(g[a], g[r])
                row[f"{lab}"] = b["best"]
                row[f"{lab}|c"] = round(b["c_best"], 3)
                row[f"{lab}|c0"] = round(b["c0"], 3)
        # Solar-geometry centroid of NG: SUN on PST (UTC-8), interval midpoint.
        sun = g["SUN"].clip(lower=0)
        hpst = ((g.index - pd.Timedelta(hours=8)).hour + 0.5).to_numpy()
        row["SUN_centroid_PST"] = (
            round(float((sun * hpst).sum() / sun.sum()), 2) if sun.sum() > 0 else np.nan
        )
        osun = g["o_sun"].clip(lower=0)
        row["OUTsun_centroid_PST"] = (
            round(float((osun * hpst).sum() / osun.sum()), 2)
            if osun.sum() > 0
            else np.nan
        )
        mrows.append(row)
    monthly = pd.DataFrame(mrows).merge(tacclk, on=["year", "month"], how="left")

    # Daily best lag for the sharpest pairs.
    drows = []
    for day, g in df.groupby(df.index.floor("D")):
        row = {"day": day.date()}
        for a, r, lab in PAIRS:
            if g[a].notna().sum() >= 20 and g[r].notna().sum() >= 20:
                row[lab] = _day_lag(df, day, a, r)
        drows.append(row)
    daily = pd.DataFrame(drows)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 60)
    lagcols = (
        ["year", "month"]
        + [p[2] for p in PAIRS]
        + ["SUN_centroid_PST", "OUTsun_centroid_PST", "tacclk_best"]
    )
    print("\n== Monthly best lag (+1 = EIA-930 late) ==")
    print(monthly[[c for c in lagcols if c in monthly]].to_string(index=False))
    print("\n== Daily best-lag share per year (fraction of days at each lag) ==")
    daily["year"] = pd.to_datetime(daily["day"]).dt.year
    for _, _, lab in PAIRS:
        if lab in daily:
            tab = (
                daily.groupby("year")[lab]
                .value_counts(normalize=True)
                .unstack()
                .round(3)
            )
            print(f"-- {lab}\n{tab.to_string()}")
    monthly.to_csv(outdir / "phase0-monthly.csv", index=False)
    daily.to_csv(outdir / "phase0-daily.csv", index=False)
    audit.to_csv(outdir / "phase0-tac-audit.csv", index=False)


def _day_lag(df: pd.DataFrame, day: pd.Timestamp, a: str, r: str) -> float:
    """Best lag for one UTC day, the EIA series allowed to reach +-2 h outside it."""
    lo, hi = day - pd.Timedelta(hours=3), day + pd.Timedelta(hours=27)
    w = df.loc[lo:hi]
    dr = w[r].diff()
    best, bc = np.nan, -np.inf
    for lag in LAGS:
        da = w[a].shift(-lag).diff()
        j = pd.concat([da, dr], axis=1).loc[day : day + pd.Timedelta(hours=23)].dropna()
        if len(j) < 18:
            continue
        cc = j.iloc[:, 0].corr(j.iloc[:, 1])
        if cc > bc:
            best, bc = lag, cc
    return best


if __name__ == "__main__":
    main()
