"""Configuration objects for the LCE portfolio optimizer.

``PortfolioConfig`` is the single user-facing knob bag, mirroring the
``ScenarioConfig`` dataclass style of the market simulator (a flat, typed,
default-rich dataclass). Every solver input traces back to a field here or to
the resource-cost table; there are no magic numbers buried in the LP builder.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, replace
from pathlib import Path

HOURS_PER_YEAR = 8760  # non-leap; the tool models a single representative year


@dataclass(frozen=True)
class PortfolioConfig:
    """User-facing configuration for one portfolio-optimization run.

    Fields are grouped: (1) structural, (2) optimization framing, (3) cost
    sensitivities, (4) resource limits, (5) premium/netting semantics. Defaults
    reproduce the minimal working example; production runs override them or feed
    a config file. See ``docs/planning-sessions/`` for the decisions that will
    refine several of these (excess sale price, cost basis, matching semantics).
    """

    # --- (1) Structural -----------------------------------------------------
    iso: str = "SAMPLE"
    """ISO the load has been aggregated to (single node per run)."""
    year: int = 2030
    """Modeled year; drives CF-profile selection and (future) LMP vintage."""
    hours: int = HOURS_PER_YEAR
    profile_shape_year: int | None = None
    """CF-profile shape vintage, decoupled from the modeled ``year`` (real
    profile files are built by ``scripts/build_profiles.py`` for specific
    weather years, e.g. 2024, while ``year`` is typically a future study year
    like 2030). ``None`` (default) keeps the prior implicit behavior:
    ``profiles.build_cf_matrix`` is called with ``year`` and missing files
    warn-and-fall-back to synthetic shapes. When set, the profile file for
    that exact year is REQUIRED — a missing file is a hard
    ``FileNotFoundError``, never a silent synthetic substitution, so a real
    run can't accidentally price a portfolio against the wrong (or absent)
    shape data (reproducibility spirit of ADR 0011)."""

    # --- (2) Optimization framing ------------------------------------------
    mode: str = "premium_cap"
    """``"premium_cap"`` (default, Mode A: max matching s.t. premium <= delta)
    or ``"matching_target"`` (Mode B: min premium s.t. matching >= target)."""
    premium_deltas: tuple[float, ...] = (1.0, 2.0, 5.0, 7.0, 10.0, 20.0)
    """Premium caps ($/MWh above wholesale) to sweep in Mode A. Any values."""
    matching_targets: tuple[float, ...] = (0.8, 0.9, 0.95, 1.0)
    """Hourly CFE matching fractions to sweep in Mode B."""
    strict_hourly_matching: bool = False
    """Mode B only: if True, enforce per-hour ``grid_buy[t] <= (1-target)*load[t]``
    (hard 24/7) instead of the annual-sum matching constraint."""

    # --- (3) Cost sensitivities --------------------------------------------
    lcoe_sensitivity: str = "mid"
    """Which cost column to read from the resource table: ``low``/``mid``/``high``.

    For ``capex_fixed`` rows this selects the ATB case (low=Advanced,
    mid=Moderate, high=Conservative capex). For ``ppa_mwh`` existing resources it
    selects the going-forward energy-cost band."""
    discount_rate: float = 0.07
    """Real discount rate ``r`` used in the capital-recovery factor
    ``CRF = r(1+r)^n / ((1+r)^n - 1)`` that annualizes ATB overnight capex into
    ``fixed_mwyr`` (ADR 0004). Default 0.07 ≈ NREL ATB real WACC."""

    # --- (4) Resource limits & selection -----------------------------------
    active_resources: tuple[str, ...] | None = None
    """Subset of resource names to make available; ``None`` = the table's
    ``active_minimal`` flag (keeps the minimal example small)."""
    resource_caps_mw: dict[str, float] = field(default_factory=dict)
    """Per-resource max buildable MW, overriding the table default
    (the user's 'set a capacity max on nuclear and other resources')."""
    resource_floors_mw: dict[str, float] = field(default_factory=dict)
    """Per-resource existing/committed MW floor (``cap_min``)."""
    eac_premium_mwh: dict[str, float] = field(default_factory=dict)
    """Per-resource override ($/MWh) of the ``eac_premium_mwh`` clean-attribute
    premium column for ``ppa_mwh`` existing resources (ADR 0008). When a resource
    name is present here its value replaces the table column; absent resources use
    the table value. Values must be non-negative. Empty ``{}`` = use the table."""
    gas_price_mmbtu: float = 0.0
    """Delivered natural-gas price override ($/MMBtu) for fuel-burning resources
    (ADR 0012). Resolution precedence: a value > 0 here wins; else the per-ISO
    delivered price from ``data/fuel/gas_prices.csv`` (Henry Hub AEO2025
    Reference ~2030 + the market sim's per-ISO basis differential); else — if a
    fuel-burning resource is active — resource loading raises (a CCS resource
    must never dispatch at zero fuel cost). 0.0 (default) = use the table."""
    ccs_45q_per_ton: float = 85.0
    """IRA §45Q carbon-sequestration credit ($/tCO₂ captured and geologically
    stored), netted off the variable cost of capture-equipped resources as
    ``capture_rate × pre-capture intensity × ccs_45q_per_ton`` (ADR 0012).
    Default 85.0 = 26 U.S.C. §45Q as amended by the IRA 2022 for saline
    geologic storage (cross-checked vs market_sim ``policy/ira.py``
    ``CCUS_45Q_CREDIT_PER_TON = 85.0``). Set 0 to disable the credit. Flat —
    45Q vintage/duration limits deferred per ADR 0012."""
    additionality_only: bool = False
    """If True, only *additional* (newly-built) clean supply may count toward
    hourly matching — existing PPA resources still dispatch but their matched
    energy is excluded from the CFE accounting (ADR 0008). Parsed and validated
    now; the matching-accounting behavior it gates lands in PP-02b, so this flag
    currently has no effect on the LP beyond being carried through the config."""

    # --- (5) Premium / netting semantics -----------------------------------
    excess_sale_fraction: float = 1.0
    """Fraction of LMP received when selling excess clean generation to the grid.
    1.0 = full wholesale resale; 0.0 = curtail for free. Default 1.0 per ADR 0005
    as amended & ratified 2026-07-02: surplus is credited at the full hourly
    ISO-average LMP (the provisional 0.75 basis/cannibalization haircut was
    removed — the hourly LMP already reflects depressed prices in surplus hours,
    so a further scalar haircut double-counts the effect)."""
    storage_epsilon: float = 0.001
    """Throughput tiebreaker ($/MWh) on charge+discharge to avoid degeneracy
    (mirrors the market-sim storage epsilon rule)."""
    # --- Load intake / growth ----------------------------------------------
    load_growth_rate: float = 0.0
    """Annual load-growth CAGR applied to the intake profile (optional)."""
    load_growth_years: int = 0
    """Number of years of ``load_growth_rate`` to compound onto the intake."""
    load_file: str | None = None
    """Path to the facility load-intake file (ADR 0010). ``None`` = the caller
    supplies a path directly (e.g. ``--load`` on the CLI); set here for
    reproducible config-file-driven runs."""
    lmp_file: str | None = None
    """Path to the BAU LMP file (ADR 0011): the calibrated market-sim
    forecast-year export for the modeled year, columns ``(hour, iso, lmp)``.
    No escalation is applied — the vintage in this file is used as-is."""
    emissions_file: str | None = None
    """Path to the hourly grid CO₂-intensity file (ADR 0013): the market-sim
    dispatch export of the **fossil-only average** emission rate for the modeled
    ISO/year, columns ``(hour, iso, fossil_avg_co2_rate)`` in tCO₂/MWh, produced
    by ``scripts/build_fossil_avg_co2_rate.py``. Residual carbon is attributed
    to unmatched grid purchases hour-by-hour:
    ``residual_co2_tons = Σ_t grid_buy[t] × rate[t]`` (attributional / GHG
    Protocol location-based accounting — an *average* factor, never a
    marginal/non-baseload one; ADR 0013 supersedes ADR 0007's marginal-rate
    attribution). ``None`` disables residual-carbon reporting (the rate is
    treated as an all-zero vector), e.g. for the ``SAMPLE`` demo ISO."""

    def __post_init__(self) -> None:
        """Validate field values (runs on construction; dataclass is frozen)."""
        # Canonicalize the ISO once, at the single seam every loader shares
        # (audit finding DL-1): a lowercase iso previously matched the
        # case-normalizing profiles loader but silently missed the exact-match
        # caps/hydro/gas tables, dropping eligibility limits without warning.
        object.__setattr__(self, "iso", str(self.iso).strip().upper())
        if not self.iso:
            raise ValueError("iso must be a non-empty string")
        if self.mode not in ("premium_cap", "matching_target"):
            raise ValueError(
                f"mode must be premium_cap/matching_target, got {self.mode!r}"
            )
        if self.lcoe_sensitivity not in ("low", "mid", "high"):
            raise ValueError(
                f"lcoe_sensitivity must be low/mid/high, got {self.lcoe_sensitivity!r}"
            )
        if not 0.0 <= self.excess_sale_fraction <= 1.0:
            raise ValueError("excess_sale_fraction must be in [0, 1]")
        if self.hours <= 0:
            raise ValueError("hours must be positive")
        if self.profile_shape_year is not None and self.profile_shape_year <= 0:
            raise ValueError("profile_shape_year must be positive when set")
        if self.storage_epsilon < 0:
            raise ValueError("storage_epsilon must be non-negative")
        if self.load_growth_years < 0:
            raise ValueError("load_growth_years must be non-negative")
        if any(d <= 0 for d in self.premium_deltas):
            raise ValueError("premium_deltas must all be positive")
        if any(not 0.0 <= t <= 1.0 for t in self.matching_targets):
            raise ValueError("matching_targets must all be in [0, 1]")
        if any(v < 0 for v in self.eac_premium_mwh.values()):
            raise ValueError("eac_premium_mwh values must be non-negative")
        if self.gas_price_mmbtu < 0:
            raise ValueError("gas_price_mmbtu must be non-negative (0 = use table)")
        if self.ccs_45q_per_ton < 0:
            raise ValueError("ccs_45q_per_ton must be non-negative (0 = disabled)")
        # bool is an int subclass, so `discount_rate: true` would silently
        # mean r = 1.0 (100% real WACC); reject it with the range check
        # (audit findings DL-4/CL-11 — r <= -1 crashed CRF with a raw
        # ZeroDivisionError, r in (-1, 0) silently zeroed annualized capex).
        if isinstance(self.discount_rate, bool) or not (
            0.0 <= self.discount_rate < 1.0
        ):
            raise ValueError(
                f"discount_rate must be a real rate in [0, 1), got "
                f"{self.discount_rate!r}"
            )

    def with_overrides(self, **changes) -> "PortfolioConfig":
        """Return a copy with ``changes`` applied (dataclasses.replace wrapper)."""
        return replace(self, **changes)

    @classmethod
    def from_file(cls, path: str | Path) -> "PortfolioConfig":
        """Build a config from a JSON or YAML file (reproducible runs).

        Unknown keys raise; list-valued fields (``premium_deltas``,
        ``matching_targets``, ``active_resources``) are coerced to tuples. YAML
        requires ``pyyaml`` to be installed; JSON always works.
        """
        import json

        text = Path(path).read_text()
        if str(path).endswith((".yaml", ".yml")):
            try:
                import yaml
            except ImportError as exc:  # pragma: no cover - optional dep
                raise ImportError(
                    "YAML config requires pyyaml; use JSON instead"
                ) from exc
            data = yaml.safe_load(text) or {}
        else:
            data = json.loads(text)

        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        for key in ("premium_deltas", "matching_targets", "active_resources"):
            if key in data and data[key] is not None:
                data[key] = tuple(data[key])
        return cls(**data)
