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


# --- Run-failure error message purity (review finding LN-11) -----------------


def test_run_failure_message_is_clean_of_access_log(tmp_path: Path) -> None:
    """LN-11: contextlib.redirect_stderr swaps sys.stderr process-wide during
    a solve, so handler threads logging requests mid-solve wrote into the
    run's captured stderr — HTTP access-log lines ended up glued onto the
    friendly error message. The failure message must carry only the run's
    own error text; the log must go to the real console."""
    bad_load = tmp_path / "bad_load.csv"  # exists (passes validation), but
    bad_load.write_text("hour,iso,load_mwh\n0,SAMPLE,100\n")  # misses 8759 hours
    lmp = tmp_path / "lmp.csv"
    lmp.write_text("hour,iso,lmp\n0,SAMPLE,25\n")

    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        status, body = _post_json(
            f"{base}/api/run",
            {
                "runs": [
                    {
                        "iso": "SAMPLE",
                        "mode": "premium_cap",
                        "premium_deltas": "5",
                        "load_file": str(bad_load),
                        "lmp_file": str(lmp),
                        "run_id": "failing_run",
                        "open_report_when_done": False,
                    }
                ]
            },
        )
        assert status == 200, body
        batch_id = body["batch_id"]

        final = None
        deadline = time.time() + 60.0
        while time.time() < deadline:
            run = _get_json(f"{base}/api/status?batch={batch_id}")["runs"][0]
            if run["state"] in ("done", "error"):
                final = run
                break
            time.sleep(0.2)
        assert final is not None and final["state"] == "error"
        # Friendly single error, no traceback, no access-log pollution.
        assert "load intake" in final["message"]
        assert "Traceback" not in final["message"]
        assert "HTTP/1.1" not in final["message"]


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


# Routes the hardened loopback server actually serves (see ``do_GET`` in
# launcher.py): the index itself, the JSON API, and the report browser.
_SERVED_PREFIXES = ("/api/", "/reports/")


def test_launch_page_has_no_dead_relative_links() -> None:
    """Every relative link the launch page emits must resolve to a route the
    server actually serves. Guards the HP-05 regression where the footer
    linked to ``../docs/site/index.html`` -- a ``/docs/`` route the hardened
    server never exposes (it serves only ``/``, ``/api/*`` and ``/reports/*``,
    so that link 404s). Docs are pointed at as an on-disk path instead."""
    page = _rendered_page()
    for href in re.findall(r'href\s*=\s*"([^"]*)"', page):
        # in-page anchors and data: URIs are not navigations to a route.
        if href.startswith(("#", "data:")):
            continue
        # external URLs are already banned by the self-contained test.
        assert not re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://", href), (
            f"external link on launch page: {href!r}"
        )
        served = href == "/" or href.startswith(_SERVED_PREFIXES)
        assert served, f"dead relative link on launch page: {href!r}"


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


# --- Past-runs browser (HP-03 §A) -------------------------------------------


def test_list_past_runs_finds_committed_sample_run() -> None:
    """The browser must render the repo's own committed SAMPLE_premium_cap_*
    bundle: ok, correct ISO/mode, a working report link."""
    runs = lce_launcher.list_past_runs(_PORTFOLIO_ROOT / "results")
    sample_runs = [r for r in runs if r["run_id"].startswith("SAMPLE_premium_cap_")]
    assert sample_runs, "expected the committed SAMPLE_premium_cap_* bundle"
    r = sample_runs[0]
    assert r["ok"] is True
    assert r["isos"] == ["SAMPLE"]
    assert r["mode"] == "premium_cap"
    assert r["report_url"] == f"/reports/{r['run_id']}/report.html"


def test_scan_run_dir_flags_missing_metadata(tmp_path: Path) -> None:
    """No ``*_run_metadata.json`` at all -- flagged, not a traceback."""
    run_dir = tmp_path / "empty_run"
    run_dir.mkdir()
    row = lce_launcher._scan_run_dir(run_dir)
    assert row["ok"] is False
    assert "no run metadata found" in row["flag"]


