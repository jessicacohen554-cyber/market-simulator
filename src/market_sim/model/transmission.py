"""Transmission network representation and constraints.

Implements the pipe-and-bubble (transportation) model of inter-zonal
transmission: each zone is a copper-plate "bubble" and each transfer link
is a "pipe" with a total-transfer-capability limit. The incidence/ttc
builders turn a list of :class:`~market_sim.config.iso_configs.TransferLink`
objects into the ``incidence`` and ``ttc`` arrays that
:func:`~market_sim.model.dispatch.solve_dispatch` already accepts.

Priced import/export nodes are also modeled here: rather than a bespoke LP
formulation, an ISO's neighbors are represented as a handful of synthetic
:class:`~market_sim.data.fleet.Generator` objects in the ISO's external
zone (:data:`~market_sim.config.constants.IMPORT_ZONE`) — import supply
tranches plus export sinks. Appended to the fleet, they participate in
dispatch purely through the ordinary energy balance and the external zone's
links into the ISO's trading zones. CAISO's WECC node was the original;
the same machinery now serves PJM (and is data-driven, so NYISO/NEISO only
need constants entries).
"""

import numpy as np
import pandas as pd
import scipy.sparse as sp

from market_sim.config.constants import (
    CARB_UNSPECIFIED_IMPORT_EF,
    EXPORT_TRANCHES,
    IMPORT_EFORD,
    IMPORT_NODE_LINKS,
    IMPORT_TRANCHE_EF,
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
    IMPORT_ZONE,
)
from market_sim.config.iso_configs import ISOConfig, TransferLink, Zone
from market_sim.data.fleet import Generator


def build_incidence_matrix(
    links: list[TransferLink], zone_names: list[str]
) -> sp.csr_matrix:
    """Return the node-link incidence matrix of the transmission network.

    The result has shape ``(n_zones, n_links)``. For each link the
    ``from_zone`` row entry is ``-1`` (the exporting zone loses power) and
    the ``to_zone`` row entry is ``+1`` (the importing zone gains power).
    A positive link flow therefore moves power from ``from_zone`` to
    ``to_zone``.

    Args:
        links: Transfer links connecting pairs of zones.
        zone_names: Ordered zone names; row index of each zone.

    Returns:
        A CSR incidence matrix of shape ``(n_zones, n_links)``.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)
    n_links = len(links)

    rows = np.empty(2 * n_links, dtype=int)
    cols = np.empty(2 * n_links, dtype=int)
    data = np.empty(2 * n_links, dtype=float)
    for ln, link in enumerate(links):  # ln: transmission link index
        rows[2 * ln] = zone_to_idx[link.from_zone]
        rows[2 * ln + 1] = zone_to_idx[link.to_zone]
        cols[2 * ln] = ln
        cols[2 * ln + 1] = ln
        data[2 * ln] = -1.0  # exporting zone
        data[2 * ln + 1] = 1.0  # importing zone

    return sp.csr_matrix((data, (rows, cols)), shape=(n_zones, n_links))


def get_ttc_array(links: list[TransferLink]) -> np.ndarray:
    """Return the ``(n_links,)`` array of total transfer capabilities in MW."""
    return np.array([link.ttc_mw for link in links], dtype=float)


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
    :data:`~market_sim.config.constants.IMPORT_TRANCHES` becomes a synthetic
    :class:`~market_sim.data.fleet.Generator` in the ISO's external zone.
    When ``year`` matches an
    :data:`~market_sim.config.constants.IMPORT_TRANCHES_BY_YEAR` entry for the
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
    (:data:`~market_sim.config.constants.IMPORT_TRANCHE_EF`), so a firm
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
    tranches = IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year) if (
        year is not None
    ) else None
    if tranches is None:
        tranches = IMPORT_TRANCHES.get(iso, [])
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    gens = []
    for name, capacity, marginal_cost in tranches:
        ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
        tranche_carbon = border_carbon_per_mwh * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        gens.append(Generator(
            unit_id=f"{zone}_{name}",
            name=name,
            zone=zone,
            fuel_type="import",
            pmax_mw=capacity,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=marginal_cost + tranche_carbon,
            eford=IMPORT_EFORD.get(iso, 0.0),
        ))
    return gens


def build_export_sinks(iso: str) -> list[Generator]:
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

    Returns:
        Export sinks in the ISO's external zone; empty when none are
        configured.
    """
    zone = IMPORT_ZONE.get(iso)
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
        for name, capacity, price in EXPORT_TRANCHES.get(iso, [])
    ]


