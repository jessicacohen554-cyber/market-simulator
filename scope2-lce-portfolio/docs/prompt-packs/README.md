# Prompt Packs

Each `PP-NN-*.md` is a **build prompt**: a self-contained instruction to
implement or deepen one module, citing the ADRs (`../decisions/`) it must honor.
Packs turn decisions into code. A team member can open a pack in a fresh session
and execute it.

## Ordering & gating

Run in order; each pack lists its **upstream decisions**. Do not run a pack until
its ADRs are recorded (a pack that depends on an undecided question should trigger
the relevant planning session first).

| PP | Builds | Upstream decisions |
|---|---|---|
| PP-00 | Scaffold & `PortfolioConfig` | 0001, 0002 |
| PP-01 | Load intake & LMP coupling | PS-07, PS-08 |
| PP-02 | Resource catalog & costs | PS-01, PS-03, PS-05, PS-06 |
| PP-03 | CF profiles (first vendoring) | — |
| PP-04 | LP core (both modes, constraints) | PS-02, PS-04 |
| PP-05 | Sweep driver & CLI | 0002 |
| PP-06 | Outputs & reporting | PS-02, PS-04 |
| PP-07 | Tests | all |

## Current state

Waves 0–1 implemented: **PP-00** (config + validation + `from_file` loader),
**PP-01** (real intake rules, hard missing-hour/dup errors, load growth, `prepare_lmp` +
`collapse_zonal_lmp`), **PP-02** (resource catalog ATB 2024 CRF, per-ISO caps/eligibility,
hydro monthly budgets, split-tech parse; split LP logic lands PP-02b), **PP-03** (real
per-ISO CF Parquets + synthetic fallback + `build_profiles.py` vendored script),
**PP-04** (LP core both modes, split-storage vars, hydro budget constraint, additionality
accounting, infeasible-safe), **PP-05** (sweep + CLI with `--config`, `--all-isos` batch,
graceful infeasible handling), **PP-06** (enriched frontier metrics + residual CO₂ +
run metadata). Tests: 76 passing (PP-07). Open: PP-07 suite depth, PP-09 (gas-CC+CCS)
backlog.

## Rules for every pack

- Stay standalone: **no `import market_sim`**. Reused logic is copied into
  `src/lce_portfolio/vendored/` with a source + revision + re-sync header.
- Follow the LP rules that apply (no Python loop over hours in matrix
  construction; duals for prices; docstrings on every public function/module).
- Add/extend tests (PP-07) and update `PLAN.md`'s status table.
