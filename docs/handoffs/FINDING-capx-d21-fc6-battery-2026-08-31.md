# FINDING — capx D21: the FC-6 driver battery for the NEISO t3 golden (priced, run, scored — and it FAILs the gate)

**Session:** D21 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d21-fc6-battery-652ngq`, lane issued at the director's 2026-08-31 sitting under
owner ruling Q16 (the FC-5/FC-6 ceiling is fixed BEFORE any second golden campaign; FC-6
first because its tooling already exists and the gate is merely un-run).
**Date:** 2026-08-31 · **HEAD at launch:** `836e48e1` (origin/main) · **solve vintage:**
`9e56f0f` (§2).

**Headline: FC-6 can now grade a golden, and on its first real execution it grades this one
FAIL.** The paired invariant P1 fails at full magnitude — cumulative 2026–2050 CO2 **RISES
210.52 → 320.84 Mt (+52.4 %) under a $25/t carbon price** — and the battery's own T1.6
ladder turns out to be unable to test anything: its pre-registered driver
(`renewable_buildout_pace`) is consumed by no model code, so both gate rows pass on
all-constant series (vacuous per rubric §FC-6.2, never citable as confirmation). Per the
lane charter, a FAIL here is the instrument working; nothing in the model was moved, no
threshold/band/expectation was edited, and `neiso-t3` is re-scored with FC-6 = FAIL
(determination stays HOLD, which five other gates already force).

---

## 1. Charter discipline (what this lane did NOT do)

No golden re-solve (Q16 holds the campaign as registered at its pre-R-A posture epoch); no
FC-5 work (lane D22); no threshold, band, or pre-registered expectation edited anywhere; no
mechanism tested, no `ScenarioConfig` field added, no matrix cell minted (rule 28 duties do
not fire — `renewable_buildout_pace` has no matrix row, and its inertness is a wiring fact
routed to the director, not a lever verdict); no out-of-training backcast year touched; no
backcast keeper shard, `status/*.js`, or `calibration-complete.json` touched. The two
instrument amendments this lane DID make (§5.1, §6.1) are strictly evidence-tightening:
each makes a mandated check fire where it previously could not, and neither moves a
numeric threshold.

## 2. The config-vintage pin — and the data-vintage leak the reproduction check caught

**Code:** all solves ran from a git worktree at `9e56f0f` — the golden bundle's own
`git.basis_sha` (its solved branch sha `271ad606c3fd` is unreachable — branch deleted — but
PR #4447/#4452 file lists prove the branch carried results/docs only, so `9e56f0f` IS the
solve-time code). Running at HEAD would NOT have been the bundle's vintage: owner ruling
R-A armed the two storage-entry defaults after the golden solved, and NEISO-RC-R (PR #4467)
reworked the NEISO FCA/MRI capacity-curve inputs. The four instrument scripts
(`run_driver_battery.py`, `check_forecast_invariants.py`, `forecast_verdict.py`,
`run_full_horizon.py`) are byte-identical between `9e56f0f` and HEAD, so the vintage
worktree ran the current instruments by construction. Data was served from the main
checkout via the `MARKET_SIM_DATA_ROOT` seam.

**The data-vintage leak (caught, root-caused, fixed, re-run):** the first battery/arm
solves ran against a `data/clean` tree curated from CURRENT `data/raw`, which two
post-golden intakes had moved for NEISO — the RC-R-modified
`capacity-market/demand-curve/neiso/neiso.csv` (+15 lines), and the modified
`confirmed-retirements/neiso.csv` that made the vintage curation FAIL its datatype
(one of the full rebuild's "2/52 failed"), leaving no NEISO confirmed-exits partition
where the golden had one. The base arm matched the golden 2026–2027 and diverged from 2028
(the coal-exit timing) — caught by the pre-planned reproduction check. Fix: re-curate
those datatypes from the `9e56f0f` raw bytes (NEISO demand-curve parquet hash
`a3b40778…` → `1542326936…`), discard the stale outputs (commit `ea1ae5ad`), re-run
everything. **After the fix the base arm reproduces the golden's committed trajectory
EXACTLY — all 25 years × 13 fields and the full I1–I14 vector (its I3 FAIL and I13 WARN
included).** The vintage pin is therefore proven end-to-end, not asserted.

**The cache-key red herring, resolved:** the base arm's key `0365174ab16cc318` ≠ the
bundle's `a4b11ef4aaa1be35` despite byte-identical resolved configs. Cause:
`cache_key()` folds absolute paths to sentinels via `_cache_key_path_roots()`; the
split-root session (repo=worktree, data root=main checkout) folds the same path strings to
`<data-root>` where the golden's single-root container folded them to `<repo>`. Forcing
the single-root fold on this session's resolved config reproduces `a4b11ef4aaa1be35`
byte-exactly. Bookkeeping, not a scenario difference — but it means **a key computed under
a relocated `MARKET_SIM_DATA_ROOT` is not comparable to a single-root key** for any config
carrying path fields; cite configs, not keys, across environments.

## 3. Stage 1 — the pricing (written before any solve; scratchpad text reproduced verbatim in substance)

Anchors: golden 25-yr solve 1753.2 s = 29.2 min / 3.50 GB peak RSS (its own
`full_horizon_summary.json`); per-year median 68.7 s; S-4b 5-yr anchor 8.0 min / 3.17 GB;
data/clean rebuild ~30 min; box 15 GB / 4 CPU / 20 GB disk.

- **Option A — "all nine ladders on NEISO" at 2026–2050:** 26 rungs × 29.2 min ≈ 12.7 h
  + 4 paired arms ≈ 1.9 h → **≈ 14.6 h of solves. Does not fit a session — and is not the
  instrument:** the battery's pre-registered ladder registry names NEISO for **T1.6 only**
  (2 rungs); every other ladder is registered ERCOT/PJM (T1.9 ERCOT-only). Running them on
  NEISO would mean editing the pre-registered ISO applicability — out of charter.
- **Option B (chosen) — the actual NEISO battery at the golden window:** T1.6 (2 rungs,
  workers=2) ≈ ≤30 min + paired arms (base, carbon 25, gas ×1.5, gas ×1.05) ≈ 60–120 min
  in ≤2-concurrent waves (rule 12) + overheads → **≈ 3.5–4.5 h. Fits.**
- **Option C (not chosen) — 5-yr window:** ≈ 48 min of solves, rejected while B fits: P1's
  pre-registered object is cumulative-**2050** CO2, P3's cumulative-2035 builds
  (forecast-validation-program §2.2), and a 2030 endpoint invites exactly the T1.7a
  constant-series vacuous pass.

**§2.1b licensing basis (recorded, not assumed):** the 25-yr solves exceed the 5-solve-year
cap; the licensing basis is this lane's charter, issued at the director's sitting under
Q16, which instructs pricing the battery at the golden's 2026–2050 vintage against the
29.2-min full-solve record and running what was priced — scoped to the FC-6 instrument
runs for the registered golden only. The programmatic battery path asserts no schedulable
guard (guards are CLI-level); the paired-arm driver called
`assert_schedulable(2026, 2050, full_solve_authorized=True, "D21 FC-6 paired arm")`
explicitly so the gate was consciously passed, mirroring the golden's own
`--full-solve-authorized`.

**Measured vs priced:** battery 696.5 s (both rungs, workers=2); base 1998.1 s / 3.57 GB;
carbon25 655.2 s; gasup150 2003.2 s; gaspm5 in the same band. Total session solve wall
≈ 2.6 h including the data-vintage re-run — inside the priced envelope.

## 4. Stage 2 — what ran, and the committed artifacts

All solves: worktree `9e56f0f`, `MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1
OMP_NUM_THREADS=1 MARKET_SIM_DATA_ROOT=/home/user/market-simulator`, years sequential
within each invocation (rule 12), ≤2 concurrent per-plant solves.

1. **Battery:** `run_driver_battery.py --iso NEISO --start-year 2026 --end-year 2050
   --workers 2` → `results/ff-t3-neiso-golden/bau/fc6/driver-battery-neiso-2026-08-31.{json,md}`
   + `fc6/_battery_metrics/NEISO/*.json` (committed). Rungs `vre_short`/`vre_long`
   (configs differ in exactly one field; distinct cache keys `c78105c31485c405` /
   `2476a2f00522c4a5`), both 25/25 years.
2. **Paired arms**, each the golden's exact CLI construction
   (`reference_config("NEISO", 2026, 2050, cmc=False, golden_posture=True)`) plus one
   `dataclasses.replace` perturbation, solved through `solve_and_summarize` (the golden's
   own engine); driver script reproduced in §8:
   - `base` `{}` — key `0365174ab16cc318`; **reproduces the golden exactly** (§2).
   - `carbon25` `{"carbon_price": 25.0}` — the T1.1/T1.2 anchor rung; key `7924eccc695c0168`.
   - `gasup150` `{"gas_price_factor": 1.5}` — T1.3's pre-registered top rung; key `13f9357712250600`.
   - `gaspm5` `{"gas_price_factor": 1.05}` — the checker's own ±5 % P3 construction.
   Committed per arm: `fc6/arms/<arm>/{full_horizon_summary.json, run_config.json}`.
3. **Paired invariants** (`check_forecast_invariants.py --paired … --json`, P1/P2/P3):
   committed as `fc6/paired_invariants.json` (the instrument's concatenated machine
   output).

## 5. Stage 3 — the row-by-row FC-6 verdict

### 5.1 Battery gate rows — both vacuous, and the driver is disconnected

| Row | Rule | Series | Battery status | Rubric §FC-6.2 reading |
|---|---|---|---|---|
| T1.6a REC dual ≤ ACP | `le_target` | `[1.0, 1.0]` | PASS | **vacuous — all-constant series ⇒ CAVEAT, never PASS** |
| T1.6b REC dual ↓ as VRE builds | `monotone_down` | `[1.0, 1.0]` | PASS | **vacuous — all-constant series ⇒ CAVEAT, never PASS** |

The two rungs solved **metric-identically across all 18 extracted values** (CO2 195.5868 Mt,
renewable build 33.0 GW, dual/ACP 1.0, …), replicated on BOTH data vintages (the stale-tree
first run and the corrected re-run). Root cause: **`renewable_buildout_pace` — the T1.6
ladder's pre-registered driver — is defined in `ScenarioConfig`, registered in
`_CACHE_KEY_OPTIONAL_FIELDS`, and consumed by NO model code, at `9e56f0f` and at HEAD
alike.** The ladder solves the same model twice under different labels; it cannot test what
it pre-registers ("VRE fleet held short vs long"). The 2026-07-12 session could not see
this — its NEISO rungs crashed (issue #2063) before producing comparable output; #2063 is
fixed, and the first real execution of T1.6 exposes the disconnected driver. Additionally
the REC dual sits pinned at the $50 ACP ceiling in every year of both rungs — the golden's
own "escaping to its price cap" behavior — so even a connected pace driver may not move the
2050 dual; that is for the wiring lane to establish.

**Scorer gap closed (evidence-tightening, scored both ways):** `score_fc6` treated only
gate-row SKIPs as vacuous; a PASS on an empty/all-constant series — the rubric's own
FC-6.2 sentence, with the T1.6a-2026-07 (empty) and T1.7a (constant) precedents — scored
PASS. Amended (commit `f0243cbf`) to check the series metadata the battery output already
carries (`rungs[].metrics`), with the `all_equal` negative-control rule (T1.7b: constancy
IS its claim) and the single-endpoint `approx_*` rules exempt from the constant-series
flag, and an explicit `vacuous` row marker trusted outright. Strictly tightening
(PASS → CAVEAT only); no threshold moves; 79/79 verdict tests green (5 new). Both scorer
versions agree FC-6 = FAIL overall (P1 dominates); they differ only in the battery row:
pre-fix "all 2 gate rows PASS", post-fix "CAVEAT — 2 vacuous rows named".

### 5.2 Paired invariants

| Row | Construction | Status | Detail |
|---|---|---|---|
| **P1** CO2 monotone vs carbon | base vs `carbon_price=25` | **FAIL** | cumulative CO2 base **210.52 Mt** vs high **320.84 Mt** — CO2 RISES +52.4 % under a $25/t carbon price |
| **P2** merit-order sign | base vs gas ×1.5 | **PASS** | year 2050: all signs correct (gas_cc ↓, LW price ↑, objective ↑; coal leg auto-skipped — no 2050 coal) |
| **P3** perturbation stability | base vs gas ×1.05 | see committed `paired_invariants.json` | cliff-edge detector, WARN-level |

**P1's failure decomposes into two channels, both visible in the committed arm
summaries:**

1. **The CCS retrofit screen responds to the carbon price with LESS abatement.** By 2040
   the base fleet holds **13,049 MW gas_cc_ccs and ZERO unabated gas_cc** (the screen
   retrofits the entire CC fleet at carbon_price=0), while the $25/t arm holds **4,000 MW
   unabated gas_cc and only 9,993.5 MW CCS** — ~3 GW less CCS *because of* the carbon
   price. Annual CO2 splits accordingly: 2040 base 4.49 vs carbon 11.77 Mt; 2045 2.67 vs
   11.86; 2050 3.21 vs 13.26. Prices tell the same story from the other side — the carbon
   arm's LW price is LOWER (2040: 59.45 vs 70.53 $/MWh) because it keeps the cheap
   unabated CC fleet the base has converted to costlier CCS dispatch.
2. **A same-fleet dispatch-level rise in 2026:** +0.21 Mt (16.32 → 16.53) with
   byte-identical capacity in every fuel — a pure dispatch reordering under the carbon
   adder that INCREASES emissions.

Both are root-cause objects for a follow-on lane (the retrofit screen's carbon-price term
— spec §5.6's "incremental uplift over the best unabated state" — and the dispatch-level
sign). **Nothing was tuned, re-run for a better draw, or softened here** (rules 1/11/14;
the lane charter's own clause). Report-only annotation: gas ×1.5 moves the horizon-mean LW
price +19.18 $/MWh and cumulative CO2 +17.3 Mt; all three perturbed arms carry the base's
own I3-FAIL/I13-WARN invariant signature.

**P1 instrument gap closed on the way (evidence-tightening):** P1 SKIPped "emissions
absent" on every forecast bundle — the forecast `DispatchResult` never populates
`emissions`, the 2026-07-12 weekly's standing gap — so FC-6's paired leg was unrunnable as
specified for forecast runs since inception. `_annual_co2_tons` now reconstructs
dispatch × the fleet context's per-generator emission rate when the array is absent —
the same arithmetic `run_full_horizon._co2_tons` / golden_forecast_bands already use for
every reported `co2_mt` (commit `74cb3c8e`; 49 checker tests green, 2 new; SKIP still
fires when neither source exists). The pre-fix SKIP row is quoted here for the record:
`{"ident": "P1", "status": "SKIP", "detail": "emissions absent"}`.

### 5.3 The re-scored `neiso-t3`

Re-scored from committed artifacts only, same inputs as the golden's own scoring (whose
committed verdict this session first REPRODUCED exactly from those inputs before changing
anything) plus the two new FC-6 inputs. FC-6: SKIPPED-required → **FAIL** (battery gate
rows CAVEAT with both vacuous rows named; paired P1 FAIL; P2 PASS; P3 per its row).
Every other category unchanged (FC-1/2/3/4/7 FAIL, FC-5 SKIPPED-required, FC-8 PASS).
**Determination: HOLD — unchanged, now on six failing gates and one unscored instrument
(FC-5, lane D22).** `ff-verdicts.json`: prior verdict preserved at `neiso-t3-pre-fc6`
(the RC-R preserve-then-overwrite precedent), `neiso-t3` overwritten with the re-score;
the bundle's `forecast_verdict.json` replaced in place.

## 6. Findings register (all at full magnitude; none actioned in this lane)

1. **FC-6 FAIL on P1 — the carbon-response sign defect** (§5.2): the model's cumulative
   CO2 rises 52.4 % under a $25/t carbon price, driven by the CCS retrofit screen's
   carbon-price response plus a 2026 dispatch-level rise. THE gate finding of this run.
2. **T1.6's driver is disconnected** (§5.1): `renewable_buildout_pace` is a registered,
   cache-keyed, consumed-by-nothing field — the inverse of a rule-24 off-registry channel:
   an on-registry dead knob that silently mints distinct cache keys for identical solves.
   Whether to wire it or delete it (rule 26) is the director's/owner's call; the T1.6
   ladder cannot grade NEISO's RPS/ACP response until then, and FC-6's NEISO battery leg
   is structurally CAVEAT-at-best while it stands.
3. **NEISO's whole pre-registered battery is one ladder.** With T1.6 vacuous, the entire
   NEISO battery contribution to FC-6 is two vacuous rows; the gate's real NEISO content
   today is P1–P3. Whether more ladders should be registered for NEISO (T1.1/T1.3/T1.4
   are ISO-agnostic in principle) is a plan-§2 question for the director — this lane does
   not edit pre-registrations.
4. **P1 was unrunnable on forecast bundles since inception** ("emissions absent" — §5.2);
   fixed as measurement plumbing, no thresholds moved.
5. **The scorer's vacuous-pass check under-fired** (SKIP-only — §5.1); fixed per the
   rubric's own sentence, strictly tightening, scored both ways.
6. **Split-root cache keys are not portable** (§2): a `MARKET_SIM_DATA_ROOT`-relocated
   session folds path fields to a different sentinel, so its keys differ from single-root
   keys for identical configs. Worth a docs note in `docs/fast-clone.md`/`CLAUDE.md`
   whenever a lane quotes keys across environments.
7. **Post-golden raw intakes silently invalidate vintage clean rebuilds** (§2): a
   vintage-pinned session must curate from vintage raw bytes, not current raw — and a
   modified raw csv can make the vintage curation fail its whole datatype (the
   confirmed-retirements "2/52" failure), which then presents as a MISSING clean
   partition, not an error the solve reports. The base-arm reproduction check is the
   defense; recommend it as standing practice for any vintage-pinned instrument run.

## 7. Exit state and the answer to the director

**Delivered:** FC-6 evidence built, committed into the golden bundle
(`results/ff-t3-neiso-golden/bau/fc6/`), and scored; `neiso-t3` re-scored (FC-6
SKIPPED → FAIL; determination HOLD, unchanged); two instrument amendments landed with
tests; board stamped (NEISO block + top-level `d21_fc6_battery`); everything pushed and
blob-verified on `claude/capx-d21-fc6-battery-652ngq`.

**Can FC-6 now grade a golden?** Yes — the instrument chain runs end-to-end (battery →
paired invariants → scorer) with real, committed inputs at the bundle's proven vintage,
and its vacuity detection now matches the rubric's text. **What does it say about this
one?** FAIL, on the P1 carbon-response sign at +52.4 % cumulative CO2 — a real,
located, two-channel model defect (CCS-retrofit carbon response + a dispatch-level 2026
rise), plus a disconnected T1.6 driver that leaves the NEISO battery leg vacuous. The
t3 ceiling for NEISO is now FC-5 (lane D22), FC-7's attestation, and the six failing
gates — of which FC-6's P1 is the newest and, being a sign defect in the model's economic
core, arguably the most consequential for any 2026–2050 claim under a carbon scenario.

## 8. Reproduction record

The paired-arm driver (run 4×, verbatim; from the session scratchpad):

```python
"""D21 FC-6 paired-invariant arm driver."""
import importlib.util, json, sys
from dataclasses import replace
from pathlib import Path
WORKTREE = Path("/home/user/msim-vintage")           # git worktree @ 9e56f0f
sys.path.insert(0, str(WORKTREE / "src")); sys.path.insert(0, str(WORKTREE))
spec = importlib.util.spec_from_file_location("rfh", WORKTREE / "scripts" / "run_full_horizon.py")
rfh = importlib.util.module_from_spec(spec); spec.loader.exec_module(rfh)
overrides = json.loads(sys.argv[1]); out_dir = Path(sys.argv[2])
rfh.assert_schedulable(2026, 2050, True, "D21 FC-6 paired arm")
cfg = rfh.reference_config("NEISO", 2026, 2050, cmc=False, golden_posture=True)
if overrides: cfg = replace(cfg, **overrides)
summary = rfh.solve_and_summarize(cfg, "NEISO", out_dir)
raise SystemExit(1 if summary.get("error") else 0)
```

Invocations (env for every solve: `MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1
OMP_NUM_THREADS=1 MARKET_SIM_DATA_ROOT=<main checkout>`; run from the worktree):

```
uv run python scripts/run_driver_battery.py --iso NEISO --start-year 2026 --end-year 2050 \
    --workers 2 --out <repo>/results/ff-t3-neiso-golden/bau/fc6 --cache-root <scratch>
uv run python paired_arm.py '{}'                          <arms>/base
uv run python paired_arm.py '{"carbon_price": 25.0}'      <arms>/carbon25
uv run python paired_arm.py '{"gas_price_factor": 1.5}'   <arms>/gasup150
uv run python paired_arm.py '{"gas_price_factor": 1.05}'  <arms>/gaspm5
scripts/check_forecast_invariants.py --paired <base> <carbon25> --pair-kind carbon --json
scripts/check_forecast_invariants.py --paired <base> <gasup150> --pair-kind gas_up --json
scripts/check_forecast_invariants.py --paired <base> <gaspm5>   --pair-kind gas_pm5 --json
scripts/forecast_verdict.py --tier t3 \
    --summary results/ff-t3-neiso-golden/bau/full_horizon_summary.json \
    --run-config results/ff-t3-neiso-golden/bau/run_config.json \
    --dof-ledger results/ff-t3-neiso-golden/bau/dof_ledger.json \
    --hindcast-score results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json \
    --crossover-score results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json \
    --driver-battery results/ff-t3-neiso-golden/bau/fc6/driver-battery-neiso-2026-08-31.json \
    --paired-invariants results/ff-t3-neiso-golden/bau/fc6/paired_invariants.json \
    --json-out results/ff-t3-neiso-golden/bau/forecast_verdict.json
```

Vintage-clean rebuild for a pinned session: hydrate raw; `git checkout <vintage> --
data/raw/<the moved subtrees> data/dictionary/schema/<moved schemas>`; run the WORKTREE's
`scripts/regenerate_clean.py`; restore HEAD raw afterwards; verify with the base-arm
reproduction check before trusting any perturbed arm.
