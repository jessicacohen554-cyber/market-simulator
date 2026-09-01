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


# --- the CLASS-LEVEL carve-out (audit checklist item 10, 2026-09-01) --------
# `classify_prereg_artifact` replaced 31 hand-maintained allowlist entries with
# a two-conjunct structural test. These tests pin BOTH conjuncts and, just as
# importantly, everything the class must REFUSE — a classifier with no
# refusal tests is how the next 40-entry allowlist starts.


def _bundle(repo, name, files):
    """Write a results/calibration/<name> dir holding ``files`` {relpath: text}."""
    d = repo / "results" / "calibration" / name
    d.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        target = d / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return d


def _record(repo, name, text):
    """Write a committed record doc under results/calibration/."""
    (repo / "results" / "calibration").mkdir(parents=True, exist_ok=True)
    (repo / "results" / "calibration" / name).write_text(text)


def test_class_r_recipe_dir_is_admitted(tmp_path):
    """A meta.json-only dir named by a committed record is class R."""
    repo = _fake_repo(tmp_path)
    _bundle(repo, "nyiso999_armX_recipe", {"meta.json": "{}"})
    _record(
        repo,
        "PREREG-x.md",
        "--replay-bundle results/calibration/nyiso999_armX_recipe\n",
    )
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []
    assert swept == 1
    reason = crpp.classify_prereg_artifact(
        repo / "results" / "calibration" / "nyiso999_armX_recipe",
        crpp.record_corpus(repo),
    )
    assert reason is not None and reason.startswith("class R")


def test_class_r_requires_a_citation(tmp_path):
    """An UNCITED recipe dir still fails — conjunct (2) is load-bearing."""
    repo = _fake_repo(tmp_path)
    _bundle(repo, "nyiso999_armX_recipe", {"meta.json": "{}"})
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert len(problems) == 1
    assert "nyiso999_armX_recipe" in problems[0]


def test_class_r_refuses_a_dir_holding_more_than_meta(tmp_path):
    """Class R is `meta.json` ONLY — a second file takes it out of the class."""
    repo = _fake_repo(tmp_path)
    _bundle(repo, "nyiso999_armX_recipe", {"meta.json": "{}", "notes.txt": "x"})
    _record(repo, "PREREG-x.md", "results/calibration/nyiso999_armX_recipe\n")
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert len(problems) == 1


def test_class_p_campaign_point_is_admitted(tmp_path):
    """A point-score marker named by a committed record is class P."""
    repo = _fake_repo(tmp_path)
    _bundle(
        repo,
        "ercot999_r3",
        {"ercot999_point_score.json": "{}", "official_2023.json": "{}"},
    )
    _record(
        repo, "PRECOMMIT-x.md", "each point keeps its `ercot999_point_score.json`\n"
    )
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []
    assert swept == 1
    reason = crpp.classify_prereg_artifact(
        repo / "results" / "calibration" / "ercot999_r3", crpp.record_corpus(repo)
    )
    assert reason is not None and reason.startswith("class P")


def test_class_p_requires_the_marker_to_be_cited(tmp_path):
    """A point-score marker no committed record names does not admit the dir."""
    repo = _fake_repo(tmp_path)
    _bundle(repo, "ercot999_r3", {"ercot999_point_score.json": "{}"})
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert len(problems) == 1


def test_solve_output_is_never_class_admitted(tmp_path):
    """Conjunct (1): a cited dir carrying solve output still fails.

    This is what stops the carve-out becoming a blanket exemption — a real
    abandoned bundle always carries solve output, so it can never enter the
    class however thoroughly it is cited.
    """
    repo = _fake_repo(tmp_path)
    for name, extra in (
        ("dead_metrics", {"metrics.json": "{}"}),
        ("dead_attest", {"calibration_attestation.json": "{}"}),
        ("dead_diag", {"legitimacy_diagnostics.json": "{}"}),
        ("dead_parquet", {"hourly/system_2023.parquet": "x"}),
    ):
        _bundle(repo, name, {"meta.json": "{}", **extra})
        _record(repo, f"RESULT-{name}.md", f"results/calibration/{name}\n")
    problems, swept = crpp.check_bundle_retention({}, repo=repo)
    assert swept == 4
    assert len(problems) == 4


def test_citation_must_be_a_whole_identifier(tmp_path):
    """`ercot999_r1` is not excused by a record that only names `ercot999_r10`.

    Without the delimiter guard a pruned grid point would inherit its
    neighbour's citation.
    """
    repo = _fake_repo(tmp_path)
    _bundle(repo, "ercot999_r1", {"meta.json": "{}"})
    _record(repo, "PRECOMMIT-x.md", "the winner is results/calibration/ercot999_r10\n")
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert len(problems) == 1
    assert "ercot999_r1:" in problems[0]


def test_empty_dir_is_never_class_admitted(tmp_path):
    """An empty dir is litter, not a pre-registered artifact."""
    repo = _fake_repo(tmp_path, dirs=["empty_E"])
    _record(repo, "RESULT-x.md", "results/calibration/empty_E\n")
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert len(problems) == 1


def test_docs_root_also_counts_as_a_committed_record(tmp_path):
    """The ERCOT campaign records live under docs/, so that root must count."""
    repo = _fake_repo(tmp_path)
    _bundle(repo, "ercot999_r3", {"ercot999_point_score.json": "{}"})
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "PRECOMMIT-x.md").write_text("`ercot999_point_score.json`\n")
    problems, _ = crpp.check_bundle_retention({}, repo=repo)
    assert problems == []


def test_live_allowlist_holds_only_uncoverable_residue():
    """Every remaining named entry must be one the class genuinely cannot cover.

    The point of item 10 is that the allowlist stops absorbing artifacts the
    classifier can recognise. If an entry here IS class-admissible it should
    have been retired, and this test says so.
    """
    corpus = crpp.record_corpus()
    calib = crpp.REPO / "results" / "calibration"
    redundant = [
        name
        for name in crpp.KEEP_REQUIRED_UNMAPPED_BUNDLES
        if (calib / name).is_dir()
        and crpp.classify_prereg_artifact(calib / name, corpus) is not None
    ]
    assert redundant == []


def test_live_allowlist_has_no_entry_for_an_absent_dir():
    """A named dir that no longer exists is the 're-armable hole' the list warns of.

    `nyiso147_control` sat here after its dir was gone; this stops the next one.
    """
    calib = crpp.REPO / "results" / "calibration"
    if not calib.is_dir():  # partial checkout
        return
    absent = sorted(
        name
        for name in crpp.KEEP_REQUIRED_UNMAPPED_BUNDLES
        if not (calib / name).is_dir()
    )
    assert absent == []
