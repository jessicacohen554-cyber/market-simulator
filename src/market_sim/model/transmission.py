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
zone (:data:`~market_sim.config.interchange_config.IMPORT_ZONE`) — import supply
tranches plus export sinks. Appended to the fleet, they participate in
dispatch purely through the ordinary energy balance and the external zone's
links into the ISO's trading zones. CAISO's WECC node was the original;
the same machinery now serves PJM (and is data-driven, so NYISO/NEISO only
need constants entries).
"""

import logging

import numpy as np
import pandas as pd
import scipy.sparse as sp

from market_sim.config.constants import (
    CARB_UNSPECIFIED_IMPORT_EF,
    MISO_RDT_CONTRACT_N_TO_S_MW,
    MISO_RDT_CONTRACT_S_TO_N_MW,
    MISO_RDT_DEFAULT_DERATE_FRAC,
    MISO_RDT_TCDC_STEP1_PRICE,
    MISO_RDT_TCDC_STEP2_PRICE,
    MISO_RDT_TCDC_STEP2_START_FRAC,
    MISO_RPE_DEMAND_VALUE,
    MISO_SOUTH_EXTERNAL_ZONE,
    NYISO_LOCAL_SELFSUPPLY_FRAC,
)
from market_sim.config.interchange_config import (
    CAISO_CORRIDOR_ATC_SOLAR_K,
    CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC,
    CAISO_DSW_OVERNIGHT_CLEAN_NAME,
    CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_SURPLUS_CLEAN_DEPTH_STATIC,
    CAISO_DSW_SURPLUS_CLEAN_NAME,
    CAISO_DSW_SURPLUS_REMOTE_VOM,
    CAISO_IMPORT_DELIVERY_BASIS,
    CAISO_IMPORT_TRANCHE_HUB,
    CAISO_OVERNIGHT_CLEAN_HOD_MAX,
    CAISO_PER_HUB_IMPORT_ZONES,
    CAISO_PER_HUB_NEIGHBORS,
    EXPORT_TRANCHES,
    EXPORT_TRANCHES_BY_YEAR,
    EXTERNAL_SIMULTANEOUS_LIMITS,
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
    resolve_miso_manitoba_firm_import_mw,
)
from market_sim.config.iso_configs import (
    InterfaceLimit,
    ISOConfig,
    TransferLink,
    Zone,
)
from market_sim.data.fleet import Generator
from market_sim.data.floor_mechanisms import (
    MECH_CAISO_GAS_COMMITMENT_FLOOR,
    MECH_FIRM_IMPORT,
    MECH_NYISO_SELFSUPPLY,
    MECH_RELIABILITY_FLOOR,
    ensure_mechanism,
)


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
) -> list[tuple]:
    """Resolve aggregate interface limits to LP flow-column groups.

    Maps each :class:`~market_sim.config.iso_configs.InterfaceLimit`'s
    ``(from_zone, to_zone)`` pair references onto EVERY link joining that zone
    pair: a link whose own from→to matches the listed orientation enters with
    sign ``+1``, a reversed link with ``-1`` — so the group sum reads as the
    net corridor flow in the listed direction (a one-way link pair such as
    MISO's RDT contributes ``flow(a→b) − flow(b→a)`` from one listed pair).
    Returns one ``(link_idx, cap_mw, bidirectional, lower_cap_mw, signs)``
    tuple per limit for :func:`market_sim.model.dispatch.build_constraints`,
    where ``lower_cap_mw`` is the limit's ``reverse_cap_mw`` (``None`` keeps
    the symmetric/one-sided ``bidirectional`` behaviour). Returns an empty
    list when the ISO declares no interface limits (the LP is then identical).
    """
    groups: list[tuple] = []
    for limit in interface_limits:
        idx: list[int] = []
        signs: list[float] = []
        for pair in limit.links:
            a, b = tuple(pair)
            for i, ln in enumerate(links):
                if (ln.from_zone, ln.to_zone) == (a, b):
                    idx.append(i)
                    signs.append(1.0)
                elif (ln.from_zone, ln.to_zone) == (b, a):
                    idx.append(i)
                    signs.append(-1.0)
        lower = None if limit.reverse_cap_mw is None else float(limit.reverse_cap_mw)
        groups.append(
            (
                np.array(idx, dtype=int),
                float(limit.cap_mw),
                bool(limit.bidirectional),
                lower,
                np.array(signs, dtype=float),
            )
        )
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


def get_link_flow_cost_array(links: list[TransferLink]) -> np.ndarray | None:
    """Return the ``(n_links,)`` per-MWh flow-cost array, or ``None`` if all zero.

    Nonzero entries carry a priced transfer step (MISO's RDT TCDC tiers, see
    :func:`apply_miso_rdt_tcdc`) into the LP objective's flow block. Returning
    ``None`` when every link is free keeps the default cost vector
    byte-identical (the flow block stays zero-cost).
    """
    costs = np.array([getattr(link, "flow_cost", 0.0) for link in links], dtype=float)
    return costs if np.any(costs != 0.0) else None


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
# FALLBACK-ONLY (audit item C-14, scalar-remediation B-CAI-1 2026-07-05). This
# single aggregate export cap is used ONLY by the superseded
# `build_caiso_bidir_intertie` (gated on `caiso_bidir_intertie`, default off).
# The caiso-51 keeper — and every current CAISO run — uses `caiso_per_hub_intertie`
# instead, whose export legs are bounded by each corridor's physical link TTC
# (`_caiso_corridor_export_cap_mw`) plus the measured p95 net-export
# deliverability envelope (`caiso_corridor_flow_limit` /
# `eia_loader.measured_corridor_flow_envelope(direction="export")`) — NOT this
# scalar. So changing this value does not move any keeper solve.
#   Re-derived from the SAME measured series the per-hub export envelopes use:
# the EIA-930 CISO BA-to-BA net-interchange (the realized ATC proxy on disk; the
# named "OASIS export ATC" is unreachable from this environment — see
# scripts/derive_caiso_export_cap.py). Convention matches the corridor
# envelopes' own CAISO_CORRIDOR_FLOW_PERCENTILE (p95): the peak-bucket ceiling =
# max over (month x hour-of-day) of the p95 aggregate net export, 2023-2025
# (2026 holdout excluded, rule #22) = 4,361 MW. The prior 3,500 was a
# hand-fitted "typical peak" sitting at ~p99 of the aggregate, BELOW the measured
# export capability. rule-23 source-data change: the caiso-51 keeper
# (2026-07-03-caiso-51-firm-base) landed the measured per-hub export envelopes.
# Frozen derive script: scripts/derive_caiso_export_cap.py.
CAISO_BIDIR_EXPORT_CAP_MW = 4361.0
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
    :data:`~market_sim.config.interchange_config.IMPORT_TRANCHES` (so the rising
    border-carbon ladder of :data:`~market_sim.config.interchange_config.IMPORT_TRANCHE_EF`
    is preserved — firm hydro/solar pay no CARB adder, unspecified gas pays the
    full one), but the aggregate import capacity is rescaled to
    :data:`CAISO_BIDIR_IMPORT_CAP_MW` (the tightened simultaneous-import cap).
    The export leg is a SINGLE sink bounded at :data:`CAISO_BIDIR_EXPORT_CAP_MW`,
    the measured aggregate export-direction capability ceiling (fallback-only;
    the per-hub successor uses per-corridor physical + measured envelopes).

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


def build_caiso_per_hub_intertie(
    border_carbon_per_mwh: float = 0.0,
    surplus_clean: bool = False,
    overnight_clean: bool = False,
) -> list[Generator]:
    """Return CAISO's WECC tie as TWO per-hub signed flows (Malin + Palo Verde).

    The structurally-faithful successor to :func:`build_caiso_bidir_intertie`
    (single averaged node) and the :func:`build_import_generators` +
    :func:`build_export_sinks` pair (pooled node). Each import tranche of
    :data:`~market_sim.config.interchange_config.IMPORT_TRANCHES` is placed in the
    external zone of the WECC neighbor hub it proxies
    (:data:`~market_sim.config.interchange_config.CAISO_IMPORT_TRANCHE_HUB` →
    :data:`~market_sim.config.interchange_config.CAISO_PER_HUB_IMPORT_ZONES`), and each hub
    zone gets ONE export leg (a negative-generation sink, see
    :func:`build_export_sinks`). Tranche capacities are the natural
    :data:`IMPORT_TRANCHES` values (the simultaneous cap is the interface limit,
    not a per-tranche rescale, matching the keeper); the rising border-carbon
    ladder of :data:`~market_sim.config.interchange_config.IMPORT_TRANCHE_EF` is preserved.

    Prices are placeholders, overwritten hour-by-hour by
    :func:`inject_caiso_per_hub_intertie_prices` to each leg's own measured hub.

    Args:
        border_carbon_per_mwh: Unspecified-import border carbon adjustment
            ($/MWh); scaled per import tranche by its emission factor. 0 disables.
        surplus_clean: Append the south-corridor surplus-clean depth tranche
            (caiso-87, ``ScenarioConfig.caiso_dsw_surplus_clean``). Built with
            ZERO capacity — :func:`inject_caiso_dsw_surplus_clean` arms its
            hourly capability (measured depth-in-surplus net of the shaped firm
            block, surplus-trigger hours only) and
            :func:`inject_caiso_per_hub_intertie_prices` prices it at the
            measured Palo Verde hub + wheel with EF 0 (no border carbon —
            WEIM/EDAM clean-surplus GHG attribution). Un-injected (e.g. no
            measured hub/gas series) it stays 0 MW: inert by construction.
        overnight_clean: Append the south-corridor OVERNIGHT clean depth
            tranche (caiso-93, ``ScenarioConfig.caiso_dsw_overnight_clean``).
            Same zero-capacity pattern: :func:`inject_caiso_dsw_overnight_clean`
            arms its hourly capability (measured unconditional overnight depth,
            hod 0-5, net of the shaped firm block AND the caiso-87 surplus
            tranche) and the per-hub injector prices it at the RAW measured
            Palo Verde hub with EF 0 and no wheel (WEIM transfer basis —
            ``CAISO_IMPORT_DELIVERY_BASIS``). Un-injected it stays 0 MW.

    Returns:
        The per-hub import tranches (cheapest first within each hub) followed by
        one export leg per hub zone.
    """
    iso = "CAISO"
    base = list(IMPORT_TRANCHES.get(iso, []))
    if surplus_clean:
        # Placeholder $/MWh only (never marginal at 0 MW; the per-hub injector
        # reprices it hourly): the static DSW_CCGT rung minus its carbon share
        # would be fiction — carry the scarcity rung's price so an unpriced
        # row can never undercut a real rung.
        base.append((CAISO_DSW_SURPLUS_CLEAN_NAME, 0.0, 180.0))
    if overnight_clean:
        # Same placeholder logic (caiso-93): the injector refuses to arm MW
        # without a measured hub series, so the row is 0 MW whenever this
        # price could ever matter.
        base.append((CAISO_DSW_OVERNIGHT_CLEAN_NAME, 0.0, 180.0))
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
# on (COI/Path-66 north → NP15; Path-46/WOR south → SP15_rest, the SP15 split's
# south gateway). Used both to re-home the WECC_import links onto the per-hub
# zones and to read each corridor's TTC. The DSW (Palo Verde/WOR) termination
# was re-pointed SP15 → SP15_rest by the 2026-07-09 SP15 local-area split (a
# miss here silently mis-routes the Palo Verde import — scope Phase 1 item 6).
_CAISO_CORRIDOR_LINK_TO: dict[str, tuple[str, ...]] = {
    "WECC_PNW": ("NP15",),
    "WECC_DSW": ("SP15_rest",),
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


# Calendar month → MISO planning-year season (PY runs Jun–May: Summer Jun-Aug,
# Fall Sep-Nov, Winter Dec-Feb, Spring Mar-May). Months 1-5 belong to the PY
# that *began the prior June*; months 6-12 to the PY beginning this June.
# Source: MISO LOLE Study Report seasonal construct (PY2023-24 onward).
_MISO_MONTH_TO_SEASON: dict[int, str] = {
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "fall",
    10: "fall",
    11: "fall",
    12: "winter",
}

# Non-leap month lengths in hours. The model's fixed 8760-hour clock drops
# Feb 29 (see eia_loader), so non-leap month boundaries align exactly in
# every year, including leap years.
_MONTH_HOURS: tuple[int, ...] = tuple(
    d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
)


def build_miso_deliverability_groups(
    links: list[TransferLink],
    year: int,
    hours: int,
) -> list[tuple]:
    """Return per-zone hourly CIL/CEL interface groups for the MISO backcast.

    The seasonal expansion of the static ``MISO_CIL_*`` interface limits in
    ``_miso_config`` (scope decision D7): for each Midwest zone, one signed
    interface group spanning all of the zone's incident *internal* links
    (oriented into the zone) whose hourly upper bound is the zone's seasonal
    Capacity Import Limit (CIL) and hourly lower bound is ``-CEL`` (Capacity
    Export Limit), read per planning-year season from the curated
    ``capacity-deliverability`` data (MISO LOLE Study Reports). Union zones
    (Plains = LRZ 3+5, East = LRZ 2+7) use the member-LRZ sum — a documented
    ceiling (scope decision D4). A season in which any member LRZ's CEL is
    unpublished ("No Limit Found") is export-unconstrained (``-inf``), never 0.
    MISO-South gets no group (the RDT bilateral limit governs).

    Calendar months map to PY seasons (PY = Jun–May), so a calendar backcast
    year straddles two PYs. Jan–May 2023 reads its true PY2022-23 limits
    (scope decision D5): PY2022-23 predates MISO's seasonal construct, so its
    LOLE report publishes ONE annual CIL/CEL set per LRZ — stored with season
    "annual" and read here for every month that lands in that PY. Only when a
    PY is entirely absent from the data (a backcast reaching before the
    extraction window) are its months backfilled from the *earliest
    available* PY's same-season values.

    External-node border links are NOT members: CIL/CEL measure transfer from
    the rest of MISO (the LOLE island model), while external seams carry
    their own measured limits (per-seam envelopes + the 8,700 MW simultaneous
    cap). Returns an empty list when the clean partition is absent, so the
    caller falls back to the static summer caps (graceful, never silent-zero).

    Args:
        links: The (possibly import-node-extended) link list, in flow-column
            order.
        year: Calendar backcast year.
        hours: LP horizon (≤ 8760 on the fixed non-leap clock).

    Returns:
        One ``(link_idx, cil_hourly, False, cel_hourly, signs)`` tuple per
        Midwest zone with at least one incident internal link.
    """
    from market_sim.config.capacity_area_crosswalk import _MISO_LRZ_TO_ZONE
    from market_sim.data import capacity_deliverability as capdel

    available = capdel.available_delivery_years("MISO")
    if not available:
        return []

    def _py_label(py_start: int) -> str:
        """Resolve a planning-year start to an available delivery-year label."""
        label = f"{py_start}/{py_start + 1}"
        if label in available:
            return label
        # Earlier than the extraction window → earliest available same-season
        # values (the PY2022-23 backfill); later → latest available.
        return min(available) if label < min(available) else max(available)

    # Zone → member LRZ areas (South excluded — RDT governs).
    members: dict[str, list[str]] = {}
    for lrz, zone in _MISO_LRZ_TO_ZONE.items():
        if zone != "MISO-South":
            members.setdefault(zone, []).append(lrz)

    # Per-month (delivery-year label, season), PY = Jun–May. A pre-seasonal PY
    # (PY2022-23 and earlier: one annual CIL/CEL set) resolves every season to
    # its "annual" row — asking _metric_by_area for a season the PY never
    # published would silently fall back to the latest PY's row instead.
    month_py = [
        (_py_label(year if m >= 6 else year - 1), _MISO_MONTH_TO_SEASON[m])
        for m in range(1, 13)
    ]
    seasons_by_py = {
        py: capdel.available_seasons("MISO", py) for py in {py for py, _ in month_py}
    }
    month_py = [
        (py, season if season in seasons_by_py[py] else "annual")
        for py, season in month_py
    ]
    # Cache the per-(PY, season) CIL/CEL dicts (≤ 5 distinct slots per year).
    limits: dict[tuple[str, str], tuple[dict[str, float], dict[str, float]]] = {}
    for py, season in set(month_py):
        limits[(py, season)] = (
            capdel.import_limit_by_area("MISO", py, season),
            capdel.export_limit_by_area("MISO", py, season),
        )
    if all(not imp for imp, _ in limits.values()):
        return []

    # Hour → month index on the fixed non-leap clock (Feb 29 dropped).
    month_of_hour = np.repeat(np.arange(12), _MONTH_HOURS)[:hours]

    groups: list[tuple] = []
    for zone, lrzs in members.items():
        idx: list[int] = []
        signs: list[float] = []
        for i, ln in enumerate(links):
            internal = ln.from_zone.startswith("MISO-") and ln.to_zone.startswith(
                "MISO-"
            )
            if not internal:
                continue
            if ln.to_zone == zone:
                idx.append(i)
                signs.append(1.0)
            elif ln.from_zone == zone:
                idx.append(i)
                signs.append(-1.0)
        if not idx:
            continue
        # Monthly CIL/CEL (12 values), then expanded hour-by-month. A member
        # LRZ missing from the import dict makes that season's CIL unusable →
        # +inf (never bind on a partial sum); a member missing from the export
        # dict means "No Limit Found" → export-unconstrained (-inf lower).
        cil_m = np.empty(12, dtype=float)
        cel_m = np.empty(12, dtype=float)
        for m in range(12):
            imp, exp = limits[month_py[m]]
            cil_m[m] = (
                sum(imp[a] for a in lrzs) if all(a in imp for a in lrzs) else np.inf
            )
            cel_m[m] = (
                sum(exp[a] for a in lrzs) if all(a in exp for a in lrzs) else np.inf
            )
        groups.append(
            (
                np.array(idx, dtype=int),
                cil_m[month_of_hour],
                False,
                cel_m[month_of_hour],
                np.array(signs, dtype=float),
            )
        )
    return groups


def split_caiso_import_node_per_hub(iso_config: ISOConfig) -> ISOConfig:
    """Split CAISO's single ``WECC_import`` node into the two per-hub corridors.

    Returns a copy of ``iso_config`` in which the single ``WECC_import`` external
    zone is replaced by ``WECC_PNW`` (COI/Path-66 → NP15) and ``WECC_DSW``
    (Path-46/WOR → SP15), the two ``WECC_import`` import links are re-homed onto
    those zones, and the ``WECC_import_simultaneous`` interface limit is rewritten
    to span the two corridor links (so the baked 7,500 MW simultaneous-import cap
    is preserved and re-homed — note this is the fitted audit item C-5 scalar,
    superseded in the caiso-51 keeper by the published MIC seam limit when
    ``capacity_deliverability_limits`` is on; see
    docs/caiso-c5-wecc-cap-closeout-2026-07-03.md). Internal CAISO links (Path
    15/26) and every other field are
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


