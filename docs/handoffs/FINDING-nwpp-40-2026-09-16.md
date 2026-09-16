# FINDING — lane NWPP-40: the first NWPP calibration solve (2023–2025, hydro cascade coupling ARMED)

**Lane:** NWPP-40 (`docs/multi-iso/nwpp-addition-plan-2026-09.md` §8 W4 charter; owner ruling
N10-R: no screen) · **Model:** Fable (`claude-fable-5-1`) · **Branch:** `claude/kind-keller-p4a1k0`
(harness-designated) · **DATA PROFILE:** `nwpp` · **PRECOMMIT:**
`docs/handoffs/PRECOMMIT-nwpp-40-2026-09-16.md` (+ Addenda 1 and 2, same file) · **Run:**
`2026-09-16-nwpp-1-cascade` · **Bundle:** `results/calibration/nwpp40_span_A` · **LP:** ONE shard,
ONE `--year 2023 2024 2025` invocation, years sequential inside it (rules 12 / 16 / 32(b)); the
parent never ran an LP (rule 32(a)).

## 0. Report first

1. **DETERMINATION: `NOT-YET`** (rubric v3.8; price UNSCORED by construction — no `actual_lmp.json`
   block exists for NWPP, so C3a / C3b / C3c are SKIPPED in every year and the run certifies NO
   price level, shape or tail). Not the `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` reading the
   PRECOMMIT named as the ceiling: two physical criteria FAIL. Scorer reason line, verbatim:
   *"undocumented out-of-tolerance (FAIL) criteria: fuelmix, dispatch_corr"*. Caveat budgets
   untouched (0 ledgered, 0 protective); `grade_summary`: scored 5, target-grade 3, fails 2.
2. **C1 fuel-mix — FAIL.** The model dispatches every NWPP coal unit under the generic **`COAL`**
   class (legacy heat-rate bins, card N8), while the benchmark itemizes coal as
   `COAL_PRB` / `COAL_BIT` / `COAL_WC` / `COAL_LIGNITE`. The scorer therefore reads **model 0.0 TWh
   against 29.476 (PRB) and 9.678 (BIT) in 2023, 24.038 / 9.718 in 2024** — four MODEL-MISS rows —
   while the coal FAMILY is inside its band (C2 coal 2023: model 38.54 vs actual 39.71 TWh, PASS).
   One further row: 2024 `CC_REGULAR` share +3.6 pp (volume +1.59 TWh, inside ±8 TWh; share outside
   ±3 pp). 2025 is SKIPPED by the preliminary-923 rule (per-class actuals incomplete; the C2 family
   reconcile covers it). Free-class headline: C1 all 13/18 · free 9/14.
3. **C2 system volume — PASS** (gas 63.99 / 72.57 vs 71.98 / 76.56; coal 38.54 / 26.49 vs
   39.71 / 34.32 TWh in 2023 / 2024; 2025 diagnostic-only: gas +6.1 %, coal −30.4 %).
4. **C4 fleet hourly dispatch correlation — FAIL on coal, PASS on gas.** Coal r **0.511 / 0.535 /
   0.475**, NRMSE **0.321 / 0.408 / 0.451** (bars r ≥ 0.70, NRMSE ≤ 0.30); gas r 0.736 / 0.826 /
   0.803, NRMSE 0.201 / 0.151 / 0.209. D-1 says why: the model's coal off-peak CV is 0.004 / 0.003 /
   0.006 against a measured 0.030 / 0.033 / 0.084 (cv_ratio 0.134 / 0.090 / 0.066) — the model runs
   coal flat where the fleet cycles.
5. **C6 governance — PASS** (`authorized_price_tuning_declared: NONE`; every dispatched band 1.0,
   machine-checked; DOF ledger 3 residual-tagged entries, all inherited generic defaults).
   **C8 forced-energy share — PASS** (0.0 % forced in every gated class, every year).
