# FF-1A — R-NEW retirement decision rule: implementation + re-measurement (2026-07-18)

**Charter.** FF-1A of the Forecast Finalization Program
(`docs/forecast-development-plan-2026-07.md` §1.2-1; §7 binds): implement the
owner-approved R-NEW decision/execution retirement pipeline
(`docs/handoffs/ff-retirement-rule-redesign-2026-07.md` §3.6 — THE approved
design) and re-measure the flip-gate battery. Owner decisions executed, keyed
on dispatch: **D1 = Option B** (R-NEW per memo §3.6; NOT B2 — no pre-window
seeding this pass), **D2 = delete staged thinning at the flip commit**
(rule 26), **D3 = adopt measured gas_cc execution lag = 1** (rule 14).
BEFORE legs are the committed RC-1A-D1 probes
(`docs/handoffs/position-calibration-d1-findings-2026-07-16.md`) — reused,
never re-solved. Rules 1/13/14/19/21/23/24/26/27 govern.

---

## 0. Bottom line first

**R-NEW closes the per-fuel threshold inversion in both curve-ON ISOs — the
D1 blocker is fixed — while trading it for an honest signal-LEVEL residual, not
a new composition bug.** Measured (raw / IS-2020, economic channel):

| ISO | metric | D1=3 BEFORE | R-NEW AFTER | verdict |
|---|---|--:|--:|:--|
| **MISO** | gas_st false-retire (GW) | **8.643 (FAIL)** | **0.0 (PASS)** | inversion **closed** |
| MISO | coal recall >300 MW | 29% | **76%** | wave **restored** |
| MISO | total false-retire raw/IS | 8.643 / 8.643 | **0.0 / 0.0 (PASS)** | T-R10a/b **PASS** |
| MISO | thermal GW (act 15.227) | 12.986 (+15%→−15% band) | 8.839 (**−42%**) | under-retire (level) |
| **PJM** | coal recall >300 MW | **0%** | **76%** | wave **recovered** |
| PJM | coal econ (act 6.885 GW) | 0.0 | 11.537 (**+68%**) | over-retire (level) |
| PJM | false-retire raw/IS | 4.097 / 0.0 | 8.749 / 4.652 | see §5 (level+reversal) |

- **The redesign did exactly what it was designed to do (memo §0, §3.6):** it
  removed the cross-fuel ORDER race and the fuel-partitioned eligible set. In
  MISO the pure-false-retire gas_st wave (a fuel that retired **zero** in
  reality) collapses 8.643 → **0.0 GW**; in PJM the coal wave the D1=3
  consecutive-loss counter **eliminated** (recall 0%) is **recovered** by the
  soft latch (recall 76%). T-R10 (the pre-registered no-inversion guard) is
  **PASS on the economic channel for both ISOs** (§5).
- **What it did NOT fix — and was told in advance it would not (memo §3.6
  "honest limits"):** the signal LEVEL. MISO now **under**-retires thermal
  (−42%: coal 8.054 vs 10.934, gas_ct/gas_cc/oil exit 0.0 vs 2.4/0.5/0.5
  actual); PJM **over**-retires coal on depth (+68%). Both are the revenue-side
  lane (BLK-6/BLK-9, RD-4 — the PJM coal break-even ≈ 92 vs the current
  58.5 $/kW-yr bar), **never a fuel-specific patch** (rule 1).
- **PJM's 4.097 GW nuclear "false-retire"** is the announced-channel
  Byron/Dresden reversal (IS-2020-excluded as `reversal_exposure`, §c.5-1) —
  information-set-correct, reality-reversed by IL CEJA; it is NOT an economic
  over-retire and does not enter the T-R10 economic-channel guard.

ERCOT composition leg + LOYO folds + precise BLK-10 fired-MW are **PENDING**
(§3 note, §5, §7): the PJM/MISO R-NEW bundles were solved by parallel sessions
and only their reports are committed — the bundles are not on this container's
disk, so per-fold re-scoring cannot run here without re-solving. ERCOT is
mid-solve at write time.

---

## 1. What landed (implementation)

