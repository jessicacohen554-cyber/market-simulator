"""SCN-WS1c STOP-gate scorer (PRECOMMIT section 4). Zero LP: compares the two
verify-floor snapshots against SCN-WS1a's COMMITTED phase-0 prediction."""
import json

BEFORE = json.load(open("docs/handoffs/scn-ws1c/verify-floor-before.json"))
AFTER = json.load(open("docs/handoffs/scn-ws1c/verify-floor-after.json"))
PRED = json.load(open("docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.json"))
ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
BUNDLES = ["current", "tight", "rollback"]
YEARS = [str(y) for y in range(2026, 2051)]
EXPECTED_MOVERS = {("CAISO", "tight"), ("NYISO", "tight"), ("NEISO", "tight")}

# ---- G1: after == committed `floor` column, cell by cell -------------------
g1_bad, n = [], 0
for iso in ISOS:
    for b in BUNDLES:
        for y in YEARS:
            n += 1
            got = AFTER["snapshot"]["trajectory"][iso][b][y]
            want = PRED[iso][b]["rows"][y]["floor"]
            if abs(got - want) > 0.005:
                g1_bad.append((iso, b, y, got, want))
print(f"G1 direction+magnitude : {n - len(g1_bad)}/{n} cells equal the committed `floor` "
      f"prediction  -> {'PASS' if not g1_bad else 'FAIL'}")
for row in g1_bad[:10]:
    print("   MISMATCH", row)

# ---- G2: footprint is exactly the three program-ISO tight series -----------
moved, unmoved, deltas = set(), 0, []
for iso in ISOS:
    for b in BUNDLES:
        for y in YEARS:
            a, bfr = AFTER["snapshot"]["trajectory"][iso][b][y], BEFORE["snapshot"]["trajectory"][iso][b][y]
            if abs(a - bfr) > 0.005:
                moved.add((iso, b))
                deltas.append((iso, b, y, round(a - bfr, 2)))
            else:
                unmoved += 1
g2 = moved == EXPECTED_MOVERS and len(deltas) == 75
print(f"G2 footprint           : moved series = {sorted(moved)}; moved cells = {len(deltas)}"
      f" (expect 3 series x 25 yr = 75); unmoved cells = {unmoved}/450  -> {'PASS' if g2 else 'FAIL'}")
print(f"   every delta strictly POSITIVE (no cell falls): "
      f"{all(d > 0 for *_, d in deltas)}  min +{min(d for *_,d in deltas):.2f} "
      f"max +{max(d for *_,d in deltas):.2f} $/tCO2")

# ---- the ruled no-op: tight == current on the three program ISOs -----------
print("   ruled no-op check (tight == current, all 25 yr, after the repair):")
for iso in ["CAISO", "NYISO", "NEISO"]:
    t = AFTER["snapshot"]["trajectory"][iso]
    eq = all(abs(t["tight"][y] - t["current"][y]) < 1e-9 for y in YEARS)
    print(f"     {iso:6s} tight == current in all 25 years: {eq}")
print("   strict increase where the path alone applies (tight > current, 2027-2050):")
for iso in ["ERCOT", "PJM", "MISO"]:
    t = AFTER["snapshot"]["trajectory"][iso]
    st = all(t["tight"][y] > t["current"][y] for y in YEARS[1:])
    print(f"     {iso:6s} tight >  current in 2027-2050: {st}  (2026 equal at 0.00: RFF mid knot)")

# ---- G3: byte identity ----------------------------------------------------
key_moves = {k: (v, AFTER["snapshot"]["cache_keys"][k])
             for k, v in BEFORE["snapshot"]["cache_keys"].items()
             if AFTER["snapshot"]["cache_keys"][k] != v}
dflt = BEFORE["snapshot"]["default_cache_key"] == AFTER["snapshot"]["default_cache_key"]
onbranch = AFTER["run_configs"]["on_changed_branch"]
bc_same = all(BEFORE["snapshot"]["trajectory"][i]["backcast"] == AFTER["snapshot"]["trajectory"][i]["backcast"]
              for i in ISOS)
g3 = not key_moves and dflt and not onbranch and bc_same
print(f"G3 byte identity       : cache keys moved = {len(key_moves)}/{len(BEFORE['snapshot']['cache_keys'])}; "
      f"default key {BEFORE['snapshot']['default_cache_key']} stable = {dflt}; "
      f"committed run_configs on the changed branch = {len(onbranch)}/{AFTER['run_configs']['n_files']}; "
      f"backcast 2023-25 trajectories identical in all six ISOs = {bc_same}  -> {'PASS' if g3 else 'FAIL'}")
if key_moves:
    print("   MOVED:", key_moves)

print()
print("VERDICT:", "ALL GATES PASS" if (not g1_bad and g2 and g3) else "STOP - a gate failed")
