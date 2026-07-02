#!/usr/bin/env python
"""Export the hourly fossil-only average CO2 rate from market-sim dispatch results.

This is one of the two places in the LCE portfolio tool that read the market
simulator's on-disk outputs — and, like ``scripts/build_profiles.py``, it does
so *without* importing ``market_sim`` (the tool stays standalone; see
``vendored/README.md``). It reads a cached dispatch-result Parquet
(``results/{ISO}/{cache_key}/year_{year}.parquet``, written by
``market_sim.results.outputs.to_parquet``): the per-hour ``dispatch`` list
column plus the per-generator ``emission_rate`` carried in the
``market_sim_fleet`` schema metadata. It then computes the hourly fossil-only
average CO2 rate with the vendored logic
(:mod:`lce_portfolio.vendored.fossil_avg_rate`) and writes the ADR 0013 export
contract — mirroring the ADR 0011 LMP contract's ``(hour, iso, lmp)`` shape —
to ``scope2-lce-portfolio/data/emissions/``::

    columns: hour (0..8759) | iso | fossil_avg_co2_rate (tCO2/MWh)

The rate is *attributional* (GHG Protocol Scope 2 location-based): the average
carbon intensity of the emitting fleet each hour, assigned to unmatched grid
purchases via ``config.emissions_file``. It is NOT a marginal/non-baseload
rate (that is consequential accounting — see ADR 0013).

Determinism: pure function of the input dispatch Parquet; no RNG, no
wall-clock. Re-running reproduces byte-identical exports.

Usage (run from inside ``scope2-lce-portfolio/``)::

    ../.venv/bin/python scripts/build_fossil_avg_co2_rate.py --iso ERCOT --year 2030
    ../.venv/bin/python scripts/build_fossil_avg_co2_rate.py --iso PJM --year 2030 \
        --cache-key a1b2c3d4 --market-sim-root ..
    # or point at a dispatch parquet directly (e.g. a test fixture):
    ../.venv/bin/python scripts/build_fossil_avg_co2_rate.py --iso ERCOT --year 2030 \
        --result /path/to/year_2030.parquet
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# The tool package must be importable so we can reuse the vendored rate logic
# (NOT market_sim). Add ``src/`` to the path when run as a bare script.
_TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOL_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_TOOL_ROOT / "src"))

from lce_portfolio.vendored.fossil_avg_rate import compute_fossil_avg_rate  # noqa: E402

# Schema-metadata key market_sim.results.outputs uses for the fleet context
# (per-generator fuel_types / emission_rate / zones, aligned with the
# ``dispatch`` list column's generator axis).
_FLEET_METADATA_KEY = b"market_sim_fleet"


def read_dispatch_and_rates(result_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read ``(dispatch, emission_rates)`` from a cached dispatch-result Parquet.

    Mirrors the read side of ``market_sim.results.outputs`` without importing
    it: the ``dispatch`` column is ``list<float64>`` with one row per hour and
    one list entry per generator, and the per-generator CO2 rates live in the
    ``market_sim_fleet`` schema metadata's ``emission_rate`` list.

    Args:
        result_path: A ``year_{year}.parquet`` written by market-sim's
            ``DispatchResult.to_parquet`` with a fleet context.

    Returns:
        ``dispatch`` of shape ``(n_gen, T)`` in MWh/hour and
        ``emission_rates`` of shape ``(n_gen,)`` in tCO2/MWh.

    Raises:
        FileNotFoundError: If ``result_path`` does not exist.
        ValueError: If the file carries no fleet-context metadata, or the
            metadata's generator count disagrees with the dispatch column.
    """
    result_path = Path(result_path)
    if not result_path.exists():
        raise FileNotFoundError(f"no cached dispatch result at {result_path}")

    table = pq.read_table(result_path, columns=["dispatch"])
    raw_meta = (table.schema.metadata or {}).get(_FLEET_METADATA_KEY)
    if raw_meta is None:
        raise ValueError(
            f"{result_path} carries no {_FLEET_METADATA_KEY.decode()} metadata; "
            "was it written by market_sim.results.outputs.to_parquet with a "
            "FleetContext?"
        )
    emission_rates = np.asarray(json.loads(raw_meta)["emission_rate"], dtype=float)

    col = table.column("dispatch").combine_chunks()
    flat = col.values.to_numpy(zero_copy_only=False)
    n_gen = len(col[0])
    T = len(col)
    dispatch = flat.reshape(T, n_gen).T  # (n_gen, T)

    if emission_rates.shape != (n_gen,):
        raise ValueError(
            f"{result_path}: fleet metadata has {emission_rates.shape[0]} "
            f"emission rates but the dispatch column has {n_gen} generators"
        )
    return dispatch, emission_rates


