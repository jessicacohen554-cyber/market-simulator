# FINDING — miso-138: the offer-side-only class bridge for MISO's `da_co` corpus is REFUTED on the pre-committed rule — the corpus IS the MISO fleet and its declarations DO carry class information, but coal and CC are not separable in this feature family, and that ceiling was measurable on ground truth before a single masked unit was classified

**Session:** miso-138, 2026-08-06, branch `claude/miso-138-shape-lever-rp25g4`.
Charter lane **(b)** — the §5.4 standing chartered item
(`FINDING-miso136-ct-offer-conduct-corpus-exists-2026-08-06.md` §6).

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER DERIVED. NOTHING WRITTEN UNDER
`data/raw/`. NO CELL VERDICT MINTED.** MISO keeper unchanged at
**`2026-08-05-miso-132b-cc-committed`** (NOT-YET; sole FAIL C7 `shape`;
ledgered caveats 2 of 3, `{C3a, C3c}` — re-verified from the committed
`metrics.json` this session).

**PREREG** `results/calibration/PREREG-miso138-da-co-class-bridge-2026-08-06.md`,
pushed at **`848d387a`** BEFORE any adjudicating statistic, with a two-sided
prior, the most likely failure mode named in advance, and the look-alike trap
named with a pre-committed permutation null that outranks the aggregate
statistic.

**Owner directive honoured:** no C7 lane chartered, no C7 ledger sought.

---

## 1. Headline

**The pre-committed verdict is `REFUTED`**, fired by PREREG §7 **R2** — the CC
class carries |S_cap| > 0.50 **at both EIA-860 grains in 2024 and 2025**
(generator grain **+1.240 / +1.335 / +1.283** in 2023/24/25; cc_block grain
+0.497 / **+0.726** / **+0.586**). The DEMONSTRATED branch **D1** fails at
every grain in every year, for every one of the three target classes. The
verdict does **not** flip across grains or years, so the `NOT ASSERTED` branch
does not apply — this is a stable REFUTED, and it is robust to the
pre-registered prior sensitivity (uniform priors fail D1 harder: CT S_cap
−0.880 / −0.909 / −0.901) and to EIA-860 vintage (§7).

**But three things are established, and they are the reusable half of the
result:**

1. **G-0 PASSES — the corpus IS the MISO fleet.** The screened corpus
   capability reconciles with EIA-860 MISO at fleet grain to **+12.9 / +9.0 /
   +6.0 %** on MW and **−1.4 / −4.1 / −7.5 %** on unit count (cc_block grain).
   The failure is **not** a population mismatch.
2. **The permutation null is beaten decisively, everywhere.** Observed G-3
   discrepancy **1.63–2.16** against a size-preserving null p05 of
   **8.46–8.88** (null p50 ≈ 9.5), at both grains, all three years, both
   priors. The classification carries **real class information** — it is not
   noise dressed as agreement.
3. **G-4, the nuclear positive control, substantially passes.** 12 of MISO's
   14 nuclear units are recovered from offer-side declarations alone, capacity
   within **−4.4 % (2023) / −5.9 % (2024)** at both grains. A distinctive
   technology *is* recoverable from this corpus.

**So the bridge fails not because the corpus is uninformative, but because the
one split the lane actually needs — coal versus CC — is the split this feature
family cannot make.**

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **G-0** basis reconciliation (GATING) | **PASS**, both grains, all years. rel_MW **+0.129 / +0.090 / +0.060**; rel_N −0.160/−0.183/−0.212 (generator grain) and **−0.014 / −0.041 / −0.075** (cc_block). No hard stop (the 2× stop rule is nowhere near). |
| **G-1** identification on ground truth (GATING) | **PASS, marginally**: 5-fold CV balanced accuracy **0.705** (generator grain) / **0.718** (cc_block) against a 0.70 bar, on 5,454 / 4,436 held-out non-MISO EIA-860 generators. **The pass is carried by CT and NUC; COAL was already at recall 0.382 with the labels in hand.** |
| **G-2** primary separation (two-sided) | **FAIL at every grain, year and class.** See §3. |
| **G-3** within-class shape | **FAIL** — the shape discrepancy is far better than the null (§1) but nowhere near the ±30 %/±35 % band, because the class *memberships* are wrong. |
| **G-4** nuclear control | **PASS 2023 & 2024** (Δn = −2, capacity −4.4 %/−5.9 %), **FAIL 2025** (Δn = −4 generator / −6 cc_block; capacity −17.0 %/−33.9 %). |
| §6(ii) permutation null | **BEATEN** everywhere — R4 does **not** fire. |

