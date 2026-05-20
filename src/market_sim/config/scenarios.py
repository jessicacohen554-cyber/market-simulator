"""Scenario definitions and loading for simulation runs."""

from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path

import yaml


@dataclass
class ScenarioConfig:
    """Full configuration for a single simulation scenario.

    Fields are organized into tiers (see ``TIER_TAGS``): structural
    settings, scenario levers, expert sensitivities, and calibration knobs.

    All monetary parameters (fuel prices, carbon prices, VOLL, VOM, LCOE)
    are in 2026 real USD anchored to January 1, 2026. See
    constants.REAL_DOLLAR_BASE_YEAR.
    """

    # Tier 0 (structural)
    weather_year: int = 2024
    iso: str = "ERCOT"
    voll: float = 5000.0  # $/MWh, ERCOT default
    hours: int = 8760

    # Tier 1 (scenario levers)
    gas_price_path: str = "mid"  # "low", "mid", "high" or path to CSV
    carbon_price: float = 0.0  # $/ton CO2
    carbon_price_path: str = "zero"  # "zero", "low", "mid", "high"; used when carbon_price is 0.0
    nox_price: float = 0.0  # $/ton NOx
    demand_growth_rate: float = 0.01  # flat override used only when no structured rates exist
    demand_growth_path: str = "mid"  # "low", "mid", "high" — selects from DEMAND_GROWTH_RATES
    renewable_buildout_pace: str = "mid"  # "slow", "mid", "aggressive"
    storage_deployment: str = "mid"
    retirement_aggressiveness: str = "mid"
    eac_price_nuclear: float = 0.0  # $/MWh, e.g. NY/IL Zero Emission Credit ~$17
    eac_price_wind: float = 0.0  # $/MWh, onshore wind REC
    eac_price_solar: float = 0.0  # $/MWh
    eac_price_gas_cc_ccs: float = 0.0  # $/MWh, CCS-equipped gas CC only (45Q-linked)
    eac_price_storage: float = 0.0  # $/MWh on discharge
    eac_price_offshore_wind: float = 0.0  # $/MWh, offshore-specific EAC (may differ from onshore)
    eac_price_geothermal: float = 0.0  # $/MWh, clean firm generation credit
    rps_enabled: bool = True  # whether to enforce RPS as LP constraint
    electrolyzer_type: str = "pem"  # "pem" or "alkaline" — sets H2 fuel cost
    h2_available_year: int = 2035  # was 2032.
    # Source: engineering judgment. §45V credit terminates for construction
    # after Dec 31, 2027 (OBBBA). Without $3/kg credit, green H2 fuel cost
    # ~2x higher. Deployment delayed to mid-2030s when electrolyzer costs
    # and renewable LCOE decline enough to compensate.
    ccs_available_year: int = 2030  # year CCUS enters the candidate pool
    egs_available_year: int = 2030  # year EGS enters the candidate pool
    offshore_wind_available_year: int = 2030
    offshore_wind_eligible_isos: list[str] = field(
        default_factory=lambda: ["CAISO"]
    )

    # Tier 2 (expert/sensitivity)
    gas_seasonality: bool = True  # Apply monthly Henry Hub seasonality shape
    storage_rte_4hr: float = 0.85
    storage_rte_8hr: float = 0.80
    nominal_discount_rate: float = 0.08  # Nominal WACC, $/MWh LCOE basis
    retirement_consecutive_years: int = 2  # fallback if no per-fuel override
    retirement_years_coal: int = 1  # coal retires after 1 unprofitable year
    retirement_years_gas_ct: int = 2  # CTs get 2 years
    retirement_years_gas_cc: int = 3  # modern CCs get 3 years (most flexible/valuable)
    retirement_fom_multiplier_coal: float = 1.3  # coal faces higher effective FOM
    # (regulatory risk, carbon liability, rising insurance). Source: Lazard LCOE 2024.
    retirement_fom_multiplier_gas_ct: float = 1.0
    retirement_fom_multiplier_gas_cc: float = 1.0
    retirement_reserve_margin: float = 0.15  # 15% reserve margin over peak net demand
    # Don't retire thermal below (peak_demand - firm_clean) * (1 + reserve_margin)
    fixed_om_gas_cc: float = 12.0  # $/kW-yr
    fixed_om_gas_ct: float = 8.0
    fixed_om_coal: float = 40.0
    ira_ptc_wind: float = 26.0  # $/MWh
    ira_itc_solar: float = 0.30  # 30%
    ira_itc_storage: float = 0.30
    # IRA credit schedule per OBBBA (One Big Beautiful Bill Act),
    # enacted July 4, 2025.
    # Wind/solar: §45Y/§48E BOC before July 4, 2026 + in-service by Dec 31,
    # 2027. For an annual model, treat 2027 as the last year wind/solar
    # credits are available.
    ira_wind_solar_last_year: int = 2027
    # Other clean (storage, nuclear, geothermal, hydro): §48E graduated
    # phaseout 2029-2033. 100% through 2028, 80% in 2029, 60% in 2030,
    # 40% in 2031, 20% in 2032, 0% after.
    ira_other_clean_last_full_year: int = 2028
    ira_other_clean_phaseout_end: int = 2033
    # §45V hydrogen production credit: construction start by Dec 31, 2027.
    ira_h2_45v_last_year: int = 2027
    # §45Q CCUS credit: extended but phasing out post-2032.
    ira_ccus_45q_last_year: int = 2032
    electrolyzer_efficiency_override: float | None = None  # overrides lookup
    ccs_capture_rate: float = 0.90  # fraction of CO2 captured by CCUS
    co2_transport_storage_cost: float = 15.0  # $/tCO2 for captured CO2
    egs_pmin_fraction: float = 0.20  # EGS turn-down floor (fraction of rated)
    offshore_wind_cf_override: float | None = None  # overrides OFFSHORE_WIND_PARAMS

    # Tier 2 (expert/sensitivity) — CCS retrofit parameters
    ccs_retrofit_hr_penalty: float = 0.12     # Fractional heat rate increase from capture parasitic load.
                                               # Applied as: retrofit_hr = base_hr × (1 + penalty).
                                               # 0.12 = 12% penalty. Source: NETL Cost & Performance
                                               # Baseline Rev 4, 2021. Range in literature: 0.10–0.18.
    ccs_retrofit_capex_kw: float = 900.0      # $/kW for post-combustion capture retrofit.
                                               # Source: NETL 2021, Sargent & Lundy 2022.
                                               # Lower than greenfield (~$1400/kW) because host plant exists.
    ccs_retrofit_vom_adder: float = 8.0       # $/MWh additional VOM for capture O&M, solvent, compression.
                                               # Source: NETL Cost & Performance Baseline Rev 4.
    ccs_retrofit_capture_rate: float = 0.90   # Fraction of CO2 captured. 0.90 = 90%.
                                               # Source: NETL design basis for amine scrubbing.
    ccs_retrofit_available_year: int = 2028   # Earliest year retrofits can occur.
    ccs_retrofit_max_gw_per_year: float = 3.0 # GW/yr retrofit throughput cap per ISO.
                                               # Source: engineering judgment — EPC capacity constraint.
    ccs_retrofit_min_remaining_life: int = 15 # Only retrofit units with ≥ N years remaining useful life.
                                               # Avoids retrofitting units near retirement.

    # Tier 2 (expert/sensitivity) — Fleet aggregation control
    heat_rate_bin_count: int | None = None    # Override default bin count per fuel type.
                                               # None = use HEAT_RATE_BINS defaults (3 bins).
                                               # Set to 5, 10, etc. for finer granularity.
                                               # More bins = more LP variables = slower solve.
                                               # Recommended: 3 (default) for production runs,
                                               # 5-10 for CCS/carbon sensitivity analysis.

    # Tier 2 (expert/sensitivity) — CAMPD operational binning
    # When True the thermal fleet is built from the CAMPD-derived bin
    # assignments (one row per plant, aggregated to ~120 operational bins
    # with a 4-tranche Must-Run / Committed / Economic / Peaking capacity
    # structure). When False the legacy equal-width heat-rate binning of
    # aggregate_fleet() is used. See docs/binning-methodology.md.
    use_campd_bins: bool = True
    campd_bins_path: str = "inputs/custom-bin-assignments.csv"
    plant_registry_path: str = "inputs/master-plant-registry.csv"
    unknown_zone_default: str = "South_Central"  # zone for bins tagged "Unknown"

    # Tier 3 (calibration) — CAMPD peaking-tranche heat-rate penalties.
    # The top (Peaking) slice of a bin is a separate LP generator whose
    # heat rate is the bin HR scaled by these duct-firing / peaking-increment
    # multipliers, so scarcity output bids above the economic tranche.
    cc_peak_hr_penalty: float = 1.15    # CC duct-firing increment
    ct_peak_hr_penalty: float = 1.10    # CT / gas-steam peaking increment
    coal_peak_hr_penalty: float = 1.08  # Coal peaking increment

    # Tier 3 (calibration) — Two-tranche HR multipliers for the committed
    # vs economic dispatch range. Real units have convex input-output
    # curves: less efficient at part load (the committed tranche) and
    # more efficient in the upper load range (the economic tranche).
    # Each bin's base capacity therefore splits into a Committed tranche
    # (part-load range): HR × multiplier > 1.0, and an Economic tranche
    # (upper load range): HR × multiplier < 1.0. Neither tranche carries
    # a Pmin floor. Source: GE/Siemens OEM IO curves; CEMS input-output
    # curve analysis.
    cc_committed_hr_mult: float = 1.23    # CC part-load penalty ~23%
    cc_econ_hr_mult: float = 0.96         # CC incremental HR ~4% below avg
    ct_committed_hr_mult: float = 1.28    # CT part-load penalty ~28%
    ct_econ_hr_mult: float = 0.97         # CT incremental HR ~3% below avg
    gas_st_committed_hr_mult: float = 1.32  # Gas steam part-load penalty ~32%
    gas_st_econ_hr_mult: float = 0.97     # Gas steam incremental HR
    coal_committed_hr_mult: float = 1.22  # Coal part-load penalty ~22%
    coal_econ_hr_mult: float = 0.97       # Coal incremental HR
    must_run_cf: float = 0.85  # assumed CF for CHP must-run emissions post-processing

    # Tier 2 (expert/sensitivity) — Unit commitment heuristic (2-pass)
    commitment_enabled: bool = False  # default off — opt-in for calibration.
                                       # When True, a price-based commitment
                                       # filter runs between two LP solves to
                                       # approximate integer unit commitment.
    commitment_irr_hurdle: float = 0.07  # 7% return required on startup cost.
    # A run must generate margin >= startup_per_mw × (1 + irr) to justify
    # the wear and capital risk of a start. Source: operator interviews,
    # 7-10% typical for merchant thermal assets.
    commitment_storage_weight: float = 1.0  # 0 disables. The P2 commitment
    # screen discounts a run's startup-hurdle margin in hours when storage is
    # net-charging, so a cycling unit is not committed purely to serve
    # speculative battery-charging load. Storage net-discharge hours keep
    # full weight — storage and thermal are complements at the peak.
    commitment_storage_in_merit_floor: float = 0.0  # 0 disables. When > 0,
    # an hour whose storage-charge weight falls below this floor is dropped
    # from the in-merit runs the commitment screen detects: a deep
    # battery-charging trough breaks a cycling unit's run, so the shorter
    # pieces face the min-run filter on their own. Stronger than the
    # hurdle-only discount above, which never changes which hours run.
    # 1.0 drops every net-charging hour; 0.85 drops only deep troughs.
    commitment_screen_coal: bool = True  # When False, CAMPD coal is not
    # commitment-screened in P2; instead it is pinned to its P1 dispatch, so
    # coal gains no new generation in P2 (P1 locks it) and the gas
    # re-dispatch happens around fixed coal. Lets a calibration isolate the
    # gas-internal commitment effect without coal absorbing decommitted gas.

    # Tier 3 (calibration)
    renewable_cf_adjustment: float = 1.0
    basis_differential_factor: float = 1.0
    td_loss_factor: float = 0.0  # Gross-up of EIA-930 demand, as a fraction.
    # EIA-930 "Demand" is generation-side: Demand + Total Interchange = Net
    # Generation (verified to <0.01 TWh for ERCOT 2023/2024), so the demand
    # target already equals net generation and needs no gross-up to match the
    # fleet's actual output. The former 0.058 came from eGRID net generation
    # (472.9 TWh) / EIA-930 demand (446.8 TWh) − 1, but eGRID's total includes
    # ~28 TWh of behind-the-meter CHP self-supply that EIA-930 grid demand
    # excludes — so that ratio was mostly mislabeled BTM CHP, not T&D losses,
    # and inflated grid generation by the BTM amount. Applied as:
    # demand = raw_demand × (1 + factor).
    vintage_capacity_ramp: bool = True  # When True, renewable capacity for a
    # calibration year ramps month-by-month from each plant's commercial
    # operation date (EIA-860 Operating Month/Year). When False, flat
    # year-end capacity is used (pre-calibration behavior).

    # Tier 3 (calibration) — Coal take-or-pay supply-curve tranches
    # Each coal bin is split into three tranches modeling its take-or-pay
    # fuel contract: a fraction of capacity at a fraction of fuel passthrough.
    # Tranche 1 (contracted volume) bids at VOM only — its fuel is sunk;
    # higher tranches bid progressively more of full fuel cost. The fractions
    # need not sum to 1.0 but normally do. Source: calibrated to EIA-930
    # 2023-2024 hourly ERCOT coal dispatch and eGRID 2023/2024 actuals.
    coal_tranche_1_frac: float = 0.30        # Take-or-pay capacity fraction
    coal_tranche_1_fuel_passthrough: float = 0.00  # VOM only — fuel sunk
    coal_tranche_2_frac: float = 0.25        # Partially contracted
    coal_tranche_2_fuel_passthrough: float = 0.35
    coal_tranche_3_frac: float = 0.45        # Economic dispatch
    coal_tranche_3_fuel_passthrough: float = 1.00  # Full fuel cost

    # Tier 3 (calibration) — CAMPD coal pricing. Plant-specific coal
    # delivered fuel cost is a per-year trajectory built in fuel.py
    # (COAL_PRICE_LIGNITE_BY_YEAR / COAL_PRICE_PRB_BY_YEAR). PRB plants
    # have rail/coal take-or-pay contracts; that sunk-cost share now flows
    # through the per-bin _mustrun tranche (which bids at VOM only), so
    # the default delivered-cost passthrough on the remaining tranches is
    # 1.0. Override below 1.0 only to study a flat PRB delivered-cost
    # discount on top of the must-run staircase.
    coal_prb_contract_passthrough: float = 1.00

    gas_price_override: float | None = None  # When set, pins the annual
    # Henry Hub price ($/MMBtu) to a measured value instead of the AEO
    # trajectory — used to backcast a calibration year against EIA actuals.
    # Its presence also marks the run as a historical calibration backcast,
    # so renewable capacity resolves to that year's EIA-860 year-end actual
    # rather than the forward-projection RENEWABLE_INSTALLED_MW base.

    @property
    def real_discount_rate(self) -> float:
        """Real discount rate via Fisher equation: (1+nominal)/(1+inflation) - 1."""
        from market_sim.config.constants import INFLATION_RATE
        return (1.0 + self.nominal_discount_rate) / (1.0 + INFLATION_RATE) - 1.0

    def cache_key(self) -> str:
        """Return a deterministic 16-char hash of the full config.

        Hashes the stored ``nominal_discount_rate`` field (``asdict`` covers
        it). ``real_discount_rate`` is a derived property, deterministic given
        ``INFLATION_RATE``, so it is not part of the hash.
        """
        payload = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def with_overrides(self, **kwargs) -> "ScenarioConfig":
        """Return a copy of this config with the given fields replaced."""
        return replace(self, **kwargs)

    def _non_default_values(self) -> dict:
        """Return a dict of fields whose values differ from the defaults."""
        defaults = ScenarioConfig()
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if getattr(self, f.name) != getattr(defaults, f.name)
        }

    def to_yaml(self, path) -> None:
        """Write only non-default fields to a YAML file at ``path``."""
        Path(path).write_text(
            yaml.safe_dump(self._non_default_values(), sort_keys=True)
        )

    def to_yaml_full(self, path) -> None:
        """Write every field to a YAML file at ``path`` for reproducibility."""
        Path(path).write_text(yaml.safe_dump(asdict(self), sort_keys=True))

    @classmethod
    def from_yaml(cls, path) -> "ScenarioConfig":
        """Load a config from YAML, merging stored overrides onto defaults."""
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(**data)


