"""State clean/carbon-free tier constraints (FFR-7B Arm 3 / FFR-6B E-2).

A SECOND, INDEPENDENT row family on the K-row compliance-region machinery
(``model.lp.rows._build_rps_region_rows``) — never a widening of the
renewable RPS row. Each row demands its statute's clean share of its
obligated load from its statute's QUALIFYING SET (which admits nuclear —
the very fuel the renewable row refuses by name under CX-6a — and differs
per statute: MN's carbon-free definition includes hydrogen and biomass,
MI's clean definition admits qualified CCS gas), generated in its
statute's eligible zones, with its own ACP-style feasibility escape.

Since SCN-WS2a (``docs/handoffs/forecast-scenario-readiness-plan-2026-09.md``
§3 WS-2) the family is also the carrier of the **federal CES target row**
(``policy.federal_ces.build_federal_ces_region``): one region spanning every
load zone whose qualifying spec is a per-generator credit-fraction VECTOR
rather than a fuel-name tuple, appended after the state regions through
:func:`append_clean_region`. The family no longer requires the RPS region
grain (the G-S3 coupling relaxation lives in ``model.lp``), so it stands
alone in every ISO or beside MISO's state rows.

Composition with everything that already pays a clean MWh (rule 19
[R-ONE-MECH], FFR-6B §6.4): the clean row's dual enters the EXISTING
``max(eac, rps_shadow)`` attribute doctrine at the capacity screens —
never a sum. A wind MWh satisfying both its renewable row and its clean
row is CORRECT (two constraints, one MWh — the statutes impose separate
obligations the same MWh helps meet), but the generator's credit is the
``max()`` across all attribute buyers, never the sum, per the
one-certificate-sold-once doctrine. ``federal_ces_replaces_state_rps``
suppresses the state clean rows exactly as it suppresses the state RPS
rows (the pure-federal counterfactual stays pure).

THE §45U-vs-CLEAN-DUAL COMPOSITION FOR NUCLEAR IS OPEN AND BLOCKS ARM 3's
ARMING ONLY, NOT ITS IMPLEMENTATION (FFR-6B §6.4, carried verbatim): the
retirement screen sees BOTH §45U and the clean dual, and §45U's own
gross-receipts phase-down (26 U.S.C. §45U(b)(2)) already reduces the
credit as revenue rises — implying phase-down-then-add, not ``max()``.
Unresolved. As implemented, §45U is folded into ``eac_price`` by ``max()``
upstream (``retirements.py``), so the clean dual composes as
``max(max(eac, §45U), clean)`` — the existing doctrine, documented as
provisional pending the owner call.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from market_sim.config.constants import (
    MISO_CLEAN_TIER_REGIONS,
    STATE_RPS_ACP,
)
from market_sim.policy.rps import _interp_floor_knots


def _clean_tier_target(floors: dict[int, float], year: int) -> float:
    """Return a clean-tier target at ``year`` — ZERO before the first knot.

    Deliberately NOT the RPS trajectories' edge-hold convention: a clean
    tier imposes nothing before its first statutory compliance date
    (edge-holding MN's 2030 knot would compel 80% carbon-free in 2026,
    four years before the law requires it). At and after the first knot,
    the shared linear knot interpolation applies.
    """
    if year < min(floors):
        return 0.0
    return _interp_floor_knots(floors, year)


@dataclass(frozen=True)
class CleanRegionArrays:
    """Zone-indexed per-region clean-tier row inputs for the dispatch LP.

    The clean-family sibling of ``policy.rps.RpsRegionArrays``, plus the
    per-region statutory qualifying-fuel sets (data, resolved to generator
    columns inside the row builder — rule 18's spirit).

    Attributes:
        labels: Region (state) labels, length ``K``.
        eligible_zone_mask: ``(K, n_zones)`` bool LHS mask — where region
            ``r``'s clean attribute may be generated.
        obligation_frac: ``(K, n_zones)`` float RHS weights — within-zone
            obligated load share times the region's clean target.
        acp_price: ``(K,)`` float — each row's feasibility-escape price in
            $/MWh (the documented $30 MISO proxy).
        qualifying_fuels: Per-region qualifying spec: a statutory fuel-name
            tuple (``FUEL_TYPE_MAP`` names; nuclear admitted here, unlike the
            renewable row — indicator coefficients in the LP), or an
            ``(n_gen,)`` float credit-fraction vector aligned with the fleet
            the LP solves on (the federal CES row — each generator column
            carries its own fraction). The LP builder accepts both.
        fuel_credit: Optional per-region ``{fuel_name: fraction}`` map used
            ONLY by the consumer-side mapping (:func:`clean_credit_by_fuel`):
            a vector-form region needs it because a per-generator vector has
            no fuel axis for the capacity screens, which are keyed by fuel.
            ``None`` entries (every state region) credit the region's
            qualifying-fuel names at 1.0 exactly as before. ``None`` for the
            whole tuple (the default — every MISO builder output) means every
            region is a name-tuple region.
    """

    labels: tuple[str, ...]
    eligible_zone_mask: np.ndarray
    obligation_frac: np.ndarray
    acp_price: np.ndarray
    qualifying_fuels: "tuple[tuple[str, ...] | np.ndarray, ...]"
    fuel_credit: "tuple[dict[str, float] | None, ...] | None" = None


def build_clean_region_arrays(
    iso: str, year: int, zone_names: list[str]
) -> CleanRegionArrays | None:
    """Build the per-region clean-tier row arrays for an ISO-year (Arm 3).

    Resolves the cited :data:`MISO_CLEAN_TIER_REGIONS` table (MN carbon-free,
    MI clean; Illinois deliberately absent — CEJA is a source-side phase-out,
    not an LSE share obligation, FFR-6B §6.1) onto the model's zone ordering.
    Targets are ZERO before each statute's first knot (:func:`_clean_tier_target`),
    and zero-target years still emit their rows so the row count — and the LP
    layout / cache identity — is a function of the table alone.

    Args:
        iso: ISO identifier (case-insensitive).
        year: Simulation year.
        zone_names: Model zone names in LP zone-index order.

    Returns:
        The region arrays, or ``None`` when the ISO has no clean-tier table
        (every ISO but MISO — the ISO-wide clean row is slack everywhere,
        FFR-6B §6.2, and other ISOs' clean tiers are separate per-ISO
        decisions, rule 25).

    Raises:
        KeyError: When the table names a zone absent from ``zone_names``.
    """
    if iso.upper() != "MISO":
        return None
    regions = MISO_CLEAN_TIER_REGIONS
    acp = STATE_RPS_ACP[iso.upper()]
    zone_index = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)
    labels = tuple(regions)
    k = len(labels)
    mask = np.zeros((k, n_zones), dtype=bool)
    frac = np.zeros((k, n_zones), dtype=float)
    fuels: list[tuple[str, ...]] = []
    for r, state in enumerate(labels):
        spec = regions[state]
        target = _clean_tier_target(spec["floors"], year)
        oz = zone_index[spec["obligated_zone"]]  # KeyError on topology drift
        frac[r, oz] = float(spec["obligated_load_share"]) * float(target)
        for zname in spec["eligible_zones"]:
            mask[r, zone_index[zname]] = True
        fuels.append(tuple(spec["qualifying_fuels"]))
    return CleanRegionArrays(
        labels=labels,
        eligible_zone_mask=mask,
        obligation_frac=frac,
        acp_price=np.full(k, float(acp)),
        qualifying_fuels=tuple(fuels),
    )


def append_clean_region(
    arrays: CleanRegionArrays | None,
    *,
    label: str,
    eligible_zone_mask: np.ndarray,
    obligation_frac: np.ndarray,
    acp_price: float,
    qualifying: "tuple[str, ...] | np.ndarray",
    fuel_credit: "dict[str, float] | None" = None,
) -> CleanRegionArrays:
    """Return ``arrays`` with one more clean region appended (or a new K=1 spec).

    The one composition point of the family (SCN-WS2a): the federal CES row
    — and, later, any second consumer such as the voluntary-demand row
    (SCN-WS3b) — joins the state regions as an extra region in region order,
    so the LP's row/ACP-slot layout and the dual read-back stay the single
    generic K2 path. ``arrays=None`` starts the family (the federal row
    standing alone in an ISO with no state clean tier).

    Args:
        arrays: The existing family (``None`` to start one).
        label: Region label (diagnostics / the runner's dual log).
        eligible_zone_mask: ``(n_zones,)`` bool LHS mask for the new region.
        obligation_frac: ``(n_zones,)`` float RHS weights for the new region.
        acp_price: The new row's escape price in $/MWh.
        qualifying: The new region's qualifying spec (name tuple or
            ``(n_gen,)`` credit vector).
        fuel_credit: The consumer-side ``{fuel: fraction}`` map for a
            vector-form region (see :class:`CleanRegionArrays`).

    Returns:
        A new :class:`CleanRegionArrays`; ``arrays`` is never mutated.
    """
    mask_row = np.asarray(eligible_zone_mask, dtype=bool).reshape(1, -1)
    frac_row = np.asarray(obligation_frac, dtype=float).reshape(1, -1)
    if arrays is None:
        return CleanRegionArrays(
            labels=(label,),
            eligible_zone_mask=mask_row,
            obligation_frac=frac_row,
            acp_price=np.array([float(acp_price)]),
            qualifying_fuels=(qualifying,),
            fuel_credit=(fuel_credit,),
        )
    if mask_row.shape[1] != arrays.eligible_zone_mask.shape[1]:
        raise ValueError(
            f"append_clean_region: zone axis mismatch ({mask_row.shape[1]} vs "
            f"{arrays.eligible_zone_mask.shape[1]})"
        )
    k = len(arrays.labels)
    prior_credit = arrays.fuel_credit if arrays.fuel_credit is not None else (None,) * k
    return CleanRegionArrays(
        labels=arrays.labels + (label,),
        eligible_zone_mask=np.vstack([arrays.eligible_zone_mask, mask_row]),
        obligation_frac=np.vstack([arrays.obligation_frac, frac_row]),
        acp_price=np.concatenate([arrays.acp_price, [float(acp_price)]]),
        qualifying_fuels=arrays.qualifying_fuels + (qualifying,),
        fuel_credit=tuple(prior_credit) + (fuel_credit,),
    )


def _region_fuel_fractions(arrays: CleanRegionArrays) -> "list[dict[str, float]]":
    """Return each region's ``{fuel: credit fraction}`` for the consumer map.

    A name-tuple region credits every named fuel at 1.0 (the pre-SCN-WS2a
    semantics, unchanged); a vector-form region must carry its
    ``fuel_credit`` map, because a per-generator vector has no fuel axis —
    a missing map is a construction error, never a silent zero.
    """
    credit = (
        arrays.fuel_credit
        if arrays.fuel_credit is not None
        else (None,) * len(arrays.labels)
    )
    out: "list[dict[str, float]]" = []
    for r, (spec, fc) in enumerate(zip(arrays.qualifying_fuels, credit)):
        if isinstance(spec, np.ndarray):
            if fc is None:
                raise ValueError(
                    f"clean region {arrays.labels[r]!r} carries a per-generator "
                    "credit vector but no fuel_credit map for the capacity "
                    "screens (CleanRegionArrays.fuel_credit)"
                )
            out.append({f: float(v) for f, v in fc.items() if float(v) > 0.0})
        else:
            out.append({f: 1.0 for f in spec})
    return out


def clean_credit_by_fuel(
    arrays: CleanRegionArrays, region_duals: np.ndarray
) -> dict[str, np.ndarray]:
    """Map clean-row duals to per-(fuel, zone) attribute credits.

    The clean-family analogue of the RPS per-zone consumer vector, with a
    fuel axis the renewable family does not need: a fuel earns region
    ``r``'s dual only where BOTH the zone is in ``r``'s eligibility mask
    AND the fuel is in ``r``'s statutory qualifying set (a gas_cc_ccs unit
    in MISO-West earns nothing from MN's row — MN's carbon-free definition
    does not admit CCS gas). A vector-form region (the federal CES row)
    credits a fuel at ``dual × fraction`` from its ``fuel_credit`` map, so a
    CCS candidate earns 0.95 of the federal dual — the same fraction the
    LP row credits its column at.

    Args:
        arrays: The clean region spec the solve ran with.
        region_duals: ``(K,)`` clean-row duals from the solve.

    Returns:
        ``{fuel_name: (n_zones,) $/MWh}`` — max over the admitting regions,
        0 where none admits. Only fuels credited by at least one region
        appear.
    """
    duals = np.asarray(region_duals, dtype=float)
    fractions = _region_fuel_fractions(arrays)
    out: dict[str, np.ndarray] = {}
    all_fuels = sorted({f for fr in fractions for f in fr})
    for fuel in all_fuels:
        frac = np.array([fr.get(fuel, 0.0) for fr in fractions], dtype=float)
        masked = np.where(
            arrays.eligible_zone_mask & (frac[:, None] > 0.0),
            (duals * frac)[:, None],
            0.0,
        )
        out[fuel] = masked.max(axis=0)
    return out


def clean_credit_for_zone(
    by_fuel: "dict[str, np.ndarray] | None", fuel: str, zone_idx: int | None
) -> float:
    """Return the clean-tier credit a ``fuel`` resource in ``zone_idx`` earns.

    The clean-family sibling of ``policy.rps.rps_credit_for_zone``, shared
    by all capacity-screen consumers. 0.0 when the family is off (``None``),
    the fuel is in no region's qualifying set, or the caller has no zone
    context (never the broadcast max — that would credit MISO-East's dual
    to an Arkansas unit).
    """
    if not by_fuel:
        return 0.0
    vec = by_fuel.get(fuel)
    if vec is None:
        return 0.0
    if zone_idx is None or not (0 <= int(zone_idx) < vec.shape[0]):
        return 0.0
    return float(vec[int(zone_idx)])