---

## 3. The primary statistic, as pre-registered

`S_cap = (MW_corpus(k) − MW_860(k)) / MW_860(k)`, `S_count` likewise. D1 asks
for |S_cap| ≤ 0.25 and |S_count| ≤ 0.35.

**Generator grain (primary prior):**

| year | CT S_cap / S_count | CC S_cap / S_count | COAL S_cap / S_count | max class share |
|---|---|---|---|---|
| 2023 | −0.451 / −0.415 | **+1.240** / +0.749 | −0.369 / −0.574 | 0.593 |
| 2024 | −0.505 / −0.476 | **+1.335** / +0.870 | −0.512 / −0.678 | 0.640 |
| 2025 | −0.479 / −0.473 | **+1.283** / +0.745 | −0.534 / −0.678 | 0.644 |

**CC-block grain (primary prior):**

| year | CT S_cap / S_count | CC S_cap / S_count | COAL S_cap / S_count | max class share |
|---|---|---|---|---|
| 2023 | +0.505 / −0.041 | +0.497 / +0.786 | −0.334 / −0.435 | 0.396 |
| 2024 | +0.381 / −0.064 | **+0.726** / +0.869 | −0.542 / −0.565 | 0.473 |
| 2025 | +0.477 / −0.080 | **+0.586** / +0.643 | −0.487 / −0.530 | 0.447 |

**The signed pattern is identical everywhere: CC is over-assigned, coal is
under-assigned.** R3 (degenerate collapse, >60 % of capability in one class)
fires at the generator grain in 2024–2025 only; it is **grain-dependent and
the verdict does not rest on it** — R2 alone is grain-stable and sufficient.

---

## 4. Why — measured on GROUND TRUTH, where the answer is known

The G-1 confusion matrix on the held-out non-MISO EIA-860 population (rows =
true class, columns = predicted):

| true \ pred | CT | CC | COAL | NUC | recall |
|---|---:|---:|---:|---:|---:|
| **CT** | 2,666 | 773 | 0 | 0 | 0.775 |
| **CC** | 360 | 1,213 | 29 | 1 | 0.757 |
| **COAL** | 69 | **120** | **126** | 15 | **0.382** |
| **NUC** | 0 | 0 | 3 | 79 | 0.963 |

**Coal is misclassified as CC almost as often as it is classified correctly,
with the labels available.** The corpus result is that ceiling's arithmetic
consequence — coal capability drains into CC, which is exactly the +124 % to
+134 % CC over-assignment and the −37 % to −53 % coal shortfall in §3.

**The feature ablation shows how little was ever there for coal.** In-sample
COAL recall by feature set:

| features | balanced acc. | COAL recall |
|---|---:|---:|
| `logcap` | 0.612 | **0.000** |
| `logcap + minfrac` | 0.620 | 0.061 |
| `logcap + derate` | 0.656 | 0.097 |
| all three | 0.719 | 0.382 |

Coal is essentially invisible to size alone, and the three features together
still leave it worse than a coin flip.

**And the physical reason is measurable in the registration data itself.**
EIA-860 MISO, by TRUE class:

| class | derate p50 | derate p90 | share exactly flat | minfrac p50 |
|---|---:|---:|---:|---:|
| CT | +0.076 | +0.214 | 0.418 | 0.500 |
| CC | +0.081 | +0.189 | 0.269 | 0.497 |
| COAL | +0.000 | +0.029 | 0.704 | 0.317 |
| NUC | +0.020 | +0.048 | 0.071 | 0.279 |

* **The seasonal derate does not separate CT from CC at all** (+0.076 vs
  +0.081 — the two gas technologies derate alike).
* **It does separate coal** (flat, 70 % exactly zero) — but it separates coal
  *toward nuclear*, not away from CC.
* **Min-load fraction points the wrong way**: registered coal min-load
  (0.317) is **lower** than gas CT and CC (≈0.50), so the one feature that
  should have carried coal's distinctive commitment physics actively pushes it
  into the wrong half of the space.

That is the whole failure, and none of it required a masked unit.

---

## 5. My own prior, corrected against interest

PREREG §2 named the most likely failure mode as: *"`Economic Max` is a
submitted COMMERCIAL declaration, not a measured capability … the
seasonal-derate fingerprint is identically zero for every technology."*

