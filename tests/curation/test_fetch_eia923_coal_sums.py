"""``write_sums`` keeps other years' provenance on a partial EIA-923 refetch."""

from __future__ import annotations

from pathlib import Path

from scripts.data.fetch_eia923_coal_stocks import write_sums


def _line(year: int, sha: str) -> str:
    return f"{sha}  f923_{year}.zip::Schedules_2_3_4_5  https://example/f923_{year}.zip"


def test_partial_refetch_keeps_other_years(tmp_path: Path) -> None:
    path = tmp_path / "SHA256SUMS.txt"
    write_sums(path, [_line(2023, "a"), _line(2024, "b")])
    write_sums(path, [_line(2025, "c")])
    assert path.read_text().splitlines() == [
        _line(2023, "a"),
        _line(2024, "b"),
        _line(2025, "c"),
    ]


def test_refetch_replaces_the_same_year(tmp_path: Path) -> None:
    path = tmp_path / "SHA256SUMS.txt"
    write_sums(path, [_line(2024, "old")])
    write_sums(path, [_line(2024, "new")])
    assert path.read_text().splitlines() == [_line(2024, "new")]
