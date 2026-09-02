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
from functools import lru_cache

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
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator

from .new_entry import _make_new_generator
from .retirements import (
    _default_build_zone,
    _thermal_firm_mw,
    net_icr_requirement_armed,
    resolve_adequacy_requirement_mw,
    resolve_internal_supply_accounting_ratio,
    resolve_renewable_capacity_credit,
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
) -> dict[str, float]:
    """Resolved wind/solar credits on the ledger's exact basis (diagnostic).

    The same resolution :func:`accredited_firm_capacity_mw` applies —
    same nameplate computation, same ladder — surfaced so the evolution
    ledger can record the credit each class actually earned this year
    (the CR-3.1 penetration response made observable per run, e.g. for the
    capacity-hindcast before/after diagnostic).
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
            internal += _thermal_firm_mw(g, iso)
    # Internal-supply accounting ratio (capx D31): the measured wedge between
    # this census-accreditation aggregate and the market's own counted supply
    # (MISO: PRA offered Generation ZRC ÷ this ledger's internal firm — see
    # ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO's citation block).
    # Applied to every internal term; the external-tie credit below is
    # already the market's own cleared external quantity and is NOT scaled.
    internal *= resolve_internal_supply_accounting_ratio(iso)
    # Firm imports the ISO's own adequacy ledger counts (one resolver, rule 19):
    # ERCOT/PJM ties absent from topology AND the RA/FCM firm imports of the
    # import-node ISOs (CAISO WECC_import, NEISO HQ_import) — additive, never
    # double-counted against the dispatch node (see :func:`_firm_import_mw`).
    return internal + _firm_import_mw(iso)


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
    if THERMAL_ACCREDITATION_BASIS_BY_ISO.get(iso) == "seasonal_rating":
        credit = 1.0
    else:
        credit = 1.0 - EFORD["gas_ct"]
    credit *= resolve_internal_supply_accounting_ratio(iso)
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
