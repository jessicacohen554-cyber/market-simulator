"""PJM-NEXT-11 card 1 (zero LP): did PJM's LONG_RUN units OFFER less MW in the coal over-run years?

Reads the PJM DataMiner2 ``energy_market_offers`` corpus (``data/raw/pjm-energy-offers``,
gitignored; ``fetch_pjm_energy_offers.py --years 2019 ... 2025``). The LONG_RUN segment is the
committed mid-curve surface's own physics segmentation, IMPORTED from
``scripts/data/derive_pjm_offer_midcurve.py`` (``_unit_physics`` + ``_segments``, own-year medians,
exactly as each year's surface entry was derived) -- nothing is re-derived and the committed
surface is not touched (rule 23).

Per LONG_RUN unit-hour with ``avg_ecomax > 0``:

* ``E``   = ``avg_ecomax`` (the MW the unit made economically available that hour);
* ``T``   = the offer curve's top breakpoint (``max mw1..mw20``) -- the unit's own stated
  capability in the same row;
* ``Umax``= the unit's maximum ``avg_ecomax`` over the delivery year;
* ``D``   = offer-implied dispatch at the hour's actual PJM DA LMP: the cumulative MW of the
  highest curve step bid at or below the LMP, clipped to ``[0, E]`` (a step reading; ignores
  congestion and commitment, so it is an upper bound on price-driven loading);
* ``Dm``  = the same reading at the KEEPER's hourly load-weighted system P1 price (committed
  ``hourly/system_<y>.parquet``), so ``Dm - D`` is the loading shift the model's price LEVEL
  alone would produce on PJM's own offers.

Shares reported: ``E/T`` (offered-MW share of stated capability), ``E/Umax`` (share of the
unit's own best-offered MW that year), ``D/T`` and ``D/E`` (offer-implied loading).
Rows with ``avg_ecomax == 0`` are counted separately (``T`` MW offered at zero).

Sliced by year, hour-ending, month and the surface's own net-load bin (edges 0.80/0.90/0.97,
``_netload_pct`` within-year). Writes ``results/calibration/_pjmnext11_offered_ecomax.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_pjm_offer_midcurve import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _month_files,
    _netload_pct,
    _segments,
    _unit_physics,
)

YEARS = tuple(range(2019, 2026))
EDGES = (0.80, 0.90, 0.97)
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/calibration/_pjmnext11_offered_ecomax.json"
KEYS = ("E", "T", "Umax", "D", "Dm", "Emin", "n")
BUNDLE = REPO / "results/calibration/pjmnext8_xf_span"


def offer_dispatch(mws: np.ndarray, bids: np.ndarray, lmp: np.ndarray) -> np.ndarray:
    """Cumulative MW of the highest step bid <= LMP (0 when the first step is above it)."""
    ok = np.isfinite(bids) & np.isfinite(mws) & (bids <= lmp[:, None])
    return np.where(ok, mws, 0.0).max(axis=1)


def model_lmp(y: int) -> pd.Series:
    """Keeper hourly load-weighted system P1 price, indexed by hour of year."""
    d = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    d = d[d["pass"] == "P1"]
    d = d.assign(pd_=d.price * d.demand)
    g = d.groupby("hour")[["pd_", "demand"]].sum()
    return g.pd_ / g.demand


def year_frame(
    y: int, lmp: pd.Series, mlmp: pd.Series, nl: pd.DataFrame
) -> pd.DataFrame:
    """LONG_RUN unit-hour frame for one year with the per-row quantities."""
    files, _cov = _month_files([y])
    seg = _segments(_unit_physics(files))
    lr = set(seg["LONG_RUN"])
    parts, zero_t = [], 0.0
    cols = ["bid_datetime_beginning_ept", "unit_code", "avg_ecomax", "avg_ecomin"]
    for p in files:
        df = pd.read_parquet(p, columns=cols + _MW_COLS + _BID_COLS)
        df = df[df.unit_code.astype(str).isin(lr)]
        mws = df[_MW_COLS].to_numpy(float)
        top = np.nanmax(np.where(np.isfinite(mws), mws, -np.inf), axis=1)
        zero = (df.avg_ecomax.to_numpy(float) <= 0) & (top > 0)
        zero_t += float(top[zero].sum())
        keep = (df.avg_ecomax.to_numpy(float) > 0) & (top > 0)
        df, mws, top = df[keep], mws[keep], top[keep]
        ts = pd.to_datetime(
            df.bid_datetime_beginning_ept, format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        hoy = ((ts - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int)
        price = lmp.reindex(hoy.to_numpy()).to_numpy(float)
        e = df.avg_ecomax.to_numpy(float)
        bids = df[_BID_COLS].to_numpy(float)
        d = np.minimum(offer_dispatch(mws, bids, price), e)
        mprice = mlmp.reindex(hoy.to_numpy()).to_numpy(float)
        dm = np.minimum(offer_dispatch(mws, bids, mprice), e)
        parts.append(
            pd.DataFrame(
                {
                    "unit": df.unit_code.astype(str).to_numpy(),
                    "day": ts.dt.normalize().to_numpy(),
                    "he": (ts.dt.hour + 1).to_numpy(),
                    "month": ts.dt.month.to_numpy(),
                    "E": e,
                    "T": top,
                    "D": np.where(np.isfinite(price), d, np.nan),
                    "Dm": np.where(np.isfinite(mprice), dm, np.nan),
                    "Emin": df.avg_ecomin.to_numpy(float),
                }
            )
        )
        print(f"  {p.name}: {keep.sum():,} LONG_RUN rows", flush=True)
    f = pd.concat(parts, ignore_index=True)
    f["Umax"] = f.groupby("unit").E.transform("max")
    f["n"] = 1.0
    f = f.merge(nl, on=["day", "he"], how="left")
    f["bin"] = np.searchsorted(np.asarray(EDGES), f.q.to_numpy(float), side="right")
    f.attrs["zero_offer_T_mwh"] = zero_t
    f.attrs["n_units"] = len(lr)
    return f


def shares(g: pd.DataFrame) -> dict:
    """Aggregate shares for one slice."""
    s = g[list(KEYS)].sum()
    dd = g.dropna(subset=["D", "Dm"])
    hours = len(g[["day", "he"]].drop_duplicates())
    return {
        "E_over_T": round(float(s.E / s["T"]), 4),
        "E_over_Umax": round(float(s.E / s.Umax), 4),
        "D_over_T": round(float(dd.D.sum() / dd["T"].sum()), 4),
        "D_over_E": round(float(dd.D.sum() / dd.E.sum()), 4),
        "Dm_over_E": round(float(dd.Dm.sum() / dd.E.sum()), 4),
        "Emin_over_E": round(float(s.Emin / s.E), 4),
        "avg_E_gw": round(float(s.E / hours / 1e3), 2),
        "avg_T_gw": round(float(s["T"] / hours / 1e3), 2),
        "avg_D_gw": round(float(dd.D.sum() / hours / 1e3), 2),
        "avg_Dm_gw": round(float(dd.Dm.sum() / hours / 1e3), 2),
    }


def main() -> None:
    """Build every slice for the years whose 12 month-files are present."""
    act = pd.read_parquet(ACTUAL)
    nl = _netload_pct([y for y in YEARS], "within-year")
    out = {}
    for y in YEARS:
        try:
            _month_files([y])
        except SystemExit as exc:
            print(f"{y}: skipped ({exc})")
            continue
        lmp = act[act.year == y].set_index("hour").da
        f = year_frame(y, lmp, model_lmp(y), nl)
        rec = {
            "n_units": f.attrs["n_units"],
            "zero_offer_T_twh": round(f.attrs["zero_offer_T_mwh"] / 1e6, 3),
            "year": shares(f),
            "by_bin": {int(b): shares(g) for b, g in f.groupby("bin")},
            "by_he": {int(h): shares(g) for h, g in f.groupby("he")},
            "by_month": {int(m): shares(g) for m, g in f.groupby("month")},
        }
        out[str(y)] = rec
        print(y, rec["n_units"], rec["year"], flush=True)
        del f
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
