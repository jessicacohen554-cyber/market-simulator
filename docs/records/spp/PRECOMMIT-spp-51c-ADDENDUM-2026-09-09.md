# ADDENDUM to PRECOMMIT-spp-51c — phase 0 result, the SPP LMP CLOCK DEFECT, and the screen year

**Pushed BEFORE the screen solve runs.** Everything below is zero LP. It names the screen year by
the rule the PRECOMMIT declared, records the phase-0 footprint including **two declared bands that
MISSED**, and reports a defect found while validating the instrument that changes what "the measured
negative hours" even means.

---

## A. THE CLOCK DEFECT — found while validating the instrument, direction fixed by physics

`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` — the committed SPP actual-price sidecar
that C3a, C3b and C3c all score against — **is indexed on UTC, while the model's EIA-930 frame is
Central PREVAILING time.** The offset is **6 h in CST months and 5 h in CDT months**.

**This was not looked for and it is not this lane's object.** It surfaced because the PRECOMMIT's
§3.1 F-2 leg pairs the instrument's allocated hours against the measured-negative hours, and the
pairing looked wrong. The correction's **direction and magnitude were fixed by three
clock-independent physical markers, before any C3a number was computed** — never by a residual:

| marker | reading | says |
|---|---|---|
| EIA-930 SPP **solar** hour-of-day peak | index **12 / 13 / 13** (2023/24/25) | the model frame is **local** (solar noon) |
| EIA-930 SPP **load** hour-of-day peak | index **17** in all three years | the model frame is **local** (5 pm) |
| committed sidecar **RT LMP** peak | index **23 / 22 / 23** | a 22:00–23:00 local RT peak is **not physical** |
| SPP's own **GenMix**, explicitly stamped `GMT MKT Interval` | load peaks at **UTC hour 22** | and the sidecar peaks at **22** — the sidecar is on **SPP's GMT clock** |
| lag scan, corr(load rolled by L, RT), −12…+12 | single-peaked, best **L = +5** in all three years | one clean phase shift, not a broad artifact |
| the same scan split by season | best **L = 6** in Jan/Feb and Nov/Dec, **4–5** in Apr–Sep | **CST/CDT**, i.e. a true timezone mismatch |

**A six-ISO control census isolates the defect to SPP.** Best lag of corr(load, RT LMP), 2024:
**CAISO 0, PJM 0, MISO 0, NEISO 0, NYISO −1, ERCOT +2 — SPP +5**; LMP peak vs load peak index:
CAISO 18/19, PJM 17/17, MISO 16/17, NYISO 17/18, NEISO 17/17, ERCOT 18/15, **SPP 22/17**. The other
six sidecars are built by `scripts/data/derive_actual_lmp.py`, whose `_STD_TZ` registry carries
ERCOT / PJM / CAISO / NYISO / NEISO and converts report labels to the model's fixed standard clock.
**SPP's sidecar bypasses that path entirely** — it is staged pre-built by
`scripts/data/build_spp_lmp_reference.py`, whose docstring *asserts* the SPP monthly wide files are
"already hourly on the local clock". The measurement says they are not.

**What it does to the scored number, reported at full magnitude and in both directions.** Rubric
v2.4 scores C3a against `rt_lw` — *the committed hourly actual weighted by the same measured demand
the model dispatches* — which is an **hour-matched** pairing, so the offset lands directly on it.
Instrument validation first: my re-computation of the **misaligned** `rt_lw` reproduces SPP-51b's
committed bench values **exactly** (24.438 / 24.531 / 27.957).

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| `rt_lw` as committed (misaligned) | 24.438 | 24.531 | 27.957 |
| `rt_lw` on the corrected clock | **25.178** | **25.497** | **28.649** |
| delta | **+0.740** | **+0.966** | **+0.692** |
| SPP-50 C3a as scored | +15.0 % | +12.1 % | +14.2 % |
| SPP-50 C3a on the corrected actual (model side unchanged) | **≈ +11.6 %** | **≈ +7.9 %** | **≈ +11.4 %** |

**The repair makes SPP's C3a BETTER, and 2024 would flip FAIL → PASS.** That is precisely why the
ordering matters and why it is disclosed here rather than in a result: the direction was set by
solar noon and by SPP's own GMT-stamped GenMix, **before** `rt_lw` was computed either way. Rule 14
`[R-ACCURATE]` says prefer the accurate input and never bury an error back inside an inaccurate one;
it does not stop applying because the accurate input happens to help.

**THIS LANE DOES NOT LAND THE REPAIR, and says why rather than leaving it implied.** (a) It is a
**scoring-basis** change, not a model-input change: it would re-score every registered SPP run and
both SPP keepers' determinations, which needs its own pre-registration and is outside this
PRECOMMIT's declared file scope. (b) It **cannot be verified end-to-end here**: the SPP raw monthly
settlement-location exports are not staged in the repo (`data/raw/spp-lmp-alt/` carries only
`README.md`/`SOURCES.md`) and `portal.spp.org` is blocked to an anonymous caller
(`FINDING-spp-12-2026-09-06.md`), so the sidecar cannot be regenerated from source and a permutation
of the committed file cannot be proved against the publisher's own product. (c) `data/raw` is
immutable, so the correct locus is the builder / the `derive_actual_lmp._STD_TZ` seam, not the file.
**Routed as SPP-51c R-1 with the exact locus and the measured effect above. No owner card is
opened.**

**Consequences carried through this lane's own numbers, not hidden:** SPP-51b §2's bucket
decomposition and its "which hours" pairing are **misaligned** (its *counts* — 992 / 1,172 / 1,018
measured, 4 / 7 / 0 model — are each computed on one series and stand). The measured-negative **sets
before and after correction overlap by only 41.2 / 36.6 / 43.0 %**, so every hour-matched number in
§B below is computed on the **corrected** alignment and is not comparable to a misaligned one.
SPP-51b's availability arm is therefore **re-measured here** rather than quoted.

