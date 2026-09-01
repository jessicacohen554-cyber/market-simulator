"""Carbon pricing and emissions policy."""

from __future__ import annotations

from market_sim.config.constants import (
    CARBON_PRICE_PATHS,
    END_YEAR,
    START_YEAR,
    STATE_CARBON_PRICE_BY_ISO,
)
from market_sim.config.scenarios import ScenarioConfig


def state_carbon_price(config: ScenarioConfig, year: int) -> float | None:
    """Return the ISO's state carbon-program allowance price, or ``None``.

    Looks up :data:`STATE_CARBON_PRICE_BY_ISO` — the CA cap-and-trade
    (CARB) quarterly-auction settlement average for CAISO, and the RGGI
    quarterly-auction clearing-price average for NYISO and NEISO (all six
    New England states are RGGI members), 2023-2025 — so a backcast
    charges every in-state fossil unit the measured allowance cost without
    any per-scenario configuration. Returns ``None`` (caller falls through
    to the scenario carbon path) when ``config.state_carbon_pricing`` is
    off, the ISO has no registered program, or the year is outside the
    measured series (forward years need an allowance-price *trajectory*,
    which is deliberately not seeded here).

    Args:
        config: Scenario config supplying ``iso`` and the
            ``state_carbon_pricing`` toggle.
        year: Simulation year.

    Returns:
        The allowance price in $/tCO2, or ``None`` when not applicable.
    """
    if not getattr(config, "state_carbon_pricing", True):
        return None
    program = STATE_CARBON_PRICE_BY_ISO.get(config.iso)
    if program is None or year not in program:
        return None
    return float(program[year])


def resolve_carbon_price(config: ScenarioConfig, year: int) -> float:
    """Resolve the scalar carbon price ($/tCO2) for a given year.

    Thin, backward-compatible wrapper over the unified carbon-program resolver
    (:func:`market_sim.policy.cap_and_trade.resolve_carbon_program`); returns
    the resolution's ``.price_adder`` (the exogenous allowance-price channel).
    Precedence:

    1. A nonzero ``config.carbon_price`` scenario override is returned directly
       (flat trajectory), unchanged.
    2. The ISO's cap-and-trade program adder: the **measured** CARB/RGGI
       auction average in backcast years, or the **projected** program price in
       forecast years (the EM-6 seam fix — forecast carbon is no longer zero
       for a program ISO). CAISO/NYISO/NEISO carry a program; ERCOT/MISO do not.
    3. Fall through to ``config.carbon_price_path`` in
       :data:`CARBON_PRICE_PATHS` (linear-interpolated across knot years,
       nearest-endpoint clamp outside the range) when no program adder applies.

    **Final additive stage** (capx-D26, outside and after the precedence
    chain): ``config.carbon_price_delta`` is added to whatever the chain
    resolved. It exists so a paired instrument arm can construct a genuine
    carbon-price *increase over the resolved base trajectory* — under
    precedence (1) alone, a "high-carbon" arm on a program ISO silently
    REPLACED an escalating program trajectory with a flat value, i.e. a cut
    (the D23 premise inversion,
    ``docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md``). The
    default 0.0 is an exact no-op on every path; the field is forecast-only
    (``ScenarioConfig.__post_init__`` rule-13 guard) and never armed in a
    keeper or golden posture. The precedence semantics above are unchanged
    for every consumer at the default.

    The scalar returned here is the ISO-wide allowance price used by the
    capacity-evolution screen and the CARB border adder; the fractional-
    membership weighting for a partial-footprint program (PJM) is applied at the
    marginal-cost assembly seam (``data/fleet.py::assemble_mc``), not here.

    Args:
        config: Scenario config supplying the flat carbon price and the
            carbon path name.
        year: Simulation year.

    Returns:
        The carbon price in $/tCO2.
    """
    delta = float(getattr(config, "carbon_price_delta", 0.0) or 0.0)
    return _base_carbon_price(config, year) + delta


def _base_carbon_price(config: ScenarioConfig, year: int) -> float:
    """The precedence chain of :func:`resolve_carbon_price`, without the
    additive ``carbon_price_delta`` stage (see its docstring for the order)."""
    if config.carbon_price != 0:
        return float(config.carbon_price)
    return resolved_base_trajectory_price(config, year)


def resolved_base_trajectory_price(config: ScenarioConfig, year: int) -> float:
    """The carbon price that would resolve with ``carbon_price`` UNSET.

    Precedence stages (2) and (3) of :func:`resolve_carbon_price` — the
    cap-and-trade program adder (measured in a backcast, projected in a
    forecast) and then the :data:`CARBON_PRICE_PATHS` fallback — evaluated
    without stage (1)'s scenario override and without the additive
    ``carbon_price_delta``. This is the *base trajectory* a nonzero
    ``config.carbon_price`` REPLACES, so it is what
    :func:`carbon_price_below_base_warning` compares an override against.

    Pure extraction from :func:`_base_carbon_price` (capx-D34): the resolver's
    returned values are unchanged on every path, for every config.

    Args:
        config: Scenario config supplying ``iso``, ``mode`` and the carbon
            toggles. ``config.carbon_price`` is deliberately NOT read.
        year: Simulation year.

    Returns:
        The base-trajectory carbon price in $/tCO2 (0.0 when neither a program
        adder nor a configured path applies).
    """
    # Program adder (measured backcast / projected forecast). Import here to
    # avoid a circular import at module load (cap_and_trade imports scenarios).
    from market_sim.policy.cap_and_trade import resolve_carbon_program

    resolution = resolve_carbon_program(config, year)
    if resolution is not None and resolution.price_adder:
        return float(resolution.price_adder)

    path = CARBON_PRICE_PATHS.get(config.carbon_price_path)
    if path is None:
        return 0.0

    knots = sorted(path)
    if year <= knots[0]:
        return float(path[knots[0]])
    if year >= knots[-1]:
        return float(path[knots[-1]])

    for lo, hi in zip(knots, knots[1:]):
        if lo <= year <= hi:
            frac = (year - lo) / (hi - lo)
            return float(path[lo] + frac * (path[hi] - path[lo]))
    return float(path[knots[-1]])


