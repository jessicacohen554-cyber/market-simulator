#!/usr/bin/env python3
"""hydro-2 (ZERO LP): criterion-by-criterion diff of two registered runs' verdicts.

Prints per-criterion status for control vs arm, then every scored record whose
status or model value moved (``calibration_verdict.determine``).

Usage: python3 scripts/probes/hydro2_pjm_verdict_diff.py <control_run_id> <arm_run_id>
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts import calibration_verdict as cv  # noqa: E402


def records(v: dict) -> dict:
    """(criterion, key, year) -> record, over every scored record."""
    out = {}
    crit = v["criteria"]
    for name, c in (crit.items() if isinstance(crit, dict) else crit):
        for r in c.get("records") or []:
            out[(name, str(r.get("key")), r.get("year"))] = r
    return out


def main() -> None:
    """Print the determination and criterion diff between two runs."""
    a, b = cv.determine(sys.argv[1]), cv.determine(sys.argv[2])
    print(f"determination: {a['determination']} -> {b['determination']}")
    sa, sb = dict(a["criteria"]), dict(b["criteria"])
    for k in sa:
        print(f"  {sa[k]['label']:45s} {sa[k]['status']:8s} -> {sb.get(k, {}).get('status')}")
    ra, rb = records(a), records(b)
    print("\nmoved records (status change, or |d model| > 0):")
    for key in sorted(set(ra) | set(rb), key=str):
        x, y = ra.get(key, {}), rb.get(key, {})
        mx, my = x.get("model"), y.get("model")
        moved = x.get("status") != y.get("status")
        if isinstance(mx, (int, float)) and isinstance(my, (int, float)):
            moved = moved or abs(my - mx) > 1e-6
        if moved:
            print(f"  {key}: {x.get('status')} -> {y.get('status')}  model {mx} -> {my}  actual {y.get('actual', x.get('actual'))}")


if __name__ == "__main__":
    main()
