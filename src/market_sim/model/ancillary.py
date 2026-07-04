"""ERCOT ancillary-service (AS) market revenue for capacity economics.

A calibrated, exogenous AS revenue stream credited in the retirement,
new-entry and storage-entry screens — the AS analogue of the ORDC scarcity
overlay. ERCOT's energy-only design pays no capacity revenue, but resources
earn a material AS income (Reg-Up/Down, RRS, ECRS, Non-Spin) that the
energy-only LP cannot produce: in 2023 ancillary services were ~85% of
ERCOT battery revenue (~$169/kW-yr of a ~$196/kW total; IMM 2023 State of
the Market / Modo Energy). Omitting it undervalues storage ~6x and makes
the tail thermal under-earn, biasing the capacity-expansion loop toward
over-retirement and under-build.

This is NOT an AS co-optimization (explicitly out of scope, see
docs/ordc-overlay.md). It is a per-technology $/kW-yr rate
(``constants.ERCOT_AS_REVENUE_PER_KW_YR``) with a **saturation** decline:
AS is a small, quickly-saturated market, so per-kW revenue falls steeply as
the AS-eligible (mostly storage) fleet grows. Modo reports ERCOT battery AS
revenue fell ~90% from 2023 to 2025 as the fleet scaled — without the
saturation a forecast would over-build storage forever on a static AS rate.

Gated on ``ScenarioConfig.as_revenue_enabled`` and ERCOT only; returns 0
otherwise, so the default (off) is byte-identical and capacity-market ISOs
are untouched.

**Endogenous alternative (one mechanism per phenomenon, CLAUDE.md rule 19).**
This exogenous credit and the endogenous reserve co-optimization
(``ercot_storage_as_endogenous``) are two pricings of the *same* storage AS
duty and must never both apply to a resource. When the co-opt prices storage
AS, the storage new-entry screen credits the AS value **derived from the
solved co-opt's own reserve duals** — :func:`realized_storage_as_revenue_per_mw_yr`
below — and the exogenous :func:`as_revenue_per_mw_yr` is suppressed for
storage (see ``model.storage.apply_storage_new_entry``). The exogenous rate
remains the sole storage AS credit only when the endogenous flag is off (the
legacy/backcast-validation path). Thermal AS still uses the exogenous rate in
both regimes (the storage-scoped ``ercot_storage_as_endogenous`` does not
govern thermal; the thermal double-count under the co-opt is a labelled seam
in ``docs/storage-as-withholding-attribution-2026-07.md``).
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import (
    ERCOT_AS_REVENUE_PER_KW_YR,
    ERCOT_AS_SATURATION_EXPONENT,
    ERCOT_AS_SATURATION_REF_GW,
)
from market_sim.config.scenarios import ScenarioConfig


def as_saturation_factor(storage_power_mw: float) -> float:
    """Return the AS-revenue saturation multiplier in (0, 1].

    ``(ref_gw / max(storage_gw, ref_gw)) ** exponent`` — 1.0 at or below the
    calibration-point fleet, falling steeply as the AS-eligible (mostly
    storage) fleet grows past it.
    """
    storage_gw = max(0.0, float(storage_power_mw)) / 1000.0
    ref = ERCOT_AS_SATURATION_REF_GW
    if ref <= 0.0:
        return 1.0
    return (ref / max(storage_gw, ref)) ** ERCOT_AS_SATURATION_EXPONENT


def as_revenue_per_mw_yr(
    fuel_type: str,
    storage_power_mw: float,
    config: ScenarioConfig,
) -> float:
    """Return ancillary-service revenue in $/MW-yr for a technology.

    The calibrated per-kW base rate for ``fuel_type`` (storage / gas_ct /
    gas_st / gas_cc) scaled by ``config.as_revenue_multiplier`` and the
    saturation factor for the current AS-eligible fleet, converted to
    $/MW-yr. Returns 0 when AS revenue is disabled, the ISO is not ERCOT, or
    the technology earns no AS.

    Args:
        fuel_type: Generator fuel type or ``"storage"``.
        storage_power_mw: Current AS-eligible (storage) fleet power in MW,
            the saturation driver.
        config: Scenario config (toggle, ISO, scenario multiplier).

    Returns:
        AS revenue in $/MW-yr.
    """
    if not config.as_revenue_enabled or config.iso != "ERCOT":
        return 0.0
    base_per_kw = ERCOT_AS_REVENUE_PER_KW_YR.get(fuel_type, 0.0)
    if base_per_kw <= 0.0:
        return 0.0
    per_kw = (
        base_per_kw
        * config.as_revenue_multiplier
        * as_saturation_factor(storage_power_mw)
    )
    return per_kw * 1000.0


def realized_storage_as_revenue_per_mw_yr(
    reserve_price_by_family: np.ndarray | None,
    reserve_dispatch: np.ndarray | None,
    storage_charge: np.ndarray | None,
    storage_discharge: np.ndarray | None,
    storage_power_cap: np.ndarray | float,
    storage_zone_idx: np.ndarray,
    n_zones: int,
) -> float:
    """Storage AS revenue in $/MW-yr recovered from a solved reserve co-opt.

    The endogenous analogue of :func:`as_revenue_per_mw_yr`: instead of a
    calibrated exogenous rate, this reads the battery's AS income straight off
    the co-optimization's own LP duals, so under
    ``ercot_storage_as_endogenous`` exactly one mechanism prices storage AS
    (CLAUDE.md rule 19). It is a *forward* quantity — it responds to the fleet,
    the AS requirement and the energy spreads of the year that was solved, and
    it goes to zero as the fleet grows and the AS price collapses, with no
    measured award anywhere in the path (rule 13).

    Realized revenue = ``Σ_t (storage cleared reserve MW)_t × (binding AS
    price)_t``, annualized per MW of storage power:

    * cleared reserve attributed to storage via
      :func:`market_sim.model.dispatch.storage_reserve_mw` (the storage-first
      opportunity-cost attribution, an upper bound when storage is not the
      marginal fast-AS provider — see that helper's docstring);
    * priced at the per-hour binding AS clearing price, the max across reserve
      families of ``reserve_price_by_family`` (each ERCOT AS product is a
      family; a battery clears the dearest product it is eligible for).

    Fully vectorized (no hour loop). Returns 0.0 when the co-opt did not run
    (``reserve_price_by_family``/``reserve_dispatch`` is ``None``) or the fleet
    has no power — so a config that names the endogenous flag but never priced
    reserve simply credits no storage AS (and the caller's footgun guard warns).

    Args:
        reserve_price_by_family: ``(T, n_families)`` per-product reserve
            clearing price (``DispatchResult.reserve_price_by_family``).
        reserve_dispatch: ``(n_reserve_cols, T)`` cleared reserve, zone-minor
            (``DispatchResult.reserve_dispatch``).
        storage_charge: ``(n_storage, T)`` cleared charge MW.
        storage_discharge: ``(n_storage, T)`` cleared discharge MW.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` power cap MW.
        storage_zone_idx: ``(n_storage,)`` zone index of each storage unit.
        n_zones: Number of model zones (the reserve block is zone-minor over
            these, so ``n_reserve_classes = n_reserve_cols // n_zones``).

    Returns:
        Storage AS revenue in $/MW-yr (0.0 if unpriced or empty fleet).
    """
    if reserve_price_by_family is None or reserve_dispatch is None:
        return 0.0
    from market_sim.model.dispatch import storage_reserve_mw

    rd = np.asarray(reserve_dispatch, dtype=float)
    rp = np.asarray(reserve_price_by_family, dtype=float)
    if rd.ndim != 2 or rp.ndim != 2 or n_zones <= 0:
        return 0.0
    n_reserve_cols = rd.shape[0]
    if n_reserve_cols % int(n_zones) != 0:
        return 0.0
    n_reserve_classes = n_reserve_cols // int(n_zones)
    cap = np.asarray(storage_power_cap, dtype=float)
    total_mw = float(cap.sum()) if cap.ndim == 1 else float(cap.sum(axis=0).max())
    if total_mw <= 0.0:
        return 0.0
    # Storage's share of the cleared reserve, (n_zones, T), summed over zones.
    s_res = storage_reserve_mw(
        rd,
        storage_charge,
        storage_discharge,
        storage_power_cap,
        storage_zone_idx,
        n_reserve_classes,
    ).sum(axis=0)  # (T,)
    # Per-hour binding AS price (dearest product the battery can clear).
    price_t = rp.max(axis=1) if rp.shape[1] else np.zeros(rp.shape[0])
    annual_rev = float(np.dot(s_res, price_t))  # $ over the solved year
    return annual_rev / total_mw
