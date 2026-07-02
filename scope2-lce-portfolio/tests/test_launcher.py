"""Tests for the desktop launcher (ADR 0016): saved-config persistence,
request validation, and an end-to-end subprocess run against SAMPLE fixtures.

No browser, no network beyond loopback: the end-to-end test starts the
launcher's HTTP server via subprocess with ``--no-open`` and scratch
``--results``/``--state-dir`` directories, submits one SAMPLE run (mirroring
``examples/run_sample_sweep.py``'s synthetic inputs), and polls
``/api/status`` to completion. This never touches ``market_sim`` or triggers
any market-sim solve (stakeholder hard hold) — SAMPLE is a data-free demo
ISO built entirely from in-test fixtures.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lce_portfolio import launcher as lce_launcher
from lce_portfolio.config import HOURS_PER_YEAR

_PORTFOLIO_ROOT = Path(__file__).resolve().parents[1]


def _fixture_paths(tmp_path: Path) -> tuple[Path, Path]:
    """Minimal SAMPLE-ISO 8760 load + LMP fixtures (mirrors test_cli.py)."""
    hours = np.arange(HOURS_PER_YEAR)
    hod = hours % 24
    load = 100.0 + 20.0 * np.clip(np.sin((hod - 8) / 24.0 * 2 * np.pi), 0, None)
    lmp = 25.0 + 10.0 * np.clip(np.sin((hod - 9) / 24.0 * 2 * np.pi), 0, None)
    load_path = tmp_path / "load.csv"
    lmp_path = tmp_path / "lmp.csv"
    pd.DataFrame({"hour": hours, "iso": "SAMPLE", "load_mwh": load}).to_csv(
        load_path, index=False
    )
    pd.DataFrame({"hour": hours, "iso": "SAMPLE", "lmp": lmp}).to_csv(
        lmp_path, index=False
    )
    return load_path, lmp_path


# --- Saved-config / last-used persistence ---------------------------------


def test_config_store_round_trip(tmp_path: Path) -> None:
    """Saved configs persist across process boundaries (new ConfigStore, same dir)."""
    store = lce_launcher.ConfigStore(tmp_path)
    assert store.saved_configs() == {}

    store.save_config("baseline", {"iso": "SAMPLE", "mode": "premium_cap"})
    assert store.saved_configs() == {
        "baseline": {"iso": "SAMPLE", "mode": "premium_cap"}
    }

    reopened = lce_launcher.ConfigStore(tmp_path)
    assert reopened.saved_configs()["baseline"]["mode"] == "premium_cap"

    reopened.delete_config("baseline")
    assert reopened.saved_configs() == {}


def test_config_store_rejects_unsafe_names(tmp_path: Path) -> None:
    """Unsafe config names (path separators, traversal, etc.) raise, not write."""
    store = lce_launcher.ConfigStore(tmp_path)
    for bad in ("../escape", "a/b", "", ".hidden", "has space"):
        with pytest.raises(ValueError):
            store.save_config(bad, {})
    assert store.saved_configs() == {}


def test_config_store_last_used_round_trip(tmp_path: Path) -> None:
    """The last-submitted run's params persist and are readable back."""
    store = lce_launcher.ConfigStore(tmp_path)
    assert store.last_used() == {}
    store.record_last_used({"iso": "ERCOT", "mode": "matching_target"})
    assert store.last_used() == {"iso": "ERCOT", "mode": "matching_target"}


# --- Request / parameter validation ---------------------------------------


def test_validate_run_payload_accepts_good_request(tmp_path: Path) -> None:
    load_path, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "mode": "premium_cap",
            "premium_deltas": "5, 10",
            "lcoe_sensitivity": "mid",
            "load_file": str(load_path),
            "lmp_file": str(lmp_path),
            "run_id": "my_run",
        }
    )
    assert err is None
    assert kwargs["run_id"] == "my_run"
    assert kwargs["premium_deltas"] == (5.0, 10.0)
    assert kwargs["matching_targets"] == lce_launcher.DEFAULT_MATCHING_TARGETS


def test_validate_run_payload_rejects_unknown_iso(tmp_path: Path) -> None:
    load_path, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "NOT_A_REAL_ISO",
            "load_file": str(load_path),
            "lmp_file": str(lmp_path),
        }
    )
    assert kwargs is None
    assert "unknown iso" in err


