"""CAISO-103 derive-first probe: the belly-ALLOCATION statistics for the
volume-holding mechanism design (the caiso-102 §7 re-charter).

FINDING-caiso102 measured the three inelastic-conduct channels at the
window/annual grain: the DAM allocates 76-84 % of realized charge (belly
82-91 %), the FMM covers 94-97 %, RT additions are reg-down-deployment-shaped,
and the non-belly charge clears $6-9 above the belly floor (overnight second
cycle + AS SOC restoration). The CAISO-103 charter asks for the MECHANISM that
holds that volume and re-prices the charge margin; its candidate shapes each
consume a statistic FINDING-caiso102 does not carry at the needed grain. This
probe measures them (caiso-93/94 derive-first protocol — NO LP is built or
solved; any mechanism goes to an owner ask):

(A) DA-ALLOCATION HOD PROFILE — per (year, hod): the fleet-normalized IFM
    charge rate (mean + p25/p50/p75 across days, ÷ EIA-860 monthly fleet MW,
    the caiso-99 envelope's exact denominator basis) and the hod share of
    annual IFM charge. Cross-year stability of the normalized shape (pairwise
    r + per-hod CV) — the forward-story test for a DA-allocation-profile
    charge schedule (shape × future fleet MW).
(B) WINDOW ALLOCATION SHARES — per day: each window's share of the day's
    total IFM charge; p25/p50/p75 across days per year. The statistic a
    share-based redistribution constraint (charge in window w >= share_w x
    daily total) would consume, and its day-to-day dispersion.
(C) SOC TRAJECTORY — per (year, hod): RTD SOC hod-mean ÷ EIA-860 monthly
    fleet energy MWh (LESR basis vs fleet basis disclosed), the hod-6 trough
    and hod-15 peak, and the implied overnight rebuild energy — the statistic
    an AS-obligation SOC-trajectory term would consume.
(D) SECOND-CYCLE SCALING — overnight (hod 0-5) RTD charge per year, absolute
    and ÷ fleet MWh; the overnight charge-rate hod profile as frac of fleet
    MW — does the second cycle scale with the fleet (forward story) or is it
    a fixed-MW conduct?
(E) RD-BOOK PROFILE — IFM RD award ÷ fleet MW per hod, per year — stability
    of the reg-down positioning that drives the RT-added charge (channel b).

Sources (all committed raw; no model output in any statistic):
  data/raw/storage-as-awards/CAISO/storage-report-*.xlsx (market_output,
  LESR only — the caiso-98/99/100 basis; HYBD excluded),
  EIA-860 monthly battery fleet via market_sim.model.storage
  .load_eia860_storage (PS excluded; the caiso-99 envelope denominator),
  actual_lmp_hourly_CAISO.parquet (window lambda context only).

Clock: TRADE_DATE+HOUR are prevailing-Pacific hour-ending physical-hour
labels (storage_as_awards.caiso intake, verified 2023-2025), so hod = HOUR-1,
fall-back 25th hour and Feb-29 dropped (model 8760 calendar) — the
_caiso102_charge_channels convention. NOT the EIA-930 filled-frame family
(issue #2562 does not touch this basis).

Usage:
  python scripts/probes/_caiso103_alloc_stats.py [--cache <parquet>]
--cache points at a pre-parsed concat of the market_output sheets; without it
the xlsx are parsed (~5 min).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _caiso102_charge_channels import (  # noqa: E402
    WINDOWS,
    actual_lmp,
    hourly_pivot,
    load_market_output,
    wmean,
)

YEARS = (2023, 2024, 2025)
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def monthly_fleet(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(12,) installed CAISO battery MW and MWh per month (PS excluded).

    The caiso-99 envelope denominator basis (`derive_caiso_storage_shape
    .monthly_battery_fleet_mw`), extended with the energy cap for the SOC
    normalization.
    """
    from market_sim.config.paths import set_eia860_vintage
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.model.storage import load_eia860_storage

    set_eia860_vintage(None)
    cfg = ScenarioConfig(mode="backcast", storage_vintage_ramp=True)
    units = load_eia860_storage("CAISO", year, cfg)
    mw = np.zeros(12)
    mwh = np.zeros(12)
    for u in units:
        if u.tech_name == "pumped_storage":
            continue
        prof = np.array(
            u.monthly_power_mw
            if u.monthly_power_mw is not None
            else [u.power_cap_mw] * 12,
            dtype=float,
        )
        mw += prof
        # energy scales with the same COD profile (duration fixed per unit)
        dur = u.energy_cap_mwh / u.power_cap_mw if u.power_cap_mw > 0 else 0.0
        mwh += prof * dur
    return mw, mwh


def day_grids(p: pd.DataFrame, year: int) -> dict[str, np.ndarray]:
    """(365, 24) grids of the columns the stats consume, zero-filled."""
    py = p[p.TRADE_DATE.dt.year == year].copy()
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[(days.month != 2) | (days.day != 29)]
    idx = pd.MultiIndex.from_product([days, range(24)], names=["TRADE_DATE", "hod"])
    py = py.set_index(["TRADE_DATE", "hod"]).reindex(idx).fillna(0.0).reset_index()

    def grid(col: str) -> np.ndarray:
        return (
            py[col].to_numpy(dtype=float).reshape(len(days), 24)
            if col in py
            else np.zeros((len(days), 24))
        )

    return {
        "chg_ifm": np.clip(-grid("IFM_EN"), 0.0, None),
        "chg_rtd": np.clip(-grid("RTD_EN"), 0.0, None),
        "soc_rtd": grid("RTD_SOC"),
        "rd_ifm": grid("IFM_RD"),
        "month_of_day": np.array([d.month - 1 for d in days]),
    }


