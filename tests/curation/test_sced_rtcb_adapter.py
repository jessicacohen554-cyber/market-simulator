"""The RTC+B SCED read adapter and the delivery-2025-12-04 lane boundary.

Authority: ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md``
card D, signature D1 — a READ adapter, nothing more.

**Fixtures are real part excerpts, not synthetic frames.** Three excerpts under
``tests/fixtures/sced_rtcb/`` carry the full column inventory of their source
part (so the schema break is exercised verbatim) at ~70 rows each. Selection
rule, applied to the source part in original row order and deduplicated:
the first 50 rows, plus the first 20 rows carrying a non-zero AS quantity
(``AS Awards NSPIN`` for RTC+B, ``Ancillary Service NSRS`` for pre-RTC+B).
Sources, all immutable raw (never modified in place):

* ``rtcb_193col_pub2026-02.part0002`` — ``data/raw/ercot/SCED/rtcb-format-2026/
  2026-02.part0002.parquet``, delivery 2025-12-05, the 193-column variant.
* ``rtcb_195col_pub2026-03.part0000`` — ``.../rtcb-format-2026/
  2026-03.part0000.parquet``, delivery 2025-12-31, the 195-column variant.
* ``legacy_188col_pub2026-02.part0001`` — ``data/raw/ercot/SCED/
  2026-02.part0001.parquet``, delivery 2025-12-04: the last pre-RTC+B delivery
  day, i.e. the boundary's readable side.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from scripts.data import derive_ercot_sced_offer_wall as wall
from scripts.lib import sced_corpus_instruments as instruments
from scripts.lib import sced_rtcb_adapter as adapter

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sced_rtcb"
RTCB_193 = FIXTURES / "rtcb_193col_pub2026-02.part0002.excerpt.parquet"
RTCB_195 = FIXTURES / "rtcb_195col_pub2026-03.part0000.excerpt.parquet"
LEGACY_188 = FIXTURES / "legacy_188col_pub2026-02.part0001.excerpt.parquet"


# --------------------------------------------------------------------------
# The format break itself, measured off the fixtures
# --------------------------------------------------------------------------


def test_fixtures_bracket_the_boundary():
    """The three fixtures are the two sides of delivery 2025-12-04/05."""
    legacy = adapter.delivery_timestamps(pd.read_parquet(LEGACY_188))
    assert legacy.dt.date.max() == adapter.PRE_RTCB_LAST_DELIVERY
    for part in (RTCB_193, RTCB_195):
        rtcb = adapter.delivery_timestamps(pd.read_parquet(part))
        assert rtcb.dt.date.min() >= adapter.RTCB_FIRST_DELIVERY


def test_column_inventory_matches_the_documented_break():
    """The adapter's REMOVED/RENAMED/SUPERSEDED tables are what the data says."""
    legacy = set(pq.ParquetFile(LEGACY_188).schema_arrow.names)
    rtcb = set(pq.ParquetFile(RTCB_193).schema_arrow.names)

    gone = legacy - rtcb
    accounted = (
        set(adapter.REMOVED_COLUMNS)
        | set(adapter.SUPERSEDED_COLUMNS)
        | set(adapter.RENAMED_COLUMNS.values())
    )
    assert gone == accounted, "an unaccounted column changed across the break"
    assert set(adapter.REMOVED_COLUMNS) == {"HASL", "LASL"}
    # Every superseded column's declared successors really are in the RTC+B part.
    for legacy_name, successors in adapter.SUPERSEDED_COLUMNS.items():
        assert legacy_name in legacy
        assert set(successors) <= rtcb, legacy_name
    # The rename is a rename: the RTC+B spelling is present, the legacy one is not.
    for rtcb_name, canonical in adapter.RENAMED_COLUMNS.items():
        assert rtcb_name in rtcb and rtcb_name not in legacy
        assert canonical in legacy and canonical not in rtcb


