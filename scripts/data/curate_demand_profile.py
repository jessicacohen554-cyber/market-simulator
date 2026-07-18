"""Curate the ``demand-profile`` clean datatype from the legacy EIA-930 extract.

Repairs ``data/raw/eia-930/eia_demand_profiles.parquet`` (raw/ is immutable,
CLAUDE.md) at the curation seam: a per-``(iso, year)`` physical-bounds screen
flags hours whose ``raw_mw`` is non-positive or an order-of-magnitude spike,
then linear interpolation across each flagged run fills it from the nearest
valid hours. This is the sole system-total demand source
``market_sim.data.eia_loader.load_demand`` falls back to whenever an ISO has
no dedicated per-BA hourly extract for a year (every PJM year; 2021-2022 for
CAISO and MISO) — see the module docstring in
``data/dictionary/schema/demand-profile.schema.yaml`` for the full writeup and
the 2026-07-05 PJM capacity-hindcast finding that discovered the defect
(``docs/hindcast-reports/pjm-2021-2025-realized-2026-07-05.md``).

Physical-bounds screen (see :func:`screen_physical_bounds`): a real ISO/BA's
hourly system demand never departs from its own annual median by more than
~2.1x in either direction — verified empirically by sweeping every one of the
35 (iso, year) series in this raw file (7 ISOs incl. SPP x 2021-2025) outside
the flagged defects. A 5x-median ceiling and a ``<= 0`` floor are therefore
generous, unambiguous bounds that flag only genuine defects: three
9-to-10-digit spike hours (PJM 2021, SPP 2023) and a set of ``0.0`` "missing
data" sentinel hours (impossible for whole-BA demand) scattered across
CAISO/MISO/NEISO/NYISO/PJM/SPP, some in isolated hours and some in day-long
runs (several coincide with DST transition dates, suggesting a local-clock
parsing artifact in whatever legacy pipeline built this extract; others do
not, and are presumably genuine EIA-930 reporting gaps recorded as 0 rather
than NaN).

This script screens and reports on every (iso, year) series in the raw file
(all 7 ISOs it carries), but only ever repairs+writes the six ISOs the model
registers (:data:`MODEL_ISOS`) — SPP is not a modeled ISO/RTO in this repo.

The script is idempotent and reads only ``data/raw``; the clean Parquet is
overwritten on each run.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from market_sim.config.paths import EIA_930_DIR
from scripts.lib.clean_io import validate_clean, write_clean

# Legacy raw extract this script repairs (immutable; see module docstring).
_RAW_FILE = EIA_930_DIR / "eia_demand_profiles.parquet"

# Physical-bounds screen constants (see module docstring for the empirical
# derivation: every legitimate (iso, year) series in this file has
# max/median <= 2.1 and min/median >= 0.2).
MAX_MEDIAN_RATIO: float = 5.0

# ISOs this repo models (get_iso_config); the raw extract also carries SPP,
# which is screened and reported on but never written as a clean partition.
MODEL_ISOS: frozenset[str] = frozenset(
    {"ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"}
)


def screen_physical_bounds(mw: np.ndarray) -> np.ndarray:
    """Return a boolean mask of physically-impossible hours in a demand series.

    Flags any hour whose value is non-positive (system demand cannot be zero
    or negative) or more than :data:`MAX_MEDIAN_RATIO` times the series'
    median (an order-of-magnitude spike well outside any legitimate seasonal
    peak/trough — see module docstring).
    """
    mw = np.asarray(mw, dtype=float)
    if mw.size == 0:
        return np.zeros(0, dtype=bool)
    med = float(np.median(mw))
    return (mw <= 0.0) | (mw > med * MAX_MEDIAN_RATIO)


def repair_by_interpolation(mw: np.ndarray, bad: np.ndarray) -> np.ndarray:
    """Linearly interpolate flagged hours from the nearest valid neighbors.

    ``bad`` hours at either end of the series (no valid neighbor on that side)
    fall back to the nearest valid value (``limit_direction="both"``).
    """
    mw = np.asarray(mw, dtype=float).copy()
    if not bad.any():
        return mw
    masked = pd.Series(mw)
    masked[bad] = np.nan
    return masked.interpolate(method="linear", limit_direction="both").to_numpy()


def repair_series(iso: str, year: int, g: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Repair one (iso, year) group; returns the repaired frame + bad-hour count."""
    g = g.sort_values("hour").reset_index(drop=True)
    mw = g["raw_mw"].to_numpy(dtype=float)
    bad = screen_physical_bounds(mw)
    repaired_mw = repair_by_interpolation(mw, bad)
    total = repaired_mw.sum()
    out = pd.DataFrame(
        {
            "iso": iso,
            "year": int(year),
            "hour": g["hour"].to_numpy(dtype="int64"),
            "raw_mw": repaired_mw,
            "normalized": repaired_mw / total if total > 0 else np.nan,
            "repaired": bad,
        }
    )
    return out, int(bad.sum())


def curate_all() -> list:
    """Screen + repair every (iso, year) series; write clean Parquet for modeled ISOs.

    Returns the list of clean Parquet paths written. Prints a report of every
    (iso, year) series the physical-bounds screen flagged, including
    non-modeled ISOs (SPP) that are screened but not written.
    """
    if not _RAW_FILE.is_file():
        print(f"no raw demand-profiles extract at {_RAW_FILE}; nothing to curate")
        return []

    raw = pd.read_parquet(_RAW_FILE)
    written = []
    print(f"screening {_RAW_FILE} ({len(raw):,} rows)")
    for (iso, year), g in raw.groupby(["iso", "year"]):
        cleaned, n_bad = repair_series(str(iso), int(year), g)
        if n_bad:
            hours = cleaned.loc[cleaned["repaired"], "hour"].tolist()
            print(
                f"  [{'write' if iso in MODEL_ISOS else 'skip '}] {iso} {year}: "
                f"{n_bad} physically-impossible hour(s) repaired: {hours}"
            )
        if iso not in MODEL_ISOS:
            continue
        path = write_clean(
            cleaned,
            "demand-profile",
            iso=str(iso),
            year=int(year),
            source=f"data/raw/eia-930/{_RAW_FILE.name}",
            extra_provenance={"n_repaired_hours": n_bad},
        )
        validate_clean(path)
        written.append(path)
    return written


def main() -> None:
    paths_written = curate_all()
    print(
        f"\ndemand-profile curation complete: {len(paths_written)} clean file(s) written."
    )


if __name__ == "__main__":
    main()
