"""Run the dispatch model for calibration years and print comparison tables.

Backcasts the hourly economic dispatch against historical years (2021-2024)
for which EIA actuals exist, then prints headline diagnostics — generation by
fuel, CO2, zonal prices, negative-price hours and renewable curtailment — so
the modeled year can be eyeballed against the eGRID benchmark.

Each calibration year is run as a single-year dispatch (no capacity
evolution): the EIA-860 fleet is dispatched against that year's EIA-930
demand and renewable profiles, with the renewable capacity and gas price
pinned to the year's measured values.

Usage:
    python scripts/run_calibration.py --year 2023
    python scripts/run_calibration.py --year 2021 2022 2023 2024
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
import json
import logging
import sys
from dataclasses import fields
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.cycling import apply_cycling_adders  # noqa: E402
from market_sim.data.eia_loader import load_demand  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    aggregate_fleet,
    apply_coal_sunk_cost,
    assemble_mc,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.fuel import resolve_fuel_prices  # noqa: E402
from market_sim.data.renewables import (  # noqa: E402
    inject_offshore_wind_availability,
    load_renewable_profiles,
)
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from market_sim.model.storage import (  # noqa: E402
    load_eia860_storage,
    storage_units_to_arrays,
)
from market_sim.model.transmission import (  # noqa: E402
    build_incidence_matrix,
    get_ttc_array,
)
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.eac import (  # noqa: E402
    apply_eac_to_mc,
    compute_eac_dispatch_credits,
)
from market_sim.policy.ira import compute_dispatch_credits  # noqa: E402
from market_sim.results.emissions import compute_emissions  # noqa: E402
from market_sim.results.outputs import FleetContext  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_calibration")

# Calibration reference written by scripts/build_calibration_reference.py.
REFERENCE_PATH: Path = REPO / "inputs" / "calibration" / "calibration_reference.json"

# Fallback measured Henry Hub annual-average spot price ($/MMBtu), used when
# the calibration reference JSON has not yet been generated.
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
_HENRY_HUB_FALLBACK: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
}

_MWH_PER_TWH: float = 1.0e6
_TONNES_PER_MT: float = 1.0e6

# Zone-pair identifying each transfer link whose TTC the CLI can override.
# Both legs of the West Texas Export interface and the Panhandle GTC are
# exposed for tuning — these are ERCOT's primary wind-export constraints.
_TTC_LINK_ZONES: dict[str, frozenset[str]] = {
    "ttc_wn": frozenset({"West", "North"}),
    "ttc_wsc": frozenset({"West", "South_Central"}),
    "ttc_pn": frozenset({"Panhandle", "North"}),
}


def _load_reference() -> dict:
    """Return the calibration reference dict, or an empty dict if unbuilt."""
    if not REFERENCE_PATH.exists():
        logger.warning(
            "calibration reference %s not found — run "
            "build_calibration_reference.py first; using fallback gas prices",
            REFERENCE_PATH.relative_to(REPO),
        )
        return {}
    return json.loads(REFERENCE_PATH.read_text())


def _henry_hub_actual(reference: dict, year: int) -> float:
    """Return the measured Henry Hub price for ``year`` from the reference."""
    table = reference.get("henry_hub_actual", {})
    if str(year) in table:
        return float(table[str(year)])
    return _HENRY_HUB_FALLBACK[year]


def _calibration_config(year: int, iso: str, hours: int, gas_price: float):
    """Build the ScenarioConfig for one calibration year.

    The calibration configuration fixes the structural and policy levers to
    their backcast values: the weather year is the calibration year, the
    EIA-860 vintage capacity ramp is on, T&D losses are grossed up, gas
    seasonality is on, and the carbon price and RPS constraint are off.

    The measured Henry Hub price is applied through ``gas_price_override``
    when that field exists on :class:`ScenarioConfig`; otherwise the run
    falls back to the configured ``gas_price_path`` trajectory.

    Args:
        year: Calibration year.
        iso: ISO identifier.
        hours: Dispatch horizon in hours.
        gas_price: Measured Henry Hub annual price ($/MMBtu).

    Returns:
        The calibration :class:`ScenarioConfig`.
    """
    config = ScenarioConfig(
        weather_year=year,
        iso=iso,
        hours=hours,
        vintage_capacity_ramp=True,
        td_loss_factor=0.058,
        gas_seasonality=True,
        carbon_price=0.0,
        rps_enabled=False,
        commitment_enabled=True,
    )
    if any(f.name == "gas_price_override" for f in fields(ScenarioConfig)):
        config = config.with_overrides(gas_price_override=gas_price)
    else:
        logger.warning(
            "ScenarioConfig has no gas_price_override field; "
            "year %d falls back to the '%s' gas-price trajectory",
            year, config.gas_price_path,
        )
    return config


def _apply_ttc_overrides(
    iso_config, ttc: np.ndarray, overrides: dict[str, float | None]
) -> np.ndarray:
    """Return ``ttc`` with the requested link capabilities overridden.

    Args:
        iso_config: The ISO topology, used to map links to zone pairs.
        ttc: The base ``(n_links,)`` transfer-capability array.
        overrides: ``{"ttc_wn": MW | None, "ttc_wsc": MW | None,
            "ttc_pn": MW | None}``.

    Returns:
        A copy of ``ttc`` with each non-``None`` override applied.
    """
    ttc = ttc.copy()
    for key, value in overrides.items():
        if value is None:
            continue
        target = _TTC_LINK_ZONES[key]
        for i, link in enumerate(iso_config.links):
            if frozenset({link.from_zone, link.to_zone}) == target:
                logger.info(
                    "override %s link TTC: %.0f -> %.0f MW",
                    "-".join(sorted(target)), ttc[i], value,
                )
                ttc[i] = value
    return ttc


def run_year(
    year: int,
    iso: str,
    hours: int,
    gas_price: float,
    ttc_overrides: dict[str, float | None],
) -> tuple[object, FleetContext]:
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

    Returns:
        A tuple ``(result, context)`` of the dispatch result and the fleet
        context describing the dispatched fleet.
    """
    config = _calibration_config(year, iso, hours, gas_price)
    iso_config = get_iso_config(iso)
    zone_names = iso_config.zone_names

    demand = load_demand(
        iso, year, iso_config, td_loss_factor=config.td_loss_factor
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, :config.hours]
        wind_cf = wind_cf[:, :config.hours]
        solar_cf = solar_cf[:, :config.hours]

    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = _apply_ttc_overrides(
        iso_config, get_ttc_array(iso_config.links), ttc_overrides
    )

    fleet = aggregate_fleet(
        load_fleet_from_csv(iso, iso_config), n_bins=config.heat_rate_bin_count
    )
    fleet_arrays = generators_to_fleet_arrays(
        fleet, zone_names, hours=config.hours, iso=iso, config=config
    )
    inject_offshore_wind_availability(fleet_arrays, wind_cf, config, iso)

    fuel_prices = resolve_fuel_prices(config, fleet_arrays, year)
    carbon_price = resolve_carbon_price(config, year)
    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    mc = assemble_mc(fleet_arrays, fuel_prices, carbon_price, config.nox_price)
    mc = apply_cycling_adders(mc, fleet, fleet_arrays, config)
    apply_eac_to_mc(mc, fleet_arrays, config)
    # Coal bids below full fuel cost: take-or-pay fuel contracts make the
    # contracted fuel sunk regardless of dispatch.
    mc = apply_coal_sunk_cost(mc, fleet_arrays, fleet, fuel_prices, config)
    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    wind_mc -= wind_eac
    solar_mc -= solar_eac

    storage = storage_units_to_arrays(
        load_eia860_storage(iso, year), zone_names
    )

    dispatch_kwargs = dict(
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        mc=mc,
        voll=config.voll,
        incidence=incidence,
        ttc=ttc,
        storage_power_cap=storage.power_cap,
        storage_energy_cap=storage.energy_cap,
        storage_zone_idx=storage.zone_idx,
        eta_chg=storage.eta_chg,
        eta_dis=storage.eta_dis,
        wind_mc=wind_mc,
        solar_mc=solar_mc,
        storage_discharge_eac=storage_eac,
        rps_target=None,
        T=config.hours,
    )
    result = solve_dispatch(fleet_arrays, demand, **dispatch_kwargs)

    # Optional 2-pass commitment: screen Pass-1 prices to decommit thermal
    # hours that cannot clear the startup IRR hurdle, then re-solve.
    if config.commitment_enabled:
        from market_sim.model.commitment import (
            apply_commitment,
            compute_commitment,
        )

        committed = compute_commitment(
            result.prices,
            mc,
            fleet,
            fleet_arrays,
            config,
            demand=demand,
            wind_dispatched=result.wind_dispatched,
            solar_dispatched=result.solar_dispatched,
        )
        fleet_arrays_p2 = apply_commitment(
            fleet_arrays, committed, fleet, p1_dispatch=result.dispatch
        )
        result = solve_dispatch(fleet_arrays_p2, demand, **dispatch_kwargs)

    context = FleetContext.from_arrays(
        fleet_arrays, iso_config, wind_cf, wind_cap, solar_cf, solar_cap,
        storage.energy_cap,
    )
    return result, context


