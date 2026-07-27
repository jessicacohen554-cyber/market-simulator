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
