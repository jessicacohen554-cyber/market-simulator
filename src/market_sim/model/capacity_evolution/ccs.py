"""Gas-CC CCS retrofit screen (W2-C joint retrofit-or-retire).

Step 2 of the one-pass capacity evolution
(:func:`market_sim.model.capacity_evolution.evolve.evolve_fleet`; spec §5.1 /
§5.6), split out of the former ``model/capacity.py`` god-module (W-D4,
2026-07-21; refactor-consolidation plan §5 item 4). Existing gas-CC units
with enough remaining life are screened jointly with retirement — step 2 runs
BEFORE the economic-retirement screen, so a distressed CCGT whose retrofit
continuation clears converts to ``gas_cc_ccs`` instead of exiting. The screen
values the retrofit as the incremental uplift over the best unabated state,
with the certificate and §45Q (two-segment payback,
:func:`_ccs_45q_window_years`) as bid offsets; capped at 3 GW/yr/ISO, gated on
``ccs_retrofit_available_year``, annual re-screen.

The full pre-split surface stays importable from
``market_sim.model.capacity`` (the facade; see the package ``__init__``).
"""

from __future__ import annotations

import logging

import numpy as np

from market_sim.config.constants import (
    HOURS_PER_YEAR,
    NEW_ENTRY_COSTS,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.policy.federal_ces import effective_eac_price_for_unit
from market_sim.policy.ira import ccus_45q_credit_per_mwh

from .new_entry import CumulativeDeployment, wright_cost
from .retirements import _THERMAL_PLANT_LIFE_YEARS

logger = logging.getLogger(__name__)


def _adjust_retrofit_capex(base_capex_kw: float, cumulative_gw: float | None) -> float:
    """Apply Wright's Law to CCS retrofit capex.

    Uses the same learning rate and reference GW as new-build CCS --
    the capture equipment manufacturing base is shared.

    Args:
        base_capex_kw: Base retrofit capex in $/kW (from config).
        cumulative_gw: Current cumulative global CCS deployment in GW.

    Returns:
        Adjusted retrofit capex in $/kW.
    """
    if cumulative_gw is None or cumulative_gw <= 0:
        return base_capex_kw

    ccs_params = NEW_ENTRY_COSTS.get("gas_cc_ccs", {})
    lr = ccs_params.get("learning_rate", 0.10)
    ref_gw = WRIGHT_REFERENCE_GW.get("gas_cc_ccs", 2.0)

    if cumulative_gw <= ref_gw:
        return base_capex_kw

    return wright_cost(base_capex_kw, cumulative_gw, ref_gw, lr)


def _ccs_45q_window_years(config: ScenarioConfig, horizon_years: float) -> float:
    """Return the §45Q credit-earning span within a project horizon, in years.

    ``min(config.ira_45q_credit_window_years, horizon_years)`` — the
    statutory 12-year window from placed-in-service (26 U.S.C.
    §45Q(a)(3)-(4)) clipped to the asset's own horizon (remaining life for
    a retrofit, book life for a new build). ``None`` models the
    owner-requested indefinite legislative extension: the credit runs for
    the full horizon.
    """
    window = config.ira_45q_credit_window_years
    if window is None:
        return float(horizon_years)
    return min(float(window), float(horizon_years))


def _ccs_retrofit_payback_years(
    capex_per_mw: float,
    uplift_window: float,
    uplift_post_window: float,
    window_years: float,
) -> float:
    """Return the retrofit's cumulative-uplift payback in years.

    Two-segment simple payback (plan §11 Q2 — the §45Q stream is truncated
    at its credit window rather than credited undiminished forever): the
    annual incremental uplift is ``uplift_window`` while §45Q pays
    (years ``0..window_years``) and ``uplift_post_window`` afterwards.
    Payback is the point where the cumulative uplift recovers the capex;
    ``inf`` when it never does (in-window uplift non-positive, or the
    credit expires before recovery and the post-window uplift cannot
    finish the job). With no 45Q (expired / zero capture) the two uplifts
    coincide and this degenerates to the classic ``capex / uplift``.
    """
    if uplift_window <= 0.0:
        return float("inf")
    if capex_per_mw <= uplift_window * window_years:
        return capex_per_mw / uplift_window
    if uplift_post_window <= 0.0:
        return float("inf")
    remaining_capex = capex_per_mw - uplift_window * window_years
    return window_years + remaining_capex / uplift_post_window


def _retrofit_price_row(
    prices: np.ndarray, zone_names: list[str] | None, zone: str
) -> np.ndarray | None:
    """Return the hourly price row for ``zone``, or ``None`` if unmappable.

    Single-row price arrays (one-zone systems and trivial fixtures) map
    every unit to row 0; otherwise the unit's zone must resolve through
    ``zone_names`` (the LP's zone ordering, threaded from the prior-year
    results). An unmappable zone skips the candidate loudly-in-debug
    rather than silently pricing it at the wrong bus.
    """
    if prices.shape[0] == 1:
        return prices[0]
    if zone_names and zone in zone_names:
        idx = zone_names.index(zone)
        if idx < prices.shape[0]:
            return prices[idx]
    return None


def apply_ccs_retrofit(
    fleet: list[Generator],
    prices: np.ndarray | None,
    year: int,
    config: ScenarioConfig,
    iso: str,
    gas_price_per_mmbtu: float,
    carbon_price: float,
    zone_names: list[str] | None = None,
    cumulative: CumulativeDeployment | None = None,
) -> tuple[list[Generator], list[dict]]:
    """Screen existing gas CC units for CCS retrofit economics (W2-C).

    A retrofit converts a ``gas_cc`` generator to ``gas_cc_ccs`` in place.
    The unit keeps its zone, capacity and ``unit_id`` but gets:

    * ``heat_rate *= (1 + config.ccs_retrofit_hr_penalty)`` -- the retrofit
      heat rate is *derived* from the source unit's heat rate, never a fixed
      bin, so an efficient host stays efficient after capture,
    * ``vom += config.ccs_retrofit_vom_adder``,
    * ``emission_rate_co2 *= (1 - config.ccs_retrofit_capture_rate)``,
    * ``fuel_type`` changes to ``"gas_cc_ccs"``.

    **Decision basis (plan §11 resolution, owner 2026-07-17).** The screen
    values the retrofit as the INCREMENTAL uplift of the post-retrofit
    continuation over the unit's best unabated continuation, both as
    attainable (pro-forma) inframarginal margins over the prior year's
    hourly price signal — the same construction as the retirement screen
    (rule 1), so anticipated utilization is endogenous instead of the
    former fixed 0.55 screen CF. Per MW-yr::

        mc_unabated = hr·gas + vom + er·carbon
        mc_post     = hr·(1+pen)·gas + vom + vom_adder
                      + er_residual·carbon + captured·transport
        m_unabated  = Σ_t max(0, p[t] − (mc_unabated − attr_unabated)) × avail
        m_window    = Σ_t max(0, p[t] − (mc_post − attr_post − q45)) × avail
        m_post      = Σ_t max(0, p[t] − (mc_post − attr_post)) × avail
        uplift_window = m_window − m_unabated − ΔFOM
        uplift_post   = m_post   − m_unabated − ΔFOM

    where ``attr_*`` is each state's attribute (certificate) price —
    ``max(legacy eac_price_*, federal CES premium × the state's credit
    fraction)`` via :func:`policy.federal_ces.effective_eac_price_for_unit`
    (under ``cesa_ci`` the unabated state's own partial credit is netted
    out by construction; under ``clean_capture`` it is 0) — and ``q45`` is
    the §45Q credit on captured tonnes
    (:func:`policy.ira.ccus_45q_credit_per_mwh`), a SEPARATE statutory
    instrument that stacks on top of the certificate (plan §11 Q1),
    eligibility-gated on ``config.ira_ccus_45q_last_year`` at the retrofit
    year. The certificate and 45Q enter as *bid offsets* inside the
    ``max(0, ·)`` so the screen anticipates the near-baseload utilization
    a 45Q-driven CCS unit actually runs at. ``ΔFOM`` is the going-forward
    fixed-cost delta between the two states (same FOM × multiplier fields
    the retirement screen prices each state at). ``avail`` is the unit's
    flat ``1 − EFORd`` availability — the same derate the LP's
    availability arrays carry. Capacity/AS revenue is state-invariant for
    the same MW and nets out of the incremental comparison.

    **Hurdle.** A unit retrofits when it beats staying unabated
    (``uplift_window > 0``) AND the two-segment windowed payback
    (:func:`_ccs_retrofit_payback_years` — the §45Q stream truncated at
    ``min(config.ira_45q_credit_window_years, remaining life)``, plan §11
    Q2; ``None`` ⇒ indefinite extension) clears the unit's remaining life.
    Retrofit can therefore fire on a healthy unit well before distress
    ("retrofit sooner if it's more profitable than staying unabated") —
    and inside :func:`evolve_fleet` this screen runs BEFORE the economic
    retirement screen, so a distressed CCGT whose retrofit continuation
    clears converts instead of exiting (the joint three-way choice,
    plan §11 final block).

    Units younger than ``config.ccs_retrofit_min_remaining_life`` years
    from end of life are skipped, candidates are ranked shortest-payback
    first (efficient hosts win), and retrofits are applied up to the
    annual throughput cap ``config.ccs_retrofit_max_gw_per_year``;
    cap-displaced candidates stay unabated on the normal loss-year
    counter and are re-screened every year.

    Args:
        fleet: Current generator fleet.
        prices: ``(n_zones, T)`` zonal price signal from the prior year
            (the capacity-screen ``price_signal``). ``None`` — no prior
            dispatch — skips the screen entirely, the same rule as the
            other price-driven capacity screens. Margins computed over a
            shorter-than-8760 series are annualized by ``8760 / T``.
        year: Current simulation year.
        config: Scenario configuration.
        iso: ISO identifier (reserved for future per-ISO calibration).
        gas_price_per_mmbtu: Resolved gas price for this year.
        carbon_price: Resolved carbon price for this year ($/ton CO2).
        zone_names: LP zone ordering aligned with ``prices`` rows, from the
            prior-year results. ``None`` is legal only for single-row price
            arrays (trivial fixtures); multi-zone units that cannot be
            mapped are skipped.
        cumulative: Global cumulative deployment tracker. When supplied,
            the retrofit capex follows the shared CCS Wright's-Law learning
            curve, and the retrofitted GW is added back to the tracker --
            a retrofit grows the capture-equipment experience base.

    Returns:
        Tuple ``(updated_fleet, retrofit_log)`` where ``retrofit_log`` is a
        list of dicts recording each APPLIED retrofit for diagnostics
        (``annual_net_savings_per_mw`` is the in-window incremental
        uplift; the margin decomposition rides along).
    """
    if year < config.ccs_retrofit_available_year:
        return fleet, []
    if prices is None:
        # The economics-based screen values both continuations against the
        # prior year's hourly price signal; with no prior dispatch there is
        # no signal (e.g. the first simulated year).
        return fleet, []

    prices = np.asarray(prices, dtype=float)
    if prices.ndim == 1:
        prices = prices[np.newaxis, :]
    # Trivial fixtures screen over short series; production passes 8760.
    annualize = float(HOURS_PER_YEAR) / prices.shape[1]

    # The capture island is the same equipment whether bolted onto an
    # existing plant or built new, so retrofit capex shares the new-build
    # CCS learning curve.
    adjusted_capex_kw = _adjust_retrofit_capex(
        config.ccs_retrofit_capex_kw,
        cumulative.get("gas_cc_ccs") if cumulative else None,
    )
    retrofit_capex_per_mw = adjusted_capex_kw * 1000.0

    # Going-forward fixed-cost delta between the two states, $/MW-yr — the
    # same FOM × multiplier construction the retirement screen prices each
    # state at, so the uplift stays consistent with the model's own
    # per-state accounting.
    delta_fom_per_mw_yr = (
        config.fixed_om_gas_cc_ccs * config.retirement_fom_multiplier_gas_cc_ccs
        - config.fixed_om_gas_cc * config.retirement_fom_multiplier_gas_cc
    ) * 1000.0

    candidates: list[tuple[float, Generator, dict]] = []
    for gen in fleet:
        if gen.fuel_type != "gas_cc":
            continue
        # Skip units near end of life -- a short remaining life cannot pay
        # back the retrofit capex.
        age = year - gen.online_year
        remaining_life = max(0, _THERMAL_PLANT_LIFE_YEARS - age)
        if remaining_life < config.ccs_retrofit_min_remaining_life:
            continue
        price_row = _retrofit_price_row(prices, zone_names, gen.zone)
        if price_row is None:
            logger.debug(
                "ccs retrofit screen: zone %r of unit %s not mappable onto "
                "the %d-row price signal; skipping candidate",
                gen.zone,
                gen.unit_id,
                prices.shape[0],
            )
            continue

        old_hr = gen.heat_rate
        new_hr = old_hr * (1.0 + config.ccs_retrofit_hr_penalty)
        old_er = gen.emission_rate_co2
        new_er = old_er * (1.0 - config.ccs_retrofit_capture_rate)
        captured = old_er - new_er

        # Full variable cost per state. Post-retrofit pays fuel at the
        # penalized heat rate, the capture VOM adder, carbon on the residual
        # rate only, and transport/storage on every captured tonne (the same
        # per-tonne cost the new-build CCS LCOE carries — a stored tonne
        # earning §45Q pays its way to the reservoir on either path).
        mc_unabated = old_hr * gas_price_per_mmbtu + gen.vom + old_er * carbon_price
        mc_post = (
            new_hr * gas_price_per_mmbtu
            + gen.vom
            + config.ccs_retrofit_vom_adder
            + new_er * carbon_price
            + captured * config.co2_transport_storage_cost
        )

        # Per-state attribute (certificate) prices — max(legacy eac_price_*,
        # premium × state credit fraction); the unabated state's cesa_ci
        # partial credit is what makes the uplift INCREMENTAL, never gross.
        attr_unabated = effective_eac_price_for_unit(config, "gas_cc", old_er, year)
        attr_post = effective_eac_price_for_unit(config, "gas_cc_ccs", new_er, year)
        # §45Q stacks on top of the certificate (separate instrument),
        # eligibility-gated at the retrofit year.
        q45_per_mwh = ccus_45q_credit_per_mwh(captured, year, config)

        avail = max(0.0, 1.0 - gen.eford)
        margin_unabated = (
            float(np.maximum(price_row - (mc_unabated - attr_unabated), 0.0).sum())
            * avail
            * annualize
        )
        margin_window = (
            float(
                np.maximum(price_row - (mc_post - attr_post - q45_per_mwh), 0.0).sum()
            )
            * avail
            * annualize
        )
        margin_post = (
            float(np.maximum(price_row - (mc_post - attr_post), 0.0).sum())
            * avail
            * annualize
        )

        uplift_window = margin_window - margin_unabated - delta_fom_per_mw_yr
        uplift_post = margin_post - margin_unabated - delta_fom_per_mw_yr
        # Beats-staying-unabated gate: a retrofit whose in-window uplift is
        # non-positive is never worth the capex.
        if uplift_window <= 0.0:
            continue

        window_years = _ccs_45q_window_years(config, float(remaining_life))
        payback_years = _ccs_retrofit_payback_years(
            retrofit_capex_per_mw, uplift_window, uplift_post, window_years
        )
        if payback_years >= remaining_life:
            continue

        candidates.append(
            (
                payback_years,
                gen,
                {
                    "unit_id": gen.unit_id,
                    "zone": gen.zone,
                    "old_hr": old_hr,
                    "new_hr": new_hr,
                    "old_emission_rate": old_er,
                    "new_emission_rate": new_er,
                    # In-window incremental uplift — the quantity the payback
                    # recovers capex from (key name kept for the runner's
                    # per-year retrofit logging).
                    "annual_net_savings_per_mw": uplift_window,
                    "payback_years": payback_years,
                    "carbon_price": carbon_price,
                    # Decision decomposition (W2-C): the three attainable
                    # margins and the per-MWh credit stack behind them.
                    "margin_unabated_per_mw_yr": margin_unabated,
                    "margin_window_per_mw_yr": margin_window,
                    "margin_post_window_per_mw_yr": margin_post,
                    "uplift_post_window_per_mw_yr": uplift_post,
                    "q45_usd_per_mwh": q45_per_mwh,
                    "attr_post_usd_per_mwh": attr_post,
                    "attr_unabated_usd_per_mwh": attr_unabated,
                    "window_years": window_years,
                    "delta_fom_per_mw_yr": delta_fom_per_mw_yr,
                    "remaining_life_years": remaining_life,
                },
            )
        )

    # Shortest payback first -- the best-economics (most efficient) hosts win.
    candidates.sort(key=lambda item: item[0])

    cap_mw = config.ccs_retrofit_max_gw_per_year * 1000.0
    retrofitted_mw = 0.0
    retrofit_log: list[dict] = []
    for _payback, gen, log_entry in candidates:
        if retrofitted_mw + gen.pmax_mw > cap_mw:
            continue
        # Convert the generator in place -- a retrofit is irreversible.
        gen.heat_rate = gen.heat_rate * (1.0 + config.ccs_retrofit_hr_penalty)
        gen.vom = gen.vom + config.ccs_retrofit_vom_adder
        gen.emission_rate_co2 = gen.emission_rate_co2 * (
            1.0 - config.ccs_retrofit_capture_rate
        )
        gen.fuel_type = "gas_cc_ccs"
        retrofitted_mw += gen.pmax_mw
        retrofit_log.append(log_entry)

    # A retrofit adds to the global CCS manufacturing experience base just
    # like a new build, so feed the retrofitted GW back into the tracker.
    if retrofitted_mw > 0.0 and cumulative is not None:
        cumulative.add("gas_cc_ccs", retrofitted_mw / 1000.0)

    return fleet, retrofit_log
