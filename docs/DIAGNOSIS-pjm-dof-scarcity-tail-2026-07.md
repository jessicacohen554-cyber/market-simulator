# DIAGNOSIS — PJM at the pjm-105 keeper: what the six fitted DOF stand in for, and what actually owns the C3c scarcity tail

**Date:** 2026-07-14. **Session:** Fable diagnosis + run-config design (no solve —
the solve is a gated follow-on after owner approval of the companion spec,
`docs/handoffs/pjm-107-measured-tail-config-spec-2026-07.md`).
**Keeper:** `2026-07-13-pjm-105-symmetric-net` (owner-promoted 2026-07-14;
PR #2212 rebased, conflict-resolved and merged to main this session —
`keepers.json` PJM pointer live, `audit_keepers.py --check` PASS).
**State:** every gated criterion PASSES except **C3c** (2025 model 17 h vs DA
actual 51 h > $200); C3a is PASS with a flagged low-side trough drift (DA-diag
2024 −5.3 %, 2025 −11.4 %). Attestation DOF ledger: 14 entries, **6
residual-identified** (`results/calibration/pjm105_symmetric_net/calibration_attestation.json`).

This note does two things, per rule 24 (a residual closable only by a tuned
value is an open root-cause issue, not a parameter):

- **Part A** — for each residual-identified DOF, name the real market/physical
  structure the knob stands in for and the measured/published mechanism that
  retires it to neutral, with build status.
- **Part B** — root-cause the C3c tail miss (and the C3a trough drift) on new
  no-LP evidence, close the post-solve-vs-in-LP architecture question, and
  bound what is legitimately reachable vs what is a disclosed representation
  boundary.

---

## Part A — the six residual-identified DOF: structure owed, retirement path

| # | DOF (scalars) | real structure it stands in for | measured/published retirement | status |
|---|---|---|---|---|
| 1 | `offer_curve_by_group` (60) | the submitted-offer surface above SRMC: start/no-load recovery, risk premia, commitment economics that PJM units express in their DataMiner2 energy offers | progressive measured ownership of the offer stack, segment by segment (see below) | CT_FAST done (pjm-103); LONG_RUN done (pjm-104); **CC_LIKE ready — flag-only** (spec leg B); remnant R6-keep pending D-6 holdout |
| 2 | `offer_curve_committed_below_floor[PJM]` (5) | coal take-or-pay / self-schedule **avoidable-cost** economics (fuel partially sunk under contract) expressed as sub-physical fitted multipliers (0.512–0.684 vs the §2 0.85 floor) | issue #1302 evening-merit-style diagnosis first; candidate measured basis: EIA-923 Schedule-5 spot-vs-contract tonnage split (on disk, per #1347) feeding the built-but-off `coal_takeorpay_from_data` / `coal_bit_committed_takeorpay` structure | **needs its own FINDING** — not in this cycle; no blanket change |
| 3 | `offer_curve_smoothing` (3) | within-unit offer dispersion (the rising within-plant share ladder real units submit) approximated by a synthetic ramp | the measured within-unit share ladders in `pjm_offer_midcurve_condbinned.json` measure exactly this shape; replace synthetic smoothing with the measured ladder once floor-form coverage is complete (level-form ownership) | longer-term; document-and-keep |
| 4 | `COAL_SIGMOID_DEFAULTS[PJM]` (12) | the coal fleet's contract/spot cost-exposure mix vs the gas regime (how much of delivered coal cost is passed through to offers as gas moves) | re-derive from the measured 36-month offer corpus: implied flat-in-gas passthrough anchors ≈ 0.74/0.66/0.79 (midmerit finding §3) — a **source-data-triggered** re-derive (rule 23): the corpus intake (2026-07-12) supersedes #1347's "no admissible source exists" premise. Lowers coal offers ⇒ must land **with** the CC_LIKE evening-margin structure (§6 item 2) | chartered follow-on (needs a derive script; sequence after spec legs A+B) |
| 5 | `wefor_multiplier` = 0.7 | statistical **thermal** forced-outage-rate miscalibration: the class-table WEFOR + age escalation overstates availability loss, most in shoulder months (note: audit C-15's "wind EFOR" label is a misnomer — `scenarios.py:3039` scales every *thermal* class's WEFOR) | CAMPD-derived per-class short-outage statistics from the same CEMS record the overlay uses (measured frequency × duration, pooled 2023–2025, frozen, forward-regenerating) replacing the global 0.7 haircut | chartered follow-on (derive script + A/B) |
| 6 | `wefor_residual` = 0.015 | the <5-day forced-outage residual **below the historic-overlay detector floor** for overlay-covered classes (the rationale is documented and physical; the *value* is residual-picked from "~1–2 %") | same CAMPD short-outage derive as #5 — the residual cap becomes a measured per-class statistic instead of one hand value | chartered with #5 |

