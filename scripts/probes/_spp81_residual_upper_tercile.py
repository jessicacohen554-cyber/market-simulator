"""SPP-81 (zero LP): what carries SPP's residual upper-tercile cost object?

SPP-80 (``docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md``) left, after
congestion, scarcity and delivered-gas basis, a residual in the real SPP hub's RT upper
tercile (p67-p99, February excluded): MEC ex-scarcity divided by the ANNUAL delivered
KS/OK/NE gas price sits +3.19 / +3.43 heat-rate units above 2019-21 in 2023 / 2024. This
probe measures three candidate carriers on SPP-80's exact hour set:

  1. **Marginal-unit heat-rate mix** — CAMPD hourly heat input / gross load for SWPP-BA
     gas units (EIA-860 ``Balancing Authority Code == SWPP``; SPP-73's unit classifier),
     including the units in their dispatchable range (the MMU's marginal-unit criterion:
     not at economic minimum or maximum). The MMU's own RT marginal-technology frequencies
     are transcribed separately into ``som-competitive-conduct`` and read in the FINDING.
  2. **Intra-year / intra-month gas cost** — the residual recomputed with the MONTHLY
     delivered price each hour actually faced, and then with that monthly price shaped by
     the daily/monthly Henry Hub ratio (the only free daily series; no free daily
     Panhandle / OGT / Southern Star print exists — FINDING §4).
  3. **Ramp-product dispatch effect** — RTBM cleared ramp-up MW
     (``spp_rtbm_or_cleared_hourly.parquet``, ``scripts/data/fetch_spp_or_cleared.py``)
     against MEC at matched net load, and the residual split at 2022-03-01 / 2023-07-06.

Solves nothing and writes nothing. Record:
``docs/handoffs/FINDING-spp-81-residual-upper-tercile-2026-09-25.md``.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp72_demand_tightness import CST_OFFSET_H, model_clock_index  # noqa: E402
from scripts.probes._spp73_commitment_reach import (  # noqa: E402
    MST_STATES,
    SPP_STATES,
    classify,
    swpp_gas_units,
)
from scripts.probes._spp80_upper_tercile_premium import (  # noqa: E402
    BASE_YEARS,
    BUNDLE,
    YEARS,
    genmix_hourly,
    reserve_hourly,
)

# A unit is in its dispatchable (price-setting-eligible) range when its hourly gross load
# is strictly between its economic minimum and maximum (SOM "Generation on the margin"
# criterion, e.g. 2023 SOM PDF p.57). CAMPD carries neither, so both are proxied from the
# unit's own year of operation: max = its p99 hourly gross load; min = the p10 of its
# running hours. The FLEX_BAND pads both by 5 % of max so a unit sitting on either limit
# is excluded; the result is reported beside a no-band all-online comparison.
FLEX_PAD = 0.05
HR_VALID = (5.0, 25.0)  # MMBtu/MWh: drops start-up / metering unit-hours outside physics
MIN_MW = 5.0  # unit-hours below this gross MW are start-up tails, not dispatch


def frame(y: int, lmp: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    """SPP-80's hourly frame without the binding-constraint join (unused here)."""
    s = pd.read_parquet(f"{BUNDLE}/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    d = s.groupby("hour").demand.sum()
    m = (s.price * s.demand).groupby(s.hour).sum() / d
    f = pd.DataFrame({"d": d, "m": m})
    f["rt"] = lmp[lmp.year == y].set_index("hour").rt.reindex(f.index)
    c = comp[(comp.year == y) & (comp.market == "rt")].groupby("hour")[["mec"]].mean()
    f = f.join(c).join(reserve_hourly(y)).join(genmix_hourly(y))
    f["mon"] = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(f.index, unit="h")).month
    # Calendar date on the model clock (Feb 29 dropped), for the gas-day join.
    clock = model_clock_index(y) - pd.Timedelta(hours=CST_OFFSET_H)
    f["date"] = pd.Series(clock.tz_localize(None).normalize(), index=range(8760)).reindex(f.index)
    return f.dropna(subset=["rt", "m"])


