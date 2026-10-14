# PRECOMMIT — UC-3-SPP: clean relaunch of both SPP UC arms (A: floors kept · B: floors off) at the clean engine, every SPP backcast year, 2026-10-14

> **STATUS: LAUNCHED at the uc-1.5 pin (Addendum A).** The first draft was staged at the charter pin `580c4fbf` and held by UC-DESK (11:38Z) for defect 7. UC-DESK sent the pin `2dd69d5a…` at 12:46Z, and §6 was applied before any number existed.

**Written and pushed before any shard of this lane exists.** Every reading, bar, kill and budget below is fixed here and fails
closed. Nothing moves after a number comes in (GATESPEC §7.1; rule 1(c) by analogy). Lane `UC-3-SPP` (session
`session_01CjZHqjM9ardXPg9RSYzrzt`, Opus), branch `claude/ucmilp-3-spp-ab` off `580c4fbf80b8bf970bc19acf14f614728de9d401`.
Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on **the owner's ruling of 2026-10-14, verbatim *"Go with your
recommendations"***, decision 7: relaunch every UC-2 ISO at uc-1.4, with SPP's prior R **held, not recorded**. The ruling is
recorded on `main` in `docs/uc-milp-program-plan-2026-10.md` §11 r09 and in the §12 register (commit `05e3164a`, PR #7240).

**Why a relaunch, not a re-test (rule 28).** Both prior SPP arms solved on engine uc-1.1, before four fixes and one ruling. Two
of the five are relevant to SPP:
- **Defect 6** (uc-1.3 #7237, uc-1.4 #7238): the cluster floor was spread pro rata over a plant's offer tranches, which forced
  `_peak*` tranches on. SPP's integer clusters are per-plant tranche sets of 3–12 members
  (`FINDING-ucmilp-fix4-floor-merit-2026-10-10.md` §1), so they carried the defect.
- **Ruling (a)** (uc-1.2): a cluster whose members are all budget-pinned carries no integer.

Defects 3 (time-major TTC slice) and 4 (NYISO link band) are inert for SPP. Defect 5 (the min-down guard read the unpinned fleet)
was not observed in SPP but was fixed after the SPP legs. Rule 1 [R-STRUCT]: an R verdict confounded by an engine defect is not a
structural rejection. Same config, clean engine: this lane re-enters the `unit_commitment_milp` × SPP cell. It is not a new lever.

## 0. Preconditions (zero LP, checked at the pin before this file was written)

| check | result |
|---|---|
| keeper designation `frontend/data/backcast/keepers/SPP.json` | `"keeper": "2026-10-03-closeout-spp-nuc-keeper"`, the same keeper as arms A and B |
| control bundle, keeper shard and `iso_configs.py` unchanged since arm A's pin: `git diff --quiet ae224faf 580c4fbf -- results/calibration/closeout_spp_nuc_span frontend/data/backcast/keepers/SPP.json src/market_sim/config/iso_configs.py` | **identical** (exit 0) |
| the UC stage is reachable only through the gate | `pipeline.uc` is imported only under `if getattr(config, "unit_commitment_milp", False)`: `pipeline/solve.py:675`, `runner.py:4175`, `run_calibration_full.py:7481`. No other solve-path importer of `model/uc` |
| `coal_sync_floor_release` (arm B's field, PR #7219) present at the pin | yes: `scenarios.py`, default `False` |

## 1. Pin, control, arms

- **Pin (charter):** `580c4fbf80b8bf970bc19acf14f614728de9d401` (`main`; engine uc-1.4). Shards pin **this branch's head**, whose
  `src/` and `scripts/` tree equals the pin's. `source_revision` is that full 40-char SHA, never a branch. **The pin moves to the
  FIX-5 merge before any launch (§6).**
- **Control (rule 29(b), no control solve):** keeper `2026-10-03-closeout-spp-nuc-keeper`, bundle `results/calibration/closeout_spp_nuc_span`.
  It has seven year-isolated legs, 2019–2025, solved at `8c3ea461…`. Its committed `metrics.json`, `legitimacy_diagnostics.json`
  and `hourly/*` are the control readings, the same as for both prior arms.
- **Prior-arm comparators (read, never re-solved):** arm A uc-1.1 at `docs/records/spp/ucmilp/data/ucmilp_spp_span/`; arm B uc-1.1 at
  `docs/records/spp/ucmilp/data/ucmilp_spp_b_span/`.
- **Arm A (definition unchanged, `PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` §1):** `replay_keeper.py results/calibration/closeout_spp_nuc_span
  --years <y> --set unit_commitment_milp=true`. Both conduct floors (`coal_mustrun_per_plant`, `st_gas_mustrun_per_plant`) stay armed,
  as the keeper arms them (owner ruling R5). Rule-19 substitutions: none needed, because the keeper arms no bridge and no posture.
- **Arm B (model delta unchanged, `PRECOMMIT-ucmilp-spp-b-2026-10-09.md` Addendum C, owner ruling D-5b V2):** `--set unit_commitment_milp=true
  --set st_gas_mustrun_per_plant=false --set coal_sync_floor_release=true`.
- **Solver settings, ONE declared choice for both arms (accepted by UC-DESK, 2026-10-14 11:45Z): the pin's registered defaults** (`uc_solver_preset="lean"`, `uc_slim_window=true`).
  Arm B's prior fourth `--set uc_solver_preset="highs_default"` was declared (its Addendum C) as *"the declared solver choice … not a model
  delta"*, made **so that arm B matched arm A's solver path**. At this pin the rationale points the other way. Arm A's definition is
  "`uc_*` at declared defaults", which now means `lean` + slim. A/B parity therefore means both arms at the defaults, so the fourth `--set`
  is dropped.
  - Both settings change the MILP's path, not its feasible set or optimum. FINDING-ucmilp-speed §3: paired equivalence passed on 62/62
    windows, with the largest relative objective delta 8.9e-4. FINDING-ucmilp-slim: the slim window is an exact reduction, and its paired
    gate passed with 0/62 windows differing.
  - The sibling lane UC-3-ERCOT solves at the same defaults (`PRECOMMIT-ucmilp3-ercot-ab-2026-10-14.md` §1).
  - Cost, stated: arm B's uc-1.1 wall rows (highs_default, full window) are not like-for-like with this lane's.
- Every other `uc_*` field stays at its declared default and is never swept: window/look-ahead 24/12, `uc_mip_rel_gap` 1e-3,
  `uc_window_time_limit_s` 600, scope `physics`, no-load source `campd_regression`, boundary `p0_targets`, `uc_prefixing=false`.
  Pricing (R3: markup zeroed on integer clusters, make-whole in the sidecar, never in the LMP) and rule 20 (R4: MECH 28 reported,
  not budgeted) are unchanged. The keeper's authorized price tuning (`offer_curve_by_group`, all bands 0.93) rides unchanged.
- **DOF (rule 21):** zero free parameters are added. No offer band, floor share or `uc_*` value is touched (rule 1).

### 1.1 G-DRIFT (zero LP; every hunk on the backcast path)

The prior pins' drift is already classified: `ae224faf → 6cf95135` in arm B §8, and `6cf95135 → 9cb0eecb` in arm B Addendum C. Both were
INERT for the control; on the arm, only UC-SPEED's preset path was LIVE. **New here: `9cb0eecb → 580c4fbf`** (83 commits). Outside `docs/`,
`tests/` and `results/{bench,phase0}`, 17 paths change:

| file(s) | hunk | control (gate off) | arms (gate on) |
|---|---|---|---|
| `model/uc/{window,solve,schedule,params,diagnose}.py`, `pipeline/uc.py` | uc-1.2 defect 5 (min-down guard on the pinned window fleet, #7230) + ruling (a) (all-budget-pinned clusters carry no integer); uc-1.3 merit-order cluster-floor fill + pass-2 reuse by input digest (#7237); uc-1.4 P1 floor = row (b) `mlf·p̄·a·u` (#7238); per-window log | **INERT**: gated import (§0 row 3) | **LIVE**, intended (the release) |
| `model/uc/slim.py` (new, 666 lines), `scenarios.py` +23 (`uc_slim_window: bool = True`, in `_CACHE_KEY_OPTIONAL_FIELDS` at `"True"`, `TIER_TAGS` 1) | UC-SLIM (#7222): exact reduction of the window MILP | **INERT**: read only inside the UC stage; at its default it drops out of `cache_key()` | **LIVE on the solver path**, exact (§1) |
| `model/uc/uplift.py` −117 | `uplift_from_bundle` deleted; make-whole priced in-process at `mc_base` only | INERT | reporting only; never in the LMP |
| `data/campd_crosswalk.py` +91 (`load_crosswalk`, `camd_to_eia_plant`), `scripts/lib/uc_params/{__init__,ercot}.py`, `scripts/lib/clean_profiles.py` (`uc-params` raw inputs + crosswalk, PUDL) | FIX-3 (#7229): uc-params keyed by EIA plant code, not the CEMS facility id | **INERT**: `campd_crosswalk`'s only importer is `scripts/lib/uc_params` (grep at the pin); the `uc-params` datatype is read only by `model/uc/params.py` | **LIVE**: SPP's no-load / start-cost fit coverage can change (uc-1.1: `uc-params` on 122–123 clusters, class fallback on 86–103). Reported in S4, not judged |
| `scripts/probes/_ucmilp_compose_span.py` | no longer recomputes uplift from the bundle | not on the solve path | composer only (§5) |
| `scripts/lib/uc_bench.py`, `scripts/diagnostics/bench_uc_ladder.py` | bench harness | not on the solve path | not used |
| `.gitignore` +8 | other lanes' leg directories | — | — |

No `constants.py`, `iso_configs.py`, `model/lp/*`, fleet/offer `data/*` or orchestrator hunk. **The control is INERT**, so the keeper
bundle remains the control and no control solve is owed. Every arm-vs-control delta is UC-stage-only, plus the two declared solver-path
settings.

## 2. Readings (inherited, same bars; plus the charter's per-year table)

- **Targets T1–T5** (arm A §2, unchanged). T1: 2020 C3a, control +27.7 %, bar ≤ +18.85 %. T2: 2019 C3a, +12.3 %, bar ≤ +11.15 %.
  T3: 2020 C3b, 0.345, bar ≤ 0.2725. T4: M3 low-price-hour ratios (2019, 2020), sign only. T5: M4 reserve dormancy, sign only.
  The 2024 C3a/C3b cost row is reported beside them.
- **Control readings** (arm A §3 / arm B §3, unchanged): no PASS → FAIL flip vs the keeper on any year, criterion or class row. The
  tight rows are the ones named there. Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year; no new
  D-4 FAIL row. For arm B, the absence of the control's seven `st_gas_mustrun_per_plant` D-4 FAIL rows is expected and is not a reading.
- **Hypothesis readings H1–H4** (arm B §4, unchanged instrument and bars). They are read for arm B against the new arm A, which makes
  them the clean stacking test. They are also reported against the uc-1.1 arm A.
- **Structure / cost** (arm A §§4–5, arm B §5): S1 MECH 28 share, S2 starts vs CEMS (M1), S3 is skipped (the SPP portal comparator
  is still not on disk), S4 integer set and fallback shares, W1 wall vs the ruled 3× ceiling (a cost finding, never a defeat),
  W2 time-limit hits ≤ 3/365, W3 uplift ≤ 2 %, W4 infeasible windows = 0.
- **Charter table, per year, control → arm A → arm B** (the RESULT's first table):
  - C1, C3a, C3b, C3c and C4 status and value;
  - C8 as scored, and with MECH 28 removed (R4);
  - unserved MWh;
  - uplift % (Σ `uplift_usd` ÷ Σ λ_P1·load);
  - CC_REGULAR / ST_GAS / COAL_PRB / COAL_LIGNITE starts vs CEMS (M1);
  - **forced peak-tranche TWh**: P1 energy on `_peak*` tranches in hours where the merit fill placed a UC floor on them. Expected
    ≈ 0 at uc-1.4. **Any year above 0.1 TWh is reported to UC-DESK as a defect-6 recurrence**;
  - wall ÷ (P0+P1), using the declared proxy of the shard's own `solve_p0 + solve_p1`;
  - integer clusters / gate set (clusters), and how many lost their integer under ruling (a);
  - time-limit hits.
- **Price-move diagnosis (zero LP, from the bundles; descriptive, never tuned on).** It runs for every year and arm with |ΔC3a| > 2 pp
  or |ΔC3b| > 0.02 vs the control:
  1. Δ mean LMP by hour class: actual-price terciles, actual ≤ $15, the top-100 actual hours, and on-peak (HE07–22 weekdays) vs
     off-peak.
  2. In each class, the marginal mix: `unit_marginal` rows with `marginal == 1`, by plant class and offer band.
  3. Online-MW delta in those hours: `uc_schedule` `online_mw` vs the control's online MW on the 1 %-of-cap convention.
  4. The sign of each piece, attributing the move to one of three causes: (i) a higher tranche or class at the margin after
     decommitment; (ii) a lost near-min-load body in the trough; (iii) a reserve-dual change.

## 3. Kills (GATESPEC §5, as applied in both prior PRECOMMITs; unchanged)

1. **An infeasible window** (`windows[].status`, or the engine's "no incumbent" hard stop): an engine defect. That leg stops. Its
   window index, hours and traceback go to UC-DESK with a repro. This lane patches no `src/`.
2. **A non-deterministic schedule**: the `uc_schedule_<y>.parquet` hash differs between two completed runs of the same arm-year. It is
   exercised only if a relaunched leg and its predecessor both complete; otherwise it is reported as "not exercised".
3. **A control flip** (§2) vs the keeper, in any year.

The legs of an arm run in parallel and independently, so a kill is recorded when it is read. Kill #1 stops its own leg and does not
cancel legs that are already running. Kills #2 and #3 are read at composition, after every leg has landed. A fired kill fixes that
arm's verdict at R. Every year is still scored and reported. Nothing is re-tuned, and no further arm is run.

## 4. Verdict rule (unchanged; each arm gets its own verdict)

- **K candidate**: T1, T2 and T3 met, T4/T5 signs right, no kill, every leg Optimal (for arm B, also H1–H3 met). The lane then
  recommends that the owner's D-6 card read "promote on structure". The lane never promotes (rule 31).
- **R**: any target moves the wrong way past its control (2019 or 2020 C3a up, 2020 C3b up), or any kill fires.
- **I**: no kill, no wrong-sign move, and |Δ| below the bar on T1–T3.
- **Mixed**: the worst of the three target rows, stated row by row. The RESULT names the rule-1 reading separately: is the
  remaining gap engine, calibration, or structural?
- The matrix cell `unit_commitment_milp` × SPP is stamped from the RESULT, with both arms' verdicts and the citation.

## 5. Solve plan (rules 16, 32–36)

- **14 shards**: arms {A, B} × 2019–2025, one year each, solved alone (rule 36). Out-dirs are `results/calibration/ucmilp3_spp_{a,b}_<y>`
  and branches `claude/ucmilp3-spp-{a,b}-<y>`. Prompts come from `scripts/shard_prompt.py --iso SPP --year <y> --sha <branch head>
  --lane ucmilp3-spp-{a,b} --bundle results/calibration/closeout_spp_nuc_span --set … --budget 720`, plus the lane appendix:
  - confirm in the pushed tree `hourly/uc_schedule_<y>.parquet`, `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json` and
    `hourly/unit_marginal_<y>.parquet`, with `dispatch/<y>_P1.parquet` (rule 34);
  - paste the arm's field values from `run_config.json`, the recorded `uc_solver_preset` / `uc_slim_window` and engine version, and
    (arm B) the count of `coal_mustrun` / `st_gas_mustrun_per_plant` floor rows (expected 0);
  - paste the GATESPEC §6.1 wall row;
  - **split any file over 100 MB into ≤ 95 MB parts** (`split -b 95M`), with the original's and each part's sha256 in
    `<out-dir>/SPLIT_SHA256SUMS`, and keep the original unstaged.

  Prompts are committed as `shard-prompts-ucmilp3-spp.txt` (staged; regenerated at the FIX-5 pin, §6).
- **Budget: 720 min of LP wall per shard** (the protocol cap; UC-DESK 2026-10-14 11:45Z, before any number: *"Raise the per-shard budget to the protocol's 720 min: SPP has run 5–7× P0+P1, and a 180-min budget risks budget stops"*; this file's first draft read 180). For reference, arm B at uc-1.1 (highs_default, full window) ran 39–67 min end to end. A shard at the budget with no bundle stops and reports, and that is a cost finding, not a kill. One shard commit is ≤ 20 min of runtime (rule 32). A shard PENDING for more than 45 min is archived and relaunched.
- **Each leg:** fetch; check that `git ls-tree -r <sha> -- <out-dir>` is non-empty; check out; verify the P1 dispatch, the three UC
  files and `unit_marginal`; then archive (rule 33).
- **Compose and score in the parent (zero LP).** `_ucmilp_compose_span.py` at the pin still lacks per-year `gas_price_override` and
  `_respan_shared_inputs`. The lane therefore applies the **same scratch-copy workaround as both prior arms** (arm A Addendum D):
  1. add `gas_price_override` to `PER_YEAR_FIELDS`;
  2. respan `meta.json` with the keeper composer's function, so the frames resolve to the keeper's own hashes;
  3. verify with `--restore-shared-inputs`.

  No repo script is edited, and the workaround is disclosed in the RESULT. The output is `results/calibration/ucmilp3_spp_{a,b}_span`.
  Then: `calibration_verdict.py`, regenerated `legitimacy_diagnostics.json`, `screen_year` M1/M3/M4, the flip diff, R4, H1–H4 and the
  §2 diagnosis. C3c CAVEAT → FAIL in an unattested probe is the known attestation artefact and is compared on magnitude.
- **No registration** (E13: keeper-only), no promotion, nothing deleted (rule 31). Slim spans go under
  `docs/records/spp/ucmilp/data/ucmilp3_spp_{a,b}_span/`: metrics, diagnostics, configs, meta, UC logs and the `hourly/` sidecars,
  never `dispatch/`. The RESULT goes beside this file. The SPP matrix cell is stamped. One PR to `main`, not merged (UC-DESK merges).

## 6. Pin-move rule (fixed now, before any number)

When UC-DESK sends the FIX-5 pin:
1. Merge it into this branch (no rebase).
2. Append Addendum A with the G-DRIFT `580c4fbf → <pin>`. Any hunk outside the UC stage on the backcast path is classified
   INERT/LIVE for the control. A LIVE control hunk stops the lane and goes to UC-DESK, because the keeper would no longer be the control.
3. Regenerate the 14 prompts at the new branch head, push them, verify the blobs, then launch.

Readings, bars, kills, verdict rule, arms, solver declaration and budget are UNCHANGED by a pin move. A defect that fires after
launch is handled the same way, under kill #1.

## 7. DO NOT REDO

`docs/mechanism-testing-matrix.md` §5.7's DO-NOT-REDO list (curtailment ceiling, gas bridge, offer-band retunes). `spp_commitment_posture`
(R) is not re-run in any form. No `uc_*` value other than the declared defaults. No `--set` beyond each arm's list. No control
solve. No re-solve of a uc-1.1 leg for comparison. No sweep of which floor to remove.

## Addendum A (2026-10-14, before any number exists) — the uc-1.5 pin, G-DRIFT `580c4fbf → 2dd69d5a`

**Pin: `2dd69d5aa936547b402a1ba54d2eba57e759b7e7`** = `main` at the merge of PR #7246 (UC-1-FIX-5, engine `UC_ENGINE_VERSION = "uc-1.5"`:
defect 7 fixed, the UC cost basis pays no-load once). UC-DESK (12:46Z): *"the uc-1.5 pin is 2dd69d5a… Go: run your §6 pin-move rule …
then launch arms A and B."* The pin was merged into this branch with no rebase (`7575ba7a`). The branch tree equals the pin's apart from
this file and the prompts (`git diff --name-only 2dd69d5a HEAD` lists only those two). Shards pin the branch head after this addendum.

**G-DRIFT (zero LP).** 7 commits. Outside `docs/` and `tests/`, 6 paths change:

| file(s) | hunk | control (gate off) | arms (gate on) |
|---|---|---|---|
| `model/uc/params.py` +44, `model/uc/uplift.py` ±23, `pipeline/uc.py` ±16 | uc-1.5: integer clusters' UC energy and the uplift cost side priced on a basis that excludes the no-load heat already paid by `noload` (defect 7) | **INERT**: `pipeline/solve.py`, `runner.py` and `run_calibration_full.py` are unchanged, so the import is still gated (§0 row 3) | **LIVE**, intended (the release) |
| `scripts/lib/uc_bench.py` ±3 | bench harness | not on the solve path | not used |
| `scripts/data/derive_ercot_sced_uc_bands.py` (new), `data/raw/_validation-source/ercot_sced_uc_bands.json` (new) | UC-BANDS-ERCOT phase 1a (#7242), zero-LP evidence | **INERT**: no `src/` or `scripts/` importer or reader (`git grep` at the pin); ERCOT-only validation source | not read |

Records-only commits: desk r09 (#7240), UC-BANDS-ERCOT phase 0 (#7241), UC-3-CAISO/NEISO/NYISO RESULTs (#7243–#7245). No `constants.py`,
`iso_configs.py`, `scenarios.py`, `model/lp/*`, fleet/offer `data/*` or orchestrator hunk. `results/calibration/closeout_spp_nuc_span/**` and
`keepers/SPP.json` are not touched. **The control is INERT, so the keeper bundle remains the control.** Arms, readings, bars, kills, verdict
rule, solver declaration (lean + slim) and the 720-min budget are UNCHANGED. The 14 prompts are regenerated at this branch head.

## Addendum B (2026-10-14 12:48–12:52Z, before any number exists) — launch record

Addendum A was pushed as `ca0acb24` (and the prompts as `b3af1fc7`; PRECOMMIT 203 lines and prompts 507 lines, both blob-verified) **before** any shard.
14 shards were launched at `ca0acb249fc61485982c1a0264fe52e9344254a1`, model `claude-opus-5-5`, tag `ucmilp:UC-3-SPP-shard`, budget 720 min:

| year | arm A (floors kept) | arm B (floors off) |
|---|---|---|
| 2019 | `session_016JRaeUkeeGq6z84NoCtsWd` | `session_01Y8uj8JU7N57fPtkbL33G91` |
| 2020 | `session_01CpvB2qbHznhFYj8NWuF8Yk` | `session_01RSZqvjg4miQvSudYmxbvKq` |
| 2021 | `session_01XpYakgUBjGXPwcrQs22Frn` | `session_01Dr9hepsAe2Rin49BGGr8ca` |
| 2022 | `session_01QzkT6SRX5pPcanu1oBUbso` | `session_012Eh7PCtyaA7BUAdZQXqQir` |
| 2023 | `session_01Rirmg2uuNT2s3iX4SVP2Pa` | `session_01JFncMWzTgMRV4agp1hBQs6` |
| 2024 | `session_0191BgT1JL6ABsLvZEiQMzDk` | `session_0112GaACCNyjGszpy9Nza4dm` |
| 2025 | `session_01FVzQa1tnKCVju9dkTEaqUn` | `session_01P5PJ4odpkcMonNDKeT3HJw` |

Branches: `claude/ucmilp3-spp-{a,b}-<y>`. Out-dirs: `results/calibration/ucmilp3_spp_{a,b}_<y>`.
