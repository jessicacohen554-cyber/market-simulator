"""Tests for the promotion-completeness check (owner ruling R-BF, 2026-09-25).

``scripts/check_promotion_completeness.py`` runs four legs, but only for the
ISOs whose keeper shard changed against the PR base:
(a) gate-(a) provenance, (b) the ``complete`` marker names the new keeper,
(c) FR-22 has 0 UNACCOUNTED, and (d) E13 is clean.

These tests pin three things. Each leg's pass and fail. The diff scoping: an
unchanged ISO is never checked, and a new shard counts as changed. And one live
run: the committed tree passes every leg for every current keeper.
"""

import json
import subprocess

from scripts import check_promotion_completeness as cpc

OLD = "2026-09-01-x-old"
NEW = "2026-09-25-x-new"


def _row(keeper, complete, status):
    return {
        "status": status,
        "detail": (
            f"keeper {keeper} (full-span 2023-2025); "
            f"marker complete={complete} final=False."
        ),
    }


def _status_doc(iso, row):
    return {"isos": {iso: {"gate": {"a_keeper_marker": row}}}}


def _complete_doc(iso, keeper=None):
    return {"complete": {iso: {"keeper": keeper}} if keeper else {}, "final": {}}


# --- leg (a) ---------------------------------------------------------------


def test_leg_a_passes_on_a_rekeyed_row():
    problems, notes = cpc.leg_a_gate(
        "PJM",
        NEW,
        _status_doc("PJM", _row(NEW, True, "pass")),
        _complete_doc("PJM", NEW),
    )
    assert problems == [] and notes == []


def test_leg_a_fails_on_a_row_citing_the_outgoing_keeper():
    problems, _ = cpc.leg_a_gate(
        "PJM",
        NEW,
        _status_doc("PJM", _row(OLD, True, "pass")),
        _complete_doc("PJM", NEW),
    )
    assert len(problems) == 1 and "SUPERSEDED" in problems[0]
    assert problems[0].startswith("(a) ")


def test_leg_a_notes_an_iso_with_no_board_row():
    problems, notes = cpc.leg_a_gate("SOCO", NEW, {"isos": {}}, _complete_doc("SOCO"))
    assert problems == []
    assert notes and "not applicable" in notes[0]


# --- leg (b) ---------------------------------------------------------------


def test_leg_b_silent_without_a_complete_entry():
    assert cpc.leg_b_marker("MISO", NEW, _complete_doc("MISO")) == []


def test_leg_b_passes_when_the_marker_names_the_new_keeper():
    assert cpc.leg_b_marker("PJM", NEW, _complete_doc("PJM", NEW)) == []


def test_leg_b_fails_when_the_marker_names_the_outgoing_keeper():
    problems = cpc.leg_b_marker("PJM", NEW, _complete_doc("PJM", OLD))
    assert len(problems) == 1 and OLD in problems[0] and NEW in problems[0]


# --- leg (d) ---------------------------------------------------------------


def _sidecar(reg, run_id, iso, stamped=None):
    rec = {"id": run_id, "iso": iso, "years": [2023, 2024, 2025]}
    if stamped:
        rec["holdout"] = {"keeper": stamped}
    (reg / f"{run_id}.json").write_text(json.dumps(rec))


def test_leg_d_passes_on_a_keeper_only_registered_set(tmp_path):
    _sidecar(tmp_path, NEW, "PJM")
    _sidecar(tmp_path, "2026-09-25-x-rung", "PJM", stamped=NEW)
    _sidecar(tmp_path, OLD, "MISO")  # another ISO's run is not this ISO's orphan
    assert cpc.leg_d_e13("PJM", NEW, tmp_path) == []


def test_leg_d_fails_when_the_outgoing_keeper_is_left_registered(tmp_path):
    _sidecar(tmp_path, NEW, "PJM")
    _sidecar(tmp_path, OLD, "PJM")
    problems = cpc.leg_d_e13("PJM", NEW, tmp_path)
    assert len(problems) == 1 and OLD in problems[0] and "E13" in problems[0]


# --- diff scoping ----------------------------------------------------------


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _shard(repo, iso, keeper):
    d = repo / cpc.KEEPERS_REL
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{iso}.json").write_text(json.dumps({"iso": iso, "keeper": keeper}))


def test_changed_isos_scopes_to_the_shards_whose_keeper_moved(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _shard(tmp_path, "PJM", OLD)
    _shard(tmp_path, "MISO", "2026-09-01-miso-same")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    _shard(tmp_path, "PJM", NEW)  # promoted
    _shard(tmp_path, "NWPP", "2026-09-25-nwpp-first")  # newly registered ISO
    changed = cpc.changed_isos(tmp_path, "HEAD")
    assert changed == {
        "PJM": (OLD, NEW),
        "NWPP": (None, "2026-09-25-nwpp-first"),
    }


def test_unresolvable_base_exits_2(tmp_path):
    _git(tmp_path, "init", "-q")
    _shard(tmp_path, "PJM", NEW)
    assert cpc.main(["--repo", str(tmp_path), "--base", "no-such-rev"]) == 2


# --- the committed tree ----------------------------------------------------


def test_every_current_keeper_passes_all_four_legs():
    """Each current keeper shard passes (a)-(d) on the committed tree."""
    isos = sorted(cpc.head_keepers(cpc.REPO))
    assert isos, "no keeper shards found"
    argv = []
    for iso in isos:
        argv += ["--iso", iso]
    assert cpc.main(argv) == 0
