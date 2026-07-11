# Documentation & Site Update — Prompt Pack (2026-07)

> Copy-paste prompts for the refresh described in `UPDATE-PLAN-2026-07.md`.
> Each prompt is **self-contained** and begins with the same contract:
> **read the authoritative code → validate the existing doc/site claim → update
> to match code, citing `file:line`.** Never trust the current site or prose as
> correct.
>
> **Phase order is sequential** (a phase must finish before the next starts);
> **prompts within a phase run in parallel** unless marked SEQUENTIAL.
> Model assignment is on each prompt header. The code-grounded fact base every
> prompt references is `UPDATE-PLAN-2026-07.md` §2 — read it first, then
> re-open the cited code to confirm before writing.

---

## Execution map

```
Phase 0  ──  0A  (Opus)  authoritative methodology doc   ── BLOCKING
                 │
     ┌───────────┬─────────────────────────────────┐
     ▼           ▼                                 ▼
Phase 1 (DOCS, parallel)          Phase 2 (SCAFFOLD, SEQUENTIAL gate)
  1A 1B 1C 1D 1E (Sonnet)           2A (Sonnet)  nav + data + page shells
                                          │
                            ┌─────────────┬─────────────┐
                            ▼             ▼             ▼
                   Phase 3 (SITE PAGES, parallel)
                     3A (Opus)     3B (Opus)     3C (Opus)
                            │
                            ▼
                   Phase 4 (INTEGRATION & QA, SEQUENTIAL)
                     4A (Sonnet)  →  4B (Opus + keeper-auditor agent)
```

Phase 1 (docs) may run concurrently with Phase 2 (site scaffold) — they touch
disjoint files. Phase 3 must wait for 0A (its source) **and** 2A (nav + data +
shells).

---

## Phase 0 — Authoritative methodology doc (BLOCKING)

### 0A — Write `docs/calibration-and-validation-methodology.md`  ·  **Opus**

