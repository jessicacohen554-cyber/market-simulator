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

**COMPLETE (FF-1A-C, 2026-07-18).** All three R-NEW legs are re-solved at
merged HEAD, scored (raw + IS-2020 + T-R10 + LOYO + BLK-10, all scorer-side
via `score_capacity_hindcast.py --flip-gate-extras`), and registered on the
forecast-validation dashboard. The ERCOT composition row is §4, the measured
LOYO fold tables and T-R10 verdicts are §5, the ERCOT flip-gate row is §6, and
the precise BLK-10 fired-MW per leg is §7. Headline adds: **PJM's IS-2020
thermal total is 11.546 vs 11.121 actual (+3.8%, PASS)** — the raw +41% FAIL
is carried entirely by the reality-reversed Byron/Dresden nuclear — and the
**ERCOT R-NEW leg collapses the over-retirement level 12.727 → 1.87 GW
(+730% → +22%)** while inverting its composition onto zero-real gas_st
(T-R10a/b FAIL, the §8 pre-declared honest limit, routed to BLK-6/RD-4).

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
| PJM `pjm-2021-2025-realized-cmc-rnew` | `--capacity-market-clearing --retirement-rule pipeline` | **RE-SOLVED at HEAD** (bundle `784e354a7b8b7317`, FF-1A-C; supersedes the truncated-tree `cb5e2ecf49e7cfa3`) | `-cmc-probe-d1` (D1=3) + `-cmc-probe` (D1=1) + `-cmc-before` |
| MISO `miso-2021-2025-realized-cmc-rnew` | same (seasonal RBDC grain resolver-native since RC-1C) | **RE-SOLVED at HEAD** (bundle `3860df088dfb3066`; reproduces `e5254f0e8abd6a48` exactly) | `-cmc-probe-d1` / `-cmc-probe` / `-cmc-before` |
| ERCOT `ercot-2021-2025-realized-comp-rnew` | `--entry-lookahead-reprice --limited-foresight-dispatch --retirement-rule pipeline` | **SOLVED at HEAD** (bundle `9641a1b790fad79a`, FF-1A-C) | `-g31staged-rc2a` (thermal 12.727 GW, coal 6.466, recall 1.0, false 11.292 GW) |

