# GATESPEC — caiso-193 (lane 3): a CAISO-derived, publicly cited ST_GAS WEFOR base (`gas_st_wefor_base_override`)

**Authored by caiso-191 on 2026-08-11, BEFORE any lane-3 measurement exists.** These
gates are fixed and fail-closed. The lane discharges FINDING-caiso187 §3d /
known-open item 3: CAISO's **2,858.8 MW** of ST_GAS carries a statistical WEFOR base
of **0.21** that the mechanism matrix's own note records as *"fitted to ERCOT's
once-through 1950s-60s steamers and more than 2× every other thermal class"* — an
ERCOT-fitted parameter governing a different ISO's fleet, with **zero** CAMPD overlay
coverage (0 of 3 plants, all three years) so the statistical term is the ONLY outage
mechanism on the class. The registered field built for this,
`gas_st_wefor_base_override`, is armed at MISO (0.10) and `None` at CAISO.

## 0. Direction-hazard regime (verbatim, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

A derived value below 0.21 adds ST_GAS capability and lowers price — the flattering
sign. Hence §4's conservative default: ambiguity in the citation chain resolves to
the HIGHER defensible value.

## 1. Objective

Replace the ERCOT-fitted 0.21 base with a CAISO-fleet-derived, publicly cited class
EFOR, entered through the existing registered field `gas_st_wefor_base_override`
(rule 24 — no new field, no env knob). Rule 25 governs absolutely: MISO's 0.10 and
ERCOT's 0.21 are neither adopted, averaged, nor used as a sanity check on the CAISO
value; each appears below only as a fence or an explanation obligation.

## 2. Exogenous instrument closure

* EIA-860 — the CAISO ST_GAS fleet census: the units, their vintages, sizes, cooling
  and prime-mover detail. This is what makes the value CAISO's OWN (rule 25).
* A **published, public** generating-unit-class EFOR/EFORd source for the matching
  class — NERC GADS Generating Availability Report class tables (or an equivalent
  published NERC/EIA class statistic). The source must be citable by
  document-and-table, not "industry experience".
* NOTHING else. **No LMP/price series, no CAMPD conduct fit, no model output, no
  residual** anywhere in the derivation. (CAMPD may be cited only to re-verify the
  zero-overlay-coverage premise — a count, not a fit.)

## 3. Numeric gates — each with its written anchor

| gate | bar | anchor |
|---|---|---|
| **G-FROZEN** | The override VALUE is committed in the PRECHECK **before any solve** — one value, no sweep, no second candidate, no "±0.02 to check". Recomputing or adjusting after any price is read voids the session. | The caiso-187 G-FROZEN discipline, inherited whole: a value that can respond to a price is a tuned value (rules 13/21). |
| **G-CITE** | A full public citation chain in the PRECHECK: EIA-860 fleet census (which units, which vintages) → the published GADS-class EFOR table row(s) used → the mapping arithmetic (capacity-weighting, vintage adjustment if the source publishes one). Every link public and quoted; a reviewer must be able to reproduce the value from the citations alone. | Rule 13's admissibility test verbatim: the same quantity could be produced for a forward year from forward drivers (re-run the census against a newer EIA-860 + the current GADS report) and responds to changed conditions (fleet turnover moves it). |
| **G-BAND** | The derived value lies in **[0.03, 0.21]**. Below 0.03 ⇒ refused (no published gas-steam class EFOR sits at or below 3 % — that is better than the best published thermal classes and would mean the derivation slipped a decimal or mis-mapped a class). Above 0.21 ⇒ refused UNLESS the EIA-860 census independently shows the CAISO fleet is older/worse than the ERCOT once-through steamers the 0.21 was fitted to — a claim that must be made from vintage data, not asserted. | The band's ends are pre-existing published/repo objects: the floor is the best published GADS thermal-class EFOR territory (~3–5 %); the ceiling is the incumbent 0.21, which the matrix note already characterizes as an extreme (">2× every other thermal class"). Neither end derives from the C3a residual or from the value being measured. |
| **G-POSITION** | The value's position relative to MISO's 0.10 must be EXPLAINED by the fleet census (vintage/technology/size composition of CAISO's 3 plants vs what the cited class tables condition on) — never chosen to land near or away from it. The explanation is part of the PRECHECK, written before any solve. | Rule 25: a cross-ISO value may be a coincidence, never a target. The census is the only admissible explainer. |
| **G-DOF** | The ledger does not increase. The armed field enters identified `measured` (cited), and the ERCOT-fitted 0.21 stops governing CAISO — a provenance improvement, not a new free parameter. MISO/ERCOT values byte-untouched (rule 25). | The committed DOF ledger (11/8) is the baseline; arithmetic, not choice. |

## 4. Conservative-default rules

* **Ambiguity in the citation chain resolves to the HIGHER defensible cited value**
  (more removal = the anti-flattering direction). If two published class rows both
  plausibly match the fleet, the higher EFOR row governs; the choice and its
  direction are stated in the PRECHECK.
* If NO public chain reaches the fleet (no published class row defensibly matches),
  the outcome is **no arm** — the field stays `None`, the null result is a FINDING,
  and the ERCOT-fitted base remains a named open root-cause issue (rule 21). A null
  outcome here is honest and acceptable; a stretched citation is not.

## 5. Kill criteria

* Value outside G-BAND without the census-grounded exception ⇒ refused, no solve.
* Any link in the chain non-public or non-quotable ⇒ no arm (null-FINDING).
* Any post-PRECHECK value change ⇒ void.
* Any use of MISO/ERCOT values as evidence ⇒ void (rule 25).

## 6. A/B protocol

* **CONTROL** — the caiso-188 keeper recipe re-solved per integration protocol §3
  (`--replay-bundle results/calibration/caiso188_d1_micseam`; capacity-deliverability
  partition materialized and log-verified; `hydro_ror_split` explicitly False,
  disclosed). Ratified tolerance met, noise floor quoted first. A session running
  lanes 2 and 3 may share ONE control solve (disclosed in both FINDINGs).
* **ARM** — control + `gas_st_wefor_base_override = <the frozen cited value>`.
  **ONE field, one mechanism** (rule 19): the keeper's `wefor_multiplier` stays at
  its control value in this arm — the multiplier is lane 2's object, never bundled
  here.
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms sequential
  (rule 12); both registered (rule 15) with `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is
  `gas_st_wefor_base_override` = <value> at CAISO; no other input differs."

## 7. Required artifacts

* `results/calibration/PRECHECK-caiso193-stgas-wefor-<date>.md` — the frozen value,
  the full citation chain, the G-POSITION explanation; committed before any solve.
* Record: `results/calibration/_caiso193_stgas_census.json` — the EIA-860 census
  rows, the cited table values, the weighting arithmetic.
* Run bundles `caiso193_l3_control` (or the shared lane-2 control, disclosed),
  `caiso193_l3_stgas`.
* `results/calibration/FINDING-caiso193-stgas-wefor-<date>.md` with gate tally, the
  direction-hazard clause quoted, and the matrix duty-(b) update in-session
  (`gas_st_wefor_base_override` CAISO cell, currently unadjudicated at CAISO).