```
CONTEXT
You are writing the authoritative prose reference for how an LP-based
electricity-market simulator is calibrated and validated. This doc does not
exist yet — the concepts currently live only in code comments, keepers.json
notes, and scattered handoff memos, several of which are stale. CODE IS THE
SOURCE OF TRUTH. Read docs/codebase-site/UPDATE-PLAN-2026-07.md §2 for the
validated fact base and the exact file:line map; then re-open each cited file
to confirm before writing.

CONTRACT (applies to every claim you write)
1. Read the authoritative code. 2. Confirm or correct the fact base. 3. Write
prose that matches code, and add a "Source: <file>:<line>" note under each
major section so the next reviewer can re-verify.

TASK
Create docs/calibration-and-validation-methodology.md with five parts:

1. THE CALIBRATION RUBRIC (v2.x).
   - The two-file split: scripts/calibration_verdict.py (scorer, RUBRIC_VERSION,
     C1-C8, determination, caveat budgets) vs scripts/legitimacy_diagnostics.py
     (D-1..D-10 diagnostics that C7/C8 READ — the scorer never recomputes them).
     State clearly: the diagnostic MEASURES, the verdict GATES.
   - A C1-C8 table: name, tier (load-bearing / supporting / protective), coded
     threshold. Verify each threshold against calibration_verdict.py:139-357.
   - Determination logic + budgets (MAX_PROTECTIVE_CAVEATS, MAX_LEDGERED_CAVEATS;
     commercial-band caveats unbudgeted).
   - The C8 grounded-above-budget escalation (v2.2): provenance (D-4 window per
     binding non-exempt merchant mechanism; no window => fail) AND shape (D-1
     r/CV). Explain GROUNDED_ABOVE_BUDGET is a clean PASS surfaced as a note.
   - The D4_WINDOWS registry (legitimacy_diagnostics.py:202-262) — what it is.
   - Version history v1 -> v2 -> v2.1 -> v2.2 -> v2.3 -> v2.4, one line each
     (verify against rubric §9).
   - CAUTIONS to bake in: C3a/C3b are single-band in effect now (0.10==0.10,
     0.20==0.20 — do NOT imply a live price caveat range); the scorer reads the
     committed run payload, NOT dispatch/<year>_P2.parquet (P2 archived).

2. ABLATION TWINS + DOF LEDGER.
   - Ablation twin = re-solve of the keeper config with every MERCHANT
     floor/bridge/drag off, structural must-run kept. Definition:
     ScenarioConfig.as_zero_forcing_ablation (scenarios.py:4803-4831); off-list
     derived from the D-2 mechanism registry via
     floor_mechanisms.zero_forcing_field_overrides() with
     assert_ablation_coverage() (floor_mechanisms.py:171-187).
   - Production: run_calibration_full.py --zero-forcing-ablation, -ablation
     suffix, ablation_of field. Linkage: keeper sidecar ablation_twin field
     (MANUAL, not auto-wired by dashboard_add_run.py). Enforced by audit_keepers
     E9. Purpose: keeper-vs-twin per-class energy delta = what each floor buys.
   - DOF ledger = free_parameters block in calibration_attestation.json (schema
     dof-ledger/v1), built by scripts/build_dof_ledger.py; identification ∈
     {published, measured-physical, residual}; residual entries REQUIRE a
     non-empty root_cause. Enforced by audit_keepers E8.
   - CAUTION: the requirement is CLAUDE.md rule 21 but code comments say
     "rule 20" (documented +1 offset). Note it; do not "fix" the code comments.

3. THE HOLDOUT / VALIDITY-TESTING PROGRAM (three tiers).
   - Train 2023-2025 (only years tuned; one bundle per keeper).
   - Validation 2022 (iterable ladder 2022 -> 2020-2022 -> earlier); a 2022
     number is model-SELECTION evidence, not certified skill.
   - Locked test 2019 + H1-2026 (touch once, ever; result stands; no calibration
     responds to it).
   - Operational meaning of "first 2022 validation, then 2019 locked test":
     declaring an ISO complete unlocks holdout solves; iterate 2022 (a miss may
     send you back to re-tune 2023-2025); only when satisfied, fire the one-shot
     2019 + H1-2026 and never re-tune against it.
   - Enforcement: {2023,2024,2025} frozenset in run_calibration_full.py:5025,
     audit_keepers.py:185, legitimacy_diagnostics.py:319; CLI
     enforce_holdout_year_gate + --holdout-authorized + marker; CI
     quarantine-gates job. Code enforces one binary — the validation/locked
     distinction is DISCIPLINE, not machine-enforced. Only NEISO is marked
     complete (calibration-complete.json). Data intake is deliberately UNGATED
     (2018-H1-2026 on disk; solve/score/register quarantined). Known gap:
     run_calibration.py (non-_full) has no year gate.
   - Forecast-side validation: capacity hindcast (run_capacity_hindcast.py:
     2020-vintage -> solve 2021/2023/2024/2025, bridge 2022; ERCOT+PJM only;
     diagnostic misses), forecast invariants I1-I14/P1-P3, D-7 statmode + D-8
     stability (2023-2025 only).

4. BACKCAST vs FORECAST SPANS.
   - Data on disk 2018 -> H1-2026; scored backcast dispatch 2023-2025 only;
     forecast horizon 2026-2050 (constants.py:3292-3293).
   - The 2018-2025 backcast / 2024-2030 forecast / 2024-2025 dual-mode overlap
     is a TARGET DESIGN, NOT IMPLEMENTED — say so explicitly. No code path
     scores 2024-2026 in both modes today. Mark it as roadmap.

5. THE "FRONTIER ACHIEVED" DESIGNATION.
   - Owner-declared, purely declarative, NEVER gating (build_status.py:458-463;
     keepers.json "frontier" map). Distinct from the calibration-complete marker
     (which IS gating) — a table contrasting the two. NEISO + NYISO; why (both
     residual is the C3c scarcity tail, gated by reserve dynamics that are
     unimplemented by the real ISO or need new measured identification — closing
     them would be rule-26 residual-fitting).
   - CAUTION: for NEISO the frontier-note keeper (neiso-56), keepers.json pointer
     (neiso-56), and complete-marker keeper (neiso-54 / locked-test neiso-53)
     are DIFFERENT runs. The word "frontier" is overloaded in the logs — name
     the FORMAL designation unambiguously.

STYLE
Match the repo's existing methodology-doc tone (see model-methodology-spec.md
and docs/calibration-determination-rubric.md). Concise, tables where they help,
every section source-cited. This is the doc the site pages will cite — make it
the single reliable reference.

ACCEPTANCE
- [ ] Every C1-C8 threshold matches calibration_verdict.py (re-read it).
- [ ] The scorer-vs-diagnostic and complete-vs-frontier distinctions are explicit.
- [ ] The 2024-2025 overlap is labelled roadmap, not behaviour.
- [ ] Rule-21-vs-"rule 20"-in-code offset noted.
- [ ] Every major section carries a Source: file:line note.
```

