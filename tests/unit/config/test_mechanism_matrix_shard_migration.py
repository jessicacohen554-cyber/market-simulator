"""Byte-faithfulness gate for the HOUSE-3 mechanism-matrix shard migration.

The 2026-08-11 migration split ``docs/codebase-site/data/mechanism-matrix.js``
(one six-char ``cells`` string per row, position = ISO — the shape that made a
PJM lane and a MISO lane edit the same character of the same line) into a
mechanism-level base file plus one shard per ISO
(``mechanism-matrix/<ISO>.js``), mirroring the 2026-07-19 keeper sharding
(``frontend/data/backcast/keepers/README.md``).

The migration is MECHANICAL, NOT EDITORIAL, and this module is the standing
proof: the pre-shard monolith is frozen as a fixture
(``tests/fixtures/mechanism_matrix_preshard_2026-08-11.js.gz``), and the same
committed transform that produced the shards (``split_monolith``) must, when
round-tripped through the same committed assembly (``assemble`` — the Python
twin of the page's ``mechanism-matrix-assemble.js``), reproduce the pre-shard
content EXACTLY, per mechanism × ISO — verdict characters and citations alike.
A verdict that moves during this round-trip is stop-the-line, never something
to fix in passing.

At migration time the committed shard files were verified equal to
``split_monolith(fixture)`` output (recorded in
``docs/handoffs/house-3-matrix-shard-2026-08-11.md``); the LIVE store is not
compared against the fixture here because future lanes legitimately edit
verdicts — the live store's integrity is ``check_mechanism_matrix.py``'s job,
exercised by ``test_live_store_parses_and_covers_every_mechanism`` below.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from scripts.lib import mech_matrix as mm  # noqa: E402

FIXTURE = REPO / "tests/fixtures/mechanism_matrix_preshard_2026-08-11.js.gz"


def _preshard_text() -> str:
    return gzip.decompress(FIXTURE.read_bytes()).decode("utf-8")


def _split_and_assemble(text: str):
    """The committed migration transform, round-tripped: split → parse → merge."""
    base_text, shard_texts = mm.split_monolith(text)
    base = mm.parse_assignment(base_text, "window.MECH_MATRIX").value
    shards = {
        iso: mm.parse_assignment(t, f"window.MECH_MATRIX_SHARDS.{iso}").value
        for iso, t in shard_texts.items()
    }
    return mm.assemble(base, shards)


def test_split_then_assemble_reproduces_the_preshard_matrix_exactly() -> None:
    """Every mechanism × ISO: cell verdict, fc posture and citation survive."""
    orig = mm.parse_assignment(_preshard_text(), "window.MECH_MATRIX").value
    merged = _split_and_assemble(_preshard_text())
    assert mm.canonical(merged) == mm.canonical(orig)


def test_no_verdict_character_moves_row_by_row() -> None:
    """The cells/fc strings themselves are reproduced verbatim, row by row.

    ``canonical()`` already implies this; asserting the raw strings keeps the
    failure message legible (it names the row and shows both six-char strings).
    """
    orig = mm.parse_assignment(_preshard_text(), "window.MECH_MATRIX").value
    merged = _split_and_assemble(_preshard_text())
    merged_rows = {r["id"]: r for r in merged["rows"]}
    assert len(orig["rows"]) == len(merged_rows)
    for row in orig["rows"]:
        got = merged_rows[row["id"]]
        assert got["cells"] == row["cells"], row["id"]
        if "fc" in row:
            assert got.get("fc") == row["fc"], row["id"]


def test_no_citation_is_deleted() -> None:
    """Every pre-shard `ev` value survives, keyed to the same ISO (or, for the
    cross-ISO keys like `All`, kept on the base row). Legacy key spellings
    (`MISO`→`M`, `NE`→`Q`) normalize in the KEY only — values byte-identical.
    """
    orig = mm.parse_assignment(_preshard_text(), "window.MECH_MATRIX").value
    merged_rows = {r["id"]: r for r in _split_and_assemble(_preshard_text())["rows"]}
    for row in orig["rows"]:
        want = {
            mm.EV_KEY_ALIASES.get(k, k): v for k, v in (row.get("ev") or {}).items()
        }
        got = merged_rows[row["id"]].get("ev") or {}
        assert got == want, row["id"]


def test_keeper_and_gates_stamps_survive_per_iso() -> None:
    orig = mm.parse_assignment(_preshard_text(), "window.MECH_MATRIX").value
    merged = _split_and_assemble(_preshard_text())
    assert merged["keepers"] == orig["keepers"]
    assert merged["gates"] == orig["gates"]
    assert merged["isos"] == orig["isos"]


def test_fixture_matches_known_migration_facts() -> None:
    """Pin the fixture's identity so a swapped fixture can't hollow the proof."""
    orig = mm.parse_assignment(_preshard_text(), "window.MECH_MATRIX").value
    assert len(orig["rows"]) == 211
    # The fixture is the FROZEN pre-shard monolith, so its ISO list is pinned to
    # the six that existed on 2026-08-11 — literally, not against mm.ISO_ORDER,
    # which legitimately grows as ISOs are registered (SPP joined at SPP-21,
    # 2026-09-06; SOCO at SOCO-21, 2026-09-13). Comparing to the live tuple would
    # make a new ISO look like a swapped fixture, which is the opposite of what
    # this test is pinning.
    assert orig["isos"] == ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
    by_id = {r["id"]: r for r in orig["rows"]}
    assert by_id["use_campd_bins"]["cells"] == "KKKKKK"
    assert by_id["ordc_scarcity_overlay"]["cells"] == "RKGG.K"


def test_live_store_parses_and_covers_every_mechanism() -> None:
    """The committed base + shards stay assemblable with full cell coverage."""
    merged = mm.load_merged(REPO)
    isos = merged["isos"]
    assert list(isos) == list(mm.ISO_ORDER)
    for row in merged["rows"]:
        assert len(row["cells"]) == len(isos), row["id"]
        assert set(row["cells"]) <= mm.CELL_CHARS, row["id"]
    # A keeper stamp is required of every ISO that HAS a keeper. An ISO whose
    # column is seeded before its first keeper exists (SPP, seeded at SPP-21
    # 2026-09-06; first keeper at SPP-40 — and SOCO, seeded at SOCO-21
    # 2026-09-13, first keeper at SOCO-40) carries an empty stamp by design — the
    # same fail-open scoping check_mechanism_matrix.keeper_drift already applies
    # when frontend/data/backcast/keepers/<ISO>.json is absent.
    for iso in isos:
        if not (REPO / f"frontend/data/backcast/keepers/{iso}.json").exists():
            continue
        assert merged["keepers"][iso], f"{iso} shard has no keeper stamp"


def test_python_and_browser_assemblers_stay_in_sync() -> None:
    """The JS assembler must implement the same fc-fallback + ev-letter rules.

    No JS runtime in CI, so this pins the CONTRACT textually: the browser twin
    declares the same ISO→letter map and the same cell-fallback for fc that
    ``mech_matrix.assemble`` implements. Weak on purpose — the real proof was
    the migration-time Node comparison recorded in the handoff.
    """
    js = (REPO / mm.ASSEMBLE_PATH).read_text(encoding="utf-8")
    for iso, letter in mm.ISO_EV_KEY.items():
        assert f"{iso}: '{letter}'" in js
    assert "fc += e.cell" in js  # per-ISO fc fallback = backcast cell