6. **Memory peak (verbatim):** `memory peak: cgroup_peak_rss_gib=4.35, cgroup_peak_rss_plus_swap_gib=4.35,
   process_vmhwm_gib=4.05, process_vmswap_now_gib=0.00` against a 13.36 GiB cgroup ceiling; swap
   could not be provisioned on the relaunch (stale 10 GiB swapfile from attempt 1) and was not needed.
7. **Where the bundle is, and what a promotion costs from here (rule 34(e)):** the FULL bundle
   (36 files, 48 MB, including `dispatch/{2023,2024,2025}_P1.parquet` and the bundle-root
   `system.parquet`) is on the shard branch `claude/nwpp-40-span-b` at
   **`fe09a98e72efe473b4e5f1a3ea0ecbedd9178f0a`** (`git checkout fe09a98e72efe473b4e5f1a3ea0ecbedd9178f0a
   -- results/calibration/nwpp40_span_A`); the committed slim set + `hourly/` (cascade sidecars
   included) is on this branch at `88ab697d`; the heavy parquets also sit in this session's working
   tree until the container is reclaimed. **A promotion costs ZERO re-solves.** Nothing was deleted
   (rule 31).
8. **THE PROMOTION QUESTION (rule 31), asked explicitly:** this is the first NWPP bundle that has
   ever existed and there is no incumbent. It is structurally the most faithful NWPP run there is —
   by construction, being the only one — and it reads `NOT-YET` on two physical criteria, one of
   which (C1) is a class-taxonomy seam rather than a dispatch miss. **Should
   `2026-09-16-nwpp-1-cascade` be designated the NWPP keeper?** If yes, the promoting session runs
   `keeper_store.py --set NWPP 2026-09-16-nwpp-1-cascade`, adds NWPP to `keepers/index.json`,
   `build_status.py --iso NWPP`, `audit_keepers.py --iso NWPP`, re-keys `calibration-complete.json`,
   and re-stamps the matrix cell `K`. This lane recommends **promote**, on rule 1 `[R-STRUCT]`
   (structure first; there is no more-faithful alternative and no residual was tuned) and on rule 15
   (the dashboard needs an NWPP keeper for the status page to carry the region at all); the two
   FAILs stay reported at full magnitude either way.

## 1. Timeline — two shards, one run, one container restart

