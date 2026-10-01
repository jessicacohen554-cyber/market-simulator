# FINDING miso-202 — the adjacent-window BOUNDARY-DAY DOUBLE-COUNT is real, wider than miso-201 could see, and the C3a-2025 charter's object is measured to be a TAIL miss the outage family cannot reach (2026-09-03)

**Session:** miso-202 (2026-09-03). **Keeper at open:** `2026-09-02-miso-201-stbasis`
(bundle `results/calibration/miso201_stbasis_B`), determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested (ledger 40/2).

**KEEPER AT CLOSE: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`), promoted with **all ten A/B gates passing**.
`audit_keepers --iso MISO` **PASS 0/0**.

**Charter:** queue item 1 — FINDING-miso201 §7 item 1's named successor, the adjacent-window
boundary-day double-count, *"with the numerator aligned the ONLY mechanism still producing
steam overflow"*. Plus the lane's standing re-charter, C3a-2025 summer scarcity (miso-167).

---

## 1. The two results, in one paragraph each

**THE LEVER.** The defect is real, it is a defect rather than a judgement call, and it is
**wider than the instrument that found it could see**. `unit_outage_event_window`
reconstructs a day-granular extract row as `[outage_start, outage_end + 1 day)`, so two
windows of the same unit sharing a boundary date both cover that day while
`_unit_outage_factors_from_events` **sums** row shares rather than unioning them — the
unit's capacity is subtracted twice on a day it can be at most 100 % out. What settles the
diagnosis is the census's shape, not its size: across MISO's committed extracts **every one
of the 845 same-unit window overlaps is exactly 24.0 hours**, a single-bin histogram, which
is the fingerprint of the `+ 1 day` artifact and of nothing else. miso-201 met the object
only where it *overflowed* a steam bin and sized it from that steam-scoped view at
"24–72 h/yr per bin"; measured class-agnostically it is 845 pairs across 63 bins reaching
**CC_REGULAR, ST_GAS, COAL, CC_CHP and ST_CHP**, restoring **91.1 / 77.6 / 103.4 GWh** of
capability. And an overflowing cell is precisely the case where it is *inert* — the correct
answer there is 0.0 and the clip already delivers it — which is why a census scoped to
overflow could not see the live part.

**THE CHARTER.** The lane has spent three sessions (miso-199, -200, -201) in the
unit-outage overlay family while C3a-2025 drifted from −12.2745 to −12.3845, because every
repair in that family restores availability and so moves the residual the wrong way. This
session measured **where the −12.38 % actually is**, from committed artifacts and with no
solve, and the answer changes what the next lever should be: **C3a-2025 is not a level miss
at all — it is entirely a missing scarcity tail, and it is the same object as C3c rather
than an independent one.**

## 2. THE ANATOMY OF C3a-2025 (`_miso202_c3a_2025_anatomy.json`)

Instrument validated first: the load-weighted annual mean recomputed from the keeper's own
committed `hourly/system_<year>.parquet` reproduces `calibration_verdict`'s C3a face in all
three years (**+0.1267 / −4.5967 / −12.3849** against **+0.1218 / −4.5820 / −12.3845**).

**A-1, the miss is a June–July miss.** Of 2025's −5.625 $/MWh load-weighted gap, Jun–Sep
carries **77.7 %** and **June + July alone carry 59.0 %**:

| month | model | actual | gap | contribution | share of gap |
|---|---:|---:|---:|---:|---:|
| **Jun** | 40.03 | **57.39** | **−17.36** | −1.546 | **27.5 %** |
| **Jul** | 41.96 | **59.45** | **−17.49** | −1.774 | **31.5 %** |
| Sep | 37.52 | 46.37 | −8.85 | −0.733 | 13.0 % |
| Jan | 44.37 | 51.52 | −7.15 | −0.653 | 11.6 % |
| Aug | 37.06 | 40.44 | −3.38 | −0.319 | 5.7 % |
| May | 38.47 | 33.93 | **+4.54** | +0.346 | −6.2 % |

Feb–Apr sit within 0.5–1.8 $/MWh and May is **over**, so there is no level bias to find.

**A-2, and it is entirely a TAIL miss.** Over Jun–Jul 2025, against the committed
hub-average hourly RT series:

| | p50 | p75 | p90 | p95 | p99 | p99.9 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| actual | 32.73 | 42.93 | 61.77 | 91.03 | **238.93** | **746.10** | **1,669.52** |
| model | **37.47** | **44.14** | 48.12 | 52.48 | 69.04 | 148.92 | 165.58 |

**The model's median is HIGHER than actual, and so is its p75.** The gap opens only above
p90. **The top 1 % of actual hours — 15 hours — carry 99.9 % of the entire mean gap**; the
other 1,449 hours contribute −0.00.

**A-3, because the model never enters scarcity.** Its maximum price in **any** zone-hour of
Jun–Jul 2025 is **183.22 $/MWh** against an actual hub maximum of 1,669.52; it produces
**zero** zone-hours above $200 in those months against 20 actual hub-hours; unserved energy
is **0.0 MWh**; and the ORDC registers a shortfall in **3 hours of 8,760** across all four
reserve families. **The ceiling is not in the ORDC curve** — its 14 steps span $65–$3,500.
The system is simply never short.

**A-4, and the model is not missing the EVENT — only its PRICE.** In those same 15 hours,
against the other 1,449 Jun–Jul hours, the keeper dispatches CT_PEAKER **13,120.9 MW
(+8,783.4)**, **import 6,351.3 MW (+3,844.4)**, ST_GAS 5,087.0 MW (+2,826.5), COAL_PRB
+2,174.8, against wind −2,023.9 and solar −2,808.5. It sees the net-load spike and answers
it; it simply has enough supply to serve it at ~$183. (Model-side only, and labelled as
such: no hourly interchange actual is committed for MISO, so this is descriptive, not a
residual against a benchmark.)

**What follows for the lane, stated as a finding and not as a lever.** The measured chain
is: **surplus supply in the binding hours → reserves never short → the ORDC never climbs
its own curve → a ~$183 energy-price ceiling in exactly the months that carry the miss.**
C3a-2025 is therefore not closable by anything that moves the price *level*, and the
outage-overlay vein is exhausted as a route to it — not because those repairs are wrong,
but because they act on the wrong object and in the adverse direction. The **+3.8 GW of
import** in those 15 hours is the same object the **D-2 5(i) seam-response** ruling names
at +2.1 GW of binding-hour import excess, which this measurement independently
corroborates as the lane's strongest next candidate. It remains **NAMED, NOT CHARTERED**,
pending the owner's admissibility decision; this session proposes no mechanism for it.

## 3. What phase 0 measured, before the mechanism existed

`_miso202_boundary_day_phase0.json`, committed **before** the PREREG and before a line of
mechanism code.

* **N-1 REPRODUCTION PASS on 589 bins**, across all three layers that share the accumulator
  (std5d, short, lay-up). Every reconstructed pre-clip share reproduces production's
  `clip(1 − v, 0, 1)` exactly. A reconstruction that does not reproduce production measures
  nothing — the discipline miso-200 applied on 121 bins and miso-201 on 988.
* **N-2 CENSUS: 845 same-unit overlapping pairs** — std5d 648, lay-up 197, short **0** —
  measured on the *reconstructed* windows the accumulator actually sees, under the
  production row filters, not on the raw CSV. **The overlap-length histogram is a single
  bin at exactly 24.0 h.**
* **N-3 COUNTERFACTUAL: +91.1 / +77.6 / +103.4 GWh**, by class: CC_REGULAR 55.9 / 17.3 /
  50.2, ST_GAS 32.0 / 56.3 / 50.6, COAL 0.7 / 1.5 / 2.4, plus small CC_CHP and ST_CHP.
* **N-4 WHERE IT LANDS**, measured before the arm existed so it could not be read back from
  a result: only **1.4 % / 0.0 % / 1.4 %** of the restored capability falls in the keeper's
  own top-1 % price hours. The honest ex-ante expectation was therefore that C3a barely
  moves — and (per §2) that it *could not* have been closed here either way.
* **N-5 THE MAXGEN TWIN: zero overlapping pairs over 544 unit-series.** Its windows are
  already hour-granular, so it cannot carry a boundary-DAY defect. Its exclusion from the
  mechanism is a **measurement**, not an assumption, and a signature assertion in the tests
  fails if a future edit wires the flag in.

## 4. The mechanism

`ScenarioConfig.unit_outage_per_unit_clip` — **GATED, default off, byte-inert off**,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` **in the same commit as the field** (the
nyiso-119 / caiso-186 / miso-201 discipline, so the pinned default key never moves;
`tests/unit/config` 652 passed).