@pytest.mark.parametrize("part,ncols", [(RTCB_193, 193), (RTCB_195, 195)])
def test_both_column_variants_parse_to_one_contract(part, ncols):
    """193- and 195-column parts both read, and agree on the shared contract."""
    assert len(pq.ParquetFile(part).schema_arrow.names) == ncols
    df = adapter.read_rtcb_part(part)
    assert len(df) > 0
    # The variant delta is additive (AS Capability RRSPF/RRSFF) — the shared
    # contract is identical, so a consumer reading canonical names is unaffected.
    shared = set(adapter.canonical_columns(RTCB_193)) & set(
        adapter.canonical_columns(RTCB_195)
    )
    assert set(adapter.canonical_columns(RTCB_193)) <= set(df.columns) | shared


def test_rtcb_reads_into_the_existing_frame_contract():
    """The canonical read columns of the corpus consumers all survive the break.

    ``HASL`` is the exception, and it is the whole reason for the quarantine —
    it is asserted absent, not present-and-NaN, by the next test.
    """
    df = adapter.read_rtcb_part(RTCB_193)
    contract = [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "Output Schedule",
        "HSL",
        "HDL",
        "LSL",
        "LDL",
        "Base Point",
        "Telemetered Net Output ",  # served under the canonical spelling
        *[f"SCED2 Curve-MW{i}" for i in (1, 35)],
        *[f"SCED2 Curve-Price{i}" for i in (1, 35)],
        *[f"Submitted TPO-MW{k}" for k in (1, 10)],
        *[f"Submitted TPO-Price{k}" for k in (1, 10)],
    ]
    missing = [c for c in contract if c not in df.columns]
    assert not missing, missing
    # Contract-identical dtype: the verbatim all-string CSV copy, uncoerced.
    assert str(df["HSL"].dtype) == str(pd.read_parquet(LEGACY_188)["HSL"].dtype)


# --------------------------------------------------------------------------
# Contract promise 1 — removed columns are ABSENT, never NaN-filled
# --------------------------------------------------------------------------


@pytest.mark.parametrize("part", [RTCB_193, RTCB_195])
def test_removed_columns_are_absent_not_nan_filled(part):
    df = adapter.read_rtcb_part(part)
    for name in adapter.REMOVED_COLUMNS:
        assert name not in df.columns
    for name in adapter.SUPERSEDED_COLUMNS:
        assert name not in df.columns
    # Nothing was invented: no column is wholly null in the returned frame.
    assert not any(df[c].isna().all() for c in df.columns)


@pytest.mark.parametrize("name", ["HASL", "LASL"])
def test_requesting_a_removed_column_raises(name):
    with pytest.raises(adapter.ScedFormatBreakError) as e:
        adapter.read_rtcb_part(RTCB_193, columns=["SCED Time Stamp", name])
    msg = str(e.value)
    assert name in msg and "NOT NaN-filled" in msg


@pytest.mark.parametrize("name", sorted(adapter.SUPERSEDED_COLUMNS))
def test_requesting_a_superseded_column_raises_and_names_successors(name):
    with pytest.raises(adapter.ScedFormatBreakError) as e:
        adapter.read_rtcb_part(RTCB_193, columns=[name])
    msg = str(e.value)
    assert name in msg
    for successor in adapter.SUPERSEDED_COLUMNS[name]:
        assert successor in msg


def test_unknown_column_raises_rather_than_nan_filling():
    with pytest.raises(adapter.ScedFormatBreakError, match="not NaN-filled"):
        adapter.read_rtcb_part(RTCB_193, columns=["No Such Column"])


def test_superseded_as_block_is_served_under_its_rtcb_names():
    """The refusal is scoped: the RTC+B-native columns ARE readable."""
    df = adapter.read_rtcb_part(
        RTCB_193, columns=["AS Awards NSPIN", "AS Capability REGUP", "Ramp Rate Up"]
    )
    assert list(df.columns) == [
        "AS Awards NSPIN",
        "AS Capability REGUP",
        "Ramp Rate Up",
        adapter.SCED_FORMAT_COLUMN,
    ]


# --------------------------------------------------------------------------
# Contract promise 2 — a format flag on every row
# --------------------------------------------------------------------------


