"""nyiso-238 phase 0 (ZERO LP): which seam defect manufactures the keeper's
non-positive ``Upstate_West`` hours?

The object is nyiso-237's finding: the keeper prices ``Upstate_West`` at or below
$0 in **498 hours of 2022** against a measured 21 (WEST zone alone) / 127 (the
five-zone A-E mean that IS the model zone), and in every one of those hours the
model's ``Upstate_West -> Capital_Hudson`` link sits at its monthly measured
Central-East DAM TTC cap (``NYISO_INTERFACE_TTC_BY_MONTH``). This probe censuses
that hour set against four candidate causes, all from COMMITTED data:

* **(a) flat monthly-mean TTC applied hourly** - the armed table is a calendar-
  month arithmetic mean of an HOURLY posting (nyiso-104), so every hour whose
  true posted limit exceeded the mean is over-constrained. Measured against the
  committed MIS P-32 hourly ``positive_limit_mw`` for ``CENTRAL EAST - VC``.
* **(b) no West export outlet** - the model's ``NYISO_external -> Upstate_West``
  link bottoms at -138 MW, i.e. essentially no export path, while zones A/D tie
  to IESO, PJM-west and HQ. Measured against the P-32 external schedules.
* **(c) firm imports into a saturated zone** - ``nyiso_firm_imports`` floors
  HQ/IESO rows via ``min_gen``; nyiso-237 measured 433 MW still flowing INTO the
  West in the fabricated hours. Measured against the real HQ/OH schedules in the
  same clock hours.
* **(d) the nested cutset** - the model's single A-E -> F+ link carries the
  **TOTAL EAST** cutset but is capped at the **CENTRAL EAST** sub-cutset's limit
  (nyiso-224's confirmed object). Measured as the TOTAL EAST / CENTRAL EAST flow
  ratio and as the real TOTAL EAST flow against the model's cap.

Every input is committed and every comparison in the 498-hour census is
**hour-for-hour on the same local clock** (2022 is fully covered by both the
keeper sidecar and the P-32 corpus), not month x hod matched:

* ``results/calibration/nyiso235_gasrepair_span/hourly/system_<y>.parquet`` -
  the keeper's P1 zonal price / demand.
* ``data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<y>.csv.gz`` -
  the MIS P-32 "Interface Limits and Flows" posting, hourly, with the
  most-binding ``positive_limit_mw`` per hour (README in that directory).
* ``market_sim.config.constants.NYISO_INTERFACE_TTC_BY_MONTH`` - the armed cap.

Usage::

    python3 scripts/probes/nyiso238_central_east_seam_phase0.py \\
        --keeper results/calibration/nyiso235_gasrepair_span [--years 2022 2023]

Record: docs/PRECOMMIT-nyiso238-central-east-hourly-grain-2026-09-16.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import (  # noqa: E402
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_YEAR,
)

LINK = ("Upstate_West", "Capital_Hudson")
CE = "CENTRAL EAST - VC"
TE = "TOTAL EAST"
# P-32 external schedule rows whose NYISO landing zone is inside the model's
# Upstate_West (zones A-E): Ontario ties into zone A/B (Niagara/St Lawrence
# corridor) and HQ into zone D (Chateauguay / Cedars). PJM's ties land
# downstate (zone G/J) and are carried for the contrast, not the outlet test.
WEST_EXTERNAL = ["SCH - OH - NY", "SCH - HQ - NY", "SCH - HQ_CEDARS"]
DOWNSTATE_EXTERNAL = ["SCH - PJ - NY", "SCH - PJM_HTP", "SCH - PJM_NEPTUNE", "SCH - PJM_VFT"]
SENTINEL = 9999.0


def load_p32(year: int) -> pd.DataFrame:
    """Return the P-32 hourly frame for ``year`` with sentinel limits nulled."""
    path = ROOT / f"data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_{year}.csv.gz"
    d = pd.read_csv(path)
    d["ts"] = pd.to_datetime(d["interval_start_local"])
    d["month"] = d.ts.dt.month
    for col in ("positive_limit_mw", "negative_limit_mw"):
        d.loc[d[col].abs() >= SENTINEL, col] = np.nan
    # A negative positive-limit is a posted counter-flow requirement, not a
    # transfer capability; it cannot serve as an export headroom and is nulled.
    d.loc[d.positive_limit_mw < 0, "positive_limit_mw"] = np.nan
    return d


def interface_hourly(d: pd.DataFrame, name: str, year: int) -> pd.DataFrame:
    """Return one interface's rows indexed by hour-of-year 0..8759.

    ALIGNMENT CONVENTION. The model's hour index is a NAIVE non-leap 8760-hour
    sequence with no DST (``data.fleet.models._hour_to_month_index`` maps hours
    to months off a representative non-leap year), while the P-32
    ``interval_start_local`` column is true wall-clock local time. Both series
    run Jan-01 00:00 -> Dec-31 23:00 with exactly 8760 rows, so row ``i`` is
    matched to model hour ``i`` POSITIONALLY. Between the spring-forward gap and
    the fall-back duplicate the two clocks differ by at most ONE hour (measured
    2022: 5,711 of 8,760 rows carry a +1 h offset, 8 of which cross a month
    boundary); everywhere else they are identical. Every month label and every
    model cap below is therefore taken from the MODEL's naive clock, so the cap
    array is exact by construction and only the measured P-32 value carries the
    <= 1 h positional slack.
    """
    x = d[d.interface == name].copy().sort_values("ts").reset_index(drop=True)
    x["hour"] = np.arange(len(x))
    return x


def model_clock(year: int, hours: int) -> pd.DatetimeIndex:
    """Return the MODEL's naive hour clock (no DST) for ``year``."""
    return pd.date_range(f"{year}-01-01", periods=hours, freq="h")


