# FINDING — miso-136: MISO DOES publish a submitted-curve corpus at unit-hour grain — the miso-134 §9.3 absence assertion is FALSE — and the verdict is the pre-declared CONDITIONAL: corpus-exists / bridge-unproven

**Session:** miso-136, 2026-08-06, branch `claude/miso-136-calibration-t4olnw`,
off `origin/main` at `dc10345c`.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NOTHING INTAKEN under `data/raw/`. NO CONDUCT
STATISTIC COMPUTED** (PREREG K4 — structural checks only). MISO keeper
unchanged at **`2026-08-05-miso-132b-cc-committed`** (NOT-YET; sole FAIL C7
`COAL_PRB` 2025 `cv_ratio` 0.338 vs 0.50; ledgered caveats 2/3 {C3a, C3c}).
Rule 22 `[R-HOLDOUT]`: only 2023–2025-dated report files were fetched (the
full list is in §5); no out-of-training quantity was read.

**Pre-registration**
`results/calibration/PREREG-miso136-ct-offer-conduct-survey-2026-08-06.md`,
committed and pushed at **`ebca8364`** *before any MISO / IMM / FERC source
was opened*, with the model-memory prior disclosed as a prior. **Probe**
`scripts/probes/_miso136_ct_offer_conduct_survey.py`; **record**
`results/calibration/_miso136_ct_offer_conduct_survey.json`.

**Lane:** charter option **(a)** — the miso-134 named successor's data
prerequisite: *does an identification for within-day MISO CT offer conduct
exist that is NOT the C7 residual?* The load-bearing assertion under test
(miso-134 FINDING §9.3): *"MISO publishes no submitted-curve corpus at the
grain the `measured_offer_surface` family needs."* That assertion was never
surveyed, and the `measured_offer_surface` MISO = `U` cell rests on it.

---

## 1. Headline

**The absence assertion is FALSE.** MISO publishes, daily, a masked
**submitted-offer corpus at unit-hour grain** for BOTH markets:

> `https://docs.misoenergy.org/marketreports/YYYYMMDD_da_co.zip` (DA)
> `https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_co.zip` (RT)

one CSV row per **masked unit × hour**, carrying the full 10-segment
price/MW offer curve, economic/emergency limits, must-run / available /
economic flags, self-scheduled MW, curtailment offer price, slope flag, and
storage energy-level bounds, with a Region (North/Central/South) attribute —
published on a ~90-day lag (zip member timestamps: 2024-07-15 report
generated 2024-10-13; 2025-01-15 → 2025-04-15), i.e. the Order-719-family
conduct-transparency publication. The repo already consumes its ancillary
sibling (`asm_rt_co`, `fetch_miso_asm.py`); the energy analogue was sitting
at the same endpoint.

**And the verdict is NOT a clean YES — it is the pre-declared CONDITIONAL
(PREREG §4): corpus-exists / bridge-unproven.** The corpus carries **no
unit-type / fuel attribute** (machine-verified 4/4 sample days: zero columns
matching `fuel|type|technolog`), so the direct CT-class bridge (class A) is
ABSENT. The masking is the publication's *purpose*, exactly as the
pre-registered purpose test predicted: a conduct-transparency report
publishes conduct and withholds identity. What remains is bridge class B —
a classifier over offer-side declarations, admissible in kind,
**undemonstrated** — so the miso-134 successor's data prerequisite is
**NOT discharged**, no lever is licensed, and the bridge demonstration is
the chartered successor question (§6).

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **G-0** access (GATING) | **PASS.** Enumerable URL pattern; five sample zips fetched across all three training years; boundary files `20230102_da_co.zip` and `20251231_da_co.zip` both live (HTTP 200) ⇒ the full 2023–2025 daily span is retrievable today, despite the ~3.5-year rolling-window concern disclosed in PREREG §0. |
| **G-1** kind | **PASS** for the offer-side columns. The curve segments, limits, and flags are participant declarations recorded ex ante. Decisively, the DA file is **NOT clearing-conditioned**: 392–614 units per sample day clear **zero** MW in every hour of the day and still appear with their full submitted curves — the file is the offer book, not a cleared-set reconstruction. (The files also carry outcome columns — DA `MW` award, RT `Cleared MW1–12` — flagged in §4; the conduct columns are separable.) |
| **G-2(i)** within-day grain | **PASS.** One row per unit-hour, 24 distinct hours per file; and within-day variation **exists in the data, not just the format**: 309–435 units per sample day submit hour-varying curves, 625+ vary availability/econ-max declarations (grain-existence counts only — no level, class, or profile was read). |
| **G-2(ii)** CT bridge | **Class A ABSENT** (no type/fuel column). **Class B material PRESENT**: masked IDs are **persistent** — 1,351/1,351 day-over-day overlap (2024-07-15 vs -16), 1,278 / 1,335 / 1,263 units shared across 2023↔2024 / 2024↔2025 / 2023↔2025 (≈92–99 %) — unlike PJM's annually re-masked codes (PREREG §0); plus Region, econ max/min structure, emergency ranges, must-run/self-schedule flags. **Bridge undemonstrated ⇒ CONDITIONAL**, per the pre-committed decision rule. |
| **G-3** coverage | **PASS.** 1,319 / 1,351 / 1,376 units per sample day (2023/2024/2025) — footprint scale, comfortably containing the ~249-unit / 22.3 GW CT class scale reference; ~32–33k unit-hour rows per day; N/C/S regions all populated. RT book is smaller (1,114 units on 2024-07-15), as an RT offer set should be. |