def test_scan_run_dir_flags_corrupt_metadata(tmp_path: Path) -> None:
    """A truncated/hand-edited metadata file -- flagged, not a traceback."""
    run_dir = tmp_path / "bad_run"
    run_dir.mkdir()
    (run_dir / "SAMPLE_run_metadata.json").write_text("{not valid json")
    row = lce_launcher._scan_run_dir(run_dir)
    assert row["ok"] is False
    assert "unreadable metadata" in row["flag"]


def test_scan_run_dir_flags_incomplete_metadata(tmp_path: Path) -> None:
    """Valid JSON missing the required keys -- flagged, not a KeyError."""
    run_dir = tmp_path / "partial_run"
    run_dir.mkdir()
    (run_dir / "SAMPLE_run_metadata.json").write_text(json.dumps({"iso": "SAMPLE"}))
    row = lce_launcher._scan_run_dir(run_dir)
    assert row["ok"] is False
    assert "incomplete metadata" in row["flag"]


def test_list_past_runs_skips_tmp_staging_dirs(tmp_path: Path) -> None:
    """A ``<run_id>.tmp`` scratch sibling (cli.py's atomic-ish publish) is
    in-flight/crashed, not a finished run -- never shown, flagged or not."""
    (tmp_path / "some_run.tmp").mkdir()
    assert lce_launcher.list_past_runs(tmp_path) == []


