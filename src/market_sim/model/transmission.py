"""Transmission network representation and constraints.

Implements the pipe-and-bubble (transportation) model of inter-zonal
transmission: each zone is a copper-plate "bubble" and each transfer link
is a "pipe" with a total-transfer-capability limit. The incidence/ttc
builders turn a list of :class:`~market_sim.config.iso_configs.TransferLink`
objects into the ``incidence`` and ``ttc`` arrays that
:func:`~market_sim.model.dispatch.solve_dispatch` already accepts.

The CAISO WECC import node is also modeled here: rather than a bespoke LP
formulation, the rest of the WECC is represented as a handful of synthetic
:class:`~market_sim.data.fleet.Generator` objects in the ``WECC_import``
zone. Appended to the fleet, they participate in dispatch purely through
the ordinary energy balance and the WECC_import -> CAISO_main link.
"""

import numpy as np
import scipy.sparse as sp

from market_sim.config.iso_configs import TransferLink
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


def build_wecc_import_generators() -> list[Generator]:
    """Return the CAISO WECC import node as a list of pseudo-generators.

    The aggregate import capability into CAISO from the rest of the WECC is
    modeled as a stepped supply curve: each tranche is a synthetic
    :class:`~market_sim.data.fleet.Generator` in the ``WECC_import`` zone.
    The marginal cost of a tranche is set directly through the ``vom``
    field; ``heat_rate`` is zero, so no fuel price enters the cost. Appended
    to the fleet, the tranches compete in merit order through the ordinary
    energy balance and the WECC_import -> CAISO_main link -- no special LP
    formulation is needed.

    Returns:
        Four import tranches ordered cheapest first, spanning 15000 MW.
    """
    # (name, capacity MW, marginal cost $/MWh) for each import tranche.
    # TODO: fit these tranche capacities and marginal costs from EIA-930
    # interchange data instead of the hand-set placeholders below.
    tranches: list[tuple[str, float, float]] = [
        ("PNW_hydro", 3000.0, 15.0),
        ("DSW_CCGT", 5000.0, 35.0),
        ("DSW_CT", 4000.0, 55.0),
        ("Expensive_import", 3000.0, 80.0),
    ]
    return [
        Generator(
            unit_id=f"WECC_import_{name}",
            name=name,
            zone="WECC_import",
            fuel_type="import",
            pmax_mw=capacity,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=marginal_cost,
            eford=0.02,
        )
        for name, capacity, marginal_cost in tranches
    ]


def build_wecc_export_sink() -> Generator:
    """Return the CAISO export "sink" as a single pseudo-generator.

    CAISO surplus -- typically midday solar that exceeds in-state demand --
    is exported across the WECC_import -> CAISO_main link into the
    ``WECC_import`` zone, where this sink absorbs it. Absorption is modeled
    as *negative* generation: the unit's output is bounded in ``[-5000, 0]``
    MW, so a dispatch of ``-x`` withdraws ``x`` MW from the WECC_import
    node. The 5000 MW export capability is therefore carried by ``pmin_mw``,
    and ``pmax_mw`` is held at zero so the sink can never inject phantom
    cheap power and distort the import merit order.

    Returns:
        A 5000 MW export sink located in the ``WECC_import`` zone.
    """
    # TODO: fit the export capability from EIA-930 interchange data.
    return Generator(
        unit_id="WECC_export_sink",
        name="WECC_export_sink",
        zone="WECC_import",
        fuel_type="import",
        pmax_mw=0.0,
        pmin_mw=-5000.0,
        heat_rate=0.0,
        vom=0.0,
        eford=0.0,
    )
