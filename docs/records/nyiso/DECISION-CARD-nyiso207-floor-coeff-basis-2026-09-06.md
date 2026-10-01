# DECISION CARD — nyiso-207: every live NYISO floor coefficient is a percentile of **daily** aggregates applied **hourly**. Is nyiso-203 §6 one coefficient to rule on, or a construction?

**For:** the owner, and the governance / cross-ISO lane. **From:** session nyiso-207, NYISO
`backcast-calibration` lane, 2026-09-06.
**Zero solve. Nothing armed, nothing re-scored, no `src/market_sim/` change, no derive-script
change, no coefficient edit, no CSV edit, no scorer edit, no marker touched.**

**This card does not replace `DECISION-CARD-nyiso203`'s question — it SCOPES it.** nyiso-203 §8
point 3 held that its NYC gap *"needs a ruling, not another measurement"*, and it was right that no
further measurement of **that limb** would help. What was missing was whether the owner is being
asked to rule on **one coefficient or on a construction**. **It is a construction**, and the
evidence is below.

**Evidence:** `docs/FINDING-nyiso207-floor-coeff-basis-census-2026-09-06.md`;
machine records `results/calibration/_nyiso207_floor_coeff_basis_census.json` and
`_nyiso207_ct_denominator_check.json`;
pre-registration `results/calibration/PREREG-nyiso207-floor-coeff-basis-census.md` (+ addendum §A).
**Keeper, unchanged:** `2026-09-06-nyiso-202-startup-aware` (CALIBRATED, fails 0).

> **Read this first.** The session's own **pre-registered class verdict FAILED** (§3). The positive
> result below is a *different and weaker* claim than the one it pre-registered, and it is labelled
> as such throughout. **Nothing in this card is a proposal to change a coefficient.** The lane's
> reading is that **Option A is right, and Option B is the one thing this card cannot supply.**

---

## 1. The defect

Both NYISO floor derive scripts identify their coefficients as a **percentile over a population of
DAILY aggregates**:

```python
# derive_nyiso_st_reliability_floor.py
all_day = g.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
base24  = float(cool24["cf"].quantile(0.25))   # p25 of DAILY MEANS
cap     = float(P["cf"].quantile(0.97))        # p97 of DAILY MEANS
# derive_nyiso_ct_reliability_floor.py
daily = ev.groupby("date")["grossLoad"].sum() / (nameplate * len(EVENING_HOURS))
```

The model applies them **per hour**: `frac × pmax × availability[t]`
(`model/interchange/core.py::_apply_frac`). **A percentile of daily means is not the percentile of
the hourly population it is applied to.**

Measured on all ten live knots, from source, pooled 2023–2025, using the **shipped** derive-script
functions. `M1` re-derives the frozen value (hard gate, 0.002 absolute — a limb that fails it gets
**no** gap, so a pipeline difference can never be reported as a basis difference); `M2` is the same
percentile on the hourly population, one change only:

