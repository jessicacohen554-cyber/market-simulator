# FINDING — capx D105: NEISO T1-F re-solve on keeper `2026-10-02-w0-neiso` (gate (d), one instrument)

**Lane** capx D105 (forecast solve shard) · **date** 2026-10-03 · **one LP** (five NEISO years, one invocation) ·
DATA PROFILE: `neiso` · **source** `origin/main` `828c54b6560b61aedc3eeebc929f9a214f808090` (the charter's pin
`07f5b88e` was three zero-LP merges behind: PRs #7115/#7116/#7117 — docs, backcast status parts, backcast
`calibration_verdict.py`, probes; none on the forecast path) · **PRECOMMIT** `PRECOMMIT-capx-d105-2026-10-03.md`
(commit `246438aa`, pushed before the LP) · **authority** owner ruling Q76 (capx ledger §0bn.2a rung 3; plan §2.1b
gate (d) for T1-F NEISO 2026–2030 only).

**Headline.** The headline `neiso-t1f` recipe re-solved on the W0 keeper resolves to cache key
**`66fb439918cbefd6`** — pre-declared and matched. **PROMOTE → PROMOTE**, 0 reasons, 0 caveats, every FC status
unchanged; all 14 invariants PASS. The key move from D50's `18515067bf4d2fbe` is exactly the two owner-ruled CCS
default moves (Q47) plus the nine moved NEISO solve-surface rows; nothing keeper-driven enters through a config
field. **Against interest:** the *trajectory* moved far more than the verdict — 2028–2030 CO2 falls 41–69 %
and the 2030 max hourly price falls from 283 to 84 $/MWh, because the re-identified CCS VOM adder
(8.0 → 2.95 $/MWh) moves the converted `gas_cc_ccs` fleet ahead of unabated CC in the merit order (§3).

## 1. Wall / RSS vs the §2.4 anchor (~85 s median/yr; D50 6.7 min)

| year | wall s | peak RSS MB | | year | wall s | peak RSS MB |
|---|---:|---:|---|---|---:|---:|
| 2026 | 167.1 | 3,214 | | 2029 | 128.2 | 2,678 |
| 2027 | 122.6 | 2,427 | | 2030 | 142.7 | 2,873 |
| 2028 | 122.7 | 2,669 | | **total** | **683.5 (11.4 min)** | **3,214** |

Median 128 s/yr — 1.5× the §2.4 anchor, 1.7× D50 (69–117 s/yr), inside the 45-min T1-F budget. Shard clock: clean
build 58 min (57 datatypes ok), solve started minute 59 (< 80) and ended minute 71; scoring/registration zero-LP.

## 2. The resolved key and what moved it (PRECOMMIT §2–3, all HIT)

| step | key | content |
|---|---|---|
| D50 recorded | `18515067bf4d2fbe` | reproduced by `head_key(D50 payload)` under the live drop rules |
| + Q47 CCS moves (`ccs_retrofit_vom_adder` 8.0→2.95; `ccs_retrofit_fixed_cost_co2_scaling` →True) | `c3519b861f920bbe` | = `head_key(new payload, surface=False)` exactly; 166 added fields are schema growth at drop value, 2 retired (`nyiso_firm_imports`, `retiree_cems_cap`) |
| + 9 moved surface rows (fp `b514541af339c180`, epochs `[]`) | **`66fb439918cbefd6`** | = the solved `run_config.json` / `solve_surface.json`; `git.sha 246438aa`, `dirty false`, 949 fields, `mode=forecast`, `outage_source=statistical` |

The D102 movers `CC_STEAM_PART_REPAIR_ISOS` and `STORAGE_BASE_FLEET_MW` are two of the nine rows.

## 3. FC-1..FC-8 before (`neiso-t1f-pre-d105`, D50 `9e48ff6`) vs after (`neiso-t1f`, this run)

| row | before | after | pre-declared? |
|---|---|---|---|
| FC-1 invariants | PASS (14) | PASS (14; I12 band [2.9 %, 17.9 %] all in-band) | expected |
| FC-2 row1 / row3 | PASS / PASS | PASS / PASS | expected |
| FC-2 row4 backstop share | PASS 1.2 % | PASS **0.0 %** | expected to move, ≤ 10 % — HIT |
| FC-3/FC-4 n/a; FC-5/FC-6 | SKIPPED | SKIPPED | expected |
| FC-7 run_config | PASS 784 keys | PASS **949 keys** | expected (exact) |
| FC-7 dof ledger | PASS 8 entries | PASS **7 entries, 0 UNIDENTIFIED** | expected (exact; `ccs_retrofit_capex_co2_scaling` is now the shipped default) |
| FC-8 runtime | PASS 6.7 min | PASS **11.4 min** | expected band [6, 12] — HIT, high side |
| rubric version | 1.0 | 1.1 | **UNEXPECTED (not pre-declared)** — the scorer's live rubric stamp; no row changed kind |
| **determination** | **PROMOTE** | **PROMOTE** | expected |

