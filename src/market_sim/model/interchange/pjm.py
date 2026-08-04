"""PJM interchange: external flow groups, east interface cut, seam repricers.

Everything PJM-specific that lived in ``model/transmission.py``: the
per-border external star-node flow caps, the measured joint EMAAC-import
(Eastern reactive interface) cut, the measured Q-Q seam-ladder repricer, and
the per-neighbor seam deliverability envelopes. Per-ISO tuned limits
transplant byte-for-byte (CLAUDE.md rules 23/25). Moved INTACT from
``model/transmission.py`` (session 3F, refactor-consolidation plan §5
item 6); ``transmission`` remains the full-surface facade.
"""

import numpy as np

from market_sim.config.iso_configs import TransferLink
from market_sim.model.interchange.import_nodes import (
    _inject_seam_ladder,
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
)


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
    ``scripts/data/derive_pjm_seam_ladders.py`` from PJM's settlement-grade
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


#: The model's western→MAD cut: the two internal links crossing PJM's
#: Manual-03 AP SOUTH reactive transfer interface boundary at the 8-zone
#: grain. ``constants.PJM_INTERFACE_LINK_MAP``'s own note names exactly this
#: pair as the parallel paths the flowgate splits across in this reduced
#: network (FINDING-pjm134 §4).
PJM_APSOUTH_CUT_LINKS: tuple[tuple[str, str], ...] = (
    ("PJM_West_APS", "PJM_SWMAAC"),
    ("PJM_West_APS", "PJM_Dominion"),
)


def pjm_external_star_cut_links() -> tuple[tuple[str, str], ...]:
    """The star node's five ``PJM_external→border`` links, in topology order.

    Derived from :data:`~market_sim.config.interchange_config.IMPORT_NODE_LINKS`
    and :data:`~market_sim.config.interchange_config.IMPORT_ZONE` rather than
    re-listed, so the cut spans exactly the links the import-node extension
    creates and cannot drift from them. Empty when PJM has no import zone.
    """
    from market_sim.config.interchange_config import IMPORT_NODE_LINKS, IMPORT_ZONE

    ext = IMPORT_ZONE.get("PJM")
    if ext is None:
        return ()
    return tuple((ext, border) for border, _ in IMPORT_NODE_LINKS.get("PJM", []))


def _build_joint_interface_cut(
    links: list[TransferLink],
    limit_hourly: np.ndarray,
    cut_links: tuple[tuple[str, str], ...],
) -> list[tuple]:
    """One one-sided aggregate interface group over ``cut_links``.

    Shared core of the two PJM joint cuts. Caps the summed flow across the
    named zone pairs at the hour's measured limit; a link oriented opposite
    the cut enters with sign −1 so the group reads net flow in the cut's
    direction. One-sided (``bidirectional=False``): an import security limit
    never caps the reverse direction, which keeps the per-link TTCs.

    Args:
        links: The topology's transfer links (pre- or post- import-node
            extension — matching is by zone pair).
        limit_hourly: ``(T,)`` measured hourly cap.
        cut_links: The ``(from_zone, to_zone)`` pairs the interface spans,
            oriented in the cut's direction.

    Returns:
        A single-element list of 5-tuples ``(link_idx, cap_hourly, False,
        None, signs)`` for :func:`market_sim.model.dispatch._build_interface_rows`,
        or an empty list when no cut link exists in the topology (the LP is
        then byte-identical).
    """
    idx: list[int] = []
    signs: list[float] = []
    for a, b in cut_links:
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


