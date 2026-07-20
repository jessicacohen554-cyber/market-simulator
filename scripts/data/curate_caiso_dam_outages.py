"""Consolidate the CAISO DAM daily outage reports into per-MRID windows.

Second stage of the owner-directed DAM-outage intake (caiso-104; fetch stage:
:mod:`scripts.data.fetch_caiso_dam_outages`). Each daily Curtailed and
Non-Operational Generator report is a SNAPSHOT of the outages active on its
trade date, so a multi-day outage appears in many consecutive reports —
often with an open (NaT) end until its final day. This script parses every
fetched daily xlsx and consolidates to one row per (OUTAGE MRID, RESOURCE
ID, OUTAGE TYPE, NATURE OF WORK, CURTAILMENT MW) episode:

  * ``start`` — the minimum CURTAILMENT START DATE TIME across snapshots;
  * ``end`` — the maximum CURTAILMENT END DATE TIME across snapshots; an
    episode never seen with a closed end takes its last snapshot's trade
    date end-of-day (the outage was still active on the last day it was
    reported);
  * ``days_reported`` — the number of daily snapshots carrying the row (a
    consistency check against the window length).

Output: ``data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet``
(committed; the loader-facing artifact the RESOURCE-ID -> ORIS crosswalk and
the DAM-before-CAMPD precedence consume) plus a coverage summary printed for
the intake record. No model input changes here — the loader precedence is a
separate, gated step.

Usage:
  python scripts/data/curate_caiso_dam_outages.py
"""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DAILY = REPO / "data" / "raw" / "caiso-dam-outages" / "daily"
OUT = REPO / "data" / "raw" / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"

COLS = {
    "OUTAGE MRID": "mrid",
    "RESOURCE NAME": "resource_name",
    "RESOURCE ID": "resource_id",
    "OUTAGE TYPE": "outage_type",
    "NATURE OF WORK": "nature_of_work",
    "CURTAILMENT START DATE TIME": "start",
    "CURTAILMENT END DATE TIME": "end",
    "CURTAILMENT MW": "curtailment_mw",
    "RESOURCE PMAX MW": "resource_pmax_mw",
    "NET QUALIFYING CAPACITY MW": "nqc_mw",
}


def parse_daily(path: Path) -> pd.DataFrame:
    """One daily snapshot -> normalized rows with the trade date attached."""
    df = pd.read_excel(path, sheet_name="PREV_DAY_OUTAGES", header=9)
    df = df.dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    out = df[list(COLS)].rename(columns=COLS)
    out = out.dropna(subset=["mrid", "resource_id"])
    stamp = path.stem.split("-")[-1]
    out["trade_date"] = pd.Timestamp(f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}")
    return out


def main() -> int:
    files = sorted(DAILY.glob("cnog-*.xlsx"))
    if not files:
        print(f"no daily files under {DAILY} — run the fetch first")
        return 1
    frames = []
    for i, f in enumerate(files):
        try:
            frames.append(parse_daily(f))
        except Exception as exc:
            print(f"SKIP {f.name}: {exc}")
        if (i + 1) % 100 == 0:
            print(f"... parsed {i + 1}/{len(files)}", flush=True)
    rows = pd.concat(frames, ignore_index=True)
    rows["start"] = pd.to_datetime(rows["start"], errors="coerce")
    rows["end"] = pd.to_datetime(rows["end"], errors="coerce")
    rows["mrid"] = rows["mrid"].astype("int64")
    for c in ("curtailment_mw", "resource_pmax_mw", "nqc_mw"):
        rows[c] = pd.to_numeric(rows[c], errors="coerce")

    key = ["mrid", "resource_id", "outage_type", "nature_of_work", "curtailment_mw"]
    g = rows.groupby(key, dropna=False)
    win = g.agg(
        resource_name=("resource_name", "first"),
        start=("start", "min"),
        end=("end", "max"),
        last_trade_date=("trade_date", "max"),
        first_trade_date=("trade_date", "min"),
        days_reported=("trade_date", "nunique"),
        resource_pmax_mw=("resource_pmax_mw", "max"),
        nqc_mw=("nqc_mw", "max"),
    ).reset_index()
    # An episode never reported with a closed end was still active on its
    # last snapshot day: close it at that trade date's end-of-day.
    open_end = win["end"].isna()
    win.loc[open_end, "end"] = win.loc[open_end, "last_trade_date"] + pd.Timedelta(
        hours=23, minutes=59
    )
    win = win.sort_values(["resource_id", "start", "mrid"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    win.to_parquet(OUT, index=False)

    print(
        f"\nwrote {OUT} ({len(win)} episodes from {len(rows)} snapshot rows, "
        f"{len(files)} daily files)"
    )
    print(f"resources: {win.resource_id.nunique()}")
    print("episodes by year:")
    print(win.start.dt.year.value_counts().sort_index().to_string())
    print("by outage_type:", win.outage_type.value_counts().to_dict())
    print(
        "open-ended episodes closed at last snapshot: "
        f"{int(open_end.sum())} ({open_end.mean():.1%})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
