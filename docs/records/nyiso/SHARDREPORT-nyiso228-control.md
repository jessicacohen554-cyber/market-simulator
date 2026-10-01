# SHARD REPORT — nyiso-228 arm **C (CONTROL)**

**Session:** nyiso-228 · **Shard:** C (CONTROL) · **ISO:** NYISO · **Date:** 2026-09-12
**Branch:** `claude/nyiso228-control-span` · **Bundle:** `results/calibration/nyiso228_control_span`
**Charter:** `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` §3 arm C, §6 shard table.

## STATUS: **1** — solved (exit 0, all four years), committed and pushed.

**Headline: the G-DRIFT audit of PRECOMMIT §2 is CONFIRMED, and arm C is a valid control.**
Every one of nyiso-227's post-re-basing arm-side numbers reproduces here **exactly** — C3a to four
decimals in all three overlapping years, D-2 `reliability_floor × ST_GAS` to four decimals, C8
ST_GAS forced share to four decimals, and the D-4 plant-2480 failure byte-for-byte. The session's
comparisons may stand on arm C.

---

## 1. HARD STOPS — all three PASS, with observed values

| # | stop | required | observed | verdict |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD` at session start | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | **PASS** |
| 2 | PRECOMMIT + `nyiso228_peak_x150.json` exist | both | `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` 21,997 B · `results/calibration/nyiso228_peak_x150.json` 339 B | **PASS** |
| 3 | config signature in the **written** `run_config.json` | see table | see table | **PASS** |

No rebase, no `git pull`, no sync at any point.

### 1.1 Hard stop 3, verified against the bundle's own written `run_config.json`

| field | required | observed | verdict |
|---|---|---|---|
| `nyiso_hub_gap_month_level` | `false` | `False` | **PASS** |
| `nyiso_import_reconciliation` | `true` | `True` | **PASS** |
| `offer_curve_by_group["CT_PEAKER"]["peak"]` | `4.0` | `4.0` | **PASS** |
| `offer_curve_by_group["ST_GAS"]["peak"]` | `4.2` | `4.2` | **PASS** |

The base `nyiso223_gapfill_span` carries `nyiso_hub_gap_month_level=True`; the single `--set`
disarms it, and the other three fields were already at the required values. **Arm C moves no offer
band** — that is arm A's variable, and its absence here is what makes this the control.

### 1.2 Provenance of the solve's `git_sha`, stated explicitly

`meta.json` records `git_sha: d4f97391`, **not** the pinned sha, and that is correct rather than a
drift: `d4f97391` is this shard's own heartbeat commit, whose parent is exactly
`55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` and whose entire content is **one new docs file**
(`docs/SHARDREPORT-nyiso228-control.md`, +61 lines, nothing else). `git merge-base --is-ancestor`
confirms the pinned sha is an ancestor of HEAD. **The solve path is byte-identical to the pinned
sha.**

## 2. PREP LOG

| step | result |
|---|---|
| `hydrate_data.py --profile nyiso` | no-op — this container is a FULL clone, every blob already local |
| `prepare_solve_container.py` | 8 GiB swap at `/swapfile-marketsim`; RAM 15.7 + swap 8.0 = 23.7 GiB; 16.9 GiB free disk; 4 cpus |
| env pins | `MALLOC_ARENA_MAX=2` `MARKET_SIM_HIGHS_THREADS=1` `OMP_NUM_THREADS=1` in every solve shell |
| pip pins | PyYAML · highspy 1.14.0 · numpy 2.4.6 · scipy 1.17.1 · pandas 3.0.3 · pyarrow 24.0.0 · pydantic 2.13.4 · openpyxl · tzdata — all exit 0 |
| `pip install -e .` | run (parent steer) — `market_sim` now imports without `PYTHONPATH` games |
| `data/clean/` | gitignored, started EMPTY; rebuilt as described below |

`curate_lmp.py` was **not** run (charter: known pre-existing `KeyError: 'MGHG'` on a CAISO file,
repair out of scope). C3a/C3b percentages are the parent's to score.

### 2.1 Two prep findings the sibling shards will hit

**(a) `PYTHONPATH=.` is insufficient for most curate scripts — the repo is a `src/` layout.**
`scripts/data/curate_fleet.py` inserts both the repo root *and* `src` on `sys.path`, but
`curate_fuel_prices.py`, `curate_reference.py`, `scripts/lib/clean_io.py` and 17 others insert only
the repo root, so they die on `ModuleNotFoundError: No module named 'market_sim'`. **20 of 27
partitions failed this way on the first pass.** The fix is `pip install -e .` (or
`PYTHONPATH=<repo>:<repo>/src`). No file under `src/` or `scripts/` was edited.

