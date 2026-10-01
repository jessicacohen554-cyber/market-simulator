# PRECOMMIT — SPP-38 card A: land the EIA-860 vintage-cache repair, then re-solve the keeper on a correct LP input

Lane **SPP-38** · base `origin/main` @ **`859c5dd52f4ac9e2be6381faf595a85ec66de217`** ·
branch `claude/spp-38-vintage-cache-repair-<suffix>` · DATA PROFILE `spp`.

**Object:** the defect `docs/handoffs/FINDING-spp-37-order-sensitivity-2026-09-12.md`
measured at zero LP — years 2+ of every SPP span run compute their unit-outage
denominator and their CC duct-peaking offer band from **year 1's** EIA-860 vintage,
because the loaders are `lru_cache`d on keys that omit the active directory.

**This is a construction repair, not a mechanism.** No `ScenarioConfig` field, no gate,
no declared default flip, no free parameter (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`),
**no matrix row and no matrix cell verdict moves** (rule 28 `[R-MECH-MATRIX]` does not
reach a cache key — it is not a tuning channel). There is no posture to A/B: one of the
two constructions is simply wrong about which fleet existed in 2025. The basis is
rule 14 `[R-ACCURATE]`, never the residual.

---

## 1. A1 — THE REPAIR (parent, ZERO LP). LANDED.

Each leaking loader keeps its **public name as an uncached thin shim** and moves its body
into a **cached core taking the active EIA-860 directory as its first key argument** — the
pattern the repo already uses four times (`cod_ramp._load_cod_map(eia860_dir)`,
`chp._chp_by_plant`, `eia860._cc_steam_part_generators`, `eia860._eia860_plant_sectors`).
Where the core reads a sheet directly it now reads **from its own argument**, so a stale
global cannot desync from the key.

**TWELVE loaders repaired, not eleven.** FINDING-spp-37 §3's table has twelve rows and
calls eleven of them "LEAKS"; the twelfth, `eia860_selfcommit_scope_plants`, is
vintage-blind by exactly the same construction — it is a `maxsize=1` cache over a union of
two loaders that both move — and would have pinned year 1's union even with its inputs
repaired. Its "stable" reading was an artifact of the probe clearing the union's own cache
but not its two legs, not a property of the data, and the repair does not rest on it.

| # | module | public shim | cached core | reached by SPP keeper 10 |
|---|---|---|---|---|
| 1 | `data/outages.py` | `_iso_plant_capacity` | `_iso_plant_capacity_cached` | **YES — both outage overlays** |
| 2 | `data/outages.py` | `_iso_plant_unit_capacity` | `_iso_plant_unit_capacity_cached` | no (`unit_outage_st_capacity_basis=False`) |
| 3 | `data/outages.py` | `_fleet_status_index` | `_fleet_status_index_cached` | no (`unit_outage_fleet_status_scope=False`) |
| 4 | `data/fleet/campd_bins.py` | `cc_duct_peaking_pct` | `_cc_duct_peaking_pct_cached` | **YES — `cc_duct_peaking=True`** |
| 5 | `data/fleet/campd_bins.py` | `cc_summer_capacity` | `_cc_summer_capacity_cached` | no |
| 6 | `data/fleet/campd_bins.py` | `cc_winter_capacity` | `_cc_winter_capacity_cached` | no |
| 7 | `data/fleet/campd_bins.py` | `coal_summer_capacity` | `_coal_summer_capacity_cached` | no |
| 8 | `data/fleet/eia860.py` | `_eia860_plant_sector` | `_eia860_plant_sector_cached` | no |
| 9 | `data/fleet/eia860.py` | `eia860_plant_states` | `_eia860_plant_states_cached` | no |
| 10 | `data/fleet/eia860.py` | `eia860_regulated_plants` | `_eia860_regulated_plants_cached` | no |
| 11 | `data/fleet/eia860.py` | `eia860_costofservice_majority_plants` | `_eia860_costofservice_majority_plants_cached` | no |
| 12 | `data/fleet/eia860.py` | `eia860_selfcommit_scope_plants` | `_eia860_selfcommit_scope_plants_cached` | no |

Rows 2–12 are the same defect class, latent behind gates SPP has off; they are fixed here
rather than left for the next ISO to arm vintage tracking to re-discover.

### 1.1 The blast radius, MEASURED (probe §6 re-run at this HEAD)

```
tracks_solve_year=True  ['vintage_2023','vintage_2024','eia-860']  CHANGES per year -> live
tracks_solve_year=False ['eia-860','eia-860','eia-860']            constant -> strict NO-OP
```

Re-confirmed **at this HEAD, not inherited**: of 154 committed bundle configs carrying the
field, **SPP's is the only one that arms it** — see §1.4. So the repair is byte-inert for
every other ISO, for every SPP single-year run, and for year 1 (2023) of every SPP span.

### 1.2 The repair is PROVEN, not asserted — `scripts/probes/_spp37_vintage_cache_census.py`

The probe is updated (it referenced `cache_clear` on names that are now uncached shims) and
gains a **§2b** that measures the invariant §2 never could: §2 clears before every read, so
it measures whether the DATA moves; §2b reads vintage A then vintage B on a **warm** cache
and compares against B's own cold value — which is the defect itself.

* **§2b — all twelve read `rekeys`.** Pre-repair the two live rows returned year 1's value.
* **§5 is the decisive number.** The span-vs-single-year delta in **the LP's own 2025
  availability input** (`availability[g,:] *= f`, a direct generator bound):

  | overlay | pre-repair (FINDING §4b) | post-repair |
  |---|---|---|
  | ≥ 5-day | **−5,817,173 MWh (18 bins differ)** | **+0 MWh (0 bins differ)** |
  | < 5-day | **+142,296 MWh (5 bins differ)** | **+0 MWh (0 bins differ)** |

  The span path now computes exactly what the single-year path computes — which FINDING §5
  established is the correct leg.
* §3/§4 are unchanged (they read cold maps): the denominators still move across vintages
  (224/229/238 bins; 51,319.20 / 50,905.65 / 54,059.64 MW) and the stale map still misses
  12 bins / 526.1 MW in 2024 and 26 bins / 3,692.3 MW in 2025 — that is the *data*, which
  the repair does not and must not change.

### 1.3 Regression test — `tests/unit/data/test_eia860_vintage_cache_keying.py` (33 tests, hermetic)

Pins both legs the prompt requires, over synthetic vintages in `tmp_path` (no `data/raw`):

* **re-keys** — vintage flipped between calls on a warm cache returns each vintage's own
  value, for all twelve (the nine sheet-backed ones driven from synthetic parquets, the two
  fleet-summed ones from a monkeypatched vintage-dependent fleet, the union one through
  both its legs);
* **strict no-op at a constant vintage** — the second call is a cache HIT: the **same
  object** back, `currsize == 1`, `hits >= 1`;
* **structural guard** — each public name has no `cache_info`, each core does, and each
  core's **first parameter is named `eia860_dir`**, so the keying cannot be regressed away
  silently.

### 1.4 Hard stops cleared before push

| check | result |
|---|---|
| `tests/unit/pipeline/test_run_year_kwarg_binding.py` (the SPP-36 incident guard) | **4 passed** |
| `tests/unit/data/test_eia860_vintage_cache_keying.py` (new) | **33 passed** |
| `test_outages` + `test_campd_bins` + the 4 unit-outage/coal suites | **209 passed, 23 subtests** |
| `test_cache_control.py` + `tests/regression/test_fleet_facade.py` | **24 passed** |
| fast lane `-m "not slow and not integration and not fulldata"` | **see §5** |
| `ruff check src/` + `ruff format --check` | clean |
| committed bundle configs arming `eia860_vintage_tracks_solve_year` | **SPP only**, re-measured at this HEAD |

`tests/unit/data/test_cache_control.py::test_enumerates_and_clears_a_real_package_cache` is
updated to use `_iso_plant_capacity_cached` as its example cache. That test is **about the
cache-control walker**, not about `_iso_plant_capacity`; the cache now lives on the core, so
the example moves with it and the test's intent is unchanged. (It was the only
`.cache_clear()` call on any of the twelve anywhere in `src/`, `scripts/` or `tests/`.
Every other reference — `patch.object`, `monkeypatch.setattr`, plain calls — targets the
public name, whose signature is unchanged, and needs no edit.)

### 1.5 Rule 27 `[R-PUSH]`

All three edited modules are ≥ 300 lines and all three **grew** (no shrink):

| file | before | after |
|---|---|---|
| `src/market_sim/data/outages.py` | 2,774 | 2,843 |
| `src/market_sim/data/fleet/campd_bins.py` | 2,739 | 2,798 |
| `src/market_sim/data/fleet/eia860.py` | 3,836 | 3,909 |

Edited locally with the Edit tool; the exact on-disk bytes are pushed; the pushed blobs are
verified (line count + hash) immediately after the push and before anything else.

---

## 2. G-DRIFT — the rule 29(b) code audit, recorded BEFORE any arm is solved

Keeper 10's `basis_sha` **`706aa5475a44e2bb87326a556833f326f926160b`** → base
**`859c5dd52f4ac9e2be6381faf595a85ec66de217`**, over
`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`. **10 files, +896/−7.**

| file | Δ | classification |
|---|---|---|
| `config/scenarios.py` | +114 | **INERT** — two new fields, `miso_import_sil_measured_envelope` and `gas_offer_margin_zonal_anchor_vintage`, both `bool = False`, both declared in `_CACHE_KEY_OPTIONAL_FIELDS` at their default, absent from keeper 10's recipe |
| `runner.py` | +42 | **INERT** — one `if getattr(config, "miso_import_sil_measured_envelope", False):` block, default-off and MISO-only |
| `model/interchange/{__init__,miso}.py` | +119 | **INERT** — new module, reached only from that gate |
| `data/eia930/{__init__,envelopes}.py` | +113 | **INERT** — new module, reached only from that gate |
| `data/fuel/zonal_anchor.py` | +145 | **INERT** — new module, reached only under `gas_offer_margin_zonal_anchor_vintage` (default `False`) |
| `scripts/run_calibration.py` | +135 | **INERT** — CLI wiring for the two gates above; additive `add_argument`, `default=False` |
| `config/plant_taxonomy.py` | +29/−1 | **needs proof — see §2.1** (pumped-storage `PS` → `OTHER` classifier repair, gov-hydro-seam-1) |
| `scripts/run_calibration_full.py` | +206/−6 | **needs proof — see §2.1** (the hydro BENCHMARK predicate `_hydro_benchmark_is_923_only`; scorer-side, so it can move a scored band without touching the LP) |

*(The audit was first run against `2c2fc065`, where the work was done; `origin/main` then
moved to `859c5dd5` and the branch was rebased onto it. The audit was **re-run over the
increment** `2c2fc065 → 859c5dd5` across the same paths: **ZERO files changed on the solve
path**, so every classification below carries over to the new base unchanged.)*

**A "files changed, therefore void" heuristic is not a reason to spend an LP** (rule 29(b)).
The two hunks that could not be classified by inspection were **measured**, not asserted.

### 2.1 The two live-looking hunks, measured for SPP

* **`_hydro_benchmark_is_923_only("SPP", y)` reads `False` in 2023, 2024 and 2025.** The
  predicate fires only for a BA in `EIA930_PS_FOLDED_INTO_WAT` (`{MISO, PJM}`) or before its
  `EIA930_PS_SPLIT_COMPLETE_FROM` year (`{NEISO: 2025}`). **SPP is in neither.** INERT.
* **The whole scorer surface was then checked end-to-end, which is stronger than either
  hunk-by-hunk argument: keeper 10's COMMITTED bundle was re-scored at this base and
  reproduces its committed determination exactly** — `CALIBRATED`, rubric **v3.7**, grade
  **7 of 8**, **0 FAILS**, **1 ledgered C3c caveat**, **0 protective**, free-class C1
  **16/16 all · 12/12 free**, `fuelmix / sysvol / price_mean / price_shape / dispatch_corr /
  governance / forced_share` all PASS and `price_tail` CAVEAT. Zero LP spent.

**CONCLUSION: G-CTRL form 4 is VALID. Keeper 10's committed bundle is the control, and no
control solve is spent.**

### 2.2 The one LIVE hunk is MY OWN, and it is live by construction

**A1 is a LIVE hunk for SPP** — that is the entire point of the lane, and it is stated here
rather than classified inert. It changes SPP's 2024 and 2025 LP inputs (and only those: 2023
is year 1 and was always correct). This is exactly why the arm below is a **re-solve of the
keeper's own recipe** rather than a mechanism A/B: the control is keeper 10's committed
numbers, the arm is the same recipe on a repaired input, and the difference is the leak.

### 2.3 An anomaly found while establishing the baseline, recorded and NOT acted on

Keeper 10's promotion note records **C3b 0.1760 / 0.1658 / 0.1878**. The scorer at this base
reads **0.176 / 0.175 / 0.175**, and an independent reconstruction straight off the
committed `hourly/system_<y>.parquet` + `bench/SPP/<y>.json.gz` (the instrument the SPP
prompt pack documents) gives **0.1760 / 0.1722 / 0.1753**. The **C3a load-weighted price
reproduces to 4 dp in all three years on all three instruments** (25.7428 / 26.0214 /
29.5377), so the bundle and the bench agree; it is the note's 2024/2025 **C3b** figures that
are not reproducible from the committed artifacts by either the scorer or an independent
instrument. Nothing turns on it — C3b PASSes with room in every year on every instrument
(≤ 0.176 against a ≤ 0.20 bar) and the determination is unchanged — so it is reported, not
chased. **The baseline used below is the HEAD re-score**, which is the like-for-like
comparison (same scorer, same rubric, same artifacts).

---

## 3. A2 — THE RE-SOLVE. ONE SHARD, ONE INVOCATION, ONE BUNDLE.

**Rule 32(a): the parent runs NO LP.** Rule 32(b) as amended 2026-09-12: **slim per-year
fan-out is BANNED** — the legs cannot be reassembled (`build_payload` needs the bundle-root
`system.parquet`; D-1/D-2/D-4 need `dispatch/*.parquet`; `--reuse-solved` gates on both) and
a composite's diagnostics **pass with ZERO ROWS**. This is the defect SPP-36 hit. So: one
shard, one `--years 2023 2024 2025`, years sequential inside it (rule 12), one bundle.

**Rule 35(b) — the year set enumerated BEFORE anything is pruned.** The union of `years`
over every SPP sidecar in `frontend/data/backcast/registry/` is exactly
**{2023, 2024, 2025}** — one registered run (`2026-09-12-spp-36-shortwindow-span`), no run
stamped `holdout.keeper` to it. The span shard therefore covers SPP's whole registered year
set, and rules 34(c) / 35(c) are satisfied without a second shard. *(Noted so it is on the
record: `bench/SPP/` is 2023–2025 only, so SPP's 2019–2022 actual-LMP coverage from SPP-30
is still unscoreable. That gap is not this lane's.)*

**The arm is a PURE REPRODUCTION of keeper 10's recipe with NO `--set` at all:**

```
python3 scripts/replay_keeper.py results/calibration/spp36_span \
  --years 2023 2024 2025 --out-dir results/calibration/spp38_span \
  --note "SPP-38: keeper 10 recipe re-solved on the repaired EIA-860 vintage cache"
```

Config signature the shard must self-verify, **or STOP and not push**:

| check | required value |
|---|---|
| `git rev-parse HEAD` | the pinned full 40-char SHA of this PRECOMMIT's commit |
| `offer_curve_by_group` whole-mapping `json.dumps(sort_keys=True)` SHA-256 | `090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65` |
| `eia860_vintage_tracks_solve_year` | `True` |
| `unit_outage_short_windows` | `True` |
| `unit_outage_short_windows_gas` | `False` |

*(The handoff prompt describes `offer_curve_by_group` as "uniform 0.93". It is not — the
mapping carries 18 distinct values (0.5 … 15.0). **The SHA-256 above is the binding check**
and it verifies against the committed keeper; the "uniform 0.93" phrasing is wrong and is
not used as a gate. The channel is not touched, re-cut, swept or examined against any gate:
rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`.)*

**Rule 34 `[R-SHARD-PROMOTABLE]`: the shard PUSHES its bundle to its own branch**, including
`dispatch/<year>_P1.parquet` and the bundle-root `system.parquet`, by appending a
`.gitignore` **negation** for its own out-dir and using a **plain `git add`** (never
`git add -f`, which the auto-mode classifier refuses). A result that cannot back a promotion
must not be produced. The parent keeps the heavy files out of `main` at the seam (rule
32(d)); `.gitignore` §8's existing slim-bundle rules do that automatically.

**Rule 29(c) / 31 `[R-RETAIN]`:** `results/calibration/spp38_span/` is added to the parent's
`.gitignore` **in this commit, before the shard runs** — that is what discharges 29(c).
**Nothing is `rm`'d, ever.** The line is removed by the promotion commit if the owner
promotes.

**Forbidden to the shard, by name:** `git add -A` / `git add .`; `dashboard_add_run.py`,
`build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, anything under
`frontend/data/backcast/**`; any edit under `src/` or `scripts/`; opening a PR; deleting any
result; `git pull` / `git rebase` / any "sync". Memory (rule 32(c)(8)): run the runner
unmodified, never pass `--no-container-preflight`, report the `container preflight:` and
`memory peak:` lines.

---

## 4. A4 — WHAT THE RE-SOLVE MEANS, DECLARED BEFORE IT RUNS

**The repair is landed on rule 14 `[R-ACCURATE]`, and the movement is REPORTED, NOT GATED.**
C3a / C3b / C1 will move in 2024 and 2025 by an amount nobody can predict from here.

* If the bands get **worse**, the repair **stays** and the worse fit is a discovered bug to
  root-cause — rule 14's own instruction — not a reason to revert.
* If they get **better**, that is **not evidence for it either**.
* There is **no pre-registered gate on the residual**, because there is no arm to kill: a
  known-wrong LP input is not a candidate mechanism competing against a correct one
  (rule 1 `[R-STRUCT]`).

**The baseline the movement is reported against** (keeper 10, re-scored at this base, §2.1):

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a model LW price $/MWh (actual) | 25.74 (25.13) | 26.02 (25.45) | 29.54 (28.60) |
| C3b monthly-LW NRMSE | 0.176 | 0.175 | 0.175 |
| determination | \multicolumn — `CALIBRATED`, grade 7/8, 0 FAILS, 1 ledgered C3c, 0 protective, free-class 16/16 · 12/12 ||

**2023 must reproduce keeper 10 to 4 dp** — it is year 1 in both constructions and the
repair cannot reach it. That is the single strongest self-check on the shard's output: a
2023 that moves means something other than the cache key changed, and is a stop-the-line
event.

**Rule 21 `[R-DOF]`:** the like-for-like DOF baseline is the control's own config **rebuilt
at HEAD**, never keeper 10's committed ledger (which reads 5 entries / 3 residual and can be
stale — keeper 9's was). The repair adds **zero** free parameters.

**After this lands, keeper 10's committed 2024/2025 numbers are superseded** and the
re-solved bundle becomes SPP's control. Until then, rule 29(b) **form 4 is VOID for SPP
2024/2025** — differencing a new arm against keeper 10 would measure the leak plus the arm.
That is why A2 precedes the queue (R-be day selection, R-ba merit inversion, R-bc
price-forming curtailment), all of which reason off per-plant 2024/2025 thermal behaviour —
the years the leak moves, and `ST_GAS` the class it moves most (+1.2737 TWh in 2025).

**`[R-HOLDOUT]` was removed 2026-09-09.** No SPP number here is a certified out-of-sample
skill claim; `CALIBRATED` is a rubric determination.

---

## 5. STANDING ITEMS — flagged, not acted on

* **The bundle-retention parity gate is already RED at the base**, five offenders:
  `caiso275_B_gascoupling_{2023,2024,2025}` and `nyiso227_rebasis_span` (other lanes' —
  left alone) and **`results/calibration/spp36_2025`** (SPP's, inherited from SPP-36's
  banned fan-out). `spp36_2025` is also the only committed artifact showing the CORRECT 2025
  construction and is FINDING-spp-37 §4c's evidence, so rule 31 `[R-RETAIN]` keeps it until
  the owner rules. Recovery pin (full SHA, rule 33(d)):
  `git checkout 18ef91756ac84482a78ea719c2fc8d57ec7d5cf5 -- results/calibration/spp36_2025`.
  Removing SPP's alone would not turn the gate green. **Raised, not acted on unilaterally.**
* **`scripts/lib/bundle_fleet.reconstruct_bundle_fleet` is order-dependent across years for
  SPP** (SPP-27) — the same defect class one layer over. **Assessed in §6 of the RESULT.**
* **SPP holds NO `complete` and NO `frontier`, and this lane creates neither.** Both are
  owner acts. `calibration-complete.json` is touched only for the keeper re-key that a
  promotion requires, and never to add a `complete` marker.
