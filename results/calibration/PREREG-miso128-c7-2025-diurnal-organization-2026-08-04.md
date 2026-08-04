# PRE-REGISTRATION — miso-128: what MISO's 2025 C7 `COAL_PRB` failure actually is, and whether any lever remains

**Date:** 2026-08-04 · **ISO:** MISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-04-miso-127-onlinepmin`
(`results/calibration/miso127_onlinepmin_B`), determination **NOT-YET**,
sole FAIL **C7 `COAL_PRB` — 2025 only** (cv_ratio 0.347 vs the 0.5 gate),
ledgered caveats 2/3 {C3a, C3c}, `audit_keepers --iso MISO` 0/0.

**Pushed before any adjudicating statistic.** Rule 22 `[R-HOLDOUT]`: 2023–2025
only — MISO holds **no** `calibration-complete` marker, so no out-of-training
year is solved, scored **or read**.

**Off-queue declaration (rule 28(a)).** `docs/mechanism-testing-matrix.md` §5.4
records that MISO has **no named, un-adjudicated, non-data-blocked queue item**
(the head was spent at miso-125; miso-126 and miso-127 both promoted keepers off
successors they named themselves). The two bounded non-solve steps that remain —
item 1's Form 580 tonnage count and miso-114 §6's overnight-gas measurement — are
respectively a **sourcing** pass and **spent** (miso-127's parallel lane,
`FINDING-miso127-overnight-gas-composition-2026-08-04.md`). This session
therefore takes the miso-127 §5 **named successor**: the 2025-only C7
`COAL_PRB` gap. It is on-queue as a *target*; what it lacks is a *lever*, and
supplying one honestly is this pre-registration's job.

---

## §0 — DISCLOSURE: what was already measured before this document was written

This session opened with an exploratory decomposition, on committed artifacts
only, no LP. Those numbers are stated here **in full** so that nothing below can
be reverse-engineered from a result the reader cannot see, and so the reader can
tell an ex-ante property from a post-exploratory one. Every property in §2 is
labelled **EX ANTE** (not yet measured when this was written) or **DISCLOSED**
(measured in exploration; restated here with its falsifier so the finding's
structure is fixed before the *lever* adjudication in §3, which is what this
session actually turns on).

Construction: `scripts/legitimacy_diagnostics.py`'s own D-1 inputs — the
committed bench `frontend/data/backcast/bench/MISO/<year>.json.gz` and the
keeper's registered payload `runs/2026-08-04-miso-127-onlinepmin.js`, paired on
keys present in **both** (the gate's own matched-plant convention).

**(a) The gated statistic reproduces.** cv_ratio 0.512 / 0.525 / 0.345 against
the committed artifact's 0.514 / 0.529 / 0.347 (the artifact was computed from
the solve-time `dispatch/` parquet, this from the payload).

**(b) The class off-peak (h0–h14) hour-of-day profile.**

| year | actual mean / std (MW) | model mean / std (MW) |
|---|---|---|
| 2023 | 14,108 / 2,184 | 13,094 / 1,038 |
| 2024 | 13,654 / 1,655 | 12,514 / 797 |
| 2025 | 16,392 / 1,207 | 15,993 / 407 |

**(c) A three-factor decomposition of the gated ratio.** With
`dfrac := std(hour-of-day profile, h0–14) / std(hourly MW, off-peak hours)` —
the share of a series' off-peak dispersion that is diurnally organised —

`cv_ratio = R_tot × R_dfrac × R_level`, where
`R_tot = tot_std_m/tot_std_a`, `R_dfrac = dfrac_m/dfrac_a`,
`R_level = mean_a/mean_m`.

| year | R_tot | R_dfrac | R_level | product | gated cv_ratio |
|---|---|---|---|---|---|
| 2023 | 0.907 | 0.525 | 1.077 | 0.512 | 0.512 |
| 2024 | 0.877 | 0.549 | 1.091 | 0.525 | 0.525 |
| 2025 | **0.952** | **0.355** | **1.025** | 0.345 | 0.345 |

**(d) On fully-online days only** (every h0–14 above 5 % of nameplate, both
sides, per plant — outage on/off removed): model/actual `resid_std` (the
non-diurnal, day-to-day component) is **0.825 / 0.808 / 0.829**, model/actual
diurnal amplitude is **0.473 / 0.483 / 0.315**, model/actual level is
**1.015 / 0.941 / 0.972**.

**(e) Flat-plant census** (off-peak profile std < 1 % of nameplate): model
26.0 / 27.4 / **59.4** % of PRB nameplate vs actual 0.0 / 7.5 / **12.3** %.

**(f) Per-plant amplitude vs loading**, pooled 90 plant-years, capacity-weighted
least squares: actual `std_frac = +0.0558 × cf_off + 0.0289` (wR² 0.429);
model `std_frac = −0.0028 × cf_off + 0.0250` (wR² 0.003).

**(g) The measured driver.** The keeper's own `calibration_flags.gas_prices` are
**2.54 / 2.19 / 3.52 $/MMBtu** — a **+61 %** 2024→2025 move. Matched-set
`COAL_PRB` annual energy: actual 126.0 → 150.1 TWh (**+19.1 %**), model
112.3 → 142.9 TWh (**+27.2 %**).

**(h) Dispatch-level discreteness**, off-peak online hours, same uint8 encoding
both sides: capacity-weighted perplexity model 13.5 / 11.8 / 13.9 vs actual
45.0 / 43.8 / 44.0 — a standing gap, **flat across years**, so it is not what
changed in 2025.

Nothing in §0 licenses a mechanism. §3 is where the session is decided.

---

## §1 — the reading under test

miso-127 §5 named the successor as "a *level-of-variability* question in the year
the fleet cycled least" and warned the ratio "is not monotone in the gap: both
sides fell, the model's fell further." The reading this session tests is
sharper and falsifiable:

> **R.** The 2025 C7 failure is **not** a new 2025 dispatch defect and **not** a
> deficit of dispatch variability. It is the 2025 projection of a standing,
> year-invariant defect in **one** dimension — the hour-of-day organisation of
> MISO coal's off-peak output — surfacing through a **ratio-form** gate whose
> denominator fell in 2025 for a driver (the +61 % gas move) the model
> reproduces.

R has a corollary that must be tested rather than assumed, because it is the
part that would make this a criterion artifact rather than a defect:

> **R′.** If R holds, the model's *absolute* amplitude deficit does **not**
> worsen in 2025 even though the ratio does.

---

## §2 — properties, each with its own falsifier

**P1 — reproduction control (DISCLOSED).** The construction reproduces the
committed `legitimacy_diagnostics.json` D-1 `COAL_PRB` cv_ratio within **±0.02**
in all three years. *Falsifier:* any year outside ±0.02 ⇒ the construction is
not measuring the gated statistic and **no statistic below is read**.

**P2 — two-grain dispatch control (EX ANTE, miso-126(a) duty).** The
payload-derived matched-class model off-peak profile std is cross-checked against
the keeper bundle's **unquantized** `hourly/class_hourly_<year>.parquet`
`COAL_PRB` series. Because the parquet carries the *full* class and the payload
the *matched* subset, the bar is on **shape, not level**: hour-of-day profile
correlation **≥ 0.98** and profile-std-over-mean agreement within **±10 %
relative** in all three years. *Falsifier:* either bar missed in any year ⇒ the
payload grain is not a faithful stand-in for the solve's own dispatch and the
decomposition is reported as unreadable rather than adjudicated.

**P3 — quantization floor (EX ANTE).** The uint8 CF% payload/bench encoding
resolves 0.01 × nameplate per hour; averaged into a 365-day hour-of-day profile
its noise contribution to `std_frac` is bounded. The measured bound must be
**≤ 5 % of the 1 %-of-nameplate flat-plant threshold** used in §0(e).
*Falsifier:* bound above that ⇒ the flat-plant census (e) is withdrawn; the
class-level decomposition (c)/(d) stands, since it is 3 orders of magnitude
above the floor.

**P4 — the decomposition is exact (DISCLOSED).** `R_tot × R_dfrac × R_level`
equals the directly-computed cv_ratio to **≤ 1e-6 relative** in all three years.
*Falsifier:* it does not ⇒ the three-factor attribution is arithmetic error and
is withdrawn.

**P5 — the 2025 attribution is single-factor (DISCLOSED).** All three hold:
`R_tot(2025) > R_tot(2024)`; `R_level(2025) < R_level(2024)`;
`R_dfrac(2025) < 0.80 × R_dfrac(2024)`. *Falsifier:* any one fails ⇒ the 2025
failure is **not** attributable to diurnal organisation alone and R is refused.

**P6 — R′, the absolute-deficit test (DISCLOSED as inputs, EX ANTE as a test).**
The model's absolute off-peak amplitude deficit, measured three ways —
(i) `std_a − std_m` in MW, (ii) that deficit divided by the class's actual
off-peak mean, (iii) `cv_a − cv_m` — is **non-increasing** from 2023 to 2024 to
2025 on all three. *Falsifier:* any of the three rises in 2025 ⇒ R′ fails, the
2025 failure carries a genuine absolute-amplitude regression, and the finding
must say so instead of calling the ratio scale-sensitive.

**P7 — the defect is year-invariant in the dimension R names (EX ANTE).** On
fully-online days the model/actual **non-diurnal** ratio `resid_std_m/resid_std_a`
varies across 2023–2025 by **less than ±0.10 absolute**, while the diurnal ratio
falls by **more than 0.10** into 2025. *Falsifier:* the non-diurnal ratio moves
more than the diurnal one ⇒ the defect is not dimension-specific and R is
refused.

**P8 — control classes (EX ANTE, a fork not a kill).** The same decomposition is
run for `COAL_BIT` and `COAL_LIGNITE`. Declared in advance: if `R_dfrac` collapses
in 2025 for those classes too, the object is a **coal-fleet-wide** hour-of-day
defect; if it does not, it is **`COAL_PRB`-specific**. Both outcomes are
reported; neither kills R. Declared so the result cannot be narrated either way
after the fact.

---

## §3 — the lever adjudication (fully EX ANTE — this is what the session turns on)

The brief names one open lever: `coal_tranche_1/2/3_frac` (0.30/0.25/0.45) with
their passthroughs, declared in `scenarios.py` as "calibrated to EIA-930
2023–2024 hourly **ERCOT** coal dispatch", flagged residual-identified in the DOF
ledger with open issue **#1336** — a live rule-25 `[R-ISO-SCOPE]` / rule-21
`[R-DOF]` debt sitting on the C7 mechanism.

**P9 — is the named lever reachable on MISO's own solve path? (EX ANTE, two
grains, miso-126(a) duty.)**

* **Grain 1 — construction, by source read.** `market_sim.data.fleet.assembly`
  branches on `if campd_bins is not None:`; `split_coal_tranches` — the **sole**
  consumer of `coal_tranche_{1,2,3}_frac` outside probe scripts
  (`data/offer_curves.py:70-72`) — is called **only in the `else` limb**. The
  MISO keeper runs `use_campd_bins = True` / `plant_level_fleet = True`
  (`run_config.json`), i.e. the CAMPD-binned limb, whose per-bin fuel fractions
  come from `campd_tranche_fuel_frac`.
* **Grain 2 — measurement.** Assemble the MISO 2025 dispatch fleet at HEAD under
  the keeper's own config, then again with `coal_tranche_1/2/3_frac` perturbed
  to a materially different split, and compare the resulting per-generator
  `pmax_mw` vector and `fuel_fracs` vector elementwise.

*Adjudication, declared now:*
* If grain 2 shows **zero** elementwise difference, the lever is **INERT BY
  WIRING at MISO** — it is not a MISO tuning channel, #1336 is not a MISO debt,
  and **no arm is solved on it**. This is a zero-solve kill on a pre-registered
  property (the miso-127 Lane A pattern).
* If grain 2 shows **any** difference, the wiring kill is **REFUSED** and the
  lever is live. It then still may not be swept against the C7 residual
  (rules 1 `[R-STRUCT]` / 24 `[R-REGISTRY]`); it would need a rule-23
  `[R-FROZEN-DERIVE]` re-derive citing a **source-data** change, which is its own
  session. Either way **this session solves nothing on it** — the difference is
  only whether the debt is MISO's.

**P10 — the successor screen (EX ANTE).** An arm is chartered **this session**
only if a candidate mechanism satisfies **all four**:

1. it is not in a family already closed at MISO — the take-or-pay **period-budget**
   family (closed by proof, miso-127 §1.2), take-or-pay **removal** (R twice,
   miso-102), the **regulated-self-commitment forcing** family (miso-111 R /
   112 R / 113 I), or receipts-derived tonnage in any variant (miso-103);
2. its parameters have an identification source that is **not** the C7 residual
   (rule 13 `[R-MEASURED]` / rule 21 `[R-DOF]`);
3. it is proven **wired into MISO's actual solve path at two grains** before any
   solve (miso-126(a));
4. it targets the **`R_dfrac` factor specifically** — a mechanism that adds
   dispatch variability without organising it hour-of-day cannot move the gated
   statistic, since §0(c)/(d) already show total dispersion is 83–95 % right.

*Falsifier / default:* if no candidate satisfies all four, **NO arm is solved,
no bundle is produced and no run is registered** — and the finding says so
explicitly rather than manufacturing a successor (rule 19 `[R-ONE-MECH]`).

**P11 — `coal_mustrun_online_pmin` is out of scope (EX ANTE, declared to be
binding).** The freshly-promoted keeper mechanism is **not** re-swept, re-tuned
or re-sized in any arm this session, in any year (rules 1 / 24, and the brief's
DO-NOT-REDO). *Falsifier:* none — this is a prohibition, and a session that
finds itself sizing it has already failed.

---

## §4 — KILLs

* **KILL-1.** No statistic is read if **P1** fails.
* **KILL-2.** The flat-plant census is withdrawn if **P3** fails; it is
  presentation, never the load-bearing evidence.
* **KILL-3.** Reading R is refused if **P5** or **P7** fails.
* **KILL-4.** **Nothing may be sized on any Δ measured here.** Every quantity in
  §0 and §2 is a residual or a function of one; using one to set a parameter is
  rules 13 / 21 / 24. This binds regardless of outcome.
* **KILL-5.** No out-of-training year is solved, scored or read (rule 22). The
  2025-only framing is a statement about a **training** year.
* **KILL-6.** No number here is quoted as a **price** result. The C7 statistic is
  a dispatch-shape statistic; miso-121's DO-NOT-REDO (binding is not marginality)
  and miso-102's P5 (C7 and diurnal-spread compression are separate misses) both
  bind.

---

## §5 — what a PASS of R would and would not license

**Would:** re-describing MISO's C7 residual, for every future session, as a
single-dimension hour-of-day-organisation defect that is **year-invariant in
magnitude** and merely **projected** onto a shrinking denominator in 2025 — which
retires "2025 is different" as a lane and stops the next session hunting a
2025-specific driver that does not exist.

**Would not:** license any mechanism, any sizing, or any claim that C7 is
"really" passing. The gate is the gate; a scale-sensitive statistic is still the
scored statistic, and the underlying amplitude deficit (the model carries under
half of reality's diurnal coal amplitude in **every** year) is real, unfixed, and
the thing a successor must attack.
