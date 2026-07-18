"""Fold raw CAISO OASIS downloads into compact hourly aggregates.

Companion to :mod:`scripts.data.fetch_caiso_oasis`. The raw OASIS window CSVs are
bulky — the 5-minute RTM LMP series alone is ~800 MB over 2023-2025 — so the
repo keeps tidy hourly aggregates instead and the raw files are staged out
(in CI they become a build artifact):

* ``data/raw/lmp-data/CAISO/CAISO_dam_hourly_{year}.csv``
  -- columns ``interval_start_gmt, node, LMP, MCC, MCE, MCL, MGHG`` (hourly
  DAM prices per trading hub, straight from PRC_LMP).
* ``data/raw/lmp-data/CAISO/CAISO_rtm_hourly_{year}.csv``
  -- same shape; the PRC_INTVL_LMP 5-minute intervals averaged per hour.
* ``data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_{year}.csv``
  -- columns ``interval_start_gmt, tac_area, mw`` for the CAISO TAC areas
  (PGE/SCE/SDGE/VEA TACs + the CA ISO-TAC system total) from SLD_FCST.

Aggregation is idempotent and incremental: existing aggregate rows are
merged with newly processed raws, de-duplicated on the (timestamp, series)
key, and rewritten sorted. Processed raw window files (the
``{dataset}_{node}_{start}_{end}.csv`` naming of the fetch script) are moved
to ``--stage-dir``; raw files with other names (e.g. hand-downloaded OASIS
zips' inner CSVs) are folded in but left in place.

Run: ``python scripts/data/postprocess_oasis_downloads.py --stage-dir /tmp/oasis-raw``
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402  (resolves the data root)

# Paths resolve through config/paths.py — the W1 relocation collapsed the legacy
# inputs/raw-data tree into data/raw.
LMP_DIR = paths.RAW_DATA_DIR / "lmp-data" / "CAISO"
LOAD_DIR = paths.RAW_DATA_DIR / "zone-specific-demand" / "CAISO"

# CAISO TAC areas kept from SLD_FCST (the report also carries the other WECC
# BAs' system loads, which we drop). VEA is Valley Electric, the small NV
# member; CA ISO-TAC is the system total used for reconciliation.
CAISO_TACS = ("CA ISO-TAC", "PGE-TAC", "SCE-TAC", "SDGE-TAC", "VEA-TAC")

# Raw window files written by fetch_caiso_oasis.py: {key}_{node}_{Ymd}_{Ymd}.csv
_FETCH_NAME = re.compile(r"^(dam|rtm|load)_.+_\d{8}_\d{8}\.csv$")


def _merge_write(
    per_year: dict[int, pd.DataFrame], out_dir: Path, stem: str, keys: list[str]
) -> None:
    """Merge new per-year frames into the existing aggregates and rewrite."""
    for year, frame in sorted(per_year.items()):
        path = out_dir / f"{stem}_{year}.csv"
        if path.exists():
            frame = pd.concat([pd.read_csv(path), frame], ignore_index=True)
        # Normalize the timestamp key: rows read back from an existing CSV
        # are strings while freshly parsed rows are tz-aware datetimes, and
        # mixed types defeat drop_duplicates (the bug that doubled the 2023
        # load aggregate in workflow run 27352329351).
        frame["interval_start_gmt"] = pd.to_datetime(
            frame["interval_start_gmt"], utc=True
        )
        frame = (
            frame.drop_duplicates(subset=keys, keep="last")
            .sort_values(keys)
            .reset_index(drop=True)
        )
        frame.to_csv(path, index=False)
        print(f"wrote {path.relative_to(REPO)} ({len(frame)} rows)")


def _lmp_frames(paths: list[Path], hourly_mean: bool) -> dict[int, pd.DataFrame]:
    """Parse raw PRC_LMP / PRC_INTVL_LMP CSVs into wide per-year frames."""
    per_year: dict[int, list[pd.DataFrame]] = {}
    for path in paths:
        df = pd.read_csv(path)
        # PRC_LMP names the price column MW; PRC_INTVL_LMP names it VALUE.
        value_col = "MW" if "MW" in df.columns else "VALUE"
        ts = pd.to_datetime(df["INTERVALSTARTTIME_GMT"], utc=True)
        df = df.assign(interval_start_gmt=ts.dt.floor("h") if hourly_mean else ts)
        wide = (
            df.pivot_table(
                index=["interval_start_gmt", "NODE"],
                columns="LMP_TYPE",
                values=value_col,
                aggfunc="mean",  # 5-min -> hourly mean; no-op for hourly DAM
            )
            .reset_index()
            .rename(columns={"NODE": "node"})
        )
        wide.columns.name = None
        # Aggregate years by the PST trade date convention (GMT-8) so a
        # year file holds exactly its own trade dates.
        year = (wide["interval_start_gmt"] - pd.Timedelta(hours=8)).dt.year
        for y, chunk in wide.groupby(year):
            per_year.setdefault(int(y), []).append(chunk)
    return {y: pd.concat(chunks, ignore_index=True) for y, chunks in per_year.items()}


def _load_frames(paths: list[Path]) -> dict[int, pd.DataFrame]:
    """Parse raw SLD_FCST CSVs into tidy per-year CAISO TAC load frames."""
    per_year: dict[int, list[pd.DataFrame]] = {}
    for path in paths:
        df = pd.read_csv(path)
        df = df[df["TAC_AREA_NAME"].isin(CAISO_TACS)]
        tidy = pd.DataFrame(
            {
                "interval_start_gmt": pd.to_datetime(
                    df["INTERVALSTARTTIME_GMT"], utc=True
                ),
                "tac_area": df["TAC_AREA_NAME"],
                "mw": pd.to_numeric(df["MW"], errors="coerce"),
            }
        )
        year = (tidy["interval_start_gmt"] - pd.Timedelta(hours=8)).dt.year
        for y, chunk in tidy.groupby(year):
            per_year.setdefault(int(y), []).append(chunk)
    return {y: pd.concat(chunks, ignore_index=True) for y, chunks in per_year.items()}


def _stage(paths: list[Path], stage_dir: Path | None) -> None:
    """Move fetch-script raw window files out of the repo tree."""
    if stage_dir is None:
        return
    stage_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if _FETCH_NAME.match(path.name):
            shutil.move(str(path), stage_dir / path.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--stage-dir",
        type=Path,
        default=None,
        help="move processed fetch-script raws here (left in place when omitted)",
    )
    args = parser.parse_args()

    dam = sorted(LMP_DIR.glob("dam_*.csv"))
    if dam:
        _merge_write(
            _lmp_frames(dam, hourly_mean=False),
            LMP_DIR,
            "CAISO_dam_hourly",
            ["interval_start_gmt", "node"],
        )
        _stage(dam, args.stage_dir)

    rtm = sorted(LMP_DIR.glob("rtm_*.csv"))
    if rtm:
        _merge_write(
            _lmp_frames(rtm, hourly_mean=True),
            LMP_DIR,
            "CAISO_rtm_hourly",
            ["interval_start_gmt", "node"],
        )
        _stage(rtm, args.stage_dir)

    # Fetch-script load windows plus any hand-downloaded SLD_FCST CSVs.
    load = sorted(LOAD_DIR.glob("load_*.csv")) + sorted(
        LOAD_DIR.glob("*_SLD_FCST_*.csv")
    )
    if load:
        _merge_write(
            _load_frames(load),
            LOAD_DIR,
            "CAISO_tac_load_hourly",
            ["interval_start_gmt", "tac_area"],
        )
        _stage(load, args.stage_dir)  # hand-downloaded names are left in place

    if not (dam or rtm or load):
        print("nothing to process — no raw OASIS window files found")


if __name__ == "__main__":
    main()
