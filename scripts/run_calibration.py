"""Run the dispatch model for calibration years and print comparison tables.

Backcasts the hourly economic dispatch against historical years (2021-2024)
for which EIA actuals exist, then prints headline diagnostics — generation by
fuel, CO2, zonal prices, negative-price hours and renewable curtailment — so
the modeled year can be eyeballed against the eGRID benchmark.

Each calibration year is run as a single-year dispatch (no capacity
evolution): the EIA-860 fleet is dispatched against that year's EIA-930
demand and renewable profiles, with the renewable capacity and gas price
pinned to the year's measured values.

Usage:
    python scripts/run_calibration.py --year 2023
    python scripts/run_calibration.py --year 2021 2022 2023 2024
    python scripts/run_calibration.py --year 2023 --hours 168
    python scripts/run_calibration.py --year 2023 --ttc-wn 9000 --ttc-wsc 3000

Options:
    --year         One or more calibration years to run.
    --iso          ISO to calibrate (default ERCOT).
    --hours        Dispatch horizon in hours (default 8760); use a small
                   value such as 168 for a quick smoke test.
    --ttc-wn       Override the West<->North transfer capability (MW).
    --ttc-wsc      Override the West<->South_Central transfer capability (MW).
    --ttc-pn       Override the Panhandle<->North transfer capability (MW).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import fields
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    GAS_BASIS_DIFFERENTIAL,
    HOURS_PER_YEAR,
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_YEAR,
    resolve_reference_price_interface,
)
from market_sim.config.interchange_config import (  # noqa: E402
    INTERFACE_NEIGHBORS,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
    resolve_priced_interchange,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
)
from market_sim.data.hydro import build_hydro_fleet  # noqa: E402
from market_sim.data.coal import coal_takeorpay_share  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    _hour_to_month_index,
    COAL_MUSTRUN_BY_PLANT,
    aggregate_fleet,
    apply_coal_tranches,
    apply_ct_netload_drag_floor,
    apply_gas_st_netload_drag_floor,
    assemble_mc,
    bins_to_fleet,
    campd_tranche_fuel_frac,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_campd_bins,
    load_fleet_from_csv,
    load_retired_within_window,
    thermal_tranche_overrides,
)
from market_sim.data.offer_curves import (  # noqa: E402
    split_coal_tranches,
    split_gas_tranches,
)
from market_sim.data.fuel import (  # noqa: E402
    apply_coal_supply_pricing,
    apply_dual_fuel_pricing,
    apply_ercot_west_netload_gas_shape,
    apply_ercot_zonal_gas_basis,
    apply_hub_basis_overlay,
    apply_miso_zonal_gas_basis,
    apply_nyiso_downstate_ct_gas_basis,
    apply_nyiso_zonal_gas_basis,
    apply_pjm_zonal_gas_basis,
    apply_plant_monthly_fuel_prices,
    coal_passthrough_by_supply,
    dual_fuel_switch_mask,
    ercot_west_oversupply_collapse_freq,
    prb_follower_passthrough_series,
    resolve_fuel_prices,
)
from market_sim.data.renewables import (  # noqa: E402
    hsl_potential_mw,
    inject_offshore_wind_availability,
    load_hsl_hourly,
    load_renewable_profiles,
)
from market_sim.model.commitment import (  # noqa: E402
    apply_commitment_with_coal_pin,
    as_adequacy_commit,
    compute_commitment,
    compute_monthly_markup,
)
from market_sim.model.dispatch import DispatchModel, solve_dispatch  # noqa: E402
from market_sim.pipeline import (  # noqa: E402
    DispatchSpec,
    apply_reserve_coopt,
    build_base_dispatch_kwargs,
)
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    reserve_storage_as_power,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    apply_interchange_injections,
    build_incidence_matrix,
    build_interface_groups,
    get_link_bidirectional_array,
    get_ttc_array,
    wecc_border_carbon_adder,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.eac import (  # noqa: E402
    apply_eac_to_mc,
    apply_negative_renewable_offer_floor,
    compute_eac_dispatch_credits,
)
from market_sim.policy.ira import compute_dispatch_credits  # noqa: E402
from market_sim.results.calibration import (  # noqa: E402
    check_hourly_dispatch_correlation,
)
from market_sim.results.emissions import compute_emissions  # noqa: E402
from market_sim.results.outputs import FleetContext  # noqa: E402

# Model fuel types that make up the EIA-930 "natural gas" telemetry series:
# combined cycle, combustion turbine and gas steam are reported as one fuel.
_GAS_FUEL_TYPES: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st"})

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_calibration")

# Calibration reference written by scripts/build_calibration_reference.py.
REFERENCE_PATH: Path = CALIBRATION_DIR / "calibration_reference.json"

# Fallback measured Henry Hub annual-average spot price ($/MMBtu), used when
# the calibration reference JSON has not yet been generated.
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
_HENRY_HUB_FALLBACK: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}

_MWH_PER_TWH: float = 1.0e6
_TONNES_PER_MT: float = 1.0e6

# Zone-pair identifying each transfer link whose TTC the CLI can override.
# Both legs of the West Texas Export interface and the Panhandle GTC are
# exposed for tuning — these are ERCOT's primary wind-export constraints.
_TTC_LINK_ZONES: dict[str, frozenset[str]] = {
    "ttc_wn": frozenset({"West", "North"}),
    "ttc_wsc": frozenset({"West", "South_Central"}),
    "ttc_pn": frozenset({"Panhandle", "North"}),
}


def _takeorpay_by_plant(fleet, config) -> dict[int, float] | None:
    """Return ``{plant_code: contract_share}`` for coal plants, or ``None``.

    ``None`` (the default) leaves ``campd_tranche_fuel_frac`` on its hardcoded
    100%-sunk must-run behaviour. When ``config.coal_takeorpay_from_data`` is
    set, build the measured EIA-923 Schedule-5 take-or-pay share
    (:func:`fleet.coal_takeorpay_share`) for every coal plant in the fleet that
    has a classifiable Purchase Type; plants without one are omitted and keep
    the default treatment.
    """
    if not getattr(config, "coal_takeorpay_from_data", False):
        return None
    out: dict[int, float] = {}
    for g in fleet:
        if g.fuel_type != "coal":
            continue
        code = int(g.plant_code)
        if code in out:
            continue
        share = coal_takeorpay_share(code)
        if share is not None:
            out[code] = share
    return out


def _load_reference() -> dict:
    """Return the calibration reference dict, or an empty dict if unbuilt."""
    if not REFERENCE_PATH.exists():
        logger.warning(
            "calibration reference %s not found — run "
            "build_calibration_reference.py first; using fallback gas prices",
            REFERENCE_PATH.relative_to(REPO),
        )
        return {}
    return json.loads(REFERENCE_PATH.read_text())


def _henry_hub_actual(reference: dict, year: int) -> float:
    """Return the measured Henry Hub price for ``year`` from the reference."""
    table = reference.get("henry_hub_actual", {})
    if str(year) in table:
        return float(table[str(year)])
    return _HENRY_HUB_FALLBACK[year]


def _deep_merge_offer_curve(
    base: dict[str, dict[str, float]],
    overrides: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Deep-merge ``overrides`` onto the default ``offer_curve_by_group``.

    Each top-level key is a fleet class (CC_REGULAR, CT_PEAKER, ...); the
    nested dict holds the band multipliers (committed, econ_low, econ_high,
    peak, econ_low_share, pct_peaking). Only the bands named in ``overrides``
    are replaced; every unspecified band keeps its calibrated default, so a
    caller can tune one knob on one class without restating the whole curve.
    Unknown classes/bands are passed through unchanged (the dispatch code
    ignores keys it does not consume) so a typo fails loudly downstream
    rather than being silently dropped here.
    """
    merged = {cls: dict(bands) for cls, bands in base.items()}
    for cls, bands in overrides.items():
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve override for {cls!r} must be an object of "
                f"band->multiplier, got {type(bands).__name__}"
            )
        merged.setdefault(cls, {}).update(bands)
    return merged


def _apply_offer_curve_deltas(
    base: dict[str, dict[str, float]],
    deltas: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Return ``base`` with each ``deltas`` value ADDED to the current band.

    Unlike :func:`_deep_merge_offer_curve` (absolute replacement), this nudges
    a band relative to whatever it already is: ``{"CT_PEAKER":{"committed":0.05}}``
    turns a 1.40 committed multiplier into 1.45, and ``-0.05`` into 1.35 — so a
    re-tune does not have to restate the absolute value. The class/band must
    already exist in ``base`` (you can only nudge a band the offer curve
    actually has); an unknown one raises with the valid options listed.
    """
    merged = {cls: dict(bands) for cls, bands in base.items()}
    for cls, bands in deltas.items():
        if cls not in merged:
            raise ValueError(
                f"offer-curve delta for unknown class {cls!r}; valid classes: "
                f"{', '.join(sorted(merged))}"
            )
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve delta for {cls!r} must be an object of "
                f"band->delta, got {type(bands).__name__}"
            )
        for band, delta in bands.items():
            if band not in merged[cls]:
                raise ValueError(
                    f"offer-curve delta for unknown band {cls}.{band!r}; "
                    f"{cls} bands: {', '.join(sorted(merged[cls]))}"
                )
            merged[cls][band] = merged[cls][band] + delta
    return merged


# The core gas classes whose generic band multipliers are ERCOT-lineage and must
# NOT silently cross ISO boundaries (audit C-11/C-13, rule #24). The
# ``*_INTERMEDIATE`` classes are a measured-duty-shape mechanism (not
# ERCOT-residual-fitted) and coal classes route by EIA-923 fuel rank, so both are
# left generic — only these five gas classes are neutralized.
_GENERIC_NEUTRAL_GAS_CLASSES: tuple[str, ...] = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_CHP",
    "CT_PEAKER",
    "ST_GAS",
)


def _neutralize_generic_gas_bands(
    base: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Return ``base`` with the generic gas band MULTIPLIERS set to neutral 1.0.

    Rule #24 / audit C-11/C-13: the generic (non-ERCOT/non-PJM) offer-curve
    fallback must carry neutral bands, so an ISO without an explicit grounded
    value inherits ``1.0`` (offer at the plant's own base heat rate) rather than
    a value fitted on ERCOT's residual. Only the four heat-rate MULTIPLIER bands
    (``committed``, ``econ_low``, ``econ_high``, ``peak``) of the five core gas
    classes are reset; the STRUCTURAL tranche shares (``econ_low_share``,
    ``pct_peaking``) and every other class (coal, ``*_INTERMEDIATE``) are kept.
    Each non-ERCOT/non-PJM ISO then deep-merges its own grounded per-ISO curve on
    top; any band it does not restore stays neutral (a legible, non-inherited
    default), which is the de-leaked state.
    """
    out = {cls: dict(bands) for cls, bands in base.items()}
    for cls in _GENERIC_NEUTRAL_GAS_CLASSES:
        bands = out.get(cls)
        if not bands:
            continue
        for band in ("committed", "econ_low", "econ_high", "peak"):
            if band in bands:
                bands[band] = 1.0
    return out


# Calibrated PJM thermal offer curve (per-class band heat-rate multipliers on
# AHR x delivered fuel price). Price-calibrated multipliers, not literal heat
# rates. COAL_LIGNITE / COAL_PRB are carried for completeness but unused by
# PJM (its coal is bituminous / sub-bituminous / waste -> BIT/SUB/WC).
#
# CC_REGULAR: committed 0.87 (Manual 15 min-load SRMC floor, ERCOT keeper
# run-157 0.998; raised from 0.6624 which cleared overnight PJM LMP → CC
# over-generation miss #1), econ_high 1.50 (steepen upper ramp for miss #2,
# the 95-100% CF pile). CT_PEAKER: committed 1.25, econ_low 1.05 (pjm-59/61
# dispatch fix so CTs price as peakers not baseload; missing from pjm-58
# keeper). See docs/handoffs/pjm-cc-overgen-recommendation-2026-06.md.
_PJM_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 0.87,  # raised from 0.6624: Manual 15 min-load SRMC floor
        "econ_low": 0.92,  # raised from 0.7344: pjm-58 level
        "econ_high": 1.50,  # raised from 0.8928: steepen upper ramp (miss #2)
        "peak": 5.0,  # raised from 1.62: duct-firing scarcity (pjm-61)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CC_CHP": {
        "committed": 0.6624,
        "econ_low": 0.684,
        "econ_high": 0.8208,
        "peak": 1.62,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 0.864,
        "econ_low": 0.864,
        "econ_high": 0.864,
        "peak": 1.008,
        "econ_low_share": 0.50,
    },
    "CT_PEAKER": {
        "committed": 1.25,  # raised from 0.8784: peaker part-load penalty (pjm-59/61)
        "econ_low": 1.05,  # raised from 0.9792: base dispatch above HR (pjm-59/61)
        "econ_high": 1.40,  # from pjm-61 economic ramp
        "peak": 4.0,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,  # pjm-61: wider peaking band
    },
    "ST_GAS": {
        "committed": 0.4752,
        "econ_low": 0.6552,
        "econ_high": 0.90,
        "peak": 3.024,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
    "COAL_LIGNITE": {
        "committed": 0.684,
        "econ_low": 0.8208,
        "econ_high": 0.828,
        "peak": 1.116,
        "econ_low_share": 0.556,
    },
    "COAL_PRB": {
        "committed": 0.684,
        "econ_low": 0.5544,
        "econ_high": 0.8568,
        "peak": 1.0656,
        "econ_low_share": 0.556,
    },
    "COAL_BIT": {
        "committed": 0.648,
        "econ_low": 0.7056,
        "econ_high": 0.8064,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
    "COAL_WC": {
        "committed": 0.612,
        "econ_low": 0.648,
        "econ_high": 0.7344,
        "peak": 0.864,
        "econ_low_share": 0.55,
    },
    "COAL": {
        "committed": 0.648,
        "econ_low": 0.684,
        "econ_high": 0.792,
        "peak": 1.044,
        "econ_low_share": 0.55,
    },
}


# NYISO gas offer curves, grounded in the Potomac Economics NYISO State-of-the-
# Market (SOM) reports and the measured per-plant CAMPD heat rates, NOT fitted to
# the backcast residual. Until now NYISO fell through to the generic non-PJM/non-
# ERCOT branch in offer_curve_by_group{} below, which carried ERCOT-fitted band
# multipliers that were never validated for NYISO — the root cause of the gas-
# class merit-order substitution error (CC_REGULAR under-runs while legacy gas
# steam over-runs). These are merged on top of that branch (_deep_merge_offer_
# curve), so only the named gas classes change; coal/CT_CHP/ST_CHP keep the
# generic defaults. Per-plant committed % and duct-firing peaking % still come
# from CAMPD (cc_committed_per_plant / cc_peaking_per_plant via
# thermal_tranches_NYISO.csv) and supersede the class-wide values here.
#
# Grounding (all band multipliers scale each plant's own measured base heat rate,
# bin_assignments_NYISO.csv Plant_Avg_HR; cap-weighted class HRs: CC_CHP 6.99,
# CC_REGULAR 7.76, CT_CHP 7.58, ST_GAS 10.61, CT_PEAKER 11.95 MMBtu/MWh):
#  - NYISO is a competitive energy market: suppliers offer close to short-run
#    marginal cost (2023 SOM §VI.A "output gap" 0.05% at the mitigation
#    threshold, 1.9% at ref+25%). So the multipliers encode a near-marginal-cost
#    SHAPE around each unit's real heat rate, not a strategic markup. The
#    physically-correct merit order is CC (efficient) < ST_GAS (legacy steam,
#    high HR) < CT_PEAKER.
#  - ST_GAS: 2023 & 2024 SOM Figure 2 / §I.B — "Steam turbine units appear to be
#    the most economically challenged... their high operating costs and physical
#    constraints... usually prevent steam units from earning much energy or
#    reserve revenue, except in Long Island [reliability contracts]." The generic
#    committed 0.81x put the legacy-steam min-load slice (0.81*10.61 = 8.6 eff
#    HR) BELOW the top of CC_REGULAR's econ ramp (1.27*7.76 = 9.9 eff HR), so an
#    inefficient steam unit undercut an efficient CC — physically backwards.
#    Raising committed to 0.97 (min-load eff HR ~= avg, steam part-load HR is no
#    better than full-load) puts steam back above CC across its whole econ range,
#    so it only runs in genuinely high-load hours / on the LI floor, matching the
#    SOM. NOTE the offer SHAPE only works if each plant's *base* heat rate is
#    right: Ravenswood (plant 2500) is a mixed CC+ST facility, and its 1,725 MW
#    ST_GAS row had inherited the 8.8 MMBtu/MWh *facility-blended* heat rate (the
#    CC efficiency leaking into the steam row), so 0.97x8.8 = 8.5 eff HR put the
#    big NYC steam unit BELOW CC's econ ramp (1.12x7.76 = 8.7) and it cleared
#    ahead of idle NYC CC in ~8.5k hr/yr (the 2023 CC_REGULAR -4 TWh / ST_GAS
#    +3.5 TWh merit inversion). Corrected the Ravenswood ST_GAS base HR to 9.5
#    (data.fleet.MIXED_FACILITY_STEAM_HR) — the steam units' own HR recovered by
#    backing the efficient CC out of the 8.8 generation-weighted CC+ST plant
#    blend (CC ~0.6 / steam ~0.15 CF -> steam ~9.5), modestly above the blend and
#    below the older NYC peers (Arthur Kill 11.27, Astoria 11.95). A measured-data
#    correction (CLAUDE.md rule #11: the blended HR was silently masking the
#    inversion), forward-reproducible, not fitted to the price/volume residual.
#  - CC_REGULAR / CC_CHP: the efficient gas workhorses. CC marginal HR is ~flat
#    and ~0.95x average across the bulk of the operating range (CAMPD CC fit,
#    also cited on the ERCOT curve), with the incremental HR rising toward full
#    load as the unit pushes against its rating (the approach to duct firing).
#    The CAMPD CC marginal-HR SRMC *reach* at the top of the econ ramp is
#    ~1.21x base_hr -- the SAME fit ERCOT's keeper uses (committed 0.87 /
#    econ_low 0.92 / econ_high 1.21). So the rising econ ramp now spans
#    econ_low 0.95 -> econ_high 1.21 (run 27 re-level; econ_high was 1.12).
#    WHY 1.12 was wrong: it compressed the upper econ slices BELOW the CAMPD CC
#    marginal HR, pricing the top of each CC's body too cheap. While the old
#    75% CC capacity wall was in place that compression was masked; once run 26
#    removed the wall (cc_nameplate_summer_derate -> full EIA-860 nameplate) the
#    un-walled CC fleet cleared its now-exposed top slices too cheap and mildly
#    over-ran on energy (CC_REGULAR ~+2 TWh/yr) while DEPRESSING the marginal
#    LMP (C3a 2023 -8.9% / 2024 -11.0%). Raising econ_high to the ERCOT/CAMPD
#    1.21 reach prices those marginal slices out, so CC stops over-running and
#    stops setting too-low a clearing price -- a grounded offer-LEVEL
#    calibration (CLAUDE.md rule #1 second step: right structure in run 26,
#    offer level here), grounded in the CAMPD CC marginal heat rate, NOT a
#    re-walled capacity nor a residual-fitted adder (rules #11/#12). econ_low
#    stays 0.95 (already above ERCOT's 0.92; the cheap baseload body is correct
#    -- the miss was only the compressed top). CC_CHP (most efficient, 6.99)
#    stays nudged a touch higher (econ_high 1.24, +0.03 over CC_REGULAR) to trim
#    its small over-run. The duct-firing peak stays a separate inflexible flat
#    tranche (2023 SOM §VI.A: "Some combined cycles offer inflexibly... to
#    manage physical operating constraints on the duct-fired portion"; duct
#    burners are not flexible enough for AGC/10-min reserves).
#  - CT_PEAKER: offers near marginal cost in NYISO's competitive market; the
#    generic committed 1.55 was an ERCOT P1 startup-cost hurdle never validated
#    here that parked the peakers idle. Lowered to 1.35 so peakers pick up the
#    high-load tail (SOM: NYC GTs run for peak/reliability), econ/peak unchanged.
#
# RUN-28 PROBE (rejected, 2026-06-25): re-grounding ALL of CC_REGULAR / CC_CHP /
# ST_GAS committed/econ_low/econ_high to NYISO's OWN CAMPD incremental-HR medians
# (scripts/derive_campd_marginal_hr.py: CC_REGULAR 0.632/0.784/0.925, CC_CHP
# 0.809/0.989/1.103, ST_GAS 0.818/0.825/0.830) was tried to remove the borrowed
# ERCOT reach. It CRATERED C3a mean LMP to -24/-26.5/-23.5% across 2023-25: the
# bare CEMS marginal heat rate is the marginal COST, not the OFFER — it omits the
# competitive offer markup (no-load/start/AS cost recovery + inframarginal rent)
# that NYISO has no offer disclosure to measure, so the borrowed 1.21 reach was
# proxying that real markup. Keeper stays this run-27 curve; the run-28 bundle
# (results/calibration/nyiso_28_native-hr) keeps the rejected curve + finding.
# The steam-side re-level WAS directionally right (it nearly halved the 2024
# ST_GAS under-run), so the run-29 path is a NYISO-grounded markup ON TOP of the
# native marginal HR, not a restored cross-ISO borrow. See the run-28 attestation
# and docs/calibration-best-so-far-nyiso.md.
#
# RUN-32 KEEPER (2026-06-26): the run-29 path executed on ST_GAS only. The legacy
# gas-steam offer is re-levelled to the native steam marginal HR x the CC-grounded
# competitive markup (1.31x): committed 0.97/econ_low 1.10/econ_high 1.45 ->
# 1.05/1.08/1.13 (see the ST_GAS inline comment). CC stays at the run-27 reach
# (the markup that holds the clearing price -- NOT stripped, unlike run-28). HARD
# C1 improves across the board (2023 ST_GAS -1.26 -> -0.01 TWh PASS, CC_REGULAR
# +1.70 -> +0.99 PASS; 2024 ST_GAS -4.14 -> -3.28, CC_REGULAR +2.09 -> +1.74); the
# flat measured band reproduces measured steam VOLUME almost exactly, validating
# the offer level a priori. SOFT C3a regresses to a documented CAVEAT (the keeper-27
# steep ramp was a compensating over-pricing propping up the mid-merit price;
# removing it exposes the ledgered reserve-scarcity tail) -- kept per rule #1.
# Keeper since it is the most structurally faithful NYISO config: measured-grounded
# steam offer + grounded CC reach. See the run-32 attestation.
_NYISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 0.90,
        "econ_low": 0.95,
        # DE-LEAKED (audit C-13, rule #25, B-NYI-1): econ_high was 1.21 — a CAMPD
        # CC marginal-HR reach value grounded on ERCOT's CC analysis and
        # cross-borrowed to NYISO, i.e. a rule-25 cross-ISO leak. It was retained
        # only because removing it craters C3a ≈ −24%, which is a residual
        # justification, not a NYISO-identified value — so it neutralizes to the
        # neutral 1.0 band (CC offers at its own econ heat rate, no borrowed
        # markup). The C3a hole this exposes is an OPEN ROOT CAUSE (rule #1):
        # the real missing mechanism is NYISO scarcity/reserve (RCPF/AS) price
        # formation, NOT a CC energy markup — see GitHub issue #1344. Do NOT
        # re-arm this markup to close C3a (rule #26, rule #1).
        "econ_high": 1.0,
        "peak": 2.25,  # physical F-class duct-burner ratio (not ERCOT-fitted)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CC_CHP": {
        # NYISO's own run-27 CHP curve (+0.03 over CC_REGULAR to trim CHP
        # over-run) — NYISO-identified, not the generic ERCOT fallback (else-arm
        # CC_CHP is 0.92/0.96/1.12). Left as-is; the residual-fit +0.03 is a DOF
        # item for the later NYISO calibration phase.
        "committed": 0.90,
        "econ_low": 0.98,
        "econ_high": 1.24,
        "peak": 2.25,  # physical F-class duct-burner ratio
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        "committed": 1.35,  # NYISO/CAISO-grounded evening-ramp start hurdle
        #   (NYISO/ISO-NE CTs serve the ramp, not the ERCOT 1.55 idle-park).
        # econ bands DE-LEAKED from the ERCOT generic fallback (was econ_low 1.27
        # / econ_high 1.98) to neutral 1.0 (offer at the CT's own base heat rate):
        # NYISO carries no independent CT part-load heat-rate spread yet. OPEN
        # ROOT CAUSE (rule #1): a NYISO-grounded CT econ ramp (CAMPD CT heat-rate
        # spread) is a later disciplined-calibration item — NOT re-tuned here.
        "econ_low": 1.0,
        "econ_high": 1.0,
        # peak DE-LEAKED from the inherited ERCOT 13.15x $5,000-ORDC scarcity wall
        # (audit C-13) to 4.0 — NYISO's energy offer cap is $1,000 ($2,000
        # cost-based under scarcity), NOT ERCOT's $5,000 ORDC. This promotes the
        # NEISO-42 precedent (capped 13.15 -> 4.0 but never promoted). Same cap
        # and reasoning as PJM/CAISO/MISO/NEISO.
        "peak": 4.0,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # CT_CHP: DE-LEAKED from the generic ERCOT-lineage `else` branch (was
    # 1.10/1.20/1.20/1.40) to neutral 1.0 — NYISO carries no independent CT_CHP
    # heat-rate spread yet (later disciplined-calibration item, rule #1).
    "CT_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
    },
    "ST_GAS": {
        # run 32: re-levelled from the ERCOT-shaped rising ramp (0.97/1.10/1.45)
        # to NYISO's OWN measured CAMPD steam marginal HR x a grounded competitive
        # markup. Native steam marginal HR (NY+NJ CAMPD pooled,
        # nyiso_campd_marginal_hr_summary.csv) is committed 0.818 / econ_low 0.830
        # / econ_high 0.828 -- essentially FLAT (legacy steam part-load HR is no
        # better than full-load, matching the 2023/24 SOM). The bare marginal HR is
        # the marginal COST not the OFFER (run-28 finding: it craters C3a), so a
        # competitive markup is applied ON TOP: the CC class's own defensible reach
        # ratio (CC econ_high 1.21 / native CC marginal 0.925 = 1.31x) x the steam
        # native marginal (~0.82-0.83 x 1.31 ~= 1.08), with a thin monotone spread
        # 1.05 -> 1.13 to keep a valid rising offer and a modest scarcity reach
        # below the inflexible peak tranche. Effective HR 11.1-12.0 stays ABOVE CC
        # econ_high 9.4 and BELOW CT_PEAKER 16.1 (merit preserved, no inversion).
        # Recovers the legacy-steam under-run (2023 ST_GAS -1.26 -> -0.01 TWh,
        # near-EXACT -> the flat measured band reproduces measured steam volume,
        # validating the level a priori, not residual-fitted). The C3a depression
        # this exposes is the missing reserve-scarcity tail (ledgered, rule #1).
        "committed": 1.05,
        "econ_low": 1.08,
        "econ_high": 1.13,
        "peak": 4.20,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
}