def test_runs_endpoint_flags_malformed_dir_and_lists_ok_run(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    ok_run = results_dir / "ok_run"
    ok_run.mkdir(parents=True)
    (ok_run / "SAMPLE_run_metadata.json").write_text(
        json.dumps(
            {
                "iso": "SAMPLE",
                "mode": "premium_cap",
                "lmp_kind": "hourly",
                "solves": [{"setpoint": 5.0, "status": "Optimal"}],
            }
        )
    )
    (ok_run / "report.html").write_text("<html></html>")
    (results_dir / "bad_run").mkdir(parents=True)

    with _launcher_server(tmp_path) as port:
        data = _get_json(f"http://127.0.0.1:{port}/api/runs")
    rows = {r["run_id"]: r for r in data["runs"]}
    assert rows["ok_run"]["ok"] is True
    assert rows["ok_run"]["report_url"] == "/reports/ok_run/report.html"
    assert rows["ok_run"]["lmp_kind"] == "hourly"
    assert rows["bad_run"]["ok"] is False
    assert "no run metadata found" in rows["bad_run"]["flag"]


# --- Report-route traversal hardening (regression contract, PP-13) --------


def test_report_path_regex_rejects_traversal_and_absolute_paths() -> None:
    """The past-runs browser links through the SAME ``/reports/`` route and
    regex used since ADR 0016 -- HP-03 must never relax it."""
    bad_paths = [
        "/reports/../report.html",
        "/reports/..%2Freport.html",
        "/reports//abs/report.html",
        "/reports/foo/../bar/report.html",
        "/reports//etc/passwd",
        "/reports/foo/bar/report.html",  # two path segments, not one
        "/reports/.hidden/report.html",  # leading dot
        "/reports/foo/report.txt",  # disallowed filename
    ]
    for path in bad_paths:
        assert lce_launcher._REPORT_PATH_RE.match(path) is None, path


def test_serve_report_rejects_escaped_traversal_over_http(tmp_path: Path) -> None:
    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        for bad in (
            "/reports/..%2f..%2fetc%2fpasswd",
            "/reports/foo%2f..%2fbar/report.html",
        ):
            try:
                with urllib.request.urlopen(f"{base}{bad}", timeout=10) as resp:
                    status = resp.status
            except urllib.error.HTTPError as exc:
                status = exc.code
            assert status == 404, bad


# --- Input-candidate discovery / Templates help (HP-03 §C) -----------------


def test_classify_input_file_detects_all_schemas(tmp_path: Path) -> None:
    hourly = tmp_path / "hourly.csv"
    hourly.write_text("hour,iso,lmp\n0,SAMPLE,25\n")
    assert lce_launcher.classify_input_file(hourly) == lce_launcher.LMP_KIND_HOURLY

    annual = tmp_path / "annual.csv"
    annual.write_text("iso,annual_avg_lmp\nSAMPLE,25\n")
    assert (
        lce_launcher.classify_input_file(annual)
        == lce_launcher.LMP_KIND_ANNUAL_AVERAGE_FLAT
    )

    load = tmp_path / "load.csv"
    load.write_text("hour,iso,load_mwh\n0,SAMPLE,100\n")
    assert lce_launcher.classify_input_file(load) == "load"

    unknown = tmp_path / "unknown.csv"
    unknown.write_text("foo,bar\n1,2\n")
    assert lce_launcher.classify_input_file(unknown) == "unknown"

    assert (
        lce_launcher.classify_input_file(tmp_path / "does_not_exist.csv") == "unknown"
    )


def test_list_input_candidates_whitelisted_and_degrades_gracefully(
    tmp_path: Path,
) -> None:
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "bau_lmp_2030.csv").write_text("hour,iso,lmp\n0,SAMPLE,25\n")
    (inputs_dir / "notes.txt").write_text("ignore me")  # not .csv/.parquet

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    annual_template = templates_dir / "lmp_annual_average_template.csv"
    annual_template.write_text("iso,annual_avg_lmp\nERCOT,42.5\n")

    missing_bundled = tmp_path / "does_not_exist_bundled_lmp"
    reference_load = tmp_path / "reference_load.csv"
    reference_load.write_text("hour,iso,load_mwh\n0,SAMPLE,100\n")

    result = lce_launcher.list_input_candidates(
        inputs_dir=inputs_dir,
        bundled_lmp_dir=missing_bundled,
        templates_dir=templates_dir,
        reference_load=reference_load,
    )
    paths = {c["path"] for c in result["candidates"]}
    assert str(inputs_dir / "bau_lmp_2030.csv") in paths
    assert str(annual_template) in paths
    assert str(reference_load) in paths
    assert not any("notes.txt" in p for p in paths)
    # bundled_lmp_dir doesn't exist (pre-HP-02 checkout) -- no error, no rows.
    assert not any("does_not_exist_bundled_lmp" in p for p in paths)

    annual_candidate = next(
        c for c in result["candidates"] if c["path"] == str(annual_template)
    )
    assert annual_candidate["kind"] == lce_launcher.LMP_KIND_ANNUAL_AVERAGE_FLAT


def test_list_template_help_reads_columns_live(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "lmp_8760_template.csv").write_text("hour,iso,lmp\n0,ERCOT,41.9\n")
    help_rows = lce_launcher.list_template_help(templates_dir)
    assert len(help_rows) == 1
    assert help_rows[0]["columns"] == "hour, iso, lmp"
    assert "hourly BAU LMP" in help_rows[0]["label"]


def test_input_files_endpoint_whitelisted_only(tmp_path: Path) -> None:
    """Every candidate path resolves under one of the whitelisted roots —
    never arbitrary filesystem browsing (bundled_lmp/templates use the real
    committed repo dirs here since ``--inputs-dir`` is the only one this
    launcher subprocess overrides)."""
    with _launcher_server(tmp_path) as port:
        data = _get_json(f"http://127.0.0.1:{port}/api/input-files")
    candidates = data["candidates"]
    assert candidates
    allowed_roots = (
        str(tmp_path),
        str(lce_launcher.DEFAULT_BUNDLED_LMP_DIR),
        str(lce_launcher.DEFAULT_TEMPLATES_DIR),
        str(lce_launcher.DEFAULT_REFERENCE_LOAD),
    )
    for c in candidates:
        assert any(c["path"].startswith(root) for root in allowed_roots), c

    bundled = [c for c in candidates if c["source"] == "bundled_lmp"]
    assert bundled, "expected HP-02's committed real-LMP bundle"
    assert all(c["kind"] == lce_launcher.LMP_KIND_HOURLY for c in bundled)


