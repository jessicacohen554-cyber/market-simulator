"""Facade re-export contract for the ``config/constants.py`` split.

The 2026-07-20 constants split (refactor-consolidation plan §5, item D-1)
moved three blocks into ``config/fuel_trajectories.py``,
``config/capacity_market.py`` and ``config/ercot_envelopes.py``, leaving
``config/constants.py`` as scalars plus a facade that re-exports every
moved name. This test freezes that contract: every moved name (public and
private) must keep resolving from ``market_sim.config.constants`` AND be
the very same object as at its new home, so the 130+ pre-split importers
never notice the move.
"""

import importlib

# The frozen moved-name inventory, per new home. Generated from the new
# modules' top-level AST at split time; a name leaving this surface is a
# facade break for pre-split importers, not a routine edit.
MOVED_SURFACE: dict[str, tuple[str, ...]] = {
    "market_sim.config.fuel_trajectories": (
        "BIOMASS_PRICE_PER_MMBTU",
        "CAISO_CITYGATE_TRANSPORT_ADDER",
        "CARBON_PRICE_PATHS",
        "CARB_UNSPECIFIED_IMPORT_EF",
        "COAL_DELIVERY_COMMODITY_SHARE",
        "COAL_HEAT_CONTENT_MMBTU_PER_TON",
        "COAL_MAX_CF_BY_PLANT",
        "COAL_PRICE_BASE",
        "COAL_PRICE_ESCALATION",
        "COAL_PRICE_TRAJECTORIES",
        "COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU",
        "COAL_SIGMOID_BASELINE_SLOPE",
        "COAL_SIGMOID_FLOOR_MIN",
        "COAL_SIGMOID_FOLLOWER_DISCOUNT",
        "COAL_SIGMOID_REP_HR_COAL",
        "COAL_SIGMOID_REP_HR_GAS_CC",
        "COAL_SIGMOID_SLOPE_MAX",
        "COAL_SIGMOID_SLOPE_MIN",
        "GAS_BASIS_DIFFERENTIAL",
        "GAS_MONTHLY_SEASONALITY",
        "HENRY_HUB_TRAJECTORIES",
        "LIGNITE_PRICE_2023_25",
        "MAINTENANCE_MONTHLY_SHAPE",
        "NUCLEAR_FUEL_PRICE_HISTORICAL",
        "OIL_PRICE_PER_MMBTU",
        "OIL_PRICE_TRAJECTORIES",
        # Added to fuel_trajectories by the PJM RGGI lane without the paired
        # facade re-export, which left this frozen inventory red on main
        # (nyiso-114 hit it as a pre-existing failure). Restored to contract:
        # inventory entry + `constants.py` re-export, no value touched.
        "PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE",
        "PRB_COMMODITY_DECLINE",
        "PRB_COMMODITY_FLAT_THROUGH",
        "PRB_COMMODITY_SHARE",
        "PRB_PRICE_BY_YEAR",
        "PRB_RAIL_DIESEL_SHARE",
        "PRB_RAIL_NONDIESEL_SHARE",
        "STATE_CARBON_PRICE_BY_ISO",
        # Re-homed from data/fleet/arrays.py by miso-91 (4732235) to put them
        # under parameter-registry coverage; constants.py already re-exports
        # both, so they join the frozen surface rather than break it.
        "SUMMER_CLASS_DERATE",
        "SUMMER_WEFOR_SHARE",
        "THERMAL_AVAILABILITY",
    ),
    "market_sim.config.capacity_market": (
        "ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO",
        "ADEQUACY_EXTERNAL_TIE_FIRM_MW",
        "AS_REVENUE_PER_KW_YR_BY_ISO",
        "AS_SATURATION_REF_GW_BY_ISO",
        # FFR-4F (2026-08-09, commit 675b9782) added the CAISO RA-MPB capacity
        # anchor and its resolver to capacity_market.py without re-exporting
        # either from the constants facade or registering them here — the same
        # omission as FFR-1C and FFR-4D below, and it turned the BLOCKING
        # refactor-guards job red on main for every branch cut after it.
        # Registered (and re-exported) 2026-08-10.
        "CAISO_RA_MPB_ANCHOR_PER_KW_YR",
        "CAMPD_BINNING_ISOS",
        "CAPACITY_CURVE_ELIGIBLE_BY_ISO",
        "CAP_AND_TRADE_PROGRAMS",
        "CARBON_PROGRAM_PRICE_PATH_ESCALATION_MULTIPLIER",
        "CARB_ALLOWANCE_BUDGET",
        "CARB_FLOOR_ESCALATION",
        "CARB_FLOOR_PRICE",
        "CapAndTradeProgram",
        "CapacityDemandCurvePoint",
        "DEFAULT_MARKET_DESIGN",
        "ERCOT_AS_REVENUE_PER_KW_YR",
        "ERCOT_AS_SATURATION_EXPONENT",
        "ERCOT_AS_SATURATION_REF_GW",
        "FORECAST_POOL_REQUIREMENT_BY_ISO",
        "HISTORIC_OUTAGE_OVERLAY_BY_ISO",
        # FFR-1C (2026-07-31) added this to capacity_market.py and DID
        # re-export it from the constants facade, but left it out of this
        # frozen inventory — so test_moved_surface_is_complete went red on
        # main in the BLOCKING refactor-guards job. Registered 2026-08-01.
        "HYDRO_ACCREDITATION_CREDIT_BY_ISO",
        "MARKET_DESIGN",
        "MARKET_DESIGN_VINTAGES",
        "MISOSeasonRBDC",
        # FFR-7B Arm 3: the per-state MISO clean/carbon-free tier table.
        "MISO_CLEAN_TIER_REGIONS",
        # FFR-7B Arm 2: the per-state MISO RPS compliance-region table.
        "MISO_RPS_COMPLIANCE_REGIONS",
        "MISO_RPS_MIDWEST_FOOTPRINT_ZONES",
        "MISO_SEASONAL_RBDC",
        "MarketDesign",
        "MarketDesignVintage",
        "NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO",
        "NONFOSSIL_ANNOUNCED_HORIZON_YEARS",
        "PJM_RGGI_ZONE_SHARE",
        "PLANNING_RESERVE_MARGIN_BY_ISO",
        "PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO",
        "QUEUE_CAP_GW",
        "QUEUE_CAP_PER_TECH_GW",
        "RENEWABLE_CAPACITY_CREDIT",
        "RENEWABLE_CAPACITY_CREDIT_BY_ISO",
        "RENEWABLE_ELCC_CURVES_BY_ISO",
        "RENEWABLE_NQC_CURVES_BY_ISO",
        "RGGI_MEMBER_STATES_BY_YEAR",
        "RGGI_RESERVE_ESCALATION",
        "RGGI_STATE_CO2_BUDGET",
        # FFR-7B Arm 1: the statute-defined RPS eligible-fuel sets.
        "RPS_ELIGIBLE_FUELS_BY_ISO",
        "RenewableElccCurve",
        "SHORT_TON_TO_METRIC_TONNE",
        "STATE_RPS_ACP",
        "STATE_RPS_FLOORS",
        "STORAGE_ANNUAL_BUILD_CAP_MW",
        "STORAGE_BASE_FLEET_MW",
        "STORAGE_DEGRADATION_REPLACEMENT_FRACTION",
        # Backfilled at FFR-7B: FFR-4D added this to capacity_market + the
        # constants facade without extending this inventory — the test was
        # failing on main for every session (pre-existing, verified at
        # a9e1d084).
        "STORAGE_MEASURED_BASE_FLEET_ISOS",
        "STORAGE_DEPLOYMENT_CEILING_MW",
        "STORAGE_ELCC_BY_DURATION",
        "STORAGE_ELCC_BY_DURATION_BY_ISO",
        "STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO",
        "STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO",
        "STORAGE_ELCC_SATURATION_EXPONENT",
        "STORAGE_TECHS",
        "STORAGE_TECH_BUILD_SHARE_CAP",
        "STORAGE_TECH_POWER_SHARE",
        # FFR-4E: CAISO's published whole-class storage accreditation, the
        # rung that replaces the by-duration table for an ISO that accredits
        # storage at demonstrated capability instead of by duration.
        "STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO",
        "SeasonalRBDC",
        "THERMAL_ACCREDITATION_BASIS_BY_ISO",
        "THERMAL_ELCC_CLASS_RATING_BY_ISO",
        "_MISO_DAILY_NET_CONE_PER_MW_DAY",
        "_MISO_NC_NET_CONE_PER_MW_YR",
        "_MISO_RBDC_CAP_X",
        "_MISO_RBDC_CURVE",
        "_MISO_RBDC_ZERO_X",
        "_MISO_VERTICAL_CURVE",
        "_MISO_VERTICAL_STEP",
        "_NEISO_FCA_CAP_X",
        "_NEISO_FCA_CURVE",
        "_NEISO_FCA_ZERO_X",
        "_NYISO_ICAP_CURVE",
        "_NYISO_NYCA_CURVE_LENGTH",
        "_PJM_VRR_CURVE",
        "_PJM_VRR_CURVE_2027_2028",
        "_PJM_VRR_CURVE_2028_2029",
        "_miso_seasonal_curve",
        "_neiso_fca_vintage_curve",
        "_nyiso_icap_vintage_curve",
        "evaluate_demand_curve",
        "evaluate_renewable_elcc_curve",
        "forward_net_cone_anchor",
        "resolve_caiso_ra_mpb_anchor",  # FFR-4F, see the note above.
        "resolve_capacity_curve_eligible",
        "resolve_capacity_market_clearing",
        "resolve_demand_curve_vintage",
        "seasonal_rbdc_price_per_firm_mw_yr",
    ),
    "market_sim.config.ercot_envelopes": (
        "ERCOT_ONLINE_CAP_DELIV_COEF",
        "ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME",
        "ERCOT_ONLINE_CAP_DELIV_PROFILE_MEASURED",
        "ERCOT_ONLINE_CAP_MEASURED_AVAIL_CLASSES",
        "ERCOT_ONLINE_CAP_SHARE",
        "ERCOT_ONLINE_CAP_SHARE_EXTREME",
        "ERCOT_ONLINE_CAP_SHARE_MEASURED",
        "ERCOT_RTOLCAP_FWD_DELIV_COEF",
        "ERCOT_RTOLCAP_FWD_N_DECILE",
        "ERCOT_RTOLCAP_FWD_N_SEASON",
        "ERCOT_RTOLCAP_FWD_OFFLINE_CLASSES",
        "ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF",
        "ERCOT_RTOLCAP_FWD_OFFLINE_SHARE",
        "ERCOT_RTOLCAP_FWD_ONLINE_CLASSES",
        "ERCOT_RTOLCAP_FWD_ONLINE_SHARE",
        "ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH",
        "ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC",
    ),
}