@pytest.mark.parametrize("part", [RTCB_193, RTCB_195])
def test_format_flag_on_every_row(part):
    df = adapter.read_rtcb_part(part)
    assert (df[adapter.SCED_FORMAT_COLUMN] == adapter.FORMAT_RTCB).all()
    assert df[adapter.SCED_FORMAT_COLUMN].notna().all()


def test_multi_part_read_flags_every_row_and_uses_the_intersection():
    df = adapter.read_rtcb(paths=[RTCB_193, RTCB_195])
    assert len(df) == len(pd.read_parquet(RTCB_193)) + len(pd.read_parquet(RTCB_195))
    assert (df[adapter.SCED_FORMAT_COLUMN] == adapter.FORMAT_RTCB).all()
    # The 195-only columns are dropped by the intersection, not NaN-filled.
    assert "AS Capability RRSPF" not in df.columns


# --------------------------------------------------------------------------
# THE BOUNDARY — RTC+B rows must never reach a delivery-2023..2025 lane
# --------------------------------------------------------------------------


# Publication months laid down in the miniature corpus. ``_sced_source_files``
# only lets a publication-month corpus supersede the legacy sample-day extracts
# once it majority-covers the delivery year (``_CORPUS_MIN_DELIVERY_MONTHS`` = 7
# of 12; delivery month M publishes at M+2). Nine months of the delivery-2025
# window clears that, so the test exercises the real corpus branch rather than
# the legacy fallback. The selector reads FILENAMES, so every shard is the same
# real pre-RTC+B excerpt under its publication-month name.
_PUB_MONTHS = (
    "2025-06",
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
)


def _corpus_with_quarantine(root: Path) -> Path:
    """A miniature corpus: pre-RTC+B parts + the RTC+B quarantine subdir."""
    sced = root / "SCED"
    (sced / adapter.RTCB_DIR.name).mkdir(parents=True)
    for month in _PUB_MONTHS:
        shutil.copy(LEGACY_188, sced / f"{month}.part0001.parquet")
    shutil.copy(RTCB_193, sced / adapter.RTCB_DIR.name / "2026-02.part0002.parquet")
    shutil.copy(RTCB_195, sced / adapter.RTCB_DIR.name / "2026-03.part0000.parquet")
    return sced


def test_delivery_year_filter_alone_would_NOT_stop_rtcb_rows(tmp_path):
    """Why the directory quarantine is load-bearing, pinned as a fact.

    RTC+B deliveries are 2025-12-05..31 — inside delivery year 2025 — so the
    lanes' own row filter keeps them. Only the subdirectory keeps them out.
    """
    rtcb = pd.read_parquet(RTCB_195)
    kept = wall._delivery_year_rows(rtcb, 2025)
    assert len(kept) == len(rtcb), (
        "if this ever fails the boundary story changed: the delivery-year "
        "filter is NOT what excludes RTC+B rows"
    )


def test_wall_deriver_file_selection_never_reaches_the_quarantine(
    tmp_path, monkeypatch
):
    """``_sced_source_files`` — the selector behind the wall, faststart, steam
    and shoulder-span derives — cannot see the quarantined parts."""
    sced = _corpus_with_quarantine(tmp_path)
    monkeypatch.setattr(wall, "SCED_DIR", tmp_path)
    monkeypatch.setattr(wall, "_CORPUS_DIRS", (tmp_path, sced))
    # 2026-02/2026-03 publications fall inside delivery-2025's selection window,
    # so the window is NOT what excludes them.
    lo, hi = 2025 * 12 + 1, 2026 * 12 + 2
    assert lo <= 2026 * 12 + 1 <= hi and lo <= 2026 * 12 + 2 <= hi

    selected = wall._sced_source_files(2025)
    names = {p.name for p in selected}
    assert names == {f"{m}.part0001.parquet" for m in _PUB_MONTHS}, (
        "the readable side must still load, in full"
    )
    assert not any(adapter.RTCB_DIR.name in p.parts for p in selected)
    adapter.assert_pre_rtcb_files(selected)


