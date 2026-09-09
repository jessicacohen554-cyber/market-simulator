"""Zero-LP census for the NEISO fuel-vintage lane (session neiso-fuelvintage-1).

Two questions, both answered without an LP, both on the committed keeper's own
recipe (``results/calibration/neiso106_offerlevel``):

1. **The fuel seam's written-cell mask.** How many gas cells does arming
   ``gas_electric_power_monthly_level`` actually change, given that NEISO's
   keeper already prices gas off the measured Algonquin hub index
   (``gas_hub_basis_overlay``), which supersedes the seam by the
   ``FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09`` §4 ordering, and
   already overwrites per-plant gas with F923 prints
   (``gas_plant_monthly_fuel_pricing``).
2. **Confinement.** Non-gas fuels must move exactly 0.0.

Usage::

    python3 scripts/probes/_neiso_fuelvintage_census.py 2023 2024 2025
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

BUNDLE = ROOT / "results/calibration/neiso106_offerlevel"


def build(year: int, arm: bool) -> dict:
    """Return ``run_year``'s ``fleet_only`` payload for one year and one side.

    Args:
        year: Solve year to build for.
        arm: True to arm ``gas_electric_power_monthly_level``, False for the
            keeper's own recipe.

    Returns:
        The ``fleet_only`` payload dict.
    """
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kwargs.items() if k in sig}
    call.update(
        year=year,
        iso=meta["iso"],
        hours=8760,
        fleet_only=True,
        gas_price=meta["gas_prices"][str(year)],
        ttc_overrides={},
    )
    if arm:
        call["prb_overrides"] = dict(call.get("prb_overrides") or {})
        call["prb_overrides"]["gas_electric_power_monthly_level"] = True
    return rc.run_year(**call)


def report(year: int) -> dict:
    """Measure and print the armed-vs-keeper delta for one year.

    Args:
        year: Solve year to census.

    Returns:
        A dict of the measured scalars, for the caller's JSON record.
    """
    ctrl = build(year, False)
    arm = build(year, True)
    fa = ctrl["fleet_arrays"]

    fc = np.asarray(ctrl["fuel_prices"], float)
    fam = np.asarray(arm["fuel_prices"], float)
    mc = np.asarray(ctrl["mc_base"], float)
    mca = np.asarray(arm["mc_base"], float)

    from market_sim.data.fleet import FUEL_TYPE_MAP

    fuel_idx = np.asarray(fa.fuel_type_idx)
    gas_codes = {v for k, v in FUEL_TYPE_MAP.items() if str(k).startswith("gas")}
    gas_mask = np.isin(fuel_idx, sorted(gas_codes))

    dfuel = np.abs(fam - fc)
    dmc = np.abs(mca - mc)
    # fuel_prices is (n_gen, T) or (n_gen,) depending on the recipe.
    per_gen_fuel = dfuel.max(axis=1) if dfuel.ndim == 2 else dfuel

    out = {
        "year": year,
        "n_gen": int(fuel_idx.shape[0]),
        "n_gas_gen": int(gas_mask.sum()),
        "fuel_cells": int(dfuel.size),
        "fuel_cells_written": int((dfuel > 0).sum()),
        "fuel_max_abs_delta": float(dfuel.max()),
        "nongas_fuel_max_abs_delta": float(per_gen_fuel[~gas_mask].max()),
        "gas_fuel_max_abs_delta": float(per_gen_fuel[gas_mask].max()),
        "mc_cells_written": int((dmc > 0).sum()),
        "mc_max_abs_delta": float(dmc.max()),
        "nongas_mc_max_abs_delta": float(
            (dmc.max(axis=1) if dmc.ndim == 2 else dmc)[~gas_mask].max()
        ),
    }
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    years = [int(a) for a in sys.argv[1:]] or [2023]
    print(json.dumps([report(y) for y in years], indent=2))
