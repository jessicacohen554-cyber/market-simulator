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

*(Sections below were filled AFTER the pre-registered work ran, in order, as
produced.)*

## 2. The regeneration and its gates — all PASSED

The §1.3 recipe ran verbatim at this head (`regenerate_clean.py` full, then
the solve): solved `[2021, 2023, 2024, 2025]`, bridged `[2022]`, exit 0,
runtime **`cache_key=816031a3308cccde` exactly as pre-registered** (zero
`src/market_sim/` diffs exist between the FFR-9A merge `c96f64f` and this
head, checked before launch). Fresh out-dir
`results/hindcast/ercot-2021-2025-t1ff-armr-ffr9b-regen`; NOT registered in
any namespace, per charter.

* **Reproduction gate: PASSED with ZERO field diffs** — a deep compare of the
  regenerated `score.json` against the surviving registered treated arm's
  (`…-ffr9a-storageseed`) over EVERY block (additions, additions_cod_basis,
  additions_basis, retirements, co2, …; `generated_utc` excluded) is empty.
* **R1: PASSED EXACTLY.** The regenerated evolution ledgers' decision-grain
  rows reproduce the §1.2 hypothesis table CELL-FOR-CELL to 0.1 MW
  (committed extract: `docs/handoffs/ffr-9b/evolution-ledger-extract.json`;
  the ledgers themselves sit under the gitignored hindcast scratch family,
  `.gitignore:550`).
* **R2/R3: the replay identity holds everywhere.** The probe
  (`scripts/probes/ffr9b_entry_screen_replay.py`, record
  `docs/handoffs/ffr-9b/entry-screen-replay.json`) re-invoked both entry
  screens per step with the bundle's own inputs: replayed build MW ==
  ledger decided MW for every (step, tech) INCLUDING storage, under BOTH
  reserve-leg bounds, and the margin ORDER is identical under both bounds at
  every step — every binder label below is reserve-leg-robust. (Protocol
  note, §1.4 R3's anticipated degradation: the true reserve leg — the prior
  solved year's realized post-solve ORDC adder — is not recoverable offline
  because hourly fleet availability is not persisted; the two bounds bracket
  it and no sign, rank, or MW differs between them.)
* **R4: storage confirmed** — replay == ledger (5,000 = the annual cap in
  2022/2023/2024; 0 in 2025 with every storage tech unprofitable at the
  into-2025 signal). The §1.2 label "QUEUE−pending (still profitable)" for
  solar-2025 is confirmed as written.
* Label nuance for later readers: the screen's own `binding_cap` string
  labels a queue-cap-minus-pending clip as `iso_budget` whenever the netted
  cap sits below the full per-tech cap (`new_entry.py:1454-1458` compares
  against the FULL cap). The §3 table uses the arithmetically-resolved
  binder; the probe JSON records both.

## 3. THE ANSWER — what binds, per tech per year, with megawatts attributed

The charter's question, answered from the ledger + the identity replay. The
screen prices everything through four hot/cold regimes: into-2022 mean
$192.83, into-2023 $431.54, into-2024 $309.69, into-2025 $31.20 (the §1.1
lookahead signal). **At the three hot screens EVERY candidate clears its
fixed cost by 9–24× (margins $166–$3,503/kW-yr vs $147–$818/kW-yr CONE) —
economics differentiate nothing there; the caps are the entire allocator.**
Economics bind only (i) through the margin ORDER (which tech drains the
shared 12 GW budget first — wind ranks LAST at all three hot screens) and
(ii) at the cold into-2025 screen, which kills everything except solar.

Decision-grain MW by evolution step (ledger; margins $/kW-yr from the
replay, r=None leg):

| step | wind | solar | gas_cc | gas_ct | nuclear_smr | storage |
|---|---|---|---|---|---|---|
| 2022 | **482.4** — ISO-BUDGET residual (12,000 − 11,517.6; margin $166, ranked 5/5) | **4,946.6** — GROWTH LADDER (2×2,473.3 seed; margin $908) | **3,000** — QUEUE CAP (margin $1,336, rank 1) | **1,571** — GROWTH LADDER (2×785.5 seed; margin $1,290) | **2,000** — QUEUE CAP (margin $702) | **5,000** — ANNUAL CAP |
| 2023 | **4,517.6** — QUEUE−pending (5,000−482.4; margin $557) | **53.4** — QUEUE−pending (5,000−4,946.6; margin $2,420) | **0** — pending-BLOCKED (3,000 pending) | **1,429** — QUEUE−pending (3,000−1,571; margin $3,461) | **0** — pending-BLOCKED (2,000 pending) | **5,000** — ANNUAL CAP |
| 2024 | **482.4** — QUEUE−pending (5,000−4,517.6; margin $468) | **4,946.6** — QUEUE−pending (5,000−53.4; margin $2,131) | **3,000** — QUEUE CAP, freed by COD (margin $2,455) | **1,571** — QUEUE−pending (3,000−1,429; margin $2,423) | **2,000** — QUEUE CAP, freed (margin $1,625) | **5,000** — ANNUAL CAP |
| 2025 | **0** — ECONOMICS (margin −$30; 4,517.6 of cap free, untaken) | **53.4** — QUEUE−pending; the ONLY profitable merchant (+$14.8) | **0** — pending-blocked AND unprofitable (−$26) | **0** — ECONOMICS (−$12; 1,429 free) | **0** — ECONOMICS (−$570) | **0** — ECONOMICS (all techs) |
| **decided total** | **5,482** | **10,000** | **6,000** | **4,571** | **4,000** | **15,000** |
| actual COD 2021–25 | 12,663 | 25,080 | 244 | 3,692 | 0 | 13,691 |

