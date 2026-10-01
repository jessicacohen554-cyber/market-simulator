# PRECHECK — caiso-204: Phase-0 of the ADAPTIVE-EXPECTATION storage scarcity offer, CAISO transfer test (rule 25: enters CAISO as U — own event threshold, own window, own constants, own conduct identification; NOTHING transfers from the ERCOT verdict)

**Session caiso-204, 2026-08-19, branch `claude/caiso-adaptive-storage-offer-l4bx2t`
off main 3fef613. Keeper at pin: `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET
under rubric v3.4; C3a the sole load-bearing FAIL +4.1 PASS/+12.8/+15.7 % vs
actual RT LMP; C3c the single ledgered caveat 0h/47, 1h/35, 2025 PASS).**
This file is pushed and blob-verified BEFORE the identification probe fits
anything and BEFORE any bid-corpus value is read. NO SOLVE in Phase-0.

Charter: the owner re-opening of the rested CAISO lane for this ONE lever
(direct owner dispatch 2026-08-19, "test the adaptive battery offer lever on
CAISO"), bound by the caiso-203b owner rulings
(`results/calibration/caiso203-owner-rulings-2026-08-19.md`): C3a is judged
against ACTUAL (RT) LMP — no DA-basis framing anywhere in this lane — and NO
funded data intake in any branch.

## 0. THE DATA ACTION AND ITS READING, STATED UP FRONT (charter Phase-0 step 1)

Phase-0's identification needs CAISO's measured daily evening storage offer
surface. Source = the OASIS `PUB_BID_DAM` public-bid corpus, whose payload is
gitignored (`data/raw/caiso-public-bids/README.md`) and therefore absent from
this fresh clone. **This session re-fetches a subset of that already-established
public corpus. Reading relied on: the caiso-203b ruling's own scope note —
"a zero-cost re-fetch of an already-established public corpus (the OASIS
PUB_BID_DAM re-fetch pattern of caiso-150/151) is not a funded intake and is
not struck by this ruling." This is that pattern exactly: the fetcher is the
committed `scripts/data/fetch_caiso_public_bids.py`, 6 s spacing, no new
source, no cost.** If the owner objects to this reading, the work is
data-blocked and stops (the standing blocker discipline). Reachability was
verified before this push (one GroupZip request, 2024-07-10, valid 434 KB zip).

DO-NOT-REDO adjacency, addressed explicitly:

- caiso-178 §8 bans re-fetching this corpus **"to identify `battery_dispatch_
  adder`"** and bans **"reading the first discharge rung as a marginal cost"**.
  This session does NEITHER: the question here is the *conduct dynamics* of the
  evening offer surface (does it track trailing spike experience?), which is
  exactly the object caiso-178 §4 established the bid to be — "a dispatch-intent
  object", NOT a cost. The adaptive-expectation mechanism prices intent, so
  caiso-178's structural result is this instrument's foundation, not its bar.
  `battery_dispatch_adder` stays 5.0 untouched in every branch.
- caiso-203 §G bans regenerating `caiso_intertie_selfsched_ceiling.csv` from a
  re-fetch with no source change — not touched here (storage resources only,
  a different derived object).
- `storage_daily_cycling` G, `caiso_ps_charge_shape_anchor` G,
  `caiso_da_rt_two_settlement` R (governance-closed), `storage_measured_anchors`
  K, the caiso-131 §10 offer rungs: none is re-tested, re-derived or re-tuned.

## 1. THE MECHANISM FAMILY (CAISO form, pinned)

Same family as `ercot_storage_adaptive_expectation` (mechanism-matrix.js row;
PRECOMMIT-ercot221 §1 + Amendments 1–4), re-derived on CAISO's own regime. The
v2 (two-constant) form is the family tested — ERCOT's v1 regime-uncertainty
prior term is NOT carried: its own ablation measured zero identified work
(corr 0.006) and CAISO's training window contains no ECRS-like design go-live
to date-gate a prior on (a prior with no driver instrument would violate rule
17's spirit).

- **Event**: `S(d) = 1` iff day *d*'s maximum hourly CA-system price ≥
  **$200/MWh**. CAISO's own threshold, derived two independent ways that
  converge, declared before any response value exists:
  (a) the repo's frozen CAISO scarcity-tail threshold (rubric §5,
  `frontend/data/backcast/tail/actual_tail.json` `thresholds.CAISO = 200.0`,
  fixed 2026-07-16 — long before this charter, and the exact tail C3c gates
  on); (b) cap-regime proportionality: ERCOT's $1,000 event sits at 20 % of
  its $5,000 cap regime; 20 % of CAISO's $1,000 soft energy bid cap = $200.
  **NEVER ERCOT's absolute $1,000**: the measured CA system RT maximum over
  2023–2025 is $907 (2023), so a $1,000 event definition is degenerate
  (all-zero series) in the entire training window — it is reported below as a
  diagnostic, not used.
- **Identification driver**: measured CA hub RT daily maxima from the committed
  `actual_lmp_hourly_CAISO.parquet` (`rt`, nan-aware) — prices as
  identification evidence about conduct, the sanctioned rule-13 class
  (ercot-210/211/218/221 precedent). Measured event days at $200:
  **2023: 22, 2024: 9, 2025: 5** (dates listed in the probe record).
- **Armed event basis (if ever built)**: the model's OWN CA demand-weighted P1
  scored price = λ + the model's own `caiso_scarcity_overlay` adder (the
  post-solve LOLP × (VOLL − λ) adder, Tariff §39.6.1 parameters, already
  written into the keeper's scored prices) — both outputs of its own solve,
  ZERO measured content (the ercot-221 Amendment 3/4 discipline, applied here
  from the start: CAISO's scored settle basis already contains its scarcity
  expression, so there is no residual model-side term left to add later).
- **Trailing state**: `P_trail(d)` = normalized EWMA of `S` over the trailing
  **120** days strictly before *d* (uses `S(d−1)` and earlier), half-life λh
  (days, identified). Per-solve-year reset (day 0 reads 0) — same pinned
  limitation as ERCOT, disclosed.
- **Expectation**: `P_hat(d) = clip(β · P_trail(d), 0, 1)`, β ≥ 0 identified.
- **Offer floor (armed)**: each CAISO battery's discharge cost floored at
  `max(vom, P_hat(d) × $1,000)` in window hours only. **$1,000 = CAISO's soft
  energy bid cap — the level the measured fleet actually parks at (caiso-178
  §3: modal first discharge rung $1,000 in all three years) — NOT the $2,000
  justified-cap ceiling and NOT the overlay VOLL.** Outside the window the
  keeper's storage offer is unchanged (the ercot-219 G-BAT whole-day-floor
  lesson).
- **Window**: hours **{18, 19, 20, 21} PT** (hour-beginning, prevailing time) —
  CAISO's evening net-load peak, and the four contiguous hours with the highest
  measured cheap-bid concentration in caiso-178 §4 (ratios at h18–21:
  1.68/1.89/1.73/1.45 in 2023; peak h19 in all three years). NOT ERCOT's
  h17–20 CST.
- **Orchestration (if armed)**: two-pass P1 through the existing
  `run_energy_solve(p1_storage_discharge_cost=…)` seam, exactly one adaptation
  pass, P0 untouched — the committed ercot-221 pattern in
  `scripts/run_calibration.py`, behind a NEW caiso-gated default-off
  `ScenarioConfig` field (the ERCOT field is never widened — rule 25).

Free parameters: **λh, β** — two, identified from CAISO's own measured conduct;
plus conventions ($200 event; 120-day trail; h18–21 PT; per-year reset; one
adaptation pass; $1,000 park cap), disclosed here as conventions.

## 2. THE IDENTIFICATION INSTRUMENT (pinned)

**Corpus subset (deterministic day-selection rule, declared before any fetch):**
for each year 2023–2025, the union of (a) every 6th day of year (doy ≡ 1 mod 6,
1-based), giving seasonal balance by construction, and (b) each measured $200
event day *e* and the 21 days after it (dense sampling of the decay the
trailing term must explain), minus the known OASIS archive hole 2023-06-01.
**585 trade dates (2023: 282, 2024: 172, 2025: 131).** Fetch via the committed
fetcher at its 6 s spacing; every fetched-vs-failed date is reported (rule 15,
no silent caps — the selection rule above IS the coverage, stated here).

**Storage classification**: caiso-178's price-blind classifier, reused with its
committed thresholds (`derive_caiso_battery_bid_floor.py`: S1 withdrawal-capable
|MW| ≥ 1.0 both sides; S2 wd_frac ≥ 0.50; S3 sym ∈ [0.5, 2.0]; S4
pumped-storage exclusion ≥ 200 MW stable across years). One adaptation, forced
by the subset and declared here: S2's absolute floor `en_hours ≥ 500` (defined
on a 365-day scan) becomes the same per-day density on the fetched subset,
`en_hours ≥ 500 × (fetched_days_year / 365)`. No other threshold moves.

**Response**: for each fetched trade date *d*, the **MW-weighted p50 of
discharge-side (MW > 0) energy-bid segment prices of storage-classified
resources over hours 18–21 PT** (DST-exact America/Los_Angeles, the caiso-178
hod convention; segment volume = the caiso-178 discharge-width construction).
`implied_P(d)` = response ÷ $1,000 (the soft-cap park level). A day is
admissible with ≥ **40** segment rows in the window (the ercot-154 convention;
CAISO's 77–167-resource fleet clears this trivially — reported, not binding).

**Fit**: least squares of `implied_P(d)` on `P_hat(d; λh, β)` over admissible
days across all of 2023–2025 (per-year reset), grid λh ∈ {5, 7, 10, 15, 20,
30, 45} d, β ≥ 0 by OLS per grid point. For gate comparisons only, the
prediction is `max(β · P_trail × $1,000, base)` where `base` = the median
evening response over admissible **quiet days** (no $200 event in the trailing
120 within-year days, so `P_trail = 0` by construction — an identification
window disjoint from the trail term's; in the LP the standing ask is carried by
the keeper's storage offer, so `base` never enters the armed floor).

## 3. PHASE-0 GATES (ALL must PASS to enter Phase-1; any FAIL stops the lane, recorded unrewritten)

| gate | rule |
|---|---|
| **G-DRIVER** | the measured $200 event series is non-degenerate: ≥ 10 event days total 2023–2025 AND ≥ 2 calendar quarters (of any year) with ≥ 2 events. *Known at declaration: 36 days spread across winter and summer episodes — this gate documents that the threshold choice yields identifying variation; the $1,000 diagnostic series (0 days) is reported alongside.* |
| **G-COV** | ≥ 250 fetched-and-parsed trade dates; ≥ 15 admissible days per calendar quarter-of-year pooled across years; fidelity — on the fetched subset, the per-year share of storage first-discharge-rungs priced > $15 within ±10 pp of caiso-178's committed full-corpus values (89.5 / 81.3 / 81.6 %) |
| **G-ID** | daily corr(`implied_P`, `P_hat`) ≥ 0.6 over admissible days (full-span fit), AND among (year, month) cells with ≥ 5 admissible days, ≥ 60 % have predicted monthly median within ±35 % of measured |
| **G-DECAY** | fit on 2023 admissible days ONLY → predict the 2024 AND 2025 (year, month) cells with ≥ 5 admissible days; ≥ 60 % within ±50 %. AND the base-only ablation (β = 0, prediction ≡ `base`) must FAIL G-ID's correlation leg — the trailing term must do identified work |
| **G-BOOT** | (bootstrap feasibility — the armed path reads only the model's own scored path) on the keeper's committed scored price paths (`hourly/system_<yr>.parquet`, CA-zone demand-weighted, the same series C3c is scored on): (i) ≥ 3 model event days (daily max ≥ $200) in ≥ 1 training year; (ii) with the fitted constants, the implied in-window floor reaches ≥ $200 in ≥ 12 window-hours of that year. **Ex-ante expectation, recorded for honesty: leg (i) is expected to FAIL — the keeper's committed C3c record (model 0 h / 1 h / 0 h ≥ $200) already implies model event days 0 / 1 / 0, verified from the sidecars before this push. The gate is declared and measured exactly, not assumed.** |
| **G-SAFE** | (self-extinction falsifier) with the fitted constants, `P_hat` on the keeper's committed 2023 and 2025 scored paths yields windowed floors ≤ vom + $100 in ≥ 95 % of ALL hours each year — the mechanism must be a predicted no-op in the years the keeper already passes (2023 C3a PASS, 2025 C3c PASS). *Expected trivial PASS for the same reason G-BOOT is expected to fail (0 model event days both years) — the two gates are the two sides of the same committed-path fact, and are reported together.* |

Verdict rule, mechanical: ALL six gates PASS ⇒ Phase-1 (build + A/B per the
charter, its PRECHECK pushed before any solve). ANY gate FAIL ⇒ the lane stops,
the verdict is recorded unrewritten in
`results/calibration/caiso204_adaptive_phase0.json`, the CAISO cell is stamped
from the failure mode — conduct absent (G-ID/G-DECAY fail) → **R**; conduct
present but the armed path infeasible on this keeper (G-BOOT the sole
structural fail) → **I** with the wall recorded — and Phase-1 entry over a
recorded FAIL requires EXPLICIT owner instruction (the ercot-188/213/215/221
pattern), never assumed.

Direction hazard, restated from the charter: C3a is inadmissible as acceptance
evidence in EITHER direction, and every price number in this lane is against
ACTUAL RT LMP. No gate above reads a price residual of the model; G-BOOT/G-SAFE
read the model's own committed path only to ask whether the mechanism CAN fire,
never whether firing improves the fit (rule 1 / rule 13).

## 4. BUILD FENCES (Phase-1 only, restated so they are pinned before any pass)

Rule 27 (Fable session; edit locally, blob-verify ≥ 300-line pushed files);
rule 25 (caiso-gated NEW field, ERCOT field untouched, cross-ISO byte-identity
seam proof with the flag ARMED); rules 5/23/24 (both constants + conventions as
registered `ScenarioConfig` fields with citations, no off-registry channel);
rule 28(c) (new family row already exists — the CAISO test stamps the CAISO
shard cell; a NEW CAISO-gated field adds its own matrix row + a cell line in
EVERY shard in the build commit); rules 15/16 (both A/B members registered with
payloads, all three years in one bundle per member, same session); rule 22
({2023, 2024, 2025} only; holdout freeze ACTIVE); rule 12 (years sequential
within each invocation, the two members concurrent); no new workflows, no cron,
no PR. MUST NOT REGRESS: C3b (0.097/0.174/0.181 vs 0.20), C8, C6. DOF ledger
10/7 may only hold (the two adaptive constants would enter with
measured-conduct identification lines, not residual lines).
