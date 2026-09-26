"""Measured MONTHLY delivered-gas LEVEL, per ISO, from the EIA N3045 state series.

The ISO-agnostic generalization of ERCOT's own level anchor
(:func:`market_sim.data.fuel.basis.ercot.ercot_electric_power_gas_basis`,
EIA series ``N3045TX3``): the price of natural gas **sold to electric-power
consumers** is published monthly for every state, so an ISO's measured
delivered LEVEL is that series blended across its footprint states by the
ISO's own installed gas capacity there
(``data/raw/reference/iso-gas-capacity-state-weights.csv``, written by
``scripts/data/derive_iso_gas_state_weights.py``).

**Why a LEVEL and not another shape.** Every ISO's gas price today resolves
from one annual scalar — ``HENRY_HUB_TRAJECTORIES[path][year]`` (or the
keeper's ``gas_price_override``) plus a flat ``GAS_BASIS_DIFFERENTIAL``
constant — and the existing monthly mechanisms are *mean-preserving by
construction*: ``gas_hh_monthly_shape`` normalizes to the annual level
exactly, and ``gas_daily_shape`` normalizes per month. A shape cannot repair
a level, so a year whose annual mean is contaminated by one extreme month
overprices every other month of that year and underprices the extreme one —
one term, both signs
(``docs/FINDING-ercot254-2021-offer-level-root-cause-2026-09-07.md``). This
replaces the LEVEL month by month with the measured one.

**It is the price of the DELIVERED COMMODITY, not the city gate.** N3045 is
what power plants pay; ``N3050`` (city gate) carries the LDC distribution
margin generators do not pay, and is deliberately not used here — the same
distinction ``ercot.ERCOT_ELECTRIC_POWER_GAS_PATH`` records.

**Where it does NOT apply, and why that is rule 19 ``[R-ONE-MECH]`` rather
than a gap.** It is applied at the ISO-month level, ahead of
:func:`~market_sim.data.fuel.hubs.apply_hub_basis_overlay`, so an ISO that
already prices its gas off a **measured constrained-hub index** (NEISO
Algonquin Citygate, CAISO SoCal/PG&E Citygate, NYISO Transco Z6) keeps that
index: a hub index is the marginal unit's own opportunity cost, while the
state series is an average delivered cost across every purchase in the state,
and the more local measured marginal series wins. The levels are strictly
ordered — national annual < state-average monthly < measured hub index — and
each supersedes the one before it rather than stacking on it.

**Forward reproducibility (rule 13 ``[R-MEASURED]``).** The construction is
``blend(state monthly delivered) ``; for a forward year it regenerates from a
forward monthly gas curve through the identical blend, and it responds to
changed conditions (a mild winter's cheap February reaches the merit order).
A year with no admissible print returns ``None`` and the caller keeps its
existing construction byte-for-byte, so every forecast run is unchanged.

**Admissibility, declared ex ante and never swept.** For a year to be priced
here, the states used must (a) print in **all twelve months** of that year —
so the basket's composition is constant within the year and no month-to-month
price move can be an artifact of a state entering or leaving it — and
(b) together carry a **strict majority of the ISO's gas capacity**. There is
no national-average backfill for an unprinted state: substituting
``N3045US3`` would put a national number back into exactly the state-months
where the local price departs most from national (Uri in Louisiana, Elliott
in the Mid-Atlantic), which is the defect being repaired. A year that fails
either test is inert.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import GAS_PRICES_DIR, REFERENCE_DIR

#: EIA N3045 monthly "natural gas price sold to electric power consumers",
#: every state, $/Mcf. Intake and coverage:
#: ``data/raw/gas-prices/SOURCES_eia_delivered_gas_electric_power_by_state.md``.
ELECTRIC_POWER_GAS_BY_STATE_PATH: Path = (
    GAS_PRICES_DIR / "eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv"
)

#: Per-ISO gas-capacity share by state (``scripts/data/derive_iso_gas_state_weights.py``).
ISO_GAS_STATE_WEIGHTS_PATH: Path = REFERENCE_DIR / "iso-gas-capacity-state-weights.csv"

#: EIA heat content of pipeline-quality natural gas: 1 Mcf = 1.036 MMBtu
#: (EIA Natural Gas Annual, average heat content of natural gas delivered to
#: consumers). The N3045 series is $/Mcf; the model prices $/MMBtu.
MCF_TO_MMBTU: float = 1.036

#: Minimum share of an ISO's gas capacity the admitted state basket must carry
#: for the year to be priced here — a strict majority, i.e. the blend must
#: represent more of the ISO's gas fleet than it omits. Declared ex ante and
#: NEVER swept against a gate (rule 1 ``[R-STRUCT]`` condition (c)).
MIN_FOOTPRINT_COVERAGE: float = 0.5

_MONTHS = tuple(range(1, 13))


@lru_cache(maxsize=4)
def _load_state_prices(path: str | None = None) -> dict[tuple[str, int, int], float]:
    """Return ``{(state, year, month): $/Mcf}`` for the N3045 state series."""
    resolved = Path(path) if path else ELECTRIC_POWER_GAS_BY_STATE_PATH
    if not resolved.exists():
        return {}
    frame = pd.read_csv(resolved).dropna(subset=["price_usd_mcf"])
    return {
        (str(r.state), int(r.year), int(r.month)): float(r.price_usd_mcf)
        for r in frame.itertuples()
    }


@lru_cache(maxsize=4)
def _load_iso_weights(path: str | None = None) -> dict[str, dict[str, float]]:
    """Return ``{iso: {state: gas-capacity weight}}``."""
    resolved = Path(path) if path else ISO_GAS_STATE_WEIGHTS_PATH
    if not resolved.exists():
        return {}
    frame = pd.read_csv(resolved)
    out: dict[str, dict[str, float]] = {}
    for r in frame.itertuples():
        out.setdefault(str(r.iso), {})[str(r.state)] = float(r.weight)
    return out


def iso_footprint_basket(
    iso: str,
    year: int,
    prices_path: str | None = None,
    weights_path: str | None = None,
) -> tuple[dict[str, float], float]:
    """Return ``({state: weight}, covered_share)`` for one ISO-year.

    The basket is the ISO's footprint states that print a price in **all
    twelve** months of ``year`` (see the module docstring on why composition
    must be constant within the year); ``covered_share`` is the share of the
    ISO's gas capacity they carry, before renormalization.
    """
    weights = _load_iso_weights(weights_path).get(iso.upper(), {})
    prices = _load_state_prices(prices_path)
    basket = {
        state: weight
        for state, weight in weights.items()
        if all((state, year, month) in prices for month in _MONTHS)
    }
    return basket, float(sum(basket.values()))


def iso_electric_power_monthly_level(
    iso: str,
    year: int,
    prices_path: str | None = None,
    weights_path: str | None = None,
) -> np.ndarray | None:
    """Return the ``(12,)`` measured delivered gas level ($/MMBtu), or ``None``.

    ``None`` means the year is not admissible (see the module docstring) and
    the caller must keep its existing construction unchanged.

    Args:
        iso: ISO identifier.
        year: Calendar year.
        prices_path: Override for the N3045 state CSV (tests).
        weights_path: Override for the ISO weight table (tests).

    Returns:
        A ``(12,)`` array of $/MMBtu indexed January..December, or ``None``.
    """
    basket, covered = iso_footprint_basket(iso, year, prices_path, weights_path)
    if covered <= MIN_FOOTPRINT_COVERAGE:
        return None
    prices = _load_state_prices(prices_path)
    level = np.empty(12, dtype=float)
    for index, month in enumerate(_MONTHS):
        blended = sum(
            weight * prices[(state, year, month)] for state, weight in basket.items()
        )
        level[index] = blended / covered / MCF_TO_MMBTU
    return level


def state_electric_power_monthly_gas(
    state: str,
    year: int,
    prices_path: str | None = None,
) -> np.ndarray | None:
    """Return ONE state's ``(12,)`` measured delivered-to-electric-power gas ($/MMBtu).

    The single-state read of the same N3045 series
    :func:`iso_electric_power_monthly_level` blends. Used where a price is keyed
    to one physical location rather than an ISO footprint — the R-CAISO-3
    intertie-hub gap fill (``ScenarioConfig.caiso_intertie_gap_fill_measured_gas``),
    whose operand is the host state of the hub. A month the state does not
    print is ``NaN`` (never backfilled from ``N3045US3``, per the module
    docstring); ``None`` when the state prints no month of ``year``.

    Args:
        state: Two-letter US state code (e.g. ``"AZ"``).
        year: Calendar year.
        prices_path: Override for the N3045 state CSV (tests).

    Returns:
        A ``(12,)`` array of $/MMBtu indexed January..December, or ``None``.
    """
    prices = _load_state_prices(prices_path)
    out = np.array(
        [prices.get((state.upper(), year, month), np.nan) for month in _MONTHS],
        dtype=float,
    )
    if not np.isfinite(out).any():
        return None
    return out / MCF_TO_MMBTU