def main() -> int:
    cache = None
    args = sys.argv[1:]
    if "--cache" in args:
        cache = Path(args[args.index("--cache") + 1])
    p = hourly_pivot(load_market_output(cache))
    p["TRADE_DATE"] = pd.to_datetime(p["TRADE_DATE"])

    shapes = {}  # year -> (24,) mean fleet-normalized IFM charge rate
    for year in YEARS:
        g = day_grids(p, year)
        mw, mwh = monthly_fleet(year)
        fleet_d = mw[g["month_of_day"]][:, None]  # (365,1) MW
        fleet_e_d = mwh[g["month_of_day"]][:, None]  # (365,1) MWh
        lmps = actual_lmp(year)

        print(
            f"\n===== {year} (fleet Jan {mw[0]:.0f} -> Dec {mw[-1]:.0f} MW, "
            f"{mwh[0] / 1e3:.1f} -> {mwh[-1] / 1e3:.1f} GWh) ====="
        )

        # -- (A) DA-allocation hod profile (fleet-normalized) ---------------
        rate = g["chg_ifm"] / fleet_d  # (365,24) frac of fleet MW
        shapes[year] = rate.mean(axis=0)
        ann = g["chg_ifm"].sum()
        print(
            "(A) IFM charge, fleet-normalized rate by hod "
            "(mean | p25/p50/p75 across days; hod-share of annual):"
        )
        for h in range(24):
            q = np.quantile(rate[:, h], [0.25, 0.5, 0.75])
            print(
                f"    hod {h:2d}: {rate[:, h].mean():.4f} | "
                f"{q[0]:.4f}/{q[1]:.4f}/{q[2]:.4f} | "
                f"share {g['chg_ifm'][:, h].sum() / ann:.4f}"
            )

        # -- (B) window shares of the day's IFM charge ----------------------
        daily = g["chg_ifm"].sum(axis=1)
        ok = daily > 1.0  # skip empty report days
        print("(B) window share of daily IFM charge (p25/p50/p75 across days):")
        for wname, hods in WINDOWS.items():
            s = g["chg_ifm"][ok][:, list(hods)].sum(axis=1) / daily[ok]
            q = np.quantile(s, [0.25, 0.5, 0.75])
            lam_da = wmean(lmps["da"][:, list(hods)], g["chg_ifm"][:, list(hods)])
            print(
                f"    {wname:16s}: {q[0]:.3f}/{q[1]:.3f}/{q[2]:.3f}"
                f"  (chg-wtd DA lam {lam_da:6.1f})"
            )

        # -- (C) SOC trajectory (normalized by fleet MWh) -------------------
        socn = (g["soc_rtd"] / fleet_e_d).mean(axis=0)
        trough_h, peak_h = int(np.argmin(socn)), int(np.argmax(socn))
        rebuild = float((g["soc_rtd"][:, 10] - g["soc_rtd"][:, trough_h]).mean())
        print("(C) RTD SOC hod-mean / fleet MWh: " + " ".join(f"{v:.3f}" for v in socn))
        print(
            f"    trough hod {trough_h} ({socn[trough_h]:.3f}), "
            f"peak hod {peak_h} ({socn[peak_h]:.3f}); "
            f"mean trough->hod10 rebuild {rebuild:.0f} MWh/day"
        )

        # -- (D) second-cycle scaling ---------------------------------------
        on = list(WINDOWS["overnight(0-5)"])
        on_twh = g["chg_rtd"][:, on].sum() / 1e6
        on_ifm_twh = g["chg_ifm"][:, on].sum() / 1e6
        print(
            f"(D) overnight RTD chg {on_twh:.3f} TWh (IFM {on_ifm_twh:.3f}) "
            f"| / fleet-MWh-yr {on_twh * 1e6 / (mwh.mean() * 365):.3f} "
            f"| rate profile (frac fleet MW): "
            + "/".join(f"{(g['chg_rtd'][:, h] / fleet_d[:, 0]).mean():.4f}" for h in on)
        )

        # -- (E) RD-book profile (fleet-normalized) -------------------------
        rdn = (g["rd_ifm"] / fleet_d).mean(axis=0)
        print(
            "(E) IFM RD award / fleet MW by window: "
            + " ".join(f"{rdn[list(h)].mean():.4f}" for h in WINDOWS.values())
        )

    # -- cross-year stability of the (A) shape ------------------------------
    print("\n(A) cross-year stability of the normalized IFM allocation shape:")
    ys = list(shapes)
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            r = float(np.corrcoef(shapes[ys[i]], shapes[ys[j]])[0, 1])
            print(f"    r({ys[i]},{ys[j]}) = {r:.3f}")
    arr = np.stack([shapes[y] for y in ys])
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = np.where(arr.mean(0) > 1e-4, arr.std(0) / arr.mean(0), np.nan)
    print(
        "    per-hod CV (mean-normalized): "
        + " ".join(f"{v:.2f}" if np.isfinite(v) else "--" for v in cv)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
