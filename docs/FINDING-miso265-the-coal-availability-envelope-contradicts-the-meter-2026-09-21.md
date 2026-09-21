# FINDING — miso-265: MISO's coal availability envelope is INFEASIBLE against its own metered coal, in every year of the span, by 20–32 TWh

```
SESSION : miso-265        ISO: MISO        LP SPENT: ZERO. No shard launched.
KEEPER  : 2026-09-20-miso-264-anchor-vintage (results/calibration/miso264_anchor_span,
          2020-2025) — VERIFIED ON main BEFORE ANY WORK. UNCHANGED by this session.
          Train tier 2023-2025 CALIBRATED, C3c the lone ledgered caveat.
OBJECT  : the 2020 QUANTITY / COMMITMENT object RESULT-miso264 §7/§9(1) routed here.
ANSWER  : it is neither a commitment object nor an offer object. It is an INPUT
          CONTRADICTION. The model's own availability array asserts MISO's coal fleet
          could not have produced what CAMPD metered it producing — 25.4 TWh across
          142,058 plant-hours in 2020, and 20-32 TWh in EVERY year 2020-2025, the
          CALIBRATED train tier included.
CAUSE   : the unit-outage derate sums CONCURRENT unit windows and clips at FULL
          derate, so plants are zeroed outright in hours they demonstrably ran —
          5.318 TWh across 24,100 plant-hours at availability == 0 in 2020 alone.
          NOT the economic-idleness story I first proposed; §3.1 withdraws it.
REPAIRS : FOUR candidates tested at ZERO LP and ALL FOUR REFUTED (§4), including
          both repairs the accumulator's own docstring names for this pathology.
          That retires them before anyone spends 12 shard-years arming them.
```

---

## 0. THE CHARTER WAS FIVE SESSIONS STALE — READ THIS FIRST

`HANDOFF-miso260` opened this lane against keeper `2026-09-16-miso-259-coal-fuel`
and a miss list led by **C1 2021 CC_REGULAR −9.46**, **C1 2022 CC_REGULAR −9.47**,
**C3a 2022 −14.6 %** and **C3b 2020**. Sessions miso-260 … miso-264 have since run
and **every one of those four is now PASSING**. The live keeper is
`2026-09-20-miso-264-anchor-vintage` and the next session number is **miso-265**,
not miso-260.

Scored live on the current keeper, same scorer, committed bench:

| criterion | year | live miss |
|---|---|---|
| **C1** fuel-mix | 2020 | COAL_BIT **−10.92 TWh** (share −1.6 pp) |
| **C1** | 2022 | COAL_PRB **+8.13 TWh** (share +1.7 pp) |
| **C3a** mean LMP | 2020 | **+14.6 %** |
| **C3b** price shape | 2021 | NRMSE **0.304** |
| C3c tail | 2022 | CAVEAT, ledgered, non-downgrading |

C2, C4, C6, C8 PASS. **Train tier 2023-2025 CALIBRATED, zero failing criteria** —
re-verified in this session before any work, and untouched by it.

## 1. THE OBJECT, AND WHY THE PREDECESSOR COULD NOT SEE IT

`RESULT-miso264` §7 reached a real conclusion by two price-side instruments: in
2020 the price residual and the coal-volume residual demand **opposite** offer
moves, so *"MISO's coal is held off by something that is NOT its offer — a
QUANTITY / COMMITMENT object."* That is correct and it stops one step short. Both
of its instruments were **price-side**, and the thing holding the coal off is not
priced at all.

The quantity-side test neither instrument performed is one line. The LP bounds
every coal row above by `pmax * availability`, so the most energy a plant can
possibly deliver is

```
ceiling[t] = sum_{g in plant} pmax[g] * availability[g, t]      (MW)
```

Set that beside the CAMPD meter the benchmark already commits for the same plant
and the same hour, and ask how often the meter is **above** it.

## 2. THE ANSWER, AT ZERO LP

### 2.1 The annual form — the headroom exists in aggregate and NOT plant by plant

`scripts/probes/_miso265_coal_availability_ceiling.py`, MISO 2020, on the keeper's
own reconstructed fleet (3,291 LP rows):

| class | rows | pmax GW | ceiling | model | actual | head | util |
|---|---:|---:|---:|---:|---:|---:|---:|
| COAL_BIT | 233 | 16.76 | 78.28 | 55.36 | 66.27 | **+12.01** | 0.707 |
| COAL_PRB | 394 | 35.24 | 168.48 | 121.91 | 126.68 | +41.81 | 0.724 |
| COAL_LIGNITE | 45 | 1.85 | 13.63 | 9.21 | 8.36 | +5.27 | 0.676 |

At **class** level there is headroom, so this is not an aggregate wall. Plant by
plant it is a different statement: **seven COAL_BIT plants carry an annual ceiling
below their own measured annual output**, 4.191 TWh of it, led by