---

## Phase 1 — Stale-doc fixes (PARALLEL)  ·  all **Sonnet**

> Independent files; run 1A–1E concurrently. Each: read the code/data named,
> confirm the correct value, edit the doc, done. May run alongside Phase 2.

### 1A — Fix `docs/calibration-best-so-far-neiso.md`

```
Read frontend/data/backcast/keepers.json (NEISO keeper + "frontier" note),
frontend/data/backcast/calibration-complete.json (NEISO marker), and
docs/handoffs/neiso-calibration-complete-memo-2026-07.md. The file
docs/calibration-best-so-far-neiso.md is badly stale: it names keeper
neiso-49-stgas-netload with a "NOT-YET" determination. Update it to the current
truth: keeper = 2026-07-09-neiso-56-reserve-coopt, determination
CALIBRATED-WITH-CAVEATS, calibration-complete (declared 2026-07-07), and add the
formal FRONTIER-ACHIEVED note (from keepers.json "frontier".NEISO). Reconcile
the three divergent keeper pointers explicitly: keepers.json pointer = neiso-56,
frontier-note keeper = neiso-56, complete-marker keeper = neiso-54 with
locked-test scored on neiso-53. Do NOT invent metrics — quote them from the
memo/keepers data. Code/data is source of truth.
```

### 1B — Add frontier note to `docs/calibration-best-so-far-nyiso.md`

```
Read frontend/data/backcast/keepers.json "frontier".NYISO and
docs/calibration-log.md:173-210 (nyiso-61 follow-up). Add a formal
"Frontier achieved (2026-07-11)" section to docs/calibration-best-so-far-nyiso.md
stating the designation and its evidence (the >$300 tail's two reserve levers
chased to ground; the sole remaining gap is the net-load forecast-uncertainty
reserve increment = IMM Recommendation 2021-1, unimplemented by NYISO, no
published formula, closing it would be rule-26 residual-fitting). Disambiguate
this FORMAL designation from the older informal "frontier" phrasing already in
the file. Note NYISO has a frontier designation but NO calibration-complete
marker. Quote metrics, don't invent.
```

### 1C — Mark `docs/forecast-validation-plan.md` superseded

```
Read docs/handoffs/forecast-validation-program-2026-07.md (the live design).
docs/forecast-validation-plan.md describes the ORIGINAL superseded plan
(2018->2025 hindcast, AEO2018 fuel). Add a prominent "SUPERSEDED" banner at the
top pointing to forecast-validation-program-2026-07.md as the live spec
(2020-vintage -> solve 2021/2023/2024/2025, bridge 2022, AEO2021). Do not delete
the content — mark it historical.
```

### 1D — Correct stale `complete: {}` claims

