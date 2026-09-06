# DECISION CARD — nyiso-206: `floor_pct`'s two factors are not separately identified in delivery. What should the reliability floor's per-row cap be?

**For:** the owner, and the governance / cross-ISO lane. **From:** session nyiso-206, NYISO
`backcast-calibration` lane, 2026-09-06.
**Zero solve. Nothing armed, nothing re-scored, no `src/market_sim/` change, no coefficient edit,
no scorer edit, no marker touched.** The NYISO lane may not change
`model/interchange/core.py::_distribute_group_floor` — it is the shared kernel behind **37 of 50**
live reliability-floor limbs across **five other ISOs** (rule 25 `[R-ISO-SCOPE]`), the same shape
as `DECISION-CARD-nyiso193`'s `legitimacy_diagnostics.py`. **This card carries the measurement and
asks for the ruling.**

**Evidence:** `docs/FINDING-nyiso206-ch-fill-level-basis-2026-09-06.md`;
machine record `results/calibration/_nyiso206_ch_fill_level_basis.json`;
pre-registration `results/calibration/PREREG-nyiso206-ch-fill-level-basis.md` (+ addenda §A/§B).
**Keeper, unchanged:** `2026-09-06-nyiso-202-startup-aware`.

> **Read this first.** The measurement below establishes a real defect **and refutes the only
> zero-parameter repair for it.** Nothing in this card is a proposal. The lane's own reading is
> that **Option A is right and Option C is refuted by its own numbers** — and the numbers that
> refute C are in §3, not in a footnote.

---

## 1. The defect

`floor_pct = commit_frac × min_stable_pct` is documented by the script that derives it
(`scripts/data/derive_reliability_coeffs.py`) as a **per-unit physics statement with a commitment
count on top**: `min_stable_pct` is *"the class's physical min-stable level (Pmin/Pmax) of a
**committed unit** … once committed it sits at this physical Pmin"* (ST_GAS **0.12**, WWSIS-2
Table 7); `commit_frac` is *"the share of the class's nameplate that is online on
temperature-flagged days — **a commitment count**"* (**0.8105**).

The delivery mechanism caps each row's fill at its **full available capacity**, not at its
min-stable level:

```python
take = np.minimum(remaining, cap_r)      # cap_r = pmax[r] * availability[r, :]
```

Measured on the Capital_Hudson `ST_GAS` `tmax 31.1` limb's own binding window (504 / 432 / 600 h),
on the keeper's own reconstructed fleet, with the shipped kernel — intensity `i = floor / cap_r`
over every raised (row, hour) cell:

| year | `i` mean (MW-weighted) | **× min-stable 0.12** | `i` max | forced energy **above** min-stable | forced energy **pinned** at `i ≥ 0.999` |
|---|---:|---:|---:|---:|---:|
| 2023 | 0.8710 | **7.26×** | **1.0000** | **100.0 %** | 74.3 % |
| 2024 | 0.8947 | **7.46×** | **1.0000** | **100.0 %** | 14.1 % |
| 2025 | 0.9579 | **7.98×** | **1.0000** | **98.5 %** | 81.9 % |

The aggregate is delivered **exactly** (max hourly gap **0.0 MW** in all three years), and the
result survives all three pre-registered hour cuts. In 2025, Bowline's cheapest tranche is pinned
at `i = 1.0000` in **504 of 600** binding hours — a must-run at full output, not a minimum-stable
commitment.

**So the product is honoured and the factorisation is not.** `floor_pct`'s two factors are **not
separately identified in delivery — only their product is.**

## 2. Why it is the owner's ruling, not a lane fix

- The instrument is **one kernel shared by six ISOs.** nyiso-205's committed provenance census
  counts `cheapest_first` as the operator of **37 of 50** live floor limbs program-wide (ERCOT 5/5,
  MISO 12/12, NEISO 6/6, PJM 14/14 — all by dataclass default). Changing its per-row cap moves
  every one of them at once. **Their exposure is UNMEASURED and this lane may not measure it**
  (rule 25).
- Any change to a live keeper limb's delivered floor is a mechanism change on a **calibrated**
  ISO, requiring its own PREREG, rule-29 screen and full span — none of which this session has or
  should have, since it produced no arm.
- The competing readings of `min_stable_pct` are a **methodology-spec** question (what does the
  reliability floor assert?), not a calibration question, and the spec is owner-governed.

## 3. Options, each with its measured cost

### Option A — **change nothing in the mechanism; correct the DOCUMENTATION to the aggregate-only reading**

State in `derive_reliability_coeffs.py` and in the CSV's `threshold_basis` prose that `floor_pct`
is an **aggregate class-commitment share**, and that `commit_frac`/`min_stable_pct` identify its
*magnitude* rather than a per-unit loading rule.

- **Solve impact: zero.** Byte-identical for every ISO, every keeper, every year.
- **DOF: zero.** No parameter moves.
- **Cost:** the model keeps a delivery whose per-row intensity is 7.3–8.0× the physical minimum
  stable level named in its own derivation. That is a real gap and Option A **does not close it** —
  it stops the codebase asserting something its mechanism does not do.
- **What it is defensible on:** §4 — the metered conduct supports concentration, and every
  alternative measured so far is worse on rule 17 `[R-FLOOR-WINDOW]`.

### Option B — **Option A, plus a program-wide measurement before any mechanism change**

Run this session's intensity probe on the other five ISOs' `cheapest_first` limbs (one
`fleet_only` reconstruction per ISO-year, **zero LP**) so the size of the exposure is known before
anyone rules on the kernel.