def test_corpus_instruments_glob_never_reaches_the_quarantine(tmp_path):
    """``sced_corpus_instruments`` globs the corpus root non-recursively."""
    sced = _corpus_with_quarantine(tmp_path)
    selected = sorted(sced.glob("*.parquet"))  # the module's own expression
    assert [p.name for p in selected] == [f"{m}.part0001.parquet" for m in _PUB_MONTHS]
    adapter.assert_pre_rtcb_files(selected)
    # ...and the module still points at the real corpus root, not the quarantine.
    assert instruments.SCED_CORPUS_DIR.name != adapter.RTCB_DIR.name
    assert adapter.RTCB_DIR.parent == instruments.SCED_CORPUS_DIR


def test_assert_pre_rtcb_files_rejects_a_quarantined_part(tmp_path):
    sced = _corpus_with_quarantine(tmp_path)
    leaked = sorted((sced / adapter.RTCB_DIR.name).glob("*.parquet"))
    with pytest.raises(adapter.ScedQuarantineLeakError, match="RTC\\+B-format part"):
        adapter.assert_pre_rtcb_files(leaked)


def test_assert_no_rtcb_rows_separates_the_two_sides():
    adapter.assert_no_rtcb_rows(pd.read_parquet(LEGACY_188), where="legacy fixture")
    for part in (RTCB_193, RTCB_195):
        with pytest.raises(adapter.ScedQuarantineLeakError, match="2025-12-05"):
            adapter.assert_no_rtcb_rows(pd.read_parquet(part), where=part.name)
    adapter.assert_no_rtcb_rows(pd.DataFrame())  # empty is vacuously clean


def test_adapter_never_registers_the_quarantine_as_a_corpus_root():
    """A structural guard: the quarantine is a subdirectory of the corpus root,
    and no consumer's root tuple contains it."""
    assert adapter.RTCB_DIR.parent == adapter.SCED_CORPUS_DIR
    assert adapter.RTCB_DIR not in wall._CORPUS_DIRS
    assert instruments.SCED_CORPUS_DIR != adapter.RTCB_DIR


# --------------------------------------------------------------------------
# FENCE — no existing-lane behaviour change
# --------------------------------------------------------------------------


def test_pre_rtcb_read_is_identical_with_and_without_the_quarantine_present(
    tmp_path, monkeypatch
):
    """Byte-for-byte proof for the pre-2025-12-05 corpus.

    The same pre-RTC+B corpus is read twice through the existing lane — once
    with the RTC+B quarantine subdirectory present, once with it absent. The
    selected file list and the resulting frame must be identical, and the frame
    must be byte-identical when round-tripped to parquet.
    """
    frames, selections, digests = [], [], []
    for with_quarantine in (True, False):
        root = tmp_path / f"q{int(with_quarantine)}"
        sced = _corpus_with_quarantine(root)
        if not with_quarantine:
            shutil.rmtree(sced / adapter.RTCB_DIR.name)
        monkeypatch.setattr(wall, "SCED_DIR", root)
        monkeypatch.setattr(wall, "_CORPUS_DIRS", (root, sced))

        files = wall._sced_source_files(2025)
        selections.append([p.name for p in files])
        df = pd.concat(
            [
                wall._coerce_sced_numeric(
                    wall._delivery_year_rows(
                        pd.read_parquet(p, columns=wall._READ_COLS), 2025
                    )
                )
                for p in files
            ],
            ignore_index=True,
        )
        frames.append(df)
        out = root / "out.parquet"
        df.to_parquet(out, index=False)
        digests.append(out.read_bytes())

    assert selections[0] == selections[1]
    assert len(frames[0]) > 0, "the fixture corpus must actually produce rows"
    pd.testing.assert_frame_equal(frames[0], frames[1])
    assert digests[0] == digests[1], "pre-RTC+B output is not byte-identical"


def test_importing_the_adapter_mutates_no_consumer_state():
    """The adapter is additive: it rebinds nothing in the lanes it documents."""
    assert wall._CORPUS_DIRS == (wall.SCED_DIR, wall.SCED_DIR / "SCED")
    assert instruments.SCED_CORPUS_DIR == adapter.SCED_CORPUS_DIR
    assert "HASL" in wall._READ_COLS  # the required column that defines the break
