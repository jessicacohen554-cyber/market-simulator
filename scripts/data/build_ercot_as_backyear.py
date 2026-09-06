"""Build the MEASURED back-year (2018-2022) ERCOT load-resource RRS series.

Writes ``data/raw/ercot-AS/ercot_<year>_as_up_mw.parquet`` for a DELIVERY year
in 2018-2022 — the same schema as the 2023 (``build_ercot_as_2023.py``) and
2024/2025 (``build_ercot_as_withholding.py``) files, so the co-opt
load-resource credit (``scarcity.ercot_load_resource_reserve_mw``, which reads
only ``rrsufr_mw``) resolves for a back year exactly as it does for a
training year. Data intake under CLAUDE.md rule 22 `[R-HOLDOUT]`: *what is
held out is the SCORE, never the DATA* — a measured input belongs in every
year, and this builder prepares it; whether a solve consumes it is the
``ercot_load_resource_reserve_from_year`` recipe gate, which this script
never touches.

Why the back years are DIRECTLY measurable (unlike 2023):
    The 60-Day DAM Disclosure **Load Resource Data** file
    (``data/raw/ercot-AS/60d_DAM_Load_Resource_Data_<posting-year>.parquet``,
    owner drop 2026-09-06) carries the per-Load-Resource cleared DAM
    **awards** — ``RRS Awarded`` before the 2022-10-15 RRS split and
    ``RRSPFR/RRSFFR/RRSUFR Awarded`` after it — so the load-side Responsive
    Reserve is read off the awards, not reconstructed. The 2023 series had to
    be a measured-shape / cleared-level hybrid because only the Load Resource
    *offers* file exists for 2023; that limitation does not apply here.

What ``rrsufr_mw`` is for a back year:
    The system total of Load-Resource RRS awards in the hour — pre-split the
    single ``RRS Awarded`` column (LR RRS was undifferentiated; by protocol the
    overwhelming share is the under-frequency-relay product), post-split the
    sum of the three components. The post-split LR PFR share is ~4 % (2022
    Oct 15 - Nov 1: UFR ~976 MW, PFR ~40 MW), so carrying the LR total keeps
    the 2022 series internally consistent across the split at the cost of a
    ~40 MW definitional difference from the 2023+ series, which are UFR-only.
    Generator RRSUFR awards are 0 in every file (verified), so the
    load-resource total is the whole RRS-UFR product.

Coverage and the ONE reconstructed window:
    The disclosure files are named by POSTING year and each spans deliveries
    Nov 2 (Y-1) .. Nov 1 (Y), so a delivery year needs the Y and Y+1 files.
    Delivery 2018-2021 are fully covered. Delivery **2022 Nov 2 - Dec 31**
    (1,440 h, 16.4 % of the year) is NOT: the posting-year-2023 Load Resource
    file is not in the repo (the Gen Resource half of that same disclosure
    IS, under ``data/raw/ercot/``). Those hours are filled by the measured
    residual identity
    ``LR_RRS(t) = ASPLAN_RRS(t) - gen_RRS_awards(t) - offset``,
    where ``offset`` is the within-year mean of ``(plan - gen - LR)`` over the
    7,318 covered 2022 hours (the self-arranged / un-awarded RRS share, stable
    at ~700-830 MW in every month; corr(plan - gen, LR) = 0.92). The
    reconstructed hours are flagged in the parquet metadata with the offset,
    the covered-hour count and the window; the same class of within-year
    reconciliation the 2023 series documents for its Oct 2 - Dec 9 gap. A
    year with uncovered hours and no ASPLAN file zero-fills them with a
    warning (the ``build_ercot_as_withholding`` convention: never fabricate
    reserve across a multi-month hole) — no such year exists in 2018-2022.

Other columns (schema parity, NOT consumed downstream): ``regup_mw`` /
``nspin_mw`` are cleared-to-plan (ASPLAN) where a plan file exists, else the
gen + LR awards; ``rrspfr_mw`` / ``rrsffr_mw`` are the generator awards (the
pre-split gen ``RRS Awarded`` — governor-response reserve — is booked to
``rrspfr_mw``); ECRS (launched 2023-06-10) and NSPNM (Dec 2025) are zero.

Clock: the fixed non-leap 8760-hour ERCOT-local STANDARD clock (CST, UTC-6).
The 60-Day labels are Central Prevailing sequential HE (HE 1-25 on the
fall-back day) and are converted with ``prevailing_he_to_cst``; ASPLAN's
repeated-HE + DSTFlag labels with ``_prevailing_to_standard``.

Run:
    python scripts/data/build_ercot_as_backyear.py                 # 2020 2021 2022
    python scripts/data/build_ercot_as_backyear.py --year 2022
    python scripts/data/build_ercot_as_backyear.py --year 2018 2019 2020 2021 2022
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
sys.path.insert(
    0, str(REPO_ROOT)
)  # repo root: canonical scripts.data.* sibling imports on direct run
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.data.build_ercot_as_withholding import (  # noqa: E402
    HOURS_PER_YEAR,
    prevailing_he_to_cst,
)
from scripts.data.build_ercot_hsl import _prevailing_to_standard  # noqa: E402

from market_sim.config.paths import ERCOT_AS_DIR, ERCOT_MIS_DIR  # noqa: E402

AS_DIR = ERCOT_AS_DIR
MIS_DIR = ERCOT_MIS_DIR

# Delivery years the 60-Day Load Resource Data drop can serve. 2023+ have no
# Load Resource awards file (see the 2023 builder); the default build is the
# rule-22 validation ladder, 2018/2019 are explicit.
BUILDABLE_YEARS: tuple[int, ...] = (2018, 2019, 2020, 2021, 2022)
DEFAULT_YEARS: tuple[int, ...] = (2020, 2021, 2022)

# RRS award columns across the 2022-10-15 split (a file carries whichever
# subset its posting window used; absent columns read as zero).
_RRS_COLS: tuple[str, ...] = (
    "RRS Awarded",
    "RRSPFR Awarded",
    "RRSFFR Awarded",
    "RRSUFR Awarded",
)
_LR_COLS: tuple[str, ...] = _RRS_COLS + ("RegUp Awarded", "NonSpin Awarded")
_GEN_COLS: tuple[str, ...] = _LR_COLS

# (month, day, hour) calendar of the fixed non-leap 8760-hour clock.
_CALENDAR = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
_FULL_INDEX = pd.MultiIndex.from_arrays(
    [_CALENDAR.month, _CALENDAR.day, _CALENDAR.hour], names=["month", "day", "hour"]
)


# ---------------------------------------------------------------------------
# Source readers (each returns per-resource rows already summed to the hour)
# ---------------------------------------------------------------------------


def _read_awards(paths: list[Path], cols: tuple[str, ...], year: int) -> pd.DataFrame:
    """Sum per-resource award columns to ``(date, he)`` rows for delivery ``year``.

    Reads every file in ``paths`` (the disclosure files are keyed by POSTING
    year, so a delivery year spans two of them), keeps only rows whose
    ``Delivery Date`` falls in ``year``, sums each award column across
    resources per ``(Delivery Date, Hour Ending)``, and drops duplicate
    hours if the same delivery window is present in more than one file.
    Missing columns (pre-/post-split schemas) read as zero.
    """
    frames: list[pd.DataFrame] = []
    for path in paths:
        have = set(pq.read_schema(path).names)
        use = [c for c in cols if c in have]
        df = pd.read_parquet(path, columns=["Delivery Date", "Hour Ending", *use])
        df["date"] = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y")
        df = df[df["date"].dt.year == year]
        if df.empty:
            continue
        for c in cols:
            if c not in df.columns:
                df[c] = 0.0
        frames.append(df.groupby(["date", "Hour Ending"])[list(cols)].sum())
    if not frames:
        return pd.DataFrame(columns=list(cols))
    out = pd.concat(frames)
    return out[~out.index.duplicated(keep="first")].sort_index()


def _lr_paths() -> list[Path]:
    """Every 60-Day Load Resource Data (awards) file on disk."""
    return sorted(AS_DIR.glob("60d_DAM_Load_Resource_Data_*.parquet"))


def _gen_paths() -> list[Path]:
    """Every 60-Day Gen Resource Data file on disk (both intake directories)."""
    return sorted(AS_DIR.glob("60d_DAM_Gen_Resource_Data_*.parquet")) + sorted(
        MIS_DIR.glob("60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet")
    )


def _asplan_path(year: int) -> Path | None:
    """The ASPLANNP433 file for ``year`` if it exists (2022+ only on disk)."""
    path = MIS_DIR / f"ASPLANNP433_{year}.parquet"
    return path if path.exists() else None


# ---------------------------------------------------------------------------
# Clock placement
# ---------------------------------------------------------------------------


def awards_to_rows(hourly: pd.DataFrame, col: str) -> pd.DataFrame:
    """``(date, he)``-indexed sums -> ``(ts, mw)`` hour-beginning CST rows."""
    if hourly.empty:
        return pd.DataFrame({"ts": pd.to_datetime([]), "mw": []})
    idx = hourly.index.to_frame(index=False)
    ts = prevailing_he_to_cst(idx["date"], idx["Hour Ending"].astype(int))
    return pd.DataFrame({"ts": ts.to_numpy(), "mw": hourly[col].to_numpy(dtype=float)})


def asplan_rows(asp: pd.DataFrame, as_type: str, year: int) -> pd.DataFrame:
    """ASPLAN rows of one ``AncillaryType`` -> ``(ts, mw)`` on the CST clock.

    ASPLAN labels are Central Prevailing in the repeated-HE convention with
    the fall-back repeat flagged ``DSTFlag == 'Y'``.
    """
    sub = asp[asp["AncillaryType"] == as_type].copy()
    if sub.empty:
        return pd.DataFrame({"ts": pd.to_datetime([]), "mw": []})
    date = pd.to_datetime(sub["DeliveryDate"], format="%m/%d/%Y", errors="coerce")
    if date.isna().all():
        date = pd.to_datetime(sub["DeliveryDate"])
    he = sub["HourEnding"].astype(str).str.slice(0, 2).astype(int)
    ts = _prevailing_to_standard(
        date + pd.to_timedelta(he - 1, unit="h"), sub["DSTFlag"]
    )
    rows = pd.DataFrame(
        {"ts": ts.to_numpy(), "mw": sub["Quantity"].to_numpy(dtype=float)}
    )
    rows = rows.dropna(subset=["ts"])
    return rows[pd.to_datetime(rows["ts"]).dt.year == year]


def to_clock_keep_gaps(rows: pd.DataFrame, year: int) -> np.ndarray:
    """Place ``(ts, mw)`` rows on the 8760 clock for ``year``; uncovered hours NaN.

    Averages duplicate stamps (none survive the CPT->CST conversion on a
    gapless feed), drops Feb 29, and leaves every uncovered hour NaN so the
    caller decides — explicitly — what to do with a hole.
    """
    if rows.empty:
        return np.full(HOURS_PER_YEAR, np.nan)
    ts = pd.to_datetime(rows["ts"])
    keep = (ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    rows = rows[keep]
    ts = ts[keep]
    if rows.empty:
        return np.full(HOURS_PER_YEAR, np.nan)
    grouped = rows.groupby([ts.dt.month, ts.dt.day, ts.dt.hour])["mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    return grouped.reindex(_FULL_INDEX).to_numpy(dtype=float)


# ---------------------------------------------------------------------------
# The series
# ---------------------------------------------------------------------------


def build_rrsufr(
    lr_rrs: np.ndarray,
    gen_rrs: np.ndarray,
    plan_rrs: np.ndarray | None,
    year: int,
) -> tuple[np.ndarray, dict[str, str]]:
    """The load-resource RRS series with any uncovered hours reconstructed.

    ``lr_rrs`` is the measured LR award total on the clock (NaN where the
    awards file does not cover the hour); ``gen_rrs`` the generator RRS award
    total; ``plan_rrs`` the ASPLAN RRS requirement (or ``None``). Covered
    hours are returned as measured. Uncovered hours are filled with
    ``plan - gen - offset`` where ``offset`` is the mean of
    ``plan - gen - lr`` over the covered hours (the within-year residual
    reconciliation described in the module docstring); with no plan they are
    zero-filled. Returns the series and a metadata dict describing exactly
    which hours were reconstructed and how.
    """
    lr = np.asarray(lr_rrs, dtype=float)
    covered = ~np.isnan(lr)
    meta: dict[str, str] = {
        "rrsufr_covered_hours": str(int(covered.sum())),
        "rrsufr_reconstructed_hours": "0",
    }
    if covered.all():
        return lr, meta
    out = lr.copy()
    if plan_rrs is None:
        out[~covered] = 0.0
        meta["rrsufr_reconstructed_hours"] = str(int((~covered).sum()))
        meta["rrsufr_reconstruction"] = (
            "ZERO-FILLED: no ASPLANNP433 file for the year, so the uncovered "
            "hours carry no reserve rather than a fabricated one"
        )
        print(
            f"  WARNING: {int((~covered).sum())} uncovered hours in {year} "
            "zero-filled (no ASPLAN file to reconstruct from)"
        )
        return out, meta
    plan = np.asarray(plan_rrs, dtype=float)
    gen = np.nan_to_num(np.asarray(gen_rrs, dtype=float))
    resid = plan - gen
    both = covered & ~np.isnan(resid)
    offset = float(np.mean(resid[both] - lr[both]))
    corr = float(np.corrcoef(resid[both], lr[both])[0, 1])
    fill = np.maximum(resid - offset, 0.0)
    fill_mask = ~covered
    out[fill_mask] = fill[fill_mask]
    still = np.isnan(out)
    if still.any():
        out[still] = 0.0
    hours = np.flatnonzero(fill_mask)
    meta["rrsufr_reconstructed_hours"] = str(int(fill_mask.sum()))
    meta["rrsufr_reconstruction"] = (
        f"hours {int(hours.min())}..{int(hours.max())} (model-clock index) have no "
        "Load Resource awards coverage and are the measured residual identity "
        "ASPLAN_RRS - gen_RRS_awards - offset, offset = within-year mean of "
        f"(plan - gen - LR) over the {int(both.sum())} covered hours = "
        f"{offset:.1f} MW (corr(plan - gen, LR) = {corr:.3f}); "
        f"{int(still.sum())} hours with neither source zero-filled"
    )
    return out, meta


def build_year(year: int, *, write: bool = True) -> Path | None:
    """Build (and by default write) ``ercot_<year>_as_up_mw.parquet``."""
    if year not in BUILDABLE_YEARS:
        raise SystemExit(
            f"{year} is outside the 60-Day Load Resource Data coverage "
            f"{BUILDABLE_YEARS}; 2023+ are built by build_ercot_as_2023.py / "
            "build_ercot_as_withholding.py"
        )
    print(f"=== ERCOT load-resource RRS series, delivery year {year} ===")
    lr_h = _read_awards(_lr_paths(), _LR_COLS, year)
    gen_h = _read_awards(_gen_paths(), _GEN_COLS, year)
    if lr_h.empty:
        print(f"  no Load Resource award rows for {year} — skipping")
        return None
    lr_h["lr_rrs"] = lr_h[list(_RRS_COLS)].sum(axis=1)
    gen_h["gen_rrs"] = gen_h[list(_RRS_COLS)].sum(axis=1)

    lr_rrs = to_clock_keep_gaps(awards_to_rows(lr_h, "lr_rrs"), year)
    gen_rrs = to_clock_keep_gaps(awards_to_rows(gen_h, "gen_rrs"), year)
    print(
        f"  LR awards cover {int((~np.isnan(lr_rrs)).sum())}/{HOURS_PER_YEAR} h; "
        f"gen awards cover {int((~np.isnan(gen_rrs)).sum())}/{HOURS_PER_YEAR} h"
    )

    plan_path = _asplan_path(year)
    asp = pd.read_parquet(plan_path) if plan_path is not None else None
    plan_rrs = (
        to_clock_keep_gaps(asplan_rows(asp, "RRS", year), year)
        if asp is not None
        else None
    )

    rrsufr, meta = build_rrsufr(lr_rrs, gen_rrs, plan_rrs, year)
    print(
        f"  rrsufr_mw: mean {rrsufr.mean():.0f} MW  min {rrsufr.min():.0f}  "
        f"max {rrsufr.max():.0f}  (2023/2024/2025 series: 884 / 904 / 787)"
    )
    if meta["rrsufr_reconstructed_hours"] != "0":
        print(f"  {meta['rrsufr_reconstruction']}")

    def gen_col(col: str) -> np.ndarray:
        return np.nan_to_num(to_clock_keep_gaps(awards_to_rows(gen_h, col), year))

    def lr_col(col: str) -> np.ndarray:
        return np.nan_to_num(to_clock_keep_gaps(awards_to_rows(lr_h, col), year))

    def plan_col(as_type: str, fallback: np.ndarray) -> np.ndarray:
        if asp is None:
            return fallback
        arr = to_clock_keep_gaps(asplan_rows(asp, as_type, year), year)
        return np.where(np.isnan(arr), fallback, arr)

    # Pre-split generator RRS is governor-response reserve -> rrspfr_mw.
    frame = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "regup_mw": plan_col(
                "REGUP", gen_col("RegUp Awarded") + lr_col("RegUp Awarded")
            ),
            "rrspfr_mw": gen_col("RRS Awarded") + gen_col("RRSPFR Awarded"),
            "rrsffr_mw": gen_col("RRSFFR Awarded"),
            "rrsufr_mw": rrsufr,
            "ecrss_mw": np.zeros(HOURS_PER_YEAR),
            "ecrsm_mw": np.zeros(HOURS_PER_YEAR),
            "nspin_mw": plan_col(
                "NSPIN", gen_col("NonSpin Awarded") + lr_col("NonSpin Awarded")
            ),
            "nspnm_mw": np.zeros(HOURS_PER_YEAR),
        }
    )
    frame["as_up_mw"] = frame[
        [c for c in frame.columns if c.endswith("_mw") and c != "as_up_mw"]
    ].sum(axis=1)
    if not write:
        return None
    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "ERCOT 60-Day DAM Disclosure (NP3-966-ER) Load Resource Data "
            "per-resource cleared AWARDS + Gen Resource Data awards"
            + (" + ASPLANNP433" if asp is not None else "")
            + ".",
            "description": f"ERCOT {year} system-wide hourly UP-AS MW. rrsufr_mw is the "
            "MEASURED load-resource Responsive Reserve award total (RRS Awarded before "
            "the 2022-10-15 PFR/FFR/UFR split; RRSPFR+RRSFFR+RRSUFR after it) — the "
            "consumed co-opt load-resource credit; see "
            "scripts/data/build_ercot_as_backyear.py. Other columns are cleared-to-plan "
            "(ASPLAN, where present) / measured awards for schema parity and are not "
            "consumed downstream.",
            "units": "MW (hour-beginning)",
            "clock": "Fixed non-leap 8760h ERCOT-local STANDARD time (CST, UTC-6): the "
            "60-Day Central-Prevailing sequential-HE labels (HE 1-25 on the fall-back "
            "day) and ASPLAN repeated-HE + DSTFlag labels are converted CPT->CST before "
            "placement, matching the EIA-930 demand clock.",
            "year": str(year),
            **meta,
        }
    )
    out = AS_DIR / f"ercot_{year}_as_up_mw.parquet"
    pq.write_table(table, out)
    print(f"  wrote {out}")
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--year",
        type=int,
        nargs="+",
        default=list(DEFAULT_YEARS),
        help=f"delivery years to build (default {list(DEFAULT_YEARS)}; any of {list(BUILDABLE_YEARS)})",
    )
    args = ap.parse_args(argv)
    for year in args.year:
        build_year(int(year))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
