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

*(MEASURED verdicts filled in §4–§6 below; this section summarizes after
measurement.)* TO FILL.

---

## 1. What landed (implementation)

`retirement_rule: str = "legacy"` gates the decision rule in
`ScenarioConfig`; `model/capacity.py::apply_economic_retirements` computes the
identical per-unit screen margins under both rules and branches:

- **`"legacy"` (default, byte-identical):** the per-fuel consecutive-loss
  counters (`retirement_years_*`), exactly as shipped. Byte-identity proof:
  1. default `cache_key()` = `c42c02de25bf3120` on both `origin/main` and this
     branch (the new fields are `_CACHE_KEY_OPTIONAL_FIELDS`-dropped at
     defaults; the deleted staged pair was already optional-at-default);
  2. the legacy branch consumes margins computed by the same code path in the
     same order (counter update moved after the margin loop — arithmetic,
     ordering, and eligible-set construction unchanged);
  3. the full committed test battery passes unchanged (the pre-existing
     environment failures reproduce **identically** — 68 = 68 — with the
     changed files swapped for `origin/main`'s, so no failure is
     change-attributable);
  4. `test_legacy_default_ignores_pipeline_fields` proves the lag fields are
     inert under the default rule.
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
     identification as the adopted D1=3, coal timing byte-equivalent, proven
     by `test_coal_timing_matches_legacy_d1_counter`), gas_ct 2, gas_st 1,
     oil 1, gas_cc 1 (D3: measured adopted over holding 2), nuclear held 3
     (open DOF), gas_cc_ccs `None` = inherits gas_cc (open DOF)).
     `decided_year` = the loss year (`year − 1` at screen time); execution at
     `decided_year + L_f`.
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
§a.6). The harness flags are removed; `--retirement-rule {legacy,pipeline}`
is the new probe arm (`scripts/run_capacity_hindcast.py`, default `legacy`,
never the harness default pending FF-2C).

Cross-year state: under the pipeline rule the existing
`consecutive_loss_years` dict seam threads `unit_id -> decided_year` — no
runner/evolve_fleet signature change; callers are rule-agnostic.

## 2. DOF-ledger delta (memo §5 executed)