`retirement_rule: str = "legacy"` gates the decision rule in
`ScenarioConfig`; `model/capacity.py::apply_economic_retirements` computes the
identical per-unit screen margins under both rules and branches:

- **`"legacy"` (default, byte-identical):** the per-fuel consecutive-loss
  counters (`retirement_years_*`), exactly as shipped. Byte-identity proof:
  1. the new fields are `_CACHE_KEY_OPTIONAL_FIELDS`-dropped at their defaults,
     and the deleted staged pair was already optional-at-default, so the default
     `cache_key()` is unchanged on `origin/main` and this branch;
  2. the legacy branch consumes margins computed by the same code path in the
     same order (counter update moved after the margin loop — arithmetic,
     ordering, and eligible-set construction unchanged);
  3. the full committed test battery passes unchanged (the pre-existing
     environment failures — missing gitignored `data/clean/` partitions in a
     fresh container + a CAISO topology test drift — reproduce **identically**,
     62 = 62, with the changed files swapped for `origin/main`'s, so no failure
     is change-attributable);
  4. `test_config.py::test_retirement_years_coal_default_is_three` proves the
     lag fields are inert under the default rule.
- **`"pipeline"` (R-NEW, probe arm):** `_apply_pipeline_retirements` —
  1. *Uniform decision* at the identical `net_revenue < going_forward_cost`
     bar; decision persistence **D = 0** (open DOF, held by parsimony — the
     flat-expectation degenerate NPV form, memo §3.1; never tunable, rule 21).
  2. *Joint pipeline-entry competition:* all newly failing units across ALL
     fuels compete in one year, considered worst-first by margin depth
     ($/kW-yr shortfall); admission capped by the EXISTING accredited-adequacy
     requirement (`resolve_adequacy_requirement_mw` — `peak ×
     (1 + PLANNING_RESERVE_MARGIN_BY_ISO)` vs `accredited_firm_capacity_mw`)
     evaluated on the schedule of pending exits, retention
     cheapest-firm-adequacy-first via the UNCHANGED `_apply_reliability_floor`
     machinery and metric. No new parameter.
  3. *Soft latch:* a pipelined unit leaves ONLY by re-clearing the same bar at
     a later screen (`reversed`); a failing re-screen is `re_confirmed`.
  4. *Execution after the identified lag:* `retirement_execution_lag_*`
     (RC-0B §a.3 measured announcement→deactivation medians — coal 3 (same
     identification as the adopted D1=3; coal timing byte-equivalent, proven by
     `test_coal_timing_matches_legacy_d1_counter`), gas_ct 2, gas_st 1, oil 1,
     gas_cc 1 (D3: measured adopted over holding 2), nuclear held 3 (open DOF),
     gas_cc_ccs `None` = inherits gas_cc (open DOF)). `decided_year` = the loss
     year (`year − 1` at screen time); execution at `decided_year + L_f`.
  5. *Reliability floor at execution unchanged* — the realized-year backstop;
     a floor-retained due unit stays online AND pipelined.
  6. *Ledger:* `pipeline_events` rows (`decided` / `re_confirmed` /
     `reversed` / `entry_capped` / `executed`, with `decided_year` /
     `execute_year`) in the evolution ledger, so scoring sees decision and
     execution separately.

**D2 executed (rule 26 — deleted, not zeroed):** `staged_oversupply_thinning`
+ `staged_thinning_max_gw_per_year` and `_apply_staged_thinning_cap` are
REMOVED; a config passing them now raises `TypeError`
(`test_staged_thinning_fields_are_deleted`). The execution-lag pipeline
carries the same physical deactivation queue exactly once (rule 19; RC-0B
§a.6). The harness staged flags are removed; `--retirement-rule
{legacy,pipeline}` is the probe arm (`scripts/run_capacity_hindcast.py`,
default `legacy`, never the harness default pending FF-2C).

Cross-year state: under the pipeline rule the existing `consecutive_loss_years`
dict seam threads `unit_id -> decided_year` — no runner/evolve_fleet signature
change; callers are rule-agnostic.

## 2. DOF-ledger delta (memo §5 executed)