# Firm/contracted CAISO import tranches (``caiso_perhub_firm_base``): the
# blocks that proxy long-term specified-source contracts and out-of-state
# ownership shares (BPA firm hydro over COI; desert-SW solar PPAs over
# Path-46), which in the real market are scheduled at contract cost and flow
# largely independent of the hourly spot spread — they are INFRAMARGINAL, so
# CAISO's clearing price stays domestic even while 3-6 GW imports flow (the
# 2023/24 summer evidence: CAISO cleared $50-54 while Palo Verde spot sat at
# $69-74 and real imports still ran 3-4 GW). Pricing these blocks at the
# hourly spot hub (the plain per-hub injector) mis-structures the seam: any
# hour the tie is marginal transplants the spot spike into CAISO. With the
# flag on, these tranches keep their static contract-cost estimates from
# IMPORT_TRANCHES (documented Tier-3 contract-cost proxies — a reconciled
# estimate kept where the accurate spot price is misaligned to the contracted
# quantity it would price, CLAUDE.md #14 exception), while the genuinely
# spot-traded tranches (Mid-C economy, desert-SW thermal, scarcity) and both
# export legs stay at the measured hourly hub.
CAISO_FIRM_IMPORT_TRANCHES: frozenset[str] = frozenset(
    {"PNW_hydro_base", "DSW_solar_PV"}
)


def inject_caiso_per_hub_intertie_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
    carbon_price: float,
    firm_base: bool = False,
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
    charge of :data:`~market_sim.config.interchange_config.CAISO_IMPORT_DELIVERY_BASIS`
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
    # The surplus-clean (caiso-87) and overnight-clean (caiso-93) depth
    # tranches are not on the static ladder; each prices like any other spot
    # rung (EF 0 zeroes the carbon term; the overnight tranche's delivery
    # basis is (0.0, 0.0) — raw hub, no wheel).
    import_names.add(CAISO_DSW_SURPLUS_CLEAN_NAME)
    import_names.add(CAISO_DSW_OVERNIGHT_CLEAN_NAME)
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
            if firm_base and name in CAISO_FIRM_IMPORT_TRANCHES:
                continue  # firm/contracted block: inframarginal contract cost,
                # keeps its static ladder price (see CAISO_FIRM_IMPORT_TRANCHES)
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


def inject_caiso_firm_import_shape(fleet_arrays, iso: str, year: int) -> bool:
    """Shape the CAISO firm import blocks by the measured revealed base profile.

    caiso-73 (``config.caiso_firm_import_shape``; FINDING-caiso72 live lead
    #1): the flat firm base (:data:`CAISO_FIRM_IMPORT_TRANCHES` under
    ``caiso_perhub_firm_base``) offers the same MW every hour, while the
    measured CISO corridor net imports are strongly shaped — overnight
    5.3–6.3 GW, midday 0.2–1.3 GW, evening ramping back to 5.4–6.2 GW
    (2023–2025, model-clock aligned) — so the model under-imports the deep
    evening by 1.4–2.2 GW and over-imports midday (+2.3 GW at h14;
    FINDING-caiso72-step0). For each firm tranche this rewrites the hourly
    availability CAPABILITY as::

        cap[t] = firm_mw[year] × w[t]        # then pmax = max(cap),
                                             # availability ∝ cap / max(cap)

    where ``firm_mw[year]`` is the tranche's year-grounded published level —
    the DMM annual RA-import capacity × MIC corridor split of
    :data:`~market_sim.config.interchange_config.IMPORT_TRANCHES_BY_YEAR`
    (full derivation and sources in its comment block; an unmapped year uses
    the static ladder) — and ``w`` is the unit-mean measured shape of
    :func:`market_sim.data.eia_loader.measured_firm_import_shape` (per-(month
    × hod) median of total measured corridor net imports, same-year in a
    backcast, pooled climatology in a forecast year). Because mean(w) = 1 the
    firm block's annual energy capability equals the published DMM sizing —
    the measured series contributes only the shape, never the level.

    STEP-0 sizing (2024, w from the 2024 extract, firm total 3,371 MW):
    shaped firm ≈ 5.0 GW overnight / 1.0–1.5 GW midday / 4.2–4.9 GW deep
    evening, vs 3.37 GW flat — against the measured evening import deficit of
    1.4–2.2 GW at h19–22 and the +2.3 GW midday over-import. Per-corridor
    maxima (PNW 3.1 GW, DSW 3.6 GW) stay below the corridor link TTCs
    (COI 4.8 GW, Path-46/WOR 10.6 GW); the corridor ATC envelope
    (``caiso_corridor_flow_limit``) and the simultaneous-import interface
    limit still bound the delivered flow. The existing eford derate is
    preserved multiplicatively; the block stays a capability the LP clears
    below (pmin = 0) — an hour-varying pmax, not a floor, not a price adder
    (rules #13/#14).

    Returns ``True`` when at least one firm tranche was shaped, ``False``
    (byte-identical) when the fleet has no firm rows or no measured shape is
    available.
    """
    from market_sim.data.eia_loader import measured_firm_import_shape

    hours = int(fleet_arrays.availability.shape[1])
    w = measured_firm_import_shape(iso, year, hours)
    if w is None:
        return False
    ladder = IMPORT_TRANCHES_BY_YEAR.get(iso, {}).get(year) or IMPORT_TRANCHES.get(
        iso, []
    )
    firm_mw = {
        name: cap for name, cap, _ in ladder if name in CAISO_FIRM_IMPORT_TRANCHES
    }
    per_hub_zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        zone = next((z for z in per_hub_zones if uid.startswith(f"{z}_")), None)
        if zone is None:
            continue
        name = uid[len(zone) + 1 :]
        level = firm_mw.get(name)
        if level is None or level <= 0.0:
            continue
        shaped = level * w  # (hours,) capability
        peak = float(shaped.max())
        if peak <= 0.0:
            continue
        fleet_arrays.availability[row, :] *= shaped / peak
        fleet_arrays.pmax[row] = peak
        applied = True
    return applied


def inject_caiso_firm_import_selfschedule(fleet_arrays, iso: str, year: int) -> bool:
    """Floor the CAISO firm import blocks at their shaped capability (must-flow).

    caiso-77 (``config.caiso_firm_import_selfschedule``; gap register G-15
    residual (b)): the firm/contracted tranches
    (:data:`CAISO_FIRM_IMPORT_TRANCHES`) proxy RA import contracts and
    long-term specified-source ownership shares that in the real market are
    self-scheduled or bid at/below $0/MWh (CPUC D.20-06-028 RA import
    must-offer; the block comment above :data:`CAISO_FIRM_IMPORT_TRANCHES`
    documents the same behaviour) — they flow largely independent of the
    hourly spot spread. Pricing them at static contract-cost proxies makes
    them price-GATED instead: any hour the model's LMP sits below the proxy
    (overnight, shoulder) the LP leaves the contracted base untaken and
    serves the load with domestic CC_REGULAR running flat — the measured
    signature is the model's −0.6..−2.3 GW overnight/evening import deficit
    against the revealed 4.3–5.9 GW self-scheduled base while same-fleet
    CAMPD shows CC_REGULAR +0.9–1.6 GW over in exactly those hours.

    This floors each firm tranche's hourly ``min_gen`` at its FULL shaped
    capability ``pmax × availability`` — the published DMM RA-import ×
    MIC-split level × the measured unit-mean revealed-base shape installed by
    :func:`inject_caiso_firm_import_shape` (eford preserved multiplicatively
    inside ``availability``) — the exact analogue of the Manitoba / HQ firm
    must-flow blocks (:func:`inject_miso_firm_imports` /
    :func:`inject_nyiso_firm_imports`, floor frac 1.0). Mechanism attribution
    is :data:`~market_sim.data.floor_mechanisms.MECH_FIRM_IMPORT`: a
    CONTRACT, ablation-kept and D-2 exempt by construction
    (``NON_THERMAL_MECHS`` / ``MECH_ABLATION_KEPT``). At ``pmin = pmax`` the
    tranche can never set the margin, so its ladder $/MWh becomes pure
    inframarginal contract-cost bookkeeping — the two G-26
    static-fitted-pending-measured firm prices stop influencing dispatch.

    Zero new free parameters: the floor reuses the caiso-73 measured level ×
    shape unchanged. Rule-17 declaration: driver = RA/LTC contract must-offer
    (CPUC D.20-06-028) and the DMM revealed self-scheduled base; window =
    every hour AT the measured (month × hod) median self-schedule (the shape
    is the window — midday the measured base itself collapses to
    0.2–1.3 GW); forward story = the DMM forward ladder level × pooled
    climatology shape regenerate in any forecast year.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when at least one
    firm tranche was floored, ``False`` (byte-identical) when the fleet has
    no firm rows.
    """
    hours = int(fleet_arrays.availability.shape[1])
    per_hub_zones = set(CAISO_PER_HUB_IMPORT_ZONES.values())
    applied = False
    for r, uid in enumerate(fleet_arrays.unit_ids):
        zone = next((z for z in per_hub_zones if uid.startswith(f"{z}_")), None)
        if zone is None:
            continue
        name = uid[len(zone) + 1 :]
        if name not in CAISO_FIRM_IMPORT_TRANCHES or fleet_arrays.pmax[r] <= 0.0:
            continue
        floor = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis],
                (fleet_arrays.pmin.size, hours),
            ).copy()
        raised = fleet_arrays.min_gen[r, :] < floor
        np.maximum(fleet_arrays.min_gen[r, :], floor, out=fleet_arrays.min_gen[r, :])
        ensure_mechanism(fleet_arrays)[r, raised] = MECH_FIRM_IMPORT
        applied = True
    return applied


