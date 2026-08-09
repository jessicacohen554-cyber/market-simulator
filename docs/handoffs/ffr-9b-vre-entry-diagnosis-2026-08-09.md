# FFR-9B — diagnose the VRE entry under-build (and gas_cc over-entry) in the ERCOT T1-FF posture

**Session.** FFR Wave 9, DIAGNOSE-ONLY lane (manager dispatch Addendum AH.4,
under the owner-re-opened D-21(a) completion mandate). Branch
`claude/ffr-9b-vre-entry-diagnosis-ouzvi0`, off `origin/main` `51d4e98`.
Model: Fable (rule 27-adjacent; capacity-evolution reading).

**Charter.** Decompose, per tech per ledger year 2021–2025, WHAT BINDS the
entry decision in the ERCOT T1-FF posture of record
(`ercot-2021-2025-t1ff-armr-ffr9a-storageseed`, FFR-9A §3.5): treated
additions decision basis 45.1 GW vs 55.4 actual, with solar 10.0 vs 25.1 and
wind 5.5 vs 12.7 GW, gas_cc 6.0 vs 0.244 (FFR-8B §2.3), under screens whose
per-fuel margins reach ~26× the replica-at-measured-prices columns
(FFR-9A §3.4). For each (tech, year): (a) an entry CAP (which one, at what
value, cited); (b) the entry ECONOMICS; (c) an eligibility/pipeline gate;
(d) something else — with the config/constants citation and the megawatts
attributed. **DIAGNOSE-ONLY: NO repair, NO code change to any solve path, NO
new ScenarioConfig field, NO epoch.** FH-4-ERCOT runs in parallel; this lane
must not re-base it. The repair charter is the manager's next dispatch.

**Rule-1/13 posture.** The actual build (55.436 GW) is the reality benchmark,
never a target. If the diagnosis concludes the model's entry economics are
right and reality over-built on drivers the model lacks, that is the finding;
every candidate repair input carries a rule-13 admissibility pre-assessment.

---

## 1. PRE-REGISTRATION

*§1 was written and committed BEFORE the regeneration solve was launched and
before any regenerated ledger was read. Honest sequencing note: the FFR-9A
arms' SURVIVING bundle files — `score.json` and the four
`screen_signal_diag_*.npz` per arm (this container retained
`results/hindcast/`, contrary to the charter's died-with-the-container
assumption) — plus the committed `docs/handoffs/ffr-9a/*.json` probe records
were read before this prereg; they are the registered evidence base the
charter directs this lane to. What is pre-registered here is (i) the derived
per-tech-per-year HYPOTHESIS table those aggregates pin, (ii) the
regeneration that tests it at ledger grain, and (iii) the offline
margin-replay reads. Nothing in §1 changes after the regeneration runs.*

### 1.1 The mechanism inventory (from code, at this head)

The economic-entry allocator (`model/capacity_evolution/new_entry.py::
apply_economic_new_entry`) screens candidates
`(wind, solar, gas_cc, gas_ct, nuclear_smr)` + gated emerging techs, ranks
positive margins highest-first, then allocates MW through FOUR independent
cap layers (build = the min; first exhausted layer is the binder):

| layer | value (ERCOT) | citation |
|---|---|---|
| ISO annual queue budget, shared across techs in margin order | **12 GW/yr** | `config/capacity_market.py::QUEUE_CAP_GW["ERCOT"]` (CDR throughput) |
| per-tech annual queue cap | wind **5.0**, solar **5.0**, gas_cc **3.0**, gas_ct **3.0**, nuclear **2.0** GW/yr | `QUEUE_CAP_PER_TECH_GW["ERCOT"]`; `nuclear_smr → nuclear` via `_QUEUE_CAP_GROUP` |
| growth ladder (armed: `entry_rate_limits=True`) = 2.0 × prior-max annual build, seeded from vintage-2020 EIA-860, rising endogenously with model builds | seeds (2011–2020 max, GW/yr): wind 3.472, solar 2.473, gas_cc 2.570, gas_ct 0.785 → ladder caps **6.943 / 4.947 / 5.140 / 1.571**; nuclear has NO windowed COD ⇒ **NO ladder** (rule-25 neutral fallback) | `entry_config.ENTRY_GROWTH_LIMIT_MULTIPLE=2.0` (ReEDS hard bound), `data/build_throughput.py::max_annual_build_gw_by_tech`, `runner.py:1370–1380, 1688–1694` |
| pending-stock netting (armed: `entry_commissioning_lag=True`, `entry_pipeline_aware_signal=False` default) — decided-but-uncommissioned pipeline MW subtracted from the per-tech cap AND the ladder | COD lag **2 yr uniform** (`ENTRY_COD_LAG_YEARS`, LBNL IA→COD median); commissioning (evolve step 4.5, `evolve.py:673–704`) runs BEFORE the entry screen, so a tech's cap frees exactly when its 2-year-old cohort lands | `new_entry.py:1400–1404, 1420–1441` |

