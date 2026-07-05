"""Emissions accounting from dispatch results.

Converts a thermal dispatch schedule into hourly system-wide pollutant
totals. The hourly functions follow the same vectorized pattern: weight
each generator's hourly output by its per-MWh emission rate and sum across
the fleet.

:func:`compute_must_run_emissions` is a separate, post-processing step: the
CHP must-run (steam) tranche is removed from the LP capacity, so its
generation and emissions are reconstructed here for asset-level reporting.
"""

import numpy as np
import pandas as pd


def compute_emissions(dispatch: np.ndarray, emission_rates: np.ndarray) -> np.ndarray:
    """Return hourly system CO2 emissions from a dispatch schedule.

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        emission_rates: Per-generator CO2 rate of shape ``(n_gen,)`` in
            tCO2/MWh.

    Returns:
        Hourly system CO2 emissions of shape ``(T,)`` in tCO2.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    emission_rates = np.asarray(emission_rates, dtype=float)
    return (dispatch * emission_rates[:, None]).sum(axis=0)


def compute_fossil_avg_rate(
    dispatch: np.ndarray, emission_rates: np.ndarray
) -> np.ndarray:
    """Return the hourly fossil-only average CO2 emission rate (tCO2/MWh).

    For each hour ``t``::

        rate[t] = Σ_g dispatch[g, t] × emission_rates[g]   (over fossil g)
                  ------------------------------------------------------
                  Σ_g dispatch[g, t]                       (over fossil g)

    i.e. the tCO2 emitted by fossil generation that hour divided by the
    fossil MWh generated that hour — the average carbon intensity of the
    *emitting* fleet, not of the whole system (zero-carbon generation is
    excluded from both numerator and denominator). This is the location-based
    average emission factor for attributional Scope 2 accounting of unmatched
    grid purchases (scope2-lce-portfolio ADR 0013), as opposed to a marginal
    /non-baseload rate, which is a consequential-accounting concept.

    The fossil subset is identified as ``emission_rates > 0``: per
    ``market_sim.config.constants.FUEL_CO2_FACTOR_PER_MMBTU`` only fossil
    fuels (gas, coal, oil) carry a nonzero CO2 factor — nuclear, wind, solar,
    hydro, geothermal, imports, hydrogen, and biomass (biogenic, carbon-
    neutral under EPA/RGGI accounting) are all zero — so no fuel-type string
    list is needed.

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        emission_rates: Per-generator CO2 rate of shape ``(n_gen,)`` in
            tCO2/MWh.

    Returns:
        Hourly fossil-fleet average CO2 rate of shape ``(T,)`` in tCO2/MWh.
        Hours with zero fossil dispatch return ``0.0`` (no fossil generation
        that hour means there is nothing to attribute at the fossil rate),
        never ``nan``/``inf``.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    emission_rates = np.asarray(emission_rates, dtype=float)
    fossil = emission_rates > 0.0  # emitting (fossil) generators only
    fossil_co2 = (dispatch[fossil] * emission_rates[fossil][:, None]).sum(axis=0)
    fossil_mwh = dispatch[fossil].sum(axis=0)
    # Zero-fossil hours: no emitting generation to average -> rate 0, not nan.
    return np.divide(
        fossil_co2,
        fossil_mwh,
        out=np.zeros_like(fossil_co2),
        where=fossil_mwh > 0.0,
    )


def compute_nox(dispatch: np.ndarray, nox_rates: np.ndarray) -> np.ndarray:
    """Return hourly system NOx emissions from a dispatch schedule.

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        nox_rates: Per-generator NOx rate of shape ``(n_gen,)`` in
            tons NOx/MWh.

    Returns:
        Hourly system NOx emissions of shape ``(T,)`` in tons NOx.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    nox_rates = np.asarray(nox_rates, dtype=float)
    return (dispatch * nox_rates[:, None]).sum(axis=0)


def compute_so2(dispatch: np.ndarray, so2_rates: np.ndarray) -> np.ndarray:
    """Return hourly system SO2 emissions from a dispatch schedule.

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        so2_rates: Per-generator SO2 rate of shape ``(n_gen,)`` in
            tons SO2/MWh.

    Returns:
        Hourly system SO2 emissions of shape ``(T,)`` in tons SO2.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    so2_rates = np.asarray(so2_rates, dtype=float)
    return (dispatch * so2_rates[:, None]).sum(axis=0)


