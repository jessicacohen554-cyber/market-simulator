"""Curate the ``gtc-limits`` clean datatype: measured hourly ERCOT GTC limits.

Reads the ERCOT **NP6-86-CD "SCED Shadow Prices and Binding Transmission
Constraints"** archives from ``data/raw/iso-specific-transmission``
(``*SCEDBTCNP686*`` zips — monthly Data Portal bundles of per-SCED-interval
zips/CSVs, or loose MIS current-window files), keeps only the **Generic
Transmission Constraint** rows (empty ``FromStation`` — a GTC caps a weighted
flow sum, not one monitored element), and aggregates the ~5-minute intervals
onto the fixed non-leap 8760-hour ERCOT-local clock (Feb 29 dropped, the DST
fall-back merged by the clock-hour group-by — the convention shared with the
``ercot-hsl`` and ORDC raw series).

The output is SPARSE: a ``(gtc, hour)`` row exists only when the constraint
appeared in SCED's active set that hour, carrying the mean/min enforced limit,
the active/binding interval counts and the mean positive shadow price. Hours
without a row mean SCED was not enforcing the constraint; consumers
(``market_sim.data.gtc``) stand those in at the constraint's measured
envelope, never at the binding-hour mean.

Rule #13/#14 admissibility: a GTC limit is ERCOT's published stability
transfer limit — a reproducible physical/market input that regenerates every
year and responds to changed grid conditions. Nothing here reads the model's
outputs or the reported curtailment totals (the validation target).

Writes one Parquet per calendar year via
:func:`scripts.lib.clean_io.write_clean` (``iso="ERCOT"``, ``year=<year>``).
Idempotent; reads only ``data/raw``.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

DATATYPE = "gtc-limits"
RAW_SUBDIR = "iso-specific-transmission"
# NP6-86 archive glob — the Data Portal monthly bundles and the MIS
# current-window per-interval files both carry this product stem.
ARCHIVE_GLOB = "*SCEDBTCNP686*"

# Columns consumed from the NP6-86 CSVs (full header documented in
# data/raw/iso-specific-transmission/README.md).
_USECOLS = ["SCEDTimeStamp", "ConstraintName", "ShadowPrice", "Limit", "FromStation"]

HOURS_PER_YEAR = 8760


def _iter_csv_bytes(path: Path):
    """Yield the CSV payload bytes of every NP6-86 file under ``path``.

    Handles the three layouts the product ships in: a monthly zip of daily/
    interval zips of CSVs (Data Portal bundle), a flat zip of CSVs, or a loose
    ``.csv``. Nested zips are walked recursively; non-CSV members are skipped.
    """
    if path.suffix.lower() == ".csv":
        yield path.read_bytes()
        return

    def _walk(zf: zipfile.ZipFile):
        for name in zf.namelist():
            lower = name.lower()
            if lower.endswith(".zip"):
                try:
                    with zipfile.ZipFile(io.BytesIO(zf.read(name))) as inner:
                        yield from _walk(inner)
                except zipfile.BadZipFile:
                    continue
            elif lower.endswith(".csv"):
                yield zf.read(name)

    with zipfile.ZipFile(path) as zf:
        yield from _walk(zf)


def _read_gtc_rows(path: Path) -> pd.DataFrame:
    """Return every GTC row (empty ``FromStation``) in one archive file.

    Off-schema or unreadable member CSVs are skipped rather than aborting the
    archive (a few daily NP6-86 files carry a stray header); latin-1 decodes
    every byte so encoding never fails the read.
    """
    frames: list[pd.DataFrame] = []
    for payload in _iter_csv_bytes(path):
        try:
            df = pd.read_csv(io.BytesIO(payload), usecols=_USECOLS, encoding="latin-1")
        except (ValueError, UnicodeDecodeError):
            continue
        gtc = df[df["FromStation"].isna()].drop(columns=["FromStation"])
        if not gtc.empty:
            frames.append(gtc)
    if not frames:
        return pd.DataFrame(columns=[c for c in _USECOLS if c != "FromStation"])
    return pd.concat(frames, ignore_index=True)


def _to_hourly(rows: pd.DataFrame, year: int) -> pd.DataFrame:
    """Aggregate one year's GTC interval rows to the non-leap model clock.

    Groups by ``(gtc, month, day, hour)`` — merging the DST fall-back repeat
    and dropping Feb 29 — and maps each group to its 0-8759 position on the
    fixed non-leap hourly calendar.
    """
    ts = pd.to_datetime(rows["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S")
    rows = rows.assign(ts=ts)
    rows = rows[
        (rows["ts"].dt.year == year)
        & ~((rows["ts"].dt.month == 2) & (rows["ts"].dt.day == 29))
    ]
    if rows.empty:
        return pd.DataFrame()

    binding = rows["ShadowPrice"] > 0
    grouped = (
        rows.assign(
            month=rows["ts"].dt.month,
            day=rows["ts"].dt.day,
            hr=rows["ts"].dt.hour,
            shadow_pos=rows["ShadowPrice"].where(binding),
            is_binding=binding,
        )
        .groupby(["ConstraintName", "month", "day", "hr"])
        .agg(
            limit_mean_mw=("Limit", "mean"),
            limit_min_mw=("Limit", "min"),
            n_active=("ts", "nunique"),
            n_binding=("ts", lambda s: 0),  # placeholder, replaced below
            shadow_price_mean=("shadow_pos", "mean"),
        )
    )
    # n_binding needs the per-group distinct binding timestamps; a second
    # group-by keeps the main agg vectorized.
    nb = (
        rows[binding]
        .assign(month=rows["ts"].dt.month, day=rows["ts"].dt.day, hr=rows["ts"].dt.hour)
        .groupby(["ConstraintName", "month", "day", "hr"])["ts"]
        .nunique()
    )
    grouped["n_binding"] = nb.reindex(grouped.index).fillna(0).astype("int64")
    grouped = grouped.reset_index()

    # Map (month, day, hour) to the 0-8759 non-leap clock position.
    calendar = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    pos = pd.Series(
        np.arange(HOURS_PER_YEAR, dtype="int64"),
        index=pd.MultiIndex.from_arrays(
            [calendar.month, calendar.day, calendar.hour], names=["month", "day", "hr"]
        ),
    )
    key = pd.MultiIndex.from_frame(grouped[["month", "day", "hr"]])
    grouped["hour"] = pos.reindex(key).to_numpy()
    grouped["interval_start_local"] = pd.to_datetime(
        {
            "year": year,
            "month": grouped["month"],
            "day": grouped["day"],
            "hour": grouped["hr"],
        }
    )

    out = grouped.rename(columns={"ConstraintName": "gtc"})
    out["iso"] = "ERCOT"
    out["n_active"] = out["n_active"].astype("int64")
    return out[
        [
            "iso",
            "gtc",
            "hour",
            "interval_start_local",
            "limit_mean_mw",
            "limit_min_mw",
            "n_active",
            "n_binding",
            "shadow_price_mean",
        ]
    ].sort_values(["gtc", "hour"], ignore_index=True)


def curate(raw_root: Path | None = None, isos: list[str] | None = None) -> list[Path]:
    """Curate every NP6-86 archive year found under the raw root.

    ``raw_root`` overrides ``data/raw`` for tests; ``isos`` is accepted for
    orchestrator symmetry (the product is ERCOT-only — anything not including
    ERCOT is a no-op). Returns the written clean paths.
    """
    if isos is not None and "ERCOT" not in [i.upper() for i in isos]:
        return []
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    archive_dir = raw_root / RAW_SUBDIR
    archives = sorted(archive_dir.glob(ARCHIVE_GLOB))
    if not archives:
        print(
            f"no {ARCHIVE_GLOB} archives under {archive_dir} — see the "
            "DATA NEEDED note in its README.md"
        )
        return []

    rows = pd.concat([_read_gtc_rows(p) for p in archives], ignore_index=True)
    if rows.empty:
        print("archives contained no GTC (empty-FromStation) rows")
        return []
    years = (
        pd.to_datetime(rows["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S")
        .dt.year.unique()
        .tolist()
    )

    source = "; ".join(
        [f"data/raw/{RAW_SUBDIR}/{p.name}" for p in archives]
        + ["ERCOT NP6-86-CD SCED Shadow Prices and Binding Transmission Constraints"]
    )
    written: list[Path] = []
    for year in sorted(years):
        hourly = _to_hourly(rows, int(year))
        if hourly.empty:
            continue
        path = write_clean(hourly, DATATYPE, iso="ERCOT", year=int(year), source=source)
        validate_clean(path)
        written.append(path)
        n_gtc = hourly["gtc"].nunique()
        print(f"{year}: {len(hourly)} (gtc, hour) rows across {n_gtc} GTCs -> {path}")
    return written


def main() -> None:
    """CLI entry point: curate the archives under ``data/raw`` (or an override)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--raw-root", default=None, help="Override the data/raw root (for testing)."
    )
    args = ap.parse_args()
    written = curate(raw_root=args.raw_root)
    if not written:
        raise SystemExit(1)
    print(f"wrote {len(written)} clean year file(s)")


if __name__ == "__main__":
    main()
