"""Build per-zone MISO wind capacity-factor profiles from MERRA-2 reanalysis wind speed.

MISO wind capacity spans regions with materially different wind regimes: the
upper-plains **North** (MN/ND/SD/IA) is dominated by the Great-Plains nocturnal
low-level jet — a pronounced overnight wind maximum and a strong winter peak —
while the lower-Midwest **Central** (WI/MI/IL/IN/KY) and the Entergy **South**
(AR/LA/MS/E.TX) have a flatter, more afternoon-weighted regime. The model used
ONE EIA-930 MISO-wide hourly wind profile for all three zones (scaled only by
EIA-860 capacity share), which is wrong for the inter-zone shape. This script
builds a distinct hourly wind profile for each model zone.

**The construction itself is the shared rule and lives in one place:**
``scripts/lib/wind_shape.py``. This file is the MISO wrapper — the ISO name, the
default years, the CLI and the provenance below. Read that module's docstring
for the method, for R-LEVEL (each zone's series is the capacity-weighted mean
over its WHOLE operable fleet, not a six-plant subsample) and for why the level,
not merely the diurnal shape, is load-bearing in the downstream split.

Method (forward-admissible per CLAUDE.md rule 13 ``[R-MEASURED]`` — a
reproducible physical input that regenerates for any year and responds to
changed conditions), in brief:

  1. Assign every EIA-860 operable MISO wind plant online by the target year to
     its model zone (the same ``zone_assignment`` geography as the fleet/solar
     path).
  2. Pull MERRA-2 reanalysis 50 m wind speed (NASA POWER hourly ``WS50M``) at
     each plant for the model's UTC clock.
  3. Extrapolate to the plant's EIA-860 turbine hub height with the standard
     1/7-power-law wind-shear profile, then run the speed through a generic
     IEC-class onshore turbine power curve to get an hourly capacity factor.
  4. Capacity-weight EVERY plant's CF into one hourly series per zone, on the
     model's fixed non-leap 8760-hour clock (aligned hour-for-hour to the
     EIA-930 ``MISO hourly`` series the dispatch reconciles against).

``market_sim.data.renewables`` reconciles these profiles to the measured
EIA-930 MISO-wide series so the capacity-weighted system total and annual energy
are preserved exactly (see ``_redistribute_preserving_total``) — no level is
pinned to an actual. What each zone's level DOES set is that zone's share of the
system total, which is why R-LEVEL estimates it over the whole fleet rather than
a sample.

NASA POWER is queried in UTC and mapped onto the model clock via the very
``UTC time`` column the renewable loader uses (``_eia_hourly_frame_filled``),
so the profile lines up with ``cf_profile`` hour-for-hour with no timezone guess.

Source:
    NASA POWER (Prediction Of Worldwide Energy Resources), hourly ``WS50M``
    (50 m wind speed) from the MERRA-2 reanalysis:
    https://power.larc.nasa.gov/api/temporal/hourly/point
    EIA-860 wind operable schedule (plant locations, hub heights).

This script also builds ERCOT's per-zone shapes (``--iso ERCOT``); see
``data/raw/ercot-wind-shape/README.md``.

Run:
    python scripts/data/build_miso_wind_shape.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import wind_shape_dir  # noqa: E402
from scripts.lib import wind_shape  # noqa: E402

ISO = "MISO"
DEFAULT_YEARS = (2023, 2024, 2025)


def main() -> None:
    """Build every requested year's per-zone wind-shape parquet for an ISO."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    parser.add_argument(
        "--iso",
        default=ISO,
        help="ISO to build (default MISO). Must be registered in "
        "market_sim.config.paths.WIND_SHAPE_DIRS.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write the parquets here instead of the ISO's registered "
        "wind-shape directory. Use this for a throwaway build that must not "
        "touch the solve path.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Always hit NASA POWER instead of reading the reanalysis memo "
        "under data/clean/. The memo changes no value; this is for verifying "
        "that.",
    )
    args = parser.parse_args()
    iso = args.iso.upper()

    out_dir = args.out_dir or wind_shape_dir(iso)
    if out_dir is None:
        parser.error(
            f"{iso} has no wind-shape directory registered "
            f"(market_sim.config.paths.WIND_SHAPE_DIRS)"
        )
    cache_dir = None if args.no_cache else wind_shape.REANALYSIS_CACHE_DIR
    zone_names = get_iso_config(iso).zone_names
    out_dir.mkdir(parents=True, exist_ok=True)
    for year in args.years:
        print(f"\nBuilding {iso} wind shape for {year}...")
        df = wind_shape.build_year(year, zone_names, iso, cache_dir=cache_dir)
        if df is None:
            continue
        wind_shape.print_validation(year, df, zone_names, iso)
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata(
            wind_shape.shape_table_metadata(iso, year)
        )
        out_file = out_dir / f"{iso.lower()}_{year}_wind_zone_shape.parquet"
        pq.write_table(table, out_file)
        print(f"Wrote {out_file} ({out_file.stat().st_size / 1024:.1f} KiB)")


if __name__ == "__main__":
    sys.exit(main())
