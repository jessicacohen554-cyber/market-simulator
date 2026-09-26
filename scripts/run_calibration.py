"""Run the dispatch model for calibration years and print comparison tables.

Backcasts the hourly economic dispatch against historical years for which EIA
actuals exist, then prints headline diagnostics — generation by fuel, CO2,
zonal prices, negative-price hours and renewable curtailment — so the modeled
year can be eyeballed against the eGRID benchmark.

Each calibration year is run as a single-year dispatch (no capacity
evolution): the EIA-860 fleet is dispatched against that year's EIA-930
demand and renewable profiles, with the renewable capacity and gas price
pinned to the year's measured values.

Any ``--year`` outside the 2023-2025 training window is a designated holdout
and hard-fails at the entry point unless authorized (CLAUDE.md rule 22
[R-HOLDOUT]): the gate is ``run_calibration_full.enforce_holdout_year_gate``
— freeze first, then the year's tier marker plus ``--holdout-authorized``,
fail closed. (Closed 2026-08-16, third-party audit gap row B1: this CLI was
the one solve entry point outside the three-gate enforcement.)

Usage:
    python scripts/run_calibration.py --year 2023
    python scripts/run_calibration.py --year 2023 2024 2025
    python scripts/run_calibration.py --year 2023 --hours 168
    python scripts/run_calibration.py --year 2023 --ttc-wn 9000 --ttc-wsc 3000

Options:
    --year         One or more calibration years to run.
    --iso          ISO to calibrate (default ERCOT).
    --hours        Dispatch horizon in hours (default 8760); use a small
                   value such as 168 for a quick smoke test.
    --ttc-wn       Override the West<->North transfer capability (MW).
    --ttc-wsc      Override the West<->South_Central transfer capability (MW).
    --ttc-pn       Override the Panhandle<->North transfer capability (MW).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    HOURS_PER_YEAR,
    resolve_reference_price_interface,
)
from market_sim.config.interchange_config import (  # noqa: E402
    INTERFACE_NEIGHBORS,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
    resolve_priced_interchange,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand,
    load_ercot_fossil_gen,
)
from market_sim.data.fleet import (  # noqa: E402
    _hour_to_month_index,
    apply_coal_tranches,
    apply_ercot_ct_offer_surface,
    apply_neiso_coldsnap_derate,
    apply_netload_drag_floors,
    assemble_mc,
    build_base_fleet,
    build_dispatch_fleet,
    build_ercot_offer_surface_conditional_markup,
    build_ercot_offer_surface_lowcurve_markdown,
    build_caiso_offer_surface_conditional_markup,
    build_neiso_offer_surface_conditional_markup,
    build_pjm_offer_surface_conditional_markup,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_campd_bins,
    load_fleet_from_csv,
    load_mothballed_but_operating,
    load_retired_within_window,
    thermal_tranche_overrides,
)
from market_sim.data.offer_curves import (  # noqa: E402
    apply_cc_committed_offer_margin,
    apply_gas_offer_margin,
    apply_miso_offer_spread_anchored,
    apply_miso_offer_surface,
)
from market_sim.data.fuel import (  # noqa: E402
    apply_caiso_zonal_gas_basis,
    apply_coal_supply_pricing,
    apply_dual_fuel_pricing,
    apply_ercot_west_netload_gas_shape,
    apply_ercot_zonal_gas_basis,
    apply_hub_basis_overlay,
    apply_miso_gas_marginal_commodity,
    apply_miso_winter_citygate_daily,
    apply_miso_zonal_gas_basis,
    apply_nyiso_downstate_ct_gas_basis,
    apply_nyiso_downstate_ct_gas_daily,
    apply_nyiso_ldc_generator_delivered_gas,
    apply_nyiso_zonal_gas_basis,
    apply_pjm_zonal_gas_basis,
    apply_plant_monthly_fuel_prices,
    dual_fuel_switch_mask,
    ercot_west_oversupply_collapse_freq,
    resolve_fuel_prices,
)
from market_sim.data.renewables import (  # noqa: E402
    hsl_potential_mw,
    inject_offshore_wind_availability,
    load_hsl_hourly,
    load_renewable_profiles,
)
from market_sim.data.input_completeness import check_clean_partitions  # noqa: E402
from market_sim.pipeline import (  # noqa: E402
    UNSET,
    DispatchSpec,
    EnergySolveResult,
    apply_ercot_commitment_posture,
    apply_reserve_coopt,
    backcast_config,
    build_base_dispatch_kwargs,
    resolve_hydro_cascade,
    resolve_hydro_period_hours,
    build_caiso_ra_p1_prep,
    build_caiso_reserve_p1_prep,
    build_ercot_gas_bridge_p1_preps,
    build_miso_coal_night_floor_p1_prep,
    build_nyiso_gas_bridge_p1_prep,
    build_pjm_reserve_p1_prep,
    build_soco_gas_st_campaign_p1_prep,
    build_spp_gas_bridge_p1_prep,
    reset_pass_timing_log,
    run_commitment_pass,
    run_energy_solve,
    take_pass_timing_log,
)
import market_sim.pipeline.reference as _pipeline_reference  # noqa: E402
import market_sim.pipeline.ttc as _pipeline_ttc  # noqa: E402
from market_sim.pipeline.backcast_config import (  # noqa: E402
    _GENERIC_NEUTRAL_GAS_CLASSES,  # noqa: F401 -- re-exported for test_offer_curve_deleakage
    _MISO_CC_COAL_REBALANCE,
    _deep_merge_offer_curve,
    _neutralize_generic_gas_bands,  # noqa: F401 -- re-exported for test_offer_curve_deleakage
)
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    reserve_storage_as_power,
    storage_cap_profiles,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    apply_interchange_injections,
    build_incidence_matrix,
    build_interface_groups,
    build_caiso_link_loss,
    build_miso_link_loss,
    build_nyiso_link_loss,
    build_pjm_link_loss,
    get_link_bidirectional_array,
    get_link_flow_cost_array,
    get_ttc_array,
    wecc_border_carbon_adder,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.constraints import (  # noqa: E402
    build_mass_cap_dispatch_kwargs,
)
from market_sim.policy.eac import (  # noqa: E402
    apply_eac_to_mc,
    apply_negative_renewable_offer_floor,
    compute_eac_dispatch_credits,
)
from market_sim.policy.ira import compute_dispatch_credits  # noqa: E402
from market_sim.results.calibration import (  # noqa: E402
    check_hourly_dispatch_correlation,
)
from market_sim.results.emissions import compute_emissions  # noqa: E402
from market_sim.results.outputs import FleetContext  # noqa: E402

# Model fuel types that make up the EIA-930 "natural gas" telemetry series:
# combined cycle, combustion turbine and gas steam are reported as one fuel.
_GAS_FUEL_TYPES: frozenset[str] = frozenset({"gas_cc", "gas_ct", "gas_st"})

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_calibration")

# Reference + TTC-overlay halves: PERMANENT same-name aliases of their canonical
# pipeline homes (orchestrator-unification lane, refactor-consolidation plan §5 —
# the Stage-7 ``_calibration_config`` precedent below). The bodies moved to
# ``market_sim.pipeline.{reference,ttc}``; this module's exported symbol names
# are a frozen surface (probe scripts, tests and ``run_calibration_full``'s seam
# imports all read them), so every moved name keeps its ``_``-prefixed spelling
# here and resolves to the SAME object. Verified equivalent before conversion by
# ``inspect.getsource`` diff (name-only) and constant equality.
#
# Calibration reference written by scripts/data/build_calibration_reference.py.
REFERENCE_PATH: Path = _pipeline_reference.REFERENCE_PATH

# Fallback measured Henry Hub annual-average spot price ($/MMBtu), used when
# the calibration reference JSON has not yet been generated.
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
_HENRY_HUB_FALLBACK: dict[int, float] = _pipeline_reference.HENRY_HUB_FALLBACK

_MWH_PER_TWH: float = 1.0e6
_TONNES_PER_MT: float = 1.0e6

# Zone-pair identifying each transfer link whose TTC the CLI can override.
# Both legs of the West Texas Export interface and the Panhandle GTC are
# exposed for tuning — these are ERCOT's primary wind-export constraints.
_TTC_LINK_ZONES: dict[str, frozenset[str]] = _pipeline_ttc.TTC_LINK_ZONES

_load_reference = _pipeline_reference.load_reference
_henry_hub_actual = _pipeline_reference.henry_hub_actual

# Backward-compatible alias (orchestrator-unification Stage 7 moved the
# function to market_sim.pipeline.backcast_config): probe/derive scripts and
# tests importing ``_calibration_config`` from this module, or calling it via
# ``rc._calibration_config``, keep working unchanged.
_calibration_config = backcast_config

_apply_ttc_overrides = _pipeline_ttc.apply_ttc_overrides
_apply_iso_year_ttc = _pipeline_ttc.apply_iso_year_ttc
_apply_iso_monthly_ttc = _pipeline_ttc.apply_iso_monthly_ttc


def _apply_caiso_solar_deliverability(
    solar_cf: np.ndarray, iso: str, year: int, config
) -> np.ndarray:
    """Re-curtail the CAISO solar potential for the local congestion the reduced
    topology can't see (Lever D).

    Two CAISO-only paths, both operating on the per-zone solar CF upper bound the
    LP dispatches against:

    * **Structural** (``config.caiso_solar_deliverability``, the keeper path): a
      local-deliverability derate ``clip(1 − k × solar_frac(t), floor, 1)`` from
      :func:`market_sim.model.transmission.caiso_solar_deliverability_derate`,
      driven by the FORWARD solar-penetration signal. The curtailed VOLUME emerges
      per-year from that year's own penetration/build — never a pin to actuals.

    * **Interim stopgap** (``config.caiso_solar_cap_at_delivered``, a default-off
      DIAGNOSTIC): caps each hour's solar at the measured EIA-930 delivered share
      of the HSL potential. This PINS solar to the measured outcome (no forward
      analogue) and must never feed a keeper — it exists only as an A/B reference
      for the structural derate (CLAUDE.md #11).

    Returns ``solar_cf`` unchanged (byte-identical) for non-CAISO ISOs, when
    neither flag is set, or when the forward signal / HSL data is unavailable.
    """
    if iso.upper() != "CAISO":
        return solar_cf
    hours = solar_cf.shape[1]

    if getattr(config, "caiso_solar_cap_at_delivered", False):
        # DIAGNOSTIC: delivered/potential ratio from the HSL parquet (delivered
        # gen ÷ uncurtailed potential), applied as a per-hour ceiling on the CF.
        from market_sim.data.renewables import load_hsl_hourly

        hsl = load_hsl_hourly("CAISO", year)
        if hsl is not None:
            pot = hsl["solar_hsl_mw"].to_numpy(dtype=float)[:hours]
            gen = hsl["solar_gen_mw"].to_numpy(dtype=float)[:hours]
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(pot > 0.0, np.clip(gen / pot, 0.0, 1.0), 1.0)
            logger.info(
                "CAISO %d: solar cap-at-delivered DIAGNOSTIC (default-off pin, "
                "not forecast skill) — solar potential haircut to measured "
                "delivered, mean ratio %.3f midday",
                year,
                float(
                    np.mean(
                        ratio[
                            (np.arange(hours) % 24 >= 9) & (np.arange(hours) % 24 <= 15)
                        ]
                    )
                ),
            )
            return solar_cf * ratio[None, :]
        logger.warning(
            "CAISO %d: --caiso-solar-cap-at-delivered requested but no HSL "
            "parquet — solar left uncapped (no-op)",
            year,
        )
        return solar_cf

    if getattr(config, "caiso_solar_endogenous_spill", False):
        logger.info(
            "CAISO %d: endogenous solar spill — full solar potential passed "
            "to LP (no pre-LP CF derate); solar sets the midday dual when "
            "curtailed",
            year,
        )
        return solar_cf

    if getattr(config, "caiso_solar_deliverability", False):
        from market_sim.model.transmission import caiso_solar_deliverability_derate

        derate = caiso_solar_deliverability_derate(
            year,
            hours,
            float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
            float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
        )
        if derate is not None:
            hod = np.arange(hours) % 24
            mid = (hod >= 9) & (hod <= 15)
            logger.info(
                "CAISO %d: local solar deliverability derate (Lever D) — "
                "solar potential capped at clip(1 − %.3f × solar_frac, %.2f, 1); "
                "midday mean derate %.3f (≈ %.1f%% midday curtailment headroom)",
                year,
                float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
                float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
                float(np.mean(derate[mid])),
                100.0 * (1.0 - float(np.mean(derate[mid]))),
            )
            return solar_cf * derate[None, :]
        logger.warning(
            "CAISO %d: caiso_solar_deliverability on but no forward solar "
            "penetration signal — solar left uncapped (no-op)",
            year,
        )
    return solar_cf


def p0_commitment_pattern(
    p0_dispatch: "np.ndarray", pmax: "np.ndarray"
) -> "np.ndarray":
    """Bit-pack the P0 on/off pattern — the markup's ONLY input from P0.

    :func:`market_sim.model.commitment.compute_monthly_markup` touches the P0
    dispatch through exactly one expression,
    ``find_runs(dispatch[g, h0:h1] > threshold)`` with
    ``threshold = 0.05 * pmax[g]``. The boolean this returns is therefore the
    **complete and exact** P0 contribution to the P1 startup amortization:
    nothing in the markup depends on the P0 dispatch *level*.

    Persisting it lets a later session rebuild a surrogate dispatch
    ``pmax[:, None] * unpacked`` and hand it to the PRODUCTION markup function,
    which then returns the bit-identical array the solve itself used — so the
    markup is READ rather than reconstructed. That closes the P0-proxy error
    (18-22 pp on MISO's CT) which no committed bundle could bound, because
    ``hourly/`` sidecars carry ``pass == "P1"`` only
    (``results/calibration/FINDING-miso154-ct-commitment-instrument-2026-08-12.md``
    section 4; the repair is pre-registered in
    ``PREREG-miso155-p0-exact-commitment-instrument-2026-08-13.md``).

    Args:
        p0_dispatch: The P0 (base-cost) dispatch, shape ``(n_gen, T)``.
        pmax: Per-generator Pmax, shape ``(n_gen,)``.

    Returns:
        ``np.packbits`` of the ``(n_gen, T)`` on/off boolean, shape
        ``(n_gen, ceil(T / 8))`` of ``uint8``. Rows with ``pmax == 0`` pack as
        all-off: their threshold is 0 and a zero dispatch is not ``> 0``, which
        is what the markup itself sees.
    """
    return np.packbits(
        np.asarray(p0_dispatch) > (0.05 * np.asarray(pmax))[:, None], axis=1
    )


def _aggregate_pass_timing(final: "EnergySolveResult") -> "dict":
    """Sum a year's build / P0 / P1 solve seconds over EVERY energy-solve pass.

    ``markup`` is not a measured phase: ``run_calibration_full.solve_and_persist``
    derives it as ``energy_solve_s - build_s - solve_p0_s - solve_p1_s``. Before
    PERF-B session 3 (charter C-2) the three subtrahends came from the FINAL
    :class:`EnergySolveResult` alone — ``p1.build_time``, ``r0.solve_time``,
    ``p1.solve_time`` — while ``energy_solve_s`` spans the whole bracket. A year
    is not always one energy solve (the ercot-221 adaptive-expectation offer runs
    a second P1 pass; ercot-230's fixed point iterates), so every EARLIER pass's
    whole matrix build and both HiGHS runs were booked as ``markup``, and so was
    the P0 model's build whenever P1 cold-rebuilt: 91-94 % of an ERCOT year's
    ``markup`` was solver and build time under the wrong name
    (``docs/FINDING-perfb-s2-markup-attribution-2026-09.md`` §1, §4.1).

    This drains the per-pass log ``pipeline.solve.run_energy_solve`` writes and
    returns the SUMS — ``build_s`` (every ``DispatchModel`` build of every
    pass), ``solve_p0_s`` and ``solve_p1_s`` (every pass's two ``h.run()``) —
    plus the summed interior ``markup_parts``. With those as the subtrahends,
    ``markup`` is the genuine non-solve, non-build residual (both passes'
    solution marshalling, ``compute_monthly_markup``, the P0→P1 seam) and no
    ``prior_build`` / ``prior_solve`` component is needed. The remainder — this
    frame's call edges and the between-pass adaptive machinery (spike detection,
    P_hat, floor assembly) — is booked by ``solve_and_persist`` as ``other``, so
    the emitted clause is exhaustive over ``markup``.

    Args:
        final: The year's last :class:`EnergySolveResult`. Read ONLY when the
            per-pass log is empty (a caller that bypassed the shared solve, or
            a test double that never appended), in which case its own per-pass
            fields are the one pass there is.

    Returns:
        ``{"build_s", "solve_p0_s", "solve_p1_s", "markup_parts", "n_passes"}``.
        ``markup_parts`` is the ordered summed ``{component: seconds}``, empty
        when nothing was recorded (which emits no clause at all).
    """
    passes = take_pass_timing_log()
    if not passes:
        return {
            "build_s": float(getattr(final, "build_s", 0.0) or 0.0),
            "solve_p0_s": float(getattr(final, "solve_p0_s", 0.0) or 0.0),
            "solve_p1_s": float(getattr(final, "solve_p1_s", 0.0) or 0.0),
            "markup_parts": dict(getattr(final, "markup_parts", {}) or {}),
            "n_passes": 1,
        }
    parts: dict[str, float] = {}
    for entry in passes:
        for name, seconds in entry["parts"].items():
            parts[name] = parts.get(name, 0.0) + seconds
    return {
        "build_s": float(sum(e["build_s"] for e in passes)),
        "solve_p0_s": float(sum(e["solve_p0_s"] for e in passes)),
        "solve_p1_s": float(sum(e["solve_p1_s"] for e in passes)),
        "markup_parts": parts,
        "n_passes": len(passes),
    }


def _p1_storage_cost_identical(
    candidate: np.ndarray,
    pass1_override: "np.ndarray | None",
    dispatch_kwargs: dict,
) -> bool:
    """Is an adaptive pass's P1 storage discharge cost the one pass 1 solved with?

    The exact-equality guard of PERF-B session 3 charter item C-1a. An
    adaptive-expectation pass (ercot-221) re-runs :func:`run_energy_solve`
    with every argument the SAME OBJECT as pass 1's except
    ``p1_storage_discharge_cost``. That array is the ONLY thing that can
    differ between the two LPs, and ``lp.costs.build_cost_vector`` writes it
    into the discharge columns elementwise — a static ``(n_storage,)`` /
    scalar cost broadcast across hours, an hourly ``(n_storage, T)`` cost
    transposed — so two costs that are elementwise equal after broadcasting
    produce the identical cost vector on the identical matrix. When that
    holds, the pass would hand HiGHS the LP pass 1 already solved and pass 1's
    result IS the answer; the caller skips the pass.

    Exact ``np.array_equal`` — no tolerance, no ``isclose``: the claim is
    identity of the LP, not proximity, so the guard must be an equality. NaN
    anywhere reads as not-identical (``array_equal`` semantics), which is the
    conservative side.

    Args:
        candidate: The adaptive pass's ``(n_storage, T)`` discharge cost.
        pass1_override: Pass 1's own ``p1_storage_discharge_cost`` (the
            ercot-219 reservation offer) or ``None`` when pass 1 solved on
            the kwargs default.
        dispatch_kwargs: The shared LP kwargs; ``storage_discharge_cost`` is
            what pass 1's P1 used when ``pass1_override`` is ``None`` (the
            LP default ``0.0`` if the key is absent, mirroring
            ``solve_dispatch``'s signature default).

    Returns:
        ``True`` iff ``candidate`` equals pass 1's resolved cost at every
        ``(unit, hour)``.
    """
    cand = np.asarray(candidate, dtype=float)
    base = (
        pass1_override
        if pass1_override is not None
        else dispatch_kwargs.get("storage_discharge_cost", 0.0)
    )
    base = np.asarray(base, dtype=float)
    try:
        if base.ndim == 2:
            ref = base
        else:
            # Static per-unit (n_storage,) or scalar: broadcast across hours
            # exactly as build_cost_vector does (rows = units, cols = hours).
            ref = np.broadcast_to(
                base.reshape(-1, 1) if base.ndim == 1 else base, cand.shape
            )
    except ValueError:
        return False
    return cand.shape == ref.shape and bool(np.array_equal(cand, ref))


def _renewable_bound_is_delivered_pinned(iso: str, year: int) -> bool:
    """Is the year's renewable CF bound the raw delivered outcome?

    Screened on 2023 by ercot-251 (docs/RESULT-ercot251-nohsl-ceiling-screen-2026-09-06.md)
    and ADMITTED as a correctness fix by owner ruling 2026-09-06 (ercot-252,
    docs/PRECOMMIT-ercot252-2022-repair-resolve-2026-09-06.md); byte-identical wherever an
    HSL parquet exists (every ERCOT training year), live only on no-HSL years.
    The curtailment gates below skip their ceiling when the bound already embeds the
    historical curtailment, because capping an already-curtailed series double-curtails it.
    They test HSL-parquet existence for that, which is wrong whenever the loader falls
    through to ``forecast_uncurtailed`` -- the delivered shape GROSSED UP by another year's
    reference rate, which is real headroom the ceiling is supposed to take back (see
    renewables.renewable_bound_provenance, and the forecast leg at renewables.py L2496-2513
    which pairs gross-up + ceiling deliberately). Only ``delivered_pinned`` needs the guard.
    """
    from market_sim.data.renewables import (
        RENEWABLE_BOUND_DELIVERED_PINNED,
        renewable_bound_provenance,
    )

    return all(
        renewable_bound_provenance(iso, year, fuel) == RENEWABLE_BOUND_DELIVERED_PINNED
        for fuel in ("wind", "solar")
    )


def _measured_heat_rate_flags(config: ScenarioConfig) -> dict[str, bool]:
    """Return the five measured-heat-rate flags as loader keyword arguments.

    F1 D4: the retiree and mothball channels take the SAME measured heat-rate
    swaps the operable fleet loader does, read from one place so the three
    call sites cannot drift (rule 24 [R-REGISTRY]).
    """
    return {
        name: bool(getattr(config, name, False))
        for name in (
            "measured_ct_heat_rates",
            "measured_coal_heat_rates",
            "measured_st_heat_rates",
            "measured_cc_heat_rates",
            "measured_chp_heat_rates",
        )
    }


def _reliability_floor_layup_shares(
    config, iso: str, year: int, fleet_arrays
) -> dict[tuple[int, str], np.ndarray] | None:
    """Lay-up shares for ``ScenarioConfig.reliability_floor_layup_window_mask``.

    Returns ``{(plant_code, plant_group): (hours,) laid-up capacity share}`` read
    from the lay-up half of the SAME merit-guarded detection the availability
    overlay reads its outage half from — every selector and basis argument
    mirrors ``data.fleet.arrays``' own ``unit_outage_derate_factors`` call, which
    is what makes the two shares additive (the loader's contract). Returns
    ``None`` when the mask is off, the run is not a backcast (rule 13: same-year
    lay-up windows have no forward analogue), or the run carries no historic
    outage overlay for the windows to be a complement of — so the off path is
    byte-inert.
    """
    if not getattr(config, "reliability_floor_layup_window_mask", False):
        return None
    if getattr(config, "mode", "forecast") != "backcast":
        return None
    if getattr(config, "outage_source", None) != "historic":
        return None
    from types import SimpleNamespace

    from market_sim.data.outages import (
        BINS_CSV_DEFAULT,
        lp_bin_capacity_index,
        unit_layup_removed_fractions,
    )

    iso_u = (iso or "ERCOT").upper()
    per_unit = bool(getattr(config, "campd_per_unit_attribution", False))
    merit = per_unit and bool(getattr(config, "campd_outage_merit_order_guard", False))
    lp_bins = None
    if (
        getattr(config, "unit_outage_dispatched_bin_denominator", False)
        and iso_u != "ERCOT"
    ):
        lp_bins = lp_bin_capacity_index(
            [
                SimpleNamespace(plant_code=int(c), plant_group=str(g))
                for c, g in zip(fleet_arrays.plant_code, fleet_arrays.plant_group)
            ],
            np.asarray(fleet_arrays.pmax, dtype=float),
        )
    shares = unit_layup_removed_fractions(
        int(getattr(config, "weather_year", 0) or year),
        int(fleet_arrays.availability.shape[1]),
        getattr(config, "campd_bins_path", None) or str(BINS_CSV_DEFAULT),
        iso=iso_u,
        cc_steam_part_reclass=getattr(config, "cc_steam_part_reclass", False),
        cc_nameplate_basis=getattr(config, "unit_outage_lp_capacity_basis", False),
        st_capacity_basis=getattr(config, "unit_outage_st_capacity_basis", False),
        per_unit_clip=getattr(config, "unit_outage_per_unit_clip", False),
        extract_basis_share=getattr(config, "unit_outage_extract_basis_share", False),
        lp_bin_capacity=lp_bins,
        per_unit_crosswalk=per_unit,
        merit_order_guard=merit,
        hour_grain=merit
        and bool(getattr(config, "unit_outage_window_hour_grain", False)),
    )
    logger.info(
        "%s %d: reliability_floor_layup_window_mask ARMED: %d plant-group "
        "lay-up share series mask the pro_rata reliability-floor basis",
        iso,
        year,
        len(shares),
    )
    return shares


def run_year(
    year: int,
    iso: str,
    hours: int,
    gas_price: float,
    ttc_overrides: dict[str, float | None],
    coal_passthrough: float | None = None,
    commitment_enabled: bool = False,
    commitment_screen_coal: bool = True,
    coal_lignite_mustrun: float | None = None,
    coal_prb_mustrun: float | None = None,
    coal_prb_passthrough: float = 1.0,
    outage_source: str = "historic",
    coal_prb_passthrough_sigmoid: bool = False,
    coal_mustrun_per_plant: bool = False,
    retiree_cems_cap: bool = False,
    ct_mustrun_per_plant: bool = False,
    ct_mustrun_floor_frac: float = 1.0,
    coal_drop_pof: bool = False,
    coal_prb_passthrough_tiered: bool = False,
    prb_overrides: dict | None = None,
    coal_bit_sigmoid: bool = False,
    bit_overrides: dict | None = None,
    coal_econ_srmc_bound: bool = False,
    coal_econ_marginal_hr_bound: bool | None = None,
    committed_band_measured_basis: bool | None = None,
    ercot_offer_hrmult_ep_rebasis: bool | None = None,
    ercot_offer_hrmult_ep_rebasis_bands: "list[str] | None" = None,
    coal_takeorpay_from_data: bool = False,
    coal_mustrun_online_pmin: bool = False,
    coal_sync_srmc_tranche: bool = False,
    commitment_floor_window_netload: bool = False,
    ct_intermediate_split: bool = False,
    ct_intermediate_cf_threshold: float | None = None,
    cc_intermediate_split: bool = False,
    cc_intermediate_cf_threshold: float | None = None,
    tranche_startup_amortization: bool = False,
    tranche_startup_measured_runs: bool = False,
    tranche_startup_conditional_runs: bool = False,
    gas_offer_margin: bool = False,
    gas_offer_margin_zonal_anchor: bool = False,
    coal_offer_margin: bool = False,
    cc_committed_offer_margin: bool = False,
    coal_peak_offer_margin: bool = False,
    coal_peak_offer_yearly_level: bool = False,
    coal_perplant_offer_level: bool = False,
    coal_perplant_offer_yearly: bool = False,
    nysdec_peaker_rule_availability: bool = False,
    nyiso_solar_market_generator_basis: bool = False,
    oil_primary_bin_fuel: bool = False,
    plant_tranche_config: str | None = None,
    storage_daily_cycling: bool = False,
    storage_vintage_ramp: bool = False,
    battery_dispatch_adder: float = 0.0,
    gas_offer_curve: bool = False,
    gas_monthly_actuals: bool = False,
    pjm_zonal_gas_basis: bool = False,
    miso_zonal_gas_basis: bool = False,
    miso_winter_citygate_daily: bool = False,
    pjm_congestion: bool = False,
    offer_curve_overrides: dict[str, dict[str, float]] | None = None,
    offer_curve_deltas: dict[str, dict[str, float]] | None = None,
    curve_smoothing: dict[str, float | int | None] | None = None,
    cc_derate_from_top: bool = False,
    cc_nameplate_summer_derate: bool = False,
    coal_nameplate_summer_derate: bool = False,
    gt_ambient_derate: bool = False,
    gt_ambient_derate_ref_c: float | None = None,
    gt_ambient_derate_slope_cc: float | None = None,
    gt_ambient_derate_slope_ct: float | None = None,
    temp_dependent_derate: bool = False,
    temp_derate_hourly_grain: bool = False,
    temp_derate_mean_anchored: bool = False,
    temp_derate_classes: frozenset[str] | tuple[str, ...] | None = None,
    temp_derate_slope_st_chp: float | None = None,
    temp_derate_slope_ct_chp: float | None = None,
    ercot_offer_surface_conditional: bool = False,
    ercot_offer_surface_midcurve_conditional: bool = False,
    ercot_offer_surface_cleared_share: bool = False,
    ercot_offer_surface_cleared_share_state: bool = False,
    ercot_offer_surface_cleared_share_steam: bool = False,
    ercot_offer_surface_lowcurve: bool = False,
    ercot_offer_surface_lowcurve_floorscoped: bool = False,
    wind_ptc_vintage_offers: bool = False,
    neiso_offer_surface_conditional: bool = False,
    pjm_offer_surface_conditional: bool = False,
    pjm_da_virtual_bids: bool = False,
    pjm_offer_midcurve_conditional: bool = False,
    pjm_offer_midcurve_segments: "tuple[str, ...] | None" = None,
    caiso_offer_surface_measured: bool = False,
    caiso_offer_surface_measured_ungrounded: bool = False,
    caiso_st_gas_committed_measured: bool = False,
    caiso_st_gas_peak_measured: bool = False,
    caiso_ct_peaker_committed_measured: bool = False,
    nyiso_ct_peaker_bands_measured: bool = False,
    nyiso_ct_peaker_committed_measured: bool = False,
    nyiso_st_gas_econ_bands_deleaked: bool = False,
    caiso_offer_surface_conditional: bool = False,
    nearby_fuel_price_zone_donor_guard: bool = False,
    fleet_state_from_eia860: bool = False,
    caiso_citygate_spot_coverage: bool = False,
    ercot_nuclear_unit_availability: bool = False,
    nuclear_unit_availability: bool = False,
    ercot_thermal_dam_availability: bool = False,
    ercot_thermal_dam_availability_hourly: bool = False,
    ercot_thermal_dam_availability_plant: bool = False,
    ercot_wind_zone_shape: bool = False,
    ercot_noncampd_plant_availability: bool = False,
    ercot_storage_capability_measured: bool = False,
    ercot_online_capacity_envelope_measured: bool = False,
    ercot_ordc_only_scarcity: bool = False,
    must_run_mw: "np.ndarray | None" = None,
    inject_biomass_mustrun: bool = False,
    priced_interchange: bool = False,
    hydro_backfill_year: int | None = None,
    as_reserve_withholding: bool = False,
    as_reserve_formula: bool = False,
    energy_reserve_coopt: bool = False,
    miso_zonal_reserves: bool = False,
    miso_midwest_subregional_reserves: bool = False,
    miso_reserve_pergen: bool = False,
    miso_commitment_posture: bool = False,
    miso_reserve_online_gated: bool = False,
    miso_measured_reserve_requirements: bool = False,
    miso_south_seam_split: bool = False,
    miso_rdt_tcdc: bool = False,
    miso_zonal_loss_surface: bool = False,
    pjm_zonal_loss_surface: bool = False,
    ercot_multiproduct_as_coopt: bool = False,
    ercot_ecrs_conservative_deployment: bool = False,
    ercot_nonreleasable_as_withholding: bool = False,
    ercot_ordc_total_reserve: bool = False,
    ercot_as_aware_commitment: bool = False,
    ercot_reserve_supply_cap: bool = False,
    ercot_reserve_supply_cap_from_year: int = 2023,
    ercot_reserve_supply_forward: bool = False,
    pjm_reserve_supply_cap: bool = False,
    pjm_reserve_online_gated: bool = False,
    pjm_reserve_online_rho: float = 1.0,
    pjm_reserve_commitment_scoped: bool = False,
    pjm_reserve_pergen: bool = False,
    pjm_reserve_pergen_sync: bool = False,
    pjm_reserve_pergen_size_split: bool = False,
    pjm_commitment_posture: bool = False,
    measured_ramp_capability: bool = False,
    ercot_as_forward_requirement: bool = False,
    ercot_load_resource_reserve: bool = False,
    ercot_load_resource_reserve_from_year: int = 2023,
    ercot_storage_as_reserve: bool = False,
    ercot_storage_as_reserve_from_year: int = 2025,
    ercot_ecrs_requirement: bool = False,
    ercot_ecrs_requirement_from_year: int = 2023,
    ordc_lolp_params_path: str | None = None,
    ercot_storage_as_product_credit: bool = False,
    gas_hh_monthly_shape: bool = False,
    storage_as_commitment: bool = False,
    ercot_storage_as_deployment: bool = False,
    ercot_storage_as_deployment_from_year: int = 2023,
    ercot_storage_as_endogenous: bool = False,
    ercot_storage_as_duration_gate: bool = False,
    hydro_eia930_monthly: bool = False,
    hydro_budget_period_by_instrument: bool = False,
    hydro_forecast_budget: bool = False,
    hydro_year: str = "normal",
    interchange_shaping: bool = False,
    interchange_shaping_export_only: bool = False,
    reference_price_interface: bool = False,
    negative_renewable_offers: bool | None = None,
    caiso_gas_commitment_floor: bool | None = None,
    caiso_gas_floor_frac: float | None = None,
    caiso_ra_mustoffer: bool | None = None,
    caiso_ra_min_load_frac: float | None = None,
    caiso_ra_startup_bridge: bool | None = None,
    caiso_ra_bridge_decommit: bool | None = None,
    ercot_gas_commitment_bridge: bool | None = None,
    ercot_gas_bridge_min_load_frac: float | None = None,
    ercot_gas_bridge_startup: bool | None = None,
    ercot_gas_bridge_da_horizon: bool | None = None,
    ercot_gas_bridge_online_hours: bool | None = None,
    ercot_commitment_posture: bool | None = None,
    ercot_commitment_posture_min_load_frac: float | None = None,
    carry_operating_mothballs: bool | None = None,
    reliability_floor: bool | None = None,
    reliability_floor_overrides: dict | None = None,
    # nyiso-140 per-plant floor-membership exclusion. The mechanism landed in
    # 3febd5c wired end-to-end EXCEPT here: solve_and_persist grew the kwarg and
    # passes it to run_year, which had no parameter to receive it, so EVERY
    # calibration solve of EVERY ISO raised TypeError at HEAD (found by ercot-213
    # 2026-08-16 on the first replay after the merge). Default None = leave the
    # config's own value, so the arming semantics and the "default off, every
    # existing bundle byte-identical" claim are untouched.
    # (miso-160 rebase, 2026-08-17: the nyiso-140 branch's own merge ALSO added
    # this parameter nine lines up, so main carried it TWICE — a SyntaxError
    # blocking every solve CLI at HEAD. The bare duplicate is removed; this
    # commented one stays.)
    reliability_floor_plant_exclusions: bool | None = None,
    scarcity_price_overlay: bool | None = None,
    caiso_scarcity_pricing: bool | None = None,
    caiso_lcr_commitment_credit: bool | None = None,
    caiso_solar_deliverability: bool | None = None,
    caiso_solar_deliverability_k: float | None = None,
    caiso_solar_endogenous_spill: bool | None = None,
    caiso_solar_cap_at_delivered: bool | None = None,
    neiso_gas_coldsnap_derate: bool | None = None,
    neiso_coldsnap_derate_dualfuel_unswitched: bool | None = None,
    neiso_oil_burn_budget: bool | None = None,
    neiso_winter_fuel_inventory: bool | None = None,
    neiso_winter_fuel_start_fill_bbl: float | None = None,
    neiso_winter_fuel_mustrun: bool | None = None,
    coal_fuel_inventory: bool | None = None,
    caiso_import_hub_prices: bool | None = None,
    caiso_import_gas_coupling: bool | None = None,
    caiso_import_solar_shape: bool | None = None,
    caiso_per_hub_intertie: bool | None = None,
    caiso_perhub_firm_base: bool | None = None,
    caiso_corridor_flow_limit: bool | None = None,
    caiso_intertie_reference_price: bool | None = None,
    caiso_corridor_atc_forward: bool | None = None,
    caiso_reference_price_seam: bool | None = None,
    caiso_per_year_import_caps: bool | None = None,
    caiso_asymmetric_path_ratings: bool | None = None,
    caiso_zonal_loss_surface: bool | None = None,
    capacity_deliverability_limits: bool | None = None,
    unit_outage_lp_capacity_basis: bool | None = None,
    unit_outage_mixed_gas_routing: bool | None = None,
    unit_outage_st_capacity_basis: bool | None = None,
    unit_outage_per_unit_clip: bool | None = None,
    unit_outage_dispatched_bin_denominator: bool | None = None,
    unit_outage_short_windows_gas: bool | None = None,
    unit_outage_window_hour_grain: bool | None = None,
    campd_per_unit_attribution: bool | None = None,
    campd_outage_merit_order_guard: bool | None = None,
    netload_drag_layup_window_mask: bool | None = None,
    netload_drag_merit_allocation: bool | None = None,
    netload_drag_min_run_persistence: bool | None = None,
    vre_curtailment_oversupply_allocation: bool | None = None,
    spp_curtailment_ceiling: bool | None = None,
    spp_curtail_depth_wind: float | None = None,
    # caiso-186 published seasonal CC capability basis. run_calibration_full
    # .solve_and_persist has threaded this to run_year since the caiso-186
    # merge, but the parameter was never added here, so EVERY solve through
    # the orchestrator raised TypeError (see the ercot-185 FINDING §disclosed).
    cc_winter_capability_basis: bool | None = None,
    ramp_limits: bool | None = None,
    local_capacity_constraints: bool | None = None,
    nyiso_local_selfsupply: bool | None = None,
    nyiso_scr_edrp: bool | None = None,
    nyiso_scr_edrp_strike: float | None = None,
    nyiso_firm_imports: bool | None = None,
    nyiso_import_reconciliation: bool | None = None,
    nyiso_import_hub_prices: bool | None = None,
    nyiso_iroquois_winter_spread: bool | None = None,
    nyiso_synchronised_reserve: bool | None = None,
    nyiso_li_locational_reserve: bool | None = None,
    nyiso_incity_commitment_obligation: bool | None = None,
    nyiso_east_reserve_families: bool | None = None,
    nyiso_gas_commitment_bridge: bool | None = None,
    spp_gas_commitment_bridge: bool | None = None,
    soco_gas_st_campaign_commitment: bool | None = None,
    miso_coal_night_floor: bool | None = None,
    nyiso_gas_bridge_cc_min_load_frac: float | None = None,
    nyiso_gas_bridge_st_min_load_frac: float | None = None,
    nyiso_gas_bridge_startup: bool | None = None,
    nyiso_gas_bridge_da_horizon: bool | None = None,
    nyiso_gas_bridge_min_run: bool | None = None,
    nyiso_gas_bridge_plant_exclusions: bool | None = None,
    nyiso_gas_bridge_reserve_duty_exclusions: bool | None = None,
    nyiso_gas_bridge_plant_min_run: bool | None = None,
    nyiso_gas_bridge_online_hours: bool | None = None,
    nyiso_gas_bridge_state_floor_min_run: bool | None = None,
    nyiso_gas_bridge_startup_aware: bool | None = None,
    nyiso_chp_btm_measured: bool | None = None,
    cc_reserve_duty_split: bool | None = None,
    chp_layup_duty_split: bool | None = None,
    chp_layup_duty_curve: bool | None = None,
    egrid_identity_heat_rates: bool | None = None,
    measured_ct_heat_rates: bool | None = None,
    measured_coal_heat_rates: bool | None = None,
    measured_st_heat_rates: bool | None = None,
    egrid_family_heat_rates: bool | None = None,
    egrid_steam_collapse_heat_rates: bool | None = None,
    nyiso_gas_bridge_cc_min_run_hours: float | None = None,
    nyiso_gas_bridge_st_min_run_hours: float | None = None,
    nyiso_spin_reserve_online: bool | None = None,
    nyiso_spin_headroom_frac: float | None = None,
    nyiso_dynamic_reserve_requirements: bool | None = None,
    nyiso_hydro_reserve_eligible: bool | None = None,
    nyiso_scr_edrp_reserve_eligible: bool | None = None,
    neiso_dynamic_reserve_requirements: bool | None = None,
    miso_firm_imports: bool | None = None,
    miso_seam_flow_limit: bool = False,
    miso_seam_flow_percentile: float | None = None,
    miso_seam_export_limit: bool = False,
    miso_seam_envelope_merit_cap: bool = False,
    miso_seam_envelope_hour_ending_key: bool = False,
    miso_import_sil_measured_envelope: bool = False,
    nyiso_seam_deliverability_envelope: bool = False,
    nyiso_seam_par_attribution: bool = False,
    miso_pjm_border_anchor: bool = False,
    miso_cc_coal_rebalance: bool = False,
    miso_firm_import_floor: bool = False,
    miso_pjm_lmp_import_pricing: bool = False,
    miso_seam_measured_ladder: bool = False,
    pjm_seam_flow_limit: bool = False,
    pjm_seam_flow_percentile: float | None = None,
    pjm_seam_export_limit: bool = False,
    pjm_seam_measured_ladder: bool = False,
    pjm_seam_neighbour_hourly_ladder: bool = False,
    gas_hub_basis_overlay: bool | None = None,
    gas_st_netload_drag: bool = False,
    gas_st_drag_overrides: dict[str, float] | None = None,
    st_gas_intermediate: bool = False,
    st_gas_intermediate_cf_threshold: float | None = None,
    ct_netload_drag: bool | None = None,
    pjm_interface_feed_admissibility_gate: bool | None = None,
    gas_offer_margin_anchor_vintage: bool = False,
    gas_offer_margin_zonal_anchor_vintage: bool = False,
    ct_drag_overrides: dict[str, float] | None = None,
    chp_export_floor_measured: bool = False,
    ercot_gtc_limits_measured: bool = False,
    pjm_measured_interface_limits: bool = False,
    ercot_wtx_curtailment_driver: bool | None = None,
    ercot_wtx_curtail_depth_wind: float | None = None,
    ercot_wtx_curtail_depth_solar: float | None = None,
    mass_cap_enabled: bool = False,
    mass_cap_tons: float | None = None,
    mass_cap_program: str | None = None,
    zero_forcing_ablation: bool = False,
    fleet_only: bool = False,
    xyear_cache: "list | None" = None,
    demand: "np.ndarray | None" = None,
    persist_p0_commitment: bool = False,
    persist_p0_dispatch: bool = False,
) -> "tuple[object, FleetContext, object | None, dict] | dict":
    """Solve the single-year calibration dispatch for one ISO-year.

    Builds the calibration configuration, loads the EIA-860 generator and
    storage fleets and the year's EIA-930 demand and renewable profiles,
    assembles the marginal-cost array (fuel cost, cycling adders, EAC and
    IRA dispatch credits) and solves the hourly economic dispatch. No
    capacity evolution is performed — the fleet is dispatched as observed.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).
        ttc_overrides: Optional per-link TTC overrides for a sweep.
        coal_passthrough: Optional PRB coal contract-passthrough override.
        commitment_enabled: When True, run the P2 unit-commitment pass after
            P1 and return the P1 result for comparison.
        commitment_screen_coal: When False, coal is exempt from the P2 screen.
        zero_forcing_ablation: When True, neutralize every merchant floor/
            bridge (keeping only nuclear must-run, CHP steam-following and coal
            take-or-pay) via ``ScenarioConfig.as_zero_forcing_ablation`` after
            all config resolution — the D-3 ablation twin (audit §7 /
            CLAUDE.md rule 20).
        fleet_only: When True, stop after the fleet/storage arrays are built
            and return a state dict instead of solving any LP. Lets a
            post-processor (e.g. the ORDC scarcity overlay,
            ``scripts/data/derive_ordc_overlay.py``) reconstruct the exact hourly
            availability a persisted bundle solved against — same config,
            same outage overlay, same derates — without re-solving.
        priced_interchange: When True, interchange is served by the priced
            import/export node (import tranches + export sinks in the ISO's
            external zone, the forward-scenario mechanism) instead of the
            measured schedule added to demand. Lets a backcast validate the
            node's calibration against the EIA-930 net-interchange duration
            curve.
        mass_cap_enabled: When True, thread the unified carbon resolver's
            power-sector mass-cap ROW into this calibration year (G-29,
            docs/handoffs/emissions-mass-cap-plan-2026-07.md) instead of the
            default adder path. Default False leaves the calibration harness
            byte-identical (the row was previously unreachable here at all).
            A diagnostic/validation lever only — never a keeper default.
        mass_cap_tons: Optional explicit annual budget (metric tons CO2)
            overriding the ISO program's published schedule; see
            ``policy.cap_and_trade._power_sector_cap``.
        mass_cap_program: Optional cap label override (see
            ``policy.cap_and_trade._power_sector_cap``).
        demand: Optional pre-loaded hourly zonal demand array
            (``(n_zones, hours)``). When ``None`` (the default) it is loaded
            here via :func:`load_demand`. A caller may thread in the array it
            already loaded to avoid the duplicate read, but only when that
            array is byte-identical to what this function would load — i.e.
            same ``iso_config`` zones/load-shares, ``td_loss_factor``,
            ``include_interchange``, ``caiso_demand_clock_realign`` and
            ``ercot_tie_zonal_interchange``, and non-strict demand profile
            (this function never passes ``strict_demand_profile`` to
            :func:`load_demand`).
        persist_p0_commitment: OPT-IN (default ``False``), WRITE-ONLY. When
            set, stash the P0 commitment pattern and the startup run-ratio
            series in ``p2_state`` so the caller can persist them as bundle
            sidecars. Cannot change a solve — it is read after both LPs have
            run and nothing downstream consumes it — so it is a persistence
            parameter on the ``persist_p2_state`` precedent, NOT a
            ``ScenarioConfig`` field (CLAUDE.md rule 24 ``[R-REGISTRY]``
            governs tunables that can change a solve). See
            :func:`p0_commitment_pattern`.
        persist_p0_dispatch: OPT-IN (default ``False``), WRITE-ONLY, and the
            MW-valued sibling of ``persist_p0_commitment``. When set, stash the
            P0 dispatch array and the P0 zonal duals in ``p2_state`` so the
            caller can persist them as bundle sidecars. Same solve-invariance
            argument as its sibling — both are read after P0 and P1 have run
            and neither is consumed by anything downstream — so it is a
            persistence parameter, not a ``ScenarioConfig`` field.

            Why the MW array and not only the bit-packed pattern (caiso-287):
            the commitment sidecar carries the on/off pattern at the
            detector's ``0.05 x pmax`` threshold, which is enough to recover
            the bridge detector's ``runs`` but NOT enough to replay either
            screen that acts on them. The ``startup_aware`` run screen scores
            each run by ``sum((price - mc) * dispatch) / pmax``
            (:func:`model.commitment.caiso_ra_mustoffer_min_gen`), and the
            surplus decommit screen derives its hourly absorption from the
            interchange rows' dispatch
            (:func:`model.commitment._apply_economic_bridges`) — both read MW,
            and both read the P0 DUALS rather than the P1 prices the committed
            ``hourly/system_<year>.parquet`` carries. Persisting the two arrays
            the prep hook actually passes (``r0.dispatch``, ``r0.prices``, via
            :func:`pipeline.commitment.build_caiso_ra_p1_prep`) lets a later
            session replay both screens exactly, offline and at zero LP,
            instead of bounding them analytically.

    Returns:
        A tuple ``(result, context, result_p1, p2_state)``. ``result`` is the
        final dispatch (P2 when commitment is enabled, otherwise P1);
        ``result_p1`` is the pre-commitment P1 result when commitment ran,
        else ``None``; ``p2_state`` is the cached P1 input bundle that
        :func:`_commitment_pass` (the P2 post-process) consumes.
    """
    config = backcast_config(
        year,
        iso,
        hours,
        gas_price,
        coal_passthrough,
        commitment_enabled,
        commitment_screen_coal,
        coal_lignite_mustrun,
        coal_prb_mustrun,
        coal_prb_passthrough,
        outage_source,
        coal_prb_passthrough_sigmoid,
        coal_mustrun_per_plant,
        retiree_cems_cap,
        ct_mustrun_per_plant,
        ct_mustrun_floor_frac,
        coal_drop_pof,
        coal_prb_passthrough_tiered,
        offer_curve_overrides=offer_curve_overrides,
        offer_curve_deltas=offer_curve_deltas,
        ercot_offer_surface_conditional=ercot_offer_surface_conditional,
        ercot_offer_surface_midcurve_conditional=(
            ercot_offer_surface_midcurve_conditional
        ),
        neiso_offer_surface_conditional=neiso_offer_surface_conditional,
        pjm_offer_surface_conditional=pjm_offer_surface_conditional,
        pjm_da_virtual_bids=pjm_da_virtual_bids,
        pjm_offer_midcurve_conditional=pjm_offer_midcurve_conditional,
        caiso_offer_surface_measured=caiso_offer_surface_measured,
        caiso_offer_surface_measured_ungrounded=(
            caiso_offer_surface_measured_ungrounded
        ),
        caiso_st_gas_committed_measured=caiso_st_gas_committed_measured,
        caiso_st_gas_peak_measured=caiso_st_gas_peak_measured,
        caiso_ct_peaker_committed_measured=caiso_ct_peaker_committed_measured,
        nyiso_ct_peaker_bands_measured=nyiso_ct_peaker_bands_measured,
        nyiso_ct_peaker_committed_measured=nyiso_ct_peaker_committed_measured,
        nyiso_st_gas_econ_bands_deleaked=nyiso_st_gas_econ_bands_deleaked,
        caiso_offer_surface_conditional=caiso_offer_surface_conditional,
        nearby_fuel_price_zone_donor_guard=nearby_fuel_price_zone_donor_guard,
        fleet_state_from_eia860=fleet_state_from_eia860,
        caiso_citygate_spot_coverage=caiso_citygate_spot_coverage,
    )
    if pjm_offer_midcurve_segments is not None:
        # Rule-19 scope: floor only the named measured segments (e.g.
        # ("LONG_RUN",) so the CT_FAST rows stay owned by the fast-start
        # startup amortization). None = every mapped segment (pjm-101/102).
        config = config.with_overrides(
            pjm_offer_midcurve_segments=tuple(pjm_offer_midcurve_segments)
        )
    if ercot_offer_surface_cleared_share:
        # ERCOT-72 DAM cleared-share offer boundary (measured boundary + wall,
        # P1-only markup; ScenarioConfig field docstring has the full
        # provenance/admissibility note). ERCOT-gated in the builder.
        config = config.with_overrides(ercot_offer_surface_cleared_share=True)
    if ercot_offer_surface_cleared_share_state:
        # ERCOT-73 measured commitment-loading state weight on the wall
        # (ScenarioConfig field docstring has the provenance/admissibility
        # note). Requires the wall flag; the builder hard-errors otherwise.
        config = config.with_overrides(ercot_offer_surface_cleared_share_state=True)
    if ercot_offer_surface_cleared_share_steam:
        # ERCOT-77 steam-cliff extension of the wall (ScenarioConfig field
        # docstring has the provenance/admissibility + rule-19 row-scope
        # note). Requires the wall flag; the builder hard-errors otherwise.
        config = config.with_overrides(ercot_offer_surface_cleared_share_steam=True)
    if ercot_offer_surface_lowcurve:
        # G-22 conditional-offer-distribution LOW leg (measured trough-side
        # quantile ladders, P1-only markdown; ScenarioConfig field docstring has
        # the full provenance/admissibility note). ERCOT-gated in the builder.
        config = config.with_overrides(ercot_offer_surface_lowcurve=True)
    if ercot_offer_surface_lowcurve_floorscoped:
        # ERCOT-64 FLOOR-SCOPED committed-LSL markdown (the measured LSL bid
        # only in the gas commitment bridge's own floored plant-hours;
        # ScenarioConfig field docstring has the full provenance/composition
        # note). Requires the bridge and excludes the tranche-wide v2 —
        # enforced loud at pipeline.commitment.build_ercot_gas_bridge_p1_preps.
        config = config.with_overrides(ercot_offer_surface_lowcurve_floorscoped=True)
    if hydro_budget_period_by_instrument:
        # nyiso-220: shorten the hydro energy-budget period PER PLANT to the
        # period that project's own governing instrument -- or, where the
        # instrument states none, its measured pondage -- permits energy to be
        # reallocated over (registry
        # constants.HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT; the ScenarioConfig
        # field docstring carries the full provenance and the rule-19
        # reconciliation with hydro_dispatch_envelope). A plant absent from the
        # registry keeps the calendar month, so this is a byte-identical no-op
        # for every ISO with no entry.
        config = config.with_overrides(hydro_budget_period_by_instrument=True)
    if wind_ptc_vintage_offers:
        # ERCOT-65 PTC vintage scoping: replace the flat -ira_ptc_wind wind
        # dispatch offer with the per-zone-month measured-vintage blend
        # (ScenarioConfig field docstring has the full provenance /
        # adjudication note). ISO-agnostic; applied at the wind_mc seam.
        config = config.with_overrides(wind_ptc_vintage_offers=True)
    if ercot_nuclear_unit_availability:
        # Window-grain nuclear refuel availability (measured 60-Day DAM
        # disclosure daily series; ScenarioConfig field docstring has the full
        # provenance/admissibility note). ERCOT-gated in the fleet application.
        config = config.with_overrides(ercot_nuclear_unit_availability=True)
    if nuclear_unit_availability:
        # ISO-generic window-grain nuclear refuel availability (measured NRC
        # daily Power Reactor Status; ScenarioConfig field docstring has the
        # full provenance/admissibility note). The fleet application excludes
        # ERCOT, which keeps its own flag/file above.
        config = config.with_overrides(nuclear_unit_availability=True)
    if ercot_thermal_dam_availability:
        # Measured class-day thermal availability rescale (60-Day DAM
        # disclosure HSL/status; ScenarioConfig field docstring has the full
        # provenance/admissibility note). ERCOT-gated in the fleet application.
        config = config.with_overrides(ercot_thermal_dam_availability=True)
    if ercot_thermal_dam_availability_hourly:
        # ERCOT-96 grain switch: the same measured DAM availability applied at
        # class-HOUR grain (per-Hour-Ending fraction replaces the day-flat
        # block; ScenarioConfig field docstring has the full provenance note).
        # No effect unless ercot_thermal_dam_availability is also on.
        config = config.with_overrides(ercot_thermal_dam_availability_hourly=True)
    if ercot_thermal_dam_availability_plant:
        # ERCOT-97 plant grain: pin accepted-crosswalked plants to their own
        # measured site-hour fraction and water-fill the unmapped remainder so
        # the class-HOUR total is unchanged (redistribution; ScenarioConfig
        # field docstring has the full note). Requires the class-HOUR flag.
        config = config.with_overrides(ercot_thermal_dam_availability_plant=True)
    if ercot_wind_zone_shape:
        # ERCOT-113 per-zone wind SHAPE: each ERCOT zone gets its own MERRA-2
        # reanalysis wind shape instead of one ISO-wide profile (ScenarioConfig
        # field docstring has the full provenance note). Purely spatial — the
        # ISO aggregate is preserved exactly every hour, so only WHICH ZONE
        # holds the wind moves. ERCOT-gated in the renewable loader.
        config = config.with_overrides(ercot_wind_zone_shape=True)
    if ercot_noncampd_plant_availability:
        # Measured CAMPD-blind per-plant availability (60-Day DAM disclosure
        # live HSL + EIA-923 zero months; ScenarioConfig field docstring has the
        # full provenance/admissibility note). ERCOT-gated in the fleet
        # application.
        config = config.with_overrides(ercot_noncampd_plant_availability=True)
    if ercot_storage_capability_measured:
        # Measured hourly battery-fleet capability re-basis (60-Day DAM
        # disclosure non-OUT PWRSTR/ESR HSL; ScenarioConfig field docstring
        # has the full provenance/admissibility note). ERCOT-gated at the
        # storage-cap seam below.
        config = config.with_overrides(ercot_storage_capability_measured=True)
    if ercot_online_capacity_envelope_measured:
        # Measured-fleet-basis G-22 envelope (the ercot57 joint round;
        # ScenarioConfig field docstring has the provenance/identification
        # note). ERCOT-gated in the reserve design.
        config = config.with_overrides(ercot_online_capacity_envelope_measured=True)
    if gas_st_netload_drag:
        config = config.with_overrides(
            gas_st_netload_drag=True, **(gas_st_drag_overrides or {})
        )
    # Tri-state: None keeps the backcast_config per-ISO default (CAISO
    # keeper default-ON), True/False force the drag on/off — so an A/B arm
    # can run CAISO with the drag scrubbed (--no-ct-netload-drag) without
    # touching the keeper default.
    if ct_netload_drag is not None:
        config = config.with_overrides(ct_netload_drag=bool(ct_netload_drag))
        if ct_netload_drag and ct_drag_overrides:
            config = config.with_overrides(**ct_drag_overrides)
    # Tri-state (ct_netload_drag pattern): None keeps the backcast_config
    # per-ISO default (PJM ARMED default-ON, pjm-169 owner decision 2026-09-06),
    # True/False force it — so --no-pjm-interface-feed-admissibility-gate
    # expresses the PRE-ARM posture as an explicit caller value rather than an
    # absence, which is what keeps a control arm reachable and its key stable.
    if pjm_interface_feed_admissibility_gate is not None:
        config = config.with_overrides(
            pjm_interface_feed_admissibility_gate=bool(
                pjm_interface_feed_admissibility_gate
            )
        )
    if chp_export_floor_measured:
        # Measured steam-following export floor (backcast overlay): CHP bins'
        # grid floor rides at the year's measured EIA-923 class CF x the
        # sector grid-delivery share instead of the pooled CAMPD p2 minimum.
        config = config.with_overrides(chp_export_floor_measured=True)
    if ercot_gtc_limits_measured:
        # Measured ERCOT GTC transfer limits (backcast overlay): the GTC-
        # carrying links' export capability follows the hourly NP6-86 series
        # (gtc-limits clean datatype) instead of the static ttc_mw.
        config = config.with_overrides(ercot_gtc_limits_measured=True)
    if pjm_measured_interface_limits:
        # Measured PJM internal interface limits (backcast overlay): the
        # mapped internal links' forward capability follows the hourly Data
        # Miner 2 series (transfer-interface-limits clean datatype) instead
        # of the static ttc_mw / pjm_congestion medians.
        config = config.with_overrides(pjm_measured_interface_limits=True)
    # ERCOT West Texas Export corridor VRE curtailment-share driver (WP-B):
    # the West/Panhandle wind & solar CF ceiling follows the derived
    # net-load-indexed congestion share (data.curtailment_share) so the
    # sub-zonal Permian/CREZ nodal congestion the 8-zone reduction cannot
    # resolve is represented. depth=0 -> inert (zero-forcing ablation twin).
    # Tri-state (ct_netload_drag pattern): None keeps the backcast_config
    # per-ISO default (ERCOT keeper default-ON, owner GO 2026-07-07);
    # True/False force it on/off so an A/B arm can scrub the driver without
    # touching the keeper default.
    _wtx_overrides: dict = {}
    if ercot_wtx_curtailment_driver is not None:
        _wtx_overrides["ercot_wtx_curtailment_driver"] = bool(
            ercot_wtx_curtailment_driver
        )
    if ercot_wtx_curtail_depth_wind is not None:
        _wtx_overrides["ercot_wtx_curtail_depth_wind"] = float(
            ercot_wtx_curtail_depth_wind
        )
    if ercot_wtx_curtail_depth_solar is not None:
        _wtx_overrides["ercot_wtx_curtail_depth_solar"] = float(
            ercot_wtx_curtail_depth_solar
        )
    if _wtx_overrides:
        config = config.with_overrides(**_wtx_overrides)
    if mass_cap_enabled:
        # G-29 wiring: the calibration harness previously had no path to
        # mass_cap_enabled at all, so the mass-cap row (policy.cap_and_trade
        # .resolve_carbon_program's ROW path) was inert here even though
        # runner.py's forecast path has threaded it since the mass-cap plan
        # landed. Diagnostic-only lever (e.g. the RGGI dual-vs-auction-price
        # probe); never a keeper default.
        config = config.with_overrides(
            mass_cap_enabled=True,
            mass_cap_tons=mass_cap_tons,
            mass_cap_program=mass_cap_program,
        )
    if interchange_shaping:
        config = config.with_overrides(interchange_shaping=True)
    if interchange_shaping_export_only:
        config = config.with_overrides(
            interchange_shaping=True, interchange_shaping_export_only=True
        )
    if reference_price_interface:
        config = config.with_overrides(reference_price_interface=True)
    if coal_takeorpay_from_data:
        # Coal must-run sunk fraction = measured EIA-923 Schedule-5 take-or-pay
        # share per plant (campd_tranche_fuel_frac), not the hardcoded 100%.
        config = config.with_overrides(coal_takeorpay_from_data=True)
    if coal_mustrun_online_pmin:
        # Coal must-run band sized to the measured online-net-MW synchronization
        # Pmin (thermal_tranches mustrun_online_pct), not the all-hours
        # available-CF floor (rebuild step 2).
        config = config.with_overrides(coal_mustrun_online_pmin=True)
    if coal_sync_srmc_tranche:
        # SRMC-priced synchronization tranche (rebuild step 3a): the coal
        # online-Pmin band is split by the measured contract share into a
        # fuel-free _mustrun floor and a full-SRMC _sync band, both forced on so
        # coal holds synchronized at min-load while dispatchable tranches above
        # price-follow.
        config = config.with_overrides(coal_sync_srmc_tranche=True)
    if commitment_floor_window_netload:
        # Rank the SHARED commitment-floor window on NET load rather than
        # system load (SPP-66, owner ruling "Shared gate" 2026-09-20). One
        # series feeds all four floors that shape themselves on it -- coal
        # synchronization, the per-plant CC/ST_GAS committed floor, the ST_GAS
        # p25 level swap and the CT_PEAKER reliability must-run -- so they are
        # never windowed on different drivers (rule 19 [R-ONE-MECH]). Default
        # off, so every existing bundle keeps its key and its floors.
        config = config.with_overrides(commitment_floor_window_netload=True)
    if ct_intermediate_split:
        # Route the measured intermediate-duty CT cohort
        # (fleet.ct_intermediate_plants) to the flatter CT_INTERMEDIATE offer
        # curve so their always-on energy clears instead of carrying the steep
        # true-peaker start-cost hurdle (the CT_PEAKER-under / CC-over miss).
        config = config.with_overrides(ct_intermediate_split=True)
    if ct_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            ct_intermediate_cf_threshold=float(ct_intermediate_cf_threshold)
        )
    if cc_intermediate_split:
        # Route the measured baseload-duty CC cohort (fleet.cc_intermediate_plants)
        # to the flatter CC_INTERMEDIATE offer curve so the upper operating-range
        # tranches of MISO's near-baseload CC fleet clear instead of carrying the
        # ERCOT-peaker-fit rising econ ramp (the 2023/2024 gas-CC under-run). Only
        # the operating-range ramp is corrected; the duct-burner peak is unchanged.
        config = config.with_overrides(cc_intermediate_split=True)
    if cc_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            cc_intermediate_cf_threshold=float(cc_intermediate_cf_threshold)
        )
    if tranche_startup_amortization:
        # Fast-start tranche pricing (ISO-NE Order 825 analogue): the gas
        # bins' econ/peak tranches carry the same NREL start cost as the
        # committed anchor, so the P1 markup amortizes each tranche's own P0
        # run lengths into its bid — the fuel-price-invariant commitment-cost
        # component of the real offer stack the HR-multiplier curve cannot
        # express (winter over- / summer-evening under-pricing signature).
        config = config.with_overrides(tranche_startup_amortization=True)
    if tranche_startup_measured_runs:
        # v3 measured-run-length basis: the simple-cycle CT tranches amortize
        # over the CAMPD-measured median start-to-stop run length
        # (derive_campd_ct_run_lengths.py artifact) as the horizon ceiling —
        # P0 runs may only shorten it — removing the v2 circularity where
        # too-cheap offers → long P0 blocks → ≈0 markup (nyiso-44 finding).
        config = config.with_overrides(tranche_startup_measured_runs=True)
    if tranche_startup_conditional_runs:
        # v4 condition-keyed horizon: the v3 measured ceiling scales per hour
        # by the CAMPD-measured net-load-percentile band ratio (tight-hour
        # engagements are shorter commitment blocks — the ELMP evening-timing
        # element). Measured shape (campd_ct_run_bands_<ISO>.csv), forward-
        # native trigger (within-year net-load percentile); rules 13/23/25.
        config = config.with_overrides(tranche_startup_conditional_runs=True)
    if gas_offer_margin:
        # Gas-offer NET-REVENUE MARGIN form (markup compression): each gas
        # band's above-physical markup is repriced from the fuel-scaled
        # multiplier to a fixed $/MWh margin identified at the ISO's
        # training-window delivered-gas anchor — offers reduce exactly to the
        # registered multipliers at anchor gas and compress toward true MC as
        # gas rises (the 2022 NEISO holdout rotation + the neiso-45 winter-
        # over/summer-under signature). The anchor resolves HERE from the
        # registry so the bundle's run_config.json records the value
        # (rule 25); an ISO without a derived anchor is a hard error, never a
        # fallback (rule 24). Design: docs/handoffs/
        # gas-offer-net-revenue-margin-design-2026-07.md.
        from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

        if iso not in GAS_OFFER_MARGIN_ANCHOR_BY_ISO:
            raise SystemExit(
                f"--gas-offer-margin: no derived delivered-gas anchor for {iso} "
                "in constants.GAS_OFFER_MARGIN_ANCHOR_BY_ISO — run "
                "scripts/data/derive_gas_offer_margin_anchor.py and register "
                "the value (rule 24: anchors never cross ISO boundaries)"
            )
        config = config.with_overrides(
            gas_offer_net_revenue_margin=True,
            gas_offer_margin_anchor=GAS_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
        )
    if gas_offer_margin_zonal_anchor:
        # nyiso-109 — the SAME mechanism's identification point, resolved at
        # the grain its own definition requires. `_gas_series` (which the ISO
        # anchor is derived from) is ISO-level and does NOT carry the per-zone
        # basis the solve applies afterwards on the (n_gen, T) array, so on an
        # ISO whose keeper arms a zonal basis the ISO anchor is the REFERENCE
        # zone's level and every other zone's units price their markup at a
        # fuel level they never pay. The zone table resolves HERE from the
        # registry so run_config.json records the values (rule 21); an ISO
        # without one is a hard error, never a fallback (rules 24/25).
        # Identification: derive_gas_offer_margin_anchor.py --by-zone.
        from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ZONE

        if iso not in GAS_OFFER_MARGIN_ANCHOR_BY_ZONE:
            raise SystemExit(
                "--gas-offer-margin-zonal-anchor: no derived zone anchor table "
                f"for {iso} in constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE — run "
                "scripts/data/derive_gas_offer_margin_anchor.py --by-zone on "
                "that ISO's own basis and register the values (rule 25: a zone "
                "table never crosses an ISO boundary)"
            )
        config = config.with_overrides(
            gas_offer_margin_zonal_anchor=True,
            gas_offer_margin_anchor_by_zone=dict(GAS_OFFER_MARGIN_ANCHOR_BY_ZONE[iso]),
        )
    if coal_offer_margin:
        # Coal-offer NET-REVENUE MARGIN form (ERCOT-137, the gas form's coal
        # analogue): the CAMPD coal _mustrun (take-or-pay) band is repriced
        # from the fitted VOM-only sunk-fuel discount to the measured
        # net-margin-off-fuel-cost form — full delivered-fuel tracking plus a
        # fuel-invariant margin that lands the bid EXACTLY on the measured RT
        # curve bottom (SCED Submitted TPO-Price1 cap-wtd p50) at the
        # training-window delivered-coal anchor. Both identification
        # constants resolve HERE from the registries so the bundle's
        # run_config.json records the values (rule 25); an ISO without a
        # derived pair is a hard error, never a fallback (rule 24).
        # Identification: scripts/data/derive_coal_offer_margin_anchor.py.
        from market_sim.config.constants import (
            COAL_OFFER_MARGIN_ANCHOR_BY_ISO,
            COAL_OFFER_MARGIN_LEVEL_BY_ISO,
        )

        if (
            iso not in COAL_OFFER_MARGIN_ANCHOR_BY_ISO
            or iso not in COAL_OFFER_MARGIN_LEVEL_BY_ISO
        ):
            raise SystemExit(
                f"--coal-offer-margin: no derived delivered-coal anchor/level "
                f"for {iso} in constants.COAL_OFFER_MARGIN_ANCHOR_BY_ISO / "
                "COAL_OFFER_MARGIN_LEVEL_BY_ISO — run "
                "scripts/data/derive_coal_offer_margin_anchor.py and register "
                "the values (rule 24: anchors never cross ISO boundaries)"
            )
        config = config.with_overrides(
            coal_offer_net_revenue_margin=True,
            coal_offer_margin_anchor=COAL_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
            coal_offer_margin_level=COAL_OFFER_MARGIN_LEVEL_BY_ISO[iso],
        )
    if cc_committed_offer_margin:
        # CC COMMITTED-BLOCK measured offer level (ERCOT-139, the coal min-load
        # form's gas-CC analogue): the CC_REGULAR _committed tranche is repriced
        # from its band multiplier to full delivered-fuel tracking plus a
        # fuel-invariant margin that lands the bid EXACTLY on the measured RT
        # curve bottom (SCED Submitted TPO-Price1 cap-wtd p50, 95.1-98.0 %
        # curve coverage) at the SHARED delivered-gas anchor. Both constants
        # resolve HERE from the registries so the bundle's run_config.json
        # records the values (rule 25); an ISO without a derived level is a hard
        # error, never a fallback (rule 24). The ANCHOR is the SAME registry the
        # gas margin form uses — one identification point for the whole gas
        # offer surface (rule 19), so it resolves whether or not
        # gas_offer_margin is also armed.
        # Identification: scripts/data/derive_cc_committed_offer_margin.py.
        from market_sim.config.constants import (
            CC_COMMITTED_OFFER_LEVEL_BY_ISO,
            GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        )

        if (
            iso not in CC_COMMITTED_OFFER_LEVEL_BY_ISO
            or iso not in GAS_OFFER_MARGIN_ANCHOR_BY_ISO
        ):
            raise SystemExit(
                f"--cc-committed-offer-margin: no derived CC committed level / "
                f"delivered-gas anchor for {iso} in "
                "constants.CC_COMMITTED_OFFER_LEVEL_BY_ISO / "
                "GAS_OFFER_MARGIN_ANCHOR_BY_ISO — run "
                "scripts/data/derive_cc_committed_offer_margin.py and register "
                "the level (rule 24: levels never cross ISO boundaries)"
            )
        config = config.with_overrides(
            cc_committed_offer_margin=True,
            cc_committed_offer_level=CC_COMMITTED_OFFER_LEVEL_BY_ISO[iso],
            gas_offer_margin_anchor=GAS_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
        )
    if coal_peak_offer_margin:
        # Coal `_peak`-tranche gas-anchored offer margin (ERCOT-140, the coal
        # offer-curve UPPER-TAIL successor ERCOT-123 §7.2 chartered): the
        # CAMPD coal _peak tranche is repriced from its band-multiplier ×
        # sigmoid composition to the measured top-decile level at the SHARED
        # gas anchor, with the corpus's own measured GAS slope (the top
        # tracks gas — gas-parity opportunity pricing — not coal fuel). All
        # constants resolve HERE from the registries so the bundle's
        # run_config.json records the values (rule 25); an ISO without a
        # derived pair is a hard error, never a fallback (rule 24). The
        # ANCHOR is the SAME registry the gas margin forms use — one gas
        # identification point for the whole offer surface (rule 19), so it
        # resolves whether or not the gas mechanisms are also armed.
        # Identification: scripts/data/derive_coal_peak_offer_margin.py.
        from market_sim.config.constants import (
            COAL_PEAK_OFFER_GAS_HR_BY_ISO,
            COAL_PEAK_OFFER_LEVEL_BY_ISO,
            GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
        )

        if (
            iso not in COAL_PEAK_OFFER_LEVEL_BY_ISO
            or iso not in COAL_PEAK_OFFER_GAS_HR_BY_ISO
            or iso not in GAS_OFFER_MARGIN_ANCHOR_BY_ISO
        ):
            raise SystemExit(
                f"--coal-peak-offer-margin: no derived coal peak level / gas "
                f"slope / delivered-gas anchor for {iso} in "
                "constants.COAL_PEAK_OFFER_LEVEL_BY_ISO / "
                "COAL_PEAK_OFFER_GAS_HR_BY_ISO / GAS_OFFER_MARGIN_ANCHOR_BY_ISO "
                "— run scripts/data/derive_coal_peak_offer_margin.py and "
                "register the values (rule 24: levels never cross ISO "
                "boundaries)"
            )
        config = config.with_overrides(
            coal_peak_offer_margin=True,
            coal_peak_offer_level=COAL_PEAK_OFFER_LEVEL_BY_ISO[iso],
            coal_peak_offer_gas_hr=COAL_PEAK_OFFER_GAS_HR_BY_ISO[iso],
            gas_offer_margin_anchor=GAS_OFFER_MARGIN_ANCHOR_BY_ISO[iso],
        )
    # PER-YEAR refinement of the coal `_peak` LEVEL (--coal-peak-offer-yearly-
    # level; ScenarioConfig.coal_peak_offer_yearly_level, ercot-192 — matrix
    # §5.1 item 13, owner signature B1 on DECISION-CARD-ercot188 card B).
    # Refines the block above: the WIRING guard here enforces the dependency
    # (the margin flag is a solve kwarg, so a construction-time config check
    # cannot see it — the coal_perplant_offer_yearly precedent). The FULL
    # year-keyed table resolves into the config (rule 25: run_config records
    # what the solve used, year-invariantly); the consumer indexes it by the
    # solve year, and a year absent from the table (2024/2025 — it carries only
    # 2023) falls through to the static level unchanged (precommit G-BIT).
    # Identification: scripts/probes/ercot192_coal_limbs_bound_phase0.py.
    if coal_peak_offer_yearly_level:
        from market_sim.config.constants import (
            COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO,
        )

        if not coal_peak_offer_margin:
            raise SystemExit(
                "--coal-peak-offer-yearly-level requires "
                "--coal-peak-offer-margin: the year table refines that "
                "mechanism's level and has no meaning without it (rule 24)"
            )
        if iso not in COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO:
            raise SystemExit(
                f"--coal-peak-offer-yearly-level: no derived year-keyed coal "
                f"peak level for {iso} in "
                "constants.COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO — derive it "
                "from that ISO's own SCED disclosure and register it (rule 25: "
                "levels never cross ISO boundaries)"
            )
        config = config.with_overrides(
            coal_peak_offer_yearly_level=True,
            coal_peak_offer_level_yearly=COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO[iso],
        )
        logger.info(
            "%s coal peak-tranche YEAR level (ercot-192): years %s; solve year "
            "%d is %s the table",
            iso,
            sorted(COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO[iso]),
            year,
            (
                "IN"
                if year in COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO[iso]
                else "NOT in (static fall-through)"
            ),
        )
    if nysdec_peaker_rule_availability:
        # NYSDEC 6 NYCRR 227-3 peaker-rule availability overlay: curated
        # unit-level ozone-season compliance windows (Gold Book IV-3..IV-6),
        # availability only, never an offer/price change (rule #12 class of
        # the CAMPD outage windows).
        config = config.with_overrides(nysdec_peaker_rule_availability=True)
    if nyiso_solar_market_generator_basis:
        # NYISO front-of-meter solar capacity basis (rule 14 [R-ACCURATE]): the
        # EIA-860 utility-scale NY population includes ~2 GW of distribution-
        # connected community solar already netted out of the EIA-930 NYIS
        # demand series used as load, so carrying it as grid supply double-
        # counts it. Swap the capacity basis to NYISO's own Gold Book Table
        # III-2a market-generator registry. Input only, never an offer/price
        # change (rule 13 class of the CAMPD outage windows).
        config = config.with_overrides(nyiso_solar_market_generator_basis=True)
    if oil_primary_bin_fuel:
        # Measured EIA-860 oil-primary fuel correction (plant-registry screen
        # unioned with the generator-level Energy-Source-1 majority screen);
        # CLI-explicit counterpart of the legacy ERCOT_OIL_PRIMARY env gate.
        config = config.with_overrides(oil_primary_bin_fuel=True)
    if st_gas_intermediate:
        # MISO intermediate gas-steam structure (one consolidated lever, default
        # OFF → prior keepers / other ISOs byte-identical). The legacy gas-steam
        # fleet (Harding Street, Ames, Nine Mile Pt, Lewis Creek, Sabine, ...)
        # runs intermediate-duty, not as peakers, but inherits ERCOT-fitted steam
        # parameters that under-run it (Moselle / Lewis Creek) and let it cycle
        # with peaker agility. Three coupled corrections, each well-grounded:
        #  1. route the measured median-CF cohort (fleet.st_gas_intermediate_plants)
        #     to the flatter ST_GAS_INTERMEDIATE offer curve so its sustained
        #     energy clears;
        #  2. the ST_GAS startup cost + min-run feed the P1 bid markup so a
        #     stop-start costs more than idling (steam drags, not cycles);
        #  3. replace the ERCOT-fitted ST_GAS WEFOR base (0.21, >2x every other
        #     thermal class) with a realistic NERC-GADS gas-steam EFOR, lifting
        #     the implicit availability crush off MISO's net-summer-rated steam.
        # NOTE: the net-load reliability-drag floor (the Little Gypsy / River
        # load-pocket weather-dependent must-run) is deliberately NOT enabled
        # here. Its ScenarioConfig coefficients are ERCOT-derived and SATURATE at
        # the 0.34 cap across all of MISO's larger net-load range (60-110 GW),
        # degenerating into a flat 34% must-run rather than the weather-responsive
        # curve intended — borrowed coefficients, not a MISO mechanism. It needs
        # a MISO-specific regression (MISO overnight ST_GAS CAMPD CF vs MISO
        # net-load), mirroring the ERCOT/NYISO/CAISO per-ISO floor derivations,
        # before it can be a keeper lever. Tracked as the immediate follow-up;
        # enable per-run via --gas-st-netload-drag once MISO coefficients exist.
        config = config.with_overrides(
            st_gas_intermediate_split=True,
            gas_st_startup_cost=True,
            gas_st_wefor_base_override=0.10,
        )
    if st_gas_intermediate_cf_threshold is not None:
        config = config.with_overrides(
            st_gas_intermediate_cf_threshold=float(st_gas_intermediate_cf_threshold)
        )
    # Tri-state overrides: None = keep the per-ISO base default from
    # backcast_config (CAISO defaults the RA floor + negative offers ON, the
    # validated keeper); an explicit True/False from the CLI overrides it (so a
    # no-floor baseline probe is --no-caiso-gas-commitment-floor).
    if negative_renewable_offers is not None:
        config = config.with_overrides(
            negative_renewable_offers=negative_renewable_offers
        )
    if caiso_gas_commitment_floor is not None:
        config = config.with_overrides(
            caiso_gas_commitment_floor=caiso_gas_commitment_floor
        )
    if caiso_gas_floor_frac is not None:
        config = config.with_overrides(caiso_gas_floor_frac=caiso_gas_floor_frac)
    if caiso_ra_mustoffer is not None:
        config = config.with_overrides(caiso_ra_mustoffer=caiso_ra_mustoffer)
    if caiso_ra_min_load_frac is not None:
        config = config.with_overrides(caiso_ra_min_load_frac=caiso_ra_min_load_frac)
    if caiso_ra_startup_bridge is not None:
        config = config.with_overrides(caiso_ra_startup_bridge=caiso_ra_startup_bridge)
    if ercot_gas_commitment_bridge is not None:
        config = config.with_overrides(
            ercot_gas_commitment_bridge=ercot_gas_commitment_bridge
        )
    if ercot_commitment_posture is not None:
        config = config.with_overrides(
            ercot_commitment_posture=ercot_commitment_posture
        )
    if ercot_commitment_posture_min_load_frac is not None:
        config = config.with_overrides(
            ercot_commitment_posture_min_load_frac=(
                ercot_commitment_posture_min_load_frac
            )
        )
    if ercot_gas_bridge_min_load_frac is not None:
        config = config.with_overrides(
            ercot_gas_bridge_min_load_frac=ercot_gas_bridge_min_load_frac
        )
    if ercot_gas_bridge_startup is not None:
        config = config.with_overrides(
            ercot_gas_bridge_startup=ercot_gas_bridge_startup
        )
    if ercot_gas_bridge_da_horizon is not None:
        config = config.with_overrides(
            ercot_gas_bridge_da_horizon=ercot_gas_bridge_da_horizon
        )
    if ercot_gas_bridge_online_hours is not None:
        config = config.with_overrides(
            ercot_gas_bridge_online_hours=ercot_gas_bridge_online_hours
        )
    if carry_operating_mothballs is not None:
        config = config.with_overrides(
            carry_operating_mothballs=carry_operating_mothballs
        )
    if caiso_ra_bridge_decommit is not None:
        config = config.with_overrides(
            caiso_ra_bridge_decommit=caiso_ra_bridge_decommit
        )
    if reliability_floor is not None:
        config = config.with_overrides(reliability_floor=reliability_floor)
    # nyiso-140 per-plant floor-membership exclusion. Restored 2026-08-17: two
    # sessions independently repaired the duplicate-argument SyntaxError this
    # parameter arrived with (6bb3a22 and 19f77d4), and each deleted one of the
    # two duplicate PAIRS -- so both override blocks were removed while the
    # parameter survived, leaving it silently ignored. Default None = leave the
    # config's own value, so the arming semantics are unchanged.
    # De-duplicated 2026-08-17 (miso-162): the restore itself then landed TWICE
    # -- PR #4054 and the miso-160 merge resolution repaired it independently,
    # the same over-repair pattern one cycle later. The second copy was
    # idempotent (same value re-applied), so this removal is a byte no-op for
    # every solve; it exists so the next reader does not repair a third time.
    if reliability_floor_plant_exclusions is not None:
        config = config.with_overrides(
            reliability_floor_plant_exclusions=reliability_floor_plant_exclusions
        )
    if reliability_floor_overrides is not None:
        config = config.with_overrides(
            reliability_floor_overrides=reliability_floor_overrides
        )
    if scarcity_price_overlay is not None:
        config = config.with_overrides(
            scarcity_pricing_enabled=scarcity_price_overlay,
            scarcity_price_overlay=scarcity_price_overlay,
        )
    if caiso_scarcity_pricing is not None:
        config = config.with_overrides(
            scarcity_pricing_enabled=True,
            caiso_scarcity_pricing=caiso_scarcity_pricing,
        )
    if caiso_lcr_commitment_credit is not None:
        config = config.with_overrides(
            caiso_lcr_commitment_credit=caiso_lcr_commitment_credit,
        )
    if caiso_solar_deliverability is not None:
        config = config.with_overrides(
            caiso_solar_deliverability=caiso_solar_deliverability
        )
    if caiso_solar_deliverability_k is not None:
        config = config.with_overrides(
            caiso_solar_deliverability_k=caiso_solar_deliverability_k
        )
    if caiso_solar_endogenous_spill is not None:
        config = config.with_overrides(
            caiso_solar_endogenous_spill=caiso_solar_endogenous_spill
        )
    if caiso_solar_cap_at_delivered is not None:
        config = config.with_overrides(
            caiso_solar_cap_at_delivered=caiso_solar_cap_at_delivered
        )
    if neiso_gas_coldsnap_derate is not None:
        config = config.with_overrides(
            neiso_gas_coldsnap_derate=neiso_gas_coldsnap_derate
        )
    if neiso_coldsnap_derate_dualfuel_unswitched is not None:
        config = config.with_overrides(
            neiso_coldsnap_derate_dualfuel_unswitched=neiso_coldsnap_derate_dualfuel_unswitched
        )
    if neiso_oil_burn_budget is not None:
        config = config.with_overrides(neiso_oil_burn_budget=neiso_oil_burn_budget)
    if neiso_winter_fuel_inventory is not None:
        config = config.with_overrides(
            neiso_winter_fuel_inventory=neiso_winter_fuel_inventory
        )
    if coal_fuel_inventory is not None:
        config = config.with_overrides(coal_fuel_inventory=coal_fuel_inventory)
    if neiso_winter_fuel_start_fill_bbl is not None:
        config = config.with_overrides(
            neiso_winter_fuel_start_fill_bbl=neiso_winter_fuel_start_fill_bbl
        )
    if neiso_winter_fuel_mustrun is not None:
        config = config.with_overrides(
            neiso_winter_fuel_mustrun=neiso_winter_fuel_mustrun
        )
    if caiso_import_hub_prices is not None:
        config = config.with_overrides(caiso_import_hub_prices=caiso_import_hub_prices)
    if caiso_import_gas_coupling is not None:
        config = config.with_overrides(
            caiso_import_gas_coupling=caiso_import_gas_coupling
        )
    if caiso_import_solar_shape is not None:
        config = config.with_overrides(
            caiso_import_solar_shape=caiso_import_solar_shape
        )
    if caiso_per_hub_intertie is not None:
        config = config.with_overrides(caiso_per_hub_intertie=caiso_per_hub_intertie)
    if caiso_perhub_firm_base is not None:
        config = config.with_overrides(caiso_perhub_firm_base=caiso_perhub_firm_base)
    if caiso_corridor_flow_limit is not None:
        config = config.with_overrides(
            caiso_corridor_flow_limit=caiso_corridor_flow_limit
        )
    if caiso_intertie_reference_price is not None:
        config = config.with_overrides(
            caiso_intertie_reference_price=caiso_intertie_reference_price
        )
    if caiso_corridor_atc_forward is not None:
        config = config.with_overrides(
            caiso_corridor_atc_forward=caiso_corridor_atc_forward
        )
    if caiso_reference_price_seam is not None:
        config = config.with_overrides(
            caiso_reference_price_seam=caiso_reference_price_seam
        )
    if caiso_per_year_import_caps is not None:
        config = config.with_overrides(
            caiso_per_year_import_caps=caiso_per_year_import_caps
        )
    if caiso_asymmetric_path_ratings is not None:
        config = config.with_overrides(
            caiso_asymmetric_path_ratings=caiso_asymmetric_path_ratings
        )
    if caiso_zonal_loss_surface is not None:
        config = config.with_overrides(
            caiso_zonal_loss_surface=caiso_zonal_loss_surface
        )
    if capacity_deliverability_limits is not None:
        config = config.with_overrides(
            capacity_deliverability_limits=capacity_deliverability_limits
        )
    if unit_outage_lp_capacity_basis is not None:
        config = config.with_overrides(
            unit_outage_lp_capacity_basis=unit_outage_lp_capacity_basis
        )
    if unit_outage_mixed_gas_routing is not None:
        config = config.with_overrides(
            unit_outage_mixed_gas_routing=unit_outage_mixed_gas_routing
        )
    if unit_outage_st_capacity_basis is not None:
        # miso-201: the STEAM-side capacity-basis alignment. Sibling of the two
        # overrides above and scoped exactly like them.
        config = config.with_overrides(
            unit_outage_st_capacity_basis=unit_outage_st_capacity_basis
        )
    if unit_outage_per_unit_clip is not None:
        # miso-202: the one-unit-cannot-be-more-than-100 %-out clip. THIS is the
        # SOLVE path for the flag (run_calibration_full's _recorded_config only
        # records it), so an override missing here would solve the control twice.
        config = config.with_overrides(
            unit_outage_per_unit_clip=unit_outage_per_unit_clip
        )
    if unit_outage_dispatched_bin_denominator is not None:
        # miso-266: the DISPATCHED-bin derate denominator. THIS is the SOLVE
        # path for the flag (run_calibration_full's _recorded_config only
        # records it), so an override missing here would solve the ARM as the
        # CONTROL — the miso-265 trap, where two registered outage tunables
        # turned out to have no run_year plumbing at all (rule 24 [R-REGISTRY]).
        config = config.with_overrides(
            unit_outage_dispatched_bin_denominator=unit_outage_dispatched_bin_denominator
        )
    if unit_outage_window_hour_grain is not None:
        # nyiso-229: the DETECTED-HOUR outage window grain. THIS is the SOLVE
        # path for the flag (run_calibration_full's _recorded_config only
        # records it), so an override missing here would solve the ARM as the
        # CONTROL — and, because run_year does not take **kwargs, omitting the
        # PARAMETER above raises TypeError before the LP is built rather than
        # silently no-opping. The nyiso-229 screen's first two shards died on
        # exactly that, which is the loud half of this failure mode doing its job.
        config = config.with_overrides(
            unit_outage_window_hour_grain=unit_outage_window_hour_grain
        )
    if unit_outage_short_windows_gas is not None:
        # pjm-d4-4: the GAS-side sub-5-day outage scope. THIS is the SOLVE path
        # for the flag (run_calibration_full's _recorded_config only records
        # it), so an override missing here would solve the control twice.
        config = config.with_overrides(
            unit_outage_short_windows_gas=unit_outage_short_windows_gas
        )
    if unit_outage_window_hour_grain is not None:
        # nyiso-229: the DETECTED-hour grain of the merit-guarded per-unit
        # outage windows. THIS is the SOLVE path for the flag (as for every
        # sibling above, run_calibration_full's _recorded_config only records
        # it), so an override missing here would solve the control twice.
        #
        # RESTORED 2026-09-12 (lane SPP-36, stop-the-line). The introducing
        # commit 3497a1d8 added this kwarg to `solve_and_persist`'s
        # UNCONDITIONAL run_year(...) call in run_calibration_full.py and to
        # ScenarioConfig, but never to `run_year` here — so EVERY
        # solve_and_persist invocation, for every ISO and every year, raised
        # `TypeError: run_year() got an unexpected keyword argument
        # 'unit_outage_window_hour_grain'` before any LP work. Both production
        # entry points were dead (run_calibration_full.main and
        # replay_keeper.main). Found by SPP-36 shard 1, which stopped and
        # reported instead of patching; see
        # docs/handoffs/SHARDREPORT-spp36-2023.md and
        # docs/handoffs/FINDING-spp-36-runyear-kwarg-2026-09-12.md.
        config = config.with_overrides(
            unit_outage_window_hour_grain=unit_outage_window_hour_grain
        )
    if campd_per_unit_attribution is not None:
        # nyiso-176: ONE gate over BOTH CAMPD-derived solve inputs (the
        # thermal-tranche artifact and the unit-outage extract), which must
        # move together — a tranche row's statistics are computed over an
        # outage-derated denominator (rule 19 [R-ONE-MECH]).
        config = config.with_overrides(
            campd_per_unit_attribution=campd_per_unit_attribution
        )
    if campd_outage_merit_order_guard is not None:
        # nyiso-177: the SECOND half of the same selector — the economic-lay-up
        # guard rides both CAMPD companions together for the same rule 19
        # [R-ONE-MECH] reason, and is inert without the gate above.
        config = config.with_overrides(
            campd_outage_merit_order_guard=campd_outage_merit_order_guard
        )
    if netload_drag_layup_window_mask is not None:
        # ercot-256: the net-load drag floors' measured lay-up WINDOW MASK. It
        # consumes the very extract the guard above writes, so the two ride the
        # same replay path; inert (an empty share dict) when no extract exists
        # for the ISO/year, and refused outright in forecast mode by
        # _BACKCAST_ONLY_OVERLAY_FIELDS (rule 13 [R-MEASURED]).
        config = config.with_overrides(
            netload_drag_layup_window_mask=netload_drag_layup_window_mask
        )
    if vre_curtailment_oversupply_allocation is not None:
        # SPP-51c: the hourly ALLOCATION of the frozen reference-rate
        # curtailment energy. One field, one seam (the renewable bound), and the
        # annual potential is identical either way — so it rides this replay
        # path as a single-field A/B arm. Forward-native (rule 13), so it is NOT
        # in _BACKCAST_ONLY_OVERLAY_FIELDS.
        config = config.with_overrides(
            vre_curtailment_oversupply_allocation=vre_curtailment_oversupply_allocation
        )
    if spp_curtailment_ceiling is not None:
        # SPP-58: the SPP wind curtailment CEILING. One field, one seam (the
        # wind CF upper bound), and it SUPERSEDES the oversupply allocation in
        # data.renewables rather than stacking on it (rule 19 [R-ONE-MECH]) --
        # so it rides this replay path as a single-field A/B arm against a
        # keeper recipe that still carries the allocation flag. Forward-native
        # (rule 13, forecast leg in runner.py), so it is NOT in
        # _BACKCAST_ONLY_OVERLAY_FIELDS.
        config = config.with_overrides(spp_curtailment_ceiling=spp_curtailment_ceiling)
    if spp_curtail_depth_wind is not None:
        config = config.with_overrides(
            spp_curtail_depth_wind=float(spp_curtail_depth_wind)
        )
    if netload_drag_merit_allocation is not None:
        # ercot-259: the net-load drag mandate's MERIT ALLOCATION. Same driver,
        # same rows, same hourly aggregate and the same mechanism id — only the
        # distribution across tranches changes (rule 19 [R-ONE-MECH]), so it
        # rides this same replay path as a single-field A/B arm. Forward-native,
        # so it is NOT in _BACKCAST_ONLY_OVERLAY_FIELDS.
        config = config.with_overrides(
            netload_drag_merit_allocation=netload_drag_merit_allocation
        )
    if netload_drag_min_run_persistence is not None:
        # pjm-177: the net-load drag mandate's HOUR ELIGIBILITY. Same driver,
        # same rows, same coefficients and the same mechanism id — only WHICH
        # HOURS the mandate lands in changes (rule 19 [R-ONE-MECH]), so it rides
        # this same replay path as a single-field A/B arm. Forward-native, so it
        # is NOT in _BACKCAST_ONLY_OVERLAY_FIELDS.
        config = config.with_overrides(
            netload_drag_min_run_persistence=netload_drag_min_run_persistence
        )
    if cc_winter_capability_basis is not None:
        config = config.with_overrides(
            cc_winter_capability_basis=cc_winter_capability_basis
        )
    if ramp_limits is not None:
        config = config.with_overrides(ramp_limits=ramp_limits)
    if local_capacity_constraints is not None:
        config = config.with_overrides(
            local_capacity_constraints=local_capacity_constraints
        )
    if nyiso_local_selfsupply is not None:
        config = config.with_overrides(nyiso_local_selfsupply=nyiso_local_selfsupply)
    if nyiso_scr_edrp is not None:
        config = config.with_overrides(nyiso_scr_edrp=nyiso_scr_edrp)
    if nyiso_scr_edrp_strike is not None:
        config = config.with_overrides(nyiso_scr_edrp_strike=nyiso_scr_edrp_strike)
    if nyiso_firm_imports is not None:
        config = config.with_overrides(nyiso_firm_imports=nyiso_firm_imports)
    if nyiso_import_reconciliation is not None:
        config = config.with_overrides(
            nyiso_import_reconciliation=nyiso_import_reconciliation
        )
    if nyiso_import_hub_prices is not None:
        config = config.with_overrides(nyiso_import_hub_prices=nyiso_import_hub_prices)
    if nyiso_iroquois_winter_spread is not None:
        config = config.with_overrides(
            nyiso_iroquois_winter_spread=nyiso_iroquois_winter_spread
        )
    if nyiso_synchronised_reserve is not None:
        config = config.with_overrides(
            nyiso_synchronised_reserve=nyiso_synchronised_reserve
        )
    if nyiso_li_locational_reserve is not None:
        config = config.with_overrides(
            nyiso_li_locational_reserve=nyiso_li_locational_reserve
        )
    if nyiso_incity_commitment_obligation is not None:
        config = config.with_overrides(
            nyiso_incity_commitment_obligation=nyiso_incity_commitment_obligation
        )
    if nyiso_east_reserve_families is not None:
        config = config.with_overrides(
            nyiso_east_reserve_families=nyiso_east_reserve_families
        )
    if nyiso_gas_commitment_bridge is not None:
        config = config.with_overrides(
            nyiso_gas_commitment_bridge=nyiso_gas_commitment_bridge
        )
    if soco_gas_st_campaign_commitment is not None:
        config = config.with_overrides(
            soco_gas_st_campaign_commitment=soco_gas_st_campaign_commitment
        )
    if spp_gas_commitment_bridge is not None:
        config = config.with_overrides(
            spp_gas_commitment_bridge=spp_gas_commitment_bridge
        )
    if miso_coal_night_floor is not None:
        config = config.with_overrides(miso_coal_night_floor=miso_coal_night_floor)
    if nyiso_gas_bridge_cc_min_load_frac is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_cc_min_load_frac=nyiso_gas_bridge_cc_min_load_frac
        )
    if nyiso_gas_bridge_st_min_load_frac is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_st_min_load_frac=nyiso_gas_bridge_st_min_load_frac
        )
    if nyiso_gas_bridge_startup is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_startup=nyiso_gas_bridge_startup
        )
    if nyiso_gas_bridge_da_horizon is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_da_horizon=nyiso_gas_bridge_da_horizon
        )
    if nyiso_gas_bridge_min_run is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_min_run=nyiso_gas_bridge_min_run
        )
    if nyiso_gas_bridge_plant_exclusions is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_plant_exclusions=nyiso_gas_bridge_plant_exclusions
        )
    if nyiso_gas_bridge_reserve_duty_exclusions is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_reserve_duty_exclusions=(
                nyiso_gas_bridge_reserve_duty_exclusions
            )
        )
    if nyiso_gas_bridge_plant_min_run is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_plant_min_run=nyiso_gas_bridge_plant_min_run
        )
    if nyiso_gas_bridge_online_hours is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_online_hours=nyiso_gas_bridge_online_hours
        )
    if nyiso_gas_bridge_state_floor_min_run is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_state_floor_min_run=nyiso_gas_bridge_state_floor_min_run
        )
    if nyiso_gas_bridge_startup_aware is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_startup_aware=nyiso_gas_bridge_startup_aware
        )
    if nyiso_chp_btm_measured is not None:
        config = config.with_overrides(nyiso_chp_btm_measured=nyiso_chp_btm_measured)
    if cc_reserve_duty_split is not None:
        config = config.with_overrides(cc_reserve_duty_split=cc_reserve_duty_split)
    if chp_layup_duty_split is not None:
        config = config.with_overrides(chp_layup_duty_split=chp_layup_duty_split)
    if chp_layup_duty_curve is not None:
        config = config.with_overrides(chp_layup_duty_curve=chp_layup_duty_curve)
    if egrid_identity_heat_rates is not None:
        config = config.with_overrides(
            egrid_identity_heat_rates=egrid_identity_heat_rates
        )
    if measured_ct_heat_rates is not None:
        config = config.with_overrides(measured_ct_heat_rates=measured_ct_heat_rates)
    if measured_coal_heat_rates is not None:
        config = config.with_overrides(
            measured_coal_heat_rates=measured_coal_heat_rates
        )
    if measured_st_heat_rates is not None:
        config = config.with_overrides(measured_st_heat_rates=measured_st_heat_rates)
    if egrid_family_heat_rates is not None:
        config = config.with_overrides(egrid_family_heat_rates=egrid_family_heat_rates)
    if egrid_steam_collapse_heat_rates is not None:
        config = config.with_overrides(
            egrid_steam_collapse_heat_rates=egrid_steam_collapse_heat_rates
        )
    if nyiso_gas_bridge_cc_min_run_hours is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_cc_min_run_hours=nyiso_gas_bridge_cc_min_run_hours
        )
    if nyiso_gas_bridge_st_min_run_hours is not None:
        config = config.with_overrides(
            nyiso_gas_bridge_st_min_run_hours=nyiso_gas_bridge_st_min_run_hours
        )
    if nyiso_spin_reserve_online is not None:
        config = config.with_overrides(
            nyiso_spin_reserve_online=nyiso_spin_reserve_online
        )
    if nyiso_spin_headroom_frac is not None:
        config = config.with_overrides(
            nyiso_spin_headroom_frac=nyiso_spin_headroom_frac
        )
    if nyiso_dynamic_reserve_requirements is not None:
        config = config.with_overrides(
            nyiso_dynamic_reserve_requirements=nyiso_dynamic_reserve_requirements
        )
    if nyiso_hydro_reserve_eligible is not None:
        config = config.with_overrides(
            nyiso_hydro_reserve_eligible=nyiso_hydro_reserve_eligible
        )
    if nyiso_scr_edrp_reserve_eligible is not None:
        config = config.with_overrides(
            nyiso_scr_edrp_reserve_eligible=nyiso_scr_edrp_reserve_eligible
        )
    if neiso_dynamic_reserve_requirements is not None:
        config = config.with_overrides(
            neiso_dynamic_reserve_requirements=neiso_dynamic_reserve_requirements
        )
    if miso_firm_imports is not None:
        config = config.with_overrides(miso_firm_imports=miso_firm_imports)
    if miso_seam_flow_limit:
        config = config.with_overrides(miso_seam_flow_limit=True)
    if miso_seam_flow_percentile is not None:
        # Round-2 import-lift: raise the seam deliverability percentile (p90 ->
        # e.g. p95) so the priced seam clears more import in tight hours. Only
        # bites with --miso-seam-flow-limit; still a measured-duration ceiling.
        config = config.with_overrides(
            miso_seam_flow_percentile=float(miso_seam_flow_percentile)
        )
    if miso_seam_export_limit:
        config = config.with_overrides(miso_seam_export_limit=True)
    if miso_seam_envelope_merit_cap:
        config = config.with_overrides(miso_seam_envelope_merit_cap=True)
    if miso_seam_envelope_hour_ending_key:
        config = config.with_overrides(miso_seam_envelope_hour_ending_key=True)
    if miso_import_sil_measured_envelope:
        config = config.with_overrides(miso_import_sil_measured_envelope=True)
    if nyiso_seam_deliverability_envelope:
        config = config.with_overrides(nyiso_seam_deliverability_envelope=True)
    if nyiso_seam_par_attribution:
        config = config.with_overrides(nyiso_seam_par_attribution=True)
    if pjm_seam_flow_limit:
        config = config.with_overrides(pjm_seam_flow_limit=True)
    if pjm_seam_flow_percentile is not None:
        config = config.with_overrides(
            pjm_seam_flow_percentile=float(pjm_seam_flow_percentile)
        )
    if pjm_seam_export_limit:
        config = config.with_overrides(pjm_seam_export_limit=True)
    if pjm_seam_measured_ladder:
        config = config.with_overrides(pjm_seam_measured_ladder=True)
    if pjm_seam_neighbour_hourly_ladder:
        config = config.with_overrides(pjm_seam_neighbour_hourly_ladder=True)
    if miso_pjm_border_anchor:
        config = config.with_overrides(miso_pjm_border_anchor=True)
    if miso_cc_coal_rebalance and iso.upper() == "MISO":
        # Raise the MISO CC_REGULAR / COAL_BIT offer curve so the marginal CC /
        # coal-bit MWh sits above the priced-import hurdle (and the under-running
        # CT_PEAKER / ST_GAS), correcting the cheap-domestic-fill-eats-imports
        # miss. ISO-gated (other ISOs / forecasts byte-identical); applied as a
        # deep-merge offer-curve override on top of the calibrated MISO curve.
        rebalanced = _deep_merge_offer_curve(
            config.offer_curve_by_group, _MISO_CC_COAL_REBALANCE
        )
        config = config.with_overrides(
            offer_curve_by_group=rebalanced, miso_cc_coal_rebalance=True
        )
    if miso_firm_import_floor:
        # Firm (must-flow) import floor on the reference-price seam — forces the
        # measured near-firm PJM/IESO net-import base so the seam stops wrongly
        # net-exporting (fixes the import shortfall + 2025 energy-balance overshoot
        # by displacing the over-running domestic coal/CC). Requires the priced
        # interface; MISO-only (only the PJM seam carries a floor).
        config = config.with_overrides(miso_firm_import_floor=True)
    if miso_pjm_lmp_import_pricing:
        config = config.with_overrides(miso_pjm_lmp_import_pricing=True)
    if miso_seam_measured_ladder:
        config = config.with_overrides(miso_seam_measured_ladder=True)
    if gas_hub_basis_overlay is not None:
        config = config.with_overrides(gas_hub_basis_overlay=gas_hub_basis_overlay)
    # Per-run PRB passthrough sigmoid floor/ceiling tune (run_calibration_full
    # --prb-* flags); None entries leave the ScenarioConfig default in place.
    if prb_overrides:
        # ERCOT-65 discovery: this generic channel is applied LAST, so a key
        # it carries stomps any explicit tri-state kwarg handled above (the
        # keeper-lineage metas carry ercot_wtx_curtailment_driver=true here
        # while the meta-writer's coerced top-level ``False`` rode the
        # kwarg — the live solve has ALWAYS taken the prb value). Surface the
        # conflict loudly instead of silently double-governing (rule 24).
        for _k in (
            "ercot_wtx_curtailment_driver",
            "ercot_wtx_curtail_depth_wind",
            "ercot_wtx_curtail_depth_solar",
        ):
            _prb_v = prb_overrides.get(_k)
            if (
                _prb_v is not None
                and _k in _wtx_overrides
                and (_prb_v != _wtx_overrides[_k])
            ):
                logger.warning(
                    "%s: explicit kwarg %r is stomped by prb_overrides %r "
                    "(this channel applies last) — the LP solves with the "
                    "prb value. Pass the driver through ONE channel.",
                    _k,
                    _wtx_overrides[_k],
                    _prb_v,
                )
        config = config.with_overrides(
            **{k: v for k, v in prb_overrides.items() if v is not None}
        )
    # nyiso-199 FAIL-LOUD GUARD (rule 24 [R-REGISTRY]). This flag's consumer
    # lives inside ``backcast_config`` (line ~861), which has ALREADY RUN by the
    # time the generic ``prb_overrides`` channel applies here — so a run that
    # arms it through prb ALONE would carry ``nyiso_ct_peaker_bands_measured =
    # True`` in its recorded run_config while the LP solved the FITTED bands: a
    # silent no-op advertising a mechanism that never ran, which is exactly the
    # caiso-157 defect class this file's own solve-path guard was written for.
    # ``replay_keeper --set`` routes through both channels, and the CLI flag
    # threads the named kwarg, so the supported paths are fine; this catches the
    # unsupported one loudly instead of producing a bundle that lies.
    if getattr(config, "nyiso_ct_peaker_bands_measured", False):
        _ny_ct = (config.offer_curve_by_group or {}).get("CT_PEAKER") or {}
        _unapplied = [
            b
            for b in ("committed", "econ_low", "econ_high")
            if f"phys_{b}" in _ny_ct
            and abs(float(_ny_ct.get(b, 0.0)) - float(_ny_ct[f"phys_{b}"])) > 1e-9
        ]
        if _unapplied:
            raise ValueError(
                "nyiso_ct_peaker_bands_measured is True on the resolved config "
                f"but band(s) {', '.join(_unapplied)} still carry the fitted "
                "multiplier — the flag reached ScenarioConfig AFTER its "
                "backcast_config consumer ran (the generic prb_overrides "
                "channel alone). Pass it as the named run_year kwarg, via "
                "--nyiso-ct-peaker-bands-measured, or via replay_keeper --set "
                "(which routes both channels). A silent no-op here would "
                "advertise a mechanism the LP never solved (rule 24)."
            )
    # nyiso-241: the identical fail-loud guard for the COMMITTED-ONLY limb, for
    # the identical reason (rule 24 [R-REGISTRY]) — a run that arms it through
    # the generic ``prb_overrides`` channel alone would record the flag while
    # the LP solved the fitted 1.35.
    if getattr(config, "nyiso_ct_peaker_committed_measured", False):
        _ny_ctc = (config.offer_curve_by_group or {}).get("CT_PEAKER") or {}
        if "phys_committed" in _ny_ctc and (
            abs(float(_ny_ctc.get("committed", 0.0)) - float(_ny_ctc["phys_committed"]))
            > 1e-9
        ):
            raise ValueError(
                "nyiso_ct_peaker_committed_measured is True on the resolved "
                "config but the `committed` band still carries the fitted "
                "multiplier — the flag reached ScenarioConfig AFTER its "
                "backcast_config consumer ran (the generic prb_overrides "
                "channel alone). Pass it as the named run_year kwarg, via "
                "--nyiso-ct-peaker-committed-measured, or via replay_keeper "
                "--set (which routes both channels). A silent no-op here would "
                "advertise a mechanism the LP never solved (rule 24)."
            )
    # nyiso-232: the identical guard for the ST_GAS econ de-leak, for the
    # identical reason. ``prb_overrides`` is applied ABOVE, i.e. AFTER
    # ``backcast_config`` has already resolved the offer curve, so a run that
    # arms this field through that channel ALONE would record
    # ``nyiso_st_gas_econ_bands_deleaked = True`` beside the LEAKED bands the LP
    # actually solved. Fail loudly rather than ship a bundle that lies (rule 24
    # [R-REGISTRY]).
    if getattr(config, "nyiso_st_gas_econ_bands_deleaked", False):
        _ny_st = (config.offer_curve_by_group or {}).get("ST_GAS") or {}
        _unapplied = [
            b
            for b in ("econ_low", "econ_high")
            if abs(float(_ny_st.get(b, 1.0)) - 1.0) > 1e-9
        ]
        if _unapplied:
            raise ValueError(
                "nyiso_st_gas_econ_bands_deleaked is True on the resolved "
                f"config but band(s) {', '.join(_unapplied)} still carry the "
                "leaked multiplier — the flag reached ScenarioConfig AFTER its "
                "backcast_config consumer ran (the generic prb_overrides "
                "channel alone). Pass it as the named run_year kwarg or via "
                "--nyiso-st-gas-econ-bands-deleaked. A silent no-op here would "
                "advertise a mechanism the LP never solved (rule 24)."
            )
    # Gas-keyed coal passthrough sigmoids per supply chain. The bit family
    # has its own flag/overrides; the sub/lignite enables and all their
    # tuning params ride the generic prb_overrides ScenarioConfig override
    # channel (run_calibration_full --coal-{sub,lignite}-sigmoid and the
    # --{sub,lignite}-* flags). Params left at None resolve from the
    # per-ISO COAL_SIGMOID_DEFAULTS table (fuel.coal_sigmoid_params).
    if coal_bit_sigmoid:
        config = config.with_overrides(coal_bit_passthrough_sigmoid=True)
    if bit_overrides:
        config = config.with_overrides(
            **{k: v for k, v in bit_overrides.items() if v is not None}
        )
    # Marginal-coal measured-SRMC offer bound (run_calibration_full
    # --coal-econ-srmc-bound): clamp the econ*/peak coal tranches' fuel
    # passthrough to >= 1.0 so the marginal coal offer never sits below the
    # plant's measured F923 incremental delivered SRMC; the committed/
    # must-run bands keep the contracted take-or-pay discount
    # (fleet.campd_tranche_fuel_frac; ScenarioConfig.coal_econ_srmc_bound).
    if coal_econ_srmc_bound:
        config = config.with_overrides(coal_econ_srmc_bound=True)
    # Measured incremental-heat-rate floor on the COAL econ ramp
    # (run_calibration_full --coal-econ-marginal-hr-bound;
    # ScenarioConfig.coal_econ_marginal_hr_bound, ERCOT-111). Runs AFTER the
    # offer-curve overrides/deltas resolved in backcast_config and after the
    # prb_overrides ScenarioConfig application above, so it bounds the curve the
    # calibration path actually produced: each coal class's econ_low/econ_high
    # is clamped UP to the ISO's own measured CAMPD marginal (incremental) heat
    # rate for COAL. Markups above the measured basis are untouched; the
    # committed/must-run take-or-pay bands and the peak scarcity wall are out of
    # scope (rule 19). Adds no tunable — the floor is the already-committed
    # derive_campd_marginal_hr artifact (rule 13).
    # Tri-state (ercot_wtx_curtailment_driver pattern): None keeps the
    # backcast_config per-ISO default (ERCOT keeper default-ON since the
    # ercot-115 promotion); True/False force it on/off so an A/B arm can scrub
    # the floor, and so replay_keeper can pin a pre-promotion bundle to the
    # behaviour it was actually solved with. A bare `or` here would make an
    # explicit False unscrubbable once the per-ISO default turned on.
    _marginal_hr_on = (
        bool(config.coal_econ_marginal_hr_bound)
        if coal_econ_marginal_hr_bound is None
        else bool(coal_econ_marginal_hr_bound)
    )
    if _marginal_hr_on:
        from market_sim.data.coal import apply_coal_econ_marginal_hr_floor

        _curve, _lifted = apply_coal_econ_marginal_hr_floor(
            config.offer_curve_by_group, iso
        )
        config = config.with_overrides(
            coal_econ_marginal_hr_bound=True, offer_curve_by_group=_curve
        )
        if _lifted:
            logger.info(
                "%s coal econ marginal-HR floor (%d): %s",
                iso,
                len(_lifted),
                "; ".join(
                    f"{c}.{b} {before:.3f} -> {after:.3f}"
                    for c, b, before, after in _lifted
                ),
            )
        else:
            logger.info(
                "%s coal econ marginal-HR floor: no band below its measured "
                "basis — offer curve unchanged",
                iso,
            )
    elif config.coal_econ_marginal_hr_bound:
        # Explicit scrub of a per-ISO default-ON: the LP must solve WITHOUT the
        # floor, so the recorded config must say so too (rule 25 — run_config
        # records what was solved, never what was defaulted).
        config = config.with_overrides(coal_econ_marginal_hr_bound=False)
        logger.info(
            "%s coal econ marginal-HR floor: SCRUBBED by explicit False "
            "(per-ISO default was on) — offer curve unchanged",
            iso,
        )
    # ERCOT-118 EP-basis rebasis of the measured CC DAM band multipliers
    # (run_calibration_full --ercot-offer-hrmult-ep-rebasis;
    # ScenarioConfig.ercot_offer_hrmult_ep_rebasis). Runs AFTER the offer-curve
    # overrides/deltas resolved in backcast_config, after the prb_overrides
    # ScenarioConfig application, and after the conditional peak split, so it
    # rebases the curve the calibration path actually produced: the pooled
    # HH-0.50-derived CC_REGULAR/CC_CHP bands are replaced with the committed
    # PER-YEAR EP-basis artifact values, the run's offer_curve_deltas for those
    # bands re-applied on top (composition preserved — the calibrated delta
    # stays, the measured base under it moves), the conditional peak_ladder
    # rungs re-stamped at the rebased peak, and the year's EP delivered mean
    # threaded on as the rebased classes' margin_anchor (basis-consistent
    # markup pricing under gas_offer_net_revenue_margin). Adds no tunable —
    # the values are the frozen rule-23 artifact (ERCOT-117 FINDING §4.3).
    # Tri-state (the ercot-115 seam pattern): None keeps the ScenarioConfig /
    # prb_overrides-resolved value; True/False force it on/off so an A/B arm
    # can scrub it. ERCOT-scoped (rule 25). The ERCOT-119 band scope
    # (ercot_offer_hrmult_ep_rebasis_bands) rides the same tri-state pattern:
    # None keeps the config-resolved scope (whose own default None = all
    # artifact bands, the ERCOT-118 behaviour); a list restricts the rebasis
    # to the named bands, keeping the peak standing wall (and its ladder
    # rungs and window margin anchor) at the run's resolved values.
    _ep_rebasis_on = (
        bool(getattr(config, "ercot_offer_hrmult_ep_rebasis", False))
        if ercot_offer_hrmult_ep_rebasis is None
        else bool(ercot_offer_hrmult_ep_rebasis)
    )
    _ep_rebasis_bands = (
        getattr(config, "ercot_offer_hrmult_ep_rebasis_bands", None)
        if ercot_offer_hrmult_ep_rebasis_bands is None
        else list(ercot_offer_hrmult_ep_rebasis_bands)
    )
    if _ep_rebasis_on and iso.upper() == "ERCOT":
        from market_sim.data.offer_curves import apply_ercot_dam_hrmult_ep_rebasis

        _curve, _replaced, _ep_anchor = apply_ercot_dam_hrmult_ep_rebasis(
            config.offer_curve_by_group,
            year,
            offer_curve_deltas,
            bands=_ep_rebasis_bands,
        )
        config = config.with_overrides(
            ercot_offer_hrmult_ep_rebasis=True,
            ercot_offer_hrmult_ep_rebasis_bands=_ep_rebasis_bands,
            offer_curve_by_group=_curve,
        )
        logger.info(
            "ERCOT DAM offer hr-mult EP rebasis (%d): scope=%s; %d bands; %s; "
            "per-class margin anchor %.4f $/MMBtu",
            year,
            ("ALL" if _ep_rebasis_bands is None else ",".join(_ep_rebasis_bands)),
            len(_replaced),
            "; ".join(
                f"{c}.{b} {before:.3f} -> {after:.3f}"
                for c, b, before, after in _replaced
            ),
            _ep_anchor,
        )
    elif _ep_rebasis_on:
        raise ValueError(
            "ercot_offer_hrmult_ep_rebasis is ERCOT-scoped (rule 25) — "
            f"refusing to arm it for {iso}"
        )
    elif getattr(config, "ercot_offer_hrmult_ep_rebasis", False):
        # Explicit scrub (kwarg False over a config/prb True): the LP solves
        # WITHOUT the rebasis, so the recorded config must say so (rule 25).
        config = config.with_overrides(ercot_offer_hrmult_ep_rebasis=False)
        logger.info(
            "ERCOT DAM offer hr-mult EP rebasis: SCRUBBED by explicit False "
            "— offer curve unchanged"
        )
    # Per-plant measured coal offer curves (run_calibration_full
    # --coal-perplant-offer-level; ScenarioConfig.coal_perplant_offer_level,
    # ERCOT-144 — the DOF-retirement lane ERCOT-143 §2 chartered). Runs AFTER
    # every offer-curve transformation above (backcast_config deltas,
    # prb_overrides, the coal econ marginal-HR floor, the EP rebasis) because
    # it is a rule-19 REPLACEMENT of the whole COAL band-multiplier × sigmoid
    # composition on the CAMPD committed/econ rows: the COAL_* groups are
    # STRIPPED from offer_curve_by_group, the PRB/lignite passthrough
    # sigmoids and the coal econ marginal-HR floor are disarmed (all three
    # price only the rows this mechanism now owns — nothing re-armable
    # remains in the recorded config, rule 26 [R-DELETE] spirit), and the
    # curve registry resolves HERE from constants so run_config.json records
    # the values the solve used (rule 25). `_mustrun` (ERCOT-137) and
    # `_peak` (ERCOT-140) keep their own measured owners. An ISO without a
    # derived registry is a hard error, never a fallback (rule 24).
    # Identification: scripts/data/derive_coal_perplant_offer.py.
    if coal_perplant_offer_level:
        from market_sim.config.constants import COAL_PERPLANT_OFFER_CURVE_BY_ISO

        if iso not in COAL_PERPLANT_OFFER_CURVE_BY_ISO:
            raise SystemExit(
                f"--coal-perplant-offer-level: no derived per-plant coal "
                f"offer curves for {iso} in "
                "constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO — run "
                "scripts/data/derive_coal_perplant_offer.py and register the "
                "curves (rule 24: curves never cross ISO boundaries)"
            )
        _stripped = {
            g: v
            for g, v in (config.offer_curve_by_group or {}).items()
            if not g.startswith("COAL")
        }
        config = config.with_overrides(
            coal_perplant_offer_level=True,
            coal_perplant_offer_curves=COAL_PERPLANT_OFFER_CURVE_BY_ISO[iso],
            offer_curve_by_group=_stripped,
            coal_prb_passthrough_sigmoid=False,
            coal_lignite_passthrough_sigmoid=False,
            coal_econ_marginal_hr_bound=False,
        )
        logger.info(
            "%s coal per-plant measured offer curves (ERCOT-144): %d plants; "
            "COAL_* offer_curve_by_group groups stripped, PRB/lignite "
            "sigmoids + coal econ marginal-HR floor disarmed (rule-19 "
            "replacement)",
            iso,
            len(COAL_PERPLANT_OFFER_CURVE_BY_ISO[iso]),
        )
    # Per-year windowed per-plant coal offer curves (run_calibration_full
    # --coal-perplant-offer-yearly; ScenarioConfig.coal_perplant_offer_yearly,
    # ercot-168 — matrix §5.1 item 12's rule-23 re-derivation of the armed
    # ERCOT-144 identification from the delivery-2023 corpus). Refines the
    # block above: the WIRING guard here enforces the dependency (the level
    # flag is a solve kwarg, so a construction-time config check cannot see
    # it — the soc-reserve precedent). The FULL year-keyed table resolves
    # into the config (rule 25: run_config records what the solve used,
    # year-invariantly); the consumer indexes it by the solve year, and a
    # year absent from the table (2024/2025 — it carries only 2023) falls
    # through to the static registry unchanged (precommit G-BIT).
    # Identification: scripts/data/derive_coal_perplant_offer.py --year 2023.
    if coal_perplant_offer_yearly:
        from market_sim.config.constants import (
            COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO,
        )

        if not coal_perplant_offer_level:
            raise SystemExit(
                "--coal-perplant-offer-yearly requires "
                "--coal-perplant-offer-level: the year table refines the "
                "per-plant mechanism and has no meaning without it (rule 24)"
            )
        if iso not in COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO:
            raise SystemExit(
                f"--coal-perplant-offer-yearly: no derived year-windowed "
                f"coal offer curves for {iso} in "
                "constants.COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO — run "
                "scripts/data/derive_coal_perplant_offer.py --year <Y> and "
                "register the curves (rule 24: curves never cross ISO "
                "boundaries)"
            )
        config = config.with_overrides(
            coal_perplant_offer_yearly=True,
            coal_perplant_offer_curves_yearly=(
                COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO[iso]
            ),
        )
        logger.info(
            "%s coal per-plant YEAR-windowed offer curves (ercot-168): "
            "years %s; solve year %d is %s the table",
            iso,
            sorted(COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO[iso]),
            year,
            (
                "IN"
                if year in COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO[iso]
                else "NOT in (static fall-through)"
            ),
        )
    # ROUTE A "REPLACE" — the COMMITTED band's MEASURED basis
    # (run_calibration_full --committed-band-measured-basis;
    # ScenarioConfig.committed_band_measured_basis, pjm-h6). Runs LAST among
    # the offer-curve transformations — after backcast_config's overrides and
    # deltas, after the prb_overrides application, after the coal econ
    # marginal-HR floor, after the ERCOT-118 EP rebasis and after the ERCOT-144
    # per-plant coal replacement — because it REPLACES the resolved `committed`
    # multiplier outright rather than bounding it, so it must see the curve the
    # calibration path actually produced (rule 25: run_config records what was
    # solved).
    #
    # Half (a) only lives here; half (b) — the coal supply passthrough dropped
    # from the same band — rides the ScenarioConfig field into
    # fleet.campd_tranche_fuel_frac. They are ONE mechanism (rule 19
    # [R-ONE-MECH]) and the flag arms both together; arming the multiplier
    # alone would leave the sigmoid scaling the same block, which delivers the
    # measured basis in NO year (charter §4).
    #
    # Tri-state, the ercot-115 seam pattern: None keeps the config-resolved
    # value (default False for every ISO and every lane), True/False force it
    # on/off so an A/B control arm can scrub it and replay_keeper can pin a
    # pre-promotion bundle to the behaviour it actually solved with.
    _committed_basis_on = (
        bool(config.committed_band_measured_basis)
        if committed_band_measured_basis is None
        else bool(committed_band_measured_basis)
    )
    if _committed_basis_on and coal_perplant_offer_level:
        # Two mechanisms would own the coal committed rows: ERCOT-144 strips
        # the COAL_* groups out of offer_curve_by_group entirely and prices
        # those rows from its own per-plant registry, so half (a) would reach
        # no coal class while half (b) still dropped the sigmoid — a torn
        # mechanism, not a composition (rule 19 [R-ONE-MECH]).
        raise SystemExit(
            "--committed-band-measured-basis is incompatible with "
            "--coal-perplant-offer-level: both own the coal committed band's "
            "price, and the per-plant mechanism strips COAL_* from "
            "offer_curve_by_group so the measured substitution could not "
            "reach it (rule 19 [R-ONE-MECH])"
        )
    if _committed_basis_on:
        from market_sim.data.offer_curves import apply_committed_band_measured_basis

        _cb_curve, _cb_sub = apply_committed_band_measured_basis(
            config.offer_curve_by_group, iso
        )
        config = config.with_overrides(
            committed_band_measured_basis=True, offer_curve_by_group=_cb_curve
        )
        if _cb_sub:
            logger.info(
                "%s committed-band measured basis (%d): %s",
                iso,
                len(_cb_sub),
                "; ".join(
                    f"{c} {before:.4f} -> {after:.4f}" for c, before, after in _cb_sub
                ),
            )
        else:
            logger.info(
                "%s committed-band measured basis: no covered class moved — "
                "offer curve unchanged (no artifact, or every band already at "
                "its measured value)",
                iso,
            )
    elif config.committed_band_measured_basis:
        # Explicit scrub: the LP must solve WITHOUT the mechanism, so the
        # recorded config must say so too — and half (b) reads this same field,
        # so scrubbing it here disarms BOTH halves together.
        config = config.with_overrides(committed_band_measured_basis=False)
        logger.info(
            "%s committed-band measured basis: SCRUBBED by explicit False — "
            "offer curve and coal committed passthrough unchanged",
            iso,
        )
    # Per-plant tranche-config override sheet (run_calibration_full
    # --plant-tranche-config): each listed plant's tranche shares + band HR
    # multipliers come straight from the CSV, bypassing the offer curve.
    if plant_tranche_config:
        config = config.with_overrides(plant_tranche_config_path=plant_tranche_config)
    # Daily SOC-cycling cap (run_calibration_full --storage-daily-cycling):
    # bounds storage perfect foresight to within-day arbitrage.
    if storage_daily_cycling:
        config = config.with_overrides(storage_daily_cycling=True)
    if storage_vintage_ramp:
        config = config.with_overrides(storage_vintage_ramp=True)
    # AS reserve withholding (run_calibration_full --as-reserve-withholding):
    # remove the measured cleared reserve MW from the gas/flexible-thermal
    # headroom before the energy supply curve clears (ERCOT up-AS / PJM Primary
    # Reserve requirement; fleet.generators_to_fleet_arrays).
    if as_reserve_withholding:
        config = config.with_overrides(as_reserve_withholding=True)
    # CAISO formula-based operating-reserve withholding (run_calibration_full
    # --as-reserve-formula): withhold R(t) = max(MSSC, 0.067*load) + 0.01*load
    # (WECC MORC + 1% regulation-up) from gas top-of-merit headroom; CAISO-only,
    # the default-off scaffold until OASIS cleared-AS data can be pulled
    # (fleet.caiso_operating_reserve_mw / generators_to_fleet_arrays).
    if as_reserve_formula:
        config = config.with_overrides(as_reserve_formula=True)
    # Energy+reserve co-optimization (run_calibration_full
    # --energy-reserve-coopt): co-optimize energy and Primary Reserve inside the
    # LP (structural 1.5 x MSSC requirement + published ORDC demand curve);
    # PJM-gated in _run_dispatch. Replaces the post-solve ORDC overlay.
    if energy_reserve_coopt:
        config = config.with_overrides(energy_reserve_coopt=True)
    # MISO locational (zonal) reserve families on top of the market-wide RBDC
    # (run_calibration_full --miso-zonal-reserves): BPM-002 §3.3.2 zonal
    # minimum requirements priced at the published §5.2.1.2 zonal curve.
    if miso_zonal_reserves:
        config = config.with_overrides(miso_zonal_reserves=True)
    # MISO Midwest sub-regional reserve-holding family on top of the
    # market-wide RBDC (run_calibration_full --miso-midwest-subregional-
    # reserves): the measured North+Central OR reservation held IN the 5
    # physical Midwest zones, priced at the published $200 RPE demand value,
    # reserve_class 0 nested (miso-71 engagement-depth lane).
    if miso_midwest_subregional_reserves:
        config = config.with_overrides(miso_midwest_subregional_reserves=True)
    # MISO per-asset (zone x fuel-class pooled) 10-min-ramp-bounded reserve
    # columns (run_calibration_full --miso-reserve-pergen): reserve competes
    # with energy on the marginal pool and cleared reserve is capped at the
    # deliverable 10-minute ramp, so the RBDC / zonal ORDC families can run
    # short (reserve_config._miso_design pergen branch).
    if miso_reserve_pergen:
        config = config.with_overrides(miso_reserve_pergen=True)
    # Pooled linear commitment-posture lever on the pergen pools (design note
    # docs/multi-iso/miso-scarcity-posture-design-2026-07.md §A).
    if miso_commitment_posture:
        config = config.with_overrides(miso_commitment_posture=True)
    # Online-gated Reg+Spin reserve supply on the pergen pools
    # (PREREG-miso167 §2; reserve_config._miso_design gated branch).
    if miso_reserve_online_gated:
        config = config.with_overrides(miso_reserve_online_gated=True)
    # Measured hourly OR requirement basis for the MISO co-opt families
    # (asm_rt_cleared_mw intake, data.miso_reserve_requirements): replaces
    # the flat fleet-MSSC+400 and South within-zone-MSSC estimates with the
    # measured hourly reservation (rules 13/14; NYISO #1344 pattern).
    if miso_measured_reserve_requirements:
        config = config.with_overrides(miso_measured_reserve_requirements=True)
    # MISO RDT congestion-depth pair (miso-57 lane): sever the free
    # South→external→Midwest wheel around the RDT (topology split) and price
    # the RDT with the published 92% default derate + $40/$500 TCDC tiers
    # (2024 SOM §III.B). Both structural, zero fitted scalars; the flags ride
    # config into apply_interchange_topology / get_interchange_spec.
    if miso_south_seam_split:
        config = config.with_overrides(miso_south_seam_split=True)
    if miso_rdt_tcdc:
        config = config.with_overrides(miso_rdt_tcdc=True)
    # MISO marginal-loss physics (miso-76 M3): the flag rides config into
    # apply_interchange_topology (L1-L6 one-way loss pairs) and the
    # DispatchSpec link_loss assembly below. Measured delivery-factor
    # surface, zero fitted scalars.
    if miso_zonal_loss_surface:
        config = config.with_overrides(miso_zonal_loss_surface=True)
    # PJM marginal-loss physics (pjm-136 M2): the flag rides config into
    # apply_interchange_topology (internal one-way loss pairs) and the
    # DispatchSpec link_loss assembly below. Measured delivery-factor
    # surface from PJM's own published MLC record, zero fitted scalars.
    if pjm_zonal_loss_surface:
        config = config.with_overrides(pjm_zonal_loss_surface=True)
    if ercot_multiproduct_as_coopt:
        config = config.with_overrides(ercot_multiproduct_as_coopt=True)
    # Published pre-reform ECRS deployment design (no price-based release
    # through 2024-07-31 -> at-cap demand step; standing ramp after): see
    # reserve_config.ERCOT_ECRS_RELEASE_REFORM_* citations.
    if ercot_ecrs_conservative_deployment:
        config = config.with_overrides(ercot_ecrs_conservative_deployment=True)
    # Published pre-RTC+B RRS/Reg-Up carve-out (no price-based SCED release
    # through RTC+B go-live 2025-12-05 -> at-cap demand steps; standing ramp
    # after): see ScenarioConfig.ercot_nonreleasable_as_withholding.
    if ercot_nonreleasable_as_withholding:
        config = config.with_overrides(ercot_nonreleasable_as_withholding=True)
    # Lumped ORDC total-reserve family (RTORPA) layered on the product stack:
    # see ScenarioConfig.ercot_ordc_total_reserve / reserve_config.
    if ercot_ordc_total_reserve:
        config = config.with_overrides(ercot_ordc_total_reserve=True)
    # Pre-RTC+B ORDC-only reserve-scarcity pricing (the ercot57 product-ladder
    # design; ScenarioConfig field docstring has the design note). Applied
    # AFTER the co-opt/total-reserve flags: __post_init__ requires them.
    if ercot_ordc_only_scarcity:
        config = config.with_overrides(ercot_ordc_only_scarcity=True)
    # Measured battery AS award netted off the fast products' requirements
    # (multi-product measured-storage path): reserve_config.
    if ercot_storage_as_product_credit:
        config = config.with_overrides(ercot_storage_as_product_credit=True)
    # Measured HH monthly gas shape (level-preserving): fuel.gas_seasonal_shape.
    if gas_hh_monthly_shape:
        config = config.with_overrides(gas_hh_monthly_shape=True)
    if ercot_as_aware_commitment:
        config = config.with_overrides(ercot_as_aware_commitment=True)
    if ercot_reserve_supply_cap:
        config = config.with_overrides(
            ercot_reserve_supply_cap=True,
            ercot_reserve_supply_cap_from_year=ercot_reserve_supply_cap_from_year,
        )
    if ercot_reserve_supply_forward:
        config = config.with_overrides(ercot_reserve_supply_forward=True)
    if pjm_reserve_supply_cap:
        config = config.with_overrides(pjm_reserve_supply_cap=True)
    if pjm_reserve_online_gated:
        config = config.with_overrides(
            pjm_reserve_online_gated=True,
            pjm_reserve_online_rho=pjm_reserve_online_rho,
        )
    if pjm_reserve_commitment_scoped:
        # PJM path B (G-20b): commitment-scoped reserve supply — fa_p2-style
        # availability mask from the P0 run pattern at the P0->P1 seam +
        # deliverable supply cap recomputed on the masked fleet
        # (pipeline.commitment.build_pjm_reserve_p1_prep). GATED default off.
        config = config.with_overrides(pjm_reserve_commitment_scoped=True)
    if pjm_reserve_pergen:
        config = config.with_overrides(pjm_reserve_pergen=True)
    if pjm_reserve_pergen_sync:
        # PJM per-gen OPPORTUNITY-COST co-opt (G-20b successor): Synchronized
        # sub-product families + per-pool sync/non-sync column split, sync
        # caps online-scoped at the P0->P1 seam
        # (pipeline.commitment.build_pjm_reserve_p1_prep). Requires
        # pjm_reserve_pergen. GATED default off.
        config = config.with_overrides(pjm_reserve_pergen_sync=True)
    if pjm_reserve_pergen_size_split:
        # PJM pergen SIZE-SPLIT pooling tier (pjm-87 diagnosis remedy):
        # splits each (zone, fuel-class) pool's large plants into individual
        # columns, self-normalizing threshold (reserve_config.
        # PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE). Requires pjm_reserve_pergen.
        # GATED default off.
        config = config.with_overrides(pjm_reserve_pergen_size_split=True)
    if pjm_commitment_posture:
        # PJM commitment-posture lever (design note §A ported; requires the
        # pergen reserve co-opt). U/SU columns on non-fast-start pools; zero
        # fitted parameters. GATED default off.
        config = config.with_overrides(pjm_commitment_posture=True)
    if measured_ramp_capability:
        # Measured EIA-860/CAMPD ramp-capability reconciliation of the class
        # ramp10 fractions (data/ramp_capability.py; rule 14 measured-over-
        # estimate). Consumed at fleet build; GATED default off.
        config = config.with_overrides(measured_ramp_capability=True)
    if ercot_as_forward_requirement:
        config = config.with_overrides(ercot_as_forward_requirement=True)
    # ERCOT load-resource reserve credit (run_calibration_full
    # --ercot-load-resource-reserve): credit measured RRS-UFR (load-side
    # responsive reserve) into the co-opt reserve balance. GATED — alters
    # dispatch volumes. ERCOT co-opt only; a no-op otherwise.
    if ercot_load_resource_reserve:
        config = config.with_overrides(
            ercot_load_resource_reserve=True,
            ercot_load_resource_reserve_from_year=int(
                ercot_load_resource_reserve_from_year
            ),
        )
    # ERCOT storage-AS reserve credit (run_calibration_full
    # --ercot-storage-as-reserve): credit the measured battery-provided AS back
    # into the co-opt reserve balance — storage_as_commitment removes it from the
    # reserve cap, so the committed battery AS would otherwise be dropped from
    # reserve supply. GATED; ERCOT co-opt + storage_as_commitment only.
    if ercot_storage_as_reserve:
        config = config.with_overrides(
            ercot_storage_as_reserve=True,
            ercot_storage_as_reserve_from_year=int(ercot_storage_as_reserve_from_year),
        )
    if ercot_ecrs_requirement:
        config = config.with_overrides(
            ercot_ecrs_requirement=True,
            ercot_ecrs_requirement_from_year=int(ercot_ecrs_requirement_from_year),
        )
    # Published ORDC LOLP table (run_calibration_full --ordc-lolp-params-path):
    # replace the neutral flat fallback (mu=0) with ERCOT's published NP6-576-ER
    # seasonal/TOD mu/sigma so the co-opt reserve demand curve sits at the real
    # reserve level the adder begins to bite. Grounded input, not a price fit.
    if ordc_lolp_params_path:
        config = config.with_overrides(ordc_lolp_params_path=str(ordc_lolp_params_path))
    # Storage AS commitment (run_calibration_full --storage-as-commitment):
    # ERCOT-only reservation of measured storage up-AS MW from the battery
    # dispatch power cap (applied after storage_cap_profiles below).
    if storage_as_commitment:
        config = config.with_overrides(storage_as_commitment=True)
    # Measured-award AS->energy co-participation (run_calibration_full
    # --ercot-storage-as-deployment): force the measured evening award draw-down
    # as a battery discharge floor at the net-load ramp (the storage-cycling-lane
    # fix, applied after storage_cap_profiles/reservation below). Requires
    # storage_as_commitment (the reservation it releases from).
    if ercot_storage_as_deployment:
        config = config.with_overrides(
            ercot_storage_as_deployment=True,
            ercot_storage_as_deployment_from_year=int(
                ercot_storage_as_deployment_from_year
            ),
        )
    # Endogenous storage energy-vs-AS co-opt (run_calibration_full
    # --ercot-storage-as-endogenous, G5): the battery CHOOSES energy vs upward-AS
    # inside the multi-product co-opt, replacing the measured-award reservation.
    # Full battery cap to the co-opt (no measured subtraction below), the measured
    # reserve credit guarded off (scarcity.ercot_*_coopt_inputs), and the cleared
    # storage AS counts toward the measured RTOLCAP supply cap. Takes precedence
    # over storage_as_commitment when both are set.
    if ercot_storage_as_endogenous:
        config = config.with_overrides(ercot_storage_as_endogenous=True)
    if ercot_storage_as_duration_gate:
        config = config.with_overrides(ercot_storage_as_duration_gate=True)
    # Battery throughput/cycling cost (run_calibration_full --battery-adder):
    # per-MWh-discharged adder that tames LP over-cycling of the BESS fleet.
    # CAISO defaults to $5/MWh when no explicit adder is passed: the 10+ GW
    # fleet with perfect-foresight LP over-cycles without a throughput cost
    # proxy for degradation + ancillary-service opportunity cost.
    # caiso-100 discovery (2026-07-19): this block runs AFTER the generic
    # prb_overrides ScenarioConfig application above, so it silently STOMPED a
    # prb-carried adder back to the kwarg/fallback value (the pre-registered
    # B-leg's derived 14.25 never reached the LP), and the CAISO fallback was
    # live in every keeper-lineage solve while run_config recorded 0.0 (the
    # recorder in run_calibration_full never mirrored it — fixed there too).
    # Per the ERCOT-65 convention the generic channel governs: skip this block
    # when prb_overrides carries the key.
    _batt_adder = battery_dispatch_adder
    if (prb_overrides or {}).get("battery_dispatch_adder") is not None:
        _batt_adder = None  # prb channel already applied above and governs
    elif not _batt_adder and iso.upper() == "CAISO":
        _batt_adder = 5.0
    if _batt_adder:
        config = config.with_overrides(battery_dispatch_adder=_batt_adder)
    if gas_offer_curve:
        config = config.with_overrides(gas_offer_curve=True)
    # Measured ISO-month delivered gas (EIA-923) instead of annual + shape.
    if gas_monthly_actuals:
        config = config.with_overrides(gas_monthly_actuals=True)
    # pjm-169 F4: re-resolve the gas-offer net-revenue margin's identification
    # point onto the SOLVE YEAR. Deliberately placed HERE, not at the
    # `--gas-offer-margin` lookup ~1,200 lines above: `_gas_series` is only the
    # series the offer path prices against once `gas_hub_basis_overlay` and
    # `gas_monthly_actuals` have been applied, and both are set LATER than that
    # lookup. Resolving at the lookup would measure a series no unit ever pays
    # (PRECOMMIT-pjm169-f4-anchor-vintage-2026-09-06.md §2; gate S1 is exactly
    # this identity). The resolved value overwrites `gas_offer_margin_anchor`,
    # so run_config.json records the number the LP solved with rather than a
    # lookup indirection (rule 24 [R-REGISTRY]) and the cache key moves with it.
    # A zone-resolved anchor takes precedence and is never stacked on
    # (rule 19 [R-ONE-MECH]).
    # nyiso-231: honour EITHER the solve kwarg OR the registered ScenarioConfig
    # field, the same way the zone-resolved block below already does. The field
    # is the ONLY route `replay_keeper.py --set` has (that channel writes the
    # field, never the kwarg), so a kwarg-only gate would let a --set A/B
    # silently solve the CONTROL -- the nyiso-229 failure mode. It is also what
    # keeps the recorded mirror honest: `_recorded_config`'s
    # `mirror_solve_year_gas_anchors` gates on kwarg-or-field, so a field-armed
    # solve that did NOT resolve here would record an anchor the LP never
    # priced against (rule 24 [R-REGISTRY]).
    if gas_offer_margin_anchor_vintage or getattr(
        config, "gas_offer_margin_anchor_vintage", False
    ):
        if not getattr(config, "gas_offer_net_revenue_margin", False):
            raise SystemExit(
                "--gas-offer-margin-anchor-vintage requires --gas-offer-margin: "
                "the vintage flag moves the identification point of the "
                "net-revenue margin mechanism, so arming it alone is a no-op "
                "the run record would misreport (rule 24)"
            )
        if getattr(config, "gas_offer_margin_zonal_anchor", False):
            raise SystemExit(
                "--gas-offer-margin-anchor-vintage and "
                "--gas-offer-margin-zonal-anchor both re-resolve the SAME "
                "identification point; they are alternatives, never stacked "
                "(rule 19 [R-ONE-MECH])"
            )
        from market_sim.data.fuel.trajectories import _gas_series as _f4_gas_series

        _f4_anchor = float(
            np.asarray(_f4_gas_series(config, year, hours), dtype=float).mean()
        )
        logger.info(
            "gas offer margin anchor VINTAGE %d: %.4f $/MMBtu (window anchor "
            "%s) — the solve year's own mean delivered-gas series",
            year,
            _f4_anchor,
            config.gas_offer_margin_anchor,
        )
        config = config.with_overrides(
            gas_offer_margin_anchor_vintage=True,
            gas_offer_margin_anchor=_f4_anchor,
        )
    # nyiso-230 — the ZONE-RESOLVED half of the same move. Placed here for the
    # same reason as the block above: `_gas_series` is only the series the offer
    # path prices against once `gas_hub_basis_overlay` and `gas_monthly_actuals`
    # have been applied. Re-resolves the per-zone anchors on the SOLVE YEAR, so
    # `data.fleet.assembly` reads the level each zone's units actually pay in
    # THIS year instead of the frozen 2023-2025 window mean. The resolved values
    # overwrite `gas_offer_margin_anchor_by_zone`, so run_config.json records
    # the numbers the LP solved with (rule 24 [R-REGISTRY]) and the cache key
    # moves with them. One identification point, resolved on (zone, year) —
    # never stacked on the ISO-level vintage flag (rule 19 [R-ONE-MECH]).
    # Honour EITHER the solve kwarg OR the registered ScenarioConfig field: the
    # field is in _CACHE_KEY_OPTIONAL_FIELDS, so a config carrying it True MUST
    # resolve, or a cache key would claim a resolution the solve never did
    # (rule 24 [R-REGISTRY]). It is also the ONLY route replay_keeper.py --set
    # has: that channel writes the config field, never the kwarg, so gating on
    # the kwarg alone would let an A/B probe silently solve the CONTROL --
    # the nyiso-229 failure mode, one layer over.
    if gas_offer_margin_zonal_anchor_vintage or getattr(
        config, "gas_offer_margin_zonal_anchor_vintage", False
    ):
        if not getattr(config, "gas_offer_net_revenue_margin", False):
            raise SystemExit(
                "--gas-offer-margin-zonal-anchor-vintage requires "
                "--gas-offer-margin: the vintage flag moves the identification "
                "point of the net-revenue margin mechanism, so arming it alone "
                "is a no-op the run record would misreport (rule 24)"
            )
        if not getattr(config, "gas_offer_margin_zonal_anchor", False):
            raise SystemExit(
                "--gas-offer-margin-zonal-anchor-vintage requires "
                "--gas-offer-margin-zonal-anchor: it re-resolves the ZONE table "
                "on the solve year, and without the zonal gate there is no zone "
                "table in the offer path to resolve. For an ISO with no zonal "
                "basis the ISO-level --gas-offer-margin-anchor-vintage is the "
                "flag you want (rule 19 [R-ONE-MECH])"
            )
        if gas_offer_margin_anchor_vintage or getattr(
            config, "gas_offer_margin_anchor_vintage", False
        ):
            raise SystemExit(
                "--gas-offer-margin-zonal-anchor-vintage and "
                "--gas-offer-margin-anchor-vintage both re-resolve the SAME "
                "identification point; they are alternatives, never stacked "
                "(rule 19 [R-ONE-MECH])"
            )
        from market_sim.data.fuel.zonal_anchor import zonal_gas_anchors_for_year

        _f5_by_zone = zonal_gas_anchors_for_year(config, year, hours)
        logger.info(
            "gas offer margin ZONAL anchors VINTAGE %d: %s $/MMBtu (window "
            "anchors %s) — the solve year's own mean delivered-gas series, "
            "per zone",
            year,
            {z: round(a, 4) for z, a in _f5_by_zone.items()},
            config.gas_offer_margin_anchor_by_zone,
        )
        config = config.with_overrides(
            gas_offer_margin_zonal_anchor_vintage=True,
            gas_offer_margin_anchor_by_zone=_f5_by_zone,
        )
    # PJM per-zone gas basis (opens the west-cheap / east-dear spread so PJM
    # stops clearing as a single copper-plate). No-op for non-PJM ISOs — the
    # apply gates on iso == "PJM" — so setting it here is safe regardless.
    if pjm_zonal_gas_basis:
        config = config.with_overrides(pjm_zonal_gas_basis=True)
    # MISO per-zone gas basis (opens the north/south gas gradient). No-op for
    # non-MISO ISOs — the apply gates on iso == "MISO".
    if miso_zonal_gas_basis:
        config = config.with_overrides(miso_zonal_gas_basis=True)
    # MISO winter fuel-security citygate daily overlay (miso-72): in Dec/Jan/Feb,
    # reprice the Chicago-hub zones' gas units at the measured Chicago Citygate
    # daily shape, superseding the national HH gas_daily_shape there. No-op for
    # non-MISO ISOs — the apply gates on iso == "MISO".
    if miso_winter_citygate_daily:
        config = config.with_overrides(miso_winter_citygate_daily=True)
    # PJM transmission-congestion lever (break the copper-plate): cap the priced
    # external star node to the measured per-border interchange envelope + tighten
    # the internal interfaces to their measured transfer limits. Wired below at
    # the interface-group / TTC build; no-op for non-PJM ISOs.
    if pjm_congestion:
        config = config.with_overrides(pjm_congestion=True)
    # Econ-ramp rendering sweep (run_calibration_full --curve-n / --curve-exp):
    # offer_curve_smoothing_n / offer_curve_smoothing_exp; None entries keep
    # the ScenarioConfig defaults.
    if curve_smoothing:
        config = config.with_overrides(
            **{k: v for k, v in curve_smoothing.items() if v is not None}
        )
    # Top-of-stack outage allocation for CC_REGULAR (run_calibration_full
    # --cc-derate-from-top): partial outages truncate the expensive end of
    # the offer curve instead of scaling every tranche pro-rata. CAISO
    # defaults ON: per-plant peaking bands are narrow (0-4%), so pro-rata
    # derates crush the committed floor and prevent 0% CF hours.
    if cc_derate_from_top or iso.upper() == "CAISO":
        config = config.with_overrides(cc_outage_derate_from_top=True)
    if cc_nameplate_summer_derate:
        config = config.with_overrides(cc_nameplate_summer_derate=True)
    if coal_nameplate_summer_derate:
        config = config.with_overrides(coal_nameplate_summer_derate=True)
    if gt_ambient_derate:
        # Physics-grounded GT ambient-temperature derate on the hottest hours
        # (fleet.generators_to_fleet_arrays). Slopes/reference default to the
        # ScenarioConfig physical values unless the caller overrides them.
        _amb = {"gt_ambient_derate": True}
        if gt_ambient_derate_ref_c is not None:
            _amb["gt_ambient_derate_ref_c"] = float(gt_ambient_derate_ref_c)
        if gt_ambient_derate_slope_cc is not None:
            _amb["gt_ambient_derate_slope_cc"] = float(gt_ambient_derate_slope_cc)
        if gt_ambient_derate_slope_ct is not None:
            _amb["gt_ambient_derate_slope_ct"] = float(gt_ambient_derate_slope_ct)
        config = config.with_overrides(**_amb)
    if temp_dependent_derate:
        # Temperature-dependent capacity derate: replaces the flat EIA-860
        # net-summer derate with a per-class physical curve in measured hourly
        # zone dry-bulb temperature (fleet.generators_to_fleet_arrays). Slopes/
        # reference temps default to the ScenarioConfig physical values.
        _td: dict = {"temp_dependent_derate": True}
        # Hour-grain / mean-anchored legs (miso-101). Both default off, so an
        # unset flag leaves the committed day-flat hinged curve untouched.
        if temp_derate_hourly_grain:
            _td["temp_derate_hourly_grain"] = True
        if temp_derate_mean_anchored:
            _td["temp_derate_mean_anchored"] = True
        if temp_derate_classes:
            _td["temp_derate_classes"] = frozenset(temp_derate_classes)
        if temp_derate_slope_st_chp is not None:
            _td["temp_derate_slope_st_chp"] = float(temp_derate_slope_st_chp)
        if temp_derate_slope_ct_chp is not None:
            _td["temp_derate_slope_ct_chp"] = float(temp_derate_slope_ct_chp)
        config = config.with_overrides(**_td)
    if zero_forcing_ablation:
        # D-3 zero-forcing ablation twin (audit §7 / CLAUDE.md rule 20): drop
        # every MERCHANT floor/bridge, keeping only the structural must-run set
        # (nuclear / CHP-steam / coal take-or-pay). Applied AFTER every per-ISO
        # default and with_overrides so the floors go off regardless of how they
        # were set — the CAISO ct_netload_drag / caiso_ra_mustoffer defaults are
        # config-level (not kwargs), so only a config transform can neutralize
        # them. The off-list is derived from the D-2 mechanism registry, so a
        # new floor is ablated by default (see ScenarioConfig.as_zero_forcing_
        # ablation / data.floor_mechanisms.zero_forcing_field_overrides).
        config = ScenarioConfig.as_zero_forcing_ablation(config)
    # Point the EIA-860 loaders at a year-matched vintage when the scenario asks
    # for one (backcast knob; None resets to the canonical 2025ER snapshot the
    # COD ramp filters to the solved year). Must precede every fleet / storage /
    # renewable / COD-map load below so they all read the same vintage.
    from market_sim.config.paths import (
        resolve_backcast_eia860_vintage,
        set_eia860_vintage,
    )

    set_eia860_vintage(
        resolve_backcast_eia860_vintage(
            config.eia860_vintage_year,
            year,
            getattr(config, "eia860_vintage_tracks_solve_year", False),
        )
        if config.mode == "backcast"
        else None
    )
    # Arm/disarm the CAISO FSNO sub-zonal partition for this solve BEFORE the
    # first get_iso_config / zone-lookup call, so the LP and every bare
    # get_iso_config() consumer (renewables shares, hydro budgets, storage
    # fleets, zonal gas basis, …) see the same topology — the
    # set_eia860_vintage pattern directly above (caiso-224;
    # config.topology_variant module docstring has the full rationale).
    from market_sim.config.topology_variant import set_caiso_fsno_partition

    set_caiso_fsno_partition(
        iso == "CAISO" and getattr(config, "caiso_fsno_subzonal_topology", False)
    )
    # PJM-NEXT fleet_zone_vintage_coords: armed per solve, like the partition
    # above, before the first fleet load reads the zone lookup.
    from market_sim.data.zone_assignment import set_fleet_zone_vintage_coords

    set_fleet_zone_vintage_coords(getattr(config, "fleet_zone_vintage_coords", False))
    iso_config = get_iso_config(iso)
    # Year-varying interface limits (e.g. NYISO Central-East jumps with the AC
    # Transmission project in service Dec 2023) — applied before the import
    # node joins so the corrected links flow through the whole solve.
    iso_config = _apply_iso_year_ttc(iso_config, iso, year)
    # CAISO per-year SP15-pocket import caps (config.caiso_per_year_import_caps,
    # default off -> byte-identical no-op). The SP15 split (2026-07-09) baked the
    # two internal import-limited links (SP15_rest -> LA_BASIN, SP15_rest -> SDGE)
    # at the STATIC 2023 tightest-year LCT import_cap; this swaps each solve
    # year's link TTC to that year's own published row. Measured limit over a
    # frozen estimate (CLAUDE.md #14), zero free parameters (#24).
    #
    # WHY THIS CALL SITE EXISTS (caiso-162): the mechanism was previously wired
    # ONLY into runner.py::run_scenario_iso -- the forecast/scenario path -- so a
    # BACKCAST solve, which reaches the LP through this module and
    # pipeline.solve.run_energy_solve, silently ignored the flag. Arm B of
    # caiso-162 recorded caiso_per_year_import_caps=true in its run_config.json
    # and still bounded both pocket links at the static 12,008 / 1,436 MW,
    # proving the calibration lane never saw it. Applied here, immediately after
    # _apply_iso_year_ttc and BEFORE the import node joins, so the corrected
    # links flow through incidence, interface groups and the TTC array alike --
    # the same placement rationale as the year-varying interface limits above.
    if iso == "CAISO" and getattr(config, "caiso_per_year_import_caps", False):
        from market_sim.model.transmission import apply_caiso_local_import_limits

        iso_config = apply_caiso_local_import_limits(iso_config, iso, year)
    # Priced import/export node (orchestrator-unification Stage 5): the
    # builder choice — reference-price seam vs CAISO per-hub / bidirectional
    # intertie vs the static year-grounded tranche ladder, plus the Manitoba
    # firm-import block — is resolved by the SHARED
    # config/interchange_config.get_interchange_spec (the same spec the
    # forecast runner consumes), and the generators come from the shared
    # build_interchange_fleet, which delegates to the canonical
    # transmission.py builders. The external zone joins the topology and its
    # import tranches + export sinks join the fleet below; the measured
    # interchange schedule then stays out of demand (no double count).
    import_generators: list = []
    # Default the CAISO corridor intertie flag so the later corridor-limit
    # and forward-ATC checks are bound on every path; it is only set inside
    # the priced-interchange block below (CAISO-only), so a non-priced or
    # non-CAISO run keeps it False.
    caiso_corridors = False
    # caiso-110 Option A: when the endogenous WECC-West node is on (CAISO only),
    # the WECC_import node becomes a REAL co-optimized neighbor ZONE — its own
    # measured demand + a reduced import-priced fleet built from the
    # wecc-west-supply frame — instead of the static import tranches. It
    # SUPERSEDES the tranche fleet, the per-hub topology split, and the CAISO
    # import injectors (firm/clean/spot) — one mechanism per phenomenon (rule 18;
    # docs/handoffs/caiso-endogenous-wecc-node-design-2026-07-21.md). The base
    # _caiso_config already carries the single WECC_import zone, its two corridor
    # ties, and the 7,500 MW simultaneous cap, so no apply_interchange_topology
    # runs (no split); the tie flow carries the West's endogenous net export.
    _endogenous_wecc = (
        getattr(config, "caiso_endogenous_wecc_node", False) and iso == "CAISO"
    )
    _wecc_west_avail: dict[str, np.ndarray] = {}
    _wecc_west_demand: np.ndarray | None = None
    if _endogenous_wecc:
        from market_sim.data.wecc_west_fleet import build_wecc_west_fleet

        import_generators, _wecc_west_avail, _wecc_west_demand = build_wecc_west_fleet(
            year, gas_price, hours
        )
    elif priced_interchange:
        # CARB levies its cap-and-trade allowance on unspecified WECC imports
        # (border carbon adjustment, EF 0.428 t/MWh x allowance), so every
        # CAISO import tranche carries it in its delivered cost — the same
        # adder the production runner applies (model.runner). It is NOT on the
        # export sinks (exports owe no CA compliance cost). Resolved at the
        # backcast year's carbon price (each calibration solve is single-year).
        border_carbon = (
            wecc_border_carbon_adder(resolve_carbon_price(config, year))
            if iso == "CAISO"
            else 0.0
        )
        interchange_spec = get_interchange_spec(config, iso, year=year)
        caiso_corridors = interchange_spec.use_corridors
        import_generators = build_interchange_fleet(interchange_spec, border_carbon)
        # Shared topology sequence (same order as always): external node
        # extension, the capacity-deliverability Part-A seam import cap
        # (backcast mirror of the runner hook — the published per-area MIC
        # replaces the calibrated simultaneous-import scalar, resolved for
        # THIS backcast year's delivery year; no-op off the default-off flag
        # or when the clean data is absent), then the CAISO per-hub corridor
        # split re-homing the import links + simultaneous cap onto the
        # corridor zones the per-hub / reference-seam builder used.
        iso_config = apply_interchange_topology(
            iso_config,
            interchange_spec,
            config,
            year=year,
            extend_node=True,
        )
    zone_names = iso_config.zone_names

    # Demand: reuse a caller-supplied array when threaded in (the backcast
    # orchestrator already loads it once for the must-run residual pass), else
    # load it here. The caller only threads it when it matches this load
    # exactly (see the ``demand`` arg docstring), so the two paths are
    # byte-identical.
    if demand is None:
        demand = load_demand(
            iso,
            year,
            iso_config,
            td_loss_factor=config.td_loss_factor,
            include_interchange=not priced_interchange,
            caiso_demand_clock_realign=getattr(
                config, "caiso_demand_clock_realign", False
            ),
            caiso_supply_consistent_demand=getattr(
                config, "caiso_supply_consistent_demand", False
            ),
            ercot_tie_zonal_interchange=config.ercot_tie_zonal_interchange,
            nwpp_grid_carried_wind_served=getattr(
                config, "nwpp_grid_carried_wind_served", False
            ),
            nwpp_demand_plant_basis=getattr(config, "nwpp_demand_plant_basis", False),
            demand_balance_screen=getattr(config, "demand_balance_screen", False),
        )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, : config.hours]
        wind_cf = wind_cf[:, : config.hours]
        solar_cf = solar_cf[:, : config.hours]

    # caiso-110: give the WECC_import zone its OWN measured West demand (EIA-930
    # Region NW+SW aggregate) — the neighbor's energy balance. load_demand left
    # this row at 0 (load_share 0.0); the West fleet built above serves it and
    # exports the surplus over the ties. The West zone stays out of CAISO's
    # scored load/gen/CO2 via the results zone-exclusion (run_calibration_full).
    if _endogenous_wecc and _wecc_west_demand is not None:
        _wecc_idx = zone_names.index("WECC_import")
        demand = demand.copy()
        demand[_wecc_idx, : config.hours] = _wecc_west_demand[: config.hours]

    # CAISO Lever-D: re-curtail the uncurtailed HSL solar potential the dispatch
    # is handed. The reduced 3-zone topology cannot see the sub-area / local
    # congestion that drives ~70% of CAISO solar curtailment, so the LP runs the
    # full potential and curtails ~0 (docs/caiso-lever-audit-2026-06.md, Lever D).
    solar_cf = _apply_caiso_solar_deliverability(solar_cf, iso, year, config)

    # Must-run "other" resources (biomass, process gas, ...) serve load
    # exogenously — they run for industrial/process reasons, not LP economics —
    # so net them out of demand before the dispatch so they displace marginal
    # gas instead of being double-counted on top of a fully-served balance.
    if must_run_mw is not None:
        mr = np.asarray(must_run_mw, dtype=float)
        if mr.shape[1] > config.hours:
            mr = mr[:, : config.hours]
        demand = np.maximum(demand - mr, 0.0)

    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = _apply_ttc_overrides(
        iso_config, get_ttc_array(iso_config.links), ttc_overrides
    )
    # PJM congestion lever (Lever B): tighten the internal interfaces with a
    # confident measured mapping to their measured PJM transfer-limit postings
    # (constants.PJM_MEASURED_INTERNAL_TTC). Applied to the scalar TTC array before
    # the monthly expansion; no-op off the flag or for non-PJM ISOs.
    if getattr(config, "pjm_congestion", False) and iso == "PJM":
        from market_sim.config.constants import PJM_MEASURED_INTERNAL_TTC

        ttc = ttc.copy()
        for i, link in enumerate(iso_config.links):
            measured = PJM_MEASURED_INTERNAL_TTC.get((link.from_zone, link.to_zone))
            if measured is not None and measured != ttc[i]:
                logger.info(
                    "PJM congestion: internal TTC %s->%s %.0f -> %.0f MW "
                    "(measured transfer-limit posting)",
                    link.from_zone,
                    link.to_zone,
                    ttc[i],
                    measured,
                )
                ttc[i] = measured
    # Seasonal interface envelope: expand the scalar TTC to a per-hour matrix
    # where a measured monthly limit exists (NYISO Central-East). No-op (1-D)
    # for ISOs/years without one.
    ttc = _apply_iso_monthly_ttc(
        ttc, iso_config, iso, year, demand.shape[1], config=config
    )
    # NYISO Zone-K LCR/TSL mechanism (issue #1345, config.nyiso_li_lcr_tsl):
    # cap the NYC->Long_Island link at the published locality import limit in
    # the HB14-21 design-condition window, replacing the Long_Island 0.45
    # self-supply energy floor (excluded below — rule 19, one mechanism per
    # phenomenon). LI reliability energy then clears economically behind a
    # published limit instead of through a forced min_gen floor.
    if getattr(config, "nyiso_li_lcr_tsl", False):
        from market_sim.model.transmission import apply_nyiso_li_tsl_import_cap

        _li_n11 = bool(getattr(config, "nyiso_li_tsl_n11_security", False))
        ttc = apply_nyiso_li_tsl_import_cap(
            ttc,
            iso_config,
            iso,
            year,
            demand.shape[1],
            n11_security_basis=_li_n11,
        )
        logger.info(
            "%s %d: Zone-K LCR/TSL import cap on NYC->Long_Island (HB14-21, "
            "published %s; replaces the LI self-supply energy floor)",
            iso,
            year,
            "N-1-1 transmission security limit" if _li_n11 else "locality import limit",
        )
    # NYISO Zone-J (NYC) LCR/TSL mechanism (nyiso-61, config.nyiso_nyc_lcr_tsl):
    # cap the Lower_Hudson->NYC (Dunwoodie-South) link at the published NYC
    # locality import limit (2,875 MW) in the HB14-21 design-condition window,
    # replacing the link's 3,900 MW energy-TTC estimate. The Zone-J analog of
    # the Zone-K cap above; a transmission limit, not a floor (forces no energy).
    if getattr(config, "nyiso_nyc_lcr_tsl", False):
        from market_sim.model.transmission import apply_nyiso_nyc_tsl_import_cap

        ttc = apply_nyiso_nyc_tsl_import_cap(
            ttc, iso_config, iso, year, demand.shape[1]
        )
        logger.info(
            "%s %d: Zone-J LCR/TSL import cap on Lower_Hudson->NYC (HB14-21, "
            "published NYC locality import limit; replaces the 3,900 MW "
            "Dunwoodie-South energy-TTC estimate)",
            iso,
            year,
        )
    # Measured ERCOT GTC export limits (backcast overlay, ScenarioConfig.
    # ercot_gtc_limits_measured): the GTC-carrying links' export direction
    # follows the hourly NP6-86 measured limit series so West/Panhandle
    # curtailment emerges endogenously from the binding published limits.
    # Skipped only when the renewable upper bound is the raw delivered actuals
    # (``delivered_pinned``: EIA-930-as-CF already embeds the curtailment, so a
    # binding export cap would double-curtail wind below what really flowed);
    # a measured-potential OR reference-rate grossed-up bound keeps the limits
    # (ercot-252). The import direction keeps the static rating (a GTC is an
    # export stability limit).
    ttc_import = None
    if getattr(config, "ercot_gtc_limits_measured", False) and iso == "ERCOT":
        from market_sim.data.gtc import ercot_gtc_ttc_hourly

        if _renewable_bound_is_delivered_pinned(iso, year):
            logger.warning(
                "ercot_gtc_limits_measured: %d renewable bound is delivered-pinned "
                "— measured GTC limits skipped for this year to avoid "
                "double-curtailment",
                year,
            )
        else:
            gtc_out = ercot_gtc_ttc_hourly(
                np.asarray(ttc, dtype=float), iso_config, year, demand.shape[1]
            )
            if gtc_out is None:
                logger.warning(
                    "ercot_gtc_limits_measured: no gtc-limits clean partition "
                    "for %d — static TTC kept (supply the NP6-86 archives and "
                    "run scripts/data/curate_gtc_limits.py)",
                    year,
                )
            else:
                ttc, ttc_import = gtc_out

    # Measured PJM internal interface limits (backcast overlay, ScenarioConfig.
    # pjm_measured_interface_limits): the internal links whose static ttc_mw
    # was seeded from the Data Miner 2 transfer-limit postings follow the
    # measured HOURLY series (constants.PJM_INTERFACE_LINK_MAP; min of pre/post
    # contingency where both publish) in the forward west->east direction; the
    # reverse direction keeps the static rating. Applied AFTER pjm_congestion's
    # static medians so the hourly series supersedes them on mapped links
    # (same feed, finer aggregation — rule 19) while the run's statics remain
    # the reverse bound / fallback fill.
    if getattr(config, "pjm_measured_interface_limits", False) and iso == "PJM":
        from market_sim.data.transfer_interface_limits import (
            pjm_interface_ttc_hourly,
        )

        tif_out = pjm_interface_ttc_hourly(
            np.asarray(ttc, dtype=float),
            iso_config,
            year,
            demand.shape[1],
            admissibility_gate=getattr(
                config, "pjm_interface_feed_admissibility_gate", False
            ),
        )
        if tif_out is None:
            logger.warning(
                "pjm_measured_interface_limits: no transfer-interface-limits "
                "clean partition for %d — static TTC kept (run "
                "scripts/data/curate_transfer_interface_limits.py)",
                year,
            )
        else:
            ttc, ttc_import = tif_out

    # NYISO external seam deliverability envelope (nyiso-125, ScenarioConfig.
    # nyiso_seam_deliverability_envelope): the two border links whose external
    # ties land unambiguously in ONE NYISO load zone -- NYISO_external>NYC
    # (Zone J) and NYISO_external>Long_Island (Zone K) -- trade their flat
    # SYMMETRIC static rating for NYISO's own measured DIRECTIONAL HOURLY
    # envelope off the MIS P-32 posting. Upstate_West and Capital_Hudson keep
    # their statics: their envelopes are refused on identification because
    # SCH - PJ - NY spans the Central-East cutset and no public source splits it
    # (data.nyiso_seam_envelope docstring; rule 20 [R-DOF]). Applied here, after
    # the monthly/LCR overrides, so the measured envelope supersedes the
    # statics on its two links while every other link keeps the run's own TTC.
    # NYISO FULL-SEAM PAR attribution (nyiso-127, ScenarioConfig.
    # nyiso_seam_par_attribution): rebuild ALL FOUR NYISO_external border-link
    # caps from the measured MIS P-32 per-neighbour schedules. Each posted row
    # goes to the model zone its ties physically land in (Gold Book external
    # interconnections); the one row that does NOT land in a single zone --
    # SCH - PJ - NY, which spans the Central-East cutset -- is split hour by hour
    # by NYISO's OWN published NY-NJ PAR interchange percentages, conditioned on
    # published PAR availability (MIS P-33 outSched). This SUPERSEDES the
    # nyiso-125 two-link envelope rather than stacking on it (rule 19
    # [R-ONE-MECH]): it computes those same two links from the same measured
    # rows, so exactly one of the two mechanisms is applied.
    if getattr(config, "nyiso_seam_par_attribution", False) and iso == "NYISO":
        from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE
        from market_sim.data.nyiso_par_attribution import (
            nyiso_par_attributed_ttc_hourly,
        )

        ttc, ttc_import = nyiso_par_attributed_ttc_hourly(
            np.asarray(ttc, dtype=float), iso_config, year, demand.shape[1]
        )
        logger.info(
            "%s %d: nyiso_seam_par_attribution — all four border links follow "
            "the measured p%.0f directional envelope of the ATTRIBUTED seam "
            "(SCH - PJ - NY split by the published PAR shares under published "
            "PAR availability); supersedes nyiso_seam_deliverability_envelope",
            iso,
            year,
            NYISO_SEAM_FLOW_PERCENTILE,
        )
    elif (
        getattr(config, "nyiso_seam_deliverability_envelope", False) and iso == "NYISO"
    ):
        from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE
        from market_sim.data.nyiso_seam_envelope import nyiso_seam_ttc_hourly

        ttc, ttc_import = nyiso_seam_ttc_hourly(
            np.asarray(ttc, dtype=float), iso_config, year, demand.shape[1]
        )
        logger.info(
            "%s %d: nyiso_seam_deliverability_envelope — NYC / Long_Island "
            "border links follow the measured p%.0f directional seam envelope "
            "(Upstate_West / Capital_Hudson keep their statics: refused on "
            "identification, nyiso-125 Phase 0)",
            iso,
            year,
            NYISO_SEAM_FLOW_PERCENTILE,
        )

    # ERCOT West Texas Export corridor VRE curtailment-share driver (WP-B): a
    # per-(zone, hour) ceiling on West/Panhandle wind & solar reproducing the
    # sub-zonal Permian/CREZ nodal congestion the 8-zone reduction cannot resolve.
    # Reads the derived congestion-share table and the model's OWN net-load, so it
    # regenerates forward. Skipped only when the bound is delivered-pinned (the
    # delivered-as-CF renewables already embed curtailment and the ceiling would
    # double-count); a measured-potential or reference-rate grossed-up bound
    # keeps the ceiling, exactly as the forecast leg pairs them (ercot-252).
    wind_curtail_share = None
    solar_curtail_share = None
    if getattr(config, "ercot_wtx_curtailment_driver", False) and iso == "ERCOT":
        if _renewable_bound_is_delivered_pinned(iso, year):
            logger.warning(
                "ercot_wtx_curtailment_driver: %d renewable bound is "
                "delivered-pinned — curtailment ceiling skipped to avoid "
                "double-curtailment",
                year,
            )
        else:
            from market_sim.config import paths as _paths
            from market_sim.data.curtailment_share import (
                wtx_curtail_multipliers,
                wtx_family_curtail_multipliers,
            )

            # System net-load on the potential convention (fleet net-load drag):
            # demand minus uncurtailed wind & solar potential, summed over zones.
            net_load = (
                demand.sum(axis=0)
                - (np.asarray(wind_cap)[:, None] * wind_cf).sum(axis=0)
                - (np.asarray(solar_cap)[:, None] * solar_cf).sum(axis=0)
            )
            _depth_w = float(getattr(config, "ercot_wtx_curtail_depth_wind", 0.0))
            _depth_s = float(getattr(config, "ercot_wtx_curtail_depth_solar", 0.0))
            # ercot-165: the UNPOOLED diurnal-family variant gives each corridor
            # zone its own measured share instead of broadcasting one saturating
            # pooled union to both (rule 19 [R-ONE-MECH] on the Panhandle
            # interface). Same two depths, same axis, same forward story.
            _unpooled = bool(getattr(config, "ercot_wtx_curtail_unpooled", False))
            if _unpooled:
                mult = wtx_family_curtail_multipliers(
                    net_load,
                    list(zone_names),
                    depth_wind=_depth_w,
                    depth_solar=_depth_s,
                    panhandle_owner=str(
                        getattr(config, "ercot_wtx_panhandle_owner", "tie")
                    ),
                    reference_dir=_paths.RAW_DIR / "reference",
                )
            else:
                mult = wtx_curtail_multipliers(
                    net_load,
                    list(zone_names),
                    depth_wind=_depth_w,
                    depth_solar=_depth_s,
                    reference_dir=_paths.RAW_DIR / "reference",
                )
            if mult is None:
                logger.warning(
                    "ercot_wtx_curtailment_driver: no derived share table for %d "
                    "— ceiling skipped (run "
                    "scripts/data/derive_ercot_wtx_curtailment_share.py)",
                    year,
                )
            else:
                wind_curtail_share, solar_curtail_share = mult
                logger.info(
                    "ercot_wtx_curtailment_driver: %d West/Panhandle VRE ceiling "
                    "active (depth wind=%.4f solar=%.4f, %s)",
                    year,
                    _depth_w,
                    _depth_s,
                    (
                        "unpooled families, panhandle_owner="
                        + str(getattr(config, "ercot_wtx_panhandle_owner", "tie"))
                        if _unpooled
                        else "pooled share"
                    ),
                )
    # SPP wind curtailment ceiling (SPP-58, config.spp_curtailment_ceiling,
    # default off -> byte-identical no-op). SPP's 2-zone reduction collapses the
    # SPS / Texas-Panhandle and western Kansas / Oklahoma export pockets that do
    # the real curtailing, so the LP re-curtails 0.17-0.26 % of a bound grossed
    # up by 9.65 %. The ceiling supersedes the oversupply allocation rather than
    # stacking on it (rule 19 [R-ONE-MECH], enforced in data.renewables), and is
    # skipped on a delivered-pinned bound for the same reason ERCOT's is: there
    # is no gross-up headroom to remove and the ceiling would curtail energy the
    # market actually delivered.
    if getattr(config, "spp_curtailment_ceiling", False) and iso == "SPP":
        if _renewable_bound_is_delivered_pinned(iso, year):
            logger.warning(
                "spp_curtailment_ceiling: %d wind bound is delivered-pinned — "
                "ceiling skipped to avoid double-curtailment",
                year,
            )
        else:
            from market_sim.config import paths as _spp_paths
            from market_sim.data.curtailment_share import spp_curtail_multipliers

            # System net load on the potential convention, identical to the
            # ERCOT leg above: demand minus uncurtailed wind & solar potential.
            _spp_net_load = (
                demand.sum(axis=0)
                - (np.asarray(wind_cap)[:, None] * wind_cf).sum(axis=0)
                - (np.asarray(solar_cap)[:, None] * solar_cf).sum(axis=0)
            )
            _spp_depth = float(getattr(config, "spp_curtail_depth_wind", 0.0))
            _spp_mult = spp_curtail_multipliers(
                _spp_net_load,
                list(zone_names),
                depth_wind=_spp_depth,
                reference_dir=_spp_paths.RAW_DIR / "reference",
            )
            if _spp_mult is None:
                logger.warning(
                    "spp_curtailment_ceiling: no derived share table for %d — "
                    "ceiling skipped (run "
                    "scripts/data/derive_spp_curtailment_share.py)",
                    year,
                )
            else:
                wind_curtail_share, solar_curtail_share = _spp_mult
                logger.info(
                    "spp_curtailment_ceiling: %d wind ceiling active on both "
                    "zones (depth=%.6f, mean ceiling %.4f)",
                    year,
                    _spp_depth,
                    float(np.mean(wind_curtail_share)),
                )
    # Aggregate interface limits (CAISO's simultaneous WECC import cap): resolve
    # the configured link groups to flow-column indices for the LP. Empty (no
    # extra rows) for ISOs without an interface_limits entry.
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )
    # The limit list that BUILT ``interface_groups``, kept in lockstep so a
    # later consumer can locate a named group by index. The MISO block below
    # rebuilds the groups from a DIFFERENT list, so this must be reassigned
    # there too — indexing iso_config.interface_limits after that rebuild
    # would address the wrong row.
    effective_interface_limits = list(iso_config.interface_limits)
    # MISO per-zone seasonal CIL/CEL deliverability groups: replace the static
    # summer ``MISO_CIL_*`` fallbacks baked into _miso_config with per-season
    # hourly caps from the LOLE Study Report data (scope decision D7 — the
    # NYISO monthly-TTC pattern, fed from data/capacity_deliverability instead
    # of a constants table). Always on for MISO: the measured seasonal limits
    # ARE the internal congestion structure (rule #10-admissible — they
    # regenerate every planning year from forward drivers). Falls back to the
    # static summer caps when the clean partition is absent (never silent-zero).
    if iso == "MISO":
        from market_sim.model.transmission import build_miso_deliverability_groups

        seasonal_groups = build_miso_deliverability_groups(
            iso_config.links, year, demand.shape[1]
        )
        if seasonal_groups:
            static_limits = [
                lim
                for lim in iso_config.interface_limits
                if not lim.name.startswith("MISO_CIL_")
            ]
            interface_groups = (
                build_interface_groups(iso_config.links, static_limits)
                + seasonal_groups
            )
            # Groups are now static_limits-ordered; the seasonal groups carry
            # no InterfaceLimit of their own and are appended after, so the
            # named-group lookup below stays valid over the static prefix.
            effective_interface_limits = list(static_limits)
            logger.info(
                "MISO %d: seasonal CIL/CEL interface caps on %d zone group(s) "
                "(per-season hourly vectors from the LOLE deliverability data; "
                "static summer fallbacks replaced)",
                year,
                len(seasonal_groups),
            )
        else:
            logger.warning(
                "MISO %d: capacity-deliverability clean partition absent — "
                "falling back to static PY2025-26 summer CIL/CEL caps; run "
                "scripts/data/curate_capacity_deliverability.py",
                year,
            )
    # miso-255 miso_import_sil_measured_envelope (MISO-only, GATED default off):
    # REPLACE the 8,700 MW bidirectional MISO_simultaneous_import scalar -- the
    # published Capacity Import Limit, a PRA/LOLE accreditation construct used
    # as the hourly energy bound in BOTH directions -- with MISO's own measured
    # coincident boundary transfer envelope per direction. Rule 14
    # [R-ACCURATE]; replaces, never stacks (rule 19).
    #
    # IT MUST LIVE HERE, NOT ONLY IN runner.py. The backcast/calibration path
    # builds its OWN interface_groups above and never enters
    # runner.run_scenario_iso, which is the forecast/scenario front end -- the
    # exact trap the comment at the caiso_endogenous_wecc_node block records,
    # and the one this mechanism fell into: a first pair of screen shards
    # solved with the flag set and the arm silently inert (miso-255). It is
    # keyed off ``effective_interface_limits`` because the MISO seasonal block
    # above rebuilds the groups from ``static_limits``.
    if iso == "MISO" and getattr(config, "miso_import_sil_measured_envelope", False):
        from market_sim.model.transmission import apply_miso_measured_sil_envelope

        interface_groups, _sil_info = apply_miso_measured_sil_envelope(
            interface_groups,
            effective_interface_limits,
            year,
            demand.shape[1],
            percentile=getattr(config, "miso_seam_flow_percentile", None),
            hour_ending_key=getattr(
                config, "miso_seam_envelope_hour_ending_key", False
            ),
        )
        if _sil_info is not None:
            logger.info(
                "MISO %d: aggregate simultaneous-transfer limit REPLACED by "
                "the measured coincident boundary envelope -- declared scalar "
                "%.0f MW -> import mean %.0f / max %.0f MW, export mean %.0f / "
                "max %.0f MW; import below the scalar in %d h, export in %d h",
                year,
                _sil_info["declared_scalar_mw"],
                _sil_info["import_env_mean_mw"],
                _sil_info["import_env_max_mw"],
                _sil_info["export_env_mean_mw"],
                _sil_info["export_env_max_mw"],
                _sil_info["hours_import_below_scalar"],
                _sil_info["hours_export_below_scalar"],
            )
        else:
            logger.warning(
                "MISO %d: miso_import_sil_measured_envelope armed but NO "
                "envelope resolved -- the aggregate limit keeps its declared "
                "scalar and this run is NOT an armed run",
                year,
            )
    # Measured PJM EAST interface cut (pjm_east_interface_cut, backcast
    # overlay, default off — pjm-cong-1, diagnosis §10.5): one one-sided
    # hourly aggregate group capping Flow(Central_PA→EMAAC) +
    # Flow(SWMAAC→EMAAC) at the measured "Average Eastern" limit — PJM's
    # EASTERN reactive transfer interface, whose monitored EHV set spans BOTH
    # model links (Manual 03 §3.8), so the joint cap is the faithful
    # reduced-network reading; the per-link pjm_measured_interface_limits
    # overlay keeps its (now dominated) Central_PA→EMAAC bound. Zero fitted
    # scalars; no-op off the flag, for non-PJM, or when the year has no
    # clean partition (byte-identical).
    if getattr(config, "pjm_east_interface_cut", False) and iso == "PJM":
        from market_sim.data.transfer_interface_limits import (
            pjm_eastern_interface_hourly,
        )
        from market_sim.model.transmission import (
            build_pjm_east_interface_cut_groups,
        )

        east_lim = pjm_eastern_interface_hourly(
            year,
            demand.shape[1],
            admissibility_gate=getattr(
                config, "pjm_interface_feed_admissibility_gate", False
            ),
        )
        if east_lim is None:
            logger.warning(
                "pjm_east_interface_cut: no transfer-interface-limits clean "
                "partition (or no Average Eastern series) for %d — joint "
                "EMAAC cut skipped (run "
                "scripts/data/curate_transfer_interface_limits.py)",
                year,
            )
        else:
            east_groups = build_pjm_east_interface_cut_groups(
                iso_config.links, east_lim
            )
            # pjm-168: when pjm_interface_feed_admissibility_gate judged the
            # series inadmissible it returns an all-+inf limit, i.e. the
            # declared "joint EMAAC import cut is NOT APPLIED this year" posture
            # (PRECOMMIT-pjm167-interface-feed-admissibility §1). Adding a
            # degenerate non-binding group would be a no-op row in the LP and
            # made the summary below reduce over an empty finite subset. The
            # gate has already emitted its own loud WARNING upstream, so drop
            # the group and say nothing more here (rule 19 [R-ONE-MECH]).
            finite_east = east_lim[np.isfinite(east_lim)]
            if finite_east.size == 0:
                east_groups = []
            if east_groups:
                interface_groups = interface_groups + east_groups
                logger.info(
                    "PJM %d: measured EAST interface cut on %d link(s) — "
                    "joint EMAAC import cap follows Average Eastern "
                    "(hourly %0.0f-%0.0f MW, mean %0.0f)",
                    year,
                    len(east_groups[0][0]),
                    float(np.min(finite_east)),
                    float(np.max(finite_east)),
                    float(np.mean(finite_east)),
                )

    # Measured PJM AP-SOUTH interface cut (pjm_apsouth_interface_cut, backcast
    # overlay, default off — pjm-134, FINDING-pjm134 §4): the western→MAD twin
    # of the EAST cut above. ONE one-sided hourly aggregate group capping
    # Flow(West_APS→SWMAAC) + Flow(West_APS→Dominion) at the measured AP-South
    # limit — the aggregate western→MAD 500 kV flowgate, which
    # constants.PJM_INTERFACE_LINK_MAP's own note records as spanning BOTH
    # model links while the per-link overlay applies it to West_APS→SWMAAC
    # alone (leaving West_APS→Dominion on a 3,000 MW static the real interface
    # does not have). Rule 19: this REPLACES that flagged misalignment rather
    # than stacking on it — the joint cap dominates the per-link bound. Zero
    # fitted scalars; no-op off the flag, for non-PJM, or when neither cut link
    # exists (byte-identical).
    if getattr(config, "pjm_apsouth_interface_cut", False) and iso == "PJM":
        from market_sim.data.transfer_interface_limits import (
            pjm_apsouth_interface_hourly,
        )
        from market_sim.model.transmission import (
            build_pjm_apsouth_interface_cut_groups,
        )

        aps_lim = pjm_apsouth_interface_hourly(year, demand.shape[1])
        aps_groups = build_pjm_apsouth_interface_cut_groups(iso_config.links, aps_lim)
        if aps_groups:
            interface_groups = interface_groups + aps_groups
            logger.info(
                "PJM %d: measured AP-SOUTH interface cut on %d link(s) — "
                "joint western→MAD cap follows AP-South "
                "(hourly %0.0f-%0.0f MW, mean %0.0f)",
                year,
                len(aps_groups[0][0]),
                float(np.min(aps_lim[np.isfinite(aps_lim)])),
                float(np.max(aps_lim[np.isfinite(aps_lim)])),
                float(np.mean(aps_lim[np.isfinite(aps_lim)])),
            )

    # [measured: EIA-930 per-corridor (month × hour-of-day) p95 net-flow
    #  envelope → corridor import/export caps | forecast substitute:
    #  caiso_corridor_atc_forward — the shared
    #  transmission.forward_corridor_interface_groups capability envelope,
    #  which the forecast runner also wires (Stage 5); the measured branch
    #  below is a backcast overlay, plan §3.1]
    # Measured WECC corridor deliverability envelope (CAISO per-hub only): cap
    # each corridor link's import-direction flow at the per-(month × hour-of-day)
    # p95 measured net import (an ATC proxy that tightens midday), so the LP can
    # no longer pull the neighbors' idle thermal tranches over the cheap-priced
    # hub up to the 8.3 GW simultaneous cap. One-sided hourly upper bounds, added
    # to the interface groups; export keeps the physical TTC. No-op off the flag
    # or when the year has no measured interchange (byte-identical).
    forward_atc = caiso_corridors and getattr(
        config, "caiso_corridor_atc_forward", False
    )
    if forward_atc or (
        caiso_corridors and getattr(config, "caiso_corridor_flow_limit", False)
    ):
        from market_sim.model.transmission import build_caiso_corridor_flow_groups

        corridor_export_env = (
            None  # measured branch fills it; forward ATC leaves it off
        )
        if forward_atc:
            # FORWARD ATC: corridor TTC × posted-ATC base fraction × forward solar
            # derate (CISO solar / demand), a capability limit — not the measured
            # p95 flow (CLAUDE.md #12). Supersedes the measured envelope when on.
            from market_sim.model.transmission import forward_corridor_atc_envelope

            corridor_env = forward_corridor_atc_envelope(
                iso_config, iso, year, demand.shape[1]
            )
            cap_label = "FORWARD ATC (TTC × ATC-frac × solar derate)"
        else:
            from market_sim.data.eia_loader import measured_corridor_flow_envelope

            corridor_env = measured_corridor_flow_envelope(iso, year, demand.shape[1])
            # Symmetric measured export-deliverability ceiling: caps each
            # corridor's export (negative) flow at its p95 net export, which
            # collapses to ~0 in the evening ramp where the corridor reliably
            # net-imports — forbidding the LP's unphysical evening wheel-out of
            # cheap CA gas that over-dispatched CC_REGULAR and inflated the
            # evening LMP. A capability envelope the LP clears below, not the
            # hourly residual (rule #12).
            corridor_export_env = measured_corridor_flow_envelope(
                iso, year, demand.shape[1], direction="export"
            )
            from market_sim.config.interchange_config import (
                CAISO_CORRIDOR_FLOW_PERCENTILE,
            )

            cap_label = f"measured p{CAISO_CORRIDOR_FLOW_PERCENTILE:g} ATC proxy"
        if corridor_env:
            corridor_groups = build_caiso_corridor_flow_groups(
                iso_config.links,
                corridor_env,
                export_envelope=None if forward_atc else corridor_export_env,
            )
            interface_groups = interface_groups + corridor_groups
            exp_note = ""
            if corridor_export_env:
                exp_note = (
                    "; export-direction cap on (evening net-export ~0 → no wheel-out): "
                    f"median export DSW {float(np.median(corridor_export_env.get('WECC_DSW', [np.nan]))) / 1000.0:.1f} GW "
                    f"/ PNW {float(np.median(corridor_export_env.get('WECC_PNW', [np.nan]))) / 1000.0:.1f} GW"
                )
            logger.info(
                "%s %d: WECC corridor deliverability cap on %d link(s) — %s; "
                "median import DSW %.1f GW / PNW %.1f GW; midday tighter%s",
                iso,
                year,
                len(corridor_groups),
                cap_label,
                float(np.median(corridor_env.get("WECC_DSW", [np.nan]))) / 1000.0,
                float(np.median(corridor_env.get("WECC_PNW", [np.nan]))) / 1000.0,
                exp_note,
            )

    # PJM congestion lever (Lever A): cap each PJM_external→border link's signed
    # flow per hour at the measured per-border net-interchange envelope, so the
    # priced external star node can no longer wheel ~30 GW uncongested into the 5
    # border zones (the copper-plate bypass). Mirrors the CAISO corridor cap
    # (asymmetric per-hour interface groups); no-op off the flag, for non-PJM, or
    # when the measured tie file is absent (byte-identical).
    if getattr(config, "pjm_congestion", False) and iso == "PJM" and priced_interchange:
        from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
        from market_sim.config.interchange_config import IMPORT_ZONE
        from market_sim.data.eia_loader import pjm_zonal_interchange_envelope
        from market_sim.model.transmission import build_pjm_external_flow_groups

        env = pjm_zonal_interchange_envelope(
            year, zone_names, demand.shape[1], PJM_EXTERNAL_FLOW_PERCENTILE
        )
        if env is not None:
            import_cap, export_cap = env
            ext_groups = build_pjm_external_flow_groups(
                iso_config.links, import_cap, export_cap, zone_names
            )
            interface_groups = interface_groups + ext_groups
            # Per-border median caps (GW) for the log: dominant direction generous,
            # minor direction ~0 (EMAAC import / Dominion export / interior zones).
            border_rows = {
                ln.to_zone
                for ln in iso_config.links
                if ln.from_zone == IMPORT_ZONE.get("PJM")
            }
            zone_idx = {z: i for i, z in enumerate(zone_names)}
            cap_note = "; ".join(
                f"{z.replace('PJM_', '')} imp {np.median(import_cap[zone_idx[z]]) / 1000.0:.1f}"
                f"/exp {np.median(export_cap[zone_idx[z]]) / 1000.0:.1f} GW"
                for z in sorted(border_rows)
                if z in zone_idx
            )
            logger.info(
                "PJM %d: external-node deliverability cap (p%g) on %d link(s) — %s",
                year,
                PJM_EXTERNAL_FLOW_PERCENTILE,
                len(ext_groups),
                cap_note,
            )

    # Measured PJM star-node NET-POSITION cut (pjm_external_net_position_cut,
    # backcast overlay, default off — pjm-135, FINDING-pjm135 §5): the EXTERNAL
    # twin of the EAST / AP-SOUTH joint cuts above. ONE one-sided hourly
    # aggregate group capping the SUMMED injection across all five
    # PJM_external→border links — i.e. the LP's own net interchange — at the
    # measured (month × hour-of-day) p95 net-position envelope. Rule 19: this
    # REPLACES the sum-of-marginals ceiling on the aggregate question (the
    # per-border groups above cap each link at its own border's marginal p95 and
    # nothing bounds the total), it does not stack — the joint cap dominates, so
    # the per-border groups keep the locational bound while this row owns the
    # total. Zero fitted scalars: same tie-line file, same percentile, same
    # bucketing. Requires the priced star node; no-op off the flag, for non-PJM,
    # or when the year has no measured tie file (byte-identical).
    if (
        getattr(config, "pjm_external_net_position_cut", False)
        and iso == "PJM"
        and priced_interchange
    ):
        from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
        from market_sim.data.eia_loader import pjm_net_interchange_envelope
        from market_sim.model.transmission import (
            build_pjm_external_net_position_cut_groups,
        )

        net_lim = pjm_net_interchange_envelope(
            year, demand.shape[1], PJM_EXTERNAL_FLOW_PERCENTILE
        )
        if net_lim is None:
            logger.warning(
                "pjm_external_net_position_cut: no measured PJM tie-line file "
                "for %d — joint star-node net-position cut skipped",
                year,
            )
        else:
            net_groups = build_pjm_external_net_position_cut_groups(
                iso_config.links, net_lim
            )
            if net_groups:
                interface_groups = interface_groups + net_groups
                logger.info(
                    "PJM %d: measured star-node NET-position cut (p%g) on %d "
                    "link(s) — joint net import ≤ measured envelope (hourly "
                    "%0.0f-%0.0f MW, mean %0.0f)",
                    year,
                    PJM_EXTERNAL_FLOW_PERCENTILE,
                    len(net_groups[0][0]),
                    float(np.min(net_lim)),
                    float(np.max(net_lim)),
                    float(np.mean(net_lim)),
                )

    # Commercial-operation-date (COD) vintage ramp: in a backcast the fleet
    # snapshot is a recent vintage that includes units built after the solved
    # year. The ramp is now applied uniformly inside generators_to_fleet_arrays
    # (config.cod_ramp_enabled, default on) via the month-precise EIA-860
    # plant-code map — covering the ERCOT CAMPD bins and every raw EIA-860 unit
    # alike — so the per-fleet-path scaling that used to live here is gone. See
    # data.cod_ramp.

    # Whole-plant exits that retired mid-window (e.g. Mystic) are absent from
    # the single recent operable snapshot, so the COD ramp has nothing to age
    # out. Inject them into the backcast fleet base — the ramp
    # (generators_to_fleet_arrays) then dispatches each through its real
    # retirement month and zeros it after. Mirror of forecast's planned
    # additions; backcast-mode only (run_calibration is always backcast). The
    # year selects the active EIA-860 vintage; a year-matched native vintage
    # carries these exits in its own operable file and ships no retiree parquet,
    # so this returns nothing there (no double-count).
    retired_units = (
        load_retired_within_window(
            iso,
            iso_config,
            year=year,
            # miso-188 vintage-status oracle: drop retiree-channel units
            # EIA's own contemporaneous vintage marks non-OP (deactivated
            # before their formal retirement date). Default-off; byte-inert
            # while off.
            vintage_status_scope=getattr(config, "retiree_vintage_status_scope", False),
            # miso-190 partial-plant exit carry: ALSO inject units retired
            # mid-window whose plants survive, timed out at unit grain on
            # their own actual retirement months. Default-off; byte-inert
            # while off.
            partial_plant_exit_carry=getattr(config, "partial_plant_exit_carry", False),
            # SPP-48 mid-vintage-year whole-plant exit carry: inject the
            # plants a year-matched native vintage drops from BOTH sheets
            # because they retired DURING that year (Oklaunion 127, ret
            # 9/2020, 1,209.2 GWh metered). Default-off; byte-inert while
            # off, and inert wherever the whole-plant retiree parquet exists.
            mid_vintage_exit_carry=getattr(config, "mid_vintage_exit_carry", False),
            # F1 D4: the measured heat-rate swaps reach the retiree channel,
            # at this solve year's own rate (the operable loader's flags).
            **_measured_heat_rate_flags(config),
        )
        if config.mode == "backcast"
        else []
    )

    # Mothballed-but-operating re-carry (the Cottonwood lane): OA units the
    # snapshot's OP filter drops but the year-matched vintage marks OP — the
    # partial-mothball blind spot between the OP filter and the whole-plant
    # retiree channel. Gated default-off (carry_operating_mothballs),
    # backcast-only, per-unit, zero fitted DOF (the vintage's own status is
    # the availability oracle). Joins retired_units at both injection sites
    # below so the carried units are binned/dispatched exactly like the rest
    # of the fleet. See fleet.load_mothballed_but_operating and
    # docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md.
    if config.mode == "backcast" and config.carry_operating_mothballs:
        retired_units = retired_units + load_mothballed_but_operating(
            iso,
            iso_config,
            year=year,
            # miso-190: widen the snapshot status set {OA} -> {OA, OS, SB}
            # under the same vintage-OP oracle (Big Cajun 2-1, Warrick-2).
            # Default-off; byte-inert while off.
            partial_plant_exit_carry=getattr(config, "partial_plant_exit_carry", False),
            **_measured_heat_rate_flags(config),
        )

    # Resolve the per-plant bin frame, then build the base fleet and the
    # LP-ready dispatch fleet through the SHARED builders
    # (fleet.build_base_fleet / fleet.build_dispatch_fleet) — the same
    # bodies the forecast runner calls (orchestrator-unification Stage 6).
    # Backcast-specific inputs enter as explicit parameters: the year-matched
    # EIA-860 vintage, the curated ERCOT bin sheet at this solve year's
    # vintage, the measured hydro monthly budgets, the biomass-injection
    # drop, the historical import placement (after hydro), and the
    # emission-override seam (off — backcast per-plant rates enter via the
    # bin artifacts and the v2 hook inside bins_to_fleet, G-39 §9.6).
    campd_bins = (
        load_campd_bins(
            config.campd_bins_path,
            year=year,
            capacity_reconcile_path=(
                config.cc_capacity_reconcile_path
                if config.cc_capacity_reconcile
                else None
            ),
            # R-ERCOT (AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24
            # §5.3.2 (b)): the curated sheet is one heat-rate snapshot for
            # every year; in a backcast re-resolve each row at THIS solve
            # year through the F1 hierarchy (measured CAMPD year row ->
            # pooled -> year-matched eGRID -> sheet). The five measured flags
            # and the vintage flag are coerced off outside mode="backcast",
            # so every forecast / hindcast bin frame is byte-identical.
            heat_rate_year=(
                year if getattr(config, "mode", "forecast") == "backcast" else None
            ),
            measured_flags=_measured_heat_rate_flags(config),
            egrid_year_match=bool(
                getattr(config, "eia860_vintage_tracks_solve_year", False)
            ),
            iso=iso,
        )
        if config.use_campd_bins and iso == "ERCOT"
        else None
    )
    if (
        campd_bins is None
        and getattr(config, "plant_level_fleet", False)
        and thermal_tranche_overrides(iso)
    ):
        # Per-plant thermal fleet with ERCOT's smoothed rising offer curve:
        # synthesize the per-plant bins frame (committed / coal must-run from
        # the CAMPD thermal-tranche artifact). An empty synthesis (no
        # artifact coverage) leaves campd_bins None and falls through to the
        # legacy aggregate path inside build_base_fleet (n_bins=0 keeps the
        # per-plant identity).
        # NOTE: this is the BACKCAST's own copy of the bin synthesis in
        # ``fleet.assembly.load_or_synthesize_bins`` — every fleet-sourcing
        # flag has to be forwarded HERE too, or a calibration solve silently
        # ignores it while ``run_config.json`` records it as on
        # (``measured_ct_heat_rates`` was byte-identical to its control for
        # exactly this reason, nyiso-89). Covered by
        # tests/unit/data/test_measured_ct_heat_rates.py.
        synth = fleet_to_bins(
            load_fleet_from_csv(
                iso,
                iso_config,
                year=year,
                measured_ct_heat_rates=config.measured_ct_heat_rates,
                measured_coal_heat_rates=config.measured_coal_heat_rates,
                measured_st_heat_rates=config.measured_st_heat_rates,
                measured_cc_heat_rates=config.measured_cc_heat_rates,
                measured_chp_heat_rates=config.measured_chp_heat_rates,
                cc_steam_part_capacity=config.cc_steam_part_capacity,
                cc_steam_part_reclass=config.cc_steam_part_reclass,
                egrid_identity_heat_rates=config.egrid_identity_heat_rates,
                egrid_family_heat_rates=config.egrid_family_heat_rates,
                egrid_steam_collapse_heat_rates=config.egrid_steam_collapse_heat_rates,
                cc_block_summer_rating=config.cc_block_summer_rating,
            )
            + retired_units,
            iso,
            config,
        )
        if not synth.empty:
            campd_bins = synth
    fleet_base = build_base_fleet(
        campd_bins,
        iso,
        iso_config,
        zone_names,
        config,
        retired_units,
        [],  # planned additions are forecast-only; the vintage carries built units
        year,
        None,  # confirmed exits ride the year-matched vintage in a backcast
        vintage_year=year,
        # Gas/coal are dispatched via the CAMPD bins; biomass is injected as
        # a must-run resource (run_calibration_full). Oil is kept as its own
        # raw LP unit so it dispatches as the scarcity peaker it is — the
        # backcast's historical divergence from the runner's oil-excluding
        # default set (see build_base_fleet's nonthermal_exclude note).
        # gas_st mirrors the default set's D-25 addition: ERCOT's gas-steam
        # rows classed gas_ct before the taxonomy fix and were excluded here;
        # without it they would re-enter as raw duplicates of curated bins.
        nonthermal_exclude=(
            frozenset({"gas_cc", "gas_ct", "gas_st", "coal", "biomass"})
            if iso == "ERCOT"
            else None
        ),
        legacy_n_bins=(
            0
            if getattr(config, "plant_level_fleet", False)
            else config.heat_rate_bin_count
        ),
    )
    fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = build_dispatch_fleet(
        fleet_base,
        campd_bins,
        import_generators,
        iso,
        year,
        zone_names,
        config,
        hydro_backfill_year=hydro_backfill_year,
        hydro_eia930_monthly=hydro_eia930_monthly,
        hydro_forecast_budget=hydro_forecast_budget,
        hydro_year=hydro_year,
        drop_biomass_units=inject_biomass_mustrun,
        imports_after_hydro=True,
        apply_emission_overrides=False,
    )
    # PJM DA virtual-bid layer (G-22 lever B, config.pjm_da_virtual_bids,
    # PJM-gated, default off): the year's measured HOURLY submitted INC/DEC
    # bid curves as pseudo-units with endogenous clearing (data.virtual_bids
    # module docstring has the structure/admissibility notes). Units append
    # to the plain fleet list here; their hourly MW bounds apply after the
    # arrays are built (availability for INC, min_gen for DEC) and their
    # hourly bid prices land on their fuel_prices rows before assemble_mc.
    virtual_profiles: dict = {}
    virtual_price_rows: dict = {}
    if getattr(config, "pjm_da_virtual_bids", False) and iso == "PJM":
        from market_sim.data.virtual_bids import build_pjm_da_virtual_units

        virtual_units, virtual_profiles, virtual_price_rows = (
            build_pjm_da_virtual_units(config, iso, year, demand, zone_names)
        )
        fleet = fleet + virtual_units
        # fuel_fracs is row-parallel with the fleet list (apply_coal_tranches
        # indexes it by generator position): virtual units pass their full
        # "fuel" cost through (frac 1.0 = no take-or-pay discount).
        fuel_fracs = fuel_fracs + [1.0] * len(virtual_units)
    # NYISO SCR/EDRP emergency demand response (config.nyiso_scr_edrp, NYISO-
    # gated, default off): one price-responsive supply block per model zone at
    # the zone's Gold-Book-registered DR MW and the EDRP-floor strike, appended
    # to the plain fleet list like the virtual units above. It clears the energy
    # balance only when the zone LBMP exceeds the strike (endogenous scarcity
    # trigger); the summer/winter capability-period availability is stamped on
    # the arrays after they are built (inject_nyiso_dr_availability, below).
    if getattr(config, "nyiso_scr_edrp", False) and iso == "NYISO":
        from market_sim.data.nyiso_demand_response import build_nyiso_dr_generators

        dr_units = build_nyiso_dr_generators(config, year)
        fleet = fleet + dr_units
        # Row-parallel with the fleet list; DR blocks carry heat_rate 0 so their
        # fuel frac is inert (frac 1.0, matching the virtual-unit convention).
        fuel_fracs = fuel_fracs + [1.0] * len(dr_units)
    # CT_PEAKER reliability must-run floor: pass the peakers' CAMPD/CEMS hourly
    # on/off shape so the floor starts/stops with the real unit (zero in every
    # hour the plant did not report load), instead of being smeared flat. The
    # parasitic factor only scales magnitude, which the per-month shape
    # normalization removes, so a bare gross series is enough.
    ct_campd_shape = None
    if getattr(config, "ct_mustrun_per_plant", False):
        from market_sim.data import campd as _campd

        _states = _campd.states_for_iso(iso)
        if _states:
            _cdf = _campd.load_campd_hourly(_states, [config.weather_year])
            if not _cdf.empty:
                ct_campd_shape = _campd.plant_hourly_net(
                    _cdf, {}, config.weather_year, hours=config.hours
                )
    # NET-load window series for the commitment floors
    # (config.commitment_floor_window_netload, SPP-66, owner ruling "Shared
    # gate" 2026-09-20). THIS is the seam every calibration run and every
    # fleet_only reconstruction takes -- runner.py has its own, separate
    # build, and BOTH are wired, because a gate armed on only one of them is
    # inert in exactly the lane that would use it (measured: the first wiring
    # of this mechanism touched runner.py alone and the armed arm reproduced
    # the control's floors cell-for-cell).
    #
    # Built ONLY when the gate is armed, so an unarmed run does exactly the
    # array work it did before and every committed bundle is byte-identical.
    # Same construction as runner.py's six existing net-load sites -- demand
    # less AVAILABLE wind/solar -- so no new scalar enters (rules 21 [R-DOF] /
    # 24 [R-REGISTRY]), and it is the MODEL's own capacity x CF rather than
    # measured VRE output, so it regenerates for a forecast year off the
    # evolved fleet (rule 13 [R-MEASURED]).
    _floor_netload_shape = None
    if getattr(config, "commitment_floor_window_netload", False):
        _floor_netload_shape = (
            demand.sum(axis=0)
            - (np.asarray(wind_cap, dtype=float)[:, None] * wind_cf).sum(axis=0)
            - (np.asarray(solar_cap, dtype=float)[:, None] * solar_cf).sum(axis=0)
        )
    fleet_arrays = generators_to_fleet_arrays(
        fleet,
        zone_names,
        hours=config.hours,
        iso=iso,
        config=config,
        load_shape=demand.sum(axis=0),
        netload_shape=_floor_netload_shape,
        ct_campd_shape=ct_campd_shape,
        year=config.weather_year,
    )
    inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)
    # NYISO SCR/EDRP demand-response blocks: overwrite the flat pseudo-gen
    # availability (1 - eford = 1.0) with the summer/winter capability-period
    # seasonal profile — the mirror of inject_offshore_wind_availability. A
    # no-op unless config.nyiso_scr_edrp is on, the ISO is NYISO, and DR rows
    # are present (the function guards internally).
    if getattr(config, "nyiso_scr_edrp", False) and iso == "NYISO":
        from market_sim.data.nyiso_demand_response import inject_nyiso_dr_availability

        inject_nyiso_dr_availability(fleet_arrays, config, iso, year, list(zone_names))
    # caiso-110: shape the endogenous WECC-West VRE / hydro / nuclear pseudo-gens
    # to their MEASURED hourly output (availability = measured MW / nameplate),
    # the mirror of the NYISO-DR / offshore-wind availability overlays above.
    # Dispatchable West thermal (coal/gas) keeps its flat 1.0 (economic to
    # nameplate). No-op unless the endogenous node is on (rows absent otherwise).
    if _endogenous_wecc and _wecc_west_avail:
        _uid_to_row = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
        for _uid, _series in _wecc_west_avail.items():
            _r = _uid_to_row.get(_uid)
            if _r is not None:
                fleet_arrays.availability[_r, : config.hours] = _series[: config.hours]
    # Net-load-indexed ST_GAS + CT_PEAKER reliability-drag min-gen floors —
    # the single shared gate-and-log wrapper both orchestrators call
    # (fleet.apply_netload_drag_floors, orchestrator-unification Stage 6).
    # Gates internally on gas_st_netload_drag / ct_netload_drag; net-load uses
    # the same LP-served convention as the other net-load consumers below.
    apply_netload_drag_floors(
        fleet_arrays,
        fleet,
        demand,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        config,
        iso,
        year,
    )
    # PJM DA virtual-bid layer: hourly MW bounds for the pseudo-units built
    # above (INC upper bound via availability, DEC lower bound via min_gen).
    if virtual_profiles:
        from market_sim.data.virtual_bids import apply_virtual_profiles

        n_bound = apply_virtual_profiles(fleet_arrays, virtual_profiles)
        logger.info(
            "PJM %d DA virtual-bid layer: hourly bounds applied to %d pseudo-unit rows",
            year,
            n_bound,
        )
    # ══════════════════════════════════════════════════════════════════════
    # BACKCAST MEASURED INTERCHANGE OVERLAYS — availability / seam limits.
    # Every block below feeds a MEASURED series into the priced node's bounds
    # (CLAUDE.md rule 12: reproducible capability envelopes, never an outcome
    # pin) and is backcast-only by design (plan §3.1). None is reachable from
    # the forecast path: the forecast substitutes are noted per overlay.
    # The forward-native interchange injections live in the SHARED
    # transmission.apply_interchange_injections, called below after the mc
    # assembly (both orchestrators run it).
    # ══════════════════════════════════════════════════════════════════════
    # [measured: EIA-930 CISO diurnal interchange envelope → import/export
    #  availability shape | forecast substitute: none — the reference-price /
    #  per-hub seams price the diurnal signal instead of bounding it]
    # Shape the priced import/export node by the measured EIA-930 diurnal
    # interchange envelope (import overnight, export the midday solar glut) so
    # the node stops clearing a flat all-hours import that floors the midday
    # price. Only fires with priced interchange + the opt-in flag + a measured
    # envelope; otherwise the static node is unchanged.
    if priced_interchange and getattr(config, "interchange_shaping", False):
        from market_sim.model.transmission import inject_interchange_shape

        export_only = getattr(config, "interchange_shaping_export_only", False)
        # Per-direction envelope percentile is a ScenarioConfig field (rule
        # 24 — was an os.environ INTERCHANGE_SHAPE_IMPORT_PCT/EXPORT_PCT read
        # inside inject_interchange_shape), so the value that ran is recorded
        # in run_config.json. Both default to 90.0, reproducing the env-unset
        # behavior of every run to date.
        import_pct = getattr(config, "interchange_shape_import_pct", 90.0)
        export_pct = getattr(config, "interchange_shape_export_pct", 90.0)
        if inject_interchange_shape(
            fleet_arrays,
            iso,
            year,
            export_only=export_only,
            import_percentile=import_pct,
            export_percentile=export_pct,
        ):
            logger.info(
                "%s %d: priced node shaped by measured EIA-930 interchange "
                "envelope (%s, import p%g / export p%g)",
                iso,
                year,
                "export midday only — imports uncapped"
                if export_only
                else "import overnight / export midday",
                import_pct,
                export_pct,
            )
    # [measured: EIA-930 MISO BA-to-BA net-import envelope → seam import cap |
    #  forecast substitute: the seam's interface_limit_mw + reference prices]
    # MISO reference-price seam deliverability cap: bound each seam's
    # (PJM/SPP/South) import-band availability at the measured EIA-930 BA-to-BA
    # net-import envelope, so the model stops over-importing on the SPP/southern
    # borders MISO actually nets ~0 / net-EXPORTS over. One-sided import ceiling;
    # export bands keep their priced economics. No-op off the flag, for non-MISO,
    # or when the year has no measured interchange (byte-identical).
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "miso_seam_flow_limit", False
    ):
        from market_sim.model.transmission import inject_miso_seam_flow_limit

        # Optional round-2 import-lift: raise the deliverability percentile so the
        # priced seam clears more import in tight hours (None keeps the p90
        # default). Still a measured-duration-curve ceiling, not a residual pin.
        _seam_pct = getattr(config, "miso_seam_flow_percentile", None)
        # miso-73: envelope composition semantics — merit-order (waterfall)
        # ceiling instead of the uniform per-band derate when armed.
        _seam_merit = getattr(config, "miso_seam_envelope_merit_cap", False)
        # miso-175: read the DIBA local_time stamp as hour-ENDING (its
        # measured convention) so the (month × hod) cap key is un-rotated.
        _seam_hek = getattr(config, "miso_seam_envelope_hour_ending_key", False)
        if inject_miso_seam_flow_limit(
            fleet_arrays,
            iso,
            year,
            percentile=_seam_pct,
            merit_cap=_seam_merit,
            hour_ending_key=_seam_hek,
        ):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured EIA-930 "
                "BA-to-BA deliverability envelope (p%g; SPP/South clip toward "
                "~0 import, PJM keeps its measured eastern transfer)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE if _seam_pct is None else _seam_pct,
            )
    # Export mirror: cap each seam's net EXPORT at the measured net-export
    # envelope by raising the export bands' lower bound toward 0. Clips the PJM
    # seam (which MISO net-imports over) to ~0 export, removing the spurious
    # export of cheap MISO coal back east; SPP/South keep their measured export
    # headroom. Shares the import cap's percentile (one envelope, both
    # directions). No-op off the flag, for non-MISO, or with no measured year.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "miso_seam_export_limit", False
    ):
        from market_sim.model.transmission import inject_miso_seam_flow_limit

        _seam_pct = getattr(config, "miso_seam_flow_percentile", None)
        _seam_merit = getattr(config, "miso_seam_envelope_merit_cap", False)
        _seam_hek = getattr(config, "miso_seam_envelope_hour_ending_key", False)
        if inject_miso_seam_flow_limit(
            fleet_arrays,
            iso,
            year,
            percentile=_seam_pct,
            direction="export",
            merit_cap=_seam_merit,
            hour_ending_key=_seam_hek,
        ):
            from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam export capped at measured EIA-930 "
                "BA-to-BA net-export envelope (p%g; PJM seam clips export toward "
                "~0, SPP/South keep their measured export headroom)",
                iso,
                year,
                MISO_SEAM_FLOW_PERCENTILE if _seam_pct is None else _seam_pct,
            )
    # [measured: PJM tie-line per-neighbor flow envelope → seam import cap |
    #  forecast substitute: the seam's interface_limit_mw + reference prices]
    # PJM seam import cap: cap each of PJM's 5 reference-price seams' import
    # bands at the measured per-neighbor deliverability envelope (PJM tie-line
    # file, aggregated from border zones to neighbor level). Fixes the ~38 TWh
    # over-export by capping the LP's simultaneous full-TTC export on all 5
    # seams. No-op off the flag, for non-PJM, or with no measured tie file.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "pjm_seam_flow_limit", False
    ):
        from market_sim.model.transmission import inject_pjm_seam_flow_limit

        _pjm_pct = getattr(config, "pjm_seam_flow_percentile", None)
        if inject_pjm_seam_flow_limit(
            fleet_arrays,
            iso,
            year,
            zone_names,
            hours,
            percentile=_pjm_pct,
        ):
            from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam import capped at measured PJM "
                "tie-line deliverability envelope (p%g); each neighbor's "
                "import bands derated to its PER-NEIGHBOR (own ties) envelope",
                iso,
                year,
                PJM_SEAM_FLOW_PERCENTILE if _pjm_pct is None else _pjm_pct,
            )
    # PJM seam export cap: symmetric mirror — cap each seam's net export at
    # the measured per-neighbor export envelope.
    if getattr(config, "reference_price_interface", False) and getattr(
        config, "pjm_seam_export_limit", False
    ):
        from market_sim.model.transmission import inject_pjm_seam_flow_limit

        _pjm_pct = getattr(config, "pjm_seam_flow_percentile", None)
        if inject_pjm_seam_flow_limit(
            fleet_arrays,
            iso,
            year,
            zone_names,
            hours,
            percentile=_pjm_pct,
            direction="export",
        ):
            from market_sim.config.constants import PJM_SEAM_FLOW_PERCENTILE

            logger.info(
                "%s %d: reference-price seam export capped at measured PJM "
                "tie-line net-export envelope (p%g); each neighbor's export "
                "bands floored to its PER-NEIGHBOR (own ties) envelope",
                iso,
                year,
                PJM_SEAM_FLOW_PERCENTILE if _pjm_pct is None else _pjm_pct,
            )
    # ── end of the backcast measured interchange overlays (availability) ──
    # (the measured PRICE overlays live in _backcast_measured_interchange_
    # prices below, threaded into the shared injection sequence; the measured
    # NYISO reconciliation band and CAISO corridor envelopes are built at
    # their structural call sites further down, labelled the same way.)
    # CAISO RA must-offer floor: hold the gas fleet online midday at the
    # measured EIA-930 NG: NG profile (frac-scaled) so the model goes LONG and
    # its surplus exports/curtails at ~$0 (mirrors inject_interchange_shape).
    if getattr(config, "caiso_gas_commitment_floor", False):
        from market_sim.model.transmission import (
            inject_caiso_gas_commitment_floor,
        )

        frac = float(getattr(config, "caiso_gas_floor_frac", 1.0))
        if inject_caiso_gas_commitment_floor(fleet_arrays, iso, year, frac):
            logger.info(
                "%s %d: RA must-offer floor — gas fleet held online midday at "
                "%.2f x measured EIA-930 NG: NG (long-midday floor)",
                iso,
                year,
                frac,
            )

    # ── Generic registry-driven reliability floor ──────────────────────────
    # One flag, one engine, one registry: every enabled (zone, class, driver)
    # limb in RELIABILITY_FLOOR_REGISTRY[iso] (seeded from the derived
    # reliability_floor_coeffs_<ISO>.csv) is applied by the single ISO-agnostic
    # engine. Per-run overrides (config.reliability_floor_overrides) can toggle
    # or re-tune individual limbs without editing the registry.
    if getattr(config, "reliability_floor", False):
        from market_sim.config.iso_configs import (
            RELIABILITY_FLOOR_REGISTRY,
            apply_reliability_floor_overrides,
            apply_reliability_floor_plant_exclusions,
            drop_drag_owned_reliability_specs,
            drop_obligation_owned_reliability_specs,
        )
        from market_sim.model.transmission import inject_reliability_floor

        _floor_specs = apply_reliability_floor_overrides(
            RELIABILITY_FLOOR_REGISTRY.get(iso, []),
            getattr(config, "reliability_floor_overrides", None),
        )
        # Rule 19: when a net-load drag owns a class's commitment (CT_PEAKER via
        # ct_netload_drag), drop that class's reliability-floor limbs so the two
        # do not stack into an all-day floor binding overnight (the D-4
        # off-window failure; docs/FINDING-pjm-burndown-2026-07.md). No-op when
        # no drag is active, so non-drag ISOs/runs are byte-identical.
        _n_before = len(_floor_specs)
        _floor_specs = drop_drag_owned_reliability_specs(_floor_specs, config)
        if len(_floor_specs) < _n_before:
            logger.info(
                "%s %d: reliability floor — dropped %d drag-owned limb(s) "
                "(CLAUDE.md rule 19: net-load drag owns the class commitment)",
                iso,
                year,
                _n_before - len(_floor_specs),
            )
        # Rule 19, same shape: when the NYISO in-city commitment obligation is
        # armed, the published NYC/LI 10-minute requirement owns downstate
        # steam commitment, so those zones' ST_GAS floor limbs are SUPERSEDED
        # rather than stacked on (in-city must-run charter §2).
        _n_pre_obligation = len(_floor_specs)
        _floor_specs = drop_obligation_owned_reliability_specs(_floor_specs, config)
        if len(_floor_specs) < _n_pre_obligation:
            logger.info(
                "%s %d: reliability floor — dropped %d NYC/LI ST_GAS limb(s) "
                "superseded by the in-city commitment obligation "
                "(CLAUDE.md rule 19: published J/K requirement owns the class)",
                iso,
                year,
                _n_pre_obligation - len(_floor_specs),
            )
        # Rule 17 [R-FLOOR-WINDOW] membership correction: a persistent-baseline
        # limb is identified on a FLEET-aggregate CF but applied per UNIT, so an
        # economically laid-up plant would be held at the fleet baseline in every
        # hour. Arms each limb's exclude_plant_codes when the run opts in; clears
        # them otherwise, so a disarmed run is byte-identical (nyiso-140).
        _n_excluded = sum(len(s.exclude_plant_codes) for s in _floor_specs)
        _floor_specs = apply_reliability_floor_plant_exclusions(_floor_specs, config)
        if _n_excluded and sum(len(s.exclude_plant_codes) for s in _floor_specs):
            logger.info(
                "%s %d: reliability floor — %d plant exclusion(s) ARMED "
                "(CLAUDE.md rule 17: laid-up units are not floored)",
                iso,
                year,
                _n_excluded,
            )
        # Rule 17 [R-FLOOR-WINDOW], hour grain (NYISO-NEXT): the measured
        # economic-lay-up windows leave each pro_rata limb's per-unit basis.
        # None unless reliability_floor_layup_window_mask is armed in a
        # backcast, which inject_reliability_floor reads as the unmasked basis.
        _floor_layup = _reliability_floor_layup_shares(config, iso, year, fleet_arrays)
        if _floor_specs and inject_reliability_floor(
            fleet_arrays,
            iso,
            year,
            _floor_specs,
            zone_names,
            demand=demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
            layup_removed=_floor_layup,
        ):
            logger.info(
                "%s %d: reliability floor — %d enabled limb spec(s) applied "
                "from RELIABILITY_FLOOR_REGISTRY",
                iso,
                year,
                sum(1 for s in _floor_specs if getattr(s, "enabled", True)),
            )

    # NEISO winter fuel-security must-run (Component B): posture the fuel-secure
    # steam fleet (COAL_BIT + oil-capable ST_GAS) at minimum-stable on winter
    # cold days under the ISO-NE winter-reliability program posture (WRP/IEP/OFSA)
    # — the seasonal-reliability commitment coupled to the Component-A oil-burn
    # inventory budget above. Runs AFTER the reliability-floor engine so it
    # composes cheapest-first via `maximum` and its raised unit-hours carry the
    # MECH_WINTER_FUELSEC D-2 tag. Replaces the disabled COAL/ST_GAS tmin cold
    # limbs (rule 19). NEISO-only; default off (byte-identical).
    if getattr(config, "neiso_winter_fuel_mustrun", False):
        from market_sim.data.winter_fuel_inventory import (
            _WINTER_FUELSEC_CLASSES,
            apply_winter_fuelsec_mustrun,
        )

        # Rule 19/24 reconcile: the NEISO ST_GAS net-load reliability limb
        # (reliability_floor_coeffs_NEISO.csv, 2026-07-06) owns the legacy-steam
        # commitment on tight-system days — hot AND cold, a superset of Component
        # B's cold-day window for that class. When both mechanisms are armed in a
        # run, Component B keeps only its coal scope so two floors never stack on
        # one phenomenon (the tmin limbs it replaced stay disabled either way).
        from market_sim.config.iso_configs import (
            RELIABILITY_FLOOR_REGISTRY as _rf_registry,
        )

        _wf_classes = _WINTER_FUELSEC_CLASSES
        if getattr(config, "reliability_floor", False) and any(
            s.enabled and s.plant_class == "ST_GAS" and s.driver == "netload"
            for s in _rf_registry.get(iso, [])
        ):
            _wf_classes = tuple(c for c in _wf_classes if c != "ST_GAS")

        if apply_winter_fuelsec_mustrun(
            fleet_arrays,
            iso,
            config.weather_year,
            zone_names,
            plant_classes=_wf_classes,
            min_stable_pct=float(
                getattr(config, "neiso_winter_fuelsec_min_stable_pct", 0.40)
            ),
            commit_frac=float(getattr(config, "neiso_winter_fuelsec_commit_frac", 1.0)),
            tmin_threshold_c=float(
                getattr(config, "neiso_winter_fuelsec_tmin_c", -7.0)
            ),
            hours=config.hours,
        ):
            logger.info(
                "%s %d: winter fuel-security must-run (Component B) applied — "
                "COAL_BIT/ST_GAS floored at %.2f x min-stable on Nov-Mar cold "
                "days (TMIN < %.1f C, NERC cold-onset; WRP/IEP/OFSA posture)",
                iso,
                year,
                float(getattr(config, "neiso_winter_fuelsec_commit_frac", 1.0)),
                float(getattr(config, "neiso_winter_fuelsec_tmin_c", -7.0)),
            )

    # NEISO winter gas-availability cold-snap derate — the shared
    # gate-and-log wrapper both orchestrators call
    # (fleet.apply_neiso_coldsnap_derate, orchestrator-unification Stage 6;
    # closes the §2.2 accidental-drift row). Gates internally on
    # neiso_gas_coldsnap_derate; must run before the reserve-co-opt inputs
    # are built so the shared-headroom RHS sees the derated availability.
    apply_neiso_coldsnap_derate(fleet_arrays, config, iso, year)

    # NYISO firm import baseload (HQ/Ontario must-flow) and the Manitoba
    # firm-hydro floor now run inside the SHARED
    # transmission.apply_interchange_injections below — contract-structure
    # floors, forward-native, reachable from both orchestrators (Stage 5).

    # [measured: EIA-930 NYISO monthly net-interchange schedule → monthly LP
    #  band | forecast substitute: config.nyiso_forward_net_import_twh —
    #  build_import_node_reconciliation is mode-aware, the runner passes
    #  mode="forecast"]
    # NYISO priced-node boundary-flow reconciliation: pin the priced node's
    # MONTHLY net interchange to the measured EIA-930 schedule via a per-month
    # band constraint in the LP (transmission.build_import_node_reconciliation ->
    # dispatch._build_import_node_rows). The near-static economic tranche ladder
    # clears a near-flat ~18.5-21.6 TWh that does not track the metered
    # schedule's 23.45 -> 20.35 -> 19.09 TWh decline; the band replaces that
    # economic estimate with the authoritative measurement (CLAUDE.md rule #11),
    # priced tranches still setting the marginal price within each month's
    # envelope. Only fires with priced interchange + the flag + a priced node.
    import_node_recon = None
    if priced_interchange and getattr(config, "nyiso_import_reconciliation", False):
        from market_sim.model.transmission import build_import_node_reconciliation

        # Mode-aware band target: backcast -> measured EIA-930 schedule
        # (calibration always sets mode="backcast", so this is byte-identical to
        # the prior behaviour); forecast -> the neighbor's forecast net position
        # (config.nyiso_forward_net_import_twh), shaped to monthly by the
        # forecast load, else relaxed to the bare priced-seam economics.
        import_node_recon = build_import_node_reconciliation(
            fleet_arrays,
            iso,
            year,
            mode=getattr(config, "mode", "backcast"),
            forward_net_import_twh=getattr(
                config, "nyiso_forward_net_import_twh", None
            ),
            system_demand=demand,
        )
        if import_node_recon is not None:
            node_idx, recon_lo, recon_hi = import_node_recon
            _recon_target = (
                "the neighbor's forecast net position"
                if getattr(config, "mode", "backcast") == "forecast"
                else "measured EIA-930 net interchange"
            )
            logger.info(
                "%s %d: priced import node reconciled to %s — %d node rows, "
                "annual band [%.2f, %.2f] TWh",
                iso,
                year,
                _recon_target,
                int(node_idx.size),
                recon_lo.sum() / 1e6,
                recon_hi.sum() / 1e6,
            )

    # NYISO Long Island local self-supply floor: force the cable-islanded LI
    # pocket to meet a forward fraction of its own load with in-zone thermal
    # generation rather than importing cheap NYC gas (transmission.
    # inject_nyiso_local_selfsupply). NYISO-only; scales with load.
    if getattr(config, "nyiso_local_selfsupply", False):
        from market_sim.model.transmission import inject_nyiso_local_selfsupply

        # Zone-K LCR/TSL mechanism active (issue #1345): the published-limit
        # import cap owns Long_Island this run; skipping its floor entry here
        # keeps the two mechanisms from stacking (rule 19).
        _selfsupply_exclude = (
            frozenset({"Long_Island"})
            if getattr(config, "nyiso_li_lcr_tsl", False)
            else frozenset()
        )
        if inject_nyiso_local_selfsupply(
            fleet_arrays, iso, demand, zone_names, exclude_zones=_selfsupply_exclude
        ):
            logger.info(
                "%s %d: local self-supply floor applied to downstate pocket(s) "
                "(LMIC / cable-islanded local reliability)",
                iso,
                year,
            )

    # Fuel prices: gas/coal base, then the lignite/PRB supply base for coal
    # (our costs), then the actual EIA-923 monthly per-plant delivered cost
    # on top — so measured monthly cost takes precedence and the supply
    # trajectory is only the base/fallback for plant-months without data.
    fuel_prices = resolve_fuel_prices(config, fleet_arrays, year, apply_monthly=False)
    if config.coal_supply_repricing:
        apply_coal_supply_pricing(fuel_prices, fleet, config, year)
    # The overlay returns the mask of cells it WROTE (own print or nearby pool);
    # the MISO zonal-basis applier below consumes it under
    # miso_zonal_gas_basis_skip_923_priced (miso-213, rule 19) — a print-derived
    # cell already carries the regional delivered premium. This chain mirrors
    # resolve_fuel_prices' apply_monthly=True branch, which threads it the same
    # way, so the calibration and forecast paths agree.
    print_cells = apply_plant_monthly_fuel_prices(
        fuel_prices, fleet_arrays, config, year
    )
    # Hub-basis overlay (NEISO only): replace the gas price with the measured
    # Algonquin Citygate hub spot in covered months — daily-resolved when
    # gas_hub_basis_daily is on. Because run_year resolves fuel prices with
    # apply_monthly=False (so the coal-supply base lands before the per-plant
    # EIA-923 overwrite), the overlay that resolve_fuel_prices runs in its
    # apply_monthly=True branch must be re-applied here, mirroring that branch's
    # order: plant-monthly, then hub overlay, then the dual-fuel min. No-op
    # unless gas_hub_basis_overlay is set (and basis rows exist), so non-NEISO
    # runs are unchanged.
    apply_hub_basis_overlay(fuel_prices, fleet_arrays, config, year)
    # NYISO per-zone gas-hub basis: shift each gas unit to its region's pipeline
    # index so the east marginal gas stays dearer than the west (the structural
    # source of the upstate-cheap / east-dear spread). Mirrors the
    # resolve_fuel_prices apply_monthly=True order: after the plant-monthly /
    # hub overlay, before the dual-fuel min so oil parity still caps any winter
    # spike. No-op unless nyiso_zonal_gas_basis is set (NYISO only).
    apply_nyiso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # NYISO downstate CT-peaker interruptible city-gate gas premium: lift each
    # NYC / Long Island CT_PEAKER unit's delivered gas by the measured monthly
    # LDC city-gate premium (summer-peaked interruptible-gas scarcity these
    # non-firm peakers face) so an efficient LM6000 no longer undercuts the
    # dearer downstate steam fleet on flat hub gas (issue #1344 / B-NYI-1). Same
    # order as the other basis overlays: after the zonal basis, before the
    # dual-fuel oil-parity min. No-op unless nyiso_downstate_ct_gas_basis is set
    # (NYISO only). See fuel.apply_nyiso_downstate_ct_gas_basis.
    apply_nyiso_downstate_ct_gas_basis(fuel_prices, fleet_arrays, config, year)
    # NYISO downstate CT-peaker DAILY delivered-gas re-grounding: SET each NYC /
    # Long Island CT_PEAKER unit's gas to the curated measured daily delivered
    # index (Transco Z6 NY daily spot + monthly LDC premium), so the cold-snap
    # blowouts on the exact days the interruptible peakers run lift their offer —
    # the daily-resolution successor to the monthly premium above (rules
    # #11/#13). Same order: after the monthly basis, before the dual-fuel
    # oil-parity min. No-op unless nyiso_downstate_ct_gas_daily is set (NYISO
    # only). See fuel.apply_nyiso_downstate_ct_gas_daily.
    apply_nyiso_downstate_ct_gas_daily(fuel_prices, fleet_arrays, config, year)
    # NYC gas-steam LDC delivery leg (NYISO-STGAS-2023): add each crosswalked
    # NYC ST_GAS plant's LDC line-loss gross-up + filed transport rate on top of
    # the hub the overlays above set. Same order: before the dual-fuel oil-parity
    # min. No-op unless nyiso_ldc_generator_delivered_gas is set (NYISO only).
    apply_nyiso_ldc_generator_delivered_gas(fuel_prices, fleet_arrays, config, year)
    # ERCOT per-zone gas-hub basis: shift each gas unit to its zone's measured
    # regional hub (Waha-cheap West/Permian, dearer North/East-Texas and South)
    # so the merit order stops over-running DFW/North CCs on flat Waha-discounted
    # gas. Mean-zero anchored so the aggregate gas level is preserved. Same order
    # as the resolve_fuel_prices apply_monthly=True branch: after the
    # plant-monthly / hub overlay, before the dual-fuel min. No-op unless
    # ercot_zonal_gas_basis is set (ERCOT only).
    apply_ercot_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # PJM per-zone gas basis: shift each gas unit to its zone's measured regional
    # delivered-to-electric-power basis (west coal belt cheap, eastern
    # EMAAC/SWMAAC/Dominion dear) so PJM stops clearing as a single copper-plate —
    # the internal TTCs bind, eastern LMP separates up, eastern CCs back off and
    # western coal serves the east. Capacity-weighted mean-zero so the aggregate
    # gas level is preserved. Same order as the resolve_fuel_prices
    # apply_monthly=True branch: after the plant-monthly / hub overlay, before the
    # dual-fuel min. No-op unless pjm_zonal_gas_basis is set (PJM only). The
    # print-derived-cell mask is passed always; the applier consumes it only
    # under pjm_zonal_gas_basis_skip_923_priced (PJM-NEXT-2; off => identical).
    apply_pjm_zonal_gas_basis(
        fuel_prices, fleet_arrays, config, year, skip_cells=print_cells
    )
    # MISO winter fuel security (miso-72): in Dec/Jan/Feb, swap the national HH
    # gas_daily_shape for the measured Chicago Citygate daily shape on the
    # Chicago-hub zones' gas units. BEFORE the zonal basis (acts on
    # level x national_shape; the additive zonal spread lands un-shaped) and
    # before dual-fuel (oil parity still caps). Mirrors the resolve_fuel_prices
    # apply_monthly=True order. No-op unless miso_winter_citygate_daily is set
    # (MISO only). See fuel.apply_miso_winter_citygate_daily.
    # miso-224: gas at MARGINAL commodity (measured daily hub spot per zone)
    # instead of the EIA-923 AVERAGE print. Off by default and byte-identical
    # off. Armed, it supersedes (rule 19, never stacks) the winter Chicago SHAPE
    # overlay below (the daily series carries level AND shape) and the mean-zero
    # zonal increment (its written mask joins the print-derived mask, which the
    # MISO applier honours under either flag). Mirrors the resolve_fuel_prices
    # apply_monthly=True branch — this calibration chain is the path a backcast
    # solve actually takes, so the hook must live here too (miso-224 Addendum A).
    spot_cells = apply_miso_gas_marginal_commodity(
        fuel_prices, fleet_arrays, config, year
    )
    if spot_cells is None:
        apply_miso_winter_citygate_daily(fuel_prices, fleet_arrays, config, year)
    else:
        print_cells = spot_cells if print_cells is None else (print_cells | spot_cells)
    # MISO per-zone gas basis (north/south gas gradient). Same mean-zero core as
    # PJM. No-op unless miso_zonal_gas_basis is set (MISO only). The
    # print-derived-cell mask is passed always; the applier consumes it only
    # under miso_zonal_gas_basis_skip_923_priced (flag off => byte-identical).
    apply_miso_zonal_gas_basis(
        fuel_prices, fleet_arrays, config, year, skip_cells=print_cells
    )
    # CAISO per-zone citygate basis (NP15/ZP26 on PG&E Citygate, SP15 on SoCal
    # Citygate — measured weekly prints, mean-zero). No-op unless
    # caiso_zonal_gas_basis is set (CAISO only).
    apply_caiso_zonal_gas_basis(fuel_prices, fleet_arrays, config, year)
    # Net-load-indexed West/Panhandle Waha shape: redistribute the West gas basis
    # across hours (firm at high net-load, collapsed at low) so peakers — which
    # burn only in scarcity hours — see firm Waha and idle, while the West CCs on
    # all-hours blended gas stay baseload. Mean-zero so the annual basis above is
    # preserved; structural replacement for the flat delivered-floor scalar. No-op
    # unless ercot_west_netload_gas_shape (+ ercot_zonal_gas_basis) is set, ERCOT.
    if getattr(config, "ercot_west_netload_gas_shape", False):
        west_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        # Endogenous Waha collapse frequency (gap G6): how often forecast West/
        # Panhandle VRE over-supplies the local basin (local load + export TTC).
        # Built from the per-zone VRE capacity×CF, the West load, and the
        # WESTEX+PNHNDL export limit the model already carries — the forward
        # driver that replaces the measured neg_day_freq when
        # ercot_west_gas_endogenous_collapse is on. Always computed so it can be
        # logged against the measured value; the function uses it only when the
        # flag is set.
        waha_zone_idx = [
            i for i, name in enumerate(zone_names) if name in ("West", "Panhandle")
        ]
        west_oversupply_freq = None
        if waha_zone_idx:
            widx = np.array(waha_zone_idx)
            west_vre = (solar_cap[widx, None] * solar_cf[widx]).sum(axis=0) + (
                wind_cap[widx, None] * wind_cf[widx]
            ).sum(axis=0)
            west_local_load = demand[widx].sum(axis=0)
            # Export takeaway: total TTC on links leaving the Waha zones (WESTEX
            # West->North/South_Central + PNHNDL Panhandle->North); the constrained
            # path the surplus must squeeze through before it crashes the hub.
            export_limit = sum(
                link.ttc_mw
                for link in iso_config.links
                if link.from_zone in ("West", "Panhandle")
                and link.to_zone not in ("West", "Panhandle")
            )
            west_oversupply_freq = ercot_west_oversupply_collapse_freq(
                west_vre, west_local_load, export_limit
            )
        apply_ercot_west_netload_gas_shape(
            fuel_prices,
            fleet_arrays,
            config,
            year,
            west_net_load,
            west_oversupply_freq=west_oversupply_freq,
        )
    # Capture which dual-fuel generator-hours will switch to oil (gas price >
    # oil parity) BEFORE the min-cap below overwrites the gas price, so the
    # dispatch re-attribution can count their MWh as petroleum, not gas (the
    # switch itself is objective-only; this is a reporting re-attribution).
    # Gated on dual_fuel_oil_reattribution (NEISO-only) so PJM/NYISO — whose
    # dual-fuel units also switch on their own winter gas — stay byte-identical.
    # Also computed for the winter fuel-inventory budget (Component A), which
    # gates each dual-fuel unit's oil-burn budget to exactly these oil hours so
    # the seasonal stock constraint never caps its gas generation.
    dual_fuel_oil_mask = (
        dual_fuel_switch_mask(fuel_prices, fleet_arrays, config, year)
        if (
            getattr(config, "dual_fuel_oil_reattribution", False)
            or getattr(config, "neiso_winter_fuel_inventory", False)
        )
        else None
    )
    # Dual-fuel switching last, so the oil-parity min sees the final delivered
    # gas price — the AGT-hub winter spot, so the gas->oil switch trips on cold
    # days (NEISO) — not the per-plant monthly cost alone (PJM).
    apply_dual_fuel_pricing(fuel_prices, fleet_arrays, config, year)
    # PJM DA virtual-bid layer: the pseudo-units' hourly bid prices are their
    # fuel_prices rows (heat_rate 1.0, vom 0) — written LAST among the
    # fuel-price appliers so no gas/coal overlay can touch them.
    if virtual_price_rows:
        from market_sim.data.virtual_bids import apply_virtual_bid_prices

        n_priced = apply_virtual_bid_prices(
            fuel_prices, fleet_arrays, virtual_price_rows
        )
        logger.info(
            "PJM %d DA virtual-bid layer: hourly bid prices applied to %d "
            "pseudo-unit rows",
            year,
            n_priced,
        )
    carbon_price = resolve_carbon_price(config, year)
    # Partial-footprint carbon program (pjm-146): when the ISO's program maps
    # membership per zone (program.zone_share is not None — today only PJM's
    # RGGI footprint) and the resolved adder is nonzero, replace the scalar
    # with the per-generator membership-weighted column assemble_mc already
    # accepts: emission_rate[g] x m[g] x p_allowance, with m[g] the exact
    # per-plant EIA-860 state test against the year's member set (VA 2023
    # only) and the committed PJM_RGGI_ZONE_SHARE fallback for synthetic
    # rows. Whole-ISO programs (CAISO/NYISO/NEISO, zone_share None) keep the
    # scalar path BY CONSTRUCTION — membership there is uniform 1.0 on load
    # zones, so the scalar IS exact and their solves stay byte-identical
    # (rule 25 lane isolation). zone_names here is the runtime interchange-
    # extended list (assigned after apply_interchange_topology), matching
    # fleet_arrays.zone_idx as resolve_carbon_program requires; an external
    # node absent from the zone_share map takes 0.0 membership.
    carbon_mc = carbon_price  # what assemble_mc sees; scalar unless below
    if carbon_price:
        from market_sim.config.constants import CAP_AND_TRADE_PROGRAMS
        from market_sim.policy.cap_and_trade import (
            per_generator_membership,
            resolve_carbon_program,
        )

        _carbon_program = CAP_AND_TRADE_PROGRAMS.get(iso)
        if _carbon_program is not None and _carbon_program.zone_share is not None:
            _carbon_resolution = resolve_carbon_program(
                config, year, zone_names=zone_names
            )
            if _carbon_resolution is not None and _carbon_resolution.price_adder:
                carbon_mc = per_generator_membership(
                    iso, year, _carbon_resolution.membership, fleet_arrays
                ) * float(_carbon_resolution.price_adder)
                logger.info(
                    "%s %d: partial-footprint carbon adder — %d/%d generators "
                    "carry a nonzero membership-weighted allowance price "
                    "(program %s, %.2f $/t)",
                    iso,
                    year,
                    int((carbon_mc > 0).sum()),
                    len(carbon_mc),
                    _carbon_program.name,
                    float(_carbon_resolution.price_adder),
                )
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    if getattr(config, "wind_ptc_vintage_offers", False):
        # ERCOT-65 PTC vintage scoping: the flat -ira_ptc_wind offer becomes
        # the per-zone-month measured EIA-860 vintage blend
        # -PTC_statutory(year) x eligible_share[z, month] (policy.ira.
        # wind_ptc_vintage_dispatch_offer; full adjudication at the
        # ScenarioConfig field). Enters BOTH P0 and P1 — it is the unit's
        # cost-basis bid, exactly like the flat credit it replaces. Falls
        # back to the flat offer when the share data is unavailable.
        from market_sim.policy.ira import wind_ptc_vintage_dispatch_offer

        _vintage_wind_mc = wind_ptc_vintage_dispatch_offer(
            iso, year, zone_names, config, hours
        )
        if _vintage_wind_mc is not None:
            wind_mc = _vintage_wind_mc
    # Base marginal cost: fuel + VOM + carbon + NOx, then exogenous EACs,
    # then the coal take-or-pay tranche discount. No startup-cost markup.
    mc_base = assemble_mc(fleet_arrays, fuel_prices, carbon_mc, config.nox_price)
    apply_eac_to_mc(mc_base, fleet_arrays, config)
    apply_coal_tranches(
        mc_base, fleet, fleet_arrays, fuel_fracs, fuel_prices, config, year=year
    )
    # Gas-offer net-revenue margin (gas_offer_net_revenue_margin, default
    # off): compress each gas tranche's above-physical markup to a fixed
    # $/MWh margin at the ISO's delivered-gas anchor. Runs after
    # apply_dual_fuel_pricing has finalized fuel_prices (the compression keys
    # on the post-switch delivered price) and on the BASE cost, so P0 run
    # discovery and the P1 bid see the same offer curve — exactly like the
    # multiplier form it reprices. Byte-identical when off (no-op return).
    apply_gas_offer_margin(mc_base, fleet, fuel_prices, config)
    # MISO POSITION-conditioned MEASURED offer surface (miso_offer_surface_
    # measured, default off, MISO-gated — miso-151 queue item 9, owner-chartered).
    # SUBSUMES the margin the call above just set on MISO's ABOVE-BASE gas
    # tranches (rule 19 [R-ONE-MECH]): those rows have `offer_markup_hr × anchor`
    # removed and MISO's own measured own-curve RISE put in its place, so no row
    # is ever priced by both. Runs immediately after, on the BASE cost, so P0 run
    # discovery and the P1 bid see the same curve. SHAPE only — the measured
    # object is a within-unit price DIFFERENCE, so the model's level stays on its
    # own physical basis (miso-145 measured the real book CHEAPER at matched
    # position; a level transfer would move C3a the wrong way). Byte-identical
    # when off (no-op return).
    if getattr(config, "miso_offer_surface_measured", False) and iso == "MISO":
        from market_sim.data.fuel.trajectories import _gas_series

        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        apply_miso_offer_surface(
            mc_base,
            fleet,
            _surface_net_load,
            _gas_series(config, year, mc_base.shape[1]),
            config,
        )
    # miso-180 anchored SPREAD-ONLY across-unit dispersion graft
    # (miso_offer_spread_anchored, default off, MISO-gated): floor the
    # above-anchor econ/peak tranches at the stack's own monthly anchor level
    # plus the MEASURED eligible-book rise Q(r) − Q(a) × G_ref — the
    # top-decile tail steepening miso-179 located, grafted raise-only with
    # the model's own level kept at and below the anchor (shape, never
    # level). Runs on the BASE cost, immediately after the offer-margin /
    # measured-surface family, so P0 run discovery and the P1 bid see the
    # same curve; the P1 startup markup stays on top. Byte-identical when
    # off (no-op return).
    apply_miso_offer_spread_anchored(mc_base, fleet, fleet_arrays, config, year)
    # CC committed-block measured offer level (cc_committed_offer_margin,
    # default off — ERCOT-139): reprice the CC_REGULAR `_committed` tranche from
    # its band multiplier to the measured RT SCED curve bottom, expressed as a
    # fuel-invariant margin at the SHARED gas anchor. Runs after
    # apply_gas_offer_margin (which is provably inert on this row — ERCOT-138
    # §J) and on the BASE cost, so P0 run discovery and the P1 bid see the same
    # offer curve. Byte-identical when off (no-op return).
    apply_cc_committed_offer_margin(mc_base, fleet, fleet_arrays, config)
    # ERCOT G-22 condition-responsive CT/peaker offer surface (default off,
    # ERCOT-gated): raise the CT/peaker econ+peak tranche bid to the MEASURED
    # self-withholding level (60-Day DAM disclosure) in the top-net-load hours
    # where the real fleet's peakers price to the cap band, removing the
    # "phantom sub-$200 spare" that caps the energy dual in the missed tail.
    # Net-load uses the same LP-served convention as the drag floors above.
    if getattr(config, "ercot_ct_offer_surface", False) and iso == "ERCOT":
        _ct_surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        apply_ercot_ct_offer_surface(mc_base, fleet, _ct_surface_net_load, config)
    # ERCOT G-22 §8 heterogeneity-preserving condition-responsive offer surface
    # (default off, ERCOT-gated): the P1-ONLY additive markup that reprices the gas
    # peak-band scarcity wall in anticipated-tight hours. Built here (net-load + the
    # per-gen fuel price are ready) and threaded into run_energy_solve so it lands on
    # the P1 clearing objective only — P0 run lengths (and the CT<->ST startup
    # coupling) stay byte-identical to the keeper (fleet.
    # build_ercot_offer_surface_conditional_markup). None when the flag is off.
    offer_surface_mc_bid_adjust = None
    if getattr(config, "ercot_offer_surface_conditional", False) and iso == "ERCOT":
        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        offer_surface_mc_bid_adjust = build_ercot_offer_surface_conditional_markup(
            fleet_arrays, fleet, fuel_prices, _surface_net_load, config
        )
    # ERCOT MID-CURVE offer surface (G-22 lever A', the ERCOT analogue of the PJM
    # mid-curve): floors the gas econ-tranche rows' P1 bids at the measured
    # capacity-share offer level of the 60-Day DAM disclosure body
    # (fleet.build_ercot_offer_midcurve_conditional_markup). Targets econ rows
    # only — disjoint from the peak surface above (which owns the PEAK rungs), so
    # the two markups SUM without overlap when both flags are armed (one
    # mechanism per row, rule 19). P1-only; needs mc_base + year in scope.
    if (
        getattr(config, "ercot_offer_surface_midcurve_conditional", False)
        and iso == "ERCOT"
    ):
        from market_sim.data.fleet import (
            build_ercot_offer_midcurve_conditional_markup,
        )

        _mc_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        _ercot_midcurve = build_ercot_offer_midcurve_conditional_markup(
            fleet_arrays, fleet, mc_base, _mc_net_load, config, year
        )
        if _ercot_midcurve is not None:
            offer_surface_mc_bid_adjust = (
                _ercot_midcurve
                if offer_surface_mc_bid_adjust is None
                else offer_surface_mc_bid_adjust + _ercot_midcurve
            )
    # ERCOT-72 DAM CLEARED-SHARE offer boundary: floors the merchant gas econ*
    # rows ABOVE the bin's measured DAM cleared share at the bin's measured
    # above-boundary offer wall (fleet.build_ercot_offer_surface_cleared_share_
    # markup — the covered-CC/CT composition mechanism). Econ rows only —
    # disjoint from the peak surface (peak rungs) and mutually exclusive with
    # the mid-curve belt (same econ rows; the builder hard-errors if both are
    # armed, rule 19). P1-only; sums with the peak surface's markup.
    if getattr(config, "ercot_offer_surface_cleared_share", False) and iso == "ERCOT":
        from market_sim.data.fleet import (
            build_ercot_offer_surface_cleared_share_markup,
        )

        _cs_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        _ercot_cleared_share = build_ercot_offer_surface_cleared_share_markup(
            fleet_arrays, fleet, mc_base, _cs_net_load, config, year
        )
        if _ercot_cleared_share is not None:
            offer_surface_mc_bid_adjust = (
                _ercot_cleared_share
                if offer_surface_mc_bid_adjust is None
                else offer_surface_mc_bid_adjust + _ercot_cleared_share
            )
    # ERCOT-88 offline fast-start pool (charter §9 of the residual-midband
    # lane): the merchant-CT bid rows above the measured offline-pool
    # boundary priced at the pool's above-LSL SCED2 ladder
    # (fleet.build_ercot_faststart_pool_markup). REPLACE-BY-MASK composition
    # (rule 19, one owner per row-hour): in the pool's row-hours the pool
    # markup REPLACES the summed surface markups above (conditional peak
    # surface + cleared-share wall/RT) — offline-startable capability prices
    # on its startup-inclusive RT offer, not on any online/DA basis. P1-only;
    # None (byte-identical) when the gate is off or the year is unmeasured.
    if getattr(config, "ercot_faststart_pool_offer", False) and iso == "ERCOT":
        from market_sim.data.fleet import build_ercot_faststart_pool_markup

        _fsp_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        _fsp = build_ercot_faststart_pool_markup(
            fleet_arrays, fleet, mc_base, _fsp_net_load, config, year
        )
        if _fsp is not None:
            _fsp_markup, _fsp_mask = _fsp
            if offer_surface_mc_bid_adjust is None:
                offer_surface_mc_bid_adjust = _fsp_markup
            else:
                offer_surface_mc_bid_adjust = np.where(
                    _fsp_mask, _fsp_markup, offer_surface_mc_bid_adjust
                )
    # ERCOT G-22 conditional-offer-distribution LOW leg: the trough-side mirror
    # of the surface above at the P1-only seam, but P0-CONDITIONED — the
    # measured committed-unit LSL/lower-body markdown (ratio clamped <= 1) is
    # gated to plant-hours the model's OWN P0 commitment discovery runs the
    # plant (the CAISO-RA/PJM-path-B forward-regenerating construction), so
    # offline plants' discounted blocks never undercut coal/ST in P1. Built
    # inside run_energy_solve via the p1_bid_adjust_prep hook (it needs the P0
    # solution); composes additively with the top leg's static markup
    # (disjoint rows: peak rungs vs committed/econ rungs, rule 19). None when
    # the flag is off (byte-identical).
    lowcurve_bid_adjust_prep = None
    if getattr(config, "ercot_offer_surface_lowcurve", False) and iso == "ERCOT":
        _lowcurve_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )

        def lowcurve_bid_adjust_prep(r0):  # noqa: E306
            return build_ercot_offer_surface_lowcurve_markdown(
                fleet_arrays,
                fleet,
                fuel_prices,
                _lowcurve_net_load,
                config,
                p0_dispatch=r0.dispatch,
            )

    # ERCOT-64 FLOOR-SCOPED committed-LSL markdown: the same measured LSL
    # artifact applied ONLY in the gas commitment bridge's own floored
    # plant-hours (never the v2 P0-online gate — P0-online is False in
    # bridged gaps by construction). The closure receives the bridge's own
    # floor mask from build_ercot_gas_bridge_p1_preps, which computes the
    # floor ONCE and shares it across the fleet and bid hooks (charter
    # wiring traps #1/#2). None when the flag is off (byte-identical).
    floorscoped_markdown_fn = None
    if (
        getattr(config, "ercot_offer_surface_lowcurve_floorscoped", False)
        and iso == "ERCOT"
    ):
        from market_sim.data.fleet import (
            build_ercot_offer_surface_lowcurve_floorscoped_markdown,
        )

        _floorscoped_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )

        def floorscoped_markdown_fn(floor_mask):  # noqa: E306
            return build_ercot_offer_surface_lowcurve_floorscoped_markdown(
                fleet_arrays,
                fleet,
                fuel_prices,
                _floorscoped_net_load,
                config,
                floor_mask,
            )

    # NEISO fast-start offer surface (charter Limb B): the identical P1-only
    # seam, NEISO-gated (fleet.build_neiso_offer_surface_conditional_markup).
    if getattr(config, "neiso_offer_surface_conditional", False) and iso == "NEISO":
        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        offer_surface_mc_bid_adjust = build_neiso_offer_surface_conditional_markup(
            fleet_arrays, fleet, fuel_prices, _surface_net_load, config
        )
    # PJM energy-offer surface (G-22 lever A): the identical P1-only seam,
    # PJM-gated (fleet.build_pjm_offer_surface_conditional_markup).
    if getattr(config, "pjm_offer_surface_conditional", False) and iso == "PJM":
        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        offer_surface_mc_bid_adjust = build_pjm_offer_surface_conditional_markup(
            fleet_arrays, fleet, fuel_prices, _surface_net_load, config
        )
    # CAISO measured offer surface (C1 lane WP-A): the identical P1-only
    # seam, CAISO-gated (fleet.build_caiso_offer_surface_conditional_markup).
    if getattr(config, "caiso_offer_surface_conditional", False) and iso == "CAISO":
        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        offer_surface_mc_bid_adjust = build_caiso_offer_surface_conditional_markup(
            fleet_arrays, fleet, fuel_prices, _surface_net_load, config
        )
    # PJM MID-CURVE offer surface (G-22 lever A'): floors the econ-tranche
    # rows' P1 bids at the measured capacity-share offer level
    # (fleet.build_pjm_offer_midcurve_conditional_markup). Targets econ rows
    # (+ LONG_RUN peak rows) only — disjoint from the top-of-curve surface's
    # CC/CT peak rungs, so the two markups SUM without overlap when both
    # flags are armed (one mechanism per row, rule 19).
    if getattr(config, "pjm_offer_midcurve_conditional", False) and iso == "PJM":
        from market_sim.data.fleet import build_pjm_offer_midcurve_conditional_markup

        _surface_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        _midcurve = build_pjm_offer_midcurve_conditional_markup(
            fleet_arrays, fleet, mc_base, _surface_net_load, config, year
        )
        if _midcurve is not None:
            offer_surface_mc_bid_adjust = (
                _midcurve
                if offer_surface_mc_bid_adjust is None
                else offer_surface_mc_bid_adjust + _midcurve
            )
    # PJM CT_FAST measured max()-seam reprice (pjm-123 composite leg 3): a bid
    # LEVEL, not a markup — run_energy_solve applies it as max(bid, target)
    # AFTER the startup amortization, so the measured CT corpus and the pjm-103
    # start-cost pricing reconcile instead of stacking (rule 19; the additive
    # pjm-101/102 form over-expressed at CT -12 TWh). None for every
    # non-PJM / gate-off run (byte-identical).
    p1_bid_max_target = None
    if getattr(config, "pjm_ct_measured_max_reprice", False) and iso == "PJM":
        from market_sim.data.fleet import build_pjm_ct_measured_max_target

        _ct_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        p1_bid_max_target = build_pjm_ct_measured_max_target(
            fleet_arrays, fleet, mc_base, _ct_net_load, config, year
        )
    # ERCOT-176 offline-increment SLOW-START tier
    # (ScenarioConfig.ercot_offline_commit_offer): the merchant CC bid rows
    # above the measured offline boundary priced at that band's own measured
    # start-inclusive above-LSL SCED2 ladder
    # (fleet.build_ercot_offline_commit_target). A bid LEVEL, not a markup —
    # run_energy_solve applies it as max(bid, target) AFTER the startup
    # amortization, so the measured start-inclusive ladder and P1's start
    # pricing RECONCILE instead of stacking (rule 19; an additive form would
    # price the row at ladder + startup and double-count the start, the
    # pjm-101/102 failure mode). Disjoint from the ERCOT-88 fast-start pool
    # by unit physics (min-down 1 h vs 4-8 h). None for every non-ERCOT /
    # gate-off / unmeasured-year run (byte-identical).
    # PRECOMMIT-ercot176 §2 + its 2026-08-07 pre-solve amendment.
    if getattr(config, "ercot_offline_commit_offer", False) and iso == "ERCOT":
        from market_sim.data.fleet import build_ercot_offline_commit_target

        _oc_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        _oc = build_ercot_offline_commit_target(
            fleet_arrays, fleet, mc_base, _oc_net_load, config, year
        )
        if _oc is not None:
            # ERCOT and PJM gate exclusively, so the seam carries one target.
            p1_bid_max_target = _oc[0]
    # v4 condition-keyed fast-start amortization horizon
    # (tranche_startup_conditional_runs): the hour's within-year net-load
    # percentile band scales the v3 CAMPD-measured run-length ceiling by the
    # class band ratio (campd_ct_run_bands_<ISO>.csv — measured shape, plant
    # median level). Same LP-served net-load convention as the offer
    # surfaces above; None (flag off / no per-ISO artifact) keeps the v3
    # markup byte-identical.
    startup_run_ratio_t = None
    if getattr(config, "tranche_startup_conditional_runs", False):
        from market_sim.data.fleet import campd_ct_run_band_ratios

        _bands = campd_ct_run_band_ratios(iso)
        if _bands is not None:
            _edges, _ratios = _bands
            _nl = (
                demand.sum(axis=0)
                - (solar_cap[:, None] * solar_cf).sum(axis=0)
                - (wind_cap[:, None] * wind_cf).sum(axis=0)
            )
            _pct = (np.argsort(np.argsort(_nl)) + 1.0) / float(_nl.shape[0])
            _band_idx = np.searchsorted(
                np.asarray(_edges, dtype=float), _pct, side="right"
            )
            startup_run_ratio_t = np.asarray(_ratios, dtype=float)[_band_idx]
    # ── Interchange price/limit injections (orchestrator-unification Stage 5)
    # The forward-native sequence — reference-price seams (generic + CAISO
    # dedicated), firm import/export floors, and the CAISO offer couplings —
    # is the SHARED transmission.apply_interchange_injections, the exact call
    # the forecast runner makes; every step is gated by its existing
    # ScenarioConfig field. The BACKCAST-ONLY measured-price overlays are
    # consolidated below and threaded into the shared sequence at its
    # documented seam point (after the forward base prices, before the
    # couplings — the order the inline code always had). Each overlay names
    # its measured source and forecast substitute (plan §3.1); none is
    # reachable from the forecast path, which passes measured_overlay=None.
    caiso_ref_seam = (
        getattr(config, "caiso_reference_price_seam", False) and iso == "CAISO"
    )
    per_hub_intertie = (
        (not caiso_ref_seam)
        and getattr(config, "caiso_per_hub_intertie", False)
        and iso == "CAISO"
    )
    # caiso_bidir_intertie was DELETED at caiso-236 (rule 26 [R-DELETE]): dead on
    # the keeper AND in the ScenarioConfig defaults, so its fitted 4,361 MW
    # aggregate export cap was a re-armable answer key. Only the per-hub node and
    # the legacy pooled ladder remain.
    legacy_intertie = not per_hub_intertie

    def _backcast_measured_interchange_prices(fleet_arrays, mc_base) -> None:
        """Backcast measured-price interchange overlays (BOD, plan §3.1).

        Measured hub/border LMP overwrites on the priced node's mc rows —
        each a real delivered price fed as an input (rule 12-admissible), but
        with no forward analogue series, so the forecast substitutes the
        reference-price formula per seam. Runs inside the shared injection
        sequence after the forward base prices and before the couplings.
        """
        # [measured: PJM DA LMP at the MISO-facing western border hubs |
        #  forecast substitute: gas × HR reference price, optionally re-
        #  anchored via miso_pjm_border_anchor]. Overwrites ONLY the PJM seam
        # rows the generic inject_reference_price_mc just priced; SPP/South
        # keep their gas × HR pricing. Measured LMP takes precedence over the
        # border anchor when both are on. No-op without the measured parquet.
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "miso_pjm_lmp_import_pricing", False)
        ):
            from market_sim.model.transmission import (
                inject_miso_pjm_lmp_import_prices,
            )

            if inject_miso_pjm_lmp_import_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: PJM seam repriced to MEASURED hourly PJM "
                    "border-hub DA LMP (CHICAGO GEN / AEP GEN / ATSI GEN "
                    "mean + $%.0f hurdle)",
                    iso,
                    year,
                    next(
                        (
                            n.hurdle
                            for n in INTERFACE_NEIGHBORS.get(iso, [])
                            if n.name == "PJM"
                        ),
                        2.0,
                    ),
                )
        # [measured: per-seam Q-Q band ladders — EIA-930 seam flow duration
        #  curves coupled with the measured MISO DA hub LMP
        #  (interchange_config.MISO_SEAM_LADDER_BY_YEAR, scripts/
        #  derive_miso_seam_ladders.py) | forecast substitute: the gas-elastic
        #  reference-price formula (hr_by_year two-track; pooled ladder = the
        #  forward story)]. Overwrites EVERY seam band (PJM/SPP/South, both
        # directions) with its measured revealed-supply-curve price, so the
        # firm/scheduled PJM+IESO base the spot-spread pricing deletes (G-23
        # 2025 import starvation) clears economically. Runs LAST among the
        # seam price overwrites — displaces the border-anchor / PJM-LMP
        # prices on the rows it covers (alternatives, never stacked).
        # miso-225: the neighbour-anchored overlay is meaningless without the
        # ladder it overlays, and the block below would silently skip it — the
        # fail-open this repo refuses. Checked here, at the point of use, on the
        # complete as-solved config (a __post_init__ check sees intermediate
        # configs in which the pair is legitimately split; miso-225 Addendum A).
        if getattr(
            config, "miso_seam_neighbour_anchored_ladder", False
        ) and not getattr(config, "miso_seam_measured_ladder", False):
            raise ValueError(
                "miso_seam_neighbour_anchored_ladder requires "
                "miso_seam_measured_ladder: the neighbour-anchored PJM entry "
                "OVERLAYS the measured Q-Q ladder, and there is nothing to "
                "overlay when the ladder itself is off (rule 19 [R-ONE-MECH])"
            )
        # miso-231: the same fail-closed guard for the HOURLY overlay, for the
        # same reason and at the same point of use.
        if getattr(config, "miso_seam_neighbour_hourly_ladder", False) and not getattr(
            config, "miso_seam_measured_ladder", False
        ):
            raise ValueError(
                "miso_seam_neighbour_hourly_ladder requires "
                "miso_seam_measured_ladder: the hourly neighbour-anchored PJM "
                "entry OVERLAYS the measured Q-Q ladder, and there is nothing "
                "to overlay when the ladder itself is off (rule 19 "
                "[R-ONE-MECH])"
            )
        # miso-233: the SPP hourly overlay is a SUB-GATE of the PJM one, so it
        # is refused rather than silently half-arming a family (rule 19
        # [R-ONE-MECH]); same fail-closed point of use as its parent.
        if getattr(config, "miso_seam_neighbour_hourly_spp", False) and not getattr(
            config, "miso_seam_neighbour_hourly_ladder", False
        ):
            raise ValueError(
                "miso_seam_neighbour_hourly_spp requires "
                "miso_seam_neighbour_hourly_ladder: the SPP hourly entry is a "
                "SUB-GATE of the hourly neighbour-anchored family, not a "
                "mechanism beside it, and arming one seam hourly while the "
                "other keeps a frozen annual anchor is the half-armed state "
                "rule 19 [R-ONE-MECH] exists to prevent"
            )
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "miso_seam_measured_ladder", False)
        ):
            from market_sim.model.transmission import (
                inject_miso_seam_ladder_prices,
            )

            neighbour = bool(
                getattr(config, "miso_seam_neighbour_anchored_ladder", False)
            )
            neighbour_hourly = bool(
                getattr(config, "miso_seam_neighbour_hourly_ladder", False)
            )
            neighbour_hourly_spp = bool(
                getattr(config, "miso_seam_neighbour_hourly_spp", False)
            )
            if inject_miso_seam_ladder_prices(
                fleet_arrays,
                mc_base,
                iso,
                year,
                neighbour_anchored=neighbour,
                neighbour_hourly=neighbour_hourly,
                neighbour_hourly_spp=neighbour_hourly_spp,
            ):
                logger.info(
                    "%s %d: seam bands repriced to the MEASURED per-seam Q-Q "
                    "ladders (EIA-930 flow durations x %s; "
                    "PJM/SPP/South, import + export; no added hurdle)",
                    iso,
                    year,
                    (
                        (
                            "HOURLY PJM western-border DA + measured spread "
                            "offsets on the PJM seam (miso-231) AND HOURLY SPP "
                            "NORTH hub DA + measured spread offsets on the SPP "
                            "seam (miso-233), MISO DA hub quantiles on South"
                            if neighbour_hourly_spp
                            else "HOURLY PJM western-border DA + measured "
                            "spread offsets on the PJM seam (miso-231), MISO "
                            "DA hub quantiles on SPP/South"
                        )
                        if neighbour_hourly
                        else (
                            "PJM WESTERN-BORDER DA quantiles on the PJM seam "
                            "(miso-225 neighbour-anchored), MISO DA hub "
                            "quantiles on SPP/South"
                            if neighbour
                            else "MISO DA hub quantiles"
                        )
                    ),
                )
        # [measured: per-seam Q-Q band ladders — PJM settlement-grade tie-line
        #  flow duration curves coupled with the measured PJM DA system LMP
        #  (interchange_config.PJM_SEAM_LADDER_BY_YEAR, scripts/
        #  derive_pjm_seam_ladders.py) | forecast substitute: the gas-elastic
        #  reference-price formula (hr_by_year two-track; pooled ladder = the
        #  forward story)]. Overwrites EVERY seam band (MISO/NYISO/Carolinas/
        # TVA/LGEE, both directions) with its measured revealed-supply-curve
        # price, so the direction-structural record (near-always export to
        # MISO/NYISO, near-always import from the south) the spot-spread
        # pricing inverts (pjm-95 2023: imports 46% of hours vs measured ~2%,
        # displacing CC_REGULAR) clears economically. The firm scheduled-
        # export floor is displaced on ladder years inside
        # apply_interchange_injections (alternatives, never stacked; rule 19).
        if (
            getattr(config, "reference_price_interface", False)
            and iso in INTERFACE_NEIGHBORS
            and iso != "CAISO"
            and getattr(config, "pjm_seam_measured_ladder", False)
        ):
            from market_sim.model.transmission import (
                inject_pjm_seam_ladder_prices,
            )

            # pjm-174: the hourly neighbour anchor is a SUB-GATE of this
            # injector — it can only arm inside the parent measured ladder,
            # and it displaces the parent's scalar band price per seam.
            neighbour_hourly = bool(
                getattr(config, "pjm_seam_neighbour_hourly_ladder", False)
            )
            if inject_pjm_seam_ladder_prices(
                fleet_arrays, mc_base, iso, year, neighbour_hourly=neighbour_hourly
            ):
                logger.info(
                    "%s %d: seam bands repriced to the MEASURED per-seam Q-Q "
                    "ladders (tie-line flow durations x PJM DA system "
                    "quantiles; MISO/NYISO/Carolinas/TVA/LGEE, import + "
                    "export; no added hurdle; firm-export floor displaced)%s",
                    iso,
                    year,
                    "; NEIGHBOUR-ANCHORED HOURLY overlay armed on the covered "
                    "seams (bands clear on the measured seam SPREAD)"
                    if neighbour_hourly
                    else "",
                )
        # [measured: WECC intertie hub LMP (Malin / Palo Verde, OASIS) per
        #  corridor | forecast substitute: caiso_intertie_reference_price —
        #  the forward (HH+basis)×HR×load-shape per-hub seam, which the
        #  shared sequence prices INSTEAD of this overlay when set]. The
        # caiso-51 keeper's headline seam: each per-hub corridor priced at
        # its OWN measured hub, firm/contracted tranches held at contract
        # cost under caiso_perhub_firm_base.
        if per_hub_intertie and not getattr(
            config, "caiso_intertie_reference_price", False
        ):
            from market_sim.model.transmission import (
                inject_caiso_per_hub_intertie_prices,
            )

            if inject_caiso_per_hub_intertie_prices(
                fleet_arrays,
                mc_base,
                iso,
                year,
                carbon_price,
                firm_base=getattr(config, "caiso_perhub_firm_base", False),
                gap_fill_measured_gas=getattr(
                    config, "caiso_intertie_gap_fill_measured_gas", False
                ),
                gap_fill_measured_dam=getattr(
                    config, "caiso_intertie_gap_fill_measured_dam", False
                ),
            ):
                logger.info(
                    "%s %d: per-hub WECC intertie — two signed corridors (Malin/COI "
                    "→ NP15, Palo Verde/Path-46 → SP15), each priced at its OWN "
                    "measured hub (per-hub basis + per-hub netting, arbitrage-free, "
                    "one direction per hour per corridor)%s",
                    iso,
                    year,
                    (
                        " — firm/contracted tranches held at contract cost "
                        "(caiso_perhub_firm_base)"
                        if getattr(config, "caiso_perhub_firm_base", False)
                        else ""
                    ),
                )
        # [measured: WECC intertie hub LMPs (Mid-C / Palo Verde) on the pooled
        #  legacy node, import + export sides | forecast substitute: the
        #  static ladder / the per-hub or reference seams]. Superseded by the
        # per-hub node; gated to the legacy pooled topology only.
        if legacy_intertie and getattr(config, "caiso_import_hub_prices", False):
            from market_sim.model.transmission import (
                inject_caiso_export_hub_prices,
                inject_caiso_import_hub_prices,
            )

            if inject_caiso_import_hub_prices(
                fleet_arrays, mc_base, iso, year, carbon_price
            ):
                logger.info(
                    "%s %d: import tranches repriced to measured WECC intertie "
                    "hub LMPs (Mid-C / Palo Verde) — static ladder bypassed",
                    iso,
                    year,
                )
            # Symmetric export side of the same bidirectional intertie, so the
            # tie can reverse to the measured +3.5 GW export.
            if inject_caiso_export_hub_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: neighbor-export sink repriced to the measured WECC "
                    "intertie hub LMP — intertie can reverse to export",
                    iso,
                    year,
                )
        # [measured: PJM / ISO-NE Day-Ahead system LMP (hourly) | forecast
        #  substitute: the year-grounded static ladder / a future NYISO
        #  reference seam]. NYISO analogue of the CAISO/MISO measured-hub
        # pricing; the monthly EIA-930 reconciliation band, HQ firm floor and
        # SIL cap are unchanged.
        if (
            iso == "NYISO"
            and priced_interchange
            and getattr(config, "nyiso_import_hub_prices", False)
        ):
            from market_sim.model.transmission import inject_nyiso_import_hub_prices

            if inject_nyiso_import_hub_prices(fleet_arrays, mc_base, iso, year):
                logger.info(
                    "%s %d: import tranches repriced to measured neighbor hourly "
                    "DA LMPs (PJM_west→PJM, ISONE_tie→NEISO, scarcity→hourly max, "
                    "export sink→hourly min) — static ladder bypassed",
                    iso,
                    year,
                )

    # Net load for the solar-shape coupling: the LP-served load (net of
    # must-run) less utility solar/wind generation — same convention as the
    # drag floors and the forecast runner.
    _interchange_net_load = None
    if getattr(config, "caiso_import_solar_shape", False):
        _interchange_net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
    # caiso-110: the endogenous WECC-West fleet REPLACES the import tranches, so
    # the CAISO import injectors (firm-shape/self-schedule, clean-depth surplus/
    # overnight/daytime, per-hub hub pricing, gas coupling) have nothing to price
    # and MUST NOT run — the West units are fuel_type="import" and would be
    # repriced away from their measured vom. One mechanism per phenomenon
    # (rule 18); the mutual exclusion is enforced here.
    if not _endogenous_wecc:
        apply_interchange_injections(
            fleet_arrays,
            mc_base,
            config,
            iso,
            year,
            carbon_price=carbon_price,
            gas_scenario=config.gas_price_path,
            net_load=_interchange_net_load,
            measured_overlay=_backcast_measured_interchange_prices,
        )
    else:
        # caiso-114: re-price the endogenous WECC-West GAS export units at the
        # MEASURED delivered West hub (+ CARB border carbon), hour-varying, via
        # an mc_base override — the import-price-injection pattern. Bare Henry-Hub
        # gas MC under-prices the West and floods the tie (caiso-110 diagnostic);
        # the measured hub sets the West's export price so the tie clears
        # interior. No-op (West stays on its Henry-Hub vom) when the measured hub
        # is unavailable or the endogenous node built no fleet.
        if _wecc_west_avail:
            from market_sim.data.wecc_west_fleet import build_wecc_west_thermal_mc

            _wecc_thermal_mc = build_wecc_west_thermal_mc(
                year, gas_price, carbon_price, config.hours
            )
            if _wecc_thermal_mc:
                _uid_to_row = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}
                for _uid, _mc in _wecc_thermal_mc.items():
                    _r = _uid_to_row.get(_uid)
                    if _r is not None:
                        mc_base[_r, : config.hours] = _mc[: config.hours]

    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc -= wind_eac
    solar_mc -= solar_eac
    # Floor the curtailable wind/solar offers at the negative keep-running
    # (REC/PTC) value so curtailed renewables can set a sub-$0 marginal price
    # in oversupply (CAISO negative midday LMPs). No-op unless
    # config.negative_renewable_offers is on; the floor is the more-negative of
    # the existing offer and -renewable_keep_running_value (so wind's PTC is not
    # double-counted). See market_sim.policy.eac.
    wind_mc, solar_mc = apply_negative_renewable_offer_floor(wind_mc, solar_mc, config)

    storage_units = load_eia860_storage(iso, year, config)
    storage = storage_units_to_arrays(storage_units, zone_names)
    # Static (n_storage,) caps, or hour-varying (n_storage, T) when the
    # intra-year COD ramp is on (config.storage_vintage_ramp) and capacity
    # was commissioned mid-year — mid-year GWs stay offline before COD.
    storage_power_cap, storage_energy_cap = storage_cap_profiles(
        storage_units, storage, config.hours
    )
    # Measured battery-fleet capability re-basis (ERCOT-66): replace the
    # EIA-860 COD-ramped battery power basis with the 60-Day DAM disclosure's
    # registered non-OUT storage HSL, keeping EIA-860 as the zone-split and
    # duration basis (ScenarioConfig.ercot_storage_capability_measured has the
    # full provenance note). Applied BEFORE the measured AS-award reservation
    # below, so the award subtracts from the measured capability — the same
    # ordering as reality's co-optimization.
    if (
        getattr(config, "ercot_storage_capability_measured", False)
        and iso == "ERCOT"
        and getattr(config, "mode", "forecast") == "backcast"
    ):
        from market_sim.model.storage import ercot_storage_capability_caps

        _pre_mean = float(
            np.asarray(storage_power_cap, dtype=float).sum(axis=0).mean()
            if np.asarray(storage_power_cap).ndim == 2
            else np.asarray(storage_power_cap, dtype=float).sum()
        )
        storage_power_cap, storage_energy_cap = ercot_storage_capability_caps(
            storage_power_cap,
            storage_energy_cap,
            storage_units,
            config.weather_year,
            config.hours,
        )
        logger.info(
            "ERCOT measured storage capability re-basis (%d): fleet power "
            "mean %.0f -> %.0f MW",
            config.weather_year,
            _pre_mean,
            float(np.asarray(storage_power_cap, dtype=float).sum(axis=0).mean()),
        )
    # Reserve the measured storage up-AS MW from the dispatch power cap so AS-
    # committed battery capacity cannot also arbitrage energy (ERCOT only).
    # SKIPPED under ercot_storage_as_endogenous (G5): the endogenous co-opt hands
    # the FULL battery cap to the LP and lets it choose energy vs AS, so the
    # measured-award subtraction must not apply (it would pre-commit the split).
    if (
        getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and iso == "ERCOT"
    ):
        storage_power_cap = reserve_storage_as_power(
            storage_power_cap, config.weather_year, config.hours
        )

    # Measured-award AS->energy CO-PARTICIPATION (ercot_storage_as_deployment,
    # the storage-cycling-lane fix; docs/DIAGNOSIS-ercot-storage-cycling-lane-
    # 2026-07.md). storage_as_commitment reserves the measured up-AS award out of
    # the discharge cap in every hour and never returns it to energy — but the
    # real fleet moves capacity from AS to energy at the net-load ramp (the
    # measured award declines from its midday peak into the evening). This forces
    # exactly that measured draw-down as a battery discharge FLOOR, so the ramp
    # co-participation the arbitrage-only LP misses enters the energy balance.
    # Rule 19: the floor draw-down = daily_peak(award) - award(t) sits INSIDE the
    # room the reservation left (cap = P - award(t) >= peak - award(t) since the
    # daily-peak award <= fleet power), so it releases exactly the reserved MW,
    # never stacked and never above the physical cap. Requires storage_as_commit-
    # ment (the reservation it reconciles with); off under the endogenous split.
    storage_discharge_min = None
    deploy_sys = None  # shared with the SOC reservation below (rule 19: the
    # deployed AS energy is subtracted from the SOC floor's backing)
    if (
        getattr(config, "ercot_storage_as_deployment", False)
        and getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and iso == "ERCOT"
        and int(config.weather_year)
        >= int(getattr(config, "ercot_storage_as_deployment_from_year", 2023))
        and storage.n_storage
    ):
        from market_sim.results.scarcity import ercot_storage_as_deployment_mw

        net_load = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        deploy_sys = ercot_storage_as_deployment_mw(
            config.weather_year, config.hours, net_load
        )  # (T,) system measured-award draw-down at the net-load ramp
        # Allocate across BATTERY units pro-rata by their (post-reservation)
        # available power — pumped storage is not an LESR and holds no measured
        # battery award (the reserve_storage_as_power / reserve_caiso pattern).
        batt = np.array(
            [u.tech_name != "pumped_storage" for u in storage_units], dtype=bool
        )
        pc = np.asarray(storage_power_cap, dtype=float)
        pc2 = np.repeat(pc[:, None], config.hours, axis=1) if pc.ndim == 1 else pc
        dmin = np.zeros((storage.n_storage, config.hours), dtype=float)
        if batt.any():
            bpow = pc2[batt]
            total = bpow.sum(axis=0)  # (T,) battery discharge cap available
            with np.errstate(divide="ignore", invalid="ignore"):
                weight = np.where(total[None, :] > 0.0, bpow / total[None, :], 0.0)
            dmin[batt] = np.minimum(weight * deploy_sys[None, :], bpow)
        storage_discharge_min = dmin
        logger.info(
            "ERCOT storage AS->energy deployment (%d): mean %.0f MW, max %.0f MW "
            "forced as a battery discharge floor at the net-load ramp",
            config.weather_year,
            float(deploy_sys.mean()),
            float(deploy_sys.max()),
        )

    # Measured AS SOC reservation (ercot_storage_as_soc_reserve, ercot-167 —
    # matrix §5.1 item 10, the ercot-162 §2 named successor). The power
    # reservation above withholds the measured award's MW from the discharge
    # cap but "reserves *power*, not state of charge" (its own docstring);
    # ERCOT Nodal Protocols §3.17.3 also requires the SOC BEHIND each award
    # (award × published product duration) to stay in the tank. This floors
    # battery SOC at Σ_p award_p(t) × duration_p, per-product shares measured
    # from the same 60-Day corpus, normalized to the SAME committed total the
    # power dock subtracts (rule 19: one award basis, both sides). Off /
    # missing series → None (byte-identical LP). Requires storage_as_commitment
    # (validated); off under the endogenous split (validated).
    storage_soc_min = None
    if (
        getattr(config, "ercot_storage_as_soc_reserve", False)
        and getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and iso == "ERCOT"
        and storage.n_storage
    ):
        from market_sim.model.storage import ercot_storage_as_soc_min

        _pc = np.asarray(storage_power_cap, dtype=float)
        if _pc.ndim == 1:
            _pc = np.repeat(_pc[:, None], config.hours, axis=1)
        soc_floor = ercot_storage_as_soc_min(
            storage_energy_cap,
            config.weather_year,
            config.hours,
            deploy_mw=deploy_sys,
            # Scaffold-reachability inputs (the 2023 probe measured the raw
            # floor infeasible against the daily SOC pin + award-docked power;
            # see _pin_reachability_clip): the post-dock power cap bounds both
            # charge and discharge in the LP, the deployment floor is the
            # forced discharge, and the pin applies whenever the daily-cycling
            # scaffold does.
            charge_cap=_pc,
            discharge_min=storage_discharge_min,
            eta_chg=np.array([u.eta_charge for u in storage_units], dtype=float),
            eta_dis=np.array([u.eta_discharge for u in storage_units], dtype=float),
            daily_pin=bool(
                getattr(config, "storage_daily_cycling", False)
                or getattr(config, "limited_foresight_dispatch", False)
            ),
        )
        if float(np.asarray(soc_floor).max()) > 0.0:
            storage_soc_min = soc_floor
            logger.info(
                "ERCOT storage AS SOC reservation (%d): fleet floor mean %.0f MWh, "
                "max %.0f MWh (award x product duration) held out of arbitrage",
                config.weather_year,
                float(np.asarray(soc_floor).sum(axis=0).mean()),
                float(np.asarray(soc_floor).sum(axis=0).max()),
            )

    # CAISO analogue (caiso_storage_as_reservation): reserve the measured
    # battery AS-award MW (Daily Energy Storage Report, storage-as-awards
    # clean datatype) out of the battery power cap, and floor the battery SOC
    # at the tariff 30-min sustain of the spin/non-spin awards
    # (CAISO_AS_SUSTAIN_DURATION_H). Batteries only — pumped storage is not an
    # LESR. Zero fitted parameters; see model.storage.
    if getattr(config, "caiso_storage_as_reservation", False) and iso == "CAISO":
        from market_sim.data.storage_as_awards import upward_award_mw
        from market_sim.model.storage import (
            caiso_storage_as_soc_min,
            reserve_caiso_storage_as_power,
        )

        storage_soc_min = caiso_storage_as_soc_min(
            storage_power_cap,
            storage_energy_cap,
            storage_units,
            config.weather_year,
            config.hours,
        )
        storage_power_cap = reserve_caiso_storage_as_power(
            storage_power_cap, storage_units, config.weather_year, config.hours
        )
        _upward = upward_award_mw("CAISO", config.weather_year, config.hours)
        logger.info(
            "CAISO storage-AS reservation (%d): upward award mean %.0f MW "
            "(max %.0f) reserved from battery power; SOC sustain floor mean "
            "%.0f MWh",
            config.weather_year,
            float(_upward.mean()),
            float(_upward.max()),
            float(storage_soc_min.sum(axis=0).mean()),
        )

    # Measured battery dispatch-shape envelope (caiso_storage_shape_anchor,
    # caiso-99 Mechanism B, GATED default off): cap the battery units' hourly
    # charge/discharge at the measured p95 hour-of-day rate per MW of fleet
    # (EIA-930 NG:OTH ÷ EIA-860 monthly fleet, committed rule-23 derivation) —
    # the AS-holdback/bid-conservatism capability the nameplate power cap
    # overstates. Composes with the COD vintage ramp already inside
    # storage_power_cap; pumped storage passes through. None (flag off /
    # other ISOs) leaves both keys unset — identical LP.
    storage_charge_cap = None
    storage_discharge_cap = None
    if getattr(config, "caiso_storage_shape_anchor", False) and iso == "CAISO":
        from market_sim.model.storage import caiso_storage_shape_caps

        storage_charge_cap, storage_discharge_cap = caiso_storage_shape_caps(
            storage_power_cap, storage_units, config.weather_year, config.hours
        )
        _pc2 = np.asarray(storage_power_cap, dtype=float)
        _pc2 = (
            np.repeat(_pc2[:, None], config.hours, axis=1) if _pc2.ndim == 1 else _pc2
        )
        logger.info(
            "CAISO storage shape envelope (%d): belly(10-14) charge cap mean "
            "%.0f MW vs fleet power %.0f MW; evening(17-21) discharge cap "
            "mean %.0f MW",
            config.weather_year,
            float(
                storage_charge_cap.sum(axis=0)[
                    np.isin(np.arange(config.hours) % 24, range(10, 15))
                ].mean()
            ),
            float(
                _pc2.sum(axis=0)[
                    np.isin(np.arange(config.hours) % 24, range(10, 15))
                ].mean()
            ),
            float(
                storage_discharge_cap.sum(axis=0)[
                    np.isin(np.arange(config.hours) % 24, range(17, 22))
                ].mean()
            ),
        )

    # Per-plant cited pump-power charge caps (caiso_ps_plant_params, lane 5 —
    # GATESPEC-caiso195, GATED default off): the per-plant PS units built by
    # load_eia860_pumped_storage carry cited pump-side ratings (Helms 930 MW
    # pumping vs 1,212 MW generating; Gianelli 375.8 vs 424 — PG&E / DWR
    # B132-22 motor ratings) as static charge caps on the SAME
    # storage_charge_cap channel the battery shape anchor uses — disjoint
    # unit rows, one channel (rule 19). Fires with or without the anchor so
    # the mechanism never silently depends on another gate (the caiso-98
    # dead-flag lesson); None (flag off / no cited rating) leaves the channel
    # exactly as the anchor block left it.
    if getattr(config, "caiso_ps_plant_params", False) and iso == "CAISO":
        from market_sim.model.storage import caiso_ps_charge_caps

        _ps_chg = caiso_ps_charge_caps(
            storage_power_cap, storage_units, config.hours, storage_charge_cap
        )
        if _ps_chg is not None:
            storage_charge_cap = _ps_chg
            _ps_rows = [
                u.unit_id
                for u in storage_units
                if getattr(u, "charge_power_cap_mw", None) is not None
            ]
            logger.info(
                "CAISO per-plant PS pump caps armed on %d unit(s): %s",
                len(_ps_rows),
                ", ".join(_ps_rows),
            )

    # Measured DA charge-allocation schedule (caiso_charge_allocation_schedule,
    # M1 — owner-granted caiso-103 belly ask, executed caiso-104; GATED default
    # off): floor each day's fleet battery charge in every measured-support
    # hour at alloc_share[hod] x da_frac x (day total charge) — the DAM
    # allocation conduct, volume-holding by construction (dispatch.
    # _build_storage_alloc_rows). Statistics from the committed rule-23
    # derive data/raw/reference/caiso-charge-allocation-profile.csv. None
    # (flag off / other ISOs) leaves the keys unset — identical LP.
    storage_alloc_params = None
    if getattr(config, "caiso_charge_allocation_schedule", False) and iso == "CAISO":
        from market_sim.model.storage import caiso_charge_allocation_params

        storage_alloc_params = caiso_charge_allocation_params(
            storage_units, config.weather_year, config.hours
        )
        _b_idx, _share, _dafrac = storage_alloc_params
        logger.info(
            "CAISO DA charge-allocation schedule (%d): %d battery units, "
            "da_frac %.4f, belly(10-14) share %.3f, active hods %d",
            config.weather_year,
            int(_b_idx.size),
            _dafrac,
            float(_share[10:15].sum()),
            int((_share[:24] > 0).sum()),
        )

    if fleet_only:
        # Availability-reconstruction exit (no LP): everything a post-solve
        # consumer needs to recompute pmax x availability per unit-hour,
        # the renewable potential (cf x cap) and the storage power caps,
        # aligned with the persisted bundle. ``mc_base`` / ``fuel_prices``
        # are the assembled P0 objective (fuel + VOM + carbon + NOx + EAC +
        # coal tranches, all pricing overlays applied) so post-solve offer-
        # stack diagnostics read the SAME offer prices the LP solved on —
        # never a re-derivation that could drift (G-22 idle-supply audit).
        # ``wind_mc`` / ``solar_mc`` complete that contract on the RENEWABLE
        # side: the fully assembled dispatch offers the LP is handed (IRA/PTC
        # dispatch credits, the PTC vintage blend where armed, exogenous EACs,
        # and the negative-renewable-offer floor), so a curve that has to place
        # the model's wind and solar alongside its generator rows reads the
        # SAME offer prices rather than re-deriving the credit sequence
        # outside the orchestrator (miso-150, the model-side universe fix).
        return {
            "config": config,
            "fleet": fleet,
            "fleet_arrays": fleet_arrays,
            "storage_units": storage_units,
            "storage": storage,
            "storage_power_cap": storage_power_cap,
            "wind_cf": wind_cf,
            "wind_cap": wind_cap,
            "solar_cf": solar_cf,
            "solar_cap": solar_cap,
            "wind_mc": wind_mc,
            "solar_mc": solar_mc,
            "demand": demand,
            "mc_base": mc_base,
            "fuel_prices": fuel_prices,
            # The year's topology-extended ISOConfig (external nodes, corridor
            # zones): ``fleet_arrays.zone_idx`` indexes ITS zone_names, which
            # the base ``get_iso_config(iso)`` does not carry.
            "iso_config": iso_config,
        }

    # caiso-157's fail-fast guard, WIRED (caiso-188). An armed mechanism whose
    # derived CLEAN partition is absent silently no-ops, and the bundle then
    # advertises in its meta/run_config a mechanism that never ran — which is
    # how the RETIRED fitted 7,500 MW WECC_import_simultaneous scalar re-became
    # CAISO's binding seam limit across five keeper promotions (caiso-157) and
    # then AGAIN across every promotion from caiso-175 onward, the designated
    # keeper included (FINDING-caiso188-import-tranche-dof-2026-08-09.md §4).
    # caiso-157 wrote the guard but its only call site was
    # pipeline/year.py::run_year_solve, which NOTHING calls — the backcast
    # orchestrator reaches the LP through run_energy_solve directly, so the
    # guard has never once run in a solve and the defect recurred. Wire it on
    # the solve path, AFTER the fleet_only exit so fleet-reconstruction probes
    # (caiso-131/134/140/150/151/188) still run against whatever is on disk.
    # No config field, no threshold, no tunable: a pure config-vs-disk
    # assertion, and a no-op for every flag left at its default.
    #
    # caiso-190: strict=True is stated explicitly (it is also the default) —
    # THIS is the lane keepers are promoted from, so even a mechanism with a
    # DECLARED fallback is fatal here. A CAISO run that arms
    # capacity_deliverability_limits without the MIC partition would otherwise
    # solve on the baked 7,500 MW fitted scalar and register a bundle claiming
    # the published cap, which is exactly what happened from caiso-175 onward
    # (FINDING-caiso188 §4). The forecast orchestrator passes strict=False;
    # the asymmetry is deliberate and documented in input_completeness.
    check_clean_partitions(config, iso, strict=True)

    # Oil-burn inventory budget (NEISO-gated). When the budget binds in a
    # cold-snap month, its dual is the scarcity rent that lifts the persisted P1
    # LMP above the flat dual-fuel oil-parity cap (~$258).
    #
    # Two derivations of the same LP mechanism (dispatch._build_oil_budget_rows):
    #   - neiso_winter_fuel_inventory (Component A, keeper path): forward-
    #     derivable capacity/logistics budget (tank fill + re-supply) over the
    #     oil-primary + dual-fuel oil-limb fleet, the limb gated to its exogenous
    #     oil-switch hours (dual_fuel_oil_mask) so gas generation is never
    #     capped. One pooled fleet row per winter month, MMBtu-weighted.
    #   - neiso_oil_burn_budget (superseded): EIA-923 petroleum RECEIPTS, a
    #     measured deliveries-to-tank OUTCOME inadmissible under CLAUDE.md #13.
    #     Kept only as a reference path; never a keeper.
    oil_monthly_budget = None
    oil_budget_gen_idx = None
    oil_budget_month_index = None
    oil_budget_gen_hour_coeff = None
    oil_budget_group_index = None
    if getattr(config, "neiso_winter_fuel_inventory", False):
        from market_sim.data.winter_fuel_inventory import build_winter_fuel_budget

        _wf = build_winter_fuel_budget(
            iso,
            fleet_arrays,
            dual_fuel_oil_mask,
            start_fill_bbl=getattr(config, "neiso_winter_fuel_start_fill_bbl", None),
            hours=config.hours,
        )
        if _wf is not None:
            (
                oil_budget_gen_idx,
                oil_monthly_budget,
                oil_budget_month_index,
                oil_budget_gen_hour_coeff,
                oil_budget_group_index,
            ) = _wf
            _fin = np.isfinite(oil_monthly_budget)
            logger.info(
                "winter fuel-inventory budget (%s %d): %d oil-capable gens, "
                "start_fill=%s bbl, %d winter month(s) constrained, "
                "monthly cap %.2f M MMBtu (~%.2f TWh @HR10.8)",
                iso,
                year,
                oil_budget_gen_idx.size,
                (
                    f"{getattr(config, 'neiso_winter_fuel_start_fill_bbl', None):.0f}"
                    if getattr(config, "neiso_winter_fuel_start_fill_bbl", None)
                    else "2.8M(default)"
                ),
                int(_fin.sum()),
                float(oil_monthly_budget[_fin].max()) / 1e6 if _fin.any() else 0.0,
                float(oil_monthly_budget[_fin].max()) / 10.8 / 1e6
                if _fin.any()
                else 0.0,
            )
    elif getattr(config, "neiso_oil_burn_budget", False):
        from market_sim.data.fuel import load_oil_burn_budget

        _oil_result = load_oil_burn_budget(
            iso,
            year,
            fleet_arrays,
        )
        if _oil_result is not None:
            oil_budget_gen_idx, oil_monthly_budget = _oil_result

    # Coal fuel-inventory budget (MISO-gated, backcast only). The missing
    # CEILING on coal: coal carries take-or-pay and must-run FLOORS and nothing
    # caps its energy, so the LP cannot represent "the fleet drew its stockpile
    # down in one year and could only burn what it received in the next"
    # (FINDING-miso256 section 4 / FINDING-miso258). Rule 19 [R-ONE-MECH]: a
    # MISSING LIMB, not a competing mechanism — there is no incumbent coal
    # ceiling, and this is never stacked on a coal floor.
    #
    # Reaches lp/rows.py::_build_oil_budget_rows through its OWN coal_* kwarg
    # family, so the coal and NEISO-oil budgets append as separate independent
    # row families and can never silently overwrite one another.
    #
    # Rule 13 [R-MEASURED]: every sizing quantity predates `year` — the
    # footprint's December ending stock of year-1 plus mean receipts over
    # year-2 and year-1. The builder returns None (leaving the solve
    # byte-identical) when either measured input is missing; a missing input is
    # never substituted.
    # UNSET, not None: DispatchSpec drops UNSET fields outright, so an UNARMED
    # run's dispatch-kwargs KEY SET is unchanged and its LP is byte-identical --
    # the same discipline hydro_period_hours uses a few lines below.
    coal_monthly_budget = UNSET
    coal_budget_gen_idx = UNSET
    coal_budget_month_index = UNSET
    coal_budget_gen_hour_coeff = UNSET
    coal_budget_group_index = UNSET
    if getattr(config, "coal_fuel_inventory", False):
        if iso.upper() != "MISO":
            raise ValueError(
                "coal_fuel_inventory is MISO-gated (rule 25 [R-ISO-SCOPE]): its "
                "footprint crosswalk and delivery-rate construction were "
                f"identified on MISO's own market, not {iso}'s. Arming it for "
                "another ISO needs that ISO's own evidence and its own matrix "
                "cell, which enters as U."
            )
        if config.mode != "backcast":
            raise ValueError(
                "coal_fuel_inventory is backcast-only: a forecast year's "
                "opening stock is the model's OWN carried inventory from the "
                "prior simulated year, and that carry is not built yet. "
                "Arming it in forecast mode would read a measured prior-year "
                "stock into a forward run."
            )
        from market_sim.data.coal_fuel_inventory import build_coal_fuel_budget

        _coal_result = build_coal_fuel_budget(
            fleet_arrays,
            year,
            hours=config.hours,
        )
        if _coal_result is None:
            logger.warning(
                "coal fuel-inventory budget (%s %d): NOT APPLIED — no coal "
                "generators, or no curated opening stock / prior-years "
                "delivery rate for this year. The solve is byte-identical to "
                "an unarmed run; the budget is never sized on a substitute.",
                iso,
                year,
            )
        else:
            (
                coal_budget_gen_idx,
                coal_monthly_budget,
                coal_budget_month_index,
                coal_budget_gen_hour_coeff,
                coal_budget_group_index,
                _coal_prov,
            ) = _coal_result
            logger.info(
                "coal fuel-inventory budget (%s %d): %d coal gens over %d "
                "plants (%d shared-storage), opening stock %.2f Mt + delivery "
                "rate %.2f Mt/yr (from %s) @ %.3f MMBtu/ton -> annual %.1f "
                "TWh-equiv @HR10.661, monthly cap %.2f M MMBtu",
                iso,
                year,
                _coal_prov.n_generators,
                _coal_prov.n_plants,
                _coal_prov.n_storage_entities,
                _coal_prov.opening_stock_tons / 1e6,
                _coal_prov.delivery_rate_tons_per_year / 1e6,
                "+".join(str(y) for y in _coal_prov.rate_source_years),
                _coal_prov.mmbtu_per_ton,
                _coal_prov.annual_budget_mmbtu / 10.661 / 1e6,
                _coal_prov.monthly_budget_mmbtu / 1e6,
            )

    # miso-268 per-coal-yard ANNUAL budget rows (coal_fuel_inventory_plant_grain,
    # default off). The pooled rows above treat every yard's stock and receipts
    # as one fleet pile; these cap each yard's annual coal energy input at its OWN
    # Dec(Y-1) stock plus prior-years receipts. Same measured inputs and rule-13
    # admissibility as the pooled budget; only the partition changes. UNSET when
    # off, so an unarmed run's dispatch-kwargs key set and LP are unchanged.
    coal_plant_budget = UNSET
    coal_plant_gen_idx = UNSET
    coal_plant_month_index = UNSET
    coal_plant_gen_hour_coeff = UNSET
    coal_plant_group_index = UNSET
    if getattr(config, "coal_fuel_inventory_plant_grain", False):
        if not getattr(config, "coal_fuel_inventory", False):
            raise ValueError(
                "coal_fuel_inventory_plant_grain is the plant grain OF "
                "coal_fuel_inventory and is inert without it: arm both, or "
                "neither (rule 19 [R-ONE-MECH])."
            )
        from market_sim.data.coal_fuel_inventory import build_coal_plant_budget

        _cp = build_coal_plant_budget(fleet_arrays, year, hours=config.hours)
        if _cp is None:
            logger.warning(
                "coal per-yard budget (%s %d): NOT APPLIED — no yard carries a "
                "curated stock or receipt record. Never sized on a substitute.",
                iso,
                year,
            )
        else:
            (
                coal_plant_gen_idx,
                coal_plant_budget,
                coal_plant_month_index,
                coal_plant_gen_hour_coeff,
                coal_plant_group_index,
                _cp_prov,
            ) = _cp
            logger.info(
                "coal per-yard budget (%s %d): %d yards, %d coal gens rowed "
                "(%d unrowed: no curated record), annual %.1f TWh-equiv "
                "@HR10.661 (rate from %s)",
                iso,
                year,
                _cp_prov.n_entities,
                _cp_prov.n_generators,
                _cp_prov.n_unrowed_generators,
                _cp_prov.annual_budget_mmbtu / 10.661 / 1e6,
                "+".join(str(y) for y in _cp_prov.rate_source_years),
            )

    # Base dispatch kwargs + priced import-node band: the shared pipeline
    # assembly (orchestrator-unification Stage 2) — the same key set the
    # inline dict carried, byte-identical values. The backcast-only keys
    # (ttc_import, oil_*) are passed explicitly so they stay present (possibly
    # None-valued) exactly as before; the forecast assembly leaves them UNSET.
    dispatch_spec = DispatchSpec(
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        # Load-shed penalty = the ISO's own energy bid cap (ISOConfig.voll),
        # not the ERCOT-flavored ScenarioConfig default ($5,000). NYISO/CAISO/
        # MISO/PJM cap verifiable energy offers at $2,000 (FERC Order 831);
        # ERCOT at $5,000. Using the per-ISO cap makes scarcity hours price at
        # the ceiling the market actually clears against.
        voll=iso_config.voll,
        incidence=incidence,
        ttc=ttc,
        # Import-direction bound when the measured ERCOT GTC overlay made the
        # export caps hourly/asymmetric; None keeps the symmetric -ttc.
        ttc_import=ttc_import,
        # ERCOT West Texas Export corridor VRE curtailment ceilings (WP-B);
        # None off-corridor / driver-off leaves the uncurtailed CF bound.
        wind_curtail_share=wind_curtail_share,
        solar_curtail_share=solar_curtail_share,
        storage_power_cap=storage_power_cap,
        storage_energy_cap=storage_energy_cap,
        storage_zone_idx=storage.zone_idx,
        eta_chg=storage.eta_chg,
        eta_dis=storage.eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_eac,
        storage_discharge_cost=storage.vom,
        rps_target=None,
        storage_daily_cycle_hours=24 if config.storage_daily_cycling else None,
        interface_groups=interface_groups or None,
        # One-way links (MISO's RDT 3,000/2,500 MW directional pair) floor
        # their flow at 0 instead of -ttc. Every other ISO's links are
        # bidirectional (all-True array -> byte-identical bounds). This was
        # built in dispatch but never wired here, so the RDT asymmetry was
        # silently symmetric (+/-ttc per leg) before the six-zone refinement.
        link_bidirectional=get_link_bidirectional_array(iso_config.links),
        # Priced RDT TCDC tiers (miso_rdt_tcdc): $/MWh on the tiered one-way
        # links' directed flow; None (all links free) is byte-identical.
        link_flow_cost=get_link_flow_cost_array(iso_config.links),
        # Marginal loss fractions on the one-way Midwest loss pairs
        # (miso_zonal_loss_surface): (n_links, T) receiving-side losses from
        # the derived delivery-factor surface; None (flag off / other ISOs)
        # keeps the ±1 incidence coefficients — byte-identical.
        # PJM (pjm_zonal_loss_surface) rides the same seam with its own
        # per-ISO surface; the two flags are ISO-gated inside their builders
        # so they can never both fire in one solve (rule 25).
        link_loss=(
            build_miso_link_loss(iso_config.links, iso, year, int(demand.shape[1]))
            if getattr(config, "miso_zonal_loss_surface", False)
            else (
                build_pjm_link_loss(iso_config.links, iso, year, int(demand.shape[1]))
                if getattr(config, "pjm_zonal_loss_surface", False)
                else (
                    build_caiso_link_loss(
                        iso_config.links, iso, year, int(demand.shape[1])
                    )
                    if getattr(config, "caiso_zonal_loss_surface", False)
                    else (
                        build_nyiso_link_loss(
                            iso_config.links, iso, year, int(demand.shape[1])
                        )
                        if getattr(config, "nyiso_zonal_loss_surface", False)
                        else None
                    )
                )
            )
        ),
        hydro_monthly_energy=hydro_monthly_energy,
        hydro_gen_idx=hydro_gen_idx,
        # Per-plant hydro budget period from the project's own governing
        # instrument (nyiso-220). UNSET unless armed AND this ISO has
        # registry entries, so every other run's dispatch-kwargs key set --
        # and therefore its LP -- is unchanged. The BACKCAST orchestrator's
        # own assembly; runner.py's forecast loop wires the same value
        # through the same shared resolver.
        hydro_period_hours=resolve_hydro_period_hours(
            iso, fleet, hydro_gen_idx, config
        ),
        # Hydraulic-cascade coupling (NWPP-36, owner ruling N3). UNSET unless
        # armed AND this ISO-year has a measured cascade artifact resolving
        # onto the fleet, so every other run's dispatch-kwargs key set -- and
        # therefore its LP -- is unchanged. Same shared resolver as runner.py.
        hydro_cascade=resolve_hydro_cascade(
            iso,
            year,
            fleet,
            hydro_gen_idx,
            config,
            hydro_monthly_energy=hydro_monthly_energy,
        ),
        oil_monthly_budget=oil_monthly_budget,
        oil_gen_idx=oil_budget_gen_idx,
        oil_month_index=oil_budget_month_index,
        oil_gen_hour_coeff=oil_budget_gen_hour_coeff,
        oil_group_index=oil_budget_group_index,
        coal_monthly_budget=coal_monthly_budget,
        coal_gen_idx=coal_budget_gen_idx,
        coal_month_index=coal_budget_month_index,
        coal_gen_hour_coeff=coal_budget_gen_hour_coeff,
        coal_group_index=coal_budget_group_index,
        coal_plant_budget=coal_plant_budget,
        coal_plant_gen_idx=coal_plant_gen_idx,
        coal_plant_month_index=coal_plant_month_index,
        coal_plant_gen_hour_coeff=coal_plant_gen_hour_coeff,
        coal_plant_group_index=coal_plant_group_index,
        T=config.hours,
    )
    dispatch_kwargs = build_base_dispatch_kwargs(
        dispatch_spec, import_node_recon=import_node_recon
    )
    # Overgeneration-dump guard domain (dump_cost_full_offer_domain, GATED
    # default off — caiso-139): widen build_cost_vector's dump price over every
    # offer that can reach a dumpable node, so a measured-hub import tranche
    # priced below -dump_cost can no longer generate purely to dump. Flag off
    # leaves the key unset — identical LP.
    if getattr(config, "dump_cost_full_offer_domain", False):
        dispatch_kwargs.update(dump_cost_full_offer_domain=True)
    # Measured storage-AS SOC sustain floor (caiso_storage_as_reservation,
    # GATED default off): the power-cap leg is already inside
    # storage_power_cap above; this adds the (n_storage, T) SOC lower bound.
    # None (flag off / other ISOs) leaves the key unset — identical LP.
    if storage_soc_min is not None:
        dispatch_kwargs.update(storage_soc_min=storage_soc_min)
    # Measured-award AS->energy deployment floor (ercot_storage_as_deployment):
    # the (n_storage, T) battery discharge lower bound. None (flag off / other
    # ISOs / no award file) leaves the key unset — identical LP.
    if storage_discharge_min is not None:
        dispatch_kwargs.update(storage_discharge_min=storage_discharge_min)
    # Measured battery dispatch-shape envelope (caiso_storage_shape_anchor):
    # the (n_storage, T) charge/discharge upper bounds. None (flag off / other
    # ISOs) leaves the keys unset — identical LP.
    if storage_charge_cap is not None:
        dispatch_kwargs.update(
            storage_charge_cap=storage_charge_cap,
            storage_discharge_cap=storage_discharge_cap,
        )
    # Measured DA charge-allocation schedule (caiso_charge_allocation_schedule,
    # M1): the per-day allocation floor rows' inputs. None (flag off / other
    # ISOs / no batteries) leaves the keys unset — identical LP.
    if storage_alloc_params is not None and storage_alloc_params[0].size:
        dispatch_kwargs.update(
            storage_alloc_batt_idx=storage_alloc_params[0],
            storage_alloc_share=storage_alloc_params[1],
            storage_alloc_da_frac=storage_alloc_params[2],
        )
    # ERCOT measured RT storage discharge-offer surface (ercot_storage_rt_offer_
    # surface, GATED default off — ercot-162): split each ERCOT battery unit's
    # discharge into K priced tranches at the measured per-net-load-bin
    # absolute-$ SCED ladder, REPLACING the flat battery_dispatch_adder on ERCOT
    # battery discharge (rule 19; PS + other ISOs untouched). The tranche width
    # fractions apply to the FINAL storage_power_cap above (measured capability
    # net of the AS reservation — the HASL-net energy headroom the ladder
    # measured), so they price exactly the energy-side discharge. Backcast-only
    # (the measured surface is a backcast overlay); None (flag off / other ISOs /
    # year absent / no batteries) leaves the keys unset — identical LP.
    if (
        getattr(config, "ercot_storage_rt_offer_surface", False)
        and iso == "ERCOT"
        and getattr(config, "mode", "forecast") == "backcast"
        and storage.n_storage
    ):
        from market_sim.model.storage import ercot_storage_rt_offer_tranches

        net_load_rt = (
            demand.sum(axis=0)
            - (solar_cap[:, None] * solar_cf).sum(axis=0)
            - (wind_cap[:, None] * wind_cf).sum(axis=0)
        )
        tranche_params = ercot_storage_rt_offer_tranches(
            storage_units, config.weather_year, net_load_rt, config.hours
        )
        if tranche_params is not None:
            arm_idx, width_frac, price_KT = tranche_params
            dispatch_kwargs.update(
                dis_tranche_arm_idx=arm_idx,
                dis_tranche_width=width_frac,
                dis_tranche_price=price_KT,
            )
            logger.info(
                "ERCOT storage RT offer surface (%d): %d battery units armed, "
                "K=%d tranches; tranche-price range $%.0f–$%.0f/MWh (replaces "
                "the flat $%.0f battery_dispatch_adder on ERCOT battery discharge)",
                config.weather_year,
                int(arm_idx.size),
                int(width_frac.size),
                float(price_KT.min()),
                float(price_KT.max()),
                float(getattr(config, "battery_dispatch_adder", 0.0)),
            )
        else:
            logger.info(
                "ERCOT storage RT offer surface (%d): no admissible ladder "
                "(year absent / artifact missing) — arm inert, flat adder retained",
                config.weather_year,
            )
    # Declared-window ELMP emergency-tier pricing (maxgen_emergency_tier_
    # pricing, GATED default off — the MISO F5 scarcity-depth lane): inside a
    # maxgen-events registry window declared at Max Gen Warning or higher,
    # the declared region's zones reprice the load slack from the ISO bid cap
    # to min(voll, tier floor) — $500 Tier 1 (Warning/Step 1), $1,000 Tier 2
    # (Step 2+), SOM-footnoted (config.reserve_config citations; frozen
    # design docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md).
    # Backcast-only overlay (D-5): this orchestrator is the backcast path;
    # the forecast runner never arms it. None (flag off / no Warning+ window
    # overlapping the year) leaves the key unset — identical LP.
    if getattr(config, "maxgen_emergency_tier_pricing", False):
        from market_sim.data.maxgen_events import emergency_tier_slack_cost

        _tier_slack = emergency_tier_slack_cost(
            iso, year, list(zone_names), iso_config.voll, config.hours
        )
        if _tier_slack is not None:
            dispatch_kwargs.update(slack_cost=_tier_slack)
    # Emissions mass-cap rows (policy constraint path, gated; G-29). Mirrors
    # runner.py's forecast-path `mass_caps` block so the backcast calibration
    # harness shares the identical seam — before this wire-through,
    # mass_cap_enabled was never reachable here at all (`get_active_policy_
    # constraints` had no caller in either run_calibration.py or
    # run_calibration_full.py). Default off -> {} -> no dispatch_kwargs
    # change, identical LP. See docs/handoffs/emissions-mass-cap-plan-2026-07.md.
    dispatch_kwargs.update(
        build_mass_cap_dispatch_kwargs(config, year, zone_names, fleet_arrays)
    )

    # Plant-group hourly ramp envelopes (config.ramp_limits, GATED default
    # off): CAMPD-measured trajectory bounds per plant group per hour
    # transition (model/dispatch._build_ramp_rows; design
    # docs/ramp-locational-design-2026-07.md §1). Mirrored in runner.py so
    # the forecast path shares the mechanism (forecast parity, design §4).
    # No-op (identical LP) when off or when the ISO has no envelope artifact.
    if config.ramp_limits:
        from market_sim.data.fleet import build_ramp_groups

        ramp_groups = build_ramp_groups(fleet_arrays, iso)
        if ramp_groups is not None:
            r_gen_idx, r_group_col, r_up, r_dn = ramp_groups
            dispatch_kwargs.update(
                ramp_gen_idx=r_gen_idx,
                ramp_group_col=r_group_col,
                ramp_up_mw=r_up,
                ramp_dn_mw=r_dn,
            )
            logger.info(
                "%s %d: ramp envelopes on %d plant groups (%d member tranches)",
                iso,
                year,
                r_up.size,
                r_gen_idx.size,
            )

    # Local-capacity (LCR-area) minimum-generation rows
    # (config.local_capacity_constraints, GATED default off): published-study
    # load-pocket relaxation (design §3), RHS from the LCR report parameters
    # scaled by this year's zonal load shape. Mirrored in runner.py (forecast
    # parity). No-op when off or the ISO has no covered areas / crosswalk.
    if getattr(config, "local_capacity_constraints", False):
        from market_sim.data.local_capacity import build_local_capacity_specs

        lcr_specs, _lcr_meta = build_local_capacity_specs(
            iso,
            year,
            fleet_arrays.plant_code,
            fleet_arrays.pmax,
            fleet_arrays.availability,
            zone_names,
            demand,
            storage.zone_idx,
            storage_power_cap,
        )
        if lcr_specs:
            dispatch_kwargs.update(local_capacity_specs=lcr_specs)

    # Hydro hourly deliverability envelope (config.hydro_dispatch_envelope,
    # GATED default off): fleet-wide hourly ceiling at the measured
    # per-(month x hod) percentile of EIA-930 NG:WAT — bounds the budget LP's
    # perfect-foresight hoarding of the monthly hydro energy into the top
    # price hours (caiso-72 STEP-2; FINDING-caiso72-step0). Mirrored in
    # runner.py (forecast parity — a forecast year falls back to the pooled
    # climatology envelope inside the loader). No-op (identical LP) when off,
    # no hydro fleet, or no measured series.
    if (
        getattr(config, "hydro_dispatch_envelope", False)
        and hydro_gen_idx is not None
        and len(hydro_gen_idx)
    ):
        from market_sim.data.eia_loader import measured_hydro_hourly_envelope

        env = measured_hydro_hourly_envelope(iso, year, config.hours)
        if env is not None:
            # Feasibility guard: never cap below the fleet's own hourly lower
            # bounds (min_gen floors / pmin).
            h_idx = np.asarray(hydro_gen_idx, dtype=int)
            if getattr(fleet_arrays, "min_gen", None) is not None:
                lo = fleet_arrays.min_gen[h_idx, : config.hours].sum(axis=0)
            else:
                lo = np.full(config.hours, fleet_arrays.pmin[h_idx].sum())
            env = np.maximum(env, lo)
            # CISO's NG:WAT includes pumped-storage net output (no separate
            # PS series), so the capped model quantity includes PS net
            # discharge — like-for-like with the measured envelope.
            ps_idx = np.flatnonzero(
                np.char.startswith(np.asarray(storage.tech_names, dtype=str), "pumped")
            )
            dispatch_kwargs.update(
                hydro_envelope_gen_idx=h_idx,
                hydro_envelope_mw=env,
                hydro_envelope_storage_idx=(ps_idx if ps_idx.size else None),
            )
            logger.info(
                "%s %d: hydro deliverability envelope on %d units "
                "(evening p95 %.0f MW)",
                iso,
                year,
                h_idx.size,
                float(np.quantile(env, 0.95)),
            )

    # Energy+reserve co-optimization: the shared pipeline wrapper
    # (orchestrator-unification Stage 2) — the per-ISO reserve designs live in
    # config/reserve_config.py (get_reserve_design), already shared with the
    # forecast runner; the wrapper owns the gate (energy_reserve_coopt, CAISO
    # excluded), the forward-driver threading, the merge, and the logging.
    # Collapses the former per-ISO elif ladder, byte-identically:
    #   * the hand-built PJM zone-aggregate block == reserve_config._pjm_design
    #     (measured Primary requirement + published ORDC — only the last ORDC
    #     step width depends on the requirement scalar and the design sets it
    #     to max(req), the same value — + deliverable supply cap + online gate);
    #   * the post-design ERCOT RTOLCAP supply-cap overwrite is folded into the
    #     designs themselves (audit gap A5): in backcast mode the design's
    #     internal ercot_rtolcap_supply_cap_mw call returns the same measured
    #     parquet series the overwrite applied.
    # sim_year=year is value-identical here: the backcast pins weather_year to
    # the solve year and every sim_year consumer falls back to weather_year.
    reserve_design = apply_reserve_coopt(
        dispatch_kwargs,
        config,
        fleet_arrays,
        config.hours,
        zone_names,
        system_load=demand.sum(axis=0),
        wind_gen=(wind_cap[:, None] * wind_cf).sum(axis=0),
        solar_gen=(solar_cap[:, None] * solar_cf).sum(axis=0),
        sim_year=year,
    )
    # ERCOT standalone energy-only commitment-posture (ercot_commitment_posture,
    # docs/handoffs/ercot-commitment-thinness-2026-07.md): reserve-decoupled, so
    # merged as its own dispatch kwargs after the reserve seam. No-op / byte-
    # identical for every non-ERCOT run and default-off ERCOT.
    apply_ercot_commitment_posture(dispatch_kwargs, config, fleet_arrays)

    # P0 → monthly startup markup → P1 via the shared pipeline solve core
    # (orchestrator-unification Stage 3): the intra-year warm start, the
    # cross-year warm-start seam (xyear_cache threaded from the multi-year
    # loop, basis exported even when the XYEAR flag is off so a downstream A/B
    # does not depend on call ordering), and the startup-markup config gates
    # all moved to pipeline.solve.run_energy_solve statement-for-statement.
    # P1-native CAISO RA must-offer bridge: the hook floors the merchant gas
    # CC/CT fleet from the P0 run pattern before the P1 clearing solve, so the
    # RA structure rides the scored P1 pass (P2 is archived — CLAUDE.md: P0/P1
    # only). None for every non-CAISO / non-RA run (byte-identical).
    ra_p1_prep = build_caiso_ra_p1_prep(
        config,
        iso,
        fleet,
        fleet_arrays,
        mc_base,
        renewable_potential_mw=(
            (wind_cap[:, None] * wind_cf) + (solar_cap[:, None] * solar_cf)
        ).sum(axis=0),
    )
    # P1-native ERCOT gas commitment bridge (ERCOT-63): the committed-state
    # floor on the merchant gas-CC fleet, detected from the P0 run pattern —
    # the ISO-exclusive sibling of the CAISO hook above. None for every
    # non-ERCOT / gate-off run (byte-identical).
    ercot_bridge_prep, ercot_bridge_bid_prep = build_ercot_gas_bridge_p1_preps(
        config,
        iso,
        fleet,
        fleet_arrays,
        mc_base,
        floorscoped_markdown_fn=floorscoped_markdown_fn,
    )
    # ercot-227 F3 (Amendment 3): chain the measured RUC-instruction floor
    # after the bridge's (works with the bridge on or off; ISO/flag-gated
    # inside — every other path returns the prep unchanged, byte-identical).
    from market_sim.pipeline.commitment import wrap_ercot_ruc_floor_prep

    ercot_bridge_prep = wrap_ercot_ruc_floor_prep(
        config, iso, fleet_arrays, ercot_bridge_prep
    )
    # P1-native NYISO gas commitment bridge (nyiso-87): the committed-state
    # floor on the merchant slow-start gas fleet (CC_REGULAR + ST_GAS by unit
    # physics) — minimum run duration, minimum down time and the
    # startup-restart inequality, all read off the P0 run pattern. The
    # ISO-exclusive sibling of the two hooks above; None for every non-NYISO /
    # gate-off run (byte-identical).
    nyiso_bridge_prep = build_nyiso_gas_bridge_p1_prep(
        config, iso, fleet, fleet_arrays, mc_base
    )
    # P1-native SPP gas commitment bridge (SPP-44): the SPP leg of the same
    # family on SPP's merchant slow-start gas fleet (CC_REGULAR + ST_GAS by
    # unit physics) at its measured plant-basis minimum stable load, read off
    # the P0 run pattern. The ISO-exclusive sibling of the three hooks above;
    # None for every non-SPP / gate-off run (byte-identical).
    spp_bridge_prep = build_spp_gas_bridge_p1_prep(
        config, iso, fleet, fleet_arrays, mc_base
    )
    # P1-native SOCO gas-steam CAMPAIGN commitment floor (SOCO-53d): the SOCO
    # leg of the same family, and the only one whose object is a multi-WEEK
    # campaign rather than an overnight or midday gap. Measured minimum-run
    # extension + online-hours LSL state floor on SOCO's campaign-duty gas
    # boilers at their own measured plant-basis minimum stable load; the restart
    # legs are NOT armed (SOCO's boilers do not two-shift). The ISO-exclusive
    # sibling of the four hooks above; None for every non-SOCO / gate-off run
    # (byte-identical).
    soco_campaign_prep = build_soco_gas_st_campaign_p1_prep(
        config, iso, fleet, fleet_arrays
    )
    # P1-native MISO regulated-coal night floor (miso-113): the committed-state
    # floor on the regulated PRB/subbituminous fleet at each plant's OWN
    # measured within-run night level, net of its _mustrun band (rule 19), on
    # the P0-detected committed run. The ISO-exclusive sibling of the
    # CAISO/ERCOT/NYISO hooks above; None for every non-MISO / gate-off run
    # (byte-identical).
    miso_night_floor_prep = build_miso_coal_night_floor_p1_prep(
        config, iso, fleet, fleet_arrays
    )
    # P1-native PJM commitment-scoped reserve supply (path B, G-20b): the fleet
    # hook zeroes non-fast-start reserve-eligible units' availability in their
    # plant's P0-offline hours (the fa_p2-style mask), the kwargs hook
    # recomputes the deliverable reserve-supply cap on the masked fleet. (None,
    # None) for every non-PJM / gate-off run (byte-identical). ISO-exclusive
    # with the CAISO hook, so at most one fleet prep is ever non-None.
    pjm_fleet_prep, pjm_kwargs_prep = build_pjm_reserve_p1_prep(
        config, iso, fleet_arrays
    )
    # P1-native CAISO online-scoped reserve split (caiso_reserve_online_scoped):
    # the kwargs hook recomputes the (2*n_r, T) spin/non-spin product-split
    # ramp caps from the P0 run pattern — SPIN scoped to online iron, NONSPIN
    # to offline fast-start (pipeline.commitment.caiso_pergen_sync_reserve_caps).
    # None for every non-CAISO / gate-off run (byte-identical); ISO-exclusive
    # with the PJM kwargs hook. Composes with the CAISO RA-bridge fleet hook.
    caiso_reserve_kwargs_prep = build_caiso_reserve_p1_prep(config, iso, fleet_arrays)
    # ercot-219 stages 2-3 (B-1; PRECOMMIT-ercot219 §1.2-§1.3): the within-day
    # exhaustion expectation and the P1-only storage reservation-price offer.
    # Stage 2 is computed here — after fleet assembly (so it sees the
    # post-stage-1 reconciled availability) and after apply_reserve_coopt (so
    # the armed *_withheld families' LP requirement rows are read from the
    # SAME resolved design the solve binds, zero re-implementation) — from the
    # model's own state and registered constants only. No price, no residual,
    # no measured outcome enters. Stage 3 hands run_energy_solve the
    # (n_storage, T) P1-only discharge re-cost; P0 is untouched by seam.
    p1_storage_discharge_cost = None
    ercot219_exhaustion = None
    if iso == "ERCOT" and getattr(config, "ercot_exhaustion_expectation", False):
        from market_sim.results.scarcity import (
            lolp,
            resolve_lolp_params,
            within_day_forward_max,
        )

        # The model's own total supply envelope: all-thermal capability
        # (post-reconciliation), storage discharge power, and the renewable
        # LP upper bounds (uncurtailed cf x cap — the WTX corridor ceilings
        # bind West export at high-wind hours, ~zero at evening exhaustion
        # hours; precommit §1.2 convention).
        # storage_power_cap is (n_storage,) static or (n_storage, T) hourly
        # (the armed ercot_storage_capability_measured series) — sum over
        # UNITS only, never over hours.
        _spc = np.asarray(storage_power_cap, dtype=float)
        _storage_term = _spc.sum(axis=0) if _spc.ndim == 2 else float(_spc.sum())
        _cap_total = (
            (fleet_arrays.pmax[:, None] * fleet_arrays.availability).sum(axis=0)
            + _storage_term
            + (wind_cap[:, None] * wind_cf).sum(axis=0)
            + (solar_cap[:, None] * solar_cf).sum(axis=0)
        )
        # Sequestered AS MW = the armed withholding families' LP requirement
        # rows (ECRS/RRS/RegUp *_withheld, rigid windows, post-credit),
        # exactly as the resolved ReserveDesign carries them.
        _t_h = int(config.hours)
        _as_seq = np.zeros(_t_h)
        if reserve_design is not None:
            for _fam in reserve_design.families:
                if _fam.name.endswith("_withheld"):
                    _as_seq += np.asarray(_fam.requirement, dtype=float)[:_t_h]
        _h_margin = _cap_total - demand.sum(axis=0) - _as_seq
        # LOLP through the registered machinery (full-tier form): the
        # ordc_lolp_* constants enter as an EXPECTATION input — the in-LP
        # ORDC curve, the written adder and every price channel are
        # untouched (ercot-206 B0 held; precommit §1.2).
        _mu, _sigma = resolve_lolp_params(config, _t_h)
        _lolp_t = lolp(
            _h_margin,
            _mu,
            _sigma,
            float(config.ordc_mcl_mw),
            float(config.ordc_lolp_shift_sigma),
        )
        # P_exhaust(t) = max over h in [t..end-of-day] of LOLP(H(h)) — the
        # remainder-of-operating-day window on the fixed-CST clock
        # (within_day_forward_max: reverse cumulative maximum per day block,
        # rule 2 — no hour loop).
        _p_exh = within_day_forward_max(_lolp_t)
        ercot219_exhaustion = {
            "h_margin_mw": _h_margin,
            "as_sequestered_mw": _as_seq,
            "lolp": _lolp_t,
            "p_exhaust": _p_exh,
        }
        logger.info(
            "ERCOT exhaustion expectation (%d): H p5/p50 %.0f/%.0f MW, "
            "LOLP>=0.5 in %d h, P_exhaust*VOLL >= $1000 in %d h",
            year,
            float(np.percentile(_h_margin, 5)),
            float(np.percentile(_h_margin, 50)),
            int((_lolp_t >= 0.5).sum()),
            int((_p_exh * float(config.ordc_voll) >= 1000.0).sum()),
        )
        if getattr(config, "ercot_storage_reservation_offer", False):
            # Stage 3: P1-only raise-only reservation floor —
            # max(vom_base, P_exhaust x ordc_voll) per (unit, hour). The
            # keeper's own offer is the floor, so the mechanism
            # self-extinguishes as P_exhaust -> 0 (precommit §1.3).
            p1_storage_discharge_cost = np.maximum(
                np.asarray(storage.vom, dtype=float)[:, None],
                _p_exh[None, :] * float(config.ordc_voll),
            )
            logger.info(
                "ERCOT storage reservation-price offer (%d): P1 discharge "
                "offer > base in %d of %d hours, max $%.0f/MWh",
                year,
                int((_p_exh * float(config.ordc_voll) > storage.vom.max()).sum()),
                _t_h,
                float(p1_storage_discharge_cost.max()),
            )
    elif iso == "ERCOT" and getattr(config, "ercot_storage_reservation_offer", False):
        # Rule 5: on an ERCOT solve, stage 3 without stage 2 is a loud error
        # (nothing to price), never a silent fallback. On a NON-ERCOT solve
        # the three fields are inert by the iso gate (rule 25; seam proof
        # SP-2 forces them TRUE cross-ISO and asserts byte-identity).
        raise ValueError(
            "ercot_storage_reservation_offer requires ercot_exhaustion_"
            "expectation (stage 3 prices stage 2's P_exhaust; armed alone "
            "there is nothing to price)."
        )
    # Drain any stale per-pass timings before this year's solves so the
    # markup attribution below covers exactly this year (PERF-B session 2).
    reset_pass_timing_log()
    # Same-year P1 basis seed, adaptive leg (wallclock item B, memo §6.4): an
    # ercot-221 pass 2 reaches run_energy_solve with ``reuse_p0_from`` and no
    # live P0 model, and its P1 is the identical floored LP under a different
    # storage discharge cost — so pass 1 exports its P1 basis for it, ONLY when
    # that pass may follow (the same gate the adaptive block below opens on).
    # Ignored by an unseeded pass; False on every other ISO / gate-off run.
    _p1_basis_for_adaptive = bool(
        iso == "ERCOT"
        and getattr(config, "ercot_storage_adaptive_expectation", False)
        and storage.n_storage
    )
    _t_solve_start = time.perf_counter()
    energy_solve = run_energy_solve(
        fleet,
        fleet_arrays,
        demand,
        mc_base,
        dispatch_kwargs,
        config,
        xyear_cache=xyear_cache,
        p1_fleet_prep=(
            ra_p1_prep
            or ercot_bridge_prep
            or nyiso_bridge_prep
            or spp_bridge_prep
            or soco_campaign_prep
            or miso_night_floor_prep
            or pjm_fleet_prep
        ),
        p1_kwargs_prep=pjm_kwargs_prep or caiso_reserve_kwargs_prep,
        mc_bid_adjust=offer_surface_mc_bid_adjust,
        # The v2 lowcurve and the ERCOT-64 floor-scoped bid hooks are mutually
        # exclusive (rule 19, enforced at build_ercot_gas_bridge_p1_preps), so
        # at most one is non-None here.
        p1_bid_adjust_prep=lowcurve_bid_adjust_prep or ercot_bridge_bid_prep,
        p1_bid_max_target=p1_bid_max_target,
        startup_run_ratio_t=startup_run_ratio_t,
        # ercot-219 stage-3 P1-only storage reservation-price re-cost
        # (None on every flag-off / non-ERCOT path — byte-identical).
        p1_storage_discharge_cost=p1_storage_discharge_cost,
        export_p1_basis=_p1_basis_for_adaptive,
    )
    _t_solve_end = time.perf_counter()
    # ercot-221 ADAPTIVE-EXPECTATION storage offer (owner card by dispatch;
    # PRECOMMIT-ercot221 §1 + Amendments 1-3): TWO-PASS P1. The pass-1 solve
    # above ran with the incumbent offers; the model's OWN daily
    # demand-weighted P1 energy dual — PURE lambda, Amendment 3: zero
    # measured content enters this path (rule 13) — yields the daily spike
    # events whose trailing EWMA frequency (the two rule-23 frozen constants)
    # is the storage fleet's experience-based spike expectation. Pass 2, THE
    # scored pass, floors ERCOT storage discharge at max(vom, P_hat x VOLL)
    # in the evening window ONLY, through the same p1_storage_discharge_cost
    # seam (off-window hours carry storage.vom exactly — the seam's default —
    # so ordinary-hour cycling is untouched by construction). P0 identical in
    # both passes; exactly ONE adaptation pass (rule 10 spirit, precommit).
    # Every non-ERCOT / gate-off run never enters this block (byte-identical).
    ercot221_adaptive = None
    # ercot-230 fixed-point iteration trajectory (None on every flag-off /
    # non-ERCOT run) — persisted as hourly/adaptive_iteration_<year>.json.
    ercot230_iteration = None
    if (
        iso == "ERCOT"
        and getattr(config, "ercot_storage_adaptive_expectation", False)
        and storage.n_storage
    ):
        if getattr(config, "ercot_storage_reservation_offer", False):
            raise ValueError(
                "ercot_storage_adaptive_expectation and "
                "ercot_storage_reservation_offer both drive the P1 storage "
                "discharge re-cost seam — arm at most one (rule 19)."
            )
        from market_sim.results.scarcity import (
            ERCOT_ADAPTIVE_EVENT_USD,
            ERCOT_ADAPTIVE_WINDOW_HOURS,
            ercot_adaptive_expectation_daily,
        )

        _t_h = int(config.hours)
        _dem_t = demand.sum(axis=0)[:_t_h]
        _voll = float(config.ordc_voll)
        _n_days = _t_h // 24
        _vom_s = np.asarray(storage.vom, dtype=float)[:, None]
        _hod = np.arange(_t_h) % 24
        _day_of = np.minimum(np.arange(_t_h) // 24, _n_days - 1)
        _in_win = np.isin(_hod, ERCOT_ADAPTIVE_WINDOW_HOURS)

        def _ercot_adaptive_floor(_p1_res):
            """The ercot-221 floor construction from one solved P1 result.

            Factored (ercot-230) so the incumbent adaptation pass and the
            gated fixed-point iteration below run the IDENTICAL arithmetic —
            one construction, rule 19; the flag-off path calls it exactly
            once on pass 1, reproducing the pre-refactor floats expression
            for expression (G-REPRO validated on the keeper replay).
            Returns ``(s_events, p_hat, floor_t, settle_t)``.
            """
            _lam_t = (
                np.asarray(_p1_res.prices, dtype=float)[:, :_t_h] * demand[:, :_t_h]
            ).sum(axis=0) / np.where(_dem_t > 0.0, _dem_t, 1.0)
            # Event basis (precommit Amendment 4): the model's own settled-price
            # analogue = lambda + its OWN decontaminated anchored scarcity-adder
            # mirror — the identical arithmetic the persist path writes (cap-dual
            # ALL tier, min'd with the ORDC total family's balance dual where
            # present, x (VOLL - lambda)/VOLL, protocol-capped). Both terms are
            # duals of the model's own LP pass: zero measured content (rule 13;
            # the measured RTORDPA overlay is deliberately EXCLUDED). A config
            # with no reserve duals degrades to lambda-only, disclosed inert.
            _adder_t = np.zeros(_t_h)
            _cd = getattr(_p1_res, "reserve_supply_cap_dual", None)
            _rpf = getattr(_p1_res, "reserve_price_by_family", None)
            _gam = None
            if _cd is not None:
                _gam = np.asarray(_cd, dtype=float)[:, :_t_h][-1]
            if _rpf is not None:
                _fam = np.asarray(_rpf, dtype=float)[:_t_h, -1]
                _gam = _fam if _gam is None else np.minimum(_gam, _fam)
            if _gam is not None:
                _head = np.maximum(_voll - _lam_t, 0.0)
                _adder_t = np.minimum(np.maximum(_gam, 0.0) * _head / _voll, _head)
            _settle_t = _lam_t + _adder_t
            _day_max = _settle_t[: _n_days * 24].reshape(_n_days, 24).max(axis=1)
            _s_m = (_day_max >= ERCOT_ADAPTIVE_EVENT_USD).astype(float)
            _p_hat = ercot_adaptive_expectation_daily(
                _s_m,
                half_life_days=float(config.ercot_adaptive_half_life_days),
                beta=float(config.ercot_adaptive_beta),
            )
            _floor_t = np.zeros(_t_h)
            _floor_t[_in_win] = _p_hat[_day_of[_in_win]] * float(config.ordc_voll)
            # ercot-223 EVENT-REALIZED RELEASE guard (rule 17 structural yield;
            # PRECOMMIT-ercot223-event-release-guard-2026-08-19.md §1). The
            # conduct floor is an offer — withhold in anticipation OF the spike;
            # at hours the SAME settle basis the day-max event detector reads —
            # pass 1 for the incumbent adaptation, the immediately-preceding
            # pass under ercot_adaptive_fixed_point (PRECOMMIT-ercot230 §1) —
            # marks the spike as REALIZED (>= ERCOT_ADAPTIVE_EVENT_USD,
            # the existing frozen constant — zero new fitted scalars), a cleared
            # offer does not withhold physical energy, so the floor is masked
            # and the cost falls back to storage vom (the seam default). Without
            # this, offer-as-cost debases the storage SOC shadow against the
            # co-opt's floor-free reserve-headroom value and manufactures load
            # shed at real event hours (the 2024 h3066 G-SHED defect,
            # ercot223_shed_phase0.json). Default off: byte-identical floors.
            if getattr(config, "ercot_adaptive_event_release", False):
                _floor_t[_settle_t >= ERCOT_ADAPTIVE_EVENT_USD] = 0.0
            return _s_m, _p_hat, _floor_t, _settle_t

        _s_m, _p_hat, _floor_t, _settle_t = _ercot_adaptive_floor(energy_solve.p1)
        _adaptive_cost = np.maximum(_vom_s, _floor_t[None, :])
        # PERF-B session 3, charter C-1a: pass 2 solves the SAME LP as pass 1
        # — same fleet, demand, kwargs, base cost and hooks (every argument
        # below is the same object pass 1 received) — and differs ONLY in the
        # P1 storage discharge objective, ``_adaptive_cost`` against the cost
        # pass 1's P1 actually solved with (``p1_storage_discharge_cost`` when
        # set, else the kwargs default ``storage_discharge_cost``, which is
        # what ``lp.costs.build_cost_vector`` broadcast). When the two are
        # ELEMENTWISE EQUAL (exact ``np.array_equal``, no tolerance — a unit
        # whose VOM sits below the fleet-max VOM is why the ``floor > vom``
        # counter on the log line is a symptom, never the test) pass 2 would
        # hand HiGHS the identical cost vector on the identical matrix, so
        # pass 1's EnergySolveResult IS what pass 2 would have produced, and
        # the pass is skipped. In the ERCOT 2025 keeper year that pass was
        # 926 s (half the year) for a bit-identical answer
        # (docs/FINDING-perfb-s2-markup-attribution-2026-09.md §4.4); in 2023
        # / 2024 the floor rises above VOM in hundreds of window hours and the
        # guard stays down. The adaptive sidecar (s_model / p_hat / floor_t)
        # is recorded either way — it describes the floor construction, which
        # is unchanged by whether the LP had to be re-solved to apply it.
        _pass2_identical = _p1_storage_cost_identical(
            _adaptive_cost, p1_storage_discharge_cost, dispatch_kwargs
        )
        logger.info(
            "ERCOT adaptive-expectation offer (%d): pass-1 model spike days "
            "%d, P_hat max %.3f, floor > vom in %d of %d window hours; %s",
            year,
            int(_s_m.sum()),
            float(_p_hat.max()),
            int((_floor_t[_in_win] > float(_vom_s.max())).sum()),
            int(_in_win.sum()),
            (
                "pass-2 storage discharge cost is elementwise IDENTICAL to the "
                "cost pass 1 solved with (max(vom, floor) == vom for every "
                "unit-hour) — pass 2 SKIPPED, pass 1 IS the scored pass (C-1a)"
                if _pass2_identical
                else "re-solving P1 (pass 2, THE scored pass)"
            ),
        )
        ercot221_adaptive = {
            "s_model": _s_m,
            "p_hat": _p_hat,
            "floor_t": _floor_t,
        }
        if not _pass2_identical:
            energy_solve = run_energy_solve(
                fleet,
                fleet_arrays,
                demand,
                mc_base,
                dispatch_kwargs,
                config,
                xyear_cache=xyear_cache,
                p1_fleet_prep=(
                    ra_p1_prep
                    or ercot_bridge_prep
                    or nyiso_bridge_prep
                    or miso_night_floor_prep
                    or pjm_fleet_prep
                ),
                p1_kwargs_prep=pjm_kwargs_prep or caiso_reserve_kwargs_prep,
                mc_bid_adjust=offer_surface_mc_bid_adjust,
                p1_bid_adjust_prep=lowcurve_bid_adjust_prep or ercot_bridge_bid_prep,
                p1_bid_max_target=p1_bid_max_target,
                startup_run_ratio_t=startup_run_ratio_t,
                p1_storage_discharge_cost=_adaptive_cost,
                # C-1b (PERF-B session 3): every argument above is the same
                # object pass 1 received and the discharge cost applies to P1
                # only, so pass 1's P0 IS this pass's P0 — reuse it instead of
                # rebuilding and cold-solving the identical LP (honoured only
                # when pass 1's P1 was cold; see run_energy_solve).
                reuse_p0_from=energy_solve,
                # P1 basis seed (item B): seeded from pass 1's P1 basis; export
                # this pass's own P1 basis only when an ercot-230 fixed-point
                # iteration may follow.
                export_p1_basis=bool(
                    getattr(config, "ercot_adaptive_fixed_point", False)
                ),
            )
        # ercot-230 FIXED-POINT ITERATION (PRECOMMIT-ercot230-adaptive-fixed-
        # point-2026-08-23.md §1; the FINDING-ercot221 §4 first named
        # successor, owner-chartered). The incumbent pass-2 floors were
        # derived from the UNFLOORED pass-1 path — the measured bootstrap
        # starvation (7 spike days vs reality's 23). When armed, adaptation
        # passes continue: each re-derives the identical floor arithmetic
        # from the latest P1 and re-solves, until the floor vector reproduces
        # itself exactly (fixed point — the next pass would solve the
        # identical LP, so the last solved pass IS the scored fixed point),
        # a floor recurs non-adjacently (cycle, disclosed), or the
        # pre-registered operational cap is reached (disclosed). Zero new
        # identified constants; the stopping rule is parameter-free discrete
        # self-reproduction. Flag-off: this block never runs — byte-identical.
        if getattr(config, "ercot_adaptive_fixed_point", False):
            import hashlib as _hashlib

            from market_sim.results.scarcity import ERCOT_ADAPTIVE_MAX_PASSES

            def _floor_sha(_fl):
                return _hashlib.sha256(np.ascontiguousarray(_fl).tobytes()).hexdigest()[
                    :16
                ]

            _fp_floors = [_floor_t]
            ercot230_iteration = {
                "stop_reason": None,
                "n_adapt_passes": 0,
                # Aligned by generation step: entry i pairs the events of
                # solved pass i+1's own path with the floor derived FROM them
                # (the floor pass i+2 would run under). Entry 0 = pass-1
                # events -> the incumbent pass-2 floor.
                "spike_days_by_pass": [int(_s_m.sum())],
                "floored_window_hours_by_pass": [int((_floor_t[_in_win] > 0.0).sum())],
                "released_window_hours_by_pass": [
                    int((_in_win & (_settle_t >= ERCOT_ADAPTIVE_EVENT_USD)).sum())
                ],
                "floor_sha_by_pass": [_floor_sha(_floor_t)],
            }
            for _fp_extra in range(ERCOT_ADAPTIVE_MAX_PASSES + 1):
                _s_k, _ph_k, _fl_k, _st_k = _ercot_adaptive_floor(energy_solve.p1)
                ercot230_iteration["spike_days_by_pass"].append(int(_s_k.sum()))
                ercot230_iteration["floored_window_hours_by_pass"].append(
                    int((_fl_k[_in_win] > 0.0).sum())
                )
                ercot230_iteration["released_window_hours_by_pass"].append(
                    int((_in_win & (_st_k >= ERCOT_ADAPTIVE_EVENT_USD)).sum())
                )
                ercot230_iteration["floor_sha_by_pass"].append(_floor_sha(_fl_k))
                if np.array_equal(_fl_k, _fp_floors[-1]):
                    ercot230_iteration["stop_reason"] = "converged"
                    break
                if any(np.array_equal(_fl_k, _f) for _f in _fp_floors[:-1]):
                    ercot230_iteration["stop_reason"] = "cycle"
                    break
                if _fp_extra == ERCOT_ADAPTIVE_MAX_PASSES:
                    ercot230_iteration["stop_reason"] = "cap"
                    break
                logger.info(
                    "ERCOT adaptive fixed-point (%d): pass-%d path spike days "
                    "%d, P_hat max %.3f, floor > vom in %d window hours "
                    "(%d released); re-solving P1 (pass %d)",
                    year,
                    2 + _fp_extra,
                    int(_s_k.sum()),
                    float(_ph_k.max()),
                    int((_fl_k[_in_win] > float(_vom_s.max())).sum()),
                    int((_in_win & (_st_k >= ERCOT_ADAPTIVE_EVENT_USD)).sum()),
                    3 + _fp_extra,
                )
                # The audit sidecar keeps the incumbent semantics one level
                # up: the floor-GENERATING state + the floors the scored
                # pass ran under (PRECOMMIT-ercot230 §1).
                ercot221_adaptive = {
                    "s_model": _s_k,
                    "p_hat": _ph_k,
                    "floor_t": _fl_k,
                }
                energy_solve = run_energy_solve(
                    fleet,
                    fleet_arrays,
                    demand,
                    mc_base,
                    dispatch_kwargs,
                    config,
                    xyear_cache=xyear_cache,
                    p1_fleet_prep=(
                        ra_p1_prep
                        or ercot_bridge_prep
                        or nyiso_bridge_prep
                        or miso_night_floor_prep
                        or pjm_fleet_prep
                    ),
                    p1_kwargs_prep=pjm_kwargs_prep or caiso_reserve_kwargs_prep,
                    mc_bid_adjust=offer_surface_mc_bid_adjust,
                    p1_bid_adjust_prep=lowcurve_bid_adjust_prep
                    or ercot_bridge_bid_prep,
                    p1_bid_max_target=p1_bid_max_target,
                    startup_run_ratio_t=startup_run_ratio_t,
                    p1_storage_discharge_cost=np.maximum(_vom_s, _fl_k[None, :]),
                    # C-1b: same premise as pass 2 — the previous iteration's
                    # P0 is this iteration's P0.
                    reuse_p0_from=energy_solve,
                    # P1 basis seed (item B): seeded from the previous
                    # iteration's P1 basis; export for the next one (the
                    # final iteration's export is one wasted getBasis, accepted
                    # — the stop is only known after the solve).
                    export_p1_basis=True,
                )
                _fp_floors.append(_fl_k)
                ercot230_iteration["n_adapt_passes"] += 1
            logger.info(
                "ERCOT adaptive fixed-point (%d): stop=%s after %d additional "
                "pass(es); final-path spike days %d",
                year,
                ercot230_iteration["stop_reason"],
                ercot230_iteration["n_adapt_passes"],
                ercot230_iteration["spike_days_by_pass"][-1],
            )
        _t_solve_end = time.perf_counter()
    # caiso-205 ADAPTIVE-EXPECTATION storage offer — the CAISO leg of the
    # ercot-221 family (owner order caiso-205 branch 1 over the caiso-204
    # recorded Phase-0 G-BOOT FAIL; constants FROZEN at the caiso-204
    # identification, caiso204_adaptive_phase0.json). TWO-PASS P1 through
    # the same p1_storage_discharge_cost seam, one adaptation pass (rule 10
    # spirit). Event basis: the model's OWN daily max CA demand-weighted P1
    # energy dual — PURE lambda, which IS CAISO's scored backcast price
    # (caiso-137b: the calibration lane's price writer carries no CAISO
    # overlay term, so unlike ERCOT's Amendment-4 case there is no
    # model-side scarcity-adder mirror to add; zero measured content in the
    # armed path, rule 13). WECC_import carries load_share 0.0, so the
    # all-zone demand weighting below IS the CA-zone weighting of the
    # caiso-204 G-BOOT instrument. The floor applies to BATTERY rows only —
    # the caiso-204 S4 classifier excluded pumped storage from the
    # identified conduct population, so PS keeps its own calibrated
    # throughput adder untouched (rule 25 spirit within the ISO). Every
    # non-CAISO / gate-off run never enters this block (byte-identical).
    caiso205_adaptive = None
    if (
        iso == "CAISO"
        and getattr(config, "caiso_storage_adaptive_expectation", False)
        and storage.n_storage
    ):
        from market_sim.results.scarcity import (
            CAISO_ADAPTIVE_EVENT_USD,
            CAISO_ADAPTIVE_PARK_CAP_USD,
            CAISO_ADAPTIVE_WINDOW_HOURS,
            ercot_adaptive_expectation_daily,
        )

        _t_h = int(config.hours)
        _dem_t = demand.sum(axis=0)[:_t_h]
        _lam_t = (
            np.asarray(energy_solve.p1.prices, dtype=float)[:, :_t_h] * demand[:, :_t_h]
        ).sum(axis=0) / np.where(_dem_t > 0.0, _dem_t, 1.0)
        _n_days = _t_h // 24
        _day_max = _lam_t[: _n_days * 24].reshape(_n_days, 24).max(axis=1)
        _s_m = (_day_max >= CAISO_ADAPTIVE_EVENT_USD).astype(float)
        _p_hat = ercot_adaptive_expectation_daily(
            _s_m,
            half_life_days=float(config.caiso_adaptive_half_life_days),
            beta=float(config.caiso_adaptive_beta),
        )
        _vom_s = np.asarray(storage.vom, dtype=float)[:, None]
        _floor_t = np.zeros(_t_h)
        _hod = np.arange(_t_h) % 24
        _day_of = np.minimum(np.arange(_t_h) // 24, _n_days - 1)
        _in_win = np.isin(_hod, CAISO_ADAPTIVE_WINDOW_HOURS)
        _floor_t[_in_win] = _p_hat[_day_of[_in_win]] * CAISO_ADAPTIVE_PARK_CAP_USD
        # Battery-only mask: t=hour rows below are (n_storage, T); PS rows
        # keep the incumbent static vom exactly (broadcast byte-identical).
        _batt = np.asarray(storage.tech_names) != "pumped_storage"
        _adaptive_cost = np.broadcast_to(_vom_s, (storage.n_storage, _t_h)).copy()
        _adaptive_cost[_batt] = np.maximum(_vom_s[_batt], _floor_t[None, :])
        _batt_vom_max = float(_vom_s[_batt].max()) if _batt.any() else 0.0
        logger.info(
            "CAISO adaptive-expectation offer (%d): pass-1 model spike days "
            "%d, P_hat max %.3f, floor > battery vom in %d of %d window "
            "hours; re-solving P1 (pass 2, THE scored pass)",
            year,
            int(_s_m.sum()),
            float(_p_hat.max()),
            int((_floor_t[_in_win] > _batt_vom_max).sum()),
            int(_in_win.sum()),
        )
        caiso205_adaptive = {
            "s_model": _s_m,
            "p_hat": _p_hat,
            "floor_t": _floor_t,
        }
        energy_solve = run_energy_solve(
            fleet,
            fleet_arrays,
            demand,
            mc_base,
            dispatch_kwargs,
            config,
            xyear_cache=xyear_cache,
            p1_fleet_prep=(
                ra_p1_prep
                or ercot_bridge_prep
                or nyiso_bridge_prep
                or miso_night_floor_prep
                or pjm_fleet_prep
            ),
            p1_kwargs_prep=pjm_kwargs_prep or caiso_reserve_kwargs_prep,
            mc_bid_adjust=offer_surface_mc_bid_adjust,
            p1_bid_adjust_prep=lowcurve_bid_adjust_prep or ercot_bridge_bid_prep,
            p1_bid_max_target=p1_bid_max_target,
            startup_run_ratio_t=startup_run_ratio_t,
            p1_storage_discharge_cost=_adaptive_cost,
        )
        _t_solve_end = time.perf_counter()
    # OPT-IN P0 commitment record, taken HERE and not below: ``fleet_arrays``
    # is about to be rebound to ``energy_solve.p1_fleet_arrays``, and the
    # markup was computed against the PRE-prep arrays. A P1 fleet hook only
    # rewrites ``min_gen`` (never ``pmax``), so the two agree today on every
    # armed path — but packing against the arrays the markup itself saw makes
    # that an invariant of this code rather than of the hooks'.
    _p0_commitment_bits = (
        p0_commitment_pattern(energy_solve.r0.dispatch, fleet_arrays.pmax)
        if persist_p0_commitment
        else None
    )
    # OPT-IN P0 dispatch/dual record (caiso-287), taken at the SAME seam and
    # for the same reason: these are the two arrays
    # ``pipeline.commitment.build_caiso_ra_p1_prep`` hands the bridge detector
    # (``r0.dispatch``, ``r0.prices``), so capturing them here — before
    # ``fleet_arrays`` is rebound — records exactly what the screens saw,
    # rather than a P1 stand-in for it. Copied, not aliased: ``r0`` stays live
    # below and a view would let a later in-place write reach the sidecar.
    # float64, NOT a narrowed float32: the point of this pair is that the
    # screens replay EXACTLY, so the reproduction gate against the committed
    # floors array is an equality rather than a tolerance. Halving the file
    # would buy ~60 MB at the cost of the only property it has.
    _p0_dispatch_mw = (
        np.array(energy_solve.r0.dispatch, dtype=np.float64)
        if persist_p0_dispatch
        else None
    )
    _p0_zonal_prices = (
        np.array(energy_solve.r0.prices, dtype=np.float64)
        if persist_p0_dispatch
        else None
    )
    result = energy_solve.p1
    mc_bid = energy_solve.mc_bid
    # The fleet P1 actually solved on — the RA-floored fleet when the bridge
    # fired, else the input fleet unchanged. Persist ITS min_gen as the P1 pass's
    # floors and expose it downstream (D-2 forced-energy attribution).
    fleet_arrays = energy_solve.p1_fleet_arrays

    context = FleetContext.from_arrays(
        fleet_arrays,
        iso_config,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        storage.energy_cap,
    )

    # ORDC-only scarcity pricing (ercot57 joint round v2): RTORPA computed
    # post-solve on the P1 result's REALIZED envelope room — the published
    # SCED-plus-adder settlement construction (scarcity.
    # ercot_ordc_realized_adder has the full design note). Stashed on
    # p2_state so solve_and_persist's frame writer adds it into the settled
    # price exactly like the cap-dual adder it replaces (rule 19: the two
    # never coexist — __post_init__ forbids the in-LP total family here).
    ercot_ordc_realized = None
    if (
        iso == "ERCOT"
        and getattr(config, "ercot_ordc_only_scarcity", False)
        and reserve_design is not None
    ):
        from market_sim.results.scarcity import ercot_ordc_realized_adder

        ercot_ordc_realized = ercot_ordc_realized_adder(
            config,
            year,
            design=reserve_design,
            dispatch=result.dispatch,
            prices=result.prices,
            demand=demand,
        )
        if ercot_ordc_realized is not None:
            logger.info(
                "ERCOT ORDC realized-room adder (%d): mean $%.2f/MWh, "
                ">$10 in %d h, max $%.0f",
                year,
                float(ercot_ordc_realized.mean()),
                int((ercot_ordc_realized > 10).sum()),
                float(ercot_ordc_realized.max()),
            )
    # Drain this year's per-pass timing log ONCE: every pass's builds and both
    # HiGHS runs, summed (PERF-B session 3, charter C-2) — read into ``_timing``
    # below.
    _pass_timing = _aggregate_pass_timing(energy_solve)
    # Everything the P2 commitment pass needs, kept so P2 can be re-run as a
    # post-process (see _commitment_pass / run_p2) without re-solving P0/P1.
    p2_state = {
        "year": year,
        "iso": iso,
        "fleet": fleet,
        "fleet_arrays": fleet_arrays,
        "mc_base": mc_base,
        "mc_bid": mc_bid,
        "p1_result": result,
        "demand": demand,
        "dispatch_kwargs": dispatch_kwargs,
        "config": config,
        "context": context,
        "storage_units": storage_units,
        "dual_fuel_oil_mask": dual_fuel_oil_mask,
        # Zone-name list for the shared P2 core's NYISO path B (Stage 4);
        # older pickled p2_states predate the key (the core requires it only
        # when that branch fires).
        "zone_names": zone_names,
        # Link list in flow-column order (the possibly import-node-extended /
        # per-hub-split topology actually solved), so the bundle can persist
        # per-link flows for interface-binding diagnostics (the MISO zonal
        # gates report binding-hour counts per CIL/CEL group and the RDT).
        "links": iso_config.links,
        # ORDC-only realized-room RTORPA for the P1 result (None unless
        # ercot_ordc_only_scarcity computed one above): the frame writer adds
        # it to the settled price (P1 rows only).
        "ercot_ordc_realized_adder": ercot_ordc_realized,
        # The resolved ``ReserveDesign`` (None when the co-opt is off), so the
        # bundle can name each reserve family and persist its requirement
        # alongside its solved balance-row dual — the
        # ``hourly/reserve_family_<year>.parquet`` sidecar. The LP reports duals
        # positionally, (T, n_fam); only the design knows which column is
        # ``li_30min_total`` and what its hourly requirement was.
        "reserve_design": reserve_design,
        # ercot-219 stage-2 exhaustion series (None unless
        # ercot_exhaustion_expectation armed): H margin, sequestered AS MW,
        # LOLP(H) and the within-day P_exhaust — persisted by the bundle as
        # ``hourly/exhaustion_<year>.parquet`` so G-EXH and the stage-3 offer
        # are auditable from committed artifacts without a re-solve.
        "ercot219_exhaustion": ercot219_exhaustion,
        # ercot-221 adaptive-expectation audit series (None on every flag-off
        # run): the pass-1 model spike days, daily P_hat and the hourly floor
        # actually applied — the committed audit trail for the A/B gates.
        "ercot221_adaptive": ercot221_adaptive,
        # ercot-230 fixed-point iteration trajectory (None on every flag-off
        # run): per-pass spike days / floored-released window-hour counts /
        # floor hashes and the stop reason — persisted as
        # ``hourly/adaptive_iteration_<year>.json`` (PRECOMMIT-ercot230 §1).
        "ercot230_iteration": ercot230_iteration,
        # caiso-205 adaptive-expectation audit series (None on every flag-off
        # run): the CAISO leg's pass-1 spike days, daily P_hat and applied
        # evening-window floor — same columns, same "adaptive" sidecar.
        "caiso205_adaptive": caiso205_adaptive,
        # OPT-IN P0 commitment record (--persist-p0-commitment, default off).
        # Read AFTER both LPs have run and consumed by nothing downstream, so
        # it cannot perturb a solve; absent entirely at default, which is what
        # keeps every existing bundle byte-identical. The pair is exactly what
        # ``compute_monthly_markup`` needs to be replayed bit-identically: the
        # P0 on/off pattern (its only P0 input) and the ``(T,)`` conditional
        # band series (its only other non-fleet input).
        **(
            {
                "p0_commitment_bits": _p0_commitment_bits,
                "startup_run_ratio_t": startup_run_ratio_t,
            }
            if persist_p0_commitment
            else {}
        ),
        # OPT-IN P0 dispatch/dual record (--persist-p0-dispatch, default off),
        # the MW-valued sibling of the pair above. Same property, same reason
        # it cannot perturb a solve: read after both LPs have run, consumed by
        # nothing downstream, and absent entirely at default — which is what
        # keeps every existing bundle byte-identical. The pair is exactly what
        # the RA-bridge screens are called with, so persisting it lets a later
        # session replay ``caiso_ra_mustoffer_min_gen`` offline at zero LP.
        **(
            {
                "p0_dispatch_mw": _p0_dispatch_mw,
                "p0_zonal_prices": _p0_zonal_prices,
            }
            if persist_p0_dispatch
            else {}
        ),
        # ``build_s`` / ``solve_p0_s`` / ``solve_p1_s`` are SUMMED over every
        # energy-solve pass of this year and over every matrix build of each
        # pass (PERF-B session 3, charter C-2) — not the final pass's
        # ``p1.build_time`` / ``r0.solve_time`` / ``p1.solve_time``, which left
        # every earlier pass and the P0 model's build inside ``markup``.
        # ``markup_parts`` is the attribution of the ``markup`` RESIDUAL the
        # caller derives from the four fields (PERF-B session 2);
        # ``solve_and_persist`` appends the ``other`` remainder covering the
        # bracket edges and the between-pass adaptive machinery, so the clause
        # it logs is exhaustive. See _aggregate_pass_timing.
        "_timing": {
            "energy_solve_s": _t_solve_end - _t_solve_start,
            **{
                k: _pass_timing[k]
                for k in (
                    "build_s",
                    "solve_p0_s",
                    "solve_p1_s",
                    "markup_parts",
                    "n_passes",
                )
            },
        },
    }

    # P2 (ARCHIVED — last resort, CLAUDE.md "Dispatch & Commitment"): the
    # optional third LP solve. P0/P1 are the only production passes and every run
    # is scored on P1; P2 runs only when a legacy diagnostic gate is explicitly
    # set. The CAISO RA must-offer bridge NO LONGER triggers P2 — it is applied
    # P1-native above (build_caiso_ra_p1_prep). ERCOT AS-aware commitment stays a
    # P2 trigger, reachable only behind the CLI's --enable-legacy-p2 unlock; it
    # values a unit's own P1 reserve dual in the screen and needs the
    # multi-product co-opt to supply the per-product reserve duals.
    as_aware = (
        getattr(config, "ercot_as_aware_commitment", False)
        and iso == "ERCOT"
        and getattr(config, "energy_reserve_coopt", False)
    )
    result_p1 = None
    if config.commitment_enabled or as_aware:
        result_p1 = result
        result = _commitment_pass(p2_state)

    return result, context, result_p1, p2_state


# Stage 4 (orchestrator unification): the P2 commitment body moved to the
# shared core (``market_sim.pipeline.commitment.run_commitment_pass``) — one
# commitment pass for both orchestrators. The old name is kept as the seam
# ``run_calibration_full`` imports (bundle writer + the ``run_p2`` pickled-state
# re-run path); it accepts the same ``(state, config=None)`` signature and
# stashes ``state["fleet_arrays_p2"]`` exactly as before.
_commitment_pass = run_commitment_pass


def _generation_twh(result, context: FleetContext) -> dict[str, float]:
    """Return modeled annual generation by fuel (TWh)."""
    gen_per_unit = result.dispatch.sum(axis=1)
    twh: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        twh[fuel] = twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
    twh["wind"] = (
        twh.get("wind", 0.0) + float(result.wind_dispatched.sum()) / _MWH_PER_TWH
    )
    twh["solar"] = (
        twh.get("solar", 0.0) + float(result.solar_dispatched.sum()) / _MWH_PER_TWH
    )
    return twh


def _print_table(title: str, rows: list[tuple]) -> None:
    """Print a titled, column-aligned text table."""
    print(f"\n  {title}")
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _report_year(
    year: int, iso: str, result, context: FleetContext, reference: dict, label: str = ""
) -> None:
    """Print the calibration diagnostics for one solved ISO-year."""
    tag = f"  [{label}]" if label else ""
    print(f"\n{'=' * 64}")
    print(f"  Calibration: {iso} {year}   (status: {result.status}){tag}")
    print(f"{'=' * 64}")

    model_twh = _generation_twh(result, context)
    # The benchmark is EIA-923 by-fuel net generation for the run year --
    # unlike the eGRID plant snapshot, its totals sum to the balancing
    # authority's actual net generation. Compared only for a full 8760-hour
    # run; a sub-annual horizon (--hours) is a smoke test, not a backcast.
    full_year = result.dispatch.shape[1] >= HOURS_PER_YEAR
    year_ref = reference.get("isos", {}).get(iso, {}).get(str(year), {})
    bench_twh = year_ref.get("generation_twh", {}) if full_year else {}
    if not full_year:
        print(
            f"\n  NOTE: {result.dispatch.shape[1]}-hour run -- EIA-923 "
            "benchmark comparison suppressed (full 8760h required)."
        )
    # The EIA-923 monthly file for the current year is preliminary until
    # the annual revision (typically Sep of the following year): it
    # under-reports renewable generation by ~30 TWh because small / new
    # wind and solar plants are slow to submit Form 923. Flag that here
    # so the "+13.6% total" gap is read as a benchmark gap, not a model
    # error. The EIA-930 hourly extract is the more complete reference
    # for the current year (see the calibration_reference.json
    # ``eia930_total_twh`` block).
    if full_year and iso == "ERCOT" and year >= 2025:
        print(
            "\n  NOTE: ERCOT 2025 EIA-923 monthly file is preliminary "
            "(released Feb 2026). It under-reports renewable generation "
            "by ~30 TWh vs EIA-930 hourly metered output; expect "
            "+10-15% model-vs-EIA-923 gaps until the annual revision."
        )

    fuels = sorted(set(model_twh) | set(bench_twh))
    gen_rows: list[tuple] = [("fuel", "model TWh", "EIA-923 TWh", "diff %")]
    for fuel in fuels:
        m = model_twh.get(fuel, 0.0)
        b = bench_twh.get(fuel)
        if b is None:
            gen_rows.append((fuel, f"{m:.2f}", "—", "—"))
        else:
            diff = 100.0 * (m - b) / b if b else float("inf")
            gen_rows.append((fuel, f"{m:.2f}", f"{b:.2f}", f"{diff:+.1f}"))
    total_m = sum(model_twh.values())
    total_b = sum(bench_twh.values()) if bench_twh else None
    gen_rows.append(
        (
            "TOTAL",
            f"{total_m:.2f}",
            f"{total_b:.2f}" if total_b else "—",
            f"{100.0 * (total_m - total_b) / total_b:+.1f}" if total_b else "—",
        )
    )
    _print_table("Generation by fuel", gen_rows)

    emissions_t = float(
        compute_emissions(result.dispatch, np.asarray(context.emission_rate)).sum()
    )
    model_co2 = emissions_t / _TONNES_PER_MT
    # The EIA-923 Page 1 benchmark carries no CO2; report modeled CO2 alone.
    print(f"\n  CO2 emissions\n    model {model_co2:.2f} Mt")

    price_rows: list[tuple] = [("zone", "avg $/MWh", "neg-price hrs")]
    iso_config = get_iso_config(iso)
    for z, zone in enumerate(iso_config.zone_names):
        zone_price = result.prices[z]
        price_rows.append(
            (
                zone,
                f"{zone_price.mean():.2f}",
                str(int((zone_price < 0.0).sum())),
            )
        )
    system_price = result.prices.mean(axis=0)
    price_rows.append(
        (
            "SYSTEM",
            f"{system_price.mean():.2f}",
            str(int((system_price < 0.0).sum())),
        )
    )
    _print_table("Zonal prices", price_rows)

    _report_curtailment(year, iso, result, context, full_year)

    _report_hourly_correlation(year, iso, result, context, full_year)


def _report_curtailment(
    year: int, iso: str, result, context: FleetContext, full_year: bool
) -> None:
    """Print the headline modeled-vs-reported renewable curtailment metric.

    Modeled curtailment is the dispatch's unused wind/solar potential. For
    ISO-years with a built HSL-style parquet (scripts/data/build_ercot_hsl.py /
    build_caiso_hsl.py) the reported curtailment — the telemetered
    ``hsl - gen`` — is printed beside it, with the monthly shape (the CAISO
    P6 / ERCOT E3 headline metric): a transmission-constrained dispatch fed
    uncurtailed potential should reproduce both the level and the
    seasonality of real curtailment. The reported comparison is suppressed
    on a sub-annual smoke run, and the table falls back to model-only
    columns when no HSL data covers the year.
    """
    hsl = load_hsl_hourly(iso, year)
    compare = hsl is not None and full_year

    caps = {"wind": context.wind_cap_mw, "solar": context.solar_cap_mw}
    potential = {
        "wind": context.wind_potential_mwh,
        "solar": context.solar_potential_mwh,
    }
    dispatched = {
        "wind": np.asarray(result.wind_dispatched, dtype=float).sum(axis=0),
        "solar": np.asarray(result.solar_dispatched, dtype=float).sum(axis=0),
    }

    rows: list[tuple] = [
        (
            "resource",
            "installed GW",
            "potential TWh",
            "model TWh",
            "model %",
            "reported TWh",
            "reported %",
        )
    ]
    for fuel in ("wind", "solar"):
        pot_mwh = potential[fuel]
        curt_mwh = max(pot_mwh - float(dispatched[fuel].sum()), 0.0)
        reported_twh = reported_pct = "—"
        if compare:
            rep_curt = float(
                (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"]).clip(lower=0.0).sum()
            )
            rep_pot = float(hsl[f"{fuel}_hsl_mw"].sum())
            reported_twh = f"{rep_curt / _MWH_PER_TWH:.2f}"
            reported_pct = f"{100.0 * rep_curt / rep_pot:.1f}" if rep_pot > 0 else "—"
        rows.append(
            (
                fuel,
                f"{caps[fuel] / 1e3:.2f}",
                f"{pot_mwh / _MWH_PER_TWH:.2f}",
                f"{curt_mwh / _MWH_PER_TWH:.2f}",
                f"{100.0 * curt_mwh / pot_mwh:.1f}" if pot_mwh > 0 else "—",
                reported_twh,
                reported_pct,
            )
        )
    _print_table("Renewable curtailment — modeled vs reported", rows)
    if hsl is None:
        print(
            f"    (no reported HSL data for {iso} {year}; build with "
            "scripts/data/build_ercot_hsl.py / build_caiso_hsl.py — ERCOT 2024+ "
            "needs the NP6 report uploads)"
        )
        return
    if not compare:
        print("    (reported comparison suppressed -- full 8760h run required)")
        return

    # Monthly shape: model re-curtailment vs reported, GWh per month. The
    # model's hourly potential is the same rescaled HSL series the dispatch
    # consumed (renewables.hsl_potential_mw), so the comparison isolates
    # *when* the model curtails, not profile-construction differences.
    month_idx = _hour_to_month_index(HOURS_PER_YEAR)
    monthly: dict[str, np.ndarray] = {}
    for fuel in ("wind", "solar"):
        pot_mw = hsl_potential_mw(iso, year, fuel)
        model_curt = np.clip(pot_mw - dispatched[fuel][:HOURS_PER_YEAR], 0.0, None)
        rep_curt = (
            (hsl[f"{fuel}_hsl_mw"] - hsl[f"{fuel}_gen_mw"])
            .clip(lower=0.0)
            .to_numpy(dtype=float)
        )
        monthly[f"{fuel}_model"] = (
            np.bincount(month_idx, weights=model_curt, minlength=12) / 1e3
        )
        monthly[f"{fuel}_reported"] = (
            np.bincount(month_idx, weights=rep_curt, minlength=12) / 1e3
        )
    monthly_rows: list[tuple] = [
        ("month", "wind model", "wind rptd", "solar model", "solar rptd"),
    ]
    for m in range(12):
        monthly_rows.append(
            (
                str(m + 1),
                f"{monthly['wind_model'][m]:.0f}",
                f"{monthly['wind_reported'][m]:.0f}",
                f"{monthly['solar_model'][m]:.0f}",
                f"{monthly['solar_reported'][m]:.0f}",
            )
        )
    _print_table("Monthly curtailment (GWh)", monthly_rows)


def _report_hourly_correlation(
    year: int, iso: str, result, context: FleetContext, full_year: bool
) -> None:
    """Print the modeled-vs-EIA-930 hourly dispatch correlation for coal/gas.

    Compares the shape of the hourly dispatch — not just annual totals — so
    a model that hits the right yearly TWh by running flat when the real
    fleet cycled is still visible. ERCOT only, and only for a full 8760-hour
    run (the EIA-930 fossil series is a whole-year extract).
    """
    if iso != "ERCOT" or not full_year:
        return
    eia_hourly = load_ercot_fossil_gen(year)
    if eia_hourly is None:
        print(
            "\n  Hourly dispatch correlation\n    (no EIA-930 fossil "
            f"series for {year})"
        )
        return

    coal = np.zeros(result.dispatch.shape[1])
    gas = np.zeros(result.dispatch.shape[1])
    for g, fuel in enumerate(context.fuel_types):
        if fuel == "coal":
            coal += result.dispatch[g]
        elif fuel in _GAS_FUEL_TYPES:
            gas += result.dispatch[g]

    stats = check_hourly_dispatch_correlation({"coal": coal, "gas": gas}, eia_hourly)
    rows: list[tuple] = [("fuel", "pearson r", "nrmse", "model TWh", "EIA TWh")]
    for fuel in ("coal", "gas"):
        s = stats[fuel]
        rows.append(
            (
                fuel,
                f"{s['pearson_r']:.3f}",
                f"{s['nrmse']:.3f}",
                f"{s['model_twh']:.2f}",
                f"{s['eia_twh']:.2f}",
            )
        )
    _print_table("Hourly dispatch correlation (vs EIA-930)", rows)


def _build_parser() -> argparse.ArgumentParser:
    """Return the run_calibration argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_calibration",
        description="Run dispatch for calibration years and compare to EIA.",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        required=True,
        help="One or more calibration years (training window 2023-2025; any "
        "other year is a designated holdout gated by --holdout-authorized "
        "plus the ISO's tier marker, rule 22).",
    )
    parser.add_argument(
        "--iso",
        default="ERCOT",
        help="ISO to calibrate (default ERCOT).",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=8760,
        help="Dispatch horizon in hours (default 8760; 168 for a quick test).",
    )
    parser.add_argument(
        "--ttc-wn",
        type=float,
        default=None,
        help="Override the West<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-wsc",
        type=float,
        default=None,
        help="Override the West<->South_Central transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-pn",
        type=float,
        default=None,
        help="Override the Panhandle<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--coal-passthrough",
        type=float,
        default=None,
        help="Override coal_prb_contract_passthrough (PRB take-or-pay "
        "fuel-cost fraction); 1.0 disables the discount.",
    )
    parser.add_argument(
        "--enable-legacy-p2",
        action="store_true",
        help="Unlock the ARCHIVED P2 commitment pass (last resort). P0/P1 are the "
        "only production passes and every run is scored on P1. --commitment / "
        "--no-coal-p2 are hidden and inert unless this is passed.",
    )
    parser.add_argument(
        "--commitment",
        action="store_true",
        # ARCHIVED P2 trigger — hidden from --help, gated behind --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no-coal-p2",
        action="store_true",
        # ARCHIVED P2 knob — hidden; only meaningful under --enable-legacy-p2.
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--priced-interchange",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Serve interchange through the priced import/export node "
        "(import tranches + export sinks in the ISO's external zone) "
        "instead of the measured schedule added to demand. Default per "
        f"ISO: on for {', '.join(sorted(PRICED_INTERCHANGE_DEFAULT_ISOS))} "
        "(no measured-schedule mode), off elsewhere; pass "
        "--no-priced-interchange to force the measured schedule.",
    )
    parser.add_argument(
        "--reference-price-interface",
        action="store_true",
        help="Serve the priced-interchange seam through the forecast-grade "
        "reference-price interface (per-neighbor gas x heat-rate x "
        "load-shape, cleared on the spread vs the ISO LMP with a hurdle) "
        "instead of the fitted IMPORT_TRANCHES/EXPORT_TRANCHES. Implies "
        "--priced-interchange; gated to ISOs in INTERFACE_NEIGHBORS (PJM). "
        "See docs/reference-price-interface.md.",
    )
    parser.add_argument(
        "--negative-renewable-offers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Floor the curtailable wind/solar dispatch offer at the negative "
        "keep-running (REC/PTC) value so curtailed renewables set a "
        "sub-$0 marginal price in oversupply (CAISO negative midday "
        "LMPs). Default (unset) keeps the per-ISO base config value (ON "
        "for CAISO); --no-negative-renewable-offers forces it off.",
    )
    parser.add_argument(
        "--mass-cap-enabled",
        action="store_true",
        help="Thread the unified carbon resolver's power-sector mass-cap "
        "ROW (policy.cap_and_trade.resolve_carbon_program) into this "
        "calibration year instead of the default measured-price adder "
        "(G-29, docs/handoffs/emissions-mass-cap-plan-2026-07.md). "
        "Diagnostic-only (e.g. the RGGI dual-vs-auction-price validation "
        "probe); never a keeper default. No effect on ISOs with no "
        "cap-and-trade program (ERCOT/MISO) or no published budget for "
        "the requested year.",
    )
    parser.add_argument(
        "--mass-cap-tons",
        type=float,
        default=None,
        help="Explicit annual mass-cap budget (metric tons CO2), overriding "
        "the ISO program's published schedule. Only meaningful with "
        "--mass-cap-enabled.",
    )
    parser.add_argument(
        "--mass-cap-program",
        default=None,
        help="Label override for the mass-cap row's reported allowance "
        "price. Only meaningful with --mass-cap-enabled.",
    )
    parser.add_argument(
        "--no-xyear-warmstart",
        action="store_true",
        help="Disable cross-year LP warm-start (MARKET_SIM_WARMSTART_XYEAR). "
        "It is ON by default on the calibration path — each year's optimal "
        "basis warm-starts the next year's P0 solve (~2.3x faster on warm "
        "years, basis-neutral; see docs/cross-year-warmstart.md). Pass this "
        "to force the cold path (e.g. a basis-independent A/B baseline). An "
        "explicit MARKET_SIM_WARMSTART_XYEAR env var is honored over the "
        "default; this flag overrides both.",
    )
    parser.add_argument(
        "--no-p1-basis-seed",
        action="store_true",
        help="Force the same-year P1 basis seed OFF (MARKET_SIM_P1_BASIS_SEED). "
        "It is OFF by default (rule 36 [R-YEAR-ISOLATION], owner ruling "
        "2026-09-19) — on the ISOs whose keeper carries a P1-native floor "
        "bridge (ERCOT / NYISO gas commitment bridges, CAISO RA must-offer) "
        "the P1 cold-rebuilds a second model on the floored fleet, and the "
        "seed hands it the P0 model's optimal basis instead of starting from "
        "nothing (ERCOT 2025 P1 287 -> 139 s; warm-start class, marginal-tie "
        "only; see docs/cross-year-warmstart.md 'Same-year P1 basis seed'). "
        "Inert wherever the P1 re-solves the live P0 model. INDEPENDENT of "
        "--no-xyear-warmstart since PERF-C S1 (2026-09-20): the seed carries "
        "no cross-year state, so it is gated on its own env var and the "
        "goldens/replay determinism env pins it to 0 explicitly. A seeded P1 "
        "that does not reach Optimal discards the basis and re-solves cold. "
        "An explicit MARKET_SIM_P1_BASIS_SEED env var is honored over the "
        "default; this flag overrides both.",
    )
    parser.add_argument(
        "--no-container-preflight",
        action="store_true",
        help="Skip the container preflight (scripts/lib/solve_container.py): "
        "the binding-cgroup memory ceiling read, the swapfile provisioning up "
        "to 24 GiB, and the single-thread solve-profile pins. On by default "
        "because a per-plant MISO/PJM year exceeds the 13.34 GiB CCR bash "
        "cgroup and is OOM-killed without swap. Does not change the LP.",
    )
    return parser


def resolve_p1_basis_seed_default(disable: bool) -> bool:
    """Resolve the same-year P1 basis seed default for the calibration path.

    The sibling of :func:`resolve_xyear_warmstart_default` for
    ``MARKET_SIM_P1_BASIS_SEED`` (wallclock desk item B; owner memo
    ``docs/handoffs/p1-basis-seed-decision-memo-2026-09.md``, signed (A) FLIP
    2026-09-06). The seed hands the cold-rebuilt P1 model — the route every
    P1-native floor bridge takes — the same year's P0 optimal basis before its
    first solve. Validated warm-start-class neutral (objective and total
    generation identical, per-unit differences marginal-tie only, price
    differences dual-degenerate hours only; memo §3).

    **THAT VALIDATION DID NOT HOLD AND THIS NOW DEFAULTS OFF** (owner ruling
    2026-09-19, miso-262 — the same ruling that flipped
    :func:`resolve_xyear_warmstart_default`, and the two are flipped together
    because the solve core arms this seed only INSIDE the cross-year gate).
    The seed is the component that moves a LEG-FIRST year, where no prior-year
    basis exists: MISO 2020 and 2023 are the first years of their legs and
    still diverge from a pinned-cold replay by 0.0048 and 0.1440 TWh, which is
    small but is not the "identical" the memo claims. On later years it
    compounds with the cross-year basis into 7.16-24.18 TWh. Evidence:
    ``docs/RESULT-miso262-mer-control-and-the-year-grouping-defect-2026-09-19.md``
    §3.

    Same precedence as the cross-year resolver, highest first:

    1. ``--no-p1-basis-seed`` (``disable=True``) → force OFF.
    2. An explicitly-set ``MARKET_SIM_P1_BASIS_SEED`` env var → honored as-is.
    3. Otherwise → default **OFF**.

    Sets ``os.environ["MARKET_SIM_P1_BASIS_SEED"]`` so the shared solve core
    (``pipeline.solve.run_energy_solve``) reads the resolved value, and returns
    the resolved boolean.

    **THE SEED IS NO LONGER NESTED INSIDE THE CROSS-YEAR GATE** (PERF-C S1,
    2026-09-20, ``docs/handoffs/FINDING-perfc-s1-p1-seed-2026-09-20.md``). This
    paragraph used to read "the resolved value is necessary, not sufficient:
    the solve core arms the seed only INSIDE the cross-year gate", and that
    coupling is what took the same-year seed down with rule 36's cross-year
    ruling — a ruling whose evidence (miso-262) is entirely about state
    crossing a YEAR boundary, which this seed does not do: it installs this
    year's own P0 basis on this year's own P1, inside one
    ``run_energy_solve`` call. The two knobs are now independent. What still
    binds, in ``pipeline.solve``: the intra-year warm start must be on (the
    seed's source is the live P0 ``DispatchModel``) and the caller must leave
    ``xyear_warmstart`` at ``None``, so the forecast path — an explicit gate
    argument — never reads this env var at all.

    **Consequence for reproducibility**: ``--no-xyear-warmstart`` no longer
    turns this off with it, so ``scripts/capture_keeper_goldens.py`` and
    ``scripts/replay_keeper.py`` pin ``MARKET_SIM_P1_BASIS_SEED=0`` in their
    determinism env explicitly. Calibration fresh-solve path only: ``--report``
    / ``--replay-bundle`` / ``--rebuild-benchmark`` and the direct
    ``solve_and_persist`` callers keep the global default OFF.

    **The default stays OFF and flipping it is the owner's call.** PERF-C S1
    removed the coupling ONLY; it produced no new timing evidence and ran no
    solve to measure speed. The standing numbers are desk-log item B
    (``docs/handoffs/wallclock-desk-log-2026-09.md``).
    """
    if disable:
        os.environ["MARKET_SIM_P1_BASIS_SEED"] = "0"
    elif "MARKET_SIM_P1_BASIS_SEED" not in os.environ:
        # Owner ruling 2026-09-19 (miso-262): default OFF. Was "1".
        os.environ["MARKET_SIM_P1_BASIS_SEED"] = "0"
    # else: env var explicitly set by the caller -> honor it verbatim.
    return os.environ.get("MARKET_SIM_P1_BASIS_SEED", "0") != "0"


def resolve_xyear_warmstart_default(disable: bool) -> bool:
    """Resolve the cross-year LP warm-start default for the calibration path.

    Cross-year warm-start (``MARKET_SIM_WARMSTART_XYEAR``) carries each backcast
    year's optimal basis into the next year's cold P0 solve. It is validated
    basis-neutral on the calibration/backcast path — objective, every zonal
    price and total generation are bit-identical; the only movement is the
    marginal-tie reshuffling the intra-year warm start already ships (see
    ``docs/cross-year-warmstart.md``).

    **THAT NEUTRALITY CLAIM IS FALSIFIED AND THIS NOW DEFAULTS OFF** (owner
    ruling 2026-09-19, miso-262). Measured on MISO's designated keeper by
    replaying each of its six years standalone against the same committed
    bundle at one pinned HEAD: the first year of each solve leg reproduces
    (max |Δ class TWh| 0.0048 in 2020, 0.1440 in 2023) and the later years do
    not (7.1586 / 24.1796 / 4.0034 in 2021 / 2022 / 2025), with 43,160 of
    70,080 price cells moving in 2022. It is deterministic — two independent
    shards in different containers reproduced 2021 byte-identically — and it is
    not two optima of one LP: the 2022 swap moves 24 TWh off CC_REGULAR
    (median ``mc`` $54.52/MWh) onto coal ($31.93/MWh) to serve identical
    demand, of order $500 M of objective, so the warm-started solve was not at
    the optimum. Record:
    ``docs/RESULT-miso262-mer-control-and-the-year-grouping-defect-2026-09-19.md``.

    **A BACKCAST HAS NO REASON TO WANT THIS.** Its years are independent by
    construction — every input is that year's own EIA-860/923 vintage, and the
    backcast year loop carries no ``evolve_fleet``, no ``prior_results`` and no
    carry-forward of any kind, so the LP basis was the ONLY channel crossing a
    year boundary. Cross-year warm start was a wallclock optimisation for
    multi-year spans, and per-year shard containers (CLAUDE.md rule 36
    ``[R-YEAR-ISOLATION]``) make it obsolete. A FORECAST genuinely needs the
    span — year 2's builds set year 3's fleet — but the forecast never reads
    this env var (it passes an explicit ``xyear_warmstart``), so nothing there
    moves.

    Precedence, highest first:

    1. ``--no-xyear-warmstart`` (``disable=True``) → force OFF.
    2. An explicitly-set ``MARKET_SIM_WARMSTART_XYEAR`` env var → honored as-is
       (the escape hatch for a deliberate wallclock experiment, which is then
       a solve-affecting choice the run must declare).
    3. Otherwise → default **OFF**.

    Sets ``os.environ["MARKET_SIM_WARMSTART_XYEAR"]`` so the shared solve core
    (``pipeline.solve.run_energy_solve``) reads the resolved value, and returns
    the resolved boolean. **Calibration path only, and it stays that way for a
    different reason than it used to.** This docstring formerly said the
    forecast loop "passes ``xyear_cache=None`` and cannot consume the basis
    regardless of the env var" — that stopped being true at owner decision D-9
    (2026-07-26), which wired the forecast's own holder behind
    ``ScenarioConfig.forecast_xyear_warmstart``. What isolates the two lanes
    now is the gate ARGUMENT, not an absent holder: ``runner.py`` passes an
    explicit ``xyear_warmstart`` bool, and ``run_energy_solve`` defers to this
    env var only when that argument is ``None`` — which is what the calibration
    path (and only the calibration path) passes. So this env var still cannot
    reach a forecast, and since owner decision **D-10** (2026-08-04) every
    forecast bundle passes ``False`` explicitly, making the forecast cold-only
    again — by decision this time, not by plumbing.
    """
    if disable:
        os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"
    elif "MARKET_SIM_WARMSTART_XYEAR" not in os.environ:
        # Owner ruling 2026-09-19 (miso-262): default OFF. Was "1".
        os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"
    # else: env var explicitly set by the caller -> honor it verbatim.
    return os.environ.get("MARKET_SIM_WARMSTART_XYEAR", "0") != "0"


def main(argv: list[str] | None = None) -> None:
    """Entry point: run each requested calibration year and print diagnostics.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    # P2 is ARCHIVED (P0/P1 only; scored on P1). Reaching for it without the
    # explicit unlock is a hard error so it is never a silent calibration option.
    if (args.commitment or args.no_coal_p2) and not args.enable_legacy_p2:
        parser.error(
            "the P2 commitment pass is ARCHIVED (P0/P1 only; runs are scored on "
            "P1). --commitment / --no-coal-p2 require --enable-legacy-p2 to run "
            'P2 as a last resort. See CLAUDE.md "Dispatch & Commitment".'
        )
    iso = args.iso.upper()
    # CLAUDE.md rule 22 [R-HOLDOUT]: until 2026-08 this CLI was the one solve
    # entry point outside the three-gate enforcement (third-party audit
    # 2026-08, gap row B1) — a direct `--year 2022` here solved with no
    # code-level gate. Reuse run_calibration_full's single-home gate rather
    # than a second copy of the policy (the replay_keeper.py /
    # backfill_nonfossil_hourly.py pattern); imported lazily so importing this
    # module for its helpers stays cheap. The gate checks the freeze file
    # first and fails closed (tier map from scripts/lib/holdout_policy.py).
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    # Container preflight BEFORE the first loader allocates anything: binding
    # cgroup ceiling, swap provisioning, solve-profile pins (the same call
    # run_calibration_full.solve_and_persist makes; once per process, never
    # raises, does not change the LP). --no-container-preflight skips it.
    if not args.no_container_preflight:
        from scripts.lib.solve_container import ensure_solve_container

        ensure_solve_container(log=logger)

    # The reference-price interface is on when the CLI flag is set OR the ISO is
    # in the per-ISO default-on set (MISO); see resolve_reference_price_interface.
    reference_price_interface = resolve_reference_price_interface(
        args.reference_price_interface, iso
    )
    priced_interchange = resolve_priced_interchange(args.priced_interchange, iso)
    # The reference-price interface serves the seam through the priced node, so
    # it implies priced interchange (unless explicitly turned off on the CLI).
    if reference_price_interface and args.priced_interchange is not False:
        priced_interchange = True
    reference = _load_reference()
    ttc_overrides = {
        "ttc_wn": args.ttc_wn,
        "ttc_wsc": args.ttc_wsc,
        "ttc_pn": args.ttc_pn,
    }

    # Cross-year warm-start defaults ON for calibration (--no-xyear-warmstart to
    # opt out, explicit env var honored). Resolved before the year loop so every
    # run_year sees the same gate; sets MARKET_SIM_WARMSTART_XYEAR for the shared
    # solve core. Forecast (runner.py) is unaffected (xyear_cache=None).
    _xwarm = resolve_xyear_warmstart_default(args.no_xyear_warmstart)
    logger.info("cross-year LP warm-start: %s", "ON" if _xwarm else "OFF")
    # Same-year P1 basis seed (item B): default OFF (rule 36), --no-p1-basis-
    # seed to force OFF, explicit env var honored. INDEPENDENT of the gate
    # above since PERF-C S1 — the reported state is the resolver's own, not
    # ``_p1_seed and _xwarm``, because the solve core no longer nests them.
    _p1_seed = resolve_p1_basis_seed_default(args.no_p1_basis_seed)
    logger.info("P1 basis seed: %s", "ON" if _p1_seed else "OFF")

    # Single-element holder carrying the prior year's optimal basis across
    # run_year calls for cross-year warm-start (MARKET_SIM_WARMSTART_XYEAR=1).
    # Years are run in the order requested, so listing them chronologically lets
    # each P0 warm-start from the adjacent year's basis.
    xyear_cache: list = []
    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            iso,
            year,
            args.hours,
            gas_price,
        )
        result, context, result_p1, _ = run_year(
            year,
            iso,
            args.hours,
            gas_price,
            ttc_overrides,
            args.coal_passthrough,
            commitment_enabled=args.commitment,
            commitment_screen_coal=not args.no_coal_p2,
            priced_interchange=priced_interchange,
            reference_price_interface=reference_price_interface,
            negative_renewable_offers=args.negative_renewable_offers,
            mass_cap_enabled=args.mass_cap_enabled,
            mass_cap_tons=args.mass_cap_tons,
            mass_cap_program=args.mass_cap_program,
            xyear_cache=xyear_cache,
        )
        if result_p1 is not None:
            _report_year(year, iso, result_p1, context, reference, label="P1")
            _report_year(year, iso, result, context, reference, label="P2")
        else:
            _report_year(year, iso, result, context, reference)


if __name__ == "__main__":
    main()