def test_templates_help_endpoint_reads_live_columns(tmp_path: Path) -> None:
    with _launcher_server(tmp_path) as port:
        data = _get_json(f"http://127.0.0.1:{port}/api/templates-help")
    templates = {t["path"].rsplit("/", 1)[-1]: t for t in data["templates"]}
    assert "lmp_annual_average_template.csv" in templates
    assert templates["lmp_annual_average_template.csv"]["columns"] == (
        "iso, annual_avg_lmp"
    )


# --- Persistent run log (HP-03 §B) ------------------------------------------


def test_run_log_append_and_tail(tmp_path: Path) -> None:
    log = lce_launcher.RunLog(tmp_path)
    assert log.tail(10) == []
    log.append({"run_id": "r1", "status": "done"})
    log.append({"run_id": "r2", "status": "error"})
    entries = log.tail(10)
    assert [e["run_id"] for e in entries] == ["r1", "r2"]


def test_run_log_tail_skips_corrupt_trailing_line(tmp_path: Path) -> None:
    log = lce_launcher.RunLog(tmp_path)
    log.append({"run_id": "r1", "status": "done"})
    with log.path.open("a", encoding="utf-8") as f:
        f.write("not valid json\n")
    entries = log.tail(10)
    assert [e["run_id"] for e in entries] == ["r1"]