# CAISO gas offer curves, grounded in the CAISO DMM (Department of Market
# Monitoring) State-of-the-Market reports and the measured per-plant CAMPD heat
# rates, NOT fitted to the price residual (CLAUDE.md rules #1/#11). Until now
# CAISO fell through every per-band ternary to the generic non-PJM/non-ERCOT
# `else` branch in offer_curve_by_group{} below, whose values were "fit to
# Colorado Bend II / Wolf Hollow II" — ERCOT plants — and carried the ERCOT
# CT_PEAKER `peak` 13.15x scarcity wall. That wall encodes ERCOT's $5,000 ORDC
# scarcity, which has no CAISO analogue (CAISO's energy offer cap is the $1,000
# soft cap, raised to $2,000 only with cost verification under extreme
# scarcity), so it inflated the 2023 high-price tail (744 h > $200 vs 21
# actual), while the ERCOT-fitted CC econ band (econ_low 1.06 / econ_high 1.27)
# over-priced the midday CC body (the domestic source of the CA-zone LMP
# over-price diagnosed in DIAGNOSIS-caiso36-body-overprice-domestic-2026-06-28).
# These are merged on top of that generic branch (_deep_merge_offer_curve), so
# only the named GAS classes (CC_REGULAR, CT_PEAKER) change; CC_CHP / CT_CHP /
# ST_GAS / coal keep the generic defaults. Per-plant committed % and duct-firing
# peaking % still come from CAMPD (cc_committed_per_plant / cc_peaking_per_plant
# via thermal_tranches_CAISO.csv) and supersede the class-wide values here.
#
# Grounding (band multipliers scale each plant's own measured base heat rate,
# bin_assignments_CAISO.csv Plant_Avg_HR; cap-weighted class base HRs:
# CC_REGULAR 7.44, CT_PEAKER 10.86 MMBtu/MWh):
#  - CAISO is a structurally competitive energy market (DMM 2023/2024 SOM): the
#    market-power mitigation Default Energy Bid (DEB) for a gas unit is
#    cost-based — gas x measured heat rate + variable O&M + a ~10% competitive
#    adder — so suppliers offer close to short-run marginal cost. The
#    multipliers therefore encode a near-SRMC SHAPE around each unit's real heat
#    rate, NOT a strategic markup or a residual-tuned level.
#  - CC_REGULAR: the efficient gas workhorse and the midday marginal class (the
#    diagnosis shows CA midday needs ~6.5 GW of economic gas_cc whose bid sets
#    the body price). The CAMPD CC marginal-HR fit is ~flat at ~0.95x average
#    across the body, rising to ~1.21x average at the top of the economic range
#    (the approach to duct firing) — the SAME fit ERCOT's and NYISO's keepers
#    use (committed 0.90 / econ_low 0.95 / econ_high 1.21). The generic
#    ERCOT-fitted econ_low 1.06 / econ_high 1.27 priced the CC body ~10% above
#    that measured incremental cost, the domestic driver of the midday over-
#    price; re-grounding to 0.95 -> 1.21 removes that ERCOT level premium. The
#    duct-firing `peak` stays the physical F-class duct-burner multiplier (2.25),
#    NOT capped — capping a real physical band to move price would be an
#    unphysical fit (rule #11).
#  - CT_PEAKER: offers near its DEB cost in CAISO's competitive market. The
#    `peak` band is capped at 4.0 (cap-weighted eff HR ~43, ~$150/MWh at 2023-25
#    gas — a defensible CAISO scarcity offer well inside the $1,000-2,000 soft
#    cap), the SAME cap and reasoning PJM adopted ("an ERCOT-style 13x wall is
#    far too high ... inflating the high-price tail"); it replaces the ERCOT
#    13.15x $5,000-ORDC wall that drove the 2023 > $200 tail. The econ band is
#    re-grounded to the DEB cost-plus-adder shape (econ_low 1.10 ~= HR x 1.1 at
#    the bottom of the range, econ_high 1.50 the rising part-load/hot-day reach)
#    in place of the ERCOT-fitted 1.27 / 1.98. The committed min-load start-cost
#    hurdle is lowered from the ERCOT 1.55 (which parks peakers idle) to 1.35
#    (NYISO-grounded): CAISO's fast-start CTs and aeroderivatives serve the steep
#    net-load evening ramp and should clear on the ramp rather than forcing the
#    CC duct-fire + startup tranches to set the evening price.
_CAISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        # LEVER A (2026-07-04, FINDING-caiso-evening-merit): raised 0.90 -> 1.00.
        #   The committed band is the min-STABLE-load (at/below-LSL) tranche
        #   (derive_campd_marginal_hr.py: "committed" = at/below LSL min-gen),
        #   whose true incremental heat rate is ABOVE the plant average (min-load
        #   is thermally inefficient). Multipliers scale Plant_Avg_HR, so 0.90x
        #   avg priced the min-load block ~$1.2/MWh BELOW true marginal cost AND
        #   below econ_low (0.95) — an INVERTED merit order (min-load block
        #   cheaper than the efficient incremental band). This borrowed
        #   (NYISO-aligned, not CAISO-measured) sub-cost offer emulated
        #   commitment and flooded cheap CC around the clock (+3.2 GW overnight
        #   over-run, LMP pinned ~$42, physically-backwards evening EXPORT to
        #   Malin/Palo Verde). 1.00x avg HR restores committed >= econ_low
        #   ordering and is still CONSERVATIVE vs the true (>avg) min-load HR; any
        #   avoided-startup credit belongs in an explicit UC layer, not the P1
        #   offer (rule #1; DOF ledger E8). econ_low is NOT raised — it is the
        #   measured CAMPD marginal SRMC (below), and lifting it would over-price
        #   incremental energy above marginal cost (reintroducing the caiso-36
        #   midday over-price).
        "committed": 1.00,
        "econ_low": 0.95,  # CAMPD CC flat body marginal HR ~0.95x avg = true
        #   incremental SRMC (generic ERCOT-fit 1.06 over-priced the midday body;
        #   held here — raising to 1.0 would over-price the incremental band).
        "econ_high": 1.21,  # CAMPD CC marginal-HR SRMC reach (ERCOT/NYISO fit;
        #   generic 1.27).
        "peak": 2.25,  # physical F-class duct-burner band, unchanged.
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        "committed": 1.35,  # NYISO-grounded start hurdle; CAISO CTs serve the
        #   evening ramp (generic ERCOT idle-park hurdle was 1.55).
        "econ_low": 1.10,  # DEB cost + ~10% adder (generic ERCOT-fit 1.27).
        "econ_high": 1.50,  # rising part-load/hot-day reach (generic 1.98).
        "peak": 4.0,  # CAISO $1,000-2,000 soft-cap scarcity, capped far below
        #   the ERCOT $5,000-ORDC 13.15x wall (PJM's reasoning/value).
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # CC_CHP / CT_CHP / ST_GAS below are PINNED to the values CAISO previously
    # inherited from the generic ERCOT-lineage `else` branch. They are NOT
    # CAISO-grounded — they are preserved verbatim ONLY so the neutral generic
    # fallback (rule #24, added by the 2026-07 cross-ISO-bands scrub) does not
    # silently change the caiso-51 keeper, which this scrub does not re-solve
    # (scope: MISO/NEISO/NYISO). Re-grounding these on CAISO's own DMM/CAMPD data
    # is a separate, out-of-scope CAISO item (audit §5.1 lists CAISO's tuned
    # surface elsewhere). Making the inheritance explicit here is what lets the
    # shared fallback go neutral without touching CAISO's dispatch.
    "CC_CHP": {
        # LEVER A (2026-07-04): committed 0.92 -> 1.00, same min-load-block
        #   physics as CC_REGULAR above (the borrowed sub-cost committed offer
        #   inverted committed<econ_low and flooded cheap CC). econ_low/econ_high
        #   held (marginal-SRMC / duct band); the steam-host floor
        #   (chp_steam_following) still governs the price-inelastic min-gen.
        "committed": 1.00,
        "econ_low": 0.96,
        "econ_high": 1.12,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 1.10,
        "econ_low": 1.20,
        "econ_high": 1.20,
        "peak": 1.40,
        "econ_low_share": 0.50,
    },
    "ST_GAS": {
        "committed": 0.81,
        "econ_low": 1.05,
        "econ_high": 1.40,
        "peak": 4.20,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
}


# MISO gas offer curves, grounded in the measured per-plant CAMPD heat rates
# (bin_assignments_MISO.csv Plant_Avg_HR_MMBtu_MWh; cap-weighted class HRs:
# CC_CHP 6.76, CC_REGULAR 7.44, ST_GAS 11.27, CT_PEAKER 12.37 MMBtu/MWh) and the
# MISO market structure, NOT fitted to the backcast residual. Until now MISO was
# the only large multi-zone ISO with no branch: it fell through EVERY
# offer_curve_by_group ternary to the generic non-PJM/non-ERCOT/non-NEISO `else`,
# whose band multipliers were fit to ERCOT plants (Colorado Bend II / Wolf Hollow
# II) and never validated for MISO — including the 13.15x ERCOT-CT "peak" wall
# that PJM and CAISO already discarded. These are merged on top of that branch
# (_deep_merge_offer_curve), so ONLY the named gas classes change; coal / CC_CHP /
# CT_CHP / ST_GAS keep the generic defaults (they sit correctly in merit for MISO
# — see below). Per-plant committed % and duct-firing peaking % still come from
# CAMPD (cc_committed_per_plant / cc_peaking_per_plant via thermal_tranches_
# MISO.csv) and supersede the class-wide values here.
#
# Grounding (band multipliers scale each plant's own measured base heat rate):
#  - CC_REGULAR: MISO's entire CC fleet runs intermediate/baseload (thermal_
#    tranches_MISO.csv: all 44 CC_REGULAR plants measure median CF 50-150%, mean
#    ~90% — near-100% CF). The generic curve was fit to ERCOT's duct-fire-heavy
#    2x1 peaker CCs and carries a rising start-cost-amortized econ ramp (econ_low
#    1.06 / econ_high 1.27) that over-prices the upper operating range of an
#    already-committed baseload CC, whose incremental energy is ~flat at ~0.93x
#    its own average heat rate (the measured CAMPD CC shape, negligible routine
#    duct-firing). That over-pricing pushes the CC's upper econ tranches above the
#    clearing price -> the model under-runs the CC fleet (the 2023/2024 gas-CC
#    under-run, ~-23/-20 TWh vs EIA-923). Flatten the econ ramp to the measured
#    near-baseload incremental cost (econ 0.95 -> 1.08, straddling the full-load
#    0.93x and the average 1.0x) while KEEPING the physically-real F-class duct-
#    burner scarcity peak (2.25). This is the same flat curve validated via the
#    cc_intermediate_split CC_INTERMEDIATE cohort routing; promoting it to the
#    MISO CC_REGULAR BASE makes MISO's CC correct even on a non-split run, and
#    renders the split a near-no-op for MISO's all-baseload fleet (it stays
#    available for genuinely MIXED CC duty — a future MISO peaker CC, or another
#    ISO).
#    The committed (min-stable-load) band was separately raised 0.92 -> 1.20 to
#    the measured part-load premium: a CC's min-load $/MWh is ~30-40% above its
#    full-load SRMC (CAMPD part-load shape), so the min-load tranche MUST price
#    above the full-load body. The old 0.92 (6.84 eff HR) sat BELOW econ_low
#    (0.95*7.44 = 7.07) — the inverse of the real part-load curve — an unphysical,
#    artificially-cheap min-load block. Lifting committed to 1.20 (8.93 eff HR)
#    restores the correct part-load ordering (committed > econ_high > econ_low).
#    This is a pure offer-SHAPE faithfulness fix and is METRIC-NEUTRAL: vs the
#    miso22 base (committed 0.92), gmModel CC_REGULAR moves only -1.5/-0.8/-0.9
#    TWh (2023/24/25, right direction) and ST_GAS / CT_PEAKER / coal / prices all
#    move <0.5 TWh and <$0.1/MWh. It does NOT close the ST_GAS under-run
#    (gmModel ST_GAS stays -7.2/-9.5/-8.1 vs EIA-923) — the committed band is a
#    must-run min-load PRICE block whose VOLUME is set by commitment, not by its
#    own offer, so raising its price corrects the merit ORDER without moving
#    volume. 1.20 is capped just under the ST_GAS non-inversion ceiling
#    (9.13/7.44 = 1.227). Merit preserved: CC econ_high 1.08*7.44 = 8.0 and CC
#    committed 1.20*7.44 = 8.93 eff HR both stay below ST_GAS's min-load (generic
#    committed 0.81*11.27 = 9.1) and CT_PEAKER.
#    NOTE the residual CC_REGULAR over-run (+24/+25/+13) and CT_PEAKER under-run
#    (-19.6/-15.1/-16.6) are NOT offer-curve-addressable: CC's excess is in its
#    measured-flat econ body (must not be steepened — rule #11) and CT's deficit
#    is gated by the missing scarcity mechanism (0 model >$200 hours; RDC/ELMP
#    co-optimization is a separate future lever) plus the 2024/2025 import
#    under-run (-17.0/-5.9 vs actual -23.1/-19.0 TWh). Both are flagged as
#    discovered root causes (rules #1/#11), not papered over here.
#  - CT_PEAKER: CAP the peak band well below the inherited 13.15x ERCOT wall.
#    MISO's energy offer cap is ~$1000-2000/MWh (the ELMP shadow price plus the
#    Reserve Demand Curve / RDT scarcity adder), NOT ERCOT's $5000 ORDC, so a
#    13x heat-rate wall is far too high and inflates the high-price tail — the
#    same reasoning PJM used to cap its CT_PEAKER at 4.0. Drop the peak to 4.0
#    (~$1500/MWh at a 12.4 base HR and typical MISO gas), the MISO-cap-consistent
#    ballpark. The committed start-cost hurdle (1.55) and the econ ramp
#    (1.27 -> 1.98) are left at the generic shape (they are not the ERCOT-specific
#    artifact; only the $5000-ORDC peak is). MISO currently shows 0 scarcity
#    (>$200) hours, so this is forward-correctness — removing an inherited tail
#    that would mis-fire in a forecast — not a live price change.
#  - CC_CHP / CT_CHP / ST_GAS: NOT overridden. The generic CC_CHP (econ
#    0.96 -> 1.12) is already flat and the efficient cogen CCs (measured HR 6.76)
#    sit correctly below CC_REGULAR. The generic ST_GAS committed 0.81*11.27 =
#    9.1 eff HR sits ABOVE the new flat CC_REGULAR (max 8.0), so there is no merit
#    inversion for MISO — and MISO's baseload steam is separately handled by the
#    st_gas_intermediate split (ST_GAS_INTERMEDIATE), so the base ST_GAS curve
#    only prices true-peaker steam. Leaving these generic keeps the change tight
#    and grounded (rule #11: merge only the named bands that diverge).
#
# LEVEL sanity-checked against Potomac Economics, "State of the Market Report for
# the MISO Electricity Markets" (the MISO IMM). A worse interchange / energy
# balance from this curve is a discovered bug to root-cause, not a reason to
# refit (rules #1/#11).
_MISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        # Min-stable-load premium: a CC's part-load $/MWh is ~30-40% above its
        # full-load SRMC (measured CAMPD part-load shape), so the committed
        # (min-load) tranche must price ABOVE the full-load body, not below it.
        # Held at 1.20 (run 30): the committed tranche is a merit-order lever,
        # NOT a volume lever — even at 1.38 (tested), the committed band at
        # ~$26/MWh still clears below $32/MWh system price, so CC volume is
        # unchanged while the price lift draws excess imports (-17 TWh energy
        # balance). CC over-dispatch vs CAMPD requires a different mechanism.
        "committed": 1.20,
        "econ_low": 0.95,  # flat baseload incremental (straddles full-load 0.93x)
        "econ_high": 1.08,  # measured near-flat full-load HR, NOT the ERCOT 1.27 ramp
        "peak": 2.25,  # physically-real F-class duct-burner scarcity band (kept)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        # committed / econ bands DE-LEAKED from the ERCOT generic fallback (was
        # committed 1.55 / econ_low 1.27 / econ_high 1.98 — the "generic shape"
        # prior comments retained is exactly the ERCOT else-arm) to neutral 1.0:
        # MISO carries no independent CT part-load heat-rate spread yet. OPEN ROOT
        # CAUSE (rule #1): a MISO-grounded CT committed hurdle + econ ramp (CAMPD
        # CT heat-rate spread, base HR ~12.37) is a later disciplined-calibration
        # item — NOT re-tuned here. Expect CT over-run vs the prior 1.55 hurdle.
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 4.00,  # MISO offer cap ~$1-2k/MWh -> caps the 13.15x ERCOT-ORDC wall
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    # CC_CHP / CT_CHP / ST_GAS: DE-LEAKED from the generic ERCOT-lineage `else`
    # branch to neutral 1.0 multipliers (offer at each unit's own base heat rate),
    # keeping structural tranche shares and the physical F-class CC duct-burner
    # peak (2.25). MISO carries no independent per-class heat-rate spread for
    # these yet; grounding them on MISO CAMPD spreads (CC_CHP base HR ~6.76,
    # ST_GAS ~11.27) is a later disciplined-calibration item (rule #1), not
    # re-tuned here. Base ST_GAS prices only true-peaker steam (baseload steam
    # routes to ST_GAS_INTERMEDIATE, untouched).
    "CC_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 2.25,  # physical F-class duct-burner ratio (not ERCOT-fitted)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
    },
    "ST_GAS": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
    },
}


# NEISO gas offer curve — ISO-NE-grounded gas-class band multipliers, at parity
# with _PJM_OFFER_CURVE / _NYISO_OFFER_CURVE / _CAISO_OFFER_CURVE / _MISO_OFFER_CURVE.
# Deep-merged on top of the generic non-PJM/non-ERCOT branch so only the named
# GAS classes change; coal / *_INTERMEDIATE keep the generic defaults, and the
# per-plant committed/peaking % from NEISO's CAMPD sheet still supersede the
# class-wide values.
#
# Grounding (band multipliers scale each plant's own measured base heat rate,
# bin_assignments_NEISO.csv Plant_Avg_HR; cap-weighted class base HRs:
# CC_REGULAR ~7.2, CC_CHP ~7.0, CT_PEAKER ~12.0, ST_GAS ~10.6 MMBtu/MWh):
#
#  - CC_REGULAR: committed 1.27 — NEISO min-stable-load offer anchored to the
#    measured CAMPD CC heat-rate shape (min-load 40-55% of nameplate runs ~1.30x
#    the fleet-average HR; raising committed to the full-load offer level (=
#    econ_high 1.27) removes the artificially-cheap min-load block the removed
#    net-summer CC "wall" was masking — ISO-NE Market Rule 1 incremental-energy
#    shape, a conservative floor, not residual-fitted). econ_low 1.06 / econ_high
#    1.27 / peak 2.25 (F-class duct-burner mult) carried from the generic curve.
#  - CC_CHP / CT_CHP / ST_GAS: the generic gas-class values, unchanged.
#  - CT_PEAKER: CAP the peak band at 4.0, down from the inherited 13.15x ERCOT
#    scarcity wall. ISO-NE's energy offer cap is $1,000 ($2,000 cost-based under
#    extreme scarcity per Market Rule 1 §III.1.10.1A); the RCPF reserve scarcity
#    adder tops near $1,500-2,000 (FERC Order 831). That is NOT ERCOT's $5,000
#    ORDC. A 13.15x peak wall creates CT offers ~$550/MWh (12 HR × 13.15 × $3.50
#    gas) that NEVER clear in normal operations — effectively parking the entire
#    CT fleet idle except under extreme scarcity the model can't produce without
#    reserve co-optimization. Cap to 4.0 (~$168/MWh eff offer at typical gas), the
#    SAME cap and reasoning PJM/CAISO/MISO adopted ("an ERCOT-style 13x wall is
#    structurally wrong in a $1,000-2,000 offer-cap market"). The committed hurdle
#    is lowered from 1.55 (ERCOT startup-cost idle-park) to 1.35 (matching
#    NYISO/CAISO's grounded start hurdle — ISO-NE CTs serve the evening ramp and
#    cold-snap reliability, per ISO-NE IMM 2023/2024 SOM). The econ ramp
#    (1.27 → 1.98) is left at the generic shape (not the ERCOT-specific artifact;
#    only the $5,000-ORDC peak and idle-park committed are).
_NEISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 1.27,
        # econ band re-anchored (2026-07-03, neiso-45/46/47 probe chain). The
        # generic 1.06->1.27 band was inherited from the ERCOT-shaped curve and
        # expresses the above-SRMC offer component as a HEAT-RATE MULTIPLIER,
        # i.e. proportional to the fuel price. The month/hour decomposition of
        # the 2024 C3b failure showed the signature that parameterization
        # forces: a flat all-hours winter over-shoot (Jan/Feb 2024 +$9-10 at
        # $3.5-7.7 AGT hub gas; model marginal implied HR ~10.5 vs the actual
        # mild-winter margin ~8.2) alongside a summer-evening under-shoot
        # (Jul/Aug 2024 -$10-11 at $1.8 gas, when the same multipliers collapse
        # the whole stack to ~$33). Physics bound: the econ band is the
        # incremental output of an already-committed CC, whose incremental heat
        # rate sits near the plant-average and rises gently toward the duct
        # margin. Level calibration (rule #1 second step — offer-curve tuning
        # AFTER the structure is right): the high-gas winter months make the
        # marginal implied HR directly observable — the actual mild-winter
        # margin ~8.2 MMBtu/MWh lands on the model's marginal winter plant
        # (Salem Harbor, base HR 7.38) at a mid-band of ~1.08x, so the ramp is
        # 1.00 -> 1.15 (the 0.95->1.05 probe, neiso-45, left the winter floor
        # low across the board: C3a 2023 -6.2%). The fuel-price-INVARIANT part
        # of the real offer component (fast-start start/no-load amortization)
        # is priced by --tranche-startup-amortization on the fast-start-capable
        # tranches, not by inflating the HR band.
        "econ_low": 1.00,
        "econ_high": 1.15,
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    # CC_CHP / CT_CHP / ST_GAS: DE-LEAKED from the generic ERCOT-lineage `else`
    # branch to neutral 1.0 multipliers (offer at each unit's own base heat rate),
    # keeping structural tranche shares and the physical F-class CC duct-burner
    # peak (2.25). NEISO carries no independent per-class heat-rate spread for
    # these yet; grounding them on NEISO CAMPD spreads (CC_CHP base HR ~7.0,
    # ST_GAS ~10.6) is a later disciplined-calibration item (rule #1), not
    # re-tuned here.
    "CC_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 2.25,  # physical F-class duct-burner ratio (not ERCOT-fitted)
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_CHP": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.50,
    },
    "CT_PEAKER": {
        "committed": 1.35,  # NYISO/CAISO-grounded start hurdle (ISO-NE CTs serve
        #   evening ramp + cold-snap reliability, not ERCOT idle-park)
        # econ bands DE-LEAKED from the ERCOT generic fallback (was econ_low 1.27
        # / econ_high 1.98) to neutral 1.0 — NEISO carries no independent CT
        # part-load heat-rate spread yet. OPEN ROOT CAUSE (rule #1), not re-tuned.
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 4.0,  # ISO-NE offer cap $1,000-2,000 (not ERCOT $5,000 ORDC)
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    "ST_GAS": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "econ_low_share": 0.500,
        "pct_peaking": 15.0,
    },
}


# MISO round-2 CC_REGULAR / COAL_BIT offer-curve rebalance (deep-merged onto the
# calibrated MISO base curve when --miso-cc-coal-rebalance is set; ISO-gated, so
# only the named bands change and every other class/band keeps its default).
# Structural correction for the conservation-of-energy miss: with imports too low
# the cheap domestic CC_REGULAR and COAL_BIT over-run and price out the
# under-running CT_PEAKER / ST_GAS. The marginal (top-tranche) MWh of a baseload
# CC/coal unit is NOT the cheapest available supply once priced imports and the
# reliability-floored gas-steam/CT are on the bar, so its committed + econ-high
# bands are raised to clear ABOVE the import hurdle (MISO seam reference ~$36;
# the all-MISO LMP sits above the neighbors most hours). An offer-SHAPE
# correction, NOT a residual-tuned adder — validated by the import↑ / CC↓ / coal↓
# / CT↑ / ST↑ response, not by MAE. Base MISO bands: CC_REGULAR committed 0.92 /
# econ_high 1.27; COAL_BIT econ_high 1.10.
_MISO_CC_COAL_REBALANCE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        # Lift the min-load committed tranche off the artificially-cheap 0.92 (a
        # CC's min-stable-load $/MWh is ~30-40% above its full-load SRMC, the
        # measured CAMPD shape) and steepen the econ ramp so the marginal CC MWh
        # clears above the priced-import hurdle and the gas-steam/CT it displaces.
        "committed": 1.00,
        "econ_high": 1.42,
    },
    "COAL_BIT": {
        # Raise the bituminous-coal econ-high so the marginal coal-bit MWh is no
        # longer the cheapest top-of-merit fill (2025 coal 232 vs EIA-923 201 TWh).
        "econ_high": 1.22,
    },
}