| when (UTC) | event |
|---|---|
| PRECOMMIT pushed, pin `c8819f51de3d8a8d5e754f016d7f3620e59e5185` | shard A launched (150-min budget, §4.5's 15–45 min expectation) |
| 09:16 | **shard A STOPPED at budget**: 2023 solved in 7,004.0 s = 116.7 min (P0 1,728.6 s / P1 5,217.1 s); 2024 ~32 min into P0; pushed nothing under `results/` (rule 32(b) STOP rule). Report `docs/handoffs/SHARDREPORT-nwpp-40-span-2026-09-16.md` at `4e218d0f` on `claude/nwpp-40-span-a`; its 2023 diagnostic record at `20807883399c9069f13ebf59be6e473e55ad3579` on `claude/nwpp-40-span-a-diag2023` |
| 09:20 | Addendum 1: budget re-set to 480 min on the measured rate, recipe unchanged; 23 NWPP-SNV VOLL hours in 2023 P1 recorded ex ante |
| 09:26:44 | shard B attempt 1 launched at pin **`9580bdd040a10ba5998ccf303129b2cca26bd4f4`** |
| ~09:27–10:30 | attempt 1 **killed by a container restart** while the shard session was idle (`uptime` 1 min on re-entry; no Traceback, no OOM). Log kept: `results/calibration/nwpp40_span_A.launch.attempt1-killed-by-container-restart.log` |
| 10:31:30 | attempt 2 relaunched with the byte-identical command line — **THE run**; parent kept the container alive with half-hourly pokes |
| 15:12 | Addendum 2: budget extended to 600 min (2023 4,942.9 s; 2024 10,412.0 s) |
| 19:42:28 | bundle written: **551 min** wall from relaunch (2025 P1 alone 15,831.7 s) |
| 19:46 | bundle pushed at `fe09a98e` (rule 34(a): `.gitignore` negation + plain `git add`) |
| 19:48 | parent fetched, checked out, verified; shard archived; keep-alive pokes deleted (rule 33) |

Per-pass HiGHS (single-thread profile, 4 vCPU): 2023 P0 1,236.5 s (523,199 it) / P1 3,674.2 s
(533,017); 2024 P0 2,235.8 s (383,505) / P1 8,156.4 s (876,716); 2025 P0 1,833.6 s (328,523) / P1
15,831.7 s (1,058,919). The warm P1 grew 2.2× then 1.9× year over year while P0 stayed
1,237–2,236 s — reported, not interpreted. Span 33,038.5 s = 550.6 min.

## 2. Verification against the PRECOMMIT (§7 steps 1–3)

- `git ls-tree -r fe09a98e -- results/calibration/nwpp40_span_A` → **36 files** (rule 34(d)),
  `dispatch/<year>_P1.parquet` × 3 present. Checked out at the immutable SHA, then unstaged so only a
  plain `git add` chose the slim set (the SPP-40 trap); the shard's `.gitignore` negation was NOT
  taken onto this branch.
- **Config signature:** `iso NWPP`, `mode backcast`, `years [2023, 2024, 2025]`, `passes ["P1"]`,
  `hydro_cascade_coupling true`, `hydro_backfill_year 2024`, `hydro_eia930_monthly false`;
  `committed / econ_low / econ_high / peak` = **1.0** on every class NWPP dispatches; no `phys_*`
  row; the three `*_INTERMEDIATE` curves carry the generic non-unit defaults and are inert
  (PRECOMMIT §2.4). `use_campd_bins true` and inert (NWPP ∉ `CAMPD_BINNING_ISOS`).
- **Cache keys:** the bundle's recorded `scenario_config` hashes to **`678d38882c2bcfca`** = the
  PRECOMMIT's expected armed 2023 key; the same construction re-run at HEAD reproduces all three
  (`678d38882c2bcfca` / `3977fcf867296207` / `ff5254b07b104419`; unarmed `b40c352048c144cc` /
  `e54ec61ffddaf915` / `1750859025f0ea4e`). The runner records no per-year key field (reported by
  the shard; not repaired).
- `git_sha` in the bundle is `d59b84bd`, not the pin: five docs-only status commits sit above
  `9580bdd0` on the shard branch; `src/`, `scripts/`, `data/` are byte-identical between them.
- **Cascade sidecars:** `hourly/hydro_cascade_{2023,2024,2025}.parquet`, 43,800 rows each
  (5 plants × 8,760 h), columns `year, pass, plant_code, hour, spill_kcfs, pond_kcfsh, water_value`.
  Resolve line every year: `5 coupled plants [3921, 3886, 6200, 3075, 3925], 5 links, tau by link
  [0, 1, 1, 0, 0] h`.

## 3. Registration mechanics — one gap found and closed in `scripts/`, zero LP

1. **The bundle carried no benchmark parquets** (they live in the gitignored content-addressed
   `results/calibration/_shared/NWPP/` on the shard). Rebuilt in place with
   `run_calibration_full.py --rebuild-benchmark` (a post-processing step over the persisted dispatch;
   no re-solve). First rebuild reproduced the shard's hashes exactly (`eia923-28b6d15f2185`,
   `campd-a5fde7813755`).
