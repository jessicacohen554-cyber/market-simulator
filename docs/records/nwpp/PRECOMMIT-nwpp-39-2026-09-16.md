# PRECOMMIT — NWPP-39: a zero-baseline guard on the EIA-930 `NG:` unit-slip screen

**Lane** NWPP-39 · **Base sha** `a9950612798b05dbb05b0290458bbdde4037aebc` (`main` at issuance; the
harness-designated branch `claude/tender-edison-9nu5h8` carries the work, as NWPP-37b's did)
**Date** 2026-09-16 · **Model** Fable · **DATA PROFILE** `nwpp` (every one of the 26 `<BA> hourly`
extracts the nine regions read is already on disk, so the census below is over all nine)
**Charter** NWPP-DESK r#8 issuance notice, owner ruling N13. **No LP is run by this lane.**

## 0. Ordering of this record

This document is committed BEFORE the guard is written into `actuals.py` and BEFORE the nine-region
before/after measurement is taken. What was read before writing it, stated so the reader can judge
whether the guard is a construction or a fit:

* NWPP-37 §6 (the specification — its measurement is taken as given, not re-derived), NWPP-37b
  (which moved the screen per pool member, so the guard here runs on every NWPP member series too),
  `_screen_fuel_spike_columns` and `frames.py` in full.
* **A population census** of every `NG: <CODE>` series in every extract on disk, 2019–2026
  (737 series, 687 with a positive p99.9): median, p95, p99, p99.9, max, fraction of positive hours,
  and the current screen's flag count. The census is a property of the population; it was read to
  see where the population sits relative to the construction in §2, **not** to choose the
  construction. **No alternative rank and no alternative factor was tried**, before or after reading
  it. The one alternative constructions considered (§2.3) were rejected on principle, not on what
  they would flag.
* The hour-by-hour context of the four series §3 predicts will move — read to classify them under
  the rule in §4.2, which is stated here before the exit measurement is taken.

## 1. The defect, in the screen's own terms

The screen's second limb flags an hour above `2.5 × p99.9` of the series (the ninth-largest of 8,760
hours). Its premise, from the docstring: a legitimate fuel series cannot carry one hour 2.5× above
its ninth-largest hour, because a fleet dispatched against a nameplate ceiling occupies the
neighbourhood of that ceiling for many hours — **the top of a legitimate series is a plateau**. That
premise holds only when the ninth-largest hour lies INSIDE the occupied top regime. For a series
whose operating hours are rare, short events, rank 9 lies outside every event, and the anchor is the
idle tail: SOCO `NG: OIL` 2024 has 285 positive hours of 8,752, 28 hours ≥ 50 MW, 8 hours ≥ 100 MW;
its "robust peak" of 71.7 MW is the ninth-largest hour of a fleet that is essentially always off.
The Winter Storm Heather start (7 hours, 530–801 MW) is shorter than the anchor's rank, so the whole
event exceeds 2.5× an anchor that is not an operating level. The same fleet ran ≥ 9 hours above
851 MW in 2025 (p99.9 = 851 MW) and the screen flagged nothing there — **whether a real peaker start
is deleted depends on whether the event lasted 9 hours**, which is the defect in one sentence.

The screen already recognises the degenerate end of this: "a series whose robust peak is not positive
… has no operating scale to screen against and passes through" (`peak <= 0.0`). The guard is that
sentence extended from *not positive* to *not a plateau level*.

## 2. The guard — CONSTRUCTED, fixed here

### 2.1 Statement

The anchor is tested by the screen's **own premise at the next-coarser rank**. Let `peak = p99.9`
(rank ≈ 9) and `plateau = p99.0` (rank ≈ 88). If

    peak > _FUEL_SPIKE_RATIO × plateau          (i.e. p99.9 > 2.5 × p99.0)

then the ninth-largest hour is itself a "spike" relative to the eighty-eighth: the top 0.1 % of the
series is a tail, not a plateau, the premise the second limb rests on is falsified by the series
itself, and there is nothing to screen against — the column passes through untouched, exactly as
the `peak <= 0` case does today. `plateau = 0` with `peak > 0` is the same case (the top 1 % is
idle), and it falls out of the inequality with no special branch.

### 2.2 Why this is a construction and not a fit

* **No new factor.** The factor is `_FUEL_SPIKE_RATIO`, bound by import to the demand screen's
  `_DEMAND_SPIKE_THRESHOLD` (rule 19 `[R-ONE-MECH]`, SPP-31 §3.2). The guard asks of the anchor
  exactly what the screen asks of an hour.