**Measured, that prediction is largely WRONG and I record it as wrong.** The
corpus's unconditional derate distribution over screened units:

| year | p10 | p50 | p90 | share exactly flat |
|---|---:|---:|---:|---:|
| 2023 | −0.0016 | +0.0000 | **+0.162** | 0.466 |
| 2024 | −0.0037 | +0.0134 | **+0.192** | 0.396 |
| 2025 | −0.0224 | +0.0030 | **+0.193** | 0.410 |
| *EIA-860 MISO, all classes* | — | *+0.044* | — | *0.413* |

**The corpus's flat-declaration share (0.40–0.47) is essentially the same as
the registration data's (0.413)**, and its p90 (+0.16 to +0.19) sits in the
right physical range. MISO participants *do* declare a seasonal capability,
and roughly as often as EIA-860 records one. The corpus is flatter than
registration at the median (+0.000–0.013 vs +0.044), which is a real but
second-order difference.

**So the bridge did not fail for the reason I expected.** It failed because
the *classes themselves* are not separable in this feature family — a
property of CT/CC/coal physics as recorded in EIA-860, not of MISO's masking.
Had the corpus been perfect, G-1's 0.382 coal recall would still have capped
it.

---

## 6. The look-alike trap — where it fired, and what caught it

PREREG §6 named it: *aggregate distributional agreement is compatible with an
arbitrarily scrambled per-unit assignment.*

**It fired, visibly, at the cc_block grain on CT**: `S_count` reads
**−0.041 / −0.064 / −0.080** — an apparently excellent count reconciliation —
while `S_cap` on the same class and grain reads **+0.505 / +0.381 / +0.477**.
Right number of units, wrong units. Quoting that count agreement as evidence
the CT class had been recovered would have been exactly the trap; the
pre-registered pairing of count with capacity and within-class quantiles is
what made it impossible to quote.

**The null leg did its opposite job just as usefully.** Because the observed
G-3 discrepancy beats the size-preserving null by a factor of ~5 at every
grain, year and prior, the failure **cannot** be dismissed as "the classifier
learned nothing." The pre-committed machinery therefore separated two things
that would otherwise be confounded: the assignment is **informative and
insufficient**, and only one of those two is fixable by a better feature set.

---

## 7. Robustness — the two objections that do not survive

* **EIA-860 vintage.** The primary reference is the current 2025 Early Release
  parquet, compared against three corpus years. Re-measured on the year-matched
  vintages, MISO's class aggregates barely move: CT 624/627/636 units and
  24.4/24.5/25.0 GW; CC 261/252/252 and 34.2/33.4/34.2 GW; COAL 127/118/117
  and 45.2/43.0/43.0 GW; NUC 13/14/14 and 11.6/12.3/12.3 GW. **≤5 % on every
  class — vintage drift cannot account for a +124 % CC over-assignment.**
* **The VER exclusion screen.** It removed **34.4 / 36.5 / 44.5 GW** across
  2023/24/25 against EIA-860 MISO wind+solar of **38.3 / 45.4 / 53.6 GW** —
  90 % / 80 % / 83 %, growing in the right direction with MISO's build, with
  the shortfall consistent with distribution-connected solar that never enters
  the DA offer book. The screen is doing what it was specified to do.

One instrument limit, reported rather than buried: EIA-860's CT class carries
p50 capacity **18.8 MW** because the repo's `NG_CT_PRIME_MOVERS` includes `IC`
reciprocating engines — hundreds of small units that largely never register in
MISO's DA market. This inflates the EIA-860 CT count relative to anything the
corpus could contain and is part of the generator-grain CT `S_count` of −0.42
to −0.48. It does not touch the coal↔CC result, which is where the verdict
comes from.

---

## 8. What this session does NOT adjudicate

The PREREG's admissible list included secondary offer-side features —
emergency-range structure, must-run and self-schedule structure, Region —
which were excluded from the discriminant **by design**, because they have no
EIA-860 analogue and so cannot cross the held-out training population. **This
session therefore says nothing about whether they would help.**

Explicitly flagged so it is not mis-quoted later: those features *appear*
contrasted when tabulated by predicted class (e.g. must-run fraction 0.500 for
predicted-COAL against 0.000 for predicted-CT/CC). **That reading is circular**
— the classes are the classifier's own output — and it is **not** evidence.
Any future use of them would need a different identification strategy and
would forfeit exactly the ground-truth ceiling measurement that made this
session cheap and decisive.