def test_validate_run_payload_rejects_unknown_mode(tmp_path: Path) -> None:
    load_path, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "mode": "bogus_mode",
            "load_file": str(load_path),
            "lmp_file": str(lmp_path),
        }
    )
    assert kwargs is None
    assert "unknown mode" in err


def test_validate_run_payload_rejects_missing_load_file(tmp_path: Path) -> None:
    _, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "load_file": str(tmp_path / "does_not_exist.csv"),
            "lmp_file": str(lmp_path),
        }
    )
    assert kwargs is None
    assert "load file not found" in err


def test_validate_run_payload_rejects_missing_lmp_file(tmp_path: Path) -> None:
    load_path, _ = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "load_file": str(load_path),
            "lmp_file": str(tmp_path / "does_not_exist.csv"),
        }
    )
    assert kwargs is None
    assert "LMP file not found" in err


def test_validate_run_payload_rejects_unsafe_run_id(tmp_path: Path) -> None:
    load_path, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "load_file": str(load_path),
            "lmp_file": str(lmp_path),
            "run_id": "../escape",
        }
    )
    assert kwargs is None
    assert "invalid --run-id" in err


def test_validate_run_payload_rejects_non_numeric_premium_deltas(
    tmp_path: Path,
) -> None:
    load_path, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "load_file": str(load_path),
            "lmp_file": str(lmp_path),
            "premium_deltas": "not_a_number",
        }
    )
    assert kwargs is None
    assert "premium_deltas" in err


def test_build_argv_premium_cap_vs_matching_target() -> None:
    """The composed CLI argv sweeps whichever setpoint list matches the mode."""
    base = {
        "iso": "SAMPLE",
        "load_file": "load.csv",
        "lmp_file": "lmp.csv",
        "lcoe_sensitivity": "mid",
        "run_id": "r1",
        "premium_deltas": (5.0,),
        "matching_targets": (0.9,),
    }
    premium_argv = lce_launcher.build_argv({**base, "mode": "premium_cap"})
    assert "--deltas" in premium_argv and "5.0" in premium_argv
    assert "--targets" not in premium_argv

    target_argv = lce_launcher.build_argv({**base, "mode": "matching_target"})
    assert "--targets" in target_argv and "0.9" in target_argv
    assert "--deltas" not in target_argv


# --- End-to-end: subprocess server + one SAMPLE run -----------------------


def _wait_for_serving_url(proc: subprocess.Popen, timeout: float = 15.0) -> int:
    """Read the launcher's stdout until it reports its bound port."""
    pattern = re.compile(r"http://127\.0\.0\.1:(\d+)/")
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                raise RuntimeError(
                    f"launcher process exited (rc={proc.returncode}) before serving"
                )
            continue
        match = pattern.search(line)
        if match:
            return int(match.group(1))
    raise TimeoutError("launcher did not report a serving URL in time")


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


