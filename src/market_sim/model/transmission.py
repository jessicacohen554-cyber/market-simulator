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

import os as _os

import numpy as np
import pandas as pd
import scipy.sparse as sp

from market_sim.config.constants import (
    CAISO_CORRIDOR_ATC_SOLAR_K,
    CAISO_IMPORT_DELIVERY_BASIS,
    CAISO_IMPORT_TRANCHE_HUB,
    CAISO_PER_HUB_IMPORT_ZONES,
    CAISO_PER_HUB_NEIGHBORS,
    CARB_UNSPECIFIED_IMPORT_EF,
    EXPORT_TRANCHES,
    IMPORT_EFORD,
    IMPORT_NODE_LINKS,
    IMPORT_TRANCHE_EF,
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
    IMPORT_ZONE,
    MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC,
    MISO_MANITOBA_FIRM_IMPORT_NAME,
    MISO_MANITOBA_FIRM_IMPORT_OFFER,
    MISO_MANITOBA_FIRM_IMPORT_ZONE,
    NYISO_FIRM_IMPORT_FLOOR_FRAC,
    NYISO_IMPORT_RECON_BAND_FRAC,
    NYISO_LOCAL_SELFSUPPLY_FRAC,
    resolve_miso_manitoba_firm_import_mw,
)
from market_sim.config.iso_configs import (
    InterfaceLimit,
    ISOConfig,
    TransferLink,
    Zone,
)
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


def build_interface_groups(
    links: list[TransferLink], interface_limits: list[InterfaceLimit]
) -> list[tuple[np.ndarray, float, bool]]:
    """Resolve aggregate interface limits to LP flow-column groups.

    Maps each :class:`~market_sim.config.iso_configs.InterfaceLimit`'s
    ``(from_zone, to_zone)`` link references to their indices in ``links`` (the
    flow-block column order), returning one
    ``(link_idx, cap_mw, bidirectional)`` tuple per limit for
    :func:`market_sim.model.dispatch.build_constraints`. Returns an empty list
    when the ISO declares no interface limits (the LP is then identical).
    """
    pair_to_idx = {(ln.from_zone, ln.to_zone): i for i, ln in enumerate(links)}
    groups: list[tuple[np.ndarray, float, bool]] = []
    for limit in interface_limits:
        idx = np.array([pair_to_idx[tuple(pair)] for pair in limit.links], dtype=int)
        groups.append((idx, float(limit.cap_mw), bool(limit.bidirectional)))
    return groups


def get_link_bidirectional_array(links: list[TransferLink]) -> np.ndarray:
    """Return the ``(n_links,)`` bool array of per-link bidirectionality.

    ``True`` (the default) lets a link carry power both ways up to its TTC;
    ``False`` makes it one-way (from->to only, ``0 <= flow <= ttc``), so a
    pair of opposite one-way links can give an interface an asymmetric rating
    (e.g. a tight import limit into a load pocket with a looser export limit).
    Returns all-``True`` when every link is bidirectional (the LP then leaves
    the symmetric ``-ttc <= flow <= ttc`` path byte-identical).
    """
    return np.array(
        [getattr(link, "is_bidirectional", True) for link in links], dtype=bool
    )


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


# Single-signed-flow WECC intertie (``caiso_bidir_intertie``). The legacy
# representation modeled CAISO's tie as TWO independent one-way mechanisms on
# the same external node — priced import tranches (:func:`build_import_generators`)
# and separate export sinks (:func:`build_export_sinks`) — so the LP could
# simultaneously import the cheap midday hub AND stay long on its own solar (the
# two never netted: 2024 diurnal interchange corr −0.65, anti-correlated). The
# bidirectional intertie collapses both legs onto ONE signed flow over a shared
# directional cap: import (flow into CAISO) priced at hub + per-tranche border
# carbon, export (flow out of CAISO) priced at the hub (no CA carbon). Because
# every import leg (hub + carbon, carbon ≥ 0) is priced at or above the export
# leg (hub) at every hour, the two legs are arbitrage-free *by construction*, so
# the LP never imports and exports in the same hour — one net direction per hour,
# no MIP. Caps are the measured directional limits.
CAISO_BIDIR_IMPORT_CAP_MW = 8300.0  # aggregate simultaneous-import limit (the
# import-tightening cap: WECC COI/Path 66 + Path 46/WOR deliverable import into
# CAISO, ~ the deep-import hours of the EIA-930 CISO net-interchange curve).
CAISO_BIDIR_EXPORT_CAP_MW = 3500.0  # measured export-direction peak (EIA-930
# CISO 2024 net export reverses to ~+3.5 GW in the midday solar glut).
_CAISO_BIDIR_EXPORT_NAME = "export_bidir"
# Intertie throughput tiebreaker (same role/magnitude as the storage ε = 0.001
# $/MWh in the objective): the cheapest import leg (firm hydro/solar, zero CARB
# EF) prices exactly at the hub, which is also the export price, so a gross
# round-trip (import + export in the same hour) is cost-NEUTRAL and the LP is
# free to return a degenerate wash that inflates the gross interchange. Charging
# this ε on each direction makes any round-trip strictly cost-positive (2ε), so
# the tie nets to one direction per hour. Negligible vs the price body; not a
# fitted level.
CAISO_INTERTIE_TIEBREAK_EPS = 1e-3


def build_caiso_bidir_intertie(border_carbon_per_mwh: float = 0.0) -> list[Generator]:
    """Return CAISO's WECC tie as a single signed flow (import leg + export leg).

    The structurally-faithful replacement for the separate
    :func:`build_import_generators` + :func:`build_export_sinks` pair on the
    ``WECC_import`` node. The import leg keeps the per-tranche supply curve of
    :data:`~market_sim.config.constants.IMPORT_TRANCHES` (so the rising
    border-carbon ladder of :data:`~market_sim.config.constants.IMPORT_TRANCHE_EF`
    is preserved — firm hydro/solar pay no CARB adder, unspecified gas pays the
    full one), but the aggregate import capacity is rescaled to
    :data:`CAISO_BIDIR_IMPORT_CAP_MW` (the tightened simultaneous-import cap).
    The export leg is a SINGLE sink bounded at :data:`CAISO_BIDIR_EXPORT_CAP_MW`,
    the measured export-direction peak.

    Both legs sit in the ISO's external zone and net through the ordinary energy
    balance + the WECC border links, so the LP's *net* interchange on the tie is
    one signed quantity. The energy prices are placeholders here — overwritten
    hour-by-hour by :func:`inject_caiso_bidir_intertie_prices` to the measured
    hub (import = hub + border carbon, export = hub), which makes the two legs
    arbitrage-free so only one direction clears per hour.

    Args:
        border_carbon_per_mwh: Unspecified-import border carbon adjustment
            ($/MWh); scaled per import tranche by its emission factor. 0 disables.

    Returns:
        The import tranches (cheapest first) followed by the single export sink.
    """
    iso = "CAISO"
    zone = IMPORT_ZONE[iso]
    base = IMPORT_TRANCHES.get(iso, [])
    total = sum(cap for _, cap, _ in base) or 1.0
    scale = CAISO_BIDIR_IMPORT_CAP_MW / total
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    gens: list[Generator] = []
    for name, capacity, marginal_cost in base:
        ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
        tranche_carbon = border_carbon_per_mwh * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        gens.append(
            Generator(
                unit_id=f"{zone}_{name}",
                name=name,
                zone=zone,
                fuel_type="import",
                pmax_mw=capacity * scale,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=marginal_cost + tranche_carbon,
                eford=IMPORT_EFORD.get(iso, 0.0),
            )
        )
    # Single export leg sharing the same signed tie (negative-generation sink;
    # see build_export_sinks for the sign convention). Priced at the hub (no CA
    # carbon) by inject_caiso_bidir_intertie_prices.
    gens.append(
        Generator(
            unit_id=f"{zone}_{_CAISO_BIDIR_EXPORT_NAME}",
            name=_CAISO_BIDIR_EXPORT_NAME,
            zone=zone,
            fuel_type="import",
            pmax_mw=0.0,
            pmin_mw=-CAISO_BIDIR_EXPORT_CAP_MW,
            heat_rate=0.0,
            vom=0.0,
            eford=0.0,
        )
    )
    return gens


# Per-hub signed WECC intertie (``caiso_per_hub_intertie``). The unification of
# the single-flow bidir node (which fixed the inverted diurnal sign but had to
# AVERAGE the two neighbor hubs into one price) and the per-hub-basis hub-price
# node (which kept Malin != Palo Verde but pooled both import legs + one averaged
# export sink onto a single bubble, so the cheap midday Palo Verde block filled
# the whole 8.3 GW budget over either link and never netted → over-import +
# inverted diurnal). Here CAISO's tie is its TWO REAL corridors, each a single
# signed flow priced at its OWN measured hub:
#   * WECC_PNW  — COI / Path 66, the Malin / Mid-C hub, into NP15 (north); holds
#     the PNW_* import tranches + one PNW export leg.
#   * WECC_DSW  — Path 46 / West-of-River, the Palo Verde / desert-SW hub, into
#     SP15 (south); holds the DSW_*/WECC_scarcity import tranches + one DSW
#     export leg.
# Per corridor every import leg (hub + wheel + border carbon, all ≥ 0) is priced
# at/above its export leg (hub − ε), so the two are arbitrage-free by
# construction → one net direction per hour per corridor (no MIP). The 8.3 GW
# simultaneous-import cap stays as the WECC_import_simultaneous interface limit,
# re-homed to the two corridor links by :func:`split_caiso_import_node_per_hub`.
# Export legs carry no separate fitted cap: the export volume is endogenous (how
# long CAISO is) and is bounded by the same physical corridor link TTCs + the
# bidirectional interface limit the imports use — the real WECC tie carries power
# both ways up to the same ratings (rule #12: a physical limit, not the measured
# export peak fitted as a constant).
_CAISO_PER_HUB_EXPORT_PREFIX = "export"


def _caiso_import_tranche_of(uid: str, default_zone: str | None) -> str | None:
    """Return the import-tranche name carried by ``uid``, in any CAISO import zone.

    Handles both the single pooled ``WECC_import`` node and the per-hub
    ``WECC_PNW`` / ``WECC_DSW`` corridors, so the gas-coupling / solar-shape
    injectors find the desert-SW blocks under whichever topology is active. The
    per-hub zone names are tried first (none is a prefix of ``default_zone``), and
    ``default_zone`` (``IMPORT_ZONE[iso]``) keeps the single-node path
    byte-identical. Returns ``None`` when ``uid`` is not in a CAISO import zone.
    """
    for zone in (*CAISO_PER_HUB_IMPORT_ZONES.values(), default_zone):
        if zone and uid.startswith(f"{zone}_"):
            return uid[len(zone) + 1 :]
    return None


