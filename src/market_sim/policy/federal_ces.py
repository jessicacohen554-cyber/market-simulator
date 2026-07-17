"""National Clean Energy Standard (CES) federal EAC-premium resolver.

Models a federal clean-energy standard in which every credited MWh earns
one Energy Attribute Certificate (EAC) at an exogenous scenario-set
premium (an ensemble of premium levels), rather than clearing a national
certificate market endogenously. The premium joins the legacy per-tech
``eac_price_*`` scalars and the endogenous RPS shadow price via ``max()``
— one certificate per MWh, sold once (house no-stack doctrine,
:mod:`market_sim.policy.eac`).

Two owner-specified crediting modes (``ScenarioConfig.federal_ces_crediting``,
plan §1 of ``docs/handoffs/national-ces-eac-premium-plan-2026-07.md``):

* ``"clean_capture"`` (DEFAULT) — eligible zero-carbon fuels credit at
  1.0; abated gas (``gas_cc_ccs``, retrofit or new-build) credits at the
  policy-assumed capture fraction ``federal_ces_ccs_capture_fraction``;
  unabated fossil credits 0. Simple, certificate-like, no per-unit CI
  dependence.
* ``"cesa_ci"`` (VARIANT) — CESA-style fractional crediting
  ``clip(1 − CI/benchmark, 0, 1)`` (benchmark
  ``federal_ces_ci_benchmark_t_per_mwh``, CESA S.1359 116th Cong. /
  Bingaman S.2146 112th Cong.), extended to UNABATED gas CC whose CI is
  at or under ``federal_ces_unabated_ci_threshold_t_per_mwh`` — an
  eligibility cutoff only: the credit fraction is always computed
  against the benchmark, never against the threshold. Per-unit CI is the
  fleet's own CO2 rate in tCO2/MWh at the LP boundary
  (``FleetArrays.emission_rate``).

All premiums are real 2026$/MWh (model-wide convention,
``constants.REAL_DOLLAR_BASE_YEAR``); a constant real premium tracks
inflation in nominal terms automatically. Consumers (wired in W2-A, plan
§5.3): the dispatch cost vector (``policy.eac.apply_eac_to_mc`` /
``compute_eac_dispatch_credits``), the economic-retirement screen and
both new-entry screens (``model.capacity``), and the state-RPS-row
suppression counterfactual (``runner``). The CCS-retrofit screen is
deliberately NOT a consumer yet — its whole economics are redesigned in
W2-C (plan §11) and it keeps its legacy ``eac_price_gas_cc_ccs`` input
until then. With ``federal_ces_enabled=False`` every resolver below
returns zeros or the legacy ``eac_price_*`` values unchanged, keeping
dispatch bytes and cache keys identical to the pre-CES model.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.constants import CO2_RATES, REAL_DOLLAR_BASE_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.policy.eac import _EAC_PRICE_FIELDS, get_eac_price_for_new_entry

# Candidate-technology name -> fleet fuel type. New-entry candidate techs
# whose cost tier differs from their dispatch fuel (capacity.py collapses
# nuclear_smr/nuclear_large to fuel_type "nuclear") credit as that fuel;
# every other tech name is already a fleet fuel type.
_TECH_FUEL_ALIASES: dict[str, str] = {
    "nuclear_smr": "nuclear",
    "nuclear_large": "nuclear",
}


def premium_for_year(config: ScenarioConfig, year: int | None) -> float:
    """Return the federal CES premium in real 2026$/MWh for a model year.

    Resolution order (plan §5.2 / D3):

    * ``0.0`` unless ``config.federal_ces_enabled``.
    * If ``config.federal_ces_premium_by_year`` is set (non-empty), the
      sparse ``{year: value}`` knots govern: linear interpolation between
      knot years, edge-held outside them (the ``STATE_RPS_FLOORS``
      trajectory pattern, :func:`market_sim.policy.rps.get_rps_target`).
      Keys are coerced ``str -> int`` so a YAML round-trip (which
      stringifies mapping keys) resolves identically.
    * Otherwise the geometric path
      ``base × (1 + escalation_real)^(year − 2026)`` anchored at
      ``constants.REAL_DOLLAR_BASE_YEAR`` (2026). The owner-confirmed
      default escalation is 0 — a flat real premium (CPI-tracking in
      nominal terms).

    Args:
        config: Scenario config supplying the ``federal_ces_*`` fields.
        year: Simulation year the premium applies to. ``None`` is legal
            only while the CES is disabled (legacy pre-W2-A callers that
            never threaded a year): an enabled CES with no year raises
            rather than silently mispricing the premium — a channel that
            silently fails to deliver is the ERCOT-65 defect class.

    Returns:
        The premium in real 2026$/MWh; ``0.0`` when the CES is disabled.

    Raises:
        ValueError: If the CES is enabled and ``year`` is ``None``.
    """
    if not config.federal_ces_enabled:
        return 0.0
    if year is None:
        raise ValueError(
            "federal_ces_enabled requires a simulation year to resolve the "
            "premium path; this call site predates the W2-A year threading "
            "(plan §5.3) — pass the solve year through"
        )

    knots_raw = config.federal_ces_premium_by_year
    if knots_raw:
        # YAML round-trips stringify int keys; coerce back so on-disk and
        # in-memory configs resolve identically (plan §5.1).
        knots = {int(k): float(v) for k, v in knots_raw.items()}
        years = sorted(knots)
        if year <= years[0]:
            return knots[years[0]]
        if year >= years[-1]:
            return knots[years[-1]]
        for lo, hi in zip(years, years[1:]):
            if lo <= year <= hi:
                frac = (year - lo) / (hi - lo)
                return knots[lo] + frac * (knots[hi] - knots[lo])
        return knots[years[-1]]

    n = year - REAL_DOLLAR_BASE_YEAR
    return config.federal_ces_premium_usd_per_mwh * (
        (1.0 + config.federal_ces_premium_escalation_real) ** n
    )


def _eligible_fuel_codes(config: ScenarioConfig) -> list[int]:
    """Map ``federal_ces_eligible_fuels`` names to fleet fuel-type codes.

    The eligibility list carries fleet FUEL TYPES (``FUEL_TYPE_MAP``
    names) only — candidate-tech aliases resolve via
    :func:`tech_credit_fraction`, and storage is gated by its own
    ``federal_ces_storage_eligible`` boolean. An unknown name is a config
    error (most likely a typo silently zero-crediting a fuel), so it
    raises rather than no-ops.

    Raises:
        ValueError: If a listed fuel is not a ``FUEL_TYPE_MAP`` name.
    """
    codes: list[int] = []
    for fuel in config.federal_ces_eligible_fuels:
        code = FUEL_TYPE_MAP.get(fuel)
        if code is None:
            raise ValueError(
                "federal_ces_eligible_fuels entries must be fleet fuel "
                f"types ({sorted(FUEL_TYPE_MAP)}); got {fuel!r}"
            )
        codes.append(code)
    return codes


def _credit_fractions_from_codes(
    config: ScenarioConfig, fuel_idx: np.ndarray, emission_rate: np.ndarray
) -> np.ndarray:
    """Vectorized crediting core, shared and UNGATED by the master switch.

    Applies the config's crediting mode to per-generator fuel codes and
    CO2 rates without consulting ``federal_ces_enabled`` — the gate
    belongs to the callers: :func:`unit_credit_fractions` (payment path)
    zeroes everything when the CES is off, while
    :func:`reporting_credit_fractions` (diagnostics) deliberately does
    not. Semantics per mode are documented on
    :func:`unit_credit_fractions`.
    """
    eligible = np.isin(fuel_idx, _eligible_fuel_codes(config))

    if config.federal_ces_crediting == "clean_capture":
        fractions = np.zeros(fuel_idx.shape[0], dtype=float)
        fractions[eligible] = 1.0
        ccs_mask = eligible & (fuel_idx == FUEL_TYPE_MAP["gas_cc_ccs"])
        fractions[ccs_mask] = config.federal_ces_ccs_capture_fraction
        return fractions

    # cesa_ci (the only other mode; __post_init__ validates the name).
    emission_rate = np.asarray(emission_rate, dtype=float)
    cesa = np.clip(
        1.0 - emission_rate / config.federal_ces_ci_benchmark_t_per_mwh, 0.0, 1.0
    )
    unabated_cc_credited = (fuel_idx == FUEL_TYPE_MAP["gas_cc"]) & (
        emission_rate <= config.federal_ces_unabated_ci_threshold_t_per_mwh
    )
    return np.where(eligible | unabated_cc_credited, cesa, 0.0)


def unit_credit_fractions(config: ScenarioConfig, fleet: FleetArrays) -> np.ndarray:
    """Return the per-generator CES credit fraction, shape ``(n_gen,)``.

    Vectorized over the fleet arrays (rule 2 — no unit loops):

    * Disabled CES: all zeros.
    * ``clean_capture``: generators whose fuel type is in
      ``federal_ces_eligible_fuels`` credit at 1.0, except ``gas_cc_ccs``
      which credits at the policy-assumed
      ``federal_ces_ccs_capture_fraction``; every non-eligible fuel
      (unabated fossil, biomass, imports) credits 0.
    * ``cesa_ci``: eligible fuels credit at
      ``clip(1 − emission_rate/benchmark, 0, 1)`` — zero-carbon fuels
      land at 1.0 and abated gas earns the formula on its residual CI —
      PLUS unabated ``gas_cc`` units whose emission rate is at or under
      ``federal_ces_unabated_ci_threshold_t_per_mwh`` earn the same
      benchmark formula (the threshold is an eligibility cutoff, never
      the denominator). Everything else credits 0.
      ``fleet.emission_rate`` is tCO2/MWh at the LP boundary, the same
      array the dispatch marginal-cost build prices carbon with.

    Args:
        config: Scenario config supplying the ``federal_ces_*`` fields.
        fleet: Vectorized fleet arrays supplying ``fuel_type_idx`` and
            ``emission_rate``.

    Returns:
        Float array of credit fractions in ``[0, 1]``, shape ``(n_gen,)``.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    if not config.federal_ces_enabled:
        return np.zeros(fuel_idx.shape[0], dtype=float)
    return _credit_fractions_from_codes(
        config, fuel_idx, np.asarray(fleet.emission_rate)
    )