```
Read frontend/data/backcast/calibration-complete.json (NEISO is in "complete",
declared 2026-07-07). Two memos still assert the marker file is empty:
docs/handoffs/holdout-policy-memo-2026-07.md (~lines 9-10, "still reads
complete: {}") and docs/handoffs/forecast-validation-program-2026-07.md
(~lines 30, 266, "none declared yet"). Correct both to reflect that NEISO has
been declared complete and its 2019 + H1-2026 locked-test one-shot has been
scored once and stands. Add a dated note; do not rewrite the surrounding
analysis.
```

### 1E — Cross-reference from `model-methodology-spec.md`

```
The primary spec (model-methodology-spec.md) has NO section on the calibration
rubric, holdout tiers, ablation twins, or the frontier designation. Add a short
"Calibration & Validation" cross-reference subsection (near the outage /
forecast-vs-backcast material, §1.7) pointing readers to the new
docs/calibration-and-validation-methodology.md as the authoritative reference.
Separately, check the three-solve UC section (§1.6): if it still implies P2 is a
live calibration pass, add a one-line note that P2 is ARCHIVED (per CLAUDE.md) —
verify against model/commitment.py / pipeline/commitment.py before editing.
```

---

## Phase 2 — Site scaffold (SEQUENTIAL gate)  ·  **Sonnet**

### 2A — Nav entries, illustrative data, and page shells

```
CONTEXT
You are scaffolding two new pages on the codebase-explorer site at
docs/codebase-site/ so that parallel page-build sessions (Phase 3) can run
without shared-file collisions. Read docs/codebase-site/UPDATE-PLAN-2026-07.md
§3.2 and §2. Read an existing narrative page (e.g. results-calibration.html) for
the exact <head>/shell pattern, and docs/codebase-site/js/nav.js lines 10-58
(the NAV_ITEMS array — the whole nav mechanism; no build step).

DELIVERABLES
1. js/nav.js — add two entries to the "Backcast" dropdown group in NAV_ITEMS:
   { label: 'Calibration Rubric', href: 'calibration-rubric.html', num: '<glyph>' }
   { label: 'Model Validity',     href: 'model-validity.html',     num: '<glyph>' }
   Use HTML-entity glyphs consistent with the existing entries. One insertion
   each covers desktop + mobile.

2. calibration-rubric.html and model-validity.html — SHELL ONLY: the full
   <head> (same CSS/JS includes as results-calibration.html: shared.css,
   site.css, nav.js, shared-header.js, shared.js), a .header block with
   SVG-waveform eyebrow/title/subtitle placeholder, an empty <main> with a
   <nav id="topNav"></nav> placeholder, and the page-footer/bottom-banner. NO
   body content yet — Phase 3 fills these.

3. data/*.json — three illustrative, _meta-tagged files (faithful proportions,
   NOT raw solver output):
   - rubric-scorecard-v2.json — one ISO-year, C1-C8 rows: {crit, name, tier,
     actual, modeled, threshold, status}. Mix of PASS / CAVEAT / GROUNDED /
     SKIP for illustration.
   - ablation-delta.json — per-class energy (TWh) keeper vs zero-forcing twin
     for ~6 classes (CT_PEAKER, ST_GAS, CC, coal, etc.), showing the delta each
     floor buys.
   - holdout-tiers.json — the three-tier timeline: years 2018-2030 tagged
     {year, tier: data|train|validation|locked|forecast|overlap, scored: bool}.
     Encode 2018-2022 as data/holdout, 2023-2025 train, 2022 validation, 2019 +
     H1-2026 locked, 2026-2050 forecast, and 2024-2025 as a ROADMAP overlap flag.

GUARDRAILS
Do NOT create or touch anything under docs/codebase-site/data/backcast/ or
frontend/data/backcast/ (deploy-owned/generated). Only static narrative data/.

ACCEPTANCE
- [ ] Both new pages appear in the top nav (desktop + mobile) and load with no
      console errors (empty body is fine).
- [ ] Three data JSON files are valid, _meta-tagged, internally consistent.
- [ ] No deploy-owned file touched.
```