def build_caiso_per_hub_intertie(border_carbon_per_mwh: float = 0.0) -> list[Generator]:
    """Return CAISO's WECC tie as TWO per-hub signed flows (Malin + Palo Verde).

    The structurally-faithful successor to :func:`build_caiso_bidir_intertie`
    (single averaged node) and the :func:`build_import_generators` +
    :func:`build_export_sinks` pair (pooled node). Each import tranche of
    :data:`~market_sim.config.constants.IMPORT_TRANCHES` is placed in the
    external zone of the WECC neighbor hub it proxies
    (:data:`~market_sim.config.constants.CAISO_IMPORT_TRANCHE_HUB` →
    :data:`~market_sim.config.constants.CAISO_PER_HUB_IMPORT_ZONES`), and each hub
    zone gets ONE export leg (a negative-generation sink, see
    :func:`build_export_sinks`). Tranche capacities are the natural
    :data:`IMPORT_TRANCHES` values (the simultaneous cap is the interface limit,
    not a per-tranche rescale, matching the keeper); the rising border-carbon
    ladder of :data:`~market_sim.config.constants.IMPORT_TRANCHE_EF` is preserved.

    Prices are placeholders, overwritten hour-by-hour by
    :func:`inject_caiso_per_hub_intertie_prices` to each leg's own measured hub.

    Args:
        border_carbon_per_mwh: Unspecified-import border carbon adjustment
            ($/MWh); scaled per import tranche by its emission factor. 0 disables.

    Returns:
        The per-hub import tranches (cheapest first within each hub) followed by
        one export leg per hub zone.
    """
    iso = "CAISO"
    base = IMPORT_TRANCHES.get(iso, [])
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    eford = IMPORT_EFORD.get(iso, 0.0)
    gens: list[Generator] = []
    for name, capacity, marginal_cost in base:
        hub = CAISO_IMPORT_TRANCHE_HUB.get(name)
        zone = CAISO_PER_HUB_IMPORT_ZONES.get(hub) if hub else None
        if zone is None:
            continue  # tranche with no hub mapping is dropped from the per-hub node
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
                eford=eford,
            )
        )
    # One export leg per hub zone (negative-generation sink). The export-direction
    # bound is the corridor's own physical link TTC; the bidirectional interface
    # limit caps the simultaneous export across both corridors at the same 8.3 GW
    # the imports share. Priced at the hub (no CA carbon) by the injector.
    for hub, zone in CAISO_PER_HUB_IMPORT_ZONES.items():
        gens.append(
            Generator(
                unit_id=f"{zone}_{_CAISO_PER_HUB_EXPORT_PREFIX}_{hub}",
                name=f"{_CAISO_PER_HUB_EXPORT_PREFIX}_{hub}",
                zone=zone,
                fuel_type="import",
                pmax_mw=0.0,
                pmin_mw=-_caiso_corridor_export_cap_mw(zone),
                heat_rate=0.0,
                vom=0.0,
                eford=0.0,
            )
        )
    return gens


def _caiso_corridor_export_cap_mw(zone: str) -> float:
    """Return the export-direction MW bound for a CAISO per-hub corridor zone.

    The physical corridor link TTC (COI ≈ 4,800 MW into NP15; Path-46/WOR ≈
    10,623 MW into SP15 — the same ratings the import direction uses). The
    bidirectional ``WECC_import_simultaneous`` interface limit (8.3 GW) caps the
    SUM of the two corridors' export flows, so this per-leg bound only stops a
    single corridor exceeding its own line rating — not a fitted export cap.
    """
    from market_sim.config.iso_configs import get_iso_config

    cfg = get_iso_config("CAISO")
    for link in cfg.links:
        if (
            link.from_zone == "WECC_import"
            and link.to_zone in _CAISO_CORRIDOR_LINK_TO.get(zone, ())
        ):
            return float(link.ttc_mw)
    return float("inf")


# Per-hub corridor zone → the CAISO trading zone its WECC import link terminates
# on (COI/Path-66 north → NP15; Path-46/WOR south → SP15). Used both to re-home
# the WECC_import links onto the per-hub zones and to read each corridor's TTC.
_CAISO_CORRIDOR_LINK_TO: dict[str, tuple[str, ...]] = {
    "WECC_PNW": ("NP15",),
    "WECC_DSW": ("SP15",),
}


def build_caiso_corridor_flow_groups(
    links: list[TransferLink],
    envelope: dict[str, np.ndarray],
    export_envelope: dict[str, np.ndarray] | None = None,
) -> list[tuple]:
    """Return per-hour interface groups capping each corridor's signed flow.

    For each per-hub corridor zone in ``envelope`` (``WECC_PNW`` / ``WECC_DSW``),
    finds the corridor's import link (``from_zone`` = corridor, ``to_zone`` =
    NP15/SP15 via :data:`_CAISO_CORRIDOR_LINK_TO`) and returns an interface group
    that caps that link's flow hour by hour at the measured deliverability
    envelope (via :func:`~market_sim.model.dispatch._build_interface_rows`).

    When ``export_envelope`` is ``None`` the group is one-sided
    ``(link_idx, import_cap, bidirectional=False)`` — only the import (positive,
    neighbor→CAISO) direction is bounded and the export direction keeps the
    link's own physical TTC (the original behaviour).

    When ``export_envelope`` is supplied the group is asymmetric
    ``(link_idx, import_cap, False, export_cap)`` — the import direction is capped
    at the corridor's p95 net-import ceiling and the export (negative) direction
    at its p95 net-*export* ceiling. The export ceiling collapses to ~0 in
    evening-ramp (month, hod) buckets where the corridor reliably net-imports, so
    the LP can no longer wheel cheap CA gas out across the seam in the evening
    peak (the structural CC over-dispatch + evening price inflation). Both are
    smoothed measured capability envelopes the LP clears *below*, not the hourly
    residual (rule #12). Pairs with
    :func:`~market_sim.data.eia_loader.measured_corridor_flow_envelope`
    (``direction="import"`` / ``"export"``); used by the calibration runner only
    when ``config.caiso_corridor_flow_limit`` is on.

    Returns an empty list when no corridor link is found (e.g. the per-hub split
    was not applied), so the LP is byte-identical off the flag.
    """
    pair_to_idx = {(ln.from_zone, ln.to_zone): i for i, ln in enumerate(links)}
    groups: list[tuple] = []
    for zone, cap in envelope.items():
        link_idx = next(
            (
                pair_to_idx[(zone, to_z)]
                for to_z in _CAISO_CORRIDOR_LINK_TO.get(zone, ())
                if (zone, to_z) in pair_to_idx
            ),
            None,
        )
        if link_idx is None:
            continue
        idx = np.array([link_idx], dtype=int)
        import_cap = np.asarray(cap, dtype=float)
        exp = export_envelope.get(zone) if export_envelope else None
        if exp is not None:
            groups.append((idx, import_cap, False, np.asarray(exp, dtype=float)))
        else:
            groups.append((idx, import_cap, False))
    return groups


def split_caiso_import_node_per_hub(iso_config: ISOConfig) -> ISOConfig:
    """Split CAISO's single ``WECC_import`` node into the two per-hub corridors.

    Returns a copy of ``iso_config`` in which the single ``WECC_import`` external
    zone is replaced by ``WECC_PNW`` (COI/Path-66 → NP15) and ``WECC_DSW``
    (Path-46/WOR → SP15), the two ``WECC_import`` import links are re-homed onto
    those zones, and the ``WECC_import_simultaneous`` interface limit is rewritten
    to span the two corridor links (so the 8.3 GW simultaneous-import cap is
    preserved). Internal CAISO links (Path 15/26) and every other field are
    unchanged. A no-op (the same config) for a non-CAISO ISO or one without a
    ``WECC_import`` node, so the build path stays byte-identical off the flag.

    Paired with :func:`build_caiso_per_hub_intertie` /
    :func:`inject_caiso_per_hub_intertie_prices`; used by the calibration runner
    only when ``config.caiso_per_hub_intertie`` is on.
    """
    if not any(z.name == "WECC_import" for z in iso_config.zones):
        return iso_config
    # Map WECC_import → corridor zone by the trading zone each link terminates on.
    to_zone_corridor = {
        to_z: corridor
        for corridor, tos in _CAISO_CORRIDOR_LINK_TO.items()
        for to_z in tos
    }
    zones = [z for z in iso_config.zones if z.name != "WECC_import"]
    for corridor in CAISO_PER_HUB_IMPORT_ZONES.values():
        zones.append(Zone(name=corridor, iso=iso_config.name, load_share=0.0))
    links = []
    for link in iso_config.links:
        if link.from_zone == "WECC_import":
            corridor = to_zone_corridor.get(link.to_zone)
            if corridor is None:
                raise ValueError(
                    f"WECC_import link to {link.to_zone!r} has no per-hub corridor"
                )
            links.append(link.model_copy(update={"from_zone": corridor}))
        else:
            links.append(link)
    interface_limits = []
    for lim in iso_config.interface_limits:
        new_links = [
            (to_zone_corridor.get(to_z, frm), to_z)
            if frm == "WECC_import"
            else (frm, to_z)
            for frm, to_z in lim.links
        ]
        interface_limits.append(lim.model_copy(update={"links": new_links}))
    return iso_config.model_copy(
        update={"zones": zones, "links": links, "interface_limits": interface_limits}
    )


def inject_caiso_per_hub_intertie_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
    carbon_price: float,
) -> bool:
    """Price each CAISO per-hub corridor at its OWN measured intertie hub.

    The per-hub analogue of :func:`inject_caiso_bidir_intertie_prices`: each
    corridor (WECC_PNW / WECC_DSW) is a single signed flow priced from the
    measured hub of the neighbor it proxies
    (:func:`market_sim.data.eia_loader.measured_import_hub_prices`, which returns
    one series per import tranche keyed to its hub). For every row::

        import leg → hub + wheel + border_carbon × (EF / EF_unspecified) + ε
        export leg → hub − ε

    where ``hub`` is the tranche/corridor's own measured nodal LMP (energy +
    congestion + loss, GHG excluded), ``wheel`` the additive OATT point-to-point
    charge of :data:`~market_sim.config.constants.CAISO_IMPORT_DELIVERY_BASIS`
    (the multiplicative line-loss markup is dropped — the measured MCL already
    carries the real loss; rules #11/#12), and ``border`` the CARB adder (clean
    hydro/solar pay none). Because wheel ≥ 0 and carbon ≥ 0, every import leg is
    priced at/above its corridor's export leg every hour, so each corridor nets
    to one direction per hour (no MIP). The Palo Verde corridor crashes negative
    in the desert-SW solar glut, so it reverses to export midday — the diurnal
    interchange sign tracks the measured tie per hub.

    The export leg's hub is the AVERAGE of the corridor's import-tranche hub
    series (both PNW tranches map to Malin, so the PNW export = Malin; the DSW
    tranches all map to Palo Verde, so the DSW export = Palo Verde) — i.e. each
    corridor exports into its own neighbor, not a blended hub.

    Returns ``True`` when the tie was repriced, ``False`` (byte-identical) when
    CAISO has no measured hub series for the year (e.g. 2023's OASIS gap), so the
    per-hub legs keep their static-ladder placeholder prices.
    """
    from market_sim.data.eia_loader import measured_import_hub_prices

    prices = measured_import_hub_prices(iso, year, int(mc.shape[1]))
    if not prices:
        return False
    border = wecc_border_carbon_adder(carbon_price)
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    import_names = {name for name, _, _ in IMPORT_TRANCHES.get(iso, [])}
    eps = CAISO_INTERTIE_TIEBREAK_EPS
    # Per-corridor export hub = mean of that corridor's import-tranche hub series.
    corridor_export_hub: dict[str, np.ndarray] = {}
    for tranche, series in prices.items():
        hub = CAISO_IMPORT_TRANCHE_HUB.get(tranche)
        zone = CAISO_PER_HUB_IMPORT_ZONES.get(hub) if hub else None
        if zone is not None:
            corridor_export_hub.setdefault(zone, []).append(series)
    corridor_export_hub = {
        z: np.mean(np.vstack(v), axis=0) for z, v in corridor_export_hub.items()
    }
    per_hub_zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        zone = next((z for z in per_hub_zones if uid.startswith(f"{z}_")), None)
        if zone is None:
            continue
        name = uid[len(zone) + 1 :]
        if name.startswith(f"{_CAISO_PER_HUB_EXPORT_PREFIX}_"):
            hub_series = corridor_export_hub.get(zone)
            if hub_series is not None:
                mc[row, :] = hub_series - eps  # export earns the hub, no CA carbon
                applied = True
        elif name in import_names:
            hub_series = prices.get(name)
            if hub_series is None:
                continue  # tranche with no measured hub stays on the ladder
            _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(name, (0.0, 0.0))
            ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
            mc[row, :] = (
                hub_series + wheel + border * (ef / CARB_UNSPECIFIED_IMPORT_EF) + eps
            )
            applied = True
    return applied


