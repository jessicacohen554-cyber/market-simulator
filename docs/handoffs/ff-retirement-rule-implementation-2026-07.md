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

TO FILL (T-R1a–e, T-R2a–c, T-R3a–d, T-R4, T-R5-inv, T-R7, raw AND IS-2020).

## 5. T-R10 no-inversion guard + LOYO (memo §4, pre-registered)

TO FILL (T-R10a first-mover gate; T-R10b >1 GW composition corollary; LOYO
folds within 2023–2025, ≥2/3 must hold; verdicts per ISO-window).

## 6. §2.1 flip-gate items 3–4 per ISO — MEASURED (the FF-2C input)

TO FILL.

## 7. BLK-10 re-measure

TO FILL (backstop MW fired per leg; the gap-register row requires this before
any sizing rework).

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