* **No new rank chosen by outcome.** The screen's anchor is already one decade of rank below the
  maximum (rank 1 → rank 8.76 = 0.1 % of 8,760). The guard steps the same decade again:
  `_FUEL_SPIKE_PLATEAU_PCT = 100 − 10 × (100 − _FUEL_SPIKE_SCALE_PCT) = 99.0`, written in the code
  as that expression so the derivation is literal. The "10" is the decade the screen already took.
* **Scale-invariant.** It is a ratio of two order statistics of the same series; it reads no MW
  level, no other column, no other BA and no residual. Rule 13 `[R-MEASURED]` admissibility is the
  screen's own: it regenerates for any forward year from that year's own extract.
* **Monotone in the safe direction.** The guard can only *release* a series (return it unscreened);
  it can never flag an hour the current screen does not. And on any series where the guard is
  active, the current screen is already structurally unable to distinguish an artifact run from an
  operating event (its anchor is not a level), so nothing that was a *reliable* repair is given up.

### 2.3 Alternatives considered and rejected — on principle

| construction | rejected because |
|---|---|
| a MW floor on the anchor (the desk's "floor on the anchor" phrasing) | a magic number (rule 5) and not scale-invariant: the same floor cannot be right for a 200 MW PUD member (CHPD, DOPD) and a 47 GW BA |
| `median > 0` as the eligibility test | exempts every solar series (night hours are zero; FLA 2023 `NG: SUN` median 70 MW, 60 % positive) although solar has an unambiguous nameplate plateau — the guard would remove real coverage from a class the screen handles correctly |
| a minimum fraction of positive hours | a new free number with no derivation from the premise; and it is the median test in disguise |
| the anchor vs the MEDIAN (`p99.9 > 2.5 × median`) | the docstring already proves the median is not a fuel series' operating scale (4,116 MISO solar hours); it would release every solar and every peaker series |

### 2.4 What the guard does NOT do (rule 19)

It does not touch the pooled-vs-per-member population question (NWPP-37 §5, since taken by
NWPP-37b): the guard is evaluated on whatever population the caller hands the screen, member or
pool. It does not touch `_screen_demand_spikes` / `_screen_demand_dropouts` — the CHPD cold-snap
failure on the DEMAND side is the same failure mode and a different phenomenon; the demand spike
screen is already deliberately not applied to pool members (`frames._pool_hourly_frame`). It adds
no `ScenarioConfig` field, no CLI flag, no env var, no matrix row (rules 24, 28(c)).

**Interaction with NWPP-37b's two reported-not-adjudicated member flags** (PGE 2023 `NG: OTH` 119 MW,
NWMT 2024 `NG: WAT` 1,782 MW): PGE 2023 `NG: OTH` reads p99.9 = 33 MW against p99 = 14 MW, ratio
2.357 — **below** 2.5, so the guard is inactive there and the flag stands exactly as NWPP-37b left
it; NWMT `NG: WAT` is a plateau series (ratio 1.024). Neither adjudication is pre-empted by this lane.

## 3. Pre-registered predictions, read off the census

The census places the population as follows (ratio `p99.9 / p99.0`, 687 series with p99.9 > 0):
median 1.066, p90 1.337, p95 1.915. **26 series** sit above 2.5 (guard active). They are, with two
exceptions, `NG: OIL` series of rarely-run oil fleets (FLA, NYIS, ISNE, SWPP, SOCO, PJM 2022) and
sub-10-MW `NG: OIL` / `NG: COL` / `NG: OES` series whose top 1 % is idle; the two exceptions are
ERCO `NG: OTH` 2019 and 2025, where a ≥ 9-hour run lifted the p99.9 to 3,800 / 22,972 MW against a
p99 of 118 / 122 MW — a case the current screen cannot flag either (its anchor is the lifted one),
so the guard changes nothing there.

Of the **21 series the current screen flags**, the guard is active on exactly **four**:

| series | p99 | p99.9 | ratio | flagged hours | flagged max |
|---|---:|---:|---:|---|---:|
| SOCO 2023 `NG: OIL` | 22.41 | 88.24 | 3.94 | h7975 | 390 MW |
| SOCO 2024 `NG: OIL` | 25.00 | 71.73 | 2.87 | h386–392 | 801 MW |
| IPCO 2024 `NG: OIL` | 0.00 | 2.24 | ∞ | h298 | 6 MW |
| NEVP 2024 `NG: OIL` | 0.00 | 1.00 | ∞ | h82 | 3 MW |

