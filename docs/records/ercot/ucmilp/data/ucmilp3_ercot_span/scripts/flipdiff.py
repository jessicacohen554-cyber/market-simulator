"""PASS->FAIL flips (PRECOMMIT §3) between two calibration_verdict --json outputs.

Usage: flipdiff.py control.json arm.json [years...]
"""

import json
import sys


def rows(path):
    d = json.load(open(path))
    out = {}
    for cname, c in d["criteria"].items():
        for r in c.get("records") or []:
            out[(cname, str(r.get("key")), r.get("year"))] = r
    return out


ctl, arm = rows(sys.argv[1]), rows(sys.argv[2])
years = {int(y) for y in sys.argv[3:]} or None
flips, moves = [], []
for k, a in sorted(arm.items(), key=lambda kv: str(kv[0])):
    if years and k[2] not in years:
        continue
    c = ctl.get(k)
    if c is None:
        continue
    if c["status"] != a["status"]:
        moves.append(
            (k, c["status"], a["status"], c.get("magnitude"), a.get("magnitude"))
        )
        if c["status"] == "PASS" and a["status"] == "FAIL":
            flips.append(k)
print(f"status changes: {len(moves)}")
for m in moves:
    print("  ", m)
print(f"PASS->FAIL flips: {len(flips)}")
for f in flips:
    print("  FLIP", f)