# Unit-id markers tagging a reference-price seam pseudo-generator so the
# post-assembly mc injector (:func:`inject_reference_price_mc`) can find each row
# and map it back to its neighbor. Import rows take the neighbor price + hurdle;
# export rows take the neighbor price - hurdle.
_REF_IMPORT_MARK = "_refimp_"
_REF_EXPORT_MARK = "_refexp_"


def build_reference_price_node(iso: str) -> list[Generator]:
    """Return the reference-price seam as import/export pseudo-generators.

    The forecast-grade replacement for the fitted
    :func:`build_import_generators` / :func:`build_export_sinks`: one import
    pseudo-generator and one export sink **per neighbor** in
    :data:`~market_sim.config.constants.INTERFACE_NEIGHBORS`, each sized to that
    neighbor's interface transfer limit and placed in the ISO's external zone.
    The marginal cost is left at zero here — it is a *placeholder* overwritten
    hour-by-hour with the neighbor's reference price ± hurdle by
    :func:`inject_reference_price_mc` after the fleet's mc is assembled (the cost
    is hourly, so it cannot ride in the static ``vom``). The unit id carries the
    neighbor name (via :data:`_REF_IMPORT_MARK` / :data:`_REF_EXPORT_MARK`) so
    the injector can map each row back to its neighbor.

    Import rows are ordinary positive-output generators bounded ``[0, limit]``;
    export sinks are negative-output blocks bounded ``[-limit, 0]`` (the same
    convention as :func:`build_export_sinks`). With every neighbor in the one
    external bubble, the LP trades with the cheapest neighbor to import from and
    the dearest to export to each hour, in merit order, bounded by each
    neighbor's limit and the external zone's border-link TTCs.

    Args:
        iso: ISO identifier; must have an entry in ``INTERFACE_NEIGHBORS`` and
            in :data:`~market_sim.config.constants.IMPORT_ZONE`.

    Returns:
        Import + export pseudo-generators; empty for an ISO with no neighbor
        registry (so an un-onboarded ISO stays byte-identical).
    """
    from market_sim.config.constants import INTERFACE_NEIGHBORS

    zone = IMPORT_ZONE.get(iso)
    gens: list[Generator] = []
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
        gens.append(Generator(
            unit_id=f"{zone}{_REF_IMPORT_MARK}{neighbor.name}",
            name=f"ref_import_{neighbor.name}",
            zone=zone,
            fuel_type="import",
            pmax_mw=neighbor.interface_limit_mw,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=0.0,
            eford=0.0,
        ))
        gens.append(Generator(
            unit_id=f"{zone}{_REF_EXPORT_MARK}{neighbor.name}",
            name=f"ref_export_{neighbor.name}",
            zone=zone,
            fuel_type="import",
            pmax_mw=0.0,
            pmin_mw=-neighbor.interface_limit_mw,
            heat_rate=0.0,
            vom=0.0,
            eford=0.0,
        ))
    return gens


def inject_reference_price_mc(
    fleet_arrays, mc: np.ndarray, iso: str, year: int,
    gas_scenario: str = "mid",
) -> bool:
    """Overwrite the reference-price seam rows of ``mc`` with hourly prices.

    Mirrors :func:`inject_interchange_shape`'s post-assembly pattern, but for
    cost rather than availability: after the fleet's marginal-cost matrix is
    assembled, each reference-price pseudo-generator's row is replaced with its
    neighbor's hourly reference price (from
    :func:`market_sim.data.neighbor_price.interface_reference_prices`) plus a
    hurdle for an import row and minus a hurdle for an export row. So PJM imports
    from a neighbor only when its own LMP exceeds that neighbor's price by the
    hurdle, and exports only when it falls below by the hurdle. A neighbor that
    resolved no individual price (no load extract or proxy) falls back to the
    capacity-weighted aggregate. Modifies ``mc`` in place.

    Returns ``True`` when at least one seam row was priced, ``False`` when the
    fleet has no reference-price node (so a non-reference run is untouched).
    """
    from market_sim.config.constants import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import interface_reference_prices

    hours = int(mc.shape[1])
    prices = interface_reference_prices(iso, year, hours, gas_scenario)
    aggregate = prices.aggregate()
    specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(iso, [])}
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if _REF_IMPORT_MARK in uid:
            name, sign = uid.rsplit(_REF_IMPORT_MARK, 1)[1], +1.0
        elif _REF_EXPORT_MARK in uid:
            name, sign = uid.rsplit(_REF_EXPORT_MARK, 1)[1], -1.0
        else:
            continue
        price = prices.per_neighbor.get(name, aggregate)
        if price is None:
            continue
        hurdle = specs[name].hurdle if name in specs else 0.0
        mc[row, :] = price + sign * hurdle
        applied = True
    return applied


