"""Parse ERCOT 60-Day DAM Disclosure "Gen Resource Data" into a tidy offer table.

ERCOT's 60-Day DAM Disclosure publishes, per QSE-submitted generation resource
and per delivery hour, a **three-part offer**:

  1. **Startup** (``Start Up Hot`` / ``Inter`` / ``Cold``, $/start) — the cost to
     bring the unit online from each thermal state.
  2. **Min Gen Cost** ($/MWh at LSL) — the all-in price of the minimum-stable-load
     floor the unit holds once committed.
  3. A **10-point energy offer curve** (``QSE submitted Curve-MW1..10`` /
     ``Curve-Price1..10``) — the *incremental* energy offer **above LSL**, a
     monotone non-decreasing MW->price step function, NaN-padded when the QSE
     submits fewer than 10 points.

The disclosure is one **wide** row per ``(resource, delivery date, hour ending)``
with the 10 curve points spread across 20 columns. This script reshapes it to a
**tidy long** table — one row per ``(resource, hour, curve point)`` carrying the
melted ``point / mw / price`` plus the per-resource three-part fields
(startup/min-gen), the operating envelope (HSL/LSL/awarded), the settlement point
and price, and the per-resource ancillary-service awards. That tidy form is what
``scripts/archive/analyze_dam_offer_multipliers.py`` normalizes into heat-rate-multiplier
space to ground the model's thermal offer-curve bands against the real ERCOT
offer distribution.

Resource Type -> model class map (verified ERCOT codes):

  CCGT90, CCLE90        -> CC          (CC_REGULAR / CC_CHP; CHP split needs the
                                        EIA crosswalk, deferred — see --help)
  SCGT90, SCLE90        -> CT_PEAKER
  GSREH, GSNONR, GSSUP  -> ST_GAS      (reheat / non-reheat / supercritical steam)
  CLLIG                 -> COAL        (lignite)
  DSL                   -> OIL         (diesel/oil peakers)
  WIND, PVGR, PWRSTR,
  HYDRO, NUC, RENEW     -> (non-thermal, skipped for offer-curve work)

By default only the thermal classes are kept (the offer-curve target). All
resource statuses are retained with a ``committed`` boolean derived from the
status code, because the QSE-submitted curve is the offer **regardless of award**
— a peaker offers its full curve even on hours it clears OFF, and that offer
distribution is exactly what we want to characterize. Downstream analysis filters
on ``committed`` where committed-band economics specifically want online units.

Outputs (under ``data/raw/_processed-legacy/`` by default):

  * ``ercot_dam_offers.parquet`` — the tidy long offer table.
  * ``ercot_resource_settlement_crosswalk.csv`` — the unique
    ``resource_name -> settlement_point`` table (+ class, observed HSL/LSL), the
    bonus deliverable that also seeds the nodal-pocket resource->pocket mapping
    and is the join key for the (still-missing) resource->EIA-plant crosswalk.

Usage::

    python scripts/data/parse_ercot_dam_offers.py                 # all Gen Resource files
    python scripts/data/parse_ercot_dam_offers.py --glob '*2024*' # one year
    python scripts/data/parse_ercot_dam_offers.py --all-classes   # keep non-thermal too
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Resource Type -> model class. Only the thermal classes are offer-curve
# targets; the rest are skipped unless --all-classes is passed.
# ---------------------------------------------------------------------------
RESOURCE_TYPE_TO_CLASS: dict[str, str] = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSNONR": "ST_GAS",
    "GSSUP": "ST_GAS",
    "CLLIG": "COAL",
    "DSL": "OIL",
}
THERMAL_CLASSES = {"CC", "CT_PEAKER", "ST_GAS", "COAL", "OIL"}

# Statuses that mean the unit is online / committed in the DAM (dispatching),
# as opposed to OFF/OUT (offer submitted but not awarded). Used only to tag the
# ``committed`` boolean — every offering row is kept either way.
ONLINE_STATUSES = {"ON", "ONOS", "ONRR", "ONTEST", "ONEMR", "ONREG", "EMR", "EMRSWGR"}

N_CURVE_POINTS = 10

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "src"))
from market_sim.config import paths  # noqa: E402

# W1 data reorg: inputs/raw-data -> data/raw, inputs/processed ->
# data/raw/_processed-legacy, resolved through config/paths.py.
DEFAULT_INPUT_DIR = paths.RAW_DIR / "ercot"
DEFAULT_OUTPUT_DIR = paths.PROCESSED_DIR
DEFAULT_GLOB = "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"

# Columns carried straight through from the wide row onto every tidy point row.
_CARRY_COLUMNS = {
    "Delivery Date": "delivery_date",
    "Hour Ending": "hour_ending",
    "QSE": "qse",
    "Resource Name": "resource_name",
    "Resource Type": "resource_type",
    "Resource Status": "resource_status",
    "Settlement Point Name": "settlement_point",
    "HSL": "hsl",
    "LSL": "lsl",
    "Awarded Quantity": "awarded_qty",
    "Min Gen Cost": "min_gen_cost",
    "Start Up Hot": "startup_hot",
    "Start Up Inter": "startup_inter",
    "Start Up Cold": "startup_cold",
    "Energy Settlement Point Price": "spp",
    "RegUp Awarded": "regup_awarded",
    "RegDown Awarded": "regdown_awarded",
    "RRSPFR Awarded": "rrspfr_awarded",
    "RRSFFR Awarded": "rrsffr_awarded",
    "RRSUFR Awarded": "rrsufr_awarded",
    "ECRSSD Awarded": "ecrs_awarded",
    "NonSpin Awarded": "nonspin_awarded",
}


def _parse_one_file(path: str, keep_classes: set[str]) -> pd.DataFrame:
    """Reshape one wide disclosure parquet into tidy point-level rows."""
    df = pd.read_parquet(path)
    df["model_class"] = df["Resource Type"].map(RESOURCE_TYPE_TO_CLASS)
    df = df[df["model_class"].isin(keep_classes)].copy()
    if df.empty:
        return df

    # Drop rows that carry neither a curve nor any three-part field — pure
    # non-offering placeholder rows contribute nothing to the offer distribution.
    has_curve = df["QSE submitted Curve-MW1"].notna()
    has_three_part = df["Min Gen Cost"].notna() | df["Start Up Cold"].notna()
    df = df[has_curve | has_three_part].copy()
    if df.empty:
        return df

    # Some columns (e.g. ECRS, only launched mid-2023) are absent in earlier
    # files — fill them with NaN so the tidy schema is stable across years.
    for src in _CARRY_COLUMNS:
        if src not in df.columns:
            df[src] = pd.NA
    carry = df[list(_CARRY_COLUMNS)].rename(columns=_CARRY_COLUMNS)
    carry["model_class"] = df["model_class"].to_numpy()
    carry["delivery_date"] = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y")
    carry["committed"] = df["Resource Status"].isin(ONLINE_STATUSES)
    carry["source_file"] = os.path.basename(path)

    # Stack the 10 MW/price column pairs into long point rows.
    frames = []
    for k in range(1, N_CURVE_POINTS + 1):
        mw = df[f"QSE submitted Curve-MW{k}"]
        price = df[f"QSE submitted Curve-Price{k}"]
        point = carry.copy()
        point["point"] = k
        point["curve_mw"] = mw.to_numpy()
        point["curve_price"] = price.to_numpy()
        frames.append(point)

    tidy = pd.concat(frames, ignore_index=True)
    # Keep only points the QSE actually submitted (drop the NaN padding).
    tidy = tidy[tidy["curve_mw"].notna() & tidy["curve_price"].notna()].copy()

    # Compact dtypes so the multi-year canonical parquet stays small.
    for col in (
        "hsl",
        "lsl",
        "awarded_qty",
        "min_gen_cost",
        "startup_hot",
        "startup_inter",
        "startup_cold",
        "spp",
        "curve_mw",
        "curve_price",
        "regup_awarded",
        "regdown_awarded",
        "rrspfr_awarded",
        "rrsffr_awarded",
        "rrsufr_awarded",
        "ecrs_awarded",
        "nonspin_awarded",
    ):
        tidy[col] = pd.to_numeric(tidy[col], downcast="float")
    tidy["hour_ending"] = pd.to_numeric(tidy["hour_ending"], downcast="integer")
    tidy["point"] = tidy["point"].astype("int8")
    # String columns are left as object — parquet dictionary-encodes them on
    # write, so the multi-year file compresses just as well as categoricals
    # without the cross-file category-union headache when streaming row groups.
    _COLUMN_ORDER = [
        "delivery_date",
        "hour_ending",
        "qse",
        "resource_name",
        "resource_type",
        "model_class",
        "resource_status",
        "committed",
        "settlement_point",
        "hsl",
        "lsl",
        "awarded_qty",
        "min_gen_cost",
        "startup_hot",
        "startup_inter",
        "startup_cold",
        "spp",
        "point",
        "curve_mw",
        "curve_price",
        "regup_awarded",
        "regdown_awarded",
        "rrspfr_awarded",
        "rrsffr_awarded",
        "rrsufr_awarded",
        "ecrs_awarded",
        "nonspin_awarded",
        "source_file",
    ]
    return tidy[_COLUMN_ORDER]


def parse_to_parquet(
    paths: list[str], keep_classes: set[str], out_parquet: Path
) -> int:
    """Stream each file's tidy rows into ``out_parquet``; return total rows."""
    writer = None
    total = 0
    try:
        for p in sorted(paths):
            t = _parse_one_file(p, keep_classes)
            rows = 0 if t is None else len(t)
            print(f"  {os.path.basename(p):65s} -> {rows:>10,} tidy point rows")
            if not rows:
                continue
            table = pa.Table.from_pandas(t, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_parquet, table.schema, compression="zstd")
            writer.write_table(table)
            total += rows
    finally:
        if writer is not None:
            writer.close()
    if total == 0:
        raise SystemExit("No matching thermal offer rows found.")
    return total