---

## B. PHASE-0 FOOTPRINT — the three allocation rules, like for like on the corrected clock

Every arm distributes the **identical** frozen annual energy: annual wind potential is
**114.0552 / 120.9925 / 122.2552 TWh** for all three rules in all three years (rule 23 intact).

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured hours < \$0 (corrected clock) | 992 | 1,173 | 1,018 |
| **share of C landing in those hours** — flat rule (today) | 17.01 % | 18.72 % | 16.91 % |
| — arm A, availability shape (SPP-51b §3, **re-measured here**) | 32.91 % | 34.33 % | 43.49 % |
| — **arm B, oversupply water-fill (this lane)** | **40.75 %** | **42.68 %** | **43.71 %** |
| **mean lift of the bound in those hours** — arm A | +1,764 MW | +1,553 MW | +3,081 MW |
| — **arm B** | **+2,634 MW** | **+2,385 MW** | **+3,106 MW** |
| **share of the measured-negative hours that receive any allocation** — arm A | 62.9 % | 58.7 % | 67.8 % |
| — **arm B** | **93.1 %** | **86.0 %** | **91.2 %** |
| hours receiving any allocation — arm B | 3,090 | 3,173 | 3,025 |
| λ\* (reported, never set) | 16.15 GW | 16.48 GW | 17.58 GW |
| mechanism's reallocated energy Σ\|new−old\| | 12.053 TWh | 13.031 TWh | **13.587 TWh** |

**Arm B beats arm A in every year on every measure**, and most clearly on coverage — it reaches
86–93 % of the measured-negative hours against arm A's 59–68 %. That is the oversupply key doing
what the availability key could not.

### Declared bands, graded — TWO MISSED

| leg | declared | measured | verdict |
|---|---|---|---|
| **F-1** identity + root | ≤ 0.1 %, `potential ≥ delivered` ∀t, λ root exists | rel err **0 / 0 / 1.2e-16**; true ∀t; root exists; the capacity cap binds in **0** hours | **PASS** |
| **F-2** concentration | **≥ 45 %** | **40.75 / 42.68 / 43.71 %** | **MISS — in all three years** |
| **F-3** breadth | 1,200–4,000 h | 3,090 / 3,173 / 3,025 | **PASS** |
| **F-4** reach | **+3.0 to +8.0 GW** | **+2.63 / +2.38 / +3.11 GW** | **MISS in 2023 and 2024**; 2025 inside |
| **F-5** λ plausibility | 15–32 GW | 16.15 / 16.48 / 17.58 | **PASS** |

**F-2 and F-4 are reported in the words they were written in.** F-2's bar was "≥ 45 %" and the best
year reached **43.71 %** — a miss, not "≈ 45 %". F-4's band was "+3.0 to +8.0 GW" and two of three
years came in **below** it. I set both bars myself, before the numbers existed, and they missed.

**Why this is nevertheless not partition branch 2.** Branch 2 fires at **F-2 < 20 %**, on the stated
ground that the oversupply key would be "no better than the availability key". At 40.75 / 42.68 /
43.71 % against arm A's 32.91 / 34.33 / 43.49 % and the flat rule's 17 / 19 / 17 %, it is neither
below 20 % nor no-better. **The declared partition sends this arm to the screen, and I am honoring
it rather than re-cutting a threshold after seeing the number.**

---

## C. THE SCREEN YEAR, and the ex-ante G-1 prediction

**Screen year = 2025**, by the PRECOMMIT's declared rule — the largest reallocated energy
Σ|potential_new − potential_old| = **13.587 TWh**, against 12.053 (2023) and 13.031 (2024). Recorded
against interest: 2025 is **not** the year with the worst C3a on either basis (2023 is, at +15.0 %
as scored / ≈ +11.6 % corrected), so the choice is footprint-driven exactly as rule 1 requires.

**Ex-ante G-1 prediction, computed now and frozen.** Estimator: keeper-3's committed 2025 P1 class
hourlies give the LP's thermal dispatch and its realised deep floor (p0.5 = **5,164.8 MW**, annual
min 3,076.8 MW, mean 17,444.1 MW); wind is predicted to go strictly interior in an hour when the
arm's bound lift exceeds the thermal turn-down available there. Lift is positive in **2,291 h** and
peaks at **9,871 MW**.

- **G-1a — hours with wind STRICTLY INTERIOR to its bound: predicted 871**, gate band
  **[348, 2178]** (0.4×–2.5×). This is the mechanism's own direct signature. Control: essentially
  **0** — SPP-50 re-curtails 0.00030 % of its 2025 wind.
- **G-1b — system load-weighted hours < \$0: predicted 592**, gate band **[237, 1480]**, derived as
  871 × the measured 68 % of SPP's negative hours in which **both** hubs are negative together (a
  system LW price needs both; SPP-51b §5 R-3). Consistent with the PRECOMMIT's against-interest
  X-1, which predicted **below 700**.

**Stated limitation, not smoothed:** keeper-3 is the **pre-SPP-48/49** input surface, so this is an
**estimator**, not a control. SPP-50 is the control on the current surface and has **no `hourly/`
sidecars**, so no hour-level control differencing is claimed anywhere in this lane — exactly as the
PRECOMMIT's rule-29(b) posture said.

**Everything else in the PRECOMMIT is unchanged**: the gate stays structural and STOP-only,
C3a/C3b/C3c stay marked "not gated on" in both directions, and the partition is untouched.
