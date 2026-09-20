"""nyiso-242 phase 0C — the model's OWN delivered fuel price in the hours it misses the 2022 tail.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Uses the sanctioned ``run_year(..., fleet_only=True)``
rebuild of the designated keeper's own recipe — the same instrument nyiso-232 and
nyiso-241 used — which builds the fleet arrays and the delivered ``fuel_prices``
surface without ever entering HiGHS.

Phase 0A/0B established that the 100 missed hours are TWO different objects:

* a **winter** cluster (70 h, Jan/Feb/Dec) in which all five zones clear above
  $300 while the model's thermal fleet sits at 47 % of its own annual max and
  its marginal emission rate is indistinguishable from an ordinary hour — i.e.
  nothing is tight and nothing has switched fuel; and
* a **summer** cluster (23 h) in which the model IS tight (91 % of annual max,
  peakers and the steam fleet on) and simply does not price the tail.

This probe measures the input the winter cluster turns on: what delivered gas
price does the LP actually see on those days, against the measured Transco Z6
NY daily print for the same gas day, and against the distillate parity the
``dual_fuel_switching`` cap prices a switchable unit at?

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso242_fuel_in_missed.py [--year 2022]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
TZ6 = REPO / "data" / "raw" / "gas-prices" / "transco_z6_ny_daily.csv"
THRESHOLD = 300.0
#: Classes whose delivered fuel price is the gas series the winter question is about.
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")


def fleet_state(year: int):
    """Fleet-only rebuild of the keeper's recipe — no LP is entered."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, year))
    return run_year(year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)


def missed_hours(year: int) -> tuple[list[int], list[int], list[int]]:
    """(all, winter, summer) hour indices the model misses against the actual tail."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "z", REPO / "scripts" / "probes" / "nyiso242_tail_zonal.py"
    )
    z = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(z)
    act, mod = z.actual_zonal(year), z.model_zonal(year)
    n = min(len(act), len(mod))
    df = pd.concat(
        [act.iloc[:n].reset_index(drop=True), mod.iloc[:n].reset_index(drop=True)], axis=1
    )
    month = pd.Series(pd.date_range(f"{year}-01-01", periods=n, freq="h").month, index=df.index)
    miss = list(df.index[(df["actual_hub11"] > THRESHOLD) & (df["model_max"] <= THRESHOLD)])
    return (
        miss,
        [h for h in miss if month[h] in (1, 2, 12)],
        [h for h in miss if month[h] in (6, 7, 8)],
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument(
        "--out", default=str(REPO / "results" / "calibration" / "_nyiso242_fuel_in_missed.json")
    )
    args = ap.parse_args()
    year = args.year

    st = fleet_state(year)
    fa = st["fleet_arrays"]
    klass = np.asarray([str(k) for k in fa.plant_group])
    pmax = np.asarray(fa.pmax, dtype=float)
    fuel = np.asarray(st["fuel_prices"], dtype=float)
    if fuel.ndim == 1:  # one price per unit, broadcast across the year
        fuel = np.repeat(fuel[:, None], 8760, axis=1)

    allm, win, summ = missed_hours(year)

    # The measured print, forward-filled onto calendar days (gas trades on
    # business days; a weekend burns on Friday's package price).
    gz = pd.read_csv(TZ6, parse_dates=["date"])
    gz = gz[gz["date"].dt.year == year].set_index("date")
    cal = pd.DataFrame(index=pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D"))
    cal["tz6"] = gz["transco_z6_ny_usd_mmbtu"].reindex(cal.index).ffill().bfill()
    hours = pd.date_range(f"{year}-01-01", periods=fuel.shape[1], freq="h")
    tz6_h = cal["tz6"].reindex(hours.normalize()).to_numpy()

    out: dict = {"year": year, "bundle": str(BUNDLE.relative_to(REPO)), "windows": {}}
    for label, sel in (("all_missed", allm), ("winter", win), ("summer", summ), ("all_8760", list(range(fuel.shape[1])))):
        if not sel:
            continue
        rec: dict = {"hours": len(sel)}
        for cls in GAS_CLASSES:
            m = klass == cls
            if not m.any():
                continue
            w = pmax[m]
            sub = fuel[np.ix_(m, sel)]
            # Capacity-weighted delivered fuel price, then the median over the window.
            cw = (sub * w[:, None]).sum(axis=0) / w.sum()
            rec[cls] = round(float(np.median(cw)), 3)
        rec["measured_tz6_median"] = round(float(np.median(tz6_h[sel])), 3)
        rec["measured_tz6_max"] = round(float(np.max(tz6_h[sel])), 3)
        if "CC_REGULAR" in rec:
            rec["model_over_measured_CC"] = round(rec["CC_REGULAR"] / rec["measured_tz6_median"], 3)
        out["windows"][label] = rec

    # The whole point in one line per window: what the gap is worth in $/MWh at
    # the model's own capacity-weighted CC and ST heat rates.
    hr = np.asarray(fa.heat_rate, dtype=float)
    hrs = {}
    for cls in ("CC_REGULAR", "ST_GAS", "CT_PEAKER"):
        m = klass == cls
        if m.any():
            hrs[cls] = round(float((hr[m] * pmax[m]).sum() / pmax[m].sum()), 3)
    out["capacity_weighted_heat_rate"] = hrs
    w = out["windows"].get("winter", {})
    if w and "CC_REGULAR" in w:
        gap = w["measured_tz6_median"] - w["CC_REGULAR"]
        out["winter_fuel_gap"] = {
            "delta_usd_per_mmbtu": round(gap, 3),
            "worth_usd_per_mwh_at_CC_hr": round(gap * hrs.get("CC_REGULAR", 0.0), 2),
            "worth_usd_per_mwh_at_ST_hr": round(gap * hrs.get("ST_GAS", 0.0), 2),
        }

    print(json.dumps(out, indent=2))
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