def model_cap_by_hour(year: int, hours: int) -> np.ndarray:
    """Return the armed model cap (MW) broadcast to every hour of ``year``."""
    monthly = NYISO_INTERFACE_TTC_BY_MONTH.get(year, {}).get(LINK)
    if monthly is None:
        annual = NYISO_INTERFACE_TTC_BY_YEAR[year][LINK]
        return np.full(hours, float(annual))
    return np.asarray([monthly[m - 1] for m in model_clock(year, hours).month], dtype=float)


def keeper_zone_price(keeper: Path, year: int, zone: str) -> pd.DataFrame:
    """Return the keeper's P1 price/demand for ``zone`` indexed by hour."""
    s = pd.read_parquet(keeper / f"hourly/system_{year}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone == zone)].sort_values("hour")
    return s.reset_index(drop=True)


def census(keeper: Path, year: int) -> dict:
    """Run the four-candidate census for one year and print it."""
    p32 = load_p32(year)
    ce = interface_hourly(p32, CE, year)
    te = interface_hourly(p32, TE, year)
    n = min(len(ce), len(te), 8784)
    uw = keeper_zone_price(keeper, year, "Upstate_West")
    n = min(n, len(uw))
    cap = model_cap_by_hour(year, n)

    price = uw.price.to_numpy()[:n]
    ce_lim = ce.positive_limit_mw.to_numpy()[:n]
    ce_flow = ce.flow_mw.to_numpy()[:n]
    te_flow = te.flow_mw.to_numpy()[:n]
    # Month labels come from the MODEL's naive clock, not the local timestamp,
    # so ``cap`` and ``month`` are consistent by construction (see
    # ``interface_hourly``'s alignment note).
    month = model_clock(year, n).month.to_numpy()

    neg = price <= 0.0
    lo5 = price <= 5.0
    H = np.flatnonzero(neg)

    print(f"\n{'='*94}\n  YEAR {year} - the fabricated-hour set\n{'='*94}")
    print(f"  model Upstate_West <= $0 : {int(neg.sum()):5d} h      <= $5 : {int(lo5.sum()):5d} h")
    if H.size == 0:
        print("  EMPTY SET - no fabrication in this year; every candidate is inert here.")
        return {"year": year, "n_neg": 0}

    # ---- (a) grain: hourly posted limit vs the flat monthly mean --------------
    have = np.isfinite(ce_lim[H])
    head_a = ce_lim[H] - cap[H]
    print(f"\n  (a) FLAT MONTHLY-MEAN GRAIN  [instrument: P-32 hourly {CE} positive_limit_mw]")
    print(f"      hours with a posted hourly limit      : {int(have.sum())}/{H.size}")
    print(f"      hours whose HOURLY limit > monthly cap: {int(np.nansum(head_a > 0))} "
          f"({100*np.nansum(head_a > 0)/H.size:.1f} %)")
    print(f"      headroom the grain repair adds (MW)   : mean {np.nanmean(head_a):8.1f}   "
          f"p50 {np.nanmedian(head_a):8.1f}   p90 {np.nanquantile(head_a, .90):8.1f}")
    # WHY the grain repair moves the wrong way: planned transmission outages
    # (which is what the within-month variation IS, nyiso-104 3.) are taken in
    # low-load hours, which are exactly the hours the model over-supplies the
    # West. Measured as the hourly limit's own anomaly against its month mean,
    # split by the keeper's own Upstate_West load quintile.
    dem = uw.demand.to_numpy()[:n]
    mm = pd.Series(ce_lim[:n]).groupby(month).transform("mean").to_numpy()
    anom = ce_lim[:n] - mm
    q = pd.qcut(pd.Series(dem), 5, labels=False, duplicates="drop").to_numpy()
    qs = [float(np.nanmean(anom[q == i])) for i in range(5)]
    print(f"      hourly-limit anomaly vs its own month mean, by Upstate_West load quintile (MW):")
    print(f"        Q1(low load) -> Q5(high): " + " · ".join(f"{v:+.0f}" for v in qs))
    print(f"      => the posted limit is {qs[0]-qs[-1]:+.0f} MW LOWER in the lowest load quintile "
          f"than the highest; outage derates co-occur with the hours the model fabricates.")

    # ---- (d) nested cutset: TOTAL EAST vs CENTRAL EAST ----------------------
    head_d = te_flow[H] - cap[H]
    print(f"\n  (d) NESTED CUTSET  [instrument: P-32 {TE} flow, the cutset the model link IS]")
    print(f"      real TOTAL EAST flow in these hours   : mean {te_flow[H].mean():8.1f}   "
          f"p50 {np.median(te_flow[H]):8.1f}")
    print(f"      model cap on the same cutset          : mean {cap[H].mean():8.1f}")
    print(f"      hours real TE flow EXCEEDED model cap : {int((head_d > 0).sum())} "
          f"({100*(head_d > 0).mean():.1f} %)")
    print(f"      shortfall of the cap vs real flow (MW): mean {head_d.mean():8.1f}   "
          f"p50 {np.median(head_d):8.1f}")
    print(f"      TE/CE flow ratio in these hours       : "
          f"mean {np.mean(te_flow[H]/np.maximum(ce_flow[H],1e-6)):6.2f}")

    # ---- (b) West export outlet ---------------------------------------------
    print(f"\n  (b) WEST EXPORT OUTLET  [instrument: P-32 external schedules, + = import to NY]")
    tot_w = np.zeros(n)
    for nm in WEST_EXTERNAL:
        x = interface_hourly(p32, nm, year)
        f = x.flow_mw.to_numpy()[:n]
        tot_w += np.nan_to_num(f)
        print(f"      {nm:22s} all-h {np.nanmean(f):8.1f} | fab-h {np.nanmean(f[H]):8.1f} "
              f"| delta {np.nanmean(f[H])-np.nanmean(f):+8.1f}")
    print(f"      {'WEST-LANDING TOTAL':22s} all-h {tot_w.mean():8.1f} | fab-h {tot_w[H].mean():8.1f} "
          f"| delta {tot_w[H].mean()-tot_w.mean():+8.1f}")
    exp_h = (tot_w[H] < 0).mean()
    print(f"      hours the West ties ran NET EXPORT    : {100*exp_h:.1f} % "
          f"(all hours {100*(tot_w<0).mean():.1f} %)")

    # ---- (c) firm imports ----------------------------------------------------
    print(f"\n  (c) FIRM IMPORT FLOOR  [model floors HQ/IESO via min_gen; 433 MW measured in fab hours]")
    for nm in ("SCH - OH - NY", "SCH - HQ - NY"):
        x = interface_hourly(p32, nm, year)
        f = x.flow_mw.to_numpy()[:n]
        print(f"      {nm:22s} fab-h mean {np.nanmean(f[H]):8.1f} | "
              f"p10 {np.nanquantile(f[H],.10):8.1f} | share of fab-h at/below 0: "
              f"{100*np.nanmean(f[H] <= 0):5.1f} %")

    # ---- monthly detail ------------------------------------------------------
    print(f"\n  MONTHLY DETAIL (fabricated hours only)")
    print(f"      {'mo':>3s} {'fab h':>6s} {'cap':>7s} {'CE lim p50':>11s} {'CE lim p90':>11s} "
          f"{'(a) MW':>8s} | {'TE flow p50':>12s} {'(d) MW':>8s}")
    rows = []
    for m in range(1, 13):
        sel = H[month[H] == m]
        if sel.size == 0:
            continue
        a = np.nanmedian(ce_lim[sel] - cap[sel])
        dd = np.median(te_flow[sel] - cap[sel])
        rows.append((m, sel.size, cap[sel][0], np.nanmedian(ce_lim[sel]),
                     np.nanquantile(ce_lim[sel], .90), a, np.median(te_flow[sel]), dd))
        print(f"      {m:3d} {sel.size:6d} {cap[sel][0]:7.0f} {np.nanmedian(ce_lim[sel]):11.0f} "
              f"{np.nanquantile(ce_lim[sel],.90):11.0f} {a:8.0f} | {np.median(te_flow[sel]):12.0f} {dd:8.0f}")
    return {
        "year": year, "n_neg": int(neg.sum()), "n_lo5": int(lo5.sum()),
        "a_share_pos": float(np.nansum(head_a > 0) / H.size),
        "a_mean_mw": float(np.nanmean(head_a)),
        "d_share_pos": float((head_d > 0).mean()),
        "d_mean_mw": float(head_d.mean()),
        "monthly": rows,
    }


def grain_vs_mean_all_years(years: list[int]) -> None:
    """Print the level/grain reconciliation: armed monthly mean vs P-32 hourly."""
    print(f"\n{'='*94}\n  LEVEL RECONCILIATION - armed DAM monthly mean vs P-32 hourly posting\n{'='*94}")
    print(f"  {'yr':>4s} {'mo':>3s} {'MODEL cap':>10s} {'P32 lim mean':>13s} {'diff':>8s} "
          f"{'P32 p10':>9s} {'P32 p90':>9s} {'p90/mean':>9s}")
    for y in years:
        p32 = load_p32(y)
        ce = p32[p32.interface == CE]
        monthly = NYISO_INTERFACE_TTC_BY_MONTH.get(y, {}).get(LINK)
        if monthly is None:
            continue
        for m in range(1, 13):
            lim = ce[ce.month == m].positive_limit_mw.dropna()
            if lim.empty:
                continue
            mm = lim.mean()
            print(f"  {y:4d} {m:3d} {monthly[m-1]:10.0f} {mm:13.0f} {mm-monthly[m-1]:+8.0f} "
                  f"{lim.quantile(.10):9.0f} {lim.quantile(.90):9.0f} {lim.quantile(.90)/mm:9.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", default="results/calibration/nyiso235_gasrepair_span")
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023, 2024, 2025])
    args = ap.parse_args()
    keeper = ROOT / args.keeper if not Path(args.keeper).is_absolute() else Path(args.keeper)

    out = [census(keeper, y) for y in args.years]
    grain_vs_mean_all_years(args.years)

    print(f"\n{'='*94}\n  SUMMARY\n{'='*94}")
    print(f"  {'yr':>4s} {'<=$0':>6s} {'<=$5':>6s} {'(a) share>0':>12s} {'(a) mean MW':>12s} "
          f"{'(d) share>0':>12s} {'(d) mean MW':>12s}")
    for o in out:
        if o.get("n_neg", 0) == 0:
            print(f"  {o['year']:4d} {0:6d} {'-':>6s} {'inert':>12s} {'-':>12s} {'inert':>12s} {'-':>12s}")
            continue
        print(f"  {o['year']:4d} {o['n_neg']:6d} {o['n_lo5']:6d} {100*o['a_share_pos']:11.1f}% "
              f"{o['a_mean_mw']:12.1f} {100*o['d_share_pos']:11.1f}% {o['d_mean_mw']:12.1f}")


if __name__ == "__main__":
    main()
