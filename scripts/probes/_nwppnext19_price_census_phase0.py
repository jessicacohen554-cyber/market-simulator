"""NWPP-NEXT-19 phase 0 (zero LP): split measured NWPP price variance into gas-daily and interface parts.

Reads committed raw data only (WEIM hourly ELAP per BA, CAISO hourly RT/DA, Henry Hub daily,
CA composite citygate daily, Sumas weekly, Mid-C Peak daily ICE) plus keeper #20's per-year
shard legs for the price-taker section (``results/calibration/nwppnext16c_<Y>``, extracted with
``git archive <sha> results/calibration/nwppnext16c_<Y>``; full SHAs in
``docs/records/nwpp/FINDING-nwppnext19-price-census-phase0-2026-10-02.md``). Prints every table
of that FINDING. No LP is run.

Usage: python scripts/probes/_nwppnext19_price_census_phase0.py LEG_ROOT
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAW = Path("data/raw")
GAS = RAW / "gas-prices"
YEARS = (2023, 2024, 2025)
BAS = ("BPAT", "PACE", "IPCO")
# keeper #20's EIA-930 benchmark frame (restore: run_calibration_full.py --restore-shared-inputs <bundle>).
E930 = Path("results/calibration/_shared/NWPP/eia930-6da961d2d14a.parquet")
# keeper #20 zone -> the WEIM BA whose ELAP prices it (largest priced BA in the zone, README §2).
ZONE_BA = {"NWPP-NW": "BPAT", "NWPP-OR": "PGE", "NWPP-INLAND": "IPCO", "NWPP-EAST": "PACE", "NWPP-SNV": "NEVP"}


def _model_days(year: int) -> pd.DatetimeIndex:
    """Return the 365 calendar dates of the model clock (Feb 29 dropped)."""
    d = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    return d[~((d.month == 2) & (d.day == 29))]


def _daily_staircase(path: Path, col: str, year: int) -> pd.Series:
    """Return a dated series on the model days, last print carried forward (weekends / weekly)."""
    s = pd.read_csv(path, parse_dates=["date"]).set_index("date")[col].dropna().sort_index()
    days = _model_days(year)
    full = s.reindex(s.index.union(days)).ffill()
    return pd.Series(full.reindex(days).values, index=np.arange(365))


def _prices() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return WEIM hourly per BA and CAISO hourly RT/DA, model clock."""
    w = pd.read_parquet(RAW / "nwpp-weim/weim_hourly_by_ba.parquet")
    c = pd.read_parquet(RAW / "_validation-source/actual_lmp_hourly_CAISO.parquet")
    return w, c


def _r2(y: np.ndarray, x: np.ndarray) -> float:
    """Return the OLS R^2 of y on the columns of x (with intercept)."""
    x = np.column_stack([np.ones(len(y)), x])
    b, *_ = np.linalg.lstsq(x, y, rcond=None)
    e = y - x @ b
    return 1.0 - e.var() / y.var()


