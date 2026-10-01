# FINDING — miso-127: miso-114's overnight mispriced-marginal-unit reading is FALSIFIED, and the measurement it asked for is BLOCKED by a bench-coverage gap nobody had measured

**Session:** miso-127 (dispatch label `pjm-154-cross-iso-queue`; Lane B — the PJM
lane had no owner answer, so this took MISO, the last ISO with a failing
criterion). **Branch** `claude/pjm-154-cross-iso-queue-5e2frp`.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED.**
MISO keeper unchanged at `2026-08-04-miso-126-steampart-b` (**NOT-YET**, C7
`COAL_PRB` shape the sole FAIL). Rule 22 `[R-HOLDOUT]`: 2023–2025 only — MISO
holds no `complete` marker and the holdout spend freeze is active.

**Pre-registration** `results/calibration/PREREG-miso127-overnight-gas-composition-2026-08-04.md`,
committed and pushed at `49cf0877` **before** any adjudicating statistic.
**Probe** `scripts/probes/_miso127_overnight_gas_composition.py`; **record**
`results/calibration/_miso127_overnight_gas_composition.json`.

---

## 1. Headline

miso-114 §6 named a bounded NO-LP step and this session took it: the model keeps
~2 GW of `CT_PEAKER` + `ST_GAS` online at h1–3 while being short 3.4–3.9 GW of
gas overall against EIA-930 — **does MISO's own metered record run that much
overnight?** The reading under test was that the model holds *expensive* gas
online overnight that the market does not, which would make the model's
overnight marginal machine structurally wrong and explain miso-114's flat
**+$4 to +$8 level offset across net-load deciles 0–8**.

**Three results, in decreasing order of how much they matter.**

**(1) The reading is CONFIRMED IN ZERO YEARS by any construction available from
committed artifacts.** On the machines both sides can actually see, the model
runs **less** overnight gas than the market in **3 of 3** years — not more:
**−931.2 / −593.8 / −697.5 MW**. And it is short in **every** gas class
(`CC_REGULAR`, `CC_CHP`, `CT_PEAKER`, `CT_CHP`, `ST_GAS`), the single exception
being `ST_CHP` 2023 at +4.3 MW. A one-sided class bound (§4) puts the model
short at **class** grain in 2023 and leaves 2024/2025 unresolved. **Nothing
finds the model long.** miso-114's reading is falsified in the only direction
the data can resolve, and this finding does not re-frame it into a
confirmation.

**(2) The pre-registered adjudication P3 is UNAVAILABLE ON COVERAGE**, by the
pre-registration's own P2 rule. Against the correct denominator — the model's
**full** class — the matched machines carry only **0.845 / 0.865 / 0.823** of
`CT_PEAKER` and **0.605 / 0.611 / 0.629** of `ST_GAS`, against a pre-registered
0.90 bar. P2 says a class below the bar "is REPORTED but NOT gated — its Δ is
descriptive only and cannot carry P3", so P3's verdict is not read and KILL-2 /
KILL-3 do not fire as written. Result (1) rests on the matched-machine
comparison and the one-sided bound, both of which survive the coverage failure
because they never require the unmatched machines.

**(3) The coverage failure is itself the session's most useful output, and it
was not previously on the record.** The model's `ST_GAS` class carries
**8.33 / 8.28 / 7.53 TWh/yr — 37–39 % of its own class energy — on machines
with no committed bench counterpart at all**, and `CT_PEAKER` carries
2.16 / 2.49 / 3.09 TWh (14–18 %), against `COAL_PRB` at 96–98 % matched and
`CC_REGULAR` at 93–95 %. **This is what actually blocks the measurement
miso-114 asked for**: no class-grain statement about MISO's overnight gas is
determinable while a third of the steam-gas class has no measured counterpart.
It is handed off as an OBSERVATION under rule 25 `[R-ISO-SCOPE]`, **not
chartered here** (PREREG KILL-4/KILL-5).

---

## 2. Construction, and why it is trustworthy

Matched-plant, committed artifacts only. Measured side is the dashboard's own
committed class actual (`frontend/data/backcast/bench/MISO/<year>.json.gz`,
per-plant `campd`) — never a hand-built roster summed out of raw CAMPD. Model
side is the **keeper's own** registered payload
(`frontend/data/backcast/runs/2026-08-04-miso-126-steampart-b.js`, per-plant
`m`), with the keeper bundle's `class_hourly_<year>.parquet` (P1) as the
independent full-class aggregate. Window: hour-of-day {1, 2, 3}, miso-114's
"h1–3".

