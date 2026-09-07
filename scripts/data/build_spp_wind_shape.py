"""Build per-zone SPP wind capacity-factor profiles from MERRA-2 reanalysis wind speed.

SPP's wind fleet is the largest of any US ISO relative to its load, and it is
split almost exactly in half by the North/South seam: EIA-860 operable capacity
is 17.7 GW across 120 plants in **SPP-North** and 17.8 GW across 110 plants in
**SPP-South** (2025 vintage; the 35.5 GW total reconciles with SPP's own
published 35,934 MW of registered wind nameplate at end-2025,
``data/raw/spp-hsl/spp_wind_curtailment_annual.csv``). Those two halves sit in
*different wind regimes*: the northern High Plains (NE / KS / the Dakotas via
WAUE) and the southern Oklahoma / Texas-Panhandle fleet (OKGE / SPS / WFEC /
CSWS territory) sit at different distances from the core of the Great-Plains
nocturnal low-level jet, and they do NOT peak at the same hour.

**Measured, and worth stating because it runs the opposite way to the MISO
intuition:** the SOUTH is the nocturnal zone, not the north. The builder's own
night(00-06)/afternoon(12-18) ratios put SPP-South overnight-weighted and
SPP-North afternoon-weighted, which is what the meteorology says once you look
rather than assume: the LLJ's climatological core sits over Oklahoma / Kansas /
the Texas Panhandle, i.e. over SPP-SOUTH, and weakens northward into Nebraska
and the Dakotas. (In MISO the north/south contrast points the other way because
MISO-North *is* the upper Plains and MISO-South is the Gulf.) Applying ONE
EIA-930 SWPP-wide hourly wind profile to both zones averages the two together,
so the model holds wind in the wrong zone at the wrong hour and the
North<->South link binds at the wrong times. This script builds a distinct
hourly wind profile for each model zone.

**The construction itself is the shared rule and lives in one place:**
``scripts/lib/wind_shape.py``, which ``build_miso_wind_shape.py`` (and, through
its ``--iso ERCOT`` leg, ERCOT) imports too.
This file is the SPP wrapper — the ISO name, the clock, the GenMix
reconciliation leg and the CLI. Read that module's docstring for the method, for
R-LEVEL (each zone's series is the capacity-weighted mean over its WHOLE
operable fleet, not a six-plant subsample) and for why the level, not merely the
diurnal shape, is load-bearing in the downstream split. Per rule 21 ``[R-DOF]``
the physics constants and the power curve are shared by intent: a different
shear exponent for SPP would be an unmotivated per-ISO degree of freedom. What
is genuinely SPP's is the zone geography, the SWPP clock, and the GenMix leg.

Method (forward-admissible per CLAUDE.md rule 13 ``[R-MEASURED]`` — a
reproducible physical input that regenerates for any year and responds to
changed conditions), in brief:

  1. Assign every EIA-860 operable SPP wind plant online by the target year to
     its model zone (the same ``zone_assignment`` geography as the fleet/solar
     path).
  2. Pull MERRA-2 reanalysis 50 m wind speed (NASA POWER hourly ``WS50M``) at
     each plant for the model's UTC clock.
  3. Extrapolate to the plant's EIA-860 turbine hub height with the standard
     1/7-power-law wind-shear profile, then run the speed through a generic
     IEC-class onshore turbine power curve to get an hourly capacity factor.
  4. Capacity-weight EVERY plant's CF into one hourly series per zone, on the
     model's fixed non-leap 8760-hour clock (aligned hour-for-hour to the
     EIA-930 ``SWPP hourly`` series the dispatch reconciles against).

``market_sim.data.renewables`` reconciles these profiles to the measured
SWPP-wide series so the capacity-weighted system total and annual energy are
preserved exactly (``_redistribute_preserving_total``) — **no level is pinned to
an actual**. What each zone's level DOES set is that zone's share of the system
total, which is why R-LEVEL estimates it over the whole fleet rather than a
sample.

SPP additionally publishes its OWN delivered wind at 5-minute resolution
(``data/raw/spp-genmix/GenMix_<year>.csv``, ``Wind Market`` + ``Wind Self``),
which is a stricter reconciliation target than the EIA-930 aggregate. The
``--reconcile`` flag scores the built profile against it — hourly correlation,
the diurnal profile and the seasonal profile — and PRINTS the result without
changing a single value in the parquet. That separation is the point: the
reconciliation is a *check on the shape*, never a channel through which the
measured series could set it (rule 1 ``[R-STRUCT]`` / rule 13 ``[R-MEASURED]``).

NASA POWER is queried in UTC and mapped onto the model clock via the very
``UTC time`` column the renewable loader uses (``_eia_hourly_frame_filled`` for
BA code ``SWPP``), so the profile lines up with ``cf_profile`` hour-for-hour
with no timezone guess.

Source:
    NASA POWER (Prediction Of Worldwide Energy Resources), hourly ``WS50M``
    (50 m wind speed) from the MERRA-2 reanalysis:
    https://power.larc.nasa.gov/api/temporal/hourly/point
    EIA-860 wind operable schedule (plant locations, hub heights).
    SPP Integrated Marketplace public generation mix (reconciliation target
    only): data/raw/spp-genmix/README.md.

Run:
    python scripts/data/build_spp_wind_shape.py [--years 2023 2024 2025]
    python scripts/data/build_spp_wind_shape.py --reconcile
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR, wind_shape_dir  # noqa: E402
from scripts.lib import wind_shape  # noqa: E402

ISO = "SPP"
DEFAULT_YEARS = (2023, 2024, 2025)

# --- SPP GenMix reconciliation leg (diagnostic only) -------------------------
# SPP's public Integrated Marketplace generation mix, 5-minute, UTC-stamped
# ("GMT MKT Interval"). Delivered wind is the SUM of the market-dispatched and
# self-scheduled columns — SPP splits every fuel that way and neither half alone
# is the fleet's output.
_GENMIX_DIR: Path = RAW_DATA_DIR / "spp-genmix"
_GENMIX_TIME_COLUMN: str = "GMT MKT Interval"
_GENMIX_WIND_COLUMNS: tuple[str, str] = ("Wind Market", "Wind Self")


def load_genmix_wind_hourly(year: int, iso: str = ISO) -> np.ndarray | None:
    """Return SPP's own delivered wind (MW) on the model's 8760 clock, or ``None``.

    Reads ``data/raw/spp-genmix/GenMix_<year>.csv`` — SPP's public Integrated
    Marketplace generation mix at 5-minute resolution, UTC-stamped — sums the
    market-dispatched and self-scheduled wind columns
    (:data:`_GENMIX_WIND_COLUMNS`; neither half alone is the fleet's output),
    and averages the 5-minute intervals into the model's hourly UTC clock
    (:func:`scripts.lib.wind_shape.model_utc_index`).

    This is the RECONCILIATION TARGET ONLY. Nothing in the built parquet is
    scaled, shifted or otherwise touched by it — see :func:`reconcile_year` and
    the module docstring.

    Args:
        year: Model calibration year.
        iso: ISO whose clock indexes the result.

    Returns:
        ``(HOURS_PER_YEAR,)`` delivered wind MW, or ``None`` when the GenMix
        file or the ISO clock is unavailable.
    """
    path = _GENMIX_DIR / f"GenMix_{year}.csv"
    if not path.exists():
        return None
    utc_index = wind_shape.model_utc_index(year, iso)
    if utc_index is None:
        return None
    raw = pd.read_csv(path)
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in (_GENMIX_TIME_COLUMN, *_GENMIX_WIND_COLUMNS) if c not in raw]
    if missing:
        print(f"  GenMix {year}: missing column(s) {missing}; reconciliation skipped.")
        return None
    ts = pd.to_datetime(raw[_GENMIX_TIME_COLUMN], utc=True, errors="coerce")
    wind = sum(
        pd.to_numeric(raw[c], errors="coerce").fillna(0.0) for c in _GENMIX_WIND_COLUMNS
    )
    frame = pd.DataFrame({"ts": ts.dt.tz_localize(None), "mw": wind}).dropna(
        subset=["ts"]
    )
    # 5-minute intervals -> hourly mean, then onto the model's UTC hours.
    hourly = frame.set_index("ts")["mw"].resample("1h").mean()
    return hourly.reindex(utc_index).to_numpy(dtype=float)


def reconcile_year(
    year: int, df: pd.DataFrame, zone_names: list[str], iso: str = ISO
) -> dict[str, float] | None:
    """Score the built profile against SPP's own delivered wind, and print it.

    Builds the capacity-weighted ISO-wide series implied by the per-zone
    profiles and compares it to the GenMix delivered series
    (:func:`load_genmix_wind_hourly`) on three axes that a *shape* — as opposed
    to a level — is answerable for:

    * **hourly correlation** over all covered hours;
    * **diurnal profile correlation** (24 hour-of-day means);
    * **seasonal profile correlation** (12 monthly means).

    Both series are normalised to unit mean before comparison, so the score is
    invariant to level by construction. THAT IS THE POINT: no level is pinned
    (rule 13 ``[R-MEASURED]``), the renewable loader reconciles the system total
    downstream, and this function only reports whether the shape moves when
    SPP's own metered wind moves.

    A caveat this function states rather than hides: GenMix is *delivered*
    wind, i.e. net of the ~10%/yr SPP curtails
    (``data/raw/spp-hsl/spp_wind_curtailment_annual.csv``), while the built
    profile is an uncurtailed potential. Correlation is therefore the right
    statistic and a level ratio would not be.

    Args:
        year: Model calibration year.
        df: The per-zone wind-shape frame.
        zone_names: Ordered model-zone names.
        iso: ISO being reconciled.

    Returns:
        ``{"hourly_r": .., "diurnal_r": .., "seasonal_r": .., "hours": ..}``,
        or ``None`` when the GenMix series is unavailable.
    """
    measured = load_genmix_wind_hourly(year, iso)
    if measured is None:
        print(f"  GenMix {year}: not available; reconciliation skipped.")
        return None
    fleets = wind_shape.load_zone_wind_fleet(year, zone_names, iso)
    weights = np.array([sum(p[2] for p in fleets[z]) for z in zone_names], dtype=float)
    if weights.sum() <= 0.0:
        return None
    modelled = (df[zone_names].to_numpy(dtype=float) * weights).sum(axis=1) / (
        weights.sum()
    )
    ok = np.isfinite(measured) & np.isfinite(modelled)
    if ok.sum() < 24 or measured[ok].sum() <= 0.0:
        return None
    a = modelled[ok] / modelled[ok].mean()
    b = measured[ok] / measured[ok].mean()
    hourly_r = float(np.corrcoef(a, b)[0, 1])

    hod = (np.arange(HOURS_PER_YEAR) % 24)[ok]
    diurnal_a = np.array([a[hod == h].mean() for h in range(24)])
    diurnal_b = np.array([b[hod == h].mean() for h in range(24)])
    diurnal_r = float(np.corrcoef(diurnal_a, diurnal_b)[0, 1])

    month = _month_of_hour()[ok]
    seas_a = np.array([a[month == m].mean() for m in range(12)])
    seas_b = np.array([b[month == m].mean() for m in range(12)])
    seasonal_r = float(np.corrcoef(seas_a, seas_b)[0, 1])

    print(
        f"\n=== {iso} {year} profile vs SPP GenMix delivered wind "
        f"(no level pinned; unit-mean normalised) ==="
    )
    print(f"  hours compared      : {int(ok.sum())}")
    print(f"  hourly correlation  : {hourly_r:.4f}")
    print(f"  diurnal (24h) corr  : {diurnal_r:.4f}")
    print(f"  seasonal (12m) corr : {seasonal_r:.4f}")
    return {
        "hourly_r": hourly_r,
        "diurnal_r": diurnal_r,
        "seasonal_r": seasonal_r,
        "hours": float(ok.sum()),
    }


def _month_of_hour() -> np.ndarray:
    """Return the 0-based calendar month of each hour on the non-leap clock.

    Returns:
        ``(HOURS_PER_YEAR,)`` int array of month indices ``0..11``.
    """
    days = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    return np.repeat(np.arange(12), days * 24)


def main() -> None:
    """Build every requested year's per-zone wind-shape parquet for an ISO."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=list(DEFAULT_YEARS))
    parser.add_argument(
        "--iso",
        default=ISO,
        help="ISO to build (default SPP). Must be registered in "
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
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Also score each built profile against SPP's own GenMix delivered "
        "wind and print the result. Diagnostic only — it changes no value in "
        "the parquet.",
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
        if args.reconcile:
            reconcile_year(year, df, zone_names, iso)
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata(
            wind_shape.shape_table_metadata(iso, year)
        )
        out_file = out_dir / f"{iso.lower()}_{year}_wind_zone_shape.parquet"
        pq.write_table(table, out_file)
        print(f"Wrote {out_file} ({out_file.stat().st_size / 1024:.1f} KiB)")


if __name__ == "__main__":
    sys.exit(main())
