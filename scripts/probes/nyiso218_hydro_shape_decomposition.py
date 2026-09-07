"""nyiso-218 §8 — decompose NYISO's hydro SHAPE residual (zero LP).

The keeper reproduces hydro VOLUME almost exactly (−2.18 / −0.82 / −0.15 /
−0.19 % in 2022–2025) while hourly ``r`` sits at 0.694 / 0.677 / 0.757 / 0.723.
That is purely a SHAPE defect, and it is FLAT across all four years, so it is
identifiable entirely on the training tier with zero rule-22 exposure.

The handoff names ``scripts/probes/nyiso92_hourly_r_decomposition.py`` as "the
committed instrument". **It does not exist at this HEAD** — it was pruned under
the delete-not-archive discipline — so this is its replacement, written from the
construction nyiso-92's finding describes.

Four layers, model vs EIA-930 ``NG: WAT``:

* **hourly** — ``r`` on the raw 8760 series (the headline).
* **day energy** — ``r`` on the 365 daily totals ("is the water on the right DAY").
* **hour-of-day profile** — ``r`` on the 24 climatological hour-of-day means
  ("is the average diurnal SHAPE right").
* **within-day residual** — ``r`` on ``x[h] − day_mean[d(h)]``, i.e. the shape
  left after both the daily level and nothing else ("is the water in the right
  HOUR of the day it was produced").

Plus two diagnostics that are not layers:

* **price-shaping signature** — the correlation of the model-minus-actual hydro
  residual against the load-weighted system price. A strongly positive value is
  the signature of the LP dispatching to price water the river delivered on flow.
* **bound census proxy** — the share of hours the model's hydro sits within
  0.5 % of its own annual max / min, a cheap stand-in for "at the envelope
  ceiling / at the min-flow floor" that needs no fleet rebuild.

ZERO LP; every input is a committed artifact. Nothing here is gated on a price
residual (rule 1 ``[R-STRUCT]``); it measures a structural object.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

KEEPER = ROOT / "results/calibration/nyiso213_summer_seam"
TP2022 = ROOT / "results/calibration/nyiso213_tp2022"
OUT = ROOT / "results/calibration/_nyiso218_hydro_shape_decomposition.json"
T = 8760


def _r(a: np.ndarray, b: np.ndarray) -> float | None:
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _nrmse(m: np.ndarray, a: np.ndarray) -> float:
    return float(np.sqrt(((m - a) ** 2).mean()) / a.mean())


def _layers(model: np.ndarray, actual: np.ndarray) -> dict:
    days = np.arange(T) // 24
    hod = np.arange(T) % 24
    dm = np.array([model[days == d].sum() for d in range(365)])
    da = np.array([actual[days == d].sum() for d in range(365)])
    pm = np.array([model[hod == h].mean() for h in range(24)])
    pa = np.array([actual[hod == h].mean() for h in range(24)])
    daymean_m = np.repeat(dm / 24.0, 24)[:T]
    daymean_a = np.repeat(da / 24.0, 24)[:T]
    # Split the day-energy layer into ACROSS-month and WITHIN-month. The two
    # armed shape mechanisms (hydro_dispatch_envelope, a month x hour-of-day
    # percentile ceiling; hydro_min_flow_floor, month-constant) are BOTH
    # month x hour-of-day constructions, so neither constrains day-to-day
    # allocation inside a month. If within-month is the weak half, the residual
    # lives in the one dimension no armed mechanism touches.
    month_starts = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30])
    dmonth = np.searchsorted(month_starts, np.arange(365), side="right") - 1
    mm = np.array([dm[dmonth == k].mean() for k in range(12)])
    ma = np.array([da[dmonth == k].mean() for k in range(12)])
    dm_dev = dm - mm[dmonth]
    da_dev = da - ma[dmonth]
    return {
        "month_energy_r": _r(mm, ma),
        "within_month_day_energy_r": _r(dm_dev, da_dev),
        "month_energy_model_gwh": [round(float(v * 1) / 1e3, 2) for v in mm],
        "month_energy_actual_gwh": [round(float(v * 1) / 1e3, 2) for v in ma],
        "hourly_r": _r(model, actual),
        "hourly_nrmse": _nrmse(model, actual),
        "day_energy_r": _r(dm, da),
        "hour_of_day_profile_r": _r(pm, pa),
        "within_day_residual_r": _r(model - daymean_m, actual - daymean_a),
        "model_twh": float(model.sum() / 1e6),
        "actual_twh": float(actual.sum() / 1e6),
        "vol_err_pct": float(100.0 * (model.sum() - actual.sum()) / actual.sum()),
        "hour_of_day_model": [round(float(v), 1) for v in pm],
        "hour_of_day_actual": [round(float(v), 1) for v in pa],
    }


def main() -> None:
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    rows = {}
    for year, bundle in ((2023, KEEPER), (2024, KEEPER), (2025, KEEPER), (2022, TP2022)):
        ch = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
        ch = ch[(ch["pass"] == "P1") & (ch["klass"] == "hydro")].sort_values("hour")
        model = ch["mw"].to_numpy(dtype=float)[:T]
        actual = np.asarray(load_eia_hourly_benchmark("NYISO", year)["hydro"], float)[:T]
        rec = _layers(model, actual)

        sysd = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        num = np.zeros(T)
        den = np.zeros(T)
        for _z, sub in sysd.groupby("zone"):
            sub = sub.sort_values("hour")
            d = sub["demand"].to_numpy(dtype=float)[:T]
            num += sub["price"].to_numpy(dtype=float)[:T] * d
            den += d
        price = np.divide(num, den, out=np.zeros(T), where=den > 0)
        resid = model - actual
        rec["resid_vs_price_r"] = _r(resid, price)
        days = np.arange(T) // 24
        dres = np.array([resid[days == d].sum() for d in range(365)])
        dprice = np.array([price[days == d].mean() for d in range(365)])
        rec["day_resid_vs_day_price_r"] = _r(dres, dprice)
        rec["model_vs_price_r"] = _r(model, price)
        rec["actual_vs_price_r"] = _r(actual, price)

        hi, lo = model.max(), model.min()
        rec["share_hours_within_0.5pct_of_annual_max"] = float(
            (model >= hi * 0.995).mean()
        )
        rec["share_hours_within_0.5pct_of_annual_min"] = float(
            (model <= lo * 1.005 if lo > 0 else model <= 1e-9).mean()
        )
        rec["model_min_mw"] = float(lo)
        rec["model_max_mw"] = float(hi)
        rec["actual_min_mw"] = float(actual.min())
        rec["actual_max_mw"] = float(actual.max())
        rows[year] = rec
        print(
            f"{year}: r {rec['hourly_r']:.3f} | day {rec['day_energy_r']:.3f} | "
            f"hod {rec['hour_of_day_profile_r']:.3f} | within-day "
            f"{rec['within_day_residual_r']:.3f} | vol {rec['vol_err_pct']:+.2f} % | "
            f"resid~price r {rec['resid_vs_price_r']:+.3f}",
            flush=True,
        )
    OUT.write_text(json.dumps({"by_year": rows}, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
