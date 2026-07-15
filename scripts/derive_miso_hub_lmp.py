"""Reduce the staged MISO hub LMP rows to the zonal validation parquet.

Reads the compact per-(year, market) hub stagings written by
``scripts/fetch_miso_hub_lmp.py`` (``data/raw/lmp-data/MISO/
miso_hub_lmp_<year>_<da|rt>.csv.gz`` -- verbatim LMP/MCC/MLC rows for the
eight named MISO trading hubs, hour-ending 1-24 EST) and writes the
zone-resolved successor to ``actual_lmp_hourly_MISO.parquet`` (scope decision
D6, docs/multi-iso/miso-zonal-refinement-scope.md §7):

    data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet
    columns: year, hour, hub, zone, rt, da

One row per (year, hour-of-year, hub) with the hub's RT-final and DA-ex-post
LMP. Hours are the model's CHRONOLOGICAL non-leap 8760-hour calendar: row k =
k-th real (UTC) hour after Central STANDARD-time midnight Jan 1, CST Feb 29
dropped. The EIA-930 ``MISO hourly`` extract the model's demand/renewables
live on *stamps* Central Prevailing Time (verified: 5,711 hours at UTC-5 /
3,049 at UTC-6 in 2023), but the model's calendar position is chronological
(``eia_loader._eia_hourly_frame`` sorts by UTC; the CPT stamps only select
the year's rows) — so the scoring reference must be chronological too, NOT
prevailing-indexed. (Until 2026-07-15 this script converted EST -> Central
*prevailing* and indexed the wall label, pairing every CST-month comparison
one real hour off — the all-ISO scoring-clock artifact,
docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md §1.)
The market reports are hour-ending 1-24 Eastern Standard Time **year-round**
(each daily file's header says so), i.e. UTC-5 fixed, so each hour-ending
maps to a unique CST slot by a constant -1 h — no fall-back averaging, no
spring-forward NaN. A year's last CST hour comes from the NEXT calendar
year's first EST file, so it is NaN for the newest staged year.

The system scoring reference ``actual_lmp_hourly_MISO.parquet`` (columns
``year, hour, rt, da`` — verified hour-for-hour identical to this staging's
INDIANA.HUB series under the shared indexing) is re-emitted from the same
frame, so both files always carry the same clock. Years not built are
preserved from the committed file (MERGE, never replace — rule 22).

Hub -> model-zone mapping (scope §7): MINN.HUB -> MISO-West, ILLINOIS.HUB ->
MISO-Illinois, INDIANA.HUB -> MISO-Indiana, MICHIGAN.HUB -> MISO-East,
ARKANSAS.HUB / LOUISIANA.HUB / TEXAS.HUB / MS.HUB -> MISO-South (a zone's
actual is the simple mean of its member hubs, taken downstream). MISO-Plains
(LRZ 3+5, IA/MO) has NO trading hub; the parquet carries measured hub rows
only, and consumers use the documented proxy -- the simple mean of MINN.HUB
and ILLINOIS.HUB, the two hubs bracketing the Iowa/Missouri wheel-through
corridor (see ``build_miso_lmp_reference.py``).

This file is the SCORING reference for the zonal-spread gate -- measured
market data, never model output (CLAUDE.md rule #13's admissibility test does
not even arise: it is a validation target, not a model input).

Usage:
    python scripts/derive_miso_hub_lmp.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import logging

import numpy as np
import pandas as pd

from market_sim.config.paths import CALIBRATION_DIR, RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_miso_hub_lmp")

STAGE_DIR = RAW_DIR / "lmp-data" / "MISO"
OUT = CALIBRATION_DIR / "actual_lmp_hourly_zonal_MISO.parquet"

DEFAULT_YEARS = (2023, 2024, 2025)

# Named trading hub -> model zone (scope decision D6). MISO-Plains has no hub.
HUB_TO_ZONE: dict[str, str] = {
    "MINN.HUB": "MISO-West",
    "ILLINOIS.HUB": "MISO-Illinois",
    "INDIANA.HUB": "MISO-Indiana",
    "MICHIGAN.HUB": "MISO-East",
    "ARKANSAS.HUB": "MISO-South",
    "LOUISIANA.HUB": "MISO-South",
    "TEXAS.HUB": "MISO-South",
    "MS.HUB": "MISO-South",
}

_HOURS_PER_YEAR = 8760
_HE_COLS = [f"he{h:02d}" for h in range(1, 25)]

# The reports' clock: hour-ending 1-24, Eastern Standard Time year-round
# (UTC-5 fixed; every daily file's header states it).
_EST_UTC_OFFSET_H = 5
# The model's MISO calendar clock: fixed Central STANDARD time (Etc/GMT+6 ==
# UTC-6). The model's 8760 rows are chronological from the CST Jan-1 midnight
# anchor (eia_loader._eia_hourly_frame sorts by UTC), so the validation series
# indexes the same fixed-offset clock — never the DST prevailing wall label.
_STD_TZ = "Etc/GMT+6"

# Fixed non-leap calendar: hour-of-year at which each month starts (matches
# derive_actual_lmp._MONTH_START_HOUR).
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.concatenate(([0], np.cumsum(_DAYS_IN_MONTH) * 24))[:12]


def _staged_paths(year: int, market: str) -> list:
    """Return the staged file(s) for (year, market).

    2023-2025 predate the chunk split and ship as one gzip yearly file; 2022
    onward (fetched via the Data Exchange API, ``fetch_miso_hub_lmp.py``
    module docstring) ships as ~7-day plain-CSV ``_p<NN>`` chunks so each
    fits a single ``push_files`` call. Prefer the legacy yearly file if both
    exist.
    """
    legacy = STAGE_DIR / f"miso_hub_lmp_{year}_{market}.csv.gz"
    if legacy.is_file():
        return [legacy]
    return sorted(STAGE_DIR.glob(f"miso_hub_lmp_{year}_{market}_p??.csv"))


def _market_frame(year: int, market: str) -> pd.DataFrame:
    """Return one staged (year, market) as a long ``hub, year, hour, price`` frame.

    Melts the 24 hour-ending EST columns of the LMP rows, converts each
    hour-beginning EST timestamp to fixed Central standard time (a constant
    -1 h), and places it on the chronological non-leap calendar (CST Feb 29
    dropped; blank cells become NaN). Every EST hour maps to a unique slot —
    no DST duplicates arise under fixed offsets. Rows may land in ``year - 1``
    (the first EST hour of Jan 1 belongs to the prior CST year).
    """
    paths = _staged_paths(year, market)
    if not paths:
        raise FileNotFoundError(
            f"no miso_hub_lmp_{year}_{market}(.csv.gz|_??.csv) under "
            f"{STAGE_DIR} -- stage it with scripts/fetch_miso_hub_lmp.py"
        )
    df = pd.concat((pd.read_csv(p) for p in paths), ignore_index=True)
    df = df[df["value"] == "LMP"]
    # Hour-beginning EST: date 00:00 + (HE-1); UTC = EST + 5h.
    day_utc = pd.to_datetime(df["date"]).to_numpy() + np.timedelta64(
        _EST_UTC_OFFSET_H, "h"
    )
    utc = (day_utc[:, None] + np.arange(24) * np.timedelta64(1, "h")).ravel()
    local = pd.DatetimeIndex(utc, tz="UTC").tz_convert(_STD_TZ).tz_localize(None)
    month = np.asarray(local.month)
    day = np.asarray(local.day)
    hour = _MONTH_START_HOUR[month - 1] + (day - 1) * 24 + np.asarray(local.hour)
    out = pd.DataFrame(
        {
            "hub": np.repeat(df["node"].to_numpy(), 24),
            "year": np.asarray(local.year),
            "hour": hour,
            "price": df[_HE_COLS]
            .apply(pd.to_numeric, errors="coerce")
            .to_numpy(float)
            .ravel(),
        }
    )
    # Feb 29 has no slot on the fixed non-leap calendar.
    return out[~((month == 2) & (day == 29))]


def build(years) -> pd.DataFrame:
    """Return the dense ``year, hour, hub, zone, rt, da`` frame over ``years``.

    Reads every staged year so the CST year-boundary spill (Jan 1's first EST
    hours belong to the prior local year) fills each year's final hour when
    the next year is staged; the newest year's final hour stays NaN.
    """
    hubs = sorted(HUB_TO_ZONE)
    dense_idx = pd.MultiIndex.from_product(
        [hubs, range(_HOURS_PER_YEAR)], names=["hub", "hour"]
    )
    staged_years = sorted(
        {int(p.name.split("_")[3]) for p in STAGE_DIR.glob("miso_hub_lmp_*_rt*.csv*")}
        | set(years)
    )
    long: dict[str, pd.DataFrame] = {}
    for market in ("rt", "da"):
        frames = [
            _market_frame(y, market) for y in staged_years if _staged_paths(y, market)
        ]
        # Mean is a no-op on the fixed-offset clock (every EST hour maps to a
        # unique slot); it only guards against a duplicated staged row.
        long[market] = (
            pd.concat(frames, ignore_index=True)
            .groupby(["year", "hub", "hour"])["price"]
            .mean()
        )

    parts: list[pd.DataFrame] = []
    for year in years:
        merged = pd.DataFrame(index=dense_idx)
        for market in ("rt", "da"):
            g = long[market]
            g = g.loc[year] if year in g.index.get_level_values("year") else None
            merged[market] = g.reindex(dense_idx) if g is not None else np.nan
        merged = merged.reset_index()
        merged.insert(0, "year", np.int32(year))
        parts.append(merged)
        for market in ("rt", "da"):
            n_nan = int(merged[market].isna().sum())
            if n_nan:
                log.warning("%d %s: %d NaN hub-hours", year, market, n_nan)
    out = pd.concat(parts, ignore_index=True)
    out["zone"] = out["hub"].map(HUB_TO_ZONE)
    return out[["year", "hour", "hub", "zone", "rt", "da"]]


SYSTEM_OUT = CALIBRATION_DIR / "actual_lmp_hourly_MISO.parquet"
# The committed system scoring reference's composition: the INDIANA.HUB series
# (verified hour-for-hour identical to the staged INDIANA.HUB rows under the
# shared indexing — see module docstring). Kept as the standing choice; this
# script only fixes the clock, never the composition.
SYSTEM_HUB = "INDIANA.HUB"


def write_system_parquet(df: pd.DataFrame) -> None:
    """Re-emit ``actual_lmp_hourly_MISO.parquet`` from the zonal frame.

    Takes the :data:`SYSTEM_HUB` rows of the built years and merges them
    into the committed system parquet, preserving rows for any other year
    byte-for-byte (the out-of-training holdout blocks, rule 22).
    """
    sys_df = df[df["hub"] == SYSTEM_HUB][["year", "hour", "rt", "da"]].copy()
    sys_df = sys_df.astype(
        {"year": np.int16, "hour": np.int16, "rt": np.float32, "da": np.float32}
    ).sort_values(["year", "hour"], ignore_index=True)
    if SYSTEM_OUT.exists():
        old = pd.read_parquet(SYSTEM_OUT)
        keep = old[~old["year"].isin(sys_df["year"].unique())]
        if not keep.empty:
            log.info(
                "system parquet: preserving committed rows for years %s",
                sorted(keep["year"].unique().tolist()),
            )
            sys_df = pd.concat([keep, sys_df], ignore_index=True).sort_values(
                ["year", "hour"], ignore_index=True
            )
    sys_df.to_parquet(SYSTEM_OUT, index=False)
    log.info("wrote %s (%d rows)", SYSTEM_OUT, len(sys_df))


def main() -> None:
    """CLI: build and write the zonal + system validation parquets."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    args = ap.parse_args()
    df = build(args.years)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    log.info("wrote %s (%d rows)", OUT, len(df))
    write_system_parquet(df)
    # Eyeball block: per-zone annual means (South = member-hub mean).
    zonal = df.groupby(["year", "zone"])[["rt", "da"]].mean().round(2)
    print(zonal.to_string())


if __name__ == "__main__":
    main()
