"""Renewable portfolio standard constraints."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from market_sim.config.constants import (
    MISO_RPS_COMPLIANCE_REGIONS,
    RPS_ELIGIBLE_FUELS_BY_ISO,
    STATE_RPS_ACP,
    STATE_RPS_FLOORS,
)


def _interp_floor_knots(floors: dict[int, float], year: int) -> float:
    """Linearly interpolate a knot-year floor trajectory at ``year``.

    Years before the first knot take the first value, years after the last
    take the last value (the edge-hold convention shared by every trajectory
    in :data:`STATE_RPS_FLOORS`; the FH-2 as-of caveat documented there).
    """
    knots = sorted(floors)
    if year <= knots[0]:
        return floors[knots[0]]
    if year >= knots[-1]:
        return floors[knots[-1]]

    for lo, hi in zip(knots, knots[1:]):
        if lo <= year <= hi:
            span = hi - lo
            frac = (year - lo) / span
            return floors[lo] + frac * (floors[hi] - floors[lo])
    return floors[knots[-1]]


def get_rps_target(iso: str, year: int) -> float | None:
    """Return the clean-energy share required of an ISO in a given year.

    The floor trajectory in :data:`STATE_RPS_FLOORS` is defined at a few
    knot years; intermediate years are linearly interpolated. Years before
    the first knot take the first value, years after the last take the
    last value.

    Args:
        iso: ISO identifier (case-insensitive), e.g. ``"CAISO"``.
        year: Simulation year.

    Returns:
        The required clean-energy fraction, or ``None`` when the ISO has no
        renewable portfolio standard defined.
    """
    floors = STATE_RPS_FLOORS.get(iso.upper())
    if floors is None:
        return None
    return _interp_floor_knots(floors, year)


@dataclass(frozen=True)
class RpsRegionArrays:
    """Zone-indexed per-region RPS row inputs for the dispatch LP.

    One entry per compliance region (state standard), rows ordered as
    ``labels``. Built by :func:`build_rps_region_arrays` from the cited
    :data:`MISO_RPS_COMPLIANCE_REGIONS` table against the caller's model zone
    ordering; consumed by ``model.lp`` (``rps_region_zone_mask`` /
    ``rps_region_obligation_frac`` / ``rps_region_acp_price``).

    Attributes:
        labels: Region (state) labels, length ``K``.
        eligible_zone_mask: ``(K, n_zones)`` bool — where a certificate for
            region ``r`` may be *generated* (the row's LHS mask).
        obligation_frac: ``(K, n_zones)`` float — per (region, zone) RHS
            weight: the region's within-zone load share times its target,
            nonzero only in the obligated zone. The LP row's RHS is
            ``sum_z obligation_frac[r, z] * sum_t demand[z, t]``.
        acp_price: ``(K,)`` float — each region's ACP escape price in $/MWh.
    """

    labels: tuple[str, ...]
    eligible_zone_mask: np.ndarray
    obligation_frac: np.ndarray
    acp_price: np.ndarray


def build_rps_region_arrays(
    iso: str, year: int, zone_names: list[str]
) -> RpsRegionArrays | None:
    """Build the per-region RPS row arrays for an ISO-year (FFR-7B Arm 2).

    Resolves the cited per-state compliance-region table (MISO:
    :data:`MISO_RPS_COMPLIANCE_REGIONS`) onto the model's zone ordering:
    each state standard becomes one row with its statutory target
    interpolated at ``year``, its obligated-zone load-share RHS weight, its
    statute's eligibility mask over zones, and its ACP escape price
    (:data:`STATE_RPS_ACP` — MISO's $30 forward REC-price-ceiling proxy for
    every region; per-region ACPs are a refinement, not a requirement,
    FFR-6B §3.4).

    Regions whose interpolated target is zero at ``year`` are still emitted
    (a zero-RHS ``>=`` row is trivially slack and its dual is 0) so the row
    count — and with it the LP layout and cache identity — is a function of
    the table alone, never of the year.

    Args:
        iso: ISO identifier (case-insensitive).
        year: Simulation year (targets interpolated at this year).
        zone_names: Model zone names in LP zone-index order.

    Returns:
        The region arrays, or ``None`` when the ISO has no per-state
        compliance-region table (every ISO but MISO — their single ISO-wide
        row is arithmetically exact, FFR-6B §2.1).

    Raises:
        KeyError: When the table names a zone absent from ``zone_names``
            (a topology drift — fail loud, never silently drop a state).
    """
    if iso.upper() != "MISO":
        return None
    regions = MISO_RPS_COMPLIANCE_REGIONS
    acp = STATE_RPS_ACP[iso.upper()]
    zone_index = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)
    labels = tuple(regions)
    k = len(labels)
    mask = np.zeros((k, n_zones), dtype=bool)
    frac = np.zeros((k, n_zones), dtype=float)
    for r, state in enumerate(labels):
        spec = regions[state]
        target = _interp_floor_knots(spec["floors"], year)
        oz = zone_index[spec["obligated_zone"]]  # KeyError on topology drift
        frac[r, oz] = float(spec["obligated_load_share"]) * float(target)
        for zname in spec["eligible_zones"]:
            mask[r, zone_index[zname]] = True
    return RpsRegionArrays(
        labels=labels,
        eligible_zone_mask=mask,
        obligation_frac=frac,
        acp_price=np.full(k, float(acp)),
    )


def rps_credit_for_zone(
    rps_shadow_price: "float | np.ndarray | None", zone_idx: int | None
) -> float:
    """Return the RPS attribute credit a resource in ``zone_idx`` can earn.

    The REQUIRED per-zone companion of the K-row RPS grain (FFR-7B Arm 2 /
    FFR-6B §3.2): under per-region rows ``rps_shadow_price`` is a per-zone
    vector ``p[z] = max{dual_r : z in eligible_zones(r)}``, and every
    capacity-screen consumer must index it by the candidate's/unit's zone —
    a scalar left broadcast would credit MISO-East's dual to an Arkansas
    candidate and rebuild the very defect the row grain fixed. This is the
    single shared helper all three consumers (``new_entry`` x2,
    ``retirements``) route through.

    Args:
        rps_shadow_price: Scalar (legacy single-row dual — passes through
            unchanged), per-zone ``(n_zones,)`` vector (K-row grain), or
            ``None``/0.
        zone_idx: The resource's LP zone index, or ``None`` when the caller
            has no zone context.

    Returns:
        The $/MWh credit. A vector with no zone context yields 0.0 — never
        the max (that would be the broadcast defect); the armed path always
        carries zone context, so 0.0 only degrades an out-of-contract
        caller conservatively.
    """
    if rps_shadow_price is None:
        return 0.0
    arr = np.asarray(rps_shadow_price)
    if arr.ndim == 0:
        return float(arr)
    if zone_idx is None or not (0 <= int(zone_idx) < arr.shape[0]):
        return 0.0
    return float(arr[int(zone_idx)])


def get_rps_acp(iso: str) -> float | None:
    """Return the RPS Alternative Compliance Payment ceiling for an ISO.

    The ACP (:data:`STATE_RPS_ACP`) is the $/MWh price at which a
    load-serving entity buys out of the renewable portfolio standard when
    physical RECs are short. It is the price ceiling of the REC market, so the
    dispatch LP enters it as the cost of an RPS ACP escape column: this keeps
    the annual RPS row feasible when in-region wind+solar cannot reach the
    target and caps the row's dual (the REC shadow price) at this ceiling.

    Args:
        iso: ISO identifier (case-insensitive), e.g. ``"NEISO"``.

    Returns:
        The ACP ceiling in $/MWh, or ``None`` when the ISO has no RPS defined
        (in which case no ACP escape column is added and the LP is unchanged).
    """
    return STATE_RPS_ACP.get(iso.upper())


def get_rps_eligible_fuels(iso: str) -> tuple[str, ...] | None:
    """Return the statute-defined RPS-row eligible fuel set for an ISO.

    The set (:data:`RPS_ELIGIBLE_FUELS_BY_ISO`, cited per statute) names the
    fuel classes the ISO's governing *renewable-tier* statute counts toward
    its target. Wind and solar are the LP's zone columns and always count;
    names beyond them add the matching thermal-block generator columns to the
    RPS row (``model.lp.rows._resolve_rps_eligible_gen_idx``). FFR-7B Arm 1
    (rule 14 [R-ACCURATE]): the previous universal wind+solar-only convention
    under-counted NYISO by 20.2 pp (CLCPA counts existing hydro) and CAISO by
    7.1 pp (geothermal, biomass), pinning those rows' duals at the ACP ceiling
    (FFR-6B §8).

    Args:
        iso: ISO identifier (case-insensitive), e.g. ``"NYISO"``.

    Returns:
        The eligible fuel-name tuple, or ``None`` when the ISO has no
        entry — the row then keeps the wind+solar-only convention
        (byte-identical LP; PJM/MISO's folded-in convention is adjudicated
        sound to within ~2 pp, FFR-6B §8.2).
    """
    return RPS_ELIGIBLE_FUELS_BY_ISO.get(iso.upper())