2. **`render_calibration_html.build_payload` then refused the bundle: no `eia930` input.** Root
   cause: the runner's `_eia930_frame_generic` calls `load_eia_hourly_benchmark`, which is `None`
   for a POOL region by construction (NWPP names no single `<BA> hourly` file; FINDING-nwpp-39 §4
   had recorded exactly this). The pool-aware, per-member-screened equivalent already existed —
   `build_calibration_reference._pool_hourly_benchmark` (NWPP-31), the function the scorer's
   `calibration_reference.json` NWPP block is built from. **Fix (this lane, `scripts/` only, in
   commit `88ab697d`):** `_eia930_frame_generic` dispatches on `_is_pool_region(iso)` — pool →
   `_pool_hourly_benchmark`, else the loader unchanged. Data-driven, never an `iso ==` ladder;
   every single-BA region takes exactly the path it took before. `tests/unit/pipeline/
   test_hydro_cascade_cli_flag.py` (5 tests) still passes against the patched runner.
3. Second rebuild: `eia930-e539ed483b64` appears and **`eia923` moves to `b651a5f68862`**, because the
   923 benchmark frame takes the 930 frame as its renewable under-count repair input (2025: wind
   21.96 → 38.22 TWh, hydro 74.94 → 110.32 TWh grid totals). A benchmark-side change only; the solve
   is untouched.
4. `dashboard_add_run.py --label "nwpp 1 cascade" --bundle results/calibration/nwpp40_span_A
   --no-prune` → `RUN_ID=2026-09-16-nwpp-1-cascade`; wrote the sidecar, `runs/<id>.js` (383,372 B),
   `bench/NWPP/{2023,2024,2025}.json.gz` (new ISO — 229,534 / 240,286 / 235,780 B) and, after the
   diagnostics + attestation, `metrics.json`. `legitimacy_diagnostics.py` → D-2 / D-4 / D-5 / D-9 /
   D-10 PASS, D-1 FAIL (COAL all three years, ST_GAS 2025 — the shape leg C4 already carries);
   `gen_nwpp40_attestation.py` → `calibration_attestation.json` (recipe machine-checked,
   `authorized_price_tuning_declared: NONE`, no `authorized_price_tuning` block, 5 free parameters,
   `exceptions: []`). `build_manifest.py` assembles 11 runs across 9 ISOs, NWPP years
   `[2023, 2024, 2025]`; its regenerated `rubric-consts.js` (3.7 → 3.8) was NOT committed (deploy-
   owned generated file).
5. **Energy balance, printed by the report and carried here at full magnitude:** model generation
   270.51 / 277.71 / 288.82 TWh vs EIA-930 net generation 277.58 / 287.42 / 298.83 → **−7.07 /
   −9.72 / −10.01 TWh, every year outside the ±3.0 TWh tolerance.** The served measured interchange
   the LP nets from load reads −1,569 / −1,472 / −546 MW avg (export-positive; 13.7 / 12.9 / 4.8 TWh
   net export) where the benchmark's own `Total interchange` reads −6.63 / −3.12 / +5.35 TWh. The two
   are different constructions of the same seam (NWPP-20's `NG_adj − D_adj` pool identity vs the
   benchmark column; PRECOMMIT §8 line 10) and the gap is routed, not absorbed (§7).

## 4. What the solve says — reported, not adjudicated

**Prices (MODEL-ONLY, UNVERIFIED — nothing to compare against):** load-weighted mean $/MWh
48.71 / 28.59 / 31.82. NWPP-SNV clears at VOLL ($2,000) in **23 zone-hours in 2023** (4,221.7 MWh
slack over 13 hours — the identical 23 hours shard A's 2023 leg produced, so the result is
reproducible) and **34 in 2024** (8,818.0 MWh slack, June–July); **none in 2025**. No other zone
exceeds $144.12 (2023), $41.75 (2024), $51.46 (2025). Zero negative-price hours; zero dump.

**Class TWh, model vs the EIA-923 benchmark** (2025 benchmark preliminary): CC_REGULAR 53.47 /
58.32 / 62.67 vs 56.33 / 56.73 / 56.43; COAL 38.54 / 26.49 / 26.36 vs coal family 39.71 / 34.32 /
(37.87 diag); CT_PEAKER 2.97 / 6.16 / 9.71 vs 7.10 / 7.34 / 5.08; ST_GAS 0.13 / 0.45 / 0.32 vs 1.51 /
4.62 / 4.17; hydro 106.87 / 107.88 / 113.08 vs 106.93 / 107.90 / 110.32; nuclear 8.43 / 9.93 / 7.73
vs 8.44 / 9.97 / 7.75; wind and solar ride the L1 delivered bound (D-10: pinned, advisory-only).