def build_crosswalk(tidy: pd.DataFrame) -> pd.DataFrame:
    """Unique resource_name -> settlement_point table with observed envelope."""
    g = (
        tidy.groupby(
            ["resource_name", "model_class", "resource_type", "settlement_point"],
            observed=True,
        )
        .agg(
            n_offer_rows=("curve_mw", "size"),
            hsl_max=("hsl", "max"),
            lsl_median=("lsl", "median"),
            min_gen_cost_median=("min_gen_cost", "median"),
            startup_cold_median=("startup_cold", "median"),
            first_date=("delivery_date", "min"),
            last_date=("delivery_date", "max"),
        )
        .reset_index()
        .sort_values(["model_class", "resource_name"])
    )
    return g


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    ap.add_argument(
        "--glob", default=DEFAULT_GLOB, help="filename glob within --input-dir"
    )
    ap.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    ap.add_argument("--output-name", default="ercot_dam_offers.parquet")
    ap.add_argument(
        "--all-classes",
        action="store_true",
        help="keep non-thermal resources too (default: thermal only)",
    )
    args = ap.parse_args()

    paths = glob.glob(os.path.join(args.input_dir, args.glob))
    if not paths:
        raise SystemExit(f"No files match {args.glob} in {args.input_dir}")
    keep = set(RESOURCE_TYPE_TO_CLASS.values()) if args.all_classes else THERMAL_CLASSES

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_parquet = out_dir / args.output_name

    print(f"Parsing {len(paths)} file(s); keeping classes: {sorted(keep)}")
    total = parse_to_parquet(paths, keep, out_parquet)
    size_mb = out_parquet.stat().st_size / 1e6

    # Second pass over the written file for the crosswalk + summary (cheap; the
    # crosswalk reads only the columns it needs).
    xwalk_cols = [
        "resource_name",
        "model_class",
        "resource_type",
        "settlement_point",
        "hsl",
        "lsl",
        "min_gen_cost",
        "startup_cold",
        "curve_mw",
        "delivery_date",
    ]
    crosswalk = build_crosswalk(pd.read_parquet(out_parquet, columns=xwalk_cols))
    out_xwalk = out_dir / "ercot_resource_settlement_crosswalk.csv"
    crosswalk.to_csv(out_xwalk, index=False)

    summary = pd.read_parquet(out_parquet, columns=["model_class", "delivery_date"])
    print(f"\nWrote {out_parquet}  ({total:,} rows, {size_mb:.1f} MB)")
    print(f"Wrote {out_xwalk}  ({len(crosswalk):,} resources)")
    print("\nClass coverage (tidy point rows):")
    print(summary.groupby("model_class", observed=True).size().to_string())
    print(
        f"\nDate span: {summary['delivery_date'].min().date()} "
        f"-> {summary['delivery_date'].max().date()}"
    )


if __name__ == "__main__":
    main()
