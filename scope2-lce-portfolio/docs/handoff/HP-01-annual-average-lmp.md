# HP-01 — Annual-average LMP intake mode + input-template generator

**Model:** Sonnet · **Depends on:** nothing · **Unblocks:** HP-03, HP-04
**Targets:** `src/lce_portfolio/intake.py`, `src/lce_portfolio/outputs.py`,
`src/lce_portfolio/report.py`, `scripts/make_input_templates.py` (new),
`data/templates/README.md`, `tests/`

Paste the block below into a fresh Claude Code session on
`jessicacohen554-cyber/market-simulator`.

```text
You are finalizing the standalone Scope 2 LCE portfolio tool in
scope2-lce-portfolio/ (repo jessicacohen554-cyber/market-simulator). Work ONLY
inside scope2-lce-portfolio/. Develop on a fresh branch off latest origin/main
named scope2/hp-01-annual-avg-lmp (or the branch your session designates);
push there; open NO pull request.

GOAL
Implement the annual-average LMP intake mode described in
data/templates/README.md §2b, so the tool accepts EITHER the hourly LMP
contract (hour,iso,lmp — already wired, ADR 0011) OR an annual-average file
(iso,annual_avg_lmp — no hour column), expanded to a flat 8760 $/MWh vector
per ISO. Also add a small template-generator script.

CONTEXT (read first)
- scope2-lce-portfolio/PLAN.md, README.md, data/templates/README.md
- src/lce_portfolio/intake.py (lmp_intake / prepare_lmp and their validation
  idioms: hard errors on missing hours, duplicates, non-finite values)
- docs/decisions/0011-lmp-coupling-scenario-selection.md (hourly contract)
- src/lce_portfolio/outputs.py (run_metadata assembly) and report.py
  (provenance section) for where run provenance surfaces.

REQUIREMENTS
1. Schema detection in the LMP read path: if the file has columns
   {iso, annual_avg_lmp} and NO hour column, treat it as annual-average;
   expand each ISO's value to a flat vector of length 8760 (use the existing
   HOURS_PER_YEAR constant — no magic 8760 literals). If the file has the
   hourly columns, behavior is byte-identical to today. Any other column
   combination keeps today's clear error messages.
2. Validation for the new schema, matching the module's existing idioms:
   duplicate iso rows are a hard error naming an example; non-finite or
   negative-average values are a hard error; an ISO requested by the run but
   absent from the file keeps the existing missing-ISO error shape.
3. Provenance: thread an lmp_kind field ("hourly" | "annual_average_flat")
   into the run metadata JSON and the report payload; the rendered report's
   provenance section must visibly label annual-average runs as a flat-price
   comparison (hourly shape/covariance value excluded). Bump the report
   payload_version if the payload contract changes; keep render_report() a
   pure function of the payload.
4. Do NOT change the LP, the premium definition, or any ADR semantics — a
   flat LMP is just a degenerate price vector to the existing machinery.
5. New script scripts/make_input_templates.py: writes full-8760 fillable
   skeleton CSVs (load-by-facility and hourly LMP, for a --isos list,
   default the six real ISOs) plus the annual-average template, into a
   --out-dir (default data/templates/skeletons/, gitignored — add the
   ignore). The three committed draft templates in data/templates/ stay the
   small human-readable examples; do not overwrite them.
6. Update data/templates/README.md: remove the "until HP-01 lands" status
   caveat, document the generator, keep the schema tables accurate.
7. Tests (mirror existing style in tests/test_intake.py, trivial cases
   first): schema detection both ways; flat expansion correctness (every
   hour equals the annual value); duplicate-iso and negative/non-finite
   errors; end-to-end CLI run on a tiny synthetic annual-average file
   asserting lmp_kind lands in run_metadata.json and the report HTML
   contains the flat-price label; template generator round-trips through
   intake with zero validation errors after filling values.

INVARIANTS (non-negotiable)
- Standalone: no `import market_sim` anywhere; verify
  `grep -rn "import market_sim" src/ || echo OK-standalone`.
- No Python loops over hours in anything that builds vectors — numpy
  (np.full / np.repeat) only.
- Docstrings on every public function; no magic numbers (constants/config).
- Report HTML stays fully self-contained (existing smoke test enforces no
  external references — keep it green).

VERIFY before commit (from scope2-lce-portfolio/, ../.venv/bin/python inside
the repo):
  python -m pytest tests/ -q                       # all green, incl. new tests
  python examples/run_sample_sweep.py              # unchanged behavior
  grep -rn "import market_sim" src/ || echo OK     # isolation
Commit in small, imperative-present-tense commits and push with
`git push -u origin <branch>`; if a push 413s once, use
mcp__github__push_files instead of retrying. Do not put raw model IDs in
commits or code. Finish by summarizing what changed and confirming all
verify commands passed.
```
