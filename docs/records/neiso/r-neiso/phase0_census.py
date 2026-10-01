"""R-NEISO phase 0 (zero LP): per-year fleet census, incumbent vs corrected-input recipe.

Every number is a ``run_year(fleet_only=True)`` rebuild — the calibration prep
path stops after the fleet/availability arrays are built, so no LP is
constructed or solved (rule 32 ``[R-SHARD]`` (a): zero-LP work stays in the
parent).

Recipes, both from the NEISO keeper's own ``meta.json``
(``results/calibration/hydro5_neiso_ror_span``):

* ``A`` — the incumbent recipe at this HEAD with F1's six backcast defaults
  forced to their pre-F1 values (``eia860_vintage_tracks_solve_year`` and
  ``measured_{coal,st,cc}_heat_rates`` False; CT / CHP stay True, as the keeper
  armed them). Reads the F1-rejoined eGRID heat rates regardless (those are
  data, not a flag), so A isolates the FLAG posture, not the data refresh.
* ``B`` — the R-NEISO recipe: the keeper + every F1 default ON + the two outage
  families this lane arms (``unit_outage_short_windows_gas``,
  ``unit_partial_outage_windows``) + the two mid-year exit channels that keep a
  year-END vintage table from dropping a plant or unit that retired DURING the
  year (``mid_vintage_exit_carry``, ``partial_plant_exit_carry``).
* ``B-nosg`` / ``B-nopart`` — B minus one family, so each family's
  availability contribution is measured on its own.

Per year and recipe it reports: the EIA-860 directory the loaders resolved,
thermal nameplate by plant group, the MW-weighted mean heat rate by group,
class-table MW (a plant with no joined eGRID rate in its source table whose
loaded rate is a ``HEAT_RATE_BINS`` value — F1's exact measure, applied to the
post-overlay fleet the LP would dispatch), and mean unavailable MW by group.

Usage::

    uv run python docs/handoffs/r-neiso/phase0_census.py --out docs/handoffs/r-neiso/phase0_census.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import HEAT_RATE_BINS  # noqa: E402
from market_sim.config.paths import active_eia860_dir, set_eia860_vintage  # noqa: E402
from market_sim.data.fleet.eia860 import ba_codes  # noqa: E402

BUNDLE = REPO / "results/calibration/hydro5_neiso_ror_span"
YEARS = tuple(range(2019, 2026))
F1_OFF = {
    "eia860_vintage_tracks_solve_year": False,
    "measured_coal_heat_rates": False,
    "measured_st_heat_rates": False,
    "measured_cc_heat_rates": False,
}
F1_ON = {
    "eia860_vintage_tracks_solve_year": True,
    "measured_ct_heat_rates": True,
    "measured_coal_heat_rates": True,
    "measured_st_heat_rates": True,
    "measured_cc_heat_rates": True,
    "measured_chp_heat_rates": True,
}
ARMS = {
    "unit_outage_short_windows_gas": True,
    "unit_partial_outage_windows": True,
    "mid_vintage_exit_carry": True,
    "partial_plant_exit_carry": True,
}
RECIPES = {
    "A": F1_OFF,
    "B": {**F1_ON, **ARMS},
    "B-nosg": {**F1_ON, **ARMS, "unit_outage_short_windows_gas": False},
    "B-nopart": {**F1_ON, **ARMS, "unit_partial_outage_windows": False},
}
RENAMES = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
}
SKIP = {"year", "iso", "hours", "gas_price", "ttc_overrides", "fleet_only", "xyear_cache", "must_run_mw"}


def _null_hr_plants(path: Path) -> set[int]:
    """Plant codes whose EIA-860 source rows carry no joined eGRID heat rate."""
    df = pd.read_parquet(path)
    codes = ba_codes("NEISO")
    if codes and "balancing_authority_code" in df.columns:
        df = df[df["balancing_authority_code"].astype(str).str.strip().isin(codes)]
    if "heat_rate" not in df.columns:
        return set(pd.to_numeric(df["plant_id"], errors="coerce").dropna().astype(int))
    hr = pd.to_numeric(df["heat_rate"], errors="coerce")
    return set(pd.to_numeric(df[hr.isna() | (hr <= 0)]["plant_id"], errors="coerce").dropna().astype(int))


def _bin_values() -> np.ndarray:
    return np.array(sorted({float(v) for d in HEAT_RATE_BINS.values() for v in d.values()}))


def _build(year: int, overrides: dict):
    from scripts.run_calibration import run_year
    import inspect

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    kw = {}
    for k, v in meta.items():
        k2 = RENAMES.get(k, k)
        if k2 in params and k2 not in SKIP:
            kw[k2] = v
    kw["inject_biomass_mustrun"] = True  # derived_run_year_inputs: True in every keeper year
    kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **overrides}
    from scripts import run_calibration_full as rcf

    from market_sim.pipeline.reference import henry_hub_actual

    gas = henry_hub_actual(rcf._load_reference(), year)
    state = run_year(year, "NEISO", 8760, gas, {}, fleet_only=True, **kw)
    return state, active_eia860_dir()


def census_one(year: int, label: str) -> dict:
    """Fleet census for one (year, recipe)."""
    state, eia_dir = _build(year, RECIPES[label])
    fa = state["fleet_arrays"]
    groups = np.asarray(fa.plant_group).astype(str) if fa.plant_group is not None else np.array(["?"] * len(fa.pmax))
    pmax = np.asarray(fa.pmax, float)
    hr = np.asarray(fa.heat_rate, float)
    avail = np.asarray(fa.availability, float)
    mean_av = avail.mean(axis=1) if avail.ndim == 2 else avail
    thermal = hr > 0
    null_plants = _null_hr_plants(eia_dir / "eia860_generators.parquet")
    binv = _bin_values()
    is_bin = np.array([np.any(np.abs(binv - h) < 1e-9) for h in hr])
    codes = np.asarray(fa.plant_code).astype(int)
    cls_tab = thermal & is_bin & np.isin(codes, list(null_plants))
    by_group = {}
    for g in sorted(set(groups[thermal])):
        m = thermal & (groups == g)
        mw = float(pmax[m].sum())
        by_group[g] = {
            "mw": round(mw, 1),
            "hr_mw_wt": round(float((hr[m] * pmax[m]).sum() / mw), 4) if mw else None,
            "unavail_mw": round(float((pmax[m] * (1 - mean_av[m])).sum()), 1),
            "class_table_mw": round(float(pmax[m & cls_tab].sum()), 1),
        }
    resid = {}
    for i in np.where(cls_tab)[0]:
        resid.setdefault(int(codes[i]), [0.0, groups[i]])
        resid[int(codes[i])][0] += float(pmax[i])
    bins_plants = {}
    for i in np.where(thermal & is_bin)[0]:
        bins_plants[int(codes[i])] = bins_plants.get(int(codes[i]), 0.0) + float(pmax[i])
    return {
        "eia860_dir": eia_dir.name,
        "thermal_mw": round(float(pmax[thermal].sum()), 1),
        "class_table_mw": round(float(pmax[cls_tab].sum()), 1),
        # The audit's coarser heuristic: ANY thermal row at a HEAT_RATE_BINS value,
        # whatever its source (catches carried retiree / partial-exit rows too).
        "bins_mw": round(float(pmax[thermal & is_bin].sum()), 1),
        "bins_plants": {str(k): round(v, 1) for k, v in sorted(bins_plants.items(), key=lambda kv: -kv[1])},
        "unavail_mw": round(float((pmax[thermal] * (1 - mean_av[thermal])).sum()), 1),
        "by_group": by_group,
        "class_table_plants": {str(k): [round(v[0], 1), v[1]] for k, v in sorted(resid.items(), key=lambda kv: -kv[1][0])},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--recipes", nargs="+", default=list(RECIPES))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)  # carry / outage lines are the G2 evidence
    out = {}
    for y in args.years:
        for r in args.recipes:
            out.setdefault(str(y), {})[r] = census_one(y, r)
            set_eia860_vintage(None)
            print(y, r, out[str(y)][r]["eia860_dir"], out[str(y)][r]["thermal_mw"],
                  out[str(y)][r]["class_table_mw"], out[str(y)][r]["unavail_mw"], flush=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