Structural mechanics the table exhibits (each at ledger grain, the ERCOT
instance of the FFR-4A/5C general law):

* **The C/L alternation.** With the 2-yr COD lag armed and
  `entry_pipeline_aware_signal` OFF, the pending stock nets against the
  annual flow caps, so every tech alternates cap-year/blocked-year —
  effective long-run rate = cap/2. The ISO budget saturates at exactly
  12,000 MW in 2022 and 2024 (in 2024 the freed-caps sum ties the budget at
  12,000.0 — a degenerate double-bind) and idles at 6,000 in 2023.
* **The ladder ratchet works as cited** (ReEDS ×2): gas_ct 1,571 →
  3,142 after its first build; solar 4,946.6 → 9,893.2; wind 6,943.4 →
  9,035.2 — after year 1 the ladder never binds again; the static queue
  caps take over.
* **The into-2024 screen is pipeline-blind** (dump-proven, §1.1/FFR-5C):
  its solar potential maxes at exactly 4,864 MW — the vintage pool — while
  4,946.6 MW of committed COD-2024 solar sits invisible in the pipeline.
  The screen prices 2024 as if the capacity it already decided didn't
  exist, overshoots, and re-decides the opportunity (the cobweb).

### 3.1 Per-tech attribution of the gap vs reality

**Solar (10.0 vs 25.08 GW; −15.1).** Binder chain: ladder seed (4,946.6)
year 1, then queue-cap-minus-pending ever after; NEVER economics (profitable
at every screen including into-2025). The C/L alternation alone costs
~9.8 GW over the window (blocked 2023; 53 MW crumbs where 4,947 was free a
year earlier): with the alternation removed the same caps and margins
support ≈ 19.9 GW. The rest of the gap is the cap LEVEL itself — actual
solar CODs ran 7.29/7.74 GW/yr in 2024/2025, 1.5× the model's 5.0 GW/yr
queue cap — plus the pre-vintage cohort (below). Category: **(a) caps**,
two layers deep, with zero economics content.

**Wind (5.48 vs 12.66 GW; −7.2).** The ONLY tech ever clipped by the shared
ISO budget: it ranks LAST on margin at all three hot screens (shape-aware
capture on the scarcity-priced signal), so in 2022 it receives the 482.4 MW
residual after gas_cc + gas_ct + nuclear_smr + solar take 11.5 GW. Of the
12 GW hot-year budget, **6.57 GW/yr goes to thermal + SMR — techs whose
actual additions were ≈ 0.06 GW/yr** — and that allocation, plus the C/L
alternation, plus the into-2025 economics kill (−$30/kW-yr with 4.5 GW of
cap free) is the whole wind story. Note the reality contrast cuts BOTH
ways: actual wind never exceeded 3.95 GW/yr — BELOW the model's own caps —
and was falling through 2023–25 (1.5–1.7 GW/yr), so the model's caps are
not what reality's wind was pushing against; the model's wind gap is
**(b) economics-rank + (a) budget-crowding**, and part of the residual is
rule-1-honest: 2021–22 actual wind (7.8 GW) was largely PTC-vintage
safe-harbor construction decided before the 2020 vintage — a driver the
model's information set excludes by design (see F-5).

