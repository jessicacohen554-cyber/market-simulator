"""Close-out CAISO w2, phase 0 (ZERO LP): the DSW formula-hub diurnal shape.

Plan ``docs/backcast-closeout-plan-2026-10.md`` §3.7, "new zero-parameter lever
for later": in the hours the R-CAISO-18 unprinted-year branch prices Palo Verde
on the measured-gas formula (all of 2019-2020, Jan-Apr 2021), the hub is

    gas_AZ(month) × HR_DSW × (CISO net load / mean)

so its diurnal SHAPE comes from CAISO's own net load, a proxy. The candidate
replaces the proxy with the net load of the DSW corridor's own balancing
authorities (``spec.CAISO_CORRIDOR_DIBA`` → WECC_DSW, the declared corridor map;
EIA-930 BALANCE archive, committed). Level is preserved (both shapes are
normalised to unit mean); only the hour-by-hour shape moves.

Reads only committed artifacts:

* the keeper bundle ``results/calibration/closeout_caiso_w1_a2_span`` P1
  ``unit_marginal_<y>`` / ``system_<y>`` sidecars;
* ``data/raw/eia-930/EIA930_BALANCE_<y>_<half>.parquet`` (DSW BAs);
* the live formula code (``caiso_hub_measured_gas_reference_price``,
  ``measured_intertie_hub_unprinted_year_mask``) for the incumbent hub.

First-order reach (fixed duals): each formula-priced WECC_DSW tranche's P1
offer moves by Δhub(t); a tranche whose offer crosses the WECC_DSW dual adds
(cap − mw) or drops mw. Corridor-binding hours (|λ_DSW − λ_SP15_rest| > $1)
are reported separately: there an added DSW MW cannot reach CAISO.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w2_dsw_shape.py [--out PATH]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia930.envelopes import measured_intertie_hub_unprinted_year_mask
from market_sim.data.eia930.frames import (
    _eia_hourly_frame_filled,
    set_caiso_eia930_clock_repair,
)
from market_sim.data.neighbor_price import (
    caiso_hub_load_shape,
    caiso_hub_measured_gas_reference_price,
)
from market_sim.model.interchange.spec import (
    CAISO_CORRIDOR_DIBA,
    CAISO_PER_HUB_NEIGHBORS,
)

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results/calibration/closeout_caiso_w1_a2_span/hourly"
BAL = ROOT / "data/raw/eia-930"
YEARS = (2019, 2020, 2021)
T = 8760
DSW_BAS = sorted(
    b for b, c in CAISO_CORRIDOR_DIBA.items() if c == "WECC_DSW" and b != "CEN"
)
SPEC = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
NOT_HUB_PRICED = ("DSW_solar_PV", "export_PALOVRDE")
BIND_TOL = 1.0
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
HOD = np.arange(T) % 24


def dsw_net_load(year: int) -> np.ndarray:
    """DSW corridor BAs' summed net load (Demand adj − solar − wind) on the CISO model clock."""
    frames = []
    for half in ("Jan_Jun", "Jul_Dec"):
        for y in (year, year + 1) if half == "Jan_Jun" else (year,):
            p = BAL / f"EIA930_BALANCE_{y}_{half}.parquet"
            if p.exists():
                frames.append(pd.read_parquet(p))
    b = pd.concat(frames)
    b = b[b["Balancing Authority"].isin(DSW_BAS)].copy()
    b["utc"] = pd.to_datetime(
        b["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p"
    )
    num = lambda c: pd.to_numeric(b[c], errors="coerce")  # noqa: E731
    b["net"] = (
        num("Demand (MW) (Adjusted)")
        - num("Net Generation (MW) from Solar").fillna(0.0)
        - num("Net Generation (MW) from Wind").fillna(0.0)
    )
    piv = b.pivot_table(
        index="utc", columns="Balancing Authority", values="net", aggfunc="sum"
    )
    piv = piv.interpolate(limit=6).sum(axis=1, min_count=len(DSW_BAS))
    ciso = _eia_hourly_frame_filled("CISO", year)
    utc = pd.DatetimeIndex(ciso["UTC time"]).tz_localize(None)
    out = piv.reindex(utc).interpolate().bfill().ffill().to_numpy(dtype=float)
    assert out.shape[0] >= T, out.shape
    return out[:T]


def shape_from(driver: np.ndarray) -> np.ndarray:
    """Same normalisation as ``caiso_hub_load_shape`` (unit mean, 0.05 floor, exponent)."""
    norm = np.clip(driver / driver.mean(), 0.05, None)
    return norm**SPEC.load_shape_exponent


def year_reach(year: int) -> dict:
    """Δhub and the first-order DSW volume reach for one fold year."""
    hub_old = caiso_hub_measured_gas_reference_price(
        SPEC, year, T, eia923_fallback=True
    )
    shp_old = caiso_hub_load_shape(SPEC, year, T)
    shp_new = shape_from(dsw_net_load(year))
    hub_new = hub_old / shp_old * shp_new
    mask = measured_intertie_hub_unprinted_year_mask(
        "CAISO", year, T, SPEC.hub, gap_fill_measured_dam=True
    )
    mask = np.zeros(T, bool) if mask is None else mask
    dhub = np.where(mask, hub_new - hub_old, 0.0)

    um = pd.read_parquet(
        BUNDLE / f"unit_marginal_{year}.parquet",
        columns=["unit_id", "zone", "hour", "mw", "cap_mw", "mc"],
    )
    um = um[um.zone.astype(str) == "WECC_DSW"]
    sysd = pd.read_parquet(
        BUNDLE / f"system_{year}.parquet", columns=["zone", "hour", "price"]
    )
    lam = (
        sysd[sysd.zone == "WECC_DSW"]
        .set_index("hour")["price"]
        .reindex(range(T))
        .to_numpy()
    )
    lam_sp = (
        sysd[sysd.zone == "SP15_rest"]
        .set_index("hour")["price"]
        .reindex(range(T))
        .to_numpy()
    )
    binding = np.abs(lam - lam_sp) > BIND_TOL

    rows = {}
    add = np.zeros(T)
    drop = np.zeros(T)
    check = {}
    for uid, g in um.groupby("unit_id", observed=True):
        name = str(uid)[len("WECC_DSW_") :]
        g = g.set_index("hour").reindex(range(T))
        mw, cap, mc = (g[c].to_numpy(dtype=float) for c in ("mw", "cap_mw", "mc"))
        if name in NOT_HUB_PRICED:
            rows[name] = {"twh": float(np.nansum(mw) / 1e6), "hub_priced": False}
            continue
        off = (mc - hub_old)[mask & np.isfinite(mc)]
        check[name] = {"mc_minus_hub_std": float(np.std(off)) if off.size else None}
        mc_new = mc + dhub
        a = np.where(mask & (mc_new < lam - 0.01) & (mw < cap - 1e-6), cap - mw, 0.0)
        d = np.where(mask & (mc_new > lam + 0.01) & (mw > 1e-6), mw, 0.0)
        add += np.nan_to_num(a)
        drop += np.nan_to_num(d)
        rows[name] = {
            "twh": float(np.nansum(mw) / 1e6),
            "add_twh": float(np.nansum(a) / 1e6),
            "drop_twh": float(np.nansum(d) / 1e6),
        }

    def agg(x, sel):
        return float(x[sel].sum() / 1e6)

    bands = {"h0_5": HOD <= 5, "h6_17": (HOD >= 6) & (HOD <= 17), "h18_23": HOD >= 18}
    by_hod_dhub = [
        float(np.mean(dhub[mask & (HOD == h)])) if (mask & (HOD == h)).any() else None
        for h in range(24)
    ]
    return {
        "unprinted_hours": int(mask.sum()),
        "dsw_bas": DSW_BAS,
        "hub_old_mean_masked": float(hub_old[mask].mean()) if mask.any() else None,
        "hub_new_mean_masked": float(hub_new[mask].mean()) if mask.any() else None,
        "shape_corr_old_new": float(np.corrcoef(shp_old, shp_new)[0, 1]),
        "dhub_by_hod": by_hod_dhub,
        "mc_offset_check": check,
        "tranches": rows,
        "first_order": {
            "add_twh": agg(add, slice(None)),
            "drop_twh": agg(drop, slice(None)),
            "net_twh": agg(add - drop, slice(None)),
            "net_twh_nonbinding": agg(np.where(binding, 0.0, add - drop), slice(None)),
            "net_by_band": {k: agg(add - drop, v) for k, v in bands.items()},
            "net_nonbinding_by_band": {
                k: agg(np.where(binding, 0.0, add - drop), v) for k, v in bands.items()
            },
            "binding_hours_masked": int((binding & mask).sum()),
        },
    }


def main() -> None:
    """Run the phase-0 reach for 2019-2021 and write the JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(ROOT / "docs/records/caiso/closeout-caiso-w2/_dsw_shape.json"),
    )
    a = ap.parse_args()
    # The keeper arms caiso_eia930_clock_repair (R-CAISO-13/17): the LP's
    # incumbent shape reads the clock-repaired CISO frame.
    set_caiso_eia930_clock_repair(True)
    res = {str(y): year_reach(y) for y in YEARS}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    for y, r in res.items():
        print(
            y,
            json.dumps(
                {
                    k: r[k]
                    for k in (
                        "unprinted_hours",
                        "hub_old_mean_masked",
                        "hub_new_mean_masked",
                        "shape_corr_old_new",
                    )
                }
            ),
        )
        print("  first_order", json.dumps(r["first_order"]))
        print("  tranches", json.dumps(r["tranches"]))
        print("  check", json.dumps(r["mc_offset_check"]))
        print(
            "  dhub_by_hod",
            [round(v, 2) if v is not None else None for v in r["dhub_by_hod"]],
        )


if __name__ == "__main__":
    main()
