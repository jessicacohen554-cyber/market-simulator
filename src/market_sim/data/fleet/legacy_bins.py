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
from typing import TYPE_CHECKING

import numpy as np

from market_sim.data.fleet.models import (
    FleetArrays,
    Generator,
)

if TYPE_CHECKING:
    from market_sim.config.scenarios import ScenarioConfig

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")

# Fuel types collapsed into efficiency-bin representative units. Everything
# else -- nuclear, hydro, import (few in number, distinct characteristics)
# and wind/solar (not part of the thermal fleet) -- passes through unchanged.
# Oil and biomass are aggregatable thermal blocks too; including them here
# also means ERCOT's CAMPD-bin path (which sources non-aggregatable fuels
# from EIA-860) excludes the handful of ERCOT oil/biomass units exactly as it
# already excluded their gas_ct-classified predecessors, keeping ERCOT
# dispatch unchanged. gas_st joined when the D-25 taxonomy fix gave gas-steam
# boilers their own fuel (they classed gas_ct before): it must stay in this
# set so the ERCOT exclusion keeps covering those rows — dropping it would
# re-admit ~10 GW of curated-bin-covered ERCOT steam capacity as raw
# duplicate LP units.
_AGGREGATABLE_FUELS: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "coal", "oil", "biomass"}
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
    committed_dispatchable_supplies: "frozenset[str] | None" = None,
    committed_measured_basis: bool = False,
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

    ``committed_dispatchable_supplies``
    (``ScenarioConfig.coal_prb_committed_dispatchable`` → ``{"prb",
    "subbituminous"}``): coal plants whose ``coal_supply`` tag is in this set
    are excluded from ALL THREE committed-band discounts above — their
    ``_committed`` tranche bids full delivered cost under its supply
    passthrough, exactly like a merchant plant's. The ``_mustrun`` band keeps
    its sunk-contract treatment. Measured basis: miso-111 (the regulated PRB
    fleet's own CEMS record shows its committed band cycling nightly and
    price-responsively — the discount held it byte-flat instead).

    The ``_sync`` synchronization tranche (rebuild step 3a,
    ``ScenarioConfig.coal_sync_srmc_tranche``) bids its **full SRMC** — full
    delivered fuel + VOM + reagents — so it passes ``1.0`` (no discount). It is
    the spot (avoidable-fuel) share of the forced-on coal min-load; the
    contracted share is carried by the fuel-free ``_mustrun`` band beside it,
    sized in :func:`bins_to_fleet` from the same measured contract share (so
    ``takeorpay_by_plant`` is *not* re-applied to ``_mustrun`` in sync mode —
    the runner passes ``None`` there and the default 0.0 fuel-free bid stands).

    ``committed_measured_basis``
    (``ScenarioConfig.committed_band_measured_basis``) is HALF (b) of the Route A
    REPLACE mechanism: a coal ``_committed`` tranche passes ``1.0`` — full
    delivered fuel, no supply passthrough of any kind — so the band's effective
    basis IS the measured ``avg_committed_p50`` multiplier half (a) installs
    (:func:`market_sim.data.offer_curves.apply_committed_band_measured_basis`),
    in every hour of every year. The two halves are ONE mechanism and are never
    armed apart: with the sigmoid left on, the effective basis becomes
    ``measured × passthrough`` and lands on the measurement in NO year (PJM
    2020-2025: 0.618 .. 1.205 against a measured 0.916), which is the stacking
    rule 19 ``[R-ONE-MECH]`` forbids. The ``econ*``/``peak`` bands KEEP the
    sigmoid — its merit-order-crossover rationale is about INCREMENTAL coal
    competing with gas, while the min-load block is the cost of being on, not a
    bid for the marginal MWh. ``_mustrun`` and ``_sync`` return above this and
    are untouched; every committed-band fuel modifier below it (the three
    take-or-pay discounts, the SRMC bound) is bypassed by construction, because
    a band carrying any of them would no longer hold the identity that is this
    mechanism's whole claim.
    """
    if gen.unit_id.endswith("_sync"):
        return 1.0
    if gen.unit_id.endswith("_mustrun"):
        if takeorpay_by_plant is not None and gen.fuel_type == "coal":
            share = takeorpay_by_plant.get(int(gen.plant_code))
            if share is not None:
                return float(1.0 - share)
        return 0.0
    # ScenarioConfig.committed_band_measured_basis (Route A REPLACE, half (b)).
    # Placed HERE — after the fuel-free `_mustrun`/`_sync` bands, before every
    # committed-band fuel modifier — so the coal min-load block pays full
    # delivered fuel and nothing scales it. That is what makes the band's
    # effective basis equal to the measured multiplier half (a) installs, which
    # is the mechanism's defining claim (see the docstring).
    if committed_measured_basis and (
        gen.fuel_type == "coal" and gen.unit_id.rsplit("_", 1)[-1] == "committed"
    ):
        return 1.0
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
    # ScenarioConfig.coal_prb_committed_dispatchable: PRB-supplied plants are
    # excluded from the committed-band discount — their committed band bids
    # full delivered cost like a merchant's. The meter shows that band cycling
    # nightly and price-responsively even at regulated plants (miso-111,
    # PREREG-miso111-prb-committed-flex-2026-07-31.md §8); the self-commitment
    # is carried once, by `_mustrun` (rule 19 [R-ONE-MECH]).
    if (
        committed_dispatchable_supplies
        and getattr(gen, "coal_supply", "") in committed_dispatchable_supplies
    ):
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
        # `_commitcyc` (ScenarioConfig.coal_prb_committed_split, miso-112):
        # the cycling slice of a split regulated-PRB committed band. It is
        # never matched by the `_committed` discount rules above (suffix
        # scoping), so it reaches here and bids its full supply passthrough;
        # under coal_econ_srmc_bound it takes the same >= 1.0 clamp as the
        # econ/peak tranches — its marginal fuel is bought at market
        # (PREREG-miso112-prb-committed-split-2026-07-31.md §3).
        if econ_srmc_bound and (
            uid.endswith("_peak") or "_econ" in uid or uid.endswith("_commitcyc")
        ):
            if isinstance(pt, np.ndarray):
                return np.maximum(pt, 1.0)
            return max(float(pt), 1.0)
        return pt
    return 1.0


#: Tranche-suffix stacking rank for the per-plant capacity-window mapping
#: (ERCOT-144). Physical (capacity) semantics, deliberately NOT the assembled
#: bid order: `_mustrun` is the plant's LSL block at the bottom, `_committed`
#: sits above it, the econ ramp ascends `econlo` -> `econhi` (or
#: `econc00..econcNN` — the smoothing slices are an ascending ladder by
#: construction), and `peak*` tops the stack. Bid-sorted ordering would let a
#: residual-identified multiplier inversion (e.g. the keeper's lignite
#: econ_low 1.216 > econ_high 1.113) reorder the physical stack.
def _coal_tranche_rank(unit_id: str) -> float:
    suffix = unit_id.rpartition("_")[2]
    if suffix in ("mustrun", "sync"):
        return 0.0
    if suffix == "committed":
        return 1.0
    if suffix == "commitcyc":
        # miso-112 cycling slice: the upper part of the committed band,
        # physically between the hold-through slice and the econ ramp.
        return 1.5
    if suffix == "econlo":
        return 2.0
    if suffix == "econhi":
        return 3.0
    if suffix.startswith("econc"):
        try:
            return 2.0 + int(suffix[5:]) / 100.0
        except ValueError:
            return 2.5
    if suffix.startswith("peak"):
        return 99.0
    return 50.0  # unknown suffixes stack below peak, above econ


def _coal_perplant_levels(
    generators: "list[Generator]",
    fleet_arrays: FleetArrays,
    curves: "dict[int, tuple[tuple[float, float], ...]]",
    self_sched_floor: float,
) -> dict[int, float]:
    """Per-row measured offer levels for CAMPD coal committed/econ tranches.

    For each coal plant present in ``curves`` (the measured merged modal
    60-Day SCED ``Submitted TPO`` supply curve,
    ``constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO`` — ERCOT-144), the plant's
    CAMPD tranches are stacked in physical capacity order
    (:func:`_coal_tranche_rank`), each `_committed`/`_econ*` tranche's
    capacity window ``[lo, hi]`` (fractions of plant capability) is mapped
    onto the measured curve (scaled to its own top MW), and the tranche's
    level is the capacity-weighted mean measured price over the window's
    PRICED segments. Points at/below ``self_sched_floor`` (San Miguel's
    −$249 LSL block) are excluded from the mean — they are a price-taker
    self-schedule signal, not a marginal cost; a window falling entirely
    inside the floor block takes the first priced price above it.

    Returns ``{row_index: level}`` for exactly the rows to reprice.
    """
    by_plant: dict[int, list[int]] = {}
    for g, gen in enumerate(generators):
        if gen.fuel_type == "coal" and getattr(gen, "is_campd_bin", False):
            code = int(getattr(gen, "plant_code", 0) or 0)
            if code in curves:
                by_plant.setdefault(code, []).append(g)
    out: dict[int, float] = {}
    for code, rows in by_plant.items():
        pts = curves[code]
        top = float(pts[-1][0])
        edges = [0.0] + [float(mw) for mw, _p in pts]
        prices = [float(p) for _mw, p in pts]
        total = float(sum(fleet_arrays.pmax[g] for g in rows))
        if total <= 0 or top <= 0:
            continue
        rows_ord = sorted(rows, key=lambda g: _coal_tranche_rank(generators[g].unit_id))
        cum = 0.0
        for g in rows_ord:
            share = float(fleet_arrays.pmax[g]) / total
            lo_f, hi_f = cum, cum + share
            cum = hi_f
            rank = _coal_tranche_rank(generators[g].unit_id)
            if not (1.0 <= rank < 99.0):
                continue  # mustrun/sync/peak keep their own measured owners
            lo, hi = lo_f * top, hi_f * top
            wsum = psum = 0.0
            for k in range(len(prices)):
                if prices[k] <= self_sched_floor:
                    continue
                w = max(0.0, min(edges[k + 1], hi) - max(edges[k], lo))
                if w > 0:
                    wsum += w
                    psum += w * prices[k]
            if wsum > 0:
                out[g] = psum / wsum
            else:
                # window entirely inside the self-schedule floor block: the
                # first priced price above it is the plant's marginal level
                priced = [p for p in prices if p > self_sched_floor]
                if priced:
                    out[g] = priced[0]
    return out


#: Non-leap month lengths for the model's fixed 8760 CST calendar (rule 8).
_MONTH_DAYS: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _hour_month_hod(T: int) -> tuple[np.ndarray, np.ndarray]:
    """Month-of-hour (1..12) and hour-of-day arrays for the model's calendar.

    The model hour axis is fixed-CST hour-beginning on the non-leap 8760
    calendar; the windowed per-plant curves (ercot-168) are derived onto the
    SAME clock (CPT->CST conversion at derivation), so a plain calendar map is
    the whole alignment story here.
    """
    doy = np.arange(T) // 24
    bounds = np.cumsum((0,) + _MONTH_DAYS)
    month = np.searchsorted(bounds, doy, side="right").astype(np.int64)
    hod = np.arange(T) % 24
    return month, hod


def _coal_perplant_yearly_levels(
    generators: "list[Generator]",
    fleet_arrays: FleetArrays,
    year_windows: "dict[int, tuple]",
    self_sched_floor: float,
) -> dict[int, list[tuple[tuple[int, ...], tuple[int, ...], float]]]:
    """Per-row windowed measured levels for the ercot-168 year table.

    ``year_windows`` is one solve-year's plant table
    (``plant_code -> ((months, hours, curve), ...)``). The tranche stacking
    and the capacity-window -> price mapping are the SAME construction as
    :func:`_coal_perplant_levels`, evaluated per (months × hours) window on
    the window's own curve — deliberately a parallel implementation rather
    than a refactor of the static path, so the armed 2024/25 arithmetic is
    untouched at the byte level (the precommit's G-BIT gate; a unit test
    asserts the two paths agree on a single all-months-all-hours window).

    Returns ``{row_index: [(months, hours, level), ...]}`` for exactly the
    rows to reprice.
    """
    by_plant: dict[int, list[int]] = {}
    for g, gen in enumerate(generators):
        if gen.fuel_type == "coal" and getattr(gen, "is_campd_bin", False):
            code = int(getattr(gen, "plant_code", 0) or 0)
            if code in year_windows:
                by_plant.setdefault(code, []).append(g)
    out: dict[int, list[tuple[tuple[int, ...], tuple[int, ...], float]]] = {}
    for code, rows in by_plant.items():
        entries = year_windows[code]
        total = float(sum(fleet_arrays.pmax[g] for g in rows))
        if total <= 0:
            continue
        rows_ord = sorted(rows, key=lambda g: _coal_tranche_rank(generators[g].unit_id))
        cum = 0.0
        for g in rows_ord:
            share = float(fleet_arrays.pmax[g]) / total
            lo_f, hi_f = cum, cum + share
            cum = hi_f
            rank = _coal_tranche_rank(generators[g].unit_id)
            if not (1.0 <= rank < 99.0):
                continue  # mustrun/sync/peak keep their own measured owners
            wins: list[tuple[tuple[int, ...], tuple[int, ...], float]] = []
            for months, hours, pts in entries:
                top = float(pts[-1][0])
                if top <= 0:
                    continue
                edges = [0.0] + [float(mw) for mw, _p in pts]
                prices = [float(p) for _mw, p in pts]
                lo, hi = lo_f * top, hi_f * top
                wsum = psum = 0.0
                for k in range(len(prices)):
                    if prices[k] <= self_sched_floor:
                        continue
                    w = max(0.0, min(edges[k + 1], hi) - max(edges[k], lo))
                    if w > 0:
                        wsum += w
                        psum += w * prices[k]
                if wsum > 0:
                    level = psum / wsum
                else:
                    # window entirely inside the self-schedule floor block:
                    # the first priced price above it (the static path's own
                    # convention)
                    priced = [p for p in prices if p > self_sched_floor]
                    if not priced:
                        continue
                    level = priced[0]
                wins.append(
                    (
                        tuple(int(m) for m in months),
                        tuple(int(h) for h in hours),
                        float(level),
                    )
                )
            if wins:
                out[g] = wins
    return out


def apply_coal_tranches(
    mc: np.ndarray,
    generators: list[Generator],
    fleet_arrays: FleetArrays,
    fuel_fracs: list[float],
    fuel_prices: np.ndarray,
    config: "ScenarioConfig | None" = None,
    year: int | None = None,
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

    **Coal-offer net-revenue margin form** (ERCOT-137,
    ``config.coal_offer_net_revenue_margin``): a CAMPD coal ``_mustrun``
    tranche is NOT fuel-discounted; instead its assembled cost is shifted to
    the measured net-margin form::

        mc[g, t] = heat_rate[g] × (fuel(t) − anchor) + emis(t) + level

    (implemented as ``mc[g, :] += level − heat_rate[g] × anchor − vom[g]`` on
    the assembled cost — the VOM already inside ``mc`` is folded into the
    measured all-in level, never double-counted). The block keeps FULL
    delivered-fuel tracking while everything above fuel is the fuel-invariant
    measured margin; at ``fuel == anchor`` the bid is exactly ``level``, the
    measured RT curve bottom (ERCOT-136 §3). Mirrors
    :func:`market_sim.data.offer_curves.apply_gas_offer_margin`; scope is the
    CAMPD tranche path only (legacy ``_t1`` rows keep the sunk-fuel form —
    the same legacy-path inertness the gas mechanism declares). The
    committed/econ supply-sigmoid passthroughs above the block are a separate
    mechanism (rule 19) and are untouched.

    **Coal `_peak`-tranche gas-anchored margin form** (ERCOT-140,
    ``config.coal_peak_offer_margin``): a CAMPD coal ``_peak*`` tranche is
    repriced from its band-multiplier composition to the measured
    top-of-curve form::

        mc[g, t] = gas_hr × (gas_cc(t) − anchor) + emis(t) + level

    (implemented as ``mc[g, :] += level + gas_hr × (gas_cc − anchor) −
    heat_rate[g] × fuel_price[g, :] − vom[g]`` on the assembled cost — the
    coal-fuel and VOM terms are folded into the measured all-in level). The
    slope basis is GAS, not coal: the measured top tracks delivered gas
    (gas-parity opportunity pricing of the marginal coal MW) while delivered
    coal moved the other way, so coal-fuel tracking is REMOVED on these rows
    — that is the measured finding, not an omission
    (``docs/PRECOMMIT-ercot140-coal-peak-offer-2026-07-30.md`` §0.1).
    ``gas_cc(t)`` is the pmax-cap-weighted mean of the CC_REGULAR CAMPD
    rows' delivered-gas series — the identification's own fuel basis
    (ERCOT-138 §J ``fuel_capwtd``). The anchor is the SHARED gas anchor
    (``config.gas_offer_margin_anchor`` — rule 19, never a second one); at
    ``gas == anchor`` the resolved bid is exactly ``level``. The branch
    exits before the fuel-frac discount, so the supply-sigmoid passthrough
    never composes with it (rule 19 replacement — the two prior owners of
    this row's price, the peak multiplier and the sigmoid, both stand down).

    **Per-plant measured offer curves** (ERCOT-144,
    ``config.coal_perplant_offer_level``): every CAMPD coal
    ``_committed``/``_econ*`` tranche of a plant present in
    ``config.coal_perplant_offer_curves`` is repriced to the
    capacity-weighted measured price of its capacity window on the plant's
    own merged modal SCED TPO supply curve
    (:func:`_coal_perplant_levels`)::

        mc[g, t] = level_{plant,window} + emis(t)

    (implemented as ``mc[g, :] += level − heat_rate[g] × fuel_price[g, :] −
    vom[g]`` on the assembled cost). The levels are fuel-invariant BY
    MEASUREMENT — the measured mid-band did not co-move with delivered gas
    (+46 %) or coal across the corpus years — while the curve's bottom
    (``_mustrun``, coal-anchored ERCOT-137 form) and top (``_peak``,
    gas-anchored ERCOT-140 form) keep their own measured fuel responses.
    The branch exits before the fuel-frac discount: the COAL_* band
    multipliers, the supply sigmoids and the econ marginal-HR floor all
    stand down on these rows (rule 19 replacement — the harness also strips
    them from the armed config so nothing re-armable remains, rule 26).

    **Per-year windowed curves** (ercot-168,
    ``config.coal_perplant_offer_yearly`` — requires the ERCOT-144 gate):
    when the solve ``year`` is present in
    ``config.coal_perplant_offer_curves_yearly``, a listed plant's
    committed/econ tranches take the SAME all-in replacement with the level
    a step series over the year table's (months × hours) windows — each
    window's level is the tranche's capacity-window price on that window's
    own measured curve (:func:`_coal_perplant_yearly_levels`). A year absent
    from the table falls through to the static branch unchanged; the derive
    guarantees exhaustive (month × hour) coverage and the branch hard-fails
    on any gap (rule 25).

    Args:
        mc: The ``(n_gen, T)`` marginal-cost array, modified in place.
        generators: The generator list aligned row-for-row with ``mc``.
        fleet_arrays: The vectorized fleet, for per-generator heat rate.
        fuel_fracs: Per-generator fuel-cost passthrough from
            :func:`campd_tranche_fuel_frac`.
        fuel_prices: The ``(n_gen, T)`` delivered fuel price array used to
            assemble ``mc``.
        config: Scenario configuration supplying the coal net-revenue margin
            gate and its identification constants. ``None`` (legacy callers)
            keeps the sunk-fuel form everywhere.
        year: The solve year, used only by the per-year windowed curve
            branch (ercot-168) to index the year table. ``None`` with that
            gate armed is a hard error; legacy callers without the gate are
            unaffected.

    Raises:
        ValueError: ``coal_offer_net_revenue_margin`` armed without a
            resolved anchor or level (rule 25 — the constants must be
            resolved into the recorded config, never silently defaulted).
    """
    margin_on = config is not None and getattr(
        config, "coal_offer_net_revenue_margin", False
    )
    coal_anchor = coal_level = 0.0
    if margin_on:
        _anchor = getattr(config, "coal_offer_margin_anchor", None)
        _level = getattr(config, "coal_offer_margin_level", None)
        if _anchor is None or _level is None:
            raise ValueError(
                "coal_offer_net_revenue_margin is armed but "
                "coal_offer_margin_anchor / coal_offer_margin_level is unset; "
                "resolve them from constants.COAL_OFFER_MARGIN_ANCHOR_BY_ISO / "
                "COAL_OFFER_MARGIN_LEVEL_BY_ISO at config build (rule 25 — no "
                "silent fallback in the offer path)"
            )
        coal_anchor, coal_level = float(_anchor), float(_level)
    n_margin = 0
    fuel_prices = np.asarray(fuel_prices, dtype=float)
    # Coal `_peak`-tranche gas-anchored margin (ERCOT-140): resolve the gate
    # and, when armed, build the gas reference series gas_cc(t) — the
    # pmax-cap-weighted mean of the CC_REGULAR CAMPD rows' delivered-gas
    # series, the identification's own fuel basis (ERCOT-138 §J).
    peak_margin_on = config is not None and getattr(
        config, "coal_peak_offer_margin", False
    )
    peak_level = peak_gas_hr = peak_anchor = 0.0
    gas_cc: "np.ndarray | None" = None
    n_peak_margin = 0
    if peak_margin_on:
        _plevel = getattr(config, "coal_peak_offer_level", None)
        _pghr = getattr(config, "coal_peak_offer_gas_hr", None)
        _panchor = getattr(config, "gas_offer_margin_anchor", None)
        if _plevel is None or _pghr is None or _panchor is None:
            raise ValueError(
                "coal_peak_offer_margin is armed but coal_peak_offer_level / "
                "coal_peak_offer_gas_hr / gas_offer_margin_anchor is unset; "
                "resolve them from constants.COAL_PEAK_OFFER_LEVEL_BY_ISO / "
                "COAL_PEAK_OFFER_GAS_HR_BY_ISO / GAS_OFFER_MARGIN_ANCHOR_BY_ISO "
                "at config build (rule 25 — no silent fallback in the offer "
                "path; the anchor is SHARED with the gas offer surface, "
                "rule 19)"
            )
        peak_level, peak_gas_hr, peak_anchor = (
            float(_plevel),
            float(_pghr),
            float(_panchor),
        )
        # Per-year LEVEL refinement (ercot-192, matrix §5.1 item 13): a solve
        # year PRESENT in the resolved table swaps the level only — the slope
        # and the shared anchor are untouched (rule 19). A year ABSENT falls
        # through here unchanged, which is the G-BIT bit-identity kill for
        # 2024/2025.
        if getattr(config, "coal_peak_offer_yearly_level", False):
            _pytab = getattr(config, "coal_peak_offer_level_yearly", None)
            if not _pytab:
                raise ValueError(
                    "coal_peak_offer_yearly_level is armed but "
                    "coal_peak_offer_level_yearly is unset; resolve it from "
                    "constants.COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO at config "
                    "build (rule 24 — the mechanism would silently do nothing)"
                )
            if year is None:
                raise ValueError(
                    "coal_peak_offer_yearly_level is armed but no solve year "
                    "was passed to apply_coal_tranches — the year table cannot "
                    "be indexed (rule 24)"
                )
            _pylevel = {int(k): float(v) for k, v in _pytab.items()}.get(int(year))
            if _pylevel is not None:
                logger.info(
                    "coal peak-tranche offer YEAR level (ercot-192, year %d): "
                    "%.4f -> %.4f $/MWh (slope and shared anchor unchanged)",
                    int(year),
                    peak_level,
                    _pylevel,
                )
                peak_level = _pylevel
            else:
                logger.info(
                    "coal peak-tranche offer YEAR level (ercot-192): solve year "
                    "%d is NOT in the table %s — static level kept",
                    int(year),
                    sorted({int(k) for k in _pytab}),
                )
        cc_rows = [
            g
            for g, gen in enumerate(generators)
            if getattr(gen, "is_campd_bin", False)
            and getattr(gen, "plant_group", None) == "CC_REGULAR"
        ]
        if not cc_rows:
            raise ValueError(
                "coal_peak_offer_margin is armed but no CC_REGULAR CAMPD rows "
                "exist to form the delivered-gas reference series gas_cc(t) — "
                "the mechanism's fuel basis (ERCOT-138 §J) is undefined for "
                "this fleet (rule 25 — no silent fallback)"
            )
        _w = np.array([float(fleet_arrays.pmax[g]) for g in cc_rows], dtype=float)
        gas_cc = (_w[:, None] * np.asarray(fuel_prices, dtype=float)[cc_rows, :]).sum(
            axis=0
        ) / _w.sum()
    # Per-plant measured coal offer curves (ERCOT-144): resolve the gate and
    # precompute each CAMPD committed/econ tranche's measured window level
    # from its plant's own merged modal SCED TPO supply curve. Rule-19
    # REPLACEMENT of the COAL_* band multipliers + supply sigmoids on these
    # rows — the branch exits before the fuel-frac discount, and the full
    # assembled fuel+VOM terms are folded into the measured all-in level
    # (the levels are fuel-invariant BY MEASUREMENT; emissions adders stay).
    perplant_on = config is not None and getattr(
        config, "coal_perplant_offer_level", False
    )
    pp_levels: dict[int, float] = {}
    if perplant_on:
        _curves = getattr(config, "coal_perplant_offer_curves", None)
        if not _curves:
            raise ValueError(
                "coal_perplant_offer_level is armed but "
                "coal_perplant_offer_curves is unset; resolve it from "
                "constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO at config build "
                "(rule 25 — no silent fallback in the offer path)"
            )
        from market_sim.config.constants import COAL_PERPLANT_SELF_SCHED_FLOOR

        _curves = {int(k): v for k, v in _curves.items()}
        pp_levels = _coal_perplant_levels(
            generators, fleet_arrays, _curves, COAL_PERPLANT_SELF_SCHED_FLOOR
        )
        if not pp_levels:
            raise ValueError(
                "coal_perplant_offer_level is armed but no CAMPD coal "
                "committed/econ tranche matched the per-plant curve registry "
                "— the mechanism would silently do nothing (rule 24)"
            )
    # Per-year windowed per-plant coal offer curves (ercot-168): for a solve
    # year PRESENT in the resolved year table, committed/econ tranches of
    # listed plants take their (months x hours) window levels instead of the
    # static level; a year ABSENT from the table falls through to the static
    # path unchanged (2024/2025 bit-identity is the precommit's G-BIT kill).
    yearly_on = config is not None and getattr(
        config, "coal_perplant_offer_yearly", False
    )
    pp_year_levels: dict[int, list] = {}
    _ym: "np.ndarray | None" = None
    _yh: "np.ndarray | None" = None
    if yearly_on:
        if not perplant_on:
            raise ValueError(
                "coal_perplant_offer_yearly is armed without "
                "coal_perplant_offer_level — the year table refines the "
                "per-plant mechanism and has no meaning without it (rule 24)"
            )
        _ytab = getattr(config, "coal_perplant_offer_curves_yearly", None)
        if not _ytab:
            raise ValueError(
                "coal_perplant_offer_yearly is armed but "
                "coal_perplant_offer_curves_yearly is unset; resolve it from "
                "constants.COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO at config "
                "build (rule 25 — no silent fallback in the offer path)"
            )
        if year is None:
            raise ValueError(
                "coal_perplant_offer_yearly is armed but the caller passed no "
                "solve year — the year table cannot resolve (rule 25)"
            )
        from market_sim.config.constants import COAL_PERPLANT_SELF_SCHED_FLOOR

        _ytab = {int(y): tab for y, tab in _ytab.items()}
        _ywin = _ytab.get(int(year))
        if _ywin:
            _ywin = {int(k): v for k, v in _ywin.items()}
            pp_year_levels = _coal_perplant_yearly_levels(
                generators, fleet_arrays, _ywin, COAL_PERPLANT_SELF_SCHED_FLOOR
            )
            if not pp_year_levels:
                raise ValueError(
                    "coal_perplant_offer_yearly is armed and the year table "
                    f"carries {year}, but no CAMPD coal committed/econ "
                    "tranche matched it — the mechanism would silently do "
                    "nothing (rule 24)"
                )
            _ym, _yh = _hour_month_hod(mc.shape[1])
    for g, gen in enumerate(generators):
        if (
            peak_margin_on
            and gen.fuel_type == "coal"
            and getattr(gen, "is_campd_bin", False)
            and gen.unit_id.rpartition("_")[2].startswith("peak")
        ):
            # Gas-anchored top-of-curve margin form: remove the assembled
            # coal-fuel and VOM terms and post the measured gas-parity bid
            # (emissions adders stay on top). Exits before the fuel-frac
            # discount — the sigmoid passthrough never composes (rule 19).
            mc[g, :] += (
                peak_level
                + peak_gas_hr * (gas_cc - peak_anchor)
                - fleet_arrays.heat_rate[g] * fuel_prices[g, :]
                - fleet_arrays.vom[g]
            )
            n_peak_margin += 1
            continue
        if (
            margin_on
            and gen.fuel_type == "coal"
            and getattr(gen, "is_campd_bin", False)
            and gen.unit_id.endswith("_mustrun")
        ):
            # Net-revenue margin form: keep the assembled full fuel cost
            # (no sunk-fuel discount) and add the fuel-invariant measured
            # margin, netting out the VOM already in mc (the measured level
            # is the all-in submitted offer price).
            mc[g, :] += (
                coal_level
                - fleet_arrays.heat_rate[g] * coal_anchor
                - fleet_arrays.vom[g]
            )
            n_margin += 1
            continue
        if yearly_on and g in pp_year_levels:
            # Per-year windowed measured level (ercot-168): the same all-in
            # replacement as the static branch below, with the level a step
            # series over the (months x hours) windows of the solve year's
            # own measured curves. Vectorized per window (a handful of
            # windows per row, never a loop over hours — rule 2).
            lev = np.full(mc.shape[1], np.nan)
            for _months, _hours, _level in pp_year_levels[g]:
                _msk = np.isin(_ym, _months) & np.isin(_yh, _hours)
                lev[_msk] = _level
            if np.isnan(lev).any():
                raise ValueError(
                    "coal_perplant_offer_curves_yearly leaves uncovered "
                    f"hours for row {g} ({generators[g].unit_id}) — the "
                    "window table must cover every (month, hour) cell "
                    "(rule 25; derive emits exhaustive coverage)"
                )
            mc[g, :] += (
                lev
                - fleet_arrays.heat_rate[g] * fuel_prices[g, :]
                - fleet_arrays.vom[g]
            )
            continue
        if perplant_on and g in pp_levels:
            # Per-plant measured window level (ERCOT-144): remove the
            # assembled fuel and VOM terms and post the plant's own measured
            # all-in level for this tranche's capacity window (emissions
            # adders stay on top). Exits before the fuel-frac discount —
            # neither the band multipliers nor the sigmoid passthrough ever
            # composes with the measured level (rule 19 replacement).
            mc[g, :] += (
                pp_levels[g]
                - fleet_arrays.heat_rate[g] * fuel_prices[g, :]
                - fleet_arrays.vom[g]
            )
            continue
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
    if n_margin:
        logger.info(
            "coal offer net-revenue margin: %d _mustrun tranche(s) repriced at "
            "level %.4f $/MWh / anchor %.4f $/MMBtu (fuel-invariant margin, "
            "full delivered-fuel tracking)",
            n_margin,
            coal_level,
            coal_anchor,
        )
    if pp_year_levels:
        _by_plant_y: dict[int, list[float]] = {}
        for g, wins in pp_year_levels.items():
            _by_plant_y.setdefault(
                int(getattr(generators[g], "plant_code", 0) or 0), []
            ).extend(lv for _m, _h, lv in wins)
        logger.info(
            "coal per-plant YEAR-windowed offer levels (ercot-168, year %s): "
            "%d committed/econ tranche(s) across %d plant(s) on the year's "
            "own measured window curves — %s",
            year,
            len(pp_year_levels),
            len(_by_plant_y),
            "; ".join(
                f"{code} [{min(v):.2f}..{max(v):.2f}]"
                for code, v in sorted(_by_plant_y.items())
            ),
        )
    if pp_levels:
        _by_plant: dict[int, list[float]] = {}
        for g, lev in pp_levels.items():
            _by_plant.setdefault(
                int(getattr(generators[g], "plant_code", 0) or 0), []
            ).append(lev)
        logger.info(
            "coal per-plant measured offer levels (ERCOT-144): %d "
            "committed/econ tranche(s) across %d plant(s) repriced onto their "
            "own merged modal SCED TPO curves — %s",
            len(pp_levels),
            len(_by_plant),
            "; ".join(
                f"{code} [{min(v):.2f}..{max(v):.2f}]"
                for code, v in sorted(_by_plant.items())
            ),
        )
    if n_peak_margin:
        logger.info(
            "coal peak-tranche offer margin: %d _peak tranche(s) repriced at "
            "level %.4f $/MWh / gas slope %.4f MMBtu/MWh / shared gas anchor "
            "%.4f $/MMBtu (gas-parity top-of-curve form; coal-fuel tracking "
            "removed on these rows by measurement — ERCOT-140)",
            n_peak_margin,
            peak_level,
            peak_gas_hr,
            peak_anchor,
        )
