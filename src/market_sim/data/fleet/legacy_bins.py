"""Legacy equal-width heat-rate bin aggregation and marginal-cost assembly.

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

import logging
import numpy as np

from market_sim.data.fleet.models import (
    FleetArrays,
    Generator,
)

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")

# Fuel types collapsed into efficiency-bin representative units. Everything
# else -- nuclear, hydro, import (few in number, distinct characteristics)
# and wind/solar (not part of the thermal fleet) -- passes through unchanged.
# Oil and biomass are aggregatable thermal blocks too; including them here
# also means ERCOT's CAMPD-bin path (which sources non-aggregatable fuels
# from EIA-860) excludes the handful of ERCOT oil/biomass units exactly as it
# already excluded their gas_ct-classified predecessors, keeping ERCOT
# dispatch unchanged.
_AGGREGATABLE_FUELS: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "coal", "oil", "biomass"}
)


def _capacity_weighted(units: list[Generator], attr: str) -> float:
    """Return the capacity-weighted average of ``attr`` over ``units``.

    Falls back to a plain mean when the group has no positive capacity.
    """
    total_cap = sum(u.pmax_mw for u in units)
    if total_cap > 0.0:
        return sum(getattr(u, attr) * u.pmax_mw for u in units) / total_cap
    return sum(getattr(u, attr) for u in units) / len(units)


def _aggregate_with_predefined_bins(
    generators: list[Generator], fuel_type: str
) -> list[Generator]:
    """Aggregate one fuel type's generators by their predefined efficiency bins.

    Generators are grouped by ``(efficiency_bin, zone)`` -- the loader-assigned
    vintage bins from :data:`HEAT_RATE_BINS` -- and each group collapses into a
    single capacity-weighted representative. This is the backward-compatible
    aggregation used when no explicit bin count is requested.
    """
    groups: dict[tuple[str, str], list[Generator]] = {}
    for g in generators:
        groups.setdefault((g.efficiency_bin, g.zone), []).append(g)

    result: list[Generator] = []
    for efficiency_bin, zone in sorted(groups):
        units = groups[(efficiency_bin, zone)]
        unit_id = f"{fuel_type}_{efficiency_bin}_{zone}"
        result.append(
            Generator(
                unit_id=unit_id,
                name=unit_id,
                zone=zone,
                fuel_type=fuel_type,
                efficiency_bin=efficiency_bin,
                pmax_mw=sum(u.pmax_mw for u in units),
                pmin_mw=sum(u.pmin_mw for u in units),
                heat_rate=_capacity_weighted(units, "heat_rate"),
                vom=_capacity_weighted(units, "vom"),
                emission_rate_co2=_capacity_weighted(units, "emission_rate_co2"),
                nox_rate=_capacity_weighted(units, "nox_rate"),
                eford=_capacity_weighted(units, "eford"),
                # Preserve the bin's vintage (see aggregate_fleet) so the
                # CCS-retrofit remaining-life screen and learning
                # attribution survive re-aggregation.
                online_year=int(round(_capacity_weighted(units, "online_year"))),
            )
        )
    return result


def aggregate_fleet_by_efficiency(
    generators: list[Generator],
    fuel_type: str,
    n_bins: int | None = None,
) -> list[Generator]:
    """Aggregate generators of one fuel type into efficiency bins.

    If ``n_bins`` is ``None``, use the predefined :data:`HEAT_RATE_BINS`
    vintage bins for this fuel type (backward-compatible default behavior).

    If ``n_bins`` is an integer, ignore :data:`HEAT_RATE_BINS` and instead
    create ``n_bins`` equal-width bins spanning the heat rate range of the
    input generators. Each bin gets:

    * ``heat_rate`` -- capacity-weighted average of generators in the bin,
    * ``pmax_mw`` -- sum of generator capacities in the bin,
    * ``emission_rate_co2`` / ``vom`` / ``nox_rate`` / ``eford`` --
      capacity-weighted averages,
    * ``efficiency_bin`` -- ``f"bin_{i+1}_of_{n_bins}"``.

    This allows fine-grained sensitivity analysis without changing any
    constants -- just set ``config.heat_rate_bin_count``. Note that 10+ bins
    add LP columns and may increase solve time; profile if using 20+ bins.

    Args:
        generators: All generators of this fuel type (assumed one zone).
        fuel_type: Fuel type string (e.g. ``"gas_cc"``).
        n_bins: Number of efficiency bins. ``None`` uses the defaults.

    Returns:
        List of aggregated :class:`Generator` objects, one per non-empty bin.
    """
    if n_bins is None:
        return _aggregate_with_predefined_bins(generators, fuel_type)

    if len(generators) == 0:
        return []

    sorted_gens = sorted(generators, key=lambda g: g.heat_rate)
    hr_min = sorted_gens[0].heat_rate
    hr_max = sorted_gens[-1].heat_rate

    # All generators essentially the same heat rate -- collapse to one bin.
    if hr_max - hr_min < 0.01:
        n_bins = 1

    bin_width = (hr_max - hr_min) / n_bins if n_bins > 1 else 1.0
    bins: list[list[Generator]] = [[] for _ in range(n_bins)]
    for g in sorted_gens:
        if n_bins == 1:
            idx = 0
        else:
            idx = min(int((g.heat_rate - hr_min) / bin_width), n_bins - 1)
        bins[idx].append(g)

    result: list[Generator] = []
    for i, bin_gens in enumerate(bins):
        if not bin_gens:
            continue
        unit_id = f"{fuel_type}_bin{i + 1}of{n_bins}"
        result.append(
            Generator(
                unit_id=unit_id,
                name=unit_id,
                zone=bin_gens[0].zone,
                fuel_type=fuel_type,
                efficiency_bin=f"bin_{i + 1}_of_{n_bins}",
                pmax_mw=sum(g.pmax_mw for g in bin_gens),
                pmin_mw=sum(g.pmin_mw for g in bin_gens),
                heat_rate=_capacity_weighted(bin_gens, "heat_rate"),
                vom=_capacity_weighted(bin_gens, "vom"),
                emission_rate_co2=_capacity_weighted(bin_gens, "emission_rate_co2"),
                nox_rate=_capacity_weighted(bin_gens, "nox_rate"),
                eford=_capacity_weighted(bin_gens, "eford"),
                # Preserve the bin's vintage: dropping it to the Generator
                # default (2000) makes every aggregated CC look near
                # end-of-life, silently disqualifying the whole bin from
                # the CCS-retrofit screen and from learning attribution.
                online_year=int(round(_capacity_weighted(bin_gens, "online_year"))),
            )
        )
    return result


def aggregate_fleet(
    generators: list[Generator], n_bins: int | str | None = None
) -> list[Generator]:
    """Collapse individual generators into representative units.

    With ``n_bins=None`` thermal generators are grouped by
    ``(fuel_type, efficiency_bin, zone)``; each group becomes a single
    :class:`Generator` whose capacity is the group total and whose per-MWh
    attributes are capacity-weighted averages of the group. This shrinks the
    LP from one column per physical unit (200+) to one column per thermal bin
    (~36), the dominant solve-time win.

    With an integer ``n_bins`` the thermal generators of each
    ``(fuel_type, zone)`` group are instead split into ``n_bins`` equal-width
    heat-rate bins (see :func:`aggregate_fleet_by_efficiency`), giving finer
    resolution for carbon-pricing and CCS sensitivity analysis at the cost of
    more LP columns.

    With ``n_bins=0`` or ``n_bins="unit"`` no aggregation is performed: the
    fleet is returned unchanged, one LP column per physical unit. This gives
    full plant-level granularity for calibration and financial analysis.

    Nuclear, hydro and import units pass through unchanged -- they are few
    in number and have distinct characteristics. Wind and solar are not part
    of the thermal fleet handled here, so they are unaffected. A thermal unit
    carrying a scheduled ``retirement_year`` also passes through, so the
    known-retirement mechanism keeps its per-unit retirement dates.

    **CAMPD per-plant bins (``is_campd_bin``) also pass through unchanged**
    (G-28 fix). :func:`build_base_fleet` builds the first-year CAMPD fleet as
    one LP unit per plant (:func:`bins_to_fleet`) *without* aggregation, so
    each tranche carries its originating ``plant_code`` and its
    must-run/committed/economic/peaking offer-curve structure. Collapsing those
    tranches into ``(fuel_type, efficiency_bin, zone)`` vintage representatives
    in the post-base-year re-aggregation dropped the ``plant_code`` (it is not
    a grouping key and was not propagated onto the representative) and the
    tranche structure, so a confirmed exit effective 2+ years into a CAMPD
    forecast went unmatched (:func:`~market_sim.model.capacity.apply_confirmed_exits`
    matches by ``plant_code``) and the retirement grain became lumpy zone
    vintage bins rather than per-plant. Passing CAMPD bins through keeps every
    projected year's thermal fleet at the same per-plant grain the base year
    already solves, preserving plant identity for the confirmed-exit,
    emission-rate-uniformity and hindcast-recall paths. Legacy (non-CAMPD)
    fleets are untouched -- they carry no ``plant_code`` and still collapse to
    vintage/heat-rate bins.

    Args:
        generators: The individual-unit fleet.
        n_bins: Number of equal-width efficiency bins per ``(fuel_type, zone)``
            group. ``None`` uses the predefined vintage bins; ``0`` or
            ``"unit"`` disables aggregation entirely.

    Returns:
        A new fleet list: pass-through units in their original order,
        followed by one representative unit per thermal group.
    """
    # n_bins == 0 / "unit": full unit granularity, no aggregation.
    if n_bins == 0 or n_bins == "unit":
        return list(generators)

    passthrough: list[Generator] = []
    groups: dict[tuple, list[Generator]] = {}
    for g in generators:
        if (
            g.fuel_type not in _AGGREGATABLE_FUELS
            or g.retirement_year is not None
            # CAMPD per-plant tranche: keep it un-aggregated so its plant_code
            # (and tranche offer curve) survives re-aggregation (G-28). The
            # base fleet is already built at this grain (build_base_fleet /
            # bins_to_fleet); merging it into vintage bins here was the sole
            # place plant identity was lost between projected years.
            or g.is_campd_bin
        ):
            passthrough.append(g)
            continue
        key = (
            (g.fuel_type, g.zone)
            if n_bins is not None
            else (g.fuel_type, g.efficiency_bin, g.zone)
        )
        groups.setdefault(key, []).append(g)

    representatives: list[Generator] = []
    if n_bins is None:
        for key in sorted(groups):
            fuel_type, efficiency_bin, zone = key
            units = groups[key]
            unit_id = f"{fuel_type}_{efficiency_bin}_{zone}"
            representatives.append(
                Generator(
                    unit_id=unit_id,
                    name=unit_id,
                    zone=zone,
                    fuel_type=fuel_type,
                    efficiency_bin=efficiency_bin,
                    pmax_mw=sum(u.pmax_mw for u in units),
                    pmin_mw=sum(u.pmin_mw for u in units),
                    heat_rate=_capacity_weighted(units, "heat_rate"),
                    vom=_capacity_weighted(units, "vom"),
                    emission_rate_co2=_capacity_weighted(units, "emission_rate_co2"),
                    nox_rate=_capacity_weighted(units, "nox_rate"),
                    eford=_capacity_weighted(units, "eford"),
                    # Preserve the bin's vintage (see the per-efficiency
                    # aggregator) so retrofit screens and learning
                    # attribution survive re-aggregation.
                    online_year=int(round(_capacity_weighted(units, "online_year"))),
                )
            )
    else:
        for key in sorted(groups):
            fuel_type, zone = key
            for rep in aggregate_fleet_by_efficiency(groups[key], fuel_type, n_bins):
                # The per-efficiency aggregator names bins within one zone;
                # qualify the id with the zone so cross-zone bins stay unique.
                rep.unit_id = f"{rep.unit_id}_{zone}"
                rep.name = rep.unit_id
                representatives.append(rep)

    return passthrough + representatives


def assemble_mc(
    fleet: FleetArrays,
    fuel_prices: np.ndarray,
    carbon_price: np.ndarray | float,
    nox_price: np.ndarray | float = 0.0,
    **adders: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    """Return the ``(n_gen, T)`` marginal cost array for the fleet.

    The marginal cost of each generator in each hour is::

        mc = heat_rate * fuel_price + vom
             + emission_rate * carbon_price
             + nox_rate * nox_price
             + sum(rate * price for each adder)

    ``fuel_prices`` is ``(n_gen, T)`` or broadcastable to it. ``carbon_price``
    and ``nox_price`` may be scalars or ``(T,)`` hourly arrays. ``carbon_price``
    may additionally be a **per-generator** membership-weighted allowance adder
    (``m_zone[zone_idx] * price``, shape ``(n_gen,)`` or ``(n_gen, 1)``) so a
    cap-and-trade program with fractional/partial footprint membership charges
    each generator only its member share (a uniform ``m_zone == 1`` reproduces
    the scalar path bit-for-bit). A bare ``(n_gen,)`` vector is reshaped to a
    column; in this model ``n_gen`` (hundreds) is never equal to ``T`` (8760),
    so the per-generator vs per-hour shapes never collide. Each ``adders``
    keyword value is a ``(generator_rate_array, hourly_price_array)`` pair,
    allowing extra cost terms (e.g. SO2) without changing the signature.
    """
    heat_rate = fleet.heat_rate[:, np.newaxis]
    mc = heat_rate * np.asarray(fuel_prices, dtype=float)
    mc = mc + fleet.vom[:, np.newaxis]
    carbon = np.asarray(carbon_price, dtype=float)
    # A per-generator membership-weighted adder arrives as a length-n_gen
    # vector; reshape to a column so it broadcasts down the T axis (a scalar or
    # (T,) hourly price is left as-is).
    if carbon.ndim == 1 and carbon.shape[0] == fleet.n_gen:
        carbon = carbon[:, np.newaxis]
    mc = mc + fleet.emission_rate[:, np.newaxis] * carbon
    mc = mc + fleet.nox_rate[:, np.newaxis] * np.asarray(nox_price, dtype=float)

    for rate_array, price_array in adders.values():
        rate = np.asarray(rate_array, dtype=float)[:, np.newaxis]
        mc = mc + rate * np.asarray(price_array, dtype=float)

    return mc


def campd_tranche_fuel_frac(
    gen: Generator,
    passthrough_by_supply: "dict[str, float | np.ndarray] | None" = None,
    takeorpay_by_plant: "dict[int, float] | None" = None,
    econ_srmc_bound: bool = False,
    committed_takeorpay_bit: bool = False,
    committed_takeorpay_all: bool = False,
    committed_takeorpay_regulated: bool = False,
    regulated_plants: "frozenset[int] | None" = None,
    committed_takeorpay_sunk_fixed: bool = False,
) -> "float | np.ndarray":
    """Return the fuel-cost passthrough for one CAMPD tranche generator.

    ``passthrough_by_supply`` maps a coal supply tag (the
    :func:`coal_supply_class` vocabulary — "prb" / "subbituminous" /
    "bituminous" / "lignite" / "waste") to that supply chain's passthrough:
    a scalar (flat) or an ``(T,)`` array (its gas-keyed sigmoid,
    ``fuel.coal_passthrough_by_supply``). Each coal tranche above must-run
    looks up its own tag, so each supply's curve — tuned to its basin, rank
    and delivery economics per ISO — applies only to its own plants. Tags
    without an entry (e.g. unclassified "") pass full fuel cost
    (``1.0``); :func:`apply_coal_tranches` applies the result.

    Must-run tranches (any fuel) pass ``0.0`` by default — their fuel is sunk
    under take-or-pay coal contracts, CHP host-steam obligations or ERCOT RUC,
    so they bid VOM + carbon + NOx only. A passthrough < 1.0 price-takes (an
    already-online unit bids to clear rather than on full marginal cost);
    > 1.0 marks the bid up to suppress over-dispatch.

    ``takeorpay_by_plant`` (set when ``ScenarioConfig.coal_takeorpay_from_data``
    is on) maps ``plant_code → measured contract share`` (EIA-923 Schedule-5
    Purchase Type, :func:`coal_takeorpay_share`). When given, a **coal** must-run
    tranche passes ``1 - share`` of its fuel instead of ``0.0``: only the
    contracted (take-or-pay) fraction is sunk, and the spot remainder bids full
    delivered fuel. ``share = 1.0`` (fully contracted) reproduces the default
    0.0; a plant absent from the map keeps the default 100%-sunk behaviour.

    ``econ_srmc_bound`` (``ScenarioConfig.coal_econ_srmc_bound``): when set,
    a **marginal** coal tranche (unit id ending ``_peak`` or containing
    ``_econ``) has its passthrough clamped to ``>= 1.0`` — its fuel is bought
    at market, so the offer never drops below the plant's full measured
    delivered fuel cost. Committed/must-run bands keep their contracted
    discount; markups above 1.0 are untouched.

    ``committed_takeorpay_bit`` (``ScenarioConfig.coal_bit_committed_takeorpay``):
    when set, the ``_committed`` tranche of a **bituminous** coal plant present
    in ``takeorpay_by_plant`` passes ``1 - contract_share`` (its contracted
    fuel is sunk, like ``_mustrun``) instead of the full-cost supply
    passthrough, bounded below by any supply curve already in force. Lets
    contracted bituminous baseload hold against cheap gas; the econ*/peak
    tranches above keep full delivered cost. Grounded by the plant's measured
    EIA-923 Schedule-5 share (rule 1/13), not a fitted sigmoid.

    ``committed_takeorpay_regulated``
    (``ScenarioConfig.coal_committed_takeorpay_regulated``): the same
    committed-band sunk-contract rule scoped by the plant's EIA-860
    ``Regulatory Status`` instead of coal supply — only plants in
    ``regulated_plants`` (the ``RE`` set, :func:`eia860_regulated_plants`)
    discount; merchant/IPP committed bands keep full delivered cost (SOM
    Table 7: regulated utilities self-commit 53-56% of coal starts, merchants
    offer economically 74-93%). Union scope with the other two flags.

    ``committed_takeorpay_sunk_fixed``
    (``ScenarioConfig.coal_committed_takeorpay_sunk_fixed``): suppresses the
    COMMITTED-band discount of all three flags above — the ``_mustrun`` band's
    ``1 - share`` is untouched. A take-or-pay contract is an obligation over an
    accounting period (contracted tonnage per year/month), not a per-hour
    price: over that period it is sunk in aggregate and so does not enter the
    marginal cost of an incremental MWh, because a plant that over-fulfils its
    contract buys its marginal ton at spot. Discounting the committed band in
    every hour converts that sunk FIXED cost into a MARGINAL subsidy and pins
    the band inframarginal for all 8760 h, which is what stops MISO's regulated
    PRB fleet de-loading overnight (miso-96; rules 17 ``[R-FLOOR-WINDOW]`` —
    a discount with no window — and 19 ``[R-ONE-MECH]`` — the contract is
    already carried once, on the band that runs regardless of price). The
    committed band then bids full delivered cost under its supply passthrough.

    The ``_sync`` synchronization tranche (rebuild step 3a,
    ``ScenarioConfig.coal_sync_srmc_tranche``) bids its **full SRMC** — full
    delivered fuel + VOM + reagents — so it passes ``1.0`` (no discount). It is
    the spot (avoidable-fuel) share of the forced-on coal min-load; the
    contracted share is carried by the fuel-free ``_mustrun`` band beside it,
    sized in :func:`bins_to_fleet` from the same measured contract share (so
    ``takeorpay_by_plant`` is *not* re-applied to ``_mustrun`` in sync mode —
    the runner passes ``None`` there and the default 0.0 fuel-free bid stands).
    """
    if gen.unit_id.endswith("_sync"):
        return 1.0
    if gen.unit_id.endswith("_mustrun"):
        if takeorpay_by_plant is not None and gen.fuel_type == "coal":
            share = takeorpay_by_plant.get(int(gen.plant_code))
            if share is not None:
                return float(1.0 - share)
        return 0.0
    # ScenarioConfig.coal_bit_committed_takeorpay: the `_committed` baseload
    # band's fuel is covered by the same take-or-pay contract as `_mustrun`
    # (MISO coal is ~100% contracted), so for a BITUMINOUS plant in the
    # measured share map it passes ``1 - contract_share`` (sunk contracted
    # fuel) rather than the full-cost supply passthrough — the committed
    # baseload then holds against cheap gas while the econ*/peak tranches above
    # keep full delivered cost (coal_econ_srmc_bound) so BIT price-follows
    # above the committed band. Grounded by the plant's own EIA-923 Schedule-5
    # share (rule 1/13); bounded below by any supply curve already in force.
    _bit = getattr(gen, "coal_supply", "") == "bituminous"
    _reg = committed_takeorpay_regulated and (
        regulated_plants is not None and int(gen.plant_code) in regulated_plants
    )
    _scope = committed_takeorpay_all or (committed_takeorpay_bit and _bit) or _reg
    # ScenarioConfig.coal_committed_takeorpay_sunk_fixed: the contract is an
    # accounting-period tonnage obligation, sunk in aggregate, so it is a FIXED
    # cost and never a marginal one for a plant that over-fulfils it. The
    # `_mustrun` band above already carries it once, on the capacity that is on
    # regardless of price; discounting the committed band as well subsidises
    # the MARGINAL MWh in all 8760 h (rules 17/19, miso-96).
    if committed_takeorpay_sunk_fixed:
        _scope = False
    if (
        _scope
        and gen.unit_id.endswith("_committed")
        and gen.fuel_type == "coal"
        and takeorpay_by_plant is not None
    ):
        share = takeorpay_by_plant.get(int(gen.plant_code))
        if share is not None:
            disc = float(1.0 - share)
            base = 1.0
            if passthrough_by_supply:
                base = passthrough_by_supply.get(getattr(gen, "coal_supply", ""), 1.0)
            if isinstance(base, np.ndarray):
                return np.minimum(base, disc)
            return min(float(base), disc)
    if gen.fuel_type == "coal" and passthrough_by_supply:
        pt = passthrough_by_supply.get(getattr(gen, "coal_supply", ""), 1.0)
        # ScenarioConfig.coal_econ_srmc_bound: a MARGINAL coal tranche
        # (econ*/peak — above the contracted committed band) buys its fuel
        # at market, so its offer may never drop below full measured
        # delivered fuel cost: clamp the supply chain's passthrough to
        # >= 1.0 (markups > 1.0 pass through unchanged). The committed
        # band keeps the take-or-pay/stay-online discount.
        uid = gen.unit_id
        if econ_srmc_bound and (uid.endswith("_peak") or "_econ" in uid):
            if isinstance(pt, np.ndarray):
                return np.maximum(pt, 1.0)
            return max(float(pt), 1.0)
        return pt
    return 1.0


def apply_coal_tranches(
    mc: np.ndarray,
    generators: list[Generator],
    fleet_arrays: FleetArrays,
    fuel_fracs: list[float],
    fuel_prices: np.ndarray,
) -> None:
    """Reduce coal-tranche marginal cost by the sunk (unpassed) fuel fraction.

    For each coal tranche ``g``, the take-or-pay contract makes
    ``1 - fuel_fracs[g]`` of the physical fuel cost (``heat_rate ×
    fuel_price``) sunk, so it is removed from the bid::

        mc[g, t] -= (1 - fuel_fracs[g]) × heat_rate[g] × fuel_price[g, t]

    Tranche 1 (``fuel_frac = 0``) is left bidding at VOM (plus carbon/NOx);
    tranche 3 (``fuel_frac = 1``) is unchanged. VOM, carbon and NOx are never
    discounted — they are incurred per MWh dispatched regardless of the fuel
    contract. ``mc`` is modified in place.

    Args:
        mc: The ``(n_gen, T)`` marginal-cost array, modified in place.
        generators: The generator list aligned row-for-row with ``mc``.
        fleet_arrays: The vectorized fleet, for per-generator heat rate.
        fuel_fracs: Per-generator fuel-cost passthrough from
            :func:`split_coal_tranches`.
        fuel_prices: The ``(n_gen, T)`` delivered fuel price array used to
            assemble ``mc``.
    """
    fuel_prices = np.asarray(fuel_prices, dtype=float)
    for g, gen in enumerate(generators):
        # Discount the fuel term for any generator with a take-or-pay
        # contract or host-steam obligation that sinks part of its fuel
        # cost (coal tranches; CAMPD must-run tranches across all fuels).
        # fuel_fracs[g] is a scalar, or an (T,) array for a gas-keyed PRB
        # passthrough — an hourly-varying frac applies elementwise (and a
        # value > 1.0 marks the bid up).
        ff = fuel_fracs[g]
        if np.isscalar(ff) and ff >= 1.0:
            continue
        fuel_cost = fleet_arrays.heat_rate[g] * fuel_prices[g, :]
        mc[g, :] -= (1.0 - np.asarray(ff, dtype=float)) * fuel_cost
