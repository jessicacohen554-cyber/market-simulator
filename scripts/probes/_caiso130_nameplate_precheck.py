"""caiso-130 pre-solve precheck — how large can the nameplate-aware delta be?

Sizes the ``hydro_budget_nameplate_aware`` delta BEFORE arm B is solved, so
the pre-registration carries a physical bound rather than a hope. Two halves:

1. **The keeper baseline**, recomputed from the keeper bundle's own committed
   ``hourly/class_hourly_<year>.parquet`` sidecars (never a replay): the
   hydro window gaps (model − measured EIA-930 ``NG: WAT``) that
   FINDING-caiso126 §2 and FINDING-caiso127 §Ask quote.
2. **The delta's energy budget**, from the same no-LP ``build_hydro_fleet``
   diff the blast-radius probe uses, split by DESTINATION CLASS. The
   re-allocated energy is only free to land in the evening if it goes to a
   **reservoir**-class (shapeable) plant; energy that lands on a
   ``hydro_ror_split`` RoR plant raises a MONTH-CONSTANT flat level spread
   over all 24 hours, so at most 5/24 of it can reach the evening window.
   That yields a hard per-year upper bound on the evening movement, which is
   what the prereg registers as its ceiling.

**No LP is built or solved.**

Usage:
    PYTHONPATH=.:src:scripts/probes .venv/bin/python \
        scripts/probes/_caiso130_nameplate_precheck.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

from _caiso125_overnight_attribution import (  # noqa: E402
    WINDOWS,
    hydro_hourly,
    measured_hydro,
)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.hydro import build_hydro_fleet, hours_per_month  # noqa: E402
from market_sim.data.hydro_modes import load_hydro_shapeable  # noqa: E402

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "caiso126_rorsplit_B"
EVENING_HOURS = len(WINDOWS["evening"])  # hod 17-21


def keeper_window_gaps() -> dict[int, dict[str, float]]:
    """Return the keeper's (model − measured) hydro window gaps in MW."""
    out: dict[int, dict[str, float]] = {}
    for year in YEARS:
        model = hydro_hourly(KEEPER, year)
        meas = measured_hydro(year, len(model))
        hod = np.arange(len(model)) % 24
        out[year] = {
            name: float(np.nanmean(model[np.isin(hod, list(win))] - meas[np.isin(hod, list(win))]))
            for name, win in WINDOWS.items()
        }
        out[year]["annual_model_mw"] = float(np.nanmean(model))
        out[year]["annual_meas_mw"] = float(np.nanmean(meas))
    return out


def delta_by_destination(year: int) -> dict[str, float]:
    """Split the flag's re-allocated energy by RoR vs reservoir destination."""
    zone_names = get_iso_config("CAISO").zone_names
    common = dict(
        zone_names=zone_names,
        backfill_year=2024,
        eia930_monthly=True,
        forecast_budget=False,
        ror_split=True,
        min_flow_floor=True,
    )
    units_a, mon_a = build_hydro_fleet("CAISO", year, nameplate_aware_target=False, **common)
    _units_b, mon_b = build_hydro_fleet("CAISO", year, nameplate_aware_target=True, **common)
    modes = load_hydro_shapeable("CAISO") or {}
    # RoR-class == the classifier says NOT shapeable; unclassified stays shapeable.
    is_ror = np.array(
        [modes.get(int(u.plant_code), True) is False for u in units_a], dtype=bool
    )
    delta = mon_b - mon_a
    gain = np.maximum(delta, 0.0)  # energy ARRIVING at a plant-month
    hpm = hours_per_month().astype(float)
    cap = np.array([u.pmax_mw for u in units_a], dtype=float)[:, None] * hpm[None, :]
    return {
        "moved_mwh": float(gain.sum()),
        "to_reservoir_mwh": float(gain[~is_ror].sum()),
        "to_ror_mwh": float(gain[is_ror].sum()),
        "undeliverable_off_mwh": float(np.maximum(0.0, mon_a - cap).sum()),
        "n_ror_plants": int(is_ror.sum()),
        "n_plants": int(len(units_a)),
    }


def main() -> None:
    logging.basicConfig(level=logging.ERROR)
    base = keeper_window_gaps()
    print("=== A. keeper baseline: hydro window gap (model - measured), MW ===")
    for year in YEARS:
        row = base[year]
        print(
            f"  {year}: overnight {row['overnight']:+8.1f} | belly {row['belly']:+8.1f} "
            f"| evening {row['evening']:+8.1f} | annual model {row['annual_model_mw']:.0f} "
            f"vs meas {row['annual_meas_mw']:.0f} MW"
        )

    print("\n=== B. delta energy budget and the EVENING CEILING ===")
    summary = {}
    for year in YEARS:
        d = delta_by_destination(year)
        # Ceiling: every reservoir-bound MWh lands in the evening window, plus
        # the RoR-bound MWh spread flat over 24 h (5/24 reaches the evening).
        ceiling_mw = (
            d["to_reservoir_mwh"] + d["to_ror_mwh"] * EVENING_HOURS / 24.0
        ) / (365.0 * EVENING_HOURS)
        summary[year] = {**d, "evening_ceiling_mw": ceiling_mw}
        print(
            f"  {year}: moved {d['moved_mwh']/1e3:8.1f} GWh "
            f"(reservoir {d['to_reservoir_mwh']/1e3:7.1f} / RoR {d['to_ror_mwh']/1e3:6.1f}) "
            f"=> evening ceiling {ceiling_mw:+6.1f} MW "
            f"vs gap {base[year]['evening']:+7.1f} MW"
        )

    out = REPO / "results" / "probes" / "caiso130_precheck.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"baseline": base, "delta": summary}, indent=1, default=float) + "\n"
    )
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