def inject_caiso_dsw_surplus_clean(fleet_arrays, iso: str, year: int) -> bool:
    """Arm the south-corridor surplus-clean import depth (caiso-87).

    In surplus-West hours the marginal import into CAISO is a WEIM/EDAM
    transfer attributed to CLEAN surplus resources — the measured CAISO−hub
    spread carries NO unspecified-import carbon wedge in those hours
    (FINDING-caiso82 §1/§3) — but the model's zero-EF depth truncates at the
    firm blocks + PNW_midC, after which every MW pays a fossil CARB rung.
    This sets the hourly CAPABILITY of the ``DSW_surplus_clean`` tranche
    (built at 0 MW by :func:`build_caiso_per_hub_intertie`)::

        cap[t] = surplus[t] × max(0, depth_year − firm_south_capability[t])

    * ``surplus[t]`` — the corridor's own measured Palo Verde hub price
      sits below the remote gas-CCGT floor ``HR_DSW_CCGT × SoCal_citygate
      weekly + remote VOM`` (no carbon: AZ/NV are uncarbonized), i.e. gas is
      not the hub's marginal resource, so the surplus is clean. Evaluated
      ONLY on measured hub hours (the 2023 Jan–Feb reference-formula fill is
      pricing continuity, not surplus evidence → non-surplus).
    * ``depth_year`` — the measured year depth-in-surplus
      (:data:`CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR`, p95 corridor net import
      over trigger hours; CV 0.056 / LOYO ≤12.5% across 2023–2025 — gates in
      the interchange_config block); an unmapped year carries the pooled
      static entry (persistent WEIM market structure).
    * ``firm_south_capability[t]`` — the shaped DSW firm block
      (``pmax × availability`` after :func:`inject_caiso_firm_import_shape`),
      so the clean depth is net of capacity already carried clean.

    A capability, not a floor (``pmin`` stays 0); the corridor ATC envelope
    (``caiso_corridor_flow_limit``) still caps the delivered flow; the fossil
    rungs are UNCHANGED and price the flow beyond the clean depth (secondary
    dispatch). Pricing (measured hub + Path-46 wheel + EF 0 × border + ε)
    comes from :func:`inject_caiso_per_hub_intertie_prices` via the shared
    tranche maps. Must run AFTER the firm-shape injector.

    Modifies ``fleet_arrays`` in place (eford availability preserved
    multiplicatively). Returns ``True`` when the tranche was armed, ``False``
    (byte-identical: the row stays 0 MW) when the fleet has no clean row or a
    measured hub/gas series is unavailable for ``year``.
    """
    from market_sim.data.eia_loader import measured_intertie_hub_price_raw
    from market_sim.data.fuel import socal_citygate_weekly_hourly

    hours = int(fleet_arrays.availability.shape[1])
    zone = CAISO_PER_HUB_IMPORT_ZONES.get(
        CAISO_IMPORT_TRANCHE_HUB[CAISO_DSW_SURPLUS_CLEAN_NAME]
    )
    uid = f"{zone}_{CAISO_DSW_SURPLUS_CLEAN_NAME}"
    row = next(
        (r for r, u in enumerate(fleet_arrays.unit_ids) if u == uid),
        None,
    )
    if row is None:
        return False
    hub = measured_intertie_hub_price_raw(
        iso, year, hours, CAISO_IMPORT_TRANCHE_HUB[CAISO_DSW_SURPLUS_CLEAN_NAME]
    )
    gas = socal_citygate_weekly_hourly(year, hours)
    if hub is None or gas is None:
        return False
    hr = _CAISO_IMPORT_COUPLE_HR["DSW_CCGT"]  # 0.37/0.0531 ≈ 6.97, matches EF
    floor = hr * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
    surplus = np.isfinite(hub) & np.isfinite(floor) & (hub < floor)
    if not surplus.any():
        return False
    depth = CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR.get(
        year, CAISO_DSW_SURPLUS_CLEAN_DEPTH_STATIC
    )
    # Net of the shaped south firm block (post inject_caiso_firm_import_shape).
    firm_cap = np.zeros(hours)
    for r, u in enumerate(fleet_arrays.unit_ids):
        if not u.startswith(f"{zone}_"):
            continue
        name = u[len(zone) + 1 :]
        if name in CAISO_FIRM_IMPORT_TRANCHES:
            firm_cap += fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
    cap = np.where(surplus, np.clip(depth - firm_cap, 0.0, None), 0.0)
    if cap.max() <= 0.0:
        return False
    # availability carries eford (set at build); scale it by cap/depth and
    # let pmax carry the year depth, mirroring the firm-shape pattern.
    fleet_arrays.availability[row, :] *= cap / depth
    fleet_arrays.pmax[row] = depth
    return True


def inject_caiso_dsw_overnight_clean(fleet_arrays, iso: str, year: int) -> bool:
    """Arm the south-corridor OVERNIGHT clean import depth (caiso-93).

    Overnight (hod 0-5) the measured CAISO−PaloVerde spread carries NO
    unspecified-import carbon wedge in 93-99 % of ALL overnight hours
    (FINDING-caiso93 §2-3): the marginal overnight import is a WEIM/EDAM
    transfer attributed to the West's overnight non-emitting surplus (NW
    hydro + wind), so it pays no border carbon even while gas sets the HUB
    price. The caiso-87 surplus tranche cannot cover this — its
    hub-below-gas-floor trigger fires in only 1.2-3.6 % of 2024/25 overnight
    hours (the no-wedge state overnight is UNCONDITIONAL, not
    hub-state-gated). This sets the hourly CAPABILITY of the
    ``DSW_overnight_clean`` tranche (built at 0 MW by
    :func:`build_caiso_per_hub_intertie`)::

        cap[t] = overnight[t] × max(0, depth_year − firm_south_capability[t]
                                       − surplus_clean_capability[t])

    * ``overnight[t]`` — hod(t) ≤ :data:`CAISO_OVERNIGHT_CLEAN_HOD_MAX`
      (the FINDING-caiso91c/92b window, fixed upstream of the spread
      measurement) AND the raw measured Palo Verde hub is finite for the
      hour — the 2023 Jan–Feb OASIS-gap reference fill is pricing
      continuity, not clean-attribution evidence, so gap hours stay 0 MW
      (the closed winter lane is protected by construction).
    * ``depth_year`` — the measured unconditional overnight depth
      (:data:`CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR`, p95 corridor net
      import over ALL overnight hours; CV 0.041 / LOYO ≤ 8.1 % — gates in
      the interchange_config block, `derive_caiso_overnight_clean_depth.py`);
      an unmapped year carries the pooled static entry.
    * the headroom is net of the shaped DSW firm block AND the caiso-87
      ``DSW_surplus_clean`` tranche's armed capability, so overlap hours
      (overnight ∩ surplus-trigger) never double-carry clean depth — the
      hourly clean total is ``max(firm + surplus, depth_year)``.

    A capability, not a floor (``pmin`` stays 0); the corridor ATC envelope
    still caps delivered flow; the fossil rungs are unchanged and price the
    flow beyond the clean depth. Pricing (RAW measured hub + EF 0 × border
    + ε, NO wheel — WEIM transfers pay no OATT point-to-point charge,
    corroborated by the measured overnight spread) comes from
    :func:`inject_caiso_per_hub_intertie_prices` via the shared tranche maps
    and :data:`CAISO_IMPORT_DELIVERY_BASIS`. Must run AFTER the firm-shape
    injector and AFTER :func:`inject_caiso_dsw_surplus_clean`.

    Modifies ``fleet_arrays`` in place (eford availability preserved
    multiplicatively). Returns ``True`` when the tranche was armed, ``False``
    (byte-identical: the row stays 0 MW) when the fleet has no overnight row
    or no measured hub series exists for ``year`` (the injector never arms MW
    the per-hub price injector cannot price at a measured hub).
    """
    from market_sim.data.eia_loader import measured_intertie_hub_price_raw

    hours = int(fleet_arrays.availability.shape[1])
    zone = CAISO_PER_HUB_IMPORT_ZONES.get(
        CAISO_IMPORT_TRANCHE_HUB[CAISO_DSW_OVERNIGHT_CLEAN_NAME]
    )
    uid = f"{zone}_{CAISO_DSW_OVERNIGHT_CLEAN_NAME}"
    row = next(
        (r for r, u in enumerate(fleet_arrays.unit_ids) if u == uid),
        None,
    )
    if row is None:
        return False
    hub = measured_intertie_hub_price_raw(
        iso, year, hours, CAISO_IMPORT_TRANCHE_HUB[CAISO_DSW_OVERNIGHT_CLEAN_NAME]
    )
    if hub is None:
        return False
    # t = hour index on the model clock; hod = t mod 24 (local calendar).
    overnight = (np.arange(hours) % 24 <= CAISO_OVERNIGHT_CLEAN_HOD_MAX) & np.isfinite(
        hub
    )
    if not overnight.any():
        return False
    depth = CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR.get(
        year, CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC
    )
    # Net of the shaped south firm block AND the caiso-87 surplus tranche
    # (both post-injection: this runs after their injectors).
    firm_cap = np.zeros(hours)
    for r, u in enumerate(fleet_arrays.unit_ids):
        if not u.startswith(f"{zone}_"):
            continue
        name = u[len(zone) + 1 :]
        if name in CAISO_FIRM_IMPORT_TRANCHES or name == CAISO_DSW_SURPLUS_CLEAN_NAME:
            firm_cap += fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
    cap = np.where(overnight, np.clip(depth - firm_cap, 0.0, None), 0.0)
    if cap.max() <= 0.0:
        return False
    fleet_arrays.availability[row, :] *= cap / depth
    fleet_arrays.pmax[row] = depth
    return True


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
    # The surplus-clean (caiso-87) and overnight-clean (caiso-93) depth
    # tranches are not on the static ladder; each prices like any other spot
    # rung (EF 0 zeroes the carbon term; the overnight tranche's delivery
    # basis is (0.0, 0.0) — raw hub, no wheel).
    import_names.add(CAISO_DSW_SURPLUS_CLEAN_NAME)
    import_names.add(CAISO_DSW_OVERNIGHT_CLEAN_NAME)
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
    (:data:`~market_sim.config.interchange_config.CAISO_PER_HUB_NEIGHBORS`), and
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


def caiso_solar_deliverability_derate(
    year: int, hours: int, k: float, floor: float
) -> np.ndarray | None:
    """Return CAISO's hourly LOCAL solar deliverability derate, or ``None``.

    The solar-generation analogue of :func:`forward_corridor_atc_envelope`'s
    midday import collapse, and the Lever-D fix for CAISO solar under-curtailment
    (``docs/caiso-lever-audit-2026-06.md``). The reduced 3-zone CAISO topology
    collapses the sub-area / distribution network where ~70% of CAISO solar
    curtailment actually occurs, so handed the uncurtailed HSL potential the LP
    dispatches ≈ the full potential and re-curtails ≈ 0. This returns a
    multiplicative ceiling on the solar potential::

        derate(t) = clip(1 − k × solar_frac(t), floor, 1)

    where ``solar_frac(t)`` is CAISO's hourly solar penetration
    (:func:`market_sim.data.eia_loader.caiso_solar_fraction`, CISO solar /
    demand). As midday penetration rises the local network can evacuate a smaller
    share of the concentrated solar and the surplus curtails. ``solar_frac`` is a
    FORWARD driver that responds to a changed solar build and load — never the
    measured curtailment outcome — so the curtailed VOLUME emerges per-year from
    that year's own penetration and potential, not a pin to actuals (CLAUDE.md
    #1/#11). The caller multiplies it onto the per-zone solar CF upper bound; the
    LP still dispatches economically up to the ceiling and curtails further below
    it under system oversupply.

    ``k`` (the penetration sensitivity) is derived as the reference-year midday
    curtailment rate ÷ midday solar penetration, stable across CAISO 2023/2024
    (≈ 0.166 / 0.146); see ``ScenarioConfig.caiso_solar_deliverability_k``.

    Args:
        year: Calendar (backcast) year — selects the CISO solar-penetration series.
        hours: Number of LP hours (the returned array length).
        k: Local-deliverability sensitivity to solar penetration.
        floor: Minimum derate, so even at extreme penetration the local network
            still evacuates ``floor`` × potential.

    Returns:
        A ``(hours,)`` derate in ``[floor, 1]``, or ``None`` when the CISO solar
        penetration is unavailable (a forecast year with no extract) or ``k`` is
        non-positive — in which case the caller leaves solar uncapped
        (byte-identical).
    """
    if k <= 0.0:
        return None
    from market_sim.data.eia_loader import caiso_solar_fraction

    solar_frac = caiso_solar_fraction(year, hours)
    if solar_frac is None:
        return None
    return np.clip(1.0 - k * np.asarray(solar_frac, dtype=float), floor, 1.0)


# Unit-id markers tagging a reference-price seam pseudo-generator so the
# post-assembly mc injector (:func:`inject_reference_price_mc`) can find each row
# and map it back to its neighbor and flow tranche. The id is
# ``<zone><mark><name>#<k>`` — import rows take the neighbor price + hurdle,
# export rows the neighbor price - hurdle, both evaluated at tranche ``k``'s flow.
_REF_IMPORT_MARK = "_refimp_"
_REF_EXPORT_MARK = "_refexp_"


