"""Configuration objects for the LCE portfolio optimizer.

``PortfolioConfig`` is the single user-facing knob bag, mirroring the
``ScenarioConfig`` dataclass style of the market simulator (a flat, typed,
default-rich dataclass). Every solver input traces back to a field here or to
the resource-cost table; there are no magic numbers buried in the LP builder.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

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
    """Which cost column to read from the resource table: ``low``/``mid``/``high``."""
    discount_rate: float = 0.07
    """Reserved for future capital-recovery conversion (see PS-01)."""

    # --- (4) Resource limits & selection -----------------------------------
    active_resources: tuple[str, ...] | None = None
    """Subset of resource names to make available; ``None`` = the table's
    ``active_minimal`` flag (keeps the minimal example small)."""
    resource_caps_mw: dict[str, float] = field(default_factory=dict)
    """Per-resource max buildable MW, overriding the table default
    (the user's 'set a capacity max on nuclear and other resources')."""
    resource_floors_mw: dict[str, float] = field(default_factory=dict)
    """Per-resource existing/committed MW floor (``cap_min``)."""

    # --- (5) Premium / netting semantics -----------------------------------
    excess_sale_fraction: float = 1.0
    """Fraction of LMP received when selling excess clean generation to the grid.
    1.0 = full wholesale resale; 0.0 = curtail for free. Finalized in PS-02."""
    storage_epsilon: float = 0.001
    """Throughput tiebreaker ($/MWh) on charge+discharge to avoid degeneracy
    (mirrors the market-sim storage epsilon rule)."""

    # --- Load intake / growth ----------------------------------------------
    load_growth_rate: float = 0.0
    """Annual load-growth CAGR applied to the intake profile (optional)."""
    load_growth_years: int = 0
    """Number of years of ``load_growth_rate`` to compound onto the intake."""

    def with_overrides(self, **changes) -> "PortfolioConfig":
        """Return a copy with ``changes`` applied (dataclasses.replace wrapper)."""
        return replace(self, **changes)
