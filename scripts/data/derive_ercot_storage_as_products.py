"""Derive ERCOT hourly battery (PWRSTR) upward-AS awards BY PRODUCT.

Writes ``data/raw/ercot-AS/ercot_<year>_storage_as_products_hourly.parquet``
with columns ``hour, regup, rrs, ecrs, nonspin`` — the 60-Day DAM cleared
upward-AS awards of ERCOT Gen-side battery resources (Resource Type
``PWRSTR``), per product, on the model's fixed non-leap 8760 CST clock.

Chartered at ercot-167 (mechanism-testing-matrix §5.1 item 10, owner-chartered
2026-08-05 at ercot-166): the SOC-side reservation ``ercot_storage_as_soc_reserve``
(``model/storage.ercot_storage_as_soc_min``) needs the PRODUCT split because the
published per-product SOC durations differ (RegUp/RRS 1 h, ECRS 2 h, Non-Spin
4 h — ``reserves.spec.ERCOT_AS_PRODUCT_DURATION_H``, Nodal Protocols §3.17.3).
The committed total-storage series the armed power reservation consumes
(``ercot_<year>_as_by_restype_hourly.parquet`` ``storage`` column,
``build_ercot_as_by_restype_from_60day.py``) is NOT touched: the consumer uses
this file's per-product SHARES multiplied by that committed total, so the armed
mechanisms' input stays byte-identical and the two files can never diverge in
total. Validation here measures the reconstruction against the committed total:
2023/2024 reproduce it exactly (max |diff| 0.0 MW); 2025's committed file is an
older disclosure vintage (committed mean 2,515 vs this corpus 2,824 MW), which
is exactly why shares-times-committed is the consumption convention.

Same product basis as the total series (``_UP_AWARD_COLS``): RegUp; RRS =
RRSPFR + RRSFFR + RRSUFR; ECRS = ECRSSD (from the 2023-06-10 launch); NonSpin.
Gen-side only — battery Load-Resource awards are not in the repo (the
``60d_DAM_Load_Resource_Data`` awards file is absent), matching the total
series' declared scope. Rule 23: re-derive only when the Gen Resource Data
source files change, citing the change.

Run:
    python scripts/data/derive_ercot_storage_as_products.py --year 2023 2024 2025
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_ercot_as_withholding import (  # noqa: E402
    HOURS_PER_YEAR,
    _to_model_clock,
    prevailing_he_to_cst,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = REPO_ROOT / "data/raw/ercot"
OUT_DIR = REPO_ROOT / "data/raw/ercot-AS"

# Product -> (award columns, published SOC duration h). Durations are NOT
# written to the parquet — the consumer takes them from
# reserves.spec.ERCOT_AS_PRODUCT_DURATION_H (single source, cited there).
PRODUCT_COLS: dict[str, tuple[str, ...]] = {
    "regup": ("RegUp Awarded",),
    "rrs": ("RRSPFR Awarded", "RRSFFR Awarded", "RRSUFR Awarded"),
    "ecrs": ("ECRSSD Awarded",),
    "nonspin": ("NonSpin Awarded",),
}
_ALL_COLS = tuple(c for cols in PRODUCT_COLS.values() for c in cols)


def _load_pwrstr() -> pd.DataFrame:
    """All PWRSTR Gen Resource Data rows with per-product award MW."""
    files = sorted(
        glob.glob(
            str(GEN_DIR / "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet")
        )
    )
    if not files:
        raise SystemExit(f"no Gen Resource Data parquets under {GEN_DIR}")
    parts: list[pd.DataFrame] = []
    for f in files:
        have = set(pq.ParquetFile(f).schema.names)
        cols = ["Delivery Date", "Hour Ending", "Resource Type"] + [
            c for c in _ALL_COLS if c in have
        ]
        df = pd.read_parquet(f, columns=cols)
        df = df[df["Resource Type"] == "PWRSTR"].copy()
        if df.empty:
            continue
        for prod, srcs in PRODUCT_COLS.items():
            present = [c for c in srcs if c in df.columns]
            df[prod] = (
                df[present]
                .apply(pd.to_numeric, errors="coerce")
                .fillna(0.0)
                .sum(axis=1)
                if present
                else 0.0
            )
        parts.append(df[["Delivery Date", "Hour Ending", *PRODUCT_COLS]])
    big = pd.concat(parts, ignore_index=True)
    big["dd"] = pd.to_datetime(big["Delivery Date"])
    big["he"] = big["Hour Ending"].astype(int)
    return big


def build_year(big: pd.DataFrame, year: int) -> pd.DataFrame | None:
    """One delivery year -> (8760,) per-product frame, or None if uncovered."""
    sub = big[big["dd"].dt.year == year]
    if sub.empty:
        print(f"  {year}: no delivery rows — skipping.")
        return None
    ts = prevailing_he_to_cst(sub["dd"], sub["he"])
    frame = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR, dtype="int64")})
    for prod in PRODUCT_COLS:
        rows = pd.DataFrame({"ts": ts, "mw": sub[prod]})
        rows = rows.groupby("ts", as_index=False)["mw"].sum()
        frame[prod] = _to_model_clock(rows, year)
    tot = frame[list(PRODUCT_COLS)].sum(axis=1)
    # Validation against the committed total the consumer normalizes to.
    committed_path = OUT_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    note = ""
    if committed_path.exists():
        committed = pd.read_parquet(committed_path)["storage"].to_numpy(dtype=float)[
            :HOURS_PER_YEAR
        ]
        diff = np.abs(tot.to_numpy() - committed)
        note = f" | vs committed total: max|diff| {diff.max():.1f} MW"
    print(
        f"  {year}: product means MW "
        + " ".join(f"{p}:{frame[p].mean():.0f}" for p in PRODUCT_COLS)
        + f" | total {tot.mean():.0f}{note}"
    )
    return frame


def _write(frame: pd.DataFrame, year: int) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "ERCOT 60-Day DAM Disclosure (NP3-966-ER), "
            "60d_DAM_Gen_Resource_Data; measured per-resource DAM awards, "
            "Resource Type PWRSTR only (Gen-side batteries).",
            "description": f"ERCOT {year} hourly battery upward-AS awarded MW by "
            "product (regup; rrs=RRSPFR+RRSFFR+RRSUFR; ecrs=ECRSSD; nonspin). "
            "Consumed as SHARES x the committed by-restype 'storage' total by "
            "model/storage.ercot_storage_as_soc_min (ercot_storage_as_soc_reserve).",
            "units": "MW (hour-beginning)",
            "year": str(year),
            "clock": "Model 8760 non-leap ERCOT-local STANDARD time (CST, UTC-6); "
            "Feb29 dropped; Central-Prevailing sequential-HE labels converted "
            "CPT->CST before placement (build_ercot_as_withholding helpers).",
        }
    )
    out = OUT_DIR / f"ercot_{year}_storage_as_products_hourly.parquet"
    pq.write_table(table, out)
    print(f"  wrote {out.relative_to(REPO_ROOT)}")


def main() -> None:
    """CLI: build the per-product battery AS-award parquet per delivery year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    big = _load_pwrstr()
    for year in args.year:
        frame = build_year(big, year)
        if frame is not None:
            _write(frame, year)


if __name__ == "__main__":
    main()
