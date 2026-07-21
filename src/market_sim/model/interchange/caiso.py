"""CAISO interchange: WECC intertie builders, injectors, and path limits.

Everything CAISO-specific that lived in ``model/transmission.py``: the
bidirectional / per-hub WECC intertie builders and their measured-hub or
forward reference-price injectors, the firm-import shape/self-schedule and
DSW clean-depth (caiso-87/93/94) capability injectors, corridor flow groups
and forward ATC envelopes, local (SP15-pocket) and asymmetric path limits,
the RA gas commitment floor, and the solar deliverability derate. Per-ISO
tuned limits and basis tables transplant byte-for-byte (CLAUDE.md rules
23/25). Moved INTACT from ``model/transmission.py`` (session 3F,
refactor-consolidation plan §5 item 6); ``transmission`` remains the
full-surface facade.
"""

import logging

import numpy as np
import pandas as pd

from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
from market_sim.config.iso_configs import (
    InterfaceLimit,
    ISOConfig,
    TransferLink,
    Zone,
)
from market_sim.data.fleet_models import Generator
from market_sim.data.floor_mechanisms import (
    MECH_CAISO_GAS_COMMITMENT_FLOOR,
    MECH_FIRM_IMPORT,
    ensure_mechanism,
)
from market_sim.model.interchange.import_nodes import (
    build_export_sinks,
    build_import_generators,
    inject_reference_price_mc,
    wecc_border_carbon_adder,
)
from market_sim.model.interchange.spec import (
    CAISO_CORRIDOR_ATC_SOLAR_K,
    CAISO_DAYTIME_CLEAN_HOD_MAX,
    CAISO_DAYTIME_CLEAN_HOD_MIN,
    CAISO_DAYTIME_CLEAN_TRIM_HOD_MAX,
    CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC,
    CAISO_DSW_DAYTIME_CLEAN_NAME,
    CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR,
    CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_STATIC,
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
    IMPORT_EFORD,
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
    IMPORT_TRANCHE_EF,
    IMPORT_ZONE,
)

_logger = logging.getLogger(__name__)


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
# scripts/data/derive_caiso_export_cap.py). Convention matches the corridor
# envelopes' own CAISO_CORRIDOR_FLOW_PERCENTILE (p95): the peak-bucket ceiling =
# max over (month x hour-of-day) of the p95 aggregate net export, 2023-2025
# (2026 holdout excluded, rule #22) = 4,361 MW. The prior 3,500 was a
# hand-fitted "typical peak" sitting at ~p99 of the aggregate, BELOW the measured
# export capability. rule-23 source-data change: the caiso-51 keeper
# (2026-07-03-caiso-51-firm-base) landed the measured per-hub export envelopes.
# Frozen derive script: scripts/data/derive_caiso_export_cap.py.
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
    daytime_clean: bool = False,
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
        daytime_clean: Append the south-corridor DAYTIME trigger-OFF clean
            depth tranche (caiso-94, ``ScenarioConfig.caiso_dsw_daytime_clean``).
            Same zero-capacity pattern: :func:`inject_caiso_dsw_daytime_clean`
            arms its hourly capability (measured daytime trigger-OFF depth,
            hod 6-21, net of the shaped firm block AND the caiso-87 surplus
            tranche AND the caiso-93 overnight tranche) and the per-hub injector
            prices it at the RAW measured Palo Verde hub with EF 0 and no wheel.
            Un-injected it stays 0 MW.

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
    if daytime_clean:
        # Same placeholder logic (caiso-94): the injector refuses to arm MW
        # without a measured hub series, so the row is 0 MW whenever this
        # price could ever matter.
        base.append((CAISO_DSW_DAYTIME_CLEAN_NAME, 0.0, 180.0))
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
    # The surplus-clean (caiso-87), overnight-clean (caiso-93) and daytime-clean
    # (caiso-94) depth tranches are not on the static ladder; each prices like
    # any other spot rung (EF 0 zeroes the carbon term; the overnight and
    # daytime tranches' delivery basis is (0.0, 0.0) — raw hub, no wheel).
    import_names.add(CAISO_DSW_SURPLUS_CLEAN_NAME)
    import_names.add(CAISO_DSW_OVERNIGHT_CLEAN_NAME)
    import_names.add(CAISO_DSW_DAYTIME_CLEAN_NAME)
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


