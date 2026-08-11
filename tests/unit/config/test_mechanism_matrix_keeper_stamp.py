"""Rule 28 [R-MECH-MATRIX] keeper-stamp guard in ``check_mechanism_matrix.py``.

Each per-ISO matrix shard (``docs/codebase-site/data/mechanism-matrix/<ISO>.js``
since the 2026-08-11 HOUSE-3 sharding; previously the monolith's ``keepers:``
header map) carries a ``keeper:`` stamp that rule 28 requires the promoting
session to re-stamp whenever an ISO's keeper changes. Nothing checked it
against the authoritative per-ISO shard
(``frontend/data/backcast/keepers/<ISO>.json``), so three ISOs drifted at once
(nyiso-105 missed its stamp; ERCOT and CAISO sat on 2026-07-29 ids after
2026-07-31 promotions) and every one passed CI. These cover the comparison and
the deliberate warn/fail split: pre-existing drift belongs to the owning ISO's
lane and only warns, while a PR that itself moves a keeper shard must re-stamp
its ISO's matrix shard.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from check_mechanism_matrix import (  # noqa: E402
    keeper_drift,
    load_store,
    matrix_isos,
    matrix_keepers,
    shard_keeper,
)

MATRIX_PATH = REPO / "docs/codebase-site/data/mechanism-matrix.js"
ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")


def _stamps() -> dict[str, str]:
    _base, shards, errors = load_store()
    assert not errors, errors
    return matrix_keepers(shards)


def test_matrix_isos_parses_all_six() -> None:
    """The base `isos:` list is the display/cell order; all six present."""
    assert matrix_isos(MATRIX_PATH.read_text(encoding="utf-8")) == list(ISOS)


def test_matrix_keepers_stamps_every_iso() -> None:
    """Every ISO's matrix shard stamps a non-empty keeper id."""
    stamps = _stamps()
    assert set(stamps) == set(ISOS)
    assert all(stamps[iso] for iso in ISOS)


def test_every_iso_has_a_readable_keeper_shard() -> None:
    """Each ISO's keeper shard exists and names a keeper (the guard's authority)."""
    for iso in ISOS:
        assert shard_keeper(iso), f"{iso} keeper shard missing or has no `keeper`"


def test_nyiso_matrix_stamp_matches_its_keeper_shard() -> None:
    """NYISO specifically — the stamp nyiso-105 missed and nyiso-106 restored."""
    assert _stamps()["NYISO"] == shard_keeper("NYISO")


def test_keeper_drift_reports_iso_stamp_and_shard() -> None:
    """A mismatched matrix stamp yields that ISO's `(iso, stamp, shard)` triple.

    Scoped to NYISO rather than asserting the whole list: other ISOs may carry
    their own live drift, and that is their lane's to clear, not this test's
    to encode.
    """
    stamps = _stamps()
    real = shard_keeper("NYISO")
    stamps["NYISO"] = "2020-01-01-not-a-real-keeper"
    nyiso = [row for row in keeper_drift(stamps) if row[0] == "NYISO"]
    assert nyiso == [("NYISO", "2020-01-01-not-a-real-keeper", real)]


def test_keeper_drift_empty_when_all_stamps_agree() -> None:
    """Drift is reported per ISO, so an ISO whose stamp agrees never appears."""
    assert all(iso != "NYISO" for iso, _h, _s in keeper_drift(_stamps()))
