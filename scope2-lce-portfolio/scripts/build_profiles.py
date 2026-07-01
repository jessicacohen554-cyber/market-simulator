#!/usr/bin/env python
"""Build per-ISO real hourly CF profiles from the market simulator's data tree.

This is the **only** place in the LCE portfolio tool that reads the market
simulator's on-disk data — and it does so *without* importing ``market_sim``
(the tool stays standalone; see ``vendored/README.md``). It reads the EIA-930
normalized generation-distribution Parquet, turns each ISO's wind/solar/offshore
distribution into an hourly capacity-factor series with the vendored shape logic
(:mod:`lce_portfolio.vendored.renewable_shapes`), and writes one long-format
Parquet per ISO-year under ``scope2-lce-portfolio/data/profiles/``::

    columns: hour (0..8759) | resource (solar_pv/onshore_wind/offshore_wind) | cf

Zonal->ISO reconciliation (ADR 0011): the EIA-930 generation-distribution the
market simulator ships is already an **ISO-wide, system-metered** series — i.e.
the capacity-weighted aggregate of every zone's plants (each zone's generation
sums into the balancing-authority total). The market simulator *distributes*
that ISO shape onto zones downstream by EIA-860 capacity share; collapsing back
with the same capacity weights (:func:`...capacity_weighted_collapse`) is the
exact inverse and returns this ISO series. So for a single-node tool the correct
per-ISO profile is the ISO-wide distribution consumed directly — the capacity-
weighted collapse is an identity here and is not re-applied. (The vendored
collapse primitive is still exercised/tested for the case where genuinely
independent per-zone shapes are supplied.)

Determinism: pure function of the input Parquet + the documented constants
below; no RNG, no wall-clock. Re-running reproduces byte-identical profiles.

Usage (run from inside ``scope2-lce-portfolio/``)::

    ../.venv/bin/python scripts/build_profiles.py --iso ERCOT
    ../.venv/bin/python scripts/build_profiles.py            # all six ISOs
    ../.venv/bin/python scripts/build_profiles.py --iso PJM --year 2023 \
        --market-sim-root ..
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# The tool package must be importable so we can reuse the vendored shape logic
# (NOT market_sim). Add ``src/`` to the path when run as a bare script.
_TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOL_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_TOOL_ROOT / "src"))

from lce_portfolio.vendored.renewable_shapes import (  # noqa: E402
    derive_cf_profile,
    derive_offshore_wind_profile,
)

# --- Vendored constants (copied from market_sim.config.constants, with the
# upstream citation kept). Re-sync alongside vendored/renewable_shapes.py. ----

# Annual-average renewable capacity factors (fraction) by ISO and technology,
# used to rescale the normalized EIA-930 distributions into CF profiles.
# Source: EIA Electric Power Monthly 2024, ERCOT CDR, CAISO annual report
# (market_sim.config.constants.RENEWABLE_AVG_CF @ commit
# 2012b2fdbb42eaafaab43931d9851445c333b123).
RENEWABLE_AVG_CF: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 0.35, "solar": 0.27},
    "CAISO": {"wind": 0.30, "solar": 0.28},
    "PJM": {"wind": 0.31, "solar": 0.19},
    "MISO": {"wind": 0.34, "solar": 0.22},
    "NYISO": {"wind": 0.26, "solar": 0.15},
    "NEISO": {"wind": 0.30, "solar": 0.15},
}

# Fixed-bottom offshore-wind annual-average CF (NREL ATB 2024). Used as the
# target mean for both the measured EIA-930 offshore distribution (where the ISO
# reports one) and the onshore-derived fallback (where it does not).
# Source: market_sim.config.constants.OFFSHORE_WIND_PARAMS["fixed_bottom"].
OFFSHORE_BASE_CF: float = 0.45

HOURS_PER_YEAR: int = 8760

# EIA-930 fuel key for each tool resource that carries a real renewable shape.
_RESOURCE_TO_EIA_FUEL: dict[str, str] = {
    "solar_pv": "solar",
    "onshore_wind": "wind",
    "offshore_wind": "offshore_wind",
}

# The six ISOs the tool supports (parquet ISO names match the tool's names).
DEFAULT_ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

_GEN_PROFILES_REL = Path("data") / "raw" / "eia-930" / "eia_generation_profiles.parquet"


def _fuel_distribution(
    profiles: pd.DataFrame, iso: str, year: int, fuel: str
) -> np.ndarray | None:
    """Return the ``(8760,)`` normalized EIA-930 distribution, or ``None``.

    ``None`` when the ``(iso, year, fuel)`` group is absent, incomplete, or sums
    to zero (a reporting gap rather than genuine zero output).
    """
    rows = profiles[
        (profiles["iso"] == iso)
        & (profiles["year"] == year)
        & (profiles["fuel"] == fuel)
    ].sort_values("hour")
    if len(rows) != HOURS_PER_YEAR:
        return None
    values = rows["value"].to_numpy(dtype=float)
    if values.sum() <= 0.0:
        return None
    return values


def build_iso_profile(
    profiles: pd.DataFrame, iso: str, year: int
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Build the long-format CF profile for one ISO-year.

    Returns a ``(hour, resource, cf)`` DataFrame plus a ``{resource: mean_cf}``
    sanity dict. Solar and onshore wind take the EIA-930 distribution rescaled
    to the ISO's annual-average CF. Offshore wind takes the ISO's measured
    offshore distribution where one is reported, else the documented fallback:
    the onshore shape smoothed + floored + rescaled to ``OFFSHORE_BASE_CF``
    (:func:`derive_offshore_wind_profile`) — flagged in the emitted metadata.

    Raises:
        ValueError: if the ISO has no wind and no solar distribution for the
            year (nothing to build).
    """
    avg_cf = RENEWABLE_AVG_CF.get(iso, {})
    records: list[pd.DataFrame] = []
    means: dict[str, float] = {}
    offshore_source: dict[str, str] = {}

    onshore_cf: np.ndarray | None = None
    for resource, fuel in _RESOURCE_TO_EIA_FUEL.items():
        if resource == "offshore_wind":
            continue  # handled after onshore so the fallback can reuse it
        dist = _fuel_distribution(profiles, iso, year, fuel)
        if dist is None:
            continue
        target = avg_cf.get(fuel)
        if target is None:
            continue
        cf = derive_cf_profile(dist, target, HOURS_PER_YEAR)
        if resource == "onshore_wind":
            onshore_cf = cf
        records.append(
            pd.DataFrame(
                {"hour": np.arange(HOURS_PER_YEAR), "resource": resource, "cf": cf}
            )
        )
        means[resource] = float(cf.mean())

    # Offshore wind: prefer the ISO's measured offshore distribution.
    offshore_dist = _fuel_distribution(profiles, iso, year, "offshore_wind")
    offshore_cf: np.ndarray | None = None
    if offshore_dist is not None:
        offshore_cf = derive_cf_profile(offshore_dist, OFFSHORE_BASE_CF, HOURS_PER_YEAR)
        offshore_source["offshore_wind"] = "eia930_measured"
    elif onshore_cf is not None:
        # Documented fallback: derive from onshore (smoothed, floored, higher
        # mean). Flagged so downstream metadata records it is not measured.
        offshore_cf = derive_offshore_wind_profile(onshore_cf, OFFSHORE_BASE_CF)
        offshore_source["offshore_wind"] = "derived_from_onshore"
    if offshore_cf is not None:
        records.append(
            pd.DataFrame(
                {
                    "hour": np.arange(HOURS_PER_YEAR),
                    "resource": "offshore_wind",
                    "cf": offshore_cf,
                }
            )
        )
        means["offshore_wind"] = float(offshore_cf.mean())

    if not records:
        raise ValueError(f"{iso} {year}: no wind/solar distribution to build")

    df = pd.concat(records, ignore_index=True)
    # Provenance columns travel with every row (single-node tool metadata).
    df["iso"] = iso
    df["year"] = year
    df["offshore_source"] = df["resource"].map(offshore_source).fillna("")
    return df, means