def _generation_twh(result, context: FleetContext) -> dict[str, float]:
    """Return modeled annual generation by fuel (TWh)."""
    gen_per_unit = result.dispatch.sum(axis=1)
    twh: dict[str, float] = {}
    for g, fuel in enumerate(context.fuel_types):
        twh[fuel] = twh.get(fuel, 0.0) + float(gen_per_unit[g]) / _MWH_PER_TWH
    twh["wind"] = twh.get("wind", 0.0) + float(
        result.wind_dispatched.sum()
    ) / _MWH_PER_TWH
    twh["solar"] = twh.get("solar", 0.0) + float(
        result.solar_dispatched.sum()
    ) / _MWH_PER_TWH
    return twh


def _curtailment_pct(potential: float, dispatched: float) -> float:
    """Return curtailed energy as a percentage of available potential."""
    if potential <= 0.0:
        return 0.0
    return 100.0 * max(potential - dispatched, 0.0) / potential


def _print_table(title: str, rows: list[tuple]) -> None:
    """Print a titled, column-aligned text table."""
    print(f"\n  {title}")
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        cells = [str(row[c]).rjust(widths[c]) for c in range(len(row))]
        print("    " + "  ".join(cells))


def _report_year(year: int, iso: str, result, context: FleetContext,
                  reference: dict) -> None:
    """Print the calibration diagnostics for one solved ISO-year."""
    print(f"\n{'=' * 64}")
    print(f"  Calibration: {iso} {year}   (status: {result.status})")
    print(f"{'=' * 64}")

    model_twh = _generation_twh(result, context)
    # The eGRID benchmark is a full-year snapshot; compare only the
    # calibration year it describes, and only for a full 8760-hour run —
    # a sub-annual horizon (--hours) is a smoke test, not a backcast.
    full_year = result.dispatch.shape[1] >= HOURS_PER_YEAR
    iso_benchmark = reference.get("egrid_benchmark", {}).get(iso, {})
    benchmark = (
        iso_benchmark
        if full_year and iso_benchmark.get("benchmark_year") == year
        else {}
    )
    if not full_year:
        print(
            f"\n  NOTE: {result.dispatch.shape[1]}-hour run — eGRID "
            "benchmark comparison suppressed (full 8760h required)."
        )
    bench_twh = benchmark.get("generation_twh", {})

    fuels = sorted(set(model_twh) | set(bench_twh))
    gen_rows: list[tuple] = [("fuel", "model TWh", "eGRID TWh", "diff %")]
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
    gen_rows.append((
        "TOTAL", f"{total_m:.2f}",
        f"{total_b:.2f}" if total_b else "—",
        f"{100.0 * (total_m - total_b) / total_b:+.1f}" if total_b else "—",
    ))
    _print_table("Generation by fuel", gen_rows)

    emissions_t = float(
        compute_emissions(result.dispatch, np.asarray(context.emission_rate)).sum()
    )
    model_co2 = emissions_t / _TONNES_PER_MT
    bench_co2 = benchmark.get("co2_mt")
    if bench_co2 is not None:
        total_bench_co2 = sum(bench_co2.values())
        co2_line = (
            f"model {model_co2:.2f} Mt   eGRID {total_bench_co2:.2f} Mt   "
            f"diff {100.0 * (model_co2 - total_bench_co2) / total_bench_co2:+.1f}%"
        )
    else:
        co2_line = f"model {model_co2:.2f} Mt   (no benchmark for {year})"
    print(f"\n  CO2 emissions\n    {co2_line}")

    price_rows: list[tuple] = [("zone", "avg $/MWh", "neg-price hrs")]
    iso_config = get_iso_config(iso)
    for z, zone in enumerate(iso_config.zone_names):
        zone_price = result.prices[z]
        price_rows.append((
            zone,
            f"{zone_price.mean():.2f}",
            str(int((zone_price < 0.0).sum())),
        ))
    system_price = result.prices.mean(axis=0)
    price_rows.append((
        "SYSTEM",
        f"{system_price.mean():.2f}",
        str(int((system_price < 0.0).sum())),
    ))
    _print_table("Zonal prices", price_rows)

    wind_curt = _curtailment_pct(
        context.wind_potential_mwh, float(result.wind_dispatched.sum())
    )
    solar_curt = _curtailment_pct(
        context.solar_potential_mwh, float(result.solar_dispatched.sum())
    )
    _print_table("Renewable curtailment", [
        ("resource", "installed GW", "curtailed %"),
        ("wind", f"{context.wind_cap_mw / 1e3:.2f}", f"{wind_curt:.1f}"),
        ("solar", f"{context.solar_cap_mw / 1e3:.2f}", f"{solar_curt:.1f}"),
    ])