def build_reference_price_node(
    iso: str, zone_overrides: dict[str, str] | None = None
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

    Returns:
        Import + export pseudo-generators; empty for an ISO with no neighbor
        registry (so an un-onboarded ISO stays byte-identical).
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    import_zone = IMPORT_ZONE.get(iso)
    gens: list[Generator] = []
    for neighbor in INTERFACE_NEIGHBORS.get(iso, []):
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
    :data:`~market_sim.config.interchange_config.CAISO_IMPORT_DELIVERY_BASIS` is added
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


def inject_miso_pjm_lmp_import_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
) -> bool:
    """Overwrite MISO's PJM seam rows of ``mc`` with measured PJM border LMP.

    The MISO analog of :func:`inject_caiso_import_hub_prices`: each PJM import
    tranche's marginal cost is set to the **measured hourly PJM Day-Ahead LMP**
    at the MISO-facing western border hubs (equal-weight mean of CHICAGO GEN /
    AEP GEN / ATSI GEN) plus the inter-RTO wheeling hurdle, replacing the
    synthetic gas × heat-rate × load-shape ladder that is too flat / too high
    to reproduce the off-peak price dips that drive real PJM-to-MISO import.

    Export tranches are also repriced at hub_price − hurdle, so the seam is
    arbitrage-free: MISO exports to PJM only when MISO's LMP dips below the
    measured PJM border price minus the wheeling cost.

    All import tranches get the SAME measured price (no flow-responsive slope)
    because the measured PJM LMP is the actual border price regardless of flow
    volume — the slope in the gas × HR mechanism is a modeling artifact of the
    supply-curve approximation, not a real market feature.

    Requires the ``pjm_border_lmp_hourly_MISO.parquet`` built by
    ``scripts/build_pjm_border_lmp_miso.py``. Returns ``True`` when at least
    one seam row was repriced, ``False`` when MISO has no measured PJM border
    series (so the run keeps the gas × HR ladder and is byte-identical).
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import measured_miso_pjm_border_prices

    prices = measured_miso_pjm_border_prices(iso, year, int(mc.shape[1]))
    if prices is None:
        return False

    specs = {n.name: n for n in INTERFACE_NEIGHBORS.get(iso, [])}
    pjm_spec = specs.get("PJM")
    hurdle = pjm_spec.hurdle if pjm_spec is not None else 2.0

    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if _REF_IMPORT_MARK in uid:
            tag = uid.rsplit(_REF_IMPORT_MARK, 1)[1]
            name = tag.partition("#")[0]
            if name != "PJM":
                continue
            mc[row, :] = prices + hurdle
            applied = True
        elif _REF_EXPORT_MARK in uid:
            tag = uid.rsplit(_REF_EXPORT_MARK, 1)[1]
            name = tag.partition("#")[0]
            if name != "PJM":
                continue
            mc[row, :] = prices - hurdle
            applied = True
    return applied


def inject_miso_seam_ladder_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
) -> bool:
    """Overwrite MISO's seam band rows of ``mc`` with the measured Q-Q ladders.

    The MISO application of the NEISO audit-C-6 measured-ladder pattern: every
    reference-price band of every seam (PJM / SPP / South, import AND export
    directions) takes its per-year measured band price from
    :data:`~market_sim.config.interchange_config.MISO_SEAM_LADDER_BY_YEAR` —
    the seam's revealed supply curve, derived by
    ``scripts/derive_miso_seam_ladders.py`` from the EIA-930 per-seam flow
    duration curves Q-Q coupled with the measured MISO DA hub LMP. Band ``k``'s
    price is the DA quantile whose exceedance duration equals the measured
    duration of the seam flowing deeper than the band's midpoint, so the LP —
    still clearing each band economically on its OWN hourly internal price —
    reproduces the measured flow duration curve when its price distribution is
    faithful, including the firm/scheduled base that flows regardless of the
    hourly spread (the flow the hurdle-gated spot-spread pricing structurally
    deletes; G-23 2025 import starvation).

    No hurdle is added on top: the ladder prices are revealed clearing
    thresholds that already embed delivery/wheeling costs. Band capacities,
    the measured (month × hour-of-day) seam deliverability envelopes
    (:func:`inject_miso_seam_flow_limit`) and the firm Manitoba block are
    untouched. Runs LAST among the seam price overwrites, displacing the
    ``miso_pjm_border_anchor`` / ``miso_pjm_lmp_import_pricing`` prices on any
    row it covers (the flags are alternatives, never stacked).

    Returns ``True`` when at least one band row was repriced, ``False`` when
    ``iso``/``year`` has no ladder entry or the fleet carries no
    reference-price bands (byte-identical no-op — forecast years fall through
    to the gas-elastic reference-price formula, the hr_by_year two-track
    design).
    """
    from market_sim.config.interchange_config import MISO_SEAM_LADDER_BY_YEAR

    if iso != "MISO":
        return False
    return _inject_seam_ladder(fleet_arrays, mc, MISO_SEAM_LADDER_BY_YEAR.get(year))


def inject_pjm_seam_ladder_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
) -> bool:
    """Overwrite PJM's seam band rows of ``mc`` with the measured Q-Q ladders.

    The PJM application of the MISO/NEISO measured-ladder pattern
    (:func:`inject_miso_seam_ladder_prices`): every reference-price band of
    every seam (MISO / NYISO / Carolinas / TVA / LGEE, import AND export
    directions) takes its per-year measured band price from
    :data:`~market_sim.config.interchange_config.PJM_SEAM_LADDER_BY_YEAR` —
    the seam's revealed supply curve, derived by
    ``scripts/derive_pjm_seam_ladders.py`` from PJM's settlement-grade
    tie-line flow duration curves Q-Q coupled with the measured PJM DA system
    LMP. The LP — still clearing each band economically on its OWN hourly
    internal price — reproduces the measured direction-structural record
    (near-always export to MISO/NYISO, near-always import from
    Carolinas/TVA/LGEE) that the hurdle-gated spot-spread pricing inverts
    (the pjm-95 2023 46%-import-hours miss displacing CC_REGULAR dispatch).

    No hurdle is added on top: the ladder prices are revealed clearing
    thresholds that already embed delivery/wheeling costs. Band capacities
    and the measured per-border deliverability envelopes
    (:func:`inject_pjm_seam_flow_limit`) are untouched. The caller skips the
    firm scheduled-export floor (:func:`inject_reference_price_firm_export`)
    on the rows/years this ladder covers — the firm base the floor pinned is
    the same deep-duration structure the ladder prices (alternatives, never
    stacked; rule 19).

    Returns ``True`` when at least one band row was repriced, ``False`` when
    ``iso``/``year`` has no ladder entry or the fleet carries no
    reference-price bands (byte-identical no-op — forecast years fall through
    to the gas-elastic reference-price formula, the hr_by_year two-track
    design).
    """
    from market_sim.config.interchange_config import PJM_SEAM_LADDER_BY_YEAR

    if iso != "PJM":
        return False
    return _inject_seam_ladder(fleet_arrays, mc, PJM_SEAM_LADDER_BY_YEAR.get(year))


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


# NYISO priced-node tranche → the modeled neighbor whose measured hourly system
# LMP prices it (nyiso_import_hub_prices). HQ_hydro and IESO_Ontario are absent
# on purpose: neither carries an organized-market LMP series in-repo (HQ is a
# firm-contract flow, firm-floored by inject_nyiso_firm_imports; IESO's HOEP is
# not uploaded), so they keep their static contract-ladder values.
_NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR: dict[str, str] = {
    "PJM_west": "PJM",
    "ISONE_tie": "NEISO",
}
# The residual deep non-firm block spans the remaining tie depth across the
# eastern interfaces; its marginal MW cannot be cheaper than every real
# adjacent market, so it prices at the hourly max of the measured neighbors.
_NYISO_HUB_SCARCITY_TRANCHE: str = "import_scarcity"
_NYISO_HUB_EXPORT_TRANCHE: str = "export_surplus"
# Inter-control-area wheeling hurdle ($/MWh) on the NYISO seam — the same $1
# dead-band the PJM↔NYISO NeighborInterface spec carries (INTERFACE_NEIGHBORS
# ["PJM"]["NYISO"].hurdle), applied symmetrically: import at neighbor + hurdle,
# export at neighbor − hurdle, so a same-hour round trip is strictly
# cost-positive (arbitrage-free).
NYISO_IMPORT_HUB_HURDLE: float = 1.0


def inject_nyiso_import_hub_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
) -> bool:
    """Reprice NYISO's non-firm import tranches at measured neighbor hourly LMPs.

    The NYISO analogue of :func:`inject_caiso_import_hub_prices` (measured WECC
    intertie LMP) and :func:`inject_miso_pjm_lmp_import_prices` (measured PJM
    border DA LMP): the priced import node's ``PJM_west`` / ``ISONE_tie`` rows
    take the **measured hourly Day-Ahead system LMP** of the neighbor they proxy
    (:func:`market_sim.data.neighbor_price.neighbor_lmp_hourly`, ``rt``
    fallback) plus the wheeling hurdle; the residual ``import_scarcity`` block
    takes the hourly **max** of the two priced neighbors + hurdle (the deep
    non-firm MW beyond the direct-tie blocks cannot undercut every real
    adjacent market); the ``export_surplus`` sink takes the hourly **min** of
    the two − hurdle. The min (not max) on the destination-blind single sink is
    deliberate: pricing it at the dearer neighbor would open a phantom
    wheel-through arbitrage against the cheap static Canadian import tranches
    (buy IESO at its $22-37 contract constant, "sell" at the NE winter price
    inside the external node) that permanently occupies the sink's 600 MW and
    blocks genuine export hours; the min is the wash-free lower envelope of the
    neighbors' willingness-to-pay. ``HQ_hydro`` / ``IESO_Ontario`` keep their
    static firm-contract ladder values (no organized-market series; the HQ
    block is firm-floored anyway).

    Why: the static ``IMPORT_TRANCHES_BY_YEAR`` ladder is a per-year constant
    fit, blind to neighbor fundamentals — it caps the modeled seam price at its
    top constant exactly when the real seam repriced with the neighbors (the
    Dec-2024 New-England-complex month, the Jun-2025 heat wave), and its cheap
    constants soften off-peak prices the real seam never saw. The measured
    neighbor LMP is the real delivered opportunity cost of the imported energy
    (rule #12: regenerates for a forward year from the modeled neighbor /
    reference-price formula, responds to changed conditions), read blind to
    NYISO's own flow (rule #11). The monthly EIA-930 reconciliation band, HQ
    firm floor and simultaneous-import limit are untouched.

    Returns ``True`` when at least one row was repriced, ``False`` (byte-
    identical static ladder) for non-NYISO ISOs, a missing import node, or
    missing measured neighbor series (e.g. forecast years).
    """
    from market_sim.data.neighbor_price import neighbor_lmp_hourly

    if iso.upper() != "NYISO":
        return False
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return False
    hours = int(mc.shape[1])
    series: dict[str, np.ndarray] = {}
    for neighbor in sorted(set(_NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR.values())):
        lmp = neighbor_lmp_hourly(neighbor, year, "da")
        if lmp is None:
            lmp = neighbor_lmp_hourly(neighbor, year, "rt")
        if lmp is None or lmp.shape[0] < hours:
            continue
        series[neighbor] = np.asarray(lmp[:hours], dtype=float)
    if not series:
        return False
    # Hourly max (deep-import ceiling) / min (wash-free export willingness-to-
    # pay) over the priced neighbors.
    deep_import = np.maximum.reduce(list(series.values()))
    export_wtp = np.minimum.reduce(list(series.values()))
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if not uid.startswith(f"{zone}_"):
            continue
        tranche = uid[len(zone) + 1 :]
        neighbor = _NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR.get(tranche)
        if neighbor is not None and neighbor in series:
            mc[row, :] = series[neighbor] + NYISO_IMPORT_HUB_HURDLE
            applied = True
        elif tranche == _NYISO_HUB_SCARCITY_TRANCHE:
            mc[row, :] = deep_import + NYISO_IMPORT_HUB_HURDLE
            applied = True
        elif tranche == _NYISO_HUB_EXPORT_TRANCHE:
            mc[row, :] = export_wtp - NYISO_IMPORT_HUB_HURDLE
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
      :data:`~market_sim.config.interchange_config.IMPORT_TRANCHE_EF`), and
    * the single export leg row → ``hub`` (exports owe no CA compliance cost).

    PROBE NOTE (caiso 24 bidir+wheel-only): each import leg is priced at
    ``hub + wheel + border_carbon × (EF / EF_unspecified)`` — the ADDITIVE
    per-tranche OATT point-to-point wheeling charge of
    :data:`~market_sim.config.interchange_config.CAISO_IMPORT_DELIVERY_BASIS`, but NOT its
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

# Net-load band over which the offer collapses (full collapse, s=1, at/below
# the LO percentile; none above HI) now lives in ScenarioConfig as
# caiso_solar_shape_nl_lo_pct / caiso_solar_shape_nl_hi_pct, grounded on the
# duck-curve net-load belly definition rather than an env-overridable tuning
# channel — see the citation there. As a POST-HOC diagnostic only (not the
# band's anchor), the resulting collapse window has historically lined up
# with observed CAISO negative-price hours (~9% of hours, 2024 DA/RT,
# precision ~100% — every modeled negative hour was a real negative hour);
# that check is informative but must never be used to re-tune the percentiles
# (CLAUDE.md rule #23 — no off-registry tuning channels).
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

    with ``nl_hi`` / ``nl_lo`` the ``config.caiso_solar_shape_nl_hi_pct`` /
    ``_nl_lo_pct`` percentiles of the year's net load and ``floor =
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
    nl_hi_pct = float(getattr(config, "caiso_solar_shape_nl_hi_pct", 30.0))
    nl_lo_pct = float(getattr(config, "caiso_solar_shape_nl_lo_pct", 10.0))
    nl_hi = float(np.percentile(nl, nl_hi_pct))
    nl_lo = float(np.percentile(nl, nl_lo_pct))
    if not (nl_hi > nl_lo):
        return False
    s = np.clip((nl_hi - nl) / (nl_hi - nl_lo), 0.0, 1.0)
    floor = -float(config.renewable_keep_running_value)
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


def split_miso_south_external_node(iso_config: ISOConfig) -> ISOConfig:
    """Re-home the MISO-South border link onto its own external zone.

    The shared ``MISO_external`` bus links to all five border zones, so the
    LP can wheel energy South→external→Midwest through the external zone's
    energy balance without touching any priced seam band — a free 3,000 MW
    bypass around the RDT contract path, which is the ONLY real South↔Midwest
    boundary (MISO's footprints are not directly interconnected; MISO/SPP
    JOA). The southern seam's neighbors (SOCO/TVA/AECI —
    ``MISO_SEAM_DIBA["South"]``) are electrically on the *South* side of the
    RDT, so their seam cannot deliver into MISO Midwest. This transform:

    1. appends the zero-load :data:`~market_sim.config.constants.MISO_SOUTH_EXTERNAL_ZONE`,
    2. re-points the ``(MISO_external, MISO-South)`` border link onto it, and
    3. rewrites any interface-limit member pair referencing the old link
       (the ``MISO_simultaneous_import`` SIL keeps its South member).

    The South seam's reference-price bands must be hosted in the new zone by
    :func:`build_reference_price_node` (``zone_overrides``) — wired by
    ``build_interchange_fleet`` off the same ``miso_south_seam_split`` flag.
    Idempotent: a topology already carrying the zone is returned unchanged.

    Raises:
        ValueError: When the topology has no ``(MISO_external, MISO-South)``
            link to re-home (fail loud — never silently skip the fix).
    """
    external = IMPORT_ZONE.get("MISO")
    if MISO_SOUTH_EXTERNAL_ZONE in iso_config.zone_names:
        return iso_config
    new_links: list[TransferLink] = []
    repointed = False
    for ln in iso_config.links:
        pair = (ln.from_zone, ln.to_zone)
        if pair == (external, "MISO-South") or pair == ("MISO-South", external):
            new_links.append(
                ln.model_copy(
                    update={
                        "from_zone": (
                            MISO_SOUTH_EXTERNAL_ZONE
                            if ln.from_zone == external
                            else ln.from_zone
                        ),
                        "to_zone": (
                            MISO_SOUTH_EXTERNAL_ZONE
                            if ln.to_zone == external
                            else ln.to_zone
                        ),
                    }
                )
            )
            repointed = True
        else:
            new_links.append(ln)
    if not repointed:
        raise ValueError(
            "split_miso_south_external_node: no (MISO_external, MISO-South) "
            "border link found — apply after extend_with_import_node"
        )
    new_limits: list[InterfaceLimit] = []
    for lim in iso_config.interface_limits:
        pairs = [tuple(p) for p in lim.links]
        rewritten = [
            (
                tuple(MISO_SOUTH_EXTERNAL_ZONE if z == external else z for z in pair)
                if set(pair) == {external, "MISO-South"}
                else pair
            )
            for pair in pairs
        ]
        new_limits.append(
            lim.model_copy(update={"links": rewritten}) if rewritten != pairs else lim
        )
    extended = iso_config.model_copy(
        update={
            "zones": [
                *iso_config.zones,
                Zone(name=MISO_SOUTH_EXTERNAL_ZONE, iso="MISO", load_share=0.0),
            ],
            "links": new_links,
            "interface_limits": new_limits,
        }
    )
    extended.validate_topology()
    return extended


def apply_miso_rdt_tcdc(iso_config: ISOConfig, rpe_pricing: bool = False) -> ISOConfig:
    """Replace the static RDT pair with the published derate + TCDC tiers.

    The real market does not run the RDT at the JOA contract limits: MISO
    derates the modeled limit to 92% of contract by default (2024 SOM
    §III.B), and flow above the modeled limit is *priced* by the two-step
    RDT Transmission Constraint Demand Curve ($40/MWh at the modeled limit,
    $500/MWh from 102% of it) rather than hard-capped. Each one-way RDT link
    (``Plains→South`` at :data:`~market_sim.config.constants.MISO_RDT_CONTRACT_N_TO_S_MW`,
    ``South→Plains`` at :data:`~market_sim.config.constants.MISO_RDT_CONTRACT_S_TO_N_MW`)
    becomes three parallel one-way tiers:

    * base: ``[0, derate × contract]`` free — the modeled (derated) limit;
    * step 1: width ``(STEP2_START_FRAC − 1) × modeled`` at ``STEP1_PRICE``;
    * step 2: the remainder up to the JOA contract entitlement at
      ``STEP2_PRICE`` (scheduled transfers cannot exceed the contract path).

    The LP's Midwest−South dual separation then reproduces the market's
    price formation: $0 below the modeled limit, ~$40-class while the first
    TCDC step clears, up to $500-class in deep violation — instead of a
    degenerate hard cap at a limit the operators never run to.
    :func:`build_interface_groups` picks up all tiers automatically (every
    link joining a listed zone pair joins the group), so the Plains CIL/CEL
    still reads the net corridor flow. All parameters published
    (``constants.MISO_RDT_*``); zero fitted scalars.

    With ``rpe_pricing`` (``ScenarioConfig.miso_rpe_pricing``), the Reserve
    Procurement Enhancement constraint's single published demand value
    (:data:`~market_sim.config.constants.MISO_RPE_DEMAND_VALUE`, $200/MWh)
    is added to both *violation* tiers — the 2023-2025 market's measured
    pricing, where the RDT TCDC and the RPE demand curve "apply additively"
    whenever the RDT is in real violation, producing $240 spreads in small
    violation ($40 + $200) and $700 in deep violation ($500 + $200)
    (2024 SOM §II.E/§III.B). The free tier below the modeled limit is
    untouched, so the adder engages only in the constraint's own driver
    window (flow above the derated limit). The RPE's STR-scarcity binding
    channel (binding *without* an RDT violation) is deliberately
    unrepresented — the LP carries no STR product — a documented one-way
    under-separation gap.

    Raises:
        ValueError: When either one-way RDT link is missing (fail loud).
    """
    rpe_adder = MISO_RPE_DEMAND_VALUE if rpe_pricing else 0.0
    tiers: list[TransferLink] = []
    new_links: list[TransferLink] = []
    found = set()
    for ln in iso_config.links:
        pair = (ln.from_zone, ln.to_zone)
        if pair == ("MISO-Plains", "MISO-South") and not ln.is_bidirectional:
            contract = MISO_RDT_CONTRACT_N_TO_S_MW
        elif pair == ("MISO-South", "MISO-Plains") and not ln.is_bidirectional:
            contract = MISO_RDT_CONTRACT_S_TO_N_MW
        else:
            new_links.append(ln)
            continue
        found.add(pair)
        modeled = MISO_RDT_DEFAULT_DERATE_FRAC * contract
        step1_top = min(MISO_RDT_TCDC_STEP2_START_FRAC * modeled, contract)
        for ttc, cost in (
            (modeled, 0.0),
            (step1_top - modeled, MISO_RDT_TCDC_STEP1_PRICE + rpe_adder),
            (contract - step1_top, MISO_RDT_TCDC_STEP2_PRICE + rpe_adder),
        ):
            if ttc <= 0.0:
                continue
            tiers.append(ln.model_copy(update={"ttc_mw": ttc, "flow_cost": cost}))
    if len(found) != 2:
        raise ValueError(
            "apply_miso_rdt_tcdc: expected the one-way RDT pair "
            "(MISO-Plains↔MISO-South), found "
            f"{sorted(found) or 'neither'}"
        )
    extended = iso_config.model_copy(update={"links": [*new_links, *tiers]})
    extended.validate_topology()
    return extended


# CAISO SP15-split internal import-limited links (foundation 2026-07-09): the
# one-way pockets whose TTC is upgraded from the static 2023 baked-in value to
# the solve year's measured LCT import_cap (peak_load - requirement) by
# apply_caiso_local_import_limits below. Keyed by the LCT `area` name so it
# reads the same rows as data.local_capacity.load_lcr_parameters.
_CAISO_LOCAL_IMPORT_LINKS: dict[str, tuple[str, str]] = {
    "LA Basin": ("SP15_rest", "LA_BASIN"),
    "San Diego/Imperial Valley": ("SP15_rest", "SDGE"),
}


def apply_caiso_local_import_limits(
    iso_config: ISOConfig, iso: str, year: int
) -> ISOConfig:
    """Swap the SP15-pocket import-link TTCs to the solve year's measured LCT cap.

    The SP15-split foundation (2026-07-09) baked the two internal import-limited
    links (``SP15_rest -> LA_BASIN``, ``SP15_rest -> SDGE``) at the STATIC 2023
    (tightest-year) ``import_cap = peak_load - requirement`` value as the
    scope-sanctioned MVP; per-year was documented there as the deferred end
    state (docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md,
    "Import-cap values"). This is that upgrade: gated on
    ``ScenarioConfig.caiso_per_year_import_caps`` (default off), it replaces
    each link's ``ttc_mw`` with the measured cap for ``year`` from
    :func:`market_sim.data.local_capacity.load_lcr_parameters` — the same
    ``peak_load - requirement`` convention, frozen per rule 24 (never the
    reserve-margin gross-up, never tuned to a residual).

    A no-op (returns ``iso_config`` unchanged) for any ISO but CAISO, or when
    ``year`` has no published LCT row for either area (``load_lcr_parameters``
    omits the area rather than guessing) — the link keeps its static 2023
    baked-in default TTC.

    Args:
        iso_config: CAISO topology carrying the two SP15-split import links.
        iso: Model ISO name.
        year: Solve year (resolves the LCT delivery-year row).

    Returns:
        ``iso_config`` with the matching links' TTC set to the measured value,
        or unchanged.
    """
    if iso.upper() != "CAISO":
        return iso_config
    from market_sim.data.local_capacity import load_lcr_parameters

    params = load_lcr_parameters(iso, year)
    if not params:
        return iso_config
    new_ttc: dict[tuple[str, str], float] = {}
    for area, (from_zone, to_zone) in _CAISO_LOCAL_IMPORT_LINKS.items():
        p = params.get(area)
        if p is not None:
            new_ttc[(from_zone, to_zone)] = float(p["import_cap_mw"])
    if not new_ttc:
        return iso_config
    changed = False
    new_links: list[TransferLink] = []
    for link in iso_config.links:
        cap = new_ttc.get((link.from_zone, link.to_zone))
        if cap is not None and cap != link.ttc_mw:
            new_links.append(link.model_copy(update={"ttc_mw": cap}))
            changed = True
        else:
            new_links.append(link)
    if not changed:
        return iso_config
    extended = iso_config.model_copy(update={"links": new_links})
    extended.validate_topology()
    return extended


# WECC-accepted directional ratings for CAISO's two internal N-S paths
# (WECC Path Rating Catalog, 2024 public version; Tier 1 measured). Each model
# link's symmetric ttc_mw is only ONE direction's rating — Path 15's 5,400 MW
# is its S→N limit and Path 26's 4,000 MW its N→S limit — so the LP's reverse
# directions run up to 65% too loose. Keyed by the model link orientation
# (from_zone, to_zone) = the listed/positive direction of the InterfaceLimit;
# values are (forward_cap_mw, reverse_cap_mw).
CAISO_PATH_DIRECTIONAL_RATINGS: dict[tuple[str, str], tuple[float, float]] = {
    # Path 15 (Midway–Los Banos): N→S 3,265 MW / S→N 5,400 MW.
    ("NP15", "ZP26"): (3265.0, 5400.0),
    # Path 26 (Midway–Vincent): N→S 4,000 MW / S→N 3,000 MW. Keyed on the
    # re-pointed link orientation after the SP15 split (ZP26 → SP15_rest).
    ("ZP26", "SP15_rest"): (4000.0, 3000.0),
}


def apply_caiso_asymmetric_path_limits(iso_config: ISOConfig, config) -> ISOConfig:
    """Cap Path 15 / Path 26 at their WECC directional ratings (CAISO only).

    Gated on ``ScenarioConfig.caiso_asymmetric_path_ratings`` (default off —
    byte-identical no-op for every existing run). When on, appends one
    :class:`InterfaceLimit` per entry of :data:`CAISO_PATH_DIRECTIONAL_RATINGS`
    over that single link, bounding the listed (N→S) direction at
    ``forward_cap_mw`` and the reverse (S→N) at ``reverse_cap_mw``. The
    per-link symmetric ``ttc_mw`` is left untouched (it already equals the
    looser direction's rating), so the effective directional bounds become
    ``min(ttc, forward)`` / ``min(ttc, reverse)`` — the published ratings.

    Replaces a symmetric estimate with the measured directional data (rule 14):
    the tightened S→N Path 26 limit (4,000 → 3,000 MW) is what confines the
    south's midday solar surplus, letting the measured NP15-over-SP15 basis
    form instead of the zones equalizing through a limit the real system does
    not have. A no-op when the ISO carries neither listed link (non-CAISO
    topologies), and idempotent (existing same-named limits are replaced).
    """
    if not getattr(config, "caiso_asymmetric_path_ratings", False):
        return iso_config
    link_pairs = {(ln.from_zone, ln.to_zone) for ln in iso_config.links}
    new_limits = [
        lim
        for lim in iso_config.interface_limits
        if not lim.name.startswith("CAISO_path_directional_")
    ]
    added = 0
    for (from_z, to_z), (fwd_mw, rev_mw) in CAISO_PATH_DIRECTIONAL_RATINGS.items():
        if (from_z, to_z) not in link_pairs and (to_z, from_z) not in link_pairs:
            continue
        new_limits.append(
            InterfaceLimit(
                name=f"CAISO_path_directional_{from_z}_{to_z}",
                links=[(from_z, to_z)],
                cap_mw=fwd_mw,
                reverse_cap_mw=rev_mw,
            )
        )
        added += 1
    if added == 0:
        return iso_config
    extended = iso_config.model_copy(update={"interface_limits": new_limits})
    extended.validate_topology()
    return extended


def build_pjm_external_flow_groups(
    links: list[TransferLink],
    import_cap: np.ndarray,
    export_cap: np.ndarray,
    zone_names: list[str],
) -> list[tuple]:
    """Return per-hour asymmetric flow caps for PJM's external star-node links.

    Breaks the PJM copper-plate (0.000 zonal LMP spread in every hour): the
    priced :data:`~market_sim.config.interchange_config.IMPORT_ZONE` ``PJM_external`` node
    wires ~30 GW of *uncongested* transfer to 5 border zones, so the dear-east
    load pockets import directly from one price hub and never pull power through
    the internal west→east lines — every zone's energy-balance dual ties to one
    price. This caps each ``PJM_external→border`` link's signed flow, per hour, at
    the measured per-border net-interchange envelope
    (:func:`market_sim.data.eia_loader.pjm_zonal_interchange_envelope`): the import
    direction (positive flow, hub→border) at ``import_cap`` and the export
    direction (negative flow, border→hub) at ``export_cap``. Returned as one
    asymmetric interface group per external link — a 4-tuple
    ``(link_idx, import_cap_hourly, bidirectional=False, export_cap_hourly)`` for
    :func:`market_sim.model.dispatch._build_interface_rows` (the same machinery
    the CAISO per-hub corridor caps use). The link keeps its own (looser) static
    TTC as an outer bound; this group binds first.

    With the dominant tie direction (ComEd/AEP/EMAAC export, Dominion import)
    holding a generous high-percentile ceiling and the minor direction collapsed
    toward ~0, the hub can no longer flood the east with cheap imports, so the
    interior dear-east zones must source western power across the internal
    interfaces — opening the congestion the copper-plate suppressed — and the
    over-export shrinks toward the measured schedule.

    Args:
        links: The (already import-node-extended) transfer links; the external
            links are those whose ``from_zone`` is the PJM import zone.
        import_cap: Per-border import ceiling, ``(n_zones, T)`` MW, row order
            matching ``zone_names``.
        export_cap: Per-border export ceiling, ``(n_zones, T)`` MW.
        zone_names: Ordered zone names (the topology's zone set), giving each
            border zone's row in ``import_cap`` / ``export_cap``.

    Returns:
        One 4-tuple interface group per external link, or an empty list when the
        ISO has no external import zone (so the LP is byte-identical off the lever).
    """
    from market_sim.config.interchange_config import IMPORT_ZONE

    ext_zone = IMPORT_ZONE.get("PJM")
    if ext_zone is None:
        return []
    zone_row = {name: i for i, name in enumerate(zone_names)}
    groups: list[tuple] = []
    for li, link in enumerate(links):
        if link.from_zone != ext_zone:
            continue
        row = zone_row.get(link.to_zone)
        if row is None:
            continue
        idx = np.array([li], dtype=int)
        groups.append(
            (
                idx,
                np.asarray(import_cap[row], dtype=float),
                False,
                np.asarray(export_cap[row], dtype=float),
            )
        )
    return groups


#: The model's EMAAC import cut: the two internal links crossing PJM's
#: Manual-03 EASTERN reactive transfer interface boundary at the 8-zone
#: grain (diagnosis §10.3/§10.5 — the interface's monitored EHV set spans
#: both paths; external seam links are NOT part of the interface).
PJM_EAST_CUT_LINKS: tuple[tuple[str, str], ...] = (
    ("PJM_Central_PA", "PJM_EMAAC"),
    ("PJM_SWMAAC", "PJM_EMAAC"),
)


def build_pjm_east_interface_cut_groups(
    links: list[TransferLink],
    limit_hourly: np.ndarray,
) -> list[tuple]:
    """The measured joint EMAAC-import cut (``pjm_east_interface_cut``).

    One ONE-SIDED aggregate interface group capping the summed eastward flow
    across :data:`PJM_EAST_CUT_LINKS` at the hour's measured "Average
    Eastern" limit (PJM's EASTERN reactive transfer interface — the real
    EMAAC import cut, which the per-link
    ``pjm_measured_interface_limits`` overlay applies to Central_PA→EMAAC
    alone while the 5,000 MW SWMAAC→EMAAC static rides in parallel; the real
    interface monitors both paths, so the joint cap is the faithful
    reduced-network reading — diagnosis §10.5, zero fitted scalars). A link
    oriented opposite the cut (EMAAC→X) enters with sign −1 so the group
    reads net eastward flow. One-sided (``bidirectional=False``): an import
    security limit never caps the reverse (westward) direction, which keeps
    the per-link TTCs.

    Args:
        links: The topology's transfer links (pre- or post- import-node
            extension — matching is by zone pair).
        limit_hourly: ``(T,)`` measured hourly cap from
            :func:`market_sim.data.transfer_interface_limits.pjm_eastern_interface_hourly`.

    Returns:
        A single-element list of 5-tuples ``(link_idx, cap_hourly, False,
        None, signs)`` for :func:`market_sim.model.dispatch._build_interface_rows`,
        or an empty list when neither cut link exists in the topology (the LP
        is then byte-identical).
    """
    idx: list[int] = []
    signs: list[float] = []
    for a, b in PJM_EAST_CUT_LINKS:
        for li, link in enumerate(links):
            if (link.from_zone, link.to_zone) == (a, b):
                idx.append(li)
                signs.append(1.0)
            elif (link.from_zone, link.to_zone) == (b, a):
                idx.append(li)
                signs.append(-1.0)
    if not idx:
        return []
    return [
        (
            np.array(idx, dtype=int),
            np.asarray(limit_hourly, dtype=float),
            False,
            None,
            np.array(signs, dtype=float),
        )
    ]


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


def inject_miso_seam_flow_limit(
    fleet_arrays,
    iso: str,
    year: int,
    percentile: float | None = None,
    direction: str = "import",
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

    With ``direction="export"`` this instead caps each seam's net *export* at the
    measured net-export envelope (:func:`~market_sim.data.eia_loader
    .measured_seam_import_envelope` with ``direction="export"``) — the exact
    symmetric mirror of the import availability derate. The seam's export bands
    are negative-output sinks bounded ``[pmin=-step, 0]``; raising their lower
    bound (``FleetArrays.min_gen``) toward 0 caps the deliverable net export. The
    eastern PJM seam (which MISO reliably net-*imports* over) clips export to ~0,
    removing the LP's spurious export of cheap MISO coal back over the PJM border;
    the southern (TVA) and SPP seams keep their measured ~GW of export headroom.
    Composed with any existing ``min_gen`` floor via ``maximum`` (the cap can only
    reduce export, never force it); the export bands keep their priced economics
    and clear the merit order below the cap. Modifies ``fleet_arrays`` in place.

    Returns ``True`` when at least one seam was capped, ``False`` when no
    reference-price bands (of the requested direction) are present or no measured
    envelope is available (forecast year / unmapped ISO), leaving the seam
    unchanged (byte-identical).
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    from market_sim.data.eia_loader import measured_seam_import_envelope

    hours = int(fleet_arrays.availability.shape[1])
    env = measured_seam_import_envelope(
        iso, year, hours, percentile, direction=direction
    )
    if not env:
        return False
    mark = _REF_IMPORT_MARK if direction == "import" else _REF_EXPORT_MARK
    if direction == "export" and fleet_arrays.min_gen is None:
        # Export rows take their lower bound from min_gen; broadcast pmin first so
        # every other row keeps its natural bound (byte-identical elsewhere).
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()
    applied = False
    for name, cap in env.items():
        # Bands of this neighbor: uid is "<zone>_ref{imp,exp}_<name>#k".
        rows = [
            r
            for r, uid in enumerate(fleet_arrays.unit_ids)
            if mark in uid and uid.rsplit(mark, 1)[1].partition("#")[0] == name
        ]
        if not rows:
            continue
        cap = np.asarray(cap, dtype=float)
        if direction == "import":
            total = float(fleet_arrays.pmax[rows].sum())  # = interface_limit_mw
            if total <= 0.0:
                continue
            # Uniform per-band derate so the seam's summed import availability ≤
            # cap each hour; the bands keep their rising (flow-responsive) prices,
            # so the LP still fills the cheapest first below the ceiling.
            frac = np.clip(cap / total, 0.0, 1.0)
            for r in rows:
                fleet_arrays.availability[r, :] *= frac
            applied = True
        else:
            total = -float(fleet_arrays.pmin[rows].sum())  # = interface_limit_mw
            if total <= 0.0:
                continue
            # Uniform per-band lower-bound raise so the seam's summed max export ≤
            # cap each hour. pmin[r] < 0; pmin[r] × frac ∈ [pmin[r], 0] raises the
            # bound toward 0 as the cap tightens, and maximum() composes with any
            # existing floor (the cap only reduces export, never forces it).
            frac = np.clip(cap / total, 0.0, 1.0)
            for r in rows:
                capped = float(fleet_arrays.pmin[r]) * frac
                np.maximum(
                    fleet_arrays.min_gen[r, :], capped, out=fleet_arrays.min_gen[r, :]
                )
            applied = True
    return applied


def inject_pjm_seam_flow_limit(
    fleet_arrays,
    iso: str,
    year: int,
    zone_names: list[str],
    hours: int,
    percentile: float | None = None,
    direction: str = "import",
) -> bool:
    """Cap each PJM reference-price seam's import/export bands at the measured envelope.

    The PJM analogue of :func:`inject_miso_seam_flow_limit`. PJM's five
    reference-price seams (MISO / NYISO / Carolinas / TVA / LGEE, defined in
    :data:`~market_sim.config.interchange_config.INTERFACE_NEIGHBORS`) export at
    full TTC on all five seams simultaneously (~16.3 GW), producing ~38 TWh net
    export in every year regardless of actuals (2023=40, 2024=33, 2025=18 TWh).

    This caps each neighbor's import/export bands at the measured per-neighbor
    deliverability envelope built from :func:`~market_sim.data.eia_loader
    .pjm_zonal_interchange_envelope` (the PJM tie-line file, attributed to
    border zones then summed to neighbor level via each neighbor's
    ``border_zones``). The mechanism is identical to the MISO function:
    import caps scale ``availability``; export caps raise ``min_gen``.

    Returns ``True`` when at least one seam was capped.
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    if iso.upper() != "PJM":
        return False
    from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import pjm_zonal_interchange_envelope

    pct = PJM_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)
    env = pjm_zonal_interchange_envelope(year, zone_names, hours, pct)
    if env is None:
        return False
    import_cap, export_cap = env
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    neighbors = INTERFACE_NEIGHBORS.get("PJM", [])
    if not neighbors:
        return False

    mark = _REF_IMPORT_MARK if direction == "import" else _REF_EXPORT_MARK
    if direction == "export" and fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()

    applied = False
    for neighbor in neighbors:
        rows = [
            r
            for r, uid in enumerate(fleet_arrays.unit_ids)
            if mark in uid and uid.rsplit(mark, 1)[1].partition("#")[0] == neighbor.name
        ]
        if not rows:
            continue
        # Sum the envelope across the neighbor's border zones.
        cap_data = export_cap if direction == "export" else import_cap
        border_rows = [zone_idx[z] for z in neighbor.border_zones if z in zone_idx]
        if not border_rows:
            continue
        cap = np.clip(cap_data[border_rows].sum(axis=0), 0.0, None)

        if direction == "import":
            total = float(fleet_arrays.pmax[rows].sum())
            if total <= 0.0:
                continue
            frac = np.clip(cap / total, 0.0, 1.0)
            for r in rows:
                fleet_arrays.availability[r, :] *= frac
            applied = True
        else:
            total = -float(fleet_arrays.pmin[rows].sum())
            if total <= 0.0:
                continue
            frac = np.clip(cap / total, 0.0, 1.0)
            for r in rows:
                capped = float(fleet_arrays.pmin[r]) * frac
                np.maximum(
                    fleet_arrays.min_gen[r, :], capped, out=fleet_arrays.min_gen[r, :]
                )
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
    mech = ensure_mechanism(fleet_arrays)
    order = gas_rows[np.argsort(fleet_arrays.heat_rate[gas_rows], kind="stable")]
    remaining = target.copy()
    for r in order:
        cap = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap)
        raised = fleet_arrays.min_gen[r, :] < take
        np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
        mech[r, raised] = MECH_CAISO_GAS_COMMITMENT_FLOOR
        remaining = remaining - take
    return True


