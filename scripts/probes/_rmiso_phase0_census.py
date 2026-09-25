#!/usr/bin/env python3
"""R-MISO phase 0 (zero LP): fleet-only census of the re-solve recipe, 2019-2025.

AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24 §5.3.3 step 0. For each
year, rebuild the fleet with ``run_year(fleet_only=True)`` on the R-MISO recipe
(the miso-268 keeper recipe from its ``meta.json`` + that year's
``config_partition_overrides`` overlay + the two outage arms) and record:

(a) the EIA-860 source the solve resolved (``eia860_vintage_year`` /
    ``eia860_vintage_tracks_solve_year``) and the measured-heat-rate flags;
(b) thermal MW whose LP heat rate equals a ``HEAT_RATE_BINS`` class value
    (the audit's heuristic; the exact null-join measure is F1's census);
(c) the armed outage-family files the config resolves to.

2019 has no keeper leg, so it takes the BASE recipe (validation tier, the
2020 config; ``miso_measured_reserve_requirements`` stays False because the
measured cleared-reserve parquet starts in 2023) and the 2020 leg's
``inject_biomass_mustrun`` (recipe-constant across 2020-2025, checked).

Usage::

    uv run python scripts/probes/_rmiso_phase0_census.py --years 2019 2020 --out X.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402

from market_sim.config.constants import HEAT_RATE_BINS  # noqa: E402
from market_sim.data.fleet.models import FUEL_TYPE_MAP  # noqa: E402
from scripts.replay_keeper import (  # noqa: E402
    config_partition_overlay,
    derived_run_year_inputs,
    run_year_kwargs,
)
from scripts.run_calibration import run_year  # noqa: E402

KEEPER = REPO / "results/calibration/miso268_yard_span"
#: The two outage arms this lane adds (audit §5.3.3 "ARM short-gas + unit partial-derate").
ARMS = {"unit_outage_short_windows_gas": True, "unit_partial_outage_windows": True}
FLAGS = (
    "eia860_vintage_year",
    "eia860_vintage_tracks_solve_year",
    "carry_operating_mothballs",
    "retiree_vintage_status_scope",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "unit_outage_maxgen_events",
    "unit_outage_mixed_gas_routing",
    "miso_measured_reserve_requirements",
    "gas_offer_margin_anchor",
    "gas_price_override",
)


def recipe(year: int) -> dict:
    """The R-MISO ``run_year`` kwargs for ``year``."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
    kw["prb_overrides"].update(config_partition_overlay(meta, year))
    kw["prb_overrides"].update(ARMS)
    src_year = year if (KEEPER / f"hourly/class_hourly_{year}.parquet").exists() else 2020
    kw.update(derived_run_year_inputs(KEEPER, src_year))
    return kw


def census(year: int, hh: float) -> dict:
    """Fleet-only rebuild + the three census measures for one year."""
    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True, **recipe(year))
    cfg, fa = st["config"], st["fleet_arrays"]
    out = {"year": year, "config": {k: getattr(cfg, k, None) for k in FLAGS}}
    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    fuel = np.array([inv.get(int(i), "?") for i in fa.fuel_type_idx], dtype=object)
    hr = np.asarray(fa.heat_rate, dtype=float)
    cap = np.asarray(fa.pmax, dtype=float)
    thermal = np.isin(fuel, ["coal", "gas_cc", "gas_ct", "gas_st", "oil", "gas"])
    bin_hit = np.array(
        [any(abs(h - v) < 1e-9 for v in HEAT_RATE_BINS.get(f, {}).values()) for f, h in zip(fuel, hr)]
    )
    out["thermal_mw"] = round(float(cap[thermal].sum()), 1)
    out["class_table_mw"] = round(float(cap[thermal & bin_hit].sum()), 1)
    out["class_table_by_fuel"] = {
        str(f): round(float(cap[thermal & bin_hit & (fuel == f)].sum()), 1)
        for f in sorted(set(fuel[thermal & bin_hit]))
    }
    out["n_units"] = int(len(cap))
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore

    ref = _load_reference()
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    rows = []
    for y in args.years:
        rows.append(census(y, _henry_hub_actual(ref, y)))
        print(json.dumps(rows[-1], default=str))
        Path(args.out).write_text(json.dumps(rows, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
