#!/usr/bin/env python3
"""nyiso-148 — size the cross-ISO exposure of the stale-benchmark-part defect.

WHY (owner ruling 2026-08-21, session nyiso-148): the shared per-(ISO, year)
benchmark part is refreshed only when a registering bundle happens to carry the
benchmark inputs, so a part can sit un-refreshed for weeks while the builder
that produces it moves underneath. NYISO's part had been unchanged since
2026-08-17; regenerating it flipped EVERY registered NYISO run to NOT-YET
(`FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md`). The
mechanism is ISO-agnostic, so the owner asked how large the exposure is.

WHAT THIS MEASURES, and what it deliberately does not. Regenerating every ISO's
part would need each ISO's raw data hydrated and a bundle carrying benchmark
inputs — hours of solve for a sizing question. This measures the exposure
EXACTLY at the resolution git already carries:

    a committed part is POTENTIALLY STALE iff the benchmark-builder code path
    changed after that part was last written.

That is an UPPER BOUND on the exposure — a builder change need not move a given
ISO's numbers — and it is stated as one. It is also the only bound available
without a per-ISO regeneration, and it answers the question that matters: how
many ISOs' keeper determinations rest on a part that predates the builder.

The one ISO where the bound was CONFIRMED tight by actual regeneration is
NYISO, where the flip is real and now landed.

Read-only: no data is written, no part is regenerated, nothing is committed.

Usage:
    python scripts/probes/_nyiso148_bench_staleness_sweep.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench"

#: The code path that produces a bench part's payload. `build_payload` in
#: render_calibration_html computes the `bench` dict (incl. `classFull`);
#: render_backcast writes it to the part; backcast_assets does the encoding.
#: A change to any of these can move a part's contents.
BUILDER_PATHS: tuple[str, ...] = (
    "scripts/render_calibration_html.py",
    "scripts/render_backcast.py",
    "scripts/lib/backcast_assets.py",
)

#: The builder's IMPORT CLOSURE that can move a part's numbers: the class map,
#: the CHP shares and the benchmark reconciliation all come from the engine.
#: Restricting the measure to the three scripts above UNDERSTATES the exposure,
#: which is why both are reported.
CLOSURE_PATHS: tuple[str, ...] = (
    "src/market_sim/data/",
    "src/market_sim/config/",
)

#: Builder commits that are provably GATED and therefore cannot move a part
#: they do not apply to — annotated so the bound is not read as tighter than
#: it is. 01db36d (nyiso-147) touches `_btm_share` only behind
#: `meta["nyiso_chp_btm_measured"] and meta["iso"] == "NYISO"`, so it can move
#: NYISO's two measured-BTM per-plant fields and NOTHING else — it explains
#: neither the ~4 TWh NYISO classFull drift nor any non-NYISO part.
GATED_BUILDER_COMMITS: dict[str, str] = {
    "01db36d": (
        "nyiso-147 _btm_share measured override — gated on the bundle's own "
        "nyiso_chp_btm_measured flag AND iso == NYISO; cannot move any other "
        "ISO's part, and does not touch the classFull reconciliation layer"
    ),
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=False
    ).stdout.strip()


def last_commit(path: str) -> tuple[str, str]:
    """Return ``(sha, iso-date)`` of the last commit touching *path*."""
    out = _git("log", "-1", "--format=%h %ad", "--date=short", "--", path)
    if not out:
        return ("", "")
    sha, _, date = out.partition(" ")
    return sha, date


def commits_since(
    paths: tuple[str, ...], date: str, exclude_sha: str = ""
) -> list[dict]:
    """Return commits touching *paths* after *date*, excluding *exclude_sha*.

    ``--since`` is day-granular, so the commit that WROTE the part is itself
    returned when it lands on the same day; excluding it by sha is what keeps
    the count from reporting a part as one commit behind itself.
    """
    if not date:
        return []
    out = _git(
        "log", f"--since={date} 23:59:59", "--format=%h\t%ad\t%s",
        "--date=short", "--", *paths,
    )
    rows = []
    for line in out.splitlines():
        sha, _, rest = line.partition("\t")
        d, _, subj = rest.partition("\t")
        if exclude_sha and sha == exclude_sha:
            continue
        rows.append(
            {
                "sha": sha,
                "date": d,
                "subject": subj[:110],
                "gated_note": GATED_BUILDER_COMMITS.get(sha),
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out", default="results/calibration/_nyiso148_bench_staleness_sweep.json"
    )
    args = ap.parse_args()

    builder = {p: last_commit(p) for p in BUILDER_PATHS if (REPO / p).exists()}
    builder_latest = max((d for _, d in builder.values() if d), default="")
    print("BENCHMARK-BUILDER CODE PATH — last change per file")
    for p, (sha, date) in sorted(builder.items()):
        print(f"  {date}  {sha:<9} {p}")
    print(f"  => builder last moved: {builder_latest}\n")

    keepers = json.loads(
        (REPO / "frontend/data/backcast/keepers/keepers.json").read_text()
    ) if (REPO / "frontend/data/backcast/keepers/keepers.json").exists() else {}

    rows: list[dict] = []
    for iso_dir in sorted(BENCH_DIR.iterdir()):
        if not iso_dir.is_dir():
            continue
        for part in sorted(iso_dir.glob("*.json.gz")):
            rel = str(part.relative_to(REPO))
            sha, date = last_commit(rel)
            since_builder = commits_since(BUILDER_PATHS, date, sha)
            since_closure = commits_since(CLOSURE_PATHS, date, sha)
            ungated = [c for c in since_builder if not c["gated_note"]]
            rows.append(
                {
                    "iso": iso_dir.name,
                    "year": int(part.stem.split(".")[0]),
                    "part": rel,
                    "last_written": date,
                    "last_written_sha": sha,
                    "builder_commits_since": since_builder,
                    "builder_commits_since_ungated": len(ungated),
                    "closure_commits_since": len(since_closure),
                    "potentially_stale": bool(
                        date and (ungated or since_closure)
                    ),
                }
            )

    print(
        f"{'ISO':<8}{'year':<7}{'part written':<14}"
        f"{'builder cmts':<14}{'engine cmts':<13}{'verdict'}"
    )
    by_iso: dict[str, list[dict]] = {}
    for r in rows:
        by_iso.setdefault(r["iso"], []).append(r)
        print(
            f"{r['iso']:<8}{r['year']:<7}"
            f"{r['last_written'] or '(uncommitted)':<14}"
            f"{len(r['builder_commits_since'])} ({r['builder_commits_since_ungated']} ungated){'':<1}"
            f"{r['closure_commits_since']:<13}"
            f"{'POTENTIALLY STALE' if r['potentially_stale'] else 'current'}"
        )

    exposed = sorted({r["iso"] for r in rows if r["potentially_stale"]})
    print(f"\nISOs with at least one potentially-stale part: {exposed or 'none'}")
    print(
        "CONFIRMED by regeneration: NYISO (every registered run flipped to "
        "NOT-YET; keeper determination restated by owner ruling 2026-08-21)."
    )
    print(
        "The rest are an UPPER BOUND — a builder change need not move a given "
        "ISO's numbers. Confirming each needs that ISO's raw data hydrated and "
        "a bundle carrying benchmark inputs."
    )

    out = {
        "session": "nyiso-148",
        "measure": (
            "a committed bench part is POTENTIALLY STALE iff the "
            "benchmark-builder code path changed after the part was last "
            "written; an UPPER BOUND on the exposure, not a confirmation"
        ),
        "builder_paths": {p: {"sha": s, "date": d} for p, (s, d) in builder.items()},
        "builder_last_moved": builder_latest,
        "parts": rows,
        "isos_exposed": exposed,
        "confirmed_by_regeneration": ["NYISO"],
        "keepers": keepers if isinstance(keepers, dict) else {},
    }
    (REPO / args.out).write_text(json.dumps(out, indent=1))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