**Overall: CONDITIONAL — "corpus-exists / bridge-unproven"** (PREREG §4,
pre-committed): *"the miso-134 §9.3 assertion is FALSE but the prerequisite
is still open."* Kills K1–K7 all honoured; K4 specifically — the probe
computes counts, sets, and header facts only.

---

## 3. Per-source closures (each on the purpose test first)

* **S1 — MISO Market Reports `da_co`/`rt_co`: CONDITIONAL pass, §2.** The
  purpose test called both halves in advance: the publication exists to
  disclose offer conduct (so the conduct is there, at exactly the needed
  grain) and to protect unit identity (so the class bridge is deliberately
  absent). The right quantity, with the bridge as the open question — the
  miso-135 lesson's constructive case.
* **S2 — MISO Data Exchange: closed, immaterial.** The catalog page is
  WAF-blocked from this environment (HTTP 403) and `apim.misoenergy.org`
  products are subscription-keyed (repo `.env.example`). Immaterial to the
  verdict: S1 *is* the offer publication of record; an API product would
  serve the same masked data.
* **S3 — Potomac SOM: closed on purpose + form.** Monitoring analytics in
  PDF (2023–2025 SOM bodies + Analytic Appendices enumerated live):
  aggregate figures, and the markup/output-gap analytics are built on
  confidential IMM reference-level *estimates* — PREREG T2 and T4 both, at
  any depth of search. No unit-hour corpus exists there.
* **S4 — FERC EQR: closed on purpose, no fetch.** EQR exists for reporting
  jurisdictional *sales* — contract/transaction records, quarterly. It
  records transactions, not offers into the RTO; fails G-1 kind on its face.

---

## 4. The trap register, closed out (PREREG K7)

* **T1** (generation dressed as conduct): **did not fire** — no generation
  series was touched. Flagged for the successor: the corpus itself embeds
  outcome columns (DA `MW` award, RT `Cleared MW1–12`); a class-B classifier
  may not read them.
* **T2** (IMM estimates): **fired at S3**, in the anticipated form; closed.
* **T3** (corpus real, bridge forbidden — the wave-through trap): **fired in
  its CONDITIONAL form and was caught by the pre-declared category.** The
  corpus is real, hourly, offer-kind — and identity-masked. Neither waved
  through as YES nor buried as NO.
* **T4** (aggregate SOM figures): **fired at S3**; closed.
* **T5** (rule-22 hazard): **honoured** — fetched files enumerated in §5,
  all dated 2023–2025.

---

## 5. Exactly what was fetched (rule 22 audit line)

`20230715_da_co.zip`, `20240715_da_co.zip`, `20240716_da_co.zip`,
`20250115_da_co.zip`, `20240715_rt_co.zip` (parsed); HEAD-only existence
checks `20230102_da_co.zip`, `20251231_da_co.zip`, plus initial 1-byte range
probes of the same names and `20240715_asm_da_co.zip`. All 2023–2025
operating days. Nothing written under `data/raw/`; scratch copies only
(assessment, not intake — an actual corpus intake needs its own
authorization and the `data-intake` contract).

---

## 6. The chartered successor question (named, NOT opened here)

**Demonstrate — or refute — a CT-class bridge for the `da_co` corpus using
offer-side information only.** Pre-committed shape (PREREG G-2 class B):