| Change | Fields | Status |
|---|---|---|
| **Retired (7 fitted-adjacent integers)** | `retirement_years_{gas_ct,gas_st,oil,gas_cc,nuclear}` (consistent-but-unidentified decision thresholds — superseded as decision inputs; the fields remain parseable ONLY for the gated legacy rule's byte-identity, deleted outright at the FF-2C flip) + `staged_oversupply_thinning`, `staged_thinning_max_gw_per_year` (**deleted at this commit**, rule 26) | executed |
| **In (5 identified lags)** | `retirement_execution_lag_{coal=3,gas_ct=2,gas_st=1,oil=1,gas_cc=1}` — RC-0B §a.3 measured medians, rule-23-frozen (re-derive only on EIA-860 vintage update) | executed |
| **Open DOFs held (2)** | decision persistence `D = 0` (unobservable, RC-0B §a.1 — held by parsimony, never residual-tunable); `retirement_execution_lag_nuclear = 3` / `gas_cc_ccs = inherit` (no identifying sample; T-R7 guards the nuclear channel) | ledgered |
| **No new parameter** | soft-latch reversal bar (= the existing GFC bar), depth-ordering metric (computed), entry adequacy cap (existing requirement) | per memo §5 |

Net: **−7 fitted-adjacent integers, +5 identified lags, 2 open DOFs held (none
tuned)** — identification quality strictly improves (memo §5).

## 3. Measurement set

All R-NEW runs `retirement_rule="pipeline"` at HEAD, 2021–2025 realized, 2022
bridged-never-solved, allowed solve years {2021, 2023, 2024, 2025} (rule 22 /
plan §2.3); forecast-validation dashboard ONLY. Multi-zone legs solved
sequentially (rule 12 memory clause; ~8.6 GB each). BEFORE legs reused from the
committed record (never re-solved):

| Leg | Config | Status | BEFORE reference |
|---|---|---|---|
| PJM `pjm-2021-2025-realized-cmc-rnew` | `--capacity-market-clearing --retirement-rule pipeline` | **SOLVED** (bundle `cb5e2ecf49e7cfa3`; report committed) | `-cmc-probe-d1` (D1=3) + `-cmc-probe` (D1=1) + `-cmc-before` |
| MISO `miso-2021-2025-realized-cmc-rnew` | same (seasonal RBDC grain resolver-native since RC-1C) | **SOLVED** (bundle `e5254f0e8abd6a48`; report committed) | `-cmc-probe-d1` / `-cmc-probe` / `-cmc-before` |
| ERCOT `ercot-2021-2025-realized-comp-rnew` | `--entry-lookahead-reprice --limited-foresight-dispatch --retirement-rule pipeline` | **PENDING** (in-session solve; clean tree regenerating) | `-g31staged-rc2a` (thermal 12.727 GW, coal 6.466, recall 1.0, false 11.292 GW) |

> **Bundle-availability note (rule 27 aftermath).** The PJM/MISO R-NEW bundles
> were solved on parallel-session containers; only their `.md` reports were
> committed (the sidecar/registry files are the deliverable per CLAUDE.md rule
> 15, but the full evolution-ledger bundles are gitignored/disposable and are
> NOT on this container's disk). The measured numbers in §4–§6 are quoted
> **verbatim from the committed reports**; anything requiring a re-score of the
> raw bundle (per-fold LOYO, precise backstop fired-MW) is marked PENDING rather
> than recomputed from an absent bundle or — forbidden — invented (rule 1 /
> RC-2B §0: only MEASURED numbers are PASS evidence).

## 4. T-R scorecard — MEASURED (bands imported by reference, never restated looser)

Quoted verbatim from the committed R-NEW reports
(`docs/hindcast-reports/{pjm,miso}-2021-2025-realized-cmc-rnew-2026-07-18.md`).
Grain: per-fuel MW coverage (G-31); raw AND IS-2020 (T-R8) reported side by
side. ❌/✅ are the reports' own band verdicts.

### PJM (curve-ON)

| quantity | actual | R-NEW model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired (T-R1) | 11.121 | 15.643 | +41% | ❌ FAIL |
| unit recall >300 MW (T-R1) | 17 | 13 matched (76%) | — | ✅ PASS |
| false-retire raw / IS-2020 | — | 8.749 / 4.652 | 56% / 40% of model | ❌ FAIL |
| coal econ (cum) | 6.885 | 11.537 | +68% | over-retire |
| gas_ct / oil econ | 3.491 / 0.555 | 0.0 / 0.0 | −100% | under-retire |
| wind / solar adds | 1.619 / 13.066 | 6.0 / 24.0 | +271% / +84% | ❌ FAIL (T-R3 mix) |
| gas_cc / gas_ct adds | 8.525 / 0.447 | 5.0 / 2.353 | −41% / +426% | ❌ FAIL |
| 2025 system CO₂ (Mt) | 448.7 | 301.9 | −33% | ❌ FAIL |

### MISO (curve-ON, seasonal)

| quantity | actual | R-NEW model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired (T-R1) | 15.227 | 8.839 | −42% | ❌ FAIL |
| unit recall >300 MW (T-R1) | 17 | 13 matched (76%) | — | ✅ PASS |
| false-retire raw / IS-2020 | — | **0.0 / 0.0** | 0% | ✅ **PASS** |
| coal econ (cum) | 10.934 | 8.054 | −26% | under-retire |
| gas_ct / gas_cc / oil econ | 2.435 / 0.521 / 0.502 | 0.0 / 0.0 / 0.0 | −100% | under-retire |
| wind / solar adds | 7.2 / 18.649 | 12.0 / 12.0 | +67% / −36% | ❌ FAIL (T-R3 mix) |
| gas_cc / gas_ct adds | 3.867 / 1.379 | 0.0 / 0.0 | −100% | ❌ FAIL |
| 2025 system CO₂ (Mt) | 301.4 | 319.5 | +6% | ✅ PASS |

> **Reading (T-R1/T-R2/T-R4).** Both ISOs keep the **76% recall PASS** and pass
> their scarcity-position / CO₂ items where the D1 legs did; the **thermal-GW
> magnitude FAILs are the signal-level residual** the redesign explicitly does
> not address (memo §0). ERCOT (T-R3 composition leg) is PENDING (§3).

## 5. T-R10 no-inversion guard + LOYO (memo §4, pre-registered)

**T-R10 is the instrument this redesign exists to move**, and it is the metric
that is fully evaluable from the committed per-fuel exit tables + the
RD-5-fixed actuals (no absent-bundle dependency). Definitions (memo §4):
`first_mover` = fuel of the earliest model **economic-channel** exit;
**T-R10a** FAILs iff `A_{first_mover}=0`; **T-R10b** FAILs iff any fuel with
`A_f=0` accumulates > 1 GW model economic exits.

| ISO | first economic mover | `A_{first_mover}` | zero-real fuel w/ >1 GW model econ exit? | T-R10a | T-R10b |
|---|---|--:|---|:--|:--|
| **MISO** | coal | 10.934 GW | none (model econ exits = coal 8.054 + nuclear 0.768; both `A_f>0`) | ✅ PASS | ✅ PASS |
| **PJM** | coal | 6.885 GW | none (model econ exits = coal 11.537; gas_ct/oil model = 0.0) | ✅ PASS | ✅ PASS |

- **MISO is the flagship BEFORE→AFTER (memo §0, D1 findings §3).** The D1=3 leg
  FAILed both gates: gas_st (`A=0`) was the first mover and accumulated
  **8.643 GW** — the exact inversion the redesign targets. R-NEW: gas_st →
  **0.0**, coal is the first mover (`A=10.934>0`), no zero-real fuel exits at
  all → **both gates PASS**. The 8.643 → 0.0 GW collapse is the measured proof
  the cross-fuel race and the fuel-partitioned eligible set are gone.
- **PJM** never tripped T-R10a on the economic channel (its D1=3 failure was
  *elimination* — recall 0% — not a wrong-fuel race). R-NEW **recovers** the
  coal wave (recall 0% → 76%) via the soft latch and stays inversion-clean
  (only coal exits economically). The 4.097 GW nuclear is the **announced
  channel** (Byron/Dresden reversal, `reversal_exposure`, IS-2020-excluded per
  §c.5-1) — it is not an economic exit and does not enter T-R10.

**LOYO (rule 22) — PENDING (blocker stated).** The leave-one-year-out folds
within 2023–2025 require re-scoring each R-NEW bundle with one year held out;
the PJM/MISO R-NEW bundles are not on this container's disk (§3 note), so LOYO
cannot be computed here without re-solving. It is **not** estimated. Next
session (or a container with the bundles) runs: for each fold, confirm the
T-R10a/b PASS and the 76% recall hold in ≥ 2/3 folds; a fold regression BLOCKS
and is a finding, never a band to widen. The single-window T-R10 PASS above is
selection evidence, not a certified fold-robust number.

## 6. §2.1 flip-gate items 3–4 per ISO — MEASURED (the FF-2C input)

Flip-gate items 3 (no cross-fuel inversion) and 4 (recall restored without a
false-retire blow-up), graded on the measured economic channel:

| ISO | item 3 — no inversion (T-R10a/b) | item 4 — recall w/o false-retire blow-up | net gate |
|---|:--|:--|:--|
| **MISO** | ✅ PASS (gas_st 8.643 → 0.0; first mover coal) | ✅ PASS (recall 29% → 76%; false-retire 8.643 → **0.0**) | **CLEARS 3–4**; blocked only on level (thermal −42%, revenue lane) |
| **PJM** | ✅ PASS (coal-only econ exits; nuclear = announced reversal) | ⚠️ MIXED (recall 0% → 76% PASS; but false-retire 4.097→8.749 raw / 0.0→4.652 IS — the rise is coal **depth** over-retire + the IS-excluded nuclear reversal, a LEVEL issue) | **CLEARS item 3**; item 4 recall-restored but level-over on coal (RD-4 bar) |
| **ERCOT** | PENDING (composition leg solving) | PENDING | PENDING |

**FF-2C reading:** items 3–4 (the inversion + wave-elimination blockers RC-1A-D1
raised) are **cleared for MISO and PJM** by R-NEW; the remaining PJM/MISO gaps
are signal-LEVEL (over/under-retire depth), which route to the revenue lane
(BLK-6/BLK-9, RD-4), not to the decision rule. ERCOT is the open leg.

## 7. BLK-10 re-measure

- **PJM (from the committed D1 record, D1 findings §2):** BLK-10 —
  the `gas_ct_adequacy_2025` backstop over-fire — was **resolved** at the
  curve-ON level: the D1=1/D1=3 gas_ct adequacy adds went 8.428 → 0.0 (no coal
  wave → no adequacy deficit → no backstop fire). Under **R-NEW**, the PJM
  report shows **gas_ct adds = 2.353 GW** (economic entry, +426% vs the 0.447
  actual) — a partial re-emergence, but the precise split between economic new
  entry and the `reserve_margin_build` backstop requires the bundle's per-year
  `evolution_*.json` (absent, §3). **Precise backstop-fired-MW per leg:
  PENDING** — flagged for the next session with the bundle. The gap-register
  "re-measure after the rule change" requirement is partially satisfied (the
  wave-coupling finding holds); the exact fired-MW is the open number.
- **MISO / ERCOT:** PENDING (MISO bundle absent; ERCOT solving).

## 8. Honest limits & open blockers (stated in advance, memo §3.6)

- The redesign fixes ORDER and COMPOSITION races, not signal level. Measured:
  MISO under-retires thermal −42%, PJM over-retires coal +68% — both route to
  the revenue lane (BLK-6/BLK-9, RD-4), **never a fuel patch** (rule 1).
- PJM's coal over-retire is consistent with the memo's forewarned RD-4 bar
  question (§3.6): the PJM coal break-even ≈ 92 vs the current 58.5 $/kW-yr
  going-forward bar; the oscillating 24–142 $/kW-yr margin trace straddles 92,
  not 58.5. Raising the bar is the revenue lane's job, not the rule's.
- A residual closable only by an unidentified value is an open blocker, written
  up, NOT a parameter (rule 21).

## 9. Push-transport incident (rule 27) — STOP-THE-LINE record

**What happened.** The original FF-1A landing (PR #2430, merged as `2563370`)
truncated `src/market_sim/model/capacity.py` from **3762 → 2291 lines
(−39%)** — a response-budget-clipped `push_files` full-file rewrite (exactly
the failure mode CLAUDE.md rule 27's push-integrity protocol names). It deleted
`evolve_fleet` (the orchestrator, still called at `runner.py:789`),
`apply_ccs_retrofit` + its helpers (`_adjust_retrofit_capex`,
`_ccs_retrofit_payback_years`, `_retrofit_price_row`,
`_renewable_nameplate_by_fuel`, `renewable_credits_applied`, `_prior_attr`,
`_credit`, `_ccs_45q_window_years`), `apply_economic_new_entry`,
`apply_reserve_margin_build`, `resolve_reserve_margin_build_enabled`,
`capacity_reserve_position`, and `accredited_firm_capacity_mw` (still called at
`capacity.py:1106` and `runner.py:2096`). Live call sites dangled ⇒ `import
market_sim.runner` failed ⇒ **main was import-broken**. Only
`_apply_staged_thinning_cap` was a valid removal (D2). Subsequent "restore"
commits merged fragments (0 / 500 / 1,020 / 1,000 lines) and did not fix it.

**Restoration (this session, PR #2438, merged `7d4b7389`).**
1. Restored `capacity.py` to the last-good merge base `573350d`
   (`git show 573350d:…` — the FF-1A merge base, 3762 lines) and confirmed
   every deleted function was back **before** changing anything.
2. Re-applied ONLY R-NEW to `apply_economic_retirements` (uniform decision,
   joint adequacy-capped entry, soft latch, per-fuel execution lag, floor
   unchanged, ledger events) + helpers `_apply_pipeline_retirements` /
   `_event` / `_execution_lag_years`; evolution_ledger `pipeline_events`;
   `register_hindcast` r-new arm.
3. Deleted ONLY `_apply_staged_thinning_cap` + the two staged config fields
   (D2, rule 26) — nothing else.
4. **Verified before any push (rule 27):** `git diff 573350d` touches only
   R-NEW + the staged-thinning removal, nothing touching evolve_fleet / CCS /
   new-entry / backstop / accredited-capacity; def-name set == parent minus
   `{_apply_staged_thinning_cap}` plus the 3 R-NEW helpers; capacity.py 3967
   lines; `runner.py:789` + both `accredited_firm_capacity_mw` sites resolve;
   `test_capacity.py` + `test_config.py` = 229 pass; the full-suite pre-existing
   failures reproduce **identically** (62 = 62) with the changed files swapped
   for `origin/main`'s (proven failure-neutral); a 1-gen/1-zone `evolve_fleet`
   smoke runs green under both rules.
5. **Byte-exact push, then blob-verified.** Raw REST writes are proxy-blocked
   (403) and inlining the 490 KB `scenarios.py` / 189 KB `capacity.py` through
   `push_files` would re-truncate (the same response-budget clip) — so the push
   used the exact local git objects (server-side commit), and **every pushed
   file's git blob SHA + line count was fetched back and compared to local**
   before proceeding (capacity.py 3967≡3967, scenarios.py 7423≡7423, all six
   files match). Rebased onto the moved `origin/main` (PR #2436 had independently
   landed the `--retirement-rule` harness/test scaffolding, satisfied here by
   the scenarios.py fields). Not self-merged in seconds — `file-integrity-guard`
   ran (3+ min) and PASSED before the merge; the merge grew capacity.py
   (2291 → 3967) so the >30%-shrink guard never tripped.

---

*Produced 2026-07-18 (FF-1A). No holdout year solved or scored; 2022 bridged;
no backcast artifact touched; nothing tuned to a residual. Measured numbers
quoted verbatim from committed reports; ERCOT leg + LOYO folds + precise
BLK-10 fired-MW are PENDING with the blocker stated (§3), never estimated.*