**The do-not-touch list** (measured/cited ledger entries, confirmed):
`reliability_floor` coefficients, `PJM_SEAM_LADDER_BY_YEAR`, the hourly
interface-TTC overlay, `cc_mustrun_per_plant` inputs, `CT_STARTUP_PARAMS`,
the CAMPD CT run lengths/bands, the LONG_RUN mid-curve floor, and the
symmetric-net DA-virtual curves.

### A.1 The offer-curve retirement mechanism (DOF #1/#3) — how "retire" actually works

The G-22 line established the pattern: each measured mechanism takes *ownership*
of a stack segment, after which the fitted multipliers on that segment are
either dominated (floor form) or replaceable (level form):

- **CT_FAST** (fast-start CTs): owned since pjm-103 by NREL/SR-5500-55433
  start/no-load cost amortized over CAMPD-measured run horizons. The measured
  basis is fuel-price-invariant — an HR multiplier *cannot* express it, which
  is why the CT bands were fitted for ~76 solves.
- **LONG_RUN** (coal/gas-steam): owned since pjm-104 by the measured mid-curve
  floor (econ + peak rows).
- **CC_LIKE** (CC_REGULAR econ rows): the one remaining unmeasured mid-merit
  top (`econ_high` 1.5 / the s85–s99 belt). The measured surface already
  carries the segment with the extended share grid
  (`shares = [0.05…0.95, 0.97, 0.99]`; 2025 top-net-load-bin ladder reaches
  17.7× the delivered gas-day at s0.99). Arming it is a **pure flag change**
  (`pjm_offer_midcurve_segments=("LONG_RUN","CC_LIKE")` — scoping already in
  `fleet.py:3243–3253`; CC *peak* rungs stay fitted-curve-owned since the
  pjm-99 top surface is retired). This is midmerit §6 item 5, explicitly
  unblocked by the clamp removal.
- **After CC_LIKE lands**: run the *dominance ablation* — measure, per fitted
  band, the share of row-hours where the measured floor exceeds the fitted
  level. A dominated band is retirable to neutral (1.0) with a byte-delta
  check; an undominated band stays R6-keep with its residual-identification
  honestly ledgered until the D-6 one-shot holdout program scores it.

