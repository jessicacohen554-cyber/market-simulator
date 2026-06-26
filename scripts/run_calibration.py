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
    INTERFACE_NEIGHBORS,
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_YEAR,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    VOM,
    resolve_priced_interchange,
    resolve_reference_price_interface,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
    measured_monthly_hydro,
)
from market_sim.data.hydro import (  # noqa: E402
    forecast_monthly_hydro,
    load_hydro_budget,
)
from market_sim.data.fleet import (  # noqa: E402
    _hour_to_month_index,
    COAL_MUSTRUN_BY_PLANT,
    Generator,
    aggregate_fleet,
    apply_coal_tranches,
    apply_gas_st_netload_drag_floor,
    assemble_mc,
    bins_to_fleet,
    campd_tranche_fuel_frac,
    coal_takeorpay_share,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_campd_bins,
    load_fleet_from_csv,
    load_retired_within_window,
    split_coal_tranches,
    split_gas_tranches,
    thermal_tranche_overrides,
)
from market_sim.data.fuel import (  # noqa: E402
    apply_coal_supply_pricing,
    apply_dual_fuel_pricing,
    apply_ercot_west_netload_gas_shape,
    apply_ercot_zonal_gas_basis,
    apply_hub_basis_overlay,
    apply_nyiso_zonal_gas_basis,
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
    compute_commitment,
    compute_monthly_markup,
)
from market_sim.model.dispatch import DispatchModel, solve_dispatch  # noqa: E402
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    reserve_storage_as_power,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    build_export_sinks,
    build_import_generators,
    build_incidence_matrix,
    build_interface_groups,
    build_reference_price_node,
    extend_with_import_node,
    get_ttc_array,
    inject_reference_price_mc,
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


