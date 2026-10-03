# D2 — site drift audit, calibration / validity / forecast pages (2026-10-03, HEAD d7ff7c2)

Scope: model-validity, results-calibration, calibration-rubric, calibration-status, backcast-runs,
scarcity-deep-dive, mechanism-matrix, data-completeness, forecast-status, forecast-runs,
forecast-bands, forecast-validation, marginal-abatement (static prose only). Source of truth:
CLAUDE.md rule 22 `[R-C3C]`, `docs/governance/rule-history.md` §18 (holdout removal 2026-09-09) and
§26 (frontier withdrawals 2026-09-30), `scripts/lib/holdout_policy.py:1-25` (pure classifier),
`scripts/run_calibration_full.py:10297` (`HOLDOUT_CALIBRATION_YEARS`), `docs/calibration-determination-rubric.md:3`
(RUBRIC_VERSION 3.17, 2026-10-02), `frontend/data/backcast/keepers/<ISO>.json` (nine keepers, 2026-10-02).

## Changes made

- model-validity.html:7 — meta description "three-tier train/validation/locked-test holdout ladder, touch-once discipline, quarantine gates" → post-2026-09-09 regime (any year solvable/scorable/registrable, no certified out-of-sample number, touchpoints fold per rule 30) (rule-history.md:1174-1230; CLAUDE.md rule 22).
- model-validity.html:313 — h1 "Model Validity & Holdouts" → "Model Validity & Year Spans".
- model-validity.html:315 — subtitle now opens with the 2026-09-09 status paragraph (rule 22 `[R-C3C]`, rule-history §18); tier vocabulary described as a pure classifier (holdout_policy.py:9-24).
- model-validity.html:337, 562, 587, 592, 598 — former-gate paragraphs prefixed "[Historical — removed 2026-09-09 …]"; verbs moved to past tense where they asserted live enforcement (rule-history.md:1180-1195 table of removed gates).
- model-validity.html:457 — "As of 2026-08-19 three ISOs hold a complete marker … no locked-test year has ever been solved" → tiers carry no permission; calibration-complete.json = keeper designation + forecast gate (a); nine keepers 2026-10-02; 2019–2022 touchpoints fold (keepers/*.json; rule 30).
- model-validity.html:489 — "This is the gate: it unlocks the rule-22 holdout solves" → not a gate; designation + gate (a) only (rule-history.md §18 "What was deliberately KEPT").
- model-validity.html:614 — Source line (stale line numbers :7969/:7981-8071, TIER_MARKER_BLOCK, run_d6_quarantine, ci.yml quarantine-gates, holdout-freeze.json) → surviving code at HEAD (run_calibration_full.py:10297; holdout_policy.py tier_for_year) + the removed list.
- model-validity.html:726 — Figure MV3 caption "confined to 2023–2025 (… NEISO 2019 + H1-2026 locked-test one-shot)" → training window plus folded 2019–2022 touchpoints (keepers/SPP.json gates, CAISO.json disposition_note).
- model-validity.html:774 — key takeaway "solving is governed … locked test is the touch-once honest number" → open solving, worst-of determination over every registered year (CLAUDE.md rule 30; calibration_verdict.py::iso_determination).
- results-calibration.html:734 — "v2.x rubric (RUBRIC_VERSION 2.4)" → v3.x, RUBRIC_VERSION 3.17 (docs/calibration-determination-rubric.md:3).
- results-calibration.html:850 — scorecard source note: thresholds mirror v2.4 snapshot, scorer now 3.17 (rubric-scorecard-v2.json `_meta`/`run_metadata.rubric_version` = 2.4 is the illustrative file's own version, left as-is).
- results-calibration.html:1007 — Model Validity cross-ref "three-tier … holdout program and its quarantine gates" → post-removal description.
- calibration-rubric.html:584 — calibration-complete.json purpose "Gating — authorizes rule-22 validation holdout solves" → keeper designation + forecast gate (a), authorizes nothing (rule-history §18).
- calibration-rubric.html:602 — "frontier does not imply holdout authorization … NYISO holds a complete marker … two current holders" → no live frontier declaration; all withdrawn 2026-09-30 (keepers/CAISO.json `withdrawn_note`, rule 30(c), rule-history §26).
- mechanism-matrix.html:248 — glossary row "Holdout tiers … locked test = 2019 + H1-2026 (scored once, ever) … spend is frozen" → "Year tiers" with the removed-regime wording.

## Found, not resolved (out of time budget or needs owner/other data)

- model-validity.html — the body sections §§ on the tier ladder (Figure MV2 data `data/holdout-tiers.json`), the "touch-once" narrative (~lines 479-515), and the holdout-policy-memo citations (lines 395, 462) still describe the former regime in present tense beyond the marked paragraphs; a fuller rewrite of those sections is warranted (rule-history §18). Marked at the page head only.
- calibration-rubric.html:7 — meta says "rubric v3.x" (fine) but the version-history block ends well before 3.17; §9 of the rubric md has the newer amendments (3.4→3.17) not reflected on the page.
- calibration-rubric.html:602 ff. — remaining "frontier-achieved" section prose (badge `.cs-badge.det-frontier`, "holders") describes a designation nobody currently holds; left as record, header sentence corrected only.
- results-calibration.html — rubric-scorecard-v2.json is explicitly an illustrative v2.4 excerpt; not regenerated (generated/illustrative data, out of scope).
- data-completeness.html:368-376, 442-443 — JS note says SPP/NWPP/SOCO have no audited rows since the 2026-07-10 census; `data/completeness.js` is deploy-generated and absent in this checkout, so the claim could not be verified against rows. Not fabricated; left as-is. The "six ISOs" at :376 is a historical census statement and accurate as written.
- calibration-status.html, backcast-runs.html, scarcity-deep-dive.html, forecast-status.html, forecast-runs.html, forecast-bands.html, forecast-validation.html, marginal-abatement.html — grep for holdout / locked-test / tier / stale ISO counts / "as of 2026-0x" / RUBRIC_VERSION found no static-prose hits; not line-audited beyond that within budget.
