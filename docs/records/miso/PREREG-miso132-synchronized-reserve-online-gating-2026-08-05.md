# PREREG miso-132 — SYNCHRONIZED-RESERVE ONLINE-GATING at MISO (`miso_reserve_online_gated`)

Session miso-132, 2026-08-05, branch `claude/miso-132-backcast-calibration-d8gen8`,
off `origin/main` at `b4581c49`. Keeper at entry:
**`2026-08-04-miso-127-onlinepmin`** (bundle `results/calibration/miso127_onlinepmin_B`),
determination **NOT-YET**, sole FAIL **C7 `COAL_PRB` 2025** (`cv_ratio` 0.347 vs the
0.50 gate), ledgered caveats 2/3 {C3a, C3c}. MISO holds **NO** `calibration-complete`
marker — rule 22 `[R-HOLDOUT]`: **2023–2025 only**, and this session neither solves,
scores, nor READS 2022 / 2019 / 2026 data.

**This document is pushed BEFORE any adjudicating statistic is computed.** Nothing
below is sized on a measured Δ. The lane is the miso-130 stamp (b) / miso-131 §3
**successor 1**, the only structural, hour-organizing, price-regime-immune candidate
left on the §5.4 queue.

---

## §0 Contamination disclosure (every previously-measured number this session has read)

The session read, before writing this file: CLAUDE.md; the §5.4 queue stamps
miso-131 / miso-130 / miso-129; `FINDING-miso130-c7-night-regime-2026-08-05.md`;
`FINDING-miso131-granularity-inert-at-class-grain-2026-08-05.md`; the keeper bundle's
`run_config.json` / `meta.json` / `class_hourly_2025.parquet` **schema** (columns only);
`model/reserves/spec.py`, `model/lp/reserve_rows.py`, `data/reserve_requirements.py`.

Numbers already in hand (all from those documents, none recomputed here):

* C7 `COAL_PRB` `cv_ratio` **0.529 / 0.514 / 0.347** (2023/24/25), gate 0.50; the needed
  move is **×1.447** on 2025.
* miso-128's factorisation of the 2025 failure: `R_tot` **0.952**, `R_dfrac` **0.354**,
  i.e. the defect is the *organisation* term, and `R_tot` has no room.
* July `COAL_PRB` model−actual night (h0–5) surplus **+2,276 / +2,204 / +3,454 MW**;
  July 2025 daytime (h10–18) **matched** at +141 MW.
* July night price bias **+$7.0–8.7/MWh** in all three years; the July-2025 monthly
  load-weighted miss −$8.24 (≈$5.2 C3c-ledgered >$200 tail, ≈$3.1 body).
* miso-130 §6(b): `_miso_design` sets **no** `online_gated`; the RBDC requirement runs
  ≈2.5–2.7 GW every hour of 2025 and may be backed entirely by **idle** capacity.
* The gas-commitment-bridge pool census (0 plants in 2024/2025) — irrelevant to this
  lane, recorded so it is not mistaken for new evidence.

**Nothing in the sizing screen (§2) or the A/B (§3) has been computed.** The
identification (§1) is a *published market-design* reading; its MW magnitudes are
measured for the first time under the §2 bars.

---

## §1 IDENTIFICATION FIRST — the online portion from PUBLISHED requirements only

The charter's binding prerequisite (miso-130 stamp (b)(i)): the online (spin+reg)
portion of MISO's Operating Reserve comes from published requirements, **never** the
residual. It does, and the split is **definitional**, not a share fitted to anything.

### 1a. The published qualification rule (primary source)

MISO **BPM-002 (Energy and Operating Reserve Markets)**, §4.2.1.1.2 *Real-Time Resource
Eligibility* (Regulation) and §4.2.1.2.2 *Real-Time Resource Eligibility* (Spin):

> **Regulation** Qualified Resources that are eligible to provide Regulation Service in
> the Real-Time Energy and Operating Reserve Market are: **synchronized** Generation
> Resources; **synchronized** DRRs-Type II; and available External Asynchronous
> Resources …

> **Spin** Qualified Resources that are eligible to provide Spinning Reserve in the
> Real-Time Energy and Operating Reserve Market are: **Synchronized** Generation
> Resources; Uncommitted DRRs-Type I with a Contingency Reserve Status of "**online**";
> **Synchronized** DRRs-Type II; and available External Asynchronous Resources …

§4.2.1.3 then registers Regulation/Spin resources as Supplemental Qualified Resources —
Supplemental is the product an **offline** resource may provide, which PJM's public
cross-RTO survey states directly for MISO: "MISO does qualification testing to provide
**offline supplemental reserve**, but not for synchronized reserves."

