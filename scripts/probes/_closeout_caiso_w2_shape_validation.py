"""Close-out CAISO w2, phase 0 (ZERO LP): validate the formula-hub shape on PRINTED hours.

The R-CAISO-18 formula prices each WECC hub as ``gas_state(month) × HR ×
shape``. In the printed years the measured hub exists, so the two candidate
shape drivers can be tested against it out of the fold:

* ``proxy`` — the incumbent ``caiso_hub_load_shape`` (CISO net load for DSW,
  CISO gross load for PNW; clock-repaired frame, as the keeper solves);
* ``own``   — the corridor's own BAs (``spec.CAISO_CORRIDOR_DIBA``; net for DSW,
  gross for PNW), EIA-930 BALANCE archive.

Pre-fixed bar (FINDING §2, written before this ran): per corridor, ``own`` beats
``proxy`` on BOTH the hourly Pearson r of formula vs measured hub AND the RMSE
of the unit-mean hour-of-day profile, in >= 3 of the 4 printed years 2022-2025.
2021 May-Dec is reported, not gated. A corridor that fails is excluded.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w2_shape_validation.py [--out PATH]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia930.envelopes import measured_intertie_hub_price_raw
from market_sim.data.eia930.frames import (
    _eia_hourly_frame_filled,
    set_caiso_eia930_clock_repair,
)
from market_sim.data.fuel.electric_power import (
    state_electric_power_monthly_gas,
    state_electric_power_monthly_gas_eia923,
)
from market_sim.data.neighbor_price import caiso_hub_load_shape
from market_sim.model.interchange.spec import (
    CAISO_CORRIDOR_DIBA,
    CAISO_INTERTIE_HUB_GAS_STATE,
    CAISO_PER_HUB_NEIGHBORS,
)

ROOT = Path(__file__).resolve().parents[2]
BAL = ROOT / "data/raw/eia-930"
T = 8760
HOD = np.arange(T) % 24
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
YEARS = (2021, 2022, 2023, 2024, 2025)
GATED = (2022, 2023, 2024, 2025)


def own_ba_driver(zone: str, kind: str, year: int) -> np.ndarray:
    """Summed driver (gross or net load) of a corridor's own BAs on the CISO model clock."""
    bas = sorted(b for b, c in CAISO_CORRIDOR_DIBA.items() if c == zone and b != "CEN")
    frames = [
        pd.read_parquet(p)
        for y, h in ((year, "Jan_Jun"), (year, "Jul_Dec"), (year + 1, "Jan_Jun"))
        if (p := BAL / f"EIA930_BALANCE_{y}_{h}.parquet").exists()
    ]
    b = pd.concat(frames)
    b = b[b["Balancing Authority"].isin(bas)].copy()
    b["utc"] = pd.to_datetime(
        b["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p"
    )
    v = pd.to_numeric(b["Demand (MW) (Adjusted)"], errors="coerce")
    if kind == "net":
        for col in ("Solar", "Wind"):
            cols = [
                c
                for c in b.columns
                if c.startswith(f"Net Generation (MW) from {col}")
                and "(" not in c[len("Net Generation (MW) from ") :]
            ]
            v = v - b[cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum(
                axis=1
            )
    b["v"] = v
    piv = b.pivot_table(
        index="utc", columns="Balancing Authority", values="v", aggfunc="sum"
    )
    s = piv.interpolate(limit=6).sum(axis=1, min_count=len(bas))
    utc = pd.DatetimeIndex(
        _eia_hourly_frame_filled("CISO", year)["UTC time"]
    ).tz_localize(None)
    return s.reindex(utc).interpolate().bfill().ffill().to_numpy(dtype=float)[:T]


def hod_profile(x: np.ndarray, sel: np.ndarray) -> np.ndarray:
    """Unit-mean hour-of-day profile over the selected hours."""
    p = np.array([np.nanmean(x[sel & (HOD == h)]) for h in range(24)])
    return p / p.mean()


def score(zone: str, year: int) -> dict:
    """Formula-vs-measured skill of the proxy and own-BA shapes for one corridor-year."""
    spec = CAISO_PER_HUB_NEIGHBORS[zone]
    meas = measured_intertie_hub_price_raw("CAISO", year, T, spec.hub)
    if meas is None:
        return {"printed_hours": 0}
    state = CAISO_INTERTIE_HUB_GAS_STATE[spec.hub]
    gas = state_electric_power_monthly_gas(state, year)
    rebuilt = state_electric_power_monthly_gas_eia923(state, year)
    if gas is None:
        gas = rebuilt
    elif rebuilt is not None:
        gas = np.where(np.isfinite(gas), gas, rebuilt)
    base = gas[MONTH - 1] * spec.marginal_heat_rate
    proxy = base * caiso_hub_load_shape(spec, year, T)
    drv = own_ba_driver(zone, spec.load_shape_kind, year)
    own = base * np.clip(drv / drv.mean(), 0.05, None) ** spec.load_shape_exponent
    sel = np.isfinite(meas) & np.isfinite(proxy) & np.isfinite(own)
    pm = hod_profile(meas, sel)
    out = {"printed_hours": int(sel.sum())}
    for name, f in (("proxy", proxy), ("own", own)):
        out[name] = {
            "r_hourly": float(np.corrcoef(f[sel], meas[sel])[0, 1]),
            "hod_rmse": float(np.sqrt(np.mean((hod_profile(f, sel) - pm) ** 2))),
            "hod_profile": [round(v, 3) for v in hod_profile(f, sel)],
        }
        # within-day skill: demean each day so the monthly gas level does not dominate r
        day = np.arange(T) // 24
        dm = pd.Series(meas).where(sel).groupby(day).transform("mean").to_numpy()
        df = pd.Series(f).where(sel).groupby(day).transform("mean").to_numpy()
        out[name]["r_within_day"] = float(
            np.corrcoef((f - df)[sel], (meas - dm)[sel])[0, 1]
        )
    out["measured_hod_profile"] = [round(v, 3) for v in pm]
    out["own_wins"] = bool(
        out["own"]["r_hourly"] > out["proxy"]["r_hourly"]
        and out["own"]["hod_rmse"] < out["proxy"]["hod_rmse"]
    )
    return out


def main() -> None:
    """Score both corridors over the printed years and apply the pre-fixed bar."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(
            ROOT / "docs/records/caiso/closeout-caiso-w2/_shape_validation.json"
        ),
    )
    a = ap.parse_args()
    set_caiso_eia930_clock_repair(True)
    res = {}
    for zone in ("WECC_DSW", "WECC_PNW"):
        res[zone] = {str(y): score(zone, y) for y in YEARS}
        wins = sum(res[zone][str(y)].get("own_wins", False) for y in GATED)
        res[zone]["gate"] = {"wins_2022_2025": wins, "pass": wins >= 3}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    for zone, r in res.items():
        print(zone, r["gate"])
        for y in YEARS:
            s = r[str(y)]
            if not s.get("printed_hours"):
                print(" ", y, "no print")
                continue
            print(
                " ",
                y,
                s["printed_hours"],
                "proxy r=%.3f rwd=%.3f rmse=%.3f"
                % (
                    s["proxy"]["r_hourly"],
                    s["proxy"]["r_within_day"],
                    s["proxy"]["hod_rmse"],
                ),
                "| own r=%.3f rwd=%.3f rmse=%.3f"
                % (
                    s["own"]["r_hourly"],
                    s["own"]["r_within_day"],
                    s["own"]["hod_rmse"],
                ),
                "win" if s["own_wins"] else "LOSE",
            )


if __name__ == "__main__":
    main()
