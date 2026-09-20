"""nyiso-248 phase 0 — gate G-3: does ``_gas_series`` see what the merit order sees?

ZERO LP (rule 32 ``[R-SHARD]`` (a)).

``_hub_overlay_series`` documents an explicit invariant:

    "used by :func:`_gas_series` so gas-keyed coal passthrough sigmoids see the
    same delivered gas price the merit order sees."

G-2 measured that the two disagree on the keeper (within-month CV 0.0000 against
0.2646-0.3639). This gate proves WHY mechanically rather than by reading: it
calls both overlay paths on the keeper's own resolved config and diffs them.

``apply_hub_basis_overlay`` branches on ``gas_hub_basis_daily`` into
``iso_hub_daily_gas_prices``. ``_hub_overlay_series`` has **no such branch** —
it calls ``iso_hub_monthly_gas_prices`` and expands, unconditionally. So the
single-series analogue silently ignores the daily gate that the array path
honours.

It also sizes the NYISO blast radius, because a defect nobody's fleet feels is
a routing note and not a mechanism: ``_gas_series``' live solve-path consumers
are the gas-keyed COAL passthrough sigmoids (``runner.py``,
``run_calibration.py``) and ``data/fuel/zonal_anchor.py`` (inert on this keeper
— nyiso-247 disarmed ``gas_offer_net_revenue_margin``).

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso248_series_invariant.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
OUT = REPO / "results" / "calibration" / "_nyiso248_series_invariant.json"
YEARS = (2022, 2023, 2024, 2025)
HOURS = 8760


def _keeper_config(year: int):
    """The keeper's OWN resolved ScenarioConfig, from the fleet-only rebuild."""
    from scripts.probes.nyiso242_tail_reachability import fleet_state

    st = fleet_state(year)
    for key in ("config", "scenario", "scenario_config", "cfg"):
        if st.get(key) is not None:
            return st[key], st
    raise SystemExit("no ScenarioConfig in fleet-only state")


def run_year(year: int) -> dict:
    from market_sim.data.fuel.hubs import (
        iso_hub_daily_gas_prices,
        iso_hub_monthly_gas_prices,
    )

    cfg, st = _keeper_config(year)

    monthly = iso_hub_monthly_gas_prices(cfg, year)
    daily = iso_hub_daily_gas_prices(cfg, year)

    rec: dict = {
        "gas_hub_basis_overlay": bool(getattr(cfg, "gas_hub_basis_overlay", False)),
        "gas_hub_basis_daily": bool(getattr(cfg, "gas_hub_basis_daily", False)),
        "monthly_available": monthly is not None,
        "daily_available": daily is not None,
    }
    if monthly is not None:
        m = np.asarray(monthly, dtype=float)
        rec["monthly_distinct"] = int(np.unique(np.round(m[~np.isnan(m)], 6)).size)
    if daily is not None:
        d = np.asarray(daily, dtype=float)
        dd = d[~np.isnan(d)]
        rec["daily_distinct"] = int(np.unique(np.round(dd, 6)).size)
        rec["daily_min"] = float(dd.min())
        rec["daily_max"] = float(dd.max())
        rec["daily_p50"] = float(np.percentile(dd, 50))

    # The series the solve actually hands the coal sigmoids.
    series = np.load(CACHE / f"gas_{year}.npy").astype(float)
    rec["gas_series_distinct"] = int(np.unique(np.round(series, 6)).size)
    rec["gas_series_min"] = float(series.min())
    rec["gas_series_max"] = float(series.max())

    # THE INVARIANT: is _gas_series the daily object the array path uses?
    if daily is not None:
        d = np.asarray(daily, dtype=float)
        both = ~np.isnan(d)
        rec["max_abs_diff_vs_daily"] = float(
            np.abs(series[both] - d[both]).max()
        )
        rec["invariant_holds"] = bool(rec["max_abs_diff_vs_daily"] < 1e-9)

    # NYISO blast radius: the gas-keyed COAL passthrough consumers.
    fa = st["fleet_arrays"]
    groups = np.array([str(g) for g in fa.plant_group])
    pmax = np.asarray(fa.pmax, dtype=float)
    coal_mw = float(pmax[np.char.upper(groups.astype(str)) == "COAL"].sum())
    gas_mw = float(
        pmax[
            [any(t in g.upper() for t in ("CC", "CT", "ST_GAS")) for g in groups]
        ].sum()
    )
    rec["coal_mw"] = coal_mw
    rec["gas_mw"] = gas_mw
    rec["coal_share_of_thermal"] = coal_mw / (coal_mw + gas_mw) if gas_mw else 0.0
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()

    result = {"gate": "G-3", "years": {}}
    for y in args.year:
        r = run_year(y)
        result["years"][str(y)] = r
        print(f"\n===== {y} =====")
        for k, v in r.items():
            print(f"  {k:<28} {v}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
