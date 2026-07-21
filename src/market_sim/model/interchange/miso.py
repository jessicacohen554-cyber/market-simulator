"""MISO interchange: RDT/TCDC, seams, deliverability, and firm imports.

Everything MISO-specific that lived in ``model/transmission.py``: the
seasonal CIL/CEL deliverability groups, the South external-node split and
the published RDT derate + TCDC price tiers, the Midwest zonal loss-link
split and per-link marginal loss fractions, the measured PJM-border LMP and
Q-Q seam-ladder repricers, the per-seam deliverability envelopes, and the
Manitoba firm-hydro import block and floor. Per-ISO tuned limits and basis
tables transplant byte-for-byte (CLAUDE.md rules 23/25). Moved INTACT from
``model/transmission.py`` (session 3F, refactor-consolidation plan §5
item 6); ``transmission`` remains the full-surface facade.
"""

import logging

import numpy as np

from market_sim.config.constants import (
    MISO_RDT_CONTRACT_N_TO_S_MW,
    MISO_RDT_CONTRACT_S_TO_N_MW,
    MISO_RDT_DEFAULT_DERATE_FRAC,
    MISO_RDT_TCDC_STEP1_PRICE,
    MISO_RDT_TCDC_STEP2_PRICE,
    MISO_RDT_TCDC_STEP2_START_FRAC,
    MISO_RPE_DEMAND_VALUE,
    MISO_SOUTH_EXTERNAL_ZONE,
)
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
from market_sim.model.interchange.import_nodes import (
    _inject_seam_ladder,
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
)
from market_sim.model.interchange.spec import (
    IMPORT_ZONE,
    MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC,
    MISO_MANITOBA_FIRM_IMPORT_NAME,
    MISO_MANITOBA_FIRM_IMPORT_OFFER,
    MISO_MANITOBA_FIRM_IMPORT_ZONE,
    resolve_miso_manitoba_firm_import_mw,
)

_logger = logging.getLogger(__name__)


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
    ``scripts/data/build_pjm_border_lmp_miso.py``. Returns ``True`` when at least
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
    ``scripts/data/derive_miso_seam_ladders.py`` from the EIA-930 per-seam flow
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


# Loss-pair flow tiebreaker (miso_zonal_loss_surface): the same role and
# magnitude as the storage ε = 0.001 $/MWh (CLAUDE.md rule #9) and
# CAISO_INTERTIE_TIEBREAK_EPS — charged on BOTH one-way directions of each
# lossy Midwest link so (a) a degenerate lossless-direction wash nets to one
# direction per hour, and (b) circulating flow (both directions at once,
# which dissipates ε_loss × flow at each end — free disposal) is strictly
# cost-positive whenever |zonal dual| × loss fraction < this charge. With
# MISO renewables offering at ≥ $0 (negative_renewable_offers is CAISO-only)
# the model's zonal duals floor near -dump ε, so 0.001 dominates the
# disposal value in every hour. Numerical device, not a hurdle rate (the
# measured-MCC hurdle family is refuted — charter §3 M2); not a fitted level.
MISO_LOSS_LINK_TIEBREAK_EPS = 1e-3


def _miso_midwest_internal(from_zone: str, to_zone: str) -> bool:
    """Whether a link joins two MISO Midwest zones (South/RDT excluded)."""
    return (
        from_zone.startswith("MISO-")
        and to_zone.startswith("MISO-")
        and "MISO-South" not in (from_zone, to_zone)
    )


