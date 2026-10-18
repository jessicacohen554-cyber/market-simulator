"""The SPP stale-snapshot DOF-ledger note is attested only under its epoch."""

from __future__ import annotations

import json

from scripts.build_dof_ledger import _SPP_STALE_SNAPSHOT_EPOCH, data_qa_entries


def _bundle(tmp_path, epochs):
    if epochs is not None:
        (tmp_path / "solve_surface.json").write_text(json.dumps({"epochs": epochs}))
    return tmp_path


def test_note_present_for_an_spp_bundle_solved_under_the_epoch(tmp_path):
    [entry] = data_qa_entries(_bundle(tmp_path, [_SPP_STALE_SNAPSHOT_EPOCH]), "SPP")
    assert entry["identification"] == "measured"
    assert "SPC" in entry["note"] and "150 MW" in entry["note"]


def test_no_note_for_an_older_bundle_or_another_iso(tmp_path):
    assert data_qa_entries(_bundle(tmp_path, None), "SPP") == []
    assert data_qa_entries(_bundle(tmp_path, ["2026-10-18a"]), "SPP") == []
    assert data_qa_entries(_bundle(tmp_path, [_SPP_STALE_SNAPSHOT_EPOCH]), "MISO") == []