Storage enters through a SEPARATE stack (`model/storage.py::
apply_storage_new_entry`, spec §5.5): budget =
min(`STORAGE_ANNUAL_BUILD_CAP_MW["ERCOT"]` = **5,000 MW/yr**, ceiling
45,000 − existing); per-tech share cap 0.6 × budget; **in-year
commissioning, no COD lag, no pending netting, outside the 12 GW ISO
budget**; value stack = duration-window arbitrage + AS credit
(`as_revenue_per_mw_yr("storage", existing_mw, …)`, saturating on the
existing fleet; `ercot_storage_as_endogenous=False` in this posture) +
capacity value (**$0 in ERCOT** — energy-only `MARKET_DESIGN`).

Economics plumbing in this posture (`capacity_screen_unified_lookahead=True`,
`capacity_screen_scarcity_restoration=True`):

* The screen's price vector is the unified-lookahead pro-forma
  (`runner._lookahead_reprice_signal`): the entering year's known net load
  searchsorted into the current fleet's time-mean merit stack + the
  published ORDC curve on committed reserves — returned `(n_zones, T)` with
  **identical rows** (system-wide). Recorded per screen in the
  `screen_signal_diag_<solve>_for_<entering>.npz` dumps
  (`price_base_usd_mwh + adder_usd_mwh`).
* VRE revenue is SHAPE-AWARE (plan §6 CX-6c): build zone's hourly CF dotted
  against that zone's row of the signal (all rows equal ⇒ shape-aware,
  basis-free). Solar LCOE nets the ITC (`ira_itc_solar`, cliff
  `ira_wind_solar_last_year`); wind nets the levelized PTC
  (`wind_ptc_levelized_per_mwh`). Cost side stays on `base_cf`
  (wind 0.38, solar 0.27; `NEW_ENTRY_COSTS`).
* Thermal (gas_cc/gas_ct) revenue = Σ_t max(price_t − vc, r_t) with r = the
  reserve signal; under `screen_reserve_value_enabled=True` (default) and
  `ercot_thermal_as_endogenous=False`, r = the PRIOR SOLVED YEAR's realized
  post-solve ORDC adder (`runner.py:3482–3484`) — an energy-leg (lookahead
  into Y+1) vs reserve-leg (realized year Y) timing asymmetry, noted. The
  hourly reserve tier suppresses the annual AS credits (rule 19). Capacity
  payment $0 (ERCOT energy-only).
* `nuclear_smr` is in the ALWAYS-ELIGIBLE `_NEW_ENTRY_TECHS` tuple
  (`new_entry.py:108–114`) — unlike the `_EMERGING_AVAILABLE_YEAR` techs it
  carries **no availability-year gate**. ATB costs SMR from 2030 only
  (`NEW_ENTRY_COSTS` comment); the screen will happily "build" one in 2022.
* Announced/planned additions (step 4, `load_planned_additions`) are
  forecast-mode EIA-860 pipeline; the T1-FF vintage-2020 posture carries
  none of the 2021+ actual COD wave — all VRE/storage/thermal entry beyond
  the vintage fleet is endogenous through the screens above.

### 1.2 The derived hypothesis table (committed before the regeneration)

The surviving aggregates over-determine the treated arm's per-year
decisions. Constraints used: (i) five per-tech decision totals
(score.json `additions.by_tech`: wind 5.482 / solar 10.0 / gas_cc 6.0 /
gas_ct 4.571 / storage 15.0; `model_total_gw` 45.053 ⇒ +4.0 GW unscored),
(ii) the cod-basis block (wind 5.0 / solar 5.0 / gas_cc 3.0 / gas_ct 3.0 /
storage 15.0), (iii) `decided_in_window_cod_after_window_gw`
(solar 5.0 / gas_cc 3.0 / gas_ct 1.571 / nuclear_smr 2.0 / wind 0.482 =
12.053), (iv) the committed R1 storage trajectory (0 / 5,000 / 5,000 /
5,000 / 0 by ledger year), (v) the cap layers of §1.1, (vi) 14 decided
pipeline rows. The UNIQUE reconstruction consistent with all of these
(every aggregate reproduced to 3 decimals):