def inject_caiso_per_hub_reference_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
    carbon_price: float,
    gas_scenario: str = "mid",
) -> bool:
    """Price each CAISO per-hub corridor at its FORWARD reference price.

    The forecast-native analogue of :func:`inject_caiso_per_hub_intertie_prices`:
    structurally identical (same per-hub signed legs, per-tranche wheel + CARB
    carbon, arbitrage-free import ≥ export), but each corridor's hub price is the
    forward reference price
    :func:`market_sim.data.neighbor_price.caiso_hub_reference_price` —
    ``(henry_hub[year] + gas_basis) × marginal_heat_rate × load_shape`` — instead
    of the measured WECC OASIS hub LMP. The level rides the forward Henry Hub
    trajectory and the shape rides the neighbor's hourly tightness (the desert-SW
    on net load, so it dips midday with the solar glut), so the seam reprices
    forward as gas/solar move and stays live in a forecast year — where the
    measured series is absent. For every row::

        import leg → hub_ref + wheel + border_carbon × (EF / EF_unspecified) + ε
        export leg → hub_ref − ε

    Because ``wheel ≥ 0`` and ``border_carbon ≥ 0``, every import leg is priced
    at/above its corridor's export leg every hour, so each corridor nets to one
    direction per hour (no MIP), exactly as the measured injector.

    The honesty line (CLAUDE.md #10/#12): the price is formed from forward
    gas/HR/shape, never from the measured Malin/Palo-Verde LMP — that series is
    only the backcast realization the formula is validated against
    (``scripts/compare_caiso_intertie_formula_vs_measured.py``). Supersedes the
    measured per-hub injector when on; pairs with the forward ATC corridor cap
    (:func:`forward_corridor_atc_envelope`).

    Returns ``True`` when at least one corridor was repriced, ``False``
    (byte-identical) when no corridor resolved a forward shape (e.g. the CISO
    extract is absent), so the legs keep their static-ladder placeholders.
    """
    from market_sim.data.neighbor_price import caiso_hub_reference_price

    hours = int(mc.shape[1])
    # Forward reference price per corridor zone (None where the shape can't load).
    corridor_price: dict[str, np.ndarray] = {}
    for zone, spec in CAISO_PER_HUB_NEIGHBORS.items():
        price = caiso_hub_reference_price(spec, year, hours, gas_scenario)
        if price is not None:
            corridor_price[zone] = price
    if not corridor_price:
        return False
    border = wecc_border_carbon_adder(carbon_price)
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    import_names = {name for name, _, _ in IMPORT_TRANCHES.get(iso, [])}
    eps = CAISO_INTERTIE_TIEBREAK_EPS
    per_hub_zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        zone = next((z for z in per_hub_zones if uid.startswith(f"{z}_")), None)
        if zone is None:
            continue
        ref = corridor_price.get(zone)
        if ref is None:
            continue  # corridor with no forward shape stays on the ladder
        name = uid[len(zone) + 1 :]
        if name.startswith(f"{_CAISO_PER_HUB_EXPORT_PREFIX}_"):
            mc[row, :] = ref - eps  # export earns the corridor's price, no CA carbon
            applied = True
        elif name in import_names:
            _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(name, (0.0, 0.0))
            ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
            mc[row, :] = ref + wheel + border * (ef / CARB_UNSPECIFIED_IMPORT_EF) + eps
            applied = True
    return applied


def _caiso_corridor_import_ttc_mw(iso_config: ISOConfig) -> dict[str, float]:
    """Return each CAISO per-hub corridor's physical import-link TTC (MW).

    Reads the import link (``from_zone`` = corridor zone, ``to_zone`` = the
    NP15/SP15 trading zone via :data:`_CAISO_CORRIDOR_LINK_TO`) for each per-hub
    corridor in the (already-split) config. Used to scale the forward ATC ceiling
    off the corridor's real line rating (COI ≈ 4,800 MW, Path-46/WOR ≈ 10,623 MW)
    rather than a measured flow.
    """
    out: dict[str, float] = {}
    for zone, tos in _CAISO_CORRIDOR_LINK_TO.items():
        for link in iso_config.links:
            if link.from_zone == zone and link.to_zone in tos:
                out[zone] = float(link.ttc_mw)
                break
    return out


def forward_corridor_atc_envelope(
    iso_config: ISOConfig, iso: str, year: int, hours: int
) -> dict[str, np.ndarray] | None:
    """Return each CAISO corridor's FORWARD ATC import-deliverability ceiling.

    The forecast-native replacement for the measured p95 envelope
    (:func:`market_sim.data.eia_loader.measured_corridor_flow_envelope`). For
    each per-hub corridor, the ceiling is built from a *capability* limit, never
    the measured net-import flow::

        ATC(t) = TTC × atc_base_fraction × clip(1 − k × solar_frac(t), floor, 1)

    where ``TTC`` is the corridor's physical import-link rating
    (:func:`_caiso_corridor_import_ttc_mw`), ``atc_base_fraction`` the posted-ATC
    share of that rating available for CAISO economy imports
    (:data:`~market_sim.config.constants.CAISO_PER_HUB_NEIGHBORS`), and
    ``solar_frac(t)`` the region's hourly solar penetration
    (:func:`market_sim.data.eia_loader.caiso_solar_fraction`, CISO solar /
    demand) — a FORWARD driver that responds to a changed solar build. The solar
    derate reproduces the structural midday deliverability collapse (the WECC
    neighbors are themselves long on solar midday) without reading the measured
    corridor flow (CLAUDE.md #12). Applied one-sided on the import direction via
    :func:`build_caiso_corridor_flow_groups`; the export direction keeps the
    physical TTC.

    Returns ``{corridor_zone: (hours,) MW}`` for the corridors whose TTC and
    solar fraction resolve, or ``None`` when no corridor resolves (so the caller
    leaves the corridors uncapped, byte-identical).
    """
    from market_sim.data.eia_loader import caiso_solar_fraction

    if iso.upper() != "CAISO":
        return None
    solar_frac = caiso_solar_fraction(year, hours)
    if solar_frac is None:
        return None
    ttc = _caiso_corridor_import_ttc_mw(iso_config)
    out: dict[str, np.ndarray] = {}
    for zone, spec in CAISO_PER_HUB_NEIGHBORS.items():
        corridor_ttc = ttc.get(zone)
        if corridor_ttc is None:
            continue
        derate = np.clip(
            1.0 - CAISO_CORRIDOR_ATC_SOLAR_K * solar_frac, spec.atc_solar_floor, 1.0
        )
        out[zone] = corridor_ttc * spec.atc_base_fraction * derate
    return out or None


# Unit-id markers tagging a reference-price seam pseudo-generator so the
# post-assembly mc injector (:func:`inject_reference_price_mc`) can find each row
# and map it back to its neighbor and flow tranche. The id is
# ``<zone><mark><name>#<k>`` — import rows take the neighbor price + hurdle,
# export rows the neighbor price - hurdle, both evaluated at tranche ``k``'s flow.
_REF_IMPORT_MARK = "_refimp_"
_REF_EXPORT_MARK = "_refexp_"