def build_pjm_apsouth_interface_cut_groups(
    links: list[TransferLink],
    limit_hourly: np.ndarray,
) -> list[tuple]:
    """The measured joint western→MAD cut (``pjm_apsouth_interface_cut``).

    One ONE-SIDED aggregate interface group capping the summed eastward flow
    across :data:`PJM_APSOUTH_CUT_LINKS` at the hour's measured AP-South
    limit (:func:`market_sim.data.transfer_interface_limits.pjm_apsouth_interface_hourly`).

    This **replaces**, rather than stacks on (rule 19 ``[R-ONE-MECH]``), the
    documented misalignment ``constants.PJM_INTERFACE_LINK_MAP`` already
    records: the per-link ``pjm_measured_interface_limits`` overlay applies
    AP-South to West_APS→SWMAAC alone while the parallel West_APS→Dominion
    path rides a 3,000 MW static, so the LP's west→MAD capability is
    ``AP-South(t) + 3,000 MW`` against a published flowgate of ~3,900 MW. The
    joint cap is the faithful reduced-network reading of a flowgate that spans
    both paths, and it dominates the per-link bound (a sum below the limit
    implies each term is), so the surviving per-link overlay is redundant, not
    additive. Zero fitted scalars — the same construction, and the same
    Manual-03 provenance, as
    :func:`build_pjm_east_interface_cut_groups` (``pjm_east_interface_cut``).

    Args:
        links: The topology's transfer links (pre- or post- import-node
            extension — matching is by zone pair).
        limit_hourly: ``(T,)`` measured hourly cap from
            :func:`market_sim.data.transfer_interface_limits.pjm_apsouth_interface_hourly`.

    Returns:
        A single-element list of 5-tuples for
        :func:`market_sim.model.dispatch._build_interface_rows`, or an empty
        list when neither cut link exists in the topology (the LP is then
        byte-identical).
    """
    return _build_joint_interface_cut(links, limit_hourly, PJM_APSOUTH_CUT_LINKS)


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
    return _build_joint_interface_cut(links, limit_hourly, PJM_EAST_CUT_LINKS)


def build_pjm_external_net_position_cut_groups(
    links: list[TransferLink],
    limit_hourly: np.ndarray,
) -> list[tuple]:
    """The measured joint star-node NET-position cut (``pjm_external_net_position_cut``).

    One ONE-SIDED aggregate interface group capping the **summed** injection
    across every ``PJM_external→border`` link
    (:func:`pjm_external_star_cut_links`) at the hour's measured net-position
    envelope (:func:`market_sim.data.eia_loader.pjm_net_interchange_envelope`)::

        Σ_z Flow(PJM_external → z)  ≤  P_p95( measured net import | month, hod )

    Because the summed star-link flow **is** the LP's net interchange, this one
    row is the model's only statement about PJM's net position — today there is
    none. The star node is bounded solely by *marginal* per-border, per-direction
    percentiles: ``build_pjm_external_flow_groups`` caps each link's signed flow
    at that border's own p95 and ``inject_pjm_seam_flow_limit`` sizes each
    neighbor's bands from the same rows, so five marginal 95th percentiles are
    summed as though they were a joint one, and nothing bounds the total.

    Rule 19 ``[R-ONE-MECH]`` — this **REPLACES** that sum-of-marginals ceiling on
    the aggregate question rather than stacking on it: the joint cap dominates
    (a sum under the limit implies the marginal terms are), so the per-border
    groups stay as the *locational* bound while the joint row owns the *total*.
    It is the same construction as :func:`build_pjm_apsouth_interface_cut_groups`
    and :func:`build_pjm_east_interface_cut_groups` — a measured aggregate
    applied to the aggregate rather than element by element — carried from the
    internal flowgates to the external seam (pjm-135; FINDING-pjm134 §7's
    handover). Zero fitted scalars: the same tie-line file, the same
    ``PJM_EXTERNAL_FLOW_PERCENTILE``, the same (month × hour-of-day) bucketing
    the per-border envelope already uses.

    One-sided (``bidirectional=False``): the cap bounds how import-heavy the net
    position may be and never bounds net export, so the LP keeps every export
    path it has today. PJM is a measured net exporter in 92.5–98.1 % of hours,
    so the ceiling is normally negative — an upper bound on net import that
    reads as a floor on net export.

    Args:
        links: The **import-node-extended** transfer links (the star links exist
            only after that extension; matching is by zone pair).
        limit_hourly: ``(T,)`` measured hourly net-import ceiling, MW
            import-positive, from
            :func:`market_sim.data.eia_loader.pjm_net_interchange_envelope`.

    Returns:
        A single-element list of 5-tuples ``(link_idx, cap_hourly, False,
        None, signs)`` for :func:`market_sim.model.dispatch._build_interface_rows`,
        or an empty list when the topology carries no star link (the LP is then
        byte-identical).
    """
    return _build_joint_interface_cut(
        links, limit_hourly, pjm_external_star_cut_links()
    )