def _build_parser() -> argparse.ArgumentParser:
    """Return the run_calibration argument parser."""
    parser = argparse.ArgumentParser(
        prog="run_calibration",
        description="Run dispatch for calibration years and compare to EIA.",
    )
    parser.add_argument(
        "--year", type=int, nargs="+", required=True,
        help="One or more calibration years (2021-2024).",
    )
    parser.add_argument(
        "--iso", default="ERCOT", help="ISO to calibrate (default ERCOT).",
    )
    parser.add_argument(
        "--hours", type=int, default=8760,
        help="Dispatch horizon in hours (default 8760; 168 for a quick test).",
    )
    parser.add_argument(
        "--ttc-wn", type=float, default=None,
        help="Override the West<->North transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-wsc", type=float, default=None,
        help="Override the West<->South_Central transfer capability (MW).",
    )
    parser.add_argument(
        "--ttc-pn", type=float, default=None,
        help="Override the Panhandle<->North transfer capability (MW).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: run each requested calibration year and print diagnostics.

    Args:
        argv: Argument vector to parse. Defaults to ``sys.argv[1:]``.
    """
    args = _build_parser().parse_args(argv)
    iso = args.iso.upper()
    reference = _load_reference()
    ttc_overrides = {
        "ttc_wn": args.ttc_wn,
        "ttc_wsc": args.ttc_wsc,
        "ttc_pn": args.ttc_pn,
    }

    for year in args.year:
        gas_price = _henry_hub_actual(reference, year)
        logger.info(
            "running %s %d (hours=%d, Henry Hub=$%.2f/MMBtu)",
            iso, year, args.hours, gas_price,
        )
        result, context = run_year(
            year, iso, args.hours, gas_price, ttc_overrides
        )
        _report_year(year, iso, result, context, reference)


if __name__ == "__main__":
    main()