**gas_cc (6.0 vs 0.244 GW; +5.76 — the over-entry).** Pure **(b)
economics, screen-level overshoot**: gas_cc ranks FIRST at every hot screen
(margins $1,336/$3,503/$2,455 per kW-yr = 9–24× its $147.2 CONE) and
builds its full 3.0 GW queue cap in both freed years. At the
replica-at-measured-prices levels (FFR-6A/9A: 2024 $86.7, 2025
$76.4/kW-yr, BELOW the $147.2 CONE) **gas_cc entry would clear in neither
scored year — the entire 6.0 GW is attributable to the screens' price-level
overshoot**, which is itself the missing-VRE feedback (FFR-9A §3.4) plus
the pipeline-blind signal (F-2). The over-entry is DOWNSTREAM of the VRE
under-build: one mechanism, now with entry-side evidence. No cap-side fix
is warranted (3.0 GW/yr ≈ the demonstrated CC build era); deflate the
screen and CC entry dies on its own.

**nuclear_smr (4.0 vs 0 GW).** Category **(c) eligibility**: `nuclear_smr`
sits in the always-eligible `_NEW_ENTRY_TECHS` tuple with NO
availability-year gate (spec §5.3 documents "the classic four … always
eligible"), while ATB itself costs SMR from 2030 only. At 0.90 CF its
$103.96/MWh LCOE clears any screen with mean ≳ $104 — all three hot
screens — and it enters at the 2.0 GW nuclear queue cap, which carries NO
growth ladder (no windowed 2011–2020 COD ⇒ rule-25 no-cap fallback). A
2022-decided, 2024-commissioned ERCOT SMR is not a real object; its 4.0 GW
also displaces exactly that much of the shared budget in the years wind is
budget-clipped.

**gas_ct (4.57 vs 3.69 GW; +0.88).** The closest tech, and the ladder's
success case: the measured seed (0.785 GW = ERCOT's 2011–2020 max CT year)
holds year 1 to 1,571 MW while actual CT additions ran 0.6–1.2 GW/yr;
after the ratchet the queue-minus-pending governs; into-2025 economics
kill it (−$12/kW-yr) exactly when actual 2025 CT additions fell to
0.19 GW. Category: **(a) ladder then queue−pending, (b) at the cold
screen** — and approximately right.

**storage (15.0 vs 13.69 GW decided; timing 3.7×→1.9× ahead).** The
annual 5,000 MW cap (`STORAGE_ANNUAL_BUILD_CAP_MW`) binds in all three hot
build years — with ≥2 of 3 techs profitable, merit order + the 0.6 share
cap fill the budget exactly — then the into-2025 signal kills the whole
stack (0 built, ceiling irrelevant at 15.2 of 45 GW). Two notes for the
repair lane: (i) in THIS posture the stack is **arbitrage-only**
(`as_revenue_enabled=False`; capacity value $0 in energy-only ERCOT) — the
AS slice the spec calls ~85 % of 2023 ERCOT battery revenue is absent, yet
the cap still saturates at hot screens; at measured price levels the
arbitrage-only stack would likely clear nothing, so **the cap is currently
doing the work reality's AS revenue does** — a compensation to unwind, not
keep; (ii) the cap-saturated flat 5/5/5/0 profile vs the actual
0.6→1.3→2.0→4.1→5.6 ramp is the FFR-9A §3.1 timing finding, unchanged.
Category: **(a) cap** at hot screens, **(b) economics** at the cold one.

### 3.2 The window/vintage asymmetry (F-5, applies to every VRE row)

The model's first possible merchant COD is 2024 (first decision step 2022 +
2-yr lag), while **18.4 GW — 33 % — of the actual 2021–25 CODs landed in
2021–23**, decided before the 2020 vintage on information (signed IAs,
PTC safe-harbor vintages) the hindcast's information gate deliberately
excludes. The D-9(ii) decision-basis scoring absorbs part of this (model
decisions are counted when made), but the per-tech mix comparison
inherits it: no admissible screen repair can reproduce the 2021–23 cohort;
only the committed-queue channel can (FFR-5E, §4 R-d).

## 4. Repair candidates, each with its rule-13 pre-assessment (NO REPAIR PERFORMED)

Named for the manager's repair charter; none is implemented, armed, or
tested here.

* **R-a — arm `entry_pipeline_aware_signal` (FFR-5C) in the T1-FF
  posture.** Fixes F-1 (restores every per-tech rate from C/2 to C: the
  netting relocates out of the flow caps) AND F-2 (the pro-forma prices
  its own committed pipeline, deflating the into-2024-class overshoots).
  Rule-13: clean — a relocation with zero new parameters, built and gated
  (default off), pipeline rows are model state that regenerates forward
  and responds to conditions. Matrix cell ERCOT = `U` (untested; the MISO
  measurement was cap-arithmetic only). Test sketch: paired arm on the
  ffr9a-storageseed recipe ± the flag; expected signatures — solar
  ~5/5/5/· with the 53-MW crumbs gone, the alternation killed
  (the FFR-5C MISO-wind law: mean C not C/2), into-2024 screen deflates
  (pipeline visible), gas_cc entry falls WITH the deflation. Score
  leave-one-year-out within 2023–2025 before any promotion (rule 22).
* **R-b — gate SMR eligibility on an availability year.** Move
  `nuclear_smr` under the `_EMERGING_AVAILABLE_YEAR` mechanism (or
  equivalent) with an ATB-cited availability year (ATB costs new nuclear
  from 2030). Rule-13: clean — a published availability year, forward-
  reproducible, condition-responsive (a config field like the existing
  `ccs_available_year` family). Removes 4.0 GW of phantom SMR and frees
  the budget MW that crowd wind. Needs a `ScenarioConfig` field (or
  constants entry) → matrix row in the same PR (rule 28c), the repair
  session's to design.
* **R-c — re-derive the solar queue cap from the post-2020 record (only
  AFTER R-a).** `QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"] = 5.0` sits below
  actual 2024/2025 solar CODs (7.29/7.74 GW). Rule-23 admissible ONLY as a
  re-derivation from updated source data (the EIA-860 2025 record of
  demonstrated throughput), never from the residual; and it is NOT the
  first-order fix — R-a alone roughly doubles effective solar throughput.
  Assess after R-a's paired arm.
* **R-d — arm the FFR-5E procurement channel (`vre_procurement_additions_enabled`)
  at vintage 2020.** The ONLY admissible instrument for the 18.4 GW
  pre-vintage cohort (§3.2): proposed-sheet-at-vintage rows with
  construction-committed status, admissibility already adjudicated
  (D-18(a)); the FFR-5E-H "netting untested" caveat does not carry to
  ERCOT, where the merchant screen demonstrably decides at every hot
  screen, so the netting would be exercised. Expected magnitude at vintage
  2020 is the repair lane's first read (the shipped-vintage ERCOT pipeline
  was 6,575 MW; the vintage-2020 sheet's committed 2021–23 cohort is the
  quantity that matters).
