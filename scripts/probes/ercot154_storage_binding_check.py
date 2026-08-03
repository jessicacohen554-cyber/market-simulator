"""ERCOT-154 Phase 1b — confront the measured ESR offer surface with the keeper.

Phase 1a (``ercot154_storage_offer_surface.py``) measured what the real ERCOT
battery fleet OFFERS. This probe asks the two questions that decide whether an
arm is worth a solve, both answered on COMMITTED bytes only -- the ercot150b
keeper's own hourly sidecars -- with no LP built and no year solved:

1. **Is it inert?** How much of the keeper's storage discharge happens at a
   model price BELOW the measured offer level for that hour's cell. That MWh
   is what a measured offer would withhold; if it is ~0 the mechanism is inert
   by construction and must not be armed (the caiso-144 / ERCOT-146
   inert-by-wiring precedent -- an A/B that cannot move is not evidence).
2. **Is the sign right?** Where the withheld MWh sits in the diurnal profile.
   The ERCOT-153 object is a PEAK-HALF amplitude deficit; withholding that
   lands in the trough would raise the trough and make amplitude worse, which
   is a pre-registered kill, not a surprise to be discovered after a solve.

It also reads the keeper's May-2024 shoulder over-amplification (ERCOT-153
cell 1.295) directly, since the pre-registered guard is that the arm must not
worsen an already-over-amplified cell.

Usage::

    python scripts/probes/ercot154_storage_binding_check.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    NETLOAD_PCT_EDGES,
    _netload_pct,
)
from ercot154_storage_offer_surface import HOUR_BLOCKS  # noqa: E402

BUNDLE = REPO / "results/calibration/ercot150_zonalanchor_B/hourly"
SURFACE = REPO / "results/calibration/ercot154_storage_offer_surface.json"
DEFAULT_OUT = REPO / "results/calibration/ercot154_storage_binding_check.json"

# The keeper's incumbent flat discharge adder ($/MWh), DOF-ledger
# `battery_dispatch_adder`, identification: residual. The measured surface
# would REPLACE this value (rule 19), never stack on it.
KEEPER_BATTERY_ADDER = 10.0

# Ladder rung index used as the candidate single-price level. Index 1 = p30 of
# LADDER_QUANTILES, the ONLY rung the Phase-1a year-pair test identifies
# (median ratio 0.969, rel IQR 0.143; p50 drifts to 0.68 and p70 collapses to
# 0.11). Selected on cross-year stability -- a criterion computed entirely
# from the SCED corpus and blind to any model residual (rule 23).
RUNG_INDEX = 1
RUNG_NAME = "p30"


def _system_price(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Load-weighted system price and total demand, per hour, from the keeper."""
    df = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    dem = df.groupby("hour")["demand"].sum().reindex(range(8760))
    lw = ((df["price"] * df["demand"]).groupby(df["hour"]).sum() / dem).reindex(
        range(8760)
    )
    return lw.to_numpy(float), dem.to_numpy(float)


