"""The run-id collision guard in ``scripts/register_hindcast.py`` (FFR-3A-4).

A hindcast run id is the bundle directory's BASENAME, so two out-dirs sharing a
basename — the natural thing to do when a battery organises legs as
``t1h/pjm`` and ``t1x/pjm`` — resolve to the same sidecar path and the second
registration overwrites the first. There is no error, no warning and no
mismatch in the written file: the loss is visible only by counting outputs.

That has bitten two sessions in a row (FFR-3A-2 blocker 9, reproduced as
FFR-3A-3 blocker 2, where six registrations produced five sidecars). These
tests pin the guard's two halves: a DIFFERENT run under an existing id is
refused, and the same run re-registering itself still succeeds — re-scores and
invariant refreshes are routine and must not be collateral damage.

No solve, no network, no repo writes: the guard is exercised directly against
tmp-dir sidecars.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import register_hindcast as RH


def _meta(
    iso: str = "MISO", kind: str = "crossover", start: int = 2023, end: int = 2027
) -> dict:
    """A bundle ``meta.json`` carrying just the identity keys the guard reads."""
    return {"iso": iso, "kind": kind, "start_year": start, "end_year": end}


def _write_sidecar(path: Path, meta: dict) -> Path:
    path.write_text(json.dumps({"run_id": path.stem, "meta": meta}) + "\n")
    return path


def test_no_sidecar_yet_is_not_a_collision(tmp_path):
    RH._refuse_run_id_collision("miso", _meta(), tmp_path / "miso.json")


def test_same_run_reregistering_is_allowed(tmp_path):
    # Re-scores and --preserve-invariants refreshes rewrite their own sidecar
    # constantly; the guard must not treat that as a collision.
    existing = _write_sidecar(tmp_path / "miso.json", _meta())
    RH._refuse_run_id_collision("miso", _meta(), existing)


@pytest.mark.parametrize(
    "incoming",
    [
        # The t1h/pjm vs t1x/pjm case that actually bit, twice.
        _meta(iso="PJM", kind="hindcast"),
        _meta(iso="MISO", kind="crossover"),
        _meta(iso="PJM", kind="crossover", start=2021, end=2025),
    ],
    ids=["different-kind", "different-iso", "different-window"],
)
def test_different_run_under_an_existing_id_is_refused(tmp_path, incoming):
    existing = _write_sidecar(tmp_path / "pjm.json", _meta(iso="PJM", kind="crossover"))

    with pytest.raises(SystemExit) as exc:
        RH._refuse_run_id_collision("pjm", incoming, existing)

    message = str(exc.value)
    assert "run-id collision" in message
    # Both identities are printed, so the operator can see WHAT they'd clobber.
    assert "registered:" in message and "incoming:" in message


def test_unreadable_sidecar_is_not_treated_as_a_collision(tmp_path):
    # Failing closed here would block registration on a corrupt neighbour file;
    # a sidecar that cannot be parsed is not evidence about run identity.
    bad = tmp_path / "miso.json"
    bad.write_text("{not json")
    RH._refuse_run_id_collision("miso", _meta(), bad)


def test_build_sidecar_calls_the_guard(tmp_path, monkeypatch):
    """The guard is wired into the id-derivation path, not merely defined."""
    bundle = tmp_path / "miso-2023-2027-crossover-ffr3a4"
    bundle.mkdir()
    (bundle / "meta.json").write_text(json.dumps({**_meta(), "bundle": str(bundle)}))

    sidecar_dir = tmp_path / "sidecars"
    sidecar_dir.mkdir()
    # A DIFFERENT run already occupying this id.
    _write_sidecar(sidecar_dir / f"{bundle.name}.json", _meta(iso="PJM"))
    monkeypatch.setattr(RH, "SIDECAR_DIR", sidecar_dir)

    with pytest.raises(SystemExit, match="run-id collision"):
        RH.build_sidecar(bundle)


def _scoring_only_bundle(tmp_path) -> Path:
    """A committed-shape crossover bundle: score JSON only, no parquets."""
    bundle = tmp_path / "miso-2023-2027-crossover-ffr2a"
    cache = bundle / "MISO" / "k"
    cache.mkdir(parents=True)
    (bundle / "meta.json").write_text(
        json.dumps({**_meta(), "bundle": str(cache), "cache_key": "k"})
    )
    (cache / "crossover_score.json").write_text(json.dumps({"iso": "MISO"}))
    return bundle


def test_preserve_invariants_never_recomputes_over_an_absent_cache(
    tmp_path, monkeypatch
):
    """Scoring-only registration with no prior sidecar carries NO invariants.

    The dispatch parquets are intentionally uncommitted, so recomputing the
    battery over the bare committed bundle would emit vacuously-PASS rows —
    evidence that is not. The audit-tolerated shape for a scoring-only
    registration is an ABSENT block (``check_forecast_invariants.audit_sidecars``),
    and that is what ``--preserve-invariants`` must produce when there is
    nothing to preserve.
    """
    bundle = _scoring_only_bundle(tmp_path)
    sidecar_dir = tmp_path / "sidecars"
    sidecar_dir.mkdir()
    monkeypatch.setattr(RH, "SIDECAR_DIR", sidecar_dir)

    out = RH.build_sidecar(bundle, preserve_invariants=True)
    assert "invariants" not in out
    assert out["score"] == {"iso": "MISO"}


def test_preserve_invariants_reuses_the_committed_block(tmp_path, monkeypatch):
    bundle = _scoring_only_bundle(tmp_path)
    sidecar_dir = tmp_path / "sidecars"
    sidecar_dir.mkdir()
    stored = [
        {"ident": "I1", "name": "energy balance", "status": "PASS", "detail": "x"}
    ]
    (sidecar_dir / f"{bundle.name}.json").write_text(
        json.dumps({"run_id": bundle.name, "meta": _meta(), "invariants": stored})
    )
    monkeypatch.setattr(RH, "SIDECAR_DIR", sidecar_dir)

    out = RH.build_sidecar(bundle, preserve_invariants=True)
    assert out["invariants"] == stored