**Trajectory, D50 → D105 (read off the two committed `full_horizon_summary.json`; the verdict does not score it):**

| year | RM | LW price $/MWh | CO2 Mt | `gas_cc_ccs` TWh | `gas_cc` TWh | import TWh | max price |
|---|---|---|---|---|---|---|---|
| 2026 | 0.155→0.168 | 52.1→51.7 | 16.3→16.0 | — | 40.4→39.6 | 28.5→28.1 | 70→66 |
| 2027 | 0.046→0.048 | 53.3→51.2 | 17.6→17.2 | — | 40.3→39.9 | 28.3→26.9 | 280→237 |
| 2028 | 0.032→0.040 | 58.1→52.2 | 16.8→**9.9** | 2.4→**22.4** | 36.6→17.6 | 30.5→28.2 | 284→240 |
| 2029 | 0.033→0.044 | 62.5→51.5 | 15.4→**4.7** | 10.6→**36.6** | 24.1→4.2 | 32.4→26.1 | 285→241 |
| 2030 | 0.066→0.084 | 69.7→53.7 | 15.0→**6.0** | 19.2→26.2 | 14.5→8.7 | 33.0→29.1 | 283→**84** |

The converted CCS fleet is nearly the same size (ledger `ccs_retrofits`: 2028 2,982→2,976 MW, 2029 2,997→2,948,
2030 2,983→2,302; the 3 GW/yr cap still binds in 2028–2029), so the CO2 move is **dispatch**, not conversion:
at a 2.95 $/MWh adder the converted units displace unabated CC and imports. The W0 keeper's surface rows
show in the 2027 pre-retrofit fleet (`gas_cc` 10,714→10,327 MW, `gas_ct` 1,328→1,658, `oil` 5,084→4,754 —
class re-assignment under `PLANT_CLASSES` / `CC_STEAM_PART_REPAIR_ISOS`). Which of the two drivers owns which
share is a controlled-swap question this one-instrument charter does not answer; recorded, not attributed.

## 4. Registration

* `frontend/data/forecast/ff-verdicts.json`: prior `neiso-t1f` preserved byte-equal at **`neiso-t1f-pre-d105`**;
  new condensed verdict at `neiso-t1f`, `provenance` = {`scored_at_sha 246438aa743a`, `cache_epoch 66fb439918cbefd6`,
  `solve_surface` (fp, 9 moved rows), `run_id neiso-2026-2030-d105-w0neiso`, `session capx-D105`}. Writer reproduces
  the committed formatting (`indent=1`, `ensure_ascii`, trailing newline), round-trip verified.
* `register_forecast_run.py --summary … --kind t1f --label d105-w0neiso --extra-meta {verdict_key: neiso-t1f, …}`
  → sidecar `frontend/data/hindcast/neiso-2026-2030-d105-w0neiso.json`; namespace regenerated (192 runs; the
  generated registry/runs/manifest/program-status.js are gitignored). `program-status.json` untouched by hand
  and unchanged by the script.
* Bundle on `main` (this PR): `results/ff-t1f-d105/neiso/{run_config,full_horizon_summary,forecast_verdict,
  dof_ledger,invariants}.json`, `invariants.txt`, `NEISO/66fb439918cbefd6/{config.yaml,solve_surface.json,
  evolution_2026..2030.json}` — the ff-t1f-d50/d60 slim convention; `year_*.parquet`, floor-retention dumps and the
  log stay gitignored (`.gitignore` block, plain `git add`). A promotion costs nothing further: this *is* the
  headline key's registered record.

## 5. What this lane did NOT do

No `--set`, tuning, second recipe, other ISO or window; no edit under `src/`, `scripts/`, `CLAUDE.md`, keepers,
`calibration-complete.json`, `status/*.js`, `program-status.json` or a matrix shard (no mechanism tested). The D50 ↔ D105 trajectory move is **not attributed** between
the Q47 CCS re-pricing and the keeper's surface rows (one instrument, no control). **Leftover for the desk:**
`register_forecast_run.py::VERDICT_MAP["neiso-2026-2030-d50-ccscapex"]` still reads `neiso-t1f`, so the D50 run's
generated registry sidecar bakes the new verdict until it is re-pointed to `neiso-t1f-pre-d105` (a `scripts/`
edit outside this shard). Other `neiso-*` keys (t1h, t1x, t3) remain STALE-SURFACE per D102.