def startup_co2_tons(
    fit: pd.DataFrame,
    startup_co2_kg_by_plant: dict[int, float],
) -> pd.Series:
    """Return per-plant reporting-only startup CO2 (metric tons).

    EM-5 / plan §5 R6: the measured incremental CO2 of bringing a unit online
    (``campd._startup_factors`` ``startup_co2_kg``, a per-start kg adder) times
    the model's simulated start count (``plant_hourly_fit.model_starts``). This
    is a **reporting-only** figure — bounded at 0.015-0.018% of annual CO2, and
    under 0.2% even at a 10x cycling error (plan §3) — so it is never in the
    dispatch LP and its computation is gated default-OFF
    (:attr:`ScenarioConfig.startup_co2_reporting`).

    Args:
        fit: The ``plant_hourly_fit`` frame, carrying ``plant_code`` and the
            persisted ``model_starts`` column.
        startup_co2_kg_by_plant: ``{plant_code: measured kg per start}`` from the
            CAMPD emission-rate artifact's pooled rows.

    Returns:
        A Series of startup CO2 (metric tons) indexed by ``plant_code``; empty
        when ``fit`` lacks ``model_starts`` / ``plant_code``.
    """
    if (
        fit is None
        or fit.empty
        or not {"plant_code", "model_starts"} <= set(fit.columns)
    ):
        return pd.Series(dtype=float)
    starts = fit.set_index("plant_code")["model_starts"].astype(float)
    kg = (
        pd.Series(startup_co2_kg_by_plant, dtype=float)
        .reindex(starts.index)
        .fillna(0.0)
    )
    return (starts * kg / 1000.0).rename("startup_co2_tons")


def _chp_group_from_unit_type(unit_type: str) -> str | None:
    """Map a CAMPD ``unit_type`` to the model CHP plant_group, or ``None``.

    The three gas CHP bins the must-run reconstruction covers split by prime
    mover: combined cycle → ``CC_CHP``, combustion/gas turbine → ``CT_CHP``,
    boiler/fired steam → ``ST_CHP``. ``None`` for unit types outside these
    (they are not among the must-run bins).
    """
    s = str(unit_type).lower()
    if "combined cycle" in s:
        return "CC_CHP"
    if "turbine" in s:  # "combustion turbine", "gas turbine"
        return "CT_CHP"
    if "boiler" in s or "fired" in s or "steam" in s:
        return "ST_CHP"
    return None