def test_every_moved_name_resolves_from_constants_facade() -> None:
    """Every moved name resolves from constants and is the same object."""
    constants = importlib.import_module("market_sim.config.constants")
    missing: list[str] = []
    diverged: list[str] = []
    for mod_path, names in MOVED_SURFACE.items():
        home = importlib.import_module(mod_path)
        for name in names:
            if not hasattr(home, name):
                missing.append(f"{mod_path}.{name} (new home lost it)")
                continue
            if not hasattr(constants, name):
                missing.append(f"constants.{name} (facade lost it)")
                continue
            if getattr(constants, name) is not getattr(home, name):
                diverged.append(f"{mod_path}.{name}")
    assert not missing, f"facade re-export broken: {missing}"
    assert not diverged, f"facade name diverged from new home: {diverged}"


def test_moved_surface_is_complete() -> None:
    """No top-level name exists at a new home outside the frozen inventory."""
    for mod_path, names in MOVED_SURFACE.items():
        home = importlib.import_module(mod_path)
        toplevel = {
            n
            for n, v in vars(home).items()
            if not n.startswith("__")
            and not type(v).__name__ == "module"
            and n != "dataclass"
        }
        extra = toplevel - set(names)
        assert not extra, (
            f"{mod_path} grew names the facade does not re-export: {sorted(extra)}"
        )
