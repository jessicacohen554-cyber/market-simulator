"""Validate the ERCOT forward AS requirement formula against the measured AS Plan.

The forward requirement-setting methodology (G3,
:func:`market_sim.results.scarcity.ercot_as_forward_requirement_mw`) sets each AS
product (RegUp / RRS / ECRS / NonSpin) from forecast drivers — net-load,
net-load up-ramp, VRE share, and the net-load day-ahead forecast-error standard
deviation — instead of reading the measured AS Plan (ASPLANNP433). This script
builds the forward requirement from the model's OWN forecast drivers (the same
served-load + wind/solar-generation series the dispatch uses) and compares it to
the measured ASPLANNP433 realization for 2023-H2 / 2024 / 2025.

This is a **requirement-MW** validation (modeled vs measured procurement
quantity), never a price fit (CLAUDE.md #12). Run:

    python scripts/validate_ercot_as_forward_requirement.py
"""

from __future__ import annotations

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import load_demand
from market_sim.data.renewables import load_renewable_profiles
from market_sim.results.scarcity import (
    ercot_as_forward_drivers,
    ercot_as_forward_requirement_mw,
    ercot_as_plan_requirement_mw,
)

PRODUCTS = ("REGUP", "RRS", "ECRS", "NSPIN")
YEARS = (2023, 2024, 2025)
# ECRS launched 2023-06-10; only score it (and the 2023 totals) over H2.
_H2_START_HOUR_2023 = 181 * 24  # 2023-07-01, non-leap hour-of-year index


def _drivers_for(year: int) -> tuple[dict[str, np.ndarray], int]:
    """Build the forward AS drivers for ``year`` from the model's forecast series."""
    cfg = ScenarioConfig(iso="ERCOT", weather_year=year, mode="backcast")
    iso_config = get_iso_config("ERCOT")
    demand = load_demand(
        "ERCOT",
        year,
        iso_config,
        td_loss_factor=cfg.td_loss_factor,
        include_interchange=True,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "ERCOT", year, iso_config, cfg
    )
    hours = min(8760, demand.shape[1])
    demand = demand[:, :hours]
    wind_cf = wind_cf[:, :hours]
    solar_cf = solar_cf[:, :hours]
    drivers = ercot_as_forward_drivers(
        demand.sum(axis=0),
        (wind_cap[:, None] * wind_cf).sum(axis=0),
        (solar_cap[:, None] * solar_cf).sum(axis=0),
    )
    return drivers, hours


def main() -> None:
    cfg_fwd = ScenarioConfig(
        iso="ERCOT",
        weather_year=2024,
        mode="backcast",
        ercot_as_forward_requirement=True,
    )
    print(
        f"{'product':7} {'year':>5} {'meas':>7} {'model':>7} "
        f"{'MAE':>6} {'bias':>7} {'corr':>5}"
    )
    print("-" * 48)
    for product in PRODUCTS:
        for year in YEARS:
            drivers, hours = _drivers_for(year)
            measured = ercot_as_plan_requirement_mw(year, hours, product)
            model = ercot_as_forward_requirement_mw(cfg_fwd, product, hours, drivers)
            active = measured > 0
            # ECRS: score only its live window (2023-H2 onward in 2023).
            if year == 2023 and product == "ECRS":
                active = active & (np.arange(hours) >= _H2_START_HOUR_2023)
            if active.sum() == 0:
                continue
            m = measured[active]
            p = model[active]
            mae = float(np.abs(p - m).mean())
            bias = float((p - m).mean())
            corr = float(np.corrcoef(p, m)[0, 1])
            print(
                f"{product:7} {year:>5} {m.mean():7.0f} {p.mean():7.0f} "
                f"{mae:6.0f} {bias:+7.0f} {corr:5.2f}"
            )

    # Total AS held (the quantity that drives the shared-headroom scarcity).
    print("\nTotal up-AS held (sum of the four products), demand-active hours:")
    print(f"{'year':>5} {'meas GW':>8} {'model GW':>9} {'ratio':>6}")
    for year in YEARS:
        drivers, hours = _drivers_for(year)
        meas_tot = np.zeros(hours)
        model_tot = np.zeros(hours)
        for product in PRODUCTS:
            meas_tot += ercot_as_plan_requirement_mw(year, hours, product)
            model_tot += ercot_as_forward_requirement_mw(
                cfg_fwd, product, hours, drivers
            )
        active = meas_tot > 0
        mt = meas_tot[active].mean() / 1000.0
        pt = model_tot[active].mean() / 1000.0
        print(f"{year:>5} {mt:8.2f} {pt:9.2f} {pt / mt:6.2f}")


if __name__ == "__main__":
    main()