# Calibrated PJM thermal offer curve (per-class band heat-rate multipliers on
# AHR x delivered fuel price). Tuned against the 2023 & 2024 EIA-930 fuel mix
# and PJM hub-average LMP (data/raw/_validation-source). Built in two stages, mirroring
# the operator workflow:
#   1. SHAPE — relative band multipliers set the generation mix: coal vs gas,
#      and the CC / CT / gas-steam split. With PJM delivered gas ~ $3.21/MMBtu
#      (Henry Hub + the EIA-923 +0.67 basis), this lands gas_cc, gas_ct and the
#      2023 gas-steam classes within tolerance and coal within ~4% of EIA-930.
#   2. LEVEL — every band is then scaled by a single global factor (~0.72), so
#      the *ratio* between classes (the mix) is held fixed while the absolute
#      bid level — and therefore the cleared LMP — is pulled down from ~+50% to
#      within ~+8-16% of the PJM hub average. The CT scarcity (`peak`) band is
#      additionally capped at 4.0 (an ERCOT-style 13x wall is far too high for
#      PJM's price formation; it was inflating the high-price tail). The scale
#      is folded into the multipliers because there is no separate price-scale
#      lever; read these as *price-calibrated* multipliers, not literal heat
#      rates. COAL_LIGNITE / COAL_PRB are carried for completeness but unused by
#      PJM (its coal is bituminous / sub-bituminous / waste -> BIT/SUB/WC).
# Known residuals (a single static curve cannot remove them; see calibration
# log): 2024 gas-steam runs ~20% light because the model's economic gas-steam
# falls with cheaper 2024 gas while the EIA-923 actual rises, and grid solar
# sits ~10% under EIA-930 because PJM's distributed/BTM solar never reaches the
# wholesale grid the LP dispatches.
_PJM_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 0.6624,
        "econ_low": 0.7344,
        "econ_high": 0.8928,
        "peak": 1.62,
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
        "committed": 0.8784,
        "econ_low": 0.9792,
        "econ_high": 1.4256,
        "peak": 4.0,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
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
_NYISO_OFFER_CURVE: dict[str, dict[str, float]] = {
    "CC_REGULAR": {
        "committed": 0.90,
        "econ_low": 0.95,
        "econ_high": 1.21,  # run 27: 1.12 -> 1.21, CAMPD CC marginal-HR SRMC reach (ERCOT-grounded)
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CC_CHP": {
        "committed": 0.90,
        "econ_low": 0.98,
        "econ_high": 1.24,  # run 27: 1.15 -> 1.24, +0.03 over CC_REGULAR (trim CHP over-run)
        "peak": 2.25,
        "econ_low_share": 0.50,
        "pct_peaking": 8.0,
    },
    "CT_PEAKER": {
        "committed": 1.35,
        "econ_low": 1.27,
        "econ_high": 1.98,
        "peak": 13.15,
        "econ_low_share": 0.526,
        "pct_peaking": 7.0,
    },
    "ST_GAS": {
        "committed": 0.97,
        "econ_low": 1.10,
        "econ_high": 1.45,
        "peak": 4.20,
        "econ_low_share": 0.50,
        "pct_peaking": 15.0,
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
        gas_hub_basis_overlay=(iso.upper() == "NEISO"),
        #   Doc-08 NEISO design decision 1: the marginal NEISO gas unit
        #   prices off Algonquin Citygate spot, whose Dec-Feb basis blows out
        #   to +$4-13/MMBtu (measured ISO-NE MA gas index 2023-2025,
        #   data/raw/gas_basis_by_iso_month.csv). The overlay replaces
        #   the gas price with HH-month + measured AGT basis in covered
        #   months — THE ISO-NE winter price driver and the dual-fuel switch
        #   trigger (P13). No basis rows exist for other ISOs (the NYISO
        #   Transco Z6 leg is still unsourced), so this is a NEISO-only
        #   repricing.
        gas_hub_basis_daily=False,
        #   Daily resolution for the AGT overlay is an OFF-BY-DEFAULT diagnostic
        #   (opt in with --gas-hub-basis-daily). It redistributes each winter
        #   month's measured mean basis across days by NEISO
        #   demand^AGT_DAILY_BASIS_CONVEXITY to build the winter >$200 tail the
        #   flat monthly plateau can't — but that convexity is a value fitted to
        #   the backcast (not a measured/forecast-grade input), and the daily
        #   AGT spot it proxies (upload U4) is paywalled/unavailable, so the
        #   keepers rest on the measured *monthly* overlay only and treat the
        #   winter tail + near-zero oil as honest monthly-granularity limits.
        #   See market_sim.data.fuel.iso_hub_daily_gas_prices and
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
        caiso_gas_commitment_floor=(iso.upper() == "CAISO"),  # CAISO keeper
        #   default-ON: the RA must-offer midday gas-commitment floor holds the
        #   RA-obligated gas fleet online at min-load through the solar glut (it
        #   can't economically cycle off for the evening ramp), so the model goes
        #   LONG midday and its surplus exports/curtails at ~$0 — the structurally
        #   correct CAISO market design. Validated keeper caiso-6-floor-negrenew:
        #   spring-midday LMP floor collapses (min 28->0 every year) with gas
        #   disciplined vs EIA-923 (2024 71.3 vs 67.7). See
        #   transmission.inject_caiso_gas_commitment_floor and
        #   results/calibration/RESULTS-caiso-ra-mustoffer-floor.md. Other ISOs
        #   stay off (byte-identical).
        caiso_gas_floor_frac=(0.80 if iso.upper() == "CAISO" else 1.0),  # 0.80 =
        #   EIA-923 gas / EIA-930 NG: NG, stripping the ~21% geo+bio the CISO
        #   NG: NG silently absorbs (CISO reports neither) — targets the true
        #   must-offer gas without padding the mix.
        caiso_ct_reliability_floor=(iso.upper() == "CAISO"),  # CAISO keeper
        #   default-ON: the local-RA CT_PEAKER reliability floor holds simple-
        #   cycle gas peakers online through the hot-day afternoon-evening ramp
        #   for local capacity-area reliability (LA Basin / Big-Creek-Ventura /
        #   Bay-Area). An energy-only LP leaves these top-of-merit peakers off and
        #   spills their energy onto the cheaper CC fleet (CT_PEAKER under-runs,
        #   CC_REGULAR over-runs); the floor restores the measured merit split. It
        #   is keyed to the load-weighted CAISO daily max temperature (NOAA GHCN),
        #   coefficients regressed from measured CAMPD CT_PEAKER evening CF vs
        #   TMAX, 2023-2025 — a physical heat->commitment rule, not a TWh-residual
        #   fit. See transmission.inject_caiso_ct_reliability_floor and
        #   docs/caiso-ct-reliability-floor-2026-06.md. Other ISOs stay off
        #   (byte-identical); coefficients from ScenarioConfig defaults.
        caiso_ct_floor_base=(0.049 if iso.upper() == "CAISO" else 0.0),  # CAISO
        #   keeper default-ON: the YEAR-ROUND local-RA baseline the temperature
        #   hot-limb clips to zero. CAISO's Local Capacity Requirement is a
        #   year-round load-pocket floor (binding hardest at summer peak but
        #   holding a must-offer minimum on mild days too), so peakers run a steady
        #   baseline even off the hot limb. 0.049 = the measured median CAMPD
        #   CT_PEAKER evening (15-22) capacity factor on cool days (TMAX<25 degC),
        #   2023-2025 — the regression intercept the hot-limb fit discards, not a
        #   TWh-residual tune (scripts/derive_caiso_ct_reliability_floor.py).
        negative_renewable_offers=(iso.upper() == "CAISO"),  # CAISO keeper
        #   default-ON: CA solar/wind bid below $0 (RPS/REC/PTC keep-running
        #   value) in oversupply, so the curtailable renewable tier sets a sub-$0
        #   marginal price once the model is long past the $0 export sink — the
        #   negative midday tail. Byte-identical when not binding (current floor
        #   frac reaches $0, not yet negative; bites with export shaping / a
        #   higher floor). See policy.eac.apply_negative_renewable_offer_floor
        #   and results/calibration/NEGRENEW-caiso-findings.md.
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
            iso.upper() in ("PJM", "NYISO", "NEISO")
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
                # NEISO min-stable-load offer re-anchored to the measured CAMPD
                # heat-rate curve. The CC_REGULAR fleet's gen-weighted average
                # heat rate is set at full load (load-fraction >0.90 HR = 0.93x
                # the fleet average), while the min-stable-load band (40-55% of
                # nameplate, the committed tranche) runs at 1.30x the average —
                # min-load is ~40% less efficient than full load. The legacy
                # committed 0.92 priced min-load *below* full-load (econ_high
                # 1.27), the inverse of the measured shape, leaving an
                # artificially-cheap min-load block that the (now-removed,
                # a8b0e55) net-summer CC "wall" was masking. Raise the NEISO
                # committed tranche to the full-load offer level (= econ_high
                # 1.27) so min-load $/MWh is at-or-above full-load SRMC
                # (ISO-NE Market Rule 1 incremental-energy shape); a
                # conservative floor (the measured curve supports up to ~1.30)
                # that removes the cheap min-load block without fitting to the
                # price residual. ISO-gated; ERCOT/PJM and forecasts unchanged.
                "committed": 1.27 if iso == "NEISO" else 0.92,
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
            # NOTE (CAISO CT_CHP — EOR cogen over-dispatch, deferred to next
            # session): the CAISO CT_CHP fleet is dominated by Kern-County
            # enhanced-oil-recovery STEAM cogens (Sycamore, Kern River, Midway
            # Sunset, Fresno, Badger Creek, Bear Mountain) that burn gas primarily
            # to make oil-field injection steam, with electricity a byproduct. The
            # compact-cogen 1.10/1.20/1.40 multipliers price them as efficient
            # baseload, so the energy-only LP runs them flat at ~88% CF (7.0 TWh)
            # vs ~3.5 measured (EIA-923; e.g. Kern River 1.35 model vs 0.20) — a
            # real over-dispatch. A power-only-HR re-price (committed ~1.75) was
            # trialled but REVERTED: with the total CAISO gas envelope already
            # over-sized by the import / energy-balance over-generation drift,
            # cutting cheap CT_CHP does not lower total gas — it reshuffles
            # straight onto CC_REGULAR (CC +5 TWh worse), since CC is the next-
            # cheapest dispatchable. The EOR re-price must land AFTER the total-
            # gas / import-drift fix (so the freed energy leaves as imports, not
            # CC), not before.
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
        # parity, and the daily overlay is itself an off-by-default diagnostic.
        # With the keepers on the monthly overlay, modeled oil stays near zero
        # (the documented monthly-granularity limit), not relabeled.
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


def _hydro_fleet(
    iso: str,
    year: int,
    zone_names: list[str],
    backfill_year: int | None = None,
    eia930_monthly: bool = False,
    forecast_budget: bool = False,
    hydro_year: str = "normal",
) -> tuple[list[Generator], np.ndarray | None]:
    """Return the ISO's conventional-hydro LP units and their monthly budgets.

    Each EIA-923-reporting conventional hydro plant (prime mover ``HY``;
    pumped storage is a storage resource, not inflow hydro) becomes one LP
    unit at its EIA-860 nameplate, paired row-for-row with its EIA-923
    monthly net-generation energy budget. The dispatch LP's hydro budget
    family then lets each plant choose *when* within a month to generate
    (peak shaving) while its monthly energy stays pinned to the measured
    inflow — strictly better than the flat-monthly must-run injection it
    replaces, which couldn't shave peaks at all.

    Plants that resolve to no model zone are dropped. Returns
    ``([], None)`` when the ISO has no usable hydro for ``year``.

    ``backfill_year`` carries plants that reported hydro in that prior year
    but not in ``year`` at their prior-year monthly generation — the
    :func:`load_hydro_budget` early-release path. The most recent EIA-923
    vintage is a monthly-survey-only release covering the large reporters, so
    a current-year backcast under-counts conventional hydro until the final
    annual file lands (NEISO 2025: 5 of ~166 plants, 0.09 of ~6 TWh); the
    missing inflow is otherwise served by gas, inflating the modeled gas
    level. ``None`` (default) loads ``year`` exactly as reported and changes
    no existing run.

    ``eia930_monthly`` repins the assembled budget's monthly energy to the
    measured EIA-930 ``NG: WAT`` monthly total for ``(iso, year)`` (preserving
    per-plant within-month shares), correcting both the level and the monthly
    shape when the backfilled early-release vintage misstates an off-year
    (NEISO 2025: 2024 backfill 6.65 TWh, flat, vs measured 5.12 TWh). No-op
    when EIA-930 hydro for the ISO/year is unavailable. ``False`` (default)
    changes no existing run.

    ``forecast_budget`` is the forward analogue of ``eia930_monthly``: instead
    of pinning the budget to a measured year, it sets the monthly *level* to a
    normal-water-year climatology (the multi-year mean of measured EIA-930
    ``NG: WAT``) scaled by the wet/dry ``hydro_year`` lever — see
    :func:`market_sim.data.hydro.forecast_monthly_hydro`. The per-plant
    within-month shares still come from ``year``'s EIA-923 (the budget shape);
    only the level is the forecast climatology, so the same when-to-generate
    dispatch mechanism runs against a forward-reproducible level rather than a
    realized one. Mutually exclusive with ``eia930_monthly`` (a run is either a
    backcast realization or a forecast). No-op when no climatology exists for
    the ISO. ``False`` (default) changes no existing run.
    """
    if eia930_monthly and forecast_budget:
        raise ValueError(
            "eia930_monthly (measured backcast level) and forecast_budget "
            "(normal-water-year forecast level) are mutually exclusive"
        )
    if eia930_monthly:
        target = measured_monthly_hydro(iso, year)
    elif forecast_budget:
        target = forecast_monthly_hydro(iso, hydro_year)
    else:
        target = None
    try:
        budget = load_hydro_budget(
            iso, year, backfill_year=backfill_year, monthly_target_mwh=target
        )
    except (FileNotFoundError, ValueError):
        return [], None
    units: list[Generator] = []
    monthly: list[np.ndarray] = []
    for i, pid in enumerate(budget.plant_ids):
        zone = budget.zones[i]
        cap = float(budget.max_mw[i])
        energy = np.asarray(budget.monthly_energy[i], dtype=float)
        if zone not in zone_names or cap <= 0.0 or energy.sum() <= 0.0:
            continue
        units.append(
            Generator(
                unit_id=f"{int(pid)}_hydro",
                name=budget.plant_names[i],
                zone=zone,
                fuel_type="hydro",
                pmax_mw=cap,
                vom=VOM["hydro"],
                eford=0.0,  # availability is captured by the energy budget
                plant_group="hydro",
                plant_code=int(pid),
            )
        )
        monthly.append(energy)
    if not units:
        return [], None
    return units, np.vstack(monthly)


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
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    storage_vintage_ramp: bool = False,
    battery_dispatch_adder: float = 0.0,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
    curve_smoothing: dict[str, float | int | None] | None = None,
    cc_derate_from_top: bool = False,
    must_run_mw: "np.ndarray | None" = None,
    inject_biomass_mustrun: bool = False,
    priced_interchange: bool = False,
    hydro_backfill_year: int | None = None,
    as_reserve_withholding: bool = False,
    as_reserve_formula: bool = False,
    energy_reserve_coopt: bool = False,
    ercot_multiproduct_as_coopt: bool = False,
    ercot_load_resource_reserve: bool = False,
    ercot_load_resource_reserve_from_year: int = 2023,
    ercot_storage_as_reserve: bool = False,
    ercot_storage_as_reserve_from_year: int = 2025,
    ercot_ecrs_requirement: bool = False,
    ercot_ecrs_requirement_from_year: int = 2023,
    ordc_lolp_params_path: str | None = None,
    storage_as_commitment: bool = False,
    hydro_eia930_monthly: bool = False,
    hydro_forecast_budget: bool = False,
    hydro_year: str = "normal",
    interchange_shaping: bool = False,
    interchange_shaping_export_only: bool = False,
    reference_price_interface: bool = False,
    negative_renewable_offers: bool | None = None,
    caiso_gas_commitment_floor: bool | None = None,
    caiso_gas_floor_frac: float | None = None,
    caiso_ct_reliability_floor: bool | None = None,
    caiso_import_hub_prices: bool | None = None,
    caiso_import_gas_coupling: bool | None = None,
    caiso_import_solar_shape: bool | None = None,
    caiso_bidir_intertie: bool | None = None,
    caiso_per_hub_intertie: bool | None = None,
    caiso_corridor_flow_limit: bool | None = None,
    caiso_intertie_reference_price: bool | None = None,
    caiso_corridor_atc_forward: bool | None = None,
    nyiso_local_selfsupply: bool | None = None,
    nyiso_firm_imports: bool | None = None,
    nyiso_import_reconciliation: bool | None = None,
    nyiso_synchronised_reserve: bool | None = None,
    nyiso_spin_headroom_frac: float | None = None,
    miso_firm_imports: bool | None = None,
    miso_seam_flow_limit: bool = False,
    gas_hub_basis_overlay: bool | None = None,
    gas_st_netload_drag: bool = False,
    gas_st_drag_overrides: dict[str, float] | None = None,
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
    if caiso_ct_reliability_floor is not None:
        config = config.with_overrides(
            caiso_ct_reliability_floor=caiso_ct_reliability_floor
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
    if nyiso_local_selfsupply is not None:
        config = config.with_overrides(nyiso_local_selfsupply=nyiso_local_selfsupply)
    if nyiso_firm_imports is not None:
        config = config.with_overrides(nyiso_firm_imports=nyiso_firm_imports)
    if nyiso_import_reconciliation is not None:
        config = config.with_overrides(
            nyiso_import_reconciliation=nyiso_import_reconciliation
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
    if ercot_multiproduct_as_coopt:
        config = config.with_overrides(ercot_multiproduct_as_coopt=True)
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
    # Battery throughput/cycling cost (run_calibration_full --battery-adder):
    # per-MWh-discharged adder that tames LP over-cycling of the BESS fleet.
    if battery_dispatch_adder:
        config = config.with_overrides(battery_dispatch_adder=battery_dispatch_adder)
    if gas_offer_curve:
        config = config.with_overrides(gas_offer_curve=True)
    # Measured ISO-month delivered gas (EIA-923) instead of annual + shape.
    if gas_monthly_actuals:
        config = config.with_overrides(gas_monthly_actuals=True)
    # Econ-ramp rendering sweep (run_calibration_full --curve-n / --curve-exp):
    # offer_curve_smoothing_n / offer_curve_smoothing_exp; None entries keep
    # the ScenarioConfig defaults.
    if curve_smoothing:
        config = config.with_overrides(
            **{k: v for k, v in curve_smoothing.items() if v is not None}
        )
    # Top-of-stack outage allocation for CC_REGULAR (run_calibration_full
    # --cc-derate-from-top): partial outages truncate the expensive end of
    # the offer curve instead of scaling every tranche pro-rata.
    if cc_derate_from_top:
        config = config.with_overrides(cc_outage_derate_from_top=True)
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
    # Priced import/export node: the external zone joins the topology and its
    # import tranches + export sinks join the fleet below; the measured
    # interchange schedule then stays out of demand (no double count).
    import_generators: list = []
    # Default the CAISO per-hub intertie flag so the later corridor-limit check
    # is bound on every path; it is only set True inside the priced-interchange
    # block below (CAISO-only), so a non-priced or non-CAISO run keeps it False.
    caiso_per_hub = False
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
        # Year-grounded import ladder: the priced node's neighbor-hub blocks
        # are gas-priced, so each single-year calibration solve pins the ladder
        # to its own year (IMPORT_TRANCHES_BY_YEAR); un-tabulated years fall
        # back to the static default inside build_import_generators.
        # Forecast-grade reference-price interface (PJM today): replace the
        # fitted tranches with one import/export pseudo-gen per neighbor, priced
        # hourly from neighbor gas x heat-rate x load-shape (mc overwritten by
        # inject_reference_price_mc after assembly). Gated to ISOs in
        # INTERFACE_NEIGHBORS; byte-identical (falls through to the fitted node)
        # otherwise. See docs/reference-price-interface.md.
        caiso_per_hub = (
            getattr(config, "caiso_per_hub_intertie", False) and iso == "CAISO"
        )
        if caiso_per_hub:
            # Two per-hub signed WECC corridors: COI/Path-66 at the Malin hub
            # (WECC_PNW → NP15) and Path-46/WOR at the Palo Verde hub (WECC_DSW →
            # SP15), each a single net direction over its own real link.
            # Recovers BOTH the per-hub basis and per-hub netting (arbitrage-free
            # hub pricing applied post-assembly); the simultaneous-import cap is
            # the interface limit re-homed onto the two corridor links.
            from market_sim.model.transmission import build_caiso_per_hub_intertie

            import_generators = build_caiso_per_hub_intertie(border_carbon)
        elif getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO":
            # Single signed WECC intertie: import leg + export leg share one
            # net direction over a shared directional cap (arbitrage-free hub
            # pricing applied post-assembly). Replaces the separate import
            # tranches + export sinks so the LP cannot import-cheap and stay
            # long in the same hour.
            from market_sim.model.transmission import build_caiso_bidir_intertie

            import_generators = build_caiso_bidir_intertie(border_carbon)
        elif getattr(config, "reference_price_interface", False) and (
            iso in INTERFACE_NEIGHBORS
        ):
            import_generators = build_reference_price_node(iso)
        else:
            import_generators = build_import_generators(
                iso, border_carbon, year=year
            ) + build_export_sinks(iso)
        # Manitoba Hydro firm-hydro import (MISO only): ~10-15 TWh/yr of firm
        # contracted hydro into MISO-North, OUTSIDE the gas-margin reference-price
        # seam. A SEPARATE block priced as firm hydro (low, near-constant offer),
        # landed directly in MISO-North (build_miso_firm_imports) and ADDED to the
        # reference node's seam gens. The must-flow firm floor is applied
        # post-assembly (inject_miso_firm_imports). No-op for non-MISO ISOs.
        if getattr(config, "miso_firm_imports", False):
            from market_sim.model.transmission import build_miso_firm_imports

            import_generators = import_generators + build_miso_firm_imports(iso)
        iso_config = extend_with_import_node(iso_config)
        if caiso_per_hub:
            # Split the single WECC_import node into the two per-hub corridors
            # (WECC_PNW → NP15, WECC_DSW → SP15) and re-home the import links +
            # the 8.3 GW simultaneous-import interface limit onto them, matching
            # the zones build_caiso_per_hub_intertie placed its tranches in.
            from market_sim.model.transmission import split_caiso_import_node_per_hub

            iso_config = split_caiso_import_node_per_hub(iso_config)
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
    # Seasonal interface envelope: expand the scalar TTC to a per-hour matrix
    # where a measured monthly limit exists (NYISO Central-East). No-op (1-D)
    # for ISOs/years without one.
    ttc = _apply_iso_monthly_ttc(ttc, iso_config, iso, year, demand.shape[1])
    # Aggregate interface limits (CAISO's simultaneous WECC import cap): resolve
    # the configured link groups to flow-column indices for the LP. Empty (no
    # extra rows) for ISOs without an interface_limits entry.
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )
    # Measured WECC corridor deliverability envelope (CAISO per-hub only): cap
    # each corridor link's import-direction flow at the per-(month × hour-of-day)
    # p95 measured net import (an ATC proxy that tightens midday), so the LP can
    # no longer pull the neighbors' idle thermal tranches over the cheap-priced
    # hub up to the 8.3 GW simultaneous cap. One-sided hourly upper bounds, added
    # to the interface groups; export keeps the physical TTC. No-op off the flag
    # or when the year has no measured interchange (byte-identical).
    forward_atc = caiso_per_hub and getattr(config, "caiso_corridor_atc_forward", False)
    if forward_atc or (
        caiso_per_hub and getattr(config, "caiso_corridor_flow_limit", False)
    ):
        from market_sim.model.transmission import build_caiso_corridor_flow_groups

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
            from market_sim.config.constants import CAISO_CORRIDOR_FLOW_PERCENTILE

            cap_label = f"measured p{CAISO_CORRIDOR_FLOW_PERCENTILE:g} ATC proxy"
        if corridor_env:
            corridor_groups = build_caiso_corridor_flow_groups(
                iso_config.links, corridor_env
            )
            interface_groups = interface_groups + corridor_groups
            logger.info(
                "%s %d: WECC corridor deliverability cap on %d link(s) — %s; "
                "median DSW %.1f GW / PNW %.1f GW; midday tighter",
                iso,
                year,
                len(corridor_groups),
                cap_label,
                float(np.median(corridor_env.get("WECC_DSW", [np.nan]))) / 1000.0,
                float(np.median(corridor_env.get("WECC_PNW", [np.nan]))) / 1000.0,
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
    hydro_units, hydro_monthly_energy = _hydro_fleet(
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
    if getattr(config, "gas_st_netload_drag", False):
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
    # Shape the priced import/export node by the measured EIA-930 diurnal
    # interchange envelope (import overnight, export the midday solar glut) so
    # the node stops clearing a flat all-hours import that floors the midday
    # price. Only fires with priced interchange + the opt-in flag + a measured
    # envelope; otherwise the static node is unchanged.
    if priced_interchange and getattr(config, "interchange_shaping", False):
        from market_sim.model.transmission import inject_interchange_shape

        export_only = getattr(config, "interchange_shaping_export_only", False)
        if inject_interchange_shape(fleet_arrays, iso, year, export_only=export_only):
            logger.info(
                "%s %d: priced node shaped by measured EIA-930 interchange "
                "envelope (%s)",
                iso,
                year,
                "export midday only — imports uncapped"
                if export_only
                else "import overnight / export midday",
            )
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

        if inject_miso_seam_flow_limit(fleet_arrays, iso, year):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured EIA-930 "
                "BA-to-BA deliverability envelope (p%g; SPP/South clip toward "
                "~0 import, PJM keeps its measured eastern transfer)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE,
            )
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

    # CAISO local-RA CT_PEAKER reliability floor: hold simple-cycle gas peakers
    # online through the hot-day afternoon-evening ramp at a temperature-driven
    # commitment fraction (clip(slope*(TMAX-T0),0,cap) x available capacity),
    # keyed to the load-weighted CAISO daily max temperature. Recovers the local
    # capacity-area reliability energy an energy-only LP leaves on the (cheaper)
    # CC fleet (transmission.inject_caiso_ct_reliability_floor).
    if getattr(config, "caiso_ct_reliability_floor", False):
        from market_sim.model.transmission import (
            inject_caiso_ct_reliability_floor,
        )

        _ct_slope = float(getattr(config, "caiso_ct_floor_slope_per_c", 0.047))
        _ct_t0 = float(getattr(config, "caiso_ct_floor_t0_c", 25.0))
        _ct_cap = float(getattr(config, "caiso_ct_floor_cap", 0.46))
        _ct_base = float(getattr(config, "caiso_ct_floor_base", 0.0))
        if inject_caiso_ct_reliability_floor(
            fleet_arrays, iso, year, _ct_slope, _ct_t0, _ct_cap, _ct_base
        ):
            logger.info(
                "%s %d: local-RA CT_PEAKER reliability floor — peakers held "
                "online on afternoons/evenings at clip(%.3f + %.3f*(TMAX-%.0f), "
                "%.3f, %.2f) x available capacity (temperature hot-limb + "
                "year-round baseline)",
                iso,
                year,
                _ct_base,
                _ct_slope,
                _ct_t0,
                _ct_base,
                _ct_cap,
            )

    # NYISO firm import baseload: HQ/Ontario flow firm regardless of NY's hourly
    # price, so floor the matching priced-node rows at their firm fraction
    # (transmission.inject_nyiso_firm_imports). Only fires with priced
    # interchange + the flag + a matching import row.
    if priced_interchange and getattr(config, "nyiso_firm_imports", False):
        from market_sim.model.transmission import inject_nyiso_firm_imports

        if inject_nyiso_firm_imports(fleet_arrays, iso, year):
            logger.info(
                "%s %d: firm import baseload floored (HQ/Ontario must-flow)",
                iso,
                year,
            )

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

    # Manitoba firm-hydro import floor (MISO only): the contracted firm baseload
    # flows into MISO-North every hour regardless of MISO's hourly price (the
    # firm-schedule pattern; transmission.inject_miso_firm_imports). Only fires
    # with priced interchange + the flag + the block in the fleet.
    if priced_interchange and getattr(config, "miso_firm_imports", False):
        from market_sim.model.transmission import inject_miso_firm_imports

        if inject_miso_firm_imports(fleet_arrays, iso, year):
            logger.info(
                "%s %d: Manitoba firm-hydro import baseload floored (must-flow)",
                iso,
                year,
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
    # ERCOT per-zone gas-hub basis: shift each gas unit to its zone's measured
    # regional hub (Waha-cheap West/Permian, dearer North/East-Texas and South)
    # so the merit order stops over-running DFW/North CCs on flat Waha-discounted
    # gas. Mean-zero anchored so the aggregate gas level is preserved. Same order
    # as the resolve_fuel_prices apply_monthly=True branch: after the
    # plant-monthly / hub overlay, before the dual-fuel min. No-op unless
    # ercot_zonal_gas_basis is set (ERCOT only).
    apply_ercot_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
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
    dual_fuel_oil_mask = (
        dual_fuel_switch_mask(fuel_prices, fleet_arrays, config, year)
        if getattr(config, "dual_fuel_oil_reattribution", False)
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
    # Reference-price seam: overwrite each neighbor pseudo-gen's mc row with its
    # hourly reference price ± hurdle (the cost is hourly, so it could not ride
    # in the static vom). mc_bid inherits it (the import gens take no startup
    # markup). No-op unless the reference node is in the fleet, so non-reference
    # runs stay byte-identical.
    if getattr(config, "reference_price_interface", False) and (
        iso in INTERFACE_NEIGHBORS
    ):
        if inject_reference_price_mc(
            fleet_arrays, mc_base, iso, year, config.gas_price_path
        ):
            logger.info(
                "%s %d: reference-price interface — %d neighbor seams priced "
                "from gas x heat-rate x load-shape (hurdle in $/MWh)",
                iso,
                year,
                len(INTERFACE_NEIGHBORS.get(iso, [])),
            )
    # CAISO measured-hub import pricing: overwrite each priced-import tranche's mc
    # row with the measured WECC neighbor-hub LMP it proxies (Mid-C/Malin for the
    # PNW blocks, Palo Verde for the desert-SW blocks) + per-tranche border carbon,
    # replacing the static bundle-fitted ladder. The real delivered cost of the
    # imported energy: seasonal (spring runoff) and negative in the solar glut, so
    # it both lowers the over-high body and reproduces the negative midday tail
    # (DIAGNOSIS-caiso-import-ladder-2026-06-19). No-op (byte-identical) unless
    # caiso_import_hub_prices is on AND the measured intertie parquet is present.
    # Single signed WECC intertie: one arbitrage-free injector reprices both
    # legs (import = hub + per-tranche carbon, export = hub) off the measured
    # hub, superseding the separate import-hub / export-hub / gas-coupling /
    # solar-shape injectors below (those target the legacy two-mechanism node).
    per_hub_intertie = (
        getattr(config, "caiso_per_hub_intertie", False) and iso == "CAISO"
    )
    if per_hub_intertie and getattr(config, "caiso_intertie_reference_price", False):
        # FORWARD seam: price each corridor from the reference-price formula
        # ((HH + basis) × HR × load-shape) instead of the measured hub LMP, so
        # the seam stays live in a forecast year and is validated — not pinned —
        # against the measured realization (CLAUDE.md #10/#12).
        from market_sim.model.transmission import (
            inject_caiso_per_hub_reference_prices,
        )

        if inject_caiso_per_hub_reference_prices(
            fleet_arrays, mc_base, iso, year, carbon_price, config.gas_price_path
        ):
            logger.info(
                "%s %d: per-hub WECC intertie — FORWARD reference price per "
                "corridor ((HH+basis)×HR×load-shape; PNW@Malin gross-load, "
                "DSW@Palo-Verde net-load), arbitrage-free, one direction per hour "
                "per corridor (measured hub kept only as backcast validation)",
                iso,
                year,
            )
    elif per_hub_intertie:
        from market_sim.model.transmission import (
            inject_caiso_per_hub_intertie_prices,
        )

        if inject_caiso_per_hub_intertie_prices(
            fleet_arrays, mc_base, iso, year, carbon_price
        ):
            logger.info(
                "%s %d: per-hub WECC intertie — two signed corridors (Malin/COI "
                "→ NP15, Palo Verde/Path-46 → SP15), each priced at its OWN "
                "measured hub (per-hub basis + per-hub netting, arbitrage-free, "
                "one direction per hour per corridor)",
                iso,
                year,
            )
    bidir_intertie = getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO"
    if not per_hub_intertie and bidir_intertie:
        from market_sim.model.transmission import inject_caiso_bidir_intertie_prices

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
    # The legacy two-mechanism injectors (separate import-hub / export-hub /
    # solar-shape) target the pooled WECC_import node; the per-hub and bidir nodes
    # supersede them. Gas-coupling still applies (it shifts the desert-SW gas
    # tranches, which the per-hub node keeps in WECC_DSW).
    legacy_intertie = not per_hub_intertie and not bidir_intertie
    if legacy_intertie and getattr(config, "caiso_import_hub_prices", False):
        from market_sim.model.transmission import inject_caiso_import_hub_prices

        if inject_caiso_import_hub_prices(
            fleet_arrays, mc_base, iso, year, carbon_price
        ):
            logger.info(
                "%s %d: import tranches repriced to measured WECC intertie "
                "hub LMPs (Mid-C / Palo Verde) — static ladder bypassed",
                iso,
                year,
            )
        # Symmetric export side of the same bidirectional intertie: price the
        # neighbor-export sink at the measured hub too, so CAISO exports its
        # midday glut whenever its internal price drops below the neighbor's
        # (the static $8 block only bit near $0; the model was stuck importing
        # 100% of hours and never reversing to the measured +3.5 GW export).
        from market_sim.model.transmission import inject_caiso_export_hub_prices

        if inject_caiso_export_hub_prices(fleet_arrays, mc_base, iso, year):
            logger.info(
                "%s %d: neighbor-export sink repriced to the measured WECC "
                "intertie hub LMP — intertie can reverse to export",
                iso,
                year,
            )

    # CAISO gas-coupled imports: shift the desert-SW gas import tranches
    # (DSW_CCGT, DSW_CT) by the measured commodity-gas delta so they track the
    # same Henry-Hub-plus-citygate-basis spot the hub-basis overlay applies to
    # in-state gas (PLAN-caiso-gas-coupled-imports-2026-06-20). No-op unless
    # caiso_import_gas_coupling is on AND the measured gas series are available;
    # pairs with --gas-hub-basis-overlay so both legs price off the same gas.
    if not bidir_intertie and getattr(config, "caiso_import_gas_coupling", False):
        from market_sim.model.transmission import inject_caiso_import_gas_coupling

        if inject_caiso_import_gas_coupling(fleet_arrays, mc_base, config, year):
            logger.info(
                "%s %d: desert-SW gas import tranches (DSW_CCGT/DSW_CT) coupled "
                "to the measured commodity-gas delta (tracks --gas-hub-basis-overlay)",
                iso,
                year,
            )

    # CAISO desert-SW solar-shaped import offer: collapse the DSW_solar_PV block
    # toward the negative keep-running floor in the net-load belly so the marginal
    # midday import bids sub-$0 (Palo Verde spring solar glut), restoring the
    # CAISO negative midday tail. No-op unless caiso_import_solar_shape is on;
    # applies on top of the gas coupling. Net load is the LP-served load (net of
    # must-run) less utility solar/wind generation.
    if not bidir_intertie and getattr(config, "caiso_import_solar_shape", False):
        from market_sim.model.transmission import inject_caiso_import_solar_shape

        net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        if inject_caiso_import_solar_shape(fleet_arrays, mc_base, config, net_load):
            logger.info(
                "%s %d: desert-SW solar import (DSW_solar_PV) offer collapsed "
                "toward the negative keep-running floor in the net-load belly "
                "(negative midday tail)",
                iso,
                year,
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
    if getattr(config, "storage_as_commitment", False) and iso == "ERCOT":
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

    dispatch_kwargs = dict(
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
        hydro_monthly_energy=hydro_monthly_energy,
        hydro_gen_idx=hydro_gen_idx,
        T=config.hours,
    )
    # Priced import-node monthly net-interchange band (NYISO boundary-flow
    # reconciliation): pins the node's net throughput to the measured EIA-930
    # schedule. Part of the LP feasible region (same for P0/P1), so it warm-starts
    # cleanly. No keys (identical LP) unless the reconciliation was built above.
    if import_node_recon is not None:
        node_idx, recon_lo, recon_hi = import_node_recon
        dispatch_kwargs.update(
            import_node_gen_idx=node_idx,
            import_node_monthly_lo=recon_lo,
            import_node_monthly_hi=recon_hi,
        )

    # Energy+reserve co-optimization (config.energy_reserve_coopt; PJM-gated
    # until other ISOs are validated). Reserve-eligible units are dispatchable
    # thermal; the requirement is the structural 1.5 x most-severe single
    # contingency (fleet-derived, forecast-responsive), and the published
    # two-step ORDC curve prices a shortfall so the reserve clearing price
    # emerges as the balance-row dual and lifts the energy LMP. This replaces
    # the post-solve ORDC overlay (derive_pjm_ordc_overlay.py) for co-opt runs.
    if getattr(config, "energy_reserve_coopt", False) and config.iso == "ERCOT":
        # ERCOT: the published ORDC reserve demand curve enters the LP as a
        # VOLL-anchored reserve demand (scarcity.ercot_ordc_demand_steps).
        # Reserve-eligible thermal units split capacity between energy and
        # upward reserve against the shared-headroom constraint, and the reserve
        # clearing price (the balance-row dual) lifts the energy LMP endogenously
        # — RTSPP = LMP + reserve price. Replaces the post-solve ORDC overlay
        # for co-opt runs. The curve is constant across hours; the scarcity
        # *incidence* comes from the hourly fleet availability in the headroom
        # RHS, so the requirement is flat at the demand curve's top.
        if getattr(config, "ercot_multiproduct_as_coopt", False):
            # MULTI-PRODUCT AS stack: one co-opt demand curve per AS product
            # (RegUp/RRS/ECRS/NonSpin), additive and cascading. The binding
            # product's balance-row dual is the MCPC, formed endogenously — the
            # forward analogue of the measured DAM-AS overlay. Pair with
            # commitment_enabled for the phantom-headroom fix (the P2 solve's
            # availability zeroes idle slow-start units out of the reserve pool).
            from market_sim.results.scarcity import (
                ercot_multiproduct_reserve_coopt_inputs,
            )

            (
                coopt_req,
                coopt_elig,
                coopt_pen,
                coopt_w,
                coopt_mask,
                coopt_counts,
                coopt_class,
                coopt_hr_elig,
                coopt_hr_prod,
            ) = ercot_multiproduct_reserve_coopt_inputs(
                config, fleet_arrays, config.hours
            )
            dispatch_kwargs.update(
                reserve_requirement=coopt_req,
                reserve_eligible=coopt_elig,
                reserve_storage=True,
                ordc_penalties=coopt_pen,
                ordc_step_widths=coopt_w,
                reserve_balance_zone_mask=coopt_mask,
                reserve_balance_ordc_counts=coopt_counts,
                reserve_balance_class=coopt_class,
                reserve_headroom_eligible=coopt_hr_elig,
                reserve_headroom_products=coopt_hr_prod,
            )
            from market_sim.config.constants import ERCOT_AS_PRODUCTS

            logger.info(
                "energy+reserve co-opt (ERCOT MULTI-PRODUCT): %d AS products %s, "
                "per-product req means %s MW, %d steps total, %d headroom tiers",
                len(ERCOT_AS_PRODUCTS),
                [p[0] for p in ERCOT_AS_PRODUCTS],
                [int(coopt_req[p].mean()) for p in range(coopt_req.shape[0])],
                len(coopt_pen),
                int(coopt_hr_prod.shape[0]),
            )
        else:
            from market_sim.results.scarcity import ercot_reserve_coopt_inputs

            coopt_req, coopt_elig, coopt_pen, coopt_w = ercot_reserve_coopt_inputs(
                config, fleet_arrays, config.hours
            )
            dispatch_kwargs.update(
                reserve_requirement=coopt_req,
                reserve_eligible=coopt_elig,
                reserve_storage=True,  # ERCOT batteries are the dominant RRS/ECRS
                # provider — count their headroom as reserve, else scarcity
                # overshoots.
                ordc_penalties=coopt_pen,
                ordc_step_widths=coopt_w,
            )
            logger.info(
                "energy+reserve co-opt (ERCOT): VOLL-anchored ORDC demand, "
                "req top %.0f MW, %d steps ($%.0f-$%.0f), %d reserve-eligible units",
                float(coopt_req[0]),
                len(coopt_pen),
                float(coopt_pen.min()),
                float(coopt_pen.max()),
                int(coopt_elig.sum()),
            )
    elif getattr(config, "energy_reserve_coopt", False) and config.iso == "PJM":
        from market_sim.config.constants import PJM_ORDC_CURVE_PATH
        from market_sim.data.fleet import FUEL_TYPE_NAMES
        from market_sim.results.scarcity import (
            RESERVE_FUEL_TYPES,
            largest_single_contingency_mw,
            load_pjm_measured_reserve_requirement,
            load_pjm_ordc_curve,
            pjm_ordc_shortfall_steps,
            pjm_primary_reserve_requirement,
        )

        elig = np.array(
            [
                FUEL_TYPE_NAMES[i] in RESERVE_FUEL_TYPES
                for i in fleet_arrays.fuel_type_idx
            ],
            dtype=bool,
        )
        lsc = largest_single_contingency_mw(
            fleet_arrays.pmax,
            fleet_arrays.availability,
            elig,
            plant_code=fleet_arrays.plant_code,
        )
        # Backcast: use the measured PJM Primary Reserve requirement (a reliability
        # input, like the outage overlay), hour-varying. Forecast: the fleet-
        # responsive 1.5x-MSSC formula. The measured series is never tuned to the
        # LMP; the fleet MSSC is logged either way for the forecast cross-check.
        measured = (
            load_pjm_measured_reserve_requirement(config.weather_year, config.hours)
            if config.mode == "backcast"
            else None
        )
        if measured is not None:
            req_hourly = measured
            req_src = "measured PJM pr_req"
        else:
            req_hourly = pjm_primary_reserve_requirement(lsc, config.hours)
            req_src = "1.5x-MSSC formula"
        curve = load_pjm_ordc_curve(PJM_ORDC_CURVE_PATH)[("Primary", "RTO")]
        # ORDC shortfall steps: inner band sized to the peak requirement so
        # reserves can fall to zero in every hour; the +offset shoulder is added
        # per hour to the (possibly hour-varying) requirement.
        max_offset = max(o for o, _ in curve)
        _, ordc_pen, ordc_w = pjm_ordc_shortfall_steps(curve, float(req_hourly.max()))
        dispatch_kwargs.update(
            reserve_requirement=req_hourly + max_offset,
            reserve_eligible=elig,
            ordc_penalties=ordc_pen,
            ordc_step_widths=ordc_w,
        )
        logger.info(
            "energy+reserve co-opt (PJM): MSSC %.0f MW (formula req %.0f), using "
            "%s req mean %.0f MW (+%.0f ORDC shoulder), %d reserve-eligible units",
            lsc,
            1.5 * lsc,
            req_src,
            float(req_hourly.mean()),
            max_offset,
            int(elig.sum()),
        )
    elif getattr(config, "energy_reserve_coopt", False) and config.iso == "NYISO":
        # NYISO: LOCATIONAL nested reserve co-optimization. The system NYCA tier
        # plus the East ⊃ SENY ⊃ NYC regional tiers (NYISO_RCPF_PRODUCTS /
        # NYISO_RCPF_LOCATIONAL, FERC ER21-502 / RS4 anchors) each become a
        # reserve "family" — a balance row over its member zones. Holding the
        # import-constrained downstate pocket to its locational reserve keeps the
        # NYC peaker/quick-start headroom in reserve, so in tight hours those
        # units clear on energy and the reserve shortfall stacks a scarcity price
        # into the downstate zonal LMP (the locational tail the NYCA-aggregate
        # energy LP and the post-solve RCPF adder cannot dispatch).
        from market_sim.results.scarcity import nyiso_reserve_coopt_inputs

        (
            coopt_req,
            coopt_elig,
            coopt_pen,
            coopt_w,
            coopt_mask,
            coopt_counts,
            coopt_class,
            coopt_online_gated,
            coopt_online_rho,
        ) = nyiso_reserve_coopt_inputs(config, fleet_arrays, config.hours, zone_names)
        dispatch_kwargs.update(
            reserve_requirement=coopt_req,
            reserve_eligible=coopt_elig,
            reserve_storage=True,  # downstate batteries back reserve too
            ordc_penalties=coopt_pen,
            ordc_step_widths=coopt_w,
            reserve_balance_zone_mask=coopt_mask,
            reserve_balance_ordc_counts=coopt_counts,
            reserve_balance_class=coopt_class,
            reserve_online_gated=coopt_online_gated,
            reserve_online_rho=coopt_online_rho,
        )
        import numpy as _np

        _elig2d = _np.atleast_2d(coopt_elig)
        logger.info(
            "energy+reserve co-opt (NYISO): %d locational reserve families "
            "(%d 10-min/quick-start), %d ORDC steps ($%.0f-$%.0f), "
            "%d full-fleet / %d quick-start reserve-eligible units",
            coopt_mask.shape[0],
            int((_np.asarray(coopt_class) == 1).sum()),
            len(coopt_pen),
            float(coopt_pen.min()) if len(coopt_pen) else 0.0,
            float(coopt_pen.max()) if len(coopt_pen) else 0.0,
            int(_elig2d[0].sum()),
            int(_elig2d[1].sum()) if _elig2d.shape[0] > 1 else 0,
        )
        if coopt_online_gated is not None:
            logger.info(
                "  NYISO synchronised reserve ON: online-gated spinning class "
                "(rho=%.2f), %d gated reserve family/ies",
                float(coopt_online_rho),
                int((_np.asarray(coopt_class) == 2).sum()),
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
    }

    # P2 (optional): screen CC/CT commitment on P1 prices vs base MC, pin
    # coal to its P1 dispatch, and re-solve (a single LP solve).
    result_p1 = None
    if config.commitment_enabled:
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
    )
    return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk)


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
