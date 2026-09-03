# FINDING miso-202 — the adjacent-window BOUNDARY-DAY DOUBLE-COUNT is real, wider than miso-201 could see, and the C3a-2025 charter's object is measured to be a TAIL miss the outage family cannot reach (2026-09-03)

**Session:** miso-202 (2026-09-03). **Keeper at open:** `2026-09-02-miso-201-stbasis`
(bundle `results/calibration/miso201_stbasis_B`), determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested (ledger 40/2).

**KEEPER AT CLOSE:** _pending the A/B._

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

_pending._

## 6. Reported against the outcome, at full magnitude

_pending._

## 7. Handed on

_pending._

## 8. Governance

_pending._