| limb | frozen | M1 | gate | M2 | **gap %** | band % | CV |
|---|---:|---:|:---:|---:|---:|---:|---:|
| NYC ST `base_ev` | 0.1850 | 0.1849 | ✓ | 0.1819 | **−1.62** | 0.89 | 0.1173 |
| NYC ST `base_24h` *(nyiso-203's limb)* | 0.1750 | 0.1749 | ✓ | 0.1663 | **−4.89** | 1.97 | 0.1658 |
| LI ST `base_ev` | 0.3500 | 0.3502 | ✓ | 0.3258 | **−6.97** | 3.37 | 0.2199 |
| **DS CT `base` — carried by TWO live limbs** | 0.1320 | 0.1316 | ✓ | 0.1140 | **−13.35** | 5.54 | 0.3162 |
| LI ST `base_24h` *(nyiso-140's limb)* | 0.2620 | 0.2623 | ✓ | 0.2011 | **−23.34** | 14.60 | 0.3920 |
| LI ST `cap` | 0.8820 | 0.8815 | ✓ | 0.9140 | **+3.68** | 1.39 | 0.1804 |
| DS CT `cap` | 0.6790 | 0.6789 | ✓ | 0.7056 | **+3.93** | 0.72 | 0.2916 |
| CH ST `base_ev` | 0.0000 | 0.0000 | ✓ | 0.0000 | *inert at zero* | 0.00 | 0.0858 |
| NYC ST `cap` | 1.0000 | 1.0358 | **✗** | — | *inert — clamp at the physical bound* | — | 0.1275 |
| CH ST `cap` | 0.3200 | 0.8701 | **✗** | — | *different construction — see §5* | — | 0.0809 |

**Two findings, both pre-registered before the numbers:**

1. **SIGN — 7 of 7.** Every base knot gaps **negative**, every cap knot **positive**, exactly as the
   mechanism requires (a percentile of a *less dispersed* population sits above the hourly p25 and
   below the hourly p97). One dissenter would have refuted it. There is none.
2. **MAGNITUDE — one variable explains it.** Rank the base knots by **within-window dispersion**
   (median across days of the within-window CV of hourly CF) and |gap| rises **strictly monotonically,
   5 of 5**, over a 14× range, across two derive scripts, two plant classes, three zones and two
   window widths: 1.62 % @ CV 0.117 → 4.89 → 6.97 → 13.35 → **23.34 % @ CV 0.392**.
   *(The split-by-statistic view is **POST-HOC** and labelled so in the finding §4.4; the pooled
   version this session actually pre-registered was internally inconsistent with its own sign
   prediction and is scored **REFUTED**.)*

**So nyiso-203 §6's NYC gap is not a property of the NYC limb.** It is one draw from a construction
whose bias is systematic in direction and predictable in size.

## 2. Why it is the owner's ruling, not a lane fix

- **Rule 23 `[R-FROZEN-DERIVE]` has no trigger.** No source data has updated. nyiso-140's
  re-derivation cited one (the `6a8f285` guard fix); this has nothing to cite.
- **It would MOVE live coefficients**, where nyiso-140's correction did not. That correction was
  accepted as **zero-DOF precisely because `floor_pct` was unchanged** (0.2666 vs 0.2620). Whether a
  construction repair is itself an adequate identification under rule 21 `[R-DOF]` is an owner call
  — nyiso-203 §7 reason 2 held exactly this, and this session does not disturb it.
- **The instrument is two derive scripts with per-ISO siblings**, and `_apply_frac` is shared. Their
  exposure is **unmeasured, and this lane may not measure it** (rule 25 `[R-ISO-SCOPE]`) — the same
  refusal nyiso-206 §5 made for the shared fill kernel.
- **NYISO reads `fails 0`.** Taking an untriggered move on live floors in a model with no structural
  problem to solve is the shape rule 1 `[R-STRUCT]` exists to refuse — which is why this session
  never opened a metrics file, a price series or a volume residual.

## 3. The size, and the verdict that failed — stated before the options

**The session's pre-registered class verdict is NOT MET.** PREREG §6 required **≥ 2 in-scope** limbs
at **|gap| ≥ 5 %**; of the three in-scope limbs that cleared M1, **exactly one** is. On the
pre-registered terms the **evening knots are a CLEAN NEGATIVE**, and that stands. The §1 findings are
a *different, weaker* claim — about **sign and predictability**, not about magnitude on the live
evening limbs.

**And the prediction that cut against this session was confirmed.** PREREG §5 item 2 declared, before
measuring, that evening knots aggregate over 8 h and so should gap **much less** than 24 h knots, with
the explicit commitment that a small evening gap *"will not be spun as a class-wide defect."*
Measured: NYC −1.62 % vs −4.89 % (3.0×), LI −6.97 % vs −23.34 % (3.3×).

**What a repair would actually move**, one knot at a time, under the model's own max-composition of
the 24 h base with the evening ramp, pooled 2023–2025:

| zone | added TWh, frozen | base knot basis-matched | Δ |
|---|---:|---:|---:|
| Long_Island | 1.31762 | 1.24965 | **−0.06797 (−5.2 %)** |
| NYC | 1.04953 | 1.03215 | **−0.01738 (−1.7 %)** |
| Capital_Hudson | 0.03035 | 0.03035 | **0.00000** |

Reachability agrees: the measured band covers **0.89–3.37 %** of the in-scope limbs' hours. **The
size sits in the two `base_24h` limbs already before you** — nyiso-203 sized NYC's at −0.133 TWh, and
Long_Island's band alone covers **14.60 %** of its hours.

## 4. Options, each with its measured cost

### Option A — **change nothing; correct the DOCUMENTATION to the aggregate-basis reading**

State in both derive scripts, and in the CSV `threshold_basis` prose, that each coefficient is a
percentile of a **daily-aggregate** population and is applied hourly, with the measured direction and
size of the resulting bias recorded.

- **Solve impact: zero.** Byte-identical for every ISO, every keeper, every year.
- **DOF: zero.** No parameter moves.
- **Cost:** the model keeps floors whose identification basis differs from their application basis by
  −1.6 % to −23.3 %. **Option A does not close that** — it stops the codebase asserting a basis it
  does not use.
- **Defensible on:** §3 — on the live evening limbs the effect is small and its reachability smaller;
  and the two large limbs' cases are already documented and, for Long_Island, already adjudicated as
  a membership question at zero DOF.

### Option B — **Option A, plus a program-wide measurement before any repair** *(the lane's recommendation, and the one fact this card cannot supply)*

Run this census on the other five ISOs' floor coefficients (source data only, **zero LP**, ~minutes
per ISO) so the exposure is known before anyone repairs a construction that six ISOs share.

- **Buys:** whether NYISO is an outlier or the norm. `DECISION-CARD-nyiso193` §5.1 is the cautionary
  precedent — two ISOs measured, **both** breached, and the "NYISO peculiarity" reading did not
  survive contact.
- **This lane cannot run it** (rule 25 `[R-ISO-SCOPE]`). It is a cross-ISO tasking. *(It is the same
  Option B that `DECISION-CARD-nyiso206` asks for on the shared fill kernel, on the same grounds and
  for the same reason — the two could be tasked together.)*

### Option C — **repair the construction: identify each coefficient on the hourly population it is applied to**

The one-change repair, with **zero new free parameters** (no value is invented; each coefficient is
re-derived on the population it is already applied to).

- **Measured effect on NYISO:** every base knot falls, every cap knot rises, by the §1 table; forced
  energy falls **−0.068 TWh** on the largest live evening limb and **−0.133 TWh** on NYC's `base_24h`
  (nyiso-203's sizing).
- **Cost 1 — rule 23 has no trigger** (§2). This is the binding objection, and it is not one this
  lane can discharge.
- **Cost 2 — it moves live coefficients on a CALIBRATED ISO**, so it is a mechanism change owing its
  own PREREG, rule-29 screen and full span — none of which this session has or should have.
- **Cost 3 — it would land on a construction six ISOs share**, unmeasured (Option B).
- **Not proposed, and no value is put forward for any coefficient.** The measured basis-matched
  numbers in §1 are reported as *measurements of the gap*, **not** as replacement values.

### Option D — **repair Long_Island's `base_24h` alone** (the single largest gap, −23.3 %)

Reported for completeness and **argued against**: that limb's coefficient is the one nyiso-140
deliberately left at 0.2620 because **two basis errors cancel there** — a daily-mean statistic applied
hourly (which inflates it) against a fleet aggregate including a laid-up plant (which deflated it) —
and the membership half is already fixed. Repairing the time half **alone**, on the post-exclusion
membership, is what nyiso-140 measured as 0.2666 — i.e. **essentially no move at all**. Singling out
this limb would change the least while looking like the most.

## 5. Two live limbs whose frozen values this census could not reproduce — reported, not diagnosed

Both failed the M1 gate, so **no gap is claimed for either**, and neither is a finding of this session:

- **NYC ST `cap` (frozen 1.0000, p97 basis 1.0358).** **Not a defect** — the CSV's own prose says
  *"clamped at the 1.0 physical bound … measured p97 avail-CF **1.036** exceeds it"*, and the probe
  reproduces 1.036. A floor already clamped at 1.0 cannot be raised by a basis move: **inert**.
- **CH ST `cap` (frozen 0.3200, p97 basis 0.8701).** Its prose names a **different** construction —
  *"legacy CH slope 0.0246/C hot-limb to clamp @38C; measured hot-day CF **regression**"* — which
  this census does not evaluate, so the divergence is **not attributable to the time basis**. It is an
  unexplained legacy value on a live limb, **named here for the owner and not diagnosed**, because
  diagnosing it is a different object with its own PREREG.

## 6. What the lane recommends, and what it refuses to do

**Recommends Option A now, and Option B before anyone takes Option C.** Option C is measured and
coherent but has no rule-23 trigger and would land on a six-ISO construction whose exposure is
unknown. Option D changes the least while appearing to change the most.

**Refused, and named so silence is not read as absence:** this session **edited no coefficient**,
**proposed no replacement value**, **changed no derive script**, **re-tested nothing** marked
`R`/`I`/`G`, and **measured no other ISO**. It did not touch the `offer_curve_by_group` channel
(owner court, carve-out condition (c)). NYISO's keeper is unchanged and its markers are untouched
(`complete` WITHDRAWN under Q5; `frontier` withdrawn on the determination limb; C-19 / Q51 PARKED).
`DECISION-CARD-nyiso193` and `DECISION-CARD-nyiso206` both stay **UNRULED**.

## 7. What a ruling would need to say

1. **Is a floor coefficient's identification basis required to match its application basis?** Option A
   settles the documentation either way; only a "yes" implies Option C.
2. **If yes — does a construction repair with zero new free parameters clear rule 23
   `[R-FROZEN-DERIVE]` without a source-data trigger, and rule 21 `[R-DOF]` on identification?** This
   is the same question nyiso-203 §7 reason 2 raised and it is still the binding one.
3. **Should Option B run first?** Six ISOs share the construction; the nyiso-193 precedent says "one
   ISO's peculiarity" is the reading most likely to be wrong.
4. **Nothing here is urgent.** NYISO reads `fails 0`; the live evening limbs' effect is ≤ 5.2 % of one
   limb's forced energy; and no gate, criterion or determination moves either way.

---

*(nyiso-207, 2026-09-06. Zero LP. The card carries the measurement — including the verdict that
failed; the ruling is the owner's.)*