# Lazily-built default config for reporting-side crediting when a caller
# has no ScenarioConfig at hand (see reporting_credit_fractions).
_DEFAULT_REPORTING_CONFIG: ScenarioConfig | None = None


def reporting_credit_fractions(
    config: ScenarioConfig | None,
    fuel_types: "list[str] | tuple[str, ...]",
    emission_rates,
) -> np.ndarray:
    """Return REPORTING-side credit fractions from fuel names + CO2 rates.

    The diagnostics companion of :func:`unit_credit_fractions`, for the
    ``clean_share`` / premium-capture metrics (plan §5.4). Two deliberate
    differences from the payment-path resolver:

    * **Not gated by ``federal_ces_enabled``.** A clean-share metric must
      be comparable across a premium ladder that includes the CES-off BAU
      case — the gated resolver would report BAU as 0% clean by
      construction, breaking the clean-share-vs-premium curve. This
      function therefore applies the config's crediting RULE (mode,
      eligibility list, capture fraction) unconditionally. It is a
      reporting quantity only: nothing in the LP, the offers, or the
      capacity screens may consume it (those go through the gated
      resolvers above).
    * **Keyed by fuel-type NAME** (the :class:`FleetContext` /
      plant-financials representation), not ``FleetArrays`` codes. A name
      unknown to ``FUEL_TYPE_MAP`` credits 0 rather than raising — cached
      contexts are data, not config, so a stray label is not a config
      error.

    Args:
        config: Scenario config supplying the crediting fields. ``None``
            falls back to a default :class:`ScenarioConfig` (i.e. the
            owner-default ``clean_capture`` crediting) so config-less
            summary callers still get a well-defined physical clean
            share.
        fuel_types: Per-generator fleet fuel-type names.
        emission_rates: Per-generator CO2 rates in tCO2/MWh at the LP
            boundary (the ``cesa_ci`` crediting input), aligned with
            ``fuel_types``.

    Returns:
        Float array of credit fractions in ``[0, 1]``, one per entry of
        ``fuel_types``.
    """
    if config is None:
        global _DEFAULT_REPORTING_CONFIG
        if _DEFAULT_REPORTING_CONFIG is None:
            _DEFAULT_REPORTING_CONFIG = ScenarioConfig()
        config = _DEFAULT_REPORTING_CONFIG
    # Unknown names map to -1, a code no fuel carries -> credit 0.
    fuel_idx = np.array([FUEL_TYPE_MAP.get(f, -1) for f in fuel_types], dtype=int)
    return _credit_fractions_from_codes(
        config, fuel_idx, np.asarray(emission_rates, dtype=float)
    )


