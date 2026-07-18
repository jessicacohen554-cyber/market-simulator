"""Score the ercot41 Stage-4 integration run against gates G-1..G-7 (plan §6).

Reads ercot41's full solve bundle (system.parquet: per-zone hourly price/demand/
reserve_price/rtordpa_overlay) and the RT actual hub LMP, and prints the gate
table plus the deeper metrics the standard dashboard payload doesn't carry
(tail>500/>1000, May-2024 acute-day dw, the RTORDPA∧reserve-dual min-overlap
audit). Baseline dw / tail comparisons come from the decoded ercot32 (keeper) and
ercot33 (ex-overlay) dashboard payloads.

All price gates are scored vs RT actuals; the DA diagnostic is reported alongside.
Usage: python scripts/archive/score_ercot41_gates.py [BUNDLE_DIR]
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

BUNDLE = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else REPO / "results/calibration/ercot41_integration_2026-07"
)
YEARS = [2023, 2024, 2025]

# RT actual hub series (the scarcity-relevant benchmark; C3c / tail).
_act = pd.read_parquet(CALIBRATION_DIR / "actual_lmp_hourly_ERCOT.parquet")


def actual_rt(year: int) -> np.ndarray:
    d = _act[_act["year"] == year].sort_values("hour")
    rt = d["rt"].to_numpy(float)
    da = d["da"].to_numpy(float) if "da" in d.columns else np.full_like(rt, np.nan)
    return np.where(np.isnan(rt), da, rt)


def actual_da(year: int) -> np.ndarray:
    d = _act[_act["year"] == year].sort_values("hour")
    return d["da"].to_numpy(float)


def load_year(year: int):
    """Return (price[z,t], demand[z,t], reserve_price[t], rtordpa[t], zones)."""
    df = pd.read_parquet(BUNDLE / "system.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    zones = sorted(df["zone"].unique())
    T = int(df["hour"].max()) + 1
    price = np.zeros((len(zones), T))
    dem = np.zeros((len(zones), T))
    for i, z in enumerate(zones):
        zd = df[df["zone"] == z].sort_values("hour")
        price[i] = zd["price"].to_numpy(float)
        dem[i] = zd["demand"].to_numpy(float)
    rp = df[df["zone"] == zones[0]].sort_values("hour")["reserve_price"].to_numpy(float)
    rtordpa = (
        df[df["zone"] == zones[0]]
        .sort_values("hour")["rtordpa_overlay"]
        .to_numpy(float)
        if "rtordpa_overlay" in df.columns
        else np.zeros(T)
    )
    return price, dem, rp, rtordpa, zones


def dw_mean(price, dem, mask=None):
    """System load-weighted mean LMP across zones (optionally over a mask of hours)."""
    if mask is not None:
        price, dem = price[:, mask], dem[:, mask]
    num = (price * dem).sum()
    den = dem.sum()
    return num / den if den else float("nan")


def hub_price(price, dem):
    """Load-weighted hub series (per hour, weighted across zones) — the model 'hub'."""
    den = dem.sum(axis=0)
    den = np.where(den <= 0, 1.0, den)
    return (price * dem).sum(axis=0) / den


def month_index(T):
    # 8760-hour calendar (non-leap alignment used throughout the repo bundles).
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    idx = np.zeros(T, dtype=int)
    h = 0
    for m, d in enumerate(days):
        n = d * 24
        idx[h : h + n] = m
        h += n
    idx[h:] = 11
    return idx


baselines = json.load(
    open(REPO / "scratchpad_baselines.json")
    if (REPO / "scratchpad_baselines.json").exists()
    else open(
        "/tmp/claude-0/-home-user-market-simulator/c408e5e1-5fe8-5963-96c0-ab9e73f26219/scratchpad/baselines.json"
    )
)

print(
    f"\n{'=' * 78}\n  ercot41 Stage-4 gate scoring   bundle={BUNDLE.name}\n{'=' * 78}"
)

results = {}
for year in YEARS:
    price, dem, rp, rtordpa, zones = load_year(year)
    T = price.shape[1]
    rt = actual_rt(year)[:T]
    da = actual_da(year)[:T]
    hub = hub_price(price, dem)
    maxz = price.max(axis=0)

    dw = dw_mean(price, dem)
    dw_act_rt = np.nansum(rt * dem.sum(axis=0)) / dem.sum()  # actual dw over model load
    # tail (max zonal LMP vs actual hub)
    tail = {thr: int((maxz > thr).sum()) for thr in (200, 500, 1000)}
    tail_act = {thr: int(np.nansum(rt > thr)) for thr in (200, 500, 1000)}

    # monthly dw
    mi = month_index(T)
    mon_dw = [dw_mean(price, dem, mi == m) for m in range(12)]
    mon_rt = [
        np.nansum(rt[mi == m] * dem.sum(axis=0)[mi == m])
        / dem.sum(axis=0)[mi == m].sum()
        for m in range(12)
    ]

    results[year] = dict(
        dw=round(dw, 2),
        dw_act=round(float(dw_act_rt), 2),
        tail=tail,
        tail_act=tail_act,
        mon_dw=[round(x, 2) for x in mon_dw],
        mon_rt=[round(float(x), 2) for x in mon_rt],
        maxz=maxz,
        hub=hub,
        rt=rt,
        da=da,
        dem=dem,
        price=price,
        rp=rp,
        rtordpa=rtordpa,
        mi=mi,
    )

    b32 = baselines["ercot32"][str(year)]
    b33 = baselines["ercot33"][str(year)]
    print(f"\n----- {year} -----")
    print(
        f"  system dw LMP:  ercot41 ${dw:6.2f}   RT-actual ${dw_act_rt:6.2f}   "
        f"ercot32 ${b32['dw']}   ercot33 ${b33['dw']}"
    )
    print(
        f"  DA diagnostic:  actual DA ${np.nanmean(da):6.2f} (DART premium ${np.nanmean(da) - np.nanmean(rt):+.2f})"
    )
    print(
        f"  tail  model >200/>500/>1000: {tail[200]:4d}/{tail[500]:3d}/{tail[1000]:3d}"
    )
    print(
        f"        actual>200/>500/>1000: {tail_act[200]:4d}/{tail_act[500]:3d}/{tail_act[1000]:3d}   "
        f"(ercot32 g200m {b32['gt200_model']}, ercot33 g200m {b33['gt200_model']})"
    )

# --- G-1 acute days: May-2024 8/24/26 ---
print(
    f"\n{'=' * 78}\n  G-1 acute-day reproduction (May-2024 8/24/26, dw LMP model vs RT)\n{'=' * 78}"
)
r24 = results[2024]
for day in (8, 24, 26):
    # May = month 4; day-of-month → hour offset from Jan 1 (non-leap): Jan-Apr = 31+28+31+30 = 120 days
    h0 = (120 + (day - 1)) * 24
    sl = slice(h0, h0 + 24)
    m_dw = dw_mean(r24["price"][:, sl], r24["dem"][:, sl])
    a_dw = (
        np.nansum(r24["rt"][sl] * r24["dem"].sum(axis=0)[sl])
        / r24["dem"].sum(axis=0)[sl].sum()
    )
    err = (m_dw - a_dw) / a_dw * 100 if a_dw else float("nan")
    print(
        f"  May {day:2d} 2024: model ${m_dw:7.2f}   RT-actual ${a_dw:7.2f}   {err:+6.1f}%  "
        f"{'PASS' if abs(err) <= 25 else 'MISS'} (±25%)"
    )

# --- G-6 min-overlap: RTORDPA ∧ reserve-dual ---
print(
    f"\n{'=' * 78}\n  G-6 one-event-one-channel: RTORDPA ∧ reserve-dual overlap\n{'=' * 78}"
)
for year in YEARS:
    r = results[year]
    rtordpa, rp = r["rtordpa"], r["rp"]
    both = (rtordpa > 1.0) & (rp > 1.0)
    overlap_k = float(np.minimum(rtordpa, rp)[both].sum()) / 1000.0
    print(
        f"  {year}: RTORDPA active {int((rtordpa > 1).sum()):4d}h, reserve-dual active {int((rp > 1).sum()):5d}h, "
        f"shared {int(both.sum()):3d}h, min-overlap ${overlap_k:.2f}k"
    )

json.dump(
    {
        y: {k: v for k, v in results[y].items() if not isinstance(v, np.ndarray)}
        for y in YEARS
    },
    open(BUNDLE / "ercot41_gate_metrics.json", "w"),
    indent=1,
)
print(f"\n  wrote {BUNDLE / 'ercot41_gate_metrics.json'}")
