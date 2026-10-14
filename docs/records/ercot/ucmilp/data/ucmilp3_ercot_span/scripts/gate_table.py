"""Per-year gate table: control | uc-1.4 | uc-1.5. Usage: gate_table.py control.json arm14.json [arm15.json]"""
import json, sys
def rows(p):
    d = json.load(open(p)); out = {}
    for c, v in d["criteria"].items():
        for r in v.get("records") or []:
            out[(c, str(r.get("key")), r.get("year"))] = r
    return out
src = [rows(p) for p in sys.argv[1:]]
ab = {"PASS": "P", "FAIL": "F", "CAVEAT": "C", "SKIPPED": "S", "UNATTESTED": "U"}
def cell(r):
    if r is None: return "—"
    m = str(r.get("magnitude", "")).split(" (")[0].split(", share")[0].replace("NRMSE ", "").replace(" forced", "").replace("C1 flags: ", "")
    if r.get("criterion") == "price_tail" or "model " in m:
        m = m.replace("model ", "").split(" [")[0]
    return f"{m} {ab.get(r['status'], r['status'])}"
spec = [("C1 CC", "fuelmix", "CC_REGULAR"), ("C1 PRB", "fuelmix", "COAL_PRB"), ("C1 LIG", "fuelmix", "COAL_LIGNITE"), ("C1 ST", "fuelmix", "ST_GAS"),
        ("C2 gas", "sysvol", "gas"), ("C2 coal", "sysvol", "coal"), ("C3a", "price_mean", "None"), ("C3b", "price_shape", "None"),
        ("C3c", "price_tail", "None"), ("C4 gas", "dispatch_corr", "gas"), ("C4 coal", "dispatch_corr", "coal"), ("C8 ST", "forced_share", "ST_GAS"), ("C8 CC", "forced_share", "CC_REGULAR")]
for y in range(2019, 2026):
    print(f"\n**{y}** | control | " + " | ".join(["uc-1.4", "uc-1.5"][: len(src) - 1]))
    print("|---|" + "---|" * len(src))
    for lab, c, k in spec:
        print(f"| {lab} | " + " | ".join(cell(s.get((c, k, y))) for s in src) + " |")
