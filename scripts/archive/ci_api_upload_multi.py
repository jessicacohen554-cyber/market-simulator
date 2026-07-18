#!/usr/bin/env python3
"""Commit several runs' dashboard files to a branch via the GitHub Data API.

Multi-run generalization of ``scripts/archive/ci_api_upload.py`` (same blob -> tree ->
commit -> ref flow, same reason: ``git push`` over this remote 413/500s on the
~400-600 KB run payloads even from a CI runner). Differences:

* accepts repeated ``--rid RID --bundle DIR`` pairs (zipped in order) so a
  main run and its zero-forcing ablation twin land in ONE commit;
* parents the commit on the tip of the TARGET BRANCH (falling back to main
  when the branch does not exist yet), so it stacks on prior branch work
  instead of silently discarding it — ci_api_upload.py parents on main and
  force-patches, which drops any earlier commit on the branch when called
  twice in a row.
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
    ap.add_argument("--rid", action="append", required=True)
    ap.add_argument("--bundle", action="append", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument(
        "--bench-iso",
        default="CAISO",
        help="ISO whose bench/<ISO>/*.json.gz parts ride along (once).",
    )
    ap.add_argument(
        "--extra",
        action="append",
        default=[],
        help="Additional repo-relative file(s) to include in the same commit "
        "(e.g. a bundle's calibration_attestation.json, an appended "
        "docs/calibration-log.md, a workflow-patched script). Reads from "
        "disk, so files far beyond the MCP relay's single-call ceiling "
        "still upload.",
    )
    a = ap.parse_args()
    if len(a.rid) != len(a.bundle):
        sys.exit("--rid and --bundle must be given the same number of times")

    files = []
    for rid, bundle in zip(a.rid, a.bundle):
        files += [
            "frontend/data/backcast/registry/%s.json" % rid,
            "frontend/data/backcast/runs/%s.js" % rid,
            "%s/meta.json" % bundle,
            "%s/run_config.json" % bundle,
            "%s/metrics.json" % bundle,
            "%s/legitimacy_diagnostics.json" % bundle,
            "%s/calibration_attestation.json" % bundle,
        ]
    files += sorted(
        glob.glob("frontend/data/backcast/bench/%s/*.json.gz" % a.bench_iso)
    )
    files += list(a.extra)
    files = [f for f in files if os.path.exists(f)]

    try:
        base = req("GET", "/repos/%s/%s/git/ref/heads/%s" % (OWNER, REPO, a.branch))[
            "object"
        ]["sha"]
    except urllib.error.HTTPError:
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
        print("blob %-70s -> %s" % (p, blob["sha"][:8]))

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
        req("PATCH", ref_path, {"sha": commit})
    except urllib.error.HTTPError:
        req(
            "POST",
            "/repos/%s/%s/git/refs" % (OWNER, REPO),
            {"ref": "refs/heads/%s" % a.branch, "sha": commit},
        )
    print(
        "committed %d files as %s on %s (parent %s)"
        % (len(files), commit[:8], a.branch, base[:8])
    )


if __name__ == "__main__":
    main()