# Winter cold-snap peak hours (morning HB6-9 + evening HB17-20) — the gas-system
# stress windows the oil/coal/steam reliability fleet covers; an explicit tuple
# of local hours-of-day (two disjoint ranges, not a single [start,end] band).
NEISO_COLDSNAP_FLOOR_HOURS: tuple[int, ...] = (6, 7, 8, 9, 17, 18, 19, 20)


def _distribute_group_floor(
    fleet_arrays,
    rows,
    frac: np.ndarray,
    hours: int,
    mech_id: int = MECH_RELIABILITY_FLOOR,
) -> None:
    """Floor a plant-group fleet at ``frac`` x available capacity, cheapest-first.

    Shared kernel for :func:`inject_reliability_floor`: sizes the hourly group
    target as ``frac`` x the group's available capacity and distributes it over
    the group's units cheapest-first (by heat rate), each capped at its available
    capacity, composing with any existing ``FleetArrays.min_gen`` floor via
    ``maximum``. ``mech_id`` tags the raised unit-hours for the D-2
    forced-energy attribution (data.floor_mechanisms).
    """
    avail_cap = fleet_arrays.pmax[rows, np.newaxis] * fleet_arrays.availability[rows, :]
    target = frac * avail_cap.sum(axis=0)
    if fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()
    mech = ensure_mechanism(fleet_arrays)
    order = rows[np.argsort(fleet_arrays.heat_rate[rows], kind="stable")]
    remaining = target.copy()
    for r in order:
        cap_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
        take = np.minimum(remaining, cap_r)
        raised = fleet_arrays.min_gen[r, :] < take
        np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
        mech[r, raised] = mech_id
        remaining = remaining - take


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


