"""Shared leaf for the :mod:`market_sim.data.fuel` package split.

Cross-cutting constants and pure helpers every fuel submodule uses: the
fuel-type integer codes, the delivered-gas floor, the non-leap month calendar
helpers, the opt-in clean-data gate, the clean-datatype names, and
:func:`_pkg_ns` — the call-time resolver for the package namespace that keeps
historical ``monkeypatch.setattr("market_sim.data.fuel.<name>", ...)`` /
``patch.object(fuel, ...)`` targets intercepting package internals exactly as
the pre-split module-global reads behaved. Split out of ``data/fuel.py``
(W-D3; refactor-consolidation plan §5 item 3) as pure code motion.

This module is a LEAF: it imports nothing from its sibling submodules, so the
package's module-level import graph stays acyclic (tests/test_persisted_identity.py
``test_no_module_level_import_cycles``).
"""

from __future__ import annotations

import logging
import os

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data.fleet import FUEL_TYPE_MAP

# One logger for the whole package, under the pre-split module name, so log
# records (and any logging-config filters) are unchanged by the split.
logger = logging.getLogger("market_sim.data.fuel")


def _pkg_ns():
    """Return the shared package namespace (:mod:`market_sim.data.fuel`).

    The package took over the exact import path of the pre-split module, so
    every historical ``monkeypatch.setattr("market_sim.data.fuel.<name>", ...)``,
    ``mock.patch.object(fuel, "<name>", ...)`` and direct ``fuel.<name> = ...``
    attribute write lands on the package namespace. Package internals resolve
    the historically patched names through it AT CALL TIME so those patches
    keep intercepting the lookups — the pre-split module-global semantics.
    The routed names (the 2026-07 census union): ``dual_fuel_plant_groups``,
    ``iso_hub_monthly_gas_prices``, ``iso_monthly_gas_prices``,
    ``iso_monthly_oil_prices``, ``ercot_gas_spot_share_by_plant``,
    ``ercot_electric_power_gas_basis``, ``nyiso_reconciled_reference_monthly``,
    ``ZONAL_BASIS_APPLIERS``, ``IROQUOIS_Z2_DAILY_PATH``, ``_load_monthly_cache``,
    ``_henry_hub_monthly``, ``_henry_hub_daily``, ``_henry_hub_daily_dated``,
    ``_algonquin_daily``, ``_transco_z6_daily``, ``_transco_z6_daily_dated``,
    ``_caiso_citygate_daily_dated``, ``_miso_citygate_daily_dated``,
    ``_trade_date_staircase``.
    """
    from market_sim.data import fuel

    return fuel


# Fuel-type integer codes (from FUEL_TYPE_MAP) that burn natural gas and
# therefore pay the Henry Hub price. CCUS (``gas_cc_ccs``) burns the same
# natural gas as an unabated gas CC; ``gas_st`` is legacy gas steam.
_GAS_FUEL_IDX: tuple[int, ...] = (
    FUEL_TYPE_MAP["gas_cc"],
    FUEL_TYPE_MAP["gas_ct"],
    FUEL_TYPE_MAP["gas_cc_ccs"],
    FUEL_TYPE_MAP["gas_st"],
)

# Floor for a delivered gas price after a zonal-basis shift: a deep negative
# regional basis (e.g. a cheap upstate index) can never drive the marginal fuel
# cost to zero or below. Well under any real delivered cost, so it only guards
# the degenerate tail.
_GAS_PRICE_FLOOR: float = 0.10

# Fuel-type integer code for coal-fired units, which pay the coal price.
_COAL_FUEL_IDX: int = FUEL_TYPE_MAP["coal"]

# Fuel-type integer code for oil-fired units (distillate/residual peakers and
# steam), which pay the delivered oil price.
_OIL_FUEL_IDX: int = FUEL_TYPE_MAP["oil"]

# Fuel-type integer code for biomass units, which pay the delivered biomass
# fuel cost.
_BIOMASS_FUEL_IDX: int = FUEL_TYPE_MAP["biomass"]

