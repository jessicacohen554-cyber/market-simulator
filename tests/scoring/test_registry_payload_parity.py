"""Tests for the Class-E retention rule point-4 bundle sweep.

The rule (adopted 2026-08-16, closing BLOAT-2; text in
``frontend/data/backcast/keepers/README.md``) makes bundle linkage explicit:
retention deletes sidecar + payload + bundle together, so a top-level
``results/calibration/<bundle>`` directory that no retained sidecar's
``bundle`` field maps — and that is not keep-required — is dead solve output.
``check_registry_payload_parity.check_bundle_retention`` is the sweep that
fails it. These tests pin the sweep on a tmp-dir fake repo: the failing case,
every keep-required carve-out, the nested-path and outside-root safety
behaviors, and the partial-checkout guard. No network, no writes into the
checkout.
"""

import json

from scripts import check_registry_payload_parity as crpp


def _fake_repo(tmp_path, dirs=(), loose_files=()):
    """Create a fake repo root with the given results/calibration entries."""
    repo = tmp_path / "repo"
    calib = repo / "results" / "calibration"
    calib.mkdir(parents=True)
    for d in dirs:
        (calib / d).mkdir()
    for f in loose_files:
        (calib / f).write_text("loose record\n")
    return repo


def _sidecar(rid, bundle):
    return {"id": rid, "iso": "ERCOT", "bundle": bundle}


def test_unmapped_bundle_dir_fails(tmp_path):
    """A dir no retained sidecar maps, with no carve-out, is a problem."""
    repo = _fake_repo(tmp_path, dirs=["orphan_D"])
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert swept == 1
    assert len(problems) == 1
    assert "results/calibration/orphan_D" in problems[0]
    assert "Class-E retention rule point 4" in problems[0]


def test_sidecar_mapped_dir_passes(tmp_path):
    """A dir mapped by a retained sidecar's bundle field is clean."""
    repo = _fake_repo(tmp_path, dirs=["mapped_A"])
    sidecars = {"r1": _sidecar("r1", "results/calibration/mapped_A")}
    problems, swept = crpp.check_bundle_retention(sidecars, repo=repo)
    assert problems == []
    assert swept == 1


def test_nested_bundle_path_maps_its_top_level_dir(tmp_path):
    """A sidecar pointing at a nested path maps the top-level bundle dir."""
    repo = _fake_repo(tmp_path, dirs=["mapped_A"])
    (repo / "results" / "calibration" / "mapped_A" / "sub").mkdir()
    sidecars = {"r1": _sidecar("r1", "results/calibration/mapped_A/sub")}
    problems, _ = crpp.check_bundle_retention(sidecars, repo=repo)
    assert problems == []


def test_underscore_dirs_are_keep_required_and_not_swept(tmp_path):
    """The §5.2 `_`-prefixed working/archive dirs are outside the sweep."""
    repo = _fake_repo(tmp_path, dirs=["_archive", "_scratch"])
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []
    assert swept == 0


def test_loose_records_are_out_of_scope(tmp_path):
    """Root-level loose files (the finding record) are never examined."""
    repo = _fake_repo(tmp_path, loose_files=["FINDING-x-2026-01-01.md", "metrics.json"])
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []
    assert swept == 0


def test_regression_golden_reference_is_keep_required(tmp_path):
    """A dir a goldens manifest references in keepers.<ISO>.bundle is kept."""
    repo = _fake_repo(tmp_path, dirs=["golden_B"])
    capture = repo / "results" / "regression-goldens" / "tag-before"
    capture.mkdir(parents=True)
    (capture / "manifest.json").write_text(
        json.dumps({"keepers": {"ERCOT": {"bundle": "results/calibration/golden_B"}}})
    )
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []
    assert swept == 1


def test_unreadable_golden_manifest_never_widens_the_carve_out(tmp_path):
    """A corrupt capture record is skipped; the dir still fails."""
    repo = _fake_repo(tmp_path, dirs=["golden_B"])
    capture = repo / "results" / "regression-goldens" / "tag-before"
    capture.mkdir(parents=True)
    (capture / "manifest.json").write_text("{not json")
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert len(problems) == 1


def test_allowlist_entry_is_keep_required(tmp_path, monkeypatch):
    """A KEEP_REQUIRED_UNMAPPED_BUNDLES entry is excused (and only it)."""
    repo = _fake_repo(tmp_path, dirs=["allow_C", "orphan_D"])
    monkeypatch.setattr(crpp, "KEEP_REQUIRED_UNMAPPED_BUNDLES", frozenset({"allow_C"}))
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert swept == 2
    assert len(problems) == 1
    assert "orphan_D" in problems[0]


def test_bundle_outside_calibration_root_never_maps(tmp_path):
    """The bundle_dir_for safety guard: an outside-root field maps nothing.

    A sidecar whose ``bundle`` escapes ``results/calibration`` (the retention
    delete guard rejects it) must not excuse a same-named orphan dir — and
    must not crash the sweep.
    """
    repo = _fake_repo(tmp_path, dirs=["orphan_D"])
    sidecars = {
        "r1": _sidecar("r1", "results/hindcast/orphan_D"),
        "r2": _sidecar("r2", "../outside/orphan_D"),
        "r3": {"id": "r3", "iso": "ERCOT"},  # no bundle field at all
    }
    problems, _ = crpp.check_bundle_retention(sidecars, repo=repo)
    assert len(problems) == 1
    assert "orphan_D" in problems[0]


def test_missing_calibration_root_sweeps_nothing(tmp_path):
    """A partial checkout without results/calibration is not a failure."""
    repo = tmp_path / "repo"
    repo.mkdir()
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []
    assert swept == 0