The other 17 flagged series — including both control artifacts (SWPP 2023 `NG: WND`, ratio 1.060;
NYIS 2024 `NG: OTH`, ratio 1.051), every NWPP member slip (AVA / NWMT, ratios 1.02–1.06), SOCO
2025 `NG: NG` (1.087) and PGE 2023 `NG: OTH` (2.357) — have the guard inactive and are **predicted
byte-identical**. FLA (a proxy BA in `interchange/spec.py`, not a registered region) is flagged in
`NG: OTH` / `NG: SUN` at ratios 1.10–1.25: byte-identical.

Predicted movers at the consumer level: the SOCO frame and SOCO benchmark `oil` in 2023 and 2024;
the NWPP pool frame's `NG: OIL` in 2024 (through the IPCO and NEVP member frames, per NWPP-37b's
per-member seam) and the NWPP benchmark `oil` 2024, at MWh scale. **Nothing else, in any region.**

## 4. Gates — STOP gates, fixed before the measurement

* **G1 — the two known artifacts are still repaired.** SWPP 2023 `NG: WND` h3907 and NYIS 2024
  `NG: OTH` h6759 are NaN after the screen; the SPP 2023 wind benchmark still reads 103.0488 TWh and
  the NYISO 2024 other benchmark 3.3197 TWh (the existing live pins). **Fail = STOP.**
* **G2 — restoration.** SOCO 2024 benchmark `oil` 0.0012 → 0.0056 TWh (NWPP-37 §6's number), with
  h386–392 carrying the filed values.
* **G3 — nine-region byte-identity outside §3's predicted set.** Every `NG:` column of every region
  frame (`_eia_hourly_frame_filled` for the 8 single-BA regions and the NWPP pool, plus the 17 NWPP
  member frames) and every `load_eia_hourly_benchmark` series, nine regions × 2019–2026, hashed
  before and after. Any mover outside the predicted set is reported and classified; **an
  unpredicted mover is not itself a STOP, but a mover classified as re-admitting an artifact is.**
* **G4 — the screen's own tests still pass**, plus the new pins: a Heather-shaped synthetic run on a
  zero-baseline column survives; a unit slip on a plateau column in the same frame is still repaired;
  the parameter-free pin extends to the plateau rank's derivation.

### 4.1 Non-gates, stated so they cannot become gates

No residual, no calibration score, no keeper number is consulted. The SOCO region has no keeper.
Whether the restored oil energy improves any SOCO C1/C4 number is not asked.

### 4.2 Classification rule for every released hour — fixed here

A released hour set **re-admits an artifact** if ANY released hour carries one of the three unit-slip
signatures the screen's own record documents:

* **S1** — the fuel exceeds the BA's `Net generation` in that hour (the SOCO 2025 `NG: NG` signature:
  70,683 MW of gas in a 32,574 MW hour);
* **S2** — a decade mis-scaling: the hour is ≥ 10× BOTH of its neighbouring hours (the SWPP / NWMT /
  AVA signature: 159× / 100× / 1,000× the adjacent readings);
* **S3** — the hour abuts an EIA-930 reporting gap (a NaN run) within ±1 h in the same frame (the
  NYIS 2024 `NG: OTH` signature: 16,117 MW immediately followed by a 9-hour gap).

Otherwise it **restores real data**. A single re-admitted artifact is a STOP, per the charter.

## 5. What is in the diff

* `src/market_sim/data/eia930/actuals.py`: `_FUEL_SPIKE_PLATEAU_PCT` (derived expression, cited),
  the guard line in `_screen_fuel_spike_columns`, the docstring's "known defect" paragraph rewritten
  as the repair, and the "no operating scale" sentence extended.
* `tests/unit/data/test_eia930_fuel_spike_screen.py`: the pins in G4, plus a live SOCO 2024 pin.
* `docs/handoffs/PRECOMMIT-nwpp-39-2026-09-16.md` (this), `FINDING-nwpp-39-2026-09-16.md`.

Not touched: `frames.py` (the seam does not need to know about the guard — it is inside the one
function), `demand.py`, any registry, config, verdict script, `frontend/`, the plan, the ledger, the
matrix files (no field, no row, no cell: a data-repair correction is not a mechanism).
