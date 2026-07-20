"""CAISO-105 priority-1 measurement: the belly DA-vs-RT price-basis wedge.

FINDING-caiso104 §3b (lane implication): the belly +6.0/+6.6/+4.3 residual has
survived BOTH conduct families the measured storage behaviour supports — the
bid-cost family (caiso-100/101, volume-refuted) and the DA charge-allocation
family (caiso-104 M1 v2, conduct-faithful yet lambda-inert; the DA bundle is
~72 % belly). The remaining hypothesis is the PRICE BASIS: the real fleet's
charge clears in the DAM at DA prices (IFM DA-share of realized charge
0.840/0.799/0.760 — FINDING-caiso102 §1), while the backcast scores the
model's lambda against the RT price. If the DA belly price sits materially
BELOW the RT belly price in exactly the charge-weighted hours, the LP's
requirement that the marginal charged MWh be arbitrage-profitable at RT
lambda is pricing the charge against the wrong basis, and the wedge is the
measured size of that mis-basis.

This probe MEASURES the wedge; it arms nothing (rule 19 — any mechanism goes
to an owner ask). Per year x window (the FINDING-caiso102 §3 window
convention), from `actual_lmp_hourly_CAISO.parquet` (da/rt columns, model
8760 clock):

  1. UNWEIGHTED basis: mean DA, mean RT, mean (DA-RT) over the window's hours
     — the raw calendar wedge, no conduct conditioning.
  2. MEASURED-charge weighting: charge-weighted mean DA and RT lambda with
     weights = the storage report's IFM (DA-scheduled) charge MW per model
     hour, and separately weights = RTD (realized) charge — the price basis
     the REAL fleet's charge decision actually cleared against vs the RT
     basis the backcast scores. LESR EN rows, TRADE_DATE+HOUR hour-ending ->
     hod = HOUR-1, Feb-29 dropped (the `_caiso102_charge_channels` clock
     convention shared by derive_caiso_charge_allocation.py).
  3. MODEL-charge weighting: same DA/RT weighted means with weights = the
     A-leg bundle's fleet-battery charge (storage.parquet, P1, non-PS) — the
     wedge in the hours the LP actually charges.
  4. The scoring identity: the model's charge-weighted RT-basis lambda uses
     the bundle's own model lambda (system.parquet CA demand-weighted) in the
     same model-charge hours, so the wedge can be read against the belly
     residual it is hypothesized to prop.

Usage:
  python scripts/probes/_caiso105_da_rt_basis.py <bundle_dir> \
      [--cache <market_output.parquet>]
--cache points at a pre-parsed concat of the storage-report market_output
sheets (the derive_caiso_charge_allocation.py --cache convention); without it
the quarterly xlsx are parsed (~5 min).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
YEARS = (2023, 2024, 2025)
# FINDING-caiso102 §3 window convention (hod, interval-beginning model clock).
WINDOWS = (
    ("overnight", (0, 1, 2, 3, 4, 5)),
    ("morning", (6, 7, 8, 9)),
    ("belly", (10, 11, 12, 13, 14)),
    ("pm-shldr", (15, 16)),
    ("evening", (17, 18, 19, 20, 21)),
    ("late", (22, 23)),
)
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _hidx(dates: pd.Series, hod: np.ndarray, year: int) -> np.ndarray:
    """(date, hod) -> model-hour index on the non-leap 8760 calendar.

    Feb-29 must already be dropped; in a leap year dayofyear is +1 after
    Feb-28 vs the model calendar (the `cems_hourly_by_klass` convention).
    """
    doy = dates.dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where((dates.dt.month > 2).to_numpy(), doy - 1, doy)
    return (doy - 1) * 24 + hod


def measured_charge(cache: Path | None) -> dict[int, dict[str, np.ndarray]]:
    """Per year: (8760,) IFM and RTD fleet charge MW (LESR, hour-avg)."""
    from derive_caiso_charge_allocation import hourly_pivot, load_market_output

    p = hourly_pivot(load_market_output(cache))
    p["TRADE_DATE"] = pd.to_datetime(p["TRADE_DATE"])
    out: dict[int, dict[str, np.ndarray]] = {}
    for year in YEARS:
        py = p[p.TRADE_DATE.dt.year == year]
        if py.empty:
            continue
        idx = _hidx(py.TRADE_DATE, py.hod.to_numpy(int), year)
        series = {}
        for col, tag in (("IFM_EN", "ifm"), ("RTD_EN", "rtd")):
            chg = np.clip(-np.nan_to_num(py[col].to_numpy(float)), 0.0, None)
            v = np.zeros(8760)
            np.add.at(v, idx, chg)
            series[tag] = v
        out[year] = series
    return out


def model_charge(bundle: Path, year: int) -> np.ndarray:
    """(8760,) A-leg fleet-battery charge MW (P1, pumped storage excluded)."""
    st = pd.read_parquet(bundle / "storage.parquet")
    st = st[(st["pass"] == "P1") & (st.year == year) & (st.tech != "pumped_storage")]
    v = np.zeros(8760)
    np.add.at(v, st.hour.to_numpy(int), st.charge_mw.to_numpy(float))
    return v


def model_lambda(bundle: Path, year: int) -> np.ndarray:
    """(8760,) CA demand-weighted model lambda (system.parquet, P1)."""
    s = pd.read_parquet(bundle / "system.parquet")
    s = s[(s["pass"] == "P1") & (s.year == year)]
    ca = s[~s.zone.str.startswith("WECC")]
    dw = (
        ca.assign(pw=ca.price * ca.demand)
        .groupby("hour")[["pw", "demand"]]
        .sum()
        .sort_index()
        .reindex(range(8760))
    )
    return (dw.pw / dw.demand).to_numpy()


def _wavg(v: np.ndarray, w: np.ndarray, mask: np.ndarray) -> float:
    m = mask & np.isfinite(v) & (w > 0)
    return float(np.average(v[m], weights=w[m])) if m.any() else float("nan")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    cache = None
    args = sys.argv[1:]
    if "--cache" in args:
        cache = Path(args[args.index("--cache") + 1])

    meas = measured_charge(cache)
    hod = np.arange(8760) % 24
    lmp = pd.read_parquet(LMP)

    for year in YEARS:
        a = lmp[lmp.year == year].sort_values("hour")
        da = np.full(8760, np.nan)
        rt = np.full(8760, np.nan)
        da[a.hour.to_numpy(int)] = a.da.to_numpy(float)
        rt[a.hour.to_numpy(int)] = a.rt.to_numpy(float)
        chg_m = model_charge(bundle, year)
        lam = model_lambda(bundle, year)
        mm = meas.get(year, {})
        chg_ifm = mm.get("ifm", np.zeros(8760))
        chg_rtd = mm.get("rtd", np.zeros(8760))

        print(f"\n===================== {year} =====================")
        print(
            "window     |  hrs-mean DA    RT  DA-RT | IFM-wtd DA    RT  wedge "
            "| RTD-wtd DA    RT  wedge | MODEL-wtd DA    RT  wedge  mod-lam"
        )
        for wname, whods in WINDOWS:
            wm = np.isin(hod, whods)
            fin = wm & np.isfinite(da) & np.isfinite(rt)
            un_da, un_rt = float(np.nanmean(da[fin])), float(np.nanmean(rt[fin]))
            i_da, i_rt = _wavg(da, chg_ifm, fin), _wavg(rt, chg_ifm, fin)
            r_da, r_rt = _wavg(da, chg_rtd, fin), _wavg(rt, chg_rtd, fin)
            m_da, m_rt = _wavg(da, chg_m, fin), _wavg(rt, chg_m, fin)
            m_lam = _wavg(lam, chg_m, fin)
            print(
                f"{wname:<10} | {un_da:8.1f} {un_rt:5.1f} {un_da - un_rt:+6.1f} "
                f"| {i_da:7.1f} {i_rt:5.1f} {i_da - i_rt:+6.1f} "
                f"| {r_da:7.1f} {r_rt:5.1f} {r_da - r_rt:+6.1f} "
                f"| {m_da:7.1f} {m_rt:5.1f} {m_da - m_rt:+6.1f} {m_lam:8.1f}"
            )
        # window charge volumes (TWh) per weight basis, for the record
        print("window     |  IFM TWh  RTD TWh  MODEL TWh")
        for wname, whods in WINDOWS:
            wm = np.isin(hod, whods)
            print(
                f"{wname:<10} | {chg_ifm[wm].sum() / 1e6:8.3f} "
                f"{chg_rtd[wm].sum() / 1e6:8.3f} {chg_m[wm].sum() / 1e6:9.3f}"
            )
        ann = (
            f"annual     | {chg_ifm.sum() / 1e6:8.3f} "
            f"{chg_rtd.sum() / 1e6:8.3f} {chg_m.sum() / 1e6:9.3f}"
        )
        print(ann)
    return 0


if __name__ == "__main__":
    sys.exit(main())