def _calibration_config(
    year: int,
    iso: str,
    hours: int,
    gas_price: float,
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    retiree_cems_cap: bool = False,
    ct_mustrun_per_plant: bool = False,
    ct_mustrun_floor_frac: float = 1.0,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
):
    """Build the ScenarioConfig for one calibration year.

    The calibration configuration fixes the structural and policy levers to
    their backcast values: the weather year is the calibration year, the
    EIA-860 vintage capacity ramp is on, the EIA-930 generation-side demand
    is used without a T&D gross-up, gas seasonality is on, and the RPS
    constraint is off. The federal carbon price is zero, which lets the
    state carbon program through: CAISO years charge the measured CARB
    cap-and-trade allowance price, and NYISO/NEISO years the measured RGGI
    auction clearing average (see policy.carbon.state_carbon_price); other
    ISOs see no carbon cost.

    The measured Henry Hub price is applied through ``gas_price_override``
    when that field exists on :class:`ScenarioConfig`; otherwise the run
    falls back to the configured ``gas_price_path`` trajectory.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).

    Returns:
        The calibration :class:`ScenarioConfig`.
    """
    config = ScenarioConfig(
        weather_year=year,
        iso=iso,
        mode="backcast",  # explicit mode signal: historical-actuals
        #   renewable capacity and measured hourly profiles. Never inferred
        #   from gas_price_override.
        hours=hours,
        vintage_capacity_ramp=True,
        td_loss_factor=0.0,  # EIA-930 demand is generation-side
        #   (Demand + Interchange = Net Generation); no gross-up so the grid
        #   demand target equals actual grid net generation and BTM CHP
        #   self-supply stays off-grid. See ScenarioConfig.td_loss_factor.
        gas_seasonality=True,
        carbon_price=0.0,  # no *federal* carbon price in the backcast years;
        #   carbon_price=0 falls through to the state carbon program in
        #   resolve_carbon_price, so CAISO charges the measured CARB
        #   cap-and-trade allowance price and NYISO/NEISO the measured RGGI
        #   auction clearing average (2023-25) on in-state fossil MC.
        #   ERCOT/PJM have no state program and stay at 0.
        rps_enabled=False,
        gas_monthly_actuals=(iso.upper() in ("CAISO", "NYISO", "NEISO")),
        # NYISO prices gas off different pipeline hubs by region (cheap Tenn Z4
        # 200L / Niagara upstate, dearer Iroquois Z2 / Tenn Z6 in the east,
        # Transco Z6 NY in the city), so the east marginal gas is persistently
        # dearer than the west — the structural source of the upstate-cheap /
        # east-dear LMP gradient the ISO-month average flattens. Measured from
        # the NYISO State-of-the-Market reports (data/raw/
        # nyiso_zonal_gas_hub.csv); see fuel.apply_nyiso_zonal_gas_basis.
        nyiso_zonal_gas_basis=(iso.upper() == "NYISO"),
        # ERCOT prices gas off structurally different regional hubs by zone
        # (deeply-discounted Waha in the West/Permian, ~Henry-Hub North/East
        # Texas and Houston Ship Channel, a South-Texas premium), so the flat
        # fleet-wide Waha scalar over-runs DFW/North CCs and under-runs
        # West/Permian and South CCs. Measured per-zone basis from EIA-923
        # Schedule-5 receipts + published Waha/HSC annual averages
        # (data/raw/ercot_zonal_gas_hub.csv), mean-zero anchored so the
        # aggregate gas level is unchanged. DEFAULT-OFF DIAGNOSTIC: enabling it
        # confirms the gas-basis mechanism (shrinks the North CC over-run) but
        # relocates the residual onto West/Permian CT peakers the zonal LP can't
        # trap (see the docstring on ScenarioConfig.ercot_zonal_gas_basis), so
        # it is kept off in the keeper. Gated on the ERCOT_ZONAL_GAS env flag.
        # See market_sim.data.fuel.apply_ercot_zonal_gas_basis.
        ercot_zonal_gas_basis=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_ZONAL_GAS", "").lower() in ("1", "true", "on")
        ),
        # Delivered-gas floor on the zonal basis above: the West/Panhandle Waha
        # basis is a *hub* (wellhead) basis that goes deeply negative, but a power
        # plant pays *delivered* gas (transport + commodity on top) so its discount
        # has a transport-grounded floor. Without it the West/Permian gas units
        # offer ~$0/MWh and run baseload (the CT_PEAKER over-run); the measured TX
        # delivered-to-electric-power level ($2.11/MMBtu, 2024) shows no TX plant
        # paid near $0 delivered. ERCOT_GAS_FLOOR=1 floors the per-zone delivered
        # discount at the cited measured Waha delivered basis (-0.50);
        # ERCOT_GAS_FLOOR_BASIS=<float> overrides the floor depth. ERCOT only, and
        # only meaningful with ERCOT_ZONAL_GAS on. See
        # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
        ercot_gas_delivered_floor_basis=(
            (
                float(os.environ["ERCOT_GAS_FLOOR_BASIS"])
                if os.environ.get("ERCOT_GAS_FLOOR_BASIS")
                else GAS_BASIS_DIFFERENTIAL.get("ERCOT", -0.50)
            )
            if (
                iso.upper() == "ERCOT"
                and (
                    os.environ.get("ERCOT_GAS_FLOOR", "").lower() in ("1", "true", "on")
                    or os.environ.get("ERCOT_GAS_FLOOR_BASIS")
                )
            )
            else None
        ),
        # Measured re-grounding of the floor depth: scale each zone's Waha hub
        # basis by its EIA-923-measured gas SPOT share (only the spot fraction
        # sees the hub collapse; firm-contracted gas is insulated), so the West
        # delivered discount is a measured haircut, not the cited -0.50 scalar.
        # ERCOT_GAS_HAIRCUT=1 enables it; no-op unless the receipt-derived share
        # (scripts/derive_gas_takeorpay.py) is on disk. ERCOT only. See
        # market_sim.data.fuel.apply_ercot_zonal_gas_basis.
        ercot_gas_contract_haircut=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_GAS_HAIRCUT", "").lower() in ("1", "true", "on")
        ),
        # MEASURED per-unit fuel correction: EIA-860 Petroleum-Liquids (DFO)
        # combustion-turbine peakers (e.g. Morgan Creek 3492) sit in the gas
        # CT_PEAKER class on the bin sheet and otherwise burn cheap Waha gas at
        # baseload. ERCOT_OIL_PRIMARY=1 reprices their gas_ct tranches on
        # distillate (OIL_PRICE_PER_MMBTU), keeping their CT_PEAKER group — a
        # structural data-correctness fix from the EIA-860 energy source, not a
        # residual adder. See market_sim.data.fleet.oil_primary_bin_plants.
        oil_primary_bin_fuel=(
            os.environ.get("ERCOT_OIL_PRIMARY", "").lower() in ("1", "true", "on")
        ),
        # STRUCTURAL net-load-indexed West/Panhandle Waha gas basis: the Waha hub
        # collapses negative at low demand and firms at high demand, so the basis
        # is indexed to system net-load (load - wind - solar) instead of a flat
        # annual scalar. A West peaker (burns only in high-net-load scarcity
        # hours) then sees firm Waha and idles; a West CC (burns all hours) sees
        # the blended-cheap annual mean and stays baseload — the peaker/CC split
        # falls out of WHEN each runs, not a chosen floor. Mean-zero so the
        # measured annual Waha basis is preserved. ERCOT_WEST_NETLOAD_GAS=1 enables
        # it (no-op unless ERCOT_ZONAL_GAS is also on, ERCOT only);
        # ERCOT_WEST_GAS_FIRM_BASIS=<float> overrides the firm (high-demand) Waha
        # delivered basis the top net-load hours reach (default the cited normal
        # Waha discount). See market_sim.data.fuel.apply_ercot_west_netload_gas_shape.
        ercot_west_netload_gas_shape=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_WEST_NETLOAD_GAS", "").lower()
            in ("1", "true", "on")
        ),
        ercot_west_gas_firm_basis=(
            float(os.environ["ERCOT_WEST_GAS_FIRM_BASIS"])
            if os.environ.get("ERCOT_WEST_GAS_FIRM_BASIS")
            else None
        ),
        # Diagnostic override of the measured Waha negative-day frequency that
        # splits the two-regime step (default: per-year neg_day_freq from the
        # zonal-gas CSV). Probe-only — never set to chase the CT residual.
        ercot_west_gas_collapse_freq=(
            float(os.environ["ERCOT_WEST_GAS_COLLAPSE_FREQ"])
            if os.environ.get("ERCOT_WEST_GAS_COLLAPSE_FREQ")
            else None
        ),
        # ENDOGENOUS collapse frequency (gap G6): derive the two-regime split from
        # forecast West/Panhandle oversupply (VRE > local load + export TTC)
        # instead of the measured neg_day_freq, closing the last measured input of
        # the West net-load gas shape. ERCOT_WEST_ENDOGENOUS_COLLAPSE=1 enables it
        # (no-op unless ERCOT_WEST_NETLOAD_GAS is also on, ERCOT only); the
        # measured neg_day_freq stays logged as the backcast realization to
        # validate against. See fuel.ercot_west_oversupply_collapse_freq.
        ercot_west_gas_endogenous_collapse=(
            iso.upper() == "ERCOT"
            and os.environ.get("ERCOT_WEST_ENDOGENOUS_COLLAPSE", "").lower()
            in ("1", "true", "on")
        ),
        # Burner-tip delivered floor for the collapse regime (kills the cheap-hour
        # magnet that pulls low-HR West CTs into low-demand hours). Physical
        # transport-bound input; default off keeps the generic gas floor.
        ercot_west_gas_delivered_floor=(
            float(os.environ["ERCOT_WEST_GAS_DELIVERED_FLOOR"])
            if os.environ.get("ERCOT_WEST_GAS_DELIVERED_FLOOR")
            else None
        ),
        # Daily Henry Hub within-month shape on top of the measured monthly
        # level: physics-input correctness (the merit order sees the real
        # day-to-day gas swing), mean-preserving so the annual mix is
        # unchanged. On wherever the monthly-actuals level is.
        gas_daily_shape=(iso.upper() in ("CAISO", "NYISO", "NEISO")),
        #   Default-on: the +1.20 SoCal basis seed misses the measured
        #   delivered-gas reality badly in stressed years (EIA-923 implied
        #   basis +7.06 in 2023 — Jan-23 delivered $38.7/MMBtu — +2.26 in
        #   2024, +1.12 in 2025), so CAISO backcasts price gas at the
        #   measured ISO-month series. NYISO is the same story (P7): the
        #   flat +0.55 basis seed misses the Transco Z6 winter blowout the
        #   measured 923 series carries (Jan-2023 delivered $10.02/MMBtu vs
        #   HH $3.27; Dec-2025 $8.20), so NYISO backcasts price gas at the
        #   measured ISO-month series too. NEISO default-on for the same
        #   reason (the +1.10 seed is a normal-year scalar), though its
        #   ISO-month 923 series rests on two reporting plants — the AGT hub
        #   overlay below supersedes it in covered months. PJM keeps the
        #   --gas-monthly-actuals flag (its keeper runs pass it explicitly);
        #   ERCOT stays on annual + shape (E1).
        gas_hub_basis_overlay=(iso.upper() in ("NEISO", "CAISO")),
        #   Doc-08 NEISO design decision 1: the marginal gas unit prices off
        #   its constrained trading hub's spot (the opportunity cost of gas in
        #   hand is the spot price it could be resold at), NOT the contract-
        #   laden plant-average EIA-923 delivered cost. The overlay replaces
        #   the gas price with HH-month + the measured hub basis in covered
        #   months (data/raw/gas_basis_by_iso_month.csv).
        #     - NEISO: Algonquin Citygate, whose Dec-Feb basis blows out to
        #       +$4-13/MMBtu (measured ISO-NE MA gas index 2023-2025) — THE
        #       ISO-NE winter price driver and the dual-fuel switch trigger (P13).
        #     - CAISO (caiso 38): the SoCal / PG&E Citygate (EIA N3050CA3
        #       citygate - Henry Hub). The default ISO-month EIA-923 series for
        #       CAISO is volume-weighted across only ~7 reporting plants
        #       (Gateway/Colusa/Lodi PG&E + SDGE Palomar — NorCal/SDGE-skewed),
        #       running ~$0.6/MMBtu above the full-census CA electric-power
        #       delivered gas (EIA N3045CA3 2024 = $3.98/Mcf = $3.84/MMBtu) and
        #       missing the cheap SoCal-border gas the SP15-dominated marginal
        #       CC actually burns (SoCal border fell to a discount to Henry Hub
        #       in summer 2024). The citygate overlay is the measured CA trading
        #       hub the marginal CC prices off — captures both the Jan-2023
        #       western gas crisis (+$24/MMBtu basis) and the summer-2024 SoCal
        #       discount — and supersedes the skewed 7-plant sample (rule #11:
        #       prefer accurate measured data; reconcile a misaligned sample to
        #       the representative hub). NYISO's Transco Z6 leg is still
        #       unsourced, so it keeps the ISO-month 923 series.
        gas_hub_basis_daily=False,
        #   Daily resolution for the AGT overlay (opt in with
        #   --gas-hub-basis-daily). It replaces the flat monthly hub price with a
        #   MEASURED daily series — measured Henry Hub daily + measured Algonquin
        #   Citygate daily spot prints (EIA Weekly Update), Transco Z6 NY daily
        #   basis as the sparse-print shape fallback — MEAN-PRESERVING to the
        #   measured monthly basis, so the annual gas burn and fuel mix are
        #   unchanged and only the within-month winter shape is added. (The old
        #   demand^AGT_DAILY_BASIS_CONVEXITY exponent, which WAS fitted to the oil
        #   burn, was RETIRED 2026-06; the daily leg is now all measured gas-market
        #   data — forward-reproducible and condition-responsive, CLAUDE.md #10.)
        #   The cold-day spikes it builds trip the physical dual-fuel gas->oil
        #   switch, so it is what restores the measured ~1.5 TWh winter oil burn
        #   (and trims the gas the flat monthly overlay leaves over-counted); the
        #   NEISO keepers run it (neiso-33 onward). See
        #   market_sim.data.fuel.iso_hub_daily_gas_prices and
        #   docs/multi-iso/neiso-data-audit.md.
        commitment_enabled=commitment_enabled,  # P1-only by default: the
        #   3-tranche, no-Pmin bin structure dispatches correctly without the
        #   P2 screen. Opt in with --commitment to add the unit-commitment pass.
        commitment_screen_coal=commitment_screen_coal,
        wefor_multiplier=0.7,  # lighten thermal forced-outage rates ~30%
        #   (shape preserved) so coal can hold its shoulder-month output
        #   rather than being availability-capped in spring/autumn.
        coal_prb_passthrough=coal_prb_passthrough,  # default 1.0 = OFF (it is
        #   gas-price fragile; coal level set by the must-run floor). Set via
        #   --coal-prb-passthrough to re-test the price-taking discount.
        coal_lignite_mustrun_override=coal_lignite_mustrun,
        coal_prb_mustrun_override=coal_prb_mustrun,
        outage_source=outage_source,  # backcast pins actual coal/CC outages;
        #   "statistical" reverts to the WEFOR/POF availability model.
        caiso_gas_commitment_floor=False,  # Step-1 overhaul: DEFAULT OFF. The
        #   measured-NG:NG midday slab pinned the gas fleet to 0.80 x its measured
        #   EIA-930 output (a measured-OUTCOME overlay, None for forecast years) —
        #   it held CC_REGULAR ~2x above the real midday duck-belly and
        #   manufactured the $0 midday price by forcing gas LONG, failing CLAUDE.md
        #   #1/#11 (docs/caiso-lever-audit-2026-06.md, Lever A). Replaced by the
        #   forward-derivable RA must-offer COMMITMENT below (caiso_ra_mustoffer):
        #   units online at min-load, free to dispatch down to it. The inject fn
        #   is kept (transmission.inject_caiso_gas_commitment_floor) and re-armable
        #   via --caiso-gas-commitment-floor for the baseline A/B. Other ISOs were
        #   already off (byte-identical).
        caiso_gas_floor_frac=(0.80 if iso.upper() == "CAISO" else 1.0),  # 0.80 =
        #   EIA-923 gas / EIA-930 NG: NG, stripping the ~21% geo+bio the CISO
        #   NG: NG silently absorbs (CISO reports neither) — targets the true
        #   must-offer gas without padding the mix. Only used when the (now
        #   default-off) caiso_gas_commitment_floor is re-armed.
        caiso_ra_mustoffer=(iso.upper() == "CAISO"),  # CAISO Step-1 default-ON:
        #   the forward-derivable RA must-offer COMMITMENT replacing the measured
        #   gas slab above. Through the P2 pass it holds each merchant gas CC/CT
        #   unit that the economic P1 dispatch runs before AND after a midday idle
        #   gap shorter than its physical min-down time at min-load across the gap
        #   (it cannot cycle off and restart for the evening ramp). Detected from
        #   the model's own run pattern + min-down (model.commitment.
        #   caiso_ra_mustoffer_min_gen) — no measured-outcome pin. The LP
        #   dispatches economically above it, so it only binds when oversupply
        #   would drive a committed unit cold; the midday ~$0 must come from real
        #   oversupply (Lever D), not the floor. Other ISOs stay off (byte-
        #   identical). Toggle with --no-caiso-ra-mustoffer.
        caiso_ra_min_load_frac=0.26,  # min stable load of a committed gas unit
        #   (fraction of available capacity) for the RA bridge above. Grounded in
        #   the CAMPD/CEMS-measured CAISO combined-cycle minimum stable load
        #   (P5 of net CF over online hours, scripts/derive_thermal_tranches.py;
        #   data/raw/_processed-legacy/thermal_tranches_CAISO.csv committed_pct):
        #   capacity-weighted 0.259 over the 23-plant, 12.7 GW CA CC fleet
        #   (range 0.10-0.63, median 0.25). Supersedes the generic 0.40 NREL/
        #   Master-File textbook turn-down (~14pp too high for this fleet) per
        #   CLAUDE.md #11 — a measured, forward-reproducible physical limit that
        #   responds to fleet composition, NOT a price/volume fit. The flat
        #   fraction multiplies each tranche row's pmax, so it sums to ~0.26 of
        #   plant pmax across a plant's tranches.
        reliability_floor=(
            iso.upper() in ("ERCOT", "CAISO", "NYISO", "NEISO", "MISO")
        ),  # Registry-driven temperature/net-load reliability floor: ON for the
        #   five calibrated ISOs. Every enabled (zone, class, driver) limb in
        #   RELIABILITY_FLOOR_REGISTRY[iso] (seeded from the derived
        #   reliability_floor_coeffs_<ISO>.csv) is applied by the single engine.
        #   The registry is empty until Phase 2 fills the coefficient CSVs, so
        #   this is a no-op today; per-limb tuning is via
        #   reliability_floor_overrides. New ISOs need ONLY this flag + a registry
        #   row + a weather file.
        neiso_oil_burn_budget=(iso.upper() == "NEISO"),  # NEISO keeper
        #   default-ON: inventory-limited oil-burn monthly budget. Oil/dual-fuel
        #   peakers ration limited on-site distillate over multi-day cold snaps;
        #   the LP shadow price when the budget binds IS the scarcity rent that
        #   lifts the cleared LMP above the flat dual-fuel oil-parity cap (~$258)
        #   and produces >$300 hours endogenously. Budget from measured EIA-923
        #   Schedule 5 monthly Petroleum receipts (MMBtu -> MWh); a reproducible
        #   physical deliverability input (CLAUDE.md #10). NEISO-only, no-op for
        #   other ISOs (byte-identical).
        ct_netload_drag=(iso.upper() == "CAISO"),  # CAISO keeper default-ON: the
        #   forward-native CT_PEAKER reliability-drag floor that REPLACES the flat
        #   TMAX floor above (audit Lever B). Same mechanism validated on ERCOT —
        #   a min-gen floor clip(slope*netGW + intercept, 0, cap) x available
        #   CT_PEAKER capacity gated to the afternoon-evening ramp window — but
        #   keyed to system NET-LOAD (load - wind - solar) instead of TMAX, so it
        #   RISES with the duck-curve neck and naturally PEAKS in the evening ramp
        #   (h18-21) rather than holding a flat rectangle. Both the trigger
        #   (net-load) and the magnitude (physical min-gen) are forward-derivable
        #   and condition-responsive, admissible in backcast AND forecast (#10/#11)
        #   — explicitly NOT the measured-actuals ct_mustrun_per_plant crutch. See
        #   fleet.apply_ct_netload_drag_floor. Other ISOs use the CLI flag.
        #   CAISO-specific curve coefficients (do NOT reuse ERCOT's 0.00703 /
        #   -0.1427 / 0.47): regressed from measured CAMPD CT_PEAKER evening
        #   (h15-22 local-std) capacity factor on EIA-930 CISO net-load, 2023-2025
        #   (scripts/derive_caiso_ct_reliability_floor.py). Non-CAISO ISOs fall
        #   back to the ScenarioConfig ERCOT defaults (byte-identical).
        ct_drag_slope_per_gw=(0.00901 if iso.upper() == "CAISO" else 0.00703),
        ct_drag_intercept=(-0.1124 if iso.upper() == "CAISO" else -0.1427),
        ct_drag_cap=(0.36 if iso.upper() == "CAISO" else 0.47),
        negative_renewable_offers=(iso.upper() == "CAISO"),  # CAISO keeper
        #   default-ON: CA solar/wind bid below $0 (RPS/REC/PTC keep-running
        #   value) in oversupply, so the curtailable renewable tier sets a sub-$0
        #   marginal price once the model is long past the $0 export sink — the
        #   negative midday tail. Byte-identical when not binding (current floor
        #   frac reaches $0, not yet negative; bites with export shaping / a
        #   higher floor). See policy.eac.apply_negative_renewable_offer_floor
        #   and results/calibration/NEGRENEW-caiso-findings.md.
        caiso_solar_deliverability=(iso.upper() == "CAISO"),  # CAISO Lever-D
        #   default-ON: re-curtail the uncurtailed HSL solar potential for the
        #   local / sub-area congestion the reduced 3-zone topology can't see
        #   (~70% of real CAISO curtailment). Caps the per-zone solar CF upper
        #   bound at clip(1 − k × solar_frac, floor, 1) — the solar analogue of
        #   the accepted WECC corridor ATC derate, driven by the FORWARD solar-
        #   penetration signal so the curtailed VOLUME emerges per-year from that
        #   year's own build, not a pin to actuals (CLAUDE.md #1/#11). See
        #   transmission.caiso_solar_deliverability_derate and docs/caiso-lever-
        #   audit-2026-06.md (Lever D). Other ISOs stay off (byte-identical);
        #   --no-caiso-solar-deliverability forces it off (the over-run baseline).
        caiso_solar_endogenous_spill=(iso.upper() == "CAISO"),  # CAISO midday
        #   price fix: skip the pre-LP solar CF derate and pass the full solar
        #   potential to the LP. The LP endogenously curtails in oversupply hours
        #   (solar not fully dispatched → solar marginal → dual = solar_mc ≈ $0
        #   or negative via the keep-running value). Overrides the pre-LP CF
        #   derate from caiso_solar_deliverability while leaving the flag on for
        #   the derate profile computation (used in diagnostics/logging).
        storage_vintage_ramp=(iso.upper() in ("CAISO", "ERCOT", "NEISO")),  # CAISO,
        #   ERCOT and NEISO commissioned batteries mid-backcast (CAISO 3.0 GW
        #   in 2023 + 3.6 GW in 2024; ERCOT ramped ~3.5 -> 6.5 -> 10 GW across
        #   2023-25; NEISO's grid-battery fleet stepped up across 2023-25 as its
        #   EIA-860 COD months landed), so a flat year-end fleet overstates
        #   spring/summer battery capability — measured ERCOT model power
        #   3.9/8.1/13.7 GW vs reality ~3.5/6.5/10. The dispatch caps now ramp
        #   month-by-month from each unit's COD (EIA-860 Operating Month/Year),
        #   and out again on its Planned Retirement Month, for all three. PJM
        #   stays flat until its own recalibration pass. The --storage-vintage-
        #   ramp CLI flag can force it on for any other ISO.
        nearby_fuel_price_fallback=(iso.upper() != "ERCOT"),  # merchant-heavy
        #   ISOs (PJM) have many plants that file no EIA-923 delivered cost;
        #   fill those months from state/zone neighbours before the Henry Hub
        #   curve. Off for ERCOT, whose plants overwhelmingly report.
        plant_level_fleet=(iso.upper() != "ERCOT"),  # non-ERCOT ISOs run the
        #   per-plant EIA-860 fleet (no efficiency-bin aggregation) so the
        #   per-plant fuel cost and CAMPD outage overlay bind to real plants.
        #   ERCOT builds its fleet from CAMPD bins, so this path is unused.
        coal_plant_monthly_pricing=True,  # plant-specific EIA-923 monthly coal
        #   cost where reported (Fayette/San Miguel/J K Spruce); the rest fall
        #   back to the flat lignite/PRB average.
        coal_takeorpay_from_data=(iso.upper() == "MISO"),  # MISO is split-fleet
        #   (not in CAMPD_BINNING_ISOS), so its coal take-or-pay depth comes from
        #   split_coal_tranches, not offer_curve_by_group. Replace the uniform
        #   assumed 100%-sunk first tranche with each plant's MEASURED EIA-923
        #   Schedule-5 contracted share (coal_takeorpay_MISO.csv; CLAUDE.md
        #   #11/#12 — measured > estimate, forward-reproducible). The measured
        #   data shows MISO coal is ~97% contract (tonnage-wtd) — MORE take-or-
        #   pay than ERCOT (~71%), refuting the "market-bought, less depth"
        #   premise: the deep sunk tranche is correct for MISO, so coal offers
        #   are not the LMP/seam lever. Only the few spot-heavy plants (e.g.
        #   1167 S:100%, 6213 S:47%) bid their first tranche fuller. ERCOT and
        #   the CAMPD-binned ISOs are untouched (flag off).
        coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,  # gas-keyed
        #   PRB passthrough when set; else the flat coal_prb_passthrough.
        coal_mustrun_per_plant=coal_mustrun_per_plant,  # per-plant CAMPD coal
        #   must-run floors when set; else the uniform lignite/PRB overrides.
        retiree_cems_cap=retiree_cems_cap,  # cap within-window retirees to their
        #   measured monthly CAMPD CEMS envelope (backcast) when set.
        ct_mustrun_per_plant=ct_mustrun_per_plant,  # per-plant EIA-923 CT_PEAKER
        #   reliability must-run floor (WEFOR/POF exempt) when set.
        ct_mustrun_floor_frac=ct_mustrun_floor_frac,
        coal_drop_pof=coal_drop_pof,  # drop statistical POF on coal (planned
        #   maintenance now comes from the historic outage overlay).
        coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,  # separate
        #   follower-tier PRB sigmoid for low-must-run load-followers.
        gas_st_startup_spread=True,  # amortize ST_GAS startup over the whole
        #   May-Sep season (one seasonal start), not per calendar month.
        # CC and ST_GAS supply curves now come from the unified offer curve
        # below (offer_curve_by_group), so their legacy override triples are
        # left unset. CT_CHP keeps its legacy override (not in the offer curve).
        cc_committed_per_plant=True,  # ground each CC_REGULAR committed % in
        #   CAMPD-observed minimum stable load (fleet.CC_REGULAR_COMMITTED_PCT_
        #   BY_PLANT) instead of the coarse assumed CSV Pct_Committed.
        cc_peaking_per_plant=True,  # the four F-class(late) 2x1 CCs (CBII,
        #   WH2, Rayburn, Temple) move the duct-burner peak band start to 85%
        #   (pct_peaking 15) so the expensive band bites earlier and they back
        #   down out of the 80-90% CF range (fleet.CC_REGULAR_PEAKING_PCT_BY_PLANT).
        cc_duct_peaking=(iso.upper() == "PJM"),  # per-plant EIA-860
        #   duct-burner peaking shares for CC_REGULAR/CC_CHP: duct-fired
        #   plants (65 of 84 PJM CCs, ~50 GW) get their nameplate-vs-summer
        #   capability gap as the peak band, the 19 non-duct plants (~10 GW)
        #   get 0 — replacing the class-uniform pct_peaking 8.0 that handed
        #   every CC the same phantom duct band and stacked the fleet at one
        #   72% CF mass point (fleet.cc_duct_peaking_pct). ERCOT keeps its
        #   CAMPD-fitted class curve + hand-set per-plant map.
        cc_duct_peaking_cap_pct=(8.0 if iso.upper() == "PJM" else None),  # cap
        #   the per-plant duct band at the F-class supplementary-firing physical
        #   max. The raw nameplate-vs-net-summer gap folds the ambient summer
        #   derate into the duct band (median 6.6%, but up to 28% for high-derate
        #   plants), oversizing it and dropping the price wall to ~76% of
        #   nameplate (Guernsey 13% gap). Capping at 8% keeps the per-plant duct
        #   flag (non-duct CCs still 0) but positions the wall at the real ~92%
        #   duct-firing point. ERCOT uses a flat class pct_peaking (no cap).
        cc_nameplate_summer_derate=(
            iso.upper() in ("PJM", "NYISO", "NEISO", "CAISO")
        ),  # CC_REGULAR/CC_CHP carry full EIA-860 nameplate in the LP and are
        #   derated to the measured net-summer rating in summer only (the correct
        #   seasonal shape: full cold-weather capability in winter, ambient-
        #   derated in summer). Replaces pinning the LP capacity at net-summer
        #   year-round (which under-modelled winter AND, with the flat 10%
        #   _SUMMER_CLASS_DERATE on top, derated summer twice) with the per-plant
        #   measured derate (fleet.cc_summer_capacity). In backcast the
        #   statistical WEFOR/POF/age derate are also dropped for CC — the CAMPD
        #   overlay already supplies the real outages. The duct-firing peak band
        #   then sits at the top of nameplate (its physical location) instead of
        #   inside a net-summer-capped range. ERCOT (CAMPD-bin nameplate) and
        #   CAISO/MISO/SPP keep their prior behaviour. Wired for the winter-
        #   fidelity CC ISOs (PJM first; NYISO/NEISO share the per-plant path).
        ct_committed_hr_override=1.1,  # CT_CHP supply curve above its must-run
        ct_econ_hr_override=1.2,  # BTM + steam-following floor; raised in
        ct_peak_hr_override=1.4,  # run9 (CT_CHP was running too much). NOTE:
        #   these are INERT for CT_CHP now — its offer is the offer_curve_by_group
        #   ["CT_CHP"] curve below (the CAISO EOR power-only-HR multipliers).
        # Unified thermal offer curve (operator-supplied band multipliers on
        # AHR x fuel_price; VOM constant across bands). The economic block is a
        # rising ramp from econ_low to econ_high (its slope set by those two
        # endpoints); the duct-firing peak is a separate band above it. CC peak
        # is a tweakable "peak" key (2.25 = the F-class duct-burner multiplier,
        # the modal CC class) instead of the per-turbine-class default, so it
        # can be tuned like every other group's peak. Gas Steam committed kept
        # at the current 0.65x reliability
        # value (per operator); CC and Coal keep their CSV peaking %, while
        # Gas CT -> 7% and Gas Steam -> 15%.
        offer_curve_by_group={
            # CC offer curve fit to Colorado Bend II / Wolf Hollow II observed
            # CAMPD heat-rate curves: marginal HR ~0.95x avg and flat across
            # the operating range, negligible duct-firing. committed/econ are a
            # flat cheap band; peak 2.25 = F-class duct-burner mult (tweakable);
            # pct_peaking 8% = observed duct-fire headroom. committed % per-plant
            # grounded (cc_committed_per_plant).
            # PJM CC econ raised moderately (econ_low 1.06->1.20, econ_high
            # 1.27->1.49) to trim a residual CC_REGULAR overrun. The bulk of
            # the gas-level correction is done by the EIA-923-derived gas basis
            # (+0.67, constants.GAS_BASIS_DIFFERENTIAL) + per-plant gas pricing,
            # not the offer curve; this only rebalances the CC-vs-CT split that
            # economic dispatch (no commitment) leaves CC-heavy. ERCOT keeps the
            # fitted values.
            # ERCOT econ bands fold in the run57 baseline (econ_low 1.06->1.16,
            # econ_high 1.27->1.41) so a no-tweak ERCOT run reproduces run57 and
            # workflow tweaks are +/- relative to it. PJM / other ISOs unchanged.
            "CC_REGULAR": {
                # Generic CC_REGULAR min-stable-load committed band. NEISO's
                # ISO-specific committed lift (1.27, anchored to its measured
                # CAMPD CC heat-rate shape — min-load ~1.30x the fleet-average HR,
                # removing the artificially-cheap min-load block the removed
                # net-summer CC "wall" was masking) now lives in _NEISO_OFFER_CURVE
                # and is deep-merged on top below, so this stays the generic 0.92.
                "committed": 0.92,
                "econ_low": 1.20
                if iso == "PJM"
                else (1.16 if iso == "ERCOT" else 1.06),
                "econ_high": 1.49
                if iso == "PJM"
                else (1.41 if iso == "ERCOT" else 1.27),
                "peak": 2.25,
                "econ_low_share": 0.50,
                "pct_peaking": 8.0,
            },
            # Flatter curve for the measured baseload-duty MISO CC cohort
            # (fleet.cc_intermediate_plants, median CF >= threshold), routed here
            # only when cc_intermediate_split is set (--cc-intermediate-split;
            # default OFF, so every prior keeper / other ISO is byte-identical and
            # the CC_REGULAR curve above is untouched). MISO's entire CC fleet runs
            # intermediate/baseload (median CF 50-150%, mean ~90%), but the
            # CC_REGULAR curve was fit to ERCOT's duct-fire-heavy 2x1 peaker CCs:
            # its rising start-cost-amortized econ ramp (econ_high 1.27) over-prices
            # the upper operating range of an already-committed baseload CC, whose
            # incremental energy is near its flat full-load heat rate (~0.93x its
            # own average, the documented CC measured shape), so the upper econ
            # tranches sit above the clearing price and the model under-runs the CC
            # fleet (the 2023/2024 gas-CC under-run, -24 to -28 TWh vs EIA-923).
            # This flattens the econ ramp to that measured near-baseload
            # incremental cost (econ 0.95->1.08, straddling the full-load 0.93x and
            # average 1.0x) while KEEPING the physically-real F-class duct-burner
            # peak (2.25) — only the operating-range ramp is corrected, never the
            # duct-fire peak (which would be an unphysical fit to volume; rule #11).
            # The committed band stays 0.92 (the cheap min-stable-load base) and
            # the peaking band stays per-plant via cc_peaking_per_plant. Mirrors
            # ST_GAS_INTERMEDIATE / CT_INTERMEDIATE.
            "CC_INTERMEDIATE": {
                "committed": 0.92,
                "econ_low": 0.95,
                "econ_high": 1.08,
                "peak": 2.25,
                "econ_low_share": 0.50,
                "pct_peaking": 8.0,
            },
            "CC_CHP": {
                "committed": 0.92,
                "econ_low": 0.95 if iso == "PJM" else 0.96,
                "econ_high": 1.14 if iso == "PJM" else 1.12,
                "peak": 2.25,
                "econ_low_share": 0.50,
                "pct_peaking": 8.0,
            },
            # CT_CHP cogens: previously driven by the legacy ct_*_hr_override
            # triple (committed 1.10 / econ 1.20 / peak 1.40). Now expressed as
            # an offer curve so the econ ramp and peak are tweakable like every
            # other group. econ_low == econ_high keeps the default a flat 1.20
            # economic block (no dispatch change vs the old single econ value);
            # pull them apart to create a slope. Peaking % stays the CSV value
            # (no pct_peaking key). The ct_*_hr_override fields above are now
            # inert for CT_CHP.
            # NOTE (CAISO CT_CHP — EOR cogen over-dispatch, FIXED at the fleet
            # heat-rate layer, not here): the CAISO CT_CHP fleet's three big
            # Kern-County enhanced-oil-recovery cogens (Kern River 10496,
            # Sycamore 50134, Midway Sunset 52169) report a steam-credited
            # (artificially efficient ~5-6 MMBtu/MWh) EIA-923 heat rate, so this
            # offer curve's 1.10 committed multiplier priced them as cheap
            # baseload and the LP ran the three flat at ~88% CF (3.7 TWh in 2024)
            # vs ~0.8 measured. The fix is the POWER-ONLY heat-rate correction in
            # fleet._correct_caiso_chp_steam_credit_hr, which
            # lifts those three units to the simple-cycle band (~9-11) so they
            # clear on price like peakers — CT_CHP 6.95 -> 3.54 TWh (2024),
            # FAIL -> PASS. It is grounded in topping-cycle physics (steam-credit
            # ratio), NOT this residual-tunable offer curve, so the offer curve
            # stays the validated compact-cogen 1.10/1.20/1.40 for the rest of
            # CT_CHP. (The freed energy backfills onto CC_REGULAR via the
            # evening-ramp import-under / domestic-gas-over root cause, which is
            # the open C1/C3 item — see docs/caiso-eor-power-hr-2026-06.md.)
            "CT_CHP": {
                "committed": 1.20 if iso == "PJM" else 1.10,
                "econ_low": 1.20,
                "econ_high": 1.20,
                "peak": 1.40,
                "econ_low_share": 0.50,
            },
            # CT/ST committed band raised as a P1 startup-cost proxy: the
            # part-load committed slice only clears when price is high, so
            # peakers stop parking at ~20% CF for hundreds of hours. CT hurdle
            # is committed 1.55 (peak HR mult 13.15); ST hurdle committed 0.81
            # with a slightly lower econ-high / peak top. The CT committed
            # hurdle / econ-low / peak are an ERCOT calibration tune; PJM keeps
            # its own validated CT curve (committed 1.10, econ_low 1.32,
            # peak 13.0).
            # ERCOT committed folds in the run57 baseline (1.55 -> 1.48).
            "CT_PEAKER": {
                "committed": 1.10
                if iso == "PJM"
                else (1.48 if iso == "ERCOT" else 1.55),
                "econ_low": 1.20 if iso == "PJM" else 1.27,
                "econ_high": 1.98,
                "peak": 13.0 if iso == "PJM" else 13.15,
                "econ_low_share": 0.526,
                "pct_peaking": 7.0,
            },
            # Intermediate-duty simple-cycle CTs (MISO). EIA-860 confirms these
            # are genuine GT/IC units, not mislabeled CCs — but their measured
            # CAMPD median CF (>= ct_intermediate_cf_threshold) shows they run
            # intermediate/near-baseload, not as true peakers. Routed here only
            # when config.ct_intermediate_split is set (fleet._offer_curve_for_group
            # + fleet.ct_intermediate_plants); the rest of CT_PEAKER keeps the
            # steep true-peaker curve above. The committed-band start-cost hurdle
            # (CT_PEAKER 1.55) is dropped — an always-running unit amortizes its
            # one start over thousands of hours, so its committed energy is priced
            # at its own delivered marginal cost (base_HR x ~1.0-1.2) with a thin
            # rising ramp, overlapping the CC fleet so it clears at intermediate
            # load. A modest scarcity peak (3.0) is kept above the ramp. Inert for
            # every ISO/run with the split off (keepers unchanged).
            "CT_INTERMEDIATE": {
                "committed": 1.00,
                "econ_low": 1.00,
                "econ_high": 1.20,
                "peak": 3.00,
                "econ_low_share": 0.50,
                "pct_peaking": 5.0,
            },
            # ERCOT bands fold in the run57 baseline (committed 0.81->0.91,
            # econ_low 1.05->1.15, econ_high 1.40->1.55). Other ISOs unchanged.
            "ST_GAS": {
                "committed": 0.91 if iso == "ERCOT" else 0.81,
                "econ_low": 1.15 if iso == "ERCOT" else 1.05,
                "econ_high": 1.55 if iso == "ERCOT" else 1.40,
                "peak": 4.20,
                "econ_low_share": 0.500,
                "pct_peaking": 15.0,
            },
            # Flatter curve for the measured intermediate-duty MISO steam cohort
            # (fleet.st_gas_intermediate_plants, median CF >= threshold), routed
            # here only when st_gas_intermediate_split is set (--st-gas-intermediate;
            # default OFF, so every prior keeper / other ISO is byte-identical and
            # the base ST_GAS curve above is untouched). These near-baseload
            # boilers (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine)
            # carry almost no peaking band — their energy is sustained, not
            # scarcity — so the steep peaker-shaped ST_GAS curve mis-prices them
            # above merit and the model under-runs them. Mirrors CT_INTERMEDIATE.
            "ST_GAS_INTERMEDIATE": {
                "committed": 0.85,
                "econ_low": 1.00,
                "econ_high": 1.15,
                "peak": 2.20,
                "econ_low_share": 0.500,
                "pct_peaking": 6.0,
            },
            # Coal split by supply: lignite (mine-mouth) raised +0.05 across the
            # board; PRB uses a pure offer curve (sigmoid off) -- higher commit,
            # lower econ-low start, slightly higher econ-high.
            "COAL_LIGNITE": {
                "committed": 0.95,
                "econ_low": 1.14,
                "econ_high": 1.15,
                "peak": 1.55,
                "econ_low_share": 0.556,
            },
            # ERCOT econ bands fold in the run57 baseline (econ_low 0.77->0.70,
            # econ_high 1.19->0.94). Other ISOs keep the prior PRB curve.
            # PRB committed-band tuning is applied per-run as an offer-curve
            # delta (e.g. Run-60 -0.05, Run-61 -0.20), not baked in here, so the
            # baseline stays at run57 and every run's tweak is delta-from-run57.
            "COAL_PRB": {
                "committed": 0.95,
                "econ_low": 0.70 if iso == "ERCOT" else 0.77,
                "econ_high": 0.94 if iso == "ERCOT" else 1.19,
                "peak": 1.48,
                "econ_low_share": 0.556,
            },
            # Non-ERCOT coal by EIA-923 fuel rank (scripts/derive_coal_supply.py;
            # routes via fleet._COAL_SUPPLY_TO_CURVE). PJM 2024: 25 bituminous,
            # 8 waste, 2 sub-bituminous plants. Per-plant delivered fuel cost
            # already comes from EIA-923, so these shape the dispatch curve:
            #  - COAL_BIT: Appalachian/Illinois-Basin bituminous — the baseload
            #    workhorse; keeps the validated generic-coal curve.
            #  - Sub-bituminous (Powder River by rail) routes to COAL_PRB —
            #    one PRB name across ISOs (plant_taxonomy COAL_SUPPLY_TO_CLASS);
            #    its non-ERCOT band variants live on the COAL_PRB entry above.
            #  - COAL_WC: waste coal/culm (subsidised remediation fluidised-bed)
            #    — runs flat baseload, almost never peaks (low peak band).
            "COAL_BIT": {
                "committed": 0.90,
                "econ_low": 0.95,
                "econ_high": 1.10,
                "peak": 1.45,
                "econ_low_share": 0.55,
            },
            "COAL_WC": {
                "committed": 0.85,
                "econ_low": 0.90,
                "econ_high": 1.02,
                "peak": 1.20,
                "econ_low_share": 0.55,
            },
            # Generic fallback for coal plants with no EIA-923 receipts / rank
            # (and ISOs not yet derived). Flat baseload curve.
            "COAL": {
                "committed": 0.90,
                "econ_low": 0.95,
                "econ_high": 1.10,
                "peak": 1.45,
                "econ_low_share": 0.55,
            },
        },
        chp_steam_following=True,  # model CC/CT/ST_CHP as steam-host cogens:
        #   a per-plant sector-keyed BTM pull-out (fleet.chp_btm_pct) plus a
        #   grid-delivered steam-following min-gen (CHP_PMIN_CF_BY_PLANT - BTM).
        chp_btm_floor_pct=40.0,  # flat fallback only (sector BTM supersedes it).
        # ERCOT's unit-level derate only supplements the facility overlay, so it
        # keeps both. Other ISOs (PJM) derive their unit-level file from ALL
        # CAMPD unit data — the complete outage source — so they drop the
        # redundant facility overlay to avoid double-counting (which crushed
        # coal availability and spiked prices).
        historic_outage_overlay=(iso == "ERCOT"),
        # Uniform gas pricing is the default because ERCOT's EIA-923 gas
        # reporting is sparse (~12% of CC capacity), so per-plant pricing
        # penalises the few reporting plants. Non-ERCOT ISOs (PJM) have good
        # gas reporting coverage, and uniform Henry-Hub+basis underprices their
        # delivered gas — CC overran +25 TWh and displaced coal. Re-enable
        # per-plant EIA-923 monthly gas costs for them.
        gas_plant_monthly_fuel_pricing=(iso != "ERCOT"),
        # Dual-fuel switching (doc 03 Pack G; doc-07 design decision 3): EIA-860
        # oil/gas switch-capable gas units price fuel at min(gas, oil) per hour,
        # so winter delivered-gas spikes past oil parity no longer price them out
        # of the merit order. Gated to the winter-fidelity cluster — PJM plus the
        # NE/NY ISOs (doc-07 P13: NYISO downstate Ravenswood/Astoria/Bowline/
        # Roseton/Northport CT/ST units carry ~17 GW of oil backup; doc-08:
        # NEISO's Algonquin-spot marginal gas unit). Default-off for every other
        # ISO (ERCOT/CAISO/MISO/SPP) — their fleets carry no meaningful dual-fuel
        # behaviour — so they stay byte-identical. NOTE (NYISO U4 caveat): without
        # the Transco Z6 winter-basis upload, the gas leg is the ISO-average
        # measured 923 series, whose Jan-2023 $10.02/MMBtu stays below distillate
        # parity (~$16-20), so the switch is correctly wired but rarely binds on
        # the ISO-average; the downstate Z6 blowout (U4) is what crosses parity.
        dual_fuel_switching=(iso.upper() in ("PJM", "NYISO", "NEISO")),
        # Re-attribute switched dual-fuel MWh to oil (doc-08 §2d) — OFF by
        # default (opt in with --gas-hub-basis-daily, which it rides with):
        # it only bites once the daily overlay pushes winter gas past oil
        # parity. The NEISO keepers run the measured daily overlay (neiso-33
        # onward), so the switch trips on the real cold-day AGT spikes and the
        # ~1.5 TWh measured winter oil burn is relabeled out of gas. Without the
        # daily overlay (flat monthly hub) modeled oil collapses to ~zero and the
        # gas family is over-counted by that ~1.5 TWh — the regression that broke
        # neiso-36's C2 before the daily overlay was restored.
        dual_fuel_oil_reattribution=False,
    )
    if any(f.name == "gas_price_override" for f in fields(ScenarioConfig)):
        config = config.with_overrides(gas_price_override=gas_price)
    else:
        logger.warning(
            "ScenarioConfig has no gas_price_override field; "
            "year %d falls back to the '%s' gas-price trajectory",
            year,
            config.gas_price_path,
        )
    if coal_passthrough is not None:
        config = config.with_overrides(coal_prb_contract_passthrough=coal_passthrough)
    # PJM uses its own price-calibrated offer curve (the per-class block above
    # carries ERCOT-fitted values for the shared classes). Replacing the whole
    # dict keeps the calibrated PJM curve in one place (_PJM_OFFER_CURVE) and
    # out of the per-band `if iso == "PJM"` ternaries. Operator --offer-curve
    # overrides/deltas below still merge on top, so a sweep starts from the
    # calibrated PJM curve.
    if iso.upper() == "PJM":
        config = config.with_overrides(
            offer_curve_by_group={k: dict(v) for k, v in _PJM_OFFER_CURVE.items()}
        )
    # Neutralize the generic gas band multipliers for every non-ERCOT/non-PJM ISO
    # BEFORE its grounded per-ISO curve is deep-merged on top (rule #24, audit
    # C-11/C-13): the shared fallback carries 1.0 multipliers, so a band an ISO
    # does not explicitly ground resolves to its own base heat rate instead of a
    # silently-inherited ERCOT-fitted value. ERCOT keeps the calibrated base; PJM
    # is fully replaced above. CAISO/MISO/NEISO/NYISO each restore their grounded
    # bands via the per-ISO curves below.
    elif iso.upper() not in ("ERCOT",):
        config = config.with_overrides(
            offer_curve_by_group=_neutralize_generic_gas_bands(
                config.offer_curve_by_group
            )
        )
    # NYISO gas offer curves (SOM-grounded; see _NYISO_OFFER_CURVE). Merged on
    # top of the generic non-PJM/non-ERCOT branch so only the gas classes change
    # and coal/CT_CHP/ST_CHP keep their defaults. Operator --offer-curve
    # overrides/deltas below still merge on top.
    if iso.upper() == "NYISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _NYISO_OFFER_CURVE
            )
        )
    # CAISO gas offer curves (DMM-grounded near-SRMC shape + the $1,000-2,000
    # soft-cap CT scarcity band; see _CAISO_OFFER_CURVE). Merged on top of the
    # generic non-PJM/non-ERCOT branch so only the named gas classes change and
    # CC_CHP / CT_CHP / ST_GAS / coal keep their generic defaults. Replaces the
    # silently-inherited ERCOT offer multipliers (and the ERCOT 13.15x CT wall)
    # that were the domestic source of the CA-zone midday/body LMP over-price.
    # Operator --offer-curve overrides/deltas below still merge on top.
    if iso.upper() == "CAISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _CAISO_OFFER_CURVE
            )
        )
    # MISO gas offer curves (CAMPD-/structure-grounded; see _MISO_OFFER_CURVE).
    # Merged on top of the generic non-PJM/non-ERCOT branch so only the named gas
    # classes change (CC_REGULAR flattened to MISO's measured baseload shape;
    # CT_PEAKER peak capped off the inherited ERCOT 13.15x ORDC wall) and coal /
    # CC_CHP / CT_CHP / ST_GAS keep their generic defaults. Replaces MISO's silent
    # inheritance of the ERCOT-fitted `else` values. Operator --offer-curve
    # overrides/deltas below still merge on top.
    if iso.upper() == "MISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _MISO_OFFER_CURVE
            )
        )
    # NEISO gas offer curve (see _NEISO_OFFER_CURVE). Consolidates NEISO's
    # effective gas curve — previously a scattered inline CC_REGULAR committed
    # override plus a silent fall-through to the generic ERCOT-derived else — into
    # one grounded, commented place at parity with PJM/NYISO. Merged on top of the
    # generic branch so only the named gas classes change and coal / *_INTERMEDIATE
    # keep their defaults; per-plant committed/peaking % from CAMPD still supersede.
    # Operator --offer-curve overrides/deltas below still merge on top.
    if iso.upper() == "NEISO":
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, _NEISO_OFFER_CURVE
            )
        )
    # Operator-supplied per-class/per-band heat-rate multiplier overrides
    # (run_calibration_full --offer-curve-json) deep-merged onto the calibrated
    # defaults above. Only the named bands change; the merged curve is recorded
    # verbatim in the bundle's run_config.json (scenario_config.offer_curve_by_group).
    if offer_curve_overrides:
        config = config.with_overrides(
            offer_curve_by_group=_deep_merge_offer_curve(
                config.offer_curve_by_group, offer_curve_overrides
            )
        )
    # Relative nudges (run_calibration_full --offer-curve-delta-json): added on
    # top of the (possibly absolute-overridden) curve, so the operator can tweak
    # by +/-0.05 without restating the prior value. The resolved absolute curve
    # is still recorded in run_config.json.
    if offer_curve_deltas:
        config = config.with_overrides(
            offer_curve_by_group=_apply_offer_curve_deltas(
                config.offer_curve_by_group, offer_curve_deltas
            )
        )
    return config