* **R-e — the gas_cc over-entry needs NO dedicated lever.** It is the
  screens' price-level overshoot monetized by the first-ranked tech; R-a +
  R-d (+ the FFR-9A-attributed VRE trajectory repairs generally) deflate
  the screens, and at measured-replica levels CC clears nowhere. A CC cap
  cut or a CC-specific economics patch would be treating the symptom
  (rule 19: the phenomenon's mechanism is the screen level, one mechanism).
* **Rule-1 statement for wind.** Part of wind's gap is reality building on
  drivers the model lacks by design: pre-vintage PTC-safe-harbor decisions
  (R-d's cohort) and post-2022 actual wind FALLING below every model cap —
  after R-a/R-d, the residual wind gap is expected to be an economics-rank
  object (capture at the model's scarcity-shaped signal), and should be
  re-measured before any wind-specific lever is invented.

**NO-REPAIR-PERFORMED STATEMENT.** This session changed no solve path, no
`ScenarioConfig` field, no constant, no gate, no default; it performed no
tuning toward 55.4 GW or any other actual; the regeneration is
identical-recipe, unregistered, and produced zero new epoch. The only code
added is the offline replay probe (`scripts/probes/ffr9b_entry_screen_replay.py`).

## 5. Governance

* **Charter compliance.** Diagnose-only; FH-4-ERCOT not re-based (no epoch,
  no registration, no harness change). The FFR-9A registrations stand; the
  regeneration is noted here (§2) as the charter requires. One bounded
  re-solve spent, on the treated recipe, reproduction-gated with zero
  diffs.
* **Rule 22.** Solves {2021, 2023, 2024, 2025} + the 2022 bridge; holdout
  freeze ACTIVE at launch; no marker spent; no out-of-training year solved
  or scored; the bridged 2022 was never solved and no 2022 market data was
  read (the 2022 EVOLUTION ledger — fleet bookkeeping of a bridge year —
  is read, as FFR-9A's R1 probe already did).
* **Rule 28 duty (b).** No new field, no cell verdict moved (diagnosis, not
  a mechanism test). Evidence citations added to the `entry_dampers` and
  `entry_pipeline_aware_signal` rows (the ERCOT ledger-grain instance of
  the C/L law and the dump-proven pipeline-blind signal); cells unchanged.
* **Rule 27.** Fable. All edits local on-disk bytes; no ≥300-line file
  pushed from regenerated content; pushes verified by branch state.
* **Artifacts committed with this handoff:** the regen bundle's slim files
  (score.json + 4 screen dumps + meta/run_config/config.yaml), the ledger
  extract + replay record under `docs/handoffs/ffr-9b/`, the scorer's
  report (`docs/hindcast-reports/ercot-2021-2025-t1ff-armr-ffr9b-regen-2026-08-09.md`),
  and the probe script.
