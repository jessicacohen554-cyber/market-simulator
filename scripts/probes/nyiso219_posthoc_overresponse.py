"""nyiso-219 POST-HOC — **NOT pre-registered.** Is the model's defect *over-response*?

The pre-registered census (:mod:`scripts.probes.nyiso219_hydro_daily_driver_census`)
returned a result its own predictions did not anticipate: the *measured* NYISO hydro
fleet's within-month day-to-day allocation is better explained by **daily load**
(mean r 0.307 over 2019-2025) than by **measured basin inflow** (mean r 0.243), and a
day-of-year climatology explains essentially **nothing** (mean r 0.031). That points
the successor object away from "a missing inflow driver" and toward "a missing limit
on how far the fleet may swing between days" -- so these four diagnostics test that
reading directly.

**Every number here is POST-HOC.** It was computed after the pre-registered numbers
were read, it moves no gate, it scores no criterion, and it is reported as a
follow-up reading rather than as a confirmed prediction. It exists so the successor
object is stated on evidence instead of on inference.

Scope discipline (rule 22 ``[R-HOLDOUT]``): PH-1 reads **model** output, so it is
restricted to the training tier 2023-2025 and the keeper's own committed
``hourly/class_hourly_<year>.parquet``. The measured-data diagnostics (PH-2..PH-4)
span 2019-2025 like the census, reading actuals only.

ZERO LP.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.probes.nyiso219_hydro_daily_driver_census import (  # noqa: E402
    GAUGES,
    SCORED_YEARS,
    _actual_hydro_daily,
    _actual_load_daily,
    _daily_totals,
    _r,
    _within_month_dev,
    load_discharge,
    water_source_census,
)

KEEPER_BUNDLE = REPO / "results" / "calibration" / "nyiso213_summer_seam"
TRAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)
OUT_JSON = REPO / "results" / "calibration" / "_nyiso219_posthoc_overresponse.json"


def _model_hydro_daily(year: int) -> np.ndarray | None:
    """Keeper P1 hydro, daily energy (MWh/day), from the committed class hourly."""
    path = KEEPER_BUNDLE / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    hydro = frame[frame["klass"] == "hydro"]
    if hydro.empty:
        return None
    series = hydro.groupby("hour")["mw"].sum().sort_index().to_numpy(dtype=float)
    if len(series) != 8760:
        return None
    return _daily_totals(series)


def main() -> None:
    census = water_source_census()
    discharge = load_discharge()

    weights = {
        row["source"]: row["pct_mw"]
        for row in census["sources"]
        if row["source"] in GAUGES and GAUGES[row["source"]]["role"] == "material-basin"
    }
    weight_sum = sum(weights.values())

    def basin_index(year: int) -> np.ndarray | None:
        """The census's MW-weighted, mean-normalized basin discharge index."""
        stacked = np.zeros(365)
        for source, pct in weights.items():
            sub = discharge[
                (discharge.site == GAUGES[source]["site"])
                & (discharge.date.dt.year == year)
                & ~((discharge.date.dt.month == 2) & (discharge.date.dt.day == 29))
            ].sort_values("date")
            values = sub.cfs.to_numpy(dtype=float)
            if len(values) != 365 or not np.isfinite(values).all():
                return None
            stacked += (pct / weight_sum) * (values / values.mean())
        return stacked

    out: dict[str, dict] = {"PH1_model_vs_actual_response": {}}

    # PH-1 -- the over-response test. If the model and the actual respond to the
    # SAME driver but the model responds harder, the model's own r with load will
    # exceed the actual's, and its within-month daily sd will exceed the actual's.
    for year in TRAIN_YEARS:
        model = _model_hydro_daily(year)
        actual = _actual_hydro_daily(year)
        load = _actual_load_daily(year)
        if model is None or actual is None or load is None:
            continue
        m_dev, a_dev, l_dev = (_within_month_dev(x) for x in (model, actual, load))
        out["PH1_model_vs_actual_response"][str(year)] = {
            "model_r_with_load": round(_r(m_dev, l_dev), 4),
            "actual_r_with_load": round(_r(a_dev, l_dev), 4),
            "model_within_month_daily_sd_gwh": round(float(m_dev.std()) / 1e3, 3),
            "actual_within_month_daily_sd_gwh": round(float(a_dev.std()) / 1e3, 3),
            "sd_ratio_model_over_actual": round(float(m_dev.std() / a_dev.std()), 3),
            "model_r_with_actual": round(_r(m_dev, a_dev), 4),
        }

    # PH-2 -- per-basin mean r across the scored years. The sharpest form of the
    # census result: the river under 52 % of the fleet's MW carries almost none of
    # the day-to-day signal, while a 4 %-of-MW runoff cascade carries the most.
    per_basin: dict[str, list[float]] = {}
    for year in SCORED_YEARS:
        actual = _actual_hydro_daily(year)
        if actual is None:
            continue
        target = _within_month_dev(actual)
        for source in weights:
            sub = discharge[
                (discharge.site == GAUGES[source]["site"])
                & (discharge.date.dt.year == year)
                & ~((discharge.date.dt.month == 2) & (discharge.date.dt.day == 29))
            ].sort_values("date")
            values = sub.cfs.to_numpy(dtype=float)
            if len(values) == 365 and np.isfinite(values).all():
                per_basin.setdefault(source, []).append(_r(_within_month_dev(values), target))
    out["PH2_per_basin_mean_r_2019_2025"] = {
        source: {
            "mean_r": round(float(np.mean(vals)), 4),
            "pct_fleet_mw": round(weights[source], 2),
            "n_years": len(vals),
        }
        for source, vals in per_basin.items()
    }

    # PH-3 -- how much do flow and load explain TOGETHER? An OLS multiple-R on the
    # two candidate drivers, to see whether inflow adds anything beyond load.
    combo: dict[str, dict] = {}
    for year in SCORED_YEARS:
        actual = _actual_hydro_daily(year)
        load = _actual_load_daily(year)
        flow = basin_index(year)
        if actual is None or load is None or flow is None:
            continue
        target = _within_month_dev(actual)
        design = np.column_stack(
            [np.ones(365), _within_month_dev(load), _within_month_dev(flow)]
        )
        coef, *_ = np.linalg.lstsq(design, target, rcond=None)
        fitted = design @ coef
        combo[str(year)] = {
            "multiple_r_load_plus_flow": round(_r(fitted, target), 4),
            "r_load_only": round(_r(_within_month_dev(load), target), 4),
            "r_flow_only": round(_r(_within_month_dev(flow), target), 4),
        }
    out["PH3_load_plus_flow"] = combo

    # PH-4 -- the amplitude the actual actually uses, as a share of the monthly
    # budget. This is the quantity a "how far may the fleet shift water between
    # days" limit would have to be stated in, so it is measured rather than assumed.
    amplitude: dict[str, dict] = {}
    for year in SCORED_YEARS:
        actual = _actual_hydro_daily(year)
        if actual is None:
            continue
        dev = _within_month_dev(actual)
        amplitude[str(year)] = {
            "mean_daily_gwh": round(float(actual.mean()) / 1e3, 3),
            "within_month_daily_sd_gwh": round(float(dev.std()) / 1e3, 3),
            "within_month_daily_sd_pct_of_mean": round(
                100.0 * float(dev.std() / actual.mean()), 3
            ),
            "max_abs_within_month_dev_pct_of_mean": round(
                100.0 * float(np.abs(dev).max() / actual.mean()), 2
            ),
            "p95_abs_within_month_dev_pct_of_mean": round(
                100.0 * float(np.percentile(np.abs(dev), 95) / actual.mean()), 2
            ),
        }
    out["PH4_actual_within_month_amplitude"] = amplitude

    out["_provenance"] = {
        "post_hoc": True,
        "pre_registered": False,
        "moves_no_gate": True,
        "model_years_read": list(TRAIN_YEARS),
        "keeper_bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
    }
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
