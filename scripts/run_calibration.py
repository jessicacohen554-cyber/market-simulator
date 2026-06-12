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
    HOURS_PER_YEAR,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    VOM,
    resolve_priced_interchange,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
)
from market_sim.data.hydro import load_hydro_budget  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    _AGGREGATABLE_FUELS,
    _hour_to_month_index,
    COAL_MUSTRUN_BY_PLANT,
    Generator,
    aggregate_fleet,
    apply_coal_tranches,
    assemble_mc,
    bins_to_fleet,
    campd_tranche_fuel_frac,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_campd_bins,
    load_fleet_from_csv,
    split_coal_tranches,
    split_gas_tranches,
    thermal_tranche_overrides,
)
from market_sim.data.fuel import (  # noqa: E402
    apply_coal_supply_pricing,
    apply_dual_fuel_pricing,
    apply_plant_monthly_fuel_prices,
    coal_passthrough_by_supply,
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
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    build_export_sinks,
    build_import_generators,
    build_incidence_matrix,
    extend_with_import_node,
    get_ttc_array,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.eac import (  # noqa: E402
    apply_eac_to_mc,
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
REFERENCE_PATH: Path = REPO / "inputs" / "calibration" / "calibration_reference.json"

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
                f"band->multiplier, got {type(bands).__name__}")
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
                f"{', '.join(sorted(merged))}")
        if not isinstance(bands, dict):
            raise ValueError(
                f"offer-curve delta for {cls!r} must be an object of "
                f"band->delta, got {type(bands).__name__}")
        for band, delta in bands.items():
            if band not in merged[cls]:
                raise ValueError(
                    f"offer-curve delta for unknown band {cls}.{band!r}; "
                    f"{cls} bands: {', '.join(sorted(merged[cls]))}")
            merged[cls][band] = merged[cls][band] + delta
    return merged


# Calibrated PJM thermal offer curve (per-class band heat-rate multipliers on
# AHR x delivered fuel price). Tuned against the 2023 & 2024 EIA-930 fuel mix
# and PJM hub-average LMP (inputs/calibration). Built in two stages, mirroring
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
    "CC_REGULAR": {"committed": 0.6624, "econ_low": 0.7344,
                   "econ_high": 0.8928, "peak": 1.62,
                   "econ_low_share": 0.50, "pct_peaking": 8.0},
    "CC_CHP": {"committed": 0.6624, "econ_low": 0.684,
               "econ_high": 0.8208, "peak": 1.62,
               "econ_low_share": 0.50, "pct_peaking": 8.0},
    "CT_CHP": {"committed": 0.864, "econ_low": 0.864,
               "econ_high": 0.864, "peak": 1.008, "econ_low_share": 0.50},
    "CT_PEAKER": {"committed": 0.8784, "econ_low": 0.9792,
                  "econ_high": 1.4256, "peak": 4.0,
                  "econ_low_share": 0.526, "pct_peaking": 7.0},
    "ST_GAS": {"committed": 0.4752, "econ_low": 0.6552,
               "econ_high": 0.90, "peak": 3.024,
               "econ_low_share": 0.50, "pct_peaking": 15.0},
    "COAL_LIGNITE": {"committed": 0.684, "econ_low": 0.8208,
                     "econ_high": 0.828, "peak": 1.116,
                     "econ_low_share": 0.556},
    "COAL_PRB": {"committed": 0.684, "econ_low": 0.5544,
                 "econ_high": 0.8568, "peak": 1.0656,
                 "econ_low_share": 0.556},
    "COAL_BIT": {"committed": 0.648, "econ_low": 0.7056,
                 "econ_high": 0.8064, "peak": 1.044, "econ_low_share": 0.55},
    "COAL_WC": {"committed": 0.612, "econ_low": 0.648,
                "econ_high": 0.7344, "peak": 0.864, "econ_low_share": 0.55},
    "COAL": {"committed": 0.648, "econ_low": 0.684,
             "econ_high": 0.792, "peak": 1.044, "econ_low_share": 0.55},
}



