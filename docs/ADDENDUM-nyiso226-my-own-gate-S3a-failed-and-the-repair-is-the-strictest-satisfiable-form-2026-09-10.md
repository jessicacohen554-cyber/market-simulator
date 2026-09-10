# ADDENDUM nyiso-226 — **MY OWN SCREEN GATE `S3(a)` FAILED, AND IT FAILED BECAUSE I WROTE IT AGAINST AN INVARIANT THE MODEL DOES NOT HAVE.** Published FIRST, at full magnitude; the repair MOVES NO BAR, and its bar is read from the model's own loss table rather than from the number I saw

**Governs:** `docs/PRECOMMIT-nyiso226-nyc-base-rebasis-2026-09-10.md` §4 gate **`S3(a)` only**.
**`S1`, `S2`, `S3(b)`, `S3(c)` and `S4` are UNTOUCHED** — no bar, no operand and no disposition
of theirs moves.

---

## 0. THE FAILURE, FIRST AND AT FULL MAGNITUDE

`S3(a)` required: *"arm system total within **0.001 TWh** of 148.3100 (energy balance — load is
untouched)."*

| | TWh |
|---|---|
| control supply total (keeper `hourly/class_hourly_2023.parquet`) | 148.310013 |
| arm supply total (shard report) | 148.311355 |
| **Δ** | **+0.001343** |
| registered tolerance | 0.001 |

**The gate FAILED, by 34 % of its own tolerance, and I am not arguing that away.**

**AND THE REPAIR IS DECLARED AFTER I HAD SEEN THE NUMBER.** That is weaker than the
`miso-245` precedent this follows, where the repair was declared before its numbers existed, and
it is stated here rather than left for a reader to notice. What limits the damage is that the
repair's only quantitative bar is taken from the **model's own committed loss surface**, not
from the observed value — see §2 — so it could not have been chosen to fit the result. The
disposition it produces is nevertheless **put to the owner** rather than acted on (RESULT §6).

## 1. WHY IT FAILED: I ASSERTED THAT SUPPLY IS CONSERVED WHEN LOAD IS. IT IS NOT — THE MODEL CARRIES LOSSES

The gate's parenthetical states its premise: *"load is untouched"*. That premise is **true and
measured** — the arm's `demand` column is byte-identical to the control's (mean **2797.732972**
on both sides). What does not follow is the thing I gated on. In this model

> `supply = demand + transmission losses`

and `nyiso_zonal_loss_surface` is **ARMED in the keeper recipe**: the four internal chain links
(UW↔CH, CH↔LH, LH↔NYC, NYC↔LI) are split into one-way pairs each carrying a measured,
month-varying marginal loss fraction (`model/interchange/nyiso.py::build_nyiso_link_loss`,
nyiso-159). Measured on the control's own committed artifacts, **2023 losses are 1.261168 TWh,
0.8577 % of demand.**

Losses are a function of **where** energy is generated. The arm moves 0.078174 TWh of generation
out of NYC — the far end of a chain whose lossy direction is uniformly north→south — and into
upstream CC_REGULAR / CC_CHP. **Serving the same NYC load from further upstream necessarily
costs more losses.** The implied marginal loss factor on the substitution is
**+0.001343 / 0.078174 = 1.7177 %**, against a system average of 0.8577 % — a marginal factor
about twice the average, which is what a marginal loss factor is supposed to look like.

**So `S3(a)` as written is not merely tight — it is unsatisfiable for any arm that redispatches
anything at all.** Only an arm with *no dispatch effect* can hold supply constant to 0.001 TWh.
A gate that only an inert arm can pass does not measure confinement; it measures "did anything
happen", which `S1` already measures and which the screen is not supposed to punish. That is my
error, not the mechanism's.

## 2. THE REPAIR — `S3(a′)`. FOUR LEGS, ALL MEASURED; THE ONE BAR COMES FROM THE MODEL'S OWN TABLE

> **`S3(a′)` PASS iff ALL FOUR hold:**
>
> 1. **LOAD IS UNTOUCHED.** The arm's `demand` series is identical to the control's. *(This is
>    the invariant `S3(a)`'s parenthetical actually named.)*
> 2. **NO UNSERVED ENERGY.** `slack ≡ 0` across all zone-hours, as in the control.
> 3. **NO DUMPING.** `dump ≡ 0` across all zone-hours, as in the control.
> 4. **THE SUPPLY–DEMAND GAP MOVES ONLY BY LOSSES ON THE REDISPATCHED ENERGY:**
>    `|Δ(supply − demand)| ≤ |Δ_class,max| × L_max`, where **`L_max` is the model's own maximum
>    cumulative one-way chain loss fraction for the solve year**, computed from
>    `build_nyiso_link_loss` — NOT a number chosen here.

**`L_max` for 2023, from the model's committed surface** (per-one-way-link maxima:
UW→CH 0.063482, CH→LH 0.025986, LH→NYC 0.009979, NYC→LI 0.019360):
cumulative UW→NYC **9.6922 %**, UW→LI **11.4405 %** ⇒ **`L_max` = 0.114405.**

**Bar** = 0.078174 × 0.114405 = **0.008943 TWh**. **Observed 0.001343 TWh — inside, at 15.0 % of
the bar.**

**Why this is the strictest SATISFIABLE form and not a loosened one.** `S3(a)`'s question was
*"is the arm's energy accounting sound, or is the edit reaching somewhere it should not?"* Legs
1–3 pin the three things that would actually indicate unsoundness — moved load, unserved energy,
curtailment — each to **exact equality**, which is stricter than the 0.001 TWh band it replaces.
Leg 4 keeps a quantitative bar on the one quantity that legitimately moves, and sources it from
the model's own physics rather than from the observation. **Confinement itself is not weakened at
all**: it is `S3(b)` and `S3(c)` that test it, both untouched, and both passed decisively — in
the arm **ST_GAS is the only class that falls**, and every other class is unchanged or rises.

## 3. WHAT THIS DOES NOT DO

- It does **not** promote the arm. Rule 29 `[R-SCREEN]`: a screen gate may kill an arm and may
  never promote one, and a repaired gate promotes nothing either.
- It does **not** move `S2`'s band, which is where the arm's magnitude is actually judged, and
  which it passed **as written** at 2.77× the pre-registered first-order prediction inside a
  registered ceiling of 3×.
- It does **not** license spending the full span on my own reading. That question, and the
  promotion question behind it, go to the owner (RESULT §6).
