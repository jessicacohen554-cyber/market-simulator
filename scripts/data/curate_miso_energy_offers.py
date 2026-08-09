"""Curate the ``energy-offers`` clean datatype from MISO's masked offer corpus.

Reads the immutable daily zips landed by
``scripts/data/fetch_miso_energy_offers.py`` under
``data/raw/miso-energy-offers/<market>/`` and writes one clean long-format
Parquet per (market, year) to ``data/clean/energy-offers/MISO/<MARKET>/``
through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Wide -> long transform
----------------------
Each source row is one masked ``Unit Code`` x operating hour carrying up to ten
cumulative-MW/price breakpoints as parallel wide columns (``MW1``/``Price1`` ...
``MW10``/``Price10``).  This script pivots them into long form: one row per
(unit_code x hour x step index), dropping null steps.  Unit-hour attributes
(economic/emergency limits, the declaration flags, self-scheduled MW, the
curtailment offer price, storage SOC bounds) are repeated on every step row for
the same key so callers join without a second lookup.

Column mapping (source -> clean)
--------------------------------
``Region``                     -> ``region``
``Unit Code``                  -> ``unit_code``
``Date/Time Beginning (EST)``  -> ``interval_start_local`` (DA; tz-naive EST)
``Mkthour Begin (EST)``        -> ``interval_start_local`` (RT; tz-naive EST)
(EST + 5 h)                    -> ``interval_start_utc``
``Economic Max`` / ``Min``     -> ``ecomax_mw`` / ``ecomin_mw``
``Emergency Max`` / ``Min``    -> ``emergency_max_mw`` / ``emergency_min_mw``
``Economic Flag``              -> ``economic_flag``
``Emergency Flag``             -> ``emergency_flag``
``Must Run Flag``              -> ``must_run_flag``
``Unit Available Flag``        -> ``unit_available_flag``
``Self Scheduled MW``          -> ``self_scheduled_mw``
``Curtailment Offer Price``    -> ``curtailment_offer_price_usd_per_mwh``
``MWn`` / ``Pricen``           -> ``step_mw`` / ``step_price_usd_per_mwh``
``Slope``                      -> ``bid_slope_flag``
``Min/MaxEnergyStorageLevel``  -> ``min/max_energy_storage_level_mwh``

RULE 13 ``[R-MEASURED]`` -- OUTCOME COLUMNS ARE DROPPED HERE AND NOWHERE ELSE.
The source files carry dispatch awards: RT ``Cleared MW1``-``Cleared MW12`` and
DA ``MW``.  Those are outcomes (the answer class), not conduct.  They have no
column in the schema and this module never emits them, so no downstream reader
can consume them even by accident.  ``Target MW Reduction`` is dropped for the
same reason.  :data:`OUTCOME_COLS` names them explicitly and
:func:`_transform_day` asserts none survives the transform.

Timezone
--------
MISO publishes these reports on **fixed EST (UTC-5)** year-round -- the header
says ``(EST)`` and the files carry 24 rows per day across both DST transitions.
``interval_start_local`` is stored tz-naive as published; ``interval_start_utc``
is that stamp plus five hours.  No DST localisation is applied, because none is
present in the source.

Run
---
    python scripts/data/curate_miso_energy_offers.py                  # every landed day
    python scripts/data/curate_miso_energy_offers.py --years 2025 --markets rt
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import write_clean  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("curate_miso_energy_offers")

ISO = "MISO"
DATATYPE = "energy-offers"
N_STEPS = 10
#: MISO market reports are published on fixed EST (UTC-5), no DST shift.
EST_OFFSET_H = 5

#: Dispatch AWARDS present in the source and deliberately never curated
#: (rule 13 ``[R-MEASURED]``): reading these back would be pinning the answer.
OUTCOME_COLS: tuple[str, ...] = (
    "MW",
    "Target MW Reduction",
    *(f"Cleared MW{i}" for i in range(1, 13)),
)

_ATTR_RENAME: dict[str, str] = {
    "Region": "region",
    "Unit Code": "unit_code",
    "Economic Max": "ecomax_mw",
    "Economic Min": "ecomin_mw",
    "Emergency Max": "emergency_max_mw",
    "Emergency Min": "emergency_min_mw",
    "Self Scheduled MW": "self_scheduled_mw",
    "Curtailment Offer Price": "curtailment_offer_price_usd_per_mwh",
    "MinEnergyStorageLevel": "min_energy_storage_level_mwh",
    "MaxEnergyStorageLevel": "max_energy_storage_level_mwh",
}
_FLAG_RENAME: dict[str, str] = {
    "Economic Flag": "economic_flag",
    "Emergency Flag": "emergency_flag",
    "Must Run Flag": "must_run_flag",
    "Unit Available Flag": "unit_available_flag",
}
_FLOAT_COLS = (
    "ecomax_mw",
    "ecomin_mw",
    "emergency_max_mw",
    "emergency_min_mw",
    "self_scheduled_mw",
    "curtailment_offer_price_usd_per_mwh",
    "min_energy_storage_level_mwh",
    "max_energy_storage_level_mwh",
)

SCHEMA_COLS: tuple[str, ...] = (
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "market",
    "unit_code",
    "region",
    "bid_slope_flag",
    "step_idx",
    "step_mw",
    "step_price_usd_per_mwh",
    "ecomin_mw",
    "ecomax_mw",
    "emergency_min_mw",
    "emergency_max_mw",
    "economic_flag",
    "emergency_flag",
    "must_run_flag",
    "unit_available_flag",
    "self_scheduled_mw",
    "curtailment_offer_price_usd_per_mwh",
    "min_energy_storage_level_mwh",
    "max_energy_storage_level_mwh",
)


def read_day(path: Path) -> pd.DataFrame:
    """Return the single CSV member of one daily ``*_co.zip`` as a DataFrame."""
    with zipfile.ZipFile(path) as z:
        member = z.namelist()[0]
        raw = z.read(member)
    return pd.read_csv(io.BytesIO(raw), low_memory=False)


def _transform_day(df: pd.DataFrame, market: str) -> pd.DataFrame:
    """Transform one day's source frame into schema-ordered long rows.

    ``market`` is ``"DA"`` or ``"RT"``.  Outcome columns are dropped first and
    their absence asserted, so the rule-13 exclusion is enforced by the code
    rather than by convention.
    """
    df = df.drop(columns=[c for c in OUTCOME_COLS if c in df.columns])
    leaked = [c for c in OUTCOME_COLS if c in df.columns]
    assert not leaked, f"rule 13: outcome columns survived the drop: {leaked}"

    ts_col = "Date/Time Beginning (EST)" if market == "DA" else "Mkthour Begin (EST)"
    local = pd.to_datetime(df[ts_col], format="%m/%d/%Y %H:%M:%S", errors="coerce")

    attrs = pd.DataFrame(index=df.index)
    attrs["interval_start_local"] = local
    attrs["interval_start_utc"] = (
        local + pd.Timedelta(hours=EST_OFFSET_H)
    ).dt.tz_localize("UTC")
    attrs["iso"] = ISO
    attrs["market"] = market
    for src, dst in _ATTR_RENAME.items():
        attrs[dst] = df[src] if src in df.columns else np.nan
    for src, dst in _FLAG_RENAME.items():
        attrs[dst] = (
            pd.to_numeric(df[src], errors="coerce").fillna(0).astype(bool)
            if src in df.columns
            else pd.Series(False, index=df.index)
        )
    attrs["bid_slope_flag"] = (
        pd.to_numeric(df["Slope"], errors="coerce").fillna(0).astype(bool)
    )
    attrs["unit_code"] = attrs["unit_code"].astype(str)
    attrs["region"] = attrs["region"].astype(str)
    for c in _FLOAT_COLS:
        attrs[c] = pd.to_numeric(attrs[c], errors="coerce").astype(float)

    parts: list[pd.DataFrame] = []
    for i in range(1, N_STEPS + 1):
        mw_col, price_col = f"MW{i}", f"Price{i}"
        if mw_col not in df.columns or price_col not in df.columns:
            continue
        chunk = attrs.copy()
        chunk["step_idx"] = np.int64(i)
        chunk["step_mw"] = pd.to_numeric(df[mw_col], errors="coerce").values
        chunk["step_price_usd_per_mwh"] = pd.to_numeric(
            df[price_col], errors="coerce"
        ).values
        parts.append(chunk)

    long = pd.concat(parts, ignore_index=True)
    long = long.dropna(
        subset=["step_mw", "step_price_usd_per_mwh", "interval_start_utc"]
    )
    long["step_idx"] = long["step_idx"].astype(np.int64)
    return long[list(SCHEMA_COLS)]


def curate(market: str, year: int, days: list[Path]) -> Path:
    """Curate one (market, year) slice and return the written clean path."""
    frames = [_transform_day(read_day(p), market.upper()) for p in sorted(days)]
    long = pd.concat(frames, ignore_index=True)
    # Duplicate keys would silently double-count MW in any aggregation.
    key = ["iso", "market", "unit_code", "interval_start_utc", "step_idx"]
    dup = int(long.duplicated(subset=key).sum())
    if dup:
        log.warning("%s %d: dropping %d duplicate key rows", market, year, dup)
        long = long.drop_duplicates(subset=key, keep="first")
    out = write_clean(
        long,
        DATATYPE,
        iso=ISO,
        year=year,
        market=market.upper(),
        source=(
            f"MISO Market Reports YYYYMMDD_{market.lower()}_co.zip "
            f"({len(days)} operating days); awards excluded (rule 13)"
        ),
    )
    log.info("%s %d: %d days -> %d rows -> %s", market, year, len(days), len(long), out)
    return out


def main() -> None:
    """CLI entry point — curate every landed (market, year) slice."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=None)
    ap.add_argument("--markets", nargs="+", default=["da", "rt"], choices=["da", "rt"])
    args = ap.parse_args()

    for market in args.markets:
        src = paths.MISO_ENERGY_OFFERS_DIR / market
        by_year: dict[int, list[Path]] = {}
        for p in sorted(src.glob(f"*_{market}_co.zip")):
            year = int(p.name[:4])
            by_year.setdefault(year, []).append(p)
        for year, days in sorted(by_year.items()):
            if args.years and year not in args.years:
                continue
            curate(market, year, days)


if __name__ == "__main__":
    main()