def extend_with_import_node(iso_config: ISOConfig) -> ISOConfig:
    """Return ``iso_config`` with its external import/export zone appended.

    Adds the ISO's :data:`~market_sim.config.constants.IMPORT_ZONE` as a
    zero-load zone plus its border links
    (:data:`~market_sim.config.constants.IMPORT_NODE_LINKS`). A no-op when
    the ISO has no import node configured or the zone is already part of
    the topology (CAISO bakes ``WECC_import`` into ``_caiso_config``).

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
    extended = iso_config.model_copy(
        update={
            "zones": [
                *iso_config.zones,
                Zone(name=zone, iso=iso, load_share=0.0),
            ],
            "links": [*iso_config.links, *links],
        }
    )
    extended.validate_topology()
    return extended


def build_wecc_import_generators(
    border_carbon_per_mwh: float = 0.0,
) -> list[Generator]:
    """Return the CAISO WECC import node (see :func:`build_import_generators`)."""
    return build_import_generators("CAISO", border_carbon_per_mwh)


def build_wecc_export_sink() -> Generator:
    """Return CAISO's $0 curtailment export sink.

    CAISO has two export sinks (a shallow midday-solar block and this deeper
    curtailment floor; see :func:`build_export_sinks`). This convenience
    wrapper returns the $0 curtailment block — the "free" sink that absorbs
    surplus that would otherwise be shed.
    """
    sinks = build_export_sinks("CAISO")
    return min(sinks, key=lambda g: g.vom)


def inject_interchange_shape(
    fleet_arrays, iso: str, year: int, percentile: float = 90.0
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
    """
    from market_sim.data.eia_loader import measured_interchange_envelope
    from market_sim.data.fleet import FUEL_TYPE_MAP

    import_code = FUEL_TYPE_MAP["import"]
    is_node = fleet_arrays.fuel_type_idx == import_code
    imp_rows = np.flatnonzero(is_node & (fleet_arrays.pmax > 0.0))
    exp_rows = np.flatnonzero(
        is_node & (fleet_arrays.pmax <= 0.0) & (fleet_arrays.pmin < 0.0)
    )
    if imp_rows.size == 0 and exp_rows.size == 0:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    env = measured_interchange_envelope(iso, year, hours, percentile)
    if env is None:
        return False
    import_cap, export_cap = env

    if imp_rows.size:
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


# Midday solar-glut window (local hour-of-day, ``[start, end)``) over which the
# CAISO RA must-offer gas floor binds — the duck-curve belly when CAISO is long
# and exports/curtails its surplus. Outside it the gas fleet dispatches purely
# economically (no floor), so the evening ramp and overnight hours are
# unchanged. Mirrors the existing seasonal must-run windows (``_GAS_ST_SUMMER_
# MONTHS`` in data/fleet.py): a documented operating window, not a fitted value.
CAISO_GAS_FLOOR_HOURS: tuple[int, int] = (9, 16)


