"""nyiso-188: side-by-side criteria of two registered runs (scorer output only).

Runs ``scripts/calibration_verdict.py --json`` on each bundle (committed
artifacts only — never a solve) and prints, per criterion record, the
baseline vs arm magnitude, flagging PASS -> FAIL flips on C2 / C3a / C3b / C8
(the pre-registered rejection rule) and every other status change.

Usage:
    python scripts/probes/nyiso188_verdict_compare.py <baseline_bundle> <arm_bundle>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REJECT_ON = {"sysvol", "price_mean", "price_shape", "forced_share"}


def verdict(bundle: str) -> dict:
    """Return the verdict JSON for one bundle."""
    # calibration_verdict exits non-zero on a NOT-YET determination; the JSON
    # on stdout is complete either way.
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json", bundle],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        check=False,
    )
    return json.loads(proc.stdout)


def main() -> None:
    """CLI entry point."""
    base, arm = verdict(sys.argv[1]), verdict(sys.argv[2])
    print(f"baseline {base['run_id']}: {base['determination']} {base['grade_summary']}")
    print(f"arm      {arm['run_id']}: {arm['determination']} {arm['grade_summary']}")
    flips = []
    for cid, cb in base["criteria"].items():
        ca = arm["criteria"].get(cid, {})
        print(f"\n[{cid}] {cb.get('label')}: {cb.get('status')} -> {ca.get('status')}")
        ra = {(r.get("key"), r.get("year")): r for r in ca.get("records", [])}
        for rb in cb.get("records", []):
            k = (rb.get("key"), rb.get("year"))
            r2 = ra.get(k, {})
            if rb.get("status") == "SKIPPED" and r2.get("status") == "SKIPPED":
                continue
            mark = ""
            if rb.get("status") != r2.get("status"):
                mark = "  <-- STATUS CHANGE"
                if cid in REJECT_ON and rb.get("status") == "PASS" and r2.get("status") == "FAIL":
                    mark = "  <-- PASS->FAIL on a rejection criterion"
                    flips.append((cid, k))
            print(
                f"   {k[1]} {k[0] or '':>12} | {rb.get('status'):7} {str(rb.get('magnitude'))[:60]:60} "
                f"| {str(r2.get('status')):7} {str(r2.get('magnitude'))[:60]}{mark}"
            )
    print("\nREJECTION-RULE FLIPS:", flips or "none")
    print("VERDICT:", "REJECTED PROBE" if flips else "KEEPER CANDIDATE (report every regression at full magnitude)")


if __name__ == "__main__":
    main()
