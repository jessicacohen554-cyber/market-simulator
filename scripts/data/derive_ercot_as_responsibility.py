"""Derive ERCOT hourly telemetered real-time AS responsibilities, by product.

Writes (both committed):

* ``data/raw/ercot-AS/ercot_<year>_as_responsibility_hourly.parquet`` —
  columns ``hour, regup, rrs, rrsffr, nsrs, ecrs``: system-total telemetered
  upward-AS responsibility MW held on ONLINE Gen resources, per product, on
  the model's fixed non-leap 8760 CST clock (hourly mean of SCED-interval
  sums; hours with no corpus coverage read 0.0 — the loader's plan-fallback
  contract).
* ``data/raw/ercot-AS/ercot_<year>_as_responsibility_by_class_hourly.parquet``
  — ``hour`` + ``<class>_<product>`` wide columns for class in
  {gas_cc, gas_ct, gas_st, coal, storage}: the same series split by model
  plant class (the ercot-226 F2 held-location input).

Chartered at ercot-226 (PRECOMMIT-ercot226-held-sequestration-2026-08-22 §2,
factors F1/F1b/F2 under owner waiver W-3 (ercot-226)): the 2023
operator-conservatism depth object is the measured telemetered hold, the
quantity ERCOT subtracts from HSL to form HASL (Nodal Protocols
§6.5.7.6.2.3 / §3.17). Source: the NP3-965 60-Day SCED Gen Resource Data
corpus (``data/raw/ercot/SCED/YYYY-MM.part*.parquet``), read through the
committed constructions of ``derive_ercot_sced_offer_wall``
(``_sced_source_files`` publication-window shard selection +
``_delivery_year_rows`` delivery-year filter) — never re-derived here.

Constructions (all committed precedents, cited):

* Clock: ``SCED Time Stamp`` is Central Prevailing Time; CPT ->
  ``Etc/GMT+6`` fixed CST -> Feb-29 dropped -> ``_MONTH_START_HOUR`` non-leap
  hour-of-year (the ``derive_ercot_sced_offer_wall._chunk_segments`` clock;
  the ercot-216-repaired discipline).
* Status: ``Telemetered Resource Status`` in the ercot123 ``ONLINE`` set
  MINUS ``ONTEST`` (a unit on test is synchronised but its responsibilities
  are not market holds — the ercot-218 §C convention; conservative).
* Products: the five ``AS_UP_COLS`` (``Ancillary Service {REGUP, RRS,
  RRSFFR, NSRS, ECRS}``) — exactly what forms HASL = HSL - sum(resp).
  ``RRSFFR`` is written as its OWN column and NOT summed into ``rrs``
  (PRECOMMIT-ercot226 DECISION-2: the ercot-218 nesting-arithmetic refusal;
  conservative under the F1 max). A shard lacking the ECRS column (pubs
  before 2023-08) reads 0.0 for it — a true zero before the 2023-06-10
  launch, and a DISCLOSED under-measurement for delivery June 2023
  (precommit §2 F1(c)(ii)); no HSL-HASL reconstruction is ever attempted
  (rule 13 line).
* Class map: the committed ``_RESTYPE_TO_CLASS`` of
  ``build_ercot_as_by_restype_from_60day.py`` (unmapped resource types carry
  negligible upward AS and are dropped). Load Resources are out of the Gen
  corpus entirely — disclosed conservative scope, matching the awards
  series.

Rule 23 [R-FROZEN-DERIVE]: re-derive only when the SCED corpus itself
changes, citing the change. Rule 13: this is a measured market quantity
(a power reservation), never an outcome; it enters the model only through
``ScenarioConfig``-gated mechanisms (``ercot_as_held_requirement`` family).

Run:
    python scripts/data/derive_ercot_as_responsibility.py --year 2023
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_HERE = Path(__file__).resolve().parent
REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(REPO / "scripts" / "probes"))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_dam_cleared_share import _MONTH_START_HOUR  # noqa: E402
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _delivery_year_rows,
    _sced_source_files,
)
from ercot123_coal_sced_reach import AS_UP_COLS, ONLINE  # noqa: E402

_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)

#: Product column names, output order. Keys = output columns, values = the
#: NP3-965 telemetered responsibility columns.
PRODUCT_COLS: dict[str, str] = {
    "regup": "Ancillary Service REGUP",
    "rrs": "Ancillary Service RRS",
    "rrsffr": "Ancillary Service RRSFFR",
    "nsrs": "Ancillary Service NSRS",
    "ecrs": "Ancillary Service ECRS",
}
assert set(PRODUCT_COLS.values()) == set(AS_UP_COLS)

#: ONLINE minus ONTEST (module docstring; ercot-218 §C convention).
ONLINE_HELD = frozenset(ONLINE) - {"ONTEST"}

#: Committed RESTYPE -> model class map (build_ercot_as_by_restype_from_60day).
RESTYPE_TO_CLASS: dict[str, str] = {
    "CCGT90": "gas_cc",
    "CCLE90": "gas_cc",
    "SCGT90": "gas_ct",
    "SCLE90": "gas_ct",
    "GSREH": "gas_st",
    "GSSUP": "gas_st",
    "GSNONR": "gas_st",
    "CLLIG": "coal",
    "PWRSTR": "storage",
}
CLASSES: tuple[str, ...] = ("gas_cc", "gas_ct", "gas_st", "coal", "storage")

OUT_DIR = REPO / "data" / "raw" / "ercot-AS"
#: Full-coverage guard: a year with fewer covered delivery days than this is
#: refused without --allow-partial (prevents a fragmentary publication bleed
#: from silently arming the F1 max on a handful of days).
MIN_COVERED_DAYS = 350


def _read_shard(path: Path, year: int) -> pd.DataFrame | None:
    """One shard -> long frame ``ts, cls, n_rows, <product sums>`` or None."""
    avail = set(pq.ParquetFile(path).schema.names)
    prod_have = {k: c for k, c in PRODUCT_COLS.items() if c in avail}
    cols = ["SCED Time Stamp", "Resource Type", "Telemetered Resource Status"]
    df = pd.read_parquet(path, columns=cols + sorted(prod_have.values()))
    df = _delivery_year_rows(df, year)
    if df.empty:
        return None
    stat = df["Telemetered Resource Status"].astype(str).str.strip()
    df = df[stat.isin(ONLINE_HELD)]
    df["cls"] = df["Resource Type"].map(RESTYPE_TO_CLASS)
    df = df.dropna(subset=["cls"])
    if df.empty:
        return None
    for k, c in prod_have.items():
        df[k] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    for k in PRODUCT_COLS:
        if k not in prod_have:
            df[k] = 0.0  # column absent in this publication vintage -> 0
    g = (
        df.groupby(["SCED Time Stamp", "cls"], sort=False)[list(PRODUCT_COLS)]
        .sum()
        .reset_index()
        .rename(columns={"SCED Time Stamp": "ts"})
    )
    return g


def _hoy_of_ts(ts: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """CPT timestamps -> (non-leap hour-of-year, keep-mask). Feb-29 dropped."""
    t = pd.to_datetime(ts, format="%m/%d/%Y %H:%M:%S", errors="coerce")
    cst = t.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = t.notna().to_numpy() & ~((mo == 2) & (dy == 29))
    hoy = np.full(len(ts), -1, dtype=int)
    hoy[ok] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    return hoy, ok


def derive_year(year: int, allow_partial: bool) -> None:
    """Build and write both parquets for one delivery year."""
    files = _sced_source_files(year)
    if not files:
        print(f"[{year}] no SCED source shards — skipping")
        return
    parts: list[pd.DataFrame] = []
    for i, p in enumerate(files):
        g = _read_shard(p, year)
        if g is not None:
            parts.append(g)
        if (i + 1) % 40 == 0:
            print(f"[{year}] scanned {i + 1}/{len(files)} shards")
    if not parts:
        print(f"[{year}] no delivery rows — skipping")
        return
    long = pd.concat(parts, ignore_index=True)
    # A delivery interval publishes in exactly one 60-day drop; guard anyway.
    n0 = len(long)
    long = long.drop_duplicates(subset=["ts", "cls"], keep="first")
    n_dup = n0 - len(long)
    if n_dup:
        print(f"[{year}] WARNING: dropped {n_dup} duplicate (ts, cls) rows")

    hoy, ok = _hoy_of_ts(long["ts"])
    long = long.loc[ok].assign(hoy=hoy[ok])
    # Interval count per hour from DISTINCT interval stamps (all classes), so
    # a class with no rows in an interval averages as a true zero.
    n_int = long.groupby("hoy")["ts"].nunique()
    covered_days = int((long["hoy"] // 24).nunique())
    covered_hours = int(n_int.size)
    print(
        f"[{year}] covered: {covered_hours} hours / {covered_days} days; "
        f"intervals/hour p50 = {float(n_int.median()):.0f}"
    )
    if covered_days < MIN_COVERED_DAYS and not allow_partial:
        raise SystemExit(
            f"[{year}] only {covered_days} covered delivery days "
            f"(< {MIN_COVERED_DAYS}); pass --allow-partial to write anyway"
        )

    sums = long.groupby(["hoy", "cls"], sort=True)[list(PRODUCT_COLS)].sum()
    # Hourly held MW = (sum of interval sums in the hour) / (distinct intervals
    # in the hour) — a class absent from an interval thereby averages as zero.
    hourly = (
        sums / n_int.reindex(sums.index.get_level_values("hoy")).to_numpy()[:, None]
    )

    meta = {
        b"source": b"ERCOT NP3-965 60-Day SCED Gen Resource Data (data/raw/ercot/SCED)",
        b"description": b"telemetered upward-AS responsibility MW, ONLINE\\ONTEST "
        b"Gen resources, hourly mean of SCED-interval sums",
        b"units": b"MW",
        b"year": str(year).encode(),
        b"clock": b"CPT->Etc/GMT+6, non-leap 8760, hour-of-year 0-based",
        b"covered_hours": str(covered_hours).encode(),
        b"duplicate_rows_dropped": str(n_dup).encode(),
        b"charter": b"PRECOMMIT-ercot226-held-sequestration-2026-08-22 section 2",
    }

    grid = pd.DataFrame({"hour": np.arange(8760, dtype=np.int32)})
    sys_wide = hourly.groupby(level="hoy").sum()
    for k in PRODUCT_COLS:
        grid[k] = sys_wide[k].reindex(grid["hour"]).fillna(0.0).to_numpy(float)
    out1 = OUT_DIR / f"ercot_{year}_as_responsibility_hourly.parquet"
    pq.write_table(
        pa.Table.from_pandas(grid, preserve_index=False).replace_schema_metadata(meta),
        out1,
    )
    print(
        f"[{year}] wrote {out1.name}: "
        + ", ".join(f"{k} mean {grid[k].mean():.0f}" for k in PRODUCT_COLS)
    )

    bycls = pd.DataFrame({"hour": np.arange(8760, dtype=np.int32)})
    for cls in CLASSES:
        for k in PRODUCT_COLS:
            col = f"{cls}_{k}"
            if cls in hourly.index.get_level_values("cls"):
                s = hourly.xs(cls, level="cls")[k]
                bycls[col] = s.reindex(bycls["hour"]).fillna(0.0).to_numpy(float)
            else:
                bycls[col] = 0.0
    out2 = OUT_DIR / f"ercot_{year}_as_responsibility_by_class_hourly.parquet"
    pq.write_table(
        pa.Table.from_pandas(bycls, preserve_index=False).replace_schema_metadata(meta),
        out2,
    )
    print(f"[{year}] wrote {out2.name}")

    _print_validations(year, grid, bycls, files)


def _print_validations(
    year: int, grid: pd.DataFrame, bycls: pd.DataFrame, files: list[Path]
) -> None:
    """The precommit's three report-only validation prints (no gating here)."""
    # (a) HASL identity on one sample shard (delivery-August publication).
    sample = next((p for p in files if f"{year}-10." in p.name), files[len(files) // 2])
    cols = [
        "SCED Time Stamp",
        "Resource Type",
        "Telemetered Resource Status",
        "HSL",
        "HASL",
    ]
    avail = set(pq.ParquetFile(sample).schema.names)
    have = [c for c in AS_UP_COLS if c in avail]
    if {"HSL", "HASL"} <= avail and have:
        df = pd.read_parquet(sample, columns=cols + have)
        df = _delivery_year_rows(df, year)
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.isin(ONLINE_HELD)]
        df = df[df["Resource Type"].isin(RESTYPE_TO_CLASS)]
        hsl = pd.to_numeric(df["HSL"], errors="coerce")
        hasl = pd.to_numeric(df["HASL"], errors="coerce")
        resp = sum(pd.to_numeric(df[c], errors="coerce").fillna(0.0) for c in have)
        dev = (hsl - hasl - resp).abs()
        print(
            f"[{year}] HASL identity ({sample.name}, n={len(df)}): "
            f"median |HSL-HASL-sum(resp)| = {float(dev.median()):.2f} MW, "
            f"mean = {float(dev.mean()):.2f} MW"
        )
    # (b) monthly held vs ASPLANNP433 plan, per model product.
    try:
        from market_sim.results.scarcity import ercot_as_plan_requirement_mw

        held_of = {"REGUP": "regup", "RRS": "rrs", "ECRS": "ecrs", "NSPIN": "nsrs"}
        month = np.searchsorted(_MONTH_START_HOUR, np.arange(8760), "right")
        print(
            f"[{year}] monthly mean MW, held (this derive) vs plan "
            f"(ASPLANNP433) [RRS excludes RRSFFR — DECISION-2]:"
        )
        for code, col in held_of.items():
            plan = ercot_as_plan_requirement_mw(year, 8760, code)
            h = pd.Series(grid[col].to_numpy()).groupby(month).mean()
            pl = pd.Series(np.asarray(plan, float)).groupby(month).mean()
            row = " ".join(
                f"{m}:{h.get(m, 0):.0f}/{pl.get(m, 0):.0f}" for m in range(1, 13)
            )
            print(f"    {code:6s} {row}")
    except Exception as e:  # validation print only — never fails the derive
        print(f"[{year}] plan comparison skipped: {e}")
    # (c) storage class vs committed storage DAM-award products.
    awards = OUT_DIR / f"ercot_{year}_storage_as_products_hourly.parquet"
    if awards.exists():
        aw = pd.read_parquet(awards)
        for col, aw_col in (
            ("storage_regup", "regup"),
            ("storage_rrs", "rrs"),
            ("storage_ecrs", "ecrs"),
            ("storage_nsrs", "nonspin"),
        ):
            if aw_col in aw.columns and col in bycls.columns:
                print(
                    f"[{year}] storage {aw_col}: telemetered mean "
                    f"{bycls[col].mean():.0f} vs DAM award mean "
                    f"{aw[aw_col].mean():.0f} MW"
                )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, nargs="+", default=[2023])
    ap.add_argument("--allow-partial", action="store_true")
    args = ap.parse_args()
    for y in args.year:
        derive_year(y, allow_partial=args.allow_partial)


if __name__ == "__main__":
    main()
