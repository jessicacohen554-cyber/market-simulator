# PREREG — nyiso-173: the CC availability over-statement, phase 0

**Session:** nyiso-173 · **Registered:** 2026-09-02 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves planned in phase 0: ZERO.**

Committed **with** `scripts/probes/nyiso173_cc_availability_anatomy.py` and
**before** either is run. Nothing below may be edited after the probe runs;
anything measured that is not registered here is reported **in addition to**
these gates, never in place of them (the nyiso-171 A5b / nyiso-172 S7–S10
discipline).

---

## 0. The object

nyiso-172 §3.4 established, with a **one-sided proof** rather than an
association: the measured CC fleet's maximum output **within a month** is a
strict lower bound on what that fleet could have produced that month, and the
model's CC exceeds it in **93 / 773 / 1,211 hours** (1.06 / 8.82 / 13.82 %) of
2023 / 2024 / 2025, at a CC mean gap of **+224 / +495 / +636 MW**, while
matching the measured CC **peak** to 0.99–1.03×. The bound is conservative
twice over (CAMPD `grossLoad` is gross, `class_hourly` is delivered; a monthly
maximum is the loosest within-month bound), so the true over-statement is at
least this large.

nyiso-172 §3.4 also **names a cause and explicitly declines to establish it**:
`UNIT_OUTAGE_MIN_DAYS = 5` (`src/market_sim/data/outages.py:239`) makes
sub-5-day derates invisible to the armed overlay, and the companion
partial-plateau overlay is likewise a sustained-ceiling construction. **This
session tests that hypothesis.** It is phase 0 only: no parameter is touched
and no solve is run unless the gates below identify a grounded measured input.

## 1. Construction (frozen before running)

Identical to the nyiso-170 / 171 / 172 construction, unchanged:

| instrument | source |
|---|---|
| model hourly MW by class | keeper `hourly/class_hourly_<year>.parquet`, pass **P1** |
| measured hourly MW per unit | `data/raw/campd-unit-level/NY_<year>.parquet`, `grossLoad` |
| class construction | CAMPD `unitType` × EIA-860 CHP flag |
| armed overlay windows | `data/raw/campd-unit-outages-NYISO.csv` (≥ 5-day, the ARMED extract) |
| lay-up reclassifications | `data/raw/campd-unit-outages-layup-NYISO.csv` |
| what already forces CC | keeper `legitimacy_diagnostics.json`, D-2 rows |
| armed availability config | keeper `run_config.json`, `scenario_config` |
| actual price | `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` |
| clock | `STD_TZ = "Etc/GMT+5"` (fixed standard time; `America/New_York` raises on 2023-03-12 02:00) |

**CC** means `CC_CHP + CC_REGULAR`, exactly as nyiso-172 §3.4 computed it.

**Per-unit capability reference `cap_u`** is the unit's own **within-year
maximum** `grossLoad` — a *demonstrated* lower bound on its capability, the
same logic as the fleet bound itself. It is availability-INCLUSIVE, so a unit
derated all year measures a depressed `cap_u`; every shortfall statistic below
is therefore **conservative** (it understates unavailability). Declared here,
not discovered later.

**Detector thresholds are the code's own, read not chosen** (rule 23
`[R-FROZEN-DERIVE]`): `ST_GAS_CF_PEAK = 0.02` is the event-based off
threshold the CC/gas-steam detector itself uses, `ST_GAS_MIN_OUTAGE_HOURS =
120` its duration floor, and `_CEILING_FRAC = 0.65` the frozen plateau
detector's depressed-ceiling fraction. No threshold is tuned, and none is
swept.

**Rule 13 `[R-MEASURED]` compliance.** CAMPD enters only as *conduct
identification*. The within-month bound is a measured **outcome used as
evidence** and is never fed back as an input; nothing is pinned to observed
generation; no statistic is tuned to any residual.

**Rule 22 `[R-HOLDOUT]`.** Every year read is 2023, 2024 or 2025. NYISO's
`complete` marker was declared 2026-07-31 and **withdrawn 2026-08-30**, and
NYISO has never appeared in `final`. No out-of-training year is read, solved,
scored or registered, and **no marker is requested**.

## 2. The pre-registered gates

### P1 — is the hypothesised cause the real one?

Decompose the measured CC fleet's **shortfall from its own demonstrated
capability**, `Σ_u (cap_u − gen_u,t)`, restricted to the violation hours (model
CC > measured within-month max), into four mutually exclusive per-unit-hour
states:

| state | definition | overlay treatment |
|---|---|---|
| **A** | inside a detected ≥ 5-day window in `campd-unit-outages-NYISO.csv` | **VISIBLE — armed** |
| **B** | off (`gen_u < 0.02 × cap_u`) in a contiguous off episode **< 120 h**, not in A | **INVISIBLE** |
| **D** | inside a lay-up window in `campd-unit-outages-layup-NYISO.csv`, not in A or B | deliberately excluded (economic) |
| **C** | on (`gen_u ≥ 0.02 × cap_u`) and below `cap_u`, not in A/B/D | **INVISIBLE** |

States are assigned in the order A → B → D → C, so they partition the
shortfall exactly.

* **P1a PASS** iff share(B) + share(C) **> 0.50 in all three years** — i.e. the
  majority of the measured CC shortfall in the violation hours is invisible to
  the armed overlay. **FAIL** ⇒ the violation sits in shortfall the overlay
  should already carry, the §3.4 hypothesis is not the cause, and this is a
  **different lane** which the finding must say so plainly.
