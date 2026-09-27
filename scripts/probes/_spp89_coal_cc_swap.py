"""SPP-89 stage 2 (ZERO LP): why does the keeper swap CC_REGULAR for coal in 2021-22 at every price?

Reads the stage-1 stacks (``_spp89_stack_dump.py``: the keeper ``spp86_arm_span`` fleet rebuilt
with no LP) and, per year, per hour, compares three things for CC_REGULAR and COAL (PRB+lignite):

* ``A``  actual generation: CAMPD CEMS gross MW of the model's own plants (gross basis);
* ``M``  keeper P1 generation (committed ``hourly/class_hourly``, net basis);
* ``I``  the keeper's OFFERED MW at or below the ACTUAL system RT LMP in that hour
         (``cap`` over rows with ``mc_base <= lmp_actual``) - what a merit clear of the keeper's
         own offers would load if the price were the real one.

``I - A`` is the offer-consistency test. For a class whose offers are right, ``I >= A`` in
hours the real price clears it (the real fleet cannot run more than is economic at the real
price unless it is self-scheduled or held on by commitment). ``I << A`` means the keeper's offers
are too HIGH for the dispatch SPP actually had (fuel input / hedging / commitment); ``I >> A``
means the class is offered too LOW (withholding / markup - SPP-41/44's coal object).

Also: monthly capacity-weighted offer fuel and mc per class against Henry Hub (daily and monthly)
and the actual LMP, i.e. the coal-CC spread by month (candidates 1 and 3), and available CC MW
vs CEMS CC max-online MW (candidate 2).

Usage: ``python scripts/probes/_spp89_coal_cc_swap.py --stack-dir <dir> --out <json>``
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes._spp72_demand_tightness import CST_OFFSET_H, model_clock_index  # noqa: E402
from scripts.probes._spp73_commitment_reach import MST_STATES, SPP_STATES  # noqa: E402

BUNDLE = REPO / "results/calibration/spp86_arm_span"
YEARS = range(2019, 2026)
BUCKETS = [(-np.inf, 15.0), (15.0, 30.0), (30.0, 60.0), (60.0, np.inf)]
GROUPS = {"CC": ("CC_REGULAR",), "COAL": ("COAL_PRB", "COAL_LIGNITE"), "ST": ("ST_GAS",)}


def cems(y: int, plant_group: dict[int, str]) -> dict[str, np.ndarray]:
    """Actual CEMS gross MW per group on the model clock, for the model's own plants."""
    clock = model_clock_index(y)
    slot = pd.Series(np.arange(8760), index=(clock - pd.Timedelta(hours=CST_OFFSET_H)).tz_localize(None))
    out = {g: np.zeros(8760) for g in GROUPS}
    for st in SPP_STATES:
        p = RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["facilityId", "date", "hour", "grossLoad", "primaryFuelInfo", "unitType"])
        d["fid"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["fid"].isin(plant_group)]
        if d.empty:
            continue
        ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
        if st in MST_STATES:
            ts = ts + pd.Timedelta(hours=1)
        s = slot.reindex(ts.to_numpy()).to_numpy()
        ok = np.isfinite(s)
        d, s = d[ok], s[ok].astype(int)
        fuel = d["primaryFuelInfo"].astype(str).str.lower()
        ut = d["unitType"].astype(str).str.lower()
        grp = d["fid"].map(plant_group).to_numpy()
        coal = fuel.str.contains("coal").to_numpy()
        gas = fuel.str.contains("gas").to_numpy()
        cc = gas & ((grp == "CC") | ut.str.contains("combined cycle").to_numpy())
        stg = gas & ~cc & (grp == "ST")
        mw = d["grossLoad"].fillna(0).to_numpy()
        for g, m in (("COAL", coal & (grp == "COAL")), ("CC", cc), ("ST", stg)):
            np.add.at(out[g], s[m], mw[m])
    return out


def cw_median(v: np.ndarray, w: np.ndarray) -> float:
    """Capacity-weighted median."""
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, c[-1] / 2.0)]) if c[-1] > 0 else float("nan")


