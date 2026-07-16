"""A2 marginal-price attribution on a solved CAISO bundle (autumn-2025 lane).

Rebuild of the caiso-87 session's attribution tool (2026-07-16 handoff, Session
1a): classifies the model's hourly system lambda against the CONSTRUCTED import
rung offers and the in-state CC floor, and prints monthly / hour-of-day
model-vs-actual tables. No LP — reads a solved bundle's dispatch parquets.

Offer construction mirrors the injectors byte-for-byte where possible
(``transmission.inject_caiso_import_hub_prices`` + surplus-clean block):

  PNW_midC          = MALIN nodal DA LMP + $5 OATT wheel            (EF 0)
  DSW_solar_PV      = PALOVRDE + $4 wheel                           (EF 0)
  DSW_surplus_clean = PALOVRDE + $4 wheel (surplus-trigger hours)   (EF 0)
  DSW_CCGT          = PALOVRDE + $4 + 0.37 x allowance  (+gas-coupling delta)
  DSW_CT            = PALOVRDE + $4 + 0.55 x allowance  (+gas-coupling delta)
  WECC_scarcity     = PALOVRDE + $6 + 0.428 x allowance
  CC floor          = 7.0 x CA citygate daily + $2.5 VOM + 0.37 x allowance

The gas-coupling delta (spot - F923 monthly, x HR) is omitted — it is ~0-2
$/MWh in 2024-25 and the classification tolerance absorbs it; the printed
class shares are attribution evidence, not scored metrics.

Usage:
  python scripts/probes/_caiso_autumn2025_attribution.py <bundle_dir> <year> [months...]
  e.g. ... results/calibration/caiso87_dsw_surplus_clean 2025 9 10 11 12
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MON_OF_HOUR = np.repeat(np.arange(1, 13), np.array(_DAYS) * 24)
HOD = np.tile(np.arange(24), 365)

# 2023/24/25 CARB allowance settlement means the keeper lineage uses
# (FINDING-caiso82 SS1; handoff "allowances 33.03/35.23/28.06").
ALLOWANCE = {2023: 33.03, 2024: 35.23, 2025: 28.06}
CAISO_ZONES = ["LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26"]
TOL = 2.0  # $/MWh classification tolerance around each constructed offer


def load_gas_daily() -> pd.Series:
    """CA citygate daily spot ($/MMBtu), forward-filled to a dense calendar."""
    g = pd.read_csv(
        REPO / "data/raw/gas-prices/caiso_citygate_daily.csv", parse_dates=["date"]
    ).set_index("date")["ca_composite_usd_mmbtu"]
    idx = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    return g.reindex(idx.union(g.index)).sort_index().ffill().bfill().reindex(idx)


def load_socal_weekly() -> pd.Series:
    """SoCal citygate weekly print ($/MMBtu), forward-filled daily (trigger gas)."""
    g = (
        pd.read_csv(
            REPO / "data/raw/gas-prices/pge_socal_citygate_weekly.csv",
            parse_dates=["date"],
        )
        .set_index("date")["socal_citygate_usd_mmbtu"]
        .dropna()
    )
    idx = pd.date_range("2023-01-01", "2025-12-31", freq="D")
    return g.reindex(idx.union(g.index)).sort_index().ffill().bfill().reindex(idx)


def daily_to_hourly(s: pd.Series, year: int) -> np.ndarray:
    """Expand a dense daily series to the model's 8760 clock (no Feb 29)."""
    dsel = pd.date_range(
        f"{year}-01-01", periods=366 if year % 4 == 0 else 365, freq="D"
    )
    v = s.reindex(dsel)
    if year % 4 == 0:
        v = v[~((v.index.month == 2) & (v.index.day == 29))]
    return np.repeat(v.to_numpy(dtype=float), 24)


