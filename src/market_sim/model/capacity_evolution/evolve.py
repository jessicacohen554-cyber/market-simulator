"""``evolve_fleet`` — the one-pass per-year capacity-evolution step.

Split out of the former ``model/capacity.py`` god-module (W-D4, 2026-07-21;
refactor-consolidation plan §5 item 4). Chains the mechanisms into one year
step, spec §5.1 step ordering 0→7 EXACTLY:

0. Confirmed exits (GATED ``confirmed_exits_enabled``, default on) →
1. Announced retirements → 2. CCS retrofit screen (BEFORE economic
retirements since W2-C: steps 2+3 are the joint retrofit-or-retire choice) →
3. Economic retirements → 4. Known additions → 5. Economic new entry →
6. Reserve-margin adequacy backstop (GATED ``reserve_margin_build_enabled``,
default off) → 7. dispatch with RPS as an LP constraint (shadow price feeds
next year's entry screen; dispatch itself happens back in the runner).

``evolve_fleet`` resolves every step function through the package namespace
at call time (:func:`_pkg_ns`), so the historical
``mock.patch("market_sim.model.capacity.<step>")`` targets and probe-style
``capacity.<step> = wrapped`` instrumentation (run_foresight_ab.py, the
confirmed-retirement probe, the FOM-scarcity grid) keep intercepting the
steps, exactly as the pre-split module-global reads behaved. The full
pre-split surface stays importable from ``market_sim.model.capacity`` (the
facade; see the package ``__init__``).
"""

from __future__ import annotations

import logging

from market_sim.config.constants import NONFOSSIL_ANNOUNCED_HORIZON_YEARS
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.confirmed_retirements import ConfirmedExit
from market_sim.data.fleet import Generator, aggregate_fleet

from .adequacy import (
    accredited_firm_capacity_mw,
    resolve_reserve_margin_build_enabled,
)
from .new_entry import (
    CumulativeDeployment,
    _make_new_generator,
    _merge_renewable_additions,
)
from .retirements import (
    _storage_portfolio_elcc_dilution,
    deliverability_headroom_by_zone,
    resolve_planning_reserve_margin,
)


def _pkg_ns():
    """Return the shared package namespace (:mod:`market_sim.model.capacity_evolution`).

    The ``capacity`` facade aliases itself to this package, so every
    historical ``mock.patch("market_sim.model.capacity.<name>")`` (and
    probe-style ``capacity.<name> = wrapped``) lands on the package
    namespace. ``evolve_fleet`` resolves the six step functions through it
    at call time so those patches keep intercepting the steps, exactly as
    the pre-split module-global reads behaved.
    """
    from market_sim.model import capacity_evolution

    return capacity_evolution


logger = logging.getLogger(__name__)


def _prior_attr(prior_results: object, name: str, default: object = None) -> object:
    """Read ``name`` from ``prior_results``, which may be a dict or object."""
    if prior_results is None:
        return default
    if isinstance(prior_results, dict):
        return prior_results.get(name, default)
    return getattr(prior_results, name, default)