def build_reference_price_node(iso: str) -> list[Generator]:
    """Return the reference-price seam as import/export pseudo-generators.

    The forecast-grade replacement for the fitted
    :func:`build_import_generators` / :func:`build_export_sinks`: per neighbor in
    :data:`~market_sim.config.constants.INTERFACE_NEIGHBORS`, the import and
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
            in :data:`~market_sim.config.constants.IMPORT_ZONE`.

    Returns:
        Import + export pseudo-generators; empty for an ISO with no neighbor
        registry (so an un-onboarded ISO stays byte-identical).
    """
    from market_sim.config.constants import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    zone = IMPORT_ZONE.get(iso)
    gens: list[Generator] = []
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
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

    Returns ``True`` when at least one seam row was priced, ``False`` when the
    fleet has no reference-price node (so a non-reference run is untouched).
    """
    from market_sim.config.constants import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import (
        interface_reference_prices,
        seam_tranche_prices,
    )

    hours = int(mc.shape[1])
    aggregate = interface_reference_prices(iso, year, hours, gas_scenario).aggregate()
    specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(iso, [])}
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
                seam_tranche_prices(spec, year, hours, gas_scenario=gas_scenario)
                if spec is not None
                else None
            )
        priced = tranches[name]
        hurdle = specs[name].hurdle if name in specs else 0.0
        if priced is not None:
            export_p, import_p, _ = priced
            band = export_p[k] if is_export else import_p[k]
            mc[row, :] = band - hurdle if is_export else band + hurdle
        elif aggregate is not None:
            # No load shape: flat aggregate, same for every band (no slope).
            mc[row, :] = aggregate - hurdle if is_export else aggregate + hurdle
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
    :attr:`~market_sim.config.constants.NeighborInterface.firm_export_floor_by_year`
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
    from market_sim.config.constants import INTERFACE_NEIGHBORS
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


def inject_caiso_import_hub_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
    carbon_price: float,
) -> bool:
    """Overwrite the CAISO import tranche rows of ``mc`` with measured hub prices.

    Mirrors :func:`inject_reference_price_mc` (post-assembly cost overwrite), but
    for the static priced-import node: each import tranche's marginal cost is set
    to the **measured hourly WECC neighbor-hub LMP** it proxies
    (:func:`market_sim.data.eia_loader.measured_import_hub_prices`) plus its CARB
    border-carbon adder, instead of the static bundle-fitted ladder value carried
    in the tranche ``vom``.

    Why: ``DIAGNOSIS-caiso-import-ladder-2026-06-19`` — the static ladder was
    re-fit against the model's own (too-high) solved price, so the import blocks
    that set the CAISO LMP in its cheaper hours sit ~$15-20 above the real
    delivered cost, and never go negative; the measured intertie price is the
    actual delivered energy cost (seasonal spring-runoff crash, negative
    desert-SW solar glut), which both lowers the body and reproduces the negative
    midday tail. The per-tranche border carbon is re-added here (clean
    hydro/solar tranches pay none) so the carbon treatment matches the static
    ladder; the measured ``price`` is the delivered nodal LMP (energy +
    congestion + loss = MCE+MCC+MCL), the GHG component excluded so the border
    carbon is not double-counted.

    Per-hub basis: the measured hub price is now the FULL nodal LMP *at the
    neighbor scheduling point* — the congestion (MCC) and loss (MCL) components
    make MALIN (PNW/Mid-C) and PALOVRDE (desert-SW) diverge, so the PNW and
    desert-SW tranches no longer clear at the same flat ~$38 system energy price
    (the gap behind DIAGNOSIS-caiso-body-overprice-2026-06-21). Delivered-cost
    basis: because the nodal MCL already carries the real loss, only the OATT
    point-to-point wheeling charge of
    :data:`~market_sim.config.constants.CAISO_IMPORT_DELIVERY_BASIS` is added
    (the modeled multiplicative line-loss markup is dropped to avoid
    double-counting — rules #11/#12). The gas blocks (``DSW_CCGT`` / ``DSW_CT``)
    carry the wheel here but are then overwritten off measured gas by
    :func:`inject_caiso_import_gas_coupling`, so the basis mainly shapes the
    non-gas blocks.

    Returns ``True`` when at least one import tranche row was repriced, ``False``
    when CAISO has no measured hub series (so the run keeps the static ladder and
    is byte-identical).
    """
    from market_sim.data.eia_loader import measured_import_hub_prices

    prices = measured_import_hub_prices(iso, year, int(mc.shape[1]))
    if not prices:
        return False
    zone = IMPORT_ZONE.get(iso)
    border = wecc_border_carbon_adder(carbon_price)
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if zone is None or not uid.startswith(f"{zone}_"):
            continue
        tranche = uid[len(zone) + 1 :]
        hub_price = prices.get(tranche)
        if hub_price is None:
            continue  # tranche with no measured hub series stays on the ladder
        # Delivered-cost basis over the measured nodal hub price. The hub series
        # is now the FULL nodal LMP (energy + congestion + loss = MCE+MCC+MCL;
        # see fetch_caiso_intertie_lmp.py), so the measured MCL already carries
        # the real marginal loss at the scheduling point. We therefore DROP the
        # modeled multiplicative line-loss markup (it would double-count the loss
        # the nodal price now measures) and add only the OATT point-to-point
        # wheeling charge — a separate commercial charge the intervening BAA(s)
        # levy that is NOT part of CAISO's nodal LMP. rules #11/#12: prefer the
        # measured loss, ground the change (a representation reconciliation), not
        # a residual-fitted offset.
        _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(tranche, (0.0, 0.0))
        delivered = hub_price + wheel
        ef = IMPORT_TRANCHE_EF.get(iso, {}).get(tranche, CARB_UNSPECIFIED_IMPORT_EF)
        mc[row, :] = delivered + border * (ef / CARB_UNSPECIFIED_IMPORT_EF)
        applied = True
    return applied


# CAISO export sink(s) repriced to the measured neighbor hub — the blocks that
# carry the neighbors' willingness-to-pay (sold to WECC), NOT the deep in-state
# curtailment floor (export_curtail stays at its $0 value as the beyond-tie
# renewable curtailment block).
_CAISO_HUB_EXPORT_TRANCHES = ("export_solar",)


def inject_caiso_export_hub_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
) -> bool:
    """Reprice CAISO's neighbor-export sink to the measured WECC hub LMP.

    Symmetric to :func:`inject_caiso_import_hub_prices`. CAISO sells its surplus
    to the WECC neighbor at *that neighbor's* hub price, so the export sink's
    willingness-to-pay (the value of exported energy, carried in the sink ``mc``)
    is the measured intertie hub LMP — the energy (MCE) component, no CA carbon
    (exports carry no in-state compliance cost). Replaces the static
    ``EXPORT_TRANCHES`` fit ($8 ``export_solar`` / $0 ``export_curtail``), which
    only let CAISO export when its internal price fell near $0; with the real
    ~$38 hub the model exports whenever its price drops below the neighbor's —
    recovering the midday solar-glut export the static blocks could not (the
    measured 2024 intertie swings to +3.5 GW net export, while the model was
    stuck importing 100% of hours). Only the neighbor-export block(s) in
    :data:`_CAISO_HUB_EXPORT_TRANCHES` are repriced; the deep ``export_curtail``
    block keeps its $0 in-state curtailment floor.

    Returns ``True`` when at least one export sink was repriced, ``False`` when
    CAISO has no measured hub series (run keeps the static blocks, byte-identical).
    """
    from market_sim.data.eia_loader import measured_import_hub_prices

    prices = measured_import_hub_prices(iso, year, int(mc.shape[1]))
    if not prices:
        return False
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return False
    # The export sink sells into a single blended WECC neighbor, so average the
    # per-hub nodal series (MALIN/PALOVRDE) into one willingness-to-pay. (The
    # per-tranche import path keeps them separate; the single export leg does not
    # distinguish which neighbor buys.)
    hub_price = np.mean(np.vstack(list(prices.values())), axis=0)
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if not uid.startswith(f"{zone}_"):
            continue
        name = uid[len(zone) + 1 :]
        if name in _CAISO_HUB_EXPORT_TRANCHES:
            mc[row, :] = hub_price
            applied = True
    return applied


def inject_caiso_bidir_intertie_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
    carbon_price: float,
) -> bool:
    """Price the single signed WECC intertie at the measured hub (arbitrage-free).

    The unified replacement for :func:`inject_caiso_import_hub_prices` +
    :func:`inject_caiso_export_hub_prices`, paired with
    :func:`build_caiso_bidir_intertie`. Both legs of the tie are repriced from
    the SAME measured hub energy series (the MCE component of the CAISO intertie
    LMP, :func:`market_sim.data.eia_loader.measured_import_hub_prices`):

    * each import tranche row → ``hub + border_carbon × (EF / EF_unspecified)``
      (the per-tranche CARB adder of
      :data:`~market_sim.config.constants.IMPORT_TRANCHE_EF`), and
    * the single export leg row → ``hub`` (exports owe no CA compliance cost).

    PROBE NOTE (caiso 24 bidir+wheel-only): each import leg is priced at
    ``hub + wheel + border_carbon × (EF / EF_unspecified)`` — the ADDITIVE
    per-tranche OATT point-to-point wheeling charge of
    :data:`~market_sim.config.constants.CAISO_IMPORT_DELIVERY_BASIS`, but NOT its
    multiplicative line-loss markup (``loss·max(hub,0)``). On the capped 8.3 GW
    single-flow bidir node the multiplicative loss double-counts the congestion
    the cap already prices and over-suppresses imports (caiso-23 basis-only: net
    −19.09, neg 194, corr −0.04); the additive wheel still separates the flat
    ~$38 MCE into a rising delivered-import merit order without the price-scaling
    explosion that crushes midday imports. (The full-basis unify variant — loss +
    wheel — lives in commit af1e369; the floor-only probe drops both.)

    Because the carbon adder is ≥ 0, *every* import leg is priced at or above the
    export leg at every hour, so importing and exporting in the same hour can
    never both reduce the objective: the LP carries one net direction per hour
    over the shared cap (no MIP). The measured hub crashes in the spring PNW
    runoff and goes negative in the desert-SW solar glut, so the tie reverses to
    export midday — the diurnal interchange now tracks the measured sign instead
    of anti-correlating with it.

    Returns ``True`` when the tie was repriced, ``False`` (byte-identical) when
    CAISO has no measured hub series for the year (e.g. 2023's OASIS-retention
    gap), so the bidir tie keeps its static-ladder placeholder prices.
    """
    from market_sim.data.eia_loader import measured_import_hub_prices

    prices = measured_import_hub_prices(iso, year, int(mc.shape[1]))
    if not prices:
        return False
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return False
    # The bidir tie is a SINGLE signed node, so collapse the per-hub nodal series
    # (MALIN/PALOVRDE) into one price both legs share. (The per-tranche import
    # path keeps the hubs separate; the single tie cannot.)
    hub = np.mean(np.vstack(list(prices.values())), axis=0)
    border = wecc_border_carbon_adder(carbon_price)
    ef_map = IMPORT_TRANCHE_EF.get(iso, {})
    import_names = {name for name, _, _ in IMPORT_TRANCHES.get(iso, [])}
    eps = CAISO_INTERTIE_TIEBREAK_EPS
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if not uid.startswith(f"{zone}_"):
            continue
        name = uid[len(zone) + 1 :]
        if name == _CAISO_BIDIR_EXPORT_NAME:
            # Export earns the hub (no CA carbon), less the ε tiebreaker so a
            # gross round-trip is strictly cost-positive.
            mc[row, :] = hub - eps
            applied = True
        elif name in import_names:
            loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(name, (0.0, 0.0))
            # Wheel-only (additive) delivery: the per-tranche OATT point-to-point
            # wheeling charge ($/MWh) restores the rising delivered-import merit
            # order the flat MCE collapses, but WITHOUT the multiplicative
            # line-loss markup (loss·max(hub,0)) — on the capped 8.3 GW
            # single-flow bidir node that loss term double-counts the congestion
            # the cap already prices and over-suppresses imports (caiso-23
            # basis-only: net −19.09, corr −0.04). rule #12: the wheel is a real,
            # forward-reproducible physical charge; the dropped loss is a
            # representation correction for the cap, not a residual tune.
            # Arbitrage-free: wheel ≥ 0 and carbon ≥ 0 so every import leg ≥
            # export (hub − ε) every hour.
            ef = ef_map.get(name, CARB_UNSPECIFIED_IMPORT_EF)
            mc[row, :] = hub + wheel + border * (ef / CARB_UNSPECIFIED_IMPORT_EF) + eps
            applied = True
    return applied


# Representative desert-SW heat rates (MMBtu/MWh) for the price COUPLING — the
# Palo Verde / Path-46 import blocks whose *price-setting* marginal unit is
# SW gas, so their level tracks the measured commodity gas. DSW_CCGT / DSW_CT
# match their carbon EF / 0.0531 (the EIA gas CO2 factor: EF = heat rate x
# 0.0531). DSW_solar_PV is the desert-SW daytime marginal block: it carries a
# zero CARBON EF (specified solar/nuclear, no border carbon) but its $48
# price-setting *level* is gas-set (DIAGNOSIS-caiso-import-ladder: it sets the
# CAISO price in ~21% of hours, mapped to the gas-influenced Palo Verde hub),
# so the coupling uses a representative SW CCGT heat rate for its price only.
# PNW (hydro) and WECC_scarcity (unspecified peak energy) are not gas-coupled.
_CAISO_IMPORT_COUPLE_HR: dict[str, float] = {
    "DSW_solar_PV": 7.0,  # SW daytime marginal (Palo Verde CCGT-equivalent)
    "DSW_CCGT": 0.37 / 0.0531,  # ~6.97, matches IMPORT_TRANCHE_EF
    "DSW_CT": 0.55 / 0.0531,  # ~10.36, matches IMPORT_TRANCHE_EF
}


def inject_caiso_import_gas_coupling(
    fleet_arrays, mc: np.ndarray, config, year: int
) -> bool:
    """Shift the gas-set CAISO import tranches by the measured commodity-gas delta.

    Forecast-consistent, no-OASIS replacement for the desert-SW leg of lever A
    (``PLAN-caiso-gas-coupled-imports-2026-06-20``). The static
    ``IMPORT_TRANCHES["CAISO"]`` desert-SW blocks (DSW_solar_PV, DSW_CCGT,
    DSW_CT) are the Palo Verde / Path-46 import whose price-setting marginal unit
    is SW gas, but their *level* was fitted against the F923 **delivered** gas
    world. When ``--gas-hub-basis-overlay`` reprices in-state gas to the measured
    **commodity spot** (Henry Hub month + measured CA citygate basis), those
    import blocks must move by the same per-MMBtu shift, or cheaper in-state gas
    undercuts them and steals their share (gas TWh over-runs ~+12%,
    RESULTS-caiso-leverB-citygate — the share lost is the DSW_solar_PV block).
    This adds, per coupled tranche::

        mc[row] += (commodity_spot_gas[m] - F923_delivered_gas[m]) x HR_tranche

    with ``HR_tranche`` the representative desert-SW heat rate
    (:data:`_CAISO_IMPORT_COUPLE_HR`) and the two measured monthly gas series
    from :func:`market_sim.data.fuel.iso_hub_monthly_gas_prices` /
    :func:`~market_sim.data.fuel.iso_monthly_gas_prices`. The shift is ~0 at the
    baseline (un-overlaid) gas level, so the validated import volume is preserved
    -- only the gas-sensitivity is coupled in, with no new fitted constant. The
    border CARBON stays on its own per-tranche EF (DSW_solar_PV pays none), so
    only the *energy* level is gas-coupled. Designed to pair with
    ``--gas-hub-basis-overlay`` (both legs then price off the same commodity gas,
    keeping the in-state-gas / SW-import merit order consistent).

    Returns ``True`` when at least one tranche row was shifted, ``False``
    (byte-identical) when the measured gas series are unavailable (forecast
    years) or the import node is absent.
    """
    from market_sim.data.fuel import (
        _expand_monthly_to_hourly,
        iso_hub_monthly_gas_prices,
        iso_monthly_gas_prices,
    )

    iso = config.iso
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return False
    spot = iso_hub_monthly_gas_prices(config, year)
    f923 = iso_monthly_gas_prices(config, year)
    if spot is None or f923 is None:
        return False
    delta_m = spot - f923  # $/MMBtu; NaN in months either series does not cover
    delta_m = np.where(np.isfinite(delta_m), delta_m, 0.0)
    if not np.any(delta_m):
        return False
    delta_h = _expand_monthly_to_hourly(delta_m, int(mc.shape[1]))
    couple_hr = _CAISO_IMPORT_COUPLE_HR if iso.upper() == "CAISO" else {}
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        # Find the tranche under either the pooled WECC_import node or the
        # per-hub WECC_PNW / WECC_DSW corridors (CAISO); other ISOs keep the
        # single-zone match. Byte-identical to the prior code off the per-hub flag.
        if iso.upper() == "CAISO":
            tranche = _caiso_import_tranche_of(uid, zone)
        else:
            tranche = uid[len(zone) + 1 :] if uid.startswith(f"{zone}_") else None
        if tranche is None:
            continue
        heat_rate = couple_hr.get(tranche)
        if not heat_rate:
            continue
        mc[row, :] = mc[row, :] + delta_h * heat_rate
        applied = True
    return applied


# Net-load percentile band over which the desert-SW solar import offer collapses
# from its (gas-coupled) level toward the negative keep-running floor. The Palo
# Verde / Path-46 desert-SW hub price collapses to sub-$0 midday in the spring
# belly (the regional AZ/NV solar glut), so the marginal desert-SW SOLAR import
# bids negative and can set a sub-$0 CAISO LMP — the model otherwise prices that
# marginal block flat ($48, gas-coupled), so its midday floor never goes
# negative (model 14 hrs <=$0 vs actual ~868, 2024). The collapse is gated on
# CAISO net load (load less utility solar/wind) so it fires spring-midday (deep
# belly) and not summer-midday (high net load): full collapse at the annual
# net-load floor, none above the low decile. Depth is the same REC/PTC
# keep-running constant the in-state negative_renewable_offers floor uses
# (renewable_keep_running_value) — no new fitted price constant. Only the SOLAR
# import block is shaped; the desert-SW gas blocks (DSW_CCGT/DSW_CT) keep their
# positive gas SRMC.

# Net-load band over which the offer collapses. Full collapse (s=1) at/below the
# LO percentile, none above HI. The LO percentile is anchored to the observed
# CAISO negative-price prevalence (~9% of hours, 2024 DA/RT) so the deepest
# net-load belly hours — the regional glut — price negative; HI sets the ramp
# above it. Validated against actual hourly LMP (precision ~100% — every modeled
# negative hour is a real negative hour). Overridable via env for sweeps.
_CAISO_SOLAR_SHAPE_NL_HI_PCT = float(_os.environ.get("CAISO_SS_NL_HI", "30.0"))
_CAISO_SOLAR_SHAPE_NL_LO_PCT = float(_os.environ.get("CAISO_SS_NL_LO", "10.0"))
# Marginal CAISO import blocks set by *long WECC neighbors* in the midday belly:
# the desert-SW solar/Palo Verde hub and the Mid-C (Pacific NW) hub, both of
# which print sub-$0 in the regional spring solar/hydro glut. The firm baseload
# hydro block (PNW_hydro_base) is NOT collapsed — it is the cheap must-take floor,
# not a glut-priced marginal block. Collapsing the two marginal blocks fills the
# (aggregate path-constrained) import lane and pushes the $28 firm-hydro block
# out of the margin, so the price-setting import bids sub-$0.
_CAISO_SOLAR_SHAPE_TRANCHES = ("DSW_solar_PV", "PNW_midC")
# Export sinks (EXPORT_TRANCHES["CAISO"]): the neighbors' willingness-to-pay for
# CAISO surplus. Off the belly that is positive (export_solar $8 / export_curtail
# $0), but in the midday belly the neighbors are long too, so CAISO must PAY them
# to take the surplus — the export price collapses sub-$0 on the same signal. This
# floors a *long* CAISO at the negative export price (instead of +$8), so the
# belly LMP follows the in-state negative_renewable_offers / negative export down
# rather than pinning at the export sink. Only bites when CAISO is long (the sink
# is idle otherwise), so it is self-limiting on the price body.
_CAISO_SOLAR_SHAPE_EXPORT_TRANCHES = ("export_solar", "export_curtail")


def inject_caiso_import_solar_shape(
    fleet_arrays, mc: np.ndarray, config, net_load: np.ndarray
) -> bool:
    """Collapse the marginal long-neighbor import offers toward the negative floor in the belly.

    Forecast-/no-OASIS-consistent restoration of the CAISO negative midday tail.
    The marginal CAISO imports midday are the desert-SW solar (``DSW_solar_PV``,
    Palo Verde hub) and Mid-C (``PNW_midC``, Pacific-NW hub) blocks
    (:data:`_CAISO_SOLAR_SHAPE_TRANCHES`), but their price-setting *level* is
    priced flat (gas-coupled ~$48 / $36), so they can never set the sub-$0 LMP
    those hubs print in the regional spring solar/hydro glut. This shifts their
    per-hour offer from that level toward ``-renewable_keep_running_value`` as
    CAISO net load drops into its annual belly::

        s(t) = clip((nl_hi - net_load[t]) / (nl_hi - nl_lo), 0, 1)
        mc[DSW_solar_PV, t] = base(t) * (1 - s(t)) + floor * s(t)

    with ``nl_hi`` / ``nl_lo`` the :data:`_CAISO_SOLAR_SHAPE_NL_HI_PCT` /
    ``_LO_PCT`` percentiles of the year's net load and ``floor =
    -renewable_keep_running_value``. Net-load-gated so the negative offer fires
    in the deep (spring-midday) belly and stays at the gas-coupled level off the
    belly (nights, summer peak). Applies on top of the gas coupling (so ``base``
    already carries the commodity-gas shift). Returns ``True`` when the block was
    shaped, ``False`` (byte-identical) for non-CAISO ISOs, a missing import node,
    a length mismatch, or a degenerate (flat) net-load band.
    """
    iso = config.iso
    if iso.upper() != "CAISO":
        return False
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return False
    nl = np.asarray(net_load, dtype=float).reshape(-1)
    if nl.size != mc.shape[1]:
        return False
    nl_hi = float(np.percentile(nl, _CAISO_SOLAR_SHAPE_NL_HI_PCT))
    nl_lo = float(np.percentile(nl, _CAISO_SOLAR_SHAPE_NL_LO_PCT))
    if not (nl_hi > nl_lo):
        return False
    s = np.clip((nl_hi - nl) / (nl_hi - nl_lo), 0.0, 1.0)
    floor = -float(getattr(config, "renewable_keep_running_value", 20.0))
    # Import tranches matched by name under either the pooled WECC_import node or
    # the per-hub WECC_PNW/WECC_DSW corridors; export sinks (single-node only)
    # matched by full uid (the per-hub node replaces them with hub-priced export
    # legs that already carry the negative belly signal).
    import_targets = set(_CAISO_SOLAR_SHAPE_TRANCHES)
    export_targets = {f"{zone}_{t}" for t in _CAISO_SOLAR_SHAPE_EXPORT_TRANCHES}
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        tranche = _caiso_import_tranche_of(uid, zone)
        if (tranche in import_targets) or (uid in export_targets):
            mc[row, :] = mc[row, :] * (1.0 - s) + floor * s
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
    fleet_arrays,
    iso: str,
    year: int,
    percentile: float = 90.0,
    export_only: bool = False,
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
    """
    from market_sim.data.eia_loader import measured_interchange_envelope
    from market_sim.data.fleet import FUEL_TYPE_MAP

    # The envelope percentile sets how tightly the measured diurnal interchange
    # caps the priced node. Under the bidirectional intertie (gross == net), the
    # net-import envelope IS the deliverable import, so the import cap can ride a
    # higher percentile (fatter overnight tail) without re-admitting the midday
    # imports the (near-zero) midday envelope already excludes. Overridable per
    # direction for the bidir sweep; defaults to the passed ``percentile`` so the
    # legacy export-only path is byte-identical.
    import_pct = float(_os.environ.get("INTERCHANGE_SHAPE_IMPORT_PCT", percentile))
    export_pct = float(_os.environ.get("INTERCHANGE_SHAPE_EXPORT_PCT", percentile))
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


def inject_miso_seam_flow_limit(
    fleet_arrays,
    iso: str,
    year: int,
    percentile: float | None = None,
) -> bool:
    """Cap each MISO reference-price seam's import bands at the measured envelope.

    The reference-price seam (:func:`build_reference_price_node`) makes every
    import band of every neighbor available in every hour, so the LP imports up
    to the full interface limit on each seam whenever its priced spread is
    positive — and because MISO's LMP sits above all three neighbors' nearly
    every hour, it over-imports on ALL three seams (the −72/−50/−7 TWh net
    interchange vs the measured −38/−23/−19). In reality only the eastern PJM
    seam is a large net-import path; MISO nets ≈0 over SPP and net-*exports* over
    the southern (TVA-dominated) seam.

    This scales, per hour, each neighbor's import-band ``availability`` by its
    measured per-seam net-import deliverability envelope
    (:func:`market_sim.data.eia_loader.measured_seam_import_envelope`) relative
    to that seam's static interface limit, so the seam can import at most its
    historical *deliverable* transfer in that (month × hour-of-day) period. The
    envelope is a one-sided (import-direction) ceiling: a seam that reliably
    net-exports caps to ~zero import, while its export bands keep their priced
    economics. A high percentile keeps headroom above the median, so the modeled
    seam price — not the cap — sets the typical hour. Mirrors
    :func:`inject_interchange_shape` (post-assembly availability scaling) but
    per-seam and on the measured *directed* BA-to-BA flow rather than the
    aggregate net interchange. Modifies ``fleet_arrays`` in place.

    Returns ``True`` when at least one seam was capped, ``False`` when no
    reference-price import bands are present or no measured envelope is available
    (forecast year / unmapped ISO), leaving the seam unchanged (byte-identical).
    """
    from market_sim.data.eia_loader import measured_seam_import_envelope

    hours = int(fleet_arrays.availability.shape[1])
    env = measured_seam_import_envelope(iso, year, hours, percentile)
    if not env:
        return False
    applied = False
    for name, cap in env.items():
        # Import bands of this neighbor: uid is "<zone>_refimp_<name>#k".
        rows = [
            r
            for r, uid in enumerate(fleet_arrays.unit_ids)
            if _REF_IMPORT_MARK in uid
            and uid.rsplit(_REF_IMPORT_MARK, 1)[1].partition("#")[0] == name
        ]
        if not rows:
            continue
        total = float(fleet_arrays.pmax[rows].sum())  # = interface_limit_mw
        if total <= 0.0:
            continue
        # Uniform per-band derate so the seam's summed import availability ≤ cap
        # each hour; the bands keep their rising (flow-responsive) prices, so the
        # LP still fills the cheapest first below the ceiling.
        frac = np.clip(np.asarray(cap, dtype=float) / total, 0.0, 1.0)
        for r in rows:
            fleet_arrays.availability[r, :] *= frac
        applied = True
    return applied


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
        fleet_arrays.pmax[gas_rows, np.newaxis] * fleet_arrays.availability[gas_rows, :]
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
    order = gas_rows[np.argsort(fleet_arrays.heat_rate[gas_rows], kind="stable")]
    remaining = target.copy()
    for r in order:
        cap = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap)
        np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
        remaining = remaining - take
    return True