| decision step (screen) | wind | solar | gas_cc | gas_ct | nuclear_smr | Σ merchant | storage |
|---|---|---|---|---|---|---|---|
| 2021 (base year — no evolution) | — | — | — | — | — | — | — |
| 2022 (into-2022, mean $192.83) | **0.482** = 12 − 11.518 ISO-BUDGET residual | **4.947** LADDER (2×2.473) | **3.0** QUEUE | **1.571** LADDER (2×0.785) | **2.0** QUEUE | **12.0 = ISO budget SATURATED** | **5.0 CAP** |
| 2023 (into-2023, mean $431.54) | **4.518** QUEUE−pending (5−0.482) | **0.053** QUEUE−pending (5−4.947) | **0** pending-BLOCKED | **1.429** QUEUE−pending (3−1.571) | **0** pending-BLOCKED | 6.0 | **5.0 CAP** |
| 2024 (into-2024, mean $309.69) | **0.482** QUEUE−pending (5−4.518) | **4.947** QUEUE−pending (5−0.053) | **3.0** QUEUE (freed) | **1.571** QUEUE−pending (3−1.429) | **2.0** QUEUE (freed) | **12.0** (budget + freed caps bind simultaneously — degenerate) | **5.0 CAP** |
| 2025 (into-2025, mean $31.20) | **0** ECONOMICS (4.518 cap free, not taken) | **0.053** QUEUE−pending (5−4.947; still profitable) | 0 pending-blocked | **0** ECONOMICS (1.429 free, not taken) | **0** ECONOMICS | 0.053 | **0 ECONOMICS** |
| totals | 5.482 | 10.0 | 6.0 | 4.571 | 4.0 | 30.053 | 15.0 |

Checksums this table reproduces exactly: all five decision totals; the
cod-basis block (2022+2023 decisions, cod 2024/2025: wind 0.482+4.518=5.0,
solar 4.947+0.053=5.0, gas_cc 3.0, gas_ct 1.571+1.429=3.0); the
after-window split 12.0 (2024) + 0.053 (2025) = 12.053 per tech; the
in-window sum 18.0 = EXACTLY Σ(per-tech queue caps); `model_total` 45.053 =
41.053 + 4.0 nuclear_smr. Independent corroboration: the 2024_for_2025
dump's VRE potentials imply entering-2025 pools of wind ≈ 32.5 GW / solar
≈ 9.86 GW = vintage (27,541 / 4,864 MW, FFR-3V) + exactly this table's
commissioned additions.

**The ONE free assumption:** wind ranked LAST among the five positive
margins at the into-2022 screen (required for wind's 0.482 to be the ISO
budget residual). Testable by read R3; everything else is forced by cap
arithmetic.

Control-arm note (not the object of record): the same method leaves the
control's late-step solar split (2.482 after-window) under-determined from
aggregates alone — recorded as a residual open cell, resolved only if the
control were regenerated (it is not; one bounded re-solve is licensed and
it is spent on the treated arm).

### 1.3 The regeneration (the licensed ONE bounded re-solve)

The committed artifacts pin totals and cohorts but not the ledger-grain
decided rows, margin ordering, or per-step binder labels. Per the charter's
license, ONE identical-recipe regeneration of the **treated** arm, VERBATIM
at this head (the FFR-9A fix is merged; today's head reproduces the treated
code state):

```
uv run python scripts/regenerate_clean.py            # cold clean store, ~63–65 min
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9b-regen
```

* **Fresh `--out-dir`** (`…-ffr9b-regen`), never the surviving FFR-9A dirs —
  the D-13 same-key hazard: a shared dir would silently mix stale bundle
  files into the regeneration. The out-dir is not part of the config hash,
  so the arm content is unchanged.
* 4 LP years sequential (2022 bridged), rule 12. NOT registered — the
  FFR-9A registration stands; this regeneration exists only to read ledgers.
* **Bookkeeping**: the runtime `cache_key=` line is read and verified
  before believing any ledger path; expected `816031a3308cccde` (no
  registered field has moved since FFR-9A measured it — HOUSE-1 and
  subsequent merges are checked against the pinned-key regression by CI). A
  DIFFERENT key is diagnosed before proceeding, not explained away.