def measured_class_cf(annual: pd.DataFrame) -> dict[str, float]:
    """Return ``{plant_group: measured capacity factor}`` from CAMPD history.

    A CHP class's forward behind-the-meter utilization, grounded in measured
    operation rather than a fabricated constant (EM-7 / plan §5 R5). Cogen units
    are identified directly by their **measured steam output**
    (``steam_load_klbh_sum > 0`` — a CEMS-reported CHP signature, not an
    assumption), split into ``CC_CHP`` / ``CT_CHP`` / ``ST_CHP`` by CAMPD
    ``unit_type``. Each unit-year contributes its op-hours fraction
    ``op_hours / 8760`` (near-baseloaded steam-host CHP runs close to flat, so
    measured op-hours utilization is the right forward CF prior), gen-weighted
    across the class. Reproducible and forward-admissible (op-hours regenerate
    and respond to fleet changes; CLAUDE.md rule 13); replaces the flat 0.85.

    ``annual`` needs columns ``unit_type``, ``steam_load_klbh_sum``,
    ``gross_mwh`` and ``op_hours`` (the ``emissions-unit-annual`` grain).
    Returns an empty map when the frame lacks them or holds no steam-reporting
    units, so the caller falls back to its flat ``must_run_cf``.
    """
    need = {"unit_type", "steam_load_klbh_sum", "gross_mwh", "op_hours"}
    if annual is None or annual.empty or not need <= set(annual.columns):
        return {}
    df = annual[
        (annual["steam_load_klbh_sum"].astype(float) > 0.0)
        & (annual["gross_mwh"].astype(float) > 0.0)
    ].copy()
    if df.empty:
        return {}
    df["plant_group"] = df["unit_type"].map(_chp_group_from_unit_type)
    df = df[df["plant_group"].notna()]
    if df.empty:
        return {}
    df["cf"] = (df["op_hours"].astype(float) / 8760.0).clip(0.0, 1.0)
    # Gen-weighted class CF: high-output unit-years dominate the class prior.
    out: dict[str, float] = {}
    for grp, sub in df.groupby("plant_group", observed=True):
        w = sub["gross_mwh"].to_numpy(dtype=float)
        cf = sub["cf"].to_numpy(dtype=float)
        tot = w.sum()
        out[str(grp)] = float((cf * w).sum() / tot) if tot > 0 else 0.0
    return out