> **Reproduction & provenance (rule 27 aftermath, closed by FF-1A-C).** The
> original PJM/MISO R-NEW bundles were solved on parallel-session containers
> running the **#2430-truncated capacity.py** (the manager ledger verified the
> retirement pipeline md5-identical across the truncated/restored trees, so
> their retirement numbers were valid; the truncation had deleted only the
> forecast-evolution helpers). The FF-1A-C re-solve at merged HEAD confirms
> exactly that: **every retirement metric reproduces byte-for-byte** in both
> ISOs (MISO's report reproduces in full), and the only PJM deltas are on the
> restored-evolution side — the 2025 adequacy backstop re-sizes 2.353 → 2.5 GW
> gas_ct and 2025 CO2 shifts 301.9 → 301.8 Mt (the larger backstop CT in the
> 2025 dispatch). The HEAD bundles supersede; the committed reports were
> regenerated from them. §4–§7 numbers are measured from the HEAD bundles'
> committed `score.json` (raw AND IS-2020; nothing quoted from an absent
> bundle, rule 1 / RC-2B §0).

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
| gas_cc / gas_ct adds | 8.525 / 0.447 | 5.0 / 2.5 | −41% / +459% | ❌ FAIL (gas_ct = the §7 backstop row, HEAD sizing) |
| 2025 system CO₂ (Mt) | 448.7 | 301.8 | −33% | ❌ FAIL |

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
> not address (memo §0). New with the HEAD re-score: **PJM's IS-2020 thermal
> total is 11.546 vs 11.121 actual (+3.8%, inside the ±10% T-R1 band — PASS)**;
> the raw +41% is entirely the information-set-correct Byron/Dresden nuclear.

### ERCOT (T-R3 composition leg — energy-only; measured at HEAD, FF-1A-C)

R-NEW arm `--entry-lookahead-reprice --limited-foresight-dispatch
--retirement-rule pipeline` (the staged-thinning arm of the rc2a BEFORE no
longer exists — D2 deleted it; this leg is its R-NEW successor, not an
apples-to-apples rerun). BEFORE = `-g31staged-rc2a` (2026-07-16).

| quantity | actual | rc2a BEFORE | R-NEW | band |
|---|--:|--:|--:|:--|
| thermal GW retired (level) | 1.534 | 12.727 (+730%) | **1.87 (+22%)** | ❌ FAIL (but ~7× closer) |
| unit recall >300 MW | 3 | 3/3 (100%) | **0/3 (0%)** | ❌ FAIL |
| false-retire raw = IS-2020 | — | 11.292 GW (89%) | **1.87 GW (100% of model)** | ❌ FAIL |
| coal / gas_ct / gas_st econ exits | 0.932 / 0.502 / 0.0 | 6.466 / 3.023 / 3.237 | **0.0 / 0.0 / 1.87** | inversion (T-R10, §5) |
| solar adds (T-R3c) | 25.08 | 4.0 | **0.0** | ❌ regression |
| wind / gas_cc / gas_ct / storage adds | 12.663 / 0.244 / 3.692 / 13.691 | 15.0 / 6.0 / 6.0 / 16.0 | 20.0 / 3.0 / 0.0 / 9.0 | ❌ FAIL (storage Δ-share PASS) |
| 2025 CO₂ (Mt) | 193.6 | 115.7 (−40%) | **140.7 (−27%)** | ❌ FAIL |

- **The level is fixed by the honest mechanism, the composition is not.**
  R-NEW's uniform bar + soft latch + execution lags collapse the rc2a
  over-retirement 12.727 → 1.87 GW — but the surviving exits are 100% gas_st
  (`A = 0`), decided 2021 and executed 2022 (lag 1), while the real coal/CT
  exits are missed entirely (recall 100% → 0%). This is the §8 pre-declared
  honest limit measured precisely: without the scarcity/AS revenue the screens
  under-value peaking-adjacent classes (screen CT $/kW-yr ≈ 25% of the SOM ≈68
  anchor, plan §1.2/T-R3b), so the only class the uniform bar exits is the
  gas_st drag class reality kept online. **Routed to BLK-6/RD-4 (G-20/G-22
  lane) as a finding — never a fuel patch (rule 1).**
- **T-R3(a) is superseded, not failed:** the committed staged arm cannot be
  reproduced at HEAD because `staged_oversupply_thinning` was deleted (D2,
  rule 26); this leg replaces it as the composition probe of record.
- **Solar entry 4 → 0 GW (T-R3c regression):** the rc2a solar entry rode the
  staged-thinning arm's tightened fleet; with the thinning deleted and R-NEW
  exiting only 1.87 GW, no in-year scarcity forms and the BLK-8 solar-entry
  zero returns. Confirms BLK-8/FF-2A's entry-stack charter (and FF-1B's
  availability work) carry this, not the decision rule.
- I5 (no retire-reenter) and I13 (no cobweb) **PASS** on all three legs
  (T-R5-inv); ERCOT I12 reserve-margin sits 34–47% vs the [13.8%, 28.7%] band
  — the under-retirement + wind-overbuild signature, report-only here.

## 5. T-R10 no-inversion guard + LOYO (memo §4, pre-registered)

**T-R10 is the instrument this redesign exists to move**, and it is the metric
that is fully evaluable from the committed per-fuel exit tables + the
RD-5-fixed actuals (no absent-bundle dependency). Definitions (memo §4):
`first_mover` = fuel of the earliest model **economic-channel** exit;
**T-R10a** FAILs iff `A_{first_mover}=0`; **T-R10b** FAILs iff any fuel with
`A_f=0` accumulates > 1 GW model economic exits.

Now computed by the scorer (`score_tr10`, raw AND IS-2020 — identical verdicts
in both modes on all three legs), from the HEAD bundles' `score.json`:

| ISO | first economic mover (year) | `A_{first_mover}` | zero-real fuel w/ >1 GW model econ exit? | T-R10a | T-R10b |
|---|---|--:|---|:--|:--|
| **MISO** | coal (2024) | 10.934 GW | none (econ channel = coal 8.054 only; nuclear 0.768 is announced) | ✅ PASS | ✅ PASS |
| **PJM** | coal (2024) | 6.885 GW | none (econ channel = coal 11.537 only) | ✅ PASS | ✅ PASS |
| **ERCOT** | gas_st (2022) | **0.0 GW** | **gas_st, 1.87 GW** | ❌ FAIL | ❌ FAIL |

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

