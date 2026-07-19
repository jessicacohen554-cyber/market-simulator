"""Parse ISO-NE Morning Report CSVs into the committed operable-capacity table.

Reads the daily Morning Report CSVs fetched by
``scripts/data/fetch_neiso_morning_report.py`` (gitignored, regenerable) and
transcribes each report's Section 3 "Operable Capacity Analysis" -- plus the
prior-day peak, largest first contingency and annual-maintenance exposure -- into
one tidy row per delivery date, written as one committed CSV per calendar year

    data/raw/neiso-operable-capacity/neiso_operable_capacity_<YYYY>.csv

(the repo's per-year partition convention -- keeps each committed file small
enough for the API-only push path, which carries file content inline).

This is the NEISO analogue of ``data/raw/ercot-thermal-dam-availability.csv``
(the ERCOT measured DAM class-day availability -- itself a committed CSV): the
ISO-published, forward-reproducible generation-outage / operable-capacity series
that a NEISO backcast can use IN PLACE OF the CAMPD-derived unit-outage fallback
(``campd-unit-outages-NEISO.csv``). Every stored column is a value ISO-NE
PUBLISHES in MW -- a physical outage / operable-capacity measurement, never a
price and never an outcome fitted to a residual (CLAUDE.md rules 13/14). The
availability FRACTION the model consumes is derived downstream in
``market_sim.data.neiso_operable_capacity`` from these published figures, so the
committed table stays a faithful transcription.

**Format.** The committed artifact is a CSV (all published figures are whole MW /
whole hours, so columns are nullable integers -- compact and git-diffable). CSV,
not parquet, because the repo's API-only push path (CLAUDE.md "Git & Pushing")
commits file content as text and cannot round-trip binary; this matches the
ERCOT DAM-availability precedent, which is likewise a committed CSV. Pass
``--parquet <path>`` to additionally emit a columnar parquet locally for anyone
who wants one (not committed).

Robust to the report's format epochs: labels are matched by prefix (the "I. Peak
Load Forecast For Hour Ending19" hour suffix, the interconnection line-item set
that gained NECEC in 2025), and the planned/forced outage split -- blank before
the mid-2025 format change -- is nullable.

Usage:
    python scripts/data/build_neiso_operable_capacity.py
    python scripts/data/build_neiso_operable_capacity.py --daily-dir <dir> --out-dir <dir>
    python scripts/data/build_neiso_operable_capacity.py --parquet /tmp/neiso_oc.parquet
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "neiso-operable-capacity"
DEFAULT_DAILY_DIR = RAW_DIR / "daily"
#: Committed output directory. One CSV per calendar year
#: (``neiso_operable_capacity_<YYYY>.csv``) — the repo's per-year partition
#: convention (cf. ``eia-930``, ``campd-unit-level``). Partitioning keeps each
#: committed file small enough for the API-only push path (CLAUDE.md "Git &
#: Pushing"), which carries file content inline.
DEFAULT_OUT_DIR = RAW_DIR
FILENAME_TEMPLATE = "neiso_operable_capacity_{year}.csv"

SOURCE = (
    "ISO-NE ISO Express Morning Report, Section 3 Operable Capacity Analysis "
    "(https://www.iso-ne.com/transform/csv/morningreport)"
)

#: Section-3 (and neighbouring) line-item label PREFIX -> output column. Matched
#: as a prefix so hour-suffixed labels ("I. Peak Load Forecast For Hour
#: Ending19") and reworded tails still resolve. Order matters only in that each
#: label is tested against every prefix; the prefixes are mutually exclusive.
_FIELD_PREFIXES: tuple[tuple[str, str], ...] = (
    ("A. Capacity Supply Obligation", "cso_mw"),
    ("B. Capacity Additions EcoMax", "capacity_additions_ecomax_gt_cso_mw"),
    ("C. Generation Outages and Reductions", "gen_outages_reductions_mw"),
    ("Generation Planned Outages and Reductions", "gen_planned_outages_mw"),
    ("Generation Forced Outages and Reductions", "gen_forced_outages_mw"),
    ("D. Uncommitted Available Generation", "uncommitted_available_gen_nonfast_mw"),
    ("E. DRR Capacity", "drr_capacity_mw"),
    ("F. Uncommitted Available DRR", "uncommitted_available_drr_mw"),
    ("Net Deliveries", "net_capacity_deliveries_mw"),
    ("H. Total Available Capacity", "total_available_capacity_mw"),
    ("I. Peak Load Forecast", "peak_load_forecast_mw"),
    ("J. Total Operating Reserve Requirement", "total_operating_reserve_req_mw"),
    ("K. Capacity Required", "capacity_required_mw"),
    ("L. Surplus", "surplus_deficiency_mw"),
    ("M. Replacement Reserve Requirement", "replacement_reserve_req_mw"),
    ("N. Excess Commitment", "excess_commitment_mw"),
    ("Section 4. Largest First Contingency", "largest_first_contingency_mw"),
    ("Section 5. Annual Maintenance Schedule", "ams_peak_load_exposure_mw"),
)

#: Numeric output columns (float MW), in on-disk order after the identity cols.
_VALUE_COLUMNS: tuple[str, ...] = tuple(col for _, col in _FIELD_PREFIXES)


def _to_float(raw: str) -> float | None:
    """Parse a Morning Report MW cell to float, blank/'-'/N/A -> None."""
    s = (raw or "").strip().replace(",", "")
    if s in ("", "-", "N/A", "NA"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_report(path: Path) -> dict | None:
    """Parse one Morning Report CSV into a flat dict, or ``None`` if unusable.

    The delivery date is taken from the filename (``morning_report_YYYYMMDD``)
    and cross-checked against the report's ``Report for MM/DD/YYYY`` comment.
    Section-3 line items are matched by label prefix (see ``_FIELD_PREFIXES``);
    the prior-day peak (Section 2) is captured separately because it is a
    date/hour/MW triple rather than a labelled MW.
    """
    stem = path.stem  # morning_report_YYYYMMDD
    try:
        report_date = dt.datetime.strptime(stem.split("_")[-1], "%Y%m%d").date()
    except ValueError:
        return None

    rec: dict[str, object] = {
        "report_date": report_date,
        "iso": "NEISO",
        "prior_day_peak_date": None,
        "prior_day_peak_hour_ending": None,
        "prior_day_peak_mw": None,
    }
    for col in _VALUE_COLUMNS:
        rec[col] = None

    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        rows = list(csv.reader(fh))

    in_prior_peak = False
    got_any = False
    for row in rows:
        if not row:
            continue
        rtype = row[0].strip()
        if rtype == "H":
            # Section headers toggle the prior-day-peak capture window.
            in_prior_peak = len(row) > 1 and row[1].startswith(
                "Section 2. Prior Day Peak"
            )
            continue
        if rtype != "D" or len(row) < 2:
            continue
        label = row[1].strip()
        value = row[2].strip() if len(row) > 2 else ""

        if in_prior_peak and "/" in label:
            # "D","01/14/2024","18","16282" -> prior-day peak triple.
            try:
                rec["prior_day_peak_date"] = dt.datetime.strptime(
                    label, "%m/%d/%Y"
                ).date()
            except ValueError:
                pass
            rec["prior_day_peak_hour_ending"] = _to_float(value)
            if len(row) > 3:
                rec["prior_day_peak_mw"] = _to_float(row[3])
            in_prior_peak = False
            continue

        for prefix, col in _FIELD_PREFIXES:
            if label.startswith(prefix):
                rec[col] = _to_float(value)
                got_any = True
                break

    # A usable report must carry the two headline figures.
    if not got_any or rec["gen_outages_reductions_mw"] is None:
        return None
    rec["source"] = SOURCE
    return rec


#: Integer-valued columns (whole MW / whole hours) -> stored as nullable Int64
#: so the CSV is compact (no ".0") and NaN survives.
_INT_COLUMNS: tuple[str, ...] = (
    "prior_day_peak_hour_ending",
    "prior_day_peak_mw",
    *_VALUE_COLUMNS,
)


def build_frame(daily_dir: Path | None = None) -> pd.DataFrame:
    """Parse every daily CSV under ``daily_dir`` into a schema-shaped frame.

    Idempotent: re-reads all daily CSVs and returns them sorted by
    ``report_date``. Raises ``FileNotFoundError`` when the daily directory has no
    parseable report (run the fetch script first). Integer-valued columns are
    nullable ``Int64``; dates are ISO ``YYYY-MM-DD`` strings.
    """
    daily_dir = Path(daily_dir) if daily_dir else DEFAULT_DAILY_DIR
    if not daily_dir.exists():
        raise FileNotFoundError(
            f"{daily_dir} not found; run scripts/data/fetch_neiso_morning_report.py first"
        )
    records = []
    for path in sorted(daily_dir.glob("morning_report_*.csv")):
        rec = parse_report(path)
        if rec is not None:
            records.append(rec)
    if not records:
        raise FileNotFoundError(f"no parseable Morning Report CSVs under {daily_dir}")

    df = pd.DataFrame.from_records(records)
    # The constant iso ("NEISO") and source columns are documented in the raw
    # README rather than repeated on every row (they would triple the CSV size);
    # the datatype and provenance are carried by the directory + README, matching
    # the ERCOT ercot-thermal-dam-availability.csv precedent.
    ordered = [
        "report_date",
        "prior_day_peak_date",
        "prior_day_peak_hour_ending",
        "prior_day_peak_mw",
        *_VALUE_COLUMNS,
    ]
    df = df[ordered].copy()
    # Dates as plain ISO strings (empty for missing) — round-trips through CSV
    # without a spurious time component.
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.strftime("%Y-%m-%d")
    df["prior_day_peak_date"] = (
        pd.to_datetime(df["prior_day_peak_date"]).dt.strftime("%Y-%m-%d").fillna("")
    )
    for col in _INT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").round().astype("Int64")
    return df.sort_values("report_date").reset_index(drop=True)


def build(
    daily_dir: Path | None = None,
    out_dir: Path | None = None,
    parquet_out: Path | None = None,
) -> list[Path]:
    """Write one committed CSV per calendar year (and an optional local parquet).

    Returns the list of per-year CSV paths written, sorted by year. Each
    ``neiso_operable_capacity_<YYYY>.csv`` is the committed deliverable (text,
    git-diffable, small enough for the API-only push path); ``parquet_out``, when
    given, additionally writes a single combined parquet locally (not committed).
    """
    out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
    df = build_frame(daily_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    year = pd.to_datetime(df["report_date"]).dt.year
    written: list[Path] = []
    for yr, sub in df.groupby(year, sort=True):
        path = out_dir / FILENAME_TEMPLATE.format(year=int(yr))
        sub.to_csv(path, index=False)
        written.append(path)
        print(f"wrote {len(sub)} rows -> {path.name}")
    if parquet_out is not None:
        parquet_out = Path(parquet_out)
        parquet_out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(parquet_out, index=False)
        print(f"  also wrote combined parquet -> {parquet_out}")
    span = f"{df['report_date'].min()} .. {df['report_date'].max()}"
    print(f"total {len(df)} daily rows ({span}) across {len(written)} year file(s)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-dir", type=Path, default=None)
    parser.add_argument(
        "--out-dir", type=Path, default=None, help="committed per-year CSV directory"
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=None,
        help="also emit a single combined parquet here (local convenience)",
    )
    args = parser.parse_args(argv)
    build(args.daily_dir, args.out_dir, args.parquet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