def _apply_ttc_overrides(
    iso_config, ttc: np.ndarray, overrides: dict[str, float | None]
) -> np.ndarray:
    """Return ``ttc`` with the requested link capabilities overridden.

    Args:
        iso_config: The ISO topology, used to map links to zone pairs.
        ttc: The base ``(n_links,)`` transfer-capability array.
        overrides: ``{"ttc_wn": MW | None, "ttc_wsc": MW | None,
            "ttc_pn": MW | None}``.

    Returns:
        A copy of ``ttc`` with each non-``None`` override applied.
    """
    ttc = ttc.copy()
    for key, value in overrides.items():
        if value is None:
            continue
        target = _TTC_LINK_ZONES[key]
        for i, link in enumerate(iso_config.links):
            if frozenset({link.from_zone, link.to_zone}) == target:
                logger.info(
                    "override %s link TTC: %.0f -> %.0f MW",
                    "-".join(sorted(target)),
                    ttc[i],
                    value,
                )
                ttc[i] = value
    return ttc


def _apply_iso_year_ttc(iso_config, iso: str, year: int):
    """Return ``iso_config`` with year-varying interface TTCs applied.

    Some interfaces change capacity across the backcast years as transmission
    is built (e.g. NYISO's Central-East jumps with the NY Transco AC
    Transmission project, in service December 2023). The static topology in
    ``iso_configs`` carries one value; this rewrites the matching links to the
    year-accurate limit (``constants.NYISO_INTERFACE_TTC_BY_YEAR``) so 2023
    runs on the pre-upgrade limit and 2024+ on the upgraded one. A no-op for
    ISOs/years with no entry.
    """
    if iso != "NYISO":
        return iso_config
    overrides = NYISO_INTERFACE_TTC_BY_YEAR.get(year)
    if not overrides:
        return iso_config
    links = []
    for link in iso_config.links:
        new_ttc = overrides.get((link.from_zone, link.to_zone))
        if new_ttc is not None and new_ttc != link.ttc_mw:
            logger.info(
                "NYISO %d interface TTC: %s->%s %.0f -> %.0f MW "
                "(AC Transmission year-varying limit)",
                year,
                link.from_zone,
                link.to_zone,
                link.ttc_mw,
                new_ttc,
            )
            links.append(link.model_copy(update={"ttc_mw": new_ttc}))
        else:
            links.append(link)
    return iso_config.model_copy(update={"links": links})


def _apply_iso_monthly_ttc(ttc, iso_config, iso: str, year: int, hours: int):
    """Expand the scalar TTC array to a per-hour ``(hours, n_links)`` matrix
    when the ISO has a measured monthly interface envelope for ``year``.

    NYISO's Central-East day-ahead TTC is not flat across a year: it steps up
    when the AC Transmission upgrade energizes (Dec 2023) and derates each
    late-summer/shoulder. ``constants.NYISO_INTERFACE_TTC_BY_MONTH`` carries the
    measured 12-month mean per interface; this maps each hour of the backcast
    year to its calendar month (leap-safe) and rewrites the matching link's
    limit hour by hour, so the dispatch binds on the seasonal envelope rather
    than one annual value. Returns ``ttc`` unchanged (1-D) for ISOs/years with
    no monthly table — byte-identical to the prior scalar path.
    """
    if iso != "NYISO":
        return ttc
    monthly = NYISO_INTERFACE_TTC_BY_MONTH.get(year)
    if not monthly:
        return ttc
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_per_month = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_of_hour = np.repeat(np.arange(1, 13), [d * 24 for d in days_per_month])[
        :hours
    ]
    ttc_t = np.broadcast_to(ttc, (hours, len(ttc))).copy()
    for i, link in enumerate(iso_config.links):
        profile = monthly.get((link.from_zone, link.to_zone))
        if profile is None:
            continue
        prof = np.asarray(profile, dtype=float)
        ttc_t[:, i] = prof[month_of_hour - 1]
        logger.info(
            "NYISO %d %s->%s monthly TTC envelope: %.0f-%.0f MW "
            "(measured Central-East DAM postings)",
            year,
            link.from_zone,
            link.to_zone,
            prof.min(),
            prof.max(),
        )
    return ttc_t


def _apply_caiso_solar_deliverability(
    solar_cf: np.ndarray, iso: str, year: int, config
) -> np.ndarray:
    """Re-curtail the CAISO solar potential for the local congestion the reduced
    topology can't see (Lever D).

    Two CAISO-only paths, both operating on the per-zone solar CF upper bound the
    LP dispatches against:

    * **Structural** (``config.caiso_solar_deliverability``, the keeper path): a
      local-deliverability derate ``clip(1 − k × solar_frac(t), floor, 1)`` from
      :func:`market_sim.model.transmission.caiso_solar_deliverability_derate`,
      driven by the FORWARD solar-penetration signal. The curtailed VOLUME emerges
      per-year from that year's own penetration/build — never a pin to actuals.

    * **Interim stopgap** (``config.caiso_solar_cap_at_delivered``, a default-off
      DIAGNOSTIC): caps each hour's solar at the measured EIA-930 delivered share
      of the HSL potential. This PINS solar to the measured outcome (no forward
      analogue) and must never feed a keeper — it exists only as an A/B reference
      for the structural derate (CLAUDE.md #11).

    Returns ``solar_cf`` unchanged (byte-identical) for non-CAISO ISOs, when
    neither flag is set, or when the forward signal / HSL data is unavailable.
    """
    if iso.upper() != "CAISO":
        return solar_cf
    hours = solar_cf.shape[1]

    if getattr(config, "caiso_solar_cap_at_delivered", False):
        # DIAGNOSTIC: delivered/potential ratio from the HSL parquet (delivered
        # gen ÷ uncurtailed potential), applied as a per-hour ceiling on the CF.
        from market_sim.data.renewables import load_hsl_hourly

        hsl = load_hsl_hourly("CAISO", year)
        if hsl is not None:
            pot = hsl["solar_hsl_mw"].to_numpy(dtype=float)[:hours]
            gen = hsl["solar_gen_mw"].to_numpy(dtype=float)[:hours]
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(pot > 0.0, np.clip(gen / pot, 0.0, 1.0), 1.0)
            logger.info(
                "CAISO %d: solar cap-at-delivered DIAGNOSTIC (default-off pin, "
                "not forecast skill) — solar potential haircut to measured "
                "delivered, mean ratio %.3f midday",
                year,
                float(
                    np.mean(
                        ratio[
                            (np.arange(hours) % 24 >= 9) & (np.arange(hours) % 24 <= 15)
                        ]
                    )
                ),
            )
            return solar_cf * ratio[None, :]
        logger.warning(
            "CAISO %d: --caiso-solar-cap-at-delivered requested but no HSL "
            "parquet — solar left uncapped (no-op)",
            year,
        )
        return solar_cf

    if getattr(config, "caiso_solar_endogenous_spill", False):
        logger.info(
            "CAISO %d: endogenous solar spill — full solar potential passed "
            "to LP (no pre-LP CF derate); solar sets the midday dual when "
            "curtailed",
            year,
        )
        return solar_cf

    if getattr(config, "caiso_solar_deliverability", False):
        from market_sim.model.transmission import caiso_solar_deliverability_derate

        derate = caiso_solar_deliverability_derate(
            year,
            hours,
            float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
            float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
        )
        if derate is not None:
            hod = np.arange(hours) % 24
            mid = (hod >= 9) & (hod <= 15)
            logger.info(
                "CAISO %d: local solar deliverability derate (Lever D) — "
                "solar potential capped at clip(1 − %.3f × solar_frac, %.2f, 1); "
                "midday mean derate %.3f (≈ %.1f%% midday curtailment headroom)",
                year,
                float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
                float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
                float(np.mean(derate[mid])),
                100.0 * (1.0 - float(np.mean(derate[mid]))),
            )
            return solar_cf * derate[None, :]
        logger.warning(
            "CAISO %d: caiso_solar_deliverability on but no forward solar "
            "penetration signal — solar left uncapped (no-op)",
            year,
        )
    return solar_cf


def _drop_biomass_units(fleet, fuel_fracs):
    """Remove biomass LP units (and their parallel fuel fractions) from a fleet.

    Used when biomass is injected as a measured EIA-923 must-run profile (the
    caller nets it out of demand and re-adds it as a fixed pseudo-unit), so the
    raw biomass generators must not also clear the merit order — else biomass is
    served twice. Returns the filtered ``(fleet, fuel_fracs)`` pair (order- and
    length-preserving). A no-op for a fleet with no biomass units (e.g. ERCOT,
    whose CAMPD path already excludes them).
    """
    kept = [(g, ff) for g, ff in zip(fleet, fuel_fracs) if g.fuel_type != "biomass"]
    return [g for g, _ in kept], [ff for _, ff in kept]


