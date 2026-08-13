"""The replay driver's diagnostics-write seam (the ercot-193-disclosed gap).

``scripts/replay_keeper.py`` historically stopped at the solve: a replayed
bundle carried no ``legitimacy_diagnostics.json``, so C8 had nothing to score
until an operator ran the post-step by hand (disclosed in the ercot-193
calibration-log entry and ``FINDING-ercot193-soc-regate-2026-08-13.md`` §4).
The driver now closes the gap by invoking the SAME entry point the manual
post-step uses — ``legitimacy_diagnostics.main`` with the
``calibration_verdict._LEGIT_HOWTO`` argv (``--bundle/--iso/--json-out``) —
on the replayed bundle. Trivial-first per the repo testing pattern: the solve
is stubbed out (no LP), the suite entry is recorded, and these tests pin the
seam's CLI contract plus its never-lose-the-solve error tolerance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts import legitimacy_diagnostics as ld
from scripts import replay_keeper
from scripts import run_calibration_full as rcf

# Minimal keeper meta: iso/years/timestamp are curated provenance keys and
# ``commitment`` is the one real solve kwarg, so build_kwargs stays strict-clean
# against the stub solve signature below.
_META = {
    "iso": "ERCOT",
    "years": [2023],
    "timestamp": "2026-08-01T12:00:00",
    "commitment": False,
}


def _stub_solve(
    iso=None,
    years=None,
    hours=None,
    reference=None,
    run_dir=None,
    note=None,
    commitment=False,
    ercot_wtx_curtailment_driver=None,
    coal_econ_marginal_hr_bound=None,
):
    """``solve_and_persist`` stand-in: rewrites ``meta.json``, runs no LP.

    The named parameters matter — ``build_kwargs`` strict-checks every meta
    key against ``inspect.signature(rcf.solve_and_persist)``, so the stub
    must expose the kwargs the driver passes (including the two pre-driver
    ERCOT backstops the replay pins when meta is silent).
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "meta.json").write_text(
        json.dumps(dict(_META, timestamp="2026-08-13T09:00:00")) + "\n"
    )
    return run_dir


@pytest.fixture
def bundle(tmp_path):
    """A tmp keeper bundle with just the meta.json the driver reads."""
    b = tmp_path / "bundle"
    b.mkdir()
    (b / "meta.json").write_text(json.dumps(_META) + "\n")
    return b


@pytest.fixture
def stubbed_solve(monkeypatch):
    monkeypatch.setattr(rcf, "solve_and_persist", _stub_solve)
    monkeypatch.setattr(rcf, "_load_reference", lambda: {})


def _run_main(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["replay_keeper.py", *argv])
    replay_keeper.main()


class _SuiteRecorder:
    """Stands in for ``legitimacy_diagnostics.main``; records the argv and
    emulates its ``--json-out`` artifact write."""

    def __init__(self, rc: int = 0):
        self.rc = rc
        self.calls: list[list[str]] = []

    def __call__(self, argv):
        self.calls.append(list(argv))
        args = dict(zip(argv[::2], argv[1::2]))
        Path(args["--json-out"]).write_text(
            json.dumps({"schema": "legitimacy-diagnostics/v1"}) + "\n"
        )
        return self.rc


def test_replay_invokes_the_post_step_seam(monkeypatch, bundle, stubbed_solve):
    """In-place replay calls the S1 suite with the _LEGIT_HOWTO argv."""
    recorder = _SuiteRecorder()
    monkeypatch.setattr(ld, "main", recorder)
    _run_main(monkeypatch, [str(bundle)])
    assert recorder.calls == [
        [
            "--bundle",
            str(bundle),
            "--iso",
            "ERCOT",
            "--json-out",
            str(bundle / "legitimacy_diagnostics.json"),
        ]
    ]
    assert (bundle / "legitimacy_diagnostics.json").exists()
    # The suite ran against the bundle's FINAL on-disk state: the in-place
    # replay's meta date was already restored when the seam fired.
    meta = json.loads((bundle / "meta.json").read_text())
    assert meta["timestamp"].startswith("2026-08-01")


def test_out_dir_replay_writes_diagnostics_into_out_dir(
    monkeypatch, bundle, stubbed_solve, tmp_path
):
    """An A/B-style --out-dir replay gets its own artifact (the ercot-193
    arm/control case), never the source keeper's."""
    out = tmp_path / "arm"
    recorder = _SuiteRecorder()
    monkeypatch.setattr(ld, "main", recorder)
    _run_main(monkeypatch, [str(bundle), "--out-dir", str(out)])
    [argv] = recorder.calls
    assert argv[1] == str(out)
    assert (out / "legitimacy_diagnostics.json").exists()
    assert not (bundle / "legitimacy_diagnostics.json").exists()


def test_gate_fail_does_not_fail_the_replay(monkeypatch, bundle, stubbed_solve):
    """A diagnostics gate FAIL (rc=1) is disclosure, not a replay failure."""
    monkeypatch.setattr(ld, "main", _SuiteRecorder(rc=1))
    _run_main(monkeypatch, [str(bundle)])
    assert (bundle / "legitimacy_diagnostics.json").exists()


def test_suite_hard_error_never_loses_the_solve(
    monkeypatch, bundle, stubbed_solve, capsys
):
    """A suite crash (or parser SystemExit) is loud but non-fatal, and prints
    the manual fallback command."""

    def _boom(argv):
        raise SystemExit(2)

    monkeypatch.setattr(ld, "main", _boom)
    _run_main(monkeypatch, [str(bundle)])
    err = capsys.readouterr().err
    assert "legitimacy diagnostics generation failed" in err
    assert "scripts/legitimacy_diagnostics.py" in err


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