Each unit's removed MW accumulates into its own hourly array and is capped at that unit's
own capacity before the units sum into the bin. **A ceiling on a sum, not a window-merging
heuristic**: no date arithmetic, no adjacency test, no tolerance — so it is the identity
everywhere except the physically impossible case, and it can only ever remove *less*. That
monotonicity is the mechanism's own soundness line and the A/B gates it as **S-3**, a hard
VOID checked on every bin and hour off the production loaders before either leg is solved.

The ceiling is the **largest** capacity a unit's own rows claim, never a smaller one: a
unit re-rated mid-extract must not have a legitimate single window silently clipped. It
clips **per unit, not per bin** — two *different* units out concurrently still zero the
bin, which is correct.

**Scope by measurement.** Shared by the std ≥5-day, short, partial and **lay-up** layers
(rule 19 `[R-ONE-MECH]`: a lay-up share and an outage share for the same plant sit on the
same basis and are additive, and phase-0 measures 197 same-unit overlaps in the lay-up
extract, so the layer is not merely eligible but live). The declared-event **maxgen** layer
is excluded per N-5.

**Verification before the A/B:** the built mechanism reproduces the phase-0 N-3
counterfactual **exactly** (91.133 / 77.570 / 103.414 GWh), and on MISO's real extracts its
availability delta is ≥ 0 at every bin-hour (worst regression 0.00e+00). 24 unit tests on a
**synthetic** fleet and extract, so a change to the committed MISO extract can never
quietly turn one green; `tests/unit/data` 1617 passed.