@contextlib.contextmanager
def _launcher_server(tmp_path: Path):
    """Start ``python -m lce_portfolio.launcher --no-open`` as a subprocess.

    Yields the bound loopback port; always terminates the server on exit.
    Scratch ``--results``/``--state-dir``/``--inputs-dir`` all live under
    ``tmp_path`` so nothing leaks into the repo.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_PORTFOLIO_ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "lce_portfolio.launcher",
            "--no-open",
            "--port",
            "0",
            "--results",
            str(tmp_path / "results"),
            "--state-dir",
            str(tmp_path / "launcher_state"),
            "--inputs-dir",
            str(tmp_path),
        ],
        cwd=str(_PORTFOLIO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        yield _wait_for_serving_url(proc)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


def _raw_post(port: int, content_length: str, body: bytes = b'{"runs": []}') -> int:
    """POST /api/run with a hand-rolled Content-Length; return the status.

    Sent as one raw-socket write so a server that (correctly) responds before
    draining the body can't race the client. A server that hangs instead of
    responding fails the test via the 10 s socket timeout.
    """
    request = (
        f"POST /api/run HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\n"
        f"Content-Type: application/json\r\nConnection: close\r\n"
        f"Content-Length: {content_length}\r\n\r\n"
    ).encode() + body
    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
        sock.sendall(request)
        data = b""
        while b"\r\n" not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    status_line = data.split(b"\r\n", 1)[0].decode(errors="replace")
    return int(status_line.split()[1])


def test_launcher_end_to_end_sample_run(tmp_path: Path) -> None:
    """Start the launcher, submit one SAMPLE run, poll to completion.

    Smallest/fastest launcher-exposed config that solves: SAMPLE ISO (data-free
    demo), premium_cap mode, a single premium delta — the library-default
    active-resource set (mirrors ``examples/run_sample_sweep.py`` and the
    committed ``results/SAMPLE_premium_cap_*/`` bundle; ``active_resources``
    itself is config-file-only, not a launch-page field, ADR 0016 §3).
    """
    load_path, lmp_path = _fixture_paths(tmp_path)
    results_dir = tmp_path / "results"

    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"

        with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")

        run_id = "launcher_e2e_sample"
        status, body = _post_json(
            f"{base}/api/run",
            {
                "runs": [
                    {
                        "iso": "SAMPLE",
                        "mode": "premium_cap",
                        "premium_deltas": "5",
                        "lcoe_sensitivity": "mid",
                        "load_file": str(load_path),
                        "lmp_file": str(lmp_path),
                        "run_id": run_id,
                        "open_report_when_done": False,
                    }
                ]
            },
        )
        assert status == 200, body
        batch_id = body["batch_id"]
        assert body["runs"][0]["run_id"] == run_id

        deadline = time.time() + 120.0
        final_status = None
        while time.time() < deadline:
            data = _get_json(f"{base}/api/status?batch={batch_id}")
            state = data["runs"][0]["state"]
            if state in ("done", "error"):
                final_status = data["runs"][0]
                break
            time.sleep(1.0)
        assert final_status is not None, "run did not finish within the timeout"
        assert final_status["state"] == "done", final_status["message"]

        report_path = results_dir / run_id / "report.html"
        assert report_path.exists()

        # The report is also servable straight from the launcher.
        with urllib.request.urlopen(
            f"{base}{final_status['report_url']}", timeout=10
        ) as resp:
            assert resp.status == 200


def test_launcher_rejects_bad_run_over_http(tmp_path: Path) -> None:
    """A validation failure comes back as a clean 400 JSON payload, no crash."""
    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        status, body = _post_json(
            f"{base}/api/run",
            {"runs": [{"iso": "NOT_A_REAL_ISO", "load_file": "x", "lmp_file": "y"}]},
        )
        assert status == 400
        assert "unknown iso" in body["error"]


# --- run_lce.sh end-to-end (ADR 0016 §1; review finding LN-10) ---------------


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_run_lce_sh_starts_and_serves(tmp_path: Path) -> None:
    """LN-10: ADR 0016 §1 says CI exercises the .sh path end-to-end, but the
    tests only ever invoked `python -m lce_portfolio.launcher` directly —
    the script's Python resolution (../.venv → PATH fallback with the
    3.11+/import gate) and PYTHONPATH wiring were untested. Run the actual
    script and confirm it resolves a Python, binds loopback, and serves."""
    script = _PORTFOLIO_ROOT / "launcher" / "run_lce.sh"
    assert script.exists() and os.access(script, os.X_OK)

    proc = subprocess.Popen(
        [
            "bash",
            str(script),
            "--no-open",
            "--port",
            "0",
            "--results",
            str(tmp_path / "results"),
            "--state-dir",
            str(tmp_path / "launcher_state"),
            "--inputs-dir",
            str(tmp_path),
        ],
        cwd=str(_PORTFOLIO_ROOT),
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        port = _wait_for_serving_url(proc)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


# --- Worker-thread error discipline (review finding LN-9) --------------------


def test_execute_survives_system_exit(tmp_path: Path, monkeypatch) -> None:
    """LN-9: SystemExit is not an Exception — uncaught, it killed the single
    worker thread silently and every later queued run hung at 'queued'.
    _execute must absorb it into a friendly error status instead."""

    def _exiting_main(argv):
        raise SystemExit(2)

    monkeypatch.setattr(lce_launcher.cli, "main", _exiting_main)
    state = lce_launcher.LauncherState(
        state_dir=tmp_path / "state",
        results_dir=tmp_path / "results",
        open_browser=False,
    )
    run_kwargs = {
        "iso": "SAMPLE",
        "mode": "premium_cap",
        "premium_deltas": (5.0,),
        "matching_targets": (0.9,),
        "lcoe_sensitivity": "mid",
        "load_file": "load.csv",
        "lmp_file": "lmp.csv",
        "run_id": "sysexit_run",
        "open_report_when_done": False,
    }
    # Register the batch directly (bypassing the queue) so the idle worker
    # thread can't race this synchronous _execute call.
    state.batches["b1"] = [
        lce_launcher.RunStatus(run_id="sysexit_run", iso="SAMPLE", mode="premium_cap")
    ]
    state._execute("b1", 0, run_kwargs)  # must not raise
    status = state.batch_status("b1")[0]
    assert status["state"] == "error"
    assert "internal error" in status["message"]


# --- Last-used pre-fill freshness (review finding LN-7) ----------------------


def _page_ctx(base: str) -> dict:
    """Fetch / and parse the embedded CTX JSON blob out of the page script."""
    with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
        page = resp.read().decode()
    match = re.search(r"const CTX = (.*);", page)
    assert match, "CTX blob not found in launch page"
    return json.loads(match.group(1))


def test_launch_page_prefills_fresh_last_used(tmp_path: Path) -> None:
    """LN-7: last-used values were merged once at server start, so a page
    reload never reflected the latest submit. They must be re-read per page
    load; the run id must never be pre-filled (a stale id would overwrite
    that run's results on resubmit); and the SYNTHETIC flag must track the
    pre-filled LMP path, staying visible for a _dummy stub."""
    state_dir = tmp_path / "launcher_state"
    state_dir.mkdir()
    (state_dir / "last_used.json").write_text(
        json.dumps(
            {
                "iso": "CAISO",
                "run_id": "stale_run",
                "lmp_file": str(tmp_path / "bau_lmp_2030_dummy.csv"),
            }
        )
    )
    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        defaults = _page_ctx(base)["defaults"]
        assert defaults["iso"] == "CAISO"
        assert defaults["run_id"] == ""  # never pre-filled
        assert defaults["lmp_is_synthetic"] is True

        # Updated mid-session (as a submit would) → next page load sees it.
        (state_dir / "last_used.json").write_text(json.dumps({"iso": "PJM"}))
        assert _page_ctx(base)["defaults"]["iso"] == "PJM"


# --- Launch page: self-containment + injection surface (ADR 0016 §2, LN-6) --


def _rendered_page() -> str:
    ctx = lce_launcher.build_page_context(
        inputs_dir=lce_launcher.DEFAULT_INPUTS_DIR,
        reference_load=lce_launcher.DEFAULT_REFERENCE_LOAD,
    )
    ctx["saved_configs"] = {}
    return lce_launcher.render_index(ctx)


def test_launch_page_is_self_contained() -> None:
    """ADR 0016 §2: inline CSS/JS only — no CDN, no external fetch. Only
    data: URIs and #anchors are allowed as URL-ish content."""
    page = _rendered_page()
    assert not re.search(r"https?://", page)
    assert "@import" not in page
    assert "//fonts" not in page
    assert not re.search(r"<link\b", page)
    assert not re.search(r"""\bsrc\s*=\s*["'](?!data:|#)""", page)


def test_launch_page_status_table_avoids_html_injection() -> None:
    """LN-6: the status table's run-id/state/detail cells were assembled with
    innerHTML template literals, so solver stderr (which can echo text from
    user-supplied input files) could inject markup. Cells must be built via
    textContent; only container resets may touch innerHTML."""
    page = _rendered_page()
    assert "tr.innerHTML" not in page
    assert "textContent" in page
    for line in page.splitlines():
        if "innerHTML" in line:
            # container resets ('') and static literals are fine; any
            # interpolation of runtime data into innerHTML is not.
            assert "${" not in line, line


def test_launcher_cli_has_no_host_flag() -> None:
    """LN-5: ADR 0016 defers remote use — the un-authenticated server binds
    loopback only, and no CLI flag may rebind it to another interface."""
    with pytest.raises(SystemExit):
        lce_launcher.main(["--host", "0.0.0.0", "--no-open"])


# --- Non-finite / empty numeric lists (review finding LN-4) -----------------


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "", "5, nan", ", ,"])
def test_validate_run_payload_rejects_non_finite_or_empty_deltas(
    tmp_path: Path, bad: str
) -> None:
    """LN-4: nan slips through PortfolioConfig's d <= 0 check (nan comparisons
    are all False) and would reach the LP; empty lists fail late and
    confusingly. Both must be clean validation errors."""
    load_path, lmp_path = _fixture_paths(tmp_path)
    kwargs, err = lce_launcher.validate_run_payload(
        {
            "iso": "SAMPLE",
            "mode": "premium_cap",
            "premium_deltas": bad,
            "load_file": str(load_path),
            "lmp_file": str(lmp_path),
        }
    )
    assert kwargs is None
    assert "premium_deltas" in err