---

## Phase 3 — Build the pages (PARALLEL)  ·  all **Opus**

> 3A, 3B, 3C write to separate HTML files (+ their own viz JS) — no shared-file
> writes. All depend on 0A (their source of truth) and 2A (shells + nav + data).
> Each MUST re-open the cited code to confirm claims — do not copy the fact base
> blindly.

### 3A — `calibration-rubric.html` (rubric v2.x + frontier)

```
CONTEXT
Build the "Calibration Rubric" narrative page at
docs/codebase-site/calibration-rubric.html (shell already exists from Phase 2).
SOURCE OF TRUTH: docs/calibration-and-validation-methodology.md (Parts 1 and 5)
and the code it cites — RE-OPEN scripts/calibration_verdict.py and
scripts/legitimacy_diagnostics.py to confirm every threshold before publishing.
Match the quality/section-rhythm of results-calibration.html exactly (use only
shared.css/site.css classes).

SECTIONS
1. "How a run is judged" — the scorer-vs-diagnostic split
   (calibration_verdict.py measures the verdict; legitimacy_diagnostics.py
   computes the D-rows C7/C8 read). One sentence: the diagnostic MEASURES, the
   verdict GATES.
2. "The eight criteria" — an interactive/collapsible C1-C8 table from
   data/rubric-scorecard-v2.json, colour-coded by tier (load-bearing /
   supporting / protective) with PASS/CAVEAT/GROUNDED/SKIP badges. Build a small
   viz-rubric-scorecard.js if a static table isn't enough.
3. "Two bands and the caveat budget" — determination logic, MAX_PROTECTIVE=1 /
   MAX_LEDGERED=3, commercial-band caveats unbudgeted. NOTE explicitly that
   C3a/C3b are single-band in effect now (do not imply a live price caveat
   range).
4. "Forced energy and the D-4 escalation" — the C8 15%/30% caps, the 2%
   materiality floor, and the grounded-above-budget escalation (provenance via
   D-4 window + shape via D-1) => GROUNDED_ABOVE_BUDGET clean PASS. Reference the
   D4_WINDOWS registry.
5. "Version history" — v1 -> v2.4 timeline with the one-line change per version.
6. "Frontier achieved" — explain the owner-declared, non-gating designation;
   contrast it with the (gating) calibration-complete marker in a two-column
   table; NEISO + NYISO and why (C3c tail gated by unimplementable reserve
   dynamics; closing would be rule-26 residual-fitting). Link to the live
   calibration-status.html where the FRONTIER badge renders.
7. insight-box: "Backcast match is NOT the objective — a keeper is the most
   structurally faithful run, not the lowest-error one" (CLAUDE.md rule 1).

Cross-link to model-validity.html and results-calibration.html. Add a
"Source: file:line" caption under each data-bearing section.

ACCEPTANCE
- [ ] Every threshold shown matches calibration_verdict.py (re-verified).
- [ ] Frontier vs calibration-complete distinction is explicit and correct.
- [ ] No stale ±5% / binary rubric language anywhere.
- [ ] Loads clean, responsive, section rhythm correct, nav highlights the page.
```

### 3B — `model-validity.html` (three-tier holdout + spans)