Matching is the point: MISO's sub-25-MW peakers are below the CEMS reporting
threshold, so an unmatched comparison reads the model long **by construction**.
Only keys present on both sides are compared.

**All three protective properties pass.**

| control | 2023 | 2024 | 2025 | bar |
|---|---|---|---|---|
| **P1** `COAL_PRB` hour-of-day r (phase alignment) | 0.9876 | 0.9776 | 0.9712 | ≥ 0.90 → **PASS 3/3** |
| **P5** gas-class arithmetic closure | 0.0585 MW | 0.1034 MW | 0.0403 MW | ≤ 1 MW → **PASS 3/3** |
| **P6** `uint8` quantization bound | 22.50 MW | 21.36 MW | 21.42 MW | reported — **~40× below the Δ** |

P1 is the load-bearing one: it reproduces the keeper's own 0.97–0.99
`COAL_PRB` `profile_r` on *this* construction, so the two 8760 indexes are
phase-aligned and the hour-of-day window means what it says.

**Independent model-side reproduction across two keepers.** miso-114 measured
1,907 / 2,415 / 2,350 MW of overnight `CT_PEAKER` + `ST_GAS` on the
`miso109b_hy_level_B` bundle. This session's full-class figure on the
`miso126_steampart_B` keeper is **1,677 / 2,262 / 2,082 MW** — same object,
different keeper, different construction, same magnitude. miso-114's model-side
number is confirmed; it is the *market* side that was never measured, and that
is what changes the conclusion.

---

## 3. The matched-machine result (P3 statistic, descriptive per P2)

Overnight (h1–3) mean MW, matched machines, model − measured:

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| `CC_REGULAR` | −757.3 | −245.3 | −582.2 |
| `CC_CHP` | −220.4 | −242.2 | −478.1 |
| `CT_PEAKER` | −508.6 | −172.1 | −249.5 |
| `CT_CHP` | −252.0 | −394.1 | −369.4 |
| `ST_GAS` | −422.6 | −421.7 | −448.0 |
| `ST_CHP` | +4.3 | −13.1 | −12.2 |
| **`CT_PEAKER` + `ST_GAS` (P3)** | **−931.2** | **−593.8** | **−697.5** |

Every gas class is short, in essentially every year. Whatever else is true, the
model is **not** holding gas online overnight that the market leaves off.

**P4's coherence test passes, in the direction that matters.** The
pre-registration required that a *long*-peaker result be accompanied by a
comparable *short*-CC result or be judged internally incoherent. The result is
short-everything, which is coherent with miso-114's independently measured
3.4–3.9 GW all-gas hole and its 2.6–3.7 GW of extra coal: the model's overnight
substitution runs **coal-for-gas**, the opposite direction from the hypothesis
under test.

---

## 4. The one-sided class bound — the only class-grain statement available

Measured-matched is a **lower bound** on the true measured class: every
unmatched machine can only *add* generation. So comparing it against the
model's **full** class is a valid one-sided test — if the measured floor
already exceeds the full model class, the model is short at class grain and no
amount of unmatched measured generation can reverse it.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model FULL class (`class_hourly`) | 1,677.4 MW | 2,261.8 MW | 2,081.6 MW |
| measured LOWER BOUND (matched) | 1,805.7 MW | 1,986.1 MW | 1,889.2 MW |
| gap | **+128.3** | −275.7 | −192.4 |
| verdict | **model SHORT at class grain** | UNRESOLVED (long by ≤ 276) | UNRESOLVED (long by ≤ 192) |

The bound resolves the direction in **one** of three years, and in that year it
says **short**. In 2024 and 2025 the direction is genuinely undetermined and is
reported as undetermined — the unmatched third of `ST_GAS` is larger than the
gap, so the data cannot close it. **That is the honest ceiling on what this
measurement can say at class grain**, and it is why result (3) is the
prerequisite for anyone who wants more.

---

## 5. Post-hoc descriptive (D): the shortfall is a LEVEL defect, not an overnight one

Not pre-registered; carries no verdict; gates nothing. Added because the P3
result immediately raises the question, and the answer changes what a successor
could even be.

Matched machines, model − measured:

| class | year | annual model / measured (TWh) | Δ annual | Δ night (h1–3) | Δ peak (h16–19) |
|---|---|---|---|---|---|
| `CT_PEAKER` | 2023 | 11.771 / 17.952 | −6.181 | −508.6 MW | −750.8 MW |
| | 2024 | 15.978 / 18.156 | −2.178 | −172.1 MW | −204.7 MW |
| | 2025 | 14.412 / 18.662 | −4.250 | −249.5 MW | −574.5 MW |
| `ST_GAS` | 2023 | 12.763 / 15.497 | −2.734 | −422.6 MW | −175.2 MW |
| | 2024 | 13.011 / 16.811 | −3.800 | −421.7 MW | −447.7 MW |
| | 2025 | 12.762 / 15.551 | −2.789 | −448.0 MW | −233.7 MW |