**(b) The partition the NYISO solve actually hard-required was NOT on the charter's list:
`capacity-deliverability`.** The first launch died in 26 s — not a timeout, a real missing input:

```
ValueError: nyiso_li_lcr_tsl=True but no published Long Island transfer_security_limit for
delivery year 2022/2023 in the capacity-deliverability table
(data/raw/capacity-deliverability/nyiso/nyiso.csv); available areas: []
```

`python3 scripts/regenerate_clean.py capacity-deliverability` wrote NYISO (35 rows) and the relaunch
cleared. Per the parent's steer the speculative curation was stopped and no further partition was
rebuilt up front; everything else the solve needed came from the 17 partitions already on disk.

## 3. SOLVE — per year wall-clock and exit code

```
PYTHONPATH=. python3 scripts/replay_keeper.py results/calibration/nyiso223_gapfill_span \
  --set nyiso_hub_gap_month_level=false \
  --out-dir results/calibration/nyiso228_control_span \
  --years 2022 2023 2024 2025 \
  --note "nyiso-228 arm C CONTROL: keeper recipe at HEAD over 2022-2025; earned by the G-DRIFT LIVE hunk reliability_floor_coeffs_NYISO.csv (nyiso-227 NYC ST_GAS re-basing)"
```

Years sequential inside the one invocation (rule 12) — never parallelised.

| year | wall-clock | completed at (UTC) | exit |
|---|---|---|---|
| 2022 | **3 m 23 s** | 02:14:50 | 0 |
| 2023 | **3 m 30 s** | 02:18:20 | 0 |
| 2024 | **4 m 12 s** | 02:22:32 | 0 |
| 2025 | **3 m 52 s** | 02:26:24 | 0 |
| **invocation total** | **15 m 13 s** (LP 14 m 57 s + diagnostics) | 02:26:40 | **`SOLVE_EXIT=0`** |

Start 02:11:27 UTC. Per-year figures are from the per-year `class_hourly_<yr>.parquet` mtimes, each
written at the end of its own year's solve. **Inside the 20-minute shard budget (rule 32(b))**, with
no year approaching it; no subdivision was needed.

## 4. RESULTS

### 4.3 P1 load-weighted price, five load zones (`NYISO_external` excluded)

| year | mean (pooled LW = C3a basis) | mean (hourly-LW series) | p95 | p99 | max | h>$150 | h>$200 | h>$300 |
|---|---|---|---|---|---|---|---|---|
| 2022 | **69.9525** | 65.32 | 122.42 | 170.49 | 1429.99 | 197 | 30 | 8 |
| 2023 | **33.6760** | 32.38 | 48.15 | 63.30 | 213.86 | 8 | 1 | 0 |
| 2024 | **40.1782** | 38.66 | 60.67 | 116.00 | 203.97 | 44 | 7 | 0 |
| 2025 | **61.6235** | 58.38 | 124.78 | 177.52 | 313.94 | 222 | 43 | 3 |

### 4.4 P1 reserve families — all nine, all four years

Each cell: **hours dual>0 / max dual ($/MWh) / hours shortfall>0 / max shortfall (MW)**

| family | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| `east_10min_total` | 9 / 775.00 / 8 / 1200.0 | 0 / -0.00 / 0 / 0.0 | 3 / 32.69 / 0 / 0.0 | 1 / 1.86 / 0 / 0.0 |
| `li_10min_total` | 3 / 25.00 / 3 / 120.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 |
| `li_30min_total` | 4 / 25.00 / 4 / 540.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 |
| `nyc_10min_total` | 152 / 25.00 / 88 / 500.0 | 21 / 25.00 / 20 / 342.7 | 22 / 25.00 / 15 / 342.7 | 48 / 25.00 / 33 / 460.5 |
| `nyc_30min_total` | 68 / 49.42 / 52 / 1000.0 | 15 / 25.00 / 12 / 416.3 | 9 / 25.00 / 9 / 388.7 | 25 / 25.00 / 24 / 481.1 |
| `nyca_10min_spin` | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 |
| `nyca_10min_total` | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 |
| `nyca_30min_total` | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 | 0 / -0.00 / 0 / 0.0 |
| `seny_30min_total` | 12 / 500.00 / 10 / 1800.0 | 4 / 40.00 / 3 / 205.6 | 1 / 40.00 / 1 / 2.5 | 8 / 40.00 / 7 / 424.4 |