def unit_credit_fraction(
    config: ScenarioConfig, fuel_type: str, emission_rate_t_per_mwh: float
) -> float:
    """Return one unit's CES credit fraction from its fuel and CO2 rate.

    Scalar companion of :func:`unit_credit_fractions` for the capacity
    screens, which loop existing ``Generator`` objects rather than
    holding a ``FleetArrays`` (the retirement screen's per-unit
    attribute-revenue seam, plan §5.3). Same crediting semantics, one
    unit at a time:

    * Disabled CES: ``0.0``.
    * ``clean_capture``: eligible fuels 1.0, ``gas_cc_ccs`` at the
      policy-assumed capture fraction, everything else 0.
    * ``cesa_ci``: eligible fuels earn
      ``clip(1 − emission_rate/benchmark, 0, 1)`` on the unit's own CI —
      for an existing ``gas_cc_ccs`` unit that is its actual residual
      rate, not the class construction — and unabated ``gas_cc`` at or
      under the CI threshold earns the same benchmark formula.

    Args:
        config: Scenario config supplying the ``federal_ces_*`` fields.
        fuel_type: The unit's fleet fuel type.
        emission_rate_t_per_mwh: The unit's CO2 rate in tCO2/MWh at the
            LP boundary (``Generator.emission_rate_co2``).

    Returns:
        Credit fraction in ``[0, 1]``.
    """
    if not config.federal_ces_enabled:
        return 0.0

    eligible = fuel_type in config.federal_ces_eligible_fuels
    if config.federal_ces_crediting == "clean_capture":
        if not eligible:
            return 0.0
        if fuel_type == "gas_cc_ccs":
            return config.federal_ces_ccs_capture_fraction
        return 1.0

    # cesa_ci (the only other mode; __post_init__ validates the name).
    credited = eligible or (
        fuel_type == "gas_cc"
        and emission_rate_t_per_mwh
        <= config.federal_ces_unabated_ci_threshold_t_per_mwh
    )
    if not credited:
        return 0.0
    return float(
        np.clip(
            1.0 - emission_rate_t_per_mwh / config.federal_ces_ci_benchmark_t_per_mwh,
            0.0,
            1.0,
        )
    )