def build_fossil_rate_frame(result_path: Path, iso: str) -> pd.DataFrame:
    """Build the ADR 0013 export frame ``(hour, iso, fossil_avg_co2_rate)``.

    Reads one cached dispatch result and applies the vendored
    :func:`compute_fossil_avg_rate` (identical to
    ``market_sim.results.emissions.compute_fossil_avg_rate``): tCO2 emitted
    by fossil generation each hour divided by fossil MWh that hour, 0.0 in
    zero-fossil hours.
    """
    dispatch, emission_rates = read_dispatch_and_rates(result_path)
    rate = compute_fossil_avg_rate(dispatch, emission_rates)
    return pd.DataFrame(
        {
            "hour": np.arange(rate.shape[0], dtype=int),
            "iso": iso,
            "fossil_avg_co2_rate": rate,
        }
    )


def locate_result(
    results_root: Path, iso: str, year: int, cache_key: str | None
) -> Path:
    """Locate ``results/{iso}/{cache_key}/year_{year}.parquet`` on disk.

    With ``cache_key`` the path is direct. Without it, every cached scenario
    for the ISO is scanned; exactly one must hold the requested year, else the
    candidates are listed and the caller must disambiguate with
    ``--cache-key``.
    """
    if cache_key:
        path = results_root / iso / cache_key / f"year_{year}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"no cached dispatch result at {path}")
        return path

    candidates = sorted((results_root / iso).glob(f"*/year_{year}.parquet"))
    if not candidates:
        raise FileNotFoundError(
            f"no cached dispatch result for {iso} {year} under {results_root / iso}; "
            "run the market simulator first or pass --result directly"
        )
    if len(candidates) > 1:
        keys = ", ".join(p.parent.name for p in candidates)
        raise ValueError(
            f"{len(candidates)} cached scenarios hold {iso} {year} "
            f"(cache keys: {keys}); disambiguate with --cache-key"
        )
    return candidates[0]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: export one ISO-year's hourly fossil-average CO2 rate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, help="ISO to export (e.g. ERCOT).")
    parser.add_argument(
        "--year", type=int, required=True, help="scenario year of the cached solve."
    )
    parser.add_argument(
        "--market-sim-root",
        type=Path,
        default=_TOOL_ROOT.parent,
        help="path to the market-simulator repo root (default ..).",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=None,
        help="market-sim results cache root (default <market-sim-root>/results).",
    )
    parser.add_argument(
        "--cache-key",
        default=None,
        help="scenario cache key under results/<ISO>/ (needed when several "
        "cached scenarios hold the year).",
    )
    parser.add_argument(
        "--result",
        type=Path,
        default=None,
        help="explicit path to a year_<year>.parquet dispatch result "
        "(bypasses the results-root lookup; useful for fixtures).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_TOOL_ROOT / "data" / "emissions",
        help="output directory for <ISO>_<year>_fossil_avg_co2_rate.parquet.",
    )
    args = parser.parse_args(argv)

    iso = args.iso.upper()
    results_root = args.results_root or args.market_sim_root.resolve() / "results"
    result_path = args.result or locate_result(
        results_root, iso, args.year, args.cache_key
    )

    df = build_fossil_rate_frame(result_path, iso)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{iso}_{args.year}_fossil_avg_co2_rate.parquet"
    df.to_parquet(out_path, index=False)

    rate = df["fossil_avg_co2_rate"].to_numpy()
    zero_hours = int((rate == 0.0).sum())
    print(
        f"{iso} {args.year}: wrote {out_path} "
        f"(mean {rate.mean():.4f} tCO2/MWh, min {rate.min():.4f}, "
        f"max {rate.max():.4f}, {zero_hours} zero-fossil hour(s)) "
        f"from {result_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