### 4.5 Annual TWh per klass (P1)

| klass | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| `CC_CHP` | 13.4279 | 15.9260 | 19.5871 | 20.4056 |
| `CC_REGULAR` | 36.8800 | 33.8439 | 36.9842 | 35.3487 |
| `COAL_BIT` | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `COAL_PRB` | 0.6552 | 0.0000 | 0.0000 | 0.0000 |
| `CT_CHP` | 2.0850 | 1.5430 | 1.2003 | 1.6859 |
| `CT_PEAKER` | 4.2661 | 0.3982 | 0.3716 | 1.3198 |
| `OTHER` | 2.1861 | 2.1973 | 2.2014 | 1.9483 |
| `ST_CHP` | 1.4936 | 1.3725 | 1.1315 | 1.4498 |
| `ST_GAS` | 6.4847 | 9.7315 | 8.5034 | 9.3041 |
| `biomass` | 1.0615 | 0.8395 | 0.7597 | 0.6724 |
| `hydro` | 25.6101 | 26.6158 | 26.7390 | 24.0589 |
| `import` | 27.8487 | 23.3360 | 20.7073 | 19.3580 |
| `nuclear` | 26.7531 | 27.4871 | 26.9532 | 28.3416 |
| `oil` | 0.6255 | 0.1498 | 0.4436 | 1.2840 |
| `solar` | 0.1093 | 0.2798 | 0.5861 | 0.9813 |
| `wind` | 4.7044 | 4.5907 | 6.0116 | 7.0487 |
| **ISO TOTAL** | 154.1909 | 148.3114 | 152.1801 | 153.2070 |

### 4.6 `metrics.json` — **absent, and that is expected, not a failure**