| plant | LP MW | mean avail | ceiling | actual | head |
|---|---:|---:|---:|---:|---:|
| R M Schahfer | 1,625 | **0.054** | 0.769 | 2.695 | **−1.926** |
| Prairie State | 1,630 | 0.733 | 10.467 | 11.308 | −0.841 |
| Dallman | 492 | **0.026** | 0.112 | 0.756 | −0.644 |
| Warrick | 662 | 0.748 | 4.337 | 4.718 | −0.381 |
| Coal Creek | 1,142 | 0.799 | 7.996 | 8.218 | −0.222 |

An availability of **0.054** on a four-unit coal station that metered 2.7 TWh is
not a description of that station's 2020.

### 2.2 The hour-grain form — which removes the timing escape

The annual form can in principle be produced by a timing mismatch. The hour-grain
form (`scripts/probes/_miso265_ceiling_vs_meter_hourly.py`) cannot:

| year | infeasible energy | plant-hours | plants | COAL_PRB | COAL_BIT | COAL_LIGNITE |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | **25.414 TWh** | 142,058 | 51 | 16.804 | 7.659 | 0.952 |
| 2021 | **32.427 TWh** | 192,247 | 52 | 24.032 | 7.278 | 1.116 |
| 2022 | **28.939 TWh** | 171,591 | 48 | 22.463 | 5.303 | 1.173 |
| 2023 | **22.337 TWh** | 135,172 | 45 | 17.069 | 4.000 | 1.267 |
| 2024 | **20.243 TWh** | 119,639 | 45 | 15.226 | 3.860 | 1.157 |
| 2025 | **26.097 TWh** | 164,540 | 44 | 19.893 | 4.994 | 1.210 |

Every hour in those sets is an hour the solved dispatch **could not have
reproduced at any price, under any offer curve, with any commitment rule.** It is
not a calibration residual. It is an infeasible pair of measured inputs.

Two shapes are present and both are real. Some plants are short on **level**
(Schahfer 0.769 against 2.590; South Oak Creek 1.311 against 3.380). Others carry
enough annual ceiling but it is placed in the **wrong hours** — Monroe (MI) has a
ceiling of 15.860 against a meter of 14.269 and still breaches in 3,306 hours.

### 2.3 The instrument is validated, not asserted

The whole finding rests on `pmax * availability` really being this LP's upper
bound, so that is tested rather than assumed, by the strongest check available:
**the keeper's own solved dispatch must never exceed it**
(`scripts/probes/_miso265_ceiling_selfcheck.py`). On MISO 2020, 52 coal plants:
**zero breach.** The largest apparent excess anywhere is 11.61 MW at Monroe
against a decode quantization step of 32.93 MW — i.e. inside the codec, not the
model. Verdict **PASS**: the ceiling is a valid hard bound, so a meter above it is
an infeasible input pair.

That check is also what sets the reporting threshold. The committed plant series
are `_b64` uint8 percent-of-capacity, so a breach smaller than one step is codec
noise; requiring a full step **shrinks** the 2020 figure only from 25.438 to
25.414 TWh, which is the measure of how little of this is decode error.

**The two sides are on the same basis, checked rather than assumed.** The obvious
way this finding could be an artifact is a gross-vs-net mismatch — CAMPD's native
`grossLoad` carries auxiliary load a net capability does not, and at ~5 % of MISO
coal that alone would be ~10 TWh. It is not the case: the committed series is
**net**, by the bench builder's own statement (`render_calibration_html.py:1072`,
*"reconstructing CAMPD annual GROSS from the committed NET series"*), which is the
same net basis `FINDING-miso261` §2 uses and the correct one to set against
`pmax * availability`.

## 3. THE MECHANISM — a FULL-PLANT derate, not an economics story

**The sharpest form of the contradiction removes every remaining argument.** Ask
only for the hours in which the model says a plant is **100 % unavailable** and
the meter says it ran (`scripts/probes/_miso265_hard_zero_hours.py`). MISO 2020:

> **5.318 TWh metered across 24,100 plant-hours at `availability == 0`, over 33
> plants.** Of the 109,392 coal plant-hours the overlay drives to a hard zero,
> **22.0 % are contradicted by the plant's own committed meter.**

| plant | LP MW | hours at avail=0 | contradicted | TWh | peak MW |
|---|---:|---:|---:|---:|---:|
| R M Schahfer | 1,625 | 8,112 | 8,019 | 2.167 | 754 |
| South Oak Creek | 1,112 | 4,224 | 3,368 | 0.832 | 597 |
| Dallman | 492 | 7,536 | 4,779 | 0.530 | 306 |
| Sherburne County | 2,238 | 1,224 | **1,224** | 0.454 | **1,602** |
| Marion | 290 | 5,808 | 3,408 | 0.305 | 248 |

