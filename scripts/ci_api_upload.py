#!/usr/bin/env python3
"""Commit per-run dashboard files to a branch via the GitHub Data API.

`git push` over this remote rejects large packs (HTTP 413 from a local push,
HTTP 500 / "remote hung up" from a CI runner) whenever the pack carries the
~600 KB run payload. This commits the per-run files server-side through the git
Data API (blob -> tree -> commit -> ref), exactly as mcp__github__push_files
does, so it never negotiates a pack and never hits that wall. Parents the new
commit on the live tip of main, so the branch is a clean per-run diff.
"""

import argparse
import base64
import glob
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
    ap.add_argument("--rid", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--message", required=True)
    a = ap.parse_args()

    files = [
        "frontend/data/backcast/registry/%s.json" % a.rid,
        "frontend/data/backcast/runs/%s.js" % a.rid,
        "%s/meta.json" % a.bundle,
        "%s/run_config.json" % a.bundle,
        "%s/metrics.json" % a.bundle,
        "%s/legitimacy_diagnostics.json" % a.bundle,
    ]
    files += sorted(glob.glob("frontend/data/backcast/bench/CAISO/*.json.gz"))
    files = [f for f in files if os.path.exists(f)]

    base = req("GET", "/repos/%s/%s/git/ref/heads/main" % (OWNER, REPO))["object"][
        "sha"
    ]
    base_tree = req("GET", "/repos/%s/%s/git/commits/%s" % (OWNER, REPO, base))["tree"][
        "sha"
    ]

    tree = []
    for p in files:
        with open(p, "rb") as fh:
            payload = base64.b64encode(fh.read()).decode()
        blob = req(
            "POST",
            "/repos/%s/%s/git/blobs" % (OWNER, REPO),
            {"content": payload, "encoding": "base64"},
        )
        tree.append({"path": p, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print("blob %-64s -> %s" % (p, blob["sha"][:8]))

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
    print("committed %d files as %s on %s" % (len(files), commit[:8], a.branch))


if __name__ == "__main__":
    main()