* **Inputs allowed:** the corpus's own declarations (econ max/min and their
  ratio structure, emergency ranges, availability structure, self-schedule
  structure, Region, storage-level columns for exclusion), registration-grain
  public data (EIA-860 unit inventories) at *distribution* level.
* **Forbidden:** matching masked units to CEMS/dispatch/generation series
  (the miso-103 answer-key family); classifying by the conduct statistic the
  successor lever would then measure (circular); reading the corpus's
  outcome columns.
* **Validation bar:** a pre-registered separation statistic against EIA-860
  MISO CT fleet aggregates (count and capacity distribution), two-sided, with
  the failure mode named in advance. If the bridge clears, THEN the
  hour-organizing CT lever lane (miso-134's named successor) becomes
  charterable with its own PREREG and the full kill stack (C1 16/16,
  COAL_BIT no-overshoot, D-4 window, LOYO, two-grain firing). If it fails,
  the prerequisite is closed NO with the corpus on record, and the lane-(c)
  owner assessment becomes the honest next step.

**Lane (c) is NOT opened this session:** the charter gates it on (a) closing
NO. (a) closed CONDITIONAL — a live, admissible, bounded data question
remains, so MISO's lever space is not exhausted and an owner determination
ask would be premature.

---

## 7. The generalisable lesson — **AN ABSENCE CLAIM IS A MEASUREMENT, NOT A PREMISE**

miso-134 §9.3 stated "MISO publishes no submitted-curve corpus" without
surveying; miso-135 §10 then (correctly, per its own scope) grounded a matrix
cell on that unsurveyed claim; one afternoon of survey falsified it — the
corpus was one URL pattern away from a fetcher the repo already runs daily
(`asm_rt_co`). **A negative existence claim carries the same evidential
burden as a positive one: survey it before building on it, and record the
survey either way so the ground stops being an assertion.** The constructive
half of the miso-135 purpose test: the filer's purpose predicts not only
what a source *cannot* carry, but what it *must* — a conduct-transparency
publication must carry conduct at conduct grain, and that prediction is what
made this survey cheap.

Family: miso-129 *a signature is not a cause* → miso-131 *a plant-grain
signature is not a class-grain defect* → miso-132(a) *a missing rule is not a
binding one* → miso-133 *measure the slack, on one basis* → miso-134 *binding
is not licensing* → miso-135 *the right quantity at the wrong grain is the
wrong source* → **miso-136 *an absence claim is a measurement, not a
premise***.

---

## 8. Consequences for the queue

1. **The miso-134 §9.3 absence assertion is CORRECTED on the record** (this
   finding; matrix note; §5.4 stamp). The `measured_offer_surface` MISO cell
   **stays `U`** — no mechanism was tested and no verdict is minted — but its
   ground changes from *"U by absence of a testable input (unsurveyed)"* to
   *"U with a surveyed input: corpus EXISTS (miso-136), CT bridge unproven"*.
2. **ONE chartered successor enters the §5.4 queue:** the §6 bridge
   demonstration (no-LP data question, bounded, pre-registration mandatory).
   It is the ONLY chartered item; everything adjudicated-closed in the
   miso-135 stamp carries forward intact.
3. **DO-NOT-REDO, added:** re-asserting corpus absence; deep-reading SOM
   PDFs for a unit-hour corpus (closed on purpose + form); EQR as an offer
   source (closed on kind); bridging masked IDs via CEMS/dispatch matching
   (forbidden in advance).
4. **Charter lane (b)** (CT_CHP/ST_CHP S-2 residuals) was not opened — lane
   (a) ran to verdict and consumed the session; it remains available to a
   future session exactly as the handoff left it.
5. **C7-2025 stays where miso-103 left it** — failing and unledgered. Nothing
   here claims C7 relief; the corpus is a *prerequisite* answer, not a lever.

---

## 9. Rule duties

* **Rule 15** — no LP solved, no run to register (miso-131…135 precedent).
  Keeper and dashboard untouched.
* **Rule 28(b)** — no cell verdict minted (no mechanism tested); the matrix
  edit is the §8.1 ground update on the `measured_offer_surface` MISO note,
  which the PREREG §5 committed to in advance. §5.4 queue stamp written this
  session.
* **Rule 22** — §5 audit line; training-span dates only.
* **Rules 13/19/21/24/25** — nothing sized on any residual, no parameter
  derived, no artifact re-derived, no tuning channel created, no other ISO's
  cell read into MISO (the PJM masking precedent was cited only as the shape
  a NO could take, and MISO's masking proved materially different).
