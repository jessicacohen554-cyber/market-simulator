#!/usr/bin/env python
"""Assemble the per-ISO §2.1b full-solve gate scorecard (FFR-3A-2).

The §2.1b gate opens, per ISO, on four criteria
(`docs/forecast-development-plan-2026-07.md` §0 / §2.1b):

  (a) completed backcast calibration,
  (b) green T1 proof-of-concept gates,
  (c) measured worth-the-compute evidence (crossover input gap + projected
      full-horizon cost),
  (d) an explicit, per-campaign owner authorization.

This script MEASURES (a)-(c) from committed artifacts plus this session's
scored legs, and reports (d) as the owner's, never inferred. It scores
NOTHING itself: every verdict it prints is read from an artifact another
instrument produced (`forecast_verdict`, `score_capacity_hindcast`,
`score_crossover`, `ff_readiness_battery`, `calibration_verdict`). It exists
so the scorecard is reproducible rather than hand-tabulated, and so a
successor can re-derive it without re-solving.

Rule 1 / rule 14: a criterion that misses is reported as it lands. Nothing
here widens a band or re-grades a miss, and no value is chosen to clear one.

Usage::

    python scripts/build_ffr3a2_scorecard.py \\
        --t1f-dir results/ffr3a2/t1f --t1h-dir results/ffr3a2/t1h \\
        --t1x-dir results/ffr3a2/t1x \\
        --ff3e results/ffr3a2/ff3e/ff3e_readiness_bundle.json \\
        --out results/ffr3a2/scorecard
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# The FF-2D rubric-verdict snapshot is the regression baseline (plan §7.5 — the
# committed input the forecast board is derived from).
FF_VERDICTS = REPO / "frontend/data/forecast/ff-verdicts.json"
MARKERS = REPO / "frontend/data/backcast/calibration-complete.json"
KEEPER_DIR = REPO / "frontend/data/backcast/keepers"
FREEZE = REPO / "frontend/data/backcast/holdout-freeze.json"


def _load(p: Path):
    """Return parsed JSON at ``p``, or None when it is absent/unreadable."""
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def scored_at_sha() -> str:
    """Return the short sha the scorecard is scored at (FFR-3B schema)."""
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


def cache_epoch() -> str:
    """Return the active cache-epoch label from the ledger in cache.py."""
    txt = (REPO / "src/market_sim/results/cache.py").read_text()
    for line in txt.splitlines():
        if line.startswith("**Epoch "):
            return line.split("**")[1].strip()
    return "unknown"


# --------------------------------------------------------------------------- #
# (a) backcast calibration
# --------------------------------------------------------------------------- #
def criterion_a() -> dict:
    """Per-ISO backcast-calibration state: keeper, determination, marker tier."""
    markers = _load(MARKERS) or {}
    complete = markers.get("complete", {}) or {}
    final = markers.get("final", {}) or {}
    out = {}
    for iso in ISOS:
        shard = _load(KEEPER_DIR / f"{iso}.json") or {}
        entry = complete.get(iso) or {}
        det = entry.get("determination") or ""
        # First clause of the determination sentence is the grade itself.
        grade = det.split(" on ")[0].strip() if det else None
        source = "calibration-complete.json"
        if not grade:
            # An ISO without a `complete` marker still carries a determination in
            # its keeper shard's promotion note. Read it there rather than
            # reporting "no determination", which would be false.
            blob = " ".join(v for v in shard.values() if isinstance(v, str))
            m = re.search(
                r"DETERMINATION[:\s]+((?:CALIBRATED-WITH-CAVEATS|CALIBRATED|NOT-YET))",
                blob,
            )
            if m:
                grade, source = m.group(1), f"keepers/{iso}.json (promotion note)"
            else:
                source = None
        out[iso] = {
            "keeper": shard.get("keeper"),
            "marker_complete": iso in complete,
            "marker_final": iso in final,
            "determination": grade,
            "determination_source": source,
            "determination_full": det or None,
        }
    return out


# --------------------------------------------------------------------------- #
# (b) T1 gate verdicts
# --------------------------------------------------------------------------- #
def _verdicts_in(run_dir: Path, tier: str) -> dict:
    """Collect `forecast_verdict` sidecars written under ``run_dir``."""
    found = {}
    if not run_dir or not run_dir.exists():
        return found
    for p in sorted(run_dir.rglob("forecast_verdict.json")):
        v = _load(p)
        if not v:
            continue
        iso = (v.get("iso") or "").upper()
        if iso:
            found.setdefault(iso, []).append({"path": str(p), "tier": tier, **v})
    return found


def criterion_b(t1f: Path, t1h: Path, t1x: Path) -> dict:
    """Per-ISO T1-F / T1-H / T1-X determinations measured THIS session."""
    got = {
        "t1f": _verdicts_in(t1f, "t1f"),
        "t1h": _verdicts_in(t1h, "t1h"),
        "t1x": _verdicts_in(t1x, "t1x"),
    }
    out = {}
    for iso in ISOS:
        row = {}
        for tier, byiso in got.items():
            entries = byiso.get(iso) or []
            row[tier] = (
                {
                    "determination": entries[0].get("determination"),
                    "categories": {
                        c: d.get("status")
                        for c, d in (entries[0].get("categories") or {}).items()
                    },
                    "reasons": entries[0].get("reasons"),
                }
                if entries
                else None
            )
        out[iso] = row
    return out


# --------------------------------------------------------------------------- #
# (c) worth-the-compute
# --------------------------------------------------------------------------- #
def criterion_c(ff3e: Path, t1x: Path) -> dict:
    """Projected full-horizon cost (FF-3E part d) + the T1-X measured input gap."""
    bundle = _load(ff3e) or {}
    proj = (bundle.get("wall_rss_projection") or {}).get("per_iso") or {}
    out = {}
    for iso in ISOS:
        p = proj.get(iso) or {}
        out[iso] = {
            "projected_hours": p.get("projected_h"),
            "lower_hours": p.get("lower_bound_h"),
            "peak_gb": p.get("proj_peak_rss_gb"),
            "must_run_solo": p.get("no_corun"),
        }
    # crossover input gap, when this session scored one
    for p in sorted((t1x or Path("/nonexistent")).rglob("crossover_score*.json")):
        sc = _load(p) or {}
        iso = (sc.get("iso") or "").upper()
        if iso in out:
            out[iso]["crossover_score"] = str(p)
    return out


# --------------------------------------------------------------------------- #
def regression_vs_ff2d(measured: dict) -> dict:
    """Diff this session's per-ISO determinations against the FF-2D snapshot."""
    base = _load(FF_VERDICTS) or {}
    by_iso_tier = {}
    for _id, v in base.items():
        by_iso_tier.setdefault((v.get("iso"), v.get("tier")), []).append((_id, v))
    out = {}
    for iso in ISOS:
        rows = {}
        for tier in ("t1f", "t1h", "t1x"):
            prior = by_iso_tier.get((iso, tier)) or []
            now = (measured.get(iso) or {}).get(tier)
            rows[tier] = {
                "ff2d": [
                    {
                        "id": i,
                        "determination": v.get("determination"),
                        "categories": {
                            c: d.get("status")
                            for c, d in (v.get("categories") or {}).items()
                        },
                    }
                    for i, v in prior
                ],
                "now": now,
            }
        out[iso] = rows
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--t1f-dir", type=Path, default=REPO / "results/ffr3a2/t1f")
    ap.add_argument("--t1h-dir", type=Path, default=REPO / "results/ffr3a2/t1h")
    ap.add_argument("--t1x-dir", type=Path, default=REPO / "results/ffr3a2/t1x")
    ap.add_argument(
        "--ff3e",
        type=Path,
        default=REPO / "results/ffr3a2/ff3e/ff3e_readiness_bundle.json",
    )
    ap.add_argument("--out", type=Path, default=REPO / "results/ffr3a2/scorecard")
    args = ap.parse_args(argv)

    a = criterion_a()
    b = criterion_b(args.t1f_dir, args.t1h_dir, args.t1x_dir)
    c = criterion_c(args.ff3e, args.t1x_dir)
    freeze = _load(FREEZE) or {}

    payload = {
        "scored_at_sha": scored_at_sha(),
        "cache_epoch": cache_epoch(),
        "holdout_freeze_active": bool(freeze.get("active")),
        "criterion_a_backcast_calibration": a,
        "criterion_b_t1_gates": b,
        "criterion_c_worth_the_compute": c,
        "criterion_d_owner_authorization": (
            "NOT MEASURED HERE — an explicit, per-campaign owner decision. "
            "No ISO carries one; `final` is empty by design."
        ),
        "regression_vs_ff2d": regression_vs_ff2d(b),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "scorecard.json").write_text(json.dumps(payload, indent=1))

    # Human table
    lines = [
        f"§2.1b GATE SCORECARD — scored_at_sha={payload['scored_at_sha']} "
        f"cache_epoch={payload['cache_epoch']} "
        f"holdout_freeze_active={payload['holdout_freeze_active']}",
        "",
        f"{'ISO':6s} {'(a) backcast':34s} {'mk':4s} {'(b) t1f':8s} {'t1h':8s} "
        f"{'t1x':8s} {'(c) proj h':10s} solo",
    ]
    for iso in ISOS:
        ra, rb, rc = a[iso], b[iso], c[iso]
        det = (ra["determination"] or "—")[:33]
        mk = ("C" if ra["marker_complete"] else "-") + (
            "F" if ra["marker_final"] else "-"
        )
        f = (rb["t1f"] or {}).get("determination") or "—"
        h = (rb["t1h"] or {}).get("determination") or "—"
        x = (rb["t1x"] or {}).get("determination") or "—"
        ph = rc.get("projected_hours")
        lines.append(
            f"{iso:6s} {det:34s} {mk:4s} {f:8s} {h:8s} {x:8s} "
            f"{(str(ph) if ph is not None else '—'):10s} {rc.get('must_run_solo')}"
        )
    txt = "\n".join(lines)
    (args.out / "scorecard.txt").write_text(txt + "\n")
    print(txt)
    print(f"\nwrote {args.out}/scorecard.json + scorecard.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
