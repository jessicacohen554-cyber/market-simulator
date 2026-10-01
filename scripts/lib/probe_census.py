"""Census of ``scripts/probes/``: which probes live code still names, which are recent, which can go.

A probe is **retained** when either

* (a) its module stem is named by a standing surface — ``src/``, ``scripts/lib``,
  ``scripts/data``, a top-level ``scripts/*.py``, ``tests/``, ``.github/``,
  ``.claude/``, ``docs/testing.md``, ``docs/codebase/`` or ``docs/RUNBOOK.md`` — or
  by another retained probe (closure to a fixed point), or
* (b) it was first added within the last ``--days`` days (an active lane).

Everything else is a superseded one-run script and is listed ``DELETE``; deletion is
done by hand (``git rm``) after review, never by this tool. ``git log`` is the record.

The first-added date is read from ``git log --diff-filter=A``; in a shallow clone a
file present at the shallow boundary reads as added on the boundary date, so deepen
the clone past the window first (``git fetch --shallow-since=<date> origin <sha>``).

Usage::

    python3 scripts/lib/probe_census.py                # markdown table to stdout
    python3 scripts/lib/probe_census.py --list DELETE  # one path per line
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROBES = REPO / "scripts" / "probes"
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".js",
    ".html",
    ".toml",
    ".txt",
    ".sh",
    ".cfg",
}
ROOTS = (
    "src",
    "scripts/lib",
    "scripts/data",
    "tests",
    ".github",
    ".claude",
    "docs/testing.md",
    "docs/codebase",
    "docs/RUNBOOK.md",
)
TOKEN = re.compile(r"[A-Za-z0-9_]+")


def iter_root_files() -> list[Path]:
    """Return every text file under the standing reference roots plus top-level scripts."""
    files: list[Path] = sorted((REPO / "scripts").glob("*.py"))
    for root in ROOTS:
        path = REPO / root
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in sorted(path.rglob("*"))
                if p.is_file() and p.suffix in TEXT_SUFFIXES
            )
    return [p for p in files if "__pycache__" not in p.parts]


def tokens_of(path: Path) -> set[str]:
    """Return the identifier-like tokens in ``path`` (empty if unreadable)."""
    try:
        return set(TOKEN.findall(path.read_text(errors="ignore")))
    except OSError:
        return set()


def first_added_dates() -> dict[str, str]:
    """Map ``scripts/probes/<file>`` to the ISO date it was first added (one ``git log`` call)."""
    out = subprocess.run(
        [
            "git",
            "log",
            "--diff-filter=A",
            "--format=C %cs",
            "--name-only",
            "--",
            "scripts/probes",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    dates: dict[str, str] = {}
    current = ""
    for line in out.splitlines():
        if line.startswith("C "):
            current = line[2:]
        elif line.strip():
            dates[line.strip()] = (
                current  # log is newest-first: the last write is the earliest add
            )
    return dates


def census(days: int, as_of: dt.date) -> list[dict[str, str]]:
    """Classify every probe as KEEP-ref, KEEP-recent or DELETE."""
    probes = sorted(PROBES.glob("*.py"))
    stems = {p.stem: p for p in probes}
    referrer: dict[str, str] = {}
    for path in iter_root_files():
        for tok in tokens_of(path) & stems.keys():
            referrer.setdefault(tok, str(path.relative_to(REPO)))
    added = first_added_dates()
    cutoff = as_of - dt.timedelta(days=days)
    recent = {
        s
        for s, p in stems.items()
        if added.get(f"scripts/probes/{p.name}", "") >= cutoff.isoformat()
    }
    kept = set(referrer) | recent
    frontier = set(kept)
    while frontier:  # retained probes keep what they name
        nxt: set[str] = set()
        for stem in frontier:
            for tok in (tokens_of(stems[stem]) & stems.keys()) - kept - {stem}:
                referrer.setdefault(tok, f"scripts/probes/{stem}.py")
                nxt.add(tok)
        kept |= nxt
        frontier = nxt
    rows = []
    for stem, path in stems.items():
        if stem in referrer:
            status = "KEEP-ref"
        elif stem in recent:
            status = "KEEP-recent"
        else:
            status = "DELETE"
        rows.append(
            {
                "probe": path.name,
                "status": status,
                "referrer": referrer.get(stem, ""),
                "added": added.get(f"scripts/probes/{path.name}", "?"),
            }
        )
    return rows


def main() -> None:
    """CLI: print the census as a markdown table, or list one status's paths."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--days", type=int, default=14, help="active-lane window (days since first add)"
    )
    ap.add_argument("--as-of", type=dt.date.fromisoformat, default=dt.date.today())
    ap.add_argument(
        "--list",
        choices=["KEEP-ref", "KEEP-recent", "DELETE"],
        help="print only the paths with this status",
    )
    args = ap.parse_args()
    rows = census(args.days, args.as_of)
    if args.list:
        for r in rows:
            if r["status"] == args.list:
                print(f"scripts/probes/{r['probe']}")
        return
    counts = {
        s: sum(r["status"] == s for r in rows)
        for s in ("KEEP-ref", "KEEP-recent", "DELETE")
    }
    print(f"probes: {len(rows)} · " + " · ".join(f"{k} {v}" for k, v in counts.items()))
    print("\n| probe | status | first added | named by |\n|---|---|---|---|")
    for r in rows:
        if r["status"] != "DELETE":
            print(
                f"| `{r['probe']}` | {r['status']} | {r['added']} | {r['referrer']} |"
            )


if __name__ == "__main__":
    main()