# Afternoon-evening window (local hour-of-day, ``[start, end]`` inclusive) over
# which the CAISO CT_PEAKER local-RA reliability floor binds — the net-load ramp
# / duck-curve neck. On hot days (TMAX >= 30 deg C) this window carries ~80% of
# measured CT_PEAKER energy; outside it the peakers dispatch purely on price. A
# documented operating window, mirroring CAISO_GAS_FLOOR_HOURS.
CAISO_CT_FLOOR_HOURS: tuple[int, int] = (15, 22)


def inject_caiso_ct_reliability_floor(
    fleet_arrays,
    iso: str,
    year: int,
    slope_per_c: float,
    t0_c: float,
    cap: float,
    base: float = 0.0,
    hod_window: tuple[int, int] = CAISO_CT_FLOOR_HOURS,
) -> bool:
    """Floor CAISO CT_PEAKER at a temperature-driven local-RA commitment.

    Models CAISO's **local Resource-Adequacy** commitment of simple-cycle gas
    peakers (``CT_PEAKER``): on hot afternoons the load-pocket cooling load climbs
    and solar collapses at sunset, so fast-start CTs in the LA Basin /
    Big-Creek-Ventura / Bay-Area local capacity areas are held online for local
    reliability regardless of system-energy economics. An energy-only LP never
    dispatches these top-of-merit peakers, so the backcast under-runs CT_PEAKER
    and the freed energy spills onto the cheaper combined-cycle fleet
    (CC_REGULAR over-generates).

    After :func:`~market_sim.data.fleet.generators_to_fleet_arrays` builds the
    fleet, this imposes a hard minimum-generation floor on the CT_PEAKER units
    over the afternoon-evening ``hod_window``, sized to ``frac`` x available
    capacity where ``frac = clip(base + slope_per_c*(TMAX - t0_c), base, cap)`` is
    keyed to the load-weighted CAISO daily max temperature (:func:`~market_sim
    .data.eia_loader.caiso_load_weighted_tmax`). ``base`` is the YEAR-ROUND
    local-RA baseline (the measured cool-day evening CF the hot-limb fit clips to
    zero — CAISO's Local Capacity Requirement holds a must-offer minimum on mild
    days, not only hot ones); ``base = 0`` is byte-identical to the hot-limb-only
    floor. The hourly fleet target is
    distributed over the CT_PEAKER units **cheapest-first** (by heat rate), each
    capped at its available capacity — the same hour-varying
    ``FleetArrays.min_gen`` lower bound the CHP steam floor and the gas
    commitment floor use, composed with any floor already present via
    ``maximum``. The LP dispatches economically *above* the floor, so it only
    binds on the hot-day evening hours an energy-only merit order would leave the
    peakers off — exactly the missing local-RA energy.

    The curve coefficients are the measured CAMPD CT_PEAKER evening capacity
    factor regressed on TMAX (2023-2025; ``scripts/derive_caiso_ct_reliability_
    floor.py``, ``docs/caiso-ct-reliability-floor-2026-06.md``) — a physical
    temperature->commitment rule, not a fit to a TWh residual. It is forward-
    derivable (a forecast year pins a weather year, hence a TMAX series, exactly
    as it pins load/wind/solar) and condition-responsive (hotter years -> more
    CT), which is what makes it admissible in both backcast and forecast
    (CLAUDE.md #10/#11).

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was applied,
    ``False`` (byte-identical) when ``iso`` is not CAISO, ``slope_per_c``/``cap``
    are non-positive, the fleet has no CT_PEAKER units, or no archived TMAX
    series is available (forecast year / unmapped ISO).
    """
    if iso != "CAISO" or slope_per_c <= 0.0 or cap <= 0.0:
        return False
    from market_sim.data.eia_loader import caiso_load_weighted_tmax

    if fleet_arrays.plant_group is None:
        return False
    is_ct = np.asarray(fleet_arrays.plant_group) == "CT_PEAKER"
    ct_rows = np.flatnonzero(is_ct & (fleet_arrays.pmax > 0.0))
    if ct_rows.size == 0:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    tmax = caiso_load_weighted_tmax(year, hours)
    if tmax is None:
        return False

    # Temperature->commitment fraction: the hot-limb line clipped between the
    # year-round local-RA BASELINE (``base``, the measured cool-day evening
    # minimum the hot-limb fit clips to zero) and the hottest-day ceiling
    # (``cap``), restricted to the afternoon-evening window (zero elsewhere). With
    # base = 0 this is byte-identical to the hot-limb-only floor. Row 0 of the
    # dispatch is the first local hour of the year, so a plain local clock
    # reproduces the hour-of-day index.
    frac = np.clip(
        base + slope_per_c * (np.asarray(tmax, dtype=float) - t0_c), base, cap
    )
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    hod = clock.hour.to_numpy()
    start, end = hod_window
    window = (hod >= start) & (hod <= end)
    frac = np.where(window, frac, 0.0)
    if not np.any(frac > 0.0):
        return False

    # Per-hour CT fleet target = frac x available CT_PEAKER capacity that hour.
    avail_cap = (
        fleet_arrays.pmax[ct_rows, np.newaxis] * fleet_arrays.availability[ct_rows, :]
    )
    target = frac * avail_cap.sum(axis=0)

    if fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis],
            (fleet_arrays.pmin.size, hours),
        ).copy()

    # Distribute the hourly fleet target cheapest-first (by heat rate) over the
    # CT_PEAKER units, each capped at its available capacity; ``maximum`` composes
    # with any existing floor rather than clobbering it.
    order = ct_rows[np.argsort(fleet_arrays.heat_rate[ct_rows], kind="stable")]
    remaining = target.copy()
    for r in order:
        cap_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap_r)
        np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
        remaining = remaining - take
    return True


