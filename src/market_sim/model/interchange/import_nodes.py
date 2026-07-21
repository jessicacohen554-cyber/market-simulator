"""Priced import/export nodes and the generic reference-price seam.

The ISO-generic external-interchange machinery: an ISO's neighbors as
synthetic :class:`~market_sim.data.fleet.Generator` supply tranches / export
sinks in its external zone (:func:`build_import_generators` /
:func:`build_export_sinks`), the flow-banded reference-price seam
(:func:`build_reference_price_node` / :func:`inject_reference_price_mc` and
the firm scheduled-flow floors), the shared measured seam-ladder repricer
(:func:`_inject_seam_ladder`), the import-node topology extension
(:func:`extend_with_import_node` / :func:`apply_deliverability_seam_limit`),
and the measured diurnal interchange shape
(:func:`inject_interchange_shape`). Moved INTACT from
``model/transmission.py`` (session 3F, refactor-consolidation plan §5
item 6); ``transmission`` remains the full-surface facade.
"""

import logging

import numpy as np

from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
from market_sim.config.iso_configs import (
    InterfaceLimit,
    ISOConfig,
    TransferLink,
    Zone,
)
from market_sim.data.fleet_models import Generator
from market_sim.data.floor_mechanisms import (
    MECH_FIRM_IMPORT,
    ensure_mechanism,
)
from market_sim.model.interchange.spec import (
    EXPORT_TRANCHES,
    EXPORT_TRANCHES_BY_YEAR,
    EXTERNAL_SIMULTANEOUS_LIMITS,
    IMPORT_EFORD,
    IMPORT_NODE_LINKS,
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
    IMPORT_TRANCHE_EF,
    IMPORT_ZONE,
    NeighborInterface,
)

_logger = logging.getLogger(__name__)


def wecc_border_carbon_adder(carbon_price: float) -> float:
    """Return the CAISO border carbon adjustment on imports ($/MWh).

    CARB levies the cap-and-trade allowance obligation on electricity
    imported into California; unspecified-source power is assessed at the
    default emission factor :data:`CARB_UNSPECIFIED_IMPORT_EF`
    (0.428 tCO2e/MWh, MRR 17 CCR §95111(b)). The adder is therefore
    ``0.428 x allowance price`` — ~$15/MWh at the 2024 average allowance
    price of $35.23/t — and belongs on every WECC import tranche price
    (but NOT on the export sink: exports carry no CA compliance cost).

    Args:
        carbon_price: The allowance price in $/tCO2 (e.g. from
            :func:`market_sim.policy.carbon.resolve_carbon_price`).

    Returns:
        The border adjustment in $/MWh of imported energy.
    """
    return CARB_UNSPECIFIED_IMPORT_EF * carbon_price


def build_import_generators(
    iso: str, border_carbon_per_mwh: float = 0.0, year: int | None = None
) -> list[Generator]:
    """Return an ISO's import node as a list of pseudo-generators.

    The aggregate import capability from the ISO's neighbors is modeled as a
    stepped supply curve: each tranche of
    :data:`~market_sim.config.interchange_config.IMPORT_TRANCHES` becomes a synthetic
    :class:`~market_sim.data.fleet.Generator` in the ISO's external zone.
    When ``year`` matches an
    :data:`~market_sim.config.interchange_config.IMPORT_TRANCHES_BY_YEAR` entry for the
    ISO, that year-grounded ladder is used instead of the static default — the
    priced node's neighbor-hub blocks are gas-priced, so a backcast year with a
    different gas/neighbor-price level needs its own price ladder (an unmapped
    year, e.g. any forecast year, falls back to the static ladder).
    The marginal cost of a tranche is set directly through the ``vom``
    field; ``heat_rate`` is zero, so no fuel price enters the cost. Appended
    to the fleet, the tranches compete in merit order through the ordinary
    energy balance and the external zone's links into the ISO's trading
    zones -- no special LP formulation is needed.

    A border carbon adjustment (CAISO: see :func:`wecc_border_carbon_adder`)
    enters as ``border_carbon_per_mwh`` — the *unspecified* adjustment
    (``CARB_UNSPECIFIED_IMPORT_EF`` × allowance price). Each tranche pays it
    scaled by its own emission factor relative to the unspecified default
    (:data:`~market_sim.config.interchange_config.IMPORT_TRANCHE_EF`), so a firm
    hydro/solar block (EF 0) pays nothing while an unspecified block pays the
    full adder — matching CARB, which charges specified imports their actual
    (often zero) emissions and only unspecified power the 0.428 default. A
    tranche absent from the EF map pays the full adder (byte-identical to the
    prior flat behaviour for any ISO without a map). It is carried in the
    tranche VOM rather than as an ``emission_rate_co2`` so the import carbon
    cost reaches the merit order without the import MWh inflating the modeled
    *in-state* CO2 total that calibration benchmarks against eGRID
    generation-based emissions.

    Args:
        iso: ISO identifier, e.g. ``"CAISO"`` or ``"PJM"``.
        border_carbon_per_mwh: Unspecified-import border carbon adjustment
            ($/MWh); 0 disables it. Scaled per tranche by its emission factor.
        year: backcast year; selects an ``IMPORT_TRANCHES_BY_YEAR[iso][year]``
            ladder when one exists, else the static ``IMPORT_TRANCHES[iso]``.

    Returns:
        Import tranches ordered cheapest first; empty for an ISO with no
        import node configured (e.g. ERCOT, whose DC-tie interchange rides
        in its demand series).
    """
    zone = IMPORT_ZONE.get(iso)
    tranches = (
        IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year) if (year is not None) else None
    )
    if tranches is None:
        tranches = IMPORT_TRANCHES.get(iso, [])
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    gens = []
    for name, capacity, marginal_cost in tranches:
        ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
        tranche_carbon = border_carbon_per_mwh * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        gens.append(
            Generator(
                unit_id=f"{zone}_{name}",
                name=name,
                zone=zone,
                fuel_type="import",
                pmax_mw=capacity,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=marginal_cost + tranche_carbon,
                eford=IMPORT_EFORD.get(iso, 0.0),
            )
        )
    return gens


