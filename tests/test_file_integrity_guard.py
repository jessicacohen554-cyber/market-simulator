"""Regression tests for ``.github/workflows/file-integrity-guard.yml``.

CLAUDE.md rule 27's automated half. The guard is a bash step inside a workflow,
so nothing in the normal test suite exercised it — and it failed OPEN twice in
one day (2026-07-24 PR #2866, then again on PR #2893) for two *different* bash
failure modes, each of which left the job green while the scan had silently
abandoned its loop. Both were invisible to a plain-``bash`` replay; both only
reproduce under ``bash -e``, which is how GitHub Actions runs a ``run:`` block.

These tests extract the guard's own script from the workflow YAML (so they
cannot drift from what CI executes) and replay it under ``bash -e`` against
synthetic git repositories that reproduce each historical failure shape.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "file-integrity-guard.yml"


def _guard_script() -> str:
    """Return the guard step's ``run:`` body, verbatim from the workflow."""
    spec = yaml.safe_load(WORKFLOW.read_text())
    steps = spec["jobs"]["shrink-guard"]["steps"]
    runs = [s["run"] for s in steps if "run" in s]
    assert len(runs) == 1, f"expected exactly one run step, got {len(runs)}"
    return runs[0]


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    return repo


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _write(repo: Path, rel: str, n_lines: int) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(f"line {i}\n" for i in range(n_lines)))


def _run_guard(repo: Path, base: str, head: str, labels: str = "") -> tuple[int, str]:
    """Replay the guard under ``bash -e`` — the shell Actions actually uses."""
    script = repo / "guard_step.sh"
    script.write_text(_guard_script())
    proc = subprocess.run(
        ["bash", "-e", str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            "PATH": __import__("os").environ["PATH"],
            "EVENT_NAME": "push",
            "BASE_SHA": base,
            "HEAD_SHA": head,
            "PR_LABELS": labels,
        },
    )
    return proc.returncode, proc.stdout + proc.stderr


pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or not WORKFLOW.exists(),
    reason="git or the guard workflow is unavailable",
)


def test_catches_truncation_of_a_core_file(tmp_path):
    """The base case: a >=300-line core file gutted to a stub must FAIL."""
    repo = _init_repo(tmp_path)
    _write(repo, "scripts/big.py", 1911)
    base = _commit(repo, "base")
    _write(repo, "scripts/big.py", 1)
    head = _commit(repo, "truncate")

    code, out = _run_guard(repo, base, head)
    assert code == 1, out
    assert "shrank 1911 -> 1 lines" in out
    assert "Scanned 1/1 core paths." in out


def test_added_file_sorting_first_does_not_abandon_the_scan(tmp_path):
    """PR #2866's exact shape — the incident that made this guard necessary.

    An ADDED core file has no base blob. The original implementation computed
    its base line count as ``$(git show ... | wc -l || echo 0)``, which yields
    the two-line string "0\\n0"; feeding that to ``(( ))`` raised an
    arithmetic-expansion error, and under bash 5.2 that ABANDONS THE ENCLOSING
    LOOP. The added path sorts before the truncated one in the diff, so the
    truncation was never examined and the job still exited 0.
    """
    repo = _init_repo(tmp_path)
    _write(repo, "scripts/render.py", 1911)
    base = _commit(repo, "base")
    # 'backfill' sorts before 'render' — same ordering as the real incident.
    _write(repo, "scripts/backfill.py", 400)
    _write(repo, "scripts/render.py", 1)
    head = _commit(repo, "add one file, truncate another")

    code, out = _run_guard(repo, base, head)
    assert code == 1, out
    assert "shrank 1911 -> 1 lines" in out
    assert "render.py" in out
    # Both core paths must have been examined, not just the first.
    assert "Scanned 2/2 core paths." in out


def test_trailing_non_core_path_does_not_kill_the_pipeline(tmp_path):
    """PR #2893's shape: the last path in the diff is NOT a core path.

    The counting pass was once written as ``is_core "$p" && echo x``. Under
    ``bash -e`` with ``pipefail`` that leaves the loop's exit status at 1
    whenever the final path read is non-core, poisoning the pipeline and
    killing the script before a single file was checked.
    """
    repo = _init_repo(tmp_path)
    _write(repo, "scripts/big.py", 1911)
    base = _commit(repo, "base")
    _write(repo, "scripts/big.py", 1)
    # 'zzz_notes.md' is non-core and sorts last.
    _write(repo, "zzz_notes.md", 10)
    head = _commit(repo, "truncate core, touch non-core last")

    code, out = _run_guard(repo, base, head)
    assert code == 1, out
    assert "shrank 1911 -> 1 lines" in out
    assert "Scanned 1/1 core paths." in out


def test_deletion_of_a_core_file_fails(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "src/market_sim/mod.py", 500)
    base = _commit(repo, "base")
    (repo / "src/market_sim/mod.py").unlink()
    head = _commit(repo, "delete")

    code, out = _run_guard(repo, base, head)
    assert code == 1, out
    assert "core file DELETED (was 500 lines)" in out


def test_intentional_shrink_label_is_the_escape_hatch(tmp_path):
    repo = _init_repo(tmp_path)
    _write(repo, "scripts/big.py", 1911)
    base = _commit(repo, "base")
    _write(repo, "scripts/big.py", 1)
    head = _commit(repo, "truncate")

    code, out = _run_guard(repo, base, head, labels="intentional-shrink")
    assert code == 0, out
    assert "guard skipped" in out


def test_ordinary_edits_and_small_files_pass(tmp_path):
    """No false positives: a modest edit, a new file, and a small file that
    shrinks a lot (below the 300-line floor) must all pass."""
    repo = _init_repo(tmp_path)
    _write(repo, "scripts/big.py", 1000)
    _write(repo, "scripts/small.py", 100)
    base = _commit(repo, "base")
    _write(repo, "scripts/big.py", 900)  # -10%, inside the 30% budget
    _write(repo, "scripts/small.py", 2)  # -98% but below the 300-line floor
    _write(repo, "src/market_sim/new.py", 50)  # added
    head = _commit(repo, "ordinary work")

    code, out = _run_guard(repo, base, head)
    assert code == 0, out
    assert "file-integrity-guard passed." in out
    assert "Scanned 3/3 core paths." in out


def test_rename_is_guarded_at_its_destination(tmp_path):
    """A core file truncated *and* renamed must still fail, scored at the
    destination path."""
    repo = _init_repo(tmp_path)
    _write(repo, "scripts/old_name.py", 1200)
    base = _commit(repo, "base")
    (repo / "scripts/old_name.py").unlink()
    _write(repo, "scripts/new_name.py", 5)
    head = _commit(repo, "rename and truncate")

    code, out = _run_guard(repo, base, head)
    assert code == 1, out