| Change | Fields | Status |
|---|---|---|
| **Retired (7 fitted-adjacent integers)** | `retirement_years_{gas_ct,gas_st,oil,gas_cc,nuclear}` (consistent-but-unidentified decision thresholds — superseded as decision inputs; the fields remain parseable ONLY for the gated legacy rule's byte-identity, and are deleted outright at the FF-2C flip) + `staged_oversupply_thinning`, `staged_thinning_max_gw_per_year` (**deleted at this commit**, rule 26) | executed |
| **In (5 identified lags)** | `retirement_execution_lag_{coal=3,gas_ct=2,gas_st=1,oil=1,gas_cc=1}` — RC-0B §a.3 measured medians, rule-23-frozen (re-derive only on EIA-860 vintage update) | executed |
| **Open DOFs held (2)** | decision persistence `D = 0` (unobservable, RC-0B §a.1 — held by parsimony, never residual-tunable); `retirement_execution_lag_nuclear = 3` / `gas_cc_ccs = inherit` (no identifying sample; T-R7 guards the nuclear channel) | ledgered |
| **No new parameter** | soft-latch reversal bar (= the existing GFC bar), depth-ordering metric (computed), entry adequacy cap (existing requirement) | per memo §5 |

## 3. Measurement set

All runs `retirement_rule="pipeline"` at HEAD, 2021–2025 realized, 2022
bridged-never-solved, allowed solve years {2021, 2023, 2024, 2025} (rule 22 /
plan §2.3); forecast-validation dashboard ONLY. Multi-zone legs solved
sequentially (rule 12 memory clause; ~8.6 GB each on a 15 GiB box). BEFORE
legs reused from the committed record (never re-solved):

| Leg | Config | BEFORE reference |
|---|---|---|
| PJM `pjm-2021-2025-realized-cmc-rnew` | `--capacity-market-clearing --retirement-rule pipeline` | `pjm-2021-2025-realized-cmc-probe-d1` (D1=3) + `-cmc-probe` (D1=1) + `-cmc-before` |
| MISO `miso-2021-2025-realized-cmc-rnew` | same (seasonal RBDC grain is resolver-native since RC-1C) | `miso-…-cmc-probe-d1` / `-cmc-probe` / `-cmc-before` |
| ERCOT `ercot-2021-2025-realized-comp-rnew` | `--entry-lookahead-reprice --limited-foresight-dispatch --retirement-rule pipeline` (the composition leg; staged arm superseded by the pipeline per D2) | `ercot-…-g31staged-rc2a` (lookahead+staged+ltd-foresight: thermal 12.727 GW, coal 6.466, recall 1.0, false 11.292 GW) |

## 4. T-R scorecard — MEASURED (bands imported by reference, never restated looser)

### PJM (`pjm-2021-2025-realized-cmc-rnew`) vs D1=1 / D1=3 committed probes

| leg | coal econ (GW,cum) | thermal (GW,cum) | recall >300MW | false raw / IS-2020 (GW) | gas_cc / gas_ct adds (GW) |
|---|--:|--:|--:|--:|---|
| BEFORE (fixed, D1-invariant) | 0.0 | 4.106 | 0% | 4.097 / 0.0 | 12.0 / 0.0 |
| D1=1 probe | 9.913 | 14.02 | 76% | 7.125 / 3.028 | 8.0 / 8.428 |
| D1=3 probe | 0.0 | 4.106 | 0% | 4.097 / 0.0 | 8.0 / 0.0 |
| **R-NEW (this leg)** | **11.537** (all 2024) | **15.643** | **76% PASS** | **8.749 / 4.652** | **5.0 / 2.353** |
| actual | 6.885 | 11.121 | — | — | 8.525 / 0.447 |

The coal wave the D1=3 counter ELIMINATED is restored: 90 units decided at
the 2022-bridge screen (loss year 2021), 36 reversed by the latch on later
profitable screens, 54 executed 11.537 GW at the 2024 screen (decided 2021 +
L=3). Reversal exposure 4.097 GW (Byron/Dresden, announced channel,
IS-2020-excluded). All false-retire is coal OVERSHOOT (11.5 vs 6.9) — no
wrong-fuel exit; the pipeline-entry adequacy cap held back 2,843
unit-screens.

| ID | criterion | D1=3 measured | **R-NEW measured** | verdict |
|---|---|---|---|---|
| T-R1a | coal recall > 0; cum ∈ [2,14] GW | 0.0, 0% FAIL | **11.537, 76%** | **PASS** (restored) |
| T-R1b | thermal ≤ 2× actual (22.2 GW) | 4.106 | 15.643 | PASS |
| T-R1c | zero economic nuclear | 0 | 0 (channels: economic = coal only) | PASS |
| T-R1d | 2025 position ≥ half 1.06→1.007 | 0.998 | **0.989** | PASS (mechanism no longer inert — real exits carry it) |
| T-R1e | additions not degraded vs BEFORE | PASS | solar 0→24.0 (closer to 13.07 ✓); wind 6.0 =; gas_cc 5.0 (3.53 vs BEFORE's 3.48 from actual — ~neutral); **gas_ct 2.353 vs BEFORE 0 (actual 0.447) — degraded** (backstop re-fire, §7) | **FAIL (gas_ct only)** |
| T-R4 | 2025 within ±0.028 of 1.007; long yrs OUT | 0.998 in; 2024 1.056 pays 13.4 | **0.989 (abs err 0.018) in-band**; 2023 1.1448 OUT ($0) ✓; **2024 1.0399 pays 40.2 vs real 10.6** — overshoot returns (wave lands all-in-2024) | **PASS on 2025 / FAIL on 2024** |
| T-R5-inv | I5 + I13 PASS | PASS | I5 PASS, I13 PASS (I3/I7/I12/I14 = known 2021 base-year artifacts, identical to committed legs) | PASS |
| T-R7 | nuclear guard | PASS | economic nuclear 0; Byron/Dresden announced → IS-2020 exclusion | PASS |

### MISO (`miso-2021-2025-realized-cmc-rnew`) vs D1=1 / D1=3 committed probes

| leg | coal (GW,cum) | gas_st (GW) | thermal (GW,cum) | recall | false raw / IS-2020 (GW) | 2025 CO2 err |
|---|--:|--:|--:|--:|--:|--:|
| BEFORE (fixed) | 0.0 | 0.0 | 0.784 | 0% | 0.0 / 0.0 | +14% |
| D1=1 probe | 11.809 | 0.0 | 12.593 | 76% | 0.874 / 0.874 | +5% |
| D1=3 probe | 3.558 | **8.643** | 12.986 | 29% | 8.643 / 8.643 FAIL | +8.5% |
| **R-NEW (this leg)** | **8.054** (all 2024) | **0.0** | **8.839** | **76% PASS** | **0.000 / 0.000 PASS** | **+6.0%** |
| actual | 10.934 | 0.0 | 15.227 | — | — | — |

**The D1=3 inversion is eliminated: the economic channel exits coal ONLY.**
59 decided, 6 reversed, 36 executed (8.054 GW at the 2024 screen), 4,089
unit-screens entry-capped by the adequacy requirement. gas_st — the fuel the
per-fuel thresholds pushed out first (8.643 GW against zero real exits) —
never leaves: at decision time it competes jointly and the
cheapest-firm-adequacy retention keeps it (its $35/kW-yr GFC is the cheap
adequacy; coal's 58.5 is the expensive one), exactly the "retain gas_st,
release coal" composition defect 3 made unreachable.

| ID | criterion | D1=3 measured | **R-NEW measured** | verdict |
|---|---|---|---|---|
| T-R2a | coal recall > 0; cum ∈ [3,22] GW | 3.558, 29%, false 8.643 FAIL | **8.054, 76%, false 0.000** | **PASS** (clean — best false-retire of any leg) |
| T-R2b | gas_cc AND wind adds fall vs BEFORE | gas_cc ↓, wind ✗ | gas_cc 9.0→0.0 ✓; **wind 12.0 = 12.0 ✗** (unchanged — BLK-7/RC-0C entry-side lane, D1-invariant) | FAIL (wind half, unchanged from every leg) |
| T-R2c | 2025 CO2 → 0 (report-only) | +8.5% | **+6.0%** (2023 −1.6%, 2024 −6.8%) | improves |
| T-R5-inv | I5 + I13 | PASS | PASS both | PASS |
| T-R7 | nuclear guard | PASS | economic nuclear 0 (0.768 announced = Palisades class, actual 0.812) | PASS |

## 5. T-R10 no-inversion guard + LOYO (memo §4, pre-registered)

| gate | PJM | MISO | verdict |
|---|---|---|---|
| T-R10a first mover (`A_f = 0` fuel may not move first) | coal, 2024 — A_coal = 6.885 GW | coal, 2024 — A_coal = 10.934 GW | **PASS both** |
| T-R10b (> 1 GW model exits in any `A_f = 0` fuel) | none (economic exits are coal-only) | none (coal-only) | **PASS both** |

Raw and IS-2020 modes agree (the economic-channel composition is identical
in both; the IS-2020 adjustment touches only the announced-channel nuclear).

**LOYO (scorer-side folds within 2023–2025, ≥2/3 must hold for each
redesign-attributable verdict flip):**

| fold | PJM recall / false GW | MISO recall / false GW |
|---|--:|--:|
| full | 0.765 / 8.749 | 0.765 / 0.000 |
| drop 2023 | 1.000 / 11.153 | 0.786 / 0.000 |
| drop 2024 | **0.000** / 4.097 | **0.000** / 0.006 |
| drop 2025 | 0.750 / 9.194 | 0.765 / 0.000 |

- **PJM T-R1a FAIL→PASS flip: holds 2/3 folds ✓** (fails only drop-2024).
- **MISO T-R2a FAIL→PASS flip: holds 2/3 folds ✓** on recall; the
  false-retire PASS holds **3/3**.
- The shared drop-2024 recall failure is a real, named finding — **wave
  concentration**: the model executes its entire coal wave at the single
  2024 screen (decided at the 2022-bridge screen off the 2021 loss year +
  L=3), where reality spread exits 2021–2025. It is the D=0 + synchronized-
  onset signature, NOT a fuel inversion; it is year-timing, not composition.
  Routed as an open observation for FF-2C (a decision-staggering mechanism
  would need its own identification — none exists on disk; rule 21 forbids
  inventing one).

## 6. §2.1 flip-gate items 3–4 per ISO — MEASURED (the FF-2C input)

| # | Gate item | PJM @ R-NEW | MISO @ R-NEW |
|---|---|---|---|
| 3 | Position | **PASS-leaning-OPEN.** 2025 = 0.989, abs err 0.018 from the auction's 1.007 — in the ±0.028 band, AND for the first time carried by a real exit mechanism (11.5 GW coal wave + entry relief), not entry-relief alone (the D1=3 qualified-PASS's "inert exit" caveat is closed). 2023 stays OUT ($0 at 1.145) ✓. **Remaining miss: 2024 pays 40.2 vs real 10.6** — the all-in-2024 wave concentration overshoots the short direction one year early. | **FAIL/OPEN — degraded.** 2025 = 1.0795, pays $0 vs the 243.3 cap-clearing (D1=1: 1.035/24.5; D1=3: 1.068/$0). With gas_st correctly retained and coal at 8.05 GW, the fleet stays longest of the three legs: the missing ~7 GW of real exits (coal −2.9, gas_ct −2.4, oil −0.5, gas_cc −0.5) sit in classes whose screen margins CLEAR the bar — a revenue-level residual (BLK-6/BLK-9/RD-4), not an order/composition defect. |
| 4 | Skill | **PASS-qualified.** Recall 0 → 76% (vs fixed BEFORE); T-R10 clean; false-retire IS-2020 4.652 GW, ALL of it coal overshoot (no wrong fuel) — worse than BEFORE's 0.0 (which had zero economic exits at all). The overshoot is level, not composition. | **PASS.** Recall 0 → 76%; false-retire 0.000 (raw AND IS-2020) — strictly no degradation; gas_cc additions fall 9→0 toward actual 3.9; the inversion instrument (T-R10) clean. Wind non-response unchanged (entry-side lane). |

Items 1/2/5 are D1/R-NEW-invariant (unchanged from RC-1A/RC-2B: PJM 1-2
PASS, MISO 2 PASS-leaning-OPEN resolved, 5 PASS).

## 7. BLK-10 re-measure

| leg | backstop fired |
|---|---|
| PJM R-NEW | **2,353 MW gas_ct (2025)** — partial re-fire, wave-coupled: between D1=1's 6,428 MW (full wave) and D1=3's 0 (no wave). Confirms the D1 finding that the backstop over-fire is coupled to the exit wave; at the R-NEW wave size the adequacy deficit is real but smaller. No sizing rework indicated beyond the wave-concentration observation (§5). |
| MISO R-NEW | **0 MW** — the entry-cap holds the fleet at adequacy, no backstop. |

## 8. Honest limits & open blockers (stated in advance, memo §3.6)

- The redesign fixes ORDER and COMPOSITION races, not signal level: a
  surviving gas_st-type false-retire routes to the revenue lane
  (BLK-6/BLK-9, RD-4), never a fuel patch.
- PJM in-window coal recall may not recover under ANY admissible in-window
  rule (pre-window decisions + the RD-4 bar question) — measured, that is a
  finding about the window, not the rule.
- A residual closable only by an unidentified value is an open blocker,
  written up, NOT a parameter (rule 21).

## 9. Push-transport incident (rule 27) — STOP-THE-LINE record

TO FILL before commit: exact record of the push_files size-limit incident,
the branch state, and the restoration.

---

*Produced 2026-07-18 (FF-1A). No holdout year solved or scored; 2022 bridged;
no backcast artifact touched; nothing tuned to a residual.*