def inject_caiso_dsw_daytime_clean(
    fleet_arrays, iso: str, year: int, evening_trim: bool = False
) -> bool:
    """Arm the south-corridor DAYTIME trigger-OFF clean import depth (caiso-94).

    The measured no-wedge structure that admitted the caiso-93 OVERNIGHT leg
    extends to the DAYTIME hours the caiso-87 surplus trigger does not cover:
    the daytime trigger-OFF CAISO−PaloVerde spread carries NO unspecified-import
    carbon wedge in every daytime cell (FINDING-caiso94 §2), and the autumn
    daytime cells clear at raw-hub parity. This sets the hourly CAPABILITY of
    the ``DSW_daytime_clean`` tranche (built at 0 MW by
    :func:`build_caiso_per_hub_intertie`)::

        cap[t] = daytime_off[t] × max(0, depth_year − firm_south_capability[t]
                                          − surplus_clean_capability[t]
                                          − overnight_clean_capability[t])

    * ``daytime_off[t]`` — :data:`CAISO_DAYTIME_CLEAN_HOD_MIN` ≤ hod(t) ≤
      :data:`CAISO_DAYTIME_CLEAN_HOD_MAX` (the FINDING-caiso94 daytime band)
      AND the raw measured Palo Verde hub is finite for the hour AND the
      caiso-87 surplus trigger is OFF (``PaloVerde ≥ HR_DSW_CCGT ×
      SoCal_citygate weekly + remote VOM``). The trigger-OFF scoping is
      LOAD-BEARING: daytime caiso-87 is coverage-RICH (66-90 % trigger-ON in
      the belly), so this leg is scoped to the COMPLEMENT to stay DISJOINT from
      caiso-87 (unlike caiso-93 overnight, unconditional because caiso-87 is
      coverage-starved overnight — FINDING-caiso94 §1). The 2023 Jan–Feb
      OASIS-gap fill never arms (gap hours stay 0 MW).
    * ``depth_year`` — the measured daytime trigger-OFF depth
      (:data:`CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR`, p95 corridor net import
      over the daytime trigger-OFF window; CV 0.040 / LOYO ≤ 8.1 % — gates in
      the interchange_config block, `derive_caiso_daytime_clean_depth.py`); an
      unmapped year carries the pooled static entry.
    * the headroom is net of the shaped DSW firm block AND the caiso-87
      ``DSW_surplus_clean`` tranche AND the caiso-93 ``DSW_overnight_clean``
      tranche, so no hour double-carries clean depth across the four
      constructions (their hod/state windows are mostly disjoint, but the
      per-hour netting guarantees it in any overlap).

    With ``evening_trim`` (caiso-97, ``ScenarioConfig.
    caiso_dsw_daytime_evening_trim`` — FINDING-caiso94 §7's pre-registered
    overshoot fix, owner evening-watch TRIPPED ruling 2026-07-18) the window's
    upper bound drops to :data:`CAISO_DAYTIME_CLEAN_TRIM_HOD_MAX` (hod 6-17 —
    the evening peak 18-21 was the §4A EXCLUDE cell) and the depth switches to
    :data:`CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR`, re-derived over the
    trimmed window so the depth always prices the same population it caps.

    A capability, not a floor (``pmin`` stays 0); the corridor ATC envelope
    still caps delivered flow; the fossil rungs are unchanged and price the
    flow beyond the clean depth. Pricing (RAW measured hub + EF 0 × border + ε,
    NO wheel — WEIM transfer basis, ``CAISO_IMPORT_DELIVERY_BASIS``) comes from
    :func:`inject_caiso_per_hub_intertie_prices`. Must run AFTER the firm-shape
    injector, :func:`inject_caiso_dsw_surplus_clean`, and
    :func:`inject_caiso_dsw_overnight_clean`.

    Modifies ``fleet_arrays`` in place (eford availability preserved
    multiplicatively). Returns ``True`` when the tranche was armed, ``False``
    (byte-identical: the row stays 0 MW) when the fleet has no daytime row or a
    measured hub/gas series is unavailable for ``year``.
    """
    from market_sim.data.eia_loader import measured_intertie_hub_price_raw
    from market_sim.data.fuel import socal_citygate_weekly_hourly

    hours = int(fleet_arrays.availability.shape[1])
    zone = CAISO_PER_HUB_IMPORT_ZONES.get(
        CAISO_IMPORT_TRANCHE_HUB[CAISO_DSW_DAYTIME_CLEAN_NAME]
    )
    uid = f"{zone}_{CAISO_DSW_DAYTIME_CLEAN_NAME}"
    row = next(
        (r for r, u in enumerate(fleet_arrays.unit_ids) if u == uid),
        None,
    )
    if row is None:
        return False
    hub = measured_intertie_hub_price_raw(
        iso, year, hours, CAISO_IMPORT_TRANCHE_HUB[CAISO_DSW_DAYTIME_CLEAN_NAME]
    )
    gas = socal_citygate_weekly_hourly(year, hours)
    if hub is None or gas is None:
        return False
    # t = hour index on the model clock; hod = t mod 24 (local calendar).
    # Window and depth MOVE TOGETHER under the trim (caiso-97): the depth is
    # the p95 over exactly the window hours the capability arms.
    hod_max = (
        CAISO_DAYTIME_CLEAN_TRIM_HOD_MAX
        if evening_trim
        else CAISO_DAYTIME_CLEAN_HOD_MAX
    )
    hod = np.arange(hours) % 24
    daytime_hod = (hod >= CAISO_DAYTIME_CLEAN_HOD_MIN) & (hod <= hod_max)
    # Trigger-OFF = measured hub, NOT the caiso-87 surplus trigger. Identical
    # trigger construction to inject_caiso_dsw_surplus_clean (read-only reuse —
    # the daytime leg never re-evaluates or widens caiso-87's own trigger).
    hr = _CAISO_IMPORT_COUPLE_HR["DSW_CCGT"]  # 0.37/0.0531 ≈ 6.97
    floor = hr * gas + CAISO_DSW_SURPLUS_REMOTE_VOM
    surplus = np.isfinite(hub) & np.isfinite(floor) & (hub < floor)
    daytime = daytime_hod & np.isfinite(hub) & ~surplus
    if not daytime.any():
        return False
    if evening_trim:
        depth = CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR.get(
            year, CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_STATIC
        )
    else:
        depth = CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR.get(
            year, CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC
        )
    # Net of the shaped south firm block AND the caiso-87 surplus tranche AND
    # the caiso-93 overnight tranche (all post-injection: this runs last).
    firm_cap = np.zeros(hours)
    for r, u in enumerate(fleet_arrays.unit_ids):
        if not u.startswith(f"{zone}_"):
            continue
        name = u[len(zone) + 1 :]
        if (
            name in CAISO_FIRM_IMPORT_TRANCHES
            or name == CAISO_DSW_SURPLUS_CLEAN_NAME
            or name == CAISO_DSW_OVERNIGHT_CLEAN_NAME
        ):
            firm_cap += fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
    cap = np.where(daytime, np.clip(depth - firm_cap, 0.0, None), 0.0)
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
    # The surplus-clean (caiso-87), overnight-clean (caiso-93) and daytime-clean
    # (caiso-94) depth tranches are not on the static ladder; each prices like
    # any other spot rung (EF 0 zeroes the carbon term; the overnight and
    # daytime tranches' delivery basis is (0.0, 0.0) — raw hub, no wheel).
    import_names.add(CAISO_DSW_SURPLUS_CLEAN_NAME)
    import_names.add(CAISO_DSW_OVERNIGHT_CLEAN_NAME)
    import_names.add(CAISO_DSW_DAYTIME_CLEAN_NAME)
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