TIER_TAGS: dict[str, int] = {
    "weather_year": 0,
    "iso": 0,
    "voll": 0,
    "hours": 0,
    "gas_price_path": 1,
    "carbon_price": 1,
    "carbon_price_path": 1,
    "nox_price": 1,
    "demand_growth_rate": 1,
    "demand_growth_path": 1,
    "renewable_buildout_pace": 1,
    "storage_deployment": 1,
    "retirement_aggressiveness": 1,
    "eac_price_nuclear": 1,
    "eac_price_wind": 1,
    "eac_price_solar": 1,
    "eac_price_gas_cc_ccs": 1,
    "eac_price_storage": 1,
    "eac_price_offshore_wind": 1,
    "eac_price_geothermal": 1,
    "rps_enabled": 1,
    "electrolyzer_type": 1,
    "h2_available_year": 1,
    "ccs_available_year": 1,
    "egs_available_year": 1,
    "offshore_wind_available_year": 1,
    "offshore_wind_eligible_isos": 1,
    "gas_seasonality": 2,
    "storage_rte_4hr": 2,
    "storage_rte_8hr": 2,
    "nominal_discount_rate": 2,
    "retirement_consecutive_years": 2,
    "retirement_years_coal": 2,
    "retirement_years_gas_ct": 2,
    "retirement_years_gas_cc": 2,
    "retirement_fom_multiplier_coal": 2,
    "retirement_fom_multiplier_gas_ct": 2,
    "retirement_fom_multiplier_gas_cc": 2,
    "retirement_reserve_margin": 2,
    "fixed_om_gas_cc": 2,
    "fixed_om_gas_ct": 2,
    "fixed_om_coal": 2,
    "ira_ptc_wind": 2,
    "ira_itc_solar": 2,
    "ira_itc_storage": 2,
    "ira_wind_solar_last_year": 2,
    "ira_other_clean_last_full_year": 2,
    "ira_other_clean_phaseout_end": 2,
    "ira_h2_45v_last_year": 2,
    "ira_ccus_45q_last_year": 2,
    "electrolyzer_efficiency_override": 2,
    "ccs_capture_rate": 2,
    "co2_transport_storage_cost": 2,
    "egs_pmin_fraction": 2,
    "offshore_wind_cf_override": 2,
    "ccs_retrofit_hr_penalty": 2,
    "ccs_retrofit_capex_kw": 2,
    "ccs_retrofit_vom_adder": 2,
    "ccs_retrofit_capture_rate": 2,
    "ccs_retrofit_available_year": 2,
    "ccs_retrofit_max_gw_per_year": 2,
    "ccs_retrofit_min_remaining_life": 2,
    "heat_rate_bin_count": 2,
    "use_campd_bins": 2,
    "campd_bins_path": 2,
    "plant_registry_path": 2,
    "unknown_zone_default": 2,
    "commitment_enabled": 2,
    "commitment_irr_hurdle": 2,
    "commitment_storage_weight": 2,
    "commitment_storage_in_merit_floor": 2,
    "commitment_screen_coal": 2,
    "cc_peak_hr_penalty": 3,
    "ct_peak_hr_penalty": 3,
    "coal_peak_hr_penalty": 3,
    "cc_committed_hr_mult": 3,
    "cc_econ_hr_mult": 3,
    "ct_committed_hr_mult": 3,
    "ct_econ_hr_mult": 3,
    "gas_st_committed_hr_mult": 3,
    "gas_st_econ_hr_mult": 3,
    "coal_committed_hr_mult": 3,
    "coal_econ_hr_mult": 3,
    "must_run_cf": 3,
    "renewable_cf_adjustment": 3,
    "basis_differential_factor": 3,
    "td_loss_factor": 3,
    "vintage_capacity_ramp": 3,
    "coal_tranche_1_frac": 3,
    "coal_tranche_1_fuel_passthrough": 3,
    "coal_tranche_2_frac": 3,
    "coal_tranche_2_fuel_passthrough": 3,
    "coal_tranche_3_frac": 3,
    "coal_tranche_3_fuel_passthrough": 3,
    "coal_prb_contract_passthrough": 3,
    "gas_price_override": 3,
}


@dataclass
class SweepDefinition:
    """A parameter sweep that expands into multiple ``ScenarioConfig`` objects."""

    sweep: dict[str, list] = field(default_factory=dict)
    mode: str = "factorial"

    def generate(self) -> list[ScenarioConfig]:
        """Expand the sweep into a list of configs (cartesian product)."""
        if not self.sweep:
            return [ScenarioConfig()]
        names = list(self.sweep.keys())
        value_lists = [self.sweep[name] for name in names]
        configs = []
        for combo in itertools.product(*value_lists):
            overrides = dict(zip(names, combo))
            configs.append(ScenarioConfig().with_overrides(**overrides))
        return configs

    @classmethod
    def from_yaml(cls, path) -> "SweepDefinition":
        """Load a sweep definition from a YAML file at ``path``."""
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(
            sweep=data.get("sweep", {}),
            mode=data.get("mode", "factorial"),
        )
