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
import scipy.sparse as sp

from market_sim.config.constants import (
    CARB_UNSPECIFIED_IMPORT_EF,
    EXPORT_TRANCHES,
    IMPORT_EFORD,
    IMPORT_NODE_LINKS,
    IMPORT_TRANCHES,
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
    iso: str, border_carbon_per_mwh: float = 0.0
) -> list[Generator]:
    """Return an ISO's import node as a list of pseudo-generators.

    The aggregate import capability from the ISO's neighbors is modeled as a
    stepped supply curve: each tranche of
    :data:`~market_sim.config.constants.IMPORT_TRANCHES` becomes a synthetic
    :class:`~market_sim.data.fleet.Generator` in the ISO's external zone.
    The marginal cost of a tranche is set directly through the ``vom``
    field; ``heat_rate`` is zero, so no fuel price enters the cost. Appended
    to the fleet, the tranches compete in merit order through the ordinary
    energy balance and the external zone's links into the ISO's trading
    zones -- no special LP formulation is needed.

    A border carbon adjustment (CAISO: see :func:`wecc_border_carbon_adder`)
    enters as ``border_carbon_per_mwh``, added to every tranche's price. It
    is carried in the tranche VOM rather than as an ``emission_rate_co2`` so
    the import carbon cost reaches the merit order without the import MWh
    inflating the modeled *in-state* CO2 total that calibration benchmarks
    against eGRID generation-based emissions.

    Args:
        iso: ISO identifier, e.g. ``"CAISO"`` or ``"PJM"``.
        border_carbon_per_mwh: Border carbon adjustment ($/MWh) added to
            each tranche price; 0 disables it.

    Returns:
        Import tranches ordered cheapest first; empty for an ISO with no
        import node configured (e.g. ERCOT, whose DC-tie interchange rides
        in its demand series).
    """
    zone = IMPORT_ZONE.get(iso)
    return [
        Generator(
            unit_id=f"{zone}_{name}",
            name=name,
            zone=zone,
            fuel_type="import",
            pmax_mw=capacity,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=marginal_cost + border_carbon_per_mwh,
            eford=IMPORT_EFORD.get(iso, 0.0),
        )
        for name, capacity, marginal_cost in IMPORT_TRANCHES.get(iso, [])
    ]


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
    """Return the CAISO export sink (see :func:`build_export_sinks`)."""
    return build_export_sinks("CAISO")[0]