def load_generation_profiles(market_sim_root: Path) -> pd.DataFrame:
    """Read the EIA-930 generation-distribution Parquet from the market-sim tree.

    Raises:
        FileNotFoundError: if the expected parquet is not under
            ``<market_sim_root>/data/raw/eia-930/``.
    """
    path = market_sim_root / _GEN_PROFILES_REL
    if not path.exists():
        raise FileNotFoundError(
            f"market-sim generation profiles not found at {path}; pass "
            "--market-sim-root pointing at the market-simulator repo root"
        )
    return pd.read_parquet(path)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: build and write per-ISO CF profiles, print sanity stats."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iso",
        action="append",
        help="ISO to build (repeatable); default builds all six.",
    )
    parser.add_argument(
        "--year", type=int, default=2024, help="weather/study year (default 2024)."
    )
    parser.add_argument(
        "--market-sim-root",
        type=Path,
        default=_TOOL_ROOT.parent,
        help="path to the market-simulator repo root (default ..).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=_TOOL_ROOT / "data" / "profiles",
        help="output directory for <ISO>_<year>.parquet.",
    )
    args = parser.parse_args(argv)

    isos = [i.upper() for i in (args.iso or DEFAULT_ISOS)]
    profiles = load_generation_profiles(args.market_sim_root.resolve())
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"building CF profiles for year {args.year} -> {args.out_dir}")
    print(f"{'ISO':7} {'solar_pv':>10} {'onshore':>10} {'offshore':>10}  offshore_src")
    for iso in isos:
        try:
            df, means = build_iso_profile(profiles, iso, args.year)
        except ValueError as exc:
            print(f"{iso:7} SKIP: {exc}")
            continue
        out_path = args.out_dir / f"{iso}_{args.year}.parquet"
        df.to_parquet(out_path, index=False)
        src = df.loc[df["resource"] == "offshore_wind", "offshore_source"]
        src_label = src.iloc[0] if len(src) else "-"
        print(
            f"{iso:7} {means.get('solar_pv', float('nan')):>10.3f} "
            f"{means.get('onshore_wind', float('nan')):>10.3f} "
            f"{means.get('offshore_wind', float('nan')):>10.3f}  {src_label}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
