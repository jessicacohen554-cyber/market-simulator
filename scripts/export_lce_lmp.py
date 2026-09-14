"""Export BAU forecast LMPs for the standalone Scope 2 LCE Portfolio tool.

Reads cached market-sim forecast results (the LP duals on the zonal energy
balance) for one scenario-year per ISO, collapses the zonal prices to a
single hourly ISO price by load-weighted average, and writes the long-form
``(hour, iso, lmp)`` CSV the portfolio tool's ``lce_portfolio.intake``
module consumes (ADR 0011 export contract, documented in
``scope2-lce-portfolio/docs/decisions/0011-lmp-coupling-scenario-selection.md``
and ``scope2-lce-portfolio/docs/04-lmp-export.md``).

This script lives on the market-sim side of the fence: it imports
``market_sim`` (read-only — cached results and the demand loaders) and only
*writes a data file* into ``scope2-lce-portfolio/data/inputs/`` (gitignored
there). It never imports ``lce_portfolio``.

Zonal→ISO reconciliation mirrors the tool's ``collapse_zonal_lmp`` seam:
per hour, the ISO price is the average of zonal LMPs weighted by that
hour's zonal load; an hour whose total zonal load is zero falls back to the
simple (unweighted) mean of the zonal LMPs. Import/export pseudo-zones
(CAISO ``WECC_import``, PJM's external node, …) carry ``load_share == 0``
so they get zero weight automatically — the ISO price is set by the
load-carrying zones.

Provenance (ADR 0011: which scenario/year produced the series must be
recorded) is written as a sidecar JSON next to the CSV — a ``#`` header
comment inside the CSV would break the consumer's plain ``pd.read_csv``.

**Stub mode (``--dummy``):** the market-sim BAU forecast is not yet
production-ready, so until it is, this script doubles as the format-defining
stub: ``--dummy`` emits a deterministic synthetic LMP series per (iso, year)
in the exact same ``(hour, iso, lmp)`` contract, so the portfolio tool's
intake wiring can be built and validated end-to-end now. The sidecar marks
the file ``synthetic-dummy``; a dummy file must never be presented as a
market-sim forecast. The cache-reading path above is the real coupling and
defines what the LP runner must produce — one final ``DispatchResult`` per
(scenario, iso, year) with zonal ``prices`` duals, cached under
``results/{iso}/{cache_key}/year_{year}.parquet``.

Usage:
    python scripts/export_lce_lmp.py --iso ERCOT --year 2026 --dummy
    python scripts/export_lce_lmp.py --iso ERCOT --iso CAISO --year 2026 \
        --out scope2-lce-portfolio/data/inputs/bau_lmp_2026.csv

A missing cached result is reported and skipped, never solved implicitly:
solve it first with the standard runner entry point
(``market_sim.runner.run_scenario_iso``), which caches each year as it
completes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from market_sim.config.constants import START_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.interchange_config import (  # noqa: E402
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.config.paths import REPO_ROOT  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import load_demand  # noqa: E402
from market_sim.model.transmission import extend_with_import_node  # noqa: E402
from market_sim.results import cache  # noqa: E402

# Anchor the result cache at the repo root so the exporter works from any
# working directory (cache.CACHE_ROOT is a settable module seam, default
# relative "results").
cache.CACHE_ROOT = REPO_ROOT / "results"

# Default output location inside the portfolio tool's gitignored input dir.
_DEFAULT_OUT_DIR = REPO_ROOT / "scope2-lce-portfolio" / "data" / "inputs"

# Synthetic-stub base price level per ISO, $/MWh. PLACEHOLDER values for the
# --dummy wiring stub only — loosely ordered like recent annual averages
# (gas-heavy New England/New York high, MISO low) so downstream sanity
# checks exercise a realistic range, but they are NOT model output and NOT
# citable. The real export reads cached LP duals instead.
_DUMMY_BASE_LMP: dict[str, float] = {
    "ERCOT": 42.0,
    "CAISO": 38.0,
    "PJM": 40.0,
    "MISO": 34.0,
    "NYISO": 45.0,
    "NEISO": 48.0,
    # SPP added 2026-09-07 (lane SPP-34, routed item R-8 of FINDING-spp-20 §5)
    # on SPP's registration as the seventh ISO. Placed below MISO like the rest
    # of the table's loose ordering: SPP is wind-dominated (36.6 % of 2025 net
    # generation) and spends 11-13 % of real-time hours at a negative hub price
    # (docs/multi-iso/spp-data-audit.md). PLACEHOLDER, like every row here.
    "SPP": 32.0,
    # NWPP added 2026-09-14 (lane NWPP-20) on its registration as the eighth
    # region. Placed between MISO and CAISO in the table's loose ordering: the
    # footprint is 36 % hydro by nameplate and the Mid-C traded index sits
    # below the CAISO hubs outside the winter/summer scarcity months
    # (docs/multi-iso/nwpp-data-audit.md). PLACEHOLDER, like every row here.
    "NWPP": 36.0,
    # SOCO added 2026-09-14 (lane SOCO-20) on its registration as the ninth
    # region (NWPP, the eighth, merged the same day). SOCO is a vertically-integrated BALANCING AUTHORITY with NO
    # published LMP at all (card S2 / SOCO-13 read NO price series; rubric
    # v3.8 scores it PRICE UNSCORED), so this row exists only so the --dummy
    # wiring stub is distinguishable from PJM's, exactly as the guard test
    # requires. PLACEHOLDER, like every row here — never a SOCO price claim.
    "SOCO": 36.0,
}
_DUMMY_DEFAULT_BASE: float = 40.0  # any ISO not in the table above


def resolve_bau_config(config: ScenarioConfig, iso: str) -> ScenarioConfig:
    """Return ``config`` canonicalized for ``iso`` exactly as the runner does.

    ``run_scenario_iso`` overrides the config's ISO and then applies the
    ISO's ``default_scenario_overrides`` for every field the caller left at
    its dataclass default, *before* computing the cache key. The exporter
    must replay the same canonicalization or it looks up the wrong cache
    directory.
    """
    iso = iso.upper()
    if config.iso != iso:
        config = config.with_overrides(iso=iso)
    iso_config = get_iso_config(iso)
    if iso_config.default_scenario_overrides:
        defaults = ScenarioConfig()
        overrides_to_apply = {
            k: v
            for k, v in iso_config.default_scenario_overrides.items()
            if getattr(config, k) == getattr(defaults, k)
        }
        if overrides_to_apply:
            config = config.with_overrides(**overrides_to_apply)
    return config


def collapse_zonal_prices(prices: np.ndarray, loads: np.ndarray) -> np.ndarray:
    """Collapse zonal LMPs to one hourly ISO price by load-weighted average.

    Mirrors the portfolio tool's ``collapse_zonal_lmp`` reconciliation seam
    (ADR 0011): per hour the price is ``sum(lmp_z * load_z) / sum(load_z)``;
    an hour whose total zonal load is zero has an undefined weighted average
    and falls back to the simple (unweighted) mean across zones. A zone with
    zero load in a nonzero-load hour simply gets zero weight, so pure
    import/export nodes never move the ISO price.

    Args:
        prices: Zonal LMPs, shape ``(n_zones, T)`` ($/MWh) — the LP duals.
        loads: Zonal hourly load, shape ``(n_zones, T)`` (MWh).

    Returns:
        The hourly ISO price, shape ``(T,)``.
    """
    if prices.shape != loads.shape:
        raise ValueError(
            f"prices {prices.shape} and loads {loads.shape} must align (n_zones, T)"
        )
    load_sum = loads.sum(axis=0)
    weighted_sum = (prices * loads).sum(axis=0)
    simple_mean = prices.mean(axis=0)
    out = np.divide(
        weighted_sum,
        load_sum,
        out=simple_mean.astype(float).copy(),
        where=load_sum > 0,
    )
    return out


def load_zonal_demand(config: ScenarioConfig, iso: str, year: int) -> np.ndarray:
    """Reconstruct the zonal hourly load the cached dispatch was solved against.

    The dispatch result stores prices but not the demand RHS, so the weights
    are rebuilt exactly the way ``run_scenario_iso`` builds the LP's energy-
    balance RHS: weather-year zonal demand (grossed up by the T&D loss
    factor, interchange netted unless a priced import node serves it),
    trimmed to ``config.hours``, then compounded to ``year`` with the
    scenario's demand growth path. The growth factor is uniform across zones
    and hours, so it cannot change the weighted average — it is applied only
    so the sidecar's load totals describe the modeled year faithfully.

    Args:
        config: The canonicalized scenario config (see
            :func:`resolve_bau_config`).
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Target simulation year the cached result was solved for.

    Returns:
        Zonal load, shape ``(n_zones, T)``, zone axis ordered like the
        (possibly import-node-extended) ISO topology used in the solve.
    """
    # Deferred import: pulling the runner loads the full model stack, which
    # is only needed for its demand-scaling helper.
    from market_sim.runner import _scale_demand

    iso_config = get_iso_config(iso)
    # Priced import/export node (CAISO's WECC node is baked into its
    # topology; PJM's external zone is appended): when active it serves the
    # interchange, so the measured schedule stays out of demand. The border
    # carbon adder only shifts import-tranche marginal costs, never the zone
    # set, so 0.0 is fine for reconstructing demand.
    interchange_spec = get_interchange_spec(config, iso)
    import_generators = build_interchange_fleet(interchange_spec, 0.0)
    if import_generators:
        iso_config = extend_with_import_node(iso_config)

    demand = load_demand(
        iso,
        config.weather_year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not import_generators,
    )
    if config.hours < demand.shape[1]:
        demand = demand[:, : config.hours]
    return _scale_demand(demand, config, year)


def export_iso(
    config: ScenarioConfig, iso: str, year: int
) -> tuple[pd.DataFrame, dict]:
    """Build one ISO's ``(hour, iso, lmp)`` block from its cached result.

    Args:
        config: Scenario config as passed on the CLI (pre-canonicalization).
        iso: ISO identifier.
        year: Simulation year to export.

    Returns:
        ``(frame, provenance)`` — the long-form block with hours
        ``0..T-1``, and the provenance record for the sidecar JSON.

    Raises:
        FileNotFoundError: When no cached result exists for the
            (scenario, iso, year); the caller decides whether to skip.
        ValueError: When the cached price array and the reconstructed
            demand disagree on the zone set — a config/topology mismatch
            that would silently mis-weight the collapse.
    """
    iso = iso.upper()
    config = resolve_bau_config(config, iso)
    cache_key = config.cache_key()

    result = cache.load_result(iso, cache_key, year)
    prices = np.asarray(result.prices, dtype=float)  # (n_zones, T) LP duals

    loads = load_zonal_demand(config, iso, year)
    if loads.shape != prices.shape:
        raise ValueError(
            f"{iso}: cached prices have shape {prices.shape} but the "
            f"reconstructed zonal demand has shape {loads.shape}; the "
            "scenario config no longer reproduces the solve's topology "
            "(zone count or horizon drifted). Re-solve or fix the config."
        )

    lmp = collapse_zonal_prices(prices, loads)
    T = lmp.shape[0]  # T: number of hours
    frame = pd.DataFrame({"hour": np.arange(T), "iso": iso, "lmp": lmp})

    provenance = {
        "iso": iso,
        "scenario_cache_key": cache_key,
        "mode": config.mode,
        "weather_year": config.weather_year,
        "simulation_year": year,
        "source_parquet": str(cache.get_cache_path(iso, cache_key, year)),
        "hours": T,
        "collapse": "load-weighted average of zonal LMPs; zero-load hour "
        "falls back to simple mean (ADR 0011)",
        "lmp_mean": float(lmp.mean()),
        "lmp_min": float(lmp.min()),
        "lmp_max": float(lmp.max()),
        "annual_load_twh": float(loads.sum() / 1e6),
    }
    return frame, provenance


def synthetic_lmp(iso: str, year: int, T: int = 8760) -> np.ndarray:
    """Return a deterministic synthetic hourly LMP series for the stub mode.

    Seeded by ``(iso, year)`` so re-running the export reproduces the file
    byte-for-byte. The shape is qualitatively LMP-like — summer/winter
    seasonal swell, a two-peak diurnal profile with a nighttime trough, a
    midday depression (solar), mild lognormal noise, and a handful of
    summer-evening scarcity spikes — so the consumer's validation and any
    downstream plots exercise realistic structure. The *level* comes from
    the placeholder :data:`_DUMMY_BASE_LMP` table; nothing here is model
    output.

    Args:
        iso: ISO identifier (selects the base level and the seed).
        year: Year label (part of the seed only; no escalation, ADR 0011).
        T: Number of hours (default full 8760).

    Returns:
        Hourly prices, shape ``(T,)``, $/MWh.
    """
    iso = iso.upper()
    # hash() is salted per process for str; derive a stable seed from a
    # digest (a plain byte-truncation would drop the year for long names).
    digest = hashlib.sha256(f"{iso}-{year}".encode()).digest()
    seed = int.from_bytes(digest[:4], "little")
    rng = np.random.default_rng(seed)

    hod = np.arange(T) % 24  # t: hour of day
    doy = np.arange(T) // 24  # t: day of year
    base = _DUMMY_BASE_LMP.get(iso, _DUMMY_DEFAULT_BASE)

    # Seasonal swell: summer peak (~day 200) plus a smaller winter shoulder.
    seasonal = (
        1.0
        + 0.18 * np.exp(-(((doy - 200) / 45.0) ** 2))
        + 0.10 * np.exp(-(((doy - 15) / 30.0) ** 2))
        + 0.10 * np.exp(-(((doy - 350) / 30.0) ** 2))
    )
    # Diurnal: morning and evening peaks, midday solar depression, night trough.
    diurnal = (
        1.0
        + 0.12 * np.exp(-(((hod - 8) / 2.0) ** 2))
        + 0.30 * np.exp(-(((hod - 19) / 2.5) ** 2))
        - 0.15 * np.exp(-(((hod - 13) / 2.5) ** 2))
        - 0.12 * np.exp(-(((hod - 3) / 3.0) ** 2))
    )
    noise = rng.lognormal(mean=0.0, sigma=0.08, size=T)
    lmp = base * seasonal * diurnal * noise

    # A few summer-evening scarcity spikes so max-price handling is exercised.
    summer_evening = (np.abs(doy - 200) < 45) & (hod >= 17) & (hod <= 20)
    candidates = np.flatnonzero(summer_evening)
    n_spikes = min(12, candidates.size)
    if n_spikes:
        spike_hours = rng.choice(candidates, size=n_spikes, replace=False)
        lmp[spike_hours] += rng.uniform(150.0, 900.0, size=n_spikes)
    return lmp


def export_iso_dummy(iso: str, year: int, T: int = 8760) -> tuple[pd.DataFrame, dict]:
    """Build one ISO's block from the synthetic stub generator.

    Same return contract as :func:`export_iso`, with the provenance record
    loudly marked as synthetic so the file can never be mistaken for a
    market-sim forecast.
    """
    iso = iso.upper()
    lmp = synthetic_lmp(iso, year, T)
    frame = pd.DataFrame({"hour": np.arange(T), "iso": iso, "lmp": lmp})
    provenance = {
        "iso": iso,
        "source": "synthetic-dummy",
        "warning": "SYNTHETIC placeholder series — NOT market-sim output. "
        "Wiring stub until the BAU forecast is production-ready.",
        "simulation_year": year,
        "hours": T,
        "lmp_mean": float(lmp.mean()),
        "lmp_min": float(lmp.min()),
        "lmp_max": float(lmp.max()),
    }
    return frame, provenance


def write_export(
    frames: list[pd.DataFrame],
    provenances: list[dict],
    out_path: Path,
    dummy: bool = False,
) -> Path:
    """Write the combined CSV and its provenance sidecar JSON.

    The CSV carries no comment header — the consumer reads it with a plain
    ``pd.read_csv`` — so the ADR 0011 provenance record (which scenario and
    year produced the series) goes to ``<out>.provenance.json`` instead.

    Args:
        frames: One ``(hour, iso, lmp)`` block per exported ISO.
        provenances: The matching provenance records.
        out_path: Destination CSV path; parents are created.

    Returns:
        The CSV path written.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(out_path, index=False, float_format="%.4f")

    sidecar = out_path.with_suffix(out_path.suffix + ".provenance.json")
    contract = "ADR 0011 (hour, iso, lmp) BAU forecast export"
    if dummy:
        contract += " — SYNTHETIC DUMMY DATA (wiring stub, not a forecast)"
    sidecar.write_text(
        json.dumps(
            {
                "contract": contract,
                "generator": "scripts/export_lce_lmp.py",
                "isos": provenances,
            },
            indent=2,
        )
        + "\n"
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns a process exit code."""
    parser = argparse.ArgumentParser(
        description="Export BAU forecast LMPs (hour, iso, lmp) for the "
        "Scope 2 LCE Portfolio tool."
    )
    parser.add_argument(
        "--iso",
        action="append",
        required=True,
        help="ISO to export; repeat for multiple (e.g. --iso ERCOT --iso CAISO).",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=START_YEAR,
        help=f"Simulation year to export (default {START_YEAR}, the first "
        "forecast year).",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Path to a scenario YAML; defaults to the base/BAU forecast "
        "ScenarioConfig().",
    )
    parser.add_argument(
        "--allow-backcast",
        action="store_true",
        help="Permit a backcast-mode scenario (ADR 0011: validation studies "
        "only, never the portfolio default).",
    )
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Emit deterministic SYNTHETIC placeholder LMPs in the contract "
        "format (wiring stub while the BAU forecast matures); reads no "
        "cached results.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV path (default "
        "scope2-lce-portfolio/data/inputs/bau_lmp_<year>.csv, or "
        "bau_lmp_<year>_dummy.csv with --dummy).",
    )
    args = parser.parse_args(argv)

    config = (
        ScenarioConfig.from_yaml(args.scenario) if args.scenario else ScenarioConfig()
    )
    if config.mode != "forecast" and not args.allow_backcast:
        parser.error(
            f"scenario mode is {config.mode!r}; ADR 0011 couples the "
            "portfolio tool to the calibrated FORECAST run. Pass "
            "--allow-backcast only for a diagnostic validation study."
        )

    default_name = (
        f"bau_lmp_{args.year}_dummy.csv" if args.dummy else f"bau_lmp_{args.year}.csv"
    )
    out_path = Path(args.out) if args.out else _DEFAULT_OUT_DIR / default_name

    frames: list[pd.DataFrame] = []
    provenances: list[dict] = []
    missing: list[str] = []
    for iso in args.iso:
        try:
            if args.dummy:
                frame, provenance = export_iso_dummy(iso, args.year)
            else:
                frame, provenance = export_iso(config, iso, args.year)
        except FileNotFoundError as exc:
            print(f"SKIP {iso.upper()}: {exc}", file=sys.stderr)
            missing.append(iso.upper())
            continue
        frames.append(frame)
        provenances.append(provenance)
        tag = "SYNTHETIC" if args.dummy else f"key {provenance['scenario_cache_key']}"
        print(
            f"{iso.upper()}: mean ${provenance['lmp_mean']:.2f}/MWh "
            f"min ${provenance['lmp_min']:.2f} max ${provenance['lmp_max']:.2f} "
            f"({provenance['hours']} hours, {tag})"
        )

    if not frames:
        print(
            "no ISO had a cached result; solve first via "
            "market_sim.runner.run_scenario_iso (each year caches as it "
            "completes), or use --dummy for the wiring stub.",
            file=sys.stderr,
        )
        return 1

    written = write_export(frames, provenances, out_path, dummy=args.dummy)
    print(f"wrote {written} (+ provenance sidecar)")
    if missing:
        print(f"missing (not exported): {', '.join(missing)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