def _calibration_config(
    year: int, iso: str, hours: int, gas_price: float,
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
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
        #   inputs/raw-data/gas_basis_by_iso_month.csv). The overlay replaces
        #   the gas price with HH-month + measured AGT basis in covered
        #   months — THE ISO-NE winter price driver and the dual-fuel switch
        #   trigger (P13). No basis rows exist for other ISOs (the NYISO
        #   Transco Z6 leg is still unsourced), so this is a NEISO-only
        #   repricing.
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
        storage_vintage_ramp=(iso.upper() == "CAISO"),  # CAISO commissioned
        #   3.0 GW of batteries during 2023 and 3.6 GW during 2024 (EIA-860
        #   energy-storage schedule), so a flat year-end fleet overstates the
        #   spring/summer battery capability by 1.5-2 GW — the dispatch caps
        #   ramp month-by-month from each COD instead. ERCOT/PJM stay flat:
        #   their calibrations were tuned against year-end fleets and flip on
        #   only with a recalibration pass (CAISO prompt pack E2).
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
        coal_prb_passthrough_sigmoid=coal_prb_passthrough_sigmoid,  # gas-keyed
        #   PRB passthrough when set; else the flat coal_prb_passthrough.
        coal_mustrun_per_plant=coal_mustrun_per_plant,  # per-plant CAMPD coal
        #   must-run floors when set; else the uniform lignite/PRB overrides.
        coal_drop_pof=coal_drop_pof,  # drop statistical POF on coal (planned
        #   maintenance now comes from the historic outage overlay).
        coal_prb_passthrough_tiered=coal_prb_passthrough_tiered,  # separate
        #   follower-tier PRB sigmoid for low-must-run load-followers.
        gas_st_startup_spread=True,  # amortize ST_GAS startup over the whole
        #   May-Sep season (one seasonal start), not per calendar month.
        # CC and ST_GAS supply curves now come from the unified offer curve
        # below (offer_curve_by_group), so their legacy override triples are
        # left unset. CT_CHP keeps its legacy override (not in the offer curve).
        cc_committed_per_plant=True,   # ground each CC_REGULAR committed % in
        #   CAMPD-observed minimum stable load (fleet.CC_REGULAR_COMMITTED_PCT_
        #   BY_PLANT) instead of the coarse assumed CSV Pct_Committed.
        cc_peaking_per_plant=True,     # the four F-class(late) 2x1 CCs (CBII,
        #   WH2, Rayburn, Temple) move the duct-burner peak band start to 85%
        #   (pct_peaking 15) so the expensive band bites earlier and they back
        #   down out of the 80-90% CF range (fleet.CC_REGULAR_PEAKING_PCT_BY_PLANT).
        ct_committed_hr_override=1.1,  # CT_CHP supply curve above its must-run
        ct_econ_hr_override=1.2,        # BTM + steam-following floor; raised in
        ct_peak_hr_override=1.4,        # run9 (CT_CHP was running too much).
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
            "CC_REGULAR": {"committed": 0.92,
                           "econ_low": 1.20 if iso == "PJM" else (
                               1.16 if iso == "ERCOT" else 1.06),
                           "econ_high": 1.49 if iso == "PJM" else (
                               1.41 if iso == "ERCOT" else 1.27),
                           "peak": 2.25,
                           "econ_low_share": 0.50,
                           "pct_peaking": 8.0},
            "CC_CHP": {"committed": 0.92,
                       "econ_low": 0.95 if iso == "PJM" else 0.96,
                       "econ_high": 1.14 if iso == "PJM" else 1.12,
                       "peak": 2.25,
                       "econ_low_share": 0.50,
                       "pct_peaking": 8.0},
            # CT_CHP cogens: previously driven by the legacy ct_*_hr_override
            # triple (committed 1.10 / econ 1.20 / peak 1.40). Now expressed as
            # an offer curve so the econ ramp and peak are tweakable like every
            # other group. econ_low == econ_high keeps the default a flat 1.20
            # economic block (no dispatch change vs the old single econ value);
            # pull them apart to create a slope. Peaking % stays the CSV value
            # (no pct_peaking key). The ct_*_hr_override fields above are now
            # inert for CT_CHP.
            "CT_CHP": {"committed": 1.20 if iso == "PJM" else 1.10,
                       "econ_low": 1.20,
                       "econ_high": 1.20, "peak": 1.40,
                       "econ_low_share": 0.50},
            # CT/ST committed band raised as a P1 startup-cost proxy: the
            # part-load committed slice only clears when price is high, so
            # peakers stop parking at ~20% CF for hundreds of hours. CT hurdle
            # is committed 1.55 (peak HR mult 13.15); ST hurdle committed 0.81
            # with a slightly lower econ-high / peak top. The CT committed
            # hurdle / econ-low / peak are an ERCOT calibration tune; PJM keeps
            # its own validated CT curve (committed 1.10, econ_low 1.32,
            # peak 13.0).
            # ERCOT committed folds in the run57 baseline (1.55 -> 1.48).
            "CT_PEAKER": {"committed": 1.10 if iso == "PJM" else (
                              1.48 if iso == "ERCOT" else 1.55),
                          "econ_low": 1.20 if iso == "PJM" else 1.27,
                          "econ_high": 1.98,
                          "peak": 13.0 if iso == "PJM" else 13.15,
                          "econ_low_share": 0.526, "pct_peaking": 7.0},
            # ERCOT bands fold in the run57 baseline (committed 0.81->0.91,
            # econ_low 1.05->1.15, econ_high 1.40->1.55). Other ISOs unchanged.
            "ST_GAS": {"committed": 0.91 if iso == "ERCOT" else 0.81,
                       "econ_low": 1.15 if iso == "ERCOT" else 1.05,
                       "econ_high": 1.55 if iso == "ERCOT" else 1.40,
                       "peak": 4.20,
                       "econ_low_share": 0.500, "pct_peaking": 15.0},
            # Coal split by supply: lignite (mine-mouth) raised +0.05 across the
            # board; PRB uses a pure offer curve (sigmoid off) -- higher commit,
            # lower econ-low start, slightly higher econ-high.
            "COAL_LIGNITE": {"committed": 0.95, "econ_low": 1.14,
                             "econ_high": 1.15, "peak": 1.55,
                             "econ_low_share": 0.556},
            # ERCOT econ bands fold in the run57 baseline (econ_low 0.77->0.70,
            # econ_high 1.19->0.94). Other ISOs keep the prior PRB curve.
            # PRB committed-band tuning is applied per-run as an offer-curve
            # delta (e.g. Run-60 -0.05, Run-61 -0.20), not baked in here, so the
            # baseline stays at run57 and every run's tweak is delta-from-run57.
            "COAL_PRB": {"committed": 0.95,
                         "econ_low": 0.70 if iso == "ERCOT" else 0.77,
                         "econ_high": 0.94 if iso == "ERCOT" else 1.19,
                         "peak": 1.48,
                         "econ_low_share": 0.556},
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
            "COAL_BIT": {"committed": 0.90, "econ_low": 0.95,
                         "econ_high": 1.10, "peak": 1.45,
                         "econ_low_share": 0.55},
            "COAL_WC": {"committed": 0.85, "econ_low": 0.90,
                        "econ_high": 1.02, "peak": 1.20,
                        "econ_low_share": 0.55},
            # Generic fallback for coal plants with no EIA-923 receipts / rank
            # (and ISOs not yet derived). Flat baseload curve.
            "COAL": {"committed": 0.90, "econ_low": 0.95,
                     "econ_high": 1.10, "peak": 1.45,
                     "econ_low_share": 0.55},
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
    )
    if any(f.name == "gas_price_override" for f in fields(ScenarioConfig)):
        config = config.with_overrides(gas_price_override=gas_price)
    else:
        logger.warning(
            "ScenarioConfig has no gas_price_override field; "
            "year %d falls back to the '%s' gas-price trajectory",
            year, config.gas_price_path,
        )
    if coal_passthrough is not None:
        config = config.with_overrides(
            coal_prb_contract_passthrough=coal_passthrough
        )
    # PJM uses its own price-calibrated offer curve (the per-class block above
    # carries ERCOT-fitted values for the shared classes). Replacing the whole
    # dict keeps the calibrated PJM curve in one place (_PJM_OFFER_CURVE) and
    # out of the per-band `if iso == "PJM"` ternaries. Operator --offer-curve
    # overrides/deltas below still merge on top, so a sweep starts from the
    # calibrated PJM curve.
    if iso.upper() == "PJM":
        config = config.with_overrides(
            offer_curve_by_group={
                k: dict(v) for k, v in _PJM_OFFER_CURVE.items()
            }
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
                    "-".join(sorted(target)), ttc[i], value,
                )
                ttc[i] = value
    return ttc


