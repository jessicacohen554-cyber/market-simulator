"""PJM-NEXT-19 card 1 (zero LP): real offered supply vs the model's in model-coal-set hours.

A "coal-set hour" is a model hour whose marginal weight is >= 0.5 on COAL_* (NEXT-18,
from the keeper's committed ``unit_marginal_<y>.parquet``). Two price tests per hour:
``X_coal`` = the model's marginal coal offer (median marginal COAL_* ``mc``) and
``X_rt`` = the actual RT price. For each, the MW offered below it:

* REAL — DataMiner2 ``energy_market_offers``. Step curve: segment ``(mw_{k-1}, mw_k]``
  at ``bid_k`` (the derive's convention), capped at the row's ``avg_ecomax`` (the
  economic range). Units are segmented by the derive's own physics rules
  (``_unit_physics`` + ``_segments`` on the year's present files; NUCLEAR = ecomin ratio
  >= 0.95 and EcoMax >= 800 MW; ZERO = median curve top < $1, i.e. renewables/hydro/
  storage, excluded on both sides). The feed carries no fuel, and CC_LIKE (min-run
  2-16 h, ecomin share > 0.2) also captures coal and gas-steam units, so each priced unit
  is further tagged GAS-TRACKING when the correlation of its daily median mid-curve offer
  (bid at 50 % of EcoMax) with the daily delivered-gas price is >= ``GAS_CORR`` — a
  diagnostic identity, reported at three cut-offs.
* MODEL — the keeper's LP units by fuel, ``cap_mw`` (hourly available MW) priced at
  ``mc``; hydro, imports and virtuals excluded.

Also a capacity-weighted implied-heat-rate ladder (price / the model's delivered-gas
day price, ``_pjm_fuel_daily``; a common denominator, so the ladders compare in $/MWh).
Hours are EPT hour-of-year (the ``_pjmnext11`` convention). Only months whose offer file
is present are scored; the month set is recorded.

Run: ``python3 scripts/probes/_pjmnext19_cc_vs_coal_stack.py <year> [...]``
Writes ``results/phase0/pjm/_pjmnext19_cc_vs_coal_stack.json`` (merged per year).
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
    _segments,
    _unit_physics,
)
from scripts.data.derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    NUCLEAR_ECOMIN_RATIO,
    NUCLEAR_MIN_ECOMAX_MW,
    ZERO_TOP_FLOOR_USD,
    _pjm_fuel_daily,
)

RAW = REPO / "data/raw/pjm-energy-offers"
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext19_cc_vs_coal_stack.json"
T = 8760
#: Share of an hour's marginal weight on coal for it to count as coal-set (NEXT-18).
COAL_SET_WEIGHT = 0.5
#: Diagnostic gas-tracking cut-offs (correlation of daily mid offer with gas).
GAS_CORRS = (0.5, 0.6, 0.7)
GAS_CORR = 0.6
MODEL_FUELS = ("coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear")
#: Implied-HR ladder edges (x delivered gas) — resolution only.
HR_EDGES = (-np.inf, 0.0, 5.0, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 12.0, np.inf)


def _ladder(ihr: np.ndarray, w: np.ndarray) -> dict[str, float]:
    """Share of weight per implied-HR cell."""
    b = np.clip(np.searchsorted(HR_EDGES, ihr, side="right") - 1, 0, len(HR_EDGES) - 2)
    s = np.bincount(b, weights=w, minlength=len(HR_EDGES) - 1) / max(w.sum(), 1e-9)
    return {
        f"{HR_EDGES[i]:g}..{HR_EDGES[i + 1]:g}": round(float(s[i]), 3)
        for i in range(len(HR_EDGES) - 1)
    }


def _coal_set(y: int, months: set[int]) -> tuple[np.ndarray, pd.DataFrame]:
    """Coal-set hours in ``months`` and the keeper unit frame restricted to them."""
    cols = ["plant_group", "fuel", "hour", "mc", "cap_mw", "mw", "marginal"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[u.hour < T]
    m = u[u.marginal == 1].copy()
    m["coal"] = m.plant_group.astype(str).str.startswith("COAL")
    m["w"] = 1.0 / m.groupby("hour").hour.transform("size")
    cw = m[m.coal].groupby("hour").w.sum()
    hrs = cw[cw >= COAL_SET_WEIGHT].index.to_numpy()
    mon = pd.date_range(f"{y}-01-01", periods=T, freq="h").month.to_numpy()
    hrs = np.sort(hrs[np.isin(mon[hrs], sorted(months))])
    coal_mc = m[m.coal].groupby("hour").mc.median().reindex(hrs).to_numpy()
    return hrs, coal_mc, u[u.hour.isin(hrs)]


def _model_side(u: pd.DataFrame, x: dict[str, pd.Series], gas: np.ndarray) -> dict:
    """Model MW below each test price, by fuel, mean over scored hours."""
    u = u[u.fuel.astype(str).isin(MODEL_FUELS) & (u.cap_mw > 0)]
    f = u.fuel.astype(str).to_numpy()
    out: dict = {"cap_gw": {}, "gen_gw": {}}
    n = len(next(iter(x.values())))
    for fu in MODEL_FUELS:
        s = f == fu
        out["cap_gw"][fu] = round(u.cap_mw.to_numpy(float)[s].sum() / n / 1e3, 2)
        out["gen_gw"][fu] = round(u.mw.to_numpy(float)[s].sum() / n / 1e3, 2)
    for k, xs in x.items():
        px = xs.reindex(u.hour).to_numpy()
        below = np.where(u.mc.to_numpy(float) < px, u.cap_mw.to_numpy(float), 0.0)
        out[f"below_{k}_gw"] = {
            fu: round(below[f == fu].sum() / n / 1e3, 2) for fu in MODEL_FUELS
        }
    cc = f == "gas_cc"
    ihr = u.mc.to_numpy(float)[cc] / gas[u.hour.to_numpy()[cc]]
    out["gas_cc_ihr_ladder"] = _ladder(ihr, u.cap_mw.to_numpy(float)[cc])
    return out


def _real_rows(files: list[Path], hrs: np.ndarray, y: int, fuel: pd.Series):
    """Yield per-month arrays for offer rows in the scored hours (+ all-day mid offers)."""
    t0 = pd.Timestamp(f"{y}-01-01")
    hset = set(hrs.tolist())
    cols = ["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
    for p in files:
        df = pd.read_parquet(p, columns=cols + _BID_COLS + _MW_COLS)
        df = df[df.avg_ecomax > 0]
        ts = pd.to_datetime(
            df.bid_datetime_beginning_ept, format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        h = ((ts - t0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
        emax = df.avg_ecomax.to_numpy(float)
        mws = np.minimum(df[_MW_COLS].to_numpy(float), emax[:, None])
        bids = df[_BID_COLS].to_numpy(float)
        prev = np.concatenate([np.zeros((len(mws), 1)), mws[:, :-1]], axis=1)
        seg = np.clip(
            np.where(np.isfinite(mws), mws - np.nan_to_num(prev), 0.0), 0, None
        )
        valid = np.isfinite(mws) & np.isfinite(bids) & (seg > 0)
        seg = np.where(valid, seg, 0.0)
        bids = np.where(valid, bids, np.nan)
        # mid-curve offer: first breakpoint at or above 50 % of EcoMax
        k = np.argmax(np.nan_to_num(mws, nan=-1) >= 0.5 * emax[:, None], axis=1)
        mid = bids[np.arange(len(bids)), k]
        day = ts.dt.normalize()
        g = fuel.reindex(pd.DatetimeIndex(day)).to_numpy(float)
        yield {
            "unit": df.unit_code.astype(str).to_numpy(),
            "hour": h,
            "in_scope": np.isin(h, list(hset)),
            "seg": seg,
            "bids": bids,
            "mid": mid,
            "day": day.to_numpy(),
            "gas": g,
        }
        print(f"  {p.name}", flush=True)


def run_year(y: int) -> dict:
    """Score one year on its present offer month files."""
    files = sorted(RAW.glob(f"pjm_energy_offers_{y:04d}_*.parquet"))
    months = {int(p.stem.split("_")[-1]) for p in files}
    hrs, coal_mc, u = _coal_set(y, months)
    act = pd.read_parquet(ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
    x = {"coal": pd.Series(coal_mc, index=hrs), "rt": pd.Series(rt[hrs], index=hrs)}
    days = pd.date_range(f"{y}-01-01", periods=T, freq="h").normalize()
    fuel = _pjm_fuel_daily()
    gas_h = fuel.reindex(days).to_numpy(float)
    model = _model_side(u, x, gas_h)

    per_unit = _unit_physics(files)
    seg_of = pd.Series("OTHER", index=per_unit.index)
    for name, idx in _segments(per_unit).items():
        seg_of[idx] = name
    nuc = (per_unit.ratio >= NUCLEAR_ECOMIN_RATIO) & (
        per_unit.ecomax >= NUCLEAR_MIN_ECOMAX_MW
    )
    seg_of[nuc] = "NUCLEAR"
    seg_of[(per_unit.top < ZERO_TOP_FLOOR_USD) & ~nuc] = "ZERO"

    # pass A: per-unit daily mid offer vs gas -> gas-tracking correlation
    mids, chunks = [], []
    for r in _real_rows(files, hrs, y, fuel):
        mids.append(pd.DataFrame({"unit": r["unit"], "day": r["day"], "mid": r["mid"]}))
        s = r["in_scope"]
        chunks.append(
            {k: (v[s] if isinstance(v, np.ndarray) else v) for k, v in r.items()}
        )
    md = pd.concat(mids).groupby(["unit", "day"]).mid.median().reset_index()
    md["gas"] = fuel.reindex(pd.DatetimeIndex(md.day)).to_numpy(float)
    corr = md.dropna().groupby("unit")[["mid", "gas"]].corr().xs("mid", level=1)["gas"]

    real: dict = {}
    for cut in GAS_CORRS:
        gt = set(corr[corr >= cut].index)
        tag = f"gas_tracking_{cut:g}"
        real[tag] = {}
        for k, xs in x.items():
            tot = {}
            for c in chunks:
                lab = seg_of.reindex(c["unit"]).fillna("OTHER").to_numpy()
                lab = np.where(
                    np.isin(c["unit"], list(gt)) & (lab != "ZERO"), "GAS_TRK", lab
                )
                px = xs.reindex(c["hour"]).to_numpy()[:, None]
                b = np.where(c["bids"] < px, c["seg"], 0.0).sum(axis=1)
                for name in np.unique(lab):
                    tot.setdefault(name, [0.0, 0.0])
                    tot[name][0] += b[lab == name].sum()
                    tot[name][1] += c["seg"][lab == name].sum()
            real[tag][f"below_{k}_gw"] = {
                n: round(v[0] / len(hrs) / 1e3, 2) for n, v in tot.items()
            }
            real[tag]["cap_gw"] = {
                n: round(v[1] / len(hrs) / 1e3, 2) for n, v in tot.items()
            }
        if cut == GAS_CORR:
            ih, w = [], []
            for c in chunks:
                s = np.isin(c["unit"], list(gt))
                ih.append((c["bids"][s] / c["gas"][s, None]).ravel())
                w.append(c["seg"][s].ravel())
            ih, w = np.concatenate(ih), np.concatenate(w)
            ok = np.isfinite(ih) & (w > 0)
            real["gas_tracking_ihr_ladder"] = _ladder(ih[ok], w[ok])
            real["gas_tracking_units"] = len(gt)
    real["segment_units"] = seg_of.value_counts().to_dict()
    return {
        "months": sorted(months),
        "coal_set_hours_scored": int(len(hrs)),
        "median_coal_offer": round(float(np.median(coal_mc)), 2),
        "median_actual_rt": round(float(np.median(rt[hrs])), 2),
        "median_gas": round(float(np.median(gas_h[hrs])), 3),
        "model": model,
        "real": real,
    }


def main() -> None:
    """Score the requested years; merge into the JSON artifact."""
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in [int(a) for a in sys.argv[1:]]:
        res[str(y)] = run_year(y)
        print(y, json.dumps(res[str(y)], indent=1), flush=True)
        OUT.write_text(json.dumps(res, indent=1, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
