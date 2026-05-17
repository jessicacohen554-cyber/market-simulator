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
    demand_growth_rate: float = 0.01  # annual
    renewable_buildout_pace: str = "mid"  # "slow", "mid", "aggressive"
    storage_deployment: str = "mid"
    retirement_aggressiveness: str = "mid"
    rec_price_nuclear: float = 0.0  # $/MWh, e.g. NY/IL Zero Emission Credit ~$17
    rec_price_wind: float = 0.0  # $/MWh, stacks with IRA PTC
    rec_price_solar: float = 0.0  # $/MWh
    rec_price_gas_cc: float = 0.0  # $/MWh, for CCS-equipped or clean H2 CC
    rec_price_storage: float = 0.0  # $/MWh on discharge
    rps_enabled: bool = True  # whether to enforce RPS as LP constraint
    electrolyzer_type: str = "pem"  # "pem" or "alkaline" — sets H2 fuel cost
    h2_available_year: int = 2032  # year H2 turbines enter the candidate pool
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
    discount_rate: float = 0.08
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
    ira_expiry_year: int = 2035
    electrolyzer_efficiency_override: float | None = None  # overrides lookup
    ccs_capture_rate: float = 0.90  # fraction of CO2 captured by CCUS
    co2_transport_storage_cost: float = 15.0  # $/tCO2 for captured CO2
    egs_pmin_fraction: float = 0.20  # EGS turn-down floor (fraction of rated)
    offshore_wind_cf_override: float | None = None  # overrides OFFSHORE_WIND_PARAMS

    # Tier 3 (calibration)
    renewable_cf_adjustment: float = 1.0
    basis_differential_factor: float = 1.0

    def cache_key(self) -> str:
        """Return a deterministic 16-char hash of the full config."""
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
    "renewable_buildout_pace": 1,
    "storage_deployment": 1,
    "retirement_aggressiveness": 1,
    "rec_price_nuclear": 1,
    "rec_price_wind": 1,
    "rec_price_solar": 1,
    "rec_price_gas_cc": 1,
    "rec_price_storage": 1,
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
    "discount_rate": 2,
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
    "ira_expiry_year": 2,
    "electrolyzer_efficiency_override": 2,
    "ccs_capture_rate": 2,
    "co2_transport_storage_cost": 2,
    "egs_pmin_fraction": 2,
    "offshore_wind_cf_override": 2,
    "renewable_cf_adjustment": 3,
    "basis_differential_factor": 3,
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