def upper(f: pd.DataFrame) -> pd.DataFrame:
    """SPP-80's upper tercile (p67 <= RT < p99, ex-Feb) with its scarcity flag."""
    f = f[f.mon != 2]
    q67, q99 = f.rt.quantile([0.67, 0.99])
    u = f[(f.rt >= q67) & (f.rt < q99)].copy()
    # ``scar`` is reserve_hourly's INTERVAL-level flag (any 5-min interval in the hour
    # with Spin/Supp MCP > $100 or Reg-Up MCP > $500), exactly SPP-80's.
    u["scar"] = u.scar.fillna(False).astype(bool)
    return u


def delivered_gas_monthly(year: int) -> pd.Series:
    """EIA-923 delivered gas to KS/OK/NE plants by month, quantity-weighted ($/MMBtu)."""
    g = pd.read_parquet(RAW_DATA_DIR / "_processed-legacy/eia923_monthly_fuel_costs.parquet")
    g = g[
        (g.fuel_group == "Natural Gas") & g.state.isin(["KS", "OK", "NE"]) & (g.year == year)
    ].dropna(subset=["price_per_mmbtu"])
    w = g.price_per_mmbtu * g.quantity
    return w.groupby(g.month).sum() / g.quantity.groupby(g.month).sum()


def hh_daily_ratio() -> pd.Series:
    """Flow-date Henry Hub daily price / its calendar-month mean.

    ``henry_hub_daily.csv`` is dated by TRADE date; a day-ahead print prices next-day
    flow, so each flow date takes the last print strictly before it (weekend/holiday
    flow dates take Friday's package, as the MISO daily-citygate overlay does).
    """
    h = pd.read_csv(RAW_DATA_DIR / "gas-prices/henry_hub_daily.csv", parse_dates=["date"])
    h = h.set_index("date").price_usd_mmbtu.sort_index()
    flow = pd.date_range("2018-12-01", "2026-01-31", freq="D")
    p = h.reindex(h.index.union(flow)).ffill().shift(1).reindex(flow)
    mm = p.groupby([p.index.year, p.index.month]).transform("mean")
    return p / mm


def campd_gas(y: int, ids: set[int], pm: dict[int, set[str]]) -> tuple[pd.Series, np.ndarray, np.ndarray]:
    """Class per SWPP gas unit and (n_units, 8760) gross MW and heat input on the model clock."""
    clock = model_clock_index(y)
    slot = pd.Series(np.arange(8760), index=(clock - pd.Timedelta(hours=CST_OFFSET_H)).tz_localize(None))
    cols = ["stateCode", "facilityId", "unitId", "date", "hour", "grossLoad", "heatInput", "primaryFuelInfo", "unitType"]
    frames = []
    for st in SPP_STATES:
        p = RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"
        if p.exists():
            d = pd.read_parquet(p, columns=cols)
            d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
            frames.append(d[d.facilityId.isin(ids)])
    d = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    ts = ts + pd.to_timedelta(d["stateCode"].isin(MST_STATES).astype(int), unit="h")
    d["slot"] = slot.reindex(ts.to_numpy()).to_numpy()
    d = d[np.isfinite(d.slot)]
    d["u"] = d.facilityId.astype(int).astype(str) + "|" + d.unitId.astype(str)
    meta = d.groupby("u").agg(fid=("facilityId", "first"), ut=("unitType", "first"), fu=("primaryFuelInfo", "first"))
    meta["cls"] = [classify(r.ut, r.fu, pm.get(int(r.fid), set())) for r in meta.itertuples()]
    meta = meta[meta.cls.notna()]
    d = d[d.u.isin(meta.index)]
    r, c = meta.index.get_indexer(d.u), d.slot.astype(int).to_numpy()
    mw, hi = np.zeros((len(meta), 8760)), np.zeros((len(meta), 8760))
    np.add.at(mw, (r, c), d.grossLoad.fillna(0).to_numpy())
    np.add.at(hi, (r, c), d.heatInput.fillna(0).to_numpy())
    return meta.cls, mw, hi