def build_export_sinks(iso: str, year: int | None = None) -> list[Generator]:
    """Return an ISO's export sinks as a list of pseudo-generators.

    ISO surplus is exported across the external zone's links and absorbed
    by these sinks. Absorption is modeled as *negative* generation: each
    block's output is bounded in ``[-capacity, 0]`` MW, so a dispatch of
    ``-x`` withdraws ``x`` MW from the external node. The capacity is
    therefore carried by ``pmin_mw``, and ``pmax_mw`` is held at zero so a
    sink can never inject phantom cheap power and distort the import merit
    order. A block's $/MWh price rides in ``vom``: negative dispatch times
    a positive ``vom`` *reduces* the LP objective, so the block is the
    neighbors' willingness-to-pay and the ISO exports into it whenever its
    internal marginal cost is below that price (CAISO's single $0 sink
    only ever absorbs surplus that would otherwise be curtailed).

    Args:
        iso: ISO identifier, e.g. ``"CAISO"`` or ``"PJM"``.
        year: backcast year; selects an ``EXPORT_TRANCHES_BY_YEAR[iso][year]``
            ladder when one exists, else the static ``EXPORT_TRANCHES[iso]``
            (the export-side mirror of :func:`build_import_generators`'s
            year resolution).

    Returns:
        Export sinks in the ISO's external zone; empty when none are
        configured.
    """
    zone = IMPORT_ZONE.get(iso)
    sinks = (
        EXPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year) if (year is not None) else None
    )
    if sinks is None:
        sinks = EXPORT_TRANCHES.get(iso, [])
    return [
        Generator(
            unit_id=f"{zone}_{name}",
            name=name,
            zone=zone,
            fuel_type="import",
            pmax_mw=0.0,
            pmin_mw=-capacity,
            heat_rate=0.0,
            vom=price,
            eford=0.0,
        )
        for name, capacity, price in sinks
    ]


# Unit-id markers tagging a reference-price seam pseudo-generator so the
# post-assembly mc injector (:func:`inject_reference_price_mc`) can find each row
# and map it back to its neighbor and flow tranche. The id is
# ``<zone><mark><name>#<k>`` — import rows take the neighbor price + hurdle,
# export rows the neighbor price - hurdle, both evaluated at tranche ``k``'s flow.
_REF_IMPORT_MARK = "_refimp_"
_REF_EXPORT_MARK = "_refexp_"


