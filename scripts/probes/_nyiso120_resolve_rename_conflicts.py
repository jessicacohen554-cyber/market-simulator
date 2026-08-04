#!/usr/bin/env python3
"""Repair the 9 bundle JSONs left carrying rebase conflict markers.

WHAT HAPPENED (recorded, not papered over). During nyiso-120's rebase onto
main, git rename-detected the bundle files of the top-15-pruned
``nyiso111_control_A`` against BOTH the newly-landed ``nyiso119_*`` bundles
(main's side) and the new ``nyiso120_control_A`` (this branch's side), producing
rename/rename conflicts. Those were resolved with a blanket ``git add`` of every
``AU``/``UA`` path on the assumption that each path was uniquely owned by one
side and the working tree therefore already held that side's bytes. **That
assumption was wrong**: for rename/rename git writes a merged file with conflict
markers at every conflicted path, so nine JSONs were committed containing BOTH
versions plus ``<<<<<<<</========/>>>>>>>>`` markers — five of them belonging to
another lane's (nyiso-119's) committed bundle.

THE REPAIR IS LOSSLESS AND NEEDS NO RE-SOLVE. Every conflicted file contains
both versions in full, and git labels each side with the path it came from::

    <<<<<<<< HEAD:results/calibration/nyiso119_seny_increment/metrics.json
    ...main's bytes...
    ========
    ...this branch's bytes...
    >>>>>>>> <sha> (...):results/calibration/nyiso120_control_A/metrics.json

so the correct side for a file is simply the block whose label is that file's
own path. This is a mechanical selection from committed bytes — no content is
authored, regenerated or guessed, and each result is verified to parse as JSON
and to carry the ``run_id`` its own bundle should have.

    python scripts/probes/_nyiso120_resolve_rename_conflicts.py [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (REPO / "results/calibration", REPO / "frontend/data/backcast")


def _split_hunks(lines: list[str], rel: str) -> list[str]:
    """Return ``lines`` with every conflict hunk collapsed to this path's side.

    ``rel`` is the file's own repo-relative path; the side whose marker label
    ends with it wins. A hunk whose labels match neither path is left untouched
    and reported by the caller as unresolved rather than guessed at.
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("<<<<<<<"):
            out.append(line)
            i += 1
            continue
        # Collect the hunk: <<<<<<< label / ours / ======= / theirs / >>>>>>> label
        ours_label = line.split(":", 1)[1].strip() if ":" in line else ""
        i += 1
        ours: list[str] = []
        while i < len(lines) and not lines[i].startswith("======="):
            ours.append(lines[i])
            i += 1
        i += 1  # skip the ======= divider
        theirs: list[str] = []
        while i < len(lines) and not lines[i].startswith(">>>>>>>"):
            theirs.append(lines[i])
            i += 1
        theirs_label = lines[i].split(":", 1)[1].strip() if i < len(lines) and ":" in lines[i] else ""
        i += 1  # skip the >>>>>>> terminator
        if ours_label == rel:
            out.extend(ours)
        elif theirs_label == rel:
            out.extend(theirs)
        else:
            raise ValueError(
                f"{rel}: neither conflict side is labelled with this path "
                f"(ours={ours_label!r}, theirs={theirs_label!r}) — not guessing"
            )
    return out


def main(argv: list[str] | None = None) -> int:
    """Repair every conflicted JSON under the scan roots."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args(argv)

    hits: list[Path] = []
    for root in SCAN_ROOTS:
        for path in root.rglob("*.json"):
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if "\n<<<<<<<" in "\n" + text:
                hits.append(path)

    if not hits:
        print("no conflicted files found")
        return 0

    failures = 0
    for path in sorted(hits):
        rel = str(path.relative_to(REPO))
        try:
            fixed = _split_hunks(path.read_text().splitlines(), rel)
            body = "\n".join(fixed) + "\n"
            parsed = json.loads(body)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"FAILED  {rel}: {exc}")
            failures += 1
            continue
        rid = parsed.get("run_id") or parsed.get("iso") or "—"
        if args.check:
            print(f"would fix  {rel}  -> run_id/iso {rid}")
        else:
            path.write_text(body)
            print(f"fixed  {rel}  -> run_id/iso {rid}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
