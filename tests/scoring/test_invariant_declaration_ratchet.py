"""The forecast-invariant declaration ratchet at the registration seam (Y-24).

``scripts/check_forecast_invariants.py --sidecar-dir`` (CI job
``forecast-invariant-artifacts``) is a DETECTOR: it audits sidecars that are
already committed and goes red after the fact. The single registration seam,
``scripts/register_forecast_run.py``, had no declaration check at all — a lane
could land a sidecar carrying invariant FAILs and nothing refused it. That is
why the undeclared backlog regressed 4 -> 16 -> 17 -> 20, and why lane Y-19
declared 16 of 20 and was still behind when it merged.

Y-24 adds the ratchet at that seam. These tests pin the four properties that
make it a ratchet rather than a second detector:

1. **Refusal.** A registration whose sidecar carries an undeclared FAIL exits
   non-zero and writes NOTHING — the gate runs before the canonical sidecar,
   so a refused run leaves nothing behind.
2. **Declaration is the remedy.** The same run passes once the ledger declares
   the ident. There is no bypass flag, and the tests assert there is none.
3. **Baseline = inflow only.** A pair in ``registration_ratchet_baseline``
   passes the registration gate but STAYS RED in the CI audit, so the standing
   backlog changes no already-registered run while routing keeps its teeth.
4. **The deploy path is untouched.** ``--reindex`` never reaches the gate and
   stays importable under a bare ``python3`` (it IS the Pages deploy assembly
   step, which installs no dependencies).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import register_forecast_run as RF
from scripts.lib import invariant_ledger as il

REPO = Path(__file__).resolve().parents[2]


def _sidecar(run_id: str = "iso-2026-2030-probe", **statuses: str) -> dict:
    """A minimal canonical sidecar whose I1-I14 block carries ``statuses``."""
    return {
        "run_id": run_id,
        "meta": {"iso": "ERCOT", "kind": "t1f"},
        "invariants": [
            {
                "ident": f"I{i}",
                "name": f"inv {i}",
                "status": statuses.get(f"I{i}", "PASS"),
                "detail": "",
            }
            for i in range(1, 15)
        ],
    }


def _ledger(tmp_path: Path, **blocks) -> Path:
    path = tmp_path / "invariant-failures.json"
    path.write_text(json.dumps({"schema_version": 1, **blocks}))
    return path


# --------------------------------------------------------------------------- #
# 1. Refusal — an undeclared FAIL is not registrable
# --------------------------------------------------------------------------- #


def test_undeclared_fail_refuses_registration(tmp_path):
    """A FAIL in neither ledger block exits with the run id and the ident."""
    ledger = _ledger(tmp_path, declared_failures={}, registration_ratchet_baseline={})
    with pytest.raises(SystemExit) as exc:
        RF.enforce_invariant_declaration_gate(_sidecar(I7="FAIL"), ledger_path=ledger)
    msg = str(exc.value)
    assert "REGISTRATION REFUSED" in msg
    assert "iso-2026-2030-probe" in msg
    assert "I7" in msg
    # The remedy is named, and it is the declaration — not a flag.
    assert "declared_failures" in msg
    assert "no bypass flag" in msg.lower()


def test_every_failing_ident_is_named_not_just_the_first(tmp_path):
    """A multi-ident failure reports all of them, so one edit closes the run."""
    ledger = _ledger(tmp_path, declared_failures={})
    with pytest.raises(SystemExit) as exc:
        RF.enforce_invariant_declaration_gate(
            _sidecar(I3="FAIL", I7="FAIL", I12="FAIL"), ledger_path=ledger
        )
    msg = str(exc.value)
    assert "I3" in msg and "I7" in msg and "I12" in msg


def test_partial_declaration_still_refuses(tmp_path):
    """Declaring one of two FAILs does not buy the other one through."""
    ledger = _ledger(tmp_path, declared_failures={"iso-2026-2030-probe": ["I3"]})
    with pytest.raises(SystemExit) as exc:
        RF.enforce_invariant_declaration_gate(
            _sidecar(I3="FAIL", I7="FAIL"), ledger_path=ledger
        )
    assert "I7" in str(exc.value)
    assert "'I3'" not in str(exc.value)


def test_no_bypass_flag_exists_on_the_registration_cli():
    """The remedy is the declaration: no CLI escape hatch may be added."""
    source = (REPO / "scripts" / "register_forecast_run.py").read_text()
    for banned in (
        "--skip-invariant",
        "--no-invariant-gate",
        "--allow-undeclared",
        "--force",
    ):
        assert banned not in source, f"{banned} is a bypass around the ratchet"


# --------------------------------------------------------------------------- #
# 2. A declared run registers
# --------------------------------------------------------------------------- #


def test_declared_fail_passes(tmp_path):
    ledger = _ledger(tmp_path, declared_failures={"iso-2026-2030-probe": ["I7"]})
    RF.enforce_invariant_declaration_gate(_sidecar(I7="FAIL"), ledger_path=ledger)


def test_clean_run_passes_with_an_empty_ledger(tmp_path):
    """No FAILs, nothing to declare — the gate is silent on a healthy run."""
    ledger = _ledger(tmp_path, declared_failures={})
    RF.enforce_invariant_declaration_gate(_sidecar(), ledger_path=ledger)


def test_non_fail_statuses_are_not_gated(tmp_path):
    """WARN / SKIP are not FAILs; the ledger declares FAILs only."""
    ledger = _ledger(tmp_path, declared_failures={})
    RF.enforce_invariant_declaration_gate(
        _sidecar(I12="WARN", I10="SKIP"), ledger_path=ledger
    )


def test_scoring_only_sidecar_without_invariants_passes(tmp_path):
    """A registration carrying no invariants block has no FAILs to declare."""
    ledger = _ledger(tmp_path, declared_failures={})
    RF.enforce_invariant_declaration_gate(
        {"run_id": "iso-rescore", "meta": {}}, ledger_path=ledger
    )


# --------------------------------------------------------------------------- #
# 3. The baseline gates inflow only
# --------------------------------------------------------------------------- #


def test_baselined_fail_passes_the_registration_gate(tmp_path):
    """An already-registered pair stays registrable: the ratchet is inflow-only."""
    ledger = _ledger(
        tmp_path,
        declared_failures={},
        registration_ratchet_baseline={"iso-2026-2030-probe": ["I7"]},
    )
    RF.enforce_invariant_declaration_gate(_sidecar(I7="FAIL"), ledger_path=ledger)


def test_baseline_does_not_cover_a_new_ident_on_a_baselined_run(tmp_path):
    """The baseline forgives the recorded pair, never the whole run."""
    ledger = _ledger(
        tmp_path, registration_ratchet_baseline={"iso-2026-2030-probe": ["I7"]}
    )
    with pytest.raises(SystemExit) as exc:
        RF.enforce_invariant_declaration_gate(
            _sidecar(I3="FAIL", I7="FAIL"), ledger_path=ledger
        )
    assert "I3" in str(exc.value)


def test_baseline_never_makes_the_ci_audit_green(tmp_path):
    """The audit ignores the baseline, so routing keeps its teeth.

    This is the load-bearing asymmetry of the design: a baselined pair passes
    the REGISTRATION gate (it changes no already-registered run) and stays a
    problem in the DETECTOR (an undiagnosed FAIL is not absolved by being old).
    """
    from scripts import check_forecast_invariants as CFI

    sidecar_dir = tmp_path / "hindcast"
    sidecar_dir.mkdir()
    (sidecar_dir / "run.json").write_text(json.dumps(_sidecar(I7="FAIL")))
    ledger = _ledger(
        tmp_path, registration_ratchet_baseline={"iso-2026-2030-probe": ["I7"]}
    )

    problems = CFI.audit_sidecars(sidecar_dir, ledger)
    assert any("I7" in p and "not declared" in p for p in problems)
    # ... and the same pair is registrable, from the same ledger.
    RF.enforce_invariant_declaration_gate(_sidecar(I7="FAIL"), ledger_path=ledger)


@pytest.mark.parametrize(
    "declared,fails,reason",
    [
        ({}, {}, "no sidecar carrying invariants"),
        ({}, {"I3": "FAIL"}, "no longer FAIL"),
        ({"iso-2026-2030-probe": ["I7"]}, {"I7": "FAIL"}, "now also declared"),
    ],
)
def test_superseded_baseline_line_becomes_an_audit_problem(
    tmp_path, declared, fails, reason
):
    """The baseline may only SHRINK — a line kept past its cause is red.

    Without this the baseline would silently forgive a future regression on the
    same ident, which is the failure mode the ratchet exists to close.
    """
    from scripts import check_forecast_invariants as CFI

    sidecar_dir = tmp_path / "hindcast"
    sidecar_dir.mkdir()
    if fails:
        (sidecar_dir / "run.json").write_text(json.dumps(_sidecar(**fails)))
    ledger = _ledger(
        tmp_path,
        declared_failures=declared,
        registration_ratchet_baseline={"iso-2026-2030-probe": ["I7"]},
    )
    problems = CFI.audit_sidecars(sidecar_dir, ledger)
    assert any(reason in p for p in problems), problems


# --------------------------------------------------------------------------- #
# 4. The seam: a refused registration leaves nothing behind
# --------------------------------------------------------------------------- #


def test_refused_registration_writes_no_sidecar(tmp_path, monkeypatch):
    """main(--bundle) refuses BEFORE the canonical sidecar reaches disk."""
    from scripts import register_hindcast as RH

    sidecar_dir = tmp_path / "hindcast"
    monkeypatch.setattr(RH, "SIDECAR_DIR", sidecar_dir)
    monkeypatch.setattr(RH, "build_sidecar", lambda *a, **k: _sidecar(I7="FAIL"))
    # Anything past the gate would reindex the real namespace; a refused
    # registration must never get that far.
    monkeypatch.setattr(RF, "register_one", lambda *a, **k: pytest.fail("registered"))

    # The REAL gate against the REAL committed ledger: the synthetic run id is
    # in neither block, so it is refused exactly as a new undeclared run is.
    with pytest.raises(SystemExit) as exc:
        RF.main(["--bundle", str(tmp_path / "bundle")])
    assert "REGISTRATION REFUSED" in str(exc.value)
    assert not sidecar_dir.exists(), "a refused registration left a sidecar behind"


def test_gate_precedes_every_write_in_both_registration_branches():
    """Source-order guard: the gate call sits above the sidecar write.

    The 'leaves nothing behind' property is an ORDERING property, and the two
    branches are edited by different lanes over time. Pinning the order here
    catches a reordering that no functional test would notice until a refused
    run had already been half-written.
    """
    source = (REPO / "scripts" / "register_forecast_run.py").read_text()
    body = source[source.index("def main(") :]
    gate_calls = [
        i
        for i, line in enumerate(body.splitlines())
        if "enforce_invariant_declaration_gate(sidecar)" in line
    ]
    writes = [
        i
        for i, line in enumerate(body.splitlines())
        if '.json").write_text(' in line or "mkdir(parents=True" in line
    ]
    assert len(gate_calls) == 2, "both --bundle and --summary must call the gate"
    assert len(writes) >= 2, "write detection found nothing — the guard is vacuous"
    assert min(writes) > min(gate_calls), "a write precedes the first gate call"
    assert max(writes) > max(gate_calls), "a write precedes the last gate call"


@pytest.mark.parametrize(
    "module,fn",
    [
        ("scripts/register_hindcast.py", "enforce_invariant_declaration_gate"),
        ("scripts/register_forecast_baseline.py", "enforce_invariant_declaration_gate"),
    ],
)
def test_legacy_direct_writers_are_not_a_bypass(module, fn):
    """Both legacy entry points write the canonical sidecar themselves.

    Each has its own ``main()`` + ``__main__`` and writes
    ``frontend/data/hindcast/<id>.json`` directly before delegating the
    namespace rebuild to ``register_forecast_run``. Without the same gate they
    would be open doors around the ratchet.
    """
    assert fn in (REPO / module).read_text()


# --------------------------------------------------------------------------- #
# 5. Contracts the two consumers share
# --------------------------------------------------------------------------- #


def test_fail_literal_matches_the_checkers():
    """``invariant_ledger`` re-declares FAIL to stay stdlib-only; keep them equal."""
    from scripts import check_forecast_invariants as CFI

    assert il.FAIL == CFI.FAIL


def test_ledger_file_constant_matches_the_checker_default():
    from scripts import check_forecast_invariants as CFI

    default = CFI.main.__globals__["_REPO"] / il.LEDGER_FILE
    assert default.name == "invariant-failures.json"
    assert default.exists()


def test_reindex_stays_importable_without_third_party_deps():
    """``--reindex`` IS the Pages deploy step and runs under a bare python3.

    A module-scope import of anything outside the stdlib (numpy, market_sim)
    would not fail a test run — the test env has them — it would fail the
    DEPLOY. So this asserts it in a clean interpreter with the site-packages
    the deploy lacks made unimportable.
    """
    probe = (
        "import sys;"
        "sys.modules['numpy']=None;"
        "sys.modules['pandas']=None;"
        "sys.modules['market_sim']=None;"
        "import scripts.register_forecast_run as R;"
        "assert R.enforce_invariant_declaration_gate"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], cwd=REPO, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr


def test_committed_ledger_baseline_is_consistent_with_the_committed_sidecars():
    """The shipped baseline names real, still-undeclared, still-failing pairs.

    The ratchet's credibility rests on the baseline being exactly the standing
    backlog and nothing more — an entry for a run that passes, or one that a
    desk has since declared, would be a live forgiveness token.
    """
    ledger = il.load_ledger(REPO)
    baseline = ledger.get(il.BASELINE_KEY, {})
    assert baseline, "the ratchet baseline block is missing"
    for run_id, idents in baseline.items():
        sidecar_path = REPO / "frontend" / "data" / "hindcast" / f"{run_id}.json"
        assert sidecar_path.exists(), f"{run_id} is baselined but has no sidecar"
        failing = set(il.fail_idents(json.loads(sidecar_path.read_text())))
        assert set(idents) <= failing, f"{run_id} baselines a non-failing ident"
        declared = set(ledger.get(il.DECLARED_KEY, {}).get(run_id, ()))
        assert not (set(idents) & declared), f"{run_id} is both baselined and declared"