- **Cost:** ~5 ISO-lanes × a few minutes each of reconstruction; no solve.
- **Buys:** the one fact this card cannot supply — whether NYISO's Capital_Hudson is an outlier or
  the program-wide norm. `DECISION-CARD-nyiso193` §5.1 is the cautionary precedent: two ISOs
  measured, **both** breached, and the "NYISO peculiarity" reading did not survive contact.
- **This lane cannot run it** (rule 25). It is a cross-ISO tasking.

### Option C — **cap the fill at `min_stable_pct × cap_r`** — *measured, and REFUTED*

The construction the coefficient literally describes: commit units in merit order, each at its
physical minimum stable level, until the zonal target is met. **Zero free parameters** (0.12 is
already in the CSV and is already a factor of the coefficient being delivered), **always feasible**
(`0.0973 < 0.12`), and its committed share is `floor_pct / min_stable_pct = commit_frac` in closed
form. It behaves exactly as predicted: target met to 1e-14 MW, `i` capped at exactly 0.1200, zero
energy at the pin.

**It is refuted by the meters, on the same test that refuted `pro_rata` one session ago**
(nyiso-205 §3.2, rule 17 `[R-FLOOR-WINDOW]`):

| year | plant | shipped fill | **Option C** | metered P(on) on those hours | *(refuted `pro_rata`)* |
|---|---|---:|---:|---:|---:|
| 2023 | **2480 Danskammer** | 192 h | **504 h (100 %)** | **0.125** | *504 (100 %)* |
| 2024 | **2480** | 24 h | **432 h (100 %)** | **0.255** | *432 (100 %)* |
| 2025 | **2480** | 0 h | **600 h (100 %)** | **0.370** | *600 (100 %)* |

**It is the same table, hour for hour.** Option C floors a plant in **every** binding hour of
**every** year while its own meter reads zero in 63–88 % of them, and manufactures **1.54×** the
energy (0.03595 vs 0.02332 TWh; per year 1.79× / 0.91× / 4.13×) — against `pro_rata`'s 1.64×.

**Option C inherits `pro_rata`'s refutation entire. The lane does not recommend it.** This test was
added **post-hoc and declared as such** (PREREG addendum §B), specifically because §3.1 of the
finding made Option C look attractive.

### Option D — **lower `floor_pct`** (the instrument the nyiso-206 charter named)

- **Rule 23 `[R-FROZEN-DERIVE]` has no trigger**: no source data has updated, and none was
  consulted for a level here.
- **And the measurement RE-SPECIFIES the question**: lowering `floor_pct` rescales the *aggregate*
  and leaves the *intensity ratio* essentially untouched — the fill simply pins fewer row-hours at
  the same ceiling. **The level is not the instrument for this gap.**
- Reported for completeness; **no value is proposed, and none was computed.**

## 4. The finding under the finding — why the shipped mechanism is defensible anyway

The coefficient's two factors describe a fleet the meters do not show:

- `commit_frac = 0.8105` asserts **many** units commit, at **minimum**.
- nyiso-205 measured, **9 of 9** year × cut cells unanimous, that Capital_Hudson steam's hot-day
  commitment is **concentrated by heat rate** — the cheapest plant above its availability share
  (g/a 1.19–2.01), both dearer plants below (0.15–0.99).

**Few units running hard, not many running at minimum.** Any fill honouring the min-stable half
must commit ~81 % of available capacity and therefore reach the bottom of the merit stack in
**every** binding hour — which is precisely what Option C's numbers are. `cheapest_first` honours
the **product** (exactly) and the **metered concentration**, and pays for it by discarding the
per-unit reading of `min_stable_pct`.

**That is the trade the owner is being asked to rule on**, and it is a genuine one: the mechanism
is wrong about *what a floor is*, and right about *what this fleet does*.

## 5. What the lane recommends, and what it refuses to do

**Recommends Option A, and Option B before anyone rules on the kernel.** Option C is refuted on
this ISO's own meters; Option D has no rule-23 trigger and does not reach the defect.

**Refused, and named so silence is not read as absence:** this session wrote **no patch** to the
shared kernel, **proposed no value** for `floor_pct`, **re-tested nothing** marked `R`/`I`/`G`, and
**measured no other ISO**. NYISO's keeper is unchanged, its markers are untouched
(`complete` WITHDRAWN under Q5; `frontier` withdrawn on the determination limb; C-19 / Q51 PARKED),
and `DECISION-CARD-nyiso193` stays **UNRULED** — though §1's pinning is a direct mechanical
explanation for the unit-grain `ST_GAS` C8 exposure that card measures (0.351 / 0.343 / 0.268
against the 0.30 cap), and the two are naturally ruled together.

**A related, still-unruled construction gap on a neighbouring limb**, presentable with this one:
nyiso-203 §6 — the NYC persistent-base limb's coefficient is identified on **daily means** and
applied **hourly** (0.1750 vs a basis-matched 0.1663, **−5.0 %**), sized, reported, and not taken
for want of a rule-23 trigger. Same class of defect; this one is ~150× larger in relative terms.

## 6. What a ruling would need to say

1. **Is `floor_pct` an aggregate class-commitment share, or a per-unit loading rule?** (Option A
   settles the documentation either way; only a "per-unit" answer implies a mechanism change.)
2. **If per-unit: what is the per-row cap, given Option C is refuted?** No candidate is currently
   measured that is better than the shipped fill on rule 17.
3. **Should Option B run first?** The five other ISOs' exposure is unmeasured, and the nyiso-193
   precedent says "one ISO's peculiarity" is the reading most likely to be wrong.

---

*(nyiso-206, 2026-09-06. Zero LP. The card carries the measurement; the ruling is the owner's.)*
