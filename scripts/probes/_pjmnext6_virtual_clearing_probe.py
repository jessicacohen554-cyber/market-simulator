"""PJM-NEXT-6 card 2 probe: clear the measured DA virtual-bid curves at ACTUAL DA prices.

Zero-LP diagnostic (never enters a solve). For each backcast year it reads the
measured submitted ``hrl_da_incs_decs`` curves exactly as
``market_sim.data.virtual_bids`` does (same loader, same model-clock join,
same rung compression) and clears them at:

* the ACTUAL hourly PJM DA price — primary basis the published RTO system
  energy price (``energy_usd_per_mwh`` of the clean ``lmp`` DAM datatype,
  identical across every hub pnode, i.e. the RTO-wide reference price the
  RTO-aggregated bid curves are keyed to); sensitivity basis the 12-hub mean
  total DA LMP;
* the MODEL's own hourly zonal duals from the keeper's committed
  ``hourly/system_<y>.parquet`` (load-share-split per zone exactly as
  ``build_pjm_da_virtual_units`` splits rungs), as a reproduction check
  against the keeper's ``VIRTUAL_DEC``/``VIRTUAL_INC`` class hourlies.

Reports gross cleared DEC / INC, net (DEC − INC) TWh, and on/off-peak splits.
Usage: ``python scripts/probes/_pjmnext6_virtual_clearing_probe.py [years...]``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import virtual_bids as vb  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "pjmnext5_sh_span" / "hourly"
LMP_DIR = REPO / "data" / "clean" / "lmp" / "PJM" / "DAM"
T = 8760


def actual_da_prices(year: int) -> pd.DataFrame:
    """Hourly actual DA prices on the model clock: columns t, sys, hubmean."""
    lmp = pd.read_parquet(
        LMP_DIR / f"lmp_{year}.parquet",
        columns=[
            "interval_start_local",
            "node",
            "lmp_usd_per_mwh",
            "energy_usd_per_mwh",
        ],
    )
    g = lmp.groupby("interval_start_local").agg(
        sys=("energy_usd_per_mwh", "mean"), hubmean=("lmp_usd_per_mwh", "mean")
    )
    g = g.reset_index()
    ts = pd.DatetimeIndex(g["interval_start_local"])
    g["day"] = ts.normalize()
    g["he"] = ts.hour + 1
    g = g.groupby(["day", "he"], as_index=False)[["sys", "hubmean"]].mean()
    hmap = vb._hour_index_map("PJM", year, T)
    out = hmap.merge(g, on=["day", "he"], how="left").set_index("t")
    # The model clock drops the duplicated DST fall-back (day, he); forward-fill
    # that one hour so every array is indexed 0..T-1.
    out = out.reindex(np.arange(T)).ffill()
    return out.reset_index().rename(columns={"index": "t"})


def clear_full(bids: pd.DataFrame, lam: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Gross cleared DEC and INC MW per hour at price ``lam`` (full submitted curve)."""
    p = bids["price"].to_numpy()
    t = bids["t"].to_numpy()
    lt = lam[t]
    ok = ~np.isnan(lt)
    dec = np.where(ok & (p >= lt), bids["dec"].to_numpy(), 0.0)
    inc = np.where(ok & (p <= lt), bids["inc"].to_numpy(), 0.0)
    return np.bincount(t, dec, minlength=T)[:T], np.bincount(t, inc, minlength=T)[:T]