def build_reference_price_node(
    iso: str,
    zone_overrides: dict[str, str] | None = None,
    extra_neighbors: list[NeighborInterface] | None = None,
) -> list[Generator]:
    """Return the reference-price seam as import/export pseudo-generators.

    The forecast-grade replacement for the fitted
    :func:`build_import_generators` / :func:`build_export_sinks`: per neighbor in
    :data:`~market_sim.config.interchange_config.INTERFACE_NEIGHBORS`, the import and
    export ranges are each split into
    :data:`~market_sim.data.neighbor_price.SEAM_FLOW_TRANCHES` equal-width flow
    bands, all placed in the ISO's external zone. Splitting into bands lets the
    injector give each band a different, *flow-responsive* price (the neighbor's
    price at that band's flow), so the seam sees a downward-sloping import-demand
    curve and self-limits below the cap rather than pinning at it.

    The marginal cost is left at zero here — it is a *placeholder* overwritten
    hour-by-hour by :func:`inject_reference_price_mc` after the fleet's mc is
    assembled (the cost is hourly, so it cannot ride in the static ``vom``). The
    unit id carries the neighbor name and tranche index (via
    :data:`_REF_IMPORT_MARK` / :data:`_REF_EXPORT_MARK` and a ``#k`` suffix) so
    the injector can map each row back to its neighbor and band.

    Import bands are positive-output generators bounded ``[0, limit/n]``; export
    bands are negative-output sinks bounded ``[-limit/n, 0]`` (the
    :func:`build_export_sinks` convention). The bands sum to the interface limit,
    so total ``|flow| <= limit`` still holds; the LP fills bands in merit order,
    bounded also by the external zone's border-link TTCs.

    Args:
        iso: ISO identifier; must have an entry in ``INTERFACE_NEIGHBORS`` and
            in :data:`~market_sim.config.interchange_config.IMPORT_ZONE`.
        zone_overrides: Optional neighbor-name → zone map re-homing a seam's
            bands into a different external zone (MISO's South seam under
            ``miso_south_seam_split``). Non-CAISO only; ``None`` keeps every
            band in the shared external node (byte-identical).
        extra_neighbors: Optional additional seams appended to the registry
            list for this build only (MISO's Manitoba two-way seam under
            ``miso_manitoba_seam``; miso-74). ``None`` keeps the registry
            unchanged (byte-identical), so the extra seam's ladder/envelope
            entries stay inert until its bands are built here.

    Returns:
        Import + export pseudo-generators; empty for an ISO with no neighbor
        registry (so an un-onboarded ISO stays byte-identical).
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    import_zone = IMPORT_ZONE.get(iso)
    gens: list[Generator] = []
    for neighbor in [*INTERFACE_NEIGHBORS.get(iso, []), *(extra_neighbors or [])]:
        # CAISO lands each corridor's tranches in its OWN external corridor zone
        # (the neighbor name IS the per-hub zone WECC_DSW / WECC_PNW, created by
        # split_caiso_import_node_per_hub), so the corridor link and its ATC
        # envelope cap each corridor independently. Every other ISO uses the
        # single appended external node (byte-identical), unless the caller
        # re-homes a specific seam via ``zone_overrides`` (neighbor name →
        # zone; MISO's South seam under miso_south_seam_split, hosted in
        # MISO_SOUTH_EXTERNAL_ZONE by split_miso_south_external_node).
        zone = neighbor.name if iso == "CAISO" else import_zone
        if zone_overrides and neighbor.name in zone_overrides:
            zone = zone_overrides[neighbor.name]
        # Split each direction into SEAM_FLOW_TRANCHES bands of equal width so
        # the flow-responsive injector can price each band at its midpoint flow
        # along the neighbor's supply curve. The bands sum to the interface
        # limit, so |flow| <= limit still holds.
        step = neighbor.interface_limit_mw / SEAM_FLOW_TRANCHES
        for k in range(1, SEAM_FLOW_TRANCHES + 1):
            gens.append(
                Generator(
                    unit_id=f"{zone}{_REF_IMPORT_MARK}{neighbor.name}#{k}",
                    name=f"ref_import_{neighbor.name}_t{k}",
                    zone=zone,
                    fuel_type="import",
                    pmax_mw=step,
                    pmin_mw=0.0,
                    heat_rate=0.0,
                    vom=0.0,
                    eford=0.0,
                )
            )
            gens.append(
                Generator(
                    unit_id=f"{zone}{_REF_EXPORT_MARK}{neighbor.name}#{k}",
                    name=f"ref_export_{neighbor.name}_t{k}",
                    zone=zone,
                    fuel_type="import",
                    pmax_mw=0.0,
                    pmin_mw=-step,
                    heat_rate=0.0,
                    vom=0.0,
                    eford=0.0,
                )
            )
    return gens


def inject_reference_price_mc(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
    gas_scenario: str = "mid",
    carbon_price: float = 0.0,
    border_anchor: bool = False,
    forward_skill: str | None = None,
) -> bool:
    """Overwrite the reference-price seam rows of ``mc`` with hourly prices.

    Mirrors :func:`inject_interchange_shape`'s post-assembly pattern, but for
    cost rather than availability. Each seam row is one flow tranche ``k`` of a
    neighbor (``..._refimp_<name>#k`` / ``..._refexp_<name>#k``); its row is set
    to the **flow-responsive** price for that band from
    :func:`market_sim.data.neighbor_price.seam_tranche_prices` — the neighbor's
    price evaluated at the band's midpoint flow, so the willingness-to-pay
    slides down the neighbor's supply curve as the ISO exports more (and rises
    as it imports more). An export tranche takes ``- hurdle``, an import tranche
    ``+ hurdle``, so PJM exports only while a band's flow-responsive price still
    exceeds its own LMP by the hurdle, and the seam self-limits below the cap
    instead of pinning at it. A neighbor with no resolvable load shape falls back
    to the flat capacity-weighted aggregate (every band at the same price — no
    slope). Modifies ``mc`` in place.

    ``carbon_price`` (> 0 only for the CAISO/CARB seam) adds a border-carbon
    adjustment to each IMPORT tranche whose neighbor carries an
    ``import_emission_factor``:
    ``wecc_border_carbon_adder(carbon_price) × (EF / CARB_UNSPECIFIED_IMPORT_EF)``
    — the same per-resource EF scaling :func:`build_import_generators` applies, so
    a clean PNW-hydro corridor (EF 0) pays nothing and a desert-SW gas corridor
    pays its share. Export legs never pay it (no CA compliance cost). PJM/MISO
    pass ``carbon_price=0`` (and their neighbors carry no EF), so they are
    byte-identical.

    ``border_anchor`` (MISO opt-in) re-anchors the PJM seam from PJM's
    system-average realized LMP to its MISO-facing western border hubs (ComEd /
    AEP-Ohio / ATSI; :data:`~market_sim.config.interchange_config.MISO_PJM_BORDER_HR_BY_YEAR`)
    by swapping the PJM spec's ``hr_by_year`` for the lower border table — the
    cheaper western border clears more import in tight hours (the 2024/2025 MISO
    import under-run), while 2023 (already matched) barely moves. No-op for every
    other ISO / when off (byte-identical).

    ``forward_skill`` is forwarded to
    :func:`market_sim.data.neighbor_price.neighbor_heat_rate` (via
    ``interface_reference_prices`` / ``seam_tranche_prices``) — sourced from
    ``ScenarioConfig.neighbor_hr_forward_skill``, default ``None`` (off,
    byte-identical). See that field's docstring.

    Returns ``True`` when at least one seam row was priced, ``False`` when the
    fleet has no reference-price node (so a non-reference run is untouched).
    """
    from dataclasses import replace

    from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
    from market_sim.config.interchange_config import (
        INTERFACE_NEIGHBORS,
        MISO_PJM_BORDER_HR_BY_YEAR,
    )
    from market_sim.data.neighbor_price import (
        interface_reference_prices,
        seam_tranche_prices,
    )

    hours = int(mc.shape[1])
    aggregate = interface_reference_prices(
        iso, year, hours, gas_scenario, forward_skill
    ).aggregate()
    specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(iso, [])}
    if border_anchor and iso == "MISO" and "PJM" in specs:
        # Western-border re-anchor: price the PJM seam off its MISO-facing border
        # hubs (lower than PJM's eastern-weighted system average) so the seam
        # clears more import. Only the hr_by_year level changes; the load shape,
        # hurdle and tranche structure are untouched.
        specs["PJM"] = replace(specs["PJM"], hr_by_year=MISO_PJM_BORDER_HR_BY_YEAR)
    border = wecc_border_carbon_adder(carbon_price) if carbon_price > 0.0 else 0.0
    # Cache each neighbor's (export, import) tranche price matrices once.
    tranches: dict[str, tuple | None] = {}
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if _REF_IMPORT_MARK in uid:
            tag, is_export = uid.rsplit(_REF_IMPORT_MARK, 1)[1], False
        elif _REF_EXPORT_MARK in uid:
            tag, is_export = uid.rsplit(_REF_EXPORT_MARK, 1)[1], True
        else:
            continue
        name, _, k_str = tag.partition("#")
        k = int(k_str) - 1 if k_str else 0
        if name not in tranches:
            spec = specs.get(name)
            tranches[name] = (
                seam_tranche_prices(
                    spec,
                    year,
                    hours,
                    gas_scenario=gas_scenario,
                    forward_skill=forward_skill,
                )
                if spec is not None
                else None
            )
        priced = tranches[name]
        spec = specs.get(name)
        hurdle = spec.hurdle if spec is not None else 0.0
        # CARB border carbon on the import leg only, scaled by the corridor's
        # marginal-import EF (None / export → 0).
        carbon_adder = 0.0
        if (not is_export) and border > 0.0 and spec is not None:
            ef = getattr(spec, "import_emission_factor", None)
            if ef is not None:
                carbon_adder = border * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        if priced is not None:
            export_p, import_p, _ = priced
            band = export_p[k] if is_export else import_p[k]
            mc[row, :] = band - hurdle if is_export else band + hurdle + carbon_adder
        elif aggregate is not None:
            # No load shape: flat aggregate, same for every band (no slope).
            mc[row, :] = (
                aggregate - hurdle if is_export else aggregate + hurdle + carbon_adder
            )
        else:
            continue
        applied = True
    return applied


def inject_reference_price_firm_export(fleet_arrays, iso: str, year: int) -> bool:
    """Floor PJM's firm (must-flow) scheduled export on the reference-price seam.

    The mirror of :func:`inject_nyiso_firm_imports` / :func:`inject_miso_firm_imports`
    for the EXPORT direction. PJM exports to MISO / NYISO in ~87-100% of hours at
    a mean spread too thin for the economic seam to clear every hour, because a
    large share is firm, long-term SCHEDULED capacity/energy that flows
    regardless of the hourly price. The economic tranches alone back this firm
    base off in cheap-spread hours (the PJM 2023 NYISO +4.3 vs +18.5 TWh miss).

    For each neighbor carrying a
    :attr:`~market_sim.config.interchange_config.NeighborInterface.firm_export_floor_by_year`
    entry for ``year``, this forces the neighbor's CHEAPEST export tranches on at
    ``floor_mw`` by lowering their upper bound (``pmax``) to a negative value —
    the seam's export rows are negative-output sinks (output ``<= 0``), so an
    upper bound of ``-x`` forces at least ``x`` MW of export through that band.
    The floor is laid into the cheapest bands first (lowest tranche index = the
    neighbor's highest willingness-to-pay), exactly the bands the economic seam
    fills first, so the firm base and the economic increment above it are priced
    consistently along the same convex supply curve with no double counting. The
    economic tranches above the floor still clear on the hourly spread.

    The floor never exceeds the lightest measured scheduled-export hour (it is the
    p10 of PJM's OWN scheduled flow), so it cannot force a phantom over-export;
    in a year/seam where the model already exports more than the floor it is
    simply non-binding. Modifies ``fleet_arrays.pmax`` in place.

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ISOs in ``INTERFACE_NEIGHBORS`` apply a floor.
        year: Backcast year keying ``firm_export_floor_by_year``.

    Returns:
        ``True`` if any firm-export floor was applied, else ``False``
        (byte-identical) when no neighbor has a floor for ``year``.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(iso, [])}
    if not specs:
        return False
    unit_ids = list(fleet_arrays.unit_ids)
    applied = False
    for name, spec in specs.items():
        table = spec.firm_export_floor_by_year
        floor = table.get(year, 0.0) if table else 0.0
        if floor <= 0.0:
            continue
        # Export tranche rows for this neighbor, indexed by tranche k (1-based).
        rows: dict[int, int] = {}
        suffix = f"{_REF_EXPORT_MARK}{name}#"
        for r, uid in enumerate(unit_ids):
            if suffix in uid:
                rows[int(uid.rsplit("#", 1)[1])] = r
        if not rows:
            continue
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        remaining = floor
        # Lay the firm floor into the cheapest bands first (lowest k = highest
        # neighbor willingness-to-pay), forcing each fully until the floor is met,
        # then the partial remainder on the last band.
        for k in sorted(rows):
            if remaining <= 0.0:
                break
            r = rows[k]
            forced = min(step, remaining)
            # pmax < 0 -> col_upper = pmax x availability < 0 -> output <= -forced
            # (the export sink must flow at least `forced` MW). availability is
            # 1.0 for the eford=0 seam rows, so pmax = -forced is exact.
            fleet_arrays.pmax[r] = -forced
            remaining -= forced
            applied = True
    return applied


def inject_reference_price_firm_import(fleet_arrays, iso: str, year: int) -> bool:
    """Floor the firm (must-flow) scheduled IMPORT on the reference-price seam.

    The import-direction mirror of :func:`inject_reference_price_firm_export` (and
    of the Manitoba/HQ firm-import blocks). An ISO can net-import from a neighbor
    in ~99-100% of hours at a stable multi-GW base — cheap surplus baseload
    (Ontario nuclear/hydro behind the PJM seam) plus firm scheduled transfers —
    that flows regardless of the hourly price spread. A pure gas x heat-rate
    economic seam, which prices the neighbor's border ABOVE the ISO's own cheap
    coal, then wrongly net-EXPORTS over that seam (MISO's 2024 -8.3 vs -23.1 net
    interchange and 2025 +18 vs -19 sign flip + the +20 TWh energy-balance
    overshoot).

    For each neighbor carrying a
    :attr:`~market_sim.config.interchange_config.NeighborInterface.firm_import_floor_by_year`
    entry for ``year``, this forces the neighbor's CHEAPEST import tranches on at
    ``floor_mw`` by raising their hour-varying lower bound
    (``FleetArrays.min_gen``) — the seam's import rows are positive-output
    pseudo-generators, so a lower bound of ``x`` forces at least ``x`` MW of
    import through that band. The floor is laid into the cheapest bands first
    (lowest tranche index = the lowest delivered import price), exactly the bands
    the economic seam fills first, so the firm base and the economic increment
    above it are priced consistently along the same convex supply curve with no
    double counting. Being inframarginal (must-flow), the firm base does not set
    the clearing price; it displaces the marginal domestic unit (the over-running
    coal/CC), and the economic tranches above the floor still clear on the hourly
    spread. Each band's forced level is capped at its available capacity
    (``pmax x availability``) each hour, so a feasible LP solution always exists
    even after the seam deliverability envelope (:func:`inject_miso_seam_flow_limit`)
    has scaled the bands' availability; composed with any existing ``min_gen``
    floor via ``maximum``.

    The floor is the p10 of the seam's OWN measured net import (the base imported
    in >=90% of hours), so it cannot force a phantom over-import; in a year/seam
    where the model already imports more than the floor it is simply non-binding.
    Modifies ``fleet_arrays.min_gen`` in place.

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ISOs in ``INTERFACE_NEIGHBORS`` apply a floor.
        year: Backcast year keying ``firm_import_floor_by_year``.

    Returns:
        ``True`` if any firm-import floor was applied, else ``False``
        (byte-identical) when no neighbor has a floor for ``year``.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(iso, [])}
    if not specs:
        return False
    unit_ids = list(fleet_arrays.unit_ids)
    hours = int(fleet_arrays.availability.shape[1])
    applied = False
    for name, spec in specs.items():
        table = spec.firm_import_floor_by_year
        floor = table.get(year, 0.0) if table else 0.0
        if floor <= 0.0:
            continue
        # Import tranche rows for this neighbor, indexed by tranche k (1-based).
        suffix = f"{_REF_IMPORT_MARK}{name}#"
        rows: dict[int, int] = {}
        for r, uid in enumerate(unit_ids):
            if suffix in uid:
                rows[int(uid.rsplit("#", 1)[1])] = r
        if not rows:
            continue
        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
            ).copy()
        remaining = floor
        # Lay the firm floor into the cheapest bands first (lowest k), forcing each
        # up to its available capacity until the floor is met, then the partial
        # remainder on the next band.
        for k in sorted(rows):
            if remaining <= 0.0:
                break
            r = rows[k]
            avail_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
            forced = np.minimum(remaining, avail_r)
            raised = fleet_arrays.min_gen[r, :] < forced
            np.maximum(
                fleet_arrays.min_gen[r, :], forced, out=fleet_arrays.min_gen[r, :]
            )
            ensure_mechanism(fleet_arrays)[r, raised] = MECH_FIRM_IMPORT
            # Reduce the remaining floor by the band's minimum forced capacity so
            # the next band covers any shortfall (use the min across hours so the
            # floor is met even in the band's tightest-availability hour).
            remaining -= float(forced.min())
            applied = True
    return applied


def _inject_seam_ladder(fleet_arrays, mc: np.ndarray, ladder) -> bool:
    """Reprice every reference-price band row of ``mc`` from ``ladder``.

    Shared core of the per-ISO measured seam-ladder injectors: ``ladder`` is
    one year's ``{seam: {"import"/"export": (price per band,)}}`` registry
    entry (``None`` no-ops). Rows are matched by the reference-node unit-id
    convention (``<zone><mark><seam>#<k>``); non-band rows and seams absent
    from the ladder are untouched.
    """
    if not ladder:
        return False

    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if _REF_IMPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
        elif _REF_EXPORT_MARK in uid:
            tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
        else:
            continue
        name, _, k_str = tag.partition("#")
        seam = ladder.get(name)
        if seam is None or not k_str:
            continue
        prices = seam[side]
        k = int(k_str) - 1
        if not 0 <= k < len(prices):
            continue
        mc[row, :] = prices[k]
        applied = True
    return applied


def extend_with_import_node(iso_config: ISOConfig) -> ISOConfig:
    """Return ``iso_config`` with its external import/export zone appended.

    Adds the ISO's :data:`~market_sim.config.interchange_config.IMPORT_ZONE` as a
    zero-load zone plus its border links
    (:data:`~market_sim.config.interchange_config.IMPORT_NODE_LINKS`). A no-op when
    the ISO has no import node configured or the zone is already part of
    the topology (CAISO bakes ``WECC_import`` into ``_caiso_config``).

    When the ISO has an entry in
    :data:`~market_sim.config.interchange_config.EXTERNAL_SIMULTANEOUS_LIMITS`,
    the corresponding aggregate :class:`InterfaceLimit` is appended too —
    capping the total simultaneous flow across ALL border links at the
    published SIL/SEC (Simultaneous Import Limit / Simultaneous Export
    Capability), which is materially less than the sum of individual path
    ratings. The per-link TTCs remain as individual path bounds; the
    aggregate constraint binds only when several paths would load
    simultaneously past the network's real simultaneous capability.

    PJM's external node is appended here, on demand, rather than baked into
    ``_pjm_config``: an external zone whose links join several border zones
    creates a wheeling path around the internal interfaces (real PJM loop
    flow, but absent from the calibrated 8-zone backcast, which serves the
    measured interchange schedule at its border zones instead).
    """
    iso = iso_config.name
    zone = IMPORT_ZONE.get(iso)
    if zone is None or zone in iso_config.zone_names:
        return iso_config
    links = [
        TransferLink(from_zone=zone, to_zone=border, ttc_mw=ttc)
        for border, ttc in IMPORT_NODE_LINKS.get(iso, [])
    ]
    # SIL/SEC: aggregate simultaneous import/export limit across all border
    # links, built dynamically so the link references always match the border
    # links actually appended.
    sil_spec = EXTERNAL_SIMULTANEOUS_LIMITS.get(iso)
    new_interface_limits: list[InterfaceLimit] = []
    if sil_spec is not None and links:
        name, cap_mw, bidirectional = sil_spec
        new_interface_limits.append(
            InterfaceLimit(
                name=name,
                links=[(zone, border) for border, _ in IMPORT_NODE_LINKS[iso]],
                cap_mw=cap_mw,
                bidirectional=bidirectional,
            )
        )
    extended = iso_config.model_copy(
        update={
            "zones": [
                *iso_config.zones,
                Zone(name=zone, iso=iso, load_share=0.0),
            ],
            "links": [*iso_config.links, *links],
            "interface_limits": [
                *iso_config.interface_limits,
                *new_interface_limits,
            ],
        }
    )
    extended.validate_topology()
    return extended


def apply_deliverability_seam_limit(
    iso_config: ISOConfig, iso: str, seam_import_mw: float | None
) -> ISOConfig:
    """Replace the import-node simultaneous cap with the measured seam limit.

    Part A of ``ScenarioConfig.capacity_deliverability_limits``: where the ISO
    publishes a per-area *seam* import limit (CAISO branch-group Maximum Import
    Capability summed to the WECC boundary — routed to the import node by
    :mod:`market_sim.config.capacity_area_crosswalk`), that measured value
    supersedes the calibrated system-wide scalar (the baked-in CAISO
    ``WECC_import_simultaneous`` cap, or the
    :data:`~market_sim.config.interchange_config.EXTERNAL_SIMULTANEOUS_LIMITS`
    entry appended by :func:`extend_with_import_node`).

    The simultaneous-import :class:`InterfaceLimit` is identified structurally as
    the one whose every link originates at the import node, so this is
    ISO-agnostic. A no-op (returns ``iso_config`` unchanged) when
    ``seam_import_mw`` is ``None``/non-positive, the ISO has no import node, or
    no matching interface limit exists. Preferring the published limit over the
    fitted scalar can loosen the cap and move the backcast (repo rule #12); that
    is expected — the mechanism stays and any residual is a root-cause note.

    Args:
        iso_config: The (possibly import-node-extended) ISO topology.
        iso: Model ISO name.
        seam_import_mw: Summed per-area seam import limit in MW.

    Returns:
        ``iso_config`` with the simultaneous-import cap replaced, or unchanged.
    """
    if seam_import_mw is None or seam_import_mw <= 0.0:
        return iso_config
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return iso_config
    new_limits: list[InterfaceLimit] = []
    replaced = False
    for lim in iso_config.interface_limits:
        if lim.links and all(pair[0] == zone for pair in lim.links):
            new_limits.append(lim.model_copy(update={"cap_mw": float(seam_import_mw)}))
            replaced = True
        else:
            new_limits.append(lim)
    if not replaced:
        return iso_config
    extended = iso_config.model_copy(update={"interface_limits": new_limits})
    extended.validate_topology()
    return extended


def inject_interchange_shape(
    fleet_arrays,
    iso: str,
    year: int,
    percentile: float = 90.0,
    export_only: bool = False,
    import_percentile: float | None = None,
    export_percentile: float | None = None,
) -> bool:
    """Shape the priced import/export node by the measured diurnal interchange.

    The static node (:func:`build_import_generators` /
    :func:`build_export_sinks`) makes every import tranche and export sink
    available in every hour, so the LP clears a near-constant import schedule
    and never exports — whereas real CAISO imports overnight and **exports** the
    midday solar glut. After :func:`generators_to_fleet_arrays` builds the
    fleet, this scales, per hour:

    * each import tranche's ``availability`` by the measured net-import envelope
      (so midday cheap imports shrink toward their historical midday level), and
    * each export sink's hour-varying lower bound (``min_gen``) by the measured
      net-export envelope (so the midday surplus can flow into the sink).

    The envelope is the (month × hour-of-day) percentile of EIA-930 ``Total
    interchange`` (:func:`market_sim.data.eia_loader
    .measured_interchange_envelope`) relative to the node's static tranche
    totals — a measured shape with no fitted constant. Price still clears in
    merit order *within* the envelope. Modifies ``fleet_arrays`` in place.

    Returns ``True`` when a shape was applied, ``False`` when the node is absent
    or no measured envelope is available (forecast year / unmapped ISO), in
    which case the static node is left unchanged (byte-identical).

    With ``export_only=True`` the import-availability cap is skipped: only the
    export side (the midday-export envelope) is shaped, leaving every import
    tranche available in every hour. The full (both-sided) shape caps *gross*
    import availability to the *net*-import envelope (net << gross, since CAISO
    imports and exports simultaneously across different interties), which
    starves baseload imports and substitutes gas — inflating gas TWh and the
    mean LMP. Export-only keeps the part that helps (the midday export cap, so
    surplus beyond the measured export curtails and prices negative) and drops
    the part that regresses the mix.

    ``import_percentile`` / ``export_percentile`` override ``percentile`` per
    direction (the caller sources these from ``config.interchange_shape_
    import_pct`` / ``_export_pct`` — see :class:`~market_sim.config.scenarios
    .ScenarioConfig` — rather than an environment variable, so the value that
    ran is visible in the persisted ``run_config.json``). Each defaults to
    ``percentile`` when not given, so a caller that only ever passed the
    positional ``percentile`` gets byte-identical behavior.
    """
    from market_sim.data.eia_loader import measured_interchange_envelope
    from market_sim.data.fleet import FUEL_TYPE_MAP

    # The envelope percentile sets how tightly the measured diurnal interchange
    # caps the priced node. Under the bidirectional intertie (gross == net), the
    # net-import envelope IS the deliverable import, so the import cap can ride a
    # higher percentile (fatter overnight tail) without re-admitting the midday
    # imports the (near-zero) midday envelope already excludes. Overridable per
    # direction for the bidir sweep via import_percentile/export_percentile;
    # each defaults to the passed ``percentile`` so the legacy export-only path
    # is byte-identical.
    import_pct = float(percentile if import_percentile is None else import_percentile)
    export_pct = float(percentile if export_percentile is None else export_percentile)
    import_code = FUEL_TYPE_MAP["import"]
    is_node = fleet_arrays.fuel_type_idx == import_code
    imp_rows = np.flatnonzero(is_node & (fleet_arrays.pmax > 0.0))
    exp_rows = np.flatnonzero(
        is_node & (fleet_arrays.pmax <= 0.0) & (fleet_arrays.pmin < 0.0)
    )
    if imp_rows.size == 0 and exp_rows.size == 0:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    env = measured_interchange_envelope(iso, year, hours, import_pct)
    if env is None:
        return False
    import_cap, _ = env
    if export_pct == import_pct:
        _, export_cap = env
    else:
        env_exp = measured_interchange_envelope(iso, year, hours, export_pct)
        if env_exp is None:
            return False
        _, export_cap = env_exp

    if imp_rows.size and not export_only:
        import_total = float(fleet_arrays.pmax[imp_rows].sum())
        if import_total > 0.0:
            imp_avail = np.clip(import_cap / import_total, 0.0, 1.0)
            for r in imp_rows:
                fleet_arrays.availability[r, :] *= imp_avail

    if exp_rows.size:
        export_total = float(-fleet_arrays.pmin[exp_rows].sum())
        if export_total > 0.0:
            exp_frac = np.clip(export_cap / export_total, 0.0, 1.0)
            if fleet_arrays.min_gen is None:
                fleet_arrays.min_gen = np.broadcast_to(
                    fleet_arrays.pmin[:, np.newaxis],
                    (fleet_arrays.pmin.size, hours),
                ).copy()
            for r in exp_rows:
                fleet_arrays.min_gen[r, :] = fleet_arrays.pmin[r] * exp_frac
    return True


def apply_reference_price_seam_injections(
    fleet_arrays,
    mc,
    config,
    iso: str,
    year: int,
    *,
    carbon_price: float = 0.0,
    gas_scenario: str = "mid",
    forward_skill: str | None = None,
) -> None:
    """Registry step: the generic (non-CAISO) reference-price seam block.

    Verbatim step 1 of the historical ``apply_interchange_injections``
    monolith: the gas x heat-rate x load-shape seam prices
    (:func:`inject_reference_price_mc`, with the MISO
    ``miso_pjm_border_anchor`` re-anchor when set), the firm scheduled-export
    floor (skipped where the measured PJM seam ladder displaces it — rule
    19), and the ``miso_firm_import_floor`` mirror. Self-gates on
    ``config.reference_price_interface`` and INTERFACE_NEIGHBORS membership
    exactly as the monolith did, so a registry entry for an ISO with no seam
    registry is a byte-identical no-op.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    _forward_skill = forward_skill
    # --- 1. Generic reference-price seam (non-CAISO; CAISO uses its dedicated
    #     caiso_reference_price_seam block below, which adds the CARB border
    #     carbon — the generic single-node path never applies to CAISO). ---
    if (
        getattr(config, "reference_price_interface", False)
        and iso in INTERFACE_NEIGHBORS
        and iso != "CAISO"
    ):
        _border_anchor = getattr(config, "miso_pjm_border_anchor", False)
        if inject_reference_price_mc(
            fleet_arrays,
            mc,
            iso,
            year,
            gas_scenario,
            border_anchor=_border_anchor,
            forward_skill=_forward_skill,
        ):
            _logger.info(
                "%s %d: reference-price interface — %d neighbor seams priced "
                "from gas x heat-rate x load-shape (hurdle in $/MWh)%s",
                iso,
                year,
                len(INTERFACE_NEIGHBORS.get(iso, [])),
                "; PJM seam re-anchored to its western (ComEd/AEP/ATSI) border hubs"
                if _border_anchor and iso == "MISO"
                else "",
            )
        # The measured PJM seam ladder DISPLACES the firm scheduled-export
        # floor on the years it covers (rule 19 — alternatives, never
        # stacked): the firm base the floor pins is exactly the deep-duration
        # structure the ladder prices (its base export band clears in ~97-100%
        # of hours economically). Forecast years have no ladder entry AND no
        # floor entry, so both paths no-op identically there.
        from market_sim.config.interchange_config import PJM_SEAM_LADDER_BY_YEAR

        _pjm_ladder_active = (
            iso == "PJM"
            and getattr(config, "pjm_seam_measured_ladder", False)
            and year in PJM_SEAM_LADDER_BY_YEAR
        )
        if not _pjm_ladder_active and inject_reference_price_firm_export(
            fleet_arrays, iso, year
        ):
            _logger.info(
                "%s %d: firm scheduled-export floor applied (must-flow seam base)",
                iso,
                year,
            )
        if getattr(config, "miso_firm_import_floor", False):
            if inject_reference_price_firm_import(fleet_arrays, iso, year):
                _logger.info(
                    "%s %d: firm scheduled-import floor applied (must-flow seam "
                    "base — net-import seam, displaces marginal domestic coal/CC)",
                    iso,
                    year,
                )
