# FINDING — neiso-67 (STEP 2 of the freeze-lift lane): the COMMITMENT test is **not informative either**. The observed idle/run split does **not** track start-cost recovery — measured per unit, the metric is a coin flip (median AUC 0.47–0.57), it scores **below** the marginal test it was meant to replace in **every** configuration tried, and on the seam population its sign is **backwards**. The instrument is proven live by an internal positive control, so this is a property of the hypothesis, not of the probe (2026-07-26)

**Freeze status: STILL ACTIVE, and this finding does not lift it.** It closes
§6 step 2 with a negative result and makes step 3's disposition a decision the
owner can now take on measured evidence. **Only the owner lifts the freeze.**

Probe (committed, re-runnable, **no LP solve**):
`scripts/probes/_neiso67_startcost_recovery.py`.

Context: `FINDING-neiso66-overcount-rootcause-2026-07-26.md` §6 left three
ordered steps. Step 1 (re-measure NEISO on a sound instrument) is DONE and
PASSED (§5b). Step 2 is this:

> **Test the commitment-economics mechanism directly** — does the observed
> idle/run split track start-cost recovery over the expected run (start cost vs
> spread × expected run hours), per unit? §4 shows the marginal test is
> uninformative here; it does not yet show the commitment test is informative.

It is now measured. **It is not informative.**

---

## §1 — what was built, and why it is rule-13 clean

Per unit `u`, per day `d`, on measured inputs only — no LP solve, no LMP, no
cleared price, no cleared quantity, no dispatch outcome and no residual is an
INPUT anywhere:

* `SRMC_u(t) = HR_u × px(u, t)` — the charter D1 construction, reused verbatim
  from `scripts/lib/outage_detect.py` (CAMPD-measured heat rate × delivered fuel
  price).
* `RCC(t)` — the charter D1 revealed clearing cost, **recomputed leave-one-out
  for every unit under test**. The guard never needed this (it only ever asks
  about windows where the unit is off, contributing nothing to its own
  reference); this probe compares idle days against RUNNING days, and on a
  running day the unit sits in its own RCC panel, nudging the quantile in the
  direction that flatters the hypothesis. Removed rather than argued about.
  *Measured size of the correction: mean |Δ| 0.033–0.064 $/MWh against an RCC
  median of 20.8–43.9 $/MWh — ~0.15 %. Immaterial, and excluded anyway.*
* **start cost and minimum run** — the published NREL/SR-5500-55433 tables
  already in `config/constants.py`, selected by the unit's CAMPD-reported
  `unitType` (combined cycle / combustion turbine / boiler — a reported physical
  fact) and then by its **own measured heat rate**, which picks the class row
  (h-class / f-class / older). No class-name knob, no fitted scalar (rules
  17/20/24).
* **the expected run** — the maximum-sum contiguous block of at least
  `min_run_hours` inside a forward horizon of `max(24, min_run_hours)` hours
  (`DA_COMMITMENT_HORIZON_HOURS` = 24), by O(H) prefix-sum scan. The block the
  unit would actually pick, not a fixed window.
* `margin_d` = Σ (`RCC_loo` − `SRMC_u`) over that block, $/MW.
  **`R_d = margin_d / start_cost_u`** — the recovery ratio. `R ≥ 1`: the start
  pays for itself.

Scope, NEISO 2023 / 2024 / 2025: **89 / 84 / 83** identified units
(CC 61/14.4 GW, 61/14.2 GW, 57/12.7 GW; plus CT and gas steam),
**32,483 / 30,741 / 30,294** evaluable unit-days.

Three caveats bound the reading, and **all three point the same way — they can
only depress the measured power, so the null below is conservative**: the block
is picked with perfect foresight (an upper bound on what a day-ahead forecast
could carry); the margin is energy-only, while NEISO units also earn capacity,
ancillary and RMR revenue (every one of them a reason to start when `R < 1`);
and genuine mechanical outages are noise in the dependent variable (handled by
reporting an AVAILABLE population that drops every detector-booked day).

## §2 — the instrument is live: an internal positive control

Before any null is read, the machinery has to be shown to carry signal at all.
It does. `R` decomposes into two bands that mean different things, and the
**marginal band `R < 0`** — the best feasible block has *negative* energy
margin, i.e. the unit is out of merit across the horizon — tracks ISO-NE's
published available-but-not-committed series strongly and stably:

| RCC pctl / horizon | 2023 | 2024 | 2025 |
|---|---|---|---|
| p50 | +0.60 | +0.48 | +0.72 |
| p75 | +0.72 | +0.64 | +0.53 |
| **p90 (default)** | **+0.70** | **+0.79** | **+0.63** |
| p99 | +0.60 | +0.75 | +0.53 |
| horizon 48 h | +0.70 | +0.79 | +0.62 |
| horizon 72 h | +0.69 | +0.78 | +0.61 |

