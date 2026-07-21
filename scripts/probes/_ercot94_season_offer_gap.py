"""ERCOT-94 MEASURE probe — DJF-vs-JJA offer-level gap in the high net-load bins.

Measure-first (ERCOT-89/90/92 cadence) for the season-conditioned offer-wall
price ladder (ERCOT-94 charter). The ERCOT-93 steam RT wall tripped the
zero-spurious §6 gate on the Jan-14/15 winter cold snap because the wall's
price ladder is net-load-percentile-bin-conditioned ONLY: the not-RT-scarce
winter high-net-load cold snap draws the summer-scarcity-dominated expensive
high-bin ladder. This probe quantifies the winter (DJF) vs summer (JJA)
posted-offer level in each net-load bin, BEFORE any wall is season-resolved, to
prove the season axis is a real measured signal (rule 1: measure first; rule 13
bright line: only the conditional distribution, never a per-hour outcome).

For each delivery year and class (ST_GAS steam; CC/CT for context), per
net-load percentile bin x meteorological season, it reports the MW-weighted
p50 (and p10/p90) of the SCED online-spare offer as an effective-HR multiplier
(price / delivered-gas day), plus the interval coverage per cell (so an
under-sampled DJF high-bin cell is visible, not silently trusted). The headline
is the DJF/JJA p50 ratio in the high bins (b4/b5/b6), i.e. how much cheaper the
winter cold-snap online-spare offer was than the pooled summer ladder the
ERCOT-93 wall applied.

Read-only measurement: writes nothing, changes no solve. Reuses the offer-wall
derives' exact helpers so the numbers match what a season-resolved derive would
emit.

Usage::

    .venv/bin/python scripts/probes/_ercot94_season_offer_gap.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    HOURS,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    CLASS_OF_RESTYPE,
    _STD_TZ,
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
    _spare_segments,
)
from derive_ercot_sced_offer_wall_steam import (  # noqa: E402
    ST_RESTYPES,
    _READ_COLS,
    _scope_fleet,
)
from derive_ercot_shoulder_online_span import SEASON_OF_MONTH  # noqa: E402

SEASON_NAME = ("DJF", "MAM", "JJA", "SON")
# CC/CT read cols reuse the CC/CT derive's set; steam uses its own (_READ_COLS).
_CCCT_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_CCCT_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_CCCT_READ = [
    "SCED Time Stamp",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "Base Point",
] + [c for pair in zip(_CCCT_MW, _CCCT_PR) for c in pair]


def _season_of_hoy(hoy: np.ndarray) -> np.ndarray:
    """Meteorological season index (0=DJF..3=SON) for each hour-of-year."""
    month = np.searchsorted(np.append(_MONTH_START_HOUR[1:], HOURS), hoy, side="right")
    return np.asarray(SEASON_OF_MONTH, dtype=int)[month]


def _accumulate(year: int, steam: bool, gas_day: pd.Series):
    """Stream shards -> per (bin, season, cls) multiplier + MW arrays.

    Returns {(cls, bin, season): (mult_array, mw_array)} accumulators, keyed by
    concatenation at the end.
    """
    files = _sced_source_files(year)
    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)

    restypes = ST_RESTYPES if steam else tuple(CLASS_OF_RESTYPE)
    read_cols = _READ_COLS if steam else _CCCT_READ
    mult_acc: dict = {}
    mw_acc: dict = {}
    iv_acc: dict = {}
    for path in files:
        chunk = pd.read_parquet(path, columns=read_cols)
        chunk = _delivery_year_rows(chunk, year)
        chunk = chunk[chunk["Resource Type"].isin(restypes)]
        if chunk.empty:
            continue
        chunk = _coerce_sced_numeric(chunk)
        if steam:
            fleet, _exc = _scope_fleet(chunk)
        else:
            fleet = chunk
        del chunk
        stat = fleet["Telemetered Resource Status"].astype(str).str.strip()
        df = fleet[stat.str.startswith("ON")].copy()
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert(_STD_TZ)
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        df["cls"] = (
            "ST" if steam else df["Resource Type"].map(CLASS_OF_RESTYPE)
        )
        df["_ts_key"] = df["SCED Time Stamp"].to_numpy()
        dates = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)]
        df["gas_day"] = gas_day.reindex(pd.DatetimeIndex(dates)).to_numpy(float)
        df = df[df["gas_day"] > 0]
        if df.empty:
            continue
        seg = _spare_segments(df)
        if seg.empty:
            continue
        date_by_ts = dict(zip(df["_ts_key"], df["gas_day"]))
        mult = (seg["price"] / seg["ts"].map(date_by_ts).astype(float)).to_numpy()
        hoy = seg["hoy"].to_numpy(int)
        b = hour_bin[np.minimum(hoy, HOURS - 1)]
        s = _season_of_hoy(np.minimum(hoy, HOURS - 1))
        mw = seg["mw"].to_numpy()
        cls = seg["cls"].to_numpy()
        for key in set(zip(cls.tolist(), b.tolist(), s.tolist())):
            m = (cls == key[0]) & (b == key[1]) & (s == key[2])
            mult_acc.setdefault(key, []).append(mult[m])
            mw_acc.setdefault(key, []).append(mw[m])
            iv_acc[key] = iv_acc.get(key, 0) + int(
                len(set(seg["ts"].to_numpy()[m]))
            )
    return mult_acc, mw_acc, iv_acc


def _report(year: int, steam: bool, gas_day: pd.Series) -> None:
    mult_acc, mw_acc, iv_acc = _accumulate(year, steam, gas_day)
    label = "ST_GAS" if steam else "CC/CT"
    classes = sorted({k[0] for k in mult_acc})
    n_bins = len(NETLOAD_PCT_EDGES) + 1
    print(f"\n===== {year} {label} : p50 offer multiplier by bin x season =====")
    for cls in classes:
        print(f"\n  class {cls}  (rows: p50 mult; parens: interval count)")
        header = "  bin  " + "".join(f"{SEASON_NAME[s]:>16}" for s in range(4))
        print(header)
        for b in range(n_bins):
            cells = []
            for s in range(4):
                key = (cls, b, s)
                if key in mult_acc:
                    mult = np.concatenate(mult_acc[key])
                    mw = np.concatenate(mw_acc[key])
                    p50 = _weighted_quantiles(mult, mw, (0.5,))[0]
                    cells.append(f"{p50:7.2f}({iv_acc[key]:5d})")
                else:
                    cells.append(f"{'--':>7}(    0)")
            lo = 0.0 if b == 0 else NETLOAD_PCT_EDGES[b - 1]
            hi = 1.0 if b == n_bins - 1 else NETLOAD_PCT_EDGES[b]
            print(f"  b{b} [{lo:.2f}-{hi:.2f}] " + "".join(f"{c:>16}" for c in cells))
        # Headline: DJF/JJA p50 ratio in the high bins (b4,b5,b6).
        print("  --- DJF vs JJA p50 in high net-load bins (b4/b5/b6) ---")
        for b in (4, 5, 6):
            kd, kj = (cls, b, 0), (cls, b, 2)
            if kd in mult_acc and kj in mult_acc:
                pd_ = _weighted_quantiles(
                    np.concatenate(mult_acc[kd]), np.concatenate(mw_acc[kd]), (0.5,)
                )[0]
                pj = _weighted_quantiles(
                    np.concatenate(mult_acc[kj]), np.concatenate(mw_acc[kj]), (0.5,)
                )[0]
                ratio = pd_ / pj if pj else float("nan")
                print(
                    f"    b{b}: DJF p50 {pd_:7.2f} ({iv_acc[kd]:5d} iv)  vs  "
                    f"JJA p50 {pj:7.2f} ({iv_acc[kj]:5d} iv)  ->  DJF/JJA = {ratio:.2f}"
                )
            else:
                have = "DJF" if kd in mult_acc else ""
                have += " JJA" if kj in mult_acc else ""
                print(f"    b{b}: incomplete coverage (have:{have or 'none'})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--cc-ct", action="store_true", help="also report CC/CT")
    args = ap.parse_args()
    print(f"HCAP={HCAP_USD_MWH} ladder_q={LADDER_QUANTILES} bins={NETLOAD_PCT_EDGES}")
    gas_day = _gas_day_series()
    for y in args.years:
        _report(y, steam=True, gas_day=gas_day)
        if args.cc_ct:
            _report(y, steam=False, gas_day=gas_day)


if __name__ == "__main__":
    main()
