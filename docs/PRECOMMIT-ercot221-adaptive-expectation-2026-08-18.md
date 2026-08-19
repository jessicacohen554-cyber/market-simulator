# PRECOMMIT — ercot-221: the ADAPTIVE-EXPECTATION storage offer (`ercot_storage_adaptive_expectation`) — rule family, identification instrument, and kill gates, pinned BEFORE any fit and BEFORE any solve

**Session ercot-221 (in the ercot-220 session, owner-dispatched), 2026-08-18,
branch `claude/ercot-220-lever-phase0-je3znm`. Keeper at pin:
`2026-08-17-ercot215-arm-decontam` (NOT-YET, {C3a-2023 −40.1 %, C3b-2023
0.736}, C3c ledgered CAVEAT ×3).** This file is pushed and blob-verified
BEFORE the identification probe fits anything and BEFORE any solve.

## 0. THE OWNER DISPATCH (verbatim, recorded per the X-1/X-2/B-1
signature-by-dispatch precedent)

On the ercot-220b recommendation (charter a Phase-0 of the adaptive
expectation offer — the family DECISION-CARD-ercot218b §2 reserved as "its
own future card"):

> "Ok yes let's do this"

and, mid-session, strengthening the authorization to the full lane:

> "I want you to do the adaptive battery fix for sure"

This constitutes the owner card for the family. Scope granted: Phase-0
identification, and — **only if every Phase-0 gate passes** — the Phase-1
build and full-span A/B in the same session. The "for sure" buys the
attempt, not the answer: a Phase-0 or A/B kill is recorded unrewritten and
nothing is armed (promotion over a kill remains a separate explicit owner
act, the ercot-188/213/215 pattern). B-2 remains UNSIGNED and untouched by
this lane — no capability, commitment or telemetry input changes.

## 1. THE MECHANISM (pinned)

**What it models:** the 2023 storage fleet's scarcity conduct was an
*adaptive expectation* — batteries priced scarce SOC at the experienced
recent frequency of deep-scarcity events times the cap, parking at the cap
in the weeks after the ECRS design change while the new regime was unknown
(evidence: RESEARCH-ercot220b §2 — Sep-2023 implied P 0.81 tracks the
trailing-30d realized frequency 0.53, not its own month's 0.13; Jun/Jul park
at implied 1.00 on trailing ~0; measured storage conduct $3,361–5,000 p50 at
matched tightness vs any physically-implied same-hour offer ≤ $650 p50,
FINDING-ercot220 §6).

**The rule family (all constants identified in Phase-0 from measured 2023
conduct, then FROZEN — rule 23; never residual-tuned):**

- Event: `S(d) = 1` iff day *d*'s maximum hourly settled price ≥
  **$1,000/MWh** (the deep-scarcity range; the RESEARCH-ercot218b §5
  spike-day convention). In the identification instrument the price is the
  measured hub RT; **in the armed mechanism it is the model's OWN
  demand-weighted P1 settled price — no measured price ever enters the
  armed path** (rule 13).
- Trailing state: `P_trail(d)` = normalized exponentially-weighted mean of
  `S` over the trailing **120** days strictly before *d* (uses `S(d−1)` and
  earlier only), half-life **λh** (days, identified). State resets to 0 on
  Jan 1 of each solve-year (no cross-year carry — pinned limitation: keeps
  each year's mechanism self-contained; 2024/2025's own quiet paths keep the
  state ≈ 0 regardless).
- Regime-uncertainty prior: `P_prior(d) = P0 · exp(−(d − d_ECRS)/τ0)` for
  d ≥ d_ECRS else 0, where `d_ECRS` = **2023-06-10** (ECRS go-live, the
  published instrument already carried by the keeper; the prior exists only
  in the year containing a go-live date — it is date-gated structure, not a
  year key; ercot-217 stays closed). `P0`, `τ0` identified.
- Expectation: `P_hat(d) = clip(β · P_trail(d) + P_prior(d), 0, 1)`, `β`
  identified.
- Offer: in **P1 only**, through the EXISTING ercot-219 stage-3 seam
  (`run_energy_solve(p1_storage_discharge_cost=…)`), each ERCOT storage
  unit's discharge cost is floored at `max(vom, P_hat(d) × ordc_voll)`
  **in hours h17–20 CST of each day only** (the evening net-peak window —
  identical to the identification window, §2; outside it the offer is the
  keeper's unchanged). The window scoping is the measured lesson of
  ercot-219's G-BAT-2024 collapse (ratio 0.41 under a whole-day floor):
  ordinary-hour cycling is untouched by construction.
- Orchestration: **two-pass P1** — P1a solves with keeper offers, the model's
  own daily path yields `S_m(d)` → `P_hat_m(d)` → P1b (THE scored pass)
  applies the floor. P0 untouched; exactly ONE adaptation pass (no
  fixed-point iteration — rule 10 spirit, pinned). Non-ERCOT ISOs and
  gate-off: byte-identical (seam proof required).

Free parameters: **λh, β, P0, τ0** — four, identified from measured 2023
conduct (the same admissibility class as the CAMPD-measured
`min_load_frac`s and the ercot-168/192 year-scoped measured curves), plus
the conventions ($1,000 event threshold; 120-day window; h17–20 CST;
per-year reset), disclosed here as conventions.

## 2. THE IDENTIFICATION INSTRUMENT (pinned)

Response: for each 2023 delivery day, the **MW-weighted p50 of STORAGE
(PWRSTR) above-LSL, HASL-capped SCED2 offer segments in hours h17–20 CST**
— the ERCOT-154/161 population discipline verbatim (telemetered-ONLINE,
ONTEST excluded, absolute $/MWh), constructed with the committed
ercot-210/218 corpus machinery unchanged, on the on-disk committed
delivery-2023 corpus (`data/raw/ercot/SCED/`, pubs 2023-03 → 2024-03).
`implied_P(d)` = response ÷ `ordc_voll`. A day is admissible with ≥ **40**
segment rows in the window (the ercot-154 cell convention).

Fit: least squares of `implied_P(d)` on `P_hat(d; λh, β, P0, τ0)` over
admissible days **2023-06-10 → 2023-12-31** (the post-go-live regime the
mechanism is for), grid + local refinement; the fitted constants are the
Phase-1 registered values.

Driver series for identification: measured hub RT daily maxima (committed
`actual_lmp_hourly_ERCOT.parquet`) — prices as *identification evidence
about conduct*, exactly the ercot-210/211/218 instrument class; the armed
path never reads them.

## 3. PHASE-0 GATES (all must PASS to enter Phase-1; any FAIL stops the lane, recorded)

| gate | rule |
|---|---|
| **G-COV** | ≥ 300 admissible 2023 days; instrument fidelity — the same population machinery reproduces the committed ercot-210 monthly tightness-cut storage p50s within ±10 % where both exist |
| **G-ID** | daily corr(`implied_P`, `P_hat`) ≥ 0.6 over the fit span, AND monthly p50 reconstruction within ±35 % in ≥ 4 of the ≥ 6 admissible months Jun–Dec |
| **G-DECAY** | (the dynamic signature, decisive) fit on Jun 10–Sep 30 ONLY → predict Oct/Nov/Dec monthly p50s each within ±50 %; AND the β=0 ablation (prior only) must FAIL G-ID's correlation leg — the trailing term must be doing identified work |
| **G-SAFE** | (self-extinction falsifier) `P_hat` computed on the KEEPER's own committed 2024 and 2025 model price paths yields floors ≤ vom+$100 in ≥ 95 % of hours each year — the mechanism is a predicted no-op in the years the keeper already passes |
| **G-BOOT** | (bootstrap feasibility) `P_hat` on the keeper's own committed 2023 model path yields an Aug 1–Sep 30 mean in-window floor ≥ **$750** (it must exceed the caught-hour dw $659 to be able to move it) |

## 4. PHASE-1 A/B KILL GATES (inherited card-§4 table, direction-blind; control = the ercot-215 keeper recipe replayed)

| gate | rule |
|---|---|
| G-CAP | 0 protocol-cap violations (λ + adders ≤ VOLL) in all 26,280 h |
| G-SPUR | spurious mid-band hours vs 9/11/1, bar ≤ +5/yr |
| G-SHED | no new load-shed hours vs 0/1/0 |
| G-OWNER | C3a-2024 PASS, C3a-2025 PASS, C3b-2024 ≤ 0.20 all retained |
| G-BAT | storage net discharge at actual-tail hours within ±25 % of EIA-930 BAT (2024/2025) |
| G-DOF | ledger delta = the four §1 constants with their measured-conduct identification cited; `n_residual` not increased |
| G-D2 | mechanism attribution row present with its declared window (h17–20, P_hat-active days); no new D-4 off-window rows |
| G-REPRO | control replays the keeper's committed determination (and sidecar hashes) before the arm is read |
| LOYO | the constants are 2023-conduct-measured (ercot-168/192 year-scoped-measured precedent); leave-2023-out is structurally impossible for a 2023-identified behavioral constant — **G-SAFE is the declared cross-year falsifier in its place**, stated ex ante |

2023 price numbers (C3a/C3b/C3c) are **side-effect reporting at full
magnitude under Q-B FINAL / R-A — never a gate**: the table above contains
no 2023 price criterion by design, and the verdict rule is mechanical —
any gate FAIL ⇒ REJECTED-AS-ARMED, recorded unrewritten; promotion on any
recorded verdict is the owner's separate act.

**Ex-ante expectation bound, recorded for honesty:** the depth-only ceiling
is probe C3a-2023 −37.8 → −13.4 % (RESEARCH-ercot220b §1, perfect
execution); a single adaptation pass on the model's own path (G-BOOT level
~$750–1,500 vs reality's $2,000–5,000) should land materially short of the
ceiling. The 117 missed hours are out of scope by construction.

## 5. BUILD FENCES

Rule 27 (edit locally, blob-verify ≥300-line pushed files); rule 25
(ERCOT-gated; cross-ISO byte-identity seam proof with the flag ARMED);
rules 5/23/24 (all four constants + conventions as registered
`ScenarioConfig` fields with citations, cache-key registration, no
env-var/off-registry channel); rule 28(c) (the new family row
`ercot_storage_adaptive_expectation` in `mechanism-matrix.js` + a cell line
in EVERY ISO shard, in the build commit); rule 15/16 (both A/B members
registered with payloads, all three years in one bundle per member, same
session); rule 22 ({2023, 2024, 2025} only); rule 12 (years sequential
within each invocation); no new workflows, no cron, no PR. DO-NOT-REDO
honoured: no measured offer surface is fed to any solve
(`ercot_storage_rt_offer_surface` stays R — the armed path consumes only
model-path quantities and four frozen constants); Door A's static
conduct-function closures untouched (this is the dynamic family their
post-mortems pointed at); the ercot-219 aggregate reconciliation stays R;
item 11 / mid-band / regime lanes stay closed.

---

## AMENDMENT 1 (pushed BEFORE any v2 fit; the v1 verdict stands recorded)

**Family v1 as pre-registered was fitted once and FAILED its gates — recorded
unrewritten** (`results/calibration/ercot221_adaptive_phase0.json`, v1
section): G-ID daily corr 0.44 vs 0.6 (1/7 months in band); G-DECAY
over-predicts the fall tail; G-SAFE read 0.67 on 2024; G-COV's fidelity leg
mis-specified. G-BOOT PASSED ($1,319 Aug–Sep mean floor from the keeper's own
2023 path vs the $750 bar). Diagnosis, from the measured response itself:

1. **The prior term is mis-specified and does no identified work.** The
   Jun/Jul cap-parking lives in the tightness-conditioned surface (offers at
   the year's tightest hours), NOT in the unconditional evening window the
   windowed mechanism actually floors (measured evening p50s: Jun $175, Jul
   $761 — cheap at typical evenings, cap only when tight). The pre-registered
   ablation leg measured the prior's own correlation at 0.006. The evening
   response is a pure experience-follower: $175 → $761 → $4,700 → $5,000 →
   $1,852 → $300 across Jun–Dec against spike-day counts 1/2/16/4/0/0/0.
2. **v1's fitted half-life (45–90 d) was the prior term's artifact** — with
   the prior absorbing the summer level, SSE pushed the trail term long.
3. **G-SAFE was computed on an UNWINDOWED daily floor** the mechanism never
   applies (§1 pins the floor to h17–20 only).
4. **G-COV's ±10 % fidelity leg compared non-identical populations**: the
   committed ercot-210 monthly values are per-month admissible-fold subsets
   (n = 2/6/9/4/1 hours) not reconstructable from the JSON alone; the
   saturated/flat months reproduce exactly (Jun −0.02 %, Jul 0.00 %, Dec
   −0.00 %), which is the byte-fidelity evidence.

**Family v2 (STRICTLY FEWER DOF — a term is removed, nothing added):**
`P_hat(d) = clip(β · P_trail(d; λh), 0, 1)` — two identified constants
(λh, β), grid λh ∈ {5, 7, 10, 15, 20, 30, 45} d, β ≥ 0 by OLS. The prior
term is RETIRED (its phenomenon is out of the windowed mechanism's scope and
its ablation showed zero identified work). For gate comparisons only, the
prediction is `max(β · P_trail × VOLL, base)` where `base` = the median
daily evening p50 over the PRE-go-live window Jan 1–Jun 9 2023 (a measured
standing-ask constant identified on a window disjoint from the fit span —
the fleet's ordinary evening ask, which in the LP is carried by the
keeper's own storage offer, so `base` never enters the armed floor). The
ARMED mechanism is unchanged from §1 except the prior term is zero.

**Gate re-statements (bars unchanged):** G-ID and G-DECAY identical bars on
the v2 prediction. G-SAFE unchanged bar (≥ 95 % of all 8,760 hours ≤
vom+$100) computed on the mechanism's ACTUAL windowed floor schedule
(h17–20 carry the floor; all other hours are vom by construction). G-COV
fidelity leg: the saturated/flat months (Jun/Jul/Dec) within ±1 %
(measured: pass), with the Aug/Sep population mismatch disclosed. G-BOOT
unchanged (already PASS at v1; re-scored at v2 constants).

Verdict rule unchanged: ALL v2 gates must pass to enter Phase-1; a v2 fail
closes the lane with both fits recorded.
