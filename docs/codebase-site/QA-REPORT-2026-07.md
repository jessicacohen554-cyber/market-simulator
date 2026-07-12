# Calibration/Validity Documentation Refresh — Final Truth-Gate QA

**Date:** 2026-07-12
**Scope:** `calibration-rubric.html`, `model-validity.html`, the changed
(calibration) sections of `results-calibration.html`, the illustrative data
files they render (`data/rubric-scorecard-v2.json`, `data/holdout-tiers.json`),
and `docs/calibration-and-validation-methodology.md`.
**Method:** every factual claim, threshold, equation, and diagram label was
read against its source of truth — `scripts/calibration_verdict.py`,
`scripts/legitimacy_diagnostics.py`, `scripts/audit_keepers.py`,
`scripts/build_dof_ledger.py`, `scripts/run_calibration_full.py`,
`scripts/build_status.py`, `src/market_sim/config/scenarios.py`,
`src/market_sim/config/constants.py`, `src/market_sim/data/floor_mechanisms.py`,
`.github/workflows/ci.yml`, `frontend/data/backcast/keepers.json`, and
`frontend/data/backcast/calibration-complete.json` — and discrepancies were
fixed directly. The `calibration-keeper-auditor` agent then independently
verified the keeper/frontier text against the registered run results.

**Result:** 9 discrepancies found and fixed (7 stale line citations, 2
substantive), plus 2 substantive fixes in the wider prose docs caught by the
`/sync-docs` sweep. **Zero threshold/behaviour errors** — every C1–C8
tolerance, budget, gate, and determination rule on the pages matches
`calibration_verdict.py` (RUBRIC_VERSION 2.4) exactly. The keeper auditor
reported **0 mismatches** on keeper/frontier text.

---

## Findings & fixes

| # | File | Claim as written | Source truth | Fix |
|---|---|---|---|---|
| 1 | `docs/calibration-and-validation-methodology.md` §2.1 | `as_zero_forcing_ablation` cited at `scenarios.py:4848-4876` | Lives at `scenarios.py:4957-4985` | Citation updated |
| 2 | same, §2.1 | Ablation CLI + `ablation_of` cited at `run_calibration_full.py:5131-5171, 5581-5620` | `ablation_of` wiring ≈5340-5350; `--zero-forcing-ablation` CLI ≈5759-5800 | Citation updated |
| 3 | same, §2.2 | DOF schema tag cited at `build_dof_ledger.py:756` | `"schema": "dof-ledger/v1"` at line 802 | Citation updated |
| 4 | same, §3.2 | `HOLDOUT_CALIBRATION_YEARS` at `run_calibration_full.py:5039`, `enforce_holdout_year_gate` at `:5043`, source `:5031-5090` | Constants at 5217, gate at 5221-5267 | Citations updated |
| 5 | same, §4 | `START_YEAR`/`END_YEAR` at `constants.py:3292-3293` | At `constants.py:3871-3872` | Citation updated |
| 6 | `calibration-rubric.html` §4 | D-4 window table showed 4 mechanism rows | `D4_WINDOWS` has 6 entries — table omitted `caiso_gas_commitment_floor` → [9, 17) and `cc_mustrun_per_plant × CC_REGULAR` → [0, 24) (`legitimacy_diagnostics.py:202-262`) | Both rows added, with their cited driver evidence |
| 7 | `calibration-rubric.html` §4 | `D4_WINDOWS` cited at `legitimacy_diagnostics.py:184-229` | Registry spans 184-262 | Citation updated |
| 8 | `data/rubric-scorecard-v2.json` (rendered by both calibration-rubric.html and results-calibration.html) | C6 PASS note: "Attestation complete: DOF ledger present, ablation twin linked, outage source machine-clean" | C6 (`score_governance`, `calibration_verdict.py:1767-1826`) gates the **four governance assertions** + machine-clean config only; the DOF ledger and ablation twin are `audit_keepers` **E8/E9** checks, not C6 | Note rewritten to the four actual assertions, with the E8/E9 distinction stated |
| 9 | `results-calibration.html` §3 | Measured-data insight box "(See CLAUDE.md rule #12.)" | The measured-data admissibility rule is CLAUDE.md **rule 13** (rule 12 is parallel-solve discipline) | Citation corrected to #13 |
| 10 | `model-validity.html` §4 | Holdout gate cited at `run_calibration_full.py:5056` / `:5060-5104` | 5217 / 5221-5267 | Citations updated |
| 11 | `model-validity.html` §6 | `START_YEAR`/`END_YEAR` at `constants.py:3292-3293` | 3871-3872 | Citation updated |
| 12 | `docs/calibration-determination-rubric.md` C6.1 (sync-docs sweep) | "the rule #12 admissibility test" | Rule **13** in current CLAUDE.md (the same doc's C5a section already cites rule #13) | Corrected to #13 |
| 13 | `docs/calibration-determination-rubric.md` C8 (sync-docs sweep) | "(rule 12: no floor without a window)" | CLAUDE.md **rule 17**; "rule 12" is the older code-comment numbering the methodology doc documents | Corrected to rule 17 with the older-numbering note |

## Verified clean (no change needed)

- **C1–C8 thresholds** — every constant on the pages matches
  `calibration_verdict.py`: C1 min(2 % load, 8 TWh) + ±3.0 pp; C2 ±2.5 %/±5 %
  prelim-923 fallback with complete-vintage deferral to C1, 10 TWh
  immateriality; C3a/C3b 0.10/0.20 with coincident commercial bands; C3c
  [0.5×, 2×], small-count 10, tail thresholds $200 (ERCOT/PJM/MISO/CAISO) /
  $300 (NYISO/NEISO); C4 r ≥ 0.70, NRMSE ≤ 0.30, 5 TWh skip; C5a ±7 %/±10 %;
  C5b ±30 %; C5c r ≥ 0.50, CV < 0.25 skip; C7 r ≥ 0.8, CV ratio ≥ 0.5; C8
  15 %/30 % with the 2 % materiality floor.
- **Scorer-vs-diagnostic split** — "the diagnostic MEASURES, the verdict
  GATES" wording matches the implementation (scorer reads committed
  `legitimacy_diagnostics.json`, re-gates measured shares, never re-solves).