**C5a CO2 (REPORTED-ONLY, never gating since v2.9):** model 28.674 / 32.775 / 35.524 Mt vs eGRID
84.182 / 79.501 / 78.919 → **−65.9 / −58.8 / −55.0 %.** Far larger than the fuel-volume miss can
explain (model coal alone is 26–39 TWh); a per-plant emission-rate / footprint-coverage question,
routed (§7).

**The coupling in the solve** (from the sidecars; there is NO unarmed control by ruling N10-R, so
no residual delta is claimed — rule 1): the spill object is live — plant-hours with spill > 0
**9,210 / 8,894 / 9,115**, concentrated at Bonneville (3,259–3,418 h, mean 47–49 kcfs, max 477) and
Ice Harbor (3,260–3,559 h, mean 17–19 kcfs); Wells 1,348–1,544 h; Rocky Reach 726–961 h; Chief
Joseph 186 / 30 / 7 h. Pondage binds only below a head with storage: CHJ pond peaks 101.9 / 234.0 /
315.1 kcfs·h, IHR 157.7 / 232.8 / 0.0; BON, WEL, RIS ponds read 0 all year. Pond-balance duals are
~0.001 $/kcfs·h in every hour of 2023 and 2024 (zero plant-hours with |dual| > 1) — **except Chief
Joseph in 2025, where the dual sits at a constant −325.17 for 5,808 of 8,760 hours with pond = 0
and spill = 0.** Checked, not assumed: none of the five coupled plants nor Grand Coulee (6163) is
among the 255 plants backfilled with 2024 water in 2025 — each carries its own 2025 monthly series
(CHJ 9,806 GWh vs GCL 16,154 GWh, ratio 0.607 against 0.603 / 0.598 in 2023 / 2024) — so the NWPP-32
backfill posture is not the cause by that evidence. Routed as the first cascade-specific question
(§7).

## 5. The determination basis — PRECOMMIT §8's ten lines, carried

1. **Price gap** — C3a / C3b / C3c UNSCORED, never PASS; model mean LMP printed MODEL-ONLY above.
2. **G-A3** — amplitude response 1–10 %, not ≥ 30 % (owner ruling N12 accepts it as a
   mis-specified gate).
3. **Coupled set is 16 %**, not 66 %, of hydro nameplate (5 of 15 links).
4. **PNCA terminated 2024-09-15 inside the window**; NWPP-38 verdict (a).
5. **Card N7's two-regime PRM** — one scalar 0.144; inert in a backcast; lever NWPP-57.
6. **2025 posture** — 263 `NO_923_SERIES` plants on 2024 water (255 backfilled in the budget,
   38,219 GWh); `eia923_incomplete`; the EIA-930 monthly repin REFUSED (rule 14).
7. **VOLL $2,000 interim** — and it binds: 23 + 34 NWPP-SNV zone-hours.
8. **NW↔OR Tier-3 placeholder** (43,600 MW, non-binding); lever NWPP-55.
9. **Colstrip and Centralia file no EIA-923 fuel price** (26.7 % of coal MW).
10. **The served interchange is a footprint scalar spread by load share**, on two reporting bases
    — and §3.5 above measures what it costs: −7.1 / −9.7 / −10.0 TWh of energy balance.

## 6. Gates run in the parent

- `check_registry_payload_parity.py` — **RED, not this lane's**: two unmapped bundle dirs,
  `results/calibration/caiso279_ablate_dswcouple_span` and `results/calibration/soco15_spp_arm`,
  both committed on `origin/main` (34 files each) by other lanes. `nwpp40_span_A` maps to its
  sidecar and is clean. Nothing deleted (rule 31; charter).