def clear_rungs(rungs, lam: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Net-form rung clearing (the LP's representation) at price ``lam`` (T,)."""
    dec_mw, dec_p, inc_mw, inc_p = rungs
    lam = np.where(np.isnan(lam), np.nan, lam)[None, :]
    dec = np.where(dec_p > lam, dec_mw, 0.0).sum(axis=0)
    inc = np.where(inc_p < lam, inc_mw, 0.0).sum(axis=0)
    return dec, inc


def clear_rungs_zonal(rungs, sysdf: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Rung clearing at the MODEL's zonal duals, rungs split by zonal load share."""
    dec_mw, dec_p, inc_mw, inc_p = rungs
    price = sysdf.pivot(index="zone", columns="hour", values="price").to_numpy()[:, :T]
    dem = sysdf.pivot(index="zone", columns="hour", values="demand").to_numpy()[:, :T]
    share = dem / np.maximum(dem.sum(axis=0, keepdims=True), 1.0)
    dec = np.zeros(T)
    inc = np.zeros(T)
    for z in range(price.shape[0]):
        lam = price[z][None, :]
        dec += (np.where(dec_p > lam, dec_mw, 0.0) * share[z][None, :]).sum(axis=0)
        inc += (np.where(inc_p < lam, inc_mw, 0.0) * share[z][None, :]).sum(axis=0)
    return dec, inc


def run_year(year: int) -> dict:
    """All clearing variants for one year; TWh unless noted."""
    bids = vb._load_bids_frame("PJM", year, T)
    if bids is None:
        return {"year": year, "missing": True}
    rungs = vb._hourly_net_rungs(bids, T, vb.N_RUNGS)
    act = actual_da_prices(year)
    lam_sys = act["sys"].to_numpy()
    lam_hub = act["hubmean"].to_numpy()
    hours = pd.DatetimeIndex(act["day"] + pd.to_timedelta(act["he"] - 1, unit="h"))
    onpk = ((hours.dayofweek < 5) & (act["he"].between(8, 23))).to_numpy()

    out = {"year": year, "n_nan_price": int(np.isnan(lam_sys).sum())}
    gd = bids.groupby("t")[["dec", "inc"]].sum()
    out["submitted_dec_TWh"] = gd["dec"].sum() / 1e6
    out["submitted_inc_TWh"] = gd["inc"].sum() / 1e6
    d, i = clear_full(bids, lam_sys)
    out.update(
        full_dec=d.sum() / 1e6,
        full_inc=i.sum() / 1e6,
        full_net=(d - i).sum() / 1e6,
        full_net_on=(d - i)[onpk].sum() / 1e6,
        full_net_off=(d - i)[~onpk].sum() / 1e6,
    )
    d2, i2 = clear_full(bids, lam_hub)
    out.update(fullhub_net=(d2 - i2).sum() / 1e6)
    rd, ri = clear_rungs(rungs, lam_sys)
    out.update(
        rung_dec=rd.sum() / 1e6,
        rung_inc=ri.sum() / 1e6,
        rung_net=(rd - ri).sum() / 1e6,
        rung_net_on=(rd - ri)[onpk].sum() / 1e6,
        rung_net_off=(rd - ri)[~onpk].sum() / 1e6,
    )
    # Crossing price lambda0 (net curve zero) proxy: MW-weighted DEC-rung top vs INC-rung bottom.
    out["mean_actual_sys"] = float(np.nanmean(lam_sys))

    sysdf = pd.read_parquet(KEEPER / f"system_{year}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    md, mi = clear_rungs_zonal(rungs, sysdf)
    out.update(
        recl_model_dec=md.sum() / 1e6,
        recl_model_inc=mi.sum() / 1e6,
        recl_model_net=(md - mi).sum() / 1e6,
    )
    lw = (
        sysdf.assign(pd_=sysdf.price * sysdf.demand)
        .groupby("hour")[["pd_", "demand"]]
        .sum()
    )
    lam_model = (lw["pd_"] / lw["demand"]).to_numpy()[:T]
    out["mean_model_lw"] = float(lam_model.mean())
    out["model_minus_actual_on"] = float(np.nanmean((lam_model - lam_sys)[onpk]))
    out["model_minus_actual_off"] = float(np.nanmean((lam_model - lam_sys)[~onpk]))
    ch = pd.read_parquet(KEEPER / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    vdec = -ch.loc[ch.klass == "VIRTUAL_DEC", "mw"].sum() / 1e6
    vinc = ch.loc[ch.klass == "VIRTUAL_INC", "mw"].sum() / 1e6
    out.update(keeper_dec=abs(vdec), keeper_inc=vinc, keeper_net=abs(vdec) - vinc)
    return out


def main(argv: list[str]) -> None:
    """Run every requested year and print a table."""
    years = [int(a) for a in argv] or list(range(2019, 2026))
    rows = [run_year(y) for y in years]
    df = pd.DataFrame(rows).set_index("year")
    pd.set_option("display.width", 250, "display.max_columns", 50)
    print(df.round(2).T.to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
