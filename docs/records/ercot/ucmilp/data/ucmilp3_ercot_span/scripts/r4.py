"""R4 (D-4 ruling) adjustment of C8: the D-2 forced share with MECH 28 (uc_schedule) removed.

Usage: r4.py <bundle>/legitimacy_diagnostics.json
Prints, per (year, class) summary row: scorer share, uc_schedule TWh, share without it, verdict both ways.
A C8 flip counts (PRECOMMIT §1 R4, §3) only if the class still fails with uc_schedule removed.
"""

import json
import sys

d2 = json.load(open(sys.argv[1]))["diagnostics"]["D2"]
uc = {}
for r in d2["rows"]:
    if r["mechanism"] == "uc_schedule":
        uc[(r["year"], r["class"])] = (
            uc.get((r["year"], r["class"]), 0.0) + r["forced_twh"]
        )
print("year class        scorer   uc_TWh  r4_share  limit  scorer_v  r4_v")
for s in d2["summary"]:
    k = (s["year"], s["class"])
    u = uc.get(k, 0.0)
    tot = s["class_total_twh"] or float("nan")
    r4 = (s["forced_twh"] - u) / tot
    r4v = "pass" if s["immaterial"] or r4 <= s["limit"] else "FAIL"
    print(
        f"{s['year']} {s['class']:<12} {s['forced_share']:6.1%}  {u:6.2f}  {r4:7.1%}  {s['limit']:.0%}   {s['verdict']:<8}  {r4v}"
    )