def run_year(
    year: int,
    iso: str,
    hours: int,
    gas_price: float,
    ttc_overrides: dict[str, float | None],
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    retiree_cems_cap: bool = False,
    ct_mustrun_per_plant: bool = False,
    ct_mustrun_floor_frac: float = 1.0,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    coal_bit_sigmoid: bool = False,
    bit_overrides: dict | None = None,
    coal_takeorpay_from_data: bool = False,
    coal_mustrun_online_pmin: bool = False,
    coal_sync_srmc_tranche: bool = False,
    ct_intermediate_split: bool = False,
    ct_intermediate_cf_threshold: float | None = None,
    cc_intermediate_split: bool = False,
    cc_intermediate_cf_threshold: float | None = None,
    tranche_startup_amortization: bool = False,
    tranche_startup_measured_runs: bool = False,
    nysdec_peaker_rule_availability: bool = False,
    oil_primary_bin_fuel: bool = False,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    storage_vintage_ramp: bool = False,
    battery_dispatch_adder: float = 0.0,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    pjm_zonal_gas_basis: bool = False,
    miso_zonal_gas_basis: bool = False,
    pjm_congestion: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
    curve_smoothing: dict[str, float | int | None] | None = None,
    cc_derate_from_top: bool = False,
    cc_nameplate_summer_derate: bool = False,
    must_run_mw: "np.ndarray | None" = None,
    inject_biomass_mustrun: bool = False,
    priced_interchange: bool = False,
    hydro_backfill_year: int | None = None,
    as_reserve_withholding: bool = False,
    as_reserve_formula: bool = False,
    energy_reserve_coopt: bool = False,
    miso_zonal_reserves: bool = False,
    miso_reserve_pergen: bool = False,
    ercot_multiproduct_as_coopt: bool = False,
    ercot_ecrs_conservative_deployment: bool = False,
    ercot_ordc_total_reserve: bool = False,
    ercot_as_aware_commitment: bool = False,
    ercot_reserve_supply_cap: bool = False,
    ercot_reserve_supply_cap_from_year: int = 2023,
    ercot_reserve_supply_forward: bool = False,
    pjm_reserve_supply_cap: bool = False,
    pjm_reserve_online_gated: bool = False,
    pjm_reserve_online_rho: float = 1.0,
    pjm_reserve_pergen: bool = False,
    ercot_as_forward_requirement: bool = False,
    ercot_load_resource_reserve: bool = False,
    ercot_load_resource_reserve_from_year: int = 2023,
    ercot_storage_as_reserve: bool = False,
    ercot_storage_as_reserve_from_year: int = 2025,
    ercot_ecrs_requirement: bool = False,
    ercot_ecrs_requirement_from_year: int = 2023,
    ordc_lolp_params_path: str | None = None,
    ercot_storage_as_product_credit: bool = False,
    gas_hh_monthly_shape: bool = False,
    storage_as_commitment: bool = False,
    ercot_storage_as_endogenous: bool = False,
    ercot_storage_as_duration_gate: bool = False,
    hydro_eia930_monthly: bool = False,
    hydro_forecast_budget: bool = False,
    hydro_year: str = "normal",
    interchange_shaping: bool = False,
    interchange_shaping_export_only: bool = False,
    reference_price_interface: bool = False,
    negative_renewable_offers: bool | None = None,
    caiso_gas_commitment_floor: bool | None = None,
    caiso_gas_floor_frac: float | None = None,
    caiso_ra_mustoffer: bool | None = None,
    caiso_ra_min_load_frac: float | None = None,
    caiso_ra_startup_bridge: bool | None = None,
    caiso_ra_bridge_decommit: bool | None = None,
    reliability_floor: bool | None = None,
    reliability_floor_overrides: dict | None = None,
    scarcity_price_overlay: bool | None = None,
    caiso_solar_deliverability: bool | None = None,
    caiso_solar_deliverability_k: float | None = None,
    caiso_solar_endogenous_spill: bool | None = None,
    caiso_solar_cap_at_delivered: bool | None = None,
    neiso_gas_coldsnap_derate: bool | None = None,
    neiso_oil_burn_budget: bool | None = None,
    neiso_winter_fuel_inventory: bool | None = None,
    neiso_winter_fuel_start_fill_bbl: float | None = None,
    caiso_import_hub_prices: bool | None = None,
    caiso_import_gas_coupling: bool | None = None,
    caiso_import_solar_shape: bool | None = None,
    caiso_bidir_intertie: bool | None = None,
    caiso_per_hub_intertie: bool | None = None,
    caiso_perhub_firm_base: bool | None = None,
    caiso_corridor_flow_limit: bool | None = None,
    caiso_intertie_reference_price: bool | None = None,
    caiso_corridor_atc_forward: bool | None = None,
    caiso_reference_price_seam: bool | None = None,
    capacity_deliverability_limits: bool | None = None,
    ramp_limits: bool | None = None,
    local_capacity_constraints: bool | None = None,
    nyiso_local_selfsupply: bool | None = None,
    nyiso_firm_imports: bool | None = None,
    nyiso_import_reconciliation: bool | None = None,
    nyiso_import_hub_prices: bool | None = None,
    nyiso_iroquois_winter_spread: bool | None = None,
    nyiso_synchronised_reserve: bool | None = None,
    nyiso_spin_headroom_frac: float | None = None,
    miso_firm_imports: bool | None = None,
    miso_seam_flow_limit: bool = False,
    miso_seam_flow_percentile: float | None = None,
    miso_seam_export_limit: bool = False,
    miso_pjm_border_anchor: bool = False,
    miso_cc_coal_rebalance: bool = False,
    miso_firm_import_floor: bool = False,
    miso_pjm_lmp_import_pricing: bool = False,
    pjm_seam_flow_limit: bool = False,
    pjm_seam_flow_percentile: float | None = None,
    pjm_seam_export_limit: bool = False,
    gas_hub_basis_overlay: bool | None = None,
    gas_st_netload_drag: bool = False,
    gas_st_drag_overrides: dict[str, float] | None = None,
    st_gas_intermediate: bool = False,
    st_gas_intermediate_cf_threshold: float | None = None,
    ct_netload_drag: bool | None = None,
    ct_drag_overrides: dict[str, float] | None = None,
    chp_export_floor_measured: bool = False,
    ercot_gtc_limits_measured: bool = False,
    zero_forcing_ablation: bool = False,
    fleet_only: bool = False,
    xyear_cache: "list | None" = None,
) -> "tuple[object, FleetContext, object | None, dict] | dict":
    """Solve the single-year calibration dispatch for one ISO-year.

    Builds the calibration configuration, loads the EIA-860 generator and
    storage fleets and the year's EIA-930 demand and renewable profiles,
    assembles the marginal-cost array (fuel cost, cycling adders, EAC and
    IRA dispatch credits) and solves the hourly economic dispatch. No
    capacity evolution is performed — the fleet is dispatched as observed.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).
        ttc_overrides: Optional per-link TTC overrides for a sweep.
        coal_passthrough: Optional PRB coal contract-passthrough override.
        commitment_enabled: When True, run the P2 unit-commitment pass after
            P1 and return the P1 result for comparison.
        commitment_screen_coal: When False, coal is exempt from the P2 screen.
        zero_forcing_ablation: When True, neutralize every merchant floor/
            bridge (keeping only nuclear must-run, CHP steam-following and coal
            take-or-pay) via ``ScenarioConfig.as_zero_forcing_ablation`` after
            all config resolution — the D-3 ablation twin (audit §7 /
            CLAUDE.md rule 20).
        fleet_only: When True, stop after the fleet/storage arrays are built
            and return a state dict instead of solving any LP. Lets a
            post-processor (e.g. the ORDC scarcity overlay,
            ``scripts/derive_ordc_overlay.py``) reconstruct the exact hourly
            availability a persisted bundle solved against — same config,
            same outage overlay, same derates — without re-solving.
        priced_interchange: When True, interchange is served by the priced
            import/export node (import tranches + export sinks in the ISO's
            external zone, the forward-scenario mechanism) instead of the
            measured schedule added to demand. Lets a backcast validate the
            node's calibration against the EIA-930 net-interchange duration
            curve.

    Returns:
        A tuple ``(result, context, result_p1, p2_state)``. ``result`` is the
        final dispatch (P2 when commitment is enabled, otherwise P1);
        ``result_p1`` is the pre-commitment P1 result when commitment ran,
        else ``None``; ``p2_state`` is the cached P1 input bundle that
        :func:`_commitment_pass` (the P2 post-process) consumes.
    """
    config = _calibration_config(
        year,
        iso,
        hours,
        gas_price,
        coal_passthrough,
        commitment_enabled,
        commitment_screen_coal,
        coal_lignite_mustrun,
        coal_prb_mustrun,
        coal_prb_passthrough,
        outage_source,
        coal_prb_passthrough_sigmoid,
        coal_mustrun_per_plant,
        retiree_cems_cap,
        ct_mustrun_per_plant,
        ct_mustrun_floor_frac,
        coal_drop_pof,
        coal_prb_passthrough_tiered,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
    )
    if gas_st_netload_drag:
        config = config.with_overrides(
            gas_st_netload_drag=True, **(gas_st_drag_overrides or {})
        )
    # Tri-state: None keeps the _calibration_config per-ISO default (CAISO
    # keeper default-ON), True/False force the drag on/off — so an A/B arm
    # can run CAISO with the drag scrubbed (--no-ct-netload-drag) without
    # touching the keeper default.
    if ct_netload_drag is not None:
        config = config.with_overrides(ct_netload_drag=bool(ct_netload_drag))
        if ct_netload_drag and ct_drag_overrides:
            config = config.with_overrides(**ct_drag_overrides)
    if chp_export_floor_measured:
        # Measured steam-following export floor (backcast overlay): CHP bins'
        # grid floor rides at the year's measured EIA-923 class CF x the
        # sector grid-delivery share instead of the pooled CAMPD p2 minimum.
        config = config.with_overrides(chp_export_floor_measured=True)
    if ercot_gtc_limits_measured:
        # Measured ERCOT GTC transfer limits (backcast overlay): the GTC-
        # carrying links' export capability follows the hourly NP6-86 series
        # (gtc-limits clean datatype) instead of the static ttc_mw.
        config = config.with_overrides(ercot_gtc_limits_measured=True)
    if interchange_shaping:
        config = config.with_overrides(interchange_shaping=True)
    if interchange_shaping_export_only:
        config = config.with_overrides(
            interchange_shaping=True, interchange_shaping_export_only=True
        )
    if reference_price_interface:
        config = config.with_overrides(reference_price_interface=True)
    if coal_takeorpay_from_data:
        # Coal must-run sunk fraction = measured EIA-923 Schedule-5 take-or-pay
        # share per plant (campd_tranche_fuel_frac), not the hardcoded 100%.
        config = config.with_overrides(coal_takeorpay_from_data=True)
    if coal_mustrun_online_pmin:
        # Coal must-run band sized to the measured online-net-MW synchronization
        # Pmin (thermal_tranches mustrun_online_pct), not the all-hours
        # available-CF floor (rebuild step 2).
        config = config.with_overrides(coal_mustrun_online_pmin=True)
    if coal_sync_srmc_tranche:
        # SRMC-priced synchronization tranche (rebuild step 3a): the coal
        # online-Pmin band is split by the measured contract share into a
        # fuel-free _mustrun floor and a full-SRMC _sync band, both forced on so
        # coal holds synchronized at min-load while dispatchable tranches above
        # price-follow.
        config = config.with_overrides(coal_sync_srmc_tranche=True)
    if ct_intermediate_split:
        # Route the measured intermediate-duty CT cohort
        # (fleet.ct_intermediate_plants) to the flatter CT_INTERMEDIATE offer
        # curve so their always-on energy clears instead of carrying the steep
        # true-peaker start-cost hurdle (the CT_PEAKER-under / CC-over miss).
        config = config.with_overrides(ct_intermediate_split=True)
    if ct_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            ct_intermediate_cf_threshold=float(ct_intermediate_cf_threshold)
        )
    if cc_intermediate_split:
        # Route the measured baseload-duty CC cohort (fleet.cc_intermediate_plants)
        # to the flatter CC_INTERMEDIATE offer curve so the upper operating-range
        # tranches of MISO's near-baseload CC fleet clear instead of carrying the
        # ERCOT-peaker-fit rising econ ramp (the 2023/2024 gas-CC under-run). Only
        # the operating-range ramp is corrected; the duct-burner peak is unchanged.
        config = config.with_overrides(cc_intermediate_split=True)
    if cc_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            cc_intermediate_cf_threshold=float(cc_intermediate_cf_threshold)
        )
    if tranche_startup_amortization:
        # Fast-start tranche pricing (ISO-NE Order 825 analogue): the gas
        # bins' econ/peak tranches carry the same NREL start cost as the
        # committed anchor, so the P1 markup amortizes each tranche's own P0
        # run lengths into its bid — the fuel-price-invariant commitment-cost
        # component of the real offer stack the HR-multiplier curve cannot
        # express (winter over- / summer-evening under-pricing signature).
        config = config.with_overrides(tranche_startup_amortization=True)
    if tranche_startup_measured_runs:
        # v3 measured-run-length basis: the simple-cycle CT tranches amortize
        # over the CAMPD-measured median start-to-stop run length
        # (derive_campd_ct_run_lengths.py artifact) as the horizon ceiling —
        # P0 runs may only shorten it — removing the v2 circularity where
        # too-cheap offers → long P0 blocks → ≈0 markup (nyiso-44 finding).
        config = config.with_overrides(tranche_startup_measured_runs=True)
    if nysdec_peaker_rule_availability:
        # NYSDEC 6 NYCRR 227-3 peaker-rule availability overlay: curated
        # unit-level ozone-season compliance windows (Gold Book IV-3..IV-6),
        # availability only, never an offer/price change (rule #12 class of
        # the CAMPD outage windows).
        config = config.with_overrides(nysdec_peaker_rule_availability=True)
    if oil_primary_bin_fuel:
        # Measured EIA-860 oil-primary fuel correction (plant-registry screen
        # unioned with the generator-level Energy-Source-1 majority screen);
        # CLI-explicit counterpart of the legacy ERCOT_OIL_PRIMARY env gate.
        config = config.with_overrides(oil_primary_bin_fuel=True)
    if st_gas_intermediate:
        # MISO intermediate gas-steam structure (one consolidated lever, default
        # OFF → prior keepers / other ISOs byte-identical). The legacy gas-steam
        # fleet (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine, ...)
        # runs intermediate-duty, not as peakers, but inherits ERCOT-fitted steam
        # parameters that under-run it (Moselle / Lewis Creek) and let it cycle
        # with peaker agility. Three coupled corrections, each well-grounded:
        #  1. route the measured median-CF cohort (fleet.st_gas_intermediate_plants)
        #     to the flatter ST_GAS_INTERMEDIATE offer curve so its sustained
        #     energy clears;
        #  2. the ST_GAS startup cost + min-run feed the P1 bid markup so a
        #     stop-start costs more than idling (steam drags, not cycles);
        #  3. replace the ERCOT-fitted ST_GAS WEFOR base (0.21, >2x every other
        #     thermal class) with a realistic NERC-GADS gas-steam EFOR, lifting
        #     the implicit availability crush off MISO's net-summer-rated steam.
        # NOTE: the net-load reliability-drag floor (the Little Gypsy / River
        # load-pocket weather-dependent must-run) is deliberately NOT enabled
        # here. Its ScenarioConfig coefficients are ERCOT-derived and SATURATE at
        # the 0.34 cap across all of MISO's larger net-load range (60-110 GW),
        # degenerating into a flat 34% must-run rather than the weather-responsive
        # curve intended — borrowed coefficients, not a MISO mechanism. It needs
        # a MISO-specific regression (MISO overnight ST_GAS CAMPD CF vs MISO
        # net-load), mirroring the ERCOT/NYISO/CAISO per-ISO floor derivations,
        # before it can be a keeper lever. Tracked as the immediate follow-up;
        # enable per-run via --gas-st-netload-drag once MISO coefficients exist.
        config = config.with_overrides(
            st_gas_intermediate_split=True,
            gas_st_startup_cost=True,
            gas_st_wefor_base_override=0.10,
        )
    if st_gas_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            st_gas_intermediate_cf_threshold=float(st_gas_intermediate_cf_threshold)
        )
    # Tri-state overrides: None = keep the per-ISO base default from
    # _calibration_config (CAISO defaults the RA floor + negative offers ON, the
    # validated keeper); an explicit True/False from the CLI overrides it (so a
    # no-floor baseline probe is --no-caiso-gas-commitment-floor).
    if negative_renewable_offers is not None:
        config = config.with_overrides(
            negative_renewable_offers=negative_renewable_offers
        )
    if caiso_gas_commitment_floor is not None:
        config = config.with_overrides(
            caiso_gas_commitment_floor=caiso_gas_commitment_floor
        )
    if caiso_gas_floor_frac is not None:
        config = config.with_overrides(caiso_gas_floor_frac=caiso_gas_floor_frac)
    if caiso_ra_mustoffer is not None:
        config = config.with_overrides(caiso_ra_mustoffer=caiso_ra_mustoffer)
    if caiso_ra_min_load_frac is not None:
        config = config.with_overrides(caiso_ra_min_load_frac=caiso_ra_min_load_frac)
    if caiso_ra_startup_bridge is not None:
        config = config.with_overrides(caiso_ra_startup_bridge=caiso_ra_startup_bridge)
    if caiso_ra_bridge_decommit is not None:
        config = config.with_overrides(
            caiso_ra_bridge_decommit=caiso_ra_bridge_decommit
        )
    if reliability_floor is not None:
        config = config.with_overrides(reliability_floor=reliability_floor)
    if reliability_floor_overrides is not None:
        config = config.with_overrides(
            reliability_floor_overrides=reliability_floor_overrides
        )
    if scarcity_price_overlay is not None:
        config = config.with_overrides(
            scarcity_pricing_enabled=scarcity_price_overlay,
            scarcity_price_overlay=scarcity_price_overlay,
        )
    if caiso_solar_deliverability is not None:
        config = config.with_overrides(
            caiso_solar_deliverability=caiso_solar_deliverability
        )
    if caiso_solar_deliverability_k is not None:
        config = config.with_overrides(
            caiso_solar_deliverability_k=caiso_solar_deliverability_k
        )
    if caiso_solar_endogenous_spill is not None:
        config = config.with_overrides(
            caiso_solar_endogenous_spill=caiso_solar_endogenous_spill
        )
    if caiso_solar_cap_at_delivered is not None:
        config = config.with_overrides(
            caiso_solar_cap_at_delivered=caiso_solar_cap_at_delivered
        )
    if neiso_gas_coldsnap_derate is not None:
        config = config.with_overrides(
            neiso_gas_coldsnap_derate=neiso_gas_coldsnap_derate
        )
    if neiso_oil_burn_budget is not None:
        config = config.with_overrides(neiso_oil_burn_budget=neiso_oil_burn_budget)
    if neiso_winter_fuel_inventory is not None:
        config = config.with_overrides(
            neiso_winter_fuel_inventory=neiso_winter_fuel_inventory
        )
    if neiso_winter_fuel_start_fill_bbl is not None:
        config = config.with_overrides(
            neiso_winter_fuel_start_fill_bbl=neiso_winter_fuel_start_fill_bbl
        )
    if caiso_import_hub_prices is not None:
        config = config.with_overrides(caiso_import_hub_prices=caiso_import_hub_prices)
    if caiso_import_gas_coupling is not None:
        config = config.with_overrides(
            caiso_import_gas_coupling=caiso_import_gas_coupling
        )
    if caiso_import_solar_shape is not None:
        config = config.with_overrides(
            caiso_import_solar_shape=caiso_import_solar_shape
        )
    if caiso_bidir_intertie is not None:
        config = config.with_overrides(caiso_bidir_intertie=caiso_bidir_intertie)
    if caiso_per_hub_intertie is not None:
        config = config.with_overrides(caiso_per_hub_intertie=caiso_per_hub_intertie)
    if caiso_perhub_firm_base is not None:
        config = config.with_overrides(caiso_perhub_firm_base=caiso_perhub_firm_base)
    if caiso_corridor_flow_limit is not None:
        config = config.with_overrides(
            caiso_corridor_flow_limit=caiso_corridor_flow_limit
        )
    if caiso_intertie_reference_price is not None:
        config = config.with_overrides(
            caiso_intertie_reference_price=caiso_intertie_reference_price
        )
    if caiso_corridor_atc_forward is not None:
        config = config.with_overrides(
            caiso_corridor_atc_forward=caiso_corridor_atc_forward
        )
    if caiso_reference_price_seam is not None:
        config = config.with_overrides(
            caiso_reference_price_seam=caiso_reference_price_seam
        )
    if capacity_deliverability_limits is not None:
        config = config.with_overrides(
            capacity_deliverability_limits=capacity_deliverability_limits
        )
    if ramp_limits is not None:
        config = config.with_overrides(ramp_limits=ramp_limits)
    if local_capacity_constraints is not None:
        config = config.with_overrides(
            local_capacity_constraints=local_capacity_constraints
        )
    if nyiso_local_selfsupply is not None:
        config = config.with_overrides(nyiso_local_selfsupply=nyiso_local_selfsupply)
    if nyiso_firm_imports is not None:
        config = config.with_overrides(nyiso_firm_imports=nyiso_firm_imports)
    if nyiso_import_reconciliation is not None:
        config = config.with_overrides(
            nyiso_import_reconciliation=nyiso_import_reconciliation
        )
    if nyiso_import_hub_prices is not None:
        config = config.with_overrides(nyiso_import_hub_prices=nyiso_import_hub_prices)
    if nyiso_iroquois_winter_spread is not None:
        config = config.with_overrides(
            nyiso_iroquois_winter_spread=nyiso_iroquois_winter_spread
        )
    if nyiso_synchronised_reserve is not None:
        config = config.with_overrides(
            nyiso_synchronised_reserve=nyiso_synchronised_reserve
        )
    if nyiso_spin_headroom_frac is not None:
        config = config.with_overrides(
            nyiso_spin_headroom_frac=nyiso_spin_headroom_frac
        )
    if miso_firm_imports is not None:
        config = config.with_overrides(miso_firm_imports=miso_firm_imports)
    if miso_seam_flow_limit:
        config = config.with_overrides(miso_seam_flow_limit=True)
    if miso_seam_flow_percentile is not None:
        # Round-2 import-lift: raise the seam deliverability percentile (p90 ->
        # e.g. p95) so the priced seam clears more import in tight hours. Only
        # bites with --miso-seam-flow-limit; still a measured-duration ceiling.
        config = config.with_overrides(
            miso_seam_flow_percentile=float(miso_seam_flow_percentile)
        )
    if miso_seam_export_limit:
        config = config.with_overrides(miso_seam_export_limit=True)
    if pjm_seam_flow_limit:
        config = config.with_overrides(pjm_seam_flow_limit=True)
    if pjm_seam_flow_percentile is not None:
        config = config.with_overrides(
            pjm_seam_flow_percentile=float(pjm_seam_flow_percentile)
        )
    if pjm_seam_export_limit:
        config = config.with_overrides(pjm_seam_export_limit=True)
    if miso_pjm_border_anchor:
        config = config.with_overrides(miso_pjm_border_anchor=True)
    if miso_cc_coal_rebalance and iso.upper() == "MISO":
        # Raise the MISO CC_REGULAR / COAL_BIT offer curve so the marginal CC /
        # coal-bit MWh sits above the priced-import hurdle (and the under-running
        # CT_PEAKER / ST_GAS), correcting the cheap-domestic-fill-eats-imports
        # miss. ISO-gated (other ISOs / forecasts byte-identical); applied as a
        # deep-merge offer-curve override on top of the calibrated MISO curve.
        rebalanced = _deep_merge_offer_curve(
            config.offer_curve_by_group, _MISO_CC_COAL_REBALANCE
        )
        config = config.with_overrides(
            offer_curve_by_group=rebalanced, miso_cc_coal_rebalance=True
        )
    if miso_firm_import_floor:
        # Firm (must-flow) import floor on the reference-price seam — forces the
        # measured near-firm PJM/IESO net-import base so the seam stops wrongly
        # net-exporting (fixes the import shortfall + 2025 energy-balance overshoot
        # by displacing the over-running domestic coal/CC). Requires the priced
        # interface; MISO-only (only the PJM seam carries a floor).
        config = config.with_overrides(miso_firm_import_floor=True)
    if miso_pjm_lmp_import_pricing:
        config = config.with_overrides(miso_pjm_lmp_import_pricing=True)
    if gas_hub_basis_overlay is not None:
        config = config.with_overrides(gas_hub_basis_overlay=gas_hub_basis_overlay)
    # Per-run PRB passthrough sigmoid floor/ceiling tune (run_calibration_full
    # --prb-* flags); None entries leave the ScenarioConfig default in place.
    if prb_overrides:
        config = config.with_overrides(
            **{k: v for k, v in prb_overrides.items() if v is not None}
        )
    # Gas-keyed coal passthrough sigmoids per supply chain. The bit family
    # has its own flag/overrides; the sub/lignite enables and all their
    # tuning params ride the generic prb_overrides ScenarioConfig override
    # channel (run_calibration_full --coal-{sub,lignite}-sigmoid and the
    # --{sub,lignite}-* flags). Params left at None resolve from the
    # per-ISO COAL_SIGMOID_DEFAULTS table (fuel.coal_sigmoid_params).
    if coal_bit_sigmoid:
        config = config.with_overrides(coal_bit_passthrough_sigmoid=True)
    if bit_overrides:
        config = config.with_overrides(
            **{k: v for k, v in bit_overrides.items() if v is not None}
        )
    # Per-plant tranche-config override sheet (run_calibration_full
    # --plant-tranche-config): each listed plant's tranche shares + band HR
    # multipliers come straight from the CSV, bypassing the offer curve.
    if plant_tranche_config:
        config = config.with_overrides(plant_tranche_config_path=plant_tranche_config)
    # Daily SOC-cycling cap (run_calibration_full --storage-daily-cycling):
    # bounds storage perfect foresight to within-day arbitrage.
    if storage_daily_cycling:
        config = config.with_overrides(storage_daily_cycling=True)
    if storage_vintage_ramp:
        config = config.with_overrides(storage_vintage_ramp=True)
    # AS reserve withholding (run_calibration_full --as-reserve-withholding):
    # remove the measured cleared reserve MW from the gas/flexible-thermal
    # headroom before the energy supply curve clears (ERCOT up-AS / PJM Primary
    # Reserve requirement; fleet.generators_to_fleet_arrays).
    if as_reserve_withholding:
        config = config.with_overrides(as_reserve_withholding=True)
    # CAISO formula-based operating-reserve withholding (run_calibration_full
    # --as-reserve-formula): withhold R(t) = max(MSSC, 0.067*load) + 0.01*load
    # (WECC MORC + 1% regulation-up) from gas top-of-merit headroom; CAISO-only,
    # the default-off scaffold until OASIS cleared-AS data can be pulled
    # (fleet.caiso_operating_reserve_mw / generators_to_fleet_arrays).
    if as_reserve_formula:
        config = config.with_overrides(as_reserve_formula=True)
    # Energy+reserve co-optimization (run_calibration_full
    # --energy-reserve-coopt): co-optimize energy and Primary Reserve inside the
    # LP (structural 1.5 x MSSC requirement + published ORDC demand curve);
    # PJM-gated in _run_dispatch. Replaces the post-solve ORDC overlay.
    if energy_reserve_coopt:
        config = config.with_overrides(energy_reserve_coopt=True)
    # MISO locational (zonal) reserve families on top of the market-wide RBDC
    # (run_calibration_full --miso-zonal-reserves): BPM-002 §3.3.2 zonal
    # minimum requirements priced at the published §5.2.1.2 zonal curve.
    if miso_zonal_reserves:
        config = config.with_overrides(miso_zonal_reserves=True)
    # MISO per-asset (zone x fuel-class pooled) 10-min-ramp-bounded reserve
    # columns (run_calibration_full --miso-reserve-pergen): reserve competes
    # with energy on the marginal pool and cleared reserve is capped at the
    # deliverable 10-minute ramp, so the RBDC / zonal ORDC families can run
    # short (reserve_config._miso_design pergen branch).
    if miso_reserve_pergen:
        config = config.with_overrides(miso_reserve_pergen=True)
    if ercot_multiproduct_as_coopt:
        config = config.with_overrides(ercot_multiproduct_as_coopt=True)
    # Published pre-reform ECRS deployment design (no price-based release
    # through 2024-07-31 -> at-cap demand step; standing ramp after): see
    # reserve_config.ERCOT_ECRS_RELEASE_REFORM_* citations.
    if ercot_ecrs_conservative_deployment:
        config = config.with_overrides(ercot_ecrs_conservative_deployment=True)
    # Lumped ORDC total-reserve family (RTORPA) layered on the product stack:
    # see ScenarioConfig.ercot_ordc_total_reserve / reserve_config.
    if ercot_ordc_total_reserve:
        config = config.with_overrides(ercot_ordc_total_reserve=True)
    # Measured battery AS award netted off the fast products' requirements
    # (multi-product measured-storage path): reserve_config.
    if ercot_storage_as_product_credit:
        config = config.with_overrides(ercot_storage_as_product_credit=True)
    # Measured HH monthly gas shape (level-preserving): fuel.gas_seasonal_shape.
    if gas_hh_monthly_shape:
        config = config.with_overrides(gas_hh_monthly_shape=True)
    if ercot_as_aware_commitment:
        config = config.with_overrides(ercot_as_aware_commitment=True)
    if ercot_reserve_supply_cap:
        config = config.with_overrides(
            ercot_reserve_supply_cap=True,
            ercot_reserve_supply_cap_from_year=ercot_reserve_supply_cap_from_year,
        )
    if ercot_reserve_supply_forward:
        config = config.with_overrides(ercot_reserve_supply_forward=True)
    if pjm_reserve_supply_cap:
        config = config.with_overrides(pjm_reserve_supply_cap=True)
    if pjm_reserve_online_gated:
        config = config.with_overrides(
            pjm_reserve_online_gated=True,
            pjm_reserve_online_rho=pjm_reserve_online_rho,
        )
    if pjm_reserve_pergen:
        config = config.with_overrides(pjm_reserve_pergen=True)
    if ercot_as_forward_requirement:
        config = config.with_overrides(ercot_as_forward_requirement=True)
    # ERCOT load-resource reserve credit (run_calibration_full
    # --ercot-load-resource-reserve): credit measured RRS-UFR (load-side
    # responsive reserve) into the co-opt reserve balance. GATED — alters
    # dispatch volumes. ERCOT co-opt only; a no-op otherwise.
    if ercot_load_resource_reserve:
        config = config.with_overrides(
            ercot_load_resource_reserve=True,
            ercot_load_resource_reserve_from_year=int(
                ercot_load_resource_reserve_from_year
            ),
        )
    # ERCOT storage-AS reserve credit (run_calibration_full
    # --ercot-storage-as-reserve): credit the measured battery-provided AS back
    # into the co-opt reserve balance — storage_as_commitment removes it from the
    # reserve cap, so the committed battery AS would otherwise be dropped from
    # reserve supply. GATED; ERCOT co-opt + storage_as_commitment only.
    if ercot_storage_as_reserve:
        config = config.with_overrides(
            ercot_storage_as_reserve=True,
            ercot_storage_as_reserve_from_year=int(ercot_storage_as_reserve_from_year),
        )
    if ercot_ecrs_requirement:
        config = config.with_overrides(
            ercot_ecrs_requirement=True,
            ercot_ecrs_requirement_from_year=int(ercot_ecrs_requirement_from_year),
        )
    # Published ORDC LOLP table (run_calibration_full --ordc-lolp-params-path):
    # replace the neutral flat fallback (mu=0) with ERCOT's published NP6-576-ER
    # seasonal/TOD mu/sigma so the co-opt reserve demand curve sits at the real
    # reserve level the adder begins to bite. Grounded input, not a price fit.
    if ordc_lolp_params_path:
        config = config.with_overrides(ordc_lolp_params_path=str(ordc_lolp_params_path))
    # Storage AS commitment (run_calibration_full --storage-as-commitment):
    # ERCOT-only reservation of measured storage up-AS MW from the battery
    # dispatch power cap (applied after storage_cap_profiles below).
    if storage_as_commitment:
        config = config.with_overrides(storage_as_commitment=True)
    # Endogenous storage energy-vs-AS co-opt (run_calibration_full
    # --ercot-storage-as-endogenous, G5): the battery CHOOSES energy vs upward-AS
    # inside the multi-product co-opt, replacing the measured-award reservation.
    # Full battery cap to the co-opt (no measured subtraction below), the measured
    # reserve credit guarded off (scarcity.ercot_*_coopt_inputs), and the cleared
    # storage AS counts toward the measured RTOLCAP supply cap. Takes precedence
    # over storage_as_commitment when both are set.
    if ercot_storage_as_endogenous:
        config = config.with_overrides(ercot_storage_as_endogenous=True)
    if ercot_storage_as_duration_gate:
        config = config.with_overrides(ercot_storage_as_duration_gate=True)
    # Battery throughput/cycling cost (run_calibration_full --battery-adder):
    # per-MWh-discharged adder that tames LP over-cycling of the BESS fleet.
    # CAISO defaults to $5/MWh when no explicit adder is passed: the 10+ GW
    # fleet with perfect-foresight LP over-cycles without a throughput cost
    # proxy for degradation + ancillary-service opportunity cost.
    _batt_adder = battery_dispatch_adder
    if not _batt_adder and iso.upper() == "CAISO":
        _batt_adder = 5.0
    if _batt_adder:
        config = config.with_overrides(battery_dispatch_adder=_batt_adder)
    if gas_offer_curve:
        config = config.with_overrides(gas_offer_curve=True)
    # Measured ISO-month delivered gas (EIA-923) instead of annual + shape.
    if gas_monthly_actuals:
        config = config.with_overrides(gas_monthly_actuals=True)
    # PJM per-zone gas basis (opens the west-cheap / east-dear spread so PJM
    # stops clearing as a single copper-plate). No-op for non-PJM ISOs — the
    # apply gates on iso == "PJM" — so setting it here is safe regardless.
    if pjm_zonal_gas_basis:
        config = config.with_overrides(pjm_zonal_gas_basis=True)
    # MISO per-zone gas basis (opens the north/south gas gradient). No-op for
    # non-MISO ISOs — the apply gates on iso == "MISO".
    if miso_zonal_gas_basis:
        config = config.with_overrides(miso_zonal_gas_basis=True)
    # PJM transmission-congestion lever (break the copper-plate): cap the priced
    # external star node to the measured per-border interchange envelope + tighten
    # the internal interfaces to their measured transfer limits. Wired below at
    # the interface-group / TTC build; no-op for non-PJM ISOs.
    if pjm_congestion:
        config = config.with_overrides(pjm_congestion=True)
    # Econ-ramp rendering sweep (run_calibration_full --curve-n / --curve-exp):
    # offer_curve_smoothing_n / offer_curve_smoothing_exp; None entries keep
    # the ScenarioConfig defaults.
    if curve_smoothing:
        config = config.with_overrides(
            **{k: v for k, v in curve_smoothing.items() if v is not None}
        )
    # Top-of-stack outage allocation for CC_REGULAR (run_calibration_full
    # --cc-derate-from-top): partial outages truncate the expensive end of
    # the offer curve instead of scaling every tranche pro-rata. CAISO
    # defaults ON: per-plant peaking bands are narrow (0-4%), so pro-rata
    # derates crush the committed floor and prevent 0% CF hours.
    if cc_derate_from_top or iso.upper() == "CAISO":
        config = config.with_overrides(cc_outage_derate_from_top=True)
    if cc_nameplate_summer_derate:
        config = config.with_overrides(cc_nameplate_summer_derate=True)
    if zero_forcing_ablation:
        # D-3 zero-forcing ablation twin (audit §7 / CLAUDE.md rule 20): drop
        # every MERCHANT floor/bridge, keeping only the structural must-run set
        # (nuclear / CHP-steam / coal take-or-pay). Applied AFTER every per-ISO
        # default and with_overrides so the floors go off regardless of how they
        # were set — the CAISO ct_netload_drag / caiso_ra_mustoffer defaults are
        # config-level (not kwargs), so only a config transform can neutralize
        # them. The off-list is derived from the D-2 mechanism registry, so a
        # new floor is ablated by default (see ScenarioConfig.as_zero_forcing_
        # ablation / data.floor_mechanisms.zero_forcing_field_overrides).
        config = ScenarioConfig.as_zero_forcing_ablation(config)
    # Point the EIA-860 loaders at a year-matched vintage when the scenario asks
    # for one (backcast knob; None resets to the canonical 2025ER snapshot the
    # COD ramp filters to the solved year). Must precede every fleet / storage /
    # renewable / COD-map load below so they all read the same vintage.
    from market_sim.config.paths import set_eia860_vintage

    set_eia860_vintage(
        config.eia860_vintage_year if config.mode == "backcast" else None
    )
    iso_config = get_iso_config(iso)
    # Year-varying interface limits (e.g. NYISO Central-East jumps with the AC
    # Transmission project in service Dec 2023) — applied before the import
    # node joins so the corrected links flow through the whole solve.
    iso_config = _apply_iso_year_ttc(iso_config, iso, year)
    # Priced import/export node (orchestrator-unification Stage 5): the
    # builder choice — reference-price seam vs CAISO per-hub / bidirectional
    # intertie vs the static year-grounded tranche ladder, plus the Manitoba
    # firm-import block — is resolved by the SHARED
    # config/interchange_config.get_interchange_spec (the same spec the
    # forecast runner consumes), and the generators come from the shared
    # build_interchange_fleet, which delegates to the canonical
    # transmission.py builders. The external zone joins the topology and its
    # import tranches + export sinks join the fleet below; the measured
    # interchange schedule then stays out of demand (no double count).
    import_generators: list = []
    # Default the CAISO corridor intertie flag so the later corridor-limit
    # and forward-ATC checks are bound on every path; it is only set inside
    # the priced-interchange block below (CAISO-only), so a non-priced or
    # non-CAISO run keeps it False.
    caiso_corridors = False
    if priced_interchange:
        # CARB levies its cap-and-trade allowance on unspecified WECC imports
        # (border carbon adjustment, EF 0.428 t/MWh x allowance), so every
        # CAISO import tranche carries it in its delivered cost — the same
        # adder the production runner applies (model.runner). It is NOT on the
        # export sinks (exports owe no CA compliance cost). Resolved at the
        # backcast year's carbon price (each calibration solve is single-year).
        border_carbon = (
            wecc_border_carbon_adder(resolve_carbon_price(config, year))
            if iso == "CAISO"
            else 0.0
        )
        interchange_spec = get_interchange_spec(config, iso, year=year)
        caiso_corridors = interchange_spec.use_corridors
        import_generators = build_interchange_fleet(interchange_spec, border_carbon)
        # Shared topology sequence (same order as always): external node
        # extension, the capacity-deliverability Part-A seam import cap
        # (backcast mirror of the runner hook — the published per-area MIC
        # replaces the calibrated simultaneous-import scalar, resolved for
        # THIS backcast year's delivery year; no-op off the default-off flag
        # or when the clean data is absent), then the CAISO per-hub corridor
        # split re-homing the import links + simultaneous cap onto the
        # corridor zones the per-hub / reference-seam builder used.
        iso_config = apply_interchange_topology(
            iso_config,
            interchange_spec,
            config,
            year=year,
            extend_node=True,
        )
    zone_names = iso_config.zone_names

    demand = load_demand(
        iso,
        year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not priced_interchange,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, : config.hours]
        wind_cf = wind_cf[:, : config.hours]
        solar_cf = solar_cf[:, : config.hours]

    # CAISO Lever-D: re-curtail the uncurtailed HSL solar potential the dispatch
    # is handed. The reduced 3-zone topology cannot see the sub-area / local
    # congestion that drives ~70% of CAISO solar curtailment, so the LP runs the
    # full potential and curtails ~0 (docs/caiso-lever-audit-2026-06.md, Lever D).
    solar_cf = _apply_caiso_solar_deliverability(solar_cf, iso, year, config)

    # Must-run "other" resources (biomass, process gas, ...) serve load
    # exogenously — they run for industrial/process reasons, not LP economics —
    # so net them out of demand before the dispatch so they displace marginal
    # gas instead of being double-counted on top of a fully-served balance.
    if must_run_mw is not None:
        mr = np.asarray(must_run_mw, dtype=float)
        if mr.shape[1] > config.hours:
            mr = mr[:, : config.hours]
        demand = np.maximum(demand - mr, 0.0)

    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = _apply_ttc_overrides(
        iso_config, get_ttc_array(iso_config.links), ttc_overrides
    )
    # PJM congestion lever (Lever B): tighten the internal interfaces with a
    # confident measured mapping to their measured PJM transfer-limit postings
    # (constants.PJM_MEASURED_INTERNAL_TTC). Applied to the scalar TTC array before
    # the monthly expansion; no-op off the flag or for non-PJM ISOs.
    if getattr(config, "pjm_congestion", False) and iso == "PJM":
        from market_sim.config.constants import PJM_MEASURED_INTERNAL_TTC

        ttc = ttc.copy()
        for i, link in enumerate(iso_config.links):
            measured = PJM_MEASURED_INTERNAL_TTC.get((link.from_zone, link.to_zone))
            if measured is not None and measured != ttc[i]:
                logger.info(
                    "PJM congestion: internal TTC %s->%s %.0f -> %.0f MW "
                    "(measured transfer-limit posting)",
                    link.from_zone,
                    link.to_zone,
                    ttc[i],
                    measured,
                )
                ttc[i] = measured
    # Seasonal interface envelope: expand the scalar TTC to a per-hour matrix
    # where a measured monthly limit exists (NYISO Central-East). No-op (1-D)
    # for ISOs/years without one.
    ttc = _apply_iso_monthly_ttc(ttc, iso_config, iso, year, demand.shape[1])
    # Measured ERCOT GTC export limits (backcast overlay, ScenarioConfig.
    # ercot_gtc_limits_measured): the GTC-carrying links' export direction
    # follows the hourly NP6-86 measured limit series so West/Panhandle
    # curtailment emerges endogenously from the binding published limits.
    # Applied only when the year ALSO has measured HSL renewable potential —
    # without it the renewable upper bound is the delivered actuals
    # (EIA-930-as-CF) and any binding export cap would double-curtail wind
    # below what really flowed. The import direction keeps the static rating
    # (a GTC is an export stability limit).
    ttc_import = None
    if getattr(config, "ercot_gtc_limits_measured", False) and iso == "ERCOT":
        from market_sim.data.gtc import ercot_gtc_ttc_hourly

        if load_hsl_hourly(iso, year) is None:
            logger.warning(
                "ercot_gtc_limits_measured: %d has no measured HSL potential "
                "(renewables ride delivered-as-CF) — measured GTC limits "
                "skipped for this year to avoid double-curtailment",
                year,
            )
        else:
            gtc_out = ercot_gtc_ttc_hourly(
                np.asarray(ttc, dtype=float), iso_config, year, demand.shape[1]
            )
            if gtc_out is None:
                logger.warning(
                    "ercot_gtc_limits_measured: no gtc-limits clean partition "
                    "for %d — static TTC kept (supply the NP6-86 archives and "
                    "run scripts/curate_gtc_limits.py)",
                    year,
                )
            else:
                ttc, ttc_import = gtc_out
    # Aggregate interface limits (CAISO's simultaneous WECC import cap): resolve
    # the configured link groups to flow-column indices for the LP. Empty (no
    # extra rows) for ISOs without an interface_limits entry.
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )
    # MISO per-zone seasonal CIL/CEL deliverability groups: replace the static
    # summer ``MISO_CIL_*`` fallbacks baked into _miso_config with per-season
    # hourly caps from the LOLE Study Report data (scope decision D7 — the
    # NYISO monthly-TTC pattern, fed from data/capacity_deliverability instead
    # of a constants table). Always on for MISO: the measured seasonal limits
    # ARE the internal congestion structure (rule #10-admissible — they
    # regenerate every planning year from forward drivers). Falls back to the
    # static summer caps when the clean partition is absent (never silent-zero).
    if iso == "MISO":
        from market_sim.model.transmission import build_miso_deliverability_groups

        seasonal_groups = build_miso_deliverability_groups(
            iso_config.links, year, demand.shape[1]
        )
        if seasonal_groups:
            static_limits = [
                lim
                for lim in iso_config.interface_limits
                if not lim.name.startswith("MISO_CIL_")
            ]
            interface_groups = (
                build_interface_groups(iso_config.links, static_limits)
                + seasonal_groups
            )
            logger.info(
                "MISO %d: seasonal CIL/CEL interface caps on %d zone group(s) "
                "(per-season hourly vectors from the LOLE deliverability data; "
                "static summer fallbacks replaced)",
                year,
                len(seasonal_groups),
            )
        else:
            logger.warning(
                "MISO %d: capacity-deliverability clean partition absent — "
                "falling back to static PY2025-26 summer CIL/CEL caps; run "
                "scripts/curate_capacity_deliverability.py",
                year,
            )
    # [measured: EIA-930 per-corridor (month × hour-of-day) p95 net-flow
    #  envelope → corridor import/export caps | forecast substitute:
    #  caiso_corridor_atc_forward — the shared
    #  transmission.forward_corridor_interface_groups capability envelope,
    #  which the forecast runner also wires (Stage 5); the measured branch
    #  below is a backcast overlay, plan §3.1]
    # Measured WECC corridor deliverability envelope (CAISO per-hub only): cap
    # each corridor link's import-direction flow at the per-(month × hour-of-day)
    # p95 measured net import (an ATC proxy that tightens midday), so the LP can
    # no longer pull the neighbors' idle thermal tranches over the cheap-priced
    # hub up to the 8.3 GW simultaneous cap. One-sided hourly upper bounds, added
    # to the interface groups; export keeps the physical TTC. No-op off the flag
    # or when the year has no measured interchange (byte-identical).
    forward_atc = caiso_corridors and getattr(
        config, "caiso_corridor_atc_forward", False
    )
    if forward_atc or (
        caiso_corridors and getattr(config, "caiso_corridor_flow_limit", False)
    ):
        from market_sim.model.transmission import build_caiso_corridor_flow_groups

        corridor_export_env = (
            None  # measured branch fills it; forward ATC leaves it off
        )
        if forward_atc:
            # FORWARD ATC: corridor TTC × posted-ATC base fraction × forward solar
            # derate (CISO solar / demand), a capability limit — not the measured
            # p95 flow (CLAUDE.md #12). Supersedes the measured envelope when on.
            from market_sim.model.transmission import forward_corridor_atc_envelope

            corridor_env = forward_corridor_atc_envelope(
                iso_config, iso, year, demand.shape[1]
            )
            cap_label = "FORWARD ATC (TTC × ATC-frac × solar derate)"
        else:
            from market_sim.data.eia_loader import measured_corridor_flow_envelope

            corridor_env = measured_corridor_flow_envelope(iso, year, demand.shape[1])
            # Symmetric measured export-deliverability ceiling: caps each
            # corridor's export (negative) flow at its p95 net export, which
            # collapses to ~0 in the evening ramp where the corridor reliably
            # net-imports — forbidding the LP's unphysical evening wheel-out of
            # cheap CA gas that over-dispatched CC_REGULAR and inflated the
            # evening LMP. A capability envelope the LP clears below, not the
            # hourly residual (rule #12).
            corridor_export_env = measured_corridor_flow_envelope(
                iso, year, demand.shape[1], direction="export"
            )
            from market_sim.config.interchange_config import (
                CAISO_CORRIDOR_FLOW_PERCENTILE,
            )

            cap_label = f"measured p{CAISO_CORRIDOR_FLOW_PERCENTILE:g} ATC proxy"
        if corridor_env:
            corridor_groups = build_caiso_corridor_flow_groups(
                iso_config.links,
                corridor_env,
                export_envelope=None if forward_atc else corridor_export_env,
            )
            interface_groups = interface_groups + corridor_groups
            exp_note = ""
            if corridor_export_env:
                exp_note = (
                    "; export-direction cap on (evening net-export ~0 → no wheel-out): "
                    f"median export DSW {float(np.median(corridor_export_env.get('WECC_DSW', [np.nan]))) / 1000.0:.1f} GW "
                    f"/ PNW {float(np.median(corridor_export_env.get('WECC_PNW', [np.nan]))) / 1000.0:.1f} GW"
                )
            logger.info(
                "%s %d: WECC corridor deliverability cap on %d link(s) — %s; "
                "median import DSW %.1f GW / PNW %.1f GW; midday tighter%s",
                iso,
                year,
                len(corridor_groups),
                cap_label,
                float(np.median(corridor_env.get("WECC_DSW", [np.nan]))) / 1000.0,
                float(np.median(corridor_env.get("WECC_PNW", [np.nan]))) / 1000.0,
                exp_note,
            )

    # PJM congestion lever (Lever A): cap each PJM_external→border link's signed
    # flow per hour at the measured per-border net-interchange envelope, so the
    # priced external star node can no longer wheel ~30 GW uncongested into the 5
    # border zones (the copper-plate bypass). Mirrors the CAISO corridor cap
    # (asymmetric per-hour interface groups); no-op off the flag, for non-PJM, or
    # when the measured tie file is absent (byte-identical).
    if getattr(config, "pjm_congestion", False) and iso == "PJM" and priced_interchange:
        from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
        from market_sim.config.interchange_config import IMPORT_ZONE
        from market_sim.data.eia_loader import pjm_zonal_interchange_envelope
        from market_sim.model.transmission import build_pjm_external_flow_groups

        env = pjm_zonal_interchange_envelope(
            year, zone_names, demand.shape[1], PJM_EXTERNAL_FLOW_PERCENTILE
        )
        if env is not None:
            import_cap, export_cap = env
            ext_groups = build_pjm_external_flow_groups(
                iso_config.links, import_cap, export_cap, zone_names
            )
            interface_groups = interface_groups + ext_groups
            # Per-border median caps (GW) for the log: dominant direction generous,
            # minor direction ~0 (EMAAC import / Dominion export / interior zones).
            border_rows = {
                ln.to_zone
                for ln in iso_config.links
                if ln.from_zone == IMPORT_ZONE.get("PJM")
            }
            zone_idx = {z: i for i, z in enumerate(zone_names)}
            cap_note = "; ".join(
                f"{z.replace('PJM_', '')} imp {np.median(import_cap[zone_idx[z]]) / 1000.0:.1f}"
                f"/exp {np.median(export_cap[zone_idx[z]]) / 1000.0:.1f} GW"
                for z in sorted(border_rows)
                if z in zone_idx
            )
            logger.info(
                "PJM %d: external-node deliverability cap (p%g) on %d link(s) — %s",
                year,
                PJM_EXTERNAL_FLOW_PERCENTILE,
                len(ext_groups),
                cap_note,
            )

    # Commercial-operation-date (COD) vintage ramp: in a backcast the fleet
    # snapshot is a recent vintage that includes units built after the solved
    # year. The ramp is now applied uniformly inside generators_to_fleet_arrays
    # (config.cod_ramp_enabled, default on) via the month-precise EIA-860
    # plant-code map — covering the ERCOT CAMPD bins and every raw EIA-860 unit
    # alike — so the per-fleet-path scaling that used to live here is gone. See
    # data.cod_ramp.

    # Whole-plant exits that retired mid-window (e.g. Mystic) are absent from
    # the single recent operable snapshot, so the COD ramp has nothing to age
    # out. Inject them into the backcast fleet base — the ramp
    # (generators_to_fleet_arrays) then dispatches each through its real
    # retirement month and zeros it after. Mirror of forecast's planned
    # additions; backcast-mode only (run_calibration is always backcast). The
    # year selects the active EIA-860 vintage; a year-matched native vintage
    # carries these exits in its own operable file and ships no retiree parquet,
    # so this returns nothing there (no double-count).
    retired_units = (
        load_retired_within_window(iso, iso_config, year=year)
        if config.mode == "backcast"
        else []
    )

    # Build the dispatch fleet the same way the runner does: CAMPD
    # operational bins for ERCOT (three stepped tranches per bin, nuclear
    # and other non-aggregatable units from EIA-860), the legacy
    # equal-width heat-rate binning otherwise.
    campd_bins = (
        load_campd_bins(
            config.campd_bins_path,
            year=year,
            capacity_reconcile_path=(
                config.cc_capacity_reconcile_path
                if config.cc_capacity_reconcile
                else None
            ),
        )
        if config.use_campd_bins and iso == "ERCOT"
        else None
    )
    if campd_bins is not None:
        campd_fleet, _ = bins_to_fleet(campd_bins, zone_names, config)
        # Gas/coal are dispatched via the CAMPD bins; biomass is injected as a
        # must-run resource (run_calibration_full), so neither is added as a raw
        # unit here. Oil is kept as its own raw LP unit so it dispatches as the
        # scarcity peaker it is (its fuel price / heat rate come from constants).
        _campd_binned_or_injected = {"gas_cc", "gas_ct", "coal", "biomass"}
        non_thermal = [
            g
            for g in (load_fleet_from_csv(iso, iso_config, year=year) + retired_units)
            if g.fuel_type not in _campd_binned_or_injected
        ]
        fleet = non_thermal + campd_fleet
        # Must-run tranches bid at VOM + carbon + NOx only — fuel sunk
        # under take-or-pay coal contracts, CHP host steam obligations or
        # ERCOT RUC. Above must-run, each coal tranche passes its own
        # supply chain's passthrough — flat scalar, or an (T,) gas-keyed
        # sigmoid resolved per (ISO, supply) — so baseloaded coal clears
        # the merit order instead of being priced out by cheap gas.
        # apply_coal_tranches applies the discounts/markups.
        pt_by_supply = coal_passthrough_by_supply(config, year, config.hours)
        # Measured take-or-pay (contract) share per coal plant: when on, the
        # coal must-run tranche's sunk fraction is the EIA-923 Schedule-5
        # Purchase Type share instead of the hardcoded 100% (campd_tranche_fuel_frac).
        takeorpay = _takeorpay_by_plant(fleet, config)
        if config.coal_prb_passthrough_sigmoid and config.coal_prb_passthrough_tiered:
            # Tiered PRB (ERCOT): low-must-run "prb" load-followers swap
            # the baseload prb curve for the follower-tier one. The tier
            # split is specific to the curated ERCOT prb supply.
            foll = {
                **pt_by_supply,
                "prb": prb_follower_passthrough_series(config, year, config.hours),
            }
            thr = config.coal_prb_follower_mustrun_max

            def _pt_for(g):
                if (
                    g.fuel_type == "coal"
                    and getattr(g, "coal_supply", "") == "prb"
                    and COAL_MUSTRUN_BY_PLANT.get(g.plant_code, 100.0) <= thr
                ):
                    return foll
                return pt_by_supply

            fuel_fracs = [
                campd_tranche_fuel_frac(g, _pt_for(g), takeorpay) for g in fleet
            ]
        else:
            fuel_fracs = [
                campd_tranche_fuel_frac(g, pt_by_supply, takeorpay) for g in fleet
            ]
    else:
        # Per-plant calibration fleet (plant_level_fleet) keeps each EIA-860
        # unit as its own LP column so plant_code / plant_group / state carry
        # into dispatch — required for per-plant EIA-923 fuel costs and the
        # CAMPD outage overlay to bind. Otherwise use the legacy efficiency-
        # bin aggregation (faster, but identity-free).
        #
        # When the ISO has a CAMPD-derived thermal-tranche artifact
        # (thermal_tranches_<ISO>.csv), give its per-plant thermal fleet the
        # SAME smoothed rising offer curve ERCOT gets: build a synthetic
        # per-plant bins frame (committed / coal must-run from the artifact)
        # and route it through bins_to_fleet, with every non-binned generator
        # (nuclear, oil, biomass, hydro, ...) kept as its own raw LP unit. The
        # binned-keys exclusion guarantees no double-count and no dropped unit.
        if getattr(config, "plant_level_fleet", False) and thermal_tranche_overrides(
            iso
        ):
            all_gens = load_fleet_from_csv(iso, iso_config, year=year) + retired_units
            synth = fleet_to_bins(all_gens, iso, config)
            if not synth.empty:
                binned = set(zip(synth["Plant_Code"].astype(int), synth["Plant_Group"]))
                thermal_fleet, _ = bins_to_fleet(synth, zone_names, config)
                non_binned = [
                    g
                    for g in all_gens
                    if (int(g.plant_code), g.plant_group) not in binned
                ]
                fleet = non_binned + thermal_fleet
                pt_by_supply = coal_passthrough_by_supply(config, year, config.hours)
                fuel_fracs = [campd_tranche_fuel_frac(g, pt_by_supply) for g in fleet]
            else:
                fleet, fuel_fracs = split_coal_tranches(
                    aggregate_fleet(all_gens, n_bins=0), config
                )
        else:
            n_bins = (
                0
                if getattr(config, "plant_level_fleet", False)
                else config.heat_rate_bin_count
            )
            fleet_base = aggregate_fleet(
                load_fleet_from_csv(iso, iso_config, year=year) + retired_units,
                n_bins=n_bins,
            )
            fleet, fuel_fracs = split_coal_tranches(fleet_base, config)
            # Optional stepped gas offer curve (committed/economic/peaking
            # heat-rate bands) for the per-plant fleet; off by default.
            if getattr(config, "gas_offer_curve", False):
                fleet, fuel_fracs = split_gas_tranches(fleet, fuel_fracs, config)
    # Biomass injected as a measured EIA-923 must-run profile (the caller nets it
    # out of demand and re-adds it as a fixed pseudo-unit), so drop the raw
    # biomass LP units to avoid double-serving — and to make biomass output the
    # fuel/contract-limited, price-insensitive quantity it is in reality instead
    # of a dispatchable unit the LP runs to max when gas rises. Mirrors the ERCOT
    # CAMPD path, which already excludes biomass from its fleet (_campd_binned_-
    # or_injected). Gated on inject_biomass_mustrun so callers that do NOT inject
    # biomass (overlay-derivation / probe scripts) keep biomass as an LP unit and
    # never lose it. No-op for ERCOT (its fleet already carries no biomass unit).
    if inject_biomass_mustrun:
        fleet, fuel_fracs = _drop_biomass_units(fleet, fuel_fracs)
    # Energy-limited conventional hydro (every ISO): one LP unit per
    # EIA-923-reporting hydro plant, capped by its EIA-860 nameplate per hour
    # and by its measured monthly net generation via the dispatch LP's hydro
    # budget rows. Replaces the flat-monthly must-run injection (which could
    # not peak-shave) and leaves ISOs without hydro data unchanged.
    hydro_units, hydro_monthly_energy = build_hydro_fleet(
        iso,
        year,
        zone_names,
        backfill_year=hydro_backfill_year,
        eia930_monthly=hydro_eia930_monthly,
        forecast_budget=hydro_forecast_budget,
        hydro_year=hydro_year,
    )
    hydro_gen_idx = None
    if hydro_units:
        hydro_gen_idx = np.arange(len(fleet), len(fleet) + len(hydro_units), dtype=int)
        fleet = fleet + hydro_units
        fuel_fracs = list(fuel_fracs) + [1.0] * len(hydro_units)
        logger.info(
            "%s %d: %d hydro plants in LP (%.0f MW, %.2f TWh monthly budget)",
            iso,
            year,
            len(hydro_units),
            sum(g.pmax_mw for g in hydro_units),
            hydro_monthly_energy.sum() / 1e6,
        )
    if import_generators:
        fleet = fleet + import_generators
        fuel_fracs = list(fuel_fracs) + [1.0] * len(import_generators)
        logger.info(
            "%s %d: priced import/export node — %d import tranches "
            "(%.0f MW), %d export sinks (%.0f MW)",
            iso,
            year,
            sum(1 for g in import_generators if g.pmax_mw > 0),
            sum(g.pmax_mw for g in import_generators),
            sum(1 for g in import_generators if g.pmin_mw < 0),
            -sum(g.pmin_mw for g in import_generators),
        )
    # CT_PEAKER reliability must-run floor: pass the peakers' CAMPD/CEMS hourly
    # on/off shape so the floor starts/stops with the real unit (zero in every
    # hour the plant did not report load), instead of being smeared flat. The
    # parasitic factor only scales magnitude, which the per-month shape
    # normalization removes, so a bare gross series is enough.
    ct_campd_shape = None
    if getattr(config, "ct_mustrun_per_plant", False):
        from market_sim.data import campd as _campd

        _states = _campd.states_for_iso(iso)
        if _states:
            _cdf = _campd.load_campd_hourly(_states, [config.weather_year])
            if not _cdf.empty:
                ct_campd_shape = _campd.plant_hourly_net(
                    _cdf, {}, config.weather_year, hours=config.hours
                )
    fleet_arrays = generators_to_fleet_arrays(
        fleet,
        zone_names,
        hours=config.hours,
        iso=iso,
        config=config,
        load_shape=demand.sum(axis=0),
        ct_campd_shape=ct_campd_shape,
        year=config.weather_year,
    )
    inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)
    # Net-load-indexed ST_GAS reliability-drag floor: hold legacy gas-steam at
    # a minimum-generation floor that rises with system net-load (load - wind -
    # solar) — the operational proxy for the reserve tightness ERCOT RUC keys
    # off — over which the LP dispatches economically. Replaces the blunt
    # seasonal gas_st_summer_mustrun calendar fraction with an endogenous,
    # weather-driven floor (see fleet.apply_gas_st_netload_drag_floor). Net-load
    # uses the same LP-served (net-of-must-run) convention as the runner's other
    # net-load consumers below.
    if getattr(config, "gas_st_netload_drag", False) or getattr(
        config, "ct_netload_drag", False
    ):
        net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        if apply_gas_st_netload_drag_floor(fleet_arrays, fleet, net_load, config):
            logger.info(
                "%s %d: ST_GAS net-load reliability-drag floor applied "
                "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f); net-load mean %.0f / "
                "max %.0f MW)",
                iso,
                year,
                config.gas_st_drag_slope_per_gw,
                config.gas_st_drag_intercept,
                config.gas_st_drag_cap,
                float(net_load.mean()),
                float(net_load.max()),
            )
        # CT_PEAKER net-load reliability-drag floor (simple-cycle analog), gated
        # to the afternoon-evening ramp window — the forward-native replacement
        # for the ct_mustrun_per_plant actuals pin. See
        # fleet.apply_ct_netload_drag_floor.
        if apply_ct_netload_drag_floor(fleet_arrays, fleet, net_load, config):
            logger.info(
                "%s %d: CT_PEAKER net-load reliability-drag floor applied "
                "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f) in ramp %dh-%dh)",
                iso,
                year,
                config.ct_drag_slope_per_gw,
                config.ct_drag_intercept,
                config.ct_drag_cap,
                config.ct_drag_ramp_start,
                config.ct_drag_ramp_end,
            )
    # ══════════════════════════════════════════════════════════════════════
    # BACKCAST MEASURED INTERCHANGE OVERLAYS — availability / seam limits.
    # Every block below feeds a MEASURED series into the priced node's bounds
    # (CLAUDE.md rule 12: reproducible capability envelopes, never an outcome
    # pin) and is backcast-only by design (plan §3.1). None is reachable from
    # the forecast path: the forecast substitutes are noted per overlay.
    # The forward-native interchange injections live in the SHARED
    # transmission.apply_interchange_injections, called below after the mc
    # assembly (both orchestrators run it).
    # ══════════════════════════════════════════════════════════════════════
    # [measured: EIA-930 CISO diurnal interchange envelope → import/export
    #  availability shape | forecast substitute: none — the reference-price /
    #  per-hub seams price the diurnal signal instead of bounding it]
    # Shape the priced import/export node by the measured EIA-930 diurnal
    # interchange envelope (import overnight, export the midday solar glut) so
    # the node stops clearing a flat all-hours import that floors the midday
    # price. Only fires with priced interchange + the opt-in flag + a measured
    # envelope; otherwise the static node is unchanged.
    if priced_interchange and getattr(config, "interchange_shaping", False):
        from market_sim.model.transmission import inject_interchange_shape

        export_only = getattr(config, "interchange_shaping_export_only", False)
        # Per-direction envelope percentile is a ScenarioConfig field (rule
        # 24 — was an os.environ INTERCHANGE_SHAPE_IMPORT_PCT/EXPORT_PCT read
        # inside inject_interchange_shape), so the value that ran is recorded
        # in run_config.json. Both default to 90.0, reproducing the env-unset
        # behavior of every run to date.
        import_pct = getattr(config, "interchange_shape_import_pct", 90.0)
        export_pct = getattr(config, "interchange_shape_export_pct", 90.0)
        if inject_interchange_shape(
            fleet_arrays,
            iso,
            year,
            export_only=export_only,
            import_percentile=import_pct,
            export_percentile=export_pct,
        ):
            logger.info(
                "%s %d: priced node shaped by measured EIA-930 interchange "
                "envelope (%s, import p%g / export p%g)",
                iso,
                year,
                "export midday only — imports uncapped"
                if export_only
                else "import overnight / export midday",
                import_pct,
                export_pct,
            )
    # [measured: EIA-930 MISO BA-to-BA net-import envelope → seam import cap |
    #  forecast substitute: the seam's interface_limit_mw + reference prices]
    # MISO reference-price seam deliverability cap: bound each seam's
    # (PJM/SPP/South) import-band availability at the measured EIA-930 BA-to-BA
    # net-import envelope, so the model stops over-importing on the SPP/southern
    # borders MISO actually nets ~0 / net-EXPORTS over. One-sided import ceiling;
    # export bands keep their priced economics. No-op off the flag, for non-MISO,
    # or when the year has no measured interchange (byte-identical).
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "miso_seam_flow_limit", False
    ):
        from market_sim.model.transmission import inject_miso_seam_flow_limit

        # Optional round-2 import-lift: raise the deliverability percentile so the
        # priced seam clears more import in tight hours (None keeps the p90
        # default). Still a measured-duration-curve ceiling, not a residual pin.
        _seam_pct = getattr(config, "miso_seam_flow_percentile", None)
        if inject_miso_seam_flow_limit(fleet_arrays, iso, year, percentile=_seam_pct):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured EIA-930 "
                "BA-to-BA deliverability envelope (p%g; SPP/South clip toward "
                "~0 import, PJM keeps its measured eastern transfer)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE if _seam_pct is None else _seam_pct,
            )
    # Export mirror: cap each seam's net EXPORT at the measured net-export
    # envelope by raising the export bands' lower bound toward 0. Clips the PJM
    # seam (which MISO net-imports over) to ~0 export, removing the spurious
    # export of cheap MISO coal back east; SPP/South keep their measured export
    # headroom. Shares the import cap's percentile (one envelope, both
    # directions). No-op off the flag, for non-MISO, or with no measured year.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "miso_seam_export_limit", False
    ):
        from market_sim.model.transmission import inject_miso_seam_flow_limit

        _seam_pct = getattr(config, "miso_seam_flow_percentile", None)
        if inject_miso_seam_flow_limit(
            fleet_arrays, iso, year, percentile=_seam_pct, direction="export"
        ):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam export capped at measured EIA-930 "
                "BA-to-BA net-export envelope (p%g; PJM seam clips export toward "
                "~0, SPP/South keep their measured export headroom)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE if _seam_pct is None else _seam_pct,
            )
    # [measured: PJM tie-line per-neighbor flow envelope → seam import cap |
    #  forecast substitute: the seam's interface_limit_mw + reference prices]
    # PJM seam import cap: cap each of PJM's 5 reference-price seams' import
    # bands at the measured per-neighbor deliverability envelope (PJM tie-line
    # file, aggregated from border zones to neighbor level). Fixes the ~38 TWh
    # over-export by capping the LP's simultaneous full-TTC export on all 5
    # seams. No-op off the flag, for non-PJM, or with no measured tie file.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "pjm_seam_flow_limit", False
    ):
        from market_sim.model.transmission import inject_pjm_seam_flow_limit

        _pjm_pct = getattr(config, "pjm_seam_flow_percentile", None)
        if inject_pjm_seam_flow_limit(
            fleet_arrays, iso, year, zone_names, hours, percentile=_pjm_pct
        ):
            from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured PJM "
                "tie-line deliverability envelope (p%g); each neighbor's "
                "import bands derated to border-zone summed envelope",
                iso,
                year,
                PJM_SEAM_FLOW_PERCENTILE if _pjm_pct is None else _pjm_pct,
            )
    # PJM seam export cap: symmetric mirror — cap each seam's net export at
    # the measured per-neighbor export envelope.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "pjm_seam_export_limit", False
    ):
        from market_sim.model.transmission import inject_pjm_seam_flow_limit

        _pjm_pct = getattr(config, "pjm_seam_flow_percentile", None)
        if inject_pjm_seam_flow_limit(
            fleet_arrays,
            iso,
            year,
            zone_names,
            hours,
            percentile=_pjm_pct,
            direction="export",
        ):
            from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam export capped at measured PJM "
                "tie-line net-export envelope (p%g); each neighbor's export "
                "bands floored to border-zone summed envelope",
                iso,
                year,
                PJM_SEAM_FLOW_PERCENTILE if _pjm_pct is None else _pjm_pct,
            )
    # ── end of the backcast measured interchange overlays (availability) ──
    # (the measured PRICE overlays live in _backcast_measured_interchange_
    # prices below, threaded into the shared injection sequence; the measured
    # NYISO reconciliation band and CAISO corridor envelopes are built at
    # their structural call sites further down, labelled the same way.)
    # CAISO RA must-offer floor: hold the gas fleet online midday at the
    # measured EIA-930 NG: NG profile (frac-scaled) so the model goes LONG and
    # its surplus exports/curtails at ~$0 (mirrors inject_interchange_shape).
    if getattr(config, "caiso_gas_commitment_floor", False):
        from market_sim.model.transmission import (
            inject_caiso_gas_commitment_floor,
        )

        frac = float(getattr(config, "caiso_gas_floor_frac", 1.0))
        if inject_caiso_gas_commitment_floor(fleet_arrays, iso, year, frac):
            logger.info(
                "%s %d: RA must-offer floor — gas fleet held online midday at "
                "%.2f x measured EIA-930 NG: NG (long-midday floor)",
                iso,
                year,
                frac,
            )

    # ── Generic registry-driven reliability floor ──────────────────────────
    # One flag, one engine, one registry: every enabled (zone, class, driver)
    # limb in RELIABILITY_FLOOR_REGISTRY[iso] (seeded from the derived
    # reliability_floor_coeffs_<ISO>.csv) is applied by the single ISO-agnostic
    # engine. Per-run overrides (config.reliability_floor_overrides) can toggle
    # or re-tune individual limbs without editing the registry.
    if getattr(config, "reliability_floor", False):
        from market_sim.config.iso_configs import (
            RELIABILITY_FLOOR_REGISTRY,
            apply_reliability_floor_overrides,
            drop_drag_owned_reliability_specs,
        )
        from market_sim.model.transmission import inject_reliability_floor

        _floor_specs = apply_reliability_floor_overrides(
            RELIABILITY_FLOOR_REGISTRY.get(iso, []),
            getattr(config, "reliability_floor_overrides", None),
        )
        # Rule 19: when a net-load drag owns a class's commitment (CT_PEAKER via
        # ct_netload_drag), drop that class's reliability-floor limbs so the two
        # do not stack into an all-day floor binding overnight (the D-4
        # off-window failure; docs/FINDING-pjm-burndown-2026-07.md). No-op when
        # no drag is active, so non-drag ISOs/runs are byte-identical.
        _n_before = len(_floor_specs)
        _floor_specs = drop_drag_owned_reliability_specs(_floor_specs, config)
        if len(_floor_specs) < _n_before:
            logger.info(
                "%s %d: reliability floor — dropped %d drag-owned limb(s) "
                "(CLAUDE.md rule 19: net-load drag owns the class commitment)",
                iso,
                year,
                _n_before - len(_floor_specs),
            )
        if _floor_specs and inject_reliability_floor(
            fleet_arrays,
            iso,
            year,
            _floor_specs,
            zone_names,
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
        ):
            logger.info(
                "%s %d: reliability floor — %d enabled limb spec(s) applied "
                "from RELIABILITY_FLOOR_REGISTRY",
                iso,
                year,
                sum(1 for s in _floor_specs if getattr(s, "enabled", True)),
            )

    # NEISO winter gas-availability derate (temperature-dependent forced outage):
    # on cold snaps the gas-electric constraint makes non-dual-fuel gas-CC/CT
    # capacity physically UNAVAILABLE, so the fleet goes reserve-short and the
    # RCPF co-opt prices the >$300 scarcity tail (and widens the storage spread).
    # Must run before the reserve-coopt inputs are built so the shared-headroom
    # RHS sees the derated availability (transmission.inject_neiso_gas_coldsnap_
    # derate). Dual-fuel units are excluded (they switch to oil, not vanish).
    if getattr(config, "neiso_gas_coldsnap_derate", False):
        from market_sim.model.transmission import inject_neiso_gas_coldsnap_derate

        if inject_neiso_gas_coldsnap_derate(
            fleet_arrays,
            iso,
            year,
            float(getattr(config, "neiso_gas_derate_t0_c", -7.0)),
            float(getattr(config, "neiso_gas_derate_slope_per_c", 0.018)),
            float(getattr(config, "neiso_gas_derate_cap", 0.20)),
        ):
            logger.info(
                "%s %d: winter gas-availability derate — non-dual-fuel gas-CC/CT "
                "availability cut by clip(slope*(t0-TMIN),0,cap) over the cold-snap "
                "window (TDFOR, NERC cold-weather anchored)",
                iso,
                year,
            )

    # NYISO firm import baseload (HQ/Ontario must-flow) and the Manitoba
    # firm-hydro floor now run inside the SHARED
    # transmission.apply_interchange_injections below — contract-structure
    # floors, forward-native, reachable from both orchestrators (Stage 5).

    # [measured: EIA-930 NYISO monthly net-interchange schedule → monthly LP
    #  band | forecast substitute: config.nyiso_forward_net_import_twh —
    #  build_import_node_reconciliation is mode-aware, the runner passes
    #  mode="forecast"]
    # NYISO priced-node boundary-flow reconciliation: pin the priced node's
    # MONTHLY net interchange to the measured EIA-930 schedule via a per-month
    # band constraint in the LP (transmission.build_import_node_reconciliation ->
    # dispatch._build_import_node_rows). The near-static economic tranche ladder
    # clears a near-flat ~18.5-21.6 TWh that does not track the metered
    # schedule's 23.45 -> 20.35 -> 19.09 TWh decline; the band replaces that
    # economic estimate with the authoritative measurement (CLAUDE.md rule #11),
    # priced tranches still setting the marginal price within each month's
    # envelope. Only fires with priced interchange + the flag + a priced node.
    import_node_recon = None
    if priced_interchange and getattr(config, "nyiso_import_reconciliation", False):
        from market_sim.model.transmission import build_import_node_reconciliation

        # Mode-aware band target: backcast -> measured EIA-930 schedule
        # (calibration always sets mode="backcast", so this is byte-identical to
        # the prior behaviour); forecast -> the neighbor's forecast net position
        # (config.nyiso_forward_net_import_twh), shaped to monthly by the
        # forecast load, else relaxed to the bare priced-seam economics.
        import_node_recon = build_import_node_reconciliation(
            fleet_arrays,
            iso,
            year,
            mode=getattr(config, "mode", "backcast"),
            forward_net_import_twh=getattr(
                config, "nyiso_forward_net_import_twh", None
            ),
            system_demand=demand,
        )
        if import_node_recon is not None:
            node_idx, recon_lo, recon_hi = import_node_recon
            _recon_target = (
                "the neighbor's forecast net position"
                if getattr(config, "mode", "backcast") == "forecast"
                else "measured EIA-930 net interchange"
            )
            logger.info(
                "%s %d: priced import node reconciled to %s — %d node rows, "
                "annual band [%.2f, %.2f] TWh",
                iso,
                year,
                _recon_target,
                int(node_idx.size),
                recon_lo.sum() / 1e6,
                recon_hi.sum() / 1e6,
            )

    # NYISO Long Island local self-supply floor: force the cable-islanded LI
    # pocket to meet a forward fraction of its own load with in-zone thermal
    # generation rather than importing cheap NYC gas (transmission.
    # inject_nyiso_local_selfsupply). NYISO-only; scales with load.
    if getattr(config, "nyiso_local_selfsupply", False):
        from market_sim.model.transmission import inject_nyiso_local_selfsupply

        if inject_nyiso_local_selfsupply(fleet_arrays, iso, demand, zone_names):
            logger.info(
                "%s %d: local self-supply floor applied to downstate pocket(s) "
                "(LMIC / cable-islanded local reliability)",
                iso,
                year,
            )

    # Fuel prices: gas/coal base, then the lignite/PRB supply base for coal
    # (our costs), then the actual EIA-923 monthly per-plant delivered cost
    # on top — so measured monthly cost takes precedence and the supply
    # trajectory is only the base/fallback for plant-months without data.
    fuel_prices = resolve_fuel_prices(config, fleet_arrays, year, apply_monthly=False)
    if config.coal_supply_repricing:
        apply_coal_supply_pricing(fuel_prices, fleet, config, year)
    apply_plant_monthly_fuel_prices(fuel_prices, fleet_arrays, config, year)
    # Hub-basis overlay (NEISO only): replace the gas price with the measured
    # Algonquin Citygate hub spot in covered months — daily-resolved when
    # gas_hub_basis_daily is on. Because run_year resolves fuel prices with
    # apply_monthly=False (so the coal-supply base lands before the per-plant
    # EIA-923 overwrite), the overlay that resolve_fuel_prices runs in its
    # apply_monthly=True branch must be re-applied here, mirroring that branch's
    # order: plant-monthly, then hub overlay, then the dual-fuel min. No-op
    # unless gas_hub_basis_overlay is set (and basis rows exist), so non-NEISO
    # runs are unchanged.
    apply_hub_basis_overlay(fuel_prices, fleet_arrays, config, year)
    # NYISO per-zone gas-hub basis: shift each gas unit to its region's pipeline
    # index so the east marginal gas stays dearer than the west (the structural
    # source of the upstate-cheap / east-dear spread). Mirrors the
    # resolve_fuel_prices apply_monthly=True order: after the plant-monthly /
    # hub overlay, before the dual-fuel min so oil parity still caps any winter
    # spike. No-op unless nyiso_zonal_gas_basis is set (NYISO only).
    apply_nyiso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # NYISO downstate CT-peaker interruptible city-gate gas premium: lift each
    # NYC / Long Island CT_PEAKER unit's delivered gas by the measured monthly
    # LDC city-gate premium (summer-peaked interruptible-gas scarcity these
    # non-firm peakers face) so an efficient LM6000 no longer undercuts the
    # dearer downstate steam fleet on flat hub gas (issue #1344 / B-NYI-1). Same
    # order as the other basis overlays: after the zonal basis, before the
    # dual-fuel oil-parity min. No-op unless nyiso_downstate_ct_gas_basis is set
    # (NYISO only). See fuel.apply_nyiso_downstate_ct_gas_basis.
    apply_nyiso_downstate_ct_gas_basis(fuel_prices, fleet_arrays, config, year)
    # ERCOT per-zone gas-hub basis: shift each gas unit to its zone's measured
    # regional hub (Waha-cheap West/Permian, dearer North/East-Texas and South)
    # so the merit order stops over-running DFW/North CCs on flat Waha-discounted
    # gas. Mean-zero anchored so the aggregate gas level is preserved. Same order
    # as the resolve_fuel_prices apply_monthly=True branch: after the
    # plant-monthly / hub overlay, before the dual-fuel min. No-op unless
    # ercot_zonal_gas_basis is set (ERCOT only).
    apply_ercot_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # PJM per-zone gas basis: shift each gas unit to its zone's measured regional
    # delivered-to-electric-power basis (west coal belt cheap, eastern
    # EMAAC/SWMAAC/Dominion dear) so PJM stops clearing as a single copper-plate —
    # the internal TTCs bind, eastern LMP separates up, eastern CCs back off and
    # western coal serves the east. Capacity-weighted mean-zero so the aggregate
    # gas level is preserved. Same order as the resolve_fuel_prices
    # apply_monthly=True branch: after the plant-monthly / hub overlay, before the
    # dual-fuel min. No-op unless pjm_zonal_gas_basis is set (PJM only).
    apply_pjm_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # MISO per-zone gas basis (north/south gas gradient). Same mean-zero core as
    # PJM. No-op unless miso_zonal_gas_basis is set (MISO only).
    apply_miso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # Net-load-indexed West/Panhandle Waha shape: redistribute the West gas basis
    # across hours (firm at high net-load, collapsed at low) so peakers — which
    # burn only in scarcity hours — see firm Waha and idle, while the West CCs on
    # all-hours blended gas stay baseload. Mean-zero so the annual basis above is
    # preserved; structural replacement for the flat delivered-floor scalar. No-op
    # unless ercot_west_netload_gas_shape (+ ercot_zonal_gas_basis) is set, ERCOT.
    if getattr(config, "ercot_west_netload_gas_shape", False):
        west_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        # Endogenous Waha collapse frequency (gap G6): how often forecast West/
        # Panhandle VRE over-supplies the local basin (local load + export TTC).
        # Built from the per-zone VRE capacity×CF, the West load, and the
        # WESTEX+PNHNDL export limit the model already carries — the forward
        # driver that replaces the measured neg_day_freq when
        # ercot_west_gas_endogenous_collapse is on. Always computed so it can be
        # logged against the measured value; the function uses it only when the
        # flag is set.
        waha_zone_idx = [
            i for i, name in enumerate(zone_names) if name in ("West", "Panhandle")
        ]
        west_oversupply_freq = None
        if waha_zone_idx:
            widx = np.array(waha_zone_idx)
            west_vre = (solar_cap[widx, None] * solar_cf[widx]).sum(axis=0) + (
                wind_cap[widx, None] * wind_cf[widx]
            ).sum(axis=0)
            west_local_load = demand[widx].sum(axis=0)
            # Export takeaway: total TTC on links leaving the Waha zones (WESTEX
            # West->North/South_Central + PNHNDL Panhandle->North); the constrained
            # path the surplus must squeeze through before it crashes the hub.
            export_limit = sum(
                link.ttc_mw
                for link in iso_config.links
                if link.from_zone in ("West", "Panhandle")
                and link.to_zone not in ("West", "Panhandle")
            )
            west_oversupply_freq = ercot_west_oversupply_collapse_freq(
                west_vre, west_local_load, export_limit
            )
        apply_ercot_west_netload_gas_shape(
            fuel_prices,
            fleet_arrays,
            config,
            year,
            west_net_load,
            west_oversupply_freq=west_oversupply_freq,
        )
    # Capture which dual-fuel generator-hours will switch to oil (gas price >
    # oil parity) BEFORE the min-cap below overwrites the gas price, so the
    # dispatch re-attribution can count their MWh as petroleum, not gas (the
    # switch itself is objective-only; this is a reporting re-attribution).
    # Gated on dual_fuel_oil_reattribution (NEISO-only) so PJM/NYISO — whose
    # dual-fuel units also switch on their own winter gas — stay byte-identical.
    # Also computed for the winter fuel-inventory budget (Component A), which
    # gates each dual-fuel unit's oil-burn budget to exactly these oil hours so
    # the seasonal stock constraint never caps its gas generation.
    dual_fuel_oil_mask = (
        dual_fuel_switch_mask(fuel_prices, fleet_arrays, config, year)
        if (
            getattr(config, "dual_fuel_oil_reattribution", False)
            or getattr(config, "neiso_winter_fuel_inventory", False)
        )
        else None
    )
    # Dual-fuel switching last, so the oil-parity min sees the final delivered
    # gas price — the AGT-hub winter spot, so the gas->oil switch trips on cold
    # days (NEISO) — not the per-plant monthly cost alone (PJM).
    apply_dual_fuel_pricing(fuel_prices, fleet_arrays, config, year)
    carbon_price = resolve_carbon_price(config, year)
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    # Base marginal cost: fuel + VOM + carbon + NOx, then exogenous EACs,
    # then the coal take-or-pay tranche discount. No startup-cost markup.
    mc_base = assemble_mc(fleet_arrays, fuel_prices, carbon_price, config.nox_price)
    apply_eac_to_mc(mc_base, fleet_arrays, config)
    apply_coal_tranches(mc_base, fleet, fleet_arrays, fuel_fracs, fuel_prices)
    # ── Interchange price/limit injections (orchestrator-unification Stage 5)
    # The forward-native sequence — reference-price seams (generic + CAISO
    # dedicated), firm import/export floors, and the CAISO offer couplings —
    # is the SHARED transmission.apply_interchange_injections, the exact call
    # the forecast runner makes; every step is gated by its existing
    # ScenarioConfig field. The BACKCAST-ONLY measured-price overlays are
    # consolidated below and threaded into the shared sequence at its
    # documented seam point (after the forward base prices, before the
    # couplings — the order the inline code always had). Each overlay names
    # its measured source and forecast substitute (plan §3.1); none is
    # reachable from the forecast path, which passes measured_overlay=None.
    caiso_ref_seam = (
        getattr(config, "caiso_reference_price_seam", False) and iso == "CAISO"
    )
    per_hub_intertie = (
        (not caiso_ref_seam)
        and getattr(config, "caiso_per_hub_intertie", False)
        and iso == "CAISO"
    )
    bidir_intertie = getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO"
    legacy_intertie = not per_hub_intertie and not bidir_intertie

    def _backcast_measured_interchange_prices(fleet_arrays, mc_base) -> None:
        """Backcast measured-price interchange overlays (BOD, plan §3.1).

        Measured hub/border LMP overwrites on the priced node's mc rows —
        each a real delivered price fed as an input (rule 12-admissible), but
        with no forward analogue series, so the forecast substitutes the
        reference-price formula per seam. Runs inside the shared injection
        sequence after the forward base prices and before the couplings.
        """
        # [measured: PJM DA LMP at the MISO-facing western border hubs |
        #  forecast substitute: gas × HR reference price, optionally re-
        #  anchored via miso_pjm_border_anchor]. Overwrites ONLY the PJM seam
        # rows the generic inject_reference_price_mc just priced; SPP/South
        # keep their gas × HR pricing. Measured LMP takes precedence over the
        # border anchor when both are on. No-op without the measured parquet.
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "miso_pjm_lmp_import_pricing", False)
        ):
            from market_sim.model.transmission import (
                inject_miso_pjm_lmp_import_prices,
            )

            if inject_miso_pjm_lmp_import_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: PJM seam repriced to MEASURED hourly PJM "
                    "border-hub DA LMP (CHICAGO GEN / AEP GEN / ATSI GEN "
                    "mean + $%.0f hurdle)",
                    iso,
                    year,
                    next(
                        (
                            n.hurdle
                            for n in INTERFACE_NEIGHBORS.get(iso, [])
                            if n.name == "PJM"
                        ),
                        2.0,
                    ),
                )
        # [measured: WECC intertie hub LMP (Malin / Palo Verde, OASIS) per
        #  corridor | forecast substitute: caiso_intertie_reference_price —
        #  the forward (HH+basis)×HR×load-shape per-hub seam, which the
        #  shared sequence prices INSTEAD of this overlay when set]. The
        # caiso-51 keeper's headline seam: each per-hub corridor priced at
        # its OWN measured hub, firm/contracted tranches held at contract
        # cost under caiso_perhub_firm_base.
        if per_hub_intertie and not getattr(
            config, "caiso_intertie_reference_price", False
        ):
            from market_sim.model.transmission import (
                inject_caiso_per_hub_intertie_prices,
            )

            if inject_caiso_per_hub_intertie_prices(
                fleet_arrays,
                mc_base,
                iso,
                year,
                carbon_price,
                firm_base=getattr(config, "caiso_perhub_firm_base", False),
            ):
                logger.info(
                    "%s %d: per-hub WECC intertie — two signed corridors (Malin/COI "
                    "→ NP15, Palo Verde/Path-46 → SP15), each priced at its OWN "
                    "measured hub (per-hub basis + per-hub netting, arbitrage-free, "
                    "one direction per hour per corridor)%s",
                    iso,
                    year,
                    (
                        " — firm/contracted tranches held at contract cost "
                        "(caiso_perhub_firm_base)"
                        if getattr(config, "caiso_perhub_firm_base", False)
                        else ""
                    ),
                )
        # [measured: WECC intertie hub LMP (MCE, per-hub series averaged to
        #  one) | forecast substitute: none wired — the bidir STRUCTURE is
        #  forward-reachable via the spec; its legs keep the static ladder
        #  prices in a forecast]. Single signed tie, both legs at the hub.
        if not per_hub_intertie and bidir_intertie:
            from market_sim.model.transmission import (
                inject_caiso_bidir_intertie_prices,
            )

            if inject_caiso_bidir_intertie_prices(
                fleet_arrays, mc_base, iso, year, carbon_price
            ):
                logger.info(
                    "%s %d: bidirectional WECC intertie — single signed flow on a "
                    "shared cap, both legs priced at the measured hub (import + "
                    "border carbon / export, arbitrage-free, one direction per hour)",
                    iso,
                    year,
                )
        # [measured: WECC intertie hub LMPs (Mid-C / Palo Verde) on the pooled
        #  legacy node, import + export sides | forecast substitute: the
        #  static ladder / the per-hub or reference seams]. Superseded by the
        # per-hub and bidir nodes; gated to the legacy pooled topology only.
        if legacy_intertie and getattr(config, "caiso_import_hub_prices", False):
            from market_sim.model.transmission import (
                inject_caiso_export_hub_prices,
                inject_caiso_import_hub_prices,
            )

            if inject_caiso_import_hub_prices(
                fleet_arrays, mc_base, iso, year, carbon_price
            ):
                logger.info(
                    "%s %d: import tranches repriced to measured WECC intertie "
                    "hub LMPs (Mid-C / Palo Verde) — static ladder bypassed",
                    iso,
                    year,
                )
            # Symmetric export side of the same bidirectional intertie, so the
            # tie can reverse to the measured +3.5 GW export.
            if inject_caiso_export_hub_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: neighbor-export sink repriced to the measured WECC "
                    "intertie hub LMP — intertie can reverse to export",
                    iso,
                    year,
                )
        # [measured: PJM / ISO-NE Day-Ahead system LMP (hourly) | forecast
        #  substitute: the year-grounded static ladder / a future NYISO
        #  reference seam]. NYISO analogue of the CAISO/MISO measured-hub
        # pricing; the monthly EIA-930 reconciliation band, HQ firm floor and
        # SIL cap are unchanged.
        if (
            iso == "NYISO"
            and priced_interchange
            and getattr(config, "nyiso_import_hub_prices", False)
        ):
            from market_sim.model.transmission import inject_nyiso_import_hub_prices

            if inject_nyiso_import_hub_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: import tranches repriced to measured neighbor hourly "
                    "DA LMPs (PJM_west→PJM, ISONE_tie→NEISO, scarcity→hourly max, "
                    "export sink→hourly min) — static ladder bypassed",
                    iso,
                    year,
                )

    # Net load for the solar-shape coupling: the LP-served load (net of
    # must-run) less utility solar/wind generation — same convention as the
    # drag floors and the forecast runner.
    _interchange_net_load = None
    if getattr(config, "caiso_import_solar_shape", False):
        _interchange_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
    apply_interchange_injections(
        fleet_arrays,
        mc_base,
        config,
        iso,
        year,
        carbon_price=carbon_price,
        gas_scenario=config.gas_price_path,
        net_load=_interchange_net_load,
        measured_overlay=_backcast_measured_interchange_prices,
    )

    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc -= wind_eac
    solar_mc -= solar_eac
    # Floor the curtailable wind/solar offers at the negative keep-running
    # (REC/PTC) value so curtailed renewables can set a sub-$0 marginal price
    # in oversupply (CAISO negative midday LMPs). No-op unless
    # config.negative_renewable_offers is on; the floor is the more-negative of
    # the existing offer and -renewable_keep_running_value (so wind's PTC is not
    # double-counted). See market_sim.policy.eac.
    wind_mc, solar_mc = apply_negative_renewable_offer_floor(wind_mc, solar_mc, config)

    storage_units = load_eia860_storage(iso, year, config)
    storage = storage_units_to_arrays(storage_units, zone_names)
    # Static (n_storage,) caps, or hour-varying (n_storage, T) when the
    # intra-year COD ramp is on (config.storage_vintage_ramp) and capacity
    # was commissioned mid-year — mid-year GWs stay offline before COD.
    storage_power_cap, storage_energy_cap = storage_cap_profiles(
        storage_units, storage, config.hours
    )
    # Reserve the measured storage up-AS MW from the dispatch power cap so AS-
    # committed battery capacity cannot also arbitrage energy (ERCOT only).
    # SKIPPED under ercot_storage_as_endogenous (G5): the endogenous co-opt hands
    # the FULL battery cap to the LP and lets it choose energy vs AS, so the
    # measured-award subtraction must not apply (it would pre-commit the split).
    if (
        getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and iso == "ERCOT"
    ):
        storage_power_cap = reserve_storage_as_power(
            storage_power_cap, config.weather_year, config.hours
        )

    if fleet_only:
        # Availability-reconstruction exit (no LP): everything a post-solve
        # consumer needs to recompute pmax x availability per unit-hour,
        # the renewable potential (cf x cap) and the storage power caps,
        # aligned with the persisted bundle.
        return {
            "config": config,
            "fleet": fleet,
            "fleet_arrays": fleet_arrays,
            "storage_units": storage_units,
            "storage": storage,
            "storage_power_cap": storage_power_cap,
            "wind_cf": wind_cf,
            "wind_cap": wind_cap,
            "solar_cf": solar_cf,
            "solar_cap": solar_cap,
            "demand": demand,
        }

    # Oil-burn inventory budget (NEISO-gated). When the budget binds in a
    # cold-snap month, its dual is the scarcity rent that lifts the persisted P1
    # LMP above the flat dual-fuel oil-parity cap (~$258).
    #
    # Two derivations of the same LP mechanism (dispatch._build_oil_budget_rows):
    #   - neiso_winter_fuel_inventory (Component A, keeper path): forward-
    #     derivable capacity/logistics budget (tank fill + re-supply) over the
    #     oil-primary + dual-fuel oil-limb fleet, the limb gated to its exogenous
    #     oil-switch hours (dual_fuel_oil_mask) so gas generation is never
    #     capped. One pooled fleet row per winter month, MMBtu-weighted.
    #   - neiso_oil_burn_budget (superseded): EIA-923 petroleum RECEIPTS, a
    #     measured deliveries-to-tank OUTCOME inadmissible under CLAUDE.md #13.
    #     Kept only as a reference path; never a keeper.
    oil_monthly_budget = None
    oil_budget_gen_idx = None
    oil_budget_month_index = None
    oil_budget_gen_hour_coeff = None
    oil_budget_group_index = None
    if getattr(config, "neiso_winter_fuel_inventory", False):
        from market_sim.data.winter_fuel_inventory import build_winter_fuel_budget

        _wf = build_winter_fuel_budget(
            iso,
            fleet_arrays,
            dual_fuel_oil_mask,
            start_fill_bbl=getattr(config, "neiso_winter_fuel_start_fill_bbl", None),
            hours=config.hours,
        )
        if _wf is not None:
            (
                oil_budget_gen_idx,
                oil_monthly_budget,
                oil_budget_month_index,
                oil_budget_gen_hour_coeff,
                oil_budget_group_index,
            ) = _wf
            _fin = np.isfinite(oil_monthly_budget)
            logger.info(
                "winter fuel-inventory budget (%s %d): %d oil-capable gens, "
                "start_fill=%s bbl, %d winter month(s) constrained, "
                "monthly cap %.2f M MMBtu (~%.2f TWh @HR10.8)",
                iso,
                year,
                oil_budget_gen_idx.size,
                (
                    f"{getattr(config, 'neiso_winter_fuel_start_fill_bbl', None):.0f}"
                    if getattr(config, "neiso_winter_fuel_start_fill_bbl", None)
                    else "2.8M(default)"
                ),
                int(_fin.sum()),
                float(oil_monthly_budget[_fin].max()) / 1e6 if _fin.any() else 0.0,
                float(oil_monthly_budget[_fin].max()) / 10.8 / 1e6
                if _fin.any()
                else 0.0,
            )
    elif getattr(config, "neiso_oil_burn_budget", False):
        from market_sim.data.fuel import load_oil_burn_budget

        _oil_result = load_oil_burn_budget(
            iso,
            year,
            fleet_arrays,
        )
        if _oil_result is not None:
            oil_budget_gen_idx, oil_monthly_budget = _oil_result

    # Base dispatch kwargs + priced import-node band: the shared pipeline
    # assembly (orchestrator-unification Stage 2) — the same key set the
    # inline dict carried, byte-identical values. The backcast-only keys
    # (ttc_import, oil_*) are passed explicitly so they stay present (possibly
    # None-valued) exactly as before; the forecast assembly leaves them UNSET.
    dispatch_spec = DispatchSpec(
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        # Load-shed penalty = the ISO's own energy bid cap (ISOConfig.voll),
        # not the ERCOT-flavored ScenarioConfig default ($5,000). NYISO/CAISO/
        # MISO/PJM cap verifiable energy offers at $2,000 (FERC Order 831);
        # ERCOT at $5,000. Using the per-ISO cap makes scarcity hours price at
        # the ceiling the market actually clears against.
        voll=iso_config.voll,
        incidence=incidence,
        ttc=ttc,
        # Import-direction bound when the measured ERCOT GTC overlay made the
        # export caps hourly/asymmetric; None keeps the symmetric -ttc.
        ttc_import=ttc_import,
        storage_power_cap=storage_power_cap,
        storage_energy_cap=storage_energy_cap,
        storage_zone_idx=storage.zone_idx,
        eta_chg=storage.eta_chg,
        eta_dis=storage.eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_eac,
        storage_discharge_cost=storage.vom,
        rps_target=None,
        storage_daily_cycle_hours=24 if config.storage_daily_cycling else None,
        interface_groups=interface_groups or None,
        # One-way links (MISO's RDT 3,000/2,500 MW directional pair) floor
        # their flow at 0 instead of -ttc. Every other ISO's links are
        # bidirectional (all-True array -> byte-identical bounds). This was
        # built in dispatch but never wired here, so the RDT asymmetry was
        # silently symmetric (+/-ttc per leg) before the six-zone refinement.
        link_bidirectional=get_link_bidirectional_array(iso_config.links),
        hydro_monthly_energy=hydro_monthly_energy,
        hydro_gen_idx=hydro_gen_idx,
        oil_monthly_budget=oil_monthly_budget,
        oil_gen_idx=oil_budget_gen_idx,
        oil_month_index=oil_budget_month_index,
        oil_gen_hour_coeff=oil_budget_gen_hour_coeff,
        oil_group_index=oil_budget_group_index,
        T=config.hours,
    )
    dispatch_kwargs = build_base_dispatch_kwargs(
        dispatch_spec, import_node_recon=import_node_recon
    )

    # Plant-group hourly ramp envelopes (config.ramp_limits, GATED default
    # off): CAMPD-measured trajectory bounds per plant group per hour
    # transition (model/dispatch._build_ramp_rows; design
    # docs/ramp-locational-design-2026-07.md §1). Mirrored in runner.py so
    # the forecast path shares the mechanism (forecast parity, design §4).
    # No-op (identical LP) when off or when the ISO has no envelope artifact.
    if getattr(config, "ramp_limits", False):
        from market_sim.data.fleet import build_ramp_groups

        ramp_groups = build_ramp_groups(fleet_arrays, iso)
        if ramp_groups is not None:
            r_gen_idx, r_group_col, r_up, r_dn = ramp_groups
            dispatch_kwargs.update(
                ramp_gen_idx=r_gen_idx,
                ramp_group_col=r_group_col,
                ramp_up_mw=r_up,
                ramp_dn_mw=r_dn,
            )
            logger.info(
                "%s %d: ramp envelopes on %d plant groups (%d member tranches)",
                iso,
                year,
                r_up.size,
                r_gen_idx.size,
            )

    # Local-capacity (LCR-area) minimum-generation rows
    # (config.local_capacity_constraints, GATED default off): published-study
    # load-pocket relaxation (design §3), RHS from the LCR report parameters
    # scaled by this year's zonal load shape. Mirrored in runner.py (forecast
    # parity). No-op when off or the ISO has no covered areas / crosswalk.
    if getattr(config, "local_capacity_constraints", False):
        from market_sim.data.local_capacity import build_local_capacity_specs

        lcr_specs, _lcr_meta = build_local_capacity_specs(
            iso,
            year,
            fleet_arrays.plant_code,
            fleet_arrays.pmax,
            fleet_arrays.availability,
            zone_names,
            demand,
            storage.zone_idx,
            storage_power_cap,
        )
        if lcr_specs:
            dispatch_kwargs.update(local_capacity_specs=lcr_specs)

    # Energy+reserve co-optimization: the shared pipeline wrapper
    # (orchestrator-unification Stage 2) — the per-ISO reserve designs live in
    # config/reserve_config.py (get_reserve_design), already shared with the
    # forecast runner; the wrapper owns the gate (energy_reserve_coopt, CAISO
    # excluded), the forward-driver threading, the merge, and the logging.
    # Collapses the former per-ISO elif ladder, byte-identically:
    #   * the hand-built PJM zone-aggregate block == reserve_config._pjm_design
    #     (measured Primary requirement + published ORDC — only the last ORDC
    #     step width depends on the requirement scalar and the design sets it
    #     to max(req), the same value — + deliverable supply cap + online gate);
    #   * the post-design ERCOT RTOLCAP supply-cap overwrite is folded into the
    #     designs themselves (audit gap A5): in backcast mode the design's
    #     internal ercot_rtolcap_supply_cap_mw call returns the same measured
    #     parquet series the overwrite applied.
    # sim_year=year is value-identical here: the backcast pins weather_year to
    # the solve year and every sim_year consumer falls back to weather_year.
    apply_reserve_coopt(
        dispatch_kwargs,
        config,
        fleet_arrays,
        config.hours,
        zone_names,
        system_load=demand.sum(axis=0),
        wind_gen=(wind_cap[:, None] * wind_cf).sum(axis=0),
        solar_gen=(solar_cap[:, None] * solar_cf).sum(axis=0),
        sim_year=year,
    )

    # P0 and P1 solve the *same* LP -- identical constraint matrix and bounds
    # -- and differ only in the objective (P1 = base MC + startup markup). So
    # build the model once and warm-start P1 from P0's optimal basis
    # (changeColsCost in place): this skips the second matrix build and
    # converges in ~8x fewer simplex iterations, cutting the P1 solve ~5x. It
    # does not move annual generation or prices -- validated plant-by-plant on
    # ERCOT 2023, where every plant's annual MWh and the zonal prices are
    # unchanged; the only difference is sub-MW hourly reshuffling among units
    # tied at the margin, which the LP is already indifferent to. Set
    # MARKET_SIM_WARMSTART=0 to fall back to two independent cold solves (e.g.
    # for an A/B comparison or to isolate a solver issue).
    _warm = os.environ.get("MARKET_SIM_WARMSTART", "1") != "0"
    model = DispatchModel(fleet_arrays, demand, **dispatch_kwargs) if _warm else None
    # Cross-year warm-start (MARKET_SIM_WARMSTART_XYEAR=1): once intra-year warm-
    # start has made the P1 second solve cheap, the one remaining cold solve is
    # each year's P0. Adjacent years share zones, network and most units, so the
    # prior year's optimal basis -- carried in xyear_cache and remapped onto this
    # year's fleet (surviving units by unit_id, fleet changes left for HiGHS to
    # repair) -- is a strong warm start for P0. The LP optimum is basis-
    # independent, so this only changes the solve path, never the cleared prices
    # or generation. Off by default; A/B against a cold P0 with the flag.
    _xwarm = _warm and os.environ.get("MARKET_SIM_WARMSTART_XYEAR", "0") != "0"
    if _xwarm and xyear_cache is not None and xyear_cache:
        model.apply_cross_year_basis(xyear_cache[0])
    # P0: solve with base MC to extract per-month run lengths.
    if _warm:
        r0 = model.solve(mc=mc_base)
    else:
        r0 = solve_dispatch(fleet_arrays, demand, mc=mc_base, **dispatch_kwargs)
    # P1: solve with bid MC = base MC + monthly startup amortization.
    markup = compute_monthly_markup(
        fleet,
        fleet_arrays,
        r0.dispatch,
        config.hours,
        gas_st_season_spread=config.gas_st_startup_spread,
        gas_st_startup_cost=getattr(config, "gas_st_startup_cost", False),
        chp_startup_covered=getattr(config, "chp_startup_covered", False),
        coal_warm_committed=getattr(config, "coal_warm_committed", False),
    )
    mc_bid = mc_base + markup
    if _warm:
        result = model.solve(mc=mc_bid)
    else:
        result = solve_dispatch(fleet_arrays, demand, mc=mc_bid, **dispatch_kwargs)

    # Hand this year's optimal basis to the next year's P0 (cross-year warm
    # start). Stored even when the flag is off so a downstream A/B does not
    # depend on call ordering; only consumed when MARKET_SIM_WARMSTART_XYEAR=1.
    if _warm and xyear_cache is not None:
        basis = model.export_cross_year_basis()
        if basis is not None:
            xyear_cache[:] = [basis]

    context = FleetContext.from_arrays(
        fleet_arrays,
        iso_config,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        storage.energy_cap,
    )
    # Everything the P2 commitment pass needs, kept so P2 can be re-run as a
    # post-process (see _commitment_pass / run_p2) without re-solving P0/P1.
    p2_state = {
        "year": year,
        "iso": iso,
        "fleet": fleet,
        "fleet_arrays": fleet_arrays,
        "mc_base": mc_base,
        "mc_bid": mc_bid,
        "p1_result": result,
        "demand": demand,
        "dispatch_kwargs": dispatch_kwargs,
        "config": config,
        "context": context,
        "storage_units": storage_units,
        "dual_fuel_oil_mask": dual_fuel_oil_mask,
        # Link list in flow-column order (the possibly import-node-extended /
        # per-hub-split topology actually solved), so the bundle can persist
        # per-link flows for interface-binding diagnostics (the MISO zonal
        # gates report binding-hour counts per CIL/CEL group and the RDT).
        "links": iso_config.links,
    }

    # P2 (optional): screen CC/CT commitment on P1 prices vs base MC, pin
    # coal to its P1 dispatch, and re-solve (a single LP solve). ERCOT AS-aware
    # commitment triggers the same P2 pass (valuing AS revenue in the screen)
    # even when the energy-only commitment screen is off — it requires the
    # multi-product co-opt to supply the per-product reserve duals.
    as_aware = (
        getattr(config, "ercot_as_aware_commitment", False)
        and iso == "ERCOT"
        and getattr(config, "energy_reserve_coopt", False)
    )
    # CAISO RA must-offer commitment (Step-1 overhaul): a min-load bridge floor
    # on the merchant gas CC/CT fleet, derived from the economic P1 run pattern,
    # re-solved in the same P2 pass. Triggers P2 even with the economic
    # commitment screen off (CAISO runs P1-only otherwise).
    caiso_ra = getattr(config, "caiso_ra_mustoffer", False) and iso == "CAISO"
    result_p1 = None
    if config.commitment_enabled or as_aware or caiso_ra:
        result_p1 = result
        result = _commitment_pass(p2_state)

    return result, context, result_p1, p2_state