# NYISO downstate CT_PEAKER reliability-floor window (HB14-21 local) and the
# load-pocket zones it applies to. The measured downstate (NYC + Long Island +
# Lower Hudson) peaker fleet's hot-day capacity factor peaks HB14-18 (~0.69) and
# tails through HB21 (derive_nyiso_ct_reliability_floor.py); the floor is keyed to
# the in-city / cable-islanded load pockets, NOT the upstate peakers (which carry
# no AC-cable reliability driver).
NYISO_CT_FLOOR_HOURS: tuple[int, int] = (14, 21)
NYISO_CT_FLOOR_ZONES: tuple[str, ...] = ("NYC", "Long_Island", "Lower_Hudson")


def inject_nyiso_ct_reliability_floor(
    fleet_arrays,
    iso: str,
    year: int,
    zone_names: list[str],
    slope_per_c: float,
    t0_c: float,
    cap: float,
    base: float = 0.0,
    hod_window: tuple[int, int] = NYISO_CT_FLOOR_HOURS,
) -> bool:
    """Floor NYISO **downstate** CT_PEAKER at a temperature-driven local-RA commitment.

    Models NYISO's in-city / Long-Island local-reliability commitment of
    simple-cycle gas peakers: on hot afternoons the cable-constrained downstate
    cooling load (NYC zone J, Long Island zone K, Lower Hudson) climbs and the
    UPNY-SENY / Long-Island-cable import limits bind, so fast-start GTs in the
    load pockets are held online for local capacity-area reliability regardless of
    system-energy economics. An energy-only LP never dispatches these
    top-of-merit peakers (it imports cheap upstate/NYC CC instead), so the
    backcast under-runs CT_PEAKER and the freed energy spills onto the cheaper
    combined-cycle fleet (CC_REGULAR over-generates) — the documented downstate
    CT_PEAKER miss.

    Identical mechanism to :func:`inject_caiso_ct_reliability_floor`, with two
    NYISO specializations: (1) the floor is restricted to the **downstate load
    pockets** (``NYISO_CT_FLOOR_ZONES``) — upstate peakers carry no AC-cable
    reliability driver and are left to economics; (2) the daily max temperature is
    the NYC-metro series (:func:`~market_sim.data.eia_loader.nyiso_downstate_tmax`,
    NOAA GHCN-Daily TMAX for Central Park / LaGuardia / JFK). The hourly
    downstate-fleet target is ``frac = clip(base + slope_per_c*(TMAX - t0_c),
    base, cap)`` over the afternoon-evening ``hod_window``, distributed
    cheapest-first over the in-pocket CT_PEAKER units (each capped at available
    capacity), composed with any existing ``FleetArrays.min_gen`` floor via
    ``maximum``. The LP dispatches economically above the floor, so it binds only
    on the hot-day evening hours an energy-only merit order would leave the
    downstate peakers off.

    The curve coefficients are the measured downstate CAMPD CT_PEAKER evening
    (HB14-21) capacity factor regressed on NYC TMAX, 2023-2025
    (``scripts/derive_nyiso_ct_reliability_floor.py``) — a physical
    temperature->commitment rule, not a fit to a TWh residual. Forward-derivable
    (a forecast year pins a weather year, hence a TMAX series) and
    condition-responsive (hotter years -> more downstate CT), admissible in both
    backcast and forecast (CLAUDE.md #10/#11). It does NOT address the *winter*
    downstate run (a gas-electric constraint, not a cooling driver) — that belongs
    to the dual-fuel / Transco-Z6 gas-basis frontier.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was applied,
    ``False`` (byte-identical) when ``iso`` is not NYISO, ``slope_per_c``/``cap``
    are non-positive, the fleet has no downstate CT_PEAKER units, or no archived
    TMAX series is available (forecast year / unmapped ISO).
    """
    if iso != "NYISO" or slope_per_c <= 0.0 or cap <= 0.0:
        return False
    from market_sim.data.eia_loader import nyiso_downstate_tmax

    if fleet_arrays.plant_group is None:
        return False
    # Restrict to the downstate load pockets (NYC / Long Island / Lower Hudson);
    # upstate peakers carry no AC-cable reliability driver.
    ds_zone_idx = {i for i, z in enumerate(zone_names) if z in NYISO_CT_FLOOR_ZONES}
    is_ct = np.asarray(fleet_arrays.plant_group) == "CT_PEAKER"
    is_downstate = np.isin(fleet_arrays.zone_idx, list(ds_zone_idx))
    ct_rows = np.flatnonzero(is_ct & is_downstate & (fleet_arrays.pmax > 0.0))
    if ct_rows.size == 0:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    tmax = nyiso_downstate_tmax(year, hours)
    if tmax is None:
        return False

    frac = np.clip(
        base + slope_per_c * (np.asarray(tmax, dtype=float) - t0_c), base, cap
    )
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    hod = clock.hour.to_numpy()
    start, end = hod_window
    window = (hod >= start) & (hod <= end)
    frac = np.where(window, frac, 0.0)
    if not np.any(frac > 0.0):
        return False

    avail_cap = (
        fleet_arrays.pmax[ct_rows, np.newaxis] * fleet_arrays.availability[ct_rows, :]
    )
    target = frac * avail_cap.sum(axis=0)

    if fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis],
            (fleet_arrays.pmin.size, hours),
        ).copy()

    order = ct_rows[np.argsort(fleet_arrays.heat_rate[ct_rows], kind="stable")]
    remaining = target.copy()
    for r in order:
        cap_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap_r)
        np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
        remaining = remaining - take
    return True


