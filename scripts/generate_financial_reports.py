"""Generate plant-level and company-level financial reports for a scenario.

Orchestrates the full plant-financials pipeline:

1. Load the scenario's cached bin-level dispatch parquets (one per year).
2. Resolve fuel, carbon and NOx prices from the cached ``ScenarioConfig``.
3. Build the plant-to-bin map from the EIA-860 fleet.
4. For each year: disaggregate bin dispatch to plants, compute hourly
   financials, aggregate to an annual per-plant summary.
5. Join with the ownership map and roll up to parent companies.
6. Accumulate trajectory NPV across all years.
7. Write parquet (model data) and CSV (human-readable report) outputs.

Memory: years are processed one at a time. Only the small annual summary
frames are retained for the trajectory NPV; hourly data is written and
released per year, and is emitted to parquet only under ``--include-hourly``.

Usage:
    python scripts/generate_financial_reports.py \\
        --results-dir results/ERCOT/abc123def/ \\
        --eia860-path data/fleet/eia860_2024.xlsx \\
        --ownership-map data/ownership/parent_company_fleet_2024.parquet \\
        --iso ERCOT --output-dir reports/ --years 2026-2050 \\
        [--discount-rate 0.08] [--include-hourly]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    COAL_PRICE_BASE,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel import resolve_annual_gas_price  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    PROCESSED_DIR,
    load_fleet_from_csv,
)
from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.results import outputs as _outputs  # noqa: E402,F401
from market_sim.results.cache import get_cache_path, get_config_path  # noqa: E402
from market_sim.results.outputs import read_fleet_context  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.results.plant_financials import (  # noqa: E402
    build_plant_bin_map,
    compute_company_summary,
    compute_plant_annual_summary,
    compute_plant_hourly_financials,
    compute_trajectory_npv,
    disaggregate_dispatch,
)
from market_sim.data.ownership import build_parent_mapping  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("generate_financial_reports")

# Model fuel types that burn natural gas and pay the escalated gas price.
_GAS_FUELS = ("gas_cc", "gas_ct", "gas_cc_ccs")


def _parse_years(spec: str) -> list[int]:
    """Parse a ``2026-2050`` or ``2026,2030`` year spec into a list of ints."""
    if "-" in spec:
        lo, hi = (int(x) for x in spec.split("-", 1))
        return list(range(lo, hi + 1))
    return [int(x) for x in spec.split(",")]


def _bin_dispatch_frame(
    result: DispatchResult, context, zone_names: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(bin_dispatch, zonal_prices)`` long-format frames.

    ``bin_dispatch`` has columns ``bin_label``, ``zone``, ``hour`` and
    ``dispatch_mw``; ``zonal_prices`` has ``zone``, ``hour`` and
    ``price_per_mwh``. The per-generator bin label is
    ``{fuel_type}_{efficiency_bin}``.
    """
    dispatch = np.asarray(result.dispatch, dtype=float)  # (n_gen, T)
    n_gen, T = dispatch.shape
    bin_labels = [
        f"{f}_{b}"
        for f, b in zip(context.fuel_types, context.efficiency_bins, strict=True)
    ]
    gen_df = pd.DataFrame(
        {
            "bin_label": np.repeat(bin_labels, T),
            "zone": np.repeat(context.zones, T),
            "hour": np.tile(np.arange(T), n_gen),
            "dispatch_mw": dispatch.ravel(),
        }
    )
    bin_dispatch = gen_df.groupby(["bin_label", "zone", "hour"], as_index=False)[
        "dispatch_mw"
    ].sum()

    prices = np.asarray(result.prices, dtype=float)  # (n_zones, T)
    n_zones = prices.shape[0]
    zonal_prices = pd.DataFrame(
        {
            "zone": np.repeat(zone_names[:n_zones], T),
            "hour": np.tile(np.arange(T), n_zones),
            "price_per_mwh": prices.ravel(),
        }
    )
    return bin_dispatch, zonal_prices


