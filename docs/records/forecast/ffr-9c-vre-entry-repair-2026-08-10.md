# FFR-9C — execute the VRE-entry repair menu (R-a/R-b/R-d) as a staged paired-arm program

**Session.** FFR Wave 9, staged repair lane (manager dispatch Addendum AI.2,
under the owner-re-opened D-21(a) completion mandate — the repair charter
FFR-9B §4 named). Branch `claude/ffr-9c-vre-entry-repair-3r3uy8`, off
`origin/main` `aa61791e`. Model: Fable (rule 27 — capacity-evolution core).

**Charter.** Execute the FFR-9B §4 repair menu as a STAGED paired-arm program
on the ffr9a-storageseed posture (the control posture of record): a verbatim
control, then stage A (+R-a), then stage B (+R-b, +R-d), each a paired read
against the same control. **NO promotion into any shipped default this
session** — every repair is armed BY INVOCATION in measurement arms;
promotion is a later manager/owner act on this lane's evidence. **NO tuning
toward 55.4 GW or any actual.** Evidence base, cited never re-derived:
`docs/handoffs/ffr-9b-vre-entry-diagnosis-2026-08-09.md` §3 (the binding
table) and §4 (the menu, with rule-13 pre-assessments);
`docs/handoffs/ffr-9a-storage-vintage-seed-2026-08-09.md` §1.3/§2–§3 (the
control recipe and its registered reads).

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. The stage-B code (the R-b gate) was built,
regression-tested and committed before this prereg (`9ba23986`) — it is a
GATED default-off field armed only by invocation, with zero parameters
identified from any solve this session runs (the armed value 2030 is the
published ATB availability year). The FFR-9B replay probe's staged-arm
passthrough extension (additive; defaults reproduce the FFR-9B construction
byte-for-byte) is committed with this prereg, before any solve.*

### 1.1 The stages (three cold invocations, one recipe head)

All three arms run VERBATIM at this branch head, sequentially in this
container (15 GB RAM / 4 cores — FFR-9A's measured constraint; rule 12's
≤2-concurrent cap is therefore not exercised), 4 LP solve-years each
(2021, 2023, 2024, 2025; 2022 bridged), years SEQUENTIAL within each
invocation (rule 12). Prerequisites first: `uv sync`, then a COLD
`scripts/regenerate_clean.py`. Each arm gets a FRESH `--out-dir` (the D-13
same-key/stale-bundle hazard — never a surviving FFR-9A/9B dir).

```
# CONTROL (invocation 1) — the ffr9a-storageseed recipe VERBATIM
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9c-control

# STAGE A (invocation 2) — control + R-a (the FFR-5C flag; zero new params)
  ... --entry-pipeline-aware-signal \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9c-pipeline

# STAGE B (invocation 3) — stage A + R-b (SMR gate, ATB-cited 2030)
#                                  + R-d (FFR-5E procurement, vintage 2020)
  ... --entry-pipeline-aware-signal --smr-available-year 2030 \
  --vre-procurement-additions \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr9c-full
```

**Pre-registered runtime cache keys** (computed pre-launch through the
runner's own resolution path — `build_config` → `resolve_policy_bundle` →
`apply_iso_scenario_defaults` — at commit `9ba23986`):

| arm | runtime key | why |
|---|---|---|
| control | `816031a3308cccde` | MUST equal the FFR-9A/9B registered key exactly — the R-b field is registered-and-dropped-at-default, so the verbatim recipe's key is untouched (verified by the cache-key-pin verdict: default pin `603c2498bf71d21d` unmoved, `check_cache_key_registration` 159 fields clean) |
| stage A | `3301180d9f501bcd` | `entry_pipeline_aware_signal=True` enters the hash — a distinct scenario |
| stage B | `d6bc5469694eeedb` | + `smr_available_year=2030` + `vre_procurement_additions_enabled=True` |

The runtime `cache_key=` line of each arm and the ledger path
`<out-dir>/ERCOT/<runtime-key>/` are verified against this table before any
ledger is believed. A DIFFERENT key is diagnosed before proceeding, not
explained away.

**Reproduction gate (control, BY CONTENT).** The control must reproduce the
FFR-9A registered treated-arm reads with zero field diffs: the three probe
records re-run verbatim on the control bundle and deep-compared against the
committed `docs/handoffs/ffr-9a/{storage-trajectory,rebase-reads,e1-dispersion}-treated.json`
(every key except `cache_dir`/`bundle` path strings). Additionally the
control's `score.json` `additions` / `additions_cod_basis` /
`additions_basis` blocks must equal the registered
`ercot-2021-2025-t1ff-armr-ffr9a-storageseed` sidecar's field-for-field.
Reproduction failure is diagnosed before ANY stage comparison is believed.