def _commitment_pass(state: dict, config=None):
    """Run the P2 commitment pass from a P1 ``state`` dict; return the result.

    Re-uses the cached P1 marginal cost, demand and dispatch inputs, so only
    the single P2 LP solve runs — no P0/P1 re-solve. ``config`` overrides the
    state's config (to iterate commitment params); defaults to the state's.
    This is the seam the P2 post-processing layer uses.
    """
    cfg = config if config is not None else state["config"]
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    p1 = state["p1_result"]
    dk = state["dispatch_kwargs"]
    # CAISO RA must-offer commitment (Step-1 overhaul): a PURE min-load bridge
    # floor on the merchant gas CC/CT fleet — NO economic decommit screen. Each
    # unit the economic P1 dispatch runs before AND after a midday idle gap
    # shorter than its min-down time is held at min-load across the gap
    # (model.commitment.caiso_ra_mustoffer_min_gen); the P2 re-solve then sets
    # the level economically above that floor. This replaces the removed
    # measured-NG:NG slab. Distinct from the ERCOT AS-aware path below (other
    # ISO); engaged only when the economic commitment screen is off (the keeper
    # config) so the two never compose.
    if (
        getattr(cfg, "caiso_ra_mustoffer", False)
        and state["iso"] == "CAISO"
        and not cfg.commitment_enabled
    ):
        import dataclasses

        from market_sim.model.commitment import caiso_ra_mustoffer_min_gen

        # Startup-cost-aware extension (caiso-44, default off): also bridge a gap
        # LONGER than min-down when cycling off is uneconomic, using the model's
        # OWN P1 dual (LMP) and base MC in the restart inequality — no measured
        # pin. Off => the plain physical (gap < min-down) bridge, byte-identical.
        startup_bridge = bool(getattr(cfg, "caiso_ra_startup_bridge", False))
        # Solar-proportional / seasonal decommitment (caiso-48, default off):
        # bound economic bridges to the day-ahead commitment horizon and
        # decommit them RUC-order where the candidate floors exceed the P1
        # import/export absorption — the surplus hours reprice to the
        # curtailable-renewable keep-running offer, the same floor the
        # negative_renewable_offers dispatch offers use (no new constant).
        bridge_decommit = startup_bridge and bool(
            getattr(cfg, "caiso_ra_bridge_decommit", False)
        )
        surplus_floor_value = (
            -float(getattr(cfg, "renewable_keep_running_value", 20.0))
            if getattr(cfg, "negative_renewable_offers", False)
            else 0.0
        )
        ra_floor = caiso_ra_mustoffer_min_gen(
            p1.dispatch,
            fa,
            fleet,
            float(getattr(cfg, "caiso_ra_min_load_frac", 0.40)),
            p1_prices=p1.prices if startup_bridge else None,
            base_mc=state["mc_base"] if startup_bridge else None,
            startup_bridge=startup_bridge,
            bridge_decommit=bridge_decommit,
            surplus_floor_value=surplus_floor_value,
        )
        base_min_gen = (
            fa.min_gen
            if fa.min_gen is not None
            else np.broadcast_to(fa.pmin[:, None], ra_floor.shape)
        )
        new_min_gen = np.maximum(base_min_gen, ra_floor)
        # D-2 attribution: the RA bridge wins wherever it strictly raised the
        # composed floor (maximum-composition, data.floor_mechanisms).
        from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER

        base_mech = getattr(fa, "min_gen_mechanism", None)
        new_mech = (
            base_mech.copy()
            if base_mech is not None
            else np.zeros(ra_floor.shape, dtype=np.int8)
        )
        new_mech[ra_floor > base_min_gen] = MECH_RA_MUSTOFFER
        fa_ra = dataclasses.replace(
            fa,
            min_gen=new_min_gen,
            min_gen_mechanism=new_mech,
            pmin=fa.pmin.copy(),
        )
        # All-committed mask: no decommit. preserve_min_gen carries the RA
        # min-load floor into P2 and raises availability to keep it feasible.
        committed = np.ones(ra_floor.shape, dtype=bool)
        fa_p2 = apply_commitment_with_coal_pin(
            fa_ra,
            committed,
            p1.dispatch,
            fleet,
            screen_coal=False,
            preserve_min_gen=True,
        )
        # Expose the P2 bounds (incl. the RA floor + mechanism ids) so the
        # bundle writer can persist the floors the P2 dispatch actually saw.
        state["fleet_arrays_p2"] = fa_p2
        return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk)
    # AS-aware (ERCOT multi-product co-opt): value a unit's AS revenue (the P1
    # per-product reserve dual x its reserve-eligible headroom) in the screen, so
    # the units a tight month keeps online FOR AS stay committed and the P2 co-opt
    # headroom reflects realistic online capacity. The AS value comes from the
    # model's OWN P1 balance-row dual, never the measured MCPC (no fit).
    as_value = None
    if (
        getattr(cfg, "ercot_as_aware_commitment", False)
        and state["iso"] == "ERCOT"
        and getattr(cfg, "energy_reserve_coopt", False)
    ):
        from market_sim.results.scarcity import ercot_as_aware_unit_value

        as_value = ercot_as_aware_unit_value(
            fa, p1.dispatch, p1.reserve_price_by_family, cfg.hours
        )
    committed = compute_commitment(
        p1.prices,
        state["mc_base"],
        fleet,
        fa,
        cfg,
        storage_charge=p1.storage_charge,
        storage_discharge=p1.storage_discharge,
        storage_zone_idx=dk["storage_zone_idx"],
        demand=state["demand"],
        as_value=as_value,
    )
    # AS-adequacy floor (ERCOT AS-aware): re-commit cheapest eligible units until
    # committed online headroom covers the MEASURED total AS requirement, so the
    # screen cannot strip the reserve pool below what ERCOT procured (which would
    # price a false VOLL-scale shortage). The broad-month elevation then forms from
    # the binding shared-headroom dual (opportunity cost), while genuinely-short
    # acute hours still price the VOLL curve. Requirement = sum of the per-product
    # ASPLANNP433 quantities already in dispatch_kwargs.
    if as_value is not None:
        # Aggregate the per-FAMILY requirement onto per-PRODUCT (reserve-class)
        # rows for the tier-aware adequacy floor: the ECRS conservative-
        # deployment split runs one product as two disjoint-window families
        # sharing a class (reserve_balance_class maps family -> product), so
        # summing families per class recovers the product requirement exactly
        # (identity when families == products).
        req_fam = np.atleast_2d(np.asarray(dk["reserve_requirement"], dtype=float))
        hp = np.atleast_2d(np.asarray(dk["reserve_headroom_products"], dtype=bool))
        fam_class = np.asarray(
            dk.get("reserve_balance_class", np.arange(req_fam.shape[0])), dtype=int
        )
        req_by_class = np.zeros((hp.shape[1], req_fam.shape[1]), dtype=float)
        np.add.at(req_by_class, fam_class, req_fam)
        committed = as_adequacy_commit(
            committed,
            fa,
            fleet,
            dk["reserve_headroom_eligible"],
            dk["reserve_headroom_products"],
            req_by_class,
            p1.dispatch,
            headroom_frac=float(getattr(cfg, "ercot_as_adequacy_frac", 1.0)),
        )
    # A reserve / AS-deployment floor (ct_deployment / reliability_deployment)
    # must survive the economic commitment screen — those units ran for
    # reliability, not economics. Preserve min_gen through P2 only when such an
    # overlay is active (NEISO/other backcasts opt in); off by default so the
    # forecast runner and every non-overlay keeper stay byte-identical.
    preserve_min_gen = bool(
        getattr(cfg, "ct_deployment_overlay", False)
        or getattr(cfg, "reliability_deployment_overlay", False)
        or getattr(cfg, "caiso_gas_commitment_floor", False)
        or getattr(cfg, "nyiso_local_selfsupply", False)
        or getattr(cfg, "reliability_floor", False)
        or getattr(cfg, "nyiso_firm_imports", False)
        or getattr(cfg, "miso_firm_imports", False)
    )
    fa_p2 = apply_commitment_with_coal_pin(
        fa,
        committed,
        p1.dispatch,
        fleet,
        screen_coal=cfg.commitment_screen_coal,
        preserve_min_gen=preserve_min_gen,
        # WS1 (commitment-state-aware reserve headroom): a cold plant's peak
        # (duct-firing) tranche can neither generate nor hold reserve — couple
        # it to the committed tranche so it leaves the P2 headroom RHS too.
        couple_peak=as_value is not None,
    )
    dk_p2 = dk
    if as_value is not None:
        # Commitment-state-aware reserve headroom (WS1): online CTs join the
        # synchronized (fast) pool via the P2 availability, offline quick-start
        # capacity backs Non-Spin only via the extra-cap RHS. Overrides only
        # the two headroom kwargs; everything else in dk is shared with P1.
        from market_sim.config.reserve_config import (
            ercot_commitment_headroom_overrides,
        )

        dk_p2 = {
            **dk,
            **ercot_commitment_headroom_overrides(
                fa, committed, dk["reserve_headroom_eligible"]
            ),
        }
    # Expose the P2 bounds so the bundle writer can persist the floors the
    # P2 dispatch actually saw (D-2 forced-energy attribution).
    state["fleet_arrays_p2"] = fa_p2
    return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk_p2)


