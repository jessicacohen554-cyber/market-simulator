#!/usr/bin/env python3
"""Commit files to a branch via the GitHub Data API, PARENTED ON MAIN.

Variant of ``scripts/ci_api_upload_multi.py`` for the rebase-refresh case:
when a session branch's history conflicts with main (two sessions spliced
the same top-of-file region of docs/calibration-log.md), a commit parented
on the BRANCH can never merge cleanly. This uploader builds the commit on
top of CURRENT ``main``'s tree instead and force-updates the branch ref to
it — the branch becomes main + exactly the given changes, so its PR merges
clean. Files are read from disk (no relay ceiling). ``--delete`` removes a
path in the same commit (tree entry with a null sha) — used for registry
prunes that must land atomically with the dashboard files that reference
them. Never include ``.github/workflows/*`` in the commit: the runner token
cannot update a ref whose new commits touch workflows (caiso-77 postmortem).

Usage:
  GH_TOKEN=... python scripts/ci_api_upload_onmain.py \
      --branch <branch> --message <msg> --file a.md --file b.js \
      --delete old/registry.json
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

OWNER = "jessicacohen554-cyber"
REPO = "market-simulator"
API = "https://api.github.com"


def req(method, path, body=None):
    """Issue an authenticated GitHub API request and return the parsed JSON."""
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", "Bearer " + os.environ["GH_TOKEN"])
    r.add_header("Accept", "application/vnd.github+json")
    if data:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.stderr.write(
            "%s %s -> %s: %s\n" % (method, path, e.code, e.read().decode())
        )
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument(
        "--delete",
        action="append",
        default=[],
        help="Repo path to remove in the same commit (null-sha tree entry).",
    )
    a = ap.parse_args()
    if not a.file and not a.delete:
        sys.exit("nothing to do: give at least one --file or --delete")

    base = req("GET", "/repos/%s/%s/git/ref/heads/main" % (OWNER, REPO))["object"][
        "sha"
    ]
    base_tree = req("GET", "/repos/%s/%s/git/commits/%s" % (OWNER, REPO, base))["tree"][
        "sha"
    ]

    tree = []
    for p in a.file:
        with open(p, "rb") as fh:
            payload = base64.b64encode(fh.read()).decode()
        blob = req(
            "POST",
            "/repos/%s/%s/git/blobs" % (OWNER, REPO),
            {"content": payload, "encoding": "base64"},
        )
        tree.append({"path": p, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("blob %-60s -> %s" % (p, blob["sha"][:8]))
    for p in a.delete:
        tree.append({"path": p, "mode": "100644", "type": "blob", "sha": None})
        print("del  %s" % p)

    new_tree = req(
        "POST",
        "/repos/%s/%s/git/trees" % (OWNER, REPO),
        {"base_tree": base_tree, "tree": tree},
    )["sha"]
    commit = req(
        "POST",
        "/repos/%s/%s/git/commits" % (OWNER, REPO),
        {"message": a.message, "tree": new_tree, "parents": [base]},
    )["sha"]

    ref_path = "/repos/%s/%s/git/refs/heads/%s" % (OWNER, REPO, a.branch)
    try:
        req("PATCH", ref_path, {"sha": commit, "force": True})
    except urllib.error.HTTPError:
        req(
            "POST",
            "/repos/%s/%s/git/refs" % (OWNER, REPO),
            {"ref": "refs/heads/%s" % a.branch, "sha": commit},
        )
    print("branch %s -> %s (parent: main %s)" % (a.branch, commit[:8], base[:8]))


if __name__ == "__main__":
    main()
