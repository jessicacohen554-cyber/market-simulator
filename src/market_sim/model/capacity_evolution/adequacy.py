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

from market_sim.config.constants import (
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    DEFAULT_MARKET_DESIGN,
    EFORD,
    MARKET_DESIGN,
    QUEUE_CAP_GW,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator

from .new_entry import _make_new_generator
from .retirements import (
    _default_build_zone,
    _thermal_firm_mw,
    resolve_adequacy_requirement_mw,
    resolve_renewable_capacity_credit,
)


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
      capacity imports) — the firm tie is otherwise absent from the model.
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


def accredited_firm_capacity_mw(
    fleet: list[Generator],
    wind_pool_mw: float = 0.0,
    solar_pool_mw: float = 0.0,
    storage_firm_mw: float = 0.0,
    iso: str | None = None,
    peak_demand_mw: float | None = None,
    elcc_curves_enabled: bool = False,
) -> float:
    """Return the system's accredited firm (ELCC/UCAP) capacity in MW.

    Each resource contributes the firm fraction of its nameplate it can be
    relied on for at the system peak, on the ISO's own published counting
    convention when ``iso`` is given: thermal at ``1 - EFORd`` (UCAP) or at
    its seasonal rating (:func:`_thermal_firm_mw` /
    :data:`THERMAL_ACCREDITATION_BASIS_BY_ISO` — ERCOT's CDR basis),
    variable renewables at their capacity credit
    (:func:`resolve_renewable_capacity_credit` — penetration-indexed
    published ELCC curve when ``elcc_curves_enabled``, per-ISO point
    override, generic :data:`RENEWABLE_CAPACITY_CREDIT` fallback), storage
    at its duration-dependent ELCC (passed in pre-accredited as
    ``storage_firm_mw``, since the ELCC helper lives in the storage module),
    plus the firm import capacity the ISO's own adequacy ledger counts
    (:func:`_firm_import_mw` / :data:`ADEQUACY_EXTERNAL_TIE_FIRM_MW` — ERCOT's DC
    ties, PJM's CIL-governed cleared BRA imports, and the RA/FCM firm imports of
    the import-node ISOs CAISO/NEISO, credited additively without
    double-counting the dispatch import node). Wind/solar
    held in the zonal pools (not Generators) are passed as ``wind_pool_mw``
    / ``solar_pool_mw``.

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
        )

    firm = float(storage_firm_mw)
    firm += wind_pool_mw * (_credit("wind") or 0.0)
    firm += solar_pool_mw * (_credit("solar") or 0.0)
    # Firm imports the ISO's own adequacy ledger counts (one resolver, rule 19):
    # ERCOT/PJM ties absent from topology AND the RA/FCM firm imports of the
    # import-node ISOs (CAISO WECC_import, NEISO HQ_import) — additive, never
    # double-counted against the dispatch node (see :func:`_firm_import_mw`).
    firm += _firm_import_mw(iso)
    for g in fleet:
        credit = _credit(g.fuel_type)
        if credit is not None:
            firm += g.pmax_mw * credit
        else:
            firm += _thermal_firm_mw(g, iso)
    return firm


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
    )
    return accredited_mw / requirement_mw


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
    # derate it by EFORd.
    if THERMAL_ACCREDITATION_BASIS_BY_ISO.get(iso) == "seasonal_rating":
        credit = 1.0
    else:
        credit = 1.0 - EFORD["gas_ct"]
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