def tech_credit_fraction(config: ScenarioConfig, tech: str) -> float:
    """Return the CES credit fraction for a candidate technology / fuel type.

    The class-level companion of :func:`unit_credit_fractions` for the
    capacity-economics screens, which reason about technologies rather
    than fleet units (plan §5.1 candidate mapping):

    * Disabled CES: ``0.0`` for every tech.
    * ``nuclear_smr`` / ``nuclear_large`` alias to ``nuclear``; eligible
      fuels (default: nuclear, wind, solar, hydro, geothermal,
      offshore_wind, hydrogen_ct, hydrogen_ccgt) credit at 1.0.
    * ``gas_cc_ccs`` credits at the policy-assumed
      ``federal_ces_ccs_capture_fraction`` in ``clean_capture`` mode, and
      at the CESA benchmark formula on the residual CLASS CI in
      ``cesa_ci`` mode. The residual class CI mirrors the new-build
      candidate construction exactly (``model/capacity.py``,
      ``_build_new_entrant``): best-bin unabated gas-CC CO2 rate ×
      ``(1 − config.ccs_capture_rate)`` — the ENGINEERING capture rate,
      because cesa_ci credits the CI the unit will physically carry,
      while ``clean_capture`` pays the policy-assumed fraction.
    * ``storage`` credits 1.0 only when ``federal_ces_storage_eligible``
      (owner D5 default: off — discharge creates no new attribute).
    * Everything else (unabated fossil techs, imports, biomass) is 0.
      Per-unit cesa_ci crediting of unabated gas CC under the CI
      threshold is a UNIT-level property (it depends on the unit's own
      emission rate) and goes through :func:`unit_credit_fractions`, not
      this class-level table.

    Args:
        config: Scenario config supplying the ``federal_ces_*`` fields.
        tech: Candidate technology or fleet fuel-type name.

    Returns:
        Credit fraction in ``[0, 1]``.
    """
    if not config.federal_ces_enabled:
        return 0.0

    fuel = _TECH_FUEL_ALIASES.get(tech, tech)
    if fuel == "storage":
        return 1.0 if config.federal_ces_storage_eligible else 0.0
    if fuel not in config.federal_ces_eligible_fuels:
        return 0.0
    if fuel == "gas_cc_ccs":
        if config.federal_ces_crediting == "clean_capture":
            return config.federal_ces_ccs_capture_fraction
        # cesa_ci: benchmark formula on the residual class CI, mirroring
        # the capacity.py new-entrant emission-rate construction.
        residual_ci = min(CO2_RATES["gas_cc"].values()) * (
            1.0 - config.ccs_capture_rate
        )
        return float(
            np.clip(
                1.0 - residual_ci / config.federal_ces_ci_benchmark_t_per_mwh,
                0.0,
                1.0,
            )
        )
    return 1.0


