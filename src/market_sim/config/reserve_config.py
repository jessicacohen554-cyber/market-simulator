"""Unified reserve co-optimization configuration and dispatch-kwargs builder.

Replaces the 6 per-ISO ``*_reserve_coopt_inputs()`` functions in
``results/scarcity.py`` and the 200-line ``if/elif`` ISO dispatch chain in
``runner.py`` with a single config-driven system. Every ISO's reserve physics
is ported into a per-ISO private helper that produces a ``ReserveDesign``;
``build_reserve_dispatch_kwargs`` converts it into the dict that
``dispatch.py`` (``_build_reserve_rows``) consumes. The LP builder is
untouched — mathematical results are byte-identical for all 6 ISOs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

# ---------------------------------------------------------------------------
# Reserve-product constants (moved from config/constants.py)
# ---------------------------------------------------------------------------

RESERVE_FUEL_TYPES: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "coal", "nuclear", "oil"}
)

QUICK_START_FUEL_TYPES: frozenset[str] = frozenset({"gas_ct", "oil"})

NYISO_SPIN_FRACTION: float = 0.5

NYISO_DOWNSTATE_SPIN_ZONES: frozenset[str] = frozenset({"NYC"})

# ERCOT multi-product AS products: (display_name, ASPLANNP433_code, tier).
ERCOT_AS_PRODUCTS: tuple[tuple[str, str, str], ...] = (
    ("RegUp", "REGUP", "fast"),
    ("RRS", "RRS", "fast"),
    ("ECRS", "ECRS", "fast"),
    ("NonSpin", "NSPIN", "all"),
)

# --- ERCOT forward AS requirement-setting methodology (G3) -----------------
ERCOT_AS_FE_FRAC_LOAD: float = 0.01
ERCOT_AS_FE_FRAC_WIND: float = 0.10
ERCOT_AS_FE_FRAC_SOLAR: float = 0.18

ERCOT_AS_REGUP_FLOOR_MW: float = 275.0
ERCOT_AS_REGUP_SIGMA_COEF: float = 0.065
ERCOT_AS_REGUP_MIN_MW: float = 80.0
ERCOT_AS_REGUP_MAX_MW: float = 1100.0

ERCOT_AS_RRS_FLOOR_MW: float = 2300.0
ERCOT_AS_RRS_INERTIA_COEF_MW: float = 1160.0
ERCOT_AS_RRS_MAX_MW: float = 3300.0

ERCOT_AS_ECRS_BASE_MW: float = 950.0
ERCOT_AS_ECRS_SIGMA_COEF: float = 0.24
ERCOT_AS_ECRS_RAMP_COEF: float = 0.017
ERCOT_AS_ECRS_MIN_MW: float = 500.0
ERCOT_AS_ECRS_MAX_MW: float = 3300.0

ERCOT_AS_NSPIN_BASE_MW: float = 2475.0
ERCOT_AS_NSPIN_LOAD_COEF: float = 0.00418
ERCOT_AS_NSPIN_RAMP_COEF: float = 0.025
ERCOT_AS_NSPIN_MIN_MW: float = 1400.0
ERCOT_AS_NSPIN_MAX_MW: float = 5700.0

ERCOT_AS_RAMP_WINDOW_HOURS: int = 3

# --- ORDC floor steps (OBDRR048) -------------------------------------------
ORDC_FLOOR_STEPS: tuple[tuple[float, float], ...] = (
    (6500.0, 20.0),
    (7000.0, 10.0),
)
ORDC_FLOOR_START_HOUR_2023: int = 304 * 24

# --- PJM -------------------------------------------------------------------
PJM_PRIMARY_RESERVE_LSC_FACTOR: float = 1.5
from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

PJM_ORDC_CURVE_PATH: str = str(CALIBRATION_DIR / "pjm_ordc_curve.csv")

# Model zones inside PJM's Mid-Atlantic/Dominion (MAD) Reserve Subzone
# (Manual 11 sec 4.2: the MAAC transmission zones plus Dominion). Crosswalk
# onto the 8-zone model topology (iso_configs._pjm_config): PJM_EMAAC (PSEG,
# JCPL, PECO, DPL, AECO, RECO), PJM_SWMAAC (BGE, PEPCO), PJM_Central_PA (PPL,
# PENELEC, METED — all MAAC) and PJM_Dominion (DOM). Known misalignment
# (CLAUDE.md #13 reconciliation): PJM_Central_PA also rolls up EKPC (eastern
# Kentucky, NOT in MAD), a small co-op (~2% of PJM load) our reduced topology
# cannot split out — including Central_PA whole errs by that sliver rather
# than dropping the PPL/PENELEC/METED bulk of the subzone.
PJM_MAD_ZONES: tuple[str, ...] = (
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)

# --- MISO ------------------------------------------------------------------
MISO_REGULATING_RESERVE_MW: float = 400.0
MISO_RESERVE_DEMAND_CURVE_MAX: float = 3500.0
MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW: float = 0.0

# MISO Zonal Operating Reserve Demand Curve (config.miso_zonal_reserves):
# the PUBLISHED stepped curve, BPM-002 §5.2.1.2 / Tariff Schedule 28-A —
# (width as a fraction of the zonal requirement, penalty $/MWh), cheapest
# band (smallest shortfall) first, the ordering model.dispatch consumes:
#   * 80-100% of the zonal requirement cleared -> $200/MWh;
#   * 10-80%  -> $1,100/MWh (Energy Offer Price Cap $1,000 + Contingency
#     Reserve Offer Price Cap $100);
#   * 0-10%   -> VOLL ($3,500, Schedule 28) minus the Zonal Regulating
#     Reserve Demand Curve price (the monthly average peaker proxy, Schedule
#     28 §IV — posted monthly values run ~$156-$222 across 2025-26, so $200
#     Tier-3 -> a $3,300 top step; the top band prices only the last 10% of
#     the requirement, so the proxy's month-to-month wiggle is immaterial).
# Zone set and requirement basis are in _miso_design.
MISO_ZONAL_ORDC_STEPS: tuple[tuple[float, float], ...] = (
    (0.20, 200.0),
    (0.70, 1100.0),
    (0.10, 3300.0),
)
# Default zonal reserve family set (config.miso_zonal_reserve_zones override):
# MISO-South only — the sub-region whose reserves are separated from the
# Midwest pool by the RDT contract-path limit (scope doc §6). MISO-East
# (Michigan pocket) is the optional second family.
MISO_ZONAL_RESERVE_DEFAULT_ZONES: tuple[str, ...] = ("MISO-South",)

# --- NYISO RCPF products ---------------------------------------------------
NYISO_RCPF_PRODUCTS: tuple[tuple[str, float, float, float], ...] = (
    ("nyca_30min_total", 2620.0, 1965.0, 750.0),
    ("nyca_10min_total", 1310.0, 0.0, 750.0),
    ("nyca_10min_spin", 655.0, 0.0, 775.0),
)

NYISO_RCPF_LOCATIONAL: dict[str, dict] = {
    "East": {
        "zones": ("Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"),
        "products": (("east_30min_total", 1200.0, 0.0, 500.0),),
    },
    "SENY": {
        "zones": ("Lower_Hudson", "NYC", "Long_Island"),
        "products": (("seny_30min_total", 1100.0, 0.0, 500.0),),
    },
    "NYC": {
        "zones": ("NYC",),
        "products": (
            ("nyc_30min_total", 1000.0, 0.0, 500.0),
            ("nyc_10min_total", 500.0, 0.0, 500.0),
        ),
    },
}

# --- NEISO RCPF products ---------------------------------------------------
NEISO_RCPF_PRODUCTS: tuple[tuple[str, float, float, float], ...] = (
    ("ne_30min_total", 1800.0, 0.0, 1000.0),
    ("ne_10min_total", 1200.0, 0.0, 1500.0),
    ("ne_10min_spin", 600.0, 0.0, 50.0),
)

# --- ERCOT load-resource RRS-UFR enrollment forecast (G4) ------------------
ERCOT_LR_RRS_ENROLL_BASE_YEAR: int = 2025
ERCOT_LR_RRS_ENROLL_BASE_MW: float = 900.0
ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR: float = 60.0
ERCOT_LR_RRS_ENROLL_CAP_MW: float = 1400.0


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ReserveFamily:
    """One reserve balance-row family (a region x product pair)."""

    name: str
    requirement: np.ndarray  # (T,) MW
    zone_mask: np.ndarray  # (n_zones,) bool
    ordc_penalties: np.ndarray  # ascending shortfall-step $/MWh
    ordc_step_widths: np.ndarray  # corresponding widths MW
    reserve_class: int = 0  # eligibility-class index


@dataclass
class ReserveDesign:
    """Complete reserve co-optimization specification for one ISO-year."""

    families: list[ReserveFamily]
    eligible: np.ndarray  # (n_classes, n_gen) bool
    storage_eligible: bool = False
    supply_cap: Optional[np.ndarray] = None  # (n_headroom_rows, T) MW
    headroom_eligible: Optional[np.ndarray] = None  # (n_hr, n_gen) bool
    headroom_products: Optional[np.ndarray] = None  # (n_hr, n_families) bool
    headroom_extra_cap: Optional[np.ndarray] = None
    online_gated: Optional[np.ndarray] = None  # (n_classes,) bool
    online_rho: float = 1.0
    # Per-generator reserve spec (dispatch._build_reserve_rows_pergen): one
    # R column per reserve-providing asset, bounded by its 10-min deliverable
    # ramp. ``pergen_gen_idx`` lists every member generator; ``pergen_col``
    # maps each member to its R column (plant-level aggregation — tranches of
    # one plant share a column; ``None`` = one column per member). When set,
    # the zone-aggregate scoping fields above (supply_cap/online_gated/
    # headroom_*) must be None — the per-unit bound supersedes them.
    pergen_gen_idx: Optional[np.ndarray] = None  # (n_members,) fleet indices
    pergen_col: Optional[np.ndarray] = None  # (n_members,) R column per member
    pergen_ramp10: Optional[np.ndarray] = None  # (n_r,) MW ramp10 caps


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_reserve_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    *,
    system_load: np.ndarray | None = None,
    wind_gen: np.ndarray | None = None,
    solar_gen: np.ndarray | None = None,
    sim_year: int | None = None,
) -> ReserveDesign:
    """Build the reserve co-optimization design for any ISO.

    Dispatches to the correct per-ISO helper based on ``config.iso``.
    """
    iso = str(config.iso)
    if iso == "ERCOT":
        if getattr(config, "ercot_multiproduct_as_coopt", False):
            return _ercot_multiproduct_design(
                config,
                fleet_arrays,
                hours,
                zone_names,
                system_load=system_load,
                wind_gen=wind_gen,
                solar_gen=solar_gen,
                sim_year=sim_year,
            )
        return _ercot_design(config, fleet_arrays, hours, sim_year=sim_year)
    if iso == "PJM":
        return _pjm_design(config, fleet_arrays, hours, zone_names)
    if iso == "MISO":
        return _miso_design(config, fleet_arrays, hours, zone_names)
    if iso == "NYISO":
        return _nyiso_design(config, fleet_arrays, hours, zone_names)
    if iso == "NEISO":
        return _neiso_design(config, fleet_arrays, hours, zone_names)
    raise ValueError(f"No reserve design for ISO {iso!r}")


def build_reserve_dispatch_kwargs(
    design: ReserveDesign,
) -> dict:
    """Convert a ``ReserveDesign`` into the ``dispatch_kwargs`` dict.

    The returned dict can be passed directly to ``dispatch_kwargs.update()``.
    """
    families = design.families
    if not families:
        return {}

    n_fam = len(families)
    T = families[0].requirement.shape[0]
    n_zones = families[0].zone_mask.shape[0]

    requirement = np.zeros((n_fam, T), dtype=float)
    zone_mask = np.zeros((n_fam, n_zones), dtype=bool)
    counts = np.zeros(n_fam, dtype=int)
    reserve_class = np.zeros(n_fam, dtype=int)
    pen_list: list[np.ndarray] = []
    wid_list: list[np.ndarray] = []

    for f, fam in enumerate(families):
        requirement[f, :] = fam.requirement
        zone_mask[f, :] = fam.zone_mask
        reserve_class[f] = fam.reserve_class
        pen_list.append(fam.ordc_penalties)
        wid_list.append(fam.ordc_step_widths)
        counts[f] = fam.ordc_penalties.shape[0]

    ordc_penalties = np.concatenate(pen_list) if pen_list else np.zeros(0)
    ordc_step_widths = np.concatenate(wid_list) if wid_list else np.zeros(0)

    # Squeeze to (T,) / (n_gen,) for single-family ISOs with one class, to
    # match the old functions' return shapes exactly.
    if n_fam == 1 and design.headroom_eligible is None:
        out_req = requirement[0]  # (T,)
        out_elig = design.eligible[0] if design.eligible.ndim == 2 else design.eligible
    else:
        out_req = requirement
        out_elig = design.eligible

    kw: dict = dict(
        reserve_requirement=out_req,
        reserve_eligible=out_elig,
        ordc_penalties=ordc_penalties.astype(float),
        ordc_step_widths=ordc_step_widths.astype(float),
    )

    if design.storage_eligible:
        kw["reserve_storage"] = True

    # Multi-family: zone mask, counts, class
    if n_fam > 1 or design.headroom_eligible is not None:
        kw["reserve_balance_zone_mask"] = zone_mask
        kw["reserve_balance_ordc_counts"] = counts
        kw["reserve_balance_class"] = reserve_class

    # Headroom rows (ERCOT multiproduct quality cascade)
    if design.headroom_eligible is not None:
        kw["reserve_headroom_eligible"] = design.headroom_eligible
        kw["reserve_headroom_products"] = design.headroom_products

    if design.headroom_extra_cap is not None:
        kw["reserve_headroom_extra_cap"] = design.headroom_extra_cap

    # Online-gated reserve (NYISO synchronised, PJM)
    if design.online_gated is not None:
        kw["reserve_online_gated"] = design.online_gated
        kw["reserve_online_rho"] = design.online_rho

    # Supply cap (ERCOT RTOLCAP, PJM deliverable ramp)
    if design.supply_cap is not None:
        kw["reserve_supply_cap"] = design.supply_cap

    # Per-generator reserve columns (PJM pjm_reserve_pergen)
    if design.pergen_gen_idx is not None:
        kw["reserve_pergen_gen_idx"] = design.pergen_gen_idx
        kw["reserve_pergen_ramp10"] = design.pergen_ramp10
        if design.pergen_col is not None:
            kw["reserve_pergen_col"] = design.pergen_col

    return kw


# ---------------------------------------------------------------------------
# Per-ISO private helpers — ported physics from scarcity.py
# ---------------------------------------------------------------------------


def _reserve_eligible(fleet_arrays: FleetArrays) -> np.ndarray:
    """ISO-agnostic thermal reserve-eligibility mask ``(n_gen,)``."""
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    return np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))


def _quick_start_eligible(fleet_arrays: FleetArrays) -> np.ndarray:
    """Quick-start (10-min capable) subset of the reserve fleet ``(n_gen,)``."""
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    return np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))


# ---- ERCOT single-product -------------------------------------------------


def _ercot_design(
    config, fleet_arrays: FleetArrays, hours: int, *, sim_year: int | None = None
) -> ReserveDesign:
    """ERCOT single-product ORDC co-optimization (the lumped contingency reserve)."""
    from market_sim.results.scarcity import (
        ercot_ecrs_requirement_mw,
        ercot_load_resource_reserve_credit_mw,
        ercot_ordc_demand_steps,
        ercot_storage_as_reserve_mw,
        resolve_lolp_params,
    )

    mu, sigma = resolve_lolp_params(config, hours)
    mu_s = float(np.mean(mu))
    sigma_s = float(np.mean(sigma))
    req_total, penalties, widths = ercot_ordc_demand_steps(
        voll=config.ordc_voll,
        mcl_mw=config.ordc_mcl_mw,
        mu_mw=mu_s,
        sigma_mw=sigma_s,
        shift_sigma=config.ordc_lolp_shift_sigma,
        multistep_floor=config.ordc_multistep_floor,
    )
    requirement = np.full(int(hours), req_total, dtype=float)

    if getattr(config, "ercot_ecrs_requirement", False) and int(
        config.weather_year
    ) >= int(getattr(config, "ercot_ecrs_requirement_from_year", 2023)):
        requirement = requirement + ercot_ecrs_requirement_mw(
            int(config.weather_year), hours
        )

    if getattr(config, "ercot_load_resource_reserve", False) and int(
        config.weather_year
    ) >= int(getattr(config, "ercot_load_resource_reserve_from_year", 2023)):
        load_mw = ercot_load_resource_reserve_credit_mw(config, hours, year=sim_year)
        requirement = np.maximum(requirement - load_mw, float(config.ordc_mcl_mw))

    if (
        getattr(config, "ercot_storage_as_reserve", False)
        and getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and int(config.weather_year)
        >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))
    ):
        storage_as_mw = ercot_storage_as_reserve_mw(int(config.weather_year), hours)
        requirement = np.maximum(requirement - storage_as_mw, float(config.ordc_mcl_mw))

    eligible = _reserve_eligible(fleet_arrays)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    zone_mask = np.ones(n_zones, dtype=bool)

    fam = ReserveFamily(
        name="ercot_ordc",
        requirement=requirement,
        zone_mask=zone_mask,
        ordc_penalties=penalties,
        ordc_step_widths=widths,
        reserve_class=0,
    )
    return ReserveDesign(
        families=[fam],
        eligible=eligible.reshape(1, -1),
        storage_eligible=True,
    )


# ---- ERCOT multi-product ---------------------------------------------------


def _ercot_multiproduct_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    *,
    system_load: np.ndarray | None = None,
    wind_gen: np.ndarray | None = None,
    solar_gen: np.ndarray | None = None,
    sim_year: int | None = None,
) -> ReserveDesign:
    """ERCOT multi-product AS co-optimization (RegUp/RRS/ECRS/NonSpin)."""
    from market_sim.results.scarcity import (
        ercot_as_forward_drivers,
        ercot_as_forward_requirement_mw,
        ercot_as_plan_requirement_mw,
        ercot_load_resource_reserve_credit_mw,
        ercot_rtolcap_supply_cap_mw,
        nyiso_rcpf_product_shortfall_steps,
    )

    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    products = list(ERCOT_AS_PRODUCTS)
    n_prod = len(products)
    voll = float(config.ordc_voll)
    crit_frac = float(getattr(config, "ercot_as_critical_frac", 0.0))
    n_ramp = int(getattr(config, "ercot_as_n_ramp", 12))
    year = int(config.weather_year)

    forward_drivers: dict[str, np.ndarray] | None = None
    if (
        getattr(config, "ercot_as_forward_requirement", False)
        and system_load is not None
        and wind_gen is not None
        and solar_gen is not None
    ):
        forward_drivers = ercot_as_forward_drivers(system_load, wind_gen, solar_gen)

    requirement = np.zeros((n_prod, T), dtype=float)
    families: list[ReserveFamily] = []
    zone_mask_all = np.ones(n_zones, dtype=bool)

    for p, (_name, code, _tier) in enumerate(products):
        req_t = ercot_as_forward_requirement_mw(config, code, T, forward_drivers)
        if req_t is None:
            req_t = ercot_as_plan_requirement_mw(year, T, code)
        requirement[p, :] = req_t
        req_peak = float(req_t.max())
        if req_peak <= 0.0:
            pens = np.zeros(0)
            wids = np.zeros(0)
        else:
            crit = crit_frac * req_peak
            pens, wids = nyiso_rcpf_product_shortfall_steps(
                req_peak, crit, voll, n_ramp=n_ramp
            )
        families.append(
            ReserveFamily(
                name=_name,
                requirement=req_t,
                zone_mask=zone_mask_all.copy(),
                ordc_penalties=pens,
                ordc_step_widths=wids,
                reserve_class=p,
            )
        )

    # Load-Resource RRS-UFR supply credit (G4).
    if getattr(config, "ercot_load_resource_reserve", False) and year >= int(
        getattr(config, "ercot_load_resource_reserve_from_year", 2023)
    ):
        rrs_idx = next(
            (i for i, (_n, c, _t) in enumerate(products) if c == "RRS"), None
        )
        if rrs_idx is not None and requirement[rrs_idx].max() > 0.0:
            lr_mw = ercot_load_resource_reserve_credit_mw(config, T, year=sim_year)
            requirement[rrs_idx, :] = np.maximum(requirement[rrs_idx, :] - lr_mw, 0.0)
            families[rrs_idx] = ReserveFamily(
                name=families[rrs_idx].name,
                requirement=requirement[rrs_idx],
                zone_mask=families[rrs_idx].zone_mask,
                ordc_penalties=families[rrs_idx].ordc_penalties,
                ordc_step_widths=families[rrs_idx].ordc_step_widths,
                reserve_class=families[rrs_idx].reserve_class,
            )

    full_elig = _reserve_eligible(fleet_arrays)
    reserve_eligible = np.tile(full_elig, (n_prod, 1))

    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    responsive = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    fast_elig = responsive & ~quick
    headroom_eligible = np.vstack([fast_elig, responsive])
    headroom_products = np.zeros((2, n_prod), dtype=bool)
    for p, (_name, _code, tier) in enumerate(products):
        headroom_products[1, p] = True
        if tier == "fast":
            headroom_products[0, p] = True

    supply_cap = ercot_rtolcap_supply_cap_mw(config, T)

    return ReserveDesign(
        families=families,
        eligible=reserve_eligible,
        storage_eligible=True,
        headroom_eligible=headroom_eligible,
        headroom_products=headroom_products,
        supply_cap=supply_cap,
    )


# ---- PJM ------------------------------------------------------------------


def _pjm_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str] | None = None,
) -> ReserveDesign:
    """PJM energy+reserve co-optimization (measured Primary requirement + published ORDC).

    Two layouts, both on the measured Primary requirement and the published
    two-step ORDC:

    * Zone-aggregate (default): the legacy single RTO family drawing on total
      eligible zone headroom, optionally re-scoped by the deliverable supply
      cap (``pjm_reserve_supply_cap``) and/or online gating
      (``pjm_reserve_online_gated``).
    * Per-generator (``pjm_reserve_pergen``): one R column per reserve-eligible
      unit with nonzero 10-min ramp (``R[j] ≤ FleetArrays.ramp10``), joint
      ``P+R ≤ cap`` per unit-hour, and TWO nested measured balance families per
      Manual 11 sec 4.2 — the RTO Reserve Zone (``pr_req_mw``) and the
      Mid-Atlantic/Dominion Reserve Subzone (``mad_pr_req_mw``, zones
      :data:`PJM_MAD_ZONES`; a MAD MW counts toward both, the NYISO nesting
      template). Reserve then competes with energy on the same marginal unit,
      which is what prices the sub-shortage opportunity-cost band
      (docs/multi-iso/pjm-reserve-ordc.md Phase 2). The zone-aggregate scoping
      flags are ignored in this mode (the per-unit ramp10 bound supersedes
      them). The forecast path (no measured series) falls back to the
      1.5×MSSC formula for the RTO family and omits the MAD family.
    """
    from market_sim.results.scarcity import (
        largest_single_contingency_mw,
        load_pjm_measured_mad_reserve_requirement,
        load_pjm_measured_reserve_requirement,
        load_pjm_ordc_curve,
        pjm_ordc_shortfall_steps,
        pjm_primary_reserve_requirement,
        pjm_reserve_deliverable_supply_cap_mw,
    )

    year = int(config.weather_year)
    req = load_pjm_measured_reserve_requirement(year, hours)
    if req is None:
        eligible_mask = _reserve_eligible(fleet_arrays)
        lsc = largest_single_contingency_mw(
            fleet_arrays.pmax,
            availability=fleet_arrays.availability,
            reserve_mask=eligible_mask,
            plant_code=fleet_arrays.plant_code,
        )
        req = pjm_primary_reserve_requirement(lsc, hours)
    req = np.asarray(req, dtype=float)

    curve = load_pjm_ordc_curve(PJM_ORDC_CURVE_PATH)
    steps = curve[("Primary", "RTO")]
    outer_offset = float(max(o for o, _ in steps))
    _req_total_nom, penalties, widths = pjm_ordc_shortfall_steps(
        steps, float(np.mean(req))
    )
    widths = np.asarray(widths, dtype=float).copy()
    widths[-1] = float(np.max(req))

    requirement = req + outer_offset
    eligible = _reserve_eligible(fleet_arrays)
    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    zone_mask = np.ones(n_zones, dtype=bool)

    fam = ReserveFamily(
        name="pjm_primary",
        requirement=requirement,
        zone_mask=zone_mask,
        ordc_penalties=penalties.astype(float),
        ordc_step_widths=widths.astype(float),
        reserve_class=0,
    )

    if getattr(config, "pjm_reserve_pergen", False):
        families = [fam]
        # Nested MAD subzone family — measured backcast series only; a
        # forecast year (no series) runs the RTO family alone.
        mad_req = load_pjm_measured_mad_reserve_requirement(year, hours)
        if mad_req is not None and zone_names:
            mad_steps = curve[("Primary", "MAD")]
            mad_offset = float(max(o for o, _ in mad_steps))
            mad_req = np.asarray(mad_req, dtype=float)
            _mad_total, mad_pen, mad_wid = pjm_ordc_shortfall_steps(
                mad_steps, float(np.mean(mad_req))
            )
            mad_wid = np.asarray(mad_wid, dtype=float).copy()
            mad_wid[-1] = float(np.max(mad_req))
            mad_mask = np.array([z in PJM_MAD_ZONES for z in zone_names], dtype=bool)
            if mad_mask.any():
                families.append(
                    ReserveFamily(
                        name="pjm_primary_mad",
                        requirement=mad_req + mad_offset,
                        zone_mask=mad_mask,
                        ordc_penalties=mad_pen.astype(float),
                        ordc_step_widths=mad_wid.astype(float),
                        reserve_class=0,
                    )
                )
        ramp10 = np.asarray(
            getattr(fleet_arrays, "ramp10", np.zeros(eligible.size)), dtype=float
        )
        # Members: eligible units that can deliver within 10 min (ramp10 > 0)
        # — an exact reduction: a zero-ramp column would be fixed at 0.
        pergen_gen_idx = np.flatnonzero(eligible & (ramp10 > 0.0))
        # R-column granularity is memory-tiered to what the 15 GB calibration
        # box fits (docs/multi-iso/pjm-reserve-ordc.md Phase 2 memtests: the
        # per-tranche build OOM'd at ~15.9 GB, plant-level everywhere at
        # ~15.1 — the HiGHS workspace scales with the joint-row count):
        #
        # * INSIDE the MAD subzone (where the binding locational requirement
        #   lives): one column per (plant, fuel-class, zone) asset. Not
        #   per-tranche: a plant's must-run/committed/economic/peaking
        #   tranches dispatch bang-bang, so headroom and the 10-minute ramp
        #   are PLANT properties (the pjm_online_reserve doctrine), and
        #   sum(tranche ramp10) == RAMP10_FRAC[class] x plant pmax — the
        #   column's cap is the same physics. Units without a positive plant
        #   code stay singleton columns.
        # * OUTSIDE MAD: one column per (zone, fuel-class). Coarser headroom
        #   pooling on the side where no locational requirement binds — the
        #   RTO-wide family still draws on every column, bounded by the same
        #   summed ramp10, and reserve still competes with the zone-class's
        #   energy at its margin. Never a breakpoint/penalty change (rule
        #   #11); the granularity tier is documented, not fitted.
        plant = np.asarray(fleet_arrays.plant_code, dtype=int)[pergen_gen_idx]
        fuel = np.asarray(fleet_arrays.fuel_type_idx, dtype=int)[pergen_gen_idx]
        zone = np.asarray(fleet_arrays.zone_idx, dtype=int)[pergen_gen_idx]
        if zone_names:
            in_mad = np.array(
                [zone_names[z] in PJM_MAD_ZONES for z in zone], dtype=bool
            )
        else:
            in_mad = np.ones(zone.size, dtype=bool)
        singleton = np.where(plant > 0, -1, np.arange(pergen_gen_idx.size))
        # Non-MAD members collapse to their (zone, fuel) key (plant/singleton
        # masked out); MAD members keep the (plant, fuel, zone) asset key.
        keys = np.stack(
            [
                np.where(in_mad, plant, -1),
                fuel,
                zone,
                np.where(in_mad, singleton, -1),
            ],
            axis=1,
        )
        _, pergen_col = np.unique(keys, axis=0, return_inverse=True)
        n_r = int(pergen_col.max()) + 1 if pergen_col.size else 0
        col_ramp10 = np.zeros(n_r, dtype=float)
        np.add.at(col_ramp10, pergen_col, ramp10[pergen_gen_idx])
        return ReserveDesign(
            families=families,
            eligible=eligible.reshape(1, -1),
            storage_eligible=False,
            pergen_gen_idx=pergen_gen_idx,
            pergen_col=pergen_col.astype(int),
            pergen_ramp10=col_ramp10,
        )

    supply_cap = pjm_reserve_deliverable_supply_cap_mw(config, fleet_arrays, T)

    online_gated = None
    online_rho = 1.0
    if getattr(config, "pjm_reserve_online_gated", False):
        rho = float(getattr(config, "pjm_reserve_online_rho", 1.0))
        online_gated = np.array([True])
        online_rho = rho

    return ReserveDesign(
        families=[fam],
        eligible=eligible.reshape(1, -1),
        storage_eligible=False,
        supply_cap=supply_cap,
        online_gated=online_gated,
        online_rho=online_rho,
    )


# ---- MISO -----------------------------------------------------------------


def _miso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str] | None = None,
    n_ramp: int = 8,
) -> ReserveDesign:
    """MISO energy+reserve co-optimization: market-wide RBDC, optional zonal.

    Always builds the market-wide RBDC family (requirement = MSSC +
    regulating, demand curve ramping to the $3,500/MWh VOLL anchor — MISO
    BPM-002 / Schedule 28/28-A, unchanged from the miso3/miso-34 probes).

    When ``config.miso_zonal_reserves`` is on (GATED, default off) it appends
    one LOCATIONAL operating-reserve family per zone in
    ``config.miso_zonal_reserve_zones`` (default
    :data:`MISO_ZONAL_RESERVE_DEFAULT_ZONES` = MISO-South), the NYISO
    nested-family template: MISO enforces a minimum Zonal Operating Reserve
    Requirement per Reserve Zone (BPM-002 §3.3/§3.3.2), anchored to the
    pre-determined largest zonal contingency event — modeled as the
    within-zone MSSC (fleet-derived, forward-responsive) — and shortfalls
    price at the published Zonal Operating Reserve Demand Curve
    (:data:`MISO_ZONAL_ORDC_STEPS`, BPM-002 §5.2.1.2). The zonal family
    shares the market-wide family's reserve class, so a South reserve MW
    counts toward both constraints (nested, like NYISO East ⊂ NYCA). Zero
    parameters fitted to the price residual.
    """
    from market_sim.results.scarcity import (
        largest_single_contingency_mw,
        nyiso_rcpf_product_shortfall_steps,
    )

    eligible = _reserve_eligible(fleet_arrays)
    mssc = largest_single_contingency_mw(
        fleet_arrays.pmax,
        availability=fleet_arrays.availability,
        reserve_mask=eligible,
        plant_code=fleet_arrays.plant_code,
    )
    req = float(mssc) + MISO_REGULATING_RESERVE_MW
    penalties, widths = nyiso_rcpf_product_shortfall_steps(
        req,
        MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW,
        MISO_RESERVE_DEMAND_CURVE_MAX,
        n_ramp=n_ramp,
    )
    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    zone_mask = np.ones(n_zones, dtype=bool)
    requirement = np.full(T, req, dtype=float)

    families = [
        ReserveFamily(
            name="miso_rbdc",
            requirement=requirement,
            zone_mask=zone_mask,
            ordc_penalties=penalties.astype(float),
            ordc_step_widths=widths.astype(float),
            reserve_class=0,
        )
    ]

    if getattr(config, "miso_zonal_reserves", False):
        if not zone_names:
            raise ValueError(
                "miso_zonal_reserves requires zone_names to map zonal reserve "
                "families onto model zones"
            )
        zone_index = {name: i for i, name in enumerate(zone_names)}
        zonal_zones = tuple(
            getattr(config, "miso_zonal_reserve_zones", None)
            or MISO_ZONAL_RESERVE_DEFAULT_ZONES
        )
        for zname in zonal_zones:
            if zname not in zone_index:
                raise ValueError(
                    f"miso_zonal_reserve_zones entry {zname!r} is not a model "
                    f"zone (zones: {list(zone_names)})"
                )
            z = zone_index[zname]
            in_zone = np.asarray(fleet_arrays.zone_idx, dtype=int) == z
            # Zonal requirement = the largest zonal contingency event: the
            # within-zone MSSC over reserve-eligible units (plant-aggregated
            # common-mode, availability-aware) — BPM-002 §3.3.2's minimum
            # zonal requirement basis, per the MISO STR design's
            # "pre-determined largest zonal events".
            zonal_req = float(
                largest_single_contingency_mw(
                    fleet_arrays.pmax,
                    availability=fleet_arrays.availability,
                    reserve_mask=eligible & in_zone,
                    plant_code=fleet_arrays.plant_code,
                )
            )
            if zonal_req <= 0.0:
                continue
            zmask = np.zeros(n_zones, dtype=bool)
            zmask[z] = True
            zonal_pen = np.array([p for _, p in MISO_ZONAL_ORDC_STEPS])
            zonal_wid = np.array(
                [frac * zonal_req for frac, _ in MISO_ZONAL_ORDC_STEPS]
            )
            families.append(
                ReserveFamily(
                    name=f"miso_zonal_or_{zname.lower().replace('-', '_')}",
                    requirement=np.full(T, zonal_req, dtype=float),
                    zone_mask=zmask,
                    ordc_penalties=zonal_pen,
                    ordc_step_widths=zonal_wid,
                    reserve_class=0,
                )
            )

    return ReserveDesign(
        families=families,
        eligible=eligible.reshape(1, -1),
        storage_eligible=False,
    )


# ---- NYISO -----------------------------------------------------------------


def _nyiso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    n_ramp: int = 8,
) -> ReserveDesign:
    """NYISO locational energy+reserve co-optimization (nested RCPF families)."""
    from market_sim.results.scarcity import (
        nyiso_rcpf_product_shortfall_steps,
        nyiso_spin_requirement_mw,
    )

    T = int(hours)
    zone_index = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)

    raw_families: list[tuple[tuple[int, ...], str, tuple[float, float, float]]] = []
    nyca_products = tuple(
        getattr(config, "nyiso_rcpf_products", None) or NYISO_RCPF_PRODUCTS
    )
    all_zones = tuple(range(n_zones))
    for name, req, crit, pen in nyca_products:
        raw_families.append(
            (all_zones, str(name), (float(req), float(crit), float(pen)))
        )

    locational = getattr(config, "nyiso_rcpf_locational", None) or NYISO_RCPF_LOCATIONAL
    for region in locational.values():
        member_idx = tuple(zone_index[z] for z in region["zones"] if z in zone_index)
        if not member_idx:
            continue
        for name, req, crit, pen in region["products"]:
            raw_families.append(
                (member_idx, str(name), (float(req), float(crit), float(pen)))
            )

    synch = bool(getattr(config, "nyiso_synchronised_reserve", False))
    commit_gated = synch and bool(getattr(config, "commitment_enabled", False))
    if synch:
        nyc_idx = tuple(i for z, i in zone_index.items() if z == "NYC")
        spin_req = nyiso_spin_requirement_mw(config)
        if nyc_idx:
            spin_name = "nyc_spin_commit" if commit_gated else "nyc_spin_online"
            raw_families.append((nyc_idx, spin_name, (spin_req, 0.0, 500.0)))

    families: list[ReserveFamily] = []
    for member_idx, name, (req, crit, pen) in raw_families:
        zmask = np.zeros(n_zones, dtype=bool)
        zmask[list(member_idx)] = True
        rclass = (
            2
            if "spin_online" in name
            else (1 if "10min" in name or "spin" in name else 0)
        )
        requirement_arr = np.full(T, req, dtype=float)
        p, w = nyiso_rcpf_product_shortfall_steps(req, crit, pen, n_ramp=n_ramp)
        families.append(
            ReserveFamily(
                name=name,
                requirement=requirement_arr,
                zone_mask=zmask,
                ordc_penalties=p,
                ordc_step_widths=w,
                reserve_class=rclass,
            )
        )

    full_elig = _reserve_eligible(fleet_arrays)
    quick_elig = _quick_start_eligible(fleet_arrays)
    if synch and not commit_gated:
        eligible = np.vstack([full_elig, quick_elig, quick_elig])
        online_gated = np.array([False, False, True], dtype=bool)
        q_idx = np.flatnonzero(quick_elig)
        pmin_q = np.asarray(fleet_arrays.pmin, dtype=float)[q_idx]
        pmax_q = np.asarray(fleet_arrays.pmax, dtype=float)[q_idx]
        valid = (pmin_q > 0) & (pmax_q > pmin_q)
        if valid.any():
            ratio = (pmax_q[valid] - pmin_q[valid]) / pmin_q[valid]
            online_rho = float(
                np.clip(np.average(ratio, weights=pmax_q[valid]), 0.5, 4.0)
            )
        else:
            online_rho = 1.0
    else:
        eligible = np.vstack([full_elig, quick_elig])
        online_gated = None
        online_rho = 1.0

    return ReserveDesign(
        families=families,
        eligible=eligible,
        storage_eligible=True,
        online_gated=online_gated,
        online_rho=online_rho,
    )


# ---- NEISO ----------------------------------------------------------------


def _neiso_design(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    n_ramp: int = 8,
) -> ReserveDesign:
    """NEISO system-wide energy+reserve co-optimization (3-level RCPF nesting)."""
    from market_sim.results.scarcity import nyiso_rcpf_product_shortfall_steps

    T = int(hours)
    n_zones = len(zone_names)
    all_zones = tuple(range(n_zones))
    products = tuple(
        getattr(config, "neiso_rcpf_products", None) or NEISO_RCPF_PRODUCTS
    )

    families: list[ReserveFamily] = []
    for name, req, crit, pen in products:
        zmask = np.zeros(n_zones, dtype=bool)
        zmask[list(all_zones)] = True
        rclass = 1 if "10min" in str(name) or "spin" in str(name) else 0
        requirement_arr = np.full(T, float(req), dtype=float)
        p, w = nyiso_rcpf_product_shortfall_steps(
            float(req), float(crit), float(pen), n_ramp=n_ramp
        )
        families.append(
            ReserveFamily(
                name=str(name),
                requirement=requirement_arr,
                zone_mask=zmask,
                ordc_penalties=p,
                ordc_step_widths=w,
                reserve_class=rclass,
            )
        )

    full_elig = _reserve_eligible(fleet_arrays)
    quick_elig = _quick_start_eligible(fleet_arrays)
    eligible = np.vstack([full_elig, quick_elig])

    return ReserveDesign(
        families=families,
        eligible=eligible,
        storage_eligible=True,
    )
