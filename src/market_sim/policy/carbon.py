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
    2. Otherwise the **floor** of the two exogenous carbon channels
       (:func:`resolved_base_trajectory_price`; owner ruling S2, card D-1):
       ``max`` of

       * the ISO's cap-and-trade program adder — the **measured** CARB/RGGI
         auction average in backcast years, or the **projected** program price
         in forecast years (the EM-6 seam fix). CAISO/NYISO/NEISO carry a
         program; ERCOT/MISO do not, and a program ISO with
         ``state_carbon_pricing=False`` contributes ``0.0``; and
       * ``config.carbon_price_path`` in :data:`CARBON_PRICE_PATHS`
         (linear-interpolated across knot years, nearest-endpoint clamp outside
         the range; ``"zero"``, the default, is ``0.0`` in every year).

       So a named federal path is a FLOOR under the state program, never a
       replacement for it: on a non-program ISO the path applies alone, and on
       a program ISO the tighter instrument binds. Before S2 an explicit path
       SUPPRESSED the program, which made ``policy_bundle="tight"`` a
       carbon-price cut on every program ISO in every horizon year.

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

    Stages (2) and (3) of :func:`resolve_carbon_price` — the cap-and-trade
    program adder (measured in a backcast, projected in a forecast) and the
    :data:`CARBON_PRICE_PATHS` federal RFF path — **composed as a FLOOR**, and
    evaluated without stage (1)'s scenario override and without the additive
    ``carbon_price_delta``. This is the *base trajectory* a nonzero
    ``config.carbon_price`` REPLACES, so it is what
    :func:`carbon_price_below_base_warning` compares an override against.

    **The floor (owner ruling S2, 2026-09-06, card D-1; desk ledger
    ``docs/handoffs/scenario-desk-ledger-2026-09.md`` §2):**
    ``effective = max(RFF path(year), program trajectory(year))`` on a program
    ISO, and the path alone elsewhere — which the same ``max`` expresses,
    because a non-program ISO's adder is ``0.0`` and no registered path is ever
    negative (:func:`rff_path_price`). This is THE one composition point for the
    two exogenous carbon channels (rule 19 [R-ONE-MECH]); neither
    :func:`~market_sim.policy.cap_and_trade.resolve_carbon_program` nor any
    consumer composes them again.

    *Why a floor.* A unit's marginal compliance cost is set by whichever
    instrument binds. A state allowance price cannot durably sit below a
    federal price every emitter in the state also faces — it would fall to its
    auction reserve and the federal price would bind — and where the state
    escalator is the higher of the two, the federal price is not the binding
    constraint. ``max`` is the exogenous-price approximation of that at zero new
    parameters, and it is **monotone**: a higher federal path can never lower
    anyone's carbon price. It replaced *replace* semantics, under which a named
    federal path suppressed the state program and
    ``policy_bundle="tight"`` was a $16-$102/t CUT on CAISO/NYISO/NEISO in every
    horizon year (``FINDING-scn-ws1a-2026-09-05.md`` §0.1, §6).

    *Measured consequence, ruled with the ruling and not a defect to engineer
    around:* the RFF **mid** path never exceeds a program trajectory in any
    year, so under the floor ``policy_bundle="tight"`` is an exact **no-op** on
    CAISO, NYISO and NEISO — its carbon leg bites only on ERCOT/PJM/MISO.
    Whether ``tight`` should mean something else on a program ISO is open card
    **D-1(b)**; how a federal floor composes with PJM's *partial* RGGI
    footprint is open card **D-1(c)**. Neither is answered here.

    Byte identity at the change: with ``carbon_price_path="zero"`` (every
    committed keeper and forecast bundle) the path operand is ``0.0``, so the
    ``max`` returns the program adder — the value the pre-floor early-return
    returned. Backcast is untouched in every case.

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
    program = float(resolution.price_adder) if resolution is not None else 0.0
    return max(program, rff_path_price(config.carbon_price_path, year))


def rff_path_price(path_name: str, year: int) -> float:
    """The RFF federal carbon path's $/tCO2 at ``year``, alone.

    :data:`CARBON_PRICE_PATHS` linear-interpolated across its knot years with a
    nearest-endpoint clamp outside the range — stage (3) of
    :func:`resolve_carbon_price`'s precedence chain, extracted verbatim so the
    floor in :func:`resolved_base_trajectory_price` and the invariant guard
    :func:`carbon_path_below_program_warning` read ONE implementation of the
    path arithmetic (rule 19 [R-ONE-MECH]).

    Every registered path is non-negative at every knot (``zero`` 0/0/0/0 …
    ``high`` 0/30/70/110), so this never returns a negative price and the
    ``max`` it feeds is never the operand that lowers a resolved trajectory.

    Args:
        path_name: A :data:`CARBON_PRICE_PATHS` key (``"zero"``/``"low"``/
            ``"mid"``/``"high"``). An unregistered name yields ``0.0`` — the
            pre-extraction fallback, kept so an unvalidated
            ``carbon_price_path`` string cannot inject a price.
        year: Simulation year.

    Returns:
        The path's carbon price in $/tCO2 (0.0 for ``"zero"`` and for any
        unregistered name).
    """
    path = CARBON_PRICE_PATHS.get(path_name)
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


