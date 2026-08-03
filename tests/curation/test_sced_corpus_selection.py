"""Trivial-case tests for the NP3-965 SCED corpus source-file selection.

Covers ``derive_ercot_sced_offer_wall._sced_source_files`` (shared by the
CC/CT wall, the steam wall and the fast-start pool derives) after the
2026-08-03 delivery-2023 corpus re-upload (ERCOT-151 §4 ask 1):

* publication-month shards are discovered in BOTH corpus locations
  (``data/raw/ercot/`` and ``data/raw/ercot/SCED/``), the subdirectory copy
  winning a filename collision;
* the corpus supersedes the legacy sample-day extracts only on MAJORITY
  delivery-month coverage — the re-upload's edge months (pubs 2024-01..03)
  must NOT silently replace delivery-2024's sample-day basis;
* the pool derive's ``_load_year`` delivery-year-filters and numerically
  coerces corpus rows (string-typed raw copy, ``MM/DD/YYYY`` stamps,
  empty-string curve steps).
"""

import sys

import pandas as pd

from scripts.data import derive_ercot_faststart_pool as pool
from scripts.data import derive_ercot_sced_offer_wall as wall


def _pub_months(year_first: int, month_first: int, n: int) -> list[str]:
    """``n`` consecutive publication months as ``YYYY-MM`` strings."""
    out = []
    idx = year_first * 12 + (month_first - 1)
    for k in range(n):
        out.append(f"{(idx + k) // 12:04d}-{(idx + k) % 12 + 1:02d}")
    return out


def _wire(monkeypatch, tmp_path):
    """Point the selection globals at a tmp top-level dir + SCED/ subdir.

    The scripts flat-import ``derive_ercot_sced_offer_wall`` (their own
    ``sys.path`` inserts) while tests package-import it — two module objects
    for one file. Patch BOTH so the pool's ``_load_year`` (which calls the
    flat instance's ``_sced_source_files``) sees the tmp dirs too.
    """
    top = tmp_path / "ercot"
    sub = top / "SCED"
    sub.mkdir(parents=True)
    for mod in {wall, sys.modules.get("derive_ercot_sced_offer_wall")} - {None}:
        monkeypatch.setattr(mod, "SCED_DIR", top)
        monkeypatch.setattr(mod, "_CORPUS_DIRS", (top, sub))
    return top, sub


def test_subdir_corpus_majority_supersedes_legacy(monkeypatch, tmp_path):
    """12/12 delivery months covered from SCED/ -> corpus mode, no legacy."""
    top, sub = _wire(monkeypatch, tmp_path)
    for ym in _pub_months(2023, 3, 12):  # pubs 2023-03..2024-02 = delivery 2023
        (sub / f"{ym}.part0000.parquet").touch()
    legacy = top / "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2023_x.parquet"
    legacy.touch()
    files = wall._sced_source_files(2023)
    assert len(files) == 12
    assert all(p.parent == sub for p in files)
    assert legacy not in files


def test_fragment_bleed_falls_back_to_legacy(monkeypatch, tmp_path):
    """Pubs 2024-01..03 cover 1/12 of delivery-2024 -> legacy basis kept."""
    top, sub = _wire(monkeypatch, tmp_path)
    for ym in ("2024-01", "2024-02", "2024-03"):
        (sub / f"{ym}.part0000.parquet").touch()
    legacy = top / "60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2024_x.parquet"
    legacy.touch()
    assert wall._sced_source_files(2024) == [legacy]


def test_no_corpus_no_legacy_is_empty(monkeypatch, tmp_path):
    """An uncovered year selects nothing (year-scoped, never a fallback)."""
    _wire(monkeypatch, tmp_path)
    assert wall._sced_source_files(2025) == []


def test_duplicate_shard_prefers_subdirectory_copy(monkeypatch, tmp_path):
    """A filename in both corpus dirs resolves to the SCED/ re-upload copy."""
    top, sub = _wire(monkeypatch, tmp_path)
    for ym in _pub_months(2023, 3, 12):
        (sub / f"{ym}.part0000.parquet").touch()
    (top / "2023-03.part0000.parquet").touch()  # stale top-level twin
    files = wall._sced_source_files(2023)
    assert len(files) == 12  # deduped by name, never double-weighted
    picked = [p for p in files if p.name == "2023-03.part0000.parquet"]
    assert picked == [sub / "2023-03.part0000.parquet"]


def _corpus_frame() -> pd.DataFrame:
    """String-typed corpus rows: CT 2023 x2 (OFFQS+ON), CC 2023, CT 2022."""
    row = {c: "" for c in pool._READ_COLS}
    base = {
        **row,
        "HASL": "90.0",
        "HSL": "100.0",
        "LSL": "20.0",
        "SCED2 Curve-MW1": "50.0",
        "SCED2 Curve-Price1": "31.5",
    }
    return pd.DataFrame(
        [
            {
                **base,
                "SCED Time Stamp": "01/15/2023 00:05:12",
                "Resource Type": "SCGT90",
                "Telemetered Resource Status": "OFFQS",
            },
            {
                **base,
                "SCED Time Stamp": "01/15/2023 00:05:12",
                "Resource Type": "SCLE90",
                "Telemetered Resource Status": "ON",
            },
            {
                **base,
                "SCED Time Stamp": "01/15/2023 00:05:12",
                "Resource Type": "CCGT90",
                "Telemetered Resource Status": "ON",
            },
            {
                **base,
                "SCED Time Stamp": "12/31/2022 23:50:03",
                "Resource Type": "SCGT90",
                "Telemetered Resource Status": "OFFQS",
            },
        ]
    ).astype("string")


def test_pool_load_year_filters_and_coerces_corpus_rows(monkeypatch, tmp_path):
    """_load_year keeps CT-class delivery-2023 rows only, numerics as float."""
    _, sub = _wire(monkeypatch, tmp_path)
    months = _pub_months(2023, 3, 12)
    _corpus_frame().to_parquet(sub / f"{months[0]}.part0000.parquet", index=False)
    empty = _corpus_frame().iloc[:0]
    for ym in months[1:]:
        empty.to_parquet(sub / f"{ym}.part0000.parquet", index=False)

    live_df, pool_df, files = pool._load_year(2023)
    assert len(files) == 12
    # CC row dropped by class, 2022 row by delivery year; the OFFQS CT row
    # lands in BOTH frames (live keeps all statuses, pool the OFFQS/OFFNS).
    assert len(live_df) == 2
    assert list(live_df.columns) == pool._LIVE_COLS
    assert float(live_df["HSL"].iloc[0]) == 100.0
    assert len(pool_df) == 1
    assert pool_df["Resource Type"].iloc[0] == "SCGT90"
    assert float(pool_df["HASL"].iloc[0]) == 90.0
    # '' curve steps coerce to NaN (the segment builder's absent-step guard)
    assert pd.isna(pool_df["SCED2 Curve-MW2"].iloc[0])
    assert pool_df["SCED2 Curve-MW1"].dtype.kind == "f"
