"""R-CAISO-16 phase 0 (zero LP): re-scan the CISO per-DIBA interchange feed's clock.

Measures, per DST regime (PST/PDT) x window (inside / outside the EIA-930
generation late window ``EIA930_CISO_CLOCK_LATE_WINDOWS_UTC["generation"]``)
x year, the best lag of the summed per-DIBA net import against:
  REF-U  the extract's ``Total interchange`` UNREPAIRED;
  REF-R  the same column REPAIRED (``caiso_eia930_clock_repair`` armed);
  REF-M  an independent clock: the counterparty BAs' own EIA-930 submissions
         (BPAT / PACW / NEVP ``diba == "CISO"`` legs, sign-flipped), matched
         leg-by-leg against CISO's BPAT / PACW / NEVP legs.
Lags are RESIDUAL to the pinned read-seam correction
(``_caiso_interchange_model_clock``): 0 means the current constants map the
feed onto the reference's clock. Differenced series (d/dt) are correlated so
the slow seasonal level cannot hide a 1-hour phase error. Reads only measured
inputs (rule 23).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.config.constants import EIA930_CISO_CLOCK_LATE_WINDOWS_UTC  # noqa: E402
from market_sim.data.eia930 import envelopes, frames  # noqa: E402

IC = paths.RAW_DATA_DIR / "eia-930-interchange"
EXTRACT = paths.RAW_DATA_DIR / "eia-930-hourly" / "CISO hourly.parquet"
LO, HI = (pd.Timestamp(s) for s in EIA930_CISO_CLOCK_LATE_WINDOWS_UTC["generation"])
LAGS = range(-3, 4)


def _pac_to_utc(stamps: pd.DatetimeIndex) -> pd.DatetimeIndex:
    loc = stamps.tz_localize("US/Pacific", ambiguous=False, nonexistent="shift_forward")
    return loc.tz_convert("UTC").tz_localize(None)


def feed_on_extract_clock(ic: pd.DataFrame) -> pd.Series:
    """Feed net import, stamped on the extract's hour-ending UTC clock via the
    pinned correction (model clock is the extract's Local-date/Hour grid)."""
    s = (
        ic.groupby("local_time", observed=True)["mw"]
        .sum(min_count=1)
        .mul(-1)
        .sort_index()
    )
    model = envelopes._caiso_interchange_model_clock(pd.DatetimeIndex(s.index))
    # model clock = start-of-hour on the extract's local wall grid; the extract
    # row with Local date d, Hour h (hour-ending) starts at d + (h-1).
    return pd.Series(s.to_numpy(), index=model)


def extract_ti(repaired: bool) -> pd.Series:
    e = pd.read_parquet(EXTRACT)
    frames.set_caiso_eia930_clock_repair(repaired)
    e = frames._repair_published_extract(e, "CISO")
    frames.set_caiso_eia930_clock_repair(False)
    ti = -pd.to_numeric(e["Total interchange"], errors="coerce").to_numpy()
    utc = pd.DatetimeIndex(e["UTC time"])
    if utc.tz is not None:
        utc = utc.tz_convert("UTC").tz_localize(None)
    # The model clock is the extract's row POSITION grid = local STANDARD time
    # (fixed UTC-8), start-of-hour; ``UTC time`` is hour-ending.
    start = utc - pd.Timedelta(hours=9)
    df = pd.DataFrame({"ti": ti, "utc": utc}, index=pd.DatetimeIndex(start))
    return df[~df.index.duplicated()]


def _dst(utc: pd.Series) -> pd.Series:
    loc = (
        pd.DatetimeIndex(utc - pd.Timedelta(hours=1))
        .tz_localize("UTC")
        .tz_convert("US/Pacific")
    )
    return pd.Series(np.array([bool(t.dst()) for t in loc]), index=utc.index)


def scan(feed: pd.Series, ref: pd.Series, utc: pd.Series, dst: pd.Series) -> list[dict]:
    """Per lag: diff-correlation and the EXACT-MATCH share (|feed - ref| < 1 MW)."""
    rows = []
    for lag in LAGS:
        f = feed.copy()
        f.index = f.index + pd.Timedelta(hours=lag)
        f = f[~f.index.duplicated()]
        j = pd.concat(
            {"f": f, "r": ref, "utc": utc, "dst": dst}, axis=1, join="inner"
        ).dropna()
        j["df"], j["dr"] = j["f"].diff(), j["r"].diff()
        j = j.dropna()
        j["win"] = np.where((j["utc"] >= LO) & (j["utc"] <= HI), "IN", "OUT")
        j["year"] = j.index.year
        for (yr, win, reg), g in j.groupby(["year", "win", "dst"]):
            if len(g) > 300:
                rows.append(
                    {
                        "year": yr,
                        "win": win,
                        "regime": "PDT" if reg else "PST",
                        "lag": lag,
                        "n": len(g),
                        "corr": g["df"].corr(g["dr"]),
                        "exact": float(((g["f"] - g["r"]).abs() < 1.0).mean()),
                    }
                )
    return rows


def summarize(rows: list[dict], label: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    out = []
    for key, g in df.groupby(["year", "win", "regime"]):
        g = g.sort_values("corr", ascending=False)
        best, second = g.iloc[0], g.iloc[1]
        at0 = g.loc[g["lag"] == 0, "corr"]
        out.append(
            {
                "ref": label,
                "year": key[0],
                "win": key[1],
                "regime": key[2],
                "n": int(best["n"]),
                "best_lag": int(best["lag"]),
                "corr_best": round(best["corr"], 3),
                "corr_runner": round(second["corr"], 3),
                "corr_lag0": round(float(at0.iloc[0]), 3) if len(at0) else np.nan,
                "exact_best": round(float(g.sort_values("exact").iloc[-1]["exact"]), 3),
                "exact_lag": int(g.sort_values("exact").iloc[-1]["lag"]),
                "exact_lag0": round(float(g.loc[g["lag"] == 0, "exact"].iloc[0]), 3)
                if len(at0)
                else np.nan,
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    ic = pd.read_parquet(IC / "CISO interchange hourly.parquet")
    feed = feed_on_extract_clock(ic)
    tables = []
    for rep, label in (
        (False, "REF-U extract TI unrepaired"),
        (True, "REF-R extract TI repaired"),
    ):
        x = extract_ti(rep)
        dst = _dst(x["utc"])
        tables.append(summarize(scan(feed, x["ti"], x["utc"], dst), label))
    # REF-M: counterparty mirror legs on their own Pacific local clocks (no
    # correction applied to them: an independent submission). Compared leg-by-leg
    # against CISO's legs on the pinned-corrected clock.
    x = extract_ti(False)
    dst = _dst(x["utc"])
    for cp in ("BPAT", "PACW", "NEVP"):
        m = pd.read_parquet(IC / f"{cp} interchange hourly.parquet")
        m = (
            m[m["diba"] == "CISO"]
            .groupby("local_time")["mw"]
            .sum(min_count=1)
            .sort_index()
        )
        # counterparty hour-ending local stamps -> start-of-hour local wall clock
        # Counterparty stamps read on an HONEST Pacific wall clock (hour-ending):
        # -> UTC -> LST start-of-hour. No correction constant is applied to them.
        mirror = pd.Series(
            m.to_numpy(),
            index=_pac_to_utc(pd.DatetimeIndex(m.index)) - pd.Timedelta(hours=9),
        )
        mirror = mirror[~mirror.index.duplicated()]
        leg = (
            ic[ic["diba"] == cp]
            .groupby("local_time")["mw"]
            .sum(min_count=1)
            .mul(-1)
            .sort_index()
        )
        leg = pd.Series(
            leg.to_numpy(),
            index=envelopes._caiso_interchange_model_clock(pd.DatetimeIndex(leg.index)),
        )
        # mirror: +mw = cp exports to CISO = CISO import; leg = CISO net import from cp
        tables.append(summarize(scan(leg, mirror, x["utc"], dst), f"REF-M {cp} mirror"))
    out = pd.concat(tables, ignore_index=True)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))
    out.to_csv(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", index=False)


if __name__ == "__main__":
    main()
