#!/usr/bin/env python3
"""miso-298 gate table (ZERO LP): keeper vs arm, every criterion-year, both ways.

Scores two REGISTERED run ids with the live scorer
(``calibration_verdict.determine_from_artifacts``) and prints, per criterion
record (C1 class-year, C2 family-year, C3a/C3b/C3c year, C4-C8), the keeper's
and the arm's status and magnitude side by side, flagging every status flip.
Writes the same as JSON so the RESULT cites committed numbers.

Usage (repo root)::

    .venv/bin/python scripts/probes/_miso298_gate_table.py \\
        --keeper 2026-09-28-miso-280-splitremap --arm <arm run id> \\
        --out results/phase0/miso/_miso298_gate_table.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts import calibration_verdict as cv  # noqa: E402


def _flatten(det: dict) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for crit, blk in sorted(det.get("criteria", {}).items()):
        rows[f"{crit}"] = {
            "status": blk.get("status"),
            "tier": blk.get("tier"),
            "caveat_kind": blk.get("caveat_kind"),
        }
        for r in blk.get("records") or []:
            key = f"{crit}|{r.get('key')}|{r.get('year')}"
            rows[key] = {
                "status": r.get("status"),
                "model": r.get("model"),
                "actual": r.get("actual"),
                "magnitude": r.get("magnitude"),
            }
    return rows


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--keeper", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    dets = {}
    for tag, rid in (("keeper", args.keeper), ("arm", args.arm)):
        d = cv.determine_from_artifacts(rid, cv.load_artifacts(rid))
        dets[tag] = d if isinstance(d, dict) else d.__dict__
    k, a = _flatten(dets["keeper"]), _flatten(dets["arm"])
    out = {
        "keeper": args.keeper,
        "arm": args.arm,
        "determination": {
            t: {kk: vv for kk, vv in dets[t].items() if kk != "criteria"} for t in dets
        },
        "rows": {},
        "flips": [],
    }
    print(f"| criterion | key | year | {args.keeper} | {args.arm} | flip |")
    print("|---|---|---|---|---|---|")
    for key in sorted(set(k) | set(a)):
        kr, ar = k.get(key, {}), a.get(key, {})
        flip = (kr.get("status") != ar.get("status")) and "da_diagnostic" not in key
        out["rows"][key] = {"keeper": kr, "arm": ar, "flip": flip}
        if flip:
            out["flips"].append(key)
        if kr.get("status") == "SKIPPED" and ar.get("status") == "SKIPPED":
            continue
        parts = key.split("|")
        crit, kk, yy = (parts + ["", ""])[:3]
        km = kr.get("magnitude") or ""
        am = ar.get("magnitude") or ""
        if (
            kr.get("model") is not None
            and kr.get("actual") is not None
            and isinstance(kr.get("model"), (int, float))
            and isinstance(kr.get("actual"), (int, float))
            and crit == "fuelmix"
        ):
            km = f"{kr['model'] - kr['actual']:+.2f} TWh"
            am = (
                f"{ar['model'] - ar['actual']:+.2f} TWh"
                if isinstance(ar.get("model"), (int, float))
                and isinstance(ar.get("actual"), (int, float))
                else am
            )
        print(
            f"| {crit} | {kk} | {yy} | {kr.get('status')} {str(km)[:60]} | "
            f"{ar.get('status')} {str(am)[:60]} | {'**FLIP**' if flip else ''} |"
        )
    print("\nflips:", out["flips"])
    print(
        "determination:", json.dumps(out["determination"], indent=1, default=str)[:1500]
    )
    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