# --------------------------------------------------------------------------
# Marginal transmission-loss physics (pjm_zonal_loss_surface, pjm-136 M2)
# --------------------------------------------------------------------------

# Non-leap month lengths in hours. The model's fixed 8760-hour clock drops
# Feb 29, so non-leap month boundaries align exactly in every year.
_MONTH_HOURS: tuple[int, ...] = tuple(
    d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
)

# Loss-pair flow tiebreaker (``pjm_zonal_loss_surface``): the same role and
# magnitude as the storage ε = 0.001 $/MWh (CLAUDE.md rule 9 ``[R-EPSILON]``),
# charged on BOTH one-way directions of each lossy internal PJM link so that
# (a) a degenerate lossless-direction wash nets to one direction per hour, and
# (b) circulating flow (both directions at once, which dissipates
# ε_loss × flow at each end — free disposal) is strictly cost-positive whenever
# |zonal dual| × loss fraction < this charge. PJM renewables offer at ≥ $0
# (``negative_renewable_offers`` is default-off and CAISO-scoped), so the
# model's PJM duals floor near −dump ε and 0.001 dominates the disposal value
# in every hour. A numerical device, not a hurdle rate and not a fitted level —
# the priced-hurdle family is deliberately NOT what this mechanism is
# (rule 13 ``[R-MEASURED]``: the separation comes from measured loss physics in
# the energy balance, never from a cost adder tuned to a price residual).
PJM_LOSS_LINK_TIEBREAK_EPS = 1e-3


def _pjm_internal(from_zone: str, to_zone: str) -> bool:
    """Whether a link joins two internal PJM zones (the external star excluded).

    The star node's five ``PJM_external→border`` links are deliberately NOT
    lossy: ``PJM_external`` is a fictitious pricing node with no location, so
    it has no published delivery-factor deviation to derive one from, and
    inventing one would be a fitted scalar (rule 5 ``[R-NO-MAGIC]``). The seam
    keeps its own mechanisms — the per-border envelopes, the measured ladders
    and the pjm-135 net-position cut.
    """
    return (
        from_zone.startswith("PJM_")
        and to_zone.startswith("PJM_")
        and "PJM_external" not in (from_zone, to_zone)
    )