def _generation_twh(result, context: FleetContext) -> dict[str, float]:
    """Return modeled annual generation by fuel (TWh)."""
    gen_per_unit = result.dispatch.sum(axis=1)
    twh: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        twh[fuel] = twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
    twh["wind"] = (
        twh.get("wind", 0.0) + float(result.wind_dispatched.sum()) / _MWH_PER_TWH
    )
    twh["solar"] = (
        twh.get("solar", 0.0) + float(result.solar_dispatched.sum()) / _MWH_PER_TWH
    )
    return twh


def _print_table(title: str, rows: list[tuple]) -> None:
    """Print a titled, column-aligned text table."""
    print(f"\n  {title}")
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _report_year(
    year: int, iso: str, result, context: FleetContext, reference: dict, label: str = ""
) -> None:
    """Print the calibration diagnostics for one solved ISO-year."""
    tag = f"  [{label}]" if label else ""
    print(f"\n{'=' * 64}")
    print(f"  Calibration: {iso} {year}   (status: {result.status}){tag}")
    print(f"{'=' * 64}")

    model_twh = _generation_twh(result, context)
    # The benchmark is EIA-923 by-fuel net generation for the run year --
    # unlike the eGRID plant snapshot, its totals sum to the balancing
    # authority's actual net generation. Compared only for a full 8760-hour
    # run; a sub-annual horizon (--hours) is a smoke test, not a backcast.
    full_year = result.dispatch.shape[1] >= HOURS_PER_YEAR
    year_ref = reference.get("isos", {}).get(iso, {}).get(str(year), {})
    bench_twh = year_ref.get("generation_twh", {}) if full_year else {}
    if not full_year:
        print(
            f"\n  NOTE: {result.dispatch.shape[1]}-hour run -- EIA-923 "
            "benchmark comparison suppressed (full 8760h required)."
        )
    # The EIA-923 monthly file for the current year is preliminary until
    # the annual revision (typically Sep of the following year): it
    # under-reports renewable generation by ~30 TWh because small / new
    # wind and solar plants are slow to submit Form 923. Flag that here
    # so the "+13.6% total" gap is read as a benchmark gap, not a model
    # error. The EIA-930 hourly extract is the more complete reference
    # for the current year (see the calibration_reference.json
    # ``eia930_total_twh`` block).
    if full_year and iso == "ERCOT" and year >= 2025:
        print(
            "\n  NOTE: ERCOT 2025 EIA-923 monthly file is preliminary "
            "(released Feb 2026). It under-reports renewable generation "
            "by ~30 TWh vs EIA-930 hourly metered output; expect "
            "+10-15% model-vs-EIA-923 gaps until the annual revision."
        )

    fuels = sorted(set(model_twh) | set(bench_twh))
    gen_rows: list[tuple] = [("fuel", "model TWh", "EIA-923 TWh", "diff %")]
    for fuel in fuels:
        m = model_twh.get(fuel, 0.0)
        b = bench_twh.get(fuel)
        if b is None:
            gen_rows.append((fuel, f"{m:.2f}", "—", "—"))
        else:
            diff = 100.0 * (m - b) / b if b else float("inf")
            gen_rows.append((fuel, f"{m:.2f}", f"{b:.2f}", f"{diff:+.1f}"))
    total_m = sum(model_twh.values())
    total_b = sum(bench_twh.values()) if bench_twh else None
    gen_rows.append(
        (
            "TOTAL",
            f"{total_m:.2f}",
            f"{total_b:.2f}" if total_b else "—",
            f"{100.0 * (total_m - total_b) / total_b:+.1f}" if total_b else "—",
        )
    )
    _print_table("Generation by fuel", gen_rows)

    emissions_t = float(
        compute_emissions(result.dispatch, np.asarray(context.emission_rate)).sum()
    )
    model_co2 = emissions_t / _TONNES_PER_MT
    # The EIA-923 Page 1 benchmark carries no CO2; report modeled CO2 alone.
    print(f"\n  CO2 emissions\n    model {model_co2:.2f} Mt")

    price_rows: list[tuple] = [("zone", "avg $/MWh", "neg-price hrs")]
    iso_config = get_iso_config(iso)
    for z, zone in enumerate(iso_config.zone_names):
        zone_price = result.prices[z]
        price_rows.append(
            (
                zone,
                f"{zone_price.mean():.2f}",
                str(int((zone_price < 0.0).sum())),
            )
        )
    system_price = result.prices.mean(axis=0)
    price_rows.append(
        (
            "SYSTEM",
            f"{system_price.mean():.2f}",
            str(int((system_price < 0.0).sum())),
        )
    )
    _print_table("Zonal prices", price_rows)

    _report_curtailment(year, iso, result, context, full_year)

    _report_hourly_correlation(year, iso, result, context, full_year)


