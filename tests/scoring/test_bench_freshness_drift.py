"""Tests for the bench gate's engine-drift arithmetic (audit checklist item 12).

The SOFT (never-gating) leg of ``scripts/check_bench_freshness.py`` counts
engine commits that landed after a bench part was committed. Until 2026-09-01
it compared the part's **author** date, truncated to a calendar day, against a
``git log --since`` filter that git applies to the **COMMITTER** date — a
date-kind mismatch layered on day granularity, evaluated in the runner's local
timezone. On the record the count read 6 -> 0 -> 20 across three consecutive
readings with the bench bytes never touched.

These tests build a throwaway git repo in ``tmp_path`` and pin the three
properties the repair rests on: committer-not-author, instant-not-day, and
timezone-independence. Each constructs the exact confusion that used to
produce a wrong count and asserts the right one. No network, no writes into
the checkout.
"""

import subprocess

import pytest

from scripts import check_bench_freshness as cbf


def _run(repo, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    ).stdout


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "t@example.invalid")
    _run(repo, "config", "user.name", "t")
    return repo


def _commit(repo, rel, text, *, author_date, commit_date=None):
    """Commit ``rel`` with explicitly separated author and committer dates."""
    import os

    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    env = dict(os.environ)
    env["GIT_AUTHOR_DATE"] = author_date
    env["GIT_COMMITTER_DATE"] = commit_date or author_date
    _run(repo, "add", rel)
    _run(repo, "commit", "-q", "-m", f"touch {rel}", env=env)
    return _run(repo, "log", "-1", "--format=%h").strip()


@pytest.fixture
def patched(monkeypatch, tmp_path):
    """Point the module's git helper and ENGINE_PATHS at a throwaway repo."""
    repo = _repo(tmp_path)
    monkeypatch.setattr(cbf, "REPO", repo)
    monkeypatch.setattr(cbf, "ENGINE_PATHS", ("engine/",))
    return repo


def test_last_commit_reads_the_committer_date_not_the_author_date(patched):
    """The value fed to --since must be the kind --since filters on.

    A rebased or cherry-picked engine commit carries an author date well
    before its committer date; reading %ad and filtering on the committer date
    is what let one commit trip the drift signal 38 minutes after it was
    authored.
    """
    _commit(
        patched,
        "bench/x.json.gz",
        "part",
        author_date="2026-08-01T00:00:00+00:00",
        commit_date="2026-08-20T12:00:00+00:00",
    )
    _sha, instant = cbf._last_commit("bench/x.json.gz")
    assert instant.startswith("2026-08-20T12:00:00")


def test_same_day_engine_commit_is_counted(patched):
    """The failure item 12 named: bench touch and engine commit share a day.

    MISO/2023 read 0 drift at the audit pin for exactly this reason while four
    engine commits had in fact landed after it.
    """
    _commit(patched, "bench/x.json.gz", "part", author_date="2026-08-31T00:33:15+00:00")
    _commit(patched, "engine/mod.py", "code", author_date="2026-08-31T18:00:00+00:00")
    sha, instant = cbf._last_commit("bench/x.json.gz")
    assert cbf._engine_commits_since(instant, sha) == 1


def test_engine_commit_before_the_part_is_not_counted(patched):
    """Drift means AFTER the part was written — earlier commits never count."""
    _commit(patched, "engine/mod.py", "code", author_date="2026-08-31T00:00:00+00:00")
    _commit(patched, "bench/x.json.gz", "part", author_date="2026-08-31T18:00:00+00:00")
    sha, instant = cbf._last_commit("bench/x.json.gz")
    assert cbf._engine_commits_since(instant, sha) == 0


def test_the_parts_own_commit_is_never_counted_as_drift(patched):
    """--since is INCLUSIVE, so exclude_sha is load-bearing, not belt-and-braces."""
    import os

    repo = patched
    (repo / "bench").mkdir(parents=True, exist_ok=True)
    (repo / "engine").mkdir(parents=True, exist_ok=True)
    (repo / "bench" / "x.json.gz").write_text("part")
    (repo / "engine" / "mod.py").write_text("code")
    env = dict(os.environ)
    env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = "2026-08-31T12:00:00+00:00"
    _run(repo, "add", "bench/x.json.gz", "engine/mod.py")
    _run(repo, "commit", "-q", "-m", "one commit touching both", env=env)

    sha, instant = cbf._last_commit("bench/x.json.gz")
    assert cbf._engine_commits_since(instant, sha) == 0


def test_the_count_does_not_depend_on_the_runners_timezone(patched, monkeypatch):
    """Same bytes, different TZ, same count — the 6 -> 0 -> 20 swing's cause.

    The cutoff is now an offset-bearing instant, so both sides of the
    comparison are absolute. Under the old day-granularity arithmetic this
    engine commit fell on the far side of ``<day> 23:59:59`` in one timezone
    and the near side in another.
    """
    _commit(patched, "bench/x.json.gz", "part", author_date="2026-08-30T21:53:31+00:00")
    _commit(patched, "engine/mod.py", "code", author_date="2026-08-30T23:10:00+00:00")
    sha, instant = cbf._last_commit("bench/x.json.gz")
    counts = set()
    for tz in ("UTC", "America/Los_Angeles", "Pacific/Auckland"):
        monkeypatch.setenv("TZ", tz)
        counts.add(cbf._engine_commits_since(instant, sha))
    assert counts == {1}


def test_as_utc_normalizes_an_offset_bearing_instant():
    """Report lines render in UTC so two parts a minute apart read that way."""
    assert cbf._as_utc("2026-08-30T14:53:31-07:00") == "2026-08-30T21:53:31Z"
    assert cbf._as_utc("2026-08-30T21:53:31+00:00") == "2026-08-30T21:53:31Z"


def test_as_utc_passes_through_an_unparseable_value():
    """A part with no commit yields "" — the report must not crash on it."""
    assert cbf._as_utc("") == ""
    assert cbf._as_utc("not-a-date") == "not-a-date"


def test_uncommitted_part_reports_no_drift(patched):
    """A part written but never committed has no cutoff, so no drift claim."""
    sha, instant = cbf._last_commit("bench/never-committed.json.gz")
    assert (sha, instant) == ("", "")
    assert cbf._engine_commits_since(instant, sha) == 0