def apply_caiso_seam_injections(
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
    """Registry step: the CAISO dedicated-seam + firm/clean-depth block.

    Verbatim steps 2-3 (CAISO half) of the historical
    ``apply_interchange_injections`` monolith: the dedicated CAISO seams
    (``caiso_reference_price_seam`` or the per-hub FORWARD reference prices),
    then the firm-import shape/self-schedule and the caiso-87/93/94 clean
    depth injectors in their load-bearing order (each nets the previous
    tranche's headroom). The measured-hub pricing stays a backcast overlay
    (the caller-supplied ``measured_overlay``), never here.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    _forward_skill = forward_skill
    # --- 2. CAISO dedicated seams (forward-native pricing only). ---
    caiso_ref_seam = (
        getattr(config, "caiso_reference_price_seam", False) and iso == "CAISO"
    )
    per_hub_intertie = (
        (not caiso_ref_seam)
        and getattr(config, "caiso_per_hub_intertie", False)
        and iso == "CAISO"
    )
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
    # CAISO south-corridor DAYTIME trigger-OFF clean depth
    # (caiso_dsw_daytime_clean, caiso-94): the daytime WEIM clean-transfer
    # capability in the hours the caiso-87 surplus trigger does not cover —
    # measured daytime trigger-OFF depth net of the shaped firm block AND the
    # caiso-87 surplus tranche AND the caiso-93 overnight tranche, hod 6-21
    # measured-hub trigger-OFF hours only, EF 0, raw-hub pricing (no wheel).
    # Under the caiso-97 evening trim the window is hod 6-17 with the depth
    # re-derived over that window (FINDING-caiso94 §7 pre-registered fix).
    # Must run LAST of the clean-depth injectors (its headroom nets all three).
    if per_hub_intertie and getattr(config, "caiso_dsw_daytime_clean", False):
        _day_trim = bool(getattr(config, "caiso_dsw_daytime_evening_trim", False))
        if inject_caiso_dsw_daytime_clean(
            fleet_arrays, iso, year, evening_trim=_day_trim
        ):
            _logger.info(
                "%s %d: south-corridor DAYTIME trigger-OFF clean import depth "
                "armed (WEIM clean transfer: measured daytime trigger-OFF depth "
                "%s MW net of the shaped firm block + surplus + overnight "
                "tranches, hod %d-%d measured-hub trigger-OFF hours, EF 0, raw hub)",
                iso,
                year,
                (
                    CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR.get(
                        year, CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_STATIC
                    )
                    if _day_trim
                    else CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR.get(
                        year, CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC
                    )
                ),
                CAISO_DAYTIME_CLEAN_HOD_MIN,
                CAISO_DAYTIME_CLEAN_TRIM_HOD_MAX
                if _day_trim
                else CAISO_DAYTIME_CLEAN_HOD_MAX,
            )