def apply_miso_zonal_loss_links(iso_config: ISOConfig) -> ISOConfig:
    """Split each Midwest-internal bidirectional link into a one-way loss pair.

    The miso-76 M3 topology transform (charter
    ``docs/handoffs/miso-nc-price-separation-design-2026-07.md`` §4, gated on
    ``ScenarioConfig.miso_zonal_loss_surface``): every bidirectional
    Midwest-internal link (L1–L6) becomes TWO one-way links
    (``is_bidirectional=False``, same TTC each way — the RDT pair's
    established structure), each charged the
    :data:`MISO_LOSS_LINK_TIEBREAK_EPS` flow cost. The per-direction
    marginal loss fractions themselves are hour-varying and enter the
    energy balance via :func:`build_miso_link_loss` +
    ``dispatch.build_constraints(link_loss=...)`` — the split exists
    because a loss coefficient on a SIGNED link would create energy on
    reverse flow (see the ``link_loss`` docstring), so each direction must
    be its own nonnegative column.

    Interface groups (the CIL/CEL envelopes and static ``MISO_CIL_*``
    limits) match links by zone pair with orientation signs, so the pair
    sums to the net corridor flow automatically — the same mechanism the
    RDT one-way pair already rides. The RDT/South links and external seams
    are untouched: South separation stays owned by the RDT TCDC structure
    (one mechanism per phenomenon, rule #19).

    Returns a validated copy; a config with no Midwest-internal
    bidirectional links (already split, or not MISO) is returned unchanged.
    """
    new_links: list[TransferLink] = []
    changed = False
    for ln in iso_config.links:
        if ln.is_bidirectional and _miso_midwest_internal(ln.from_zone, ln.to_zone):
            for frm, to in ((ln.from_zone, ln.to_zone), (ln.to_zone, ln.from_zone)):
                new_links.append(
                    ln.model_copy(
                        update={
                            "from_zone": frm,
                            "to_zone": to,
                            "is_bidirectional": False,
                            "flow_cost": ln.flow_cost + MISO_LOSS_LINK_TIEBREAK_EPS,
                        }
                    )
                )
            changed = True
        else:
            new_links.append(ln)
    if not changed:
        return iso_config
    extended = iso_config.model_copy(update={"links": new_links})
    extended.validate_topology()
    return extended


def build_miso_link_loss(
    links: list[TransferLink], iso: str, year: int, hours: int
) -> np.ndarray | None:
    """Return the ``(n_links, hours)`` per-link marginal loss fractions.

    For each one-way Midwest-internal link ``x -> y`` and month ``m``, the
    receiving-side loss fraction is::

        eps_(x->y),m = max(0, (dev_y,m - dev_x,m) / (1 + dev_y,m))

    so an interior, uncongested flow ``x -> y`` prices the receiving zone at
    ``lambda_y = lambda_x x (1 + dev_y,m)/(1 + dev_x,m)`` — exactly the
    measured marginal delivery-factor ratio (MLC construction: LMP's loss
    component is ``MEC x (DF - 1)``). The reverse direction of the pair
    clamps to 0 for that month (the marginal-DF linearization is oriented
    by the month's persistent gradient; the clamp is conservative —
    atypical-direction hours carry no separation rather than a fabricated
    inverted one). Months where the measured gradient flips sign swap the
    lossy direction automatically.

    The monthly surface comes from
    :func:`market_sim.data.loss_surface.load_zone_month_deviation` (year
    rows for a train backcast year, pooled rows otherwise) and expands to
    hours on the model's fixed non-leap calendar. Non-Midwest links carry
    zero rows. Fails loud if any Midwest-internal link is still
    bidirectional (the loss coefficient would create energy on reverse
    flow — apply :func:`apply_miso_zonal_loss_links` first), or if a
    Midwest zone is missing from the surface.

    Returns ``None`` for a non-MISO ``iso`` (byte-identical elsewhere,
    rule 24).
    """
    if iso.upper() != "MISO":
        return None
    from market_sim.data.loss_surface import load_zone_month_deviation

    surface = load_zone_month_deviation(iso, year)
    month_of_hour = np.repeat(np.arange(12), _MONTH_HOURS)[:hours]
    loss = np.zeros((len(links), hours), dtype=float)
    for i, ln in enumerate(links):  # i: link column (few links, not hours)
        if not _miso_midwest_internal(ln.from_zone, ln.to_zone):
            continue
        if ln.is_bidirectional:
            raise ValueError(
                f"link {ln.from_zone}->{ln.to_zone} is bidirectional; "
                "apply_miso_zonal_loss_links must run before "
                "build_miso_link_loss (a signed lossy link would create "
                "energy on reverse flow)"
            )
        try:
            dev_from = np.asarray(surface[ln.from_zone], dtype=float)
            dev_to = np.asarray(surface[ln.to_zone], dtype=float)
        except KeyError as exc:
            raise ValueError(
                f"loss surface has no zone {exc.args[0]!r} — regenerate "
                "scripts/data/derive_miso_loss_surface.py"
            ) from exc
        eps_m = np.maximum(0.0, (dev_to - dev_from) / (1.0 + dev_to))
        loss[i, :] = eps_m[month_of_hour]
    return loss if np.any(loss > 0.0) else None


