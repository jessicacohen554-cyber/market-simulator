"""Curate the ``outages`` clean datatype: per-unit hourly availability.

``outages`` is a DERIVED datatype — nothing is downloaded for it. This script
reconciles three outage-window sources into per-``(plant, unit)`` hourly
availability rows that conform to
``data/dictionary/schema/outages.schema.yaml`` and routes every write through
:func:`scripts.lib.clean_io.write_clean` (never a hand-built path).

Sources (all under ``data/raw``)
--------------------------------
1. ``campd-unit-outages.csv`` — unit-grain windows, the committed output of
   ``scripts/data/derive_campd_unit_outages.py``. ``outage_mw`` is the unit's own
   offline capacity (``unit_capacity_mw``).
2. ``reference/tx-jan-aug23-unit-outages.csv`` — ERCOT's curated unit-outage
   list (the same window layout as #1).

The facility-summed source (``campd-outages.csv``, output of the deleted
``scripts/derive_campd_outages.py``) was removed 2026-07-17: the per-unit
detector is now the sole CAMPD outage source for every ISO, so this datatype is
unit-grain only and carries no ``unit_id="ALL"`` rows
(``results/calibration/FINDING-ercot79-phantom-outage-2026-07.md``).

We deliberately do NOT re-run the zero-gross-load detection here: those CSVs
*are* the derive scripts' output (the existing logic over
``data/raw/campd-unit-level/*``), so curation only reconciles their windows to
hourly availability rather than reimplementing the detector.

Reconciliation
--------------
Every window is expanded to hourly rows. ``outage_mw`` is the capacity offline
during the interval (the unit's MW for unit-grain rows; the plant nameplate for
facility-grain ``"ALL"`` rows). ``available_mw = nameplate - outage_mw``
(clamped at 0), where ``nameplate`` is the plant's ``nameplate_capacity_mw``
read straight from ``data/raw/reference/master-plant-registry.csv``. When two
sources cover the same ``(plant, unit, hour)`` (e.g. the ERCOT list and the
CAMPD unit derivation both flag W A Parish in 2023) the larger offline MW wins.

Timestamps
----------
EPA CAMPD / ERCOT operational data is reported in **local standard time** (no
DST) — the campd hourly grid is a tz-naive Central-Standard clock. So
``interval_start_local`` carries that naive wall-clock and
``interval_start_utc = interval_start_local + 6h`` (ERCOT = UTC-6, fixed).
Writes are partitioned by the UTC year.

Nameplate coupling
------------------
Nameplate is read from the raw registry CSV, NOT from the (not-yet-curated)
fleet clean tree, so this curation does not block on fleet curation. The
coupling is intentional and called out in the PR.

Idempotent and re-runnable; reads only ``data/raw``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

# ERCOT is the only ISO these three sources cover. CAMPD reports in local
# standard time (no DST), so Central is a fixed UTC-6 offset and the UTC stamp
# is the naive local wall-clock plus six hours.
ISO = "ERCOT"
UTC_OFFSET_HOURS = 6

# Final column order = the outages schema's columns.
SCHEMA_COLUMNS = [
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "plant_id",
    "unit_id",
    "outage_mw",
    "available_mw",
    "outage_type",
]


# ---------------------------------------------------------------------------
# Nameplate (raw registry, not the fleet clean tree)
# ---------------------------------------------------------------------------
def load_nameplate(registry_csv: Path) -> dict[int, float]:
    """Return ``plant_id -> nameplate_capacity_mw`` from the raw plant registry.

    The registry is one row per plant; rows with a missing or non-positive
    nameplate are dropped (they give no availability denominator).
    """
    reg = pd.read_csv(registry_csv, usecols=["plantid", "nameplate_capacity_mw"])
    out: dict[int, float] = {}
    for plant_id, cap in reg.itertuples(index=False):
        if pd.notna(plant_id) and pd.notna(cap) and float(cap) > 0.0:
            out[int(plant_id)] = float(cap)
    return out


# ---------------------------------------------------------------------------
# Window expansion
# ---------------------------------------------------------------------------
def _expand_daily(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Hourly naive local stamps for an inclusive daily window [start, end]."""
    lo = pd.Timestamp(start).normalize()
    hi = pd.Timestamp(end).normalize() + pd.Timedelta(hours=23)
    return pd.date_range(lo, hi, freq="h")


