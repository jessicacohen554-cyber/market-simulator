"""PJM-NEXT-21 card 2 (zero LP): coal offer-curve shape, PJM's own offers vs the keeper.

NEXT-20 card 1 located the COAL_BIT over-run in the keeper's in-merit LOADING response:
at $0-15 of margin (actual RT minus the plant's MW-weighted keeper offer), with the real
plant online, the keeper loads +0.04..+0.11 more of its capacity than real coal in
2019-21 and 2025, and -0.01..+0.06 in 2023/24. Real coal's curve is near-identical across
years. This probe asks whether the keeper's econ LADDER is steeper than PJM's own coal
offer curves over the same band, and whether that difference orders the years.

Shape metric (both sides, per unit-hour / plant-hour, over the dispatchable range above
the floor):

* PJM offers: range = [avg_ecomin, avg_ecomax]; each curve segment's MW inside it carries
  its bid. Population: NEXT-17's ``COALLIKE`` heuristic (LONG_RUN units whose daily
  MW-weighted bid does not track daily PJM delivered gas, r < 0.5) - a declared heuristic,
  not a fuel identity (the feed is anonymised).
* Keeper: ``unit_marginal_<y>`` COAL_* tranches; range = econ (``_econ*``) + ``_peak``
  tranches (the floor is ``_mustrun`` + ``_committed``); each tranche's ``cap_mw`` at its
  ``mc``.

Per curve: ``mu`` = MW-weighted mean price of the range; ``S(d)`` = share of the range's
MW priced <= mu + d for d in (-5, 0, 5, 15) $/MWh; ``iqr`` = p75 - p25 of price over the
range's MW. Fleet medians weighted by range MW, for the months the offers corpus carries
(Jan/Apr/Jul/Oct refetch); the keeper is restricted to the same months.

Writes ``results/phase0/pjm/_pjmnext21_coal_offer_slope.json``.
Run: ``.venv/bin/python scripts/probes/_pjmnext21_coal_offer_slope.py``
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
    _segments,
    _unit_physics,
)
from scripts.data.derive_pjm_offer_surface import RAW_DIR, _pjm_fuel_daily  # noqa: E402

YEARS = tuple(range(2019, 2026))
MONTHS = (1, 4, 7, 10)
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
OUT = REPO / "results/phase0/pjm/_pjmnext21_coal_offer_slope.json"
DS = (-5.0, 0.0, 5.0, 15.0)
GAS_R_MAX = 0.5  # NEXT-17 COALLIKE heuristic, unchanged
STRIDE = 3  # hour sample (every 3rd hour) on both sides
T = 8760


def _curve_stats(mw: np.ndarray, px: np.ndarray) -> dict[str, np.ndarray]:
    """Per-row shape stats from per-segment range MW ``mw`` and prices ``px`` (n x k).

    Segments are sorted by price within the row first, so the keeper's tranches and
    PJM's (monotone) curves are read the same way.
    """
    o = np.argsort(np.where(mw > 0, px, np.inf), axis=1)
    mw = np.take_along_axis(mw, o, 1)
    px = np.take_along_axis(px, o, 1)
    px = np.where(mw > 0, px, 0.0)
    tot = mw.sum(1)
    mu = (mw * px).sum(1) / np.maximum(tot, 1e-9)
    out = {"tot": tot, "mu": mu}
    for d in DS:
        out[f"S{d:+g}"] = (mw * (px <= (mu + d)[:, None])).sum(1) / np.maximum(
            tot, 1e-9
        )
    cs = np.cumsum(mw, 1) / np.maximum(tot, 1e-9)[:, None]
    for q in (0.25, 0.75):
        k = np.argmax(cs >= q - 1e-9, axis=1)
        out[f"p{int(q * 100)}"] = px[np.arange(len(px)), k]
    out["iqr"] = out["p75"] - out["p25"]
    return out


def _wmed(x: np.ndarray, w: np.ndarray) -> float:
    """Weighted median."""
    ok = np.isfinite(x) & (w > 0)
    x, w = x[ok], w[ok]
    if not len(x):
        return float("nan")
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, 0.5 * c[-1])])


def _summ(st: dict[str, np.ndarray]) -> dict:
    """Range-MW-weighted means of S(d) and weighted median iqr."""
    w = st["tot"]
    rec = {
        f"S{d:+g}": round(float(np.average(st[f"S{d:+g}"], weights=w)), 3) for d in DS
    }
    rec["iqr_median"] = round(_wmed(st["iqr"], w), 2)
    rec["mu_median"] = round(_wmed(st["mu"], w), 2)
    rec["n"] = int(len(w))
    rec["range_gw_mean"] = round(float(w.mean()) / 1e3, 4)
    return rec


def pjm_offers(y: int) -> dict | None:
    """COALLIKE LONG_RUN unit-hour shape stats for year ``y`` (present month files)."""
    files = [
        RAW_DIR / f"pjm_energy_offers_{y:04d}_{m:02d}.parquet"
        for m in MONTHS
        if (RAW_DIR / f"pjm_energy_offers_{y:04d}_{m:02d}.parquet").exists()
    ]
    if not files:
        return None
    phys = _unit_physics(files)
    lr = pd.Index(_segments(phys)["LONG_RUN"])
    gas = _pjm_fuel_daily()
    cols = ["bid_datetime_beginning_ept", "unit_code", "avg_ecomax", "avg_ecomin"]
    frames, stats = [], []
    for p in files:
        df = pd.read_parquet(p, columns=cols + _MW_COLS + _BID_COLS)
        df = df[df.unit_code.astype(str).isin(lr) & (df.avg_ecomax > 0)]
        ts = pd.to_datetime(
            df.bid_datetime_beginning_ept, format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        df = df[(ts.dt.hour % STRIDE == 0).to_numpy()]
        ts = ts[(ts.dt.hour % STRIDE == 0).to_numpy()]
        mws = np.fmax.accumulate(np.nan_to_num(df[_MW_COLS].to_numpy(float)), axis=1)
        bids = df[_BID_COLS].to_numpy(float)
        lo = df.avg_ecomin.to_numpy(float)[:, None]
        hi = df.avg_ecomax.to_numpy(float)[:, None]
        prev = np.concatenate([np.zeros((len(mws), 1)), mws[:, :-1]], axis=1)
        seg = np.clip(np.minimum(mws, hi) - np.maximum(prev, lo), 0.0, None)
        seg = np.where(np.isfinite(bids), seg, 0.0)
        st = _curve_stats(seg, np.nan_to_num(bids))
        keep = st["tot"] > 0
        stats.append({k: v[keep] for k, v in st.items()})
        frames.append(
            pd.DataFrame(
                {
                    "unit": df.unit_code.astype(str).to_numpy()[keep],
                    "day": ts.dt.normalize().to_numpy()[keep],
                    "mu": st["mu"][keep],
                }
            )
        )
        print(f"  {p.name}: {int(keep.sum()):,} LONG_RUN unit-hours", flush=True)
    f = pd.concat(frames, ignore_index=True)
    st = {k: np.concatenate([s[k] for s in stats]) for k in stats[0]}
    dly = f.groupby(["unit", "day"]).mu.mean().reset_index()
    dly["gas"] = gas.reindex(pd.DatetimeIndex(dly.day)).to_numpy(float)
    r = dly.groupby("unit")[["mu", "gas"]].apply(
        lambda g: g.mu.corr(g.gas) if len(g) > 30 and g.mu.std() > 0 else np.nan
    )
    coallike = set(r.index[(r < GAS_R_MAX) | r.isna()])
    m = f.unit.isin(coallike).to_numpy()
    return {
        "months": [int(p.stem.rpartition("_")[2]) for p in files],
        "n_coallike_units": len(coallike),
        "coallike": _summ({k: v[m] for k, v in st.items()}),
        "longrun_all": _summ(st),
    }


def keeper(y: int, months: list[int]) -> dict:
    """Keeper COAL_* econ+peak ladder shape stats for the same months."""
    u = pd.read_parquet(
        HOURLY / f"unit_marginal_{y}.parquet",
        columns=[
            "pass",
            "unit_id",
            "plant_code",
            "plant_group",
            "hour",
            "cap_mw",
            "mc",
        ],
    )
    u = u[(u["pass"] == "P1") & u.plant_group.astype(str).str.startswith("COAL")]
    mon = pd.date_range(f"{y}-01-01", periods=T, freq="h").month.to_numpy()
    u = u[np.isin(mon[u.hour.to_numpy()], months) & (u.hour % STRIDE == 0)]
    uid = u.unit_id.astype(str)
    out = {}
    for lab, pat in (("econ_peak", r"_econ|_peak$"), ("econ_only", r"_econ")):
        e = u[uid.str.contains(pat, regex=True) & (u.cap_mw > 0)]
        e = e.assign(k=e.groupby(["plant_code", "hour"], observed=True).cumcount())
        w = e.pivot_table(
            index=["plant_code", "hour"], columns="k", values="cap_mw", observed=True
        )
        p = e.pivot_table(
            index=["plant_code", "hour"], columns="k", values="mc", observed=True
        )
        out[lab] = _summ(
            _curve_stats(
                np.nan_to_num(w.to_numpy(float)), np.nan_to_num(p.to_numpy(float))
            )
        )
    return out


def main() -> None:
    """Every year with offers present."""
    res: dict = {
        "what": "PJM-NEXT-21 card 2: coal offer-curve shape, PJM COALLIKE offers vs "
        "keeper econ ladder. ZERO LP.",
        "keeper_bundle": str(HOURLY.relative_to(REPO)),
        "metric": "S(d) = share of range MW priced <= MW-weighted mean + d; iqr $",
        "years": {},
    }
    for y in YEARS:
        print(y, flush=True)
        po = pjm_offers(y)
        if po is None:
            print("  no offers", flush=True)
            continue
        res["years"][str(y)] = {"pjm": po, "keeper": keeper(y, po["months"])}
        print(json.dumps(res["years"][str(y)]), flush=True)
    OUT.write_text(json.dumps(res, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