def campd_metrics(cls: pd.Series, mw: np.ndarray, hi: np.ndarray, hours: np.ndarray) -> dict:
    """Upper-tercile gas-fleet heat-rate and marginal-range mix from CAMPD unit-hours."""
    run = mw >= MIN_MW
    runs = np.where(run, mw, np.nan)
    umax = np.nanpercentile(np.where(run, mw, np.nan), 99, axis=1)
    umin = np.nanpercentile(runs, 10, axis=1)
    hr = np.divide(hi, mw, out=np.full_like(mw, np.nan), where=run)
    ok = run & (hr >= HR_VALID[0]) & (hr <= HR_VALID[1])
    lo = (umin + FLEX_PAD * umax)[:, None]
    hi_lim = ((1 - FLEX_PAD) * umax)[:, None]
    flex = ok & (mw > lo) & (mw < hi_lim)
    H = np.zeros(8760, bool)
    H[hours] = True
    out = {}
    tot_mw = mw[:, H].sum()
    for k in ("CC", "CT", "ST_GAS"):
        m = (cls == k).to_numpy()
        out[f"share_{k}"] = mw[m][:, H].sum() / tot_mw
        sel = ok[m][:, H]
        out[f"hr_{k}"] = hi[m][:, H][sel].sum() / mw[m][:, H][sel].sum()
        out[f"flexshare_{k}"] = mw[m][:, H][flex[m][:, H]].sum()
    fl = out["flexshare_CC"] + out["flexshare_CT"] + out["flexshare_ST_GAS"]
    for k in ("CC", "CT", "ST_GAS"):
        out[f"flexshare_{k}"] /= fl
    out["hr_all"] = hi[:, H][ok[:, H]].sum() / mw[:, H][ok[:, H]].sum()
    out["hr_flex"] = hi[:, H][flex[:, H]].sum() / mw[:, H][flex[:, H]].sum()
    # Top of the running gas stack: per hour, the MW-weighted p90 heat rate over flex units.
    p90 = []
    for t in hours:
        f = flex[:, t]
        if f.sum() < 3:
            continue
        h, w = hr[f, t], mw[f, t]
        o = np.argsort(h)
        cw = np.cumsum(w[o]) / w.sum()
        p90.append(h[o][np.searchsorted(cw, 0.9)])
    out["hr_flex_p90"] = float(np.mean(p90))
    out["gas_gw"] = mw[:, H].sum(0).mean() / 1e3
    out["ct_online_gw"] = np.where(run, mw, 0)[(cls == "CT").to_numpy()][:, H].sum(0).mean() / 1e3
    out["n_units"] = len(cls)
    return out


def ramp_effect(frames: dict, u_sets: dict, gas_m: dict) -> pd.DataFrame:
    """Ramp-up cleared MW vs MEC/delivered-gas at matched net load, per year 2022+."""
    orc = pd.read_parquet(RAW_DATA_DIR / "_validation-source/spp_rtbm_or_cleared_hourly.parquet")
    rows = []
    for y, f in frames.items():
        o = orc[orc.year == y].set_index("hour")
        g = f[(f.mon != 2) & f.mec.notna()].copy()
        g["hrd"] = g.mec / g.mon.map(gas_m[y])
        g = g.join(o[[c for c in ("rampup", "uncup", "regup", "spin", "supp") if c in o]])
        u = g.loc[g.index.intersection(u_sets[y].index)]
        row = {
            "year": y,
            "rampup_clr_all": g.get("rampup", pd.Series(dtype=float)).mean(),
            "rampup_clr_up": u.get("rampup", pd.Series(dtype=float)).mean(),
            "uncup_clr_up": u.uncup.mean() if "uncup" in u else np.nan,
            "regup_clr_up": u.regup.mean() if "regup" in u else np.nan,
            "spin_clr_up": u.spin.mean() if "spin" in u else np.nan,
            "supp_clr_up": u.supp.mean() if "supp" in u else np.nan,
        }
        if "rampup" in g and g.rampup.notna().sum() > 1000 and g.rampup.max() > 0:
            # Within 2-GW net-load bins: OLS slope of MEC/delivered gas on cleared ramp-up MW.
            gg = g.dropna(subset=["rampup", "net", "hrd"])
            gg = gg[gg.rampup > 0]
            b = pd.cut(gg.net, np.arange(0, 60e3, 2e3))
            x = gg.rampup - gg.groupby(b, observed=True).rampup.transform("mean")
            z = gg.hrd - gg.groupby(b, observed=True).hrd.transform("mean")
            slope = (x * z).sum() / (x * x).sum()
            row["slope_hr_per_100mw"] = 100 * slope
            row["implied_up_hr"] = slope * u.rampup.mean()
            row["corr_within_band"] = np.corrcoef(x, z)[0, 1]
        rows.append(row)
    return pd.DataFrame(rows).set_index("year")