def evolve_fleet(
    fleet: list[Generator],
    prior_results: object,
    year: int,
    config: ScenarioConfig,
    loss_tracker: dict[str, int],
    rps_shadow_price: float = 0.0,
    cumulative: CumulativeDeployment | None = None,
    gas_price_per_mmbtu: float = 0.0,
    carbon_price: float = 0.0,
    events: dict | None = None,
    confirmed_exits: list[ConfirmedExit] | None = None,
    peak_demand_next: float | None = None,
    announced_reversal_plants: frozenset[int] = frozenset(),
    reserve_position: float | None = None,
    entry_rate_caps_mw: dict[str, float] | None = None,
    entry_pipeline: list[dict] | None = None,
) -> tuple[
    list[Generator],
    dict[str, int],
    dict[str, dict[str, float]],
    list[dict],
    list[dict],
]:
    """Advance the fleet by one simulation year.

    The capacity mechanisms are applied in a fixed order:

    0. confirmed exits (exogenous, any fuel, instrument-bound; gated on
       ``config.confirmed_exits_enabled``, default on),
    1. announced retirements (non-fossil within the data horizon only; announced
       fossil dates are a default no-op — the exogenous fossil channel is step 0),
    2. CCS retrofits (convert existing gas CC units to ``gas_cc_ccs``),
    3. economic retirements,
    4. known additions (planned units with ``online_year == year``),
    5. economic new entry (generation).

    Steps 2 and 3 are the JOINT retrofit-or-retire evaluation for
    retrofit-eligible gas-CCs (W2-C, national-ces plan §11 final block),
    still one pass (rule 10 — ordering, not iteration): the retrofit screen
    runs FIRST, so a unit whose retrofit continuation beats staying
    unabated and clears its windowed payback converts BEFORE the
    retirement screen can exit it — a distressed CCGT is offered the
    retrofit instead of the door, and a healthy one may convert early when
    the §45Q + premium economics say so. A unit retires only when both
    continuations fail: not-retrofitted units (uplift or payback failed,
    or displaced by the 3 GW/yr cap) stay on the normal unabated
    loss-year counter — a cap-displaced unit may still exit in a later
    year if unabated keeps failing and the cap keeps binding. Units
    retrofitted this year have their loss counters cleared and are exempt
    from this year's retirement screen (the fresh capex decision IS the
    year's decision); they re-enter it as ``gas_cc_ccs`` next year on
    their own post-retrofit dispatch.

    Retrofits also run before new entry so a retrofitted CC displaces some
    of the need for new-build CCS: the new-entry screen sees the updated
    fleet.

    The reshaped fleet is then re-aggregated into efficiency-bin
    representative units, keeping the next LP solve at ~36 thermal columns.
    When ``config.heat_rate_bin_count`` is set, the re-aggregation uses that
    many equal-width heat-rate bins instead of the predefined vintage bins.

    The renewable portfolio standard is not applied here -- it is enforced
    as an LP constraint in dispatch, and its shadow price
    (``rps_shadow_price``) feeds the economic retirement and new-entry
    screens so clean builds are economics-driven. Storage new entry is
    handled separately in the runner.

    Steps that depend on a price signal -- CCS retrofits, economic
    retirements and economic new entry -- are skipped when
    ``prior_results`` carries no dispatch outcome (e.g. the first
    simulated year).

    Args:
        fleet: The fleet at the start of the year.
        prior_results: Prior-year outcome, a dict or object that may expose
            ``fleet_arrays``, ``dispatch_result``, ``prices``,
            ``peak_demand`` and ``planned_additions``. ``None`` skips all
            price-driven steps.
        year: The simulation year being entered.
        config: Scenario config.
        loss_tracker: Per-unit consecutive-loss counters; not mutated in
            place.
        rps_shadow_price: Prior year's RPS shadow price in $/MWh, passed to
            the economic retirement and new-entry screens as the endogenous
            attribute payment (taken as max with the exogenous EAC).
        cumulative: Global cumulative deployment, passed to the new-entry
            screen so candidate capex follows a Wright's-Law learning curve.
        gas_price_per_mmbtu: Delivered gas price for the year, passed to
            the new-entry screen to cost gas CC variable fuel.
        carbon_price: Carbon price in $/tCO2 for the year, passed to the
            new-entry screen to cost thermal carbon emissions and to the
            CCS retrofit screen. (The retrofit screen's attribute revenue
            is no longer a caller-passed price: it resolves internally via
            ``policy.federal_ces.effective_eac_price_for_unit`` — one
            delivery channel, W2-C.)
        events: Optional dict (see
            :func:`market_sim.results.evolution_ledger.new_events`) populated
            in place with the per-year capacity events — retirements
            (known/economic), reliability-floor-retained units, thermal
            additions (planned/economic/reserve_backstop), CCS retrofits,
            renewable additions, and the fleet-by-fuel totals before/after.
            ``None`` records nothing and leaves the solve path byte-identical.
        peak_demand_next: The ENTERING year's known peak demand in MW
            (deterministic from the demand path — plan §2.3 component 1).
            When supplied it replaces the prior-year ``peak_demand`` in the
            peak-anchored adequacy mechanisms (the retirement reliability
            floor and the reserve-margin backstop), deleting their one-year
            bookkeeping lag. ``None`` keeps the prior-year peak.
        announced_reversal_plants: Plant codes whose announced retirement
            was reversed by a public counter-instrument (registry rows all
            superseded) — step 1 ignores their stale EIA-860 dates
            (:func:`apply_announced_retirements`'s ``reversed_plant_codes``).
            Independent of ``confirmed_exits_enabled``: honoring a documented
            reversal is a data correction, not an exit injection.
        reserve_position: System accredited reserve position (accredited firm ÷
            requirement) for the CR-1 sloped capacity demand curve, computed
            once on the entering fleet by the runner (see
            :func:`capacity_reserve_position`) and threaded verbatim into BOTH
            the retirement and thermal-entry screens so all screens share one
            requirement and one basis (rule 19). ``None`` (default) /
            ``capacity_market_clearing`` off keeps the fixed net-CONE capacity
            payment — byte-identical to the pre-CR-1 path.
        entry_rate_caps_mw: ``{tech: MW}`` current-year growth-ladder caps
            (``entry_rate_limits`` — resolved by the runner from the measured
            EIA-860 throughput seed × ENTRY_GROWTH_LIMIT_MULTIPLE, rising as
            the model builds). Threaded into the new-entry screen; the gas_ct
            entry shares ONE budget with the reserve-margin backstop (rule 19
            — one physical queue). ``None`` (default) is byte-identical.
        entry_pipeline: Cross-year pending-entry queue, MUTATED IN PLACE
            (``entry_commissioning_lag`` — the same seam pattern as
            ``events``): rows whose ``cod_year`` is reached commission here
            (thermal → fleet, VRE → renewable additions) and are removed;
            the new-entry screen appends this year's lagged decisions and
            nets pending MW from the queue caps. ``None`` (default) keeps
            in-year commissioning byte-identically.

    Returns:
        Tuple ``(fleet, loss_tracker, renewable_additions, retrofit_log,
        floor_retention_log)`` after all mechanisms are applied.
        ``renewable_additions`` is a ``{zone: {"wind": mw, "solar": mw}}``
        dict of new wind/solar capacity built this year; the caller folds it
        into the zonal ``wind_cap`` / ``solar_cap`` pools that bound the
        ``W[z,t]`` / ``S[z,t]`` dispatch variables. ``retrofit_log`` is the
        list of CCS retrofit decision dicts recorded this year.
        ``floor_retention_log`` is the retirement reliability floor's
        attribution log — one dict per unit the floor un-retired this year
        (persisted per-year by the runner as ``floor_retentions``).
    """
    loss_tracker = dict(loss_tracker)
    renewable_additions: dict[str, dict[str, float]] = {}
    floor_retention_log: list[dict] = []

    # Ledger bookkeeping: snapshot the entering fleet so each mechanism's
    # additions/retirements can be attributed by a before/after diff. No-op
    # (and zero cost beyond a dict build) when ``events`` is None.
    _rec = events is not None
    if _rec:
        from market_sim.results.evolution_ledger import fleet_totals_by_fuel

        events["fleet_by_fuel_before"] = fleet_totals_by_fuel(fleet)

    fleet_arrays = _prior_attr(prior_results, "fleet_arrays")
    dispatch_result = _prior_attr(prior_results, "dispatch_result")
    prices = _prior_attr(prior_results, "prices")
    # Capacity-screen price signal (plan §2.2-§2.3): the EWMA-blended and/or
    # lookahead-repriced series replaces raw prices in the retirement,
    # CCS-retrofit and new-entry screens. At the runner defaults it IS the
    # same econ_prices array (byte-identical); bare-dict callers without the
    # key fall back to prices.
    price_signal = _prior_attr(prior_results, "price_signal", None)
    if price_signal is not None:
        prices = price_signal
    peak_demand = float(_prior_attr(prior_results, "peak_demand", 0.0) or 0.0)
    # Peak used by the peak-anchored adequacy mechanisms (floor + backstop):
    # the entering year's known peak when the runner supplies it (plan §2.3
    # component 1 — deletes a pure one-year bookkeeping lag), else the
    # prior-year peak (legacy behaviour, e.g. older callers/tests).
    peak_demand_used = (
        float(peak_demand_next)
        if peak_demand_next is not None and peak_demand_next > 0.0
        else peak_demand
    )
    planned = _prior_attr(prior_results, "planned_additions", []) or []
    mc_cost = _prior_attr(prior_results, "mc_cost")
    # AS-eligible (storage) fleet power, the AS-revenue saturation driver.
    storage_power_mw = float(_prior_attr(prior_results, "storage_power_mw", 0.0) or 0.0)
    # Prior-year renewable pools and accredited storage ELCC: the reliability
    # floor (step 2) and the adequacy backstop (step 6) test the same
    # accredited-firm-capacity ledger (plan §3.2), so both read these.
    wind_pool_mw = float(_prior_attr(prior_results, "wind_cap_mw", 0.0) or 0.0)
    solar_pool_mw = float(_prior_attr(prior_results, "solar_cap_mw", 0.0) or 0.0)
    # Portfolio ELCC dilution (accreditation audit §3 follow-up): the
    # pre-accredited storage_firm_mw the runner computed carries no
    # penetration term, so it is diluted here — the point evolve_fleet
    # consumes it — rather than in runner.py, whose own persisted ledger
    # value stays undiluted (a parallel lane's file; see
    # _storage_portfolio_elcc_dilution docstring).
    storage_firm_mw = float(_prior_attr(prior_results, "storage_firm_mw", 0.0) or 0.0)
    storage_firm_mw *= _storage_portfolio_elcc_dilution(storage_power_mw, config.iso)
    # Per-fuel thermal AS credit DERIVED from the prior-year co-opt reserve duals,
    # populated by the runner only under ercot_thermal_as_endogenous. When present
    # the retirement/new-entry screens use it in place of the exogenous flat AS
    # rate so exactly one mechanism prices thermal AS (rule 19); None keeps the
    # exogenous rate (byte-identical default).
    thermal_as_revenue_per_mw_yr = (
        _prior_attr(prior_results, "thermal_as_revenue_per_mw_yr", None)
        if getattr(config, "ercot_thermal_as_endogenous", False)
        else None
    )
    # Hourly reserve-price signal (plan §5 step 2, screen_reserve_value_enabled):
    # the retirement and thermal new-entry screens value each reserve-eligible
    # unit's per-hour best use max(energy margin, reserve price). When present
    # it is the sole thermal AS pricing (rule 19) — see the screens' docstrings.
    reserve_price_signal = None
    reserve_price_signal_slow = None
    if getattr(config, "screen_reserve_value_enabled", True):
        reserve_price_signal = _prior_attr(prior_results, "reserve_price_signal", None)
        reserve_price_signal_slow = _prior_attr(
            prior_results, "reserve_price_signal_slow", None
        )
    # Zonal hourly CF profiles + zone ordering for the shape-aware VRE
    # new-entry revenue (plan §6 CX-6c); None falls back to the scalar screen.
    screen_zone_names = _prior_attr(prior_results, "zone_names", None)
    screen_wind_cf = _prior_attr(prior_results, "wind_cf", None)
    screen_solar_cf = _prior_attr(prior_results, "solar_cf", None)

    # Snapshot the entering fleet so the events recorder can attribute every
    # unit removed by the confirmed (step 0) and announced (step 1) channels.
    _pre_known = {g.unit_id: g for g in fleet} if _rec else None

    # 0. Confirmed exits (exogenous, instrument-bound, any fuel). GATED on
    #    confirmed_exits_enabled (default on, flipped 2026-07-05): when off, no-op
    #    and the announced/economic channels are byte-identical to before this
    #    channel existed. Runs first so the post-exit fleet is what the floor and the
    #    new-entry screen see (scarcity from a confirmed exit feeds next year's
    #    entry signal). Bypasses the reliability floor by construction.
    #    NOTE: matching is by plant_code. A unit that survives the end-of-year
    #    re-aggregation with its plant identity intact — a unit-grain unit (raw
    #    EIA-860 unit that passes through, e.g. an oil unit carrying an announced
    #    date) or a first-year exit in build_base_fleet — is matched in its exit
    #    year. Plant-binned coal/gas tranches (is_campd_bin) also keep their
    #    plant_code: aggregate_fleet passes them through un-aggregated (G-28 fix),
    #    so a confirmed exit effective any number of years into a CAMPD forecast
    #    is matched at the same per-plant grain the base year solves. (Before the
    #    fix these tranches were merged into vintage efficiency bins after the
    #    base year, dropping plant_code, and an exit 2+ years out went unmatched.)
    #    ``apply_backlog`` defaults to False here (unlike build_base_fleet's
    #    True): only the row newly effective in THIS year is selected, so a
    #    row already applied in the pre-start backlog or a prior year's
    #    evolve_fleet call is never re-selected against an already-shrunk
    #    fleet (the double-derate bug fixed 2026-07-05 — a confirmed exit is a
    #    once-at-its-date event, not a recurring per-year filter).
    confirmed_exits = confirmed_exits or []
    confirmed_channel_on = getattr(config, "confirmed_exits_enabled", False) and bool(
        confirmed_exits
    )
    if confirmed_channel_on:
        fleet = _pkg_ns().apply_confirmed_exits(fleet, year, confirmed_exits)

    # 1. Announced (EIA-860 date) retirements. Fossil units are a default no-op
    #    (their phaseout is economic, step 2; the exogenous fossil channel is
    #    step 0). Non-fossil announced dates are honored within the EIA-860 data
    #    horizon; beyond it, only when the unit is in the confirmed registry (the
    #    horizon gate activates with the confirmed channel — off = honor all
    #    non-fossil dates, as before). config.forecast_fossil_retirement_economic
    #    toggles the fossil exemption.
    horizon_years = NONFOSSIL_ANNOUNCED_HORIZON_YEARS if confirmed_channel_on else None
    confirmed_plant_codes = (
        frozenset(e.plant_id for e in confirmed_exits)
        if confirmed_channel_on
        else frozenset()
    )
    fleet = _pkg_ns().apply_announced_retirements(
        fleet,
        year,
        fossil_economic=getattr(config, "forecast_fossil_retirement_economic", True),
        horizon_years=horizon_years,
        confirmed_plant_codes=confirmed_plant_codes,
        reversed_plant_codes=announced_reversal_plants,
    )
    if _rec:
        _survived = {g.unit_id for g in fleet}
        events["retirements"].extend(
            {
                "unit_id": g.unit_id,
                "fuel": g.fuel_type,
                "mw": float(g.pmax_mw),
                "reason": "known",
            }
            for uid, g in _pre_known.items()
            if uid not in _survived
        )

    # Locational deliverability headroom per zone (empty no-op unless
    # capacity_deliverability_limits is on and the ISO has clean data). Prior-
    # year renewable pools / storage ELCC are ISO totals; distribute them across
    # zones by load_share so the firm-capacity sum is zonal. Computed once on the
    # entering fleet and shared by the retirement and new-entry screens.
    deliverability_headroom: dict[str, float] = {}
    if config.capacity_deliverability_limits:
        iso_config = get_iso_config(config.iso)
        wind_total = float(_prior_attr(prior_results, "wind_cap_mw", 0.0) or 0.0)
        solar_total = float(_prior_attr(prior_results, "solar_cap_mw", 0.0) or 0.0)
        storage_total = float(_prior_attr(prior_results, "storage_firm_mw", 0.0) or 0.0)
        wind_by_zone = {z.name: wind_total * z.load_share for z in iso_config.zones}
        solar_by_zone = {z.name: solar_total * z.load_share for z in iso_config.zones}
        storage_by_zone = {
            z.name: storage_total * z.load_share for z in iso_config.zones
        }
        deliverability_headroom = deliverability_headroom_by_zone(
            config.iso,
            year,
            fleet,
            config,
            wind_pool_by_zone=wind_by_zone,
            solar_pool_by_zone=solar_by_zone,
            storage_firm_by_zone=storage_by_zone,
        )

    # 2. CCS retrofits: convert existing gas CC units to gas_cc_ccs. Runs
    # BEFORE the economic retirement screen — the joint retrofit-or-retire
    # choice (W2-C, plan §11 final block): a gas-CC whose retrofit
    # continuation beats staying unabated and clears its windowed payback
    # converts here, so the retirement screen never sees it as a distressed
    # unabated unit; everything not converted (uplift/payback failed, or
    # displaced by the 3 GW/yr cap) falls through to step 3 on the normal
    # loss-year counter. Also runs before new entry so retrofits displace
    # some new-build CCS demand. Same skip rule as the other price-driven
    # screens: no prior-year price signal, no screen.
    _pre_ccs = {g.unit_id: g.fuel_type for g in fleet} if _rec else None
    fleet, retrofit_log = _pkg_ns().apply_ccs_retrofit(
        fleet,
        prices,
        year,
        config,
        config.iso,
        gas_price_per_mmbtu=gas_price_per_mmbtu,
        carbon_price=carbon_price,
        zone_names=screen_zone_names,
        cumulative=cumulative,
    )
    # A retrofit is this year's capital decision for the unit: clear its
    # unabated loss history (it re-enters the retirement screen as
    # gas_cc_ccs next year on its own post-retrofit dispatch) and exempt it
    # from this year's screen below.
    _retrofitted_ids = frozenset(entry["unit_id"] for entry in retrofit_log)
    for _uid in _retrofitted_ids:
        loss_tracker.pop(_uid, None)
    if _rec:
        # A CCS retrofit is a fuel shift (gas_cc → gas_cc_ccs) on the same
        # unit_id, not a new column. Detect by comparing fuel_type before/after.
        _post_ccs = {g.unit_id: g for g in fleet}
        events["ccs_retrofits"].extend(
            {
                "unit_id": uid,
                "mw": float(_post_ccs[uid].pmax_mw),
                "from_fuel": _pre_ccs[uid],
                "to_fuel": _post_ccs[uid].fuel_type,
            }
            for uid in _pre_ccs
            if uid in _post_ccs and _post_ccs[uid].fuel_type != _pre_ccs[uid]
        )

    # 3. Economic retirements (needs the prior-year dispatch). Units
    # retrofitted in step 2 are exempt this year (see above).
    if fleet_arrays is not None and dispatch_result is not None and prices is not None:
        _econ_sink: dict = {} if _rec else None
        fleet, loss_tracker, floor_retention_log = _pkg_ns().apply_economic_retirements(
            fleet,
            fleet_arrays,
            dispatch_result,
            prices,
            config,
            loss_tracker,
            peak_demand_used,
            rps_shadow_price=rps_shadow_price,
            mc=mc_cost,
            storage_power_mw=storage_power_mw,
            deliverability_headroom=deliverability_headroom,
            thermal_as_revenue_per_mw_yr=thermal_as_revenue_per_mw_yr,
            wind_pool_mw=wind_pool_mw,
            solar_pool_mw=solar_pool_mw,
            storage_firm_mw=storage_firm_mw,
            year=year,
            event_sink=_econ_sink,
            reserve_price_signal=reserve_price_signal,
            reserve_price_signal_slow=reserve_price_signal_slow,
            reserve_position=reserve_position,
            exempt_unit_ids=_retrofitted_ids,
        )
        if _rec:
            events["retirements"].extend(
                {**e, "reason": "economic"} for e in _econ_sink.get("retired", [])
            )
            events["floor_retained"].extend(_econ_sink.get("floor_retained", []))
            # R-NEW ledger attribution (FF-1A component 6): the pipeline's
            # decided/re_confirmed/reversed/entry_capped/executed rows.
            # Empty under retirement_rule="legacy".
            events.setdefault("pipeline_events", []).extend(
                _econ_sink.get("pipeline_events", [])
            )
        if floor_retention_log:
            logger.info(
                "year %d: reliability floor retained %d unit(s), %.0f MW "
                "(%.0f MW UCAP) against the PRM requirement",
                year,
                len(floor_retention_log),
                sum(r["pmax_mw"] for r in floor_retention_log),
                sum(r["ucap_mw"] for r in floor_retention_log),
            )

    # 4. Known additions: planned units coming online this year.
    _planned_now = [g for g in planned if g.online_year == year]
    fleet = fleet + _planned_now
    if _rec:
        events["thermal_additions"].extend(
            {
                "unit_id": g.unit_id,
                "fuel": g.fuel_type,
                "mw": float(g.pmax_mw),
                "zone": g.zone,
                "source": "planned",
                # Planned units come from the EIA-860 pipeline; their unit_id
                # encodes the source plant (``planned_<plant>_<gen>``), so it is
                # the traceable id when the plant_id field is unset.
                "eia860_id": getattr(g, "plant_id", None) or g.unit_id,
            }
            for g in _planned_now
        )

    # 4.5 FF-2A pipeline commissioning (entry_commissioning_lag): pending
    # economic-entry decisions whose COD year is reached materialize now —
    # thermal rows enter the fleet (picked up by the step-5 events diff as
    # source "economic"), VRE rows fold into the zonal pools. Rows are
    # removed from the pipeline (mutated in place, so they stop occupying
    # the queue the step-5 screen nets against); deterministic, so it runs
    # even in a year the price-driven screen is skipped.
    _commissioned_rows: list[dict] = []
    if entry_pipeline:
        for r in [r for r in entry_pipeline if int(r["cod_year"]) <= year]:
            entry_pipeline.remove(r)
            if r.get("kind") == "vre":
                zone_acc = renewable_additions.setdefault(r["zone"], {})
                zone_acc[r["tech"]] = zone_acc.get(r["tech"], 0.0) + float(r["mw"])
            else:
                g = _make_new_generator(
                    r["tech"],
                    float(r["mw"]),
                    r["zone"],
                    int(r["cod_year"]),
                    int(r["seq"]),
                    config,
                    config.iso,
                )
                # Distinct id per decision cohort: two cohorts can share a
                # (tech, cod_year, seq) triple once the lag separates them.
                g.unit_id = (
                    f"{r['tech']}_new_{int(r['decision_year'])}"
                    f"c{int(r['cod_year'])}_{int(r['seq'])}"
                )
                g.name = g.unit_id
                fleet = fleet + [g]
            _commissioned_rows.append(dict(r))

    # 5. Economic new entry (needs a price signal). Clean technologies see
    # the prior year's RPS shadow price as additional expected revenue.
    # Decision-grain MW by tech (screen + backstop) feed the runner's
    # growth-ladder prior-max update; tracked unconditionally (cheap).
    _decided_mw_by_tech: dict[str, float] = {}
    _pre_entry_ids_all = {g.unit_id for g in fleet}
    _pre_entry_ids = _pre_entry_ids_all if _rec else None
    # RC-0C entry-screen diagnostic sink (GATED entry_screen_diagnostics,
    # default off): a per-candidate decomposition ledger with no decision
    # effect, persisted into the year's evolution ledger by the runner.
    _screen_ledger: list[dict] | None = (
        [] if getattr(config, "entry_screen_diagnostics", False) else None
    )
    if prices is not None:
        fleet, entry_additions = _pkg_ns().apply_economic_new_entry(
            fleet,
            prices,
            year,
            config,
            config.iso,
            rps_shadow_price=rps_shadow_price,
            cumulative=cumulative,
            gas_price_per_mmbtu=gas_price_per_mmbtu,
            carbon_price=carbon_price,
            storage_power_mw=storage_power_mw,
            deliverability_headroom=deliverability_headroom,
            thermal_as_revenue_per_mw_yr=thermal_as_revenue_per_mw_yr,
            reserve_price_signal=reserve_price_signal,
            reserve_price_signal_slow=reserve_price_signal_slow,
            zone_names=screen_zone_names,
            wind_cf=screen_wind_cf,
            solar_cf=screen_solar_cf,
            reserve_position=reserve_position,
            screen_ledger=_screen_ledger,
            wind_pool_mw=wind_pool_mw,
            solar_pool_mw=solar_pool_mw,
            peak_demand_mw=peak_demand_used,
            entry_rate_caps_mw=entry_rate_caps_mw,
            entry_pipeline=entry_pipeline,
        )
        _merge_renewable_additions(renewable_additions, entry_additions)
        # Decision-grain accounting: in-year builds (fleet diff + VRE screen
        # additions) plus this year's lagged pipeline appends. Commissioned
        # rows from step 4.5 were counted at their decision year, and the
        # step-4.5 fleet units predate _pre_entry_ids_all, so nothing double
        # counts.
        for g in fleet:
            if g.unit_id not in _pre_entry_ids_all:
                _decided_mw_by_tech[g.fuel_type] = _decided_mw_by_tech.get(
                    g.fuel_type, 0.0
                ) + float(g.pmax_mw)
        for _zone_adds in entry_additions.values():
            for _t, _mw in _zone_adds.items():
                _decided_mw_by_tech[_t] = _decided_mw_by_tech.get(_t, 0.0) + float(_mw)
        if entry_pipeline is not None:
            for r in entry_pipeline:
                if int(r.get("decision_year", -1)) == year:
                    _decided_mw_by_tech[r["tech"]] = _decided_mw_by_tech.get(
                        r["tech"], 0.0
                    ) + float(r["mw"])
    if _rec and _screen_ledger is not None:
        events["entry_screen_diagnostics"] = _screen_ledger
    if _rec:
        _new_ids = {g.unit_id for g in fleet} - _pre_entry_ids
        events["thermal_additions"].extend(
            {
                "unit_id": g.unit_id,
                "fuel": g.fuel_type,
                "mw": float(g.pmax_mw),
                "zone": g.zone,
                "source": "economic",
                "eia860_id": None,
            }
            for g in fleet
            if g.unit_id in _new_ids
        )

    # 6. Reserve-margin adequacy backstop: force-build firm capacity if the
    # economic screen left the system below its planning reserve margin
    # against the entering year's known peak (prior-year peak when the runner
    # did not supply it). Firm capacity nets the thermal fleet (UCAP) and the
    # prior-year renewable pools / storage (threaded via prior_results).
    # No-op unless the backstop resolves on (G-41 market-design resolution:
    # capacity-market ISOs default-on, energy-only ERCOT off, explicit override
    # wins — resolve_reserve_margin_build_enabled).
    if (
        resolve_reserve_margin_build_enabled(config, config.iso)
        and peak_demand_used > 0.0
    ):
        firm_mw = accredited_firm_capacity_mw(
            fleet,
            wind_pool_mw,
            solar_pool_mw,
            storage_firm_mw,
            iso=config.iso,
            peak_demand_mw=peak_demand_used,
            elcc_curves_enabled=config.renewable_elcc_curves,
        )
        _pre_backstop_ids = {g.unit_id for g in fleet} if _rec else None
        # FF-2A item 2 (BLK-10): the backstop's gas_ct build draws the SAME
        # growth-ladder budget as this year's economic gas_ct decisions —
        # one physical queue (rule 19). None (gate off) is byte-identical.
        _gas_ct_rate_budget: float | None = None
        if entry_rate_caps_mw is not None and "gas_ct" in entry_rate_caps_mw:
            _gas_ct_rate_budget = max(
                0.0,
                float(entry_rate_caps_mw["gas_ct"])
                - _decided_mw_by_tech.get("gas_ct", 0.0),
            )
        fleet, adequacy_mw = _pkg_ns().apply_reserve_margin_build(
            fleet,
            firm_mw,
            peak_demand_used,
            year,
            config,
            config.iso,
            rate_limit_mw=_gas_ct_rate_budget,
        )
        if adequacy_mw > 0.0:
            _decided_mw_by_tech["gas_ct"] = (
                _decided_mw_by_tech.get("gas_ct", 0.0) + adequacy_mw
            )
        if _rec and adequacy_mw > 0.0:
            events["thermal_additions"].extend(
                {
                    "unit_id": g.unit_id,
                    "fuel": g.fuel_type,
                    "mw": float(g.pmax_mw),
                    "zone": g.zone,
                    "source": "reserve_backstop",
                    "eia860_id": None,
                }
                for g in fleet
                if g.unit_id not in _pre_backstop_ids
            )
        if adequacy_mw > 0.0:
            # Same per-ISO resolution as apply_reserve_margin_build so the
            # logged margin reflects the value actually used.
            resolved_margin = resolve_planning_reserve_margin(config, config.iso)
            logger.info(
                "year %d: reserve-margin backstop built %.0f MW gas_ct "
                "(firm %.0f MW vs peak %.0f MW x %.3f margin)",
                year,
                adequacy_mw,
                firm_mw,
                peak_demand_used,
                1.0 + resolved_margin,
            )

    if _rec:
        # Fleet totals BEFORE aggregation: aggregate_fleet rebins into
        # representative units but conserves MW per fuel, so the capacity
        # accounting is identical either way; record the physical fleet.
        events["fleet_by_fuel_after"] = fleet_totals_by_fuel(fleet)
        # Renewable pool builds (flattened from the {zone: {tech: mw}} dict).
        events["renewable_additions"] = [
            {"zone": zone, "tech": tech, "mw": float(mw)}
            for zone, techs in renewable_additions.items()
            for tech, mw in techs.items()
            if mw
        ]
        # FF-2A entry-stack attribution: decision-grain MW by tech (feeds the
        # runner's growth-ladder prior-max update), and — when the COD lag is
        # armed — the pipeline rows decided and commissioned this year, each
        # carrying BOTH decision_year and cod_year (item 3's ledger contract).
        events["entry_decided_mw_by_tech"] = dict(_decided_mw_by_tech)
        if entry_pipeline is not None:
            events["entry_pipeline"] = [
                {**r, "event": "decided"}
                for r in entry_pipeline
                if int(r.get("decision_year", -1)) == year
            ] + [{**r, "event": "commissioned"} for r in _commissioned_rows]

    # Retirements, retrofits and new entry have reshaped the fleet;
    # re-collapse it into efficiency-bin representatives so the next LP solve
    # gets ~36 thermal columns rather than one per physical unit.
    fleet = aggregate_fleet(fleet, n_bins=config.heat_rate_bin_count)

    return fleet, loss_tracker, renewable_additions, retrofit_log, floor_retention_log