# --- Batch run-id collisions (review finding LN-3) --------------------------


def _validated_run(run_id: str, auto: bool) -> dict:
    return {
        "iso": "SAMPLE",
        "mode": "premium_cap",
        "run_id": run_id,
        "run_id_auto": auto,
    }


def test_dedupe_run_ids_suffixes_auto_collisions() -> None:
    """LN-3: blank-run-id runs composed in the same second must not share a
    results directory — the later run overwrote the earlier one's results."""
    runs = [
        _validated_run("SAMPLE_premium_cap_20260702-120000", True),
        _validated_run("SAMPLE_premium_cap_20260702-120000", True),
        _validated_run("SAMPLE_premium_cap_20260702-120000", True),
    ]
    assert lce_launcher.dedupe_run_ids(runs) is None
    ids = [r["run_id"] for r in runs]
    assert len(set(ids)) == 3
    assert ids[1].endswith("-2") and ids[2].endswith("-3")


def test_dedupe_run_ids_rejects_explicit_duplicates() -> None:
    """LN-3: two runs explicitly given the same run id are a user error."""
    runs = [_validated_run("my_run", False), _validated_run("my_run", False)]
    error = lce_launcher.dedupe_run_ids(runs)
    assert error is not None and "duplicate run id" in error


def test_launcher_rejects_explicit_duplicate_run_ids_over_http(tmp_path: Path) -> None:
    """LN-3 over HTTP: an explicit duplicate is a 400, nothing is enqueued."""
    load_path, lmp_path = _fixture_paths(tmp_path)
    run = {
        "iso": "SAMPLE",
        "mode": "premium_cap",
        "premium_deltas": "5",
        "load_file": str(load_path),
        "lmp_file": str(lmp_path),
        "run_id": "dup_run",
    }
    with _launcher_server(tmp_path) as port:
        status, body = _post_json(
            f"http://127.0.0.1:{port}/api/run", {"runs": [run, dict(run)]}
        )
        assert status == 400
        assert "duplicate run id" in body["error"]


