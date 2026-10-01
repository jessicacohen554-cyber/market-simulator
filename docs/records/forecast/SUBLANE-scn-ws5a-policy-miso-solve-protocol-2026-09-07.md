# SUBLANE — SCN-WS5A-POLICY-MISO solve protocol (ruling S16)

**Parent** SCN-WS5A-POLICY-MISO · **PRECOMMIT**
`docs/handoffs/PRECOMMIT-scn-ws5a-policy-miso-2026-09-07.md` (the case set, keys, kills and
gates; a shard makes no decisions) · **THE PIN**
`bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Campaign** `scn-campaign-policy-2026-09-06`,
kind `scenario`, `reference_case: REF` · **Model** Opus `claude-opus-5` · **Data profile**
`miso`.

A shard **solves → registers → declares → reports**. It writes **no docs**, **scores no gates**
and **draws no conclusions**. Generalised from
`SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md`.

## 1. The groups

| shard | cases (in order) | key | label | run id |
|---|---|---|---|---|
| **G1** | `CARB-LO` | `1c815555d55e5db2` | `scn-campaign-policy-2026-09-06-carb-lo` | `miso-2026-2030-scn-campaign-policy-2026-09-06-carb-lo` |
| | `CARB-MID` | `27fb6e72c0ad31ae` | `…-carb-mid` | `miso-2026-2030-…-carb-mid` |
| **G2** | `CARB-HI` | `40bc61fac2b5271d` | `…-carb-hi` | `miso-2026-2030-…-carb-hi` |
| | `CARB-MID+LOAD-HI` | `e644893331d7708f` | `…-carb-mid-load-hi` | `miso-2026-2030-…-carb-mid-load-hi` |
| **G3** | `CES-P10` | `e4ba286178e0d499` | `…-ces-p10` | `miso-2026-2030-…-ces-p10` |
| | `CES-P20` | `472af7fd5ba90f99` | `…-ces-p20` | `miso-2026-2030-…-ces-p20` |
| **G4** | `CES-P30` | `3a4b528c75d7fd6d` | `…-ces-p30` | `miso-2026-2030-…-ces-p30` |
| | `CES-T80` | `82c916d847270ebf` | `…-ces-t80` | `miso-2026-2030-…-ces-t80` |
| **G5** | `VOL-MID` | `dc8ca3580e277d72` | `…-vol-mid` | `miso-2026-2030-…-vol-mid` |
| | `VOL-HI` | `7e1a2a2145711bab` | `…-vol-hi` | `miso-2026-2030-…-vol-hi` |
| **G6** | `CES-P20+VOL-HI` | `ed42e5d7d1d95d3e` | `…-ces-p20-vol-hi` | `miso-2026-2030-…-ces-p20-vol-hi` |
| | `ALL-CLEAN` | `00edacf5f50c88fc` | `…-all-clean` | `miso-2026-2030-…-all-clean` |
| **G7** | `CES-P60` *(via `--set`)* | `e5fb002f78c0c681` | `…-ces-p60` | `miso-2026-2030-…-ces-p60` |

`…` = `scn-campaign-policy-2026-09-06`. **NEVER** solve `REF`, `LOAD-HI`, `LOAD-HI-ORGANIC` or
`CAP-STATE-TIGHT` — the first two are committed legs at THE PIN and the last is proven
LP-identical to REF on MISO (PRECOMMIT §4.2).

## 2. Setup, at THE PIN

```
H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
git fetch origin main && git checkout --detach $H0
python3 scripts/hydrate_data.py --profile miso
uv sync
PYTHONPATH=. uv run python scripts/regenerate_clean.py     # derived + gitignored; ~40 min
```

`data/clean` is DERIVED and gitignored, so a fresh container has none and `run_scenario_iso`
hard-fails on MISO's `confirmed-retirements` clean partition. Start it first.

**Pre-solve checks — all must hold or STOP and report:**

- `git rev-parse HEAD` = `$H0`, and `git status --porcelain` empty;
- `results/MISO/<key>` does **not** exist for any key in your group — a pre-existing key
  directory is a **CACHE HIT and a STOP**, never a shortcut;
- re-resolve each key at the pin (§6 `rekey.py`) and assert it equals the table above. A moved
  key means the pin or the resolve chain changed under you: **STOP**.

## 3. Solve — one leg at a time, years sequential

**MISO peaks at ~9.98 GB on a 15 GB box. One solve at a time in this container; never two.**

```
for CASE in <your cases>; do
  [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
  MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
    uv run python scripts/run_ces_leg.py \
      --config configs/scenarios/miso_scenario_base_2026_2030.yaml \
      --matrix configs/scenario_campaign_matrix.yaml \
      --case "$CASE" --campaign scn-campaign-policy-2026-09-06 \
      --out-dir "results/scn-campaign-policy-2026-09-06/MISO/$CASE" \
      > "$SCRATCH/$CASE.log" 2>&1 || { echo "SOLVE FAILED $CASE"; exit 91; }
done
```

**G7 ONLY — `CES-P60` has no YAML case and is expressed through the registered `--set`
channel** (rule 24 `[R-REGISTRY]`; PRECOMMIT §2). Its invocation is:

```
[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_ces_leg.py \
    --config configs/scenarios/miso_scenario_base_2026_2030.yaml \
    --matrix configs/scenario_campaign_matrix.yaml \
    --case CES-P30 --set federal_ces_premium_usd_per_mwh=60.0 \
    --campaign scn-campaign-policy-2026-09-06 \
    --out-dir "results/scn-campaign-policy-2026-09-06/MISO/CES-P60" \
    > "$SCRATCH/CES-P60.log" 2>&1 || { echo "SOLVE FAILED CES-P60"; exit 91; }
```

Its summary records `case: "CES-P30"` with `set_overrides {"federal_ces_premium_usd_per_mwh":
60.0}` — expected, disclosed in the PRECOMMIT, and the reason **G7 SKIPS §5's assemble/report**
(the `members[case] = key` map would collide with the real `CES-P30` leg). Assert the resolved
key is `e5fb002f78c0c681` before and after.

Then, every shard, per case:

```
for CASE in <your cases>; do uv run python "$SCRATCH/extract_duals.py" MISO "results/scn-campaign-policy-2026-09-06/MISO/$CASE"; done
```

## 4. G1 only — the FC-6 paired premise on REF / CARB-MID

REF's cache is not in your container (it is a committed leg of another campaign), so only the
committed-config half runs here; the parent scores it. Run at THE PIN, before §6, and commit
the JSON with the `CARB-MID` leg:

```
uv run python scripts/check_forecast_invariants.py \
  --paired-run-configs results/scn-campaign-load-2026-09-06-r2/MISO/REF/run_config.json \
                       results/scn-campaign-policy-2026-09-06/MISO/CARB-MID/run_config.json \
  --pair-kind carbon --json > results/scn-campaign-policy-2026-09-06/MISO/CARB-MID/fc6_paired_premise.json
```

## 5. Group bundle + delta report (cache reads only, zero LP) — **G1–G6 only**

`--reference-case` is the FIRST case of your group; the parent differences against REF from the
committed absolutes, and what it needs from you is every case's ABSOLUTE columns, which this
report carries whatever the reference is.

```
G=<G1|G2|G3|G4|G5|G6>; FIRST=<first case of your group>
uv run python scripts/run_ces_leg.py --config configs/scenarios/miso_scenario_base_2026_2030.yaml \
  --matrix configs/scenario_campaign_matrix.yaml --assemble \
  --legs-dir results/scn-campaign-policy-2026-09-06/MISO \
  --out-dir "results/scn-campaign-policy-2026-09-06/MISO/bundle/$G"
uv run python scripts/report_scenario_deltas.py \
  --matrix-dir "results/scn-campaign-policy-2026-09-06/MISO/bundle/$G" \
  --reference-case "$FIRST" \
  --output-dir "results/scn-campaign-policy-2026-09-06/MISO/report/$G"
```

## 6. Register + declare — on your branch from `origin/main`, one commit per case

```
git fetch origin main
git checkout -B claude/scn-ws5a-policy-miso-solve-<g>-<4ch> origin/main   # untracked results/ survive
uv sync
```

Per case, in group order:

```
CASE=<case>; LABEL=<label from §1>; ID="miso-2026-2030-$LABEL"
uv run python scripts/register_forecast_run.py \
  --summary "results/scn-campaign-policy-2026-09-06/MISO/$CASE/full_horizon_summary.json" \
  --label "$LABEL" --kind scenario --extra-meta '{"reference_case": "REF"}'
python3 "$SCRATCH/declare_fail.py" "$ID"
uv run python scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast   # MUST exit 0
git add "results/scn-campaign-policy-2026-09-06/MISO/$CASE" "frontend/data/hindcast/$ID.json" frontend/data/hindcast/invariant-failures.json
git commit -m "SCN-WS5A-POLICY-MISO leg $CASE: solved at THE PIN, registered $ID, FAILs declared"
```

`git status` must show nothing else staged — the generated `frontend/data/forecast/` namespace
is gitignored and stays so. Then the group commit (G1–G6):

```
git add "results/scn-campaign-policy-2026-09-06/MISO/bundle/$G" "results/scn-campaign-policy-2026-09-06/MISO/report/$G"
git commit -m "SCN-WS5A-POLICY-MISO $G: bundle + absolute delta tables for <cases>"
git push -u origin <branch>
```

Push retries: on HTTP 408/500 set `git config http.version HTTP/1.1` and retry **before**
concluding anything about pack size; on rejection because `main` moved,
`git fetch origin main && git rebase origin/main`. **If `invariant-failures.json` conflicts**
(sibling shards insert into the same block): take main's version
(`git show origin/main:frontend/data/hindcast/invariant-failures.json > frontend/data/hindcast/invariant-failures.json`),
re-run `declare_fail.py` for every id you have already committed, `git add`,
`git rebase --continue`, then re-run the checker. After the push, verify by fetch-back that
`origin/<branch>:frontend/data/hindcast/invariant-failures.json` hashes identical to your local
copy. Do **not** open a PR unless the owner asks.

## 7. The two helper scripts — write them to `$SCRATCH` verbatim

`$SCRATCH/rekey.py` (§2 pre-solve check; run at THE PIN as
`uv run python "$SCRATCH/rekey.py" CASE1 CASE2 …`; pass `CES-P60` to check the `--set` leg):

```python
import subprocess, sys
from pathlib import Path
sys.path.insert(0, ".")
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition, resolve_policy_bundle
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.config.topology_variant import set_caiso_fsno_partition
from market_sim.matrix import matrix_configs
from scripts.run_full_horizon import apply_set_overrides
EXPECTED = {"CARB-LO": "1c815555d55e5db2", "CARB-MID": "27fb6e72c0ad31ae", "CARB-HI": "40bc61fac2b5271d",
 "CES-P10": "e4ba286178e0d499", "CES-P20": "472af7fd5ba90f99", "CES-P30": "3a4b528c75d7fd6d",
 "CES-T80": "82c916d847270ebf", "CARB-MID+LOAD-HI": "e644893331d7708f", "VOL-MID": "dc8ca3580e277d72",
 "VOL-HI": "7e1a2a2145711bab", "CES-P20+VOL-HI": "ed42e5d7d1d95d3e", "ALL-CLEAN": "00edacf5f50c88fc",
 "CES-P60": "e5fb002f78c0c681"}
print("HEAD", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
base = ScenarioConfig.from_yaml(Path("configs/scenarios/miso_scenario_base_2026_2030.yaml"))
configs = matrix_configs(base, SweepDefinition.from_yaml(Path("configs/scenario_campaign_matrix.yaml")))
ok = True
for case in sys.argv[1:]:
    src = configs["CES-P30"] if case == "CES-P60" else configs[case]
    if case == "CES-P60":
        src = apply_set_overrides(src, {"federal_ces_premium_usd_per_mwh": 60.0})
    cfg = resolve_policy_bundle(src)
    set_caiso_fsno_partition(False)
    cfg = apply_iso_scenario_defaults(cfg, "MISO")
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
    rps = getattr(r, "rps_region_duals", None)
    rec["years"][str(y)] = {
        "clean_region_duals": None if d is None else [float(x) for x in d],
        "rps_region_duals": None if rps is None else [float(x) for x in rps],
        "objective_value": None if getattr(r, "objective_value", None) is None else float(r.objective_value),
    }
(out / "duals.json").write_text(json.dumps(rec, indent=1) + "\n")
print(json.dumps(rec, indent=1))
```

`$SCRATCH/declare_fail.py` — copy verbatim from
`SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md` §6 (textual insert into the
`declared_failures` block, sorted, idempotent; run as
`python3 "$SCRATCH/declare_fail.py" <run id>` from the repo root).

## 8. Your final chat message

One table, one row per case: case · resolved key · `git.sha` · `git.dirty` · per-year `wall_s` /
`peak_rss_mb` (2026…2030) · invariant FAIL set · run id · headline `co2_mt` / `lw_price` /
`clean_share` per year · whether `gas_cc_ccs` appears in each year. Then the commit shas pushed,
the branch, and any STOP or anomaly **verbatim**. **No interpretation** — the gates, the deltas
vs REF and the FINDING are the parent lane's.

## 9. Never

Solve `REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` / `CAP-STATE-TIGHT`, any case outside your group, or
any year past 2030. Edit `src/`, `configs/`, `scripts/`, `.github/`, the PRECOMMIT, the
mechanism matrix, the readiness plan or the desk ledger. Create a CI workflow, move a default,
add a `ScenarioConfig` field, re-run phase 0, or parallelise years within a leg.