def main() -> None:
    bundle = Path(sys.argv[1])
    year = int(sys.argv[2])
    months = [int(m) for m in sys.argv[3:]] or [9, 10, 11, 12]

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    # Model system lambda: unweighted mean across the 5 CAISO zones (attribution
    # basis; the scored C3a is demand-weighted — compare vs bench rt_mon).
    zl = disp[disp.zone.isin(CAISO_ZONES)].groupby(["zone", "hour"])["lmp"].first()
    lam = zl.groupby("hour").mean().reindex(range(8760)).to_numpy()

    # Import tranche dispatch (MW by tranche-hour).
    imp = disp[disp.klass == "import"]
    imw = imp.pivot_table(index="hour", columns="unit_id", values="mw", aggfunc="sum")
    imw = imw.reindex(range(8760)).fillna(0.0)

    # Measured hub prices on the model clock.
    hub = pd.read_parquet(
        REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"
    )
    hp = hub.pivot_table(index=["year", "hour"], columns="hub", values="price")
    full = pd.MultiIndex.from_product([[year], range(8760)], names=["year", "hour"])
    hp = hp.reindex(full).loc[year]
    malin = hp["MALIN"].to_numpy()
    pv = hp["PALOVRDE"].to_numpy()

    # Actual CAISO system RT/DA.
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
    ).set_index(["year", "hour"])
    act = act.reindex(full).loc[year]
    rt = act["rt"].to_numpy()

    alw = ALLOWANCE[year]
    gas_d = daily_to_hourly(load_gas_daily(), year)
    socal_w = daily_to_hourly(load_socal_weekly(), year)
    trigger_on = np.isfinite(pv) & (pv < 6.97 * socal_w + 2.5)

    offers = {
        "PNW_midC": malin + 5.0,
        "DSW_cleanparity": pv + 4.0,  # solar_PV / surplus_clean / firm parity
        "DSW_CCGT": pv + 4.0 + 0.37 * alw,
        "DSW_CT": pv + 4.0 + 0.55 * alw,
        "WECC_scarcity": pv + 6.0 + 0.428 * alw,
        "CC_floor": 7.0 * gas_d + 2.5 + 0.37 * alw,
    }

    print(f"=== {bundle.name} {year} — A2 attribution ===")
    print(f"months: {months}   allowance ${alw}/t   tol ±${TOL}")

    for m in months:
        sel = MON_OF_HOUR == m
        n = int(sel.sum())
        lam_m, rt_m = lam[sel], rt[sel]
        ok = np.isfinite(lam_m) & np.isfinite(rt_m)
        print(
            f"\n--- month {m}: model mean {np.nanmean(lam_m):.1f} vs actual RT "
            f"{np.nanmean(rt_m):.1f} (gap {np.nanmean(lam_m) - np.nanmean(rt_m):+.1f}) "
            f"| hub MALIN {np.nanmean(malin[sel]):.1f} PV {np.nanmean(pv[sel]):.1f} "
            f"| trigger-ON {np.nanmean(trigger_on[sel]) * 100:.0f}% ---"
        )

        # Marginal-class share: nearest constructed offer within TOL.
        rows = []
        for name, off in offers.items():
            d = np.abs(lam_m - off[sel])
            rows.append((name, d))
        dmat = np.vstack([d for _, d in rows])
        nearest = np.argmin(dmat, axis=0)
        within = dmat[nearest, np.arange(dmat.shape[1])] <= TOL
        shares = {}
        for i, (name, _) in enumerate(rows):
            shares[name] = float(np.mean(within & (nearest == i) & ok))
        shares["UNMATCHED"] = float(np.mean((~within) & ok))
        print(
            "  model-lambda class shares:",
            {k: f"{v * 100:.0f}%" for k, v in shares.items() if v >= 0.005},
        )

        # Actual-vs-offer: share of hours actual RT below EVERY non-clean offer,
        # and below clean parity (the no-wedge signature).
        gassy = np.minimum.reduce(
            [offers["DSW_CCGT"][sel], offers["PNW_midC"][sel], offers["CC_floor"][sel]]
        )
        print(
            f"  actual RT below all gas/wedge offers: "
            f"{np.nanmean((rt_m < gassy - 0.5)[ok]) * 100:.0f}%   "
            f"below clean parity (PV+4): "
            f"{np.nanmean((rt_m < offers['DSW_cleanparity'][sel] - 0.5)[ok]) * 100:.0f}%"
        )

        # hour-of-day gap table.
        hod = HOD[sel]
        gap = lam_m - rt_m
        gtab = pd.DataFrame(
            {
                "hod": hod,
                "gap": gap,
                "lam": lam_m,
                "rt": rt_m,
                "malin": malin[sel],
                "pv": pv[sel],
            }
        )
        g = gtab.groupby("hod").mean().round(1)
        print(g.T.to_string())

        # Import tranche mean MW in-month.
        im = imw.loc[sel].mean().round(0)
        im = im[im.abs() > 1]
        print("  import tranche mean MW:", im.to_dict())


if __name__ == "__main__":
    main()