def inject_caiso_gas_commitment_floor(
    fleet_arrays,
    iso: str,
    year: int,
    frac: float = 1.0,
    percentile: float = 50.0,
    hod_window: tuple[int, int] = CAISO_GAS_FLOOR_HOURS,
) -> bool:
    """Floor the CAISO gas fleet midday at the measured EIA-930 ``NG: NG``.

    Models CAISO's Resource-Adequacy **must-offer** obligation: RA-committed
    gas stays online at minimum load through the midday solar glut (it cannot
    economically cycle off and back on for the evening ramp), so it
    over-generates midday and the ISO exports/curtails the surplus at ~$0. The
    economic dispatch instead decommits gas to ~2 GW midday and imports the
    balance, staying balanced — so its marginal is always a ≥$28 import/gas and
    the midday LMP floors far above the real ~$0/negative price.

    After :func:`~market_sim.data.fleet.generators_to_fleet_arrays` builds the
    fleet, this imposes a hard minimum-generation floor on the flexible gas
    fleet (``gas_cc`` / ``gas_ct`` — the RA must-offer fleet; near-retired
    ``gas_st`` boilers are excluded) over the midday ``hod_window``,
    sized to ``frac`` × the measured EIA-930 ``NG: NG`` (month×hour-of-day
    ``percentile``) profile (:func:`~market_sim.data.eia_loader
    .measured_gas_floor_profile`). The hourly fleet target is distributed over
    the gas units **cheapest-first** (by heat rate), each capped at its
    available capacity — the same hour-varying ``FleetArrays.min_gen`` lower
    bound the CHP steam floor and the CT reliability-deployment overlay use, and
    composed with any floor already present via ``maximum``. The floor makes the
    model long midday; pair it with ``--interchange-shaping`` (export side) and
    the $0 export/curtailment sink so the surplus prices at ~$0.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when ``iso`` is not CAISO, ``frac`` is
    non-positive, the fleet has no gas units, or no measured ``NG: NG`` profile
    is available (forecast year / unmapped ISO).
    """
    if iso != "CAISO" or frac <= 0.0:
        return False
    from market_sim.data.eia_loader import measured_gas_floor_profile
    from market_sim.data.fleet import FUEL_TYPE_MAP

    # The RA must-offer midday fleet is the flexible CC/CT gas that stays
    # online for the evening ramp — NOT the near-retired gas-steam boilers
    # (CA gas_st is ~0.15 TWh/yr in EIA-923; they are local-reliability/off,
    # not held online midday). Including gas_st let the floor manufacture
    # ~1.9 TWh of phantom steam (ST_GAS 1.7 -> 3.7 TWh in 2024). Scope it to
    # gas_cc/gas_ct so the measured NG: NG midday target is met by the real
    # must-offer fleet.
    gas_codes = [FUEL_TYPE_MAP[f] for f in ("gas_cc", "gas_ct")]
    is_gas = np.isin(fleet_arrays.fuel_type_idx, gas_codes)
    gas_rows = np.flatnonzero(is_gas & (fleet_arrays.pmax > 0.0))
    if gas_rows.size == 0:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    profile = measured_gas_floor_profile(iso, year, hours, percentile)
    if profile is None:
        return False

    # Restrict the floor to the midday window (zero elsewhere). Row 0 of the
    # dispatch is the first local hour of the year, so a plain local clock
    # reproduces the hour-of-day index (the interchange-envelope convention).
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    hod = clock.hour.to_numpy()
    start, end = hod_window
    midday = (hod >= start) & (hod < end)
    target = np.zeros(hours, dtype=float)
    target[midday] = frac * np.asarray(profile, dtype=float)[midday]

    # Never demand more gas than the fleet can supply that hour, so a feasible
    # LP solution always exists (the floor cannot manufacture unmet demand).
    avail_cap = (
        fleet_arrays.pmax[gas_rows, np.newaxis]
        * fleet_arrays.availability[gas_rows, :]
    )
    np.minimum(target, avail_cap.sum(axis=0), out=target)

    if fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis],
            (fleet_arrays.pmin.size, hours),
        ).copy()

    # Distribute the hourly fleet target cheapest-first (by heat rate), each
    # unit capped at its available capacity — the convention the CT/reliability
    # deployment overlays use (data/fleet.py). ``maximum`` composes the floor
    # with any CHP/ST/export floor already in min_gen rather than clobbering it.
    order = gas_rows[
        np.argsort(fleet_arrays.heat_rate[gas_rows], kind="stable")
    ]
    remaining = target.copy()
    for r in order:
        cap = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap)
        np.maximum(
            fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :]
        )
        remaining = remaining - take
    return True