def _report_curtailment(
    year: int, iso: str, result, context: FleetContext, full_year: bool
) -> None:
    """Print the headline modeled-vs-reported renewable curtailment metric.

    Modeled curtailment is the dispatch's unused wind/solar potential. For
    ISO-years with a built HSL-style parquet (scripts/build_ercot_hsl.py /
    build_caiso_hsl.py) the reported curtailment — the telemetered
    ``hsl - gen`` — is printed beside it, with the monthly shape (the CAISO
    P6 / ERCOT E3 headline metric): a transmission-constrained dispatch fed
    uncurtailed potential should reproduce both the level and the
    seasonality of real curtailment. The reported comparison is suppressed
    on a sub-annual smoke run, and the table falls back to model-only
    columns when no HSL data covers the year.
    """
    hsl = load_hsl_hourly(iso, year)
    compare = hsl is not None and full_year

    caps = {"wind": context.wind_cap_mw, "solar": context.solar_cap_mw}
    potential = {
        "wind": context.wind_potential_mwh,
        "solar": context.solar_potential_mwh,
    }
    dispatched = {
        "wind": np.asarray(result.wind_dispatched, dtype=float).sum(axis=0),
        "solar": np.asarray(result.solar_dispatched, dtype=float).sum(axis=0),
    }

    rows: list[tuple] = [
        (
            "resource",
            "installed GW",
            "potential TWh",
            "model TWh",
            "model %",
            "reported TWh",
            "reported %",
        )
    ]
    for fuel in ("wind", "solar"):
        pot_mwh = potential[fuel]
        curt_mwh = max(pot_mwh - float(dispatched[fuel].sum()), 0.0)
        reported_twh = reported_pct = "—"
        if compare:
            rep_curt = float(
                (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"]).clip(lower=0.0).sum()
            )
            rep_pot = float(hsl[f"{fuel}_hsl_mw"].sum())
            reported_twh = f"{rep_curt / _MWH_PER_TWH:.2f}"
            reported_pct = f"{100.0 * rep_curt / rep_pot:.1f}" if rep_pot > 0 else "—"
        rows.append(
            (
                fuel,
                f"{caps[fuel] / 1e3:.2f}",
                f"{pot_mwh / _MWH_PER_TWH:.2f}",
                f"{curt_mwh / _MWH_PER_TWH:.2f}",
                f"{100.0 * curt_mwh / pot_mwh:.1f}" if pot_mwh > 0 else "—",
                reported_twh,
                reported_pct,
            )
        )
    _print_table("Renewable curtailment — modeled vs reported", rows)
    if hsl is None:
        print(
            f"    (no reported HSL data for {iso} {year}; build with "
            "scripts/build_ercot_hsl.py / build_caiso_hsl.py — ERCOT 2024+ "
            "needs the NP6 report uploads)"
        )
        return
    if not compare:
        print("    (reported comparison suppressed -- full 8760h run required)")
        return

    # Monthly shape: model re-curtailment vs reported, GWh per month. The
    # model's hourly potential is the same rescaled HSL series the dispatch
    # consumed (renewables.hsl_potential_mw), so the comparison isolates
    # *when* the model curtails, not profile-construction differences.
    month_idx = _hour_to_month_index(HOURS_PER_YEAR)
    monthly: dict[str, np.ndarray] = {}
    for fuel in ("wind", "solar"):
        pot_mw = hsl_potential_mw(iso, year, fuel)
        model_curt = np.clip(pot_mw - dispatched[fuel][:HOURS_PER_YEAR], 0.0, None)
        rep_curt = (
            (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"])
            .clip(lower=0.0)
            .to_numpy(dtype=float)
        )
        monthly[f"{fuel}_model"] = (
            np.bincount(month_idx, weights=model_curt, minlength=12) / 1e3
        )
        monthly[f"{fuel}_reported"] = (
            np.bincount(month_idx, weights=rep_curt, minlength=12) / 1e3
        )
    monthly_rows: list[tuple] = [
        ("month", "wind model", "wind rptd", "solar model", "solar rptd"),
    ]
    for m in range(12):
        monthly_rows.append(
            (
                str(m + 1),
                f"{monthly['wind_model'][m]:.0f}",
                f"{monthly['wind_reported'][m]:.0f}",
                f"{monthly['solar_model'][m]:.0f}",
                f"{monthly['solar_reported'][m]:.0f}",
            )
        )
    _print_table("Monthly curtailment (GWh)", monthly_rows)


def _report_hourly_correlation(
    year: int, iso: str, result, context: FleetContext, full_year: bool
) -> None:
    """Print the modeled-vs-EIA-930 hourly dispatch correlation for coal/gas.

    Compares the shape of the hourly dispatch — not just annual totals — so
    a model that hits the right yearly TWh by running flat when the real
    fleet cycled is still visible. ERCOT only, and only for a full 8760-hour
    run (the EIA-930 fossil series is a whole-year extract).
    """
    if iso != "ERCOT" or not full_year:
        return
    eia_hourly = load_ercot_fossil_gen(year)
    if eia_hourly is None:
        print(
            "\n  Hourly dispatch correlation\n    (no EIA-930 fossil "
            f"series for {year})"
        )
        return

    coal = np.zeros(result.dispatch.shape[1])
    gas = np.zeros(result.dispatch.shape[1])
    for g, fuel in enumerate(context.fuel_types):
        if fuel == "coal":
            coal += result.dispatch[g]
        elif fuel in _GAS_FUEL_TYPES:
            gas += result.dispatch[g]

    stats = check_hourly_dispatch_correlation({"coal": coal, "gas": gas}, eia_hourly)
    rows: list[tuple] = [("fuel", "pearson r", "nrmse", "model TWh", "EIA TWh")]
    for fuel in ("coal", "gas"):
        s = stats[fuel]
        rows.append(
            (
                fuel,
                f"{s['pearson_r']:.3f}",
                f"{s['nrmse']:.3f}",
                f"{s['model_twh']:.2f}",
                f"{s['eia_twh']:.2f}",
            )
        )
    _print_table("Hourly dispatch correlation (vs EIA-930)", rows)


def _build_parser() -> argparse.ArgumentParser:
    """Return the run_calibration argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_calibration",
        description="Run dispatch for calibration years and compare to EIA.",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        required=True,
        help="One or more calibration years (2021-2024).",
    )
    parser.add_argument(
        "--iso",
        default="ERCOT",
        help="ISO to calibrate (default ERCOT).",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=8760,
        help="Dispatch horizon in hours (default 8760; 168 for a quick test).",
    )
    parser.add_argument(
        "--ttc-wn",
        type=float,
        default=None,
        help="Override the West<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-wsc",
        type=float,
        default=None,
        help="Override the West<->South_Central transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-pn",
        type=float,
        default=None,
        help="Override the Panhandle<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--coal-passthrough",
        type=float,
        default=None,
        help="Override coal_prb_contract_passthrough (PRB take-or-pay "
        "fuel-cost fraction); 1.0 disables the discount.",
    )
    parser.add_argument(
        "--commitment",
        action="store_true",
        help="Run the P2 unit-commitment pass after P1; both are reported.",
    )
    parser.add_argument(
        "--no-coal-p2",
        action="store_true",
        help="Pin coal to its P1 dispatch in P2 instead of screening it: "
        "coal gains no new generation in P2 (P1 locks it). Only "
        "meaningful with --commitment.",
    )
    parser.add_argument(
        "--priced-interchange",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Serve interchange through the priced import/export node "
        "(import tranches + export sinks in the ISO's external zone) "
        "instead of the measured schedule added to demand. Default per "
        f"ISO: on for {', '.join(sorted(PRICED_INTERCHANGE_DEFAULT_ISOS))} "
        "(no measured-schedule mode), off elsewhere; pass "
        "--no-priced-interchange to force the measured schedule.",
    )
    parser.add_argument(
        "--reference-price-interface",
        action="store_true",
        help="Serve the priced-interchange seam through the forecast-grade "
        "reference-price interface (per-neighbor gas x heat-rate x "
        "load-shape, cleared on the spread vs the ISO LMP with a hurdle) "
        "instead of the fitted IMPORT_TRANCHES/EXPORT_TRANCHES. Implies "
        "--priced-interchange; gated to ISOs in INTERFACE_NEIGHBORS (PJM). "
        "See docs/reference-price-interface.md.",
    )
    parser.add_argument(
        "--negative-renewable-offers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Floor the curtailable wind/solar dispatch offer at the negative "
        "keep-running (REC/PTC) value so curtailed renewables set a "
        "sub-$0 marginal price in oversupply (CAISO negative midday "
        "LMPs). Default (unset) keeps the per-ISO base config value (ON "
        "for CAISO); --no-negative-renewable-offers forces it off.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: run each requested calibration year and print diagnostics.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    args = _build_parser().parse_args(argv)
    iso = args.iso.upper()
    # The reference-price interface is on when the CLI flag is set OR the ISO is
    # in the per-ISO default-on set (MISO); see resolve_reference_price_interface.
    reference_price_interface = resolve_reference_price_interface(
        args.reference_price_interface, iso
    )
    priced_interchange = resolve_priced_interchange(args.priced_interchange, iso)
    # The reference-price interface serves the seam through the priced node, so
    # it implies priced interchange (unless explicitly turned off on the CLI).
    if reference_price_interface and args.priced_interchange is not False:
        priced_interchange = True
    reference = _load_reference()
    ttc_overrides = {
        "ttc_wn": args.ttc_wn,
        "ttc_wsc": args.ttc_wsc,
        "ttc_pn": args.ttc_pn,
    }

    # Single-element holder carrying the prior year's optimal basis across
    # run_year calls for cross-year warm-start (MARKET_SIM_WARMSTART_XYEAR=1).
    # Years are run in the order requested, so listing them chronologically lets
    # each P0 warm-start from the adjacent year's basis.
    xyear_cache: list = []
    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            iso,
            year,
            args.hours,
            gas_price,
        )
        result, context, result_p1, _ = run_year(
            year,
            iso,
            args.hours,
            gas_price,
            ttc_overrides,
            args.coal_passthrough,
            commitment_enabled=args.commitment,
            commitment_screen_coal=not args.no_coal_p2,
            priced_interchange=priced_interchange,
            reference_price_interface=reference_price_interface,
            negative_renewable_offers=args.negative_renewable_offers,
            xyear_cache=xyear_cache,
        )
        if result_p1 is not None:
            _report_year(year, iso, result_p1, context, reference, label="P1")
            _report_year(year, iso, result, context, reference, label="P2")
        else:
            _report_year(year, iso, result, context, reference)


if __name__ == "__main__":
    main()
