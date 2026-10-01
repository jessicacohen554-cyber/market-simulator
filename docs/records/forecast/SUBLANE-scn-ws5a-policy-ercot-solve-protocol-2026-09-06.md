# SUBLANE PROTOCOL — SCN-WS5A-POLICY-ERCOT parallel solve sessions (2026-09-06)

**Who runs this:** a sub-lane session launched by the owner to solve ONE GROUP of the eleven
ERCOT Stage A-POLICY legs. You are a SOLVER for lane SCN-WS5A-POLICY-ERCOT, not a new lane:
the phase 0, the case set, the keys, the kills and the gates are all committed in
`docs/handoffs/PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md` (+ its ADDENDUM A), and the
FINDING, the gate scoring, the plan/ledger rows and the matrix cells are the parent lane's.
**MODEL:** Opus (`claude-opus-5`) or Fable. **DATA PROFILE:** `ercot`.
**Branch:** `claude/scn-ws5a-policy-ercot-solve-g<N>-<4 random chars>`.

Why this exists: owner instruction 2026-09-06 (ADDENDUM A(d)) — the legs run in parallel
owner-launched sessions, each its own container, each ≤ 1 ERCOT solve at a time, years
sequential inside every leg (CLAUDE.md rule 12's within-invocation half is untouched).

## 0. Your group

| group | cases (solve in this order) | extra duty |
|---|---|---|
| G1 | `CARB-LO`, `CARB-MID`, `CARB-HI` | FC-6 paired premise on REF/CARB-MID (§5) |
| G2 | `CES-P10`, `CES-P20`, `CES-P30` | — |
| G3 | `CES-T80`, `CARB-MID+LOAD-HI`, `VOL-HI` | — |
| G4 | `CES-P20+VOL-HI`, `ALL-CLEAN` | — |

Run ids and labels (label = case lower-cased, `+` → `-plus-`; run id =
`ercot-2026-2030-<label>`):

| case | key at THE PIN (PRECOMMIT §2 / ADDENDUM A(a)) | `--label` |
|---|---|---|
| CARB-LO | `c1e09985c3e4fa56` | `scn-campaign-policy-2026-09-06-carb-lo` |
| CARB-MID | `ab8d79646b49abbd` | `scn-campaign-policy-2026-09-06-carb-mid` |
| CARB-HI | `73dadcb65d74acce` | `scn-campaign-policy-2026-09-06-carb-hi` |
| CES-P10 | `17e0b252e13a484a` | `scn-campaign-policy-2026-09-06-ces-p10` |
| CES-P20 | `5a89c34af859160c` | `scn-campaign-policy-2026-09-06-ces-p20` |
| CES-P30 | `8588e1b0d055e772` | `scn-campaign-policy-2026-09-06-ces-p30` |
| CES-T80 | `e6638b058ce4d5fb` | `scn-campaign-policy-2026-09-06-ces-t80` |
| CARB-MID+LOAD-HI | `b99311bb1f3032e0` | `scn-campaign-policy-2026-09-06-carb-mid-plus-load-hi` |
| VOL-HI | `76ef5a80df6a9277` | `scn-campaign-policy-2026-09-06-vol-hi` |
| CES-P20+VOL-HI | `5b7774c817ee425b` | `scn-campaign-policy-2026-09-06-ces-p20-plus-vol-hi` |
| ALL-CLEAN | `619cfffde44422b2` | `scn-campaign-policy-2026-09-06-all-clean` |

**NEVER solve** `REF`, `LOAD-HI`, `LOAD-HI-ORGANIC`, `VOL-MID`, `CAP-STATE-TIGHT`, any case not
in your group, or any year past 2030. **NEVER edit** anything under `src/`, `configs/`,
`scripts/`, `.github/`, the PRECOMMIT, the matrix shards, the plan or the desk ledger. **NEVER**
create a CI workflow, move a default, or add a `ScenarioConfig` field. You write ONLY:
`results/scn-campaign-policy-2026-09-06/ERCOT/<CASE>/`, `results/scn-campaign-policy-2026-09-06/ERCOT/{bundle,report}/<GROUP>/`,
`frontend/data/hindcast/<run id>.json`, and lines in `frontend/data/hindcast/invariant-failures.json`.
No docs. Your report is your final chat message (§7).

## 1. Setup — at THE PIN, before anything else

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
git fetch origin main
git checkout --detach $H0
python3 scripts/hydrate_data.py --profile ercot
uv sync
PYTHONPATH=. uv run python scripts/regenerate_clean.py      # data/clean is derived + gitignored; a fresh container has none
mkdir -p "$SCRATCH"   # your session scratchpad dir; every log goes there, never into results/
```

Pre-solve checks (all must hold, else STOP and report — do not improvise):
- `[ "$(git rev-parse HEAD)" = "$H0" ]` and `git status --porcelain` is empty.
- `ls results/ERCOT/<key>` does NOT exist for any key in your group (fresh cache; a pre-existing
  dir would be a cache hit, which is a STOP).
- Re-resolve your keys (zero LP) with the script in §6 and assert each equals the table above.

## 2. Solve — one leg at a time, years sequential, HEAD GUARD around every leg

```
for CASE in <your cases in order>; do
  [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
  MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
    uv run python scripts/run_ces_leg.py \
      --config configs/scenarios/ercot_scenario_base_2026_2030.yaml \
      --matrix configs/scenario_campaign_matrix.yaml \
      --case "$CASE" --campaign scn-campaign-policy-2026-09-06 \
      --out-dir "results/scn-campaign-policy-2026-09-06/ERCOT/$CASE" \
      > "$SCRATCH/$CASE.log" 2>&1 || { echo "SOLVE FAILED $CASE"; exit 91; }
done
```

Expect ~6.5–7 min per leg, peak RSS ~4.2 GB. Never run two legs concurrently.

Post-solve proof per leg (RESOLVE PRECOMMIT §4.2 form): in `<out-dir>/run_config.json`
`cache_key` == the table key, `git.sha` == `$H0`, `git.dirty` == false; in
`full_horizon_summary.json` `n_solved_years` == 5, `per_year_perf` has 5 rows with `wall_s` of
solve order (10²–10³ s), `error` null. A mismatch is a STOP: report it, register nothing.

## 3. Still at THE PIN — duals, FC-6 premise, bundle + report for your group

Duals (the CES-target / voluntary rows persist `clean_region_duals` in each year's cache meta;
region order state → federal → voluntary; ERCOT has no state program): run the §6
`extract_duals.py` for EVERY case in your group (carbon/premium cases record `null`, which is
itself the "no row" evidence):

```
for CASE in <your cases>; do uv run python "$SCRATCH/extract_duals.py" ERCOT "results/scn-campaign-policy-2026-09-06/ERCOT/$CASE"; done
```

Bundle + delta report for your group (cache reads only, zero LP). `--reference-case` is the
FIRST case of your group — the parent lane differences against REF from the committed absolutes
(`results/scn-campaign-load-2026-09-06/ERCOT/report/*_bau` columns); what it needs from you is
every case's ABSOLUTE columns, which this report carries whatever the reference is:

```
G=<G1|G2|G3|G4>; FIRST=<first case of your group>
uv run python scripts/run_ces_leg.py --config configs/scenarios/ercot_scenario_base_2026_2030.yaml \
  --matrix configs/scenario_campaign_matrix.yaml --assemble \
  --legs-dir results/scn-campaign-policy-2026-09-06/ERCOT \
  --out-dir "results/scn-campaign-policy-2026-09-06/ERCOT/bundle/$G"
uv run python scripts/report_scenario_deltas.py \
  --matrix-dir "results/scn-campaign-policy-2026-09-06/ERCOT/bundle/$G" \
  --reference-case "$FIRST" \
  --output-dir "results/scn-campaign-policy-2026-09-06/ERCOT/report/$G"
```

## 4. Register + declare — on your branch from `origin/main`, one commit per case

```
git fetch origin main
git checkout -B claude/scn-ws5a-policy-ercot-solve-g<N>-<4ch> origin/main   # untracked results/ survive the switch
uv sync
```

Per case, in group order:

```
CASE=<case>; LABEL=<label from the table>; ID="ercot-2026-2030-$LABEL"
uv run python scripts/register_forecast_run.py \
  --summary "results/scn-campaign-policy-2026-09-06/ERCOT/$CASE/full_horizon_summary.json" \
  --label "$LABEL" --kind scenario --extra-meta '{"reference_case": "REF"}'
python3 "$SCRATCH/declare_fail.py" "$ID"          # §6; inserts the run's FAIL set, idempotent
uv run python scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast   # must exit 0
git add "results/scn-campaign-policy-2026-09-06/ERCOT/$CASE" "frontend/data/hindcast/$ID.json" frontend/data/hindcast/invariant-failures.json
git commit -m "SCN-WS5A-POLICY-ERCOT leg $CASE: solved at THE PIN, registered $ID, FAILs declared"
```

`git status` must show nothing else staged: the generated `frontend/data/forecast/` namespace is
gitignored and must stay so. Then the group commit:

```
git add "results/scn-campaign-policy-2026-09-06/ERCOT/bundle/$G" "results/scn-campaign-policy-2026-09-06/ERCOT/report/$G"
git commit -m "SCN-WS5A-POLICY-ERCOT $G: bundle + absolute delta tables for <cases>"
git push -u origin <branch>
```

Push retries: on HTTP 408/500 `git config http.version HTTP/1.1` and retry; on rejection because
`main` moved, `git fetch origin main && git rebase origin/main`. **If `invariant-failures.json`
conflicts** (sibling sub-lanes insert at the same block): take main's version
(`git show origin/main:frontend/data/hindcast/invariant-failures.json > frontend/data/hindcast/invariant-failures.json`),
re-run `declare_fail.py` for every id you have already committed, `git add` it,
`git rebase --continue`, then re-run the checker. After the push, verify by fetch-back that
`origin/<branch>:frontend/data/hindcast/invariant-failures.json` hashes identical to your local
copy (`git rev-parse origin/<branch>:frontend/data/hindcast/invariant-failures.json` vs
`git hash-object` of the file). Do NOT open a PR unless the owner asks; repository automation
merges pushed branches.

## 5. G1 only — the FC-6 paired premise on REF / CARB-MID

REF's cache is not in your container (it is a committed leg of another campaign), so only the
committed-config half of the paired battery runs here; the parent lane scores P1 from the two
summaries. Run at THE PIN, before §4, and commit the JSON with the CARB-MID leg:

```
uv run python scripts/check_forecast_invariants.py \
  --paired-run-configs results/scn-campaign-load-2026-09-06/ERCOT/REF/run_config.json \
                       results/scn-campaign-policy-2026-09-06/ERCOT/CARB-MID/run_config.json \
  --pair-kind carbon --json > results/scn-campaign-policy-2026-09-06/ERCOT/CARB-MID/fc6_paired_premise.json
```

## 6. The three helper scripts — write them to `$SCRATCH` verbatim

`$SCRATCH/rekey.py` (§1 pre-solve check; run at THE PIN as
`uv run python "$SCRATCH/rekey.py" CASE1 CASE2 ...`):

```python
import subprocess, sys
from pathlib import Path
sys.path.insert(0, ".")
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition, resolve_policy_bundle
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.config.topology_variant import set_caiso_fsno_partition
from market_sim.matrix import matrix_configs
EXPECTED = {"CARB-LO": "c1e09985c3e4fa56", "CARB-MID": "ab8d79646b49abbd", "CARB-HI": "73dadcb65d74acce",
 "CES-P10": "17e0b252e13a484a", "CES-P20": "5a89c34af859160c", "CES-P30": "8588e1b0d055e772",
 "CES-T80": "e6638b058ce4d5fb", "CARB-MID+LOAD-HI": "b99311bb1f3032e0", "VOL-HI": "76ef5a80df6a9277",
 "CES-P20+VOL-HI": "5b7774c817ee425b", "ALL-CLEAN": "619cfffde44422b2"}
print("HEAD", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
base = ScenarioConfig.from_yaml(Path("configs/scenarios/ercot_scenario_base_2026_2030.yaml"))
configs = matrix_configs(base, SweepDefinition.from_yaml(Path("configs/scenario_campaign_matrix.yaml")))
ok = True
for case in sys.argv[1:]:
    cfg = resolve_policy_bundle(configs[case])
    set_caiso_fsno_partition(False)
    cfg = apply_iso_scenario_defaults(cfg, "ERCOT")
    key = cfg.cache_key(); m = key == EXPECTED[case]; ok &= m
    print(f"{case:<18} {key} expected {EXPECTED[case]} {'MATCH' if m else 'MISMATCH'}")
print("ALL MATCH" if ok else "KEY MOVED - STOP"); sys.exit(0 if ok else 2)
```

`$SCRATCH/extract_duals.py`:

```python
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from market_sim.results.outputs import DispatchResult
iso, out = sys.argv[1], Path(sys.argv[2])
summ = json.loads((out / "full_horizon_summary.json").read_text())
key = summ["cache_key"]; cache = Path("results") / iso / key
rec = {"cache_key": key, "case": summ.get("case"), "years": {}}
for y in summ["solved_years"]:
    r = DispatchResult.from_parquet(cache / f"year_{y}.parquet")
    d = r.clean_region_duals
    rec["years"][str(y)] = {
        "clean_region_duals": None if d is None else [float(x) for x in d],
        "objective_value": None if getattr(r, "objective_value", None) is None else float(r.objective_value),
    }
(out / "duals.json").write_text(json.dumps(rec, indent=1) + "\n")
print(json.dumps(rec, indent=1))
```

`$SCRATCH/declare_fail.py` (textual insert into the `declared_failures` block, sorted, idempotent;
run as `python3 "$SCRATCH/declare_fail.py" <run id>` from the repo root):

```python
import json, re, sys
rid = sys.argv[1]
p = sys.argv[2] if len(sys.argv) > 2 else "frontend/data/hindcast/invariant-failures.json"
sd = sys.argv[3] if len(sys.argv) > 3 else "frontend/data/hindcast"
sc = json.load(open(f"{sd}/{rid}.json"))
fails = sorted(r["ident"] for r in sc["invariants"] if r["status"] == "FAIL")
lines = open(p).read().split("\n")
if any(l.startswith(f'  "{rid}":') for l in lines):
    print("already declared", rid); sys.exit(0)
if not fails:
    print("no FAIL to declare for", rid); sys.exit(0)
start = next(i for i, l in enumerate(lines) if l.strip() == '"declared_failures": {')
end = next(i for i in range(start + 1, len(lines)) if re.match(r"^ \},?$", lines[i]))
pat = re.compile(r'^  "([^"]+)": \[')
keys = [(i, pat.match(l).group(1)) for i, l in enumerate(lines[start + 1:end], start + 1) if pat.match(l)]
ins = next((i for i, k in keys if k > rid), None)
block = [f'  "{rid}": ['] + [f'   "{f}",' for f in fails[:-1]] + [f'   "{fails[-1]}"']
if ins is None:
    j = end - 1
    lines[j] = lines[j].rstrip(",") + ","
    lines[j + 1:j + 1] = block + ["  ]"]
else:
    lines[ins:ins] = block + ["  ],"]
open(p, "w").write("\n".join(lines))
json.load(open(p))
print("declared", rid, fails)
```

## 7. Your final chat message (the parent lane reads the committed files; this is the summary)

One table, one row per case: case · key · `git.sha` · `git.dirty` · per-year `wall_s` /
`peak_rss_mb` (2026…2030) · invariant FAIL set · run id · whether `gas_cc_ccs` appears in any
year's `generation_by_fuel_mwh` (expected: never on ERCOT). Then: the commit shas pushed, the
branch, and any STOP or anomaly verbatim. No interpretation of the results — the gates, the
deltas vs REF and the FINDING are the parent lane's.