```
CONTEXT
Build the "Model Validity & Holdouts" narrative page at
docs/codebase-site/model-validity.html (shell exists). SOURCE OF TRUTH:
docs/calibration-and-validation-methodology.md (Parts 3 and 4) and the code it
cites — RE-OPEN .github/workflows/ci.yml (quarantine-gates), the
enforce_holdout_year_gate in run_calibration_full.py, and
frontend/data/backcast/calibration-complete.json before publishing. Match the
quality of results-calibration.html.

SECTIONS
1. "Data vs solving" — raw data on disk 2018 -> H1-2026, but scored dispatch is
   a governed subset. Intake is ungated (owner-authorized, no-LP validation);
   solve/score/register is quarantined.
2. "Three tiers" — an interactive timeline from data/holdout-tiers.json:
   train 2023-2025, validation 2022 (iterable ladder), locked test 2019 +
   H1-2026 (touch once). Build viz-holdout-tiers.js. Make the touch-once vs
   iterable distinction visually obvious.
3. "First 2022, then 2019 — operationally" — the workflow: declare complete ->
   iterate the 2022 validation (a miss may send you back to re-tune 2023-2025)
   -> only when satisfied, fire the one-shot 2019 + H1-2026, never re-tuning
   against it. Explain WHY 2019 is the honest number and 2022 is only
   model-selection evidence.
4. "How it's enforced" — the {2023,2024,2025} frozenset (three files), the CLI
   solve gate (--holdout-authorized + marker), the CI quarantine-gates job.
   State clearly: code enforces one binary; the validation/locked distinction is
   discipline, not machine-enforced. Only NEISO is marked complete today. Note
   the run_calibration.py ungated gap honestly.
5. "Forecast-side validation" — the capacity hindcast (2020-vintage -> 2021-2025,
   bridge 2022, ERCOT+PJM, diagnostic misses), forecast invariants, D-7/D-8. Link
   to forecast-validation.html.
6. "Backcast and forecast spans" — a clear diagram: data 2018-H1 2026, scored
   backcast 2023-2025, forecast 2026-2050. Then a clearly-labelled ROADMAP panel
   for the intended 2018-2025 backcast / 2024-2030 forecast with a 2024-2025
   dual-mode overlap — marked "planned, not yet implemented" (do NOT present as
   current behaviour). insight-box.warn stating the code does not implement the
   overlap today.

Cross-link to calibration-rubric.html and forecast-validation.html. Source-cite
each section.

ACCEPTANCE
- [ ] The three-tier + touch-once discipline is accurate and matches CLAUDE.md
      rule 22 and the enforcement code.
- [ ] The 2024-2025 overlap is unmistakably labelled roadmap, never behaviour.
- [ ] Only-NEISO-complete and the run_calibration.py gap are stated.
- [ ] Loads clean, responsive, nav highlights the page.
```

### 3C — Refresh `results-calibration.html` (rubric + ablation/DOF)

```
CONTEXT
The existing docs/codebase-site/results-calibration.html §Calibration
Diagnostics teaches the OLD ±5% binary single-tolerance rubric with a hardcoded
13/14 scorecard (~lines 600-826, backed by data/calibration-scorecard.json).
This is materially stale. SOURCE OF TRUTH:
docs/calibration-and-validation-methodology.md (Parts 1 and 2) + the cited code.
Match the page's own existing style.

TASK
1. Rewrite §Calibration Diagnostics: replace the ±5% binary explanation with a
   brief, correct v2.x summary (C1-C8, tiers, two bands, forced-energy budget)
   and DELEGATE the depth to the new calibration-rubric.html (link prominently).
   Replace the stale 13/14 scorecard example with a v2.x tiered example (reuse
   data/rubric-scorecard-v2.json, or refresh calibration-scorecard.json to the
   C1-C8 shape).
2. Add a NEW subsection "Ablation twins & the DOF ledger" explaining: the
   zero-forcing twin (every merchant floor off, structural must-run kept), the
   keeper-vs-twin per-class delta = what each floor buys (illustrate with
   data/ablation-delta.json — a small bar chart, build viz-ablation-delta.js if
   useful), and the DOF ledger (free_parameters in calibration_attestation.json,
   identification published/measured-physical/residual, residual entries carry a
   mandatory root_cause). Note enforcement by audit_keepers E8/E9. Mention the
   CLAUDE.md rule-21 vs "rule 20"-in-code offset in a footnote, accurately.
3. Update §The Calibration Dashboard to reference the two new narrative pages.

GUARDRAILS
Do not touch data/backcast/ or any generated data. Keep the dead
.badge-status.warn CSS note from QA-REPORT harmless (or remove it).

ACCEPTANCE
- [ ] No ±5%/binary rubric language remains; scorecard is C1-C8 tiered.
- [ ] Ablation-twin + DOF-ledger subsection is accurate and cited.
- [ ] Cross-links to calibration-rubric.html and model-validity.html resolve.
```