**LOYO (rule 22) — MEASURED (FF-1A-C, scorer-side folds, no re-solve).**
Fold *y* re-scores the cumulative window with year-*y* events dropped from
BOTH the model ledger and the actuals (`loyo_folds`, committed in each
bundle's `score.json`); the promotion bar is a verdict holding in ≥ 2/3 folds:

| ISO-fold | recall | false-retire raw / IS (GW) | T-R10a | T-R10b |
|---|--:|--:|:--|:--|
| PJM −2023 | 9/9 (PASS) | 11.153 / 7.056 | PASS | PASS |
| PJM −2024 | **0/16 (FAIL)** | 4.097 / 0.0 | PASS | PASS |
| PJM −2025 | 12/16 (PASS) | 9.194 / 5.097 | PASS | PASS |
| MISO −2023 | 11/14 (PASS) | 0.0 / 0.0 | PASS | PASS |
| MISO −2024 | **0/13 (FAIL)** | 0.006 / 0.006 | PASS | PASS |
| MISO −2025 | 13/17 (PASS) | 0.0 / 0.0 | PASS | PASS |
| ERCOT −2023/−2024/−2025 | 0/1, 0/3, 0/3 (FAIL) | 1.87 / 1.87 each | FAIL | FAIL |

Verdicts (`holds_2of3`): **PJM and MISO hold ≥ 2/3 on recall, T-R10a and
T-R10b — the rule-22 promotion criterion for the capacity-market flips is
MET**, with T-R10a/b holding **3/3**. ERCOT holds 0/3 on everything (its
gas_st exits are decided 2021/executed 2022 — never in a held-out year — so
every fold sees them; consistent with §4's honest limit; ERCOT is not a flip
candidate). One measured caveat, reported not widened: **both curve-ON ISOs'
recall folds sit exactly at the 2/3 boundary** — the −2024 fold zeroes recall
because the model's coal wave executes almost entirely in 2024 (coal decisions
from 2021 + execution lag 3) while the real exits spread across 2023–2025.
That is a timing-concentration finding for the revenue lane's level work
(T-R1's 1.5-yr timing band neighborhood), not a rule defect: the wave's
*membership* is fold-robust, its *calendar spread* is not.

## 6. §2.1 flip-gate items 3–4 per ISO — MEASURED (the FF-2C input)

Flip-gate items 3 (no cross-fuel inversion) and 4 (recall restored without a
false-retire blow-up), graded on the measured economic channel:

| ISO | item 3 — no inversion (T-R10a/b) | item 4 — recall w/o false-retire blow-up | net gate |
|---|:--|:--|:--|
| **MISO** | ✅ PASS (gas_st 8.643 → 0.0; first mover coal) | ✅ PASS (recall 29% → 76%; false-retire 8.643 → **0.0**) | **CLEARS 3–4**; blocked only on level (thermal −42%, revenue lane) |
| **PJM** | ✅ PASS (coal-only econ exits; nuclear = announced reversal) | ⚠️ MIXED (recall 0% → 76% PASS; but false-retire 4.097→8.749 raw / 0.0→4.652 IS — the rise is coal **depth** over-retire + the IS-excluded nuclear reversal, a LEVEL issue) | **CLEARS item 3**; item 4 recall-restored but level-over on coal (RD-4 bar) |
| **ERCOT** | ❌ FAIL (gas_st inversion persists under R-NEW: T-R10a/b FAIL, 1.87 GW zero-real) | ❌ FAIL (recall 100% → 0%; false-retire 100% of model, though 11.292 → 1.87 GW absolute) | **does NOT clear 3–4** — but ERCOT is energy-only, not a flip candidate; this is the §4/§8 honest limit routed to BLK-6/RD-4 |

**FF-2C reading (final, all legs measured):** items 3–4 (the inversion +
wave-elimination blockers RC-1A-D1 raised) are **cleared for MISO and PJM** by
R-NEW, and the clearance is **LOYO-robust (≥ 2/3 folds, T-R10 3/3 — §5)**; the
remaining PJM/MISO gaps are signal-LEVEL (over/under-retire depth), which
route to the revenue lane (BLK-6/BLK-9, RD-4), not to the decision rule.
ERCOT measured and does not clear — expected and pre-declared: it is not a
capacity-market flip candidate, and its gas_st composition inversion is the
revenue-lane residual (§4), not a flip-gate blocker for PJM/MISO.

## 7. BLK-10 re-measure — MEASURED (FF-1A-C; the FF-2A baseline)

Precise `reserve_backstop`-sourced MW per leg, from each HEAD bundle's ledgers
via `blk10_backstop_fired` (committed in `score.json`):

| Leg | backstop fired (MW) | fired rows | thermal adds by source (MW) | pre-R-NEW reference |
|---|--:|---|---|---|
| **PJM** cmc-rnew | **2,500.229** | `gas_ct_adequacy_2025` (one step, 2025) | economic 5,000 + backstop 2,500.229 | RC-1A curve-ON probe: **6,430** in one step (`gas_ct_adequacy_2025`, gap-register §3.9) |
| **MISO** cmc-rnew | **0.0** | none | (no thermal additions at all) | RC-1A: 640 (annual grain) / 10 (seasonal RC-1C leg) |
| **ERCOT** comp-rnew | **0.0** | none | economic 3,000 | n/a — energy-only, backstop disabled by design (`resolve_reserve_margin_build_enabled`) |

**Over-fire verdict (the gap-register §3.9 "re-measure after D1" gate, graded):**
the R-NEW-damped exit wave **still over-fires the PJM backstop, at ~39% of the
pre-R-NEW magnitude**. The 2024-concentrated coal execution (2021 decisions +
lag 3) leaves the 2025 entering fleet 2,275 firm-MW short (2,500.229 nameplate
× (1 − EFORd_gas_ct)) and the one-pass backstop rebuilds the full deficit in a
single step — 2,500 MW of gas_ct against an ISO whose actual 2021–2025 gas_ct
additions were 447 MW (~5.6×). Correction of the earlier reading: the
committed truncated-tree report's 2.353 GW "economic entry" was in fact this
backstop row at its truncated-tree sizing; at HEAD the split is measured —
economic gas_ct entry = 0 of the 2.353→2.5, ALL of it is the backstop. MISO's
over-fire is **fully resolved** under R-NEW (0.0 fired — the milder 0.64/0.01
GW probe-era fires disappear entirely with the damped wave). **FF-2A's
backstop-sizing rework is therefore chartered on PJM alone**: the finding is
the one-pass full-deficit rebuild (§1.5 signature), now cleanly separated from
the wave size (which R-NEW already damped 6.43 → 2.5 GW).

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

**FF-1A-C addendum (2026-07-18, this completion session) — three further
push-transport events, each caught by the rule-27 verify step, none
reaching main broken:**
1. A `push_files` call for the branch accidentally carried a literal
   placeholder string as `scripts/score_capacity_hindcast.py`'s content
   (commit `54869c3` on the working branch) — exactly the
   placeholder-overwrite failure mode rule 27 names. The immediately-following
   blob verification caught it; the next commit (`52cb462`) restored the full
   file and was verified byte-identical to the local blob before any further
   work. The placeholder exists only in intermediate branch history.
2. Generated JSON artifacts (score.json/sidecars) carry literal `\uXXXX`
   escapes on disk; inline `push_files` emission decodes them to the raw
   characters, so byte-identity fails while content is intact. Convention
   adopted and applied: generated-JSON pushes are verified by **JSON-equality
   + line count** (no content loss) and the local copy is synced to the pushed
   bytes; hand-written source/docs remain byte-verified.
3. The regenerated `forecast-validation.html` (~250 KB after 29 sidecars) is
   structurally un-pushable through full-content inline transport without the
   response-clip risk that truncated #2430 — so FF-1A-C moved the page to
   deploy-time assembly (`register_hindcast.py --page-only --site-dir` in
   `deploy-pages.yml`, stdlib-only, mirroring `build_manifest.py`); the
   committed page copy is now local-preview-only, same convention as the
   backcast manifest files.

---

*Produced 2026-07-18 (FF-1A); completed 2026-07-18 (FF-1A-C). No holdout year
solved or scored; 2022 bridged (the ERCOT gas_st executions land in the 2022
evolution step — evolved, never solved); no backcast artifact touched; nothing
tuned to a residual. All §4–§7 numbers are measured from the three HEAD
bundles' committed `score.json` (raw + IS-2020), solved/scored/registered in
this session; `capacity.py` byte-identical to `origin/main` throughout.*