# Fuel-type integer codes for hydrogen turbines, whose fuel price is the
# derived hydrogen fuel cost (see :mod:`market_sim.data.hydrogen`).
_HYDROGEN_FUEL_IDX: tuple[int, int] = (
    FUEL_TYPE_MAP["hydrogen_ct"],
    FUEL_TYPE_MAP["hydrogen_ccgt"],
)

# Fuel-type integer code for nuclear units, which pay the derived
# EIA-uranium-marketing $/MMBtu fuel-cycle cost (:func:`resolve_nuclear_fuel_price`).
_NUCLEAR_FUEL_IDX: int = FUEL_TYPE_MAP["nuclear"]

# Fuel price ($/MMBtu) for non-fuel-burning units (e.g. wind, solar,
# hydro, imports), which carry no commodity fuel cost in this model.
_ZERO_FUEL_PRICE: float = 0.0

# Calendar days per month for a non-leap year (sums to 365 -> 8760 hours).
_DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


# Opt-in clean-data read path. When the ``MARKET_SIM_USE_CLEAN`` environment flag
# is truthy, the delivered fuel-price loaders source their series from the
# curated ``data/clean`` tree via the frozen ``clean_io.read_clean`` seam instead
# of the raw ``data/raw/gas-prices`` CSVs. OFF by default: the raw path stays the
# contract, so existing runs and calibrations are byte-identical unless a caller
# opts in (and the clean path falls back to raw when the clean tree is absent).
_USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUTHY: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def _use_clean_data() -> bool:
    """Whether the opt-in clean-data read path is enabled (default ``False``)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _USE_CLEAN_TRUTHY


def _month_index(hours: int) -> np.ndarray:
    """Return an ``(hours,)`` array mapping each hour to a 0-based month."""
    full = np.empty(HOURS_PER_YEAR, dtype=int)
    hour = 0
    for month_idx, days in enumerate(_DAYS_IN_MONTH):
        hours_in_month = days * 24
        full[hour : hour + hours_in_month] = month_idx
        hour += hours_in_month
    if hours <= HOURS_PER_YEAR:
        return full[:hours]
    reps = -(-hours // HOURS_PER_YEAR)
    return np.tile(full, reps)[:hours]


def _expand_monthly_to_hourly(monthly: np.ndarray, hours: int) -> np.ndarray:
    """Broadcast a length-12 monthly price array onto the hourly horizon."""
    return monthly[_month_index(hours)]


# Clean-data consumption. Curated Parquet for each fuel-price datatype is read
# via the frozen ``clean_io.read_clean`` seam when the opt-in flag is set and the
# clean tree has been populated (``python scripts/data/curate_fuel_prices.py``). The
# raw CSV path is always the fallback so existing runs are byte-identical unless
# the caller explicitly opts in via the MARKET_SIM_USE_CLEAN env flag.
_FUEL_PRICES_DATATYPE: str = "fuel-prices"
_FUEL_HUB_MONTHLY_DATATYPE: str = "fuel-hub-monthly"
_FUEL_BASIS_DATATYPE: str = "fuel-basis"
_FUEL_ZONAL_HUB_DATATYPE: str = "fuel-zonal-hub"
_FUEL_ERCOT_EP_GAS_DATATYPE: str = "fuel-ercot-ep-gas"
_FUEL_TAKEORPAY_DATATYPE: str = "fuel-takeorpay"

_HENRY_HUB_CLEAN_KEY: tuple[str, str] = ("gas", "henry_hub")


def _clean_zonal_hub_frame(iso: str) -> pd.DataFrame | None:
    """Zonal gas-hub frame for ``iso`` from the clean ``fuel-zonal-hub`` tree.

    Returns the same ``pd.DataFrame | None`` contract as the raw CSV loaders.
    """
    from scripts.lib.clean_io import read_clean

    df = read_clean(_FUEL_ZONAL_HUB_DATATYPE, iso=iso, validate=False)
    return df if not df.empty else None