# ---------------------------------------------------------------------------
# Generic registry-driven reliability-floor engine
# ---------------------------------------------------------------------------


def _bridge_flagged_runs(flagged: np.ndarray, min_event_hours: int) -> np.ndarray:
    """Extend/merge a boolean hour mask so each flagged run spans ≥ min_event_hours.

    Steam units committed for a temperature event stay online for a minimum run,
    so an isolated flagged calendar day (24 flagged hours) extends forward to
    ``min_event_hours`` and bridges into the next flagged day, merging adjacent
    runs separated by a sub-event gap. Returns a new mask (input unchanged).
    """
    out = np.asarray(flagged, dtype=bool).copy()
    if not out.any() or min_event_hours <= 24:
        return out
    n = out.size
    padded = np.concatenate(([0], out.astype(np.int8), [0]))
    diff = np.diff(padded)
    starts = np.flatnonzero(diff == 1)
    ends = np.flatnonzero(diff == -1)  # exclusive end index into `out`
    for s, e in zip(starts, ends):
        out[s : min(s + min_event_hours, n)] = True
    return out


def inject_reliability_floor(
    fleet_arrays,
    iso: str,
    year: int,
    specs: list,
    zone_names: list[str],
    *,
    demand: np.ndarray | None = None,
    wind_cf: np.ndarray | None = None,
    wind_cap: np.ndarray | None = None,
    solar_cf: np.ndarray | None = None,
    solar_cap: np.ndarray | None = None,
) -> bool:
    """Apply temperature / net-load reliability-commitment floors from limb specs.

    The single ISO-agnostic floor engine. Each
    :class:`~market_sim.config.iso_configs.ReliabilityFloorSpec` in *specs* is one
    ``(zone, plant_class, driver)`` limb. For each ENABLED limb:

    1. Load the zone's daily weather via
       :func:`~market_sim.data.eia_loader.iso_zone_tmax` (already broadcast to the
       hourly horizon, constant within each calendar day).
    2. Build the day gate and optional sub-daily window:
       ``driver="tmax"`` → flag every hour of a day with ``tmax_c > threshold``;
       ``driver="tmin"`` → ``tmin_c < threshold``;
       ``driver="netload"`` → day's peak net-load (GW) > threshold.
       When ``start_hour``/``end_hour`` are set, only those hours-of-day bind.
    3. For steam classes (``min_event_hours > 24``) bridge an isolated flagged
       day to adjacent flagged days so a committed boiler spans a multi-day event.
    4. Set ``frac = floor_pct`` on flagged hours (0 elsewhere) and select rows
       ``plant_group == plant_class & zone_idx == zone & pmax > 0``.
    5. Distribute the floor into ``FleetArrays.min_gen`` via
       :func:`_distribute_group_floor` (cheapest-first) or pro-rata, composing
       with any existing floor through ``maximum``.

    ``floor_pct`` is ``commit_frac × min_stable_pct`` — a structural commitment
    share times the class's physical minimum-stable level, derived from the
    temperature→commitment relationship only and never tuned to a price/volume
    residual (CLAUDE.md #9/#11; plan §B.3).

    For ``driver="netload"`` limbs the per-zone net-load is computed from exogenous
    scenario drivers — zonal demand MINUS available VRE (wind_cf × wind_cap +
    solar_cf × solar_cap) — NOT endogenous dispatch (avoids circularity). A day is
    flagged when its peak net-load (GW) exceeds the limb threshold; on a flagged
    day the floor binds for all 24 h (same full-day gate as temperature limbs).
    Net-load limbs are skipped when the exogenous inputs are not supplied.

    Enabled limbs sharing a non-empty ``ramp_group`` are instead read as the
    ``(threshold, floor_pct)`` knots of one continuous piecewise-linear
    commitment curve: the floor is interpolated in the driver temperature between
    the knots (clamped flat outside their range) and applied every hour in the
    window, reproducing the legacy ``clip(base + slope×(T−T0), base, cap)`` ramp
    instead of a single step that over-fires on every warm day. Ramp families
    support only the ``tmax``/``tmin`` drivers (see :class:`ReliabilityFloorSpec`).

    Modifies *fleet_arrays* in place. Returns ``True`` iff any enabled limb
    floored at least one unit, ``False`` (byte-identical) otherwise.
    """
    if fleet_arrays.plant_group is None:
        return False
    from market_sim.data.eia_loader import iso_zone_tmax

    groups = np.asarray(fleet_arrays.plant_group)
    hours = int(fleet_arrays.availability.shape[1])
    applied = False

    def _zone_index(zone: str) -> int | None:
        return next((i for i, z in enumerate(zone_names) if z == zone), None)

    def _apply_frac(spec, z_idx: int, frac: np.ndarray) -> bool:
        """Distribute an hourly ``frac`` floor into ``min_gen`` for one limb.

        Selects the ``(plant_class, zone)`` fleet and composes ``frac × available
        capacity`` into ``FleetArrays.min_gen`` cheapest-first or pro-rata.
        Returns ``True`` iff at least one unit was floored.
        """
        if not np.any(frac > 0.0):
            return False
        sel = (
            (groups == spec.plant_class)
            & (fleet_arrays.zone_idx == z_idx)
            & (fleet_arrays.pmax > 0.0)
        )
        rows = np.flatnonzero(sel)
        if rows.size == 0:
            return False
        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis],
                (fleet_arrays.pmin.size, hours),
            ).copy()
        if spec.distribution == "cheapest_first":
            _distribute_group_floor(
                fleet_arrays, rows, frac, hours, mech_id=MECH_RELIABILITY_FLOOR
            )
        else:  # pro_rata: each unit floored at frac x its own available capacity
            mech = ensure_mechanism(fleet_arrays)
            for r in rows:
                avail_r = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
                target = frac * avail_r
                raised = fleet_arrays.min_gen[r, :] < target
                np.maximum(
                    fleet_arrays.min_gen[r, :],
                    target,
                    out=fleet_arrays.min_gen[r, :],
                )
                mech[r, raised] = MECH_RELIABILITY_FLOOR
        return True

    # System net-load (demand minus VRE, summed across zones) is computed once
    # and cached here for "netload" limbs, which key off ISO-wide tightness.
    _system_net_load: np.ndarray | None = None
    _have_netload_inputs = (
        demand is not None
        and wind_cf is not None
        and wind_cap is not None
        and solar_cf is not None
        and solar_cap is not None
    )

    # Partition enabled limbs into continuous-ramp families (shared, non-empty
    # ``ramp_group``) and standalone step limbs. A ramp family interpolates its
    # ``(threshold, floor_pct)`` knots into one piecewise-linear commitment curve
    # (see ReliabilityFloorSpec) rather than firing each knot as an independent
    # step; standalone limbs keep the original step-gate semantics below.
    ramp_families: dict[str, list] = {}
    standalone: list = []
    for spec in specs:
        if not getattr(spec, "enabled", True):
            continue
        rg = getattr(spec, "ramp_group", None)
        if rg:
            ramp_families.setdefault(rg, []).append(spec)
        else:
            standalone.append(spec)

    for rg, knots in ramp_families.items():
        head = knots[0]
        if head.driver not in ("tmax", "tmin"):
            continue  # ramps are temperature-only
        z_idx = _zone_index(head.zone)
        if z_idx is None:
            continue
        temp_result = iso_zone_tmax(iso, year, hours, zone=head.zone)
        if temp_result is None:
            continue  # no pinned weather (forecast year / unmapped) → no-op
        tmax, tmin = temp_result
        series = tmax if head.driver == "tmax" else tmin
        if series is None:
            continue
        series = np.asarray(series, dtype=float)
        # np.interp needs strictly-increasing thresholds; ys need not be monotone,
        # so tmin ramps (colder → higher floor) work by encoding descending ys.
        order = np.argsort([k.threshold for k in knots], kind="stable")
        xs = np.array([knots[i].threshold for i in order], dtype=float)
        ys = np.array([knots[i].floor_pct for i in order], dtype=float)
        floor_series = np.interp(series, xs, ys)  # clamps flat outside [xs0, xs-1]
        sh, eh = head.start_hour, head.end_hour
        if sh is not None and eh is not None:
            hod = np.arange(hours) % 24
            floor_series = np.where((hod >= sh) & (hod <= eh), floor_series, 0.0)
        if _apply_frac(head, z_idx, floor_series):
            applied = True

    for spec in standalone:
        z_idx = _zone_index(spec.zone)
        if z_idx is None:
            continue

        driver = spec.driver
        if driver in ("tmax", "tmin"):
            temp_result = iso_zone_tmax(iso, year, hours, zone=spec.zone)
            if temp_result is None:
                continue  # no pinned weather (forecast year / unmapped) → no-op
            tmax, tmin = temp_result
            series = tmax if driver == "tmax" else tmin
            if series is None:
                continue
            series = np.asarray(series, dtype=float)
            if driver == "tmax":
                flagged = series > spec.threshold
            else:
                flagged = series < spec.threshold
        elif driver == "netload":
            if not _have_netload_inputs:
                continue
            # System net-load = sum of (zonal demand - zonal VRE) across all
            # zones. CT commitment is an ISO-level reserve-tightness decision
            # (the system duck-curve neck), so the threshold (GW) is on the
            # system scale — matching the derive-script regression against
            # EIA-930 CISO system demand minus wind minus solar.
            if _system_net_load is None:
                _system_net_load = (
                    demand[:, :hours].sum(axis=0)
                    - (wind_cap[:, None] * wind_cf[:, :hours]).sum(axis=0)
                    - (solar_cap[:, None] * solar_cf[:, :hours]).sum(axis=0)
                )
            n_days = hours // 24
            daily_peak_gw = np.array(
                [
                    _system_net_load[d * 24 : (d + 1) * 24].max() / 1000.0
                    for d in range(n_days)
                ]
            )
            # Basis-consistent threshold: when the CSV carries the derivation
            # percentile, recompute the GW threshold from the engine's own
            # net-load so the flagged-day count tracks model inputs, not the
            # EIA-930 basis the derivation script used.
            threshold_gw = spec.threshold
            tp = getattr(spec, "threshold_percentile", None)
            if tp is not None:
                threshold_gw = float(np.percentile(daily_peak_gw, tp))
            day_flagged = daily_peak_gw > threshold_gw
            flagged = np.repeat(day_flagged, 24)[:hours]
        else:
            continue

        if not np.any(flagged):
            continue

        # Steam event bridging: a committed boiler stays online across a multi-day
        # event, so extend/merge flagged runs to at least min_event_hours.
        if int(getattr(spec, "min_event_hours", 24)) > 24:
            flagged = _bridge_flagged_runs(flagged, int(spec.min_event_hours))

        # Sub-daily hour-of-day window: restrict the floor to start_hour..end_hour.
        sh = getattr(spec, "start_hour", None)
        eh = getattr(spec, "end_hour", None)
        if sh is not None and eh is not None:
            hod = np.arange(hours) % 24
            flagged = flagged & (hod >= sh) & (hod <= eh)

        frac = np.where(flagged, float(spec.floor_pct), 0.0)
        if _apply_frac(spec, z_idx, frac):
            applied = True

    return applied


