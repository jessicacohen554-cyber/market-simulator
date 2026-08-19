# Model Audit Program — Director Status Board (2026-08)

> # ⛔ PROGRAM PARKED AT G1 BY OWNER DECISION — WS3/PERF PAUSED FOR CALIBRATION
>
> **This is not drift and nothing below is late.** The owner paused WS3/PERF-B so
> the calibration program can run. *PERF-B merged byte-green* is a G2
> precondition, so **G2 cannot be declared while WS3 is paused** and the program
> sits at **G1**. **DOCS-B** (G2), **SITE-A** (G3) and **AUDIT-B** (G3) are
> **waiting by design**. The FFR desk's **Q.2 supersession battery**, which
> commissions at G2 (`ffr-owner-sitting-2026-08-02.md` AS.6), **does not fire.**
> Whoever un-parks the program starts at the **RESTART CHECKLIST** at the bottom
> of this board, not at change (a).
>
> ### 🔴 NEW AT v9 — THE v8 RESTART WINDOW IS **RETRACTED**. Calibration re-armed; keeper stability is further away than at v8, not nearer.
>
> The v8 banner said every ISO lane was at rest by a decision, so the owner could
> declare the freeze without interrupting anything. **That was true at `7e6da12`
> and is false at `598554e`.** Eighteen PRs later: **NYISO promoted TWICE in one
> day** (nyiso-143 → nyiso-144), **MISO re-opened a lane the owner had closed**
> (#4097 re-charter) and executed its pre-registration, **CAISO ran two further
> diagnosis lanes**, and **ERCOT closed ercot-220 and opened ercot-221 with an
> armed full-span A/B RUNNING at the moment of this read**.
>
> **The dispatch that ordered this retraction gave a different reason, and that
> reason is itself stale.** It retracted the banner because three ISO lanes sat
> unmerged at `eb2fe60`; **all three merged before this read** (#4098, #4099,
> #4101), and seven more landed after them. So the window did not close because
> merges were pending — it closed because **the lanes re-armed**. The park holds;
> the freeze is a more expensive call today than it was at v8.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v9):** director read completed 2026-08-18 at `eb2fe60`; **this
records lane re-verified every figure live on 2026-08-19 at ~05:05 UTC against
`origin/main` @ `598554e`** · **ZERO open PRs** (live) · **eighteen PRs merged
since the v8 snapshot `7e6da12`**: **#4089–#4093 and #4095–#4107** (#4094 was the
v8 records lane itself). **Ten of those — #4098–#4107 — landed AFTER the
dispatch's stated `eb2fe60`**, which is why five of the dispatch's factual
premises are *corrected* below rather than transcribed. Per the refresh
protocol's own instruction ("verify every number against HEAD before writing
it"), HEAD wins.

**Headline: calibration re-armed, and the cycle's own premises moved under it.**
Every lane the dispatch listed as unmerged is merged; NYISO's keeper has moved
**twice past** the one the dispatch names; MISO's ≥24 GB container ask is
**retired on measurement**; and the BLOAT-2 parity gate the dispatch reports
GREEN is **RED at HEAD**. Two things the cycle *confirms* rather than corrects:
**the golden tier still has had no CI run since the red** (sixth cycle), and
**no ISO has ever spent a locked-test year**. One deviation is **CLOSED**: the
session roster is a **live read** for the first time in four cycles.

## What moved this cycle

**Read the five corrections first — the dispatch for this cycle was written at
`eb2fe60` and ten PRs landed on top of it.**