def residual_by_window(frames: dict, gas_m: dict, u_sets: dict) -> pd.DataFrame:
    """Residual (MEC ex-scarcity / monthly delivered gas) in date windows, season-matched.

    Each window's upper-tercile hours are compared with the SAME calendar months of
    2019-21's upper tercile, so a window's value is not a seasonal artefact.
    """
    def hr(y, months, lo=None, hi=None):
        f = u_sets[y]
        f = f[~f.scar & f.mon.isin(months)]
        if lo is not None:
            f = f[f.date >= pd.Timestamp(lo)]
        if hi is not None:
            f = f[f.date < pd.Timestamp(hi)]
        return (f.mec / f.mon.map(gas_m[y])).mean(), len(f)

    wins = [
        (2021, "2021 all", range(1, 13), None, None),
        (2022, "2022 Jan (pre-ramp)", [1], None, "2022-03-01"),
        (2022, "2022 Mar-Dec (ramp)", range(3, 13), "2022-03-01", None),
        (2023, "2023 Jan-Jul 5 (pre-uncertainty)", range(1, 8), None, "2023-07-06"),
        (2023, "2023 Jul 6-Dec (uncertainty)", range(7, 13), "2023-07-06", None),
        (2024, "2024 Jan-Sep", range(1, 10), None, "2024-10-01"),
        (2024, "2024 Oct-Dec (unc. enhancement)", range(10, 13), "2024-10-01", None),
        (2025, "2025 all", range(1, 13), None, None),
    ]
    rows = []
    for y, name, months, lo, hi in wins:
        v, n = hr(y, list(months), lo, hi)
        base = np.mean([hr(b, list(months))[0] for b in BASE_YEARS])
        rows.append({"window": name, "n_h": n, "hr_deliv": v, "base_same_months": base, "d": v - base})
    return pd.DataFrame(rows).set_index("window")


def residual_by_month(gas_m: dict, u_sets: dict) -> pd.DataFrame:
    """Month-by-month residual (MEC ex-scarcity / monthly delivered gas) minus the 2019-21 same-month mean."""
    def by_month(y):
        f = u_sets[y][~u_sets[y].scar]
        return (f.mec / f.mon.map(gas_m[y])).groupby(f.mon).mean()

    base = pd.concat([by_month(b) for b in BASE_YEARS], axis=1).mean(axis=1)
    return pd.DataFrame({y: by_month(y) - base for y in YEARS if y >= 2021}).round(2)


def som_rows() -> pd.DataFrame:
    """SPP MMU SOM rows SPP-81 transcribed: RT marginal shares, implied HR, hub gas."""
    s = pd.read_csv(RAW_DATA_DIR / "som-competitive-conduct/som_competitive_conduct.csv")
    s = s[s.iso == "SPP"]
    mar = s[s.metric == "rt_marginal_interval_share_digitized"].pivot(index="year", columns="fleet_segment", values="value")
    mar["sc_of_gas"] = mar.gas_simple_cycle / (mar.gas_simple_cycle + mar.gas_combined_cycle)
    hub = s[s.metric == "gas_hub_price_annual_avg"].pivot(index="year", columns="fleet_segment", values="value")
    ihr = s[s.metric == "rt_implied_heat_rate"].set_index("year").value.rename("mmu_implied_hr")
    return mar.join(hub).join(ihr)