def _hydro_fleet(
    iso: str, year: int, zone_names: list[str]
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
    """
    try:
        budget = load_hydro_budget(iso, year)
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
        units.append(Generator(
            unit_id=f"{int(pid)}_hydro",
            name=budget.plant_names[i],
            zone=zone,
            fuel_type="hydro",
            pmax_mw=cap,
            vom=VOM["hydro"],
            eford=0.0,  # availability is captured by the energy budget
            plant_group="hydro",
            plant_code=int(pid),
        ))
        monthly.append(energy)
    if not units:
        return [], None
    return units, np.vstack(monthly)


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
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    coal_bit_sigmoid: bool = False,
    bit_overrides: dict | None = None,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    battery_dispatch_adder: float = 0.0,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
    curve_smoothing: dict[str, float | int | None] | None = None,
    cc_derate_from_top: bool = False,
    must_run_mw: "np.ndarray | None" = None,
    priced_interchange: bool = False,
) -> tuple[object, FleetContext, object | None]:
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
        year, iso, hours, gas_price, coal_passthrough,
        commitment_enabled, commitment_screen_coal,
        coal_lignite_mustrun, coal_prb_mustrun,
        coal_prb_passthrough, outage_source,
        coal_prb_passthrough_sigmoid, coal_mustrun_per_plant,
        coal_drop_pof, coal_prb_passthrough_tiered,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
    )
    # Per-run PRB passthrough sigmoid floor/ceiling tune (run_calibration_full
    # --prb-* flags); None entries leave the ScenarioConfig default in place.
    if prb_overrides:
        config = config.with_overrides(
            **{k: v for k, v in prb_overrides.items() if v is not None})
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
            **{k: v for k, v in bit_overrides.items() if v is not None})
    # Per-plant tranche-config override sheet (run_calibration_full
    # --plant-tranche-config): each listed plant's tranche shares + band HR
    # multipliers come straight from the CSV, bypassing the offer curve.
    if plant_tranche_config:
        config = config.with_overrides(
            plant_tranche_config_path=plant_tranche_config)
    # Daily SOC-cycling cap (run_calibration_full --storage-daily-cycling):
    # bounds storage perfect foresight to within-day arbitrage.
    if storage_daily_cycling:
        config = config.with_overrides(storage_daily_cycling=True)
    # Battery throughput/cycling cost (run_calibration_full --battery-adder):
    # per-MWh-discharged adder that tames LP over-cycling of the BESS fleet.
    if battery_dispatch_adder:
        config = config.with_overrides(
            battery_dispatch_adder=battery_dispatch_adder)
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
            **{k: v for k, v in curve_smoothing.items() if v is not None})
    # Top-of-stack outage allocation for CC_REGULAR (run_calibration_full
    # --cc-derate-from-top): partial outages truncate the expensive end of
    # the offer curve instead of scaling every tranche pro-rata.
    if cc_derate_from_top:
        config = config.with_overrides(cc_outage_derate_from_top=True)
    iso_config = get_iso_config(iso)
    # Priced import/export node: the external zone joins the topology and its
    # import tranches + export sinks join the fleet below; the measured
    # interchange schedule then stays out of demand (no double count).
    import_generators: list = []
    if priced_interchange:
        import_generators = (
            build_import_generators(iso) + build_export_sinks(iso)
        )
        iso_config = extend_with_import_node(iso_config)
    zone_names = iso_config.zone_names

    demand = load_demand(
        iso, year, iso_config, td_loss_factor=config.td_loss_factor,
        include_interchange=not priced_interchange,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, :config.hours]
        wind_cf = wind_cf[:, :config.hours]
        solar_cf = solar_cf[:, :config.hours]

    # Must-run "other" resources (biomass, process gas, ...) serve load
    # exogenously — they run for industrial/process reasons, not LP economics —
    # so net them out of demand before the dispatch so they displace marginal
    # gas instead of being double-counted on top of a fully-served balance.
    if must_run_mw is not None:
        mr = np.asarray(must_run_mw, dtype=float)
        if mr.shape[1] > config.hours:
            mr = mr[:, :config.hours]
        demand = np.maximum(demand - mr, 0.0)

    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = _apply_ttc_overrides(
        iso_config, get_ttc_array(iso_config.links), ttc_overrides
    )

    # Build the dispatch fleet the same way the runner does: CAMPD
    # operational bins for ERCOT (three stepped tranches per bin, nuclear
    # and other non-aggregatable units from EIA-860), the legacy
    # equal-width heat-rate binning otherwise.
    campd_bins = (
        load_campd_bins(config.campd_bins_path, year=year)
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
            g for g in load_fleet_from_csv(iso, iso_config)
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
        if (config.coal_prb_passthrough_sigmoid
                and config.coal_prb_passthrough_tiered):
            # Tiered PRB (ERCOT): low-must-run "prb" load-followers swap
            # the baseload prb curve for the follower-tier one. The tier
            # split is specific to the curated ERCOT prb supply.
            foll = {**pt_by_supply,
                    "prb": prb_follower_passthrough_series(
                        config, year, config.hours)}
            thr = config.coal_prb_follower_mustrun_max

            def _pt_for(g):
                if (g.fuel_type == "coal"
                        and getattr(g, "coal_supply", "") == "prb"
                        and COAL_MUSTRUN_BY_PLANT.get(
                            g.plant_code, 100.0) <= thr):
                    return foll
                return pt_by_supply
            fuel_fracs = [
                campd_tranche_fuel_frac(g, _pt_for(g)) for g in fleet
            ]
        else:
            fuel_fracs = [
                campd_tranche_fuel_frac(g, pt_by_supply) for g in fleet
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
        if (getattr(config, "plant_level_fleet", False)
                and thermal_tranche_overrides(iso)):
            all_gens = load_fleet_from_csv(iso, iso_config)
            synth = fleet_to_bins(all_gens, iso, config)
            if not synth.empty:
                binned = set(zip(
                    synth["Plant_Code"].astype(int), synth["Plant_Group"]
                ))
                thermal_fleet, _ = bins_to_fleet(synth, zone_names, config)
                non_binned = [
                    g for g in all_gens
                    if (int(g.plant_code), g.plant_group) not in binned
                ]
                fleet = non_binned + thermal_fleet
                pt_by_supply = coal_passthrough_by_supply(
                    config, year, config.hours
                )
                fuel_fracs = [
                    campd_tranche_fuel_frac(g, pt_by_supply) for g in fleet
                ]
            else:
                fleet, fuel_fracs = split_coal_tranches(
                    aggregate_fleet(all_gens, n_bins=0), config
                )
        else:
            n_bins = 0 if getattr(config, "plant_level_fleet", False) \
                else config.heat_rate_bin_count
            fleet_base = aggregate_fleet(
                load_fleet_from_csv(iso, iso_config), n_bins=n_bins,
            )
            fleet, fuel_fracs = split_coal_tranches(fleet_base, config)
            # Optional stepped gas offer curve (committed/economic/peaking
            # heat-rate bands) for the per-plant fleet; off by default.
            if getattr(config, "gas_offer_curve", False):
                fleet, fuel_fracs = split_gas_tranches(fleet, fuel_fracs, config)
    # Energy-limited conventional hydro (every ISO): one LP unit per
    # EIA-923-reporting hydro plant, capped by its EIA-860 nameplate per hour
    # and by its measured monthly net generation via the dispatch LP's hydro
    # budget rows. Replaces the flat-monthly must-run injection (which could
    # not peak-shave) and leaves ISOs without hydro data unchanged.
    hydro_units, hydro_monthly_energy = _hydro_fleet(iso, year, zone_names)
    hydro_gen_idx = None
    if hydro_units:
        hydro_gen_idx = np.arange(
            len(fleet), len(fleet) + len(hydro_units), dtype=int
        )
        fleet = fleet + hydro_units
        fuel_fracs = list(fuel_fracs) + [1.0] * len(hydro_units)
        logger.info(
            "%s %d: %d hydro plants in LP (%.0f MW, %.2f TWh monthly budget)",
            iso, year, len(hydro_units),
            sum(g.pmax_mw for g in hydro_units),
            hydro_monthly_energy.sum() / 1e6,
        )
    if import_generators:
        fleet = fleet + import_generators
        fuel_fracs = list(fuel_fracs) + [1.0] * len(import_generators)
        logger.info(
            "%s %d: priced import/export node — %d import tranches "
            "(%.0f MW), %d export sinks (%.0f MW)",
            iso, year,
            sum(1 for g in import_generators if g.pmax_mw > 0),
            sum(g.pmax_mw for g in import_generators),
            sum(1 for g in import_generators if g.pmin_mw < 0),
            -sum(g.pmin_mw for g in import_generators),
        )
    fleet_arrays = generators_to_fleet_arrays(
        fleet, zone_names, hours=config.hours, iso=iso, config=config
    )
    inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)

    # Fuel prices: gas/coal base, then the lignite/PRB supply base for coal
    # (our costs), then the actual EIA-923 monthly per-plant delivered cost
    # on top — so measured monthly cost takes precedence and the supply
    # trajectory is only the base/fallback for plant-months without data.
    fuel_prices = resolve_fuel_prices(
        config, fleet_arrays, year, apply_monthly=False
    )
    if config.coal_supply_repricing:
        apply_coal_supply_pricing(fuel_prices, fleet, config, year)
    apply_plant_monthly_fuel_prices(fuel_prices, fleet_arrays, config, year)
    # Dual-fuel switching last, so the oil-parity min sees the final
    # (per-plant monthly) delivered gas price (PJM only; no-op elsewhere).
    apply_dual_fuel_pricing(fuel_prices, fleet_arrays, config, year)
    carbon_price = resolve_carbon_price(config, year)
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    # Base marginal cost: fuel + VOM + carbon + NOx, then exogenous EACs,
    # then the coal take-or-pay tranche discount. No startup-cost markup.
    mc_base = assemble_mc(
        fleet_arrays, fuel_prices, carbon_price, config.nox_price
    )
    apply_eac_to_mc(mc_base, fleet_arrays, config)
    apply_coal_tranches(mc_base, fleet, fleet_arrays, fuel_fracs, fuel_prices)
    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc -= wind_eac
    solar_mc -= solar_eac

    storage_units = load_eia860_storage(iso, year, config)
    storage = storage_units_to_arrays(storage_units, zone_names)
    # Static (n_storage,) caps, or hour-varying (n_storage, T) when the
    # intra-year COD ramp is on (config.storage_vintage_ramp) and capacity
    # was commissioned mid-year — mid-year GWs stay offline before COD.
    storage_power_cap, storage_energy_cap = storage_cap_profiles(
        storage_units, storage, config.hours
    )

    dispatch_kwargs = dict(
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        voll=config.voll,
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
        hydro_monthly_energy=hydro_monthly_energy,
        hydro_gen_idx=hydro_gen_idx,
        T=config.hours,
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
    # P0: solve with base MC to extract per-month run lengths.
    if _warm:
        r0 = model.solve(mc=mc_base)
    else:
        r0 = solve_dispatch(fleet_arrays, demand, mc=mc_base, **dispatch_kwargs)
    # P1: solve with bid MC = base MC + monthly startup amortization.
    markup = compute_monthly_markup(
        fleet, fleet_arrays, r0.dispatch, config.hours,
        gas_st_season_spread=config.gas_st_startup_spread,
        chp_startup_covered=getattr(config, "chp_startup_covered", False),
    )
    mc_bid = mc_base + markup
    if _warm:
        result = model.solve(mc=mc_bid)
    else:
        result = solve_dispatch(fleet_arrays, demand, mc=mc_bid, **dispatch_kwargs)

    context = FleetContext.from_arrays(
        fleet_arrays, iso_config, wind_cf, wind_cap, solar_cf, solar_cap,
        storage.energy_cap,
    )
    # Everything the P2 commitment pass needs, kept so P2 can be re-run as a
    # post-process (see _commitment_pass / run_p2) without re-solving P0/P1.
    p2_state = {
        "year": year, "iso": iso, "fleet": fleet,
        "fleet_arrays": fleet_arrays, "mc_base": mc_base, "mc_bid": mc_bid,
        "p1_result": result, "demand": demand,
        "dispatch_kwargs": dispatch_kwargs, "config": config,
        "context": context, "storage_units": storage_units,
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
        p1.prices, state["mc_base"], fleet, fa, cfg,
        storage_charge=p1.storage_charge,
        storage_discharge=p1.storage_discharge,
        storage_zone_idx=dk["storage_zone_idx"], demand=state["demand"],
    )
    fa_p2 = apply_commitment_with_coal_pin(
        fa, committed, p1.dispatch, fleet,
        screen_coal=cfg.commitment_screen_coal,
    )
    return solve_dispatch(fa_p2, state["demand"], mc=state["mc_bid"], **dk)


def _generation_twh(result, context: FleetContext) -> dict[str, float]:
    """Return modeled annual generation by fuel (TWh)."""
    gen_per_unit = result.dispatch.sum(axis=1)
    twh: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        twh[fuel] = twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
    twh["wind"] = twh.get("wind", 0.0) + float(
        result.wind_dispatched.sum()
    ) / _MWH_PER_TWH
    twh["solar"] = twh.get("solar", 0.0) + float(
        result.solar_dispatched.sum()
    ) / _MWH_PER_TWH
    return twh


def _print_table(title: str, rows: list[tuple]) -> None:
    """Print a titled, column-aligned text table."""
    print(f"\n  {title}")
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _report_year(year: int, iso: str, result, context: FleetContext,
                  reference: dict, label: str = "") -> None:
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
    year_ref = (
        reference.get("isos", {}).get(iso, {}).get(str(year), {})
    )
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
    gen_rows.append((
        "TOTAL", f"{total_m:.2f}",
        f"{total_b:.2f}" if total_b else "—",
        f"{100.0 * (total_m - total_b) / total_b:+.1f}" if total_b else "—",
    ))
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
        price_rows.append((
            zone,
            f"{zone_price.mean():.2f}",
            str(int((zone_price < 0.0).sum())),
        ))
    system_price = result.prices.mean(axis=0)
    price_rows.append((
        "SYSTEM",
        f"{system_price.mean():.2f}",
        str(int((system_price < 0.0).sum())),
    ))
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

    rows: list[tuple] = [(
        "resource", "installed GW", "potential TWh",
        "model TWh", "model %", "reported TWh", "reported %",
    )]
    for fuel in ("wind", "solar"):
        pot_mwh = potential[fuel]
        curt_mwh = max(pot_mwh - float(dispatched[fuel].sum()), 0.0)
        reported_twh = reported_pct = "—"
        if compare:
            rep_curt = float(
                (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"])
                .clip(lower=0.0).sum()
            )
            rep_pot = float(hsl[f"{fuel}_hsl_mw"].sum())
            reported_twh = f"{rep_curt / _MWH_PER_TWH:.2f}"
            reported_pct = (
                f"{100.0 * rep_curt / rep_pot:.1f}" if rep_pot > 0 else "—"
            )
        rows.append((
            fuel,
            f"{caps[fuel] / 1e3:.2f}",
            f"{pot_mwh / _MWH_PER_TWH:.2f}",
            f"{curt_mwh / _MWH_PER_TWH:.2f}",
            f"{100.0 * curt_mwh / pot_mwh:.1f}" if pot_mwh > 0 else "—",
            reported_twh,
            reported_pct,
        ))
    _print_table("Renewable curtailment — modeled vs reported", rows)
    if hsl is None:
        print(
            f"    (no reported HSL data for {iso} {year}; build with "
            "scripts/build_ercot_hsl.py / build_caiso_hsl.py — ERCOT 2024+ "
            "needs the NP6 report uploads)"
        )
        return
    if not compare:
        print("    (reported comparison suppressed -- full 8760h run "
              "required)")
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
            .clip(lower=0.0).to_numpy(dtype=float)
        )
        monthly[f"{fuel}_model"] = np.bincount(
            month_idx, weights=model_curt, minlength=12
        ) / 1e3
        monthly[f"{fuel}_reported"] = np.bincount(
            month_idx, weights=rep_curt, minlength=12
        ) / 1e3
    monthly_rows: list[tuple] = [
        ("month", "wind model", "wind rptd", "solar model", "solar rptd"),
    ]
    for m in range(12):
        monthly_rows.append((
            str(m + 1),
            f"{monthly['wind_model'][m]:.0f}",
            f"{monthly['wind_reported'][m]:.0f}",
            f"{monthly['solar_model'][m]:.0f}",
            f"{monthly['solar_reported'][m]:.0f}",
        ))
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
        print("\n  Hourly dispatch correlation\n    (no EIA-930 fossil "
              f"series for {year})")
        return

    coal = np.zeros(result.dispatch.shape[1])
    gas = np.zeros(result.dispatch.shape[1])
    for g, fuel in enumerate(context.fuel_types):
        if fuel == "coal":
            coal += result.dispatch[g]
        elif fuel in _GAS_FUEL_TYPES:
            gas += result.dispatch[g]

    stats = check_hourly_dispatch_correlation(
        {"coal": coal, "gas": gas}, eia_hourly
    )
    rows: list[tuple] = [
        ("fuel", "pearson r", "nrmse", "model TWh", "EIA TWh")
    ]
    for fuel in ("coal", "gas"):
        s = stats[fuel]
        rows.append((
            fuel, f"{s['pearson_r']:.3f}", f"{s['nrmse']:.3f}",
            f"{s['model_twh']:.2f}", f"{s['eia_twh']:.2f}",
        ))
    _print_table("Hourly dispatch correlation (vs EIA-930)", rows)


def _build_parser() -> argparse.ArgumentParser:
    """Return the run_calibration argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_calibration",
        description="Run dispatch for calibration years and compare to EIA.",
    )
    parser.add_argument(
        "--year", type=int, nargs="+", required=True,
        help="One or more calibration years (2021-2024).",
    )
    parser.add_argument(
        "--iso", default="ERCOT", help="ISO to calibrate (default ERCOT).",
    )
    parser.add_argument(
        "--hours", type=int, default=8760,
        help="Dispatch horizon in hours (default 8760; 168 for a quick test).",
    )
    parser.add_argument(
        "--ttc-wn", type=float, default=None,
        help="Override the West<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-wsc", type=float, default=None,
        help="Override the West<->South_Central transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-pn", type=float, default=None,
        help="Override the Panhandle<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--coal-passthrough", type=float, default=None,
        help="Override coal_prb_contract_passthrough (PRB take-or-pay "
             "fuel-cost fraction); 1.0 disables the discount.",
    )
    parser.add_argument(
        "--commitment", action="store_true",
        help="Run the P2 unit-commitment pass after P1; both are reported.",
    )
    parser.add_argument(
        "--no-coal-p2", action="store_true",
        help="Pin coal to its P1 dispatch in P2 instead of screening it: "
             "coal gains no new generation in P2 (P1 locks it). Only "
             "meaningful with --commitment.",
    )
    parser.add_argument(
        "--priced-interchange", action=argparse.BooleanOptionalAction,
        default=None,
        help="Serve interchange through the priced import/export node "
             "(import tranches + export sinks in the ISO's external zone) "
             "instead of the measured schedule added to demand. Default per "
             f"ISO: on for {', '.join(sorted(PRICED_INTERCHANGE_DEFAULT_ISOS))} "
             "(no measured-schedule mode), off elsewhere; pass "
             "--no-priced-interchange to force the measured schedule.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: run each requested calibration year and print diagnostics.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    args = _build_parser().parse_args(argv)
    iso = args.iso.upper()
    priced_interchange = resolve_priced_interchange(
        args.priced_interchange, iso)
    reference = _load_reference()
    ttc_overrides = {
        "ttc_wn": args.ttc_wn,
        "ttc_wsc": args.ttc_wsc,
        "ttc_pn": args.ttc_pn,
    }

    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            iso, year, args.hours, gas_price,
        )
        result, context, result_p1, _ = run_year(
            year, iso, args.hours, gas_price, ttc_overrides,
            args.coal_passthrough,
            commitment_enabled=args.commitment,
            commitment_screen_coal=not args.no_coal_p2,
            priced_interchange=priced_interchange,
        )
        if result_p1 is not None:
            _report_year(year, iso, result_p1, context, reference, label="P1")
            _report_year(year, iso, result, context, reference, label="P2")
        else:
            _report_year(year, iso, result, context, reference)


if __name__ == "__main__":
    main()