# Dispatchable thermal fuels eligible to carry a local self-supply floor — the
# in-zone gas / oil / coal fleet, excluding non-dispatchable / energy-limited /
# must-run resources (wind, solar, hydro, nuclear, geothermal, biomass) and the
# import pseudo-generators, which cannot stand in for local reliability units.
def _dispatchable_thermal_codes() -> list[int]:
    from market_sim.data.fleet import FUEL_TYPE_MAP

    names = (
        "gas_cc",
        "gas_ct",
        "gas_st",
        "oil",
        "coal",
        "gas_cc_ccs",
        "hydrogen_ct",
        "hydrogen_ccgt",
    )
    return [FUEL_TYPE_MAP[n] for n in names if n in FUEL_TYPE_MAP]


def inject_nyiso_local_selfsupply(
    fleet_arrays,
    iso: str,
    demand: np.ndarray,
    zone_names: list[str],
) -> bool:
    """Floor a NYISO downstate load pocket's in-zone thermal self-supply.

    Models NYISO's locational-minimum-installed-capacity (LMIC) /
    local-reliability rules for the cable-islanded Long Island pocket (zone K):
    a fraction of the zone's own load must be met by IN-ZONE dispatchable
    thermal generation rather than imported across the limited NYC->LI cables.
    The economic LP, lacking the rule, floods cheap NYC gas into LI and
    under-runs the LI fleet (model 3.7 vs EIA-923 8.52 TWh, 2023;
    docs/nyiso-dispatch-validation-2026-06.md).

    For each pocket zone in
    :data:`~market_sim.config.constants.NYISO_LOCAL_SELFSUPPLY_FRAC`, the hourly
    in-zone target is ``frac × demand[zone, t]``, distributed over the zone's
    dispatchable thermal generators in **marginal-cost merit order** (gas-capable
    tranches first by heat rate, the dear oil-fired peakers last) and each
    capped at its available capacity — the same hour-varying
    ``FleetArrays.min_gen`` lower bound the CHP / CT reliability floors use, and
    composed with any floor already present via ``maximum``. The target is
    clipped to the zone fleet's available capacity each hour so a feasible LP
    solution always exists (the floor can never manufacture unmet load).

    The floor is **forward-reproducible** (it scales with load and responds to
    changed conditions) and grounded in NYISO market design — it is NOT a pin to
    measured LI generation (CLAUDE.md rule #12).

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when ``iso`` is not NYISO, no pocket
    fraction is configured, or no eligible in-zone thermal capacity exists.

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ``"NYISO"`` applies a floor.
        demand: Zonal demand of shape ``(n_zones, T)`` in MW.
        zone_names: Zone names ordered to match ``demand``'s rows.

    Returns:
        ``True`` if any pocket floor was applied, else ``False``.
    """
    if iso != "NYISO" or not NYISO_LOCAL_SELFSUPPLY_FRAC:
        return False

    from market_sim.data.fleet import FUEL_TYPE_MAP

    thermal_codes = _dispatchable_thermal_codes()
    is_thermal = np.isin(fleet_arrays.fuel_type_idx, thermal_codes)
    zone_to_idx = {z: i for i, z in enumerate(zone_names)}
    demand = np.asarray(demand, dtype=float)
    hours = int(fleet_arrays.availability.shape[1])

    applied = False
    for zone, frac in NYISO_LOCAL_SELFSUPPLY_FRAC.items():
        if frac <= 0.0 or zone not in zone_to_idx:
            continue
        z_idx = zone_to_idx[zone]
        in_zone = (fleet_arrays.zone_idx == z_idx) & is_thermal
        rows = np.flatnonzero(in_zone & (fleet_arrays.pmax > 0.0))
        if rows.size == 0:
            continue

        target = frac * demand[z_idx, :hours]
        avail_cap = (
            fleet_arrays.pmax[rows, np.newaxis] * fleet_arrays.availability[rows, :]
        )
        # Never demand more than the in-zone fleet can supply that hour.
        np.minimum(target, avail_cap.sum(axis=0), out=target)

        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis],
                (fleet_arrays.pmin.size, hours),
            ).copy()

        # Fill the floor in marginal-cost merit order, not by raw heat rate: the
        # LI reliability minimum is met by the in-zone fleet that would actually
        # run — efficient gas first, the dear oil-fired peakers LAST. Distillate
        # costs ~5x gas per MMBtu, so a raw heat-rate sort put oil CTs (heat rate
        # ~9.8) AHEAD of gas CTs (~10-11) and forced ~1.5 TWh/yr of non-physical
        # flat, year-round LI oil into the floor. Tiering oil last means it enters
        # the floor only when in-zone gas capacity is exhausted (deep-winter peak);
        # genuine winter dual-fuel oil still runs economically on top of the floor
        # via the delivered-oil-priced switch (it is not suppressed, only no longer
        # force-committed for a summer reliability minimum). Fuel-cost ordering is
        # forward-reproducible (gas stays cheaper than oil in every forward year),
        # not a fit to measured oil volume (CLAUDE.md rule #12).
        oil_code = FUEL_TYPE_MAP.get("oil")
        is_oil = (fleet_arrays.fuel_type_idx[rows] == oil_code).astype(int)
        order = rows[np.lexsort((fleet_arrays.heat_rate[rows], is_oil))]
        remaining = target.copy()
        for r in order:
            cap = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
            take = np.minimum(remaining, cap)
            np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
            remaining = remaining - take
        applied = True
    return applied


def inject_nyiso_firm_imports(fleet_arrays, iso: str, year: int) -> bool:
    """Floor NYISO's firm (must-flow) import baseload at the priced node.

    Hydro-Québec (Châteauguay/Cedars) and Ontario (IESO) sell NY firm,
    long-term scheduled hydro/nuclear baseload that flows regardless of NY's
    hourly price. The priced node prices them as economic tranches (clearing
    only when NYISO's price exceeds the tranche cost), which backs them off in
    cheap-overnight hours / low-price years even though the real schedule keeps
    flowing. For each tranche in
    :data:`~market_sim.config.constants.NYISO_FIRM_IMPORT_FLOOR_FRAC`, this sets
    a constant hourly ``min_gen`` floor of ``frac × tranche capacity`` on the
    matching import row (capped at the row's available capacity), so the firm
    baseload flows every hour. The configured fractions keep the total firm
    floor below the measured lightest-import hour, so it can never force a
    phantom over-import.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when ``iso`` is not NYISO, no fraction
    is configured, or no matching import row is present (e.g. the served-wedge
    path without a priced node).

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ``"NYISO"`` applies a floor.
        year: Backcast year (unused today; carried for parity with the other
            priced-node injectors and future per-year firm schedules).

    Returns:
        ``True`` if any firm-import floor was applied, else ``False``.
    """
    if iso != "NYISO" or not NYISO_FIRM_IMPORT_FLOOR_FRAC:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    unit_ids = list(fleet_arrays.unit_ids)
    applied = False
    for name, frac in NYISO_FIRM_IMPORT_FLOOR_FRAC.items():
        if frac <= 0.0:
            continue
        rows = [i for i, uid in enumerate(unit_ids) if uid.endswith(f"_{name}")]
        for r in rows:
            if fleet_arrays.pmax[r] <= 0.0:
                continue
            floor = frac * fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
            if fleet_arrays.min_gen is None:
                fleet_arrays.min_gen = np.broadcast_to(
                    fleet_arrays.pmin[:, np.newaxis],
                    (fleet_arrays.pmin.size, hours),
                ).copy()
            np.maximum(
                fleet_arrays.min_gen[r, :], floor, out=fleet_arrays.min_gen[r, :]
            )
            applied = True
    return applied