#: The verbatim remedy sentence carried by every below-base warning. Split out
#: so the guard, its tests and the D34 finding quote ONE string (capx-D34).
CARBON_PRICE_BELOW_BASE_REMEDY = (
    "a replace below the base trajectory REDUCES the carbon signal "
    "— for an increment use carbon_price_delta"
)


def _format_year_runs(years: list[int]) -> str:
    """Render a sorted year list compactly, collapsing contiguous runs.

    ``[2026, 2027, 2028, 2040]`` renders as ``"2026-2028, 2040"`` so a
    full-horizon hit reads as one span instead of 25 comma-separated years.

    Args:
        years: Sorted, de-duplicated simulation years.

    Returns:
        The compact human-readable rendering ("" for an empty list).
    """
    runs: list[tuple[int, int]] = []
    for year in years:
        if runs and year == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], year)
        else:
            runs.append((year, year))
    return ", ".join(str(lo) if lo == hi else f"{lo}-{hi}" for lo, hi in runs)


def carbon_price_below_base_warning(config: ScenarioConfig) -> str | None:
    """Warn when a forecast ``carbon_price`` override sits BELOW the base.

    Owner ruling Q26 (capx-D34): ``ScenarioConfig.carbon_price`` KEEPS its
    documented replace semantics — precedence (1) of
    :func:`resolve_carbon_price` — and gains this loud validation warning
    instead. The trap it closes is the D23 premise inversion
    (``docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md`` §2): the
    ``carbon25`` arm set ``carbon_price=25`` on NEISO, whose base already
    carries the projected RGGI trajectory ($26.05/t in 2026 escalating at the
    published 7 %/yr CCR rate to $132.16/t by 2050), so a "carbon price
    increase" silently CUT the carbon signal in every horizon year and the
    paired experiment measured the premise of its own pair.

    This function OBSERVES only — it never alters a resolved price, and it
    returns a message rather than raising, because a deliberate below-base
    study stays legal (Q26 verbatim: guard, not semantics change). It just
    cannot be silent any more. The remedy it points at is the additive
    ``carbon_price_delta`` (capx-D26), which shifts the resolved trajectory
    uniformly and so is a strictly positive increment by construction.

    Silent (returns ``None``) when: ``mode != "forecast"`` (backcast is
    untouched — a backcast's measured overlays are a different question);
    ``carbon_price`` is unset/zero (no replacement is happening); or the
    override is at or above the base trajectory in every horizon year.

    Args:
        config: The scenario config being validated. The horizon is
            ``start_year``/``end_year`` when set, else the module defaults
            :data:`START_YEAR`/:data:`END_YEAR` — the same resolution
            ``runner.run_full_horizon`` applies.

    Returns:
        The warning message, or ``None`` when the guard does not fire.
    """
    if config.mode != "forecast":
        return None
    override = float(config.carbon_price or 0.0)
    if override == 0.0:
        return None

    start = config.start_year if config.start_year is not None else START_YEAR
    end = config.end_year if config.end_year is not None else END_YEAR
    span = range(int(start), int(end) + 1)
    if not span:
        return None

    below = [
        (year, base)
        for year in span
        if (base := resolved_base_trajectory_price(config, year)) > override
    ]
    if not below:
        return None

    worst_year, worst_base = max(below, key=lambda row: row[1] - override)
    gap = worst_base - override
    return (
        f"ScenarioConfig.carbon_price={override:g} is BELOW the {config.iso} "
        f"base carbon trajectory in {len(below)} of {len(span)} horizon "
        f"year(s): {_format_year_runs([y for y, _ in below])}. A nonzero "
        "carbon_price REPLACES the resolved trajectory (documented precedence "
        "(1)), it does not add to it. Widest gap in "
        f"{worst_year}: base ${worst_base:,.2f}/tCO2 vs carbon_price "
        f"${override:,.2f}/tCO2 (a ${gap:,.2f}/tCO2 CUT). This is the D23 "
        "premise inversion (the FC-6 P1 'carbon price increase' that cut "
        f"carbon in every horizon year): {CARBON_PRICE_BELOW_BASE_REMEDY}. Set "
        "carbon_price=0.0 and carbon_price_delta to the increment you want "
        "on top of the base trajectory, or keep this replacement if a "
        "below-base carbon signal is the study you intend."
    )
