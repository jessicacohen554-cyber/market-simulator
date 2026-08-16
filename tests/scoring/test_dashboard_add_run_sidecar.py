"""Regression tests for the dashboard_add_run metrics-sidecar path fix.

The ercot-193 tooling defect (docs/calibration-log/ercot.md, ercot-193
"Disclosures"; results/calibration/FINDING-ercot193-soc-regate-2026-08-13.md
§4): ``scripts/dashboard_add_run.py`` used the raw CLI ``--bundle`` path, so a
relative bundle argument composed against the process CWD instead of the repo
root — run from outside the repo root the ``metrics.json`` sidecar landed
under the CWD, and even from the repo root the relative path broke the
``relative_to(REPO)`` completion message, which the best-effort handler
misreported as ``determination: unavailable``. These tests pin the fix
(``dashboard_add_run.resolve_bundle`` + its use in ``main``) on a tmp-dir
fake repo from a non-repo CWD: no network, no real bundle, no writes into the
checkout.
"""

import json
import sys

from scripts import calibration_verdict as cv
from scripts import dashboard_add_run as dar

RUN_ID = "2099-01-01-tb1"

# Minimal synthetic verdict carrying every key condensed_metrics / headline
# read — no scorer run, no committed artifacts.
VERDICT = {
    "run_id": RUN_ID,
    "iso": "ERCOT",
    "label": "tb1",
    "target_years": [2024],
    "scorable_years": [2024],
    "data_blocked_years": [],
    "rubric_version": 1,
    "determination": "NOT-YET",
    "reasons": [],
    "notes": [],
    "criteria": {},
    "caveats": [],
    "grade_summary": None,
    "free_class_score": None,
}


def test_resolve_bundle_anchors_relative_at_repo_root(tmp_path, monkeypatch):
    """Relative --bundle paths anchor at the repo root, not the CWD."""
    fake_repo = tmp_path / "repo"
    bundle = fake_repo / "results" / "calibration" / "tb1"
    bundle.mkdir(parents=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr(dar, "REPO", fake_repo)

    resolved = dar.resolve_bundle("results/calibration/tb1")
    assert resolved.is_absolute()
    assert resolved == bundle
    # Absolute paths pass through untouched.
    assert dar.resolve_bundle(bundle) == bundle


def test_metrics_sidecar_lands_in_bundle_dir_not_cwd(tmp_path, monkeypatch, capsys):
    """main() run from a non-repo CWD writes metrics.json into the bundle dir.

    The old behavior composed the relative --bundle against the CWD: with a
    same-named decoy tree under the CWD (present here so the meta.json guard
    passes exactly as it did at ercot-193), the sidecar landed in the decoy
    and the completion message failed relative_to(REPO), surfacing as
    ``determination: unavailable``.
    """
    fake_repo = tmp_path / "repo"
    bundle = fake_repo / "results" / "calibration" / "tb1"
    bundle.mkdir(parents=True)
    (bundle / "meta.json").write_text('{"iso": "ERCOT"}\n')
    registry = fake_repo / "frontend" / "data" / "backcast" / "registry"

    cwd = tmp_path / "elsewhere"
    decoy = cwd / "results" / "calibration" / "tb1"
    decoy.mkdir(parents=True)
    (decoy / "meta.json").write_text('{"iso": "ERCOT"}\n')

    monkeypatch.chdir(cwd)
    monkeypatch.setattr(dar, "REPO", fake_repo)
    monkeypatch.setattr(dar, "REGISTRY_DIR", registry)
    monkeypatch.setattr(dar, "CALIB_ROOT", fake_repo / "results" / "calibration")

    entry = {"id": RUN_ID, "iso": "ERCOT", "label": "tb1", "years": [2024]}
    monkeypatch.setattr(dar.rb, "manifest_entry", lambda label, b: dict(entry))
    monkeypatch.setattr(dar.rb, "generate", lambda runs, years=None: None)
    # main() imports the canonical scripts.calibration_verdict (the bare-name
    # sibling import was converted 2026-08-16); stub only the scorer so the
    # real headline/write_metrics_sidecar paths run without committed
    # artifacts to read.
    monkeypatch.setattr(cv, "determine", lambda rid: dict(VERDICT))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "dashboard_add_run.py",
            "--label",
            "tb1",
            "--bundle",
            "results/calibration/tb1",
            "--no-prune",
        ],
    )

    dar.main()

    written = bundle / "metrics.json"
    assert written.exists(), "metrics sidecar must land in the bundle dir"
    assert not (decoy / "metrics.json").exists(), (
        "metrics sidecar must not land under the CWD"
    )
    assert json.loads(written.read_text())["run_id"] == RUN_ID
    assert (registry / f"{RUN_ID}.json").exists()

    out = capsys.readouterr().out
    assert "determination: unavailable" not in out
    assert "wrote results/calibration/tb1/metrics.json" in out
