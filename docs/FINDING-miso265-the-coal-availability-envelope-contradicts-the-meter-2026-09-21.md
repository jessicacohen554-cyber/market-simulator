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
CAUSE   : the CAMPD outage detector books ECONOMIC IDLENESS as UNAVAILABILITY. This
          repo already has the repair and already names it — the merit-order guard's
          economic-lay-up reclassification — and MISO runs with it OFF and without the
          extract it needs.
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

## 3. THE CAUSE, FROM THE EXTRACT ITSELF

The windows driving the derate are visible in
`data/raw/campd-unit-outages-MISO.csv`. R M Schahfer's 2020 rows:

| unit | window | days |
|---|---|---:|
| 14 | 2020-02-02 → 2020-06-29 | 147.6 |
| 14 | 2020-07-16 → 2020-12-31 | 168.5 |
| 15 | 2020-07-16 → 2020-12-01 | 137.6 |
| 17 | 2020-02-29 → 2020-05-08 | 68.8 |
| 18 | 2020-10-10 → 2020-12-12 | 63.6 |

Sixteen windows, covering essentially the whole year across the four units. These
are not forced or planned outages. **They are a coal station standing idle in the
cheapest gas year in the span** — the detector is a sustained-zero-output detector,
and in 2020 sustained zero output at a Midwestern coal plant is overwhelmingly
economics, not unavailability.

Booking that as unavailability is a **rule 19 `[R-ONE-MECH]` double-count**: the LP
already declines an uneconomic unit on its own merit order, and the derate then
removes the same unit again, as capacity. It is also the exact thing rule 13
`[R-MEASURED]` forbids — *didn't run* fed back as *couldn't run*.

**This repo already knows all of this and already built the repair.** From
`market_sim.data.outages.unit_layup_csv_for_iso`, in the code today:

> windows the merit-order guard RECLASSIFIED as economic lay-up … **These windows
> deliberately stay OUT of the availability envelope (an economically idle unit is
> available; the LP declines it on its own economics)**

and MISO's own keeper `2026-08-20-miso-173-layup-mask` defends the same line from
the other side — *"feeding them back as unavailability would re-arm the 23-46 %
phantom-outage bias the guard removes."* MISO arms the **mask** and not the
**guard**.

## 4. WHAT IS ACTUALLY OFF, AND WHAT IT WOULD TAKE

`campd_outage_merit_order_guard` is **`None` (off)** in the keeper's `meta.json`.
MISO's matrix cell reads **`U` — untested** (row added by nyiso-177, rule 28(c)),
with its own instruction for a lane taking it up: *"arms `campd_per_unit_attribution`
first and adds the guard as its second, separately-adjudicated rung."* Neither is a
`R`/`I`/`G` cell, so this is **on-queue and not a DO-NOT-REDO**.

The operational blocker is data, not code: MISO has **neither**
`campd-unit-outages-perunit-MISO.csv` **nor** `campd-unit-outages-perunitmerit-MISO.csv`.
The loader falls back to the incumbent extract when a companion is absent, so
arming the flags today would be **silently inert** — a trap worth naming, because
a lane that armed them and saw no movement would draw exactly the wrong conclusion.

## 5. WHAT THIS PROVES AND WHAT IT DOES NOT

**Proved.** (a) Two measured inputs the keeper carries are mutually infeasible, at
20–32 TWh/yr in all six years. (b) The contradiction is not a dispatch or offer
residual — the ceiling is a validated hard bound. (c) The conflation of economic
idleness with unavailability is visible in the extract's own windows. (d) The
repair exists in this codebase, is documented in it, and is off for MISO.

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

## 7. ROUTED, NOT ABSORBED

1. **The arm is specified and NOT taken here** — §4. Two rungs, `campd_per_unit_attribution`
   then `campd_outage_merit_order_guard`, each needing its own derived MISO extract
   and each a six-year span under rules 34(c)/36.
2. **`COAL_LIGNITE` 2025 has NEGATIVE annual headroom** (ceiling 5.75 against an
   actual 6.13) and 2022 is −0.04. A class whose whole-year ceiling is below its
   whole-year meter cannot be fixed by any dispatch lever at all.
3. **`OTHER_FOSSIL` is −0.43 to +0.69** on the scored basis across the span, i.e.
   the ±9 TWh "miss" quoted in `RESULT-miso259` §1 and repeated since is an
   upstream/downstream artifact of the same transform in item 6.1. Anyone citing
   it should re-check the basis first.
4. **wind is +3.67 to +5.14 TWh long in all six years** — a stable ungated
   over-production nothing in C1 sees, which displaces thermal in every year.
