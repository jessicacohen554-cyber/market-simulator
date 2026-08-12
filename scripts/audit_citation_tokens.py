#!/usr/bin/env python3
"""Hex-token inventory for the rewrite-prep lane (T1).

Scans the citation-bearing corpora (docs/, frontend/data/**/*.json, the sharded
mechanism matrix) for hex-looking tokens of length 7-40, resolves each against
two object databases, and buckets them.

Object databases:
  * FULL   -- a commit-only (--filter=tree:0) mirror of the ENTIRE repo history
              in the scratchpad.  The working clone is SHALLOW (263 commits), so
              this is the only DB that can answer "is this a real commit SHA".
  * LOCAL  -- the working repo, which additionally has trees/blobs for the
              shallow window (used to catch blob/tree citations).

Buckets (prompt T1):
  a_commit        real commit SHA in this repo
  b_cachekey      16-char runtime/config cache key  -- NEVER transform these
  c_blobtree      resolves to a blob or tree object
  d_identifier    non-resolving token that is part of / is a domain identifier
  e_falsepos      non-resolving token that is a number or incidental hex text
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import defaultdict

REPO = os.environ.get("REPO_ROOT", "/home/user/market-simulator")
FULL_DB = (
    "/tmp/claude-0/-home-user-market-simulator/"
    "6b30eefc-be8c-5482-bc5a-181509538df5/scratchpad/shas.git"
)
OUT = os.path.dirname(os.path.abspath(__file__))

# Matches the manager's measurement convention (\b...\b, length 7-40).
TOKEN_RE = re.compile(r"\b[0-9a-f]{7,40}\b")

CORPORA = {
    "docs": ["docs"],
    "frontend_json": ["frontend/data"],
}
SKIP_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".parquet",
    ".npz",
    ".zip",
    ".woff",
    ".woff2",
    ".ttf",
    ".ico",
    ".svg",
)


def iter_files():
    """Yield (corpus, relpath) for every file in the citation corpora."""
    for corpus, roots in CORPORA.items():
        for root in roots:
            for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, root)):
                dirnames[:] = [d for d in dirnames if d != ".git"]
                for fn in filenames:
                    if fn.endswith(SKIP_SUFFIXES):
                        continue
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, REPO)
                    if corpus == "frontend_json" and not fn.endswith(".json"):
                        continue
                    yield corpus, rel


def matrix_files():
    """The sharded mechanism matrix: base rows + one shard per ISO."""
    base = "docs/codebase-site/data/mechanism-matrix.js"
    shards = [
        f"docs/codebase-site/data/mechanism-matrix/{iso}.js"
        for iso in ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM")
    ]
    for rel in [base] + shards:
        if os.path.exists(os.path.join(REPO, rel)):
            yield "matrix", rel


def scan():
    """Extract every hex token with its file/line/context."""
    occurrences = []  # (token, corpus, relpath, lineno, line)
    files_scanned = 0
    for corpus, rel in list(iter_files()) + list(matrix_files()):
        path = os.path.join(REPO, rel)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except (OSError, UnicodeError):
            continue
        files_scanned += 1
        for i, line in enumerate(lines, 1):
            for tok in TOKEN_RE.findall(line):
                occurrences.append((tok, corpus, rel, i, line.strip()[:400]))
    return occurrences, files_scanned


def batch_check(tokens, gitdir):
    """Resolve tokens through `git cat-file --batch-check`. Returns {tok: type}."""
    if not tokens:
        return {}
    proc = subprocess.run(
        ["git", "--git-dir", gitdir, "cat-file", "--batch-check"],
        input="\n".join(tokens) + "\n",
        capture_output=True,
        text=True,
    )
    out = {}
    for tok, line in zip(tokens, proc.stdout.splitlines()):
        parts = line.split()
        if len(parts) >= 2 and parts[1] in ("commit", "tree", "blob", "tag"):
            out[tok] = parts[1]
        else:
            out[tok] = None
    return out


def main():
    occurrences, files_scanned = scan()
    tokens = sorted({o[0] for o in occurrences})
    sys.stderr.write(
        f"scanned {files_scanned} files, {len(occurrences)} occurrences, "
        f"{len(tokens)} unique tokens\n"
    )

    full_db = os.path.join(FULL_DB)
    local_db = os.path.join(REPO, ".git")
    res_full = batch_check(tokens, full_db)
    res_local = batch_check(tokens, local_db)

    # Full 40-char OID for anything that resolved as a commit in the full DB.
    commit_toks = [t for t in tokens if res_full.get(t) == "commit"]
    full_oids = {}
    if commit_toks:
        proc = subprocess.run(
            ["git", "--git-dir", full_db, "cat-file", "--batch-check=%(objectname)"],
            input="\n".join(commit_toks) + "\n",
            capture_output=True,
            text=True,
        )
        for tok, line in zip(commit_toks, proc.stdout.splitlines()):
            full_oids[tok] = line.strip()

    by_token = defaultdict(list)
    for tok, corpus, rel, lineno, line in occurrences:
        by_token[tok].append(
            {"corpus": corpus, "file": rel, "line": lineno, "text": line}
        )

    records = {}
    for tok in tokens:
        n = len(tok)
        ft, lt = res_full.get(tok), res_local.get(tok)
        if n == 16:
            # Cache keys are 16 hex chars. Flag (do not reclassify) any that
            # ALSO resolve as a commit -- that would be a genuine ambiguity.
            bucket = "b_cachekey"
            ambiguous = ft is not None
        elif ft == "commit":
            bucket, ambiguous = "a_commit", False
        elif ft in ("tree", "blob") or lt in ("tree", "blob"):
            bucket, ambiguous = "c_blobtree", False
        elif tok.isdigit():
            bucket, ambiguous = "e_falsepos", False
        else:
            bucket, ambiguous = "d_identifier", False
        records[tok] = {
            "token": tok,
            "len": n,
            "bucket": bucket,
            "resolved_full": ft,
            "resolved_local": lt,
            "full_oid": full_oids.get(tok),
            "ambiguous_cachekey": ambiguous,
            "n_occurrences": len(by_token[tok]),
            "occurrences": by_token[tok],
        }

    with open(os.path.join(OUT, "inventory.json"), "w") as fh:
        json.dump(records, fh, indent=1, sort_keys=True)

    # ---- report ----
    counts_tok = defaultdict(int)
    counts_occ = defaultdict(int)
    for tok, rec in records.items():
        counts_tok[rec["bucket"]] += 1
        counts_occ[rec["bucket"]] += rec["n_occurrences"]
    print(f"files scanned      : {files_scanned}")
    print(f"total occurrences  : {len(occurrences)}")
    print(f"unique tokens      : {len(tokens)}")
    print()
    print(f"{'bucket':<16}{'unique':>9}{'occurrences':>14}")
    for b in ("a_commit", "b_cachekey", "c_blobtree", "d_identifier", "e_falsepos"):
        print(f"{b:<16}{counts_tok[b]:>9}{counts_occ[b]:>14}")
    print()
    amb = [t for t, r in records.items() if r["ambiguous_cachekey"]]
    print(f"16-char tokens that ALSO resolve as objects: {len(amb)} {amb[:5]}")
    print()
    print("length x bucket (unique tokens):")
    lb = defaultdict(int)
    for r in records.values():
        lb[(r["len"], r["bucket"])] += 1
    for n, b in sorted(lb):
        print(f"  len {n:>2}  {b:<16} {lb[(n, b)]}")


if __name__ == "__main__":
    main()
