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
        # SOCO measured per-year basis, added to fuel_trajectories AND re-exported
        # by constants.py in b0d7f1d8 (PR #6468); only this inventory lagged.
        "GAS_BASIS_DIFFERENTIAL_MEASURED_BY_YEAR",
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
        "ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO",
        # capx D51 (2026-09-04): the dates-ON re-identification of the MISO
        # ratio, resolved only under the default-off gate.
        "ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO",
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
        # capx D57 (2026-09-05): the supply-clearing gate's pre-priced
        # capacity object, its resolver and the resolver's log-once refusal
        # set — added to capacity_market.py by the D57 build, registered here
        # (and re-exported from the constants facade) in the same PR, so the
        # BLOCKING refactor-guards job stays green. Private names are in
        # scope for both the inventory and the facade (cf. the D59 note
        # below). No value touched.
        "ClearedCapacityPrice",
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
        # Added to capacity_market.py by capx D40 (`4d3263c6`, 2026-09-02,
        # NEISO Net ICR de-vintage) WITH the paired `constants.py` re-export
        # but WITHOUT this inventory entry — the STORAGE_TECH_AVAILABLE_YEAR
        # gap below, recurring. The facade contract was never broken: both
        # names resolve from `constants` and are the same objects — this is
        # the inventory catching up. No value touched. Entered 2026-09-02 by
        # the fast-tier repair lane.
        "NET_ICR_HOLD_LAST_RATIO_BY_ISO",
        "NET_ICR_REQUIREMENT_MW_BY_ISO",
        # capx D48 (2026-09-04): PJM accreditation-design devintage + DR-as-supply
        "THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO",
        "FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO",
        "DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO",
        "DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO",
        # capx D52 (2026-09-04): NYISO adequacy-requirement devintage registries
        # (NYSRC Table D.2 forecast peak / adopted IRM / derate per capability year)
        "NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO",
        "NYCA_IRM_ADOPTED_BY_ISO",
        "NYCA_ICAP_UCAP_TRANSLATION_BY_ISO",
        # capx D59 (2026-09-05, d6256c6c): the NYISO LOCALITY (NYC / LI)
        # capacity-area registries, published locality demand-curve vintages,
        # UDR ICAP tranches and gross-CONE table, plus the three locality
        # resolvers. constants.py already re-exported all but
        # _NYISO_LOCALITY_CURVE_LENGTH, so the facade contract was never
        # broken for those seven — this is the inventory catching up, exactly
        # as NET_ICR_HOLD_LAST_RATIO_BY_ISO and STORAGE_TECH_AVAILABLE_YEAR
        # did. No value touched.
        "LOCALITY_CAPACITY_AREAS_BY_ISO",
        "LOCALITY_GROSS_CONE_BY_ISO",
        "LOCALITY_MARKET_DESIGN_VINTAGES",
        "NYISO_LOCALITY_UDR_ICAP_MW",
        "NONFOSSIL_ANNOUNCED_HORIZON_YEARS",
        "PJM_RGGI_ZONE_SHARE",
        # capx D75-R (2026-09-06, #5206/#5229): the PJM VRE ELCC delivery-year
        # vintage registry and the solar class-mix blend share it is built from
        # (FINDING-capx-d75r-2026-09-06.md §1, "what was built") were added to
        # capacity_market.py without the paired inventory entries — the
        # recurring omission the notes above record, which left the BLOCKING
        # refactor-guards job red on main (reported by
        # FINDING-capx-d79p1-2026-09-06.md §6). This SHARE was also the
        # genuinely missing constants.py re-export and is added there in the
        # same commit, exactly as the D67 and D62 resolvers were; its
        # RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO sibling below was already on
        # the facade, so for that one this is the inventory catching up (cf.
        # NET_ICR_HOLD_LAST_RATIO_BY_ISO above). No value touched.
        "PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE",
        "PLANNING_RESERVE_MARGIN_BY_ISO",
        "PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO",
        "QUEUE_CAP_GW",
        "QUEUE_CAP_PER_TECH_GW",
        "RENEWABLE_CAPACITY_CREDIT",
        "RENEWABLE_CAPACITY_CREDIT_BY_ISO",
        "RENEWABLE_ELCC_CURVES_BY_ISO",
        "RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO",  # capx D75-R, see above.
        "RENEWABLE_NQC_CURVES_BY_ISO",
        "RGGI_MEMBER_STATES_BY_YEAR",
        "RGGI_RESERVE_ESCALATION",
        "RGGI_STATE_CO2_BUDGET",
        # FFR-7B Arm 1: the statute-defined RPS eligible-fuel sets.
        "RPS_ELIGIBLE_FUELS_BY_ISO",
        # capx D67 (2026-09-06, 8bc0feb5): PJM's published Reliability
        # Requirement table and its per-ISO gate resolver, added to
        # capacity_market.py by the D67 build without the paired inventory
        # entries — the recurring omission the notes above record, which left
        # the BLOCKING refactor-guards job red on main. The CONSTANT was
        # already re-exported from the constants facade, so for it this is the
        # inventory catching up (cf. NET_ICR_HOLD_LAST_RATIO_BY_ISO above);
        # the RESOLVER below was the genuinely missing re-export and is added
        # to constants.py in the same commit, exactly as its D62 sibling
        # resolve_capacity_going_forward_bar_published was. Public by
        # construction (imported by model/capacity_evolution/retirements.py
        # and scripts/run_capacity_hindcast.py), so both join the frozen
        # surface rather than being made private. No value touched.
        "RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO",
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
        # Added to capacity_market.py by the T1-H storage-entry lane WITH the
        # paired `constants.py` re-export but WITHOUT this inventory entry,
        # which left the frozen surface red on main from 2026-08-31 (reported
        # as a pre-existing failure by FINDING-capx-d16-seam-guard-2026-08-30
        # §3 and FINDING-capx-d4m-ercot-t1h-2026-08-31 §9, fixed by neither).
        # The facade contract itself was never broken — `constants.
        # STORAGE_TECH_AVAILABLE_YEAR` resolves and is the same object — so
        # this is the inventory catching up with a name that is already on the
        # re-exported surface, exactly as PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE
        # above. No value touched.
        "STORAGE_TECH_AVAILABLE_YEAR",
        "STORAGE_TECH_BUILD_SHARE_CAP",
        "STORAGE_TECH_POWER_SHARE",
        # FFR-4E: CAISO's published whole-class storage accreditation, the
        # rung that replaces the by-duration table for an ISO that accredits
        # storage at demonstrated capability instead of by duration.
        "STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO",
        "SeasonalRBDC",
        "THERMAL_ACCREDITATION_BASIS_BY_ISO",
        "THERMAL_ELCC_CLASS_RATING_BY_ISO",
        # capx D75-R (2026-09-06): the per-delivery-year published ELCC
        # class ratings behind pjm_vre_accreditation_vintage. Landed at
        # this home with the facade re-export already in place
        # (config/constants.py), so this line only re-freezes the
        # inventory the name was missing from.
        "THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO",
        "_MISO_DAILY_NET_CONE_PER_MW_DAY",
        "_MISO_NC_NET_CONE_PER_MW_YR",
        "_MISO_RBDC_CURVE",
        # capx D31 (2026-09-02): the published-shape seasonal RBDC point
        # tuples that replaced the first-order cap/zero x-position constants
        # (_MISO_RBDC_CAP_X / _MISO_RBDC_ZERO_X — removed, rule 26) and the
        # parametric _miso_seasonal_curve builder.
        "_MISO_RBDC_FALL_POINTS",
        "_MISO_RBDC_SPRING_POINTS",
        "_MISO_RBDC_SUMMER_POINTS",
        "_MISO_RBDC_WINTER_POINTS",
        "_MISO_SEASON_DAYS",
        "_MISO_SEASON_POINTS",
        "_MISO_VERTICAL_CURVE",
        "_MISO_VERTICAL_STEP",
        "_miso_annual_reduction",
        # NEISO-RC-R R2 (2026-08-31): _NEISO_FCA_ZERO_X (the linear FCA-11
        # geometry's 1.083) is DELETED, not zeroed (rule 26) — the re-derived
        # curves carry _NEISO_MRI_ZERO_X (FCA 13's published tail zero) plus
        # the exact FCA 11/13 published shapes and the measured MRI-era points.
        "_NEISO_FCA11_CURVE",
        "_NEISO_FCA13_CURVE",
        "_NEISO_FCA_CAP_X",
        "_NEISO_FCA_CURVE",
        "_NEISO_MRI_CLEARING_POINTS",
        "_NEISO_MRI_ZERO_X",
        "_NYISO_ICAP_CURVE",
        # capx D59, see the note above. Private names are in scope for this
        # inventory and for the facade (cf. _NYISO_NYCA_CURVE_LENGTH below);
        # this one is the single genuinely missing constants.py re-export.
        "_NYISO_LOCALITY_CURVE_LENGTH",
        "_NYISO_NYCA_CURVE_LENGTH",
        "_PJM_VRR_CURVE",
        "_PJM_VRR_CURVE_2027_2028",
        "_PJM_VRR_CURVE_2028_2029",
        "_NO_DEFAULT_CAP_REFUSED_LOGGED",
        "_SUPPLY_CLEARING_REFUSED_LOGGED",  # capx D57, see the note above.
        "_neiso_fca_vintage_curve",
        "_nyiso_icap_vintage_curve",
        "evaluate_demand_curve",
        "evaluate_renewable_elcc_curve",
        "forward_net_cone_anchor",
        "locality_curve_price_per_firm_mw_yr",  # capx D59, see the note above.
        "resolve_caiso_ra_mpb_anchor",  # FFR-4F, see the note above.
        # capx D67, see the note above.
        "resolve_capacity_adequacy_requirement_published",
        "resolve_capacity_curve_eligible",
        # capx D62 (2026-09-06): the third member of the module's per-ISO
        # capacity-gate family, added alongside its two siblings below without
        # the paired facade re-export — the same omission as FFR-4F/FFR-1C/
        # FFR-4D above. Public by construction (imported by
        # model/capacity_evolution/retirements.py and
        # scripts/run_capacity_hindcast.py), so it joins the frozen surface
        # rather than being made private. Registered (and re-exported)
        # 2026-09-06 by y21.
        "resolve_capacity_going_forward_bar_published",
        "resolve_capacity_market_clearing",
        # capx D57, see the note above.
        "resolve_capacity_market_supply_clearing",
        "resolve_capacity_no_default_cap_convention",
        "resolve_demand_curve_vintage",
        "resolve_locality_curve_vintage",  # capx D59, see the note above.
        "resolve_locality_gross_cone_ratio",  # capx D59, see the note above.
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
