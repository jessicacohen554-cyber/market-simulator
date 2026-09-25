"""Fleet vectorization: ``generators_to_fleet_arrays`` and its availability/outage inputs.

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

import logging
from collections import Counter

import numpy as np

from market_sim.config.constants import (
    COAL_MAX_CF_BY_PLANT,
    MAINTENANCE_MONTHLY_SHAPE,
    NUCLEAR_DORMANT_UNTIL,
    NUCLEAR_MONTHLY_CF,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
    SUMMER_CLASS_DERATE,
    SUMMER_WEFOR_SHARE,
    THERMAL_AVAILABILITY,
)
from market_sim.config.paths import CAMPD_BINS_CSV
from market_sim.config.plant_taxonomy import (
    COAL_ARTIFACT_FAMILY,
    COAL_CLASSES,
    artifact_class,
    is_coal_class,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.cod_ramp import (
    class_cod_coverage,
    generator_online_mask,
    log_class_cod_coverage,
)
from market_sim.data.floor_mechanisms import (
    MECH_CC_MUSTRUN_PER_PLANT,
    MECH_CHP_STEAM,
    MECH_COAL_MIN_CONFIG,
    MECH_COAL_MUSTRUN,
    MECH_CT_DEPLOYMENT_OVERLAY,
    MECH_CT_MUSTRUN_PER_PLANT,
    MECH_HYDRO_MIN_FLOW,
    MECH_HYDRO_ROR_FLAT,
    MECH_NUCLEAR,
    MECH_RELIABILITY_DEPLOYMENT_OVERLAY,
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
    clear_where_unfloored,
)
from market_sim.data.outages import (
    ct_deployment_floor_for_year,
    ercot_noncampd_availability_caps,
    partial_outage_active_units,
    partial_outage_derate_factors,
    reliability_deployment_floor_for_year,
    retiree_availability_caps,
    shared_unit_hours,
    short_screened_coal_shares,
    unit_outage_active_units,
    lp_bin_capacity_index,
    unit_outage_derate_factors,
    unit_outage_maxgen_derate_factors,
    unit_outage_short_derate_factors,
    unit_partial_outage_derate_factors,
)
from market_sim.data.fleet.models import (
    FUEL_TYPE_MAP,
    FleetArrays,
    Generator,
    _hour_to_month_index,
)
from market_sim.data.fleet.withholding import (
    _AS_GAS_GROUPS,
    _AS_RESTYPE_TO_GROUPS,
    _AS_WITHHOLDING,
    _CAISO_MSSC_EXCLUDE_FUELS,
    _COAL_SYNC_FORCE_ALL,
    _ercot_dam_plant_hourly_apply,
    _ramp10_capability,
    _withdraw_top_of_merit,
    caiso_operating_reserve_mw,
    load_as_reserve_withholding_mw,
    load_as_thermal_withholding,
)
from market_sim.data.fleet.eia860 import (
    BIN_FORCED_DERATE_BY_YEAR,
    ct_mustrun_floor_mwh_by_plant,
)
from market_sim.data.fleet.models import _pkg_ns

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")

# Spring/autumn shoulder months (1-based) when thermal plants concentrate
# planned maintenance — the lull between the winter and summer demand peaks.
# Used to size each unit's annual planned-outage (POF) budget.
_CC_SHOULDER_MONTHS: frozenset[int] = frozenset({3, 4, 5, 10, 11})

# ERCOT summer peak months (1-based). Thermal units carry reduced outage
# here — planned outages are removed entirely and only a fraction of the
# forced-outage rate applies — so firm capacity is available for the load
# peak. The displaced outage energy is redistributed into the shoulder months
# only (not winter, which has its own peak), leaving each unit's
# annual-average availability unchanged. See generators_to_fleet_arrays.
_SUMMER_MONTHS: frozenset[int] = frozenset({6, 7, 8, 9})


# CAISO Kern-County enhanced-oil-recovery (EOR) topping cogens: a gas turbine
# whose exhaust raises injection steam for thermal EOR, electricity a byproduct.
# EIA-923 reports an artificially EFFICIENT plant heat rate (Kern River 5.80,
# Sycamore 5.99, Midway Sunset 5.09 MMBtu/MWh — BELOW an efficient combined
# cycle ~7) because the steam fuel is credited out of the electrical heat rate.
# The model then prices these as cheap baseload and runs the three at ~88% CF
# (3.7 TWh combined in 2024) versus their measured ~0.8 TWh (EIA-923 CF 0.05-
# 0.14, and DECLINING as CA EOR winds down) — a real CT_CHP over-dispatch. The
# physically-correct dispatch basis is the POWER-ONLY heat rate: charge ALL the
# fuel to electricity (no steam credit), which for a topping cycle is the
# simple-cycle gas-turbine heat rate ~1.8x the steam-credited blend — landing
# these units at ~9-11 MMBtu/MWh, the CT_PEAKER simple-cycle band where their
# power island physically sits. CAISO_EOR_TOPPING_FACTOR is the steam-credit
# ratio (forward-derivable turbine physics, responds to changed gas/steam
# conditions — admissible under CLAUDE.md #11/#12, the same measured-physics HR
# correction as MIXED_FACILITY_STEAM_HR, NOT a residual fit). Applied to the
# CT_CHP rows of these plants only, and only when it RAISES the heat rate.
CAISO_EOR_TOPPING_PLANTS: frozenset[int] = frozenset({10496, 50134, 52169})
CAISO_EOR_TOPPING_FACTOR: float = 1.8

# Generalized steam-credit HR correction for ALL CAISO CHP gas turbines, not
# just the three big EOR plants.  Every CHP simple-cycle CT reports a steam-
# credited EIA-923/CAMPD heat rate because total fuel includes steam-host
# thermal energy.  No simple-cycle GT achieves HR < 8.0 MMBtu/MWh on a
# power-only basis — the sub-8 values are artifacts of the CHP accounting.
# The same 1.8× topping factor used for EOR applies: all CT_CHP plants are
# physically simple-cycle turbines with similar thermodynamics; the correction
# lands them at 9–11 MMBtu/MWh regardless of the steam host type (oilfield,
# refinery, hospital, campus).  Applied only when it RAISES the heat rate.
CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD: float = 8.0

# CC_CHP plants also carry a steam credit, but smaller because the combined-
# cycle steam turbine is part of the power conversion — only ADDITIONAL process-
# steam extraction inflates efficiency.  A CC_CHP with reported HR < 6.0 is
# below even the most efficient gas-CC class (h_class = 6.3), confirming steam
# credit.  A 1.15× factor brings these into the 6.3–6.9 range (h_class to
# f_class); a floor of 6.3 prevents under-correction of heavily credited units.
CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD: float = 6.0
CAISO_CHP_CC_STEAM_CREDIT_FACTOR: float = 1.15
CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR: float = 6.3

# ISOs whose CHP gas turbines get the steam-credit power-only heat-rate
# correction (:func:`market_sim.data.chp._correct_chp_steam_credit_hr`). The
# correction is TURBINE PHYSICS, not an ISO-specific residual fit: a power-only
# simple-cycle GT cannot run below ~8 MMBtu/MWh and a power-only CC cannot run
# below ~6.3, so a CHP unit reporting less is carrying a steam credit in its
# CEMS/EIA-923 heat rate regardless of which market it sits in. Because the
# thresholds/factors/floor are universal physical limits (the same for every
# ISO — CLAUDE.md rule 24 governs *fitted* per-ISO curves, not physics), the set
# only controls WHICH ISOs have had their CHP HR distribution audited and wired
# in. PJM added 2026-07-07: its CHP reports cap-weighted HRs of CC_CHP ~4.95 /
# CT_CHP ~6.14 MMBtu/MWh (both physically impossible power-only), which let
# steam-credited CHP clear as the cheapest thermal and over-deliver grid energy
# +52-67% vs EIA-923 net-to-grid (docs/FINDING-pjm-burndown-2026-07.md). Other
# ISOs join as their CHP HR distributions are audited in the all-ISO sweep.
#
# MISO was AUDITED 2026-07-08 and deliberately NOT added: although its reported
# HRs are equally sub-physical (cap-weighted CT_CHP ~6.62 / CC_CHP ~6.76, median
# CT_CHP 5.50, min CC_CHP 4.49 MMBtu/MWh), MISO CHP does NOT over-deliver — the
# symptom the correction targets. In the miso-46 keeper CC_CHP already matched
# 923 (+0.8/+1.6/+6.0% by year) and CT_CHP was UNDER (-29/-28/-4.5%), because the
# MISO CHP fleet is BTM-dominated (chp_btm_floor_pct) and held off the grid, not
# clearing cheap on the steam-credited HR. Applying the correction there only
# pushed CT_CHP further under (to -63/-63/-42%) with no gating-criterion gain, so
# the sub-physical HR is not the operative error for MISO CHP (a BTM/commitment
# root cause is) and the physics correction is left off until that is addressed.
CHP_STEAM_CREDIT_HR_CORRECTION_ISOS: frozenset[str] = frozenset({"CAISO", "PJM"})

# The summer WEFOR reallocation share and the per-class summer ambient derate
# were RE-HOMED to config/fuel_trajectories.py (miso-91, 2026-07-26), beside
# the THERMAL_AVAILABILITY table they modify, so that
# scripts/validate_parameters.py covers them (it scans only vars(constants) +
# ScenarioConfig defaults, skipping private/non-uppercase names, so private
# literals here were invisible to it — CLAUDE.md rule 20 [R-REGISTRY]).
# Values are unchanged; see those definitions for provenance, the recorded
# physics tension, and the standing prohibition on re-tuning them.
#
# The private aliases below are the module-local names the availability builder
# and its tests use; keeping them means the seasonal-availability code and the
# fleet package's re-export contract are untouched by the move.
_SUMMER_WEFOR_SHARE: float = SUMMER_WEFOR_SHARE
_SUMMER_CLASS_DERATE: dict[str, float] = SUMMER_CLASS_DERATE

# Non-coal thermal classes whose statistical planned-outage factor (POF) is
# dropped in the historic backcast (gated on config.coal_drop_pof): their
# planned outages now come from the CAMPD overlay + the unit-level derate, so
# the shoulder-month POF would double-count. Combustion turbines (CT_PEAKER /
# CT_CHP) keep POF — they have no historic overlay coverage and are excluded
# from the unit derate.
_POF_DROP_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
)

# Per-plant coal sustained-output ceilings now live in
# constants.COAL_MAX_CF_BY_PLANT (re-derived from CAMPD outage-adjusted
# availability physics, not observed output — see
# scripts/data/derive_coal_max_cf.py). The year-specific (6179, 2025) override that
# used to sit here was deleted outright: a single confirmed-unit-outage year
# has no forward analogue, and the historic-outage overlay already zeros the
# actual outage hours for backcast runs.
# Summer-only (Jun-Sep) ceilings: an ambient/derate cap that only binds in the
# heat (the unit runs higher the rest of the year).
COAL_SUMMER_MAX_CF: dict[int, float] = {
    7030: 0.87,  # Major Oak — ~13% summer derate
}


def _reconciled_summer_ratios(
    generators: list["Generator"], reconcile_path: str | None
) -> dict[int, float]:
    """Return ``{plant_code: min(1, net_summer / carried CC capacity)}`` for the
    CC plants a ``cc_capacity_reconcile`` table lists.

    Support for ``ScenarioConfig.cc_summer_derate_reconciled_basis`` (nyiso-212,
    rule 19 ``[R-ONE-MECH]``). Under ``cc_nameplate_summer_derate`` the Jun-Sep
    multiplier is ``net_summer / nameplate`` (:func:`cc_summer_derate_ratio`),
    premised on ``fleet_to_bins`` having carried the plant at NAMEPLATE. A
    reconcile row moves that capacity to the CAMPD demonstrated peak AFTER the
    rescale (``campd_bins._reconcile_cc_capacity``), and the nameplate ratio was
    still applied to it — so a ``cap`` plant's summer capability read
    ``reconciled x net_summer / nameplate`` instead of ``net_summer`` (Cricket
    Valley 57185: 1,086.9 x 1016.1/1312.5 = 841.4 MW against a published
    net-summer rating of 1,016.1 and a measured summer p99.9 of 1,078;
    FINDING-nyiso212). Here the ratio's denominator is the capacity the plant
    ACTUALLY carries — the summed ``pmax_mw`` of its CC generators after the
    reconcile — so the summer capability is stated once, as the published
    net-summer rating, and the cap bounds the year. Only plants the table lists
    are returned: an unlisted plant's carried capacity IS its nameplate, so its
    ratio is unchanged and the caller's incumbent path is byte-identical there.
    A missing table yields ``{}`` (the flag no-ops with the reconcile it
    repairs). Zero free parameters.
    """
    from pathlib import Path as _Path

    import pandas as _pd

    if not reconcile_path:
        return {}
    path = _Path(reconcile_path)
    if not path.exists():
        return {}
    listed = set(_pd.read_csv(path, usecols=["plant_code"])["plant_code"].astype(int))
    carried: dict[int, float] = {}
    for g in generators:
        if g.plant_group in ("CC_REGULAR", "CC_CHP") and int(g.plant_code) in listed:
            carried[int(g.plant_code)] = carried.get(int(g.plant_code), 0.0) + float(
                g.pmax_mw
            )
    caps = _pkg_ns().cc_summer_capacity()
    out: dict[int, float] = {}
    for code, cap_mw in carried.items():
        pair = caps.get(code)
        if pair is None or cap_mw <= 0.0:
            continue
        out[code] = min(1.0, float(pair[1]) / cap_mw)
    return out


def _thermal_outage(category: str, age: float) -> tuple[float, float, float]:
    """Return ``(POF, WEFOR, derate)`` for a thermal unit's age.

    ``category`` is the plant group (e.g. ``CC_REGULAR``, ``ST_GAS``,
    ``COAL``). POF is flat; WEFOR and the weather/performance derate are a
    base plus a linear escalation per year of age past an onset year. The
    three are additive — availability is ``1 - WEFOR - derate`` flat
    year-round, less ``POF`` in the shoulder months.
    """
    pof, w_base, w_rate, w_onset, d_base, d_rate, d_onset = THERMAL_AVAILABILITY[
        category
    ]
    wefor = w_base + max(0.0, age - w_onset) * w_rate
    derate = d_base + max(0.0, age - d_onset) * d_rate
    return pof, wefor, derate


def _nuclear_monthly(
    generators: list[Generator],
    availability: np.ndarray,
    hours: int,
    _iso: str | None,
    _yr: int | None,
    config: ScenarioConfig | None,
) -> None:
    """Apply nuclear monthly / unit-level / dormant availability in place.

    Pure array helper extracted verbatim from
    ``generators_to_fleet_arrays`` (fleet-package split sub-task (a));
    mutates ``availability`` rows of nuclear units only.
    """
    # Apply nuclear monthly availability factors (refueling outages, planned
    # maintenance). NUCLEAR_MONTHLY_CF holds 12 monthly capacity-factor caps
    # from NRC PRIS data; they multiply the EFORD derate to give the final
    # hourly availability. Non-nuclear units keep the flat 1 - eford derate.
    # Prefer the per-year 923-derived refueling pattern for the backcast;
    # fall back to the fixed seasonal average for forecast years.
    monthly_cf = NUCLEAR_MONTHLY_CF_BY_YEAR.get(_iso, {}).get(_yr) if _iso else None
    # The 923-derived per-year CF is realized availability (it already embeds
    # refueling + forced outages + derate), so it is used directly. The static
    # forecast pattern is a planned-outage cap, so the EFORD forced-outage
    # derate is layered on top of it.
    from_actual = monthly_cf is not None
    if monthly_cf is None and _iso:
        monthly_cf = NUCLEAR_MONTHLY_CF.get(_iso)
    if monthly_cf is not None:
        monthly_factors = np.array(monthly_cf, dtype=float)
        month_idx = _hour_to_month_index(hours)
        for g_idx, gen in enumerate(generators):
            if gen.fuel_type == "nuclear":
                base = monthly_factors[month_idx]
                availability[g_idx, :] = (
                    base if from_actual else (1.0 - gen.eford) * base
                )
    # ERCOT unit-level (window-grain) nuclear refuel availability
    # (config.ercot_nuclear_unit_availability, backcast measured overlay): the
    # measured per-reactor DAILY series from the 60-Day DAM disclosure replaces
    # the fleet-month smear above on covered dates — the smear carries the
    # right monthly energy but mis-times the refuel windows within the month
    # (e.g. 2024: STP-2 out 3/23-5/19 spanning the Apr/May scarcity events
    # while all four units were back for the May-24..27 record heat). NaN =
    # uncovered date -> the monthly value above is kept. Applied BEFORE the
    # nuclear flat must-run floor is built, so min_gen tracks it automatically.
    if (
        _iso == "ERCOT"
        and _yr is not None
        and getattr(config, "ercot_nuclear_unit_availability", False)
    ):
        from market_sim.data.outages import ercot_nuclear_unit_availability_series

        daily = ercot_nuclear_unit_availability_series(int(_yr), hours)
        if daily:
            applied_nuc = 0
            for g_idx, gen in enumerate(generators):
                if gen.fuel_type != "nuclear":
                    continue
                tail = str(gen.unit_id).rsplit("_", 1)[-1]
                if not tail.isdigit():
                    continue
                series = daily.get((int(gen.plant_code), int(tail)))
                if series is None:
                    continue
                covered = np.isfinite(series)
                availability[g_idx, covered] = series[covered]
                applied_nuc += 1
            logger.info(
                "ERCOT nuclear unit-availability overlay (%d): %d reactor(s) "
                "on measured daily windows (uncovered dates keep the monthly CF)",
                _yr,
                applied_nuc,
            )
    # ISO-generic unit-level nuclear availability
    # (config.nuclear_unit_availability, backcast measured overlay): the
    # per-reactor DAILY series from the NRC Power Reactor Status reports
    # replaces the fleet-month smear above on covered dates — same
    # construction and NaN semantics as the ERCOT block (which keeps its own
    # flag/file, hence the explicit ERCOT exclusion). Uncovered dates —
    # including the uprate-season months the deriver drops for the
    # thermal-vs-net wedge — keep the monthly value above. Applied BEFORE the
    # nuclear flat must-run floor is built, so min_gen tracks it, and BEFORE
    # the dormant-unit zeroing, which still wins for dormant plants.
    if (
        _iso is not None
        and _iso != "ERCOT"
        and _yr is not None
        and getattr(config, "nuclear_unit_availability", False)
    ):
        from market_sim.data.outages import nuclear_unit_availability_series

        daily = nuclear_unit_availability_series(_iso, int(_yr), hours)
        if daily:
            applied_nuc = 0
            for g_idx, gen in enumerate(generators):
                if gen.fuel_type != "nuclear":
                    continue
                tail = str(gen.unit_id).rsplit("_", 1)[-1]
                if not tail.isdigit():
                    continue
                series = daily.get((int(gen.plant_code), int(tail)))
                if series is None:
                    continue
                covered = np.isfinite(series)
                availability[g_idx, covered] = series[covered]
                applied_nuc += 1
            logger.info(
                "%s nuclear unit-availability overlay (%d): %d reactor(s) "
                "on measured daily windows (uncovered dates keep the monthly CF)",
                _iso,
                _yr,
                applied_nuc,
            )
    # Dormant nuclear (EIA-860 lists OP but the unit is physically offline,
    # e.g. the Crane/TMI-1 restart): zero it in backcast years before its
    # return-to-service year. Forecast runs keep the unit — in backcast mode
    # weather_year is the calendar year; in forecast it is only a weather
    # shape, so the comparison would be meaningless there.
    if _yr is not None and getattr(config, "mode", "forecast") == "backcast":
        for g_idx, gen in enumerate(generators):
            if gen.fuel_type == "nuclear" and _yr < NUCLEAR_DORMANT_UNTIL.get(
                int(gen.plant_code), 0
            ):
                availability[g_idx, :] = 0.0


def _availability_matrix(
    generators: list[Generator],
    availability: np.ndarray,
    hours: int,
    config: ScenarioConfig | None,
    _iso: str | None,
    year: int | None,
    ct_floor_plants: set[int],
) -> None:
    """Apply the statistical thermal availability model in place.

    Age-based WEFOR/POF with the seasonal summer/shoulder split, the
    per-class/per-plant summer derates, and the ambient-temperature
    derate curves. Pure array helper extracted verbatim from
    ``generators_to_fleet_arrays`` (fleet-package split sub-task (a));
    mutates ``availability`` in place.
    """
    # Summer peak, spring/autumn shoulder, and winter — a 3-way partition of
    # the year. The shoulder absorbs the outage shifted out of summer; winter
    # is left at base availability so the winter peak is not derated.
    month = _hour_to_month_index(hours) + 1
    summer = np.isin(month, list(_SUMMER_MONTHS))
    shoulder = np.isin(month, list(_CC_SHOULDER_MONTHS))
    summer_hours = int(summer.sum())
    shoulder_hours = int(shoulder.sum())

    # Thermal availability: an age-based model keyed to the plant-group
    # category (THERMAL_AVAILABILITY). Each unit's annual outage energy is
    # conserved but concentrated away from the summer and winter demand peaks:
    #   * WEFOR (forced outages): only _SUMMER_WEFOR_SHARE applies in summer;
    #     the remaining (1 - share) is redistributed into the shoulder months
    #     only. Winter keeps the flat WEFOR.
    #   * POF (planned outages): applies in the shoulder months only — none in
    #     summer or winter, where load peaks.
    #   * The weather/performance derate stays flat year-round.
    # The annual-average availability of each unit is unchanged — only the
    # seasonal shape moves. Non-thermal units (nuclear, hydro, ...) keep the
    # 1 - EFORD derate. Age is the SOLVE year minus the unit's commission year.
    #
    if config is not None and shoulder_hours > 0:
        # FR-7 (forecast-readiness audit §3.2): two year meanings, separated
        # explicitly. ``fleet_year`` is the SOLVE year — the fleet clock that
        # drives the age-based WEFOR/derate escalation, so the fleet keeps
        # aging through a forecast horizon and a model-built entrant
        # (online_year > weather_year) never gets a negative age. It falls
        # back to ``config.weather_year`` only when no solve year is threaded
        # (legacy/test callers); in backcast the harness pins
        # weather_year == solve year, so the fallback is value-identical
        # there. ``config.weather_year`` itself remains the WEATHER-SHAPE key
        # (the pinned 8760) for the measured-temperature lookups below
        # (_td_year / _amb_year) — never the fleet clock.
        fleet_year = year if year is not None else config.weather_year
        summer_to_shoulder = summer_hours / shoulder_hours
        drop_coal_pof = getattr(config, "coal_drop_pof", False)
        # miso-160: the measured seasonal forced-outage shape, when armed,
        # replaces the uncited SUMMER_WEFOR_SHARE heuristic (per-ISO derived
        # value, rule 25 [R-ISO-SCOPE]; None -> the module constant,
        # byte-identical to the pre-field behavior). Same mechanism either
        # way: annual outage energy conserved, only the seasonal shape moves
        # (share > 1 puts summer ABOVE annual and the shoulder below - the
        # measured sign of forced outages under heat).
        _swf_override = getattr(config, "summer_wefor_share_override", None)
        swf_share = (
            _SUMMER_WEFOR_SHARE if _swf_override is None else float(_swf_override)
        )
        # Historic-backcast WEFOR residual: the CAMPD overlay + unit-level
        # derate already carry every >= 5-day outage for the covered classes
        # (coal + _POF_DROP_GROUPS), so their full statistical WEFOR would
        # double-count those events. Cap it at the short-outage residual the
        # overlay's detector floor leaves uncovered. CTs have no overlay
        # coverage and keep the full statistical model.
        wefor_res = (
            getattr(config, "wefor_residual", None)
            if getattr(config, "outage_source", "statistical") == "historic"
            else None
        )
        # CC nameplate + per-plant summer derate (config.cc_nameplate_summer_
        # derate): CC plants carry full nameplate capacity (raised in
        # fleet_to_bins) and are derated to their measured net-summer rating in
        # summer only. In a historic backcast the statistical WEFOR/POF/age
        # derate are also dropped for CC — the CAMPD outage overlay already
        # carries every real outage, so the statistical model double-counts.
        cc_np_derate = getattr(config, "cc_nameplate_summer_derate", False)
        # PUBLISHED seasonal capability basis (config.cc_winter_capability_basis,
        # caiso-186). Acts ONLY alongside cc_nameplate_summer_derate — the two
        # are one seasonal-capability statement, and with the parent off the
        # fleet carries net-summer capacity to which a winter rating cannot be
        # applied without a basis change fleet_to_bins did not make.
        cc_winter_basis = cc_np_derate and getattr(
            config, "cc_winter_capability_basis", False
        )
        # BASIS-AWARE flat summer derate (config.summer_derate_basis_aware,
        # miso-148). The flat _SUMMER_CLASS_DERATE is the nameplate->summer
        # ambient loss, so it belongs only on a NAMEPLATE-basis capacity. On
        # the per-plant EIA-860 path pmax already IS the published net-summer
        # rating, so re-applying it double counts (miso-141). Gated on
        # plant_level_fleet: a nameplate-basis fleet (ERCOT's CAMPD-bin path)
        # has no double count and must keep the derate. See the ScenarioConfig
        # field for the measured basis and the refuted alternative reading.
        _basis_aware = bool(
            getattr(config, "summer_derate_basis_aware", False)
        ) and bool(getattr(config, "plant_level_fleet", False))
        _measured_basis_plants: frozenset[int] = (
            _pkg_ns().summer_basis_measured_plants(_iso)
            if (_basis_aware and _iso)
            else frozenset()
        )

        def _basis_aware_suppresses(gen: "Generator") -> bool:
            """True when ``gen``'s pmax already IS a measured summer capability.

            False for every generator when the flag is off, so the off path is
            byte-inert. Plants the CC guard clipped onto a nameplate-like bound,
            and plants absent from EIA-860, are absent from the set and so KEEP
            the flat derate.
            """
            if not _basis_aware:
                return False
            try:
                return int(gen.plant_code) in _measured_basis_plants
            except (TypeError, ValueError):
                return False

        if _basis_aware:
            _kept = sorted(
                {
                    int(g.plant_code)
                    for g in generators
                    if g.plant_group in _SUMMER_CLASS_DERATE
                    and not _basis_aware_suppresses(g)
                }
            )
            logger.info(
                "basis-aware summer derate (%s): flat _SUMMER_CLASS_DERATE "
                "SUPPRESSED for %d of %d flat-derate units (pmax already the "
                "published net-summer rating); KEPT for %d unit(s) across %d "
                "plant(s) still on a nameplate-like basis %s",
                _iso,
                sum(
                    1
                    for g in generators
                    if g.plant_group in _SUMMER_CLASS_DERATE
                    and _basis_aware_suppresses(g)
                ),
                sum(1 for g in generators if g.plant_group in _SUMMER_CLASS_DERATE),
                sum(
                    1
                    for g in generators
                    if g.plant_group in _SUMMER_CLASS_DERATE
                    and not _basis_aware_suppresses(g)
                ),
                len(_kept),
                _kept[:20],
            )

        def _cc_seasonal_pair(gen: "Generator") -> tuple[float, float] | None:
            """``(summer_ratio, winter_ratio)`` for a CC gen, or ``None``.

            ``None`` whenever the flag is off, the generator is not a CC group,
            or the plant is absent from either EIA-860 map — in every one of
            those cases the caller falls back to the incumbent
            ``cc_summer_derate_ratio`` treatment, which is EXACTLY the fallback
            ``fleet_to_bins`` takes for the same plant, so the capacity basis
            and the availability legs can never disagree.
            """
            if not cc_winter_basis or gen.plant_group not in ("CC_REGULAR", "CC_CHP"):
                return None
            return _pkg_ns().cc_seasonal_capability_ratios(int(gen.plant_code))

        cc_np_derate_backcast = (
            cc_np_derate
            and getattr(config, "outage_source", "statistical") == "historic"
        )
        # FORECAST-mode monthly planned-maintenance shape (spec 1.7). When
        # enabled, the flat shoulder-POF block (POF subtracted uniformly across
        # _CC_SHOULDER_MONTHS) is replaced by the historically-derived
        # MAINTENANCE_MONTHLY_SHAPE — a per-group 12-month curve whose
        # month-length-weighted mean is 1, so the group's annual POF budget
        # (POF * shoulder_hours) is conserved exactly while its seasonal
        # distribution is sharpened (peaks Apr/Oct-Nov, ~0 at the Jul/Aug
        # summer peak). Backcast runs keep the legacy flat block. _maint_derate
        # returns the per-hour planned-maintenance derate for a unit's group.
        _mode = getattr(config, "mode", "forecast")
        use_maint_shape = _mode == "forecast" and getattr(
            config, "maintenance_monthly_shape", True
        )
        month0 = month - 1  # 0-based calendar month per hour, for shape lookup
        shoulder_frac = shoulder_hours / hours
        _maint_pooled = MAINTENANCE_MONTHLY_SHAPE.get("_POOLED")

        def _maint_derate(
            group: str, pof_value: float, pof_eff_legacy: float
        ) -> np.ndarray:
            """Per-hour planned-maintenance derate for ``group``.

            Forecast (shape on): ``POF * shoulder_frac * w[group][month]`` — the
            monthly curve, annual budget conserved. Otherwise (backcast, or shape
            off): the legacy flat block, ``pof_eff_legacy`` in the shoulder
            months and zero elsewhere (byte-identical to the prior model).
            """
            if use_maint_shape:
                w = np.asarray(
                    MAINTENANCE_MONTHLY_SHAPE.get(group, _maint_pooled), dtype=float
                )
                return pof_value * shoulder_frac * w[month0]
            out = np.zeros(hours, dtype=float)
            out[shoulder] = pof_eff_legacy
            return out

        # Temperature-dependent capacity derate (config.temp_dependent_derate).
        # Precompute, per zone, the measured hourly dry-bulb TMAX (deg C) for the
        # classes this switch derates, so the loop below can (a) SKIP the flat
        # net-summer derate for temp-covered generators and (b) apply the physical
        # temperature curve in the dedicated block after the loop. Zones with no
        # weather coverage keep the flat derate (graceful fallback). See the
        # ScenarioConfig.temp_dependent_derate docstring for the full rationale.
        _td_on = (
            bool(getattr(config, "temp_dependent_derate", False)) if config else False
        )
        # (slope per deg C, reference/onset temp deg C) by plant group
        _TD_PARAMS: dict[str, tuple[float, float]] = {}
        _td_tmax: dict[str, np.ndarray] = {}
        # FR-7 meaning note: _td_year keys MEASURED-WEATHER series (zone
        # dry-bulb), i.e. "the weather 8760 this solve rides" — the solve
        # year while the solve is on realized/bridged weather (backcast, and
        # the hindcast's realized years, where it must stay aligned with the
        # realized demand of the same year), weather_year as the legacy
        # fallback. A pure-forward year has no measured file and falls back
        # gracefully to the flat class derate below (the single-pinned-
        # weather limitation is FR-17's workstream, not this seam). It is
        # NOT the fleet clock — never use it for the age model.
        _td_year = (
            year
            if year is not None
            else (getattr(config, "weather_year", None) if config else None)
        )
        # Hour-grain leg (config.temp_derate_hourly_grain): feed the curve the
        # diurnal dry-bulb reconstruction instead of the day-flat TMAX, so the
        # derate carries an hour-of-day capability wave. Falls back to the
        # day-flat series for any zone whose source lacks TMIN (byte-identical
        # to the committed path there).
        _td_hourly = (
            bool(getattr(config, "temp_derate_hourly_grain", False))
            if config
            else False
        )
        # Mean-anchored leg (config.temp_derate_mean_anchored): no hinge, curve
        # evaluated about the zone's own annual-mean dry-bulb, annual mean 1.0.
        _td_anchored = (
            bool(getattr(config, "temp_derate_mean_anchored", False))
            if config
            else False
        )
        if _td_on and _iso and _td_year:
            _ref = float(config.temp_derate_ref_c)
            # Cogen-specific slopes fall back to their merchant sibling's, so an
            # unset value is byte-identical to the committed behaviour.
            _slope_st_chp = getattr(config, "temp_derate_slope_st_chp", None)
            _slope_ct_chp = getattr(config, "temp_derate_slope_ct_chp", None)
            _TD_PARAMS = {
                "CC_REGULAR": (float(config.temp_derate_slope_cc), _ref),
                "CC_CHP": (float(config.temp_derate_slope_cc), _ref),
                "CT_PEAKER": (float(config.temp_derate_slope_ct), _ref),
                "CT_CHP": (
                    float(
                        _slope_ct_chp
                        if _slope_ct_chp is not None
                        else config.temp_derate_slope_ct
                    ),
                    _ref,
                ),
                "ST_GAS": (float(config.temp_derate_slope_st_gas), _ref),
                "ST_CHP": (
                    float(
                        _slope_st_chp
                        if _slope_st_chp is not None
                        else config.temp_derate_slope_st_gas
                    ),
                    _ref,
                ),
                # Every coal subclass reads the coal slope/reference (COAL-SUB).
                **{
                    _cc: (
                        float(config.temp_derate_slope_coal),
                        float(config.temp_derate_ref_c_coal),
                    )
                    for _cc in COAL_CLASSES
                },
            }
            # Class scope (config.temp_derate_classes): an ISO arms only the
            # classes it has identified on its own fleet (rule 25 [R-ISO-SCOPE]).
            _td_scope = getattr(config, "temp_derate_classes", None)
            if _td_scope:
                _TD_PARAMS = {
                    k: v for k, v in _TD_PARAMS.items() if k in set(_td_scope)
                }
            from market_sim.data.eia_loader import (
                iso_zone_hourly_drybulb,
                iso_zone_tmax,
            )

            _td_zones = {g.zone for g in generators if g.plant_group in _TD_PARAMS}
            for _z in _td_zones:
                _series = None
                if _td_hourly:
                    _series = iso_zone_hourly_drybulb(
                        _iso, int(_td_year), hours, zone=_z
                    )
                if _series is None:
                    _t = iso_zone_tmax(_iso, int(_td_year), hours, zone=_z)
                    _series = _t[0] if (_t is not None and _t[0] is not None) else None
                if _series is not None:
                    _td_tmax[_z] = np.asarray(_series, dtype=float)

        def _td_covers(gen: "Generator") -> bool:
            """True when the temperature derate handles this generator's summer
            capability (so the flat net-summer derate must be skipped for it).

            Never true in mean-anchored mode: that leg is a pure SHAPE overlay
            with annual mean 1.0, so it composes ON TOP of the existing level
            treatment (the flat class derate / measured net-summer ratio) rather
            than replacing it. Replacing it there would silently move the class
            level, which the within-day estimator behind the slope explicitly
            does not identify.
            """
            return (
                _td_on
                and not _td_anchored
                and gen.plant_group in _TD_PARAMS
                and gen.zone in _td_tmax
            )

        # nyiso-212 seam repair (config.cc_summer_derate_reconciled_basis, GATED
        # default-off, rule 19 [R-ONE-MECH]): at a plant a cc_capacity_reconcile
        # row has moved off nameplate, the Jun-Sep multiplier below divides the
        # published net-summer rating by the capacity the plant ACTUALLY carries
        # instead of by nameplate (see _reconciled_summer_ratios). Empty — and
        # every read site below falls through to the incumbent ratio, byte-
        # identical — unless both this flag and the reconcile are armed.
        _recon_summer_ratio: dict[int, float] = {}
        if (
            cc_np_derate
            and getattr(config, "cc_summer_derate_reconciled_basis", False)
            and getattr(config, "cc_capacity_reconcile", False)
        ):
            _recon_summer_ratio = _reconciled_summer_ratios(
                generators, getattr(config, "cc_capacity_reconcile_path", None)
            )
            if _recon_summer_ratio:
                logger.info(
                    "CC summer derate on the reconciled basis (%s): %d reconciled "
                    "plant(s) take min(1, net_summer / carried capacity) in Jun-Sep",
                    _iso or "?",
                    len(_recon_summer_ratio),
                )
        # miso-273 (ScenarioConfig.wefor_residual_short_screened_coal): the
        # coal bins whose sub-5-day forced outages the short family MEASURES
        # (unit-years that passed its baseload guard) take the WEFOR residual
        # cap on that measured capacity share only; the rest of the bin keeps
        # the full statistical term. Empty (byte-inert) while off.
        _screened_share: dict[tuple[int, str], float] = {}
        if wefor_res is not None and getattr(
            config, "wefor_residual_short_screened_coal", False
        ):
            if not getattr(config, "unit_outage_short_windows", False):
                raise ValueError(
                    "wefor_residual_short_screened_coal requires "
                    "unit_outage_short_windows: the relief is justified only "
                    "where the short coal family is armed (rule 19)"
                )
            if not getattr(config, "unit_outage_dispatched_bin_denominator", False):
                raise ValueError(
                    "wefor_residual_short_screened_coal requires "
                    "unit_outage_dispatched_bin_denominator"
                )
            _roster = lp_bin_capacity_index(generators)
            _screened_share = short_screened_coal_shares(
                int(fleet_year), _iso or "", _roster
            )
            logger.info(
                "short-screened coal WEFOR relief (%s %d): %d coal bin(s), "
                "%.1f MW measured-short capacity",
                _iso,
                int(fleet_year),
                len(_screened_share),
                sum(s * dict(_roster).get(k, 0.0) for k, s in _screened_share.items()),
            )
        for g_idx, gen in enumerate(generators):
            if gen.plant_group not in THERMAL_AVAILABILITY:
                continue
            is_cc_np = cc_np_derate and gen.plant_group in ("CC_REGULAR", "CC_CHP")
            pof, wefor, derate = _thermal_outage(
                gen.plant_group, fleet_year - gen.online_year
            )
            # ISO-gated gas-steam forced-outage base override. The global ST_GAS
            # WEFOR base (0.21) is fitted to ERCOT's once-through steamers and is
            # >2x every other thermal class — an implicit availability crush that
            # holds intermediate-duty steam off on top of the EIA-860 net-summer
            # rating already applied. When configured, replace the base with a
            # realistic NERC-GADS gas-steam EFOR, keeping the age escalation.
            _st_wefor_base = getattr(config, "gas_st_wefor_base_override", None)
            if _st_wefor_base is not None and gen.plant_group in ("ST_GAS", "ST_CHP"):
                _, _w_base, _w_rate, _w_onset, *_ = THERMAL_AVAILABILITY[
                    gen.plant_group
                ]
                _age = fleet_year - gen.online_year
                wefor = _st_wefor_base + max(0.0, _age - _w_onset) * _w_rate
            # Lighten (or raise) the forced-outage magnitude while keeping the
            # seasonal shape — applied before the summer/shoulder/winter split.
            wefor *= config.wefor_multiplier
            # WEFOR residual cap (historic-backcast double-count relief). By
            # default it applies to every CAMPD-covered class (coal +
            # _POF_DROP_GROUPS), whose sustained outages the overlay/unit/
            # partial derates already carry. ``wefor_residual_groups`` narrows
            # it to a chosen subset — the measured per-class evidence shows
            # the relief is only warranted where the class was actually
            # availability-capped (ST_GAS 2024) and is harmful where the
            # class is already over (CC) or displaces an un-relieved class
            # (CT keeps the full statistical model — no CAMPD coverage).
            _relief_groups = getattr(config, "wefor_residual_groups", None)
            _covered = (
                gen.plant_group in _relief_groups
                if _relief_groups
                else (gen.fuel_type == "coal" or gen.plant_group in _POF_DROP_GROUPS)
            )
            if wefor_res is not None and _covered:
                wefor = min(wefor, wefor_res)
            elif _screened_share and gen.fuel_type == "coal":
                _s = _screened_share.get(
                    (int(gen.plant_code), artifact_class(gen.plant_group)), 0.0
                )
                if _s > 0.0:
                    wefor = (1.0 - _s) * wefor + _s * min(wefor, wefor_res)
            if is_cc_np and cc_np_derate_backcast:
                # CC nameplate, historic backcast: the CAMPD outage overlay below
                # carries every SUSTAINED outage, so the statistical POF and the
                # age/performance derate are dropped (the net-summer rating
                # already captures performance). Only the short-outage forced
                # residual remains — wefor is already capped to
                # ``wefor_residual`` above for this overlay-covered class, the
                # brief forced events below the overlay's multi-day detector
                # floor — so the unit starts at ``1 - wefor_residual`` at
                # nameplate; the per-plant summer derate is applied below.
                availability[g_idx, :] = 1.0 - wefor
            elif is_cc_np:
                # CC nameplate, statistical/forward run: keep WEFOR/POF (no
                # overlay) but the seasonal cap comes from the per-plant summer
                # derate below, not the flat class derate.
                summer_wefor = swf_share * wefor
                shoulder_wefor = wefor + (1.0 - swf_share) * wefor * summer_to_shoulder
                pof_eff = 0.0 if drop_coal_pof else pof
                maint_h = _maint_derate(gen.plant_group, pof, pof_eff)
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - summer_wefor - derate
                availability[g_idx, shoulder] = 1.0 - shoulder_wefor - derate
                availability[g_idx, :] -= maint_h
            elif (
                gen.plant_group == "CT_PEAKER"
                and int(gen.plant_code) in ct_floor_plants
            ):
                # Reliability must-run floor unit: WEFOR and the planned-outage
                # (maintenance) derate do not apply — the floor injected below is
                # observed EIA-923 generation, which already embeds every real
                # outage, so the statistical outage model would double-count and
                # clip it. Keep only the flat performance derate (the summer
                # ambient derate still multiplies in below).
                availability[g_idx, :] = 1.0 - derate
            elif getattr(gen, "coal_sync_pmin_mw", 0.0) > 0.0:
                # Coal synchronization floor tranche (_mustrun / _sync): held at
                # the measured online Pmin via min_gen below. The STATISTICAL
                # WEFOR and planned-maintenance derate must NOT erode this floor
                # — a synced baseload coal unit physically holds min load in
                # every hour it is online, and the min_gen floor is clipped to
                # pmax x availability (line ~1682), so a statistical derate here
                # would silently pull the floor below its measured cap (the
                # MISO/Merom under-run bug). Genuine availability still relaxes
                # it: the historic facility outage overlay and the unit-level
                # outage derate apply AFTER this on the same array and still
                # zero/derate the floor during real outages, and the online%-
                # scaled top-k forcing already drops the floor in the bottom
                # (1 - online_frac) load hours the cycler genuinely shuts.
                # Mirrors the CT_PEAKER reliability-floor treatment above.
                availability[g_idx, :] = 1.0
            elif drop_coal_pof and gen.fuel_type == "coal":
                # Planned maintenance now comes from the historic outage
                # overlay, so drop the statistical POF (and its summer->shoulder
                # WEFOR redistribution) to avoid double-counting. Keep WEFOR in
                # the non-summer months and the derate all year; summer runs at
                # 1 - derate (WEFOR off for the peak).
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - derate
            else:
                summer_wefor = swf_share * wefor
                shoulder_wefor = wefor + (1.0 - swf_share) * wefor * summer_to_shoulder
                # Drop the shoulder POF for the historic-overlay classes (CC /
                # ST + their CHP) so it does not double-count the actual planned
                # outages from the overlay + unit derate; CTs keep POF.
                pof_eff = (
                    0.0
                    if drop_coal_pof and gen.plant_group in _POF_DROP_GROUPS
                    else pof
                )
                maint_h = _maint_derate(gen.plant_group, pof, pof_eff)
                # Default (winter): flat WEFOR. Then override summer and
                # shoulder for the WEFOR seasonal split, and subtract the
                # planned-maintenance derate across all months (forecast: the
                # monthly shape; backcast/legacy: pof_eff in the shoulder only).
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - summer_wefor - derate
                availability[g_idx, shoulder] = 1.0 - shoulder_wefor - derate
                availability[g_idx, :] -= maint_h
            # Per-bin forced derates for confirmed unit losses (e.g. a
            # multi-unit plant losing one boiler to a fire). Applied as a
            # flat multiplier on top of the age-based availability.
            # BACKCAST-ONLY (FR-8, rule 13 [R-MEASURED]): a measured
            # single-event derate has no forward analogue, so it must never
            # reach a forecast or crossover year — before this gate the
            # weather_year-keyed lookup re-applied the Martin Lake 2025 fire
            # to every crossover solve year under the pinned
            # weather_year=2025. Same explicit mode gate as the
            # dormant-nuclear sibling in _nuclear_monthly; keyed by the
            # solve year (== weather_year in backcast). The table's own
            # header (eia860.py) carries each entry's retirement path.
            if getattr(config, "mode", "forecast") == "backcast":
                forced = BIN_FORCED_DERATE_BY_YEAR.get(gen.bin_label, {}).get(
                    fleet_year
                )
                if forced is not None:
                    availability[g_idx, :] *= forced
            # Summer ambient-temperature derate. CC plants under
            # cc_nameplate_summer_derate use their per-plant MEASURED summer
            # derate (net_summer / nameplate) — the capacity was raised to
            # nameplate in fleet_to_bins, so this brings the summer months back
            # to the real net-summer rating. Every other class keeps the flat
            # ``_SUMMER_CLASS_DERATE``.
            # When config.temp_dependent_derate covers this generator's
            # zone+class, the flat/measured summer derate is SKIPPED here and
            # replaced by the temperature curve in the dedicated block after the
            # loop (it reproduces the same net-summer summer-mean for CC/CT, so
            # that is a reshape, not a level change).
            if not _td_covers(gen):
                if is_cc_np:
                    _pair = _cc_seasonal_pair(gen)
                    if _pair is None:
                        # Reconciled basis (nyiso-212) where armed and listed,
                        # else the incumbent nameplate ratio.
                        ratio = _recon_summer_ratio.get(int(gen.plant_code))
                        if ratio is None:
                            ratio = _pkg_ns().cc_summer_derate_ratio(
                                int(gen.plant_code)
                            )
                        if ratio is not None and ratio < 1.0:
                            availability[g_idx, summer] *= ratio
                    else:
                        # config.cc_winter_capability_basis (caiso-186): the bin
                        # is carried at the PUBLISHED seasonal envelope
                        # B = max(net_summer, winter), so each season takes its
                        # OWN published rating. The off-summer leg is the exact
                        # mirror of the summer leg — the same block, the same
                        # guard, the same source sheet — replacing the
                        # unpublished "full nameplate off-summer" premise, not
                        # stacking a second derate on it (rule 19 [R-ONE-MECH]).
                        _sr, _wr = _pair
                        if _sr < 1.0:
                            availability[g_idx, summer] *= _sr
                        if _wr < 1.0:
                            availability[g_idx, ~summer] *= _wr
                else:
                    summer_derate = _SUMMER_CLASS_DERATE.get(gen.plant_group)
                    if summer_derate and not _basis_aware_suppresses(gen):
                        availability[g_idx, summer] *= 1.0 - summer_derate
            # Per-plant coal max-CF ceilings: cap availability so the unit
            # cannot dispatch above its sustained operating limit.
            if is_coal_class(gen.plant_group):
                _pc = int(gen.plant_code)
                cap = COAL_MAX_CF_BY_PLANT.get(_pc)
                if cap is not None:
                    np.minimum(availability[g_idx, :], cap, out=availability[g_idx, :])
                scap = COAL_SUMMER_MAX_CF.get(_pc)
                if scap is not None:
                    availability[g_idx, summer] = np.minimum(
                        availability[g_idx, summer], scap
                    )
                # EIA-860 net-summer capacity derate (config.coal_nameplate_
                # summer_derate): coal carries nameplate in the LP but an old
                # steam unit cannot sustain nameplate in the summer — bring the
                # summer months down to the published net-summer rating
                # (net_summer / nameplate), the coal analogue of the CC/CT
                # cc_nameplate_summer_derate. Multiplicative, summer-only, only
                # reduces capacity; a plant rated at/above nameplate gets 1.0.
                if getattr(config, "coal_nameplate_summer_derate", False):
                    _ns_ratio = _pkg_ns().coal_summer_derate_ratio(_pc)
                    if _ns_ratio is not None and _ns_ratio < 1.0:
                        availability[g_idx, summer] *= _ns_ratio
        np.clip(availability, 0.0, 1.0, out=availability)

        # Gas-turbine ambient-temperature derate (config.gt_ambient_derate). The
        # net-summer/flat class derate above is a season-average rating; a GT
        # keeps losing output as ambient rises past that rating point, so the
        # hottest hours (where scarcity should occur) sit BELOW net-summer. Layer
        # a purely-additive incremental derate on CC/CT for hours whose measured
        # zone tmax exceeds the net-summer reference temp:
        #   extra(t) = slope_class x max(0, tmax_zone(t) - ref_c);  avail *= 1-extra
        # Physics (per-C slope) x measured hourly temperature x measured
        # net-summer anchor — a rule-11 physical input, forward-reproducible in
        # both backcast and forecast (never fitted to the price residual). Only
        # reduces capacity, only on hot hours. Vectorized per affected zone (no
        # per-hour Python loop, rule 2).
        # Same measured-weather keying as _td_year above (FR-7 meaning note):
        # the year of the zone-TMAX series, not the fleet clock.
        _amb_year = year if year is not None else getattr(config, "weather_year", None)
        if (
            getattr(config, "gt_ambient_derate", False)
            and not _td_on
            and _iso
            and _amb_year
        ):
            _amb_slope = {
                "CC_REGULAR": float(config.gt_ambient_derate_slope_cc),
                "CC_CHP": float(config.gt_ambient_derate_slope_cc),
                "CT_PEAKER": float(config.gt_ambient_derate_slope_ct),
                "CT_CHP": float(config.gt_ambient_derate_slope_ct),
            }
            _ref_c = float(config.gt_ambient_derate_ref_c)
            from market_sim.data.eia_loader import iso_zone_tmax

            _amb_zones = {g.zone for g in generators if g.plant_group in _amb_slope}
            _zone_over: dict[str, np.ndarray] = {}
            for _z in _amb_zones:
                _t = iso_zone_tmax(_iso, int(_amb_year), hours, zone=_z)
                if _t is not None and _t[0] is not None:
                    # degrees ABOVE the net-summer reference (0 below it)
                    _zone_over[_z] = np.maximum(0.0, np.asarray(_t[0], float) - _ref_c)
            if _zone_over:
                for g_idx, gen in enumerate(generators):
                    _slope = _amb_slope.get(gen.plant_group)
                    _over = _zone_over.get(gen.zone) if _slope else None
                    if _over is None:
                        continue
                    availability[g_idx, :] *= 1.0 - _slope * _over
                np.clip(availability, 0.0, 1.0, out=availability)

        # Temperature-dependent capacity derate (config.temp_dependent_derate).
        # Applies the per-class physical curve precomputed above. For CC/CT the
        # curve is rescaled so its SUMMER-hours mean reproduces the net-summer
        # capability it replaces (capacity-neutral reshape); COAL/ST_GAS take the
        # raw curve (a pure additive hot-hour condenser derate). Vectorized per
        # zone; the only Python loop is over generators, not hours (rule 2).
        # Availability is clipped to [0, 1], so it never exceeds the net-summer
        # pmax basis (no capacity is invented on cool hours).
        if _td_tmax:
            for g_idx, gen in enumerate(generators):
                _p = _TD_PARAMS.get(gen.plant_group)
                if _p is None:
                    continue
                _tmax = _td_tmax.get(gen.zone)
                if _tmax is None:
                    continue
                _slope, _ref_td = _p
                if _td_anchored:
                    # Mean-anchored (config.temp_derate_mean_anchored): NO hinge,
                    # evaluated about the zone's own annual-mean dry-bulb, so the
                    # curve's annual mean is exactly 1.0 and the arm claims only
                    # SHAPE, never level. The hinge form below asserts no
                    # response below ``_ref_td``; MISO's own CAMPD onset scan
                    # measures a clear response in the 5-15 C bins, which that
                    # hinge would zero (see ScenarioConfig.temp_derate_mean_
                    # anchored). Capability rises below the mean and falls above.
                    raw = 1.0 - _slope * (_tmax - float(np.mean(_tmax)))
                else:
                    # capacity fraction vs the ISO/onset rating point (<= 1.0)
                    raw = 1.0 - _slope * np.maximum(0.0, _tmax - _ref_td)
                # Net-summer anchor for classes that already carry a summer
                # derate: rescale so the Jun-Sep mean of the curve equals that
                # net-summer factor (reshape only). COAL/ST_GAS have no existing
                # summer derate -> no anchor, raw curve applied directly.
                # Skipped entirely in mean-anchored mode, where the flat derate
                # was never removed and the curve is already annual-mean 1.0 —
                # re-anchoring it on the summer mean there would re-introduce the
                # level move the mode exists to avoid.
                _cc_pair = None if _td_anchored else _cc_seasonal_pair(gen)
                if _td_anchored:
                    _anchor = None
                elif _cc_pair is not None:
                    # config.cc_winter_capability_basis: the SAME summer anchor,
                    # expressed against the published seasonal envelope B the
                    # bin is now carried at (net_summer / B, not
                    # net_summer / nameplate), so B x anchor is the published
                    # summer rating exactly as nameplate x (ns/np) was.
                    # Applied UNCONDITIONALLY, including at a ratio of exactly
                    # 1.0 — unlike the incumbent branch below, whose `< 1.0`
                    # skip leaves the curve UNANCHORED for a plant whose summer
                    # rating equals its nameplate, so that plant's summer mean
                    # lands at _sm x the rating instead of at the rating. This
                    # flag's identity is "each season's mean IS its published
                    # rating", for every plant or none; a per-plant exemption
                    # would be exactly the subsetting PRECHECK-caiso186 §6.4
                    # forbids.
                    _anchor = _cc_pair[0]
                elif cc_np_derate and gen.plant_group in ("CC_REGULAR", "CC_CHP"):
                    # Same two-way read as the summer leg above (nyiso-212), so
                    # the curve's anchor and the flat leg can never disagree.
                    _r = _recon_summer_ratio.get(int(gen.plant_code))
                    if _r is None:
                        _r = _pkg_ns().cc_summer_derate_ratio(int(gen.plant_code))
                    _anchor = _r if (_r is not None and _r < 1.0) else None
                elif gen.plant_group in _SUMMER_CLASS_DERATE:
                    # Basis-aware (miso-148): when the flat derate is suppressed
                    # for this plant the unit's summer capability IS its carried
                    # rating, so the curve's summer mean anchors at 1.0 — not at
                    # None, which would leave it unanchored and re-introduce an
                    # implicit derate through the back door. Inert on the MISO
                    # keeper, whose temp curve is mean-anchored (_anchor=None
                    # above), and kept consistent so the two read sites of the
                    # flat derate can never disagree in another configuration.
                    _anchor = (
                        1.0
                        if _basis_aware_suppresses(gen)
                        else 1.0 - _SUMMER_CLASS_DERATE[gen.plant_group]
                    )
                else:
                    _anchor = None
                if _anchor is not None:
                    _sm = float(np.mean(raw[summer]))
                    if _sm > 0.0:
                        raw = raw * (_anchor / _sm)
                if _cc_pair is not None:
                    # The OFF-SUMMER anchor — the mirror of the summer one above
                    # and the whole point of the flag. Today the curve is
                    # anchored on ONE season, and its summer-mean rescale is
                    # applied to all 8760 hours, so the off-summer LEVEL is an
                    # incidental by-product of a summer statistic that no
                    # published quantity asserts (PRECHECK-caiso186 §1a).
                    # Re-anchor the off-summer block so its own mean is the
                    # published winter ratio: B x (winter / B) = the published
                    # WINTER rating. The block is rescaled AFTER the summer
                    # rescale and about its own mean, so the result is
                    # independent of the summer leg and the summer block is
                    # untouched.
                    _osm = float(np.mean(raw[~summer]))
                    if _osm > 0.0:
                        raw = raw.copy()
                        raw[~summer] = raw[~summer] * (_cc_pair[1] / _osm)
                if _td_anchored:
                    # The mean-anchored curve is >1 on cold hours BY DESIGN (a
                    # gas turbine makes more than its rating point when the air
                    # is dense). Clipping the multiplier at 1 here would keep
                    # only the downward half and turn a level-neutral reshape
                    # into a net level cut; the trailing clip on availability
                    # still bounds the result at the pmax basis.
                    availability[g_idx, :] *= np.maximum(raw, 0.0)
                elif _cc_pair is not None:
                    # H-CLIP (PRECHECK-caiso186 §3b). The off-summer re-anchor
                    # can push the curve above 1 on the coldest hours; clipping
                    # it here would keep only the downward half and land the
                    # off-summer mean BELOW the published winter rating the
                    # anchor just set — the same asymmetry the mean-anchored
                    # branch above documents. The off-summer block therefore
                    # takes the lower bound only; the trailing clip on
                    # availability still bounds capability at the pmax basis B,
                    # so no capacity is invented above the published envelope.
                    # The SUMMER block keeps the incumbent clip unchanged.
                    _rawc = np.clip(raw, 0.0, 1.0)
                    _rawc[~summer] = np.maximum(raw[~summer], 0.0)
                    availability[g_idx, :] *= _rawc
                else:
                    availability[g_idx, :] *= np.clip(raw, 0.0, 1.0)
            np.clip(availability, 0.0, 1.0, out=availability)


def _apply_outage_overlays(
    generators: list[Generator],
    availability: np.ndarray,
    pmax: np.ndarray,
    heat_rate: np.ndarray,
    hours: int,
    config: ScenarioConfig | None,
    _iso: str | None,
    _yr: int | None,
) -> None:
    """Apply measured availability overlays in place (backcast layers).

    Historic CAMPD unit/partial/maxgen outage windows, retiree and
    CAMPD-blind caps, the NYSDEC peaker-rule windows, the ERCOT
    measured DAM class/hour/plant availability rescale, and the
    CC top-of-stack outage reallocation. Pure array helper extracted
    verbatim from ``generators_to_fleet_arrays`` (fleet-package split
    sub-task (a)); mutates ``availability`` in place.
    """
    # Historic-outage overlay (backcast only). When config.outage_source is
    # "historic", derate coal/CC/gas-steam availability during measured CAMPD
    # unit-outage windows, a hard override of the statistical WEFOR/POF model in
    # those hours. Forward/forecast runs leave outages statistical
    # (outage_source == "statistical", the default). The unit-level derate below
    # is the SOLE CAMPD outage layer for every ISO — the old facility-summed
    # overlay (the campd-outages*.csv builder, a hard availability=0 per plant;
    # its detection primitives now live in scripts/lib/outage_detect.py) was
    # removed 2026-07-17 because summing a plant's
    # units hid single-unit outages and folded daily-cycling combined cycles
    # into phantom summer outages
    # (results/calibration/FINDING-ercot79-phantom-outage-2026-07.md).
    if (
        config is not None
        and getattr(config, "outage_source", "statistical") == "historic"
    ):
        # ERCOT-only overlays further down in this block (noncampd availability
        # caps, retiree CEMS cap) gate on this; other ISOs skip them.
        is_ercot = _iso == "ERCOT" or _iso is None
        # miso-266 (ScenarioConfig.unit_outage_dispatched_bin_denominator,
        # GATED default-off): the derate DENOMINATOR, summed off the very
        # generators/pmax every factor below is then multiplied into — the
        # capacity the multiplier is applied to, which is the invariant
        # _iso_plant_capacity's own docstring states and cannot honour by
        # reconstruction (it is blind to the exit-cohort bins fleet/assembly.py
        # synthesizes under the same key). Built ONCE and shared by every layer,
        # because one denominator is one mechanism (rule 19 [R-ONE-MECH]).
        # ``None`` while off, so every loader takes its incumbent argument and
        # the off path is byte-inert.
        _lp_bins = (
            lp_bin_capacity_index(generators, pmax)
            if (
                getattr(config, "unit_outage_dispatched_bin_denominator", False)
                and not is_ercot
            )
            else None
        )
        # miso-272 point-of-use guard (ScenarioConfig.cc_block_summer_rating):
        # the reconstructed outage-capacity map (_iso_plant_capacity) is built
        # WITHOUT the block reconciliation, so dividing an overlay by it would
        # read the very phantom the flag removes. The dispatched-bin denominator
        # divides by the LP's own pmax and is the only construction that
        # composes with it — refuse the pair rather than no-op (rule 24).
        if (
            getattr(config, "cc_block_summer_rating", False)
            and not is_ercot
            and _lp_bins is None
        ):
            raise ValueError(
                "cc_block_summer_rating requires unit_outage_dispatched_bin_"
                "denominator under a non-ERCOT historic outage overlay: the "
                "reconstructed outage-capacity map does not carry the block "
                "reconciliation (rule 19 [R-ONE-MECH])"
            )
        # Unit-level outage derate (backcast): partial availability cut per
        # unit outage >= 5 days, sized by the unit's share of its plant's
        # capacity (CTs excluded; ERCOT split plants routed to the right asset
        # class). Catches single-unit outages a facility-summed CEMS series
        # hides — e.g. the W A Parish coal units, masked by the gas units that
        # keep running — and fully zeros a genuinely single-unit plant (the
        # unit's capacity == its plant-bin capacity, so the derate share is 1.0).
        # Built per ISO by scripts/data/derive_campd_unit_outages.py --iso <ISO>;
        # ISOs with no unit-outage file get an empty derate (no effect).
        # Multiplies the statistical availability already set above.
        ufac = unit_outage_derate_factors(
            config.weather_year,
            hours,
            getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
            iso=_iso or "ERCOT",
            cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
            cc_nameplate_basis=getattr(config, "unit_outage_lp_capacity_basis", False),
            st_capacity_basis=getattr(config, "unit_outage_st_capacity_basis", False),
            per_unit_clip=getattr(config, "unit_outage_per_unit_clip", False),
            extract_basis_share=getattr(
                config, "unit_outage_extract_basis_share", False
            ),
            fleet_status_scope=getattr(config, "unit_outage_fleet_status_scope", False),
            # SPP-48: the mid-vintage-year whole-plant exit channel injects
            # plants a year-matched native vintage drops from BOTH EIA sheets,
            # so the derate DENOMINATOR must carry them too — otherwise their
            # measured outage rows route to a (plant_code, plant_group) absent
            # from the map and are silently skipped, leaving the injected plant
            # un-capped (Oklaunion 127: the committed SPP extract carries its
            # real 2020-01-01 -> 05-19 and 09-26 -> 12-31 stops). Byte-inert
            # while off.
            mid_vintage_exit_carry=getattr(config, "mid_vintage_exit_carry", False),
            # miso-200 (rule 14 [R-ACCURATE]): route each unit's window by its
            # OWN CAMPD unitType at a facility carrying two or more model gas
            # bins, where _resolve_unit_group's fac_group short-circuit loses
            # its own stated premise. Selects the '-unitroute-' companion
            # extract; byte-inert while off.
            mixed_gas_routing=getattr(config, "unit_outage_mixed_gas_routing", False),
            # nyiso-175b/176 (rule 14 [R-ACCURATE], rule 19 [R-ONE-MECH]): the
            # WIDER form of the same repair — every unit routes by the shared
            # campd_measured_classes crosswalk, not just the mixed-gas subset,
            # and the SAME gate selects the tranche artifact's matching
            # '-perunit-' companion, because a tranche row's online/committed
            # statistics are computed over an outage-derated denominator.
            # Selects the '-perunit-' extract; byte-inert while off. The maxgen
            # layer below is out of scope BY CONSTRUCTION (no '-perunit-'
            # companion is written for it) — a documented boundary, not an
            # oversight; it carries a miso-only registry and reaches no NYISO
            # plant.
            per_unit_crosswalk=getattr(config, "campd_per_unit_attribution", False),
            merit_order_guard=bool(getattr(config, "campd_per_unit_attribution", False))
            and bool(getattr(config, "campd_outage_merit_order_guard", False)),
            # nyiso-229 (rule 14 [R-ACCURATE], rule 19 [R-ONE-MECH]): the SAME
            # merit-guarded per-unit windows at their DETECTED HOUR grain, so
            # the loader stops re-expanding each window to 00:00-23:00 and
            # asserting up to 23 h per edge the detector never detected.
            # Predicated on BOTH flags above, so all three are one selector over
            # one artifact family; selects the '-perunitmerithour-' extract and
            # is byte-inert while off (it reads the same file it always did).
            hour_grain=bool(getattr(config, "campd_per_unit_attribution", False))
            and bool(getattr(config, "campd_outage_merit_order_guard", False))
            and bool(getattr(config, "unit_outage_window_hour_grain", False)),
            # SOCO-61 (rule 14 [R-ACCURATE]): the SAME per-unit extract plus one
            # full-year window per unit its own CAMPD id files dark all year
            # while producing in an adjacent year. Predicated on the per-unit
            # flag; selects '-perunitdark-' and is byte-inert while off.
            dark_unit_years=bool(getattr(config, "campd_per_unit_attribution", False))
            and bool(getattr(config, "campd_dark_unit_year_windows", False)),
            # miso-266: the dispatched bin's own capacity as the denominator.
            lp_bin_capacity=_lp_bins,
            # soco-67 (rule 19 [R-ONE-MECH]): drop a new unit's pre-commercial
            # window hours, which the COD ramp below already holds offline.
            # Byte-inert while off (the extract is read unchanged).
            precod_clip=bool(getattr(config, "unit_outage_precod_clip", False)),
        )
        # DAM-first outage precedence (backcast overlay, gated per ISO). Where an
        # ISO publishes its own availability instrument, use it IN PLACE OF the
        # CAMPD unit-outage derate for the scope it covers, keeping the CAMPD
        # window as the fallback everywhere it does not reach. Both loaders below
        # match unit_outage_derate_factors' {(plant_code, plant_group): (hours,)
        # multiplier} interface, so precedence is a per-key merge into ``ufac`` —
        # no double-count (exactly one factor per key), grain-preserving, and a
        # clean no-op when off (``ufac`` stays the CAMPD derate above, untouched).
        # The uniform ISO-neutral loaders are keyed to their ISO, so the wrong-ISO
        # branch never fires. Backcast-only (this block already gates on
        # outage_source == "historic"; the explicit mode guard mirrors ERCOT).
        if (
            _iso == "CAISO"
            and getattr(config, "caiso_dam_outages", False)
            and getattr(config, "mode", "forecast") == "backcast"
        ):
            # Per-PLANT grain: CAISO's measured DAM curtailment reports cover only
            # the thermal plants they name (crosswalked); those plants take the
            # measured schedule, while every other plant — and any pre-2021-06-18
            # year with no series — keeps its CAMPD window. DAM wins per covered
            # (plant_code, plant_group); the rest fall back, never silently zeroed.
            from market_sim.data.caiso_outages import (
                caiso_dam_outage_derate_factors,
                has_dam_coverage,
            )

            if has_dam_coverage(config.weather_year):
                _dam = caiso_dam_outage_derate_factors(
                    config.weather_year, hours, iso="CAISO"
                )
                if _dam:
                    ufac = {**ufac, **_dam}  # DAM wins for covered plants
                    logger.info(
                        "CAISO DAM-outage precedence (%d): %d plant-tranche(s) "
                        "from measured curtailment reports override CAMPD",
                        config.weather_year,
                        len(_dam),
                    )
        elif (
            _iso == "MISO"
            and getattr(config, "miso_native_outage_source", False)
            and getattr(config, "mode", "forecast") == "backcast"
        ):
            # AGGREGATE grain: MISO's published region/cause offline-MW envelope
            # covers the WHOLE fossil-thermal fleet uniformly (one measured
            # availability fraction on every thermal bin), so a covered year
            # REPLACES the CAMPD derate outright. A year the record does not cover
            # (pre-2023) returns an empty dict and keeps CAMPD (the fallback).
            from market_sim.data.miso_outages import (
                miso_native_outage_derate_factors,
            )

            _dam = miso_native_outage_derate_factors(
                config.weather_year, hours, iso=_iso
            )
            if _dam:
                ufac = _dam  # native envelope replaces CAMPD for covered years
                logger.info(
                    "MISO native-outage precedence (%d): measured Multiday "
                    "Operating Margin envelope replaces CAMPD on %d thermal "
                    "bin(s)",
                    config.weather_year,
                    len(_dam),
                )
        if ufac:
            # NEISO temperature-reliability-floor exemption (CLAUDE.md #11). The
            # lone Merrimack-class COAL unit and lone ST_GAS unit are winter
            # cold-snap RELIABILITY runners whose commitment is governed by
            # transmission.inject_reliability_floor, with coefficients
            # regressed from each unit's own measured CAMPD capacity factor. That
            # regression already nets out the unit's real maintenance downtime, so
            # re-applying the CF-gap unit-outage derate on top double-counts it.
            # Worse, for a unit that runs only on cold snaps (sub-10% annual CF)
            # the detector's "sustained CF < 5%" rule reads the unit's *economic
            # idleness* as a forced outage, and the derate's unit_capacity_mw /
            # plant_capacity_mw fraction is taken against the 108 MW model bin
            # while the CSV's unit capacities are the real ~460 MW plant, so a
            # single coal-unit "outage" over-derates the bin to zero -- collapsing
            # availability (0 of 8760 h in 2024) and structurally capping the
            # floor (frac x available) at ~0. The floor is the correct,
            # forward-faithful availability/commitment model for these units, so
            # exempt them here exactly as the ct_mustrun_per_plant floor exempts
            # its units from WEFOR/planned outage. Scoped to NEISO + the two floor
            # classes + floor-on, so non-floor runs stay byte-identical.
            neiso_floor_exempt = _iso == "NEISO" and getattr(
                config, "reliability_floor", False
            )
            exempt_groups = {*COAL_CLASSES, "ST_GAS"}
            applied_u = 0
            exempted_u = 0
            for g_idx, gen in enumerate(generators):
                if neiso_floor_exempt and gen.plant_group in exempt_groups:
                    exempted_u += 1
                    continue
                f = ufac.get((int(gen.plant_code), artifact_class(gen.plant_group)))
                if f is not None:
                    availability[g_idx, :] *= f
                    applied_u += 1
            logger.info(
                "unit-outage derate (%s %d): %d plant-tranches derated%s",
                _iso or "ERCOT",
                config.weather_year,
                applied_u,
                (
                    f"; {exempted_u} NEISO floor-class tranche(s) exempted "
                    "(temp-reliability floor governs availability)"
                    if exempted_u
                    else ""
                ),
            )
        # Short (< 5-day) baseload-coal unit-outage windows (gated,
        # config.unit_outage_short_windows): the sub-floor companion of the
        # unit-outage derate above. The >= 5-day duration floor makes
        # event-coincident short forced outages invisible (MISO Jul 28-29
        # 2025: ~2.8 GW of coal capability offline at the peak block beyond
        # the overlay), while the own-fleet temp-capability envelope is flat —
        # the fleet loses discrete units under stress rather than derating
        # smoothly. Windows are < 5 days by construction (disjoint from the
        # overlay above) and pass the derive script's identification guards
        # (coal-only, baseload CF >= 0.55, revealed-availability filter).
        # R-NEISO (2026-09-24): the GAS scope (unit_outage_short_windows_gas)
        # is armable on its own. It used to be reachable only inside the coal
        # gate, so an ISO whose coal sub-5-day family was REJECTED on its own
        # evidence (NEISO, neiso-69) could not carry the disjoint gas family
        # without re-arming the rejected one. coal_scope keeps the coal file
        # out when only the gas flag is set; with the coal flag set the call
        # is byte-identical to before.
        _short_coal = getattr(config, "unit_outage_short_windows", False)
        _short_gas = getattr(config, "unit_outage_short_windows_gas", False)
        if _short_coal or _short_gas:
            sfac = unit_outage_short_derate_factors(
                config.weather_year,
                hours,
                getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
                iso=_iso or "ERCOT",
                cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
                cc_nameplate_basis=getattr(
                    config, "unit_outage_lp_capacity_basis", False
                ),
                st_capacity_basis=getattr(
                    config, "unit_outage_st_capacity_basis", False
                ),
                per_unit_clip=getattr(config, "unit_outage_per_unit_clip", False),
                extract_basis_share=getattr(
                    config, "unit_outage_extract_basis_share", False
                ),
                fleet_status_scope=getattr(
                    config, "unit_outage_fleet_status_scope", False
                ),
                # pjm-d4-4: additionally read the DISJOINT gas-side companion
                # (campd-unit-outages-shortgas-<ISO>.csv). Widens a discard —
                # the < 5-day gas family the >= 5-day floor throws away — it
                # does not stack on the coal scope (disjoint plant groups) or on
                # the >= 5-day overlay (disjoint durations).
                gas_scope=getattr(config, "unit_outage_short_windows_gas", False),
                # SPP-48: the mid-vintage-year exit channel injects plants a
                # year-matched native vintage drops from BOTH EIA sheets, so
                # the derate DENOMINATOR must carry them or their measured
                # outage rows route to an absent (plant_code, plant_group) and
                # are silently skipped. Byte-inert while off.
                mid_vintage_exit_carry=getattr(config, "mid_vintage_exit_carry", False),
                # miso-266: the dispatched bin's own capacity as the
                # denominator — the same repair, on the same shared
                # accumulator, for the sub-5-day window family.
                lp_bin_capacity=_lp_bins,
                coal_scope=_short_coal,
            )
            if sfac:
                applied_s = 0
                for g_idx, gen in enumerate(generators):
                    f = sfac.get((int(gen.plant_code), artifact_class(gen.plant_group)))
                    if f is not None:
                        availability[g_idx, :] *= f
                        applied_s += 1
                logger.info(
                    "short unit-outage derate (%s %d): %d plant-tranches "
                    "derated (< 5-day windows; coal %s, gas %s)",
                    _iso or "ERCOT",
                    config.weather_year,
                    applied_s,
                    "on" if _short_coal else "off",
                    "on" if _short_gas else "off",
                )
        # Unit-grain partial-derate plateaus (gated,
        # config.unit_partial_outage_windows): the second window shape of the
        # measured unit-availability family. A baseload coal unit that keeps
        # running but at a depressed CF ceiling (half its capability out) never
        # reaches zero, so no full-stop window (>= 5-day or short) can represent
        # it. Detected on each unit's own CEMS with the plant-level partial
        # detector's frozen plateau constants + the same when-operable baseload
        # guard and in-merit filter as the short windows, then aggregated to the
        # plant by unit-capacity share (concurrent units summed, clipped at full)
        # exactly like the >= 5-day overlay — so it is keyed per (plant_code,
        # plant_group), NOT per plant_code like the ERCOT-only plant-grain
        # partial path below (which over-fires ~43 TWh/yr on PJM's cycling fleet
        # and stays ERCOT-scoped). Reads the per-ISO unit-grain file; ISOs
        # without it get an empty derate (no effect). Multiplies availability.
        if getattr(config, "unit_partial_outage_windows", False):
            ppfac = unit_partial_outage_derate_factors(
                config.weather_year,
                hours,
                getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
                iso=_iso or "ERCOT",
                cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
                cc_nameplate_basis=getattr(
                    config, "unit_outage_lp_capacity_basis", False
                ),
                st_capacity_basis=getattr(
                    config, "unit_outage_st_capacity_basis", False
                ),
                per_unit_clip=getattr(config, "unit_outage_per_unit_clip", False),
                extract_basis_share=getattr(
                    config, "unit_outage_extract_basis_share", False
                ),
                fleet_status_scope=getattr(
                    config, "unit_outage_fleet_status_scope", False
                ),
                # miso-266: the dispatched bin's own capacity as the
                # denominator (same shared accumulator).
                lp_bin_capacity=_lp_bins,
            )
            if ppfac:
                applied_pp = 0
                for g_idx, gen in enumerate(generators):
                    f = ppfac.get(
                        (int(gen.plant_code), artifact_class(gen.plant_group))
                    )
                    if f is not None:
                        availability[g_idx, :] *= f
                        applied_pp += 1
                logger.info(
                    "unit partial-outage derate (%s %d): %d plant-tranches "
                    "derated (unit-grain CF-ceiling plateaus)",
                    _iso or "ERCOT",
                    config.weather_year,
                    applied_pp,
                )
        # Declared-event-window revealed derates (gated,
        # config.unit_outage_maxgen_events): the third window shape of the
        # measured unit-availability family (M-2, MISO price-formation lane).
        # Per-unit MW reductions revealed by each unit's own CAMPD trace
        # inside the ISO's DECLARED capacity-emergency windows (the
        # maxgen-events registry) — the only channel that can carry the CT/CC
        # event-window leg (the std extract's 5-day floor and the short
        # channel's coal-only guard exclude it by design), so it is
        # class-agnostic. Identification lives in the deriver's frozen guards
        # (declared-window scope, $150 DA in-merit certificate, ±45-day
        # capability basis with best-event-hour credit, disjointness vs the
        # std/short extracts — scripts/data/derive_campd_maxgen_outages.py);
        # windows are hour-granular and clipped to the declared start/end.
        # Reads the per-ISO campd-unit-outages-maxgen-<ISO>.csv; ISOs without
        # it get an empty derate (no effect). Multiplies availability.
        if getattr(config, "unit_outage_maxgen_events", False):
            mgfac = unit_outage_maxgen_derate_factors(
                config.weather_year,
                hours,
                iso=_iso or "ERCOT",
                cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
                cc_nameplate_basis=getattr(
                    config, "unit_outage_lp_capacity_basis", False
                ),
                # unit_outage_st_capacity_basis is DELIBERATELY NOT passed here.
                # This layer's rows carry a measured derate_mw — a partial MW
                # reduction revealed by CEMS, NOT a unit capacity — so substituting
                # a fleet pmax_mw for it would substitute a capacity for a derate.
                # The routing repair had to move both layers together because a unit
                # routed to DIFFERENT BINS in the two is incoherent; a numerator
                # BASIS is per-layer and carries no such coupling (miso-201 PREREG §2).
                # unit_outage_per_unit_clip is DELIBERATELY NOT passed here either,
                # and the reason is a MEASUREMENT rather than an argument: this
                # layer's windows are already hour-granular
                # ([window_start, window_end), read straight off the extract), so
                # it cannot carry the boundary-DAY artifact the clip repairs, and
                # phase-0 N-5 confirmed ZERO same-unit window overlaps in it over
                # 544 unit-series. Passing the flag would be provably inert while
                # widening the blast radius (miso-202 PREREG §3).
                # Same routing repair, same flag: this layer shares
                # _resolve_unit_group, so it carries the same mis-attribution
                # and must move with the std layer (rule 19 [R-ONE-MECH]).
                mixed_gas_routing=getattr(
                    config, "unit_outage_mixed_gas_routing", False
                ),
                # miso-266: the dispatched bin's own capacity as the
                # denominator. This layer keeps its own accumulator loop but
                # divides by the SAME cap[bin] on the SAME key, so it carries
                # the identical defect and must move with the others (rule 19
                # [R-ONE-MECH]). Unlike st_capacity_basis above, this flag acts
                # on the DENOMINATOR, never on the measured derate_mw
                # numerator, so the objection recorded there does not apply.
                lp_bin_capacity=_lp_bins,
            )
            if mgfac:
                applied_mg = 0
                for g_idx, gen in enumerate(generators):
                    f = mgfac.get(
                        (int(gen.plant_code), artifact_class(gen.plant_group))
                    )
                    if f is not None:
                        availability[g_idx, :] *= f
                        applied_mg += 1
                logger.info(
                    "maxgen event-window derate (%s %d): %d plant-tranches "
                    "derated (declared-window revealed unit derates)",
                    _iso or "ERCOT",
                    config.weather_year,
                    applied_mg,
                )
        # Within-window retiree measured-availability cap (CAMPD unit-level):
        # a unit winding down to retirement is held at its coal must-run floor
        # by the cost-based LP while reality barely ran it (out-of-market
        # retirement economics the merit order cannot see, and the per-plant
        # binning collapses the per-unit COD before the ramp). Cap each retiree
        # plant's availability to its measured monthly CEMS envelope. Applied
        # before min_gen is built so the must-run floor (clamped to availability)
        # scales down with it. Plant-keyed (reaches every binned tranche),
        # scoped to the within-window retirees; the bulk fleet keeps its
        # cost-based dispatch. Gated to the validated ISO (config flag).
        if getattr(config, "retiree_cems_cap", False):
            rcaps = retiree_availability_caps(
                _iso or "ERCOT", config.weather_year, hours
            )
            if rcaps:
                applied_r = 0
                for g_idx, gen in enumerate(generators):
                    cap = rcaps.get(int(gen.plant_code))
                    if cap is not None:
                        np.minimum(
                            availability[g_idx, :], cap, out=availability[g_idx, :]
                        )
                        applied_r += 1
                logger.info(
                    "retiree CEMS availability cap (%s %d): %d tranche(s) across "
                    "%d retiree plant(s) capped to measured envelope",
                    _iso or "ERCOT",
                    config.weather_year,
                    applied_r,
                    len(rcaps),
                )
        # ERCOT CAMPD-blind per-plant availability (ercot_noncampd_plant_availability,
        # ERCOT-71): the ERCOT gas plants ABSENT from the TX CAMPD extract
        # (Kiamichi/Hidalgo/AVR/EG178 — has_campd_data=False) are invisible to the
        # CAMPD outage overlay above, so they ride flat statistical availability
        # while reality ran a real outage (Hidalgo 0 MWh Apr+May 2024) or committed
        # out of ERCOT (Kiamichi's switchable SPP share). Cap each blind plant's
        # availability to its measured per-plant series (60-Day DAM disclosure live
        # HSL + EIA-923 zero months; data.outages.ercot_noncampd_availability_caps).
        # Plant-keyed (reaches every binned tranche), ERCOT+backcast gated; the
        # covered fleet is untouched (surgical scope, rule 19). Applied before
        # min_gen is built so any must-run floor scales down with it.
        if getattr(config, "ercot_noncampd_plant_availability", False) and is_ercot:
            nccaps = ercot_noncampd_availability_caps(config.weather_year, hours)
            if nccaps:
                applied_nc = 0
                for g_idx, gen in enumerate(generators):
                    cap = nccaps.get(int(gen.plant_code))
                    if cap is not None:
                        np.minimum(
                            availability[g_idx, :], cap, out=availability[g_idx, :]
                        )
                        applied_nc += 1
                logger.info(
                    "ERCOT CAMPD-blind availability (%d): %d tranche(s) across "
                    "%d blind plant(s) capped to measured per-plant series",
                    config.weather_year,
                    applied_nc,
                    len(nccaps),
                )
        if not ufac:
            # A backcast year with no measured unit-outage windows (e.g.
            # CAISO 2023: no CA unit-level CEMS extract until upload U1 lands)
            # silently degrades to the statistical WEFOR/POF model; say so,
            # and record it in the run's model_changes_note.
            logger.warning(
                "outage_source='historic' but no outage windows cover %s %d; "
                "availability is statistical-only for this year",
                _iso or "ERCOT",
                config.weather_year,
            )
        # The partial-outage derate below is an ERCOT-only extract (CAMPD
        # CF-ceiling plateaus keyed to ERCOT plant codes); other ISOs carry no
        # such file, so it stays scoped to ERCOT.
        if is_ercot:
            # Partial-outage derate (CAMPD CF-ceiling plateaus): approximate
            # half-units-out events for baseload coal + a confirmed CC
            # allowlist where no unit data exists. Multiplies availability
            # over the window. Under the ercot-173 reconciliation gate the
            # lookup keys by the extract's own (plant_code, plant_group) — C1
            # grain repair — so a plateau lands only on the class bin its
            # extract row names (provably identical on the current bins sheet;
            # see partial_outage_derate_factors).
            _pgrain = getattr(
                config, "ercot_dam_availability_event_cap_reconciliation", False
            ) or getattr(config, "ercot_dam_availability_event_cap_unit_scoped", False)
            # ercot-185 fault-3 repair: the DAY-SHAPED plateau extract replaces
            # the flat multi-week factor. Same plateaus, same covered hours,
            # day-resolved profile — so this consumer and the event-cap ceiling
            # block below both see ONE repaired layer (rule 19 [R-ONE-MECH]).
            _pshaped = getattr(config, "ercot_partial_outage_shaped_derate", False)
            pfac = partial_outage_derate_factors(
                config.weather_year,
                hours,
                class_grain=_pgrain,
                shaped=_pshaped,
                # R-ERCOT-4 same-day CEMS guard on the shaped layer.
                day_guard=getattr(config, "ercot_partial_outage_day_guard", False),
            )
            if pfac:
                applied_p = 0
                for g_idx, gen in enumerate(generators):
                    _pkey = (
                        (int(gen.plant_code), artifact_class(gen.plant_group))
                        if _pgrain
                        else int(gen.plant_code)
                    )
                    f = pfac.get(_pkey)
                    if f is not None:
                        availability[g_idx, :] *= f
                        applied_p += 1
                logger.info(
                    "partial-outage derate (%d): %d bin-tranches derated",
                    config.weather_year,
                    applied_p,
                )

    # NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay
    # (config.nysdec_peaker_rule_availability, NYISO): units whose curated
    # compliance-schedule row is an ozone-season shutdown / reliability-only
    # restriction are unavailable to the energy market inside their effective
    # May 1 - Sep 30 windows. An exogenous regulatory availability event
    # (rule #12 class of the CAMPD outage windows) — availability only, never
    # an offer/price change — so it applies regardless of outage_source and in
    # any mode (the schedule is the regulation's, forward-valid). ``oil``
    # scope zeroes the plant's raw oil units (matched per generator id when
    # the row names units); ``gas_ct`` scope derates the plant's CT-class
    # tranches by restricted_mw / class capacity (full zero when the row
    # restricts the whole class).
    if config is not None and getattr(config, "nysdec_peaker_rule_availability", False):
        from market_sim.data.outages import nysdec_peaker_restrictions

        applied_dec = 0
        for r in nysdec_peaker_restrictions(config.weather_year, hours):
            code, scope = r["plant_code"], r["scope"]
            h_lo, h_hi = r["h_lo"], r["h_hi"]
            if scope == "oil":
                for g_idx, gen in enumerate(generators):
                    if int(gen.plant_code) != code or gen.fuel_type != "oil":
                        continue
                    if r["unit_ids"] and not any(
                        str(gen.unit_id).endswith(f"_{u}") for u in r["unit_ids"]
                    ):
                        continue
                    availability[g_idx, h_lo:h_hi] = 0.0
                    applied_dec += 1
            else:  # gas_ct: the plant's simple-cycle CT-class tranches
                idxs = [
                    g_idx
                    for g_idx, gen in enumerate(generators)
                    if int(gen.plant_code) == code
                    and gen.plant_group in ("CT_PEAKER", "CT_CHP")
                ]
                if not idxs:
                    continue
                class_mw = float(sum(pmax[i] for i in idxs))
                mw = r["restricted_mw"]
                frac = 1.0 if mw is None else min(1.0, mw / max(class_mw, 1e-9))
                for g_idx in idxs:
                    availability[g_idx, h_lo:h_hi] *= 1.0 - frac
                applied_dec += len(idxs)
        if applied_dec:
            logger.info(
                "NYSDEC 227-3 peaker-rule overlay (%s %d): %d unit/tranche "
                "availability window(s) restricted",
                _iso or "?",
                config.weather_year,
                applied_dec,
            )

    # ERCOT measured class-day thermal availability (backcast overlay,
    # config.ercot_thermal_dam_availability): rescale each covered class
    # (CC_REGULAR, CT_PEAKER — the deriver's scope) so its class-day MEAN
    # availability fraction equals the 60-Day DAM disclosure's measured
    # live-HSL / rating fraction. A RESCALE of the finished availability, not a
    # stacked multiplier: the measured fraction and the model's statistical
    # WEFOR/EFOR + window stack estimate the SAME quantity, so the class-day
    # total is set to the measured value while the model's own discrete
    # windows/plateaus remain the within-class distribution. Uncovered days
    # (NaN — the Oct-2023 hole, Nov-Dec 2025) keep the statistical model;
    # forecast mode is untouched (the statistical stack is the forward
    # analogue — the G4 mode-aware seam). Applied after every other
    # availability layer and before min_gen is built, so floors clamp to the
    # measured level. Tranches cap at 1.0; a 3-pass water-fill redistributes
    # the clipped mass so the class-day total still lands on the measured
    # fraction where feasible. Provenance + June/Sep-2023 forensics:
    # docs/DIAGNOSIS-ercot-june2023-scarcity-formation-2026-07.md.
    if (
        config is not None
        and _iso == "ERCOT"
        and getattr(config, "ercot_thermal_dam_availability", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        from market_sim.data.outages import ercot_thermal_dam_availability_series

        _meas = ercot_thermal_dam_availability_series(int(_yr), hours)
        # ERCOT-137 correctness fix (ERCOT-135 §7.2): the overlay's water-fill
        # ceiling is pmax × forced_derate, never raw pmax. The measured DAM
        # fraction is live/rating over the disclosure's OWN (post-unit-loss)
        # rating, while the model pmax still carries the destroyed unit —
        # only BIN_FORCED_DERATE_BY_YEAR knows it is gone (the CAMPD outage
        # derive can never detect a unit destroyed before the vintage
        # starts), so restoring toward 1.0 resurrected Martin Lake to 1.451×
        # its COP-declared max. Ceiling 1.0 everywhere else → bit-identical.
        _dam_ceil = np.array(
            [
                BIN_FORCED_DERATE_BY_YEAR.get(g.bin_label, {}).get(int(_yr), 1.0)
                for g in generators
            ],
            dtype=float,
        )
        # ERCOT-110 coal class-SCOPE gate
        # (config.ercot_thermal_dam_availability_coal). The deriver now emits
        # COAL_PRB / COAL_LIGNITE rows alongside the gas classes, so the coal
        # classes are dropped from EVERY measured dict here unless the gate is
        # armed — a re-derive can widen the artifacts without moving a keeper,
        # and an armed-gas run stays byte-identical to its pre-ERCOT-110 self.
        # Filtering the class dicts is sufficient and complete: both the
        # class-day and class-HOUR loops iterate them, and the plant grain only
        # forms mapped_plants for units of a class already in _meas_h, so a
        # coal plant in the crosswalk is unreachable while the gate is off.
        if not getattr(config, "ercot_thermal_dam_availability_coal", False):
            _meas = {k: v for k, v in _meas.items() if not k.startswith("COAL")}
        # ERCOT-96 grain switch (config.ercot_thermal_dam_availability_hourly):
        # apply the SAME measured mechanism at class-HOUR grain — the measured
        # per-Hour-Ending fraction replaces the day-flat block, keeping the
        # afternoon ambient-derate dip / overnight headroom the day mean
        # discards (ERCOT-95 Finding 6: +216 MW mean phantom CC+CT on the 181
        # actual 2023 tail hours). Same bidirectional water-fill semantics as
        # the day grain below, per hour: restore a' = a + λ(1−a) toward the
        # measured level, remove a' = a·(t/cur); the cap-weighted class-hour
        # mean lands exactly on the measured fraction, tranches cap at 1.0,
        # NaN hours keep the pre-overlay stack hour by hour. Classes the
        # hourly file does not cover fall through to the day-grain loop.
        _hourly_done: set[str] = set()
        if getattr(config, "ercot_thermal_dam_availability_hourly", False):
            from market_sim.data.outages import (
                ercot_thermal_dam_availability_hourly_series,
            )

            _meas_h = ercot_thermal_dam_availability_hourly_series(int(_yr), hours)
            if not getattr(config, "ercot_thermal_dam_availability_coal", False):
                # ERCOT-110 gate, class-HOUR grain (see the class-day filter).
                _meas_h = {k: v for k, v in _meas_h.items() if not k.startswith("COAL")}
            # ERCOT-97 plant grain (config.ercot_thermal_dam_availability_plant,
            # requires _hourly): pin each accepted-crosswalked plant to its own
            # measured site-hour fraction and water-fill the unmapped remainder
            # so the class-HOUR total is unchanged — a within-class
            # redistribution (which plant is derated), zero fitted parameters.
            # Classes it handles are added to _hourly_done so the class-HOUR
            # loop below skips them; a class with no crosswalked plant still
            # gets the plain class-HOUR treatment.
            if getattr(config, "ercot_thermal_dam_availability_plant", False):
                from market_sim.data.outages import (
                    ercot_thermal_dam_availability_plant_rating_series,
                    ercot_thermal_dam_availability_plant_series,
                )

                _plant_series = ercot_thermal_dam_availability_plant_series(
                    int(_yr), hours
                )
                if _plant_series:
                    _hourly_done |= _ercot_dam_plant_hourly_apply(
                        availability,
                        generators,
                        pmax,
                        hours,
                        int(_yr),
                        _meas_h,
                        _plant_series,
                        logger,
                        ceil_full=_dam_ceil,
                        # Ruling #10 (signature A1): the pin's remove
                        # direction is diluted to the plant's measured DAM
                        # coverage — see _ercot_dam_plant_hourly_apply.
                        plant_rating=(
                            ercot_thermal_dam_availability_plant_rating_series(
                                int(_yr), hours
                            )
                        ),
                    )
            for _cls, _t_h in _meas_h.items():
                if _cls in _hourly_done:
                    continue  # ERCOT-97: handled at the finer plant grain
                _idx = np.array(
                    [
                        gi
                        for gi, g in enumerate(generators)
                        if artifact_class(g.plant_group) == _cls
                    ],
                    dtype=int,
                )
                if _idx.size == 0:
                    continue
                _cap = pmax[_idx]  # (n,)
                _cap_sum = float(_cap.sum())
                if _cap_sum <= 0.0:
                    continue
                _t = _t_h[:hours]  # (hours,) measured fraction, NaN uncovered
                _covered = np.isfinite(_t)
                if not _covered.any():
                    continue
                _a = availability[_idx, :hours]  # (n, hours)
                _cur = (_a * _cap[:, None]).sum(axis=0) / _cap_sum  # (hours,)
                _restore = _covered & (_t >= _cur)
                _remove = _covered & (_t < _cur)
                # Per-unit forced-derate ceiling (ERCOT-137; 1.0 everywhere
                # no BIN_FORCED_DERATE_BY_YEAR entry exists → bit-identical).
                _ceil = _dam_ceil[_idx]
                _ceil_mean = float((_ceil * _cap).sum()) / _cap_sum
                _lam = np.clip(
                    (_t - _cur) / np.maximum(_ceil_mean - _cur, 1e-9), 0.0, 1.0
                )
                _new = _a.copy()
                _new[:, _restore] = _a[:, _restore] + _lam[None, _restore] * np.maximum(
                    _ceil[:, None] - _a[:, _restore], 0.0
                )
                _mu = np.where(_remove, _t / np.maximum(_cur, 1e-9), 1.0)
                _new[:, _remove] = _a[:, _remove] * _mu[None, _remove]
                availability[_idx, :hours] = np.minimum(_new, _ceil[:, None])
                _hourly_done.add(_cls)
                logger.info(
                    "ERCOT measured thermal DAM availability (%d): %s set to "
                    "measured class-HOUR level on %d hour(s) (restore %d / "
                    "remove %d), median target %.3f",
                    _yr,
                    _cls,
                    int(_covered.sum()),
                    int(_restore.sum()),
                    int(_remove.sum()),
                    float(np.median(_t[_covered])),
                )
        _n_days = hours // 24
        for _cls, _target_h in _meas.items():
            if _cls in _hourly_done:
                continue  # ERCOT-96: already applied at the finer hour grain
            _idx = np.array(
                [
                    gi
                    for gi, g in enumerate(generators)
                    if artifact_class(g.plant_group) == _cls
                ],
                dtype=int,
            )
            if _idx.size == 0:
                continue
            _cap = pmax[_idx]  # (n,)
            _cap_sum = float(_cap.sum())
            if _cap_sum <= 0.0:
                continue
            _a = availability[_idx, : _n_days * 24].reshape(_idx.size, _n_days, 24)
            _ad = _a.mean(axis=2)  # (n, days) per-unit day-mean availability
            _t = _target_h[: _n_days * 24].reshape(_n_days, 24).mean(axis=1)  # (days,)
            _covered = np.isfinite(_t)
            if not _covered.any():
                continue
            # Cap-weighted current class-day mean availability.
            _cur = (_ad * _cap[:, None]).sum(axis=0) / _cap_sum  # (days,)
            # BIDIRECTIONAL WATER-FILL to the DAM-measured class-day level — the
            # measured-availability backcast re-architecture (2026-07-18). The
            # DAM class-day availability is the AUTHORITY here (it REPLACES the
            # statistical WEFOR — the pre-overlay availability only supplies the
            # within-class shape and the uncovered-day fallback):
            #   * RESTORE (target >= cur): raise each unit toward its ceiling
            #     (1.0) proportionally to its headroom, a' = a + λ(1 − a) with
            #     λ = (target − cur)/(1 − cur). This REVIVES phantom-derated
            #     units the old multiplicative rescale could not (0 × r stays 0),
            #     which was the ercot82 April-CC over-removal defect: a class-day
            #     mean rescale cannot lift a unit the CAMPD full-stop override
            #     zeroed when the rest of the class has no 1.0-headroom.
            #   * REMOVE (target < cur): scale each unit toward 0, a' = a·
            #     (target/cur) — the class carries MORE measured outage than the
            #     CAMPD windows found (the summer under-removal case).
            # Both hit the cap-weighted class-day mean exactly. The ceiling is a
            # flat 1.0 because the measured target already embeds every real
            # (incl. residual) outage; wefor_residual governs the uncovered-day
            # fallback, not this covered level.
            _new = _ad.copy()
            _restore = _covered & (_t >= _cur)
            _remove = _covered & (_t < _cur)
            # Per-unit forced-derate ceiling (ERCOT-137; 1.0 everywhere no
            # BIN_FORCED_DERATE_BY_YEAR entry exists → bit-identical).
            _ceil = _dam_ceil[_idx]
            _ceil_mean = float((_ceil * _cap).sum()) / _cap_sum
            _lam = np.clip((_t - _cur) / np.maximum(_ceil_mean - _cur, 1e-9), 0.0, 1.0)
            _new[:, _restore] = _ad[:, _restore] + _lam[None, _restore] * np.maximum(
                _ceil[:, None] - _ad[:, _restore], 0.0
            )
            _mu = np.where(_remove, _t / np.maximum(_cur, 1e-9), 1.0)
            _new[:, _remove] = _ad[:, _remove] * _mu[None, _remove]
            # Broadcast the new day-mean over the 24 hourly slots, preserving each
            # unit's intra-day shape by the per-unit day ratio (new/old); a unit
            # revived from a zeroed day has no shape to scale, so it is set flat.
            _ratio = np.divide(
                _new, _ad, out=np.zeros_like(_ad), where=_ad > 1e-9
            )  # (n, days); 0 where the pre-overlay day was zeroed (revived below)
            _scaled = _a * _ratio[:, :, None]
            _flat = (_ad <= 1e-9) & (_new > 1e-9)  # revived-from-zero (n, days)
            if _flat.any():
                _scaled[_flat, :] = _new[_flat][:, None]
            _scaled = np.minimum(_scaled, _ceil[:, None, None])
            _scaled[:, ~_covered, :] = _a[:, ~_covered, :]  # uncovered untouched
            availability[_idx, : _n_days * 24] = _scaled.reshape(_idx.size, -1)
            logger.info(
                "ERCOT measured thermal DAM availability (%d): %s set to measured "
                "class-day level on %d day(s) (restore %d / remove %d), median "
                "target %.3f",
                _yr,
                _cls,
                int(_covered.sum()),
                int(_restore.sum()),
                int(_remove.sum()),
                float(np.median(_t[_covered])),
            )
        np.clip(availability, 0.0, 1.0, out=availability)

        # ERCOT-148 measured-event precedence cap
        # (config.ercot_dam_availability_coal_event_cap, default off): the
        # measured CAMPD event-window family is a hard availability CAP the
        # DAM COP restore cannot exceed on the COAL fleet. The plant-grain pin
        # above is BIDIRECTIONAL by design (it replaces the statistical stack),
        # but during a >= 5-day CAMPD full stop the two measured instruments
        # conflict: the frozen window identification (outage_detect
        # FULL_STOP_OVERRIDE — a weeks-long CF~0 dead stop of baseload coal is
        # the mechanical-outage signature) says the unit is OUT while the COP
        # files it OFF-at-full-HSL ("startable"), and the water-fill restores
        # the windowed-out capacity (Coleto Creek dispatched at nameplate
        # through its 2023 mothball block; Limestone at 1,653 MW plant peak
        # through LIM1's Feb-2023 dead stop — 4.36/4.98/5.01 TWh of coal
        # dispatch above the measured-window ceiling on the ercot145 keeper).
        # Rule 14: on conflict the physical CEMS record outranks the QSE's
        # paper declaration (misalignment documented on the ScenarioConfig
        # field). Rule 19: min() over the two incumbent layers — no new
        # mechanism, and the DAM overlay keeps its designed job everywhere
        # else (the remove direction and all non-window hours are untouched;
        # the window factors are 1.0 there). Gated additionally on the historic
        # overlay so the cap only reconciles layers actually applied. The cap
        # mirrors the apply block above: >= 5-day unit windows + the ERCOT
        # plant-grain partial plateaus always; short / unit-grain-partial
        # layers only when their gates armed them into availability.
        #
        # ERCOT-149 gas widening (config.ercot_dam_availability_gas_event_cap,
        # default off): the SAME precedence rule extended to the DAM-covered
        # gas classes — one mechanism, one min() block, its class scope
        # widened (rule 19: never a second cap layer). The gas windows are
        # event-based dead spans (every hour < 2% CF) that survived the armed
        # merit-order guard, and the Phase 0/1 audit measured 4.27/5.93/4.14
        # TWh (2023/24/25) of CC_REGULAR + ST_GAS dispatch above the windowed
        # ceiling, carried by the pin's own site-series misalignments
        # (config-collapse train-aliasing, partial site acceptance) plus true
        # OFF-at-HSL filings through certified dead stops — see the
        # ScenarioConfig field comment and
        # docs/DIAGNOSIS-ercot149-gas-cop-window-2026-08-01.md. CT_PEAKER is
        # in scope on principle and provably inert (peakers carry no windows
        # by the detector's design). Coal-only arms stay byte-identical: for
        # a coal generator the (plant_code, artifact_class(plant_group)) layer
        # key below is exactly the former (plant_code, "COAL") literal — the
        # artifact family token, while the unit carries its subclass (COAL-SUB).
        _evcap_scope: set[str] = set()
        if getattr(config, "ercot_dam_availability_coal_event_cap", False):
            _evcap_scope.update(COAL_CLASSES)
        if getattr(config, "ercot_dam_availability_gas_event_cap", False):
            _evcap_scope.update(("CC_REGULAR", "ST_GAS", "CT_PEAKER"))
        if (
            _evcap_scope
            and getattr(config, "outage_source", "statistical") == "historic"
        ):
            _bins_path = getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV))
            _cap_layers: list[dict] = [
                unit_outage_derate_factors(int(_yr), hours, _bins_path, iso="ERCOT"),
            ]
            if getattr(config, "unit_outage_short_windows", False):
                _cap_layers.append(
                    unit_outage_short_derate_factors(
                        int(_yr),
                        hours,
                        _bins_path,
                        iso="ERCOT",
                        gas_scope=getattr(
                            config, "unit_outage_short_windows_gas", False
                        ),
                    )
                )
            if getattr(config, "unit_partial_outage_windows", False):
                _cap_layers.append(
                    unit_partial_outage_derate_factors(
                        int(_yr), hours, _bins_path, iso="ERCOT"
                    )
                )
            # ercot-173 C1+C2 ceiling reconciliation (default off): the
            # ceiling's own layers all derive from the same CEMS record and
            # each estimates "how much of this plant is unavailable", so
            # multiplying them removes the same downtime twice — the rule-19
            # double-count ercot-172 measured at the two 2024 shed hours
            # (W A Parish 0.6995 x 0.3630 = 0.2539 vs its own-hour CEMS
            # 0.7843). Under the gate the layers compose by min() — the
            # deepest single measured resolution wins, the same way the
            # finished ceiling already composes with the COP layer below —
            # and the plant-grain partial plateau keys by the extract's own
            # (plant_code, plant_group) (C1; inert on the current bins
            # sheet). Off: the incumbent product, byte-identical.
            #
            # ercot-174 UNIT-SCOPED composition (default off, and the SUCCESSOR
            # the ercot-173 rejection named — it takes precedence when both
            # gates are set). ercot-173 measured the blanket min() in both
            # directions: right at the ercot-172 shed hours, wrong fleet-wide
            # (+0.98/+1.95/+2.73 TWh/yr of coal re-admitted above the product
            # ceiling, G-COAL148 FAIL), because the window and partial layers
            # measure the SAME units' downtime at some overlaps and DIFFERENT
            # units' at most others. So neither composition is right
            # fleet-wide, and the choice is made PER HOUR from the two layers'
            # measured CAMPD unit sets: min() where they INTERSECT (the
            # double-count is real there), the incumbent PRODUCT where they are
            # disjoint (each layer removes its own units). Pointwise
            # product <= this <= min(), so the arm can only RESTORE capability
            # and every movement is bounded by the ercot-173 record; an
            # unattributed plateau leaves the unit set empty and keeps the
            # product (fail-safe). The window-family layers keep their
            # incumbent product composition among themselves — only the
            # window-vs-partial seam is refined.
            _unit_scoped = getattr(
                config, "ercot_dam_availability_event_cap_unit_scoped", False
            )
            _reconc = (
                getattr(
                    config, "ercot_dam_availability_event_cap_reconciliation", False
                )
                and not _unit_scoped
            )
            _plant_partial = partial_outage_derate_factors(
                int(_yr),
                hours,
                class_grain=_reconc or _unit_scoped,
                # ercot-185: the same repaired layer this block's sibling
                # consumer reads (arrays.py ~1333) — one construction, one
                # layer, both seams.
                shaped=getattr(config, "ercot_partial_outage_shaped_derate", False),
                day_guard=getattr(config, "ercot_partial_outage_day_guard", False),
            )
            _w_units = (
                unit_outage_active_units(int(_yr), hours, iso="ERCOT")
                if _unit_scoped
                else {}
            )
            _p_units = (
                partial_outage_active_units(int(_yr), hours, iso="ERCOT")
                if _unit_scoped
                else {}
            )
            _n_capped = 0
            _n_shared_bins = 0
            _n_shared_hours = 0
            for g_idx, gen in enumerate(generators):
                if gen.plant_group not in _evcap_scope:
                    continue
                _ceil_w: np.ndarray | None = None
                for _layer in _cap_layers:
                    _f = _layer.get(
                        (int(gen.plant_code), artifact_class(gen.plant_group))
                    )
                    if _f is not None:
                        if _ceil_w is None:
                            _ceil_w = np.array(_f, dtype=float, copy=True)
                        elif _reconc:
                            _ceil_w = np.minimum(_ceil_w, _f)
                        else:
                            _ceil_w = _ceil_w * _f
                _binkey = (int(gen.plant_code), artifact_class(gen.plant_group))
                _ppkey = _binkey if (_reconc or _unit_scoped) else int(gen.plant_code)
                _fp = _plant_partial.get(_ppkey)
                if _fp is not None:
                    if _ceil_w is None:
                        _ceil_w = np.array(_fp, dtype=float, copy=True)
                    elif _unit_scoped:
                        _shared = shared_unit_hours(
                            _w_units.get(_binkey), _p_units.get(_binkey), hours
                        )
                        _ceil_w = np.where(
                            _shared[: _ceil_w.size],
                            np.minimum(_ceil_w, _fp),
                            _ceil_w * _fp,
                        )
                        if _shared.any():
                            _n_shared_bins += 1
                            _n_shared_hours += int(_shared.sum())
                    elif _reconc:
                        _ceil_w = np.minimum(_ceil_w, _fp)
                    else:
                        _ceil_w = _ceil_w * _fp
                if _ceil_w is None:
                    continue
                np.minimum(
                    availability[g_idx, :hours],
                    _ceil_w[:hours],
                    out=availability[g_idx, :hours],
                )
                _n_capped += 1
            logger.info(
                "ERCOT measured-event precedence cap (%d): %d %s tranche(s) "
                "capped at the CAMPD event-window ceiling (DAM COP restore "
                "bounded by measured full-stop/partial windows)",
                int(_yr),
                _n_capped,
                "/".join(sorted(_evcap_scope)),
            )
            if _unit_scoped:
                logger.info(
                    "ERCOT unit-scoped event-cap composition (%d): min() on "
                    "%d bin(s) / %d bin-hour(s) where the window and partial "
                    "layers share a CAMPD unit; product elsewhere",
                    int(_yr),
                    _n_shared_bins,
                    _n_shared_hours,
                )

    # NEISO measured FLEET operable-capacity availability (backcast overlay,
    # config.neiso_operable_capacity_availability): the ISO-NE analogue of the
    # ERCOT class-day DAM block above. ISO-NE publishes availability only at
    # FLEET grain (Morning Report Section 3; no per-unit / per-fuel series), so a
    # SINGLE measured day availability fraction is imposed on the covered
    # dispatchable-thermal classes TOGETHER: set their cap-weighted day-mean
    # availability to the measured 1 - outages/(CSO + EcoMax-above-CSO) level,
    # superseding the CAMPD unit-outage derate applied above ("instead of the
    # campd unit outage fallback"). Same bidirectional cap-1.0 water-fill as the
    # ERCOT block (RESTORE toward the ceiling where measured > model, REMOVE
    # toward zero where measured < model), here over one pooled group. Uncovered
    # dates (pre-2018-07 archive start, publication gaps) keep the pre-overlay
    # availability; forecast mode is untouched (the mode-aware seam). Provenance
    # + admissibility: data.neiso_operable_capacity.
    if (
        config is not None
        and _iso == "NEISO"
        and getattr(config, "neiso_operable_capacity_availability", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        from market_sim.data.neiso_operable_capacity import (
            neiso_thermal_availability_series,
        )

        _meas = neiso_thermal_availability_series(int(_yr), hours)
        _idx = np.array(
            [
                gi
                for gi, g in enumerate(generators)
                if g.plant_group in THERMAL_AVAILABILITY
            ],
            dtype=int,
        )
        _n_days = hours // 24
        _t = (
            _meas[: _n_days * 24].reshape(_n_days, 24).mean(axis=1)
            if _idx.size
            else np.array([])
        )
        _covered = np.isfinite(_t)
        _cap = pmax[_idx] if _idx.size else np.array([])
        _cap_sum = float(_cap.sum()) if _idx.size else 0.0
        if _idx.size and _cap_sum > 0.0 and _covered.any():
            _a = availability[_idx, : _n_days * 24].reshape(_idx.size, _n_days, 24)
            _ad = _a.mean(axis=2)  # (n, days) per-unit day-mean availability
            # Cap-weighted current pooled-thermal day-mean availability.
            _cur = (_ad * _cap[:, None]).sum(axis=0) / _cap_sum  # (days,)
            _restore = _covered & (_t >= _cur)
            _remove = _covered & (_t < _cur)
            _lam = np.clip((_t - _cur) / np.maximum(1.0 - _cur, 1e-9), 0.0, 1.0)
            _new = _ad.copy()
            _new[:, _restore] = _ad[:, _restore] + _lam[None, _restore] * (
                1.0 - _ad[:, _restore]
            )
            _mu = np.where(_remove, _t / np.maximum(_cur, 1e-9), 1.0)
            _new[:, _remove] = _ad[:, _remove] * _mu[None, _remove]
            # Preserve each unit's intra-day shape by the per-unit day ratio; a
            # unit revived from a zeroed day is set flat (no shape to scale).
            _ratio = np.divide(_new, _ad, out=np.zeros_like(_ad), where=_ad > 1e-9)
            _scaled = _a * _ratio[:, :, None]
            _flat = (_ad <= 1e-9) & (_new > 1e-9)
            if _flat.any():
                _scaled[_flat, :] = _new[_flat][:, None]
            _scaled = np.minimum(_scaled, 1.0)
            _scaled[:, ~_covered, :] = _a[:, ~_covered, :]  # uncovered untouched
            availability[_idx, : _n_days * 24] = _scaled.reshape(_idx.size, -1)
            np.clip(availability, 0.0, 1.0, out=availability)
            logger.info(
                "NEISO measured operable-capacity availability (%d): pooled "
                "thermal fleet set to measured fleet level on %d day(s) "
                "(restore %d / remove %d), median target %.3f",
                _yr,
                int(_covered.sum()),
                int(_restore.sum()),
                int(_remove.sum()),
                float(np.median(_t[_covered])),
            )

    # PJM measured generation-outage availability (backcast overlay,
    # config.pjm_dam_availability): the PJM analogue of the ERCOT class-day DAM
    # block above. PJM publishes outages only at the RTO/sub-region aggregate
    # (never per fuel class), so pjm_dam_availability_series converts the measured
    # unplanned-outage MW to ONE fleet-wide availability fraction and returns it
    # for every covered fossil-thermal class — a UNIFORM derate. Each covered
    # class is water-filled to that same measured day-mean fraction by the SAME
    # bidirectional cap-1.0 rule as the ERCOT block (RESTORE toward the ceiling
    # where measured > model, REMOVE toward zero where measured < model),
    # superseding the CAMPD unit-outage derate on covered days ("in place of the
    # campd unit outage fallback"). Uncovered days (NaN — outside the feed) keep
    # the pre-overlay availability; forecast mode is untouched (the mode-aware
    # seam). Kept a SEPARATE block from ERCOT (rather than generalizing that
    # overlay's now ERCOT-96/97-branched guard) so the ERCOT path stays
    # byte-identical. Provenance + admissibility: data.pjm_outages.
    if (
        config is not None
        and _iso == "PJM"
        and getattr(config, "pjm_dam_availability", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        from market_sim.data.pjm_outages import pjm_dam_availability_series

        _meas_pjm = pjm_dam_availability_series(int(_yr), hours)
        _n_days = hours // 24
        for _cls, _target_h in _meas_pjm.items():
            _idx = np.array(
                [
                    gi
                    for gi, g in enumerate(generators)
                    if artifact_class(g.plant_group) == _cls
                ],
                dtype=int,
            )
            if _idx.size == 0:
                continue
            _cap = pmax[_idx]  # (n,)
            _cap_sum = float(_cap.sum())
            if _cap_sum <= 0.0:
                continue
            _a = availability[_idx, : _n_days * 24].reshape(_idx.size, _n_days, 24)
            _ad = _a.mean(axis=2)  # (n, days) per-unit day-mean availability
            _t = _target_h[: _n_days * 24].reshape(_n_days, 24).mean(axis=1)  # (days,)
            _covered = np.isfinite(_t)
            if not _covered.any():
                continue
            # Cap-weighted current class-day mean availability.
            _cur = (_ad * _cap[:, None]).sum(axis=0) / _cap_sum  # (days,)
            _restore = _covered & (_t >= _cur)
            _remove = _covered & (_t < _cur)
            _lam = np.clip((_t - _cur) / np.maximum(1.0 - _cur, 1e-9), 0.0, 1.0)
            _new = _ad.copy()
            _new[:, _restore] = _ad[:, _restore] + _lam[None, _restore] * (
                1.0 - _ad[:, _restore]
            )
            _mu = np.where(_remove, _t / np.maximum(_cur, 1e-9), 1.0)
            _new[:, _remove] = _ad[:, _remove] * _mu[None, _remove]
            # Preserve each unit's intra-day shape by the per-unit day ratio; a
            # unit revived from a zeroed day is set flat (no shape to scale).
            _ratio = np.divide(_new, _ad, out=np.zeros_like(_ad), where=_ad > 1e-9)
            _scaled = _a * _ratio[:, :, None]
            _flat = (_ad <= 1e-9) & (_new > 1e-9)
            if _flat.any():
                _scaled[_flat, :] = _new[_flat][:, None]
            _scaled = np.minimum(_scaled, 1.0)
            _scaled[:, ~_covered, :] = _a[:, ~_covered, :]  # uncovered untouched
            availability[_idx, : _n_days * 24] = _scaled.reshape(_idx.size, -1)
            logger.info(
                "PJM measured generation-outage availability (%d): %s set to "
                "measured fleet level on %d day(s) (restore %d / remove %d), "
                "median target %.3f",
                _yr,
                _cls,
                int(_covered.sum()),
                int(_restore.sum()),
                int(_remove.sum()),
                float(np.median(_t[_covered])),
            )
        np.clip(availability, 0.0, 1.0, out=availability)

    # PJM measured-outage EVENT CAP (config.pjm_measured_outage_event_cap,
    # backcast overlay, pjm-161). The ERCOT-148/149 event-cap shape: the
    # incumbent CAMPD unit-grain envelope keeps sole ownership of WHICH units
    # are out, and this only DEEPENS a class-day toward PJM's own published
    # outage total where that total is deeper. Composition is min() on
    # availability — the more-derated of two measured layers wins, because the
    # CAMPD detector infers unavailability from zero generation and so cannot
    # see an outage at a unit that would not have run anyway (a LOWER BOUND by
    # construction, whose error is largest in scarcity: measured corr(derated
    # MW, net load) = -0.68..-0.77 for PJM 2022-2025).
    #
    # Two deltas from the pjm_dam_availability block above, and they are what
    # make this a different mechanism rather than a grain switch (rule 19 keeps
    # them mutually exclusive; ScenarioConfig.__post_init__ refuses both):
    #   * TOTAL outage types (forced + maintenance + planned) — the incumbent
    #     envelope includes planned outages, so the comparison must too;
    #   * REMOVE-ONLY — no restore leg at all, so a unit the finer measured
    #     record holds at zero can never be revived (ad == 0 => new == 0, the
    #     `_flat` branch is unreachable).
    if (
        config is not None
        and _iso == "PJM"
        and getattr(config, "pjm_measured_outage_event_cap", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        from market_sim.data.pjm_outages import (
            PJM_OUTAGE_ALL_TYPES,
            PJM_OUTAGE_COVERED_GROUPS,
            pjm_outage_mw_series,
        )

        # FLEET grain, not class grain, and the ex-ante measurement is why
        # (results/calibration/_pjm161_removeonly_exante.json). PJM publishes
        # ONE fleet number; `pjm_dam_availability_series` spreads it into a
        # single availability FRACTION handed to every covered class, which as
        # a remove-only cap degenerates into "every class ceilinged at the
        # fleet mean" — it bound on 282-305 of 364 days and removed 4.8-6.3 GW
        # year-mean, a level bulldozer rather than an event cap, and it would
        # have flattened the real availability differences BETWEEN classes.
        # Comparing the published FLEET outage MW against the model's own
        # FLEET outage MW instead preserves every class's relative
        # availability and fires only when the operator's record says the
        # fleet is more derated than the model believes.
        _n_days = hours // 24
        _pub_h = pjm_outage_mw_series(
            int(_yr), hours, outage_types=PJM_OUTAGE_ALL_TYPES
        )
        _pub = _pub_h[: _n_days * 24].reshape(_n_days, 24).mean(axis=1)  # (days,)
        _cov = np.array(
            [
                artifact_class(g.plant_group) in PJM_OUTAGE_COVERED_GROUPS
                for g in generators
            ],
            dtype=bool,
        )
        if _cov.any() and np.isfinite(_pub).any():
            _idx = np.flatnonzero(_cov)
            _cap = pmax[_idx]
            _cap_sum = float(_cap.sum())
            _a = availability[_idx, : _n_days * 24].reshape(_idx.size, _n_days, 24)
            _ad = _a.mean(axis=2)  # (n, days)
            _avail_mw = (_ad * _cap[:, None]).sum(axis=0)  # (days,) available MW
            _cur_out = _cap_sum - _avail_mw  # (days,) the model's own outage MW
            _covered = np.isfinite(_pub)
            _bind = _covered & (_pub > _cur_out)  # REMOVE-ONLY: never restores
            # mu solves  cap_sum - mu * avail_mw = pub  =>  the fleet's outage MW
            # rises exactly to the published total, with every unit's relative
            # availability (and every zero) preserved.
            _mu = np.ones(_n_days)
            _mu[_bind] = np.clip(
                (_cap_sum - _pub[_bind]) / np.maximum(_avail_mw[_bind], 1e-9), 0.0, 1.0
            )
            if _bind.any():
                _scaled = _a * _mu[None, :, None]
                np.clip(_scaled, 0.0, 1.0, out=_scaled)
                availability[_idx, : _n_days * 24] = _scaled.reshape(_idx.size, -1)
            logger.info(
                "PJM measured-outage event cap (%d): fleet cap bound on %d of %d "
                "covered day(s); model outage %.0f -> %.0f MW day-mean "
                "(published %.0f), median bind ratio %.3f",
                _yr,
                int(_bind.sum()),
                int(_covered.sum()),
                float(_cur_out[_covered].mean()),
                float((_cap_sum - _mu * _avail_mw)[_covered].mean()),
                float(_pub[_covered].mean()),
                float(np.median(_mu[_bind])) if _bind.any() else 1.0,
            )
        np.clip(availability, 0.0, 1.0, out=availability)

    # ercot-219 stage-1 measured aggregate-capability reconciliation (B-1
    # SIGNED by dispatch of ERCOT-219 2026-08-18; PRECOMMIT-ercot219 §1.1).
    # A single hourly TIGHTEN-ONLY scalar on merchant-thermal availability so
    # the model's aggregate online dispatchable capability matches the
    # published NP6-905 telemetered aggregate (quantity columns only). Applied
    # LAST among the level-changing overlays — after the CAMPD windows, the
    # DAM rescale and the event caps, and before ``_compose_min_gen_floors``
    # clamps every floor to ``pmax × availability`` — so the LP stays feasible
    # by construction and the rule-19 ownership split holds: the DAM family
    # keeps class/plant-grain declared availability (shape/allocation), this
    # overlay owns the aggregate real-time online LEVEL, tighten-only
    # (s ≤ 1 never loosens the DAM rescale and never resurrects an outaged
    # unit — a zeroed row stays zero under multiplication). CHP classes are
    # excluded from BOTH sides of the comparison: the measured 2023 closure
    # (ercot219_basis_phase0.json) shows T_tel tracking the SCED-corpus
    # all-thermal online truth at corr 0.9957 with a stable −4.05 GW
    # population-boundary offset — the cogen/PUN boundary, which the model's
    # CHP classes represent on their own measured basis (rule 14
    # documented-misalignment clause). Nuclear/hydro rows enter the
    # complement N(t) at their own measured availability and are never scaled.
    if (
        config is not None
        and _iso == "ERCOT"
        and getattr(config, "ercot_capability_reconciliation", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        from market_sim.data.outages import ercot_capability_reconciliation_target

        _t_tel = ercot_capability_reconciliation_target(int(_yr), hours)
        _grp = np.array([str(g.plant_group) for g in generators])
        _fuel = np.array([str(g.fuel_type) for g in generators])
        _chp = np.char.find(_grp, "CHP") >= 0
        _complement = np.isin(_fuel, ("nuclear", "hydro"))
        _merch = ~_chp & ~_complement
        # t = hour: N/M are (hours,) capability aggregates over the two
        # populations at the CURRENT (post-overlay) availability state.
        _n_t = (pmax[_complement, None] * availability[_complement, :]).sum(axis=0)
        _m_t = (pmax[_merch, None] * availability[_merch, :]).sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            _s = (_t_tel - _n_t) / np.maximum(_m_t, 1e-9)
        # PRECOMMIT-ercot219 Amendment 1 (pre-solve): the degenerate branch
        # s <= 0 — "zero merchant thermal online" — is physically impossible
        # (a statewide blackout) and is measured to occur ONLY on isolated
        # single-hour telemetry spikes in the netting series (2023 h2461 wind
        # HSL 15.2->32.0->25.0 GW; 2024 h7345 wind 33.2->43.3->22.0 GW, above
        # the year's installed wind). Such hours are series artifacts, treated
        # reconciliation-inert (s = 1) exactly like a NaN hour — counted and
        # reported, never fabricated into a shortage. Parameter-free: the
        # bound is the mechanism's own degenerate point, unreachable by any
        # real scarcity hour (T_tel p1 = 16.1 GW against N ~ 5 GW).
        _inert = ~np.isfinite(_t_tel) | (_t_tel <= _n_t)
        _s = np.clip(_s, 0.0, 1.0)
        _s[_inert] = 1.0
        availability[_merch, :] *= _s[None, :]
        np.clip(availability, 0.0, 1.0, out=availability)
        logger.info(
            "ERCOT aggregate-capability reconciliation (B-1, %d): scalar mean "
            "%.3f / min %.3f, tightened %d of %d telemetered hours (%d "
            "inert-NaN), merchant fleet %.1f GW over %d rows",
            int(_yr),
            float(_s[~_inert].mean()) if (~_inert).any() else 1.0,
            float(_s[~_inert].min()) if (~_inert).any() else 1.0,
            int((_s < 1.0).sum()),
            int((~_inert).sum()),
            int(_inert.sum()),
            float(pmax[_merch].sum()) / 1e3,
            int(_merch.sum()),
        )

    # Reallocate each CC_REGULAR plant's outage derate from pro-rata to
    # top-of-stack (config.cc_outage_derate_from_top): the plant's hourly
    # available MW is unchanged, but it now fills the tranches bottom-up in
    # heat-rate order, so a partial outage truncates the expensive duct-fire /
    # high-econ end of the offer curve while the cheap committed floor keeps
    # its level — matching how a multi-train CC sheds its least-efficient
    # increments first and runs the surviving train near full load.
    if config is not None and getattr(config, "cc_outage_derate_from_top", False):
        cc_by_plant: dict[int, list[int]] = {}
        for g_idx, gen in enumerate(generators):
            if gen.plant_group == "CC_REGULAR" and int(gen.plant_code) > 0:
                cc_by_plant.setdefault(int(gen.plant_code), []).append(g_idx)
        realloc_plants = 0
        for idxs in cc_by_plant.values():
            if len(idxs) < 2:
                continue  # single-tranche plant: nothing to reallocate
            # Merit order within the plant: tranches share one fuel price, so
            # heat rate ranks them (committed < econ slices < peak).
            order = sorted(idxs, key=lambda i: heat_rate[i])
            caps = pmax[order]  # (n_tranches,)
            avail_mw = availability[order, :].T @ caps  # (T,) plant total
            cum_below = np.concatenate(([0.0], np.cumsum(caps[:-1])))
            bounds = np.clip(
                avail_mw[np.newaxis, :] - cum_below[:, np.newaxis],
                0.0,
                caps[:, np.newaxis],
            )
            availability[order, :] = bounds / caps[:, np.newaxis]
            realloc_plants += 1
        if realloc_plants:
            logger.info(
                "CC_REGULAR outage derate reallocated top-of-stack for %d plant(s)",
                realloc_plants,
            )


def _commitment_day_order(sys_load: np.ndarray | None, hours: int) -> np.ndarray | None:
    """Operating days ranked by that day's MEAN system load, highest first.

    The whole-operating-day analogue of the hour ranking the per-plant
    must-run seams place their window with
    (``config.mustrun_window_commitment_grain``, spp-27): the same signal and
    the same ordering statistic, aggregated to the period a unit commitment is
    actually made for. Returns ``None`` when there is no usable load shape, so
    the caller falls back to the hour grain.

    Args:
        sys_load: Hourly system load, or ``None``.
        hours: The solve year's hour count.

    Returns:
        ``(n_days,)`` day indices in descending day-mean-load order, or
        ``None``.
    """
    if sys_load is None or hours < 24:
        return None
    days = hours // 24
    if days <= 0:
        return None
    key = np.asarray(sys_load, dtype=float)[: days * 24].reshape(days, 24).mean(axis=1)
    return np.argsort(-key, kind="stable")


def _mustrun_window_hours(
    load_rank: np.ndarray,
    day_order: np.ndarray | None,
    k: int,
    day_grain: bool,
) -> np.ndarray:
    """The k-hour committed window a per-plant must-run floor is placed in.

    Hour grain (the default) is the top-``k`` hours by system load. Under
    ``config.mustrun_window_commitment_grain`` the window is instead
    ``round(k / 24)`` whole operating days off *day_order*, so the floor
    carries the diurnal shape of a COMMITMENT (flat across the committed day)
    rather than the diurnal shape of LOAD. Size, level and membership are
    unchanged — only which hours are selected (rule 19 [R-ONE-MECH]).

    Args:
        load_rank: Hour indices in descending system-load order.
        day_order: Day indices from :func:`_commitment_day_order`, or ``None``.
        k: The window size in hours (``online_frac`` x hours).
        day_grain: Whether the commitment-grain gate is armed.

    Returns:
        The window's hour indices (unsorted).
    """
    if not day_grain or day_order is None or len(day_order) == 0:
        return load_rank[:k]
    n_days = int(min(len(day_order), max(1, round(k / 24.0))))
    starts = np.asarray(day_order[:n_days], dtype=int) * 24
    return (starts[:, None] + np.arange(24)[None, :]).ravel()


def _compose_min_gen_floors(
    generators: list[Generator],
    availability: np.ndarray,
    pmax: np.ndarray,
    pmin: np.ndarray,
    heat_rate: np.ndarray,
    hours: int,
    config: ScenarioConfig | None,
    _iso: str | None,
    _yr: int | None,
    load_shape: np.ndarray | None,
    ct_campd_shape: dict[int, np.ndarray] | None,
    ct_floor_mwh: dict[int, np.ndarray],
    ct_floor_frac: float,
    ct_floor_plants: set[int],
    ct_deploy_floor: dict[int, np.ndarray],
    ct_deploy_frac: float,
    ct_deploy_plants: set[int],
    rd_deploy_floor: dict[int, np.ndarray],
    rd_deploy_frac: float,
    rd_deploy_plants: set[int],
    # TRAILING and DEFAULTED on purpose: this helper has positional callers
    # (tests/unit/data/test_mustrun_commitment_feasibility_clip.py passes all
    # 21 arguments by position). A new parameter inserted mid-signature
    # silently re-binds every argument after it, so the window series goes at
    # the end and ``None`` keeps the historical system-load behaviour.
    netload_shape: np.ndarray | None = None,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """Compose the hard minimum-generation floors (min_gen / mechanism ids).

    Nuclear flat must-run, CHP steam floors, coal synchronization,
    per-plant CC/ST_GAS committed floors, the ST_GAS p25 level swap,
    and the CT/reliability deployment overlays, clipped to available
    capacity. Pure array helper extracted verbatim from
    ``generators_to_fleet_arrays`` (fleet-package split sub-task (a)).

    ``load_shape`` and ``netload_shape`` are the two candidate WINDOW series:
    four of these floors shape themselves on one shared series, resolved once
    into ``_window_shape`` below and selected by
    ``config.commitment_floor_window_netload`` (default off -> ``load_shape``,
    i.e. the historical behaviour). ``netload_shape`` may be ``None`` or the
    wrong length, in which case the resolver falls back to ``load_shape`` so a
    plumbing gap can never silently drop a floor.

    Returns:
        ``(min_gen, min_gen_mechanism)`` — both ``None`` when no floor
        mechanism is active for this fleet.
    """
    n_gen = len(generators)
    # Hard minimum-generation bounds composed below: CHP grid-steam floors,
    # coal synchronization Pmin, nuclear flat must-run, and the per-plant
    # CT/reliability deployment overlays. Temperature-driven ST_GAS commitment is
    # now handled by the generic reliability-floor engine
    # (transmission.inject_reliability_floor), not a calendar-month seasonal floor.
    min_gen = None
    min_gen_mech = None
    chp_pmin_any = any(getattr(g, "chp_grid_pmin_mw", 0.0) > 0.0 for g in generators)
    coal_sync_any = any(getattr(g, "coal_sync_pmin_mw", 0.0) > 0.0 for g in generators)
    coal_min_config_any = any(
        getattr(g, "coal_min_config_pmin_mw", 0.0) > 0.0 for g in generators
    )
    cc_mustrun_any = any(
        getattr(g, "cc_mustrun_pmin_mw", 0.0) > 0.0 for g in generators
    )
    # Hydro min-flow floor: presence is read off the units themselves (the
    # config gate was already applied when data.hydro.build_hydro_fleet stamped
    # them), so an unfloored fleet is byte-identical to before.
    hydro_min_flow_any = any(
        getattr(g, "hydro_min_flow_monthly_mw", None) for g in generators
    )
    # Hydro RoR flat dispatch (caiso-126): same stamped-attribute pattern. The
    # availability cap was already applied in generators_to_fleet_arrays; the
    # floor half here fixes dispatch at the flat level (min == max).
    hydro_ror_any = any(
        getattr(g, "hydro_ror_flat_monthly_mw", None) for g in generators
    )
    # ST_GAS p25-level floor (config.st_gas_mustrun_p25_level, the miso-67
    # LEVEL SWAP for st_gas_mustrun_per_plant): gather the gate-armed ST_GAS
    # plants with their measured p25 level (p25_cf x nameplate) and measured
    # online window here, so (a) the min_gen allocation guard below includes
    # them and (b) the cc_mustrun block hands ST_GAS off to the dedicated p25
    # block (rule 19 — the level source is REPLACED, no second floor). Gated on
    # BOTH flags: st_gas_mustrun_per_plant arms the phenomenon, p25_level swaps
    # the level. Off => empty dicts => byte-identical to today.
    # MEMBERSHIP correction for BOTH per-plant must-run floors below
    # (config.mustrun_plant_exclusions, miso-170): the plants the mechanism-blind
    # CAMPD lay-up census says are mothballed — median gross load ZERO in every
    # (year, 4-hour block) cell — carry no measured operating floor at all. A
    # laid-up plant reads ~100 % available in the outage extract (lay-up is
    # correctly not booked as a forced outage), so without this the floor holds
    # a mothballed boiler at its historical operating level in the top
    # system-load hours it never ran in (rule 17 [R-FLOOR-WINDOW]). Same census
    # the NYISO commitment bridge reads — lay-up is a property of the SITE, so
    # one identification serves every mechanism that floors it (rule 19
    # [R-ONE-MECH]). Off => empty set => byte-identical to today, and the census
    # file is not even opened.
    mustrun_excluded: frozenset[int] = frozenset()
    if config is not None and getattr(config, "mustrun_plant_exclusions", False):
        # Local import: the census module is a leaf of data/, and importing it
        # at module scope would add a fleet -> data cycle (the same reason
        # pipeline/commitment.py imports it inside its own floor builder).
        from market_sim.data.bridge_layup_exclusions import load_layup_exclusions

        mustrun_excluded = load_layup_exclusions(_iso or "ERCOT")
        logger.info(
            "mustrun_plant_exclusions ARMED (%s): %d laid-up plant(s) carry no "
            "per-plant must-run floor (mechanism-blind CAMPD lay-up census)",
            _iso or "ERCOT",
            len(mustrun_excluded),
        )
    # PER-YEAR WINDOW VINTAGE for both per-plant must-run seams
    # (config.mustrun_online_frac_per_year, miso-172). The committed
    # thermal-tranche artifact publishes ONE ``online_frac`` per plant, measured
    # over the POOLED derive window, and the runtime applies it as a SINGLE
    # SOLVE YEAR's commitment window — so a plant whose synchronization share
    # moves across the window is committed at its multi-year average in every
    # year, over-committed in its light years and under-committed in its heavy
    # ones. MISO 1402 (Little Gypsy): pooled 0.508 vs per-year
    # 0.251 / 0.615 / 0.658, a ~2.3x 2023 over-commitment the C8 D-4 conduct
    # rider convicts (rule 17 [R-FLOOR-WINDOW]). The per-year artifact is the
    # SAME frozen estimator at the grain the floor is applied at (rule 23:
    # the pooled deriver is untouched and its file is not regenerated).
    #
    # BACKCAST ONLY (rule 13 [R-MEASURED]): the solve year's own meter has no
    # forward analogue, exactly like the CAMPD outage windows this sits beside.
    # A forecast year keeps the POOLED multi-year fraction — which is the same
    # estimator's own forward form, re-derived from the most recent history as
    # each year of CEMS lands — so the mechanism regenerates forward unchanged.
    #
    # MEMBERSHIP IS NOT TOUCHED, only the window: a plant qualifies on the
    # pooled artifact exactly as today, and the per-year value then sizes its
    # window. The one consequence that IS a membership change is deliberate and
    # measured: a per-year fraction of zero means the plant's own meter says it
    # never synchronized that year, so it carries no floor that year.
    _per_year_frac: dict[tuple[int, str], float] = {}
    if (
        config is not None
        and getattr(config, "mustrun_online_frac_per_year", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        _by_year = _pkg_ns().thermal_tranche_online_frac_by_year(_iso or "ERCOT")
        _per_year_frac = {
            (pc, grp): frac
            for (pc, grp, yr), frac in _by_year.items()
            if yr == int(_yr)
        }
        logger.info(
            "mustrun_online_frac_per_year ARMED (%s %s): %d per-year "
            "synchronization fraction(s) replace the pooled window vintage",
            _iso or "ERCOT",
            _yr,
            len(_per_year_frac),
        )
    # PER-YEAR WINDOW VINTAGE for the COAL SYNCHRONIZATION floor
    # (config.coal_sync_online_frac_per_year, pjm-h15). The same defect on a
    # separate seam: ``assembly.py`` stamps ``coal_sync_online_frac`` from the
    # SAME pooled ``online_frac`` column, and the coal block below applies it as
    # a single solve year's window. Its own gate, because coal is its own
    # mechanism id (``MECH_COAL_MUSTRUN``) carrying its own D-4 conduct
    # evidence — the gas gate above says so in terms (rule 19 [R-ONE-MECH]).
    #
    # BACKCAST ONLY (rule 13 [R-MEASURED]), like the gas sibling: a forecast
    # year keeps the pooled multi-year fraction, which is the estimator's own
    # forward form. MEMBERSHIP IS NOT TOUCHED — a plant reaches this block only
    # by carrying ``coal_sync_pmin_mw > 0``, decided in assembly from the
    # POOLED artifact exactly as today — and a plant with no own-year row keeps
    # its pooled fraction, so the arm can never remove a floor for want of a
    # measurement. The one deliberate consequence is the same as the gas
    # sibling's: an own-year fraction of zero means the plant's own meter says
    # it never synchronized that year, so it carries no floor that year.
    _coal_per_year_frac: dict[int, float] = {}
    if (
        config is not None
        and getattr(config, "coal_sync_online_frac_per_year", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        _coal_by_year = _pkg_ns().thermal_tranche_online_frac_by_year(_iso or "ERCOT")
        _coal_per_year_frac = {
            pc: frac
            for (pc, grp, yr), frac in _coal_by_year.items()
            if yr == int(_yr) and grp == COAL_ARTIFACT_FAMILY
        }
        logger.info(
            "coal_sync_online_frac_per_year ARMED (%s %s): %d per-year coal "
            "synchronization fraction(s) replace the pooled window vintage",
            _iso or "ERCOT",
            _yr,
            len(_coal_per_year_frac),
        )
    # WHOLE-OPERATING-DAY COMMITMENT GRAIN for both per-plant must-run seams
    # (config.mustrun_window_commitment_grain, spp-27). The floor asserts a
    # COMMITMENT — a day-ahead, whole-operating-day decision — but the engine
    # places it by ranking INDIVIDUAL HOURS by system load, so the floor
    # inherits the diurnal shape of LOAD instead of the shape of COMMITMENT.
    # Measured on SPP's ST_GAS fleet (spp-27 phase 0, 22 plants x 3 years,
    # CAMPD hourly): the peak-to-mean of each plant's ONLINE hour-of-day
    # profile is 1.007-1.146 on 21 of 22 plants — when these units are
    # synchronized they run through the overnight trough — while the incumbent
    # window's own peak-to-mean over the same plant-years is 1.03-2.86
    # (median ~1.35). Rule 17 [R-FLOOR-WINDOW] in both directions: the floor
    # binds at the daily peak and is absent overnight on the SAME committed
    # day. When armed the window becomes ``round(k/24)`` whole operating days
    # ranked by that day's MEAN system load — the mechanical lift of the
    # incumbent's own hourly ranking to the commitment period, same signal and
    # same ordering statistic, one grain coarser. Rule 21: zero free
    # parameters. Rule 13: the ranking is the model's own load, so it
    # regenerates forward and is mode-blind. Rule 19: the window is REPLACED,
    # never stacked; SIZE (``online_frac``, pooled or per-year), level and
    # membership are untouched, and the coal/CT seams keep the hour grain
    # (separate mechanism ids, whose conduct evidence this gate does not
    # carry). The COAL seam has since acquired its OWN gate on its own
    # evidence, ``config.coal_sync_window_commitment_grain`` (pjm-h16, the
    # block immediately below); this flag still does not reach it.
    _day_grain = bool(
        config is not None and getattr(config, "mustrun_window_commitment_grain", False)
    )
    # WHOLE-OPERATING-DAY COMMITMENT GRAIN for the COAL synchronization seam
    # (config.coal_sync_window_commitment_grain, pjm-h16). Its OWN gate, not a
    # widening of the gas gate above: the coal floor is a separate mechanism id
    # (``MECH_COAL_MUSTRUN``) with its own D-4 conduct evidence, the gas gate's
    # own comment says so in terms, and widening the shared field would move
    # SPP's designated keeper -- which arms it and has coal -- without SPP's
    # lane measuring anything (rules 25 [R-ISO-SCOPE] / 28(d)).
    # Measured on PJM's OWN coal meter (pjm-h16 phase 0, 152 reachable
    # plant-years): the peak-to-mean of each plant's ONLINE hour-of-day profile
    # is 1.0001-1.3097 (median 1.0091) and its overnight/afternoon on-share
    # ratio 0.788-1.027 (median 0.9968) -- a synchronized PJM coal unit runs
    # THROUGH the trough -- while the incumbent hour-ranked window's own
    # peak-to-mean is 1.0132-4.8608 and is MORE PEAKED THAN THE PLANT ON 152 OF
    # 152. Rule 18 [R-PHYSICS]: that window implies 3,963-5,517 starts a year
    # against the fleet's metered 238-334 (13.0x-18.3x; 253 implied on 1,299 MW
    # plant 6264 in 2024 against 4 measured), where the day grain implies
    # 403-473. Rule 19: the window is REPLACED, never stacked -- size, level,
    # membership and the pmax*availability clip are untouched, and a plant at
    # ``_COAL_SYNC_FORCE_ALL`` has no window to place and is unreachable by
    # construction.
    _coal_day_grain = bool(
        config is not None
        and getattr(config, "coal_sync_window_commitment_grain", False)
    )
    # MEASURED LAY-UP WINDOW MASK for both per-plant must-run seams
    # (config.mustrun_layup_window_mask, miso-173). The merit-order guard's
    # economic-lay-up companion extract records, per unit and dated window, the
    # >= 5-day full stops it removed from the availability envelope BECAUSE the
    # unit sat out of merit — i.e. the measured hours in which the plant's
    # self-commitment driver is absent. A must-run floor binding inside such a
    # window forces operation the model's own outage pipeline adjudicated as
    # not-operating (rule 17 [R-FLOOR-WINDOW]; MISO 1402's 2023 D-4 conduct
    # FAIL is the live case). When armed, each floored plant-hour's clip basis
    # becomes pmax x max(0, availability - layup_share) — availability itself
    # is NOT touched (an economically idle unit stays available to the LP's own
    # economics), only the forcing is confined to hours outside the plant's own
    # measured lay-up windows. BACKCAST ONLY (rule 13): same-year windows have
    # no forward analogue, exactly like the CAMPD outage overlay produced by
    # the same detector. Zero free parameters (rule 21): windows, shares and
    # the out-of-merit threshold live in the frozen derive layer (rule 23).
    _layup_removed: dict[tuple[int, str], np.ndarray] = {}
    if (
        config is not None
        and getattr(config, "mustrun_layup_window_mask", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        # Local import for the same fleet -> data cycle reason as the census
        # loader above.
        from market_sim.data.outages import unit_layup_removed_fractions

        _layup_removed = unit_layup_removed_fractions(
            int(getattr(config, "weather_year", 0) or _yr),
            hours,
            getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
            iso=_iso or "ERCOT",
            cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
            cc_nameplate_basis=getattr(config, "unit_outage_lp_capacity_basis", False),
            st_capacity_basis=getattr(config, "unit_outage_st_capacity_basis", False),
            per_unit_clip=getattr(config, "unit_outage_per_unit_clip", False),
            extract_basis_share=getattr(
                config, "unit_outage_extract_basis_share", False
            ),
            # miso-266: the dispatched bin's own capacity as the denominator.
            # It moves with the outage overlay by NECESSITY, not by choice —
            # unit_layup_removed_fractions' contract is that "a lay-up share and
            # an outage share for the same plant sit on the same basis and are
            # additive", and putting one on the dispatched denominator and the
            # other on the reconstructed one would break exactly that invariant
            # (rule 19 [R-ONE-MECH], the same reasoning st_capacity_basis and
            # per_unit_clip are threaded here under).
            lp_bin_capacity=(
                lp_bin_capacity_index(generators, pmax)
                if (
                    getattr(config, "unit_outage_dispatched_bin_denominator", False)
                    and (_iso or "ERCOT") != "ERCOT"
                )
                else None
            ),
        )
        logger.info(
            "mustrun_layup_window_mask ARMED (%s %s): %d plant-tranche lay-up "
            "share series mask the per-plant must-run floors",
            _iso or "ERCOT",
            _yr,
            len(_layup_removed),
        )
    st_gas_p25_tranches: dict[int, list[int]] = {}
    st_gas_p25_levels_by_plant: dict[int, float] = {}
    st_gas_p25_frac_by_plant: dict[int, float] = {}
    st_gas_p25_level_on = (
        config is not None
        and getattr(config, "st_gas_mustrun_p25_level", False)
        and getattr(config, "st_gas_mustrun_per_plant", False)
    )
    if st_gas_p25_level_on:
        from market_sim.data.fleet.campd_bins import campd_attribution_selectors

        _pu, _mg = campd_attribution_selectors(config)
        _p25_levels = _pkg_ns().thermal_tranche_p25_level(_iso or "ERCOT", _pu, _mg)
        _p25_fracs = _pkg_ns().thermal_tranche_online_frac(_iso or "ERCOT", _pu, _mg)
        # MEASURED-MW LEVEL BASIS (config.st_gas_mustrun_p25_measured_level,
        # miso-172). ``p25_cf`` is a percentile of net / (nameplate x
        # avail_mult), so the incumbent reconstruction ``p25_cf x nameplate``
        # drops the availability derate the statistic was divided by and
        # over-floors any plant with a deep one by 1 / avail_mult. MISO 1122
        # (Ames): 0.674 x 108.7 = 73.3 MW against a measured p25-of-online of
        # 33 MW (= 0.674 x its ~49 MW available base). The replacement level is
        # the SAME percentile of the SAME online sample taken directly in MW, so
        # there is no reconstruction to drop a basis (rule 14 [R-ACCURATE]).
        # The level source is REPLACED, never stacked (rule 19 [R-ONE-MECH]);
        # membership, window and mechanism id are untouched.
        _p25_measured: dict[tuple[int, str], float] = {}
        if getattr(config, "st_gas_mustrun_p25_measured_level", False):
            _p25_measured = _pkg_ns().thermal_tranche_p25_measured_level(
                _iso or "ERCOT"
            )
            logger.info(
                "st_gas_mustrun_p25_measured_level ARMED (%s): %d measured-MW "
                "level(s) replace the p25_cf x nameplate reconstruction",
                _iso or "ERCOT",
                len(_p25_measured),
            )
        # OUT-OF-MERIT CONDITIONING of the same level slot
        # (config.st_gas_mustrun_oom_level, miso-198). The measured-MW level
        # above is a low percentile of the plant's output over EVERY hour it
        # was online — its OPERATING RANGE. What the floor represents is
        # narrower: these VLR/self-committed steamers hold load in the hours
        # merit says shut down, so the statistic conditions the SAME frozen
        # percentile on the SAME pooled window over the miso-197 W3b
        # out-of-merit hour set (the measured CC_REGULAR fleet below 0.90 of
        # its own p99.5 — cheaper CC capability demonstrably idle).
        # Rule 19 [R-ONE-MECH]: the level SOURCE is REPLACED in the same slot,
        # never stacked; membership, window, mechanism id and the
        # cheapest-first pmax*availability clip are untouched. It wins over
        # st_gas_mustrun_p25_measured_level when both are on, because it is
        # that level re-conditioned rather than a second one.
        # Rule 21: zero free parameters — see the ScenarioConfig field.
        if getattr(config, "st_gas_mustrun_oom_level", False):
            _oom_level = _pkg_ns().thermal_tranche_oom_level(_iso or "ERCOT")
            if _oom_level:
                _p25_measured = {**_p25_measured, **_oom_level}
            logger.info(
                "st_gas_mustrun_oom_level ARMED (%s): %d out-of-merit "
                "level(s) re-condition the measured-MW level",
                _iso or "ERCOT",
                len(_oom_level),
            )
        for _g_idx, _gen in enumerate(generators):
            if getattr(_gen, "plant_group", "") != "ST_GAS":
                continue
            if int(_gen.plant_code or 0) in mustrun_excluded:
                continue  # economic lay-up (config.mustrun_plant_exclusions)
            _key = (int(_gen.plant_code), "ST_GAS")
            _level = _p25_levels.get(_key, 0.0)
            _frac = _p25_fracs.get(_key, 0.0)
            if _level <= 0.0 or _frac <= 0.0:
                continue
            # Membership decided on the pooled artifact above; only the LEVEL
            # basis and the WINDOW vintage are swapped below.
            _level = _p25_measured.get(_key, _level)
            _frac = _per_year_frac.get(_key, _frac)
            if _level <= 0.0 or _frac <= 0.0:
                continue  # measured dark all year / no measured level
            _pc = int(_gen.plant_code)
            st_gas_p25_tranches.setdefault(_pc, []).append(_g_idx)
            st_gas_p25_levels_by_plant[_pc] = _level
            st_gas_p25_frac_by_plant[_pc] = _frac
    # Nuclear runs flat as must-run baseload — it physically cannot load-follow
    # on price, so it must not back down to a part-load pmin in CAISO's many
    # negative/near-zero midday hours (the ~1 TWh Diablo Canyon under-run). Pin
    # it at its hourly availability cap (the refuel-schedule-driven monthly CF
    # already set in ``availability``), which is a forward-derivable physical
    # input, not a price/volume fit. Backcast only (forecast keeps the cap as a
    # planned-outage ceiling, not a floor).
    nuclear_flat = (
        config is not None
        and getattr(config, "mode", "forecast") == "backcast"
        and any(g.fuel_type == "nuclear" for g in generators)
    )
    if (
        chp_pmin_any
        or ct_floor_plants
        or ct_deploy_plants
        or rd_deploy_plants
        or nuclear_flat
        or coal_sync_any
        or coal_min_config_any
        or cc_mustrun_any
        or st_gas_p25_tranches
        or hydro_min_flow_any
        or hydro_ror_any
    ):
        min_gen = np.zeros((n_gen, hours), dtype=float)
        # Parallel mechanism-id array (D-2 forced-energy attribution): each
        # block below tags the unit-hours whose binding floor it supplied.
        min_gen_mech = np.zeros((n_gen, hours), dtype=np.int8)
        # min_gen replaces pmin as the LP lower bound for EVERY generator
        # (build_variable_bounds), so export sinks (pmin < 0, absorption
        # modeled as negative generation) must keep their range — a zero
        # floor would pin them off whenever any CHP/ST_GAS floor is active.
        neg_pmin = pmin < 0.0
        if neg_pmin.any():
            min_gen[neg_pmin, :] = pmin[neg_pmin, np.newaxis]
        if nuclear_flat:
            # Flat must-run: floor == availability cap, so nuclear holds its
            # available output through the solar-glut belly instead of cycling
            # to a 0.9*pmax part-load when the midday price falls below its VOM.
            for g_idx, gen in enumerate(generators):
                if gen.fuel_type == "nuclear":
                    min_gen[g_idx, :] = availability[g_idx, :] * pmax[g_idx]
                    min_gen_mech[g_idx, min_gen[g_idx, :] > 0.0] = MECH_NUCLEAR
        # THE SHARED COMMITMENT-FLOOR WINDOW SERIES, resolved ONCE
        # (config.commitment_floor_window_netload, SPP-66, owner ruling
        # "Shared gate" 2026-09-20; default off). FIVE floors below shape
        # themselves on this one series -- the CHP steam duty window
        # (caiso-293, immediately below), coal synchronization, the per-plant
        # CC/ST_GAS committed floor, the ST_GAS p25 level swap and the
        # CT_PEAKER reliability must-run. Four rank hours by it (top-k carries
        # the floor, plus _commitment_day_order's day grain); the CT floor
        # builds per-month max(load - median, 0) placement weights from it. It
        # is resolved here, once, so all five are windowed on the SAME driver
        # (rule 19 [R-ONE-MECH]) -- gating one floor while its neighbour kept
        # the other driver is the defect this replaced, not a narrower version
        # of the fix.
        #
        # OFF (the default) this is the IDENTICAL expression each of the four
        # PRE-EXISTING sites evaluated inline before, so every committed bundle
        # in every ISO is byte-identical. (caiso-293 moved this resolution
        # ABOVE the CHP steam block, which now reads it as the fifth consumer;
        # the move changes no value -- the series depends only on config,
        # netload_shape, load_shape and hours, none of which any floor writes.) ON, it swaps in net load, whose external driver
        # evidence is the ScenarioConfig field's own comment: a cycler runs in
        # the high-NET-load hours, not the high-gross-load ones (rule 17
        # [R-FLOOR-WINDOW] (a)). A None/short netload_shape falls through to
        # load_shape rather than dropping the window, so an armed run can never
        # silently lose its floors to a plumbing gap.
        _use_netload = (
            bool(getattr(config, "commitment_floor_window_netload", False))
            if config is not None
            else False
        )
        _window_src = (
            netload_shape
            if _use_netload
            and netload_shape is not None
            and len(netload_shape) == hours
            else load_shape
        )
        _window_shape = (
            np.asarray(_window_src, dtype=float)
            if _window_src is not None and len(_window_src) == hours
            else None
        )
        # CHP grid-delivered steam-following floor. The cogen's steady export is
        # forced on; ``chp_grid_pmin_on_frac`` says in WHICH hours.
        #
        # 1.0 -- the default, and what every unit carries unless
        # ``config.chp_steam_duty_window`` is armed -- is the flat all-year
        # assignment this block has always made, so an unarmed run is
        # byte-identical. Below 1.0 (the DUTY WINDOW, caiso-293) the floor is
        # held only in the top ``on_frac x live-hours`` by the SHARED window
        # series resolved directly above -- the same construction the coal
        # synchronization and per-plant CC/ST_GAS committed floors below
        # already use, and the one the deriver's own ``online_frac`` comment
        # prescribes ("it sizes the committed window").
        #
        # WHY (rule 17 [R-FLOOR-WINDOW]). ``steam_level_cf`` is
        # ``on_freq x p50(loading-when-on)`` -- an ENERGY-EQUIVALENT ANNUAL
        # AVERAGE -- and holding it in all 8760 hours turns a cycler into a
        # 24/7 trickle: annual energy approximately conserved, hourly conduct
        # entirely wrong. Measured on the CAISO keeper, five of the thirteen
        # metered floored plants were forced to deliver MORE energy than their
        # own meter recorded for the whole year, and the seven the keeper's D-4
        # fails on have an hour-of-day on-frequency max/min of 12.4-35.0 (the
        # evening ramp) against 1.00-1.04 for the three genuinely flat steam
        # hosts the all-hours window's own evidence cites.
        #
        # LIVE HOURS, not all hours, is the denominator: the deriver takes the
        # on-frequency over AVAILABLE hours, and ``min_gen`` is clipped to
        # ``pmax x availability`` below, so sizing over ``availability > 0``
        # makes the realised window exactly ``on_frac`` of the plant's live
        # time. (This is a deliberate difference from ``coal_sync_online_frac``
        # above, whose own derivation takes its fraction over all hours.)
        _chp_any_windowed = any(
            float(getattr(g, "chp_grid_pmin_on_frac", 1.0)) < 1.0
            and getattr(g, "chp_grid_pmin_mw", 0.0) > 0.0
            for g in generators
        )
        _chp_rank_key = _window_shape if _chp_any_windowed else None
        for g_idx, gen in enumerate(generators):
            pmin_mw = getattr(gen, "chp_grid_pmin_mw", 0.0)
            if pmin_mw <= 0.0:
                continue
            frac = float(getattr(gen, "chp_grid_pmin_on_frac", 1.0))
            if frac >= 1.0 or _chp_rank_key is None:
                min_gen[g_idx, :] = pmin_mw
                min_gen_mech[g_idx, :] = MECH_CHP_STEAM
                continue
            live = np.flatnonzero(availability[g_idx, :] > 0.0)
            if live.size == 0:
                continue
            k = int(round(frac * live.size))
            if k <= 0:
                continue
            # Top-k LIVE hours by the shared driver. ``kind="stable"`` matches
            # the sibling floors, so a tie resolves to the earlier hour rather
            # than arbitrarily.
            hrs = live[np.argsort(-_chp_rank_key[live], kind="stable")[:k]]
            min_gen[g_idx, hrs] = pmin_mw
            min_gen_mech[g_idx, hrs] = MECH_CHP_STEAM
        # Coal synchronization floor (rebuild step 3a,
        # config.coal_sync_srmc_tranche): the _mustrun (contracted, fuel-free)
        # and _sync (spot, SRMC) coal min-load tranches are held on at the
        # measured online Pmin so the unit stays synchronized instead of
        # price-following to zero. The forcing is **online%-scaled** (step-3a
        # full fix): a plant synchronized ~all year (online_frac >=
        # _COAL_SYNC_FORCE_ALL, the supercriticals) is held every hour; a
        # two-shifting cycler is held only in the top-online_frac fraction of
        # hours by the SHARED window series resolved above — mirroring the CT
        # must-run load-shaping, so the floor lands where the cycler actually
        # runs and relaxes in the cheap hours it would real-world shut for.
        # That series is *system load* by default; under
        # config.commitment_floor_window_netload it is NET load, because in a
        # high-VRE ISO the hours a cycler runs are the high-NET-load hours and
        # not the gross-load peaks (SPP-66: measured SPP coal correlates +0.948
        # with net load against +0.716 with system load). The floor is
        # the tranche capacity; min_gen is clipped to pmax*availability below, so
        # an outage hour relaxes it. np.maximum composes with any floor already
        # placed.
        if coal_sync_any:
            sys_load = _window_shape
            # Hours ranked peak-load first; the top-k carry a cycler's floor.
            load_rank = (
                np.argsort(-sys_load, kind="stable") if sys_load is not None else None
            )
            # Whole-operating-day commitment grain
            # (config.coal_sync_window_commitment_grain, pjm-h16) — see the
            # gate block above. ``None`` when unarmed, so
            # ``_mustrun_window_hours`` returns ``load_rank[:k]`` and the hour
            # grain stands byte-identically.
            coal_day_order = (
                _commitment_day_order(sys_load, hours) if _coal_day_grain else None
            )
            # ENSEMBLE PLACEMENT (config.coal_sync_ensemble_level, SPP-71 card
            # R-bc): REPLACES the top-k window above with the continuous-
            # relaxation image of the same measured commitment — pmin x frac in
            # EVERY hour instead of pmin on the top round(frac x 8760) hours and
            # zero elsewhere. Same measured annual synchronized MWh; only the
            # placement moves. Rule 19 [R-ONE-MECH]: the three placements are
            # ALTERNATIVES, never stacked — when this is on, the per-generator
            # branch below short-circuits before the force-all branch, the
            # load_rank branch AND the pjm-h16 day-grain window, which asks a
            # DIFFERENT question of the same floor (that row re-grains the
            # window from hours to whole operating days; this row removes the
            # window). The full rationale, the rule-17/18 window declaration and
            # the SPP identification live on the ScenarioConfig field's citation
            # block.
            ensemble = bool(getattr(config, "coal_sync_ensemble_level", False))
            for g_idx, gen in enumerate(generators):
                pmin_mw = getattr(gen, "coal_sync_pmin_mw", 0.0)
                if pmin_mw <= 0.0:
                    continue
                frac = float(getattr(gen, "coal_sync_online_frac", 1.0))
                # Per-year window vintage
                # (config.coal_sync_online_frac_per_year, pjm-h15): membership
                # and the floor LEVEL stay on the pooled artifact stamped in
                # assembly; only the WINDOW it sizes becomes the SOLVE YEAR's
                # own measured synchronization share. Empty dict (unarmed, a
                # forecast year, or an ISO with no companion artifact) leaves
                # the pooled fraction and the block byte-identical.
                frac = _coal_per_year_frac.get(
                    int(getattr(gen, "plant_code", 0) or 0), frac
                )
                if frac <= 0.0:
                    continue  # measured dark all year
                if ensemble:
                    # E[floor] = pmin x P(synchronized). Clipped to
                    # pmax x availability downstream exactly as the window form,
                    # so an outage hour still relaxes it.
                    level = pmin_mw * min(frac, 1.0)
                    raised = min_gen[g_idx, :] < level
                    np.maximum(min_gen[g_idx, :], level, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_COAL_MUSTRUN
                    continue
                if frac >= _COAL_SYNC_FORCE_ALL or load_rank is None:
                    raised = min_gen[g_idx, :] < pmin_mw
                    np.maximum(min_gen[g_idx, :], pmin_mw, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_COAL_MUSTRUN
                else:
                    k = int(round(frac * hours))
                    if k <= 0:
                        continue
                    hrs = _mustrun_window_hours(
                        load_rank, coal_day_order, k, _coal_day_grain
                    )
                    # Fancy indexing returns a copy, so out= cannot target it;
                    # compute the max then assign back via the fancy index.
                    raised = hrs[min_gen[g_idx, hrs] < pmin_mw]
                    min_gen[g_idx, hrs] = np.maximum(min_gen[g_idx, hrs], pmin_mw)
                    min_gen_mech[g_idx, raised] = MECH_COAL_MUSTRUN
        # Coal MINIMUM ONLINE CONFIGURATION floor
        # (config.ercot_coal_min_config_floor, ercot129-conditional): the plant
        # may not be pushed below the registered minimum load of its SMALLEST
        # online configuration, min_u MinLoad_u (EIA-860) — and it is either
        # ABOVE that level or OFF, never in between.
        #
        # AVAILABILITY-CONDITIONAL, not availability-scaled (ERCOT-128 §P4).
        # A minimum online configuration does NOT shrink when units go out: a
        # 4-unit plant with 2 units on outage still cannot run below ONE unit's
        # 175 MW; it makes 175 MW or it is off. The first build of this floor
        # placed a per-tranche constant and let the generic clip to
        # ``pmax x availability`` scale it, which under ERCOT's DAM
        # availability water-fill (availability well below 1.0 in most hours)
        # put the applied floor BELOW the physical minimum exactly where the
        # defect lives — it removed none of the impossible loadings
        # (14,582 -> 14,886 plant-hours; run
        # 2026-07-28-ercot128-unit-grain-coal, the control). The condition is
        # evaluated on the PLANT's available capacity and the level is then
        # re-allocated across its tranches in FILL order using each tranche's
        # AVAILABLE capacity in that hour, so a partially-available plant still
        # carries its whole minimum configuration instead of a scaled fraction:
        #
        #   total[p,t] = sum_k avail[k,t] x pmax[k]        (k = plant p's tranches)
        #   floor[k,t] = clip(min_config[p] - sum_{j<k} avail_cap[j,t],
        #                     0, avail_cap[k,t])            if total >= min_config
        #              = 0                                  otherwise
        #
        # ``availability`` is EXOGENOUS DATA, not a decision variable, so the
        # conditional is a data-side computation carrying no integrality — this
        # stays inside the pure-LP rule. It is what the exactness proof always
        # described: the plant's online feasible set is the connected interval
        # [min_u MinLoad_u, Cap] *given at least one unit online*, and the
        # else-branch above is that condition (the scaled build dropped it).
        #
        # Rule 17 [R-FLOOR-WINDOW]: driver = the plant's registered unit
        # inventory; window = all 24 hours BY DRIVER (the D4_WINDOWS
        # declaration), and the conditional form is strictly NARROWER than the
        # declaration rather than wider. np.maximum composes with any floor
        # already placed — the binding floor wins, nothing stacks (rule 19
        # [R-ONE-MECH]) — and the id is overwritten only where this mechanism
        # strictly raised min_gen. Vectorized over all 8760 hours (rule 2
        # [R-VECTOR]); the only Python loops are over plants and their handful
        # of tranches.
        if coal_min_config_any:
            # The LEVEL comes from the tranches assembly tagged; the CONDITION
            # and the re-allocation run over ALL of the plant's coal tranches.
            # Both matter: a plant's minimum configuration is a property of the
            # whole plant, so a derated committed tranche must be able to spill
            # the level into the tranches above it rather than shrink it (the
            # ERCOT-128 failure mode in miniature). Restricted to the plant's
            # COAL rows, so a mixed plant's gas-steam tranches (W A Parish
            # 3470) are neither counted nor floored.
            _mc_level: dict[int, float] = {}
            _mc_rows: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                if getattr(gen, "fuel_type", "") != "coal":
                    continue
                code = int(getattr(gen, "plant_code", 0) or 0)
                # assembly appends tranches in fill order, so insertion order
                # IS merit/fill order for the allocation below.
                _mc_rows.setdefault(code, []).append(g_idx)
                share = getattr(gen, "coal_min_config_pmin_mw", 0.0)
                if share > 0.0:
                    _mc_level[code] = _mc_level.get(code, 0.0) + float(share)
            _mc_by_plant = {c: _mc_rows[c] for c in _mc_level}
            _mc_mw = 0.0
            for _code, level in _mc_level.items():
                _idx = _mc_rows[_code]
                if level <= 0.0 or not _idx:
                    continue
                _mc_mw += level
                avail_cap = availability[_idx, :] * pmax[_idx, np.newaxis]
                total = avail_cap.sum(axis=0)
                feasible = total >= level
                # Fill order: each tranche takes what is left of the level, up
                # to its own available capacity that hour.
                taken = np.zeros(hours, dtype=float)
                for row, g_idx in enumerate(_idx):
                    share = np.clip(level - taken, 0.0, avail_cap[row, :])
                    share = np.where(feasible, share, 0.0)
                    taken += share
                    raised = min_gen[g_idx, :] < share
                    np.maximum(min_gen[g_idx, :], share, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_COAL_MIN_CONFIG
            logger.info(
                "coal_min_config floor ARMED (availability-conditional): "
                "%d plants, %.0f MW of minimum online configuration across "
                "%d tranches",
                len(_mc_by_plant),
                _mc_mw,
                sum(len(v) for v in _mc_by_plant.values()),
            )
        # Per-plant gas local-reliability commitment floor
        # (config.cc_mustrun_per_plant / st_gas_mustrun_per_plant): each
        # gate-armed committed tranche is held on at its full capacity in the
        # plant's measured committed window — the top
        # ``cc_mustrun_online_frac`` fraction of hours ranked by SYSTEM LOAD
        # (the same online%-scaled placement the coal synchronization floor
        # uses for cyclers), so the forcing lands where the committed unit
        # actually ran and relaxes in the deepest off-peak troughs. The floor
        # is clipped to pmax*availability below, so an outage hour relaxes
        # it; ``np.maximum`` composes with any floor already placed (e.g. an
        # EMAAC hot-day reliability_floor limb — the binding floor wins, no
        # stacking). The ST_GAS leg stamps its own mechanism id so D-2/D-4
        # attribution stays per-leg.
        if cc_mustrun_any:
            sys_load = _window_shape
            load_rank = (
                np.argsort(-sys_load, kind="stable") if sys_load is not None else None
            )
            # Whole-operating-day commitment grain
            # (config.mustrun_window_commitment_grain, spp-27) — see the gate
            # block above. ``None`` when unarmed, so the hour grain stands.
            day_order = _commitment_day_order(sys_load, hours) if _day_grain else None
            for g_idx, gen in enumerate(generators):
                pmin_mw = getattr(gen, "cc_mustrun_pmin_mw", 0.0)
                if pmin_mw <= 0.0:
                    continue
                frac = float(getattr(gen, "cc_mustrun_online_frac", 0.0))
                if frac <= 0.0:
                    continue
                # Per-year window vintage (config.mustrun_online_frac_per_year):
                # membership stays on the pooled fraction stamped in assembly;
                # the window it sizes becomes the SOLVE YEAR's own measured
                # synchronization share. See the gather block above.
                frac = _per_year_frac.get(
                    (
                        int(getattr(gen, "plant_code", 0) or 0),
                        str(getattr(gen, "plant_group", "") or ""),
                    ),
                    frac,
                )
                if frac <= 0.0:
                    continue  # measured dark all year
                if int(getattr(gen, "plant_code", 0) or 0) in mustrun_excluded:
                    continue  # economic lay-up (config.mustrun_plant_exclusions)
                # miso-67 level swap: ST_GAS plants are floored by the dedicated
                # p25-level block below when st_gas_mustrun_p25_level is armed —
                # the committed-tranche level is replaced, not stacked (rule 19).
                if st_gas_p25_level_on and getattr(gen, "plant_group", "") == "ST_GAS":
                    continue
                mech_id = (
                    MECH_ST_GAS_MUSTRUN_PER_PLANT
                    if getattr(gen, "plant_group", "") == "ST_GAS"
                    else MECH_CC_MUSTRUN_PER_PLANT
                )
                # Measured lay-up window mask (config.mustrun_layup_window_mask,
                # miso-173): cap the floor at the plant's NON-LAID-UP available
                # capacity that hour, pmax x max(0, availability - layup_share).
                # An hour inside a measured lay-up window loses its floor
                # exactly as a measured-outage hour already does under the
                # global pmax x availability clip; no hour is added or moved.
                _lu = _layup_removed.get(
                    (
                        int(getattr(gen, "plant_code", 0) or 0),
                        str(getattr(gen, "plant_group", "") or ""),
                    )
                )
                if frac >= 1.0 or load_rank is None:
                    if _lu is not None:
                        vals = np.minimum(
                            pmin_mw,
                            pmax[g_idx] * np.maximum(0.0, availability[g_idx, :] - _lu),
                        )
                        raised = min_gen[g_idx, :] < vals
                        np.maximum(min_gen[g_idx, :], vals, out=min_gen[g_idx, :])
                    else:
                        raised = min_gen[g_idx, :] < pmin_mw
                        np.maximum(min_gen[g_idx, :], pmin_mw, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = mech_id
                else:
                    k = int(round(frac * hours))
                    if k <= 0:
                        continue
                    hrs = _mustrun_window_hours(load_rank, day_order, k, _day_grain)
                    if _lu is not None:
                        vals = np.minimum(
                            pmin_mw,
                            pmax[g_idx]
                            * np.maximum(0.0, availability[g_idx, hrs] - _lu[hrs]),
                        )
                        # Fancy indexing returns a copy (see the coal block above).
                        raised = hrs[min_gen[g_idx, hrs] < vals]
                        min_gen[g_idx, hrs] = np.maximum(min_gen[g_idx, hrs], vals)
                    else:
                        # Fancy indexing returns a copy (see the coal block above).
                        raised = hrs[min_gen[g_idx, hrs] < pmin_mw]
                        min_gen[g_idx, hrs] = np.maximum(min_gen[g_idx, hrs], pmin_mw)
                    min_gen_mech[g_idx, raised] = mech_id
        # ST_GAS per-plant p25-LEVEL commitment floor
        # (config.st_gas_mustrun_p25_level — the miso-67 level swap for
        # st_gas_mustrun_per_plant). For each gate-armed ST_GAS plant the floor
        # level is the plant's measured 25th-percentile-of-online available-CF
        # times nameplate (thermal_tranche_p25_level) instead of the committed
        # tranche (P5-of-online = LSL). The ST_GAS branch of the cc_mustrun
        # block above is skipped for these plants, so this is the SOLE ST_GAS
        # floor (rule 19 — the level is replaced, not stacked) and it stamps the
        # SAME mechanism id (MECH_ST_GAS_MUSTRUN_PER_PLANT), so D-2/D-4
        # attribution is unchanged. The level is held in the SAME top-
        # ``online_frac`` system-load window as the committed floor and, where it
        # exceeds the committed tranche, distributed cheapest-first across the
        # plant's tranches (committed -> econ), each capped at pmax*availability
        # that hour (the "clipped to pmax*availability as today" clause — an
        # outage hour relaxes the floor). Because p25_cf is a fraction of
        # AVAILABLE capacity, p25_cf*nameplate reconstructs the measured p25
        # output; it stays below available capacity, so the floor never pins the
        # plant. See the ScenarioConfig field for the rule-12/13 grounding.
        if st_gas_p25_tranches:
            sys_load = _window_shape
            load_rank = (
                np.argsort(-sys_load, kind="stable") if sys_load is not None else None
            )
            # Same commitment grain as the committed-tranche seam above: the
            # p25 swap replaces the LEVEL only, so its window construction must
            # stay single-valued (rule 19 [R-ONE-MECH]).
            day_order = _commitment_day_order(sys_load, hours) if _day_grain else None
            p25_forced_mwh = 0.0
            for pc, idxs in st_gas_p25_tranches.items():
                level = st_gas_p25_levels_by_plant.get(pc, 0.0)
                frac = st_gas_p25_frac_by_plant.get(pc, 0.0)
                if level <= 0.0 or frac <= 0.0:
                    continue
                # Per-hour target: the p25 level in the plant's measured
                # committed window (top-frac system-load hours), zero elsewhere.
                target = np.zeros(hours, dtype=float)
                if frac >= 1.0 or load_rank is None:
                    target[:] = level
                else:
                    k = int(round(frac * hours))
                    if k <= 0:
                        continue
                    target[
                        _mustrun_window_hours(load_rank, day_order, k, _day_grain)
                    ] = level
                # Distribute cheapest-first across the plant's tranches, each
                # capped at its available MW that hour; np.maximum composes with
                # any floor already placed (the CT-deployment precedent below).
                # Measured lay-up window mask (config.mustrun_layup_window_mask,
                # miso-173): the clip basis excludes the plant's laid-up
                # capacity share that hour — availability itself is untouched,
                # and the plant-level share applied per tranche sums to exactly
                # the plant's non-laid-up available MW.
                _lu = _layup_removed.get((pc, "ST_GAS"))
                for g_idx in sorted(idxs, key=lambda i: heat_rate[i]):
                    if not target.any():
                        break
                    if _lu is not None:
                        cap = pmax[g_idx] * np.maximum(
                            0.0, availability[g_idx, :] - _lu
                        )
                    else:
                        cap = pmax[g_idx] * availability[g_idx, :]
                    take = np.minimum(target, cap)
                    raised = min_gen[g_idx, :] < take
                    np.maximum(min_gen[g_idx, :], take, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_ST_GAS_MUSTRUN_PER_PLANT
                    p25_forced_mwh += float(take[raised].sum())
                    target = target - take
            logger.info(
                "ST_GAS p25-level floor (%s %s): floored %d plant(s), %.2f TWh "
                "in measured online windows (level = p25_cf x nameplate, "
                "cheapest-first, clipped to pmax*availability)",
                _iso or "ERCOT",
                _yr,
                len(st_gas_p25_tranches),
                p25_forced_mwh / 1e6,
            )
        # Per-plant CT_PEAKER reliability must-run floor: spread each plant's
        # observed monthly net generation (frac-scaled) across that month's
        # hours, *shaped by system load* — the energy is placed in the
        # above-median-load hours (where simple-cycle peakers actually run) and
        # left at zero whenever the peaker was actually offline, so it genuinely
        # starts and stops (it is not held on at a flat baseload level) and
        # displaces marginal gas/imports at the peak rather than coal baseload.
        # The hourly *shape* comes from the plant's CAMPD/CEMS hourly record
        # (zero in every hour the unit did not report load — real start/stop);
        # where a plant has no CAMPD coverage it falls back to the system-load
        # shape (energy placed in the above-median-load hours). Within each hour
        # the floor is distributed over the plant's tranches cheapest-first
        # (committed -> econ -> peak), each capped at its available capacity. The
        # floor units' availability already excludes WEFOR/POF (set above), so
        # the observed energy fits under the cap.
        if ct_floor_plants:
            month_idx = _hour_to_month_index(hours)
            sys_load = _window_shape
            ct_tranches: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                if (
                    gen.plant_group == "CT_PEAKER"
                    and int(gen.plant_code) in ct_floor_plants
                ):
                    ct_tranches.setdefault(int(gen.plant_code), []).append(g_idx)
            # System-load fallback weights (per month, summing to 1.0):
            # max(load - median, 0) concentrates energy in the peak hours.
            load_weights: dict[int, np.ndarray] = {}
            for m in range(12):
                hmask = month_idx == m
                n_h = int(hmask.sum())
                if n_h == 0:
                    continue
                if sys_load is not None:
                    lm = sys_load[hmask]
                    w = np.maximum(lm - np.median(lm), 0.0)
                    if w.sum() <= 0.0:
                        w = np.ones(n_h, dtype=float)
                else:
                    w = np.ones(n_h, dtype=float)
                load_weights[m] = w / w.sum()
            for pc, idxs in ct_tranches.items():
                # Cheapest tranche first so the floor lands on the committed band.
                idxs.sort(key=lambda i: heat_rate[i])
                mwh12 = ct_floor_mwh[pc]
                campd_shape = (
                    ct_campd_shape.get(pc) if ct_campd_shape is not None else None
                )
                for m in range(12):
                    if m not in load_weights:
                        continue
                    energy = ct_floor_frac * float(mwh12[m])
                    if energy <= 0.0:
                        continue
                    hmask = month_idx == m
                    # Prefer the plant's CAMPD on/off shape (zero hours = offline,
                    # so the floor starts/stops); fall back to the load shape.
                    w = None
                    if campd_shape is not None and len(campd_shape) == hours:
                        # NaN hours = unit not reporting = offline -> zero weight,
                        # so the floor genuinely stops there.
                        cs = np.nan_to_num(
                            np.asarray(campd_shape, dtype=float)[hmask],
                            nan=0.0,
                            posinf=0.0,
                            neginf=0.0,
                        )
                        cs = np.maximum(cs, 0.0)
                        if cs.sum() > 0.0:
                            w = cs / cs.sum()
                    if w is None:
                        w = load_weights[m]
                    # Per-hour floor (MW) summing to ``energy`` MWh over the month.
                    remaining = energy * w
                    for g_idx in idxs:
                        if not remaining.any():
                            break
                        # Flat availability within a calendar month for these
                        # units, so the cap is a scalar.
                        cap_mw = float((pmax[g_idx] * availability[g_idx, hmask]).min())
                        take = np.minimum(remaining, cap_mw)
                        min_gen[g_idx, hmask] = take
                        mech_row = min_gen_mech[g_idx, hmask]
                        mech_row[take > 0.0] = MECH_CT_MUSTRUN_PER_PLANT
                        min_gen_mech[g_idx, hmask] = mech_row
                        remaining = remaining - take
        # Per-plant CT_PEAKER AS/RUC-deployment hourly floor: in each plant's
        # measured out-of-merit hours, force its observed net output as a
        # minimum, distributed over the plant's tranches cheapest-first
        # (committed -> econ -> peak) and each capped at the tranche's available
        # MW that hour. The floor is sparse (zero outside deployment hours), so
        # the in-merit hours dispatch economically as before; ``np.maximum``
        # composes it with any reliability must-run floor already placed above
        # rather than clobbering it.
        if ct_deploy_plants:
            ct_d_tranches: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                if (
                    gen.plant_group == "CT_PEAKER"
                    and int(gen.plant_code) in ct_deploy_plants
                ):
                    ct_d_tranches.setdefault(int(gen.plant_code), []).append(g_idx)
            deploy_mwh = 0.0
            for pc, idxs in ct_d_tranches.items():
                idxs.sort(key=lambda i: heat_rate[i])
                remaining = ct_deploy_frac * ct_deploy_floor[pc]  # (hours,)
                deploy_mwh += float(remaining.sum())
                for g_idx in idxs:
                    cap = pmax[g_idx] * availability[g_idx, :]
                    take = np.minimum(remaining, cap)
                    raised = min_gen[g_idx, :] < take
                    np.maximum(min_gen[g_idx, :], take, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_CT_DEPLOYMENT_OVERLAY
                    remaining = remaining - take
            logger.info(
                "CT deployment overlay (%s %s): floored %d peaker(s), "
                "%.2f TWh of out-of-merit energy (frac %.2f)",
                _iso or "ERCOT",
                _yr,
                len(ct_d_tranches),
                deploy_mwh / 1e6,
                ct_deploy_frac,
            )
        # Per-plant spatial reliability-deployment hourly floor: in each
        # load-pocket plant's measured congestion-subset hours (economic at its
        # local load-zone price, out of merit at the system hub), force its
        # observed net output as a minimum, distributed over the plant's
        # tranches cheapest-first and each capped at that tranche's available MW.
        # Keyed by plant code (any thermal class), so a split plant's tranches
        # are gathered together. The floor is sparse (zero outside the
        # congestion hours), so in-merit hours dispatch economically as before;
        # ``np.maximum`` composes it with any floor already placed above.
        if rd_deploy_plants:
            rd_tranches: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                pc = int(gen.plant_code)
                if pc in rd_deploy_plants:
                    rd_tranches.setdefault(pc, []).append(g_idx)
            rd_mwh = 0.0
            for pc, idxs in rd_tranches.items():
                idxs.sort(key=lambda i: heat_rate[i])
                remaining = rd_deploy_frac * rd_deploy_floor[pc]  # (hours,)
                rd_mwh += float(remaining.sum())
                for g_idx in idxs:
                    cap = pmax[g_idx] * availability[g_idx, :]
                    take = np.minimum(remaining, cap)
                    raised = min_gen[g_idx, :] < take
                    np.maximum(min_gen[g_idx, :], take, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_RELIABILITY_DEPLOYMENT_OVERLAY
                    remaining = remaining - take
            logger.info(
                "reliability deployment overlay (%s %s): floored %d "
                "pocket plant(s), %.2f TWh of congestion energy (frac %.2f)",
                _iso or "ERCOT",
                _yr,
                len(rd_tranches),
                rd_mwh / 1e6,
                rd_deploy_frac,
            )
        # Conventional-hydro minimum-flow floor (config.hydro_min_flow_floor,
        # stamped per unit by data.hydro.build_hydro_fleet as a 12-entry
        # month-constant MW vector): run-of-river inflow that cannot be stored
        # plus the environmental / FERC-licence minimum releases the fleet must
        # pass. The hydro budget rows cap a plant's monthly ENERGY but impose no
        # lower bound, so the purely-economic LP parks the fleet at 0 MW in the
        # solar belly, which the measured fleet never does. The level is
        # MONTH-constant by design — a diurnal floor would pin the measured
        # shape (rule 13) — and the allocator already clipped the fleet level to
        # the month's average power, so the two-sided budget row stays feasible.
        # ``np.maximum`` composes with any floor already placed (none today: no
        # other mechanism floors hydro, rule 19).
        if hydro_min_flow_any:
            month_of_hour = _hour_to_month_index(hours)  # 0-based month per hour
            for g_idx, gen in enumerate(generators):
                monthly = getattr(gen, "hydro_min_flow_monthly_mw", None)
                if not monthly:
                    continue
                floor_t = np.asarray(monthly, dtype=float)[month_of_hour]
                if not np.any(floor_t > 0.0):
                    continue
                raised = min_gen[g_idx, :] < floor_t
                np.maximum(min_gen[g_idx, :], floor_t, out=min_gen[g_idx, :])
                min_gen_mech[g_idx, raised] = MECH_HYDRO_MIN_FLOW
        # Hydro RoR flat dispatch (config.hydro_ror_split, stamped by
        # data.hydro.build_hydro_fleet): the floor half of min == max — the
        # availability cap in generators_to_fleet_arrays already limits the
        # unit to the same flat level, so together they FIX dispatch at the
        # plant's own monthly water. Rule 19: an RoR unit never also carries
        # a min-flow stamp (build_hydro_fleet allocates the floor over the
        # reservoir class only), so the two ids never contend.
        if hydro_ror_any:
            month_of_hour = _hour_to_month_index(hours)
            for g_idx, gen in enumerate(generators):
                monthly = getattr(gen, "hydro_ror_flat_monthly_mw", None)
                if not monthly:
                    continue
                flat_t = np.asarray(monthly, dtype=float)[month_of_hour]
                if not np.any(flat_t > 0.0):
                    continue
                raised = min_gen[g_idx, :] < flat_t
                np.maximum(min_gen[g_idx, :], flat_t, out=min_gen[g_idx, :])
                min_gen_mech[g_idx, raised] = MECH_HYDRO_ROR_FLAT
        # Never demand more than the (outage/derate-adjusted) availability.
        np.minimum(min_gen, pmax[:, np.newaxis] * availability, out=min_gen)
        # COMMITMENT-FEASIBILITY CLIP
        # (config.mustrun_commitment_feasibility_clip, spp-42 card R-be).
        # The line above derates the per-plant must-run floor LINEARLY, and
        # because the committed tranche's ``cc_mustrun_pmin_mw`` IS its own
        # ``pmax`` the floor it leaves is exactly "tranche pmax x
        # availability". But that floor asserts a COMMITMENT — the plant is
        # synchronized at its own measured minimum online level — and a
        # commitment is not linear. Where a dated outage leaves the plant less
        # available capacity than that level, NO configuration the plant has
        # ever operated is feasible, and the ``np.minimum`` above silently
        # substitutes a smaller, equally infeasible commitment instead of
        # none: SPP keeper 11 floors single-unit Cimarron River (1230, 50 MW)
        # at a median 1.33 MW — 6.2 % of its own 21.6 MW minimum online level
        # — across 845 hours its own CAMPD meter reads zero (spp-42 phase 0).
        # Zero the floor in exactly those hours; every other hour keeps the
        # incumbent clip untouched.
        # Scoped to the two per-plant commitment mechanisms by their own
        # mechanism stamp, so no other floor is reachable (rule 19
        # [R-ONE-MECH]: the ONE floor's clip is replaced in the infeasible
        # hours, nothing is stacked; a cell where a different floor won the
        # composition carries that floor's stamp and is not touched).
        # Rule 21 [R-DOF]: ZERO free parameters and zero new inputs — the test
        # is the plant's own committed level against its own available
        # capacity, on the SAME basis the clip above already uses.
        # Rule 13 [R-MEASURED]: nothing measured enters; both operands are
        # arrays the LP already holds, so the rule regenerates in a FORECAST
        # year identically and responds to that year's own availability.
        if config is not None and getattr(
            config, "mustrun_commitment_feasibility_clip", False
        ):
            # The asserted level is summed over the FLOORED rows (the committed
            # tranches carrying ``cc_mustrun_pmin_mw``); the available capacity
            # is summed over ALL of that plant-group's rows, because the whole
            # plant-group is what physically carries the commitment — a
            # committed block can be served by any of the plant's capacity, and
            # testing the committed tranche against its own derated self would
            # reduce to "availability < 1" and fire on the EFOR baseline.
            _feas_cap: dict[tuple[int, str], np.ndarray] = {}
            _feas_lvl: dict[tuple[int, str], float] = {}
            _feas_rows: dict[tuple[int, str], list[int]] = {}
            _keyed: list[tuple[int, str] | None] = []
            for g_idx, gen in enumerate(generators):
                key = (
                    int(getattr(gen, "plant_code", 0) or 0),
                    str(getattr(gen, "plant_group", "") or ""),
                )
                _keyed.append(key)
                lvl = float(getattr(gen, "cc_mustrun_pmin_mw", 0.0) or 0.0)
                if lvl <= 0.0:
                    continue
                _feas_lvl[key] = _feas_lvl.get(key, 0.0) + lvl
            for g_idx, key in enumerate(_keyed):
                if key is None or key not in _feas_lvl:
                    continue
                cur = _feas_cap.get(key)
                add = pmax[g_idx] * availability[g_idx, :]
                _feas_cap[key] = add if cur is None else cur + add
                _feas_rows.setdefault(key, []).append(g_idx)
            _n_infeasible = 0
            _mwh_dropped = 0.0
            for key, lvl in _feas_lvl.items():
                bad = _feas_cap[key] < lvl - 1e-9
                if not bad.any():
                    continue
                _n_infeasible += int(bad.sum())
                rows = np.asarray(_feas_rows[key], dtype=int)
                own = np.isin(
                    min_gen_mech[np.ix_(rows, np.flatnonzero(bad))],
                    (MECH_CC_MUSTRUN_PER_PLANT, MECH_ST_GAS_MUSTRUN_PER_PLANT),
                )
                blk = min_gen[np.ix_(rows, np.flatnonzero(bad))]
                _mwh_dropped += float(blk[own].sum())
                # Fancy indexing returns a copy (see the coal block above).
                min_gen[np.ix_(rows, np.flatnonzero(bad))] = np.where(own, 0.0, blk)
            logger.info(
                "mustrun_commitment_feasibility_clip ARMED (%s %s): %d floored "
                "plant-groups tested, %d infeasible plant-hours, %.1f MWh of "
                "commitment floor released",
                _iso or "ERCOT",
                _yr,
                len(_feas_lvl),
                _n_infeasible,
                _mwh_dropped,
            )
        # An outage hour that collapsed the floor is no longer forced.
        clear_where_unfloored(min_gen_mech, min_gen)
    return min_gen, min_gen_mech


def generators_to_fleet_arrays(
    generators: list[Generator],
    zone_names: list[str],
    hours: int = 8760,
    iso: str | None = None,
    config: ScenarioConfig | None = None,
    load_shape: np.ndarray | None = None,
    netload_shape: np.ndarray | None = None,
    ct_campd_shape: dict[int, np.ndarray] | None = None,
    year: int | None = None,
) -> FleetArrays:
    """Convert a list of generators into vectorized ``FleetArrays``.

    Availability is set to ``1 - eford`` for every hour. When ``iso`` is
    given and has :data:`NUCLEAR_MONTHLY_CF` factors, nuclear generators get
    a month-varying availability instead, capturing refueling outages and
    planned maintenance. Other seasonal derates are applied later.

    Coal carries no Pmin floor: each coal plant enters as CAMPD take-or-pay
    tranches (see :func:`bins_to_fleet` / :func:`campd_tranche_fuel_frac`),
    each with ``pmin_mw = 0``, so coal's baseload behavior emerges from
    tranche economics rather than a hard minimum.

    ``netload_shape`` is the optional NET-load series (demand less available
    wind/solar) the commitment-floor window ranks on when
    ``config.commitment_floor_window_netload`` is set; it is forwarded
    unchanged to :func:`_compose_min_gen_floors`, which owns the selection.
    Leaving it ``None`` keeps the historical system-load window and is what
    every caller that does not build VRE arrays should pass.
    """
    # capx D88 [R-ONE-MECH rule 19 / R-DOF rule 21]: ``unit_id`` IS a key, so
    # assert it here -- the ONE seam every LP fleet passes through -- rather than
    # in the five downstream consumers that silently collapse on a duplicate.
    #
    # WHY THIS EXISTS. ``retirements.py``'s ``idx_of`` map is last-write-wins, so
    # two generators sharing an id read the SAME LP dispatch row inside the step-3
    # exit screen; ``exit_exempt_unit_ids``, the ``retired`` set and
    # ``_pre_entry_ids_all`` are set memberships with no fuel to qualify by, so one
    # twin's exemption exempts both and RETIRING ONE TWIN DROPS BOTH from the fleet
    # (a capacity leak, not bookkeeping); ``loss_years`` shares one exit clock; and
    # the D57 sell-offer stack double-offers under one id. None of that raises --
    # it silently mis-decides, which is why the defect ran for eighteen scored
    # years on the program's only NEISO T3 golden before a census found it.
    #
    # Duplicates are an EVOLVED-fleet event only: a base fleet is built from
    # distinct plant/bin keys, so this is silent on every backcast (which rebuilds
    # its base fleet yearly and never enters ``evolve_fleet``), every hindcast and
    # every crossover year -- proved by an on-recipe ``fleet_only`` rebuild of all
    # seven backcast keepers and the T1-F/T1-H recipes before this landed.
    # Costs one set build per call; changes no decision.
    # docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md §2.1/§2.4
    # docs/handoffs/FINDING-capx-d88-2026-09-08.md
    _unit_ids = [g.unit_id for g in generators]
    if len(set(_unit_ids)) != len(_unit_ids):
        _counts = Counter(_unit_ids)
        _dupes = sorted(uid for uid, n in _counts.items() if n > 1)
        raise ValueError(
            "duplicate unit_id in fleet passed to generators_to_fleet_arrays "
            f"(iso={iso}, year={year}, n_gen={len(_unit_ids)}): "
            + ", ".join(f"{uid!r}x{_counts[uid]}" for uid in _dupes)
            + " -- unit_id is a key (retirements.idx_of, exit_exempt_unit_ids, "
            "the retired/survivor set-diff, loss_years and the D57 sell-offer "
            "stack all address units by it). See capx D88."
        )

    zone_to_idx = {name: i for i, name in enumerate(zone_names)}

    n_gen = len(generators)
    pmax = np.array([g.pmax_mw for g in generators], dtype=float)
    pmin = np.array([g.pmin_mw for g in generators], dtype=float)
    heat_rate = np.array([g.heat_rate for g in generators], dtype=float)
    vom = np.array([g.vom for g in generators], dtype=float)
    emission_rate = np.array([g.emission_rate_co2 for g in generators], dtype=float)
    nox_rate = np.array([g.nox_rate for g in generators], dtype=float)
    so2_rate = np.array([g.so2_rate for g in generators], dtype=float)
    zone_idx = np.array([zone_to_idx[g.zone] for g in generators], dtype=int)
    fuel_type_idx = np.array(
        [FUEL_TYPE_MAP[g.fuel_type] for g in generators], dtype=int
    )

    eford = np.array([g.eford for g in generators], dtype=float)
    availability = np.broadcast_to((1.0 - eford)[:, np.newaxis], (n_gen, hours)).copy()

    _iso = iso.upper() if iso else None
    _yr = getattr(config, "weather_year", None) if config is not None else None
    _nuclear_monthly(generators, availability, hours, _iso, _yr, config)

    # Per-plant CT_PEAKER reliability must-run floor (config.ct_mustrun_per_plant,
    # backcast only). The observed EIA-923 net generation is forced on these
    # peakers as a minimum below; because that floor already nets out every real
    # outage, WEFOR and the planned-outage (maintenance) derate must NOT apply to
    # the floor units (they would double-count and clip it). The table is keyed
    # by plant code; an empty table (flag off, or forecast/missing 923) leaves
    # every code path byte-identical.
    ct_floor_mwh: dict[int, np.ndarray] = {}
    ct_floor_frac = 0.0
    if (
        config is not None
        and getattr(config, "ct_mustrun_per_plant", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        ct_floor_frac = float(getattr(config, "ct_mustrun_floor_frac", 1.0) or 0.0)
        if ct_floor_frac > 0.0:
            ct_floor_mwh = ct_mustrun_floor_mwh_by_plant(int(_yr))
    ct_floor_plants = set(ct_floor_mwh)
    # Per-plant CT_PEAKER AS/RUC-deployment hourly floor (config
    # .ct_deployment_overlay, backcast only): the measured out-of-merit CEMS
    # energy, applied below as a sparse per-hour min-gen bound. Unlike the
    # must-run floor above, the deployment units keep the statistical WEFOR/POF
    # model (the floor is well below pmax in its hours), so they are NOT added
    # to ct_floor_plants — only availability-capped where they coincide.
    ct_deploy_floor: dict[int, np.ndarray] = {}
    ct_deploy_frac = 0.0
    if (
        config is not None
        and getattr(config, "ct_deployment_overlay", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        ct_deploy_frac = float(getattr(config, "ct_deployment_floor_frac", 1.0) or 0.0)
        if ct_deploy_frac > 0.0:
            ct_deploy_floor = ct_deployment_floor_for_year(
                int(_yr), hours, _iso or "ERCOT"
            )
    ct_deploy_plants = set(ct_deploy_floor)
    # Spatial reliability-deployment hourly floor (config
    # .reliability_deployment_overlay, backcast only): the load-pocket thermal
    # fleet's measured congestion-subset CEMS energy (CC_REGULAR/COAL/ST_GAS/
    # CC_CHP in South_Central/West/Northeast). Applied below as a sparse per-hour
    # min-gen bound keyed by plant code, distributed cheapest-first over the
    # plant's tranches. Like the CT deployment floor, these units keep the
    # statistical WEFOR/POF model (the floor is sparse and below pmax), so they
    # are only availability-capped where they coincide.
    rd_deploy_floor: dict[int, np.ndarray] = {}
    rd_deploy_frac = 0.0
    if (
        config is not None
        and getattr(config, "reliability_deployment_overlay", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        rd_deploy_frac = float(
            getattr(config, "reliability_deployment_floor_frac", 1.0) or 0.0
        )
        if rd_deploy_frac > 0.0:
            rd_deploy_floor = reliability_deployment_floor_for_year(
                int(_yr), hours, _iso or "ERCOT"
            )
    rd_deploy_plants = set(rd_deploy_floor)
    _availability_matrix(
        generators, availability, hours, config, _iso, year, ct_floor_plants
    )

    _apply_outage_overlays(
        generators, availability, pmax, heat_rate, hours, config, _iso, _yr
    )

    # Hydro RoR flat dispatch, availability half (config.hydro_ror_split,
    # stamped by data.hydro.build_hydro_fleet): cap the unit at its flat
    # monthly level flat[g, m] / pmax so pmax x availability == the flat MW.
    # The min_gen half in _compose_min_gen_floors floors it at the same level
    # (MECH_HYDRO_ROR_FLAT), fixing the RoR plant's dispatch at its own
    # measured monthly water — run-of-river output cannot chase price. Applied
    # AFTER the outage overlays so nothing re-inflates the cap (no overlay
    # touches hydro today; the order makes that a guarantee, not an accident).
    if any(getattr(g, "hydro_ror_flat_monthly_mw", None) for g in generators):
        _ror_month_of_hour = _hour_to_month_index(hours)
        for _g_idx, _gen in enumerate(generators):
            _monthly = getattr(_gen, "hydro_ror_flat_monthly_mw", None)
            if not _monthly or pmax[_g_idx] <= 0.0:
                continue
            _flat_t = np.asarray(_monthly, dtype=float)[_ror_month_of_hour]
            np.minimum(
                availability[_g_idx, :],
                _flat_t / pmax[_g_idx],
                out=availability[_g_idx, :],
            )

    min_gen, min_gen_mech = _compose_min_gen_floors(
        generators,
        availability,
        pmax,
        pmin,
        heat_rate,
        hours,
        config,
        _iso,
        _yr,
        load_shape,
        ct_campd_shape,
        ct_floor_mwh,
        ct_floor_frac,
        ct_floor_plants,
        ct_deploy_floor,
        ct_deploy_frac,
        ct_deploy_plants,
        rd_deploy_floor,
        rd_deploy_frac,
        rd_deploy_plants,
        netload_shape=netload_shape,
    )

    # Ancillary-service reserve withholding (backcast). Capacity the market
    # holds out of energy as upward reserve is withdrawn from the gas/flexible-
    # thermal top-of-merit headroom (most expensive/peaking headroom first —
    # the part-loaded capacity that physically carries the reserve), so the
    # energy supply curve clears without it and the afternoon-peak price lifts.
    # ERCOT: the cleared DAM up-AS (Reg-Up/RRS/ECRS); when the per-resource-type
    # series is available each thermal class withholds *its own measured* hourly
    # AS MW from its top-of-merit headroom (the physically-grounded split;
    # storage/load AS, which carry the bulk in ERCOT, are excluded as they do
    # not withhold thermal energy), else the system-total upper bound on the gas
    # pool. PJM: the measured RT Primary Reserve requirement (the binding
    # upward 10-min product that nests Synchronized, Manual 11 sec 4.4.1) on the
    # gas + flexible-oil pool (coal/nuclear baseload excluded). The withdrawn
    # pool is consistent with scarcity.pjm_online_reserve, which measures
    # plant-level online reserve over the same thermal fleet. Applied last,
    # after every outage/derate; floored back up to any must-run min_gen.
    # Down-AS (Reg-Down) is excluded upstream — it removes no upward offer.
    if (
        config is not None
        and getattr(config, "as_reserve_withholding", False)
        and _iso in _AS_WITHHOLDING
    ):
        _yr_as = getattr(config, "weather_year", 0)
        pool_groups = _AS_WITHHOLDING[_iso][2]
        withdrawn = unmet = 0.0
        # Per-resource-type split is ERCOT-only (no PJM per-type AS file);
        # every other ISO uses the system-total measured series on its pool.
        by_class = (
            load_as_thermal_withholding(_yr_as, hours) if _iso == "ERCOT" else None
        )
        if by_class is not None:
            for col, series in by_class.items():
                pool = np.array(
                    [
                        i
                        for i, g in enumerate(generators)
                        if g.plant_group in _AS_RESTYPE_TO_GROUPS[col]
                    ],
                    dtype=int,
                )
                w, u = _withdraw_top_of_merit(
                    availability, pmax, heat_rate, pool, series
                )
                withdrawn += w
                unmet += u
            source = "measured per-type"
        else:
            as_mw = load_as_reserve_withholding_mw(_yr_as, hours, iso=_iso)
            pool = np.array(
                [i for i, g in enumerate(generators) if g.plant_group in pool_groups],
                dtype=int,
            )
            if as_mw is not None:
                withdrawn, unmet = _withdraw_top_of_merit(
                    availability, pmax, heat_rate, pool, as_mw
                )
            source = (
                "measured PR requirement"
                if _iso == "PJM"
                else "system-total upper bound"
            )
        if min_gen is not None:
            floor_frac = np.zeros_like(availability)
            np.divide(
                min_gen,
                pmax[:, np.newaxis],
                out=floor_frac,
                where=pmax[:, np.newaxis] > 0.0,
            )
            np.maximum(availability, floor_frac, out=availability)
        np.clip(availability, 0.0, 1.0, out=availability)
        logger.info(
            "AS reserve withholding (%s %s, %s): withdrew %.1f GWh-equiv "
            "from thermal top-of-merit (%.1f GWh unmet by headroom)",
            _iso,
            _yr_as,
            source,
            withdrawn / 1e3,
            unmet / 1e3,
        )

    # CAISO formula-based operating-reserve withholding (default off; the
    # measured-OASIS path is unavailable until the remote-env outbound-network
    # block is lifted). Computes R(t) = max(MSSC, 0.067*load) + 0.01*load from
    # the load shape and the fleet's largest single-unit nameplate (the WECC
    # MSSC), then withdraws it from the gas top-of-merit headroom exactly like
    # the measured ERCOT/PJM path above — lifting the tight-hour / evening-tail
    # price. Coal/nuclear baseload is left out of the pool, and the midday floor
    # (a separate longness/marginal-offer problem) is untouched.
    if (
        config is not None
        and getattr(config, "as_reserve_formula", False)
        and _iso == "CAISO"
        and load_shape is not None
    ):
        mssc_mw = float(
            max(
                (
                    pmax[i]
                    for i, g in enumerate(generators)
                    if g.fuel_type not in _CAISO_MSSC_EXCLUDE_FUELS
                ),
                default=0.0,
            )
        )
        r_mw = caiso_operating_reserve_mw(load_shape, mssc_mw, hours)
        pool = np.array(
            [i for i, g in enumerate(generators) if g.plant_group in _AS_GAS_GROUPS],
            dtype=int,
        )
        withdrawn, unmet = _withdraw_top_of_merit(
            availability, pmax, heat_rate, pool, r_mw
        )
        if min_gen is not None:
            floor_frac = np.zeros_like(availability)
            np.divide(
                min_gen,
                pmax[:, np.newaxis],
                out=floor_frac,
                where=pmax[:, np.newaxis] > 0.0,
            )
            np.maximum(availability, floor_frac, out=availability)
        np.clip(availability, 0.0, 1.0, out=availability)
        logger.info(
            "CAISO operating-reserve withholding (formula, %s): MSSC %.0f MW, "
            "R(t) mean %.0f / max %.0f MW; withdrew %.1f GWh-equiv from gas "
            "top-of-merit (%.1f GWh unmet by headroom)",
            getattr(config, "weather_year", 0),
            mssc_mw,
            float(r_mw.mean()),
            float(r_mw.max()),
            withdrawn / 1e3,
            unmet / 1e3,
        )

    # Commercial-operation-date (COD) vintage ramp — the single COD mechanism
    # for the whole fleet (data.cod_ramp). A unit that came online or retired
    # part-way through the solved year is available only in the months it
    # actually operated, instead of the all-year-or-nothing annual screen: the
    # thermal/nuclear/oil analogue of the renewable/storage vintage ramps. The
    # month-precise COD is resolved at the grain the LP unit actually has
    # (data.cod_ramp.generator_online_mask; SOCO-15, owner card S12): a raw
    # EIA-860 unit keeps its OWN measured Operating Year / Month (rule 14
    # [R-ACCURATE]); a plant-level CAMPD bin — which carries no unit date of
    # its own — takes the measured online-capacity FRACTION of its (plant,
    # group) constituents from the same EIA-860 sheet (load_unit_cod_map), so
    # a brownfield addition ramps in on its real month; the plant-collapsed
    # date (load_cod_map) is the fall-back only where neither exists. Applied
    # last (after every outage/derate/withholding) so nothing re-raises an
    # offline month; min_gen (the hard must-run floor) is scaled by the same
    # mask, else the LP lower bound would force a not-yet-built/retired unit
    # to run. Default-on for backcasts (config.cod_ramp_enabled); forecast
    # runs pass an explicit calendar ``year`` to engage it.
    _cod_year = year if year is not None else getattr(config, "weather_year", None)
    if (
        config is not None
        and getattr(config, "cod_ramp_enabled", True)
        and getattr(config, "mode", "forecast") == "backcast"
        and _cod_year is not None
    ):
        cod_map = _pkg_ns().load_cod_map()
        unit_cod_map = _pkg_ns().load_unit_cod_map()
        online_mask = np.ones((n_gen, 12), dtype=float)
        cod_class_labels: list[str] = []
        cod_online_years: list[int | None] = []
        for g_idx, gen in enumerate(generators):
            online_mask[g_idx], oy = generator_online_mask(
                int(gen.plant_code),
                gen.plant_group,
                gen.online_year,
                gen.online_month,
                gen.retirement_year,
                gen.retirement_month,
                bool(gen.is_campd_bin),
                cod_map,
                unit_cod_map,
                _cod_year,
            )
            # Per-class COD coverage guardrail: a class whose units all resolve
            # to a known EIA-860 COD is month-precision ramped; a class with no
            # COD dates silently bypasses the vintage ramp (data.cod_ramp
            # .log_class_cod_coverage WARNs so a future vintage cannot drop a
            # class unnoticed). Synthetic, non-physical units (plant_code <= 0 —
            # the WECC import-node tranches) carry no EIA-860 COD by design and
            # are excluded; the audit covers only real EIA-860 plants.
            if int(gen.plant_code) > 0:
                cod_class_labels.append(gen.plant_group or gen.fuel_type)
                cod_online_years.append(oy)
        log_class_cod_coverage(
            class_cod_coverage(cod_class_labels, cod_online_years), _iso, _cod_year
        )
        if (online_mask < 1.0).any():
            month_idx = _hour_to_month_index(hours)
            ramp = online_mask[:, month_idx]  # (n_gen, hours) 0/1
            availability *= ramp
            if min_gen is not None:
                min_gen *= ramp
                # Offline months carry no floor, hence no forcing mechanism.
                clear_where_unfloored(min_gen_mech, min_gen)
            dropped = int((online_mask.max(axis=1) < 1.0).sum())
            offline = int((online_mask < 1.0).sum())
            logger.info(
                "COD ramp (%s %s): %d unit-months masked offline "
                "(mid-year COD / retirement), %d unit(s) fully not-yet-built/"
                "retired",
                _iso,
                _cod_year,
                offline,
                dropped,
            )

    # Balancing-authority JOIN month mask (lane R-SOCO-B, owner ruling (B)
    # 2026-09-25; constants.ISO_BA_JOINS). In a joining BA's join year its
    # plants — admitted by the fleet loader from the join-year vintage, which
    # still codes them to the joining BA — are inside the region only from the
    # join month, because the region's EIA-930 demand includes their load only
    # from then (SOCO: PowerSouth ``AEC``, 2021-09-01). The same month-grain
    # 0/1 mask the COD ramp applies, applied AFTER it so nothing re-raises a
    # pre-join month, with min_gen scaled likewise. Backcast-only (a forecast
    # year is past every registered join); an empty map for every other region
    # and year, so they are byte-identical.
    if (
        config is not None
        and getattr(config, "mode", "forecast") == "backcast"
        and _cod_year is not None
        and _iso is not None
    ):
        from market_sim.data.ba_membership import ba_join_first_month

        _join = ba_join_first_month(_iso, int(_cod_year))
        if _join:
            first = np.array(
                [_join.get(int(g.plant_code), 1) for g in generators], dtype=int
            )
            if (first > 1).any():
                month_idx = _hour_to_month_index(hours)
                member = (
                    (month_idx[np.newaxis, :] + 1) >= first[:, np.newaxis]
                ).astype(float)
                availability *= member
                if min_gen is not None:
                    min_gen *= member
                    clear_where_unfloored(min_gen_mech, min_gen)
                logger.info(
                    "BA join (%s %s): %d unit(s), %.0f MW admitted from a joining "
                    "balancing authority, offline before their join month",
                    _iso,
                    _cod_year,
                    int((first > 1).sum()),
                    float(pmax[first > 1].sum()),
                )

    # Balancing-authority EXIT hour mask (lane R-SOCO-B2, owner ruling (C)
    # 2026-09-25, hour grain; constants.ISO_BA_EXITS). The twin of the join
    # mask: a recoded plant still inside the region for part of its exit year
    # (admitted by the fleet loader, ``ba_membership.exit_member_plants``) is
    # offline from the first LP row at or after its exit stamp, because the
    # region's EIA-930 demand stops including its load then (SOCO: the former
    # Gulf Power plants, to FPL at hour-ending UTC 2022-07-13 12:00, row 4637).
    # min_gen scaled likewise. Backcast-only; an empty map for every other
    # region and year, so they are byte-identical.
    if (
        config is not None
        and getattr(config, "mode", "forecast") == "backcast"
        and _cod_year is not None
        and _iso is not None
    ):
        from market_sim.data.ba_membership import ba_exit_first_outside_row

        _exit = ba_exit_first_outside_row(_iso, int(_cod_year))
        if _exit:
            last = np.array(
                [_exit.get(int(g.plant_code), hours) for g in generators], dtype=int
            )
            if (last < hours).any():
                member = (np.arange(hours)[np.newaxis, :] < last[:, np.newaxis]).astype(
                    float
                )
                availability *= member
                if min_gen is not None:
                    min_gen *= member
                    clear_where_unfloored(min_gen_mech, min_gen)
                logger.info(
                    "BA exit (%s %s): %d unit(s), %.0f MW leave the region at "
                    "LP row %d",
                    _iso,
                    _cod_year,
                    int((last < hours).sum()),
                    float(pmax[last < hours].sum()),
                    int(last.min()),
                )

    # Measured ramp/fast-start capability (GATED config.measured_ramp_capability,
    # default off): reconcile the class 10-minute fractions against the
    # ramp-capability clean datatype (EIA-860 "10M" fast-start floor + CAMPD
    # CEMS hourly-envelope ceiling, data/ramp_capability.py). Class fractions
    # remain the uncovered-plant fallback.
    _measured_ramp: dict | None = None
    if (
        config is not None
        and getattr(config, "measured_ramp_capability", False)
        and iso is not None
    ):
        from market_sim.data.ramp_capability import load_measured_ramp_capability

        _measured_ramp = load_measured_ramp_capability(iso)

    return FleetArrays(
        pmax=pmax,
        pmin=pmin,
        heat_rate=heat_rate,
        vom=vom,
        emission_rate=emission_rate,
        nox_rate=nox_rate,
        so2_rate=so2_rate,
        zone_idx=zone_idx,
        fuel_type_idx=fuel_type_idx,
        availability=availability,
        unit_ids=_unit_ids,
        efficiency_bin=np.array([g.efficiency_bin for g in generators], dtype=str),
        plant_code=np.array([int(g.plant_code) for g in generators], dtype=int),
        state=np.array([g.state for g in generators], dtype=object),
        plant_group=np.array([g.plant_group for g in generators], dtype=object),
        min_gen=min_gen,
        min_gen_mechanism=min_gen_mech,
        ramp10=_ramp10_capability(generators, pmax, measured=_measured_ramp),
    )
