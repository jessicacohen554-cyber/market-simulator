#!/usr/bin/env python
"""Build per-zone NWPP wind and solar shapes from the MEASURED per-BA EIA-930 series.

NWPP is the one region in this repo whose per-zone renewable shape needs no
reanalysis model at all, and that is a direct consequence of what the region
is. MISO, SPP and ERCOT get their per-zone wind shape from MERRA-2 reanalysis
wind speed at each plant, run through a turbine power curve
(``scripts/lib/wind_shape.py``), because EIA-930 publishes their wind as ONE
BA-wide series that cannot be taken apart. NWPP is a **pool of seventeen
balancing authorities**, EIA-930 publishes ``NG: WND`` and ``NG: SUN``
separately **for every one of them**, and owner ruling N5 makes every model
zone a whole-BA group — so each zone's hourly renewable output is a plain sum
of published series. Under rule 14 ``[R-ACCURATE]`` a measured series beats a
modelled one, so this builder reads rather than simulates, and it carries none
of the reanalysis path's physics constants (no shear exponent, no power curve,
no hub height): **zero free parameters** (rules 21 ``[R-DOF]`` / 24
``[R-REGISTRY]``).

Landed 2026-09-14 by lane **NWPP-33**
(``docs/multi-iso/nwpp-addition-plan-2026-09.md`` §5 row NWPP-33; FINDING
``docs/handoffs/FINDING-nwpp-33-2026-09-14.md``).

What it writes
--------------
Two families, same schema as every sibling shape table (``hour`` + one float
column per model zone, 8760 rows, hour-sorted), so no new parsing code exists
anywhere:

* ``data/raw/nwpp-wind-shape/nwpp_<year>_wind_zone_shape.parquet`` — the exact
  filename ``renewables._wind_zone_reanalysis_shapes`` composes from
  ``paths.wind_shape_dir("NWPP")``, so ARMING it is a registry entry plus a
  membership and no new code (see "Not armed" below).
* ``data/raw/nwpp-solar-shape/nwpp_<year>_solar_zone_shape.parquet`` — the same
  table for solar. **It has no consumer yet**: the per-zone SOLAR shape path
  (``_SOLAR_ZONE_SHAPE_ISOS``) builds a clear-sky shape from EIA-860 tracking
  geometry and reads no file at all, so wiring a measured solar shape in is a
  design question this lane routes rather than answers.

The construction, stated so it can be checked
---------------------------------------------
For each zone ``z``, fuel ``f`` and year ``y``::

    shape_z(t) = max(0, Σ_{BA ∈ z} NG:<f>_BA(t)) / cap_z(December, y)

1. **The members arrive pre-joined on the pool clock.**
   ``eia930.frames._pool_member_frames`` re-indexes every member's extract onto
   the ``_POOL_CLOCK_BA`` (BPAT) Pacific local year by a pure UTC join, so the
   three Mountain members (NWMT, PACE, WAUW) land on the Pacific hour that is
   the same physical hour, and row ``k`` here is the same positional hour ``k``
   the system demand, the zonal shares and the dispatch clock use. UTC is the
   canonical key and local time is provenance only (card N6, gate G19).
2. **Generation is grouped on the RULED zone map** (``_NWPP_BA_ZONES``). The two
   generation-only balancing authorities carry real renewable output and it
   lands with their BA: **AVRN** (5.3 TWh of wind in 2024, a third of NWPP-NW's
   total) in NWPP-NW and **GRID** (2.2 TWh) in NWPP-OR. A member that does not
   report a fuel column at all contributes nothing.
3. **The denominator is the same one the consumer weights by** — each zone's
   EIA-860 December operable capacity from
   ``renewables._eia860_monthly_capacity``, which assigns plants to zones through
   the SAME ``_NWPP_BA_ZONES`` key. Numerator and denominator are therefore
   attributed on one key, so the implied capacity factor is internally
   consistent; it is not a generation series divided by a differently-sourced
   capacity. Measured 2023-2025 it lands at wind 0.22-0.40 and solar 0.07-0.29
   by zone — physical values, not a normalisation artifact.
4. **Negative hours are clipped to zero and nothing else is done to them.**
   EIA-930 posts small negative wind/solar hours (station service netting); the
   largest effect is NWPP-NW solar at 0.56 % of that zone-year's positive
   energy and every other cell is ≤ 0.17 %. A negative capacity factor is not
   physical and ``renewables`` clips identically at read time, so clipping here
   keeps the committed artifact and the applied shape the same object. Nothing
   is padded, interpolated or rescaled (rule 13 ``[R-MEASURED]``).

Why the region needs this at all (measured, and it is not marginal)
-------------------------------------------------------------------
Night(00-06)/afternoon(12-18) WIND ratio by zone, 2023/2024/2025::

    NWPP-OR      1.26 / 1.26 / 1.32   <- nocturnal
    NWPP-INLAND  1.07 / 1.10 / 1.08
    NWPP-NW      0.89 / 0.82 / 0.82
    NWPP-EAST    0.82 / 0.86 / 0.85
    NWPP-SNV     0.55 / 0.59 / 0.57   <- afternoon

A **2.3x spread**, stable in sign and rank across all three years. For scale,
the contrast that justified SPP's own per-zone wind shape was 1.04 vs 0.97 — a
7 % difference. One footprint-wide profile applied to all five NWPP zones holds
wind in the wrong zone at the wrong hour by a far larger margin than the two
ISOs that already arm this mechanism.

Solar is the same story in a different statistic: the energy-weighted mean
hour-of-day of solar output on the pool's Pacific clock runs **11.81 (NW) ->
11.30 (OR) -> 11.21 (SNV) -> 11.05 (INLAND) -> 10.81 (EAST)** in 2023 and
reproduces to +/- 0.07 h in 2024 and 2025 — a one-hour west-to-east progression
in exactly the geographic order, which is what a footprint spanning ~11 degrees
of longitude and two timezones must produce.

Not armed, and that is deliberate
---------------------------------
This lane lands DATA. Nothing reads these files yet: ``WIND_SHAPE_DIRS`` carries
no ``NWPP`` entry and ``_WIND_ZONE_SHAPE_ISOS`` no ``NWPP`` membership, both of
which live under ``src/`` and are outside this lane's boundary. So no ``cache_key``
moves, no existing keeper is touched, and no ``ScenarioConfig`` field is added
(plan §7 gate G8). Arming is routed to NWPP-DESK — see the FINDING §5.

Usage::

    python scripts/data/build_nwpp_vre_shape.py                      # 2023-2025, both fuels
    python scripts/data/build_nwpp_vre_shape.py --year 2024 --fuel wind
    python scripts/data/build_nwpp_vre_shape.py --dry-run            # report only
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia930.frames import _pool_member_frames
from market_sim.data.renewables import _eia860_monthly_capacity
from market_sim.data.zone_assignment import _NWPP_BA_ZONES

logger = logging.getLogger(__name__)

ISO = "NWPP"

# Model fuel -> (EIA-930 pool-frame column, output directory, filename stem).
# The wind directory and stem match what ``renewables._wind_zone_reanalysis_shapes``
# composes from ``paths.wind_shape_dir(iso)``; the solar pair mirrors it so a
# future consumer needs no new naming rule.
FUELS: dict[str, tuple[str, Path, str]] = {
    "wind": ("NG: WND", RAW_DATA_DIR / "nwpp-wind-shape", "wind_zone_shape"),
    "solar": ("NG: SUN", RAW_DATA_DIR / "nwpp-solar-shape", "solar_zone_shape"),
}

HOUR_COLUMN = "hour"
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)


def zone_generation(year: int, column: str, zone_names: list[str]) -> np.ndarray | None:
    """Return ``(n_zones, 8760)`` MW of one EIA-930 fuel, grouped onto model zones.

    Sums each balancing authority's published hourly series into its ruled zone
    (``_NWPP_BA_ZONES``) on the pool clock. A member that does not carry the
    column, or carries it all-null, contributes zero. NaN hours become 0.0 MW —
    no interpolation, since an unreported renewable hour is not a load hour and
    the downstream reconciliation preserves the measured footprint total anyway.

    Args:
        year: Calendar year.
        column: Pool-frame fuel column, e.g. ``"NG: WND"``.
        zone_names: Ordered model-zone names.

    Returns:
        A ``(n_zones, HOURS_PER_YEAR)`` MW array, or ``None`` when the pool's
        member frames for ``year`` are unavailable.
    """
    members = _pool_member_frames(ISO, year)
    if members is None:
        logger.warning("%s pool member frames unavailable for %d", ISO, year)
        return None
    index = {zone: i for i, zone in enumerate(zone_names)}
    out = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    for ba, frame in members.items():
        if column not in frame.columns:
            continue
        zone = _NWPP_BA_ZONES.get(ba)
        if zone is None or zone not in index:
            logger.warning("%s member %s maps outside %s", ISO, ba, zone_names)
            return None
        out[index[zone]] += np.nan_to_num(
            frame[column].to_numpy(dtype=float), nan=0.0, posinf=0.0, neginf=0.0
        )
    return out


def zone_shape(year: int, fuel: str, zone_names: list[str]) -> pd.DataFrame | None:
    """Build one year's per-zone hourly capacity-factor table for ``fuel``.

    Args:
        year: Calendar year.
        fuel: ``"wind"`` or ``"solar"``.
        zone_names: Ordered model-zone names.

    Returns:
        A DataFrame with ``hour`` plus one column per zone, or ``None`` when the
        EIA-930 members or the EIA-860 capacity for ``year`` are unavailable.
    """
    column, _, _ = FUELS[fuel]
    generation = zone_generation(year, column, zone_names)
    if generation is None:
        return None
    monthly = _eia860_monthly_capacity(ISO, fuel, zone_names, year)
    if monthly is None:
        logger.warning("%s EIA-860 %s capacity unavailable for %d", ISO, fuel, year)
        return None
    december = monthly[:, -1]
    clipped = np.clip(generation, 0.0, None)
    with np.errstate(divide="ignore", invalid="ignore"):
        shape = np.where(december[:, None] > 0.0, clipped / december[:, None], 0.0)
    frame = pd.DataFrame({HOUR_COLUMN: np.arange(HOURS_PER_YEAR, dtype="int64")})
    for i, zone in enumerate(zone_names):
        frame[zone] = shape[i].astype("float64")
    _report(year, fuel, zone_names, generation, clipped, december, shape)
    return frame


def _report(
    year: int,
    fuel: str,
    zone_names: list[str],
    generation: np.ndarray,
    clipped: np.ndarray,
    december: np.ndarray,
    shape: np.ndarray,
) -> None:
    """Print the per-zone level and diurnal signature the FINDING quotes.

    Every number here is measured off the arrays just built, so the log line is
    directly checkable against the committed parquet without a re-run.
    """
    hour_of_day = np.arange(HOURS_PER_YEAR) % 24
    night = (hour_of_day >= 0) & (hour_of_day < 6)
    afternoon = (hour_of_day >= 12) & (hour_of_day < 18)
    print(f"\n=== {ISO} {year} per-zone {fuel} shape ===")
    for i, zone in enumerate(zone_names):
        positive = clipped[i].sum()
        negative = -generation[i][generation[i] < 0.0].sum()
        night_mean, afternoon_mean = shape[i][night].mean(), shape[i][afternoon].mean()
        ratio = night_mean / afternoon_mean if afternoon_mean > 0.0 else float("nan")
        print(
            f"  {zone:12s} cap={december[i]:9.1f} MW  energy={positive / 1e6:7.3f} TWh"
            f"  CF={shape[i].mean():.4f}  night/aft={ratio:5.2f}"
            f"  clipped={int((generation[i] < 0.0).sum()):5d} h"
            f" ({negative / positive * 100 if positive > 0 else 0.0:.2f} % of energy)"
        )


def build(years: tuple[int, ...], fuels: tuple[str, ...], dry_run: bool) -> int:
    """Build and (unless ``dry_run``) write every requested year-fuel table.

    Args:
        years: Calendar years to build.
        fuels: Fuel keys of :data:`FUELS`.
        dry_run: When true, report without writing.

    Returns:
        Number of tables written (0 on a dry run).
    """
    zone_names = get_iso_config(ISO).zone_names
    written = 0
    for fuel in fuels:
        _, out_dir, stem = FUELS[fuel]
        for year in years:
            frame = zone_shape(year, fuel, zone_names)
            if frame is None:
                continue
            if dry_run:
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"{ISO.lower()}_{year}_{stem}.parquet"
            frame.to_parquet(path, index=False)
            print(f"  wrote {path}")
            written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--year", type=int, nargs="+", default=list(DEFAULT_YEARS))
    parser.add_argument(
        "--fuel", nargs="+", choices=sorted(FUELS), default=sorted(FUELS)
    )
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    written = build(tuple(args.year), tuple(args.fuel), args.dry_run)
    print(f"\n{ISO} VRE shape build complete: {written} file(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
