"""Tests for the eGRID sheet parquet mirror (``data/egrid_sheets``).

The load-bearing property is equality: a mirrored read must return exactly the
frame the direct ``pd.read_excel`` returns — same values, same column order,
same dtypes — because both eGRID call sites on the solve path feed the frame
straight into lookups the LP reads. Everything here builds a tiny synthetic
workbook shaped like eGRID (a descriptive first row above the short-code header
row, extra columns the callers do not ask for) rather than the real 21 MB file,
so the whole module stays in the fast tier.
"""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from market_sim.data.egrid_sheets import (
    _SKIPROWS,
    _mirror_path,
    _workbook_digest,
    read_egrid_sheet,
)

# The three (sheet, usecols) pairs the solve path actually reads, from
# zone_assignment._plnt23 and fleet.eia860._egrid_boundary_hr_repairs_for.
SOLVE_PATH_READS: list[tuple[str, list[str]]] = [
    ("PLNT23", ["ORISPL", "LAT", "LON", "FIPSST", "FIPSCNTY", "BACODE"]),
    ("PLNT23", ["ORISPL", "LAT", "LON", "PLHTIAN", "PLNGENAN", "PLHTRT"]),
    ("UNT23", ["ORISPL", "HTIAN", "UNTYRONL"]),
]

# Column order here is the *sheet* order, which deliberately does not match the
# usecols order above — reproducing it is part of what the mirror must get right.
_PLNT23_COLUMNS = [
    "ORISPL",
    "BACODE",
    "FIPSST",
    "FIPSCNTY",
    "LAT",
    "LON",
    "PLHTIAN",
    "PLNGENAN",
    "PLHTRT",
    "PNAME",
]
_UNT23_COLUMNS = ["ORISPL", "UNITID", "HTIAN", "UNTYRONL"]


def _synthetic_plnt23() -> pd.DataFrame:
    """Return a small PLNT23-shaped frame with eGRID's mix of dtypes."""
    return pd.DataFrame(
        {
            "ORISPL": [3, 127, 6041, 55234],
            "BACODE": ["ERCO", "CISO", "PJM", None],
            "FIPSST": [1, 6, 42, 48],
            "FIPSCNTY": [73, 29, 3, 201],
            "LAT": [33.6456, 35.0333, 40.4406, 29.7604],
            "LON": [-87.0561, -118.2, -79.9959, -95.3698],
            "PLHTIAN": [1.2345e7, 9.87e6, None, 4.2e5],
            "PLNGENAN": [1.1e6, -2.5e4, 8.0e5, 0.0],
            "PLHTRT": [10450.0, 7123.5, None, 9900.25],
            "PNAME": ["Barry", "Alamitos", "Cheswick", "Parish"],
        }
    )


def _synthetic_unt23() -> pd.DataFrame:
    """Return a small UNT23-shaped frame with eGRID's mix of dtypes."""
    return pd.DataFrame(
        {
            "ORISPL": [3, 3, 127, 6041, 55234],
            "UNITID": ["1", "2", "GT1", "CT-A", "ST"],
            "HTIAN": [5.5e6, 6.9e6, None, 3.1e6, 4.2e5],
            "UNTYRONL": [1954, 1969, 2001, None, 2016],
        }
    )


@pytest.fixture
def workbook(tmp_path):
    """Write a two-sheet eGRID-shaped xlsx and return its path.

    Each sheet carries eGRID's long descriptive header as row 1 above the
    short-code header row, which is what the reader's ``skiprows=1`` drops.
    """
    path = tmp_path / "egrid_synthetic_data_rev2.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, columns, frame in (
            ("PLNT23", _PLNT23_COLUMNS, _synthetic_plnt23()),
            ("UNT23", _UNT23_COLUMNS, _synthetic_unt23()),
        ):
            descriptive = pd.DataFrame([[f"Description of {c}" for c in columns]])
            descriptive.to_excel(writer, sheet_name=sheet, index=False, header=False)
            frame[columns].to_excel(writer, sheet_name=sheet, index=False, startrow=1)
    return path


def _direct(path, sheet, usecols) -> pd.DataFrame:
    """Read a sheet the way the call sites used to, straight through openpyxl."""
    return pd.read_excel(path, sheet_name=sheet, skiprows=1, usecols=usecols)


@pytest.mark.parametrize(("sheet", "usecols"), SOLVE_PATH_READS)
def test_mirror_read_equals_xlsx_read(workbook, sheet, usecols):
    """The gate: mirrored read ``.equals`` the xlsx read, for all three pairs.

    The first call is a mirror miss (so it parses the workbook and writes the
    mirror); the second is a hit served from parquet. Both must equal the direct
    ``read_excel`` frame, and the hit must not merely equal it loosely — dtypes
    and column order are compared explicitly, since the callers index by name
    and feed the values to ``to_numpy(dtype=...)``.
    """
    reference = _direct(workbook, sheet, usecols)

    miss = read_egrid_sheet(workbook, sheet, usecols)
    assert _mirror_path(workbook, sheet, usecols).exists()
    assert miss.equals(reference)

    hit = read_egrid_sheet(workbook, sheet, usecols)
    assert hit.equals(reference)
    assert list(hit.columns) == list(reference.columns)
    assert hit.dtypes.to_dict() == reference.dtypes.to_dict()


