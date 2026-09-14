"""Forecast-grade neighbor reference prices for the interchange seam.

This is step (1) of the reference-price interface (model-methodology-spec
§8.3): a pure, ISO-agnostic construction of each neighboring balancing
authority's hourly energy price, plus the ISO↔neighbor spread that drives
seam flow. No LP is touched here — the module is a self-contained data layer
that can be validated against the measured net-interchange *before* it is
wired into dispatch (see :mod:`scripts.validate_neighbor_price`).

The fitted ``IMPORT_TRANCHES`` / ``EXPORT_TRANCHES`` it is meant to replace
price each seam block at a constant tuned to the ISO's net-interchange
duration curve. That is a backcast fit — re-fitted per year, blind to
neighbor fundamentals. Here the neighbor's price is built from forward
drivers instead:

    neighbor_price[h] = (henry_hub[year] + gas_basis) x marginal_heat_rate
                        x load_shape(neighbor_load[h])

* ``henry_hub[year]`` and ``gas_basis`` give the neighbor's *delivered* gas
  price — the same Henry Hub trajectory the ISO's own gas burn prices off,
  shifted by the neighbor hub's basis.
* ``marginal_heat_rate`` (~7.5 MMBtu/MWh) is the neighbor's price-setting
  gas unit; gas x HR is the baseload marginal energy cost.
* ``load_shape`` is the neighbor's own normalized hourly load raised to a
  convexity exponent (default 1.0 = mean-preserving, parameter-free), so the
  price rises in the neighbor's tight hours and falls in its slack hours
  exactly as climbing/descending its offer stack would.

Every term is a forecast input or a physically-pinned constant; nothing is
tuned to the net-MWh target. The seam then clears on the spread against the
ISO's own price, with a hurdle dead-band and the real interface limit:

    import when ISO_price > neighbor_price + hurdle
    export when ISO_price < neighbor_price - hurdle
    |flow| <= interface_limit_mw

Each neighbor in :data:`~market_sim.config.interchange_config.INTERFACE_NEIGHBORS`
prices individually when its EIA-930 load extract (or a proxy) is present;
neighbors with neither fold into a capacity-weighted aggregate. So the seam
is neighbor-resolved where the data supports it and gracefully aggregate
where it does not — add a neighbor's extract later and it lights up
individually with no code change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.constants import HENRY_HUB_TRAJECTORIES
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS, NeighborInterface
from market_sim.data.eia_loader import _eia_hourly_frame_filled
from market_sim.data.fuel.trajectories import _hold_flat_extrapolate

if TYPE_CHECKING:
    from market_sim.config.interchange_config import CaisoHubNeighbor


# FORWARD-SKILL validation values (:func:`neighbor_heat_rate`'s
# ``forward_skill`` parameter): force the seam off the measured per-year
# ``hr_by_year`` anchor so a backcast year is priced by the SAME forward
# formula a forecast year would use, then scored against the held-out
# actuals. Default ``None`` (off), so keepers (which legitimately price
# backcast years off the measured anchor, rule #12) are byte-identical.
#   "elastic" -> skip hr_by_year, use the gas-elastic coeffs (the forward fallback)
#   "flat"    -> skip hr_by_year AND the elastic coeffs, use marginal_heat_rate
# This NEVER reads the ISO's own interchange — it only changes which neighbor
# price-formation formula prices the seam (rule #11 stays satisfied). Sourced
# from ``ScenarioConfig.neighbor_hr_forward_skill`` (CLAUDE.md rule 23 — no
# off-registry tuning channel), threaded down from
# ``transmission.apply_interchange_injections`` through every call in this
# module; a validation script may still pass it explicitly.
_FORWARD_SKILL_MODES: frozenset[str] = frozenset({"elastic", "flat"})

# Affine-in-gas implied heat-rate coefficients per neighbor, keyed by the
# neighbor's name. Each ``(hr_phys, hr_adder)`` makes the neighbor's implied HR
# ``= hr_phys + hr_adder / gas`` — the neighbor's realized annual-mean LMP is
# affine in delivered gas (``LMP = hr_phys x gas + hr_adder``), so the implied HR
# eases toward the gas-proportional ``hr_phys`` as gas rises and the seam reprices
# as the Henry Hub trajectory moves, instead of riding a flat multi-year mean (the
# gap in docs/forecast-methodology-gaps-2026-06.md G11). Fit to each neighbor's OWN
# measured ``(gas, LMP)`` points — blind to the ISO's interchange (rule #11).
#
# Two families of neighbor live here, distinguished by whether the neighbor has a
# per-year ``hr_by_year`` anchor:
#
#   * **Organized-market neighbors with ``hr_by_year`` (MISO's PJM/SPP seams).**
#     Backcast years use the measured per-year realized LMP anchor (rule #12); the
#     affine coefficients price only FORECAST years (and the forward-skill
#     validation). Fit by scripts/data/derive_neighbor_hr_elasticity.py.
#   * **Coal/nuclear-set neighbors with NO organized-market LMP (PJM's Southeast
#     seams: Carolinas/TVA/LGEE).** SERC has no nodal LMP to anchor a per-year HR
#     to, so the affine fuel-stack form is the neighbor's price-formation anchor in
#     EVERY year (backcast and forward alike — there is no ``hr_by_year`` to take
#     precedence). The coefficients are the OLS of the Southeast's documented
#     Into-Southern/SERC hub price level on Henry Hub (a measured neighbor
#     price-formation series, rule #12), NOT PJM's net-MWh flow (rule #11). They
#     give a GAS-INELASTIC slope (hr_phys ~5.6, far below the flat 11.6) so the
#     coal/nuclear Southeast does not ride Henry Hub up in a dear-gas year: at the
#     flat 11.6 the seam priced to $40.8 in 2025 — only ~$2 below PJM — and the
#     diurnal swing flipped it to a wrong-direction export (+2.0 TWh vs the
#     measured −5.9); the affine form holds it at ~$33.9 (~$9 below PJM), so the
#     structural net-import direction holds across the gas cycle. Derived/checked
#     by scripts/data/derive_southeast_inelastic_hr.py.
#
# The keys are neighbor names, and a key is well-defined only while exactly ONE
# ISO registers a neighbour of that name (only MISO has a ``PJM``/``SPP`` seam;
# only PJM has ``Carolinas``/``TVA``/``LGEE``), so this never touches another
# ISO's seam; the map lives here rather than as a NeighborInterface field to
# keep the change localized to the seam-pricing layer. SPP's neighbours (``MISO``
# / ``AECI`` / ``ERCOT``, registered 2026-09-06) carry NO key here — PJM and SPP
# both name a ``MISO`` seam, so a ``"MISO"`` key would price two different
# physical seams off one fit (rule 25 [R-ISO-SCOPE]); the uniqueness check below
# (SPP plan §7 gate G10) fails the import the moment such a key is added.
# SOCO's eight neighbours (registered 2026-09-14, lane SOCO-20) are named
# ``SOCO_<DIBA>`` — ``SOCO_TVA``, ``SOCO_MISO``, ``SOCO_DUK``, ... — precisely
# so they can never collide with PJM's ``TVA`` / ``Carolinas`` keys here or
# with any other ISO's block; they carry NO key (Tier-3 anchors, default-off;
# SOCO plan §7 gate G10), and a fit for them is lever SOCO-56's.
_HR_GAS_ELASTIC: dict[str, tuple[float, float]] = {
    "PJM": (11.06, 3.21),  # MISO's PJM seam: gas-set (large slope, small adder)
    "SPP": (3.04, 16.27),  # MISO's SPP seam: wind-set (small slope, large adder)
    # PJM's Southeast seams — coal/nuclear-set, gas-INELASTIC (no organized LMP;
    # affine fit to Into-Southern/SERC hub level on Henry Hub, all years).
    "Carolinas": (5.6, 14.2),
    "TVA": (5.6, 14.2),
    "LGEE": (5.6, 14.2),
}


def _assert_hr_gas_elastic_keys_unique() -> None:
    """Fail the import if an ``_HR_GAS_ELASTIC`` key names a neighbour of two ISOs.

    The elasticity is looked up by ``NeighborInterface.name`` alone, so a name
    shared by two ISOs' registries (PJM's and SPP's ``MISO`` seams) must never
    acquire a key: it would price two physical seams, fit on one ISO's measured
    record, off a single curve (rule 25 [R-ISO-SCOPE]). Every current key is
    owned by exactly one ISO; this guard keeps it so (SPP plan §7, gate G10).
    """
    owners: dict[str, set[str]] = {}
    for iso, neighbors in INTERFACE_NEIGHBORS.items():
        for neighbor in neighbors:
            owners.setdefault(neighbor.name, set()).add(iso)
    shared = sorted(k for k in _HR_GAS_ELASTIC if len(owners.get(k, ())) > 1)
    if shared:
        raise AssertionError(
            "_HR_GAS_ELASTIC key(s) name a neighbour registered by more than one "
            f"ISO: {', '.join(f'{k} -> {sorted(owners[k])}' for k in shared)}; "
            "a per-seam fit never crosses ISO boundaries (rule 25)"
        )


_assert_hr_gas_elastic_keys_unique()


def _hr_gas_elastic(neighbor: NeighborInterface) -> tuple[float, float] | None:
    """Return the neighbor's affine-in-gas ``(hr_phys, hr_adder)`` or ``None``.

    For organized-market neighbors (``hr_by_year`` present) these price forecast
    years only; for coal/nuclear-set neighbors with no organized LMP (the
    Southeast) they price every year. See :data:`_HR_GAS_ELASTIC`.
    """
    return _HR_GAS_ELASTIC.get(neighbor.name)


def neighbor_heat_rate(
    neighbor: NeighborInterface,
    year: int,
    gas_scenario: str = "mid",
    forward_skill: str | None = None,
) -> float:
    """Return the neighbor's effective marginal heat rate for ``year`` (MMBtu/MWh).

    Resolution order:

    1. **Backcast realization** — the per-year measured anchor in
       ``neighbor.hr_by_year`` (re-anchored to the neighbor's OWN realized
       annual-mean LMP for that year), used whenever the year is tabulated. This
       is the measured price-formation input the elasticity is fit and validated
       against (claude.md rule #12: measured for the backcast).
    2. **Forward gas-elastic implied HR** — for any year NOT tabulated (every
       forecast year), ``hr_phys + hr_adder / gas`` from :data:`_HR_GAS_ELASTIC`
       when the neighbor has a fit. The neighbor's realized LMP is affine in
       delivered gas (``LMP = hr_phys x gas + hr_adder``), so the implied HR eases
       toward the gas-proportional ``hr_phys`` as gas rises — the seam reprices
       forward as the Henry Hub trajectory moves WITHOUT reading the neighbor's
       realized LMP for a future year. The coefficients are blind to the ISO's
       interchange (rule #11).
    3. **Flat structural fallback** — ``marginal_heat_rate`` when no elasticity
       is fit (neighbors with no organized-market LMP, e.g. the Carolinas), so
       those forecast runs stay byte-identical.

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        gas_scenario: Henry Hub trajectory key (only consulted on the elastic
            forward path).
        forward_skill: ``"elastic"``/``"flat"``/``None`` — see
            :data:`_FORWARD_SKILL_MODES`. ``None`` (the default, used by every
            keeper and forecast run) prices backcast years off the measured
            anchor; unrecognized values are treated as ``None``.
    """
    skill = forward_skill if forward_skill in _FORWARD_SKILL_MODES else None
    if skill is None and neighbor.hr_by_year and year in neighbor.hr_by_year:
        return neighbor.hr_by_year[year]
    coeffs = None if skill == "flat" else _hr_gas_elastic(neighbor)
    if coeffs is not None:
        hr_phys, hr_adder = coeffs
        gas = neighbor_gas_price(neighbor, year, gas_scenario)
        return hr_phys + hr_adder / gas
    return neighbor.marginal_heat_rate


#: Scenario-key prefix of the AS-KNOWN-THEN hindcast gas paths
#: (``hindcast_asknown_aeo<edition>``), whose entire purpose is to price a
#: hindcast year with ONLY the information available at the time. The measured
#: pre-first-knot path below is REFUSED for these keys — see
#: :func:`_measured_henry_hub_annual` and ``neighbor_gas_price``.
_HINDCAST_ASKNOWN_PREFIX: str = "hindcast_asknown_"

#: Months a calendar year must carry in the measured monthly spot series before
#: its annual mean is admissible as a Henry Hub level. A partial year (the
#: extract's forward edge — H1-2026 carries 6) would otherwise yield a
#: half-year mean dressed as an annual one; such a year falls back to the
#: hold-flat rule instead. Not a tunable: it is the definition of "annual".
_MEASURED_HENRY_HUB_MONTHS: int = 12


def _measured_henry_hub_annual(year: int) -> float | None:
    """Return the measured Henry Hub spot annual mean ($/MMBtu) for ``year``.

    The mean of the twelve monthly EIA Henry Hub spot prices in
    ``data/raw/gas-prices/henry_hub_monthly.csv`` — the SAME series
    :data:`~market_sim.config.constants.HENRY_HUB_TRAJECTORIES` cites for its
    own historical knots (``fuel_trajectories`` "hindcast_realized": *"the
    annual mean of data/raw/gas-prices/henry_hub_monthly.csv (EIA Henry Hub
    spot)"*), read through the ``market_sim.data.fuel`` package namespace so
    the loader's monkeypatch seam and its path cache are shared rather than
    duplicated.

    Rule 13 ``[R-MEASURED]`` admissibility: a published physical fuel price,
    not a model outcome, entering as a formulaic input; the identical
    construction regenerates for any year the EIA series covers and responds to
    nothing but that series. Rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``: zero
    free parameters and no new ``ScenarioConfig`` field — the values are
    2019 **2.5651** · 2020 **2.0337** · 2021 **3.9097** · 2022 **6.4191**.

    Args:
        year: Calendar year.

    Returns:
        The annual mean in $/MMBtu, or ``None`` when the series does not carry
        a COMPLETE year (:data:`_MEASURED_HENRY_HUB_MONTHS` months) — a missing
        year or the extract's partial forward edge — in which case the caller
        keeps the hold-flat rule.
    """
    from market_sim.data.fuel import _henry_hub_monthly

    monthly = _henry_hub_monthly(None)
    months = [
        price for (row_year, _month), price in monthly.items() if row_year == int(year)
    ]
    if len(months) != _MEASURED_HENRY_HUB_MONTHS:
        return None
    return sum(months) / float(_MEASURED_HENRY_HUB_MONTHS)


def neighbor_gas_price(
    neighbor: NeighborInterface, year: int, gas_scenario: str = "mid"
) -> float:
    """Return the neighbor's delivered gas price ($/MMBtu) for ``year``.

    Henry Hub annual average for ``year`` (from
    :data:`~market_sim.config.constants.HENRY_HUB_TRAJECTORIES`, which carries
    the historical values for backcast years identically across scenarios)
    shifted by the neighbor hub's basis. Mirrors the ISO's own gas pricing so
    a neighbor and its bordering ISO see the same Henry Hub level.

    **The pre-first-knot measured path (pjm-172, card F-A).** That contract used
    to break below the trajectory's FIRST knot. ``low``/``mid``/``high`` begin
    at 2023, and :func:`_hold_flat_extrapolate` hands every earlier year that
    2023 knot ($2.54) while the ISO's own units burn the measured year price —
    a **-32 % error in 2021 and -61 % in 2022**, binding wherever
    ``reference_price_interface`` is armed on a pre-2023 year
    (``results/calibration/ADDENDUM-pjm171-seam-fuel-basis-freeze-2026-09-07.md``).
    A year below the first knot therefore resolves its Henry Hub level from the
    measured annual series (:func:`_measured_henry_hub_annual`) instead. The
    neighbour's own ``gas_basis`` is applied unchanged, so the seam keeps its
    existing basis structure, and the repair is SEAM-LOCAL by owner decision
    (2026-09-07) — ``HENRY_HUB_TRAJECTORIES`` is not edited.

    **INERT ABOVE THE FIRST KNOT BY CONSTRUCTION.** The branch cannot execute
    when ``year`` is a knot or beyond one, which is every training year
    (2023/2024/2025) and every forecast year through 2050 on every scenario
    key; those paths are bit-identical. Asserted by
    ``tests/unit/data/test_neighbor_price_measured_gas.py``, not argued.

    **THE LOOK-AHEAD REFUSAL.** ``hindcast_asknown_*`` paths
    (:data:`_HINDCAST_ASKNOWN_PREFIX`) exist to price a hindcast year with only
    the information available at the time, so injecting a REALIZED price there
    would be look-ahead contamination — ``run_capacity_hindcast`` reaches this
    function under exactly those keys. They keep the hold-flat rule
    unconditionally. ``hindcast_realized`` already carries its own 2021 knot and
    never enters the branch.

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        gas_scenario: Henry Hub trajectory key (``"low"``/``"mid"``/``"high"``,
            or a ``hindcast_*`` path on the hindcast harness); backcast years
            are identical across keys.

    Returns:
        Delivered gas price in $/MMBtu.

    Raises:
        KeyError: if ``gas_scenario`` is not a known trajectory.
    """
    # Hold the nearest known knot flat off the ends of the trajectory, exactly
    # as the ISO's own gas resolver does (data.fuel.resolve_annual_gas_price)
    # — the docstring's contract is that "a neighbor and its bordering ISO see
    # the same Henry Hub level", and a raw dict index broke it: the ISO held
    # flat past the last knot while the seam raised KeyError (audit FR-9,
    # fixed in FFR-2A). Byte-identical wherever the year is a knot, which is
    # every backcast year and every AEO forecast year through 2050. WHICH
    # trajectory a crossover forward year rides is decided upstream by
    # data.fuel.resolve_gas_scenario_path and asserted per-year by
    # run_capacity_hindcast.assert_forward_drivers — this hold-flat is the
    # end-of-trajectory rule, never a licence to hold a measured path forward.
    trajectory = HENRY_HUB_TRAJECTORIES[gas_scenario]
    henry_hub = _hold_flat_extrapolate(trajectory, year)
    # pjm-172 F-A: below the trajectory's FIRST knot the hold-flat rule states a
    # level the source data does not support for that year, and the measured
    # series does. Refused for the as-known-then paths (look-ahead), and
    # unreachable for any year at or above the first knot.
    if int(year) < min(trajectory) and not gas_scenario.startswith(
        _HINDCAST_ASKNOWN_PREFIX
    ):
        measured = _measured_henry_hub_annual(year)
        if measured is not None:
            henry_hub = measured
    return henry_hub + neighbor.gas_basis


def neighbor_load_shape(
    neighbor: NeighborInterface, year: int, hours: int
) -> tuple[np.ndarray, str] | None:
    """Return the neighbor's normalized hourly load shape and the BA used.

    The shape is ``(load[h] / mean(load)) ** load_shape_exponent`` — a
    dimensionless multiplier whose mean is 1.0 at the default exponent 1.0, so
    multiplying the baseload gas-times-heat-rate price by it preserves the
    annual-average price while tracking the neighbor's hourly tightness. The
    load series is the EIA-930 ``Demand`` column for ``neighbor.ba_code``;
    when that extract is absent the ``proxy_ba`` series stands in (the seam
    still prices individually, just on a one-step-removed load shape).

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        hours: Expected length of the series (the model's 8760 clock).

    Returns:
        ``(shape, ba_used)`` where ``shape`` is the ``(hours,)`` multiplier
        and ``ba_used`` is the BA code whose load produced it (the primary or
        the proxy), or ``None`` when neither extract yields a usable series.
    """
    loaded = _neighbor_load(neighbor, year, hours)
    if loaded is None:
        return None
    load, mean_load, ba = loaded
    shape = (load / mean_load) ** neighbor.load_shape_exponent
    return shape, ba


def _neighbor_load(
    neighbor: NeighborInterface, year: int, hours: int
) -> tuple[np.ndarray, float, str] | None:
    """Return the neighbor's raw hourly load (MW), its mean, and the BA used.

    The shared front-end of :func:`neighbor_load_shape` and
    :func:`seam_tranche_prices`: it resolves the EIA-930 ``Demand`` series for
    ``neighbor.ba_code`` (or ``proxy_ba`` when the primary extract is absent),
    sliced to the model's clock. Returns ``None`` when neither extract yields a
    usable ``(hours,)`` series.
    """
    kind = getattr(neighbor, "load_shape_kind", "gross")
    for ba in (neighbor.ba_code, neighbor.proxy_ba):
        if ba is None:
            continue
        frame = _eia_hourly_frame_filled(ba, year)
        if frame is None or "Demand" not in frame.columns:
            continue
        demand = pd.to_numeric(frame["Demand"], errors="coerce")
        driver = demand
        if kind == "net":
            # Net load = demand − utility solar − wind, so a solar-driven
            # neighbor's price troughs midday with the solar glut rather than
            # tracking a gross-load peak (the desert-SW / Palo Verde corridor,
            # proxied off the CISO extract). Gross neighbors (every PJM/MISO
            # seam) skip this branch and stay byte-identical.
            solar = pd.to_numeric(frame.get("NG: SUN"), errors="coerce").fillna(0.0)
            wind = pd.to_numeric(frame.get("NG: WND"), errors="coerce").fillna(0.0)
            driver = demand - solar - wind
        load = driver.interpolate().bfill().ffill().to_numpy(dtype=float)
        # The extract is on the model's 8760 clock; a short-horizon run (hours
        # < 8760) takes the leading window, matching how demand is sliced. A
        # run asking for MORE hours than the extract has is unservable.
        if load.shape[0] < hours or np.isnan(load).any():
            continue
        load = load[:hours]
        mean_load = float(load.mean())
        if mean_load <= 0.0:
            continue
        return load, mean_load, ba
    return None


def neighbor_reference_price(
    neighbor: NeighborInterface,
    year: int,
    hours: int,
    gas_scenario: str = "mid",
    forward_skill: str | None = None,
) -> tuple[np.ndarray, str] | None:
    """Return the neighbor's hourly reference price ($/MWh) and the BA used.

    ``gas x heat_rate x load_shape`` — the forecast-native construction
    described in the module docstring. Returns ``None`` (no individual price)
    when the neighbor has no resolvable load shape, leaving it to fold into
    the aggregate.

    Args:
        neighbor: The seam specification.
        year: Calendar year.
        hours: Length of the hourly series.
        gas_scenario: Henry Hub trajectory key.
        forward_skill: Forwarded to :func:`neighbor_heat_rate` — see
            :data:`_FORWARD_SKILL_MODES`. ``None`` (default) is byte-identical
            to every keeper/forecast run.

    Returns:
        ``(price, ba_used)`` or ``None``.
    """
    shaped = neighbor_load_shape(neighbor, year, hours)
    if shaped is None:
        return None
    shape, ba_used = shaped
    baseload = neighbor_gas_price(neighbor, year, gas_scenario)
    baseload *= neighbor_heat_rate(neighbor, year, gas_scenario, forward_skill)
    return baseload * shape, ba_used


# Number of piecewise-linear tranches the flow-responsive seam splits each
# neighbor's [0, limit] import and export ranges into. The neighbor price is
# evaluated at the midpoint flow of each tranche, so the seam sees a stepped
# approximation of the neighbor's downward-sloping import-demand curve; 8 steps
# resolves the slope finely enough that the export self-limits smoothly without
# materially enlarging the LP (8 x 2 rows x 3 PJM neighbors = 48 seam rows).
SEAM_FLOW_TRANCHES: int = 8


def seam_tranche_prices(
    neighbor: NeighborInterface,
    year: int,
    hours: int,
    n_tranches: int = SEAM_FLOW_TRANCHES,
    gas_scenario: str = "mid",
    forward_skill: str | None = None,
) -> tuple[np.ndarray, np.ndarray, str] | None:
    """Return the flow-responsive export/import tranche prices for one seam.

    The flat :func:`neighbor_reference_price` holds the neighbor's price fixed
    regardless of how much the ISO exports into it, so the LP exports at the
    interface limit whenever the spread is positive (the ``pjm_30`` over-export).
    This makes the price **respond to the flow**: exporting ``E`` MW into the
    neighbor displaces that much of the neighbor's native generation, so its
    price is evaluated at its load *reduced* by ``E`` — sliding the
    willingness-to-pay down the neighbor's own ``gas x HR x (load/mean)^exp``
    supply curve. Importing ``I`` MW raises the neighbor's effective load by
    ``I`` (it must generate the export), lifting the price the ISO pays. As the
    ISO exports more the spread narrows and the flow self-limits at the economic
    equilibrium, instead of pinning at the cap.

    The slope is the neighbor's own load level and already-calibrated supply
    curve — no parameter is tuned to the net-MWh target (claude.md rule #11).
    Tranche ``k`` (1-based) covers the flow band ``[(k-1)/n, k/n] x limit`` and
    is priced at its **midpoint** flow ``(k-0.5)/n x limit``; the per-tranche
    hurdle is applied by the LP injector, not here.

    Args:
        neighbor: The seam specification (supplies the interface limit, heat
            rate, gas basis and load-shape exponent).
        year: Calendar year.
        hours: Length of the hourly series.
        n_tranches: Number of flow bands per direction.
        gas_scenario: Henry Hub trajectory key.
        forward_skill: Forwarded to :func:`neighbor_heat_rate` — see
            :data:`_FORWARD_SKILL_MODES`. ``None`` (default) is byte-identical
            to every keeper/forecast run.

    Returns:
        ``(export_prices, import_prices, ba_used)`` where each price array is
        ``(n_tranches, hours)`` — row ``k-1`` is the marginal price of the
        ``k``-th flow band — or ``None`` when the neighbor has no load shape (it
        then falls back to the flat aggregate, which carries no slope).
    """
    loaded = _neighbor_load(neighbor, year, hours)
    if loaded is None:
        return None
    load, mean_load, ba_used = loaded
    baseload = neighbor_gas_price(neighbor, year, gas_scenario)
    baseload *= neighbor_heat_rate(neighbor, year, gas_scenario, forward_skill)
    exp = neighbor.load_shape_exponent
    step = neighbor.interface_limit_mw / n_tranches
    # Midpoint flow of each band: (k-0.5) x step, k = 1..n.
    midpoints = (np.arange(n_tranches, dtype=float) + 0.5) * step
    # Effective load floored at 5% of mean so a band wider than a low-load hour
    # cannot drive the price to zero or negative (it asymptotes to a cheap
    # floor instead). load[h] - E for export, load[h] + I for import.
    floor = 0.05 * mean_load
    export_eff = np.clip(load[None, :] - midpoints[:, None], floor, None)
    import_eff = load[None, :] + midpoints[:, None]
    export_prices = baseload * (export_eff / mean_load) ** exp
    import_prices = baseload * (import_eff / mean_load) ** exp
    return export_prices, import_prices, ba_used


# ---------------------------------------------------------------------------
# CAISO per-hub WECC corridor forward reference price (Malin / Palo Verde)
# ---------------------------------------------------------------------------
# The forward-native price for each CAISO WECC import corridor, the analogue of
# the PJM/MISO neighbor reference price specialized to the two physical ties.
# Same construction — (henry_hub + gas_basis) × marginal_heat_rate × load_shape
# — but the load shape is built from the EIA-930 CISO extract (the only WECC
# hourly series in-repo; the desert-SW shares CAISO's solar resource), and the
# solar-driven desert-SW corridor shapes on NET load (load − solar − wind) so
# its midday trough rides the solar glut rather than a gross-load peak. Nothing
# here reads the measured Malin/Palo-Verde LMP (the honesty line, CLAUDE.md
# #10/#12); that series is only the backcast realization the formula validates
# against.


def caiso_hub_load_shape(
    spec: "CaisoHubNeighbor", year: int, hours: int
) -> np.ndarray | None:
    """Return the CAISO corridor's normalized hourly price-shape multiplier.

    Reads the EIA-930 CISO extract on the model's local 8760 clock and builds a
    dimensionless multiplier whose mean is ~1.0 at the default exponent, so
    multiplying the corridor's ``gas × heat_rate`` baseload by it preserves the
    annual-average price. The driver is the region's GROSS load (the hydro-
    following Pacific-NW, ``load_shape_kind="gross"``) or NET load — load minus
    utility solar and wind (the solar-driven desert-SW, ``"net"``), so the
    desert-SW price dips midday with the solar glut. The CISO series proxies the
    neighbor (same solar resource / time zone); it is a forward driver that
    responds to a changed solar build, never the measured hub LMP.

    Args:
        spec: The corridor specification (supplies ``load_shape_kind`` and
            ``load_shape_exponent``).
        year: Calendar year.
        hours: Expected length of the series (the model's 8760 clock).

    Returns:
        The ``(hours,)`` multiplier, or ``None`` when the CISO extract is absent
        or too short (forecast years with no extract fall back to a flat shape).
    """
    frame = _eia_hourly_frame_filled("CISO", year)
    if frame is None or "Demand" not in frame.columns:
        return None
    demand = pd.to_numeric(frame["Demand"], errors="coerce")
    driver = demand
    if spec.load_shape_kind == "net":
        solar = pd.to_numeric(frame.get("NG: SUN"), errors="coerce").fillna(0.0)
        wind = pd.to_numeric(frame.get("NG: WND"), errors="coerce").fillna(0.0)
        driver = demand - solar - wind
    driver = driver.interpolate().bfill().ffill().to_numpy(dtype=float)
    if driver.shape[0] < hours or np.isnan(driver).any():
        return None
    driver = driver[:hours]
    mean = float(driver.mean())
    if mean <= 0.0:
        return None
    # Floor the normalized driver at a small positive value before the exponent
    # so a deep net-load trough cannot drive the price negative or undefined
    # (a fractional exponent of a negative ratio is non-real); the corridor
    # asymptotes to a cheap floor midday instead.
    norm = np.clip(driver / mean, 0.05, None)
    return norm**spec.load_shape_exponent


def caiso_hub_reference_price(
    spec: "CaisoHubNeighbor",
    year: int,
    hours: int,
    gas_scenario: str = "mid",
) -> np.ndarray | None:
    """Return a CAISO corridor's hourly forward reference price ($/MWh).

    ``(henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape`` — the
    forecast-native price the corridor's imports clear against, mirroring
    :func:`neighbor_reference_price` for the two CAISO WECC ties. The level
    rides the forward Henry Hub trajectory; the shape rides the neighbor's own
    hourly tightness (gross load for the Pacific-NW, net load for the solar-
    driven desert-SW). Nothing is read from the measured hub LMP.

    Returns ``None`` when the CISO shape cannot be resolved (the caller then
    leaves the corridor on its static-ladder placeholder price, byte-identical).
    """
    from market_sim.config.constants import HENRY_HUB_TRAJECTORIES

    shape = caiso_hub_load_shape(spec, year, hours)
    if shape is None:
        return None
    # Same end-of-trajectory hold-flat as neighbor_gas_price (audit FR-9).
    henry_hub = _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES[gas_scenario], year)
    baseload = (henry_hub + spec.gas_basis) * (spec.marginal_heat_rate)
    return baseload * shape


@dataclass
class InterfacePrices:
    """Resolved per-neighbor reference prices for one ISO-year seam.

    Attributes:
        iso: ISO identifier.
        year: Calendar year.
        hours: Length of each price series.
        per_neighbor: ``name -> (hours,) $/MWh`` for every neighbor that
            resolved an individual price (own extract or proxy).
        ba_used: ``name -> BA code`` the price shape was built from.
        missing: Neighbor names that resolved no load shape at all (folded
            into the aggregate).
    """

    iso: str
    year: int
    hours: int
    per_neighbor: dict[str, np.ndarray] = field(default_factory=dict)
    ba_used: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)

    def aggregate(self) -> np.ndarray | None:
        """Return the interface-capacity-weighted blend of neighbor prices.

        A single ``(hours,)`` price for the seam as one external node — the
        representation the current single-bubble topology uses and the
        fallback for any neighbor without an individual price. Each resolved
        neighbor is weighted by its ``interface_limit_mw`` (its share of the
        seam's transfer capability). Returns ``None`` when no neighbor
        resolved a price.
        """
        if not self.per_neighbor:
            return None
        specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(self.iso, [])}
        total = np.zeros(self.hours, dtype=float)
        weight_sum = 0.0
        for name, price in self.per_neighbor.items():
            w = specs[name].interface_limit_mw if name in specs else 1.0
            total += w * price
            weight_sum += w
        return total / weight_sum if weight_sum > 0.0 else None


def interface_reference_prices(
    iso: str,
    year: int,
    hours: int,
    gas_scenario: str = "mid",
    forward_skill: str | None = None,
) -> InterfacePrices:
    """Return the reference price for every neighbor of ``iso`` in ``year``.

    Iterates :data:`~market_sim.config.interchange_config.INTERFACE_NEIGHBORS` for the
    ISO, building each neighbor's individual price where its load shape
    resolves and recording the rest as ``missing``. An ISO absent from the
    registry yields an empty result (byte-identical no-op for un-onboarded
    ISOs).

    Args:
        iso: ISO identifier, e.g. ``"PJM"``.
        year: Calendar year.
        hours: Length of the hourly series (the model's 8760 clock).
        gas_scenario: Henry Hub trajectory key.
        forward_skill: Forwarded to :func:`neighbor_heat_rate` via
            :func:`neighbor_reference_price` — see :data:`_FORWARD_SKILL_MODES`.
            ``None`` (default) is byte-identical to every keeper/forecast run.

    Returns:
        An :class:`InterfacePrices` aggregating the per-neighbor results.
    """
    result = InterfacePrices(iso=iso, year=year, hours=hours)
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        priced = neighbor_reference_price(
            neighbor, year, hours, gas_scenario, forward_skill
        )
        if priced is None:
            result.missing.append(neighbor.name)
            continue
        price, ba_used = priced
        result.per_neighbor[neighbor.name] = price
        result.ba_used[neighbor.name] = ba_used
    return result


def seam_flow_direction(
    iso_price: np.ndarray,
    neighbor_price: np.ndarray,
    hurdle: float,
) -> np.ndarray:
    """Return the seam's flow direction per hour from the price spread.

    The hurdle dead-band rule: the ISO imports (+1, draws from the neighbor)
    when its own price exceeds the neighbor price by more than ``hurdle``,
    exports (-1, sells to the neighbor) when its price is below the neighbor
    by more than ``hurdle``, and holds (0) inside the band. The sign matches
    :func:`market_sim.data.eia_loader._eia930_net_interchange` (export
    positive) once negated — exports are sales, so a -1 here is a positive net
    export. Pure, vectorized, no LP.

    Args:
        iso_price: ``(hours,)`` ISO internal price ($/MWh).
        neighbor_price: ``(hours,)`` neighbor reference price ($/MWh).
        hurdle: $/MWh dead-band half-width.

    Returns:
        ``(hours,)`` array of -1 (export), 0 (hold), +1 (import).
    """
    spread = iso_price - neighbor_price
    direction = np.zeros_like(spread)
    direction[spread > hurdle] = 1.0
    direction[spread < -hurdle] = -1.0
    return direction


# ---------------------------------------------------------------------------
# Neighbor LMP loading (realized hourly system price for a modeled neighbor)
# ---------------------------------------------------------------------------
# A neighbor that is itself a modeled ISO (PJM's NYISO neighbor, NYISO's/NEISO's
# PJM neighbor) carries a *realized* hourly LMP the constructed reference price
# is anchored to and validated against (scripts.validate_neighbor_price; the
# convexity fit in scripts.data.derive_neighbor_convexity). That series has always
# been read from the committed realized-LMP product under
# ``paths.CALIBRATION_DIR`` (``actual_lmp_hourly_<ISO>.parquet``: a hub-mean of
# the ISO's trading hubs on the model's fixed non-leap 8760-hour CHRONOLOGICAL
# calendar — slot k is the k-th real hour after local STANDARD midnight Jan 1,
# not the ISO's DST-prevailing wall clock; see ``derive_actual_lmp``).
#
# This block adds a second backend that sources the same series from the curated
# ``data/clean`` tree — ``clean_io.read_clean("lmp", iso=..., market=...,
# year=...)``, the canonical per-node total + components frame — and reduces it
# to the identical hub-mean-on-8760 series. The backend is selected by the
# ``MARKET_SIM_USE_CLEAN`` environment flag and defaults OFF, so the raw path is
# unchanged until the clean tree is explicitly opted into.
#
# "Identical" costs two things, BOTH of which this reduction has to reproduce
# from the realized product (``scripts.data.derive_actual_lmp``) and neither of
# which the clean frame supplies by itself:
#
#   1. **The clock.** The authoritative column is ``interval_start_utc``,
#      converted to the ISO's FIXED STANDARD offset (:data:`_HUB_SPECS`) — the
#      chronological calendar every model series rides. Indexing the frame's
#      other timestamp, the DST-prevailing ``interval_start_local``, lands the
#      series exactly one hour late for every DST hour (~5,700 a year).
#   2. **The hub.** Each ISO's system price is a specific node set with specific
#      weights: CAISO load-weights three trading hubs, NEISO is the internal-hub
#      sheet ALONE, NYISO excludes its four external proxy buses. A simple mean
#      over every node in the partition is a different series.
#
# Both legs were wrong until 2026-08-13. The producer moved to the standard
# clock on 2026-07-15 (``79285e6``, the ERCOT clock artifact) and this consumer
# was not updated, so the two backends silently disagreed by up to $408/MWh on
# PJM 2024 RTM for 28 days while the parity test that would have caught it sat
# behind a CI marker exclusion and a skip-if-absent guard. Diagnosis, the
# per-ISO measurements and the rejected alternatives:
# docs/FINDING-f6-lmp-backend-parity-2026-08-11.md (owner decision D-32,
# option A; resolution docs/handoffs/d32-f6fix-2026-08-13.md).

# Environment flag gating the clean-backed read path (default OFF).
USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"

# Market run -> clean ``market`` partition key. ``run`` mirrors the realized
# product's ``rt`` / ``da`` columns; the clean tree keys on RTM / DAM.
_RUN_TO_MARKET: dict[str, str] = {"rt": "RTM", "da": "DAM"}

# The model's fixed non-leap dispatch calendar (matches scripts.data.derive_actual_lmp
# and market_sim.data.campd): Feb 29 dropped, hours on the fixed standard-time
# clock — never the prevailing (DST) wall clock. See :func:`_std_hour_of_year`.
_LMP_HOURS_PER_YEAR: int = 8760
_DAYS_IN_MONTH: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12)
)


def _use_clean() -> bool:
    """Whether the clean-backed read path is enabled via ``MARKET_SIM_USE_CLEAN``."""
    return os.environ.get(USE_CLEAN_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@dataclass(frozen=True)
class _HubSpec:
    """How one ISO's clean ``lmp`` partition reduces to the model's hub series.

    Attributes:
        std_tz: The ISO's FIXED standard-time zone (``Etc/GMT+N`` == UTC-N, POSIX
            sign) — the chronological clock the model's 8760 calendar rides,
            mirroring ``scripts.data.derive_actual_lmp._STD_TZ``. Never the
            prevailing (DST) zone the market reports label their hours with.
        node_weights: ``node -> weight`` defining the ISO's system hub; a node
            absent from the map carries zero weight and is excluded. ``None``
            takes every node in the partition at equal weight.
    """

    std_tz: str
    node_weights: dict[str, float] | None = None


# NYISO's eleven INTERNAL load zones (``derive_actual_lmp.NYISO_INTERNAL``). The
# realized product's system price is their simple mean; the four external-proxy
# buses (H Q, NPX, O H, PJM) are import nodes, not NY load zones, and are out.
_NYISO_INTERNAL_ZONES: tuple[str, ...] = (
    "WEST",
    "GENESE",
    "CENTRL",
    "NORTH",
    "MHK VL",
    "CAPITL",
    "HUD VL",
    "MILLWD",
    "DUNWOD",
    "N.Y.C.",
    "LONGIL",
)

# The four ISOs ``scripts/data/curate_lmp.py`` curates a clean ``lmp`` partition
# for, each carrying the standard-time offset and the hub definition its realized
# product uses. FAIL-CLOSED: an ISO absent here reduces to ``None`` rather than
# guessing a clock or a hub. ERCOT and MISO have no curated clean partition
# (curate_lmp, "Sources deliberately NOT curated here"), so nothing is lost;
# adding one means declaring its conventions here first.
_HUB_SPECS: dict[str, _HubSpec] = {
    # PJM: the mean of the 12 trading hubs, which is every node the partition
    # carries (the raw export is hub-only), so no node map is needed.
    "PJM": _HubSpec("Etc/GMT+5"),  # EST
    # CAISO: the three trading hubs LOAD-WEIGHTED by zone share, not a simple
    # mean (``derive_actual_lmp.CAISO_HUB_WEIGHTS`` — the same static
    # ``load_share`` values as ``config.iso_configs``).
    "CAISO": _HubSpec(
        "Etc/GMT+8",  # PST
        {
            "TH_NP15_GEN-APND": 0.3969,
            "TH_ZP26_GEN-APND": 0.0646,
            "TH_SP15_GEN-APND": 0.5385,
        },
    ),
    # NYISO: the eleven internal zones at equal weight.
    "NYISO": _HubSpec("Etc/GMT+5", dict.fromkeys(_NYISO_INTERNAL_ZONES, 1.0)),  # EST
    # NEISO: the .H.INTERNAL_HUB sheet ALONE, never the zone mean
    # (``derive_actual_lmp.NEISO_HUB_SHEET``).
    "NEISO": _HubSpec("Etc/GMT+5", {"ISO NE CA": 1.0}),  # EST
}


def _std_hour_of_year(utc: pd.Series, year: int, std_tz: str) -> np.ndarray:
    """Map real instants to the model's chronological non-leap hour-of-year.

    Converts tz-aware UTC stamps to the ISO's fixed standard-time clock and maps
    (month, day, hour) onto the 8760 calendar — slot ``k`` is the k-th real hour
    after local standard midnight Jan 1. Rows outside ``year`` (a boundary spill
    from a locally-keyed partition) and the standard-clock Feb 29 map to -1 for
    the caller to drop. Mirror of
    ``scripts.data.derive_actual_lmp._std_hour_index`` so the clean-backed series
    lands on byte-identical hour slots to the realized product.

    Args:
        utc: Interval-start stamps carrying real instants (tz-aware UTC, or
            anything ``pd.to_datetime(..., utc=True)`` reads as such).
        year: Calendar year the 8760 calendar covers.
        std_tz: The ISO's fixed standard-time zone (see :class:`_HubSpec`).

    Returns:
        ``(len(utc),)`` int array of hour-of-year slots; -1 where out of scope.
    """
    std = pd.DatetimeIndex(pd.to_datetime(utc, utc=True)).tz_convert(std_tz)
    month = np.asarray(std.month)
    day = np.asarray(std.day)
    idx = (
        np.asarray(_MONTH_START_HOUR)[month - 1] + (day - 1) * 24 + np.asarray(std.hour)
    )
    ok = (np.asarray(std.year) == year) & ~((month == 2) & (day == 29))
    return np.where(ok, idx, -1)


def _fill_hourly(series: np.ndarray) -> np.ndarray:
    """Interpolate then back/forward-fill a dense 8760 series (gap-free output).

    The fixed calendar leaves the spring-forward hour empty (and a sparse source
    leaves further gaps); this fills them so downstream arithmetic sees no NaN —
    identical treatment to ``scripts.validate_neighbor_price._actual_lmp``.
    """
    return pd.Series(series).interpolate().bfill().ffill().to_numpy(dtype=float)


def _neighbor_lmp_raw(iso: str, year: int, run: str) -> np.ndarray | None:
    """Read a neighbor's realized hourly LMP from the committed raw product.

    The existing path: ``paths.CALIBRATION_DIR/actual_lmp_hourly_<iso>.parquet``
    (columns ``year``, ``hour``, ``rt``, ``da`` on the 8760 calendar). Returns
    the ``run`` column for ``year`` as a gap-filled ``(8760,)`` array, or
    ``None`` when the product or the year is absent.
    """
    path = paths.CALIBRATION_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    rows = df[df["year"] == year].sort_values("hour")
    if len(rows) != _LMP_HOURS_PER_YEAR or run not in rows.columns:
        return None
    return _fill_hourly(rows[run].to_numpy(dtype=float))


def _neighbor_lmp_clean(
    iso: str, year: int, run: str, market: str | None
) -> np.ndarray | None:
    """Read a neighbor's realized hourly LMP from the curated clean tree.

    Loads the canonical per-node LMP frame (total + components) via
    ``clean_io.read_clean("lmp", iso=iso, market=market, year=year)`` and
    reproduces the realized product's reduction exactly: the ISO's own hub
    (:data:`_HUB_SPECS` node weights) averaged per slot of the model's fixed
    non-leap 8760 calendar, indexed on ``interval_start_utc`` converted to the
    ISO's fixed standard offset. Both halves are load-bearing — see the block
    comment above; indexing ``interval_start_local`` or taking a simple mean over
    every node in the partition reproduces the F6 parity defect.

    Returns ``None`` when the ISO declares no hub spec (fail-closed — the clean
    tree carries only the four ISOs ``curate_lmp.py`` curates) or when the
    partition is absent (regenerate from raw with
    ``python scripts/regenerate_clean.py lmp``).
    """
    # Lazy import: the clean read seam lives under scripts/, off the model
    # package, so importing it eagerly would couple package import to repo-root
    # being on sys.path. The raw (default) path never needs it.
    from scripts.lib.clean_io import clean_exists, read_clean

    spec = _HUB_SPECS.get(iso)
    if spec is None:
        return None
    market = market or _RUN_TO_MARKET[run]
    if not clean_exists("lmp", iso=iso, market=market, year=year):
        return None
    df = read_clean(
        "lmp",
        iso=iso,
        market=market,
        year=year,
        columns=["interval_start_utc", "node", "lmp_usd_per_mwh"],
    )
    hoy = _std_hour_of_year(df["interval_start_utc"], year, spec.std_tz)
    price = pd.to_numeric(df["lmp_usd_per_mwh"], errors="coerce").to_numpy(dtype=float)
    weight = (
        np.ones(len(df), dtype=float)
        if spec.node_weights is None
        else pd.to_numeric(df["node"].map(spec.node_weights), errors="coerce")
        .fillna(0.0)
        .to_numpy(dtype=float)
    )
    # Off-hub nodes weigh 0; drop them along with the out-of-scope slots and any
    # unparseable price, so each slot averages exactly the hub rows the realized
    # product averages (and an hour missing a hub renormalizes over the rest).
    keep = (hoy >= 0) & (weight > 0.0) & np.isfinite(price)
    hoy, price, weight = hoy[keep], price[keep], weight[keep]
    total = np.bincount(hoy, weights=price * weight, minlength=_LMP_HOURS_PER_YEAR)
    norm = np.bincount(hoy, weights=weight, minlength=_LMP_HOURS_PER_YEAR)
    dense = np.divide(
        total, norm, out=np.full(_LMP_HOURS_PER_YEAR, np.nan), where=norm > 0.0
    )
    return _fill_hourly(dense)


def neighbor_lmp_hourly(
    iso: str, year: int, run: str = "rt", *, market: str | None = None
) -> np.ndarray | None:
    """Return a modeled neighbor's realized hourly system LMP ($/MWh), or ``None``.

    The neighbor-LMP loading the validation and convexity steps anchor to. Reads
    the realized hub-mean series on the model's fixed non-leap 8760-hour local
    calendar for the given ISO and ``run`` (``"rt"`` real-time / ``"da"``
    day-ahead). Two interchangeable backends produce the same series:

    * the committed realized-LMP product under ``paths.CALIBRATION_DIR`` (the
      default, unchanged path); and
    * the curated ``data/clean`` LMP tree via :func:`clean_io.read_clean`,
      selected when the ``MARKET_SIM_USE_CLEAN`` environment flag is set.

    Args:
        iso: Modeled-ISO code whose realized LMP is sought (e.g. ``"PJM"``).
        year: Calendar year.
        run: ``"rt"`` (real-time) or ``"da"`` (day-ahead).
        market: Clean ``market`` partition override; defaults to RTM/DAM per
            ``run`` (only consulted on the clean-backed path).

    Returns:
        A gap-filled ``(8760,)`` $/MWh array, or ``None`` when neither the
        requested year nor the partition is available on the active backend.
    """
    if _use_clean():
        return _neighbor_lmp_clean(iso, year, run, market)
    return _neighbor_lmp_raw(iso, year, run)