def _storage(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Keeper P1 storage charge/discharge MW per hour (all techs summed)."""
    df = pd.read_parquet(BUNDLE / f"storage_{year}.parquet")
    df = df[df["pass"] == "P1"]
    g = df.groupby("hour")[["charge_mw", "discharge_mw"]].sum().reindex(range(8760))
    return (
        g["discharge_mw"].to_numpy(float),
        g["charge_mw"].to_numpy(float),
    )


def check_year(year: int, surface: dict) -> dict:
    """Confront one keeper year with the measured surface for that year."""
    price, _dem = _system_price(year)
    dis, chg = _storage(year)

    pct = _netload_pct(year)
    hour_bin = np.searchsorted(np.asarray(NETLOAD_PCT_EDGES), pct, side="right")
    hod = np.tile(np.arange(24), 365)
    block_of_hod = {h: name for name, hrs in HOUR_BLOCKS for h in hrs}
    block = np.array([block_of_hod[h] for h in hod])

    # Measured level per hour. A year with no corpus (2023) and any cell the
    # corpus cannot populate carry NaN -- never a pooled fallback (rule 13).
    cells = (surface.get("years", {}).get(str(year), {}) or {}).get("cells", {})
    level = np.full(8760, np.nan)
    for t in range(8760):
        c = cells.get(f"{block[t]}|bin{hour_bin[t]}")
        if c and c["intervals"] > 0:
            v = c["usd"][RUNG_INDEX]
            if v == v:
                level[t] = v

    covered = np.isfinite(level)
    binding = covered & (dis > 0) & (price < level)
    total_dis = float(dis.sum())

    rows = []
    for name, hrs in HOUR_BLOCKS:
        m = np.isin(hod, hrs)
        d_blk = float(dis[m].sum())
        rows.append(
            {
                "block": name,
                "discharge_gwh": round(d_blk / 1e3, 1),
                "share_of_annual_discharge": round(d_blk / max(total_dis, 1e-9), 4),
                "covered_share_of_hours": round(float(covered[m].mean()), 3),
                "withheld_gwh": round(float(dis[m & binding].sum()) / 1e3, 1),
                "withheld_share_of_block": round(
                    float(dis[m & binding].sum()) / max(d_blk, 1e-9), 4
                ),
                "mean_model_price_when_discharging": round(
                    float(np.average(price[m & (dis > 0)], weights=dis[m & (dis > 0)]))
                    if (m & (dis > 0)).any()
                    else float("nan"),
                    2,
                ),
                "mean_measured_level": round(
                    float(np.nanmean(level[m])) if covered[m].any() else float("nan"), 2
                ),
            }
        )

    # How often storage is plausibly the marginal (price-setting) unit today:
    # the model price sits within $1 of the incumbent flat offer while the
    # unit is discharging. If this is ~0 the price effect must come from
    # DISPLACEMENT (a dearer thermal unit clears instead), not from storage
    # setting the dual directly.
    disch = dis > 0
    near = disch & (np.abs(price - KEEPER_BATTERY_ADDER) <= 1.0)
    return {
        "annual_discharge_gwh": round(total_dis / 1e3, 1),
        "annual_charge_gwh": round(float(chg.sum()) / 1e3, 1),
        "hours_discharging": int(disch.sum()),
        "hours_storage_near_marginal": int(near.sum()),
        "covered_share_of_hours": round(float(covered.mean()), 3),
        "withheld_gwh": round(float(dis[binding].sum()) / 1e3, 1),
        "withheld_share_of_annual_discharge": round(
            float(dis[binding].sum()) / max(total_dis, 1e-9), 4
        ),
        "by_block": rows,
    }


def supply_curve_slope(year: int) -> dict:
    """Measure the keeper's own EVENING supply-curve slope ($/MWh per GW).

    This is the question the withholding number cannot answer on its own.
    Withholding storage only raises the price if the dispatchable stack behind
    it is STEEP at the evening operating point; if it is flat, the withheld MW
    is replaced at almost the same cost and the amplitude does not move.

    Measured MATCHED, within each (month x hour-of-day) cell, so the slope is
    not contaminated by seasonal load/outage/renewable heterogeneity: an OLS
    of the keeper's load-weighted price on the residual demand the dispatchable
    stack must serve (demand - wind - solar - hydro - nuclear - discharge +
    charge). Reported as the distribution over cells, never a single fit.
    """
    sysd = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    lw = (
        (
            (sysd["price"] * sysd["demand"]).groupby(sysd["hour"]).sum()
            / sysd.groupby("hour")["demand"].sum()
        )
        .reindex(range(8760))
        .to_numpy(float)
    )
    dem = sysd.groupby("hour")["demand"].sum().reindex(range(8760)).to_numpy(float)

    cls = pd.read_parquet(BUNDLE / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    piv = (
        cls.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(8760))
        .fillna(0.0)
    )
    dis, chg = _storage(year)
    nondisp = piv[["wind", "solar", "hydro", "nuclear"]].sum(axis=1).to_numpy(float)
    resid = dem - nondisp - dis + chg

    hod = np.tile(np.arange(24), 365)
    doy = np.repeat(np.arange(365), 24)
    month_start = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])
    mon = np.searchsorted(month_start, doy, side="right") - 1
    evening = [
        h for name, hrs in HOUR_BLOCKS if name.startswith("evening") for h in hrs
    ]

    slopes: list[float] = []
    for m in range(12):
        for h in evening:
            k = (mon == m) & (hod == h)
            # A cell needs enough hours and enough spread in residual demand
            # for a slope to mean anything; both bars are disclosed.
            if k.sum() < 20 or resid[k].std() < 200.0:
                continue
            slopes.append(float(np.polyfit(resid[k], lw[k], 1)[0]))
    arr = np.array(slopes)
    ev_mask = np.isin(hod, evening)
    mean_dis = float(dis[ev_mask].mean())
    if not len(arr):
        return {"cells": 0}
    med = float(np.median(arr))
    p90 = float(np.percentile(arr, 90))
    return {
        "cells": int(len(arr)),
        "median_usd_per_mwh_per_gw": round(med * 1e3, 3),
        "p25_usd_per_mwh_per_gw": round(float(np.percentile(arr, 25)) * 1e3, 3),
        "p75_usd_per_mwh_per_gw": round(float(np.percentile(arr, 75)) * 1e3, 3),
        "p90_usd_per_mwh_per_gw": round(p90 * 1e3, 3),
        "mean_evening_discharge_mw": round(mean_dis, 1),
        "price_gain_if_all_evening_storage_withheld_median_cell": round(
            med * mean_dis, 2
        ),
        "price_gain_if_all_evening_storage_withheld_p90_cell": round(p90 * mean_dis, 2),
        "evening_price_mean": round(float(lw[ev_mask].mean()), 2),
        "evening_price_median": round(float(np.median(lw[ev_mask])), 2),
        "evening_hours_above_66_usd_share": round(
            float((lw[ev_mask] > 66.0).mean()), 4
        ),
        "evening_thermal_mean_mw": round(
            float(
                piv[
                    [
                        "CC_CHP",
                        "CC_REGULAR",
                        "COAL_LIGNITE",
                        "COAL_PRB",
                        "CT_CHP",
                        "CT_PEAKER",
                        "ST_CHP",
                        "ST_GAS",
                        "oil",
                        "OTHER",
                        "biomass",
                    ]
                ]
                .sum(axis=1)
                .to_numpy(float)[ev_mask]
                .mean()
            ),
            0,
        ),
    }


def eia930_volume_benchmark(year: int) -> dict:
    """Measured ERCOT battery discharge (EIA-930 ``NG: BAT``) for the year.

    A pre-registration GUARD only -- never an input and never a fitting
    target. (The incumbent ``battery_dispatch_adder`` was tuned against this
    very benchmark, which is why it carries ``identification: residual``; this
    probe reads it to check whether an arm would break a measured quantity,
    not to set one.) Reporting coverage matters: the ERCOT battery series
    only begins 2024-10-23, so 2023/2024 cannot carry the guard.
    """
    path = REPO / "data/raw/eia-930-hourly/ERCO hourly.parquet"
    df = pd.read_parquet(path, columns=["UTC time", "NG: BAT"])
    std = pd.DatetimeIndex(df["UTC time"]).tz_localize("UTC").tz_convert("Etc/GMT+6")
    bat = pd.to_numeric(df["NG: BAT"], errors="coerce")
    m = np.asarray(std.year == year)
    b = bat[m]
    reported = int(b.notna().sum())
    return {
        "reported_hours": reported,
        "total_hours": int(m.sum()),
        "coverage": round(reported / max(int(m.sum()), 1), 3),
        "measured_discharge_gwh": round(float(b.clip(lower=0).sum()) / 1e3, 1)
        if reported
        else None,
        "usable_as_guard": reported >= 8000,
    }


def may_shoulder_guard(year: int) -> dict:
    """Read the May over-amplified cell the arm is pre-registered not to worsen."""
    price, _ = _system_price(year)
    dis, _c = _storage(year)
    hod = np.tile(np.arange(24), 365)
    doy = np.repeat(np.arange(365), 24)
    # May = day-of-year 120..150 on the model's non-leap clock.
    may = (doy >= 120) & (doy < 151)
    prof = np.array([price[may & (hod == h)].mean() for h in range(24)])
    return {
        "may_mean_price": round(float(price[may].mean()), 2),
        "may_amplitude": round(float(prof.max() - prof.min()), 2),
        "may_peak_hour": int(np.argmax(prof)),
        "may_discharge_gwh": round(float(dis[may].sum()) / 1e3, 1),
    }


def main() -> None:
    """Run the confrontation for 2023-2025 and write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    surface = json.loads(SURFACE.read_text())
    out: dict = {
        "_provenance": {
            "session": "ERCOT-154 Phase 1b (no LP built, no year solved)",
            "keeper": "2026-08-02-ercot150b-zonal-anchor",
            "inputs": [
                "results/calibration/ercot150_zonalanchor_B/hourly/"
                "{system,storage}_<year>.parquet (committed keeper sidecars)",
                "results/calibration/ercot154_storage_offer_surface.json",
            ],
            "rung": f"{RUNG_NAME} (index {RUNG_INDEX}) — the only rung the "
            "Phase-1a year-pair test identifies",
            "keeper_battery_dispatch_adder": KEEPER_BATTERY_ADDER,
            "note": (
                "2023 carries NO measured surface (no 2023 SCED corpus on "
                "disk; re-upload owner-declined 2026-08-02), so its coverage "
                "is 0 by construction and it is reported for contrast only"
            ),
        },
        "years": {},
        "may_shoulder_guard": {},
        "supply_curve_slope": {},
        "eia930_volume_benchmark": {},
    }
    for y in (2023, 2024, 2025):
        out["years"][str(y)] = check_year(y, surface)
        out["may_shoulder_guard"][str(y)] = may_shoulder_guard(y)
        out["supply_curve_slope"][str(y)] = supply_curve_slope(y)
        out["eia930_volume_benchmark"][str(y)] = eia930_volume_benchmark(y)
        r = out["years"][str(y)]
        s = out["supply_curve_slope"][str(y)]
        v = out["eia930_volume_benchmark"][str(y)]
        print(
            f"{y}: discharge {r['annual_discharge_gwh']} GWh over "
            f"{r['hours_discharging']} h; cell coverage "
            f"{r['covered_share_of_hours']:.1%}; withheld "
            f"{r['withheld_gwh']} GWh "
            f"({r['withheld_share_of_annual_discharge']:.1%})"
        )
        print(
            f"      evening slope {s.get('median_usd_per_mwh_per_gw')} $/MWh per GW "
            f"-> withholding ALL evening storage buys "
            f"${s.get('price_gain_if_all_evening_storage_withheld_median_cell')}; "
            f"measured discharge {v['measured_discharge_gwh']} GWh "
            f"(coverage {v['coverage']:.0%}, guard usable: {v['usable_as_guard']})"
        )
    args.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