- **Single-band price** — C3a/C3b target == commercial since v2.3; every page
  states no live price caveat band; no stale ±5 %/0.15 gate language survives
  anywhere on the site (the only ±5 % mentions are correctly framed as retired
  reported magnitudes).
- **Determination logic** — order (C6 → any-FAIL → budgets → zero-caveat
  CALIBRATED), budgets 1 protective / 3 ledgered, unbudgeted commercial-band
  caveats, unscored-criterion cap: all match `determine_from_artifacts`.
- **Complete-marker vs frontier** — gating vs declarative contrast, holders
  (NEISO-only complete 2026-07-07; NEISO + NYISO frontier 2026-07-11), and
  the NEISO run-id divergence (frontier keeper neiso-56, marker keeper
  neiso-54, one-shot on neiso-53's frozen config) all match
  `calibration-complete.json` / `keepers.json` / `build_status.py:458-472`.
- **2024–2025 dual-mode crossover** — labelled roadmap/target-design (never
  behaviour) on every page and diagram; `START_YEAR = 2026` confirmed; no
  dual-mode scoring code path exists.
- **Rule-21/"rule 20" offset** — the footnote and caution match CLAUDE.md's
  documented +1 renumbering; code comments left untouched as instructed.
- **E8/E9 claims** — all six current keepers carry resolvable `ablation_twin`
  sidecar links (verified per sidecar); the one remaining grandfather literal
  (`2026-07-03-caiso-51-firm-base`) is inert dead code as described.
- **Holdout enforcement** — three parallel frozensets, both-flag-AND-marker
  CLI gate, tier-agnostic CI binary, `run_calibration.py` no-gate asterisk,
  intake-log entries (2026-07-08, 2026-07-10): all match source.
- **Keeper/frontier text vs run results** — independently verified by the
  `calibration-keeper-auditor` agent: 0 mismatches across all six ISOs
  (`audit_keepers.py` 0 failures; `build_status.py --check` in sync). Two E7
  staleness warnings (newer ERCOT/PJM runs exist than the current keepers) are
  keeper-selection questions, not documentation drift.