# Afternoon-evening peak window (local HB14-21, inclusive) the Long Island local
# self-supply floor is restricted to — the SAME downstate summer design-cooling
# window the CT/ST temperature reliability ramps use (start_hour=14/end_hour=21 in
# reliability_floor_coeffs_NYISO.csv). Rule-17/rule-18 narrowing (floor-rederive
# 2026-07-05): the LI locational-reliability / cable-import constraint the floor
# proxies physically binds only at the afternoon-evening AC peak — the condition
# the LCR locality requirements are defined at (NYISO Locality Bulk-Power
# Transmission Capability reports, design cooling day) — and is inactive
# overnight, where measured LI net import runs well below its cable ceiling
# (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md Finding 4: LI inflow
# max 2,480 MW vs ~2,850 MW ceiling, 0 h > 90%) and measured LI CT_PEAKER CF is
# ~0.06 flat. Applied all-hours the floor force-committed in-pocket LM6000 baseload
# overnight (D-2: nyiso_local_selfsupply forced 1.84/2.87/1.86 TWh of CT_PEAKER,
# 43/65/42% of the class; C7 off-peak diurnal FAIL). This is a HOURS narrowing of
# an existing floor, NOT a re-level of its (residual-identified, issue #1345) 0.45
# fraction — the level stays untouched; only the overnight hours it had no driver
# for are removed.
NYISO_SELFSUPPLY_FLOOR_HOURS: tuple[int, ...] = tuple(range(14, 22))  # HB14-21


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


def apply_nyiso_li_tsl_import_cap(
    ttc: np.ndarray,
    iso_config,
    iso: str,
    year: int,
    hours: int,
) -> np.ndarray:
    """Cap the NYC->Long_Island link at the published Zone-K locality import
    limit during the peak window (issue #1345, ``config.nyiso_li_lcr_tsl``).

    The published NYISO Locality Bulk-Power Transmission Capability import
    limit for Long Island (``data/raw/capacity-deliverability/nyiso/nyiso.csv``:
    325 / 275 / 275 MW for the 2023/24-2025/26 capability years) is the
    transmission-security boundary the Zone-K LCR is derived against — the AC
    import LI may count on at the summer design-cooling peak, with the
    UDR-backed external cables (the priced-import-node links, ~1.2 GW) counted
    separately. Mapping it to hourly dispatch terms (the rule-14
    reconciliation, documented in the ``nyiso_li_lcr_tsl`` ScenarioConfig
    comment): the limit is applied ONLY inside the design-condition window
    (:data:`NYISO_SELFSUPPLY_FLOOR_HOURS`, HB14-21 — the same window and driver
    document the PR-#1442-narrowed self-supply floor used), where it replaces
    the link's physical 1,650 MW rating; every other hour keeps the physical
    rating (measured LI off-peak imports run well below the cable ceiling and
    the security constraint's driver is inactive). Applied all-hours the
    peak-condition boundary would force ~16 TWh/yr of LI energy vs the
    ~8.5 TWh physically real — the boundary mismatch issue #1345 documents.

    In-window LI supply beyond (external ties + the security-limited AC
    import) then clears from the in-zone fleet ECONOMICALLY — this function is
    the replacement for the Long_Island 0.45 self-supply ``min_gen`` floor
    (``inject_nyiso_local_selfsupply``; the caller must exclude Long_Island
    there when this cap is active — one mechanism per phenomenon, rule 19),
    so the LI reliability energy stops being floor-forced (rule-20 D-2
    budget) and becomes merit-order dispatch behind a published limit.

    The cap is symmetric on the AC link in-window (the LP's bidirectional
    bound); measured LI peak-window exports toward NYC are ~0 MW, a
    documented, immaterial misalignment accepted over one-way link plumbing.

    Args:
        ttc: ``(n_links,)`` static or ``(hours, n_links)`` per-hour transfer
            capabilities (MW).
        iso_config: ISO topology (``links`` searched for NYC->Long_Island).
        iso: ISO identifier; every ISO but ``"NYISO"`` returns ``ttc``
            unchanged.
        year: Backcast/solve calendar year (resolves the capability-year row).
        hours: LP horizon length T.

    Returns:
        ``(hours, n_links)`` per-hour TTC matrix with the in-window LI cap
        applied (a copy), or ``ttc`` unchanged for non-NYISO.

    Raises:
        ValueError: NYISO without a published Long Island import limit for the
            resolved capability year, or no NYC->Long_Island link — the
            mechanism must never silently no-op when explicitly enabled.
    """
    if iso != "NYISO":
        return ttc

    from market_sim.data.capacity_deliverability import (
        import_limit_by_area,
        resolve_delivery_year,
    )

    delivery_year = resolve_delivery_year(iso, int(year))
    limits = import_limit_by_area(iso, delivery_year)
    tsl = limits.get("Long Island")
    if tsl is None:
        raise ValueError(
            f"nyiso_li_lcr_tsl=True but no published Long Island import limit "
            f"for delivery year {delivery_year} in the capacity-deliverability "
            f"table (data/raw/capacity-deliverability/nyiso/nyiso.csv); "
            f"available areas: {sorted(limits)}"
        )

    li_idx = [
        i
        for i, ln in enumerate(iso_config.links)
        if (ln.from_zone, ln.to_zone) == ("NYC", "Long_Island")
    ]
    if not li_idx:
        raise ValueError(
            "nyiso_li_lcr_tsl=True but the NYISO topology has no "
            "NYC->Long_Island link to cap."
        )

    ttc_arr = np.asarray(ttc, dtype=float)
    if ttc_arr.ndim == 1:
        ttc_t = np.broadcast_to(ttc_arr, (int(hours), ttc_arr.shape[0])).copy()
    else:
        ttc_t = ttc_arr.copy()
    hod = np.arange(int(hours)) % 24
    in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
    for i in li_idx:
        ttc_t[in_window, i] = np.minimum(ttc_t[in_window, i], float(tsl))
    return ttc_t


def apply_nyiso_nyc_tsl_import_cap(
    ttc: np.ndarray,
    iso_config,
    iso: str,
    year: int,
    hours: int,
) -> np.ndarray:
    """Cap the Lower_Hudson->NYC link at the published NYC (Zone-J) locality
    import limit during the peak window (nyiso-61, ``config.nyiso_nyc_lcr_tsl``).

    The Zone-J analog of :func:`apply_nyiso_li_tsl_import_cap`. The published
    NYISO NYC-locality Bulk-Power Transmission Capability import limit
    (``data/raw/capacity-deliverability/nyiso/nyiso.csv``: 2,875 MW for every
    capability year 2023/24-2025/26) is the transmission-security boundary the
    NYC LCR is derived against — the AC import NYC may count on at the summer
    design-cooling peak. It REPLACES the Lower_Hudson->NYC (Dunwoodie-South)
    link's 3,900 MW energy-TTC estimate (iso_configs.py Gold-Book seed) inside
    the design-condition window (:data:`NYISO_SELFSUPPLY_FLOOR_HOURS`, HB14-21 —
    the same window and driver document the LI cap uses); every other hour keeps
    the physical 3,900 MW rating (measured off-peak NYC imports run below the
    interface ceiling and the security constraint's driver is inactive).

    RULE-14 boundary (clean, parallel to the LI cap): the 2,875 MW is the
    AC-import transmission-security limit; the controllable HVDC ties into
    Zone J (Neptune / HTP / Linden-VFT) are counted SEPARATELY as the priced
    import-node link (``interchange_config.IMPORT_NODE_LINKS["NYISO"]``
    ``("NYC", 1000.0)``), which stays at its physical rating — so this caps
    ONLY the Dunwoodie-South AC link, not total NYC import. In-window NYC supply
    beyond (external HVDC ties + the security-limited AC import) then clears
    from the in-city fleet ECONOMICALLY, letting the dear Zone-J gas set price
    at the summer peak (the identified 2024/2025 deep-tail lever). This is a
    transmission limit, not a ``min_gen`` floor — it forces no energy (the D-2
    budget is unchanged).

    The cap is symmetric on the AC link in-window (the LP's bidirectional
    bound); measured NYC peak-window exports toward Lower_Hudson are ~0 MW, a
    documented, immaterial misalignment accepted over one-way link plumbing.

    Args:
        ttc: ``(n_links,)`` static or ``(hours, n_links)`` per-hour transfer
            capabilities (MW).
        iso_config: ISO topology (``links`` searched for Lower_Hudson->NYC).
        iso: ISO identifier; every ISO but ``"NYISO"`` returns ``ttc``
            unchanged.
        year: Backcast/solve calendar year (resolves the capability-year row).
        hours: LP horizon length T.

    Returns:
        ``(hours, n_links)`` per-hour TTC matrix with the in-window NYC cap
        applied (a copy), or ``ttc`` unchanged for non-NYISO.

    Raises:
        ValueError: NYISO without a published NYC import limit for the resolved
            capability year, or no Lower_Hudson->NYC link — the mechanism must
            never silently no-op when explicitly enabled.
    """
    if iso != "NYISO":
        return ttc

    from market_sim.data.capacity_deliverability import (
        import_limit_by_area,
        resolve_delivery_year,
    )

    delivery_year = resolve_delivery_year(iso, int(year))
    limits = import_limit_by_area(iso, delivery_year)
    tsl = limits.get("NYC")
    if tsl is None:
        raise ValueError(
            f"nyiso_nyc_lcr_tsl=True but no published NYC import limit "
            f"for delivery year {delivery_year} in the capacity-deliverability "
            f"table (data/raw/capacity-deliverability/nyiso/nyiso.csv); "
            f"available areas: {sorted(limits)}"
        )

    nyc_idx = [
        i
        for i, ln in enumerate(iso_config.links)
        if (ln.from_zone, ln.to_zone) == ("Lower_Hudson", "NYC")
    ]
    if not nyc_idx:
        raise ValueError(
            "nyiso_nyc_lcr_tsl=True but the NYISO topology has no "
            "Lower_Hudson->NYC link to cap."
        )

    ttc_arr = np.asarray(ttc, dtype=float)
    if ttc_arr.ndim == 1:
        ttc_t = np.broadcast_to(ttc_arr, (int(hours), ttc_arr.shape[0])).copy()
    else:
        ttc_t = ttc_arr.copy()
    hod = np.arange(int(hours)) % 24
    in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
    for i in nyc_idx:
        ttc_t[in_window, i] = np.minimum(ttc_t[in_window, i], float(tsl))
    return ttc_t