- `check_mechanism_matrix.py` — 0 NWPP warnings after the stamp (the anchor-drift and NYISO keeper
  warnings it prints are pre-existing and other lanes').
- `tests/unit/pipeline/test_hydro_cascade_cli_flag.py` — 5 passed against the patched runner.

## 7. Routed to the next NWPP lane (calibration tuning for the rubric failures) — NOT fixed here

1. **C1 coal taxonomy seam (the scorer's largest row).** Model coal is labelled `COAL`; the bench
   itemizes `COAL_PRB` / `COAL_BIT` / `COAL_WC`. Either the NWPP fleet path assigns the per-plant
   coal fuel class (the EIA-860/923 fuel code is on the fleet rows the legacy binner reads) or the
   benchmark rolls up to the family for a legacy-bin ISO — a structural alignment question for the
   desk, not a tuning one. Until it is closed C1 cannot pass for NWPP whatever coal does.
2. **Coal hourly shape (C4 + D-1).** Coal runs flat (off-peak CV 0.003–0.006 vs measured
   0.030–0.084). Candidates from the lever queue, per-ISO by rule 25: coal must-run / min-load
   physics on the NWPP coal fleet (Colstrip, Jim Bridger, Hunter/Huntington, Centralia-class units),
   the two no-price plants' supply-class trajectory (§5 line 9), coal unit outages.
3. **CO2 −55 to −66 %** — emission-rate coverage on the NWPP fleet (which plants carry CEMS rates,
   which fall to defaults, footprint plants outside the model).
4. **Energy-balance gap −7 to −10 TWh/yr** — the served-interchange construction vs the
   benchmark's `Total interchange` (§3.5; card N4's priced seams stay default-off).
5. **Chief Joseph 2025 coupling row binding 5,808 h at −325.17** — the first cascade-specific
   question; a per-month look at GCL outflow vs CHJ budget + turbine capacity in 2025.
6. **NWPP-SNV VOLL hours** (23 + 34) — EAST↔SNV 600/580 and INLAND↔SNV 500/360 MW tiers against
   NEVP's summer peak; a WECC path-rating question (card N5), never a VOLL change.
7. Runner nit (not a solve input): per-year cache keys are not recorded in the bundle.

## 8. Retrievability and shard hygiene (rules 33 / 34)

Shard B `session_01MFciPYgGSZcAsqp8UKDxs7` archived after fetch + checkout + verify; its two
keep-alive routines deleted. Branches left in place (deletion returns 403 here, rule 33(f)(5), and
`claude/nwpp-40-span-b` carries the only full copy of the bundle until the owner rules):
`claude/nwpp-40-span-b` @ `fe09a98e72efe473b4e5f1a3ea0ecbedd9178f0a` (bundle + shard report),
`claude/nwpp-40-span-a` @ `4e218d0f01d603c1f14b6866a2486a80dc896ead` (shard A stop report),
`claude/nwpp-40-span-a-diag2023` @ `20807883399c9069f13ebf59be6e473e55ad3579` (shard A's 2023
diagnostic record). Shard A's session was archived earlier in the lane.

## Log entry

## NWPP-40 — 2026-09-16 — FIRST NWPP SOLVE 2023–2025, cascade ARMED — registered `2026-09-16-nwpp-1-cascade` — NOT-YET (C1 taxonomy seam + C4 coal shape; price UNSCORED) — promotion question OPEN

One shard, one invocation, 551 min, peak 4.35 GiB. C2 / C6 / C8 PASS; C1 FAIL on the COAL-vs-
COAL_PRB/BIT class seam (coal family in band); C4 FAIL on coal hourly shape (r 0.48–0.54). Pool-
region EIA-930 benchmark wired into the runner's frame builder (scripts only). Bundle retrievable at
`fe09a98e` with zero re-solves. Nothing deleted. Lane recommends promote; the ruling is the owner's.