Sherburne County is the cleanest single statement available: in **every one** of
the 1,224 hours the model calls it entirely out, it was generating — up to
**1,602 MW**.

**The outage overlay alone is the whole driver**, not the statistical WEFOR
stacked on it. `unit_outage_derate_factors` returns a factor that is *itself*
exactly 0.0000 for 8,112 h at Schahfer (mean 0.0559), 7,536 h at Dallman, 4,224 h
at South Oak Creek, 1,224 h at Sherburne.

And the mechanism is the accumulator's own documented failure mode. It derates by
`unit_capacity_mw / plant_capacity_mw` and **"concurrent units sum, clipped at
full derate"** — so when a plant's unit windows overlap and the shares are taken
against a denominator the LP's own fleet does not share, the sum runs past 1.0 and
the plant is zeroed outright. The code states the arithmetic in the abstract:

> the numerator is the dark unit's capacity while `cap[tgt]` already excludes it,
> a double-count that can **sum to 1.23 of the modeled OP half and clip it to 0.0**

At Schahfer the extract's `plant_capacity_mw` is **2,009 MW** against the LP's
**1,625 MW** of coal — a ratio of **1.236**.

### 3.1 I FIRST ATTRIBUTED THIS TO ECONOMIC IDLENESS. THAT WAS WRONG.

Schahfer's sixteen 2020 windows (unit 14 out 2/02–6/29 and 7/16–12/31, unit 15
out 7/16–12/01, …) cover essentially the whole year, and the obvious reading is a
coal station standing idle in the cheapest gas year of the span — *didn't run* fed
back as *couldn't run*, which rule 13 `[R-MEASURED]` forbids and which this repo's
merit-order guard exists to strip out.

**The measurement refuses that reading.** The guard reclassifies **0 of
Schahfer's 16 windows** as economic lay-up; all 16 survive as genuine outages. So
whatever the guard's merit test sees, it does not see these as economics, and the
zeroing is a **derate-arithmetic** defect rather than an economics one. The
economic-idleness story is withdrawn; the arithmetic one is what the numbers
support.

## 4. FOUR CANDIDATE REPAIRS, ALL TESTED AT ZERO LP, ALL REFUTED

The accumulator's docstring names two gated repairs for precisely this
numerator/denominator pathology, and the matrix names a third route. All were
sized directly on the rebuilt factors and the same committed meter
(`scripts/probes/_miso265_derate_variant_sizing.py`), MISO 2020:

| variant | plant-h at avail=0 | contradicted h | metered TWh | plants |
|---|---:|---:|---:|---:|
| **incumbent (keeper)** | 103,704 | 23,849 | 5.184 | 33 |
| `+unit_outage_fleet_status_scope` | 103,704 | 23,849 | 5.184 | 33 |
| `+unit_outage_extract_basis_share` | 103,704 | 23,849 | 5.184 | 33 |
| `+both` | 103,704 | 23,849 | 5.184 | 33 |
| `+campd_outage_merit_order_guard` | 125,880 | **24,193** | **5.234** | 37 |

**Not one of them reduces the contradiction, and the merit-order guard makes it
slightly worse.** That is the single most useful line in this document for a
successor: it retires four candidate levers **before** anyone spends the twelve
shard-years that arming two of them as separately-adjudicated rungs would cost.

**The flags are live, not silently ignored** — checked, because three identical
rows is exactly what a dead switch looks like. Against the incumbent they move
**4 / 37 / 16 of 126–138 bins** with max |Δ| of 1.000 / 0.536 / 1.000. They are
doing real work; it simply lands on other bins than MISO's contradicted coal.

Two operational notes the successor needs:

* **MISO's companion extracts did not exist and now do.** This session derived
  them with the deriver's own committed constants and nothing tuned (rule 23
  `[R-FROZEN-DERIVE]`): `campd-unit-outages-perunit-MISO.csv` (10,905 windows) and
  `campd-unit-outages-perunitmerit-MISO.csv` (9,165 windows + 1,740 reclassified
  to `campd-unit-outages-layup-perunitmerit-MISO.csv`). Before this the loader
  would have **fallen back to the incumbent extract** and both flags would have
  been silently inert — a trap worth naming, since a lane that armed them and saw
  nothing move would have drawn exactly the wrong conclusion.
* **`unit_outage_fleet_status_scope` and `unit_outage_extract_basis_share` are not
  reachable from `run_year` at all.** They are `ScenarioConfig` fields
  (`scenarios.py:15187`, `:15405`) with no kwarg plumbing, so
  `replay_keeper`'s binding guard rejects them outright — *"meta.json keys not
  bound to solve_and_persist kwargs"*. They cannot be A/B'd through a bundle
  reconstruction today. Given they are measured inert here that is not this
  lane's problem to fix, but it is a rule 24 `[R-REGISTRY]` gap: a registered
  tunable the runner cannot reach.