---

## Phase 4 — Integration & QA (SEQUENTIAL)

### 4A — Integration & responsive pass  ·  **Sonnet**

```
Do the integration pass on the updated codebase-site (docs/codebase-site/).
1. Cross-link audit: every reference between the three touched pages
   (calibration-rubric, model-validity, results-calibration) and to the live
   dashboards (calibration-status.html, backcast-runs.html, forecast-validation.html)
   resolves to the correct slug/anchor.
2. Nav consistency: js/nav.js renders both new pages in the Backcast group on
   every page (desktop + mobile) and highlights the active page.
3. Responsive + section-rhythm audit on the two new pages + results-calibration
   at 1400/1000/700/400px: no horizontal scroll, no overlap, charts resize,
   dark-section text contrast >= 4.5:1, KaTeX (if used) adapts.
4. Accessibility: focus indicators, alt/aria on SVGs, logical tab order,
   prefers-reduced-motion respected.
Modify HTML/CSS/JS as needed; no new files. Do NOT touch deploy-owned generated
data.
```

### 4B — Accuracy audit + keeper-text verification  ·  **Opus** + `calibration-keeper-auditor` agent

```
Final truth gate. CODE IS THE SOURCE OF TRUTH.
1. For every factual claim, equation, threshold, and diagram label on
   calibration-rubric.html, model-validity.html, and the changed sections of
   results-calibration.html, AND in docs/calibration-and-validation-methodology.md:
   read the corresponding source (calibration_verdict.py, legitimacy_diagnostics.py,
   scenarios.py, floor_mechanisms.py, build_dof_ledger.py, audit_keepers.py,
   run_calibration_full.py, .github/workflows/ci.yml, constants.py,
   build_status.py, keepers.json, calibration-complete.json) and flag+fix any
   discrepancy directly.
   Pay special attention to: C1-C8 thresholds; scorer-vs-diagnostic; single-band
   price; complete-marker vs frontier; only-NEISO-complete; the 2024-2025 overlap
   labelled as roadmap (not behaviour); the rule-21/"rule 20" offset.
2. Spawn the calibration-keeper-auditor agent to confirm the keeper and frontier
   text on the new/edited pages matches each designated keeper's actual run
   results and the keepers.json/frontier data. Repair any drift it finds.
3. Run /sync-docs to catch remaining prose drift and log a CHANGELOG entry.
4. Append a short findings table to docs/codebase-site/QA-REPORT.md (or a new
   QA-REPORT-2026-07.md) listing every discrepancy found and fixed.

ACCEPTANCE
- [ ] Every threshold/name/claim matches code (not just the methodology doc).
- [ ] Keeper + frontier text verified against run results by the auditor agent.
- [ ] 2024-2025 overlap is roadmap-labelled everywhere; no stale ±5% rubric
      language survives on any page.
- [ ] QA findings recorded.
```

---

## Summary

- **Total prompts:** 11 (1 methodology doc + 5 doc fixes + 1 scaffold + 3 pages
  + 2 integration/QA).
- **Max parallelism:** 5 (Phase 1 docs), then 3 (Phase 3 pages).
- **Critical path:** 0A → 2A → any Phase 3 page → 4A → 4B (5 steps).
- **Model mix:** Opus for the methodology doc, the three high-accuracy pages,
  and the final audit; Sonnet for the mechanical doc fixes, scaffold, and
  integration pass.
- **Invariant across all prompts:** validate against code first; the current
  site and prose are not trusted as correct.