**Therefore: the ONLINE (synchronized) portion of MISO's Market-Wide Operating Reserve
Requirement is exactly `Regulating Reserve + Spinning Reserve`.** Supplemental is the
part idle capacity may back. This is a product-definition boundary published in the
BPM, not a share estimated from anything the model produces.

### 1b. The MW, in the backcast — the SAME already-armed measured intake, sliced by its own product label

The keeper already runs `miso_measured_reserve_requirements=True`
(`run_config.json`), whose loader
(`data/reserve_requirements.py::load_miso_reserve_requirements`) reads
`data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet` — MISO's real-time cleared-offers
report at (date, hour-ending EST, region, **product**, cleared_mw) grain, with
`product ∈ {reg, spin, supp, str}` — and today **sums `reg+spin+supp`** into the single
market-wide RBDC requirement.

The online requirement is that identical series **restricted to `product ∈ {reg, spin}`**.
No new intake, no new file, no new fetch, no residual: the split is a `groupby` on the
column the report itself publishes, under the §1a qualification rule. Every documented
caveat of the parent series (cleared-vs-requirement, RT basis, EST clock, `str`
excluded) carries over unchanged and un-"fixed".

### 1c. The forward generator (rule 13 admissibility)

The forward analogue is published and formulaic, so the mechanism regenerates for a
forecast year and responds to changed conditions:

