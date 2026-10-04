"""Close-out CAISO w4, phase 0 (ZERO LP): ICE Palo Verde daily index as the unprinted formula's within-month day shape.

w3 (L2) multiplies the unprinted Palo Verde formula's monthly gas operand by the
CA Composite citygate within-month DAILY factor (month-mean preserving). The
candidate replaces that factor with the hub's OWN measured daily price: the
EIA-published ICE "Palo Verde Peak" daily index (single-day packages; a
multi-day weekend/holiday package prices each day it covers), as a
month-mean-preserving factor ICE(day) / mean_month(ICE). The monthly level stays
the formula's (AZ gas x HR 13 x CISO net-load shape), so no basis is fitted —
the R-CAISO-18 objection to ICE as a LEVEL does not apply to a ratio.

Gate, fixed before computing (desk status 2026-10-04): on printed days the
ICE-shaped formula beats the citygate-shaped (w3) formula against the measured
OASIS DAM Palo Verde DAILY mean on BOTH r and RMSE in >= 3 of 4 years
2022-2025. 2021 (May-Dec printed) is reported, not gated.

ICE workbooks: ``https://www.eia.gov/electricity/wholesale/xls/archive/ice_electric-<y>final.xlsx``
(scratch, ``--ice-dir``; not a committed data input at phase 0).

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w4_ice_validation.py --ice-dir DIR [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]

from market_sim.data.eia930.envelopes import measured_intertie_hub_price_raw  # noqa: E402
from market_sim.data.eia930.frames import set_caiso_eia930_clock_repair  # noqa: E402
from market_sim.data.fuel.hubs import caiso_citygate_daily_shape_factors  # noqa: E402
from market_sim.data.neighbor_price import caiso_hub_measured_gas_reference_price  # noqa: E402
from market_sim.model.interchange.spec import CAISO_PER_HUB_NEIGHBORS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
T = 8760
DAY = np.arange(T) // 24
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MON_OF_DAY = np.repeat(np.arange(1, 13), _DAYS)


def ice_daily(ice_dir: Path, year: int) -> np.ndarray:
    """365-day ICE Palo Verde Peak daily price (NaN where nothing prices the day; Feb 29 dropped)."""
    x = pd.read_excel(ice_dir / f"ice_electric-{year}final.xlsx")
    x = x[x["Price hub"] == "Palo Verde Peak"]
    s = pd.to_datetime(x["Delivery start date"])
    e = pd.to_datetime(x["Delivery \nend date"])
    p = x["Wtd avg price $/MWh"].astype(float).to_numpy()
    cal = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    cal = cal[~((cal.month == 2) & (cal.day == 29))]
    single = pd.Series(p[(s == e).to_numpy()], index=s[s == e]).groupby(level=0).mean()
    out = single.reindex(cal)
    for si, ei, pi in zip(s[s != e], e[s != e], p[(s != e).to_numpy()]):
        span = (cal >= si) & (cal <= ei)
        fill = span & out.isna().to_numpy()
        out[fill] = pi
    return out.to_numpy(float)


def ice_factor(ice_dir: Path, year: int) -> np.ndarray:
    """Hourly month-mean-preserving ICE daily factor (1.0 where unpriced)."""
    d = ice_daily(ice_dir, year)
    f = np.ones(365)
    for m in range(1, 13):
        sel = MON_OF_DAY == m
        mean = np.nanmean(d[sel])
        if np.isfinite(mean) and mean > 0:
            f[sel] = np.where(np.isfinite(d[sel]), d[sel] / mean, 1.0)
    return f[DAY]


def score(ice_dir: Path, year: int) -> dict:
    """Daily-mean r / RMSE of citygate-shaped (w3) vs ICE-shaped formula against the print."""
    spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
    w3 = caiso_hub_measured_gas_reference_price(
        spec, year, T, eia923_fallback=True, daily_gas_shape=True
    )
    meas = measured_intertie_hub_price_raw("CAISO", year, T, spec.hub)
    if w3 is None or meas is None:
        return {"days": 0}
    cand = w3 / caiso_citygate_daily_shape_factors(year, T) * ice_factor(ice_dir, year)
    sel = np.isfinite(meas) & np.isfinite(w3)
    days = np.unique(DAY[sel])
    dm = np.array([meas[sel & (DAY == d)].mean() for d in days])
    out = {"days": int(days.size)}
    for name, f in (("citygate_w3", w3), ("ice", cand)):
        df = np.array([f[sel & (DAY == d)].mean() for d in days])
        out[name] = {
            "r": round(float(np.corrcoef(df, dm)[0, 1]), 4),
            "rmse": round(float(np.sqrt(np.mean((df - dm) ** 2))), 3),
        }
    out["ice_wins"] = bool(
        out["ice"]["r"] > out["citygate_w3"]["r"]
        and out["ice"]["rmse"] < out["citygate_w3"]["rmse"]
    )
    return out


def main() -> None:
    """Score 2021-2025 and apply the gate."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--ice-dir", type=Path, required=True)
    ap.add_argument(
        "--out",
        default=str(ROOT / "docs/records/caiso/closeout-caiso-w4/_ice_validation.json"),
    )
    a = ap.parse_args()
    set_caiso_eia930_clock_repair(True)
    res = {str(y): score(a.ice_dir, y) for y in (2021, 2022, 2023, 2024, 2025)}
    wins = sum(res[str(y)].get("ice_wins", False) for y in (2022, 2023, 2024, 2025))
    res["gate"] = {"ice_wins_2022_2025": int(wins), "pass": bool(wins >= 3)}
    res["ice_priced_days"] = {
        str(y): int(np.isfinite(ice_daily(a.ice_dir, y)).sum())
        for y in (2019, 2020, 2021)
    }
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