def test_launcher_run_log_records_one_line_per_finished_run(tmp_path: Path) -> None:
    load_path, lmp_path = _fixture_paths(tmp_path)
    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        run_id = "run_log_e2e"
        status, body = _post_json(
            f"{base}/api/run",
            {
                "runs": [
                    {
                        "iso": "SAMPLE",
                        "mode": "premium_cap",
                        "premium_deltas": "5",
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

        deadline = time.time() + 120.0
        final = None
        while time.time() < deadline:
            data = _get_json(f"{base}/api/status?batch={batch_id}")
            state = data["runs"][0]["state"]
            if state in ("done", "error"):
                final = data["runs"][0]
                break
            time.sleep(1.0)
        assert final is not None and final["state"] == "done", final

        log_path = tmp_path / "launcher_state" / "run_log.jsonl"
        assert log_path.exists()
        entries = [
            json.loads(line) for line in log_path.read_text().splitlines() if line
        ]
        matching = [e for e in entries if e["run_id"] == run_id]
        assert len(matching) == 1, entries
        entry = matching[0]
        assert entry["status"] == "done"
        assert entry["iso"] == "SAMPLE"
        assert entry["mode"] == "premium_cap"
        assert entry["error"] is None
        assert entry["wall_time_seconds"] >= 0

        run_log_resp = _get_json(f"{base}/api/run-log?n=5")
        assert any(e["run_id"] == run_id for e in run_log_resp["entries"])


def test_run_log_records_error_status_on_failure(tmp_path: Path) -> None:
    bad_load = tmp_path / "bad_load.csv"  # exists, but misses 8759 hours
    bad_load.write_text("hour,iso,load_mwh\n0,SAMPLE,100\n")
    lmp = tmp_path / "lmp.csv"
    lmp.write_text("hour,iso,lmp\n0,SAMPLE,25\n")

    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        run_id = "run_log_failure"
        status, body = _post_json(
            f"{base}/api/run",
            {
                "runs": [
                    {
                        "iso": "SAMPLE",
                        "mode": "premium_cap",
                        "premium_deltas": "5",
                        "load_file": str(bad_load),
                        "lmp_file": str(lmp),
                        "run_id": run_id,
                        "open_report_when_done": False,
                    }
                ]
            },
        )
        assert status == 200, body
        batch_id = body["batch_id"]

        final = None
        deadline = time.time() + 60.0
        while time.time() < deadline:
            run = _get_json(f"{base}/api/status?batch={batch_id}")["runs"][0]
            if run["state"] in ("done", "error"):
                final = run
                break
            time.sleep(0.2)
        assert final is not None and final["state"] == "error"

        log_path = tmp_path / "launcher_state" / "run_log.jsonl"
        entries = [
            json.loads(line) for line in log_path.read_text().splitlines() if line
        ]
        matching = [e for e in entries if e["run_id"] == run_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "error"
        assert matching[0]["error"]


# --- Annual-average LMP / FLAT-PRICE badge (HP-01 x HP-03) ------------------


def test_launch_page_prefills_lmp_kind_for_annual_average_default(
    tmp_path: Path,
) -> None:
    """The FLAT-PRICE badge is schema-detected server-side for whatever LMP
    path is prefilled -- mirrors the SYNTHETIC flag's ``lmp_is_synthetic``
    idiom (LN-7)."""
    state_dir = tmp_path / "launcher_state"
    state_dir.mkdir()
    annual_lmp = tmp_path / "annual_lmp.csv"
    annual_lmp.write_text("iso,annual_avg_lmp\nSAMPLE,42.5\n")
    (state_dir / "last_used.json").write_text(json.dumps({"lmp_file": str(annual_lmp)}))
    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        defaults = _page_ctx(base)["defaults"]
        assert defaults["lmp_kind"] == lce_launcher.LMP_KIND_ANNUAL_AVERAGE_FLAT


def test_launch_page_renders_flatprice_badge_markup() -> None:
    """Unit-level check that the badge markup/wiring is present and (per
    LN-6) never assembled via an unescaped innerHTML template interpolation."""
    ctx = lce_launcher.build_page_context(
        inputs_dir=lce_launcher.DEFAULT_INPUTS_DIR,
        reference_load=lce_launcher.DEFAULT_REFERENCE_LOAD,
    )
    ctx["saved_configs"] = {}
    page = lce_launcher.render_index(ctx)
    assert "flatprice-flag" in page
    assert "FLAT-PRICE" in page
    assert "selectedLmpKind" in page


def test_launcher_completes_run_with_annual_average_lmp(tmp_path: Path) -> None:
    """HP-03 §C: a tiny synthetic annual-average LMP file queues and solves
    end to end, and the resulting run_metadata/past-runs row records the
    flat-price ``lmp_kind`` (HP-01)."""
    load_path, _ = _fixture_paths(tmp_path)
    annual_lmp = tmp_path / "annual_lmp.csv"
    annual_lmp.write_text("iso,annual_avg_lmp\nSAMPLE,25.0\n")
    results_dir = tmp_path / "results"

    with _launcher_server(tmp_path) as port:
        base = f"http://127.0.0.1:{port}"
        run_id = "annual_avg_e2e"
        status, body = _post_json(
            f"{base}/api/run",
            {
                "runs": [
                    {
                        "iso": "SAMPLE",
                        "mode": "premium_cap",
                        "premium_deltas": "5",
                        "load_file": str(load_path),
                        "lmp_file": str(annual_lmp),
                        "run_id": run_id,
                        "open_report_when_done": False,
                    }
                ]
            },
        )
        assert status == 200, body
        batch_id = body["batch_id"]

        deadline = time.time() + 120.0
        final = None
        while time.time() < deadline:
            data = _get_json(f"{base}/api/status?batch={batch_id}")
            state = data["runs"][0]["state"]
            if state in ("done", "error"):
                final = data["runs"][0]
                break
            time.sleep(1.0)
        assert final is not None and final["state"] == "done", final

        meta_path = results_dir / run_id / "SAMPLE_run_metadata.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text())
        assert meta["lmp_kind"] == lce_launcher.LMP_KIND_ANNUAL_AVERAGE_FLAT

        runs = _get_json(f"{base}/api/runs")["runs"]
        row = next(r for r in runs if r["run_id"] == run_id)
        assert row["ok"] is True
        assert row["lmp_kind"] == lce_launcher.LMP_KIND_ANNUAL_AVERAGE_FLAT