## 5. WHAT THIS PROVES AND WHAT IT DOES NOT

**Proved.** (a) Two measured inputs the keeper carries are mutually infeasible, at
20–32 TWh/yr in all six years. (b) The contradiction is not a dispatch or offer
residual — the ceiling is a validated hard bound. (c) Its sharpest subset needs no
interpretation at all: 5.318 TWh metered in hours the model calls the plant
**entirely** unavailable. (d) The unit-outage derate alone produces it, by summing
concurrent unit windows and clipping at full derate. (e) Four existing candidate
repairs do not touch it.

**NOT proved, and not claimed.** That arming the guard closes C1 2020 COAL_BIT, or
C3a 2020, or moves any gate in any direction. Rule 1 `[R-STRUCT]`: this is a
structural-correctness case under rule 14 `[R-ACCURATE]` and rule 13, and it must
not be argued from the residual. **The residual is not evidence for it and a worse
residual would not retract it.**

**Disclosed because it cuts against the lane's own interest:** the defect is
**systemic, not 2020-specific**, and the train tier carries it at 20–26 TWh/yr
while reading **CALIBRATED**. So the repair is a live **G-NOFLIP risk on a
CALIBRATED tier**, and that has to be stated before it is attempted, not after.
A second disclosure: the 2020 headroom at class level is `+12.01` TWh against a
`−10.92` miss, so even a perfect availability repair is not arithmetically
guaranteed to close C1 2020 on its own.

## 6. FOUR CORRECTIONS TO MY OWN WORK — stated, not buried

1. **I read OTHER_FOSSIL off the wrong artifact.** My first table showed model
   `OTHER_FOSSIL` = 0.000 against 9.616 actual and I briefly treated it as a
   missing class. It is not. `fleet.eia860.apply_other_fossil_scoring` re-buckets
   Ninemile Point (1403) **symmetrically on both sides**, and `class_hourly` is
   written *upstream* of it while the bench/payload pair is *downstream* — the
   crossed comparison `docs/calibration-log/miso.md` already records at the
   miso-127 correction. On the scored basis the model carries 9.19 against 9.62.
   Caught by the log, before it cost anything.
2. **My first hourly decode was wrong.** I decoded the per-plant series as int16
   (`_b64_i16`); that codec is the LMP-delta heatmap's. The plant series are
   `_b64` uint8 percent-of-capacity. Every number in that first pass was
   meaningless and is discarded, not reconciled.
3. **My per-plant class map picked the wrong label for split plants.** Taking the
   first key for a plant carrying two classes mapped Edwardsport to `CC_REGULAR`
   and dropped its entire coal ceiling, reporting it as `0 MW`. Fixed to prefer
   the coal rank, with an assertion that no MISO plant splits across two coal
   ranks (verified, it does not).
4. **My first self-check tolerance was 1 MW and the self-check FAILED.** It was
   right to fail: 1 MW is far inside a 33 MW quantization step. The threshold is
   now the measured codec step, and the finding is reported at the tighter number
   it produces.
5. **I proposed the wrong cause and then refuted it myself** — §3.1. The
   economic-idleness reading was the natural one from the extract's windows, it
   was wrong, and the guard's own reclassification is what says so. The correction
   matters beyond bookkeeping: acting on the first reading would have cost twelve
   shard-years for a lever measured here to be inert.

## 7. ROUTED, NOT ABSORBED

1. **THE REPAIR IS NOT YET IDENTIFIED, AND THAT IS THE HONEST STATE.** §4 refutes
   every candidate this repo already carries. What the successor inherits is a
   precisely-located defect (the concurrent-share sum clipping at full derate, on
   a denominator the LP's fleet does not share) and four levers it now knows not
   to spend. The next step is a zero-LP reconciliation of the extract's
   `plant_capacity_mw` against the LP's own per-bin capacity at the 33
   contradicted plants — **not** a solve.
2. **`COAL_LIGNITE` 2025 has NEGATIVE annual headroom** (ceiling 5.75 against an
   actual 6.13) and 2022 is −0.04. A class whose whole-year ceiling is below its
   whole-year meter cannot be fixed by any dispatch lever at all.
3. **`OTHER_FOSSIL` is −0.43 to +0.69** on the scored basis across the span, i.e.
   the ±9 TWh "miss" quoted in `RESULT-miso259` §1 and repeated since is an
   upstream/downstream artifact of the same transform in item 6.1. Anyone citing
   it should re-check the basis first.
4. **wind is +3.67 to +5.14 TWh long in all six years** — a stable ungated
   over-production nothing in C1 sees, which displaces thermal in every year.
