"""Adequacy ledger and the reserve-margin build backstop.

Step 6 of the one-pass capacity evolution
(:func:`market_sim.model.capacity_evolution.evolve.evolve_fleet`; spec §5.1),
split out of the former ``model/capacity.py`` god-module (W-D4, 2026-07-21;
refactor-consolidation plan §5 item 4). Carries the accredited-firm-capacity
ledger (:func:`accredited_firm_capacity_mw` — UCAP/ELCC, incl. wind/solar
pools + storage ELCC), the CR-1 reserve position
(:func:`capacity_reserve_position`), and the reserve-margin adequacy backstop
(:func:`apply_reserve_margin_build`, GATED ``reserve_margin_build_enabled``,
default off). One requirement, two verbs (capacity-economics plan §3.2): the
backstop "builds up to" the same shared requirement the retirement
reliability floor "doesn't retire below"
(:func:`market_sim.model.capacity_evolution.retirements.resolve_adequacy_requirement_mw`).

The full pre-split surface stays importable from
``market_sim.model.capacity`` (the facade; see the package ``__init__``).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache

from market_sim.config.capacity_market import ClearedCapacityPrice
from market_sim.config.constants import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    DEFAULT_MARKET_DESIGN,
    EFORD,
    HYDRO_ACCREDITATION_CREDIT_BY_ISO,
    MARKET_DESIGN,
    QUEUE_CAP_GW,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    RENEWABLE_NQC_CURVES_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator

from .new_entry import _make_new_generator
from .retirements import (
    _default_build_zone,
    _thermal_firm_mw,
    gross_adequacy_requirement_mw,
    net_icr_requirement_armed,
    resolve_adequacy_requirement_mw,
    resolve_demand_response_supply_mw,
    resolve_internal_supply_accounting_ratio,
    resolve_renewable_capacity_credit,
    resolve_thermal_accreditation_basis,
)

logger = logging.getLogger(__name__)


def _renewable_nameplate_by_fuel(
    fleet: list[Generator],
    wind_pool_mw: float,
    solar_pool_mw: float,
    iso: str | None,
) -> dict[str, float]:
    """ISO-wide installed nameplate MW per credit-accredited class.

    The penetration axis for the published ELCC curves (rule 13 — the
    model's own installed share): each class's zonal pool plus any fleet
    units carrying a credit-bearing fuel type. One computation shared by
    :func:`accredited_firm_capacity_mw` and
    :func:`renewable_credits_applied` so the ledger and its diagnostics can
    never disagree on the penetration basis.
    """
    nameplate_by_fuel: dict[str, float] = {
        "wind": float(wind_pool_mw),
        "solar": float(solar_pool_mw),
    }
    for g in fleet:
        if (
            g.fuel_type in RENEWABLE_CAPACITY_CREDIT
            or g.fuel_type in RENEWABLE_ELCC_CURVES_BY_ISO.get(iso or "", {})
            or g.fuel_type in RENEWABLE_NQC_CURVES_BY_ISO.get(iso or "", {})
        ):
            nameplate_by_fuel[g.fuel_type] = nameplate_by_fuel.get(
                g.fuel_type, 0.0
            ) + float(g.pmax_mw)
    return nameplate_by_fuel


def renewable_credits_applied(
    fleet: list[Generator],
    wind_pool_mw: float,
    solar_pool_mw: float,
    iso: str | None,
    peak_demand_mw: float | None = None,
    elcc_curves_enabled: bool = False,
    nqc_curves_enabled: bool = False,
    config: ScenarioConfig | None = None,
    accreditation_year: int | None = None,
) -> dict[str, float]:
    """Resolved wind/solar credits on the ledger's exact basis (diagnostic).

    The same resolution :func:`accredited_firm_capacity_mw` applies —
    same nameplate computation, same ladder — surfaced so the evolution
    ledger can record the credit each class actually earned this year
    (the CR-3.1 penetration response made observable per run, e.g. for the
    capacity-hindcast before/after diagnostic).

    ``config`` / ``accreditation_year`` carry the capx D75-R delivery-year
    vintage axis, and are threaded for the reason this function exists: it is
    the ledger's record of the credit the ledger APPLIED, so a rung the ledger
    resolves and this diagnostic does not would make the two disagree by
    construction (rule 19). Unarmed, or either left ``None``, byte-identical.
    """
    nameplate_by_fuel = _renewable_nameplate_by_fuel(
        fleet, wind_pool_mw, solar_pool_mw, iso
    )
    out: dict[str, float] = {}
    for fuel_type in ("wind", "solar"):
        credit = resolve_renewable_capacity_credit(
            fuel_type,
            iso,
            installed_mw=nameplate_by_fuel.get(fuel_type),
            peak_demand_mw=peak_demand_mw,
            curves_enabled=elcc_curves_enabled,
            nqc_curves_enabled=nqc_curves_enabled,
            config=config,
            year=accreditation_year,
        )
        if credit is not None:
            out[fuel_type] = float(credit)
    return out


def _firm_import_mw(iso: str | None) -> float:
    """Firm import capacity the ISO's own resource-adequacy ledger counts.

    The single resolver (rule 19) for the "firm import the adequacy ledger
    counts" phenomenon, reading :data:`ADEQUACY_EXTERNAL_TIE_FIRM_MW`. Two
    provenance cases share it:

    * ISOs the model has **no** import node for (ERCOT DC ties, PJM cleared BRA
      capacity imports, NYISO Gold Book net capacity purchases — capx D-2) —
      the firm tie is otherwise absent from the persistent fleet. NYISO's
      dispatch-side imports flow through the interchange model
      (``model/interchange/nyiso.py``), never fleet units, so its credit is
      likewise additive.
    * ISOs whose import node **does** live in the dispatch topology (CAISO's
      WECC_import, NEISO's HQ_import — FF-2B). For these the adequacy credit is
      the ISO's RA/FCM firm-import product and is **additive, not
      double-counted**: :func:`accredited_firm_capacity_mw` builds the accredited
      ledger from the persistent ``fleet``, which never contains the import
      pseudo-generators (those exist only in the transient dispatch fleet), so
      this credit is purely additive to the fleet's firm MW and is never derived
      from dispatch flow.

    ``iso=None`` credits nothing (byte-identical legacy behaviour).
    """
    return ADEQUACY_EXTERNAL_TIE_FIRM_MW.get(iso or "", 0.0)


def resolve_hydro_capacity_credit(iso: str | None) -> float:
    """Firm fraction of hydro nameplate the ISO's own RA ledger counts.

    The single resolver (rule 19) for "conventional-hydro accreditation",
    reading :data:`HYDRO_ACCREDITATION_CREDIT_BY_ISO` — each ISO's published
    limited-control / run-of-river / non-dispatchable class factor (CPUC NQC
    technology factor, NYISO CAF, MISO DLOL class UCAP, PJM ELCC class
    rating), or, for ISO-NE which publishes no class rating, the aggregate of
    its own per-resource summer Seasonal Claimed Capability record over the
    model's accreditation basis (see the constant's citation block). ISOs with
    no published hydro accreditation — and ``iso=None`` — fall back to the
    generic published
    class derate :data:`RENEWABLE_CAPACITY_CREDIT`\\ ["hydro"], the same
    neutral fallback every unpublished class already takes (rule 25 spirit).
    """
    published = HYDRO_ACCREDITATION_CREDIT_BY_ISO.get(iso or "")
    if published is not None:
        return float(published)
    return float(RENEWABLE_CAPACITY_CREDIT.get("hydro", 0.0))


@lru_cache(maxsize=64)
def modelled_hydro_nameplate_mw(iso: str, year: int | None = None) -> float:
    """Nameplate MW of the hydro fleet the model actually dispatches.

    The accreditation basis has to be the model's OWN hydro capability, not an
    EIA-860 balancing-authority total (rule 13): this reproduces exactly the
    plant population :func:`market_sim.data.hydro.build_hydro_fleet` puts in the
    LP — the EIA-923-reporting conventional-hydro plants (prime mover ``HY``;
    pumped storage is a storage resource) that resolve to one of the ISO's model
    zones with positive nameplate and positive energy — and sums their MW
    envelope. Hydro is an energy-budget resource that lives only in the
    *transient dispatch* fleet, so it can never be read off the persistent
    ``fleet`` the rest of the ledger is built from (audit FR-3).

    ``year`` is the solve year; like the forecast hydro path it is clamped to
    :data:`~market_sim.data.eia923.EIA923_LATEST_FINAL_VINTAGE`, the newest
    vintage with a COMPLETE (final-release) plant census — vintages after it are
    monthly early releases carrying only the large reporters (CAISO 26 of ~160
    plants in 2025, NEISO 5 of ~166), so an unclamped year would accredit a
    partial fleet. ``None`` (the callers that carry no solve year) resolves at
    that vintage directly.

    Returns ``0.0`` — and logs — when the ISO has no usable hydro budget, so a
    missing input can never fabricate accredited MW. Cached per ``(iso, year)``:
    the ledger is recomputed several times per solve year (ledger, reliability
    floor, backstop, CR-1 position) off a static plant census.
    """
    from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE
    from market_sim.data.hydro import load_hydro_budget

    census_year = (
        EIA923_LATEST_FINAL_VINTAGE
        if year is None
        else min(int(year), EIA923_LATEST_FINAL_VINTAGE)
    )
    try:
        zone_names = set(get_iso_config(iso).zone_names)
    except Exception:
        logger.warning("hydro accreditation: unknown ISO %s — crediting 0 MW", iso)
        return 0.0
    try:
        budget = load_hydro_budget(iso, census_year)
    except (FileNotFoundError, ValueError):
        logger.warning(
            "hydro accreditation: no EIA-923 hydro budget for %s %d — "
            "crediting 0 MW to the accredited ledger",
            iso,
            census_year,
        )
        return 0.0
    total = 0.0
    for i in range(len(budget.plant_ids)):
        # Same three filters build_hydro_fleet applies before making a unit.
        if (
            budget.zones[i] in zone_names
            and float(budget.max_mw[i]) > 0.0
            and float(budget.monthly_energy[i].sum()) > 0.0
        ):
            total += float(budget.max_mw[i])
    return total


def _hydro_firm_mw(
    fleet: list[Generator], iso: str | None, year: int | None = None
) -> float:
    """Accredited firm MW of the ISO's conventional-hydro fleet (FFR-1C).

    ``modelled_hydro_nameplate_mw`` x :func:`resolve_hydro_capacity_credit` —
    the model's own hydro capability at the ISO's published accreditation, the
    hydro analogue of the wind/solar pool credits. Closes audit finding FR-3 /
    gap-register R5c: hydro was dispatched but contributed 0 MW to
    :func:`accredited_firm_capacity_mw` for every ISO, which FF-2B measured as
    the dominant cause of the NYISO base-year I7 FAIL and a major CAISO
    contributor (docs/handoffs/ff-2b-adequacy-basis-2026-07.md §4).

    **No double-count** (the ``_firm_import_mw`` discipline): the persistent
    ``fleet`` is not supposed to carry hydro at all, but should any ISO/path
    ever place hydro Generators in it — where the existing ``_credit`` loop
    already accredits them — that nameplate is netted off the pool here, so the
    pool only ever credits the capability the fleet loop did not.

    ``iso=None`` credits nothing (byte-identical legacy behaviour: the legacy
    generic basis has no ISO to resolve a hydro fleet for).
    """
    if iso is None:
        return 0.0
    pool_mw = modelled_hydro_nameplate_mw(iso, year)
    fleet_hydro_mw = sum(
        float(g.pmax_mw) for g in fleet if getattr(g, "fuel_type", None) == "hydro"
    )
    net_pool_mw = max(0.0, pool_mw - fleet_hydro_mw)
    return net_pool_mw * resolve_hydro_capacity_credit(iso)


def accredited_firm_capacity_mw(
    fleet: list[Generator],
    wind_pool_mw: float = 0.0,
    solar_pool_mw: float = 0.0,
    storage_firm_mw: float = 0.0,
    iso: str | None = None,
    peak_demand_mw: float | None = None,
    elcc_curves_enabled: bool = False,
    year: int | None = None,
    nqc_curves_enabled: bool = False,
    config: ScenarioConfig | None = None,
    accreditation_year: int | None = None,
) -> float:
    """Return the system's accredited firm (ELCC/UCAP) capacity in MW.

    Each resource contributes the firm fraction of its nameplate it can be
    relied on for at the system peak, on the ISO's own published counting
    convention when ``iso`` is given: thermal at ``1 - EFORd`` (UCAP) or at
    its seasonal rating (:func:`_thermal_firm_mw` /
    :data:`THERMAL_ACCREDITATION_BASIS_BY_ISO` — ERCOT's CDR basis),
    variable renewables at their capacity credit
    (:func:`resolve_renewable_capacity_credit` — the ISO's published
    class-average NQC accreditation when ``nqc_curves_enabled``
    (:data:`RENEWABLE_NQC_CURVES_BY_ISO`, CAISO only, default off),
    penetration-indexed published ELCC curve when ``elcc_curves_enabled``,
    per-ISO point override, generic :data:`RENEWABLE_CAPACITY_CREDIT`
    fallback), storage
    at its duration-dependent ELCC (passed in pre-accredited as
    ``storage_firm_mw``, since the ELCC helper lives in the storage module),
    conventional hydro at the ISO's published hydro accreditation
    (:func:`_hydro_firm_mw` / :data:`HYDRO_ACCREDITATION_CREDIT_BY_ISO` — the
    model's own dispatched hydro capability resolved from the hydro budget
    loader for ``year``, never from the persistent ``fleet``, which structurally
    never contains hydro; FFR-1C, audit FR-3),
    plus the firm import capacity the ISO's own adequacy ledger counts
    (:func:`_firm_import_mw` / :data:`ADEQUACY_EXTERNAL_TIE_FIRM_MW` — ERCOT's DC
    ties, PJM's CIL-governed cleared BRA imports, NYISO's Gold Book net
    capacity purchases on the UCAP requirement basis, and the RA/FCM firm
    imports of the import-node ISOs CAISO/NEISO, credited additively without
    double-counting the dispatch import node). Wind/solar
    held in the zonal pools (not Generators) are passed as ``wind_pool_mw``
    / ``solar_pool_mw``. The whole INTERNAL aggregate (everything but the
    firm-import credit) is then scaled by the ISO's measured internal-supply
    accounting ratio
    (:func:`~market_sim.model.capacity_evolution.retirements.
    resolve_internal_supply_accounting_ratio` — capx D31; MISO 0.8546, the
    PRA offered-Generation-to-census wedge; every other ISO the neutral
    1.0).

    For the CR-3.1 curves each credit-accredited class's penetration is its
    ISO-WIDE installed nameplate — the zonal pool plus any fleet units of
    that fuel — against ``peak_demand_mw``, both the model's own quantities
    (rule 13). One credit per class per call: every MW of a class is
    accredited at the same class rating, exactly the ISOs' own class-rating
    construction. ``iso=None`` reproduces the legacy generic basis
    byte-identically (UCAP thermal, generic credits, no tie MW), and
    ``elcc_curves_enabled=False`` (or an unavailable axis quantity) is the
    frozen-penetration byte-compat mode — the pre-CR-3.1 point basis.

    ``config`` and ``accreditation_year`` (both optional, default ``None``)
    carry the two capx D48 gated repairs and NOTHING else: (i) the thermal
    basis is resolved per delivery year under
    ``config.pjm_accreditation_design_vintage``
    (:func:`~market_sim.model.capacity_evolution.retirements.
    resolve_thermal_accreditation_basis` — UCAP before PJM's 2025/26 reform,
    the registry basis after); (ii) under ``config.pjm_demand_response_supply``
    the ISO's published Demand Resource supply for that delivery year
    (:func:`~market_sim.model.capacity_evolution.retirements.
    resolve_demand_response_supply_mw`) is ADDED as a market-counted term —
    outside the internal-supply accounting ratio, exactly as the firm-import
    credit is — and the requirement side stops netting it from the peak.
    ``accreditation_year`` is deliberately separate from ``year`` (which
    resolves the hydro budget) so a caller that never threaded ``year``
    keeps its hydro term byte-identical while threading the delivery year
    the two gates key on. Unarmed, or with either left ``None``, both terms
    are inert and the ledger is byte-identical.
    """
    nameplate_by_fuel = _renewable_nameplate_by_fuel(
        fleet, wind_pool_mw, solar_pool_mw, iso
    )

    def _credit(fuel_type: str) -> float | None:
        return resolve_renewable_capacity_credit(
            fuel_type,
            iso,
            installed_mw=nameplate_by_fuel.get(fuel_type),
            peak_demand_mw=peak_demand_mw,
            curves_enabled=elcc_curves_enabled,
            nqc_curves_enabled=nqc_curves_enabled,
            # capx D75-R: the delivery-year vintage axis rides the SAME
            # ``config`` / ``accreditation_year`` pair the D48 thermal half
            # already threads (rule 19), so supply's two halves can never be
            # devintaged apart. Unarmed, inert and byte-identical.
            config=config,
            year=accreditation_year,
        )

    internal = float(storage_firm_mw)
    internal += wind_pool_mw * (_credit("wind") or 0.0)
    internal += solar_pool_mw * (_credit("solar") or 0.0)
    # Conventional hydro at the ISO's published accreditation (FFR-1C / FR-3):
    # dispatched via the energy-budget path, so it is absent from `fleet` and
    # must be credited as its own pool, exactly like wind/solar above.
    internal += _hydro_firm_mw(fleet, iso, year)
    for g in fleet:
        credit = _credit(g.fuel_type)
        if credit is not None:
            internal += g.pmax_mw * credit
        else:
            internal += _thermal_firm_mw(g, iso, config, accreditation_year)
    # Internal-supply accounting ratio (capx D31): the measured wedge between
    # this census-accreditation aggregate and the market's own counted supply
    # (MISO: PRA offered Generation ZRC ÷ this ledger's internal firm — see
    # ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO's citation block).
    # Applied to every internal term; the external-tie credit below is
    # already the market's own cleared external quantity and is NOT scaled.
    # capx D51: ``config`` threads the default-off dated-net gate (the same
    # ratio re-identified on the dates-ON fleet); ``None`` keeps D31's value.
    internal *= resolve_internal_supply_accounting_ratio(iso, config)
    # Firm imports the ISO's own adequacy ledger counts (one resolver, rule 19):
    # ERCOT/PJM ties absent from topology AND the RA/FCM firm imports of the
    # import-node ISOs (CAISO WECC_import, NEISO HQ_import) — additive, never
    # double-counted against the dispatch node (see :func:`_firm_import_mw`).
    # capx D48 DR-as-supply (gated, default off): the ISO's published Demand
    # Resource supply for the delivery year — the market's own counted
    # quantity, so, like the firm-import credit, it is NOT scaled by the
    # internal-supply ratio. The hold-last branch scales by the gross
    # (un-netted) requirement built on the same peak/year the position uses.
    dr_supply_mw = 0.0
    if config is not None and iso is not None and accreditation_year is not None:
        dr_mw = resolve_demand_response_supply_mw(
            config,
            iso,
            accreditation_year,
            gross_adequacy_requirement_mw(
                config, iso, peak_demand_mw, accreditation_year
            )
            if peak_demand_mw > 0.0
            else None,
        )
        if dr_mw is not None:
            dr_supply_mw = float(dr_mw)
    return internal + _firm_import_mw(iso) + dr_supply_mw


def capacity_reserve_position(
    fleet: list[Generator],
    wind_pool_mw: float,
    solar_pool_mw: float,
    storage_firm_mw: float,
    config: ScenarioConfig,
    iso: str,
    peak_demand_mw: float,
    year: int | None = None,
) -> float | None:
    """Return the system's accredited reserve position for the CR-1 curve.

    ``accredited_firm_capacity_mw / resolve_adequacy_requirement_mw`` — the
    SAME accreditation ledger and the SAME requirement the retirement
    reliability floor and the reserve-margin backstop already compute (one
    requirement, one basis, rule 19), so the sloped-demand-curve position feeds
    the three capacity screens off a signal consistent with the adequacy
    mechanisms it sits beside. A value of ``1.0`` means the accredited fleet is
    exactly at the requirement (curve pays net-CONE); ``> 1.0`` is long (price
    slides toward zero), ``< 1.0`` is short (price rises toward the cap).

    ``year`` is threaded to the requirement resolver so a published Forecast
    Pool Requirement of the matching delivery year devintages the position's
    denominator (R2); ``None`` keeps the fallback ``(1 + PRM) x ratio``.

    Returns ``None`` when the peak or the requirement is non-positive, so the
    caller (and ``MarketDesign.capacity_price_per_firm_mw_yr``) cleanly falls
    back to the fixed price. Consumed only when
    ``config.capacity_market_clearing`` is on; the runner computes it once on
    the entering-year fleet and threads the one value into all three screens.
    """
    if peak_demand_mw <= 0.0:
        return None
    requirement_mw = resolve_adequacy_requirement_mw(config, iso, peak_demand_mw, year)
    if requirement_mw <= 0.0:
        return None
    accredited_mw = accredited_firm_capacity_mw(
        fleet,
        wind_pool_mw,
        solar_pool_mw,
        storage_firm_mw,
        iso=iso,
        peak_demand_mw=peak_demand_mw,
        elcc_curves_enabled=config.renewable_elcc_curves,
        year=year,
        nqc_curves_enabled=config.caiso_nqc_accreditation,
        config=config,
        accreditation_year=year,
    )
    return curve_convention_position(config, iso, accredited_mw / requirement_mw)


def curve_convention_position(
    config: ScenarioConfig | None, iso: str | None, position: float
) -> float:
    """Re-express a DR-netted reserve position on the ISO's curve x-convention.

    The capx D40 R-B half of the NEISO position repair
    (``FINDING-capx-d33-neiso-position-2026-09-02.md`` §1 / §4 R-B — "one
    convention for position and curve, land WITH R-A"). The model's position
    is ``firm / requirement`` on the NET convention: DR is netted from the
    requirement and absent from the numerator. ISO-NE's published MRI demand
    curve — and hence every R2 vintage point (``_NEISO_MRI_CLEARING_POINTS``,
    x = cleared MW ÷ Net ICR) — is on the RAW convention: demand-capacity
    resources are IN the cleared quantity and the Net ICR is un-netted.
    Evaluating a net-convention position on a raw-convention curve mis-pairs
    the two (D33 §2: +0.4 to +2.3 reserve-ratio points, growing with surplus,
    so it maximally inflates exactly the long years the $0 readings occur in).

    With ``f`` the ISO's DR fraction of the Net ICR
    (:data:`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`) and ``R`` the raw
    requirement, ``firm = pos_net × R × (1 − f)`` and the DR quantity is
    ``f × R``, so the raw-convention position is

        pos_raw = (firm + f·R) / R = f + (1 − f) · pos_net

    — purely algebraic in ``f``, no further data, and it holds identically on
    the in-table (absolute Net ICR) and hold-last (ratio) paths because DR is
    ``f × R`` on both. ``pos = 1.0`` is a fixed point (at the requirement the
    curve pays net-CONE on either convention); positions away from 1 are
    compressed by ``(1 − f)``. Applied ONLY when
    :func:`~market_sim.model.capacity_evolution.retirements.
    net_icr_requirement_armed` holds (the default-OFF gate + the NEISO
    registry), so every other ISO and every unarmed run is byte-identical.
    The reliability floor and the build backstop are untouched — they test
    ``firm ≥ requirement``, which is convention-invariant.
    """
    if not net_icr_requirement_armed(config, iso):
        return position
    dr_fraction = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO.get(iso or "", 0.0)
    return dr_fraction + (1.0 - dr_fraction) * position


# --------------------------------------------------------------------------- #
# capx D57 (2026-09-05): the PJM clearing half — DESIGN-capx-d54-pjm-clearing-
# half-2026-09-05.md §3. Clear the fleet's net-ACR sell-offer stack against the
# delivery year's published VRR curve; the cleared set earns the clearing price
# on its accredited MW, the uncleared set earns $0. GATED (default off) behind
# ScenarioConfig.capacity_market_supply_clearing_by_iso, resolved through
# config.capacity_market.resolve_capacity_market_supply_clearing. Zero free
# parameters (design §3.7): every operand is the retirement screen's own bar
# and E&AS margin, the D48 accreditation seam, and the published curve.
# --------------------------------------------------------------------------- #

#: One sell offer on the stack: ``(unit_id, fuel, offer $/MW-day on ACCREDITED
#: MW, accredited MW, nameplate MW)``. The offer is the unit's net Avoidable
#: Cost Rate proxy — ``max(0, going_forward_cost − E&AS net revenue) /
#: (accredited_mw × 365)`` (design §3.2) — computed by the retirement screen
#: from the same two operands its bar test consumes.
CapacityOffer = tuple[str, str, float, float, float]

#: Bisection depth for the marginal step (design §3.4 rule 4): 60 halvings of a
#: unit's accredited MW resolve the cleared quantity far below 1e-9 MW.
_CLEARING_BISECTION_STEPS: int = 60


@dataclass(frozen=True)
class CapacityClearing:
    """The result of clearing the sell-offer stack against the VRR curve.

    Design §3.4 / §3.5 (capx D54 → D57). ``price_usd_per_mw_day`` is the
    Resource Clearing Price; ``cleared_mw`` the cleared quantity (price takers
    plus every cleared offer, the marginal unit counted in full — the
    whole-unit convention, design §3.4 rule 4); ``cleared_position`` is
    ``cleared_mw / requirement_mw``; ``census_mw`` is ``price_takers_mw +
    offered_mw``, i.e. the accredited census the un-gated evaluation prices
    (invariant I1: with every offer at $0, or a curve above every offer,
    ``cleared_mw == census_mw`` and the price is the census price).
    ``how`` names which rule set the price: ``zero_block_past_zero_cross``,
    ``curve_sets_price_between_offers``, ``marginal_offer_sets_price`` or
    ``all_offers_clear_curve_sets_price``. Per-unit ``offer_usd_per_mw_day``
    and ``accredited_mw`` are carried so the screen settles each unit and the
    ledger records the stack without replaying the solve.
    """

    price_usd_per_mw_day: float
    cleared_mw: float
    cleared_position: float
    price_takers_mw: float
    offered_mw: float
    requirement_mw: float
    census_mw: float
    census_position: float
    how: str
    marginal_unit_id: str | None
    cleared_unit_ids: frozenset[str]
    uncleared_firm_mw_by_fuel: dict[str, float]
    uncleared_nameplate_mw_by_fuel: dict[str, float]
    offer_usd_per_mw_day: dict[str, float]
    accredited_mw: dict[str, float]
    fuel_by_unit: dict[str, str]

    @property
    def price_per_firm_mw_yr(self) -> float:
        """The clearing price in $/firm-MW-yr — the shared seam's unit."""
        return self.price_usd_per_mw_day * 365.0

    @property
    def n_offers(self) -> int:
        """Number of price-forming offers on the stack (screened thermal units)."""
        return len(self.offer_usd_per_mw_day)

    @property
    def n_uncleared(self) -> int:
        """Number of offers the auction did not clear."""
        return self.n_offers - sum(
            1 for uid in self.offer_usd_per_mw_day if uid in self.cleared_unit_ids
        )

    def as_price(self) -> ClearedCapacityPrice:
        """The pre-priced object the entry / storage price takers consume."""
        return ClearedCapacityPrice(
            price_per_firm_mw_yr=self.price_per_firm_mw_yr,
            cleared_position=self.cleared_position,
            census_position=self.census_position,
        )

    def as_ledger(self) -> dict:
        """The additive, decision-neutral ``evolution_<year>.json`` block
        (design §3.5 — ``capacity_clearing``). Plain JSON types only."""
        return {
            "price_usd_per_mw_day": round(self.price_usd_per_mw_day, 6),
            "price_per_firm_mw_yr": round(self.price_per_firm_mw_yr, 3),
            "cleared_mw": round(self.cleared_mw, 3),
            "cleared_position": round(self.cleared_position, 6),
            "price_takers_mw": round(self.price_takers_mw, 3),
            "offered_mw": round(self.offered_mw, 3),
            "requirement_mw": round(self.requirement_mw, 3),
            "census_mw": round(self.census_mw, 3),
            "census_position": round(self.census_position, 6),
            "uncleared_mw_by_fuel": {
                k: round(v, 3)
                for k, v in sorted(self.uncleared_firm_mw_by_fuel.items())
            },
            "uncleared_nameplate_mw_by_fuel": {
                k: round(v, 3)
                for k, v in sorted(self.uncleared_nameplate_mw_by_fuel.items())
            },
            "n_offers": self.n_offers,
            "n_uncleared": self.n_uncleared,
            "marginal_unit": self.marginal_unit_id,
            "how": self.how,
            # The whole sell-offer stack (sorted ascending by (offer, unit_id)),
            # so the E&AS-operand measurement — how many firm MW of offers sit
            # above any price, by fuel — reads off the ledger for CLEARED units
            # too, which have no pipeline_events row. Output-only.
            "offer_stack": [
                [
                    uid,
                    self.fuel_by_unit.get(uid, ""),
                    round(o, 4),
                    round(self.accredited_mw.get(uid, 0.0), 3),
                    uid in self.cleared_unit_ids,
                ]
                for o, uid in sorted(
                    (o, uid) for uid, o in self.offer_usd_per_mw_day.items()
                )
            ],
        }


def capacity_supply_curve(
    config: ScenarioConfig, iso: str, year: int | None
) -> "Callable[[float], float]":
    """Return the demand side of the clearing as ``position -> $/firm-MW-yr``.

    The SAME curve evaluation the census path prices through —
    :meth:`~market_sim.config.capacity_market.MarketDesign.
    capacity_price_per_firm_mw_yr` on the ISO's registry design at the
    delivery year's vintage, on the ISO's curve x-convention
    (:func:`curve_convention_position`) — so the clearing and the census
    evaluation can never read two curves (rule 19; invariant I1 is structural).
    Flat-extrapolated at the cap below the first published point and at the
    last point above, exactly as :func:`~market_sim.config.capacity_market.
    evaluate_demand_curve` does (design §3.3).
    """
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)

    def _price(position: float) -> float:
        return float(
            design.capacity_price_per_firm_mw_yr(
                config,
                curve_convention_position(config, iso, float(position)),
                iso=iso,
                year=year,
            )
        )

    return _price


def clear_capacity_supply_stack(
    offers: "Sequence[CapacityOffer]",
    price_takers_mw: float,
    requirement_mw: float,
    curve_price_per_firm_mw_yr: "Callable[[float], float]",
) -> CapacityClearing:
    """Clear a sell-offer stack against a capacity demand curve (design §3.4).

    Pure and deterministic — no LP, no iteration beyond one sort and at most
    one bisection on a monotone segment (rule 10 untouched). ``offers`` are
    :data:`CapacityOffer` tuples; ``price_takers_mw`` is the $0 block ``Q_0``
    (every accredited MW the ledger counts that is not a screened thermal
    unit — VRE / hydro / storage / firm imports / DR / screen-exempt units);
    ``requirement_mw`` is the shared adequacy requirement ``R``;
    ``curve_price_per_firm_mw_yr(position)`` is the demand side in
    $/firm-MW-yr at ratio ``Q / R`` (:func:`capacity_supply_curve`). Prices
    are compared in $/MW-day (``curve / 365``).

    The walk, with ``q`` the cumulative cleared MW before offer ``g`` and
    ``D(Q)`` the curve at ``Q``, offers sorted ascending by ``(offer,
    unit_id)`` (the price-taking block is the first step at $0):

    1. ``D(Q_0) ≤ 0`` — the price takers alone pass the zero-cross: price 0,
       cleared ``Q_0`` plus every $0 offer (ties at $0 all clear, as the
       auction does), every positive offer uncleared.
    2. ``D(q) < offer_g`` — the curve crosses on the vertical rise between the
       previous offer and this one: price ``D(q)`` (the curve sets it),
       cleared ``q``, ``g`` and everything above it uncleared.
    3. ``D(q + A_g) ≥ offer_g`` — ``g`` clears in full; continue.
    4. otherwise the curve crosses inside ``g``'s step: price ``offer_g`` (the
       marginal offer sets it), cleared quantity the ``Q ∈ (q, q + A_g]`` with
       ``D(Q) = offer_g`` (bisection); the marginal unit is CLEARED in full
       for the screen (whole-unit grain, design §3.4 rule 4) and everything
       above it is uncleared.
    5. the walk exhausts the stack (every offer below the curve — a SHORT
       market): price ``D(Σ)`` at the full accredited quantity, everything
       cleared — the census evaluation exactly (invariant I1).

    Invariants (design §3.6, asserted by tests): I1 census recovery; I2 the
    failing set of a screen settled on this result equals the uncleared set
    (marginal unit excepted); I3 ``0 ≤ price ≤ D(0)`` and ``Q_0 ≤ cleared ≤
    Q_0 + Σ A_g``; I4 monotone in every offer and in ``R``.
    """
    q0 = max(0.0, float(price_takers_mw))
    req = float(requirement_mw)
    if req <= 0.0:
        raise ValueError("clear_capacity_supply_stack: requirement_mw must be > 0")

    def _d(quantity_mw: float) -> float:
        # $/MW-day at the cumulative quantity, on the position axis.
        return curve_price_per_firm_mw_yr(quantity_mw / req) / 365.0

    stack = sorted(
        (
            (float(o), str(uid), str(fuel), float(a_mw), float(nameplate))
            for uid, fuel, o, a_mw, nameplate in offers
        ),
        key=lambda r: (r[0], r[1]),
    )
    offer_by_unit = {uid: o for o, uid, _f, _a, _n in stack}
    fuel_by_unit = {uid: f for _o, uid, f, _a, _n in stack}
    accredited_by_unit = {uid: a for _o, uid, _f, a, _n in stack}
    offered_mw = sum(a for _o, _u, _f, a, _n in stack)
    census_mw = q0 + offered_mw

    cleared: set[str] = set()
    marginal: str | None = None
    q = q0
    if _d(q0) <= 0.0:
        # Rule 1: only the $0 steps clear — ties at $0 are inside Q_0's step.
        for o, uid, _f, a, _n in stack:
            if o <= 0.0:
                cleared.add(uid)
                q += a
        price, how = 0.0, "zero_block_past_zero_cross"
    else:
        price, how = None, ""
        for o, uid, _f, a, _n in stack:
            lo_q, hi_q = q, q + a
            if _d(lo_q) < o:
                price, how = _d(lo_q), "curve_sets_price_between_offers"
                break
            if _d(hi_q) >= o:
                cleared.add(uid)
                q = hi_q
                continue
            # Rule 4: the curve crosses inside this step — bisection on the
            # monotone (non-increasing) segment for D(Q) = offer.
            lo, hi = lo_q, hi_q
            for _ in range(_CLEARING_BISECTION_STEPS):
                mid = 0.5 * (lo + hi)
                if _d(mid) >= o:
                    lo = mid
                else:
                    hi = mid
            cleared.add(uid)
            marginal = uid
            q = lo
            price, how = o, "marginal_offer_sets_price"
            break
        if price is None:
            # Rule 5: every offer below the curve — the SHORT market; the
            # clearing IS the census evaluation.
            price, how = _d(q), "all_offers_clear_curve_sets_price"

    unc_firm: dict[str, float] = {}
    unc_name: dict[str, float] = {}
    for _o, uid, fuel, a, nameplate in stack:
        if uid not in cleared:
            unc_firm[fuel] = unc_firm.get(fuel, 0.0) + a
            unc_name[fuel] = unc_name.get(fuel, 0.0) + nameplate
    return CapacityClearing(
        price_usd_per_mw_day=float(price),
        cleared_mw=float(q),
        cleared_position=float(q) / req,
        price_takers_mw=q0,
        offered_mw=offered_mw,
        requirement_mw=req,
        census_mw=census_mw,
        census_position=census_mw / req,
        how=how,
        marginal_unit_id=marginal,
        cleared_unit_ids=frozenset(cleared),
        uncleared_firm_mw_by_fuel=unc_firm,
        uncleared_nameplate_mw_by_fuel=unc_name,
        offer_usd_per_mw_day=offer_by_unit,
        accredited_mw=accredited_by_unit,
        fuel_by_unit=fuel_by_unit,
    )


def resolve_reserve_margin_build_enabled(config: ScenarioConfig, iso: str) -> bool:
    """Resolve whether the reserve-margin adequacy backstop fires for ``iso``.

    Market-design-dependent resolution (G-41, PJM hindcast I7 decision
    2026-07-06 — owner-approved market-design-dependent variant). The
    ``ScenarioConfig.reserve_margin_build_enabled`` field is tri-state:

    * ``True`` / ``False`` — explicit override, honoured verbatim (rule 21: the
      knob lands in ``run_config.json`` and a scenario can force it either way).
    * ``None`` (default) — resolve per market design: ON when the ISO's design
      procures capacity to an adequacy requirement
      (``MARKET_DESIGN[iso].capacity_market`` — PJM/MISO/NYISO/NEISO/CAISO; the
      LP analogue of RPM's absolute-IRM procurement), OFF for energy-only ERCOT
      and for ISOs absent from :data:`MARKET_DESIGN` (conservative — the real
      energy-only market has no absolute reliability floor: an under-remunerated
      unit exits and ORDC/scarcity prices the resulting adequacy, so a
      force-build backstop would manufacture firm MW the market never procures,
      rule 1).

    Energy-only ERCOT and any ``None``-default forecast on an unknown ISO
    resolve OFF, so the pre-G-41 default-off behaviour is byte-identical there;
    the capacity-market ISOs are where the backstop newly engages by default.

    **WHERE THE DISABLED BACKSTOP SURFACES — read this before treating an
    ERCOT I3 breach as a dispatch defect** (audit finding FR-6,
    ``docs/forecast-readiness-audit-2026-07.md``; measured by lane D4-I3,
    ``docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md``). Returning
    ``False`` here is a deliberate market-design choice, not an omission, and
    it has a deliberate consequence: energy-only ERCOT has no corrective for a
    year the entry screen under-builds. Capacity evolution is one-pass by rule
    10 [R-ONE-PASS], so nothing re-opens the build decision within the year,
    and the LP must still balance every hour — the residual therefore leaves
    through the one unbounded column that can absorb it, load slack (bounded
    ``0 <= Slack <= inf`` in :func:`model.lp.bounds.build_variable_bounds` at the
    ``_slack_off`` seam, priced at ``voll`` in
    :func:`model.lp.costs.build_cost_vector`). That slack is what forecast invariant
    I3 (``scripts/check_forecast_invariants.check_i3_unserved_dump``) reports
    as "slack N % of load". So an ERCOT I3 breach is, by construction, a
    *capacity-evolution* signal read off the *dispatch* — an under-build made
    visible — and the D4-I3 measurement bears that out: across eleven
    committed ERCOT T1-H records the slack is monotone in the year's total
    build (zero at >= 48.0 GW added, 0.01 % at 39.9 GW, 0.07 % at 27.8 GW)
    and in the resulting reserve margin. Do NOT repair such a breach by
    arming this backstop for ERCOT (that is the force-build the paragraph
    above rules out, rule 1 [R-STRUCT]) and do NOT repair it in the LP; the
    admissible object is the entry screen that chose the build.

    Args:
        config: Scenario config carrying the tri-state override field.
        iso: ISO identifier.

    Returns:
        ``True`` if the backstop should fire, else ``False``.
    """
    override = config.reserve_margin_build_enabled
    if override is not None:
        return bool(override)
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    return bool(design.capacity_market)


def apply_reserve_margin_build(
    fleet: list[Generator],
    firm_capacity_mw: float,
    peak_demand_mw: float,
    year: int,
    config: ScenarioConfig,
    iso: str,
    rate_limit_mw: float | None = None,
) -> tuple[list[Generator], float]:
    """Force-build firm capacity to meet the planning reserve margin.

    The structural adequacy backstop (ReEDS/NEMS/CDR): after the economic
    new-entry screen, if accredited firm capacity is below the shared
    requirement (:func:`resolve_adequacy_requirement_mw` — firm peak x
    (1 + PRM) on the ISO's own counting convention) the residual gap is
    filled with the cheapest firm dispatchable resource (a ``gas_ct``
    peaker), so adequacy holds even when under-priced energy/scarcity
    revenue would otherwise under-build. The economic screen still owns the
    profitable build; this only covers the shortfall.

    Sized on nameplate (the gap is a firm-MW gap, so nameplate =
    gap / (1 - EFORd_gas_ct) for UCAP-basis ISOs, gap itself for
    seasonal-rating ISOs). The build is capped at the ISO's annual
    interconnection-queue throughput so a single year cannot add unbounded
    capacity. Returns ``(fleet, built_mw)``; a no-op (built 0) when disabled,
    when the margin is already met, or when the queue cap is exhausted.

    ``rate_limit_mw`` (FF-2A item 2 / BLK-10, ``entry_rate_limits``): the
    remaining gas_ct growth-ladder budget for the year — the measured
    interconnection-throughput bound (ENTRY_GROWTH_LIMIT_MULTIPLE × the
    prior-max annual gas_ct build, net of this year's economic gas_ct
    decisions: the backstop and economic entry draw ONE physical queue,
    rule 19). Replaces the full-deficit-in-one-step over-fire: a deficit
    larger than the year's deliverable throughput carries to next year's
    screen (and the ladder rises as builds land), so a large exit wave is
    rebuilt over several years instead of one — the measured RC-1A/BLK-10
    signature (PJM 2025: 6.43 GW pre-R-NEW, 2.5 GW post-R-NEW, vs actual
    0.447 GW). ``None`` (gate off) keeps the queue-cap-only sizing
    byte-identically. The sizing stays need-proportional: never more than
    the nameplate gap.
    """
    if not resolve_reserve_margin_build_enabled(config, iso) or peak_demand_mw <= 0.0:
        return fleet, 0.0
    # Shared requirement resolution (one requirement, two verbs — plan §3.2):
    # the same firm-peak x (1 + PRM) construction the retirement reliability
    # floor uses, on the ISO's own counting convention.
    required = resolve_adequacy_requirement_mw(config, iso, peak_demand_mw, year)
    firm_gap = required - firm_capacity_mw
    if firm_gap <= 0.0:
        return fleet, 0.0

    # Nameplate needed to close a firm-MW gap, on the ISO's accreditation
    # basis: seasonal-rating ISOs count the new CT at nameplate; UCAP ISOs
    # derate it by EFORd. The internal-supply accounting ratio (capx D31)
    # rides along so the built unit's LEDGER contribution — which carries the
    # ratio in accredited_firm_capacity_mw — actually closes the gap (one
    # basis, rule 19).
    # capx D48: the basis is resolved per delivery year (byte-identical
    # unarmed — the resolver returns the registry basis).
    if resolve_thermal_accreditation_basis(iso, config, year) == "seasonal_rating":
        credit = 1.0
    else:
        credit = 1.0 - EFORD["gas_ct"]
    credit *= resolve_internal_supply_accounting_ratio(iso, config)
    nameplate_needed = firm_gap / credit if credit > 0.0 else firm_gap
    iso_config = get_iso_config(iso)
    queue_cap_mw = QUEUE_CAP_GW.get(iso_config.name, 0.0) * 1000.0
    build_mw = (
        min(nameplate_needed, queue_cap_mw) if queue_cap_mw > 0.0 else nameplate_needed
    )
    if rate_limit_mw is not None:
        build_mw = min(build_mw, max(0.0, float(rate_limit_mw)))
    if build_mw <= 0.0:
        return fleet, 0.0

    zone = _default_build_zone(iso_config)
    unit = _make_new_generator(
        "gas_ct", build_mw, zone, year, 0, config, iso_config.name
    )
    unit.unit_id = f"gas_ct_adequacy_{year}"
    unit.name = unit.unit_id
    return fleet + [unit], build_mw