## 5. The A/B

Control `2026-09-03-miso-202-control` vs arm `2026-09-03-miso-202-unitclip`, both MISO
2023+2024+2025 in one invocation, years sequential, in-session (rules 12/16), both from the
same committed keeper recipe via `--replay-bundle`. Scorer `_miso202_ab_gates.py`
**committed blind with the PREREG before the mechanism existed**.

| gate | result |
|---|---|
| S-0 control integrity | **PASS — BIT-IDENTICAL**, 9 sidecars, `max_abs_diff` 0.0 |
| S-1 single delta | **PASS** — exactly `unit_outage_per_unit_clip` |
| S-2 liveness | **PASS** — std5d 31 bins gain, lay-up 12, **short 0** |
| **S-3 monotonicity** (hard void) | **PASS** — 589 bins, **zero** bin-hours removing more, worst regression 0.000e+00 |
| **K-1 C1 band** | **PASS — no band exit anywhere** |
| K-2 C3b | PASS (Δ 0.000 every year) |
| K-3 D-4 conduct | PASS — zero new off-window binding |
| K-4 D-1 shape | PASS — zero PASS→FAIL |
| K-5 status flips | PASS — status map **identical** |
| K-6 DOF | **PASS, and REAL** — not vacuous |

**Three of these carry more than a checkmark.** S-0 is the end-to-end proof of byte-inertness
while off: a full solve carrying the field reproduces the keeper exactly. **S-2's `short 0`
is a falsifiable phase-0 prediction confirmed against production** — phase 0 censused zero
same-unit overlaps in the short layer, and the arm moved zero of its bins. **S-3** is the
gate this lever earned: a ceiling on a sum can only remove less, so it was checkable on
every bin and hour without sampling, and it held exactly.

**K-1, the pre-registered risk, in full:**

| class-year | keeper | arm | reading |
|---|---:|---:|---|
| CC_REGULAR-2024 | +6.931 | **+6.942** | **THE NAMED RISK — moved adversely as predicted**, +0.011 TWh against 1.069 TWh headroom |
| CC_REGULAR-2023 | −3.434 | **−3.408** | toward actual |
| CC_REGULAR-2025 | −2.194 | **−2.177** | toward actual |
| ST_GAS-2024 | −7.488 | −7.487 | the tightest cell on the board; does not move materially |
| ST_GAS-2023 / -2025 | −3.512 / −6.681 | −3.516 / −6.684 | essentially unmoved |
| COAL_PRB-2025 | −4.904 | −4.907 | named adverse; −0.003 TWh against 3.096 headroom |

**Determination UNCHANGED** at NOT-YET on `price_mean` alone, C3c the single ledgered
caveat, C6 attested (ledger **41 / 2**, `n_residual` unchanged).

## 6. Reported against the promotion, at full magnitude

**(a) THE ARM IS SMALL IN DISPATCH, and that is stated plainly rather than buried.** The
phase-0 capability bound was 91.1 / 77.6 / 103.4 GWh and the LP converted only a fraction:
the largest C1 move is **+0.026 TWh** (CC_REGULAR-2023). **The repair is justified as a
defect repair and its size is not its argument** — a double-counted unit is wrong at any
magnitude, and the mechanism would be right if the LP had converted none of it.

**(b) THE NAMED RISK MOVED ADVERSELY, exactly as pre-registered.** CC_REGULAR-2024
+6.931 → +6.942. Predicted in the PREREG (the model already over-produces CC there and the
arm restores CC availability), bounded ex ante at 0.017 TWh against 1.069 TWh of headroom,
and measured at +0.011 TWh. The gate is reported as it landed, not renegotiated.

