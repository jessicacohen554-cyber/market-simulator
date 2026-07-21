"""NEISO interchange: the winter gas-electric cold-snap derate.

Everything NEISO-specific that lived in ``model/transmission.py``: the
cold-snap availability derate on the non-dual-fuel gas fleet
(:func:`inject_neiso_gas_coldsnap_derate`) and its window/group constants.
Moved INTACT from ``model/transmission.py`` (session 3F,
refactor-consolidation plan §5 item 6); ``transmission`` remains the
full-surface facade.
"""

import numpy as np
import pandas as pd


# Winter cold-snap peak hours (morning HB6-9 + evening HB17-20) — the gas-system
# stress windows the oil/coal/steam reliability fleet covers; an explicit tuple
# of local hours-of-day (two disjoint ranges, not a single [start,end] band).
NEISO_COLDSNAP_FLOOR_HOURS: tuple[int, ...] = (6, 7, 8, 9, 17, 18, 19, 20)


# Gas-fired plant groups exposed to the winter gas-electric constraint (the
# pipeline diverts deliverability to heating on cold snaps). The cold-snap
# availability derate applies to these combined-cycle + combustion-turbine gas
# burners; dual-fuel-capable units are excluded at call time because they switch
# to oil rather than going unavailable. The steam groups (ST_GAS / ST_CHP) are
# deliberately omitted: the lone Merrimack-class steam-gas unit is the COLD-limb
# RELIABILITY runner the temperature floor holds ONLINE in deep cold (it has the
# firm/oil-backed fuel that lets it run when gas is short), so derating it would
# both contradict the floor and risk an infeasible min_gen > available bound.
NEISO_GAS_DERATE_GROUPS: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
)


def inject_neiso_gas_coldsnap_derate(
    fleet_arrays,
    iso: str,
    year: int,
    t0_c: float,
    slope_per_c: float,
    cap: float,
) -> bool:
    """Derate NON-dual-fuel gas-fired availability on deep-winter cold snaps.

    The physical counterpart to the reliability floor's NEISO cold limb
    (a gas-pipeline availability derate, not a must-run commitment). On the
    coldest hours ISO-NE's gas-electric constraint — the
    pipeline diverting deliverability to heating — leaves a share of the
    gas-fired fleet *unable to get fuel*: not merely expensive, physically
    UNAVAILABLE. An energy-only LP that keeps those units available-but-dear
    caps the marginal price at the dual-fuel oil parity (~$258/MWh), never goes
    reserve-short, and so never produces the winter scarcity tail (hours >
    $300/MWh) the real market shows. This derates the available capacity of the
    non-dual-fuel gas groups (:data:`NEISO_GAS_DERATE_GROUPS`) over the cold-snap
    window (:data:`NEISO_COLDSNAP_FLOOR_HOURS`, the winter morning + evening
    peaks where the gas constraint binds hardest) by a temperature-dependent
    forced-outage fraction ``frac = clip(slope_per_c * (t0_c - TMIN), 0, cap)``
    keyed to the NEISO load-weighted daily MIN temperature.

    **Dual-fuel units are excluded.** EIA-860 oil/gas dual-fuel-capable units
    (:func:`market_sim.data.fleet.dual_fuel_plant_groups`) keep running on
    distillate when gas is short — that switch is already modelled by
    :func:`market_sim.data.fuel.apply_dual_fuel_pricing` (their marginal cost
    becomes the oil parity), so derating them too would double-count the
    constraint and wrongly remove deliverable oil-backed capacity.

    Pairs with the NEISO reserve co-optimization (``energy_reserve_coopt``): the
    derate is what makes the cold-hour fleet genuinely short of its operating-
    reserve requirement, so the RCPF demand curve binds and prices scarcity into
    the energy LMP (and widens the peak/trough spread that storage arbitrages).
    The magnitude (:data:`ScenarioConfig.neiso_gas_derate_cap` etc.) traces to
    the NERC/FERC cold-weather forced-outage record (Winter Storm Elliott: gas
    fuel-supply ~20% of unplanned outages, the largest forced-out category),
    keyed to TMIN — forward-reproducible and condition-responsive, NOT fitted to
    the number of >$300 hours.

    Modifies ``fleet_arrays.availability`` in place (multiplicative, composed
    with the existing CAMPD outage overlay). Returns ``True`` when any gas
    capacity was derated, ``False`` (byte-identical) when ``iso`` is not NEISO,
    no archived TMIN series is available, or no eligible non-dual-fuel gas unit
    exists.
    """
    if iso != "NEISO":
        return False
    if fleet_arrays.plant_group is None or fleet_arrays.plant_code is None:
        return False
    if slope_per_c <= 0.0 or cap <= 0.0:
        return False
    from market_sim.data.eia_loader import neiso_load_weighted_temp
    from market_sim.data.fleet import dual_fuel_plant_groups

    hours = int(fleet_arrays.availability.shape[1])
    temp = neiso_load_weighted_temp(year, hours)
    if temp is None:
        return False
    _tmax, tmin = temp

    groups = np.asarray(fleet_arrays.plant_group)
    plant_codes = np.asarray(fleet_arrays.plant_code)
    is_gas = np.isin(groups, np.asarray(NEISO_GAS_DERATE_GROUPS))
    dual = dual_fuel_plant_groups()
    is_dual = np.array(
        [(int(plant_codes[i]), str(groups[i])) in dual for i in range(groups.size)],
        dtype=bool,
    )
    rows = np.flatnonzero(is_gas & ~is_dual & (fleet_arrays.pmax > 0.0))
    if rows.size == 0:
        return False

    # Temperature-dependent forced-outage fraction, cold-snap window only.
    frac = np.clip(slope_per_c * (t0_c - tmin), 0.0, cap)
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    window = np.isin(clock.hour.to_numpy(), np.asarray(NEISO_COLDSNAP_FLOOR_HOURS))
    frac = np.where(window, frac, 0.0)
    if not np.any(frac > 0.0):
        return False

    fleet_arrays.availability[rows, :] *= (1.0 - frac)[None, :]
    return True