def effective_eac_price_for_tech(
    config: ScenarioConfig, tech: str, year: int | None
) -> float:
    """Return the effective EAC price in real $/MWh for a tech in a year.

    ``max()`` of the legacy exogenous per-tech scalar
    (:func:`market_sim.policy.eac.get_eac_price_for_new_entry`) and the
    federal CES premium × the tech's credit fraction — the certificate is
    sold once, to whichever buyer clears higher (house no-stack doctrine;
    the caller's further ``max()`` against the RPS dual is unchanged).
    With the CES disabled this is exactly the legacy value.

    Args:
        config: Scenario config supplying legacy and federal CES fields.
        tech: Candidate technology or fleet fuel-type name.
        year: Simulation year (premium path resolution). ``None`` is
            legal only while the CES is disabled (see
            :func:`premium_for_year`).

    Returns:
        The effective EAC price in real 2026$/MWh.
    """
    legacy = get_eac_price_for_new_entry(tech, config)
    federal = premium_for_year(config, year) * tech_credit_fraction(config, tech)
    return max(legacy, federal)


def effective_eac_price_for_unit(
    config: ScenarioConfig,
    fuel_type: str,
    emission_rate_t_per_mwh: float,
    year: int | None,
) -> float:
    """Return one existing unit's effective EAC price in real $/MWh.

    The retirement-screen seam (plan §5.3): ``max()`` of the unit's
    legacy per-fuel scalar and the federal CES premium × its
    :func:`unit_credit_fraction` — unit-level rather than tech-level so
    that under ``cesa_ci`` a credited unabated ``gas_cc`` (or an abated
    unit's actual residual CI) earns its own fraction. The caller's
    further ``max()`` folds (§45U, RPS dual) are unchanged. With the CES
    disabled this is exactly the legacy value.

    Args:
        config: Scenario config supplying legacy and federal CES fields.
        fuel_type: The unit's fleet fuel type.
        emission_rate_t_per_mwh: The unit's CO2 rate in tCO2/MWh at the
            LP boundary (``Generator.emission_rate_co2``).
        year: Simulation year (premium path resolution). ``None`` is
            legal only while the CES is disabled (see
            :func:`premium_for_year`).

    Returns:
        The effective EAC price in real 2026$/MWh.
    """
    legacy = get_eac_price_for_new_entry(fuel_type, config)
    federal = premium_for_year(config, year) * unit_credit_fraction(
        config, fuel_type, emission_rate_t_per_mwh
    )
    return max(legacy, federal)


def federal_ces_suppresses_state_rps(config: ScenarioConfig) -> bool:
    """Return True when the federal CES replaces the state RPS rows.

    The pure-federal counterfactual (plan §5.3, ``runner`` seam): with
    ``federal_ces_enabled`` AND ``federal_ces_replaces_state_rps`` both
    on, the state RPS LP row is not built (``rps_target`` stays ``None``),
    so no RPS dual exists and the federal premium is the only attribute
    mechanism. Moot for ERCOT/PJM, which carry no RPS row.
    """
    return bool(config.federal_ces_enabled and config.federal_ces_replaces_state_rps)


def effective_unit_eac_prices(
    config: ScenarioConfig, fleet: FleetArrays, year: int | None
) -> np.ndarray:
    """Return per-generator effective EAC prices in real $/MWh, ``(n_gen,)``.

    Element-wise ``max()`` of the legacy per-fuel ``eac_price_*`` scalars
    broadcast onto the fleet (the ``_EAC_PRICE_FIELDS`` mapping — the
    same fuels :func:`market_sim.policy.eac.apply_eac_to_mc` credits) and
    the federal CES premium × :func:`unit_credit_fractions`. One
    certificate per MWh, sold once — never a sum. With the CES disabled
    this is exactly the legacy broadcast.

    Args:
        config: Scenario config supplying legacy and federal CES fields.
        fleet: Vectorized fleet arrays supplying ``fuel_type_idx`` and
            ``emission_rate``.
        year: Simulation year (premium path resolution). ``None`` is
            legal only while the CES is disabled (see
            :func:`premium_for_year`).

    Returns:
        Float array of effective EAC prices, shape ``(n_gen,)``.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    legacy = np.zeros(fuel_idx.shape[0], dtype=float)
    # Small fixed loop over the ~7 legacy EAC fuels (never over units or
    # hours): broadcast each per-fuel scalar onto its generators.
    for fuel, field_name in _EAC_PRICE_FIELDS.items():
        code = FUEL_TYPE_MAP.get(fuel)
        if code is None:
            # "storage" has a legacy EAC field but is not a fleet fuel
            # type — its credit rides the discharge slot, not a generator.
            continue
        price = getattr(config, field_name)
        if price != 0.0:
            legacy[fuel_idx == code] = price

    federal = premium_for_year(config, year) * unit_credit_fractions(config, fleet)
    return np.maximum(legacy, federal)