def between_day() -> None:
    """Section 1: within-month daily-mean variance, gas vs CAISO."""
    w, c = _prices()
    print("\n## 1. Between-day (daily means, demeaned within month): share of variance explained (R^2)")
    rows = []
    for y in YEARS:
        hh = _daily_staircase(GAS / "henry_hub_daily.csv", "price_usd_mmbtu", y)
        ca = _daily_staircase(GAS / "caiso_citygate_daily.csv", "ca_composite_usd_mmbtu", y)
        su = _daily_staircase(GAS / "sumas_weekly.csv", "sumas_usd_mmbtu", y)
        cc = c[c.year == y].set_index("hour").rt.reindex(range(8760))
        for ba in BAS:
            b = w[(w.year == y) & (w.baa == ba)].set_index("hour").lmp.reindex(range(8760))
            d = pd.DataFrame({"p": b.groupby(np.arange(8760) // 24).mean(),
                              "caiso": cc.groupby(np.arange(8760) // 24).mean(),
                              "hh": hh, "ca": ca, "su": su})
            d["m"] = _model_days(y).month
            d = d.dropna()
            dm = d.groupby("m")[["p", "caiso", "hh", "ca", "su"]].transform(lambda x: x - x.mean())
            g_hh = _r2(dm.p.values, dm[["hh"]].values)
            g_ca = _r2(dm.p.values, dm[["ca"]].values)
            g_su = _r2(dm.p.values, dm[["su"]].values)
            g_all = _r2(dm.p.values, dm[["hh", "ca"]].values)
            c_only = _r2(dm.p.values, dm[["caiso"]].values)
            full = _r2(dm.p.values, dm[["hh", "ca", "caiso"]].values)
            rows.append(dict(year=y, ba=ba, days=len(d), sd_within_month=dm.p.std(),
                             R2_HH=g_hh, R2_CAcitygate=g_ca, R2_Sumas_weekly=g_su,
                             R2_gas=g_all, R2_CAISO=c_only, R2_gas_CAISO=full,
                             CAISO_increment=full - g_all))
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def gas_shape_reach() -> None:
    """Section 1b: what the HH daily shape could put into a monthly-gas price (SD of HR x gas)."""
    from market_sim.data.fuel.hubs import gas_daily_shape_factors

    w, _ = _prices()
    print("\n## 1b. Between-day SD within month: measured vs what gas_daily_shape could add")
    rows = []
    for y in YEARS:
        f = gas_daily_shape_factors(y, 8760)
        hh = _daily_staircase(GAS / "henry_hub_daily.csv", "price_usd_mmbtu", y)
        days = _model_days(y)
        lvl = hh.groupby(days.month).transform("mean").values
        # 7.0 MMBtu/MWh: a CC-class marginal heat rate, the order of the keeper's marginal gas units.
        shape_sd = pd.Series(7.0 * lvl * (f[::24] - 1.0)).groupby(days.month).std().mean()
        for ba in BAS:
            b = w[(w.year == y) & (w.baa == ba)].set_index("hour").lmp.reindex(range(8760))
            d = pd.Series(b.groupby(np.arange(8760) // 24).mean().values)
            sd = d.groupby(days.month).std().mean()
            rows.append(dict(year=y, ba=ba, measured_between_day_sd=sd, hh_shape_x7_sd=shape_sd))
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def midc_vs_gas() -> None:
    """Section 1c: Mid-C Peak daily (bilateral, full years) vs gas, within-month demeaned."""
    m = pd.read_parquet(RAW / "nwpp-weim/midc_peak_daily.parquet")
    m = m[m.single_day].copy()
    m["date"] = pd.to_datetime(m.delivery_start)
    print("\n## 1c. Mid-C Peak daily (ICE, single-day delivery) vs gas, within-month R^2")
    for y in YEARS:
        days = _model_days(y)
        hh = _daily_staircase(GAS / "henry_hub_daily.csv", "price_usd_mmbtu", y)
        ca = _daily_staircase(GAS / "caiso_citygate_daily.csv", "ca_composite_usd_mmbtu", y)
        p = m[m.date.dt.year == y].groupby("date").wavg.mean().reindex(days).values
        d = pd.DataFrame({"p": p, "hh": hh.values, "ca": ca.values, "m": days.month}).dropna()
        dm = d.groupby("m")[["p", "hh", "ca"]].transform(lambda x: x - x.mean())
        print(f"{y}: days {len(d)}, R2 HH {_r2(dm.p.values, dm[['hh']].values):.2f}, "
              f"R2 CA citygate {_r2(dm.p.values, dm[['ca']].values):.2f}, "
              f"R2 both {_r2(dm.p.values, dm[['hh', 'ca']].values):.2f}")


def within_day() -> None:
    """Section 2: within-day shape, CAISO co-movement, clock check by lag."""
    w, c = _prices()
    print("\n## 2. Within-day (hourly, demeaned per day): r with CAISO RT at clock shifts, and mean-shape r")
    rows = []
    for y in YEARS:
        cc = c[c.year == y].set_index("hour")
        for ba in BAS + ("PGE", "PSEI"):
            b = w[(w.year == y) & (w.baa == ba)].set_index("hour").lmp.reindex(range(8760))
            r = {}
            for k in (-2, -1, 0, 1, 2):
                x = pd.DataFrame({"b": b.values, "c": cc.rt.reindex(range(8760)).shift(k).values})
                x["day"] = np.arange(8760) // 24
                x = x.dropna()
                dm = x.groupby("day")[["b", "c"]].transform(lambda v: v - v.mean())
                r[k] = dm.b.corr(dm.c)
            x = pd.DataFrame({"b": b.values, "c": cc.rt.reindex(range(8760)).values,
                              "hod": np.arange(8760) % 24,
                              "m": (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month})
            x = x.dropna()
            prof = x.groupby(["m", "hod"])[["b", "c"]].mean()
            prof = prof - prof.groupby("m").transform("mean")
            x["day"] = x.index // 24
            sd_b = x.groupby("day").b.std().mean()
            sd_c = x.groupby("day").c.std().mean()
            rows.append(dict(year=y, ba=ba, **{f"r_lag{k:+d}": v for k, v in r.items()},
                             r_month_hod_profile=prof.b.corr(prof.c),
                             wd_sd_ba=sd_b, wd_sd_caiso=sd_c))
    print(pd.DataFrame(rows).round(2).to_string(index=False))


def _leg(root: Path, y: int) -> Path:
    """Return keeper #20's leg directory for one year."""
    return root / f"results/calibration/nwppnext16c_{y}"


def price_taker(root: Path) -> None:
    """Section 3: class energies if every dispatchable unit faced the measured zonal price."""
    w, _ = _prices()
    print("\n## 3. Price-taker bound: class TWh at keeper offers vs measured WEIM price (Jun-Dec 2023, 2024, 2025)")
    for y in YEARS:
        u = pd.read_parquet(_leg(root, y) / f"hourly/unit_hourly_{y}.parquet",
                            columns=["unit_id", "plant_code", "fuel", "zone", "hour", "mw", "cap_mw", "mc"])
        if y == 2023:
            u = u[u.hour >= 151 * 24]
        s = pd.read_parquet(_leg(root, y) / "system.parquet", columns=["zone", "hour", "price"])
        u = u.merge(s, on=["zone", "hour"], how="left")
        meas = []
        for z, ba in ZONE_BA.items():
            m = w[(w.year == y) & (w.baa == ba)][["hour", "lmp"]].assign(zone=z)
            meas.append(m)
        u = u.merge(pd.concat(meas), on=["zone", "hour"], how="left")
        u = u[u.lmp.notna()]
        disp = u[u.fuel.isin(["coal", "gas_cc", "gas_ct", "gas_st", "oil"])].copy()
        # Floor: the unit's own minimum dispatch in the month (must-run / committed tranches); the price-taker
        # runs every unit at cap_mw when the measured price clears its offer, at that floor otherwise.
        disp["m"] = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(disp.hour, "h")).dt.month
        disp["floor"] = disp.groupby(["unit_id", "m"]).mw.transform("min")
        disp["pt"] = np.where(disp.lmp > disp.mc, disp.cap_mw, disp.floor)
        disp["pt_modelprice"] = np.where(disp.price > disp.mc, disp.cap_mw, disp.floor)
        t = disp.groupby("fuel")[["mw", "pt_modelprice", "pt"]].sum() / 1e6
        t.columns = ["model_TWh", "price_taker_at_model_price", "price_taker_at_WEIM"]
        print(f"\n{y}" + (" (Jun-Dec)" if y == 2023 else ""))
        print(t.round(2).to_string())
        b = disp[disp.plant_code == 8066].groupby("m")[["mw", "pt"]].sum() / 1e3
        if y == 2023:
            print("Bridger 8066 GWh model / at WEIM: " + ", ".join(
                f"{m}:{r.mw:.0f}/{r.pt:.0f}" for m, r in b.iterrows()))
        # C4 coal shape on the scorer's own EIA-930 frame (the keeper's restored shared input), same hours.
        e = pd.read_parquet(E930)
        a = e[(e.year == y) & (e.series == "coal")].set_index("hour").mw
        coal = disp[disp.fuel == "coal"].groupby("hour")[["mw", "pt_modelprice", "pt"]].sum()
        coal = coal.join(a.rename("eia"), how="inner")
        fit = {k: (coal[k].corr(coal.eia), np.sqrt(((coal[k] - coal.eia) ** 2).mean()) / coal.eia.mean())
               for k in ("mw", "pt_modelprice", "pt")}
        print("C4 coal r / NRMSE on these hours: " + ", ".join(
            f"{n} {fit[k][0]:.3f} / {fit[k][1]:.3f}" for k, n in
            (("mw", "model"), ("pt_modelprice", "price-taker@model"), ("pt", "price-taker@WEIM"))))


def seam_shape() -> None:
    """Section 6: does the registered NWPP seam reference price carry the measured shape?"""
    import dataclasses

    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import neighbor_reference_price

    w, c = _prices()

    def _wd(a: np.ndarray, b: np.ndarray) -> float:
        x = pd.DataFrame({"a": a, "b": b, "d": np.arange(8760) // 24}).dropna()
        dm = x.groupby("d")[["a", "b"]].transform(lambda v: v - v.mean())
        return dm.a.corr(dm.b)

    def _bd(a: np.ndarray, b: np.ndarray, y: int) -> float:
        x = pd.DataFrame({"a": a, "b": b, "d": np.arange(8760) // 24,
                          "m": (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month}).dropna()
        d = x.groupby(["m", "d"])[["a", "b"]].mean()
        d = d - d.groupby("m").transform("mean")
        return d.a.corr(d.b)

    def _ba(y: int, ba: str) -> np.ndarray:
        return w[(w.year == y) & (w.baa == ba)].set_index("hour").lmp.reindex(range(8760)).values

    seams = {n.name: n for n in INTERFACE_NEIGHBORS["NWPP"]}
    print("\n## 6a. CAISO seam reference price (registered gross vs net-load shape) against measured prices")
    rows = []
    for y in YEARS:
        rt = c[c.year == y].set_index("hour").rt.reindex(range(8760)).values
        for kind in ("gross", "net"):
            p = neighbor_reference_price(dataclasses.replace(seams["CAISO"], load_shape_kind=kind), y, 8760)[0]
            rows.append(dict(year=y, kind=kind, wd_r_CAISO_RT=_wd(p, rt), wd_r_PACE=_wd(p, _ba(y, "PACE")),
                             wd_r_BPAT=_wd(p, _ba(y, "BPAT")), bd_r_PACE=_bd(p, _ba(y, "PACE"), y),
                             bd_r_BPAT=_bd(p, _ba(y, "BPAT"), y), mean=p.mean(), sd=p.std()))
    print(pd.DataFrame(rows).round(2).to_string(index=False))
    print("\n## 6b. Seam reference price annual mean $/MWh (registered form) vs measured BA mean")
    for y in (2019, 2020, 2021, 2022) + YEARS:
        ref = {k: neighbor_reference_price(n, y, 8760)[0].mean() for k, n in seams.items()}
        meas = {ba: np.nanmean(_ba(y, ba)) for ba in BAS} if y in YEARS else {}
        print(f"{y}: " + ", ".join(f"{k} {v:.1f}" for k, v in ref.items())
              + ("" if not meas else " | measured " + ", ".join(f"{k} {v:.1f}" for k, v in meas.items())))


def main() -> None:
    """Run every section."""
    between_day()
    gas_shape_reach()
    midc_vs_gas()
    within_day()
    seam_shape()
    if len(sys.argv) > 1:
        price_taker(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
