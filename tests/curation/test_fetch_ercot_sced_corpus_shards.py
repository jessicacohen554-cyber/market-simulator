"""Offline trivial-case tests for the NP3-965 corpus shard writer (ercot-183).

Covers the pure pieces of ``scripts/data/fetch_ercot_sced_corpus_shards.py``
— part numbering that CONTINUES an on-disk month, and the raw all-string
shard schema — without any network access (the fetch loop itself is
publication-driven MIS I/O and is exercised by the intake session's own
shard forensics, not by unit tests).
"""

import pandas as pd

from scripts.data import fetch_ercot_sced_corpus_shards as mod


def test_next_part_index_empty_month(tmp_path):
    """A month with no parts on disk starts at part0000."""
    assert mod._next_part_index(tmp_path, "2024-04") == 0


def test_next_part_index_continues_existing_numbering(tmp_path):
    """The 2024-03 re-upload precedent: new parts append after part0008."""
    for k in range(9):
        (tmp_path / f"2024-03.part{k:04d}.parquet").touch()
    (tmp_path / "2024-04.part0000.parquet").touch()  # other months don't count
    assert mod._next_part_index(tmp_path, "2024-03") == 9


def test_write_part_raw_string_schema(tmp_path):
    """Shards keep the raw all-string schema, empty strings included."""
    df = pd.DataFrame(
        {
            "SCED Time Stamp": ["03/01/2024 00:05:12"],
            "SCED2 Curve-MW1": [""],  # unused steps stay EMPTY STRINGS
            "HSL": ["100.5"],
        },
        dtype=str,
    )
    path = mod._write_part(df, tmp_path, "2024-05")
    assert path.name == "2024-05.part0000.parquet"
    back = pd.read_parquet(path)
    assert back["SCED2 Curve-MW1"].iloc[0] == ""
    assert back["HSL"].iloc[0] == "100.5"  # never numerically coerced at rest
    assert mod._write_part(df, tmp_path, "2024-05").name == "2024-05.part0001.parquet"
