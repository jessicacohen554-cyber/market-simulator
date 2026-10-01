"""PJM-NEXT-17 (zero LP): do REAL PJM coal-like units under-dispatch their OWN offers?

Owner card "Dispatch-vs-offer audit". The keeper's COAL_BIT class over-runs CAMPD in
2019/2020/2021/2025 as higher LOADING when on; prior lanes found the model's coal offers sit
at 0.93-1.04x PJM's own measured offers. The unmeasured link: at the ACTUAL price, do real
coal-like units generate less than their own offers imply (a non-offer operating constraint),
while the model dispatches at its offers?

Fleet-level, hourly (the offers feed carries no dispatched MW and no fuel/plant identity):

* ``D``    = sum over PJM LONG_RUN unit-hours of offer-implied MW at the actual PJM DA LMP
  (``_pjmnext11_offered_ecomax.offer_dispatch``, clipped to ``avg_ecomax``);
* ``Dm``   = the same at the keeper's hourly load-weighted P1 price (zones excl. PJM_external);
* ``Dfl`` / ``Dmfl`` = per-row ``max(D, avg_ecomin)`` (every offering unit held at least at
  its EcoMin -- the "committed" reading; offline units also carry offer rows, so both D and
  Dfl are fleet proxies, not dispatch of committed units);
* ``Emin`` / ``E`` = sums of ``avg_ecomin`` / ``avg_ecomax``;
* actual   = CAMPD COAL_BIT hourly from ``bench/PJM/<y>.json.gz`` (``_pjmnext16._dec``);
* model    = keeper ``pjmnext16_A_span`` P1 ``class_hourly`` COAL_BIT.

Scale-free comparison: ``actual/D`` vs ``model/Dm``, annual and binned by actual DA LMP.
POPULATION MISMATCH: LONG_RUN (min_runtime > 16 h, not nuclear-like, not $0-top) is NOT the
COAL_BIT class -- it carries PRB/WC coal and any long-min-run gas steam / CC. A sensitivity
subset ``COALLIKE`` keeps LONG_RUN units whose daily MW-weighted mean bid does NOT track the
daily PJM delivered gas price (within-year Pearson r < ``GAS_R_MAX``): a declared heuristic,
not a fuel identity. Hours: the offers' EPT hour-of-year (the ``_pjmnext11`` convention) is
taken as the axis of the actual LMP, CAMPD and model series (lag 0); the best-correlation lag
of each series is reported, not applied. Months whose offer file is absent are excluded from
EVERY series (hour mask). Writes ``results/calibration/_pjmnext17_coal_offer_audit.json``.
"""

from __future__ import annotations

import gzip
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
from scripts.probes._pjmnext11_offered_ecomax import offer_dispatch  # noqa: E402
from scripts.probes._pjmnext16_cc_loading import _dec  # noqa: E402

YEARS = tuple(range(2019, 2026))
T = 8760
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
OUT = REPO / "results/calibration/_pjmnext17_coal_offer_audit.json"
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC")
BINS = (0.0, 15.0, 25.0, 35.0, 50.0, 75.0)
BIN_LABELS = ("0-15", "15-25", "25-35", "35-50", "50-75", ">75")
#: Coal-like heuristic: within-year r(daily mean bid, daily gas) below this.
GAS_R_MAX = 0.5
#: Nuclear-suspect flag inside LONG_RUN (reported only).
NUC_RATIO = 0.9


def _model(y: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Keeper P1 class MW by hour and the load-weighted system price."""
    ch = pd.read_parquet(HOURLY / f"class_hourly_{y}.parquet")
    cm = (
        ch[ch["pass"] == "P1"]
        .pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        )
        .reindex(range(T))
        .fillna(0.0)
    )
    s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone != "PJM_external")]
    s = s.assign(pd_=s.price * s.demand)
    g = s.groupby("hour")[["pd_", "demand"]].sum().reindex(range(T))
    return cm, (g.pd_ / g.demand).to_numpy(float)


def _campd(y: int) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """CAMPD hourly MW per coal group and the groups' nameplate (plants with data)."""
    bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
    mw = {k: np.zeros(T) for k in COAL}
    cap = {k: 0.0 for k in COAL}
    for bp in bench["plants"].values():
        g = bp.get("group")
        if g not in COAL or bp.get("nodata") or not bp.get("campd"):
            continue
        a = _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))[:T]
        mw[g][: len(a)] += a
        if a.sum() > 0:
            cap[g] += float(bp.get("npl") or 0.0)
    return mw, cap