* Market-Wide **Contingency** Reserve Requirement = the most severe single contingency
  (BPM-002 §3.2: "In no case will the hourly MISO Market-Wide Contingency Reserve
  Requirement be set less than the largest single supply contingency"; NERC BAL-002) —
  already in the model as `largest_single_contingency_mw`, fleet-derived.
* Market-Wide **Spinning** Reserve Requirement = "the most restrictive … requirement,
  **expressed in MW or as a percent of Contingency Reserve**, specified by [ERO/RRO/CRSG]
  standards" (BPM-002 §3.2). The in-force percentage for MISO is published in PJM's
  cross-RTO survey (*Education on Reserve Practices across RTOs/ISOs*, PJM Reserve
  Certainty Senior Task Force, 2024-01-17, slide 3): MISO primary reserve requirement
  **100 % MSSC**, synchronous requirement "**50 % of the primary reserve requirement
  must be met by spinning**".
* **Regulating** Reserve — the existing published `MISO_REGULATING_RESERVE_MW` (400 MW),
  online by §1a.

So the forward online requirement is `MISO_REGULATING_RESERVE_MW + 0.50 × MSSC`.
**This forward constant is used by NO number in this session** — every scored hour of
2023–2025 takes the measured §1b series (rule 14 `[R-ACCURATE]` mandatory swap). It is
registered so the mechanism is forward-reproducible, and it is declared here so it can
never be mistaken for a backcast tuning channel.

### 1d. What would have STOPPED this lane

Had the cleared-offers report carried no product label, or had the online share needed
to be inferred from the model's own residual, the charter's step-1 instruction is to
**STOP and file the data ask**. It does carry the label, and the split is definitional,
so the lane proceeds. (Recorded so the counterfactual is on the record, not implied.)

---

## §2 EX-ANTE SIZING SCREEN — bars declared BEFORE measurement (pjm-142 pattern)

Measured with **no LP**, from committed artifacts only: the §1b series, the keeper's
own `hourly/class_hourly_<year>.parquet`, and the fleet assembled at HEAD under the
keeper's committed config (the miso-130/131 construction). Probe:
`scripts/probes/_miso132_online_gating_sizing.py`; record
`results/calibration/_miso132_online_gating_sizing.json`.

Definitions, fixed here:

* `REQ_on(t)` = measured market-wide `reg+spin` MW (§1b); `REQ_tot(t)` = `reg+spin+supp`.
* Night = hours-of-day **0–5**; the screen window is **July** of each year (the month
  the C7 defect concentrates in, per miso-130 — chosen for the screen's *diagnosis*
  relevance, while every A/B gate in §3 is scored on the full year).
* `ONLINE_CAP(t)` = `Σ_pools min( ρ · P_pool(t), ramp10_pool(t), cap_pool(t) − P_pool(t) )`
  — the keeper's own online-backed reserve capability under the gate being built, at
  **fuel grain, all zones pooled**. Pooling zones **overstates** capability (it lets a
  Midwest MW back a South MW), so the screen is biased **against** this lane: a large
  `ONLINE_CAP` makes S-2 harder to pass, not easier. Declared, not discovered.
* `ρ` = the capacity-weighted plant-level `(pmax − pmin)/pmin` over the reserve-eligible
  pergen member set, clipped to the same physical `[0.5, 4.0]` band the existing NYISO
  online-gated path uses. A fleet property read off the arrays the LP dispatches.

**Bars (all three must hold, else the lane is KILLED with zero solves):**

| id | statistic | BAR | rationale, declared now |
|---|---|---|---|
| **S-1** | `REQ_on` July-night mean, each of 2023/24/25 | **≥ 800 MW** | the charter names ~1–1.4 GW. Below 800 MW the online family is a rounding-level constraint and cannot organise a 2.9 GW off-peak amplitude. |
| **S-2** | `REQ_on / ONLINE_CAP`, July night, **2025** | **≥ 0.25** | the gate can only bite if the online capability is *scarce*. If the keeper already carries >4× the online requirement on generating pools, the gated row is slack in the target hours and the mechanism is inert. |
| **S-3** | (a) coal share of `ONLINE_CAP`, July night 2025 **≥ 0.40**; and (b) `REQ_on × coal share` **≥ 500 MW** | **both** | the mechanism reaches C7 only through **coal**. If coal is not the bulk of the overnight online capability, the backdown pressure lands elsewhere and `COAL_PRB`'s `R_dfrac` cannot move. 500 MW is a *floor on plausible reach*, deliberately **far below** the +3,454 MW 2025 July night surplus: C7 is a SHAPE statistic (`R_dfrac` ×1.447), not a level statistic, so the bar is not "closes the surplus". |

**Two-sided prior, declared (the miso-127 Lane B duty).** The session's honest prior is
that S-1 and S-3 pass and **S-2 is the live risk** — MISO's overnight fleet is large and
`ONLINE_CAP` may exceed `REQ_on` by a wide margin, in which case the gate is slack and
this lane dies exactly as miso-131's did. If S-2 measures ≥ 0.25 the lane proceeds; if
it measures < 0.25 the finding records a P1 KILL and **no mechanism is built**, no field
is added, no arm solved.

---

## §3 THE MECHANISM, if the screen passes

New `ScenarioConfig` field **`miso_reserve_online_gated: bool = False`** (default off,
`run_config.json`-registered per rule 26 `[R-REGISTRY]`), with its
`mechanism-matrix.js` row added in the **same PR** (rule 28(c)).

* **Nested family split** — the market-wide RBDC family keeps `REQ_tot` and draws on
  **every** reserve column; a new family `miso_rbdc_online` carries `REQ_on` and draws
  **only** on the synchronized columns. A synchronized MW therefore counts toward
  **both** requirements (the NYISO East ⊂ NYCA nesting; the same structure PJM's
  `pjm_reserve_pergen_sync` uses for SR ⊂ Primary).
* **The gate** — the keeper runs the **per-generator** reserve construction
  (`miso_reserve_pergen=True`), so the gate is built there rather than on the
  zone-aggregate path: each pool's R column splits into a SYNC and a NON-SYNC column
  sharing the pool's joint `ΣP + ΣR ≤ Σcap` row, and the SYNC column carries
  `R_sync[r,t] − ρ · Σ_{members} P[g,t] ≤ 0` — idle capacity backs nothing. A pool
  ramp row `Σ_r R[r,t] ≤ ramp10_pool(t)` keeps the split from double-spending the
  10-minute deliverability the un-split column already respected.
* **`ρ`** is the §2 fleet property, not a tuned coefficient (rule 5 `[R-NO-MAGIC]`).
* **Rule 25 `[R-ISO-SCOPE]`**: `pjm_reserve_online_gated`, `pjm_reserve_pergen_sync` and
  NYISO's three online-gated arms transfer **nothing**. MISO enters the matrix at `U`
  and derives its own requirement basis (§1) and its own `ρ` from its own fleet. Only
  the generic LP machinery is shared.
* **Rule 19 `[R-ONE-MECH]`**: nothing else in the MISO design gates reserve on online
  status. `miso_commitment_posture` (default **off**, and off on the keeper) is the one
  adjacent mechanism; the arm asserts it stays off and the implementation raises if both
  are armed.

### A/B protocol

Same-HEAD **zero-delta control arm A first** (miso-124: never against the committed
keeper), then arm B, via
`scripts/replay_keeper.py results/calibration/miso127_onlinepmin_B --years 2023 2024 2025`
in **ONE invocation per arm** (a per-year chain records only the last year in
`meta.json`). Arms **sequential** (rule 12).

### KILLS — pre-registered, in order

| id | gate | KILL condition |
|---|---|---|
| **K0** | control integrity | arm A must reproduce the incumbent keeper's scorecard **and** its committed hourly sidecars. A diverging zero-delta control invalidates every Δ (caiso-146). |
| **K1** | flag fidelity / single delta | arm A records `miso_reserve_online_gated=false`, arm B `true`; the two scenario blocks differ in exactly one key (rule 26). |
| **K2** | year span | both bundles `[2023, 2024, 2025]` (rules 16 / 22). |
| **K3** | **C1 16/16** | the C1 criterion must stay **16/16**. Any C1 sub-check lost is a KILL. |
| **K4** | **`COAL_BIT` no-overshoot** (the miso-102 signature) | `COAL_BIT` off-peak `cv_ratio` must not overshoot: KILL if it exceeds **1.60** in any year, or if `COAL_BIT`'s C7 status regresses PASS→FAIL. Reaching `COAL_PRB` by making `COAL_BIT` wrong is not a fix. |
| **K5** | **D-4 driver window** | the mechanism declares its window as **all 8,760 hours** — a published 24/7 reserve requirement, not a floor. It adds **no `min_gen` floor and no forced energy**: KILL if `legitimacy_diagnostics.json`'s D-2 attribution shows a new forcing id, or any class's forced share rises. |
| **K6** | **full-balance identity** (miso-126(b)) | `d_class + d_discharge − d_charge + d_slack − d_dump − d_demand == 0` across the full sidecar set, every year. A magnitude that violates a conservation law is a boundary defect before it is a result. |
| **K7** | **`R_tot` floor 0.90** (the miso-131 P3 convention) | `COAL_PRB` `R_tot` must stay **≥ 0.90** in all three years. `R_tot` is already 0.952 with no room; a `cv_ratio` gain bought by inflating raw off-peak dispersion is not the organisation fix this lane claims. |
| **K8** | **LOYO within 2023–2025** | the verdict is scored leave-one-year-out. A `cv_ratio` improvement carried by a single year, or a PASS→FAIL flip in a currently-passing year, is overfitting. |
| **K9** | reserve-balance sanity | in every hour and every year, the online family's held MW ≤ the market-wide family's held MW, and each family's `held + shortfall ≥ requirement` (`reserve_family_<year>.parquet`). |

### TARGET, declared

**C7 `COAL_PRB` 2025 `cv_ratio` via `R_dfrac`** (the miso-128 dimension). Quote
`R_dfrac`, never raw variance (miso-128 DO-NOT-MISREAD). Success is `R_dfrac` rising
with `R_tot` held ≥ 0.90 — an *organisation* gain, not a dispersion gain.

### KEEPER DECISION RULE, declared before the numbers (rules 1 / 14; owner guidance 2026-08-05)

Promotion is decided on **structural fidelity, never on score**. The model today lets
~2.5–2.7 GW of a published *synchronized* reserve requirement be backed by idle
capacity, which is not MISO's market. If arm B is structurally correct and passes
K0–K2 / K5 / K6 / K9, it **may be promoted even if a gate regresses**. Specifically
**expected and pre-declared**: C3a's annual mean may **worsen**. Overnight prices are
already +$7.0–8.7 high in every July, and the C3c-ledgered missing >$200 peak is
un-modelled; a structural change to the overnight reserve/energy trade-off will expose
more of that missing peak. Per rule 14 that is the **compensating-error signature**,
not a rejection. Conversely, a `cv_ratio` gain achieved with a **failed** K3/K4/K5/K7
is refused however good the number: a mechanism that reaches the right statistic by a
wrong route is not a keeper (rule 1 `[R-STRUCT]`).

### KILL-4 (carried from miso-129/131)

**Nothing is sized on any Δ measured in this session.** `ρ` is a fleet property,
`REQ_on` is the published measured series, and the forward 0.50 spin share is a
published percentage. If the arm underperforms, the response is a finding — **not** a
sweep of `ρ`, not a scaling of `REQ_on`, not a window narrowed onto the residual.

---

## §4 DO-NOT-REDO honoured

Nothing here re-opens: granularity / `offer_curve_smoothing_n` at MISO (miso-131,
adjudicated inert at class grain); the take-or-pay family in any form; regulated
self-commitment forcing; `coal_tranche_*_frac`; within-band slope (premise false,
miso-129); the seam price/ceiling/floor classes (miso-114/123); trough-marginal-unit
volume (miso-115); the coal night floor (miso-113); `gas_commitment_bridge` (its MISO
pool census is empty — untouched here, cell stays `U`). No fitted trough adder. No
2025-specific lane — the mechanism is armed identically in all three years.

## §5 Rule duties this session will discharge

Rule 15 (register **both** arms on the dashboard, in this session), 16 (all three years
in one invocation per arm), 19, 21 (DOF ledger: the arm adds **zero** free parameters —
`REQ_on` measured, `ρ` fleet-derived, 0.50 published and forward-only), 22 (2023–2025
only), 25, 26, 27 (blob-verify every ≥300-line file after push), 28(b) (stamp the matrix
cell + §5.4 in this session) and 28(c) (matrix row in the same PR as the field).

Next number after this session: **miso-133**.