def inject_nyiso_local_selfsupply(
    fleet_arrays,
    iso: str,
    demand: np.ndarray,
    zone_names: list[str],
    exclude_zones: frozenset[str] = frozenset(),
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
    in-zone target is ``frac × demand[zone, t]`` **restricted to the
    afternoon-evening peak window** (:data:`NYISO_SELFSUPPLY_FLOOR_HOURS`, local
    HB14-21) and zero outside it, distributed over the zone's dispatchable
    thermal generators in **marginal-cost merit order** (gas-capable tranches
    first by heat rate, the dear oil-fired peakers last) and each capped at its
    available capacity — the same hour-varying ``FleetArrays.min_gen`` lower
    bound the CHP / CT reliability floors use, and composed with any floor
    already present via ``maximum``. The target is clipped to the zone fleet's
    available capacity each hour so a feasible LP solution always exists (the
    floor can never manufacture unmet load).

    The **window narrowing** (rule-17/18, floor-rederive 2026-07-05): the LI
    locational-reliability / cable-import constraint the floor proxies binds only
    at the summer design-cooling peak (the condition the LCR locality
    requirements are defined at), not overnight — applied all-hours the floor
    force-committed in-pocket LM6000 peaker baseload where measured LI CT_PEAKER
    CF is ~0.06 flat and LI imports run well below their cable ceiling (the D-2
    off-window forcing / C7 diurnal FAIL). The 0.45 fraction itself
    (residual-identified, issue #1345) is **unchanged** — this narrows only the
    hours it binds, never its level.

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
        exclude_zones: Pocket zones whose floor entry is skipped because a
            replacement mechanism owns them this run (rule 19 — one mechanism
            per phenomenon): the ``nyiso_li_lcr_tsl`` Zone-K LCR/TSL import
            cap (issue #1345, :func:`apply_nyiso_li_tsl_import_cap`) excludes
            ``Long_Island`` so the published-limit cap and the 0.45 energy
            floor are never stacked. Empty (the default) is byte-identical.

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
        if zone in exclude_zones:
            continue
        if frac <= 0.0 or zone not in zone_to_idx:
            continue
        z_idx = zone_to_idx[zone]
        in_zone = (fleet_arrays.zone_idx == z_idx) & is_thermal
        rows = np.flatnonzero(in_zone & (fleet_arrays.pmax > 0.0))
        if rows.size == 0:
            continue

        target = frac * demand[z_idx, :hours]
        # Restrict the floor to the afternoon-evening peak window
        # (NYISO_SELFSUPPLY_FLOOR_HOURS): the LI local-reliability / cable-import
        # constraint the floor proxies binds only at the summer design-cooling
        # peak, not overnight (rule-17/18 narrowing — see the constant's note).
        hod = np.arange(hours) % 24
        in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
        target = np.where(in_window, target, 0.0)
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
        mech = ensure_mechanism(fleet_arrays)
        for r in order:
            cap = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
            take = np.minimum(remaining, cap)
            raised = fleet_arrays.min_gen[r, :] < take
            np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
            mech[r, raised] = MECH_NYISO_SELFSUPPLY
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
    :data:`~market_sim.config.interchange_config.NYISO_FIRM_IMPORT_FLOOR_FRAC`, this sets
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
            raised = fleet_arrays.min_gen[r, :] < floor
            np.maximum(
                fleet_arrays.min_gen[r, :], floor, out=fleet_arrays.min_gen[r, :]
            )
            ensure_mechanism(fleet_arrays)[r, raised] = MECH_FIRM_IMPORT
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
    """Return Manitoba Hydro's firm-hydro import block for MISO-West.

    Manitoba Hydro is MISO's single largest import source and the structural
    reason MISO is a net IMPORTER: it sells ~10-15 TWh/yr of FIRM contracted
    hydro into MISO-West over the Manitoba<->US HVDC / 500 kV ties. This import
    sits OUTSIDE the gas-margin reference-price seam
    (:data:`~market_sim.config.interchange_config.INTERFACE_NEIGHBORS`): firm hydro has no
    gas x heat-rate price analogue, so it is a SEPARATE block priced as firm
    hydro — a low, near-constant energy offer reflecting the contract.

    The block is a single ``fuel_type="import"`` pseudo-generator landed directly
    in :data:`~market_sim.config.interchange_config.MISO_MANITOBA_FIRM_IMPORT_ZONE`
    (``MISO-West``, the model zone the ties physically enter), bounded
    ``[0, pmax]`` and offered at
    :data:`~market_sim.config.interchange_config.MISO_MANITOBA_FIRM_IMPORT_OFFER`. Because
    its ``fuel_type`` is ``"import"`` it is counted as net interchange (not
    in-state generation), and its must-flow firm floor is applied post-assembly
    by :func:`inject_miso_firm_imports`.

    The block capacity ``pmax`` is forecast-native — the flat contract midpoint
    :data:`~market_sim.config.interchange_config.MISO_MANITOBA_FIRM_IMPORT_MW` — for any
    forecast year, and in BACKCAST mode is overlaid with the measured per-year
    firm-hydro delivery
    (:data:`~market_sim.config.interchange_config.MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR`,
    drought-responsive) via
    :func:`~market_sim.config.interchange_config.resolve_miso_manitoba_firm_import_mw`.
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

    The Manitoba contract is firm must-flow energy: it flows into MISO-West
    every hour regardless of MISO's hourly price (the Hydro-Québec firm-import
    pattern, :func:`inject_nyiso_firm_imports`). This sets a constant hourly
    ``min_gen`` floor of
    :data:`~market_sim.config.interchange_config.MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC` ×
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
        raised = fleet_arrays.min_gen[r, :] < floor
        np.maximum(fleet_arrays.min_gen[r, :], floor, out=fleet_arrays.min_gen[r, :])
        ensure_mechanism(fleet_arrays)[r, raised] = MECH_FIRM_IMPORT
        applied = True
    return applied


_logger = logging.getLogger(__name__)


def forward_corridor_interface_groups(
    iso_config: ISOConfig, iso: str, year: int, hours: int
) -> list[tuple]:
    """Return the CAISO corridors' FORWARD ATC interface groups (or ``[]``).

    The forward-native corridor deliverability cap
    (``config.caiso_corridor_atc_forward``): builds the capability-based ATC
    envelope from :func:`forward_corridor_atc_envelope` (corridor TTC ×
    posted-ATC base fraction × forward solar derate — never the measured p95
    flow, CLAUDE.md #12) and wraps it in one-sided per-hour interface groups
    via :func:`build_caiso_corridor_flow_groups`. The measured-envelope
    variant (``caiso_corridor_flow_limit``) is a backcast overlay and stays in
    the calibration orchestrator.

    Returns an empty list (byte-identical) when no corridor resolves — e.g.
    the per-hub split is not applied, or the solar-fraction driver is absent
    for ``year``.
    """
    corridor_env = forward_corridor_atc_envelope(iso_config, iso, year, hours)
    if not corridor_env:
        return []
    return build_caiso_corridor_flow_groups(
        iso_config.links, corridor_env, export_envelope=None
    )


def apply_interchange_injections(
    fleet_arrays,
    mc: np.ndarray,
    config,
    iso: str,
    year: int,
    *,
    carbon_price: float = 0.0,
    gas_scenario: str = "mid",
    net_load: np.ndarray | None = None,
    measured_overlay=None,
) -> None:
    """Apply the forward-native interchange price/limit injections.

    The single post-assembly injection sequence BOTH orchestrators run
    (forecast ``runner.py`` and backcast ``scripts/run_calibration.py``), so a
    forward-native seam mechanism is reachable from both paths by construction
    (orchestrator-unification plan §2.2/§3.2). Every injection is gated by its
    existing ``ScenarioConfig`` field — all default off — and each underlying
    injector self-no-ops when its rows/data are absent, so a run without the
    gate (or without a priced node) is byte-identical.

    Order (replicating the backcast orchestrator's long-standing sequence):

    1. Generic reference-price seam (non-CAISO): hourly gas × heat-rate ×
       load-shape seam prices (:func:`inject_reference_price_mc`, with the
       MISO ``miso_pjm_border_anchor`` re-anchor when set), the firm
       scheduled-export floor (:func:`inject_reference_price_firm_export`),
       and the ``miso_firm_import_floor`` mirror.
    2. CAISO dedicated seams (mutually exclusive, the spec ladder):
       ``caiso_reference_price_seam`` (both corridor legs priced forward, CARB
       border carbon on the import leg) or the per-hub FORWARD reference
       prices (``caiso_intertie_reference_price``). The per-hub/bidir
       *measured-hub* pricing is a backcast overlay and lives in
       ``measured_overlay``, never here.
    3. Firm import floors: Manitoba (``miso_firm_imports``) and NYISO
       HQ/Ontario (``nyiso_firm_imports``) must-flow baseloads.
    4. ``measured_overlay(fleet_arrays, mc)`` — the caller-supplied backcast
       measured-price block (measured hub LMP overwrites). The forecast
       runner passes ``None``. It sits exactly here because the measured hub
       overwrites must land on the forward base prices (the MISO PJM-LMP
       overwrite replaces seam rows step 1 priced) and before the offer
       couplings below (which shift/blend whatever base price is active).
    5. Offer couplings (CAISO, skipped under the bidir tie whose injector owns
       both legs): commodity-gas coupling of the desert-SW blocks
       (:func:`inject_caiso_import_gas_coupling`) and the net-load-keyed
       solar-shape collapse (:func:`inject_caiso_import_solar_shape`).

    Args:
        fleet_arrays: Vectorized fleet (modified in place — floors/bounds).
        mc: Base marginal-cost matrix (modified in place).
        config: Scenario config carrying the gates.
        iso: ISO identifier.
        year: Solve year.
        carbon_price: Resolved carbon price ($/t) for the CARB border adder.
        gas_scenario: Gas price path for the reference-price formula.
        net_load: Hourly LP-served net load (demand − must-run − VRE), only
            required when ``caiso_import_solar_shape`` is on.
        measured_overlay: Optional callable ``(fleet_arrays, mc) -> None``
            holding the backcast-only measured-price overlays.

    ``config.neighbor_hr_forward_skill`` (default ``None``) is read here and
    threaded into every :func:`inject_reference_price_mc` call as
    ``forward_skill`` — see that field's docstring.

    Raises:
        ValueError: ``caiso_import_solar_shape`` is on but ``net_load`` was
            not supplied.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    _forward_skill = getattr(config, "neighbor_hr_forward_skill", None)

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

    # --- 2. CAISO dedicated seams (forward-native pricing only). ---
    caiso_ref_seam = (
        getattr(config, "caiso_reference_price_seam", False) and iso == "CAISO"
    )
    per_hub_intertie = (
        (not caiso_ref_seam)
        and getattr(config, "caiso_per_hub_intertie", False)
        and iso == "CAISO"
    )
    bidir_intertie = getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO"
    if caiso_ref_seam:
        if inject_reference_price_mc(
            fleet_arrays,
            mc,
            iso,
            year,
            gas_scenario,
            carbon_price=carbon_price,
            forward_skill=_forward_skill,
        ):
            _logger.info(
                "%s %d: CAISO reference-price seam — both legs of %d WECC "
                "corridors priced from gas × heat-rate × load-shape "
                "(PNW@Malin gross-load, DSW@Palo-Verde net-load; import + CARB "
                "border carbon / export at hub − hurdle)",
                iso,
                year,
                len(INTERFACE_NEIGHBORS.get(iso, [])),
            )
    if per_hub_intertie and getattr(config, "caiso_intertie_reference_price", False):
        # FORWARD seam: price each corridor from the reference-price formula
        # ((HH + basis) × HR × load-shape) instead of the measured hub LMP, so
        # the seam stays live in a forecast year and is validated — not pinned —
        # against the measured realization (CLAUDE.md #10/#12).
        if inject_caiso_per_hub_reference_prices(
            fleet_arrays, mc, iso, year, carbon_price, gas_scenario
        ):
            _logger.info(
                "%s %d: per-hub WECC intertie — FORWARD reference price per "
                "corridor ((HH+basis)×HR×load-shape; PNW@Malin gross-load, "
                "DSW@Palo-Verde net-load), arbitrage-free, one direction per hour "
                "per corridor (measured hub kept only as backcast validation)",
                iso,
                year,
            )

    # --- 3. Firm (must-flow) import floors — contract structure, not a
    #     measured-outcome pin; the backcast overlays only the measured
    #     per-year Manitoba delivery via the builder. ---
    if getattr(config, "miso_firm_imports", False):
        if inject_miso_firm_imports(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: Manitoba firm-hydro import baseload floored (must-flow)",
                iso,
                year,
            )
    if getattr(config, "nyiso_firm_imports", False):
        if inject_nyiso_firm_imports(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: firm import baseload floored (HQ/Ontario must-flow)",
                iso,
                year,
            )
    # CAISO firm-block availability shape (caiso_firm_import_shape, caiso-73):
    # hour-varying pmax CAPABILITY on the firm/contracted tranches — year
    # level from the published DMM RA-import × MIC-split ladder, shape from
    # the measured revealed import base (unit-mean, so annual firm energy is
    # conserved). An availability mechanism, not a price or a floor; a
    # forecast year regenerates from the pooled climatological shape inside
    # the loader.
    if (
        per_hub_intertie
        and getattr(config, "caiso_perhub_firm_base", False)
        and getattr(config, "caiso_firm_import_shape", False)
    ):
        if inject_caiso_firm_import_shape(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: firm import blocks shaped by the measured revealed "
                "base profile (DMM level × unit-mean (month × hod) median of "
                "measured corridor net imports; flat block replaced by an "
                "hour-varying capability)",
                iso,
                year,
            )
        # CAISO firm-block self-schedule floor (caiso_firm_import_selfschedule,
        # caiso-77): the shaped contracted base becomes must-flow — RA/LTC
        # imports are self-scheduled or bid ≤ $0 in the real market (CPUC
        # D.20-06-028), the Manitoba/HQ firm must-flow pattern. Requires the
        # shape above (the shaped capability IS the floor).
        if getattr(config, "caiso_firm_import_selfschedule", False):
            if inject_caiso_firm_import_selfschedule(fleet_arrays, iso, year):
                _logger.info(
                    "%s %d: firm import blocks floored at their shaped "
                    "capability (self-scheduled must-flow contracted base; "
                    "MECH_FIRM_IMPORT)",
                    iso,
                    year,
                )
    # CAISO south-corridor surplus-clean depth (caiso_dsw_surplus_clean,
    # caiso-87): the WEIM clean-transfer capability in surplus-West hours —
    # measured depth-in-surplus net of the shaped firm block, EF 0 (no border
    # carbon), priced at the measured Palo Verde hub by the per-hub injector.
    # Must run AFTER the firm-shape block (its headroom is net-of-firm).
    if per_hub_intertie and getattr(config, "caiso_dsw_surplus_clean", False):
        if inject_caiso_dsw_surplus_clean(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: south-corridor surplus-clean import depth armed "
                "(WEIM clean transfer: measured depth-in-surplus %s MW net of "
                "the shaped firm block, surplus-trigger hours only, EF 0)",
                iso,
                year,
                CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR.get(
                    year, CAISO_DSW_SURPLUS_CLEAN_DEPTH_STATIC
                ),
            )
    # CAISO south-corridor OVERNIGHT clean depth (caiso_dsw_overnight_clean,
    # caiso-93): the unconditional overnight WEIM clean-transfer capability —
    # measured overnight depth net of the shaped firm block AND the caiso-87
    # surplus tranche, hod 0-5 measured-hub hours only, EF 0, raw-hub pricing
    # (no wheel). Must run AFTER the firm-shape and surplus-clean blocks (its
    # headroom nets both).
    if per_hub_intertie and getattr(config, "caiso_dsw_overnight_clean", False):
        if inject_caiso_dsw_overnight_clean(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: south-corridor OVERNIGHT clean import depth armed "
                "(WEIM clean transfer: measured unconditional overnight depth "
                "%s MW net of the shaped firm block + surplus tranche, "
                "hod 0-5 measured-hub hours, EF 0, raw hub)",
                iso,
                year,
                CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR.get(
                    year, CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC
                ),
            )

    # --- 4. Backcast measured-price overlays (caller-supplied; forecast
    #     passes None). Must land after the forward base prices and before
    #     the couplings below. ---
    if measured_overlay is not None:
        measured_overlay(fleet_arrays, mc)

    # --- 5. CAISO offer couplings (skipped under the bidir tie, whose
    #     injector prices both legs itself). ---
    if not bidir_intertie and getattr(config, "caiso_import_gas_coupling", False):
        if inject_caiso_import_gas_coupling(fleet_arrays, mc, config, year):
            _logger.info(
                "%s %d: desert-SW gas import tranches (DSW_CCGT/DSW_CT) coupled "
                "to the measured commodity-gas delta (tracks --gas-hub-basis-overlay)",
                iso,
                year,
            )
    if not bidir_intertie and getattr(config, "caiso_import_solar_shape", False):
        if net_load is None:
            raise ValueError(
                "caiso_import_solar_shape is on but the orchestrator did not "
                "supply net_load to apply_interchange_injections"
            )
        if inject_caiso_import_solar_shape(fleet_arrays, mc, config, net_load):
            _logger.info(
                "%s %d: desert-SW solar import (DSW_solar_PV) offer collapsed "
                "toward the negative keep-running floor in the net-load belly "
                "(negative midday tail)",
                iso,
                year,
            )