**Stage-B build note (the netting first-read).** R-d's admissibility is
adjudicated (owner D-18(a)); the FFR-5E-H DEFER caveat ("netting vacuously
satisfied") does not carry to ERCOT per FFR-9B §4 — the ERCOT merchant
screen demonstrably decides at every hot screen, so the §2.3(b) budget
netting IS exercised here and its behaviour is a FIRST-READ, reported at
full magnitude whatever it shows. The vintage-2020 committed pipeline the
channel can see was 6,575 MW at the shipped vintage (FFR-5E measurement);
the vintage-2020 sheet's committed 2021–23 cohort magnitude is itself a
first-read.

### 1.2 Pre-registered reads R1–R5 (each stage vs the same control)

All reads come from the arms' own ledgers/dumps/score.json and four probes
re-run VERBATIM per arm (`ffr8b_rebase_reads.py`, `ffr8b_e1_dispersion.py`,
`ffr9a_storage_trajectory.py`, `ffr9b_entry_screen_replay.py` — the last
with the arm's matching stage flags, so the replay runs under the gates the
solve carried). Records land under `docs/handoffs/ffr-9c/` as
`<probe>-{control,pipeline,full}.json`. Every delta is reported at FULL
MAGNITUDE; expectations are to test, never targets.

* **R1 — additions decision basis per tech per year vs 55.4 GW actual**
  (reported, never targeted): decision-grain MW by evolution step from each
  arm's ledgers (the replay record's `ledger_decided_mw`), plus the
  score.json per-tech totals, laid against the FFR-9B §3 control table.
  Expected stage-A signatures (FFR-9B §4 R-a, pre-registered): solar
  ~5/5/5/· with the 53-MW crumbs GONE; the C/L alternation KILLED (per-tech
  effective rate C, not C/2 — the FFR-5C MISO-wind law); wind's 2023
  queue−pending clip gone. Expected stage-B signatures: nuclear_smr decided
  = 0 at every step (the 2030 gate clears the whole window), its 2.0 GW
  queue cap and ISO-budget share freed; the procurement channel injects the
  vintage-2020 committed cohort as `source: "procured"` rows (magnitude a
  first-read).
* **R2 — the FFR-9B binding-layer census re-run** (which cap binds NOW):
  the replay probe per arm with `screen_ledger` diagnostics, identity check
  (replayed build MW == ledger decided MW per (step, tech), under BOTH
  reserve-leg bounds) — when the identity holds the margins/ordering/
  `binding_cap` labels are authoritative; a failure is reported and the
  labels degrade to arithmetic attribution from ledger state (the FFR-9B
  §1.4 R3 fallback, carried verbatim). Stage A expectation: the
  queue-cap-minus-pending binder class VANISHES (netting relocated); the
  static queue caps and the ISO budget become the binder set at hot
  screens.
* **R3 — the price-side read set**: per-screen (into-2022/2023/2024/2025)
  mean / max / h>$100 / h>$1000 / adder mean, and the per-fuel replica
  margins vs the FFR-6A bars and replica-at-measured-prices columns
  (2024: 75.4/86.7/65.6/65.6, 2025: 97.2/76.4/47.0/47.0 $/kW-yr; measured
  2024: 161 h>$100, mean $26.82, max $3,060; 2025: 217 h, $32.49, $1,570).
  Expected direction (9B §4 R-a): the into-2024-class overshoot DEFLATES —
  the pro-forma prices its own committed pipeline instead of re-deciding
  it — and **gas_cc entry falls WITH the deflation** (R-e: the CC
  over-entry gets NO dedicated lever; it must die of the screen level or
  the R-e claim is refuted). Reported at full magnitude either way.
* **R4 — exits**: in-window economic executions must stay ≈ 0 — ANY
  in-window economic execution is a FALSIFICATION signal per FFR-7C, never
  a success; the gas_st false wave stays gone; the `entry_capped` census
  and per-year reserve margins reported.
* **R5 — the E1/E2 reserve-quantity reads** (the FFR-9A probes re-run
  verbatim): E1's reserve quantity vs the measured series (2024 mean
  16,703 vs 16,679 measured in the control's baseline), the B̃-vs-B
  storage-term step, and E2's `as_hold` liveness per screen. Expected
  direction: as the stages build more VRE mid-window, the screens' scarcity
  content falls and the storage-AS term moves with the (unmodified) storage
  stack's response; magnitudes are first-reads.

**Storage is context, not object**: the storage entry stack is not modified
by any stage; its trajectory (ffr9a_storage_trajectory per arm) is reported
because the deflating screens are expected to move its cap-saturated
profile, and that movement is evidence for the FFR-9A §3.1 routed finding —
not something this lane tunes.