def inject_miso_seam_flow_limit(
    fleet_arrays,
    iso: str,
    year: int,
    percentile: float | None = None,
    direction: str = "import",
    merit_cap: bool = False,
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

    ``merit_cap`` (``ScenarioConfig.miso_seam_envelope_merit_cap``, miso-73)
    selects the envelope's composition semantics. Default ``False`` keeps the
    historical uniform per-band derate (``availability × cap/limit``), under
    which the seam reaches its cap only when the internal price clears the most
    expensive band — which breaks the measured Q-Q ladder's price-to-depth
    pairing (``pi_k`` is derived at depth ``L_k`` on the FULL-width band grid)
    and was measured to suppress PJM imports −5.6/−8.3/−8.9 TWh and South
    exports +2.8/+2.6/+3.1 TWh (2023/24/25) on the miso-72 keeper. ``True``
    applies the ceiling with merit-order (waterfall) bounds — band *k* keeps
    ``clip(cap − (k−1)·step, 0, step)`` — so cheap base rungs stay full-width,
    the seam total is capped at ``min(cap, limit)`` exactly, and the LP fills
    cheapest-first below the ceiling as this docstring always intended. Given
    monotone rungs this is exactly a shared per-seam-hour ``Σ bands ≤ cap``
    constraint, implemented availability-only (no new LP rows). See
    ``docs/handoffs/miso-g23-seam-envelope-composition-design-2026-07.md``.

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
        # Band index k from the "#k" uid suffix: band order = depth order = rung
        # order (the Q-Q ladder's rungs are monotone in k by construction), so
        # the merit-cap waterfall fills band 1 first.
        rows = sorted(
            rows, key=lambda r: int(fleet_arrays.unit_ids[r].rsplit("#", 1)[1])
        )
        if direction == "import":
            total = float(fleet_arrays.pmax[rows].sum())  # = interface_limit_mw
            if total <= 0.0:
                continue
            if merit_cap:
                # Merit-order (waterfall) ceiling: band k keeps
                # clip(cap − (k−1)·step, 0, step), so the cheap base rungs stay
                # full-width and Σ_k bound_k = min(cap, limit) exactly — the
                # ceiling the measured ladder's price-to-depth pairing assumes.
                depth = 0.0
                for r in rows:
                    width = float(fleet_arrays.pmax[r])
                    if width <= 0.0:
                        continue
                    fleet_arrays.availability[r, :] *= np.clip(
                        (cap - depth) / width, 0.0, 1.0
                    )
                    depth += width
            else:
                # Uniform per-band derate: the seam's summed import availability
                # ≤ cap each hour, but every band — including the cheap base
                # rungs — shrinks by cap/limit, so reaching the cap needs the
                # dearest rung in the money (the miso-73 composition defect;
                # kept as the default for pre-miso-73 replay fidelity).
                frac = np.clip(cap / total, 0.0, 1.0)
                for r in rows:
                    fleet_arrays.availability[r, :] *= frac
            applied = True
        else:
            total = -float(fleet_arrays.pmin[rows].sum())  # = interface_limit_mw
            if total <= 0.0:
                continue
            if merit_cap:
                # Export mirror of the waterfall: band k's lower bound becomes
                # −clip(cap − (k−1)·step, 0, step); maximum() composes with any
                # existing floor (the cap only reduces export, never forces it).
                depth = 0.0
                for r in rows:
                    width = -float(fleet_arrays.pmin[r])
                    if width <= 0.0:
                        continue
                    capped = float(fleet_arrays.pmin[r]) * np.clip(
                        (cap - depth) / width, 0.0, 1.0
                    )
                    np.maximum(
                        fleet_arrays.min_gen[r, :],
                        capped,
                        out=fleet_arrays.min_gen[r, :],
                    )
                    depth += width
            else:
                # Uniform per-band lower-bound raise so the seam's summed max
                # export ≤ cap each hour. pmin[r] < 0; pmin[r] × frac ∈
                # [pmin[r], 0] raises the bound toward 0 as the cap tightens,
                # and maximum() composes with any existing floor (the cap only
                # reduces export, never forces it).
                frac = np.clip(cap / total, 0.0, 1.0)
                for r in rows:
                    capped = float(fleet_arrays.pmin[r]) * frac
                    np.maximum(
                        fleet_arrays.min_gen[r, :],
                        capped,
                        out=fleet_arrays.min_gen[r, :],
                    )
            applied = True
    return applied


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


def apply_miso_firm_import_injections(
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
    """Registry step: the Manitoba firm-hydro must-flow floor.

    Verbatim step 3 (MISO half) of the historical
    ``apply_interchange_injections`` monolith — contract structure, not a
    measured-outcome pin; gated on ``config.miso_firm_imports``.
    """
    if getattr(config, "miso_firm_imports", False):
        if inject_miso_firm_imports(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: Manitoba firm-hydro import baseload floored (must-flow)",
                iso,
                year,
            )