**(c) C3a IS ESSENTIALLY UNCHANGED, and is NEVER the justification** (rule 1 `[R-STRUCT]`):
2023 **+0.1218 unchanged**, 2025 **−12.3845 unchanged**, 2024 −4.5820 → −4.6130 (−0.031 pp,
slightly worse). This is what phase-0 N-4 predicted *before the arm existed*, and §2
explains why no repair in this family could have moved it.

**(d) THE PREREG'S NAMED C8 RISK DID NOT MATERIALISE.** ST_GAS forced share
0.1551 / 0.1529 / 0.2713 → 0.1553 / 0.1529 / 0.2714 — deltas of +0.00014 / +0.00002 /
+0.00010, all **below the pre-registered inertness epsilon of 0.0005** and far inside the
0.30 merchant budget.

**(e) K-6 WAS UNSCORED ON THE FIRST SCORING PASS**, because a `--replay-bundle` solve writes
no attestation. Diagnostics (D1=30, D2=23, D4=57 on **both** legs) and attestations were
then generated for both legs and the pair re-scored. The miso-200 vacuous-pass trap stayed
closed **by construction** — the scorer refused to score K-3/K-4/K-6 on empty inputs — rather
than being discovered after the fact.

**(f) MAIN DRIFT MEASURED, NOT ASSUMED.** Both legs solve at `fe641ebe` while `origin/main`
advanced during the session. The only drift touching `src/` or the runners is a blank line
in `new_entry.py` and additive **output-only** capacity-evolution ledger fields in
`runner.py` that no decision reads and that backcast mode never reaches. Both legs remain
one code state.

**(g) A CONTAINER RESTART KILLED THE FIRST SOLVE PAIR MID-FLIGHT.** The partial control
bundle was **deleted rather than reused** — a half-written bundle would have made S-0's
bit-identity check meaningless — and both legs were re-solved from scratch under `setsid`.
Disclosed rather than silently recovered.

## 7. Handed on

1. **THE D-2 5(i) SEAM-RESPONSE OBJECT is now the lane's clear successor, and this session
   adds independent corroboration** (§2 A-4): the model dispatches **+3.8 GW of import** in
   exactly the 15 hours the real market priced ≥ $238.93. It remains **NAMED, NOT
   CHARTERED**, pending the owner's admissibility ruling; no mechanism is proposed here.
2. **THE OUTAGE-OVERLAY FAMILY IS EXHAUSTED AS A C3a ROUTE.** §2 establishes this by
   measurement, not by exhaustion of ideas: C3a-2025 is a pure tail miss and every repair
   in this family restores availability. Remaining objects in the family (the extract/fleet
   unit-set mismatch, the `eia923_netzero` whole-plant lay-up rows, the maxgen basis
   question) are still worth doing **as defect repairs**, and should not be chartered as
   C3a levers.
3. **THE K-3 MINIMUM-BINDING-HOURS QUESTION, raised and not tuned** (miso-201 §7 item 5,
   inherited unresolved). miso-201's single fired kill was a D-4 conduct ratio on a
   **two-hour denominator**. This session's K-3 is silent, so nothing forced the issue —
   but whether D-4 should carry a minimum-binding-hours floor remains a **rubric question
   for the owner**, not a calibration one. Raised, deliberately not fixed by tuning.
4. Unchanged from miso-199/200/201: floor fragmentation; the `D4_WINDOWS` "self-windowing
   by construction" wording (self-**sizing**, not self-**placing**); the lay-up census
   cycler/mothball boundary; `CT_CHP` as the visible half of the steam-host family;
   `ST_CHP`'s CEMS invisibility; the standing wind +5 TWh/yr over EIA-930; the 2023 import
   +2.0 TWh face; the committed extract's provenance drift (`outage_artifact_provenance`,
   cell O); and **the bid-side self-schedule form, still open, still unadjudicated, cell not
   minted**.

## 8. Governance

Attestation by `scripts/gen_miso202_attestation.py` on the gen_miso186/187/188/198/200/201
pattern — one appended MEASURED entry, **n_entries 40 → 41, n_residual UNCHANGED at 2**;
`build_dof_ledger.py` deliberately NOT run on it. Diagnostics **and** attestations were
generated for **both** legs *before* the pair was scored. Keeper shard, `status/MISO.js`,
the matrix shard keeper stamp, the `unit_outage_per_unit_clip` cell (O → K) and the §5.4
prose header all re-stamped this session (rule 28b); the base matrix row plus a cell in all
six shards landed with the field (rule 28c). `audit_keepers --iso MISO` **PASS 0/0**.
Rule 25: only MISO's files were touched — the pre-existing NYISO §5.x prose-header drift
from nyiso-177 was left alone. MISO holds no `complete` marker, so the rule-22 D-5(b) re-key
does not apply. Rule 22: 2023–2025 only.

Next shorthand: **miso-203**.