**Leave-one-year-out (rule 22).** Any stage this handoff proposes for
promotion is scored LOYO within 2023–2025 IN THE HANDOFF (no promotion
performed): the stage-vs-control deltas on the scored metrics are tabulated
per scored year (2023 / 2024 / 2025) to show the movement is not
concentrated in one training year. The stages carry zero fitted parameters
(R-a relocates a guard; R-b is a published year; R-d has zero free
parameters), so LOYO here is a robustness demonstration, not a fit-selection
loop — but it is still owed before any promotion recommendation.

### 1.3 R-c (solar queue cap) — explicitly NOT this session's to change

`QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"]` stays 5.0 whatever the reads
show. IF stage A's measured solar throughput still caps below the EIA-860
2025 demonstrated record (actual solar CODs 7.29 / 7.74 GW/yr in
2024/2025, FFR-9B §3.1), this handoff WRITES THE RE-DERIVATION CASE for the
manager — rule 23: from source data only (the EIA-860 record of
demonstrated interconnection throughput), never from the residual — and
touches no constant.

### 1.4 Holdout posture

Solve years per arm: {2021, 2023, 2024, 2025} — training-tier years plus
the enumerated hindcast seed year; 2022 bridged, never solved, no market
data for it read (the 2022 EVOLUTION ledger — bridge-year fleet
bookkeeping — is read, as FFR-9A/9B's R1 probes already did). The holdout
freeze state is read at launch; no marker is spent; no out-of-training year
is approached. 2026+ is not touched in any arm.

### 1.5 What this lane will NOT do

No promotion, no shipped-default move (so NO epoch on other lanes — the
FH-4 sibling legs run concurrently on other ISOs and are not re-based by
anything here: every repair is invocation-armed, cache-key-separated, and
the control's key is byte-identical to the registered posture of record).
No tuning toward 55.4 GW or any actual. **Bar re-levels, signal scaling,
and residual tuning are REFUSED BY NAME.** No backcast-registry touch, no
keeper contact. R-c's constant is not moved (§1.3). If a stage cannot be
built without inventing a parameter: STOP, record it, land the prior
stages — the earlier stages' registrations stand on their own.

**Registration commitment.** ALL solved arms register in the HINDCAST
namespace (`scripts/register_hindcast.py`, ids
`ercot-2021-2025-t1ff-armr-ffr9c-{control,pipeline,full}`) REGARDLESS of
what the reads show. NEVER the backcast registry — the backcast CI gates
stay blind to this namespace. Commits land stage by stage (prereg →
results → handoff as they exist); pushes are small-pack `git push` after
fetch+rebase; no `push_files` on ≥300-line files; no new workflows.

**Matrix duties.** Duty (c) for the R-b field was discharged in the same
commit as the field (`9ba23986`: row `smr_available_year`, cells all U).
Duty (b): the session that tests a mechanism updates its cell + citation in
the same session — after the stages run, the ERCOT cells of
`entry_pipeline_aware_signal`, `smr_available_year` and
`vre_procurement_additions` move U → O (measured, verdict left to the
manager) with this handoff as the citation. No cell claims K/R from a
measurement lane.

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*

## 2. The arms — all three solved clean, every gate passed

All three invocations ran verbatim at this branch head, sequentially, cold:
solved `[2021, 2023, 2024, 2025]`, bridged `[2022]`, exit 0,
`leakage_violations: []`, holdout freeze ACTIVE and read at launch, no
marker spent. **Every runtime key landed exactly as pre-registered**
(control `816031a3308cccde`, stage A `3301180d9f501bcd`, stage B
`d6bc5469694eeedb`), and every meta records the SOLVED gates (FFR-3R:
stage A `entry_pipeline_aware_signal=True` only; stage B additionally
`smr_available_year=2030` + `vre_procurement_additions_enabled=True`).

* **Reproduction gate (control): PASSED, BY CONTENT, with ZERO field
  diffs** on all six comparisons — the `score.json`
  additions/additions_cod_basis/additions_basis blocks vs the committed
  ffr9b-regen blocks, and the three probe records re-run on this bundle vs
  the committed `docs/handoffs/ffr-9a/*-treated.json`. The control's
  replay identity holds at every (step, tech) under both reserve-leg
  bounds and reproduces the FFR-9B §3 decided-row table cell-for-cell.
* Registered: `ercot-2021-2025-t1ff-armr-ffr9c-{control,pipeline,full}`
  (hindcast namespace, `meta.kind="full_forward"`). Probe records:
  `docs/handoffs/ffr-9c/{rebase-reads,e1-dispersion,storage-trajectory,entry-screen-replay}-{control,pipeline,full}.json`.
* Mid-session external events, recorded: (i) this branch's first two
  commits (the R-b gate + the prereg) were merged to main as PR #3833 by
  an actor outside this session mid-run, deleting the remote branch
  (re-created on the next push; no content lost, later commits rebased
  clean); (ii) main picked up #3832, a pure namespace re-export through
  the constants facade (output-inert — two added import names, no value
  or consumer change). After each event all four pre-registered keys were
  recomputed at the new head and verified UNCHANGED before proceeding.
* Replay identity across the staged arms: stage B holds at ALL 20
  (step, tech) cells under both bounds. Stage A holds at 15/16; the
  single failure is **2024 gas_ct** (ledger 3,000 MW, replay unprofitable
  by −$13.5/kW-yr under both bounds) — the true thermal reserve leg (the
  prior solved year's REALIZED post-solve ORDC adder, `runner.py:3482`)
  sits ABOVE both bracket legs at a deflated forward screen, exactly the
  degradation §1.2 R2 pre-registered. For that one cell the ledger rows
  are authoritative and the binder label falls back to arithmetic
  attribution (`per_tech_cap`: built = the full freed 3,000 MW cap); in
  stage B (richer $40.10 screen) the same cell clears inside the bracket
  (+$63.8) and the identity passes, corroborating the attribution.

## 3. The reads — each stage vs the same control, at full magnitude

### 3.1 R1 — decision-grain additions per tech per step (MW; ledger truth)

| step | arm | wind | solar | gas_cc | gas_ct | nuclear_smr | storage | procured (w/s) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2022 | control | 482.4 | 4,946.6 | 3,000 | 1,571 | 2,000 | 5,000 | — |
| | stage A | 482.4 | 4,946.6 | 3,000 | 1,571 | 2,000 | 5,000 | — |
| | stage B | **2,078.8** | 3,960.0 | 3,000 | 1,571 | **0** | 5,000 | 350.2 / 1,040.0 |
| 2023 | control | 4,517.6 | 53.4 | 0 | 1,429 | 0 | 5,000 | — |
| | stage A | **0** | 4,000.0 | **3,000** | **3,000** | **2,000** | 5,000 | — |
| | stage B | 1,000.0 | 4,550.0 | 3,000 | 3,000 | **0** | 5,000 | 0 / 450.0 |
| 2024 | control | 482.4 | 4,946.6 | 3,000 | 1,571 | 2,000 | 5,000 | — |
| | stage A | 0 | 5,000.0 | 3,000 | 3,000 | 0 | **0** | — |
| | stage B | 0 | 5,000.0 | 3,000 | 3,000 | 0 | **5,000** | — |
| 2025 | control | 0 | 53.4 | 0 | 0 | 0 | 0 | — |
| | stage A | 0 | 0 | 0 | 0 | 0 | 0 | — |
| | stage B | 0 | 0 | 0 | 0 | 0 | 0 | — |
| **total (GW, score basis)** | control | 5.482 | 10.0 | 6.0 | 4.571 | 4.0 | 15.0 | — |
| | stage A | **0.482** | 13.947 | **9.0** | 7.571 | 4.0 | **10.0** | — |
| | stage B | **3.429** | **15.0** | 9.0 | 7.571 | **0** | 15.0 | (in wind/solar) |
| **actual COD 2021–25** | | 12.663 | 25.08 | 0.244 | 3.692 | 0 | 13.691 | |

Model totals 45.05 (control) → 45.0 (stage A) → **50.0 GW** (stage B) vs
55.4 actual — reported, never targeted.

Pre-registered signatures against outcome:

* **The C/L alternation is KILLED (stage A, confirmed).** Every
  profitable tech decides in every hot year; the 53-MW solar crumbs are
  gone; no `queue−pending` binder remains anywhere in either staged arm's
  census. Solar runs 4,946.6 / 4,000 / 5,000 — the "~5/5/5" signature,
  with the 2023 clip being the ISO budget (12,000 shared with the
  unblocked thermal+SMR), not the queue cap.
* **The into-2024-class screens DEFLATE (confirmed, ~10×).** §3.3.
* **gas_cc falls WITH the deflation — MARGIN-CONFIRMED, BUILD-REFUTED
  (the load-bearing stage-A finding).** The CC margin at into-2024
  collapses $2,455 → **$15.7**/kW-yr (stage B $93.5) and into-2025 kills
  it outright (−$120.8) — the deflation mechanism works exactly as R-a
  predicted. But CC's decided TOTAL **rises 6.0 → 9.0 GW** (vs 0.244
  actual): killing the alternation unblocks CC's 3 GW queue cap at the
  still-hot into-2022/2023 screens, which the pipeline-aware signal
  CANNOT deflate — their committed pipeline is empty/not-yet-online by
  construction (the 2022 cohort's COD 2024 lands beyond both screens).
  The early-window overshoot is the FFR-9A missing-VRE feedback (the
  vintage fleet really was that short before reality's 2021–23 build
  arrived), which is exactly the cohort only R-d can supply — and at this
  vintage R-d supplies only 1.84 GW of it (§3.6). **R-e's "no CC lever"
  claim survives for the mechanism (nothing CC-specific is warranted) but
  its sufficiency claim does not: deflation alone does not kill CC entry
  in this window.**
* **Wind: stage A COLLAPSES it (0.482 GW, −96% vs actual); the SMR gate
  is what rescues it (stage B 3.429 GW).** With thermal+SMR unblocked at
  every hot screen, last-ranked wind loses the budget residuals it lived
  on: at into-2023 the margin order (CC $3,503 > CT $3,461 > SMR $2,584 >
  solar $2,420 > wind $556, all per kW-yr) exhausts the 12 GW budget one
  rank above wind (`iso_budget_exhausted`). In stage B the phantom SMR's
  2 GW/hot-year budget share goes to wind almost exactly (2,078.8 in
  2022; 1,000 in 2023) — the FFR-9B §3.1 crowding attribution, now
  demonstrated by intervention. Wind's residual gap (−72.9%) is the
  rule-1-honest remainder: the pre-vintage PTC cohort R-d can only
  partially supply (§3.6) plus wind's last-place capture rank on a
  scarcity-shaped signal (9B §4's re-measure-before-inventing-levers
  statement stands).
* **nuclear_smr = 0 at every step (stage B, exact).** The R-b gate
  removes all 4.0 GW of phantom SMR; nothing else moves at the 2022
  screen except where the freed MW lands (wind + a solar shift from
  ladder-clip to budget-clip).

### 3.2 R2 — the binding-layer census (which cap binds NOW)

Replay-labelled, identity-checked (§2). The control census is FFR-9B §3
verbatim (reproduced to the MW). The staged arms:

| screen | stage A binder set | stage B binder set |
|---|---|---|
| into-2022 | CC/SMR `per_tech_cap`; CT/solar `growth_ladder`; wind `iso_budget` (482.4 residual) | CC `per_tech_cap`; CT `growth_ladder`; **solar `iso_budget`** (3,960 = residual net of procured); **wind `iso_budget`** (2,078.8) |
| into-2023 | CC/CT/SMR `per_tech_cap`; solar `iso_budget` (4,000); wind `iso_budget_exhausted` (0) | CC/CT `per_tech_cap`; solar `iso_budget` (4,550 net of 450 procured); wind `iso_budget` (1,000) |
| into-2024 | solar/CC `per_tech_cap`; CT `per_tech_cap` (arithmetic fallback, §2); SMR/wind `unprofitable` | solar/CC/CT `per_tech_cap`; wind `unprofitable` (−$12.9) |
| into-2025 | ALL `unprofitable` | ALL `unprofitable` |

The `queue−pending` binder class of the control (9 of its 20 cells) is
GONE from both staged arms — the R-a relocation's structural signature.
The ISO budget replaces it as the binding layer at hot screens (5 stage-A
cells, 4 stage-B cells + 2 procured-netted), and the static per-tech queue
caps take the rest.

### 3.3 R3 — the price side (expectations tested, not targets)

Screen stats (`mean $/MWh / h>$100 / h>$1000 / max / adder mean`):

| screen | control | stage A | stage B | measured |
|---|---|---|---|---|
| into-2022 | 192.83 / 666 / 372 / 5,000 / 156.95 | identical | identical | — |
| into-2023 | 431.54 / 1,278 / 876 / 5,000 / 386.72 | identical | identical | — |
| into-2024 | 309.69 / 960 / 623 / 5,000 / 285.02 | **31.22 / 122 / 31 / 4,408 / 10.70** | **40.10 / 172 / 57 / 4,814 / 19.32** | 26.82 / 161 / — / 3,060 |
| into-2025 | 31.20 / 112 / 37 / 4,936 / 13.46 | **19.83 / 18 / 7 / 4,152 / 2.91** | **19.44 / 17 / 8 / 3,793 / 2.75** | 32.49 / 217 / — / 1,570 |

Thermal replica margins ($/kW-yr; replica-at-measured-prices 2024:
coal 75.4 / CC 86.7 / CT 65.6 / ST 65.6; 2025: 97.2 / 76.4 / 47.0 / 47.0):

| screen | arm | coal | gas_cc | gas_ct | gas_st |
|---|---|---:|---:|---:|---:|
| into-2024 | control | 1,993.66 | 2,234.45 | 2,279.17 | 2,013.95 |
| | stage A | **76.05** | **112.35** | **91.39** | **74.92** |
| | stage B | 136.02 | 179.98 | 160.09 | 135.35 |
| into-2025 | control | 93.27 | 117.95 | 107.62 | 93.67 |
| | stage A | 19.70 | 32.70 | 22.92 | 19.79 |
| | stage B | 18.96 | 30.72 | 21.93 | 19.11 |

* **The into-2024-class overshoot deflates ~10× — the R-a cobweb
  mechanism, dose-response-confirmed.** into-2022/2023 are BYTE-IDENTICAL
  to control in both staged arms (the committed CODs land beyond those
  screens — the construction pricing exactly what it should and nothing
  else), and the one screen whose committed pipeline is visible collapses
  from 26× the replica columns onto them (stage A's into-2024 margins sit
  ON the replica-at-measured values; the mean lands within $4.40 of
  measured). Stage B deflates slightly less ($40.10) because gating SMR
  removes 2 GW of committed firm capacity from the very pipeline the
  signal prices — an internally-consistent interaction, reported.
* **The into-2025 screen inverts to an UNDERSHOOT (18/17 vs 217 h>$100).**
  The staged arms' extra 11.5 GW of 2023-decided thermal+solar commissions
  into the 2024 fleet, flooding the forward screen. The control's
  near-measured into-2025 (112 h) was two errors cancelling — the missing
  mid-window VRE trajectory propping up the forward edge. The honest state
  after R-a is: mid-window screens on-level, forward-edge screen
  over-supplied by the model's own (mis-mixed: CC-heavy, wind-light) build
  response. This is the entry-MIX error surfacing on the price object —
  one mechanism, now the residual one.

### 3.4 R4 — exits

* **In-window economic executions: 0 in all three arms** — the FFR-7C
  falsification bound HOLDS through every stage. The gas_st false wave
  stays gone. Model in-window thermal retirements remain 0.0 GW vs 2.294
  actual (the under-exit defect, pre-existing and untouched here).
* The staged arms' colder into-2025 screen re-fails the always-failing
  thermal cohort that the control's $93 coal margin had cleared: the
  `entry_capped` census returns at 470 units / 43.80 GW (stage A) and
  476 / 43.86 GW (stage B), decided 2025 → exe ≥ 2027 (outside the
  window), adequacy-capped, zero executions. Reserve margins:
  2021/2023/2024/2025 = 19.0/13.7/**22.2**/34.9 % (stage A) and
  19.0/14.1/**25.4**/36.1 % (stage B) vs control 19.0/13.7/28.0/33.0 %.

### 3.5 R5 — the E1/E2 reserve-quantity reads

E1's arm reserve series C vs measured RTOLCAP A (MW):

| year | read | control | stage A | stage B | measured |
|---|---|---:|---:|---:|---:|
| 2024 | C mean | 16,703 | 17,897 | 17,843 | 16,679 |
| 2024 | C p1 / min | **−3,328 / −9,175** | **+7,637 / +1,540** | +6,534 / +293 | 7,874 / 5,094 |
| 2025 | C mean | 19,594 | 18,043 | 19,788 | 19,124 |
| 2025 | C p1 | 8,619 | 12,034 | 13,784 | 8,955 |
| 2024 | storage-AS term (B̃−B step p1) | +2,117 | +2,117 | +2,117 | — |
| 2025 | storage-AS term | +3,633 | +1,883* | +3,633 | — |

*(stage A's 2025 storage-AS scalar falls to 3,578.1 MW because its storage
build dies in 2024 — §3.6.)* The FFR-8B screen-asymmetric deep-tail
starvation (control 2024 p1 −3,328 with 1,767 phys-bound hours) is GONE in
both staged arms — the 2024 low tail lands ON the measured p1 (stage A
within 237 MW) with phys-binding falling to 432 h (stage A) / 293-min
bounded (stage B). The 2025 tail now sits ABOVE measured (the arm fleet is
longer than reality's), the same over-supply read as §3.3's into-2025.

E2 (`as_hold`): unchanged at the early screens (identical fleets), mean
25.8–29.3 MW at into-2024, and at into-2025 it ticks alive in stage A only
(mean 22.4 vs 0.0) — stage A's dead 2024 storage build leaves the
storage-AS share (3,578 MW) near the responsive requirement. Consistent
with FFR-9A §3.3's one-cause attribution; no E-side mechanism moved.

### 3.6 Storage context + the R-d netting first-read

* **Storage (not this lane's object, reported):** control 5/5/5/0
  (15.0 GW). Stage A **5/5/0/0 (10.0 GW)** — the deflated $31.22
  into-2024 screen kills the arbitrage-only stack a year early (every
  storage tech unprofitable at both 2024 and 2025 screens). Stage B
  restores 5/5/5/0 — at its $40.10 screen the stack still clears. The
  FFR-9A §3.1 finding sharpens: the storage cap's saturation is a
  screen-level artifact in this posture; its build dies wherever the
  screens approach measured levels. Actual trajectory 0.6→1.3→2.0→4.1→5.6
  GW/yr; the cap-profile mismatch is unchanged and stays routed to the
  storage-entry lane (arbitrage-only stack, AS slice absent — the
  compensation FFR-9A named).
* **The R-d first-read, at full magnitude.** The vintage-2020 committed
  cohort (proposed sheet, U/V/TS statuses) is **6,761 MW — wind 1,847 /
  solar 4,914 — effective 2021–2023**. Rows effective in EVOLVING years
  inject **1,840.2 MW** (2022: solar 1,040 + wind 350.2; 2023: solar 450);
  the remaining **~4,921 MW is effective-2021 — held by the channel and
  NOT injected** at base year 2021 (the base year does not evolve; its
  pools seed from the vintage fleet). This is the FFR-5E-H "sharp form"
  measured on ERCOT: at this vintage/base-year construction the channel
  can supply only ~10 % of the 18.4 GW §3.2 pre-vintage cohort it was
  named for. NOT a defect in the channel — the safe-direction under-count
  its scope bounds document — but it bounds what R-d can close here, and
  any widening (vintage, statuses, base-year injection) is a separate
  owner decision, not this lane's.
* **The §2.3(b) netting IS exercised, and it is EXACT** (the FFR-5E-H
  DEFER caveat is discharged for ERCOT): in 2022 the screen decides
  10,609.8 MW + 1,390.0 procured = **12,000.0 MW — the ISO budget to the
  megawatt**; solar's queue clips to 3,960 (its rank's residual net of
  procured); 2023 likewise 11,550 + 450 = 12,000.0. One physical queue,
  spent once, visible in the replay identity holding at every stage-B
  cell.

## 4. Leave-one-year-out, the R-c case, and the promotion evidence

### 4.1 LOYO within 2023–2025 (rule 22; scored here, NO promotion performed)

No stage carries a fitted parameter (R-a relocates a guard with zero new
parameters; R-b's 2030 is the published ATB year; R-d has zero free
parameters), so no year could have been fitted; the LOYO table
demonstrates the movement is not concentrated in a single training year.
Stage-vs-control deltas on the per-year scored/measured streams:

| stream | year | control | stage A | stage B | direction vs actual |
|---|---|---:|---:|---:|---|
| CO2 err % | 2023 | −11.28 | −11.28 | −12.84 | A =, B slightly worse |
| | 2024 | −22.08 | −22.07 | −19.81 | A =, B better |
| | 2025 | −4.20 | −9.07 | −3.92 | A worse, B better |
| screen h>$100 (into-2024) | 2024 | 960 (meas 161) | 122 | 172 | both massively better |
| screen h>$100 (into-2025) | 2025 | 112 (meas 217) | 18 | 17 | both worse (undershoot) |
| E1 p1 (2024, meas 7,874) | 2024 | −3,328 | +7,637 | +6,534 | both massively better |
| E1 p1 (2025, meas 8,955) | 2025 | 8,619 | 12,034 | 13,784 | both worse (over-long fleet) |
| reserve margin (I12 band read) | 2024 | 28.0 % | 22.2 % | 25.4 % | — |

Stage B's movement has the same sign in every year-pair it touches except
the CO2 2023 cell (−1.6 pp, from procured VRE displacing gas a touch too
hard in the cheapest year); no single-year concentration appears. Stage
A's 2025 degradations (CO2, screen, E1) are all one object — the CC-heavy
mis-mixed build response — which stage B partially corrects.

### 4.2 The R-c re-derivation case (WRITTEN FOR THE MANAGER; nothing touched)

The prereg §1.3 condition FIRES: after R-a, measured solar throughput
still caps below the demonstrated record. In BOTH staged arms the 5.0
GW/yr solar queue cap is the binder at into-2024 with the margin
comfortably clear (+$50.9 stage A / +$119.9 stage B), i.e. the model
would build more solar in 2024 and is stopped ONLY by
`QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"] = 5.0` — while the EIA-860 2025
record shows actual ERCOT solar CODs of **7.29 GW (2024) and 7.74 GW
(2025)**: the measured interconnection throughput of the real queue
exceeds the constant by ~1.5×. Rule-23 admissible re-derivation: recompute
the cap from the post-2020 EIA-860 demonstrated-throughput record (the
same source and construction that seeded it), NOT from any residual. The
case is strengthened by the binder evidence being margin-independent (the
cap binds at wildly different margin levels, $51–$2,420) and by the wind
contrast (wind's cap never binds after stage B — no wind-cap case exists).
Owner/manager decision; this session touched no constant.

### 4.3 What the staged evidence establishes (promotion recommendation LEFT TO THE MANAGER)

* **R-a (`entry_pipeline_aware_signal`)** does exactly what FFR-5C built
  it to do, now measured through four LP-solved ERCOT screens: the
  alternation dies, the flow caps bind as their citations define, and the
  one screen that can see its committed pipeline deflates onto the
  replica-at-measured margin levels. Its honest cost: the mid-window build
  it unblocks is CC-heavy/wind-absent at the still-hot early screens, so
  ALONE it worsens wind (−96 %), gas_cc (+3 GW) and the forward-edge
  screen. R-a is the structural repair of a real double-count (rule 19)
  and its case does not rest on the residual — but as a lone arm it is
  not a candidate posture.
* **R-b (`smr_available_year=2030`)** removes a non-real object (4 GW of
  2022-vintage ERCOT SMR) with a published, zero-parameter gate, and the
  freed budget flows to wind precisely as the FFR-9B crowding attribution
  predicted. No structural argument against it surfaced in any read.
* **R-d (procurement at vintage 2020)** fires, nets exactly, and is
  bounded at this vintage to 1.84 GW injected — a real but small slice of
  the pre-vintage cohort. Its netting caveat is discharged for ERCOT.
* **Together (stage B)** the posture moves the additions basis 45.05 →
  50.0 GW vs 55.4 actual, solar −60 % → −40 %, wind −57 % → −73 %
  (better than stage A's −96 % but worse than control — the honest
  statement is that R-b/R-d recover only part of what R-a's
  alternation-kill redistributes away from wind), CC +23.6× → +35.9×
  actual (worse; its actual is 0.244 so the ratio is fragile — the GW
  error is +5.8 → +8.8), and the mid-window price/reserve objects onto
  their measured levels for the first time in this posture's record.
* **The residual object after stage B is the entry MIX at the hot early
  screens** — CC/CT take 6 GW/yr of a 12 GW budget in years whose real
  additions were ≈ 0.06 GW/yr of CC, because those screens price the
  vintage fleet's genuine scarcity while reality's relief (the 2021–23
  COD wave) is only ~10 % suppliable by any admissible channel at this
  vintage (§3.6). Candidate directions belong to the manager: the
  full pre-vintage-cohort question (R-d's vintage/base-year scope, an
  owner call), the wind capture-rank question (9B §4's re-measure clause,
  now with stage-B data to measure against), and R-c.

**NO PROMOTION PERFORMED.** Every arm is invocation-armed; every shipped
default is untouched; the manager's dispatch decides what, if anything,
promotes, on this evidence.

## 5. Governance

* **Charter compliance.** Staged paired-arm program executed exactly as
  pre-registered; no tuning toward 55.4 GW or any actual; bar re-levels,
  signal scaling and residual tuning were not performed (refused by name
  in §1.5); no keeper contact; no backcast-registry touch; all three arms
  registered in the hindcast namespace regardless of outcome (§2).
* **No epoch.** No shipped default moved; the FH-4 sibling legs are not
  re-based — the three arms are cache-key-separated by their armed
  fields, and the control's key is byte-identical to the posture of
  record (proven by the zero-diff reproduction gate).
* **Rule 22.** Solve years {2021, 2023, 2024, 2025} + the 2022 bridge in
  every arm; freeze ACTIVE at launch; no marker spent; no out-of-training
  year approached; LOYO scored in §4.1 with no promotion.
* **Rule 28.** Duty (c): the `smr_available_year` matrix row landed in
  the same commit as the field. Duty (b): the ERCOT cells of
  `entry_pipeline_aware_signal`, `smr_available_year` and
  `vre_procurement_additions` move U → O in this session's matrix commit,
  citing this handoff; verdicts (K/R) are deliberately NOT claimed — a
  measurement lane measures.
* **Rule 27.** Fable. All edits were local on-disk bytes; pushes were
  small-pack `git push` after fetch+rebase; no `push_files` on ≥300-line
  files; no new workflows; no CI offload. The mid-session branch deletion
  (PR #3833 external merge) and its clean recovery are recorded in §2.
* **Rule 12.** 4 LP years sequential within each invocation; the three
  invocations ran sequentially (15 GB / 4 core container).
* **Artifacts committed:** per-arm slim bundle files (score.json + 4
  screen dumps + meta/run_config/config.yaml), 12 probe records under
  `docs/handoffs/ffr-9c/`, 3 scorer reports under `docs/hindcast-reports/`,
  3 hindcast sidecars, this handoff, and the matrix cell updates.
