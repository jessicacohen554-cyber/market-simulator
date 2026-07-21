"""CAMPD coal supply-class delivered-cost pricing (lignite / PRB-by-rail).

The per-year lignite/PRB delivered-cost trajectories, the measured PRB monthly
reporter series, and :func:`apply_coal_supply_pricing`. Split out of
``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as pure code
motion. Distinct from :mod:`market_sim.data.coal` (the plant supply-tag
registry), which this module lazily reads.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from market_sim.config.constants import (
    END_YEAR,
    INFLATION_RATE,
    LIGNITE_PRICE_2023_25,
    PRB_COMMODITY_DECLINE,
    PRB_COMMODITY_FLAT_THROUGH,
    PRB_COMMODITY_SHARE,
    PRB_PRICE_BY_YEAR,
    PRB_RAIL_DIESEL_SHARE,
    PRB_RAIL_NONDIESEL_SHARE,
)
from market_sim.config.scenarios import ScenarioConfig

from ._shared import _month_index, _pkg_ns


# --- CAMPD coal delivered fuel cost ($/MMBtu), by year and supply type ------
# Mine-mouth lignite / PRB-by-rail base levels and trajectory shares now live
# in constants.py (LIGNITE_PRICE_2023_25, PRB_PRICE_BY_YEAR, PRB_*_SHARE,
# PRB_COMMODITY_DECLINE, PRB_COMMODITY_FLAT_THROUGH) — measured delivered-fuel-
# cost inputs (CLAUDE.md rule #13), not a fitted/residual value.


def _build_coal_price_trajectories() -> tuple[dict[int, float], dict[int, float]]:
    """Return ``(lignite, prb)`` delivered-cost dicts spanning 2023-END_YEAR."""
    lignite: dict[int, float] = {}
    prb: dict[int, float] = {}
    for y in (2023, 2024, 2025):
        lignite[y] = LIGNITE_PRICE_2023_25
        prb[y] = PRB_PRICE_BY_YEAR[y]

    avg_prb = sum(PRB_PRICE_BY_YEAR.values()) / 3.0
    commodity_base = PRB_COMMODITY_SHARE * avg_prb
    rail_diesel = PRB_RAIL_DIESEL_SHARE * avg_prb  # held flat forward
    rail_nondiesel_base = PRB_RAIL_NONDIESEL_SHARE * avg_prb
    for y in range(2026, END_YEAR + 1):
        lignite[y] = LIGNITE_PRICE_2023_25 * (1.0 + INFLATION_RATE) ** (y - 2025)
        if y <= PRB_COMMODITY_FLAT_THROUGH:
            commodity = commodity_base
        else:
            commodity = commodity_base * (1.0 - PRB_COMMODITY_DECLINE) ** (
                y - PRB_COMMODITY_FLAT_THROUGH
            )
        rail_nondiesel = rail_nondiesel_base * (1.0 + INFLATION_RATE) ** (y - 2026)
        prb[y] = commodity + rail_diesel + rail_nondiesel
    return lignite, prb


COAL_PRICE_LIGNITE_BY_YEAR, COAL_PRICE_PRB_BY_YEAR = _build_coal_price_trajectories()


@lru_cache(maxsize=1)
def _prb_monthly_actuals() -> dict[int, np.ndarray]:
    """Return ``{year: (12,) $/MMBtu}`` measured PRB delivered cost by month.

    Quantity-weighted across the EIA-923 coal-cost reporters whose plant is
    tagged PRB-by-rail in :data:`market_sim.data.fleet.COAL_PLANT_SUPPLY`
    (ERCOT: Fayette and J K Spruce — the merchant fleet's receipts are
    confidential). The series proxies the delivered PRB cost for the
    *non-reporting* PRB plants in :func:`apply_coal_supply_pricing`; the
    reporters themselves are overwritten with their own plant-months by
    :func:`apply_plant_monthly_fuel_prices` afterwards. Months without a
    report carry the year's mean of the reported months. Lignite has no
    usable monthly proxy (the only reporter, San Miguel, burns its own
    high-cost mine) and stays on the flat annual trajectory. Returns an
    empty dict when the F923 parquet is absent.
    """
    costs = _pkg_ns()._load_monthly_cache(None)
    if costs is None:
        return {}
    from market_sim.data.coal import COAL_PLANT_SUPPLY

    prb_plants = {p for p, s in COAL_PLANT_SUPPLY.items() if s == "prb"}
    sub = costs[
        costs["plant_id"].isin(prb_plants)
        & (costs["fuel_group"] == "Coal")
        & costs["price_per_mmbtu"].notna()
        & (costs["quantity"] > 0)
    ]
    out: dict[int, np.ndarray] = {}
    for year, rows in sub.groupby("year"):
        monthly = np.full(12, np.nan)
        for month, mrows in rows.groupby("month"):
            monthly[int(month) - 1] = float(
                np.average(mrows["price_per_mmbtu"], weights=mrows["quantity"])
            )
        if np.isnan(monthly).all():
            continue
        monthly[np.isnan(monthly)] = np.nanmean(monthly)
        out[int(year)] = monthly
    return out


def apply_coal_supply_pricing(
    fuel_prices: np.ndarray,
    generators: list,
    config: ScenarioConfig,
    year: int,
) -> None:
    """Reprice CAMPD coal generators by their plant fuel-supply type.

    Mine-mouth lignite and PRB-by-rail generators bid at their per-year
    delivered fuel cost — :data:`COAL_PRICE_LIGNITE_BY_YEAR` and
    :data:`COAL_PRICE_PRB_BY_YEAR`. The PRB delivered cost is scaled by
    ``coal_prb_contract_passthrough``: take-or-pay rail/coal contracts
    leave much of the delivered tonnage sunk, so the marginal dispatch bid
    sits below delivered cost. Coal generators with no ``coal_supply`` tag
    (the legacy fleet, or an unmapped plant), or a run year outside the
    coal price trajectory, keep the generic price already in
    ``fuel_prices``.

    Mutates ``fuel_prices`` in place.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array to update,
            aligned row-for-row with ``generators``.
        generators: The dispatch fleet.
        config: Scenario configuration supplying ``coal_prb_contract_passthrough``.
        year: Calendar year, selecting the coal price trajectory entry.
    """
    lignite = COAL_PRICE_LIGNITE_BY_YEAR.get(year)
    prb_delivered = COAL_PRICE_PRB_BY_YEAR.get(year)
    if lignite is None or prb_delivered is None:
        return  # year outside the coal trajectory — keep the generic price

    # PRB base: the measured monthly reporter series for historical years
    # (see _prb_monthly_actuals), expanded hour-by-hour; the flat annual
    # trajectory where no reports exist (forward years). Reporting plants
    # are overwritten with their own months downstream.
    monthly = _prb_monthly_actuals().get(year)
    if monthly is not None:
        prb_price = monthly[_month_index(fuel_prices.shape[1])]
    else:
        prb_price = prb_delivered

    price_by_supply = {
        "lignite": lignite,
        "prb": prb_price * config.coal_prb_contract_passthrough,
    }
    for g_idx, gen in enumerate(generators):
        price = price_by_supply.get(getattr(gen, "coal_supply", ""))
        if price is not None:
            fuel_prices[g_idx, :] = price