`results/calibration/nyiso228_control_span/` contains `meta.json`, `run_config.json`,
`legitimacy_diagnostics.json`, `system.parquet`, `flows.parquet`, `storage.parquet`, `btm.parquet`,
`dispatch/`, `floors/` and `hourly/` — **but no `metrics.json`**. `replay_keeper.py` solves and
writes diagnostics; it does not score. The charter assigns scoring to the parent ("You are not
expected to compute C3a/C3b percentages; the parent scores"), so there are no `metrics.json` headline
rows to report from this bundle. The parent must run its scorer to produce them.

`legitimacy_diagnostics.json` **was regenerated** (68 KB, written at the end of this invocation).
Its gate verdicts:

| diagnostic | verdict |
|---|---|
| **D-1** (diurnal shape) | `passed = True` |
| **D-2** (mechanism attribution / forced share) | `passed = True` |
| **D-4** (off-window binding) | `passed = False` |

The run logged `WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still
written; C7/C8 score from its contents)`. The D-4 failure is **pre-existing and not introduced by
this arm** — nyiso-227 reported D-4 `passed=False` on *both* sides of its A/B with byte-identical
failure text, and the 2023 row here is that same text: *"plant 2480 is floored for 0.0015 TWh (0.1 %
of the mechanism's forced energy) while its own measured median output over the 157 hours the floor
actually binds for it is 0.000 MW"*. A second 2023 row (plant 8906, 0.2283 TWh, 12.2 %) is likewise
carried by the incumbent recipe, not created here.

## 5. THE ARM-C REPRODUCTION CHECK (PRECOMMIT §5) — **PASSES, decisively**

PRECOMMIT §5 asks whether 2023 `ST_GAS` lands near **1.591 TWh** and 2024 near **1.410 TWh**, and
makes the consequence explicit: *"If arm C does NOT reproduce those, the G-DRIFT audit above is wrong
and every comparison in this session is re-based on arm C rather than on the keeper."*

**First, a definition correction that matters — and I state the actual numbers either way.**
1.591 / 1.410 are **not** model ST_GAS dispatch. The source
(`docs/RESULT-nyiso227-c3b-measured-2026-09-11.md` §1) records the row as
**`C1 ST_GAS |miss|`** — an *absolute error* `|model − actual|`. Read as dispatch, no slice of this
bundle is close, and the honest figures are:

| slice, model P1 TWh | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| ISO-wide `ST_GAS` (`class_hourly`) | 6.4847 | 9.7315 | 8.5034 | 9.3041 |
| ISO-wide `ST_GAS` (`unit_hourly`/`plant_group`) | 6.5578 | 9.7490 | 8.5399 | 9.4485 |
| NYC-only `ST_GAS` | 3.4483 | 7.2858 | 4.2685 | 4.3477 |
| NYC + Long Island `ST_GAS` | 5.8938 | 9.3901 | 7.4393 | 7.7517 |

The 2023 > 2024 ordering the targets imply does hold in every slice, but the magnitudes sit ~4.6×
above 1.591 / 1.410 — because those are residuals, not levels. Computing the `|miss|` itself needs
the EIA-923 actuals the parent's scorer holds, so **the parent should confirm C1 `ST_GAS` |miss|
≈ 1.591 (2023) / 1.410 (2024) when it scores.**

**Second, the same RESULT §1 table carries three arm-side quantities that are computable from this
bundle alone, and all three reproduce EXACTLY:**

| quantity | nyiso-227 arm | **arm C here** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **C3a** (pooled LW mean price, 5 load zones) | 33.6760 / 40.1782 / 61.6235 | **identical** | `33.6760` | `40.1782` | `61.6235` |
| **D-2 `reliability_floor × ST_GAS`** TWh | 1.8716 / 2.1733 / 2.0983 | **identical** | `1.8716` | `2.1733` | `2.0983` |
| **C8 ST_GAS forced share** | 0.1596 / 0.2071 / 0.1796 | **identical** | `0.15957` | `0.20709` | `0.17959` |

C3a reproduces to **four decimal places in all three years — a deviation of $0.0000/MWh**, against
PRECOMMIT §5's allowance of $0.30/MWh. D-2 and C8 reproduce to every digit nyiso-227 published.

**Verdict: the LIVE hunk `data/raw/reference/reliability_floor_coeffs_NYISO.csv` (0.1750 → 0.1663) is
present and active in this solve, and arm C carries nyiso-227's post-re-basing state exactly. The
G-DRIFT audit of PRECOMMIT §2 stands, and arms A and B should be differenced against arm C.**

## 6. TWO SUBSTANTIVE OBSERVATIONS FOR THE PARENT

**(a) PRECOMMIT §1.2's "the model has NO upper tail, ceiling ~$200–315" is true for 2023–2025 and
NOT true for 2022.** The 2023–2025 columns reproduce §1.2 exactly (max 213.86 / 203.97 / 313.94;
p99 63.30 / 116.00 / 177.52; h>$300 = 0 / 0 / 3). But **2022 reaches a load-weighted max of
$1,429.99** with 8 hours above $300, 30 above $200 and 197 above $150 — an order of magnitude above
the other three years, and §1.2's table left 2022's model cells blank (`—`). The amplitude diagnosis
should be restated as *"no upper tail in 2023–2025"*; 2022's tail exists and the miss there is its
**shape and hour-placement**, not its absence.

**(b) The §1.3 scarcity finding needs the same split, and the 2022 evidence strengthens the
underlying point rather than weakening it.** The three NYCA-wide families —
`nyca_30min_total`, `nyca_10min_total`, `nyca_10min_spin` — **never bind in any hour of any of the
four years**, 2022 included, exactly as §1.3 says. What is new is that in 2022 the *locational*
families do reach their full published penalties: `east_10min_total` hits **775.00** (9 h, max
shortfall 1,200 MW) and `seny_30min_total` hits **500.00** (12 h, 1,800 MW), where in 2023–2025 they
cap at 32.69 and 40.00. So the machinery is capable of pricing scarcity at the published penalty; in
2023–2025 it simply never gets there, and the NYCA-wide tier is dead in all four years. The NYC
families pin at their $25 penalty in every year (152 / 21 / 22 / 48 hours).

## 7. DISCIPLINE NOTES

* **Committed: the tracked slim set only — 23 files, 6.8 MB.** `.gitignore` already excludes
  `results/calibration/*/dispatch/` (line 651) and `results/calibration/*/hourly/unit_hourly_*.parquet`
  (line 672). **A blanket `git add -f` would have forced past both and staged 164 MB**, which the
  charter forbids ("the heavy `dispatch/` parquets are gitignored; do not force-add them") and which
  the Git & Pushing rules bar from `git push`. An unforced `git add` yields exactly the intended slim
  set, so that is what was used. `git status --short` showed nothing outside the bundle path.
* **Nothing was deleted** (rule 31 `[R-RETAIN]`). The full 164 MB bundle — `dispatch/` and
  `unit_hourly_*` included — remains on local disk for the owner's promotion decision. **This
  container is ephemeral and those gitignored artifacts will not survive it.**
* Touched **only** this bundle and this report. No `src/`, no `scripts/`, no `.gitignore`, no
  `CLAUDE.md`, no PRECOMMIT, no mechanism matrix, no calibration log, no
  `frontend/data/backcast/**`, no other shard's files, no PR, no registration script.