# --- Malformed / hostile requests (review findings LN-1/LN-2) --------------


def test_validate_run_payload_rejects_non_object_run() -> None:
    """LN-1: a string entry in "runs" gets a message, not an AttributeError."""
    kwargs, err = lce_launcher.validate_run_payload("not-an-object")
    assert kwargs is None
    assert "JSON object" in err


def test_launcher_malformed_requests_over_http(tmp_path: Path) -> None:
    """LN-1/LN-2: every malformed body/header shape is a prompt 400 JSON
    response — previously a raw traceback + dropped connection (array body,
    non-dict run entry, non-integer Content-Length) or a hung handler
    (negative or huge Content-Length) — and the server stays serviceable."""
    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"

        status, body = _post_json(f"{base}/api/run", [])
        assert status == 400
        assert "JSON object" in body["error"]

        status, body = _post_json(f"{base}/api/run", {"runs": ["not-an-object"]})
        assert status == 400
        assert "JSON object" in body["error"]

        status, body = _post_json(f"{base}/api/save-config", [])
        assert status == 400
        assert "JSON object" in body["error"]

        assert _raw_post(port, "abc") == 400
        assert _raw_post(port, "-1") == 400
        assert _raw_post(port, str(lce_launcher.MAX_REQUEST_BYTES + 1)) == 400

        # The server survived all of the above and still validates runs.
        status, body = _post_json(
            f"{base}/api/run",
            {"runs": [{"iso": "NOT_A_REAL_ISO", "load_file": "x", "lmp_file": "y"}]},
        )
        assert status == 400
        assert "unknown iso" in body["error"]
