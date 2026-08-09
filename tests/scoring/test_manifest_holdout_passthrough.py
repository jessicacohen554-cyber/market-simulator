"""The rule-22 ``holdout`` block must survive the sidecar -> manifest hop.

``scripts/stamp_touchpoint_holdout.py`` writes a ``holdout`` block onto a
touchpoint's registry sidecar, and the Run Explorer reads it twice:

* ``renderHoldoutPanel`` draws the in-sample-vs-holdout criterion table from
  ``st.runMeta.holdout`` — ``st.runMeta`` being the MANIFEST entry, not the
  sidecar; and
* ``holdoutCompanions`` follows ``holdout.keeper`` to decide which keeper may
  offer that held-out year in its year dropdown.

``build_manifest`` copies only the fields it enumerates, and ``holdout`` was
not among them until 2026-08-09 — so the block was committed on the sidecar and
silently dropped on the way to the page, leaving the touchpoint panel dead code
on the deployed dashboard. These tests pin the passthrough so it cannot be
dropped again by an edit to either tuple.
"""

from __future__ import annotations

import json

from scripts import build_manifest


def _sidecar(tmp_path, rid, iso, years, **extra):
    """Write a full-format sidecar + its run payload; return the record."""
    rec = {
        "id": rid,
        "label": rid[11:].replace("-", " "),
        "date": rid[:10],
        "shorthand": rid[11:],
        "definition": f"test run {rid}",
        "years": years,
        "iso": iso,
        "file": f"frontend/data/backcast/runs/{rid}.js",
        **extra,
    }
    (tmp_path / "registry").mkdir(exist_ok=True)
    (tmp_path / "runs").mkdir(exist_ok=True)
    (tmp_path / "registry" / f"{rid}.json").write_text(json.dumps(rec))
    (tmp_path / "runs" / f"{rid}.js").write_text("// payload")
    return rec


def _entries(tmp_path, monkeypatch):
    monkeypatch.setattr(build_manifest, "REGISTRY_DIR", tmp_path / "registry")
    monkeypatch.setattr(build_manifest, "RUNS_DIR", tmp_path / "runs")
    return {e["id"]: e for e in build_manifest._load_entries()}


HOLDOUT = {
    "tier": "validation",
    "year": 2022,
    "keeper": "2026-08-06-keeper-run",
    "keeperDetermination": "CALIBRATED-WITH-CAVEATS",
    "keeperYears": [2023, 2024, 2025],
    "holdoutDetermination": "CALIBRATED-WITH-CAVEATS",
    "criteria": [
        {
            "key": "price_mean",
            "label": "C3a mean LMP",
            "tier": "load-bearing",
            "inSample": "PASS",
            "holdout": "PASS",
            "verdict": "held",
        }
    ],
    "tierCaveat": "Validation tier: iterable model-selection evidence.",
}


def test_holdout_block_reaches_the_manifest_entry(tmp_path, monkeypatch):
    _sidecar(tmp_path, "2026-08-06-touchpoint-run", "NEISO", [2022], holdout=HOLDOUT)
    entry = _entries(tmp_path, monkeypatch)["2026-08-06-touchpoint-run"]
    assert entry["holdout"] == HOLDOUT, "the holdout block was dropped or altered"
    # The two fields the page actually navigates by.
    assert entry["holdout"]["keeper"] == "2026-08-06-keeper-run"
    assert entry["holdout"]["tier"] == "validation"


def test_holdout_is_optional_not_required(tmp_path, monkeypatch):
    """A run with no holdout block still assembles — old sidecars unaffected."""
    _sidecar(tmp_path, "2026-08-06-keeper-run", "NEISO", [2023, 2024, 2025])
    entry = _entries(tmp_path, monkeypatch)["2026-08-06-keeper-run"]
    assert "holdout" not in entry
    assert entry["years"] == [2023, 2024, 2025]


def test_run_years_are_per_run_not_per_iso(tmp_path, monkeypatch):
    """Each entry carries its OWN solve years.

    The Run Explorer's year dropdown is built from these (``runYears()``), not
    from the ISO's benchmark-year union — which is what made every NEISO/PJM
    keeper offer an empty 2022 before 2026-08-09, both ISOs shipping a 2022
    bench part.
    """
    _sidecar(tmp_path, "2026-08-06-keeper-run", "NEISO", [2023, 2024, 2025])
    _sidecar(tmp_path, "2026-08-06-touchpoint-run", "NEISO", [2022], holdout=HOLDOUT)
    entries = _entries(tmp_path, monkeypatch)
    assert entries["2026-08-06-keeper-run"]["years"] == [2023, 2024, 2025]
    assert entries["2026-08-06-touchpoint-run"]["years"] == [2022]


def test_optional_fields_tuple_still_carries_holdout():
    """Guard the tuple itself: the drop was a missing name, not broken logic."""
    assert "holdout" in build_manifest.OPTIONAL_ENTRY_FIELDS