*(monthly r of that band's capacity vs `uncommitted_available_gen_nonfast_mw`;
against published OUTAGES the same band runs −0.27 to +0.41, mostly negative.)*

18 of 18 cells positive, most of them strong. The SRMC / RCC / best-block
machinery works and the seam population is findable with it. **Everything that
follows is therefore a property of the start-cost-recovery hypothesis, not of a
broken probe.**

## §3 — per unit, the commitment test is a coin flip — and never beats the marginal test

§6 step 2 asks the question **per unit**, which is also the only form immune to
cross-unit heterogeneity (units differ several-fold in start cost and heat rate,
which alone can dilute a pooled score). Each unit is scored against its OWN
start days and decline days, over AVAILABLE start-opportunity days — the unit
was off at the previous hour and carries no booked outage that day.

| year | units scored | median AUC `R` | median AUC marginal spread | units > 0.55 | units < 0.45 (anti-predictive) |
|---|---|---|---|---|---|
| 2023 | 40 / 5,462 MW | **0.502** | 0.502 | 11/40 | **15/40** |
| 2024 | 45 / 5,867 MW | **0.546** | 0.546 | 21/45 | 8/45 |
| 2025 | 50 / 6,766 MW | **0.530** | 0.528 | 20/50 | 11/50 |

0.502 is a coin flip. And the commitment metric matches the plain marginal
spread to within ±0.002 — it is not adding a dimension, it is re-expressing one.

Robustness — per-unit median AUC of `R`, with the marginal spread in
parentheses, across every lever that could plausibly be mis-set:

| config | 2023 | 2024 | 2025 |
|---|---|---|---|
| RCC p50 | 0.539 (0.547) | 0.537 (0.534) | 0.565 (0.563) |
| RCC p75 | 0.472 (0.495) | 0.571 (0.574) | 0.508 (0.530) |
| **RCC p90 (default)** | 0.502 (0.502) | 0.546 (0.546) | 0.530 (0.528) |
| RCC p99 | 0.476 (0.501) | 0.561 (0.542) | 0.493 (0.506) |
| horizon 48 h | 0.510 (0.513) | 0.540 (0.541) | 0.521 (0.521) |
| horizon 72 h | 0.509 (0.515) | 0.519 (0.519) | 0.514 (0.510) |

All 18 cells sit in 0.47–0.57, and in all 18 the marginal spread is within
±0.02. No reference-price level and no horizon rescues it.

**The start-cost division actively destroys information.** On the pooled
AVAILABLE population the bare margin outscores the recovery ratio in every year
— 0.599 → 0.573 (2023), 0.629 → 0.591 (2024), 0.615 → 0.599 (2025) — and the
plain marginal spread outscores both, in all 18 configuration-years tested.
Dividing by the published start cost makes the discriminator *worse*.

*(A sweep of a global multiplier on start cost is not reported because it is
arithmetically incapable of moving an AUC — a positive scalar is a monotone
transform of `R`. The lever that can matter is whether dividing by the
published, class-and-heat-rate-varying start cost beats not dividing, which is
the comparison above.)*

## §4 — on the seam population the sign is BACKWARDS

The sharp test: the §4 table of the neiso-66 finding, re-run with the commitment
metric. Booked-out unit-days that the merit guard KEEPS — §4's excess-carrying
population — against the SAME units' running days.

| year | booked-OUT days | median `R` | share `R ≥ 1` | RUNNING days | median `R` | share `R ≥ 1` | `R` gap | AUC `R` |
|---|---|---|---|---|---|---|---|---|
| 2023 | 6,905 | 4.15 | **89.2 %** | 9,373 | 3.37 | 80.8 % | **×0.81** | **0.405** |
| 2024 | 5,074 | 3.72 | **90.1 %** | 10,187 | 3.33 | 75.9 % | **×0.89** | **0.391** |
| 2025 | 3,011 | 6.57 | **93.1 %** | 9,997 | 5.93 | 85.2 % | **×0.90** | **0.405** |

Read it plainly: on **89–93 %** of the seam days, the best feasible committed run
**more than repays the published start cost** — and the unit stays off anyway,
for a median ~10 days. The idle days score *higher* recovery than the days the
same units chose to run, so the AUC lands **below 0.5**: as a predictor of
running, start-cost recovery is mildly anti-predictive here.