1. **🔴 CORRECTION — the three "unmerged lane branches" are ALL MERGED.** The
   dispatch's headline item, and its new owner-queue rank 0, was that ERCOT-219,
   NYISO-143 and MISO-168 each sat one commit ahead of main awaiting an owner
   merge. Verified by ancestry at HEAD: **`claude/ercot-219-option-b-phase1-5cs9bf`
   @ `142b2f5` (#4098), `claude/nyiso-frontier-redeclaration-191c6i` @ `b025a4e`
   (#4101), `claude/miso-reserve-online-gated-colcr1` (#4099) — all three are
   ancestors of `598554e`.** There is **nothing awaiting an owner merge**; the
   queue item is retired the same cycle it was created.
   *One branch is genuinely unmerged and it is a different one:*
   **`claude/ercot-lmp-miss-analysis-cde845` @ `3f13c62`**, one commit ahead — a
   read-only ercot-221 prep measurement (2022 regime point, trailing-expectation
   test, trigger selection; no LP, no solve, 2019 untouched).
2. **🔴 CORRECTION — the NYISO keeper is `2026-08-18-nyiso-144-layup-exclusion`,
   not the nyiso-143 the dispatch describes as "PENDING MERGE".** nyiso-143
   merged (#4101) **and was superseded the same day** by nyiso-144 (#4104).
   NYISO therefore **promoted twice in one day**. nyiso-144 is the *membership*
   half of the nyiso-140 correction: `reliability_floor_plant_exclusions` never
   reached `nyiso_gas_commitment_bridge`, so the same economically laid-up
   stations stayed floored by the other mechanism that floors the same class —
   rule 19 `[R-ONE-MECH]`'s "enumerate what already floors the same class", one
   mechanism later. **ONE differing `scenario_config` field**
   (`nyiso_gas_bridge_plant_exclusions` False → True), identification the
   nyiso-140 per-cell zero-median lay-up criterion **verbatim** (rules 13/23,
   source data only). **The structure-over-gates clause is NOT needed and NOT
   invoked** — no gated criterion regresses and C3c is **bit-unchanged** at
   2/0/5 h against RT actuals 10/13/42. Determination **CALIBRATED**; rule 22
   D-5(b) re-key done (`complete` entry now names nyiso-144, `rekey_history`
   n=7, determination re-verified, worse-determination stop did not fire).
3. **🔴 CORRECTION — MISO's ≥24 GB container ask is RETIRED, not open.** The
   dispatch enters it at owner-queue rank 2 as "not fixable by re-dispatch into
   the same environment size". **miso-169 fixed it** (#4107): the owner directed
   *"Can you fix it so it doesn't need that much memory"*, and the session
   attributed the peak instead of assuming it. The build phase is **not** the
   peak (assembly tops out at 5.1 GB, ~9 GB below it); the cost is
   **highspy 1.14 solution marshalling**, and a read-only marshalling reorder —
   **verified bit-identical** — took the year peak **13.95 → 12.40 GB**. The
   full 3-year control replay runs on the 15 GB box. LP size for the record:
   **492,516 rows × 25,447,800 columns, 50.3 M nnz**.
4. **🔴 CORRECTION — BLOAT-2 registry/payload parity is RED at HEAD, not green.**
   The dispatch reports it re-run GREEN at 28/28. **Re-run at `598554e` it
   FAILS**, on two tracked bundle dirs that map to no retained sidecar `bundle`
   field and are not keep-required (Class-E retention rule point 4):
   **`results/calibration/ercot221_control_A`** (15 tracked files, added by
   `18907e5` in #4106) and **`results/calibration/nyiso144_arm_recipe`** (one
   stray `meta.json`, added by `4769a64` in #4104). Both are **fresh calibration
   output that outran its registration**, not a WS6 regression — and the ERCOT
   one is expected to resolve on its own when the in-flight ercot-221 A/B
   registers. **The remediation is already staged**: the live session read shows
   the director session itself **BLOCKED** on *"WS6 register/prune ready;
   awaiting go to issue lane"*. Back on the owner queue.
5. **🟢 DEVIATION CLOSED — the session roster is a LIVE READ.** `list_sessions`
   returned **30 sessions** this cycle (`mine: true`, `has_more: true`) after
   failing *"requires approval"* across **four attempts at v7 and two at v8**.
   The roster below is live for every lane active in the last ~26 h; three lanes
   that landed earlier on 2026-08-18 fall outside the returned page and are
   filled from `Claude-Session` commit trailers, labelled as such.

6. **🟡 CONFIRMED, NOT CORRECTED — GOLDEN-TIER CI STILL HAS NO RUN SINCE THE
   RED.** Live `actions_list` on `golden-data-tier.yml` at this read returns
   **five runs, unchanged**: latest is still the red **`31999181985`**
   (schedule, 2026-08-17T05:48:08Z, main); last green is still **`31913648051`**
   (workflow_dispatch, 2026-08-15T23:01:19Z). The #4071 fix is **not** in
   question — its finding records a full local four-step job replay, all green.
   **The CI proof is.** Note the cadence arithmetic: the red *was* the Monday
   cron (2026-08-17 is a Monday), so **waiting costs a full week** — the next
   scheduled firing is **Monday 2026-08-24 05:37 UTC**. **Sixth cycle as the top
   standing open item.**

7. **RUBRIC v3.4 (#4093, 2026-08-18) — the C1 volume band is floored at the
   share leg's own materiality.** `vol_band = min(max(2 % of ISO load, 3.0 % of
   ACTUAL total generation), 8 TWh)` in
   `calibration_verdict._fuelmix_vol_band`. **No new constant** — the floor is
   `FUELMIX_SHARE_PP` (3.0) applied to the actual-side generation total, the same
   ±3.0-pp mix materiality the share leg already declares; it reconciles C1's two
   legs rather than adding tolerance. On a deep net-importing ISO the 2 %-of-load
   term could bind **tighter** than the rubric's own declared mix-materiality on
   the same class (CAISO 2023: 2 % of 207.4 TWh load = ±4.15 TWh vs 3 % of
   175.7 TWh generation = ±5.27 TWh). Measured on **actual generation, not
   `share_pp`**, because a system-total shrink flatters `share_pp` — the same
   CAISO CC row reads −1.8 pp on share but −2.4 pp of actual generation.
   **Effect measured over all 26 then-registered runs: exactly one row flips** —
   CAISO keeper C1 2023 `CC_REGULAR` FAIL → PASS, taking the run's C1 criterion
   FAIL → PASS. **Scorer-only; no determination label changes anywhere.**
   Re-verified at HEAD: CAISO's determination stays **NOT-YET** on a **lone C3a
   `price_mean` FAIL** (2024 +12.8 %: 39.07 vs 34.65 RT; 2025 +15.7 %: 39.82 vs
   34.42 RT), C3c the lone ledgered caveat, **grade summary scored 8 /
   target-grade 6 / commercial-grade 0 / ledgered 1 / fails 1** — matching the
   dispatch exactly.

8. **PER-ISO LANE MOVEMENT** — detail in the keeper table; the two lanes that
   changed the program's *state* rather than its keepers:
   - **ERCOT — one lane closed on measurement, a second opened, and an A/B is
     RUNNING RIGHT NOW.** **ercot-219** (#4098) built the signed option-B card's
     three stages and A/B'd them full-span: **REJECTED-AS-ARMED on four gates at
     full magnitude** (G-SPUR 9→273 / 11→671 / 1→1239 against a +5 bar; G-SHED
     0/1/0 → 218/77/221 h; G-OWNER C3a +715 %/+1278 %; G-BAT-2024 0.41), with
     G-CAP/G-DOF/G-D2/G-REPRO passing. **The cause is measured and dimensional,
     not mysterious:** stage 1 reconciles the model's **AVAILABLE** capability
     envelope to a telemetered **ONLINE** aggregate (RTOLHSL) — a category error
     at the aggregate grain, and the ERCOT-159/163 realized-commitment failure
     mode restated. **Stages 2–3 are NOT refuted** — G-EXH is strongly correct
     and monotone (1,557 → 336 → 63 exhaustion hours across 2023→2025). Matrix
     cell **`R`**. **ercot-220** (#4103) then searched for a dimensionally-correct
     stage-1 basis and found the candidate space **EMPTY ON MEASUREMENT**: every
     admissible availability-side basis cannot reach the 2023 object even in the
     ideal limit of reality's own telemetered PRC (windowed reservation offer p50
     **$650** at tail hours vs measured conduct $3,361–5,000, while over-firing
     ≥$1,000 offers in **1,170** hours against 181 tail hours), and every basis
     that fires at the right level is an online/commitment object behind the
     rule-13 wall. Written up as a **CLOSURE** with the commitment-side
     reconciliation escalated as a drafted card carrying a **DO-NOT-SIGN
     recommendation**. **ercot-221** (#4106) opened on the owner's verbatim
     dispatch (*"Ok yes let's do this"*, then *"I want you to do the adaptive
     battery fix for sure"*): the adaptive-expectation storage offer. Its
     **Phase-0 v2 verdict is a recorded FAIL as pre-registered** (G-ID daily
     correlation 0.447 vs 0.6; G-DECAY; G-SAFE-2024 by 0.0011), and **Phase-1 was
     entered ON OWNER INSTRUCTION over that standing kill** under the
     ercot-188/213/215 pattern, with the §4 direction-blind A/B kill table
     unchanged as the mechanical protection. Frozen constants (rule 23):
     `ercot_adaptive_half_life_days = 30.0`, `ercot_adaptive_beta = 3.0077` —
     **two identified constants, not four**. Amendment 3, on the owner's direct
     question *"You're not letting it see actual 2023 price right?"*, drops the
     measured RTORDPA overlay so the armed event series is the model's own P1
     energy dual **only — zero measured content**. **Keeper UNCHANGED throughout;
     the armed A/B is unregistered and in flight** (the live roster shows the
     lane IDLE on *"armed solve running (~50–70 min); awaiting scorecard"*).
   - **MISO — the owner RE-CHARTERED the lane he closed, and it executed.**
     #4069 closed C3a-2025 as a model-class limit at v8; **#4097 re-opened it**
     (miso-167), re-identifying the object as a **reserve-SUPPLY** defect:
     `_miso_design` leaves `ReserveDesign.online_gated = None`, so MISO's reserve
     requirement may be backed by headroom of capacity that is not synchronised.
     miso-168 (#4099) was **RAM-blocked a second time** and surfaced a real new
     finding — PREREG-miso167 §3's no-LP pre-check needs `unit_hourly` tranche
     grain **no MISO bundle has ever committed** — recording a corrected
     execution order with the prereg **unamended**. **miso-169** (#4107) then
     executed it end to end: **all §6 gates pass** (K-1 zero record-grain flips;
     K-2 pass; K-3 forced shares unchanged to 4 dp; K-5 textbook — 2025 rise
     +$10.12 in DA-foreseen scarce hours, **$0.00 RT-only**, regspin dual 12 h),
     magnitude **+0.10 pp on C3a-2025 against a +3.3 pp ceiling**. Matrix cell
     `reserve_deliverability_scoping` **R → O**. **Promotion ESCALATED, keeper
     UNCHANGED**, determination stays NOT-YET at full magnitude per the prereg's
     rule-1 clause, on two owner asks: resolve the **uncited `RHO_CLIP` 0.5
     floor** (measured MISO rho **0.1764** committed; re-solve is one `--set`),
     and adjudicate the **nyiso-143 D-4 per-unit conduct rider that now C8-FAILs
     any regenerated MISO artifact including the keeper's own diagnostics** — a
     cross-ISO governance collision, and the sharpest new item on the board.

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` at `598554e`)

| ISO | Designated keeper | Determination | This cycle |
|-----|-------------------|---------------|------------|
| ERCOT | `2026-08-17-ercot215-arm-decontam` | `NOT-YET` | **UNCHANGED, and re-resolved fresh at session start AND end by three separate lanes.** ercot-219 (#4098) **REJECTED-AS-ARMED on four gates**; ercot-220 (#4103) **CLOSED — candidate space empty on measurement**, card escalated DO-NOT-SIGN; **ercot-221 (#4106) Phase-1 entered on owner instruction over a recorded Phase-0 FAIL — armed A/B IN FLIGHT, unregistered**. Fail set unchanged {C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}; C3c the ledgered CAVEAT ×3 (68/181, 22/53, 1/31) |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `NOT-YET` | **Keeper unchanged; C1 flipped FAIL → PASS by rubric v3.4 (#4093), scorer-only.** Determination holds NOT-YET on a **lone C3a `price_mean` FAIL**. **caiso-202 (#4102)** decomposed it from committed bytes, **no LP**: it is **one year-invariant behaviour read through three scarcity regimes** — the model overprices every sub-$60 hour by +$10–14/h in ALL THREE years and underprices the >$60 tail, so the +4.1/+12.8/+15.7 % pattern is the **cancellation ordering, not three defects**; in 2024 ~**85 %** of the miss is the RT−DA settlement basis (vs DA the model is **+1.6 %**). **Every owner-named suspect ACQUITTED** (imports <5 %, biomass month-flat, coal 13 MW, solar bound measured by design). **caiso-203 (#4105)** then killed its own charter before building: the ordered object **already exists** as `caiso_firm_import_selfsched_clip`, built and promoted at caiso-151 eighteen days earlier — cell `caiso_firm_selfsched_floor` **O → K** as bookkeeping, **no solve spent** |
| PJM | `2026-08-15-pjm-162-inputclock` | `CALIBRATED` | **Unmoved, and untouched this cycle** — no PJM lane ran. Still `final`-NOT-YET on the merits (#4083); 2020 rung not data-ready |
| NYISO | **`2026-08-18-nyiso-144-layup-exclusion`** | `CALIBRATED` | **PROMOTED TWICE IN ONE DAY.** nyiso-143 (#4101) armed NYISO's **published Zone-K N-1-1 TSL (940 MW)** in place of the Locality Import Limit — rule 14 `[R-ACCURATE]` + rule 1 `[R-STRUCT]`, **zero new free parameters** (DOF 38→39, `n_residual` unchanged at 6), all six pre-registered gates silent, C3c **regressing** so it rode the owner's structure-over-gates clause. **nyiso-144 (#4104) superseded it the same day** with the bridge lay-up **membership** correction — one differing field, **no gated criterion regresses**, C3c bit-unchanged 2/0/5, so the clause is **not needed and not invoked**. `complete` re-keyed to nyiso-144 (rule 22 D-5(b)) |
| NEISO | `2026-08-17-neiso-99-joint-p1` | `CALIBRATED` | **Unchanged. neiso-101 (#4100) executed `final` precondition #2 — INTAKE ONLY, no LP, no year of any tier solved, scored or registered, nothing granted.** Result: **the data half is CLOSED**, and **two of the card's three "absent 2019 inputs" were already closed** by neiso-89 (the card quoted neiso-87 forward). **Zero tracked files modified**; determination reproduces CALIBRATED; `actual_tail` re-derive **byte-identical**. **EIA-923 2025 final vintage STILL NOT LANDED** |
| MISO | `2026-08-16-miso-160-wefor-shape` | `NOT-YET` | **Keeper unchanged — but the lane the owner CLOSED at v8 was RE-CHARTERED by him at #4097 and has now executed.** miso-167 re-identified C3a-2025 as a reserve-**supply** defect; miso-168 (#4099) RAM-blocked a second time + a real prereg data gap; **miso-169 (#4107) executed the prereg with ALL §6 GATES PASSING** and **escalated the promotion** on the `RHO_CLIP` band and the cross-ISO D-4 conduct rider. The ≥24 GB requirement is **RETIRED** (peak 13.95 → 12.40 GB) |

**Markers at HEAD (`598554e`, re-read this cycle):** `complete` =
**{NEISO, NYISO, PJM}** · **`final` = empty (`_note` only)** · **`holdout-freeze.json`
`active: true`**, and it outranks both marker blocks. **NO ISO HAS EVER SPENT A
LOCKED-TEST YEAR** — verified exhaustively rather than asserted: across all
**34** registered sidecars the solve-year histogram is **{2022: 2, 2023: 32,
2024: 32, 2025: 32}**, and the only two out-of-training registrations are the
authorized **2022 validation touchpoints** (PJM `2026-08-05-pjm-2022-touchpoint`,
NEISO `2026-08-06-neiso-2022-corrected-basis`). No 2019, no H1-2026, anywhere
([R-HOLDOUT]).
Determinations: **PJM, NYISO, NEISO `CALIBRATED`** · **ERCOT, CAISO, MISO
`NOT-YET`** — the CALIBRATED set is still exactly the `complete`-marker set.

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8 CLOSED**, **O5 CLOSED** (#4072, re-verified **stronger** at #4085 on a newer keeper set, residual third replay path **gated + tested**), **O4 re-measured and STILL OPEN** (#4085 — disposition act only, owner card, recommendation (A)) | **In progress ~91%** | **AUDIT-B gated at G3 — waiting by design.** Rows **O4, O6, O7** open |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, sibling-import residue retired, landing-verify green on merged main. Row B1 annotated **STALE** (#4085), no code change | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured** (ERCOT #4033, NEISO #4041, NYISO #4050, CAISO #4058, MISO #4060; **PJM never captured**). Changes: **(c) landed via #3964**, **(d)+(e) merged via #4067**, **(a)/(b) unstarted**. **Close-out note + wallclock baseline landed (#4075)** | **Paused ~74%** | **Paused, not blocked — and the restart precondition is now plausibly satisfiable (see banner).** On restart: freeze calibration, then re-verify every golden — RESTART CHECKLIST |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60%** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | Held by design | **Not started** | gated at **G3** |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED** (#4032); **BLOAT-3 ADJUDICATED** (#4031) and **EXECUTED** (BLOAT-S2 #4047, −444.5 MiB / 144 files at tip). **The chartered work stays completed — but the parity GATE went RED again at HEAD** | **Completed (charter) · gate RED** | **RE-OPENED.** `check_registry_payload_parity.py` run at `598554e` **FAILS** on two tracked bundle dirs mapping to no retained sidecar `bundle` field and not keep-required (Class-E point 4): **`ercot221_control_A`** (15 files, `18907e5`/#4106) and **`nyiso144_arm_recipe`** (one stray `meta.json`, `4769a64`/#4104). **Not a WS6 regression — fresh calibration output that outran its registration**, and the ERCOT one should clear itself when the in-flight ercot-221 A/B registers. Remediation already staged: the director session is **BLOCKED awaiting the owner's "go"** to issue the WS6 register/prune/keep-require lane. Back on the owner queue |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014). First scheduled cron came back **RED**, **diagnosed + fixed same-day** (#4071), **deliverables verified by a full local four-step job replay, all green** | **Completed** | **the fix is not in question. The CI proof is: STILL NO RUN since the red**, re-read live this cycle (5 runs total; latest `31999181985` red; last green `31913648051`). **The red WAS the Monday cron**, so waiting now costs a full week — next firing **Monday 2026-08-24 05:37 UTC**. One `workflow_dispatch` settles it — **top standing open item, sixth cycle** |

**WS1–WS5 are byte-unmoved this cycle.** Verified rather than assumed: across
all eighteen merges, the only WS-related documents touched are this board and the
plan's §8 ledger. No `.github/workflows/` file changed. Rows **O4, O6, O7**
remain the open audit rows, all three gated at G3 or awaiting an owner act.

## Stage-0 golden staleness (recomputed at `598554e`)

Re-derived at HEAD from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` — **not copied from v8**.

| ISO | Golden captured against | Designated keeper at `598554e` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` (#4033) | `2026-08-17-ercot215-arm-decontam` | **STALE — keeper moved twice** |
| NEISO | `2026-08-14-neiso-93-envelope` (#4041) | `2026-08-17-neiso-99-joint-p1` | **STALE** — the re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` (#4058) | `2026-08-17-caiso-200-h1-memberpanel` | **STALE** |
| MISO | `2026-08-16-miso-160-wefor-shape` (#4060) | `2026-08-16-miso-160-wefor-shape` | **CURRENT** — and the only one that stayed current, because miso-169 escalated its promotion instead of taking it |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` (#4050) | `2026-08-18-nyiso-144-layup-exclusion` | **STALE — and NO LONGER THE CHEAP CASE.** See below |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured** |

**Count: 4 stale / 1 current / 1 no-golden** — the same 4/1/1 as v8, but **NYISO's
staleness is now of a different kind and the v8 shortcut for it is dead.** v8
recorded NYISO as cheap to re-establish because nyiso-142 was a data correction
with 718/718 `scenario_config` fields identical to the captured nyiso-140, so a
sidecar comparison could substitute for a solve. **Two promotions later that is
false, measured field-by-field against the two committed `run_config.json`s:**
nyiso-140 (717 fields) vs nyiso-144 (722) share 717 common fields, of which
**`nyiso_li_tsl_n11_security` differs in value (False → True)**, and
**`nyiso_gas_bridge_plant_exclusions` is a NEW field armed True**. That is **two
armed mechanism deltas**, not zero — so **NYISO now needs a real re-capture**,
and it is the ISO whose golden is furthest from its keeper.

**The lane's finding stands and hardened this cycle:** stage-0 could not converge
because ISO keepers moved faster than captures completed. At v8 that was a
retrospective claim about six cycles; **this cycle NYISO staled its own golden
twice in a single day.** A calibration freeze remains the precondition for
completing WS3 — and unlike at v8, calling it now **would** interrupt an armed
lane (ERCOT's ercot-221 A/B is running).

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE while WS3 is paused.** Leg 1 is *PERF-B merged byte-green*,
  PERF-B is paused by owner decision, and no other leg substitutes. The legs:
  1. **PERF-B merged byte-green** — partial: 5 of 6 captured, **4 now stale**,
     (c)/(d)/(e) merged, (a)/(b) unstarted. **Paused and still short:** byte-green
     needs goldens, and byte-green cannot even be *claimed* while the golden tier
     has no green CI run.
  2. **One completed fast-tier-green `ci.yml` run** — the sparse block landed
     (#3964, runner-validated at 31873178938: 6838 passed / 31 skipped).
  3. **A keeper freeze** — **owner call, outstanding across seven director
     cycles. NO LONGER CHEAP: the v8 "newly reachable" reading is RETRACTED.**
     At this HEAD ERCOT has an armed A/B in flight, MISO has an escalated
     promotion pending two owner answers, and NYISO promoted twice in the last
     24 h. Declaring the freeze now interrupts live lanes; declaring it at v8
     would not have. The cheapest re-open is after ercot-221 scores and MISO's
     two asks are answered.
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict,
  its chartered execution **and now its parity gate** are all satisfied
  (#4031 + #4047 + measured green); the golden-tier proof leg is satisfied by
  #4014 + the green dispatch.
- **G4** — unchanged: SITE-A + AUDIT-B.

## Watch

- **🟡 GOLDEN-TIER CI PROOF — sixth cycle, and the cost of waiting just went up.**
  Fix merged (#4071) and verified by full local job replay; **no CI run since the
  red `31999181985`**, re-read live this cycle. Until one runs, BLOAT-S2's D3 leg
  and every byte-green claim are unprovable. **The red *was* the Monday cron**, so
  the passive option is now a **full week** (next firing Monday 2026-08-24
  05:37 UTC), not "wait for Monday". One `workflow_dispatch` settles it.
- **🔴 NEW — BLOAT-2 parity RED again, and the remediation is blocked on one
  word.** Two tracked bundle dirs at HEAD map to no retained sidecar
  (`ercot221_control_A`, `nyiso144_arm_recipe`). The **director session itself is
  sitting BLOCKED** on *"say go to issue the lane for WS6 register/prune/keep-require"*.
  This is the cheapest open item on the board.
- **🔴 NEW — a CROSS-ISO GOVERNANCE COLLISION, raised by miso-169 and unadjudicated.**
  The **nyiso-143 D-4 per-unit conduct rider** now **C8-FAILs any regenerated MISO
  artifact — including the MISO keeper's own `legitimacy_diagnostics.json`.** A
  scorer-side change made in one ISO's lane is reaching another ISO's committed
  diagnostics, which is precisely the shape rule 25 `[R-ISO-SCOPE]` exists to
  prevent. Nothing is broken *on the dashboard* today because MISO's artifacts
  have not been regenerated — which is exactly why it needs adjudicating before
  something regenerates them.
- **🟠 NEW — the uncited `RHO_CLIP` 0.5 floor.** miso-169 measured MISO's own
  rho at **0.1764** and committed it, then found the clip floor at 0.5 carries no
  citation — a rule 5 `[R-NO-MAGIC]` exposure sitting inside a mechanism whose
  promotion is already escalated. **The re-solve is one `--set`.**
- **DURABLE LESSON (unchanged, and the reason the golden item matters):**
  `golden-data-tier.yml` is the **ONLY** workflow that runs
  `scripts/regenerate_clean.py`, so **any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal** — invisible to every PR
  check, surfacing only on the weekly cron, and compounded by `data/clean` being
  derived and gitignored. **Treat curate-script changes as unguarded.**
- **🟠 #4054 / nyiso-140 null-treatment question — STILL OPEN, NEVER ADJUDICATED,
  and now HARDER than when it was called matrix hygiene.** v8 recorded the cell
  verdict `K` as carrying forward unchanged because nyiso-142 was 718/718
  config-identical. **Two promotions later the NYISO keeper carries two armed
  mechanism deltas past that point** (§ stage-0 above), so "re-checking it costs
  a fidelity read, not a solve" **can no longer be asserted without re-deriving
  it**. Still bears on the evidence rather than the keeper's numbers.
- **🟢 RETIRED — the ≥24 GB MISO container ask.** Created by the dispatch,
  retired in the same cycle by miso-169's measurement (13.95 → 12.40 GB peak;
  full 3-year control replay green on the 15 GB box).

## Owner queue at cycle end

Carried from v8, **re-ordered and re-verified at `598554e`**. The dispatch's own
rank 0 ("three unmerged lane branches — THE OWNER MERGES") is **retired unmet-but-
moot: all three merged before this read**, and its rank 2 (MISO ≥24 GB) is
**retired on measurement**. Two new items replace them.

0. **🔴 GOLDEN-TIER PROOF-OF-FIX `workflow_dispatch`** — the #4071 fix is merged
   and locally replayed green; the tier's latest CI run is still the red one,
   re-read live this cycle. **Sixth cycle.** Billed minutes, so the owner's call —
   but note the passive alternative is now a **full week**, because the red *was*
   the Monday cron. *(Carried from v7/v8; unchanged in substance.)*
1. **🔴 NEW — say "go" on the WS6 register/prune lane.** BLOAT-2 parity is RED at
   HEAD on two unregistered bundle dirs, and the **director session is already
   sitting blocked** on exactly this word. Cheapest item on the board.
2. **🔴 NEW — adjudicate the nyiso-143 D-4 per-unit conduct rider**, which
   **C8-FAILs any regenerated MISO artifact including the MISO keeper's own
   diagnostics**. A rule 25 `[R-ISO-SCOPE]` exposure raised by miso-169. Pairs
   with the **uncited `RHO_CLIP` 0.5 floor** (measured MISO rho 0.1764; re-solve
   is one `--set`) — together these are what miso-169 escalated its promotion on.
3. **NEISO-100/101 keeper-candidate + EIA-923 2025 vintage.** neiso-101 (#4100)
   closed the **data half** of `final` precondition #2 with **zero tracked files
   modified** and a byte-identical `actual_tail` re-derive; **the 2025 final
   vintage is re-checked and STILL NOT LANDED**, and one remaining item is
   explicitly **not** a data item.
4. **Validation-freeze lift signature** — the **O4/O5 card**
   (`AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4), recommendation **(A) close the
   charter with cause, lift the VALIDATION tier only, leave `final` empty**. The
   detector question is closed on evidence; "resolve the detector question" is
   not one of the choices.
5. **WS3 restart / calibration freeze — THE v8 WINDOW HAS LAPSED, and the
   director did NOT re-serve it this cycle.** The v8 reading (declaring it would
   interrupt nothing) is **retracted**: ERCOT's ercot-221 A/B is armed and
   running, MISO's promotion is escalated pending the two asks at rank 2, and
   NYISO promoted twice inside 24 h. **The cheapest re-open is after ercot-221
   scores and MISO's asks are answered** — not after a set of merges, which is
   how the dispatch framed it before those merges landed.
6. **O6 — locked-test scheduling.** 2019 and H1-2026 are **touch-once** and **no
   ISO has ever spent one** — re-verified exhaustively at this HEAD across all 34
   registered sidecars (year histogram {2022: 2, 2023: 32, 2024: 32, 2025: 32}).
   `complete` = {NEISO, NYISO, PJM}; `final` holds only its `_note`; the freeze is
   `active: true` and outranks both. **Never let a lane spend one**; scheduling is
   the owner's alone.
7. **O7 — ERCOT P0 bit-identity proof forfeited** (accept-and-document, or
   charter restoration).
8. **decision-1 ack** — warm-start closed-overtaken; **still unacked, SIXTH
   cycle**; a one-word ack retires it.
9. **caiso-199 NOT-YET determination** — carried. The CAISO lane produced two
   further no-solve closures this cycle (#4102, #4105) and moved no keeper.
10. **ercot-214 counterpart-decontamination lever** — carried; superseded in
    practice by the ercot215 promotion (#4070), which is the decontamination arm.
11. **RETIRED THIS CYCLE:** ~~the ercot-218b option-B card~~ (**SIGNED and
    executed to a rejection** — ercot-219 #4098, four gates at full magnitude);
    ~~"NYISO frontier re-declaration in flight"~~ (landed twice: nyiso-143's
    answer was **NOT YET FRONTIER**, and nyiso-144 superseded it the same day with
    **still NOT-YET, but blocked on decisions and one data purchase rather than on
    investigation** — three of its four open items are no longer research
    questions); ~~three unmerged lane branches~~ (**all merged**);
    ~~MISO needs a ≥24 GB container~~ (**retired on measurement**).

## Session roster

> **🟢 DEVIATION CLOSED — THIS IS A LIVE READ.** `list_sessions` (`mine: true`,
> limit 30) **returned successfully** this cycle, after returning *"requires
> approval"* on four attempts at v7 and two at v8. The dispatch expected a third
> consecutive failure and pre-authorised a commit-trailer rebuild; **that fallback
> was not needed for the active lanes.** One honest limit: the call returned 30
> sessions with `has_more: true`, and its window covers 2026-08-19 back to
> 2026-08-14 **with a gap** — three lanes that merged earlier on 2026-08-18
> (ercot-219, nyiso-143, neiso-101) do not appear in the returned page. Those
> three rows only are rebuilt from `Claude-Session` commit trailers plus live
> branch state, and are marked **(trailer)**. Everything else below is live.

**Lanes active this cycle**, with live session status where the read covered them:

| Lane | Session | Branch | Landings | Live state |
|------|---------|--------|----------|------------|
| **Records v9 (this lane)** | `session_015jiqUxjYAVkaZhTEijkRPG` | `claude/director-records-v9-x2upg1` | board v9 + §8 entry | RUNNING |
| **Program director** | `session_01FKuWvSm52VoT7nhffjQ3J3` | `main-fresh` | — | **IDLE / BLOCKED** — *"WS6 register/prune ready; awaiting go to issue lane"* |
| ERCOT ercot-220 / 221 | `session_01RwVbPYK5zLy7pRUx4snrcW` | `claude/ercot-220-lever-phase0-je3znm` @ `18907e5` (merged, branch live) | #4103 · #4106 | **IDLE** — *"armed solve running (~50–70 min); awaiting scorecard for keeper judgment"* |
| ERCOT ercot-221 prep (read-only) | `session_018eECR6ZSrjBbj2tBjcFypv` | `claude/ercot-lmp-miss-analysis-cde845` @ `3f13c62` — **UNMERGED, 1 ahead** | none yet | IDLE / review-ready — *"2022 regime analysis: 136/181 keeper margin, 15.3 % price adder"* |
| MISO miso-169 | `session_012TsGH4LGJbqyg3D9dxZkwm` | `claude/miso-reserve-online-gated-mgcad8` @ `f542b71` (merged, branch live) | #4107 | **RUNNING** — *"promoting run (C6 attestation + edit script)"* |
| MISO miso-168 | `session_01NB9PmpZ2af8okcFKDzHYe3` | `claude/miso-reserve-online-gated-colcr1` (merged, branch live) | #4099 | ARCHIVED |
| MISO (RAM-blocked, superseded) | `session_01TZBFnycWKAT4NBFK1tr2Uz` | `claude/miso-reserve-online-gated-jzmiaa` | none | ARCHIVED — *needs_action: "provision ≥24 GB RAM"* — **the ask miso-169 retired** |
| MISO miso-166/167 re-charter | `session_017czfaSwYWD17VjWoY4vUyC` | `claude/miso-166-gate-unblock-ojjazz` | #4097 | merged + deleted |
| NYISO nyiso-144 | `session_01CCXWVoEg8Rx7QKeXefQQYo` | `claude/nyiso-downstate-scarcity-hpa75j` | #4104 | IDLE — *"keepership decision: structural gates close, recommend archive"* |
| CAISO caiso-203 | `session_019vy7V9N5iAmhfQGN2yDAWf` | `claude/caiso-firm-selfsched-floor-36maq9` | #4105 | IDLE — *"3 decisions for owner; no further work pending"* |
| CAISO caiso-202 | `session_018mA81B3qg3aikPpqnAU56e` | `claude/caiso-c3a-lmp-overrun-2k2xt3` | #4102 | ARCHIVED |
| CAISO rubric v3.4 | `session_018ZGxsfHCnntcLMhzQTPKXP` **(trailer)** | `claude/caiso-c1-lmp-pricing-ung9yv` | #4093 | merged + deleted |
| NYISO nyiso-143 | `session_01A4fJWnSf8mmgK8xELcuqMJ` **(trailer)** | `claude/nyiso-frontier-redeclaration-191c6i` | #4090 · #4092 · #4095 · #4101 | merged + deleted |
| NEISO neiso-101 | `session_01XQKk26kNqgzhcT5FCVZgFg` **(trailer)** | `claude/neiso-2019-input-prep-p1ih50` | #4100 | merged + deleted |
| ERCOT ercot-219 | **unresolved** — no `Claude-Session` trailer on `142b2f5`, and absent from the returned page | `claude/ercot-219-option-b-phase1-5cs9bf` @ `142b2f5` (merged, branch live) | #4089 · #4091 · #4096 · #4098 | — |
| Records v8 | `session_019BVioYTbFDd74HePiaVxb7` **(trailer)** | `claude/director-records-v8-ledger-78e25q` | #4094 | merged + deleted |

**Live remote branches** (complete set at this read, `git ls-remote --heads`):

| Branch | SHA | Read |
|--------|-----|------|
| `main` | `598554e` | tip (merge of #4107) |
| `claude/ercot-219-option-b-phase1-5cs9bf` | `142b2f5` | **merged** (#4098); branch not deleted |
| `claude/ercot-220-lever-phase0-je3znm` | `18907e5` | **merged** (#4106); branch not deleted |
| `claude/ercot-lmp-miss-analysis-cde845` | `3f13c62` | **UNMERGED, 1 commit ahead** — the only genuinely open branch |
| `claude/miso-reserve-online-gated-colcr1` | `dd5f59e` | **merged** (#4099); branch not deleted |
| `claude/miso-reserve-online-gated-mgcad8` | `f542b71` | **merged** (#4107); branch not deleted |
| *(this lane's branch once it pushes)* | — | board v9 + §8 entry |

Note what is **absent**: `claude/director-records-v7-9u1czg` and
`claude/ercot-218-direct-driver-5ckiur`, both listed live at v8, have since been
deleted. **PERF-B lanes remain STOOD DOWN** per the owner's pause; all merged and
deleted.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each workstream
as **not started / in progress with % / completed / pending blockers**;
(3) issues prompts for any lane whose gate has cleared, appends the §8 ledger
entry, and updates this board in the same pass.

**v9 lesson — the records lane must re-verify, not transcribe.** This cycle's
dispatch was written against `eb2fe60` and **ten PRs landed before the records
lane read HEAD**. Five of its factual premises were stale by then, including its
own headline and two owner-queue ranks. The instruction that saved the record was
the dispatch's own — *"verify every number below against HEAD before writing it;
correct anything that has moved"* — and it should stay in every future records
prompt. **A records lane that transcribes a director read is a liability on a
program whose lanes merge hourly.**

**Under the standing deviation, step (3)'s two write duties are dispatched to a
records lane rather than pushed by the director.** A refresh is not complete
until that lane has landed both files — and, per the v5→v6 gap, a dispatch that
is never launched leaves the board silently wrong. **Verify the landing before
declaring a cycle done.**

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh should confirm only (a) whether the golden tier is
proven green **in CI** after the #4071 fix, (b) whether the owner has ruled on
anything in the owner queue, and (c) whether the keeper freeze has been called —
that last one is the un-park trigger. **At v9 (c) has moved back out of reach:**
the v8 reading that declaring the freeze would interrupt nothing is retracted,
and the freeze is once again a call with a real cost attached (§ owner queue
rank 5).

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

1. **FREEZE CALIBRATION FIRST.** The precondition, not a nicety — the owner must
   declare it and no lane can. Until it holds, every golden captured can be staled
   by the next promotion, which is exactly how stage-0 failed to converge across
   seven cycles. **The v8 note that the cost of declaring it "is at its lowest" is
   RETRACTED at v9:** ERCOT has an armed A/B in flight, MISO has an escalated
   promotion pending two owner answers, and NYISO staled its own golden twice in a
   single day. Re-read the live lane state before assuming the window is open.
2. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read
   `frontend/data/backcast/keepers/<ISO>.json` and
   `results/regression-goldens/perfb-stage0/manifest.json` at that HEAD and
   re-derive it.
3. **Re-capture what is stale, and know which are cheap.** At `598554e`: ERCOT,
   CAISO, NEISO, **NYISO** stale; PJM never captured; **MISO the only current
   one.** **NYISO IS NO LONGER THE CHEAP ONE** — v8's shortcut rested on
   nyiso-142 being 718/718 `scenario_config`-identical to the captured nyiso-140,
   and two promotions later the keeper carries **two armed mechanism deltas**
   against that capture (`nyiso_li_tsl_n11_security` False → True, plus the new
   `nyiso_gas_bridge_plant_exclusions` armed True). **NYISO needs a real
   re-capture.** The **re-stamp-not-re-solve** shortcut was established for
   **neiso-97 only** and NEISO has since moved to neiso-99 — **re-establish it
   before relying on it.** Apply the sidecar-comparison test to every newly-stale
   ISO before spending a solve, but **re-derive the config diff first** rather
   than inheriting a prior cycle's "cheap" label.
4. **Capture PJM** — the one ISO with no golden at all, and the one gap no amount
   of keeper stability closes.
5. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at HEAD.
   Verify the blob (`af34031c`) rather than re-porting it.
6. **Close the #4054 residual if you want belt-and-braces** — a fidelity-only
   re-check at HEAD (hash compare, **no solve**) confirms the exclusions were
   active in the NYISO capture. Optional; the captures are already cleared on
   code-state evidence. **The nyiso-140 A/B question is separate and still
   unadjudicated** — it bears on the evidence, not the keeper's numbers — but
   v8's "the cell verdict `K` carries forward unchanged, so re-checking costs a
   fidelity read not a solve" **no longer holds without re-deriving it**: the
   keeper has moved through nyiso-142 → 143 → 144 and now differs from the
   captured config on two armed mechanisms.
7. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures.
8. **Confirm the golden tier is green IN CI before claiming any byte-green
   result.** The #4071 fix has landed and replays green locally, but **its CI
   proof is still outstanding** — one `workflow_dispatch`, or the next weekly
   cron. A tier that cannot provision `data/clean` cannot prove byte-identity of
   anything, and a local replay is not the gate.