def build_import_node_reconciliation(
    fleet_arrays,
    iso: str,
    year: int,
    band_frac: float = NYISO_IMPORT_RECON_BAND_FRAC,
    *,
    mode: str = "backcast",
    forward_net_import_twh: dict[int, float] | float | None = None,
    system_demand: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Build the priced-node monthly net-interchange band, mode-aware.

    Returns the inputs for a per-month band constraint
    (:func:`market_sim.model.dispatch._build_import_node_rows`) that holds the
    NYISO priced import node's monthly NET interchange within an envelope while
    leaving the priced tranches free to set the marginal price *within* each
    month. The band **target** depends on the run mode — and that is the whole
    forecast-vs-backcast distinction (CLAUDE.md rule #10, methodology spec §1.7):

    * ``mode == "backcast"`` — target the **measured** EIA-930 net-interchange
      schedule (:func:`market_sim.data.eia_loader.nyiso_net_interchange`), the
      *realization*. The economic priced node clears a near-flat ~18.5-21.6 TWh
      because its tranche offers are near-static and do not track the metered
      schedule's year-over-year decline (23.45 -> 20.35 -> 19.09 TWh), so it
      under-imports in 2023 and over-imports in 2024/25; banding it to the
      metered level REPLACES that economic estimate with the authoritative
      measurement (rule #11). This is standard production-cost boundary-flow
      calibration (Aurora/PLEXOS/GridView/PROMOD pin the tie-line net flow
      against an unmodeled neighbor; ReEDS fixes net trade with non-modeled
      regions): the neighbor is not co-optimized, so its flow cannot be
      economically derived and is calibrated to actuals in a backcast. The
      target is the measured schedule itself, NOT a residual-minimizing volume
      (rule #12); ``band_frac`` only sets the price / feasibility headroom.

    * ``mode == "forecast"`` — there is no measured schedule, so the target is
      the **neighbor's forecast net position** supplied via
      ``forward_net_import_twh`` (the PJM / Hydro-Québec / Ontario / ISO-NE
      forward export outlook as an annual NYISO net import, shaped to monthly by
      the forecast load via
      :func:`market_sim.data.eia_loader.nyiso_forward_net_import_monthly`). This
      keeps the dispatch being validated the same as the dispatch being forecast
      (rule #10). When no forecast is supplied the band **relaxes** (returns
      ``None``): the priced seam clears endogenously, never pinned to a measured
      monthly total. The forward band is forward-reproducible — it regenerates
      for any year from forward drivers and responds to changed conditions.

    Net sign: the node columns are import tranches (``P >= 0``, inject) plus
    export sinks (``P <= 0``, withdraw), so ``sum P`` is the node's *net import*
    in MW — the negative of the measured export-positive
    :func:`~market_sim.data.eia_loader.nyiso_net_interchange`. Both the backcast
    target (``-sum export``) and the forecast target (the supplied net import)
    are therefore in net-import (positive) MWh, on the same monthly basis.

    Args:
        fleet_arrays: Vectorized fleet (read-only here; the constraint lives in
            the LP, not in ``min_gen``).
        iso: ISO identifier; only ``"NYISO"`` builds a band.
        year: Year keying the measured (backcast) or forecast trajectory.
        band_frac: Monthly band half-width as a fraction of the monthly net
            import. ``0.0`` makes it a hard monthly equality.
        mode: ``"backcast"`` (target the measured schedule, default — preserves
            the existing calibration behaviour byte-for-byte) or ``"forecast"``
            (target the supplied neighbor forecast, else relax).
        forward_net_import_twh: Forecast-only. NYISO annual net import (TWh,
            import-positive) as a ``dict[year -> TWh]`` or bare ``float``; the
            forward band source. Ignored in backcast.
        system_demand: Forecast-only. Hourly system demand used to shape the
            annual forecast to monthly targets (imports track load). Ignored in
            backcast.

    Returns:
        Tuple ``(node_gen_idx, monthly_lo, monthly_hi)`` — the import-node
        thermal-block row indices and the per-month MWh net-import bounds — or
        ``None`` (no constraint) when ``iso`` is not NYISO, no priced import node
        is present (the served-wedge path), or no target is available for the
        mode (backcast year with no measured schedule / forecast with no
        supplied neighbor position).
    """
    if iso != "NYISO":
        return None

    from market_sim.data.eia_loader import (
        nyiso_forward_net_import_monthly,
        nyiso_net_interchange,
    )
    from market_sim.data.fleet import FUEL_TYPE_MAP, _hour_to_month_index

    hours = int(fleet_arrays.availability.shape[1])
    import_code = FUEL_TYPE_MAP["import"]
    # Import tranches (pmax > 0, inject) AND export sinks (pmin < 0, withdraw):
    # their signed P-sum is the node's net import, matching the net-interchange
    # basis. A node with neither is the served-wedge path (no priced node) —
    # nothing to reconcile.
    is_node = fleet_arrays.fuel_type_idx == import_code
    node_idx = np.flatnonzero(
        is_node & ((fleet_arrays.pmax > 0.0) | (fleet_arrays.pmin < 0.0))
    )
    if node_idx.size == 0:
        return None

    if mode == "forecast":
        # Forward band source: the neighbor's forecast net position. None when no
        # forecast is supplied -> band relaxes to the bare priced-seam economics.
        monthly_target = nyiso_forward_net_import_monthly(
            year, forward_net_import_twh, system_demand
        )
        if monthly_target is None:
            return None
    else:
        # Backcast: the measured EIA-930 realization (unchanged behaviour).
        export_pos = nyiso_net_interchange(year)  # export-positive MW, (8760,)
        if export_pos is None:
            return None
        export_pos = np.asarray(export_pos, dtype=float).reshape(-1)[:hours]
        if export_pos.size < hours:
            return None
        # Net import (MW) = -export-positive interchange; aggregate to monthly
        # MWh on the same hour->month map the LP constraint uses (no per-hour
        # Python loop).
        net_import = -export_pos
        month_index = _hour_to_month_index(hours)
        n_months = int(month_index.max()) + 1
        monthly_target = np.zeros(n_months, dtype=float)
        np.add.at(monthly_target, month_index, net_import)

    half = abs(band_frac) * np.abs(monthly_target)
    monthly_lo = monthly_target - half
    monthly_hi = monthly_target + half
    return node_idx, monthly_lo, monthly_hi


def _miso_firm_import_uid() -> str:
    """Return the unit id of the Manitoba firm-hydro import row."""
    return f"{MISO_MANITOBA_FIRM_IMPORT_ZONE}_{MISO_MANITOBA_FIRM_IMPORT_NAME}"


def build_miso_firm_imports(
    iso: str, year: int | None = None, mode: str = "forecast"
) -> list[Generator]:
    """Return Manitoba Hydro's firm-hydro import block for MISO-North.

    Manitoba Hydro is MISO's single largest import source and the structural
    reason MISO is a net IMPORTER: it sells ~10-15 TWh/yr of FIRM contracted
    hydro into MISO-North over the Manitoba<->US HVDC / 500 kV ties. This import
    sits OUTSIDE the gas-margin reference-price seam
    (:data:`~market_sim.config.constants.INTERFACE_NEIGHBORS`): firm hydro has no
    gas x heat-rate price analogue, so it is a SEPARATE block priced as firm
    hydro — a low, near-constant energy offer reflecting the contract.

    The block is a single ``fuel_type="import"`` pseudo-generator landed directly
    in :data:`~market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_ZONE`
    (``MISO-North``, the model zone the ties physically enter), bounded
    ``[0, pmax]`` and offered at
    :data:`~market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_OFFER`. Because
    its ``fuel_type`` is ``"import"`` it is counted as net interchange (not
    in-state generation), and its must-flow firm floor is applied post-assembly
    by :func:`inject_miso_firm_imports`.

    The block capacity ``pmax`` is forecast-native — the flat contract midpoint
    :data:`~market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_MW` — for any
    forecast year, and in BACKCAST mode is overlaid with the measured per-year
    firm-hydro delivery
    (:data:`~market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR`,
    drought-responsive) via
    :func:`~market_sim.config.constants.resolve_miso_manitoba_firm_import_mw`.
    Neither is fitted to the net-interchange residual (claude.md rules #11/#12):
    the per-year delivery is the measured DIRECTED firm import computed before any
    LP runs, regenerable for a forward year from Manitoba's hydro outlook + the
    contract.

    Args:
        iso: ISO identifier; only ``"MISO"`` returns a block.
        year: Run year; selects the per-year measured firm delivery in backcast
            mode (``None`` / forecast year falls back to the flat contract MW).
        mode: ``"forecast"`` (flat contract midpoint) or ``"backcast"`` (measured
            per-year firm delivery where available).

    Returns:
        The Manitoba firm-hydro import pseudo-generator (one element), or an
        empty list for any non-MISO ISO (byte-identical).
    """
    if iso != "MISO":
        return []
    pmax = resolve_miso_manitoba_firm_import_mw(year, mode)
    return [
        Generator(
            unit_id=_miso_firm_import_uid(),
            name=MISO_MANITOBA_FIRM_IMPORT_NAME,
            zone=MISO_MANITOBA_FIRM_IMPORT_ZONE,
            fuel_type="import",
            pmax_mw=pmax,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=MISO_MANITOBA_FIRM_IMPORT_OFFER,
            eford=0.0,
        )
    ]


def inject_miso_firm_imports(fleet_arrays, iso: str, year: int) -> bool:
    """Floor Manitoba Hydro's firm-hydro import block at its contracted baseload.

    The Manitoba contract is firm must-flow energy: it flows into MISO-North
    every hour regardless of MISO's hourly price (the Hydro-Québec firm-import
    pattern, :func:`inject_nyiso_firm_imports`). This sets a constant hourly
    ``min_gen`` floor of
    :data:`~market_sim.config.constants.MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC` ×
    the block's available capacity on the Manitoba import row
    (:func:`build_miso_firm_imports`), so the firm baseload flows even in
    cheap-overnight hours / low-price years where an unfloored economic offer
    would otherwise back it off. At floor frac 1.0 the block is near-constant by
    design — the contracted firm baseload, ~12.3 TWh/yr.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when the floor was
    applied, ``False`` (byte-identical) when ``iso`` is not MISO, the floor
    fraction is non-positive, or the Manitoba block is not in the fleet.

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ``"MISO"`` applies a floor.
        year: Backcast year (unused today; carried for parity with the other
            firm-import injectors and future per-year firm schedules).

    Returns:
        ``True`` if the firm-import floor was applied, else ``False``.
    """
    if iso != "MISO" or MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC <= 0.0:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    target_uid = _miso_firm_import_uid()
    applied = False
    for r, uid in enumerate(fleet_arrays.unit_ids):
        if uid != target_uid or fleet_arrays.pmax[r] <= 0.0:
            continue
        floor = (
            MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC
            * fleet_arrays.pmax[r]
            * fleet_arrays.availability[r, :]
        )
        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis],
                (fleet_arrays.pmin.size, hours),
            ).copy()
        np.maximum(fleet_arrays.min_gen[r, :], floor, out=fleet_arrays.min_gen[r, :])
        applied = True
    return applied