A floor can only *raise* bids, so floor-form ownership alone never retires a
band that sits *above* the measured level — that is what the level-form step
(#3, the measured ladder replacing the synthetic smoothing + band construction)
is for. That is deliberately sequenced last: it is a bid-construction rewrite,
not a flag.

---

## Part B — C3c (and the C3a trough drift): root cause and the honest reach

### B.1 What the gate requires (scorer arithmetic)

`calibration_verdict.py` (rubric v2.5): model DA-expressible tail count within
**[0.5×, 2×]** of the DA actual; small counts (<10) score |Δ| ≤ 10
(`TAIL_LO/TAIL_HI/TAIL_SMALL_COUNT`, lines 246–247). PJM DA actuals
(`tail/actual_tail.json`): 2023 = 8 h, 2024 = 2 h, 2025 = 51 h. pjm-105 model:
**1 / 1 / 17 h**. So:

- **2025 must reach 26–102 h** (currently 17 — the sole FAIL);
- 2023 may rise to ≤ 18 h, 2024 to ≤ 12 h before those years break — the
  levers below have that headroom to respect.

### B.2 New no-LP evidence (computed this session, measured data only)

**(a) The real 2025 tail is genuinely reserve-coupled — but at the
opportunity-cost level, not the penalty level.** Crossing
`da_reserve_market_results_2025.parquet` (RTO locale) with the DA LMP actuals:
of the 51 hours with DA LMP > $200, **38 had a DA reserve MCP > $50**
(18 > $100; SR MCP median in the tail ≈ $64, mean ≈ $105, max $370). The
$850/$300 penalty steps were touched in only ~7 h. So the observed tail is
**an expensive energy stack ($130–300 marginal offers) plus a $50–105
reserve opportunity-cost component**, occasionally more — not a penalty-step
event. (2023: 4 of 8 tail hours had reserve MCP > $50; 2024: 1 of 2.)

**(b) The 2025 tail is majority a winter fuel event.** By month:
**January 28 h** (the cold snap; morning 04–09 + evening peaks), February 1,
June 13, July 9. The C3c miss is ~55 % a *winter* phenomenon — which no
afternoon-reserve mechanism addresses.

**(c) The posted reserve requirement carries no cold-snap extension.** In the
Jan-2025 tail hours the measured `pr_req_mw` sits at 3,681–3,710 MW vs the
3,678 MW base — flat. The Manual-11 heavy-load extension binds *above* the
posted series (the ordc-doc validation already showed penalty-priced intervals
at apparent surplus), so requirement-side realism cannot be improved from the
posted data, and the owner has closed the reserve-supply lane regardless
(B.3).

### B.3 The lever ledger — every scarcity lane already adjudicated

| lane | probe/record | result | disposition |
|---|---|---|---|
| Post-solve two-step ORDC overlay (architecture **A**) | `derive_pjm_ordc_overlay.py`, pjm_26/27 honesty gate | vertical step fires 8/20/5 h on plant-online reserve; closes ~none of the residual; where it fires it *overshoots* ($850-class adders vs the $75–200 band); cannot produce the sub-shortage $50–105 component | retired to diagnostic; **inadmissible in the keeper line** — would stack on the live in-LP co-opt (rule 19) and is gated `NOT energy_reserve_coopt` in code |
| Zone-aggregate co-opt scoping | pjm-62 | reserve price $0 in all 26,280 h (deliverable cap ~50 GW ≫ 3.4 GW req) | empirically refuted |
| Per-gen (class-tier) co-opt, measured ramp (architecture **B**) | pjm-81 | **live in the keeper** (`energy_reserve_coopt` + `pjm_reserve_pergen` + `pjm_reserve_supply_cap` + `measured_ramp_capability`); fires exactly 1 h / 3 yr ($46.47, 2025-06-23 h19) | **kept — the sole reserve-price owner** (rule 19) |
| SYNC product / size split | pjm-87 / pjm-88 | duals in the correct regime but $0–10 vs the $75–200 need | **owner-CLOSED 2026-07-11** ("do not re-open reserve-supply probes for PJM C3c") |
| Commitment posture (Phase 1) | pjm-82, pre-committed gate | G-P1 FAIL all years: model online headroom 2.66–3.14× the measured online target (SR+REG ≈ 3.0–3.3 GW); tail unchanged (0 h) | REJECTED; root cause is **LP-vs-MIP**: a continuous `U` holds fractional online capacity at near-zero cost — a representation boundary under the no-MIP mandate, not a tuning gap |
| DA demand depth + measured offer levels (the "demand-side/commitment tightness" route the owner named) | G-22: pjm-100→105 | **in the keeper**; moved 2025 C3c 0 → 17 h and fixed C1/C3a/C3b/C7 | done |

**Architecture adjudication (the state question): keep B, add nothing.** The
in-LP co-opt is already the keeper's structure and the most faithful form the
box solves (miso-39-tier pooling, ~15.0 GB P1 peak with swap). A post-solve
adder on top would double-own the reserve-price phenomenon (rule 19), and the
honesty gate already showed it prices the wrong regime. **No new
scarcity-price mechanism is proposed.** Neither remaining lever below is a
scarcity-price mechanism, so no new D-2 id is needed (both force zero energy;
the D-2 registry covers min-gen floors only). The ownership table for
> $200-hour price formation is:

| phenomenon | owner (sole) | status |
|---|---|---|
| reserve price (all regimes) | `_pjm_design` in-LP co-opt (Primary RTO+MAD, published two-step ORDC, measured req/ramp) | live; opportunity-cost magnitude LP-bounded (below) |
| DA financial demand depth | `pjm_da_virtual_bids` symmetric net | live |
| LONG_RUN (coal/steam) econ+peak offer level | `pjm_offer_midcurve_conditional` (LONG_RUN) | live |
| CC econ offer level (s05–s99 belt) | same mechanism, `CC_LIKE` segment | **proposed leg B** (currently: fitted `econ_high`/smoothing) |
| CC/CT peak rungs | fitted curve (pjm-99 top surface stays retired) | R6-keep |
| within-month gas commodity swing (SRMC basis) | `gas_daily_shape` (measured HH daily, mean-preserving) | **proposed leg A** (currently: flat plant-month) |
| fast-start CT offer level | tranche startup amortization (NREL × CAMPD horizons) | live |

### B.4 The root cause of the missing 34 hours, named

Two structural gaps — both **input/offer fidelity on the energy stack**, not
missing scarcity machinery:

1. **Winter (the Jan-2025 28 h): the model prices January on a flat monthly
   gas level.** The keeper runs `gas_monthly_actuals` + F923 plant-months;
   `gas_daily_shape=False` means the merit order never sees the measured
   intra-month cold-snap commodity spike (HH daily peaked ~2.4× its January
   monthly mean in the 2025 event; East-hub delivered spikes were larger
   still). A CT/CC stack priced on the monthly mean *cannot* print $250 on
   Jan 21 — the input, not the market model, caps the tail. The mechanism to
   fix it exists, is measured, is mean-preserving (monthly level byte-kept,
   `fuel.py:3803–3817` re-carries the shape onto every overwritten gas
   plant-month), was adopted for exactly this phenomenon elsewhere (miso-50
   coal-vs-gas flip days; the NEISO daily-basis keeper line made the winter
   oil/LMP tail appear endogenously), and **has never been probed on PJM**.
2. **Summer (the Jun/Jul 22 h): the CC top belt is the one mid-merit top
   still on a fitted basis.** The measured CC_LIKE s0.95–s0.99 belt runs
   11.1–17.7× the delivered gas-day in the top net-load bin (2025 table) —
   on event-day gas that is $150–260 of measured offer the model's fitted
   `econ_high=1.5` never expresses. Note the mid-curve floor's target is
   `mult × gas_day(t)` where `gas_day` is *already* the HH-daily + PJM basis
   series (`fleet.py:3231–3236`) — so leg B also contributes winter tail
   formation on measured submitted offers, independent of leg A.

What the two legs **cannot** reach is the $50–105 reserve opportunity-cost
component in ~38 of the 51 real tail hours: that is priced by reserve
competing with energy on a *tight* online margin, and pjm-81/82 proved the
perfect-foresight LP holds ~2.7–3.1× the real online reserve at near-zero
cost. Under the no-MIP mandate this is a **disclosed representation
boundary** (pjm-82 §"Named failure modes"), not an open lever. The
pre-registered honest expectation is therefore: legs A+B move 2025 toward the
26-hour gate **through the energy stack alone**; if the count lands short,
C3c stays a disclosed boundary and **no adder is tuned to the residual**
(rules 1/11/13). Both legs are independently justified as input/structure
fidelity (rule 14) — they go in, or not, on their own gates, whatever C3c
does (rule 1).

### B.5 The C3a trough drift shares the same roots

C3a DA-diag reads 2023 +0.8 %, 2024 −5.3 %, 2025 −11.4 % (in-band, flagged).
The 2025 gap (≈ −$5/MWh) is far larger than the 51 tail hours can carry
(~$0.9/MWh-year at their excess); it lives in the broad $100–200 band — the
DA actual printed **299 h > $100 in 2025** (100 in 2024) — i.e. the same
under-priced event-day mid/top stack the two legs target. Pre-registered
expectation: A+B lift the 2024/2025 DA-diag means toward zero with the 2023
near-exact mean preserved (leg A is mean-preserving in fuel *price*; leg B is
floor-form on ≲ 15 % of CC capacity-shares). If material trough drift
persists after A+B, the next named candidate is the coal committed
take-or-pay repricing (DOF #2, issue #1302) — the committed coal bands at
0.51–0.68 are the cheapest always-on supply in the trough and their
structural replacement plausibly lifts trough duals; that is a reason to run
the #1302 diagnosis, **not** to tune the multipliers.

### B.6 Guardrails this diagnosis respects (and the one it verifies)

- **Rule 1 (ercot27 lesson) applied as a *driver-window* gate:** any new
  model tail hour must be driver-justified — leg A's additions must lie on
  days whose measured HH daily factor is elevated (the mechanism's own
  driver), leg B's in the surface's own top net-load bin conditioning. Broad
  mid-range price elevation with no event-day structure is a failure of the
  probe, whatever it does to C3c (exact gates pre-committed in the spec).
- **Rules 13/20/21:** both legs are measured, ex-ante, zero-scalar inputs
  (HH daily prints; submitted offer curves), frozen against residuals.
  N_RUNGS/share-grid/bin-edge choices are resolution, not tunables.
- **Rule 22 LOYO:** neither leg carries a free parameter, so a formal
  leave-one-year-out refit is vacuous (pjm-105 precedent); the per-year
  honest-movement table across all criteria is the promotion evidence, and
  the 2023/2024 tail headroom bounds (≤18/≤12 h) are explicit no-regression
  gates.
- **Rule 19:** legs A and B move the energy offer/cost surface; the reserve
  price stays solely co-opt-owned; the post-solve overlay stays retired.

---

## Part C — OUTCOME (2026-07-14 execution session): the winter hypothesis was inverted

The cycle solved on a **corrected** `gas_daily_shape_factors` (the G-A1
pre-check found the shared factor builder was NOT mean-preserving — bare
`np.interp` calendar-day resampling overshot the monthly mean in spike months,
worst Jan-2024 +$0.10/MMBtu; owner-authorized fix `9037c89` renormalizes the
factors to mean exactly 1.0). On the corrected mechanism the §B.4/§B.5
expectations did **not** hold — they were predicated on the flawed,
mean-inflating behaviour:

| pre-registered expectation (§B.4/§B.5) | outcome |
|---|---|
| Leg A moves 2025 tail 17 → ≥26 h via the Jan cold-snap | **2025 tail 17 → 6 h** — leg A REMOVES tail (all 6 remaining hours are Jun/Jul summer-load) |
| Leg A additions concentrated Jan, on ≥p90 HH-daily-factor days | no additions; the tail SHRANK. 1/6 remaining hours on a ≥p90 gas-day → not a gas-driver tail |
| Leg B lifts summer tail via the measured CC belt | **2025 tail → 6 h** (no lift) and **C1 −8.52 TWh** (CC displaced) → REJECT |
| A+B lift 2024/2025 C3a toward zero, 2023 preserved | leg A C3a-2025 −11.4 % → −10.0 % (slightly better), 2023 held; leg B −9.1 % but C1-broken |

**Root cause, revised.** The model's baseline (pjm-105) winter tail was
substantially a **flat-monthly-gas over-pricing artifact**: pricing every
January day at the elevated *monthly-mean* gas level pushed a spread of typical
winter hours over $200. The correct mean-preserving daily shape concentrates
the gas cost onto the few real cold-snap days and drops the rest below $200 —
so the honest model tail is 6 h, not 17. This **confirms §B.4's core claim**
that the residual 34+ h is a reserve opportunity-cost / LP-vs-MIP
representation boundary (pjm-81/82), NOT an energy-stack input-fidelity gap —
and it *strengthens* it: the energy-stack legs move the tail the *wrong* way,
so no offer/gas-side mechanism reaches the actual 51 h. No adder was tuned
(rules 1/11/13); the reserve-supply lane stays owner-closed.

**Leg dispositions (2026-07-14):** leg A (pjm-107) passes all
structure/no-regression gates and is more structurally faithful than the
flat-monthly keeper (rule 1/11) — the pjm-109 candidate, keeper recommendation
flagged to the owner (adopting it drops the headline tail 17→6, a
correctness-vs-headline tradeoff that is the owner's call). Leg B (pjm-108) is a
registered reject (C1). See the 2026-07-14 calibration-log entry.

## Pointers

- Companion spec (the deliverable this note grounds):
  `docs/handoffs/pjm-107-measured-tail-config-spec-2026-07.md`
- Keeper record: `docs/FINDING-pjm-midmerit-level-2026-07.md` §7;
  attestation/DOF ledger in `results/calibration/pjm105_symmetric_net/`
- Scarcity lane history: `docs/multi-iso/pjm-reserve-ordc.md` (phases,
  memtests, pjm-62/81 empirics);
  `docs/handoffs/pjm-commitment-posture-port-2026-07.md` (pjm-82 gate);
  calibration-log 2026-07-11 "PJM G-20b hold CONFIRMED" (owner closure)
- Measured curve provenance: `docs/multi-iso/pjm-reserve-curve-source.md`
- Open issues: #1302 (committed-below-floor), #1347 (sigmoid identification —
  premise now superseded by the offer-corpus intake, see Part A #4)
