"""Smoke test for the forecast registration path (audit FR-26).

``scripts/register_forecast_run.py`` is a 600+-line script with **zero** tests,
and it is not merely a convenience wrapper: its ``--reindex`` IS the GitHub
Pages deploy assembly step (`.github/workflows/deploy-pages.yml` runs
``--reindex --site-dir _site``), and the registry sidecars / run payloads /
manifest it writes are generated-not-committed for the forecast namespace. A
break here does not fail loudly — it publishes an empty or malformed run
explorer.

This test reindexes a TINY synthetic namespace into a tmp dir and asserts the
three things the explorer needs to render: a registry sidecar per run, a run
payload per sidecar (the 1:1 parity the backcast namespace has a CI gate for),
and a ``manifest.js`` whose facet block ("chips": isos / kinds / tiers) is
well-formed and actually covers the runs. No solve, no network, no repo writes.
"""

from __future__ import annotations

import base64
import gzip
import json

import pytest

from scripts import register_forecast_run as R


def _sidecar(run_id: str, iso: str, kind: str, **meta) -> dict:
    """A minimal canonical hindcast sidecar, shaped like the real writers'."""
    return {
        "run_id": run_id,
        "meta": {
            "iso": iso,
            "kind": kind,
            "label": meta.pop("label", "fixture"),
            "mode": "forecast",
            "start_year": 2026,
            "end_year": 2030,
            "solved_years": [2026, 2027, 2028, 2029, 2030],
            "n_solved_years": 5,
            "total_wall_s": 1.0,
            "global_peak_rss_mb": 1.0,
            **meta,
        },
        "score": None,
        "invariants": [
            {"ident": f"I{i}", "name": f"inv {i}", "status": "PASS", "detail": ""}
            for i in range(1, 15)
        ],
        "registered_utc": "2026-07-31T00:00:00Z",
    }


@pytest.fixture
def fixture_namespace(tmp_path, monkeypatch):
    """Point the registrar at a two-run synthetic hindcast dir + empty verdicts."""
    hindcast = tmp_path / "hindcast"
    hindcast.mkdir()
    runs = [
        _sidecar("fixture-pjm-2026-2030-t1f", "PJM", "t1f"),
        _sidecar("fixture-ercot-2023-2027-x", "ERCOT", "crossover"),
    ]
    for sc in runs:
        (hindcast / f"{sc['run_id']}.json").write_text(json.dumps(sc))

    monkeypatch.setattr(R, "HINDCAST_DIR", hindcast)
    monkeypatch.setattr(R, "FORECAST_DIR", tmp_path / "absent-forecast")
    monkeypatch.setattr(R, "VERDICTS_PATH", tmp_path / "absent-verdicts.json")
    monkeypatch.setattr(R, "PROGRAM_STATUS_JSON", tmp_path / "absent-status.json")
    return tmp_path, [sc["run_id"] for sc in runs]


def test_reindex_writes_a_sidecar_and_payload_per_run(fixture_namespace):
    site, run_ids = fixture_namespace
    out = site / "site"

    n = R.reindex(site_dir=out)

    assert n == len(run_ids)
    for run_id in run_ids:
        sidecar = out / "frontend" / "data" / "forecast" / "registry" / f"{run_id}.json"
        payload = out / "frontend" / "data" / "forecast" / "runs" / f"{run_id}.js"
        assert sidecar.exists(), f"{run_id}: no registry sidecar"
        # 1:1 parity — a sidecar without its payload is invisible in the
        # explorer with no error anywhere (the exact failure the backcast
        # namespace has check_registry_payload_parity.py for).
        assert payload.exists(), f"{run_id}: sidecar written with no runs/*.js payload"


def test_registry_sidecar_is_classified_and_complete(fixture_namespace):
    site, _ = fixture_namespace
    out = site / "site"
    R.reindex(site_dir=out)

    entry = json.loads(
        (
            out
            / "frontend"
            / "data"
            / "forecast"
            / "registry"
            / "fixture-pjm-2026-2030-t1f.json"
        ).read_text()
    )
    for key in ("id", "iso", "kind", "tier", "family", "file", "registered_utc"):
        assert entry.get(key), f"registry entry missing {key!r}"
    assert entry["iso"] == "PJM"
    assert (entry["kind"], entry["tier"]) == ("t1f", "t1f")
    assert entry["n_inv"] == 14
    assert entry["file"].startswith("frontend/data/forecast/runs/")

    crossover = json.loads(
        (
            out
            / "frontend"
            / "data"
            / "forecast"
            / "registry"
            / "fixture-ercot-2023-2027-x.json"
        ).read_text()
    )
    assert (crossover["kind"], crossover["tier"]) == ("t1x", "t1x")


def test_run_payload_is_gzipped_json_the_explorer_can_decode(fixture_namespace):
    site, _ = fixture_namespace
    out = site / "site"
    R.reindex(site_dir=out)

    js = (
        out / "frontend" / "data" / "forecast" / "runs" / "fixture-pjm-2026-2030-t1f.js"
    ).read_text()
    assert js.startswith("window.FF=")
    blob = json.loads(js.split("]=", 1)[1].rstrip(";\n"))
    payload = json.loads(gzip.decompress(base64.b64decode(blob)))
    assert payload["id"] == "fixture-pjm-2026-2030-t1f"
    assert len(payload["invariants"]) == 14


def test_manifest_facets_are_well_formed_and_cover_every_run(fixture_namespace):
    """The manifest's `meta` block is what the explorer renders as filter chips."""
    site, run_ids = fixture_namespace
    out = site / "site"
    R.reindex(site_dir=out)

    js = (out / "frontend" / "data" / "forecast" / "manifest.js").read_text()
    meta = json.loads(
        js.split("window.FF.meta=", 1)[1].split(";window.FF.manifest=")[0]
    )
    manifest = json.loads(js.split(";window.FF.manifest=", 1)[1].rstrip(";\n"))

    assert meta["n_runs"] == len(manifest) == len(run_ids)
    assert meta["isos"] == ["ERCOT", "PJM"]
    assert set(meta["kinds"]) == {e["kind"] for e in manifest}
    assert set(meta["tiers"]) == {e["tier"] for e in manifest}
    # Every chip facet must be a non-empty list of strings — an explorer facet
    # holding a null renders a blank, unclickable filter.
    for facet in ("isos", "kinds", "tiers"):
        assert meta[facet] and all(isinstance(v, str) and v for v in meta[facet]), (
            f"facet {facet} is malformed: {meta[facet]!r}"
        )
    assert set(meta["schema_ready"]) == {"kinds", "tiers"}
    assert meta["inv_names"], "manifest carries no invariant-name map"


def test_reindex_survives_a_malformed_sidecar(fixture_namespace):
    """One unparseable file must not take the whole deploy assembly down."""
    site, run_ids = fixture_namespace
    (R.HINDCAST_DIR / "broken.json").write_text("{not json")
    (R.HINDCAST_DIR / "no-id.json").write_text(json.dumps({"meta": {"iso": "PJM"}}))
    out = site / "site"

    assert R.reindex(site_dir=out) == len(run_ids)