* **Reproduction gate (BY CONTENT):** the regenerated bundle's
  `score.json` `additions` / `additions_cod_basis` / `additions_basis`
  blocks must equal the surviving treated arm's byte-for-byte (field-wise
  deep compare). Failure is diagnosed before any decomposition read is
  believed.
* Holdout posture: solve years {2021, 2023, 2024, 2025} + 2022 bridge —
  training-tier + the enumerated hindcast seed year; freeze state read at
  launch; no marker spent, no out-of-training year approached, no file for
  2022 opened by any read.

### 1.4 Pre-registered reads (R1–R5)

* **R1 — ledger decided rows vs the §1.2 hypothesis table.** From each
  `evolution_<year>.json` (`entry_pipeline` events + decision-grain
  additions): the per-tech-per-year decided MW. PASS = the table exactly.
  Any cell that differs REPLACES the hypothesis (the ledger is the record;
  the table is the prediction) and the mismatch is reported at full
  magnitude.
* **R2 — binder attribution per (tech, year).** For each step, recompute
  each cap layer's remaining value from ledger state (queue cap − pending;
  ladder = 2 × running prior-max − pending; ISO budget consumed in the
  replayed margin order) and label the binder = the layer whose remaining
  equals the built MW (economics label when margin ≤ 0; budget label when
  the shared budget exhausts first). Degenerate ties (2024) reported as
  ties.
* **R3 — the margin replay.** Offline probe
  (`scripts/probes/ffr9b_entry_screen_replay.py`, new, probe-only — no
  solve-path change): re-invoke `apply_economic_new_entry` /
  `apply_storage_new_entry` per step with `screen_ledger` diagnostics ON,
  feeding the regenerated bundle's own inputs (the dump's price signal;
  prior-year realized adder as the reserve legs, as `runner.py:3482` wires
  them; ledger fleet/pool/pipeline/prior-max state; `resolve_annual_gas_price`;
  the clean store's CF profiles). **Identity check:** replayed per-tech
  build MW per step == the ledger's decided rows, exactly. If the identity
  holds, the replay's margins, ordering, and `binding_cap` labels are
  authoritative; if it fails, the failure is reported and the labels
  degrade to R2's arithmetic attribution. Margins are then read per tech
  per screen: (i) does ANY of wind/solar/gas_cc/gas_ct/nuclear_smr fail
  economics at the three hot screens (expectation: none — the caps are the
  entire allocator there); (ii) which techs fail at into-2025 (expectation:
  all but solar; storage's stack also fails); (iii) wind's rank at
  into-2022 (the §1.2 free assumption); (iv) the gas_cc margin
  decomposition (energy vs reserve-leg vs fixed cost) at every screen, the
  over-entry attribution.
* **R4 — storage binder confirmation.** The committed R1 trajectory
  already pins 5,000 = cap in 2022/2023/2024 and 0 in 2025; the replay
  reads the 2025-step storage margins to attribute the zero (economics at
  the into-2025 signal vs the ceiling/cap layers, expectation: economics).
* **R5 — the reality-side decomposition (rule-1 framing).** Against the
  actual per-tech additions (55.436 GW: solar 25.08, wind 12.663, storage
  13.691, gas_ct 3.692, gas_cc 0.244): which binding layer of §1.1 is
  COUNTERFACTUALLY responsible for each tech's shortfall (i.e., with that
  layer relaxed and everything else held, what would the screen have
  built), computed arithmetically from the replay margins — labelled a
  diagnostic decomposition, never a tuning target. Each implicated input
  then gets its rule-13 pre-assessment (§4).

### 1.5 What this lane will NOT do

No repair, no solve-path/code change beyond the additive probe script, no
new `ScenarioConfig` field, no epoch, no registration (hindcast or
backcast), no keeper contact, no matrix cell verdict move (citations only,
duty (b)), no tuning toward 55.4 GW or any residual, no bar re-levels, no
signal scaling. If a read surprises, it is recorded, not adjusted for. The
FFR-8B Phase-2 escalation stays escalated; FH-4-ERCOT is not re-based (the
regeneration is unregistered and its out-dir is quarantined from the
registry namespaces).

---

*(Sections below are filled AFTER the pre-registered work runs, in order,
as produced.)*