def test_mirror_preserves_sheet_column_order_not_usecols_order(workbook):
    """``read_excel`` orders columns by the sheet, and so must the mirror.

    Guards the specific trap that makes a naive wide-mirror-plus-subset design
    wrong: the first PLNT23 call site lists ``LAT, LON`` before ``FIPSST``, but
    eGRID's sheet puts ``BACODE, FIPSST, FIPSCNTY`` first.
    """
    usecols = ["ORISPL", "LAT", "LON", "FIPSST", "FIPSCNTY", "BACODE"]
    expected = ["ORISPL", "BACODE", "FIPSST", "FIPSCNTY", "LAT", "LON"]

    assert list(_direct(workbook, "PLNT23", usecols).columns) == expected
    read_egrid_sheet(workbook, "PLNT23", usecols)  # populate the mirror
    assert list(read_egrid_sheet(workbook, "PLNT23", usecols).columns) == expected


def test_distinct_usecols_get_distinct_mirrors(workbook):
    """The two PLNT23 projections must not collide on one mirror file."""
    (_, first), (_, second) = SOLVE_PATH_READS[0], SOLVE_PATH_READS[1]
    assert _mirror_path(workbook, "PLNT23", first) != _mirror_path(
        workbook, "PLNT23", second
    )

    read_egrid_sheet(workbook, "PLNT23", first)
    assert read_egrid_sheet(workbook, "PLNT23", second).equals(
        _direct(workbook, "PLNT23", second)
    )


def test_mirror_self_invalidates_when_workbook_changes(workbook):
    """A changed workbook must never be served from the old mirror."""
    usecols = ["ORISPL", "HTIAN", "UNTYRONL"]
    stale_mirror = _mirror_path(workbook, "UNT23", usecols)
    read_egrid_sheet(workbook, "UNT23", usecols)
    assert stale_mirror.exists()

    revised = _synthetic_unt23()
    revised.loc[0, "HTIAN"] = 9.99e9
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        descriptive = pd.DataFrame([[f"Description of {c}" for c in _UNT23_COLUMNS]])
        descriptive.to_excel(writer, sheet_name="UNT23", index=False, header=False)
        revised[_UNT23_COLUMNS].to_excel(
            writer, sheet_name="UNT23", index=False, startrow=1
        )

    assert _mirror_path(workbook, "UNT23", usecols) != stale_mirror
    fresh = read_egrid_sheet(workbook, "UNT23", usecols)
    assert fresh.equals(_direct(workbook, "UNT23", usecols))
    assert fresh.loc[0, "HTIAN"] == pytest.approx(9.99e9)


def test_corrupt_mirror_falls_back_to_the_workbook(workbook, caplog):
    """An unreadable mirror degrades to the xlsx parse instead of failing."""
    sheet, usecols = SOLVE_PATH_READS[2]
    read_egrid_sheet(workbook, sheet, usecols)
    _mirror_path(workbook, sheet, usecols).write_bytes(b"not a parquet file")

    with caplog.at_level(logging.WARNING, logger="market_sim.data.egrid_sheets"):
        recovered = read_egrid_sheet(workbook, sheet, usecols)

    assert recovered.equals(_direct(workbook, sheet, usecols))
    assert "mirror read failed" in caplog.text


def test_unwritable_mirror_directory_still_returns_the_frame(workbook, monkeypatch):
    """A mirror that cannot be written is a wall-clock loss, never an error."""
    sheet, usecols = SOLVE_PATH_READS[2]

    def _refuse(self, *args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _refuse)

    frame = read_egrid_sheet(workbook, sheet, usecols)
    assert frame.equals(_direct(workbook, sheet, usecols))
    assert not _mirror_path(workbook, sheet, usecols).exists()
    # No stray temp files left behind by the failed write.
    assert not list(workbook.parent.glob("*.tmp"))


def test_digest_is_byte_compatible_with_the_a2_implementation(workbook):
    """The shared digest must reproduce A-2's inline one, character for character.

    Wall-clock item A-4 extracted the hashing primitive into
    :mod:`market_sim.data.disk_memo` so the sheet mirror and the mapping memos
    hash identically instead of twice. The extraction is only free if it leaves
    the mirror *file names* untouched — otherwise every machine silently
    re-parses the 21 MB workbook once more and A-2's measured win is spent
    again. The frozen A-2 body below is the oracle.
    """
    import hashlib

    for sheet, usecols in SOLVE_PATH_READS:
        # Rebuild A-2's exact parameter tuple: (sheet, str(_SKIPROWS), *usecols).
        expected = hashlib.sha256()
        with workbook.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                expected.update(chunk)
        for part in (sheet, str(_SKIPROWS), *usecols):
            expected.update(f"{len(part)}:{part}".encode())
        assert _workbook_digest(workbook, sheet, usecols) == (expected.hexdigest()[:16])
        # ...and the name the mirror is stored under is that digest.
        assert _mirror_path(workbook, sheet, usecols).name == (
            f"{workbook.stem}.{expected.hexdigest()[:16]}.{sheet}.parquet"
        )
