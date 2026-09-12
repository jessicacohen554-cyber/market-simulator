"""Fail if a shard branch carries no bundle — rule 34 ``[R-SHARD-PROMOTABLE]`` (d).

THE INCIDENT THIS EXISTS FOR (miso-255, 2026-09-12): a five-year screen was
sharded, every shard prompt told its shard to ``.gitignore`` the bundle under
rule 29 ``[R-SCREEN]`` (c), and the parent reported a clean result. The owner
then ruled PROMOTE — and every bundle was stranded on an ephemeral shard
container the parent had no way to reach, so a decided promotion cost a full
re-solve of every year. Rule 31 ``[R-RETAIN]`` forbids DELETING a result; nothing
forbade producing one that was never RETRIEVABLE.

A parent runs this BEFORE it archives any shard and before it reports a solve as
promotable. It answers one question mechanically: **is the bundle in git, or only
on a container that is about to disappear?**

    uv run python scripts/check_shard_bundles.py \
        claude/miso255-promote-2020 claude/miso255-promote-2021 ...

    # or by explicit sha, which is what rule 33(d) says to record:
    uv run python scripts/check_shard_bundles.py --sha be5528b4... a2354f3a...

Exit 0 when every ref carries at least one file under a results bundle path;
exit 1 naming the refs that do not, with the re-solve warning.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

BUNDLE_ROOT = "results/calibration/"
# a bundle is these, not the .md report that rides alongside it
BUNDLE_MARKERS = ("meta.json", "run_config.json", "metrics.json", "hourly/")


def _added_bundle_files(ref: str, pin: str | None) -> list[str]:
    """Paths under ``results/calibration/`` that ``ref`` ADDED over its base.

    The base is the shard's own pin — ``<ref>^`` by default, which is the commit
    it branched from. Comparing against ``origin/main`` instead is WRONG and was
    the first version's bug: a shard pinned to an older sha inherits whatever
    bundles were committed then, and those inherited dirs made a bundle-less
    shard read OK. What matters is only what this shard produced.
    """
    base = pin or f"{ref}^"
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A", base, ref, "--", BUNDLE_ROOT],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise SystemExit(f"cannot diff {base}..{ref}: {out.stderr.strip()}")
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def _bundle_dirs(paths: list[str]) -> dict[str, int]:
    """Map bundle dir -> added-file count, for dirs that look like a real bundle."""
    dirs: dict[str, int] = {}
    for p in paths:
        rest = p[len(BUNDLE_ROOT) :]
        if "/" not in rest:
            continue  # a loose doc in results/calibration/, not a bundle
        head = rest.split("/", 1)[0]
        dirs[head] = dirs.get(head, 0) + 1
    return {
        d: n
        for d, n in dirs.items()
        if any(
            any(m in p for m in BUNDLE_MARKERS)
            for p in paths
            if p.startswith(f"{BUNDLE_ROOT}{d}/")
        )
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("refs", nargs="*", help="shard branches or shas to check")
    ap.add_argument(
        "--pin",
        default=None,
        help="the sha the shards were pinned to; default is each ref's own "
        "parent (<ref>^), which is what it branched from",
    )
    a = ap.parse_args()
    if not a.refs:
        ap.error("give at least one shard ref")

    bad: list[str] = []
    for ref in a.refs:
        own = _bundle_dirs(_added_bundle_files(ref, a.pin))
        if own:
            listed = ", ".join(f"{d} ({n} files)" for d, n in sorted(own.items()))
            print(f"OK    {ref}: {listed}")
        else:
            print(f"FAIL  {ref}: NO bundle of its own under {BUNDLE_ROOT}")
            bad.append(ref)

    if bad:
        print(
            "\nrule 34 [R-SHARD-PROMOTABLE](d): "
            f"{len(bad)} shard ref(s) carry no bundle.\n"
            "Their solve output exists ONLY on an ephemeral container. Do NOT\n"
            "archive those shards and do NOT report the run as promotable — a\n"
            "promotion from this state costs a FULL RE-SOLVE. Either have the\n"
            "shard push its bundle (`git add -f <out-dir>`), or say so, with the\n"
            "re-solve cost, at the time rather than when the owner asks."
        )
        return 1
    print(f"\nall {len(a.refs)} shard ref(s) carry a retrievable bundle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