def apply_pjm_zonal_loss_links(iso_config):
    """Split each internal PJM link into a one-way loss pair.

    The pjm-136 M2 topology transform (gated on
    ``ScenarioConfig.pjm_zonal_loss_surface``): every bidirectional
    PJM-internal link becomes TWO one-way links (``is_bidirectional=False``,
    same TTC each way), each charged the
    :data:`PJM_LOSS_LINK_TIEBREAK_EPS` flow cost. The per-direction marginal
    loss fractions themselves are hour-varying and enter the energy balance
    via :func:`build_pjm_link_loss` +
    ``dispatch.build_constraints(link_loss=...)``; the split exists because a
    loss coefficient on a SIGNED link would create energy on reverse flow, so
    each direction must be its own nonnegative column.

    Composition with PJM's existing network mechanisms is by construction:

    * the joint interface cuts (``pjm_east_interface_cut``,
      ``pjm_apsouth_interface_cut``, ``pjm_external_net_position_cut``) match
      links by zone pair and enter the reverse orientation with sign −1
      (:func:`_build_joint_interface_cut`), so each pair sums to the net
      corridor flow automatically;
    * ``pjm_measured_interface_limits`` keys
      :data:`~market_sim.config.constants.PJM_INTERFACE_LINK_MAP` on the
      forward ``(from, to)`` pair, so the forward one-way link takes the
      measured hourly cap and the reverse one keeps the static rating — the
      same asymmetric semantics the bidirectional link had via ``ttc_import``;
    * the external star links are untouched (:func:`_pjm_internal`), so the
      import-node identification and the net-position cut are unchanged.

    Returns a validated copy; a config with no internal bidirectional PJM
    links (already split, or not PJM) is returned unchanged.
    """
    new_links: list[TransferLink] = []
    changed = False
    for ln in iso_config.links:
        if ln.is_bidirectional and _pjm_internal(ln.from_zone, ln.to_zone):
            for frm, to in ((ln.from_zone, ln.to_zone), (ln.to_zone, ln.from_zone)):
                new_links.append(
                    ln.model_copy(
                        update={
                            "from_zone": frm,
                            "to_zone": to,
                            "is_bidirectional": False,
                            "flow_cost": ln.flow_cost + PJM_LOSS_LINK_TIEBREAK_EPS,
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


def build_pjm_link_loss(
    links: list[TransferLink], iso: str, year: int, hours: int
) -> np.ndarray | None:
    """Return the ``(n_links, hours)`` per-link marginal loss fractions for PJM.

    For each one-way internal link ``x -> y`` and month ``m``, the
    receiving-side loss fraction is::

        eps_(x->y),m = max(0, (dev_y,m - dev_x,m) / (1 + dev_y,m))

    so an interior, uncongested flow ``x -> y`` prices the receiving zone at
    ``lambda_y = lambda_x x (1 + dev_y,m)/(1 + dev_x,m)`` — exactly the
    measured marginal delivery-factor ratio PJM's own LMPs carry
    (``LMP_i = MEC + MCC_i + MLC_i``, PJM Manual 11 §2 / OATT Att. K; the
    derive's ``dev_z = sum(MLC_z)/sum(MEC)`` estimator reproduces the measured
    MLC when re-multiplied by the measured MEC). The reverse direction of the
    pair clamps to 0 for that month — the marginal-DF linearization is oriented
    by the month's persistent gradient, and the clamp is conservative:
    atypical-direction hours carry no separation rather than a fabricated
    inverted one. A month whose measured gradient flips sign swaps the lossy
    direction automatically.

    The monthly surface comes from
    :func:`market_sim.data.loss_surface.load_zone_month_deviation` (PJM's own
    ``PJM_loss_surface.csv`` — year rows for a train backcast year, pooled rows
    otherwise) and expands to hours on the model's fixed non-leap calendar.
    External star links carry zero rows. Fails loud if any internal link is
    still bidirectional (the loss coefficient would create energy on reverse
    flow — apply :func:`apply_pjm_zonal_loss_links` first), or if a PJM zone is
    missing from the surface.

    Returns ``None`` for a non-PJM ``iso`` (byte-identical elsewhere, rule 24).
    """
    if iso.upper() != "PJM":
        return None
    from market_sim.data.loss_surface import load_zone_month_deviation

    surface = load_zone_month_deviation(iso, year)
    month_of_hour = np.repeat(np.arange(12), _MONTH_HOURS)[:hours]
    loss = np.zeros((len(links), hours), dtype=float)
    for i, ln in enumerate(links):  # i: link column (few links, not hours)
        if not _pjm_internal(ln.from_zone, ln.to_zone):
            continue
        if ln.is_bidirectional:
            raise ValueError(
                f"link {ln.from_zone}->{ln.to_zone} is bidirectional; "
                "apply_pjm_zonal_loss_links must run before "
                "build_pjm_link_loss (a signed lossy link would create "
                "energy on reverse flow)"
            )
        try:
            dev_from = np.asarray(surface[ln.from_zone], dtype=float)
            dev_to = np.asarray(surface[ln.to_zone], dtype=float)
        except KeyError as exc:
            raise ValueError(
                f"loss surface has no zone {exc.args[0]!r} — regenerate "
                "scripts/data/derive_pjm_loss_surface.py"
            ) from exc
        eps_m = np.maximum(0.0, (dev_to - dev_from) / (1.0 + dev_to))
        loss[i, :] = eps_m[month_of_hour]
    return loss if np.any(loss > 0.0) else None


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
    deliverability envelope built from the PJM tie-line file. The mechanism is
    identical to the MISO function: import caps scale ``availability``; export
    caps raise ``min_gen``.

    **The envelope is built per NEIGHBOUR, from that seam's OWN ties**
    (:data:`~market_sim.model.interchange.spec.PJM_TIE_NEIGHBOR` ->
    :func:`~market_sim.data.eia_loader.pjm_neighbor_interchange_envelope`).

    A zone-summed construction preceded it — a per-model-ZONE envelope from
    :func:`~market_sim.data.eia_loader.pjm_zonal_interchange_envelope` (each tie
    attributed to one border zone via ``data.eia930.envelopes._PJM_TIE_ZONE``),
    summed over the neighbour's ``border_zones`` — and it mixed counterparties,
    because a zone bucket holds every tie that lands in it and several
    neighbours name the same border zone. It was also where the two modules'
    attributions collided: ``_PJM_TIE_ZONE`` puts the whole TVA tie on
    ``PJM_Dominion`` while this interface's ``border_zones`` spans
    ``PJM_AEP_Ohio`` + ``PJM_Dominion``, so the TVA cap picked up the Carolinas
    ties, the MISO Indiana/Ohio ties, LGEE and TVA itself. That path was carried
    behind ``ScenarioConfig.pjm_seam_envelope_by_neighbor`` for the pjm-151
    single-delta A/B and **deleted at pjm-152 once the repair was the keeper's
    armed path** (rule 26 ``[R-DELETE]``: a deprecated parameter that still
    parses is a re-armable answer key). Measured on PJM's own file at p90
    (``scripts/probes/pjm151_seam_envelope_attribution.py``, netting each seam's
    ties within the hour before the directional clip, as
    ``pjm_zonal_interchange`` does), the zone-summed cap against this one:

    ==========  =========  ==================================  ===============
    seam        direction  legacy cap / direct cap (23/24/25)  legacy binds
    ==========  =========  ==================================  ===============
    TVA         export     124x / 53x / 40x                    0.000/0.000/0.097
    LGEE        export     33x / 42x / 26x                     0.000/0.000/0.014
    TVA         import     2.05x / 2.20x / 2.38x               0.167/0.125/0.240
    Carolinas   import     1.79x / 1.73x / 1.67x               0.681/0.531/0.635
    MISO        import     1,538/2,139/2,323 MW vs 0.1/11/24   1.000/1.000/1.000
    LGEE        import     0 MW vs 518/539/549 MW              1.000/1.000/0.986
    NYISO       export     1.00x (exact)                       1.000/1.000/0.972
    ==========  =========  ==================================  ===============

    The repair therefore LOOSENS as well as tightens — the legacy LGEE import
    cap is 0 MW against a measured p90 of ~520-550 MW, and the legacy Carolinas
    export cap is *tighter* than measured (0.67/0.97/0.81x) — which is what a
    consistency repair looks like and what a residual-fitted one would not.
    NYISO reproduces exactly (its border zone holds only its own four ties) —
    the control the measurement carries.

    This construction introduces no parameter: the tie->interface map is an
    identity taken from PJM's own tie labels (rule 5 ``[R-NO-MAGIC]``), and both
    paths read the same measured file at the same percentile (rule 13
    ``[R-MEASURED]`` — reproducible for a forward year, flow-responsive, and
    fitted to nothing).

    ``zone_names`` is retained for signature parity with
    :func:`inject_miso_seam_flow_limit` and the positional call sites; the
    per-neighbour envelope is keyed on the interface, not the model zone.

    Returns ``True`` when at least one seam was capped.
    """
    if direction not in ("import", "export"):
        raise ValueError(f"direction must be 'import' or 'export', got {direction!r}")
    if iso.upper() != "PJM":
        return False
    from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

    pct = PJM_SEAM_FLOW_PERCENTILE if percentile is None else float(percentile)
    neighbors = INTERFACE_NEIGHBORS.get("PJM", [])
    if not neighbors:
        return False

    from market_sim.data.eia_loader import pjm_neighbor_interchange_envelope

    nb_names = [n.name for n in neighbors]
    env = pjm_neighbor_interchange_envelope(year, nb_names, hours, pct)
    if env is None:
        return False
    import_cap, export_cap = env
    # Row key is the neighbour's own name; no border-zone summation.
    cap_idx = {n: i for i, n in enumerate(nb_names)}

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
        cap_data = export_cap if direction == "export" else import_cap
        # The neighbour's own row — one seam, one series, no summation.
        cap_rows = [cap_idx[neighbor.name]] if neighbor.name in cap_idx else []
        if not cap_rows:
            continue
        cap = np.clip(cap_data[cap_rows].sum(axis=0), 0.0, None)

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
