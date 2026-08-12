#!/usr/bin/env python3
"""Create (and optionally publish) the `cite/*` durable citation tags.

Reads the manifest `docs/governance/citation-tags.json` and creates one
annotated tag per load-bearing commit, so the citation record survives a history
rewrite: git-filter-repo rewrites tag refs onto the rewritten commits, so a tag
NAME resolves where a raw SHA does not.  Convention and rationale:
`docs/governance/citation-tags.md`; empirical verification:
`docs/FINDING-rewrite-prep-2026-08-11.md` §3.

Two things to know before running it:

1. **Most target commits are not in a default clone.** Claude Code sessions get
   a SHALLOW clone (263 of 12,024 commits at the time of writing), so
   `git tag` fails for ~90 % of the manifest.  Point `--git-dir` at a repository
   holding full history.  A commit-only mirror is enough and costs ~7.5 MB:

       git init --bare shas.git && cd shas.git
       git remote add origin <url>
       git fetch --filter=tree:0 origin 'refs/heads/main:refs/heads/main'

2. **Publishing needs push rights on `refs/tags/*`.** Claude Code sessions do
   NOT have them — the agent proxy refuses tag pushes with HTTP 403 over both
   the git transport and the GitHub Git Data API.  Run `--push` as the owner.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO_ROOT, "docs", "governance", "citation-tags.json")

REASON_TEXT = {
    "LB-1": "reproduction pin - a session reproducing a published result must "
    "check out this state",
    "LB-2": "governance record - cited inside a keeper shard, "
    "calibration-complete.json, or docs/governance/",
    "LB-3": "rule-28 audit trail - cited as evidence in a mechanism-matrix cell",
    "LB-4": "named incident - this commit IS the subject of standing rule guidance",
    "LB-5": "integrity proof - cited in a byte-identity / blob-verification table",
}


def tag_message(entry: dict) -> str:
    """The self-documenting annotation: what is pinned, why, and who cites it."""
    lines = [
        f"{entry['tag']} - durable citation handle",
        "",
        f"Pins {entry['oid']}",
        f"  ({entry['date']}) {entry['subject']}",
        "",
        "WHY PINNED:",
    ]
    lines += [f"  {r}  {REASON_TEXT[r]}" for r in entry["reasons"]]
    lines += [
        "",
        f"CITED AS {', '.join(entry['tokens'])} - {entry['n_citations']} "
        f"citation(s) across {entry['n_files']} file(s):",
    ]
    lines += [f"  {f}" for f in entry["files"][:10]]
    if entry["n_files"] > 10:
        lines.append(f"  ... and {entry['n_files'] - 10} more")
    lines += [
        "",
        "This tag exists so the citation survives a history rewrite: filter-repo",
        "rewrites tag refs onto the rewritten commit, so this NAME resolves where",
        "the raw SHA does not. Convention: docs/governance/citation-tags.md.",
    ]
    return "\n".join(lines)


def git(gitdir: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "--git-dir", gitdir, *args], capture_output=True, text=True
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--git-dir",
        default=os.path.join(REPO_ROOT, ".git"),
        help="repository holding the target commits (needs FULL history)",
    )
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument(
        "--push",
        action="store_true",
        help="publish to origin (needs refs/tags/* push rights)",
    )
    ap.add_argument("--remote", default="origin")
    ap.add_argument(
        "--force",
        action="store_true",
        help="retarget tags that already exist (see convention rule 4: "
        "published cite/* tags are append-only)",
    )
    args = ap.parse_args()

    entries = json.load(open(args.manifest))
    made, skipped, missing, failed = [], [], [], []

    for e in entries:
        if git(args.git_dir, "cat-file", "-e", f"{e['oid']}^{{commit}}").returncode:
            missing.append(e["tag"])
            continue
        exists = not git(
            args.git_dir, "rev-parse", "-q", "--verify", f"refs/tags/{e['tag']}"
        ).returncode
        if exists and not args.force:
            skipped.append(e["tag"])
            continue
        cmd = (
            ["tag", "-a"]
            + (["-f"] if args.force else [])
            + [e["tag"], "-m", tag_message(e), e["oid"]]
        )
        r = git(args.git_dir, *cmd)
        (made if not r.returncode else failed).append(
            e["tag"] if not r.returncode else (e["tag"], r.stderr.strip())
        )

    print(
        f"created {len(made)}  already-present {len(skipped)}  "
        f"missing-commit {len(missing)}  failed {len(failed)}"
    )
    if missing:
        print(f"\n{len(missing)} target commits are absent from {args.git_dir}.")
        print(
            "This is expected in a shallow clone -- see the module docstring "
            "for the commit-only mirror recipe."
        )
    for t, err in failed[:10]:
        print(f"  FAIL {t}: {err}")

    if args.push:
        r = git(args.git_dir, "push", args.remote, "refs/tags/cite/*:refs/tags/cite/*")
        if r.returncode:
            print(f"\nPUSH FAILED: {r.stderr.strip()[:400]}")
            print(
                "HTTP 403 here means the credentials lack refs/tags/* push "
                "rights; Claude Code sessions do not have them."
            )
            return 1
        print("\npushed. verify: git ls-remote --tags origin 'refs/tags/cite/*'")
    else:
        print("\n(dry run -- pass --push to publish)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