def carbon_path_below_program_warning(config: ScenarioConfig) -> str | None:
    """Assert the D-1 FLOOR invariant on the ``carbon_price_path`` branch.

    The D34 guard :func:`carbon_price_below_base_warning` watches precedence
    stage (1), ``carbon_price``, and could never see a cut delivered through
    stage (3), ``carbon_price_path`` — which is exactly how the G-C1 defect went
    unobserved: naming the RFF mid path (what ``policy_bundle="tight"`` does)
    suppressed the state program and cut carbon by $16-$102/tCO2 on
    CAISO/NYISO/NEISO in all 25 horizon years
    (``FINDING-scn-ws1a-2026-09-05.md`` §0.1). This is that guard extended to
    the path branch (SCN-WS1c, plan §7 "WS-1a" item 1).

    **Under the floor it can never fire, and that is the point.**
    :func:`resolved_base_trajectory_price` returns ``max(program, path)``, which
    is ``>= program`` by construction, so this function asserts an invariant
    rather than reporting an expected condition — the form WS-1a §6.4 specified
    ("the guard becomes an assertion of the invariant rather than a warning").
    It is a REGRESSION TRIPWIRE: the day an edit reintroduces a replace path, or
    a consumer recomposes the two channels itself, a named path can once again
    resolve below the program trajectory and this speaks. It is deliberately not
    an assertion statement, so a ``python -O`` run cannot silence it and a
    genuinely-intended below-program study is not made unrunnable — the same
    observe-only posture ruling Q26 fixed for the scalar guard.

    Note what it does NOT warn about: ``tight`` resolving to the program
    trajectory rather than the mid path. That is the ruled S2 outcome (the
    federal price is not the binding instrument there), not a defect, and
    warning on it would put a message on every program-ISO ``tight`` run.

    Silent (returns ``None``) when: ``mode != "forecast"``; the path is
    ``"zero"``/unset (nothing federal is named); or the ISO has no active
    program adder in any horizon year (ERCOT/MISO, or
    ``state_carbon_pricing=False``). The early exits mean a default-configured
    ``ScenarioConfig`` pays one string comparison.

    Args:
        config: The scenario config being validated. Horizon resolution is the
            same as :func:`carbon_price_below_base_warning`'s —
            ``start_year``/``end_year`` when set, else :data:`START_YEAR` /
            :data:`END_YEAR`.

    Returns:
        The invariant-breach message, or ``None`` (the only outcome reachable
        while the floor holds).
    """
    if config.mode != "forecast":
        return None
    path_name = getattr(config, "carbon_price_path", "zero")
    if path_name in ("zero", None):
        return None

    # Import here to avoid a circular import at module load (cap_and_trade
    # imports scenarios); same deferral as resolved_base_trajectory_price.
    from market_sim.policy.cap_and_trade import resolve_carbon_program

    start = config.start_year if config.start_year is not None else START_YEAR
    end = config.end_year if config.end_year is not None else END_YEAR

    breaches = []
    for year in range(int(start), int(end) + 1):
        resolution = resolve_carbon_program(config, year)
        program = float(resolution.price_adder) if resolution is not None else 0.0
        if not program:
            continue
        resolved = resolved_base_trajectory_price(config, year)
        if resolved < program:
            breaches.append((year, resolved, program))
    if not breaches:
        return None

    worst_year, worst_resolved, worst_program = max(
        breaches, key=lambda row: row[2] - row[1]
    )
    gap = worst_program - worst_resolved
    return (
        f"INVARIANT BREACH: ScenarioConfig.carbon_price_path={path_name!r} "
        f"resolves BELOW the {config.iso} carbon-program trajectory in "
        f"{len(breaches)} horizon year(s): "
        f"{_format_year_runs([y for y, _, _ in breaches])}. Owner ruling S2 "
        "(card D-1) makes a named federal RFF path a FLOOR under the state "
        "program — resolved = max(path, program) — so this is unreachable "
        f"while the floor holds. Widest gap in {worst_year}: resolved "
        f"${worst_resolved:,.2f}/tCO2 vs program ${worst_program:,.2f}/tCO2 (a "
        f"${gap:,.2f}/tCO2 CUT). This is the G-C1 defect recurring: a federal "
        "path suppressing the state program, which is what made "
        'policy_bundle="tight" a carbon-price cut on every program ISO. Fix '
        "the composition in policy.carbon.resolved_base_trajectory_price — do "
        "not work around it at a consumer."
    )