**No lever is licensed and none is proposed** (PREREG K1/K7). A bridge is a
data prerequisite, not a mechanism; even a DEMONSTRATED verdict would have
licensed only a charter.

Per `FINDING-miso136` §6's own pre-commitment — *"If it fails, the prerequisite
is closed NO with the corpus on record, and the lane-(c) owner assessment
becomes the honest next step"* — that is where the lane stands. The
measured-offer-surface route to the charter's lane (a) is **closed for this
feature family**, the corpus is on record and validated as a population, and
whether the bounded residual question in this section is worth spending is an
owner call, not this session's.

**The miso-137 bench defect** (the committed MISO `*_lw` scalars recomputing
to 45.4555 vs the committed 45.39 for 2025 RT) was **not** taken up here.
Refreshing the bench changes the C3a comparator for every MISO run, so it
needs its own PREREG and its own session rather than a ride-along in a
data-bridge lane. It remains discrete, bounded and unowned.

---

## 9. Rule-22 audit line — exactly what was fetched

24 `da_co` daily zips, all 2023-, 2024- or 2025-dated, per PREREG §4 with no
substitutions:

* **2023** summer `20230718 20230719 20230815 20230816` · winter `20230117 20230118 20230214 20230215`
* **2024** summer `20240716 20240717 20240813 20240814` · winter `20240116 20240117 20240213 20240214`
* **2025** summer `20250715 20250716 20250812 20250813` · winter `20250114 20250115 20250211 20250212`

Fetched to session scratch only (19 MB). **Nothing written under
`data/raw/`**; no path registered in `config/paths.py`; the corpus is not
committed. Charter DATA GATE honoured — a bridge demonstration on transient
fetches is in scope, an intake is not.

---

## 10. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…137 precedent). Keeper unchanged.
**Rule 28(b) `[R-MECH-MATRIX]`** — **NO cell verdict minted**: no mechanism was
tested, probed or armed. `measured_offer_surface` MISO stays **`U`**. A §5.4
queue stamp is written this session.
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; MISO holds no
`calibration-complete` marker. No out-of-training year was read, solved,
scored or registered.
**Rule 13 `[R-MEASURED]`** — the corpus is a conduct-transparency publication
read as an *input* question, never as an answer key; the forbidden set (all
`Price*`/`MW*` curve columns, `Slope`, `Curtailment Offer Price`, the DA `MW`
award, RT `Cleared MW*`) is machine-enforced by the probe, which raises if any
is ever loaded.
**Rules 19 / 21 / 24 / 25** — one mechanism per phenomenon (none added);
nothing sized to any residual and no window or magnitude from miso-137 entered
any construction here; no tuning channel created; no other ISO's cell, keeper
or parameter touched.
**Owner directive** — no C7 work.

---

## 11. The generalisable lesson — **MEASURE AN IDENTIFICATION'S CEILING WHERE THE ANSWER IS KNOWN**

The whole verdict was determined before a single masked unit was classified.
Running the pre-specified classifier on the held-out **labelled** population
returned COAL recall **0.382** — and the masked-corpus result is that number's
arithmetic consequence, not an independent discovery. The expensive half of
the session (24 fetches, three years, two grains, two priors, 12,000
permutation draws) confirmed what the cheap half had already fixed.

*Before applying an identification where truth is unobservable, run it where
truth is observable and read its ceiling there. If it cannot make the split on
labelled data, it will not make it on masked data — and no amount of
distributional agreement downstream will tell you so, because aggregates
survive a scramble.*

Family: miso-129 *a signature is not a cause* → miso-131 *a plant-grain
signature is not a class-grain defect* → miso-132(a) *a missing rule is not a
binding one* → miso-133 *measure the slack, on one basis* → miso-134 *binding
is not licensing* → miso-135 *the right quantity at the wrong grain is the
wrong source* → miso-136 *an absence claim is a measurement, not a premise* →
miso-137 *a threshold is a hypothesis, not a definition* → **miso-138 *measure
an identification's ceiling where the answer is known***.

---

**Probes** `scripts/probes/_miso138_fetch_da_co.py`,
`scripts/probes/_miso138_da_co_class_bridge.py`,
`scripts/probes/_miso138_bridge_diagnostics.py` ·
**Records** `results/calibration/_miso138_da_co_class_bridge.json`,
`results/calibration/_miso138_bridge_diagnostics.json` ·
**PREREG** `results/calibration/PREREG-miso138-da-co-class-bridge-2026-08-06.md`.