def load_unit_windows(csv_path: Path) -> list[pd.DataFrame]:
    """Expand a unit-grain window CSV to per-hour ``(plant, unit, offline)`` frames.

    Handles both ``campd-unit-outages.csv`` and the ERCOT curated
    ``tx-jan-aug23-unit-outages.csv`` (same layout). ``outage_mw`` is the unit's
    ``unit_capacity_mw``; when that is blank (a few ERCOT rows) it falls back to
    an equal share of the row's ``plant_capacity_mw``. Rows that still cannot be
    sized are skipped.
    """
    df = pd.read_csv(csv_path)
    parts: list[pd.DataFrame] = []
    for r in df.itertuples(index=False):
        cap = getattr(r, "unit_capacity_mw", None)
        if cap is None or pd.isna(cap) or float(cap) <= 0.0:
            plant_cap = getattr(r, "plant_capacity_mw", None)
            n_units = getattr(r, "total_units_at_plant", None)
            if (
                plant_cap is not None
                and pd.notna(plant_cap)
                and n_units is not None
                and pd.notna(n_units)
                and int(n_units) > 0
            ):
                cap = float(plant_cap) / int(n_units)
            else:
                continue
        hours = _expand_daily(pd.Timestamp(r.outage_start), pd.Timestamp(r.outage_end))
        if len(hours) == 0:
            continue
        parts.append(
            pd.DataFrame(
                {
                    "plant_id": int(r.facility_id),
                    "unit_id": str(r.unit_id),
                    "local": hours,
                    "outage_mw": float(cap),
                }
            )
        )
    return parts


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------
def reconcile(parts: list[pd.DataFrame], nameplate: dict[int, float]) -> pd.DataFrame:
    """Combine expanded window frames into the canonical outages frame.

    De-duplicates on the schema key ``(plant_id, unit_id, interval_start_utc)``
    keeping the largest ``outage_mw`` (most conservative), builds the tz-aware
    UTC stamp and the naive local stamp, and computes ``available_mw`` against
    the registry nameplate. Returns an empty (but correctly typed) frame when
    there are no windows.
    """
    if not parts:
        return _empty_frame()

    df = pd.concat(parts, ignore_index=True)
    # Largest offline MW wins when sources overlap on the same unit-hour.
    df = (
        df.sort_values("outage_mw", kind="stable")
        .drop_duplicates(["plant_id", "unit_id", "local"], keep="last")
        .reset_index(drop=True)
    )

    local = df["local"].astype("datetime64[ns]")
    out = pd.DataFrame(
        {
            "interval_start_utc": (
                local + pd.Timedelta(hours=UTC_OFFSET_HOURS)
            ).dt.tz_localize("UTC"),
            "interval_start_local": local,
            "iso": pd.array([ISO] * len(df), dtype="string"),
            "plant_id": df["plant_id"].astype("int64"),
            "unit_id": df["unit_id"].astype("string"),
            "outage_mw": df["outage_mw"].astype("float64"),
        }
    )
    nameplate_mw = out["plant_id"].map(nameplate)
    out["available_mw"] = (
        (nameplate_mw - out["outage_mw"]).clip(lower=0.0).astype("float64")
    )
    # No source classifies planned/forced/derate, so outage_type stays null.
    out["outage_type"] = pd.array([pd.NA] * len(df), dtype="string")
    return out[SCHEMA_COLUMNS]


def _empty_frame() -> pd.DataFrame:
    """An empty frame carrying the schema's columns and dtypes."""
    return pd.DataFrame(
        {
            "interval_start_utc": pd.Series([], dtype="datetime64[ns, UTC]"),
            "interval_start_local": pd.Series([], dtype="datetime64[ns]"),
            "iso": pd.array([], dtype="string"),
            "plant_id": pd.Series([], dtype="int64"),
            "unit_id": pd.array([], dtype="string"),
            "outage_mw": pd.Series([], dtype="float64"),
            "available_mw": pd.Series([], dtype="float64"),
            "outage_type": pd.array([], dtype="string"),
        }
    )[SCHEMA_COLUMNS]


# ---------------------------------------------------------------------------
# Curate entrypoint
# ---------------------------------------------------------------------------
def _rel(path: Path) -> str:
    """Repo-relative path string for provenance, falling back to the name."""
    try:
        return str(path.resolve().relative_to(paths.REPO_ROOT))
    except ValueError:
        return path.name


def curate(
    raw_dir: Path | None = None,
    reference_dir: Path | None = None,
    *,
    write: bool = True,
) -> list[Path]:
    """Reconcile the outage sources and write one clean Parquet per UTC year.

    Reads only ``data/raw``. ``raw_dir`` / ``reference_dir`` are overridable so
    tests can point at a synthetic fixture. Returns the written paths (empty
    when ``write=False`` or there are no rows).
    """
    raw_dir = Path(raw_dir) if raw_dir is not None else paths.RAW_DIR
    reference_dir = (
        Path(reference_dir) if reference_dir is not None else raw_dir / "reference"
    )

    registry_csv = reference_dir / "master-plant-registry.csv"
    nameplate = load_nameplate(registry_csv)

    parts: list[pd.DataFrame] = []
    sources: list[Path] = []

    unit_csv = raw_dir / "campd-unit-outages.csv"
    if unit_csv.is_file():
        parts += load_unit_windows(unit_csv)
        sources.append(unit_csv)

    tx_csv = reference_dir / "tx-jan-aug23-unit-outages.csv"
    if tx_csv.is_file():
        parts += load_unit_windows(tx_csv)
        sources.append(tx_csv)

    df = reconcile(parts, nameplate)

    source = "; ".join(
        [_rel(p) for p in sources]
        + [
            "data/raw/campd-unit-level/* via scripts/data/derive_campd_unit_outages.py",
            f"nameplate from {_rel(registry_csv)}",
        ]
    )

    written: list[Path] = []
    if not write or df.empty:
        return written

    for year, sub in df.groupby(df["interval_start_utc"].dt.year):
        sub = sub.reset_index(drop=True)
        path = write_clean(sub, "outages", year=int(year), source=source)
        validate_clean(path)
        written.append(path)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--raw-dir", default=None, help="Override the data/raw root (for testing)."
    )
    args = ap.parse_args()
    written = curate(raw_dir=args.raw_dir)
    if not written:
        print("no outage rows curated (no source windows found)")
        return
    total = 0
    for path in written:
        n = len(pd.read_parquet(path))
        total += n
        print(f"wrote {n:>8,} rows  ->  {path}")
    print(f"\ntotal {total:,} hourly outage rows across {len(written)} year file(s)")


if __name__ == "__main__":
    main()