Both classes are short **annually** and short at **both** ends of the day —
`CT_PEAKER` more so at peak than overnight in all three years. **This is a
level defect on those machines, not an overnight-specific shape defect.** A
whole-day shortfall cannot be the source of an *overnight-specific* price
residual, which is exactly what C7 `COAL_PRB` needs. So even setting the
coverage failure aside, this object does not reach the C7 target.

---

## 6. What this does to the queue, and what it does NOT do

**miso-114 §6's bounded NO-LP step is SPENT.** It returns a **falsification**,
not a lever. §5.4's C7 `COAL_PRB` residual is **NOT** redirected to an
overnight gas-composition object: the object was measured and does not exist in
the direction the reading required.

**No mechanism was tested, so no mechanism cell moves** (rule 28(b) is
satisfied by the queue stamp + this citation, not by a verdict — this session
adjudicated a *measurement question*, not a mechanism). **No successor is
chartered** — rule 19 `[R-ONE-MECH]` forbids manufacturing one, and PREREG
KILL-4 binds regardless of the result: **nothing may be sized on Δ**, which is
a residual (rules 13 / 21 / 24).

**The miso-121 DO-NOT-REDO is carried, not quietly dropped.** P3 measures
**online energy, not marginality**. Even had it come out material and long, it
would have established a composition fact and **not** a price effect. No
sentence in this finding reads it as a price result.

**§5.4's remaining bounded non-solve step is unchanged:** item 1's Form 580
tonnage count (a sourcing pass, not a solve).

---

## 7. Handed off, NOT chartered (rule 25 `[R-ISO-SCOPE]`)

**(a) The bench-coverage gap on MISO's gas classes.** Matched share of the
model's own class energy:

| class | 2023 | 2024 | 2025 | unmatched model energy |
|---|---|---|---|---|
| `COAL_PRB` | 0.960 | 0.968 | 0.975 | 3.7–5.0 TWh/yr |
| `CC_REGULAR` | 0.931 | 0.935 | 0.954 | 6.0–9.7 TWh/yr |
| `CT_PEAKER` | 0.845 | 0.865 | 0.823 | 2.2–3.1 TWh/yr |
| **`ST_GAS`** | **0.605** | **0.611** | **0.629** | **7.5–8.3 TWh/yr** |

`ST_GAS` is the outlier by a wide margin. **The cause is NOT determinable from
committed artifacts** and this session does not guess at it; the candidates are
sub-CEMS-threshold units (implausible on its own for machines of this size),
bench class assignment differing from the LP's, or model units with no bench
entry. Resolving it is a prerequisite to **any** class-grain statement about
MISO gas — including the one miso-114 asked for. It needs its own charter with
a control arm; note it touches the same artifact family as the cross-ISO
thermal-tranche staleness item already open, and must not be landed as a side
effect of either.

**(b) A construction fact future lanes need.** The dashboard payload's CHP
series carry the **whole-plant host-steam add-back**, so CHP coverage computes
to 1.45–1.78 (above 1) and the payload's CHP model series is **not** comparable
to `class_hourly`. The probe marks those classes uninterpretable rather than
reporting a coverage number that looks fine and is not. Any future matched-plant
construction must handle this or it will silently mis-state CHP.

---

## 8. Correction made in-session, recorded rather than buried

The probe's first implementation computed P2's coverage against the
**bench∩payload** subset instead of the model's full class, which made coverage
read ~1.000 for every class and would have let P3 be gated when it should not
be. It was caught by the model-side cross-check — matched `ST_GAS` came to
639 MW against `class_hourly`'s 1,365 MW, a 2× gap that a 1.000 coverage number
cannot explain — corrected to the pre-registration's stated §2 intent (coverage
**bias** control ⇒ the denominator is the model's own class), and re-run. The
corrected denominator is what produced result (2) and result (3); the earlier
reading is superseded and is recorded here so it is not re-derived by someone
reading only the JSON.

The verdict direction did not depend on the bug: the matched-machine Δ is
identical either way (the same machines are compared), and it is short in 3/3
years under both.

---

## 9. Reproduce

```
python scripts/probes/_miso127_overnight_gas_composition.py
```

No LP, no bundle, no network; reads only committed artifacts. Writes
`results/calibration/_miso127_overnight_gas_composition.json`.