def year_block(y: int, sd: Path, hh_d: pd.Series, hh_m: pd.Series) -> dict:
    """All legs for one year."""
    z = np.load(sd / f"stack_{y}.npz", allow_pickle=False)
    mc, cap, fuel, kl, codes, pmax = z["mc"], z["cap"], z["fuel"], z["klass"], z["codes"], z["pmax"]
    T = mc.shape[1]
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    lmp = lmp[lmp.year == y].set_index("hour")["rt"].reindex(range(T)).to_numpy(float)
    sysf = pd.read_parquet(BUNDLE / "hourly" / f"system_{y}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    mp = ((sysf["price"] * sysf["demand"]).groupby(sysf["hour"]).sum()
          / sysf.groupby("hour")["demand"].sum()).reindex(range(T)).to_numpy(float)
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[ch["pass"] == "P1"].pivot_table(index="hour", columns="klass", values="mw",
                                             aggfunc="sum", observed=True).reindex(range(T)).fillna(0)
    # plant -> dominant model group (by pmax)
    pg = {}
    df = pd.DataFrame({"c": codes, "k": kl, "p": pmax})
    for c, g in df.groupby("c"):
        s = g.groupby("k")["p"].sum()
        k = s.idxmax()
        pg[int(c)] = next((G for G, ks in GROUPS.items() if k in ks), "OTHER")
    A = cems(y, pg)
    month = pd.date_range(f"{y}-01-01", periods=T, freq="h").month.to_numpy()
    day = pd.date_range(f"{y}-01-01", periods=T, freq="h").normalize()
    hhh = hh_d.reindex(day, method="ffill").to_numpy(float)
    row: dict = {"year": y, "legs": {}, "monthly": {}}
    for G, ks in GROUPS.items():
        r = np.isin(kl, ks)
        M = ch[[k for k in ks if k in ch.columns]].sum(axis=1).to_numpy()
        I = np.where(mc[r] <= lmp[None, :], cap[r], 0.0).sum(axis=0)
        Im = np.where(mc[r] <= mp[None, :], cap[r], 0.0).sum(axis=0)
        av = cap[r].sum(axis=0)
        leg = {"avail_mean_mw": float(av.mean()), "A_twh": A[G].sum() / 1e6, "M_twh": M.sum() / 1e6,
               "A_max_mw": float(A[G].max()), "buckets": {}}
        for lo, hi in BUCKETS:
            m = (lmp >= lo) & (lmp < hi)
            leg["buckets"][f"{lo:g}..{hi:g}"] = {
                "hours": int(m.sum()),
                "A_twh": A[G][m].sum() / 1e6, "M_twh": M[m].sum() / 1e6,
                "I_at_actual_twh": np.minimum(I, av)[m].sum() / 1e6,
                "I_at_model_twh": Im[m].sum() / 1e6,
                "avail_twh": av[m].sum() / 1e6,
                "actual_lmp_med": float(np.median(lmp[m])) if m.any() else None,
                "model_price_med": float(np.median(mp[m])) if m.any() else None,
            }
        row["legs"][G] = leg
        mm = {}
        for mo in range(1, 13):
            s = month == mo
            w = pmax[r]
            mm[mo] = {
                "fuel_cw_med": cw_median(fuel[r][:, s].mean(axis=1), w),
                "mc_cw_med": cw_median(mc[r][:, s].mean(axis=1), w),
                "A_gwh": A[G][s].sum() / 1e3, "M_gwh": M[s].sum() / 1e3,
                "I_at_actual_gwh": I[s].sum() / 1e3,
            }
        row["monthly"][G] = mm
    row["monthly"]["price"] = {
        mo: {"lmp_mean": float(np.nanmean(lmp[month == mo])), "model_mean": float(np.nanmean(mp[month == mo])),
             "hh_daily_mean": float(np.nanmean(hhh[month == mo])),
             "hh_monthly": float(hh_m.get(pd.Timestamp(f"{y}-{mo:02d}-01"), np.nan))}
        for mo in range(1, 13)
    }
    return row


def main() -> int:
    """Run every year and print the tables."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    hd = pd.read_csv(RAW_DATA_DIR / "gas-prices/henry_hub_daily.csv", parse_dates=["date"]).set_index("date")
    hh_d = hd["price_usd_mmbtu"].sort_index()
    hh_m = hh_d.resample("MS").mean()
    out = {}
    for y in YEARS:
        r = year_block(y, a.stack_dir, hh_d, hh_m)
        out[y] = r
        print(f"\n=== {y}")
        for G in GROUPS:
            L = r["legs"][G]
            print(f" {G:5s} avail {L['avail_mean_mw']:7.0f}MW  A {L['A_twh']:6.2f}  M {L['M_twh']:6.2f}  Amax {L['A_max_mw']:6.0f}")
            for b, v in L["buckets"].items():
                print(f"   {b:>9s} h{v['hours']:5d} A {v['A_twh']:6.2f} M {v['M_twh']:6.2f} I@act {v['I_at_actual_twh']:6.2f}"
                      f" I@mod {v['I_at_model_twh']:6.2f} av {v['avail_twh']:6.2f} lmp~{v['actual_lmp_med']:.1f} mod~{v['model_price_med']:.1f}")
    args_out = a.out
    args_out.parent.mkdir(parents=True, exist_ok=True)
    args_out.write_text(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def sensitivity(sd: Path, deltas=(0.0, -0.5, -1.0)) -> dict:
    """Merit re-dispatch (SPP-76 instrument) of the keeper's P1 served thermal energy with every
    gas row's offer fuel shifted by ``delta`` $/MMBtu (mc += delta x heat_rate). A SENSITIVITY for
    sizing only, never a mechanism: the class TWh per $/MMBtu of gas-offer level, per year."""
    from scripts.probes._spp76_crossover_hr import merit_dispatch

    res = {}
    for y in YEARS:
        z = np.load(sd / f"stack_{y}.npz", allow_pickle=False)
        mc, cap, kl, hr = z["mc"].astype(float), z["cap"].astype(float), z["klass"], z["hr"]
        gas = np.array([k.startswith(("CC_", "CT_", "ST_")) for k in kl])
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[(ch["pass"] == "P1") & ch["klass"].astype(str).str.startswith(("COAL", "CC_", "CT_", "ST_"))]
        served = ch.groupby("hour")["mw"].sum().reindex(range(mc.shape[1]), fill_value=0.0).to_numpy()
        base = None
        res[y] = {}
        for d in deltas:
            m2 = mc + np.where(gas, d, 0.0)[:, None] * hr[:, None]
            e = merit_dispatch(m2, cap, served)
            tw = {G: float(e[np.isin(kl, ks)].sum() / 1e6) for G, ks in GROUPS.items()}
            if base is None:
                base = tw
            res[y][d] = {G: tw[G] - base[G] for G in tw} | {"proxy_" + G: tw[G] for G in tw}
        print(y, {d: {G: round(v[G], 2) for G in GROUPS} for d, v in res[y].items()},
              "proxy CC/COAL", round(base["CC"], 2), round(base["COAL"], 2))
    return res
