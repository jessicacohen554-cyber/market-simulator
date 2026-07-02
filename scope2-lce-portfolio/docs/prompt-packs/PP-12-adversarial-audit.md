# PP-12 — Fresh-Eyes Adversarial Audit (2026-07-02)

Not a build pack: the record of the final-phase adversarial bug hunt
(Workstream A of the final build session). Kept here so the audit's scope,
protocol, and outcomes are discoverable next to the packs whose code it
hardened.

## Protocol

- **Four blind auditors**, one per lens, none seeing the others' findings:
  (1) LP correctness (`lp.py`), (2) data/loader edge cases (`resources.py`,
  `profiles.py`, data tables), (3) intake/IO/results plumbing (`intake.py`,
  `outputs.py`, `report.py`, results store), (4) config/CLI (`config.py`,
  `cli.py`, examples). Each was instructed to *construct failing inputs*,
  not just read code, and to ship a runnable repro per claim.
- **Independent adversarial verification**: every finding was re-examined by
  a second agent instructed to refute it, judging against the governing
  contracts (ADRs, docstrings, PLAN) and distinguishing bugs from documented
  intended behavior.
- **Fix discipline**: verified bugs fixed with a regression test in the same
  commit, citing the finding ID; refuted/intended-behavior findings recorded,
  not "fixed".

## Outcome (41 findings raised → 24 fixed, 5 documented-intended, rest refuted/downgraded-duplicates)

Headline verified-and-fixed defects (commit trail on the audit branch):

| ID | Severity | Defect | Fix |
|---|---|---|---|
| IO-1/CL-2 | critical | unsanitized `--run-id` reached `shutil.rmtree` — absolute/`../` ids deleted arbitrary directories | run-id validated as a single safe path component |
| LP-2 | critical | Mode B at f=1.0 + IPM-no-crossover: zero-cost simultaneous buy+sell ray made matching %/grid CO₂ arbitrary | ε tiebreak on excess in the Mode B objective |
| LP-1 | major | additionality counted exported existing energy as unmatched load, distorting Mode B solves | `exc_ex[t]` columns, existing-first attribution; **ADR 0008 amended** |
| DL-2/DL-3 | major | blank CCS columns bypassed the ADR 0012 gate (unabated gas = 100% clean); capture>1 oversized 45Q; promised emission cross-check missing | explicit-cell requirement, capture∈(0,1], cross-check |
| CL-1 | major | `--config` silently discarded explicit sweep flags | sentinel defaults; flags override the file |
| CL-5/6/14 | major | untyped `from_file` (string "false" silently enabled strict matching; raw YAML/JSON tracebacks) | per-field type validation, wrapped parse errors |
| CL-7, CL-4 | moderate | `--all-isos` aborted on first failure losing the batch report; all-infeasible runs exited 0 looking solved | per-ISO continue + status summary; flagged rows + nonzero exit |
| IO-2/3/5/6 | major/minor | NaN prices/rates/load passed intake (NaN load summed to 0); float-hour and leap-length files crashed raw | finite/integer/calendar validation in all intakes |
| IO-7/CL-3 | minor | results-store re-run deleted the old run before solving | temp-dir write + swap on success |
| DL-1/4/5/6/9/10/11/13 | minor | lowercase-ISO cap bypass, unvalidated discount rate, NaN caps, silent duplicate rows, negative EAC premium, blank hydro/storage cells, raw KeyError | canonicalization + loader hardening |
| DL-7/DL-8 | minor | profile NaN/dup-hour acceptance, silent flat fallback for variable renewables, no shape provenance | exact-calendar + finite checks; hard error for absent wind/solar; `profile_source` in run metadata |
| LP-3/LP-4 | minor | per-resource (not fleet) hydro budgets (latent); strict-hourly shadow price = hour-0 dual only | fleet-shared rows; load-weighted mean dual |
| IO-8, CL-8/9/12/13 | minor | renderer crash on null matching_pct; misc CLI error-quality gaps; non-ISO-keyed dummy LMP reuse | uniform guards + error hygiene |

Documented-intended (no code change): IO-4 zonal-drop (docstring-documented),
CL-10 strict-flag-ignored-in-Mode-A (documented "Mode B only"), CL-15
cwd-relative paths (README-documented convention), DL-12 45Q net-VOM clamp
(deliberate — now recorded in ADR 0012), DL-8 warn-and-fallback default
(documented; provenance gap fixed as hygiene).

No plausible-but-unconfirmed findings survived verification, so no
`xfail(strict)` markers were needed.

## Regression surface

`tests/test_lp_audit_regressions.py` plus finding-tagged tests appended to
`test_cli.py`, `test_intake.py`, `test_resources.py`, `test_ccs.py`,
`test_profiles_real.py`, `test_report.py`, `test_run_real_sweep_lmp.py`.
Suite: 164 → 207 tests.
