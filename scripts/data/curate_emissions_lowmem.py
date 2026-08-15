"""PERF-A NOT-FOR-MERGE prototype: memory-bounded emissions curation.

Produces output identical to ``scripts/data/curate_emissions.py`` (same rows,
same order, same dtypes, same parquet layout via ``clean_io.write_clean_iter``'s
documented data-byte-identity) while cutting peak RSS from the measured
~10.0 GiB to a level a standard GitHub runner (7.8 GiB RAM + 3 GiB swap,
measured 2026-08-15) survives with margin. The stock script's peak is driven
by, in order: the full-frame ``pd.concat`` stacking (parts + result live
together), ``drop_duplicates`` (hashtable over a python-string key column),
``sort_values`` (whole-frame take copy), and ``write_clean``'s full
``pa.Table.from_pandas`` second copy.

What changes (mechanics only — every transform is order-equivalent):

* **Column-wise assembly.** Per-state cleaned frames are stacked one COLUMN at
  a time (``pd.concat`` on Series), freeing each part's column as it is
  consumed, so the parts and the result never coexist in full.
* **Factorized lexsort + neighbor dedupe.** The (plant_id, unit_id,
  interval_start_utc) sort key is materialized as three int64 arrays
  (``unit_id`` factorized, codes re-ranked to lexicographic order) and sorted
  with ``np.lexsort`` (stable). Because the stable sort preserves input order
  within equal keys, keeping the first row of each equal-key run selects
  exactly the rows ``drop_duplicates(keep="first")`` keeps, and the final
  order equals the stock ``sort_values`` order (keys are unique post-dedupe).
* **Column-wise take.** The kept-row gather runs per column, dropping each
  source column after it is gathered.
* **Streaming write.** ``clean_io.write_clean_iter`` (built for exactly this —
  see its docstring) writes bounded row groups laid out identically to
  ``write_clean``'s.

Verification protocol (run by PERF-A, results in
``docs/handoffs/perf-recheck-2026-08.md``): read back both parquets and
compare with ``pandas.testing.assert_frame_equal(check_exact=True)`` plus
dtype equality; peak RSS via VmHWM both ways.

Usage:
    python scripts/data/curate_emissions_lowmem.py --years 2023
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the stock module's cleaning, schema and path logic — one source of
# truth; this file only replaces the assembly/dedupe/sort/write mechanics.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.data.curate_emissions import (  # noqa: E402
    _SCHEMA_COLUMNS,
    RAW_FACILITY_DIR,
    RAW_UNIT_DIR,
    _detect_years,
    clean_campd_frame,
)
from scripts.lib import clean_io  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("curate_emissions_lowmem")

_CHUNK_ROWS = 2_000_000  # streaming-write chunk; bounds the writer's buffer


def _assemble_column(parts: list[pd.DataFrame], col: str) -> pd.Series:
    """Concat one column across parts, dropping it from each part as consumed."""
    series = pd.concat([p[col] for p in parts], ignore_index=True, copy=False)
    for p in parts:
        del p[col]
    return series


def curate_year_lowmem(
    year: int,
    *,
    unit_dir: Path = RAW_UNIT_DIR,
    fac_dir: Path = RAW_FACILITY_DIR,
) -> Path:
    """Memory-bounded equivalent of ``curate_emissions.curate_year``."""
    unit_paths = sorted(unit_dir.glob(f"*_{year}.parquet")) if unit_dir.is_dir() else []
    fac_paths = sorted(fac_dir.glob(f"*_{year}.parquet")) if fac_dir.is_dir() else []
    if not unit_paths and not fac_paths:
        raise FileNotFoundError(
            f"no CAMPD extracts for {year} in {unit_dir} or {fac_dir}"
        )

    # Per-state cleaned parts, unit grain first (their concat order is the
    # stock script's row order pre-sort, which the stable dedupe depends on).
    parts: list[pd.DataFrame] = []
    covered: set[int] = set()
    n_unit = 0
    for p in unit_paths:
        f = clean_campd_frame(pd.read_parquet(p), facility_level=False)
        covered.update(f["plant_id"].unique().tolist())
        n_unit += len(f)
        parts.append(f)
    n_fac = 0
    for p in fac_paths:
        f = clean_campd_frame(pd.read_parquet(p), facility_level=True)
        f = f[~f["plant_id"].isin(covered)]  # unit-level wins where it exists
        if len(f):
            f = f.reset_index(drop=True)
            n_fac += len(f)
            parts.append(f)

    # Column-wise stack: parts shed each column as the output gains it.
    cols: dict[str, pd.Series] = {}
    for c in _SCHEMA_COLUMNS:
        cols[c] = _assemble_column(parts, c)
    parts.clear()
    n_rows = len(cols["plant_id"])

    # Sort keys as flat int64 arrays. unit_id: factorize (hash, appearance
    # order) then re-rank the uniques lexicographically so integer order ==
    # string order; interval_start_utc: tz-aware ns since epoch.
    plant = cols["plant_id"].to_numpy()
    codes, uniques = pd.factorize(cols["unit_id"], sort=False)
    rank = np.empty(len(uniques), dtype=np.int64)
    rank[np.argsort(uniques.astype(object), kind="stable")] = np.arange(len(uniques))
    unit_key = rank[codes]
    del codes, rank
    ts = cols["interval_start_utc"].to_numpy(dtype="datetime64[ns]").view("i8")

    # Stable lexsort (primary key LAST in np.lexsort's tuple), then keep the
    # first row of each equal-key run == drop_duplicates(keep="first").
    order = np.lexsort((ts, unit_key, plant))
    p_s, u_s, t_s = plant[order], unit_key[order], ts[order]
    keep = np.empty(n_rows, dtype=bool)
    if n_rows:
        keep[0] = True
        keep[1:] = (p_s[1:] != p_s[:-1]) | (u_s[1:] != u_s[:-1]) | (t_s[1:] != t_s[:-1])
    idx = order[keep]
    del order, p_s, u_s, t_s, keep, plant, unit_key, ts

    # Column-wise gather of the kept rows, freeing each source column.
    out: dict[str, pd.Series] = {}
    for c in _SCHEMA_COLUMNS:
        out[c] = cols.pop(c).take(idx).reset_index(drop=True)
    del idx

    n_out = len(out["plant_id"])
    source = (
        f"data/raw/campd-unit-level/*_{year}.parquet, "
        f"data/raw/campd-facility-level/*_{year}.parquet"
    )

    def _chunks():
        for lo in range(0, n_out, _CHUNK_ROWS):
            hi = min(lo + _CHUNK_ROWS, n_out)
            yield pd.DataFrame(
                {c: out[c].iloc[lo:hi].reset_index(drop=True) for c in _SCHEMA_COLUMNS}
            )

    path = clean_io.write_clean_iter(_chunks(), "emissions", year=year, source=source)
    clean_io.validate_clean(path)
    logger.info(
        "emissions %d (lowmem): %d rows (%d unit-grain, %d facility-ALL pre-dedupe) -> %s",
        year,
        n_out,
        n_unit,
        n_fac,
        path,
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Memory-bounded CAMPD emissions curation (PERF-A prototype)."
    )
    parser.add_argument("--years", type=int, nargs="*", default=None)
    args = parser.parse_args(argv)
    years = args.years or _detect_years(RAW_UNIT_DIR, RAW_FACILITY_DIR)
    if not years:
        logger.error("no CAMPD extracts found")
        return 1
    for year in years:
        curate_year_lowmem(year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