def main() -> None:
    """Print the three legs' per-year tables."""
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    comp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet")
    hhm = pd.read_csv(RAW_DATA_DIR / "gas-prices/henry_hub_monthly.csv")
    hh = {y: hhm[hhm.year == y].price_usd_mmbtu.mean() for y in YEARS}
    ratio = hh_daily_ratio()
    frames = {y: frame(y, lmp, comp) for y in YEARS}
    ids, pm = swpp_gas_units()
    gas_m = {y: delivered_gas_monthly(y) for y in YEARS}
    rows, u_sets = [], {}
    for y in YEARS:
        u = upper(frames[y])
        u_sets[y] = u
        ns = u[~u.scar]
        # SPP-80's annual denominator: quantity-weighted ex-Feb; reconstructed from the monthly
        # table by re-weighting with monthly quantity.
        g = pd.read_parquet(RAW_DATA_DIR / "_processed-legacy/eia923_monthly_fuel_costs.parquet")
        g = g[(g.fuel_group == "Natural Gas") & g.state.isin(["KS", "OK", "NE"]) & (g.year == y) & (g.month != 2)]
        g = g.dropna(subset=["price_per_mmbtu"])
        ann = (g.price_per_mmbtu * g.quantity).sum() / g.quantity.sum()
        pm_h = ns.mon.map(gas_m[y])
        pd_h = pm_h * ns.date.map(ratio).fillna(1.0)
        cls, mw, hi = campd_gas(y, ids, pm)
        cm = campd_metrics(cls, mw, hi, u.index.to_numpy())
        rows.append({
            "year": y, "n_up": len(u), "hh": hh[y], "gas_ann": ann,
            "gas_up_monthly": pm_h.mean(), "hh_daily_ratio_up": ns.date.map(ratio).mean(),
            "hr_annual": ns.mec.mean() / ann,                  # SPP-80's residual basis
            "hr_monthly": (ns.mec / pm_h).mean(),               # each hour's own month
            "hr_daily": (ns.mec / pd_h).mean(),                 # month shaped by HH daily
            "mec_ns": ns.mec.mean(), "net_gw": u.net.mean() / 1e3,
            **cm,
        })
    t = pd.DataFrame(rows).set_index("year")
    base = t.loc[list(BASE_YEARS)].mean()
    for c in ("hr_annual", "hr_monthly", "hr_daily", "hr_all", "hr_flex", "hr_flex_p90",
              "hr_CC", "hr_CT", "hr_ST_GAS", "flexshare_CT", "flexshare_CC", "flexshare_ST_GAS",
              "share_CT", "share_CC", "share_ST_GAS", "ct_online_gw"):
        t[f"d_{c}"] = t[c] - base[c]
    pd.set_option("display.width", 250)
    print(t.round(3).T.to_string())
    som = som_rows()
    t = t.join(som)
    # Marginal-mix effect implied by the MMU's own frequencies: the change in the
    # simple-cycle share of gas-marginal intervals times the measured CT-minus-CC heat
    # rate gap in the upper tercile (CAMPD, this year).
    t["mix_hr_mmu"] = (t.sc_of_gas - t.loc[list(BASE_YEARS), "sc_of_gas"].mean()) * (t.hr_CT - t.hr_CC)
    # Residual basis on SPP's own hub (Panhandle Eastern, SOM annual incl. Feb): 2021 is
    # dropped from its base because Uri put Panhandle's Feb 2021 month near $22.
    t["hr_pepl"] = t.mec_ns / t.panhandle_eastern
    t["d_hr_pepl"] = t.hr_pepl - t.loc[[2019, 2020], "hr_pepl"].mean()
    t["deliv_over_pepl"] = t.gas_ann / t.panhandle_eastern
    t["mec_minus_p90_fuel"] = t.mec_ns - t.hr_flex_p90 * t.gas_ann  # $/MWh above the p90 flex unit's fuel
    print(t[["sc_of_gas", "gas_simple_cycle", "gas_combined_cycle", "wind", "coal", "mix_hr_mmu",
             "mmu_implied_hr", "panhandle_eastern", "southern_star", "henry_hub", "deliv_over_pepl",
             "hr_pepl", "d_hr_pepl", "mec_minus_p90_fuel"]].round(3).T.to_string())
    print("\nResidual by date window (MEC ex-scarcity / monthly delivered gas), season-matched:")
    print(residual_by_window(frames, gas_m, u_sets).round(3).to_string())
    print("\nResidual by month vs 2019-21 same month (upper tercile, ex-scarcity, monthly delivered gas):")
    print(residual_by_month(gas_m, u_sets).to_string())
    print("\nRamp-up cleared MW and within-net-load-band effect on MEC/delivered gas:")
    print(ramp_effect(frames, u_sets, gas_m).round(3).to_string())


if __name__ == "__main__":
    main()
