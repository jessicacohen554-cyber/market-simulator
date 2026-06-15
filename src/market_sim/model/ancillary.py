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
"""
from __future__ import annotations

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