def _fuel_price_frame(config: ScenarioConfig, year: int, hours: int) -> pd.DataFrame:
    """Return a ``fuel_type × hour`` delivered fuel price frame ($/MMBtu).

    Gas-burning fuels pay the delivered Henry Hub price for the year (AEO
    trajectory + regional basis); coal pays the flat ISO coal price; all
    other fuels carry zero cost.
    """
    gas_price = resolve_annual_gas_price(config, year)
    coal_price = COAL_PRICE_BASE[config.iso]
    per_fuel = {f: gas_price for f in _GAS_FUELS}
    per_fuel["coal"] = coal_price

    rows = []
    hour_arr = np.arange(hours)
    for fuel, price in per_fuel.items():
        rows.append(
            pd.DataFrame(
                {"fuel_type": fuel, "hour": hour_arr, "price_per_mmbtu": price}
            )
        )
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    """Run the financial-report pipeline for one cached scenario."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--eia860-path", type=Path, required=True)
    parser.add_argument("--ownership-map", type=Path, required=True)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--output-dir", type=Path, default=REPO / "reports")
    parser.add_argument("--years", default="2026-2050")
    parser.add_argument(
        "--discount-rate",
        type=float,
        default=None,
        help="Overrides ScenarioConfig.real_discount_rate.",
    )
    parser.add_argument(
        "--include-hourly",
        action="store_true",
        help="Also write the (large) per-year hourly parquet.",
    )
    args = parser.parse_args()

    if not args.results_dir.is_dir():
        raise SystemExit(f"results directory not found: {args.results_dir}")

    scenario_hash = args.results_dir.resolve().name
    out_dir = args.output_dir / scenario_hash
    out_dir.mkdir(parents=True, exist_ok=True)
    years = _parse_years(args.years)

    # Cached scenario config sits beside the year parquets.
    config_path = get_config_path(args.iso, scenario_hash, years[0])
    if config_path.exists():
        config = ScenarioConfig.from_yaml(config_path)
    elif (args.results_dir / "config.yaml").exists():
        config = ScenarioConfig.from_yaml(args.results_dir / "config.yaml")
    else:
        raise SystemExit(f"no config.yaml found for scenario {scenario_hash}")
    discount_rate = args.discount_rate or config.real_discount_rate
    base_year = START_YEAR

    iso_config = get_iso_config(args.iso)
    zone_names = list(iso_config.zone_names)

    # Plant-bin map: ensure the binned-fleet parquet exists, then build it.
    load_fleet_from_csv(args.iso, iso_config, data_dir=args.eia860_path.parent)
    fleet_parquet = PROCESSED_DIR / f"{args.iso.lower()}_fleet_binned.parquet"
    plant_map = build_plant_bin_map(fleet_parquet)

    ownership_df = build_parent_mapping(pd.read_parquet(args.ownership_map))

    annual_summaries: list[pd.DataFrame] = []
    company_summaries: list[pd.DataFrame] = []
    used_years: list[int] = []

    for year in years:
        cache_path = get_cache_path(args.iso, scenario_hash, year)
        if not cache_path.exists():
            logger.warning("no cached dispatch for %d — skipping", year)
            continue

        result = DispatchResult.from_parquet(cache_path)
        context = read_fleet_context(cache_path)

        bin_dispatch, zonal_prices = _bin_dispatch_frame(result, context, zone_names)
        hours = int(bin_dispatch["hour"].max()) + 1
        fuel_prices = _fuel_price_frame(config, year, hours)
        carbon_price = resolve_carbon_price(config, year)
        nox_price = config.nox_price

        plant_dispatch = disaggregate_dispatch(bin_dispatch, plant_map)
        hourly = compute_plant_hourly_financials(
            plant_dispatch,
            zonal_prices,
            fuel_prices,
            carbon_price,
            nox_price,
            plant_map,
            discount_rate=discount_rate,
            year=year,
            base_year=base_year,
        )
        if args.include_hourly:
            hourly.to_parquet(out_dir / f"plant_hourly_{year}.parquet", index=False)

        annual = compute_plant_annual_summary(
            hourly,
            plant_map,
            discount_rate=discount_rate,
            year=year,
            base_year=base_year,
            iso=args.iso,
            config=config,
        )
        annual.to_parquet(out_dir / f"plant_annual_{year}.parquet", index=False)
        del hourly  # release the large hourly frame before the next year

        company_total, company_by_fuel = compute_company_summary(annual, ownership_df)
        company_total.to_parquet(
            out_dir / f"company_annual_{year}.parquet", index=False
        )
        company_by_fuel.to_parquet(
            out_dir / f"company_by_fuel_{year}.parquet", index=False
        )

        annual_summaries.append(annual)
        company_summaries.append(company_total.assign(year=year))
        used_years.append(year)
        logger.info(
            "year %d: %d plants, %d companies", year, len(annual), len(company_total)
        )

    if not used_years:
        raise SystemExit("no cached dispatch years found — nothing to report")

    # Trajectory NPV — plant-level and company-level.
    plant_traj = compute_trajectory_npv(
        annual_summaries, used_years, discount_rate, base_year
    )
    plant_traj.to_parquet(out_dir / "trajectory_npv.parquet", index=False)
    company_traj = compute_trajectory_npv(
        company_summaries, used_years, discount_rate, base_year
    )
    company_traj.to_parquet(out_dir / "trajectory_company_npv.parquet", index=False)

    # Human-readable CSV reports (exception to the parquet-only rule).
    _write_csv_reports(out_dir, company_summaries, used_years, plant_traj)
    logger.info("Wrote financial reports → %s", out_dir)


def _write_csv_reports(
    out_dir: Path,
    company_summaries: list[pd.DataFrame],
    years: list[int],
    plant_traj: pd.DataFrame,
) -> None:
    """Write the three human-readable CSV report summaries."""
    all_company = pd.concat(company_summaries, ignore_index=True)

    # W2-B: the attribute (certificate) line — effective EAC/CES premium ×
    # generation, PTC/45Q excluded — resolved by compute_plant_annual_summary
    # from the cached config + year threaded through main() above.
    top = (
        all_company.groupby("parent_company", as_index=False)
        .agg(
            total_generation_mwh=("owned_generation_mwh", "sum"),
            total_revenue=("owned_revenue", "sum"),
            total_attribute_revenue=("owned_attribute_revenue", "sum"),
            total_co2_tons=("owned_co2_emissions_tons", "sum"),
        )
        .sort_values("total_generation_mwh", ascending=False)
    )
    top.to_csv(out_dir / "top_companies_summary.csv", index=False)

    plant_traj.sort_values("cumulative_npv_noi", ascending=False).to_csv(
        out_dir / "plant_profitability_ranking.csv", index=False
    )

    emissions = all_company.pivot_table(
        index="parent_company",
        columns="year",
        values="owned_co2_emissions_tons",
        aggfunc="sum",
    ).reset_index()
    emissions.to_csv(out_dir / "emissions_by_company.csv", index=False)


if __name__ == "__main__":
    main()
