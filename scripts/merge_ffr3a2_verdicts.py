#!/usr/bin/env python
"""Merge this session's rubric verdicts into the committed FF verdict snapshot.

``frontend/data/forecast/ff-verdicts.json`` is a COMMITTED input to the forecast
board (plan §7.5): ``register_forecast_run.py --reindex`` bakes its FC-1..FC-8
verdicts into every generated registry sidecar and run payload, and
``ff_readiness_battery._t1f_verdict`` reads it to fill gate (b) of the §2.1b
scorecard.

THE ONE DESIGN DECISION HERE, stated because it is not reversible by inspection:

``_t1f_verdict`` looks up the BARE key ``"<iso>-t1f"``. So a purely additive
merge — writing ``"<iso>-t1f-ffr3a2"`` alongside the FF-2D row, the convention
``ercot-t1x-ffr2a`` followed — would leave every board reader still showing the
FF-2D determination while this session's measurement sat in a key nothing reads.
Overwriting the bare key instead makes the board current but destroys the
regression baseline the close-out report is built on.

So this does BOTH, in this order:

  1. **Preserve** the existing FF-2D row under ``"<iso>-<tier>-ff2d"`` (once; a
     re-run never re-preserves an already-preserved row, so the baseline cannot
     be overwritten by its own successor).
  2. **Overwrite** the bare ``"<iso>-<tier>"`` key with this session's verdict,
     stamped with ``scored_at_sha``/``cache_epoch``/``session`` provenance.

The FF-2D numbers therefore stay quotable and diffable, and every board reader —
including the hardcoded one — shows what was actually measured at this HEAD.

Rule 1 / rule 14: this moves no band and re-grades nothing. Every verdict written
is copied verbatim from a `forecast_verdict.json` another instrument produced.

Usage::

    python scripts/merge_ffr3a2_verdicts.py --run-dir results/ffr3a2 --apply
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERDICTS = REPO / "frontend/data/forecast/ff-verdicts.json"
SESSION = "FFR-3A-2"


def _sha() -> str:
    """Return the short sha this merge is stamped with."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _epoch() -> str:
    """Return the active cache-epoch label from the ledger in cache.py."""
    for line in (REPO / "src/market_sim/results/cache.py").read_text().splitlines():
        if line.startswith("**Epoch "):
            return line.split("**")[1].strip()
    return "unknown"


def collect(run_dir: Path) -> dict:
    """Return {(iso, tier): verdict} for every scored leg under ``run_dir``."""
    out: dict[tuple[str, str], dict] = {}
    for p in sorted(run_dir.rglob("forecast_verdict.json")):
        try:
            v = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        iso = (v.get("iso") or "").upper()
        tier = (v.get("tier") or "").lower()
        if not iso or not tier:
            continue
        # A control arm is evidence for attribution, not a board row: it would
        # collide with its own treatment on the bare key.
        if "control" in p.parent.name:
            continue
        out[(iso, tier)] = v
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, default=REPO / "results/ffr3a2")
    ap.add_argument(
        "--apply", action="store_true", help="Write the file (default: dry run)."
    )
    args = ap.parse_args(argv)

    doc = json.loads(VERDICTS.read_text())
    found = collect(args.run_dir)
    if not found:
        print("no scored legs under", args.run_dir, "— nothing to merge")
        return 0

    sha, epoch = _sha(), _epoch()
    changes = []
    for (iso, tier), v in sorted(found.items()):
        bare = f"{iso.lower()}-{tier}"
        preserved = f"{bare}-ff2d"
        if bare in doc and preserved not in doc:
            doc[preserved] = dict(doc[bare])
            doc[preserved].setdefault("provenance", {})
            doc[preserved]["provenance"] = {
                "note": (
                    "FF-2D baseline, preserved verbatim by FFR-3A-2 before the bare "
                    "key was refreshed. Quotable as the regression baseline."
                )
            }
            changes.append(f"  preserve {bare} -> {preserved}")
        row = dict(v)
        row["provenance"] = {
            "session": SESSION,
            "scored_at_sha": sha,
            "cache_epoch": epoch,
        }
        prior = (doc.get(bare) or {}).get("determination")
        doc[bare] = row
        changes.append(f"  update   {bare}: {prior} -> {row.get('determination')}")

    print(f"ff-verdicts.json merge ({'APPLY' if args.apply else 'DRY RUN'})")
    print("\n".join(changes))
    if args.apply:
        VERDICTS.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print(f"wrote {VERDICTS} ({len(doc)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
