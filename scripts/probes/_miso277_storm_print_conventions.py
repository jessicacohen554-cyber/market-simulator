#!/usr/bin/env python3
"""miso-277 phase 0 (zero LP): what each storm-print convention does to MISO Feb-2021 gas.

Prepares an OWNER QUESTION, not a solve. The owner declined miso-276's D1 arm
(daily delivered print, spike days passed through) because the $129.52 Chicago
Uri weekend print took the storm week to 334.8 vs ~141 actual. A successor needs
a storm-print convention that is NOT a fitted threshold. This probe measures,
on the keeper fleet (``fleet_only`` rebuild, keeper recipe), the Feb-2021 gas
price array under:

* ``keeper``  — EIA-923 monthly purchase level x calendar-normalized daily shape;
* ``d1``      — miso-276 as built (daily hub print + measured transport);
* ``burnw``   — the keeper's own per-row daily series rescaled so its
  HEAT-INPUT-WEIGHTED Feb mean (weights = the plant's own measured CAMPD daily
  gas heat input) equals the keeper row's calendar Feb mean. Zero fitted
  scalars: the 923 level is a purchase-weighted average over the MMBtu the
  plant actually bought/burned, so the consistent normalization weights by burn,
  not by calendar day;
* ``d1_south_hh`` — D1 with MISO-South on Henry Hub as the owner ruled (the
  as-built arm defaulted South to Chicago in 2019-2021: no hub-table row);
* ``d1_burnw`` — the D1 daily series rescaled the same way onto the keeper's
  923 level (daily SHAPE from the print, LEVEL from what was paid).

Also reports the cross-check that grounds the question: the burn-weighted Feb
mean of the D1 print series vs the 923 level each zone's fleet actually paid.
If the print's burn-weighted mean is far above the 923 level, the fleet did not
pay the print on the volumes it burned.

Usage::

    uv run python scripts/probes/_miso277_storm_print_conventions.py \
        --out results/calibration/_miso277_storm_print_conventions.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _miso276_winter_gas_footprint as fp  # noqa: E402

YEAR = 2021
MISO_STATES = (
    "AR",
    "IA",
    "IL",
    "IN",
    "KY",
    "LA",
    "MI",
    "MN",
    "MO",
    "MS",
    "ND",
    "SD",
    "TX",
    "WI",
    "MT",
)
GAS_FUEL = ("Pipeline Natural Gas", "Natural Gas")


def campd_daily_gas_heat(plants: set[int]) -> pd.DataFrame:
    """Daily gas heat input (MMBtu) per CAMPD facility for Feb 2021, fleet plants only."""
    frames = []
    for st in MISO_STATES:
        p = REPO / "data/raw/campd-unit-level" / f"{st}_{YEAR}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(
            p, columns=["facilityId", "date", "heatInput", "primaryFuelInfo"]
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["facilityId"].isin(plants) & d["primaryFuelInfo"].isin(GAS_FUEL)]
        d = d[(d["date"] >= f"{YEAR}-02-01") & (d["date"] < f"{YEAR}-03-01")]
        frames.append(d)
    d = pd.concat(frames)
    return d.groupby(["facilityId", "date"])["heatInput"].sum().unstack(fill_value=0.0)


def daily(arr: np.ndarray, feb: np.ndarray) -> np.ndarray:
    """(rows, 28) daily mean of the Feb hourly columns."""
    return arr[:, feb].reshape(arr.shape[0], 28, 24).mean(axis=2)


def burn_rescale(series: np.ndarray, level: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Rescale each row so its burn-weighted mean equals ``level`` (rows without burn keep calendar)."""
    wsum = w.sum(axis=1)
    wm = np.where(
        wsum > 0,
        (series * w).sum(axis=1) / np.where(wsum > 0, wsum, 1),
        series.mean(axis=1),
    )
    return series * (level / np.where(wm > 0, wm, 1))[:, None]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore
    from market_sim.data.fuel._shared import _month_index

    hh = _henry_hub_actual(_load_reference(), YEAR)
    f0, pmax, zi, zn, gas = fp.build(YEAR, hh, False)
    f1, _, _, _, _ = fp.build(YEAR, hh, True)
    # The as-built D1 maps a zone with no hub-table row for the year to Chicago
    # (``kind_by_zone.get(zn, "chicago")``); MISO-South has no row before 2022,
    # so in 2021 South took the Chicago print against the owner's ruling (South =
    # Henry Hub). ``d1_south_hh`` re-runs D1 with South mapped to Henry Hub.
    import market_sim.data.fuel.basis.miso as mb

    orig_kind = mb._miso_zone_hub_kind
    mb._miso_zone_hub_kind = lambda year, path=None: {
        **orig_kind(year, path),
        "MISO-South": "henry",
    }
    try:
        f2, _, _, _, _ = fp.build(YEAR, hh, True)
    finally:
        mb._miso_zone_hub_kind = orig_kind
    st = __import__("scripts.run_calibration", fromlist=["run_year"])
    fa = st.run_year(
        YEAR, "MISO", 8760, hh, {}, fleet_only=True, **fp.dec.recipe(YEAR, {})
    )["fleet_arrays"]
    plant = np.asarray(fa.plant_code).astype(int)

    feb = (_month_index(f0.shape[1]) + 1) == 2
    k0, k1, k2 = daily(f0, feb), daily(f1, feb), daily(f2, feb)
    heat = campd_daily_gas_heat(set(plant[gas].tolist()))
    days = pd.date_range(f"{YEAR}-02-01", periods=28, freq="D")
    heat = heat.reindex(columns=days, fill_value=0.0)
    w = np.zeros_like(k0)
    rows_with_burn = np.zeros(len(plant), bool)
    for i in np.where(gas)[0]:
        if plant[i] in heat.index:
            w[i] = heat.loc[plant[i]].to_numpy()
            rows_with_burn[i] = w[i].sum() > 0

    level = k0.mean(
        axis=1
    )  # keeper row's calendar Feb mean = 923 level (+ zonal increment)
    conv = {
        "keeper": k0,
        "d1": k1,
        "burnw": burn_rescale(k0, level, w),
        "d1_burnw": burn_rescale(k1, level, w),
        "d1_south_hh": k2,
        "d1_south_hh_burnw": burn_rescale(k2, level, w),
    }
    storm = np.asarray((days >= "2021-02-13") & (days < "2021-02-17"))
    out: dict = {"year": YEAR, "zones": {}, "system": {}, "coverage": {}}
    gw = gas & rows_with_burn
    out["coverage"] = {
        "gas_rows": int(gas.sum()),
        "gas_rows_with_campd_burn": int(gw.sum()),
        "gas_pmax_share_with_burn": round(float(pmax[gw].sum() / pmax[gas].sum()), 3),
    }

    def summarise(mask: np.ndarray) -> dict:
        cw = pmax[mask][:, None]
        rec = {}
        for name, s in conv.items():
            x = s[mask]
            rec[name] = {
                "feb_calendar": round(float((x * cw).sum() / (cw.sum() * 28)), 2),
                "storm_13_16": round(
                    float((x[:, storm] * cw).sum() / (cw.sum() * storm.sum())), 2
                ),
                "calm": round(
                    float((x[:, ~storm] * cw).sum() / (cw.sum() * (~storm).sum())), 2
                ),
                "burn_weighted": round(
                    float((x * w[mask]).sum() / max(w[mask].sum(), 1e-9)), 2
                ),
            }
        return rec

    for z, name in enumerate(zn):
        m = gas & (zi == z)
        if m.any():
            out["zones"][name] = summarise(m)
    out["system"] = summarise(gas)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["system"], indent=1), json.dumps(out["coverage"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