def _offers(y: int, lmp: np.ndarray, mlmp: np.ndarray) -> tuple[pd.DataFrame, dict]:
    """LONG_RUN unit-hour slim frame for the year's present month files."""
    files = sorted(RAW_DIR.glob(f"pjm_energy_offers_{y:04d}_*.parquet"))
    if not files:
        return pd.DataFrame(), {"months": []}
    phys = _unit_physics(files)
    lr = pd.Index(_segments(phys)["LONG_RUN"])
    gas = _pjm_fuel_daily()
    parts = []
    cols = ["bid_datetime_beginning_ept", "unit_code", "avg_ecomax", "avg_ecomin"]
    for p in files:
        df = pd.read_parquet(p, columns=cols + _MW_COLS + _BID_COLS)
        df = df[df.unit_code.astype(str).isin(lr)]
        mws = df[_MW_COLS].to_numpy(float)
        top = np.nanmax(np.where(np.isfinite(mws), mws, -np.inf), axis=1)
        keep = (df.avg_ecomax.to_numpy(float) > 0) & (top > 0)
        df, mws, top = df[keep], mws[keep], top[keep]
        bids = df[_BID_COLS].to_numpy(float)
        ts = pd.to_datetime(
            df.bid_datetime_beginning_ept, format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        hoy = (
            ((ts - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h"))
            .astype(int)
            .to_numpy()
        )
        hoy_c = np.clip(hoy, 0, T - 1)
        price = np.where((hoy >= 0) & (hoy < T), lmp[hoy_c], np.nan)
        mprice = np.where((hoy >= 0) & (hoy < T), mlmp[hoy_c], np.nan)
        e = df.avg_ecomax.to_numpy(float)
        d = np.minimum(offer_dispatch(mws, bids, price), e)
        dm = np.minimum(offer_dispatch(mws, bids, mprice), e)
        # MW-weighted mean step price over the curve (for the gas-tracking split).
        m0 = np.where(np.isfinite(mws), mws, np.nan)
        step = np.diff(
            np.concatenate(
                [
                    np.zeros((len(m0), 1)),
                    np.fmax.accumulate(np.nan_to_num(m0, nan=0.0), axis=1),
                ],
                axis=1,
            ),
            axis=1,
        )
        b0 = np.where(np.isfinite(bids), bids, 0.0)
        mbid = (b0 * step).sum(axis=1) / np.maximum(step.sum(axis=1), 1e-9)
        parts.append(
            pd.DataFrame(
                {
                    "unit": df.unit_code.astype(str).to_numpy(),
                    "hoy": hoy,
                    "day": ts.dt.normalize().to_numpy(),
                    "D": d,
                    "Dm": dm,
                    "E": e,
                    "Emin": df.avg_ecomin.to_numpy(float),
                    "Dfl": np.maximum(d, df.avg_ecomin.to_numpy(float)),
                    "Dmfl": np.maximum(dm, df.avg_ecomin.to_numpy(float)),
                    "mbid": mbid,
                }
            )
        )
        print(f"  {p.name}: {keep.sum():,} LONG_RUN rows", flush=True)
    f = pd.concat(parts, ignore_index=True)
    f = f[(f.hoy >= 0) & (f.hoy < T)]
    # Per-unit gas tracking.
    dly = f.groupby(["unit", "day"]).mbid.mean().reset_index()
    dly["gas"] = gas.reindex(pd.DatetimeIndex(dly.day)).to_numpy(float)
    r = dly.groupby("unit")[["mbid", "gas"]].apply(
        lambda g: g.mbid.corr(g.gas) if len(g) > 30 and g.mbid.std() > 0 else np.nan
    )
    coallike = set(r.index[(r < GAS_R_MAX) | r.isna()])
    umax = f.groupby("unit").E.max()
    ratio = phys.reindex(lr)["ratio"]
    meta = {
        "months": [int(p.stem.rpartition("_")[2]) for p in files],
        "n_longrun_units": int(len(lr)),
        "longrun_umax_gw": round(float(umax.sum()) / 1e3, 2),
        "n_coallike_units": int(len(coallike & set(umax.index))),
        "coallike_umax_gw": round(
            float(umax[umax.index.isin(coallike)].sum()) / 1e3, 2
        ),
        "gas_tracking_umax_gw": round(
            float(umax[~umax.index.isin(coallike)].sum()) / 1e3, 2
        ),
        "nuclear_suspect_ratio_ge_0p9_umax_gw": round(
            float(umax[umax.index.isin(ratio.index[ratio >= NUC_RATIO])].sum()) / 1e3, 2
        ),
        "gas_r_quantiles": {
            str(q): round(float(r.quantile(q)), 3) for q in (0.1, 0.25, 0.5, 0.75, 0.9)
        },
        "median_ecomin_ratio_longrun": round(float(ratio.median()), 3),
    }
    f["coallike"] = f.unit.isin(coallike)
    return f, meta


def _hourly(f: pd.DataFrame) -> pd.DataFrame:
    """Sum the unit-hour quantities to an 8760 hourly frame (NaN where no offers)."""
    return (
        f.groupby("hoy")[["D", "Dm", "E", "Emin", "Dfl", "Dmfl"]]
        .sum()
        .reindex(range(T))
    )


def _best_lag(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> dict:
    """Lag k maximising corr(a, roll(b, k)) on masked hours, and corr at 0."""
    best, arg = -2.0, 0
    for k in range(-8, 9):
        bb = np.roll(b, k)
        c = np.corrcoef(a[mask], bb[mask])[0, 1]
        if c > best:
            best, arg = c, k
    c0 = np.corrcoef(a[mask], b[mask])[0, 1]
    return {"lag": arg, "r_best": round(float(best), 3), "r_lag0": round(float(c0), 3)}


def _block(
    h: pd.DataFrame,
    act: np.ndarray,
    mod: np.ndarray,
    lmp: np.ndarray,
    mask: np.ndarray,
    k: float,
) -> dict:
    """Annual + price-bin comparison for one offer population.

    ``k`` = CAMPD coal capacity / population Umax (for the indicative Emin..D position).
    """
    D, Dm, E, Em, Df, Dmf = (
        h[c].to_numpy(float) for c in ("D", "Dm", "E", "Emin", "Dfl", "Dmfl")
    )
    tw = lambda x: round(float(np.nansum(x[mask])) / 1e6, 2)  # noqa: E731
    out = {
        "D_twh": tw(D),
        "Dm_twh": tw(Dm),
        "Emin_twh": tw(Em),
        "E_twh": tw(E),
        "actual_over_D": round(float(act[mask].sum() / D[mask].sum()), 3),
        "model_over_Dm": round(float(mod[mask].sum() / Dm[mask].sum()), 3),
        "Emin_over_D": round(float(Em[mask].sum() / D[mask].sum()), 3),
        "Dm_over_D": round(float(Dm[mask].sum() / D[mask].sum()), 3),
        "Dfl_twh": tw(Df),
        "Dmfl_twh": tw(Dmf),
        "actual_over_Dfl": round(float(act[mask].sum() / Df[mask].sum()), 3),
        "model_over_Dmfl": round(float(mod[mask].sum() / Dmf[mask].sum()), 3),
    }
    # (actual/D) / (model/Dm): < 1 = real units under-run their own offers MORE than the
    # model under-runs the same offers at its own price; == 1 = no conduct difference.
    out["ratio_of_ratios_D"] = round(out["actual_over_D"] / out["model_over_Dm"], 3)
    out["ratio_of_ratios_Dfl"] = round(
        out["actual_over_Dfl"] / out["model_over_Dmfl"], 3
    )
    # Over-run split on the real offers: price-level term = (Dm - D) x actual/D;
    # conduct term = (model/Dm - actual/D) x Dm; the two sum to model - actual.
    a_d = act[mask].sum() / D[mask].sum()
    out["overrun_twh"] = round(float(mod[mask].sum() - act[mask].sum()) / 1e6, 2)
    out["price_level_term_twh"] = round(
        float((Dm[mask].sum() - D[mask].sum()) * a_d) / 1e6, 2
    )
    out["conduct_term_twh"] = round(
        float((mod[mask].sum() / Dm[mask].sum() - a_d) * Dm[mask].sum()) / 1e6, 2
    )
    idx = np.digitize(lmp, BINS[1:])
    bins = {}
    for i, lab in enumerate(BIN_LABELS):
        m = mask & (idx == i)
        if m.sum() < 24:
            continue
        mD, mDm, mEm, mA, mM = (float(np.mean(x[m])) for x in (D, Dm, Em, act, mod))
        bins[lab] = {
            "hours": int(m.sum()),
            "D_mw": round(mD),
            "Dm_mw": round(mDm),
            "Emin_mw": round(mEm),
            "actual_mw": round(mA),
            "model_mw": round(mM),
            "actual_over_D": round(mA / mD, 3) if mD > 0 else None,
            "model_over_Dm": round(mM / mDm, 3) if mDm > 0 else None,
            "Emin_over_D": round(mEm / mD, 3) if mD > 0 else None,
            "actual_over_Dfl": round(mA / float(np.mean(Df[m])), 3),
            "model_over_Dmfl": round(mM / float(np.mean(Dmf[m])), 3),
            "pos_actual_Emin_to_D": round((mA / k - mEm) / (mD - mEm), 3)
            if mD > mEm
            else None,
        }
    out["by_actual_da_lmp"] = bins
    return out


def main() -> None:
    """Run every year whose offer month files exist; write the JSON."""
    actd = pd.read_parquet(ACTUAL)
    res = {
        "what": "PJM-NEXT-17 coal dispatch-vs-own-offer audit. ZERO LP.",
        "keeper_hourly": str(HOURLY.relative_to(REPO)),
        "gas_r_max": GAS_R_MAX,
        "caveat": (
            "LONG_RUN != COAL_BIT (population mismatch); D is a step reading ignoring "
            "commitment/congestion/outages-of-offline units, an upper bound on price-driven "
            "loading; hour axes aligned at lag 0 (EPT hour-of-year)."
        ),
        "years": {},
    }
    for y in YEARS:
        lmp = (
            actd[actd.year == y].set_index("hour").da.reindex(range(T)).to_numpy(float)
        )
        cm, mlmp = _model(y)
        f, meta = _offers(y, lmp, mlmp)
        if f.empty:
            print(f"{y}: no offer files")
            continue
        camp, cap = _campd(y)
        act_bit = camp["COAL_BIT"]
        act_all = sum(camp.values())
        mod_bit = cm["COAL_BIT"].to_numpy(float)
        mod_all = sum(cm[c].to_numpy(float) for c in COAL if c in cm)
        hl = _hourly(f)
        hc = _hourly(f[f.coallike])
        mask = hl.D.notna().to_numpy() & np.isfinite(lmp) & np.isfinite(mlmp)
        cap_bit = cap["COAL_BIT"]
        cap_all = sum(cap.values())
        rec = {
            **meta,
            "hours_covered": int(mask.sum()),
            "campd_coal_bit_twh": round(float(act_bit[mask].sum()) / 1e6, 2),
            "campd_coal_all_twh": round(float(act_all[mask].sum()) / 1e6, 2),
            "model_coal_bit_twh": round(float(mod_bit[mask].sum()) / 1e6, 2),
            "model_coal_all_twh": round(float(mod_all[mask].sum()) / 1e6, 2),
            "campd_coal_bit_npl_gw": round(cap_bit / 1e3, 2),
            "campd_coal_all_npl_gw": round(cap_all / 1e3, 2),
            "lags": {
                "model_price_vs_actual_da": _best_lag(lmp, mlmp, mask),
                "campd_coal_all_vs_D_longrun": _best_lag(
                    hl.D.to_numpy(float), act_all, mask
                ),
                "model_coal_all_vs_Dm_longrun": _best_lag(
                    hl.Dm.to_numpy(float), mod_all, mask
                ),
            },
            "mean_actual_da": round(float(np.mean(lmp[mask])), 2),
            "mean_model_price": round(float(np.mean(mlmp[mask])), 2),
            "LONG_RUN_vs_COAL_BIT": _block(
                hl,
                act_bit,
                mod_bit,
                lmp,
                mask,
                cap_bit / max(meta["longrun_umax_gw"] * 1e3, 1),
            ),
            "LONG_RUN_vs_COAL_ALL": _block(
                hl,
                act_all,
                mod_all,
                lmp,
                mask,
                cap_all / max(meta["longrun_umax_gw"] * 1e3, 1),
            ),
            "COALLIKE_vs_COAL_BIT": _block(
                hc,
                act_bit,
                mod_bit,
                lmp,
                mask,
                cap_bit / max(meta["coallike_umax_gw"] * 1e3, 1),
            ),
            "COALLIKE_vs_COAL_ALL": _block(
                hc,
                act_all,
                mod_all,
                lmp,
                mask,
                cap_all / max(meta["coallike_umax_gw"] * 1e3, 1),
            ),
        }
        res["years"][str(y)] = rec
        b = rec["LONG_RUN_vs_COAL_BIT"]
        print(
            y,
            meta["months"],
            f"D {b['D_twh']} Dm {b['Dm_twh']} act {rec['campd_coal_bit_twh']}",
            f"mod {rec['model_coal_bit_twh']} a/D {b['actual_over_D']} m/Dm {b['model_over_Dm']}",
            flush=True,
        )
        del f
        OUT.write_text(json.dumps(res, indent=1))
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