* **P1b PASS** iff, given P1a, **share(B) > share(C)** in all three years — the
  §3.4 named cause (the sub-5-day **full-stop** floor) is the dominant carrier.
  **FAIL** ⇒ the input gap is real but its carrier is **partial derates**, a
  *different named gap* from the one §3.4 named, and the finding must report
  the hypothesis as **partially** supported and name the actual carrier.

Reported alongside, not gated: the full duration histogram of measured CC off
episodes (< 24 h / 24–72 h / 72–120 h / ≥ 120 h) by count and by MW-h, and the
same for depressed-ceiling plateaus.

### P2 — availability or shape?

The +636 MW mean gap is a two-sided statistic (nyiso-172 §6). Shape/economics
predicts the model's excess CC sits where the measured fleet was *available but
not called*; availability predicts it survives conditioning. In **2025**:

* **P2 PASS (AVAILABILITY)** iff **all three** hold:
  1. mean gap > 0 in each of the **top three actual DA price deciles** (no
     rational unit is economically backed off at the top of the price
     distribution);
  2. mean gap > 0 in each of the **top three load deciles**;
  3. mean gap > 0 within **every** quintile of the measured CC fleet's own
     **online-unit count**.
* **FAIL** ⇒ report as **NOT SEPARATED**: the gap is shape-contaminated and the
  availability reading is not established. No lever may be proposed on it.

All three legs are reported for 2023 and 2024 too; the gate binds on 2025, the
failing year.

### P3 — per-plant, or a portfolio artifact?

nyiso-171 is the standing warning that a fleet-level bound can be a portfolio
statistic. The discriminator is the **additive per-plant bound**
`Σ_p M_p,m` (each plant's own within-month maximum, summed), which is ≥ the
fleet bound by construction, so exceeding it is a strictly stronger claim.

* **P3 PASS (PER-PLANT GROUNDED)** iff the model's CC exceeds `Σ_p M_p,m` in
  **≥ 1 % of hours in 2025** (≥ 88 h).
* **FAIL** ⇒ report the object as **PORTFOLIO-ONLY**, explicitly a weaker
  object than nyiso-172 §3.4 presented, with the coverage statistic
  `M_fleet,m / Σ_p M_p,m` quoted per month.

Reported alongside, not gated: the per-plant ranking of violation-hour
shortfall, and the **East River (2493) sensitivity** — the whole bound
recomputed with 2493 removed from the measured CC series (it is `CC_CHP` under
the shared CAMPD construction but `ST_CHP` in `thermal_tranches_NYISO.csv`;
nyiso-171 §5, nyiso-172 §5). Its presence **inflates** the measured CC series
and therefore **loosens** the bound, so removal can only raise the violation
count; the finding reports both.

### P4 — rule 19 `[R-ONE-MECH]` attribution (reported, not gated)

Complete enumeration, from committed artifacts only, of everything shaping CC
availability in the keeper today: the D-2 rows forcing `CC_REGULAR` / `CC_CHP`,
every availability-related `scenario_config` field and its value, and the
on-disk row count of every NYISO outage extract (so a channel that is armable
but **empty** is identified as provably inert rather than untested). Any change
this session or a successor proposes must **replace or reconcile** what this
enumerates, never stack on it.

## 3. Stop conditions

* **P1a FAIL** ⇒ stop. The named cause is refuted; report it as a different
  lane and propose nothing.
* **P2 FAIL** ⇒ stop on the lever. The object is not established as
  availability; the finding reports the bound (which stands on its own
  one-sided proof) and refuses to name an input.
* **P3 FAIL** ⇒ the object is reported at the weaker portfolio-only strength,
  and any proposal must be justified at that strength or not made.
* **Phase 2 is entered ONLY if P1a AND P2 AND P3 all pass**, and even then only
  as a **data-intake** lane (the `data-intake` skill + the schema/`clean_io`
  contract), never a parameter lane, with its own pre-registered arm
  (direction and size expected in C1 CC and ST_GAS volume, the D-1 diurnal
  profile, and C3a-2025), and with the rule 1 `[R-STRUCT]` / rule 14
  `[R-ACCURATE]` clauses stated explicitly: a structurally-correct measured
  input **stays in** if the residual does not move, and a **worse** backcast
  after swapping an estimate for real data is a discovered bug elsewhere, never
  a reason to revert the accurate input.

## 4. Refused ex ante (no measurement will be taken to justify these)

* **Any capacity or nameplate change.** The miss is **mid-distribution**, not
  at the peak (2025 p95 model 8,471 vs measured 7,918 MW; peak ratio 0.994), so
  a flat capacity haircut is the wrong instrument by construction. This
  includes `cc_winter_capability_basis`, which is additionally **refused at
  CAISO** (caiso-186) on an unresolved rule 19 `[R-ONE-MECH]` WEFOR
  double-count that is not NYISO's to resolve.
* **Any derate tuned so the model's CC lands under the measured bound.** The
  bound is a **diagnostic, not a target**; fitting to it is pinning the
  backcast to a measured outcome, which rule 13 `[R-MEASURED]` forbids.
* **Any C3c lever** (brief instruction; C3c is supporting-tier and auto-ledgers
  under rubric v3.3).
* **The twenty closed lines** carried into this session, including nyiso-172's
  two: the ST_GAS deficit as a price-conditional dropout, and
  `gas_st_startup_cost` as an ST_GAS volume lever.

## 5. What a PASS does and does not license

A full pass identifies a **named, measured input gap**. It does **not** license
arming anything in this session: any candidate input must additionally clear
the rule 13 admissibility test — *could this same quantity be produced for a
forward year from forward drivers, and would it respond to changed
conditions?* If it cannot, it is a default-**off** diagnostic probe at best,
and the finding says so rather than arming it.