The marginal spread column reproduces neiso-66 §4 as expected (+0.09 / −0.06 /
+0.59 $/MWh, against §4's +0.47–0.82 measured on the hour grain at CAISO) — the
two instruments agree that the marginal test is flat. The commitment test does
not improve on it; it inverts.

## §5 — and the commitment band identifies nothing against the published series

The disposition question is narrower than the AUC: a detector discriminator
would not need to predict every start, only to isolate capacity that is
available-but-not-committed. So split the idle capacity into the three bands and
score each against ISO-NE's published columns. **Only the middle band is new
information** — `R < 0` is an out-of-merit condition the merit-order guard
already owns (rule 19 `[R-ONE-MECH]`), and `R ≥ 1` is the residual.

| band | 2023 MW / r(UNC) / r(OUT) | 2024 | 2025 |
|---|---|---|---|
| `R < 0` — marginal, the guard's own cut | 812 / **+0.70** / −0.14 | 1,114 / **+0.79** / −0.11 | 1,074 / **+0.63** / +0.32 |
| **`0 ≤ R < 1` — the COMMITMENT band** | 595 / **−0.51** / +0.55 | 689 / **+0.26** / +0.21 | 182 / **+0.05** / +0.34 |
| `R ≥ 1` — start repays, idle anyway | 6,514 / +0.47 / +0.35 | 5,689 / +0.44 / +0.39 | 4,468 / +0.60 / +0.59 |
| *reference*: no split, total idle | 7,910 / +0.48 / +0.38 | 7,364 / +0.59 / +0.31 | 5,661 / +0.61 / +0.57 |
| *reference*: placebo p95 (30 draws) | +0.42 | +0.60 | +0.60 |

The commitment band carries **−0.51 / +0.26 / +0.05** against the published
uncommitted series. It is not merely weak — in 2023 it is *wrong-signed*, and in
all three years it correlates **better with published OUTAGES than with
UNCOMMITTED** (+0.55 / +0.21 / +0.34), which is the opposite of what the
hypothesis predicts. Across the full sensitivity sweep the band's correlation
wanders between −0.51 and +0.57 with no stable sign. It is also small: 182–689
MW against a residual over-count of 1,660 / 1,199 / −330 MW (neiso-66 §5b).

Compare the standard the charter's D1 positive control met on the same
instrument — vetoed windows +0.77 / +0.71 / +0.67 vs UNCOMMITTED with kept
windows at +0.08 / +0.28 / +0.31, a clean sign-stable separation in all three
years. Nothing resembling that appears here.

The headline `R < 1` split (+0.32 / +0.60 / +0.60) does not clear its placebo
p95 (+0.42 / +0.60 / +0.60) in any year, and does not beat simply not splitting
at all (+0.48 / +0.59 / +0.61). A deliberately over-optimistic best-of-19
threshold sweep reaches +0.78 / +0.81 / +0.64 — but it selects a **negative**
cut (`R < −0.30`, `R < −0.11`, `R < 0.10`), i.e. it converges on the guard's own
marginal condition rather than on any commitment condition.

## §6 — what this means for STEP 3 (disposition)

The measured answer to §6 step 2 is **no**: the observed idle/run split does not
track start-cost recovery, per unit or in aggregate, at any reference-price
level or horizon tested. The seam is real and confirmed (neiso-66 §5b); what
this finding adds is that **it is not recoverable by a commitment-economics
discriminator built from rule-13-admissible inputs.**

That collapses step 3's two options to one, and the recommendation is
**disposition (b): leave the availability envelope alone and CARRY THE SEAM
EXPLICITLY.**

* Option (a) — a commitment-aware second discriminator in the detector — is
  **not buildable on the evidence**. Its only novel band is `0 ≤ R < 1`, which
  identifies nothing (§5), and rule 19 `[R-ONE-MECH]` forbids stacking it on the
  merit-order guard that already owns the `R < 0` half. Adding it would be a
  mechanism with no measured discriminating power — precisely what rule 1
  `[R-STRUCT]` forbids reaching for.
* Option (b) carries no new free parameter, keeps the guard exactly as the
  charter §8 verdict adopted it, and records the seam where it belongs: as a
  known, quantified, *definitional* difference between what CNOG/ISO-NE publish
  and what a CEMS detector can measure — not as an open root-cause item.

**Two things this finding does NOT settle, and does not attempt to.**

1. **Whether the seam should be closed at all.** neiso-66 §5b argues on
   structural grounds (rule 1) that these units belong in the envelope as
   *available*, with the LP declining them on its own commitment economics.
   Nothing here contradicts that — it says only that the *detector* cannot
   identify which units those are. Whether the LP's own commitment layer
   reproduces the population is a different question on a different instrument,
   and CAISO's `caiso_ra_mustoffer` already owns that capacity's commitment
   (rule 19: replace or reconcile, never stack).
2. **A live observation for the owner, flagged not proposed.** The day-grain
   best-block `R < 0` cut tracks published UNCOMMITTED at +0.63 to +0.79, where
   the guard's own window-grain out-of-merit share reaches +0.08 to +0.31 (D1
   table, KEPT windows). That is a **marginal**-test refinement, in the guard's
   existing lane — a possible *replacement* for its window-grain cut, never an
   addition. It is out of scope for this charter, it has not been validated
   cross-ISO, and it must not be adopted on this finding alone.

Nothing here changes a keeper, an extract, a default, or the guard. No LP solve
was run. No out-of-training year was touched.