def compute_must_run_emissions(
    bins: pd.DataFrame,
    year: int,
    must_run_cf: float = 0.85,
    total_gen_by_plant: dict[int, float] | None = None,
    btm_share_by_plant: dict[int, float] | None = None,
    measured_rate_by_plant: dict[int, float] | None = None,
    class_cf_by_group: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Reconstruct CHP must-run (behind-the-meter) generation and emissions.

    The Must-Run tranche of each CHP plant (capacity serving a steam
    contract) is removed from the dispatch LP, so its behind-the-meter
    grid-invisible generation never appears in the dispatch result. This
    adds it back for asset-level emissions and total-generation reporting.
    Covers CC_CHP, CT_CHP and ST_CHP; coal is excluded (its must-run share
    stays in the LP as a ``_mustrun`` tranche).

    Two sizing modes:

    * **Measured-share (preferred for backcasts).** When ``total_gen_by_plant``
      is given — the plant's measured net generation *for the bin's class*,
      e.g. EIA-923 Page 1 keyed per ``(plant, class)`` — the behind-the-meter
      generation is that total times the plant's host self-supply share
      (``btm_share_by_plant``, a 0-1 fraction; the sector-keyed
      :func:`market_sim.data.chp.chp_btm_pct` shares / per-plant overrides,
      the same share the LP hold-out uses). EIA-923 is
      gross-minus-station-service and so *includes* the host's on-site
      electricity, while the LP only dispatches the grid-delivered slice
      (which EIA-930 sees). Both factors are measured inputs, so the
      resulting BTM — and any benchmark derived from it — is reproducible
      and independent of the model's own dispatch (CLAUDE.md rule #13:
      sizing the BTM off ``total − model grid dispatch`` made the
      grid-delivered "actual" equal the model whenever the model
      under-dispatched, so the fuel-mix gate could never fail — a circular,
      vacuous pass — and the attribution varied with unversioned solve
      state). Keying off the per-class total (rather than whole-plant
      netgen) keeps a plant that splits across classes from inflating one
      class with another's output.
    * **Measured-CF fallback (forecasts).** Without measured totals, the
      estimate is ``nameplate × share × 8760 × cf`` where ``share`` is the
      plant's measured host self-supply share (``btm_share_by_plant``, from
      :func:`market_sim.data.chp.measured_btm_share_by_plant`) when the plant
      is covered, else the bin's own ``pct_mr`` (which already bakes the
      sector-keyed :func:`market_sim.data.chp.chp_btm_pct` default), and
      ``cf`` is the plant's class measured capacity factor
      (``class_cf_by_group``, from :func:`measured_class_cf`) when available,
      else the flat ``must_run_cf``.

    CO2 is booked at the plant's **measured** rate (``measured_rate_by_plant``,
    the same v2 ``(plant, fuel-class)`` rate its grid tranches use) when the
    plant is covered, so a covered CHP plant's behind-the-meter CO2 intensity
    equals its grid intensity (EM-7 consistency, plan §5 R5). Uncovered plants
    fall back to the fuel-class ``get_emission_rate(fuel, hr_weighted)``.

    Args:
        bins: The per-plant bin frame from
            :func:`market_sim.data.fleet.load_campd_bins`, carrying
            ``Plant_Code``, ``pct_mr``, ``capacity_mw``, ``hr_weighted``,
            ``fuel`` and (for the class-CF fallback) ``Plant_Group``.
        year: Simulation year, recorded on each output row.
        must_run_cf: Flat capacity-factor fallback for the forecast estimate
            when no measured class CF is supplied for the plant's group.
        total_gen_by_plant: Optional ``{plant_code: annual MWh}`` of measured
            net generation for the plant's bin class (e.g. EIA-923 keyed per
            ``(plant, class)``). Triggers the measured-share mode.
        btm_share_by_plant: Optional ``{plant_code: fraction}`` host
            self-supply share of the plant's generation. In the measured-share
            mode it sizes the host pull-out from ``total_gen_by_plant``; in
            the measured-CF fallback (no ``total_gen_by_plant``) it instead
            sizes ``mr_mw`` directly, in place of the bin's own ``pct_mr``
            share. Either way a plant absent from the mapping falls back to
            its bin ``pct_mr`` share.
        measured_rate_by_plant: Optional ``{plant_code: tCO2/MWh net}`` measured
            CO2 rate for the plant's must-run fuel class — the same v2 rate the
            grid tranches book. Used when positive; else the fuel-class default.
        class_cf_by_group: Optional ``{plant_group: capacity factor}`` measured
            class CF for the forecast estimate (:func:`measured_class_cf`).

    Returns:
        One row per non-coal must-run plant with ``mr_mw``, ``mr_gen_mwh``
        and ``mr_co2_tons``; empty when no such plant exists.
    """
    from market_sim.data.fleet import get_emission_rate

    mr = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")].copy()
    if mr.empty:
        return mr.assign(mr_mw=[], mr_gen_mwh=[], mr_co2_tons=[], year=[])

    mr["year"] = year
    if total_gen_by_plant is not None:
        shares = btm_share_by_plant or {}
        total = mr["Plant_Code"].map(total_gen_by_plant).fillna(0.0)
        share = mr["Plant_Code"].map(shares).fillna(mr["pct_mr"] / 100.0)
        mr["mr_gen_mwh"] = (total * share).clip(lower=0.0)
        mr["mr_mw"] = mr["mr_gen_mwh"] / 8760.0
    else:
        shares = btm_share_by_plant or {}
        share = mr["Plant_Code"].map(shares).fillna(mr["pct_mr"] / 100.0)
        mr["mr_mw"] = mr["capacity_mw"] * share
        class_cf = class_cf_by_group or {}
        if "Plant_Group" in mr.columns and class_cf:
            cf = mr["Plant_Group"].astype(str).map(class_cf).fillna(must_run_cf)
        else:
            cf = must_run_cf
        mr["mr_gen_mwh"] = mr["mr_mw"] * 8760.0 * cf

    measured = measured_rate_by_plant or {}

    def _co2_rate(r: pd.Series) -> float:
        # A covered plant books its measured (v2) rate — the identical rate its
        # grid tranches use — so BTM and grid CO2 intensity agree (plan §5 R5).
        m = measured.get(int(r["Plant_Code"]))
        if m is not None and m > 0.0:
            return float(m)
        return get_emission_rate(r["fuel"], r["hr_weighted"])

    mr["mr_co2_tons"] = mr.apply(lambda r: r["mr_gen_mwh"] * _co2_rate(r), axis=1)
    return mr
